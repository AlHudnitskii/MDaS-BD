from decimal import Decimal
from django.conf import settings
from main.models import Product
from .forms import CartUpdateProductForm


class Cart:
    def __init__(self, request):
        """Initialize the cart."""
        self.session = request.session
        cart_data = self.session.get(settings.CART_SESSION_ID)
        if not cart_data:
            cart_data = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart_data

    def add(self, product, quantity=1, override_quantity=False):
        """Add a product to the cart, or update its quantity."""
        product_id = str(product.id)

        if product_id not in self.cart:
            self.cart[product_id] = {"quantity": 0, "price": str(product.price)}

        if override_quantity:
            self.cart[product_id]["quantity"] = quantity
        else:
            self.cart[product_id]["quantity"] += quantity
        self._save() 

    def _save(self): 
        """Mark the session as modified to ensure it gets saved."""
        self.session.modified = True

    def remove(self, product):
        """Remove a product from the cart."""
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self._save()  

    def __iter__(self):
        """Iterate over the items in the cart and get the products from the database."""
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()  

        for product in products:
            product_id = str(product.id)
            cart[product_id]["product"] = product
            cart[product_id][
                "update_quantity_form"
            ] = CartUpdateProductForm(
                initial={
                    "quantity": cart[product_id]["quantity"],
                    "override": True,
                }
            )

        for item in cart.values():
            yield item

    def __len__(self):
        """Count all items in the cart."""
        return sum(item["quantity"] for item in self.cart.values())

    def clear(self):
        """Remove the cart from the session."""
        del self.session[settings.CART_SESSION_ID]

    def get_total_price(self):
        """Calculate the total cost of the items in the cart, applying discounts."""

        total = sum(
            (
                Decimal(item["price"])
                - (Decimal(item["price"]) * Decimal(item["product"].discount / 100))
            )
            * item["quantity"]
            for item in self.cart.values()
        )
        return format(total, ".2f")