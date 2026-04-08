import json
import logging
import threading
import datetime

from .redis import get_redis_pubsub, get_redis_cache

logger = logging.getLogger(__name__)

CHANNEL_CACHE_INVALIDATE = 'shop:cache:invalidate'
CHANNEL_USER_EVENTS = 'shop:user:events'
CHANNEL_ORDER_EVENTS = 'shop:order:events'


class Publisher:
    @staticmethod
    def _publish(channel: str, event_type: str, payload: dict) -> None:
        try:
            message = json.dumps({
                'event': event_type,
                'payload': payload,
                'timestamp': datetime.datetime.utcnow().isoformat(),
            })
            get_redis_pubsub().publish(channel, message)
            logger.debug(f"Published {event_type} to {channel}")
        except Exception as e:
            logger.warning(f"Publish failed channel={channel}: {e}")

    @staticmethod
    def cache_invalidated(prefix: str) -> None:
        Publisher._publish(
            CHANNEL_CACHE_INVALIDATE,
            'CACHE_INVALIDATED',
            {'prefix': prefix},
        )

    @staticmethod
    def user_updated(user_id: str, username: str) -> None:
        Publisher._publish(
            CHANNEL_USER_EVENTS,
            'USER_UPDATED',
            {'user_id': user_id, 'username': username},
        )

    @staticmethod
    def user_logged_out(user_id: str) -> None:
        Publisher._publish(
            CHANNEL_USER_EVENTS,
            'USER_LOGGED_OUT',
            {'user_id': user_id},
        )

    @staticmethod
    def order_paid(order_id: str, user_id: str) -> None:
        Publisher._publish(
            CHANNEL_ORDER_EVENTS,
            'ORDER_PAID',
            {'order_id': order_id, 'user_id': user_id},
        )


class Subscriber:
    _thread: threading.Thread | None = None
    _running: bool = False

    @classmethod
    def start(cls) -> None:
        if cls._thread and cls._thread.is_alive():
            return
        cls._running = True
        cls._thread = threading.Thread(target=cls._listen, daemon=True, name='redis-subscriber')
        cls._thread.start()
        logger.info("Redis subscriber started")

    @classmethod
    def stop(cls) -> None:
        cls._running = False
        logger.info("Redis subscriber stopped")

    @classmethod
    def _listen(cls) -> None:
        try:
            r = get_redis_pubsub()
            pubsub = r.pubsub()
            pubsub.subscribe(
                CHANNEL_CACHE_INVALIDATE,
                CHANNEL_USER_EVENTS,
                CHANNEL_ORDER_EVENTS,
            )
            logger.info("Subscribed to Redis channels")

            for message in pubsub.listen():
                if not cls._running:
                    break
                if message['type'] != 'message':
                    continue
                try:
                    data = json.loads(message['data'])
                    event_type = data.get('event')
                    payload = data.get('payload', {})
                    channel = message['channel']
                    cls._handle(channel, event_type, payload)
                except Exception as e:
                    logger.warning(f"Subscriber handle error: {e}")

        except Exception as e:
            logger.error(f"Subscriber listen error: {e}")

    @classmethod
    def _handle(cls, channel: str, event_type: str, payload: dict) -> None:
        logger.debug(f"Event received: {event_type} from {channel}")

        if event_type == 'CACHE_INVALIDATED':
            prefix = payload.get('prefix', '')
            if prefix:
                try:
                    from ..cache.service import CacheService
                    CacheService.invalidate_prefix(prefix)
                    logger.debug(f"Cache invalidated by pub/sub: prefix={prefix}")
                except Exception as e:
                    logger.warning(f"Cache invalidation via pub/sub failed: {e}")

        elif event_type == 'USER_LOGGED_OUT':
            user_id = payload.get('user_id')
            if user_id:
                try:
                    from ..auth.session_service import SessionService
                    SessionService.delete(user_id)
                    logger.debug(f"Session deleted by pub/sub: user_id={user_id}")
                except Exception as e:
                    logger.warning(f"Session deletion via pub/sub failed: {e}")

        elif event_type == 'ORDER_PAID':
            try:
                from ..cache.service import CacheService
                from ..cache.keys import CacheKeys
                CacheService.invalidate_prefix(CacheKeys.PREFIX_STATISTICS)
                CacheService.invalidate_prefix("cache:products:top:")
                logger.debug("Statistics cache invalidated by pub/sub")
            except Exception as e:
                logger.warning(f"Statistics invalidation via pub/sub failed: {e}")
