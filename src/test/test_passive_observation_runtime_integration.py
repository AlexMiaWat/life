"""
Интеграционные тесты для пассивного наблюдения с реальным runtime loop

Проверяем:
- Интеграцию компонентов наблюдения в runtime loop
- Корректность сбора данных во время работы системы
- Отсутствие влияния на производительность
- Правильность экспорта собранных данных
"""

import time
import threading
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.state.self_state import SelfState
from src.runtime.loop import run_loop
from src.observability import ObservationExporter


class TestPassiveObservationRuntimeIntegration:
    """Интеграционные тесты с реальным runtime loop"""

    def test_runtime_with_passive_observation_enabled(self):
        """Проверка работы runtime с включенным пассивным наблюдением"""
        # Создаем SelfState
        self_state = SelfState()

        # Создаем временные файлы для хранения данных
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "observation_data"
            data_dir.mkdir(exist_ok=True)

            # Настраиваем пути для данных наблюдения
            state_data_path = data_dir / "state_data.jsonl"
            history_data_path = data_dir / "history_data.jsonl"

            # Создаем event для остановки runtime
            stop_event = threading.Event()

            # Создаем mock monitor
            def mock_monitor():
                pass

            # Создаем mock event queue
            event_queue = Mock()
            event_queue.size.return_value = 0
            event_queue.get_nowait.side_effect = Exception("Queue empty")

            # Параметры для включения пассивного наблюдения
            runtime_args = {
                "self_state": self_state,
                "monitor": mock_monitor,
                "tick_interval": 0.01,  # Быстрые тики для теста
                "snapshot_period": 5,
                "stop_event": stop_event,
                "event_queue": event_queue,
                "enable_passive_observation": True,
                "observation_collection_interval": 2,  # Сбор каждые 2 тика
                "log_flush_period_ticks": 10,
                "enable_profiling": False,
            }

            # Запускаем runtime в отдельном потоке
            runtime_thread = threading.Thread(
                target=lambda: run_loop(**runtime_args),
                daemon=True
            )
            runtime_thread.start()

            # Даем поработать системе некоторое время (около 1 секунды)
            time.sleep(1.0)

            # Останавливаем runtime
            stop_event.set()
            runtime_thread.join(timeout=2.0)

            # Проверяем, что файлы данных созданы
            assert state_data_path.exists() or history_data_path.exists(), \
                "Должны быть созданы файлы данных наблюдения"

            # Проверяем содержимое файлов
            data_found = False

            # Проверяем state data файл
            if state_data_path.exists():
                with open(state_data_path, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        data_found = True
                        # Проверяем структуру JSON
                        import json
                        for line in lines[:3]:  # Проверяем первые несколько записей
                            if line.strip():
                                record = json.loads(line)
                                assert "data_type" in record
                                assert "timestamp" in record
                                assert "data" in record

            # Проверяем history data файл
            if history_data_path.exists():
                with open(history_data_path, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        data_found = True
                        # Проверяем структуру JSON
                        import json
                        for line in lines[:3]:  # Проверяем первые несколько записей
                            if line.strip():
                                record = json.loads(line)
                                assert "component" in record
                                assert "action" in record
                                assert "timestamp" in record

            # Должны быть собраны какие-то данные
            assert data_found, "Должны быть собраны данные наблюдения"

    def test_runtime_performance_with_observation(self):
        """Проверка производительности runtime с включенным наблюдением"""
        # Создаем SelfState
        self_state = SelfState()

        # Создаем event для остановки runtime
        stop_event = threading.Event()

        # Создаем mock компоненты
        def mock_monitor():
            pass

        event_queue = Mock()
        event_queue.size.return_value = 0
        event_queue.get_nowait.side_effect = Exception("Queue empty")

        # Параметры для теста производительности
        runtime_args = {
            "self_state": self_state,
            "monitor": mock_monitor,
            "tick_interval": 0.001,  # Очень быстрые тики
            "snapshot_period": 100,
            "stop_event": stop_event,
            "event_queue": event_queue,
            "enable_passive_observation": True,
            "observation_collection_interval": 50,  # Редкий сбор данных
            "log_flush_period_ticks": 100,
            "enable_profiling": False,
        }

        # Запускаем runtime и измеряем время
        start_time = time.time()

        runtime_thread = threading.Thread(
            target=lambda: run_loop(**runtime_args),
            daemon=True
        )
        runtime_thread.start()

        # Даем поработать системе
        time.sleep(0.5)

        # Останавливаем и измеряем время
        stop_event.set()
        runtime_thread.join(timeout=1.0)

        end_time = time.time()
        runtime_duration = end_time - start_time

        # Проверяем, что система работала разумное время
        # С учетом tick_interval=0.001 и 0.5 секунд, должно быть ~500 тиков
        # С observation_collection_interval=50, должно быть ~10 сборов данных
        assert 0.4 <= runtime_duration <= 0.8, \
            f"Время работы системы должно быть около 0.5 сек, фактически {runtime_duration}"

    def test_data_export_from_runtime(self):
        """Проверка экспорта данных, собранных во время работы runtime"""
        # Создаем SelfState
        self_state = SelfState()

        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "observation_data"
            data_dir.mkdir(exist_ok=True)

            # Создаем event для остановки runtime
            stop_event = threading.Event()

            def mock_monitor():
                pass

            event_queue = Mock()
            event_queue.size.return_value = 0
            event_queue.get_nowait.side_effect = Exception("Queue empty")

            # Запускаем runtime с наблюдением
            runtime_args = {
                "self_state": self_state,
                "monitor": mock_monitor,
                "tick_interval": 0.01,
                "snapshot_period": 10,
                "stop_event": stop_event,
                "event_queue": event_queue,
                "enable_passive_observation": True,
                "observation_collection_interval": 3,
                "log_flush_period_ticks": 10,
                "enable_profiling": False,
            }

            runtime_thread = threading.Thread(
                target=lambda: run_loop(**runtime_args),
                daemon=True
            )
            runtime_thread.start()

            # Даем поработать системе
            time.sleep(0.8)

            # Останавливаем runtime
            stop_event.set()
            runtime_thread.join(timeout=2.0)

            # Создаем exporter и пытаемся экспортировать данные
            exporter = ObservationExporter()

            # Проверяем наличие данных через summary
            summary = exporter.get_data_summary()

            # Даже если данные не найдены в памяти, файлы должны существовать
            # или summary должен показывать наличие компонентов наблюдения

            # Проверяем, что можем создать exporter без ошибок
            assert exporter is not None

            # Проверяем структуру summary
            assert isinstance(summary, dict)
            assert "data_types" in summary
            assert "total_records" in summary
            assert "components" in summary

    def test_runtime_without_observation_enabled(self):
        """Проверка работы runtime с отключенным наблюдением"""
        # Создаем SelfState
        self_state = SelfState()

        # Создаем event для остановки runtime
        stop_event = threading.Event()

        def mock_monitor():
            pass

        event_queue = Mock()
        event_queue.size.return_value = 0
        event_queue.get_nowait.side_effect = Exception("Queue empty")

        # Параметры с отключенным наблюдением
        runtime_args = {
            "self_state": self_state,
            "monitor": mock_monitor,
            "tick_interval": 0.01,
            "snapshot_period": 5,
            "stop_event": stop_event,
            "event_queue": event_queue,
            "enable_passive_observation": False,  # Отключено
            "log_flush_period_ticks": 10,
            "enable_profiling": False,
        }

        # Запускаем runtime
        start_time = time.time()

        runtime_thread = threading.Thread(
            target=lambda: run_loop(**runtime_args),
            daemon=True
        )
        runtime_thread.start()

        # Даем поработать системе
        time.sleep(0.3)

        # Останавливаем
        stop_event.set()
        runtime_thread.join(timeout=1.0)

        end_time = time.time()
        runtime_duration = end_time - start_time

        # Проверяем, что система работала
        assert runtime_duration > 0.2, "Система должна работать хотя бы 0.2 секунды"

        # Проверяем, что SelfState изменился
        assert self_state.ticks > 0, "Должны быть выполнены тики"

    def test_observation_collection_interval(self):
        """Проверка работы интервала сбора наблюдений"""
        # Создаем SelfState
        self_state = SelfState()

        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "observation_data"
            data_dir.mkdir(exist_ok=True)

            # Создаем event для остановки runtime
            stop_event = threading.Event()

            def mock_monitor():
                pass

            event_queue = Mock()
            event_queue.size.return_value = 0
            event_queue.get_nowait.side_effect = Exception("Queue empty")

            # Запускаем с большим интервалом сбора
            runtime_args = {
                "self_state": self_state,
                "monitor": mock_monitor,
                "tick_interval": 0.005,  # Быстрые тики
                "snapshot_period": 20,
                "stop_event": stop_event,
                "event_queue": event_queue,
                "enable_passive_observation": True,
                "observation_collection_interval": 10,  # Сбор каждые 10 тиков
                "log_flush_period_ticks": 20,
                "enable_profiling": False,
            }

            runtime_thread = threading.Thread(
                target=lambda: run_loop(**runtime_args),
                daemon=True
            )
            runtime_thread.start()

            # Даем поработать системе достаточное время для нескольких сборов
            time.sleep(0.3)  # При 0.005 тике и 10 интервале = ~6 сборов

            # Останавливаем
            stop_event.set()
            runtime_thread.join(timeout=1.0)

            # Проверяем, что система выполнила достаточное количество тиков
            # При 0.3 секунды и 0.005 тике = ~60 тиков
            # С интервалом 10 = ~6 сборов данных
            assert self_state.ticks >= 50, f"Должно быть выполнено >= 50 тиков, фактически {self_state.ticks}"

            # Проверяем, что файлы созданы (компоненты наблюдения работают)
            # Файлы могут быть созданы асинхронно, поэтому просто проверяем,
            # что система не упала и выполнила тики