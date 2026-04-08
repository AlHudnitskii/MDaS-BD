from django.conf import settings

from ..core.postgres import SQLManager
from ..cache import CacheService, CacheKeys


class CategoryRepository:

    @staticmethod
    def get_all() -> list[dict]:
        return CacheService.get_or_set(
            key = CacheKeys.CATEGORIES_ALL,
            fetch_fn = CategoryRepository._fetch_all,
            ttl = settings.CACHE_TTL['categories'],
        )

    @staticmethod
    def _fetch_all() -> list[dict]:
        with SQLManager() as db:
            return db.execute("SELECT id, name, slug FROM categories ORDER BY name")

    @staticmethod
    def get_by_slug(slug: str) -> dict | None:
        categories = CategoryRepository.get_all()
        return next((c for c in categories if c['slug'] == slug), None)

    @staticmethod
    def invalidate():
        CacheService.invalidate_prefix(CacheKeys.PREFIX_CATEGORIES)
