from random import uniform
from time import sleep

from config import USE_REGISTRATION, EMAIL, PASSWORD
from kwork import KworkClient, parse_orders


def main() -> None:
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

    if USE_REGISTRATION:
        kwork_client.add_offer_views([order.id for order in all_orders])

    print(f"Обработано страниц: {page}")
    print(f"Всего заказов: {len(all_orders)}")


if __name__ == "__main__":
    main()
