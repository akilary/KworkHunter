import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
USE_REGISTRATION = int(os.getenv("USE_REGISTRATION", 0))

SCORE_THRESHOLD = int(os.getenv("SCORE_THRESHOLD", 22))
PENALTY_RATIO = float(os.getenv("PENALTY_RATIO", 0.7))

LOG_DIR = Path("logs")
LOG_FORMAT = "[%(asctime)s.%(msecs)03d] %(levelname)-8s %(name)s:%(lineno)d - %(message)s"

BOT_TOKEN = os.getenv("BOT_TOKEN")
INTERVAL = int(os.getenv("INTERVAL", 3))
OWNER_ID = int(os.getenv("OWNER_ID", -1))
