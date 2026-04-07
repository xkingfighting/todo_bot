"""View layer: format Todo data into platform-agnostic message structures."""

import json
from models.todo import Todo, PRIORITY_LABELS, PRIORITY_ICONS


STATUS_ICONS = {0: "[ ]", 1: "[x]"}


class TodoView:

    @staticmethod
    def welcome() -> tuple[str, int]:
        """Return (text, msg_type) for welcome message."""
        text = (
            "Welcome to Todo Bot!\n\n"
            "I help you manage your tasks. Here are the commands:\n\n"
            "/add <task> - Add a new todo\n"
            "/list - Show all pending todos\n"
            "/all - Show all todos\n"
            "/done <id> - Mark as completed\n"
            "/undone <id> - Reopen a todo\n"
            "/del <id> - Delete a todo\n"
            "/priority <id> <1|2|3> - Set priority\n"
            "/due <id> <YYYY-MM-DD> - Set due date\n"
            "/clear - Clear completed todos\n"
            "/stats - Show statistics\n"
            "/help - Show this help"
        )
        return text, 1

    @staticmethod
    def help_message() -> tuple[str, int]:
        return TodoView.welcome()

    @staticmethod
    def todo_created(todo: Todo) -> tuple[str, int]:
        """ActionCard for newly created todo."""
        card = {
            "text": f"Todo #{todo.id} created!\n\n{todo.title}",
            "buttons": [
                {"label": "Done", "command": f"/done {todo.id}", "style": "primary"},
                {"label": "Set High Priority", "command": f"/priority {todo.id} 1"},
                {"label": "Delete", "command": f"/del {todo.id}"},
            ]
        }
        return json.dumps(card), 10

    @staticmethod
    def todo_list(todos: list[Todo], title: str = "Your Todos") -> tuple[str, int]:
        """ListCard for todo list."""
        if not todos:
            return "No todos found. Use /add <task> to create one!", 1

        items = []
        for t in todos:
            status_icon = STATUS_ICONS.get(t.status, "[ ]")
            priority_icon = PRIORITY_ICONS.get(t.priority, "!")
            due_str = f" | Due: {t.due_date}" if t.due_date else ""
            items.append({
                "title": f"{status_icon} #{t.id} {t.title}",
                "description": f"{priority_icon} {PRIORITY_LABELS.get(t.priority, 'Medium')}{due_str}",
                "command": f"/detail {t.id}",
            })

        card = {"title": title, "items": items}
        return json.dumps(card), 11

    @staticmethod
    def todo_detail(todo: Todo) -> tuple[str, int]:
        """DetailCard for a single todo."""
        fields = [
            {"label": "Status", "value": "Completed" if todo.status == 1 else "Pending"},
            {"label": "Priority", "value": PRIORITY_LABELS.get(todo.priority, "Medium")},
        ]
        if todo.due_date:
            fields.append({"label": "Due Date", "value": str(todo.due_date)})
        if todo.description:
            fields.append({"label": "Description", "value": todo.description})

        buttons = []
        if todo.status == 0:
            buttons.append({"label": "Done", "command": f"/done {todo.id}", "style": "primary"})
        else:
            buttons.append({"label": "Reopen", "command": f"/undone {todo.id}"})
        buttons.append({"label": "Delete", "command": f"/del {todo.id}"})

        card = {
            "title": f"Todo #{todo.id}: {todo.title}",
            "fields": fields,
            "buttons": buttons,
        }
        return json.dumps(card), 13

    @staticmethod
    def todo_completed(todo_id: int) -> tuple[str, int]:
        card = {
            "text": f"Todo #{todo_id} marked as completed!",
            "buttons": [
                {"label": "Undo", "command": f"/undone {todo_id}"},
                {"label": "View List", "command": "/list"},
            ]
        }
        return json.dumps(card), 10

    @staticmethod
    def todo_uncompleted(todo_id: int) -> tuple[str, int]:
        card = {
            "text": f"Todo #{todo_id} reopened!",
            "buttons": [
                {"label": "Done", "command": f"/done {todo_id}", "style": "primary"},
                {"label": "View List", "command": "/list"},
            ]
        }
        return json.dumps(card), 10

    @staticmethod
    def todo_deleted(todo_id: int) -> tuple[str, int]:
        return f"Todo #{todo_id} deleted.", 1

    @staticmethod
    def priority_updated(todo_id: int, priority: int) -> tuple[str, int]:
        return f"Todo #{todo_id} priority set to {PRIORITY_LABELS.get(priority, 'Medium')}.", 1

    @staticmethod
    def due_date_updated(todo_id: int, due_date: str) -> tuple[str, int]:
        return f"Todo #{todo_id} due date set to {due_date}.", 1

    @staticmethod
    def cleared(count: int) -> tuple[str, int]:
        return f"Cleared {count} completed todo(s).", 1

    @staticmethod
    def stats(counts: dict) -> tuple[str, int]:
        """DetailCard for statistics."""
        card = {
            "title": "Todo Statistics",
            "fields": [
                {"label": "Total", "value": str(counts["total"])},
                {"label": "Pending", "value": str(counts["pending"])},
                {"label": "Completed", "value": str(counts["completed"])},
            ],
            "buttons": [
                {"label": "View Pending", "command": "/list"},
                {"label": "View All", "command": "/all"},
            ]
        }
        return json.dumps(card), 13

    @staticmethod
    def error(message: str) -> tuple[str, int]:
        return f"Error: {message}", 1

    @staticmethod
    def not_found(todo_id: int) -> tuple[str, int]:
        return f"Todo #{todo_id} not found.", 1
