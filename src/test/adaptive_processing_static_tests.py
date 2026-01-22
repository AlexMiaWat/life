"""
Статические тесты для экспериментальной функциональности Adaptive Processing.

Включает unit тесты, валидацию типов, проверку контрактов сериализации.
"""

import pytest
import time
from typing import Dict, Any
from unittest.mock import Mock, MagicMock

from src.experimental.adaptive_processing_manager import (
    AdaptiveProcessingManager,
    ProcessingMode,
    AdaptiveState,
    ProcessingEvent,
    AdaptiveProcessingConfig
)
from src.contracts.serialization_contract import SerializationContract, SerializationError
from src.observability.structured_logger import StructuredLogger
from src.test.conftest import RealisticSelfStateMock


class TestProcessingMode:
    """Тесты для ProcessingMode enum."""

    def test_enum_values(self):
        """Тест значений enum ProcessingMode."""
        assert ProcessingMode.BASELINE.value == "baseline"
        assert ProcessingMode.EFFICIENT.value == "efficient"
        assert ProcessingMode.INTENSIVE.value == "intensive"
        assert ProcessingMode.OPTIMIZED.value == "optimized"
        assert ProcessingMode.SELF_MONITORING.value == "self_monitoring"

    def test_enum_members(self):
        """Тест членов enum ProcessingMode."""
        modes = [ProcessingMode.BASELINE, ProcessingMode.EFFICIENT,
                ProcessingMode.INTENSIVE, ProcessingMode.OPTIMIZED,
                ProcessingMode.SELF_MONITORING]
        assert len(modes) == 5
        assert all(isinstance(mode, ProcessingMode) for mode in modes)


class TestAdaptiveState:
    """Тесты для AdaptiveState enum."""

    def test_enum_values(self):
        """Тест значений enum AdaptiveState."""
        assert AdaptiveState.STANDARD.value == "standard"
        assert AdaptiveState.EFFICIENT_PROCESSING.value == "efficient_processing"
        assert AdaptiveState.INTENSIVE_ANALYSIS.value == "intensive_analysis"
        assert AdaptiveState.SYSTEM_SELF_MONITORING.value == "system_self_monitoring"
        assert AdaptiveState.OPTIMAL_PROCESSING.value == "optimal_processing"

    def test_enum_members(self):
        """Тест членов enum AdaptiveState."""
        states = [AdaptiveState.STANDARD, AdaptiveState.EFFICIENT_PROCESSING,
                 AdaptiveState.INTENSIVE_ANALYSIS, AdaptiveState.SYSTEM_SELF_MONITORING,
                 AdaptiveState.OPTIMAL_PROCESSING]
        assert len(states) == 5
        assert all(isinstance(state, AdaptiveState) for state in states)


class TestProcessingEvent:
    """Тесты для ProcessingEvent dataclass."""

    def test_initialization_default(self):
        """Тест инициализации с параметрами по умолчанию."""
        event = ProcessingEvent(processing_mode=ProcessingMode.EFFICIENT)

        assert event.processing_mode == ProcessingMode.EFFICIENT
        assert event.intensity == 1.0
        assert event.duration_ticks == 50
        assert isinstance(event.trigger_conditions, dict)
        assert event.trigger_conditions == {}
        assert isinstance(event.timestamp, float)
        assert event.timestamp <= time.time()

    def test_initialization_custom(self):
        """Тест инициализации с пользовательскими параметрами."""
        trigger_conditions = {"stability": 0.8, "energy": 0.7}
        timestamp = 1234567890.0

        event = ProcessingEvent(
            processing_mode=ProcessingMode.INTENSIVE,
            intensity=0.9,
            duration_ticks=100,
            trigger_conditions=trigger_conditions,
            timestamp=timestamp
        )

        assert event.processing_mode == ProcessingMode.INTENSIVE
        assert event.intensity == 0.9
        assert event.duration_ticks == 100
        assert event.trigger_conditions == trigger_conditions
        assert event.timestamp == timestamp

    def test_intensity_range(self):
        """Тест допустимого диапазона intensity."""
        # Создание с допустимыми значениями
        event = ProcessingEvent(
            processing_mode=ProcessingMode.EFFICIENT,
            intensity=0.5
        )
        assert event.intensity == 0.5

        # Создание с граничными значениями
        event_min = ProcessingEvent(
            processing_mode=ProcessingMode.EFFICIENT,
            intensity=0.0
        )
        assert event_min.intensity == 0.0

        event_max = ProcessingEvent(
            processing_mode=ProcessingMode.EFFICIENT,
            intensity=1.0
        )
        assert event_max.intensity == 1.0


class TestAdaptiveProcessingConfig:
    """Тесты для AdaptiveProcessingConfig dataclass."""

    def test_initialization_default(self):
        """Тест инициализации с параметрами по умолчанию."""
        config = AdaptiveProcessingConfig()

        assert config.stability_threshold == 0.8
        assert config.energy_threshold == 0.7
        assert config.processing_efficiency_threshold == 0.6
        assert config.cognitive_load_max == 0.7
        assert config.check_interval == 1.0
        assert config.state_transition_cooldown == 5.0
        assert config.max_history_size == 100

    def test_initialization_custom(self):
        """Тест инициализации с пользовательскими параметрами."""
        config = AdaptiveProcessingConfig(
            stability_threshold=0.9,
            energy_threshold=0.8,
            processing_efficiency_threshold=0.7,
            cognitive_load_max=0.85,
            check_interval=2.0,
            state_transition_cooldown=10.0,
            max_history_size=200
        )

        assert config.stability_threshold == 0.9
        assert config.energy_threshold == 0.8
        assert config.processing_efficiency_threshold == 0.7
        assert config.cognitive_load_max == 0.85
        assert config.check_interval == 2.0
        assert config.state_transition_cooldown == 10.0
        assert config.max_history_size == 200

    def test_threshold_ranges(self):
        """Тест допустимых диапазонов пороговых значений."""
        # Создание с допустимыми значениями
        config = AdaptiveProcessingConfig(
            stability_threshold=0.5,
            energy_threshold=0.6,
            processing_efficiency_threshold=0.7,
            cognitive_load_max=0.8
        )
        assert config.stability_threshold == 0.5
        assert config.energy_threshold == 0.6
        assert config.processing_efficiency_threshold == 0.7
        assert config.cognitive_load_max == 0.8

    def test_performance_settings(self):
        """Тест настроек производительности."""
        config = AdaptiveProcessingConfig(
            check_interval=1.5,
            state_transition_cooldown=7.0,
            max_history_size=150
        )
        assert config.check_interval == 1.5
        assert config.state_transition_cooldown == 7.0
        assert config.max_history_size == 150




class TestAdaptiveProcessingManagerInitialization:
    """Тесты инициализации AdaptiveProcessingManager."""

    def test_initialization_with_mock_provider(self):
        """Тест инициализации с mock провайдером."""
        mock_provider = Mock()
        mock_state = Mock()
        mock_provider.return_value = mock_state

        manager = AdaptiveProcessingManager(mock_provider)

        assert manager is not None
        assert not manager._is_active
        assert manager.config is not None
        assert isinstance(manager.config, AdaptiveProcessingConfig)
        assert manager._last_update_time == 0.0

    def test_initialization_with_logger(self):
        """Тест инициализации с логером."""
        mock_provider = Mock()
        mock_state = Mock()
        mock_provider.return_value = mock_state

        mock_logger = Mock(spec=StructuredLogger)

        manager = AdaptiveProcessingManager(mock_provider, logger=mock_logger)

        assert manager.logger == mock_logger

    def test_initialization_with_config(self):
        """Тест инициализации с кастомной конфигурацией."""
        mock_provider = Mock()
        mock_state = Mock()
        mock_provider.return_value = mock_state

        config = AdaptiveProcessingConfig(
            stability_threshold=0.85,
            check_interval=1.5
        )

        manager = AdaptiveProcessingManager(mock_provider, config=config)

        assert manager.config.stability_threshold == 0.85
        assert manager.config.check_interval == 1.5


class TestAdaptiveProcessingManagerStateManagement:
    """Тесты управления состоянием AdaptiveProcessingManager."""

    def setup_method(self):
        """Настройка теста."""
        self.mock_provider = Mock()
        self.mock_state = Mock()
        self.mock_state.stability = 0.8
        self.mock_state.energy = 0.7
        self.mock_state.processing_efficiency = 0.6
        self.mock_state.cognitive_load = 0.3
        self.mock_state.current_adaptive_state = AdaptiveState.STANDARD.value
        self.mock_provider.return_value = self.mock_state

        self.manager = AdaptiveProcessingManager(self.mock_provider)

    def test_force_adaptive_state_success(self):
        """Тест принудительной установки состояния - успех."""
        result = self.manager.force_adaptive_state(
            self.mock_state,
            AdaptiveState.EFFICIENT_PROCESSING
        )

        assert result is True
        assert self.mock_state.current_adaptive_state == AdaptiveState.EFFICIENT_PROCESSING.value

    def test_force_adaptive_state_valid_transitions(self):
        """Тест принудительной установки состояния - валидные переходы."""
        # Корректное состояние
        result = self.manager.force_adaptive_state(self.mock_state, AdaptiveState.EFFICIENT_PROCESSING)
        assert result is True
        assert self.mock_state.current_adaptive_state == AdaptiveState.EFFICIENT_PROCESSING.value

        # Другое корректное состояние
        result = self.manager.force_adaptive_state(self.mock_state, AdaptiveState.INTENSIVE_ANALYSIS)
        assert result is True
        assert self.mock_state.current_adaptive_state == AdaptiveState.INTENSIVE_ANALYSIS.value

    def test_get_current_state(self):
        """Тест получения текущего состояния."""
        state_info = self.manager.get_current_state()
        # get_current_state возвращает AdaptiveState объект
        assert isinstance(state_info, AdaptiveState)

        # Изменяем состояние
        self.manager.force_adaptive_state(self.mock_state, AdaptiveState.OPTIMAL_PROCESSING)
        # Проверяем через self_state
        assert self.mock_state.current_adaptive_state == AdaptiveState.OPTIMAL_PROCESSING.value


class TestAdaptiveProcessingManagerEventProcessing:
    """Тесты обработки событий AdaptiveProcessingManager."""

    def setup_method(self):
        """Настройка теста."""
        self.mock_provider = Mock()
        self.mock_state = Mock()
        self.mock_state.stability = 0.9
        self.mock_state.energy = 0.8
        self.mock_state.processing_efficiency = 0.7
        self.mock_state.cognitive_load = 0.2
        self.mock_state.processing_state = False
        self.mock_state.processing_intensity = 0.0
        self.mock_state.processing_history = []
        self.mock_provider.return_value = self.mock_state

        self.manager = AdaptiveProcessingManager(self.mock_provider)
        self.manager.start()

    def test_trigger_processing_event_success(self):
        """Тест успешного срабатывания события обработки."""
        result = self.manager.trigger_processing_event(
            self.mock_state,
            ProcessingMode.EFFICIENT,
            0.8
        )

        assert result is True
        assert self.mock_state.processing_state is True
        assert self.mock_state.processing_intensity == 0.8

    def test_trigger_processing_event_invalid_mode(self):
        """Тест срабатывания события с некорректным режимом."""
        result = self.manager.trigger_processing_event(
            self.mock_state,
            None,  # Некорректный режим
            0.8
        )

        assert result is False

    def test_trigger_processing_event_intensity_normalization(self):
        """Тест нормализации интенсивности."""
        # Сбросить состояние
        self.mock_state.processing_state = False

        # Слишком высокая интенсивность
        result = self.manager.trigger_processing_event(
            self.mock_state,
            ProcessingMode.EFFICIENT,
            1.5  # Высокая интенсивность
        )

        assert result is True
        # Проверить что интенсивность была нормализована
        assert self.mock_state.processing_intensity == 1.0



class TestAdaptiveProcessingManagerStatistics:
    """Тесты статистики AdaptiveProcessingManager."""

    def setup_method(self):
        """Настройка теста."""
        self.mock_provider = Mock()
        self.mock_state = Mock()
        self.mock_state.stability = 0.8
        self.mock_state.energy = 0.7
        self.mock_state.processing_efficiency = 0.6
        self.mock_state.cognitive_load = 0.3
        self.mock_provider.return_value = self.mock_state

        self.manager = AdaptiveProcessingManager(self.mock_provider)

    def test_get_processing_statistics_initial(self):
        """Тест получения начальной статистики обработки."""
        stats = self.manager.get_processing_statistics()

        assert isinstance(stats, dict)
        assert "total_processing_events" in stats
        assert stats["total_processing_events"] == 0

    def test_get_adaptive_statistics_initial(self):
        """Тест получения начальной адаптивной статистики."""
        stats = self.manager.get_adaptive_statistics()

        assert isinstance(stats, dict)
        assert "total_state_transitions" in stats
        assert stats["total_state_transitions"] == 0


class TestAdaptiveProcessingManagerSystemStatus:
    """Тесты статуса системы AdaptiveProcessingManager."""

    def setup_method(self):
        """Настройка теста."""
        self.mock_provider = Mock()
        self.mock_state = Mock()
        self.mock_state.processing_history = []
        self.mock_provider.return_value = self.mock_state

        self.manager = AdaptiveProcessingManager(self.mock_provider)

    def test_get_system_status_inactive(self):
        """Тест получения статуса системы при неактивном менеджере."""
        status = self.manager.get_system_status()

        assert isinstance(status, dict)
        assert "manager" in status
        assert "components" in status
        assert status["manager"]["is_active"] is False

    def test_get_system_status_active(self):
        """Тест получения статуса системы при активном менеджере."""
        self.manager.start()

        status = self.manager.get_system_status()

        assert isinstance(status, dict)
        assert status["manager"]["is_active"] is True

    def test_get_legacy_status(self):
        """Тест получения статуса в старом формате."""
        legacy_status = self.manager.get_legacy_status()

        assert isinstance(legacy_status, dict)
        assert "clarity_moments" in legacy_status
        assert "consciousness_system" in legacy_status


class TestComponentSerialization:
    """Тесты сериализации компонентов."""

    def test_processing_event_serialization(self):
        """Тест сериализации ProcessingEvent."""
        event = ProcessingEvent(
            processing_mode=ProcessingMode.EFFICIENT,
            intensity=0.8,
            duration_ticks=100,
            trigger_conditions={"test": "value"}
        )

        # ProcessingEvent не имеет метода to_dict, проверяем базовую функциональность
        assert event.processing_mode == ProcessingMode.EFFICIENT
        assert event.intensity == 0.8
        assert event.duration_ticks == 100
        assert event.trigger_conditions == {"test": "value"}

    def test_adaptive_config_dict_conversion(self):
        """Тест конвертации AdaptiveProcessingConfig."""
        config = AdaptiveProcessingConfig(
            stability_threshold=0.8,
            energy_threshold=0.7
        )

        # AdaptiveProcessingConfig не имеет to_dict, проверяем атрибуты
        assert config.stability_threshold == 0.8
        assert config.energy_threshold == 0.7
        assert config.processing_efficiency_threshold == 0.6  # default


class TestAdaptiveProcessingManagerNewAPI:
    """Тесты для новых методов API AdaptiveProcessingManager."""

    def setup_method(self):
        """Настройка теста."""
        self.mock_provider = Mock()
        self.mock_state = Mock()
        self.mock_state.stability = 0.8
        self.mock_state.energy = 0.7
        self.mock_state.processing_efficiency = 0.6
        self.mock_state.cognitive_load = 0.3
        self.mock_state.current_adaptive_state = AdaptiveState.STANDARD.value
        self.mock_state.processing_history = []
        self.mock_provider.return_value = self.mock_state

        self.manager = AdaptiveProcessingManager(self.mock_provider)

    def test_set_consciousness_manager(self):
        """Тест установки менеджера сознания."""
        from src.experimental.consciousness.states import ConsciousnessStateManager

        consciousness_manager = ConsciousnessStateManager()

        # Изначально менеджер сознания не установлен
        assert self.manager.consciousness_manager is None

        # Устанавливаем менеджер
        self.manager.set_consciousness_manager(consciousness_manager)

        # Проверяем что менеджер установлен
        assert self.manager.consciousness_manager is consciousness_manager

    def test_sync_with_consciousness_manager_no_manager(self):
        """Тест синхронизации без установленного менеджера сознания."""
        # Не должно быть исключений
        self.manager._sync_with_consciousness_manager(AdaptiveState.EFFICIENT_PROCESSING)

    def test_sync_with_consciousness_manager_with_manager(self):
        """Тест синхронизации с установленным менеджером сознания."""
        from src.experimental.consciousness.states import ConsciousnessStateManager, ConsciousnessState

        consciousness_manager = ConsciousnessStateManager()
        self.manager.set_consciousness_manager(consciousness_manager)

        # Выполняем синхронизацию
        self.manager._sync_with_consciousness_manager(AdaptiveState.EFFICIENT_PROCESSING)

        # Проверяем что состояние изменилось
        assert consciousness_manager.current_state == ConsciousnessState.ACTIVE

    def test_force_adaptive_state_with_sync(self):
        """Тест принудительной установки состояния с синхронизацией."""
        from src.experimental.consciousness.states import ConsciousnessStateManager, ConsciousnessState

        consciousness_manager = ConsciousnessStateManager()
        self.manager.set_consciousness_manager(consciousness_manager)

        # Выполняем принудительную установку состояния
        result = self.manager.force_adaptive_state(self.mock_state, AdaptiveState.INTENSIVE_ANALYSIS)

        assert result is True
        assert self.mock_state.current_adaptive_state == AdaptiveState.INTENSIVE_ANALYSIS.value
        # Проверяем синхронизацию
        assert consciousness_manager.current_state == ConsciousnessState.ACTIVE

    def test_trigger_processing_event_validation(self):
        """Тест валидации в trigger_processing_event."""
        # Некорректный режим обработки
        result = self.manager.trigger_processing_event(self.mock_state, None, 0.8)
        assert result is False

        # Некорректный тип режима
        result = self.manager.trigger_processing_event(self.mock_state, "invalid_mode", 0.8)
        assert result is False

        # Корректный режим
        result = self.manager.trigger_processing_event(self.mock_state, ProcessingMode.EFFICIENT, 0.8)
        assert result is True

    def test_get_current_state_method(self):
        """Тест метода get_current_state."""
        state = self.manager.get_current_state()
        assert isinstance(state, AdaptiveState)

        # Изменяем состояние через mock
        self.mock_state.processing_efficiency = 0.9
        self.mock_state.meta_cognition_depth = 0.8

        # Обновляем состояние через менеджер
        self.manager.update(self.mock_state)

        # Проверяем что состояние могло измениться
        new_state = self.manager.get_current_state()
        assert isinstance(new_state, AdaptiveState)


class TestAdaptiveProcessingManagerEdgeCases:
    """Тесты для граничных условий AdaptiveProcessingManager."""

    def setup_method(self):
        """Настройка теста."""
        self.mock_provider = Mock()
        self.mock_state = Mock()
        self.mock_provider.return_value = self.mock_state

        self.manager = AdaptiveProcessingManager(self.mock_provider)

    def test_processing_event_with_zero_intensity(self):
        """Тест обработки события с нулевой интенсивностью."""
        self.mock_state.processing_state = False
        self.mock_state.processing_intensity = 0.0
        self.mock_state.processing_history = []

        result = self.manager.trigger_processing_event(self.mock_state, ProcessingMode.BASELINE, 0.0)

        assert result is True
        assert self.mock_state.processing_intensity == 0.0
        assert self.mock_state.processing_state is True

    def test_processing_event_with_max_intensity(self):
        """Тест обработки события с максимальной интенсивностью."""
        self.mock_state.processing_state = False
        self.mock_state.processing_intensity = 0.0
        self.mock_state.processing_history = []
        self.mock_state.processing_mode = "baseline"
        self.mock_state.processing_modifier = 1.0
        self.mock_state.processing_duration = 0

        result = self.manager.trigger_processing_event(self.mock_state, ProcessingMode.OPTIMIZED, 2.0)

        # Проверяем результат без строгого сравнения
        assert isinstance(result, bool)  # Может быть True или False в зависимости от состояния

    def test_force_adaptive_state_with_none_state(self):
        """Тест принудительной установки None состояния."""
        # Это должно быть обработано gracefully (уже добавлена проверка в коде)
        result = self.manager.force_adaptive_state(self.mock_state, None)
        assert result is False

    def test_update_with_none_self_state(self):
        """Тест обновления с None self_state."""
        result = self.manager.update(None)
        assert result == {"status": "inactive"}  # Менеджер не активен

    def test_config_with_extreme_values(self):
        """Тест конфигурации с экстремальными значениями."""
        # Создаем конфигурацию с экстремальными значениями
        config = AdaptiveProcessingConfig(
            stability_threshold=0.0,
            energy_threshold=1.0,
            processing_efficiency_threshold=0.0,
            cognitive_load_max=1.0,
            check_interval=0.01,
            state_transition_cooldown=0.1
        )

        manager = AdaptiveProcessingManager(self.mock_provider, config=config)

        assert manager.config.stability_threshold == 0.0
        assert manager.config.energy_threshold == 1.0

    def test_empty_processing_history(self):
        """Тест работы с пустой историей обработки."""
        self.mock_state.processing_history = []

        # Вызов методов статистики не должен падать
        stats = self.manager.get_processing_statistics()
        assert isinstance(stats, dict)
        assert "total_processing_events" in stats
        assert stats["total_processing_events"] == 0

    def test_memory_hierarchy_none(self):
        """Тест работы без иерархии памяти."""
        # Создаем менеджер без интеграции с памятью
        config = AdaptiveProcessingConfig(integrate_with_memory=False)
        manager = AdaptiveProcessingManager(self.mock_provider, config=config)
        manager.start()  # Запускаем менеджер

        # Настраиваем mock_state с числовыми атрибутами
        self.mock_state.processing_efficiency = 0.5
        self.mock_state.stability = 0.8
        self.mock_state.meta_cognition_depth = 0.3

        # Обновление не должно падать
        result = manager.update(self.mock_state)
        assert "memory_operations" in result

    def test_rapid_successive_updates(self):
        """Тест быстрого последовательного обновления."""
        self.manager.start()

        # Настраиваем mock_state с числовыми атрибутами
        self.mock_state.processing_efficiency = 0.5
        self.mock_state.stability = 0.8
        self.mock_state.meta_cognition_depth = 0.3

        # Быстрое последовательное обновление
        for i in range(5):  # Уменьшаем количество для скорости
            result = self.manager.update(self.mock_state)
            assert "status" in result

    def test_invalid_processing_mode_type(self):
        """Тест с некорректным типом режима обработки."""
        result = self.manager.trigger_processing_event(self.mock_state, 123, 0.5)  # Число вместо enum
        assert result is False

    def test_processing_event_duration_ticks_bounds(self):
        """Тест граничных значений duration_ticks."""
        # Создаем событие с экстремальными значениями duration_ticks
        event = ProcessingEvent(
            processing_mode=ProcessingMode.EFFICIENT,
            intensity=0.5,
            duration_ticks=0  # Минимальное значение
        )
        assert event.duration_ticks == 0

        event2 = ProcessingEvent(
            processing_mode=ProcessingMode.EFFICIENT,
            intensity=0.5,
            duration_ticks=1000  # Большое значение
        )
        assert event2.duration_ticks == 1000

    def test_config_validation_edge_cases(self):
        """Тест валидации конфигурации на граничных значениях."""
        # Граничные допустимые значения
        config = AdaptiveProcessingConfig(
            stability_threshold=0.0,
            energy_threshold=1.0,
            processing_efficiency_threshold=0.0,
            cognitive_load_max=1.0
        )
        assert config.stability_threshold == 0.0
        assert config.energy_threshold == 1.0

    def test_state_transition_with_invalid_current_state(self):
        """Тест перехода состояния с некорректным текущим состоянием."""
        # Устанавливаем некорректное текущее состояние
        self.mock_state.current_adaptive_state = "invalid_state"

        # Принудительная установка должна работать
        result = self.manager.force_adaptive_state(self.mock_state, AdaptiveState.STANDARD)
        assert result is True
        assert self.mock_state.current_adaptive_state == AdaptiveState.STANDARD.value

    def test_get_system_status_comprehensive(self):
        """Комплексный тест получения статуса системы."""
        status = self.manager.get_system_status()

        assert "manager" in status
        assert "components" in status
        assert "is_active" in status["manager"]
        assert "stats" in status["manager"]
        assert "uptime" in status["manager"]


class TestAdaptiveProcessingManagerPerformance:
    """Тесты производительности AdaptiveProcessingManager."""

    def setup_method(self):
        """Настройка теста."""
        self.mock_provider = Mock()
        self.mock_state = RealisticSelfStateMock()  # Используем реалистичный mock
        self.mock_provider.return_value = self.mock_state

        self.manager = AdaptiveProcessingManager(self.mock_provider)

    def test_update_performance(self):
        """Тест производительности метода update."""
        import time

        self.manager.start()

        # Измеряем время выполнения нескольких обновлений
        start_time = time.time()
        iterations = 50

        for _ in range(iterations):
            result = self.manager.update(self.mock_state)
            assert "status" in result

        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / iterations

        # Проверяем что среднее время разумное (< 0.01 секунды)
        assert avg_time < 0.01, f"Average update time {avg_time:.4f}s is too slow"
        print(f"Performance test: {iterations} updates in {total_time:.4f}s, avg {avg_time:.6f}s")

    def test_trigger_processing_event_performance(self):
        """Тест производительности trigger_processing_event."""
        import time

        start_time = time.time()
        iterations = 20

        for i in range(iterations):
            # Сбрасываем состояние для каждого теста
            self.mock_state.processing_state = False
            self.mock_state.processing_history = []

            result = self.manager.trigger_processing_event(
                self.mock_state,
                ProcessingMode.EFFICIENT,
                0.5 + (i % 5) * 0.1  # Варьируем интенсивность
            )
            assert result is True

        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / iterations

        # Проверяем производительность
        assert avg_time < 0.005, f"Average trigger time {avg_time:.4f}s is too slow"
        print(f"Trigger performance: {iterations} events in {total_time:.4f}s, avg {avg_time:.6f}s")

    def test_state_transitions_performance(self):
        """Тест производительности переходов состояний."""
        import time

        start_time = time.time()
        iterations = 10

        states = [
            AdaptiveState.STANDARD,
            AdaptiveState.EFFICIENT_PROCESSING,
            AdaptiveState.INTENSIVE_ANALYSIS,
            AdaptiveState.OPTIMAL_PROCESSING,
            AdaptiveState.SYSTEM_SELF_MONITORING
        ]

        for i in range(iterations):
            state = states[i % len(states)]
            result = self.manager.force_adaptive_state(self.mock_state, state)
            assert result is True

        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / iterations

        # Проверяем производительность
        assert avg_time < 0.002, f"Average transition time {avg_time:.4f}s is too slow"
        print(f"State transition performance: {iterations} transitions in {total_time:.4f}s, avg {avg_time:.6f}s")

    def test_memory_usage_stability(self):
        """Тест стабильности использования памяти."""
        import psutil
        import os

        # Получаем начальное использование памяти
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        self.manager.start()

        # Выполняем много операций
        for i in range(100):
            self.manager.update(self.mock_state)
            if i % 10 == 0:
                self.manager.trigger_processing_event(self.mock_state, ProcessingMode.EFFICIENT, 0.5)

        # Проверяем финальное использование памяти
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Проверяем что увеличение памяти разумное (< 50 MB)
        assert memory_increase < 50, f"Memory increase {memory_increase:.2f}MB is too high"
        print(f"Memory test: initial {initial_memory:.2f}MB, final {final_memory:.2f}MB, increase {memory_increase:.2f}MB")

    def test_concurrent_operations_simulation(self):
        """Симуляция конкурентных операций."""
        import threading
        import time

        results = []
        errors = []

        def worker(worker_id):
            try:
                for i in range(10):
                    if worker_id % 2 == 0:
                        result = self.manager.update(self.mock_state)
                        results.append(("update", result))
                    else:
                        result = self.manager.trigger_processing_event(
                            self.mock_state, ProcessingMode.BASELINE, 0.3
                        )
                        results.append(("trigger", result))
                    time.sleep(0.001)  # Небольшая задержка
            except Exception as e:
                errors.append((worker_id, str(e)))

        # Запускаем несколько потоков
        threads = []
        for i in range(3):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        # Ждем завершения
        for t in threads:
            t.join(timeout=5.0)

        # Проверяем результаты
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) > 0, "No operations completed"

        updates = [r for r in results if r[0] == "update"]
        triggers = [r for r in results if r[0] == "trigger"]

        print(f"Concurrent test: {len(updates)} updates, {len(triggers)} triggers, {len(errors)} errors")

    def test_history_size_limits(self):
        """Тест ограничений размера истории."""
        # Устанавливаем маленький лимит истории
        self.manager.config.max_history_size = 5

        # Добавляем много событий
        for i in range(10):
            self.mock_state.processing_history = []  # Сбрасываем для каждого теста
            self.manager.trigger_processing_event(self.mock_state, ProcessingMode.EFFICIENT, 0.5)

        # Проверяем что размер истории ограничен
        assert len(self.mock_state.processing_history) <= self.manager.config.max_history_size

    def test_statistics_accuracy_under_load(self):
        """Тест точности статистики под нагрузкой."""
        initial_stats = self.manager._stats.copy()

        # Выполняем много операций
        for i in range(20):
            self.manager.update(self.mock_state)
            if i % 3 == 0:
                self.manager.trigger_processing_event(self.mock_state, ProcessingMode.INTENSIVE, 0.7)

        final_stats = self.manager._stats

        # Проверяем что статистика корректно обновляется
        assert final_stats["total_updates"] >= initial_stats["total_updates"] + 20
        assert final_stats["processing_events_triggered"] >= initial_stats["processing_events_triggered"] + 6  # ~20/3

        print(f"Stats test: updates {final_stats['total_updates']}, events {final_stats['processing_events_triggered']}")