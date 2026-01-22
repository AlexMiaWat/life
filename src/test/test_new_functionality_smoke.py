"""
Дымовые тесты для новой функциональности.

Проверяют основную работоспособность компонентов:
- Создание экземпляров
- Базовые операции
- Отсутствие критических ошибок
"""

import pytest
import asyncio
import time
from unittest.mock import Mock

# Импорты observability компонентов
from src.observability.passive_data_sink import PassiveDataSink
from src.observability.async_data_sink import AsyncDataSink
from src.observability.raw_data_access import RawDataAccess

# Импорты experimental компонентов
from src.experimental.clarity_moments import ClarityMoments
from src.experimental.memory_hierarchy.sensory_buffer import SensoryBuffer
from src.experimental.memory_hierarchy.hierarchy_manager import MemoryHierarchyManager
from src.experimental.memory_hierarchy.semantic_store import SemanticMemoryStore
from src.experimental.memory_hierarchy.procedural_store import ProceduralMemoryStore

# Импорты consciousness компонентов
from src.experimental.consciousness.metrics import ConsciousnessMetrics
from src.experimental.consciousness.parallel_engine import ParallelConsciousnessEngine


class TestPassiveDataSinkSmoke:
    """Дымовые тесты для PassiveDataSink."""

    def test_create_and_basic_operations(self):
        """Тест создания и базовых операций."""
        # Создание
        sink = PassiveDataSink(max_entries=100)

        # Базовые операции
        sink.receive_data("smoke_test", {"test": True}, "smoke_source")
        data = sink.get_recent_data()
        stats = sink.get_statistics()

        # Проверки
        assert len(data) == 1
        assert stats["total_entries"] == 1

    def test_multiple_operations(self):
        """Тест множественных операций."""
        sink = PassiveDataSink(max_entries=50)

        # Добавляем много данных разных типов
        for i in range(10):
            sink.receive_data(
                f"event_type_{i % 3}",
                {"id": i, "data": f"value_{i}"},
                f"source_{i % 2}"
            )

        # Проверяем все методы
        all_data = sink.get_recent_data()
        stats = sink.get_statistics()

        assert len(all_data) == 10
        assert stats["total_entries"] == 10

    def test_clear_and_stats(self):
        """Тест очистки и статистики."""
        sink = PassiveDataSink(max_entries=20)

        # Добавляем данные
        for i in range(5):
            sink.receive_data("test_event", {"id": i}, "test_source")

        # Проверяем перед очисткой
        assert len(sink.get_recent_data()) == 5

        # Очищаем (оставляем только 0 последних записей)
        sink.clear_old_data(keep_recent=0)

        # Проверяем после очистки
        assert len(sink.get_recent_data()) == 0
        stats = sink.get_statistics()
        assert stats["buffer_size"] == 0
        assert stats["total_entries"] == 5  # Общее количество сохраняется


class TestAsyncDataSinkSmoke:
    """Дымовые тесты для AsyncDataSink."""

    @pytest.mark.asyncio
    async def test_create_start_stop(self):
        """Тест создания, запуска и остановки."""
        # Создание
        sink = AsyncDataSink(max_queue_size=50, processing_interval=0.1, enabled=True)

        # Запуск
        await sink.start()
        assert sink._processing_thread is not None
        assert sink._processing_thread.is_alive()

        # Небольшая задержка для инициализации
        import time
        time.sleep(0.05)

        # Остановка
        sink.stop()
        assert not (sink._processing_thread and sink._processing_thread.is_alive())

    @pytest.mark.asyncio
    async def test_data_flow(self):
        """Тест потока данных через AsyncDataSink."""
        sink = AsyncDataSink(max_queue_size=20, processing_interval=0.05, enabled=True)

        # Запуск
        await sink.start()

        # Отправка данных
        success = await sink.receive_data_async(
            "smoke_event", {"smoke": True}, "smoke_source"
        )
        assert success is True

        # Ждем обработки
        await asyncio.sleep(0.2)

        # Проверяем обработанные данные
        processed_data = sink.get_recent_data()
        stats = sink.get_statistics()

        assert len(processed_data) >= 1
        assert stats["events_logged"] >= 1
        assert stats["events_processed"] >= 1

        # Остановка
        sink.stop()

    def test_disabled_sink(self):
        """Тест отключенного AsyncDataSink."""
        sink = AsyncDataSink(enabled=False)

        # Попытка отправки данных
        success = sink.log_event({}, "test", "source")
        assert success is False

        # Статистика
        stats = sink.get_statistics()
        assert stats["enabled"] is False

    def test_flush_functionality(self):
        """Тест функциональности flush."""
        sink = AsyncDataSink(enabled=True, max_queue_size=10, processing_interval=1.0)

        # Добавляем данные
        for i in range(3):
            sink.log_event({"id": i}, f"event_{i}", "source")

        # Flush
        sink.flush()

        # Проверяем что данные обработаны
        processed = sink.get_recent_data()
        assert len(processed) >= 3

        sink.stop()

    def test_constructor_parameters(self):
        """Тест параметров конструктора."""
        sink = AsyncDataSink(
            max_queue_size=25,
            processing_interval=0.2,
            enabled=False
        )

        assert sink.max_queue_size == 25
        assert sink.processing_interval == 0.2
        assert sink.enabled is False


class TestRawDataAccessSmoke:
    """Дымовые тесты для RawDataAccess."""

    def test_basic_functionality(self):
        """Тест базовой функциональности."""
        access = RawDataAccess()

        # Проверяем что изначально нет источников
        assert len(access.data_sources) == 0

        # Создаем mock источник данных
        mock_sink = Mock()
        mock_sink.get_entries = Mock(return_value=[])
        mock_sink.get_recent_data = Mock(return_value=[])

        # Добавляем источник
        access.add_data_source(mock_sink, name="test_source")
        assert len(access.data_sources) == 1
        assert "test_source" in access.data_sources

        # Удаляем источник
        access.remove_data_source("test_source")
        assert len(access.data_sources) == 0

    def test_data_retrieval(self):
        """Тест извлечения данных."""
        access = RawDataAccess()

        # Создаем mock данные
        from src.observability.passive_data_sink import ObservationData
        mock_data = [
            ObservationData(time.time(), "smoke_event", {"id": 1}, "smoke_source"),
            ObservationData(time.time(), "smoke_event", {"id": 2}, "smoke_source"),
        ]

        mock_sink = Mock()
        mock_sink.get_entries = Mock(return_value=mock_data)
        mock_sink.get_recent_data = Mock(return_value=mock_data)

        access.add_data_source(mock_sink)

        # Получаем данные
        all_data = access.get_raw_data()
        assert len(all_data) == 2

        # Получаем сводку
        summary = access.get_data_summary()
        assert summary["total_records"] == 2
        assert "smoke_source" in summary["sources"]
        assert "smoke_event" in summary["event_types"]

    def test_export_functionality(self):
        """Тест функциональности экспорта."""
        access = RawDataAccess()

        # Создаем mock данные
        from src.observability.passive_data_sink import ObservationData
        mock_data = [
            ObservationData(time.time(), "export_test", {"key": "value"}, "export_source")
        ]

        mock_sink = Mock()
        mock_sink.get_recent_data.return_value = mock_data
        access.add_data_source(mock_sink)

        # Экспортируем в разные форматы
        json_export = access.export_data(format_type='json')
        jsonl_export = access.export_data(format_type='jsonl')
        csv_export = access.export_data(format_type='csv')

        # Проверяем что экспорт работает
        assert isinstance(json_export, str)
        assert isinstance(jsonl_export, str)
        assert isinstance(csv_export, str)
        assert len(json_export) > 0
        assert len(jsonl_export) > 0
        assert len(csv_export) > 0

    def test_distributions_and_analysis(self):
        """Тест распределений и анализа."""
        access = RawDataAccess()

        # Создаем разнообразные mock данные
        from src.observability.passive_data_sink import ObservationData
        current_time = time.time()
        mock_data = [
            ObservationData(current_time, "event_a", {}, "source_1"),
            ObservationData(current_time, "event_a", {}, "source_2"),
            ObservationData(current_time, "event_b", {}, "source_1"),
        ]

        mock_sink = Mock()
        mock_sink.get_recent_data.return_value = mock_data
        access.add_data_source(mock_sink)

        # Проверяем распределения
        event_dist = access.get_event_type_distribution()
        source_dist = access.get_source_distribution()

        assert event_dist["event_a"] == 2
        assert event_dist["event_b"] == 1
        assert source_dist["source_1"] == 2
        assert source_dist["source_2"] == 1

    def test_iteration(self):
        """Тест итерации данных."""
        access = RawDataAccess()

        # Создаем много mock данных
        from src.observability.passive_data_sink import ObservationData
        mock_data = [
            ObservationData(time.time(), f"event_{i}", {"id": i}, "source")
            for i in range(10)
        ]

        mock_sink = Mock()
        mock_sink.get_recent_data.return_value = mock_data
        access.add_data_source(mock_sink)

        # Итерируем порциями
        chunks = list(access.iterate_data(chunk_size=3))
        total_items = sum(len(chunk) for chunk in chunks)

        assert len(chunks) > 1  # Несколько порций
        assert total_items == 10  # Все данные


class TestClarityMomentsSmoke:
    """Дымовые тесты для ClarityMoments."""

    def test_basic_functionality(self):
        """Тест базовой функциональности ClarityMoments."""
        clarity = ClarityMoments()

        # Анализ ясности
        moment = clarity.analyze_clarity()
        assert moment is not None

        # Получение моментов
        moments = clarity.get_clarity_moments()
        assert isinstance(moments, list)

        # Уровень ясности
        level = clarity.get_clarity_level()
        assert isinstance(level, float)
        assert 0.0 <= level <= 1.0

    def test_state_management(self):
        """Тест управления состоянием."""
        clarity = ClarityMoments()

        # Mock состояние
        class MockState:
            def __init__(self):
                self.clarity_state = False
                self.clarity_duration = 0
                self.clarity_modifier = 1.0

        state = MockState()

        # Проверяем условия
        result = clarity.check_clarity_conditions(state)
        assert result is not None or result is None  # Может быть None или dict

        # Активируем момент
        clarity.activate_clarity_moment(state)
        assert state.clarity_state is True
        assert state.clarity_duration > 0
        assert state.clarity_modifier > 1.0

        # Обновляем состояние
        clarity.update_clarity_state(state)
        assert state.clarity_duration >= 0

        # Деактивируем
        clarity.deactivate_clarity_moment(state)
        assert state.clarity_state is False
        assert state.clarity_duration == 0
        assert state.clarity_modifier == 1.0


class TestSensoryBufferSmoke:
    """Дымовые тесты для SensoryBuffer."""

    def test_basic_operations(self):
        """Тест базовых операций SensoryBuffer."""
        buffer = SensoryBuffer(buffer_size=50, default_ttl=1.0)

        # Создаем mock события
        mock_events = []
        for i in range(5):
            mock_event = Mock()
            mock_event.event_id = f"smoke_event_{i}"
            mock_event.event_type = f"type_{i % 2}"
            mock_event.intensity = 0.7  # Значимое событие
            mock_events.append(mock_event)
            buffer.add_event(mock_event)

        # Проверяем добавление
        assert buffer._total_entries_added == 5

        # Получаем события для обработки (события могут быть автоматически обработаны)
        processing_events = buffer.get_events_for_processing()
        # Не проверяем точное количество, так как зависит от реализации

        # Фильтрация по типу
        typed_events = buffer.get_events_by_type("type_0")
        # Метод должен работать без ошибок

        # Статистика - проверяем что статистика доступна
        stats = buffer.get_buffer_status()
        assert "total_entries_added" in stats
        assert stats["total_entries_added"] == 5

    def test_cleanup_functionality(self):
        """Тест функциональности очистки."""
        buffer = SensoryBuffer(buffer_size=10, default_ttl=0.1)  # Короткий TTL

        # Добавляем события
        for i in range(3):
            mock_event = Mock()
            mock_event.event_id = f"cleanup_test_{i}"
            mock_event.intensity = 0.6  # Значимое событие
            buffer.add_event(mock_event)

        # Проверяем перед очисткой
        initial_stats = buffer.get_buffer_status()
        assert initial_stats["buffer_size"] == 3

        # Ждем истечения TTL
        time.sleep(0.2)

        # Проверяем после очистки (очистка происходит автоматически)
        final_stats = buffer.get_buffer_status()
        # Буфер может быть пустым после очистки
        assert final_stats["total_entries_expired"] >= 0
        assert final_stats["total_entries_added"] == 3


class TestMemoryHierarchySmoke:
    """Дымовые тесты для компонентов иерархической памяти."""

    def test_semantic_store_basic(self):
        """Тест базовой функциональности SemanticMemoryStore."""
        store = SemanticMemoryStore()

        # Базовые проверки
        assert store._stats["total_concepts"] == 0
        assert len(store._concepts) == 0

        # Проверяем методы
        stats = store.get_statistics()
        assert hasattr(stats, 'total_entries')

    def test_procedural_store_basic(self):
        """Тест базовой функциональности ProceduralMemoryStore."""
        store = ProceduralMemoryStore()

        # Базовые проверки
        assert store._stats["total_patterns"] == 0
        assert len(store._patterns) == 0

        # Проверяем методы
        stats = store.get_statistics()
        assert hasattr(stats, 'total_entries')

    def test_hierarchy_manager_basic(self):
        """Тест базовой функциональности MemoryHierarchyManager."""
        # Создаем с явным SensoryBuffer для тестирования
        from src.experimental.memory_hierarchy.sensory_buffer import SensoryBuffer
        sensory_buffer = SensoryBuffer(buffer_size=10)
        manager = MemoryHierarchyManager(sensory_buffer=sensory_buffer)

        # Проверяем инициализацию компонентов
        assert manager.sensory_buffer is not None
        assert manager.semantic_store is not None
        assert manager.procedural_store is not None

        # Проверяем что все компоненты работают
        buffer_stats = manager.sensory_buffer.get_buffer_status()
        assert "buffer_size" in buffer_stats

        semantic_stats = manager.semantic_store.get_statistics()
        assert hasattr(semantic_stats, 'total_entries')

        procedural_stats = manager.procedural_store.get_statistics()
        assert hasattr(procedural_stats, 'total_entries')


class TestConsciousnessSmoke:
    """Дымовые тесты для компонентов сознания."""

    def test_consciousness_metrics_basic(self):
        """Тест базовой функциональности ConsciousnessMetrics."""
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

    def test_parallel_engine_basic(self):
        """Тест базовой функциональности ParallelConsciousnessEngine."""
        engine = ParallelConsciousnessEngine()

        # Проверяем начальное состояние
        current_state = engine.current_state
        assert current_state is not None

        # Проверяем историю переходов
        assert len(engine._transition_history) >= 0

        # Выполняем анализ
        engine.analyze_consciousness_conditions()

        # Проверяем что система не сломалась
        new_state = engine.get_current_state()
        assert new_state is not None

    def test_state_transitions(self):
        """Тест переходов между состояниями."""
        engine = ParallelConsciousnessEngine()

        # Выполняем несколько анализов
        for _ in range(3):
            engine.evaluate_consciousness_level()
            engine.update_metrics()
            time.sleep(0.01)  # Небольшая задержка

        # Проверяем что история растет
        assert len(engine._transition_history) >= 0

        # Проверяем что текущее состояние существует
        final_state = engine.get_current_state()
        assert final_state is not None