"""
Интеграционные тесты для новой функциональности наблюдения системы Life.

Тестируют взаимодействие компонентов:
- AsyncPassiveObserver с ComponentMonitor и StateTracker
- StructuredLogger с компонентами системы
- RawDataCollector с реальными snapshot файлами
- Полный цикл наблюдения: сбор данных → обработка → логирование → отчеты
"""

import json
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from src.observability.external_observer import RawDataCollector
from src.observability.component_monitor import ComponentMonitor
from src.observability.structured_logger import StructuredLogger
from src.observability.async_passive_observer import AsyncPassiveObserver
from src.observability.reporting import ReportGenerator, export_observation_report_json


class TestRawDataCollectorIntegration:
    """Интеграционные тесты для RawDataCollector."""

    def test_collect_from_real_snapshot_files(self):
        """Тест сбора данных из реальных файлов снимков."""
        collector = RawDataCollector()

        # Создаем временные файлы снимков
        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_dir = Path(temp_dir) / "snapshots"
            snapshot_dir.mkdir()

            # Создаем тестовые snapshot файлы
            snapshots_data = [
                {
                    "timestamp": 1000.0,
                    "memory_size": 50,
                    "error_count": 1,
                    "action_count": 5,
                    "event_count": 3,
                    "state_change_count": 2,
                },
                {
                    "timestamp": 1500.0,
                    "memory_size": 75,
                    "error_count": 0,
                    "action_count": 8,
                    "event_count": 5,
                    "state_change_count": 3,
                },
                {
                    "timestamp": 2000.0,
                    "memory_size": 60,
                    "error_count": 2,
                    "action_count": 6,
                    "event_count": 4,
                    "state_change_count": 1,
                },
            ]

            snapshot_paths = []
            for i, data in enumerate(snapshots_data):
                snapshot_file = snapshot_dir / f"snapshot_{i:06d}.json"
                with open(snapshot_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f)
                snapshot_paths.append(snapshot_file)

            # Меняем директорию snapshots в collector
            collector.snapshots_directory = snapshot_dir

            # Собираем данные
            report = collector.collect_raw_counters_from_snapshots(snapshot_paths)

            # Проверяем результаты
            assert report.observation_period == (1000.0, 2000.0)
            assert report.raw_counters.cycle_count == 3  # количество файлов
            assert report.raw_counters.uptime_seconds == 1000.0  # 2000 - 1000
            assert report.raw_counters.memory_entries_count == 185  # 50 + 75 + 60
            assert report.raw_counters.error_count == 3  # 1 + 0 + 2
            assert report.raw_counters.action_count == 19  # 5 + 8 + 6
            assert report.raw_counters.event_count == 12  # 3 + 5 + 4
            assert report.raw_counters.state_change_count == 6  # 2 + 3 + 1

    def test_full_data_collection_workflow(self):
        """Тест полного цикла сбора данных: логи → снимки → отчет."""
        collector = RawDataCollector()

        # 1. Создаем mock данные логов
        with patch.object(collector, '_read_logs_safely') as mock_read_logs:
            mock_read_logs.return_value = {
                "cycle_count": 500,
                "memory_count": 250,
                "error_count": 5,
                "action_count": 100,
                "event_count": 75,
                "state_change_count": 25,
            }

            # Собираем из логов
            logs_report = collector.collect_raw_counters_from_logs(1000.0, 2000.0)

            assert logs_report.raw_counters.cycle_count == 500
            assert logs_report.observation_period == (1000.0, 2000.0)

        # 2. Создаем снимки и собираем из них
        snapshots = [
            {"timestamp": 1000.0, "memory_size": 100, "error_count": 2},
            {"timestamp": 2000.0, "memory_size": 150, "error_count": 3},
        ]
        snapshots_report = collector.collect_raw_counters_from_snapshots(snapshots)

        assert snapshots_report.raw_counters.memory_entries_count == 250
        assert snapshots_report.raw_counters.error_count == 5

        # 3. Сохраняем оба отчета
        with tempfile.TemporaryDirectory() as temp_dir:
            logs_path = Path(temp_dir) / "logs_report.json"
            snapshots_path = Path(temp_dir) / "snapshots_report.json"

            collector.save_raw_data_report(logs_report, logs_path)
            collector.save_raw_data_report(snapshots_report, snapshots_path)

            assert logs_path.exists()
            assert snapshots_path.exists()

            # Проверяем содержимое
            with open(logs_path, 'r', encoding='utf-8') as f:
                logs_data = json.load(f)
                assert logs_data["raw_counters"]["cycle_count"] == 500

            with open(snapshots_path, 'r', encoding='utf-8') as f:
                snapshots_data = json.load(f)
                assert snapshots_data["raw_counters"]["memory_entries_count"] == 250

        # 4. Проверяем историю отчетов
        assert len(collector.raw_data_history) == 2
        assert collector.raw_data_history[0] == logs_report
        assert collector.raw_data_history[1] == snapshots_report


class TestComponentMonitorIntegration:
    """Интеграционные тесты для ComponentMonitor."""

    def test_monitor_real_self_state(self):
        """Тест мониторинга реального SelfState объекта."""
        monitor = ComponentMonitor()

        # Создаем mock SelfState с реалистичными данными
        mock_self_state = Mock()

        # Memory компонент
        mock_memory = Mock()
        mock_memory.episodic_memory = [Mock(), Mock(), Mock(), Mock(), Mock()]  # 5 записей
        mock_memory.archive_memory = Mock()
        mock_memory.archive_memory.episodic_memory = [Mock(), Mock()]  # 2 записи в архиве
        mock_memory.recent_events = [Mock(), Mock(), Mock()]  # 3 недавних события
        mock_self_state.memory = mock_memory

        # Learning компонент
        mock_learning = Mock()
        mock_learning.params = {"learning_rate": 0.01, "momentum": 0.9, "threshold": 0.5}
        mock_learning.operation_count = 42
        mock_self_state.learning_engine = mock_learning

        # Adaptation компонент
        mock_adaptation = Mock()
        mock_adaptation.params = {"adaptation_rate": 0.05, "reset_threshold": 0.1}
        mock_adaptation.operation_count = 15
        mock_self_state.adaptation_manager = mock_adaptation

        # Decision компонент
        mock_decision = Mock()
        mock_decision.decision_queue = [Mock(), Mock(), Mock(), Mock()]  # 4 решения в очереди
        mock_decision.operation_count = 28
        mock_self_state.decision_engine = mock_decision

        # Action компонент
        mock_action = Mock()
        mock_action.action_queue = [Mock(), Mock()]  # 2 действия в очереди
        mock_action.operation_count = 12
        mock_self_state.action_executor = mock_action

        # Environment компонент
        mock_env = Mock()
        mock_env.event_queue = Mock()
        mock_env.event_queue.qsize = Mock(return_value=7)  # 7 событий в очереди
        mock_env.event_queue.queue = [Mock()] * 7  # 7 событий
        mock_self_state.environment = mock_env

        # Intelligence компонент
        mock_self_state.intelligence = {
            "processed_sources": {
                "source1": {"status": "ok"},
                "source2": {"status": "error"},
                "source3": {"status": "ok"},
            }
        }

        # Собираем статистику
        stats = monitor.collect_component_stats(mock_self_state)

        # Проверяем результаты
        assert stats.memory_episodic_size == 5
        assert stats.memory_archive_size == 2
        assert stats.memory_recent_events == 3

        assert stats.learning_params_count == 3
        assert stats.learning_operations == 42

        assert stats.adaptation_params_count == 2
        assert stats.adaptation_operations == 15

        assert stats.decision_queue_size == 4
        assert stats.decision_operations == 28

        assert stats.action_queue_size == 2
        assert stats.action_operations == 12

        assert stats.environment_event_queue_size == 7
        assert stats.environment_pending_events == 7

        assert stats.intelligence_processed_sources == 3

    def test_monitor_error_handling(self):
        """Тест обработки ошибок при мониторинге проблемных компонентов."""
        monitor = ComponentMonitor()

        mock_self_state = Mock()

        # Создаем компоненты, которые вызывают исключения
        mock_memory = Mock()
        mock_memory.episodic_memory = Mock()
        mock_memory.episodic_memory.__len__ = Mock(side_effect=AttributeError("No len"))
        mock_self_state.memory = mock_memory

        mock_learning = Mock()
        mock_learning.params = Mock()
        mock_learning.params.__len__ = Mock(side_effect=TypeError("Not iterable"))
        mock_self_state.learning_engine = mock_learning

        # Остальные компоненты нормальные
        mock_self_state.adaptation_manager = None
        mock_self_state.decision_engine = None
        mock_self_state.action_executor = None
        mock_self_state.environment = None
        mock_self_state.intelligence = {}

        # Несмотря на ошибки, мониторинг должен продолжаться
        stats = monitor.collect_component_stats(mock_self_state)

        # Проблемные компоненты должны иметь значения по умолчанию
        assert stats.memory_episodic_size == 0  # Ошибка в episodic_memory
        assert stats.learning_params_count == 0  # Ошибка в params

        # Корректные компоненты должны работать нормально
        assert stats.decision_queue_size == 0  # None компонент

    def test_monitor_state_persistence(self):
        """Тест сохранения состояния мониторинга между вызовами."""
        monitor = ComponentMonitor()

        # Первый сбор данных
        mock_state1 = Mock()
        mock_state1.memory = Mock()
        mock_state1.memory.episodic_memory = [1, 2]
        mock_state1.learning_engine = None

        stats1 = monitor.collect_component_stats(mock_state1)
        assert stats1.memory_episodic_size == 2

        # Проверяем, что состояние сохранилось
        last_stats = monitor.get_last_system_stats()
        assert last_stats == stats1
        assert last_stats.memory_episodic_size == 2

        # Второй сбор данных
        mock_state2 = Mock()
        mock_state2.memory = Mock()
        mock_state2.memory.episodic_memory = [1, 2, 3, 4, 5]  # Изменилось
        mock_state2.learning_engine = None

        stats2 = monitor.collect_component_stats(mock_state2)
        assert stats2.memory_episodic_size == 5

        # Проверяем, что предыдущее состояние перезаписалось
        last_stats = monitor.get_last_system_stats()
        assert last_stats == stats2
        assert last_stats.memory_episodic_size == 5


class TestStructuredLoggerIntegration:
    """Интеграционные тесты для StructuredLogger."""

    def test_full_event_processing_chain(self):
        """Тест полного цикла обработки события: event → meaning → decision → action → feedback."""
        logger = StructuredLogger()

        correlation_id = None
        log_entries = []

        # Mock функцию записи для перехвата записей
        original_write = logger._write_log_entry
        def mock_write(entry):
            log_entries.append(entry)
            return original_write(entry)
        logger._write_log_entry = mock_write

        try:
            # 1. Логируем событие
            mock_event = Mock()
            mock_event.id = "event_001"
            mock_event.type = "stimulus"
            mock_event.intensity = 0.8
            mock_event.data = {"source": "environment", "value": 0.8}

            correlation_id = logger.log_event(mock_event)
            assert correlation_id.startswith("chain_")

            # 2. Логируем meaning
            mock_meaning = Mock()
            mock_meaning.significance = 0.7
            mock_meaning.impact = {"energy": -0.1, "stability": 0.05}

            logger.log_meaning(mock_event, mock_meaning, correlation_id)

            # 3. Логируем decision
            logger.log_decision("absorb", correlation_id, {"reason": "significant_impact"})

            # 4. Логируем action
            state_before = {"energy": 0.9, "stability": 0.8}
            logger.log_action("action_001", "adjust_energy", correlation_id, state_before)

            # 5. Логируем feedback
            mock_feedback = Mock()
            mock_feedback.action_id = "action_001"
            mock_feedback.delay_ticks = 3
            mock_feedback.state_delta = {"energy": 0.05, "stability": -0.02}
            mock_feedback.associated_events = ["event_001"]

            logger.log_feedback(mock_feedback, correlation_id)

            # Проверяем, что все этапы залогированы
            assert len(log_entries) == 5

            stages = [entry["stage"] for entry in log_entries]
            assert stages == ["event", "meaning", "decision", "action", "feedback"]

            # Проверяем, что correlation_id сохраняется во всех записях
            for entry in log_entries:
                assert entry["correlation_id"] == correlation_id

            # Проверяем конкретные данные
            event_entry = log_entries[0]
            assert event_entry["event_id"] == "event_001"
            assert event_entry["event_type"] == "stimulus"
            assert event_entry["intensity"] == 0.8

            meaning_entry = log_entries[1]
            assert meaning_entry["significance"] == 0.7
            assert meaning_entry["impact"] == {"energy": -0.1, "stability": 0.05}

            decision_entry = log_entries[2]
            assert decision_entry["pattern"] == "absorb"
            assert decision_entry["data"]["reason"] == "significant_impact"

            action_entry = log_entries[3]
            assert action_entry["action_id"] == "action_001"
            assert action_entry["pattern"] == "adjust_energy"
            assert action_entry["data"]["state_before"] == state_before

            feedback_entry = log_entries[4]
            assert feedback_entry["action_id"] == "action_001"
            assert feedback_entry["delay_ticks"] == 3
            assert feedback_entry["data"]["state_delta"] == {"energy": 0.05, "stability": -0.02}

        finally:
            logger._write_log_entry = original_write

    def test_tick_logging_workflow(self):
        """Тест логирования тиков и операций."""
        logger = StructuredLogger()

        log_entries = []

        # Mock функцию записи
        original_write = logger._write_log_entry
        def mock_write(entry):
            log_entries.append(entry)
            return original_write(entry)
        logger._write_log_entry = mock_write

        try:
            # Логируем начало тика
            logger.log_tick_start(42, 5)

            # Имитируем некоторые операции в тике
            logger.log_event(Mock())
            logger.log_decision("ignore", logger._get_next_correlation_id())

            # Логируем конец тика
            logger.log_tick_end(42, 125.5, 3)

            # Проверяем записи
            assert len(log_entries) == 4  # tick_start, event, decision, tick_end

            tick_start = log_entries[0]
            assert tick_start["stage"] == "tick_start"
            assert tick_start["tick_number"] == 42
            assert tick_start["queue_size"] == 5

            tick_end = log_entries[-1]
            assert tick_end["stage"] == "tick_end"
            assert tick_end["tick_number"] == 42
            assert tick_end["duration_ms"] == 125.5
            assert tick_end["events_processed"] == 3

        finally:
            logger._write_log_entry = original_write

    def test_error_logging_integration(self):
        """Тест логирования ошибок в разных стадиях."""
        logger = StructuredLogger()

        log_entries = []

        # Mock функцию записи
        original_write = logger._write_log_entry
        def mock_write(entry):
            log_entries.append(entry)
            return original_write(entry)
        logger._write_log_entry = original_write

        try:
            # Генерируем correlation_id
            correlation_id = logger._get_next_correlation_id()

            # Логируем ошибки в разных стадиях
            logger.log_error("event", ValueError("Event processing failed"), correlation_id)
            logger.log_error("meaning", RuntimeError("Meaning calculation error"), correlation_id)
            logger.log_error("decision", TypeError("Decision pattern invalid"))

            # Проверяем записи об ошибках
            assert len(log_entries) == 3

            for i, entry in enumerate(log_entries):
                assert entry["stage"] == f"error_{['event', 'meaning', 'decision'][i]}"
                assert entry["correlation_id"] in [correlation_id, "system_error"]
                assert "error_type" in entry
                assert "error_message" in entry

        finally:
            logger._write_log_entry = original_write


class TestAsyncPassiveObserverIntegration:
    """Интеграционные тесты для AsyncPassiveObserver."""

    @patch('src.observability.async_passive_observer.AsyncPassiveObserver._start_observer_thread')
    def test_observer_with_mock_snapshot_loading(self, mock_start_thread):
        """Тест наблюдателя с mock загрузкой снимков."""
        observer = AsyncPassiveObserver(collection_interval=1.0, enabled=True)

        # Mock загрузку snapshot
        with patch.object(observer, '_load_latest_snapshot') as mock_load:
            mock_load.return_value = {
                "timestamp": 1000.0,
                "memory": {"episodic_memory": [1, 2, 3]},
                "learning_engine": {"params": {"lr": 0.01}},
            }

            # Имитируем сбор данных
            observer._collect_data_point()

            # Проверяем, что компоненты получили данные
            # (AsyncDataSink должен получить данные от StateTracker и ComponentMonitor)

        observer.shutdown()

    @patch('src.observability.async_passive_observer.AsyncPassiveObserver._start_observer_thread')
    def test_observer_error_handling(self, mock_start_thread):
        """Тест обработки ошибок в наблюдателе."""
        observer = AsyncPassiveObserver(enabled=True)

        # Mock загрузку snapshot с ошибкой
        with patch.object(observer, '_load_latest_snapshot') as mock_load:
            mock_load.side_effect = Exception("Snapshot loading failed")

            # Сбор данных не должен падать с исключением
            try:
                observer._collect_data_point()
                # Если дошли сюда, значит исключение обработано
            except Exception:
                pytest.fail("Observer should handle exceptions gracefully")

        observer.shutdown()

    @patch('threading.Thread')
    @patch('src.observability.async_passive_observer.AsyncPassiveObserver._start_observer_thread')
    def test_observer_lifecycle(self, mock_start_thread, mock_thread):
        """Тест жизненного цикла наблюдателя."""
        # Mock thread для контроля
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        mock_thread_instance.is_alive.return_value = True

        observer = AsyncPassiveObserver(enabled=False)

        # Наблюдатель отключен
        assert observer.enabled is False

        # Включаем
        observer.enable()
        assert observer.enabled is True
        mock_start_thread.assert_called_once()

        # Отключаем
        observer.disable()
        assert observer.enabled is False

        # Завершаем
        observer.shutdown()
        mock_thread_instance.join.assert_called_once()


class TestFullObservabilityWorkflow:
    """Интеграционные тесты для полного цикла наблюдения."""

    def test_end_to_end_observability_workflow(self):
        """Тест полного цикла: сбор данных → логирование → отчеты."""
        # Создаем все компоненты
        collector = RawDataCollector()
        monitor = ComponentMonitor()
        logger = StructuredLogger()
        generator = ReportGenerator()

        # 1. Собираем данные из снимков
        snapshots = [
            {
                "timestamp": 1000.0,
                "memory_size": 100,
                "error_count": 2,
                "action_count": 10,
                "event_count": 8,
                "state_change_count": 3,
            }
        ]

        raw_report = collector.collect_raw_counters_from_snapshots(snapshots)

        # 2. Логируем операции
        correlation_id = logger.log_event(Mock())
        logger.log_decision("absorb", correlation_id)

        # 3. Генерируем отчет
        with patch('src.observability.reporting.export_observation_report_json') as mock_export:
            mock_export.return_value = "/test/report.json"

            json_path = generator.generate_json_report(raw_report)

            assert json_path == "/test/report.json"
            mock_export.assert_called_once()

    def test_component_interaction_robustness(self):
        """Тест надежности взаимодействия компонентов при ошибках."""
        collector = RawDataCollector()
        monitor = ComponentMonitor()

        # Тест с несуществующими путями
        collector.logs_directory = Path("/nonexistent/logs")
        collector.snapshots_directory = Path("/nonexistent/snapshots")

        # Сбор из логов не должен падать
        with patch.object(collector, '_read_logs_safely', return_value=None):
            report = collector.collect_raw_counters_from_logs()
            assert report.raw_counters.cycle_count == 0  # Значения по умолчанию

        # Мониторинг с пустым состоянием
        mock_state = Mock()
        for attr in ['memory', 'learning_engine', 'adaptation_manager',
                    'decision_engine', 'action_executor', 'environment']:
            setattr(mock_state, attr, None)
        mock_state.intelligence = {}

        stats = monitor.collect_component_stats(mock_state)

        # Все значения должны быть корректными (0 или пустые)
        assert stats.memory_episodic_size == 0
        assert stats.learning_params_count == 0
        assert stats.decision_queue_size == 0