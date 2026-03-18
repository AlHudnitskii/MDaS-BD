from ..sql_manager import SQLManager


class StatisticsRepository:

    @staticmethod
    def get_sales_summary() -> dict:
        with SQLManager() as db:
            total_sales = db.execute_one(
                "SELECT COALESCE(SUM(oi.price * oi.quantity), 0) AS total "
                "FROM order_items oi JOIN orders o ON oi.order_id = o.id WHERE o.paid = TRUE"
            )['total']
            total_orders = db.execute_one(
                "SELECT COUNT(*) AS count FROM orders WHERE paid = TRUE"
            )['count']
            avg_order = db.execute_one(
                "SELECT COALESCE(AVG(order_total), 0) AS avg FROM "
                "(SELECT SUM(oi.price * oi.quantity) AS order_total "
                " FROM order_items oi JOIN orders o ON oi.order_id = o.id "
                " WHERE o.paid = TRUE GROUP BY o.id) AS t"
            )['avg']

        return {
            'total_sales': float(total_sales),
            'total_orders': int(total_orders),
            'avg_order': float(avg_order),
        }

    @staticmethod
    def get_by_category() -> list[dict]:
        query = """
            SELECT
                c.name AS category_name,
                COALESCE(SUM(oi.quantity), 0) AS total_sold,
                COALESCE(SUM(oi.price * oi.quantity), 0) AS total_revenue
            FROM categories c
            LEFT JOIN products p ON c.id = p.category_id
            LEFT JOIN order_items oi ON p.id = oi.product_id
            LEFT JOIN orders o ON oi.order_id = o.id AND o.paid = TRUE
            GROUP BY c.id, c.name
            ORDER BY total_revenue DESC
        """
        with SQLManager() as db:
            stats = db.execute(query)

        total_units = sum(float(s['total_sold'] or 0) for s in stats)
        total_revenue = sum(float(s['total_revenue'] or 0) for s in stats)

        for s in stats:
            sold = float(s['total_sold'] or 0)
            revenue = float(s['total_revenue'] or 0)
            s['unit_percentage'] = (sold / total_units * 100) if total_units   else 0
            s['revenue_percentage'] = (revenue / total_revenue * 100) if total_revenue else 0

        return stats
