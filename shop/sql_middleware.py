from django.shortcuts import redirect
from django.urls import reverse


class SessionAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        request.user_authenticated = request.session.get('is_authenticated', False)
        request.user_id = request.session.get('user_id')
        request.username = request.session.get('username')
        
        response = self.get_response(request)
        return response


class LoginRequiredMiddleware:
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
        is_exempt = any(request.path.startswith(url) for url in self.EXEMPT_URLS)
        
        if not is_exempt:
            if not request.session.get('is_authenticated'):
                login_url = reverse('login')
                return redirect(f'{login_url}?next={request.path}')
        
        response = self.get_response(request)
        return response


class CartMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if 'cart' not in request.session:
            request.session['cart'] = {}
        
        cart = request.session.get('cart', {})
        request.cart_quantity = sum(item.get('quantity', 0) for item in cart.values())
        
        response = self.get_response(request)
        return response