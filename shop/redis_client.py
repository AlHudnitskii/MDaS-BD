import redis
from django.conf import settings

_cache_pool = redis.ConnectionPool(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    db=settings.REDIS_DB_CACHE,
    decode_responses=True,
    max_connections=20,
)

_session_pool = redis.ConnectionPool(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    db=settings.REDIS_DB_SESSIONS,
    decode_responses=True,
    max_connections=20,
)

_pubsub_pool = redis.ConnectionPool(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    db=settings.REDIS_DB_PUBSUB,
    decode_responses=True,
    max_connections=10,
)


def get_redis_cache() -> redis.Redis:
    return redis.Redis(connection_pool=_cache_pool)

def get_redis_sessions() -> redis.Redis:
    return redis.Redis(connection_pool=_session_pool)


def get_redis_pubsub() -> redis.Redis:
    return redis.Redis(connection_pool=_pubsub_pool)
