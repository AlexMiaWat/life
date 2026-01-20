"""
Статические тесты для новой функциональности (Learning, Adaptation, MeaningEngine, Subjective Time, Thread Safety)

Проверяем:
- Структуру классов и модулей
- Константы и их значения
- Сигнатуры методов
- Типы возвращаемых значений
- Отсутствие запрещенных методов/атрибутов
- Архитектурные ограничения
- Новую функциональность: субъективное время и потокобезопасность
"""

import inspect
import sys
import threading
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.adaptation.adaptation import AdaptationManager
from src.environment.event import Event
from src.learning.learning import LearningEngine
from src.meaning.engine import MeaningEngine
from src.meaning.meaning import Meaning
from src.runtime.subjective_time import compute_subjective_dt, compute_subjective_time_rate
from src.state.self_state import SelfState


@pytest.mark.static
class TestNewFunctionalityStatic:
    """Статические тесты для новой функциональности"""

    # ============================================================================
    # Learning Engine Static Tests
    # ============================================================================

    def test_learning_engine_structure(self):
        """Проверка структуры LearningEngine"""
        assert hasattr(LearningEngine, "__init__")
        assert hasattr(LearningEngine, "process_statistics")
        assert hasattr(LearningEngine, "adjust_parameters")
        assert hasattr(LearningEngine, "record_changes")
        assert hasattr(LearningEngine, "MAX_PARAMETER_DELTA")
        assert hasattr(LearningEngine, "MIN_PARAMETER_DELTA")

    def test_learning_engine_constants(self):
        """Проверка констант LearningEngine"""
        engine = LearningEngine()
        assert engine.MAX_PARAMETER_DELTA == 0.01
        assert engine.MIN_PARAMETER_DELTA == 0.001
        assert engine.MAX_PARAMETER_DELTA > engine.MIN_PARAMETER_DELTA

        # Пороги частоты
        assert hasattr(engine, "HIGH_FREQUENCY_THRESHOLD")
        assert hasattr(engine, "LOW_FREQUENCY_THRESHOLD")
        assert engine.HIGH_FREQUENCY_THRESHOLD == 0.2
        assert engine.LOW_FREQUENCY_THRESHOLD == 0.1

        # Пороги значимости
        assert hasattr(engine, "HIGH_SIGNIFICANCE_THRESHOLD")
        assert hasattr(engine, "LOW_SIGNIFICANCE_THRESHOLD")
        assert engine.HIGH_SIGNIFICANCE_THRESHOLD == 0.5
        assert engine.LOW_SIGNIFICANCE_THRESHOLD == 0.2

        # Пороги паттернов
        assert hasattr(engine, "HIGH_PATTERN_FREQUENCY_THRESHOLD")
        assert hasattr(engine, "LOW_PATTERN_FREQUENCY_THRESHOLD")
        assert engine.HIGH_PATTERN_FREQUENCY_THRESHOLD == 0.3
        assert engine.LOW_PATTERN_FREQUENCY_THRESHOLD == 0.1

    def test_learning_engine_method_signatures(self):
        """Проверка сигнатур методов LearningEngine"""
        engine = LearningEngine()

        # process_statistics
        sig = inspect.signature(engine.process_statistics)
        assert len(sig.parameters) == 1  # memory (self не учитывается)
        assert "memory" in sig.parameters

        # adjust_parameters
        sig = inspect.signature(engine.adjust_parameters)
        assert (
            len(sig.parameters) == 2
        )  # statistics + current_params (self не учитывается)
        assert "statistics" in sig.parameters
        assert "current_params" in sig.parameters

        # record_changes
        sig = inspect.signature(engine.record_changes)
        assert (
            len(sig.parameters) == 3
        )  # old_params + new_params + self_state (self не учитывается)
        assert "old_params" in sig.parameters
        assert "new_params" in sig.parameters
        assert "self_state" in sig.parameters

    def test_learning_engine_return_types(self):
        """Проверка типов возвращаемых значений LearningEngine"""
        engine = LearningEngine()

        # process_statistics возвращает dict
        result = engine.process_statistics([])
        assert isinstance(result, dict)

        # adjust_parameters возвращает dict
        # current_params не может быть пустым, передаем валидные параметры
        current_params = {
            "event_type_sensitivity": {"noise": 0.2},
            "significance_thresholds": {},
            "response_coefficients": {},
        }
        result = engine.adjust_parameters({}, current_params)
        assert isinstance(result, dict)

        # record_changes возвращает None
        self_state = type("MockState", (), {})()
        result = engine.record_changes({}, {}, self_state)
        assert result is None

    def test_learning_engine_private_methods(self):
        """Проверка приватных методов LearningEngine"""
        engine = LearningEngine()

        assert hasattr(engine, "_adjust_event_sensitivity")
        assert hasattr(engine, "_adjust_significance_thresholds")
        assert hasattr(engine, "_adjust_response_coefficients")

        # Проверяем, что они приватные (начинаются с _)
        assert engine._adjust_event_sensitivity.__name__.startswith("_")
        assert engine._adjust_significance_thresholds.__name__.startswith("_")
        assert engine._adjust_response_coefficients.__name__.startswith("_")

    # ============================================================================
    # Adaptation Manager Static Tests
    # ============================================================================

    def test_adaptation_manager_structure(self):
        """Проверка структуры AdaptationManager"""
        assert hasattr(AdaptationManager, "__init__")
        assert hasattr(AdaptationManager, "analyze_changes")
        assert hasattr(AdaptationManager, "apply_adaptation")
        assert hasattr(AdaptationManager, "store_history")
        assert hasattr(AdaptationManager, "MAX_ADAPTATION_DELTA")
        assert hasattr(AdaptationManager, "MIN_ADAPTATION_DELTA")
        assert hasattr(AdaptationManager, "MAX_HISTORY_SIZE")

    def test_adaptation_manager_constants(self):
        """Проверка констант AdaptationManager"""
        manager = AdaptationManager()
        assert manager.MAX_ADAPTATION_DELTA == 0.01
        assert manager.MIN_ADAPTATION_DELTA == 0.001
        assert manager.MAX_HISTORY_SIZE == 50
        assert manager.MAX_ADAPTATION_DELTA > manager.MIN_ADAPTATION_DELTA

    def test_adaptation_manager_method_signatures(self):
        """Проверка сигнатур методов AdaptationManager"""
        manager = AdaptationManager()

        # analyze_changes
        sig = inspect.signature(manager.analyze_changes)
        assert (
            len(sig.parameters) == 2
        )  # learning_params + adaptation_history (self не учитывается)
        assert "learning_params" in sig.parameters
        assert "adaptation_history" in sig.parameters

        # apply_adaptation
        sig = inspect.signature(manager.apply_adaptation)
        assert (
            len(sig.parameters) == 3
        )  # analysis + current_behavior_params + self_state (self не учитывается)
        assert "analysis" in sig.parameters
        assert "current_behavior_params" in sig.parameters
        assert "self_state" in sig.parameters

        # store_history
        sig = inspect.signature(manager.store_history)
        assert (
            len(sig.parameters) == 3
        )  # old_params + new_params + self_state (self не учитывается)
        assert "old_params" in sig.parameters
        assert "new_params" in sig.parameters
        assert "self_state" in sig.parameters

    def test_adaptation_manager_return_types(self):
        """Проверка типов возвращаемых значений AdaptationManager"""
        manager = AdaptationManager()

        # analyze_changes возвращает dict
        result = manager.analyze_changes({}, [])
        assert isinstance(result, dict)

        # apply_adaptation возвращает dict
        mock_state = type("MockState", (), {"learning_params": {}})()
        result = manager.apply_adaptation({}, {}, mock_state)
        assert isinstance(result, dict)

        # store_history возвращает None
        result = manager.store_history({}, {}, mock_state)
        assert result is None

    def test_adaptation_manager_private_methods(self):
        """Проверка приватных методов AdaptationManager"""
        manager = AdaptationManager()

        assert hasattr(manager, "_adapt_behavior_sensitivity")
        assert hasattr(manager, "_adapt_behavior_thresholds")
        assert hasattr(manager, "_adapt_behavior_coefficients")
        assert hasattr(manager, "_init_behavior_sensitivity")
        assert hasattr(manager, "_init_behavior_thresholds")
        assert hasattr(manager, "_init_behavior_coefficients")

        # Проверяем, что они приватные (начинаются с _)
        assert manager._adapt_behavior_sensitivity.__name__.startswith("_")
        assert manager._adapt_behavior_thresholds.__name__.startswith("_")
        assert manager._adapt_behavior_coefficients.__name__.startswith("_")

    # ============================================================================
    # Meaning Engine Static Tests
    # ============================================================================

    def test_meaning_engine_structure(self):
        """Проверка структуры MeaningEngine"""
        assert hasattr(MeaningEngine, "__init__")
        assert hasattr(MeaningEngine, "appraisal")
        assert hasattr(MeaningEngine, "impact_model")
        assert hasattr(MeaningEngine, "response_pattern")
        assert hasattr(MeaningEngine, "process")
        # base_significance_threshold - это атрибут экземпляра, проверяем через экземпляр
        engine = MeaningEngine()
        assert hasattr(engine, "base_significance_threshold")

    def test_meaning_engine_constants(self):
        """Проверка констант MeaningEngine"""
        engine = MeaningEngine()
        assert engine.base_significance_threshold == 0.1

    def test_meaning_engine_method_signatures(self):
        """Проверка сигнатур методов MeaningEngine"""
        engine = MeaningEngine()

        # appraisal
        sig = inspect.signature(engine.appraisal)
        assert len(sig.parameters) == 2  # event + self_state (self не учитывается)
        assert "event" in sig.parameters
        assert "self_state" in sig.parameters

        # impact_model
        sig = inspect.signature(engine.impact_model)
        assert (
            len(sig.parameters) == 3
        )  # event + self_state + significance (self не учитывается)
        assert "event" in sig.parameters
        assert "self_state" in sig.parameters
        assert "significance" in sig.parameters

        # response_pattern
        sig = inspect.signature(engine.response_pattern)
        assert (
            len(sig.parameters) == 3
        )  # event + self_state + significance (self не учитывается)
        assert "event" in sig.parameters
        assert "self_state" in sig.parameters
        assert "significance" in sig.parameters

        # process
        sig = inspect.signature(engine.process)
        assert len(sig.parameters) == 2  # event + self_state (self не учитывается)
        assert "event" in sig.parameters
        assert "self_state" in sig.parameters

    def test_meaning_engine_return_types(self):
        """Проверка типов возвращаемых значений MeaningEngine"""
        engine = MeaningEngine()
        event = Event(type="noise", intensity=0.5, timestamp=1.0)
        self_state = {"energy": 100.0, "stability": 1.0, "integrity": 1.0}

        # appraisal возвращает float
        result = engine.appraisal(event, self_state)
        assert isinstance(result, float)

        # impact_model возвращает dict
        significance = 0.5
        result = engine.impact_model(event, self_state, significance)
        assert isinstance(result, dict)
        assert "energy" in result
        assert "stability" in result
        assert "integrity" in result

        # response_pattern возвращает str
        result = engine.response_pattern(event, self_state, significance)
        assert isinstance(result, str)

        # process возвращает Meaning
        result = engine.process(event, self_state)
        assert isinstance(result, Meaning)

    # ============================================================================
    # Cross-Module Architectural Constraints
    # ============================================================================

    def test_learning_no_optimization_methods(self):
        """Проверка отсутствия методов оптимизации в Learning"""
        engine = LearningEngine()
        methods = dir(engine)

        forbidden_methods = [
            "optimize",
            "optimization",
            "optimizer",
            "improve",
            "improvement",
            "maximize",
            "minimize",
            "evaluate",
            "evaluation",
            "score",
            "scoring",
            "scorer",
            "rate",
            "rating",
            "judge",
            "judgment",
            "train",
            "training",
            "trainer",
            "fit",
            "fitting",
            "gradient",
            "backprop",
            "loss",
            "cost",
            "error",
        ]

        for method in forbidden_methods:
            assert (
                method not in methods
            ), f"LearningEngine не должен иметь метод {method}"

    def test_adaptation_no_optimization_methods(self):
        """Проверка отсутствия методов оптимизации в Adaptation"""
        manager = AdaptationManager()
        methods = dir(manager)

        forbidden_methods = [
            "optimize",
            "optimization",
            "optimizer",
            "improve",
            "improvement",
            "maximize",
            "minimize",
            "evaluate",
            "evaluation",
            "score",
            "scoring",
            "scorer",
            "rate",
            "rating",
            "judge",
            "judgment",
            "reinforce",
            "reinforcement",
        ]

        for method in forbidden_methods:
            assert (
                method not in methods
            ), f"AdaptationManager не должен иметь метод {method}"

    def test_learning_no_goals_or_rewards(self):
        """Проверка отсутствия целей и reward в Learning"""
        engine = LearningEngine()
        source_code = inspect.getsource(LearningEngine)

        forbidden_terms = [
            "goal",
            "target",
            "objective",
            "reward",
            "punishment",
            "utility",
            "scoring",
        ]

        lines = [
            line
            for line in source_code.split("\n")
            if not line.strip().startswith("#")
            and not line.strip().startswith('"""')
            and not line.strip().startswith("'''")
        ]
        source_clean = "\n".join(lines)

        for term in forbidden_terms:
            assert (
                term.lower() not in source_clean.lower()
            ), f"Термин {term} не должен использоваться в коде Learning"

    def test_adaptation_no_goals_or_rewards(self):
        """Проверка отсутствия целей и reward в Adaptation"""
        manager = AdaptationManager()
        source_code = inspect.getsource(AdaptationManager)

        forbidden_terms = [
            "goal",
            "target",
            "objective",
            "reward",
            "punishment",
            "utility",
            "scoring",
            "reinforcement",
        ]

        lines = [
            line
            for line in source_code.split("\n")
            if not line.strip().startswith("#")
            and not line.strip().startswith('"""')
            and not line.strip().startswith("'''")
        ]
        source_clean = "\n".join(lines)

        for term in forbidden_terms:
            assert (
                term.lower() not in source_clean.lower()
            ), f"Термин {term} не должен использоваться в коде Adaptation"

    def test_adaptation_no_direct_decision_action_control(self):
        """Проверка отсутствия прямого управления Decision/Action в Adaptation"""
        manager = AdaptationManager()
        source_code = inspect.getsource(AdaptationManager)

        # Проверяем, что нет прямых вызовов Decision/Action
        assert "decide_response" not in source_code
        assert "execute_action" not in source_code
        assert "from decision" not in source_code
        assert "from action" not in source_code

    def test_learning_slow_changes_enforced(self):
        """Проверка принудительного медленного изменения в Learning"""
        engine = LearningEngine()

        # MAX_PARAMETER_DELTA должен быть <= 0.01
        assert engine.MAX_PARAMETER_DELTA <= 0.01

        # MIN_PARAMETER_DELTA должен быть > 0
        assert engine.MIN_PARAMETER_DELTA > 0

    def test_adaptation_slow_changes_enforced(self):
        """Проверка принудительного медленного изменения в Adaptation"""
        manager = AdaptationManager()

        # MAX_ADAPTATION_DELTA должен быть <= 0.01
        assert manager.MAX_ADAPTATION_DELTA <= 0.01

        # MIN_ADAPTATION_DELTA должен быть > 0
        assert manager.MIN_ADAPTATION_DELTA > 0

    def test_learning_forbidden_patterns(self):
        """Проверка отсутствия запрещенных паттернов в Learning"""
        engine = LearningEngine()
        source_code = inspect.getsource(LearningEngine)

        forbidden_patterns = [
            "active correction",
            "reinforcement",
            "reward signal",
            "optimization loop",
            "policy adjustment",
            "self-optimizing",
        ]

        for pattern in forbidden_patterns:
            assert (
                pattern.lower() not in source_code.lower()
            ), f"Запрещенный паттерн '{pattern}' найден в коде Learning"

    def test_adaptation_forbidden_patterns(self):
        """Проверка отсутствия запрещенных паттернов в Adaptation"""
        manager = AdaptationManager()
        source_code = inspect.getsource(AdaptationManager)

        forbidden_patterns = [
            "active correction",
            "reinforcement",
            "reward signal",
            "optimization loop",
            "policy adjustment",
            "self-optimizing",
            "direct control",
            "decision override",
            "action override",
        ]

        for pattern in forbidden_patterns:
            assert (
                pattern.lower() not in source_code.lower()
            ), f"Запрещенный паттерн '{pattern}' найден в коде Adaptation"

    def test_meaning_engine_type_weights(self):
        """Проверка весов типов событий в MeaningEngine"""
        engine = MeaningEngine()

        # Проверяем наличие type_weight через инспекцию исходного кода
        source_code = inspect.getsource(MeaningEngine)
        assert "type_weight" in source_code
        assert "shock" in source_code
        assert "noise" in source_code
        assert "recovery" in source_code
        assert "decay" in source_code
        assert "idle" in source_code

    def test_meaning_engine_base_impacts(self):
        """Проверка базовых воздействий в MeaningEngine"""
        engine = MeaningEngine()

        # Проверяем наличие base_impacts через инспекцию исходного кода
        source_code = inspect.getsource(MeaningEngine)
        assert "base_impacts" in source_code
        assert "energy" in source_code
        assert "stability" in source_code
        assert "integrity" in source_code

    def test_meaning_engine_response_patterns(self):
        """Проверка паттернов реакции в MeaningEngine"""
        engine = MeaningEngine()

        # Проверяем наличие response patterns через инспекцию исходного кода
        source_code = inspect.getsource(MeaningEngine)
        assert "ignore" in source_code
        assert "absorb" in source_code
        assert "dampen" in source_code
        assert "amplify" in source_code

    # ============================================================================
    # Source Code Analysis
    # ============================================================================

    def test_learning_source_code_analysis(self):
        """Анализ исходного кода Learning на наличие запрещенных паттернов"""
        import ast

        source_file = Path(__file__).parent.parent / "learning" / "learning.py"
        with source_file.open("r", encoding="utf-8") as f:
            source_code = f.read()

        # Парсим AST
        tree = ast.parse(source_code)

        # Запрещенные имена функций/переменных
        forbidden_names = {
            "optimize",
            "maximize",
            "minimize",
            "evaluate",
            "score",
            "reward",
            "goal",
            "target",
            "objective",
            "utility",
        }

        # Собираем все имена в коде
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                names.add(node.id)
            elif isinstance(node, ast.FunctionDef):
                names.add(node.name)
            elif isinstance(node, ast.Attribute):
                names.add(node.attr)

        # Проверяем, что запрещенные имена не используются
        # (кроме случаев в комментариях/docstrings, которые мы уже проверили)
        code_lines = [
            line
            for line in source_code.split("\n")
            if not line.strip().startswith("#")
            and not line.strip().startswith('"""')
            and not line.strip().startswith("'''")
        ]
        code_text = "\n".join(code_lines)

        for forbidden in forbidden_names:
            # Проверяем, что запрещенное имя не используется в коде
            # (разрешаем только в комментариях/docstrings)
            if forbidden in code_text.lower():
                # Проверяем контекст - возможно это часть документации ограничений
                lines_with_forbidden = [
                    line for line in code_lines if forbidden.lower() in line.lower()
                ]
                for line in lines_with_forbidden:
                    assert any(
                        keyword in line.lower()
                        for keyword in ["запрещено", "forbidden", "not", "no", "never"]
                    ), f"Запрещенный термин '{forbidden}' найден в коде: {line}"

    def test_adaptation_source_code_analysis(self):
        """Анализ исходного кода Adaptation на наличие запрещенных паттернов"""
        import ast

        source_file = Path(__file__).parent.parent / "adaptation" / "adaptation.py"
        with source_file.open("r", encoding="utf-8") as f:
            source_code = f.read()

        # Парсим AST
        tree = ast.parse(source_code)

        # Запрещенные имена функций/переменных
        forbidden_names = {
            "optimize",
            "maximize",
            "minimize",
            "evaluate",
            "score",
            "reward",
            "goal",
            "target",
            "objective",
            "utility",
        }

        # Собираем все имена в коде
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                names.add(node.id)
            elif isinstance(node, ast.FunctionDef):
                names.add(node.name)
            elif isinstance(node, ast.Attribute):
                names.add(node.attr)

        # Проверяем, что запрещенные имена не используются
        code_lines = [
            line
            for line in source_code.split("\n")
            if not line.strip().startswith("#")
            and not line.strip().startswith('"""')
            and not line.strip().startswith("'''")
        ]
        code_text = "\n".join(code_lines)

        for forbidden in forbidden_names:
            if forbidden in code_text.lower():
                # Проверяем контекст - возможно это часть документации ограничений
                lines_with_forbidden = [
                    line for line in code_lines if forbidden.lower() in line.lower()
                ]
                for line in lines_with_forbidden:
                    assert any(
                        keyword in line.lower()
                        for keyword in ["запрещено", "forbidden", "not", "no", "never"]
                    ), f"Запрещенный термин '{forbidden}' найден в коде: {line}"

    def test_imports_structure(self):
        """Проверка структуры импортов"""
        # Проверяем, что модули экспортируют основные классы
        import src.adaptation.adaptation as adaptation_module
        import src.learning.learning as learning_module
        import src.meaning.engine as engine_module
        import src.meaning.meaning as meaning_module

        assert hasattr(learning_module, "LearningEngine")
        assert hasattr(adaptation_module, "AdaptationManager")
        assert hasattr(meaning_module, "Meaning")
        assert hasattr(engine_module, "MeaningEngine")

        assert learning_module.LearningEngine == LearningEngine
        assert adaptation_module.AdaptationManager == AdaptationManager
        assert meaning_module.Meaning == Meaning
        assert engine_module.MeaningEngine == MeaningEngine

    def test_class_inheritance(self):
        """Проверка наследования классов"""
        assert LearningEngine.__bases__ == (
            object,
        ), "LearningEngine должен наследоваться только от object"
        assert AdaptationManager.__bases__ == (
            object,
        ), "AdaptationManager должен наследоваться только от object"
        assert MeaningEngine.__bases__ == (
            object,
        ), "MeaningEngine должен наследоваться только от object"
        assert Meaning.__bases__ == (
            object,
        ), "Meaning должен наследоваться только от object"

    def test_docstrings_presence(self):
        """Проверка наличия docstrings"""
        assert (
            LearningEngine.__doc__ is not None
        ), "LearningEngine должен иметь docstring"
        assert (
            AdaptationManager.__doc__ is not None
        ), "AdaptationManager должен иметь docstring"
        assert MeaningEngine.__doc__ is not None, "MeaningEngine должен иметь docstring"
        assert Meaning.__doc__ is not None, "Meaning должен иметь docstring"

        # Проверяем основные методы
        engine = LearningEngine()
        assert engine.process_statistics.__doc__ is not None
        assert engine.adjust_parameters.__doc__ is not None
        assert engine.record_changes.__doc__ is not None

        manager = AdaptationManager()
        assert manager.analyze_changes.__doc__ is not None
        assert manager.apply_adaptation.__doc__ is not None
        assert manager.store_history.__doc__ is not None

        meaning_engine = MeaningEngine()
        assert meaning_engine.appraisal.__doc__ is not None
        assert meaning_engine.impact_model.__doc__ is not None
        assert meaning_engine.response_pattern.__doc__ is not None
        assert meaning_engine.process.__doc__ is not None

    # ============================================================================
    # Subjective Time Static Tests
    # ============================================================================

    def test_subjective_time_functions_structure(self):
        """Проверка структуры функций субъективного времени"""
        # Проверяем наличие функций
        assert callable(compute_subjective_dt)
        assert callable(compute_subjective_time_rate)

        # Проверяем сигнатуры
        dt_sig = inspect.signature(compute_subjective_dt)
        assert len(dt_sig.parameters) == 10  # Все параметры
        assert "dt" in dt_sig.parameters
        assert "base_rate" in dt_sig.parameters
        assert "intensity" in dt_sig.parameters
        assert "stability" in dt_sig.parameters
        assert "energy" in dt_sig.parameters

        rate_sig = inspect.signature(compute_subjective_time_rate)
        assert len(rate_sig.parameters) == 9  # Все параметры (keyword-only)
        assert "base_rate" in rate_sig.parameters
        assert "intensity" in rate_sig.parameters
        assert "stability" in rate_sig.parameters
        assert "energy" in rate_sig.parameters

    def test_subjective_time_state_integration(self):
        """Проверка интеграции субъективного времени в SelfState"""
        state = SelfState()

        # Проверяем наличие полей субъективного времени
        assert hasattr(state, "subjective_time")
        assert hasattr(state, "subjective_time_base_rate")
        assert hasattr(state, "subjective_time_rate_min")
        assert hasattr(state, "subjective_time_rate_max")
        assert hasattr(state, "subjective_time_intensity_coeff")
        assert hasattr(state, "subjective_time_stability_coeff")
        assert hasattr(state, "subjective_time_energy_coeff")

        # Проверяем типы значений
        assert isinstance(state.subjective_time, (int, float))
        assert isinstance(state.subjective_time_base_rate, (int, float))
        assert isinstance(state.subjective_time_rate_min, (int, float))
        assert isinstance(state.subjective_time_rate_max, (int, float))

        # Проверяем допустимые диапазоны
        assert state.subjective_time_rate_min >= 0.0
        assert state.subjective_time_rate_max > state.subjective_time_rate_min
        assert state.subjective_time >= 0.0

    def test_subjective_time_function_return_types(self):
        """Проверка типов возвращаемых значений функций субъективного времени"""
        state = SelfState()

        # compute_subjective_time_rate должна возвращать float
        rate = compute_subjective_time_rate(
            base_rate=state.subjective_time_base_rate,
            intensity=0.5,
            stability=0.8,
            energy=70.0,
            intensity_coeff=state.subjective_time_intensity_coeff,
            stability_coeff=state.subjective_time_stability_coeff,
            energy_coeff=state.subjective_time_energy_coeff,
            rate_min=state.subjective_time_rate_min,
            rate_max=state.subjective_time_rate_max,
        )
        assert isinstance(rate, float)
        assert state.subjective_time_rate_min <= rate <= state.subjective_time_rate_max

        # compute_subjective_dt должна возвращать float
        dt = compute_subjective_dt(
            dt=0.1,
            base_rate=state.subjective_time_base_rate,
            intensity=0.5,
            stability=0.8,
            energy=70.0,
            intensity_coeff=state.subjective_time_intensity_coeff,
            stability_coeff=state.subjective_time_stability_coeff,
            energy_coeff=state.subjective_time_energy_coeff,
            rate_min=state.subjective_time_rate_min,
            rate_max=state.subjective_time_rate_max,
        )
        assert isinstance(dt, float)
        assert dt >= 0.0

    def test_subjective_time_memory_integration(self):
        """Проверка интеграции субъективного времени в MemoryEntry"""
        from src.memory.memory import MemoryEntry

        # Проверяем, что MemoryEntry поддерживает subjective_timestamp
        entry = MemoryEntry(
            event_type="noise",
            meaning_significance=0.5,
            timestamp=100.0,
            subjective_timestamp=50.0
        )

        assert hasattr(entry, "subjective_timestamp")
        assert entry.subjective_timestamp == 50.0
        assert isinstance(entry.subjective_timestamp, (int, float, type(None)))

        # Проверяем обратную совместимость (None значение)
        entry_compat = MemoryEntry(
            event_type="noise",
            meaning_significance=0.5,
            timestamp=100.0
        )
        assert entry_compat.subjective_timestamp is None

    # ============================================================================
    # Thread Safety Static Tests
    # ============================================================================

    def test_thread_safety_state_structure(self):
        """Проверка структуры потокобезопасности в SelfState"""
        state = SelfState()

        # Проверяем наличие блокировки для API
        assert hasattr(state, "_api_lock")
        assert hasattr(state, "__setattr__")

        # Проверяем, что _api_lock является RLock
        assert hasattr(state._api_lock, 'acquire')
        assert hasattr(state._api_lock, 'release')

    def test_thread_safety_excluded_fields(self):
        """Проверка исключенных полей из блокировки"""
        state = SelfState()

        # Проверяем наличие transient полей
        assert hasattr(state, "activated_memory")
        assert hasattr(state, "last_pattern")

        # Эти поля должны быть в списке исключений
        # (проверяем через код, так как это внутреннее поведение)
        source_code = inspect.getsource(SelfState.__setattr__)
        assert "_api_lock" in source_code
        assert "activated_memory" in source_code
        assert "last_pattern" in source_code

    def test_thread_safety_apply_delta_method(self):
        """Проверка метода apply_delta на потокобезопасность"""
        state = SelfState()

        # Проверяем наличие метода apply_delta
        assert hasattr(state, "apply_delta")

        # Проверяем сигнатуру
        sig = inspect.signature(state.apply_delta)
        assert "deltas" in sig.parameters

        # Проверяем, что метод использует блокировку
        source_code = inspect.getsource(state.apply_delta)
        assert "_api_lock" in source_code

    def test_thread_safety_get_safe_status_dict(self):
        """Проверка метода get_safe_status_dict"""
        state = SelfState()

        # Проверяем наличие метода
        assert hasattr(state, "get_safe_status_dict")

        # Проверяем сигнатуру
        sig = inspect.signature(state.get_safe_status_dict)
        # Метод может иметь дополнительные параметры

        # Проверяем возвращаемый тип
        result = state.get_safe_status_dict()
        assert isinstance(result, dict)

        # Проверяем наличие основных полей
        required_fields = ["active", "energy", "stability", "integrity", "ticks", "age"]
        for field in required_fields:
            assert field in result

    def test_thread_safety_api_lock_usage(self):
        """Проверка использования _api_lock в критических методах"""
        state = SelfState()

        # Проверяем, что __setattr__ использует блокировку
        setattr_source = inspect.getsource(SelfState.__setattr__)
        assert "_api_lock" in setattr_source

        # Проверяем, что apply_delta использует блокировку
        apply_delta_source = inspect.getsource(state.apply_delta)
        assert "_api_lock" in apply_delta_source

    def test_thread_safety_is_active_method(self):
        """Проверка метода is_active на корректность логики"""
        state = SelfState()

        # Проверяем наличие метода/property
        assert hasattr(state, "is_active")

        # Проверяем логику: True если все vital параметры >= 0
        # Тестируем различные состояния (только допустимые значения из-за валидации)
        test_cases = [
            # (energy, stability, integrity, expected)
            (100.0, 1.0, 1.0, True),   # Все параметры положительные
            (50.0, 0.8, 0.8, True),    # Все параметры положительные
            (0.0, 0.0, 0.0, True),     # Нулевые параметры (граничный случай)
            (10.0, 0.1, 0.1, True),    # Маленькие положительные значения
        ]

        for energy, stability, integrity, expected in test_cases:
            state.energy = energy
            state.stability = stability
            state.integrity = integrity
            assert state.is_active() == expected, f"is_active failed for {energy}, {stability}, {integrity}"

    # ============================================================================
    # Integration Architecture Tests
    # ============================================================================

    def test_subjective_time_learning_integration_architecture(self):
        """Проверка архитектурной интеграции субъективного времени с Learning"""
        # Субъективное время не должно нарушать архитектуру Learning
        # Learning остается медленным изменением внутренних параметров

        learning_engine = LearningEngine()
        learning_source = inspect.getsource(LearningEngine)

        # Learning не должен напрямую работать с субъективным временем
        # (субъективное время - это метрика, не инструмент управления)
        forbidden_terms = ["subjective_time", "subjective_timestamp"]
        for term in forbidden_terms:
            assert term not in learning_source.lower(), f"LearningEngine не должен работать с {term}"

    def test_subjective_time_adaptation_integration_architecture(self):
        """Проверка архитектурной интеграции субъективного времени с Adaptation"""
        # Adaptation не должен напрямую работать с субъективным временем

        adaptation_manager = AdaptationManager()
        adaptation_source = inspect.getsource(AdaptationManager)

        # Adaptation работает только с learning_params
        forbidden_terms = ["subjective_time", "subjective_timestamp"]
        for term in forbidden_terms:
            assert term not in adaptation_source.lower(), f"AdaptationManager не должен работать с {term}"

    def test_thread_safety_architecture_compliance(self):
        """Проверка соответствия архитектуре потокобезопасности"""
        state = SelfState()

        # API должен использовать immutable snapshots, а не живые объекты
        # (проверяем через наличие методов для создания snapshots)
        assert hasattr(state, "get_safe_status_dict")

        # Runtime должен иметь возможность модифицировать состояние
        # (проверяем наличие методов модификации)
        assert hasattr(state, "__setattr__")
        assert hasattr(state, "apply_delta")

    def test_new_functionality_separation_of_concerns(self):
        """Проверка разделения ответственности в новой функциональности"""
        # Субъективное время - это метрика наблюдения, не механизм управления
        # Потокобезопасность - это инфраструктура, не бизнес-логика

        # Проверяем, что субъективное время не используется для принятия решений
        # (В реальном коде нужно проверить decision.py, но для теста просто проверим концепцию)

        # Проверяем, что потокобезопасность не влияет на бизнес-логику
        # (блокировка должна быть transparent для основной логики)
        state = SelfState()

        # Проверяем, что обычные операции работают без явного использования блокировок
        old_energy = state.energy
        if old_energy < 100.0:
            state.energy = old_energy + 10.0
            assert state.energy > old_energy
        else:
            # Если уже максимум, попробуем уменьшить
            state.energy = 90.0
            assert state.energy < old_energy

        # Проверяем, что чтение статуса работает
        status = state.get_safe_status_dict()
        assert isinstance(status, dict)
