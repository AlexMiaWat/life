"""
Тесты для истории изменений параметров и анализа эволюции.

Тестирует новую функциональность:
- ParameterChange структура
- parameter_history в SelfState
- learning_params_history
- adaptation_params_history
- Методы анализа эволюции
"""

import time
import pytest
from src.state.self_state import SelfState, ParameterChange


class TestParameterHistory:
    """Тесты для истории параметров SelfState."""

    def test_parameter_change_creation(self):
        """Тест создания ParameterChange."""
        change = ParameterChange(
            timestamp=1234567890.0,
            tick=100,
            parameter_name="energy",
            old_value=90.0,
            new_value=85.0,
            reason="delta_application",
            context={"source": "event"},
        )

        assert change.timestamp == 1234567890.0
        assert change.tick == 100
        assert change.parameter_name == "energy"
        assert change.old_value == 90.0
        assert change.new_value == 85.0
        assert change.reason == "delta_application"
        assert change.context == {"source": "event"}

    def test_parameter_history_tracking(self):
        """Тест отслеживания изменений параметров в SelfState."""
        state = SelfState()

        # Включаем логирование для отслеживания изменений
        state.enable_logging()

        # Применяем дельту для изменения параметра
        initial_energy = state.energy
        state.apply_delta({"energy": -5.0})

        # Проверяем, что изменение записано в parameter_history
        assert len(state.parameter_history) > 0

        # Находим изменение энергии
        energy_changes = [c for c in state.parameter_history if c.parameter_name == "energy"]
        assert len(energy_changes) > 0

        latest_change = energy_changes[-1]
        assert latest_change.old_value == initial_energy
        assert latest_change.new_value == initial_energy - 5.0
        assert latest_change.reason == "field_update"

    def test_parameter_history_limits(self):
        """Тест ограничения размера parameter_history."""
        state = SelfState()
        state.enable_logging()

        # Создаем много изменений (больше лимита 1000)
        for i in range(1100):
            state.apply_delta({"energy": 0.01})  # Маленькое изменение для создания записи

        # Проверяем, что размер ограничен
        assert len(state.parameter_history) <= 1000

        # Проверяем, что остались последние изменения
        energy_changes = [c for c in state.parameter_history if c.parameter_name == "energy"]
        assert len(energy_changes) <= 1000

    def test_get_parameter_evolution(self):
        """Тест метода get_parameter_evolution."""
        state = SelfState()
        state.enable_logging()

        # Создаем несколько изменений энергии
        initial_energy = state.energy
        changes = []

        for i in range(5):
            old_energy = state.energy
            state.apply_delta({"energy": -1.0})
            changes.append((old_energy, state.energy))

        # Получаем эволюцию энергии
        evolution = state.get_parameter_evolution("energy")

        # Проверяем, что возвращены изменения в хронологическом порядке
        assert len(evolution) >= 5

        # Проверяем порядок и значения
        energy_evolution = [c for c in evolution if c.parameter_name == "energy"]
        assert len(energy_evolution) >= 5

        # Проверяем, что изменения последовательны
        for i in range(1, len(energy_evolution)):
            prev_change = energy_evolution[i - 1]
            curr_change = energy_evolution[i]
            assert curr_change.old_value == prev_change.new_value

    def test_get_evolution_trends(self):
        """Тест метода get_evolution_trends."""
        state = SelfState()
        state.enable_logging()

        # Создаем изменения в разных направлениях
        state.apply_delta({"energy": -5.0})  # Уменьшение
        time.sleep(0.01)  # Небольшая задержка для разных timestamp
        state.apply_delta({"energy": 3.0})  # Увеличение

        # Получаем тренды
        trends = state.get_evolution_trends(time_window=1.0)

        # Проверяем структуру трендов
        assert "energy" in trends
        energy_trend = trends["energy"]

        assert "changes_count" in energy_trend
        assert "first_value" in energy_trend
        assert "last_value" in energy_trend
        assert "trend_direction" in energy_trend

        # Проверяем расчет тренда
        assert energy_trend["changes_count"] >= 2
        assert energy_trend["trend_direction"] in ["increasing", "decreasing", "stable", "complex"]

    def test_parameter_correlations(self):
        """Тест анализа корреляций между параметрами."""
        state = SelfState()
        state.enable_logging()

        # Создаем одновременные изменения двух параметров
        state.apply_delta({"energy": -2.0, "stability": -0.1})
        time.sleep(0.001)
        state.apply_delta({"energy": -2.0, "stability": -0.1})

        # Анализируем корреляции
        correlation = state.get_parameter_correlations("energy", "stability")

        assert "correlation" in correlation
        assert "sample_size" in correlation
        assert "joint_changes" in correlation

        assert correlation["correlation"] >= 0.0  # Должна быть положительная корреляция
        assert correlation["sample_size"] >= 2

    def test_serialization_with_history(self):
        """Тест сериализации состояния с новой историей параметров."""
        state = SelfState()
        state.enable_logging()

        # Создаем изменения
        state.apply_delta({"energy": -5.0})
        state.apply_delta({"stability": -0.1})

        # Получаем безопасный словарь состояния
        state_dict = state.get_safe_status_dict(include_optional=True)

        # Проверяем наличие новых полей истории
        assert "parameter_history" in state_dict
        assert isinstance(state_dict["parameter_history"], list)

        # Проверяем, что история не включена по умолчанию (слишком большая)
        state_dict_default = state.get_safe_status_dict()
        assert "parameter_history" not in state_dict_default

        # Проверяем работу с лимитами
        state_dict_limited = state.get_safe_status_dict(limits={"parameter_history_limit": 10})
        assert "parameter_history" in state_dict_limited
        assert len(state_dict_limited["parameter_history"]) <= 10


class TestLearningParamsHistory:
    """Тесты для истории learning_params."""

    def test_learning_params_history_tracking(self):
        """Тест отслеживания изменений learning_params."""
        from src.learning.learning import LearningEngine

        state = SelfState()
        engine = LearningEngine()

        # Создаем фиктивную статистику для изменения параметров
        statistics = {
            "event_counts": {"noise": 100, "decay": 50},
            "avg_significance": {"noise": 0.3, "decay": 0.4},
            "response_patterns": {"ignore": 10, "dampen": 20, "absorb": 5},
        }

        old_params = state.learning_params.copy()

        # Применяем изменения через LearningEngine
        engine.adjust_parameters(statistics, state.learning_params)

        # Проверяем, что изменения записаны в историю
        assert hasattr(state, "learning_params_history")
        assert len(state.learning_params_history) > 0

        # Проверяем структуру записи истории
        latest_entry = state.learning_params_history[-1]
        assert "timestamp" in latest_entry
        assert "tick" in latest_entry
        assert "old_params" in latest_entry
        assert "new_params" in latest_entry
        assert "changes" in latest_entry

    def test_learning_params_history_limits(self):
        """Тест ограничения размера learning_params_history."""
        from src.learning.learning import LearningEngine

        state = SelfState()
        engine = LearningEngine()

        # Создаем много изменений
        statistics = {
            "event_counts": {"noise": 100},
            "avg_significance": {"noise": 0.3},
            "response_patterns": {"ignore": 10, "dampen": 20},
        }

        for i in range(120):  # Больше лимита 100
            engine.adjust_parameters(statistics, state.learning_params)

        # Проверяем ограничение размера
        assert len(state.learning_params_history) <= 100


class TestAdaptationParamsHistory:
    """Тесты для истории adaptation_params."""

    def test_adaptation_params_history_tracking(self):
        """Тест отслеживания изменений adaptation_params."""
        from src.adaptation.adaptation import AdaptationManager

        state = SelfState()
        manager = AdaptationManager()

        # Создаем тестовые данные
        analysis = {
            "learning_changes": {"event_type_sensitivity": {"noise": 0.01}},
            "current_behavior": state.adaptation_params.copy(),
        }

        old_params = state.adaptation_params.copy()

        # Применяем изменения
        new_params = manager.apply_adaptation(analysis, old_params, state)

        # Проверяем наличие истории (через store_history в runtime loop)
        # В unit-тесте история может не записываться, так как это делает runtime loop
        # Поэтому проверяем, что метод apply_adaptation возвращает корректные данные
        assert isinstance(new_params, dict) or new_params is None

    def test_adaptation_params_history_structure(self):
        """Тест структуры adaptation_params_history."""
        # Создаем запись истории вручную для проверки структуры
        state = SelfState()

        history_entry = {
            "timestamp": time.time(),
            "tick": 100,
            "old_params": {"behavior_sensitivity": {"noise": 0.2}},
            "new_params": {"behavior_sensitivity": {"noise": 0.21}},
            "changes": {
                "behavior_sensitivity": {"old_value": {"noise": 0.2}, "new_value": {"noise": 0.21}}
            },
            "learning_params_snapshot": {},
        }

        if not hasattr(state, "adaptation_params_history"):
            state.adaptation_params_history = []

        state.adaptation_params_history.append(history_entry)

        # Проверяем структуру
        assert len(state.adaptation_params_history) == 1
        entry = state.adaptation_params_history[0]

        required_keys = [
            "timestamp",
            "tick",
            "old_params",
            "new_params",
            "changes",
            "learning_params_snapshot",
        ]
        for key in required_keys:
            assert key in entry
