from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from ..repositories.product import ProductRepository


def cart_detail_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0

    for product_id, item_data in cart.items():
        product = ProductRepository.get_by_slug(item_data.get('slug'))
        if product:
            quantity = item_data.get('quantity', 1)
            item_total = float(product['final_price']) * quantity
            total += item_total
            cart_items.append({'product': product, 'product_id': product_id,
                               'quantity': quantity, 'total': item_total})

    return render(request, 'cart/detail.html',
                  {'cart_items': cart_items, 'total_price': total})


@require_http_methods(["POST"])
def cart_add_view(request, product_id):
    product = ProductRepository.get_by_slug(request.POST.get('slug'))
    if not product:
        messages.error(request, 'Product not found.')
        return redirect('product_list')

    cart = request.session.get('cart', {})
    quantity = int(request.POST.get('quantity', 1))

    if product_id in cart:
        cart[product_id]['quantity'] += quantity
    else:
        cart[product_id] = {
            'slug': product['slug'], 'name': product['name'],
            'price': float(product['final_price']), 'quantity': quantity,
        }

    request.session['cart'] = cart
    request.session.modified = True
    messages.success(request, f"{product['name']} added to cart.")
    return redirect('cart_detail')


@require_http_methods(["POST"])
def cart_remove_view(request, product_id):
    cart = request.session.get('cart', {})
    if product_id in cart:
        del cart[product_id]
        request.session['cart']  = cart
        request.session.modified = True
        messages.success(request, 'Item removed from cart.')
    return redirect('cart_detail')
