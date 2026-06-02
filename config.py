import os
from dataclasses import dataclass
from datetime import timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    EMAIL: str | None = os.getenv("EMAIL")
    PASSWORD: str | None = os.getenv("PASSWORD")
    USE_REGISTRATION: int = int(os.getenv("USE_REGISTRATION", 0))

    SCORE_THRESHOLD: int = int(os.getenv("SCORE_THRESHOLD", 22))
    PENALTY_RATIO: float = float(os.getenv("PENALTY_RATIO", 0.7))

    LOG_DIR: Path = Path("logs")
    LOG_FORMAT: str = "[%(asctime)s.%(msecs)03d] %(levelname)-8s %(name)s:%(lineno)d - %(message)s"

    BOT_TOKEN: str | None = os.getenv("BOT_TOKEN")
    INTERVAL: int = int(os.getenv("INTERVAL", 3))
    OWNER_ID: int = int(os.getenv("OWNER_ID", -1))

    DB_PATH: str | None = os.getenv("DB_PATH")

    TIMEZONE: timezone = timezone(timedelta(hours=5))


cfg = Config()
