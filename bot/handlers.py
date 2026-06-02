import logging
from datetime import timedelta, timezone

from telegram import Update, Message, Chat, User
from telegram.ext import ContextTypes, JobQueue, CallbackContext

from bot.jobs import check_orders_job, cleanup_expired_job
from config import cfg

log = logging.getLogger(__name__)

SETTING_ALIASES = {
    "interval": "interval",
    "i": "interval",

    "use_registration": "use_registration",
    "reg": "use_registration",
    "registration": "use_registration",

    "score_threshold": "score_threshold",
    "score": "score_threshold",
    "threshold": "score_threshold",

    "penalty_ratio": "penalty_ratio",
    "penalty": "penalty_ratio",
    "ratio": "penalty_ratio",

    "time_zone": "time_zone",
    "timezone": "time_zone",
    "tz": "time_zone",
    "zone": "time_zone",
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запуск мониторинга заказов"""
    owner_context = await _validate_owner_request(update, context, "start")
    if owner_context is None:
        return

    chat, message, _, job_queue = owner_context

    chat_id = chat.id

    check_orders_job_name = f"check_orders_job_{chat_id}"
    cleanup_job_name = f"cleanup_expired_job_{chat_id}"

    _remove_old_jobs(job_queue, check_orders_job_name, "мониторинга", chat_id)
    _remove_old_jobs(job_queue, cleanup_job_name, "очистки", chat_id)

    job_queue.run_repeating(
        check_orders_job,
        interval=timedelta(hours=cfg.INTERVAL),
        first=10,
        chat_id=chat_id,
        name=check_orders_job_name,
    )

    log.info("Задача мониторинга Kwork запущена: chat_id=%s | interval_hours=%s", chat_id, cfg.INTERVAL)

    job_queue.run_repeating(
        cleanup_expired_job,
        interval=timedelta(hours=1),
        first=5,
        chat_id=chat_id,
        name=cleanup_job_name,
    )

    log.info("Задача очистки просроченных заказов запущена: chat_id=%s | interval_hours=1", chat_id)

    await message.reply_text(f"Мониторинг Kwork запущен. Проверяю заказы каждые {cfg.INTERVAL} часа")


async def stop(update: Update, context: CallbackContext) -> None:
    """Остановка мониторинга заказов"""
    owner_context = await _validate_owner_request(update, context, "stop")
    if owner_context is None:
        return

    _, message, _, job_queue = owner_context

    jobs = job_queue.jobs()

    if not jobs:
        log.debug("Попытка остановить мониторинг при отсутствии активных задач")
        await message.reply_text("Мониторинг уже остановлен или не был запущен")
        return

    for job in jobs:
        job.schedule_removal()

    log.info("Остановлен мониторинг: удалено задач=%d", len(jobs))
    await message.reply_text("Мониторинг остановлен")


async def settings(update: Update, context: CallbackContext) -> None:
    """Изменение настроек бота"""
    owner_context = await _validate_owner_request(update, context, "settings")
    if owner_context is None:
        return

    chat, message, user, job_queue = owner_context

    args = context.args

    if not args:
        await _show_settings(job_queue, chat, message)
        return

    if len(args) != 2:
        log.warning("Некорректный формат команды /settings: user_id=%s | args=%s", user.id, args)
        await message.reply_text(
            "Формат: /settings настройка значение\n\n"
            "Доступные настройки:\n"
            "interval (i)\n"
            "use_registration (reg)\n"
            "score_threshold (score)\n"
            "penalty_ratio (penalty)\n"
            "time_zone (tz)"
        )
        return

    raw_command = args[0].lower().strip()
    value = args[1].strip()

    command = SETTING_ALIASES.get(raw_command)

    if command is None:
        log.warning("Попытка изменить неизвестную настройку: user_id=%s | setting=%s", user.id, raw_command)
        await message.reply_text(f"Неизвестная настройка: {raw_command}")
        return

    try:
        match command:
            case "interval":
                new_value = int(value)
                if new_value <= 0:
                    raise ValueError("interval должен быть больше 0")

                old_value = cfg.INTERVAL
                cfg.INTERVAL = new_value
            case "use_registration":
                new_value = int(value)
                if new_value not in (0, 1):
                    raise ValueError("use_registration должен быть 0 или 1")

                old_value = cfg.USE_REGISTRATION
                cfg.USE_REGISTRATION = new_value
            case "score_threshold":
                new_value = int(value)

                old_value = cfg.SCORE_THRESHOLD
                cfg.SCORE_THRESHOLD = new_value
            case "penalty_ratio":
                new_value = float(value)
                if new_value < 0:
                    raise ValueError("penalty_ratio не может быть меньше 0")

                old_value = cfg.PENALTY_RATIO
                cfg.PENALTY_RATIO = new_value
            case "time_zone":
                hours = int(value)
                if not -23 <= hours <= 23:
                    raise ValueError("Часовой пояс должен быть от -23 до +23")

                old_value = cfg.TIMEZONE.__str__()
                cfg.TIMEZONE = timezone(timedelta(hours=hours))
                new_value = cfg.TIMEZONE.__str__()
            case _:
                log.warning("Попытка изменить неизвестную настройку: user_id=%s | setting=%s",
                            user.id,
                            command
                            )
                await message.reply_text(f"Неизвестная настройка: {command}")
                return
    except ValueError as e:
        log.warning(
            "Некорректное значение настройки: user_id=%s | setting=%s | value=%s | error=%s",
            user.id,
            command,
            value,
            e
        )
        await message.reply_text(f"Некорректное значение: {value}")
        return

    log.info("Настройка изменена: user_id=%s | %s: %s -> %s", user.id, command, old_value, new_value)
    await message.reply_text(
        f"Настройка изменена:\n"
        f"{command}: {old_value} -> {new_value}"
    )

    if command == "interval":
        await start(update, context)


async def _validate_owner_request(
        update: Update,
        context: CallbackContext,
        func_name: str
) -> tuple[Chat, Message, User, JobQueue] | None:
    """Проверяет, что команду вызвал владелец бота"""
    chat, message, user = update.effective_chat, update.effective_message, update.effective_user

    if chat is None or message is None or user is None:
        log.warning("Команда /%s получена без chat/message/user", func_name)
        return None

    log.info(
        "Получена команда /%s: user_id=%s | username=%s | chat_id=%s",
        func_name,
        user.id,
        user.username,
        chat.id,
    )

    if user.id != cfg.OWNER_ID:
        log.warning("Отказ в доступе к /%s: user_id=%s | username=%s", func_name, user.id, user.username)
        await message.reply_text("Нет доступа")
        return None

    job_queue = context.job_queue

    if job_queue is None:
        log.error("JobQueue не подключён")
        await message.reply_text("JobQueue не подключён")
        return None

    return chat, message, user, job_queue


def _remove_old_jobs(job_queue: JobQueue, job_name: str, job_label: str, chat_id: int) -> None:
    """Удаляет все старые задачи с указанным именем"""
    old_jobs = job_queue.get_jobs_by_name(job_name)

    if not old_jobs:
        log.debug("Старые задачи %s не найдены: chat_id=%s", job_label, chat_id)
        return

    for job in old_jobs:
        job.schedule_removal()

    if old_jobs:
        log.info(
            "Удалены старые задачи %s: chat_id=%s | count=%d",
            job_label,
            chat_id,
            len(old_jobs),
        )


async def _show_settings(job_queue: JobQueue, chat: Chat, message: Message) -> None:
    """Показывает состояние мониторинга и текущие настройки"""
    jobs = job_queue.jobs()
    if not jobs:
        log.debug("Статус мониторинга: активные задачи отсутствуют: chat_id=%s", chat.id)
        await message.reply_text("Мониторинг Kwork остановлен или не запускался")
        return

    active_jobs = [job for job in jobs if job.name and job.name.endswith(f"_{chat.id}")]

    if not active_jobs:
        log.debug("Для текущего чата активные задачи не найдены: chat_id=%s", chat.id)
        await message.reply_text("Для текущего чата активные задачи не найдены")
        return

    jobs_info = "\n".join(
        f"- {job.name}: "
        f"{job.next_t.astimezone(cfg.TIMEZONE).strftime('%H:%M:%S')}"
        for job in active_jobs
        if job.next_t is not None
    )

    lines = (
        "Мониторинг Kwork активен",
        f"Активных задач: {len(active_jobs)}",
        "",
        "Задачи:",
        jobs_info,
        "",
        "Настройки:",
        f"Интервал проверки: {cfg.INTERVAL} ч",
        f"Порог релевантности: {cfg.SCORE_THRESHOLD}",
        f"Штраф: {cfg.PENALTY_RATIO}",
        f"Регистрация: {'включена' if cfg.USE_REGISTRATION else 'выключена'}",
    )

    log.debug("Статус мониторинга сформирован: chat_id=%s | active_jobs=%d", chat.id, len(active_jobs))

    await message.reply_text("\n".join(lines))
