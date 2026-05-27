import logging

from telegram.ext import ApplicationBuilder, CommandHandler

from bot.handlers import start
from config import BOT_TOKEN
from database.engine import create_engine
from utils import setup_logging

setup_logging()
log = logging.getLogger(__name__)


def main() -> None:
    """Точка входа"""
    create_engine()

    log.info("Запуск Telegram-бота")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    log.debug("Обработчики зарегистрированы")

    log.info("Бот запущен в режиме polling")
    app.run_polling()


if __name__ == "__main__":
    main()
