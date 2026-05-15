import os

from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
USE_REGISTRATION = int(os.getenv("USE_REGISTRATION", 0))
