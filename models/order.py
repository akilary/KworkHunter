from dataclasses import dataclass


@dataclass
class Order:
    id: int
    title: str
    description: str
    price: float
    username: str
    url: str
    score: int | None = None
    matched_keywords: list[str] | None = None
