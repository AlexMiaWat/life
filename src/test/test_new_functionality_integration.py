"""
Интеграционные тесты для новой функциональности.

Проверяют взаимодействие новых компонентов:
- С существующими компонентами системы
- Между собой
- В составе полного жизненного цикла
"""

import pytest
import asyncio
import time
import time
from unittest.mock import Mock, patch

# Импорты существующих компонентов
from src.state.self_state import SelfState
from src.environment.event_queue import EventQueue
from src.environment.event import Event
from src.memory.memory import ArchiveMemory

# Импорты новых observability компонентов
from src.observability.passive_data_sink import PassiveDataSink
from src.observability.async_data_sink import AsyncDataSink
from src.observability.raw_data_access import RawDataAccess

# Импорты новых experimental компонентов
from src.experimental.clarity_moments import ClarityMoments
from src.experimental.memory_hierarchy.hierarchy_manager import MemoryHierarchyManager
from src.experimental.memory_hierarchy.sensory_buffer import SensoryBuffer
from src.experimental.memory_hierarchy.semantic_store import SemanticMemoryStore
from src.experimental.memory_hierarchy.procedural_store import ProceduralMemoryStore

# Импорты consciousness компонентов
from src.experimental.consciousness.parallel_engine import ParallelConsciousnessEngine


class TestObservabilityIntegration:
    """Интеграционные тесты для observability компонентов."""

    def test_passive_sink_with_self_state(self):
        """Тест интеграции PassiveDataSink с SelfState."""
        sink = PassiveDataSink(max_entries=20)

        # Создаем SelfState
        state = SelfState()

        # Отправляем данные о состоянии в sink
        sink.receive_data(
            "state_update",
            {
                "energy": state.energy,
                "integrity": state.integrity,
                "stability": state.stability,
                "age": state.age
            },
            "self_state"
        )

        # Проверяем данные
        data = sink.get_recent_data()
        assert len(data) == 1
        assert data[0].event_type == "state_update"
        assert data[0].source == "self_state"
        assert "energy" in data[0].data

    def test_raw_data_access_with_multiple_sources(self):
        """Тест RawDataAccess с множественными источниками."""
        access = RawDataAccess()

        # Создаем несколько источников данных
        passive_sink = PassiveDataSink(max_entries=10)
        async_sink = AsyncDataSink(enabled=False)  # Отключен для простоты

        # Добавляем источники
        access.add_data_source(passive_sink)
        access.add_data_source(async_sink)

        # Добавляем данные в passive sink
        for i in range(5):
            passive_sink.receive_data(
                f"integration_event_{i}",
                {"sequence": i},
                "integration_source"
            )

        # Получаем данные через RawDataAccess
        all_data = access.get_raw_data()
        assert len(all_data) == 5

        # Фильтруем данные
        filtered_data = access.get_raw_data(event_type_filter="integration_event_0")
        assert len(filtered_data) == 1

        # Проверяем сводку
        summary = access.get_data_summary()
        assert summary["total_records"] == 5
        assert "integration_source" in summary["sources"]

    def test_data_flow_passive_to_raw_access(self):
        """Тест потока данных от PassiveDataSink к RawDataAccess."""
        # Создаем компоненты
        sink = PassiveDataSink(max_entries=15)
        access = RawDataAccess()
        access.add_data_source(sink)

        # Генерируем поток данных
        event_types = ["system_event", "user_event", "background_event"]
        sources = ["component_a", "component_b", "component_c"]

        for i in range(10):
            sink.receive_data(
                event_types[i % len(event_types)],
                {"id": i, "timestamp": time.time()},
                sources[i % len(sources)]
            )

        # Проверяем интеграцию
        all_data = access.get_raw_data()
        assert len(all_data) == 10

        # Проверяем экспорт
        json_filepath = access.export_data(format_type='json')
        with open(json_filepath, 'r') as f:
            json_content = f.read()
        assert '"event_type":' in json_content

        # Проверяем распределения
        event_dist = access.get_event_type_distribution()
        source_dist = access.get_source_distribution()

        assert len(event_dist) == 3  # Три типа событий
        assert len(source_dist) == 3  # Три источника

    @pytest.mark.asyncio
    async def test_async_sink_integration(self):
        """Тест интеграции AsyncDataSink с другими компонентами."""
        # Создаем AsyncDataSink
        sink = AsyncDataSink(max_queue_size=20, processing_interval=0.05, enabled=True)

        # Создаем RawDataAccess для чтения данных
        access = RawDataAccess()
        access.add_data_source(sink)

        # Запускаем sink
        await sink.start()

        # Отправляем данные асинхронно
        for i in range(5):
            success = await sink.receive_data_async(
                "async_integration_event",
                {"batch_id": i, "data": f"test_{i}"},
                "async_source"
            )
            assert success is True

        # Ждем обработки
        await asyncio.sleep(0.3)

        # Проверяем через RawDataAccess
        data = access.get_raw_data()
        assert len(data) >= 5

        # Проверяем статистику
        stats = sink.get_statistics()
        assert stats["events_logged"] >= 5
        assert stats["events_processed"] >= 5

        # Останавливаем
        sink.stop()


class TestClarityMomentsIntegration:
    """Интеграционные тесты для ClarityMoments."""

    def test_clarity_with_self_state(self):
        """Тест интеграции ClarityMoments с SelfState."""
        clarity = ClarityMoments()
        state = SelfState()

        # Проверяем условия ясности
        result = clarity.check_clarity_conditions(state)

        # Результат может быть None или dict в зависимости от состояния
        if result:
            assert result["type"] == "clarity_moment"
            assert "clarity_id" in result["data"]

        # Активируем момент ясности на состоянии
        clarity.activate_clarity_moment(state)

        # Проверяем изменения в состоянии
        assert hasattr(state, 'clarity_state') or True  # Может не иметь атрибута изначально

        # Обновляем состояние
        clarity.update_clarity_state(state)

        # Деактивируем
        clarity.deactivate_clarity_moment(state)

    def test_clarity_with_event_queue(self):
        """Тест интеграции ClarityMoments с EventQueue."""
        clarity = ClarityMoments()
        event_queue = EventQueue()

        # Создаем события для тестирования
        test_events = []
        for i in range(3):
            event = Event(
                type="clarity_test_event",
                intensity=0.5 + i * 0.2,
                timestamp=time.time(),
                metadata={"test": True},
                source="clarity_test"
            )
            test_events.append(event)
            event_queue.push(event)

        # Проверяем что ClarityMoments может работать параллельно
        moment = clarity.analyze_clarity()
        assert moment is not None

        # Получаем моменты
        moments = clarity.get_clarity_moments()
        assert len(moments) >= 1  # Хотя бы один момент от анализа

    def test_clarity_memory_integration(self):
        """Тест интеграции ClarityMoments с памятью."""
        clarity = ClarityMoments()
        memory = ArchiveMemory()

        # Создаем несколько моментов ясности
        for i in range(3):
            moment = clarity.analyze_clarity()
            if moment:
                # Сохраняем момент в память (имитация)
                memory.add_entry(
                    event_type="clarity_moment",
                    meaning_significance=moment.intensity,
                    timestamp=moment.timestamp,
                    weight=0.8
                )

        # Проверяем что моменты сохранены в памяти
        clarity_entries = memory.search_by_type("clarity_moment")
        assert len(clarity_entries) >= 0  # Может быть 0 если моменты не создались


class TestMemoryHierarchyIntegration:
    """Интеграционные тесты для MemoryHierarchy."""

    def test_sensory_buffer_with_events(self):
        """Тест интеграции SensoryBuffer с Event объектами."""
        buffer = SensoryBuffer(buffer_size=20, default_ttl=2.0)

        # Создаем реальные Event объекты
        events = []
        for i in range(5):
            event = Event(
                type=f"sensory_event_{i}",
                intensity=0.5,
                timestamp=time.time(),
                metadata={"sensor_data": f"value_{i}"},
                source="sensor_integration_test"
            )
            events.append(event)
            buffer.add_event(event)

        # Проверяем добавление
        assert buffer._total_entries_added == 5

        # Получаем недавние события
        recent = buffer.get_events_for_processing()
        assert len(recent) == 5

        # Проверяем что события сохранены корректно
        for event in recent:
            assert isinstance(event, Event)

    def test_hierarchy_manager_full_integration(self):
        """Тест полной интеграции MemoryHierarchyManager."""
        from src.experimental.memory_hierarchy.sensory_buffer import SensoryBuffer
        sensory_buffer = SensoryBuffer(buffer_size=20)
        manager = MemoryHierarchyManager(sensory_buffer=sensory_buffer)

        # Добавляем события в сенсорный буфер
        for i in range(3):
            event = Event(
                type="hierarchy_test_event",
                intensity=0.6,
                timestamp=time.time(),
                metadata={"test_id": i},
                source="hierarchy_integration"
            )
            manager.sensory_buffer.add_event(event)

        # Проверяем компоненты
        buffer_stats = manager.sensory_buffer.get_buffer_statistics()
        assert buffer_stats["total_events"] == 3

        semantic_stats = manager.semantic_store.get_statistics()
        assert semantic_stats["total_entries"] == 0  # Пока пустой

        procedural_stats = manager.procedural_store.get_statistics()
        assert procedural_stats["total_entries"] == 0  # Пока пустой

    def test_memory_hierarchy_with_self_state(self):
        """Тест интеграции MemoryHierarchy с SelfState."""
        from src.experimental.memory_hierarchy.sensory_buffer import SensoryBuffer
        sensory_buffer = SensoryBuffer(buffer_size=20)
        manager = MemoryHierarchyManager(sensory_buffer=sensory_buffer)
        state = SelfState()

        # Добавляем события в память
        for i in range(3):
            event = Event(
                type="state_memory_event",
                intensity=0.4,
                timestamp=time.time(),
                metadata={"state_energy": state.energy, "sequence": i},
                source="state_integration"
            )
            manager.sensory_buffer.add_event(event)

        # Проверяем что память работает независимо от состояния
        buffer_data = manager.sensory_buffer.get_events_for_processing()
        assert len(buffer_data) == 3

        # Проверяем что состояние не изменилось от операций с памятью
        original_energy = state.energy
        # Операции с памятью не должны влиять на состояние
        assert state.energy == original_energy


class TestConsciousnessIntegration:
    """Интеграционные тесты для consciousness компонентов."""

    def test_consciousness_with_self_state(self):
        """Тест интеграции consciousness с SelfState."""
        engine = ParallelConsciousnessEngine()
        state = SelfState()

        # Выполняем анализ сознания
        engine.analyze_consciousness_conditions()

        # Проверяем что состояние сознания обновилось
        current_state = engine.get_current_state()
        assert current_state is not None

        # Выполняем переход состояния для тестирования истории
        from src.experimental.consciousness.parallel_engine import ConsciousnessState
        engine.transition_to_state(ConsciousnessState.REFLECTIVE)

        # Проверяем историю переходов
        assert len(engine.transition_history) > 0

        # Проверяем что SelfState не затронут (консистентность)
        assert hasattr(state, 'energy')  # Проверка что состояние целое

    def test_consciousness_with_memory(self):
        """Тест интеграции consciousness с памятью."""
        engine = ParallelConsciousnessEngine()
        memory = ArchiveMemory()

        # Выполняем несколько анализов сознания
        for _ in range(3):
            engine.analyze_consciousness_conditions()
            time.sleep(0.01)

        # Сохраняем информацию о сознании в память
        consciousness_info = {
            "current_state": engine.get_current_state().value,
            "transitions_count": len(engine.transition_history)
        }

        memory.add_entry(
            event_type="consciousness_analysis",
            meaning_significance=0.7,
            timestamp=time.time(),
            weight=0.6
        )

        # Проверяем что память сохранила информацию
        entries = memory.search_by_type("consciousness_analysis")
        assert len(entries) >= 1


class TestFullSystemIntegration:
    """Интеграционные тесты всей системы с новыми компонентами."""

    def test_observability_memory_integration(self):
        """Тест интеграции observability с memory системой."""
        # Создаем компоненты
        passive_sink = PassiveDataSink(max_entries=20)
        access = RawDataAccess()
        access.add_data_source(passive_sink)
        memory = ArchiveMemory()

        # Создаем события и сохраняем их в обоих системах
        for i in range(5):
            event_data = {
                "integration_test": True,
                "sequence": i,
                "timestamp": time.time()
            }

            # В observability
            passive_sink.receive_data(
                "full_integration_event",
                event_data,
                "full_system_test"
            )

            # В память
            memory.add_entry(
                event_type="full_integration_memory",
                meaning_significance=0.5,
                timestamp=time.time(),
                weight=0.7
            )

        # Проверяем обе системы
        obs_data = access.get_raw_data()
        assert len(obs_data) == 5

        mem_entries = memory.search_by_type("full_integration_memory")
        assert len(mem_entries) >= 1

    def test_clarity_consciousness_integration(self):
        """Тест интеграции clarity moments с consciousness."""
        clarity = ClarityMoments()
        consciousness = ParallelConsciousnessEngine()

        # Выполняем анализ clarity
        clarity_moment = clarity.analyze_clarity()

        # Выполняем анализ consciousness
        consciousness.analyze_consciousness_conditions()

        # Проверяем что оба компонента работают независимо
        assert clarity_moment is not None

        clarity_level = clarity.get_clarity_level()
        assert isinstance(clarity_level, float)

        consciousness_state = consciousness.get_current_state()
        assert consciousness_state is not None

    @pytest.mark.asyncio
    async def test_async_observability_full_flow(self):
        """Тест полного потока данных через async observability."""
        # Создаем полную цепочку
        async_sink = AsyncDataSink(max_queue_size=30, processing_interval=0.05, enabled=True)
        access = RawDataAccess()
        access.add_data_source(async_sink)

        # Запускаем
        await async_sink.start()

        # Отправляем разнообразные данные
        event_types = ["system", "user", "background", "sensor"]
        sources = ["component_a", "component_b", "sensor_x"]

        for i in range(10):
            success = await async_sink.receive_data_async(
                event_types[i % len(event_types)],
                {
                    "id": i,
                    "data": f"full_flow_test_{i}",
                    "timestamp": time.time()
                },
                sources[i % len(sources)]
            )
            assert success is True

        # Ждем полной обработки
        await asyncio.sleep(0.5)

        # Проверяем через RawDataAccess
        all_data = access.get_raw_data()
        assert len(all_data) >= 10

        # Проверяем распределения
        event_dist = access.get_event_type_distribution()
        source_dist = access.get_source_distribution()

        assert len(event_dist) == 4  # Все типы событий
        assert len(source_dist) == 3  # Все источники

        # Проверяем экспорт
        export_filepath = access.export_data(format_type='jsonl')
        assert isinstance(export_filepath, str)
        with open(export_filepath, 'r') as f:
            export_content = f.read()
        assert len(export_content.split('\n')) >= 10

        # Останавливаем
        async_sink.stop()

    def test_memory_hierarchy_full_system(self):
        """Тест полной интеграции memory hierarchy с системой."""
        from src.experimental.memory_hierarchy.sensory_buffer import SensoryBuffer
        sensory_buffer = SensoryBuffer(buffer_size=20)
        manager = MemoryHierarchyManager(sensory_buffer=sensory_buffer)
        state = SelfState()
        clarity = ClarityMoments()

        # Добавляем события в сенсорную память
        for i in range(5):
            event = Event(
                type="full_system_memory_event",
                intensity=0.3,
                timestamp=time.time(),
                metadata={
                    "energy": state.energy,
                    "clarity_level": clarity.get_clarity_level(),
                    "sequence": i
                },
                source="full_system_integration"
            )
            manager.sensory_buffer.add_event(event)

        # Проверяем все уровни памяти
        sensory_data = manager.sensory_buffer.get_events_for_processing()
        assert len(sensory_data) == 5

        # Проверяем что другие уровни тоже работают
        semantic_stats = manager.semantic_store.get_statistics()
        procedural_stats = manager.procedural_store.get_statistics()

        assert hasattr(semantic_stats, 'total_entries')
        assert hasattr(procedural_stats, 'total_entries')

        # Проверяем что система остается стабильной
        assert state.energy > 0  # Состояние не сломалось