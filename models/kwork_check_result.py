from dataclasses import dataclass

from .order import Order


@dataclass
class KworkCheckResult:
    pages_checked: int
    total_orders: int
    passed_orders: int
    already_in_db_orders: int
    new_orders: list[Order]
