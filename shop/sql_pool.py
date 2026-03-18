import threading

from psycopg2 import pool
from django.conf import settings

_connection_pool = None
_pool_lock = threading.Lock()

def get_connection_pool():
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


def close_connection_pool():
   global _connection_pool
   if _connection_pool:
      _connection_pool.closeall()
      _connection_pool = None
