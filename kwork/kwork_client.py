import json

from fake_useragent import UserAgent
from requests import Session

HEADERS = {
    "User-Agent": UserAgent().random,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru,en;q=0.9",
    "Referer": "https://kwork.ru/",
}


class KworkClient:
    """Клиент для работы с API и страницами Kwork"""

    def __init__(self):
        """Создаёт HTTP-сессию и устанавливает заголовки"""
        self.session = Session()
        self.session.headers.update(HEADERS)

    def login(self, username: str, password: str, show_response: bool = False) -> bool:
        """Авторизует пользователя по логину и паролю"""
        payload = {
            "l_username": username,
            "l_password": password,
            "jlog": 1,
            "l_remember_me": "1",
            "recaptcha_pass_token": "",
            "smart-token": "",
            "track_client_id": False,
        }

        r = self.session.post("https://kwork.ru/api/user/login", data=payload, timeout=10)

        if show_response:
            print(f"Cookies: {self.session.cookies.get_dict()}")
            print(f"Success: {json.loads(r.text)})")

        return r.status_code == 200 and json.loads(r.text)['success'] == True

    def get_projects_page(self, page: int) -> str | None:
        """Возвращает HTML страницы проектов"""
        r = self.session.get(f"https://kwork.ru/projects?view=0&page={page}", timeout=10)

        if "page=" not in r.url:
            return None

        return r.text

    def add_offer_views(self, want_ids: list[int], show_response: bool = False) -> bool:
        """Отмечает предложения как просмотренные"""
        r = self.session.post("https://kwork.ru/api/offer/addview", json={"wantIds": want_ids}, timeout=10)

        if show_response:
            print(f"Status code: {r.status_code}")
            print(f"Response: {r.text}")

        return r.status_code == 200 and json.loads(r.text)["result"] == True
