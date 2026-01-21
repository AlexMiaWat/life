"""
Тесты для ComparisonMetrics - метрик сравнения жизней
"""

import pytest
from src.comparison.comparison_metrics import ComparisonMetrics


class TestComparisonMetrics:
    """Тесты ComparisonMetrics."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.metrics = ComparisonMetrics()

    def test_initialization(self):
        """Тест инициализации ComparisonMetrics."""
        metrics = ComparisonMetrics()

        assert metrics.historical_data == {}

    def test_compute_similarity_metrics_single_instance(self):
        """Тест метрик схожести для одного инстанса."""
        instances_data = {
            "instance1": {"snapshot": {"energy": 50.0, "stability": 0.8, "integrity": 0.9}}
        }

        result = self.metrics.compute_similarity_metrics(instances_data)

        # Для одного инстанса не должно быть попарных сравнений
        assert result["state_similarity"] == {}
        assert result["behavior_similarity"] == {}
        assert result["evolution_similarity"] == {}

    def test_compute_similarity_metrics_two_instances(self):
        """Тест метрик схожести для двух инстансов."""
        instances_data = {
            "instance1": {
                "snapshot": {"energy": 50.0, "stability": 0.8, "integrity": 0.9},
                "recent_logs": [
                    {"stage": "decision", "data": {"pattern": "ignore"}},
                    {"stage": "decision", "data": {"pattern": "absorb"}},
                ],
            },
            "instance2": {
                "snapshot": {"energy": 55.0, "stability": 0.85, "integrity": 0.95},
                "recent_logs": [
                    {"stage": "decision", "data": {"pattern": "ignore"}},
                    {"stage": "decision", "data": {"pattern": "dampen"}},
                ],
            },
        }

        result = self.metrics.compute_similarity_metrics(instances_data)

        # Должны быть метрики для пары instance1_vs_instance2
        pair_key = "instance1_vs_instance2"
        assert pair_key in result["state_similarity"]
        assert pair_key in result["behavior_similarity"]
        assert pair_key in result["overall_similarity"]

        # Общая схожесть должна быть между 0 и 1
        overall_sim = result["overall_similarity"][pair_key]
        assert 0.0 <= overall_sim <= 1.0

    def test_compute_performance_metrics(self):
        """Тест метрик производительности."""
        instances_data = {
            "instance1": {
                "status": {"is_alive": True, "uptime": 100.0},
                "snapshot": {"energy": 50.0, "stability": 0.8, "integrity": 0.9, "ticks": 50},
                "recent_logs": [{"stage": "event"}, {"stage": "decision"}, {"stage": "action"}],
            }
        }

        result = self.metrics.compute_performance_metrics(instances_data)

        assert "instance1" in result["survival_rates"]
        assert "instance1" in result["adaptation_efficiency"]
        assert "instance1" in result["resource_usage"]

        survival = result["survival_rates"]["instance1"]
        assert survival["is_alive"] is True
        assert survival["uptime"] == 100.0
        assert survival["ticks_survived"] == 50

        adaptation = result["adaptation_efficiency"]["instance1"]
        assert isinstance(adaptation, float)
        assert 0.0 <= adaptation <= 1.0

    def test_compute_diversity_metrics_single_instance(self):
        """Тест метрик разнообразия для одного инстанса."""
        instances_data = {
            "instance1": {
                "recent_logs": [
                    {"stage": "decision", "data": {"pattern": "ignore"}},
                    {"stage": "decision", "data": {"pattern": "absorb"}},
                ],
                "snapshot": {"energy": 50.0, "stability": 0.8, "integrity": 0.9},
            }
        }

        result = self.metrics.compute_diversity_metrics(instances_data)

        assert result["pattern_diversity"] == 2  # 2 уникальных паттерна
        assert result["behavior_diversity"] == 1.0  # Только один набор поведения
        assert result["diversity_score"] > 0

    def test_compute_diversity_metrics_multiple_instances(self):
        """Тест метрик разнообразия для нескольких инстансов."""
        instances_data = {
            "instance1": {
                "recent_logs": [
                    {"stage": "decision", "data": {"pattern": "ignore"}},
                    {"stage": "decision", "data": {"pattern": "absorb"}},
                ],
                "snapshot": {"energy": 50.0, "stability": 0.8, "integrity": 0.9},
            },
            "instance2": {
                "recent_logs": [
                    {"stage": "decision", "data": {"pattern": "dampen"}},
                    {"stage": "decision", "data": {"pattern": "ignore"}},
                ],
                "snapshot": {"energy": 60.0, "stability": 0.7, "integrity": 0.8},
            },
        }

        result = self.metrics.compute_diversity_metrics(instances_data)

        assert result["pattern_diversity"] == 3  # ignore, absorb, dampen
        assert 0.0 <= result["behavior_diversity"] <= 1.0
        assert 0.0 <= result["diversity_score"] <= 1.0

    def test_compute_evolution_metrics_no_history(self):
        """Тест метрик эволюции без истории."""
        instances_data = {
            "instance1": {"snapshot": {"energy": 50.0, "stability": 0.8, "integrity": 0.9}}
        }

        result = self.metrics.compute_evolution_metrics(instances_data)

        assert result["growth_rates"] == {}
        assert result["adaptation_curves"] == {}

    def test_compute_evolution_metrics_with_history(self):
        """Тест метрик эволюции с историей."""
        # Добавляем историю для instance1
        self.metrics.historical_data["instance1"] = [
            {"energy": 40.0, "stability": 0.7, "integrity": 0.8, "ticks": 5},
            {"energy": 50.0, "stability": 0.8, "integrity": 0.9, "ticks": 10},
        ]

        instances_data = {
            "instance1": {
                "snapshot": {"energy": 60.0, "stability": 0.9, "integrity": 1.0, "ticks": 15}
            }
        }

        result = self.metrics.compute_evolution_metrics(instances_data)

        assert "instance1" in result["growth_rates"]
        assert "instance1" in result["adaptation_curves"]

        growth = result["growth_rates"]["instance1"]
        assert "energy_growth" in growth
        assert "stability_growth" in growth

        curve = result["adaptation_curves"]["instance1"]
        assert "trend" in curve
        assert "final_score" in curve

    def test_get_summary_report(self):
        """Тест получения сводного отчета."""
        instances_data = {
            "instance1": {
                "snapshot": {"energy": 50.0, "stability": 0.8, "integrity": 0.9},
                "recent_logs": [{"stage": "decision", "data": {"pattern": "ignore"}}],
            },
            "instance2": {
                "snapshot": {"energy": 55.0, "stability": 0.85, "integrity": 0.95},
                "recent_logs": [{"stage": "decision", "data": {"pattern": "absorb"}}],
            },
        }

        result = self.metrics.get_summary_report(instances_data)

        assert "similarity_metrics" in result
        assert "performance_metrics" in result
        assert "diversity_metrics" in result
        assert "evolution_metrics" in result

    def test_calculate_trend(self):
        """Тест расчета тренда."""
        # Возрастающая последовательность
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        trend = self.metrics._calculate_trend(values)
        assert trend > 0

        # Убывающая последовательность
        values = [5.0, 4.0, 3.0, 2.0, 1.0]
        trend = self.metrics._calculate_trend(values)
        assert trend < 0

        # Постоянная последовательность
        values = [3.0, 3.0, 3.0, 3.0, 3.0]
        trend = self.metrics._calculate_trend(values)
        assert abs(trend) < 0.001

        # Недостаточно данных
        values = [5.0]
        trend = self.metrics._calculate_trend(values)
        assert trend == 0.0

    def test_compute_state_similarity_identical(self):
        """Тест схожести идентичных состояний."""
        data1 = {"snapshot": {"energy": 50.0, "stability": 0.8, "integrity": 0.9}}
        data2 = {"snapshot": {"energy": 50.0, "stability": 0.8, "integrity": 0.9}}

        similarity = self.metrics._compute_state_similarity(data1, data2)

        assert abs(similarity - 1.0) < 0.001

    def test_compute_state_similarity_different(self):
        """Тест схожести разных состояний."""
        data1 = {"snapshot": {"energy": 100.0, "stability": 1.0, "integrity": 1.0}}
        data2 = {"snapshot": {"energy": 0.0, "stability": 0.0, "integrity": 0.0}}

        similarity = self.metrics._compute_state_similarity(data1, data2)

        # energy: 0.0, stability: 0.99, integrity: 0.99 -> среднее ~0.66
        assert abs(similarity - 0.66) < 0.01

    def test_compute_behavior_similarity_identical(self):
        """Тест схожести идентичного поведения."""
        data1 = {
            "recent_logs": [
                {"stage": "decision", "data": {"pattern": "ignore"}},
                {"stage": "decision", "data": {"pattern": "absorb"}},
            ]
        }
        data2 = {
            "recent_logs": [
                {"stage": "decision", "data": {"pattern": "ignore"}},
                {"stage": "decision", "data": {"pattern": "absorb"}},
            ]
        }

        similarity = self.metrics._compute_behavior_similarity(data1, data2)

        assert similarity > 0.8  # Высокая схожесть

    def test_compute_behavior_similarity_different(self):
        """Тест схожести разного поведения."""
        data1 = {"recent_logs": [{"stage": "decision", "data": {"pattern": "ignore"}}]}
        data2 = {"recent_logs": [{"stage": "decision", "data": {"pattern": "dampen"}}]}

        similarity = self.metrics._compute_behavior_similarity(data1, data2)

        assert similarity < 0.5  # Низкая схожесть
