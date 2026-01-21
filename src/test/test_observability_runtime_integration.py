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

from src.observability.async_passive_observer import AsyncPassiveObserver
from src.observability.developer_reports import DeveloperReports
from src.observability.external_observer import RawDataCollector
from src.state.self_state import SelfState


@pytest.mark.integration
class TestObservabilityRuntimeIntegration:
    """Интеграционные тесты observability с runtime"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.temp_files = []
        self.temp_dirs = []

    def teardown_method(self):
        """Очистка после каждого теста"""
        for temp_file in self.temp_files:
            Path(temp_file).unlink(missing_ok=True)
        for temp_dir in self.temp_dirs:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    def create_temp_file(self, suffix='.jsonl'):
        """Создание временного файла"""
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            temp_path = f.name
        self.temp_files.append(temp_path)
        return temp_path

    def create_temp_dir(self):
        """Создание временной директории"""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        return temp_dir

    def create_real_self_state(self):
        """Создание реального SelfState с компонентами"""
        self_state = SelfState()

        # Инициализируем основные параметры
        self_state.energy = 0.8
        self_state.stability = 0.9
        self_state.integrity = 0.95
        self_state.fatigue = 0.1
        self_state.tension = 0.2
        self_state.age = 1000.0
        self_state.ticks = 500

        # Инициализируем память
        self_state.memory = []
        self_state.memory_episodic_size = 150
        self_state.memory_archive_size = 300
        self_state.memory_recent_events = 25

        # Инициализируем параметры обучения
        self_state.learning_params = {
            "learning_rate": 0.01,
            "adaptation_rate": 0.005,
            "memory_decay": 0.001,
            "pattern_recognition_threshold": 0.7
        }

        # Инициализируем параметры адаптации
        self_state.adaptation_params = {
            "energy_threshold": 0.3,
            "stability_threshold": 0.5,
            "recovery_rate": 0.02,
            "stress_tolerance": 0.8
        }

        return self_state

    @pytest.mark.slow
    def test_full_observability_integration_with_runtime(self):
        """Полная интеграция observability с runtime системой"""
        # Создаем временные директории
        data_dir = self.create_temp_dir()
        snapshots_dir = Path(data_dir) / "snapshots"
        snapshots_dir.mkdir()

        # Создаем SelfState
        self_state = self.create_real_self_state()

        # Создаем snapshot файл
        snapshot_path = snapshots_dir / "test_snapshot.json"
        snapshot_data = {
            "timestamp": time.time(),
            "energy": self_state.energy,
            "stability": self_state.stability,
            "integrity": self_state.integrity,
            "fatigue": self_state.fatigue,
            "tension": self_state.tension,
            "age": self_state.age,
            "ticks": self_state.ticks,
            "memory_episodic_size": self_state.memory_episodic_size,
            "memory_archive_size": self_state.memory_archive_size,
            "memory_recent_events": self_state.memory_recent_events,
            "learning_params_count": len(self_state.learning_params),
            "adaptation_params_count": len(self_state.adaptation_params),
            "decision_queue_size": 5,
            "action_queue_size": 2
        }

        with open(snapshot_path, 'w') as f:
            import json
            json.dump(snapshot_data, f)

        # Создаем AsyncPassiveObserver
        observer = AsyncPassiveObserver(
            collection_interval=1.0,  # Быстрый сбор для теста
            snapshots_dir=str(snapshots_dir),
            enabled=True
        )

        try:
            # Даем время на сбор данных
            time.sleep(2.0)

            # Создаем RawDataCollector
            collector = RawDataCollector(snapshots_directory=snapshots_dir)

            # Собираем данные
            report = collector.collect_raw_counters_from_snapshots([snapshot_path])

            # Проверяем структуру отчета
            assert report is not None
            assert report.raw_counters.cycle_count == 1  # Один snapshot
            assert report.raw_counters.memory_entries_count == 450  # episodic + archive

            # Создаем отчеты
            reports = DeveloperReports(data_directory=data_dir)
            daily_report = reports.generate_automated_report("daily", hours=1)

            # Проверяем структуру отчета
            assert "health" in daily_report
            assert "metrics" in daily_report
            assert "insights" in daily_report

        finally:
            observer.shutdown(timeout=2.0)

    def test_observability_data_collection_from_snapshots(self):
        """Тест сбора данных из snapshot файлов"""
        # Создаем временную директорию
        snapshots_dir = Path(self.create_temp_dir())

        # Создаем тестовые snapshot файлы
        snapshots_data = []
        for i in range(3):
            snapshot_path = snapshots_dir / f"snapshot_{i}.json"
            data = {
                "timestamp": time.time() + i * 10,
                "energy": 0.8 - i * 0.1,
                "stability": 0.9 - i * 0.05,
                "memory_size": 100 + i * 50,
                "error_count": i,
                "action_count": 10 + i * 5,
                "event_count": 20 + i * 10,
                "state_change_count": 5 + i
            }
            snapshots_data.append(data)

            with open(snapshot_path, 'w') as f:
                import json
                json.dump(data, f)

        # Создаем коллектор
        collector = RawDataCollector(snapshots_directory=snapshots_dir)

        # Собираем данные
        snapshot_paths = list(snapshots_dir.glob("*.json"))
        report = collector.collect_raw_counters_from_snapshots(snapshot_paths)

        # Проверяем результаты
        assert report is not None
        assert report.raw_counters.cycle_count == 3  # Три snapshot
        assert report.raw_counters.memory_entries_count == 100 + 150 + 200  # Сумма memory_size
        assert report.raw_counters.error_count == 0 + 1 + 2  # Сумма error_count
        assert report.raw_counters.action_count == 10 + 15 + 20  # Сумма action_count

    def test_developer_reports_generation(self):
        """Тест генерации отчетов для разработчиков"""
        # Создаем временную директорию с данными
        data_dir = self.create_temp_dir()

        # Создаем файл с пассивными наблюдениями
        obs_file = Path(data_dir) / "passive_observations.jsonl"
        observations = []

        base_time = time.time()
        for i in range(10):
            obs = {
                "timestamp": base_time + i * 60,  # Каждую минуту
                "observation_type": "passive_snapshot",
                "system_state": {
                    "energy": 0.8 - i * 0.02,
                    "stability": 0.85 + i * 0.005,
                    "integrity": 0.9,
                    "fatigue": 0.1 + i * 0.01,
                    "tension": 0.15,
                    "age": 1000 + i * 10,
                    "ticks": 500 + i * 5
                },
                "memory": {
                    "episodic_size": 100 + i * 10,
                    "archive_size": 200 + i * 20,
                    "recent_events": 20 + i * 2
                },
                "processing": {
                    "learning_params": 4,
                    "adaptation_params": 4,
                    "decision_queue": 3 + i,
                    "action_queue": 1 + i
                }
            }
            observations.append(obs)

        with open(obs_file, 'w') as f:
            import json
            for obs in observations:
                f.write(json.dumps(obs) + '\n')

        # Создаем генератор отчетов
        reports = DeveloperReports(data_directory=data_dir)

        # Генерируем отчеты
        daily_report = reports.generate_automated_report("daily", hours=1)
        health_report = reports.generate_system_health_check()
        text_report = reports.generate_text_report(hours=1)

        # Проверяем структуру отчетов
        assert daily_report is not None
        assert "health" in daily_report
        assert "metrics" in daily_report
        assert "insights" in daily_report

        assert health_report is not None
        assert "snapshot_found" in health_report

        assert text_report is not None
        assert "SYSTEM OBSERVABILITY REPORT" in text_report
        assert "HEALTH ASSESSMENT" in text_report

    def test_observability_error_handling(self):
        """Тест обработки ошибок в observability"""
        # Создаем временную директорию
        data_dir = self.create_temp_dir()

        # Создаем RawDataCollector без директорий
        collector = RawDataCollector()

        # Проверяем, что ошибки обрабатываются корректно
        report = collector.collect_raw_counters_from_logs(
            start_time=time.time() - 3600,
            end_time=time.time()
        )

        # Должен вернуться отчет с значениями по умолчанию
        assert report is not None
        assert report.raw_counters.cycle_count == 0
        assert report.raw_counters.error_count == 0

    def test_async_passive_observer_lifecycle(self):
        """Тест жизненного цикла AsyncPassiveObserver"""
        # Создаем временную директорию
        data_dir = self.create_temp_dir()
        snapshots_dir = Path(data_dir) / "snapshots"
        snapshots_dir.mkdir()

        # Создаем snapshot
        snapshot_path = snapshots_dir / "test.json"
        with open(snapshot_path, 'w') as f:
            import json
            json.dump({"timestamp": time.time(), "energy": 0.8}, f)

        # Создаем observer
        observer = AsyncPassiveObserver(
            collection_interval=0.5,
            snapshots_dir=str(snapshots_dir),
            enabled=False  # Начинаем disabled
        )

        # Проверяем статус
        status = observer.get_status()
        assert status["enabled"] is False
        assert status["thread_alive"] is False

        # Включаем
        observer.enable()
        time.sleep(0.1)  # Даем время на запуск

        status = observer.get_status()
        assert status["enabled"] is True
        assert status["thread_alive"] is True

        # Даем время на сбор данных
        time.sleep(1.0)

        # Отключаем
        observer.disable()
        observer.shutdown(timeout=1.0)

        status = observer.get_status()
        assert status["enabled"] is False
        assert status["thread_alive"] is False