"""Abstract base class for bot platforms (TalkOnly, Telegram, etc.)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class User:
    id: int
    name: str
    is_group_owner: bool = False
    is_group_admin: bool = False
    group_role: str = "member"


@dataclass
class Chat:
    id: int
    type: str  # "private" or "group"


@dataclass
class Message:
    id: int
    type: str
    text: str


@dataclass
class Update:
    update_id: int
    user: User
    chat: Chat
    message: Message
    timestamp: int


class BotPlatform(ABC):
    """Abstract bot platform interface.

    Implement this class to support a new IM platform.
    """

    @abstractmethod
    def start_polling(self, on_update):
        """Start the polling loop. Calls on_update(update: Update) for each incoming update."""
        pass

    @abstractmethod
    def stop_polling(self):
        """Stop the polling loop gracefully."""
        pass

    @abstractmethod
    def send_message(self, chat_id: int, text: str, chat_type: str = "private",
                     msg_type: int = 1, reply_to: int = 0) -> dict:
        """Send a message to a chat."""
        pass

    @abstractmethod
    def send_typing(self, chat_id: int, chat_type: str = "private") -> dict:
        """Send typing indicator."""
        pass

    @abstractmethod
    def send_image(self, chat_id: int, image_url: str, caption: str = "",
                   chat_type: str = "private") -> dict:
        """Send an image message."""
        pass

    @abstractmethod
    def get_me(self) -> dict:
        """Get bot info."""
        pass
