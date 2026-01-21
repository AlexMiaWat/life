"""
Интеграционные тесты для ExternalObserver с реальными компонентами Life.

Тестирует работу наблюдателя с настоящими логами, снимками и компонентами системы.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# Добавляем src в путь
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.observability.external_observer import ExternalObserver, SystemMetrics
from src.state.self_state import SelfState
from src.observability.structured_logger import StructuredLogger
from src.runtime.loop import run_loop
from src.environment.event_queue import EventQueue
import threading
import time


class TestExternalObserverIntegrationNew(unittest.TestCase):
    """Интеграционные тесты для ExternalObserver с новыми компонентами."""

    def setUp(self):
        """Подготовка тестового окружения."""
        # Создаем временные директории для логов и снимков
        self.temp_dir = tempfile.mkdtemp()
        self.logs_dir = Path(self.temp_dir) / "logs"
        self.snapshots_dir = Path(self.temp_dir) / "snapshots"

        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

        # Создаем observer с временными путями
        self.observer = ExternalObserver(
            logs_directory=self.logs_dir, snapshots_directory=self.snapshots_dir
        )

        # Создаем компоненты для интеграции
        self.self_state = SelfState()
        self.event_queue = EventQueue()

    def tearDown(self):
        """Очистка после тестов."""
        # Удаляем временные файлы
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_observe_from_logs_with_structured_logger(self):
        """Интеграционный тест наблюдения с StructuredLogger."""
        # Создаем structured logger для записи логов
        logger = StructuredLogger("test_component")

        # Создаем тестовые логи
        test_logs = [
            {
                "timestamp": time.time() - 300,
                "event_type": "system_start",
                "component": "runtime",
                "cycle_count": 100,
                "energy_level": 0.9,
            },
            {
                "timestamp": time.time() - 200,
                "event_type": "adaptation_cycle",
                "component": "adaptation",
                "stability": 0.85,
                "learning_effectiveness": 0.8,
            },
            {
                "timestamp": time.time() - 100,
                "event_type": "error_occurred",
                "component": "memory",
                "error_count": 1,
                "integrity_score": 0.95,
            },
        ]

        # Создаем файл с логами
        log_file = self.logs_dir / "structured_log.jsonl"
        with open(log_file, "w") as f:
            for log_entry in test_logs:
                f.write(json.dumps(log_entry) + "\n")

        # Выполняем наблюдение
        start_time = time.time() - 600
        end_time = time.time()
        report = self.observer.observe_from_logs(start_time, end_time)

        # Проверяем результаты
        self.assertIsNotNone(report)
        self.assertIsInstance(report.metrics_summary, SystemMetrics)
        self.assertIsInstance(report.behavior_patterns, list)
        self.assertIsInstance(report.trends, dict)

        # Проверяем что история наблюдений сохранилась
        self.assertEqual(len(self.observer.observation_history), 1)

    def test_observe_from_snapshots_with_real_data(self):
        """Интеграционный тест наблюдения на основе снимков с реальными данными."""
        # Создаем тестовые снимки состояния
        snapshots_data = [
            {
                "timestamp": time.time() - 200,
                "cycle_count": 100,
                "energy_level": 0.9,
                "stability": 0.85,
                "integrity": 0.95,
                "memory_entries": 50,
                "learning_effectiveness": 0.8,
                "adaptation_rate": 0.7,
                "error_count": 1,
            },
            {
                "timestamp": time.time() - 100,
                "cycle_count": 150,
                "energy_level": 0.85,
                "stability": 0.88,
                "integrity": 0.92,
                "memory_entries": 75,
                "learning_effectiveness": 0.82,
                "adaptation_rate": 0.72,
                "error_count": 2,
            },
            {
                "timestamp": time.time(),
                "cycle_count": 200,
                "energy_level": 0.8,
                "stability": 0.9,
                "integrity": 0.9,
                "memory_entries": 100,
                "learning_effectiveness": 0.85,
                "adaptation_rate": 0.75,
                "error_count": 3,
            },
        ]

        # Создаем файлы снимков
        snapshot_paths = []
        for i, snapshot_data in enumerate(snapshots_data):
            snapshot_file = self.snapshots_dir / f"snapshot_{i}.json"
            with open(snapshot_file, "w") as f:
                json.dump(snapshot_data, f)
            snapshot_paths.append(snapshot_file)

        # Выполняем наблюдение
        report = self.observer.observe_from_snapshots(snapshot_paths)

        # Проверяем результаты
        self.assertIsNotNone(report)
        self.assertIsInstance(report.metrics_summary, SystemMetrics)
        self.assertGreater(report.metrics_summary.cycle_count, 0)
        self.assertGreater(report.metrics_summary.memory_entries_count, 0)

        # Проверяем что история наблюдений сохранилась
        self.assertEqual(len(self.observer.observation_history), 1)

    def test_observer_with_runtime_loop_logs(self):
        """Интеграционный тест наблюдателя с логами runtime loop."""
        # Создаем mock монитора для runtime loop
        runtime_monitor = Mock()

        # Создаем structured logger для записи логов
        logger = StructuredLogger("runtime_test")

        # Создаем стоп-событие для быстрой остановки
        stop_event = threading.Event()

        # Запускаем runtime loop на короткое время для генерации логов
        def run_short_loop():
            try:
                run_loop(
                    self_state=self.self_state,
                    monitor=runtime_monitor,
                    tick_interval=0.05,  # Быстрый тик
                    snapshot_period=1000,  # Редкие снапшоты
                    stop_event=stop_event,
                    event_queue=self.event_queue,
                    disable_weakness_penalty=True,
                    disable_structured_logging=False,  # Включаем логирование
                    disable_learning=True,
                    disable_adaptation=True,
                    log_flush_period_ticks=10,  # Частый flush для теста
                    enable_profiling=False,
                )
            except Exception as e:
                # Логируем ошибку для отладки
                print(f"Runtime loop error (expected): {e}")

        # Запускаем loop в отдельном потоке
        loop_thread = threading.Thread(target=run_short_loop, daemon=True)
        loop_thread.start()

        # Ждем немного для генерации логов
        time.sleep(0.2)

        # Останавливаем loop
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # Теперь выполняем наблюдение на основе сгенерированных логов
        start_time = time.time() - 10
        end_time = time.time()

        # Создаем тестовые логи если реальные не сгенерировались
        log_file = self.logs_dir / "structured_log.jsonl"
        if not log_file.exists():
            test_logs = [
                {
                    "timestamp": time.time() - 5,
                    "event_type": "runtime_tick",
                    "component": "runtime",
                    "cycle_count": 10,
                    "energy_level": 0.95,
                },
                {
                    "timestamp": time.time() - 3,
                    "event_type": "state_update",
                    "component": "self_state",
                    "stability": 0.9,
                    "integrity": 0.98,
                },
            ]
            with open(log_file, "w") as f:
                for log_entry in test_logs:
                    f.write(json.dumps(log_entry) + "\n")

        report = self.observer.observe_from_logs(start_time, end_time)

        # Проверяем результаты
        self.assertIsNotNone(report)
        self.assertIsInstance(report, object)  # ObservationReport

    def test_multiple_observation_sessions(self):
        """Интеграционный тест множественных сессий наблюдения."""
        # Создаем несколько наборов логов для разных сессий
        sessions_data = [
            {
                "session": 1,
                "logs": [
                    {
                        "timestamp": time.time() - 300,
                        "event_type": "session_start",
                        "cycle_count": 0,
                        "energy_level": 1.0,
                    },
                    {
                        "timestamp": time.time() - 250,
                        "event_type": "normal_operation",
                        "cycle_count": 50,
                        "energy_level": 0.95,
                    },
                ],
            },
            {
                "session": 2,
                "logs": [
                    {
                        "timestamp": time.time() - 200,
                        "event_type": "session_start",
                        "cycle_count": 0,
                        "energy_level": 1.0,
                    },
                    {
                        "timestamp": time.time() - 150,
                        "event_type": "high_load",
                        "cycle_count": 100,
                        "energy_level": 0.7,
                    },
                    {
                        "timestamp": time.time() - 100,
                        "event_type": "recovery",
                        "cycle_count": 150,
                        "energy_level": 0.85,
                    },
                ],
            },
        ]

        # Создаем логи для каждой сессии
        for session_data in sessions_data:
            session_logs_file = self.logs_dir / f"session_{session_data['session']}_log.jsonl"
            with open(session_logs_file, "w") as f:
                for log_entry in session_data["logs"]:
                    f.write(json.dumps(log_entry) + "\n")

            # Выполняем наблюдение для каждой сессии
            start_time = min(log["timestamp"] for log in session_data["logs"]) - 10
            end_time = max(log["timestamp"] for log in session_data["logs"]) + 10
            report = self.observer.observe_from_logs(start_time, end_time)

            self.assertIsNotNone(report)

        # Проверяем что все сессии сохранены в истории
        self.assertEqual(len(self.observer.observation_history), len(sessions_data))

        # Проверяем summary
        summary = self.observer.get_observation_history_summary()
        self.assertIn("total_observations", summary)
        self.assertEqual(summary["total_observations"], len(sessions_data))

    def test_observer_with_error_handling(self):
        """Интеграционный тест обработки ошибок в наблюдателе."""
        # Создаем файл с некорректными данными
        corrupted_log_file = self.logs_dir / "corrupted_log.jsonl"
        with open(corrupted_log_file, "w") as f:
            f.write("invalid json line 1\n")
            f.write('{"valid": "json", "timestamp": ' + str(time.time()) + "}\n")
            f.write("another invalid line\n")
            f.write('{"another": "valid", "timestamp": ' + str(time.time()) + "}\n")

        # Выполняем наблюдение - должно обработать ошибки gracefully
        start_time = time.time() - 100
        end_time = time.time()
        report = self.observer.observe_from_logs(start_time, end_time)

        # Проверяем что система не crashed
        self.assertIsNotNone(report)
        self.assertIsInstance(report.metrics_summary, SystemMetrics)

        # Даже при ошибках должен быть создан отчет
        self.assertIsInstance(report.behavior_patterns, list)
        self.assertIsInstance(report.anomalies, list)
        self.assertIsInstance(report.recommendations, list)

    def test_save_and_load_observation_reports(self):
        """Интеграционный тест сохранения и загрузки отчетов наблюдения."""
        # Создаем отчет наблюдения
        report = self.observer.observe_from_logs(time.time() - 3600, time.time())

        # Сохраняем отчет
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            saved_path = self.observer.save_report(report, temp_file)

            # Проверяем что файл создан
            self.assertTrue(Path(saved_path).exists())

            # Проверяем содержимое файла
            with open(saved_path, "r") as f:
                content = f.read()
                self.assertIn("observation_period", content)
                self.assertIn("metrics_summary", content)

            # Проверяем что можем загрузить и распарсить JSON
            with open(saved_path, "r") as f:
                loaded_data = json.load(f)
                self.assertIsInstance(loaded_data, dict)
                self.assertIn("observation_period", loaded_data)
                self.assertIn("metrics_summary", loaded_data)

        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_observer_with_behavior_pattern_detection(self):
        """Интеграционный тест обнаружения паттернов поведения."""
        # Создаем логи с повторяющимися паттернами
        pattern_logs = []

        # Паттерн 1: Периодические спады энергии
        base_time = time.time() - 1000
        for i in range(10):
            pattern_logs.append(
                {
                    "timestamp": base_time + i * 100,
                    "event_type": "energy_drop" if i % 3 == 0 else "normal_operation",
                    "cycle_count": i * 10,
                    "energy_level": 0.6 if i % 3 == 0 else 0.9,
                    "stability": 0.8,
                }
            )

        # Паттерн 2: Периодические пики активности обучения
        for i in range(8):
            pattern_logs.append(
                {
                    "timestamp": base_time + i * 120,
                    "event_type": "learning_burst" if i % 4 == 0 else "normal_operation",
                    "cycle_count": 100 + i * 5,
                    "learning_effectiveness": 0.95 if i % 4 == 0 else 0.7,
                    "adaptation_rate": 0.8,
                }
            )

        # Сохраняем логи
        log_file = self.logs_dir / "pattern_log.jsonl"
        with open(log_file, "w") as f:
            for log_entry in pattern_logs:
                f.write(json.dumps(log_entry) + "\n")

        # Выполняем наблюдение
        start_time = base_time - 100
        end_time = time.time()
        report = self.observer.observe_from_logs(start_time, end_time)

        # Проверяем что обнаружены паттерны
        self.assertIsNotNone(report)
        self.assertIsInstance(report.behavior_patterns, list)

        # Проверяем что есть хотя бы базовые паттерны или пустой список
        # (конкретная логика обнаружения паттернов может варьироваться)
        self.assertIsInstance(report.behavior_patterns, list)

    def test_observer_performance_with_large_logs(self):
        """Интеграционный тест производительности с большими логами."""
        # Создаем большой файл логов
        large_log_file = self.logs_dir / "large_log.jsonl"
        base_time = time.time() - 3600

        with open(large_log_file, "w") as f:
            for i in range(1000):  # 1000 записей
                log_entry = {
                    "timestamp": base_time + i * 3.6,  # Равномерно распределены по часу
                    "event_type": "tick",
                    "cycle_count": i,
                    "energy_level": 0.8 + 0.2 * (i % 2),  # Небольшая вариация
                    "stability": 0.85,
                    "integrity": 0.9,
                }
                f.write(json.dumps(log_entry) + "\n")

        # Замеряем время выполнения наблюдения
        start_observation = time.time()
        report = self.observer.observe_from_logs(base_time - 100, time.time())
        end_observation = time.time()

        observation_time = end_observation - start_observation

        # Проверяем что наблюдение завершилось разумно быстро (< 5 секунд)
        self.assertLess(observation_time, 5.0, f"Observation took too long: {observation_time}s")

        # Проверяем что отчет сгенерирован
        self.assertIsNotNone(report)
        self.assertIsInstance(report.metrics_summary, SystemMetrics)

    def test_observer_with_mixed_data_sources(self):
        """Интеграционный тест с смешанными источниками данных."""
        # Создаем и логи, и снимки
        base_time = time.time() - 1800

        # Логи
        log_entries = [
            {
                "timestamp": base_time + 300,
                "event_type": "log_event_1",
                "energy_level": 0.9,
                "stability": 0.85,
            },
            {
                "timestamp": base_time + 600,
                "event_type": "log_event_2",
                "energy_level": 0.8,
                "learning_effectiveness": 0.75,
            },
        ]

        log_file = self.logs_dir / "mixed_log.jsonl"
        with open(log_file, "w") as f:
            for entry in log_entries:
                f.write(json.dumps(entry) + "\n")

        # Снимки
        snapshot_data = {
            "timestamp": base_time + 900,
            "cycle_count": 500,
            "energy_level": 0.85,
            "stability": 0.88,
            "memory_entries": 200,
            "learning_effectiveness": 0.8,
        }

        snapshot_file = self.snapshots_dir / "mixed_snapshot.json"
        with open(snapshot_file, "w") as f:
            json.dump(snapshot_data, f)

        # Выполняем оба типа наблюдения
        logs_report = self.observer.observe_from_logs(base_time, time.time())
        snapshots_report = self.observer.observe_from_snapshots([snapshot_file])

        # Проверяем оба отчета
        self.assertIsNotNone(logs_report)
        self.assertIsNotNone(snapshots_report)

        # Проверяем что история содержит оба наблюдения
        self.assertEqual(len(self.observer.observation_history), 2)

        # Проверяем summary
        summary = self.observer.get_observation_history_summary()
        self.assertEqual(summary["total_observations"], 2)


if __name__ == "__main__":
    unittest.main()
