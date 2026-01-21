"""
Статические тесты для технического монитора поведения.

Тестируют математические функции, анализ данных и логику без зависимостей от внешних компонентов.
"""

import json
import tempfile
import time
from unittest.mock import Mock, MagicMock

import pytest

from src.technical_monitor import (
    TechnicalSnapshot,
    TechnicalReport,
    TechnicalBehaviorMonitor,
)


class TestTechnicalSnapshot:
    """Тесты для класса TechnicalSnapshot."""

    def test_snapshot_creation(self):
        """Тест создания снимка состояния."""
        snapshot = TechnicalSnapshot()

        assert isinstance(snapshot.timestamp, float)
        assert snapshot.timestamp > 0
        assert isinstance(snapshot.self_state, dict)
        assert isinstance(snapshot.memory_stats, dict)
        assert isinstance(snapshot.learning_params, dict)
        assert isinstance(snapshot.adaptation_params, dict)
        assert isinstance(snapshot.decision_history, list)
        assert isinstance(snapshot.performance_metrics, dict)

    def test_snapshot_with_custom_data(self):
        """Тест снимка с пользовательскими данными."""
        custom_time = 123456.789
        snapshot = TechnicalSnapshot(
            timestamp=custom_time,
            self_state={"energy": 0.8, "stability": 0.9},
            memory_stats={"total_entries": 100},
            learning_params={"rate": 0.1},
            adaptation_params={"stability": 0.7},
            decision_history=[{"type": "test"}],
            performance_metrics={"efficiency": 0.95},
        )

        assert snapshot.timestamp == custom_time
        assert snapshot.self_state == {"energy": 0.8, "stability": 0.9}
        assert snapshot.memory_stats == {"total_entries": 100}
        assert snapshot.learning_params == {"rate": 0.1}
        assert snapshot.adaptation_params == {"stability": 0.7}
        assert snapshot.decision_history == [{"type": "test"}]
        assert snapshot.performance_metrics == {"efficiency": 0.95}


class TestTechnicalReport:
    """Тесты для класса TechnicalReport."""

    def test_report_creation(self):
        """Тест создания технического отчета."""
        snapshot = TechnicalSnapshot()
        report = TechnicalReport(snapshot=snapshot)

        assert isinstance(report.timestamp, float)
        assert report.timestamp > 0
        assert report.snapshot is snapshot
        assert isinstance(report.performance, dict)
        assert isinstance(report.stability, dict)
        assert isinstance(report.adaptability, dict)
        assert isinstance(report.integrity, dict)
        assert isinstance(report.overall_assessment, dict)

    def test_report_with_custom_data(self):
        """Тест отчета с пользовательскими данными."""
        snapshot = TechnicalSnapshot()
        custom_time = 123456.789
        report = TechnicalReport(
            timestamp=custom_time,
            snapshot=snapshot,
            performance={"score": 0.8},
            stability={"score": 0.7},
            adaptability={"score": 0.9},
            integrity={"score": 0.6},
            overall_assessment={"total": 0.75},
        )

        assert report.timestamp == custom_time
        assert report.performance == {"score": 0.8}
        assert report.stability == {"score": 0.7}
        assert report.adaptability == {"score": 0.9}
        assert report.integrity == {"score": 0.6}
        assert report.overall_assessment == {"total": 0.75}


class TestTechnicalBehaviorMonitor:
    """Тесты для класса TechnicalBehaviorMonitor."""

    def test_monitor_initialization(self):
        """Тест инициализации монитора."""
        monitor = TechnicalBehaviorMonitor()

        assert isinstance(monitor.report_history, list)
        assert len(monitor.report_history) == 0
        assert monitor.max_history_size == 100

    def test_extract_self_state_data_complete(self):
        """Тест извлечения полных данных self_state."""
        monitor = TechnicalBehaviorMonitor()

        # Создаем mock self_state с полными данными
        self_state = Mock()
        self_state.cycle_count = 42
        self_state.current_phase = "active"
        self_state.energy_level = 0.85
        self_state.adaptation_level = 0.75
        self_state.behavior_stats = {"actions": 100, "decisions": 50}

        data = monitor._extract_self_state_data(self_state)

        assert data["cycle_count"] == 42
        assert data["current_phase"] == "active"
        assert data["energy_level"] == 0.85
        assert data["adaptation_level"] == 0.75
        assert data["behavior_stats"] == {"actions": 100, "decisions": 50}

    def test_extract_self_state_data_missing_attributes(self):
        """Тест извлечения данных self_state с отсутствующими атрибутами."""
        monitor = TechnicalBehaviorMonitor()

        # Создаем mock self_state с отсутствующими атрибутами
        self_state = Mock()
        # Не устанавливаем атрибуты - они должны получить значения по умолчанию

        data = monitor._extract_self_state_data(self_state)

        assert data["cycle_count"] == 0
        assert data["current_phase"] == "unknown"
        assert data["energy_level"] == 0.0
        assert data["adaptation_level"] == 0.0
        assert data["behavior_stats"] == {}

    def test_extract_self_state_data_clamping(self):
        """Тест ограничения значений в self_state."""
        monitor = TechnicalBehaviorMonitor()

        self_state = Mock()
        self_state.energy_level = 1.5  # Выше максимума
        self_state.adaptation_level = -0.2  # Ниже минимума

        data = monitor._extract_self_state_data(self_state)

        assert data["energy_level"] == 1.0  # Ограничено до 1.0
        assert data["adaptation_level"] == 0.0  # Ограничено до 0.0

    def test_collect_performance_metrics_complete(self):
        """Тест сбора полных метрик производительности."""
        monitor = TechnicalBehaviorMonitor()

        # Создаем mocks для всех компонентов
        self_state = Mock()
        memory = Mock()
        memory.get_statistics.return_value = {"total_entries": 200, "efficiency": 0.85}
        learning_engine = Mock()
        learning_engine.get_parameters.return_value = {"learning_rate": 0.15, "progress": 0.7}
        adaptation_manager = Mock()
        adaptation_manager.get_parameters.return_value = {"adaptation_rate": 0.2, "stability": 0.8}
        decision_engine = Mock()
        decision_engine.get_statistics.return_value = {"average_time": 0.05, "accuracy": 0.9}

        metrics = monitor._collect_performance_metrics(
            self_state, memory, learning_engine, adaptation_manager, decision_engine
        )

        assert metrics["memory_usage"] == 200
        assert metrics["memory_efficiency"] == 0.85
        assert metrics["learning_rate"] == 0.15
        assert metrics["learning_progress"] == 0.7
        assert metrics["adaptation_rate"] == 0.2
        assert metrics["adaptation_stability"] == 0.8
        assert metrics["decision_speed"] == 0.05
        assert metrics["decision_accuracy"] == 0.9

    def test_collect_performance_metrics_missing_methods(self):
        """Тест сбора метрик при отсутствии методов."""
        monitor = TechnicalBehaviorMonitor()

        # Создаем объекты без нужных методов
        self_state = Mock()
        memory = Mock()
        learning_engine = Mock()
        adaptation_manager = Mock()
        decision_engine = Mock()

        metrics = monitor._collect_performance_metrics(
            self_state, memory, learning_engine, adaptation_manager, decision_engine
        )

        # Все метрики должны иметь значения по умолчанию
        assert metrics["memory_usage"] == 0
        assert metrics["memory_efficiency"] == 0.0
        assert metrics["learning_rate"] == 0.0
        assert metrics["learning_progress"] == 0.0
        assert metrics["adaptation_rate"] == 0.0
        assert metrics["adaptation_stability"] == 0.0
        assert metrics["decision_speed"] == 0.0
        assert metrics["decision_accuracy"] == 0.0

    def test_analyze_performance(self):
        """Тест анализа производительности."""
        monitor = TechnicalBehaviorMonitor()

        snapshot = TechnicalSnapshot()
        snapshot.performance_metrics = {
            "memory_efficiency": 0.8,
            "learning_progress": 0.6,
            "decision_speed": 0.05,
            "decision_accuracy": 0.85,
        }

        analysis = monitor._analyze_performance(snapshot)

        assert "memory_efficiency" in analysis
        assert "learning_progress" in analysis
        assert "decision_speed" in analysis
        assert "decision_accuracy" in analysis
        assert "overall_performance" in analysis

        # Общая производительность должна быть взвешенным средним
        expected_overall = 0.8 * 0.25 + 0.6 * 0.25 + 0.05 * 0.25 + 0.85 * 0.25
        assert abs(analysis["overall_performance"] - expected_overall) < 0.001

    def test_analyze_stability(self):
        """Тест анализа стабильности."""
        monitor = TechnicalBehaviorMonitor()

        snapshot = TechnicalSnapshot()
        snapshot.self_state = {"energy_level": 0.9, "adaptation_level": 0.7}
        snapshot.decision_history = [
            {"type": "decision1"},
            {"type": "decision2"},
            {"type": "decision1"},  # Повтор типа для предсказуемости
        ]
        snapshot.adaptation_params = {"adaptation_stability": 0.8}

        analysis = monitor._analyze_stability(snapshot)

        assert "state_consistency" in analysis
        assert "behavior_predictability" in analysis
        assert "parameter_stability" in analysis
        assert "overall_stability" in analysis

        # Проверка расчетов
        state_consistency = (0.9 + 0.7) / 2.0  # Среднее между energy и adaptation
        assert abs(analysis["state_consistency"] - state_consistency) < 0.001

        # Предсказуемость на основе разнообразия типов решений
        # Для len(decision_history) = 3 (< 10) используется значение по умолчанию 0.5
        expected_predictability = 0.5
        assert abs(analysis["behavior_predictability"] - expected_predictability) < 0.001

        assert analysis["parameter_stability"] == 0.8

    def test_analyze_adaptability(self):
        """Тест анализа адаптивности."""
        monitor = TechnicalBehaviorMonitor()

        snapshot = TechnicalSnapshot()
        snapshot.performance_metrics = {
            "learning_rate": 0.3,
            "adaptation_rate": 0.4,
        }
        snapshot.decision_history = [
            {"type": "adaptation"},
            {"type": "normal"},
            {"type": "adaptation"},
        ]

        analysis = monitor._analyze_adaptability(snapshot)

        assert "learning_rate" in analysis
        assert "adaptation_rate" in analysis
        assert "change_responsiveness" in analysis
        assert "overall_adaptability" in analysis

        assert analysis["learning_rate"] == 0.3
        assert analysis["adaptation_rate"] == 0.4

        # Отклик на изменения: доля adaptation решений
        # Для len(decision_history) = 3 (< 5) используется значение по умолчанию 0.0
        expected_responsiveness = 0.0
        assert abs(analysis["change_responsiveness"] - expected_responsiveness) < 0.001

        # Общая адаптивность
        expected_overall = 0.3 * 0.4 + 0.4 * 0.4 + analysis["change_responsiveness"] * 0.2
        assert abs(analysis["overall_adaptability"] - expected_overall) < 0.001

    def test_analyze_integrity(self):
        """Тест анализа целостности."""
        monitor = TechnicalBehaviorMonitor()

        snapshot = TechnicalSnapshot()
        snapshot.self_state = {"valid": "data"}
        snapshot.memory_stats = {"total": 100}
        snapshot.learning_params = {"rate": 0.1}
        snapshot.adaptation_params = {"stability": 0.8}
        snapshot.decision_history = [{"id": 1}, {"id": 2}]

        analysis = monitor._analyze_integrity(snapshot)

        assert "data_consistency" in analysis
        assert "structural_integrity" in analysis
        assert "logical_coherence" in analysis
        assert "overall_integrity" in analysis

        # Все компоненты должны быть валидными
        assert analysis["data_consistency"] == 1.0  # 4/4 успешных проверок
        assert analysis["structural_integrity"] == 1.0  # 5/5 компонентов присутствуют

    def test_analyze_integrity_with_errors(self):
        """Тест анализа целостности с ошибками в данных."""
        monitor = TechnicalBehaviorMonitor()

        snapshot = TechnicalSnapshot()
        snapshot.self_state = {"error": "failed"}
        snapshot.memory_stats = {"error": "failed"}
        snapshot.learning_params = {"valid": "data"}
        snapshot.adaptation_params = {"valid": "data"}
        snapshot.decision_history = []

        analysis = monitor._analyze_integrity(snapshot)

        # 2 ошибки из 4 проверок данных
        assert analysis["data_consistency"] == 0.5  # (4-2)/4 = 0.5

        # 2 компонента из 5 присутствуют (self_state и memory_stats содержат error, decision_history пустой)
        assert analysis["structural_integrity"] == 0.4  # 2/5

    def test_calculate_overall_assessment(self):
        """Тест расчета общей оценки."""
        monitor = TechnicalBehaviorMonitor()

        report = TechnicalReport(snapshot=TechnicalSnapshot())
        report.performance = {"overall_performance": 0.8}
        report.stability = {"overall_stability": 0.7}
        report.adaptability = {"overall_adaptability": 0.9}
        report.integrity = {"overall_integrity": 0.6}

        assessment = monitor._calculate_overall_assessment(report)

        assert "performance_score" in assessment
        assert "stability_score" in assessment
        assert "adaptability_score" in assessment
        assert "integrity_score" in assessment
        assert "overall_score" in assessment
        assert "status" in assessment

        # Проверка взвешенного среднего
        expected_overall = 0.8 * 0.25 + 0.7 * 0.25 + 0.9 * 0.25 + 0.6 * 0.25
        assert abs(assessment["overall_score"] - expected_overall) < 0.001

        # Проверка статуса
        assert assessment["status"] == "good"  # 0.75 находится в диапазоне good (0.6-0.8)

    def test_calculate_overall_assessment_statuses(self):
        """Тест определения статуса на основе оценки."""
        monitor = TechnicalBehaviorMonitor()

        test_cases = [
            (0.85, "excellent"),
            (0.75, "good"),
            (0.55, "adequate"),
            (0.35, "concerning"),
            (0.15, "critical"),
        ]

        for score, expected_status in test_cases:
            report = TechnicalReport(snapshot=TechnicalSnapshot())
            report.performance = {"overall_performance": score}
            report.stability = {"overall_stability": score}
            report.adaptability = {"overall_adaptability": score}
            report.integrity = {"overall_integrity": score}

            assessment = monitor._calculate_overall_assessment(report)
            assert assessment["status"] == expected_status

    def test_save_and_load_report(self):
        """Тест сохранения и загрузки отчета."""
        monitor = TechnicalBehaviorMonitor()

        # Создаем тестовый отчет
        snapshot = TechnicalSnapshot(
            timestamp=123456.789,
            self_state={"test": "data"},
        )
        report = TechnicalReport(
            timestamp=123456.789,
            snapshot=snapshot,
            performance={"score": 0.8},
            stability={"score": 0.7},
            adaptability={"score": 0.9},
            integrity={"score": 0.6},
            overall_assessment={"total": 0.75, "status": "good"},
        )

        # Сохраняем во временный файл
        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json") as f:
            temp_path = f.name

        try:
            monitor.save_report(report, temp_path)

            # Загружаем обратно
            loaded_report = monitor.load_report(temp_path)

            assert loaded_report is not None
            assert loaded_report.timestamp == report.timestamp
            assert loaded_report.performance == report.performance
            assert loaded_report.stability == report.stability
            assert loaded_report.adaptability == report.adaptability
            assert loaded_report.integrity == report.integrity
            assert loaded_report.overall_assessment == report.overall_assessment

        finally:
            import os

            os.unlink(temp_path)

    def test_save_report_error_handling(self):
        """Тест обработки ошибок при сохранении отчета."""
        monitor = TechnicalBehaviorMonitor()

        report = TechnicalReport(snapshot=TechnicalSnapshot())

        # Попытка сохранить в несуществующую директорию
        try:
            monitor.save_report(report, "/nonexistent/directory/report.json")
        except Exception:
            # Ожидаем ошибку, но не падаем
            pass

    def test_load_report_error_handling(self):
        """Тест обработки ошибок при загрузке отчета."""
        monitor = TechnicalBehaviorMonitor()

        # Попытка загрузить несуществующий файл
        loaded_report = monitor.load_report("/nonexistent/file.json")
        assert loaded_report is None

    def test_add_to_history(self):
        """Тест добавления отчетов в историю."""
        monitor = TechnicalBehaviorMonitor()

        # Добавляем отчеты
        for i in range(5):
            report = TechnicalReport(snapshot=TechnicalSnapshot())
            monitor._add_to_history(report)

        assert len(monitor.report_history) == 5

        # Добавляем еще отчетов сверх лимита
        for i in range(100):
            report = TechnicalReport(snapshot=TechnicalSnapshot())
            monitor._add_to_history(report)

        # История должна быть ограничена max_history_size
        assert len(monitor.report_history) == monitor.max_history_size

    def test_get_trends_insufficient_data(self):
        """Тест получения трендов с недостаточным количеством данных."""
        monitor = TechnicalBehaviorMonitor()

        # Добавляем только один отчет
        report = TechnicalReport(snapshot=TechnicalSnapshot())
        monitor._add_to_history(report)

        trends = monitor.get_trends(hours=24)

        assert "error" in trends
        assert "Недостаточно данных" in trends["error"]

    def test_get_trends_calculation(self):
        """Тест расчета трендов."""
        monitor = TechnicalBehaviorMonitor()

        # Создаем последовательность отчетов с трендом улучшения
        base_scores = [0.5, 0.6, 0.7, 0.8, 0.9]
        for i, score in enumerate(base_scores):
            report = TechnicalReport(snapshot=TechnicalSnapshot())
            report.performance = {"overall_performance": score}
            report.stability = {"overall_stability": score}
            report.adaptability = {"overall_adaptability": score}
            report.integrity = {"overall_integrity": score}
            report.overall_assessment = {"overall_score": score}
            # Имитируем время
            report.timestamp = time.time() + i * 3600  # Каждый час
            monitor._add_to_history(report)

        trends = monitor.get_trends(hours=24)

        assert "performance_trend" in trends
        assert "stability_trend" in trends
        assert "adaptability_trend" in trends
        assert "integrity_trend" in trends
        assert "overall_trend" in trends

        # Все тренды должны быть улучшающимися (direction = "improving")
        for trend_key in [
            "performance_trend",
            "stability_trend",
            "adaptability_trend",
            "integrity_trend",
            "overall_trend",
        ]:
            assert trends[trend_key]["direction"] == "improving"

    def test_calculate_trend_stable(self):
        """Тест расчета стабильного тренда."""
        monitor = TechnicalBehaviorMonitor()

        # Стабильные значения
        values = [0.8, 0.8, 0.8, 0.8, 0.8]

        trend = monitor._calculate_trend(values)

        assert trend["direction"] == "stable"
        assert trend["magnitude"] < 0.01  # Почти нулевая величина

    def test_calculate_trend_improving(self):
        """Тест расчета улучшающегося тренда."""
        monitor = TechnicalBehaviorMonitor()

        # Улучшающиеся значения
        values = [0.5, 0.6, 0.7, 0.8, 0.9]

        trend = monitor._calculate_trend(values)

        assert trend["direction"] == "improving"
        assert trend["slope"] > 0
        assert trend["magnitude"] > 0

    def test_calculate_trend_declining(self):
        """Тест расчета ухудшающегося тренда."""
        monitor = TechnicalBehaviorMonitor()

        # Ухудшающиеся значения
        values = [0.9, 0.8, 0.7, 0.6, 0.5]

        trend = monitor._calculate_trend(values)

        assert trend["direction"] == "declining"
        assert trend["slope"] < 0
        assert trend["magnitude"] > 0
