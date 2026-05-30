import logging
import sqlite3

from config import DB_PATH

log = logging.getLogger(__name__)


def create_engine() -> None:
    """Создаёт базы данных и таблиц, если их ещё нет"""
    log.debug("Инициализация базы данных: path=%s", DB_PATH)

    try:
        with sqlite3.connect(DB_PATH) as con:
            con.execute("""
            CREATE TABLE IF NOT EXISTS Orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                external_id INT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                price REAL NOT NULL,
                username TEXT NOT NULL,
                url TEXT NOT NULL,
                date_expire TEXT NOT NULL,
                score INTEGER,
                matched_keywords TEXT
            )
            """)
    except sqlite3.Error:
        log.exception("Ошибка при инициализации базы данных")
        raise

    log.info("База данных инициализирована")
