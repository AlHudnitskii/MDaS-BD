import uuid
from ..sql_manager import SQLManager


class ProductRepository:
    _BASE_SELECT = """
        SELECT
            p.id, p.name, p.slug, p.description,
            p.price, p.discount,
            ROUND(p.price * (1 - p.discount), 2) AS final_price,
            c.name  AS category_name,
            c.slug  AS category_slug,
            p.image, p.available, p.created_at
        FROM products AS p
        INNER JOIN categories AS c ON p.category_id = c.id
    """

    _SORT_MAP = {
        'name': 'p.name ASC',
        'price': 'p.price ASC',
        '-price': 'p.price DESC',
        '-created': 'p.created_at DESC',
    }

    @classmethod
    def get_all(cls, category_slug: str | None = None,
                sort_by: str = 'name') -> list[dict]:
        query  = cls._BASE_SELECT + " WHERE p.available = TRUE"
        params = []

        if category_slug:
            query += " AND c.slug = %s"
            params.append(category_slug)

        order = cls._SORT_MAP.get(sort_by, 'p.name ASC')
        query += f" ORDER BY {order}"

        with SQLManager() as db:
            return db.execute(query, tuple(params) if params else None)

    @classmethod
    def get_by_slug(cls, slug: str) -> dict | None:
        query = cls._BASE_SELECT + " WHERE p.slug = %s AND p.available = TRUE"
        with SQLManager() as db:
            return db.execute_one(query, (slug,))

    @staticmethod
    def get_by_ids(product_ids: list) -> list[dict]:
        uids = []
        for pid in product_ids:
            try:
                uids.append(uuid.UUID(str(pid)))
            except ValueError:
                continue

        if not uids:
            return []

        placeholders = ','.join(['%s'] * len(uids))
        query = f"""
            SELECT
                p.id, p.name, p.slug, p.description,
                p.price, p.discount,
                ROUND(p.price * (1 - p.discount), 2) AS final_price,
                c.name AS category_name, p.image, p.available
            FROM products AS p
            INNER JOIN categories AS c ON p.category_id = c.id
            WHERE p.id IN ({placeholders})
        """
        with SQLManager() as db:
            return db.execute(query, tuple(uids))

    @staticmethod
    def search(query_text: str) -> list[dict]:
        pattern = f"%{query_text}%"
        query   = """
            SELECT
                p.id, p.name, c.name AS category_name,
                p.price, p.discount,
                ROUND(p.price * (1 - p.discount), 2) AS final_price,
                p.description, p.image
            FROM products AS p
            INNER JOIN categories AS c ON p.category_id = c.id
            WHERE (p.name ILIKE %s OR p.description ILIKE %s)
              AND p.available = TRUE
            ORDER BY p.name ASC
        """
        with SQLManager() as db:
            return db.execute(query, (pattern, pattern))

    @staticmethod
    def get_top(limit: int = 10) -> list[dict]:
        query = """
            SELECT
                p.id, p.name, p.price, p.discount, p.image,
                COUNT(DISTINCT oi.order_id)         AS order_count,
                COALESCE(SUM(oi.quantity), 0)       AS total_sold,
                COALESCE(SUM(oi.price * oi.quantity), 0) AS revenue
            FROM products p
            LEFT JOIN order_items oi ON p.id = oi.product_id
            LEFT JOIN orders o ON oi.order_id = o.id AND o.paid = TRUE
            WHERE p.available = TRUE
            GROUP BY p.id, p.name, p.price, p.discount, p.image
            ORDER BY total_sold DESC, revenue DESC
            LIMIT %s
        """
        with SQLManager() as db:
            return db.execute(query, (limit,))
