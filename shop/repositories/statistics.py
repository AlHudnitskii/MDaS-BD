from django.conf import settings
from ..sql_manager import SQLManager
from ..cache_service import CacheService, CacheKeys


class StatisticsRepository:
    @staticmethod
    def get_sales_summary() -> dict:
        return CacheService.get_or_set(
            key = CacheKeys.STATISTICS_SALES,
            fetch_fn = StatisticsRepository._fetch_sales_summary,
            ttl = settings.CACHE_TTL['statistics'],
        )

    @staticmethod
    def _fetch_sales_summary() -> dict:
        with SQLManager() as db:
            total_sales  = db.execute_one(
                "SELECT COALESCE(SUM(oi.price * oi.quantity), 0) AS total "
                "FROM order_items oi JOIN orders o ON oi.order_id = o.id WHERE o.paid = TRUE"
            )['total']
            total_orders = db.execute_one(
                "SELECT COUNT(*) AS count FROM orders WHERE paid = TRUE"
            )['count']
            avg_order    = db.execute_one(
                "SELECT COALESCE(AVG(t), 0) AS avg FROM "
                "(SELECT SUM(oi.price * oi.quantity) AS t "
                " FROM order_items oi JOIN orders o ON oi.order_id = o.id "
                " WHERE o.paid = TRUE GROUP BY o.id) AS sub"
            )['avg']
        return {
            'total_sales': float(total_sales),
            'total_orders': int(total_orders),
            'avg_order': float(avg_order),
        }

    @staticmethod
    def get_by_category() -> list[dict]:
        return CacheService.get_or_set(
            key = CacheKeys.STATISTICS_CATEGORIES,
            fetch_fn = StatisticsRepository._fetch_by_category,
            ttl = settings.CACHE_TTL['statistics'],
        )

    @staticmethod
    def _fetch_by_category() -> list[dict]:
        with SQLManager() as db:
            stats = db.execute("""
                SELECT c.name AS category_name,
                       COALESCE(SUM(oi.quantity), 0) AS total_sold,
                       COALESCE(SUM(oi.price * oi.quantity), 0) AS total_revenue
                FROM categories c
                LEFT JOIN products p ON c.id = p.category_id
                LEFT JOIN order_items oi ON p.id = oi.product_id
                LEFT JOIN orders o ON oi.order_id = o.id AND o.paid = TRUE
                GROUP BY c.id, c.name ORDER BY total_revenue DESC
            """)
        total_units = sum(float(s['total_sold'] or 0) for s in stats)
        total_revenue = sum(float(s['total_revenue'] or 0) for s in stats)
        for s in stats:
            sold = float(s['total_sold'] or 0)
            revenue = float(s['total_revenue'] or 0)
            s['unit_percentage'] = round(sold / total_units * 100, 1) if total_units else 0
            s['revenue_percentage'] = round(revenue / total_revenue * 100, 1) if total_revenue else 0
        return stats

    @staticmethod
    def invalidate():
        CacheService.invalidate_prefix(CacheKeys.PREFIX_STATISTICS)
        CacheService.invalidate_prefix("cache:products:top:")
