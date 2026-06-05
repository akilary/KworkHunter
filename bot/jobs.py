import asyncio
import logging

from telegram.error import TelegramError
from telegram.ext import ContextTypes

from database.requests import delete_expired_orders
from services.kwork_monitor import check_kwork_orders
from utils.message_formatter import build_summary_message, build_order_message

log = logging.getLogger(__name__)


async def check_orders_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Задача для проверки и отправки заказов"""
    job = context.job
    if job is None:
        log.error("check_orders_job вызван без context.job")
        return

    chat_id = job.chat_id
    if chat_id is None:
        log.error("check_orders_job вызван без chat_id")
        return

    result = await asyncio.to_thread(check_kwork_orders)

    if not result.new_orders:
        log.debug("Подходящих заказов для отправки нет")
        return

    sorted_orders = sorted(
        result.new_orders,
        key=lambda o: o.score or 0,
        reverse=True,
    )

    try:
        await context.bot.send_message(chat_id=chat_id, text=build_summary_message(result))
    except TelegramError:
        log.exception("Ошибка при отправке статистики проверки заказов")
        return

    total_orders = len(sorted_orders)

    for i, order in enumerate(sorted_orders, start=1):
        message = build_order_message(order, i, total_orders)

        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=message,
            )
        except TelegramError:
            log.exception("Ошибка при отправке уведомления о заказе: id=%s", order.id)
            continue

        log.info("Уведомление о заказе отправлено: id=%s | chat_id=%s", order.id, chat_id)


async def cleanup_expired_job(_) -> None:
    """Задача для удаления просроченных заказов из базы данных"""
    log.debug("Очистка просроченных заказов")
    await asyncio.to_thread(delete_expired_orders)
