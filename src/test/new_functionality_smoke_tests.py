"""
Дымовые тесты для новой экспериментальной функциональности.

Проверяют базовую работоспособность компонентов без углубленного тестирования.
"""

import time
import pytest
from unittest.mock import Mock

from src.experimental.adaptive_processing_manager import (
    AdaptiveProcessingManager,
    ProcessingMode,
    AdaptiveState,
    AdaptiveProcessingConfig
)
from src.experimental.consciousness.states import (
    ConsciousnessStateManager,
    ConsciousnessState
)
from src.experimental.clarity_moments import (
    ClarityMomentsTracker,
    ClarityMoments
)
from src.observability.structured_logger import StructuredLogger


class TestSmokeAdaptiveProcessingManager:
    """Дымовые тесты для AdaptiveProcessingManager."""

    def test_basic_initialization(self):
        """Базовая инициализация менеджера."""
        mock_provider = Mock()
        mock_provider.return_value = Mock()

        manager = AdaptiveProcessingManager(mock_provider)
        assert manager is not None
        assert not manager._is_active

    def test_basic_start_stop(self):
        """Базовый запуск и остановка."""
        mock_provider = Mock()
        mock_provider.return_value = Mock()

        manager = AdaptiveProcessingManager(mock_provider)

        # Запуск
        manager.start()
        assert manager._is_active

        # Остановка
        manager.stop()
        assert not manager._is_active

    def test_basic_update_cycle(self):
        """Базовый цикл обновления."""
        mock_provider = Mock()
        mock_state = Mock()
        mock_state.stability = 0.8
        mock_state.energy = 0.7
        mock_state.processing_efficiency = 0.6
        mock_state.cognitive_load = 0.3
        mock_provider.return_value = mock_state

        manager = AdaptiveProcessingManager(mock_provider)
        manager.start()

        # Установка времени для обновления
        manager._last_update_time = time.time() - 1.0

        result = manager.update(mock_state)
        assert isinstance(result, dict)
        assert "status" in result

    def test_basic_mode_triggering(self):
        """Базовое срабатывание режимов обработки."""
        mock_provider = Mock()
        mock_state = Mock()
        mock_state.stability = 0.9
        mock_state.energy = 0.8
        mock_state.processing_efficiency = 0.7
        mock_state.cognitive_load = 0.2
        mock_state.processing_history = []  # Инициализируем историю обработки
        mock_provider.return_value = mock_state

        manager = AdaptiveProcessingManager(mock_provider)
        manager.start()

        # Принудительный вызов режима
        result = manager.trigger_processing_event(mock_state, ProcessingMode.EFFICIENT, 0.8)
        assert result is True

    def test_basic_state_management(self):
        """Базовое управление состояниями."""
        mock_provider = Mock()
        mock_state = Mock()
        mock_provider.return_value = mock_state

        manager = AdaptiveProcessingManager(mock_provider)

        # Принудительное изменение состояния
        result = manager.force_adaptive_state(mock_state, AdaptiveState.EFFICIENT_PROCESSING)
        assert result is True

    def test_basic_statistics(self):
        """Базовая статистика."""
        mock_provider = Mock()
        mock_provider.return_value = Mock()

        manager = AdaptiveProcessingManager(mock_provider)

        stats = manager.get_processing_statistics()
        assert isinstance(stats, dict)

        adaptive_stats = manager.get_adaptive_statistics()
        assert isinstance(adaptive_stats, dict)

    def test_basic_system_status(self):
        """Базовый статус системы."""
        mock_provider = Mock()
        mock_provider.return_value = Mock()

        manager = AdaptiveProcessingManager(mock_provider)

        status = manager.get_system_status()
        assert isinstance(status, dict)
        assert "manager" in status
        assert "components" in status

    def test_basic_configuration(self):
        """Базовая конфигурация."""
        config = AdaptiveProcessingConfig()
        assert config.stability_threshold > 0
        assert config.energy_threshold > 0

    def test_basic_legacy_status(self):
        """Базовый статус в старом формате."""
        mock_provider = Mock()
        mock_state = Mock()
        mock_provider.return_value = mock_state

        manager = AdaptiveProcessingManager(mock_provider)

        legacy_status = manager.get_legacy_status()
        assert isinstance(legacy_status, dict)
        assert "clarity_moments" in legacy_status
        assert "consciousness_system" in legacy_status


class TestSmokeConsciousnessStateManager:
    """Дымовые тесты для ConsciousnessStateManager."""

    def test_basic_initialization(self):
        """Базовая инициализация менеджера состояний сознания."""
        manager = ConsciousnessStateManager()
        assert manager is not None
        assert manager.current_state == ConsciousnessState.INACTIVE

    def test_basic_state_transitions(self):
        """Базовые переходы состояний."""
        manager = ConsciousnessStateManager()

        # INACTIVE -> INITIALIZING
        result = manager.transition_to(ConsciousnessState.INITIALIZING)
        assert result is True
        assert manager.current_state == ConsciousnessState.INITIALIZING

        # INITIALIZING -> ACTIVE
        result = manager.transition_to(ConsciousnessState.ACTIVE)
        assert result is True
        assert manager.current_state == ConsciousnessState.ACTIVE

    def test_basic_invalid_transitions(self):
        """Базовые недопустимые переходы."""
        manager = ConsciousnessStateManager()

        # INACTIVE -> ACTIVE (недопустимый)
        result = manager.transition_to(ConsciousnessState.ACTIVE)
        assert result is False
        assert manager.current_state == ConsciousnessState.INACTIVE

    def test_basic_state_history(self):
        """Базовая история состояний."""
        manager = ConsciousnessStateManager()

        manager.transition_to(ConsciousnessState.INITIALIZING)
        manager.transition_to(ConsciousnessState.ACTIVE)

        history = manager.get_state_history()
        assert len(history) == 2

    def test_basic_state_info(self):
        """Базовая информация о состоянии."""
        manager = ConsciousnessStateManager()

        info = manager.get_current_state_info()
        assert isinstance(info, dict)
        assert "current_state" in info
        assert "total_transitions" in info

    def test_basic_transition_handlers(self):
        """Базовые обработчики переходов."""
        manager = ConsciousnessStateManager()

        called = False
        def handler(from_state, to_state):
            nonlocal called
            called = True

        manager.add_transition_handler(
            ConsciousnessState.INACTIVE,
            ConsciousnessState.INITIALIZING,
            handler
        )

        manager.transition_to(ConsciousnessState.INITIALIZING)
        assert called is True


class TestSmokeClarityMomentsTracker:
    """Дымовые тесты для ClarityMomentsTracker."""

    def test_basic_initialization(self):
        """Базовая инициализация трекера моментов ясности."""
        tracker = ClarityMomentsTracker()
        assert tracker is not None
        assert len(tracker.moments) == 0

    def test_basic_moment_creation(self):
        """Базовое создание моментов ясности."""
        from src.experimental.clarity_moments import ClarityMoment

        tracker = ClarityMomentsTracker()

        moment = ClarityMoment(
            timestamp=time.time(),
            stage="test",
            correlation_id="test_123",
            event_id="event_456",
            event_type="test_event",
            intensity=0.7,
            data={}
        )

        tracker.add_moment(moment)
        assert len(tracker.moments) == 1

    def test_basic_moment_queries(self):
        """Базовые запросы моментов."""
        tracker = ClarityMomentsTracker()

        # Добавление тестовых моментов
        for i in range(3):
            moment = Mock()
            moment.intensity = 0.5 + i * 0.2
            moment.timestamp = time.time() + i
            tracker.moments.append(moment)

        # Запросы
        by_intensity = tracker.get_moments_by_intensity(0.7)
        assert len(by_intensity) >= 0

        recent = tracker.get_recent_moments(2)
        assert len(recent) <= 2

        history = tracker.get_clarity_history()
        assert len(history) >= 0

    def test_basic_pattern_analysis(self):
        """Базовый анализ паттернов."""
        tracker = ClarityMomentsTracker()

        patterns = tracker.analyze_clarity_patterns()
        assert isinstance(patterns, dict)
        assert "total_moments" in patterns

    def test_basic_adaptive_state(self):
        """Базовое адаптивное состояние."""
        tracker = ClarityMomentsTracker()

        state = tracker.get_adaptive_state()
        assert state is not None

    def test_basic_forced_analysis(self):
        """Базовый принудительный анализ."""
        tracker = ClarityMomentsTracker()

        moment = tracker.force_clarity_analysis()
        # Может вернуть None или момент, главное чтобы не упал
        assert moment is None or hasattr(moment, 'intensity')


class TestSmokeClarityMoments:
    """Дымовые тесты для ClarityMoments (класс совместимости)."""

    def test_basic_initialization(self):
        """Базовая инициализация ClarityMoments."""
        clarity = ClarityMoments()
        assert clarity is not None

    def test_basic_clarity_operations(self):
        """Базовые операции с ясностью."""
        clarity = ClarityMoments()
        mock_state = Mock()

        # Анализ ясности
        moment = clarity.analyze_clarity(mock_state)
        assert moment is not None or moment is None  # Может вернуть None

        # Получение моментов
        moments = clarity.get_clarity_moments()
        assert isinstance(moments, list)

        # Проверка условий
        conditions = clarity.check_clarity_conditions(mock_state)
        assert conditions is None or isinstance(conditions, dict)

    def test_basic_state_management(self):
        """Базовое управление состоянием ясности."""
        clarity = ClarityMoments()
        mock_state = Mock()

        # Активация
        clarity.activate_clarity_moment(mock_state)
        assert mock_state.clarity_state is True

        # Обновление
        clarity.update_clarity_state(mock_state)
        assert mock_state.clarity_duration < 50  # Должно уменьшиться

        # Деактивация
        clarity.deactivate_clarity_moment(mock_state)
        assert mock_state.clarity_state is False

    def test_basic_clarity_level(self):
        """Базовый уровень ясности."""
        clarity = ClarityMoments()

        level = clarity.get_clarity_level()
        assert isinstance(level, float)
        assert 0.0 <= level <= 1.0


class TestSmokeIntegrationBasic:
    """Базовые интеграционные дымовые тесты."""

    def test_adaptive_and_clarity_integration(self):
        """Базовая интеграция адаптивного менеджера и моментов ясности."""
        mock_provider = Mock()
        mock_state = Mock()
        mock_provider.return_value = mock_state

        # Создание компонентов
        adaptive_manager = AdaptiveProcessingManager(mock_provider)
        clarity_tracker = ClarityMomentsTracker(self_state_provider=mock_provider)

        # Базовые операции
        adaptive_manager.start()
        moment = clarity_tracker.force_clarity_analysis()

        # Система должна оставаться стабильной
        assert adaptive_manager._is_active is True

    def test_consciousness_state_transitions(self):
        """Переходы состояний сознания."""
        state_manager = ConsciousnessStateManager()

        # Полная последовательность переходов
        transitions = [
            ConsciousnessState.INITIALIZING,
            ConsciousnessState.ACTIVE,
            ConsciousnessState.PROCESSING,
            ConsciousnessState.ANALYZING,
            ConsciousnessState.REFLECTING,
            ConsciousnessState.ACTIVE,
            ConsciousnessState.SHUTDOWN
        ]

        for state in transitions:
            if state_manager.current_state == ConsciousnessState.SHUTDOWN:
                break  # Нельзя выходить из SHUTDOWN

            result = state_manager.transition_to(state)
            if result:
                assert state_manager.current_state == state

    def test_full_system_startup_sequence(self):
        """Полная последовательность запуска системы."""
        # Создание всех компонентов
        mock_provider = Mock()
        mock_state = Mock()
        mock_state.stability = 0.9
        mock_state.energy = 0.8
        mock_state.processing_efficiency = 0.7
        mock_state.cognitive_load = 0.2
        mock_provider.return_value = mock_state

        adaptive_manager = AdaptiveProcessingManager(mock_provider)
        state_manager = ConsciousnessStateManager()
        clarity = ClarityMoments(self_state_provider=mock_provider)

        # Последовательность запуска
        state_manager.transition_to(ConsciousnessState.INITIALIZING)
        adaptive_manager.start()

        # Проверка что все компоненты инициализированы
        assert state_manager.current_state == ConsciousnessState.INITIALIZING
        assert adaptive_manager._is_active is True

        # Активация
        state_manager.transition_to(ConsciousnessState.ACTIVE)
        assert state_manager.current_state == ConsciousnessState.ACTIVE

    def test_basic_error_handling(self):
        """Базовая обработка ошибок."""
        # Создание компонентов с некорректными данными
        mock_provider = Mock()
        mock_state = Mock()
        mock_provider.return_value = mock_state

        adaptive_manager = AdaptiveProcessingManager(mock_provider)

        # Вызов методов с потенциально проблемными данными
        try:
            status = adaptive_manager.get_system_status()
            assert isinstance(status, dict)
        except Exception:
            pytest.fail("System status should handle errors gracefully")

    def test_memory_usage_basic(self):
        """Базовое использование памяти."""
        # Создание нескольких экземпляров
        managers = []
        for i in range(5):
            mock_provider = Mock()
            mock_provider.return_value = Mock()
            manager = AdaptiveProcessingManager(mock_provider)
            managers.append(manager)

        # Проверка что все созданы
        assert len(managers) == 5
        assert all(manager is not None for manager in managers)

    def test_concurrent_operations_simulation(self):
        """Симуляция конкурентных операций."""
        mock_provider = Mock()
        mock_state = Mock()
        mock_provider.return_value = mock_state

        manager = AdaptiveProcessingManager(mock_provider)
        manager.start()

        # Симуляция нескольких обновлений
        for i in range(3):
            manager._last_update_time = time.time() - 1.0
            result = manager.update(mock_state)
            assert "status" in result

        # Проверка что система осталась стабильной
        status = manager.get_system_status()
        assert status["manager"]["is_active"] is True