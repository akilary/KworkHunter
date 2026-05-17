import json
from dataclasses import dataclass


@dataclass
class _Order:
    id: int
    title: str
    description: str
    price: float
    username: str
    url: str
    score: int | None = None
    matched_keywords: list[str] | None = None


def parse_orders(html: str) -> list[_Order]:
    """Парсит список заказов из HTML страницы Kwork"""
    state_data_start = html.find('window.stateData=')
    if state_data_start == -1:
        raise ValueError("Не удалось найти 'window.stateData=' в HTML странице")

    json_start = html.find("{", state_data_start)
    if json_start == -1:
        raise ValueError(
            "Не удалось определить начало JSON с данными заказов"
        )

    json_end = html.find("};", json_start)
    if json_end == -1:
        raise ValueError("Не удалось определить начало JSON с данными заказов")

    try:
        state_data = json.loads(html[json_start:json_end + 1])
    except json.JSONDecodeError as e:
        raise ValueError(f"Ошибка декодирования stateData JSON: {e}") from e

    raw_orders = (
        state_data
        .get("wantsListData", {})
        .get("pagination", {})
        .get("data", [])
    )

    if not raw_orders:
        print("Список заказов пуст или данные отсутствуют")
        return []

    orders = []
    for i, order in enumerate(raw_orders, 1):
        try:
            order_id = int(order.get("id"))
        except (TypeError, ValueError):
            print(
                f"Пропуск заказа #{i}: некорректный order_id "
                f"({order.get('id')})"
            )
            continue

        try:
            price = float(order.get("priceLimit", 0.0))
        except (TypeError, ValueError):
            print(f"Некорректная цена у заказа {order_id}, установлено значение 0.0")
            price = 0.0

        title = order.get("name", "").strip()
        if not title:
            print(f"У заказа {order_id} отсутствует title")

        orders.append(
            _Order(
                id=order_id,
                title=title or "-",
                description=order.get("description", "").strip(),
                price=price,
                username=order.get("user", {}).get("username", "-"),
                url=f"https://kwork.ru/projects/{order_id}",
            )
        )

    if not orders:
        print("После обработки не осталось валидных заказов")
        return []

    return orders

