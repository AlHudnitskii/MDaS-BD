from .cart import Cart


def cart(request):
    """Context processor to make the cart available in templates."""
    return {"cart": Cart(request)}