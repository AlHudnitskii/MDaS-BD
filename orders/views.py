import logging

from django.shortcuts import render
from django.shortcuts import redirect

from .models import OrderItem
from .forms import OrderCreateForm
from cart.cart import Cart

logger = logging.getLogger(__name__)


def order_create(request):
    """
    This view handles the creation of an order.
    It processes the cart data and saves it into an order instance.
    """

    cart = Cart(request)
    logger.info(f"Initiating order creation. Cart contains {[item['product'].name for item in cart]}.")

    if request.method == "POST":
        form = OrderCreateForm(request.POST, request=request)
        if form.is_valid():
            order = form.save()
            logger.info(f"Order {order.id} created by user {request.user.username if request.user.is_authenticated else 'Anonymous'}.")

            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item["product"],
                    price=item["price"],
                    quantity=item["quantity"],
                )
                logger.info(f"Added item '{item['product'].name}' (quantity: {item['quantity']}) to order {order.id}.")

            cart.clear()
            logger.info(f"Cart cleared after order {order.id} creation.")

            return render(request, "orders/order/created.html", {"order": order, "from": form})
        else:
            logger.warning(f"Invalid order creation form. Errors: {form.errors}")
            return render(request, "orders/order/create.html", {"cart": cart, "form": form})
    else:
        form = OrderCreateForm(request=request)
        logger.info("Displaying order creation form.")
        return render(request, "orders/order/create.html", {"cart": cart, "form": form})