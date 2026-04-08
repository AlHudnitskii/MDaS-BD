import logging
from django.conf import settings

logger = logging.getLogger(__name__)

_client = None


def get_mongo_client():
    global _client
    if _client is None:
        try:
            from pymongo import MongoClient

            uri = getattr(settings, 'MONGODB_URI', 'mongodb://127.0.0.1:27017/')
            username = getattr(settings, 'MONGODB_USERNAME', None)
            password = getattr(settings, 'MONGODB_PASSWORD', None)

            if username and password:
                _client = MongoClient(
                    uri,
                    username=username,
                    password=password,
                    authSource='admin',
                    authMechanism='SCRAM-SHA-256',
                    serverSelectionTimeoutMS=3000,
                )
            else:
                _client = MongoClient(uri, serverSelectionTimeoutMS=3000)

            _client.admin.command('ping')
            logger.info("MongoDB connected successfully")
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            _client = None
    return _client


def get_mongo_db():
    client = get_mongo_client()
    if client is None:
        raise RuntimeError("MongoDB unavailable")
    return client[settings.MONGODB_DATABASE]


def get_logs_collection():
    return get_mongo_db()['action_logs']


def get_errors_collection():
    return get_mongo_db()['error_logs']


def ensure_indexes() -> None:
    try:
        logs = get_logs_collection()
        errors = get_errors_collection()

        logs.create_index(
            [("timestamp", 1)],
            expireAfterSeconds=90 * 24 * 3600,
            name="ttl_90days",
        )
        errors.create_index(
            [("timestamp", 1)],
            expireAfterSeconds=30 * 24 * 3600,
            name="ttl_30days",
        )
        logs.create_index([("user_id", 1)], name="idx_user_id")
        logs.create_index([("action", 1)], name="idx_action")
        logs.create_index([("status", 1)], name="idx_status")
        logs.create_index([("timestamp", -1)], name="idx_timestamp_desc")

        logger.info("MongoDB indexes ensured")
    except Exception as e:
        logger.warning(f"MongoDB index creation failed: {e}")
