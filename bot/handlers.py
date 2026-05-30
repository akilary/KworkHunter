import logging
from datetime import timedelta

from telegram import Update
from telegram.ext import ContextTypes, JobQueue

from bot.jobs import check_orders_job, cleanup_expired_job
from config import INTERVAL, OWNER_ID

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

    check_orders_job_name = f"check_orders_job_{chat_id}"
    cleanup_job_name = f"cleanup_expired_job_{chat_id}"

    _remove_old_jobs(job_queue, check_orders_job_name, "мониторинга", chat_id)
    _remove_old_jobs(job_queue, cleanup_job_name, "очистки", chat_id)

    job_queue.run_repeating(
        check_orders_job,
        interval=timedelta(hours=INTERVAL),
        first=5,
        chat_id=chat_id,
        name=check_orders_job_name,
    )

    log.info("Задача мониторинга Kwork запущена: chat_id=%s | interval_hours=%s", chat_id, INTERVAL)

    job_queue.run_repeating(
        cleanup_expired_job,
        interval=timedelta(hours=1),
        first=5,
        chat_id=chat_id,
        name=cleanup_job_name,
    )

    log.info("Задача очистки просроченных заказов запущена: chat_id=%s | interval_hours=1", chat_id)

    await message.reply_text(f"Мониторинг Kwork запущен. Проверяю заказы каждые {INTERVAL} часа")


def _remove_old_jobs(job_queue: JobQueue, job_name: str, job_label: str, chat_id: int) -> None:
    """Удаляет все старые задачи с указанным именем"""
    old_jobs = job_queue.get_jobs_by_name(job_name)

    for job in old_jobs:
        job.schedule_removal()

    if old_jobs:
        log.info(
            "Удалены старые задачи %s: chat_id=%s | count=%d",
            job_label,
            chat_id,
            len(old_jobs),
        )
