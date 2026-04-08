from ..core.postgres import SQLManager


class ProductReviewRepository:
    @staticmethod
    def create(product_id: str, user_id: str, rating: int, comment: str) -> dict | None:
        with SQLManager() as db:
            return db.execute_one(
                "INSERT INTO product_reviews "
                "(product_id, user_id, rating, comment, created_at, updated_at, is_verified) "
                "VALUES (%s::uuid, %s::uuid, %s, %s, NOW(), NOW(), FALSE) "
                "RETURNING id, rating, comment, created_at",
                (product_id, user_id, rating, comment)
            )

    @staticmethod
    def get_by_product(product_id: str) -> list[dict]:
        with SQLManager() as db:
            return db.execute(
                "SELECT pr.id, pr.rating, pr.comment, pr.created_at, pr.is_verified, "
                "u.username, u.first_name, u.last_name "
                "FROM product_reviews pr JOIN users u ON pr.user_id = u.id "
                "WHERE pr.product_id = %s::uuid ORDER BY pr.created_at DESC",
                (product_id,)
            )

    @staticmethod
    def get_by_user(user_id: str) -> list[dict]:
        with SQLManager() as db:
            return db.execute(
                "SELECT pr.id, pr.rating, pr.comment, pr.created_at, pr.is_verified, "
                "p.name AS product_name, p.slug AS product_slug "
                "FROM product_reviews pr JOIN products p ON pr.product_id = p.id "
                "WHERE pr.user_id = %s::uuid ORDER BY pr.created_at DESC",
                (user_id,)
            )

    @staticmethod
    def get_avg_rating(product_id: str) -> dict:
        with SQLManager() as db:
            result = db.execute_one(
                "SELECT ROUND(AVG(rating), 1) AS avg_rating, COUNT(*) AS reviews_count "
                "FROM product_reviews WHERE product_id = %s::uuid",
                (product_id,)
            )
            return result or {'avg_rating': 0, 'reviews_count': 0}

    @staticmethod
    def update(review_id: str, rating: int, comment: str) -> None:
        with SQLManager() as db:
            db.execute_update(
                "UPDATE product_reviews SET rating = %s, comment = %s, updated_at = NOW() "
                "WHERE id = %s::uuid",
                (rating, comment, review_id)
            )

    @staticmethod
    def delete(review_id: str) -> None:
        with SQLManager() as db:
            db.execute_update(
                "DELETE FROM product_reviews WHERE id = %s::uuid", (review_id,)
            )
