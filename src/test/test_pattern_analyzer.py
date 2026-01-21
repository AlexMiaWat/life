"""
Тесты для PatternAnalyzer - анализатора паттернов поведения
"""

import pytest
from src.comparison.pattern_analyzer import PatternAnalyzer


class TestPatternAnalyzer:
    """Тесты PatternAnalyzer."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.analyzer = PatternAnalyzer()

    def test_initialization(self):
        """Тест инициализации PatternAnalyzer."""
        analyzer = PatternAnalyzer()

        assert analyzer.pattern_stats == {}
        assert analyzer.event_stats == {}
        assert analyzer.state_evolution == {}

    def test_analyze_decision_patterns(self):
        """Тест анализа паттернов решений."""
        logs = [
            {"stage": "decision", "data": {"pattern": "ignore"}},
            {"stage": "decision", "data": {"pattern": "absorb"}},
            {"stage": "decision", "data": {"pattern": "ignore"}},
            {"stage": "event", "data": {"type": "noise"}},  # Не decision
        ]

        result = self.analyzer._analyze_decision_patterns(logs)

        assert result["total_decisions"] == 3
        assert result["patterns"]["ignore"] == 2
        assert result["patterns"]["absorb"] == 1
        assert result["most_common"][0] == ("ignore", 2)
        assert result["pattern_distribution"]["ignore"] == 2 / 3
        assert result["pattern_distribution"]["absorb"] == 1 / 3

    def test_analyze_decision_patterns_empty(self):
        """Тест анализа паттернов с пустыми логами."""
        result = self.analyzer._analyze_decision_patterns([])

        assert result["total_decisions"] == 0
        assert result["patterns"] == {}

    def test_analyze_event_types(self):
        """Тест анализа типов событий."""
        logs = [
            {"stage": "event", "data": {"type": "noise"}},
            {"stage": "event", "data": {"type": "decay"}},
            {"stage": "event", "data": {"type": "noise"}},
            {"stage": "decision", "data": {"pattern": "ignore"}},  # Не event
        ]

        result = self.analyzer._analyze_event_types(logs)

        assert result["total_events"] == 3
        assert result["types"]["noise"] == 2
        assert result["types"]["decay"] == 1
        assert result["most_common"][0] == ("noise", 2)
        assert result["type_distribution"]["noise"] == 2 / 3

    def test_analyze_state_trends(self):
        """Тест анализа трендов состояния."""
        snapshot = {"energy": 50.0, "stability": 0.8, "integrity": 0.9, "ticks": 10}

        result = self.analyzer._analyze_state_trends("test_instance", snapshot)

        assert "current" in result
        # Для одного сэмпла возвращается 'trend': 'insufficient_data'
        assert result["trend"] == "insufficient_data"
        assert result["current"]["energy"] == 50.0

    def test_analyze_state_trends_with_history(self):
        """Тест анализа трендов с историей."""
        # Добавляем историю
        self.analyzer.state_evolution["test_instance"] = [
            {"energy": 40.0, "stability": 0.7, "integrity": 0.8, "ticks": 5},
            {"energy": 50.0, "stability": 0.8, "integrity": 0.9, "ticks": 10},
            {"energy": 60.0, "stability": 0.9, "integrity": 1.0, "ticks": 15},
        ]

        snapshot = {"energy": 70.0, "stability": 1.0, "integrity": 1.0, "ticks": 20}

        result = self.analyzer._analyze_state_trends("test_instance", snapshot)

        assert result["trends"]["energy"] > 0  # Положительный тренд энергии
        assert result["stability"] == "changing"  # Несколько сэмплов

    def test_analyze_correlations(self):
        """Тест анализа корреляций событий и решений."""
        logs = [
            {"correlation_id": "chain1", "stage": "event", "data": {"type": "noise"}},
            {"correlation_id": "chain1", "stage": "decision", "data": {"pattern": "ignore"}},
            {"correlation_id": "chain2", "stage": "event", "data": {"type": "decay"}},
            {"correlation_id": "chain2", "stage": "decision", "data": {"pattern": "absorb"}},
            {"correlation_id": "chain1", "stage": "event", "data": {"type": "noise"}},
            {"correlation_id": "chain1", "stage": "decision", "data": {"pattern": "ignore"}},
        ]

        result = self.analyzer._analyze_correlations(logs)

        assert "noise" in result
        assert "decay" in result
        # chain1 имеет 2 event(noise) и 2 decision(ignore) = 4 корреляции
        assert result["noise"]["ignore"] == 4
        assert result["decay"]["absorb"] == 1

    def test_analyze_instance_data(self):
        """Тест анализа данных одного инстанса."""
        instance_data = {
            "status": {"is_running": True, "is_alive": True, "uptime": 10.5},
            "snapshot": {"energy": 50.0, "stability": 0.8, "integrity": 0.9, "ticks": 10},
            "recent_logs": [
                {"stage": "decision", "data": {"pattern": "ignore"}},
                {"stage": "event", "data": {"type": "noise"}},
            ],
        }

        result = self.analyzer.analyze_instance_data("test_instance", instance_data)

        assert result["instance_id"] == "test_instance"
        assert "decision_patterns" in result
        assert "event_types" in result
        assert "state_trends" in result
        assert "correlations" in result

    def test_analyze_comparison_data(self):
        """Тест анализа данных сравнения."""
        comparison_data = {
            "timestamp": 1234567890.0,
            "instances": {
                "instance1": {
                    "status": {"is_running": True},
                    "snapshot": {"energy": 50.0},
                    "recent_logs": [{"stage": "decision", "data": {"pattern": "ignore"}}],
                },
                "instance2": {
                    "status": {"is_running": True},
                    "snapshot": {"energy": 60.0},
                    "recent_logs": [{"stage": "decision", "data": {"pattern": "absorb"}}],
                },
            },
        }

        result = self.analyzer.analyze_comparison_data(comparison_data)

        assert result["timestamp"] == 1234567890.0
        assert "instances_analysis" in result
        assert "comparison_metrics" in result
        assert "patterns_comparison" in result
        assert "diversity_metrics" in result

        assert len(result["instances_analysis"]) == 2
        assert "instance1" in result["instances_analysis"]
        assert "instance2" in result["instances_analysis"]

    def test_calculate_trend_increasing(self):
        """Тест расчета возрастающего тренда."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        trend = self.analyzer._calculate_trend(values)

        assert trend > 0

    def test_calculate_trend_decreasing(self):
        """Тест расчета убывающего тренда."""
        values = [5.0, 4.0, 3.0, 2.0, 1.0]
        trend = self.analyzer._calculate_trend(values)

        assert trend < 0

    def test_calculate_trend_constant(self):
        """Тест расчета постоянного тренда."""
        values = [5.0, 5.0, 5.0, 5.0, 5.0]
        trend = self.analyzer._calculate_trend(values)

        assert abs(trend) < 0.001

    def test_calculate_trend_insufficient_data(self):
        """Тест расчета тренда с недостаточными данными."""
        values = [5.0]
        trend = self.analyzer._calculate_trend(values)

        assert trend == 0.0

    def test_calculate_pattern_similarity_identical(self):
        """Тест расчета схожести идентичных паттернов."""
        dist1 = {"ignore": 0.5, "absorb": 0.3, "dampen": 0.2}
        dist2 = {"ignore": 0.5, "absorb": 0.3, "dampen": 0.2}

        similarity = self.analyzer._calculate_pattern_similarity(dist1, dist2)

        assert abs(similarity - 1.0) < 0.001

    def test_calculate_pattern_similarity_different(self):
        """Тест расчета схожести разных паттернов."""
        dist1 = {"ignore": 1.0, "absorb": 0.0, "dampen": 0.0}
        dist2 = {"ignore": 0.0, "absorb": 1.0, "dampen": 0.0}

        similarity = self.analyzer._calculate_pattern_similarity(dist1, dist2)

        # ignore: 0.0, absorb: 0.0, dampen: 1.0 -> среднее 0.33
        assert abs(similarity - (1.0 / 3.0)) < 0.001
