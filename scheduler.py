"""Background scheduler for due reminders and daily summary."""

import logging
import threading
import time
from datetime import datetime

from models.todo import TodoModel
from models.user_prefs import UserPrefs
from views.todo_view import TodoView
from platforms.base import BotPlatform

logger = logging.getLogger(__name__)


class Scheduler:

    def __init__(self, platform: BotPlatform):
        self.platform = platform
        self.view = TodoView()
        self._running = False
        self._thread = None
        self._last_reminder_check = 0
        self._last_summary_hour = -1

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("Scheduler started.")

    def stop(self):
        self._running = False
        logger.info("Scheduler stopped.")

    def _loop(self):
        while self._running:
            try:
                now = datetime.now()

                # Check reminders every 10 minutes
                ts = int(time.time())
                if ts - self._last_reminder_check >= 600:
                    self._check_reminders()
                    self._last_reminder_check = ts

                # Daily summary at 9:00 AM
                if now.hour == 9 and self._last_summary_hour != now.hour:
                    self._send_daily_summaries()
                    self._last_summary_hour = now.hour

                if now.hour != 9:
                    self._last_summary_hour = -1

            except Exception:
                logger.exception("Scheduler error")

            time.sleep(60)

    def _check_reminders(self):
        todos = TodoModel.get_due_reminders()
        for todo in todos:
            try:
                prefs = UserPrefs.get(todo.user_id)
                lang = prefs.get("language", "en")
                if lang == "auto":
                    lang = "zh" if any('\u4e00' <= c <= '\u9fff' for c in todo.title) else "en"

                text, msg_type = self.view.reminder(todo, lang)
                self.platform.send_message(
                    chat_id=todo.user_id,
                    text=text,
                    chat_type="private",
                    msg_type=msg_type,
                )
                TodoModel.mark_reminded(todo.id)
                logger.info("Sent reminder for todo #%d to user %d", todo.id, todo.user_id)
            except Exception:
                logger.exception("Failed to send reminder for todo #%d", todo.id)

    def _send_daily_summaries(self):
        user_ids = TodoModel.get_daily_summary_users()
        for user_id in user_ids:
            try:
                prefs = UserPrefs.get(user_id)
                lang = prefs.get("language", "en")
                if lang == "auto":
                    lang = "zh"

                counts = TodoModel.count_by_user(user_id)
                if counts["pending"] == 0:
                    continue

                text, msg_type = self.view.daily_summary(counts, lang)
                self.platform.send_message(
                    chat_id=user_id,
                    text=text,
                    chat_type="private",
                    msg_type=msg_type,
                )
                logger.info("Sent daily summary to user %d", user_id)
            except Exception:
                logger.exception("Failed to send daily summary to user %d", user_id)
