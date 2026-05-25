import asyncio
import logging

from telegram.ext import ContextTypes

from services.kwork_monitor import check_kwork_orders

log = logging.getLogger(__name__)


async def check_orders_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Проверка и отправка заказов"""
    job = context.job
    if job is None:
        log.error("check_orders_job вызван без context.job")
        return

    chat_id = job.chat_id
    if chat_id is None:
        log.error("check_orders_job вызван без chat_id")
        return

    try:
        orders = await asyncio.to_thread(check_kwork_orders)
    except Exception:
        log.exception("Ошибка при проверке заказов Kwork")
        raise

    if not orders:
        log.debug("Подходящих заказов для отправки нет")
        return

    for order in sorted(orders, key=lambda o: o.score, reverse=True):
        message = (
            "Найден подходящий заказ\n\n"
            f"{order.title}\n"
            f"Цена: {order.price}\n"
            f"Релевантность: {order.score}\n\n"
            f"{order.description[:4000]}\n\n"
            f"{order.url}"
        )

        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=message,
            )
        except Exception:
            log.exception("Ошибка при отправке уведомления о заказе: id=%s", order.id)
            continue

        log.info("Уведомление о заказе отправлено: id=%s | chat_id=%s", order.id, chat_id)
