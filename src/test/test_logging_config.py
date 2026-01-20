"""
Тесты для конфигурации логирования.

Проверяет:
- INFO уровень по умолчанию (debug логи отключены в продакшене)
- DEBUG уровень в verbose режиме
- Правильная настройка внешних библиотек
"""

import logging
import sys
from io import StringIO
from unittest.mock import patch

import pytest

from src.logging_config import get_logger, setup_logging


@pytest.mark.unit
class TestLoggingConfig:
    """Тесты для конфигурации логирования"""

    def test_setup_logging_default_level(self):
        """Тест настройки логирования по умолчанию (INFO уровень)"""
        # Сбрасываем настройки логирования
        logging.getLogger().handlers.clear()

        # Настраиваем логирование по умолчанию
        setup_logging()

        # Проверяем уровень корневого логгера
        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO

    def test_setup_logging_verbose_level(self):
        """Тест настройки логирования в verbose режиме (DEBUG уровень)"""
        # Сбрасываем настройки логирования
        logging.getLogger().handlers.clear()

        # Настраиваем логирование в verbose режиме
        setup_logging(verbose=True)

        # Проверяем уровень корневого логгера
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

    def test_setup_logging_custom_level(self):
        """Тест настройки логирования с кастомным уровнем"""
        # Сбрасываем настройки логирования
        logging.getLogger().handlers.clear()

        # Настраиваем логирование с WARNING уровнем
        setup_logging(level=logging.WARNING)

        # Проверяем уровень корневого логгера
        root_logger = logging.getLogger()
        assert root_logger.level == logging.WARNING

    @patch("sys.stdout", new_callable=StringIO)
    def test_debug_logs_hidden_in_production(self, mock_stdout):
        """Тест, что debug логи не выводятся в продакшене"""
        # Сбрасываем настройки логирования
        logging.getLogger().handlers.clear()

        # Настраиваем логирование в продакшен режиме (INFO)
        setup_logging(verbose=False)

        logger = get_logger("test_logger")

        # Записываем debug и info сообщения
        logger.debug("This is a debug message")
        logger.info("This is an info message")
        logger.warning("This is a warning message")

        # Получаем вывод
        output = mock_stdout.getvalue()

        # Debug сообщение не должно быть в выводе
        assert "This is a debug message" not in output

        # Info и warning сообщения должны быть
        assert "This is an info message" in output
        assert "This is a warning message" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_debug_logs_shown_in_verbose(self, mock_stdout):
        """Тест, что debug логи выводятся в verbose режиме"""
        # Сбрасываем настройки логирования
        logging.getLogger().handlers.clear()

        # Настраиваем логирование в verbose режиме (DEBUG)
        setup_logging(verbose=True)

        logger = get_logger("test_logger")

        # Записываем debug и info сообщения
        logger.debug("This is a debug message")
        logger.info("This is an info message")

        # Получаем вывод
        output = mock_stdout.getvalue()

        # Debug сообщение должно быть в выводе
        assert "This is a debug message" in output
        assert "This is an info message" in output

    def test_external_libraries_logging_suppressed_in_production(self):
        """Тест, что логи внешних библиотек подавляются в продакшене"""
        # Сбрасываем настройки логирования
        logging.getLogger().handlers.clear()

        # Настраиваем логирование в продакшен режиме
        setup_logging(verbose=False)

        # Проверяем уровни для внешних библиотек
        requests_logger = logging.getLogger("requests")
        urllib3_logger = logging.getLogger("urllib3")

        assert requests_logger.level == logging.WARNING
        assert urllib3_logger.level == logging.WARNING

    def test_external_libraries_logging_not_suppressed_in_verbose(self):
        """Тест, что логи внешних библиотек не подавляются в verbose режиме"""
        # Сбрасываем настройки логирования
        logging.getLogger().handlers.clear()

        # Настраиваем логирование в verbose режиме
        setup_logging(verbose=True)

        # Проверяем уровни для внешних библиотек (должны наследовать DEBUG)
        requests_logger = logging.getLogger("requests")
        urllib3_logger = logging.getLogger("urllib3")

        # В verbose режиме внешние библиотеки должны наследовать уровень от корневого логгера
        assert requests_logger.level == logging.DEBUG
        assert urllib3_logger.level == logging.DEBUG

    def test_get_logger_returns_proper_logger(self):
        """Тест, что get_logger возвращает правильно настроенный логгер"""
        logger = get_logger("test_module")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    @patch("sys.stdout", new_callable=StringIO)
    def test_logging_format(self, mock_stdout):
        """Тест формата логирования"""
        # Сбрасываем настройки логирования
        logging.getLogger().handlers.clear()

        # Настраиваем логирование
        setup_logging(verbose=True)

        logger = get_logger("test_logger")
        logger.info("Test message")

        output = mock_stdout.getvalue()

        # Проверяем, что формат содержит ожидаемые компоненты
        assert "test_logger" in output
        assert "INFO" in output
        assert "Test message" in output
        assert "-" in output  # Разделители в формате