"""
Дымовые тесты для TechnicalBehaviorMonitor

Проверяем:
- Базовую работоспособность без падений
- Создание экземпляров классов
- Вызов основных методов с минимальными данными
- Обработку пустых/минимальных входных данных
- Граничные значения параметров
"""

import sys
import time
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.technical_monitor import (
    TechnicalBehaviorMonitor,
    TechnicalSnapshot,
    TechnicalReport
)


@pytest.mark.smoke
class TestTechnicalMonitorSmoke:
    """Дымовые тесты для TechnicalBehaviorMonitor"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.monitor = TechnicalBehaviorMonitor()

    def test_technical_monitor_instantiation(self):
        """Тест создания экземпляра TechnicalBehaviorMonitor"""
        assert self.monitor is not None
        assert isinstance(self.monitor, TechnicalBehaviorMonitor)
        assert hasattr(self.monitor, "report_history")
        assert isinstance(self.monitor.report_history, list)

    def test_capture_snapshot_minimal_data(self):
        """Дымовой тест capture_system_snapshot с минимальными данными"""
        # Создаем mock объекты с минимальными данными
        mock_self_state = Mock()
        mock_self_state.__dict__.update({
            'life_id': 'test', 'age': 0.0, 'ticks': 0,
            'energy': 0.0, 'stability': 0.0, 'integrity': 0.0,
            'adaptation_level': 0.0
        })

        mock_memory = Mock()
        mock_memory.get_statistics.return_value = {}

        mock_learning = Mock()
        mock_learning.get_parameters.return_value = {}

        mock_adaptation = Mock()
        mock_adaptation.get_parameters.return_value = {}

        mock_decision = Mock()
        mock_decision.get_recent_decisions.return_value = []
        mock_decision.get_statistics.return_value = {}

        # Должен выполниться без исключений
        snapshot = self.monitor.capture_system_snapshot(
            mock_self_state, mock_memory, mock_learning, mock_adaptation, mock_decision
        )

        assert snapshot is not None
        assert isinstance(snapshot, TechnicalSnapshot)

    def test_analyze_snapshot_empty_data(self):
        """Дымовой тест analyze_snapshot с пустыми данными"""
        # Создаем пустой snapshot
        snapshot = TechnicalSnapshot()

        # Должен выполниться без исключений
        report = self.monitor.analyze_snapshot(snapshot)

        assert report is not None
        assert isinstance(report, TechnicalReport)
        assert isinstance(report.overall_assessment, dict)
        assert "overall_score" in report.overall_assessment

    def test_save_report_basic(self):
        """Дымовой тест save_report с базовым отчетом"""
        # Создаем минимальный отчет
        snapshot = TechnicalSnapshot()
        report = TechnicalReport(snapshot=snapshot)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            # Должен выполниться без исключений
            result = self.monitor.save_report(report, temp_path)
            assert result is not None

            # Проверяем что файл создан
            assert Path(temp_path).exists()

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_load_report_basic(self):
        """Дымовой тест load_report с существующим файлом"""
        # Сначала сохраняем отчет
        snapshot = TechnicalSnapshot()
        original_report = TechnicalReport(snapshot=snapshot)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            self.monitor.save_report(original_report, temp_path)

            # Теперь загружаем
            loaded_report = self.monitor.load_report(temp_path)

            assert loaded_report is not None
            assert isinstance(loaded_report, TechnicalReport)

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_get_trends_empty_history(self):
        """Дымовой тест get_trends с пустой историей"""
        # Должен выполниться без исключений
        trends = self.monitor.get_trends(hours=1)

        assert trends is not None
        assert isinstance(trends, dict)

    def test_get_trends_with_data(self):
        """Дымовой тест get_trends с данными в истории"""
        # Добавляем отчеты в историю
        for i in range(3):
            snapshot = TechnicalSnapshot()
            report = TechnicalReport(snapshot=snapshot)
            report.timestamp = time.time() - (i * 3600)  # Разные timestamp'ы
            self.monitor.report_history.append(report)

        # Должен выполниться без исключений
        trends = self.monitor.get_trends(hours=2)

        assert trends is not None
        assert isinstance(trends, dict)

    def test_capture_snapshot_with_realistic_data(self):
        """Дымовой тест capture_system_snapshot с реалистичными данными"""
        # Создаем mock объекты с реалистичными данными
        mock_self_state = Mock()
        mock_self_state.__dict__.update({
            'life_id': 'test_life', 'age': 100.0, 'ticks': 1000,
            'energy': 0.8, 'stability': 0.9, 'integrity': 0.85,
            'adaptation_level': 0.7, 'behavior_stats': {'test_metric': 0.5}
        })

        mock_memory = Mock()
        mock_memory.get_statistics.return_value = {
            'total_entries': 50,
            'efficiency': 0.85,
            'avg_significance': 0.6
        }

        mock_learning = Mock()
        mock_learning.get_parameters.return_value = {
            'learning_rate': 0.7,
            'progress': 0.8,
            'iterations': 1000
        }

        mock_adaptation = Mock()
        mock_adaptation.get_parameters.return_value = {
            'adaptation_rate': 0.6,
            'stability': 0.9,
            'threshold': 0.5
        }

        mock_decision = Mock()
        mock_decision.get_recent_decisions.return_value = [
            {'timestamp': time.time(), 'type': 'adaptation', 'data': {}}
        ]
        mock_decision.get_statistics.return_value = {
            'total_decisions': 1,
            'average_time': 0.01,
            'accuracy': 0.8
        }

        # Должен выполниться без исключений
        snapshot = self.monitor.capture_system_snapshot(
            mock_self_state, mock_memory, mock_learning, mock_adaptation, mock_decision
        )

        assert snapshot is not None
        assert snapshot.self_state['life_id'] == 'test_life'
        assert snapshot.memory_stats['total_entries'] == 50
        assert len(snapshot.decision_history) == 1

    def test_analyze_snapshot_with_realistic_data(self):
        """Дымовой тест analyze_snapshot с реалистичными данными"""
        # Создаем snapshot с реалистичными данными
        snapshot = TechnicalSnapshot()
        snapshot.self_state = {
            'energy_level': 0.8,
            'adaptation_level': 0.7,
            'stability': 0.9,
            'integrity': 0.85
        }
        snapshot.memory_stats = {
            'total_entries': 100,
            'efficiency': 0.85
        }
        snapshot.learning_params = {
            'learning_rate': 0.7,
            'progress': 0.8
        }
        snapshot.adaptation_params = {
            'adaptation_rate': 0.6,
            'stability': 0.9
        }
        snapshot.decision_history = [
            {'timestamp': time.time(), 'type': 'learning'},
            {'timestamp': time.time(), 'type': 'adaptation'}
        ]

        # Должен выполниться без исключений
        report = self.monitor.analyze_snapshot(snapshot)

        assert report is not None
        assert 'overall_score' in report.overall_assessment
        assert 'status' in report.overall_assessment

        # Проверяем диапазоны значений
        overall_score = report.overall_assessment['overall_score']
        assert 0.0 <= overall_score <= 1.0

    def test_multiple_reports_workflow(self):
        """Дымовой тест workflow с множественными отчетами"""
        # Создаем несколько отчетов
        for i in range(5):
            snapshot = TechnicalSnapshot()
            snapshot.self_state = {'energy_level': 0.5 + i * 0.1}  # Разные значения энергии

            report = self.monitor.analyze_snapshot(snapshot)
            self.monitor.report_history.append(report)

        # Проверяем что история сохранилась
        assert len(self.monitor.report_history) == 5

        # Проверяем trends
        trends = self.monitor.get_trends(hours=1)
        assert trends is not None

        # Проверяем сохранение всех отчетов
        with tempfile.TemporaryDirectory() as temp_dir:
            for i, report in enumerate(self.monitor.report_history):
                report_path = Path(temp_dir) / f"report_{i}.json"
                self.monitor.save_report(report, report_path)
                assert report_path.exists()

    def test_error_handling_in_capture(self):
        """Дымовой тест обработки ошибок в capture_system_snapshot"""
        # Создаем mock'и которые вызывают исключения
        mock_self_state = Mock()
        mock_self_state.__dict__.update({'life_id': 'test'})

        class FailingMemory:
            def get_statistics(self):
                raise RuntimeError("Memory failure")

        class FailingLearning:
            def get_parameters(self):
                raise ValueError("Learning failure")

        mock_adaptation = Mock()
        mock_adaptation.get_parameters.return_value = {}

        mock_decision = Mock()
        mock_decision.get_recent_decisions.return_value = []
        mock_decision.get_statistics.return_value = {}

        # Должен обработать ошибки gracefully
        snapshot = self.monitor.capture_system_snapshot(
            mock_self_state, FailingMemory(), FailingLearning(),
            mock_adaptation, mock_decision
        )

        assert snapshot is not None
        # Проверяем что ошибки были записаны
        assert 'error' in snapshot.memory_stats
        assert 'error' in snapshot.learning_params

    def test_snapshot_timestamps(self):
        """Дымовой тест работы с timestamp'ами"""
        # Создаем snapshot и проверяем timestamp
        before = time.time()
        snapshot = TechnicalSnapshot()
        after = time.time()

        assert before <= snapshot.timestamp <= after

        # Создаем report и проверяем timestamp
        report = TechnicalReport(snapshot=snapshot)
        assert before <= report.timestamp <= after

    def test_empty_collections_handling(self):
        """Дымовой тест обработки пустых коллекций"""
        # Snapshot с пустыми коллекциями
        snapshot = TechnicalSnapshot()
        snapshot.decision_history = []
        snapshot.performance_metrics = {}

        # Должен обработать без ошибок
        report = self.monitor.analyze_snapshot(snapshot)

        assert report is not None
        assert isinstance(report.performance, dict)
        assert isinstance(report.adaptability, dict)

    def test_extreme_values_handling(self):
        """Дымовой тест обработки экстремальных значений"""
        # Создаем snapshot с экстремальными значениями
        snapshot = TechnicalSnapshot()
        snapshot.self_state = {
            'energy_level': 1.0,  # Максимум
            'adaptation_level': 0.0,  # Минимум
            'stability': 1.0,
            'integrity': 0.0
        }

        # Должен обработать без ошибок
        report = self.monitor.analyze_snapshot(snapshot)

        assert report is not None
        # Проверяем что оценки в допустимых диапазонах
        assert 0.0 <= report.overall_assessment['overall_score'] <= 1.0

    def test_monitor_state_persistence(self):
        """Дымовой тест сохранения состояния monitor'а"""
        # Запоминаем начальное состояние
        initial_history_length = len(self.monitor.report_history)

        # Выполняем операции
        snapshot = TechnicalSnapshot()
        report = self.monitor.analyze_snapshot(snapshot)
        self.monitor.report_history.append(report)

        # Проверяем что состояние изменилось
        assert len(self.monitor.report_history) == initial_history_length + 1

        # Проверяем что новые операции не влияют на старые
        new_report = self.monitor.analyze_snapshot(snapshot)
        assert new_report != report  # Разные объекты
        assert new_report.timestamp != report.timestamp  # Разные timestamp'ы