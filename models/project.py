"""Project model for organizing todos into lists."""

import time
from dataclasses import dataclass
from typing import Optional

from models.database import get_db


@dataclass
class Project:
    id: int = 0
    user_id: int = 0
    chat_id: int = 0
    chat_type: str = "private"
    name: str = ""
    emoji: str = ""
    created_at: int = 0


class ProjectModel:

    @staticmethod
    def create(user_id: int, chat_id: int, chat_type: str, name: str, emoji: str = "") -> Project:
        now = int(time.time())
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO projects (user_id, chat_id, chat_type, name, emoji, created_at) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (user_id, chat_id, chat_type, name, emoji, now)
        )
        pid = cursor.lastrowid
        cursor.close()
        conn.close()
        return Project(id=pid, user_id=user_id, chat_id=chat_id,
                       chat_type=chat_type, name=name, emoji=emoji, created_at=now)

    @staticmethod
    def list_by_user(user_id: int) -> list[Project]:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM projects WHERE user_id = %s ORDER BY created_at", (user_id,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [Project(**row) for row in rows]

    @staticmethod
    def get_by_id(project_id: int, user_id: int) -> Optional[Project]:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM projects WHERE id = %s AND user_id = %s", (project_id, user_id))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return Project(**row) if row else None

    @staticmethod
    def find_by_name(user_id: int, name: str) -> Optional[Project]:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM projects WHERE user_id = %s AND name = %s", (user_id, name))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return Project(**row) if row else None

    @staticmethod
    def delete(project_id: int, user_id: int) -> bool:
        conn = get_db()
        cursor = conn.cursor()
        # Unlink todos from this project
        cursor.execute("UPDATE todos SET project_id = 0 WHERE project_id = %s AND user_id = %s",
                        (project_id, user_id))
        cursor.execute("DELETE FROM projects WHERE id = %s AND user_id = %s", (project_id, user_id))
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        return affected > 0
