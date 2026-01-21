"""
Тесты для системы отчетов и визуализаций.

Проверяют генерацию HTML отчетов и обработку ошибок.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile

from src.observability.external_observer import (
    ExternalObserver, SystemMetrics, BehaviorPattern, ObservationReport
)
from src.observability.reporting import ReportGenerator


class TestReportGenerator:
    """Тесты для ReportGenerator."""

    def test_initialization(self):
        """Тест инициализации генератора отчетов."""
        generator = ReportGenerator()
        assert generator.template_dir.exists()

    def test_generate_html_report_basic(self):
        """Тест базовой генерации HTML отчета."""
        generator = ReportGenerator()

        # Создаем тестовый отчет
        report = ObservationReport(
            observation_period=(time.time() - 3600, time.time()),
            metrics_summary=SystemMetrics(
                cycle_count=1000,
                uptime_seconds=3600,
                error_count=5,
                integrity_score=0.95,
                energy_level=0.85,
            ),
            behavior_patterns=[
                BehaviorPattern(
                    pattern_type="learning_cycle",
                    description="Regular learning patterns",
                    frequency=0.8,
                    impact_score=0.7,
                    first_observed=time.time() - 1800,
                    last_observed=time.time(),
                )
            ],
            trends={"energy_level": "stable", "integrity_score": "improving"},
            anomalies=[{
                "type": "minor_anomaly",
                "description": "Minor issue detected",
                "severity": "low"
            }],
            recommendations=[
                "Continue monitoring system health",
                "Review energy consumption patterns"
            ]
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_report.html"

            # Генерируем отчет
            result_path = generator.generate_html_report(report, output_path)

            # Проверяем результат
            assert result_path == output_path
            assert output_path.exists()
            assert output_path.stat().st_size > 0

            # Проверяем содержимое HTML
            content = output_path.read_text()
            assert "<!DOCTYPE html>" in content
            assert "Life System Observation Report" in content
            assert "1000" in content  # cycle_count
            assert "95%" in content  # integrity_score
            assert "learning_cycle" in content
            assert "stable" in content  # trend
            assert "monitoring system health" in content  # recommendation

    @patch('src.observability.reporting.MATPLOTLIB_AVAILABLE', False)
    def test_generate_html_report_without_matplotlib(self):
        """Тест генерации отчета без matplotlib."""
        generator = ReportGenerator()

        report = ObservationReport(
            observation_period=(1000, 2000),
            metrics_summary=SystemMetrics(),
            behavior_patterns=[],
            trends={},
            anomalies=[],
            recommendations=[]
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_report.html"

            # Должен вызвать исключение
            with pytest.raises(ImportError, match="matplotlib и jinja2 требуются"):
                generator.generate_html_report(report, output_path)

    def test_generate_summary_report(self):
        """Тест генерации сводного отчета."""
        generator = ReportGenerator()

        # Создаем несколько отчетов
        reports = [
            ObservationReport(
                observation_period=(1000, 2000),
                metrics_summary=SystemMetrics(
                    cycle_count=100,
                    integrity_score=0.9,
                    energy_level=0.8,
                    error_count=2
                ),
                behavior_patterns=[],
                trends={},
                anomalies=[],
                recommendations=[]
            ),
            ObservationReport(
                observation_period=(2000, 3000),
                metrics_summary=SystemMetrics(
                    cycle_count=150,
                    integrity_score=0.92,
                    energy_level=0.82,
                    error_count=1
                ),
                behavior_patterns=[],
                trends={},
                anomalies=[],
                recommendations=[]
            )
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "summary_report.html"

            # Генерируем сводный отчет
            result_path = generator.generate_summary_report(reports, output_path)

            # Проверяем результат
            assert result_path == output_path
            assert output_path.exists()

            content = output_path.read_text()
            assert "<!DOCTYPE html>" in content
            assert "Summary Report" in content
            assert "2" in content  # total reports

    def test_generate_summary_report_empty_list(self):
        """Тест генерации сводного отчета с пустым списком."""
        generator = ReportGenerator()

        with pytest.raises(ValueError, match="Необходимо предоставить хотя бы один отчет"):
            generator.generate_summary_report([])

    def test_chart_generation_error_handling(self):
        """Тест обработки ошибок при генерации графиков."""
        generator = ReportGenerator()

        report = ObservationReport(
            observation_period=(1000, 2000),
            metrics_summary=SystemMetrics(),
            behavior_patterns=[],
            trends={},
            anomalies=[],
            recommendations=[]
        )

        # Мокаем генерацию графиков для имитации ошибки
        with patch.object(generator, '_generate_charts', side_effect=Exception("Chart generation failed")):
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = Path(temp_dir) / "test_report.html"

                # Отчет должен сгенерироваться несмотря на ошибку графиков
                result_path = generator.generate_html_report(report, output_path)
                assert result_path.exists()

                content = output_path.read_text()
                assert "Life System Observation Report" in content

    def test_template_loading_fallback(self):
        """Тест fallback на встроенный шаблон."""
        generator = ReportGenerator()

        # Мокаем загрузку шаблона для возврата встроенного
        with patch.object(generator, '_load_template') as mock_load:
            mock_template = Mock()
            mock_template.render.return_value="<html>Test</html>"
            mock_load.return_value = mock_template

            report = ObservationReport(
                observation_period=(1000, 2000),
                metrics_summary=SystemMetrics(),
                behavior_patterns=[],
                trends={},
                anomalies=[],
                recommendations=[]
            )

            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = Path(temp_dir) / "test_report.html"

                generator.generate_html_report(report, output_path)

                mock_load.assert_called_once()
                mock_template.render.assert_called_once()

    def test_analyze_trends_over_time(self):
        """Тест анализа трендов по времени."""
        generator = ReportGenerator()

        # Создаем отчеты с трендами
        reports = [
            ObservationReport(
                observation_period=(1000, 2000),
                metrics_summary=SystemMetrics(
                    integrity_score=0.8,
                    energy_level=0.9,
                    error_count=5
                ),
                behavior_patterns=[],
                trends={},
                anomalies=[],
                recommendations=[]
            ),
            ObservationReport(
                observation_period=(2000, 3000),
                metrics_summary=SystemMetrics(
                    integrity_score=0.85,
                    energy_level=0.87,
                    error_count=3
                ),
                behavior_patterns=[],
                trends={},
                anomalies=[],
                recommendations=[]
            )
        ]

        trends = generator._analyze_trends_over_time(reports)

        # Проверяем анализ трендов
        assert len(trends) > 0

        integrity_trend = next((t for t in trends if t["metric"] == "integrity_score"), None)
        assert integrity_trend is not None
        assert integrity_trend["direction"] == "improving"
        assert integrity_trend["change_percent"] > 0

        error_trend = next((t for t in trends if t["metric"] == "error_count"), None)
        assert error_trend is not None
        assert error_trend["direction"] == "improving"  # Ошибки уменьшились

    def test_calculate_average_metrics(self):
        """Тест расчета средних метрик."""
        generator = ReportGenerator()

        reports = [
            ObservationReport(
                observation_period=(1000, 2000),
                metrics_summary=SystemMetrics(
                    cycle_count=100,
                    integrity_score=0.8,
                    error_count=5
                ),
                behavior_patterns=[],
                trends={},
                anomalies=[],
                recommendations=[]
            ),
            ObservationReport(
                observation_period=(2000, 3000),
                metrics_summary=SystemMetrics(
                    cycle_count=150,
                    integrity_score=0.9,
                    error_count=3
                ),
                behavior_patterns=[],
                trends={},
                anomalies=[],
                recommendations=[]
            )
        ]

        averages = generator._calculate_average_metrics(reports)

        # Проверяем расчет средних
        assert averages["cycle_count"] == 125.0  # (100 + 150) / 2
        assert averages["integrity_score"] == 0.85  # (0.8 + 0.9) / 2
        assert averages["error_count"] == 4.0  # (5 + 3) / 2

    def test_calculate_average_metrics_empty_list(self):
        """Тест расчета средних с пустым списком."""
        generator = ReportGenerator()

        averages = generator._calculate_average_metrics([])
        assert averages == {}


class TestReportIntegration:
    """Интеграционные тесты для системы отчетов."""

    def test_full_observation_and_reporting_workflow(self):
        """Тест полного рабочего процесса наблюдения и отчетности."""
        # Создаем наблюдателя
        observer = ExternalObserver()

        # Мокаем методы для предсказуемого тестирования
        with patch.object(observer, '_extract_metrics_from_logs') as mock_extract, \
             patch.object(observer, '_analyze_behavior_patterns') as mock_analyze, \
             patch.object(observer, '_calculate_trends') as mock_trends, \
             patch.object(observer, '_detect_anomalies') as mock_anomalies, \
             patch.object(observer, '_generate_recommendations') as mock_recommendations:

            # Настраиваем mock-данные
            mock_extract.return_value = SystemMetrics(
                cycle_count=500,
                integrity_score=0.88,
                energy_level=0.92,
                error_count=1
            )
            mock_analyze.return_value = []
            mock_trends.return_value = {"integrity_score": "stable"}
            mock_anomalies.return_value = []
            mock_recommendations.return_value = ["System operating normally"]

            # Выполняем наблюдение
            report = observer.observe_from_logs(time.time() - 1800, time.time())

            # Создаем генератор отчетов
            generator = ReportGenerator()

            with tempfile.TemporaryDirectory() as temp_dir:
                # Генерируем отчет
                output_path = Path(temp_dir) / "integration_test_report.html"
                result_path = generator.generate_html_report(report, output_path)

                # Проверяем результат
                assert result_path.exists()
                content = result_path.read_text()

                # Проверяем ключевые элементы
                assert "Life System Observation Report" in content
                assert "500" in content  # cycle_count
                assert "88%" in content  # integrity_score
                assert "System operating normally" in content

    def test_error_recovery_in_reporting(self):
        """Тест восстановления после ошибок в отчетности."""
        observer = ExternalObserver()
        generator = ReportGenerator()

        # Создаем отчет с потенциально проблемными данными
        report = ObservationReport(
            observation_period=(1000, 2000),
            metrics_summary=SystemMetrics(
                cycle_count=-1,  # Некорректное значение
                integrity_score=1.5,  # Выше максимума
                energy_level=-0.1,  # Ниже минимума
            ),
            behavior_patterns=[
                BehaviorPattern(
                    pattern_type="invalid",
                    description="Invalid pattern",
                    frequency=1.2,  # Некорректная частота
                    impact_score=0.8,
                    first_observed=2000,  # first > last
                    last_observed=1000,
                )
            ],
            trends={},
            anomalies=[],
            recommendations=[]
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "error_recovery_test.html"

            # Генерация должна завершиться успешно несмотря на некорректные данные
            result_path = generator.generate_html_report(report, output_path)
            assert result_path.exists()

            content = result_path.read_text()
            assert "Life System Observation Report" in content