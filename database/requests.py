import logging
import sqlite3
from datetime import datetime

from config import DB_PATH
from models import Order

log = logging.getLogger(__name__)


def add_orders(orders: list[Order]) -> None:
    """Сохраняет новые заказы в базу данных"""
    if not orders:
        log.debug("Нет заказов для сохранения в базу данных")
        return

    log.debug("Сохранение заказов в базу данных: count=%d", len(orders))

    try:
        with sqlite3.connect(DB_PATH) as con:
            con.executemany(
                """
                 INSERT INTO
                    Orders (
                        external_id,
                        title,
                        description,
                        price,
                        username,
                        url,
                        date_expire,
                        score,
                        matched_keywords
                        )
                    VALUES
                        (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        order.id,
                        order.title,
                        order.description,
                        order.price,
                        order.username,
                        order.url,
                        order.date_expire.isoformat(sep=" "),
                        order.score,
                        "; ".join(order.matched_keywords) if order.matched_keywords else None
                    )
                    for order in orders
                ]
            )

            log.info(
                "Заказы сохранены в базу данных: новых=%d | передано=%d",
                con.total_changes,
                len(orders),
            )
    except sqlite3.Error:
        log.exception("Ошибка при сохранении заказов в базу данных")
        raise


def get_processed_order_ids() -> set[int]:
    """Возвращает ID уже обработанных заказов из базы данных"""
    log.debug("Загрузка ID обработанных заказов из базы данных")

    try:
        with sqlite3.connect(DB_PATH) as con:
            cur = con.cursor()
            cur.execute("SELECT external_id FROM Orders")
            return {row[0] for row in cur.fetchall()}
    except sqlite3.Error:
        log.exception("Ошибка при загрузке ID обработанных заказов из базы данных")
        raise


def delete_expired_orders() -> None:
    """Удаляет просроченные заказы"""
    now = datetime.now().isoformat(sep=" ", timespec="seconds")

    try:
        with sqlite3.connect(DB_PATH) as con:
            cur = con.cursor()
            cur.execute("DELETE FROM Orders WHERE date_expire <= ?", (now,))

            deleted_count = cur.rowcount

            if deleted_count:
                log.info("Удалены просроченные заказы: count=%d", deleted_count)
            else:
                log.debug("Просроченных заказов для удаления нет")
    except sqlite3.Error:
        log.exception("Ошибка при удалении просроченных заказов")
        raise
