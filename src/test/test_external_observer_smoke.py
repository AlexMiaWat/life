"""
Дымовые тесты для ExternalObserver

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
from unittest.mock import Mock, patch

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.observability.external_observer import (
    ExternalObserver,
    SystemMetrics,
    BehaviorPattern,
    ObservationReport
)


@pytest.mark.smoke
class TestExternalObserverSmoke:
    """Дымовые тесты для ExternalObserver"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.observer = ExternalObserver()

    def test_external_observer_instantiation(self):
        """Тест создания экземпляра ExternalObserver"""
        assert self.observer is not None
        assert isinstance(self.observer, ExternalObserver)
        assert hasattr(self.observer, "observation_history")
        assert isinstance(self.observer.observation_history, list)
        assert len(self.observer.observation_history) == 0

    def test_external_observer_custom_paths(self):
        """Тест создания ExternalObserver с пользовательскими путями"""
        custom_logs = Path("/custom/logs")
        custom_snapshots = Path("/custom/snapshots")

        observer = ExternalObserver(
            logs_directory=custom_logs,
            snapshots_directory=custom_snapshots
        )

        assert observer.logs_directory == custom_logs
        assert observer.snapshots_directory == custom_snapshots

    def test_observe_from_logs_minimal_call(self):
        """Дымовой тест observe_from_logs с минимальными параметрами"""
        # Мокаем внутренние методы для предотвращения реального чтения файлов
        with patch.object(self.observer, '_extract_metrics_from_logs') as mock_extract, \
             patch.object(self.observer, '_analyze_behavior_patterns') as mock_analyze, \
             patch.object(self.observer, '_calculate_trends') as mock_trends, \
             patch.object(self.observer, '_detect_anomalies') as mock_anomalies, \
             patch.object(self.observer, '_generate_recommendations') as mock_recommendations:

            # Настраиваем mock'и
            mock_extract.return_value = SystemMetrics()
            mock_analyze.return_value = []
            mock_trends.return_value = {}
            mock_anomalies.return_value = []
            mock_recommendations.return_value = []

            # Должен выполниться без исключений
            start_time = time.time() - 3600
            end_time = time.time()
            report = self.observer.observe_from_logs(start_time, end_time)

            assert report is not None
            assert isinstance(report, ObservationReport)
            assert len(self.observer.observation_history) == 1

    def test_observe_from_logs_default_times(self):
        """Дымовой тест observe_from_logs с параметрами по умолчанию"""
        with patch.object(self.observer, '_extract_metrics_from_logs') as mock_extract, \
             patch.object(self.observer, '_analyze_behavior_patterns') as mock_analyze, \
             patch.object(self.observer, '_calculate_trends') as mock_trends, \
             patch.object(self.observer, '_detect_anomalies') as mock_anomalies, \
             patch.object(self.observer, '_generate_recommendations') as mock_recommendations:

            mock_extract.return_value = SystemMetrics()
            mock_analyze.return_value = []
            mock_trends.return_value = {}
            mock_anomalies.return_value = []
            mock_recommendations.return_value = []

            # Вызываем без параметров (используются значения по умолчанию)
            report = self.observer.observe_from_logs()

            assert report is not None
            assert isinstance(report.observation_period, tuple)
            assert len(report.observation_period) == 2

    def test_observe_from_snapshots_minimal_call(self):
        """Дымовой тест observe_from_snapshots с минимальными данными"""
        with patch.object(self.observer, '_extract_metrics_from_snapshots') as mock_extract, \
             patch.object(self.observer, '_analyze_snapshot_patterns') as mock_analyze, \
             patch.object(self.observer, '_calculate_snapshot_trends') as mock_trends, \
             patch.object(self.observer, '_detect_snapshot_anomalies') as mock_anomalies, \
             patch.object(self.observer, '_generate_snapshot_recommendations') as mock_recommendations:

            mock_extract.return_value = SystemMetrics()
            mock_analyze.return_value = []
            mock_trends.return_value = {}
            mock_anomalies.return_value = []
            mock_recommendations.return_value = []

            # Должен выполниться без исключений с пустым списком
            report = self.observer.observe_from_snapshots([])

            assert report is not None
            assert isinstance(report, ObservationReport)

    def test_save_report_basic(self):
        """Дымовой тест save_report с базовым отчетом"""
        # Создаем минимальный отчет
        report = ObservationReport(
            observation_period=(1000.0, 2000.0),
            metrics_summary=SystemMetrics(),
            behavior_patterns=[],
            trends={},
            anomalies=[],
            recommendations=[]
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)

        try:
            # Должен выполниться без исключений
            result = self.observer.save_report(report, temp_path)
            assert result is not None

            # Проверяем что файл создан
            assert temp_path.exists()

            # Проверяем что файл содержит данные
            content = temp_path.read_text()
            assert len(content) > 0
            assert "observation_period" in content

        finally:
            temp_path.unlink(missing_ok=True)

    def test_get_observation_history_summary_empty(self):
        """Дымовой тест get_observation_history_summary с пустой историей"""
        # Должен выполниться без исключений
        summary = self.observer.get_observation_history_summary()

        assert summary is not None
        assert isinstance(summary, dict)
        assert "error" in summary  # Ожидаем ошибку для пустой истории

    def test_get_observation_history_summary_with_data(self):
        """Дымовой тест get_observation_history_summary с данными"""
        # Добавляем отчеты в историю
        for i in range(3):
            report = ObservationReport(
                observation_period=(1000.0 + i * 100, 1100.0 + i * 100),
                metrics_summary=SystemMetrics(cycle_count=100 + i * 50),
                behavior_patterns=[],
                trends={},
                anomalies=[],
                recommendations=[]
            )
            self.observer.observation_history.append(report)

        # Должен выполниться без исключений
        summary = self.observer.get_observation_history_summary()

        assert summary is not None
        assert isinstance(summary, dict)
        assert "total_observations" in summary
        assert summary["total_observations"] == 3

    def test_observe_from_logs_with_realistic_data(self):
        """Дымовой тест observe_from_logs с реалистичными данными"""
        with patch.object(self.observer, '_extract_metrics_from_logs') as mock_extract, \
             patch.object(self.observer, '_analyze_behavior_patterns') as mock_analyze, \
             patch.object(self.observer, '_calculate_trends') as mock_trends, \
             patch.object(self.observer, '_detect_anomalies') as mock_anomalies, \
             patch.object(self.observer, '_generate_recommendations') as mock_recommendations:

            # Создаем реалистичные mock данные
            metrics = SystemMetrics(
                cycle_count=1000,
                uptime_seconds=7200.0,
                memory_entries_count=500,
                learning_effectiveness=0.85,
                adaptation_rate=0.75,
                decision_success_rate=0.92,
                error_count=3,
                integrity_score=0.96,
                energy_level=0.88,
                action_count=250,
                event_processing_rate=2.5,
                state_change_frequency=1.8
            )

            patterns = [
                BehaviorPattern(
                    pattern_type="learning_cycle",
                    description="Regular learning cycles",
                    frequency=0.75,
                    impact_score=0.8,
                    first_observed=time.time() - 3600,
                    last_observed=time.time()
                )
            ]

            mock_extract.return_value = metrics
            mock_analyze.return_value = patterns
            mock_trends.return_value = {"energy_level": "stable", "learning_effectiveness": "improving"}
            mock_anomalies.return_value = []
            mock_recommendations.return_value = ["System performing well"]

            # Должен выполниться без исключений
            start_time = time.time() - 3600
            end_time = time.time()
            report = self.observer.observe_from_logs(start_time, end_time)

            assert report is not None
            assert report.metrics_summary.cycle_count == 1000
            assert len(report.behavior_patterns) == 1
            assert report.behavior_patterns[0].pattern_type == "learning_cycle"

    def test_observe_from_snapshots_with_files(self):
        """Дымовой тест observe_from_snapshots с тестовыми файлами"""
        with patch.object(self.observer, '_extract_metrics_from_snapshots') as mock_extract, \
             patch.object(self.observer, '_analyze_snapshot_patterns') as mock_analyze, \
             patch.object(self.observer, '_calculate_snapshot_trends') as mock_trends, \
             patch.object(self.observer, '_detect_snapshot_anomalies') as mock_anomalies, \
             patch.object(self.observer, '_generate_snapshot_recommendations') as mock_recommendations:

            mock_extract.return_value = SystemMetrics()
            mock_analyze.return_value = []
            mock_trends.return_value = {}
            mock_anomalies.return_value = []
            mock_recommendations.return_value = []

            # Создаем временные файлы снимков
            with tempfile.TemporaryDirectory() as temp_dir:
                snapshot1_path = Path(temp_dir) / "snapshot1.json"
                snapshot2_path = Path(temp_dir) / "snapshot2.json"

                # Создаем тестовые файлы
                snapshot1_data = {
                    "timestamp": time.time() - 100,
                    "cycle_count": 50,
                    "memory_count": 25
                }
                snapshot2_data = {
                    "timestamp": time.time(),
                    "cycle_count": 100,
                    "memory_count": 50
                }

                snapshot1_path.write_text(str(snapshot1_data).replace("'", '"'))
                snapshot2_path.write_text(str(snapshot2_data).replace("'", '"'))

                # Должен выполниться без исключений
                report = self.observer.observe_from_snapshots([snapshot1_path, snapshot2_path])

                assert report is not None
                assert isinstance(report, ObservationReport)

    def test_multiple_observations_workflow(self):
        """Дымовой тест workflow с множественными наблюдениями"""
        # Выполняем несколько наблюдений
        for i in range(3):
            with patch.object(self.observer, '_extract_metrics_from_logs') as mock_extract, \
                 patch.object(self.observer, '_analyze_behavior_patterns') as mock_analyze, \
                 patch.object(self.observer, '_calculate_trends') as mock_trends, \
                 patch.object(self.observer, '_detect_anomalies') as mock_anomalies, \
                 patch.object(self.observer, '_generate_recommendations') as mock_recommendations:

                metrics = SystemMetrics(cycle_count=100 * (i + 1))
                mock_extract.return_value = metrics
                mock_analyze.return_value = []
                mock_trends.return_value = {}
                mock_anomalies.return_value = []
                mock_recommendations.return_value = []

                start_time = time.time() - 3600 + i * 100
                end_time = time.time() + i * 100
                self.observer.observe_from_logs(start_time, end_time)

        # Проверяем что история сохранилась
        assert len(self.observer.observation_history) == 3

        # Проверяем summary
        summary = self.observer.get_observation_history_summary()
        assert summary["total_observations"] == 3

    def test_error_handling_in_observation(self):
        """Дымовой тест обработки ошибок при наблюдении"""
        # Мокаем метод извлечения метрик для генерации ошибки
        with patch.object(self.observer, '_extract_metrics_from_logs', side_effect=Exception("Test error")):
            start_time = time.time() - 3600
            end_time = time.time()

            # Наблюдение должно завершиться без исключения
            report = self.observer.observe_from_logs(start_time, end_time)

            # Проверяем что отчет все равно создан
            assert report is not None
            assert isinstance(report, ObservationReport)
            # Проверяем что используются значения по умолчанию
            assert report.metrics_summary.cycle_count == 0
            assert report.metrics_summary.integrity_score == 0.5

    def test_dataclass_creation_and_serialization(self):
        """Дымовой тест создания и сериализации dataclasses"""
        # Создаем полный набор объектов
        metrics = SystemMetrics(
            cycle_count=1000,
            uptime_seconds=3600.0,
            learning_effectiveness=0.85,
            error_count=5,
            energy_level=0.9
        )

        pattern = BehaviorPattern(
            pattern_type="test_pattern",
            description="Test behavior pattern",
            frequency=0.8,
            impact_score=0.7,
            first_observed=time.time() - 1000,
            last_observed=time.time()
        )

        report = ObservationReport(
            observation_period=(time.time() - 3600, time.time()),
            metrics_summary=metrics,
            behavior_patterns=[pattern],
            trends={"energy_level": "stable"},
            anomalies=[{"type": "high_error_rate"}],
            recommendations=["Check error handling"]
        )

        # Проверяем сериализацию
        data = report.to_dict()
        assert data is not None
        assert isinstance(data, dict)
        assert data["metrics_summary"]["cycle_count"] == 1000
        assert len(data["behavior_patterns"]) == 1

    def test_empty_collections_handling(self):
        """Дымовой тест обработки пустых коллекций"""
        # Создаем отчет с пустыми коллекциями
        report = ObservationReport(
            observation_period=(1000.0, 2000.0),
            metrics_summary=SystemMetrics(),
            behavior_patterns=[],  # Пустой список
            trends={},  # Пустой словарь
            anomalies=[],  # Пустой список
            recommendations=[]  # Пустой список
        )

        # Должен сериализоваться без ошибок
        data = report.to_dict()
        assert data is not None
        assert data["behavior_patterns"] == []
        assert data["trends"] == {}
        assert data["anomalies"] == []
        assert data["recommendations"] == []

    def test_extreme_values_handling(self):
        """Дымовой тест обработки экстремальных значений"""
        # Создаем metrics с экстремальными значениями
        metrics = SystemMetrics(
            cycle_count=999999,  # Очень большое число
            uptime_seconds=0.0,  # Минимум
            learning_effectiveness=1.0,  # Максимум
            error_count=0,  # Минимум
            energy_level=0.0,  # Минимум
            integrity_score=1.0  # Максимум
        )

        # Должен работать без ошибок
        report = ObservationReport(
            observation_period=(1000.0, 2000.0),
            metrics_summary=metrics,
            behavior_patterns=[],
            trends={},
            anomalies=[],
            recommendations=[]
        )

        data = report.to_dict()
        assert data["metrics_summary"]["cycle_count"] == 999999
        assert data["metrics_summary"]["energy_level"] == 0.0

    def test_observer_state_persistence(self):
        """Дымовой тест сохранения состояния observer'а"""
        # Запоминаем начальное состояние
        initial_history_length = len(self.observer.observation_history)

        # Выполняем наблюдение
        with patch.object(self.observer, '_extract_metrics_from_logs') as mock_extract, \
             patch.object(self.observer, '_analyze_behavior_patterns') as mock_analyze, \
             patch.object(self.observer, '_calculate_trends') as mock_trends, \
             patch.object(self.observer, '_detect_anomalies') as mock_anomalies, \
             patch.object(self.observer, '_generate_recommendations') as mock_recommendations:

            mock_extract.return_value = SystemMetrics()
            mock_analyze.return_value = []
            mock_trends.return_value = {}
            mock_anomalies.return_value = []
            mock_recommendations.return_value = []

            self.observer.observe_from_logs()

        # Проверяем что состояние изменилось
        assert len(self.observer.observation_history) == initial_history_length + 1

        # Проверяем что новые операции не влияют на старые
        summary1 = self.observer.get_observation_history_summary()
        assert summary1["total_observations"] == initial_history_length + 1

    def test_timestamp_handling(self):
        """Дымовой тест работы с timestamp'ами"""
        # Создаем объекты и проверяем timestamp'ы
        before = time.time()

        metrics = SystemMetrics()
        pattern = BehaviorPattern(
            pattern_type="test",
            description="test",
            frequency=0.5,
            impact_score=0.5,
            first_observed=before - 100,
            last_observed=before
        )
        report = ObservationReport(
            observation_period=(before - 3600, before),
            metrics_summary=metrics,
            behavior_patterns=[pattern],
            trends={},
            anomalies=[],
            recommendations=[]
        )

        after = time.time()

        # Проверяем что timestamp'ы в допустимых диапазонах
        assert before <= metrics.timestamp <= after
        assert pattern.first_observed == before - 100
        assert pattern.last_observed == before