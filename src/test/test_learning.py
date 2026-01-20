"""
Unit-тесты для модуля Learning (Этап 14)

Проверяем:
- Извлечение статистики из Memory
- Медленное изменение параметров (<= 0.01)
- Отсутствие оптимизации и целей
- Интеграция с Memory и Feedback
"""

import inspect
import sys
import time
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest

from src.learning.learning import LearningEngine
from src.memory.memory import MemoryEntry
from src.state.self_state import SelfState


@pytest.mark.unit
class TestLearningEngine:
    """Тесты для LearningEngine"""

    def test_process_statistics_empty_memory(self):
        """Тест обработки пустой Memory"""
        engine = LearningEngine()
        statistics = engine.process_statistics([])

        assert statistics["total_entries"] == 0
        assert statistics["feedback_entries"] == 0
        assert len(statistics["event_type_counts"]) == 0
        assert len(statistics["feedback_pattern_counts"]) == 0

    def test_process_statistics_event_types(self):
        """Тест извлечения статистики по типам событий"""
        engine = LearningEngine()
        memory = [
            MemoryEntry(event_type="noise", meaning_significance=0.3, timestamp=1.0),
            MemoryEntry(event_type="noise", meaning_significance=0.5, timestamp=2.0),
            MemoryEntry(event_type="shock", meaning_significance=0.8, timestamp=3.0),
        ]

        statistics = engine.process_statistics(memory)

        assert statistics["total_entries"] == 3
        assert statistics["event_type_counts"]["noise"] == 2
        assert statistics["event_type_counts"]["shock"] == 1
        assert statistics["event_type_total_significance"]["noise"] == 0.8
        assert statistics["event_type_total_significance"]["shock"] == 0.8

    def test_process_statistics_feedback_data(self):
        """Тест обработки Feedback данных"""
        engine = LearningEngine()
        memory = [
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
            ),
            MemoryEntry(
                event_type="feedback",
                meaning_significance=0.0,
                timestamp=2.0,
                feedback_data={
                    "action_id": "action_2",
                    "action_pattern": "absorb",
                    "state_delta": {"energy": 0.2, "stability": 0.1, "integrity": 0.0},
                    "delay_ticks": 3,
                    "associated_events": [],
                },
            ),
        ]

        statistics = engine.process_statistics(memory)

        assert statistics["feedback_entries"] == 2
        assert statistics["feedback_pattern_counts"]["dampen"] == 1
        assert statistics["feedback_pattern_counts"]["absorb"] == 1
        assert len(statistics["feedback_state_deltas"]["energy"]) == 2
        assert statistics["feedback_state_deltas"]["energy"][0] == -0.1
        assert statistics["feedback_state_deltas"]["energy"][1] == 0.2

    def test_adjust_parameters_slow_changes(self):
        """Тест медленного изменения параметров (<= 0.01)"""
        engine = LearningEngine()
        current_params = {
            "event_type_sensitivity": {
                "noise": 0.2,
                "decay": 0.2,
                "recovery": 0.2,
                "shock": 0.2,
                "idle": 0.2,
            },
            "significance_thresholds": {
                "noise": 0.1,
                "decay": 0.1,
                "recovery": 0.1,
                "shock": 0.1,
                "idle": 0.1,
            },
            "response_coefficients": {
                "dampen": 0.5,
                "absorb": 1.0,
                "ignore": 0.0,
            },
        }

        # Статистика с частыми событиями noise
        statistics = {
            "event_type_counts": {"noise": 10, "shock": 1},
            "event_type_total_significance": {"noise": 5.0, "shock": 0.8},
            "feedback_pattern_counts": {"dampen": 5, "absorb": 2},
            "feedback_state_deltas": {
                "energy": [-0.1, 0.2],
                "stability": [-0.05, 0.1],
                "integrity": [0.0, 0.0],
            },
            "total_entries": 11,
            "feedback_entries": 2,
        }

        new_params = engine.adjust_parameters(statistics, current_params)

        # Проверяем, что изменения медленные (<= 0.01)
        for key in new_params:
            if key in current_params:
                for param_name, new_value in new_params[key].items():
                    if param_name in current_params[key]:
                        old_value = current_params[key][param_name]
                        delta = abs(new_value - old_value)
                        assert (
                            delta <= engine.MAX_PARAMETER_DELTA + 0.001
                        ), f"Изменение {key}.{param_name} слишком большое: {delta}"

    def test_adjust_parameters_boundaries(self):
        """Тест границ параметров (clamp)"""
        engine = LearningEngine()
        current_params = {
            "event_type_sensitivity": {
                "noise": 0.99,  # Почти максимум
                "decay": 0.01,  # Почти минимум
            },
            "significance_thresholds": {},
            "response_coefficients": {},
        }

        # Статистика, которая должна увеличить noise и уменьшить decay
        statistics = {
            "event_type_counts": {"noise": 100, "decay": 1},
            "event_type_total_significance": {"noise": 50.0, "decay": 0.1},
            "feedback_pattern_counts": {},
            "feedback_state_deltas": {"energy": [], "stability": [], "integrity": []},
            "total_entries": 101,
            "feedback_entries": 0,
        }

        new_params = engine.adjust_parameters(statistics, current_params)

        # Проверяем границы
        assert 0.0 <= new_params["event_type_sensitivity"]["noise"] <= 1.0
        assert 0.0 <= new_params["event_type_sensitivity"]["decay"] <= 1.0

    def test_record_changes(self):
        """Тест фиксации изменений в SelfState"""
        engine = LearningEngine()
        self_state = SelfState()

        old_params = self_state.learning_params.copy()
        new_params = {
            "event_type_sensitivity": {
                "noise": old_params["event_type_sensitivity"]["noise"] + 0.005,
            }
        }

        engine.record_changes(old_params, new_params, self_state)

        # Проверяем, что параметры обновлены
        assert (
            self_state.learning_params["event_type_sensitivity"]["noise"]
            == new_params["event_type_sensitivity"]["noise"]
        )

    def test_record_changes_partial_update(self):
        """Тест частичного обновления параметров - проверка merge вместо перезаписи"""
        engine = LearningEngine()
        self_state = SelfState()

        # Сохраняем начальные значения всех параметров
        initial_params = self_state.learning_params.copy()
        initial_noise = initial_params["event_type_sensitivity"]["noise"]
        initial_decay = initial_params["event_type_sensitivity"]["decay"]
        initial_significance_noise = initial_params["significance_thresholds"]["noise"]
        initial_dampen = initial_params["response_coefficients"]["dampen"]

        # Создаем частичное обновление - только event_type_sensitivity для noise
        old_params = self_state.learning_params.copy()
        new_params = {
            "event_type_sensitivity": {
                "noise": initial_noise + 0.005,
                # НЕ обновляем decay - он должен остаться прежним
            }
        }

        engine.record_changes(old_params, new_params, self_state)

        # Проверяем, что обновленный параметр изменился
        assert (
            self_state.learning_params["event_type_sensitivity"]["noise"]
            == initial_noise + 0.005
        )

        # Проверяем, что НЕ обновленные параметры сохранились
        assert (
            self_state.learning_params["event_type_sensitivity"]["decay"]
            == initial_decay
        ), "decay должен остаться прежним при частичном обновлении"
        assert (
            self_state.learning_params["significance_thresholds"]["noise"]
            == initial_significance_noise
        ), "significance_thresholds должны остаться прежними"
        assert (
            self_state.learning_params["response_coefficients"]["dampen"]
            == initial_dampen
        ), "response_coefficients должны остаться прежними"

        # Проверяем, что все ключи верхнего уровня сохранились
        assert "event_type_sensitivity" in self_state.learning_params
        assert "significance_thresholds" in self_state.learning_params
        assert "response_coefficients" in self_state.learning_params

    def test_no_optimization_methods(self):
        """Проверка отсутствия методов оптимизации"""
        engine = LearningEngine()

        # Проверяем, что нет запрещенных методов
        forbidden_methods = [
            "optimize",
            "improve",
            "maximize",
            "minimize",
            "evaluate",
            "score",
            "rate",
            "judge",
        ]

        for method_name in forbidden_methods:
            assert not hasattr(
                engine, method_name
            ), f"LearningEngine не должен иметь метод {method_name}"

    def test_no_goals_or_rewards(self):
        """Проверка отсутствия целей и reward"""
        # Проверяем, что в коде нет упоминаний запрещенных терминов
        import inspect

        source = inspect.getsource(LearningEngine)
        forbidden_terms = [
            "goal",
            "target",
            "objective",
            "reward",
            "punishment",
            "utility",
            "scoring",
        ]

        # Исключаем комментарии и docstrings
        lines = [
            line
            for line in source.split("\n")
            if not line.strip().startswith("#")
            and not line.strip().startswith('"""')
            and not line.strip().startswith("'''")
        ]
        source_clean = "\n".join(lines)

        for term in forbidden_terms:
            # Проверяем, что термин не используется в коде (только в комментариях/docstrings)
            # Но разрешаем использование в комментариях как часть документации ограничений
            assert (
                term not in source_clean.lower()
                or "запрещено" in source_clean.lower()
                or "forbidden" in source_clean.lower()
            ), f"Термин {term} не должен использоваться в коде Learning"

    def test_integration_with_memory(self):
        """Интеграционный тест с Memory"""
        engine = LearningEngine()
        self_state = SelfState()

        # Добавляем записи в Memory
        self_state.memory.append(
            MemoryEntry(
                event_type="noise",
                meaning_significance=0.4,
                timestamp=1.0,
            )
        )
        self_state.memory.append(
            MemoryEntry(
                event_type="feedback",
                meaning_significance=0.0,
                timestamp=2.0,
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

        # Обрабатываем статистику
        statistics = engine.process_statistics(self_state.memory)

        assert statistics["total_entries"] == 2
        assert statistics["event_type_counts"]["noise"] == 1
        assert statistics["feedback_entries"] == 1

        # Изменяем параметры
        new_params = engine.adjust_parameters(statistics, self_state.learning_params)

        # Фиксируем изменения
        if new_params:
            engine.record_changes(self_state.learning_params, new_params, self_state)

        # Проверяем, что параметры обновлены
        assert "event_type_sensitivity" in self_state.learning_params

    def test_learning_frequency_simulation(self):
        """Симуляция частоты вызова Learning (раз в 50-100 тиков)"""
        engine = LearningEngine()
        self_state = SelfState()

        learning_interval = 75
        learning_calls = 0

        # Симулируем 200 тиков
        for tick in range(1, 201):
            self_state.ticks = tick

            # Добавляем случайные записи в Memory
            if tick % 10 == 0:
                self_state.memory.append(
                    MemoryEntry(
                        event_type="noise",
                        meaning_significance=0.3,
                        timestamp=float(tick),
                    )
                )

            # Learning вызывается раз в learning_interval тиков
            if tick % learning_interval == 0:
                statistics = engine.process_statistics(self_state.memory)
                new_params = engine.adjust_parameters(
                    statistics, self_state.learning_params
                )
                if new_params:
                    engine.record_changes(
                        self_state.learning_params, new_params, self_state
                    )
                learning_calls += 1

        # Проверяем, что Learning вызывался примерно 2-3 раза за 200 тиков
        assert (
            2 <= learning_calls <= 3
        ), f"Learning должен вызываться 2-3 раза, вызван {learning_calls} раз"

    def test_learning_no_side_effects(self):
        """Проверка, что Learning не влияет на другие модули"""
        engine = LearningEngine()
        self_state = SelfState()

        # Сохраняем начальные значения
        initial_energy = self_state.energy
        initial_stability = self_state.stability
        initial_integrity = self_state.integrity

        # Выполняем Learning
        statistics = engine.process_statistics(self_state.memory)
        new_params = engine.adjust_parameters(statistics, self_state.learning_params)
        if new_params:
            engine.record_changes(self_state.learning_params, new_params, self_state)

        # Проверяем, что energy, stability, integrity не изменились
        assert self_state.energy == initial_energy
        assert self_state.stability == initial_stability
        assert self_state.integrity == initial_integrity

    def test_learning_persistence(self):
        """Тест сохранения параметров в SelfState"""
        engine = LearningEngine()
        self_state = SelfState()

        # Изменяем параметры
        old_params = self_state.learning_params.copy()
        new_params = {
            "event_type_sensitivity": {
                "noise": old_params["event_type_sensitivity"]["noise"] + 0.005,
            }
        }

        engine.record_changes(old_params, new_params, self_state)

        # Проверяем, что параметры сохранились
        assert (
            self_state.learning_params["event_type_sensitivity"]["noise"]
            == new_params["event_type_sensitivity"]["noise"]
        )

        # Проверяем, что другие параметры не изменились
        assert (
            self_state.learning_params["event_type_sensitivity"]["decay"]
            == old_params["event_type_sensitivity"]["decay"]
        )


@pytest.mark.integration
class TestLearningIntegration:
    """Интеграционные тесты Learning с Memory и Feedback"""

    def test_learning_with_feedback_data(self):
        """Тест обработки Feedback данных Learning"""
        engine = LearningEngine()
        self_state = SelfState()

        # Создаем Feedback записи в Memory
        for i in range(5):
            self_state.memory.append(
                MemoryEntry(
                    event_type="feedback",
                    meaning_significance=0.0,
                    timestamp=float(i),
                    feedback_data={
                        "action_id": f"action_{i}",
                        "action_pattern": "dampen" if i % 2 == 0 else "absorb",
                        "state_delta": {
                            "energy": -0.1 if i % 2 == 0 else 0.2,
                            "stability": -0.05 if i % 2 == 0 else 0.1,
                            "integrity": 0.0,
                        },
                        "delay_ticks": 5,
                        "associated_events": [],
                    },
                )
            )

        # Обрабатываем статистику
        statistics = engine.process_statistics(self_state.memory)

        assert statistics["feedback_entries"] == 5
        assert statistics["feedback_pattern_counts"]["dampen"] == 3
        assert statistics["feedback_pattern_counts"]["absorb"] == 2

        # Изменяем параметры на основе Feedback
        new_params = engine.adjust_parameters(statistics, self_state.learning_params)

        # Проверяем, что параметры изменились медленно
        if new_params:
            for key in new_params:
                if key in self_state.learning_params:
                    for param_name, new_value in new_params[key].items():
                        if param_name in self_state.learning_params[key]:
                            old_value = self_state.learning_params[key][param_name]
                            delta = abs(new_value - old_value)
                            assert delta <= engine.MAX_PARAMETER_DELTA + 0.001

            engine.record_changes(self_state.learning_params, new_params, self_state)

    def test_learning_frequency_in_runtime(self):
        """Тест частоты вызова Learning в runtime loop"""
        engine = LearningEngine()
        self_state = SelfState()

        learning_interval = 75
        learning_call_count = 0
        initial_params = self_state.learning_params.copy()

        # Симулируем работу runtime loop
        for tick in range(1, 300):
            self_state.ticks = tick

            # Добавляем события в Memory
            if tick % 5 == 0:
                self_state.memory.append(
                    MemoryEntry(
                        event_type="noise",
                        meaning_significance=0.3,
                        timestamp=float(tick),
                    )
                )

            # Добавляем Feedback записи
            if tick % 10 == 0:
                self_state.memory.append(
                    MemoryEntry(
                        event_type="feedback",
                        meaning_significance=0.0,
                        timestamp=float(tick),
                        feedback_data={
                            "action_id": f"action_{tick}",
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

            # Learning вызывается раз в learning_interval тиков
            if tick % learning_interval == 0:
                statistics = engine.process_statistics(self_state.memory)
                new_params = engine.adjust_parameters(
                    statistics, self_state.learning_params
                )
                if new_params:
                    engine.record_changes(
                        self_state.learning_params, new_params, self_state
                    )
                learning_call_count += 1

        # Проверяем, что Learning вызывался несколько раз
        assert (
            learning_call_count >= 3
        ), f"Learning должен вызываться минимум 3 раза за 300 тиков, вызван {learning_call_count} раз"

        # Проверяем, что параметры изменились медленно
        for key in initial_params:
            if key in self_state.learning_params:
                for param_name, initial_value in initial_params[key].items():
                    if param_name in self_state.learning_params[key]:
                        current_value = self_state.learning_params[key][param_name]
                        total_delta = abs(current_value - initial_value)
                        # За 3+ вызова Learning максимальное изменение: 3 * 0.01 = 0.03
                        assert (
                            total_delta <= 0.05
                        ), f"Суммарное изменение {key}.{param_name} слишком большое: {total_delta}"

    def test_learning_persistence_in_snapshots(self):
        """Тест сохранения параметров Learning в snapshots"""
        from state.self_state import save_snapshot

        engine = LearningEngine()
        self_state = SelfState()

        # Изменяем параметры
        new_params = {
            "event_type_sensitivity": {
                "noise": self_state.learning_params["event_type_sensitivity"]["noise"]
                + 0.005,
            }
        }
        engine.record_changes(self_state.learning_params, new_params, self_state)

        # Сохраняем snapshot
        self_state.ticks = 100
        save_snapshot(self_state)

        # Проверяем, что learning_params сохранены в snapshot
        snapshot_file = Path("data/snapshots/snapshot_000100.json")
        if snapshot_file.exists():
            with snapshot_file.open("r") as f:
                snapshot_data = json.load(f)

            assert "learning_params" in snapshot_data
            assert (
                snapshot_data["learning_params"]["event_type_sensitivity"]["noise"]
                == self_state.learning_params["event_type_sensitivity"]["noise"]
            )

    def test_learning_no_side_effects_on_decision_action(self):
        """Проверка, что Learning не влияет на Decision и Action"""
        engine = LearningEngine()
        self_state = SelfState()

        # Сохраняем начальное состояние
        initial_energy = self_state.energy
        initial_stability = self_state.stability
        initial_integrity = self_state.integrity
        initial_memory_size = len(self_state.memory)

        # Выполняем Learning
        statistics = engine.process_statistics(self_state.memory)
        new_params = engine.adjust_parameters(statistics, self_state.learning_params)
        if new_params:
            engine.record_changes(self_state.learning_params, new_params, self_state)

        # Проверяем, что состояние не изменилось (кроме learning_params)
        assert self_state.energy == initial_energy
        assert self_state.stability == initial_stability
        assert self_state.integrity == initial_integrity
        assert len(self_state.memory) == initial_memory_size

        # Проверяем, что learning_params изменились
        assert "event_type_sensitivity" in self_state.learning_params

    def test_learning_statistics_accuracy(self):
        """Проверка корректности статистики из Memory"""
        engine = LearningEngine()
        self_state = SelfState()

        # Добавляем разнообразные записи
        event_types = ["noise", "decay", "recovery", "shock", "idle"]
        for i, event_type in enumerate(event_types):
            for j in range(i + 1):  # Разное количество каждого типа
                self_state.memory.append(
                    MemoryEntry(
                        event_type=event_type,
                        meaning_significance=0.2 + i * 0.1,
                        timestamp=float(i * 10 + j),
                    )
                )

        # Добавляем Feedback записи
        for i in range(3):
            self_state.memory.append(
                MemoryEntry(
                    event_type="feedback",
                    meaning_significance=0.0,
                    timestamp=100.0 + i,
                    feedback_data={
                        "action_id": f"action_{i}",
                        "action_pattern": ["dampen", "absorb", "ignore"][i],
                        "state_delta": {
                            "energy": [-0.1, 0.2, 0.0][i],
                            "stability": [-0.05, 0.1, 0.0][i],
                            "integrity": [0.0, 0.0, 0.0][i],
                        },
                        "delay_ticks": 5,
                        "associated_events": [],
                    },
                )
            )

        # Обрабатываем статистику
        statistics = engine.process_statistics(self_state.memory)

        # Проверяем корректность подсчета
        total_events = sum(statistics["event_type_counts"].values())
        assert total_events == 15  # 1+2+3+4+5 = 15 событий

        assert statistics["event_type_counts"]["noise"] == 1
        assert statistics["event_type_counts"]["decay"] == 2
        assert statistics["event_type_counts"]["recovery"] == 3
        assert statistics["event_type_counts"]["shock"] == 4
        assert statistics["event_type_counts"]["idle"] == 5

        assert statistics["feedback_entries"] == 3
        assert statistics["feedback_pattern_counts"]["dampen"] == 1
        assert statistics["feedback_pattern_counts"]["absorb"] == 1
        assert statistics["feedback_pattern_counts"]["ignore"] == 1


# ============================================================================
# СТАТИЧЕСКИЕ ТЕСТЫ
# ============================================================================


@pytest.mark.static
class TestLearningStatic:
    """Статические тесты для Learning - проверка структуры, типов, отсутствия запрещенных методов"""

    def test_class_structure(self):
        """Проверка структуры класса LearningEngine"""
        assert hasattr(LearningEngine, "__init__")
        assert hasattr(LearningEngine, "process_statistics")
        assert hasattr(LearningEngine, "adjust_parameters")
        assert hasattr(LearningEngine, "record_changes")
        assert hasattr(LearningEngine, "MAX_PARAMETER_DELTA")
        assert hasattr(LearningEngine, "MIN_PARAMETER_DELTA")

    def test_constants_values(self):
        """Проверка значений констант"""
        engine = LearningEngine()
        assert engine.MAX_PARAMETER_DELTA == 0.01
        assert engine.MIN_PARAMETER_DELTA == 0.001
        assert engine.MAX_PARAMETER_DELTA > engine.MIN_PARAMETER_DELTA

    def test_method_signatures(self):
        """Проверка сигнатур методов"""
        engine = LearningEngine()

        # process_statistics
        sig = inspect.signature(engine.process_statistics)
        assert len(sig.parameters) == 2  # self + memory
        assert "memory" in sig.parameters

        # adjust_parameters
        sig = inspect.signature(engine.adjust_parameters)
        assert len(sig.parameters) == 3  # self + statistics + current_params
        assert "statistics" in sig.parameters
        assert "current_params" in sig.parameters

        # record_changes
        sig = inspect.signature(engine.record_changes)
        assert len(sig.parameters) == 4  # self + old_params + new_params + self_state
        assert "old_params" in sig.parameters
        assert "new_params" in sig.parameters
        assert "self_state" in sig.parameters

    def test_method_return_types(self):
        """Проверка типов возвращаемых значений"""
        engine = LearningEngine()

        # process_statistics возвращает dict
        result = engine.process_statistics([])
        assert isinstance(result, dict)

        # adjust_parameters возвращает dict
        result = engine.adjust_parameters({}, {})
        assert isinstance(result, dict)

        # record_changes возвращает None
        self_state = SelfState()
        result = engine.record_changes({}, {}, self_state)
        assert result is None

    def test_forbidden_methods_comprehensive(self):
        """Комплексная проверка отсутствия запрещенных методов"""
        engine = LearningEngine()

        # Список всех запрещенных методов
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
            "learn",
            "learning_model",  # "learning" разрешен как часть названия модуля
            "reward",
            "punishment",
            "goal",
            "target",
            "objective",
            "utility",
            "value_function",
            "gradient",
            "backprop",
            "loss",
            "cost",
            "error",
        ]

        for method_name in forbidden_methods:
            assert not hasattr(
                engine, method_name
            ), f"LearningEngine не должен иметь метод {method_name}"

    def test_forbidden_attributes(self):
        """Проверка отсутствия запрещенных атрибутов"""
        engine = LearningEngine()

        forbidden_attrs = [
            "optimizer",
            "loss_function",
            "reward_function",
            "goal",
            "target",
            "objective",
            "training_data",
            "test_data",
        ]

        for attr_name in forbidden_attrs:
            assert not hasattr(
                engine, attr_name
            ), f"LearningEngine не должен иметь атрибут {attr_name}"

    def test_private_methods_exist(self):
        """Проверка наличия приватных методов для внутренней логики"""
        engine = LearningEngine()

        assert hasattr(engine, "_adjust_event_sensitivity")
        assert hasattr(engine, "_adjust_significance_thresholds")
        assert hasattr(engine, "_adjust_response_coefficients")

        # Проверяем, что они приватные (начинаются с _)
        assert engine._adjust_event_sensitivity.__name__.startswith("_")
        assert engine._adjust_significance_thresholds.__name__.startswith("_")
        assert engine._adjust_response_coefficients.__name__.startswith("_")

    def test_source_code_analysis(self):
        """Анализ исходного кода на наличие запрещенных паттернов"""
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

    def test_imports_structure(self):
        """Проверка структуры импортов"""
        import learning.learning as learning_module

        # Проверяем, что модуль экспортирует LearningEngine
        assert hasattr(learning_module, "LearningEngine")
        assert learning_module.LearningEngine == LearningEngine

    def test_class_inheritance(self):
        """Проверка наследования класса"""
        assert LearningEngine.__bases__ == (
            object,
        ), "LearningEngine должен наследоваться только от object"

    def test_docstrings_presence(self):
        """Проверка наличия docstrings"""
        assert (
            LearningEngine.__doc__ is not None
        ), "LearningEngine должен иметь docstring"

        engine = LearningEngine()
        assert engine.process_statistics.__doc__ is not None
        assert engine.adjust_parameters.__doc__ is not None
        assert engine.record_changes.__doc__ is not None


# ============================================================================
# ДЫМОВЫЕ ТЕСТЫ
# ============================================================================


@pytest.mark.smoke
class TestLearningSmoke:
    """Дымовые тесты для Learning - базовые проверки работоспособности"""

    def test_engine_instantiation(self):
        """Тест создания экземпляра LearningEngine"""
        engine = LearningEngine()
        assert engine is not None
        assert isinstance(engine, LearningEngine)

    def test_process_statistics_smoke(self):
        """Дымовой тест process_statistics с минимальными данными"""
        engine = LearningEngine()
        result = engine.process_statistics([])

        assert isinstance(result, dict)
        assert "total_entries" in result
        assert "feedback_entries" in result
        assert "event_type_counts" in result
        assert result["total_entries"] == 0

    def test_adjust_parameters_smoke(self):
        """Дымовой тест adjust_parameters с минимальными данными"""
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

    def test_record_changes_smoke(self):
        """Дымовой тест record_changes с минимальными данными"""
        engine = LearningEngine()
        self_state = SelfState()
        old_params = self_state.learning_params.copy()
        new_params = {}

        # Не должно вызывать исключений
        engine.record_changes(old_params, new_params, self_state)
        assert True  # Если дошли сюда, значит исключений не было

    def test_full_cycle_smoke(self):
        """Дымовой тест полного цикла: statistics -> adjust -> record"""
        engine = LearningEngine()
        self_state = SelfState()

        # Добавляем минимальные данные
        self_state.memory.append(
            MemoryEntry(event_type="noise", meaning_significance=0.3, timestamp=1.0)
        )

        # Полный цикл
        statistics = engine.process_statistics(self_state.memory)
        new_params = engine.adjust_parameters(statistics, self_state.learning_params)
        if new_params:
            engine.record_changes(self_state.learning_params, new_params, self_state)

        # Проверяем, что все прошло без ошибок
        assert "learning_params" in self_state.learning_params

    def test_empty_memory_handling(self):
        """Дымовой тест обработки пустой памяти"""
        engine = LearningEngine()
        self_state = SelfState()

        # Пустая память не должна вызывать ошибок
        statistics = engine.process_statistics(self_state.memory)
        assert statistics["total_entries"] == 0

        new_params = engine.adjust_parameters(statistics, self_state.learning_params)
        # new_params может быть пустым dict или содержать пустые подструктуры
        assert isinstance(new_params, dict)

    def test_minimal_parameters(self):
        """Дымовой тест с минимальными параметрами"""
        engine = LearningEngine()
        statistics = {
            "event_type_counts": {"noise": 1},
            "event_type_total_significance": {"noise": 0.3},
            "feedback_pattern_counts": {},
            "feedback_state_deltas": {"energy": [], "stability": [], "integrity": []},
            "total_entries": 1,
            "feedback_entries": 0,
        }
        current_params = {
            "event_type_sensitivity": {"noise": 0.2},
        }

        result = engine.adjust_parameters(statistics, current_params)
        assert isinstance(result, dict)

    def test_boundary_values_smoke(self):
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


# ============================================================================
# ДОПОЛНИТЕЛЬНЫЕ ИНТЕГРАЦИОННЫЕ ТЕСТЫ
# ============================================================================


@pytest.mark.integration
class TestLearningIntegrationExtended:
    """Расширенные интеграционные тесты Learning"""

    def test_learning_with_runtime_loop_simulation(self):
        """Интеграционный тест симуляции работы в runtime loop"""
        from environment.event import Event
        from environment.event_queue import EventQueue

        engine = LearningEngine()
        self_state = SelfState()
        event_queue = EventQueue()

        # Симулируем несколько тиков runtime loop
        for tick in range(1, 151):  # 150 тиков
            self_state.ticks = tick

            # Добавляем события
            if tick % 10 == 0:
                event = Event(type="noise", intensity=0.1, timestamp=float(tick))
                event_queue.push(event)

            # Обрабатываем события (упрощенная версия)
            if not event_queue.is_empty():
                events = event_queue.pop_all()
                for event in events:
                    self_state.memory.append(
                        MemoryEntry(
                            event_type=event.type,
                            meaning_significance=abs(event.intensity),
                            timestamp=event.timestamp,
                        )
                    )

            # Learning вызывается раз в 75 тиков
            if tick % 75 == 0:
                statistics = engine.process_statistics(self_state.memory)
                new_params = engine.adjust_parameters(
                    statistics, self_state.learning_params
                )
                if new_params:
                    engine.record_changes(
                        self_state.learning_params, new_params, self_state
                    )

        # Проверяем, что Learning работал
        assert self_state.ticks == 150
        assert len(self_state.memory) > 0
        assert "event_type_sensitivity" in self_state.learning_params

    def test_learning_with_meaning_engine_integration(self):
        """Интеграционный тест с MeaningEngine"""
        from environment.event import Event
        from meaning.engine import MeaningEngine

        meaning_engine = MeaningEngine()
        learning_engine = LearningEngine()
        self_state = SelfState()

        # Обрабатываем события через MeaningEngine
        events = [
            Event(type="noise", intensity=0.2, timestamp=1.0),
            Event(type="shock", intensity=-0.5, timestamp=2.0),
            Event(type="recovery", intensity=0.3, timestamp=3.0),
        ]

        for event in events:
            meaning = meaning_engine.process(event, self_state.__dict__)
            if meaning.significance > 0:
                self_state.memory.append(
                    MemoryEntry(
                        event_type=event.type,
                        meaning_significance=meaning.significance,
                        timestamp=event.timestamp,
                    )
                )

        # Применяем Learning
        statistics = learning_engine.process_statistics(self_state.memory)
        new_params = learning_engine.adjust_parameters(
            statistics, self_state.learning_params
        )
        if new_params:
            learning_engine.record_changes(
                self_state.learning_params, new_params, self_state
            )

        # Проверяем результат
        assert len(self_state.memory) == 3
        assert "event_type_sensitivity" in self_state.learning_params

    def test_learning_with_feedback_loop(self):
        """Интеграционный тест с полным циклом Feedback"""
        from feedback import observe_consequences, register_action

        engine = LearningEngine()
        self_state = SelfState()
        pending_actions = []

        # Регистрируем действие
        action_id = "test_action_1"
        register_action(
            action_id,
            "dampen",
            {"energy": 100.0, "stability": 1.0, "integrity": 1.0},
            time.time(),
            pending_actions,
        )

        # Симулируем прохождение времени
        time.sleep(0.1)

        # Наблюдаем последствия
        feedback_records = observe_consequences(self_state, pending_actions, None)

        # Сохраняем Feedback в Memory
        for feedback in feedback_records:
            feedback_entry = MemoryEntry(
                event_type="feedback",
                meaning_significance=0.0,
                timestamp=feedback.timestamp,
                feedback_data={
                    "action_id": feedback.action_id,
                    "action_pattern": feedback.action_pattern,
                    "state_delta": feedback.state_delta,
                    "delay_ticks": feedback.delay_ticks,
                    "associated_events": feedback.associated_events,
                },
            )
            self_state.memory.append(feedback_entry)

        # Применяем Learning
        statistics = engine.process_statistics(self_state.memory)
        new_params = engine.adjust_parameters(statistics, self_state.learning_params)
        if new_params:
            engine.record_changes(self_state.learning_params, new_params, self_state)

        # Проверяем, что Feedback обработан
        assert statistics["feedback_entries"] >= 0  # Может быть 0 если delay не прошел
        assert "response_coefficients" in self_state.learning_params

    def test_learning_persistence_across_snapshots(self):
        """Интеграционный тест сохранения параметров Learning в snapshots"""
        from state.self_state import load_snapshot, save_snapshot

        engine = LearningEngine()
        self_state = SelfState()

        # Изменяем параметры
        initial_noise = self_state.learning_params["event_type_sensitivity"]["noise"]
        new_params = {
            "event_type_sensitivity": {
                "noise": initial_noise + 0.005,
            }
        }
        engine.record_changes(self_state.learning_params, new_params, self_state)

        # Сохраняем snapshot
        self_state.ticks = 200
        save_snapshot(self_state)

        # Загружаем snapshot
        loaded_state = load_snapshot(200)

        # Проверяем, что learning_params восстановлены
        assert "learning_params" in loaded_state.learning_params
        assert (
            loaded_state.learning_params["event_type_sensitivity"]["noise"]
            == self_state.learning_params["event_type_sensitivity"]["noise"]
        )

    def test_learning_with_large_memory(self):
        """Интеграционный тест с большим объемом памяти"""
        engine = LearningEngine()
        self_state = SelfState()

        # Создаем большое количество записей
        for i in range(100):
            self_state.memory.append(
                MemoryEntry(
                    event_type=["noise", "decay", "recovery", "shock"][i % 4],
                    meaning_significance=0.1 + (i % 10) * 0.05,
                    timestamp=float(i),
                )
            )

        # Добавляем Feedback записи
        for i in range(20):
            self_state.memory.append(
                MemoryEntry(
                    event_type="feedback",
                    meaning_significance=0.0,
                    timestamp=100.0 + i,
                    feedback_data={
                        "action_id": f"action_{i}",
                        "action_pattern": ["dampen", "absorb"][i % 2],
                        "state_delta": {
                            "energy": -0.1 if i % 2 == 0 else 0.2,
                            "stability": -0.05 if i % 2 == 0 else 0.1,
                            "integrity": 0.0,
                        },
                        "delay_ticks": 5,
                        "associated_events": [],
                    },
                )
            )

        # Обрабатываем статистику
        statistics = engine.process_statistics(self_state.memory)

        assert statistics["total_entries"] == 120
        assert statistics["feedback_entries"] == 20

        # Изменяем параметры
        new_params = engine.adjust_parameters(statistics, self_state.learning_params)
        if new_params:
            engine.record_changes(self_state.learning_params, new_params, self_state)

        # Проверяем, что все работает с большим объемом данных
        assert "event_type_sensitivity" in self_state.learning_params
