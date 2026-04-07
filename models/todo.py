"""Todo model with CRUD operations."""

import json
import time
from dataclasses import dataclass
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
    tags: str = ""
    repeat_rule: str = ""
    assignee_id: int = 0
    assignee_name: str = ""
    reminder_sent: int = 0
    status: int = 0  # 0=pending, 1=completed
    completed_at: Optional[int] = None
    created_at: int = 0
    updated_at: int = 0


PRIORITY_LABELS = {1: "High", 2: "Medium", 3: "Low"}
PRIORITY_ICONS = {1: "!!!", 2: "!!", 3: "!"}


def _row_to_todo(row: dict) -> Todo:
    for k in list(row.keys()):
        if k not in Todo.__dataclass_fields__:
            del row[k]
    if row.get("due_date") and hasattr(row["due_date"], "isoformat"):
        row["due_date"] = row["due_date"].isoformat()
    return Todo(**row)


class TodoModel:

    @staticmethod
    def _invalidate_cache(user_id: int):
        r = get_redis()
        keys = r.keys(f"{CACHE_PREFIX}{user_id}:*")
        if keys:
            r.delete(*keys)

    @staticmethod
    def create(user_id: int, chat_id: int, chat_type: str, title: str,
               priority: int = 2, due_date: str = None, description: str = None,
               tags: str = "", repeat_rule: str = "",
               assignee_id: int = 0, assignee_name: str = "") -> Todo:
        now = int(time.time())
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO todos (user_id, chat_id, chat_type, title, description, priority, "
            "due_date, tags, repeat_rule, assignee_id, assignee_name, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (user_id, chat_id, chat_type, title, description, priority,
             due_date, tags, repeat_rule, assignee_id, assignee_name, now, now)
        )
        todo_id = cursor.lastrowid
        cursor.close()
        conn.close()
        TodoModel._invalidate_cache(user_id)
        return Todo(id=todo_id, user_id=user_id, chat_id=chat_id, chat_type=chat_type,
                    title=title, description=description, priority=priority,
                    due_date=due_date, tags=tags, repeat_rule=repeat_rule,
                    assignee_id=assignee_id, assignee_name=assignee_name,
                    status=0, created_at=now, updated_at=now)

    @staticmethod
    def get_by_id(todo_id: int, user_id: int) -> Optional[Todo]:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM todos WHERE id = %s AND (user_id = %s OR assignee_id = %s)",
                        (todo_id, user_id, user_id))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row:
            return None
        return _row_to_todo(row)

    @staticmethod
    def list_by_user(user_id: int, status: int = None, chat_id: int = None,
                     chat_type: str = None, tag: str = None,
                     priority: int = None, overdue_only: bool = False) -> list[Todo]:
        cache_key = f"{CACHE_PREFIX}{user_id}:s{status}:c{chat_id}:{chat_type}:t{tag}:p{priority}:o{overdue_only}"
        r = get_redis()
        cached = r.get(cache_key)
        if cached:
            rows = json.loads(cached)
            return [Todo(**row) for row in rows]

        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        sql = "SELECT * FROM todos WHERE (user_id = %s OR assignee_id = %s)"
        params = [user_id, user_id]

        if status is not None:
            sql += " AND status = %s"
            params.append(status)
        if chat_id is not None:
            sql += " AND chat_id = %s"
            params.append(chat_id)
        if chat_type is not None:
            sql += " AND chat_type = %s"
            params.append(chat_type)
        if tag:
            sql += " AND FIND_IN_SET(%s, tags) > 0"
            params.append(tag)
        if priority is not None:
            sql += " AND priority = %s"
            params.append(priority)
        if overdue_only:
            sql += " AND due_date IS NOT NULL AND due_date < CURDATE() AND status = 0"

        sql += " ORDER BY priority ASC, due_date ASC, created_at DESC"
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        for row in rows:
            if row.get("due_date") and hasattr(row["due_date"], "isoformat"):
                row["due_date"] = row["due_date"].isoformat()

        r.setex(cache_key, CACHE_TTL, json.dumps(rows, default=str))
        return [_row_to_todo(row) for row in rows]

    @staticmethod
    def search(user_id: int, keyword: str) -> list[Todo]:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        like = f"%{keyword}%"
        cursor.execute(
            "SELECT * FROM todos WHERE (user_id = %s OR assignee_id = %s) AND title LIKE %s "
            "ORDER BY priority ASC, created_at DESC",
            (user_id, user_id, like)
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [_row_to_todo(row) for row in rows]

    @staticmethod
    def complete(todo_id: int, user_id: int) -> Optional[Todo]:
        now = int(time.time())
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE todos SET status = 1, completed_at = %s, updated_at = %s "
            "WHERE id = %s AND (user_id = %s OR assignee_id = %s) AND status = 0",
            (now, now, todo_id, user_id, user_id)
        )
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        if affected:
            TodoModel._invalidate_cache(user_id)
            return TodoModel.get_by_id(todo_id, user_id)
        return None

    @staticmethod
    def uncomplete(todo_id: int, user_id: int) -> bool:
        now = int(time.time())
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE todos SET status = 0, completed_at = NULL, updated_at = %s "
            "WHERE id = %s AND (user_id = %s OR assignee_id = %s) AND status = 1",
            (now, todo_id, user_id, user_id)
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
    def update_title(todo_id: int, user_id: int, title: str) -> bool:
        now = int(time.time())
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE todos SET title = %s, updated_at = %s WHERE id = %s AND user_id = %s",
            (title, now, todo_id, user_id)
        )
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        if affected:
            TodoModel._invalidate_cache(user_id)
        return affected > 0

    @staticmethod
    def update_description(todo_id: int, user_id: int, description: str) -> bool:
        now = int(time.time())
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE todos SET description = %s, updated_at = %s WHERE id = %s AND user_id = %s",
            (description, now, todo_id, user_id)
        )
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
            "UPDATE todos SET priority = %s, updated_at = %s WHERE id = %s AND (user_id = %s OR assignee_id = %s)",
            (priority, now, todo_id, user_id, user_id)
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
            "UPDATE todos SET due_date = %s, reminder_sent = 0, updated_at = %s "
            "WHERE id = %s AND (user_id = %s OR assignee_id = %s)",
            (due_date, now, todo_id, user_id, user_id)
        )
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        if affected:
            TodoModel._invalidate_cache(user_id)
        return affected > 0

    @staticmethod
    def update_repeat_rule(todo_id: int, user_id: int, rule: str) -> bool:
        now = int(time.time())
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE todos SET repeat_rule = %s, updated_at = %s WHERE id = %s AND user_id = %s",
            (rule, now, todo_id, user_id)
        )
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        if affected:
            TodoModel._invalidate_cache(user_id)
        return affected > 0

    @staticmethod
    def assign(todo_id: int, user_id: int, assignee_id: int, assignee_name: str) -> bool:
        now = int(time.time())
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE todos SET assignee_id = %s, assignee_name = %s, updated_at = %s "
            "WHERE id = %s AND user_id = %s",
            (assignee_id, assignee_name, now, todo_id, user_id)
        )
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        if affected:
            TodoModel._invalidate_cache(user_id)
            TodoModel._invalidate_cache(assignee_id)
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
            "SELECT status, COUNT(*) as cnt FROM todos "
            "WHERE (user_id = %s OR assignee_id = %s) GROUP BY status",
            (user_id, user_id)
        )
        rows = cursor.fetchall()
        # Count overdue
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM todos "
            "WHERE (user_id = %s OR assignee_id = %s) AND status = 0 "
            "AND due_date IS NOT NULL AND due_date < CURDATE()",
            (user_id, user_id)
        )
        overdue_row = cursor.fetchone()
        cursor.close()
        conn.close()
        counts = {"pending": 0, "completed": 0, "total": 0, "overdue": 0}
        for row in rows:
            if row["status"] == 0:
                counts["pending"] = row["cnt"]
            elif row["status"] == 1:
                counts["completed"] = row["cnt"]
        counts["total"] = counts["pending"] + counts["completed"]
        counts["overdue"] = overdue_row["cnt"] if overdue_row else 0
        return counts

    @staticmethod
    def get_due_reminders() -> list[Todo]:
        """Get todos due within the next hour that haven't been reminded."""
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM todos WHERE status = 0 AND reminder_sent = 0 "
            "AND due_date IS NOT NULL AND due_date = CURDATE()"
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [_row_to_todo(row) for row in rows]

    @staticmethod
    def mark_reminded(todo_id: int):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE todos SET reminder_sent = 1 WHERE id = %s", (todo_id,))
        cursor.close()
        conn.close()

    @staticmethod
    def get_daily_summary_users() -> list[int]:
        """Get user IDs who have pending todos and daily_summary enabled."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT t.user_id FROM todos t "
            "LEFT JOIN user_prefs p ON t.user_id = p.user_id "
            "WHERE t.status = 0 AND (p.daily_summary IS NULL OR p.daily_summary = 1)"
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [r[0] for r in rows]

    @staticmethod
    def get_overdue(user_id: int) -> list[Todo]:
        return TodoModel.list_by_user(user_id, overdue_only=True)
