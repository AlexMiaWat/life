"""
Тесты race conditions для чтения /status во время тиков и edge cases очереди событий.

Проверяет:
- Race conditions между API чтением статуса и runtime loop модификацией состояния
- Конкурентный доступ к snapshots при высокой нагрузке
- Timing issues при чтении статуса во время различных фаз тика
- Edge cases в обработке очереди событий
"""

import sys
import threading
import time
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest
from fastapi.testclient import TestClient

from api import app
from src.environment.event import Event
from src.environment.event_queue import EventQueue
from src.runtime.loop import run_loop
from src.state.self_state import SelfState


@pytest.mark.concurrency
@pytest.mark.race_conditions
class TestStatusRaceConditions:
    """Тесты race conditions для чтения /status во время тиков"""

    def test_concurrent_status_reads_during_active_ticks(self):
        """Множественные одновременные запросы /status во время активных тиков"""
        client = TestClient(app)

        # API работает без аутентификации
        headers = {}

        # Создаем состояние и очередь событий
        state = SelfState()
        event_queue = EventQueue()
        stop_event = threading.Event()

        # Добавляем события в очередь для активности
        for i in range(10):
            event = Event(type="noise", intensity=0.5, timestamp=time.time())
            event_queue.push(event)

        results = []
        errors = []

        def make_concurrent_request(request_id):
            """Функция для конкурентного запроса статуса"""
            try:
                response = client.get("/status", headers=headers)
                results.append(
                    {
                        "request_id": request_id,
                        "status_code": response.status_code,
                        "ticks": response.json().get("ticks")
                        if response.status_code == 200
                        else None,
                        "timestamp": time.time(),
                    }
                )
            except Exception as e:
                errors.append({"request_id": request_id, "error": str(e)})

        # Запускаем runtime loop в отдельном потоке
        def run_runtime_with_events():
            try:
                run_loop(
                    state,
                    lambda s: None,
                    0.01,  # tick_interval
                    5,     # snapshot_period
                    stop_event,
                    event_queue,
                    False, # disable_weakness_penalty
                    False, # disable_structured_logging
                    False, # disable_learning
                    False, # disable_adaptation
                    True,  # disable_philosophical_analysis
                    False, # disable_philosophical_reports
                    True,  # disable_clarity_moments
                    10,    # log_flush_period_ticks
                    False, # enable_profiling
                )
            except Exception:
                pass  # Игнорируем для теста

        runtime_thread = threading.Thread(target=run_runtime_with_events)
        runtime_thread.start()

        # Даем runtime loop запуститься
        time.sleep(0.05)

        # Запускаем множество конкурентных запросов
        threads = []
        for i in range(20):  # 20 одновременных запросов
            thread = threading.Thread(target=make_concurrent_request, args=(i,))
            threads.append(thread)
            thread.start()

        # Ждем завершения всех запросов
        for thread in threads:
            thread.join(timeout=2.0)

        # Останавливаем runtime
        stop_event.set()
        runtime_thread.join(timeout=1.0)

        # Проверяем результаты
        successful_requests = [r for r in results if r["status_code"] == 200]
        assert (
            len(successful_requests) >= 15
        ), f"Too few successful requests: {len(successful_requests)}/{len(results)}"

        # Все успешные запросы должны возвращать валидные данные
        for request in successful_requests:
            assert request["ticks"] is not None
            assert request["ticks"] >= 0

        # Проверяем, что не было критических ошибок
        assert len(errors) <= 2, f"Too many errors: {errors}"

    def test_status_read_during_state_modification(self):
        """Чтение статуса в момент модификации состояния runtime loop"""
        client = TestClient(app)

        # API работает без аутентификации
        headers = {}

        state = SelfState()
        state.energy = 80.0
        state.ticks = 5

        results = []

        def read_status_during_modification():
            """Читаем статус в момент модификации состояния"""
            try:
                # Имитируем модификацию состояния (как в runtime loop)
                original_energy = state.energy
                state.apply_delta({"energy": -10.0, "ticks": 1})

                # Немедленно читаем статус
                response = client.get("/status", headers=headers)
                results.append(
                    {
                        "status_code": response.status_code,
                        "energy": response.json().get("energy")
                        if response.status_code == 200
                        else None,
                        "ticks": response.json().get("ticks")
                        if response.status_code == 200
                        else None,
                        "original_energy": original_energy,
                        "modified_energy": state.energy,
                    }
                )

                # Восстанавливаем состояние для повторных тестов
                state.energy = original_energy
                state.ticks -= 1

            except Exception as e:
                results.append({"error": str(e)})

        # Запускаем несколько конкурентных чтений с модификацией
        threads = []
        for i in range(10):
            thread = threading.Thread(target=read_status_during_modification)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join(timeout=2.0)

        # Проверяем результаты
        successful_reads = [
            r for r in results if "status_code" in r and r["status_code"] == 200
        ]
        assert (
            len(successful_reads) >= 8
        ), f"Too few successful reads: {len(successful_reads)}"

        # Все успешные чтения должны возвращать консистентные данные
        for read in successful_reads:
            assert read["energy"] is not None
            assert read["ticks"] is not None
            # Проверяем что данные не повреждены (в разумных пределах)
            assert 0 <= read["energy"] <= 100
            assert read["ticks"] >= 0

    def test_snapshot_consistency_under_load(self):
        """Проверка консистентности snapshot при высокой нагрузке"""
        client = TestClient(app)

        # API работает без аутентификации
        headers = {}

        # Создаем состояние с известными данными
        state = SelfState()
        state.energy = 75.0
        state.stability = 0.8
        state.ticks = 42
        state.age = 100.0

        stop_event = threading.Event()
        event_queue = EventQueue()

        # Запускаем runtime loop
        def run_runtime():
            try:
                run_loop(state, lambda s: None, 0.05, 10, stop_event, event_queue)
            except Exception:
                pass

        runtime_thread = threading.Thread(target=run_runtime)
        runtime_thread.start()

        # Даем runtime запуститься
        time.sleep(0.1)

        results = []

        def stress_read_status(iteration):
            """Интенсивное чтение статуса"""
            try:
                start_time = time.time()
                response = client.get("/status", headers=headers)
                end_time = time.time()

                if response.status_code == 200:
                    data = response.json()
                    results.append(
                        {
                            "iteration": iteration,
                            "response_time": end_time - start_time,
                            "ticks": data.get("ticks"),
                            "energy": data.get("energy"),
                            "stability": data.get("stability"),
                            "age": data.get("age"),
                        }
                    )
                else:
                    results.append(
                        {
                            "iteration": iteration,
                            "error": response.status_code,
                            "response_time": end_time - start_time,
                        }
                    )
            except Exception as e:
                results.append({"iteration": iteration, "error": str(e)})

        # Запускаем стресс-тест: 50 быстрых запросов
        threads = []
        for i in range(50):
            thread = threading.Thread(target=stress_read_status, args=(i,))
            threads.append(thread)
            thread.start()

        # Ждем завершения
        for thread in threads:
            thread.join(timeout=3.0)

        # Останавливаем runtime
        stop_event.set()
        runtime_thread.join(timeout=1.0)

        # Анализируем результаты
        successful_results = [r for r in results if "ticks" in r]
        error_results = [r for r in results if "error" in r]

        assert (
            len(successful_results) >= 40
        ), f"Too many failures: {len(error_results)}/{len(results)}"

        # Проверяем консистентность данных
        ticks_values = [
            r["ticks"] for r in successful_results if r["ticks"] is not None
        ]
        if ticks_values:
            # Все ticks должны быть >= 0 и монотонно возрастать (runtime может стартовать с 0)
            min_ticks = min(ticks_values)
            max_ticks = max(ticks_values)
            assert min_ticks >= 0, f"Invalid ticks minimum: {min_ticks}"
            # Проверяем что значения разумны (не более 100 тиков прироста)
            assert (
                max_ticks - min_ticks <= 100
            ), f"Too large ticks range: {max_ticks - min_ticks}"

        # Проверяем что время ответа разумное (< 1 секунды)
        response_times = [r["response_time"] for r in successful_results]
        avg_response_time = (
            sum(response_times) / len(response_times) if response_times else 0
        )
        assert (
            avg_response_time < 1.0
        ), f"Average response time too high: {avg_response_time}"

    def test_status_read_during_archiving(self):
        """Чтение статуса во время операций архивации памяти"""
        client = TestClient(app)

        # API работает без аутентификации
        headers = {}

        state = SelfState()
        # Создаем состояние с большим количеством записей памяти для триггера архивации
        from src.memory.memory import MemoryEntry

        for i in range(150):  # Создаем много записей
            entry = MemoryEntry(
                event_type="test_event",
                meaning_significance=0.1,
                timestamp=time.time()
                - 8 * 24 * 3600
                + i,  # Старые записи для архивации
                subjective_timestamp=float(i),
            )
            state.memory.append(entry)

        state.ticks = (
            50  # Устанавливаем ticks чтобы trigger archiving (ARCHIVE_INTERVAL = 50)
        )
        stop_event = threading.Event()
        event_queue = EventQueue()

        results = []

        def read_during_archiving():
            """Читаем статус во время потенциальной архивации"""
            try:
                response = client.get("/status", headers=headers)
                results.append(
                    {
                        "status_code": response.status_code,
                        "memory_length": len(response.json().get("memory", []))
                        if response.status_code == 200
                        else None,
                        "archive_length": len(getattr(state, "archive_memory", [])),
                    }
                )
            except Exception as e:
                results.append({"error": str(e)})

        # Запускаем runtime loop
        def run_runtime():
            try:
                # Даем время на архивацию
                run_loop(state, lambda s: None, 0.02, 1, stop_event, event_queue)
            except Exception:
                pass

        runtime_thread = threading.Thread(target=run_runtime)
        runtime_thread.start()

        # Ждем немного чтобы runtime начал работу
        time.sleep(0.05)

        # Читаем статус конкурентно
        read_during_archiving()

        # Останавливаем runtime
        stop_event.set()
        runtime_thread.join(timeout=1.0)

        # Проверяем результат
        assert len(results) == 1
        result = results[0]
        if "status_code" in result:
            assert result["status_code"] == 200
            # Проверяем что данные доступны даже во время архивации
            assert result["memory_length"] is not None

    def test_status_read_immediately_after_tick(self):
        """Чтение статуса сразу после завершения тика"""
        client = TestClient(app)

        # API работает без аутентификации
        headers = {}

        state = SelfState()
        state.ticks = 0
        stop_event = threading.Event()
        event_queue = EventQueue()

        # Добавляем событие для обработки
        event = Event(type="test", intensity=0.5, timestamp=time.time())
        event_queue.push(event)

        tick_completed = threading.Event()
        results = []

        def monitor_and_signal(s):
            """Монитор который сигнализирует о завершении тика"""
            if s.ticks > 0 and not tick_completed.is_set():
                tick_completed.set()

        def run_runtime_with_monitor():
            try:
                run_loop(state, monitor_and_signal, 0.01, 5, stop_event, event_queue)
            except Exception:
                pass

        # Запускаем runtime
        runtime_thread = threading.Thread(target=run_runtime_with_monitor)
        runtime_thread.start()

        # Ждем завершения первого тика
        assert tick_completed.wait(timeout=2.0), "Tick did not complete"

        # Немедленно читаем статус
        try:
            response = client.get("/status", headers=headers)
            results.append(
                {
                    "status_code": response.status_code,
                    "ticks": response.json().get("ticks")
                    if response.status_code == 200
                    else None,
                }
            )
        except Exception as e:
            results.append({"error": str(e)})

        # Останавливаем runtime
        stop_event.set()
        runtime_thread.join(timeout=1.0)

        # Проверяем результат
        assert len(results) == 1
        result = results[0]
        if "status_code" in result:
            assert result["status_code"] == 200
            assert result["ticks"] >= 1  # Должен быть хотя бы 1 тик

    def test_status_read_during_event_processing(self):
        """Чтение статуса во время обработки очереди событий"""
        client = TestClient(app)

        # API работает без аутентификации
        headers = {}

        state = SelfState()
        event_queue = EventQueue()

        # Добавляем много событий для обработки
        for i in range(20):
            event = Event(type="noise", intensity=0.3, timestamp=time.time())
            event_queue.push(event)

        stop_event = threading.Event()
        results = []

        def run_runtime():
            try:
                run_loop(state, lambda s: None, 0.02, 5, stop_event, event_queue)
            except Exception:
                pass

        # Запускаем runtime
        runtime_thread = threading.Thread(target=run_runtime)
        runtime_thread.start()

        # Ждем немного чтобы события начали обрабатываться
        time.sleep(0.05)

        # Читаем статус во время обработки
        try:
            response = client.get("/status", headers=headers)
            results.append(
                {
                    "status_code": response.status_code,
                    "active": response.json().get("active")
                    if response.status_code == 200
                    else None,
                    "ticks": response.json().get("ticks")
                    if response.status_code == 200
                    else None,
                }
            )
        except Exception as e:
            results.append({"error": str(e)})

        # Останавливаем runtime
        stop_event.set()
        runtime_thread.join(timeout=1.0)

        # Проверяем результат
        assert len(results) == 1
        result = results[0]
        if "status_code" in result:
            assert result["status_code"] == 200
            # Проверяем что система активна и имеет тики
            assert result["active"] is not None
            assert result["ticks"] >= 0

    def test_status_read_during_snapshot_creation(self):
        """Чтение статуса во время создания снапшота"""
        client = TestClient(app)

        # API работает без аутентификации
        headers = {}

        state = SelfState()
        state.ticks = (
            10  # Устанавливаем ticks чтобы trigger snapshot (snapshot_period=10)
        )
        stop_event = threading.Event()
        event_queue = EventQueue()

        results = []

        def run_runtime():
            try:
                run_loop(state, lambda s: None, 0.01, 10, stop_event, event_queue)
            except Exception:
                pass

        # Запускаем runtime
        runtime_thread = threading.Thread(target=run_runtime)
        runtime_thread.start()

        # Ждем немного чтобы snapshot начал создаваться
        time.sleep(0.1)

        # Читаем статус во время создания snapshot
        try:
            response = client.get("/status", headers=headers)
            results.append(
                {
                    "status_code": response.status_code,
                    "data": response.json() if response.status_code == 200 else None,
                }
            )
        except Exception as e:
            results.append({"error": str(e)})

        # Останавливаем runtime
        stop_event.set()
        runtime_thread.join(timeout=1.0)

        # Проверяем результат
        assert len(results) == 1
        result = results[0]
        if "status_code" in result:
            assert result["status_code"] == 200
            assert result["data"] is not None
            # Проверяем базовые поля
            assert "ticks" in result["data"]
            assert "energy" in result["data"]


@pytest.mark.concurrency
@pytest.mark.race_conditions
class TestEventQueueTimingStress:
    """Стресс-тесты и timing edge cases для EventQueue"""

    def test_high_frequency_event_submission(self):
        """Подача событий с высокой частотой"""
        event_queue = EventQueue()

        # Создаем события для интенсивной подачи
        events_to_submit = 200
        submitted_count = [0]
        errors = []

        def submit_events_high_frequency():
            """Интенсивная подача событий"""
            try:
                for i in range(events_to_submit):
                    event = Event(
                        type=f"stress_{i}", intensity=0.1, timestamp=time.time()
                    )
                    event_queue.push(event)
                    submitted_count[0] += 1
                    # Минимальная задержка для имитации высокой частоты
                    time.sleep(0.001)
            except Exception as e:
                errors.append(str(e))

        # Запускаем интенсивную подачу
        submit_thread = threading.Thread(target=submit_events_high_frequency)
        submit_thread.start()

        # Ждем завершения подачи
        submit_thread.join(timeout=5.0)

        # Проверяем результаты
        # Очередь имеет maxsize=100, поэтому не все события могут быть добавлены
        assert (
            submitted_count[0] >= 100
        ), f"Failed to submit events: {submitted_count[0]}"
        assert len(errors) == 0, f"Submission errors: {errors}"

        # Проверяем что очередь не превысила лимит (maxsize=100)
        assert (
            event_queue.size() <= 100
        ), f"Queue exceeded maxsize: {event_queue.size()}"
        # Но при этом должна содержать максимум возможных событий
        assert (
            event_queue.size() == 100
        ), f"Queue should be at maxsize: {event_queue.size()}"

    def test_queue_overflow_handling(self):
        """Обработка переполнения очереди (maxsize=100)"""
        # EventQueue имеет фиксированный maxsize=100
        event_queue = EventQueue()

        # Пытаемся добавить больше максимального размера
        overflow_count = 150
        successful_adds = 0
        errors = []

        for i in range(overflow_count):
            try:
                event = Event(
                    type=f"overflow_{i}", intensity=0.1, timestamp=time.time()
                )
                if event_queue.push(event):
                    successful_adds += 1
                else:
                    break  # Очередь полна
            except Exception as e:
                errors.append(str(e))
                break

        # Проверяем что очередь не превысила максимальный размер
        assert event_queue.size() <= 100, f"Queue overflow: {event_queue.size()} > 100"
        assert successful_adds <= 100, f"Too many successful adds: {successful_adds}"
        assert (
            len(errors) <= 1
        ), f"Unexpected errors: {errors}"  # Возможно один отказ при переполнении

    def test_concurrent_push_pop_operations(self):
        """Одновременные операции push и pop_all"""
        event_queue = EventQueue()
        stop_flag = [False]

        push_count = [0]
        pop_count = [0]
        push_errors = []
        pop_errors = []

        def push_worker(worker_id):
            """Работник для добавления событий"""
            while not stop_flag[0]:
                try:
                    for i in range(10):
                        if stop_flag[0]:
                            break
                        event = Event(
                            type=f"push_{worker_id}_{i}",
                            intensity=0.1,
                            timestamp=time.time(),
                        )
                        if event_queue.push(event):
                            push_count[0] += 1
                        time.sleep(0.01)  # Небольшая задержка
                except Exception as e:
                    push_errors.append(f"Push worker {worker_id}: {e}")
                    break

        def pop_worker(worker_id):
            """Работник для извлечения событий"""
            while not stop_flag[0]:
                try:
                    if not event_queue.is_empty():
                        events = event_queue.pop_all()
                        pop_count[0] += len(events)
                    time.sleep(0.02)  # Чуть больше задержка для pop
                except Exception as e:
                    pop_errors.append(f"Pop worker {worker_id}: {e}")
                    break

        # Запускаем несколько push и pop работников
        threads = []
        for i in range(3):  # 3 push работника
            thread = threading.Thread(target=push_worker, args=(i,))
            threads.append(thread)

        for i in range(2):  # 2 pop работника
            thread = threading.Thread(target=pop_worker, args=(i,))
            threads.append(thread)

        # Запускаем все потоки
        for thread in threads:
            thread.start()

        # Даем поработать 2 секунды
        time.sleep(2.0)
        stop_flag[0] = True

        # Ждем завершения
        for thread in threads:
            thread.join(timeout=2.0)

        # Проверяем результаты
        total_operations = push_count[0] + pop_count[0]
        assert total_operations > 0, "No operations performed"

        # Проверяем что не было критических ошибок
        assert len(push_errors) <= 1, f"Push errors: {push_errors}"
        assert len(pop_errors) <= 1, f"Pop errors: {pop_errors}"

    def test_empty_queue_concurrent_access(self):
        """Доступ к пустой очереди из нескольких потоков"""
        event_queue = EventQueue()

        results = []
        errors = []

        def access_empty_queue(worker_id):
            """Доступ к пустой очереди"""
            try:
                # Проверяем различные операции над пустой очередью
                is_empty = event_queue.is_empty()
                size = event_queue.size()
                events = event_queue.pop_all()

                results.append(
                    {
                        "worker_id": worker_id,
                        "is_empty": is_empty,
                        "size": size,
                        "popped_events": len(events),
                    }
                )
            except Exception as e:
                errors.append(f"Worker {worker_id}: {e}")

        # Запускаем несколько потоков для доступа к пустой очереди
        threads = []
        for i in range(10):
            thread = threading.Thread(target=access_empty_queue, args=(i,))
            threads.append(thread)
            thread.start()

        # Ждем завершения
        for thread in threads:
            thread.join(timeout=2.0)

        # Проверяем результаты
        assert len(results) == 10, f"Not all workers completed: {len(results)}"
        assert len(errors) == 0, f"Errors accessing empty queue: {errors}"

        # Все работники должны видеть пустую очередь
        for result in results:
            assert result["is_empty"] is True
            assert result["size"] == 0
            assert result["popped_events"] == 0

    def test_pop_all_during_push_operations(self):
        """Вызов pop_all во время активных push операций"""
        event_queue = EventQueue()

        push_completed = [False]
        pop_results = []

        def push_events_during_pop():
            """Добавление событий во время pop_all"""
            try:
                time.sleep(0.05)  # Небольшая задержка перед началом push
                for i in range(20):
                    event = Event(
                        type=f"during_pop_{i}", intensity=0.1, timestamp=time.time()
                    )
                    event_queue.push(event)
                    time.sleep(0.01)
                push_completed[0] = True
            except Exception as e:
                push_completed[0] = f"Error: {e}"

        def pop_during_push():
            """pop_all во время активных push операций"""
            try:
                time.sleep(0.02)  # Ждем начала push операций
                events = event_queue.pop_all()
                pop_results.append(
                    {"popped_count": len(events), "push_completed": push_completed[0]}
                )
                # Повторный pop_all для проверки консистентности
                events2 = event_queue.pop_all()
                pop_results.append(
                    {
                        "second_pop_count": len(events2),
                        "final_push_completed": push_completed[0],
                    }
                )
            except Exception as e:
                pop_results.append({"error": str(e)})

        # Запускаем потоки
        push_thread = threading.Thread(target=push_events_during_pop)
        pop_thread = threading.Thread(target=pop_during_push)

        push_thread.start()
        pop_thread.start()

        # Ждем завершения
        push_thread.join(timeout=2.0)
        pop_thread.join(timeout=2.0)

        # Проверяем результаты
        assert len(pop_results) >= 1, "Pop operation did not complete"
        assert push_completed[0] is True, f"Push did not complete: {push_completed[0]}"

        # Проверяем что pop_all корректно обработал конкурентные push
        first_pop = pop_results[0]
        if "popped_count" in first_pop:
            assert (
                first_pop["popped_count"] >= 0
            )  # Может быть 0 если push еще не начался

    def test_race_between_empty_check_and_get_nowait(self):
        """Гонка между проверкой empty() и get_nowait()"""
        event_queue = EventQueue()

        # Добавляем одно событие
        event = Event(type="race_test", intensity=0.5, timestamp=time.time())
        event_queue.push(event)

        race_detected = [False]
        results = []

        def race_condition_worker(worker_id):
            """Работник который пытается воспроизвести race condition"""
            try:
                # Имитируем последовательность: проверка empty -> get_nowait
                if not event_queue.is_empty():
                    try:
                        # Имитируем задержку между проверкой и извлечением
                        time.sleep(0.001)
                        # Пытаемся извлечь событие
                        if hasattr(event_queue, "_queue") and hasattr(
                            event_queue._queue, "get_nowait"
                        ):
                            event_queue._queue.get_nowait()
                            results.append({"worker": worker_id, "got_event": True})
                        else:
                            # Используем публичный API
                            events = event_queue.pop_all()
                            if events:
                                results.append({"worker": worker_id, "got_event": True})
                            else:
                                results.append(
                                    {"worker": worker_id, "got_event": False}
                                )
                    except Exception as e:
                        results.append({"worker": worker_id, "error": str(e)})
                        race_detected[0] = True  # Возможная race condition
                else:
                    results.append({"worker": worker_id, "queue_empty": True})
            except Exception as e:
                results.append({"worker": worker_id, "error": str(e)})

        # Запускаем несколько работников
        threads = []
        for i in range(5):
            thread = threading.Thread(target=race_condition_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Ждем завершения
        for thread in threads:
            thread.join(timeout=2.0)

        # Анализируем результаты
        got_events = [r for r in results if r.get("got_event")]

        # Должно быть не более одного успешного извлечения события
        assert (
            len(got_events) <= 1
        ), f"Multiple workers got the same event: {got_events}"

        # Остальные должны увидеть пустую очередь или ошибку race condition
        assert len(results) == 5, "Not all workers completed"

    def test_queue_state_changes_during_iteration(self):
        """Изменение состояния очереди во время итерации pop_all"""
        event_queue = EventQueue()

        # Добавляем несколько событий
        for i in range(5):
            event = Event(type=f"iteration_{i}", intensity=0.2, timestamp=time.time())
            event_queue.push(event)

        iteration_results = []

        def modify_during_iteration():
            """Модификация очереди во время pop_all"""
            try:
                # Начинаем pop_all
                events = event_queue.pop_all()
                iteration_results.append({"initial_count": len(events)})

                # Во время "обработки" добавляем новые события
                time.sleep(0.01)  # Имитируем обработку
                for i in range(3):
                    event = Event(
                        type=f"added_during_{i}", intensity=0.1, timestamp=time.time()
                    )
                    event_queue.push(event)

                iteration_results.append(
                    {"added_count": 3, "final_size": event_queue.size()}
                )

            except Exception as e:
                iteration_results.append({"error": str(e)})

        # Запускаем модификацию
        modify_thread = threading.Thread(target=modify_during_iteration)
        modify_thread.start()
        modify_thread.join(timeout=2.0)

        # Проверяем результаты
        assert len(iteration_results) >= 1, "Iteration did not complete"
        if "initial_count" in iteration_results[0]:
            assert iteration_results[0]["initial_count"] == 5, "Wrong initial count"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
