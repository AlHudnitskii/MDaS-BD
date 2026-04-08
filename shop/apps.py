from django.apps import AppConfig


class ShopConfig(AppConfig):
    name = 'shop'

    def ready(self):
        try:
            from .core.mongo import ensure_indexes
            ensure_indexes()
        except Exception:
            pass

        try:
            from .core.pubsub import Subscriber
            Subscriber.start()
        except Exception:
            pass
