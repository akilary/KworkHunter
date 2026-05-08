import json

import requests
from fake_useragent import UserAgent

HEADERS = {
    "User-Agent": UserAgent().random,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru,en;q=0.9",
    "Referer": "https://kwork.ru/",
}

session = requests.Session()
session.headers.update(HEADERS)


def login(username, password):
    payload = {
        "l_username": username,
        "l_password": password,
        "jlog": 1,
        "l_remember_me": "1",
        "recaptcha_pass_token": "",
        "smart-token": "",
        "track_client_id": False,
    }

    r = session.post(
        "https://kwork.ru/api/user/login",
        data=payload,
        timeout=10,
    )

    print(f"[LOGIN] Status code: {r.status_code}")
    print(f"[LOGIN] Cookies: {session.cookies.get_dict()}")
    print(f"[LOGIN] Success: {json.loads(r.text)['success']}")


def get_orders():
    for page in range(1, 3):
        r = session.get(
            f"https://kwork.ru/projects?page={page}",
            timeout=10,
        )

        html = r.text

        state_data_start = html.find('window.stateData=')

        if state_data_start == -1:
            print(f"[PAGE {page}] window.stateData не найден")
            continue

        json_start = html.find("{", state_data_start)
        json_end = html.find("};", json_start)

        if json_end == -1:
            print(f"[PAGE {page}] Конец JSON не найден")
            continue

        state_data = json.loads(html[json_start:json_end + 1])

        orders = (
            state_data
            .get("wantsListData", {})
            .get("pagination", {})
            .get("data", [])
        )

        print(f"\n{'=' * 60}")
        print(f"СТРАНИЦА {page}")
        print(f"Найдено заказов: {len(orders)}")
        print(f"{'=' * 60}")

        print(f"\nСтраница: {page}")
        for order in orders:
            order_id = order.get("id")
            title = order.get("name")
            price = order.get("priceLimit")
            description = order.get("description", "").strip()
            username = order.get("user", {}).get("username")
            views = order.get("views_dirty")
            time_left = order.get("timeLeft")

            print(f"ID: {order_id}")
            print(f"Название: {title}")
            print(f"Цена: {price} ₽")
            print(f"Заказчик: {username}")
            print(f"Просмотры: {views}")
            print(f"Осталось: {time_left}")
            print(f"Описание: {description[:300]}...")
            print('-' * 60)


login("@gmail.com", "psw")
get_orders()
