import json
import logging
from datetime import datetime, timedelta

from models.order import Order

log = logging.getLogger(__name__)


def parse_orders(html: str) -> list[Order]:
    """Парсит список заказов из HTML страницы Kwork"""
    log.debug("Начало парсинга HTML страницы заказов")

    state_data_start = html.find('window.stateData=')
    if state_data_start == -1:
        log.error("Не найден 'window.stateData=' в HTML странице")
        return []

    json_start = html.find("{", state_data_start)
    if json_start == -1:
        log.error("Не удалось определить начало JSON")
        return []

    json_end = html.find("};", json_start)
    if json_end == -1:
        log.error("Не удалось определить конец JSON")
        return []

    try:
        state_data = json.loads(html[json_start:json_end + 1])
    except json.JSONDecodeError:
        log.exception("Ошибка декодирования stateData JSON")
        return []

    raw_orders = (
        state_data
        .get("wantsListData", {})
        .get("pagination", {})
        .get("data", [])
    )

    if not raw_orders:
        log.warning("Список заказов пуст или данные отсутствуют")
        return []

    log.info("Получено сырых заказов: %d", len(raw_orders))

    orders = []
    for i, order in enumerate(raw_orders, 1):
        try:
            order_id = int(order.get("id"))
        except (TypeError, ValueError):
            log.warning("Пропуск заказа #%d: некорректный order_id (%s)", i, order.get("id"))
            continue

        try:
            price = float(order.get("priceLimit", 0.0))
        except (TypeError, ValueError):
            log.warning("Некорректная цена у заказа %s, установлено значение 0.0", order_id)
            price = 0.0

        title = order.get("name", "").strip()
        if not title:
            log.warning("У заказа %s отсутствует title", order_id)

        try:
            date_expire = datetime.strptime(
                order.get("date_expire", ""),
                "%Y-%m-%d %H:%M:%S"
            )
        except (TypeError, ValueError):
            log.warning(
                "Некорректная дата окончания у заказа %s (%s), используется значение по умолчанию",
                order_id,
                order.get("date_expire"),
            )
            date_expire = datetime.now() + timedelta(days=3)

        parsed_order = Order(
            id=order_id,
            title=title or "-",
            description=order.get("description", "").strip(),
            price=price,
            username=order.get("user", {}).get("username", "-"),
            url=f"https://kwork.ru/projects/{order_id}",
            date_expire=date_expire + timedelta(hours=2),
        )

        log.debug(
            "Заказ обработан: id=%s | price=%.2f | user=%s",
            parsed_order.id,
            parsed_order.price,
            parsed_order.username,
        )

        orders.append(parsed_order)

    if not orders:
        log.warning("После обработки не осталось валидных заказов")
        return []

    log.info("Парсинг завершён успешно: валидных заказов=%d", len(orders))
    return orders
