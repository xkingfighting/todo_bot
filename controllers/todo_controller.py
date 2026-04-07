"""Controller layer: handle commands and orchestrate Model + View."""

import logging
import re
import time
from datetime import datetime

from models.todo import Todo, TodoModel
from models.project import ProjectModel
from models.activity import ActivityLog
from models.user_prefs import UserPrefs
from views.todo_view import TodoView
from platforms.base import BotPlatform, Update
from utils.date_parser import parse_natural_date, parse_time
from i18n import t

logger = logging.getLogger(__name__)

SNOOZE_DURATIONS = {
    "1h": (3600, "1 hour"), "2h": (7200, "2 hours"),
    "4h": (14400, "4 hours"), "1d": (86400, "1 day"),
}


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
            "/today": self._cmd_today,
            "/done": self._cmd_done,
            "/doneall": self._cmd_doneall,
            "/undone": self._cmd_undone,
            "/del": self._cmd_delete,
            "/delete": self._cmd_delete,
            "/delall": self._cmd_delall,
            "/edit": self._cmd_edit,
            "/note": self._cmd_note,
            "/priority": self._cmd_priority,
            "/due": self._cmd_due,
            "/setdue": self._cmd_setdue,
            "/repeat": self._cmd_repeat,
            "/search": self._cmd_search,
            "/assign": self._cmd_assign,
            "/clear": self._cmd_clear,
            "/stats": self._cmd_stats,
            "/detail": self._cmd_detail,
            "/export": self._cmd_export,
            "/lang": self._cmd_lang,
            "/subtask": self._cmd_subtask,
            "/project": self._cmd_project,
            "/move": self._cmd_move,
            "/star": self._cmd_star,
            "/snooze": self._cmd_snooze,
            "/activity": self._cmd_activity,
        }

    def _get_lang(self, update: Update) -> str:
        prefs = UserPrefs.get(update.user.id)
        lang = prefs.get("language", "auto")
        if lang == "auto":
            lang = UserPrefs.detect_language(update.message.text)
        return lang

    def handle_update(self, update: Update):
        text = update.message.text.strip()
        if not text:
            return

        self.platform.send_typing(update.chat.id, update.chat.type)
        lang = self._get_lang(update)

        # First-use onboarding
        if UserPrefs.is_first_use(update.user.id):
            UserPrefs.mark_welcomed(update.user.id)
            if text == "/start" or not text.startswith("/"):
                reply_text, msg_type = self.view.onboarding(lang)
                self.platform.send_message(
                    chat_id=update.chat.id, text=reply_text,
                    chat_type=update.chat.type, msg_type=msg_type,
                )
                return

        parts = text.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if "@" in cmd:
            cmd = cmd.split("@")[0]

        handler = self._commands.get(cmd)
        if handler:
            reply_text, msg_type = handler(update, args, lang)
        else:
            reply_text, msg_type = t("err_unknown_cmd", lang), 1

        self.platform.send_message(
            chat_id=update.chat.id, text=reply_text,
            chat_type=update.chat.type, msg_type=msg_type,
            reply_to=update.message.id,
        )

    # === Core Commands ===

    def _cmd_start(self, update, args, lang):
        return self.view.welcome(lang)

    def _cmd_help(self, update, args, lang):
        return self.view.help_message(lang)

    def _cmd_add(self, update, args, lang):
        if not args:
            return self.view.error(t("err_add_usage", lang))

        title = args
        priority = 2
        due_date = None
        due_time = ""
        tags = []

        # Extract #tags (but not #high/#medium/#low, handle #project:N)
        project_id = 0
        tag_matches = re.findall(r'#(\S+)', title)
        priority_words = {"high", "medium", "low"}
        for tag in tag_matches:
            low = tag.lower()
            if low in priority_words:
                priority = {"high": 1, "medium": 2, "low": 3}[low]
            elif low.startswith("project:"):
                try:
                    project_id = int(low.split(":")[1])
                except (ValueError, IndexError):
                    pass
            else:
                tags.append(tag)
            title = title.replace(f"#{tag}", "").strip()

        # Natural language date parsing
        due_date, title = parse_natural_date(title)

        # Time parsing
        due_time, title = parse_time(title)
        if due_time is None:
            due_time = ""

        title = title.strip()
        if not title:
            return self.view.error(t("err_empty_title", lang))

        todo = self.model.create(
            user_id=update.user.id, chat_id=update.chat.id,
            chat_type=update.chat.type, title=title,
            priority=priority, due_date=due_date,
            tags=",".join(tags) if tags else "",
            due_time=due_time or "",
            project_id=project_id,
        )

        ActivityLog.log(update.chat.id, update.chat.type, update.user.id,
                        update.user.name, "created", todo.id, todo.title)
        return self.view.todo_created(todo, lang)

    def _cmd_list(self, update, args, lang):
        args = args.strip()
        lower = args.lower()

        if lower == "overdue":
            todos = self.model.get_overdue(update.user.id)
            return self.view.todo_list(todos, t("overdue_todos", lang), lang)
        if lower == "starred" or lower == "star":
            todos = self.model.list_by_user(update.user.id, status=0, starred_only=True)
            return self.view.todo_list(todos, t("starred_todos", lang), lang)
        if args.startswith("#"):
            tag = args[1:]
            todos = self.model.list_by_user(update.user.id, status=0, tag=tag)
            return self.view.todo_list(todos, f"#{tag}", lang)
        if lower.startswith("project:"):
            try:
                pid = int(lower.split(":")[1])
                todos = self.model.list_by_user(update.user.id, status=0, project_id=pid)
                proj = ProjectModel.get_by_id(pid, update.user.id)
                title = f"{proj.emoji} {proj.name}".strip() if proj else f"Project {pid}"
                return self.view.todo_list(todos, title, lang)
            except (ValueError, IndexError):
                pass
        if lower in ("high", "1"):
            todos = self.model.list_by_user(update.user.id, status=0, priority=1)
            return self.view.todo_list(todos, "High Priority", lang)
        if lower in ("medium", "2"):
            todos = self.model.list_by_user(update.user.id, status=0, priority=2)
            return self.view.todo_list(todos, "Medium Priority", lang)
        if lower in ("low", "3"):
            todos = self.model.list_by_user(update.user.id, status=0, priority=3)
            return self.view.todo_list(todos, "Low Priority", lang)

        todos = self.model.list_by_user(update.user.id, status=0)
        return self.view.todo_list(todos, t("pending_todos", lang), lang)

    def _cmd_all(self, update, args, lang):
        todos = self.model.list_by_user(update.user.id)
        return self.view.todo_list(todos, t("all_todos", lang), lang)

    def _cmd_today(self, update, args, lang):
        todos = self.model.list_by_user(update.user.id, today_only=True)
        return self.view.todo_list(todos, t("today_title", lang), lang)

    def _cmd_done(self, update, args, lang):
        todo_id = self._parse_id(args)
        if not todo_id:
            return self.view.error(t("err_done_usage", lang))
        completed_todo = self.model.complete(todo_id, update.user.id)
        if completed_todo:
            ActivityLog.log(update.chat.id, update.chat.type, update.user.id,
                            update.user.name, "completed", todo_id, completed_todo.title)
            if completed_todo.repeat_rule:
                self._recreate_recurring(completed_todo)
            return self.view.todo_completed(todo_id, lang)
        return self.view.not_found(todo_id, lang)

    def _cmd_doneall(self, update, args, lang):
        count = self.model.complete_all(update.user.id)
        return self.view.batch_done(count, lang)

    def _cmd_undone(self, update, args, lang):
        todo_id = self._parse_id(args)
        if not todo_id:
            return self.view.error(t("err_undone_usage", lang))
        if self.model.uncomplete(todo_id, update.user.id):
            return self.view.todo_uncompleted(todo_id, lang)
        return self.view.not_found(todo_id, lang)

    def _cmd_delete(self, update, args, lang):
        todo_id = self._parse_id(args)
        if not todo_id:
            return self.view.error(t("err_del_usage", lang))
        if self.model.delete(todo_id, update.user.id):
            ActivityLog.log(update.chat.id, update.chat.type, update.user.id,
                            update.user.name, "deleted", todo_id)
            return self.view.todo_deleted(todo_id, lang)
        return self.view.not_found(todo_id, lang)

    def _cmd_delall(self, update, args, lang):
        count = self.model.delete_all_completed(update.user.id)
        return self.view.batch_del(count, lang)

    def _cmd_edit(self, update, args, lang):
        parts = args.split(maxsplit=1)
        if len(parts) != 2:
            return self.view.error(t("err_edit_usage", lang))
        todo_id = self._parse_id(parts[0])
        new_title = parts[1].strip()
        if not todo_id:
            return self.view.error(t("err_id_invalid", lang))
        if not new_title:
            return self.view.error(t("err_empty_title", lang))
        if self.model.update_title(todo_id, update.user.id, new_title):
            return self.view.title_edited(todo_id, lang)
        return self.view.not_found(todo_id, lang)

    def _cmd_note(self, update, args, lang):
        parts = args.split(maxsplit=1)
        if len(parts) != 2:
            return self.view.error(t("err_note_usage", lang))
        todo_id = self._parse_id(parts[0])
        text = parts[1].strip()
        if not todo_id:
            return self.view.error(t("err_id_invalid", lang))
        if self.model.update_description(todo_id, update.user.id, text):
            return self.view.note_added(todo_id, lang)
        return self.view.not_found(todo_id, lang)

    def _cmd_priority(self, update, args, lang):
        parts = args.split()
        if len(parts) != 2:
            return self.view.error(t("err_priority_usage", lang))
        todo_id = self._parse_id(parts[0])
        try:
            priority = int(parts[1])
        except ValueError:
            return self.view.error(t("err_priority_invalid", lang))
        if priority not in (1, 2, 3):
            return self.view.error(t("err_priority_invalid", lang))
        if not todo_id:
            return self.view.error(t("err_id_invalid", lang))
        if self.model.update_priority(todo_id, update.user.id, priority):
            return self.view.priority_updated(todo_id, priority, lang)
        return self.view.not_found(todo_id, lang)

    def _cmd_due(self, update, args, lang):
        parts = args.split()
        if len(parts) < 2:
            return self.view.error(t("err_due_usage", lang))
        todo_id = self._parse_id(parts[0])
        if not todo_id:
            return self.view.error(t("err_id_invalid", lang))

        # Try natural language for the date part
        date_text = " ".join(parts[1:])
        due_date, _ = parse_natural_date(f"@{date_text}" if re.match(r'\d{4}-\d{2}-\d{2}', date_text) else date_text)
        if not due_date:
            # Try explicit format
            try:
                datetime.strptime(parts[1], "%Y-%m-%d")
                due_date = parts[1]
            except ValueError:
                return self.view.error(t("err_date_invalid", lang))

        if self.model.update_due_date(todo_id, update.user.id, due_date):
            return self.view.due_date_updated(todo_id, due_date, lang)
        return self.view.not_found(todo_id, lang)

    def _cmd_setdue(self, update, args, lang):
        todo_id = self._parse_id(args)
        if not todo_id:
            return self.view.error(t("err_setdue_usage", lang))
        todo = self.model.get_by_id(todo_id, update.user.id)
        if not todo:
            return self.view.not_found(todo_id, lang)
        return self.view.set_due_prompt(todo, lang)

    def _cmd_repeat(self, update, args, lang):
        parts = args.split()
        if len(parts) != 2:
            return self.view.error(t("err_repeat_usage", lang))
        todo_id = self._parse_id(parts[0])
        rule = parts[1].lower()
        if not todo_id:
            return self.view.error(t("err_id_invalid", lang))
        if rule == "off":
            rule = ""
        elif rule not in ("daily", "weekly", "monthly"):
            return self.view.error(t("err_repeat_invalid", lang))
        if self.model.update_repeat_rule(todo_id, update.user.id, rule):
            return self.view.repeat_set(todo_id, rule, lang)
        return self.view.not_found(todo_id, lang)

    def _cmd_search(self, update, args, lang):
        keyword = args.strip()
        if not keyword:
            return self.view.error(t("err_search_usage", lang))
        todos = self.model.search(update.user.id, keyword)
        return self.view.search_results(todos, keyword, lang)

    def _cmd_assign(self, update, args, lang):
        if update.chat.type == "private":
            return self.view.error(t("err_assign_private", lang))
        parts = args.split()
        if len(parts) < 2:
            return self.view.error(t("err_assign_usage", lang))
        todo_id = self._parse_id(parts[0])
        if not todo_id:
            return self.view.error(t("err_id_invalid", lang))
        assignee_id = self._parse_id(parts[1])
        if not assignee_id:
            return self.view.error(t("err_assign_usage", lang))
        assignee_name = parts[2] if len(parts) > 2 else str(assignee_id)
        if self.model.assign(todo_id, update.user.id, assignee_id, assignee_name):
            ActivityLog.log(update.chat.id, update.chat.type, update.user.id,
                            update.user.name, "assigned", todo_id, assignee_name)
            return self.view.assigned(todo_id, assignee_name, lang)
        return self.view.not_found(todo_id, lang)

    def _cmd_clear(self, update, args, lang):
        count = self.model.clear_completed(update.user.id)
        return self.view.cleared(count, lang)

    def _cmd_stats(self, update, args, lang):
        counts = self.model.count_by_user(update.user.id)
        return self.view.stats(counts, lang)

    def _cmd_detail(self, update, args, lang):
        todo_id = self._parse_id(args)
        if not todo_id:
            return self.view.error(t("err_id_invalid", lang))
        todo = self.model.get_by_id(todo_id, update.user.id)
        if not todo:
            return self.view.not_found(todo_id, lang)
        return self.view.todo_detail(todo, lang)

    def _cmd_export(self, update, args, lang):
        todos = self.model.list_by_user(update.user.id)
        if not todos:
            return self.view.error(t("no_todos", lang))
        filepath = self._generate_excel(todos, update.user.id, lang)
        return t("export_done", lang, path=filepath), 1

    def _cmd_lang(self, update, args, lang):
        new_lang = args.strip().lower()
        if not new_lang:
            return self.view.lang_select(lang)
        if new_lang == "auto":
            UserPrefs.set_language(update.user.id, "auto")
            return self.view.lang_set(lang)
        if new_lang not in ("en", "zh"):
            return self.view.lang_select(lang)
        UserPrefs.set_language(update.user.id, new_lang)
        return self.view.lang_set(new_lang)

    # === New Commands ===

    def _cmd_subtask(self, update, args, lang):
        parts = args.split(maxsplit=1)
        if len(parts) < 2:
            return self.view.error(t("err_subtask_usage", lang))
        parent_id = self._parse_id(parts[0])
        title = parts[1].strip()
        if not parent_id or not title:
            return self.view.error(t("err_subtask_usage", lang))
        parent = self.model.get_by_id(parent_id, update.user.id)
        if not parent:
            return self.view.not_found(parent_id, lang)
        sub = self.model.create(
            user_id=update.user.id, chat_id=update.chat.id,
            chat_type=update.chat.type, title=title,
            parent_id=parent_id, project_id=parent.project_id,
        )
        return self.view.subtask_added(sub.id, parent_id, lang)

    def _cmd_project(self, update, args, lang):
        parts = args.split(maxsplit=1)
        # No args: show project dashboard
        if not parts or not args.strip():
            projects = ProjectModel.list_by_user(update.user.id)
            return self.view.project_dashboard(projects, lang)

        action = parts[0].lower()
        name = parts[1].strip() if len(parts) > 1 else ""

        if action == "create" and name:
            proj = ProjectModel.create(update.user.id, update.chat.id, update.chat.type, name)
            return self.view.project_created_card(proj, lang)
        elif action == "delete" and name:
            # Support delete by ID or name
            proj = None
            try:
                pid = int(name)
                proj = ProjectModel.get_by_id(pid, update.user.id)
            except ValueError:
                proj = ProjectModel.find_by_name(update.user.id, name)
            if not proj:
                return self.view.error(t("err_project_not_found", lang))
            ProjectModel.delete(proj.id, update.user.id)
            return self.view.project_deleted_card(proj, lang)
        elif action == "view" and name:
            # View project detail
            try:
                pid = int(name)
                proj = ProjectModel.get_by_id(pid, update.user.id)
            except ValueError:
                proj = ProjectModel.find_by_name(update.user.id, name)
            if not proj:
                return self.view.error(t("err_project_not_found", lang))
            todos = self.model.list_by_user(update.user.id, status=0, project_id=proj.id)
            return self.view.project_detail(proj, todos, lang)
        elif action == "list" or action == "ls":
            projects = ProjectModel.list_by_user(update.user.id)
            return self.view.project_dashboard(projects, lang)
        else:
            # Treat as project name to view
            full_name = args.strip()
            proj = ProjectModel.find_by_name(update.user.id, full_name)
            if proj:
                todos = self.model.list_by_user(update.user.id, status=0, project_id=proj.id)
                return self.view.project_detail(proj, todos, lang)
            return self.view.error(t("err_project_usage", lang))

    def _cmd_move(self, update, args, lang):
        parts = args.split(maxsplit=1)
        if len(parts) != 2:
            return self.view.error(t("err_move_usage", lang))
        todo_id = self._parse_id(parts[0])
        proj_name = parts[1].strip()
        if not todo_id:
            return self.view.error(t("err_id_invalid", lang))
        proj = ProjectModel.find_by_name(update.user.id, proj_name)
        if not proj:
            return self.view.error(t("err_project_not_found", lang))
        if self.model.update_project(todo_id, update.user.id, proj.id):
            return self.view.project_assigned(todo_id, proj.name, lang)
        return self.view.not_found(todo_id, lang)

    def _cmd_star(self, update, args, lang):
        todo_id = self._parse_id(args)
        if not todo_id:
            return self.view.error(t("err_star_usage", lang))
        result = self.model.toggle_star(todo_id, update.user.id)
        if result is None:
            return self.view.not_found(todo_id, lang)
        return self.view.star_toggled(todo_id, bool(result), lang)

    def _cmd_snooze(self, update, args, lang):
        parts = args.split()
        if len(parts) != 2:
            return self.view.error(t("err_snooze_usage", lang))
        todo_id = self._parse_id(parts[0])
        duration_key = parts[1].lower()
        if not todo_id:
            return self.view.error(t("err_id_invalid", lang))
        if duration_key not in SNOOZE_DURATIONS:
            return self.view.error(t("err_snooze_invalid", lang))
        secs, label = SNOOZE_DURATIONS[duration_key]
        until = int(time.time()) + secs
        if self.model.snooze(todo_id, update.user.id, until):
            return self.view.snoozed(todo_id, label, lang)
        return self.view.not_found(todo_id, lang)

    def _cmd_activity(self, update, args, lang):
        if update.chat.type == "private":
            return self.view.error(t("err_assign_private", lang))
        entries = ActivityLog.recent(update.chat.id)
        return self.view.activity_log(entries, lang)

    # === Helpers ===

    def _generate_excel(self, todos, user_id, lang):
        import os
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from i18n import priority_label as p_label

        wb = Workbook()
        ws = wb.active
        ws.title = t("export_title", lang)

        headers = ["ID", t("status", lang), t("priority", lang), "Title",
                    t("due_date", lang), t("tags", lang), t("repeat", lang),
                    t("assignee", lang), t("description", lang)]
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        thin_border = Border(
            left=Side(style="thin"), right=Side(style="thin"),
            top=Side(style="thin"), bottom=Side(style="thin"),
        )

        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")
            cell.border = thin_border

        overdue_fill = PatternFill(start_color="FFE0E0", end_color="FFE0E0", fill_type="solid")
        done_font = Font(strikethrough=True, color="999999")
        today_str = datetime.now().strftime("%Y-%m-%d")

        for row_idx, todo in enumerate(todos, 2):
            status_str = t("completed", lang) if todo.status == 1 else t("pending", lang)
            is_overdue = todo.status == 0 and todo.due_date and str(todo.due_date) < today_str
            if is_overdue:
                status_str = t("overdue", lang)
            values = [
                todo.id, status_str, p_label(todo.priority, lang), todo.title,
                str(todo.due_date) if todo.due_date else "",
                todo.tags.replace(",", ", ") if todo.tags else "",
                todo.repeat_rule or "", todo.assignee_name or "",
                todo.description or "",
            ]
            for col, val in enumerate(values, 1):
                cell = ws.cell(row=row_idx, column=col, value=val)
                cell.border = thin_border
                if todo.status == 1:
                    cell.font = done_font
                if is_overdue:
                    cell.fill = overdue_fill

        for col in ws.columns:
            max_len = max((len(str(cell.value or "")) for cell in col), default=0)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)

        export_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "exports")
        os.makedirs(export_dir, exist_ok=True)
        filename = f"todos_{user_id}_{int(time.time())}.xlsx"
        filepath = os.path.join(export_dir, filename)
        wb.save(filepath)
        return os.path.abspath(filepath)

    def _recreate_recurring(self, todo: Todo):
        from datetime import timedelta
        next_due = None
        if todo.due_date:
            try:
                due = datetime.strptime(str(todo.due_date), "%Y-%m-%d")
                if todo.repeat_rule == "daily":
                    next_due = (due + timedelta(days=1)).strftime("%Y-%m-%d")
                elif todo.repeat_rule == "weekly":
                    next_due = (due + timedelta(weeks=1)).strftime("%Y-%m-%d")
                elif todo.repeat_rule == "monthly":
                    month = due.month % 12 + 1
                    year = due.year + (1 if due.month == 12 else 0)
                    next_due = due.replace(year=year, month=month).strftime("%Y-%m-%d")
            except ValueError:
                pass

        self.model.create(
            user_id=todo.user_id, chat_id=todo.chat_id, chat_type=todo.chat_type,
            title=todo.title, priority=todo.priority, due_date=next_due,
            description=todo.description, tags=todo.tags, repeat_rule=todo.repeat_rule,
            assignee_id=todo.assignee_id, assignee_name=todo.assignee_name,
            project_id=todo.project_id, due_time=todo.due_time,
        )

    @staticmethod
    def _parse_id(text: str) -> int | None:
        text = text.strip().lstrip("#")
        try:
            val = int(text)
            return val if val > 0 else None
        except (ValueError, TypeError):
            return None
