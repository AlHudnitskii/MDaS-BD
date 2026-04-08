import csv
import json
import datetime
import logging

from ..core.mongo import get_logs_collection

logger = logging.getLogger(__name__)


def _since(days: int) -> datetime.datetime:
    return datetime.datetime.utcnow() - datetime.timedelta(days=days)


class MongoAnalyticsRepository:
    @staticmethod
    def activity_by_period(period: str = 'day') -> list[dict]:
        try:
            days_map = {'day': 30, 'week': 90, 'month': 365}
            days = days_map.get(period, 30)

            if period == 'day':
                date_format = '%Y-%m-%d'
                trunc = {'year': {'$year': '$timestamp'},
                    'month': {'$month': '$timestamp'},
                    'day': {'$dayOfMonth': '$timestamp'}}
            elif period == 'week':
                date_format = '%Y-W%V'
                trunc = {'year': {'$isoWeekYear': '$timestamp'},
                    'week': {'$isoWeek': '$timestamp'}}
            else:
                date_format = '%Y-%m'
                trunc = {'year': {'$year': '$timestamp'},
                    'month': {'$month': '$timestamp'}}

            pipeline = [
                {'$match': {'timestamp': {'$gte': _since(days)}}},
                {'$group': {
                    '_id': trunc,
                    'total': {'$sum': 1},
                    'success': {'$sum': {'$cond': [{'$eq': ['$status', 'SUCCESS']}, 1, 0]}},
                    'failed': {'$sum': {'$cond': [{'$in':  ['$status', ['FAILED', 'ERROR']]}, 1, 0]}},
                    'unique_users':{'$addToSet': '$user_id'},
                }},
                {'$project': {
                    'total': 1,
                    'success': 1,
                    'failed': 1,
                    'unique_users': {'$size': '$unique_users'},
                }},
                {'$sort': {'_id': 1}},
            ]

            results = list(get_logs_collection().aggregate(pipeline))

            for r in results:
                g = r['_id']
                if period == 'day':
                    r['label'] = f"{g['year']}-{g['month']:02d}-{g['day']:02d}"
                elif period == 'week':
                    r['label'] = f"{g['year']}-W{g['week']:02d}"
                else:
                    r['label'] = f"{g['year']}-{g['month']:02d}"
                del r['_id']

            return results
        except Exception as e:
            logger.warning(f"activity_by_period failed: {e}")
            return []


    @staticmethod
    def top_active_users(limit: int = 10) -> list[dict]:
        try:
            pipeline = [
                {'$match': {
                    'timestamp': {'$gte': _since(30)},
                    'user_id': {'$ne': None},
                }},
                {'$group': {
                    '_id': '$user_id',
                    'total': {'$sum': 1},
                    'actions': {'$addToSet': '$action'},
                    'last_seen': {'$max': '$timestamp'},
                    'first_seen': {'$min': '$timestamp'},
                }},
                {'$project': {
                    'user_id': '$_id',
                    'total': 1,
                    'unique_actions':{'$size': '$actions'},
                    'last_seen': 1,
                    'first_seen': 1,
                }},
                {'$sort':  {'total': -1}},
                {'$limit': limit},
            ]
            results = list(get_logs_collection().aggregate(pipeline))
            for r in results:
                r['user_id'] = r.pop('_id')
            return results
        except Exception as e:
            logger.warning(f"top_active_users failed: {e}")
            return []

    @staticmethod
    def operations_distribution() -> list[dict]:
        try:
            crud_map = {
                'CREATE': ['USER_REGISTER', 'ORDER_CREATED', 'NOTE_CREATED',
                           'REVIEW_CREATED', 'WISHLIST_CREATED', 'PRODUCT_ADDED_TO_WISHLIST'],
                'READ':   ['USER_LOGIN', 'DB_QUERY'],
                'UPDATE': ['PROFILE_UPDATE', 'NOTE_UPDATED', 'REVIEW_UPDATED',
                           'WISHLIST_UPDATED', 'ORDER_PAID'],
                'DELETE': ['NOTE_DELETED', 'REVIEW_DELETED', 'WISHLIST_DELETED',
                           'PRODUCT_REMOVED_FROM_WISHLIST', 'LOGS_CLEANUP'],
                'AUTH':   ['USER_LOGOUT', 'LOGIN_FAILED'],
            }

            pipeline = [
                {'$match': {'timestamp': {'$gte': _since(30)}}},
                {'$group': {
                    '_id': '$action',
                    'count': {'$sum': 1},
                }},
                {'$sort': {'count': -1}},
            ]
            raw = list(get_logs_collection().aggregate(pipeline))

            action_to_crud = {}
            for crud_type, actions in crud_map.items():
                for action in actions:
                    action_to_crud[action] = crud_type

            crud_totals = {'CREATE': 0, 'READ': 0, 'UPDATE': 0, 'DELETE': 0, 'AUTH': 0, 'OTHER': 0}
            actions_detail = []

            for r in raw:
                action = r['_id']
                count = r['count']
                crud_type = action_to_crud.get(action, 'OTHER')
                crud_totals[crud_type] += count
                actions_detail.append({
                    'action': action,
                    'count': count,
                    'crud_type': crud_type,
                })

            total = sum(crud_totals.values()) or 1
            crud_summary = [
                {
                    'type': t,
                    'count': c,
                    'percentage': round(c / total * 100, 1),
                }
                for t, c in crud_totals.items() if c > 0
            ]
            crud_summary.sort(key=lambda x: x['count'], reverse=True)

            return {'summary': crud_summary, 'detail': actions_detail}
        except Exception as e:
            logger.warning(f"operations_distribution failed: {e}")
            return {'summary': [], 'detail': []}

    @staticmethod
    def time_series(days: int = 14) -> list[dict]:
        try:
            pipeline = [
                {'$match': {'timestamp': {'$gte': _since(days)}}},
                {'$group': {
                    '_id': {
                        'date': {
                            '$dateToString': {
                                'format': '%Y-%m-%d',
                                'date': '$timestamp',
                            }
                        },
                        'hour': {'$hour': '$timestamp'},
                    },
                    'count': {'$sum': 1},
                }},
                {'$project': {
                    'date': '$_id.date',
                    'hour': '$_id.hour',
                    'count': 1,
                }},
                {'$sort': {'_id.date': 1, '_id.hour': 1}},
            ]
            results = list(get_logs_collection().aggregate(pipeline))
            for r in results:
                r['label'] = f"{r['_id']['date']} {r['_id']['hour']:02d}:00"
                del r['_id']
            return results
        except Exception as e:
            logger.warning(f"time_series failed: {e}")
            return []

    @staticmethod
    def detect_anomalies() -> list[dict]:
        try:
            anomalies = []
            col = get_logs_collection()

            pipeline_failed = [
                {'$match': {
                    'action': 'LOGIN_FAILED',
                    'timestamp': {'$gte': _since(1)},
                    'user_id': {'$ne': None},
                }},
                {'$group': {
                    '_id': '$user_id',
                    'count': {'$sum': 1},
                }},
                {'$match': {'count': {'$gte': 3}}},
                {'$sort': {'count': -1}},
            ]
            for r in col.aggregate(pipeline_failed):
                anomalies.append({
                    'type': 'BRUTE_FORCE',
                    'severity': 'HIGH',
                    'user_id': r['_id'],
                    'description': f"Failed logins: {r['count']} attempts in 24h",
                    'count': r['count'],
                })

            pipeline_burst = [
                {'$match': {
                    'timestamp': {'$gte': _since(1)},
                    'user_id': {'$ne': None},
                }},
                {'$group': {
                    '_id': {
                        'user_id': '$user_id',
                        'hour': {'$hour': '$timestamp'},
                        'date': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$timestamp'}},
                    },
                    'count': {'$sum': 1},
                }},
                {'$match': {'count': {'$gte': 50}}},
                {'$sort': {'count': -1}},
            ]
            for r in col.aggregate(pipeline_burst):
                anomalies.append({
                    'type': 'HIGH_ACTIVITY',
                    'severity': 'MEDIUM',
                    'user_id': r['_id']['user_id'],
                    'description': f"{r['count']} actions in 1 hour ({r['_id']['date']} {r['_id']['hour']:02d}:00)",
                    'count': r['count'],
                })

            pipeline_errors = [
                {'$match': {
                    'status': {'$in': ['ERROR', 'FAILED']},
                    'timestamp': {'$gte': datetime.datetime.utcnow() - datetime.timedelta(hours=6)},
                }},
                {'$group': {
                    '_id': '$action',
                    'count': {'$sum': 1},
                }},
                {'$match': {'count': {'$gte': 5}}},
                {'$sort':  {'count': -1}},
            ]
            for r in col.aggregate(pipeline_errors):
                anomalies.append({
                    'type': 'ERROR_SPIKE',
                    'severity': 'HIGH',
                    'user_id': None,
                    'description': f"Action '{r['_id']}' failed {r['count']} times in 6h",
                    'count': r['count'],
                })

            return anomalies
        except Exception as e:
            logger.warning(f"detect_anomalies failed: {e}")
            return []

    @staticmethod
    def export_json(report_type: str, **kwargs) -> str:
        data = MongoAnalyticsRepository._get_report_data(report_type, **kwargs)
        return json.dumps(data, ensure_ascii=False, indent=2, default=str)

    @staticmethod
    def export_csv(report_type: str, **kwargs) -> str:
        import io
        data = MongoAnalyticsRepository._get_report_data(report_type, **kwargs)

        if not data:
            return ''

        if isinstance(data, dict):
            data = data.get('detail', [])

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()

    @staticmethod
    def _get_report_data(report_type: str, **kwargs):
        dispatch = {
            'activity': lambda: MongoAnalyticsRepository.activity_by_period(kwargs.get('period', 'day')),
            'top_users': lambda: MongoAnalyticsRepository.top_active_users(),
            'operations': lambda: MongoAnalyticsRepository.operations_distribution(),
            'time_series': lambda: MongoAnalyticsRepository.time_series(),
            'anomalies': lambda: MongoAnalyticsRepository.detect_anomalies(),
        }
        fn = dispatch.get(report_type)
        return fn() if fn else []
