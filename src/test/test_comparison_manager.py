"""
Тесты для ComparisonManager - центрального менеджера системы сравнения
"""

import pytest
from unittest.mock import Mock, patch

from src.comparison.comparison_manager import ComparisonManager, ComparisonConfig
from src.comparison.life_instance import LifeInstance


class TestComparisonManager:
    """Тесты ComparisonManager."""

    def test_initialization(self):
        """Тест инициализации ComparisonManager."""
        manager = ComparisonManager()

        assert manager.instances == {}
        assert manager.config is not None
        assert isinstance(manager.config, ComparisonConfig)
        assert manager.config.max_instances == 5
        assert not manager.is_collecting

    def test_create_instance_success(self):
        """Тест успешного создания инстанса."""
        manager = ComparisonManager()

        instance = manager.create_instance("test_instance")

        assert instance is not None
        assert isinstance(instance, LifeInstance)
        assert instance.config.instance_id == "test_instance"
        assert "test_instance" in manager.instances
        assert manager.stats['total_instances_created'] == 1

    def test_create_instance_duplicate(self):
        """Тест создания инстанса с существующим ID."""
        manager = ComparisonManager()

        # Создаем первый инстанс
        instance1 = manager.create_instance("test_instance")
        assert instance1 is not None

        # Пытаемся создать второй с тем же ID
        instance2 = manager.create_instance("test_instance")
        assert instance2 is None

    def test_create_instance_limit_exceeded(self):
        """Тест превышения лимита инстансов."""
        config = ComparisonConfig(max_instances=2)
        manager = ComparisonManager(config)

        # Создаем инстансы до лимита
        instance1 = manager.create_instance("instance1")
        instance2 = manager.create_instance("instance2")
        assert instance1 is not None
        assert instance2 is not None

        # Пытаемся создать третий
        instance3 = manager.create_instance("instance3")
        assert instance3 is None

    @patch('src.comparison.life_instance.LifeInstance.start')
    def test_start_instance_success(self, mock_start):
        """Тест успешного запуска инстанса."""
        mock_start.return_value = True

        manager = ComparisonManager()
        instance = manager.create_instance("test_instance")

        result = manager.start_instance("test_instance")

        assert result is True
        mock_start.assert_called_once()
        assert manager.stats['active_instances'] == 1

    def test_start_instance_not_found(self):
        """Тест запуска несуществующего инстанса."""
        manager = ComparisonManager()

        result = manager.start_instance("nonexistent")

        assert result is False

    @patch('src.comparison.life_instance.LifeInstance.stop')
    def test_stop_instance_success(self, mock_stop):
        """Тест успешной остановки инстанса."""
        mock_stop.return_value = True

        manager = ComparisonManager()
        instance = manager.create_instance("test_instance")
        manager.start_instance("test_instance")  # Предварительно запускаем

        result = manager.stop_instance("test_instance")

        assert result is True
        mock_stop.assert_called_once()
        assert manager.stats['active_instances'] == 0

    def test_get_instance_status(self):
        """Тест получения статуса инстанса."""
        manager = ComparisonManager()
        instance = manager.create_instance("test_instance")

        status = manager.get_instance_status("test_instance")

        assert status is not None
        assert status['instance_id'] == "test_instance"
        assert status['is_running'] is False

    def test_get_instance_status_not_found(self):
        """Тест получения статуса несуществующего инстанса."""
        manager = ComparisonManager()

        status = manager.get_instance_status("nonexistent")

        assert status is None

    def test_get_all_instances_status(self):
        """Тест получения статусов всех инстансов."""
        manager = ComparisonManager()

        # Создаем несколько инстансов
        manager.create_instance("instance1")
        manager.create_instance("instance2")

        statuses = manager.get_all_instances_status()

        assert len(statuses) == 2
        assert "instance1" in statuses
        assert "instance2" in statuses

    @patch('src.comparison.life_instance.LifeInstance.get_latest_snapshot')
    @patch('src.comparison.life_instance.LifeInstance.get_structured_logs')
    def test_collect_comparison_data(self, mock_logs, mock_snapshot):
        """Тест сбора данных для сравнения."""
        mock_snapshot.return_value = {'energy': 50.0, 'ticks': 10}
        mock_logs.return_value = [{'stage': 'decision', 'data': {'pattern': 'ignore'}}]

        manager = ComparisonManager()
        instance = manager.create_instance("test_instance")

        # Имитируем, что инстанс запущен
        instance.is_running = True
        instance.is_alive = Mock(return_value=True)

        data = manager.collect_comparison_data()

        assert 'timestamp' in data
        assert 'instances' in data
        assert 'summary' in data
        assert 'test_instance' in data['instances']

    def test_cleanup_instances(self):
        """Тест очистки завершившихся инстансов."""
        manager = ComparisonManager()

        # Создаем инстансы
        manager.create_instance("instance1")
        manager.create_instance("instance2")

        # Имитируем, что instance1 завершен, а instance2 запущен
        manager.instances["instance1"].is_running = False
        manager.instances["instance1"].process = None
        manager.instances["instance2"].is_running = True
        manager.instances["instance2"].is_alive = Mock(return_value=True)

        results = manager.cleanup_instances()

        assert results["instance1"] is True  # Должен быть удален
        assert results["instance2"] is False  # Должен остаться
        assert "instance1" not in manager.instances
        assert "instance2" in manager.instances

    def test_get_comparison_stats(self):
        """Тест получения статистики сравнения."""
        manager = ComparisonManager()

        stats = manager.get_comparison_stats()

        assert 'manager_stats' in stats
        assert 'active_instances' in stats
        assert 'total_instances' in stats
        assert 'is_collecting' in stats
        assert 'config' in stats

    def test_str_representation(self):
        """Тест строкового представления."""
        manager = ComparisonManager()

        str_repr = str(manager)

        assert 'ComparisonManager' in str_repr
        assert 'active=0' in str_repr
        assert 'total=0' in str_repr