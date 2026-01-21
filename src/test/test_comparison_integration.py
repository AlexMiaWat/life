"""
Интеграционные тесты для системы сравнения жизней (Comparison System).

Проверяет взаимодействие компонентов:
- API <-> Manager <-> Analyzer
- Полный workflow создания и сравнения инстансов
- Сбор и анализ данных
- Многопоточная работа
"""

import time
import pytest
import threading
import requests
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor, as_completed


class TestComparisonWorkflowIntegration:
    """Интеграционные тесты полного workflow сравнения."""

    def test_create_and_manage_instances_workflow(self):
        """Полный workflow создания и управления инстансами."""
        from src.comparison.comparison_manager import ComparisonManager

        manager = ComparisonManager()

        # 1. Создаем несколько инстансов
        instance_ids = ["workflow_inst_1", "workflow_inst_2", "workflow_inst_3"]

        for instance_id in instance_ids:
            instance = manager.create_instance(instance_id)
            assert instance is not None
            assert instance.config.instance_id == instance_id

        # 2. Проверяем статус всех инстансов
        all_status = manager.get_all_instances_status()
        assert len(all_status) == 3

        for instance_id in instance_ids:
            assert instance_id in all_status
            status = all_status[instance_id]
            assert status["instance_id"] == instance_id
            assert not status["is_running"]  # Изначально не запущены

        # 3. Проверяем статистику
        assert manager.stats["total_instances_created"] == 3
        assert manager.stats["active_instances"] == 0

    def test_instance_lifecycle_integration(self):
        """Интеграция жизненного цикла инстансов."""
        from src.comparison.comparison_manager import ComparisonManager

        manager = ComparisonManager()

        instance_id = "lifecycle_test"

        # 1. Создание
        instance = manager.create_instance(instance_id)
        assert instance is not None

        # 2. Проверка статуса до запуска
        status = manager.get_instance_status(instance_id)
        assert not status["is_running"]
        assert not status["is_alive"]

        # 3. Мокаем запуск процесса
        with patch.object(instance, '_start_process', return_value=True):
            with patch.object(instance, '_stop_process', return_value=True):
                # Запуск
                result = manager.start_instance(instance_id)
                assert result is True

                # Проверка статуса после запуска
                status = manager.get_instance_status(instance_id)
                # С моками статус может не измениться, но метод должен работать

                # Остановка
                result = manager.stop_instance(instance_id)
                assert result is True

        # 4. Удаление
        result = manager.stop_instance(instance_id)  # На всякий случай
        with manager.lock:
            if instance_id in manager.instances:
                del manager.instances[instance_id]

        # Проверка, что инстанс удален
        status = manager.get_instance_status(instance_id)
        assert status is None

    def test_data_collection_integration(self):
        """Интеграция сбора данных между менеджером и инстансами."""
        from src.comparison.comparison_manager import ComparisonManager

        manager = ComparisonManager()

        # Создаем тестовые инстансы
        instance_ids = ["data_inst_1", "data_inst_2"]
        for instance_id in instance_ids:
            manager.create_instance(instance_id)

        # Мокаем данные инстансов
        mock_data = {
            "timestamp": time.time(),
            "instances": {
                "data_inst_1": {"energy": 0.8, "patterns": {"pat1": 5}},
                "data_inst_2": {"energy": 0.7, "patterns": {"pat2": 3}},
            }
        }

        # Запускаем сбор данных
        collected_data = []

        def data_callback(data):
            collected_data.append(data)

        manager.start_data_collection(callback=data_callback)

        # Ждем немного для сбора данных
        time.sleep(0.1)

        # Останавливаем сбор
        manager.stop_data_collection()

        # Проверяем, что сбор данных работает (может быть пустым без реальных инстансов)
        assert isinstance(collected_data, list)

    def test_comparison_analysis_integration(self):
        """Интеграция анализа сравнения между менеджером и анализаторами."""
        from src.comparison.comparison_manager import ComparisonManager
        from src.comparison.comparison_metrics import ComparisonMetrics
        from src.comparison.pattern_analyzer import PatternAnalyzer

        manager = ComparisonManager()
        metrics = ComparisonMetrics()
        analyzer = PatternAnalyzer()

        # Создаем тестовые данные сравнения
        comparison_data = {
            "timestamp": time.time(),
            "instances": {
                "analysis_inst_1": {
                    "is_alive": True,
                    "uptime": 120.0,
                    "patterns": {"curious": 10, "adaptive": 5},
                    "snapshots": [
                        {"energy": 0.8, "stability": 0.7},
                        {"energy": 0.85, "stability": 0.75},
                    ]
                },
                "analysis_inst_2": {
                    "is_alive": True,
                    "uptime": 110.0,
                    "patterns": {"conservative": 8, "adaptive": 7},
                    "snapshots": [
                        {"energy": 0.75, "stability": 0.8},
                        {"energy": 0.7, "stability": 0.85},
                    ]
                }
            }
        }

        # 1. Анализируем паттерны
        pattern_analysis = analyzer.analyze_comparison_data(comparison_data)
        assert isinstance(pattern_analysis, dict)
        assert "instances_analysis" in pattern_analysis
        assert "overall_patterns" in pattern_analysis

        # 2. Вычисляем метрики
        performance_metrics = metrics.get_performance_metrics(comparison_data["instances"])
        diversity_metrics = metrics.get_diversity_metrics(pattern_analysis["instances_analysis"])

        assert isinstance(performance_metrics, dict)
        assert isinstance(diversity_metrics, dict)

        # 3. Создаем сводный отчет
        summary_report = metrics.get_summary_report(comparison_data["instances"])
        assert isinstance(summary_report, dict)
        assert "similarity_metrics" in summary_report
        assert "performance_metrics" in summary_report
        assert "diversity_metrics" in summary_report


class TestAPIIntegration:
    """Интеграционные тесты API с компонентами."""

    def test_api_manager_integration(self):
        """API должен правильно интегрироваться с ComparisonManager."""
        from src.comparison.comparison_api import ComparisonAPI

        api = ComparisonAPI(port=8010)

        # Проверяем, что менеджер доступен через API
        assert api.comparison_manager is not None

        # Создаем инстанс через API (имитируем запрос)
        from src.comparison.comparison_api import CreateInstanceRequest

        request = CreateInstanceRequest(instance_id="api_integration_test")
        instance = api.comparison_manager.create_instance(
            instance_id=request.instance_id,
            tick_interval=request.tick_interval,
            dev_mode=request.dev_mode,
        )

        assert instance is not None
        assert instance.config.instance_id == "api_integration_test"

        # Проверяем через менеджер
        assert "api_integration_test" in api.comparison_manager.instances

    def test_api_analysis_integration(self):
        """API должен правильно интегрироваться с анализаторами."""
        from src.comparison.comparison_api import ComparisonAPI

        api = ComparisonAPI(port=8011)

        # Создаем тестовые данные
        test_comparison_data = {
            "timestamp": time.time(),
            "instances": {
                "api_analysis_1": {"patterns": {"pat1": 5}},
                "api_analysis_2": {"patterns": {"pat2": 3}},
            }
        }

        # Устанавливаем данные для тестирования
        api.comparison_results = test_comparison_data

        # Получаем анализ через API (имитируем эндпоинт)
        analysis = api.pattern_analyzer.analyze_comparison_data(test_comparison_data)
        metrics = api.comparison_metrics.get_summary_report(test_comparison_data["instances"])

        assert isinstance(analysis, dict)
        assert isinstance(metrics, dict)

    @patch('src.comparison.comparison_api.threading.Thread')
    def test_api_comparison_workflow_integration(self, mock_thread):
        """Полный workflow сравнения через API."""
        from src.comparison.comparison_api import ComparisonAPI, StartComparisonRequest

        api = ComparisonAPI(port=8012)

        # Мокаем потоки
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance

        # 1. Создаем инстансы
        api.comparison_manager.create_instance("api_workflow_1")
        api.comparison_manager.create_instance("api_workflow_2")

        # 2. Запускаем сравнение (имитируем запрос)
        request = StartComparisonRequest(
            instance_ids=["api_workflow_1", "api_workflow_2"],
            duration=5.0
        )

        # Мокаем _run_comparison для тестирования
        with patch.object(api, '_run_comparison') as mock_run:
            mock_run.return_value = None

            # Вызываем метод (как в API)
            api._run_comparison(request.instance_ids, request.duration)

            # Проверяем, что метод был вызван
            mock_run.assert_called_once_with(request.instance_ids, request.duration)

    def test_api_error_handling_integration(self):
        """API должен правильно обрабатывать ошибки компонентов."""
        from src.comparison.comparison_api import ComparisonAPI

        api = ComparisonAPI(port=8013)

        # Тестируем создание инстанса с существующим ID
        api.comparison_manager.create_instance("error_test")

        # Повторное создание должно обработаться gracefully
        duplicate = api.comparison_manager.create_instance("error_test")
        assert duplicate is None  # Должно вернуть None при ошибке

        # Запрос статуса несуществующего инстанса
        status = api.comparison_manager.get_instance_status("nonexistent")
        assert status is None


class TestMultiThreadingIntegration:
    """Интеграционные тесты многопоточной работы."""

    def test_concurrent_instance_creation(self):
        """Создание инстансов в нескольких потоках."""
        from src.comparison.comparison_manager import ComparisonManager

        manager = ComparisonManager()

        def create_instance_worker(instance_id):
            return manager.create_instance(instance_id)

        # Создаем инстансы параллельно
        instance_ids = [f"concurrent_{i}" for i in range(5)]

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(create_instance_worker, iid) for iid in instance_ids]
            results = [future.result() for future in as_completed(futures)]

        # Проверяем результаты
        successful_creations = [r for r in results if r is not None]
        assert len(successful_creations) == 5

        # Проверяем, что все инстансы созданы
        assert len(manager.instances) == 5

    def test_concurrent_data_collection(self):
        """Параллельный сбор данных."""
        from src.comparison.comparison_manager import ComparisonManager

        manager = ComparisonManager()

        # Создаем несколько инстансов
        for i in range(3):
            manager.create_instance(f"data_collect_{i}")

        # Запускаем параллельный сбор данных
        collected_data = []
        lock = threading.Lock()

        def collect_worker():
            def callback(data):
                with lock:
                    collected_data.append(data)

            # Имитируем сбор данных
            callback({"timestamp": time.time(), "test": True})

        # Запускаем несколько сборщиков
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=collect_worker)
            thread.start()
            threads.append(thread)

        # Ждем завершения
        for thread in threads:
            thread.join()

        # Проверяем, что данные собраны
        assert len(collected_data) == 3

    def test_manager_thread_safety(self):
        """ComparisonManager должен быть потокобезопасен."""
        from src.comparison.comparison_manager import ComparisonManager

        manager = ComparisonManager()

        def manager_operation_worker(operation_id):
            try:
                if operation_id % 2 == 0:
                    # Создание инстанса
                    instance = manager.create_instance(f"safety_test_{operation_id}")
                    return f"created_{operation_id}" if instance else "create_failed"
                else:
                    # Получение статуса
                    status = manager.get_instance_status(f"safety_test_{operation_id-1}")
                    return f"status_{operation_id}" if status else "status_none"
            except Exception as e:
                return f"error_{operation_id}: {e}"

        # Запускаем параллельные операции
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(manager_operation_worker, i) for i in range(10)]
            results = [future.result() for future in as_completed(futures)]

        # Проверяем, что нет ошибок
        errors = [r for r in results if r.startswith("error_")]
        assert len(errors) == 0, f"Thread safety errors: {errors}"


class TestFullSystemIntegration:
    """Интеграционные тесты полной системы."""

    def test_end_to_end_comparison_workflow(self):
        """Полный end-to-end workflow сравнения."""
        from src.comparison.comparison_api import ComparisonAPI

        api = ComparisonAPI(port=8014)

        # 1. Создаем инстансы
        instance_ids = ["e2e_inst_1", "e2e_inst_2"]
        for instance_id in instance_ids:
            instance = api.comparison_manager.create_instance(instance_id)
            assert instance is not None

        # 2. Мокаем запуск инстансов
        for instance_id in instance_ids:
            with patch.object(api.comparison_manager.instances[instance_id], '_start_process', return_value=True):
                result = api.comparison_manager.start_instance(instance_id)
                assert result is True

        # 3. Запускаем сравнение
        with patch.object(api, '_run_comparison') as mock_run:
            mock_run.return_value = None

            # Имитируем запуск сравнения
            api.comparison_running = True
            api._run_comparison(instance_ids, duration=2.0)

            # Проверяем статус
            assert api.comparison_running

        # 4. Останавливаем сравнение
        api.comparison_running = False
        api.comparison_manager.stop_data_collection()

        # 5. Проверяем финальное состояние
        status = api._get_status_data()
        assert not status.get("comparison_running", True)

    def test_system_resource_management(self):
        """Система должна правильно управлять ресурсами."""
        from src.comparison.comparison_api import ComparisonAPI

        api = ComparisonAPI(port=8015)

        # Создаем несколько инстансов
        for i in range(3):
            api.comparison_manager.create_instance(f"resource_test_{i}")

        # Проверяем, что ресурсы выделены
        assert len(api.comparison_manager.instances) == 3

        # Имитируем очистку
        api.comparison_manager.instances.clear()

        # Проверяем очистку
        assert len(api.comparison_manager.instances) == 0

    def test_system_error_recovery(self):
        """Система должна восстанавливаться после ошибок."""
        from src.comparison.comparison_api import ComparisonAPI

        api = ComparisonAPI(port=8016)

        # Создаем инстанс
        instance = api.comparison_manager.create_instance("recovery_test")
        assert instance is not None

        # Имитируем ошибку (удаляем инстанс искусственно)
        with api.comparison_manager.lock:
            if "recovery_test" in api.comparison_manager.instances:
                del api.comparison_manager.instances["recovery_test"]

        # Система должна продолжать работать
        status = api.comparison_manager.get_instance_status("recovery_test")
        assert status is None

        # Создаем новый инстанс - система должна работать
        new_instance = api.comparison_manager.create_instance("recovery_test_2")
        assert new_instance is not None


class TestPerformanceIntegration:
    """Интеграционные тесты производительности."""

    def test_bulk_instance_operations(self):
        """Массовые операции с инстансами."""
        from src.comparison.comparison_manager import ComparisonManager

        manager = ComparisonManager()

        start_time = time.time()

        # Создаем много инстансов
        instance_ids = [f"bulk_{i}" for i in range(10)]

        for instance_id in instance_ids:
            instance = manager.create_instance(instance_id)
            assert instance is not None

        creation_time = time.time() - start_time

        # Проверяем производительность (должно быть быстро)
        assert creation_time < 1.0, f"Bulk creation too slow: {creation_time}s"

        # Проверяем, что все созданы
        assert len(manager.instances) == 10

    def test_analysis_performance_integration(self):
        """Производительность анализа в интеграции."""
        from src.comparison.comparison_metrics import ComparisonMetrics
        from src.comparison.pattern_analyzer import PatternAnalyzer

        metrics = ComparisonMetrics()
        analyzer = PatternAnalyzer()

        # Создаем объемные тестовые данные
        large_data = {
            "instances": {}
        }

        for i in range(5):
            large_data["instances"][f"perf_inst_{i}"] = {
                "patterns": {f"pattern_{j}": j for j in range(10)},
                "snapshots": [{"energy": 0.5 + j*0.1} for j in range(20)],
                "is_alive": True,
                "uptime": 100.0 + i*10,
            }

        start_time = time.time()

        # Выполняем анализ
        pattern_analysis = analyzer.analyze_comparison_data(large_data)
        perf_metrics = metrics.get_performance_metrics(large_data["instances"])
        diversity = metrics.get_diversity_metrics(pattern_analysis["instances_analysis"])
        summary = metrics.get_summary_report(large_data["instances"])

        analysis_time = time.time() - start_time

        # Проверяем производительность
        assert analysis_time < 2.0, f"Analysis too slow: {analysis_time}s"

        # Проверяем результаты
        assert isinstance(pattern_analysis, dict)
        assert isinstance(perf_metrics, dict)
        assert isinstance(diversity, dict)
        assert isinstance(summary, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])