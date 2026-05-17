from random import uniform
from time import sleep

from config import USE_REGISTRATION, EMAIL, PASSWORD
from filters import analyze_order_text
from kwork import KworkClient, parse_orders
from loaders import load_keywords


def main() -> None:
    """Точка входа"""
    try:
        keywords = load_keywords()
    except Exception as e:
        print(f"Ошибка при загрузке ключевых слов: {e}")
        exit(1)

    kwork_client = KworkClient()

    if USE_REGISTRATION:
        kwork_client.login(EMAIL, PASSWORD)

    all_orders = []
    page = 1
    while True:
        print(f"Обработка страницы: {page}...")
        html_page = kwork_client.get_projects_page(page)
        if not html_page:
            break

        orders = parse_orders(html_page)
        all_orders += orders
        page += 1

        sleep(uniform(2.2, 5.8))

    passed_orders = []
    for order in all_orders:
        order_analysis = analyze_order_text(order.description, keywords)

        if order_analysis.passed():
            order.score = order_analysis.net()
            order.matched_keywords = order_analysis.matched_positive
            passed_orders.append(order)

    if USE_REGISTRATION:
        kwork_client.add_offer_views([order.id for order in passed_orders], True)

    print(f"Обработано страниц: {page}")
    print(f"Всего заказов: {len(all_orders)} | прошло по ключевым словам: {len(passed_orders)}")


if __name__ == "__main__":
    main()
