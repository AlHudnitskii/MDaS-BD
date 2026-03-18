from ..repositories.order   import OrderRepository
from ..repositories.product import ProductRepository
from ..repositories.log     import LogRepository


class OrderService:
    @staticmethod
    def create_from_cart(user_id: str, form_data: dict, cart: dict) -> dict:
        if not cart:
            return {'success': False, 'error': 'Cart is empty.'}

        product_ids = list(cart.keys())
        products = ProductRepository.get_by_ids(product_ids)
        products_by_id = {str(p['id']): p for p in products}

        items = []
        for product_id, item_data in cart.items():
            if product_id not in products_by_id:
                return {'success': False, 'error': f'Product {product_id} not found.'}
            items.append({'product_id': product_id, 'quantity': item_data['quantity']})

        try:
            order_id = OrderRepository.create_with_items(
                user_id=user_id,
                items=items,
                **form_data
            )
        except Exception as e:
            return {'success': False, 'error': str(e)}

        if not order_id:
            return {'success': False, 'error': 'Failed to create order.'}

        LogRepository.log_action(
            user_id, 'ORDER_CREATED',
            {'order_id': order_id, 'items_count': len(items)},
            'SUCCESS'
        )

        return {'success': True, 'order_id': order_id}

    @staticmethod
    def process_payment(order_id: str, user_id: str) -> dict:
        try:
            OrderRepository.process_payment(order_id)
            LogRepository.log_action(
                user_id, 'ORDER_PAID',
                {'order_id': order_id},
                'SUCCESS'
            )
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
