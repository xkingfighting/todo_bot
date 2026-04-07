"""Controller layer: handle commands and orchestrate Model + View."""

import logging
import re
from datetime import datetime

from models.todo import TodoModel
from views.todo_view import TodoView
from platforms.base import BotPlatform, Update

logger = logging.getLogger(__name__)


class TodoController:

    def __init__(self, platform: BotPlatform):
        self.platform = platform
        self.view = TodoView()
        self.model = TodoModel()
        self._commands = {
            "/start": self._cmd_start,
            "/help": self._cmd_help,
            "/add": self._cmd_add,
            "/list": self._cmd_list,
            "/all": self._cmd_all,
            "/done": self._cmd_done,
            "/undone": self._cmd_undone,
            "/del": self._cmd_delete,
            "/delete": self._cmd_delete,
            "/priority": self._cmd_priority,
            "/due": self._cmd_due,
            "/clear": self._cmd_clear,
            "/stats": self._cmd_stats,
            "/detail": self._cmd_detail,
        }

    def handle_update(self, update: Update):
        """Route incoming update to the appropriate command handler."""
        text = update.message.text.strip()
        if not text:
            return

        # Send typing indicator
        self.platform.send_typing(update.chat.id, update.chat.type)

        # Parse command
        parts = text.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        # Handle @bot suffix in group chats (e.g. /list@todo_bot)
        if "@" in cmd:
            cmd = cmd.split("@")[0]

        handler = self._commands.get(cmd)
        if handler:
            reply_text, msg_type = handler(update, args)
        else:
            # Not a recognized command - show help hint
            reply_text, msg_type = "Unknown command. Type /help to see available commands.", 1

        self.platform.send_message(
            chat_id=update.chat.id,
            text=reply_text,
            chat_type=update.chat.type,
            msg_type=msg_type,
            reply_to=update.message.id,
        )

    def _cmd_start(self, update: Update, args: str) -> tuple[str, int]:
        return self.view.welcome()

    def _cmd_help(self, update: Update, args: str) -> tuple[str, int]:
        return self.view.help_message()

    def _cmd_add(self, update: Update, args: str) -> tuple[str, int]:
        if not args:
            return self.view.error("Usage: /add <task title>")

        # Parse optional flags: /add Buy milk #high @2026-04-10
        title = args
        priority = 2
        due_date = None

        # Extract priority tag
        priority_match = re.search(r'#(high|medium|low)', title, re.IGNORECASE)
        if priority_match:
            p = priority_match.group(1).lower()
            priority = {"high": 1, "medium": 2, "low": 3}[p]
            title = title.replace(priority_match.group(0), "").strip()

        # Extract due date
        due_match = re.search(r'@(\d{4}-\d{2}-\d{2})', title)
        if due_match:
            due_date = due_match.group(1)
            try:
                datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                return self.view.error("Invalid date format. Use YYYY-MM-DD.")
            title = title.replace(due_match.group(0), "").strip()

        if not title:
            return self.view.error("Task title cannot be empty.")

        todo = self.model.create(
            user_id=update.user.id,
            chat_id=update.chat.id,
            chat_type=update.chat.type,
            title=title,
            priority=priority,
            due_date=due_date,
        )
        return self.view.todo_created(todo)

    def _cmd_list(self, update: Update, args: str) -> tuple[str, int]:
        todos = self.model.list_by_user(update.user.id, status=0)
        return self.view.todo_list(todos, title="Pending Todos")

    def _cmd_all(self, update: Update, args: str) -> tuple[str, int]:
        todos = self.model.list_by_user(update.user.id)
        return self.view.todo_list(todos, title="All Todos")

    def _cmd_done(self, update: Update, args: str) -> tuple[str, int]:
        todo_id = self._parse_id(args)
        if not todo_id:
            return self.view.error("Usage: /done <id>")
        if self.model.complete(todo_id, update.user.id):
            return self.view.todo_completed(todo_id)
        return self.view.not_found(todo_id)

    def _cmd_undone(self, update: Update, args: str) -> tuple[str, int]:
        todo_id = self._parse_id(args)
        if not todo_id:
            return self.view.error("Usage: /undone <id>")
        if self.model.uncomplete(todo_id, update.user.id):
            return self.view.todo_uncompleted(todo_id)
        return self.view.not_found(todo_id)

    def _cmd_delete(self, update: Update, args: str) -> tuple[str, int]:
        todo_id = self._parse_id(args)
        if not todo_id:
            return self.view.error("Usage: /del <id>")
        if self.model.delete(todo_id, update.user.id):
            return self.view.todo_deleted(todo_id)
        return self.view.not_found(todo_id)

    def _cmd_priority(self, update: Update, args: str) -> tuple[str, int]:
        parts = args.split()
        if len(parts) != 2:
            return self.view.error("Usage: /priority <id> <1|2|3>\n1=High, 2=Medium, 3=Low")
        todo_id = self._parse_id(parts[0])
        try:
            priority = int(parts[1])
        except ValueError:
            return self.view.error("Priority must be 1 (High), 2 (Medium), or 3 (Low).")
        if priority not in (1, 2, 3):
            return self.view.error("Priority must be 1 (High), 2 (Medium), or 3 (Low).")
        if not todo_id:
            return self.view.error("Invalid todo ID.")
        if self.model.update_priority(todo_id, update.user.id, priority):
            return self.view.priority_updated(todo_id, priority)
        return self.view.not_found(todo_id)

    def _cmd_due(self, update: Update, args: str) -> tuple[str, int]:
        parts = args.split()
        if len(parts) != 2:
            return self.view.error("Usage: /due <id> <YYYY-MM-DD>")
        todo_id = self._parse_id(parts[0])
        due_date = parts[1]
        try:
            datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            return self.view.error("Invalid date format. Use YYYY-MM-DD.")
        if not todo_id:
            return self.view.error("Invalid todo ID.")
        if self.model.update_due_date(todo_id, update.user.id, due_date):
            return self.view.due_date_updated(todo_id, due_date)
        return self.view.not_found(todo_id)

    def _cmd_clear(self, update: Update, args: str) -> tuple[str, int]:
        count = self.model.clear_completed(update.user.id)
        return self.view.cleared(count)

    def _cmd_stats(self, update: Update, args: str) -> tuple[str, int]:
        counts = self.model.count_by_user(update.user.id)
        return self.view.stats(counts)

    def _cmd_detail(self, update: Update, args: str) -> tuple[str, int]:
        todo_id = self._parse_id(args)
        if not todo_id:
            return self.view.error("Usage: /detail <id>")
        todo = self.model.get_by_id(todo_id, update.user.id)
        if not todo:
            return self.view.not_found(todo_id)
        return self.view.todo_detail(todo)

    @staticmethod
    def _parse_id(text: str) -> int | None:
        text = text.strip().lstrip("#")
        try:
            val = int(text)
            return val if val > 0 else None
        except (ValueError, TypeError):
            return None
