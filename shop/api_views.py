import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .auth.jwt_service import (
    is_user_blacklisted, record_failed_login, clear_failed_attempts,
    create_access_token, create_refresh_token,
    verify_token, revoke_token,
    get_blacklist_ttl, get_token_from_request,
)
from .cache import CacheService, CacheKeys
from .repositories.user import UserRepository


@csrf_exempt
@require_http_methods(["POST"])
def api_login(request):
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            return JsonResponse({'success': False, 'error': 'username and password required'}, status=400)

        if is_user_blacklisted(username):
            ttl = get_blacklist_ttl(username)
            return JsonResponse({
                'success': False, 'error': 'Account temporarily blocked',
                'retry_after_seconds': ttl,
                'retry_after_minutes': ttl // 60,
            }, status=403)

        user = UserRepository.get_user_by_username(username)
        if user and UserRepository.check_password(username, password):
            clear_failed_attempts(username)
            user_id = str(user['id'])
            return JsonResponse({
                'success': True,
                'access_token': create_access_token(user_id, username),
                'refresh_token': create_refresh_token(user_id, username),
                'token_type': 'Bearer',
                'expires_in': 3600,
            })

        count     = record_failed_login(username)
        remaining = max(0, 3 - count)
        return JsonResponse({
            'success': False, 'error': 'Invalid credentials',
            'attempts_remaining': remaining,
        }, status=401)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_logout(request):
    token = get_token_from_request(request)
    if not token:
        return JsonResponse({'success': False, 'error': 'No token provided'}, status=400)
    revoke_token(token)
    return JsonResponse({'success': True, 'message': 'Token revoked successfully'})


@require_http_methods(["GET"])
def api_token_verify(request):
    token = get_token_from_request(request)
    if not token:
        return JsonResponse({'valid': False, 'error': 'No token provided'}, status=401)
    payload = verify_token(token)
    if payload:
        return JsonResponse({
            'valid': True,
            'user_id': payload['sub'],
            'username': payload['username'],
            'expires': payload.get('exp'),
        })
    return JsonResponse({'valid': False, 'error': 'Invalid or expired token'}, status=401)


@require_http_methods(["GET"])
def api_cache_stats(request):
    return JsonResponse({'success': True, 'cache': CacheService.get_stats()})


@csrf_exempt
@require_http_methods(["POST"])
def api_cache_invalidate(request):
    try:
        data = json.loads(request.body or '{}')
        prefix = data.get('prefix', '')
        if prefix == 'all':
            deleted = CacheService.invalidate_prefix(CacheKeys.PREFIX_ALL)
        elif prefix:
            deleted = CacheService.invalidate_prefix(prefix)
        else:
            return JsonResponse({'success': False, 'error': 'prefix required'}, status=400)
        return JsonResponse({'success': True, 'deleted_keys': deleted, 'prefix': prefix})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
