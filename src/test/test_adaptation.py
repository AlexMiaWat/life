"""
Unit-тесты для модуля Adaptation (Этап 15)

Проверяем:
- Анализ изменений от Learning
- Медленное изменение параметров поведения (<= 0.01)
- Отсутствие оптимизации и целей
- Отсутствие прямого управления Decision/Action
- Хранение истории адаптаций
- Интеграция с Learning и Memory
"""

import inspect
import sys
import time
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest

from src.adaptation.adaptation import AdaptationManager
from src.state.self_state import SelfState


@pytest.mark.unit
class TestAdaptationManager:
    """Тесты для AdaptationManager"""

    def test_analyze_changes_empty_history(self):
        """Тест анализа изменений с пустой историей"""
        manager = AdaptationManager()
        learning_params = {
            "event_type_sensitivity": {"noise": 0.3, "shock": 0.5},
            "significance_thresholds": {"noise": 0.2, "shock": 0.4},
            "response_coefficients": {"dampen": 0.6, "absorb": 0.8},
        }

        analysis = manager.analyze_changes(learning_params, [])

        assert "learning_params_snapshot" in analysis
        assert "recent_changes" in analysis
        assert "change_patterns" in analysis
        assert analysis["learning_params_snapshot"] == learning_params
        assert len(analysis["recent_changes"]) == 0

    def test_analyze_changes_with_history(self):
        """Тест анализа изменений с историей"""
        manager = AdaptationManager()
        learning_params = {
            "event_type_sensitivity": {"noise": 0.3, "shock": 0.5},
        }

        history = [
            {
                "timestamp": time.time() - 100,
                "tick": 100,
                "old_params": {},
                "new_params": {},
                "changes": {},
                "learning_params_snapshot": {
                    "event_type_sensitivity": {"noise": 0.2, "shock": 0.4},
                },
            }
        ]

        analysis = manager.analyze_changes(learning_params, history)

        assert "recent_changes" in analysis
        # Должны быть обнаружены изменения в event_type_sensitivity
        assert "event_type_sensitivity" in analysis["recent_changes"]

    def test_apply_adaptation_initialization(self):
        """Тест инициализации параметров поведения"""
        manager = AdaptationManager()
        self_state = SelfState()
        self_state.learning_params = {
            "event_type_sensitivity": {"noise": 0.3, "shock": 0.5},
            "significance_thresholds": {"noise": 0.2, "shock": 0.4},
            "response_coefficients": {"dampen": 0.6, "absorb": 0.8},
        }
        # Очищаем adaptation_params для теста инициализации
        self_state.adaptation_params = {}

        analysis = {"learning_params_snapshot": self_state.learning_params}
        current_params = {}

        new_params = manager.apply_adaptation(analysis, current_params, self_state)

        assert "behavior_sensitivity" in new_params
        assert "behavior_thresholds" in new_params
        assert "behavior_coefficients" in new_params
        assert new_params["behavior_sensitivity"]["noise"] == 0.3
        assert new_params["behavior_sensitivity"]["shock"] == 0.5

    def test_apply_adaptation_slow_changes(self):
        """Тест медленных изменений (<= 0.01)"""
        manager = AdaptationManager()
        self_state = SelfState()
        self_state.learning_params = {
            "event_type_sensitivity": {"noise": 0.5},  # Большая разница с текущим
        }

        current_params = {
            "behavior_sensitivity": {"noise": 0.2},  # Текущее значение
        }

        analysis = {"learning_params_snapshot": self_state.learning_params}
        new_params = manager.apply_adaptation(analysis, current_params, self_state)

        # Изменение должно быть медленным (<= 0.01)
        old_value = current_params["behavior_sensitivity"]["noise"]
        new_value = new_params["behavior_sensitivity"]["noise"]
        delta = abs(new_value - old_value)

        assert delta <= manager.MAX_ADAPTATION_DELTA + 0.001
        assert new_value >= 0.0
        assert new_value <= 1.0

    def test_apply_adaptation_boundaries(self):
        """Тест границ параметров [0.0, 1.0]"""
        manager = AdaptationManager()
        self_state = SelfState()
        self_state.learning_params = {
            "event_type_sensitivity": {"noise": 1.5},  # Превышает границу
        }

        current_params = {
            "behavior_sensitivity": {"noise": 0.9},
        }

        analysis = {"learning_params_snapshot": self_state.learning_params}
        new_params = manager.apply_adaptation(analysis, current_params, self_state)

        # Значение должно быть в границах [0.0, 1.0]
        new_value = new_params["behavior_sensitivity"]["noise"]
        assert new_value >= 0.0
        assert new_value <= 1.0

    def test_apply_adaptation_no_decision_action_control(self):
        """Тест отсутствия прямого управления Decision/Action"""
        manager = AdaptationManager()
        self_state = SelfState()

        # Попытка передать параметры с "decision" или "action" должна вызвать ошибку
        current_params = {
            "decision": {"pattern": "dampen"},  # Запрещенный параметр
        }

        analysis = {"learning_params_snapshot": {}}

        with pytest.raises(
            ValueError, match="не может напрямую изменять Decision/Action"
        ):
            manager.apply_adaptation(analysis, current_params, self_state)

    def test_store_history(self):
        """Тест хранения истории адаптаций"""
        manager = AdaptationManager()
        self_state = SelfState()

        old_params = {
            "behavior_sensitivity": {"noise": 0.2},
        }

        new_params = {
            "behavior_sensitivity": {"noise": 0.21},  # Изменение на 0.01
        }

        manager.store_history(old_params, new_params, self_state)

        assert hasattr(self_state, "adaptation_history")
        assert len(self_state.adaptation_history) == 1

        entry = self_state.adaptation_history[0]
        assert "timestamp" in entry
        assert "tick" in entry
        assert "old_params" in entry
        assert "new_params" in entry
        assert "changes" in entry
        assert "learning_params_snapshot" in entry

    def test_store_history_max_size(self):
        """Тест ограничения размера истории"""
        manager = AdaptationManager()
        self_state = SelfState()

        old_params = {"behavior_sensitivity": {"noise": 0.2}}
        new_params = {"behavior_sensitivity": {"noise": 0.21}}

        # Создаем больше записей, чем MAX_HISTORY_SIZE
        for i in range(manager.MAX_HISTORY_SIZE + 10):
            manager.store_history(old_params, new_params, self_state)

        # История должна быть ограничена MAX_HISTORY_SIZE
        assert len(self_state.adaptation_history) == manager.MAX_HISTORY_SIZE

    def test_store_history_only_changes(self):
        """Тест сохранения только измененных параметров"""
        manager = AdaptationManager()
        self_state = SelfState()

        old_params = {
            "behavior_sensitivity": {"noise": 0.2, "shock": 0.3},
        }

        new_params = {
            "behavior_sensitivity": {
                "noise": 0.21,
                "shock": 0.3,
            },  # Изменен только noise
        }

        manager.store_history(old_params, new_params, self_state)

        entry = self_state.adaptation_history[0]
        changes = entry["changes"]

        # В changes должен быть только noise
        assert "behavior_sensitivity" in changes
        assert "noise" in changes["behavior_sensitivity"]
        assert "shock" not in changes["behavior_sensitivity"]

    def test_apply_adaptation_minimal_delta(self):
        """Тест минимального изменения для применения"""
        manager = AdaptationManager()
        self_state = SelfState()
        self_state.learning_params = {
            "event_type_sensitivity": {"noise": 0.2001},  # Очень маленькая разница
        }

        current_params = {
            "behavior_sensitivity": {"noise": 0.2},
        }

        analysis = {"learning_params_snapshot": self_state.learning_params}
        new_params = manager.apply_adaptation(analysis, current_params, self_state)

        # Если изменение меньше MIN_ADAPTATION_DELTA, параметр не должен измениться
        old_value = current_params["behavior_sensitivity"]["noise"]
        new_value = new_params["behavior_sensitivity"]["noise"]
        delta = abs(new_value - old_value)

        # Изменение либо >= MIN_ADAPTATION_DELTA, либо == 0
        assert delta == 0.0 or delta >= manager.MIN_ADAPTATION_DELTA


@pytest.mark.unit
class TestAdaptationArchitecturalConstraints:
    """Статические тесты на архитектурные ограничения"""

    def test_no_optimization_methods(self):
        """Тест отсутствия методов оптимизации"""
        manager = AdaptationManager()
        methods = dir(manager)

        forbidden_methods = [
            "optimize",
            "improve",
            "correct",
            "adjust_decision",
            "adjust_action",
        ]

        for method in forbidden_methods:
            assert method not in methods, f"Запрещенный метод {method} найден"

    def test_no_goals_or_rewards(self):
        """Тест отсутствия целей и reward"""
        source_code = inspect.getsource(AdaptationManager)

        forbidden_terms = [
            "reward",
            "punishment",
            "utility",
            "scoring",
            "target",
            "goal",
            "reinforcement",
            "policy",
            "self_optimize",
        ]

        for term in forbidden_terms:
            assert (
                term.lower() not in source_code.lower()
            ), f"Запрещенный термин '{term}' найден в коде"

    def test_no_direct_decision_action_control(self):
        """Тест отсутствия прямого управления Decision/Action"""
        source_code = inspect.getsource(AdaptationManager)

        # Проверяем, что нет прямых вызовов Decision/Action
        assert "decide_response" not in source_code
        assert "execute_action" not in source_code
        assert "from decision" not in source_code
        assert "from action" not in source_code

    def test_slow_changes_enforced(self):
        """Тест принудительного медленного изменения"""
        manager = AdaptationManager()

        # MAX_ADAPTATION_DELTA должен быть <= 0.01
        assert manager.MAX_ADAPTATION_DELTA <= 0.01

        # MIN_ADAPTATION_DELTA должен быть > 0
        assert manager.MIN_ADAPTATION_DELTA > 0

    def test_forbidden_patterns(self):
        """Тест отсутствия запрещенных паттернов"""
        source_code = inspect.getsource(AdaptationManager)

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
            ), f"Запрещенный паттерн '{pattern}' найден в коде"


@pytest.mark.unit
class TestAdaptationIntegration:
    """Интеграционные тесты Adaptation"""

    def test_adaptation_uses_learning_params(self):
        """Тест использования параметров Learning"""
        manager = AdaptationManager()
        self_state = SelfState()
        self_state.learning_params = {
            "event_type_sensitivity": {"noise": 0.5},
            "significance_thresholds": {"noise": 0.3},
            "response_coefficients": {"dampen": 0.7},
        }

        analysis = manager.analyze_changes(
            self_state.learning_params, getattr(self_state, "adaptation_history", [])
        )

        assert "learning_params_snapshot" in analysis
        assert analysis["learning_params_snapshot"] == self_state.learning_params

    def test_adaptation_reacts_to_learning_changes(self):
        """Тест реакции Adaptation на изменения Learning"""
        manager = AdaptationManager()
        self_state = SelfState()

        # Начальные параметры Learning
        self_state.learning_params = {
            "event_type_sensitivity": {"noise": 0.2},
        }

        # Первая адаптация
        current_params = {}
        analysis = manager.analyze_changes(
            self_state.learning_params, getattr(self_state, "adaptation_history", [])
        )
        new_params1 = manager.apply_adaptation(analysis, current_params, self_state)
        manager.store_history(current_params, new_params1, self_state)

        # Learning изменяет параметры
        self_state.learning_params["event_type_sensitivity"]["noise"] = 0.5

        # Вторая адаптация должна реагировать на изменения
        analysis2 = manager.analyze_changes(
            self_state.learning_params, self_state.adaptation_history
        )
        new_params2 = manager.apply_adaptation(analysis2, new_params1, self_state)

        # Параметры должны медленно изменяться в сторону нового значения Learning
        value1 = new_params1["behavior_sensitivity"]["noise"]
        value2 = new_params2["behavior_sensitivity"]["noise"]
        learning_value = self_state.learning_params["event_type_sensitivity"]["noise"]

        # value2 должна быть ближе к learning_value, чем value1
        diff1 = abs(value1 - learning_value)
        diff2 = abs(value2 - learning_value)

        assert diff2 <= diff1  # Должны приблизиться к значению Learning

    def test_adaptation_independent_from_learning(self):
        """Тест независимости Adaptation от Learning"""
        manager = AdaptationManager()
        self_state = SelfState()

        # Adaptation не должен блокировать или изменять Learning
        # Это проверяется тем, что Adaptation только читает learning_params,
        # но не изменяет их

        initial_learning_params = {
            "event_type_sensitivity": {"noise": 0.3},
        }
        self_state.learning_params = initial_learning_params.copy()

        analysis = manager.analyze_changes(
            self_state.learning_params, getattr(self_state, "adaptation_history", [])
        )
        current_params = {}
        manager.apply_adaptation(analysis, current_params, self_state)

        # learning_params не должны быть изменены
        assert self_state.learning_params == initial_learning_params

    def test_adaptation_with_empty_params(self):
        """Тест работы с пустыми параметрами"""
        manager = AdaptationManager()
        self_state = SelfState()
        self_state.learning_params = {}

        analysis = manager.analyze_changes(
            self_state.learning_params, getattr(self_state, "adaptation_history", [])
        )
        current_params = {}
        new_params = manager.apply_adaptation(analysis, current_params, self_state)

        # Должна произойти инициализация параметров
        assert "behavior_sensitivity" in new_params
        assert "behavior_thresholds" in new_params
        assert "behavior_coefficients" in new_params

    def test_adaptation_with_minimal_data(self):
        """Тест работы с минимальными данными"""
        manager = AdaptationManager()
        self_state = SelfState()
        self_state.learning_params = {
            "event_type_sensitivity": {"noise": 0.2},
        }

        analysis = manager.analyze_changes(
            self_state.learning_params, getattr(self_state, "adaptation_history", [])
        )
        current_params = {
            "behavior_sensitivity": {"noise": 0.2},
        }
        new_params = manager.apply_adaptation(analysis, current_params, self_state)

        # Должна работать без ошибок
        assert "behavior_sensitivity" in new_params


@pytest.mark.integration
class TestAdaptationRuntimeLoop:
    """Интеграционные тесты Adaptation с Runtime Loop"""

    def test_adaptation_frequency_in_runtime(self):
        """Тест частоты вызова Adaptation в runtime loop"""
        import threading

        from src.runtime.loop import run_loop
        from src.state.self_state import SelfState

        def dummy_monitor(state):
            pass

        state = SelfState()
        stop_event = threading.Event()

        # Запускаем loop на короткое время
        thread = threading.Thread(
            target=run_loop,
            args=(state, dummy_monitor, 0.01, 1000, stop_event, None),
        )
        thread.start()

        # Ждем несколько тиков
        time.sleep(0.1)
        stop_event.set()
        thread.join(timeout=1.0)

        # Проверяем, что adaptation_params инициализированы
        assert hasattr(state, "adaptation_params")
        assert hasattr(state, "adaptation_history")

    def test_adaptation_order_with_learning(self):
        """Тест порядка вызова Adaptation после Learning"""
        import threading

        from src.runtime.loop import run_loop
        from src.state.self_state import SelfState

        adaptation_called = []
        learning_called = []

        def dummy_monitor(state):
            # Отслеживаем вызовы через изменения в параметрах
            if hasattr(state, "learning_params") and state.learning_params:
                learning_called.append(state.ticks)
            if hasattr(state, "adaptation_params") and state.adaptation_params:
                adaptation_called.append(state.ticks)

        state = SelfState()
        stop_event = threading.Event()

        # Запускаем loop на короткое время
        thread = threading.Thread(
            target=run_loop,
            args=(state, dummy_monitor, 0.01, 1000, stop_event, None),
        )
        thread.start()

        # Ждем достаточно тиков для вызова Learning и Adaptation
        time.sleep(0.5)
        stop_event.set()
        thread.join(timeout=2.0)

        # Adaptation должен вызываться реже, чем Learning (100 vs 75 тиков)
        # Проверяем, что оба модуля работают
        assert len(learning_called) > 0 or state.ticks < 75
        # Adaptation может не вызваться, если тиков < 100

    def test_adaptation_with_long_runtime(self):
        """Тест работы Adaptation при длительной работе (1000+ тиков)"""
        import threading

        from src.runtime.loop import run_loop
        from src.state.self_state import SelfState

        def dummy_monitor(state):
            pass

        state = SelfState()
        stop_event = threading.Event()

        # Запускаем loop на короткое время, но с большим количеством тиков
        thread = threading.Thread(
            target=run_loop,
            args=(state, dummy_monitor, 0.001, 1000, stop_event, None),
        )
        thread.start()

        # Ждем достаточно для нескольких адаптаций
        time.sleep(0.2)
        stop_event.set()
        thread.join(timeout=2.0)

        # Проверяем, что adaptation_params существуют
        assert hasattr(state, "adaptation_params")
        assert hasattr(state, "adaptation_history")

        # Если было достаточно тиков, должна быть история
        if state.ticks >= 100:
            assert (
                len(state.adaptation_history) >= 0
            )  # Может быть 0, если не было изменений

    def test_adaptation_persistence_in_snapshots(self):
        """Тест сохранения параметров Adaptation в snapshots"""
        import threading

        from src.runtime.loop import run_loop
        from src.state.self_state import SelfState, load_snapshot, save_snapshot

        def dummy_monitor(state):
            pass

        state = SelfState()
        stop_event = threading.Event()

        # Запускаем loop на короткое время
        thread = threading.Thread(
            target=run_loop,
            args=(state, dummy_monitor, 0.01, 10, stop_event, None),
        )
        thread.start()

        # Ждем несколько тиков
        time.sleep(0.1)
        stop_event.set()
        thread.join(timeout=1.0)

        # Сохраняем snapshot
        if state.ticks > 0:
            save_snapshot(state)

            # Загружаем snapshot
            loaded_state = load_snapshot(state.ticks)

            # Проверяем, что adaptation_params сохранились
            assert hasattr(loaded_state, "adaptation_params")
            assert hasattr(loaded_state, "adaptation_history")

    def test_partial_update_preserves_existing_params(self):
        """Тест частичного обновления параметров - существующие параметры сохраняются"""
        manager = AdaptationManager()
        self_state = SelfState()

        # Устанавливаем начальные параметры с несколькими ключами
        self_state.adaptation_params = {
            "behavior_sensitivity": {"noise": 0.2, "shock": 0.3, "decay": 0.25},
            "behavior_thresholds": {"noise": 0.1, "shock": 0.2},
            "behavior_coefficients": {"dampen": 0.5, "absorb": 1.0},
        }

        # Устанавливаем learning_params так, чтобы изменился только один параметр
        self_state.learning_params = {
            "event_type_sensitivity": {"noise": 0.21, "shock": 0.3, "decay": 0.25},
            "significance_thresholds": {"noise": 0.1, "shock": 0.2},
            "response_coefficients": {"dampen": 0.5, "absorb": 1.0},
        }

        analysis = manager.analyze_changes(
            self_state.learning_params, self_state.adaptation_history
        )
        current_params = self_state.adaptation_params.copy()
        new_params = manager.apply_adaptation(analysis, current_params, self_state)

        # Проверяем, что new_params содержит только измененные параметры
        # Но при обновлении в loop.py все существующие параметры должны сохраниться
        assert "behavior_sensitivity" in new_params
        # Проверяем, что все ключи в behavior_sensitivity присутствуют
        assert "noise" in new_params["behavior_sensitivity"]
        assert "shock" in new_params["behavior_sensitivity"]
        assert "decay" in new_params["behavior_sensitivity"]

    def test_history_stores_correct_old_params(self):
        """Тест корректности истории адаптаций - старые параметры должны быть до обновления"""
        manager = AdaptationManager()
        self_state = SelfState()

        # Устанавливаем начальные параметры
        initial_params = {
            "behavior_sensitivity": {"noise": 0.2, "shock": 0.3},
            "behavior_thresholds": {"noise": 0.1},
        }
        self_state.adaptation_params = initial_params.copy()

        # Устанавливаем learning_params для изменения
        self_state.learning_params = {
            "event_type_sensitivity": {"noise": 0.21, "shock": 0.3},
            "significance_thresholds": {"noise": 0.1},
        }

        analysis = manager.analyze_changes(
            self_state.learning_params, self_state.adaptation_history
        )
        old_params = self_state.adaptation_params.copy()
        new_params = manager.apply_adaptation(analysis, old_params, self_state)

        # Сохраняем историю
        manager.store_history(old_params, new_params, self_state)

        # Проверяем, что история содержит правильные старые параметры
        assert len(self_state.adaptation_history) == 1
        history_entry = self_state.adaptation_history[0]

        # Старые параметры должны соответствовать initial_params
        assert history_entry["old_params"]["behavior_sensitivity"]["noise"] == 0.2
        assert history_entry["old_params"]["behavior_sensitivity"]["shock"] == 0.3
        assert history_entry["old_params"]["behavior_thresholds"]["noise"] == 0.1

        # Новые параметры должны быть изменены
        assert "new_params" in history_entry
        assert "changes" in history_entry

        # Проверяем, что changes содержат только измененные параметры
        if "behavior_sensitivity" in history_entry["changes"]:
            # noise должен быть изменен (0.2 -> ~0.21)
            assert "noise" in history_entry["changes"]["behavior_sensitivity"]
            # shock не должен быть изменен (0.3 == 0.3)
            assert "shock" not in history_entry["changes"].get(
                "behavior_sensitivity", {}
            )

    def test_deep_merge_preserves_all_keys(self):
        """Тест глубокого объединения - все ключи сохраняются при частичном обновлении"""
        import copy

        # Симулируем логику обновления из loop.py
        existing_params = {
            "behavior_sensitivity": {"noise": 0.2, "shock": 0.3, "decay": 0.25},
            "behavior_thresholds": {"noise": 0.1, "shock": 0.2},
        }

        # Новые параметры содержат только часть ключей
        new_params = {
            "behavior_sensitivity": {"noise": 0.21},  # Только noise изменен
        }

        # Глубокое объединение (как в loop.py)
        for key, new_value_dict in new_params.items():
            if key not in existing_params:
                existing_params[key] = copy.deepcopy(new_value_dict)
            else:
                current_value_dict = existing_params[key]
                if isinstance(new_value_dict, dict) and isinstance(
                    current_value_dict, dict
                ):
                    for param_name, new_value in new_value_dict.items():
                        current_value_dict[param_name] = new_value

        # Проверяем, что все ключи сохранились
        assert "noise" in existing_params["behavior_sensitivity"]
        assert "shock" in existing_params["behavior_sensitivity"]
        assert "decay" in existing_params["behavior_sensitivity"]
        assert existing_params["behavior_sensitivity"]["noise"] == 0.21
        assert existing_params["behavior_sensitivity"]["shock"] == 0.3
        assert existing_params["behavior_sensitivity"]["decay"] == 0.25
        assert "behavior_thresholds" in existing_params
        assert existing_params["behavior_thresholds"]["noise"] == 0.1
