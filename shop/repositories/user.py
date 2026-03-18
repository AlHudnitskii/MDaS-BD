from ..sql_manager import SQLManager


class UserRepository:

    @staticmethod
    def get_all_active_users() -> list[dict]:
        query = """
            SELECT id, username, email, first_name, last_name,
                   is_active, is_superuser, date_joined
            FROM users
            WHERE is_active = TRUE
            ORDER BY username
        """
        with SQLManager() as db:
            return db.execute(query)

    @staticmethod
    def get_user_by_username(username: str) -> dict | None:
        query = """
            SELECT id, username, email, first_name, last_name,
                   password, is_active, image_url, is_superuser,
                   date_joined, last_login
            FROM users
            WHERE username = %s
        """
        with SQLManager() as db:
            return db.execute_one(query, (username,))

    @staticmethod
    def get_user_by_id(user_id: str) -> dict | None:
        with SQLManager() as db:
            return db.execute_one("SELECT * FROM users WHERE id = %s", (str(user_id),))

    @staticmethod
    def check_password(username: str, password: str) -> bool:
        query = """
            SELECT (password = crypt(%s, password)) AS is_valid
            FROM users
            WHERE username = %s AND is_active = TRUE
        """
        with SQLManager() as db:
            result = db.execute_one(query, (password, username))
            return bool(result and result['is_valid'])

    @staticmethod
    def create_user(username: str, email: str, password: str,
                    first_name: str, last_name: str) -> dict | None:
        query = """
            INSERT INTO users (
                username, password, email, first_name, last_name,
                is_active, is_superuser, date_joined
            )
            VALUES (
                %s, crypt(%s, gen_salt('bf')), %s, %s, %s,
                TRUE, FALSE, NOW()
            )
            RETURNING id, username, email, first_name, last_name
        """
        with SQLManager() as db:
            return db.execute_one(query, (username, password, email, first_name, last_name))

    @staticmethod
    def username_or_email_exists(username: str, email: str) -> bool:
        with SQLManager() as db:
            result = db.execute_one(
                "SELECT id FROM users WHERE username = %s OR email = %s",
                (username, email)
            )
            return result is not None

    @staticmethod
    def update_last_login(user_id: str) -> None:
        with SQLManager() as db:
            db.execute_update(
                "UPDATE users SET last_login = NOW() WHERE id = %s::uuid",
                (user_id,)
            )

    @staticmethod
    def update_profile(user_id: str, **kwargs) -> None:
        allowed = {'first_name', 'last_name', 'email', 'username', 'image_url'}
        fields  = {k: v for k, v in kwargs.items() if k in allowed and v is not None}

        if not fields:
            return

        set_clause = ', '.join(f"{col} = %s" for col in fields)
        params     = list(fields.values()) + [user_id]

        with SQLManager() as db:
            db.execute_update(
                f"UPDATE users SET {set_clause} WHERE id = %s::uuid",
                tuple(params)
            )
