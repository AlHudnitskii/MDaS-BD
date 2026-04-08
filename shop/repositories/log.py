import json
from ..core.postgres import SQLManager


class LogRepository:

    @staticmethod
    def log_action(user_id: str | None, action: str,
                   details: dict, status: str = 'SUCCESS') -> None:
        query = """
            INSERT INTO log_entries (user_id, action, details, status, timestamp)
            VALUES (%s::uuid, %s, %s::jsonb, %s, NOW())
        """
        try:
            with SQLManager() as db:
                db.execute_update(query, (user_id, action, json.dumps(details), status))
        except Exception:
            pass

    @staticmethod
    def get_filtered(action_type=None, status=None,
                     user_filter=None, days: int = 7) -> list[dict]:
        conditions = ["l.timestamp > NOW() - make_interval(days => %s)"]
        params = [int(days)]

        if action_type:
            conditions.append("l.action = %s")
            params.append(action_type)
        if status:
            conditions.append("l.status = %s")
            params.append(status)
        if user_filter:
            conditions.append("(u.username ILIKE %s OR u.email ILIKE %s)")
            params.extend([f"%{user_filter}%", f"%{user_filter}%"])

        where = " AND ".join(conditions)
        query = f"""
            SELECT l.id, l.user_id, l.action, l.details,
                   l.status, l.timestamp,
                   u.username, u.email, u.image_url
            FROM log_entries l
            LEFT JOIN users u ON l.user_id = u.id
            WHERE {where}
            ORDER BY l.timestamp DESC
        """
        with SQLManager() as db:
            return db.execute(query, tuple(params)) or []

    @staticmethod
    def get_statistics() -> dict | None:
        with SQLManager() as db:
            result = db.execute("""
                SELECT
                    COUNT(*) AS total_logs,
                    COUNT(*) FILTER (WHERE status = 'SUCCESS') AS success_count,
                    COUNT(*) FILTER (WHERE status = 'ERROR') AS error_count,
                    COUNT(*) FILTER (WHERE timestamp > NOW() - INTERVAL '1 day') AS today_logs,
                    COUNT(*) FILTER (WHERE timestamp > NOW() - INTERVAL '7 days') AS week_logs,
                    COUNT(DISTINCT user_id) AS unique_users,
                    COUNT(DISTINCT action) AS unique_actions
                FROM log_entries
                WHERE timestamp > NOW() - INTERVAL '30 days'
            """)
            return result[0] if result else None

    @staticmethod
    def get_unique_action_types() -> list[str]:
        with SQLManager() as db:
            result = db.execute(
                "SELECT DISTINCT action FROM log_entries "
                "WHERE timestamp > NOW() - INTERVAL '30 days' ORDER BY action"
            )
            return [r['action'] for r in result] if result else []

    @staticmethod
    def cleanup_old(days: int = 90) -> int:
        with SQLManager() as db:
            db.cursor.execute("CALL cleanup_old_logs(%s)", (days,))
            db.connection.commit()
            return db.cursor.rowcount
