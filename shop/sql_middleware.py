"""
Middleware для аутентификации через сессии (без Django Auth)
"""
from django.shortcuts import redirect
from django.urls import reverse


class SessionAuthMiddleware:
    """
    Middleware для проверки аутентификации пользователя через сессии
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Проверяем, аутентифицирован ли пользователь
        request.user_authenticated = request.session.get('is_authenticated', False)
        request.user_id = request.session.get('user_id')
        request.username = request.session.get('username')
        
        response = self.get_response(request)
        return response


class LoginRequiredMiddleware:
    """
    Middleware для защиты страниц, требующих авторизации
    """
    
    # Список URL, которые не требуют авторизации
    EXEMPT_URLS = [
        '/login/',
        '/register/',
        '/logout/',
        '/',
        '/shop/',
        '/about/',
        '/contacts/',
        '/api/',
        '/admin/',
        '/static/',
        '/media/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Проверяем, требуется ли авторизация для данного URL
        is_exempt = any(request.path.startswith(url) for url in self.EXEMPT_URLS)
        
        if not is_exempt:
            if not request.session.get('is_authenticated'):
                # Перенаправляем на страницу входа с указанием next
                login_url = reverse('login')
                return redirect(f'{login_url}?next={request.path}')
        
        response = self.get_response(request)
        return response


class CartMiddleware:
    """
    Middleware для работы с корзиной через сессии
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Инициализируем корзину в сессии, если её нет
        if 'cart' not in request.session:
            request.session['cart'] = {}
        
        # Добавляем количество товаров в корзине в request
        cart = request.session.get('cart', {})
        request.cart_quantity = sum(item.get('quantity', 0) for item in cart.values())
        
        response = self.get_response(request)
        return response