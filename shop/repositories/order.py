import json
from ..sql_manager import SQLManager


class OrderRepository:

    @staticmethod
    def create_with_items(user_id: str, first_name: str, last_name: str,
                          email: str, city: str, address: str,
                          postal_code: str, items: list[dict]) -> str | None:
        with SQLManager() as db:
            result = db.execute_one("""
                SELECT create_one_order_with_items(
                    %s::uuid, %s, %s, %s, %s, %s, %s, %s::jsonb
                ) AS order_id
            """, (user_id, first_name, last_name, email,
                  city, address, postal_code, json.dumps(items)))
            return str(result['order_id']) if result else None

    @staticmethod
    def get_user_orders(user_id: str) -> list[dict]:
        with SQLManager() as db:
            return db.execute("""
                SELECT o.id, o.first_name, o.last_name, o.email,
                       o.city, o.address, o.postal_code,
                       o.created_at, o.paid,
                       COUNT(oi.id) AS items_count,
                       COALESCE(SUM(oi.price * oi.quantity), 0) AS total_amount
                FROM orders o
                LEFT JOIN order_items oi ON o.id = oi.order_id
                WHERE o.user_id = %s::uuid
                GROUP BY o.id ORDER BY o.created_at DESC
            """, (user_id,))

    @staticmethod
    def get_details(order_id: str) -> dict | None:
        with SQLManager() as db:
            order = db.execute_one("""
                SELECT o.id, o.user_id, u.username,
                       o.first_name, o.last_name, o.email,
                       o.city, o.address, o.postal_code, o.created_at, o.paid
                FROM orders o LEFT JOIN users u ON o.user_id = u.id
                WHERE o.id = %s::uuid
            """, (order_id,))
            if order:
                order['items'] = db.execute("""
                    SELECT oi.id, p.name AS product_name,
                           oi.quantity, oi.price, p.discount,
                           oi.price * oi.quantity AS item_total
                    FROM order_items oi JOIN products p ON oi.product_id = p.id
                    WHERE oi.order_id = %s::uuid
                """, (order_id,))
        return order

    @staticmethod
    def process_payment(order_id: str) -> None:
        from ..repositories.statistics import StatisticsRepository

        with SQLManager() as db:
            db.cursor.execute("CALL process_payment(%s::uuid)", (order_id,))
            db.connection.commit()

        StatisticsRepository.invalidate()
