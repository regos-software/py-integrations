# core/logger.py
import logging
import sys
from config.settings import settings

def _ensure_root_handler(level: int):
    """
    Гарантируем, что root-логгер пишет в консоль и не отключён.
    Вызывается из setup_logger() при каждом импорте — idempotent.
    """
    root = logging.getLogger()
    # если на root нет ни одного хендлера — добавим консоль
    if not root.handlers:
        fmt = logging.Formatter(
            fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.NOTSET)  # пропускать всё, фильтрует уровень логгеров
        ch.setFormatter(fmt)
        root.addHandler(ch)
    # уровень и включение
    root.setLevel(level)
    root.disabled = False

def setup_logger(name: str = "app") -> logging.Logger:
    """
    Возвращает именованный логгер, который гарантированно пишет в консоль.
    - Включает root-логгер и его консольный хендлер (если не был настроен).
    - Снимает NullHandler'ы с именованного логгера.
    - Не добавляет своих хендлеров (чтобы не было дублей) — пишем через root.
    - Снимает флаг disabled, если кто-то его выставил (dictConfig с disable_existing_loggers=True).
    """
    level_name = (settings.log_level or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    # 1) гарантируем рабочий root
    _ensure_root_handler(level)

    # 2) берём наш логгер
    logger = logging.getLogger(name)

    # 3) если кто-то повесил NullHandler — уберём
    for h in list(logger.handlers):
        if isinstance(h, logging.NullHandler):
            logger.removeHandler(h)

    # 4) уровень/пропагация/включение
    logger.setLevel(level)
    logger.propagate = True      # отдаём в root
    logger.disabled = False      # на случай disable_existing_loggers=True

    return logger
