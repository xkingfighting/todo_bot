"""TalkOnly platform implementation using Polling mode."""

import logging
import time

import requests

from config.settings import settings
from platforms.base import BotPlatform, Chat, Message, Update, User

logger = logging.getLogger(__name__)


class TalkOnlyPlatform(BotPlatform):

    def __init__(self):
        self._token = settings.BOT_TOKEN
        self._base_url = settings.API_BASE_URL
        self._headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }
        self._running = False
        self._offset = 0

    def _request(self, method: str, data: dict = None) -> dict:
        url = f"{self._base_url}/{method}"
        try:
            logger.debug("API >> %s payload=%s", method, data)
            resp = requests.post(url, headers=self._headers, json=data or {}, timeout=settings.POLL_TIMEOUT + 10)
            resp.raise_for_status()
            result = resp.json()
            logger.debug("API << %s response=%s", method, result)
            return result
        except requests.RequestException as e:
            logger.error("API request failed: %s %s -> %s", method, data, e)
            return {"ok": False, "error_code": "REQUEST_FAILED", "description": str(e)}

    def _parse_update(self, raw: dict) -> Update:
        from_user = raw.get("from_user", {})
        chat = raw.get("chat", {})
        message = raw.get("message", {})
        return Update(
            update_id=raw["update_id"],
            user=User(
                id=from_user.get("id", 0),
                name=from_user.get("name", ""),
                is_group_owner=bool(from_user.get("is_group_owner", 0)),
                is_group_admin=bool(from_user.get("is_group_admin", 0)),
                group_role=from_user.get("group_role", "member"),
            ),
            chat=Chat(
                id=chat.get("id", 0),
                type=chat.get("type", "private"),
            ),
            message=Message(
                id=message.get("id", 0),
                type=message.get("type", "text"),
                text=message.get("text", ""),
            ),
            timestamp=raw.get("timestamp", 0),
        )

    # --- Public API ---

    def start_polling(self, on_update):
        self._running = True
        logger.info("Polling started (timeout=%ds)", settings.POLL_TIMEOUT)

        while self._running:
            data = self._request("getUpdates", {
                "offset": self._offset,
                "limit": settings.POLL_LIMIT,
                "timeout": settings.POLL_TIMEOUT,
            })

            if not data.get("ok"):
                logger.warning("getUpdates error: %s", data.get("description", "unknown"))
                time.sleep(3)
                continue

            updates = data.get("result", [])
            for raw in updates:
                try:
                    update = self._parse_update(raw)
                    on_update(update)
                except Exception:
                    logger.exception("Failed to handle update %s", raw.get("update_id"))
                finally:
                    self._offset = raw["update_id"] + 1

    def stop_polling(self):
        self._running = False
        logger.info("Polling stopped.")

    def send_message(self, chat_id: int, text: str, chat_type: str = "private",
                     msg_type: int = 1, reply_to: int = 0) -> dict:
        payload = {
            "chat_id": chat_id,
            "chat_type": chat_type,
            "text": text,
            "type": msg_type,
        }
        if reply_to:
            payload["reply_to_message_id"] = reply_to
        return self._request("sendMessage", payload)

    def send_typing(self, chat_id: int, chat_type: str = "private") -> dict:
        return self._request("sendTyping", {
            "chat_id": chat_id,
            "chat_type": chat_type,
        })

    def send_image(self, chat_id: int, image_url: str, caption: str = "",
                   chat_type: str = "private") -> dict:
        payload = {
            "chat_id": chat_id,
            "chat_type": chat_type,
            "image_url": image_url,
        }
        if caption:
            payload["caption"] = caption
        return self._request("sendImage", payload)

    def get_me(self) -> dict:
        return self._request("getMe")

    def delete_webhook(self, drop_pending: bool = False) -> dict:
        return self._request("deleteWebhook", {"drop_pending_updates": drop_pending})
