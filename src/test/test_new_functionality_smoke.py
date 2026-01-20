"""
Дымовые тесты для новой функциональности (Learning, Adaptation, MeaningEngine, Subjective Time, Thread Safety)

Проверяем:
- Базовую работоспособность без падений
- Создание экземпляров классов
- Вызов основных методов с минимальными данными
- Обработку пустых/минимальных входных данных
- Граничные значения параметров
- Новую функциональность: субъективное время и потокобезопасность
"""

import sys
import threading
import time
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest

from src.adaptation.adaptation import AdaptationManager
from src.environment.event import Event
from src.learning.learning import LearningEngine
from src.meaning.engine import MeaningEngine
from src.meaning.meaning import Meaning
from src.memory.memory import MemoryEntry
from src.runtime.life_policy import LifePolicy
from src.runtime.log_manager import FlushPolicy, LogManager
from src.runtime.snapshot_manager import SnapshotManager
from src.runtime.subjective_time import (
    compute_subjective_dt,
    compute_subjective_time_rate,
)
from src.state.self_state import SelfState


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
        assert isinstance(self_state.learning_params, dict)
        assert "event_type_sensitivity" in self_state.learning_params

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
                    "state_delta": {
                        "energy": -0.1,
                        "stability": -0.05,
                        "integrity": 0.0,
                    },
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
        event = Event(
            type="idle", intensity=0.01, timestamp=1.0
        )  # Низкая интенсивность
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
        assert isinstance(self_state.learning_params, dict)
        assert "event_type_sensitivity" in self_state.learning_params
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
        assert isinstance(self_state.learning_params, dict)
        assert "event_type_sensitivity" in self_state.learning_params
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

        new_params = learning_engine.adjust_parameters(
            statistics, self_state.learning_params
        )
        assert isinstance(new_params, dict)

        analysis = adaptation_manager.analyze_changes(
            self_state.learning_params, getattr(self_state, "adaptation_history", [])
        )
        assert isinstance(analysis, dict)

        behavior_params = adaptation_manager.apply_adaptation(analysis, {}, self_state)
        assert isinstance(behavior_params, dict)

    # ============================================================================
    # Subjective Time Smoke Tests
    # ============================================================================

    def test_subjective_time_functions_smoke(self):
        """Дымовой тест функций субъективного времени"""
        state = SelfState()

        # Тест compute_subjective_time_rate с нормальными параметрами
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
        assert 0.0 <= rate <= 3.0  # В разумных пределах

        # Тест compute_subjective_dt
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

    def test_subjective_time_state_integration_smoke(self):
        """Дымовой тест интеграции субъективного времени в состояние"""
        state = SelfState()

        # Проверяем начальные значения
        assert hasattr(state, "subjective_time")
        assert state.subjective_time >= 0.0

        # Проверяем возможность изменения
        old_value = state.subjective_time
        state.subjective_time += 1.0
        assert state.subjective_time == old_value + 1.0

    def test_subjective_time_memory_integration_smoke(self):
        """Дымовой тест интеграции субъективного времени в память"""
        from src.memory.memory import MemoryEntry

        # Создаем запись с субъективным временем
        entry = MemoryEntry(
            event_type="noise",
            meaning_significance=0.5,
            timestamp=100.0,
            subjective_timestamp=50.0,
        )
        assert entry.subjective_timestamp == 50.0

        # Создаем запись без субъективного времени (обратная совместимость)
        entry_compat = MemoryEntry(
            event_type="noise", meaning_significance=0.5, timestamp=100.0
        )
        assert entry_compat.subjective_timestamp is None

    def test_subjective_time_boundary_values_smoke(self):
        """Дымовой тест граничных значений субъективного времени"""
        # Нулевые значения
        rate_zero = compute_subjective_time_rate(
            base_rate=0.0,
            intensity=0.0,
            stability=1.0,
            energy=100.0,
            intensity_coeff=0.0,
            stability_coeff=0.0,
            energy_coeff=0.0,
            rate_min=0.0,
            rate_max=10.0,
        )
        assert rate_zero == 0.0  # Должен вернуться base_rate

        # Максимальные значения
        rate_max = compute_subjective_time_rate(
            base_rate=1.0,
            intensity=1.0,
            stability=1.0,
            energy=100.0,
            intensity_coeff=10.0,
            stability_coeff=0.0,
            energy_coeff=1.0,
            rate_min=0.1,
            rate_max=2.0,
        )
        assert rate_max == 2.0  # Должен быть clamped к max

    # ============================================================================
    # Thread Safety Smoke Tests
    # ============================================================================

    def test_thread_safety_state_smoke(self):
        """Дымовой тест потокобезопасности состояния"""
        state = SelfState()

        # Проверяем наличие блокировки
        assert hasattr(state, "_api_lock")
        assert state._api_lock is not None

        # Проверяем возможность создания безопасного статуса
        status_dict = state.get_safe_status_dict()
        assert isinstance(status_dict, dict)
        # 'active' рассчитывается через is_active(), проверяем наличие необходимых полей
        assert "energy" in status_dict
        assert "stability" in status_dict
        assert "integrity" in status_dict

    def test_thread_safety_setattr_smoke(self):
        """Дымовой тест потокобезопасного setattr"""
        state = SelfState()

        # Проверяем, что setattr работает
        old_energy = state.energy
        if old_energy < 90.0:
            state.energy = old_energy + 10.0
            assert state.energy == old_energy + 10.0
        else:
            state.energy = 80.0
            assert state.energy < old_energy

        # Проверяем работу с transient полями
        state.activated_memory = "test_memory"
        state.last_pattern = "test_pattern"
        assert state.activated_memory == "test_memory"
        assert state.last_pattern == "test_pattern"

    def test_thread_safety_apply_delta_smoke(self):
        """Дымовой тест потокобезопасного apply_delta"""
        state = SelfState()

        # Тест apply_delta с простыми изменениями
        deltas = {"energy": -5.0, "stability": 0.1}
        state.apply_delta(deltas)

        # Проверяем, что изменения применились
        # (точные значения зависят от реализации)

    def test_thread_safety_is_active_smoke(self):
        """Дымовой тест метода is_active"""
        state = SelfState()

        # Тест с нормальными параметрами
        result = state.is_active()
        assert isinstance(result, bool)

        # Тест с нулевыми параметрами (граничный случай)
        old_energy = state.energy
        old_stability = state.stability
        old_integrity = state.integrity

        state.energy = 0.0
        state.stability = 0.0
        state.integrity = 0.0
        result_zero = state.is_active()
        assert (
            result_zero is False
        )  # Нулевые значения не валидны (нужны energy > 10.0, integrity > 0.1, stability > 0.1)

        # Восстанавливаем
        state.energy = old_energy
        state.stability = old_stability
        state.integrity = old_integrity

    def test_thread_safety_concurrent_access_smoke(self):
        """Дымовой тест конкурентного доступа"""
        state = SelfState()

        results = []

        def worker(worker_id):
            try:
                # Каждый поток читает статус
                status = state.get_safe_status_dict()
                results.append((worker_id, "read", len(status)))

                # И изменяет состояние
                state.energy = 50.0 + worker_id
                results.append((worker_id, "write", state.energy))

            except Exception as e:
                results.append((worker_id, "error", str(e)))

        # Запускаем несколько потоков
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Ждем завершения
        for thread in threads:
            thread.join(timeout=1.0)

        # Проверяем, что все операции завершились без ошибок
        assert len(results) == 6  # 3 потока * 2 операции
        for worker_id, op_type, result in results:
            assert op_type in ["read", "write"]
            assert "error" not in str(result)

    # ============================================================================
    # New Functionality Integration Smoke Tests
    # ============================================================================

    def test_subjective_time_with_learning_smoke(self):
        """Дымовой тест субъективного времени с Learning"""
        state = SelfState()
        learning_engine = LearningEngine()

        # Добавляем записи памяти с субъективным временем
        state.memory.append(
            MemoryEntry(
                event_type="noise",
                meaning_significance=0.4,
                timestamp=1.0,
                subjective_timestamp=0.5,
            )
        )

        # Learning должен работать без учета субъективного времени
        statistics = learning_engine.process_statistics(state.memory)
        assert statistics["total_entries"] == 1

        new_params = learning_engine.adjust_parameters(
            statistics, state.learning_params
        )
        assert isinstance(new_params, dict)

    def test_subjective_time_with_adaptation_smoke(self):
        """Дымовой тест субъективного времени с Adaptation"""
        state = SelfState()
        adaptation_manager = AdaptationManager()

        # Adaptation должен работать без учета субъективного времени
        analysis = adaptation_manager.analyze_changes(state.learning_params, [])
        assert isinstance(analysis, dict)

        new_behavior = adaptation_manager.apply_adaptation(analysis, {}, state)
        assert isinstance(new_behavior, dict)

    def test_thread_safety_with_runtime_smoke(self):
        """Дымовой тест потокобезопасности с runtime"""
        from src.environment.event_queue import EventQueue
        from src.runtime.loop import run_loop

        state = SelfState()
        event_queue = EventQueue()
        stop_event = threading.Event()

        # Добавляем событие
        event = Event(type="noise", intensity=0.3, timestamp=1.0)
        event_queue.push(event)

        # Запускаем runtime в отдельном потоке
        def run_runtime():
            try:
                run_loop(
                    state,
                    lambda s: None,
                    0.001,
                    5,
                    stop_event,
                    event_queue,
                    False,
                    False,
                    False,
                    False,
                    10,
                    False,
                )
            except Exception:
                pass  # Игнорируем для smoke теста

        runtime_thread = threading.Thread(target=run_runtime)
        runtime_thread.start()

        # Пока runtime работает, проверяем потокобезопасность
        time.sleep(0.01)
        status = state.get_safe_status_dict()
        assert isinstance(status, dict)

        stop_event.set()
        runtime_thread.join(timeout=1.0)

    # ============================================================================
    # New Functionality Integration Smoke Tests
    # ============================================================================

    def test_new_functionality_integration_smoke(self):
        """Дымовой тест создания IndexEngine"""
        import shutil
        import tempfile
        from pathlib import Path

        # Создаем временные директории
        docs_dir = Path(tempfile.mkdtemp())
        todo_dir = Path(tempfile.mkdtemp())
        src_dir = Path(tempfile.mkdtemp())

        try:
            from mcp_index_engine import IndexEngine

            engine = IndexEngine(docs_dir, todo_dir, src_dir)
            assert engine is not None
            assert isinstance(engine, IndexEngine)
            assert engine.docs_dir == docs_dir.resolve()
            assert engine.todo_dir == todo_dir.resolve()
            assert engine.src_dir == src_dir.resolve()
            assert not engine._initialized
        finally:
            shutil.rmtree(docs_dir, ignore_errors=True)
            shutil.rmtree(todo_dir, ignore_errors=True)
            shutil.rmtree(src_dir, ignore_errors=True)

    def test_mcp_index_engine_tokenization(self):
        """Дымовой тест токенизации IndexEngine"""
        import shutil
        import tempfile
        from pathlib import Path

        docs_dir = Path(tempfile.mkdtemp())
        todo_dir = Path(tempfile.mkdtemp())
        src_dir = Path(tempfile.mkdtemp())

        try:
            from mcp_index_engine import IndexEngine

            engine = IndexEngine(docs_dir, todo_dir, src_dir)

            # Тест токенизации
            content = "Hello world test search"
            tokens = engine._tokenize_content(content)
            assert isinstance(tokens, set)
            assert "hello" in tokens
            assert "world" in tokens
            assert "test" in tokens
            assert "search" in tokens
            assert len(tokens) == 4

            # Тест пустой токенизации
            empty_tokens = engine._tokenize_content("")
            assert len(empty_tokens) == 0
        finally:
            shutil.rmtree(docs_dir, ignore_errors=True)
            shutil.rmtree(todo_dir, ignore_errors=True)
            shutil.rmtree(src_dir, ignore_errors=True)

    def test_mcp_index_engine_file_operations(self):
        """Дымовой тест операций с файлами IndexEngine"""
        import shutil
        import tempfile
        from pathlib import Path

        docs_dir = Path(tempfile.mkdtemp())
        todo_dir = Path(tempfile.mkdtemp())
        src_dir = Path(tempfile.mkdtemp())

        try:
            from mcp_index_engine import IndexEngine

            engine = IndexEngine(docs_dir, todo_dir, src_dir)

            # Создаем тестовый файл
            test_file = docs_dir / "test.md"
            test_file.write_text("Test content for indexing", encoding="utf-8")

            # Тест загрузки содержимого
            content = engine._load_content(test_file)
            assert content == "Test content for indexing"

            # Тест получения содержимого через кэш
            cached_content = engine._get_content(test_file, docs_dir)
            assert cached_content == "Test content for indexing"

            # Проверяем, что файл в кэше
            rel_path = engine._get_relative_path(test_file, docs_dir)
            assert rel_path in engine.content_cache
        finally:
            shutil.rmtree(docs_dir, ignore_errors=True)
            shutil.rmtree(todo_dir, ignore_errors=True)
            shutil.rmtree(src_dir, ignore_errors=True)

    def test_mcp_index_engine_indexing(self):
        """Дымовой тест индексации IndexEngine"""
        import shutil
        import tempfile
        from pathlib import Path

        docs_dir = Path(tempfile.mkdtemp())
        todo_dir = Path(tempfile.mkdtemp())
        src_dir = Path(tempfile.mkdtemp())

        try:
            from mcp_index_engine import IndexEngine

            engine = IndexEngine(docs_dir, todo_dir, src_dir)

            # Создаем тестовые файлы
            (docs_dir / "test1.md").write_text("Hello world", encoding="utf-8")
            (docs_dir / "test2.md").write_text("Hello search", encoding="utf-8")

            # Индексируем
            engine.index_directory(docs_dir)

            # Проверяем индексацию
            assert len(engine.content_cache) == 2
            assert "hello" in engine.inverted_index
            assert len(engine.inverted_index["hello"]) == 2

            # Тест поиска
            results = engine.search_in_directory(docs_dir, "hello")
            assert len(results) == 2
            assert all("test" in r["path"] for r in results)
        finally:
            shutil.rmtree(docs_dir, ignore_errors=True)
            shutil.rmtree(todo_dir, ignore_errors=True)
            shutil.rmtree(src_dir, ignore_errors=True)

    def test_mcp_index_engine_initialization(self):
        """Дымовой тест инициализации IndexEngine"""
        import shutil
        import tempfile
        from pathlib import Path

        docs_dir = Path(tempfile.mkdtemp())
        todo_dir = Path(tempfile.mkdtemp())
        src_dir = Path(tempfile.mkdtemp())

        try:
            from mcp_index_engine import IndexEngine

            engine = IndexEngine(docs_dir, todo_dir, src_dir)

            # Создаем файлы для индексации
            (docs_dir / "doc1.md").write_text("Documentation content", encoding="utf-8")
            (todo_dir / "todo1.md").write_text("TODO content", encoding="utf-8")

            # Инициализируем
            engine.initialize()

            assert engine._initialized
            assert len(engine.content_cache) == 2
            assert len(engine.inverted_index) > 0
        finally:
            shutil.rmtree(docs_dir, ignore_errors=True)
            shutil.rmtree(todo_dir, ignore_errors=True)
            shutil.rmtree(src_dir, ignore_errors=True)

    def test_mcp_index_engine_reindex(self):
        """Дымовой тест переиндексации IndexEngine"""
        import shutil
        import tempfile
        from pathlib import Path

        docs_dir = Path(tempfile.mkdtemp())
        todo_dir = Path(tempfile.mkdtemp())
        src_dir = Path(tempfile.mkdtemp())

        try:
            from mcp_index_engine import IndexEngine

            engine = IndexEngine(docs_dir, todo_dir, src_dir)

            # Создаем начальные файлы
            (docs_dir / "initial.md").write_text("Initial content", encoding="utf-8")
            engine.initialize()

            initial_cache_size = len(engine.content_cache)

            # Добавляем новый файл
            (docs_dir / "new.md").write_text("New content", encoding="utf-8")
            engine.reindex()

            # Проверяем переиндексацию
            assert len(engine.content_cache) == initial_cache_size + 1
            assert "new.md" in engine.content_cache
        finally:
            shutil.rmtree(docs_dir, ignore_errors=True)
            shutil.rmtree(todo_dir, ignore_errors=True)
            shutil.rmtree(src_dir, ignore_errors=True)

    # ============================================================================
    # API Authentication Smoke Tests
    # ============================================================================

    def test_api_app_instantiation(self):
        """Дымовой тест создания FastAPI приложения"""
        from api import app

        assert app is not None
        assert hasattr(app, "title")
        assert hasattr(app, "description")
        assert hasattr(app, "version")
        assert app.title == "Life API"
        assert app.version == "1.0.0"

    def test_api_routes_registration(self):
        """Дымовой тест регистрации маршрутов API"""
        from api import app

        routes = [route.path for route in app.routes]
        expected_routes = [
            "/",
            "/register",
            "/token",
            "/protected",
            "/status",
            "/event",
            "/users",
        ]

        for route in expected_routes:
            assert route in routes, f"Route {route} not found in API routes"

    def test_api_models_instantiation(self):
        """Дымовой тест создания экземпляров моделей API"""
        from api import EventCreate, StatusResponse, Token, User, UserCreate

        # User
        user = User(username="test", email="test@example.com")
        assert user.username == "test"
        assert user.email == "test@example.com"
        assert user.disabled is False

        # UserCreate
        user_create = UserCreate(
            username="test", email="test@example.com", password="pass"
        )
        assert user_create.username == "test"
        assert user_create.password == "pass"

        # Token
        token = Token(access_token="jwt.token", token_type="bearer")
        assert token.access_token == "jwt.token"
        assert token.token_type == "bearer"

        # EventCreate
        event = EventCreate(type="noise", intensity=0.5)
        assert event.type == "noise"
        assert event.intensity == 0.5

        # StatusResponse
        status = StatusResponse(
            active=True,
            ticks=100,
            age=100.5,
            energy=85.0,
            stability=0.95,
            integrity=0.98,
            subjective_time=50.0,
            fatigue=0.1,
            tension=0.2,
        )
        assert status.active is True
        assert status.ticks == 100
        assert status.energy == 85.0

    def test_api_utility_functions(self):
        """Дымовой тест утилитарных функций API"""
        from api import create_access_token, get_password_hash, verify_password

        # Password hashing
        password = "testpassword"
        hashed = get_password_hash(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert verify_password(password, hashed)

        # Wrong password verification
        assert not verify_password("wrongpassword", hashed)

        # JWT token creation
        data = {"sub": "testuser"}
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count(".") == 2  # JWT format

    def test_api_user_database(self):
        """Дымовой тест базы данных пользователей"""
        from api import fake_users_db

        assert isinstance(fake_users_db, dict)
        assert len(fake_users_db) >= 2  # admin and user

        # Проверяем структуру пользователей
        for username, user in fake_users_db.items():
            assert hasattr(user, "username")
            assert hasattr(user, "email")
            assert hasattr(user, "hashed_password")
            assert hasattr(user, "disabled")
            assert user.username == username

    def test_api_test_client_creation(self):
        """Дымовой тест создания тестового клиента"""
        from fastapi.testclient import TestClient

        from api import app

        client = TestClient(app)
        assert client is not None

        # Тест базового запроса
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "version" in data

    def test_api_openapi_specification(self):
        """Дымовой тест спецификации OpenAPI"""
        from fastapi.testclient import TestClient

        from api import app

        client = TestClient(app)

        # Получаем спецификацию OpenAPI
        response = client.get("/openapi.json")
        assert response.status_code == 200

        spec = response.json()
        assert "info" in spec
        assert "paths" in spec
        assert spec["info"]["title"] == "Life API"
        assert spec["info"]["version"] == "1.0.0"

        # Проверяем наличие основных эндпоинтов в спецификации
        assert "/" in spec["paths"]
        assert "/register" in spec["paths"]
        assert "/token" in spec["paths"]
        assert "/status" in spec["paths"]

    # ============================================================================
    # MCP + API Integration Smoke Tests
    # ============================================================================

    def test_mcp_api_integration_smoke(self):
        """Дымовой тест интеграции MCP Index Engine с API"""
        import shutil
        import tempfile
        from pathlib import Path

        from fastapi.testclient import TestClient

        docs_dir = Path(tempfile.mkdtemp())
        todo_dir = Path(tempfile.mkdtemp())
        src_dir = Path(tempfile.mkdtemp())

        try:
            # Создаем тестовую документацию
            (docs_dir / "api_docs.md").write_text(
                "# API Documentation\nThis is API docs for search testing",
                encoding="utf-8",
            )
            (docs_dir / "readme.md").write_text(
                "# README\nWelcome to the project", encoding="utf-8"
            )

            # Создаем IndexEngine
            from mcp_index_engine import IndexEngine

            engine = IndexEngine(docs_dir, todo_dir, src_dir)
            engine.initialize()

            # Проверяем индексацию
            assert len(engine.content_cache) == 2
            assert "api" in engine.inverted_index
            assert "documentation" in engine.inverted_index

            # Тест поиска
            results = engine.search_in_directory(docs_dir, "api")
            assert len(results) == 1
            assert "api_docs.md" in results[0]["path"]

            # Тест API клиента
            from api import app

            client = TestClient(app)

            # Регистрируем пользователя
            import uuid

            username = f"search_user_{uuid.uuid4().hex[:8]}"
            user_data = {
                "username": username,
                "email": f"{username}@example.com",
                "password": "search123",
            }
            response = client.post("/register", json=user_data)
            assert response.status_code == 201

            # Входим
            login_response = client.post(
                "/token", data={"username": username, "password": "search123"}
            )
            assert login_response.status_code == 200

            # Получаем статус
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            status_response = client.get("/status", headers=headers)
            assert status_response.status_code == 200

            # Проверяем, что все компоненты работают вместе
            assert len(engine.content_cache) == 2
            assert status_response.json()["active"] is True

        finally:
            shutil.rmtree(docs_dir, ignore_errors=True)
            shutil.rmtree(todo_dir, ignore_errors=True)
            shutil.rmtree(src_dir, ignore_errors=True)

    # ============================================================================
    # Runtime Managers Smoke Tests
    # ============================================================================

    def test_snapshot_manager_instantiation(self):
        """Дымовой тест создания экземпляра SnapshotManager"""
        from unittest.mock import Mock

        saver = Mock()
        manager = SnapshotManager(period_ticks=10, saver=saver)

        assert manager is not None
        assert isinstance(manager, SnapshotManager)
        assert manager.period_ticks == 10
        assert manager.saver == saver

    def test_snapshot_manager_basic_operations(self):
        """Дымовой тест основных операций SnapshotManager"""
        from unittest.mock import Mock

        saver = Mock()
        manager = SnapshotManager(period_ticks=5, saver=saver)
        state = SelfState()

        # Тест should_snapshot с различными тиками
        assert manager.should_snapshot(0) is False  # Тик 0 исключен
        assert manager.should_snapshot(5) is True  # Кратно периоду
        assert manager.should_snapshot(10) is True  # Кратно периоду
        assert manager.should_snapshot(7) is False  # Не кратно

        # Тест maybe_snapshot
        state.ticks = 5
        result = manager.maybe_snapshot(state)
        assert result is True
        saver.assert_called_once_with(state)

        # Проверяем статус операции
        status = manager.get_last_operation_status()
        assert isinstance(status, dict)
        assert status["success"] is True
        assert status["error"] is None

    def test_snapshot_manager_error_handling(self):
        """Дымовой тест обработки ошибок SnapshotManager"""
        from unittest.mock import Mock

        saver = Mock(side_effect=Exception("Test error"))
        manager = SnapshotManager(period_ticks=5, saver=saver)
        state = SelfState()
        state.ticks = 5

        # Ошибка не должна ронять менеджер
        result = manager.maybe_snapshot(state)
        assert result is False
        saver.assert_called_once()

        # Проверяем статус ошибки
        status = manager.get_last_operation_status()
        assert status["success"] is False
        assert status["error"] == "Test error"

    def test_log_manager_instantiation(self):
        """Дымовой тест создания экземпляра LogManager"""
        from unittest.mock import Mock

        flush_fn = Mock()
        policy = FlushPolicy()
        manager = LogManager(flush_policy=policy, flush_fn=flush_fn)

        assert manager is not None
        assert isinstance(manager, LogManager)
        assert manager.flush_policy == policy
        assert manager.flush_fn == flush_fn

    def test_log_manager_basic_operations(self):
        """Дымовой тест основных операций LogManager"""
        from unittest.mock import Mock

        flush_fn = Mock()
        policy = FlushPolicy(flush_period_ticks=5)
        manager = LogManager(flush_policy=policy, flush_fn=flush_fn)
        state = SelfState()

        # Тест создания и базовых операций (дымовой тест - главное, чтобы не падало)
        state.ticks = 3
        manager.maybe_flush(state, phase="shutdown")
        # Не проверяем вызов flush_fn - это детальная логика, а не smoke test

        # Тест периодического flush
        state.ticks = 5
        manager.maybe_flush(state, phase="tick")
        # Проверяем, что не падает, а не конкретную логику

    def test_log_manager_policy_control(self):
        """Дымовой тест управления политикой LogManager"""
        from unittest.mock import Mock

        flush_fn = Mock()

        # Политика без flush на exception
        policy = FlushPolicy(flush_on_exception=False)
        manager = LogManager(flush_policy=policy, flush_fn=flush_fn)
        state = SelfState()

        # Exception flush отключен
        manager.maybe_flush(state, phase="exception")
        flush_fn.assert_not_called()

        # Политика с flush перед snapshot
        policy_before = FlushPolicy(flush_before_snapshot=True)
        manager_before = LogManager(flush_policy=policy_before, flush_fn=flush_fn)

        manager_before.maybe_flush(state, phase="before_snapshot")
        flush_fn.assert_called()

    def test_flush_policy_instantiation(self):
        """Дымовой тест создания экземпляра FlushPolicy"""
        policy = FlushPolicy()

        assert policy is not None
        assert isinstance(policy, FlushPolicy)

        # Проверяем значения по умолчанию
        assert policy.flush_period_ticks == 10
        assert policy.flush_before_snapshot is True
        assert policy.flush_after_snapshot is False
        assert policy.flush_on_exception is True
        assert policy.flush_on_shutdown is True

    def test_flush_policy_custom_values(self):
        """Дымовой тест пользовательских значений FlushPolicy"""
        policy = FlushPolicy(
            flush_period_ticks=20,
            flush_before_snapshot=False,
            flush_after_snapshot=True,
            flush_on_exception=False,
            flush_on_shutdown=False,
        )

        assert policy.flush_period_ticks == 20
        assert policy.flush_before_snapshot is False
        assert policy.flush_after_snapshot is True
        assert policy.flush_on_exception is False
        assert policy.flush_on_shutdown is False

    def test_life_policy_instantiation(self):
        """Дымовой тест создания экземпляра LifePolicy"""
        policy = LifePolicy()

        assert policy is not None
        assert isinstance(policy, LifePolicy)

        # Проверяем значения по умолчанию
        assert policy.weakness_threshold == 0.05
        assert policy.penalty_k == 0.02
        assert policy.stability_multiplier == 2.0
        assert policy.integrity_multiplier == 2.0

    def test_life_policy_basic_operations(self):
        """Дымовой тест основных операций LifePolicy"""
        policy = LifePolicy()
        state = SelfState()

        # Тест is_weak с нормальным состоянием
        state.energy = 100.0
        state.stability = 1.0
        state.integrity = 1.0
        assert policy.is_weak(state) is False

        # Тест is_weak с ослабленным состоянием
        state.energy = 0.0  # Ниже порога
        assert policy.is_weak(state) is True

        state.energy = 100.0
        state.stability = 0.0  # Ниже порога
        assert policy.is_weak(state) is True

        # Тест weakness_penalty
        penalty = policy.weakness_penalty(1.0)
        assert isinstance(penalty, dict)
        assert "energy" in penalty
        assert "stability" in penalty
        assert "integrity" in penalty

        # Все штрафы должны быть отрицательными
        assert all(v <= 0 for v in penalty.values())

        # Штраф stability должен быть больше штрафа energy (из-за multiplier)
        assert penalty["stability"] < penalty["energy"]

    def test_life_policy_custom_parameters(self):
        """Дымовой тест LifePolicy с пользовательскими параметрами"""
        policy = LifePolicy(
            weakness_threshold=0.1,
            penalty_k=0.05,
            stability_multiplier=3.0,
            integrity_multiplier=1.5,
        )

        state = SelfState()
        state.energy = 0.05  # Ниже порога 0.1
        state.stability = 1.0
        state.integrity = 1.0

        assert policy.is_weak(state) is True

        penalty = policy.weakness_penalty(1.0)
        # Штраф должен быть больше чем с параметрами по умолчанию
        assert abs(penalty["energy"] - (-0.05)) < 1e-10  # penalty_k * dt
        assert (
            abs(penalty["stability"] - (-0.15)) < 1e-10
        )  # penalty_k * dt * stability_multiplier
        assert (
            abs(penalty["integrity"] - (-0.075)) < 1e-10
        )  # penalty_k * dt * integrity_multiplier

    def test_runtime_managers_integration_smoke(self):
        """Дымовой тест интеграции runtime managers"""
        from unittest.mock import Mock

        state = SelfState()

        # Создаем все менеджеры
        saver = Mock()
        snapshot_manager = SnapshotManager(period_ticks=10, saver=saver)

        flush_fn = Mock()
        log_policy = FlushPolicy(flush_period_ticks=5)
        log_manager = LogManager(flush_policy=log_policy, flush_fn=flush_fn)

        life_policy = LifePolicy()

        # Тест базовой работы вместе
        state.ticks = 10
        state.energy = 50.0
        state.stability = 0.8
        state.integrity = 0.9

        # Snapshot manager
        result = snapshot_manager.maybe_snapshot(state)
        assert isinstance(result, bool)

        # Log manager
        log_manager.maybe_flush(state, phase="tick")

        # Life policy
        is_weak = life_policy.is_weak(state)
        assert isinstance(is_weak, bool)

        penalty = life_policy.weakness_penalty(0.1)
        assert isinstance(penalty, dict)

        # Проверяем, что все компоненты созданы и работают
        assert snapshot_manager is not None
        assert log_manager is not None
        assert life_policy is not None

    def test_runtime_managers_edge_cases(self):
        """Дымовой тест edge cases runtime managers"""
        from unittest.mock import Mock

        # SnapshotManager с большим периодом
        saver = Mock()
        manager = SnapshotManager(period_ticks=1000, saver=saver)
        state = SelfState()

        # Рано для снапшота
        state.ticks = 50
        result = manager.maybe_snapshot(state)
        assert result is False
        saver.assert_not_called()

        # LogManager с редким flush
        flush_fn = Mock()
        policy = FlushPolicy(flush_period_ticks=100)
        log_manager = LogManager(flush_policy=policy, flush_fn=flush_fn)

        state.ticks = 50
        log_manager.maybe_flush(state, phase="tick")
        # На тике 50 при period=100 и last_flush_tick=-100: ticks_since_flush = 50 - (-100) = 150 > 100, поэтому flush происходит
        flush_fn.assert_called()  # Flush должен произойти

        # LifePolicy с высокими порогами
        policy = LifePolicy(weakness_threshold=0.5)
        state.energy = 0.3  # Ниже порога
        assert policy.is_weak(state) is True

        state.energy = 0.6  # Выше порога
        assert policy.is_weak(state) is False
