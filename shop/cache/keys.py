class CacheKeys:
    PRODUCTS_LIST  = "cache:products:list:{category}:{sort}"
    PRODUCTS_DETAIL = "cache:products:detail:{slug}"
    PRODUCTS_TOP = "cache:products:top:{limit}"
    PRODUCTS_SEARCH = "cache:products:search:{query}"
    CATEGORIES_ALL = "cache:categories:all"
    USERS_LIST = "cache:users:list"
    USERS_ROLES = "cache:users:roles"
    STATISTICS_SALES = "cache:statistics:sales"
    STATISTICS_CATEGORIES = "cache:statistics:categories"
    SESSION = "session:{user_id}"

    PREFIX_PRODUCTS = "cache:products:"
    PREFIX_CATEGORIES = "cache:categories:"
    PREFIX_USERS = "cache:users:"
    PREFIX_STATISTICS = "cache:statistics:"
    PREFIX_ALL = "cache:"

    @staticmethod
    def products_list(category: str = "all", sort: str = "name") -> str:
        return CacheKeys.PRODUCTS_LIST.format(
            category=category or "all",
            sort=sort or "name",
        )

    @staticmethod
    def products_detail(slug: str) -> str:
        return CacheKeys.PRODUCTS_DETAIL.format(slug=slug)

    @staticmethod
    def products_top(limit: int = 10) -> str:
        return CacheKeys.PRODUCTS_TOP.format(limit=limit)

    @staticmethod
    def products_search(query: str) -> str:
        return CacheKeys.PRODUCTS_SEARCH.format(query=query.lower().strip())

    @staticmethod
    def session(user_id: str) -> str:
        return CacheKeys.SESSION.format(user_id=user_id)
