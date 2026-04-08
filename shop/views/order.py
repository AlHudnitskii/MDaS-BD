from django.shortcuts import render, redirect
from django.contrib import messages

from ..repositories.product import ProductRepository
from ..repositories.order import OrderRepository
from ..repositories.mongo_log import MongoLogRepository
from ..services.order_service import OrderService


def order_create_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart_detail')

    products = ProductRepository.get_by_ids(list(cart.keys()))
    products_by_id = {str(p['id']): p for p in products}
    cart_items, total = [], 0

    for product_id, item in cart.items():
        product = products_by_id.get(product_id)
        if not product:
            continue
        item_total = item['price'] * item['quantity']
        total += item_total
        cart_items.append({'product': product, 'quantity': item['quantity'], 'total_price': item_total})

    if request.method == 'POST':
        form_data = {
            'first_name': request.POST.get('first_name'),
            'last_name': request.POST.get('last_name'),
            'email': request.POST.get('email'),
            'city': request.POST.get('city'),
            'address': request.POST.get('address'),
            'postal_code': request.POST.get('postal_code'),
        }
        result = OrderService.create_from_cart(user_id, form_data, cart)
        if result['success']:
            request.session['cart']  = {}
            request.session.modified = True
            return redirect('order_success', order_id=result['order_id'])
        messages.error(request, result['error'])

    return render(request, 'orders/order/create.html', {'cart': cart_items, 'total_price': total})


def order_success_view(request, order_id):
    order = OrderRepository.get_details(order_id)
    if not order:
        messages.error(request, 'Order not found.')
        return redirect('product_list')
    return render(request, 'orders/order/created.html', {'order': order})


def process_payment_view(request, order_id):
    user_id = request.session.get('user_id')
    result = OrderService.process_payment(order_id, user_id)

    if result['success']:
        messages.success(request, f'Payment processed for order #{order_id}.')
    else:
        messages.error(request, result['error'])

    return redirect('profile')
