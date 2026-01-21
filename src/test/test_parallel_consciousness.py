"""
Тесты для многопоточной системы сознания - Parallel Consciousness Tests.

Тестирование многопоточной модели сознания с параллельными процессами.
"""

import pytest
import time
import threading
from unittest.mock import Mock, MagicMock

from src.experimental.consciousness.parallel_engine import (
    ParallelConsciousnessEngine,
    ConsciousnessSharedState,
    NeuralActivityMonitor,
    SelfReflectionProcessor,
    MetaCognitionAnalyzer,
    StateTransitionManager,
    ConsciousnessMetricsAggregator
)
from src.state.self_state import SelfState


class TestParallelConsciousnessBasic:
    """Базовые тесты многопоточной системы сознания."""

    def test_shared_state_thread_safety(self):
        """Тест потокобезопасности разделяемого состояния."""
        shared_state = ConsciousnessSharedState()

        # Функция для обновления метрик в потоке
        def update_metrics(thread_id: int):
            for i in range(100):
                shared_state.update_metric('consciousness_level', i / 100.0)
                shared_state.update_metric('self_reflection_score', (i + 10) / 100.0)
                time.sleep(0.001)  # Небольшая задержка для переключения контекста

        # Запустить несколько потоков
        threads = []
        for i in range(5):
            thread = threading.Thread(target=update_metrics, args=(i,))
            threads.append(thread)
            thread.start()

        # Дождаться завершения
        for thread in threads:
            thread.join()

        # Проверить, что состояние осталось консистентным
        snapshot = shared_state.get_metrics_snapshot()
        assert isinstance(snapshot, dict)
        assert 'consciousness_level' in snapshot
        assert 'self_reflection_score' in snapshot

    def test_parallel_engine_initialization(self):
        """Тест инициализации параллельного движка."""
        # Mock провайдеры
        self_state_provider = Mock(return_value=SelfState())
        decision_history_provider = Mock(return_value=[])
        behavior_patterns_provider = Mock(return_value=[])
        cognitive_processes_provider = Mock(return_value=[])
        optimization_history_provider = Mock(return_value=[])

        # Создать движок
        engine = ParallelConsciousnessEngine(
            self_state_provider=self_state_provider,
            decision_history_provider=decision_history_provider,
            behavior_patterns_provider=behavior_patterns_provider,
            cognitive_processes_provider=cognitive_processes_provider,
            optimization_history_provider=optimization_history_provider
        )

        # Проверить создание процессов
        assert len(engine.processes) == 5
        process_names = [p.process_name for p in engine.processes]
        expected_names = [
            'neural_activity_monitor',
            'self_reflection_processor',
            'meta_cognition_analyzer',
            'state_transition_manager',
            'consciousness_metrics_aggregator'
        ]
        assert set(process_names) == set(expected_names)

    def test_engine_start_stop(self):
        """Тест запуска и остановки движка."""
        # Создать минимальный движок
        self_state_provider = Mock(return_value=SelfState())

        engine = ParallelConsciousnessEngine(
            self_state_provider=self_state_provider
        )

        # Проверить начальное состояние
        assert not engine.is_running

        # Запустить движок
        engine.start()
        assert engine.is_running

        # Проверить, что процессы запущены
        time.sleep(0.1)  # Дать время на запуск
        alive_processes = [p for p in engine.processes if p.is_alive()]
        assert len(alive_processes) > 0

        # Остановить движок
        engine.stop()
        assert not engine.is_running

        # Проверить, что процессы остановлены
        time.sleep(0.1)  # Дать время на остановку
        alive_processes = [p for p in engine.processes if p.is_alive()]
        assert len(alive_processes) == 0

    def test_consciousness_snapshot(self):
        """Тест получения snapshot состояния сознания."""
        self_state_provider = Mock(return_value=SelfState())

        engine = ParallelConsciousnessEngine(
            self_state_provider=self_state_provider
        )

        # Запустить движок
        engine.start()
        time.sleep(0.5)  # Дать время на работу

        # Получить snapshot
        snapshot = engine.get_consciousness_snapshot()

        # Проверить структуру
        assert 'metrics' in snapshot
        assert 'processes' in snapshot
        assert 'timestamp' in snapshot
        assert 'is_running' in snapshot

        # Проверить метрики
        metrics = snapshot['metrics']
        required_metrics = ['consciousness_level', 'self_reflection_score',
                          'meta_cognition_depth', 'current_state', 'neural_activity']
        for metric in required_metrics:
            assert metric in metrics

        # Проверить статус процессов
        processes = snapshot['processes']
        assert len(processes) == 5
        for process_name, process_info in processes.items():
            assert 'is_alive' in process_info
            assert 'update_count' in process_info

        # Остановить движок
        engine.stop()

    def test_external_metrics_update(self):
        """Тест обновления внешних метрик."""
        self_state_provider = Mock(return_value=SelfState())

        engine = ParallelConsciousnessEngine(
            self_state_provider=self_state_provider
        )

        # Обновить метрики
        engine.update_external_metrics(energy=0.8, stability=0.9, cognitive_load=0.3)

        # Проверить обновление
        snapshot = engine.get_consciousness_snapshot()
        metrics = snapshot['metrics']
        assert metrics['energy_level'] == 0.8
        assert metrics['stability'] == 0.9
        assert metrics['cognitive_load'] == 0.3


class TestNeuralActivityMonitor:
    """Тесты монитора нейронной активности."""

    def test_neural_activity_calculation(self):
        """Тест расчета нейронной активности."""
        shared_state = ConsciousnessSharedState()

        # Создать mock SelfState
        mock_self_state = Mock()
        mock_self_state.tick_frequency = 5.0
        mock_self_state.event_processing_rate = 50.0
        mock_self_state.decision_complexity = 0.7

        self_state_provider = Mock(return_value=mock_self_state)

        monitor = NeuralActivityMonitor(shared_state, self_state_provider)

        # Выполнить шаг обработки
        monitor.process_step()

        # Проверить обновление метрики
        snapshot = shared_state.get_metrics_snapshot()
        neural_activity = snapshot['neural_activity']
        assert 0.0 <= neural_activity <= 1.0

    def test_monitor_with_empty_history(self):
        """Тест монитора с пустой историей."""
        shared_state = ConsciousnessSharedState()

        mock_self_state = Mock()
        mock_self_state.tick_frequency = 1.0
        mock_self_state.event_processing_rate = 10.0
        mock_self_state.decision_complexity = 0.5

        self_state_provider = Mock(return_value=mock_self_state)

        monitor = NeuralActivityMonitor(shared_state, self_state_provider)

        # Выполнить несколько шагов
        for _ in range(5):
            monitor.process_step()

        # Проверить, что метрика рассчитывается
        snapshot = shared_state.get_metrics_snapshot()
        assert snapshot['neural_activity'] >= 0.0


class TestSelfReflectionProcessor:
    """Тесты процессора саморефлексии."""

    def test_self_reflection_with_data(self):
        """Тест саморефлексии с тестовыми данными."""
        shared_state = ConsciousnessSharedState()

        # Тестовые данные
        decision_history = [
            {'success': True, 'quality': 0.8},
            {'success': False, 'quality': 0.6},
            {'success': True, 'quality': 0.9}
        ]

        behavior_patterns = [
            {'type': 'learning', 'quality': 0.7},
            {'type': 'adaptation', 'quality': 0.8}
        ]

        decision_provider = Mock(return_value=decision_history)
        behavior_provider = Mock(return_value=behavior_patterns)

        processor = SelfReflectionProcessor(
            shared_state, decision_provider, behavior_provider
        )

        # Выполнить обработку
        processor.process_step()

        # Проверить обновление метрики
        snapshot = shared_state.get_metrics_snapshot()
        self_reflection = snapshot['self_reflection_score']
        assert 0.0 <= self_reflection <= 1.0

    def test_self_reflection_empty_data(self):
        """Тест саморефлексии с пустыми данными."""
        shared_state = ConsciousnessSharedState()

        decision_provider = Mock(return_value=[])
        behavior_provider = Mock(return_value=[])

        processor = SelfReflectionProcessor(
            shared_state, decision_provider, behavior_provider
        )

        processor.process_step()

        snapshot = shared_state.get_metrics_snapshot()
        assert snapshot['self_reflection_score'] == 0.0


class TestStateTransitionManager:
    """Тесты менеджера переходов состояний."""

    def test_state_transition_logic(self):
        """Тест логики переходов состояний."""
        shared_state = ConsciousnessSharedState()

        # Установить начальные метрики
        shared_state.update_metric('consciousness_level', 0.8)
        shared_state.update_metric('energy_level', 0.9)
        shared_state.update_metric('stability', 0.9)

        manager = StateTransitionManager(shared_state)

        # Выполнить шаг обработки
        manager.process_step()

        # Проверить, что состояние обновлено
        snapshot = shared_state.get_metrics_snapshot()
        current_state = snapshot['current_state']
        assert current_state in ['awake', 'flow', 'reflective', 'meta', 'dreaming', 'unconscious']

    def test_state_transition_cooldown(self):
        """Тест cooldown между переходами."""
        shared_state = ConsciousnessSharedState()

        manager = StateTransitionManager(shared_state)

        # Первый переход
        manager.process_step()
        first_state = shared_state.get_metrics_snapshot()['current_state']

        # Немедленный второй переход (должен быть заблокирован cooldown)
        manager.process_step()
        second_state = shared_state.get_metrics_snapshot()['current_state']

        # Состояние не должно измениться из-за cooldown
        assert first_state == second_state


class TestConsciousnessMetricsAggregator:
    """Тесты агрегатора метрик."""

    def test_metrics_aggregation(self):
        """Тест агрегации метрик."""
        shared_state = ConsciousnessSharedState()

        # Установить тестовые значения
        shared_state.update_metric('neural_activity', 0.8)
        shared_state.update_metric('self_reflection_score', 0.6)
        shared_state.update_metric('meta_cognition_depth', 0.4)
        shared_state.update_metric('energy_level', 0.7)

        aggregator = ConsciousnessMetricsAggregator(shared_state)

        # Выполнить агрегацию
        aggregator.process_step()

        # Проверить расчет уровня сознания
        snapshot = shared_state.get_metrics_snapshot()
        consciousness_level = snapshot['consciousness_level']

        # Ожидаемый расчет: 0.8*0.4 + 0.6*0.3 + 0.4*0.2 + 0.7*0.1 = 0.32 + 0.18 + 0.08 + 0.07 = 0.65
        expected = 0.8 * 0.4 + 0.6 * 0.3 + 0.4 * 0.2 + 0.7 * 0.1
        assert abs(consciousness_level - expected) < 0.01


class TestParallelConsciousnessIntegration:
    """Интеграционные тесты многопоточной системы."""

    def test_full_engine_lifecycle(self):
        """Тест полного жизненного цикла движка."""
        # Создать движок с mock провайдерами
        mock_self_state = SelfState()
        mock_self_state.energy = 0.8
        mock_self_state.stability = 0.9

        self_state_provider = Mock(return_value=mock_self_state)
        decision_history_provider = Mock(return_value=[
            {'success': True, 'quality': 0.8}
        ])
        behavior_patterns_provider = Mock(return_value=[
            {'type': 'learning', 'quality': 0.7}
        ])

        engine = ParallelConsciousnessEngine(
            self_state_provider=self_state_provider,
            decision_history_provider=decision_history_provider,
            behavior_patterns_provider=behavior_patterns_provider
        )

        # Запустить движок
        engine.start()

        # Дать время на работу процессов
        time.sleep(2.0)

        # Проверить, что метрики обновляются
        snapshot = engine.get_consciousness_snapshot()
        metrics = snapshot['metrics']

        # Проверить, что все метрики имеют разумные значения
        assert 0.0 <= metrics['consciousness_level'] <= 1.0
        assert 0.0 <= metrics['self_reflection_score'] <= 1.0
        assert 0.0 <= metrics['meta_cognition_depth'] <= 1.0
        assert metrics['current_state'] in ['awake', 'flow', 'reflective', 'meta', 'dreaming', 'unconscious']

        # Проверить метрики процессов
        process_metrics = engine.get_process_metrics()
        assert len(process_metrics) == 5

        for process_name, proc_metrics in process_metrics.items():
            assert 'update_count' in proc_metrics
            assert 'average_update_time' in proc_metrics
            assert proc_metrics['update_count'] > 0

        # Остановить движок
        engine.stop()

        # Проверить остановку
        time.sleep(0.1)
        final_snapshot = engine.get_consciousness_snapshot()
        assert not final_snapshot['is_running']

    def test_engine_reset(self):
        """Тест сброса движка."""
        self_state_provider = Mock(return_value=SelfState())

        engine = ParallelConsciousnessEngine(
            self_state_provider=self_state_provider
        )

        # Запустить и остановить
        engine.start()
        time.sleep(0.5)
        engine.stop()

        # Сбросить
        engine.reset_engine()

        # Проверить, что движок готов к повторному запуску
        assert not engine.is_running
        assert len(engine.processes) == 5

        # Повторный запуск
        engine.start()
        time.sleep(0.5)
        engine.stop()

        assert not engine.is_running