# core/logger.py
import logging
import sys
from config.settings import settings

def _ensure_root_handler(level: int):
    root = logging.getLogger()
    # Если root без хендлеров — добавим консоль
    if not root.handlers:
        fmt = logging.Formatter(
            fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.NOTSET)  # пропускать всё, фильтрует уровень логгеров
        ch.setFormatter(fmt)
        root.addHandler(ch)
    # Приведём уровень root к нужному (чтобы DEBUG показывался)
    root.setLevel(level)
    root.disabled = False

def setup_logger(name: str = "app") -> logging.Logger:
    logger = logging.getLogger(name)

    # уровень из настроек
    level_name = (settings.log_level or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    # 1) root точно настроен и пишет в консоль
    _ensure_root_handler(level)

    # 2) уберём NullHandler'ы, если их кто-то повесил
    for h in list(logger.handlers):
        if isinstance(h, logging.NullHandler):
            logger.removeHandler(h)

    # 3) уровень и проброс к root
    logger.setLevel(level)
    logger.disabled = False
    logger.propagate = True  # пишем через root; не добавляем свои хендлеры

    return logger
