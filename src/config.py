import os
from dotenv import load_dotenv


load_dotenv()


def get_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


TELEGRAM_BOT_TOKEN: str = get_env("TELEGRAM_BOT_TOKEN")
DEFAULT_TOPICS: list[str] = [t.strip() for t in os.getenv("DEFAULT_TOPICS", "technology,world").split(",") if t.strip()]
ARTICLES_PER_TOPIC: int = int(os.getenv("ARTICLES_PER_TOPIC", "3"))


