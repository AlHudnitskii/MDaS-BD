import uuid
import psycopg2
from psycopg2.extras import RealDictCursor
from .sql_pool import get_connection_pool
#Пул connections + нагрузочное тестирование сдедать
#API пару эндпоинтов + Postman
#В ОДИН из эндпоинтов вызыв хран процедуру + nested transactions 
class SQLManager:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.pool = get_connection_pool()
    
    def __enter__(self):
        self.connection = self.pool.getconn()
        self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.connection.commit() 
        else:
            self.connection.rollback()
        
        if self.cursor:
            self.cursor.close()
        
        if self.connection:
            self.pool.putconn(self.connection)
        
        return False
    
    def execute(self, query, params=None):
        if params is None:
            self.cursor.execute(query)
        else:
            self.cursor.execute(query, params)
        results = self.cursor.fetchall()
        return [dict(row) for row in results]
    
    def execute_one(self, query, params=None):
        if params is None:
            self.cursor.execute(query)
        else:
            self.cursor.execute(query, params)
        result = self.cursor.fetchone()
        return dict(result) if result else None
    
    def execute_update(self, query, params=None):
        if params is None:
            self.cursor.execute(query)
        else:
            self.cursor.execute(query, params)
        self.connection.commit()
        return self.cursor.rowcount
    
    def call_procedure(self, proc_name, params):
        self.cursor.callproc(proc_name, params)
        self.connection.commit()
    
    def begin_nested(self):
        savepoint_name = f"sp_{id(self)}"
        self.cursor.execute(f"SAVEPOINT {savepoint_name}")
        return savepoint_name
    
    def rollback_to(self, savepoint_name):
        self.cursor.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
    
    def release_savepoint(self, savepoint_name):
        self.cursor.execute(f"RELEASE SAVEPOINT {savepoint_name}")


class UserRepository:
    @staticmethod
    def get_all_active_users():
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
    def get_user_by_username(username):
        query = """
            SELECT id, username, email, first_name, last_name,
                   password, is_active, image_url, is_superuser, date_joined, last_login
            FROM users
            WHERE username = %s
        """
        with SQLManager() as db:
            return db.execute_one(query, (username,))
    
    @staticmethod
    def get_user_by_id(user_id):
        with SQLManager() as db:
            query = "SELECT * FROM users WHERE id = %s"
            return db.execute_one(query, (str(user_id),))

    
    @staticmethod
    def create_user(username, email, password, first_name, last_name):
        create_user_query = """
            INSERT INTO users (
                id, username, password, email, first_name, last_name,
                is_active, is_superuser, date_joined
            )
            VALUES (
                gen_random_uuid(), %s, crypt(%s, gen_salt('bf')), %s, %s, %s,
                TRUE, FALSE, NOW()
            )
            RETURNING id, username, email, first_name, last_name
        """

        insert_role_query = """
            INSERT INTO user_roles (
                id, user_id, role_id, assigned_at, assigned_by_id
            )
            VALUES (
                gen_random_uuid(), %s::uuid, '550e8400-e29b-41d4-a716-446655440102'::uuid,
                NOW(), '550e8400-e29b-41d4-a716-446655440001'::uuid
            )
        """

        with SQLManager() as db:
            user = db.execute_one(create_user_query, (username, password, email, first_name, last_name))

            if not user:
                return None

            user_id = uuid(user["id"])
            db.execute(insert_role_query, (user_id,))

            return user

    
    @staticmethod
    def update_user_profile(user_id, first_name=None, last_name=None, email=None, username=None, image_url=None):
        set_parts = []
        params = []

        if first_name is not None:
            set_parts.append("first_name = %s")
            params.append(first_name)
        if last_name is not None:
            set_parts.append("last_name = %s")
            params.append(last_name)
        if email is not None:
            set_parts.append("email = %s")
            params.append(email)
        if username is not None:
            set_parts.append("username = %s")
            params.append(username)
        if image_url is not None:
            set_parts.append("image_url = %s")
            params.append(image_url)

        if not set_parts:
            return  

        query = f"""
            UPDATE users
            SET {', '.join(set_parts)}
            WHERE id = %s::uuid
        """
        params.append(user_id)

        with SQLManager() as db:
            db.execute_update(query, tuple(params))


class ProductRepository:
    @staticmethod
    def get_all_products(category_slug=None, sort_by='name'):
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
    def get_product_by_slug(slug):
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
    def get_product_images(product_id):
        query = """
            SELECT id, image, alt_text, is_main, display_order, created_at
            FROM product_images
            WHERE product_id = %s::uuid
            ORDER BY is_main DESC, display_order ASC, created_at ASC
        """
        with SQLManager() as db:
            return db.execute(query, (product_id,))
    
    @staticmethod
    def search_products(search_query):
        query = """
            SELECT 
                p.id,
                p.name,
                c.name AS category_name,
                p.price,
                p.discount,
                ROUND(p.price * (1 - p.discount), 2) AS final_price,
                p.description,
                p.image
            FROM products AS p
            INNER JOIN categories AS c ON p.category_id = c.id
            WHERE (p.name ILIKE %s OR p.description ILIKE %s)
                AND p.available = TRUE
            ORDER BY p.name ASC
        """
        search_pattern = f"%{search_query}%"
        with SQLManager() as db:
            return db.execute(query, (search_pattern, search_pattern))
    
    @staticmethod
    def get_top_products(limit=10):
        query = """
            SELECT 
                p.id,
                p.name,
                p.price,
                p.discount,
                p.image,
                COUNT(DISTINCT oi.order_id) as order_count,
                COALESCE(SUM(oi.quantity), 0) as total_sold,
                COALESCE(SUM(oi.price * oi.quantity), 0) as revenue
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

    @staticmethod
    def get_products_by_ids(product_ids):
        if not product_ids:
            return []

        uids = []
        for pid in product_ids:
            try:
                uids.append(uuid.UUID(str(pid)))
            except Exception:
                continue

        if not uids:
            return []

        placeholders = ','.join(['%s'] * len(uids))
        query = f"""
            SELECT 
                p.id,
                p.name,
                p.slug,
                p.description,
                p.price,
                p.discount,
                ROUND(p.price * (1 - p.discount), 2) AS final_price,
                c.name AS category_name,
                p.image,
                p.available
            FROM products AS p
            INNER JOIN categories AS c ON p.category_id = c.id
            WHERE p.id IN ({placeholders})
        """

        with SQLManager() as db:
            return db.execute(query, tuple(uids))


class CategoryRepository:
    @staticmethod
    def get_all_categories():
        query = """
            SELECT id, name, slug
            FROM categories
            ORDER BY name
        """
        with SQLManager() as db:
            return db.execute(query)
    
    @staticmethod
    def get_category_by_slug(slug):
        query = """
            SELECT id, name, slug
            FROM categories
            WHERE slug = %s
        """
        with SQLManager() as db:
            return db.execute_one(query, (slug,))


class OrderRepository:
    @staticmethod
    def create_order_with_items(user_id, first_name, last_name, email,
                                city, address, postal_code, items):
        import json
        
        items_json = json.dumps(items)
        
        query = """
            SELECT create_one_order_with_items(
                %s::uuid, %s, %s, %s, %s, %s, %s, %s::jsonb
            ) as order_id
        """
        
        with SQLManager() as db:
            result = db.execute_one(query, (
                user_id, first_name, last_name, email,
                city, address, postal_code, items_json
            ))
            return str(result['order_id']) if result else None
    
    @staticmethod
    def get_user_orders(user_id):
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
                COALESCE(SUM(oi.price * oi.quantity), 0) as total_amount
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            WHERE o.user_id = %s::uuid
            GROUP BY o.id
            ORDER BY o.created_at DESC
        """
        with SQLManager() as db:
            return db.execute(query, (user_id,))
    
    @staticmethod
    def get_order_details(order_id):
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
                oi.price * oi.quantity as item_total
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
    def process_payment(order_id):
        query = "CALL process_payment(%s::uuid)"
        with SQLManager() as db:
            db.cursor.execute(query, (order_id,))
            db.connection.commit()


class StatisticsRepository:
    @staticmethod
    def get_sales_statistics():
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
    def get_category_statistics():
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
    def cleanup_old_logs(days=90):
        count_query = """
            SELECT COUNT(*) as count 
            FROM log_entries 
            WHERE timestamp < NOW() - INTERVAL '%s days'
        """
    
        delete_query = """
            DELETE FROM log_entries
            WHERE timestamp < NOW() - INTERVAL '%s days'
        """
        
        with SQLManager() as db:
            count_result = db.execute(count_query, (days,))
            deleted_count = count_result[0]['count'] if count_result else 0
            
            if deleted_count > 0:
                db.cursor.execute(delete_query, (days,))
                db.connection.commit()
            
            return deleted_count
    
    @staticmethod
    def get_recent_logs(limit=50):
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
    def log_action(user_id, action, details, status='SUCCESS'):
        import json
        
        query = """
            INSERT INTO log_entries (user_id, action, details, status, timestamp)
            VALUES (%s::uuid, %s, %s::jsonb, %s, NOW())
        """
        
        with SQLManager() as db:
            db.execute_update(query, (user_id, action, json.dumps(details), status))

    @staticmethod
    def get_filtered_logs(action_type=None, status=None, user_filter=None, days=7):
        conditions = ["l.timestamp > NOW() - INTERVAL '%s days'"]
        params = [days]
        
        if action_type:
            conditions.append("l.action = %s")
            params.append(action_type)
        
        if status:
            conditions.append("l.status = %s")
            params.append(status)
        
        if user_filter:
            conditions.append("(u.username ILIKE %s OR u.email ILIKE %s)")
            params.extend([f"%{user_filter}%", f"%{user_filter}%"])
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
            SELECT 
                l.id,
                l.user_id,
                l.action,
                l.details,
                l.status,
                l.timestamp,
                u.username,
                u.email,
                u.image_url
            FROM log_entries l
            LEFT JOIN users u ON l.user_id = u.id
            WHERE {where_clause}
            ORDER BY l.timestamp DESC
        """
        
        with SQLManager() as db:
            result = db.execute(query, tuple(params))
            return result if result else []
    
    @staticmethod
    def get_logs_statistics():
        query = """
            SELECT 
                COUNT(*) as total_logs,
                COUNT(*) FILTER (WHERE status = 'SUCCESS') as success_count,
                COUNT(*) FILTER (WHERE status = 'ERROR') as error_count,
                COUNT(*) FILTER (WHERE timestamp > NOW() - INTERVAL '1 day') as today_logs,
                COUNT(*) FILTER (WHERE timestamp > NOW() - INTERVAL '7 days') as week_logs,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(DISTINCT action) as unique_actions
            FROM log_entries
            WHERE timestamp > NOW() - INTERVAL '30 days'
        """
        
        with SQLManager() as db:
            result = db.execute(query)
            return result[0] if result else None
    
    @staticmethod
    def get_unique_action_types():
        query = """
            SELECT DISTINCT action
            FROM log_entries
            WHERE timestamp > NOW() - INTERVAL '30 days'
            ORDER BY action
        """
        
        with SQLManager() as db:
            result = db.execute(query)
            return [row['action'] for row in result] if result else []
    
    @staticmethod
    def get_action_type_stats():
        query = """
            SELECT 
                action,
                COUNT(*) as count,
                COUNT(*) FILTER (WHERE status = 'SUCCESS') as success_count,
                COUNT(*) FILTER (WHERE status = 'ERROR') as error_count
            FROM log_entries
            WHERE timestamp > NOW() - INTERVAL '7 days'
            GROUP BY action
            ORDER BY count DESC
            LIMIT 10
        """
        
        with SQLManager() as db:
            result = db.execute(query)
            return result if result else []

class UserNoteRepository:
    @staticmethod
    def create_note(user_id, title, content):
        query = """
            INSERT INTO user_notes (user_id, title, content, created_at, updated_at)
            VALUES (%s::uuid, %s, %s, NOW(), NOW())
            RETURNING id, title, content, created_at, updated_at
        """
        with SQLManager() as db:
            return db.execute_one(query, (user_id, title, content))
    
    @staticmethod
    def get_user_notes(user_id):
        query = """
            SELECT id, title, content, created_at, updated_at
            FROM user_notes
            WHERE user_id = %s::uuid
            ORDER BY updated_at DESC
        """
        with SQLManager() as db:
            return db.execute(query, (user_id,))
    
    @staticmethod
    def get_note_by_id(note_id):
        query = """
            SELECT id, user_id, title, content, created_at, updated_at
            FROM user_notes
            WHERE id = %s::uuid
        """
        with SQLManager() as db:
            return db.execute_one(query, (note_id,))
    
    @staticmethod
    def update_note(note_id, title, content):
        query = """
            UPDATE user_notes
            SET title = %s, content = %s, updated_at = NOW()
            WHERE id = %s::uuid
        """
        with SQLManager() as db:
            return db.execute_update(query, (title, content, note_id))
    
    @staticmethod
    def delete_note(note_id):
        query = "DELETE FROM user_notes WHERE id = %s::uuid"
        with SQLManager() as db:
            return db.execute_update(query, (note_id,))


class WishlistRepository:
    @staticmethod
    def create_wishlist(user_id, name, description=''):
        query = """
            INSERT INTO wishlists (user_id, name, description, created_at, updated_at)
            VALUES (%s::uuid, %s, %s, NOW(), NOW())
            RETURNING id, name, description, created_at
        """
        with SQLManager() as db:
            return db.execute_one(query, (user_id, name, description))
    
    @staticmethod
    def get_user_wishlists(user_id):
        query = """
            SELECT 
                w.id,
                w.name,
                w.description,
                w.created_at,
                COUNT(wi.id) as items_count
            FROM wishlists w
            LEFT JOIN wishlist_items wi ON w.id = wi.wishlist_id
            WHERE w.user_id = %s::uuid
            GROUP BY w.id, w.name, w.description, w.created_at
            ORDER BY w.created_at DESC
        """
        with SQLManager() as db:
            return db.execute(query, (user_id,))
    
    @staticmethod
    def get_wishlist(wishlist_id):
        query = """
            SELECT 
                w.id,
                w.user_id,
                w.name,
                w.description,
                w.created_at,
                w.updated_at
            FROM wishlists w
            WHERE w.id = %s::uuid
        """
        with SQLManager() as db:
            return db.execute_one(query, (wishlist_id,))
    
    @staticmethod
    def get_wishlist_items(wishlist_id):
        query = """
            SELECT 
                wi.id as wishlist_item_id,
                p.id as product_id,
                p.name,
                p.slug,
                p.price,
                p.discount,
                ROUND(p.price * (1 - p.discount), 2) as final_price,
                p.image,
                c.name as category_name,
                wi.created_at as added_at
            FROM wishlist_items wi
            JOIN products p ON wi.product_id = p.id
            JOIN categories c ON p.category_id = c.id
            WHERE wi.wishlist_id = %s::uuid
            ORDER BY wi.created_at DESC
        """
        with SQLManager() as db:
            return db.execute(query, (wishlist_id,))
    
    @staticmethod
    def get_item(wishlist_item_id):
        query = """
            SELECT 
                wi.id,
                wi.wishlist_id,
                wi.product_id,
                w.user_id
            FROM wishlist_items wi
            JOIN wishlists w ON wi.wishlist_id = w.id
            WHERE wi.id = %s::uuid
        """
        with SQLManager() as db:
            return db.execute_one(query, (wishlist_item_id,))
    
    @staticmethod
    def add_to_wishlist(wishlist_id, product_id):
        query = """
            INSERT INTO wishlist_items (wishlist_id, product_id, created_at, updated_at)
            VALUES (%s::uuid, %s::uuid, NOW(), NOW())
            ON CONFLICT (wishlist_id, product_id) DO NOTHING
            RETURNING id
        """
        with SQLManager() as db:
            return db.execute_one(query, (wishlist_id, product_id))
    
    @staticmethod
    def remove_from_wishlist(wishlist_item_id):
        query = "DELETE FROM wishlist_items WHERE id = %s::uuid"
        with SQLManager() as db:
            return db.execute_update(query, (wishlist_item_id,))
    
    @staticmethod
    def delete_wishlist(wishlist_id):
        query = "DELETE FROM wishlists WHERE id = %s::uuid"
        with SQLManager() as db:
            return db.execute_update(query, (wishlist_id,))
    
    @staticmethod
    def update_wishlist(wishlist_id, name, description):
        query = """
            UPDATE wishlists
            SET name = %s, description = %s, updated_at = NOW()
            WHERE id = %s::uuid
        """
        with SQLManager() as db:
            return db.execute_update(query, (name, description, wishlist_id))
    
    @staticmethod
    def check_product_in_wishlist(wishlist_id, product_id):
        query = """
            SELECT EXISTS(
                SELECT 1 FROM wishlist_items
                WHERE wishlist_id = %s::uuid AND product_id = %s::uuid
            ) as exists
        """
        with SQLManager() as db:
            result = db.execute_one(query, (wishlist_id, product_id))
            return result['exists'] if result else False
        
        
class ProductReviewRepository:
    @staticmethod
    def create_review(product_id, user_id, rating, comment):
        query = """
            INSERT INTO product_reviews 
            (product_id, user_id, rating, comment, created_at, updated_at, is_verified)
            VALUES (%s::uuid, %s::uuid, %s, %s, NOW(), NOW(), FALSE)
            RETURNING id, rating, comment, created_at
        """
        with SQLManager() as db:
            return db.execute_one(query, (product_id, user_id, rating, comment))
    
    @staticmethod
    def get_product_reviews(product_id):
        query = """
            SELECT 
                pr.id,
                pr.rating,
                pr.comment,
                pr.created_at,
                pr.is_verified,
                u.username,
                u.first_name,
                u.last_name
            FROM product_reviews pr
            JOIN users u ON pr.user_id = u.id
            WHERE pr.product_id = %s::uuid
            ORDER BY pr.created_at DESC
        """
        with SQLManager() as db:
            return db.execute(query, (product_id,))
    
    @staticmethod
    def get_user_reviews(user_id):
        query = """
            SELECT 
                pr.id,
                pr.rating,
                pr.comment,
                pr.created_at,
                pr.is_verified,
                p.name as product_name,
                p.slug as product_slug
            FROM product_reviews pr
            JOIN products p ON pr.product_id = p.id
            WHERE pr.user_id = %s::uuid
            ORDER BY pr.created_at DESC
        """
        with SQLManager() as db:
            return db.execute(query, (user_id,))
    
    @staticmethod
    def update_review(review_id, rating, comment):
        query = """
            UPDATE product_reviews
            SET rating = %s, comment = %s, updated_at = NOW()
            WHERE id = %s::uuid
        """
        with SQLManager() as db:
            return db.execute_update(query, (rating, comment, review_id))
    
    @staticmethod
    def delete_review(review_id: str):
        query = "DELETE FROM product_reviews WHERE id = %s::uuid"
        with SQLManager() as db:
            return db.execute_update(query, (review_id,))
    
    @staticmethod
    def get_product_average_rating(product_id):
        query = """
            SELECT 
                ROUND(AVG(rating), 1) as avg_rating,
                COUNT(*) as reviews_count
            FROM product_reviews
            WHERE product_id = %s::uuid
        """
        with SQLManager() as db:
            result = db.execute_one(query, (product_id,))
            return result if result else {'avg_rating': 0, 'reviews_count': 0}        