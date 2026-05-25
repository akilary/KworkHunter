import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.jobs import check_orders_job
from config import INTERVAL, OWNER_ID
from datetime import timedelta

log = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запуск мониторинга заказов"""
    chat, message, user = update.effective_chat, update.effective_message, update.effective_user

    if chat is None or message is None or user is None:
        log.warning("Команда /start получена без chat/message/user")
        return

    log.info("Получена команда /start: user_id=%s | username=%s | chat_id=%s", user.id, user.username, chat.id)

    if user.id != OWNER_ID:
        log.warning("Отказ в доступе к /start: user_id=%s | username=%s", user.id, user.username)
        await message.reply_text("Нет доступа")
        return

    job_queue = context.job_queue
    if job_queue is None:
        log.error("JobQueue не подключён")
        await message.reply_text("JobQueue не подключён")
        return

    chat_id = chat.id
    job_name = f"check_orders_job_{chat_id}"

    old_jobs = job_queue.get_jobs_by_name(job_name)
    for job in old_jobs:
        job.schedule_removal()

    if old_jobs:
        log.info("Удалены старые задачи мониторинга: chat_id=%s | count=%d", chat_id, len(old_jobs))

    job_queue.run_repeating(
        check_orders_job,
        interval=timedelta(hours=INTERVAL),
        first=5,
        chat_id=chat_id,
        name=f"check_orders_job_{chat_id}",
    )

    log.info("Мониторинг Kwork запущен: chat_id=%s | interval_hours=%s", chat_id, INTERVAL)

    await message.reply_text(f"Мониторинг Kwork запущен. Проверяю заказы каждые {INTERVAL} часа")
