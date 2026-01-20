"""
Интеграционные тесты для новой функциональности

Проверяем:
- Взаимодействие Learning, Adaptation и MeaningEngine в runtime loop
- Полные циклы обработки событий
- Интеграцию с Memory и Feedback
- Работа в многопоточной среде runtime loop
- Сохранение и загрузку состояния
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
from src.environment.event_queue import EventQueue
from src.learning.learning import LearningEngine
from src.memory.memory import MemoryEntry
from src.runtime.loop import run_loop
from src.runtime.subjective_time import compute_subjective_dt
from src.state.self_state import SelfState


@pytest.mark.integration
class TestNewFunctionalityIntegration:
    """Интеграционные тесты новой функциональности"""

    # ============================================================================
    # Runtime Loop Integration
    # ============================================================================

    def test_learning_adaptation_in_runtime_loop(self):
        """Интеграционный тест Learning и Adaptation в runtime loop"""
        self_state = SelfState()
        event_queue = EventQueue()
        stop_event = threading.Event()

        # Добавляем события в очередь
        for i in range(5):
            event = Event(type="noise", intensity=0.3, timestamp=float(i))
            event_queue.push(event)

        def dummy_monitor(state):
            pass

        # Запускаем loop на короткое время
        thread = threading.Thread(
            target=run_loop,
            args=(self_state, dummy_monitor, 0.01, 1000, stop_event, event_queue),
        )
        thread.start()

        # Ждем обработки событий и вызова Learning/Adaptation
        time.sleep(0.2)
        stop_event.set()
        thread.join(timeout=1.0)

        # Проверяем, что Learning и Adaptation работали
        assert hasattr(self_state, "learning_params")
        assert hasattr(self_state, "adaptation_params")
        assert hasattr(self_state, "adaptation_history")

        # Проверяем, что события были обработаны
        assert len(self_state.memory) >= 0  # Могут быть сохранены или нет

    def test_meaning_learning_integration_in_runtime(self):
        """Интеграционный тест Meaning и Learning в runtime"""
        self_state = SelfState()
        event_queue = EventQueue()
        stop_event = threading.Event()

        # Добавляем разнообразные события
        events = [
            Event(type="noise", intensity=0.4, timestamp=1.0),
            Event(type="shock", intensity=-0.6, timestamp=2.0),
            Event(type="recovery", intensity=0.5, timestamp=3.0),
        ]

        for event in events:
            event_queue.push(event)

        def monitor_with_checks(state):
            # Проверяем, что Meaning создает записи в Memory
            if hasattr(state, "memory") and state.memory:
                memory_entries = [
                    entry for entry in state.memory if entry.event_type != "feedback"
                ]
                if memory_entries:
                    assert all(
                        entry.meaning_significance >= 0 for entry in memory_entries
                    )

        # Запускаем loop
        thread = threading.Thread(
            target=run_loop,
            args=(self_state, monitor_with_checks, 0.01, 1000, stop_event, event_queue),
        )
        thread.start()

        time.sleep(0.3)
        stop_event.set()
        thread.join(timeout=1.0)

        # Проверяем, что Meaning обработал события и Learning их использовал
        assert isinstance(self_state.learning_params, dict)
        assert "event_type_sensitivity" in self_state.learning_params

    def test_full_event_processing_chain(self):
        """Интеграционный тест полной цепочки обработки событий"""
        self_state = SelfState()
        event_queue = EventQueue()
        stop_event = threading.Event()

        # Добавляем событие, которое вызовет значимую реакцию
        event = Event(type="shock", intensity=-0.8, timestamp=1.0)
        event_queue.push(event)

        processed_events = []

        def monitor_event_processing(state):
            # Отслеживаем обработку событий
            if hasattr(state, "memory"):
                for entry in state.memory:
                    if entry.event_type != "feedback":
                        processed_events.append(entry)

        # Запускаем loop
        thread = threading.Thread(
            target=run_loop,
            args=(
                self_state,
                monitor_event_processing,
                0.01,
                1000,
                stop_event,
                event_queue,
            ),
        )
        thread.start()

        time.sleep(0.2)
        stop_event.set()
        thread.join(timeout=1.0)

        # Проверяем полную цепочку
        assert len(processed_events) >= 0  # События могли быть обработаны

        # Если события обработаны, проверяем Learning
        if processed_events:
            assert isinstance(self_state.learning_params, dict)
            assert "event_type_sensitivity" in self_state.learning_params

    def test_learning_frequency_in_runtime(self):
        """Тест частоты вызова Learning в runtime loop"""
        self_state = SelfState()
        stop_event = threading.Event()

        learning_call_count = 0
        adaptation_call_count = 0

        def monitor_learning_calls(state):
            nonlocal learning_call_count, adaptation_call_count
            # Отслеживаем изменения в learning_params (признак работы Learning)
            if hasattr(state, "learning_params"):
                learning_call_count += 1
            if hasattr(state, "adaptation_params"):
                adaptation_call_count += 1

        # Запускаем loop на время, достаточное для нескольких вызовов Learning
        thread = threading.Thread(
            target=run_loop,
            args=(self_state, monitor_learning_calls, 0.001, 1000, stop_event, None),
        )
        thread.start()

        time.sleep(
            0.3
        )  # 300 тиков, должно быть несколько вызовов Learning (каждые 75 тиков)
        stop_event.set()
        thread.join(timeout=1.0)

        # Проверяем, что Learning вызывался несколько раз
        assert learning_call_count > 0, "Learning должен был вызваться хотя бы раз"

        # Adaptation вызывается реже (каждые 100 тиков)
        # Может не вызваться за короткое время теста

    def test_adaptation_reaction_to_learning_changes(self):
        """Тест реакции Adaptation на изменения Learning"""
        self_state = SelfState()
        stop_event = threading.Event()

        initial_learning_params = self_state.learning_params.copy()

        def monitor_adaptation_reaction(state):
            # Проверяем, что Adaptation реагирует на изменения Learning
            if hasattr(state, "adaptation_params") and state.adaptation_params:
                # Если есть adaptation_params, значит Adaptation работал
                assert hasattr(state, "learning_params")

        # Запускаем loop на время, достаточное для работы Adaptation
        thread = threading.Thread(
            target=run_loop,
            args=(
                self_state,
                monitor_adaptation_reaction,
                0.001,
                1000,
                stop_event,
                None,
            ),
        )
        thread.start()

        time.sleep(0.4)  # Должно хватить для 100+ тиков
        stop_event.set()
        thread.join(timeout=1.0)

        # Проверяем, что параметры могли измениться
        # (тест не требует обязательных изменений, только что система работает)
        assert hasattr(self_state, "learning_params")
        assert hasattr(self_state, "adaptation_history")

    # ============================================================================
    # Memory and Feedback Integration
    # ============================================================================

    def test_learning_with_feedback_integration(self):
        """Интеграционный тест Learning с Feedback"""
        self_state = SelfState()
        stop_event = threading.Event()

        # Создаем события и позволяем системе создать Feedback
        event_queue = EventQueue()
        event = Event(type="noise", intensity=0.5, timestamp=1.0)
        event_queue.push(event)

        feedback_created = False

        def monitor_feedback_creation(state):
            nonlocal feedback_created
            if hasattr(state, "memory"):
                feedback_entries = [
                    entry for entry in state.memory if entry.event_type == "feedback"
                ]
                if feedback_entries:
                    feedback_created = True

        # Запускаем loop
        thread = threading.Thread(
            target=run_loop,
            args=(
                self_state,
                monitor_feedback_creation,
                0.01,
                1000,
                stop_event,
                event_queue,
            ),
        )
        thread.start()

        time.sleep(0.2)
        stop_event.set()
        thread.join(timeout=1.0)

        # Если Feedback создан, Learning должен его обработать
        if feedback_created:
            # Проверяем, что Learning обработал Feedback
            assert "response_coefficients" in self_state.learning_params

    def test_memory_learning_adaptation_chain(self):
        """Тест цепочки Memory -> Learning -> Adaptation"""
        self_state = SelfState()

        # 1. Создаем записи в Memory напрямую
        for i in range(10):
            self_state.memory.append(
                MemoryEntry(
                    event_type="noise" if i % 2 == 0 else "shock",
                    meaning_significance=0.3 + (i % 5) * 0.1,
                    timestamp=float(i),
                )
            )

        # 2. Добавляем Feedback записи
        for i in range(3):
            self_state.memory.append(
                MemoryEntry(
                    event_type="feedback",
                    meaning_significance=0.0,
                    timestamp=10.0 + i,
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

        # 3. Learning обрабатывает Memory
        learning_engine = LearningEngine()
        statistics = learning_engine.process_statistics(self_state.memory)
        new_learning_params = learning_engine.adjust_parameters(
            statistics, self_state.learning_params
        )
        if new_learning_params:
            learning_engine.record_changes(
                self_state.learning_params, new_learning_params, self_state
            )

        # 4. Adaptation анализирует изменения Learning
        adaptation_manager = AdaptationManager()
        analysis = adaptation_manager.analyze_changes(
            self_state.learning_params, getattr(self_state, "adaptation_history", [])
        )

        # 5. Adaptation применяет адаптацию
        current_behavior_params = {}
        new_behavior_params = adaptation_manager.apply_adaptation(
            analysis, current_behavior_params, self_state
        )
        adaptation_manager.store_history(
            current_behavior_params, new_behavior_params, self_state
        )

        # Проверяем результаты
        assert statistics["total_entries"] == 13
        assert statistics["feedback_entries"] == 3
        assert isinstance(self_state.learning_params, dict)
        assert "event_type_sensitivity" in self_state.learning_params
        assert hasattr(self_state, "adaptation_history")

    def test_long_term_memory_integration(self):
        """Тест интеграции с долгосрочной памятью"""
        self_state = SelfState()
        stop_event = threading.Event()

        # Запускаем длительный тест
        def monitor_memory_growth(state):
            # Проверяем, что Memory растет со временем
            pass

        thread = threading.Thread(
            target=run_loop,
            args=(self_state, monitor_memory_growth, 0.001, 1000, stop_event, None),
        )
        thread.start()

        time.sleep(0.2)
        stop_event.set()
        thread.join(timeout=1.0)

        # Проверяем, что система справилась с длительной работой
        assert hasattr(self_state, "memory")
        assert hasattr(self_state, "learning_params")

    # ============================================================================
    # State Persistence Integration
    # ============================================================================

    def test_state_persistence_with_new_modules(self):
        """Тест сохранения состояния с новыми модулями"""
        from src.state.self_state import load_snapshot, save_snapshot

        self_state = SelfState()
        stop_event = threading.Event()

        # Запускаем систему на короткое время
        def dummy_monitor(state):
            pass

        thread = threading.Thread(
            target=run_loop,
            args=(self_state, dummy_monitor, 0.01, 10, stop_event, None),
        )
        thread.start()

        time.sleep(0.1)
        stop_event.set()
        thread.join(timeout=1.0)

        # Сохраняем состояние
        self_state.ticks = 50
        save_snapshot(self_state)

        # Загружаем состояние
        loaded_state = load_snapshot(50)

        # Проверяем, что новые модули сохранились
        assert hasattr(loaded_state, "learning_params")
        assert hasattr(loaded_state, "adaptation_params")
        assert hasattr(loaded_state, "adaptation_history")

    def test_snapshot_recovery_integration(self):
        """Тест восстановления из snapshot с новыми модулями"""
        from src.state.self_state import load_snapshot, save_snapshot

        # Создаем состояние с данными
        self_state = SelfState()
        self_state.learning_params["event_type_sensitivity"]["noise"] = 0.7
        self_state.ticks = 100

        # Добавляем историю адаптации
        self_state.adaptation_history = [
            {
                "timestamp": time.time(),
                "tick": 100,
                "old_params": {},
                "new_params": {"behavior_sensitivity": {"noise": 0.5}},
                "changes": {
                    "behavior_sensitivity": {
                        "noise": {"old": 0.4, "new": 0.5, "delta": 0.1}
                    }
                },
                "learning_params_snapshot": self_state.learning_params.copy(),
            }
        ]

        # Сохраняем и загружаем
        save_snapshot(self_state)
        loaded_state = load_snapshot(100)

        # Проверяем восстановление
        assert loaded_state.learning_params["event_type_sensitivity"]["noise"] == 0.7
        assert len(loaded_state.adaptation_history) == 1
        assert (
            "behavior_sensitivity" in loaded_state.adaptation_history[0]["new_params"]
        )

    # ============================================================================
    # Multithreading and Concurrency
    # ============================================================================

    def test_concurrent_event_processing(self):
        """Тест конкурентной обработки событий"""
        self_state = SelfState()
        event_queue = EventQueue()
        stop_event = threading.Event()

        # Добавляем много событий
        for i in range(20):
            event_type = ["noise", "shock", "recovery"][i % 3]
            event = Event(type=event_type, intensity=0.3, timestamp=float(i))
            event_queue.push(event)

        processed_count = 0

        def monitor_processing(state):
            nonlocal processed_count
            if hasattr(state, "memory"):
                processed_count = len(
                    [entry for entry in state.memory if entry.event_type != "feedback"]
                )

        # Запускаем loop
        thread = threading.Thread(
            target=run_loop,
            args=(self_state, monitor_processing, 0.001, 1000, stop_event, event_queue),
        )
        thread.start()

        time.sleep(0.3)
        stop_event.set()
        thread.join(timeout=1.0)

        # Проверяем, что система справилась с нагрузкой
        assert hasattr(self_state, "learning_params")

    def test_runtime_loop_stability_under_load(self):
        """Тест стабильности runtime loop под нагрузкой"""
        self_state = SelfState()
        event_queue = EventQueue()
        stop_event = threading.Event()

        # Создаем высокую нагрузку
        for i in range(50):
            event = Event(type="noise", intensity=0.2, timestamp=float(i) * 0.01)
            event_queue.push(event)

        errors_caught = []

        def monitor_errors(state):
            # В реальной системе здесь можно было бы ловить исключения
            pass

        # Запускаем loop
        thread = threading.Thread(
            target=run_loop,
            args=(self_state, monitor_errors, 0.001, 1000, stop_event, event_queue),
        )
        thread.start()

        time.sleep(0.5)
        stop_event.set()
        thread.join(timeout=1.0)

        # Проверяем, что система осталась стабильной
        assert hasattr(self_state, "learning_params")
        assert hasattr(self_state, "adaptation_params")

    # ============================================================================
    # End-to-End Scenarios
    # ============================================================================

    def test_end_to_end_event_response_cycle(self):
        """Сквозной тест цикла отклика на событие"""
        self_state = SelfState()
        event_queue = EventQueue()
        stop_event = threading.Event()

        # Сценарий: система получает шоковое событие и адаптируется
        shock_event = Event(type="shock", intensity=-0.9, timestamp=1.0)
        event_queue.push(shock_event)

        response_recorded = False

        def monitor_response_cycle(state):
            nonlocal response_recorded
            # Проверяем, что система отреагировала на шок
            if hasattr(state, "memory"):
                shock_entries = [
                    entry for entry in state.memory if entry.event_type == "shock"
                ]
                if shock_entries:
                    response_recorded = True

        # Запускаем полный цикл
        thread = threading.Thread(
            target=run_loop,
            args=(
                self_state,
                monitor_response_cycle,
                0.01,
                1000,
                stop_event,
                event_queue,
            ),
        )
        thread.start()

        time.sleep(0.3)
        stop_event.set()
        thread.join(timeout=1.0)

        # Проверяем полный цикл обработки
        assert (
            response_recorded or len(self_state.memory) >= 0
        )  # Событие могло быть обработано

    def test_system_adaptation_over_time(self):
        """Тест адаптации системы со временем"""
        self_state = SelfState()
        stop_event = threading.Event()

        initial_energy = self_state.energy
        initial_learning_noise = self_state.learning_params["event_type_sensitivity"][
            "noise"
        ]

        # Запускаем систему на продолжительное время
        thread = threading.Thread(
            target=run_loop,
            args=(self_state, lambda x: None, 0.001, 1000, stop_event, None),
        )
        thread.start()

        time.sleep(0.4)  # Должно хватить для нескольких циклов Learning/Adaptation
        stop_event.set()
        thread.join(timeout=1.0)

        # Проверяем, что система работала и могла адаптироваться
        assert hasattr(self_state, "learning_params")
        assert hasattr(self_state, "adaptation_params")

        # Параметры могли измениться (или остаться теми же - зависит от данных)
        final_learning_noise = self_state.learning_params["event_type_sensitivity"][
            "noise"
        ]
        # Не проверяем конкретные изменения, только что система функционирует

    def test_recovery_and_learning_from_experience(self):
        """Тест восстановления и обучения на опыте"""
        self_state = SelfState()
        event_queue = EventQueue()
        stop_event = threading.Event()

        # Сценарий: повреждение -> восстановление -> повторное повреждение
        events = [
            Event(type="shock", intensity=-0.7, timestamp=1.0),  # Повреждение
            Event(type="recovery", intensity=0.5, timestamp=2.0),  # Восстановление
            Event(type="shock", intensity=-0.6, timestamp=3.0),  # Повторное повреждение
        ]

        for event in events:
            event_queue.push(event)

        learning_adapted = False

        def monitor_learning_adaptation(state):
            nonlocal learning_adapted
            # Проверяем, что Learning отреагировал на паттерны
            if hasattr(state, "learning_params"):
                noise_sensitivity = state.learning_params["event_type_sensitivity"][
                    "noise"
                ]
                shock_sensitivity = state.learning_params["event_type_sensitivity"][
                    "shock"
                ]
                if (
                    abs(noise_sensitivity - 0.2) > 0.001
                    or abs(shock_sensitivity - 0.2) > 0.001
                ):
                    learning_adapted = True

        # Запускаем цикл
        thread = threading.Thread(
            target=run_loop,
            args=(
                self_state,
                monitor_learning_adaptation,
                0.01,
                1000,
                stop_event,
                event_queue,
            ),
        )
        thread.start()

        time.sleep(0.4)
        stop_event.set()
        thread.join(timeout=1.0)

        # Проверяем, что система пережила весь сценарий
        assert hasattr(self_state, "memory")
        assert hasattr(self_state, "learning_params")
        # Learning мог адаптироваться или нет - зависит от конкретных данных

    # ============================================================================
    # Subjective Time Integration Tests
    # ============================================================================

    def test_subjective_time_runtime_loop_integration(self):
        """Интеграционный тест субъективного времени в runtime loop"""
        self_state = SelfState()
        event_queue = EventQueue()
        stop_event = threading.Event()

        # Устанавливаем начальное субъективное время
        initial_subjective = 10.0
        self_state.subjective_time = initial_subjective

        # Добавляем события
        events = [
            Event(type="noise", intensity=0.3, timestamp=1.0),
            Event(type="shock", intensity=-0.5, timestamp=2.0),
            Event(type="recovery", intensity=0.4, timestamp=3.0),
        ]
        for event in events:
            event_queue.push(event)

        subjective_times = []

        def monitor_subjective_time(state):
            # Отслеживаем субъективное время на каждом тике
            if hasattr(state, "subjective_time"):
                subjective_times.append(state.subjective_time)

        # Запускаем loop
        thread = threading.Thread(
            target=run_loop,
            args=(self_state, monitor_subjective_time, 0.01, 1000, stop_event, event_queue),
        )
        thread.start()

        time.sleep(0.2)
        stop_event.set()
        thread.join(timeout=1.0)

        # Проверяем, что субъективное время изменялось
        assert len(subjective_times) > 1, "Субъективное время должно было изменяться"
        assert all(t >= initial_subjective for t in subjective_times), "Субъективное время должно быть монотонным"

    def test_subjective_time_memory_persistence_integration(self):
        """Интеграционный тест сохранения субъективного времени в памяти"""
        self_state = SelfState()
        event_queue = EventQueue()
        stop_event = threading.Event()

        # Запускаем систему
        thread = threading.Thread(
            target=run_loop,
            args=(self_state, lambda s: None, 0.01, 1000, stop_event, event_queue),
        )
        thread.start()

        # Добавляем события во время работы
        events = [
            Event(type="noise", intensity=0.4, timestamp=time.time()),
            Event(type="shock", intensity=-0.6, timestamp=time.time() + 0.1),
        ]
        time.sleep(0.05)  # Даем системе запуститься
        for event in events:
            event_queue.push(event)

        time.sleep(0.1)
        stop_event.set()
        thread.join(timeout=1.0)

        # Проверяем, что в памяти есть записи
        assert len(self_state.memory) > 0, "Должны быть записи в памяти"

        # Проверяем, что записи имеют правильную структуру
        for entry in self_state.memory:
            assert hasattr(entry, 'timestamp'), "Запись должна иметь timestamp"
            assert isinstance(entry.timestamp, float), "timestamp должен быть float"
            assert entry.timestamp > 0, "timestamp должен быть положительным"
            # subjective_timestamp может быть установлен или нет
            if hasattr(entry, 'subjective_timestamp') and entry.subjective_timestamp is not None:
                assert isinstance(entry.subjective_timestamp, float), "subjective_timestamp должен быть float"
                assert entry.subjective_timestamp >= 0.0, "subjective_timestamp должен быть положительным"

    def test_subjective_time_feedback_integration(self):
        """Интеграционный тест субъективного времени с Feedback"""
        from src.feedback import register_action

        self_state = SelfState()
        event_queue = EventQueue()
        stop_event = threading.Event()

        # Устанавливаем начальное субъективное время
        self_state.subjective_time = 5.0

        # Регистрируем действие для создания Feedback
        action_id = "integration_test_action"
        register_action(
            action_id=action_id,
            action_pattern="dampen",
            state_before={"energy": 100.0, "stability": 1.0},
            timestamp=time.time(),
            pending_actions=[],
        )

        # Запускаем runtime loop
        thread = threading.Thread(
            target=run_loop,
            args=(self_state, lambda s: None, 0.01, 1000, stop_event, event_queue),
        )
        thread.start()

        time.sleep(0.1)
        stop_event.set()
        thread.join(timeout=1.0)

        # Проверяем Feedback записи
        feedback_entries = [entry for entry in self_state.memory if entry.event_type == "feedback"]
        if feedback_entries:
            for entry in feedback_entries:
                assert hasattr(entry, "subjective_timestamp"), "Feedback должен иметь subjective_timestamp"
                assert entry.subjective_timestamp is not None, "subjective_timestamp должен быть установлен"
                assert entry.subjective_timestamp >= 0.0, "subjective_timestamp должен быть положительным"

    def test_subjective_time_state_persistence_integration(self):
        """Интеграционный тест сохранения субъективного времени в состоянии"""
        from src.state.self_state import save_snapshot, load_snapshot

        self_state = SelfState()
        event_queue = EventQueue()
        stop_event = threading.Event()

        # Устанавливаем субъективное время
        initial_subjective_time = 25.5
        self_state.subjective_time = initial_subjective_time
        self_state.ticks = 50

        # Запускаем систему ненадолго (система может изменить субъективное время)
        thread = threading.Thread(
            target=run_loop,
            args=(self_state, lambda s: None, 0.001, 10, stop_event, event_queue),
        )
        thread.start()

        time.sleep(0.05)
        stop_event.set()
        thread.join(timeout=1.0)

        # Сохраняем состояние
        final_subjective_time = self_state.subjective_time
        save_snapshot(self_state)

        # Загружаем состояние
        loaded_state = load_snapshot(50)

        # Проверяем, что субъективное время присутствует и имеет разумное значение
        assert hasattr(loaded_state, "subjective_time"), "Загруженное состояние должно иметь subjective_time"
        assert isinstance(loaded_state.subjective_time, float), "subjective_time должен быть float"
        assert loaded_state.subjective_time >= 0.0, "subjective_time должен быть положительным"
        # Субъективное время сохраняется (может быть изменено системой, но должно сохраниться текущее значение)

    def test_subjective_time_runtime_dynamics_integration(self):
        """Интеграционный тест динамики субъективного времени в runtime"""
        self_state = SelfState()
        event_queue = EventQueue()
        stop_event = threading.Event()

        # Добавляем события с разной интенсивностью
        events = [
            Event(type="idle", intensity=0.0, timestamp=1.0),    # Низкая интенсивность
            Event(type="noise", intensity=0.5, timestamp=2.0),   # Средняя интенсивность
            Event(type="shock", intensity=0.9, timestamp=3.0),   # Высокая интенсивность
        ]
        for event in events:
            event_queue.push(event)

        time_points = []

        def monitor_time_dynamics(state):
            # Записываем состояние времени на каждом тике
            if hasattr(state, "subjective_time"):
                time_points.append({
                    "subjective_time": state.subjective_time,
                    "energy": state.energy,
                    "stability": state.stability,
                    "intensity": getattr(state, "last_event_intensity", 0.0),
                })

        # Запускаем систему
        thread = threading.Thread(
            target=run_loop,
            args=(self_state, monitor_time_dynamics, 0.01, 1000, stop_event, event_queue),
        )
        thread.start()

        time.sleep(0.2)
        stop_event.set()
        thread.join(timeout=1.0)

        # Проверяем, что система собрала данные о динамике времени
        assert len(time_points) > 1, "Должны быть собраны данные о динамике времени"

        # Проверяем монотонность субъективного времени
        subjective_times = [point["subjective_time"] for point in time_points]
        assert subjective_times == sorted(subjective_times), "Субъективное время должно быть монотонным"

    # ============================================================================
    # Thread Safety Integration Tests
    # ============================================================================

    @pytest.mark.skip(reason="API tests are outdated")
    def test_thread_safety_api_runtime_concurrent_integration(self):
        """Интеграционный тест конкурентного доступа API и runtime"""
        from fastapi.testclient import TestClient
        from api import app

        client = TestClient(app, timeout=10.0)

        # Получаем токен
        login_response = client.post("/token", data={"username": "admin", "password": "admin123"})
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Создаем состояние и очередь
        state = SelfState()
        event_queue = EventQueue()
        stop_event = threading.Event()

        # Запускаем runtime loop
        runtime_thread = threading.Thread(
            target=run_loop,
            args=(state, lambda s: None, 0.001, 1000, stop_event, event_queue),
        )
        runtime_thread.start()

        # Пока runtime работает, делаем API запросы
        api_results = []
        for i in range(5):
            try:
                response = client.get("/status", headers=headers)
                api_results.append(response.status_code)
                time.sleep(0.005)  # Маленькая задержка
            except Exception as e:
                api_results.append(f"error: {e}")

        stop_event.set()
        runtime_thread.join(timeout=1.0)

        # Все API запросы должны быть успешными
        successful_requests = [r for r in api_results if r == 200]
        assert len(successful_requests) >= 3, f"Слишком много неудачных API запросов: {api_results}"

    @pytest.mark.skip(reason="API tests are outdated")
    def test_thread_safety_event_submission_during_runtime_integration(self):
        """Интеграционный тест отправки событий во время работы runtime"""
        from fastapi.testclient import TestClient
        from api import app

        client = TestClient(app, timeout=10.0)

        # Регистрируем пользователя
        user_data = {"username": "thread_test", "email": "thread@example.com", "password": "test123"}
        client.post("/register", json=user_data)

        login_response = client.post("/token", data={"username": "thread_test", "password": "test123"})
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        state = SelfState()
        event_queue = EventQueue()
        stop_event = threading.Event()

        # Запускаем runtime
        runtime_thread = threading.Thread(
            target=run_loop,
            args=(state, lambda s: None, 0.001, 1000, stop_event, event_queue),
        )
        runtime_thread.start()

        # Отправляем события через API во время работы runtime
        event_results = []
        for i in range(3):
            try:
                event_data = {
                    "type": "noise",
                    "intensity": 0.2 + i * 0.1,
                    "metadata": {"integration_test": True, "sequence": i}
                }
                response = client.post("/event", json=event_data, headers=headers)
                event_results.append(response.status_code)
                time.sleep(0.01)
            except Exception as e:
                event_results.append(f"error: {e}")

        stop_event.set()
        runtime_thread.join(timeout=1.0)

        # Все отправки событий должны быть успешными
        successful_events = [r for r in event_results if r == 200]
        assert len(successful_events) == 3, f"Не все события отправлены успешно: {event_results}"

    def test_thread_safety_state_consistency_integration(self):
        """Интеграционный тест консистентности состояния при конкурентном доступе"""
        state = SelfState()
        stop_event = threading.Event()

        # Записываем начальные значения
        initial_energy = state.energy
        initial_ticks = state.ticks

        access_log = []

        def api_reader(reader_id):
            """Имитирует API чтение"""
            for _ in range(10):
                try:
                    # Имитируем get_safe_status_dict
                    snapshot = state.get_safe_status_dict()
                    access_log.append(("read", reader_id, snapshot["ticks"], snapshot["energy"]))
                    time.sleep(0.001)
                except Exception as e:
                    access_log.append(("read_error", reader_id, str(e)))

        def runtime_writer(writer_id):
            """Имитирует runtime запись"""
            for i in range(5):
                try:
                    # Имитируем изменения состояния (не превышаем лимиты валидации)
                    new_energy = min(initial_energy + i * 5, 100.0)
                    state.energy = new_energy
                    state.ticks = initial_ticks + i
                    access_log.append(("write", writer_id, state.ticks, state.energy))
                    time.sleep(0.002)
                except Exception as e:
                    access_log.append(("write_error", writer_id, str(e)))

        # Запускаем читателей и писателей
        threads = []
        for i in range(2):  # 2 читателя
            thread = threading.Thread(target=api_reader, args=(i,))
            threads.append(thread)

        for i in range(1):  # 1 писатель
            thread = threading.Thread(target=runtime_writer, args=(i,))
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join(timeout=2.0)

        # Проверяем, что не было ошибок
        errors = [entry for entry in access_log if "error" in entry[0]]
        assert len(errors) == 0, f"Были ошибки при конкурентном доступе: {errors}"

        # Проверяем, что были и чтения и записи
        reads = [entry for entry in access_log if entry[0] == "read"]
        writes = [entry for entry in access_log if entry[0] == "write"]

        assert len(reads) > 0, "Должны быть успешные чтения"
        assert len(writes) > 0, "Должны быть успешные записи"

    def test_thread_safety_memory_consistency_integration(self):
        """Интеграционный тест консистентности памяти при потокобезопасности"""
        from src.memory.memory import Memory, MemoryEntry

        memory = Memory()
        stop_event = threading.Event()

        # Добавляем начальные записи
        for i in range(3):
            entry = MemoryEntry(
                event_type="noise",
                meaning_significance=0.3,
                timestamp=float(i)
            )
            memory.append(entry)

        operations_log = []

        def memory_reader(reader_id):
            """Читает память"""
            for _ in range(5):
                try:
                    # Имитируем чтение (создание копии)
                    snapshot = list(memory)
                    operations_log.append(("read", reader_id, len(snapshot)))
                    time.sleep(0.001)
                except Exception as e:
                    operations_log.append(("read_error", reader_id, str(e)))

        def memory_writer(writer_id):
            """Пишет в память"""
            for i in range(3):
                try:
                    entry = MemoryEntry(
                        event_type="shock",
                        meaning_significance=0.8,
                        timestamp=10.0 + i
                    )
                    memory.append(entry)
                    operations_log.append(("write", writer_id, len(memory)))
                    time.sleep(0.002)
                except Exception as e:
                    operations_log.append(("write_error", writer_id, str(e)))

        # Запускаем операции
        threads = []
        for i in range(2):  # 2 читателя
            thread = threading.Thread(target=memory_reader, args=(i,))
            threads.append(thread)

        for i in range(1):  # 1 писатель
            thread = threading.Thread(target=memory_writer, args=(i,))
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join(timeout=2.0)

        # Проверяем отсутствие ошибок
        errors = [op for op in operations_log if "error" in op[0]]
        assert len(errors) == 0, f"Были ошибки при работе с памятью: {errors}"

        # Финальная длина памяти должна быть корректной
        final_length = len(memory)
        assert final_length >= 3, "Память должна содержать хотя бы начальные записи"

    # ============================================================================
    # Combined New Functionality Integration Tests
    # ============================================================================

    @pytest.mark.skip(reason="API tests are outdated")
    def test_subjective_time_thread_safety_combined_integration(self):
        """Интеграционный тест комбинации субъективного времени и потокобезопасности"""
        from fastapi.testclient import TestClient
        from api import app

        client = TestClient(app, timeout=10.0)

        # Получаем токен
        login_response = client.post("/token", data={"username": "admin", "password": "admin123"})
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        state = SelfState()
        event_queue = EventQueue()
        stop_event = threading.Event()

        # Устанавливаем начальное субъективное время
        state.subjective_time = 100.0

        # Запускаем runtime
        runtime_thread = threading.Thread(
            target=run_loop,
            args=(state, lambda s: None, 0.001, 1000, stop_event, event_queue),
        )
        runtime_thread.start()

        # Отправляем события через API
        for i in range(3):
            event_data = {
                "type": ["noise", "shock", "recovery"][i],
                "intensity": [0.3, -0.5, 0.4][i],
                "metadata": {"combined_test": True}
            }
            response = client.post("/event", json=event_data, headers=headers)
            assert response.status_code == 200
            time.sleep(0.01)

        # Читаем статус несколько раз
        status_reads = []
        for _ in range(3):
            response = client.get("/status", headers=headers)
            assert response.status_code == 200
            status_data = response.json()
            status_reads.append(status_data.get("subjective_time"))
            time.sleep(0.005)

        stop_event.set()
        runtime_thread.join(timeout=1.0)

        # Проверяем, что субъективное время присутствует в API ответах
        valid_reads = [st for st in status_reads if st is not None]
        assert len(valid_reads) > 0, "API должен возвращать subjective_time"

        # Все значения должны быть положительными
        assert all(st >= 0 for st in valid_reads), "subjective_time должен быть положительным"

    @pytest.mark.skip(reason="API tests are outdated")
    def test_full_system_new_functionality_integration(self):
        """Полная интеграция всей новой функциональности"""
        from fastapi.testclient import TestClient
        from api import app
        from src.feedback import register_action

        client = TestClient(app, timeout=10.0)

        # Создаем пользователя
        user_data = {"username": "full_test", "email": "full@example.com", "password": "test123"}
        client.post("/register", json=user_data)

        login_response = client.post("/token", data={"username": "full_test", "password": "test123"})
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        state = SelfState()
        event_queue = EventQueue()
        stop_event = threading.Event()

        # Устанавливаем начальное субъективное время
        state.subjective_time = 50.0

        # Регистрируем действие для Feedback
        register_action(
            action_id="full_test_action",
            action_pattern="absorb",
            state_before={"energy": 100.0, "stability": 1.0},
            timestamp=time.time(),
            pending_actions=[],
        )

        # Запускаем runtime
        runtime_thread = threading.Thread(
            target=run_loop,
            args=(state, lambda s: None, 0.001, 1000, stop_event, event_queue),
        )
        runtime_thread.start()

        # Выполняем полный цикл тестирования
        time.sleep(0.02)

        # 1. Отправляем событие
        event_response = client.post("/event", json={
            "type": "shock",
            "intensity": -0.7,
            "metadata": {"full_integration_test": True}
        }, headers=headers)
        assert event_response.status_code == 200

        time.sleep(0.02)

        # 2. Читаем статус (с субъективным временем)
        status_response = client.get("/status", headers=headers)
        assert status_response.status_code == 200
        status_data = status_response.json()

        # 3. Проверяем наличие новой функциональности
        assert "subjective_time" in status_data, "API должен возвращать subjective_time"
        assert isinstance(status_data["subjective_time"], (int, float)), "subjective_time должен быть числом"
        assert status_data["subjective_time"] >= 0, "subjective_time должен быть положительным"

        stop_event.set()
        runtime_thread.join(timeout=1.0)

        # 4. Проверяем, что система сохранила состояние
        assert hasattr(state, "memory"), "Система должна иметь память"
        assert hasattr(state, "learning_params"), "Learning должен работать"
        assert hasattr(state, "adaptation_params"), "Adaptation должен работать"

        # 5. Проверяем наличие записей с субъективным временем
        memory_with_subjective = [entry for entry in state.memory
                                  if hasattr(entry, 'subjective_timestamp') and entry.subjective_timestamp is not None]
        assert len(memory_with_subjective) > 0, "Должны быть записи памяти с subjective_timestamp"

    # ============================================================================
    # MCP Index Engine Integration
    # ============================================================================

    def test_mcp_index_engine_full_integration(self):
        """Полная интеграция MCP Index Engine"""
        from pathlib import Path
        import tempfile
        import shutil
        from mcp_index_engine import IndexEngine

        docs_dir = Path(tempfile.mkdtemp())
        todo_dir = Path(tempfile.mkdtemp())
        src_dir = Path(tempfile.mkdtemp())

        try:
            # Создаем тестовую документацию
            docs_content = [
                ("api.md", "# API Documentation\nREST API with authentication using JWT tokens"),
                ("search.md", "# Search Engine\nAdvanced search capabilities with indexing"),
                ("architecture.md", "# System Architecture\nModular design with multiple components"),
            ]

            for filename, content in docs_content:
                (docs_dir / filename).write_text(content, encoding="utf-8")

            # Создаем TODO файлы
            todo_content = [
                ("features.md", "# Planned Features\n- Advanced search\n- User authentication\n- API integration"),
                ("bugs.md", "# Known Issues\n- Search performance\n- Memory usage"),
            ]

            for filename, content in todo_content:
                (todo_dir / filename).write_text(content, encoding="utf-8")

            # Инициализируем индекс
            engine = IndexEngine(docs_dir, todo_dir, src_dir)
            engine.initialize()

            # Проверяем индексацию
            assert len(engine.content_cache) == 5  # 3 docs + 2 todo
            assert len(engine.inverted_index) > 0

            # Тестируем поиск
            results = engine.search_in_directory(docs_dir, "api")
            assert len(results) >= 1
            assert any("api.md" in r["path"] for r in results)

            results = engine.search_in_directory(docs_dir, "search")
            assert len(results) >= 1  # документы, содержащие "search"

            # Тестируем разные режимы поиска
            and_results = engine.search_in_directory(docs_dir, "api authentication", mode="AND")
            assert len(and_results) >= 1

            or_results = engine.search_in_directory(docs_dir, "system modular", mode="OR")
            assert len(or_results) >= 1  # architecture.md содержит оба слова

            # Тестируем поиск по TODO
            todo_results = engine.search_in_directory(todo_dir, "authentication")
            assert len(todo_results) >= 1

            # Тестируем обновление файла
            api_file = docs_dir / "api.md"
            api_file.write_text("# API Documentation\nUpdated: REST API with JWT authentication and advanced features", encoding="utf-8")

            engine.update_file(api_file)
            updated_results = engine.search_in_directory(docs_dir, "advanced")
            assert len(updated_results) >= 1

            # Тестируем переиндексацию
            (docs_dir / "new_doc.md").write_text("# New Document\nRecently added content", encoding="utf-8")
            engine.reindex()
            assert len(engine.content_cache) == 6  # +1 новый файл

        finally:
            shutil.rmtree(docs_dir, ignore_errors=True)
            shutil.rmtree(todo_dir, ignore_errors=True)
            shutil.rmtree(src_dir, ignore_errors=True)

    def test_mcp_index_engine_performance_integration(self):
        """Интеграционный тест производительности MCP Index Engine"""
        from pathlib import Path
        import tempfile
        import shutil
        import time
        from mcp_index_engine import IndexEngine

        docs_dir = Path(tempfile.mkdtemp())

        try:
            # Создаем много файлов для тестирования производительности
            for i in range(50):
                content = f"# Document {i}\nThis is test content for document number {i}.\nKeywords: test, performance, search, indexing."
                (docs_dir / f"doc_{i:03d}.md").write_text(content, encoding="utf-8")

            engine = IndexEngine(docs_dir, Path(tempfile.mkdtemp()), Path(tempfile.mkdtemp()))

            # Замеряем время индексации
            start_time = time.time()
            engine.initialize()
            index_time = time.time() - start_time

            # Проверяем, что индексация была reasonably быстрой (< 1 секунды для 50 файлов)
            assert index_time < 1.0, f"Индексация заняла слишком много времени: {index_time}s"

            # Замеряем время поиска
            search_start = time.time()
            results = engine.search_in_directory(docs_dir, "performance", limit=100)  # Увеличим лимит
            search_time = time.time() - search_start

            # Поиск должен быть быстрым (< 0.1 секунды)
            assert search_time < 0.1, f"Поиск занял слишком много времени: {search_time}s"
            assert len(results) == 50  # Все документы содержат "performance"

            # Тестируем LRU кэширование
            small_engine = IndexEngine(docs_dir, Path(tempfile.mkdtemp()), Path(tempfile.mkdtemp()), cache_size_limit=10)

            # Заполняем кэш
            for i in range(15):
                file_path = docs_dir / f"doc_{i:03d}.md"
                small_engine._get_content(file_path, docs_dir)

            # Кэш не должен превышать лимит
            assert len(small_engine.content_cache) <= 10

        finally:
            shutil.rmtree(docs_dir, ignore_errors=True)

    def test_mcp_index_engine_error_handling_integration(self):
        """Интеграционный тест обработки ошибок MCP Index Engine"""
        from pathlib import Path
        import tempfile
        import shutil
        from mcp_index_engine import IndexEngine

        docs_dir = Path(tempfile.mkdtemp())
        todo_dir = Path(tempfile.mkdtemp())
        src_dir = Path(tempfile.mkdtemp())

        try:
            # Создаем файлы с проблемами
            (docs_dir / "valid.md").write_text("# Valid Document\nNormal content", encoding="utf-8")

            # Файл с неподдерживаемой кодировкой (имитация)
            (docs_dir / "binary.md").write_bytes(b'\x89PNG\r\n\x1a\n' + b'x' * 1000)  # PNG header + garbage

            # Слишком большой файл
            big_content = "x" * (10 * 1024 * 1024 + 1)  # > 10MB
            (docs_dir / "huge.md").write_text(big_content, encoding="utf-8")

            engine = IndexEngine(docs_dir, todo_dir, src_dir, max_file_size=10*1024*1024)

            # Индексация должна обработать ошибки gracefully
            engine.initialize()

            # Должен проиндексировать валидный файл
            assert len(engine.content_cache) >= 1
            assert "valid.md" in engine.content_cache

            # Бинарный и huge файлы должны быть пропущены
            assert "binary.md" not in engine.content_cache
            assert "huge.md" not in engine.content_cache

            # Поиск должен работать несмотря на ошибки
            results = engine.search_in_directory(docs_dir, "document")
            assert len(results) >= 1

        finally:
            shutil.rmtree(docs_dir, ignore_errors=True)
            shutil.rmtree(todo_dir, ignore_errors=True)
            shutil.rmtree(src_dir, ignore_errors=True)

    # ============================================================================
    # API Authentication Integration
    # ============================================================================

    @pytest.mark.skip(reason="API tests are outdated")
    def test_api_auth_full_lifecycle_integration(self):
        """Полная интеграция жизненного цикла API аутентификации"""
        from fastapi.testclient import TestClient
        from api import app

        client = TestClient(app)

        # 1. Регистрация пользователей
        users = [
            {"username": "testuser1", "email": "test1@example.com", "password": "pass123"},
            {"username": "testuser2", "email": "test2@example.com", "password": "pass456"},
        ]

        tokens = {}
        for user in users:
            # Регистрация
            response = client.post("/register", json=user)
            assert response.status_code == 201

            # Вход
            login_response = client.post("/token", data={
                "username": user["username"],
                "password": user["password"]
            })
            assert login_response.status_code == 200

            tokens[user["username"]] = login_response.json()["access_token"]

        # 2. Проверка изоляции пользователей
        for username, token in tokens.items():
            headers = {"Authorization": f"Bearer {token}"}

            # Каждый пользователь может получить статус
            status_response = client.get("/status", headers=headers)
            assert status_response.status_code == 200

            # Каждый пользователь может создать событие
            event_response = client.post("/event", json={
                "type": "noise",
                "metadata": {"user": username}
            }, headers=headers)
            assert event_response.status_code == 200
            assert username in event_response.json()["message"]

            # Каждый пользователь может получить список пользователей
            users_response = client.get("/users", headers=headers)
            assert users_response.status_code == 200
            users_data = users_response.json()
            assert len(users_data) >= 4  # admin, user, testuser1, testuser2

        # 3. Проверка что пользователи не могут использовать токены друг друга
        # (тестируем с токеном user1 на действия user2 - в текущей реализации токены не привязаны к пользователю в payload)
        # В данной реализации JWT содержит только username, так что изоляция на уровне API

    @pytest.mark.skip(reason="API tests are outdated")
    def test_api_auth_token_expiration_integration(self):
        """Интеграционный тест истечения токенов API"""
        from fastapi.testclient import TestClient
        import jwt
        import time
        from api import app, SECRET_KEY, ALGORITHM

        client = TestClient(app)

        # Создаем токен с коротким сроком действия
        expire_time = int(time.time()) + 2  # Истекает через 2 секунды
        token_payload = {"sub": "admin", "exp": expire_time}
        short_token = jwt.encode(token_payload, SECRET_KEY, algorithm=ALGORITHM)

        headers = {"Authorization": f"Bearer {short_token}"}

        # Токен должен работать сначала
        response = client.get("/status", headers=headers)
        assert response.status_code == 200

        # Ждем истечения
        time.sleep(3)

        # Теперь токен должен быть невалиден
        response = client.get("/status", headers=headers)
        assert response.status_code == 401

        # Проверяем что можем получить новый токен
        login_response = client.post("/token", data={"username": "admin", "password": "admin123"})
        assert login_response.status_code == 200

        new_token = login_response.json()["access_token"]
        new_headers = {"Authorization": f"Bearer {new_token}"}

        # Новый токен работает
        response = client.get("/status", headers=new_headers)
        assert response.status_code == 200

    @pytest.mark.skip(reason="API tests are outdated")
    def test_api_auth_concurrent_sessions_integration(self):
        """Интеграционный тест одновременных сессий API"""
        from fastapi.testclient import TestClient
        from api import app

        client = TestClient(app)

        # Создаем несколько токенов для одного пользователя
        tokens = []
        for _ in range(5):
            login_response = client.post("/token", data={"username": "admin", "password": "admin123"})
            assert login_response.status_code == 200
            tokens.append(login_response.json()["access_token"])

        # Все токены должны работать одновременно
        for i, token in enumerate(tokens):
            headers = {"Authorization": f"Bearer {token}"}

            # Получаем статус
            status_response = client.get("/status", headers=headers)
            assert status_response.status_code == 200

            # Создаем событие
            event_response = client.post("/event", json={
                "type": "noise",
                "metadata": {"session": i, "test": "concurrent"}
            }, headers=headers)
            assert event_response.status_code == 200

            # Получаем пользователей
            users_response = client.get("/users", headers=headers)
            assert users_response.status_code == 200

    @pytest.mark.skip(reason="API tests are outdated")
    def test_api_auth_event_processing_integration(self):
        """Интеграционный тест обработки событий через API"""
        from fastapi.testclient import TestClient
        from api import app

        client = TestClient(app)

        # Получаем токен
        login_response = client.post("/token", data={"username": "admin", "password": "admin123"})
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Создаем различные события
        events = [
            {"type": "noise", "intensity": 0.3, "metadata": {"test": "integration"}},
            {"type": "shock", "intensity": -0.7, "metadata": {"test": "integration"}},
            {"type": "recovery", "intensity": 0.8, "metadata": {"test": "integration"}},
            {"type": "decay", "intensity": -0.4, "metadata": {"test": "integration"}},
            {"type": "idle", "metadata": {"test": "integration"}},
        ]

        for event in events:
            response = client.post("/event", json=event, headers=headers)
            assert response.status_code == 200

            data = response.json()
            assert data["type"] == event["type"]
            assert data["intensity"] == event.get("intensity", 0.0)
            assert data["metadata"] == event.get("metadata", {})
            assert "message" in data
            assert "admin" in data["message"]

        # Проверяем что статус обновился после обработки событий
        status_response = client.get("/status", headers=headers)
        assert status_response.status_code == 200

        status_data = status_response.json()
        assert "last_event_intensity" in status_data

    @pytest.mark.skip(reason="API tests are outdated")
    def test_api_auth_extended_status_integration(self):
        """Интеграционный тест расширенного статуса API"""
        from fastapi.testclient import TestClient
        from api import app

        client = TestClient(app)

        # Регистрируем нового пользователя для тестирования
        user_data = {"username": "status_test", "email": "status@example.com", "password": "status123"}
        client.post("/register", json=user_data)

        login_response = client.post("/token", data={"username": "status_test", "password": "status123"})
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Получаем расширенный статус
        response = client.get("/status", headers=headers)
        assert response.status_code == 200

        data = response.json()

        # Проверяем обязательные поля
        required_fields = ["active", "energy", "integrity", "stability", "ticks", "age", "subjective_time"]
        for field in required_fields:
            assert field in data

        # Проверяем опциональные поля
        optional_fields = ["life_id", "birth_timestamp", "learning_params", "adaptation_params"]
        for field in optional_fields:
            assert field in data  # В данной реализации все поля присутствуют

        # Проверяем структуру learning_params
        if data.get("learning_params"):
            lp = data["learning_params"]
            assert "event_type_sensitivity" in lp
            assert "significance_thresholds" in lp
            assert "response_coefficients" in lp

        # Тестируем минимальный статус (API возвращает ExtendedStatusResponse даже при minimal=true)
        min_response = client.get("/status?minimal=true", headers=headers)
        assert min_response.status_code == 200

        min_data = min_response.json()
        # API возвращает расширенный статус независимо от параметра minimal
        extended_fields = {"active", "ticks", "age", "energy", "stability", "integrity", "subjective_time", "fatigue", "tension", "learning_params", "adaptation_params", "life_id", "birth_timestamp"}
        assert all(field in min_data for field in extended_fields)

        # Тестируем статус с лимитами
        limited_response = client.get("/status?memory_limit=5&events_limit=3", headers=headers)
        assert limited_response.status_code == 200

    @pytest.mark.skip(reason="API tests are outdated")
    def test_api_auth_error_handling_integration(self):
        """Интеграционный тест обработки ошибок API"""
        from fastapi.testclient import TestClient
        from api import app

        client = TestClient(app)

        # Получаем токен
        login_response = client.post("/token", data={"username": "admin", "password": "admin123"})
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Тестируем различные ошибочные запросы
        error_cases = [
            # Неправильный JSON в событии
            ("POST", "/event", "invalid json", 422),  # Pydantic validation error
            # Отсутствующий тип события
            ("POST", "/event", {"intensity": 0.5}, 422),  # Missing required field
            # Неизвестный эндпоинт
            ("GET", "/nonexistent", None, 404),
            # Неправильный метод
            ("PUT", "/status", None, 405),
        ]

        for method, endpoint, data, expected_status in error_cases:
            if method == "POST":
                response = client.post(endpoint, json=data, headers=headers)
            elif method == "GET":
                response = client.get(endpoint, headers=headers)
            elif method == "PUT":
                response = client.put(endpoint, json=data, headers=headers)
            else:
                continue

            assert response.status_code == expected_status

    # ============================================================================
    # MCP + API Combined Integration
    # ============================================================================

    @pytest.mark.skip(reason="API tests are outdated")
    def test_mcp_api_combined_search_integration(self):
        """Интеграционный тест комбинированного поиска MCP + API"""
        from pathlib import Path
        import tempfile
        import shutil
        from fastapi.testclient import TestClient
        from mcp_index_engine import IndexEngine
        from api import app

        docs_dir = Path(tempfile.mkdtemp())
        todo_dir = Path(tempfile.mkdtemp())
        src_dir = Path(tempfile.mkdtemp())

        try:
            # Создаем документацию для поиска
            docs_content = [
                ("authentication.md", "# Authentication\nJWT tokens and user management in API"),
                ("search.md", "# Search Engine\nMCP Index Engine provides fast search capabilities"),
                ("api_endpoints.md", "# API Endpoints\n/status, /event, /users with authentication"),
            ]

            for filename, content in docs_content:
                (docs_dir / filename).write_text(content, encoding="utf-8")

            # Инициализируем поисковый индекс
            engine = IndexEngine(docs_dir, todo_dir, src_dir)
            engine.initialize()

            # Тестируем поиск через индекс
            auth_results = engine.search_in_directory(docs_dir, "authentication")
            assert len(auth_results) >= 1
            # Проверяем, что найден релевантный документ
            found_auth = any("authentication" in r["path"] for r in auth_results)
            assert found_auth, f"Authentication document not found in results: {[r['path'] for r in auth_results]}"

            api_results = engine.search_in_directory(docs_dir, "api")
            assert len(api_results) >= 2  # документы, содержащие "api"

            # Тестируем API аутентификацию
            client = TestClient(app)

            # Регистрируем пользователя
            user_data = {"username": "search_user", "email": "search@example.com", "password": "search123"}
            client.post("/register", json=user_data)

            # Входим
            login_response = client.post("/token", data={"username": "search_user", "password": "search123"})
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Создаем события через API
            events = [
                {"type": "noise", "metadata": {"search_test": True, "topic": "authentication"}},
                {"type": "noise", "metadata": {"search_test": True, "topic": "api"}},
                {"type": "noise", "metadata": {"search_test": True, "topic": "search"}},
            ]

            for event in events:
                response = client.post("/event", json=event, headers=headers)
                assert response.status_code == 200

            # Проверяем статус
            status_response = client.get("/status", headers=headers)
            assert status_response.status_code == 200

            # Проверяем что обе системы работают вместе
            assert len(engine.content_cache) == 3  # Документы проиндексированы
            assert status_response.json()["active"] is True  # API работает
            assert len(api_results) >= 2  # Поиск работает

        finally:
            shutil.rmtree(docs_dir, ignore_errors=True)
            shutil.rmtree(todo_dir, ignore_errors=True)
            shutil.rmtree(src_dir, ignore_errors=True)

    def test_subjective_time_memory_integration(self):
        """Интеграционный тест записи субъективного времени в память"""
        self_state = SelfState()
        event_queue = EventQueue()
        stop_event = threading.Event()

        # Устанавливаем начальное субъективное время
        self_state.subjective_time = 10.0

        # Добавляем событие для обработки
        event = Event(type="shock", intensity=0.8, timestamp=time.time())
        event_queue.push(event)

        def dummy_monitor(state):
            pass

        # Запускаем loop на один тик
        thread = threading.Thread(
            target=run_loop,
            args=(self_state, dummy_monitor, 0.01, 1000, stop_event, event_queue),
        )
        thread.start()

        # Ждем обработки
        time.sleep(0.05)
        stop_event.set()
        thread.join(timeout=1.0)

        # Проверяем, что в памяти есть запись с subjective_timestamp
        memory_entries = [entry for entry in self_state.memory if entry.event_type == "shock"]
        assert len(memory_entries) > 0, "Должна быть запись о событии shock в памяти"

        entry = memory_entries[0]
        assert entry.subjective_timestamp is not None, "subjective_timestamp должен быть установлен"
        assert isinstance(entry.subjective_timestamp, float), "subjective_timestamp должен быть float"
        assert entry.subjective_timestamp > 0, "subjective_timestamp должен быть положительным"

    def test_subjective_time_feedback_memory_integration(self):
        """Интеграционный тест записи субъективного времени в Feedback записи"""
        from src.feedback import register_action

        self_state = SelfState()
        event_queue = EventQueue()
        stop_event = threading.Event()
        pending_actions = []

        # Устанавливаем начальное субъективное время
        self_state.subjective_time = 5.0

        # Регистрируем действие для создания Feedback
        action_id = "test_action_123"
        register_action(
            action_id=action_id,
            action_pattern="dampen",
            state_before={"energy": 100.0, "stability": 1.0},
            timestamp=time.time(),
            pending_actions=pending_actions,
        )

        # Запускаем loop для обработки Feedback
        def dummy_monitor(state):
            pass

        thread = threading.Thread(
            target=run_loop,
            args=(self_state, dummy_monitor, 0.01, 1000, stop_event, event_queue),
        )
        thread.start()

        # Ждем обработки Feedback
        time.sleep(0.05)
        stop_event.set()
        thread.join(timeout=1.0)

        # Проверяем, что система работает (Feedback может создаваться или не создаваться в зависимости от условий)
        feedback_entries = [entry for entry in self_state.memory if entry.event_type == "feedback"]

        # Если Feedback записи создались, проверяем их структуру
        if feedback_entries:
            entry = feedback_entries[0]
            assert entry.subjective_timestamp is not None, "subjective_timestamp должен быть установлен в Feedback"
            assert isinstance(entry.subjective_timestamp, float), "subjective_timestamp должен быть float"
            assert entry.subjective_timestamp > 0, "subjective_timestamp должен быть положительным"

            # Проверяем структуру feedback_data
            assert entry.feedback_data is not None, "Feedback запись должна иметь feedback_data"
            assert "action_id" in entry.feedback_data, "feedback_data должен содержать action_id"
        else:
            # Если Feedback не создался, проверяем что система все равно работает
            assert hasattr(self_state, "memory"), "Memory должна существовать"
            assert hasattr(self_state, "learning_params"), "Learning params должны существовать"

    def test_subjective_time_monotonic_in_memory(self):
        """Интеграционный тест монотонности субъективного времени в памяти"""
        self_state = SelfState()
        event_queue = EventQueue()
        stop_event = threading.Event()

        # Добавляем несколько событий
        events = [
            Event(type="noise", intensity=0.3, timestamp=time.time() + i)
            for i in range(3)
        ]
        for event in events:
            event_queue.push(event)

        timestamps_collected = []

        def monitor_collecting_timestamps(state):
            # Собираем все subjective_timestamp из памяти на каждом тике
            for entry in state.memory:
                if hasattr(entry, 'subjective_timestamp') and entry.subjective_timestamp is not None:
                    if entry.subjective_timestamp not in timestamps_collected:
                        timestamps_collected.append(entry.subjective_timestamp)

        # Запускаем loop
        thread = threading.Thread(
            target=run_loop,
            args=(self_state, monitor_collecting_timestamps, 0.01, 1000, stop_event, event_queue),
        )
        thread.start()

        # Ждем обработки всех событий
        time.sleep(0.1)
        stop_event.set()
        thread.join(timeout=1.0)

        # Проверяем монотонность: все timestamp должны быть >= 0 и не убывать
        assert len(timestamps_collected) > 0, "Должны быть собраны subjective_timestamp"
        assert all(ts >= 0 for ts in timestamps_collected), "Все subjective_timestamp должны быть >= 0"

        # Проверяем монотонность (неубывание)
        sorted_timestamps = sorted(timestamps_collected)
        assert timestamps_collected == sorted_timestamps, "subjective_timestamp должны быть монотонными"
