"""
Дымовые тесты для ComponentMonitor

Проверяем:
- Создание экземпляров классов
- Базовую функциональность методов
- Отсутствие исключений при нормальной работе
- Корректность основных операций
"""

import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.observability.component_monitor import (
    ComponentMonitor,
    ComponentStats,
    SystemComponentStats,
)


@pytest.mark.smoke
class TestComponentMonitorSmoke:
    """Дымовые тесты для ComponentMonitor"""

    def test_component_monitor_creation(self):
        """Проверка создания ComponentMonitor"""
        monitor = ComponentMonitor()
        assert monitor is not None
        assert isinstance(monitor, ComponentMonitor)

    def test_component_stats_creation(self):
        """Проверка создания ComponentStats"""
        stats = ComponentStats(component_name="test_component")
        assert stats is not None
        assert isinstance(stats, ComponentStats)
        assert stats.component_name == "test_component"

    def test_system_component_stats_creation(self):
        """Проверка создания SystemComponentStats"""
        stats = SystemComponentStats()
        assert stats is not None
        assert isinstance(stats, SystemComponentStats)

    def test_component_stats_custom_creation(self):
        """Проверка создания ComponentStats с кастомными значениями"""
        stats = ComponentStats(
            component_name="test",
            queue_size=10,
            memory_usage=1024,
            active_threads=4,
            operations_count=100,
            error_count=2,
            success_count=98,
            avg_operation_time=0.5,
            last_operation_time=0.3
        )

        assert stats.component_name == "test"
        assert stats.queue_size == 10
        assert stats.memory_usage == 1024
        assert stats.operations_count == 100

    def test_collect_component_stats_basic(self):
        """Проверка базового сбора статистики компонентов"""
        monitor = ComponentMonitor()
        mock_state = Mock()

        # Настраиваем базовые компоненты
        mock_memory = Mock()
        mock_memory.episodic_memory = [1, 2, 3]
        mock_memory.recent_events = ['a', 'b']

        mock_learning = Mock()
        mock_learning.params = {'p1': 1, 'p2': 2}
        mock_learning.operation_count = 15

        mock_state.memory = mock_memory
        mock_state.learning_engine = mock_learning

        # Вызываем метод сбора статистики
        result = monitor.collect_component_stats(mock_state)

        # Проверяем результат
        assert isinstance(result, SystemComponentStats)
        assert result.memory_episodic_size == 3
        assert result.memory_recent_events == 2
        assert result.learning_params_count == 2
        assert result.learning_operations == 15

    def test_collect_component_stats_full(self):
        """Проверка полного сбора статистики всех компонентов"""
        monitor = ComponentMonitor()
        mock_state = Mock()

        # Настраиваем все компоненты
        mock_memory = Mock()
        mock_memory.episodic_memory = [1, 2, 3, 4, 5]
        mock_memory.recent_events = ['e1', 'e2', 'e3']
        mock_archive = Mock()
        mock_archive.episodic_memory = [10, 20]
        mock_memory.archive_memory = mock_archive

        mock_learning = Mock()
        mock_learning.params = {'lr': 0.01, 'epochs': 100}
        mock_learning.operation_count = 25

        mock_adaptation = Mock()
        mock_adaptation.params = {'threshold': 0.5}
        mock_adaptation.operation_count = 10

        mock_decision = Mock()
        mock_decision.decision_queue = [1, 2, 3]
        mock_decision.operation_count = 8

        mock_action = Mock()
        mock_action.action_queue = ['a1', 'a2']
        mock_action.operation_count = 12

        mock_environment = Mock()
        mock_event_queue = Mock()
        mock_event_queue.qsize = Mock(return_value=5)
        mock_event_queue.queue = [1, 2, 3, 4, 5]
        mock_environment.event_queue = mock_event_queue

        mock_intelligence = {'processed_sources': {'src1': {}, 'src2': {}}}

        mock_state.memory = mock_memory
        mock_state.learning_engine = mock_learning
        mock_state.adaptation_manager = mock_adaptation
        mock_state.decision_engine = mock_decision
        mock_state.action_executor = mock_action
        mock_state.environment = mock_environment
        mock_state.intelligence = mock_intelligence

        result = monitor.collect_component_stats(mock_state)

        assert result.memory_episodic_size == 5
        assert result.memory_archive_size == 2
        assert result.memory_recent_events == 3
        assert result.learning_params_count == 2
        assert result.learning_operations == 25
        assert result.adaptation_params_count == 1
        assert result.adaptation_operations == 10
        assert result.decision_queue_size == 3
        assert result.decision_operations == 8
        assert result.action_queue_size == 2
        assert result.action_operations == 12
        assert result.environment_event_queue_size == 5
        assert result.environment_pending_events == 5
        assert result.intelligence_processed_sources == 2

    def test_collect_component_stats_missing_components(self):
        """Проверка сбора статистики при отсутствии некоторых компонентов"""
        monitor = ComponentMonitor()
        mock_state = Mock()

        # Настраиваем только часть компонентов
        mock_memory = Mock()
        mock_memory.episodic_memory = [1]
        mock_state.memory = mock_memory

        result = monitor.collect_component_stats(mock_state)

        # Должны быть заполнены только существующие компоненты
        assert result.memory_episodic_size == 1
        assert result.learning_params_count == 0  # отсутствует
        assert result.decision_queue_size == 0    # отсутствует

    def test_get_last_system_stats(self):
        """Проверка получения последних системных статистик"""
        monitor = ComponentMonitor()

        # Изначально должен быть None
        assert monitor.get_last_system_stats() is None

        # После сбора данных должен быть объект
        mock_state = Mock()
        mock_memory = Mock()
        mock_memory.episodic_memory = [1, 2]
        mock_state.memory = mock_memory

        monitor.collect_component_stats(mock_state)
        stats = monitor.get_last_system_stats()

        assert stats is not None
        assert isinstance(stats, SystemComponentStats)
        assert stats.memory_episodic_size == 2

    def test_monitoring_enable_disable(self):
        """Проверка включения/выключения мониторинга"""
        monitor = ComponentMonitor()

        # По умолчанию включено
        assert monitor.monitoring_enabled is True

        # Выключаем
        monitor.disable_monitoring()
        assert monitor.monitoring_enabled is False

        # При выключенном мониторинге возвращается пустой объект
        mock_state = Mock()
        result = monitor.collect_component_stats(mock_state)
        assert isinstance(result, SystemComponentStats)
        # Все поля должны быть 0 при выключенном мониторинге
        assert result.memory_episodic_size == 0

        # Включаем обратно
        monitor.enable_monitoring()
        assert monitor.monitoring_enabled is True

    def test_to_dict_functionality(self):
        """Проверка методов to_dict"""
        # ComponentStats
        component_stats = ComponentStats(
            component_name="test",
            queue_size=5,
            operations_count=20
        )
        data = component_stats.to_dict()

        assert isinstance(data, dict)
        assert data['component_name'] == "test"
        assert data['queue_size'] == 5
        assert data['operations_count'] == 20

        # SystemComponentStats
        system_stats = SystemComponentStats(
            memory_episodic_size=10,
            learning_operations=5
        )
        data = system_stats.to_dict()

        assert isinstance(data, dict)
        assert data['memory_episodic_size'] == 10
        assert data['learning_operations'] == 5

    def test_error_handling(self):
        """Проверка обработки ошибок"""
        monitor = ComponentMonitor()

        # Метод должен обрабатывать исключения gracefully
        mock_state = Mock()
        # Настраиваем mock чтобы он вызывал исключения
        mock_state.memory = Mock()
        mock_state.memory.episodic_memory = Mock(side_effect=AttributeError("Test error"))

        # Метод не должен выбрасывать исключения
        result = monitor.collect_component_stats(mock_state)
        assert isinstance(result, SystemComponentStats)

    def test_multiple_collections(self):
        """Проверка множественного сбора статистики"""
        monitor = ComponentMonitor()

        # Первый сбор
        mock_state1 = Mock()
        mock_memory1 = Mock()
        mock_memory1.episodic_memory = [1, 2, 3]
        mock_state1.memory = mock_memory1
        stats1 = monitor.collect_component_stats(mock_state1)

        # Второй сбор
        mock_state2 = Mock()
        mock_memory2 = Mock()
        mock_memory2.episodic_memory = [4, 5, 6, 7]
        mock_state2.memory = mock_memory2
        stats2 = monitor.collect_component_stats(mock_state2)

        # Последние stats должны быть от второго сбора
        last_stats = monitor.get_last_system_stats()
        assert last_stats.memory_episodic_size == 4

        # Оба stats должны существовать
        assert stats1.memory_episodic_size == 3
        assert stats2.memory_episodic_size == 4