"""
Интеграционные тесты для модуля observability

Проверяем:
- Взаимодействие компонентов observability между собой
- Интеграцию с другими модулями системы Life
- Полные сценарии сбора и хранения данных
- End-to-end функциональность
"""

import json
import tempfile
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.observability.state_tracker import StateTracker, StateSnapshot
from src.observability.component_monitor import ComponentMonitor, SystemComponentStats
from src.observability.data_collector import DataCollector, ObservationData


@pytest.mark.integration
class TestObservabilityIntegration:
    """Интеграционные тесты для модуля observability"""

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

    def test_full_observation_pipeline(self):
        """Проверка полного конвейера наблюдения"""
        # Создаем компоненты
        state_tracker = StateTracker()
        component_monitor = ComponentMonitor()
        data_collector = DataCollector(storage_path=self.create_temp_file())

        # Создаем mock self_state с полными данными
        mock_state = self._create_full_mock_state()

        # Шаг 1: Сбор данных состояния
        state_snapshot = state_tracker.collect_state_data(mock_state)
        assert isinstance(state_snapshot, StateSnapshot)
        assert state_snapshot.energy == 0.6  # Используем значение из mock_state
        assert state_snapshot.memory_size == 150  # Используем значение из episodic_memory

        # Шаг 2: Сбор данных компонентов
        component_stats = component_monitor.collect_component_stats(mock_state)
        assert isinstance(component_stats, SystemComponentStats)
        assert component_stats.memory_episodic_size == 150
        assert component_stats.learning_params_count == 5

        # Шаг 3: Сохранение данных
        data_collector.collect_state_data(state_snapshot)
        data_collector.collect_component_data(component_stats)

        # Шаг 4: Принудительный сброс буфера
        data_collector.flush()

        # Шаг 5: Проверка сохраненных данных
        state_data = data_collector.get_recent_data(data_type="state")
        component_data = data_collector.get_recent_data(data_type="component")

        assert len(state_data) == 1
        assert len(component_data) == 1

        assert state_data[0].data['energy'] == 0.6
        assert component_data[0].data['memory_episodic_size'] == 150

    def test_observation_with_disabled_collection(self):
        """Проверка работы при отключенном сборе данных"""
        # Создаем компоненты с отключенным сбором
        state_tracker = StateTracker()
        component_monitor = ComponentMonitor()
        data_collector = DataCollector()

        state_tracker.disable_collection()
        component_monitor.disable_monitoring()
        data_collector.disable_collection()

        mock_state = self._create_basic_mock_state()

        # Попытка сбора данных
        state_snapshot = state_tracker.collect_state_data(mock_state)
        component_stats = component_monitor.collect_component_stats(mock_state)

        data_collector.collect_state_data(state_snapshot)
        data_collector.collect_component_data(component_stats)

        # Проверка что данные не собираются
        assert len(data_collector._buffer) == 0
        assert state_snapshot.energy == 0.0  # пустой snapshot
        assert component_stats.memory_episodic_size == 0  # пустая статистика

    def test_data_persistence_and_retrieval(self):
        """Проверка сохранения и извлечения данных"""
        storage_path = self.create_temp_file()
        collector = DataCollector(storage_path=storage_path)

        # Создаем и сохраняем несколько наборов данных
        for i in range(3):
            snapshot = StateSnapshot(energy=0.5 + i * 0.1, memory_size=100 + i * 10)
            collector.collect_state_data(snapshot)

        # Принудительный сброс
        collector.flush()

        # Создаем новый коллектор для того же файла
        new_collector = DataCollector(storage_path=storage_path)

        # Проверяем что данные сохранились
        data = new_collector.get_recent_data(data_type="state")
        assert len(data) == 3

        # Проверяем сортировку (самые свежие первыми)
        energies = [d.data['energy'] for d in data]
        assert energies[0] >= energies[1] >= energies[2]

        # Проверяем лимит
        limited_data = new_collector.get_recent_data(limit=2)
        assert len(limited_data) == 2

    def test_cross_component_data_consistency(self):
        """Проверка согласованности данных между компонентами"""
        state_tracker = StateTracker()
        component_monitor = ComponentMonitor()

        mock_state = self._create_full_mock_state()

        # Сбор данных разными компонентами
        state_snapshot = state_tracker.collect_state_data(mock_state)
        component_stats = component_monitor.collect_component_stats(mock_state)

        # Проверяем согласованность данных памяти
        assert state_snapshot.memory_size == component_stats.memory_episodic_size

        # Проверяем согласованность счетчиков действий
        # (в mock_state action_count должен соответствовать данным)

        # Проверяем временные метки (должны быть близкими)
        time_diff = abs(state_snapshot.timestamp - component_stats.timestamp)
        assert time_diff < 1.0  # менее секунды

    def test_error_recovery_and_robustness(self):
        """Проверка восстановления после ошибок"""
        state_tracker = StateTracker()
        component_monitor = ComponentMonitor()
        data_collector = DataCollector(storage_path=self.create_temp_file())

        # Создаем mock с проблемными атрибутами
        mock_state = Mock()
        mock_state.energy = 0.7

        # Настраиваем проблемные компоненты
        mock_memory = Mock()
        mock_memory.episodic_memory = Mock(side_effect=AttributeError("Test error"))
        mock_state.memory = mock_memory

        mock_learning = Mock()
        mock_learning.params = Mock(side_effect=Exception("Learning error"))
        mock_state.learning_engine = mock_learning

        # Сбор данных должен пройти без исключений
        state_snapshot = state_tracker.collect_state_data(mock_state)
        component_stats = component_monitor.collect_component_stats(mock_state)

        # Данные должны быть собраны частично (где возможно)
        assert state_snapshot.energy == 0.7  # нормальные данные
        assert state_snapshot.memory_size == 0  # ошибка обработана

        # Сохранение должно работать
        data_collector.collect_state_data(state_snapshot)
        data_collector.collect_component_data(component_stats)
        data_collector.flush()

        # Проверка что данные сохранены
        saved_data = data_collector.get_recent_data()
        assert len(saved_data) == 2

    def test_performance_and_memory_efficiency(self):
        """Проверка производительности и эффективности памяти"""
        import time

        state_tracker = StateTracker()
        component_monitor = ComponentMonitor()
        data_collector = DataCollector(storage_path=self.create_temp_file(), )

        mock_state = self._create_basic_mock_state()

        # Измеряем время сбора данных
        start_time = time.time()
        for _ in range(100):
            snapshot = state_tracker.collect_state_data(mock_state)
            stats = component_monitor.collect_component_stats(mock_state)
            data_collector.collect_state_data(snapshot)
            data_collector.collect_component_data(stats)
        end_time = time.time()

        total_time = end_time - start_time
        avg_time_per_cycle = total_time / 100

        # Проверяем что время разумное (< 0.01 сек на цикл)
        assert avg_time_per_cycle < 0.01

        # Проверяем буфер
        assert len(data_collector._buffer) <= data_collector._buffer_size

        # Принудительный сброс и проверка файла
        data_collector.flush()
        data_count = data_collector.get_data_count()
        assert data_count == 200  # 100 state + 100 component

    def test_configuration_and_state_management(self):
        """Проверка управления конфигурацией и состоянием"""
        # Создаем компоненты
        state_tracker = StateTracker()
        component_monitor = ComponentMonitor()
        data_collector = DataCollector()

        # Проверяем начальное состояние
        assert state_tracker.collection_enabled is True
        assert component_monitor.monitoring_enabled is True
        assert data_collector.collection_enabled is True

        # Изменяем конфигурацию
        state_tracker.disable_collection()
        component_monitor.disable_monitoring()
        data_collector.disable_collection()

        assert state_tracker.collection_enabled is False
        assert component_monitor.monitoring_enabled is False
        assert data_collector.collection_enabled is False

        # Проверяем что изменения сохраняются
        mock_state = self._create_basic_mock_state()

        snapshot = state_tracker.collect_state_data(mock_state)
        stats = component_monitor.collect_component_stats(mock_state)

        data_collector.collect_state_data(snapshot)
        data_collector.collect_component_data(stats)

        # При отключенном сборе буфер должен оставаться пустым
        assert len(data_collector._buffer) == 0

        # Включаем обратно
        state_tracker.enable_collection()
        component_monitor.enable_monitoring()
        data_collector.enable_collection()

        assert state_tracker.collection_enabled is True
        assert component_monitor.monitoring_enabled is True
        assert data_collector.collection_enabled is True

    def _create_basic_mock_state(self):
        """Создание базового mock self_state"""
        mock_state = Mock()

        # Базовые параметры
        mock_state.energy = 0.6
        mock_state.stability = 0.7
        mock_state.integrity = 0.8
        mock_state.fatigue = 0.2
        mock_state.tension = 0.3
        mock_state.age = 100.0
        mock_state.subjective_time = 90.0

        # Счетчики
        mock_state.action_count = 15
        mock_state.decision_count = 8
        mock_state.feedback_count = 5

        # Память
        mock_memory = Mock()
        mock_memory.episodic_memory = list(range(150))  # 150 элементов для теста
        mock_memory.recent_events = ['a', 'b', 'c']
        mock_state.memory = mock_memory

        return mock_state

    def _create_full_mock_state(self):
        """Создание полного mock self_state со всеми компонентами"""
        mock_state = self._create_basic_mock_state()

        # Learning engine
        mock_learning = Mock()
        mock_learning.params = {'lr': 0.01, 'epochs': 100, 'batch_size': 32, 'hidden_size': 64, 'dropout': 0.1}
        mock_learning.operation_count = 25
        mock_state.learning_engine = mock_learning

        # Adaptation manager
        mock_adaptation = Mock()
        mock_adaptation.params = {'threshold': 0.5, 'rate': 0.1, 'window': 10}
        mock_adaptation.operation_count = 12
        mock_state.adaptation_manager = mock_adaptation

        # Decision engine
        mock_decision = Mock()
        mock_decision.decision_queue = [1, 2, 3, 4]
        mock_decision.operation_count = 18
        mock_state.decision_engine = mock_decision

        # Action executor
        mock_action = Mock()
        mock_action.action_queue = ['act1', 'act2', 'act3']
        mock_action.operation_count = 22
        mock_state.action_executor = mock_action

        # Environment
        mock_event_queue = Mock()
        mock_event_queue.qsize = Mock(return_value=7)
        mock_event_queue.queue = [1, 2, 3, 4, 5, 6, 7]

        mock_environment = Mock()
        mock_environment.event_queue = mock_event_queue
        mock_state.environment = mock_environment

        # Intelligence
        mock_state.intelligence = {'processed_sources': {'src1': {}, 'src2': {}, 'src3': {}}}

        # Archive memory
        mock_archive = Mock()
        mock_archive.episodic_memory = [10, 20, 30, 40, 50]
        mock_state.memory.archive_memory = mock_archive

        return mock_state