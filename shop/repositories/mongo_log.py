import datetime
import logging

from ..core.mongo import get_logs_collection, get_errors_collection

logger = logging.getLogger(__name__)


class MongoLogRepository:
    @staticmethod
    def log_action(user_id: str | None, action: str,
                   details: dict, status: str = 'SUCCESS') -> None:
        try:
            doc = {
                'user_id': str(user_id) if user_id else None,
                'action': action,
                'details': details,
                'status': status,
                'timestamp': datetime.datetime.utcnow(),
            }
            get_logs_collection().insert_one(doc)
        except Exception as e:
            logger.warning(f"MongoLog write failed action={action}: {e}")

    @staticmethod
    def log_db_query(query_type: str, table: str,
                     duration_ms: float, user_id: str | None = None) -> None:
        try:
            doc = {
                'user_id': str(user_id) if user_id else None,
                'action': 'DB_QUERY',
                'details': {
                    'query_type': query_type,   # SELECT / INSERT / UPDATE / DELETE
                    'table': table,
                    'duration_ms': duration_ms,
                },
                'status': 'SUCCESS',
                'timestamp': datetime.datetime.utcnow(),
            }
            get_logs_collection().insert_one(doc)
        except Exception as e:
            logger.warning(f"MongoLog db_query failed: {e}")

    @staticmethod
    def log_error(error_type: str, message: str,
                  traceback: str = '', user_id: str | None = None,
                  request_path: str = '') -> None:
        try:
            doc = {
                'user_id': str(user_id) if user_id else None,
                'error_type': error_type,
                'message': message,
                'traceback': traceback,
                'request_path': request_path,
                'timestamp': datetime.datetime.utcnow(),
            }
            get_errors_collection().insert_one(doc)
        except Exception as e:
            logger.warning(f"MongoLog error write failed: {e}")


    @staticmethod
    def get_filtered(action_type: str | None = None,
                     status: str | None = None,
                     user_id: str | None = None,
                     days: int = 7,
                     limit: int = 200) -> list[dict]:
        try:
            query = {
                'timestamp': {
                    '$gte': datetime.datetime.utcnow() - datetime.timedelta(days=days)
                }
            }
            if action_type:
                query['action'] = action_type
            if status:
                query['status'] = status
            if user_id:
                query['user_id'] = str(user_id)

            cursor = (
                get_logs_collection()
                .find(query, {'_id': 0})
                .sort('timestamp', -1)
                .limit(limit)
            )
            return list(cursor)
        except Exception as e:
            logger.warning(f"MongoLog get_filtered failed: {e}")
            return []

    @staticmethod
    def get_statistics() -> dict:
        try:
            col = get_logs_collection()
            since_30 = datetime.datetime.utcnow() - datetime.timedelta(days=30)
            since_1 = datetime.datetime.utcnow() - datetime.timedelta(days=1)
            since_7 = datetime.datetime.utcnow() - datetime.timedelta(days=7)

            total = col.count_documents({'timestamp': {'$gte': since_30}})
            success = col.count_documents({'timestamp': {'$gte': since_30}, 'status': 'SUCCESS'})
            error = col.count_documents({'timestamp': {'$gte': since_30}, 'status': {'$in': ['ERROR', 'FAILED']}})
            today = col.count_documents({'timestamp': {'$gte': since_1}})
            week = col.count_documents({'timestamp': {'$gte': since_7}})

            unique_users = len(col.distinct('user_id', {
                'timestamp': {'$gte': since_30},
                'user_id': {'$ne': None},
            }))
            unique_actions = len(col.distinct('action', {'timestamp': {'$gte': since_30}}))

            return {
                'total_logs': total,
                'success_count': success,
                'error_count': error,
                'today_logs': today,
                'week_logs': week,
                'unique_users': unique_users,
                'unique_actions': unique_actions,
            }
        except Exception as e:
            logger.warning(f"MongoLog get_statistics failed: {e}")
            return {}

    @staticmethod
    def get_unique_action_types() -> list[str]:
        try:
            since = datetime.datetime.utcnow() - datetime.timedelta(days=30)
            return sorted(get_logs_collection().distinct('action', {'timestamp': {'$gte': since}}))
        except Exception as e:
            logger.warning(f"MongoLog get_unique_action_types failed: {e}")
            return []

    @staticmethod
    def cleanup_old(days: int = 90) -> int:
        try:
            cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)
            result = get_logs_collection().delete_many({'timestamp': {'$lt': cutoff}})
            return result.deleted_count
        except Exception as e:
            logger.warning(f"MongoLog cleanup failed: {e}")
            return 0
