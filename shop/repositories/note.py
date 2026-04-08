from ..core.postgres import SQLManager


class UserNoteRepository:

    @staticmethod
    def create(user_id: str, title: str, content: str) -> dict | None:
        with SQLManager() as db:
            return db.execute_one(
                "INSERT INTO user_notes (user_id, title, content, created_at, updated_at) "
                "VALUES (%s::uuid, %s, %s, NOW(), NOW()) "
                "RETURNING id, title, content, created_at, updated_at",
                (user_id, title, content)
            )

    @staticmethod
    def get_by_user(user_id: str) -> list[dict]:
        with SQLManager() as db:
            return db.execute(
                "SELECT id, title, content, created_at, updated_at "
                "FROM user_notes WHERE user_id = %s::uuid ORDER BY updated_at DESC",
                (user_id,)
            )

    @staticmethod
    def get_by_id(note_id: str) -> dict | None:
        with SQLManager() as db:
            return db.execute_one(
                "SELECT id, user_id, title, content, created_at, updated_at "
                "FROM user_notes WHERE id = %s::uuid",
                (note_id,)
            )

    @staticmethod
    def update(note_id: str, title: str, content: str) -> None:
        with SQLManager() as db:
            db.execute_update(
                "UPDATE user_notes SET title = %s, content = %s, updated_at = NOW() "
                "WHERE id = %s::uuid",
                (title, content, note_id)
            )

    @staticmethod
    def delete(note_id: str) -> None:
        with SQLManager() as db:
            db.execute_update("DELETE FROM user_notes WHERE id = %s::uuid", (note_id,))
