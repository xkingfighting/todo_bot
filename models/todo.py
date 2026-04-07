"""Todo model with CRUD operations."""

import json
import time
from dataclasses import dataclass, asdict
from typing import Optional

from models.database import get_db, get_redis

CACHE_PREFIX = "todo_bot:user_todos:"
CACHE_TTL = 300  # 5 minutes


@dataclass
class Todo:
    id: int = 0
    user_id: int = 0
    chat_id: int = 0
    chat_type: str = "private"
    title: str = ""
    description: Optional[str] = None
    priority: int = 2  # 1=high, 2=medium, 3=low
    due_date: Optional[str] = None
    status: int = 0  # 0=pending, 1=completed
    completed_at: Optional[int] = None
    created_at: int = 0
    updated_at: int = 0


PRIORITY_LABELS = {1: "High", 2: "Medium", 3: "Low"}
PRIORITY_ICONS = {1: "!!!", 2: "!!", 3: "!"}


class TodoModel:

    @staticmethod
    def _invalidate_cache(user_id: int):
        r = get_redis()
        keys = r.keys(f"{CACHE_PREFIX}{user_id}:*")
        if keys:
            r.delete(*keys)

    @staticmethod
    def create(user_id: int, chat_id: int, chat_type: str, title: str,
               priority: int = 2, due_date: str = None, description: str = None) -> Todo:
        now = int(time.time())
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO todos (user_id, chat_id, chat_type, title, description, priority, due_date, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (user_id, chat_id, chat_type, title, description, priority, due_date, now, now)
        )
        todo_id = cursor.lastrowid
        cursor.close()
        conn.close()
        TodoModel._invalidate_cache(user_id)
        return Todo(id=todo_id, user_id=user_id, chat_id=chat_id, chat_type=chat_type,
                    title=title, description=description, priority=priority,
                    due_date=due_date, status=0, created_at=now, updated_at=now)

    @staticmethod
    def get_by_id(todo_id: int, user_id: int) -> Optional[Todo]:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM todos WHERE id = %s AND user_id = %s", (todo_id, user_id))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row:
            return None
        return Todo(**{k: v for k, v in row.items() if k in Todo.__dataclass_fields__})

    @staticmethod
    def list_by_user(user_id: int, status: int = None, chat_id: int = None,
                     chat_type: str = None) -> list[Todo]:
        cache_key = f"{CACHE_PREFIX}{user_id}:s{status}:c{chat_id}:{chat_type}"
        r = get_redis()
        cached = r.get(cache_key)
        if cached:
            rows = json.loads(cached)
            return [Todo(**row) for row in rows]

        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        sql = "SELECT * FROM todos WHERE user_id = %s"
        params = [user_id]

        if status is not None:
            sql += " AND status = %s"
            params.append(status)
        if chat_id is not None:
            sql += " AND chat_id = %s"
            params.append(chat_id)
        if chat_type is not None:
            sql += " AND chat_type = %s"
            params.append(chat_type)

        sql += " ORDER BY priority ASC, due_date ASC, created_at DESC"
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        # Convert date objects to strings for JSON serialization
        for row in rows:
            if row.get("due_date") and hasattr(row["due_date"], "isoformat"):
                row["due_date"] = row["due_date"].isoformat()

        r.setex(cache_key, CACHE_TTL, json.dumps(rows, default=str))
        return [Todo(**{k: v for k, v in row.items() if k in Todo.__dataclass_fields__}) for row in rows]

    @staticmethod
    def complete(todo_id: int, user_id: int) -> bool:
        now = int(time.time())
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE todos SET status = 1, completed_at = %s, updated_at = %s WHERE id = %s AND user_id = %s AND status = 0",
            (now, now, todo_id, user_id)
        )
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        if affected:
            TodoModel._invalidate_cache(user_id)
        return affected > 0

    @staticmethod
    def uncomplete(todo_id: int, user_id: int) -> bool:
        now = int(time.time())
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE todos SET status = 0, completed_at = NULL, updated_at = %s WHERE id = %s AND user_id = %s AND status = 1",
            (now, todo_id, user_id)
        )
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        if affected:
            TodoModel._invalidate_cache(user_id)
        return affected > 0

    @staticmethod
    def delete(todo_id: int, user_id: int) -> bool:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM todos WHERE id = %s AND user_id = %s", (todo_id, user_id))
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        if affected:
            TodoModel._invalidate_cache(user_id)
        return affected > 0

    @staticmethod
    def update_priority(todo_id: int, user_id: int, priority: int) -> bool:
        now = int(time.time())
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE todos SET priority = %s, updated_at = %s WHERE id = %s AND user_id = %s",
            (priority, now, todo_id, user_id)
        )
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        if affected:
            TodoModel._invalidate_cache(user_id)
        return affected > 0

    @staticmethod
    def update_due_date(todo_id: int, user_id: int, due_date: str) -> bool:
        now = int(time.time())
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE todos SET due_date = %s, updated_at = %s WHERE id = %s AND user_id = %s",
            (due_date, now, todo_id, user_id)
        )
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        if affected:
            TodoModel._invalidate_cache(user_id)
        return affected > 0

    @staticmethod
    def clear_completed(user_id: int) -> int:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM todos WHERE user_id = %s AND status = 1", (user_id,))
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        if affected:
            TodoModel._invalidate_cache(user_id)
        return affected

    @staticmethod
    def count_by_user(user_id: int) -> dict:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT status, COUNT(*) as cnt FROM todos WHERE user_id = %s GROUP BY status",
            (user_id,)
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        counts = {"pending": 0, "completed": 0, "total": 0}
        for row in rows:
            if row["status"] == 0:
                counts["pending"] = row["cnt"]
            elif row["status"] == 1:
                counts["completed"] = row["cnt"]
        counts["total"] = counts["pending"] + counts["completed"]
        return counts
