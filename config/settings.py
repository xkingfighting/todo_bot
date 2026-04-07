import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Bot
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

    # MySQL
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "app")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "todo_bot")

    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "127.0.0.1")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

    # Polling
    POLL_TIMEOUT: int = int(os.getenv("POLL_TIMEOUT", "25"))
    POLL_LIMIT: int = int(os.getenv("POLL_LIMIT", "100"))

    # TalkOnly API
    API_BASE_URL: str = "https://chat.ichuk.com/Open/Bot"


settings = Settings()
