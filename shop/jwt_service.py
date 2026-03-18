import uuid
import datetime
import jwt

from django.conf import settings

from .redis_client import get_redis_cache


def _key_failed(username: str) -> str:
    return f"failed_attempts:{username}"

def _key_blacklist(username: str) -> str:
    return f"blacklist:{username}"

def _key_jwt_revoked(jti: str) -> str:
    return f"jwt_revoked:{jti}"


def record_failed_login(username: str) -> int:
    r = get_redis_cache()
    key = _key_failed(username)

    count = r.incr(key)
    if count == 1:
        r.expire(key, settings.LOGIN_BLOCK_DURATION)

    if count >= settings.LOGIN_MAX_ATTEMPTS:
        r.setex(_key_blacklist(username), settings.LOGIN_BLOCK_DURATION, "blocked")

    return count


def is_user_blacklisted(username: str) -> bool:
    return get_redis_cache().exists(_key_blacklist(username)) > 0


def get_blacklist_ttl(username: str) -> int:
    return get_redis_cache().ttl(_key_blacklist(username))


def get_failed_attempts(username: str) -> int:
    value = get_redis_cache().get(_key_failed(username))
    return int(value) if value else 0


def clear_failed_attempts(username: str) -> None:
    get_redis_cache().delete(_key_failed(username))


def create_access_token(user_id: str, username: str) -> str:
    now = datetime.datetime.utcnow()
    expire = now + datetime.timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        'sub': str(user_id),
        'username': username,
        'iat': now,
        'exp': expire,
        'type': 'access',
        'jti': str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str, username: str) -> str:
    now = datetime.datetime.utcnow()
    expire = now + datetime.timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        'sub': str(user_id),
        'username': username,
        'iat': now,
        'exp': expire,
        'type': 'refresh',
        'jti': str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY,
                             algorithms=[settings.JWT_ALGORITHM])
        jti = payload.get('jti')
        if jti and get_redis_cache().exists(_key_jwt_revoked(jti)):
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def revoke_token(token: str) -> bool:
    """
    Добавляет JTI токена в Redis с TTL = оставшееся время жизни токена.
    Когда токен естественно истечёт — Redis-ключ тоже удалится.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY,
                             algorithms=[settings.JWT_ALGORITHM],
                             options={"verify_exp": False})
        jti = payload.get('jti')
        exp = payload.get('exp')
        if not jti:
            return False
        now          = datetime.datetime.utcnow().timestamp()
        remaining    = max(0, int(exp - now)) if exp else 3600
        if remaining > 0:
            get_redis_cache().setex(_key_jwt_revoked(jti), remaining, "revoked")
        return True
    except jwt.InvalidTokenError:
        return False


def get_token_from_request(request) -> str | None:
    """
    Ищет токен в:
      1. Заголовке Authorization: Bearer <token>
      2. Cookie access_token
    """
    auth = request.META.get('HTTP_AUTHORIZATION', '')
    if auth.startswith('Bearer '):
        return auth[7:]
    return request.COOKIES.get('access_token')
