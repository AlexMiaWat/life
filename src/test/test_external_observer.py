"""
Тесты для ExternalObserver - внешнего наблюдателя за системой Life.

Проверяют корректность анализа поведения системы без вмешательства в runtime.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile

from src.observability.external_observer import (
    ExternalObserver,
    SystemMetrics,
    ObservationReport,
)


class TestExternalObserver:
    """Тесты для ExternalObserver."""

    def test_initialization(self):
        """Тест инициализации наблюдателя."""
        observer = ExternalObserver()
        assert observer.observation_history == []
        assert observer.logs_directory == Path("logs")
        assert observer.snapshots_directory == Path("data/snapshots")

    def test_initialization_with_custom_paths(self):
        """Тест инициализации с пользовательскими путями."""
        custom_logs = Path("/custom/logs")
        custom_snapshots = Path("/custom/snapshots")

        observer = ExternalObserver(
            logs_directory=custom_logs, snapshots_directory=custom_snapshots
        )

        assert observer.logs_directory == custom_logs
        assert observer.snapshots_directory == custom_snapshots

    def test_observe_from_logs_basic(self):
        """Тест базового наблюдения на основе логов."""
        observer = ExternalObserver()

        start_time = time.time() - 3600  # 1 час назад
        end_time = time.time()

        # Мокаем внутренние методы для предсказуемого тестирования
        with (
            patch.object(observer, "_extract_metrics_from_logs") as mock_extract,
            patch.object(observer, "_analyze_behavior_patterns") as mock_analyze,
            patch.object(observer, "_calculate_trends") as mock_trends,
            patch.object(observer, "_detect_anomalies") as mock_anomalies,
            patch.object(observer, "_generate_recommendations") as mock_recommendations,
        ):

            # Настраиваем mock-объекты
            mock_metrics = SystemMetrics(
                cycle_count=100,
                uptime_seconds=3600,
                memory_entries_count=50,
                learning_effectiveness=0.8,
                adaptation_rate=0.7,
                decision_success_rate=0.9,
                error_count=2,
                integrity_score=0.95,
                energy_level=0.85,
                action_count=150,
                event_processing_rate=2.1,
                state_change_frequency=1.5,
            )

            mock_patterns = [
                BehaviorPattern(
                    pattern_type="test_pattern",
                    description="Test behavior pattern",
                    frequency=0.6,
                    impact_score=0.7,
                    first_observed=start_time,
                    last_observed=end_time,
                )
            ]

            mock_extract.return_value = mock_metrics
            mock_analyze.return_value = mock_patterns
            mock_trends.return_value = {"energy_level": "stable"}
            mock_anomalies.return_value = []
            mock_recommendations.return_value = ["System performing well"]

            # Выполняем наблюдение
            report = observer.observe_from_logs(start_time, end_time)

            # Проверяем результаты
            assert isinstance(report, ObservationReport)
            assert report.observation_period == (start_time, end_time)
            assert report.metrics_summary == mock_metrics
            assert report.behavior_patterns == mock_patterns
            assert report.trends == {"energy_level": "stable"}
            assert report.anomalies == []
            assert report.recommendations == ["System performing well"]

            # Проверяем, что методы были вызваны
            mock_extract.assert_called_once_with(start_time, end_time)
            mock_analyze.assert_called_once_with(start_time, end_time)
            mock_trends.assert_called_once_with(mock_metrics)
            mock_anomalies.assert_called_once_with(mock_metrics, mock_patterns)
            mock_recommendations.assert_called_once_with(
                mock_metrics, {"energy_level": "stable"}, []
            )

            # Проверяем историю наблюдений
            assert len(observer.observation_history) == 1
            assert observer.observation_history[0] == report

    def test_observe_from_snapshots(self):
        """Тест наблюдения на основе снимков состояния."""
        observer = ExternalObserver()

        # Создаем временные файлы снимков
        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_dir = Path(temp_dir)

            # Создаем тестовые файлы снимков
            snapshot1_path = snapshot_dir / "snapshot1.json"
            snapshot2_path = snapshot_dir / "snapshot2.json"

            snapshot1_data = {"timestamp": time.time() - 100, "cycle_count": 50, "memory_count": 25}

            snapshot2_data = {"timestamp": time.time(), "cycle_count": 100, "memory_count": 50}

            snapshot1_path.write_text(str(snapshot1_data).replace("'", '"'))
            snapshot2_path.write_text(str(snapshot2_data).replace("'", '"'))

            # Мокаем внутренние методы
            with (
                patch.object(observer, "_extract_metrics_from_snapshots") as mock_extract,
                patch.object(observer, "_analyze_snapshot_patterns") as mock_analyze,
                patch.object(observer, "_calculate_snapshot_trends") as mock_trends,
                patch.object(observer, "_detect_snapshot_anomalies") as mock_anomalies,
                patch.object(
                    observer, "_generate_snapshot_recommendations"
                ) as mock_recommendations,
            ):

                mock_metrics = SystemMetrics()
                mock_patterns = []
                mock_trends.return_value = {}
                mock_anomalies.return_value = []
                mock_recommendations.return_value = []

                mock_extract.return_value = mock_metrics
                mock_analyze.return_value = mock_patterns

                # Выполняем наблюдение
                report = observer.observe_from_snapshots([snapshot1_path, snapshot2_path])

                # Проверяем результаты
                assert isinstance(report, ObservationReport)
                assert len(observer.observation_history) == 1

                # Проверяем вызовы методов
                mock_extract.assert_called_once_with([snapshot1_data, snapshot2_data])

    def test_save_report(self):
        """Тест сохранения отчета."""
        observer = ExternalObserver()

        # Создаем тестовый отчет
        report = ObservationReport(
            observation_period=(time.time() - 100, time.time()),
            metrics_summary=SystemMetrics(),
            behavior_patterns=[],
            trends={},
            anomalies=[],
            recommendations=[],
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_report.json"

            # Сохраняем отчет
            saved_path = observer.save_report(report, output_path)

            # Проверяем, что файл создан
            assert saved_path == output_path
            assert output_path.exists()

            # Проверяем содержимое
            content = output_path.read_text()
            assert "observation_period" in content
            assert "metrics_summary" in content

    def test_get_observation_history_summary_empty(self):
        """Тест получения сводки истории при пустой истории."""
        observer = ExternalObserver()

        summary = observer.get_observation_history_summary()

        assert summary["error"] == "История наблюдений пуста"

    def test_get_observation_history_summary_with_data(self):
        """Тест получения сводки истории с данными."""
        observer = ExternalObserver()

        # Добавляем тестовые отчеты
        report1 = ObservationReport(
            observation_period=(1000, 2000),
            metrics_summary=SystemMetrics(
                cycle_count=100, learning_effectiveness=0.8, error_count=5
            ),
            behavior_patterns=[],
            trends={"learning_effectiveness": "stable"},
            anomalies=[],
            recommendations=[],
        )

        report2 = ObservationReport(
            observation_period=(2000, 3000),
            metrics_summary=SystemMetrics(
                cycle_count=150, learning_effectiveness=0.85, error_count=3
            ),
            behavior_patterns=[],
            trends={"learning_effectiveness": "improving"},
            anomalies=[],
            recommendations=[],
        )

        observer.observation_history = [report1, report2]

        summary = observer.get_observation_history_summary()

        # Проверяем структуру
        assert "total_observations" in summary
        assert "average_metrics" in summary
        assert "recent_trends" in summary
        assert "observation_period" in summary

        assert summary["total_observations"] == 2
        assert "cycle_count" in summary["average_metrics"]
        assert "learning_effectiveness" in summary["recent_trends"]

    def test_error_handling_in_observation(self):
        """Тест обработки ошибок при наблюдении."""
        observer = ExternalObserver()

        # Мокаем метод извлечения метрик для генерации ошибки
        with patch.object(
            observer, "_extract_metrics_from_logs", side_effect=Exception("Test error")
        ):
            start_time = time.time() - 3600
            end_time = time.time()

            # Наблюдение должно завершиться без исключения
            report = observer.observe_from_logs(start_time, end_time)

            # Проверяем, что отчет все равно создан
            assert isinstance(report, ObservationReport)
            assert report.metrics_summary.cycle_count == 0  # Значения по умолчанию
            assert report.metrics_summary.integrity_score == 0.5

    def test_anomaly_detection(self):
        """Тест обнаружения аномалий."""
        observer = ExternalObserver()

        # Создаем метрики с аномалиями
        metrics = SystemMetrics(
            error_count=15,  # Высокий уровень ошибок
            energy_level=0.1,  # Низкий уровень энергии
            integrity_score=0.2,  # Низкая целостность
            learning_effectiveness=0.05,  # Очень низкая эффективность обучения
        )

        patterns = [
            BehaviorPattern(
                pattern_type="dominant_pattern",
                description="Very frequent pattern",
                frequency=0.98,  # Почти всегда
                impact_score=0.5,
                first_observed=time.time(),
                last_observed=time.time(),
            )
        ]

        anomalies = observer._detect_anomalies(metrics, patterns)

        # Проверяем обнаружение аномалий
        assert len(anomalies) >= 4  # Минимум 4 аномалии должны быть обнаружены

        anomaly_types = [a["type"] for a in anomalies]
        assert "high_error_rate" in anomaly_types
        assert "low_energy_level" in anomaly_types
        assert "low_integrity_score" in anomaly_types
        assert "very_low_learning" in anomaly_types

    def test_recommendation_generation(self):
        """Тест генерации рекомендаций."""
        observer = ExternalObserver()

        metrics = SystemMetrics(
            error_count=5,
            energy_level=0.3,
            integrity_score=0.9,
            learning_effectiveness=0.9,
        )

        trends = {
            "energy_level": "declining",
            "integrity_score": "stable",
            "learning_effectiveness": "improving",
        }

        anomalies = [
            {"type": "high_error_rate", "severity": "high"},
            {"type": "low_energy_level", "severity": "medium"},
        ]

        recommendations = observer._generate_recommendations(metrics, trends, anomalies)

        # Проверяем генерацию рекомендаций
        assert len(recommendations) > 0
        assert any("энергии" in rec.lower() for rec in recommendations)  # Рекомендация по энергии
        assert any("ошибок" in rec.lower() for rec in recommendations)  # Рекомендация по ошибкам
        assert any(
            "аномалия" in rec.lower() for rec in recommendations
        )  # Рекомендации по аномалиям

    def test_behavior_pattern_validation(self):
        """Тест валидации паттернов поведения."""
        observer = ExternalObserver()

        start_time = time.time() - 1000
        end_time = time.time()

        # Мокаем анализ для возврата некорректных паттернов
        with patch.object(observer, "_analyze_behavior_patterns") as mock_analyze:
            # Паттерн с некорректными данными
            invalid_patterns = [
                BehaviorPattern(
                    pattern_type="invalid_pattern",
                    description="Pattern with invalid data",
                    frequency=1.5,  # Некорректная частота > 1
                    impact_score=0.7,
                    first_observed=end_time,  # first_observed после last_observed
                    last_observed=start_time,
                ),
                BehaviorPattern(
                    pattern_type="valid_pattern",
                    description="Valid pattern",
                    frequency=0.8,
                    impact_score=0.6,
                    first_observed=start_time,
                    last_observed=end_time,
                ),
            ]

            mock_analyze.return_value = invalid_patterns

            patterns = observer._analyze_behavior_patterns(start_time, end_time)

            # Должен остаться только валидный паттерн
            assert len(patterns) == 1
            assert patterns[0].pattern_type == "valid_pattern"


class TestSystemMetrics:
    """Тесты для SystemMetrics."""

    def test_system_metrics_creation(self):
        """Тест создания метрик системы."""
        metrics = SystemMetrics(
            cycle_count=1000,
            uptime_seconds=7200,
            memory_entries_count=500,
            learning_effectiveness=0.85,
            adaptation_rate=0.75,
            decision_success_rate=0.92,
            error_count=3,
            integrity_score=0.96,
            energy_level=0.88,
            action_count=250,
            event_processing_rate=2.5,
            state_change_frequency=1.8,
        )

        assert metrics.cycle_count == 1000
        assert metrics.uptime_seconds == 7200
        assert metrics.memory_entries_count == 500
        assert metrics.learning_effectiveness == 0.85
        assert metrics.error_count == 3
        assert metrics.integrity_score == 0.96

    def test_system_metrics_defaults(self):
        """Тест значений по умолчанию."""
        metrics = SystemMetrics()

        assert metrics.cycle_count == 0
        assert metrics.error_count == 0
        assert metrics.integrity_score == 1.0  # Значение по умолчанию
        assert isinstance(metrics.timestamp, float)
        assert metrics.timestamp > 0


class TestBehaviorPattern:
    """Тесты для BehaviorPattern."""

    def test_behavior_pattern_creation(self):
        """Тест создания паттерна поведения."""
        pattern = BehaviorPattern(
            pattern_type="learning_cycle",
            description="Regular learning cycles",
            frequency=0.75,
            impact_score=0.8,
            first_observed=1000.0,
            last_observed=2000.0,
            metadata={"confidence": 0.9},
        )

        assert pattern.pattern_type == "learning_cycle"
        assert pattern.frequency == 0.75
        assert pattern.impact_score == 0.8
        assert pattern.first_observed == 1000.0
        assert pattern.last_observed == 2000.0
        assert pattern.metadata == {"confidence": 0.9}


class TestObservationReport:
    """Тесты для ObservationReport."""

    def test_observation_report_creation(self):
        """Тест создания отчета наблюдения."""
        report = ObservationReport(
            observation_period=(1000.0, 2000.0),
            metrics_summary=SystemMetrics(),
            behavior_patterns=[],
            trends={"test": "stable"},
            anomalies=[],
            recommendations=["Test recommendation"],
        )

        assert report.observation_period == (1000.0, 2000.0)
        assert isinstance(report.metrics_summary, SystemMetrics)
        assert report.trends == {"test": "stable"}
        assert report.recommendations == ["Test recommendation"]

    def test_observation_report_to_dict(self):
        """Тест преобразования отчета в словарь."""
        report = ObservationReport(
            observation_period=(1000.0, 2000.0),
            metrics_summary=SystemMetrics(cycle_count=100),
            behavior_patterns=[],
            trends={},
            anomalies=[],
            recommendations=[],
        )

        data = report.to_dict()

        assert "observation_period" in data
        assert "metrics_summary" in data
        assert data["metrics_summary"]["cycle_count"] == 100
        assert "behavior_patterns" in data
        assert "trends" in data
        assert "anomalies" in data
        assert "recommendations" in data
