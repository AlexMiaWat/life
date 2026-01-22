"""
Интеграционные тесты для сериализации компонентов системы.

Тестирует end-to-end сериализацию и десериализацию состояния,
включая thread-safety, отказоустойчивость и производительность.
"""

import json
import threading
import time
import tempfile
from pathlib import Path
from typing import Dict, Any
from unittest.mock import MagicMock

import pytest

from src.environment.event_queue import EventQueue
from src.environment.event import Event
from src.state.self_state import SelfState
from src.dev.process_restarter import StateSerializer
from src.contracts.serialization_contract import SerializationError


class TestEventQueueSerialization:
    """Интеграционные тесты сериализации EventQueue."""

    def test_eventqueue_to_dict_basic(self):
        """Тест базовой сериализации пустой очереди."""
        queue = EventQueue()
        result = queue.to_dict()

        # Проверяем стандартизированную структуру согласно архитектурным контрактам
        assert isinstance(result, dict)
        assert "metadata" in result
        assert "data" in result

        # Проверяем метаданные
        metadata = result["metadata"]
        assert metadata["component_type"] == "EventQueue"
        assert metadata["version"] == "2.0"
        assert "timestamp" in metadata
        assert metadata["event_count"] == 0

        # Проверяем данные
        data = result["data"]
        assert isinstance(data["events"], list)
        assert len(data["events"]) == 0

    def test_eventqueue_to_dict_with_events(self):
        """Тест сериализации очереди с событиями."""
        queue = EventQueue()
        event1 = Event(type="test_event_1", intensity=0.5, timestamp=1000.0, metadata={"key": "value1"})
        event2 = Event(type="test_event_2", intensity=0.8, timestamp=1001.0, metadata={"key": "value2"})

        queue.push(event1)
        queue.push(event2)

        result = queue.to_dict()

        # Проверяем стандартизированную структуру
        assert isinstance(result, dict)
        assert "metadata" in result
        assert "data" in result

        # Проверяем метаданные
        metadata = result["metadata"]
        assert metadata["event_count"] == 2

        # Проверяем данные
        data = result["data"]
        events = data["events"]
        assert isinstance(events, list)
        assert len(events) == 2

        # Проверяем структуру сериализованных событий
        event_dict = events[0]
        assert "type" in event_dict
        assert "intensity" in event_dict
        assert "timestamp" in event_dict
        assert "metadata" in event_dict
        assert event_dict["type"] == "test_event_1"
        assert event_dict["intensity"] == 0.5
        assert event_dict["timestamp"] == 1000.0
        assert event_dict["metadata"] == {"key": "value1"}

    def test_eventqueue_serialization_thread_safety(self):
        """Тест thread-safety сериализации во время модификации очереди."""
        queue = EventQueue()
        results = []
        errors = []

        def producer():
            """Производитель событий."""
            try:
                for i in range(100):
                    event = Event(
                        type=f"event_{i}",
                        intensity=float(i) / 100.0,
                        timestamp=time.time(),
                        metadata={"index": i}
                    )
                    queue.push(event)
                    time.sleep(0.001)  # Маленькая задержка для переключения контекста
            except Exception as e:
                errors.append(f"Producer error: {e}")

        def consumer():
            """Потребитель, который сериализует очередь."""
            try:
                for _ in range(10):
                    result = queue.to_dict()
                    results.append(result)
                    time.sleep(0.002)
            except Exception as e:
                errors.append(f"Consumer error: {e}")

        # Запускаем параллельно
        producer_thread = threading.Thread(target=producer)
        consumer_thread = threading.Thread(target=consumer)

        producer_thread.start()
        consumer_thread.start()

        producer_thread.join(timeout=5.0)
        consumer_thread.join(timeout=5.0)

        # Проверяем, что нет ошибок
        assert len(errors) == 0, f"Thread safety errors: {errors}"

        # Проверяем, что сериализация работала
        assert len(results) > 0
        for result in results:
            assert isinstance(result, dict)
            assert "metadata" in result
            assert "data" in result

    def test_eventqueue_serialization_consistency(self):
        """Тест консистентности сериализации."""
        queue = EventQueue()
        events = []

        # Добавляем события
        for i in range(5):
            event = Event(
                type=f"consistent_event_{i}",
                intensity=0.5,
                timestamp=1000.0 + i,
                metadata={"consistent": True, "index": i}
            )
            events.append(event)
            queue.push(event)

        # Многократная сериализация должна давать консистентные данные
        result1 = queue.to_dict()
        result2 = queue.to_dict()

        # Метаданные могут отличаться (timestamp), но данные должны быть одинаковыми
        assert result1["data"] == result2["data"]
        assert result1["metadata"]["event_count"] == 5
        assert result2["metadata"]["event_count"] == 5

        events1 = result1["data"]["events"]
        events2 = result2["data"]["events"]
        assert len(events1) == 5
        assert len(events2) == 5

        # События должны быть в правильном порядке
        for i, event_dict in enumerate(events1):
            assert event_dict["type"] == f"consistent_event_{i}"
            assert event_dict["timestamp"] == 1000.0 + i


class TestSelfStateSerialization:
    """Интеграционные тесты сериализации SelfState."""

    def test_selfstate_to_dict_basic(self):
        """Тест базовой сериализации SelfState."""
        state = SelfState()
        result = state.to_dict()

        assert isinstance(result, dict)
        assert "metadata" in result
        assert "components" in result
        assert "legacy_fields" in result

        # Проверяем метаданные
        metadata = result["metadata"]
        assert "version" in metadata
        assert "timestamp" in metadata
        assert "component_type" in metadata
        assert metadata["component_type"] == "SelfState"

    def test_selfstate_composite_serialization(self):
        """Тест композитной сериализации с компонентами."""
        state = SelfState()

        # Устанавливаем некоторые значения
        state.subjective_time_base_rate = 1.5
        state.consciousness_level = 0.7

        result = state.to_dict()

        # Проверяем компоненты
        components = result["components"]
        assert "identity" in components
        assert "physical" in components
        assert "time" in components
        assert "memory" in components
        assert "cognitive" in components
        assert "events" in components

        # Проверяем legacy поля
        legacy = result["legacy_fields"]
        assert "subjective_time_base_rate" in legacy
        assert "consciousness_level" in legacy
        assert legacy["subjective_time_base_rate"] == 1.5
        assert legacy["consciousness_level"] == 0.7

    def test_selfstate_serialization_thread_safety(self):
        """Тест thread-safety сериализации SelfState."""
        state = SelfState()
        results = []
        errors = []

        def modifier():
            """Модификатор состояния."""
            try:
                for i in range(50):
                    state.consciousness_level = float(i) / 50.0
                    state.last_event_intensity = float(i) / 100.0
                    time.sleep(0.001)
            except Exception as e:
                errors.append(f"Modifier error: {e}")

        def serializer():
            """Сериализатор состояния."""
            try:
                for _ in range(20):
                    result = state.to_dict()
                    results.append(result)
                    time.sleep(0.002)
            except Exception as e:
                errors.append(f"Serializer error: {e}")

        # Запускаем параллельно
        mod_thread = threading.Thread(target=modifier)
        ser_thread = threading.Thread(target=serializer)

        mod_thread.start()
        ser_thread.start()

        mod_thread.join(timeout=3.0)
        ser_thread.join(timeout=3.0)

        # Проверяем, что нет ошибок
        assert len(errors) == 0, f"Thread safety errors: {errors}"

        # Проверяем, что все сериализации успешны
        assert len(results) > 0
        for result in results:
            assert isinstance(result, dict)
            assert "metadata" in result
            assert "components" in result

    def test_selfstate_serialization_error_handling(self):
        """Тест обработки ошибок при сериализации компонентов."""
        state = SelfState()

        # Создаем mock компонент, который вызывает исключение
        mock_component = MagicMock()
        mock_component.to_dict.side_effect = Exception("Test serialization error")
        state.cognitive = mock_component

        result = state.to_dict()

        # Сериализация должна завершиться успешно несмотря на ошибку компонента
        assert isinstance(result, dict)
        assert "metadata" in result

        # Должен быть warning в метаданных
        metadata = result["metadata"]
        assert "warnings" in metadata
        assert len(metadata["warnings"]) > 0

        # Компонент с ошибкой должен содержать информацию об ошибке
        components = result["components"]
        assert "cognitive" in components
        cognitive_result = components["cognitive"]
        assert "error" in cognitive_result


class TestStateSerializerIntegration:
    """Интеграционные тесты StateSerializer."""

    def test_full_state_save_load_cycle(self):
        """Тест полного цикла сохранения и загрузки состояния."""
        # Создаем компоненты
        state = SelfState()
        state.identity.life_id = "test_life_123"
        state.consciousness_level = 0.8

        queue = EventQueue()
        event = Event(type="test_event", intensity=0.6, timestamp=time.time(), metadata={"test": True})
        queue.push(event)

        config = {"test_config": True, "version": "1.0"}

        # Сохраняем состояние
        serializer = StateSerializer()
        save_success = serializer.save_restart_state(state, queue, config)

        assert save_success, "State save should succeed"

        # Загружаем состояние
        loaded_state = serializer.load_restart_state()

        assert loaded_state is not None, "State should be loaded"
        assert "self_state" in loaded_state
        assert "event_queue" in loaded_state
        assert "config" in loaded_state

        # Проверяем корректность данных
        loaded_self_state = loaded_state["self_state"]
        assert isinstance(loaded_self_state, dict)
        assert "metadata" in loaded_self_state
        assert loaded_self_state["metadata"]["life_id"] == "test_life_123"

        loaded_event_queue = loaded_state["event_queue"]
        assert isinstance(loaded_event_queue, dict)
        assert "data" in loaded_event_queue
        assert "metadata" in loaded_event_queue

        # Проверяем данные событий
        events = loaded_event_queue["data"]["events"]
        assert isinstance(events, list)
        assert len(events) == 1
        assert events[0]["type"] == "test_event"

        assert loaded_state["config"] == config

    def test_state_serializer_file_operations(self):
        """Тест файловых операций StateSerializer."""
        serializer = StateSerializer()

        # Очищаем файл, если он остался от предыдущих тестов
        serializer.cleanup_restart_state()

        # Проверяем, что файл не существует изначально
        assert not Path(serializer.RESTART_STATE_FILE).exists()

        # Сохраняем состояние
        mock_state = {"test": "data"}
        mock_queue = []
        mock_config = {}

        success = serializer.save_restart_state(mock_state, mock_queue, mock_config)
        assert success

        # Проверяем, что файл создан
        assert Path(serializer.RESTART_STATE_FILE).exists()

        # Загружаем и проверяем
        loaded = serializer.load_restart_state()
        assert loaded is not None

        # Очищаем состояние
        serializer.cleanup_restart_state()

        # Проверяем, что файл удален
        assert not Path(serializer.RESTART_STATE_FILE).exists()

    def test_state_serializer_error_handling(self):
        """Тест обработки ошибок в StateSerializer."""
        serializer = StateSerializer()

        # Тест с некорректными данными
        invalid_state = None  # Объект без to_dict
        invalid_queue = None
        config = {}

        # Сохранение должно обработать отсутствие to_dict gracefully
        success = serializer.save_restart_state(invalid_state, invalid_queue, config)
        assert success  # Использует hasattr проверку

        loaded = serializer.load_restart_state()
        assert loaded is not None
        assert loaded["self_state"] == {}  # Пустой dict по умолчанию
        assert loaded["event_queue"] == []  # Пустой list по умолчанию

        serializer.cleanup_restart_state()


class TestSerializationPerformance:
    """Тесты производительности сериализации."""

    def test_eventqueue_serialization_performance(self):
        """Тест производительности сериализации EventQueue."""
        # Создаем очередь с большим размером для теста производительности
        import queue as queue_module

        # Создаем EventQueue с инициализацией snapshot полей
        queue = EventQueue.__new__(EventQueue)
        queue._queue = queue_module.Queue(maxsize=0)  # Без ограничения размера
        queue._dropped_events_count = 0
        queue.silence_detector = None

        # Инициализируем snapshot поля для сериализации
        queue._snapshot_lock = threading.RLock()
        queue._last_snapshot_time = 0.0
        queue._snapshot_cache = None
        queue._snapshot_cache_lifetime = 0.1

        # Добавляем события (меньше, чтобы тест был быстрее)
        for i in range(500):
            event = Event(
                type=f"perf_event_{i}",
                intensity=float(i % 100) / 100.0,
                timestamp=time.time() + i,
                metadata={"index": i, "data": "x" * 50}  # Меньше данных для скорости
            )
            queue.push(event)

        # Проверяем, что все события добавлены (учитывая размер очереди)
        expected_events = min(500, queue.size())

        # Замеряем время сериализации
        start_time = time.time()
        result = queue.to_dict()
        end_time = time.time()

        serialization_time = end_time - start_time

        # Проверяем корректность
        events = result["data"]["events"]
        assert len(events) == expected_events
        assert isinstance(events[0], dict)

        # Производительность: сериализация должна быть быстрой
        assert serialization_time < 0.5, f"Serialization too slow: {serialization_time}s"

    def test_selfstate_serialization_performance(self):
        """Тест производительности сериализации SelfState."""
        state = SelfState()

        # Замеряем время сериализации
        start_time = time.time()
        result = state.to_dict()
        end_time = time.time()

        serialization_time = end_time - start_time

        # Проверяем корректность
        assert isinstance(result, dict)
        assert "components" in result

        # Производительность: сериализация SelfState должна быть быстрой
        assert serialization_time < 0.1, f"Serialization too slow: {serialization_time}s"


class TestSystemRecoveryIntegration:
    """Интеграционные тесты восстановления системы из сериализованного состояния."""

    def test_full_system_state_roundtrip(self):
        """Тест полного цикла: создание -> сериализация -> восстановление состояния системы."""
        # Создаем исходное состояние
        original_state = SelfState()
        original_state.identity.life_id = "test_recovery_life_123"
        original_state.consciousness_level = 0.75
        original_state.subjective_time_base_rate = 1.2

        # Создаем очередь с событиями
        original_queue = EventQueue()
        test_events = [
            Event(type="recovery_test_1", intensity=0.3, timestamp=1000.0, metadata={"test": "data1"}),
            Event(type="recovery_test_2", intensity=0.7, timestamp=1001.0, metadata={"test": "data2"}),
            Event(type="recovery_test_3", intensity=0.9, timestamp=1002.0, metadata={"test": "data3"}),
        ]
        for event in test_events:
            original_queue.push(event)

        config = {"recovery_test": True, "version": "2.0", "settings": {"debug": True}}

        # Сериализуем состояние
        state_snapshot = original_state.to_dict()
        queue_snapshot = original_queue.to_dict()

        # Проверяем структуру сериализованных данных
        assert isinstance(state_snapshot, dict)
        assert "metadata" in state_snapshot
        assert "components" in state_snapshot
        assert state_snapshot["metadata"]["life_id"] == "test_recovery_life_123"

        assert isinstance(queue_snapshot, dict)
        assert "data" in queue_snapshot
        assert len(queue_snapshot["data"]["events"]) == 3

        # Имитируем восстановление системы (поскольку у нас нет полного механизма десериализации,
        # проверяем корректность сериализованных данных)
        recovered_life_id = state_snapshot["metadata"]["life_id"]
        recovered_events = queue_snapshot["data"]["events"]
        recovered_config = config

        # Проверяем корректность восстановленных данных
        assert recovered_life_id == "test_recovery_life_123"
        assert len(recovered_events) == 3
        assert recovered_events[0]["type"] == "recovery_test_1"
        assert recovered_events[1]["intensity"] == 0.7
        assert recovered_events[2]["timestamp"] == 1002.0
        assert recovered_config["recovery_test"] is True

    def test_corrupted_component_recovery(self):
        """Тест восстановления системы при повреждении компонентов."""
        state = SelfState()

        # Имитируем повреждение компонента
        from unittest.mock import MagicMock
        mock_component = MagicMock()
        mock_component.to_dict.side_effect = Exception("Component corruption")
        state.memory_state = mock_component

        # Сериализация должна обработать ошибку gracefully
        result = state.to_dict()

        # Проверяем, что сериализация завершилась
        assert isinstance(result, dict)
        assert "metadata" in result
        assert "components" in result

        # Поврежденный компонент должен содержать информацию об ошибке
        components = result["components"]
        assert "memory" in components
        memory_result = components["memory"]
        assert "error" in memory_result

        # Должно быть предупреждение в метаданных
        metadata = result["metadata"]
        assert "warnings" in metadata
        assert len(metadata["warnings"]) > 0

    def test_large_scale_state_serialization(self):
        """Тест сериализации состояния с большим количеством данных."""
        state = SelfState()
        queue = EventQueue()

        # Создаем большое количество событий
        large_events = []
        for i in range(200):  # Меньше, чем в производительности, но достаточно для интеграции
            event = Event(
                type=f"large_scale_event_{i}",
                intensity=float(i % 100) / 100.0,
                timestamp=time.time() + i,
                metadata={"index": i, "category": f"cat_{i % 10}"}
            )
            large_events.append(event)
            queue.push(event)

        # Устанавливаем различные параметры состояния
        state.consciousness_level = 0.85
        state.subjective_time_base_rate = 1.8
        state.parameter_history = [
            {"timestamp": time.time() + i, "parameter": f"param_{i}", "value": i}
            for i in range(20)
        ]

        # Сериализуем большое состояние
        state_result = state.to_dict()
        queue_result = queue.to_dict()

        # Проверяем корректность
        assert state_result["metadata"]["component_type"] == "SelfState"
        assert len(queue_result["data"]["events"]) == 200

        # Проверяем, что все события сохранены корректно
        events = queue_result["data"]["events"]
        for i, event in enumerate(events):
            assert event["type"] == f"large_scale_event_{i}"
            assert "metadata" in event
            assert event["metadata"]["index"] == i

    def test_serialization_consistency_across_instances(self):
        """Тест консистентности сериализации между разными экземплярами."""
        # Создаем два идентичных состояния
        state1 = SelfState()
        state2 = SelfState()

        state1.consciousness_level = 0.6
        state1.subjective_time_base_rate = 1.3
        state1.identity.life_id = "consistency_test"

        state2.consciousness_level = 0.6
        state2.subjective_time_base_rate = 1.3
        state2.identity.life_id = "consistency_test"

        # Сериализуем оба состояния
        result1 = state1.to_dict()
        result2 = state2.to_dict()

        # Метаданные могут отличаться (timestamp), но данные должны быть консистентными
        assert result1["legacy_fields"]["consciousness_level"] == result2["legacy_fields"]["consciousness_level"]
        assert result1["legacy_fields"]["subjective_time_base_rate"] == result2["legacy_fields"]["subjective_time_base_rate"]
        assert result1["metadata"]["life_id"] == result2["metadata"]["life_id"]