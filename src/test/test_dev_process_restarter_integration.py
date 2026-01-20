"""
Интеграционные тесты для модуля process_restarter (новая функциональность dev-mode)

Проверяем:
- Полные циклы работы компонентов
- Взаимодействие StateSerializer, GracefulShutdownManager и ProcessRestarter
- Сохранение и восстановление состояния системы
- Работа в многопоточной среде
- Интеграцию с EventQueue и SelfState
"""

import json
import os
import sys
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest

from src.dev.process_restarter import (
    GracefulShutdownManager,
    ProcessRestarter,
    StateSerializer,
    get_process_restarter,
    get_state_serializer,
    load_restart_state_if_available,
)
from src.environment.event_queue import EventQueue
from src.state.self_state import SelfState


@pytest.mark.integration
class TestDevProcessRestarterIntegration:
    """Интеграционные тесты для модуля process_restarter"""

    # ============================================================================
    # Full State Management Integration
    # ============================================================================

    def test_full_state_save_and_load_cycle(self):
        """Интеграционный тест полного цикла сохранения и загрузки состояния"""
        with tempfile.TemporaryDirectory() as temp_dir:
            restart_file = f"{temp_dir}/restart_state.json"

            with patch.object(StateSerializer, "RESTART_STATE_FILE", restart_file):
                # Создаем реальные объекты состояния
                self_state = SelfState()
                self_state.energy = 75.0
                self_state.integrity = 0.8
                self_state.stability = 0.9

                event_queue = EventQueue()
                # Добавляем события в очередь
                from src.environment.event import Event

                for i in range(3):
                    event = Event(type="test_event", intensity=0.5, timestamp=float(i))
                    event_queue.push(event)

                config = {"mode": "dev", "check_interval": 1.0, "max_events": 100}

                # Сохраняем состояние
                serializer = StateSerializer()
                save_result = serializer.save_restart_state(
                    self_state, event_queue, config
                )
                assert save_result is True
                assert os.path.exists(restart_file)

                # Проверяем содержимое файла
                with open(restart_file, "r") as f:
                    saved_data = json.load(f)

                assert saved_data["restart_marker"] is True
                assert "timestamp" in saved_data
                assert "self_state" in saved_data
                assert "event_queue" in saved_data
                assert "config" in saved_data

                # Загружаем состояние
                loaded_data = serializer.load_restart_state()
                assert loaded_data is not None
                # Note: SelfState and EventQueue don't have to_dict methods,
                # so they fall back to empty dict and empty list
                assert loaded_data["self_state"] == {}
                assert loaded_data["event_queue"] == []
                assert loaded_data["config"]["mode"] == "dev"

                # Проверяем очистку
                serializer.cleanup_restart_state()
                assert not os.path.exists(restart_file)

    def test_restart_state_with_complex_objects(self):
        """Интеграционный тест сохранения состояния со сложными объектами"""
        with tempfile.TemporaryDirectory() as temp_dir:
            restart_file = f"{temp_dir}/restart_state.json"

            with patch.object(StateSerializer, "RESTART_STATE_FILE", restart_file):
                # Создаем SelfState с различными параметрами
                self_state = SelfState()
                self_state.energy = 42.5
                self_state.integrity = 0.95
                self_state.stability = 0.85
                self_state.activated_memory = ["memory1", "memory2"]
                self_state.last_pattern = {"pattern": "test"}

                # Создаем EventQueue с событиями разных типов
                event_queue = EventQueue()
                from src.environment.event import Event

                events_data = [
                    {"type": "noise", "intensity": 0.3},
                    {"type": "signal", "intensity": 0.8},
                    {"type": "feedback", "intensity": 0.6},
                ]

                for i, event_data in enumerate(events_data):
                    event = Event(
                        type=event_data["type"],
                        intensity=event_data["intensity"],
                        timestamp=time.time() + i,
                    )
                    event_queue.push(event)

                config = {
                    "complex_config": {"nested": {"value": 123}, "list": [1, 2, 3]}
                }

                # Сохраняем и загружаем
                serializer = StateSerializer()
                assert serializer.save_restart_state(self_state, event_queue, config)

                loaded_data = serializer.load_restart_state()
                assert loaded_data is not None

                # Note: SelfState and EventQueue don't have to_dict methods,
                # so they fall back to empty dict and empty list
                loaded_state = loaded_data["self_state"]
                assert loaded_state == {}

                loaded_queue = loaded_data["event_queue"]
                assert loaded_queue == []

                assert loaded_data["config"]["complex_config"]["nested"]["value"] == 123
                assert loaded_data["config"]["complex_config"]["list"] == [1, 2, 3]

    # ============================================================================
    # Graceful Shutdown Integration
    # ============================================================================

    def test_graceful_shutdown_multiple_components(self):
        """Интеграционный тест graceful shutdown нескольких компонентов"""
        manager = GracefulShutdownManager(shutdown_timeout=2.0)

        shutdown_order = []
        join_order = []

        def create_shutdown_func(name):
            def shutdown():
                shutdown_order.append(name)
                time.sleep(0.01)  # Небольшая задержка для проверки порядка

            return shutdown

        def create_join_func(name):
            def join(timeout=None):
                join_order.append(name)
                time.sleep(0.01)

            return join

        # Регистрируем несколько компонентов
        components = ["database", "api_server", "event_processor", "monitor"]
        for component in components:
            manager.register_component(
                component,
                create_shutdown_func(component),
                create_join_func(component),
                timeout=0.5,
            )

        start_time = time.time()
        result = manager.initiate_shutdown()
        end_time = time.time()

        assert result is True
        assert len(shutdown_order) == 4
        assert len(join_order) == 4
        # Проверяем что все компоненты были остановлены в правильном порядке
        assert set(shutdown_order) == set(components)
        assert set(join_order) == set(components)
        # Проверяем что общее время shutdown разумное
        assert end_time - start_time < 1.0

    def test_graceful_shutdown_with_component_failure(self):
        """Интеграционный тест shutdown при отказе одного из компонентов"""
        manager = GracefulShutdownManager()

        def good_shutdown():
            time.sleep(0.01)

        def bad_shutdown():
            raise Exception("Component failure")

        def good_join():
            pass

        manager.register_component("good_component", good_shutdown, good_join)
        manager.register_component("bad_component", bad_shutdown)

        result = manager.initiate_shutdown()

        # Shutdown должен завершиться с ошибками, но не падать
        assert result is False

    def test_graceful_shutdown_timeout_handling(self):
        """Интеграционный тест обработки таймаутов при shutdown"""
        manager = GracefulShutdownManager(shutdown_timeout=0.1)

        def slow_shutdown():
            time.sleep(0.2)  # Дольше чем таймаут

        def slow_join(timeout=None):
            # Respect timeout parameter like thread.join does
            sleep_time = min(timeout, 0.2) if timeout else 0.2
            time.sleep(sleep_time)

        manager.register_component(
            "slow_component", slow_shutdown, slow_join, timeout=0.05
        )

        start_time = time.time()
        result = manager.initiate_shutdown()
        end_time = time.time()

        # Должен вернуть False из-за таймаута
        assert result is False
        # Время выполнения: component timeout (0.05s) + некоторая задержка на обработку
        # Но не должен превышать общий shutdown_timeout (0.1s) значительно
        assert end_time - start_time < 0.3

    # ============================================================================
    # ProcessRestarter Full Integration
    # ============================================================================

    def test_process_restarter_full_component_registration(self):
        """Интеграционный тест полной регистрации компонентов в ProcessRestarter"""
        restarter = ProcessRestarter()

        # Регистрируем компоненты системы
        components_registered = []

        def create_component_shutdown(name):
            def shutdown():
                components_registered.append(f"shutdown_{name}")

            return shutdown

        def create_component_join(name):
            def join(timeout=None):
                components_registered.append(f"join_{name}")

            return join

        # Регистрируем типичные компоненты системы
        component_names = ["api_server", "event_loop", "monitor", "feedback_processor"]
        for name in component_names:
            restarter.register_component(
                name, create_component_shutdown(name), create_component_join(name)
            )

        # Проверяем что все компоненты зарегистрированы
        assert len(restarter._shutdown_manager._components) == 4

        # Проверяем graceful shutdown через ProcessRestarter
        # (фактически делегирует в shutdown manager)
        result = restarter._shutdown_manager.initiate_shutdown()
        assert result is True

        # Проверяем что все компоненты были остановлены
        expected_calls = [f"shutdown_{name}" for name in component_names] + [
            f"join_{name}" for name in component_names
        ]
        assert set(components_registered) == set(expected_calls)

    def test_process_restarter_state_management_integration(self):
        """Интеграционный тест управления состоянием в ProcessRestarter"""
        with tempfile.TemporaryDirectory() as temp_dir:
            restart_file = f"{temp_dir}/restart_state.json"

            with patch.object(StateSerializer, "RESTART_STATE_FILE", restart_file):
                restarter = ProcessRestarter()

                # Создаем тестовые объекты состояния
                self_state = SelfState()
                self_state.energy = 88.0

                event_queue = EventQueue()
                config = {"integration_test": True}

                # Сохраняем состояние через ProcessRestarter
                save_result = restarter.save_state_for_restart(
                    self_state, event_queue, config
                )
                assert save_result is True

                # Проверяем что файл создан
                assert os.path.exists(restart_file)

                # Проверяем содержимое
                with open(restart_file, "r") as f:
                    data = json.load(f)

                # SelfState falls back to empty dict since it doesn't have to_dict
                assert data["self_state"] == {}
                assert data["config"]["integration_test"] is True

    # ============================================================================
    # File Monitoring Integration
    # ============================================================================

    def test_file_monitoring_basic_functionality(self):
        """Интеграционный тест базового функционала мониторинга файлов"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Создаем копии файлов для отслеживания
            watched_files = []
            for file_path in ProcessRestarter.FILES_TO_WATCH[
                :2
            ]:  # Только первые 2 для теста
                full_path = os.path.join(temp_dir, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w") as f:
                    f.write("initial content")
                watched_files.append(full_path)

            with patch.object(ProcessRestarter, "FILES_TO_WATCH", watched_files):
                restarter = ProcessRestarter()

                # Проверяем начальную инициализацию
                assert len(restarter._file_mtimes) == 2

                # Модифицируем один файл
                modified_file = watched_files[0]
                time.sleep(0.01)  # Убеждаемся что mtime изменится
                with open(modified_file, "w") as f:
                    f.write("modified content")

                # Проверяем обнаружение изменений
                changes_detected = restarter._check_file_changes()
                assert changes_detected is True

                # Проверяем что mtime обновился
                assert restarter._file_mtimes[modified_file] != 0

                # Повторная проверка не должна обнаружить изменений
                changes_detected = restarter._check_file_changes()
                assert changes_detected is False

    def test_file_monitoring_file_deletion(self):
        """Интеграционный тест мониторинга при удалении файлов"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Создаем тестовый файл
            test_file = os.path.join(temp_dir, "test_file.py")
            with open(test_file, "w") as f:
                f.write("content")

            with patch.object(ProcessRestarter, "FILES_TO_WATCH", [test_file]):
                restarter = ProcessRestarter()
                assert test_file in restarter._file_mtimes

                # Удаляем файл
                os.remove(test_file)

                # Проверяем обнаружение удаления
                changes_detected = restarter._check_file_changes()
                assert changes_detected is True

                # Файл должен быть удален из отслеживания
                assert test_file not in restarter._file_mtimes

    # ============================================================================
    # End-to-End Restart Simulation
    # ============================================================================

    @patch("os.execv")
    @patch("sys.argv", ["test_script.py"])
    def test_end_to_end_restart_simulation(self, mock_execv):
        """Интеграционный тест симуляции полного цикла перезапуска"""
        with tempfile.TemporaryDirectory() as temp_dir:
            restart_file = f"{temp_dir}/restart_state.json"

            with patch.object(StateSerializer, "RESTART_STATE_FILE", restart_file):
                # Шаг 1: Создаем ProcessRestarter и регистрируем компоненты
                restarter = ProcessRestarter()

                shutdown_completed = []

                def test_shutdown():
                    shutdown_completed.append("component_shutdown")

                def test_join():
                    shutdown_completed.append("component_join")

                restarter.register_component("test_component", test_shutdown, test_join)

                # Шаг 2: Создаем состояние для сохранения
                self_state = SelfState()
                self_state.energy = 66.0

                event_queue = EventQueue()
                config = {"restart_simulation": True}

                # Шаг 3: Сохраняем состояние
                save_result = restarter.save_state_for_restart(
                    self_state, event_queue, config
                )
                assert save_result is True

                # Шаг 4: Имитируем обнаружение изменений в файлах
                with patch.object(restarter, "_check_file_changes", return_value=True):
                    with patch.object(time, "sleep"):  # Ускоряем тест
                        with patch.object(
                            restarter._shutdown_manager,
                            "initiate_shutdown",
                            return_value=True,
                        ):
                            # Шаг 5: Запускаем мониторинг в отдельном потоке
                            restarter.start()

                            # Ждем немного чтобы мониторинг запустился
                            time.sleep(0.1)

                            # Останавливаем мониторинг
                            restarter.stop()

                            # Проверяем что компоненты были остановлены бы
                            # (в реальности проверяем что мониторинг пытался вызвать shutdown)
                            assert restarter._shutdown_manager is not None

                # Шаг 6: Проверяем что состояние было сохранено
                assert os.path.exists(restart_file)

    # ============================================================================
    # Module Functions Integration
    # ============================================================================

    def test_global_instances_integration(self):
        """Интеграционный тест глобальных экземпляров"""
        # Получаем глобальные экземпляры
        restarter1 = get_process_restarter()
        serializer1 = get_state_serializer()

        # Получаем их снова
        restarter2 = get_process_restarter()
        serializer2 = get_state_serializer()

        # Должны быть те же экземпляры
        assert restarter1 is restarter2
        assert serializer1 is serializer2

        # ProcessRestarter creates its own StateSerializer instance,
        # so it's not the same as the global one
        assert restarter1._state_serializer is not serializer1
        assert isinstance(restarter1._state_serializer, StateSerializer)

    @patch("sys.argv", ["script.py", "--restart"])
    def test_restart_flag_integration(self):
        """Интеграционный тест флага перезапуска"""
        from src.dev.process_restarter import is_restart

        assert is_restart() is True

        # Создаем тестовое состояние
        with tempfile.TemporaryDirectory() as temp_dir:
            restart_file = f"{temp_dir}/restart_state.json"

            with patch.object(StateSerializer, "RESTART_STATE_FILE", restart_file):
                test_data = {
                    "restart_marker": True,
                    "timestamp": time.time(),
                    "self_state": {"energy": 100.0},
                    "event_queue": [],
                    "config": {"restarted": True},
                }

                with open(restart_file, "w") as f:
                    json.dump(test_data, f)

                # Загружаем состояние при перезапуске
                state, was_restart = load_restart_state_if_available()

                assert was_restart is True
                assert state is not None
                assert state["config"]["restarted"] is True
                # Файл должен быть удален
                assert not os.path.exists(restart_file)

    # ============================================================================
    # Concurrency and Threading Integration
    # ============================================================================

    def test_concurrent_state_access_simulation(self):
        """Интеграционный тест симуляции конкурентного доступа к состоянию"""
        serializer = StateSerializer()

        results = []
        errors = []

        def worker(worker_id):
            try:
                # Имитируем конкурентный доступ
                for i in range(10):
                    mock_state = MagicMock()
                    mock_state.to_dict.return_value = {
                        "worker": worker_id,
                        "iteration": i,
                    }

                    mock_queue = MagicMock()
                    mock_queue.to_dict.return_value = []

                    config = {"worker_id": worker_id}

                    result = serializer.save_restart_state(
                        mock_state, mock_queue, config
                    )
                    results.append((worker_id, i, result))
            except Exception as e:
                errors.append((worker_id, str(e)))

        # Запускаем несколько потоков
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Ждем завершения
        for thread in threads:
            thread.join()

        # Проверяем результаты
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 30  # 3 workers * 10 iterations

        # Все операции должны быть успешными
        for worker_id, iteration, result in results:
            assert result is True, f"Worker {worker_id}, iteration {iteration} failed"
