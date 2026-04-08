import json
import decimal
import uuid
import datetime
import logging

from ..core.redis import get_redis_cache

logger = logging.getLogger(__name__)


class _Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        return super().default(obj)


def _dumps(data) -> str:
    return json.dumps(data, cls=_Encoder)

def _loads(raw: str):
    return json.loads(raw)


class CacheService:

    @staticmethod
    def get(key: str):
        try:
            raw = get_redis_cache().get(key)
            return _loads(raw) if raw is not None else None
        except Exception as e:
            logger.warning(f"Cache GET failed key={key}: {e}")
            return None

    @staticmethod
    def set(key: str, value, ttl: int) -> bool:
        try:
            get_redis_cache().setex(key, ttl, _dumps(value))
            return True
        except Exception as e:
            logger.warning(f"Cache SET failed key={key}: {e}")
            return False

    @staticmethod
    def delete(key: str) -> bool:
        try:
            get_redis_cache().delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache DELETE failed key={key}: {e}")
            return False

    @staticmethod
    def invalidate_prefix(prefix: str) -> int:
        try:
            r = get_redis_cache()
            deleted, cursor = 0, 0
            while True:
                cursor, keys = r.scan(cursor, match=f"{prefix}*", count=100)
                if keys:
                    r.delete(*keys)
                    deleted += len(keys)
                if cursor == 0:
                    break
            if deleted:
                logger.debug(f"Invalidated {deleted} keys prefix={prefix}")
            return deleted
        except Exception as e:
            logger.warning(f"Cache INVALIDATE failed prefix={prefix}: {e}")
            return 0

    @staticmethod
    def get_or_set(key: str, fetch_fn, ttl: int):
        cached = CacheService.get(key)
        if cached is not None:
            logger.debug(f"Cache HIT: {key}")
            return cached
        logger.debug(f"Cache MISS: {key}")
        data = fetch_fn()
        if data is not None:
            CacheService.set(key, data, ttl)
        return data

    @staticmethod
    def get_stats() -> dict:
        try:
            r = get_redis_cache()
            info = r.info()
            groups = {'products': 0, 'categories': 0, 'users': 0, 'statistics': 0, 'other': 0}
            cursor = 0
            while True:
                cursor, keys = r.scan(cursor, match="cache:*", count=200)
                for key in keys:
                    if 'products' in key: groups['products'] += 1
                    elif 'categories' in key: groups['categories'] += 1
                    elif 'users' in key: groups['users'] += 1
                    elif 'statistics' in key: groups['statistics'] += 1
                    else: groups['other'] += 1
                if cursor == 0:
                    break
            return {
                'hits': info.get('keyspace_hits',   0),
                'misses': info.get('keyspace_misses', 0),
                'memory_used': info.get('used_memory_human', 'n/a'),
                'total_keys': sum(groups.values()),
                'keys_by_group': groups,
            }
        except Exception as e:
            return {'error': str(e)}
