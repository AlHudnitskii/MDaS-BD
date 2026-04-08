from django.http import JsonResponse
from .jwt_service import verify_token, get_token_from_request


class JWTAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.jwt_user = None

        if request.path.startswith('/api/'):
            token = get_token_from_request(request)
            if token:
                payload = verify_token(token)
                if payload:
                    request.jwt_user = {
                        'user_id': payload['sub'],
                        'username': payload['username'],
                    }

        return self.get_response(request)


def jwt_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not getattr(request, 'jwt_user', None):
            return JsonResponse(
                {'success': False, 'error': 'Authentication required. Provide Bearer token.'},
                status=401
            )
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper
