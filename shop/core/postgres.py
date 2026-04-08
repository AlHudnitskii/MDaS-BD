import threading
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from django.conf import settings

_connection_pool = None
_pool_lock = threading.Lock()


def get_connection_pool() -> pool.ThreadedConnectionPool:
    global _connection_pool
    if _connection_pool is None:
        with _pool_lock:
            if _connection_pool is None:
                _connection_pool = pool.ThreadedConnectionPool(
                    minconn=1,
                    maxconn=20,
                    user=settings.DATABASES['default']['USER'],
                    password=settings.DATABASES['default']['PASSWORD'],
                    host=settings.DATABASES['default']['HOST'],
                    port=settings.DATABASES['default']['PORT'],
                    database=settings.DATABASES['default']['NAME'],
                )
    return _connection_pool


def close_connection_pool() -> None:
    global _connection_pool
    if _connection_pool:
        _connection_pool.closeall()
        _connection_pool = None


class SQLManager:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.pool = get_connection_pool()

    def __enter__(self):
        self.connection = self.pool.getconn()
        self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.pool.putconn(self.connection)
        return False

    def execute(self, query: str, params=None) -> list[dict]:
        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]

    def execute_one(self, query: str, params=None) -> dict | None:
        self.cursor.execute(query, params)
        result = self.cursor.fetchone()
        return dict(result) if result else None

    def execute_update(self, query: str, params=None) -> int:
        self.cursor.execute(query, params)
        self.connection.commit()
        return self.cursor.rowcount

    def call_procedure(self, proc_name: str, params: tuple) -> None:
        self.cursor.callproc(proc_name, params)
        self.connection.commit()

    def begin_nested(self) -> str:
        sp = f"sp_{id(self)}"
        self.cursor.execute(f"SAVEPOINT {sp}")
        return sp

    def rollback_to(self, sp: str) -> None:
        self.cursor.execute(f"ROLLBACK TO SAVEPOINT {sp}")

    def release_savepoint(self, sp: str) -> None:
        self.cursor.execute(f"RELEASE SAVEPOINT {sp}")
