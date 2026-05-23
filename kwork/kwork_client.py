from logging import getLogger

from fake_useragent import UserAgent
from requests import Session, RequestException

HEADERS = {
    "User-Agent": UserAgent().random,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru,en;q=0.9",
    "Referer": "https://kwork.ru/",
}

log = getLogger(__name__)


class KworkClient:
    """Клиент для работы с API и страницами Kwork"""

    def __init__(self):
        """Создаёт HTTP-сессию и устанавливает заголовки"""
        self.session = Session()
        self.session.headers.update(HEADERS)

        log.debug("HTTP-сессия KworkClient создана")

    def login(self, username: str, password: str) -> bool:
        """Авторизует пользователя по логину и паролю"""
        log.info("Попытка авторизации пользователя '%s'", username)

        payload = {
            "l_username": username,
            "l_password": password,
            "jlog": 1,
            "l_remember_me": "1",
            "recaptcha_pass_token": "",
            "smart-token": "",
            "track_client_id": False,
        }

        try:
            r = self.session.post("https://kwork.ru/api/user/login", data=payload, timeout=10)
            r.raise_for_status()

            data = r.json()

            log.debug("Ответ авторизации: %s", data)
            log.debug("Cookies: %s", self.session.cookies.get_dict())

            success = data.get("success", False)

            if success:
                log.info("Авторизация успешно выполнена")
            else:
                log.warning("Не удалось авторизоваться")

            return success
        except RequestException:
            log.exception("Ошибка HTTP при авторизации")
            return False
        except ValueError:
            log.exception("Не удалось декодировать JSON ответа авторизации")
            return False

    def get_projects_page(self, page: int) -> str | None:
        """Возвращает HTML страницы проектов"""
        log.debug("Запрос страницы проектов: page=%s", page)

        try:
            r = self.session.get(f"https://kwork.ru/projects?view=0&page={page}", timeout=10)
            r.raise_for_status()

            if "page=" not in r.url:
                log.warning("Страница проектов не получена (редирект): page=%s", page)
                return None

            log.info("Страница проектов %s успешно получена", page)

            return r.text
        except RequestException:
            log.exception("Ошибка при получении страницы проектов: page=%s", page)
            return None

    def add_offer_views(self, want_ids: list[int]) -> bool:
        """Отмечает предложения как просмотренные"""
        log.debug("Отправка отметки просмотров для %s офферов", len(want_ids))

        try:
            r = self.session.post("https://kwork.ru/api/offer/addview", json={"wantIds": want_ids}, timeout=10)
            r.raise_for_status()

            data = r.json()
            log.debug("Ответ addview: %s", data)
            success = data.get("result", False)

            if success:
                log.info("Отмечено как просмотренные: %s офферов", len(want_ids))
            else:
                log.warning("Kwork не подтвердил просмотр офферов: %s", want_ids, )

            return success
        except RequestException:
            log.exception("Ошибка при отметке просмотров офферов", )
        except ValueError:
            log.exception("Не удалось декодировать JSON ответа")

        return False
