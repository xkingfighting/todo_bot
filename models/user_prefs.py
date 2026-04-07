"""User preferences model."""

import time
from models.database import get_db, get_redis

PREFS_CACHE_PREFIX = "todo_bot:prefs:"
PREFS_CACHE_TTL = 3600


class UserPrefs:

    @staticmethod
    def get(user_id: int) -> dict:
        r = get_redis()
        cached = r.get(f"{PREFS_CACHE_PREFIX}{user_id}")
        if cached:
            import json
            return json.loads(cached)

        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user_prefs WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            return {"user_id": user_id, "language": "auto", "daily_summary": 1,
                    "reminder_minutes": 60, "first_use": 1}

        import json
        r.setex(f"{PREFS_CACHE_PREFIX}{user_id}", PREFS_CACHE_TTL, json.dumps(row, default=str))
        return row

    @staticmethod
    def set_language(user_id: int, lang: str):
        UserPrefs._upsert(user_id, "language", lang)

    @staticmethod
    def mark_welcomed(user_id: int):
        UserPrefs._upsert(user_id, "first_use", 0)

    @staticmethod
    def is_first_use(user_id: int) -> bool:
        return UserPrefs.get(user_id).get("first_use", 1) == 1

    @staticmethod
    def _upsert(user_id: int, field: str, value):
        now = int(time.time())
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            f"INSERT INTO user_prefs (user_id, {field}, created_at) VALUES (%s, %s, %s) "
            f"ON DUPLICATE KEY UPDATE {field} = %s",
            (user_id, value, now, value)
        )
        cursor.close()
        conn.close()
        r = get_redis()
        r.delete(f"{PREFS_CACHE_PREFIX}{user_id}")

    @staticmethod
    def detect_language(text: str) -> str:
        """Simple CJK detection: if text contains Chinese chars, return 'zh', else 'en'."""
        for ch in text:
            if '\u4e00' <= ch <= '\u9fff':
                return "zh"
        return "en"
