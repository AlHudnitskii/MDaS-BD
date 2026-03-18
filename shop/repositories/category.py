from ..sql_manager import SQLManager


class CategoryRepository:
    @staticmethod
    def get_all() -> list[dict]:
        with SQLManager() as db:
            return db.execute("SELECT id, name, slug FROM categories ORDER BY name")

    @staticmethod
    def get_by_slug(slug: str) -> dict | None:
        with SQLManager() as db:
            return db.execute_one(
                "SELECT id, name, slug FROM categories WHERE slug = %s", (slug,)
            )
