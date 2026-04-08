from django.conf import settings

from ..core.postgres import SQLManager
from ..cache import CacheService, CacheKeys


class UserRepository:
    @staticmethod
    def get_all_active() -> list[dict]:
        return CacheService.get_or_set(
            key = CacheKeys.USERS_LIST,
            fetch_fn = UserRepository._fetch_all_active,
            ttl = settings.CACHE_TTL['users_list'],
        )

    @staticmethod
    def _fetch_all_active() -> list[dict]:
        with SQLManager() as db:
            return db.execute("""
                SELECT id, username, email, first_name, last_name,
                       is_active, is_superuser, date_joined
                FROM users WHERE is_active = TRUE ORDER BY username
            """)

    @staticmethod
    def get_all_with_roles() -> list[dict]:
        return CacheService.get_or_set(
            key = CacheKeys.USERS_ROLES,
            fetch_fn = UserRepository._fetch_all_with_roles,
            ttl = settings.CACHE_TTL['user_roles'],
        )

    @staticmethod
    def _fetch_all_with_roles() -> list[dict]:
        with SQLManager() as db:
            return db.execute("""
                SELECT u.id, u.username, u.email, u.first_name, u.last_name,
                       u.is_active, u.is_superuser, u.date_joined,
                       r.name AS role_name, ur.assigned_at AS role_assigned_at
                FROM users u
                LEFT JOIN user_roles ur ON u.id = ur.user_id
                LEFT JOIN roles r ON ur.role_id = r.id
                WHERE u.is_active = TRUE ORDER BY u.username
            """)

    @staticmethod
    def get_user_by_username(username: str) -> dict | None:
        with SQLManager() as db:
            return db.execute_one("""
                SELECT id, username, email, first_name, last_name,
                       password, is_active, image_url,
                       is_superuser, date_joined, last_login
                FROM users WHERE username = %s
            """, (username,))

    @staticmethod
    def get_user_by_id(user_id: str) -> dict | None:
        with SQLManager() as db:
            return db.execute_one(
                "SELECT * FROM users WHERE id = %s", (str(user_id),)
            )

    @staticmethod
    def check_password(username: str, password: str) -> bool:
        with SQLManager() as db:
            result = db.execute_one(
                "SELECT (password = crypt(%s, password)) AS is_valid "
                "FROM users WHERE username = %s AND is_active = TRUE",
                (password, username)
            )
            return bool(result and result['is_valid'])

    @staticmethod
    def create_user(username: str, email: str, password: str,
                    first_name: str, last_name: str) -> dict | None:
        with SQLManager() as db:
            user = db.execute_one("""
                INSERT INTO users (username, password, email, first_name, last_name,
                                   is_active, is_superuser, date_joined)
                VALUES (%s, crypt(%s, gen_salt('bf')), %s, %s, %s, TRUE, FALSE, NOW())
                RETURNING id, username, email, first_name, last_name
            """, (username, password, email, first_name, last_name))
        if user:
            UserRepository.invalidate()
        return user

    @staticmethod
    def username_or_email_exists(username: str, email: str) -> bool:
        with SQLManager() as db:
            return db.execute_one(
                "SELECT id FROM users WHERE username = %s OR email = %s",
                (username, email)
            ) is not None

    @staticmethod
    def update_last_login(user_id: str) -> None:
        with SQLManager() as db:
            db.execute_update(
                "UPDATE users SET last_login = NOW() WHERE id = %s::uuid", (user_id,)
            )

    @staticmethod
    def update_profile(user_id: str, **kwargs) -> None:
        allowed = {'first_name', 'last_name', 'email', 'username', 'image_url'}
        fields  = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not fields:
            return
        set_clause = ', '.join(f"{col} = %s" for col in fields)
        with SQLManager() as db:
            db.execute_update(
                f"UPDATE users SET {set_clause} WHERE id = %s::uuid",
                tuple(fields.values()) + (user_id,)
            )
        UserRepository.invalidate()


        try:
            from ..core.pubsub import Publisher
            Publisher.user_updated(user_id, kwargs.get('username', ''))
            Publisher.cache_invalidated(CacheKeys.PREFIX_USERS)
        except Exception:
            pass

    @staticmethod
    def invalidate():
        CacheService.invalidate_prefix(CacheKeys.PREFIX_USERS)
