from dataclasses import dataclass
from datetime import datetime


@dataclass
class Order:
    id: int
    title: str
    description: str
    price: float
    username: str
    url: str
    date_expire: datetime
    score: int | None = None
    matched_keywords: list[str] | None = None
