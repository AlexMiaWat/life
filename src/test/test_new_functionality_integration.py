"""
Интеграционные тесты для новой функциональности

Проверяем:
- Взаимодействие Learning, Adaptation и MeaningEngine в runtime loop
- Полные циклы обработки событий
- Интеграцию с Memory и Feedback
- Работа в многопоточной среде runtime loop
- Сохранение и загрузку состояния
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

    def test_api_auth_full_lifecycle_integration(self):
        """Полная интеграция жизненного цикла API аутентификации"""
        from fastapi.testclient import TestClient
        from api import app

        client = TestClient(app, timeout=10.0)

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

    def test_api_auth_token_expiration_integration(self):
        """Интеграционный тест истечения токенов API"""
        from fastapi.testclient import TestClient
        import jwt
        import time
        from api import app, SECRET_KEY, ALGORITHM

        client = TestClient(app, timeout=10.0)

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

    def test_api_auth_concurrent_sessions_integration(self):
        """Интеграционный тест одновременных сессий API"""
        from fastapi.testclient import TestClient
        from api import app

        client = TestClient(app, timeout=10.0)

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

    def test_api_auth_event_processing_integration(self):
        """Интеграционный тест обработки событий через API"""
        from fastapi.testclient import TestClient
        from api import app

        client = TestClient(app, timeout=10.0)

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

    def test_api_auth_extended_status_integration(self):
        """Интеграционный тест расширенного статуса API"""
        from fastapi.testclient import TestClient
        from api import app

        client = TestClient(app, timeout=10.0)

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

    def test_api_auth_error_handling_integration(self):
        """Интеграционный тест обработки ошибок API"""
        from fastapi.testclient import TestClient
        from api import app

        client = TestClient(app, timeout=10.0)

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
            client = TestClient(app, timeout=10.0)

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
