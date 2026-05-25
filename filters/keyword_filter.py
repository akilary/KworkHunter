import re

import pymorphy3

from models import ScoreResult

morph = pymorphy3.MorphAnalyzer()

MANUAL_REPLACEMENTS = {
    "ё": "е",
    "pythoon": "python",
    "pyton": "python",
    "phyton": "python",
    "parsng": "парсинг",
    "automaton": "automation",
    "пасринг": "парсинг"
}



def _lemmatize_word(word: str) -> str:
    """Приводит слово к нормальной форме через pymorphy3"""
    return morph.parse(word)[0].normal_form


def _normalize_order(order_text: str) -> str:
    """Очищает и нормализует текст заказа для поиска ключевых слов"""
    text = order_text

    text = re.sub(r"\[:[a-f0-9\-]+]", " ", text)
    text = re.sub(r"&#?\w+;", " ", text)
    text = re.sub(r"\r\n|\r|\n", " ", text)
    text = re.sub(
        "[\U00010000-\U0010ffff"
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U00002700-\U000027BF"
        "]+",
        " ",
        text,
        flags=re.UNICODE
    )

    text = text.lower()

    for wrong, correct in MANUAL_REPLACEMENTS.items():
        text = text.replace(wrong, correct)

    text = re.sub(r"[^\w\s\-/]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    tokens = text.split()
    tokens = [_lemmatize_word(t) if re.search(r"[а-яёa-z]", t) else t for t in tokens]

    return " ".join(tokens)


def analyze_order_text(text: str, keywords: dict[str, dict[str, int]]) -> ScoreResult:
    """Подсчитывает positive/negative score по ключевым словам"""
    normalized_text = _normalize_order(text)
    scores_result = ScoreResult()

    for category in ("positive", "negative"):
        for keyword, weight in keywords[category].items():
            is_phrase = " " in keyword

            if is_phrase:
                hit = keyword in normalized_text
            else:
                hit = bool(re.search(rf"\b{re.escape(keyword)}\b", normalized_text))

            if hit:
                match category:
                    case "positive":
                        scores_result.positive += weight
                        scores_result.matched_positive.append((keyword, weight))
                    case "negative":
                        scores_result.negative += weight
                        scores_result.matched_negative.append((keyword, weight))

    return scores_result
