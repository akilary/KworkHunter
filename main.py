import logging

from telegram.ext import ApplicationBuilder, CommandHandler, Application

from bot.handlers import start, stop, settings
from config import cfg
from database.engine import create_engine
from utils import setup_logging

setup_logging()
log = logging.getLogger(__name__)


def _register_handler(app: Application) -> None:
    """Регистрация Обработчиков"""
    handlers = {
        "start": start,
        "stop": stop,
        "settings": settings,
    }

    for command, handler in handlers.items():
        app.add_handler(CommandHandler(command, handler))


def main() -> None:
    """Точка входа"""
    create_engine()

    log.info("Запуск Telegram-бота")

    app = ApplicationBuilder().token(cfg.BOT_TOKEN).build()

    _register_handler(app)
    log.debug("Обработчики зарегистрированы")

    log.info("Бот запущен в режиме polling")
    app.run_polling()


if __name__ == "__main__":
    main()
