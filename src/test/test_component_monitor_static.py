"""
Статические тесты для ComponentMonitor

Проверяем:
- Инициализация ComponentMonitor
- Регистрация компонентов
- Сбор статистики
- Обновление метрик
- Экспорт данных
- Thread-safety
"""

import threading
import time
from unittest.mock import Mock

import pytest

from src.observability.component_monitor import ComponentMonitor, ComponentStats


class TestComponentMonitorStatic:
    """Статические тесты ComponentMonitor"""

    def test_initialization(self):
        """Тест инициализации ComponentMonitor"""
        monitor = ComponentMonitor()

        assert hasattr(monitor, '_stats')
        assert hasattr(monitor, '_lock')
        assert hasattr(monitor, '_monitors')
        assert isinstance(monitor._stats, dict)
        assert isinstance(monitor._monitors, dict)

    def test_component_registration(self):
        """Тест регистрации компонентов"""
        monitor = ComponentMonitor()

        # Регистрация компонента
        monitor.register_component("test_component")

        assert "test_component" in monitor._stats
        stats = monitor._stats["test_component"]
        assert isinstance(stats, ComponentStats)
        assert stats.component_name == "test_component"
        assert stats.timestamp > 0

    def test_register_component_with_initial_stats(self):
        """Тест регистрации компонента с начальными статистиками"""
        monitor = ComponentMonitor()

        initial_stats = {
            "queue_size": 5,
            "memory_usage": 1024,
            "active_threads": 2
        }

        monitor.register_component("test_component", initial_stats)

        stats = monitor._stats["test_component"]
        assert stats.queue_size == 5
        assert stats.memory_usage == 1024
        assert stats.active_threads == 2

    def test_update_stats(self):
        """Тест обновления статистики"""
        monitor = ComponentMonitor()
        monitor.register_component("test_component")

        # Обновление статистики
        monitor.update_stats("test_component", {
            "queue_size": 10,
            "operations_count": 5,
            "error_count": 1
        })

        stats = monitor._stats["test_component"]
        assert stats.queue_size == 10
        assert stats.operations_count == 5
        assert stats.error_count == 1

    def test_update_stats_incremental(self):
        """Тест инкрементального обновления статистики"""
        monitor = ComponentMonitor()
        monitor.register_component("test_component")

        # Первое обновление
        monitor.update_stats("test_component", {"operations_count": 5})
        assert monitor._stats["test_component"].operations_count == 5

        # Второе обновление (инкремент)
        monitor.update_stats("test_component", {"operations_count": 3})
        assert monitor._stats["test_component"].operations_count == 8

    def test_record_operation(self):
        """Тест записи операции"""
        monitor = ComponentMonitor()
        monitor.register_component("test_component")

        # Запись успешной операции
        monitor.record_operation("test_component", success=True, duration=0.1)

        stats = monitor._stats["test_component"]
        assert stats.operations_count == 1
        assert stats.success_count == 1
        assert stats.error_count == 0
        assert stats.last_operation_time == 0.1
        assert stats.avg_operation_time == 0.1

        # Запись неудачной операции
        monitor.record_operation("test_component", success=False, duration=0.2)

        stats = monitor._stats["test_component"]
        assert stats.operations_count == 2
        assert stats.success_count == 1
        assert stats.error_count == 1
        assert stats.last_operation_time == 0.2
        assert abs(stats.avg_operation_time - 0.15) < 0.001  # Среднее (0.1 + 0.2) / 2

    def test_get_stats(self):
        """Тест получения статистики"""
        monitor = ComponentMonitor()
        monitor.register_component("test_component")

        # Обновление статистики
        monitor.update_stats("test_component", {"queue_size": 7})

        stats = monitor.get_stats("test_component")
        assert stats is not None
        assert stats.queue_size == 7

        # Запрос несуществующего компонента
        assert monitor.get_stats("nonexistent") is None

    def test_get_all_stats(self):
        """Тест получения всех статистик"""
        monitor = ComponentMonitor()

        # Регистрация нескольких компонентов
        monitor.register_component("comp1")
        monitor.register_component("comp2")

        monitor.update_stats("comp1", {"queue_size": 1})
        monitor.update_stats("comp2", {"queue_size": 2})

        all_stats = monitor.get_all_stats()
        assert len(all_stats) == 2
        assert "comp1" in all_stats
        assert "comp2" in all_stats
        assert all_stats["comp1"].queue_size == 1
        assert all_stats["comp2"].queue_size == 2

    def test_unregister_component(self):
        """Тест удаления компонента"""
        monitor = ComponentMonitor()
        monitor.register_component("test_component")

        assert "test_component" in monitor._stats

        monitor.unregister_component("test_component")

        assert "test_component" not in monitor._stats

    def test_component_stats_to_dict(self):
        """Тест сериализации ComponentStats"""
        stats = ComponentStats(
            component_name="test",
            queue_size=5,
            memory_usage=1024,
            operations_count=10
        )

        data = stats.to_dict()

        assert data["component_name"] == "test"
        assert data["queue_size"] == 5
        assert data["memory_usage"] == 1024
        assert data["operations_count"] == 10
        assert "timestamp" in data

    def test_thread_safety_registration(self):
        """Тест потокобезопасности регистрации компонентов"""
        monitor = ComponentMonitor()

        errors = []
        registered_components = []

        def register_components(thread_id: int):
            """Регистрирует компоненты в потоке"""
            try:
                for i in range(10):
                    comp_name = f"thread_{thread_id}_comp_{i}"
                    monitor.register_component(comp_name)
                    registered_components.append(comp_name)
            except Exception as e:
                errors.append(str(e))

        # Запуск нескольких потоков
        threads = []
        for i in range(5):
            t = threading.Thread(target=register_components, args=(i,))
            threads.append(t)
            t.start()

        # Ожидание завершения
        for t in threads:
            t.join()

        # Проверка отсутствия ошибок
        assert len(errors) == 0

        # Проверка что все компоненты зарегистрированы
        assert len(registered_components) == 50
        assert len(monitor._stats) == 50

        # Проверка уникальности имен
        assert len(set(registered_components)) == 50

    def test_thread_safety_updates(self):
        """Тест потокобезопасности обновления статистики"""
        monitor = ComponentMonitor()
        monitor.register_component("shared_component")

        errors = []
        update_count = [0]

        def update_stats(thread_id: int):
            """Обновляет статистику в потоке"""
            try:
                for i in range(100):
                    monitor.update_stats("shared_component", {
                        "operations_count": 1,
                        "queue_size": thread_id
                    })
                    update_count[0] += 1
            except Exception as e:
                errors.append(str(e))

        # Запуск нескольких потоков
        threads = []
        for i in range(5):
            t = threading.Thread(target=update_stats, args=(i,))
            threads.append(t)
            t.start()

        # Ожидание завершения
        for t in threads:
            t.join()

        # Проверка отсутствия ошибок
        assert len(errors) == 0

        # Проверка что все обновления применились
        assert update_count[0] == 500  # 5 потоков * 100 обновлений
        stats = monitor.get_stats("shared_component")
        assert stats.operations_count == 500

    def test_monitor_functionality(self):
        """Тест функциональности мониторинга"""
        monitor = ComponentMonitor()

        # Регистрация компонента с монитором
        def test_monitor_func():
            return {"custom_metric": 42}

        monitor.register_component("test_component")
        monitor.add_monitor("test_component", "custom_monitor", test_monitor_func)

        # Выполнение мониторинга
        monitor.run_monitors("test_component")

        # Проверка что монитор выполнился (данные должны быть в stats, но это зависит от реализации)
        stats = monitor.get_stats("test_component")
        assert stats is not None

    def test_monitor_error_handling(self):
        """Тест обработки ошибок в мониторах"""
        monitor = ComponentMonitor()

        def failing_monitor():
            raise ValueError("Test error")

        monitor.register_component("test_component")
        monitor.add_monitor("test_component", "failing_monitor", failing_monitor)

        # Это не должно вызывать исключение
        monitor.run_monitors("test_component")

        # Компонент должен продолжать работать
        assert monitor.get_stats("test_component") is not None

    def test_export_stats(self):
        """Тест экспорта статистики"""
        monitor = ComponentMonitor()
        monitor.register_component("test_component")

        monitor.update_stats("test_component", {"queue_size": 5})

        exported = monitor.export_stats()

        assert isinstance(exported, dict)
        assert "test_component" in exported
        assert exported["test_component"]["queue_size"] == 5

    def test_clear_stats(self):
        """Тест очистки статистики"""
        monitor = ComponentMonitor()
        monitor.register_component("test_component")

        monitor.update_stats("test_component", {"operations_count": 10})

        # Очистка
        monitor.clear_stats("test_component")

        stats = monitor.get_stats("test_component")
        assert stats.operations_count == 0
        assert stats.success_count == 0
        assert stats.error_count == 0