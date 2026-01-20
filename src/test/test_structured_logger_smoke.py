"""
Дымовые тесты для StructuredLogger (новая функциональность наблюдаемости)

Проверяем:
- Базовую работоспособность без падений
- Создание экземпляров классов
- Вызов основных методов с минимальными данными
- Обработку пустых/минимальных входных данных
- Граничные значения параметров
"""

import json
import os
import sys
import tempfile
import threading
import time
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.environment.event import Event
from src.observability.structured_logger import StructuredLogger


@pytest.mark.smoke
class TestStructuredLoggerSmoke:
    """Дымовые тесты для StructuredLogger"""

    # ============================================================================
    # StructuredLogger Smoke Tests
    # ============================================================================

    def test_structured_logger_instantiation(self):
        """Тест создания экземпляра StructuredLogger"""
        logger = StructuredLogger()
        assert logger is not None
        assert isinstance(logger, StructuredLogger)

    def test_structured_logger_disabled_mode(self):
        """Тест создания в отключенном режиме"""
        logger = StructuredLogger(enabled=False)
        assert logger.enabled is False

    def test_structured_logger_custom_log_file(self):
        """Тест создания с кастомным файлом логов"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = f.name

        try:
            logger = StructuredLogger(log_file=temp_file)
            assert logger.log_file == temp_file
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_log_event_basic(self):
        """Дымовой тест log_event с минимальными данными"""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            temp_file = f.name

        try:
            logger = StructuredLogger(log_file=temp_file, enabled=True)

            # Создаем минимальный event
            event = Event(type="noise", intensity=0.5, timestamp=1.0)

            # Логируем event
            correlation_id = logger.log_event(event)

            # Проверяем, что correlation_id сгенерирован
            assert isinstance(correlation_id, str)
            assert correlation_id.startswith("chain_")

            # Проверяем, что файл создан и содержит запись
            assert os.path.exists(temp_file)

            with open(temp_file, "r") as f:
                content = f.read()
                assert content.strip()  # Не пустой

                # Парсим JSONL
                lines = content.strip().split("\n")
                assert len(lines) == 1

                entry = json.loads(lines[0])
                assert entry["stage"] == "event"
                assert entry["correlation_id"] == correlation_id
                assert entry["event_type"] == "noise"
                assert entry["intensity"] == 0.5

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_log_event_with_custom_correlation_id(self):
        """Тест log_event с предустановленным correlation_id"""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            temp_file = f.name

        try:
            logger = StructuredLogger(log_file=temp_file, enabled=True)

            event = Event(type="shock", intensity=-0.8, timestamp=2.0)
            custom_corr_id = "test_chain_123"

            returned_corr_id = logger.log_event(event, correlation_id=custom_corr_id)

            assert returned_corr_id == custom_corr_id

            # Проверяем запись в файл
            with open(temp_file, "r") as f:
                lines = f.read().strip().split("\n")
                entry = json.loads(lines[0])
                assert entry["correlation_id"] == custom_corr_id

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_log_meaning_basic(self):
        """Дымовой тест log_meaning с минимальными данными"""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            temp_file = f.name

        try:
            logger = StructuredLogger(log_file=temp_file, enabled=True)

            # Создаем mock объекты
            event = Event(type="noise", intensity=0.3, timestamp=1.0)

            class MockMeaning:
                def __init__(self):
                    self.significance = 0.7
                    self.impact = {"energy": -5.0, "stability": 2.0}

            meaning = MockMeaning()
            correlation_id = "test_corr_123"

            # Логируем meaning
            logger.log_meaning(event, meaning, correlation_id)

            # Проверяем запись
            with open(temp_file, "r") as f:
                lines = f.read().strip().split("\n")
                entry = json.loads(lines[0])
                assert entry["stage"] == "meaning"
                assert entry["correlation_id"] == correlation_id
                assert entry["significance"] == 0.7
                assert entry["impact"] == {"energy": -5.0, "stability": 2.0}

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_log_decision_basic(self):
        """Дымовой тест log_decision с минимальными данными"""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            temp_file = f.name

        try:
            logger = StructuredLogger(log_file=temp_file, enabled=True)

            correlation_id = "test_corr_123"
            pattern = "absorb"

            logger.log_decision(pattern, correlation_id)

            # Проверяем запись
            with open(temp_file, "r") as f:
                lines = f.read().strip().split("\n")
                entry = json.loads(lines[0])
                assert entry["stage"] == "decision"
                assert entry["correlation_id"] == correlation_id
                assert entry["pattern"] == pattern

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_log_decision_with_additional_data(self):
        """Тест log_decision с дополнительными данными"""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            temp_file = f.name

        try:
            logger = StructuredLogger(log_file=temp_file, enabled=True)

            correlation_id = "test_corr_123"
            pattern = "dampen"
            additional_data = {"confidence": 0.85, "reason": "high_intensity"}

            logger.log_decision(pattern, correlation_id, additional_data)

            # Проверяем запись
            with open(temp_file, "r") as f:
                lines = f.read().strip().split("\n")
                entry = json.loads(lines[0])
                assert entry["data"]["confidence"] == 0.85
                assert entry["data"]["reason"] == "high_intensity"

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_log_action_basic(self):
        """Дымовой тест log_action с минимальными данными"""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            temp_file = f.name

        try:
            logger = StructuredLogger(log_file=temp_file, enabled=True)

            action_id = "action_456"
            pattern = "absorb"
            correlation_id = "test_corr_123"

            logger.log_action(action_id, pattern, correlation_id)

            # Проверяем запись
            with open(temp_file, "r") as f:
                lines = f.read().strip().split("\n")
                entry = json.loads(lines[0])
                assert entry["stage"] == "action"
                assert entry["action_id"] == action_id
                assert entry["pattern"] == pattern
                assert entry["correlation_id"] == correlation_id

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_log_action_with_state_before(self):
        """Тест log_action с состоянием до действия"""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            temp_file = f.name

        try:
            logger = StructuredLogger(log_file=temp_file, enabled=True)

            action_id = "action_789"
            pattern = "ignore"
            correlation_id = "test_corr_123"
            state_before = {"energy": 80.0, "stability": 0.9}

            logger.log_action(action_id, pattern, correlation_id, state_before)

            # Проверяем запись
            with open(temp_file, "r") as f:
                lines = f.read().strip().split("\n")
                entry = json.loads(lines[0])
                assert entry["data"]["state_before"] == state_before

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_log_feedback_basic(self):
        """Дымовой тест log_feedback с минимальными данными"""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            temp_file = f.name

        try:
            logger = StructuredLogger(log_file=temp_file, enabled=True)

            class MockFeedback:
                def __init__(self):
                    self.action_id = "action_456"
                    self.delay_ticks = 3
                    self.state_delta = {"energy": -10.0}
                    self.associated_events = ["event_1", "event_2"]

            feedback = MockFeedback()
            correlation_id = "test_corr_123"

            logger.log_feedback(feedback, correlation_id)

            # Проверяем запись
            with open(temp_file, "r") as f:
                lines = f.read().strip().split("\n")
                entry = json.loads(lines[0])
                assert entry["stage"] == "feedback"
                assert entry["correlation_id"] == correlation_id
                assert entry["action_id"] == "action_456"
                assert entry["delay_ticks"] == 3
                assert entry["data"]["state_delta"] == {"energy": -10.0}
                assert entry["data"]["associated_events"] == ["event_1", "event_2"]

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_log_tick_start_basic(self):
        """Дымовой тест log_tick_start"""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            temp_file = f.name

        try:
            logger = StructuredLogger(log_file=temp_file, enabled=True)

            tick_number = 42
            queue_size = 5

            logger.log_tick_start(tick_number, queue_size)

            # Проверяем запись
            with open(temp_file, "r") as f:
                lines = f.read().strip().split("\n")
                entry = json.loads(lines[0])
                assert entry["stage"] == "tick_start"
                assert entry["tick_number"] == tick_number
                assert entry["queue_size"] == queue_size

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_log_tick_end_basic(self):
        """Дымовой тест log_tick_end"""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            temp_file = f.name

        try:
            logger = StructuredLogger(log_file=temp_file, enabled=True)

            tick_number = 42
            duration_ms = 15.7
            events_processed = 3

            logger.log_tick_end(tick_number, duration_ms, events_processed)

            # Проверяем запись
            with open(temp_file, "r") as f:
                lines = f.read().strip().split("\n")
                entry = json.loads(lines[0])
                assert entry["stage"] == "tick_end"
                assert entry["tick_number"] == tick_number
                assert entry["duration_ms"] == duration_ms
                assert entry["events_processed"] == events_processed

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_log_error_basic(self):
        """Дымовой тест log_error"""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            temp_file = f.name

        try:
            logger = StructuredLogger(log_file=temp_file, enabled=True)

            stage = "decision"
            error = ValueError("Test error")
            correlation_id = "test_corr_123"

            logger.log_error(stage, error, correlation_id)

            # Проверяем запись
            with open(temp_file, "r") as f:
                lines = f.read().strip().split("\n")
                entry = json.loads(lines[0])
                assert entry["stage"] == "error_decision"
                assert entry["correlation_id"] == correlation_id
                assert entry["error_type"] == "ValueError"
                assert entry["error_message"] == "Test error"

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_disabled_logger_no_file_operations(self):
        """Тест отключенного логера - не должно быть операций с файлами"""
        logger = StructuredLogger(enabled=False)

        # Все методы должны выполняться без ошибок, но не создавать файлы
        event = Event(type="noise", intensity=0.5, timestamp=1.0)

        correlation_id = logger.log_event(event)
        assert correlation_id.startswith("chain_")

        logger.log_meaning(
            event,
            type("Mock", (), {"significance": 0.5, "impact": {}})(),
            correlation_id,
        )
        logger.log_decision("ignore", correlation_id)
        logger.log_action("action_1", "ignore", correlation_id)
        logger.log_feedback(
            type("Mock", (), {"action_id": "action_1", "delay_ticks": 1})(),
            correlation_id,
        )
        logger.log_tick_start(1, 0)
        logger.log_tick_end(1, 10.0, 1)
        logger.log_error("test", Exception("test"))

        # Файл не должен быть создан
        assert not os.path.exists("data/structured_log.jsonl")

    def test_correlation_id_generation(self):
        """Тест генерации correlation ID"""
        logger = StructuredLogger(enabled=False)

        # Первый вызов
        corr1 = logger.log_event(Event(type="noise", intensity=0.1, timestamp=1.0))
        assert corr1 == "chain_1"

        # Второй вызов
        corr2 = logger.log_event(Event(type="noise", intensity=0.1, timestamp=2.0))
        assert corr2 == "chain_2"

        # Correlation ID должны быть разными
        assert corr1 != corr2

    def test_thread_safety_smoke(self):
        """Дымовой тест потокобезопасности"""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            temp_file = f.name

        try:
            logger = StructuredLogger(log_file=temp_file, enabled=True)

            results = []

            def worker(thread_id):
                for i in range(10):
                    event = Event(
                        type=f"event_{thread_id}_{i}", intensity=0.1, timestamp=float(i)
                    )
                    corr_id = logger.log_event(event)
                    results.append((thread_id, corr_id))
                    time.sleep(0.001)  # Маленькая задержка для имитации конкуренции

            # Запускаем несколько потоков
            threads = []
            for thread_id in range(3):
                t = threading.Thread(target=worker, args=(thread_id,))
                threads.append(t)
                t.start()

            # Ждем завершения
            for t in threads:
                t.join()

            # Проверяем, что все correlation_id уникальны
            correlation_ids = [r[1] for r in results]
            assert len(set(correlation_ids)) == len(correlation_ids)

            # Проверяем, что файл содержит записи
            with open(temp_file, "r") as f:
                lines = f.read().strip().split("\n")
                assert len(lines) == 30  # 3 потока * 10 записей

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_jsonl_format_validity(self):
        """Тест валидности JSONL формата"""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            temp_file = f.name

        try:
            logger = StructuredLogger(log_file=temp_file, enabled=True)

            # Создаем различные записи
            logger.log_event(Event(type="noise", intensity=0.5, timestamp=1.0))
            logger.log_tick_start(1, 5)
            logger.log_error("test", RuntimeError("Test error"))

            # Читаем и парсим каждую строку
            with open(temp_file, "r") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    assert line, f"Пустая строка {line_num}"

                    # Должен быть валидный JSON
                    entry = json.loads(line)
                    assert isinstance(entry, dict)

                    # Обязательные поля
                    assert "timestamp" in entry
                    assert "stage" in entry
                    assert "correlation_id" in entry
                    assert "data" in entry

                    # timestamp должен быть числом
                    assert isinstance(entry["timestamp"], (int, float))

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
