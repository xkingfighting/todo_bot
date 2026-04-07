"""Todo model with CRUD operations."""

import json
import time
from dataclasses import dataclass
from typing import Optional

from models.database import get_db, get_redis

CACHE_PREFIX = "todo_bot:user_todos:"
CACHE_TTL = 300


@dataclass
class Todo:
    id: int = 0
    user_id: int = 0
    chat_id: int = 0
    chat_type: str = "private"
    title: str = ""
    description: Optional[str] = None
    priority: int = 2
    due_date: Optional[str] = None
    tags: str = ""
    repeat_rule: str = ""
    assignee_id: int = 0
    assignee_name: str = ""
    reminder_sent: int = 0
    parent_id: int = 0
    project_id: int = 0
    starred: int = 0
    due_time: str = ""
    snooze_until: int = 0
    status: int = 0
    completed_at: Optional[int] = None
    created_at: int = 0
    updated_at: int = 0


PRIORITY_LABELS = {1: "High", 2: "Medium", 3: "Low"}
PRIORITY_ICONS = {1: "!!!", 2: "!!", 3: "!"}

_FIELDS = set(Todo.__dataclass_fields__.keys())


def _row_to_todo(row: dict) -> Todo:
    for k in list(row.keys()):
        if k not in _FIELDS:
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
               assignee_id: int = 0, assignee_name: str = "",
               parent_id: int = 0, project_id: int = 0,
               due_time: str = "") -> Todo:
        now = int(time.time())
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO todos (user_id, chat_id, chat_type, title, description, priority, "
            "due_date, tags, repeat_rule, assignee_id, assignee_name, "
            "parent_id, project_id, due_time, created_at, updated_at) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (user_id, chat_id, chat_type, title, description, priority,
             due_date, tags, repeat_rule, assignee_id, assignee_name,
             parent_id, project_id, due_time, now, now)
        )
        todo_id = cursor.lastrowid
        cursor.close()
        conn.close()
        TodoModel._invalidate_cache(user_id)
        return Todo(id=todo_id, user_id=user_id, chat_id=chat_id, chat_type=chat_type,
                    title=title, description=description, priority=priority,
                    due_date=due_date, tags=tags, repeat_rule=repeat_rule,
                    assignee_id=assignee_id, assignee_name=assignee_name,
                    parent_id=parent_id, project_id=project_id, due_time=due_time,
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
        return _row_to_todo(row) if row else None

    @staticmethod
    def list_by_user(user_id: int, status: int = None, chat_id: int = None,
                     chat_type: str = None, tag: str = None,
                     priority: int = None, overdue_only: bool = False,
                     project_id: int = None, starred_only: bool = False,
                     today_only: bool = False, parent_id: int = None) -> list[Todo]:
        cache_key = (f"{CACHE_PREFIX}{user_id}:s{status}:c{chat_id}:{chat_type}"
                     f":t{tag}:p{priority}:o{overdue_only}:pj{project_id}"
                     f":st{starred_only}:td{today_only}:pa{parent_id}")
        r = get_redis()
        cached = r.get(cache_key)
        if cached:
            rows = json.loads(cached)
            return [Todo(**row) for row in rows]

        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        sql = "SELECT * FROM todos WHERE (user_id = %s OR assignee_id = %s)"
        params: list = [user_id, user_id]

        # Default: only top-level tasks (not subtasks) unless parent_id specified
        if parent_id is not None:
            sql += " AND parent_id = %s"
            params.append(parent_id)
        elif parent_id is None and not overdue_only and not today_only:
            sql += " AND parent_id = 0"

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
        if project_id is not None:
            sql += " AND project_id = %s"
            params.append(project_id)
        if starred_only:
            sql += " AND starred = 1"
        if overdue_only:
            sql += " AND due_date IS NOT NULL AND due_date < CURDATE() AND status = 0"
        if today_only:
            sql += " AND status = 0 AND (due_date = CURDATE() OR DATE(FROM_UNIXTIME(created_at)) = CURDATE())"

        sql += " ORDER BY starred DESC, priority ASC, due_date ASC, created_at DESC"
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
    def get_subtasks(parent_id: int, user_id: int) -> list[Todo]:
        return TodoModel.list_by_user(user_id, parent_id=parent_id)

    @staticmethod
    def count_subtasks(parent_id: int) -> dict:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT status, COUNT(*) as cnt FROM todos WHERE parent_id = %s GROUP BY status",
            (parent_id,)
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        counts = {"total": 0, "done": 0}
        for row in rows:
            counts["total"] += row["cnt"]
            if row["status"] == 1:
                counts["done"] = row["cnt"]
        return counts

    @staticmethod
    def search(user_id: int, keyword: str) -> list[Todo]:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        like = f"%{keyword}%"
        cursor.execute(
            "SELECT * FROM todos WHERE (user_id = %s OR assignee_id = %s) AND title LIKE %s "
            "ORDER BY starred DESC, priority ASC, created_at DESC",
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
    def complete_all(user_id: int) -> int:
        now = int(time.time())
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE todos SET status = 1, completed_at = %s, updated_at = %s "
            "WHERE user_id = %s AND status = 0", (now, now, user_id)
        )
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        if affected:
            TodoModel._invalidate_cache(user_id)
        return affected

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
        # Also delete subtasks
        cursor.execute("DELETE FROM todos WHERE (id = %s OR parent_id = %s) AND user_id = %s",
                        (todo_id, todo_id, user_id))
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        if affected:
            TodoModel._invalidate_cache(user_id)
        return affected > 0

    @staticmethod
    def delete_all_completed(user_id: int) -> int:
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
    def update_title(todo_id: int, user_id: int, title: str) -> bool:
        return TodoModel._update_field(todo_id, user_id, "title", title)

    @staticmethod
    def update_description(todo_id: int, user_id: int, description: str) -> bool:
        return TodoModel._update_field(todo_id, user_id, "description", description)

    @staticmethod
    def update_priority(todo_id: int, user_id: int, priority: int) -> bool:
        return TodoModel._update_field(todo_id, user_id, "priority", priority)

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
    def update_due_time(todo_id: int, user_id: int, due_time: str) -> bool:
        return TodoModel._update_field(todo_id, user_id, "due_time", due_time)

    @staticmethod
    def update_repeat_rule(todo_id: int, user_id: int, rule: str) -> bool:
        return TodoModel._update_field(todo_id, user_id, "repeat_rule", rule)

    @staticmethod
    def update_project(todo_id: int, user_id: int, project_id: int) -> bool:
        return TodoModel._update_field(todo_id, user_id, "project_id", project_id)

    @staticmethod
    def toggle_star(todo_id: int, user_id: int) -> Optional[int]:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT starred FROM todos WHERE id = %s AND user_id = %s", (todo_id, user_id))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            conn.close()
            return None
        new_val = 0 if row["starred"] else 1
        now = int(time.time())
        cursor.execute("UPDATE todos SET starred = %s, updated_at = %s WHERE id = %s",
                        (new_val, now, todo_id))
        cursor.close()
        conn.close()
        TodoModel._invalidate_cache(user_id)
        return new_val

    @staticmethod
    def snooze(todo_id: int, user_id: int, until_ts: int) -> bool:
        now = int(time.time())
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE todos SET snooze_until = %s, reminder_sent = 0, updated_at = %s "
            "WHERE id = %s AND (user_id = %s OR assignee_id = %s)",
            (until_ts, now, todo_id, user_id, user_id)
        )
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        if affected:
            TodoModel._invalidate_cache(user_id)
        return affected > 0

    @staticmethod
    def assign(todo_id: int, user_id: int, assignee_id: int, assignee_name: str) -> bool:
        return TodoModel._update_fields(todo_id, user_id,
                                         {"assignee_id": assignee_id, "assignee_name": assignee_name})

    @staticmethod
    def clear_completed(user_id: int) -> int:
        return TodoModel.delete_all_completed(user_id)

    @staticmethod
    def count_by_user(user_id: int) -> dict:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT status, COUNT(*) as cnt FROM todos "
            "WHERE (user_id = %s OR assignee_id = %s) AND parent_id = 0 GROUP BY status",
            (user_id, user_id)
        )
        rows = cursor.fetchall()
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM todos "
            "WHERE (user_id = %s OR assignee_id = %s) AND status = 0 "
            "AND due_date IS NOT NULL AND due_date < CURDATE() AND parent_id = 0",
            (user_id, user_id)
        )
        overdue_row = cursor.fetchone()
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM todos "
            "WHERE user_id = %s AND starred = 1 AND status = 0 AND parent_id = 0",
            (user_id,)
        )
        starred_row = cursor.fetchone()
        cursor.close()
        conn.close()
        counts = {"pending": 0, "completed": 0, "total": 0, "overdue": 0, "starred": 0}
        for row in rows:
            if row["status"] == 0:
                counts["pending"] = row["cnt"]
            elif row["status"] == 1:
                counts["completed"] = row["cnt"]
        counts["total"] = counts["pending"] + counts["completed"]
        counts["overdue"] = overdue_row["cnt"] if overdue_row else 0
        counts["starred"] = starred_row["cnt"] if starred_row else 0
        return counts

    @staticmethod
    def get_due_reminders() -> list[Todo]:
        now_ts = int(time.time())
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM todos WHERE status = 0 AND reminder_sent = 0 "
            "AND due_date IS NOT NULL AND due_date = CURDATE() "
            "AND (snooze_until = 0 OR snooze_until <= %s)",
            (now_ts,)
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
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT t.user_id FROM todos t "
            "LEFT JOIN user_prefs p ON t.user_id = p.user_id "
            "WHERE t.status = 0 AND t.parent_id = 0 "
            "AND (p.daily_summary IS NULL OR p.daily_summary = 1)"
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [r[0] for r in rows]

    @staticmethod
    def get_overdue(user_id: int) -> list[Todo]:
        return TodoModel.list_by_user(user_id, overdue_only=True)

    @staticmethod
    def _update_field(todo_id: int, user_id: int, field: str, value) -> bool:
        now = int(time.time())
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE todos SET `{field}` = %s, updated_at = %s "
            "WHERE id = %s AND (user_id = %s OR assignee_id = %s)",
            (value, now, todo_id, user_id, user_id)
        )
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        if affected:
            TodoModel._invalidate_cache(user_id)
        return affected > 0

    @staticmethod
    def _update_fields(todo_id: int, user_id: int, fields: dict) -> bool:
        now = int(time.time())
        sets = ", ".join(f"`{k}` = %s" for k in fields)
        vals = list(fields.values()) + [now, todo_id, user_id]
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE todos SET {sets}, updated_at = %s WHERE id = %s AND user_id = %s", vals
        )
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        if affected:
            TodoModel._invalidate_cache(user_id)
        return affected > 0
