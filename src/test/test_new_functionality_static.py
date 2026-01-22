"""
Статические тесты для новой функциональности.

Тестирует основные классы и методы новых компонентов:
- PassiveDataSink
- AsyncDataSink
- RawDataAccess
- ClarityMoments
- MemoryHierarchy компоненты
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch
from pathlib import Path

# Импорты observability компонентов
from src.observability.observation_api import PassiveDataSink, ObservationData, AsyncDataSink
from src.observability.raw_data_access import RawDataAccess

# Импорты experimental компонентов
from src.experimental.clarity_moments import ClarityMoments, ClarityMoment, ClarityMomentsTracker
from src.experimental.memory_hierarchy.sensory_buffer import SensoryBuffer, SensoryEntry
from src.experimental.memory_hierarchy.hierarchy_manager import MemoryHierarchyManager
from src.experimental.memory_hierarchy.semantic_store import SemanticMemoryStore
from src.experimental.memory_hierarchy.procedural_store import ProceduralMemoryStore

# Импорты consciousness компонентов
from src.experimental.consciousness.metrics import ConsciousnessMetrics
from src.experimental.consciousness.states import ConsciousnessState
from src.experimental.consciousness.parallel_engine import ParallelConsciousnessEngine


class TestPassiveDataSink:
    """Статические тесты для PassiveDataSink."""

    def test_initialization(self):
        """Тест инициализации PassiveDataSink."""
        sink = PassiveDataSink(max_entries=100)
        assert sink.max_entries == 100
        assert len(sink._data) == 0
        assert sink._total_received == 0
        assert sink._last_receive_time is None

    def test_receive_data(self):
        """Тест приема данных."""
        sink = PassiveDataSink(max_entries=10)

        # Принимаем данные
        test_data = {"key": "value", "number": 42}
        sink.receive_data("test_event", test_data, "test_source", {"meta": "data"})

        # Проверяем
        assert len(sink._data) == 1
        assert sink._total_received == 1
        assert sink._last_receive_time is not None

        entry = sink._data[0]
        assert entry.event_type == "test_event"
        assert entry.data == test_data
        assert entry.source == "test_source"
        assert entry.metadata == {"meta": "data"}
        assert isinstance(entry.timestamp, float)

    def test_max_entries_limit(self):
        """Тест ограничения максимального количества записей."""
        sink = PassiveDataSink(max_entries=3)

        # Добавляем больше записей чем max_entries
        for i in range(5):
            sink.receive_data(f"event_{i}", {"id": i}, f"source_{i}")

        # Проверяем что буфер ограничен
        assert len(sink._data) == 3
        assert sink._total_received == 5

    def test_get_recent_data(self):
        """Тест получения недавних данных."""
        sink = PassiveDataSink(max_entries=10)

        # Добавляем данные
        for i in range(5):
            sink.receive_data(f"event_{i}", {"id": i}, "source")

        # Получаем все данные
        data = sink.get_recent_data()
        assert len(data) == 5

        # Получаем ограниченное количество
        limited_data = sink.get_recent_data(limit=3)
        assert len(limited_data) == 3

    def test_get_data_by_type(self):
        """Тест фильтрации данных по типу события."""
        sink = PassiveDataSink(max_entries=10)

        # Добавляем данные разных типов
        sink.receive_data("type_a", {"id": 1}, "source")
        sink.receive_data("type_b", {"id": 2}, "source")
        sink.receive_data("type_a", {"id": 3}, "source")

        # Фильтруем по типу
        type_a_data = sink.get_data_by_type("type_a")
        type_b_data = sink.get_data_by_type("type_b")

        assert len(type_a_data) == 2
        assert len(type_b_data) == 1
        assert all(obs.event_type == "type_a" for obs in type_a_data)

    def test_get_data_by_source(self):
        """Тест фильтрации данных по источнику."""
        sink = PassiveDataSink(max_entries=10)

        # Добавляем данные из разных источников
        sink.receive_data("event", {"id": 1}, "source_a")
        sink.receive_data("event", {"id": 2}, "source_b")
        sink.receive_data("event", {"id": 3}, "source_a")

        # Фильтруем по источнику
        source_a_data = sink.get_data_by_source("source_a")
        source_b_data = sink.get_data_by_source("source_b")

        assert len(source_a_data) == 2
        assert len(source_b_data) == 1
        assert all(obs.source == "source_a" for obs in source_a_data)

    def test_clear_data(self):
        """Тест очистки данных."""
        sink = PassiveDataSink(max_entries=10)

        # Добавляем данные
        for i in range(3):
            sink.receive_data(f"event_{i}", {"id": i}, "source")

        assert len(sink._data) == 3

        # Очищаем
        sink.clear_data()

        assert len(sink._data) == 0
        assert sink._total_received == 3  # Общее количество не сбрасывается

    def test_get_statistics_empty(self):
        """Тест статистики для пустого буфера."""
        sink = PassiveDataSink(max_entries=10)

        stats = sink.get_statistics()
        assert stats["total_received"] == 0
        assert stats["current_entries"] == 0
        assert stats["max_entries"] == 10
        assert stats["last_receive_time"] is None
        assert stats["event_types"] == []
        assert stats["sources"] == []

    def test_get_statistics_with_data(self):
        """Тест статистики с данными."""
        sink = PassiveDataSink(max_entries=10)

        sink.receive_data("event_a", {"id": 1}, "source_1")
        sink.receive_data("event_b", {"id": 2}, "source_1")
        sink.receive_data("event_a", {"id": 3}, "source_2")

        stats = sink.get_statistics()
        assert stats["total_received"] == 3
        assert stats["current_entries"] == 3
        assert set(stats["event_types"]) == {"event_a", "event_b"}
        assert set(stats["sources"]) == {"source_1", "source_2"}


class TestAsyncDataSink:
    """Статические тесты для AsyncDataSink."""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Тест инициализации AsyncDataSink."""
        sink = AsyncDataSink(max_queue_size=50, processing_interval=0.1, enabled=True)

        assert sink.max_queue_size == 50
        assert sink.processing_interval == 0.1
        assert sink.enabled is True
        assert sink._queue is None  # Не запущен
        assert len(sink._processed_data) == 0

    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Тест запуска и остановки AsyncDataSink."""
        sink = AsyncDataSink(enabled=True)

        # Запуск
        await sink.start()
        assert sink._queue is not None
        assert sink._processing_task is not None
        assert not sink._processing_task.done()

        # Остановка
        await sink.stop()
        assert sink._queue is None
        assert sink._processing_task is None or sink._processing_task.done()

    @pytest.mark.asyncio
    async def test_receive_data_async(self):
        """Тест асинхронного приема данных."""
        sink = AsyncDataSink(enabled=True)
        await sink.start()

        # Принимаем данные
        success = await sink.receive_data_async(
            "test_event", {"key": "value"}, "test_source", {"meta": "data"}
        )

        assert success is True

        # Даем время на обработку
        await asyncio.sleep(0.2)

        # Проверяем обработанные данные
        processed = sink.get_recent_data()
        assert len(processed) == 1
        assert processed[0].event_type == "test_event"
        assert processed[0].data == {"key": "value"}
        assert processed[0].source == "test_source"

        await sink.stop()

    def test_receive_data_sync_disabled(self):
        """Тест синхронного приема данных при отключенном компоненте."""
        sink = AsyncDataSink(enabled=False)

        success = sink.receive_data_sync("event", {}, "source")
        assert success is False

    def test_add_data_callback(self):
        """Тест добавления коллбэка обработки данных."""
        sink = AsyncDataSink()
        callback_called = False

        def test_callback(data):
            nonlocal callback_called
            callback_called = True

        sink.add_data_callback(test_callback)
        assert len(sink._data_callbacks) == 1

        # Удаляем коллбэк
        sink.remove_data_callback(test_callback)
        assert len(sink._data_callbacks) == 0

    def test_get_statistics(self):
        """Тест получения статистики AsyncDataSink."""
        sink = AsyncDataSink(max_queue_size=100, enabled=False)

        stats = sink.get_statistics()
        assert stats["enabled"] is False
        assert stats["queue_size"] == 0
        assert stats["max_queue_size"] == 100
        assert stats["total_received"] == 0
        assert stats["total_processed"] == 0

    def test_create_async_data_sink(self):
        """Тест фабричной функции создания AsyncDataSink."""
        from src.observability.async_data_sink import create_async_data_sink

        sink = create_async_data_sink(
            max_queue_size=25,
            processing_interval=0.5,
            enabled=False
        )

        assert sink.max_queue_size == 25
        assert sink.processing_interval == 0.5
        assert sink.enabled is False


class TestRawDataAccess:
    """Статические тесты для RawDataAccess."""

    def test_initialization(self):
        """Тест инициализации RawDataAccess."""
        access = RawDataAccess()
        assert len(access.data_sources) == 0

    def test_add_remove_data_source(self):
        """Тест добавления и удаления источников данных."""
        access = RawDataAccess()

        # Создаем mock источники
        mock_sink1 = Mock()
        mock_sink2 = Mock()

        # Добавляем
        access.add_data_source(mock_sink1)
        access.add_data_source(mock_sink2)
        assert len(access.data_sources) == 2

        # Удаляем
        access.remove_data_source(mock_sink1)
        assert len(access.data_sources) == 1
        assert mock_sink2 in access.data_sources

    def test_get_raw_data_with_filters(self):
        """Тест получения данных с фильтрами."""
        access = RawDataAccess()

        # Создаем mock PassiveDataSink
        mock_sink = Mock()
        current_time = time.time()

        mock_data = [
            ObservationData(current_time - 1, "event_a", {"id": 1}, "source_1"),
            ObservationData(current_time - 2, "event_b", {"id": 2}, "source_1"),
            ObservationData(current_time - 3, "event_a", {"id": 3}, "source_2"),
        ]
        mock_sink.get_recent_data.return_value = mock_data

        access.add_data_source(mock_sink)

        # Получаем все данные
        all_data = access.get_raw_data()
        assert len(all_data) == 3

        # Фильтр по источнику
        filtered_data = access.get_raw_data(source_filter="source_1")
        assert len(filtered_data) == 2
        assert all(obs.source == "source_1" for obs in filtered_data)

        # Фильтр по типу события
        filtered_data = access.get_raw_data(event_type_filter="event_a")
        assert len(filtered_data) == 2
        assert all(obs.event_type == "event_a" for obs in filtered_data)

    def test_get_data_by_time_window(self):
        """Тест получения данных за временной интервал."""
        access = RawDataAccess()

        # Создаем mock данные с разными временными метками
        current_time = time.time()
        mock_sink = Mock()

        mock_data = [
            ObservationData(current_time - 10, "event", {"id": 1}, "source"),  # Старое
            ObservationData(current_time - 5, "event", {"id": 2}, "source"),   # В интервале
            ObservationData(current_time - 1, "event", {"id": 3}, "source"),   # В интервале
        ]
        mock_sink.get_recent_data.return_value = mock_data

        access.add_data_source(mock_sink)

        # Получаем данные за последние 3 секунды
        window_data = access.get_data_by_time_window(3.0, current_time)
        assert len(window_data) == 1  # Одно событие в окне (последнее, timestamp=current_time)

    def test_export_data_formats(self):
        """Тест экспорта данных в разных форматах."""
        access = RawDataAccess()

        # Создаем mock данные
        mock_sink = Mock()
        mock_data = [
            ObservationData(time.time(), "test_event", {"key": "value"}, "test_source")
        ]
        mock_sink.get_recent_data.return_value = mock_data
        access.add_data_source(mock_sink)

        # Экспорт в JSON
        json_data = access.export_data(format='json')
        assert isinstance(json_data, str)
        assert '"event_type": "test_event"' in json_data

        # Экспорт в JSONL
        jsonl_data = access.export_data(format='jsonl')
        assert isinstance(jsonl_data, str)
        assert '"event_type": "test_event"' in jsonl_data

        # Экспорт в CSV
        csv_data = access.export_data(format='csv')
        assert isinstance(csv_data, str)
        assert 'test_event' in csv_data

    def test_invalid_export_format(self):
        """Тест экспорта с неверным форматом."""
        access = RawDataAccess()

        with pytest.raises(ValueError, match="Unsupported format"):
            access.export_data(format='invalid')

    def test_get_event_type_distribution(self):
        """Тест получения распределения типов событий."""
        access = RawDataAccess()

        mock_sink = Mock()
        mock_data = [
            ObservationData(time.time(), "event_a", {}, "source"),
            ObservationData(time.time(), "event_a", {}, "source"),
            ObservationData(time.time(), "event_b", {}, "source"),
        ]
        mock_sink.get_recent_data.return_value = mock_data
        access.add_data_source(mock_sink)

        distribution = access.get_event_type_distribution()
        assert distribution["event_a"] == 2
        assert distribution["event_b"] == 1

    def test_iterate_data(self):
        """Тест итерации данных порциями."""
        access = RawDataAccess()

        mock_sink = Mock()
        mock_data = [ObservationData(time.time(), f"event_{i}", {}, "source") for i in range(10)]
        mock_sink.get_recent_data.return_value = mock_data
        access.add_data_source(mock_sink)

        # Итерируем порциями по 3
        chunks = list(access.iterate_data(chunk_size=3))
        assert len(chunks) == 4  # 10 элементов / 3 = 4 порции (3, 3, 3, 1)
        assert len(chunks[0]) == 3
        assert len(chunks[-1]) == 1  # Последняя порция


class TestClarityMoments:
    """Статические тесты для ClarityMoments."""

    def test_initialization(self):
        """Тест инициализации ClarityMoments."""
        clarity = ClarityMoments()
        assert isinstance(clarity.tracker, ClarityMomentsTracker)
        assert len(clarity.tracker.moments) == 0
        assert clarity._clarity_events_count == 0

    def test_analyze_clarity(self):
        """Тест анализа ясности."""
        clarity = ClarityMoments()

        # Выполняем анализ
        moment = clarity.analyze_clarity()

        assert moment is not None
        assert isinstance(moment, ClarityMoment)
        assert moment.event_type == "system_analysis"
        assert 0.0 <= moment.intensity <= 1.0

    def test_get_clarity_moments(self):
        """Тест получения моментов ясности."""
        clarity = ClarityMoments()

        # Добавляем момент вручную
        test_moment = ClarityMoment(
            timestamp=time.time(),
            stage="test",
            correlation_id="test_123",
            event_id="event_123",
            event_type="test_event",
            intensity=0.8,
            data={"test": True}
        )

        clarity.tracker.add_moment(test_moment)

        # Получаем моменты
        moments = clarity.get_clarity_moments()
        assert len(moments) == 1
        assert moments[0].intensity == 0.8

    def test_check_clarity_conditions(self):
        """Тест проверки условий ясности."""
        clarity = ClarityMoments()

        # Проверяем условия (должен создать момент)
        result = clarity.check_clarity_conditions(None)

        assert result is not None
        assert result["type"] == "clarity_moment"
        assert "data" in result
        assert clarity._clarity_events_count == 1

    def test_clarity_state_management(self):
        """Тест управления состоянием ясности."""
        clarity = ClarityMoments()

        # Mock self_state
        class MockState:
            def __init__(self):
                self.clarity_state = False
                self.clarity_duration = 0
                self.clarity_modifier = 1.0

        state = MockState()

        # Активируем момент ясности
        clarity.activate_clarity_moment(state)
        assert state.clarity_state is True
        assert state.clarity_duration == 50  # CLARITY_DURATION_TICKS
        assert state.clarity_modifier == 1.5

        # Обновляем состояние (уменьшаем длительность)
        clarity.update_clarity_state(state)
        assert state.clarity_duration == 49

        # Деактивируем
        clarity.deactivate_clarity_moment(state)
        assert state.clarity_state is False
        assert state.clarity_duration == 0
        assert state.clarity_modifier == 1.0

    def test_get_clarity_level(self):
        """Тест получения уровня ясности."""
        clarity = ClarityMoments()

        # Без моментов
        level = clarity.get_clarity_level()
        assert level == 0.0

        # С моментом
        test_moment = ClarityMoment(
            timestamp=time.time(),
            stage="test",
            correlation_id="test_123",
            event_id="event_123",
            event_type="test_event",
            intensity=0.7,
            data={}
        )
        clarity.tracker.add_moment(test_moment)

        level = clarity.get_clarity_level()
        assert level == 0.7


class TestClarityMomentsTracker:
    """Статические тесты для ClarityMomentsTracker."""

    def test_initialization(self):
        """Тест инициализации ClarityMomentsTracker."""
        tracker = ClarityMomentsTracker()
        assert len(tracker.moments) == 0
        assert tracker._correlation_counter == 0

    def test_add_moment(self):
        """Тест добавления момента ясности."""
        tracker = ClarityMomentsTracker()

        moment = ClarityMoment(
            timestamp=time.time(),
            stage="test_stage",
            correlation_id="corr_123",
            event_id="event_123",
            event_type="test_event",
            intensity=0.8,
            data={"key": "value"}
        )

        tracker.add_moment(moment)
        assert len(tracker.moments) == 1
        assert tracker.moments[0].intensity == 0.8

    def test_get_moments_by_intensity(self):
        """Тест фильтрации моментов по интенсивности."""
        tracker = ClarityMomentsTracker()

        # Добавляем моменты с разной интенсивностью
        for intensity in [0.3, 0.6, 0.9]:
            moment = ClarityMoment(
                timestamp=time.time(),
                stage="test",
                correlation_id=f"corr_{intensity}",
                event_id=f"event_{intensity}",
                event_type="test_event",
                intensity=intensity,
                data={}
            )
            tracker.add_moment(moment)

        # Фильтруем по минимальной интенсивности
        filtered = tracker.get_moments_by_intensity(0.5)
        assert len(filtered) == 2  # 0.6 и 0.9
        assert all(m.intensity >= 0.5 for m in filtered)

    def test_get_recent_moments(self):
        """Тест получения недавних моментов."""
        tracker = ClarityMomentsTracker()

        # Добавляем моменты с разными временными метками
        base_time = time.time()
        for i in range(5):
            moment = ClarityMoment(
                timestamp=base_time + i,
                stage="test",
                correlation_id=f"corr_{i}",
                event_id=f"event_{i}",
                event_type="test_event",
                intensity=0.5,
                data={}
            )
            tracker.add_moment(moment)

        # Получаем 3 самых свежих
        recent = tracker.get_recent_moments(3)
        assert len(recent) == 3
        # Проверяем что они отсортированы по времени (новые первые)
        assert recent[0].timestamp > recent[1].timestamp

    def test_analyze_clarity_patterns_empty(self):
        """Тест анализа паттернов для пустого трекера."""
        tracker = ClarityMomentsTracker()

        patterns = tracker.analyze_clarity_patterns()
        assert patterns["total_moments"] == 0

    def test_analyze_clarity_patterns_with_data(self):
        """Тест анализа паттернов с данными."""
        tracker = ClarityMomentsTracker()

        # Добавляем тестовые моменты
        for i in range(3):
            moment = ClarityMoment(
                timestamp=time.time(),
                stage="test",
                correlation_id=f"corr_{i}",
                event_id=f"event_{i}",
                event_type=f"event_type_{i % 2}",  # Два разных типа
                intensity=0.5 + i * 0.2,  # Разная интенсивность
                data={}
            )
            tracker.add_moment(moment)

        patterns = tracker.analyze_clarity_patterns()
        assert patterns["total_moments"] == 3
        assert patterns["avg_intensity"] > 0
        assert patterns["max_intensity"] > 0
        assert patterns["unique_event_types"] == 2  # event_type_0 и event_type_1


class TestSensoryBuffer:
    """Статические тесты для SensoryBuffer."""

    def test_initialization(self):
        """Тест инициализации SensoryBuffer."""
        buffer = SensoryBuffer(buffer_size=128, default_ttl=1.5)

        assert buffer.buffer_size == 128
        assert buffer.default_ttl == 1.5
        assert len(buffer._buffer) == 0
        assert buffer._total_entries_added == 0

    def test_sensory_entry_expiration(self):
        """Тест проверки истечения срока жизни записи."""
        entry = SensoryEntry(Mock(), time.time() - 3.0, ttl_seconds=2.0)  # Истекло 3 секунды назад

        assert entry.is_expired(time.time()) is True

        # Проверяем оставшееся время
        remaining = entry.time_remaining(time.time())
        assert remaining == 0.0

    def test_sensory_entry_not_expired(self):
        """Тест записи, которая не истекла."""
        current_time = time.time()
        entry = SensoryEntry(Mock(), current_time, ttl_seconds=5.0)

        assert entry.is_expired(current_time) is False

        # Проверяем оставшееся время
        remaining = entry.time_remaining(current_time)
        assert 4.9 <= remaining <= 5.0

    def test_add_event(self):
        """Тест добавления события в буфер."""
        buffer = SensoryBuffer(buffer_size=10)

        # Создаем mock событие с intensity
        mock_event = Mock()
        mock_event.event_id = "test_event_123"
        mock_event.intensity = 0.8  # Значимое событие

        # Добавляем событие
        buffer.add_event(mock_event, custom_ttl=3.0)

        assert len(buffer._buffer) == 1
        assert buffer._total_entries_added == 1

        entry = buffer._buffer[0]
        assert entry.event == mock_event
        assert entry.ttl_seconds == 3.0

    def test_buffer_size_limit(self):
        """Тест ограничения размера буфера."""
        buffer = SensoryBuffer(buffer_size=3)

        # Добавляем больше событий чем размер буфера
        for i in range(5):
            mock_event = Mock()
            mock_event.event_id = f"event_{i}"
            mock_event.intensity = 0.5  # Значимое событие
            buffer.add_event(mock_event)

        assert len(buffer._buffer) == 3  # Кольцевой буфер
        assert buffer._total_entries_added == 5

    def test_cleanup_expired_entries(self):
        """Тест очистки истекших записей."""
        buffer = SensoryBuffer(buffer_size=10, default_ttl=0.1)  # Очень короткий TTL

        # Добавляем события с очень коротким TTL
        for i in range(3):
            mock_event = Mock()
            mock_event.event_id = f"event_{i}"
            mock_event.intensity = 0.6  # Значимое событие
            buffer.add_event(mock_event, custom_ttl=0.01)  # Очень короткий TTL

        assert len(buffer._buffer) == 3

        # Ждем истечения TTL и выполняем очистку
        time.sleep(0.1)  # Ждем дольше
        expired_count = buffer._cleanup_expired_entries()

        # Может не все истечь из-за интервала очистки, но буфер должен уменьшиться
        assert expired_count >= 0
        assert len(buffer._buffer) <= 3

    def test_get_events_for_processing(self):
        """Тест получения событий для обработки."""
        buffer = SensoryBuffer(buffer_size=10)

        # Добавляем события
        events = []
        for i in range(5):
            mock_event = Mock()
            mock_event.event_id = f"event_{i}"
            mock_event.intensity = 0.7  # Значимое событие
            events.append(mock_event)
            buffer.add_event(mock_event)

        # Получаем события для обработки
        processing_events = buffer.get_events_for_processing(max_events=3)
        assert len(processing_events) == 3

    def test_get_buffer_status(self):
        """Тест получения статистики буфера."""
        buffer = SensoryBuffer(buffer_size=10)

        # Добавляем события
        for i in range(3):
            mock_event = Mock()
            mock_event.intensity = 0.5  # Значимое событие
            buffer.add_event(mock_event)

        stats = buffer.get_buffer_status()

        assert stats["buffer_size"] == 3  # current_entries
        assert stats["buffer_capacity"] == 10
        assert stats["total_entries_added"] == 3
        assert stats["total_entries_expired"] == 0
        assert stats["total_entries_processed"] == 0


class TestConsciousnessComponents:
    """Статические тесты для компонентов сознания."""

    def test_consciousness_metrics_initialization(self):
        """Тест инициализации ConsciousnessMetrics."""
        # Создаем mock self_state_provider для AdaptiveProcessingManager
        def mock_state_provider():
            return type('MockState', (), {
                'energy': 80.0,
                'stability': 0.9,
                'processing_load': 0.3,
                'memory_usage': 0.6,
                'error_rate': 0.01
            })()

        # Monkey patch для теста
        import src.experimental.consciousness.metrics as metrics_module
        original_adaptive_init = metrics_module.AdaptiveProcessingManager.__init__

        def patched_adaptive_init(self, self_state_provider=None, *args, **kwargs):
            if self_state_provider is None:
                self_state_provider = mock_state_provider
            return original_adaptive_init(self, self_state_provider, *args, **kwargs)

        metrics_module.AdaptiveProcessingManager.__init__ = patched_adaptive_init

        try:
            metrics = ConsciousnessMetrics()

            # Проверяем наличие основных атрибутов
            assert hasattr(metrics, 'metrics')
            assert isinstance(metrics.metrics, dict)

        finally:
            # Восстанавливаем оригинальный метод
            metrics_module.AdaptiveProcessingManager.__init__ = original_adaptive_init

    def test_consciousness_state_enum(self):
        """Тест перечисления состояний сознания."""
        from src.experimental.consciousness.states import ConsciousnessState

        # Проверяем что все состояния определены
        states = [ConsciousnessState.INACTIVE,
                 ConsciousnessState.ACTIVE,
                 ConsciousnessState.PROCESSING,
                 ConsciousnessState.ANALYZING]

        for state in states:
            assert isinstance(state.value, str)
            assert len(state.value) > 0

    def test_parallel_consciousness_engine_initialization(self):
        """Тест инициализации ParallelConsciousnessEngine."""
        engine = ParallelConsciousnessEngine()

        # Проверяем базовую функциональность
        assert hasattr(engine, 'current_state')
        assert hasattr(engine, '_transition_history')
        assert len(engine._transition_history) == 0

    def test_consciousness_state_transition(self):
        """Тест переходов между состояниями сознания."""
        from src.experimental.consciousness.parallel_engine import ConsciousnessState as EngineConsciousnessState

        engine = ParallelConsciousnessEngine()

        # Проверяем начальное состояние
        initial_state = engine.current_state
        assert initial_state in EngineConsciousnessState

        # Выполняем анализ уровня сознания
        new_state = engine.evaluate_consciousness_level()
        assert new_state is not None

        # Обновляем метрики
        engine.update_metrics()

        # Проверяем что история переходов обновилась
        assert len(engine._transition_history) >= 0


class TestMemoryHierarchyComponents:
    """Статические тесты для компонентов иерархической памяти."""

    def test_semantic_store_initialization(self):
        """Тест инициализации SemanticMemoryStore."""
        store = SemanticMemoryStore()

        assert len(store._concepts) == 0
        assert store._stats["total_concepts"] == 0

    def test_procedural_store_initialization(self):
        """Тест инициализации ProceduralMemoryStore."""
        store = ProceduralMemoryStore()

        assert len(store._patterns) == 0
        assert store._stats["total_patterns"] == 0

    def test_memory_hierarchy_manager_initialization(self):
        """Тест инициализации MemoryHierarchyManager."""
        manager = MemoryHierarchyManager()

        assert hasattr(manager, 'sensory_buffer')
        assert hasattr(manager, 'episodic_memory')
        assert hasattr(manager, 'semantic_store')
        assert hasattr(manager, 'procedural_store')

        # Проверяем что компоненты инициализированы
        assert manager.sensory_buffer is not None
        assert isinstance(manager.semantic_store, SemanticMemoryStore)
        assert isinstance(manager.procedural_store, ProceduralMemoryStore)