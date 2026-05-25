import json


def load_keywords() -> dict[str, dict[str, int]]:
    """Загружает ключевые слова из файла JSON"""
    try:
        with open("data/keywords.json", "r", encoding="utf-8") as keywords_file:
            return json.load(keywords_file)
    except FileNotFoundError as error:
        raise FileNotFoundError("Keywords file was not found: data/keywords.json") from error
    except json.JSONDecodeError as error:
        raise ValueError("Invalid JSON format in keywords.json") from error
