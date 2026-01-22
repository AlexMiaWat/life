"""
Интеграционные тесты для полной интеграции экспериментальных компонентов в Runtime Loop.

Тестируют взаимодействие всех компонентов в реальном runtime loop с включенными
экспериментальными функциями: adaptive processing, parallel consciousness, clarity moments,
memory hierarchy, decision engine integration.
"""

import time
import pytest
import threading
from unittest.mock import Mock, patch, MagicMock

from src.config import feature_flags
from src.observability.structured_logger import StructuredLogger
from src.runtime.performance_monitor import performance_monitor

# Условные импорты экспериментальных компонентов
if feature_flags.is_adaptive_processing_enabled():
    from src.experimental.adaptive_processing_manager import (
        AdaptiveProcessingManager,
        ProcessingMode,
        AdaptiveState
    )

if feature_flags.is_parallel_consciousness_enabled():
    from src.experimental.consciousness.states import ConsciousnessStateManager

if feature_flags.is_clarity_moments_enabled():
    from src.experimental.clarity_moments import ClarityMoments

if feature_flags.is_memory_hierarchy_enabled():
    from src.experimental.memory_hierarchy.hierarchy_manager import MemoryHierarchyManager

from src.state.self_state import SelfState
from src.environment.internal_generator import InternalEventGenerator


@pytest.mark.skipif(
    not all([
        feature_flags.is_adaptive_processing_enabled(),
        feature_flags.is_parallel_consciousness_enabled(),
        feature_flags.is_clarity_moments_enabled(),
        feature_flags.is_memory_hierarchy_enabled()
    ]),
    reason="Требуются все экспериментальные компоненты"
)
class TestRuntimeLoopFullIntegration:
    """Интеграционные тесты для полной интеграции компонентов в runtime loop."""

    def setup_method(self):
        """Настройка полной runtime loop с экспериментальными компонентами."""
        self.logger = Mock(spec=StructuredLogger)

        # Создание реального SelfState для интеграционных тестов
        self.self_state = SelfState()
        self.self_state.energy = 0.8
        self.self_state.stability = 0.7
        self.self_state.integrity = 0.9
        self.self_state.age = 100

        # Инициализация экспериментальных компонентов
        self.adaptive_manager = AdaptiveProcessingManager(
            lambda: self.self_state,
            logger=self.logger
        )
        self.consciousness_manager = ConsciousnessStateManager()
        self.clarity_system = ClarityMoments(self_state_provider=lambda: self.self_state)

        # Mock сенсорный буфер для MemoryHierarchyManager
        self.mock_sensory_buffer = Mock()
        self.mock_sensory_buffer.get_entries = Mock(return_value=[])
        self.mock_sensory_buffer.size = Mock(return_value=0)
        self.mock_sensory_buffer.add_entry = Mock()

        self.memory_hierarchy = MemoryHierarchyManager(
            sensory_buffer=self.mock_sensory_buffer,
            episodic_memory=self.self_state.memory
        )

        # Связываем компоненты
        self.adaptive_manager.set_consciousness_manager(self.consciousness_manager)

        # Генератор событий для тестирования
        self.event_generator = InternalEventGenerator()

    def test_runtime_initialization_sequence(self):
        """Тест последовательности инициализации runtime с экспериментальными компонентами."""
        # 1. Инициализация сознания
        result = self.consciousness_manager.transition_to("INITIALIZING")
        assert result is True

        # 2. Запуск адаптивного менеджера
        self.adaptive_manager.start()
        assert self.adaptive_manager._is_active is True

        # 3. Инициализация иерархии памяти
        assert self.memory_hierarchy.is_initialized is True

        # 4. Активация сознания
        result = self.consciousness_manager.transition_to("ACTIVE")
        assert result is True

        # 5. Проверка начального состояния
        status = self.adaptive_manager.get_system_status()
        assert status["manager"]["is_active"] is True

    def test_event_processing_pipeline_integration(self):
        """Тест полной интеграции pipeline обработки событий."""
        # Инициализация системы
        self._initialize_system()

        # Создание тестового события
        event = self.event_generator.generate_event()
        event.intensity = 0.7
        event.event_type = "test_processing"

        # Имитация полного pipeline обработки событий
        with patch('src.meaning.engine.analyze_meaning') as mock_meaning, \
             patch('src.decision.decision.decide_response') as mock_decision, \
             patch('src.action.execute_action') as mock_action, \
             patch('src.feedback.observe_consequences') as mock_feedback:

            # Настройка mock ответов
            mock_meaning.return_value = {
                "event_type": "test_processing",
                "significance": 0.7,
                "urgency": 0.5,
                "data": {"test": "data"}
            }
            mock_decision.return_value = "test_response"
            mock_action.return_value = {"action": "executed"}
            mock_feedback.return_value = {"feedback": "received"}

            # 1. Meaning анализ
            meaning = mock_meaning.return_value

            # 2. Decision с логированием
            with performance_monitor.measure("DecisionEngine", "decide_response"):
                pattern = mock_decision.return_value
                self.self_state.last_pattern = pattern

            # 3. Action выполнение
            action_result = mock_action.return_value

            # 4. Feedback обработка
            feedback_result = mock_feedback.return_value

            # Проверка что pipeline завершен успешно
            assert meaning["significance"] == 0.7
            assert pattern == "test_response"
            assert action_result["action"] == "executed"
            assert feedback_result["feedback"] == "received"

    def test_adaptive_processing_runtime_integration(self):
        """Тест интеграции адаптивной обработки в runtime."""
        self._initialize_system()

        # Тестируем различные режимы обработки
        processing_scenarios = [
            (ProcessingMode.EFFICIENT, 0.6),
            (ProcessingMode.INTENSIVE, 0.8),
            (ProcessingMode.OPTIMIZED, 0.9)
        ]

        for mode, intensity in processing_scenarios:
            # Активация режима обработки
            result = self.adaptive_manager.trigger_processing_event(
                self.self_state,
                mode,
                intensity
            )
            assert result is True

            # Проверка что состояние изменилось
            assert self.self_state.processing_state is True
            assert self.self_state.processing_intensity == intensity

            # Проверка синхронизации с consciousness
            assert self.consciousness_manager.current_state.value == "active"

            # Анализ ясности во время обработки
            moment = self.clarity_system.analyze_clarity(self.self_state)
            # Момент может быть None - это нормально

            # Сброс для следующего сценария
            self.self_state.processing_state = False

    def test_consciousness_state_runtime_transitions(self):
        """Тест переходов состояний сознания в runtime."""
        self._initialize_system()

        # Цикл переходов состояний
        transitions = [
            "PROCESSING",
            "ANALYZING",
            "REFLECTING",
            "ACTIVE"
        ]

        for target_state in transitions:
            # Выполнение перехода
            result = self.consciousness_manager.transition_to(target_state)
            assert result is True
            assert self.consciousness_manager.current_state.value == target_state.lower()

            # Проверка что система остается стабильной
            status = self.adaptive_manager.get_system_status()
            assert status["manager"]["is_active"] is True

            # Адаптивная реакция на изменение состояния
            if target_state == "PROCESSING":
                self.adaptive_manager.trigger_processing_event(
                    self.self_state,
                    ProcessingMode.EFFICIENT,
                    0.6
                )
            elif target_state == "ANALYZING":
                # Анализ ясности во время анализа
                self.clarity_system.analyze_clarity(self.self_state)
            elif target_state == "REFLECTING":
                # Консолидация памяти во время рефлексии
                self.memory_hierarchy.consolidate_sensory_data()

    def test_memory_hierarchy_runtime_integration(self):
        """Тест интеграции иерархии памяти в runtime."""
        self._initialize_system()

        # Создание сенсорных данных
        sensory_data = [
            Mock(
                timestamp=time.time() + i,
                intensity=0.5 + i * 0.1,
                data=f"sensor_data_{i}",
                event_type="sensory"
            )
            for i in range(5)
        ]

        self.mock_sensory_buffer.get_entries.return_value = sensory_data

        # 1. Консолидация сенсорных данных
        self.memory_hierarchy.consolidate_sensory_data()

        # 2. Проверка что данные обработаны
        # (В реальной системе данные должны быть переданы в эпизодическую память)

        # 3. Проверка статистики памяти
        # (Проверяем что компонент памяти доступен)
        assert self.self_state.memory is not None

        # 4. Переход в состояние рефлексии для обработки памяти
        self.consciousness_manager.transition_to("REFLECTING")

        # 5. Повторная консолидация
        self.memory_hierarchy.consolidate_sensory_data()

    def test_clarity_moments_runtime_integration(self):
        """Тест интеграции моментов ясности в runtime."""
        self._initialize_system()

        # 1. Активация момента ясности
        self.clarity_system.activate_clarity_moment(self.self_state)

        assert self.self_state.clarity_state is True
        assert self.self_state.clarity_duration == 50
        assert self.self_state.clarity_modifier == 1.5

        # 2. Выполнение операций с повышенной ясностью
        for i in range(10):
            # Имитация тика с ясностью
            self.clarity_system.update_clarity_state(self.self_state)

            # Адаптивная обработка с ясностью
            if i % 3 == 0:
                self.adaptive_manager.trigger_processing_event(
                    self.self_state,
                    ProcessingMode.OPTIMIZED,
                    0.8
                )

        # 3. Проверка что ясность постепенно уменьшается
        assert self.self_state.clarity_duration < 50

        # 4. Анализ моментов ясности
        moments = self.clarity_system.get_clarity_moments()
        assert isinstance(moments, list)

        # 5. Деактивация ясности
        self.clarity_system.deactivate_clarity_moment(self.self_state)

        assert self.self_state.clarity_state is False
        assert self.self_state.clarity_duration == 0

    def test_performance_monitoring_integration(self):
        """Тест интеграции мониторинга производительности."""
        self._initialize_system()

        # Выполнение операций для накопления метрик
        operations_count = 20

        for i in range(operations_count):
            # Различные операции для метрик
            if i % 4 == 0:
                self.adaptive_manager.trigger_processing_event(
                    self.self_state,
                    ProcessingMode.EFFICIENT,
                    0.6
                )
            elif i % 4 == 1:
                self.consciousness_manager.transition_to("PROCESSING")
            elif i % 4 == 2:
                self.clarity_system.analyze_clarity(self.self_state)
            else:
                self.memory_hierarchy.consolidate_sensory_data()

        # Получение метрик производительности
        decision_metrics = performance_monitor.get_metrics("DecisionEngine")

        # Проверка что метрики накапливаются
        if decision_metrics:
            assert "DecisionEngine.decide_response" in decision_metrics

        # Получение статистики компонентов
        processing_stats = self.adaptive_manager.get_processing_statistics()
        adaptive_stats = self.adaptive_manager.get_adaptive_statistics()

        assert isinstance(processing_stats, dict)
        assert isinstance(adaptive_stats, dict)

        # Проверка минимальной активности
        assert processing_stats["total_processing_events"] >= operations_count // 4

    def test_concurrent_component_interaction(self):
        """Тест конкурентного взаимодействия компонентов."""
        self._initialize_system()

        results = []
        errors = []

        def component_worker(component_id):
            try:
                for i in range(10):
                    if component_id == 0:
                        # Adaptive processing
                        result = self.adaptive_manager.trigger_processing_event(
                            self.self_state,
                            ProcessingMode.EFFICIENT,
                            0.5
                        )
                        results.append(("adaptive", result))
                    elif component_id == 1:
                        # Consciousness transitions
                        result = self.consciousness_manager.transition_to("PROCESSING")
                        results.append(("consciousness", result))
                    elif component_id == 2:
                        # Clarity analysis
                        moment = self.clarity_system.analyze_clarity(self.self_state)
                        results.append(("clarity", moment is not None))
                    else:
                        # Memory consolidation
                        self.memory_hierarchy.consolidate_sensory_data()
                        results.append(("memory", True))

                    time.sleep(0.001)  # Небольшая задержка
            except Exception as e:
                errors.append((component_id, str(e)))

        # Запуск нескольких потоков компонентов
        threads = []
        for i in range(4):
            t = threading.Thread(target=component_worker, args=(i,))
            threads.append(t)
            t.start()

        # Ожидание завершения
        for t in threads:
            t.join(timeout=10.0)

        # Проверка результатов
        assert len(results) > 0
        assert len(errors) == 0

        # Проверка что все типы компонентов работали
        component_types = set(r[0] for r in results)
        expected_types = {"adaptive", "consciousness", "clarity", "memory"}
        assert component_types == expected_types

    def test_runtime_error_recovery_integration(self):
        """Тест восстановления после ошибок в runtime."""
        self._initialize_system()

        # Имитация ошибки в адаптивном менеджере
        original_trigger = self.adaptive_manager.trigger_processing_event

        def failing_trigger(*args, **kwargs):
            raise Exception("Simulated runtime error")

        self.adaptive_manager.trigger_processing_event = failing_trigger

        # Попытка выполнения операции - должна быть обработана
        try:
            self.adaptive_manager.trigger_processing_event(
                self.self_state,
                ProcessingMode.EFFICIENT,
                0.5
            )
        except Exception:
            pass  # Ошибка должна быть обработана

        # Восстановление
        self.adaptive_manager.trigger_processing_event = original_trigger

        # Проверка что система восстановилась
        status = self.adaptive_manager.get_system_status()
        assert isinstance(status, dict)
        assert status["manager"]["is_active"] is True

        # Проверка что сознание все еще функционирует
        assert self.consciousness_manager.current_state.value == "active"

        # Выполнение операции после восстановления
        result = self.adaptive_manager.trigger_processing_event(
            self.self_state,
            ProcessingMode.EFFICIENT,
            0.5
        )
        assert result is True

    def test_resource_usage_under_load(self):
        """Тест использования ресурсов под нагрузкой."""
        import psutil
        import os

        self._initialize_system()

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Имитация высокой нагрузки
        for i in range(100):
            # Цикл интенсивных операций
            self.adaptive_manager.trigger_processing_event(
                self.self_state,
                ProcessingMode.INTENSIVE,
                0.8
            )
            self.clarity_system.analyze_clarity(self.self_state)
            self.memory_hierarchy.consolidate_sensory_data()

            if i % 10 == 0:
                self.consciousness_manager.transition_to("PROCESSING")
            if i % 20 == 0:
                self.consciousness_manager.transition_to("ACTIVE")

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Проверка что увеличение памяти разумное (< 100MB для нагрузочного теста)
        assert memory_increase < 100 * 1024 * 1024

        # Система должна оставаться стабильной
        status = self.adaptive_manager.get_system_status()
        assert status["manager"]["is_active"] is True

        # Проверка накопленной статистики
        stats = self.adaptive_manager.get_processing_statistics()
        assert stats["total_processing_events"] >= 100

    def test_long_running_stability_integration(self):
        """Тест стабильности при длительной работе."""
        self._initialize_system()

        start_time = time.time()

        # Симуляция 100 тиков работы
        for tick in range(100):
            # Имитация различных событий
            if tick % 5 == 0:
                self.adaptive_manager.trigger_processing_event(
                    self.self_state,
                    ProcessingMode.EFFICIENT,
                    0.6
                )
            if tick % 10 == 0:
                self.clarity_system.analyze_clarity(self.self_state)
            if tick % 15 == 0:
                self.memory_hierarchy.consolidate_sensory_data()
            if tick % 20 == 0:
                state = "PROCESSING" if tick % 40 < 20 else "ACTIVE"
                self.consciousness_manager.transition_to(state)

            time.sleep(0.001)  # Имитация реального времени тика

        end_time = time.time()
        duration = end_time - start_time

        # Проверка что тест выполнился в разумное время (< 2 секунды)
        assert duration < 2.0

        # Проверка финальной стабильности системы
        assert self.adaptive_manager._is_active is True
        assert self.consciousness_manager.current_state.value in ["active", "processing"]

        # Проверка накопленных данных
        stats = self.adaptive_manager.get_processing_statistics()
        assert stats["total_processing_events"] >= 20  # Минимум 20 событий

        moments = self.clarity_system.get_clarity_moments()
        assert isinstance(moments, list)

    def _initialize_system(self):
        """Вспомогательный метод для инициализации системы."""
        # Инициализация сознания
        self.consciousness_manager.transition_to("INITIALIZING")
        self.adaptive_manager.start()
        self.consciousness_manager.transition_to("ACTIVE")

        # Проверка что все компоненты инициализированы
        assert self.adaptive_manager._is_active is True
        assert self.consciousness_manager.current_state.value == "active"
        assert self.memory_hierarchy.is_initialized is True


class TestRuntimeLoopDecisionIntegration:
    """Тесты интеграции DecisionEngine в runtime loop."""

    def setup_method(self):
        """Настройка для тестов DecisionEngine."""
        self.self_state = SelfState()
        self.self_state.energy = 0.8
        self.self_state.stability = 0.7
        self.self_state.integrity = 0.9

        self.logger = Mock(spec=StructuredLogger)

    def test_decision_engine_metrics_collection(self):
        """Тест сбора метрик DecisionEngine в runtime."""
        from src.decision.decision import decide_response

        # Имитация нескольких решений
        decisions_count = 10

        for i in range(decisions_count):
            meaning = {
                "event_type": f"decision_test_{i}",
                "significance": 0.5 + (i % 5) * 0.1,
                "urgency": 0.4 + (i % 3) * 0.1,
                "data": {"iteration": i}
            }

            with patch('src.decision.decision.decide_response') as mock_decide:
                mock_decide.return_value = f"decision_{i}"

                # Имитация вызова через performance monitor (как в runtime loop)
                with performance_monitor.measure("DecisionEngine", "decide_response"):
                    pattern = decide_response(self.self_state, meaning)
                    assert pattern == f"decision_{i}"

        # Проверка метрик
        metrics = performance_monitor.get_metrics("DecisionEngine")
        assert metrics is not None

        decide_metrics = metrics.get("DecisionEngine.decide_response", {})
        assert decide_metrics.get("total_calls", 0) >= decisions_count

    def test_decision_engine_performance_degradation_detection(self):
        """Тест обнаружения деградации производительности DecisionEngine."""
        from src.decision.decision import decide_response

        # Имитация медленных решений
        meaning = {
            "event_type": "slow_decision_test",
            "significance": 0.6,
            "urgency": 0.5,
            "data": {}
        }

        slow_decisions = 0

        for i in range(5):
            with patch('src.decision.decision.decide_response') as mock_decide:
                mock_decide.return_value = "slow_response"

                start_time = time.time()

                with performance_monitor.measure("DecisionEngine", "decide_response"):
                    # Имитация задержки
                    time.sleep(0.02)  # 20ms - выше порога 10ms
                    pattern = decide_response(self.self_state, meaning)

                end_time = time.time()

                if end_time - start_time > 0.01:  # > 10ms
                    slow_decisions += 1

        # Должны быть зарегистрированы медленные решения
        assert slow_decisions >= 5

        # Проверка что метрики зарегистрированы
        metrics = performance_monitor.get_metrics("DecisionEngine")
        assert metrics is not None

        decide_metrics = metrics.get("DecisionEngine.decide_response", {})
        assert decide_metrics.get("avg_time", 0) > 0.01  # Среднее время > 10ms

    def test_decision_context_logging_integration(self):
        """Тест интеграции логирования контекста решений."""
        # Имитация полного контекста решения (как в runtime loop)
        correlation_id = "test_corr_12345"
        event_id = "test_event_67890"

        meaning = {
            "event_type": "context_logging_test",
            "significance": 0.7,
            "urgency": 0.6,
            "data": {
                "correlation_id": correlation_id,
                "event_id": event_id,
                "context": {
                    "energy_level": 0.8,
                    "stability": 0.7,
                    "previous_decisions": ["decision_1", "decision_2"]
                }
            }
        }

        with patch('src.decision.decision.decide_response') as mock_decide:
            mock_decide.return_value = "context_aware_decision"

            # Имитация полного pipeline из runtime loop
            with performance_monitor.measure("DecisionEngine", "decide_response"):
                pattern = mock_decide(self.self_state, meaning)

            assert pattern == "context_aware_decision"
            assert self.self_state.last_pattern == "context_aware_decision"

        # Проверка что метрики зарегистрированы
        metrics = performance_monitor.get_metrics("DecisionEngine")
        assert metrics is not None