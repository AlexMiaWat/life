"""
Дымовые тесты для технического монитора поведения.

Проверяют базовую функциональность и отсутствие критических ошибок.
"""

import tempfile
import time
from unittest.mock import Mock

import pytest

from src.technical_monitor import (
    TechnicalSnapshot,
    TechnicalReport,
    TechnicalBehaviorMonitor,
)


class TestTechnicalMonitorSmoke:
    """Дымовые тесты для технического монитора."""

    def test_module_import(self):
        """Тест успешного импорта модуля."""
        try:
            from src import technical_monitor
            assert technical_monitor is not None
        except ImportError as e:
            pytest.fail(f"Не удалось импортировать модуль technical_monitor: {e}")

    def test_technical_snapshot_creation(self):
        """Тест создания TechnicalSnapshot."""
        snapshot = TechnicalSnapshot()

        assert snapshot is not None
        assert isinstance(snapshot.timestamp, float)
        assert isinstance(snapshot.self_state, dict)
        assert isinstance(snapshot.memory_stats, dict)
        assert isinstance(snapshot.learning_params, dict)
        assert isinstance(snapshot.adaptation_params, dict)
        assert isinstance(snapshot.decision_history, list)
        assert isinstance(snapshot.performance_metrics, dict)

    def test_technical_report_creation(self):
        """Тест создания TechnicalReport."""
        snapshot = TechnicalSnapshot()
        report = TechnicalReport(snapshot=snapshot)

        assert report is not None
        assert isinstance(report.timestamp, float)
        assert report.snapshot is snapshot
        assert isinstance(report.performance, dict)
        assert isinstance(report.stability, dict)
        assert isinstance(report.adaptability, dict)
        assert isinstance(report.integrity, dict)
        assert isinstance(report.overall_assessment, dict)

    def test_monitor_initialization(self):
        """Тест инициализации TechnicalBehaviorMonitor."""
        monitor = TechnicalBehaviorMonitor()

        assert monitor is not None
        assert isinstance(monitor.report_history, list)
        assert len(monitor.report_history) == 0
        assert monitor.max_history_size == 100

    def test_capture_system_snapshot_basic(self):
        """Тест базового захвата снимка системы."""
        monitor = TechnicalBehaviorMonitor()

        # Создаем mock объекты для всех компонентов
        self_state = Mock()
        memory = Mock()
        learning_engine = Mock()
        adaptation_manager = Mock()
        decision_engine = Mock()

        # Настраиваем mock методы
        memory.get_statistics.return_value = {"total_entries": 100}
        learning_engine.get_parameters.return_value = {"learning_rate": 0.1}
        adaptation_manager.get_parameters.return_value = {"adaptation_rate": 0.2}
        decision_engine.get_recent_decisions.return_value = [{"type": "test"}]

        # Захват должен пройти без исключений
        snapshot = monitor.capture_system_snapshot(
            self_state, memory, learning_engine, adaptation_manager, decision_engine
        )

        assert snapshot is not None
        assert isinstance(snapshot, TechnicalSnapshot)

    def test_capture_system_snapshot_with_errors(self):
        """Тест захвата снимка при ошибках в компонентах."""
        monitor = TechnicalBehaviorMonitor()

        # Создаем mock объекты, которые вызывают исключения
        self_state = Mock()
        memory = Mock()
        learning_engine = Mock()
        adaptation_manager = Mock()
        decision_engine = Mock()

        # Настраиваем методы на вызов исключений
        memory.get_statistics.side_effect = Exception("Memory error")
        learning_engine.get_parameters.side_effect = Exception("Learning error")
        adaptation_manager.get_parameters.side_effect = Exception("Adaptation error")
        decision_engine.get_recent_decisions.side_effect = Exception("Decision error")

        # Захват должен пройти без исключений даже при ошибках компонентов
        snapshot = monitor.capture_system_snapshot(
            self_state, memory, learning_engine, adaptation_manager, decision_engine
        )

        assert snapshot is not None
        assert isinstance(snapshot, TechnicalSnapshot)
        # Данные должны содержать информацию об ошибках
        assert "error" in snapshot.memory_stats
        assert "error" in snapshot.learning_params
        assert "error" in snapshot.adaptation_params
        assert snapshot.decision_history == []

    def test_analyze_snapshot_basic(self):
        """Тест базового анализа снимка."""
        monitor = TechnicalBehaviorMonitor()

        snapshot = TechnicalSnapshot()
        # Заполняем минимальные данные для анализа
        snapshot.self_state = {"energy_level": 0.8, "adaptation_level": 0.7}
        snapshot.memory_stats = {"total_entries": 100, "efficiency": 0.85}
        snapshot.learning_params = {"learning_rate": 0.2, "progress": 0.6}
        snapshot.adaptation_params = {"adaptation_rate": 0.3, "stability": 0.8}
        snapshot.decision_history = [{"type": "decision1"}, {"type": "decision2"}]
        snapshot.performance_metrics = {
            "memory_usage": 100,
            "memory_efficiency": 0.85,
            "learning_rate": 0.2,
            "adaptation_rate": 0.3,
            "decision_speed": 0.05,
            "decision_accuracy": 0.9,
        }

        # Анализ должен пройти без исключений
        report = monitor.analyze_snapshot(snapshot)

        assert report is not None
        assert isinstance(report, TechnicalReport)
        assert report.snapshot is snapshot
        assert isinstance(report.performance, dict)
        assert isinstance(report.stability, dict)
        assert isinstance(report.adaptability, dict)
        assert isinstance(report.integrity, dict)
        assert isinstance(report.overall_assessment, dict)

    def test_analyze_snapshot_empty_data(self):
        """Тест анализа снимка с пустыми данными."""
        monitor = TechnicalBehaviorMonitor()

        snapshot = TechnicalSnapshot()  # Все поля пустые

        # Анализ должен пройти без исключений даже с пустыми данными
        report = monitor.analyze_snapshot(snapshot)

        assert report is not None
        assert isinstance(report, TechnicalReport)

    def test_extract_self_state_data_basic(self):
        """Тест извлечения данных self_state."""
        monitor = TechnicalBehaviorMonitor()

        self_state = Mock()
        self_state.cycle_count = 42
        self_state.current_phase = "active"
        self_state.energy_level = 0.85
        self_state.adaptation_level = 0.75
        self_state.behavior_stats = {"actions": 100}

        data = monitor._extract_self_state_data(self_state)

        assert isinstance(data, dict)
        assert data["cycle_count"] == 42
        assert data["current_phase"] == "active"
        assert data["energy_level"] == 0.85
        assert data["adaptation_level"] == 0.75
        assert data["behavior_stats"] == {"actions": 100}

    def test_extract_self_state_data_missing_attrs(self):
        """Тест извлечения данных при отсутствии атрибутов."""
        monitor = TechnicalBehaviorMonitor()

        self_state = Mock()
        # Не устанавливаем атрибуты

        data = monitor._extract_self_state_data(self_state)

        assert isinstance(data, dict)
        # Должны быть значения по умолчанию
        assert data["cycle_count"] == 0
        assert data["current_phase"] == "unknown"
        assert data["energy_level"] == 0.0
        assert data["adaptation_level"] == 0.0
        assert data["behavior_stats"] == {}

    def test_collect_performance_metrics_basic(self):
        """Тест сбора метрик производительности."""
        monitor = TechnicalBehaviorMonitor()

        self_state = Mock()
        memory = Mock()
        learning_engine = Mock()
        adaptation_manager = Mock()
        decision_engine = Mock()

        # Настраиваем успешные ответы
        memory.get_statistics.return_value = {"total_entries": 200, "efficiency": 0.9}
        learning_engine.get_parameters.return_value = {"learning_rate": 0.15}
        adaptation_manager.get_parameters.return_value = {"adaptation_rate": 0.25}
        decision_engine.get_statistics.return_value = {"average_time": 0.03, "accuracy": 0.95}

        metrics = monitor._collect_performance_metrics(
            self_state, memory, learning_engine, adaptation_manager, decision_engine
        )

        assert isinstance(metrics, dict)
        assert "memory_usage" in metrics
        assert "memory_efficiency" in metrics
        assert "learning_rate" in metrics
        assert "adaptation_rate" in metrics
        assert "decision_speed" in metrics
        assert "decision_accuracy" in metrics

    def test_collect_performance_metrics_with_missing_methods(self):
        """Тест сбора метрик при отсутствии методов."""
        monitor = TechnicalBehaviorMonitor()

        self_state = Mock()
        memory = Mock()
        learning_engine = Mock()
        adaptation_manager = Mock()
        decision_engine = Mock()

        # Компоненты без нужных методов
        metrics = monitor._collect_performance_metrics(
            self_state, memory, learning_engine, adaptation_manager, decision_engine
        )

        assert isinstance(metrics, dict)
        # Все метрики должны иметь значения по умолчанию
        assert metrics["memory_usage"] == 0
        assert metrics["memory_efficiency"] == 0.0
        assert metrics["learning_rate"] == 0.0
        assert metrics["adaptation_rate"] == 0.0
        assert metrics["decision_speed"] == 0.0
        assert metrics["decision_accuracy"] == 0.0

    def test_save_and_load_report(self):
        """Тест сохранения и загрузки отчета."""
        monitor = TechnicalBehaviorMonitor()

        snapshot = TechnicalSnapshot()
        report = TechnicalReport(snapshot=snapshot)

        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            # Сохранение должно пройти без исключений
            monitor.save_report(report, temp_path)

            # Загрузка должна пройти без исключений
            loaded_report = monitor.load_report(temp_path)

            assert loaded_report is not None
            assert isinstance(loaded_report, TechnicalReport)

        finally:
            import os
            os.unlink(temp_path)

    def test_get_trends_basic(self):
        """Тест получения трендов."""
        monitor = TechnicalBehaviorMonitor()

        # Добавляем несколько отчетов в историю
        for i in range(5):
            report = TechnicalReport(snapshot=TechnicalSnapshot())
            report.performance = {"overall_performance": 0.5 + i * 0.1}
            report.stability = {"overall_stability": 0.6 + i * 0.08}
            report.adaptability = {"overall_adaptability": 0.7 + i * 0.06}
            report.integrity = {"overall_integrity": 0.8 + i * 0.04}
            report.overall_assessment = {"overall_score": 0.65 + i * 0.07}
            # Имитируем время
            report.timestamp = time.time() + i * 3600
            monitor._add_to_history(report)

        trends = monitor.get_trends(hours=24)

        assert isinstance(trends, dict)
        assert "performance_trend" in trends
        assert "stability_trend" in trends
        assert "adaptability_trend" in trends
        assert "integrity_trend" in trends
        assert "overall_trend" in trends

    def test_get_trends_insufficient_data(self):
        """Тест получения трендов с недостаточными данными."""
        monitor = TechnicalBehaviorMonitor()

        # Добавляем только один отчет
        report = TechnicalReport(snapshot=TechnicalSnapshot())
        monitor._add_to_history(report)

        trends = monitor.get_trends(hours=24)

        assert isinstance(trends, dict)
        assert "error" in trends

    def test_add_to_history(self):
        """Тест добавления отчетов в историю."""
        monitor = TechnicalBehaviorMonitor()

        # Добавляем отчеты
        for i in range(5):
            report = TechnicalReport(snapshot=TechnicalSnapshot())
            monitor._add_to_history(report)

        assert len(monitor.report_history) == 5

    def test_calculate_trend_basic(self):
        """Тест расчета тренда."""
        monitor = TechnicalBehaviorMonitor()

        values = [0.5, 0.6, 0.7, 0.8, 0.9]

        trend = monitor._calculate_trend(values)

        assert isinstance(trend, dict)
        assert "direction" in trend
        assert "magnitude" in trend
        assert "slope" in trend

    def test_calculate_overall_assessment(self):
        """Тест расчета общей оценки."""
        monitor = TechnicalBehaviorMonitor()

        report = TechnicalReport(snapshot=TechnicalSnapshot())
        report.performance = {"overall_performance": 0.8}
        report.stability = {"overall_stability": 0.7}
        report.adaptability = {"overall_adaptability": 0.9}
        report.integrity = {"overall_integrity": 0.6}

        assessment = monitor._calculate_overall_assessment(report)

        assert isinstance(assessment, dict)
        assert "performance_score" in assessment
        assert "stability_score" in assessment
        assert "adaptability_score" in assessment
        assert "integrity_score" in assessment
        assert "overall_score" in assessment
        assert "status" in assessment

    def test_realistic_usage_scenario(self):
        """Тест реалистичного сценария использования."""
        monitor = TechnicalBehaviorMonitor()

        # Имитация типичного использования в runtime loop
        self_state = Mock()
        self_state.energy = 0.8
        self_state.stability = 0.75
        self_state.ticks = 100

        memory = Mock()
        memory.get_statistics.return_value = {"total_entries": 150, "efficiency": 0.85}

        learning_engine = Mock()
        learning_engine.get_parameters.return_value = {"learning_rate": 0.12, "progress": 0.65}

        adaptation_manager = Mock()
        adaptation_manager.get_parameters.return_value = {"adaptation_rate": 0.18, "stability": 0.82}

        decision_engine = Mock()
        decision_engine.get_recent_decisions.return_value = [
            {"type": "decision", "timestamp": time.time()},
            {"type": "action", "timestamp": time.time()},
        ]
        decision_engine.get_statistics.return_value = {"average_time": 0.04, "accuracy": 0.88}

        # Полный цикл мониторинга должен пройти без исключений
        snapshot = monitor.capture_system_snapshot(
            self_state, memory, learning_engine, adaptation_manager, decision_engine
        )
        report = monitor.analyze_snapshot(snapshot)

        # Сохранение отчета
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            monitor.save_report(report, temp_path)
            loaded_report = monitor.load_report(temp_path)

            assert loaded_report is not None

            # Проверка трендов
            monitor._add_to_history(report)
            trends = monitor.get_trends(hours=1)

            assert isinstance(trends, dict)

        finally:
            import os
            os.unlink(temp_path)