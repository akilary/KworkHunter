# KworkHunter

![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/github/license/akilary/KworkHunter)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey)

A lightweight monitoring service that scans the [Kwork](https://kwork.ru) freelance marketplace and delivers relevant
new orders directly to your Telegram.

Built for freelancers with a defined niche — filters out noise using a weighted keyword system and notifies you only
about orders worth your attention.

---

## How it works

Each polling cycle follows this pipeline:

1. Fetch new orders from the Kwork API
2. Skip orders already stored in SQLite
3. Lemmatize order text, score it against weighted keywords — discard anything below `SCORE_THRESHOLD`
4. Send a structured Telegram notification for each matched order
5. Store order IDs with expiry timestamps to prevent future duplicates

---

## Features

- **Automated polling** — configurable interval, runs in the background
- **Keyword filter** — weighted positive/negative scoring with lemmatization (inflected forms match the base keyword)
- **Duplicate prevention** — SQLite-backed deduplication with automatic expiry
- **Telegram notifications** — budget, relevance score, matched keywords, and a direct link
- **Bot controls** — manage all settings at runtime via Telegram commands
- **Optional Kwork auth** — log in to mark orders as viewed and improve scraping stability
- **Anti-ban measures** — randomized request delays and User-Agent rotation

---

## Tech stack

| Layer               | Technology                       |
|---------------------|----------------------------------|
| Language            | Python 3.10+                     |
| HTTP client         | `requests`                       |
| Scheduling          | `schedule`                       |
| Telegram bot        | `python-telegram-bot[job-queue]` |
| Database            | SQLite (raw SQL, no ORM)         |
| Environment         | `python-dotenv`                  |
| User-Agent rotation | `fake-useragent`                 |

SQLAlchemy is intentionally not used — the schema is simple, there are no relations, and raw SQL keeps the dependency
footprint minimal.

---

## Project structure

```
KworkHunter/
├── bot/
│   ├── handlers.py
│   └── jobs.py
├── data/
│   ├── keywords.json
│   └── processed_orders.db
├── database/
│   ├── engine.py          
│   └── requests.py
├── filters/
│   └── keyword_filter.py
├── kwork/
│   ├── client.py
│   └── parser.py
├── logs/
│   └── app.log
├── models/
│   ├── kwork_check_result.py
│   ├── order.py
│   └── score_result.py
├── services/
│   └── kwork_monitor.py
├── utils/
│   ├── keyword_loader.py
│   ├── logging_config.py
│   └── message_formatter.py
├── config.py
├── main.py
└── requirements.txt
```

---

## Installation

### Prerequisites

- Python 3.10+
- A Telegram bot token — obtain from [@BotFather](https://t.me/BotFather)
- Your Telegram user ID — obtain from [@userinfobot](https://t.me/userinfobot)

> The bot silently ignores all commands from anyone other than the owner.

### Steps

```bash
# 1. Clone
git clone https://github.com/akilary/KworkHunter.git
cd KworkHunter

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
```

Edit `.env`:

```env
# Kwork credentials — required only if USE_REGISTRATION=1
EMAIL=
PASSWORD=
USE_REGISTRATION=0

# Filter
SCORE_THRESHOLD=22
PENALTY_RATIO=0.7

# Telegram
BOT_TOKEN=
OWNER_ID=
INTERVAL=3                # polling interval in hours

# Database
DB_PATH=data/processed_orders.db
```

### Configure keywords

Edit `data/keywords.json`. Use the **base (dictionary) form** of each word — the filter lemmatizes both keywords and
order text before matching, so `parsing`, `parsed`, and `parsers` all match `parser`.

```json
{
  "positive": {
    "python": 5,
    "telegram": 4,
    "parser": 5,
    "automation": 4,
    "bot": 4
  },
  "negative": {
    "layout": 5,
    "design": 5,
    "figma": 4
  }
}
```

### Run

```bash
python main.py
```

---

## Bot commands

All commands are owner-only.

| Command                   | Description           |
|---------------------------|-----------------------|
| `/start`                  | Start monitoring      |
| `/stop`                   | Stop monitoring       |
| `/settings`               | Show current settings |
| `/settings <key> <value>` | Update a setting      |

### Available settings

| Key                | Type             | Default | Description                                    |
|--------------------|------------------|---------|------------------------------------------------|
| `interval`         | int              | `3`     | Polling interval in minutes                    |
| `use_registration` | `0` or `1`       | `0`     | Enable / disable Kwork auth                    |
| `score_threshold`  | int              | `22`    | Minimum score to pass the keyword filter       |
| `penalty_ratio`    | float ≥ 0        | `0.7`   | Multiplier applied to negative keyword weights |
| `time_zone`        | int (−23 to +23) | `5`     | UTC offset for timestamps in notifications     |

```
/settings interval 60
/settings score_threshold 15
/settings use_registration 1
/settings penalty_ratio 0.5
/settings time_zone 3
```

---

## Database schema

```sql
CREATE TABLE IF NOT EXISTS Orders
(
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id      INT  NOT NULL UNIQUE,
    title            TEXT NOT NULL,
    description      TEXT NOT NULL,
    price            REAL NOT NULL,
    username         TEXT NOT NULL,
    url              TEXT NOT NULL,
    date_expire      TEXT NOT NULL,
    score            INTEGER,
    matched_keywords TEXT
)
```

### Duplicate expiry

| Condition                          | Retention           |
|------------------------------------|---------------------|
| Order has `expire_time` from Kwork | `expire_time` + 2 h |
| No `expire_time` provided          | 3 days + 2 h        |

Records are deleted automatically after expiry. Cleanup runs every hour in the background.

---

## Notifications

All messages are sent in Russian. Example order notification:

```
📌 Заказ #1 из 3

💰 Бюджет: 3 500 ₽
🎯 Релевантность: 18
🏷️ Ключевые слова: python, telegram, бот

Телеграм-бот для приёма заявок с сайта

Нужен простой бот на Python (aiogram), который будет принимать
заявки с лендинга через webhook и пересылать их менеджеру.
Кнопки, базовая валидация полей, уведомление об успешной отправке.

🔗 https://kwork.ru/projects/0000000/
```

<details>
<summary>Check summary example</summary>

```
🔎 Проверка заказов

⏰ Время: 14:32

📊 Статистика
- Страниц проверено: 3
- Всего найдено: 47
- Прошли фильтр: 3
- Уже в базе: 44
- Новых заказов: 3
```

</details>

---

## Roadmap

**Planned:**

- [ ] Semantic similarity filter — score orders by meaning, not just keywords (`sentence-transformers`)

**Under consideration:**

- [ ] Async rewrite (`requests` → `aiohttp`, `schedule` → `APScheduler`)
- [ ] PostgreSQL support
- [ ] SQLAlchemy Core migration

---

## License

Distributed under the terms described in the [LICENSE](LICENSE) file.