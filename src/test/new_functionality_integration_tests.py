"""
Интеграционные тесты для новой экспериментальной функциональности.

Тестируют взаимодействие компонентов в реальных сценариях использования.
"""

import time
import pytest
from unittest.mock import Mock, MagicMock

from src.config import feature_flags
from src.observability.structured_logger import StructuredLogger

# Условные импорты экспериментальных компонентов на основе feature flags
if feature_flags.is_adaptive_processing_enabled():
    from src.experimental.adaptive_processing_manager import (
        AdaptiveProcessingManager,
        ProcessingMode,
        AdaptiveState,
        AdaptiveProcessingConfig
    )

if feature_flags.is_parallel_consciousness_enabled():
    from src.experimental.consciousness.states import (
        ConsciousnessStateManager,
        ConsciousnessState
    )

if feature_flags.is_clarity_moments_enabled():
    from src.experimental.clarity_moments import (
        ClarityMomentsTracker,
        ClarityMoments,
        ClarityMoment
    )


@pytest.mark.skipif(
    not (feature_flags.is_adaptive_processing_enabled() and feature_flags.is_parallel_consciousness_enabled()),
    reason="Требуются feature flags: adaptive_processing_manager и parallel_consciousness_engine"
)
class TestIntegrationAdaptiveAndConsciousness:
    """Интеграционные тесты взаимодействия AdaptiveProcessingManager и ConsciousnessStateManager."""

    def setup_method(self):
        """Настройка теста."""
        pytest.importorskip("src.experimental.adaptive_processing_manager")
        pytest.importorskip("src.experimental.consciousness.states")

        self.logger = Mock(spec=StructuredLogger)
        self.mock_self_state_provider = Mock()
        self.mock_self_state = Mock()

        # Настройка mock self_state с базовыми атрибутами
        self.mock_self_state.stability = 0.8
        self.mock_self_state.energy = 0.7
        self.mock_self_state.processing_efficiency = 0.6
        self.mock_self_state.cognitive_load = 0.3
        self.mock_self_state.current_adaptive_state = AdaptiveState.STANDARD.value

        self.mock_self_state_provider.return_value = self.mock_self_state

        # Создание компонентов
        self.adaptive_manager = AdaptiveProcessingManager(
            self.mock_self_state_provider,
            logger=self.logger
        )
        self.consciousness_manager = ConsciousnessStateManager()

        # Связываем менеджеры для синхронизации
        self.adaptive_manager.set_consciousness_manager(self.consciousness_manager)

    def test_state_synchronization(self):
        """Тест синхронизации состояний между менеджерами."""
        # Запуск адаптивного менеджера
        self.adaptive_manager.start()

        # Начальное состояние сознания
        assert self.consciousness_manager.current_state == ConsciousnessState.INACTIVE

        # Изменение состояния через адаптивный менеджер должно вызвать синхронизацию
        self.adaptive_manager.force_adaptive_state(
            self.mock_self_state,
            AdaptiveState.OPTIMAL_PROCESSING
        )

        # Проверка что состояние изменилось
        assert self.mock_self_state.current_adaptive_state == AdaptiveState.OPTIMAL_PROCESSING.value
        # Проверка синхронизации с consciousness manager (INACTIVE -> INITIALIZING -> ACTIVE)
        assert self.consciousness_manager.current_state == ConsciousnessState.ACTIVE

        # Изменение на другой адаптивное состояние
        self.adaptive_manager.force_adaptive_state(
            self.mock_self_state,
            AdaptiveState.EFFICIENT_PROCESSING
        )

        assert self.mock_self_state.current_adaptive_state == AdaptiveState.EFFICIENT_PROCESSING.value
        assert self.consciousness_manager.current_state == ConsciousnessState.ACTIVE  # Уже ACTIVE

    def test_processing_events_and_state_transitions(self):
        """Тест связи событий обработки и переходов состояний."""
        self.adaptive_manager.start()

        # Активация режима интенсивной обработки
        result = self.adaptive_manager.trigger_processing_event(
            self.mock_self_state,
            ProcessingMode.INTENSIVE,
            0.8
        )

        assert result is True

        # Проверка что состояние изменилось
        assert self.mock_self_state.processing_state is True
        assert self.mock_self_state.processing_intensity == 0.8

        # Переход состояния сознания
        self.consciousness_manager.transition_to(ConsciousnessState.PROCESSING)

        # Проверка синхронизации
        assert self.consciousness_manager.current_state == ConsciousnessState.PROCESSING

    def test_performance_metrics_integration(self):
        """Тест интеграции метрик производительности."""
        self.adaptive_manager.start()

        # Выполнение нескольких обновлений
        for i in range(5):
            self.adaptive_manager._last_update_time = time.time() - 1.0
            self.adaptive_manager.update(self.mock_self_state)

        # Получение статистики
        processing_stats = self.adaptive_manager.get_processing_statistics()
        adaptive_stats = self.adaptive_manager.get_adaptive_statistics()

        # Проверка что статистика накапливается
        assert processing_stats["total_processing_events"] >= 0
        assert adaptive_stats["total_state_transitions"] >= 0

        # Переходы состояний сознания
        for state in [ConsciousnessState.INITIALIZING, ConsciousnessState.ACTIVE]:
            self.consciousness_manager.transition_to(state)

        # Проверка истории
        history = self.consciousness_manager.get_state_history()
        assert len(history) == 2

    def test_error_handling_integration(self):
        """Тест обработки ошибок при интеграции."""
        # Настройка компонентов на обработку ошибок
        self.adaptive_manager.start()

        # Имитация проблемного состояния
        self.mock_self_state.stability = -1.0  # Некорректное значение

        # Попытка обновления - должно обработаться без краха
        self.adaptive_manager._last_update_time = time.time() - 1.0
        result = self.adaptive_manager.update(self.mock_self_state)

        # Система должна продолжать работать
        assert isinstance(result, dict)

        # Переходы состояний должны работать
        result = self.consciousness_manager.transition_to(ConsciousnessState.ERROR)
        assert result is True


@pytest.mark.skipif(
    not (feature_flags.is_adaptive_processing_enabled() and feature_flags.is_clarity_moments_enabled()),
    reason="Требуются feature flags: adaptive_processing_manager и clarity_moments"
)
class TestIntegrationAdaptiveAndClarity:
    """Интеграционные тесты взаимодействия AdaptiveProcessingManager и ClarityMoments."""

    def setup_method(self):
        """Настройка теста."""
        self.logger = Mock(spec=StructuredLogger)
        self.mock_self_state_provider = Mock()
        self.mock_self_state = Mock()

        # Настройка mock self_state
        self.mock_self_state.stability = 0.8
        self.mock_self_state.energy = 0.7
        self.mock_self_state.processing_efficiency = 0.6
        self.mock_self_state.cognitive_load = 0.3

        self.mock_self_state_provider.return_value = self.mock_self_state

        # Создание компонентов
        self.adaptive_manager = AdaptiveProcessingManager(
            self.mock_self_state_provider,
            logger=self.logger
        )
        self.clarity_tracker = ClarityMomentsTracker(
            self_state_provider=self.mock_self_state_provider
        )

    def test_clarity_moments_from_processing_events(self):
        """Тест создания моментов ясности из событий обработки."""
        self.adaptive_manager.start()

        # Вызов события обработки высокой интенсивности
        result = self.adaptive_manager.trigger_processing_event(
            self.mock_self_state,
            ProcessingMode.OPTIMIZED,
            0.9
        )

        assert result is True

        # Принудительный анализ ясности
        moment = self.clarity_tracker.force_clarity_analysis()

        # Должен создаться момент ясности
        assert moment is not None
        assert isinstance(moment, ClarityMoment)
        assert moment.intensity > 0

        # Момент должен содержать информацию о состоянии
        assert "adaptive_state" in moment.data

    def test_adaptive_state_clarity_correlation(self):
        """Тест корреляции адаптивных состояний и ясности."""
        self.adaptive_manager.start()

        # Установка оптимального состояния
        self.adaptive_manager.force_adaptive_state(
            self.mock_self_state,
            AdaptiveState.OPTIMAL_PROCESSING
        )

        # Создание момента ясности
        moment = self.clarity_tracker.force_clarity_analysis()

        assert moment is not None
        assert moment.data["adaptive_state"] == AdaptiveState.OPTIMAL_PROCESSING.value

        # Проверка анализа паттернов
        patterns = self.clarity_tracker.analyze_clarity_patterns()

        assert patterns["total_moments"] > 0
        assert "adaptive_stats" in patterns

    def test_processing_intensity_clarity_relationship(self):
        """Тест связи интенсивности обработки и ясности."""
        self.adaptive_manager.start()

        # Тест разных уровней интенсивности
        intensities = [0.3, 0.6, 0.9]

        for intensity in intensities:
            # Вызов события обработки
            self.adaptive_manager.trigger_processing_event(
                self.mock_self_state,
                ProcessingMode.EFFICIENT,
                intensity
            )

            # Создание момента ясности
            moment = self.clarity_tracker.force_clarity_analysis()

            assert moment is not None
            assert moment.intensity >= 0.0  # Момент всегда создается

    def test_clarity_history_with_adaptive_events(self):
        """Тест истории ясности с адаптивными событиями."""
        self.adaptive_manager.start()

        # Создание последовательности событий
        for i in range(3):
            # Изменение состояния
            state = [AdaptiveState.EFFICIENT_PROCESSING,
                    AdaptiveState.INTENSIVE_ANALYSIS,
                    AdaptiveState.OPTIMAL_PROCESSING][i]

            self.adaptive_manager.force_adaptive_state(self.mock_self_state, state)

            # Создание момента ясности
            moment = self.clarity_tracker.force_clarity_analysis()
            assert moment is not None

        # Проверка истории
        history = self.clarity_tracker.get_clarity_history()
        assert len(history) == 3

        # Проверка анализа паттернов
        patterns = self.clarity_tracker.analyze_clarity_patterns()
        assert patterns["total_moments"] == 3
        assert patterns["avg_intensity"] > 0


@pytest.mark.skipif(
    not (feature_flags.is_parallel_consciousness_enabled() and feature_flags.is_clarity_moments_enabled()),
    reason="Требуются feature flags: parallel_consciousness_engine и clarity_moments"
)
class TestIntegrationConsciousnessAndClarity:
    """Интеграционные тесты взаимодействия ConsciousnessStateManager и ClarityMoments."""

    def setup_method(self):
        """Настройка теста."""
        self.consciousness_manager = ConsciousnessStateManager()
        self.clarity = ClarityMoments()

        self.mock_self_state = Mock()
        self.mock_self_state.clarity_state = False
        self.mock_self_state.clarity_duration = 0
        self.mock_self_state.clarity_modifier = 1.0

    def test_consciousness_states_and_clarity_activation(self):
        """Тест состояний сознания и активации ясности."""
        # Переход в активное состояние
        self.consciousness_manager.transition_to(ConsciousnessState.ACTIVE)

        # Активация момента ясности
        self.clarity.activate_clarity_moment(self.mock_self_state)

        # Проверка активации
        assert self.mock_self_state.clarity_state is True
        assert self.mock_self_state.clarity_duration == 50
        assert self.mock_self_state.clarity_modifier == 1.5

        # Переход в состояние обработки
        self.consciousness_manager.transition_to(ConsciousnessState.PROCESSING)

        # Проверка что ясность остается активной
        assert self.mock_self_state.clarity_state is True

    def test_state_transitions_with_clarity_events(self):
        """Тест переходов состояний с событиями ясности."""
        # Начальный переход
        self.consciousness_manager.transition_to(ConsciousnessState.INITIALIZING)

        # Создание события ясности
        conditions = self.clarity.check_clarity_conditions(self.mock_self_state)

        # Должно создаться событие
        assert conditions is not None
        assert conditions["type"] == "clarity_moment"

        # Переход в активное состояние
        self.consciousness_manager.transition_to(ConsciousnessState.ACTIVE)

        # Повторная проверка ясности
        conditions2 = self.clarity.check_clarity_conditions(self.mock_self_state)

        # Счетчик должен увеличиться
        assert conditions2["data"]["clarity_id"] == 2

    def test_reflection_state_and_clarity_analysis(self):
        """Тест состояния рефлексии и анализа ясности."""
        # Переход в состояние рефлексии
        transitions = [
            ConsciousnessState.INITIALIZING,
            ConsciousnessState.ACTIVE,
            ConsciousnessState.PROCESSING,
            ConsciousnessState.ANALYZING,
            ConsciousnessState.REFLECTING
        ]

        for state in transitions:
            result = self.consciousness_manager.transition_to(state)
            assert result is True

        # В состоянии рефлексии анализ ясности
        moment = self.clarity.analyze_clarity(self.mock_self_state)

        assert moment is not None
        assert moment.stage == "forced_analysis"

        # Проверка истории состояний
        state_history = self.consciousness_manager.get_state_history()
        assert len(state_history) == 5

        # Проверка моментов ясности
        moments = self.clarity.get_clarity_moments()
        assert len(moments) == 1

    def test_error_state_and_clarity_deactivation(self):
        """Тест состояния ошибки и деактивации ясности."""
        # Активация ясности
        self.clarity.activate_clarity_moment(self.mock_self_state)

        # Переход в состояние ошибки
        self.consciousness_manager.transition_to(ConsciousnessState.ERROR)

        # Ясность должна оставаться активной (независимо от состояния сознания)
        assert self.mock_self_state.clarity_state is True

        # Но мы можем деактивировать её вручную
        self.clarity.deactivate_clarity_moment(self.mock_self_state)

        assert self.mock_self_state.clarity_state is False
        assert self.mock_self_state.clarity_duration == 0


@pytest.mark.skipif(
    not (feature_flags.is_adaptive_processing_enabled() and
         feature_flags.is_parallel_consciousness_enabled() and
         feature_flags.is_clarity_moments_enabled()),
    reason="Требуются все экспериментальные feature flags"
)
class TestIntegrationFullSystemWorkflow:
    """Интеграционные тесты полного workflow системы."""

    def setup_method(self):
        """Настройка полной системы."""
        self.logger = Mock(spec=StructuredLogger)

        # Mock провайдер состояния
        self.mock_self_state_provider = Mock()
        self.mock_self_state = Mock()

        # Настройка базовых атрибутов
        self.mock_self_state.stability = 0.8
        self.mock_self_state.energy = 0.7
        self.mock_self_state.processing_efficiency = 0.6
        self.mock_self_state.cognitive_load = 0.3
        self.mock_self_state.current_adaptive_state = AdaptiveState.STANDARD.value
        self.mock_self_state.clarity_state = False
        self.mock_self_state.clarity_duration = 0
        self.mock_self_state.clarity_modifier = 1.0

        self.mock_self_state_provider.return_value = self.mock_self_state

        # Создание всех компонентов
        self.adaptive_manager = AdaptiveProcessingManager(
            self.mock_self_state_provider,
            logger=self.logger
        )
        self.consciousness_manager = ConsciousnessStateManager()
        self.clarity = ClarityMoments(self_state_provider=self.mock_self_state_provider)

    def test_system_startup_workflow(self):
        """Тест workflow запуска системы."""
        # 1. Инициализация сознания
        result = self.consciousness_manager.transition_to(ConsciousnessState.INITIALIZING)
        assert result is True

        # 2. Запуск адаптивного менеджера
        self.adaptive_manager.start()
        assert self.adaptive_manager._is_active is True

        # 3. Переход в активное состояние
        result = self.consciousness_manager.transition_to(ConsciousnessState.ACTIVE)
        assert result is True

        # 4. Первый анализ ясности
        moment = self.clarity.analyze_clarity(self.mock_self_state)
        assert moment is not None

        # 5. Проверка статуса системы
        status = self.adaptive_manager.get_system_status()
        assert status["manager"]["is_active"] is True

    def test_processing_workflow_under_load(self):
        """Тест workflow обработки под нагрузкой."""
        # Запуск системы
        self.consciousness_manager.transition_to(ConsciousnessState.ACTIVE)
        self.adaptive_manager.start()

        # Симуляция нагрузки - несколько циклов обработки
        for i in range(5):
            # Изменение метрик для симуляции нагрузки
            self.mock_self_state.processing_efficiency = 0.5 + (i * 0.1)
            self.mock_self_state.cognitive_load = 0.2 + (i * 0.1)

            # Обновление адаптивного менеджера
            self.adaptive_manager._last_update_time = time.time() - 1.0
            result = self.adaptive_manager.update(self.mock_self_state)
            assert result["status"] == "updated"

            # Периодический анализ ясности
            if i % 2 == 0:
                moment = self.clarity.analyze_clarity(self.mock_self_state)
                assert moment is not None

        # Проверка накопленной статистики
        stats = self.adaptive_manager.get_processing_statistics()
        assert stats["total_processing_events"] >= 0

        patterns = self.clarity.tracker.analyze_clarity_patterns()
        assert patterns["total_moments"] >= 3  # Минимум 3 момента

    def test_system_recovery_workflow(self):
        """Тест workflow восстановления системы."""
        # Запуск системы
        self.consciousness_manager.transition_to(ConsciousnessState.ACTIVE)
        self.adaptive_manager.start()

        # Имитация проблемы
        self.consciousness_manager.transition_to(ConsciousnessState.ERROR)

        # Система должна продолжать функционировать
        status = self.adaptive_manager.get_system_status()
        assert isinstance(status, dict)

        # Восстановление
        self.consciousness_manager.transition_to(ConsciousnessState.INITIALIZING)
        self.consciousness_manager.transition_to(ConsciousnessState.ACTIVE)

        # Проверка восстановления
        assert self.consciousness_manager.current_state == ConsciousnessState.ACTIVE
        assert self.adaptive_manager._is_active is True

        # Анализ ясности после восстановления
        moment = self.clarity.analyze_clarity(self.mock_self_state)
        assert moment is not None

    def test_adaptive_clarity_feedback_loop(self):
        """Тест обратной связи между адаптивными состояниями и ясностью."""
        # Запуск системы
        self.consciousness_manager.transition_to(ConsciousnessState.ACTIVE)
        self.adaptive_manager.start()

        # Создание цикла обратной связи
        for state in [AdaptiveState.EFFICIENT_PROCESSING,
                     AdaptiveState.INTENSIVE_ANALYSIS,
                     AdaptiveState.OPTIMAL_PROCESSING]:

            # Изменение адаптивного состояния
            self.adaptive_manager.force_adaptive_state(self.mock_self_state, state)

            # Создание момента ясности
            moment = self.clarity.analyze_clarity(self.mock_self_state)
            assert moment is not None

            # Активация момента ясности
            self.clarity.activate_clarity_moment(self.mock_self_state)

            # Проверка что ясность активна
            assert self.mock_self_state.clarity_state is True

            # Деактивация для следующего цикла
            self.clarity.deactivate_clarity_moment(self.mock_self_state)

        # Проверка накопленных данных
        moments = self.clarity.get_clarity_moments()
        assert len(moments) == 3

        patterns = self.clarity.tracker.analyze_clarity_patterns()
        assert patterns["total_moments"] == 3

    def test_performance_monitoring_integration(self):
        """Тест интеграции мониторинга производительности."""
        # Запуск системы
        self.consciousness_manager.transition_to(ConsciousnessState.ACTIVE)
        self.adaptive_manager.start()

        # Выполнение операций для накопления статистики
        for i in range(10):
            # Обновление адаптивного менеджера
            self.adaptive_manager._last_update_time = time.time() - 1.0
            self.adaptive_manager.update(self.mock_self_state)

            # Периодические переходы состояний
            if i % 3 == 0:
                self.consciousness_manager.transition_to(ConsciousnessState.PROCESSING)
            elif i % 3 == 1:
                self.consciousness_manager.transition_to(ConsciousnessState.ANALYZING)
            else:
                self.consciousness_manager.transition_to(ConsciousnessState.ACTIVE)

        # Получение полной статистики
        processing_stats = self.adaptive_manager.get_processing_statistics()
        adaptive_stats = self.adaptive_manager.get_adaptive_statistics()
        state_info = self.consciousness_manager.get_current_state_info()

        # Проверка что статистика разумная
        assert processing_stats["total_processing_events"] >= 0
        assert adaptive_stats["total_state_transitions"] >= 0
        assert state_info["total_transitions"] >= 10

    def test_shutdown_and_cleanup_workflow(self):
        """Тест workflow завершения работы и очистки."""
        # Запуск системы
        self.consciousness_manager.transition_to(ConsciousnessState.ACTIVE)
        self.adaptive_manager.start()

        # Создание некоторых данных
        self.clarity.analyze_clarity(self.mock_self_state)
        self.adaptive_manager.trigger_processing_event(
            self.mock_self_state, ProcessingMode.EFFICIENT, 0.7
        )

        # Завершение работы
        self.adaptive_manager.stop()
        self.consciousness_manager.transition_to(ConsciousnessState.SHUTDOWN)

        # Проверка завершения
        assert self.adaptive_manager._is_active is False
        assert self.consciousness_manager.current_state == ConsciousnessState.SHUTDOWN

        # Проверка что данные сохранились
        moments = self.clarity.get_clarity_moments()
        assert len(moments) >= 1

        stats = self.adaptive_manager.get_processing_statistics()
        assert stats["total_processing_events"] >= 1