"""Todo Bot - Entry point with polling loop."""

import logging
import signal
import sys

from config.settings import settings
from models.database import init_database
from platforms.talkonly import TalkOnlyPlatform
from controllers.todo_controller import TodoController

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("todo_bot")


def main():
    logger.info("Starting Todo Bot...")

    # Validate config
    if not settings.BOT_TOKEN:
        logger.error("BOT_TOKEN is not set. Check your .env file.")
        sys.exit(1)

    # Init database
    init_database()

    # Init platform
    platform = TalkOnlyPlatform()

    # Switch to polling mode (delete any existing webhook)
    result = platform.delete_webhook(drop_pending=False)
    logger.info("deleteWebhook: %s", result)

    # Verify bot identity
    me = platform.get_me()
    if me.get("ok"):
        bot_info = me["result"]
        logger.info("Bot: %s (@%s)", bot_info.get("name"), bot_info.get("username"))
    else:
        logger.warning("getMe failed: %s", me.get("description", "unknown error"))

    # Init controller
    controller = TodoController(platform)

    # Graceful shutdown
    def shutdown(sig, frame):
        logger.info("Shutting down...")
        platform.stop_polling()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Start polling
    logger.info("Polling for updates...")
    platform.start_polling(controller.handle_update)


if __name__ == "__main__":
    main()
