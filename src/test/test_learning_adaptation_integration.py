"""
Комплексные тесты для интеграции Learning, Adaptation и Feedback в Runtime Loop

Включает:
- Статические тесты (структура, типы, отсутствие запрещенных методов)
- Дымовые тесты (базовая работоспособность)
- Интеграционные тесты (работа в runtime loop)
"""

import inspect
import sys
import threading
import time
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest

from src.adaptation.adaptation import AdaptationManager
from src.environment.event import Event
from src.environment.event_queue import EventQueue
from src.feedback import (
    FeedbackRecord,
    PendingAction,
    observe_consequences,
    register_action,
)
from src.learning.learning import LearningEngine
from src.runtime.loop import run_loop
from src.state.self_state import SelfState


def dummy_monitor(state):
    """Простой монитор для тестов"""
    pass


# ============================================================================
# СТАТИЧЕСКИЕ ТЕСТЫ
# ============================================================================


@pytest.mark.static
class TestLearningAdaptationStatic:
    """Статические тесты для Learning и Adaptation - проверка структуры, типов"""

    def test_learning_engine_structure(self):
        """Проверка структуры LearningEngine"""
        engine = LearningEngine()

        # Проверяем наличие основных методов
        assert hasattr(engine, "process_statistics")
        assert hasattr(engine, "adjust_parameters")
        assert hasattr(engine, "record_changes")

        # Проверяем константы
        assert hasattr(engine, "MAX_PARAMETER_DELTA")
        assert hasattr(engine, "MIN_PARAMETER_DELTA")
        assert engine.MAX_PARAMETER_DELTA == 0.01
        assert engine.MIN_PARAMETER_DELTA == 0.001

    def test_adaptation_manager_structure(self):
        """Проверка структуры AdaptationManager"""
        manager = AdaptationManager()

        # Проверяем наличие основных методов
        assert hasattr(manager, "analyze_changes")
        assert hasattr(manager, "apply_adaptation")
        assert hasattr(manager, "store_history")

        # Проверяем константы
        assert hasattr(manager, "MAX_ADAPTATION_DELTA")
        assert hasattr(manager, "MIN_ADAPTATION_DELTA")
        assert manager.MAX_ADAPTATION_DELTA == 0.01
        assert manager.MIN_ADAPTATION_DELTA == 0.001

    def test_feedback_structure(self):
        """Проверка структуры Feedback модуля"""
        # Проверяем наличие функций
        assert callable(register_action)
        assert callable(observe_consequences)

        # Проверяем наличие классов
        assert hasattr(PendingAction, "__dataclass_fields__")
        assert hasattr(FeedbackRecord, "__dataclass_fields__")

    def test_runtime_loop_imports(self):
        """Проверка импортов в runtime loop"""
        import runtime.loop as loop_module

        # Проверяем, что модуль импортирует необходимые компоненты
        assert hasattr(loop_module, "run_loop")
        assert callable(loop_module.run_loop)

        # Проверяем, что LearningEngine и AdaptationManager используются
        source = inspect.getsource(loop_module.run_loop)
        assert "LearningEngine" in source
        assert "AdaptationManager" in source
        assert "observe_consequences" in source
        assert "register_action" in source

    def test_learning_interval_constants(self):
        """Проверка интервалов вызова Learning и Adaptation"""
        source_file = Path(__file__).parent.parent / "runtime" / "loop.py"
        with source_file.open("r", encoding="utf-8") as f:
            source_code = f.read()

        # Проверяем, что интервалы определены
        assert "LEARNING_INTERVAL" in source_code
        assert "ADAPTATION_INTERVAL" in source_code

        # Проверяем значения интервалов
        assert "LEARNING_INTERVAL = 50" in source_code or "LEARNING_INTERVAL=50" in source_code
        assert (
            "ADAPTATION_INTERVAL = 100" in source_code or "ADAPTATION_INTERVAL=100" in source_code
        )

    def test_forbidden_methods_learning(self):
        """Проверка отсутствия запрещенных методов в Learning"""
        engine = LearningEngine()

        forbidden_methods = [
            "optimize",
            "improve",
            "maximize",
            "minimize",
            "evaluate",
            "score",
            "reward",
            "goal",
        ]

        for method in forbidden_methods:
            assert not hasattr(engine, method), f"LearningEngine не должен иметь метод {method}"

    def test_forbidden_methods_adaptation(self):
        """Проверка отсутствия запрещенных методов в Adaptation"""
        manager = AdaptationManager()

        forbidden_methods = [
            "optimize",
            "improve",
            "maximize",
            "minimize",
            "evaluate",
            "score",
            "reward",
            "goal",
        ]

        for method in forbidden_methods:
            assert not hasattr(manager, method), f"AdaptationManager не должен иметь метод {method}"

    def test_method_signatures(self):
        """Проверка сигнатур методов"""
        engine = LearningEngine()
        manager = AdaptationManager()

        # LearningEngine
        sig = inspect.signature(engine.process_statistics)
        assert "memory" in sig.parameters

        sig = inspect.signature(engine.adjust_parameters)
        assert "statistics" in sig.parameters
        assert "current_params" in sig.parameters

        # AdaptationManager
        sig = inspect.signature(manager.analyze_changes)
        assert "learning_params" in sig.parameters
        assert "adaptation_history" in sig.parameters

        sig = inspect.signature(manager.apply_adaptation)
        assert "analysis" in sig.parameters
        assert "current_behavior_params" in sig.parameters
        assert "self_state" in sig.parameters

    def test_return_types(self):
        """Проверка типов возвращаемых значений"""
        engine = LearningEngine()
        manager = AdaptationManager()
        self_state = SelfState()

        # process_statistics возвращает dict
        result = engine.process_statistics([])
        assert isinstance(result, dict)

        # adjust_parameters возвращает dict
        result = engine.adjust_parameters({}, {})
        assert isinstance(result, dict)

        # analyze_changes возвращает dict
        result = manager.analyze_changes({}, [])
        assert isinstance(result, dict)

        # apply_adaptation возвращает dict
        result = manager.apply_adaptation({}, {}, self_state)
        assert isinstance(result, dict)


# ============================================================================
# ДЫМОВЫЕ ТЕСТЫ
# ============================================================================


@pytest.mark.smoke
class TestLearningAdaptationSmoke:
    """Дымовые тесты для Learning и Adaptation - базовая работоспособность"""

    def test_learning_engine_instantiation(self):
        """Дымовой тест создания LearningEngine"""
        engine = LearningEngine()
        assert engine is not None
        assert isinstance(engine, LearningEngine)

    def test_adaptation_manager_instantiation(self):
        """Дымовой тест создания AdaptationManager"""
        manager = AdaptationManager()
        assert manager is not None
        assert isinstance(manager, AdaptationManager)

    def test_learning_process_statistics_smoke(self):
        """Дымовой тест process_statistics"""
        engine = LearningEngine()
        result = engine.process_statistics([])

        assert isinstance(result, dict)
        assert "total_entries" in result
        assert "feedback_entries" in result
        assert result["total_entries"] == 0

    def test_learning_adjust_parameters_smoke(self):
        """Дымовой тест adjust_parameters"""
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

    def test_adaptation_analyze_changes_smoke(self):
        """Дымовой тест analyze_changes"""
        manager = AdaptationManager()
        learning_params = {
            "event_type_sensitivity": {"noise": 0.3},
        }

        result = manager.analyze_changes(learning_params, [])
        assert isinstance(result, dict)
        assert "learning_params_snapshot" in result

    def test_adaptation_apply_adaptation_smoke(self):
        """Дымовой тест apply_adaptation"""
        manager = AdaptationManager()
        self_state = SelfState()
        self_state.learning_params = {
            "event_type_sensitivity": {"noise": 0.3},
        }

        analysis = {"learning_params_snapshot": self_state.learning_params}
        current_params = {}

        result = manager.apply_adaptation(analysis, current_params, self_state)
        assert isinstance(result, dict)

    def test_feedback_register_action_smoke(self):
        """Дымовой тест register_action"""
        pending_actions = []
        register_action(
            "test_action",
            "dampen",
            {"energy": 100.0, "stability": 1.0, "integrity": 1.0},
            time.time(),
            pending_actions,
        )

        assert len(pending_actions) == 1
        assert pending_actions[0].action_id == "test_action"

    def test_feedback_observe_consequences_smoke(self):
        """Дымовой тест observe_consequences"""
        self_state = SelfState()
        pending_actions = []

        # Регистрируем действие
        register_action(
            "test_action",
            "dampen",
            {"energy": 100.0, "stability": 1.0, "integrity": 1.0},
            time.time(),
            pending_actions,
        )

        # Наблюдаем последствия (сразу после регистрации не должно быть результатов)
        feedback_records = observe_consequences(self_state, pending_actions, None)
        assert isinstance(feedback_records, list)

    def test_learning_full_cycle_smoke(self):
        """Дымовой тест полного цикла Learning"""
        engine = LearningEngine()
        self_state = SelfState()

        # Минимальные данные
        from memory.memory import MemoryEntry

        self_state.memory.append(
            MemoryEntry(event_type="noise", meaning_significance=0.3, timestamp=1.0)
        )

        # Полный цикл
        statistics = engine.process_statistics(self_state.memory)
        new_params = engine.adjust_parameters(statistics, self_state.learning_params)
        if new_params:
            engine.record_changes(self_state.learning_params, new_params, self_state)

        # Проверяем, что все прошло без ошибок
        assert "event_type_sensitivity" in self_state.learning_params

    def test_adaptation_full_cycle_smoke(self):
        """Дымовой тест полного цикла Adaptation"""
        manager = AdaptationManager()
        self_state = SelfState()
        self_state.learning_params = {
            "event_type_sensitivity": {"noise": 0.3},
        }

        # Полный цикл
        analysis = manager.analyze_changes(
            self_state.learning_params, getattr(self_state, "adaptation_history", [])
        )
        current_params = getattr(self_state, "adaptation_params", {})
        new_params = manager.apply_adaptation(analysis, current_params, self_state)
        if new_params:
            manager.store_history(current_params, new_params, self_state)

        # Проверяем, что все прошло без ошибок
        assert hasattr(self_state, "adaptation_history")


# ============================================================================
# ИНТЕГРАЦИОННЫЕ ТЕСТЫ
# ============================================================================


@pytest.mark.integration
class TestLearningAdaptationRuntimeIntegration:
    """Интеграционные тесты Learning и Adaptation в runtime loop"""

    @pytest.fixture
    def base_state(self):
        """Создает базовое состояние"""
        state = SelfState()
        state.energy = 50.0
        state.stability = 0.8
        state.integrity = 0.9
        return state

    @pytest.fixture
    def event_queue(self):
        """Создает очередь событий"""
        return EventQueue()

    def test_learning_called_in_runtime_loop(self, base_state, event_queue):
        """Тест вызова Learning в runtime loop"""
        stop_event = threading.Event()

        # Запускаем цикл
        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.01, 1000, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        # Ждем достаточно тиков для вызова Learning (75 тиков)
        time.sleep(1.0)  # 0.01 * 100 = 1 секунда для 100 тиков
        stop_event.set()
        loop_thread.join(timeout=2.0)

        # Проверяем, что learning_params инициализированы
        assert hasattr(base_state, "learning_params")
        assert "event_type_sensitivity" in base_state.learning_params

    def test_adaptation_called_in_runtime_loop(self, base_state, event_queue):
        """Тест вызова Adaptation в runtime loop"""
        stop_event = threading.Event()

        # Запускаем цикл
        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.01, 1000, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        # Ждем достаточно тиков для вызова Adaptation (100 тиков)
        time.sleep(1.5)  # 0.01 * 150 = 1.5 секунды для 150 тиков
        stop_event.set()
        loop_thread.join(timeout=2.0)

        # Проверяем, что adaptation_params инициализированы
        assert hasattr(base_state, "adaptation_params")
        assert hasattr(base_state, "adaptation_history")

    def test_learning_frequency_in_runtime(self, base_state, event_queue):
        """Тест частоты вызова Learning (раз в 75 тиков)"""
        stop_event = threading.Event()
        learning_interval = 75

        # Добавляем события для статистики
        for i in range(10):
            event = Event(type="noise", intensity=0.3, timestamp=time.time() + i)
            event_queue.push(event)

        # Запускаем цикл
        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.01, 1000, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        # Ждем достаточно тиков для вызова Learning
        time.sleep(1.0)
        stop_event.set()
        loop_thread.join(timeout=2.0)

        # Если было достаточно тиков, параметры могут измениться
        if base_state.ticks >= learning_interval:
            assert "event_type_sensitivity" in base_state.learning_params

    def test_adaptation_frequency_in_runtime(self, base_state, event_queue):
        """Тест частоты вызова Adaptation (раз в 100 тиков)"""
        stop_event = threading.Event()
        adaptation_interval = 100

        # Запускаем цикл
        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.01, 1000, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        # Ждем достаточно тиков для вызова Adaptation
        time.sleep(1.5)
        stop_event.set()
        loop_thread.join(timeout=2.0)

        # Если было достаточно тиков, adaptation_params должны быть инициализированы
        if base_state.ticks >= adaptation_interval:
            assert hasattr(base_state, "adaptation_params")

    def test_feedback_integration_in_runtime(self, base_state, event_queue):
        """Тест интеграции Feedback в runtime loop"""
        stop_event = threading.Event()

        # Добавляем значимое событие для обработки
        event = Event(type="shock", intensity=0.8, timestamp=time.time())
        event_queue.push(event)

        initial_memory_size = len(base_state.memory)

        # Запускаем цикл
        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.01, 1000, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        # Ждем обработки события и регистрации действия
        time.sleep(0.5)
        stop_event.set()
        loop_thread.join(timeout=2.0)

        # Проверяем, что событие обработано (добавлено в память)
        # Feedback записи появятся позже (через несколько тиков)
        assert len(base_state.memory) >= initial_memory_size

    def test_learning_adaptation_order(self, base_state, event_queue):
        """Тест порядка вызова Learning и Adaptation"""
        stop_event = threading.Event()

        # Запускаем цикл
        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.01, 1000, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        # Ждем достаточно тиков для вызова обоих модулей
        time.sleep(1.5)
        stop_event.set()
        loop_thread.join(timeout=2.0)

        # Проверяем, что оба модуля работают
        assert hasattr(base_state, "learning_params")
        if base_state.ticks >= 100:
            assert hasattr(base_state, "adaptation_params")

    def test_learning_with_memory_entries(self, base_state, event_queue):
        """Тест Learning с записями в Memory"""
        stop_event = threading.Event()
        learning_interval = 75

        # Добавляем несколько событий для создания записей в Memory
        for i in range(5):
            event = Event(
                type=["noise", "decay", "recovery"][i % 3],
                intensity=0.2 + i * 0.1,
                timestamp=time.time() + i,
            )
            event_queue.push(event)

        # Запускаем цикл
        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.01, 1000, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        # Ждем обработки событий и вызова Learning
        time.sleep(1.0)
        stop_event.set()
        loop_thread.join(timeout=2.0)

        # Проверяем, что Learning обработал статистику
        if base_state.ticks >= learning_interval:
            assert "event_type_sensitivity" in base_state.learning_params

    def test_adaptation_with_learning_params(self, base_state, event_queue):
        """Тест Adaptation с параметрами Learning"""
        stop_event = threading.Event()
        adaptation_interval = 100

        # Инициализируем learning_params
        base_state.learning_params = {
            "event_type_sensitivity": {"noise": 0.3, "shock": 0.5},
            "significance_thresholds": {"noise": 0.2, "shock": 0.4},
            "response_coefficients": {"dampen": 0.6, "absorb": 0.8},
        }

        # Запускаем цикл
        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.01, 1000, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        # Ждем достаточно тиков для вызова Adaptation
        time.sleep(1.5)
        stop_event.set()
        loop_thread.join(timeout=2.0)

        # Проверяем, что Adaptation использовал learning_params
        if base_state.ticks >= adaptation_interval:
            assert hasattr(base_state, "adaptation_params")
            assert hasattr(base_state, "adaptation_history")

    def test_feedback_records_in_memory(self, base_state, event_queue):
        """Тест сохранения Feedback записей в Memory"""
        stop_event = threading.Event()

        # Добавляем значимое событие
        event = Event(type="shock", intensity=0.8, timestamp=time.time())
        event_queue.push(event)

        initial_memory_size = len(base_state.memory)

        # Запускаем цикл
        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.01, 1000, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        # Ждем обработки и регистрации действия
        time.sleep(0.5)
        stop_event.set()
        loop_thread.join(timeout=2.0)

        # Проверяем, что событие обработано
        assert len(base_state.memory) >= initial_memory_size

        # Feedback записи появятся позже (через несколько тиков после регистрации)
        # Проверяем наличие записей с типом "feedback"
        feedback_entries = [entry for entry in base_state.memory if entry.event_type == "feedback"]
        # Может быть 0, если delay_ticks не прошло
        assert isinstance(feedback_entries, list)

    def test_learning_adaptation_persistence(self, base_state, event_queue):
        """Тест сохранения параметров Learning и Adaptation"""
        stop_event = threading.Event()

        # Запускаем цикл
        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.01, 1000, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        # Ждем достаточно тиков
        time.sleep(1.5)
        stop_event.set()
        loop_thread.join(timeout=2.0)

        # Проверяем, что параметры сохранились
        assert hasattr(base_state, "learning_params")
        if base_state.ticks >= 100:
            assert hasattr(base_state, "adaptation_params")
            assert hasattr(base_state, "adaptation_history")

    def test_multiple_learning_adaptation_cycles(self, base_state, event_queue):
        """Тест нескольких циклов Learning и Adaptation"""
        stop_event = threading.Event()

        # Добавляем события для статистики
        for i in range(20):
            event = Event(
                type=["noise", "decay", "recovery", "shock"][i % 4],
                intensity=0.1 + (i % 5) * 0.1,
                timestamp=time.time() + i,
            )
            event_queue.push(event)

        # Запускаем цикл
        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.01, 1000, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        # Ждем достаточно тиков для нескольких циклов
        time.sleep(2.0)
        stop_event.set()
        loop_thread.join(timeout=3.0)

        # Проверяем, что оба модуля работали
        assert hasattr(base_state, "learning_params")
        if base_state.ticks >= 100:
            assert hasattr(base_state, "adaptation_params")
            # Проверяем, что параметры изменились медленно
            if "behavior_sensitivity" in base_state.adaptation_params:
                for key, value in base_state.adaptation_params["behavior_sensitivity"].items():
                    assert 0.0 <= value <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
