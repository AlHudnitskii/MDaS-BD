from django.shortcuts import redirect
from django.urls import reverse


class SessionAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.user_authenticated = request.session.get('is_authenticated', False)
        request.user_id = request.session.get('user_id')
        request.username = request.session.get('username')
        return self.get_response(request)


class CartMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if 'cart' not in request.session:
            request.session['cart'] = {}
        cart = request.session.get('cart', {})
        request.cart_quantity = sum(item.get('quantity', 0) for item in cart.values())
        return self.get_response(request)
