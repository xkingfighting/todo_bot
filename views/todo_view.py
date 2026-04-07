"""View layer: format Todo data into TalkOnly card messages with i18n."""

import json
from datetime import datetime, timedelta
from functools import partial
from models.todo import Todo, TodoModel, PRIORITY_ICONS
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
        if todo.due_date:
            text += f"\n{t('due_date', lang)}: {todo.due_date}"
            if todo.due_time:
                text += f" {todo.due_time}"
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
            star = "*" if todo.starred else ""
            status_icon = STATUS_ICONS.get(todo.status, "[ ]")
            p_icon = PRIORITY_ICONS.get(todo.priority, "!")
            p_lbl = priority_label(todo.priority, lang)
            desc = f"{p_icon} {p_lbl}"

            if todo.due_date:
                desc += f" | {todo.due_date}"
                if todo.due_time:
                    desc += f" {todo.due_time}"
                if todo.status == 0 and str(todo.due_date) < today:
                    desc += f" {t('overdue', lang)}"
            if todo.tags:
                desc += f" | #{todo.tags.replace(',', ' #')}"
            if todo.assignee_name:
                desc += f" | @{todo.assignee_name}"

            # Subtask progress
            sub_counts = TodoModel.count_subtasks(todo.id)
            if sub_counts["total"] > 0:
                desc += f" | {t('subtasks', lang)} {t('subtask_progress', lang, done=sub_counts['done'], total=sub_counts['total'])}"

            items.append({
                "title": f"{star}{status_icon} #{todo.id} {todo.title}",
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
        if todo.starred:
            status_val += " *"

        fields = [
            {"label": t("status", lang), "value": status_val},
            {"label": t("priority", lang), "value": priority_label(todo.priority, lang)},
        ]
        if todo.due_date:
            due_val = str(todo.due_date)
            if todo.due_time:
                due_val += f" {todo.due_time}"
            fields.append({"label": t("due_date", lang), "value": due_val})
        if todo.tags:
            fields.append({"label": t("tags", lang), "value": f"#{todo.tags.replace(',', ' #')}"})
        if todo.repeat_rule:
            fields.append({"label": t("repeat", lang), "value": repeat_label(todo.repeat_rule, lang)})
        if todo.assignee_name:
            fields.append({"label": t("assignee", lang), "value": todo.assignee_name})
        if todo.description:
            fields.append({"label": t("description", lang), "value": todo.description})

        # Subtask progress
        sub_counts = TodoModel.count_subtasks(todo.id)
        if sub_counts["total"] > 0:
            fields.append({"label": t("subtasks", lang),
                           "value": t("subtask_progress", lang, done=sub_counts["done"], total=sub_counts["total"])})

        # Project name
        if todo.project_id:
            from models.project import ProjectModel
            proj = ProjectModel.get_by_id(todo.project_id, todo.user_id)
            if proj:
                fields.append({"label": "Project", "value": f"{proj.emoji} {proj.name}".strip()})

        buttons = []
        if todo.status == 0:
            buttons.append({"label": t("done", lang), "command": f"/done {todo.id}", "style": "primary"})
        else:
            buttons.append({"label": t("reopen", lang), "command": f"/undone {todo.id}"})

        # Star toggle
        star_label = t("unstarred", lang) if todo.starred else t("starred", lang)
        buttons.append({"label": f"* {star_label}", "command": f"/star {todo.id}"})

        for p in (1, 2, 3):
            if p != todo.priority:
                buttons.append({"label": f"{t('priority', lang)}: {priority_label(p, lang)}",
                                "command": f"/priority {todo.id} {p}"})
        buttons.append({"label": t("set_due", lang), "command": f"/setdue {todo.id}"})
        buttons.append({"label": f"+ {t('subtasks', lang)}", "command": f"/subtask {todo.id} "})
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
            {"label": t("starred", lang), "value": str(counts.get("starred", 0))},
        ]
        card = {
            "title": t("stats_title", lang),
            "fields": fields,
            "buttons": [
                {"label": t("view_pending", lang), "command": "/list"},
                {"label": t("today_title", lang), "command": "/today"},
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
        card = {
            "text": "Select Language / 选择语言",
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
    def subtask_added(sub_id: int, parent_id: int, lang: str) -> tuple[str, int]:
        return t("subtask_added", lang, id=sub_id, parent_id=parent_id), 1

    @staticmethod
    def project_dashboard(projects: list, lang: str) -> tuple[str, int]:
        """Main project view: list all projects with actions."""
        if not projects:
            card = {
                "text": t("no_projects", lang),
                "buttons": [
                    {"label": t("project_create_btn", lang), "command": "/project create ", "style": "primary"},
                ]
            }
            return _dumps(card), 10

        items = []
        for p in projects:
            label = f"{p.emoji} {p.name}".strip() if p.emoji else p.name
            # Count todos in project
            count = TodoModel.list_by_user(p.user_id, status=0, project_id=p.id)
            items.append({
                "title": label,
                "description": f"{len(count)} {t('pending', lang)}",
                "command": f"/project view {p.id}",
            })

        card = {"text": t("project_list_title", lang), "items": items}
        # Send list card + follow up with action buttons
        return _dumps(card), 11

    @staticmethod
    def project_created_card(project, lang: str) -> tuple[str, int]:
        """ActionCard after creating a project."""
        name = f"{project.emoji} {project.name}".strip() if project.emoji else project.name
        card = {
            "text": t("project_created", lang, name=name),
            "buttons": [
                {"label": t("project_view_btn", lang), "command": f"/project view {project.id}", "style": "primary"},
                {"label": t("project_list_btn", lang), "command": "/project"},
            ]
        }
        return _dumps(card), 10

    @staticmethod
    def project_deleted_card(project, lang: str) -> tuple[str, int]:
        """ActionCard after deleting a project."""
        card = {
            "text": t("project_deleted", lang, name=project.name),
            "buttons": [
                {"label": t("project_list_btn", lang), "command": "/project"},
            ]
        }
        return _dumps(card), 10

    @staticmethod
    def project_detail(project, todos: list[Todo], lang: str) -> tuple[str, int]:
        """DetailCard for a single project with its tasks and actions."""
        name = f"{project.emoji} {project.name}".strip() if project.emoji else project.name
        pending = sum(1 for t_ in todos if t_.status == 0)

        fields = [
            {"label": t("pending", lang), "value": str(pending)},
            {"label": t("total", lang), "value": str(len(todos))},
        ]

        buttons = [
            {"label": f"+ {t('project_add_task', lang)}", "command": f"/add #project:{project.id} ", "style": "primary"},
            {"label": t("project_view_tasks", lang), "command": f"/list project:{project.id}"},
            {"label": t("delete", lang), "command": f"/project delete {project.id}"},
            {"label": t("back", lang), "command": "/project"},
        ]

        card = {
            "title": name,
            "fields": fields,
            "buttons": buttons,
        }
        return _dumps(card), 13

    @staticmethod
    def project_assigned(todo_id: int, name: str, lang: str) -> tuple[str, int]:
        card = {
            "text": t("project_assigned", lang, id=todo_id, name=name),
            "buttons": [
                {"label": t("view_list", lang), "command": "/list"},
                {"label": t("project_list_btn", lang), "command": "/project"},
            ]
        }
        return _dumps(card), 10

    @staticmethod
    def star_toggled(todo_id: int, starred: bool, lang: str) -> tuple[str, int]:
        status = t("starred", lang) if starred else t("unstarred", lang)
        return t("star_toggled", lang, id=todo_id, status=status), 1

    @staticmethod
    def batch_done(count: int, lang: str) -> tuple[str, int]:
        return t("doneall", lang, count=count), 1

    @staticmethod
    def batch_del(count: int, lang: str) -> tuple[str, int]:
        return t("delall", lang, count=count), 1

    @staticmethod
    def snoozed(todo_id: int, duration: str, lang: str) -> tuple[str, int]:
        return t("snoozed", lang, id=todo_id, duration=duration), 1

    @staticmethod
    def due_time_set(todo_id: int, time_str: str, lang: str) -> tuple[str, int]:
        return t("due_time_set", lang, id=todo_id, time=time_str), 1

    @staticmethod
    def activity_log(entries: list[dict], lang: str) -> tuple[str, int]:
        if not entries:
            return t("no_activity", lang), 1
        lines = [t("activity_title", lang), ""]
        for e in entries[:20]:
            action = e.get("action", "")
            key = f"act_{action}"
            line = t(key, lang, user=e.get("user_name", "?"),
                     id=e.get("todo_id", 0), detail=e.get("detail", ""))
            lines.append(line)
        return "\n".join(lines), 1

    @staticmethod
    def reminder(todo: Todo, lang: str) -> tuple[str, int]:
        text = t("reminder", lang, id=todo.id, title=todo.title)
        if todo.due_time:
            text += f"\n{todo.due_time}"
        card = {
            "text": text,
            "buttons": [
                {"label": t("done", lang), "command": f"/done {todo.id}", "style": "primary"},
                {"label": "Snooze 1h", "command": f"/snooze {todo.id} 1h"},
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
                {"label": t("today_title", lang), "command": "/today"},
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
