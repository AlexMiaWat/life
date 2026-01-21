"""
Централизованная конфигурация логирования для проекта Life.

Обеспечивает:
- INFO уровень по умолчанию в продакшене (debug логи отключены)
- DEBUG уровень в разработке
- CLI флаг --verbose для включения debug логов
- Консистентный формат логов
"""

import logging
import sys
from typing import Optional


def setup_logging(
    level: Optional[int] = None,
    verbose: bool = False,
    format_string: Optional[str] = None,
) -> None:
    """
    Настройка логирования для приложения.

    Args:
        level: Уровень логирования (если None, используется INFO или DEBUG в зависимости от verbose)
        verbose: Включить verbose режим (DEBUG уровень)
        format_string: Формат логов (если None, используется стандартный)
    """
    if level is None:
        level = logging.DEBUG if verbose else logging.INFO

    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Настройка корневого логгера
    logging.basicConfig(
        level=level,
        format=format_string,
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

    # Отключение verbose логов для внешних библиотек в продакшене
    if not verbose:
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Получить логгер с указанным именем.

    Args:
        name: Имя логгера (обычно __name__)

    Returns:
        Настроенный логгер
    """
    return logging.getLogger(name)
