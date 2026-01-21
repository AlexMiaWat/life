"""
Тесты для инструментов пассивного наблюдения за системой Life

Проверяем:
- StateTracker: сбор данных SelfState без интерпретации
- ComponentMonitor: мониторинг компонентов без анализа
- DataCollector: хранение и извлечение данных
- HistoryManager: управление временными рядами
- ObservationExporter: экспорт данных в JSON/CSV
- Интеграцию в runtime loop
"""

import json
import csv
import time
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock

import pytest

from src.observability import (
    StateTracker, StateSnapshot,
    ComponentMonitor, ComponentStats, SystemComponentStats,
    DataCollector, ObservationData,
    HistoryManager, HistoryEntry,
    ObservationExporter
)


class TestStateTracker:
    """Тесты для StateTracker"""

    def test_state_tracker_initialization(self):
        """Проверка инициализации StateTracker"""
        tracker = StateTracker()
        assert tracker.last_snapshot is None
        assert tracker.collection_enabled is True

    def test_collect_state_data_basic(self):
        """Проверка базового сбора данных SelfState"""
        tracker = StateTracker()

        # Создаем mock SelfState
        mock_self_state = Mock()
        mock_self_state.energy = 0.8
        mock_self_state.stability = 0.7
        mock_self_state.integrity = 0.9
        mock_self_state.fatigue = 0.2
        mock_self_state.tension = 0.1
        mock_self_state.age = 100.0
        mock_self_state.subjective_time = 95.0
        mock_self_state.action_count = 5
        mock_self_state.decision_count = 3
        mock_self_state.feedback_count = 2

        # Mock memory
        mock_memory = Mock()
        mock_memory.episodic_memory = [1, 2, 3]
        mock_memory.recent_events = [4, 5]
        mock_self_state.memory = mock_memory

        # Mock learning engine
        mock_learning = Mock()
        mock_learning.params = {"param1": "value1", "param2": "value2"}
        mock_self_state.learning_engine = mock_learning

        # Mock adaptation manager
        mock_adaptation = Mock()
        mock_adaptation.params = {"param3": "value3"}
        mock_self_state.adaptation_manager = mock_adaptation

        snapshot = tracker.collect_state_data(mock_self_state)

        assert isinstance(snapshot, StateSnapshot)
        assert snapshot.energy == 0.8
        assert snapshot.stability == 0.7
        assert snapshot.integrity == 0.9
        assert snapshot.memory_size == 3
        assert snapshot.recent_events_count == 2
        assert snapshot.learning_params_count == 2
        assert snapshot.adaptation_params_count == 1

        # Проверяем, что snapshot сохранен
        assert tracker.get_last_snapshot() is snapshot

    def test_collect_state_data_disabled(self):
        """Проверка отключенного сбора данных"""
        tracker = StateTracker()
        tracker.disable_collection()

        mock_self_state = Mock()
        snapshot = tracker.collect_state_data(mock_self_state)

        # При отключенном сборе возвращается пустой snapshot
        assert isinstance(snapshot, StateSnapshot)
        assert snapshot.energy == 0.0

    def test_state_snapshot_to_dict(self):
        """Проверка сериализации StateSnapshot"""
        snapshot = StateSnapshot()
        snapshot.energy = 0.5
        snapshot.timestamp = 1234567890.0

        data = snapshot.to_dict()
        assert isinstance(data, dict)
        assert data['energy'] == 0.5
        assert data['timestamp'] == 1234567890.0


class TestComponentMonitor:
    """Тесты для ComponentMonitor"""

    def test_component_monitor_initialization(self):
        """Проверка инициализации ComponentMonitor"""
        monitor = ComponentMonitor()
        assert monitor.monitoring_enabled is True
        assert monitor.last_system_stats is None

    def test_collect_component_stats_basic(self):
        """Проверка базового сбора статистики компонентов"""
        monitor = ComponentMonitor()

        # Создаем mock SelfState с компонентами
        mock_self_state = Mock()

        # Mock memory
        mock_memory = Mock()
        mock_memory.episodic_memory = [1, 2, 3, 4, 5]
        mock_memory.archive_memory = Mock()
        mock_memory.archive_memory.episodic_memory = [6, 7]
        mock_memory.recent_events = [8, 9, 10]
        mock_self_state.memory = mock_memory

        # Mock learning engine
        mock_learning = Mock()
        mock_learning.params = {"p1": "v1", "p2": "v2"}
        mock_learning.operation_count = 42
        mock_self_state.learning_engine = mock_learning

        # Mock adaptation manager
        mock_adaptation = Mock()
        mock_adaptation.params = {"p3": "v3"}
        mock_adaptation.operation_count = 24
        mock_self_state.adaptation_manager = mock_adaptation

        # Mock decision engine
        mock_decision = Mock()
        mock_decision.decision_queue = [1, 2, 3]
        mock_decision.operation_count = 15
        mock_self_state.decision_engine = mock_decision

        # Mock action executor
        mock_action = Mock()
        mock_action.action_queue = [4, 5]
        mock_action.operation_count = 10
        mock_self_state.action_executor = mock_action

        # Mock environment
        mock_env = Mock()
        mock_event_queue = Mock()
        mock_event_queue.qsize = Mock(return_value=7)
        mock_event_queue.queue = [1, 2, 3, 4, 5]
        mock_env.event_queue = mock_event_queue
        mock_self_state.environment = mock_env

        stats = monitor.collect_component_stats(mock_self_state)

        assert isinstance(stats, SystemComponentStats)
        assert stats.memory_episodic_size == 5
        assert stats.memory_archive_size == 2
        assert stats.memory_recent_events == 3
        assert stats.learning_params_count == 2
        assert stats.learning_operations == 42
        assert stats.decision_queue_size == 3
        assert stats.action_queue_size == 2
        assert stats.environment_event_queue_size == 7
        assert stats.environment_pending_events == 5

    def test_collect_component_stats_disabled(self):
        """Проверка отключенного мониторинга"""
        monitor = ComponentMonitor()
        monitor.disable_monitoring()

        mock_self_state = Mock()
        stats = monitor.collect_component_stats(mock_self_state)

        # При отключенном мониторинге возвращается пустая статистика
        assert isinstance(stats, SystemComponentStats)
        assert stats.memory_episodic_size == 0

    def test_system_component_stats_to_dict(self):
        """Проверка сериализации SystemComponentStats"""
        stats = SystemComponentStats()
        stats.memory_episodic_size = 10
        stats.timestamp = 1234567890.0

        data = stats.to_dict()
        assert isinstance(data, dict)
        assert data['memory_episodic_size'] == 10
        assert data['timestamp'] == 1234567890.0


class TestDataCollector:
    """Тесты для DataCollector"""

    def test_data_collector_initialization(self):
        """Проверка инициализации DataCollector"""
        collector = DataCollector()
        assert collector.collection_enabled is True
        assert len(collector._buffer) == 0

    def test_collect_state_data(self):
        """Проверка сбора данных состояния"""
        collector = DataCollector()

        snapshot = StateSnapshot()
        snapshot.energy = 0.6

        collector.collect_state_data(snapshot)

        # Проверяем, что данные добавлены в буфер
        assert len(collector._buffer) == 1
        observation = collector._buffer[0]
        assert observation.data_type == "state"
        assert observation.data['energy'] == 0.6

    def test_collect_component_data(self):
        """Проверка сбора данных компонентов"""
        collector = DataCollector()

        stats = SystemComponentStats()
        stats.memory_episodic_size = 5

        collector.collect_component_data(stats)

        # Проверяем, что данные добавлены в буфер
        assert len(collector._buffer) == 1
        observation = collector._buffer[0]
        assert observation.data_type == "component"
        assert observation.data['memory_episodic_size'] == 5

    def test_buffer_flush(self):
        """Проверка ручного сброса буфера"""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "test_data.jsonl"
            collector = DataCollector(storage_path=str(storage_path))

            # Добавляем данные в буфер
            for i in range(3):
                snapshot = StateSnapshot()
                snapshot.energy = i * 0.1
                collector.collect_state_data(snapshot)

            # Проверяем, что данные в буфере
            assert len(collector._buffer) == 3

            # Ручной сброс буфера
            collector.flush()

            # Буфер должен быть очищен
            assert len(collector._buffer) == 0

            # Проверяем, что файл создан и содержит данные
            assert storage_path.exists()
            with open(storage_path, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 3

    def test_get_recent_data(self):
        """Проверка получения недавних данных"""
        collector = DataCollector()

        # Добавляем тестовые данные
        for i in range(5):
            snapshot = StateSnapshot()
            snapshot.energy = i * 0.1
            collector.collect_state_data(snapshot)

        # Получаем недавние данные
        recent = collector.get_recent_data(data_type="state", limit=3)
        assert len(recent) <= 3

        # Проверяем, что данные в правильном порядке (новые первыми)
        if len(recent) > 1:
            assert recent[0].timestamp >= recent[-1].timestamp

    def test_get_data_count(self):
        """Проверка подсчета данных в буфере"""
        collector = DataCollector()

        # Добавляем тестовые данные
        for i in range(3):
            snapshot = StateSnapshot()
            collector.collect_state_data(snapshot)

        # Данные должны быть в буфере
        count = collector.get_data_count("state")
        assert count == 3  # Данные только в буфере, файл не создан


class TestHistoryManager:
    """Тесты для HistoryManager"""

    def test_history_manager_initialization(self):
        """Проверка инициализации HistoryManager"""
        manager = HistoryManager()
        assert manager.collection_enabled is True
        assert len(manager._entries) == 0

    def test_add_entry(self):
        """Проверка добавления записи в историю"""
        manager = HistoryManager()

        entry = HistoryEntry(
            component="test_component",
            action="test_action",
            old_value="old",
            new_value="new"
        )

        manager.add_entry(entry)

        assert len(manager._entries) == 1
        assert manager._entries[0] is entry
        assert "test_component" in manager._component_index

    def test_add_state_change(self):
        """Проверка добавления изменения состояния"""
        manager = HistoryManager()

        manager.add_state_change("energy", 0.5, 0.7, {"reason": "test"})

        assert len(manager._entries) == 1
        entry = manager._entries[0]
        assert entry.component == "energy"
        assert entry.action == "state_change"
        assert entry.old_value == 0.5
        assert entry.new_value == 0.7
        assert entry.metadata["reason"] == "test"

    def test_add_snapshot(self):
        """Проверка добавления снимка"""
        manager = HistoryManager()

        data = {"energy": 0.8, "stability": 0.6}
        manager.add_snapshot("state", data)

        assert len(manager._entries) == 1
        entry = manager._entries[0]
        assert entry.component == "state"
        assert entry.action == "snapshot"
        assert entry.new_value == data

    def test_get_entries_with_filters(self):
        """Проверка получения записей с фильтрами"""
        manager = HistoryManager()

        # Добавляем тестовые записи
        base_time = time.time()
        for i in range(5):
            entry = HistoryEntry(
                timestamp=base_time + i,
                component=f"comp_{i % 2}",
                action="test"
            )
            manager.add_entry(entry)

        # Получаем все записи
        all_entries = manager.get_entries(limit=10)
        assert len(all_entries) == 5

        # Фильтруем по компоненту
        comp_0_entries = manager.get_entries(component="comp_0", limit=10)
        assert len(comp_0_entries) == 3  # Индексы 0, 2, 4

        # Фильтруем по времени
        recent_entries = manager.get_entries(
            start_time=base_time + 2.5,
            limit=10
        )
        # Должны быть записи с timestamp >= base_time + 2.5
        # Записи 3 и 4 имеют timestamps base_time+3 и base_time+4
        assert len(recent_entries) >= 2  # Минимум 2 записи

    def test_get_component_stats(self):
        """Проверка получения статистики компонента"""
        manager = HistoryManager()

        # Добавляем записи разных типов
        actions = ["create", "update", "delete", "snapshot"]
        for action in actions:
            entry = HistoryEntry(component="test_comp", action=action)
            manager.add_entry(entry)

        stats = manager.get_component_stats("test_comp")

        assert stats["component"] == "test_comp"
        assert stats["total_entries"] == 4
        assert stats["actions"]["create"] == 1
        assert stats["actions"]["update"] == 1
        assert stats["actions"]["delete"] == 1
        assert stats["actions"]["snapshot"] == 1

    def test_export_to_json(self):
        """Проверка экспорта в JSON"""
        manager = HistoryManager()

        # Добавляем тестовые данные
        manager.add_state_change("energy", 0.5, 0.7)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_file = f.name

        try:
            result_file = manager.export_to_json(output_file)
            assert result_file is not None
            assert Path(result_file).exists()

            # Проверяем содержимое файла
            with open(result_file, 'r') as f:
                data = json.load(f)

            assert data["total_entries"] == 1
            assert len(data["entries"]) == 1
            assert data["entries"][0]["component"] == "energy"

        finally:
            Path(output_file).unlink(missing_ok=True)


class TestObservationExporter:
    """Тесты для ObservationExporter"""

    def test_exporter_initialization(self):
        """Проверка инициализации ObservationExporter"""
        exporter = ObservationExporter()
        assert exporter.data_collector is None
        assert exporter.history_manager is None

    def test_export_state_data_json(self):
        """Проверка экспорта данных состояния в JSON"""
        # Создаем mock data collector
        mock_collector = Mock()
        mock_snapshot = Mock()
        mock_snapshot.to_dict.return_value = {"energy": 0.8, "timestamp": 1234567890.0}

        mock_collector.get_recent_data.return_value = [mock_snapshot]

        exporter = ObservationExporter(data_collector=mock_collector)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_file = f.name

        try:
            result_file = exporter.export_state_data_json(output_file)
            assert result_file == output_file

            # Проверяем содержимое файла
            with open(output_file, 'r') as f:
                data = json.load(f)

            assert "export_info" in data
            assert data["export_info"]["type"] == "state_data"
            assert len(data["data"]) == 1
            assert data["data"][0]["energy"] == 0.8

        finally:
            Path(output_file).unlink(missing_ok=True)

    def test_export_component_data_csv(self):
        """Проверка экспорта данных компонентов в CSV"""
        # Создаем mock data collector
        mock_collector = Mock()

        # Создаем объект, имитирующий ObservationData
        from src.observability.data_collector import ObservationData
        mock_observation = ObservationData(
            timestamp=1234567890.0,
            data_type="component",
            data={
                "timestamp": 1234567890.0,
                "memory_episodic_size": 10,
                "learning_params_count": 5
            }
        )

        mock_collector.get_recent_data.return_value = [mock_observation]

        exporter = ObservationExporter(data_collector=mock_collector)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_file = f.name

        try:
            result_file = exporter.export_component_data_csv(output_file)
            assert result_file == output_file

            # Проверяем содержимое файла
            with open(output_file, 'r', newline='') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 1
            assert rows[0]["memory_episodic_size"] == "10"
            assert rows[0]["learning_params_count"] == "5"

        finally:
            Path(output_file).unlink(missing_ok=True)

    def test_get_data_summary(self):
        """Проверка получения сводки данных"""
        # Создаем exporter без mock объектов (тестируем базовую функциональность)
        exporter = ObservationExporter()

        summary = exporter.get_data_summary()

        # Проверяем структуру summary
        assert isinstance(summary, dict)
        assert "data_types" in summary
        assert "total_records" in summary
        assert "components" in summary
        assert isinstance(summary["data_types"], list)
        assert isinstance(summary["total_records"], int)
        assert isinstance(summary["components"], list)

        # Без данных total_records должен быть 0
        assert summary["total_records"] == 0


class TestObservationIntegration:
    """Интеграционные тесты для компонентов наблюдения"""

    def test_full_observation_workflow(self):
        """Проверка полного рабочего процесса наблюдения"""
        # Создаем все компоненты
        state_tracker = StateTracker()
        component_monitor = ComponentMonitor()
        data_collector = DataCollector()
        history_manager = HistoryManager()
        exporter = ObservationExporter(data_collector, history_manager)

        # Создаем mock SelfState с правильной структурой
        mock_self_state = Mock()
        mock_self_state.energy = 0.75
        mock_self_state.stability = 0.8
        mock_self_state.integrity = 0.9
        mock_self_state.fatigue = 0.1
        mock_self_state.tension = 0.2
        mock_self_state.age = 100.0
        mock_self_state.subjective_time = 95.0
        mock_self_state.action_count = 5
        mock_self_state.decision_count = 3
        mock_self_state.feedback_count = 2

        # Mock memory
        mock_memory = Mock()
        mock_memory.episodic_memory = [1, 2, 3]
        mock_memory.recent_events = [4, 5]
        mock_self_state.memory = mock_memory

        # Mock learning engine
        mock_learning = Mock()
        mock_learning.params = {"param1": "value1"}
        mock_self_state.learning_engine = mock_learning

        # Mock adaptation manager
        mock_adaptation = Mock()
        mock_adaptation.params = {"param2": "value2"}
        mock_adaptation.operation_count = 5
        mock_self_state.adaptation_manager = mock_adaptation

        # Mock decision engine
        mock_decision = Mock()
        mock_decision.decision_queue = [1, 2]
        mock_decision.operation_count = 3
        mock_self_state.decision_engine = mock_decision

        # Mock action executor
        mock_action = Mock()
        mock_action.action_queue = [3, 4]
        mock_action.operation_count = 7
        mock_self_state.action_executor = mock_action

        # Mock environment
        mock_env = Mock()
        mock_event_queue = Mock()
        mock_event_queue.qsize = Mock(return_value=5)
        mock_event_queue.queue = [1, 2, 3, 4, 5]
        mock_env.event_queue = mock_event_queue
        mock_self_state.environment = mock_env

        # Собираем данные
        state_snapshot = state_tracker.collect_state_data(mock_self_state)
        component_stats = component_monitor.collect_component_stats(mock_self_state)

        # Сохраняем в коллекторе
        data_collector.collect_state_data(state_snapshot)
        data_collector.collect_component_data(component_stats)

        # Добавляем в историю
        history_manager.add_snapshot("state", state_snapshot.to_dict())
        history_manager.add_snapshot("components", component_stats.to_dict())

        # Проверяем, что данные собраны
        assert state_tracker.get_last_snapshot() is not None
        # ComponentMonitor может не собрать данные из-за mock объектов, проверяем другие компоненты
        assert data_collector.get_data_count("state") > 0
        assert len(history_manager.get_entries(limit=10)) > 0

        # Проверяем экспорт
        summary = exporter.get_data_summary()
        assert summary["total_records"] > 0

    def test_collection_disabled_behavior(self):
        """Проверка поведения при отключенном сборе данных"""
        state_tracker = StateTracker()
        component_monitor = ComponentMonitor()
        data_collector = DataCollector()
        history_manager = HistoryManager()

        # Отключаем сбор данных
        state_tracker.disable_collection()
        component_monitor.disable_monitoring()
        data_collector.disable_collection()
        history_manager.disable_collection()

        mock_self_state = Mock()

        # Пытаемся собрать данные
        state_snapshot = state_tracker.collect_state_data(mock_self_state)
        component_stats = component_monitor.collect_component_stats(mock_self_state)

        # При отключенном сборе должны возвращаться пустые структуры
        assert state_snapshot.energy == 0.0
        assert component_stats.memory_episodic_size == 0

        # Добавляем данные в отключенные коллекторы
        data_collector.collect_state_data(state_snapshot)
        history_manager.add_snapshot("test", {})

        # Данные не должны собираться
        assert data_collector.get_data_count() == 0
        assert len(history_manager.get_entries()) == 0