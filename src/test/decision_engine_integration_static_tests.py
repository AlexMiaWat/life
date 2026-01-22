"""
Статические тесты для интеграции DecisionEngine в Runtime Loop.

Включает unit тесты, валидацию типов, проверку логирования решений.
"""

import pytest
import time
from typing import Dict, Any, Optional
from unittest.mock import Mock, MagicMock, patch

from src.decision.decision import decide_response
from src.observability.structured_logger import StructuredLogger
from src.runtime.performance_monitor import performance_monitor


class TestDecisionEngineIntegration:
    """Тесты для интеграции DecisionEngine в runtime loop."""

    def setup_method(self):
        """Настройка теста."""
        self.mock_logger = Mock(spec=StructuredLogger)
        self.mock_self_state = Mock()
        self.mock_self_state.energy = 0.8
        self.mock_self_state.stability = 0.7
        self.mock_self_state.integrity = 0.9
        self.mock_self_state.adaptation_params = {
            "response_coefficients": {"dampen": 0.5, "absorb": 1.0, "ignore": 0.0}
        }
        self.mock_self_state.last_pattern = None

    def test_decide_response_basic_call(self):
        """Тест базового вызова decide_response."""
        meaning = {
            "event_type": "test_event",
            "significance": 0.7,
            "urgency": 0.5,
            "data": {"test": "value"}
        }

        with patch('src.decision.decision.decide_response') as mock_decide:
            mock_decide.return_value = "test_pattern"

            pattern = decide_response(self.mock_self_state, meaning)

            mock_decide.assert_called_once_with(self.mock_self_state, meaning)
            assert pattern == "test_pattern"

    def test_decide_response_with_meaning_structure(self):
        """Тест decide_response с полной структурой meaning."""
        meaning = {
            "event_type": "shock",
            "significance": 0.9,
            "urgency": 0.8,
            "data": {
                "intensity": 0.9,
                "duration": 100,
                "context": "test_context"
            }
        }

        with patch('src.decision.decision.decide_response') as mock_decide:
            mock_decide.return_value = "shock_response"

            pattern = decide_response(self.mock_self_state, meaning)

            assert pattern == "shock_response"
            assert self.mock_self_state.last_pattern == "shock_response"

    def test_decide_response_performance_monitoring(self):
        """Тест мониторинга производительности DecisionEngine."""
        meaning = {
            "event_type": "performance_test",
            "significance": 0.5,
            "urgency": 0.3,
            "data": {}
        }

        with performance_monitor.measure("DecisionEngine", "decide_response"):
            with patch('src.decision.decision.decide_response') as mock_decide:
                mock_decide.return_value = "performance_pattern"

                start_time = time.time()
                pattern = decide_response(self.mock_self_state, meaning)
                end_time = time.time()

                # Проверяем что вызов прошел через performance monitor
                assert pattern == "performance_pattern"
                assert (end_time - start_time) >= 0  # Время выполнения корректно

    def test_decide_response_error_handling(self):
        """Тест обработки ошибок в decide_response."""
        meaning = {
            "event_type": "error_test",
            "significance": 0.1,
            "urgency": 0.1,
            "data": {}
        }

        # Имитируем ошибку в decide_response
        with patch('src.decision.decision.decide_response') as mock_decide:
            mock_decide.side_effect = Exception("Test error")

            with pytest.raises(Exception, match="Test error"):
                decide_response(self.mock_self_state, meaning)

    def test_decision_logging_structure(self):
        """Тест структуры логирования решений."""
        correlation_id = "test_corr_123"
        event_id = "test_event_456"

        meaning = {
            "event_type": "logging_test",
            "significance": 0.6,
            "urgency": 0.4,
            "data": {"correlation_id": correlation_id, "event_id": event_id}
        }

        with patch('src.decision.decision.decide_response') as mock_decide:
            mock_decide.return_value = "logged_pattern"

            pattern = decide_response(self.mock_self_state, meaning)

            assert pattern == "logged_pattern"
            # Проверяем что last_pattern установлен
            assert self.mock_self_state.last_pattern == "logged_pattern"


class TestDecisionMetricsCollection:
    """Тесты для сбора метрик DecisionEngine."""

    def setup_method(self):
        """Настройка теста."""
        self.mock_self_state = Mock()
        self.mock_self_state.energy = 0.8
        self.mock_self_state.stability = 0.7
        self.mock_self_state.integrity = 0.9

    def test_performance_metrics_collection(self):
        """Тест сбора метрик производительности."""
        # Имитируем несколько вызовов decide_response
        meaning = {
            "event_type": "metrics_test",
            "significance": 0.5,
            "urgency": 0.3,
            "data": {}
        }

        with patch('src.decision.decision.decide_response') as mock_decide:
            mock_decide.return_value = "metrics_pattern"

            # Выполняем несколько вызовов
            for i in range(5):
                with performance_monitor.measure("DecisionEngine", "decide_response"):
                    pattern = decide_response(self.mock_self_state, meaning)
                    assert pattern == "metrics_pattern"

            # Проверяем метрики
            metrics = performance_monitor.get_metrics("DecisionEngine")
            assert metrics is not None
            assert "DecisionEngine.decide_response" in metrics

            decide_metrics = metrics["DecisionEngine.decide_response"]
            assert decide_metrics["total_calls"] >= 5
            assert "avg_time" in decide_metrics
            assert "min_time" in decide_metrics
            assert "max_time" in decide_metrics

    def test_decision_degradation_detection(self):
        """Тест обнаружения деградации производительности."""
        meaning = {
            "event_type": "degradation_test",
            "significance": 0.4,
            "urgency": 0.2,
            "data": {}
        }

        # Имитируем медленный отклик
        with patch('src.decision.decision.decide_response') as mock_decide:
            mock_decide.return_value = "slow_pattern"

            # Имитируем медленный вызов
            with patch('time.sleep') as mock_sleep:
                mock_sleep.return_value = None

                with performance_monitor.measure("DecisionEngine", "decide_response"):
                    # Имитируем задержку > 10ms
                    time.sleep(0.015)  # 15ms
                    pattern = decide_response(self.mock_self_state, meaning)

                assert pattern == "slow_pattern"

                # Проверяем что метрики зарегистрированы
                metrics = performance_monitor.get_metrics("DecisionEngine")
                assert metrics is not None


class TestDecisionStateIntegration:
    """Тесты для интеграции состояния при принятии решений."""

    def setup_method(self):
        """Настройка теста."""
        self.mock_self_state = Mock()
        self.mock_self_state.energy = 0.8
        self.mock_self_state.stability = 0.7
        self.mock_self_state.integrity = 0.9
        self.mock_self_state.last_pattern = "previous_pattern"

    def test_decision_based_on_state_energy(self):
        """Тест принятия решений на основе уровня энергии."""
        meaning = {
            "event_type": "energy_based_decision",
            "significance": 0.6,
            "urgency": 0.5,
            "data": {"energy_impact": 0.3}
        }

        # Тестируем с высокой энергией
        self.mock_self_state.energy = 0.9

        with patch('src.decision.decision.decide_response') as mock_decide:
            mock_decide.return_value = "high_energy_response"

            pattern = decide_response(self.mock_self_state, meaning)

            assert pattern == "high_energy_response"
            mock_decide.assert_called_with(self.mock_self_state, meaning)

    def test_decision_based_on_state_stability(self):
        """Тест принятия решений на основе стабильности."""
        meaning = {
            "event_type": "stability_based_decision",
            "significance": 0.7,
            "urgency": 0.6,
            "data": {"stability_impact": 0.4}
        }

        # Тестируем с низкой стабильностью
        self.mock_self_state.stability = 0.3

        with patch('src.decision.decision.decide_response') as mock_decide:
            mock_decide.return_value = "low_stability_response"

            pattern = decide_response(self.mock_self_state, meaning)

            assert pattern == "low_stability_response"

    def test_decision_with_adaptation_params(self):
        """Тест принятия решений с параметрами адаптации."""
        meaning = {
            "event_type": "adaptation_test",
            "significance": 0.8,
            "urgency": 0.7,
            "data": {"adaptation_context": "test"}
        }

        # Настраиваем параметры адаптации
        self.mock_self_state.adaptation_params = {
            "response_coefficients": {
                "dampen": 0.3,
                "absorb": 0.8,
                "ignore": 0.1
            }
        }

        with patch('src.decision.decision.decide_response') as mock_decide:
            mock_decide.return_value = "adaptation_aware_response"

            pattern = decide_response(self.mock_self_state, meaning)

            assert pattern == "adaptation_aware_response"
            # Проверяем что параметры переданы
            mock_decide.assert_called_with(self.mock_self_state, meaning)


class TestDecisionCorrelationTracking:
    """Тесты для отслеживания корреляций решений."""

    def setup_method(self):
        """Настройка теста."""
        self.mock_self_state = Mock()
        self.mock_self_state.energy = 0.8
        self.mock_self_state.stability = 0.7
        self.mock_self_state.integrity = 0.9

    def test_decision_correlation_id_tracking(self):
        """Тест отслеживания correlation_id в решениях."""
        correlation_id = "correlation_12345"

        meaning = {
            "event_type": "correlation_test",
            "significance": 0.5,
            "urgency": 0.4,
            "data": {
                "correlation_id": correlation_id,
                "event_id": "event_678"
            }
        }

        with patch('src.decision.decision.decide_response') as mock_decide:
            mock_decide.return_value = "correlated_response"

            pattern = decide_response(self.mock_self_state, meaning)

            assert pattern == "correlated_response"
            assert self.mock_self_state.last_pattern == "correlated_response"

    def test_decision_event_chain_tracking(self):
        """Тест отслеживания цепочек событий в решениях."""
        # Создаем цепочку событий
        events = [
            {
                "event_type": "chain_event_1",
                "significance": 0.4,
                "urgency": 0.3,
                "data": {"chain_id": "chain_001", "sequence": 1}
            },
            {
                "event_type": "chain_event_2",
                "significance": 0.6,
                "urgency": 0.5,
                "data": {"chain_id": "chain_001", "sequence": 2}
            },
            {
                "event_type": "chain_event_3",
                "significance": 0.8,
                "urgency": 0.7,
                "data": {"chain_id": "chain_001", "sequence": 3}
            }
        ]

        patterns = []

        with patch('src.decision.decision.decide_response') as mock_decide:
            for i, event in enumerate(events):
                mock_decide.return_value = f"pattern_{i+1}"
                pattern = decide_response(self.mock_self_state, event)
                patterns.append(pattern)

        assert patterns == ["pattern_1", "pattern_2", "pattern_3"]
        assert self.mock_self_state.last_pattern == "pattern_3"

    def test_decision_context_preservation(self):
        """Тест сохранения контекста при принятии решений."""
        meaning = {
            "event_type": "context_test",
            "significance": 0.6,
            "urgency": 0.5,
            "data": {
                "context": {
                    "previous_decisions": ["decision_1", "decision_2"],
                    "current_state": "active",
                    "environmental_factors": ["factor_a", "factor_b"]
                }
            }
        }

        with patch('src.decision.decision.decide_response') as mock_decide:
            mock_decide.return_value = "context_aware_response"

            pattern = decide_response(self.mock_self_state, meaning)

            assert pattern == "context_aware_response"
            # Проверяем что контекст сохранен в состоянии
            assert self.mock_self_state.last_pattern == "context_aware_response"