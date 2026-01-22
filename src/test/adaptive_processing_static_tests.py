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
    AdaptiveProcessingConfig,
    AdaptiveStateTransition,
    ProcessingStatistics,
    AdaptiveStatistics
)
from src.contracts.serialization_contract import SerializationContract, SerializationError
from src.observability.structured_logger import StructuredLogger


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

    def test_invalid_intensity(self):
        """Тест валидации intensity."""
        with pytest.raises(ValueError):
            ProcessingEvent(
                processing_mode=ProcessingMode.EFFICIENT,
                intensity=-0.1  # Отрицательное значение
            )

        with pytest.raises(ValueError):
            ProcessingEvent(
                processing_mode=ProcessingMode.EFFICIENT,
                intensity=1.5  # Больше 1.0
            )

    def test_invalid_duration_ticks(self):
        """Тест валидации duration_ticks."""
        with pytest.raises(ValueError):
            ProcessingEvent(
                processing_mode=ProcessingMode.EFFICIENT,
                duration_ticks=-1  # Отрицательное значение
            )


class TestAdaptiveProcessingConfig:
    """Тесты для AdaptiveProcessingConfig dataclass."""

    def test_initialization_default(self):
        """Тест инициализации с параметрами по умолчанию."""
        config = AdaptiveProcessingConfig()

        assert config.stability_threshold == 0.7
        assert config.energy_threshold == 0.6
        assert config.processing_efficiency_threshold == 0.5
        assert config.cognitive_load_threshold == 0.8
        assert config.update_interval_ticks == 10
        assert config.processing_event_timeout == 300
        assert config.adaptive_state_timeout == 600

    def test_initialization_custom(self):
        """Тест инициализации с пользовательскими параметрами."""
        config = AdaptiveProcessingConfig(
            stability_threshold=0.8,
            energy_threshold=0.7,
            processing_efficiency_threshold=0.6,
            cognitive_load_threshold=0.9,
            update_interval_ticks=20,
            processing_event_timeout=400,
            adaptive_state_timeout=800
        )

        assert config.stability_threshold == 0.8
        assert config.energy_threshold == 0.7
        assert config.processing_efficiency_threshold == 0.6
        assert config.cognitive_load_threshold == 0.9
        assert config.update_interval_ticks == 20
        assert config.processing_event_timeout == 400
        assert config.adaptive_state_timeout == 800

    def test_validation_thresholds(self):
        """Тест валидации пороговых значений."""
        # Все пороги должны быть между 0.0 и 1.0
        with pytest.raises(ValueError):
            AdaptiveProcessingConfig(stability_threshold=-0.1)

        with pytest.raises(ValueError):
            AdaptiveProcessingConfig(energy_threshold=1.5)

        with pytest.raises(ValueError):
            AdaptiveProcessingConfig(processing_efficiency_threshold=-0.5)

        with pytest.raises(ValueError):
            AdaptiveProcessingConfig(cognitive_load_threshold=2.0)

    def test_validation_timeouts(self):
        """Тест валидации таймаутов."""
        with pytest.raises(ValueError):
            AdaptiveProcessingConfig(update_interval_ticks=-1)

        with pytest.raises(ValueError):
            AdaptiveProcessingConfig(processing_event_timeout=-100)

        with pytest.raises(ValueError):
            AdaptiveProcessingConfig(adaptive_state_timeout=-200)


class TestAdaptiveStateTransition:
    """Тесты для AdaptiveStateTransition dataclass."""

    def test_initialization(self):
        """Тест инициализации AdaptiveStateTransition."""
        transition = AdaptiveStateTransition(
            from_state=AdaptiveState.STANDARD,
            to_state=AdaptiveState.EFFICIENT_PROCESSING,
            trigger_reason="high_efficiency",
            metrics={"processing_efficiency": 0.9}
        )

        assert transition.from_state == AdaptiveState.STANDARD
        assert transition.to_state == AdaptiveState.EFFICIENT_PROCESSING
        assert transition.trigger_reason == "high_efficiency"
        assert transition.metrics == {"processing_efficiency": 0.9}
        assert isinstance(transition.timestamp, float)
        assert transition.timestamp <= time.time()


class TestProcessingStatistics:
    """Тесты для ProcessingStatistics dataclass."""

    def test_initialization(self):
        """Тест инициализации ProcessingStatistics."""
        stats = ProcessingStatistics()

        assert stats.total_processing_events == 0
        assert stats.successful_events == 0
        assert stats.failed_events == 0
        assert stats.average_processing_time == 0.0
        assert stats.last_event_timestamp == 0.0
        assert stats.event_history == []

    def test_serialization(self):
        """Тест сериализации ProcessingStatistics."""
        stats = ProcessingStatistics(
            total_processing_events=10,
            successful_events=8,
            failed_events=2,
            average_processing_time=1.5,
            last_event_timestamp=1234567890.0
        )

        data = stats.to_dict()
        assert isinstance(data, dict)
        assert data["total_processing_events"] == 10
        assert data["successful_events"] == 8
        assert data["failed_events"] == 2
        assert data["average_processing_time"] == 1.5
        assert data["last_event_timestamp"] == 1234567890.0


class TestAdaptiveStatistics:
    """Тесты для AdaptiveStatistics dataclass."""

    def test_initialization(self):
        """Тест инициализации AdaptiveStatistics."""
        stats = AdaptiveStatistics()

        assert stats.total_state_transitions == 0
        assert stats.time_in_states == {}
        assert stats.transition_reasons == {}
        assert stats.average_state_duration == 0.0

    def test_serialization(self):
        """Тест сериализации AdaptiveStatistics."""
        stats = AdaptiveStatistics(
            total_state_transitions=5,
            time_in_states={"standard": 100.0, "efficient": 200.0},
            transition_reasons={"high_load": 3, "low_energy": 2},
            average_state_duration=75.0
        )

        data = stats.to_dict()
        assert isinstance(data, dict)
        assert data["total_state_transitions"] == 5
        assert data["time_in_states"] == {"standard": 100.0, "efficient": 200.0}
        assert data["transition_reasons"] == {"high_load": 3, "low_energy": 2}
        assert data["average_state_duration"] == 75.0


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
        assert manager._config is not None
        assert isinstance(manager._config, AdaptiveProcessingConfig)
        assert manager._last_update_time == 0.0
        assert manager._current_adaptive_state == AdaptiveState.STANDARD

    def test_initialization_with_logger(self):
        """Тест инициализации с логером."""
        mock_provider = Mock()
        mock_state = Mock()
        mock_provider.return_value = mock_state

        mock_logger = Mock(spec=StructuredLogger)

        manager = AdaptiveProcessingManager(mock_provider, logger=mock_logger)

        assert manager._logger == mock_logger

    def test_initialization_with_config(self):
        """Тест инициализации с кастомной конфигурацией."""
        mock_provider = Mock()
        mock_state = Mock()
        mock_provider.return_value = mock_state

        config = AdaptiveProcessingConfig(
            stability_threshold=0.8,
            update_interval_ticks=20
        )

        manager = AdaptiveProcessingManager(mock_provider, config=config)

        assert manager._config.stability_threshold == 0.8
        assert manager._config.update_interval_ticks == 20


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

    def test_force_adaptive_state_invalid_input(self):
        """Тест принудительной установки состояния - некорректный ввод."""
        # None состояние
        result = self.manager.force_adaptive_state(self.mock_state, None)
        assert result is False

        # Некорректный тип состояния
        result = self.manager.force_adaptive_state(self.mock_state, "invalid_state")
        assert result is False

    def test_get_current_adaptive_state(self):
        """Тест получения текущего адаптивного состояния."""
        state = self.manager.get_current_adaptive_state()
        assert state == AdaptiveState.STANDARD

        # Изменяем состояние
        self.manager.force_adaptive_state(self.mock_state, AdaptiveState.OPTIMAL_PROCESSING)
        state = self.manager.get_current_adaptive_state()
        assert state == AdaptiveState.OPTIMAL_PROCESSING


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

    def test_trigger_processing_event_invalid_intensity(self):
        """Тест срабатывания события с некорректной интенсивностью."""
        result = self.manager.trigger_processing_event(
            self.mock_state,
            ProcessingMode.EFFICIENT,
            -0.1  # Некорректная интенсивность
        )

        assert result is False

        result = self.manager.trigger_processing_event(
            self.mock_state,
            ProcessingMode.EFFICIENT,
            1.5  # Некорректная интенсивность
        )

        assert result is False


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
        assert "successful_events" in stats
        assert "failed_events" in stats
        assert stats["total_processing_events"] == 0

    def test_get_adaptive_statistics_initial(self):
        """Тест получения начальной адаптивной статистики."""
        stats = self.manager.get_adaptive_statistics()

        assert isinstance(stats, dict)
        assert "total_state_transitions" in stats
        assert "time_in_states" in stats
        assert "transition_reasons" in stats
        assert stats["total_state_transitions"] == 0


class TestAdaptiveProcessingManagerSystemStatus:
    """Тесты статуса системы AdaptiveProcessingManager."""

    def setup_method(self):
        """Настройка теста."""
        self.mock_provider = Mock()
        self.mock_state = Mock()
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


class TestSerializationContract:
    """Тесты сериализации компонентов."""

    def setup_method(self):
        """Настройка теста."""
        self.contract = SerializationContract()

    def test_processing_event_serialization(self):
        """Тест сериализации ProcessingEvent."""
        event = ProcessingEvent(
            processing_mode=ProcessingMode.EFFICIENT,
            intensity=0.8,
            duration_ticks=100,
            trigger_conditions={"test": "value"}
        )

        # Сериализация
        data = self.contract.serialize(event)
        assert isinstance(data, dict)
        assert "processing_mode" in data
        assert "intensity" in data
        assert "duration_ticks" in data

        # Десериализация
        restored = self.contract.deserialize(data, ProcessingEvent)
        assert isinstance(restored, ProcessingEvent)
        assert restored.processing_mode == event.processing_mode
        assert restored.intensity == event.intensity

    def test_adaptive_config_serialization(self):
        """Тест сериализации AdaptiveProcessingConfig."""
        config = AdaptiveProcessingConfig(
            stability_threshold=0.8,
            energy_threshold=0.7
        )

        # Сериализация
        data = self.contract.serialize(config)
        assert isinstance(data, dict)
        assert "stability_threshold" in data
        assert "energy_threshold" in data

        # Десериализация
        restored = self.contract.deserialize(data, AdaptiveProcessingConfig)
        assert isinstance(restored, AdaptiveProcessingConfig)
        assert restored.stability_threshold == config.stability_threshold
        assert restored.energy_threshold == config.energy_threshold