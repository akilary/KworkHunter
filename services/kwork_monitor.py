import logging
from random import uniform
from time import sleep

from config import cfg
from database.requests import add_orders, get_processed_order_ids
from filters import analyze_order_text
from kwork import KworkClient, parse_orders
from models.order import Order
from utils import load_keywords

log = logging.getLogger(__name__)


def check_kwork_orders() -> list[Order]:
    """Проверка и фильтрация заказов"""
    try:
        keywords = load_keywords()
    except (FileNotFoundError, ValueError):
        log.exception("Ошибка при загрузке ключевых слов")
        return []

    kwork_client = KworkClient()

    if cfg.USE_REGISTRATION:
        log.info("Авторизация в Kwork...")

        if not kwork_client.login(cfg.EMAIL, cfg.PASSWORD):
            log.error("Не удалось авторизоваться в Kwork")
            return []

        log.info("Авторизация выполнена успешно")

    all_orders = []
    page = 1
    while True:
        log.info("Загружаем страницу заказов: %d", page)
        html_page = kwork_client.get_projects_page(page)
        if not html_page:
            log.info("Страница %d пустая или недоступна. Завершаем сбор заказов", page)
            break

        orders = parse_orders(html_page)
        all_orders += orders

        log.info("Страница %d обработана: найдено заказов - %d", page, len(orders))
        page += 1

        delay = uniform(2.2, 5.8)
        log.debug("Пауза перед следующей страницей: %.2f сек.", delay)
        sleep(delay)

    passed_orders = []
    log.info("Начинаем фильтрацию заказов по ключевым словам")
    for order in all_orders:
        order_analysis = analyze_order_text(order.description, keywords)

        if order_analysis.passed():
            order.score = order_analysis.net()
            order.matched_keywords = [kb[0] for kb in order_analysis.matched_positive]
            passed_orders.append(order)

            log.debug(
                "Заказ прошёл фильтр: id=%s | score=%s | ключевые слова=%s",
                order.id,
                order.score,
                ", ".join(order.matched_keywords),
            )

    if cfg.USE_REGISTRATION and passed_orders:
        order_ids = [order.id for order in passed_orders]
        log.info("Отправляем просмотры офферов для заказов: %d", len(order_ids))

        kwork_client.add_offer_views(order_ids)
        log.info("Просмотры офферов успешно отправлены")

    processed_order_ids = get_processed_order_ids()

    new_passed_orders = [
        order
        for order in passed_orders
        if order.id not in processed_order_ids
    ]

    log.info(
        "Фильтрация уже обработанных заказов: подошло=%d | новых=%d | уже были=%d",
        len(passed_orders),
        len(new_passed_orders),
        len(passed_orders) - len(new_passed_orders),
    )

    add_orders(new_passed_orders)

    passed_orders = new_passed_orders

    log.info("Работа завершена")
    log.info(
        "Итог: обработано страниц - %d | всего заказов - %d | подошло - %d",
        page - 1,
        len(all_orders),
        len(passed_orders),
    )

    return passed_orders
