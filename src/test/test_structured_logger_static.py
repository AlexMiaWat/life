"""
Статические тесты для StructuredLogger

Проверяем:
- Инициализация StructuredLogger
- Создание correlation ID
- Запись лог-записей
- Thread-safety
- Включение/выключение логирования
"""

import json
import tempfile
import threading
import time
from pathlib import Path

import pytest

from src.observability.structured_logger import StructuredLogger
from src.environment.event import Event


class TestStructuredLoggerStatic:
    """Статические тесты StructuredLogger"""

    def test_initialization(self):
        """Тест инициализации StructuredLogger"""
        # Тест с параметрами по умолчанию
        logger = StructuredLogger()
        assert logger.log_file == "data/structured_log.jsonl"
        assert logger.enabled is True
        assert hasattr(logger, '_lock')
        assert logger._correlation_counter == 0

        # Тест с кастомными параметрами
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jsonl') as f:
            custom_file = f.name

        logger = StructuredLogger(log_file=custom_file, enabled=False)
        assert logger.log_file == custom_file
        assert logger.enabled is False

        # Очистка
        Path(custom_file).unlink(missing_ok=True)

    def test_correlation_id_generation(self):
        """Тест генерации correlation ID"""
        logger = StructuredLogger(enabled=False)

        # Первый ID
        id1 = logger._get_next_correlation_id()
        assert id1 == "chain_1"
        assert logger._correlation_counter == 1

        # Второй ID
        id2 = logger._get_next_correlation_id()
        assert id2 == "chain_2"
        assert logger._correlation_counter == 2

        # ID уникальны
        assert id1 != id2

    def test_log_entry_structure(self):
        """Тест структуры лог-записей"""
        # Проверяем структуру через реальное логирование с временным файлом
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jsonl') as f:
            temp_file = f.name

        try:
            logger = StructuredLogger(log_file=temp_file, enabled=True)

            # Создание события для логирования
            from src.environment.event import Event
            event = Event(type="test_event", intensity=0.8, timestamp=time.time())

            # Логирование события
            correlation_id = logger.log_event(event)

            # Чтение записанной записи
            with open(temp_file, 'r') as file:
                lines = file.readlines()
                assert len(lines) == 1

                import json
                entry = json.loads(lines[0])

            required_fields = ["timestamp", "stage", "correlation_id", "event_id", "data"]
            for field in required_fields:
                assert field in entry

            assert entry["stage"] == "event"
            assert entry["correlation_id"] == correlation_id
            assert isinstance(entry["timestamp"], (int, float))

        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_disabled_logging(self):
        """Тест отключенного логирования"""
        # Создаем уникальный путь для файла
        import uuid
        temp_file = f"/tmp/test_disabled_{uuid.uuid4()}.jsonl"

        logger = StructuredLogger(log_file=temp_file, enabled=False)

        # Попытка записи при отключенном логировании
        event = Event(type="test", intensity=0.5, timestamp=time.time())
        logger.log_event(event)

        # Файл не должен быть создан
        assert not Path(temp_file).exists()

        # Попытка записи при включенном логировании
        logger.enabled = True
        logger.log_event(event)

        # Теперь файл должен быть создан
        assert Path(temp_file).exists()

        # Очистка
        Path(temp_file).unlink(missing_ok=True)

    def test_thread_safety_correlation_ids(self):
        """Тест потокобезопасности генерации correlation ID"""
        logger = StructuredLogger(enabled=False)

        results = []
        errors = []

        def generate_ids(thread_id: int, count: int):
            """Генерирует correlation ID в потоке"""
            try:
                ids = []
                for _ in range(count):
                    ids.append(logger._get_next_correlation_id())
                results.append((thread_id, ids))
            except Exception as e:
                errors.append((thread_id, str(e)))

        # Запуск нескольких потоков
        threads = []
        for i in range(5):
            t = threading.Thread(target=generate_ids, args=(i, 10))
            threads.append(t)
            t.start()

        # Ожидание завершения
        for t in threads:
            t.join()

        # Проверка отсутствия ошибок
        assert len(errors) == 0, f"Thread safety errors: {errors}"

        # Проверка уникальности всех ID
        all_ids = []
        for thread_id, ids in results:
            all_ids.extend(ids)

        assert len(all_ids) == 50  # 5 потоков * 10 ID
        assert len(set(all_ids)) == 50  # Все уникальны

        # Проверка что ID идут последовательно
        sorted_ids = sorted(all_ids, key=lambda x: int(x.split('_')[1]))
        assert sorted_ids == all_ids

    def test_log_event_method(self):
        """Тест метода log_event"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jsonl') as f:
            temp_file = f.name

        logger = StructuredLogger(log_file=temp_file, enabled=True)

        event = Event(type="test_event", intensity=0.8, timestamp=time.time(), metadata={"test": "data"})
        correlation_id = logger.log_event(event)

        # Проверка что файл создан и содержит запись
        assert Path(temp_file).exists()

        with open(temp_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 1

            entry = json.loads(lines[0])
            assert entry["stage"] == "event"
            assert entry["correlation_id"] == correlation_id
            assert entry["event_type"] == "test_event"
            assert entry["intensity"] == 0.8

        # Очистка
        Path(temp_file).unlink(missing_ok=True)

    def test_log_meaning_method(self):
        """Тест метода log_meaning"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jsonl') as f:
            temp_file = f.name

        logger = StructuredLogger(log_file=temp_file, enabled=True)

        # Создаем mock объекты для event и meaning
        event = Event(type="test_event", intensity=0.5, timestamp=time.time())
        event.id = "event_123"

        class MockMeaning:
            def __init__(self):
                self.significance = 0.75
                self.impact = {"context": "test"}

        meaning = MockMeaning()

        logger.log_meaning(event, meaning, "chain_1")

        # Проверка записи
        assert Path(temp_file).exists()

        with open(temp_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 1

            entry = json.loads(lines[0])
            assert entry["stage"] == "meaning"
            assert entry["correlation_id"] == "chain_1"
            assert entry["event_id"] == "event_123"
            assert entry["significance"] == 0.75
            assert entry["data"]["meaning_type"] == "MockMeaning"

        # Очистка
        Path(temp_file).unlink(missing_ok=True)

    def test_log_decision_method(self):
        """Тест метода log_decision"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jsonl') as f:
            temp_file = f.name

        logger = StructuredLogger(log_file=temp_file, enabled=True)

        logger.log_decision("absorb", "chain_1", {"action_type": "test_action", "params": "test"})

        # Проверка записи
        assert Path(temp_file).exists()

        with open(temp_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 1

            entry = json.loads(lines[0])
            assert entry["stage"] == "decision"
            assert entry["correlation_id"] == "chain_1"
            assert entry["pattern"] == "absorb"
            assert entry["data"]["action_type"] == "test_action"

        # Очистка
        Path(temp_file).unlink(missing_ok=True)

    def test_log_action_method(self):
        """Тест метода log_action"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jsonl') as f:
            temp_file = f.name

        logger = StructuredLogger(log_file=temp_file, enabled=True)

        logger.log_action("action_001", "test_pattern", "chain_1", {"energy": 100})

        # Проверка записи
        assert Path(temp_file).exists()

        with open(temp_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 1

            entry = json.loads(lines[0])
            assert entry["stage"] == "action"
            assert entry["correlation_id"] == "chain_1"
            assert entry["action_id"] == "action_001"
            assert entry["pattern"] == "test_pattern"
            assert entry["data"]["state_before"]["energy"] == 100

        # Очистка
        Path(temp_file).unlink(missing_ok=True)

    def test_log_feedback_method(self):
        """Тест метода log_feedback"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jsonl') as f:
            temp_file = f.name

        logger = StructuredLogger(log_file=temp_file, enabled=True)

        # Создаем mock feedback объект
        class MockFeedback:
            def __init__(self):
                self.action_id = "action_001"
                self.delay_ticks = 5
                self.state_delta = {"energy": -5.0}
                self.associated_events = ["event_123"]

        feedback = MockFeedback()

        logger.log_feedback(feedback, "chain_1")

        # Проверка записи
        assert Path(temp_file).exists()

        with open(temp_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 1

            entry = json.loads(lines[0])
            assert entry["stage"] == "feedback"
            assert entry["correlation_id"] == "chain_1"
            assert entry["action_id"] == "action_001"
            assert entry["delay_ticks"] == 5
            assert entry["data"]["state_delta"]["energy"] == -5.0

        # Очистка
        Path(temp_file).unlink(missing_ok=True)

    def test_file_writing_error_handling(self):
        """Тест обработки ошибок при записи в файл"""
        # Попытка записи в несуществующий каталог
        logger = StructuredLogger(log_file="/nonexistent/directory/log.jsonl", enabled=True)

        # Это не должно вызывать исключение
        logger.log_event("test", {})

        # Logger должен продолжать работать
        assert logger.enabled is True