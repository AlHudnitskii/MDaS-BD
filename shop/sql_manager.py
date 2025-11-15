import logging
import psycopg2

from typing import List, Dict, Any, Optional
from psycopg2.extras import RealDictCursor
from django.conf import settings

logger = logging.getLogger(__name__)


class SQLManager:   
    def __init__(self):
        self.connection = None
        self.cursor = None
    
    def __enter__(self):
        self.connection = psycopg2.connect(
            dbname=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT']
        )
        self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
    
    def execute(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        try:
            logger.info(f"Executing SQL: {query[:100]}... with params: {params}")
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            logger.info(f"Query returned {len(results)} rows")
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"SQL Error: {e}")
            raise
    
    def execute_one(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        try:
            logger.info(f"Executing SQL (one): {query[:100]}...")
            self.cursor.execute(query, params)
            result = self.cursor.fetchone()
            return dict(result) if result else None
        except Exception as e:
            logger.error(f"SQL Error: {e}")
            raise
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        try:
            logger.info(f"Executing UPDATE SQL: {query[:100]}...")
            self.cursor.execute(query, params)
            self.connection.commit()
            rowcount = self.cursor.rowcount
            logger.info(f"Query affected {rowcount} rows")
            return rowcount
        except Exception as e:
            logger.error(f"SQL Error: {e}")
            self.connection.rollback()
            raise
    
    def call_procedure(self, proc_name: str, params: tuple = None):
        try:
            logger.info(f"Calling procedure: {proc_name} with params: {params}")
            self.cursor.callproc(proc_name, params)
            self.connection.commit()
            logger.info(f"Procedure {proc_name} executed successfully")
        except Exception as e:
            logger.error(f"Procedure Error: {e}")
            self.connection.rollback()
            raise


class UserRepository: 
    @staticmethod
    def get_all_active_users() -> List[Dict[str, Any]]:
        query = """
            SELECT id, username, email, first_name, last_name, 
                   is_active, is_superuser, date_joined
            FROM users 
            WHERE is_active = TRUE
            ORDER BY username
        """
        with SQLManager() as db:
            return db.execute(query)
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
        query = """
            SELECT id, username, email, first_name, last_name,
                   password, is_active, is_superuser, date_joined, last_login
            FROM users
            WHERE username = %s
        """
        with SQLManager() as db:
            return db.execute_one(query, (username,))
    
    @staticmethod
    def create_user(username: str, email: str, password: str, 
                   first_name: str, last_name: str) -> Dict[str, Any]:
        query = """
            INSERT INTO users (
                id, username, password, email, first_name, last_name,
                is_active, is_staff, is_superuser, date_joined
            )
            VALUES (
                gen_random_uuid(), %s, hash_password(%s), %s, %s, %s,
                TRUE, FALSE, FALSE, NOW()
            )
            RETURNING id, username, email, first_name, last_name
        """
        with SQLManager() as db:
            return db.execute_one(query, (username, password, email, first_name, last_name))
    
    @staticmethod
    def update_user_profile(user_id: str, first_name: str, last_name: str, email: str):
        query = """
            UPDATE users
            SET first_name = %s, last_name = %s, email = %s
            WHERE id = %s::uuid
        """
        with SQLManager() as db:
            return db.execute_update(query, (first_name, last_name, email, user_id))
    
    @staticmethod
    def get_users_with_roles() -> List[Dict[str, Any]]:
        query = """
            SELECT DISTINCT
                u.id,
                u.username,
                u.email,
                u.first_name,
                u.last_name,
                r.name AS role_name
            FROM users AS u
            INNER JOIN user_roles AS ur ON u.id = ur.user_id
            INNER JOIN roles AS r ON ur.role_id = r.id
            WHERE u.is_active = TRUE
            ORDER BY u.username
        """
        with SQLManager() as db:
            return db.execute(query)


class ProductRepository:
    @staticmethod
    def get_all_products(category_slug: str = None, sort_by: str = 'name') -> List[Dict[str, Any]]:
        base_query = """
            SELECT 
                p.id,
                p.name,
                p.slug,
                p.description,
                p.price,
                p.discount,
                ROUND(p.price * (1 - p.discount), 2) as final_price,
                c.name AS category_name,
                c.slug AS category_slug,
                p.image,
                p.available,
                p.created_at
            FROM products AS p
            INNER JOIN categories AS c ON p.category_id = c.id
            WHERE p.available = TRUE
        """
        
        params = []
        if category_slug:
            base_query += " AND c.slug = %s"
            params.append(category_slug)
        
        sort_options = {
            'name': 'p.name ASC',
            'price': 'p.price ASC',
            '-price': 'p.price DESC',
            '-created': 'p.created_at DESC'
        }
        
        base_query += f" ORDER BY {sort_options.get(sort_by, 'p.name ASC')}"
        
        with SQLManager() as db:
            return db.execute(base_query, tuple(params) if params else None)
    
    @staticmethod
    def get_product_by_slug(slug: str) -> Optional[Dict[str, Any]]:
        query = """
            SELECT 
                p.id,
                p.name,
                p.slug,
                p.description,
                p.price,
                p.discount,
                ROUND(p.price * (1 - p.discount), 2) as final_price,
                c.name AS category_name,
                p.image,
                p.available
            FROM products AS p
            INNER JOIN categories AS c ON p.category_id = c.id
            WHERE p.slug = %s AND p.available = TRUE
        """
        with SQLManager() as db:
            return db.execute_one(query, (slug,))
    
    @staticmethod
    def search_products(search_query: str) -> List[Dict[str, Any]]:
        query = """
            SELECT 
                p.id,
                p.name,
                c.name AS category,
                p.price,
                p.discount,
                (p.price * (1 - p.discount)) AS final_price,
                p.description
            FROM products AS p
            INNER JOIN categories AS c ON p.category_id = c.id
            WHERE (p.name ILIKE %s OR p.description ILIKE %s)
                AND p.available = TRUE
            ORDER BY final_price DESC
        """
        search_pattern = f"%{search_query}%"
        with SQLManager() as db:
            return db.execute(query, (search_pattern, search_pattern))
    
    @staticmethod
    def get_top_products(limit: int = 10) -> List[Dict[str, Any]]:
        query = """
            SELECT 
                p.id,
                p.name,
                p.price,
                p.discount,
                COUNT(DISTINCT oi.order_id) as order_count,
                SUM(oi.quantity) as total_sold,
                SUM(oi.price * oi.quantity) as revenue
            FROM products p
            LEFT JOIN order_items oi ON p.id = oi.product_id
            LEFT JOIN orders o ON oi.order_id = o.id AND o.paid = TRUE
            WHERE p.available = TRUE
            GROUP BY p.id, p.name, p.price, p.discount
            ORDER BY total_sold DESC NULLS LAST, revenue DESC NULLS LAST
            LIMIT %s
        """
        with SQLManager() as db:
            return db.execute(query, (limit,))


class CategoryRepository:
    @staticmethod
    def get_all_categories() -> List[Dict[str, Any]]:
        query = """
            SELECT id, name, slug
            FROM categories
            ORDER BY name
        """
        with SQLManager() as db:
            return db.execute(query)
    
    @staticmethod
    def get_category_by_slug(slug: str) -> Optional[Dict[str, Any]]:
        query = """
            SELECT id, name, slug
            FROM categories
            WHERE slug = %s
        """
        with SQLManager() as db:
            return db.execute_one(query, (slug,))


class OrderRepository:
    @staticmethod
    def create_order_with_items(user_id: str, first_name: str, last_name: str,
                               email: str, city: str, address: str, 
                               postal_code: str, items: List[Dict]) -> str:
        import json
        items_json = json.dumps(items)
        
        query = """
            CALL create_order_with_items(
                %s::uuid, %s, %s, %s, %s, %s, %s, %s::jsonb
            )
        """
        
        with SQLManager() as db:
            db.cursor.execute(query, (
                user_id, first_name, last_name, email,
                city, address, postal_code, items_json
            ))
            db.connection.commit()
            
            db.cursor.execute("""
                SELECT id FROM orders 
                WHERE user_id = %s::uuid 
                ORDER BY created_at DESC 
                LIMIT 1
            """, (user_id,))
            result = db.cursor.fetchone()
            return str(result['id']) if result else None
    
    @staticmethod
    def get_user_orders(user_id: str) -> List[Dict[str, Any]]:
        query = """
            SELECT 
                o.id,
                o.first_name,
                o.last_name,
                o.email,
                o.city,
                o.address,
                o.postal_code,
                o.created_at,
                o.paid,
                COUNT(oi.id) as items_count,
                SUM(oi.price * oi.quantity) as total_amount
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            WHERE o.user_id = %s::uuid
            GROUP BY o.id
            ORDER BY o.created_at DESC
        """
        with SQLManager() as db:
            return db.execute(query, (user_id,))
    
    @staticmethod
    def get_order_details(order_id: str) -> Dict[str, Any]:
        query = """
            SELECT 
                o.id,
                o.user_id,
                u.username,
                o.first_name,
                o.last_name,
                o.email,
                o.city,
                o.address,
                o.postal_code,
                o.created_at,
                o.paid
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.id
            WHERE o.id = %s::uuid
        """
        
        items_query = """
            SELECT 
                oi.id,
                p.name as product_name,
                oi.quantity,
                oi.price,
                p.discount,
                oi.price * oi.quantity * (1 - COALESCE(p.discount, 0)) as item_total
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = %s::uuid
        """
        
        with SQLManager() as db:
            order = db.execute_one(query, (order_id,))
            if order:
                order['items'] = db.execute(items_query, (order_id,))
            return order
    
    @staticmethod
    def process_payment(order_id: str):
        query = "CALL process_payment(%s::uuid)"
        with SQLManager() as db:
            db.cursor.execute(query, (order_id,))
            db.connection.commit()


class StatisticsRepository:
    @staticmethod
    def get_sales_statistics() -> Dict[str, Any]:
        total_sales_query = """
            SELECT COALESCE(SUM(oi.price * oi.quantity), 0) as total
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            WHERE o.paid = TRUE
        """
        
        total_orders_query = """
            SELECT COUNT(*) as count
            FROM orders
            WHERE paid = TRUE
        """
        
        avg_order_query = """
            SELECT COALESCE(AVG(order_total), 0) as avg
            FROM (
                SELECT SUM(oi.price * oi.quantity) as order_total
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                WHERE o.paid = TRUE
                GROUP BY o.id
            ) as order_totals
        """
        
        with SQLManager() as db:
            total_sales = db.execute_one(total_sales_query)['total']
            total_orders = db.execute_one(total_orders_query)['count']
            avg_order = db.execute_one(avg_order_query)['avg']
            
            return {
                'total_sales': float(total_sales),
                'total_orders': int(total_orders),
                'avg_order': float(avg_order)
            }
    
    @staticmethod
    def get_category_statistics() -> List[Dict[str, Any]]:
        query = """
            SELECT 
                c.name AS category_name,
                COALESCE(SUM(oi.quantity), 0) as total_sold,
                COALESCE(SUM(oi.price * oi.quantity), 0) as total_revenue
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
            
            for stat in stats:
                sold = float(stat['total_sold'] or 0)
                revenue = float(stat['total_revenue'] or 0)
                
                stat['unit_percentage'] = (sold / total_units * 100) if total_units > 0 else 0
                stat['revenue_percentage'] = (revenue / total_revenue * 100) if total_revenue > 0 else 0
            
            return stats


class LogRepository:
    @staticmethod
    def cleanup_old_logs(days: int = 90):
        query = "CALL cleanup_old_logs(%s)"
        with SQLManager() as db:
            db.cursor.execute(query, (days,))
            db.connection.commit()
    
    @staticmethod
    def get_recent_logs(limit: int = 50) -> List[Dict[str, Any]]:
        query = """
            SELECT 
                le.id,
                le.user_id,
                u.username,
                le.action,
                le.details,
                le.status,
                le.timestamp
            FROM log_entries le
            LEFT JOIN users u ON le.user_id = u.id
            ORDER BY le.timestamp DESC
            LIMIT %s
        """
        with SQLManager() as db:
            return db.execute(query, (limit,))
    
    @staticmethod
    def log_action(user_id: str, action: str, details: dict, status: str = 'SUCCESS'):
        import json
        
        query = """
            INSERT INTO log_entries (user_id, action, details, status, timestamp)
            VALUES (%s::uuid, %s, %s::jsonb, %s, NOW())
        """
        
        with SQLManager() as db:
            db.execute_update(query, (user_id, action, json.dumps(details), status))