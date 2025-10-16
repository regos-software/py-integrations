import logging
import sys
from config.settings import settings


def setup_logger(name: str = "app") -> logging.Logger:
    """Настраивает логгер с заданным именем и уровнем логирования из настроек.

    Args:
        name (str): Имя логгера. По умолчанию 'app'.

    Returns:
        logging.Logger: Настроенный объект логгера.

    Raises:
        ValueError: Если указан недопустимый уровень логирования.
    """
    logger = logging.getLogger(name)

    log_level = settings.log_level.upper()
    if not hasattr(logging, log_level):
        raise ValueError(f"Недопустимый уровень логирования: {log_level}")

    logger.setLevel(log_level)

    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
