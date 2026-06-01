import logging
from datetime import timedelta

from telegram import Update, Message, Chat, User
from telegram.ext import ContextTypes, JobQueue, CallbackContext

from bot.jobs import check_orders_job, cleanup_expired_job
from config import cfg

log = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запуск мониторинга заказов"""
    owner_context = await _validate_owner_request(update, context, "start")
    if owner_context is None:
        return

    chat, message, _, job_queue = owner_context

    chat_id = chat.id

    check_orders_job_name = f"check_orders_job_{chat_id}"
    cleanup_job_name = f"cleanup_expired_job_{chat_id}"

    _remove_old_jobs(job_queue, check_orders_job_name, "мониторинга", chat_id)
    _remove_old_jobs(job_queue, cleanup_job_name, "очистки", chat_id)

    job_queue.run_repeating(
        check_orders_job,
        interval=timedelta(hours=cfg.INTERVAL),
        first=10,
        chat_id=chat_id,
        name=check_orders_job_name,
    )

    log.info("Задача мониторинга Kwork запущена: chat_id=%s | interval_hours=%s", chat_id, cfg.INTERVAL)

    job_queue.run_repeating(
        cleanup_expired_job,
        interval=timedelta(hours=1),
        first=5,
        chat_id=chat_id,
        name=cleanup_job_name,
    )

    log.info("Задача очистки просроченных заказов запущена: chat_id=%s | interval_hours=1", chat_id)

    await message.reply_text(f"Мониторинг Kwork запущен. Проверяю заказы каждые {cfg.INTERVAL} часа")


async def _validate_owner_request(
        update: Update,
        context: CallbackContext,
        func_name: str
) -> tuple[Chat, Message, User, JobQueue] | None:
    """Проверяет, что команду вызвал владелец бота"""
    chat, message, user = update.effective_chat, update.effective_message, update.effective_user

    if chat is None or message is None or user is None:
        log.warning("Команда /%s получена без chat/message/user", func_name)
        return None

    log.info(
        "Получена команда /%s: user_id=%s | username=%s | chat_id=%s",
        func_name,
        user.id,
        user.username,
        chat.id,
    )

    if user.id != cfg.OWNER_ID:
        log.warning("Отказ в доступе к /%s: user_id=%s | username=%s", func_name, user.id, user.username)
        await message.reply_text("Нет доступа")
        return None

    job_queue = context.job_queue

    if job_queue is None:
        log.error("JobQueue не подключён")
        await message.reply_text("JobQueue не подключён")
        return None

    return chat, message, user, job_queue


def _remove_old_jobs(job_queue: JobQueue, job_name: str, job_label: str, chat_id: int) -> None:
    """Удаляет все старые задачи с указанным именем"""
    old_jobs = job_queue.get_jobs_by_name(job_name)

    if not old_jobs:
        log.debug("Старые задачи %s не найдены: chat_id=%s", job_label, chat_id)
        return

    for job in old_jobs:
        job.schedule_removal()

    if old_jobs:
        log.info(
            "Удалены старые задачи %s: chat_id=%s | count=%d",
            job_label,
            chat_id,
            len(old_jobs),
        )
