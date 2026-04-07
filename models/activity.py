"""Activity log model for group collaboration tracking."""

import time
from models.database import get_db


class ActivityLog:

    @staticmethod
    def log(chat_id: int, chat_type: str, user_id: int, user_name: str,
            action: str, todo_id: int = 0, detail: str = ""):
        if chat_type != "group":
            return
        now = int(time.time())
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO activity_log (chat_id, chat_type, user_id, user_name, action, todo_id, detail, created_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (chat_id, chat_type, user_id, user_name, action, todo_id, detail, now)
        )
        cursor.close()
        conn.close()

    @staticmethod
    def recent(chat_id: int, limit: int = 20) -> list[dict]:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM activity_log WHERE chat_id = %s ORDER BY created_at DESC LIMIT %s",
            (chat_id, limit)
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
