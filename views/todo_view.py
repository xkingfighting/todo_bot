"""View layer: format Todo data into TalkOnly card messages with i18n."""

import json
from datetime import datetime, timedelta
from functools import partial
from models.todo import Todo, PRIORITY_ICONS
from i18n import t, priority_label, repeat_label

_dumps = partial(json.dumps, ensure_ascii=False, separators=(",", ":"))

STATUS_ICONS = {0: "[ ]", 1: "[x]"}


class TodoView:

    @staticmethod
    def welcome(lang: str) -> tuple[str, int]:
        return t("welcome", lang), 1

    @staticmethod
    def help_message(lang: str) -> tuple[str, int]:
        return t("welcome", lang), 1

    @staticmethod
    def onboarding(lang: str) -> tuple[str, int]:
        card = {
            "text": t("onboarding", lang),
            "buttons": [
                {"label": t("onboarding_btn", lang), "command": t("onboarding_cmd", lang), "style": "primary"},
                {"label": t("view_list", lang), "command": "/help"},
            ]
        }
        return _dumps(card), 10

    @staticmethod
    def todo_created(todo: Todo, lang: str) -> tuple[str, int]:
        text = t("todo_created", lang, id=todo.id, title=todo.title)
        if todo.tags:
            text += f"\n#{todo.tags.replace(',', ' #')}"
        card = {
            "text": text,
            "buttons": [
                {"label": t("done", lang), "command": f"/done {todo.id}", "style": "primary"},
                {"label": t("set_high", lang), "command": f"/priority {todo.id} 1"},
                {"label": t("set_due", lang), "command": f"/setdue {todo.id}"},
                {"label": t("delete", lang), "command": f"/del {todo.id}"},
            ]
        }
        return _dumps(card), 10

    @staticmethod
    def todo_list(todos: list[Todo], title: str, lang: str) -> tuple[str, int]:
        if not todos:
            return t("no_todos", lang), 1

        today = datetime.now().strftime("%Y-%m-%d")
        items = []
        for todo in todos:
            status_icon = STATUS_ICONS.get(todo.status, "[ ]")
            p_icon = PRIORITY_ICONS.get(todo.priority, "!")
            p_label = priority_label(todo.priority, lang)
            desc = f"{p_icon} {p_label}"
            if todo.due_date:
                desc += f" | {todo.due_date}"
                if todo.status == 0 and str(todo.due_date) < today:
                    desc += f" {t('overdue', lang)}"
            if todo.tags:
                desc += f" | #{todo.tags.replace(',', ' #')}"
            if todo.assignee_name:
                desc += f" | @{todo.assignee_name}"
            items.append({
                "title": f"{status_icon} #{todo.id} {todo.title}",
                "description": desc,
                "command": f"/detail {todo.id}",
            })

        card = {"text": title, "items": items}
        return _dumps(card), 11

    @staticmethod
    def todo_detail(todo: Todo, lang: str) -> tuple[str, int]:
        today = datetime.now().strftime("%Y-%m-%d")
        status_val = t("completed", lang) if todo.status == 1 else t("pending", lang)
        if todo.status == 0 and todo.due_date and str(todo.due_date) < today:
            status_val = t("overdue", lang)

        fields = [
            {"label": t("status", lang), "value": status_val},
            {"label": t("priority", lang), "value": priority_label(todo.priority, lang)},
        ]
        if todo.due_date:
            fields.append({"label": t("due_date", lang), "value": str(todo.due_date)})
        if todo.tags:
            fields.append({"label": t("tags", lang), "value": f"#{todo.tags.replace(',', ' #')}"})
        if todo.repeat_rule:
            fields.append({"label": t("repeat", lang), "value": repeat_label(todo.repeat_rule, lang)})
        if todo.assignee_name:
            fields.append({"label": t("assignee", lang), "value": todo.assignee_name})
        if todo.description:
            fields.append({"label": t("description", lang), "value": todo.description})

        buttons = []
        if todo.status == 0:
            buttons.append({"label": t("done", lang), "command": f"/done {todo.id}", "style": "primary"})
        else:
            buttons.append({"label": t("reopen", lang), "command": f"/undone {todo.id}"})
        for p in (1, 2, 3):
            if p != todo.priority:
                buttons.append({"label": f"{t('priority', lang)}: {priority_label(p, lang)}",
                                "command": f"/priority {todo.id} {p}"})
        buttons.append({"label": t("set_due", lang), "command": f"/setdue {todo.id}"})
        buttons.append({"label": t("delete", lang), "command": f"/del {todo.id}"})

        card = {
            "title": f"Todo #{todo.id}: {todo.title}",
            "fields": fields,
            "buttons": buttons,
        }
        return _dumps(card), 13

    @staticmethod
    def todo_completed(todo_id: int, lang: str) -> tuple[str, int]:
        card = {
            "text": t("todo_completed", lang, id=todo_id),
            "buttons": [
                {"label": t("undo", lang), "command": f"/undone {todo_id}"},
                {"label": t("view_list", lang), "command": "/list"},
            ]
        }
        return _dumps(card), 10

    @staticmethod
    def todo_uncompleted(todo_id: int, lang: str) -> tuple[str, int]:
        card = {
            "text": t("todo_reopened", lang, id=todo_id),
            "buttons": [
                {"label": t("done", lang), "command": f"/done {todo_id}", "style": "primary"},
                {"label": t("view_list", lang), "command": "/list"},
            ]
        }
        return _dumps(card), 10

    @staticmethod
    def set_due_prompt(todo: Todo, lang: str) -> tuple[str, int]:
        today = datetime.now()
        d1 = today.strftime("%Y-%m-%d")
        d3 = (today + timedelta(days=3)).strftime("%Y-%m-%d")
        d7 = (today + timedelta(days=7)).strftime("%Y-%m-%d")
        card = {
            "text": t("set_due_prompt", lang, id=todo.id, title=todo.title),
            "buttons": [
                {"label": t("today", lang), "command": f"/due {todo.id} {d1}", "style": "primary"},
                {"label": t("in_3_days", lang), "command": f"/due {todo.id} {d3}"},
                {"label": t("in_7_days", lang), "command": f"/due {todo.id} {d7}"},
                {"label": t("back", lang), "command": f"/detail {todo.id}"},
            ]
        }
        return _dumps(card), 10

    @staticmethod
    def todo_deleted(todo_id: int, lang: str) -> tuple[str, int]:
        return t("todo_deleted", lang, id=todo_id), 1

    @staticmethod
    def priority_updated(todo_id: int, priority: int, lang: str) -> tuple[str, int]:
        return t("priority_set", lang, id=todo_id, priority=priority_label(priority, lang)), 1

    @staticmethod
    def due_date_updated(todo_id: int, due_date: str, lang: str) -> tuple[str, int]:
        return t("due_set", lang, id=todo_id, date=due_date), 1

    @staticmethod
    def title_edited(todo_id: int, lang: str) -> tuple[str, int]:
        return t("title_edited", lang, id=todo_id), 1

    @staticmethod
    def note_added(todo_id: int, lang: str) -> tuple[str, int]:
        return t("note_added", lang, id=todo_id), 1

    @staticmethod
    def repeat_set(todo_id: int, rule: str, lang: str) -> tuple[str, int]:
        if rule:
            return t("repeat_set", lang, id=todo_id, rule=repeat_label(rule, lang)), 1
        return t("repeat_off", lang, id=todo_id), 1

    @staticmethod
    def assigned(todo_id: int, name: str, lang: str) -> tuple[str, int]:
        return t("assigned", lang, id=todo_id, name=name), 1

    @staticmethod
    def cleared(count: int, lang: str) -> tuple[str, int]:
        return t("cleared", lang, count=count), 1

    @staticmethod
    def stats(counts: dict, lang: str) -> tuple[str, int]:
        fields = [
            {"label": t("total", lang), "value": str(counts["total"])},
            {"label": t("pending", lang), "value": str(counts["pending"])},
            {"label": t("completed", lang), "value": str(counts["completed"])},
            {"label": t("overdue", lang), "value": str(counts["overdue"])},
        ]
        card = {
            "title": t("stats_title", lang),
            "fields": fields,
            "buttons": [
                {"label": t("view_pending", lang), "command": "/list"},
                {"label": t("view_all", lang), "command": "/all"},
            ]
        }
        return _dumps(card), 13

    @staticmethod
    def search_results(todos: list[Todo], keyword: str, lang: str) -> tuple[str, int]:
        if not todos:
            return t("no_results", lang, keyword=keyword), 1
        return TodoView.todo_list(todos, t("search_title", lang, keyword=keyword), lang)

    @staticmethod
    def lang_select(lang: str) -> tuple[str, int]:
        """ActionCard for language selection."""
        card = {
            "text": "🌐 Select Language / 选择语言",
            "buttons": [
                {"label": "English", "command": "/lang en", "style": "primary" if lang == "en" else ""},
                {"label": "中文", "command": "/lang zh", "style": "primary" if lang == "zh" else ""},
                {"label": "Auto / 自动", "command": "/lang auto"},
            ]
        }
        return _dumps(card), 10

    @staticmethod
    def lang_set(lang: str) -> tuple[str, int]:
        return t("lang_set", lang), 1

    @staticmethod
    def reminder(todo: Todo, lang: str) -> tuple[str, int]:
        card = {
            "text": t("reminder", lang, id=todo.id, title=todo.title),
            "buttons": [
                {"label": t("done", lang), "command": f"/done {todo.id}", "style": "primary"},
                {"label": t("view_list", lang), "command": "/list"},
            ]
        }
        return _dumps(card), 10

    @staticmethod
    def daily_summary(counts: dict, lang: str) -> tuple[str, int]:
        card = {
            "text": t("daily_summary_text", lang, pending=counts["pending"], overdue=counts["overdue"]),
            "buttons": [
                {"label": t("view_pending", lang), "command": "/list", "style": "primary"},
            ]
        }
        if counts["overdue"] > 0:
            card["buttons"].append({"label": t("overdue", lang), "command": "/list overdue"})
        return _dumps(card), 10

    @staticmethod
    def error(message: str) -> tuple[str, int]:
        return message, 1

    @staticmethod
    def not_found(todo_id: int, lang: str) -> tuple[str, int]:
        return t("err_not_found", lang, id=todo_id), 1
