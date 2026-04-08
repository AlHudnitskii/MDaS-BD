from dataclasses import dataclass

from ..repositories.user import UserRepository
from ..repositories.mongo_log import MongoLogRepository
from ..auth.session_service import SessionService
from ..auth.jwt_service import (
    is_user_blacklisted, record_failed_login, clear_failed_attempts,
    create_access_token, create_refresh_token,
    revoke_token, get_blacklist_ttl,
)


@dataclass
class LoginResult:
    success: bool
    user_id: str | None = None
    username: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    error: str | None = None
    is_blocked: bool = False
    block_ttl: int = 0
    attempts_left: int = 0


class AuthService:
    @staticmethod
    def login(username: str, password: str, ip: str = '') -> LoginResult:
        if is_user_blacklisted(username):
            ttl = get_blacklist_ttl(username)
            return LoginResult(
                success=False, is_blocked=True, block_ttl=ttl,
                error=f'Account blocked. Try again in {ttl // 60}m {ttl % 60}s.',
            )

        user = UserRepository.get_user_by_username(username)

        if user and UserRepository.check_password(username, password):
            clear_failed_attempts(username)
            user_id = str(user['id'])
            access_token = create_access_token(user_id, username)
            refresh_token = create_refresh_token(user_id, username)

            UserRepository.update_last_login(user_id)
            SessionService.create(user_id, username, extra={'ip': ip})
            MongoLogRepository.log_action(
                user_id, 'USER_LOGIN',
                {'ip': ip, 'username': username}, 'SUCCESS',
            )

            return LoginResult(
                success=True, user_id=user_id, username=username,
                access_token=access_token, refresh_token=refresh_token,
            )

        count = record_failed_login(username)
        attempts_left = max(0, 3 - count)

        MongoLogRepository.log_action(
            str(user['id']) if user else None,
            'LOGIN_FAILED',
            {'ip': ip, 'username': username, 'attempt': count},
            'FAILED',
        )

        return LoginResult(
            success=False,
            error='Invalid username or password.',
            attempts_left=attempts_left,
        )

    @staticmethod
    def logout(user_id: str, username: str, access_token: str | None) -> None:
        if access_token:
            revoke_token(access_token)
        SessionService.delete(user_id)
        MongoLogRepository.log_action(
            user_id, 'USER_LOGOUT', {'username': username}, 'SUCCESS',
        )

        try:
            from ..core.pubsub import Publisher
            Publisher.user_logged_out(user_id)
        except Exception:
            pass


    @staticmethod
    def register(username: str, email: str, password: str,
                 first_name: str, last_name: str) -> dict:
        if len(password) < 6:
            return {'success': False, 'error': 'Password must be at least 6 characters.'}
        if UserRepository.username_or_email_exists(username, email):
            return {'success': False, 'error': 'Username or email already exists.'}

        user = UserRepository.create_user(username, email, password, first_name, last_name)
        if not user:
            return {'success': False, 'error': 'Registration failed.'}

        MongoLogRepository.log_action(
            str(user['id']), 'USER_REGISTER',
            {'username': username, 'email': email}, 'SUCCESS',
        )
        return {'success': True, 'user': user}
