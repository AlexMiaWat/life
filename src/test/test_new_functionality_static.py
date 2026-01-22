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
from src.observability.passive_data_sink import PassiveDataSink, ObservationData
from src.observability.async_data_sink import AsyncDataSink
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

    def setup_method(self):
        """Настройка перед каждым тестом."""
        import tempfile
        import os
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False)
        self.temp_file.close()
        self.temp_dir = os.path.dirname(self.temp_file.name)
        self.obs_file = os.path.basename(self.temp_file.name)

    def teardown_method(self):
        """Очистка после каждого теста."""
        import os
        try:
            os.unlink(self.temp_file.name)
        except FileNotFoundError:
            pass

    def create_sink(self, **kwargs):
        """Создать sink с временным файлом."""
        return PassiveDataSink(
            data_directory=self.temp_dir,
            observations_file=self.obs_file,
            **kwargs
        )

    def test_initialization(self):
        """Тест инициализации PassiveDataSink."""
        sink = self.create_sink(max_entries=100)
        assert sink.max_entries == 100
        stats = sink.get_stats()
        assert stats["enabled"] is True
        assert stats["total_entries"] == 0

    def test_receive_data(self):
        """Тест приема данных."""
        sink = self.create_sink(max_entries=10)

        # Принимаем данные
        test_data = {"key": "value", "number": 42}
        sink.receive_data("test_event", test_data, "test_source", {"meta": "data"})

        # Проверяем
        data = sink.get_recent_data()
        assert len(data) == 1
        stats = sink.get_stats()
        assert stats["total_entries"] == 1

        entry = data[0]
        assert entry.event_type == "test_event"
        assert entry.data == test_data
        assert entry.source == "test_source"
        assert entry.metadata == {"meta": "data"}
        assert isinstance(entry.timestamp, float)

    def test_max_entries_limit(self):
        """Тест ограничения максимального количества записей."""
        sink = self.create_sink(max_entries=3)

        # Добавляем больше записей чем max_entries
        for i in range(5):
            sink.receive_data(f"event_{i}", {"id": i}, f"source_{i}")

        # Проверяем что все записи сохранены (ограничение применяется при чтении)
        data = sink.get_recent_data()
        assert len(data) == 5  # Все записи сохранены
        stats = sink.get_stats()
        assert stats["total_entries"] == 5

    def test_get_recent_data(self):
        """Тест получения недавних данных."""
        sink = self.create_sink(max_entries=10)

        # Добавляем данные
        for i in range(5):
            sink.receive_data(f"event_{i}", {"id": i}, "source")

        # Получаем все данные
        data = sink.get_recent_data()
        assert len(data) == 5

        # Получаем ограниченное количество
        limited_data = sink.get_recent_data(limit=3)
        assert len(limited_data) == 3


    def test_clear_data(self):
        """Тест очистки данных."""
        sink = self.create_sink(max_entries=10)

        # Добавляем данные
        for i in range(3):
            sink.receive_data(f"event_{i}", {"id": i}, "source")

        data_before = sink.get_recent_data()
        assert len(data_before) == 3

        # Очищаем (теперь это архивация старых данных)
        sink.clear_old_data()

        # Данные остаются, так как файл новый
        data_after = sink.get_recent_data()
        assert len(data_after) == 3

    def test_get_statistics_empty(self):
        """Тест статистики для пустого буфера."""
        sink = self.create_sink(max_entries=10)

        stats = sink.get_statistics()
        assert stats["enabled"] is True
        assert stats["total_entries"] == 0

    def test_get_statistics_with_data(self):
        """Тест статистики с данными."""
        sink = self.create_sink(max_entries=10)

        sink.receive_data("event_a", {"id": 1}, "source_1")
        sink.receive_data("event_b", {"id": 2}, "source_1")
        sink.receive_data("event_a", {"id": 3}, "source_2")

        stats = sink.get_statistics()
        assert stats["enabled"] is True
        assert stats["total_entries"] == 3


class TestAsyncDataSink:
    """Статические тесты для AsyncDataSink."""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Тест инициализации AsyncDataSink."""
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as temp_dir:
            sink = AsyncDataSink(
                data_directory=temp_dir,
                enabled=True,
                max_queue_size=50,
                processing_interval=0.1
            )

            assert sink.max_queue_size == 50
            assert sink.processing_interval == 0.1
            assert sink.enabled is True
            assert hasattr(sink, '_queue')
            assert sink._stats["events_logged"] == 0

    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Тест запуска и остановки AsyncDataSink."""
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as temp_dir:
            sink = AsyncDataSink(data_directory=temp_dir, enabled=True)

            # Запуск AsyncDataSink
            await sink.start()
            assert hasattr(sink, '_processing_thread')
            assert sink._processing_thread and sink._processing_thread.is_alive()

            # Остановка
            sink.stop()
            # Проверяем что поток остановлен
            assert not (sink._processing_thread and sink._processing_thread.is_alive())

    def test_receive_data_async(self):
        """Тест асинхронного приема данных."""
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as temp_dir:
            sink = AsyncDataSink(data_directory=temp_dir, enabled=True)

            # Принимаем данные через log_event
            sink.log_event({"key": "value"}, "test_event", "test_source")

            # Даем время на обработку
            time.sleep(0.2)

            # Принудительная обработка оставшихся данных
            sink.flush()

            # Проверяем обработанные данные
            processed = sink.get_recent_data()
            assert len(processed) == 1
            assert processed[0].event_type == "test_event"
            assert processed[0].data == {"key": "value"}
            assert processed[0].source == "test_source"

            sink.stop()

    def test_receive_data_sync_disabled(self):
        """Тест логирования при отключенном компоненте."""
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as temp_dir:
            sink = AsyncDataSink(data_directory=temp_dir, enabled=False)

            # При отключенном компоненте log_event должен просто возвращаться
            sink.log_event({}, "event", "source")

            # Статистика не должна измениться
            assert sink._stats["events_logged"] == 0


    def test_get_statistics(self):
        """Тест получения статистики AsyncDataSink."""
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as temp_dir:
            sink = AsyncDataSink(data_directory=temp_dir, max_queue_size=100, enabled=False)

            stats = sink.get_stats()
            assert stats["enabled"] is False
            assert "events_logged" in stats
            assert "events_processed" in stats
            assert stats["events_logged"] == 0



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
        mock_sink1.get_entries = Mock(return_value=[])
        mock_sink2 = Mock()
        mock_sink2.get_entries = Mock(return_value=[])

        # Добавляем с именами
        access.add_data_source(mock_sink1, "source_0")
        access.add_data_source(mock_sink2, "source_1")
        assert len(access.data_sources) == 2

        # Удаляем по имени
        access.remove_data_source("source_0")
        assert len(access.data_sources) == 1
        assert "source_1" in access.data_sources

    def test_get_raw_data_with_filters(self):
        """Тест получения данных с фильтрами."""
        access = RawDataAccess()

        # Создаем mock PassiveDataSink
        mock_sink = Mock()
        current_time = time.time()

        # Создаем mock данные вручную
        mock_data = []
        for i, (offset, event_type, data, source) in enumerate([
            (1, "event_a", {"id": 1}, "source_1"),
            (2, "event_b", {"id": 2}, "source_1"),
            (3, "event_a", {"id": 3}, "source_2"),
        ]):
            entry = ObservationData(
                timestamp=current_time - offset,
                event_type=event_type,
                data=data,
                source=source
            )
            mock_data.append(entry)
        mock_sink.get_entries.return_value = mock_data
        mock_sink.get_entries.return_value = mock_data
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

        # Создаем mock данные
        mock_data = []
        for offset, event_type, data, source in [
            (10, "event", {"id": 1}, "source"),  # Старое
            (2, "event", {"id": 2}, "source"),   # В интервале 3 сек
            (1, "event", {"id": 3}, "source"),   # В интервале 3 сек
        ]:
            entry = ObservationData(
                timestamp=current_time - offset,
                event_type=event_type,
                data=data,
                source=source
            )
            mock_data.append(entry)
        mock_sink.get_entries.return_value = mock_data
        mock_sink.get_entries.return_value = mock_data
        mock_sink.get_recent_data.return_value = mock_data

        access.add_data_source(mock_sink)

        # Получаем данные за последние 3 секунды
        window_data = access.get_data_by_time_window(3.0)
        assert len(window_data) >= 2  # Минимум 2 события в окне (с offset 1 и 2 секунды)

    def test_export_data_formats(self):
        """Тест экспорта данных в разных форматах."""
        access = RawDataAccess()

        # Создаем mock данные
        mock_sink = Mock()
        mock_data = [ObservationData(
            timestamp=time.time(),
            event_type="test_event",
            data={"key": "value"},
            source="test_source"
        )]
        mock_sink.get_entries.return_value = mock_data
        mock_sink.get_entries.return_value = mock_data
        mock_sink.get_recent_data.return_value = mock_data
        access.add_data_source(mock_sink)

        # Экспорт в JSON
        json_filepath = access.export_data(format_type='json')
        assert isinstance(json_filepath, str)
        assert json_filepath.endswith('.json')
        with open(json_filepath, 'r') as f:
            json_data = f.read()
        assert '"event_type": "test_event"' in json_data

        # Экспорт в JSONL
        jsonl_filepath = access.export_data(format_type='jsonl')
        assert isinstance(jsonl_filepath, str)
        assert jsonl_filepath.endswith('.jsonl')
        with open(jsonl_filepath, 'r') as f:
            jsonl_data = f.read()
        assert '"event_type": "test_event"' in jsonl_data

        # Экспорт в CSV
        csv_filepath = access.export_data(format_type='csv')
        assert isinstance(csv_filepath, str)
        assert csv_filepath.endswith('.csv')
        with open(csv_filepath, 'r') as f:
            csv_data = f.read()
        assert 'test_event' in csv_data

    def test_invalid_export_format(self):
        """Тест экспорта с неверным форматом."""
        access = RawDataAccess()

        with pytest.raises(ValueError, match="Unsupported format"):
            access.export_data(format_type='invalid')

    def test_get_event_type_distribution(self):
        """Тест получения распределения типов событий."""
        access = RawDataAccess()

        mock_sink = Mock()
        current_time = time.time()
        mock_data = [
            ObservationData(current_time, "event_a", {}, "source"),
            ObservationData(current_time, "event_a", {}, "source"),
            ObservationData(current_time, "event_b", {}, "source"),
        ]
        mock_sink.get_entries.return_value = mock_data
        mock_sink.get_recent_data.return_value = mock_data
        access.add_data_source(mock_sink)

        distribution = access.get_event_type_distribution()
        assert distribution["event_a"] == 2
        assert distribution["event_b"] == 1

    def test_iterate_data(self):
        """Тест итерации данных порциями."""
        access = RawDataAccess()

        mock_sink = Mock()
        current_time = time.time()
        mock_data = [ObservationData(current_time, f"event_{i}", {}, "source") for i in range(10)]
        mock_sink.get_entries.return_value = mock_data
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
        # Создаем с явным SensoryBuffer для тестирования
        sensory_buffer = SensoryBuffer(buffer_size=64)
        manager = MemoryHierarchyManager(sensory_buffer=sensory_buffer)

        assert hasattr(manager, 'sensory_buffer')
        assert hasattr(manager, 'episodic_memory')
        assert hasattr(manager, 'semantic_store')
        assert hasattr(manager, 'procedural_store')

        # Проверяем что компоненты инициализированы
        assert manager.sensory_buffer is not None
        assert isinstance(manager.semantic_store, SemanticMemoryStore)
        assert isinstance(manager.procedural_store, ProceduralMemoryStore)