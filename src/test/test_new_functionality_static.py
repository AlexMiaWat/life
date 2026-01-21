"""
Static Tests for New Functionality.

Статические тесты проверяют:
- Структуру данных и типов
- Константы и конфигурацию
- Импорты и зависимости
- API интерфейсы
- Валидацию параметров
"""

import pytest
from unittest.mock import Mock, MagicMock
from dataclasses import is_dataclass
from enum import Enum
import sys
from pathlib import Path

# Настройка путей
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
from src.experimental.memory_hierarchy.semantic_store import SemanticConcept
from src.experimental.memory_hierarchy.procedural_store import ProceduralMemoryStore
from src.experimental.memory_hierarchy.sensory_buffer import SensoryBuffer
from src.experimental.consciousness.parallel_engine import ParallelConsciousnessEngine
from src.environment.event import Event


class TestStaticDataStructures:
    """Статические тесты структур данных."""

    def test_processing_mode_enum(self):
        """Проверка enum ProcessingMode."""
        assert isinstance(ProcessingMode.BASELINE, Enum)
        assert isinstance(ProcessingMode.EFFICIENT, Enum)
        assert isinstance(ProcessingMode.INTENSIVE, Enum)
        assert isinstance(ProcessingMode.OPTIMIZED, Enum)
        assert isinstance(ProcessingMode.SELF_MONITORING, Enum)

        # Проверка значений
        assert ProcessingMode.BASELINE.value == "baseline"
        assert ProcessingMode.EFFICIENT.value == "efficient"
        assert ProcessingMode.INTENSIVE.value == "intensive"
        assert ProcessingMode.OPTIMIZED.value == "optimized"
        assert ProcessingMode.SELF_MONITORING.value == "self_monitoring"

    def test_adaptive_state_enum(self):
        """Проверка enum AdaptiveState."""
        assert isinstance(AdaptiveState.STANDARD, Enum)
        assert isinstance(AdaptiveState.EFFICIENT_PROCESSING, Enum)
        assert isinstance(AdaptiveState.INTENSIVE_ANALYSIS, Enum)
        assert isinstance(AdaptiveState.SYSTEM_SELF_MONITORING, Enum)
        assert isinstance(AdaptiveState.OPTIMAL_PROCESSING, Enum)

        # Проверка значений
        assert AdaptiveState.STANDARD.value == "standard"
        assert AdaptiveState.EFFICIENT_PROCESSING.value == "efficient_processing"
        assert AdaptiveState.INTENSIVE_ANALYSIS.value == "intensive_analysis"
        assert AdaptiveState.SYSTEM_SELF_MONITORING.value == "system_self_monitoring"
        assert AdaptiveState.OPTIMAL_PROCESSING.value == "optimal_processing"

    def test_processing_event_dataclass(self):
        """Проверка dataclass ProcessingEvent."""
        assert is_dataclass(ProcessingEvent)

        # Создание экземпляра с минимальными параметрами
        event = ProcessingEvent(processing_mode=ProcessingMode.BASELINE)
        assert event.processing_mode == ProcessingMode.BASELINE
        assert event.intensity == 1.0
        assert event.duration_ticks == 50
        assert isinstance(event.trigger_conditions, dict)
        assert isinstance(event.timestamp, float)

    def test_adaptive_processing_config_dataclass(self):
        """Проверка dataclass AdaptiveProcessingConfig."""
        assert is_dataclass(AdaptiveProcessingConfig)

        # Создание с дефолтными значениями
        config = AdaptiveProcessingConfig()
        assert isinstance(config.stability_threshold, float)
        assert isinstance(config.energy_threshold, float)
        assert isinstance(config.processing_efficiency_threshold, float)
        assert isinstance(config.cognitive_load_max, float)
        assert isinstance(config.check_interval, float)
        assert isinstance(config.state_transition_cooldown, float)
        assert isinstance(config.max_history_size, int)
        assert isinstance(config.max_transition_history_size, int)

        # Проверка булевых флагов
        assert isinstance(config.enable_efficient_processing, bool)
        assert isinstance(config.enable_intensive_analysis, bool)
        assert isinstance(config.enable_system_self_monitoring, bool)
        assert isinstance(config.enable_optimal_processing, bool)
        assert isinstance(config.integrate_with_memory, bool)
        assert isinstance(config.adaptive_thresholds_enabled, bool)

    def test_semantic_concept_dataclass(self):
        """Проверка dataclass SemanticConcept."""
        assert is_dataclass(SemanticConcept)

        # Создание экземпляра
        concept = SemanticConcept(
            concept_id="test_concept",
            name="Test Concept",
            description="A test concept",
            confidence=0.8
        )
        assert concept.concept_id == "test_concept"
        assert concept.name == "Test Concept"
        assert concept.description == "A test concept"
        assert concept.confidence == 0.8
        assert concept.activation_count == 0
        assert isinstance(concept.related_concepts, set)
        assert isinstance(concept.properties, dict)
        assert isinstance(concept.created_at, float)
        assert isinstance(concept.last_activation, float)


class TestConstants:
    """Статические тесты констант и конфигурации."""

    def test_memory_hierarchy_constants(self):
        """Проверка констант MemoryHierarchyManager."""
        assert hasattr(MemoryHierarchyManager, 'SENSORY_TO_EPISODIC_THRESHOLD')
        assert hasattr(MemoryHierarchyManager, 'EPISODIC_TO_SEMANTIC_THRESHOLD')
        assert hasattr(MemoryHierarchyManager, 'SEMANTIC_CONSOLIDATION_INTERVAL')

        assert isinstance(MemoryHierarchyManager.SENSORY_TO_EPISODIC_THRESHOLD, int)
        assert isinstance(MemoryHierarchyManager.EPISODIC_TO_SEMANTIC_THRESHOLD, int)
        assert isinstance(MemoryHierarchyManager.SEMANTIC_CONSOLIDATION_INTERVAL, float)

        assert MemoryHierarchyManager.SENSORY_TO_EPISODIC_THRESHOLD > 0
        assert MemoryHierarchyManager.EPISODIC_TO_SEMANTIC_THRESHOLD > MemoryHierarchyManager.SENSORY_TO_EPISODIC_THRESHOLD
        assert MemoryHierarchyManager.SEMANTIC_CONSOLIDATION_INTERVAL > 0

    def test_default_config_values(self):
        """Проверка дефолтных значений конфигурации."""
        config = AdaptiveProcessingConfig()

        # Проверка диапазонов значений
        assert 0.0 <= config.stability_threshold <= 1.0
        assert 0.0 <= config.energy_threshold <= 1.0
        assert 0.0 <= config.processing_efficiency_threshold <= 1.0
        assert 0.0 <= config.cognitive_load_max <= 1.0
        assert config.check_interval > 0
        assert config.state_transition_cooldown > 0
        assert config.max_history_size > 0
        assert config.max_transition_history_size > 0


class TestImportsAndDependencies:
    """Статические тесты импортов и зависимостей."""

    def test_adaptive_processing_imports(self):
        """Проверка импортов AdaptiveProcessingManager."""
        # Проверяем что все необходимые импорты доступны
        from src.experimental.adaptive_processing_manager import (
            AdaptiveProcessingManager,
            ProcessingMode,
            AdaptiveState,
            ProcessingEvent,
            AdaptiveProcessingConfig,
        )

        # Проверяем что классы определены
        assert AdaptiveProcessingManager is not None
        assert ProcessingMode is not None
        assert AdaptiveState is not None
        assert ProcessingEvent is not None
        assert AdaptiveProcessingConfig is not None

    def test_memory_hierarchy_imports(self):
        """Проверка импортов MemoryHierarchyManager."""
        from src.experimental.memory_hierarchy.hierarchy_manager import MemoryHierarchyManager
        from src.experimental.memory_hierarchy.semantic_store import SemanticConcept
        from src.experimental.memory_hierarchy.procedural_store import ProceduralMemoryStore
        from src.experimental.memory_hierarchy.sensory_buffer import SensoryBuffer

        assert MemoryHierarchyManager is not None
        assert SemanticConcept is not None
        assert ProceduralMemoryStore is not None
        assert SensoryBuffer is not None

    def test_consciousness_imports(self):
        """Проверка импортов ParallelConsciousnessEngine."""
        from src.experimental.consciousness.parallel_engine import (
            ParallelConsciousnessEngine,
            ProcessingMode as ConsciousnessProcessingMode,
            ProcessingResult,
        )

        assert ParallelConsciousnessEngine is not None
        assert ConsciousnessProcessingMode is not None
        assert ProcessingResult is not None

    def test_no_circular_imports(self):
        """Проверка отсутствия циклических импортов."""
        # Импорт всех основных модулей
        modules_to_test = [
            'src.experimental.adaptive_processing_manager',
            'src.experimental.memory_hierarchy.hierarchy_manager',
            'src.experimental.memory_hierarchy.semantic_store',
            'src.experimental.memory_hierarchy.procedural_store',
            'src.experimental.memory_hierarchy.sensory_buffer',
            'src.experimental.consciousness.parallel_engine',
        ]

        for module_name in modules_to_test:
            # Проверяем что модуль можно импортировать без ошибок
            try:
                __import__(module_name)
                # Проверяем что модуль в sys.modules
                assert module_name in sys.modules
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")


class TestAPIInterfaces:
    """Статические тесты API интерфейсов."""

    def test_adaptive_processing_api_methods(self):
        """Проверка методов API AdaptiveProcessingManager."""
        # Создаем мок для self_state_provider
        mock_self_state = Mock()
        manager = AdaptiveProcessingManager(lambda: mock_self_state)

        # Проверяем наличие основных методов
        assert hasattr(manager, 'start')
        assert hasattr(manager, 'stop')
        assert hasattr(manager, 'update')
        assert hasattr(manager, 'analyze_system_conditions')
        assert hasattr(manager, 'get_current_state')
        assert hasattr(manager, 'trigger_processing_event')
        assert hasattr(manager, 'force_adaptive_state')
        assert hasattr(manager, 'get_system_status')
        assert hasattr(manager, 'get_processing_statistics')
        assert hasattr(manager, 'get_adaptive_statistics')
        assert hasattr(manager, 'reset_statistics')
        assert hasattr(manager, 'update_configuration')
        assert hasattr(manager, 'get_legacy_status')

        # Проверяем callable методы
        assert callable(manager.start)
        assert callable(manager.stop)
        assert callable(manager.update)
        assert callable(manager.analyze_system_conditions)
        assert callable(manager.get_current_state)

    def test_memory_hierarchy_api_methods(self):
        """Проверка методов API MemoryHierarchyManager."""
        manager = MemoryHierarchyManager()

        # Проверяем наличие основных методов
        assert hasattr(manager, 'set_episodic_memory')
        assert hasattr(manager, 'add_sensory_event')
        assert hasattr(manager, 'process_sensory_events')
        assert hasattr(manager, 'consolidate_memory')
        assert hasattr(manager, 'get_hierarchy_status')
        assert hasattr(manager, 'query_memory')
        assert hasattr(manager, 'reset_hierarchy')

        # Проверяем callable методы
        assert callable(manager.set_episodic_memory)
        assert callable(manager.add_sensory_event)
        assert callable(manager.process_sensory_events)
        assert callable(manager.consolidate_memory)
        assert callable(manager.get_hierarchy_status)
        assert callable(manager.query_memory)
        assert callable(manager.reset_hierarchy)

    def test_semantic_concept_api_methods(self):
        """Проверка методов API SemanticConcept."""
        concept = SemanticConcept(
            concept_id="test",
            name="Test",
            description="Test concept",
            confidence=0.8
        )

        # Проверяем наличие методов
        assert hasattr(concept, 'activate')
        assert hasattr(concept, 'add_relation')
        assert hasattr(concept, 'get_activation_strength')

        # Проверяем callable методы
        assert callable(concept.activate)
        assert callable(concept.add_relation)
        assert callable(concept.get_activation_strength)

    def test_parallel_consciousness_api_methods(self):
        """Проверка методов API ParallelConsciousnessEngine."""
        engine = ParallelConsciousnessEngine()

        # Проверяем наличие основных методов
        assert hasattr(engine, 'process_async')
        assert hasattr(engine, 'process_sync')
        assert hasattr(engine, 'shutdown')

        # Проверяем callable методы
        assert callable(engine.process_async)
        assert callable(engine.process_sync)
        assert callable(engine.shutdown)


class TestParameterValidation:
    """Статические тесты валидации параметров."""

    def test_adaptive_processing_config_validation(self):
        """Проверка валидации AdaptiveProcessingConfig."""
        # Валидная конфигурация
        config = AdaptiveProcessingConfig()
        manager = AdaptiveProcessingManager(lambda: Mock())

        # Это должно пройти без ошибок
        manager.config = config

        # Проверка что валидация работает
        assert hasattr(manager, '_validate_config')
        assert callable(manager._validate_config)

    def test_processing_event_validation(self):
        """Проверка валидации ProcessingEvent."""
        # Валидное событие
        event = ProcessingEvent(
            processing_mode=ProcessingMode.BASELINE,
            intensity=0.5,
            duration_ticks=100
        )

        assert event.processing_mode == ProcessingMode.BASELINE
        assert event.intensity == 0.5
        assert event.duration_ticks == 100

    def test_semantic_concept_validation(self):
        """Проверка валидации SemanticConcept."""
        # Валидная концепция
        concept = SemanticConcept(
            concept_id="valid_id",
            name="Valid Name",
            description="Valid description",
            confidence=0.75
        )

        assert concept.concept_id == "valid_id"
        assert concept.name == "Valid Name"
        assert concept.description == "Valid description"
        assert concept.confidence == 0.75

    def test_enum_value_types(self):
        """Проверка типов значений enum."""
        # ProcessingMode
        for mode in ProcessingMode:
            assert isinstance(mode.value, str)
            assert len(mode.value) > 0

        # AdaptiveState
        for state in AdaptiveState:
            assert isinstance(state.value, str)
            assert len(state.value) > 0


class TestTypeHints:
    """Статические тесты type hints."""

    def test_dataclass_field_types(self):
        """Проверка типов полей в dataclass."""
        import typing
        from typing import get_type_hints

        # ProcessingEvent
        hints = get_type_hints(ProcessingEvent)
        assert 'processing_mode' in hints
        assert 'intensity' in hints
        assert 'duration_ticks' in hints
        assert 'trigger_conditions' in hints
        assert 'timestamp' in hints

        # SemanticConcept
        hints = get_type_hints(SemanticConcept)
        assert 'concept_id' in hints
        assert 'name' in hints
        assert 'description' in hints
        assert 'confidence' in hints
        assert 'activation_count' in hints
        assert 'last_activation' in hints
        assert 'related_concepts' in hints
        assert 'properties' in hints
        assert 'created_at' in hints


if __name__ == "__main__":
    pytest.main([__file__])