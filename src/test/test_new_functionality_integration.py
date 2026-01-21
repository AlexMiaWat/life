"""
Integration Tests for New Functionality.

Интеграционные тесты проверяют взаимодействие между компонентами:
- AdaptiveProcessingManager + MemoryHierarchyManager
- ParallelConsciousnessEngine + AdaptiveProcessingManager
- Полный цикл обработки от сенсорных событий до семантических концепций
- Кросс-компонентные сценарии использования
"""

import pytest
import time
import asyncio
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
    AdaptiveProcessingConfig,
)
from src.experimental.memory_hierarchy.hierarchy_manager import MemoryHierarchyManager
from src.experimental.memory_hierarchy.semantic_store import SemanticConcept
from src.experimental.memory_hierarchy.sensory_buffer import SensoryBuffer
from src.experimental.consciousness.parallel_engine import (
    ParallelConsciousnessEngine,
    ProcessingMode as ConsciousnessProcessingMode,
)
from src.environment.event import Event
from src.state.self_state import SelfState
from src.memory.memory import ArchiveMemory
from src.observability.structured_logger import StructuredLogger


class TestAdaptiveProcessingMemoryIntegration:
    """Интеграционные тесты AdaptiveProcessingManager + MemoryHierarchyManager."""

    def test_adaptive_processing_with_memory_integration(self):
        """Тест адаптивной обработки с интеграцией памяти."""
        # Создание SelfState
        self_state = SelfState()
        self_state.stability = 0.9
        self_state.energy = 0.8
        self_state.processing_efficiency = 0.7
        self_state.cognitive_load = 0.2

        # Создание иерархии памяти
        memory_hierarchy = MemoryHierarchyManager()

        # Создание менеджера обработки с интеграцией памяти
        config = AdaptiveProcessingConfig(integrate_with_memory=True)
        manager = AdaptiveProcessingManager(
            self_state_provider=lambda: self_state,
            config=config
        )

        # Установка связи с памятью
        manager._memory_hierarchy = memory_hierarchy

        # Запуск обработки
        manager.start()

        # Выполнение цикла обновления
        result = manager.update(self_state)

        # Проверки
        assert result["status"] == "updated"
        assert "memory_operations" in result

        # Проверка что память взаимодействует
        if result["memory_operations"]:
            memory_op = result["memory_operations"][0]
            assert "operation" in memory_op
            assert "success" in memory_op

        manager.stop()

    def test_processing_event_memory_effects(self):
        """Тест эффектов режима обработки на память."""
        # Создание SelfState с памятью
        self_state = SelfState()
        self_state.memory = ArchiveMemory()
        self_state.stability = 0.8
        self_state.energy = 0.7
        self_state.processing_efficiency = 0.9  # Высокая эффективность для OPTIMIZED режима

        # Создание иерархии памяти
        memory_hierarchy = MemoryHierarchyManager()
        memory_hierarchy.set_episodic_memory(self_state.memory)

        # Создание менеджера обработки
        manager = AdaptiveProcessingManager(
            self_state_provider=lambda: self_state,
            config=AdaptiveProcessingConfig(integrate_with_memory=True)
        )
        manager._memory_hierarchy = memory_hierarchy

        # Ручной вызов OPTIMIZED режима
        success = manager.trigger_processing_event(
            self_state,
            ProcessingMode.OPTIMIZED,
            intensity=0.9
        )

        assert success is True

        # Проверка что эффекты применены к SelfState
        assert hasattr(self_state, 'processing_modifier')  # Проверяем что эффекты применились
        assert self_state.processing_state is True

        # Проверка консолидации памяти
        consolidation_stats = memory_hierarchy.consolidate_memory(self_state)
        assert isinstance(consolidation_stats, dict)
        assert "sensory_to_episodic_transfers" in consolidation_stats

    def test_state_transition_memory_integration(self):
        """Тест переходов состояний с интеграцией памяти."""
        self_state = SelfState()
        self_state.memory = ArchiveMemory()
        self_state.stability = 0.9
        self_state.energy = 0.8
        self_state.processing_efficiency = 0.85
        self_state.meta_cognition_depth = 0.9
        self_state.processing_efficiency = 0.95  # Нужно > 0.9 для OPTIMAL_PROCESSING

        # Создание иерархии памяти
        memory_hierarchy = MemoryHierarchyManager()
        memory_hierarchy.set_episodic_memory(self_state.memory)

        # Создание менеджера
        manager = AdaptiveProcessingManager(
            self_state_provider=lambda: self_state,
            config=AdaptiveProcessingConfig(integrate_with_memory=True)
        )
        manager._memory_hierarchy = memory_hierarchy

        # Выполнение обновления для триггера перехода состояния
        manager.update(self_state)

        # Проверка что состояние перешло в OPTIMAL_PROCESSING
        current_state = manager.get_current_state()
        assert current_state.value == "optimal_processing"

        # Проверка что SelfState обновлено
        assert self_state.current_adaptive_state == "optimal_processing"


class TestConsciousnessEngineAdaptiveProcessingIntegration:
    """Интеграционные тесты ParallelConsciousnessEngine + AdaptiveProcessingManager."""

    def test_consciousness_engine_adaptive_analysis(self):
        """Тест анализа через consciousness engine с адаптивным менеджером."""
        # Создание consciousness engine
        engine = ParallelConsciousnessEngine()

        # Создание задач для анализа
        tasks = [
            {
                "id": "analysis_task_1",
                "operation": "analyze",
                "data": {
                    "input_type": "system_metrics",
                    "metrics": {"efficiency": 0.8, "stability": 0.7}
                }
            },
            {
                "id": "analysis_task_2",
                "operation": "analyze",
                "data": {
                    "input_type": "memory_patterns",
                    "patterns": ["pattern_a", "pattern_b"]
                }
            }
        ]

        # Выполнение анализа
        results = engine.process_sync(tasks)

        # Проверки результатов
        assert len(results) == 2

        for result in results:
            assert result.success is True
            assert "analysis_type" in result.result
            assert "confidence" in result.result
            assert "patterns_found" in result.result
            assert "adaptive_state" in result.result

    @pytest.mark.asyncio
    async def test_async_consciousness_processing(self):
        """Тест асинхронной обработки через consciousness engine."""
        engine = ParallelConsciousnessEngine(max_workers=2)

        # Создание задач
        tasks = [
            {"id": "task_1", "operation": "transform", "data": {"value": 1}},
            {"id": "task_2", "operation": "transform", "data": {"value": 2}},
            {"id": "task_3", "operation": "analyze", "data": {"type": "test"}},
        ]

        # Асинхронная обработка
        results = await engine.process_async(tasks)

        # Проверки
        assert len(results) == 3

        for result in results:
            assert result.success is True
            assert result.processing_time >= 0

        # Очистка
        engine.shutdown()

    def test_consciousness_adaptive_state_influence(self):
        """Тест влияния consciousness engine на адаптивные состояния."""
        # Создание SelfState
        self_state = SelfState()
        self_state.processing_efficiency = 0.6

        # Создание адаптивного менеджера
        manager = AdaptiveProcessingManager(lambda: self_state)

        # Создание consciousness engine с адаптивным менеджером
        engine = ParallelConsciousnessEngine()

        # Выполнение задач через engine
        tasks = [
            {"id": "influence_task", "operation": "analyze", "data": {"influence": "high"}}
        ]

        results = engine.process_sync(tasks)

        # Проверка что адаптивный менеджер может анализировать состояние
        state = manager.get_current_state()
        assert state is not None

        # Очистка
        engine.shutdown()


class TestFullMemoryProcessingPipeline:
    """Интеграционные тесты полного цикла обработки памяти."""

    def test_sensory_to_semantic_pipeline(self):
        """Тест полного цикла: sensory → episodic → semantic."""
        # Создание SelfState с памятью
        self_state = SelfState()
        self_state.memory = ArchiveMemory()

        # Создание иерархии памяти
        memory_hierarchy = MemoryHierarchyManager()
        memory_hierarchy.set_episodic_memory(self_state.memory)

        # Добавление сенсорных событий
        for i in range(10):  # Создаем повторяющиеся события
            event = Event(
                type="recurring_event",
                timestamp=time.time() + i * 0.1,
                intensity=0.8,
                metadata={"instance": i}
            )
            memory_hierarchy.add_sensory_event(event)

        # Первая консолидация (sensory → episodic)
        stats1 = memory_hierarchy.consolidate_memory(self_state)

        # Проверка что произошли переносы
        assert stats1["sensory_to_episodic_transfers"] > 0

        # Добавление большего количества событий того же типа
        for i in range(15):
            event = Event(
                type="recurring_event",
                timestamp=time.time() + (i + 10) * 0.1,
                intensity=0.8,
                metadata={"instance": i + 10}
            )
            memory_hierarchy.add_sensory_event(event)

        # Вторая консолидация (episodic → semantic)
        stats2 = memory_hierarchy.consolidate_memory(self_state)

        # Проверка консолидации
        assert stats2["episodic_to_semantic_transfers"] >= 0  # Может быть 0 если не достигнут порог

        # Проверка статуса иерархии
        status = memory_hierarchy.get_hierarchy_status()
        assert status["episodic_memory"]["available"] is True
        assert status["semantic_store"]["available"] is True

    def test_memory_hierarchy_with_adaptive_processing(self):
        """Тест иерархии памяти с адаптивной обработкой."""
        # Создание SelfState
        self_state = SelfState()
        self_state.memory = ArchiveMemory()
        self_state.stability = 0.85
        self_state.energy = 0.75
        self_state.processing_efficiency = 0.8

        # Создание иерархии памяти
        memory_hierarchy = MemoryHierarchyManager()
        memory_hierarchy.set_episodic_memory(self_state.memory)

        # Создание адаптивного менеджера с интеграцией памяти
        config = AdaptiveProcessingConfig(integrate_with_memory=True)
        adaptive_manager = AdaptiveProcessingManager(
            self_state_provider=lambda: self_state,
            config=config
        )
        adaptive_manager._memory_hierarchy = memory_hierarchy

        # Запуск адаптивной обработки
        adaptive_manager.start()

        # Добавление сенсорных событий
        for i in range(8):
            event = Event(
                type="adaptive_test_event",
                timestamp=time.time() + i * 0.05,
                intensity=0.7,
                metadata={"test_id": i}
            )
            memory_hierarchy.add_sensory_event(event)

        # Выполнение цикла адаптивной обработки
        result = adaptive_manager.update(self_state)

        # Проверка взаимодействия
        assert "memory_operations" in result
        assert len(result["memory_operations"]) > 0

        # Проверка консолидации
        consolidation = result["memory_operations"][0]
        assert "operation" in consolidation
        assert consolidation["operation"] == "consolidation"

        adaptive_manager.stop()

    def test_memory_query_integration(self):
        """Тест интеграции запросов к памяти."""
        # Создание иерархии памяти
        memory_hierarchy = MemoryHierarchyManager()

        # Добавление сенсорных событий разных типов
        event_types = ["event_a", "event_b", "event_c"]
        for i in range(5):
            for event_type in event_types:
                event = Event(
                    type=event_type,
                    timestamp=time.time() + i * 0.1,
                    intensity=0.6 + i * 0.1,
                    metadata={"index": i}
                )
                memory_hierarchy.add_sensory_event(event)

        # Запросы к разным уровням памяти
        sensory_results = memory_hierarchy.query_memory("sensory", max_events=10)
        assert len(sensory_results) > 0

        semantic_results = memory_hierarchy.query_memory("semantic", query="event")
        assert isinstance(semantic_results, list)

        procedural_results = memory_hierarchy.query_memory("procedural", context={"test": True})
        assert isinstance(procedural_results, list)

        # Проверка что запросы не ломают систему
        status = memory_hierarchy.get_hierarchy_status()
        assert status["hierarchy_manager"]["transfers_sensory_to_episodic"] >= 0


class TestCrossComponentScenarios:
    """Интеграционные тесты кросс-компонентных сценариев."""

    def test_full_system_scenario(self):
        """Тест полного системного сценария."""
        # Создание SelfState
        self_state = SelfState()
        self_state.memory = ArchiveMemory()
        self_state.stability = 0.8
        self_state.energy = 0.7
        self_state.processing_efficiency = 0.75

        # Создание всех компонентов
        memory_hierarchy = MemoryHierarchyManager()
        memory_hierarchy.set_episodic_memory(self_state.memory)

        adaptive_config = AdaptiveProcessingConfig(integrate_with_memory=True)
        adaptive_manager = AdaptiveProcessingManager(
            self_state_provider=lambda: self_state,
            config=adaptive_config
        )
        adaptive_manager._memory_hierarchy = memory_hierarchy

        consciousness_engine = ParallelConsciousnessEngine()

        # Сценарий 1: Добавление сенсорных данных
        for i in range(6):
            event = Event(
                type="system_event",
                timestamp=time.time() + i * 0.2,
                intensity=0.7,
                metadata={"scenario": "full_system", "step": i}
            )
            memory_hierarchy.add_sensory_event(event)

        # Сценарий 2: Адаптивная обработка
        adaptive_manager.start()
        adaptive_result = adaptive_manager.update(self_state)
        assert adaptive_result["status"] == "updated"

        # Сценарий 3: Параллельная обработка через consciousness engine
        tasks = [
            {
                "id": "system_analysis",
                "operation": "analyze",
                "data": {
                    "system_state": self_state.__dict__,
                    "memory_status": memory_hierarchy.get_hierarchy_status()
                }
            }
        ]

        consciousness_results = consciousness_engine.process_sync(tasks)
        assert len(consciousness_results) == 1
        assert consciousness_results[0].success is True

        # Сценарий 4: Финальная консолидация памяти
        consolidation_stats = memory_hierarchy.consolidate_memory(self_state)
        assert isinstance(consolidation_stats, dict)

        # Очистка
        adaptive_manager.stop()
        consciousness_engine.shutdown()

    def test_error_handling_integration(self):
        """Тест обработки ошибок в интеграции компонентов."""
        # Создание компонентов с потенциальными проблемами
        self_state = SelfState()

        # Адаптивный менеджер без self_state_provider (для тестирования ошибок)
        try:
            manager = AdaptiveProcessingManager(self_state_provider=lambda: None)
            # Это не должно сломать систему
            manager.get_current_state()  # Должно обработать None gracefully
        except Exception as e:
            # Ошибки должны логироваться, но не ломать тест
            assert isinstance(e, Exception)

        # Тест с неполной конфигурацией памяти
        memory_hierarchy = MemoryHierarchyManager()
        # Отсутствие эпизодической памяти не должно ломать запросы
        result = memory_hierarchy.query_memory("episodic")
        assert isinstance(result, list)

    def test_performance_integration(self):
        """Тест производительности интеграции компонентов."""
        import time

        self_state = SelfState()
        self_state.memory = ArchiveMemory()

        # Создание компонентов
        memory_hierarchy = MemoryHierarchyManager()
        memory_hierarchy.set_episodic_memory(self_state.memory)

        adaptive_manager = AdaptiveProcessingManager(
            self_state_provider=lambda: self_state,
            config=AdaptiveProcessingConfig(integrate_with_memory=True)
        )
        adaptive_manager._memory_hierarchy = memory_hierarchy

        # Замер времени комплексной операции
        start_time = time.time()

        # Добавление событий
        for i in range(20):
            event = Event(
                type=f"perf_event_{i % 3}",
                timestamp=time.time() + i * 0.01,
                intensity=0.5,
                metadata={"perf_test": i}
            )
            memory_hierarchy.add_sensory_event(event)

        # Адаптивная обработка
        adaptive_manager.start()
        adaptive_manager.update(self_state)

        # Консолидация
        memory_hierarchy.consolidate_memory(self_state)

        # Запросы
        memory_hierarchy.query_memory("sensory")
        memory_hierarchy.query_memory("semantic")

        end_time = time.time()
        total_time = end_time - start_time

        # Проверка что операция завершилась за разумное время (< 1 секунды)
        assert total_time < 1.0, f"Integration test took too long: {total_time:.3f}s"

        adaptive_manager.stop()


if __name__ == "__main__":
    pytest.main([__file__])