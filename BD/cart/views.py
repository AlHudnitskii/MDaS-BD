import logging

from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from main.models import Product
from .cart import Cart
from .forms import CartAddProductForm, CartUpdateProductForm

logger = logging.getLogger(__name__)


@require_POST
def cart_add(request, product_id):
    """View to add a product to the cart."""

    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartAddProductForm(request.POST)

    logger.info(f"Attempting to add product '{product.name}' (ID: {product_id}) to cart.")

    if form.is_valid():
        cart_data = form.cleaned_data
        cart.add(
            product=product,
            quantity=cart_data["quantity"],
            override_quantity=cart_data["override"],
        )
        logger.info(
            f"Product '{product.name}' (ID: {product_id}) added to cart with quantity {cart_data['quantity']}, override: {cart_data['override']}."
        )
        return redirect("cart:cart_detail")
    else:
        logger.warning(
            f"Invalid form data for adding product '{product.name}' (ID: {product_id}) to cart. Errors: {form.errors}"
        )
        return redirect("cart:cart_detail")


@require_POST
def cart_remove(request, product_id):
    """View to remove a product from the cart."""

    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)

    logger.info(f"Attempting to remove product '{product.name}' (ID: {product_id}) from cart.")

    cart.remove(product)

    logger.info(f"Product '{product.name}' (ID: {product_id}) removed from cart.")
    return redirect("cart:cart_detail")


@require_POST
def cart_update(request, product_id):
    """View to update the quantity of a product in the cart."""

    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartUpdateProductForm(request.POST)

    if form.is_valid():
        cart_data = form.cleaned_data
        cart.add(
            product=product, quantity=cart_data["quantity"], override_quantity=True
        ) 

    return redirect("cart:cart_detail")


def cart_detail(request):
    """View to display the cart contents."""

    cart = Cart(request)
    logger.info("Displaying cart details.")
    return render(request, "cart/detail.html", {"cart": cart})