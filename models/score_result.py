from config import cfg


class ScoreResult:
    def __init__(self):
        self.positive: int = 0
        self.negative: int = 0
        self.matched_positive: list[tuple[str, int]] = []
        self.matched_negative: list[tuple[str, int]] = []

    def net(self) -> int:
        """Возвращает итоговый score: positive - negative"""
        return self.positive - self.negative

    def passed(self) -> bool:
        """Проверяет, проходит ли текст по порогам score и штрафов"""
        if self.positive < cfg.SCORE_THRESHOLD:
            return False
        if self.positive > 0 and (self.negative / self.positive) > cfg.PENALTY_RATIO:
            return False
        return True
