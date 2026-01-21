"""
Дымовые тесты для ComponentMonitor

Проверяем базовую функциональность:
- Регистрация компонентов и сбор статистики
- Обновление метрик
- Экспорт данных
"""

import time
import threading

import pytest

from src.observability.component_monitor import ComponentMonitor


class TestComponentMonitorSmoke:
    """Дымовые тесты ComponentMonitor"""

    def test_basic_monitoring_workflow(self):
        """Базовый рабочий процесс мониторинга"""
        monitor = ComponentMonitor()

        # Регистрация компонентов
        monitor.register_component("memory_component")
        monitor.register_component("learning_component")

        # Обновление статистики
        monitor.update_stats("memory_component", {
            "queue_size": 5,
            "memory_usage": 1024,
            "active_threads": 2
        })

        monitor.update_stats("learning_component", {
            "operations_count": 10,
            "success_count": 8,
            "error_count": 2
        })

        # Запись операций
        monitor.record_operation("memory_component", success=True, duration=0.1)
        monitor.record_operation("learning_component", success=False, duration=0.05)

        # Получение статистики
        memory_stats = monitor.get_stats("memory_component")
        learning_stats = monitor.get_stats("learning_component")

        assert memory_stats is not None
        assert learning_stats is not None

        # Проверка базовых метрик
        assert memory_stats.queue_size == 5
        assert memory_stats.memory_usage == 1024
        assert memory_stats.operations_count == 1
        assert memory_stats.success_count == 1

        assert learning_stats.operations_count == 11  # 10 + 1
        assert learning_stats.success_count == 8
        assert learning_stats.error_count == 3  # 2 + 1

    def test_export_functionality(self):
        """Функциональность экспорта"""
        monitor = ComponentMonitor()

        # Регистрация и обновление компонентов
        components = ["api", "memory", "learning"]
        for comp in components:
            monitor.register_component(comp)
            monitor.update_stats(comp, {"operations_count": 5, "queue_size": 2})

        # Экспорт статистики
        exported = monitor.export_stats()

        assert isinstance(exported, dict)
        assert len(exported) == 3

        for comp in components:
            assert comp in exported
            assert "operations_count" in exported[comp]
            assert exported[comp]["operations_count"] == 5

    def test_monitor_operations(self):
        """Операции мониторинга"""
        monitor = ComponentMonitor()

        # Регистрация компонента с монитором
        monitor.register_component("test_component")

        # Добавление простого монитора
        def simple_monitor():
            return {"test_metric": 42}

        monitor.add_monitor("test_component", "simple_monitor", simple_monitor)

        # Выполнение мониторинга
        monitor.run_monitors("test_component")

        # Получение статистики после мониторинга
        stats = monitor.get_stats("test_component")
        assert stats is not None

    def test_concurrent_operations_smoke(self):
        """Базовый тест конкурентных операций"""
        monitor = ComponentMonitor()

        errors = []

        def monitor_operations(thread_id: int):
            try:
                comp_name = f"thread_{thread_id}_component"
                monitor.register_component(comp_name)

                for i in range(5):
                    monitor.update_stats(comp_name, {
                        "operations_count": 1,
                        "queue_size": thread_id
                    })
                    monitor.record_operation(comp_name, success=True, duration=0.01)

            except Exception as e:
                errors.append(f"Thread {thread_id}: {str(e)}")

        # Запуск нескольких потоков
        threads = []
        for i in range(5):
            t = threading.Thread(target=monitor_operations, args=(i,))
            threads.append(t)
            t.start()

        # Ожидание завершения
        for t in threads:
            t.join()

        # Проверка отсутствия ошибок
        assert len(errors) == 0

        # Проверка что компоненты зарегистрированы
        all_stats = monitor.get_all_stats()
        assert len(all_stats) == 5

    def test_stats_persistence_smoke(self):
        """Базовая проверка сохранения статистики"""
        monitor = ComponentMonitor()

        monitor.register_component("persistent_component")

        # Обновление статистики
        initial_stats = {"operations_count": 10, "success_count": 8}
        monitor.update_stats("persistent_component", initial_stats)

        # Получение статистики несколько раз
        for _ in range(3):
            stats = monitor.get_stats("persistent_component")
            assert stats.operations_count == 10
            assert stats.success_count == 8

    def test_large_number_of_components(self):
        """Тест с большим количеством компонентов"""
        monitor = ComponentMonitor()

        # Регистрация множества компонентов
        for i in range(50):
            comp_name = f"component_{i:03d}"
            monitor.register_component(comp_name)
            monitor.update_stats(comp_name, {"operations_count": i})

        # Проверка что все компоненты зарегистрированы
        all_stats = monitor.get_all_stats()
        assert len(all_stats) == 50

        # Проверка конкретных значений
        for i in range(50):
            comp_name = f"component_{i:03d}"
            stats = monitor.get_stats(comp_name)
            assert stats.operations_count == i

    def test_monitor_error_recovery(self):
        """Восстановление после ошибок мониторов"""
        monitor = ComponentMonitor()

        monitor.register_component("error_component")

        # Добавление монитора, который вызывает ошибку
        def failing_monitor():
            raise ValueError("Test monitor error")

        monitor.add_monitor("error_component", "failing_monitor", failing_monitor)

        # Выполнение мониторинга (не должно вызвать исключение)
        monitor.run_monitors("error_component")

        # Компонент должен продолжать работать
        stats = monitor.get_stats("error_component")
        assert stats is not None

    def test_clear_and_reset_operations(self):
        """Операции очистки и сброса"""
        monitor = ComponentMonitor()

        monitor.register_component("reset_component")
        monitor.update_stats("reset_component", {"operations_count": 100})
        monitor.record_operation("reset_component", success=True, duration=0.1)

        # Проверка что данные есть
        stats = monitor.get_stats("reset_component")
        assert stats.operations_count == 101

        # Очистка статистики
        monitor.clear_stats("reset_component")

        # Проверка что данные сброшены
        stats = monitor.get_stats("reset_component")
        assert stats.operations_count == 0
        assert stats.success_count == 0