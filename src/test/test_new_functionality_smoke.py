"""
Дымовые тесты для новой функциональности (Learning, Adaptation, MeaningEngine)

Проверяем:
- Базовую работоспособность без падений
- Создание экземпляров классов
- Вызов основных методов с минимальными данными
- Обработку пустых/минимальных входных данных
- Граничные значения параметров
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest

from src.learning.learning import LearningEngine
from src.adaptation.adaptation import AdaptationManager
from src.meaning.engine import MeaningEngine
from src.meaning.meaning import Meaning
from src.state.self_state import SelfState
from src.memory.memory import MemoryEntry
from environment.event import Event


@pytest.mark.smoke
class TestNewFunctionalitySmoke:
    """Дымовые тесты для новой функциональности"""

    # ============================================================================
    # Learning Engine Smoke Tests
    # ============================================================================

    def test_learning_engine_instantiation(self):
        """Тест создания экземпляра LearningEngine"""
        engine = LearningEngine()
        assert engine is not None
        assert isinstance(engine, LearningEngine)

    def test_learning_process_statistics_empty_memory(self):
        """Дымовой тест process_statistics с пустой памятью"""
        engine = LearningEngine()
        result = engine.process_statistics([])

        assert isinstance(result, dict)
        assert "total_entries" in result
        assert "feedback_entries" in result
        assert "event_type_counts" in result
        assert result["total_entries"] == 0

    def test_learning_adjust_parameters_empty_data(self):
        """Дымовой тест adjust_parameters с пустыми данными"""
        engine = LearningEngine()
        statistics = {
            "event_type_counts": {},
            "event_type_total_significance": {},
            "feedback_pattern_counts": {},
            "feedback_state_deltas": {"energy": [], "stability": [], "integrity": []},
            "total_entries": 0,
            "feedback_entries": 0,
        }
        current_params = {
            "event_type_sensitivity": {"noise": 0.2},
            "significance_thresholds": {},
            "response_coefficients": {},
        }

        result = engine.adjust_parameters(statistics, current_params)
        assert isinstance(result, dict)

    def test_learning_record_changes_empty_params(self):
        """Дымовой тест record_changes с пустыми параметрами"""
        engine = LearningEngine()
        self_state = SelfState()
        old_params = self_state.learning_params.copy()
        new_params = {}

        # Не должно вызывать исключений
        engine.record_changes(old_params, new_params, self_state)
        assert True  # Если дошли сюда, значит исключений не было

    def test_learning_full_cycle_empty_data(self):
        """Дымовой тест полного цикла Learning с пустыми данными"""
        engine = LearningEngine()
        self_state = SelfState()

        # Полный цикл
        statistics = engine.process_statistics(self_state.memory)
        new_params = engine.adjust_parameters(statistics, self_state.learning_params)
        if new_params:
            engine.record_changes(self_state.learning_params, new_params, self_state)

        # Проверяем, что все прошло без ошибок
        assert "learning_params" in self_state.learning_params

    def test_learning_minimal_memory(self):
        """Дымовой тест с минимальной памятью"""
        engine = LearningEngine()
        self_state = SelfState()

        # Добавляем минимальную запись
        self_state.memory.append(
            MemoryEntry(event_type="noise", meaning_significance=0.3, timestamp=1.0)
        )

        statistics = engine.process_statistics(self_state.memory)
        assert statistics["total_entries"] == 1
        assert statistics["event_type_counts"]["noise"] == 1

        new_params = engine.adjust_parameters(statistics, self_state.learning_params)
        assert isinstance(new_params, dict)

    def test_learning_boundary_values(self):
        """Дымовой тест граничных значений"""
        engine = LearningEngine()
        self_state = SelfState()

        # Параметры на границах
        self_state.learning_params["event_type_sensitivity"]["noise"] = 0.0
        self_state.learning_params["event_type_sensitivity"]["decay"] = 1.0

        statistics = {
            "event_type_counts": {"noise": 100, "decay": 1},
            "event_type_total_significance": {"noise": 50.0, "decay": 0.1},
            "feedback_pattern_counts": {},
            "feedback_state_deltas": {"energy": [], "stability": [], "integrity": []},
            "total_entries": 101,
            "feedback_entries": 0,
        }

        new_params = engine.adjust_parameters(statistics, self_state.learning_params)
        assert isinstance(new_params, dict)

        # Проверяем, что значения остались в границах
        if "event_type_sensitivity" in new_params:
            for key, value in new_params["event_type_sensitivity"].items():
                assert 0.0 <= value <= 1.0, f"Значение {key}={value} вне границ [0, 1]"

    def test_learning_with_feedback_data(self):
        """Дымовой тест с данными Feedback"""
        engine = LearningEngine()
        self_state = SelfState()

        # Добавляем Feedback запись
        self_state.memory.append(
            MemoryEntry(
                event_type="feedback",
                meaning_significance=0.0,
                timestamp=1.0,
                feedback_data={
                    "action_id": "action_1",
                    "action_pattern": "dampen",
                    "state_delta": {"energy": -0.1, "stability": -0.05, "integrity": 0.0},
                    "delay_ticks": 5,
                    "associated_events": [],
                },
            )
        )

        statistics = engine.process_statistics(self_state.memory)
        assert statistics["feedback_entries"] == 1
        assert statistics["feedback_pattern_counts"]["dampen"] == 1

        new_params = engine.adjust_parameters(statistics, self_state.learning_params)
        assert isinstance(new_params, dict)

    # ============================================================================
    # Adaptation Manager Smoke Tests
    # ============================================================================

    def test_adaptation_manager_instantiation(self):
        """Тест создания экземпляра AdaptationManager"""
        manager = AdaptationManager()
        assert manager is not None
        assert isinstance(manager, AdaptationManager)

    def test_adaptation_analyze_changes_empty_history(self):
        """Дымовой тест analyze_changes с пустой историей"""
        manager = AdaptationManager()
        learning_params = {
            "event_type_sensitivity": {"noise": 0.3, "shock": 0.5},
            "significance_thresholds": {"noise": 0.2, "shock": 0.4},
            "response_coefficients": {"dampen": 0.6, "absorb": 0.8},
        }

        result = manager.analyze_changes(learning_params, [])

        assert isinstance(result, dict)
        assert "learning_params_snapshot" in result
        assert "recent_changes" in result
        assert "change_patterns" in result
        assert result["learning_params_snapshot"] == learning_params
        assert len(result["recent_changes"]) == 0

    def test_adaptation_apply_adaptation_initialization(self):
        """Дымовой тест инициализации параметров поведения"""
        manager = AdaptationManager()
        self_state = SelfState()
        self_state.learning_params = {
            "event_type_sensitivity": {"noise": 0.3, "shock": 0.5},
            "significance_thresholds": {"noise": 0.2, "shock": 0.4},
            "response_coefficients": {"dampen": 0.6, "absorb": 0.8},
        }

        analysis = {"learning_params_snapshot": self_state.learning_params}
        current_params = {}

        result = manager.apply_adaptation(analysis, current_params, self_state)

        assert isinstance(result, dict)
        assert "behavior_sensitivity" in result
        assert "behavior_thresholds" in result
        assert "behavior_coefficients" in result

    def test_adaptation_store_history_empty_params(self):
        """Дымовой тест store_history с пустыми параметрами"""
        manager = AdaptationManager()
        self_state = SelfState()

        old_params = {
            "behavior_sensitivity": {"noise": 0.2},
        }

        new_params = {
            "behavior_sensitivity": {"noise": 0.21},
        }

        # Не должно вызывать исключений
        manager.store_history(old_params, new_params, self_state)
        assert True  # Если дошли сюда, значит исключений не было

    def test_adaptation_full_cycle_minimal_data(self):
        """Дымовой тест полного цикла Adaptation с минимальными данными"""
        manager = AdaptationManager()
        self_state = SelfState()
        self_state.learning_params = {
            "event_type_sensitivity": {"noise": 0.2},
        }

        # Полный цикл
        analysis = manager.analyze_changes(
            self_state.learning_params, getattr(self_state, "adaptation_history", [])
        )
        current_params = {}
        new_params = manager.apply_adaptation(analysis, current_params, self_state)
        manager.store_history(current_params, new_params, self_state)

        # Проверяем, что все прошло без ошибок
        assert hasattr(self_state, "adaptation_history")
        assert len(self_state.adaptation_history) >= 0

    def test_adaptation_boundary_values(self):
        """Дымовой тест граничных значений в Adaptation"""
        manager = AdaptationManager()
        self_state = SelfState()
        self_state.learning_params = {
            "event_type_sensitivity": {"noise": 1.5},  # Превышает границу
        }

        analysis = {"learning_params_snapshot": self_state.learning_params}
        current_params = {
            "behavior_sensitivity": {"noise": 0.9},
        }

        result = manager.apply_adaptation(analysis, current_params, self_state)
        assert isinstance(result, dict)

        # Проверяем, что значения остались в границах
        if "behavior_sensitivity" in result:
            for key, value in result["behavior_sensitivity"].items():
                assert 0.0 <= value <= 1.0, f"Значение {key}={value} вне границ [0, 1]"

    def test_adaptation_with_existing_params(self):
        """Дымовой тест с существующими параметрами поведения"""
        manager = AdaptationManager()
        self_state = SelfState()
        self_state.learning_params = {
            "event_type_sensitivity": {"noise": 0.5},
        }

        current_params = {
            "behavior_sensitivity": {"noise": 0.2},
            "behavior_thresholds": {"noise": 0.1},
            "behavior_coefficients": {"dampen": 0.3},
        }

        analysis = {"learning_params_snapshot": self_state.learning_params}
        result = manager.apply_adaptation(analysis, current_params, self_state)

        assert isinstance(result, dict)
        # Параметры должны измениться медленно
        if "behavior_sensitivity" in result:
            old_value = current_params["behavior_sensitivity"]["noise"]
            new_value = result["behavior_sensitivity"]["noise"]
            delta = abs(new_value - old_value)
            assert delta <= manager.MAX_ADAPTATION_DELTA + 0.001

    # ============================================================================
    # Meaning Engine Smoke Tests
    # ============================================================================

    def test_meaning_engine_instantiation(self):
        """Тест создания экземпляра MeaningEngine"""
        engine = MeaningEngine()
        assert engine is not None
        assert isinstance(engine, MeaningEngine)

    def test_meaning_appraisal_basic_event(self):
        """Дымовой тест appraisal с базовым событием"""
        engine = MeaningEngine()
        event = Event(type="noise", intensity=0.5, timestamp=1.0)
        self_state = {"energy": 100.0, "stability": 1.0, "integrity": 1.0}

        result = engine.appraisal(event, self_state)
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0

    def test_meaning_impact_model_basic_event(self):
        """Дымовой тест impact_model с базовым событием"""
        engine = MeaningEngine()
        event = Event(type="noise", intensity=0.5, timestamp=1.0)
        self_state = {"energy": 100.0, "stability": 1.0, "integrity": 1.0}
        significance = 0.5

        result = engine.impact_model(event, self_state, significance)
        assert isinstance(result, dict)
        assert "energy" in result
        assert "stability" in result
        assert "integrity" in result
        assert all(isinstance(v, (int, float)) for v in result.values())

    def test_meaning_response_pattern_basic_event(self):
        """Дымовой тест response_pattern с базовым событием"""
        engine = MeaningEngine()
        event = Event(type="noise", intensity=0.5, timestamp=1.0)
        self_state = {"energy": 100.0, "stability": 1.0, "integrity": 1.0}
        significance = 0.5

        result = engine.response_pattern(event, self_state, significance)
        assert isinstance(result, str)
        assert result in ["ignore", "absorb", "dampen", "amplify"]

    def test_meaning_process_basic_event(self):
        """Дымовой тест process с базовым событием"""
        engine = MeaningEngine()
        event = Event(type="noise", intensity=0.5, timestamp=1.0)
        self_state = {"energy": 100.0, "stability": 1.0, "integrity": 1.0}

        result = engine.process(event, self_state)
        assert isinstance(result, Meaning)
        assert hasattr(result, "event_id")
        assert hasattr(result, "significance")
        assert hasattr(result, "impact")
        assert isinstance(result.significance, (int, float))
        assert isinstance(result.impact, dict)

    def test_meaning_engine_different_event_types(self):
        """Дымовой тест с разными типами событий"""
        engine = MeaningEngine()
        self_state = {"energy": 100.0, "stability": 1.0, "integrity": 1.0}

        event_types = ["noise", "shock", "recovery", "decay", "idle"]

        for event_type in event_types:
            event = Event(type=event_type, intensity=0.5, timestamp=1.0)

            # Все методы должны работать без ошибок
            significance = engine.appraisal(event, self_state)
            assert isinstance(significance, (int, float))

            impact = engine.impact_model(event, self_state, significance)
            assert isinstance(impact, dict)

            pattern = engine.response_pattern(event, self_state, significance)
            assert isinstance(pattern, str)

            meaning = engine.process(event, self_state)
            assert isinstance(meaning, Meaning)

    def test_meaning_engine_boundary_intensity(self):
        """Дымовой тест с граничными значениями интенсивности"""
        engine = MeaningEngine()
        self_state = {"energy": 100.0, "stability": 1.0, "integrity": 1.0}

        # Тестируем с разными интенсивностями
        for intensity in [0.0, 0.1, 0.5, 1.0, -1.0]:
            event = Event(type="noise", intensity=intensity, timestamp=1.0)

            significance = engine.appraisal(event, self_state)
            assert isinstance(significance, (int, float))
            assert 0.0 <= significance <= 1.0

            meaning = engine.process(event, self_state)
            assert isinstance(meaning, Meaning)

    def test_meaning_engine_boundary_state(self):
        """Дымовой тест с граничными значениями состояния"""
        engine = MeaningEngine()
        event = Event(type="noise", intensity=0.5, timestamp=1.0)

        # Тестируем с разными состояниями
        test_states = [
            {"energy": 0.0, "stability": 0.0, "integrity": 0.0},  # Минимальные
            {"energy": 50.0, "stability": 0.5, "integrity": 0.5},  # Средние
            {"energy": 100.0, "stability": 1.0, "integrity": 1.0},  # Максимальные
        ]

        for self_state in test_states:
            significance = engine.appraisal(event, self_state)
            assert isinstance(significance, (int, float))
            assert 0.0 <= significance <= 1.0

            meaning = engine.process(event, self_state)
            assert isinstance(meaning, Meaning)

    def test_meaning_engine_low_significance_ignore(self):
        """Дымовой тест игнорирования событий с низкой значимостью"""
        engine = MeaningEngine()
        event = Event(type="idle", intensity=0.01, timestamp=1.0)  # Низкая интенсивность
        self_state = {"energy": 100.0, "stability": 1.0, "integrity": 1.0}

        meaning = engine.process(event, self_state)

        # Событие с низкой значимостью должно игнорироваться
        if meaning.significance < engine.base_significance_threshold:
            assert all(v == 0.0 for v in meaning.impact.values())

    # ============================================================================
    # Cross-Module Smoke Tests
    # ============================================================================

    def test_learning_adaptation_integration_smoke(self):
        """Дымовой тест интеграции Learning и Adaptation"""
        learning_engine = LearningEngine()
        adaptation_manager = AdaptationManager()
        self_state = SelfState()

        # Добавляем данные для Learning
        self_state.memory.append(
            MemoryEntry(event_type="noise", meaning_significance=0.4, timestamp=1.0)
        )

        # Learning цикл
        statistics = learning_engine.process_statistics(self_state.memory)
        new_learning_params = learning_engine.adjust_parameters(
            statistics, self_state.learning_params
        )
        if new_learning_params:
            learning_engine.record_changes(
                self_state.learning_params, new_learning_params, self_state
            )

        # Adaptation цикл
        analysis = adaptation_manager.analyze_changes(
            self_state.learning_params, getattr(self_state, "adaptation_history", [])
        )
        current_behavior_params = {}
        new_behavior_params = adaptation_manager.apply_adaptation(
            analysis, current_behavior_params, self_state
        )
        adaptation_manager.store_history(
            current_behavior_params, new_behavior_params, self_state
        )

        # Проверяем, что все прошло без ошибок
        assert "learning_params" in self_state.learning_params
        assert hasattr(self_state, "adaptation_history")

    def test_meaning_learning_integration_smoke(self):
        """Дымовой тест интеграции Meaning и Learning"""
        meaning_engine = MeaningEngine()
        learning_engine = LearningEngine()
        self_state = SelfState()

        # Создаем событие и получаем Meaning
        event = Event(type="noise", intensity=0.6, timestamp=1.0)
        meaning = meaning_engine.process(event, self_state.__dict__)

        # Сохраняем в Memory для Learning
        if meaning.significance > 0:
            self_state.memory.append(
                MemoryEntry(
                    event_type=event.type,
                    meaning_significance=meaning.significance,
                    timestamp=event.timestamp,
                )
            )

        # Learning обрабатывает данные
        statistics = learning_engine.process_statistics(self_state.memory)
        new_params = learning_engine.adjust_parameters(
            statistics, self_state.learning_params
        )

        # Проверяем, что все прошло без ошибок
        assert statistics["total_entries"] >= 0
        assert isinstance(new_params, dict)

    def test_full_chain_smoke(self):
        """Дымовой тест полной цепочки: Meaning -> Learning -> Adaptation"""
        meaning_engine = MeaningEngine()
        learning_engine = LearningEngine()
        adaptation_manager = AdaptationManager()
        self_state = SelfState()

        # 1. Meaning обрабатывает событие
        event = Event(type="shock", intensity=-0.8, timestamp=1.0)
        meaning = meaning_engine.process(event, self_state.__dict__)

        # 2. Сохраняем результат в Memory
        self_state.memory.append(
            MemoryEntry(
                event_type=event.type,
                meaning_significance=meaning.significance,
                timestamp=event.timestamp,
            )
        )

        # 3. Learning анализирует статистику
        statistics = learning_engine.process_statistics(self_state.memory)
        new_learning_params = learning_engine.adjust_parameters(
            statistics, self_state.learning_params
        )
        if new_learning_params:
            learning_engine.record_changes(
                self_state.learning_params, new_learning_params, self_state
            )

        # 4. Adaptation реагирует на изменения Learning
        analysis = adaptation_manager.analyze_changes(
            self_state.learning_params, getattr(self_state, "adaptation_history", [])
        )
        current_behavior_params = {}
        new_behavior_params = adaptation_manager.apply_adaptation(
            analysis, current_behavior_params, self_state
        )
        adaptation_manager.store_history(
            current_behavior_params, new_behavior_params, self_state
        )

        # Проверяем, что вся цепочка работает
        assert len(self_state.memory) >= 1
        assert "learning_params" in self_state.learning_params
        assert hasattr(self_state, "adaptation_history")

    def test_all_modules_with_empty_state(self):
        """Дымовой тест всех модулей с пустым состоянием"""
        meaning_engine = MeaningEngine()
        learning_engine = LearningEngine()
        adaptation_manager = AdaptationManager()
        self_state = SelfState()

        # Все модули должны работать с пустым состоянием
        event = Event(type="idle", intensity=0.0, timestamp=1.0)
        meaning = meaning_engine.process(event, self_state.__dict__)
        assert isinstance(meaning, Meaning)

        statistics = learning_engine.process_statistics(self_state.memory)
        assert statistics["total_entries"] == 0

        new_params = learning_engine.adjust_parameters(statistics, self_state.learning_params)
        assert isinstance(new_params, dict)

        analysis = adaptation_manager.analyze_changes(
            self_state.learning_params, getattr(self_state, "adaptation_history", [])
        )
        assert isinstance(analysis, dict)

        behavior_params = adaptation_manager.apply_adaptation(
            analysis, {}, self_state
        )
        assert isinstance(behavior_params, dict)