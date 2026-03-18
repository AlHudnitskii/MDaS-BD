from ..sql_manager import SQLManager


class WishlistRepository:

    @staticmethod
    def create(user_id: str, name: str, description: str = '') -> dict | None:
        with SQLManager() as db:
            return db.execute_one(
                "INSERT INTO wishlists (user_id, name, description, created_at, updated_at) "
                "VALUES (%s::uuid, %s, %s, NOW(), NOW()) "
                "RETURNING id, name, description, created_at",
                (user_id, name, description)
            )

    @staticmethod
    def get_by_user(user_id: str) -> list[dict]:
        with SQLManager() as db:
            return db.execute(
                "SELECT w.id, w.name, w.description, w.created_at, "
                "COUNT(wi.id) AS items_count "
                "FROM wishlists w LEFT JOIN wishlist_items wi ON w.id = wi.wishlist_id "
                "WHERE w.user_id = %s::uuid "
                "GROUP BY w.id, w.name, w.description, w.created_at "
                "ORDER BY w.created_at DESC",
                (user_id,)
            )

    @staticmethod
    def get_by_id(wishlist_id: str) -> dict | None:
        with SQLManager() as db:
            return db.execute_one(
                "SELECT id, user_id, name, description, created_at, updated_at "
                "FROM wishlists WHERE id = %s::uuid",
                (wishlist_id,)
            )

    @staticmethod
    def get_items(wishlist_id: str) -> list[dict]:
        with SQLManager() as db:
            return db.execute(
                "SELECT wi.id AS wishlist_item_id, p.id AS product_id, "
                "p.name, p.slug, p.price, p.discount, "
                "ROUND(p.price * (1 - p.discount), 2) AS final_price, "
                "p.image, c.name AS category_name, wi.created_at AS added_at "
                "FROM wishlist_items wi "
                "JOIN products p ON wi.product_id = p.id "
                "JOIN categories c ON p.category_id = c.id "
                "WHERE wi.wishlist_id = %s::uuid ORDER BY wi.created_at DESC",
                (wishlist_id,)
            )

    @staticmethod
    def get_item_by_id(wishlist_item_id: str) -> dict | None:
        with SQLManager() as db:
            return db.execute_one(
                "SELECT wi.id, wi.wishlist_id, wi.product_id, w.user_id "
                "FROM wishlist_items wi JOIN wishlists w ON wi.wishlist_id = w.id "
                "WHERE wi.id = %s::uuid",
                (wishlist_item_id,)
            )

    @staticmethod
    def add_item(wishlist_id: str, product_id: str) -> dict | None:
        with SQLManager() as db:
            return db.execute_one(
                "INSERT INTO wishlist_items (wishlist_id, product_id, created_at, updated_at) "
                "VALUES (%s::uuid, %s::uuid, NOW(), NOW()) "
                "ON CONFLICT (wishlist_id, product_id) DO NOTHING RETURNING id",
                (wishlist_id, product_id)
            )

    @staticmethod
    def remove_item(wishlist_item_id: str) -> None:
        with SQLManager() as db:
            db.execute_update(
                "DELETE FROM wishlist_items WHERE id = %s::uuid", (wishlist_item_id,)
            )

    @staticmethod
    def item_exists(wishlist_id: str, product_id: str) -> bool:
        with SQLManager() as db:
            result = db.execute_one(
                "SELECT EXISTS(SELECT 1 FROM wishlist_items "
                "WHERE wishlist_id = %s::uuid AND product_id = %s::uuid) AS exists",
                (wishlist_id, product_id)
            )
            return result['exists'] if result else False

    @staticmethod
    def update(wishlist_id: str, name: str, description: str) -> None:
        with SQLManager() as db:
            db.execute_update(
                "UPDATE wishlists SET name = %s, description = %s, updated_at = NOW() "
                "WHERE id = %s::uuid",
                (name, description, wishlist_id)
            )

    @staticmethod
    def delete(wishlist_id: str) -> None:
        with SQLManager() as db:
            db.execute_update("DELETE FROM wishlists WHERE id = %s::uuid", (wishlist_id,))
