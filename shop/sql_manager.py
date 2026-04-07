import uuid
import psycopg2
from psycopg2.extras import RealDictCursor
from .sql_pool import get_connection_pool


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

    def execute(self, query, params=None):
        if params is None:
            self.cursor.execute(query)
        else:
            self.cursor.execute(query, params)
        results = self.cursor.fetchall()
        return [dict(row) for row in results]

    def execute_one(self, query, params=None):
        if params is None:
            self.cursor.execute(query)
        else:
            self.cursor.execute(query, params)
        result = self.cursor.fetchone()
        return dict(result) if result else None

    def execute_update(self, query, params=None):
        if params is None:
            self.cursor.execute(query)
        else:
            self.cursor.execute(query, params)
        self.connection.commit()
        return self.cursor.rowcount

    def call_procedure(self, proc_name, params):
        self.cursor.callproc(proc_name, params)
        self.connection.commit()

    def begin_nested(self):
        savepoint_name = f"sp_{id(self)}"
        self.cursor.execute(f"SAVEPOINT {savepoint_name}")
        return savepoint_name

    def rollback_to(self, savepoint_name):
        self.cursor.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")

    def release_savepoint(self, savepoint_name):
        self.cursor.execute(f"RELEASE SAVEPOINT {savepoint_name}")
