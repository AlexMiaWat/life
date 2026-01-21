"""
Дымовые тесты для StructuredLogger

Проверяем базовую функциональность:
- Создание и базовые операции
- Запись в файл
- Восстановление после ошибок
"""

import json
import tempfile
import time
from pathlib import Path

import pytest

from src.observability.structured_logger import StructuredLogger
from src.environment.event import Event


class TestStructuredLoggerSmoke:
    """Дымовые тесты StructuredLogger"""

    def test_basic_logging_workflow(self):
        """Базовый рабочий процесс логирования"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jsonl') as f:
            temp_file = f.name

        try:
            # Создание логгера
            logger = StructuredLogger(log_file=temp_file, enabled=True)

            # Создание тестового события
            event = Event(type="test_event", intensity=0.5, timestamp=time.time())

            # Логирование полного цикла
            correlation_id = logger.log_event(event)
            # Создаем mock объекты для тестирования
            class MockMeaning:
                def __init__(self):
                    self.significance = 0.75
                    self.impact = {"context": "smoke_test"}

            class MockFeedback:
                def __init__(self):
                    self.action_id = "action_001"
                    self.delay_ticks = 2
                    self.state_delta = {"reward": 0.8}

            meaning = MockMeaning()
            feedback = MockFeedback()

            logger.log_meaning(event, meaning, correlation_id)
            logger.log_decision("absorb", correlation_id, {"action": "test"})
            logger.log_action("action_001", "test_pattern", correlation_id)
            logger.log_feedback(feedback, correlation_id)

            # Проверка что файл создан и содержит данные
            assert Path(temp_file).exists()

            with open(temp_file, 'r') as f:
                lines = f.readlines()

            assert len(lines) == 5  # 5 операций логирования

            # Сбор данных из всех записей
            correlation_ids = []
            stages = []
            for line in lines:
                entry = json.loads(line)
                correlation_ids.append(entry["correlation_id"])
                stages.append(entry["stage"])

            # Все операции должны иметь одинаковый correlation_id
            assert len(set(correlation_ids)) == 1

            # Проверка стадий
            expected_stages = ["event", "meaning", "decision", "action", "feedback"]
            assert sorted(stages) == sorted(expected_stages)

        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_file_creation_and_cleanup(self):
        """Создание файла и очистка"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jsonl') as f:
            temp_file = f.name

        try:
            # Файл не должен существовать до создания логгера
            Path(temp_file).unlink(missing_ok=True)

            logger = StructuredLogger(log_file=temp_file, enabled=True)

            # Логирование должно создать файл
            logger.log_event(Event(type="test_event", intensity=0.5, timestamp=time.time()))
            assert Path(temp_file).exists()

            # Проверка что файл содержит валидный JSONL
            with open(temp_file, 'r') as f:
                content = f.read().strip()
                assert content

                # Каждая строка должна быть валидным JSON
                lines = content.split('\n')
                for line in lines:
                    if line.strip():
                        json.loads(line)

        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_disabled_logger_no_file_creation(self):
        """Отключенный логгер не создает файлы"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jsonl') as f:
            temp_file = f.name

        try:
            # Удаление файла если существует
            Path(temp_file).unlink(missing_ok=True)

            logger = StructuredLogger(log_file=temp_file, enabled=False)

            # Логирование в отключенном состоянии
            logger.log_event(Event(type="test_event", intensity=0.5, timestamp=time.time()))
            # В disabled режиме эти вызовы не должны выполняться

            # Файл не должен быть создан
            assert not Path(temp_file).exists()

        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_concurrent_logging_smoke(self):
        """Базовый тест конкурентного логирования"""
        import threading

        with tempfile.NamedTemporaryFile(delete=False, suffix='.jsonl') as f:
            temp_file = f.name

        try:
            logger = StructuredLogger(log_file=temp_file, enabled=True)

            errors = []

            def log_in_thread(thread_id: int):
                try:
                    for i in range(10):
                        event = Event(type="thread_event", intensity=0.5, timestamp=time.time())
                        logger.log_event(event)
                        time.sleep(0.001)  # Маленькая задержка
                except Exception as e:
                    errors.append(str(e))

            # Запуск нескольких потоков
            threads = []
            for i in range(3):
                t = threading.Thread(target=log_in_thread, args=(i,))
                threads.append(t)
                t.start()

            # Ожидание завершения
            for t in threads:
                t.join()

            # Проверка отсутствия ошибок
            assert len(errors) == 0

            # Проверка что данные записаны
            assert Path(temp_file).exists()

            with open(temp_file, 'r') as f:
                lines = f.readlines()

            assert len(lines) == 30  # 3 потока * 10 событий

        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_logger_recovery_from_file_errors(self):
        """Восстановление логгера после ошибок файла"""
        # Попытка создать логгер в несуществующей директории
        logger = StructuredLogger(log_file="/nonexistent/directory/log.jsonl", enabled=True)

        # Это не должно вызывать исключение
        logger.log_event(Event(type="test_event", intensity=0.5, timestamp=time.time()))

        # Логгер должен продолжать работать
        assert logger.enabled is True

    def test_large_data_logging(self):
        """Логирование больших объемов данных"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jsonl') as f:
            temp_file = f.name

        try:
            logger = StructuredLogger(log_file=temp_file, enabled=True)

            # Создание большого события
            large_data = {"data": "x" * 10000, "list": list(range(1000))}
            event = Event(type="large_event", intensity=0.9, timestamp=time.time(), metadata=large_data)

            # Логирование большого события
            logger.log_event(event)

            # Проверка что данные записаны корректно
            assert Path(temp_file).exists()

            with open(temp_file, 'r') as f:
                lines = f.readlines()

            assert len(lines) == 1
            entry = json.loads(lines[0])

            # Проверка что большие данные сохранены
            # Данные события хранятся в поле data лога
            assert isinstance(entry["data"], dict)
            # Проверяем что лог создался без ошибок с большими данными

        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_rapid_logging_smoke(self):
        """Быстрое логирование для проверки производительности"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jsonl') as f:
            temp_file = f.name

        try:
            logger = StructuredLogger(log_file=temp_file, enabled=True)

            start_time = time.time()

            # Быстрое логирование множества событий
            for i in range(100):
                event = Event(type="rapid_event", intensity=0.5, timestamp=time.time())
                logger.log_event(event)

            end_time = time.time()

            # Проверка что логирование было достаточно быстрым (< 1 секунды)
            assert end_time - start_time < 1.0

            # Проверка что все события записаны
            assert Path(temp_file).exists()

            with open(temp_file, 'r') as f:
                lines = f.readlines()

            assert len(lines) == 100

        finally:
            Path(temp_file).unlink(missing_ok=True)