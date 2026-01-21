"""
Интеграционные тесты для observability с runtime системой

Проверяем:
- Интеграцию observability компонентов в runtime loop
- Совместную работу с SelfState и существующими компонентами
- Производительность при работе с реальными данными
- Корректность сбора данных в условиях runtime
"""

import sys
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.observability.state_tracker import StateTracker
from src.observability.component_monitor import ComponentMonitor
from src.observability.data_collector import DataCollector
from src.state.self_state import SelfState


@pytest.mark.integration
class TestObservabilityRuntimeIntegration:
    """Интеграционные тесты observability с runtime"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.temp_files = []

    def teardown_method(self):
        """Очистка после каждого теста"""
        for temp_file in self.temp_files:
            Path(temp_file).unlink(missing_ok=True)

    def create_temp_file(self, suffix='.jsonl'):
        """Создание временного файла"""
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            temp_path = f.name
        self.temp_files.append(temp_path)
        return temp_path

    def create_real_self_state(self):
        """Создание реального SelfState с компонентами"""
        self_state = SelfState()

        # Настраиваем базовые параметры
        self_state.energy = 0.8
        self_state.stability = 0.7
        self_state.integrity = 0.9
        self_state.fatigue = 0.2
        self_state.tension = 0.3
        self_state.age = 100.0
        self_state.subjective_time = 95.0
        self_state.ticks = 50

        # Счетчики компонентов
        self_state.action_count = 25
        self_state.decision_count = 15
        self_state.feedback_count = 10

        # Память
        from src.memory.memory import MemoryEntry
        episodic_memory = [
            MemoryEntry(event_type="test_event", content={"test": "data"}, timestamp=time.time())
            for _ in range(10)
        ]
        self_state.memory.episodic_memory = episodic_memory
        self_state.memory.recent_events = [{"event": f"event_{i}"} for i in range(5)]

        # Learning engine
        from src.learning.learning import LearningEngine
        learning_engine = LearningEngine()
        learning_engine.params = {"lr": 0.01, "epochs": 100, "threshold": 0.5}
        learning_engine.operation_count = 20
        self_state.learning_engine = learning_engine

        # Adaptation manager
        from src.adaptation.adaptation import AdaptationManager
        adaptation_manager = AdaptationManager()
        adaptation_manager.params = {"rate": 0.1, "window": 10, "sensitivity": 0.8}
        adaptation_manager.operation_count = 15
        self_state.adaptation_manager = adaptation_manager

        # Decision engine
        from src.decision.decision import DecisionEngine
        decision_engine = DecisionEngine()
        decision_engine.decision_queue = [Mock() for _ in range(3)]
        decision_engine.operation_count = 12
        self_state.decision_engine = decision_engine

        # Action executor
        from src.action.action import ActionExecutor
        action_executor = ActionExecutor()
        action_executor.action_queue = [Mock() for _ in range(2)]
        action_executor.operation_count = 18
        self_state.action_executor = action_executor

        return self_state

    def test_full_observability_integration_with_runtime(self):
        """Полная интеграция observability с runtime компонентами"""
        # Создаем компоненты observability
        state_tracker = StateTracker()
        component_monitor = ComponentMonitor()
        data_collector = DataCollector(storage_path=self.create_temp_file())

        # Создаем реальный SelfState
        self_state = self.create_real_self_state()

        # Выполняем сбор данных (как в runtime loop)
        state_snapshot = state_tracker.collect_state_data(self_state)
        component_stats = component_monitor.collect_component_stats(self_state)

        # Сохраняем данные
        data_collector.collect_state_data(state_snapshot)
        data_collector.collect_component_data(component_stats)
        data_collector.flush()

        # Проверяем корректность собранных данных
        assert state_snapshot.energy == 0.8
        assert state_snapshot.memory_size == 10  # episodic_memory
        assert state_snapshot.recent_events_count == 5
        assert state_snapshot.learning_params_count == 3
        assert state_snapshot.adaptation_params_count == 3

        assert component_stats.memory_episodic_size == 10
        assert component_stats.learning_params_count == 3
        assert component_stats.adaptation_operations == 15
        assert component_stats.decision_queue_size == 3
        assert component_stats.action_queue_size == 2

        # Проверяем сохранение данных
        state_data = data_collector.get_recent_data(data_type="state")
        component_data = data_collector.get_recent_data(data_type="component")

        assert len(state_data) == 1
        assert len(component_data) == 1

        # Проверяем что данные соответствуют snapshot
        saved_state = state_data[0]
        assert saved_state.data['energy'] == 0.8
        assert saved_state.data['memory_size'] == 10

        saved_component = component_data[0]
        assert saved_component.data['memory_episodic_size'] == 10
        assert saved_component.data['learning_operations'] == 20

    def test_observability_during_runtime_simulation(self):
        """Тестирование observability во время симуляции runtime"""
        # Создаем компоненты
        state_tracker = StateTracker()
        component_monitor = ComponentMonitor()
        data_collector = DataCollector(storage_path=self.create_temp_file())

        self_state = self.create_real_self_state()

        # Симулируем несколько тиков runtime
        snapshots_collected = []
        stats_collected = []

        for tick in range(5):
            # Имитируем изменения состояния
            self_state.energy = 0.8 - tick * 0.05  # постепенное снижение энергии
            self_state.ticks = 50 + tick

            # Добавляем записи в память
            from src.memory.memory import MemoryEntry
            new_entry = MemoryEntry(
                event_type=f"tick_event_{tick}",
                content={"tick": tick},
                timestamp=time.time()
            )
            self_state.memory.episodic_memory.append(new_entry)

            # Сбор данных observability
            snapshot = state_tracker.collect_state_data(self_state)
            stats = component_monitor.collect_component_stats(self_state)

            snapshots_collected.append(snapshot)
            stats_collected.append(stats)

            # Сохранение
            data_collector.collect_state_data(snapshot)
            data_collector.collect_component_data(stats)

        # Принудительный сброс буфера
        data_collector.flush()

        # Проверяем что данные собирались на каждом тике
        assert len(snapshots_collected) == 5
        assert len(stats_collected) == 5

        # Проверяем постепенное изменение данных
        for i in range(5):
            assert snapshots_collected[i].energy == 0.8 - i * 0.05
            assert snapshots_collected[i].ticks == 50 + i
            assert snapshots_collected[i].memory_size == 10 + i  # базовые 10 + добавленные

        # Проверяем сохранение всех данных
        all_data = data_collector.get_recent_data()
        assert len(all_data) == 10  # 5 state + 5 component

        # Проверяем сортировку (последние данные первыми)
        state_data = [d for d in all_data if d.data_type == "state"]
        assert len(state_data) == 5
        # Первый элемент должен иметь максимальную энергию (первый тик)
        assert state_data[0].data['energy'] == 0.8

    def test_observability_performance_under_load(self):
        """Тестирование производительности observability под нагрузкой"""
        state_tracker = StateTracker()
        component_monitor = ComponentMonitor()
        data_collector = DataCollector(storage_path=self.create_temp_file())

        self_state = self.create_real_self_state()

        # Измеряем время сбора данных при многократном вызове
        iterations = 100
        start_time = time.time()

        for _ in range(iterations):
            snapshot = state_tracker.collect_state_data(self_state)
            stats = component_monitor.collect_component_stats(self_state)
            data_collector.collect_state_data(snapshot)
            data_collector.collect_component_data(stats)

        end_time = time.time()
        total_time = end_time - start_time
        avg_time_per_iteration = total_time / iterations

        # Проверяем что среднее время разумное (< 0.005 сек на итерацию)
        assert avg_time_per_iteration < 0.005

        # Проверяем что все данные собраны
        data_collector.flush()
        all_data = data_collector.get_recent_data()
        assert len(all_data) == iterations * 2  # state + component для каждой итерации

    def test_observability_with_concurrent_runtime(self):
        """Тестирование observability с имитацией concorrency"""
        state_tracker = StateTracker()
        component_monitor = ComponentMonitor()
        data_collector = DataCollector(storage_path=self.create_temp_file())

        self_state = self.create_real_self_state()

        results = []
        errors = []

        def collect_data_iteration(iteration_id):
            """Функция для сбора данных в отдельном потоке"""
            try:
                # Имитируем изменения состояния
                self_state.energy = 0.8 - (iteration_id % 5) * 0.05
                self_state.ticks = 50 + iteration_id

                # Сбор данных
                snapshot = state_tracker.collect_state_data(self_state)
                stats = component_monitor.collect_component_stats(self_state)

                data_collector.collect_state_data(snapshot)
                data_collector.collect_component_data(stats)

                results.append({
                    'iteration': iteration_id,
                    'energy': snapshot.energy,
                    'ticks': snapshot.ticks
                })
            except Exception as e:
                errors.append(f"Iteration {iteration_id}: {e}")

        # Запускаем несколько потоков
        threads = []
        for i in range(10):
            thread = threading.Thread(target=collect_data_iteration, args=(i,))
            threads.append(thread)
            thread.start()

        # Ждем завершения всех потоков
        for thread in threads:
            thread.join()

        # Проверяем что нет ошибок
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # Проверяем что все результаты собраны
        assert len(results) == 10

        # Сбрасываем буфер и проверяем сохранение
        data_collector.flush()
        all_data = data_collector.get_recent_data()
        assert len(all_data) == 20  # 10 state + 10 component

    def test_observability_error_recovery_in_runtime(self):
        """Тестирование восстановления после ошибок в runtime условиях"""
        state_tracker = StateTracker()
        component_monitor = ComponentMonitor()
        data_collector = DataCollector(storage_path=self.create_temp_file())

        self_state = self.create_real_self_state()

        # Имитируем повреждение компонентов
        self_state.memory = None  # Повреждаем память
        self_state.learning_engine = None  # Повреждаем learning

        # Сбор данных должен пройти без исключений
        snapshot = state_tracker.collect_state_data(self_state)
        stats = component_monitor.collect_component_stats(self_state)

        data_collector.collect_state_data(snapshot)
        data_collector.collect_component_data(stats)
        data_collector.flush()

        # Проверяем что система продолжила работать
        assert snapshot is not None
        assert stats is not None

        # Проверяем что поврежденные компоненты дали значения по умолчанию
        assert snapshot.memory_size == 0  # поврежденная память
        assert snapshot.learning_params_count == 0  # поврежденный learning
        assert stats.memory_episodic_size == 0  # поврежденная память
        assert stats.learning_params_count == 0  # поврежденный learning

        # Проверяем что данные сохранены
        all_data = data_collector.get_recent_data()
        assert len(all_data) == 2  # state + component

    def test_observability_data_consistency_across_runtime(self):
        """Проверка согласованности данных observability в runtime"""
        state_tracker = StateTracker()
        component_monitor = ComponentMonitor()
        data_collector = DataCollector(storage_path=self.create_temp_file())

        self_state = self.create_real_self_state()

        # Выполняем несколько циклов сбора
        for cycle in range(3):
            # Изменяем состояние
            self_state.energy -= 0.05
            self_state.ticks += 1

            # Добавляем действие в память
            from src.memory.memory import MemoryEntry
            entry = MemoryEntry(
                event_type="cycle_action",
                content={"cycle": cycle},
                timestamp=time.time()
            )
            self_state.memory.episodic_memory.append(entry)

            # Сбор данных
            snapshot = state_tracker.collect_state_data(self_state)
            stats = component_monitor.collect_component_stats(self_state)

            data_collector.collect_state_data(snapshot)
            data_collector.collect_component_data(stats)

        data_collector.flush()

        # Получаем все собранные данные
        state_data = data_collector.get_recent_data(data_type="state")
        component_data = data_collector.get_recent_data(data_type="component")

        assert len(state_data) == 3
        assert len(component_data) == 3

        # Проверяем последовательность данных
        for i in range(3):
            # Энергия должна уменьшаться
            expected_energy = 0.8 - i * 0.05
            assert abs(state_data[2-i].data['energy'] - expected_energy) < 0.01

            # Ticks должны расти
            expected_ticks = 50 + i
            assert state_data[2-i].data['ticks'] == expected_ticks

            # Размер памяти должен расти
            expected_memory = 10 + i
            assert state_data[2-i].data['memory_size'] == expected_memory
            assert component_data[2-i].data['memory_episodic_size'] == expected_memory