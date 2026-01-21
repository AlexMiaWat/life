"""
Smoke Tests for New Functionality.

Дымовые тесты проверяют базовую работоспособность компонентов:
- Создание экземпляров классов
- Базовые операции без ошибок
- Корректные возвращаемые значения
- Отсутствие исключений при нормальном использовании
"""

import pytest
import time
from unittest.mock import Mock, MagicMock

# Настройка путей
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.experimental.adaptive_processing_manager import (
    AdaptiveProcessingManager,
    ProcessingMode,
    AdaptiveState,
    ProcessingEvent,
    AdaptiveProcessingConfig,
)
from src.experimental.memory_hierarchy.hierarchy_manager import MemoryHierarchyManager
from src.experimental.memory_hierarchy.semantic_store import SemanticConcept, SemanticMemoryStore
from src.experimental.memory_hierarchy.procedural_store import ProceduralMemoryStore
from src.experimental.memory_hierarchy.sensory_buffer import SensoryBuffer
from src.experimental.consciousness.parallel_engine import (
    ParallelConsciousnessEngine,
    ProcessingMode as ConsciousnessProcessingMode,
    ProcessingResult,
)
from src.environment.event import Event
from src.observability.structured_logger import StructuredLogger


class TestAdaptiveProcessingManagerSmoke:
    """Дымовые тесты AdaptiveProcessingManager."""

    def test_manager_creation(self):
        """Тест создания экземпляра AdaptiveProcessingManager."""
        # Создаем мок для self_state_provider
        mock_self_state = Mock()
        mock_self_state.stability = 0.8
        mock_self_state.energy = 0.7
        mock_self_state.processing_efficiency = 0.6

        def mock_provider():
            return mock_self_state

        # Создание менеджера без интеграции памяти
        config = AdaptiveProcessingConfig(integrate_with_memory=False)
        manager = AdaptiveProcessingManager(mock_provider, config=config)

        # Проверки
        assert manager is not None
        assert manager._is_active is False
        assert isinstance(manager.config, AdaptiveProcessingConfig)
        assert manager._memory_hierarchy is None  # Интеграция отключена

    def test_manager_start_stop(self):
        """Тест запуска и остановки менеджера."""
        mock_self_state = Mock()
        manager = AdaptiveProcessingManager(lambda: mock_self_state)

        # Запуск
        manager.start()
        assert manager._is_active is True

        # Остановка
        manager.stop()
        assert manager._is_active is False

    def test_manager_update_cycle(self):
        """Тест цикла обновления менеджера."""
        mock_self_state = Mock()
        mock_self_state.stability = 0.8
        mock_self_state.energy = 0.7
        mock_self_state.processing_efficiency = 0.6
        mock_self_state.cognitive_load = 0.3

        manager = AdaptiveProcessingManager(lambda: mock_self_state)

        # Запуск менеджера
        manager.start()

        # Выполнение обновления
        result = manager.update(mock_self_state)

        # Проверки
        assert isinstance(result, dict)
        assert "status" in result
        assert result["status"] == "updated"
        assert "processing_events" in result
        assert "state_transitions" in result
        assert "memory_operations" in result
        assert "timestamp" in result

        manager.stop()

    def test_processing_event_triggering(self):
        """Тест ручного вызова режима обработки."""
        mock_self_state = Mock()
        # Добавим необходимые атрибуты для предотвращения исключений
        mock_self_state.processing_history = []
        mock_self_state.processing_efficiency = 0.5
        mock_self_state.cognitive_load = 0.5

        manager = AdaptiveProcessingManager(lambda: mock_self_state)

        # Вызов режима обработки (должен выполниться без исключений)
        try:
            result = manager.trigger_processing_event(
                mock_self_state,
                ProcessingMode.EFFICIENT,
                intensity=0.8
            )
            # Если дошли сюда, метод выполнился
            assert True
        except Exception as e:
            # Если было исключение, тест провалился
            pytest.fail(f"trigger_processing_event raised exception: {e}")

        # Проверка что состояние обновлено (если результат True)
        if result:
            assert mock_self_state.processing_mode == "efficient"
            assert mock_self_state.processing_intensity == 0.8

    def test_adaptive_state_forcing(self):
        """Тест принудительного перехода в адаптивное состояние."""
        mock_self_state = Mock()
        manager = AdaptiveProcessingManager(lambda: mock_self_state)

        # Принудительный переход состояния
        result = manager.force_adaptive_state(mock_self_state, AdaptiveState.OPTIMAL_PROCESSING)

        # Проверка успешного перехода
        assert result is True
        assert mock_self_state.current_adaptive_state == "optimal_processing"

    def test_system_status_retrieval(self):
        """Тест получения статуса системы."""
        mock_self_state = Mock()
        manager = AdaptiveProcessingManager(lambda: mock_self_state)

        status = manager.get_system_status()

        # Проверка структуры статуса
        assert isinstance(status, dict)
        assert "manager" in status
        assert "components" in status
        assert "is_active" in status["manager"]
        assert "stats" in status["manager"]
        assert "uptime" in status["manager"]

    def test_statistics_methods(self):
        """Тест методов получения статистики."""
        mock_self_state = Mock()
        manager = AdaptiveProcessingManager(lambda: mock_self_state)

        # Статистика обработки
        processing_stats = manager.get_processing_statistics()
        assert isinstance(processing_stats, dict)
        assert "total_processing_events" in processing_stats
        assert "active_processing" in processing_stats

        # Адаптивная статистика
        adaptive_stats = manager.get_adaptive_statistics()
        assert isinstance(adaptive_stats, dict)
        assert "total_state_transitions" in adaptive_stats
        assert "current_state" in adaptive_stats

    def test_configuration_update(self):
        """Тест обновления конфигурации."""
        mock_self_state = Mock()
        manager = AdaptiveProcessingManager(lambda: mock_self_state)

        # Обновление конфигурации
        new_config = {
            "stability_threshold": 0.9,
            "energy_threshold": 0.8,
            "enable_efficient_processing": False
        }

        # Это не должно вызвать исключение
        manager.update_configuration(new_config)

        # Проверка что конфигурация обновлена
        assert manager.config.stability_threshold == 0.9
        assert manager.config.energy_threshold == 0.8
        assert manager.config.enable_efficient_processing is False


class TestMemoryHierarchyManagerSmoke:
    """Дымовые тесты MemoryHierarchyManager."""

    def test_hierarchy_creation(self):
        """Тест создания иерархии памяти."""
        manager = MemoryHierarchyManager()

        assert manager is not None
        assert isinstance(manager.sensory_buffer, SensoryBuffer)
        assert manager.episodic_memory is None  # Не установлена
        assert isinstance(manager.semantic_store, SemanticMemoryStore)
        assert isinstance(manager.procedural_store, ProceduralMemoryStore)

    def test_sensory_event_handling(self):
        """Тест обработки сенсорных событий."""
        manager = MemoryHierarchyManager()

        # Создание тестового события
        event = Event(
            type="test_event",
            timestamp=time.time(),
            intensity=0.7,
            metadata={"test": "data"}
        )

        # Добавление события
        manager.add_sensory_event(event)

        # Проверка что событие добавлено
        events = manager.process_sensory_events(max_events=10)
        assert len(events) > 0

    def test_episodic_memory_integration(self):
        """Тест интеграции с эпизодической памятью."""
        manager = MemoryHierarchyManager()

        # Мок эпизодической памяти
        mock_memory = Mock()
        mock_memory.append = Mock()
        mock_memory.__len__ = Mock(return_value=0)

        # Установка эпизодической памяти
        manager.set_episodic_memory(mock_memory)

        assert manager.episodic_memory is mock_memory

    def test_memory_consolidation(self):
        """Тест консолидации памяти."""
        manager = MemoryHierarchyManager()

        # Мок self_state
        mock_self_state = Mock()
        mock_self_state.memory = []

        # Выполнение консолидации
        stats = manager.consolidate_memory(mock_self_state)

        # Проверка структуры результата
        assert isinstance(stats, dict)
        assert "sensory_to_episodic_transfers" in stats
        assert "episodic_to_semantic_transfers" in stats
        assert "semantic_consolidations" in stats
        assert "timestamp" in stats

    def test_hierarchy_status(self):
        """Тест получения статуса иерархии."""
        manager = MemoryHierarchyManager()

        status = manager.get_hierarchy_status()

        # Проверка структуры статуса
        assert isinstance(status, dict)
        assert "hierarchy_manager" in status
        assert "sensory_buffer" in status
        assert "episodic_memory" in status
        assert "semantic_store" in status
        assert "procedural_store" in status

    def test_memory_query(self):
        """Тест запросов к памяти."""
        manager = MemoryHierarchyManager()

        # Запрос к сенсорному буферу
        sensory_result = manager.query_memory("sensory", max_events=5)
        assert isinstance(sensory_result, list)

        # Запрос к семантической памяти
        semantic_result = manager.query_memory("semantic", query="test")
        assert isinstance(semantic_result, list)

        # Запрос к процедурной памяти
        procedural_result = manager.query_memory("procedural", context={})
        assert isinstance(procedural_result, list)

    def test_hierarchy_reset(self):
        """Тест сброса иерархии."""
        manager = MemoryHierarchyManager()

        # Добавление события перед сбросом
        event = Event(type="test", timestamp=time.time(), intensity=0.5)
        manager.add_sensory_event(event)

        # Сброс
        manager.reset_hierarchy()

        # Проверка что буфер очищен
        events = manager.process_sensory_events()
        assert len(events) == 0


class TestSemanticStoreSmoke:
    """Дымовые тесты SemanticMemoryStore."""

    def test_semantic_concept_creation(self):
        """Тест создания семантической концепции."""
        concept = SemanticConcept(
            concept_id="test_concept",
            name="Test Concept",
            description="A test semantic concept",
            confidence=0.85
        )

        assert concept.concept_id == "test_concept"
        assert concept.name == "Test Concept"
        assert concept.confidence == 0.85
        assert concept.activation_count == 0

    def test_concept_activation(self):
        """Тест активации концепции."""
        concept = SemanticConcept(
            concept_id="test",
            name="Test",
            description="Test",
            confidence=0.8
        )

        initial_count = concept.activation_count
        initial_time = concept.last_activation

        # Небольшая задержка для проверки обновления времени
        time.sleep(0.001)

        concept.activate()

        assert concept.activation_count == initial_count + 1
        assert concept.last_activation > initial_time

    def test_concept_relations(self):
        """Тест связей концепций."""
        concept1 = SemanticConcept("c1", "Concept 1", "Desc 1", 0.8)
        concept2 = SemanticConcept("c2", "Concept 2", "Desc 2", 0.7)

        # Добавление связи
        concept1.add_relation("c2")

        assert "c2" in concept1.related_concepts
        assert len(concept1.related_concepts) == 1

    def test_activation_strength(self):
        """Тест силы активации."""
        concept = SemanticConcept("test", "Test", "Test", 0.8)

        # Активация
        concept.activate()

        # Получение силы активации
        strength = concept.get_activation_strength(time.time())

        assert isinstance(strength, float)
        assert strength >= 0.0

    def test_semantic_store_operations(self):
        """Тест операций семантического хранилища."""
        store = SemanticMemoryStore()

        # Создание концепции
        concept = SemanticConcept("test", "Test Concept", "Description", 0.8)

        # Добавление концепции
        store.add_concept(concept)

        # Поиск концепций
        results = store.search_concepts("test")
        assert len(results) > 0

        # Консолидация знаний
        consolidations = store.consolidate_knowledge()
        assert isinstance(consolidations, int)
        assert consolidations >= 0


class TestParallelConsciousnessEngineSmoke:
    """Дымовые тесты ParallelConsciousnessEngine."""

    def test_engine_creation(self):
        """Тест создания движка сознания."""
        engine = ParallelConsciousnessEngine()

        assert engine is not None
        assert engine.max_workers == 4  # дефолтное значение
        assert engine.mode == ConsciousnessProcessingMode.THREADING

    def test_sync_processing(self):
        """Тест синхронной обработки."""
        engine = ParallelConsciousnessEngine()

        # Создание тестовых задач
        tasks = [
            {"id": "task1", "operation": "analyze", "data": {"input": "test1"}},
            {"id": "task2", "operation": "transform", "data": {"input": "test2"}},
        ]

        # Синхронная обработка
        results = engine.process_sync(tasks)

        # Проверки
        assert isinstance(results, list)
        assert len(results) == 2

        for result in results:
            assert isinstance(result, ProcessingResult)
            assert result.success is True
            assert isinstance(result.processing_time, float)
            assert result.processing_time >= 0

    @pytest.mark.asyncio
    async def test_async_processing(self):
        """Тест асинхронной обработки."""
        engine = ParallelConsciousnessEngine()

        # Создание тестовых задач
        tasks = [
            {"id": "task1", "operation": "analyze", "data": {"input": "test1"}},
            {"id": "task2", "operation": "transform", "data": {"input": "test2"}},
        ]

        # Асинхронная обработка
        results = await engine.process_async(tasks)

        # Проверки
        assert isinstance(results, list)
        assert len(results) == 2

        for result in results:
            assert isinstance(result, ProcessingResult)
            assert result.success is True
            assert isinstance(result.processing_time, float)

    def test_engine_shutdown(self):
        """Тест завершения работы движка."""
        engine = ParallelConsciousnessEngine()

        # Завершение работы (не должно вызвать исключение)
        engine.shutdown()

        # Повторное завершение тоже не должно вызвать исключение
        engine.shutdown()


class TestSensoryBufferSmoke:
    """Дымовые тесты SensoryBuffer."""

    def test_buffer_creation(self):
        """Тест создания сенсорного буфера."""
        buffer = SensoryBuffer()

        assert buffer is not None
        assert hasattr(buffer, 'buffer_size')
        assert hasattr(buffer, 'add_event')
        assert hasattr(buffer, 'get_events_for_processing')
        assert hasattr(buffer, 'peek_events')

    def test_event_buffering(self):
        """Тест буферизации событий."""
        buffer = SensoryBuffer()

        # Создание события
        event = Event(
            type="test_event",
            timestamp=time.time(),
            intensity=0.6,
            metadata={"test": True}
        )

        # Добавление события
        buffer.add_event(event)

        # Извлечение событий
        events = buffer.get_events_for_processing(max_events=5)

        assert len(events) == 1
        assert events[0].type == "test_event"

    def test_buffer_status(self):
        """Тест получения статуса буфера."""
        buffer = SensoryBuffer()

        status = buffer.get_buffer_status()

        assert isinstance(status, dict)
        assert "buffer_size" in status
        assert "buffer_capacity" in status
        assert "utilization_percent" in status


class TestProceduralStoreSmoke:
    """Дымовые тесты ProceduralMemoryStore."""

    def test_procedural_store_creation(self):
        """Тест создания процедурного хранилища."""
        store = ProceduralMemoryStore()

        assert store is not None
        assert hasattr(store, 'add_pattern')
        assert hasattr(store, 'find_applicable_patterns')
        assert hasattr(store, 'learn_from_experience')

    def test_pattern_operations(self):
        """Тест операций с паттернами."""
        from src.experimental.memory_hierarchy.procedural_store import ProceduralPattern

        store = ProceduralMemoryStore()

        # Создание паттерна
        pattern = ProceduralPattern(
            pattern_id="test_pattern",
            name="Test Pattern",
            description="A test procedural pattern",
            trigger_conditions={"situation": "test"}
        )

        # Добавление паттерна
        store.add_pattern(pattern)

        # Поиск паттернов
        applicable = store.find_applicable_patterns({"situation": "test"})

        assert len(applicable) > 0

    def test_pattern_learning(self):
        """Тест обучения паттернов."""
        store = ProceduralMemoryStore()

        # Обучение из опыта (не должно вызвать исключение)
        store.learn_from_experience(
            context={"situation": "test"},
            actions=[("test_action", {})],
            outcome="success",
            success=True
        )


if __name__ == "__main__":
    pytest.main([__file__])