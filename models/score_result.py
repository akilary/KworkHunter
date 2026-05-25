from config import SCORE_THRESHOLD, PENALTY_RATIO


class ScoreResult:
    def __init__(self):
        self.positive = 0
        self.negative = 0
        self.matched_positive = []
        self.matched_negative = []

    def net(self) -> int:
        """Возвращает итоговый score: positive - negative"""
        return self.positive - self.negative

    def passed(self) -> bool:
        """Проверяет, проходит ли текст по порогам score и штрафов"""
        if self.positive < SCORE_THRESHOLD:
            return False
        if self.positive > 0 and (self.negative / self.positive) > PENALTY_RATIO:
            return False
        return True
