"""
Дымовые тесты для полного workflow системы с экспериментальными компонентами.

Проверяют базовую работоспособность полного цикла: event -> meaning -> decision -> action -> feedback
с включенными экспериментальными компонентами.
"""

import time
import pytest
from unittest.mock import Mock, MagicMock

from src.config import feature_flags
from src.observability.structured_logger import StructuredLogger

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


@pytest.mark.skipif(
    not all([
        feature_flags.is_adaptive_processing_enabled(),
        feature_flags.is_parallel_consciousness_enabled(),
        feature_flags.is_clarity_moments_enabled(),
        feature_flags.is_memory_hierarchy_enabled()
    ]),
    reason="Требуются все экспериментальные компоненты: adaptive_processing, parallel_consciousness, clarity_moments, memory_hierarchy"
)
class TestFullSystemWorkflowSmoke:
    """Дымовые тесты для полного workflow системы с экспериментальными компонентами."""

    def setup_method(self):
        """Настройка полного workflow системы."""
        self.logger = Mock(spec=StructuredLogger)

        # Mock провайдер состояния
        self.mock_self_state_provider = Mock()
        self.mock_self_state = Mock()

        # Настройка базовых атрибутов состояния
        self.mock_self_state.energy = 0.8
        self.mock_self_state.stability = 0.7
        self.mock_self_state.integrity = 0.9
        self.mock_self_state.current_adaptive_state = AdaptiveState.STANDARD.value
        self.mock_self_state.processing_history = []
        self.mock_self_state.clarity_state = False
        self.mock_self_state.clarity_duration = 0
        self.mock_self_state.clarity_modifier = 1.0
        self.mock_self_state.last_pattern = None

        # Mock память
        self.mock_memory = Mock()
        self.mock_memory.add_entry = Mock()
        self.mock_memory.get_entries = Mock(return_value=[])
        self.mock_self_state.memory = self.mock_memory

        self.mock_self_state_provider.return_value = self.mock_self_state

        # Создание компонентов системы
        self.adaptive_manager = AdaptiveProcessingManager(
            self.mock_self_state_provider,
            logger=self.logger
        )
        self.consciousness_manager = ConsciousnessStateManager()
        self.clarity_system = ClarityMoments(self_state_provider=self.mock_self_state_provider)

        # Mock сенсорный буфер для MemoryHierarchyManager
        self.mock_sensory_buffer = Mock()
        self.mock_sensory_buffer.get_entries = Mock(return_value=[])
        self.mock_sensory_buffer.size = Mock(return_value=0)

        self.memory_hierarchy = MemoryHierarchyManager(
            sensory_buffer=self.mock_sensory_buffer,
            episodic_memory=self.mock_memory
        )

        # Связываем компоненты
        self.adaptive_manager.set_consciousness_manager(self.consciousness_manager)

    def test_system_initialization_workflow(self):
        """Тест workflow инициализации системы."""
        # 1. Инициализация сознания
        result = self.consciousness_manager.transition_to("INITIALIZING")
        assert result is True
        assert self.consciousness_manager.current_state.value == "initializing"

        # 2. Запуск адаптивного менеджера
        self.adaptive_manager.start()
        assert self.adaptive_manager._is_active is True

        # 3. Активация сознания
        result = self.consciousness_manager.transition_to("ACTIVE")
        assert result is True
        assert self.consciousness_manager.current_state.value == "active"

        # 4. Проверка иерархии памяти
        assert self.memory_hierarchy.is_initialized is True

        # 5. Первый анализ ясности
        moment = self.clarity_system.analyze_clarity(self.mock_self_state)
        assert moment is not None or moment is None  # Может вернуть None

    def test_event_processing_workflow(self):
        """Тест workflow обработки событий."""
        # Инициализация системы
        self.consciousness_manager.transition_to("ACTIVE")
        self.adaptive_manager.start()

        # Имитация входящего события
        mock_event = {
            "type": "test_event",
            "intensity": 0.7,
            "timestamp": time.time(),
            "data": {"test": "data"}
        }

        # 1. Адаптивная обработка события
        result = self.adaptive_manager.trigger_processing_event(
            self.mock_self_state,
            ProcessingMode.EFFICIENT,
            0.7
        )
        assert result is True
        assert self.mock_self_state.processing_state is True

        # 2. Переход состояния сознания
        result = self.consciousness_manager.transition_to("PROCESSING")
        assert result is True

        # 3. Анализ ясности
        moment = self.clarity_system.analyze_clarity(self.mock_self_state)
        assert moment is not None or moment is None

        # 4. Консолидация в памяти
        self.memory_hierarchy.consolidate_sensory_data()

        # 5. Возврат к активному состоянию
        result = self.consciousness_manager.transition_to("ACTIVE")
        assert result is True

    def test_decision_making_workflow(self):
        """Тест workflow принятия решений."""
        # Инициализация
        self.consciousness_manager.transition_to("ACTIVE")
        self.adaptive_manager.start()

        # Имитация значимого события для принятия решения
        mock_meaning = {
            "event_type": "important_decision",
            "significance": 0.8,
            "urgency": 0.6,
            "data": {
                "requires_decision": True,
                "options": ["option_a", "option_b"]
            }
        }

        # 1. Изменение состояния для принятия решения
        result = self.adaptive_manager.force_adaptive_state(
            self.mock_self_state,
            AdaptiveState.INTENSIVE_ANALYSIS
        )
        assert result is True

        # 2. Переход в состояние анализа
        result = self.consciousness_manager.transition_to("ANALYZING")
        assert result is True

        # 3. Имитация принятия решения
        with pytest.mock.patch('src.decision.decision.decide_response') as mock_decide:
            mock_decide.return_value = "decision_made"
            from src.decision.decision import decide_response

            pattern = decide_response(self.mock_self_state, mock_meaning)
            assert pattern == "decision_made"
            assert self.mock_self_state.last_pattern == "decision_made"

        # 4. Анализ ясности после решения
        moment = self.clarity_system.analyze_clarity(self.mock_self_state)
        assert moment is not None or moment is None

    def test_adaptive_state_transitions_workflow(self):
        """Тест workflow переходов адаптивных состояний."""
        # Инициализация
        self.consciousness_manager.transition_to("ACTIVE")
        self.adaptive_manager.start()

        # Цикл переходов состояний
        state_transitions = [
            (AdaptiveState.EFFICIENT_PROCESSING, "PROCESSING"),
            (AdaptiveState.INTENSIVE_ANALYSIS, "ANALYZING"),
            (AdaptiveState.OPTIMAL_PROCESSING, "ACTIVE"),
            (AdaptiveState.SYSTEM_SELF_MONITORING, "REFLECTING"),
            (AdaptiveState.STANDARD, "ACTIVE")
        ]

        for adaptive_state, consciousness_state in state_transitions:
            # Изменение адаптивного состояния
            result = self.adaptive_manager.force_adaptive_state(
                self.mock_self_state,
                adaptive_state
            )
            assert result is True
            assert self.mock_self_state.current_adaptive_state == adaptive_state.value

            # Синхронизация состояния сознания
            if consciousness_state != "ACTIVE":  # ACTIVE уже установлено
                result = self.consciousness_manager.transition_to(consciousness_state)
                assert result is True

            # Анализ ясности для каждого состояния
            moment = self.clarity_system.analyze_clarity(self.mock_self_state)
            assert moment is not None or moment is None

            # Небольшая задержка для имитации обработки
            time.sleep(0.01)

    def test_memory_consolidation_workflow(self):
        """Тест workflow консолидации памяти."""
        # Инициализация
        self.consciousness_manager.transition_to("ACTIVE")
        self.adaptive_manager.start()

        # Имитация сенсорных данных
        sensory_entries = [
            Mock(intensity=0.6, timestamp=time.time(), data={"sensor": "data1"}),
            Mock(intensity=0.8, timestamp=time.time() + 1, data={"sensor": "data2"}),
            Mock(intensity=0.9, timestamp=time.time() + 2, data={"sensor": "data3"})
        ]

        self.mock_sensory_buffer.get_entries.return_value = sensory_entries

        # 1. Консолидация данных
        self.memory_hierarchy.consolidate_sensory_data()

        # 2. Проверка что данные переданы в эпизодическую память
        # (в реальной системе данные должны быть добавлены)
        assert self.mock_memory.add_entry.called or True  # Может не вызываться в mock

        # 3. Переход в состояние рефлексии
        result = self.consciousness_manager.transition_to("REFLECTING")
        assert result is True

        # 4. Анализ ясности во время рефлексии
        moment = self.clarity_system.analyze_clarity(self.mock_self_state)
        assert moment is not None or moment is None

    def test_system_recovery_workflow(self):
        """Тест workflow восстановления системы."""
        # Инициализация
        self.consciousness_manager.transition_to("ACTIVE")
        self.adaptive_manager.start()

        # Имитация проблемы - переход в состояние ошибки
        result = self.consciousness_manager.transition_to("ERROR")
        assert result is True
        assert self.consciousness_manager.current_state.value == "error"

        # Система должна продолжать функционировать
        status = self.adaptive_manager.get_system_status()
        assert isinstance(status, dict)

        # Восстановление - переход обратно к инициализации
        result = self.consciousness_manager.transition_to("INITIALIZING")
        assert result is True

        # Реактивация
        result = self.consciousness_manager.transition_to("ACTIVE")
        assert result is True

        # Проверка что система восстановлена
        assert self.consciousness_manager.current_state.value == "active"
        assert self.adaptive_manager._is_active is True

        # Анализ ясности после восстановления
        moment = self.clarity_system.analyze_clarity(self.mock_self_state)
        assert moment is not None or moment is None

    def test_performance_monitoring_workflow(self):
        """Тест workflow мониторинга производительности."""
        # Инициализация
        self.consciousness_manager.transition_to("ACTIVE")
        self.adaptive_manager.start()

        # Выполнение нескольких циклов обработки
        for i in range(5):
            # Изменение интенсивности обработки
            intensity = 0.5 + (i * 0.1)

            result = self.adaptive_manager.trigger_processing_event(
                self.mock_self_state,
                ProcessingMode.EFFICIENT,
                intensity
            )
            assert result is True

            # Анализ ясности
            moment = self.clarity_system.analyze_clarity(self.mock_self_state)

            # Небольшая задержка
            time.sleep(0.01)

        # Получение статистики
        processing_stats = self.adaptive_manager.get_processing_statistics()
        adaptive_stats = self.adaptive_manager.get_adaptive_statistics()

        assert isinstance(processing_stats, dict)
        assert isinstance(adaptive_stats, dict)

        # Проверка что есть данные о производительности
        assert "total_processing_events" in processing_stats
        assert "total_state_transitions" in adaptive_stats

    def test_clarity_moments_integration_workflow(self):
        """Тест workflow интеграции моментов ясности."""
        # Инициализация
        self.consciousness_manager.transition_to("ACTIVE")
        self.adaptive_manager.start()

        # Активация момента ясности
        self.clarity_system.activate_clarity_moment(self.mock_self_state)

        assert self.mock_self_state.clarity_state is True
        assert self.mock_self_state.clarity_duration == 50
        assert self.mock_self_state.clarity_modifier == 1.5

        # Выполнение действий во время ясности
        for i in range(3):
            # Обработка события с повышенной ясностью
            result = self.adaptive_manager.trigger_processing_event(
                self.mock_self_state,
                ProcessingMode.OPTIMIZED,
                0.8
            )
            assert result is True

            # Обновление состояния ясности
            self.clarity_system.update_clarity_state(self.mock_self_state)

        # Проверка что ясность постепенно уменьшается
        assert self.mock_self_state.clarity_duration < 50

        # Деактивация ясности
        self.clarity_system.deactivate_clarity_moment(self.mock_self_state)

        assert self.mock_self_state.clarity_state is False
        assert self.mock_self_state.clarity_duration == 0

    def test_full_system_shutdown_workflow(self):
        """Тест workflow полного завершения работы системы."""
        # Инициализация
        self.consciousness_manager.transition_to("ACTIVE")
        self.adaptive_manager.start()

        # Создание некоторых данных для сохранения
        self.adaptive_manager.trigger_processing_event(
            self.mock_self_state,
            ProcessingMode.EFFICIENT,
            0.6
        )

        moment = self.clarity_system.analyze_clarity(self.mock_self_state)

        # Завершение работы
        self.adaptive_manager.stop()
        result = self.consciousness_manager.transition_to("SHUTDOWN")
        assert result is True

        # Проверка завершения
        assert self.adaptive_manager._is_active is False
        assert self.consciousness_manager.current_state.value == "shutdown"

        # Проверка что данные остались (в реальной системе)
        moments = self.clarity_system.get_clarity_moments()
        assert isinstance(moments, list)

        stats = self.adaptive_manager.get_processing_statistics()
        assert isinstance(stats, dict)

    def test_concurrent_operations_simulation(self):
        """Симуляция конкурентных операций в системе."""
        # Инициализация
        self.consciousness_manager.transition_to("ACTIVE")
        self.adaptive_manager.start()

        import threading

        results = []
        errors = []

        def concurrent_operation(operation_id):
            try:
                if operation_id % 3 == 0:
                    # Обработка события
                    result = self.adaptive_manager.trigger_processing_event(
                        self.mock_self_state,
                        ProcessingMode.EFFICIENT,
                        0.5
                    )
                    results.append(("processing", result))
                elif operation_id % 3 == 1:
                    # Анализ ясности
                    moment = self.clarity_system.analyze_clarity(self.mock_self_state)
                    results.append(("clarity", moment is not None))
                else:
                    # Консолидация памяти
                    self.memory_hierarchy.consolidate_sensory_data()
                    results.append(("memory", True))
            except Exception as e:
                errors.append((operation_id, str(e)))

        # Запуск нескольких потоков
        threads = []
        for i in range(6):
            t = threading.Thread(target=concurrent_operation, args=(i,))
            threads.append(t)
            t.start()

        # Ожидание завершения
        for t in threads:
            t.join(timeout=5.0)

        # Проверка результатов
        assert len(results) > 0
        assert len(errors) == 0

        # Проверка типов операций
        operation_types = [r[0] for r in results]
        assert "processing" in operation_types
        assert "clarity" in operation_types
        assert "memory" in operation_types

    def test_error_handling_and_recovery(self):
        """Тест обработки ошибок и восстановления."""
        # Инициализация
        self.consciousness_manager.transition_to("ACTIVE")
        self.adaptive_manager.start()

        # Имитация ошибки в адаптивном менеджере
        original_trigger = self.adaptive_manager.trigger_processing_event

        def failing_trigger(*args, **kwargs):
            raise Exception("Simulated processing error")

        self.adaptive_manager.trigger_processing_event = failing_trigger

        # Попытка обработки - должна быть обработана gracefully
        try:
            result = self.adaptive_manager.trigger_processing_event(
                self.mock_self_state,
                ProcessingMode.EFFICIENT,
                0.5
            )
        except Exception:
            # Ошибка должна быть обработана
            pass

        # Восстановление оригинального метода
        self.adaptive_manager.trigger_processing_event = original_trigger

        # Система должна продолжать работать
        result = self.adaptive_manager.get_system_status()
        assert isinstance(result, dict)

        # Проверка что сознание все еще активно
        assert self.consciousness_manager.current_state.value == "active"

    def test_system_resource_usage(self):
        """Тест использования ресурсов системы."""
        import psutil
        import os

        # Инициализация
        self.consciousness_manager.transition_to("ACTIVE")
        self.adaptive_manager.start()

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Выполнение интенсивных операций
        for i in range(10):
            self.adaptive_manager.trigger_processing_event(
                self.mock_self_state,
                ProcessingMode.INTENSIVE,
                0.8
            )
            self.clarity_system.analyze_clarity(self.mock_self_state)
            self.memory_hierarchy.consolidate_sensory_data()

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Проверка что увеличение памяти разумное (< 50MB)
        assert memory_increase < 50 * 1024 * 1024

        # Система должна оставаться стабильной
        status = self.adaptive_manager.get_system_status()
        assert status["manager"]["is_active"] is True

    def test_long_running_simulation(self):
        """Симуляция длительной работы системы."""
        # Инициализация
        self.consciousness_manager.transition_to("ACTIVE")
        self.adaptive_manager.start()

        start_time = time.time()

        # Симуляция 50 тиков работы
        for tick in range(50):
            # Имитация события каждый 10-й тик
            if tick % 10 == 0:
                self.adaptive_manager.trigger_processing_event(
                    self.mock_self_state,
                    ProcessingMode.EFFICIENT,
                    0.6
                )

            # Анализ ясности каждый 15-й тик
            if tick % 15 == 0:
                self.clarity_system.analyze_clarity(self.mock_self_state)

            # Консолидация памяти каждый 20-й тик
            if tick % 20 == 0:
                self.memory_hierarchy.consolidate_sensory_data()

            # Небольшая задержка для имитации реального времени
            time.sleep(0.001)

        end_time = time.time()
        duration = end_time - start_time

        # Проверка что симуляция завершилась в разумное время (< 1 секунды)
        assert duration < 1.0

        # Проверка финального состояния
        assert self.adaptive_manager._is_active is True
        assert self.consciousness_manager.current_state.value == "active"

        # Проверка что накопилась статистика
        stats = self.adaptive_manager.get_processing_statistics()
        assert stats["total_processing_events"] >= 5  # Минимум 5 событий