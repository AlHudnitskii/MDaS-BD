def auth_context(request):
    return {
        'user_authenticated': request.session.get('is_authenticated', False),
        'user_id': request.session.get('user_id'),
        'username': request.session.get('username'),
    }


def cart_context(request):
    cart = request.session.get('cart', {})
    cart_quantity = sum(item.get('quantity', 0) for item in cart.values())
    return {
        'cart': cart,
        'cart_quantity': cart_quantity,
    }
