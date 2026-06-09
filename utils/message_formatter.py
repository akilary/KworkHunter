import re
from datetime import datetime

from config import cfg
from models import KworkCheckResult
from models.order import Order
from html import unescape


def build_start_message(interval: int) -> str:
    """Создаёт сообщение о запуске мониторинга"""
    return (
        "✅ Мониторинг Kwork запущен\n\n"
        f"⏱ Интервал проверки: {interval} ч\n"
        "Первое сообщение по каждой проверке будет со статистикой, ниже — найденные заказы."
    )


def build_settings_message(active_jobs_count: int, jobs_info: str) -> str:
    """Создаёт сообщение с текущим состоянием мониторинга"""
    return "\n".join(
        (
            "✅ Мониторинг Kwork активен",
            f"Активных задач: {active_jobs_count}",
            "",
            "🧩 Задачи:",
            jobs_info,
            "",
            "⚙️ Настройки:",
            f"⏱ Интервал проверки: {cfg.INTERVAL} ч",
            f"🎯 Порог релевантности: {cfg.SCORE_THRESHOLD}",
            f"➖ Штраф: {cfg.PENALTY_RATIO}",
            f"📝 Регистрация: {'включена' if cfg.USE_REGISTRATION else 'выключена'}",
        )
    )


def build_settings_help_message() -> str:
    """Создаёт справку по команде настроек"""
    return (
        "Формат: /settings настройка значение\n\n"
        "Доступные настройки:\n"
        "interval (i)\n"
        "use_registration (reg)\n"
        "score_threshold (score)\n"
        "penalty_ratio (penalty)\n"
        "time_zone (tz)"
    )


def build_summary_message(result: KworkCheckResult) -> str:
    """Создаёт сводку по результатам проверки заказов"""
    check_time = datetime.now(cfg.TIMEZONE).strftime("%H:%M")

    return (
        "🔎 Проверка заказов\n\n"
        f"⏰ Время: {check_time}\n\n"
        "📊 Статистика\n"
        f"- Страниц проверено: {result.pages_checked}\n"
        f"- Всего найдено: {result.total_orders}\n"
        f"- Прошли фильтр: {result.passed_orders}\n"
        f"- Уже в базе: {result.already_in_db_orders}\n"
        f"- Новых заказов: {len(result.new_orders)}\n\n"
        "---------------"
    )


def build_order_message(order: Order, index: int, total: int) -> str:
    """Создаёт сообщение с информацией о заказе"""
    price = _format_price(order.price)
    score = order.score if order.score is not None else "—"
    keywords = ", ".join(order.matched_keywords[:8]) if order.matched_keywords else ""

    title = _format_text(order.title)
    description = _format_text(order.description, limit=3000)

    message = (
        f"📌 Заказ #{index} из {total}\n\n"
        f"💰 Бюджет: {price}\n"
        f"🎯 Релевантность: {score}\n"
    )

    if keywords:
        message += f"🏷️ Ключевые слова: {keywords}\n"

    message += (
        f"\n{title}\n\n"
        f"{description}\n\n"
        f"🔗 {order.url}"
    )

    return message


def _format_price(price: float) -> str:
    """Преобразует цену в удобный для чтения формат"""
    if price == int(price):
        return f"{int(price):,} ₽".replace(",", " ")

    return f"{price:,.2f} ₽".replace(",", " ")


def _format_text(text: str, limit: int | None = None) -> str:
    """Форматирует текст: HTML-сущности, emoji-плейсхолдеры, пробелы, обрезка"""
    text = unescape(text).strip()

    def replace_unicode(match: re.Match) -> str:
        try:
            return chr(int(match.group(1), 16))
        except (ValueError, OverflowError):
            return match.group(0)

    text = re.sub(r"\[:([0-9A-Fa-f]{4,6})]", replace_unicode, text)

    if limit is not None and len(text) > limit:
        text = text[:limit].rstrip() + "..."

    return text
