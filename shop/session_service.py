import json
import datetime
import logging

from django.conf import settings
from .redis_client import get_redis_sessions

logger = logging.getLogger(__name__)


class SessionService:

    @staticmethod
    def create(user_id: str, username: str,
               extra: dict | None = None) -> bool:
        try:
            r = get_redis_sessions()
            key = _session_key(user_id)

            data = {
                'user_id': user_id,
                'username': username,
                'created_at': datetime.datetime.utcnow().isoformat(),
                'last_seen': datetime.datetime.utcnow().isoformat(),
            }
            if extra:
                data.update(extra)

            r.setex(key, settings.CACHE_TTL['session'], json.dumps(data))
            return True

        except Exception as e:
            logger.warning(f"Session CREATE failed for user_id={user_id}: {e}")
            return False

    @staticmethod
    def get(user_id: str) -> dict | None:
        try:
            r = get_redis_sessions()
            key = _session_key(user_id)
            raw = r.get(key)
            if not raw:
                return None
            return json.loads(raw)
        except Exception as e:
            logger.warning(f"Session GET failed for user_id={user_id}: {e}")
            return None

    @staticmethod
    def refresh(user_id: str) -> bool:
        try:
            r = get_redis_sessions()
            key = _session_key(user_id)
            raw = r.get(key)
            if not raw:
                return False

            data = json.loads(raw)
            data['last_seen'] = datetime.datetime.utcnow().isoformat()

            r.setex(key, settings.CACHE_TTL['session'], json.dumps(data))
            return True

        except Exception as e:
            logger.warning(f"Session REFRESH failed for user_id={user_id}: {e}")
            return False

    @staticmethod
    def delete(user_id: str) -> bool:
        try:
            get_redis_sessions().delete(_session_key(user_id))
            return True
        except Exception as e:
            logger.warning(f"Session DELETE failed for user_id={user_id}: {e}")
            return False

    @staticmethod
    def exists(user_id: str) -> bool:
        try:
            return get_redis_sessions().exists(_session_key(user_id)) > 0
        except Exception:
            return False

    @staticmethod
    def get_ttl(user_id: str) -> int:
        try:
            return get_redis_sessions().ttl(_session_key(user_id))
        except Exception:
            return -2


def _session_key(user_id: str) -> str:
    return f"session:{user_id}"
