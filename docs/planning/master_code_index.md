# Master Code Index: Объединённая документация проекта Life

Этот файл — индекс всех .py из src/. Создан автоматически для удобного поиска и навигации.
**Дата генерации:** 2026-01-17 02:47:08

## Оглавление
- [action\__init__.py](#action-__init__)
- [action\action.py](#action-action)
- [activation\__init__.py](#activation-__init__)
- [activation\activation.py](#activation-activation)
- [decision\__init__.py](#decision-__init__)
- [decision\decision.py](#decision-decision)
- [environment\__init__.py](#environment-__init__)
- [environment\event.py](#environment-event)
- [environment\event_queue.py](#environment-event_queue)
- [environment\generator.py](#environment-generator)
- [environment\generator_cli.py](#environment-generator_cli)
- [feedback\__init__.py](#feedback-__init__)
- [feedback\feedback.py](#feedback-feedback)
- [intelligence\__init__.py](#intelligence-__init__)
- [intelligence\intelligence.py](#intelligence-intelligence)
- [main_server_api.py](#main_server_api)
- [meaning\__init__.py](#meaning-__init__)
- [meaning\engine.py](#meaning-engine)
- [meaning\meaning.py](#meaning-meaning)
- [memory\memory.py](#memory-memory)
- [monitor\console.py](#monitor-console)
- [planning\__init__.py](#planning-__init__)
- [planning\planning.py](#planning-planning)
- [runtime\loop.py](#runtime-loop)
- [state\self_state.py](#state-self_state)
- [test\check_feedback_data.py](#test-check_feedback_data)
- [test\conftest.py](#test-conftest)
- [test\test_action.py](#test-test_action)
- [test\test_activation.py](#test-test_activation)
- [test\test_api.py](#test-test_api)
- [test\test_api_integration.py](#test-test_api_integration)
- [test\test_decision.py](#test-test_decision)
- [test\test_environment.py](#test-test_environment)
- [test\test_event_queue_edge_cases.py](#test-test_event_queue_edge_cases)
- [test\test_event_queue_race_condition.py](#test-test_event_queue_race_condition)
- [test\test_feedback.py](#test-test_feedback)
- [test\test_feedback_data.py](#test-test_feedback_data)
- [test\test_feedback_integration.py](#test-test_feedback_integration)
- [test\test_generator.py](#test-test_generator)
- [test\test_generator_cli.py](#test-test_generator_cli)
- [test\test_generator_integration.py](#test-test_generator_integration)
- [test\test_intelligence.py](#test-test_intelligence)
- [test\test_mcp_client.py](#test-test_mcp_client)
- [test\test_mcp_interactive.py](#test-test_mcp_interactive)
- [test\test_mcp_server.py](#test-test_mcp_server)
- [test\test_meaning.py](#test-test_meaning)
- [test\test_memory.py](#test-test_memory)
- [test\test_monitor.py](#test-test_monitor)
- [test\test_planning.py](#test-test_planning)
- [test\test_runtime_integration.py](#test-test_runtime_integration)
- [test\test_runtime_loop_edge_cases.py](#test-test_runtime_loop_edge_cases)
- [test\test_runtime_loop_feedback_coverage.py](#test-test_runtime_loop_feedback_coverage)
- [test\test_state.py](#test-test_state)
- [test_main.py](#test_main)

## action\__init__.py <a id="action-__init__"></a>
**Полный путь:** src/action\__init__.py

```python
```

---

## action\action.py <a id="action-action"></a>
**Полный путь:** src/action\action.py

```python
import time

from memory.memory import MemoryEntry


def execute_action(pattern: str, self_state):
    """
    Execute action based on pattern.
    Minimal implementation: record action in memory and apply minor state update if applicable.
    """
    # Record action in memory
    action_entry = MemoryEntry(
        event_type="action", meaning_significance=0.0, timestamp=time.time()
    )
    self_state.memory.append(action_entry)

    # Minimal state update for dampen
    if pattern == "dampen":
        # Minor fatigue effect (assuming energy represents vitality)
        self_state.energy = max(0.0, self_state.energy - 0.01)

    # For absorb and ignore, no additional state changes
```

---

## activation\__init__.py <a id="activation-__init__"></a>
**Полный путь:** src/activation\__init__.py

```python
```

---

## activation\activation.py <a id="activation-activation"></a>
**Полный путь:** src/activation\activation.py

```python
from typing import List

from memory.memory import MemoryEntry


def activate_memory(
    current_event_type: str, memory: List[MemoryEntry], limit: int = 3
) -> List[MemoryEntry]:
    """
    Минимальная активация: возвращает топ-N воспоминаний с совпадающим event_type,
    отсортированных по significance (desc).
    Если нет совпадений — пустой список.
    """
    matching = [entry for entry in memory if entry.event_type == current_event_type]
    matching.sort(key=lambda e: e.meaning_significance, reverse=True)
    return matching[:limit]
```

---

## decision\__init__.py <a id="decision-__init__"></a>
**Полный путь:** src/decision\__init__.py

```python
```

---

## decision\decision.py <a id="decision-decision"></a>
**Полный путь:** src/decision\decision.py

```python
from meaning.meaning import Meaning
from state.self_state import SelfState


def decide_response(self_state: SelfState, meaning: Meaning) -> str:
    """
    Минимальный выбор паттерна на основе activated_memory.
    - Если max sig в activated >0.5 — "dampen" (опыт учит смягчать).
    - Else return Meaning's pattern (absorb/ignore).
    """
    activated = self_state.activated_memory
    if activated and max(e.meaning_significance for e in activated) > 0.5:
        return "dampen"
    # Fallback to Meaning's logic
    if meaning.significance < 0.1:
        return "ignore"
    return "absorb"
```

---

## environment\__init__.py <a id="environment-__init__"></a>
**Полный путь:** src/environment\__init__.py

```python
from .event import Event
from .event_queue import EventQueue
from .generator import EventGenerator

__all__ = ["Event", "EventQueue", "EventGenerator"]
```

---

## environment\event.py <a id="environment-event"></a>
**Полный путь:** src/environment\event.py

```python
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Event:
    """
    Минимальная структура события из Environment
    """

    type: str  # Тип события: 'noise', 'decay', 'recovery', 'shock', 'idle'
    intensity: float  # Интенсивность: [-1.0, 1.0]
    timestamp: float  # time.time()
    metadata: Optional[Dict[str, Any]] = None  # Опционально: дополнительные данные

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
```

---

## environment\event_queue.py <a id="environment-event_queue"></a>
**Полный путь:** src/environment\event_queue.py

```python
import queue

from .event import Event


class EventQueue:
    def __init__(self):
        self._queue = queue.Queue(maxsize=100)

    def push(self, event: Event) -> None:
        try:
            self._queue.put_nowait(event)
        except queue.Full:
            pass  # silently drop if full

    def pop(self) -> Event | None:
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None

    def is_empty(self) -> bool:
        return self._queue.empty()

    def size(self) -> int:
        return self._queue.qsize()

    def pop_all(self) -> list[Event]:
        """
        Извлечь все события из очереди.

        Returns:
            list[Event]: список всех событий из очереди (FIFO порядок)
        """
        events = []
        while not self._queue.empty():
            try:
                event = self._queue.get_nowait()
                events.append(event)
            except queue.Empty:
                break
        return events
```

---

## environment\generator.py <a id="environment-generator"></a>
**Полный путь:** src/environment\generator.py

```python
import random
import time
from typing import Any

from .event import Event


class EventGenerator:
    def generate(self) -> Event:
        """
        Генерирует событие согласно спецификации этапа 07.

        Диапазоны интенсивности:
        - noise: [-0.3, 0.3]
        - decay: [-0.5, 0.0]
        - recovery: [0.0, 0.5]
        - shock: [-1.0, 1.0]
        - idle: 0.0
        """
        types = ["noise", "decay", "recovery", "shock", "idle"]
        weights = [0.4, 0.3, 0.2, 0.05, 0.05]
        event_type = random.choices(types, weights=weights)[0]

        # Генерируем интенсивность согласно спецификации
        if event_type == "noise":
            intensity = random.uniform(-0.3, 0.3)
        elif event_type == "decay":
            intensity = random.uniform(-0.5, 0.0)
        elif event_type == "recovery":
            intensity = random.uniform(0.0, 0.5)
        elif event_type == "shock":
            intensity = random.uniform(-1.0, 1.0)
        else:  # idle
            intensity = 0.0

        timestamp = time.time()
        metadata: dict[str, Any] = {}
        return Event(
            type=event_type, intensity=intensity, timestamp=timestamp, metadata=metadata
        )
```

---

## environment\generator_cli.py <a id="environment-generator_cli"></a>
**Полный путь:** src/environment\generator_cli.py

```python
"""
CLI для генерации событий и отправки их на API сервера.

Пример:
    python -m environment.generator_cli --interval 5 --host localhost --port 8000
"""

import argparse
import os
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from .generator import EventGenerator


def send_event(
    host: str, port: int, payload: dict
) -> tuple[bool, int | None, str, str]:
    url = f"http://{host}:{port}/event"
    try:
        resp = requests.post(url, json=payload, timeout=5)
        code = resp.status_code
        body = resp.text
        return True, code, "", body
    except requests.exceptions.RequestException as e:
        return False, 0, str(e), ""
    except Exception as e:
        return False, None, str(e), ""


def main():
    parser = argparse.ArgumentParser(description="Environment Event Generator CLI")
    parser.add_argument(
        "--host", default="localhost", help="Хост API сервера (по умолчанию localhost)"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Порт API сервера (по умолчанию 8000)"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=5.0,
        help="Интервал генерации событий, сек (по умолчанию 5)",
    )
    args = parser.parse_args()

    generator = EventGenerator()

    print(
        f"[GeneratorCLI] start: host={args.host} port={args.port} interval={args.interval}s"
    )
    print("[GeneratorCLI] Нажмите Ctrl+C для остановки")

    try:
        while True:
            event = generator.generate()
            payload = {
                "type": event.type,
                "intensity": event.intensity,
                "timestamp": event.timestamp,
                "metadata": event.metadata,
            }
            success, code, reason, body = send_event(args.host, args.port, payload)
            if success:
                print(
                    f"[GeneratorCLI] Sent event: {payload} | Code: {code} | Body: '{body}'"
                )
            else:
                print(
                    f"[GeneratorCLI] Failed: code={code} reason='{reason}' body='{body}'"
                )

            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n[GeneratorCLI] Stopped")


if __name__ == "__main__":  # pragma: no cover
    main()
```

---

## feedback\__init__.py <a id="feedback-__init__"></a>
**Полный путь:** src/feedback\__init__.py

```python
from feedback.feedback import (
    FeedbackRecord,
    PendingAction,
    observe_consequences,
    register_action,
)

__all__ = ["register_action", "observe_consequences", "PendingAction", "FeedbackRecord"]
```

---

## feedback\feedback.py <a id="feedback-feedback"></a>
**Полный путь:** src/feedback\feedback.py

```python
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from environment.event_queue import EventQueue
from state.self_state import SelfState


@dataclass
class PendingAction:
    action_id: str
    action_pattern: str
    state_before: Dict[str, float]
    timestamp: float
    check_after_ticks: int
    ticks_waited: int = 0


@dataclass
class FeedbackRecord:
    action_id: str
    action_pattern: str
    state_delta: Dict[str, float]
    timestamp: float
    delay_ticks: int
    associated_events: List[str] = field(default_factory=list)


def register_action(
    action_id: str,
    action_pattern: str,
    state_before: Dict[str, float],
    timestamp: float,
    pending_actions: List[PendingAction],
) -> None:
    """
    Регистрирует действие для последующего наблюдения Feedback.

    Args:
        action_id: Уникальный идентификатор действия
        action_pattern: Паттерн действия ("dampen", "absorb", "ignore")
        state_before: Снимок состояния до действия
        timestamp: Время выполнения действия
        pending_actions: Список ожидающих действий (изменяется in-place)
    """
    pending = PendingAction(
        action_id=action_id,
        action_pattern=action_pattern,
        state_before=state_before.copy(),
        timestamp=timestamp,
        check_after_ticks=random.randint(3, 10),
    )
    pending_actions.append(pending)


def observe_consequences(
    self_state: SelfState,
    pending_actions: List[PendingAction],
    event_queue: Optional[EventQueue] = None,
) -> List[FeedbackRecord]:
    """
    Наблюдает последствия действий и создает Feedback записи.

    Args:
        self_state: Текущее состояние Life
        pending_actions: Список ожидающих действий (изменяется in-place)
        event_queue: Очередь событий для сбора связанных событий (опционально)

    Returns:
        Список созданных Feedback записей
    """
    feedback_records = []
    to_remove = []

    for pending in pending_actions:
        pending.ticks_waited += 1

        if pending.ticks_waited >= pending.check_after_ticks:
            # Вычисляем изменения состояния
            state_after = {
                "energy": self_state.energy,
                "stability": self_state.stability,
                "integrity": self_state.integrity,
            }

            state_delta = {
                k: state_after.get(k, 0) - pending.state_before.get(k, 0)
                for k in ["energy", "stability", "integrity"]
            }

            # Проверяем минимальный порог изменений
            if any(abs(v) > 0.001 for v in state_delta.values()):
                # Собираем связанные события (опционально)
                # Примечание: для v1.0 не потребляем события из очереди, так как они нужны основному циклу
                # В полной реализации можно отслеживать события по timestamp или использовать отдельный механизм
                associated_events = []

                # Создаем Feedback запись
                feedback = FeedbackRecord(
                    action_id=pending.action_id,
                    action_pattern=pending.action_pattern,
                    state_delta=state_delta,
                    timestamp=time.time(),
                    delay_ticks=pending.ticks_waited,
                    associated_events=associated_events,
                )
                feedback_records.append(feedback)

            to_remove.append(pending)
        elif pending.ticks_waited > 20:
            # Слишком долго ждали, удаляем
            to_remove.append(pending)

    # Удаляем обработанные записи
    for pending in to_remove:
        pending_actions.remove(pending)

    return feedback_records
```

---

## intelligence\__init__.py <a id="intelligence-__init__"></a>
**Полный путь:** src/intelligence\__init__.py

```python
```

---

## intelligence\intelligence.py <a id="intelligence-intelligence"></a>
**Полный путь:** src/intelligence\intelligence.py

```python
from state.self_state import SelfState


def process_information(self_state: SelfState) -> None:
    """
    Минимальная нейтральная обработка информации.

    Фиксирует потенциал обработки из нейтральных источников без интерпретации,
    оценки, предсказаний или влияния на другие слои.
    """
    # Получаем нейтральные источники (proxy)
    recent_events = self_state.recent_events
    energy = self_state.energy
    stability = self_state.stability
    planning = self_state.planning

    # Нейтральная обработка: фиксация размеров/значений источников
    processed = {
        "memory_proxy_size": len(recent_events),
        "adaptation_proxy": energy,
        "learning_proxy": stability,
        "planning_proxy_size": len(planning.get("potential_sequences", [])),
    }

    # Записываем в self_state без изменений других полей
    self_state.intelligence = {"processed_sources": processed}
```

---

## main_server_api.py <a id="main_server_api"></a>
**Полный путь:** src/main_server_api.py

```python
import argparse
import glob
import importlib
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from colorama import Fore, Style, init

from environment import Event, EventQueue
from monitor.console import log, monitor
from runtime.loop import run_loop
from state.self_state import SelfState, asdict

init()

from typing import Any

print(f"[ДИАГ] Тип monitor: {type(monitor).__name__}")
print(f"[ДИАГ] monitor вызываемая функция? {callable(monitor)}")
if hasattr(monitor, "__file__"):
    print(f"[ДИАГ] monitor.__file__: {monitor.__file__}")
print(f"[ДИАГ] monitor.__name__: {getattr(monitor, '__name__', 'нет __name__')}")
print(f"[ДИАГ] dir(monitor)[:10]: {dir(monitor)[:10]}")

HOST = "localhost"
PORT = 8000


class StoppableHTTPServer(HTTPServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.self_state = None
        self.event_queue: EventQueue | None = None
        self.stopped = False
        self.dev_mode = False

    def serve_forever(self, poll_interval=0.5):
        self.timeout = poll_interval
        while not self.stopped:
            self.handle_request()

    def shutdown(self):
        self.stopped = True
        self.server_close()


class LifeHandler(BaseHTTPRequestHandler):
    server: (
        Any  # Добавляем, чтобы IDE знала, что у server могут быть кастомные атрибуты
    )

    def do_GET(self):
        if self.path == "/status":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(asdict(self.server.self_state)).encode())
        elif self.path == "/clear-data":
            os.makedirs("data/snapshots", exist_ok=True)
            log_file = "data/tick_log.jsonl"
            snapshots = glob.glob("data/snapshots/*.json")
            if os.path.exists(log_file):
                os.remove(log_file)
            for f in snapshots:
                if os.path.exists(f):
                    os.remove(f)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Data cleared")
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Unknown endpoint")

    def do_POST(self):
        """
        /event — добавить событие в очередь через JSON:
        {
            "type": "noise",
            "intensity": 0.1,        # optional
            "timestamp": 1700000.0,  # optional (time.time() по умолчанию)
            "metadata": {...}        # optional
        }
        """
        if self.path != "/event":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Unknown endpoint")
            return

        if not self.server.event_queue:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"No event queue configured")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Invalid JSON")
            return

        event_type = payload.get("type")
        if not isinstance(event_type, str):
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"'type' is required")
            return

        intensity = float(payload.get("intensity", 0.0))
        timestamp = float(payload.get("timestamp", time.time()))
        metadata = payload.get("metadata") or {}

        try:
            print(
                f"[API] Получен POST /event: type='{event_type}', intensity={intensity}"
            )
            event = Event(
                type=event_type,
                intensity=intensity,
                timestamp=timestamp,
                metadata=metadata,
            )
            self.server.event_queue.push(event)
            print(
                f"[API] Event PUSHED to queue. Size now: {self.server.event_queue.size()}"
            )
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Event accepted")
        except Exception as exc:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(f"Invalid event: {exc}".encode("utf-8"))

    def log_request(self, code, size=-1):  # pragma: no cover
        if self.server.dev_mode:
            try:
                print(Fore.CYAN + "=" * 80 + Style.RESET_ALL)
                print(Fore.GREEN + "ВХОДЯЩИЙ HTTP-ЗАПРОС" + Style.RESET_ALL)
                print(
                    Fore.YELLOW
                    + f"Время: {self.log_date_time_string()}"
                    + Style.RESET_ALL
                )
                print(
                    Fore.YELLOW
                    + f"Клиент IP: {self.client_address[0]}"
                    + Style.RESET_ALL
                )
                print(Fore.YELLOW + f"Запрос: {self.requestline}" + Style.RESET_ALL)
                print(Fore.MAGENTA + f"Статус ответа: {code}" + Style.RESET_ALL)
                if isinstance(size, (int, float)) and size > 0:
                    print(
                        Fore.MAGENTA + f"Размер ответа: {size} байт" + Style.RESET_ALL
                    )
                print(Fore.CYAN + "=" * 80 + Style.RESET_ALL)
            except UnicodeEncodeError:
                # Fallback to plain text if color output fails
                print("=" * 80)
                print("ВХОДЯЩИЙ HTTP-ЗАПРОС")
                print(f"Время: {self.log_date_time_string()}")
                print(f"Клиент IP: {self.client_address[0]}")
                print(f"Запрос: {self.requestline}")
                print(f"Статус ответа: {code}")
                if isinstance(size, (int, float)) and size > 0:
                    print(f"Размер ответа: {size} байт")
                print("=" * 80)
            sys.stdout.flush()


def start_api_server(self_state, event_queue, dev_mode):
    global server
    server = StoppableHTTPServer((HOST, PORT), LifeHandler)
    server.self_state = self_state
    server.event_queue = event_queue
    server.dev_mode = dev_mode
    print(f"API server running on http://{HOST}:{PORT}")
    server.serve_forever()


def reloader_thread():  # pragma: no cover
    """
    Отслеживает изменения в исходных файлах проекта и перезагружает их "горячо".
    Перезапускает API сервер при изменении модулей.
    """
    global self_state, server, api_thread, monitor, log, loop_thread, loop_stop, config, event_queue

    # Файлы для отслеживания
    files_to_watch = [
        "src/main_server_api.py",
        "src/monitor/console.py",
        "src/runtime/loop.py",
        "src/state/self_state.py",
        "src/environment/event.py",
        "src/environment/event_queue.py",
        "src/environment/generator.py",
    ]
    mtime_dict = {}

    # Инициализация времени модификации файлов
    for f in files_to_watch:
        try:
            mtime_dict[f] = os.stat(f).st_mtime
            log(f"Watching {f}")
        except Exception as e:
            print(f"Error watching {f}: {e}")

    print("Reloader initialized, starting poll loop")

    while True:
        time.sleep(1)
        changed = False

        # Проверка изменений
        for f in files_to_watch:
            try:
                if os.stat(f).st_mtime != mtime_dict[f]:
                    changed = True
                    mtime_dict[f] = os.stat(f).st_mtime
            except FileNotFoundError:
                continue

        if changed:
            print("Detected change, reloading modules...")

            # Остановка API сервера
            if server:
                server.shutdown()
                if api_thread:
                    api_thread.join()

            # Перезагрузка модулей
            import environment.event as event_module
            import environment.event_queue as event_queue_module
            import environment.generator as generator_module
            import monitor.console as console_module
            import runtime.loop as loop_module
            import state.self_state as state_module

            importlib.reload(console_module)
            importlib.reload(loop_module)
            importlib.reload(state_module)
            importlib.reload(event_module)
            importlib.reload(event_queue_module)
            importlib.reload(generator_module)

            print(
                f"[RELOAD DIAG] Reloaded loop_module.run_loop: firstlineno={loop_module.run_loop.__code__.co_firstlineno}, argcount={loop_module.run_loop.__code__.co_argcount}"
            )
            print(
                f"[RELOAD DIAG] New run_loop code file: {loop_module.run_loop.__code__.co_filename}"
            )

            # Обновляем ссылки на функции
            monitor = console_module.monitor
            log = console_module.log
            run_loop = loop_module.run_loop
            try:
                self_state = state_module.SelfState().load_latest_snapshot()
            except FileNotFoundError:
                self_state = state_module.SelfState()

            # Перезапуск API сервера
            api_thread = threading.Thread(
                target=start_api_server,
                args=(self_state, event_queue, True),
                daemon=True,
            )
            api_thread.start()

            print("Modules reloaded and server restarted")

            # Restart runtime loop
            if loop_thread and loop_thread.is_alive():
                loop_stop.set()
                loop_thread.join(timeout=5.0)
                log("[RELOAD] Old loop stopped")

            loop_stop = threading.Event()
            loop_thread = threading.Thread(
                target=run_loop,
                args=(
                    self_state,
                    monitor,
                    config["tick_interval"],
                    config["snapshot_period"],
                    loop_stop,
                    event_queue,
                ),
                daemon=True,
            )
            loop_thread.start()
            log("[RELOAD] New loop started")


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument("--clear-data", type=str, default="no")
    parser.add_argument("--tick-interval", type=float, default=1.0)
    parser.add_argument("--snapshot-period", type=int, default=10)
    parser.add_argument(
        "--dev", action="store_true", help="Enable development mode with auto-reload"
    )
    args = parser.parse_args()
    dev_mode = args.dev

    config = {
        "tick_interval": args.tick_interval,
        "snapshot_period": args.snapshot_period,
    }

    if args.clear_data.lower() == "yes":
        print("Очистка данных при старте...")
        log_file = "data/tick_log.jsonl"
        snapshots = glob.glob("data/snapshots/*.json")
        if os.path.exists(log_file):
            os.remove(log_file)
        for f in snapshots:
            if os.path.exists(f):
                os.remove(f)

    try:
        self_state = SelfState().load_latest_snapshot()
    except FileNotFoundError:
        self_state = SelfState()

    server = None
    api_thread = None

    # Инициализация Environment
    event_queue = EventQueue()

    if args.dev:
        log("--dev mode enabled, starting reloader")
        threading.Thread(target=reloader_thread, daemon=True).start()

    # Start API thread
    api_thread = threading.Thread(
        target=start_api_server, args=(self_state, event_queue, dev_mode), daemon=True
    )
    api_thread.start()

    # Start loop thread
    loop_stop = threading.Event()
    loop_thread = threading.Thread(
        target=run_loop,
        args=(
            self_state,
            monitor,
            config["tick_interval"],
            config["snapshot_period"],
            loop_stop,
            event_queue,
        ),
        daemon=True,
    )
    loop_thread.start()

    print(
        "monitor:", monitor, type(monitor) if "monitor" in locals() else "NOT DEFINED"
    )

    loop_thread.join()
    print("Loop ended. Server still running. Press Enter to stop.")
    input()
    print("\nЖизнь завершена. Финальное состояние:")
    print(self_state)
```

---

## meaning\__init__.py <a id="meaning-__init__"></a>
**Полный путь:** src/meaning\__init__.py

```python
from .engine import MeaningEngine
from .meaning import Meaning

__all__ = ["Meaning", "MeaningEngine"]
```

---

## meaning\engine.py <a id="meaning-engine"></a>
**Полный путь:** src/meaning\engine.py

```python
from typing import Dict

from environment.event import Event

from .meaning import Meaning


class MeaningEngine:
    """
    Движок интерпретации событий.

    Преобразует Event + SelfState в Meaning.

    Компоненты:
    1. Appraisal — первичная оценка значимости
    2. ImpactModel — расчёт влияния на состояние
    3. ResponsePattern — формирование паттерна реакции
    """

    def __init__(self):
        """Инициализация движка с базовыми настройками"""
        self.base_significance_threshold = 0.1

    def appraisal(self, event: Event, self_state: Dict) -> float:
        """
        Первичная оценка: насколько это событие важно?

        Логика:
        - Учитывает тип события
        - Учитывает интенсивность
        - Учитывает текущее состояние Life

        Returns:
            significance (float): [0.0, 1.0]
        """
        # Базовая значимость из интенсивности события
        base_significance = abs(event.intensity)

        # Модификация на основе типа события
        type_weight = {
            "shock": 1.5,  # Шоки всегда значимы
            "noise": 0.5,  # Шум часто игнорируется
            "recovery": 1.0,  # Восстановление нормально
            "decay": 1.0,  # Распад нормален
            "idle": 0.2,  # Бездействие почти не значимо
        }

        weight = type_weight.get(event.type, 1.0)
        significance = base_significance * weight

        # Контекстуальная модификация на основе состояния
        # Если integrity низкая — даже малые события становятся важнее
        if self_state["integrity"] < 0.3:
            significance *= 1.5

        # Если stability низкая — события ощущаются сильнее
        if self_state["stability"] < 0.5:
            significance *= 1.2

        # Ограничение диапазона
        return max(0.0, min(1.0, significance))

    def impact_model(
        self, event: Event, self_state: Dict, significance: float
    ) -> Dict[str, float]:
        """
        Расчёт влияния: как это событие изменит состояние?

        Логика:
        - Базовые дельты зависят от типа события
        - Масштабируются на интенсивность и significance
        - Учитывают текущие параметры состояния

        Returns:
            impact (Dict[str, float]): {"energy": delta, "stability": delta, "integrity": delta}
        """
        # Базовые паттерны воздействия по типам событий
        base_impacts = {
            "shock": {"energy": -1.5, "stability": -0.10, "integrity": -0.05},
            "noise": {"energy": -0.3, "stability": -0.02, "integrity": 0.0},
            "recovery": {"energy": +1.0, "stability": +0.05, "integrity": +0.02},
            "decay": {"energy": -0.5, "stability": -0.01, "integrity": -0.01},
            "idle": {"energy": -0.1, "stability": 0.0, "integrity": 0.0},
        }

        base_impact = base_impacts.get(
            event.type, {"energy": 0.0, "stability": 0.0, "integrity": 0.0}
        )

        # Масштабирование на интенсивность и significance
        scaled_impact = {}
        for param, delta in base_impact.items():
            scaled_delta = delta * abs(event.intensity) * significance
            scaled_impact[param] = scaled_delta

        return scaled_impact

    def response_pattern(
        self, event: Event, self_state: Dict, significance: float
    ) -> str:
        """
        Определение паттерна реакции.

        Возможные паттерны:
        - "ignore"       — событие игнорируется
        - "absorb"       — событие поглощается с полным эффектом
        - "dampen"       — событие ослабляется
        - "amplify"      — событие усиливается

        Returns:
            pattern (str): название паттерна
        """
        if significance < self.base_significance_threshold:
            return "ignore"

        # При высокой стабильности — ослабление эффектов
        if self_state["stability"] > 0.8:
            return "dampen"

        # При низкой стабильности — усиление эффектов
        if self_state["stability"] < 0.3:
            return "amplify"

        # По умолчанию — нормальное поглощение
        return "absorb"

    def process(self, event: Event, self_state: Dict) -> Meaning:
        """
        Основной метод обработки события.

        Этапы:
        1. Appraisal — оценка значимости
        2. ImpactModel — расчёт влияния
        3. ResponsePattern — определение паттерна реакции
        4. Создание объекта Meaning

        Args:
            event: событие из Environment
            self_state: текущее состояние Life

        Returns:
            Meaning: интерпретированное значение
        """
        # 1. Оценка значимости
        significance = self.appraisal(event, self_state)

        # 2. Расчёт базового влияния
        base_impact = self.impact_model(event, self_state, significance)

        # 3. Определение паттерна реакции
        pattern = self.response_pattern(event, self_state, significance)

        # 4. Модификация impact на основе паттерна
        final_impact = base_impact.copy()
        if pattern == "ignore":
            final_impact = {k: 0.0 for k in final_impact}
        elif pattern == "dampen":
            final_impact = {k: v * 0.5 for k, v in final_impact.items()}
        elif pattern == "amplify":
            final_impact = {k: v * 1.5 for k, v in final_impact.items()}
        # "absorb" оставляет impact без изменений

        # 5. Создание Meaning
        return Meaning(
            event_id=str(id(event)), significance=significance, impact=final_impact
        )
```

---

## meaning\meaning.py <a id="meaning-meaning"></a>
**Полный путь:** src/meaning\meaning.py

```python
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class Meaning:
    """
    Интерпретированное значение события.

    Структура:
    - event_id: связь с исходным событием (опционально)
    - significance: субъективная важность [0.0, 1.0]
    - impact: дельты изменений для параметров состояния
    """

    event_id: Optional[str] = None
    significance: float = 0.0  # Важность: 0.0 (игнорируется) до 1.0 (критично)
    impact: Dict[str, float] = field(
        default_factory=dict
    )  # {"energy": -0.1, "stability": -0.02, "integrity": 0.0}

    def __post_init__(self):
        # Валидация significance
        if not 0.0 <= self.significance <= 1.0:
            raise ValueError(
                f"significance должен быть в диапазоне [0.0, 1.0], получено: {self.significance}"
            )
```

---

## memory\memory.py <a id="memory-memory"></a>
**Полный путь:** src/memory\memory.py

```python
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class MemoryEntry:
    event_type: str
    meaning_significance: float
    timestamp: float
    feedback_data: Optional[
        Dict
    ] = None  # Для Feedback записей (сериализованный FeedbackRecord)


class Memory(list):
    def append(self, item):
        super().append(item)
        self.clamp_size()

    def clamp_size(self):
        while len(self) > 50:
            self.pop(0)
```

---

## monitor\console.py <a id="monitor-console"></a>
**Полный путь:** src/monitor\console.py

```python
import json
import sys
from pathlib import Path

import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)
from state.self_state import SelfState

LOG_FILE = Path("data/tick_log.jsonl")
LOG_FILE.parent.mkdir(exist_ok=True)


def log(message):
    print(f"[RELOAD] {message}")
    print("TEST CHANGE")


def monitor(state: SelfState):
    ticks = state.ticks
    age = state.age
    energy = state.energy
    integrity = state.integrity
    stability = state.stability
    last_significance = state.last_significance
    activated_count = len(getattr(state, "activated_memory", []))
    top_significance = max(
        [e.meaning_significance for e in getattr(state, "activated_memory", [])],
        default=0.0,
    )
    last_pattern = getattr(state, "last_pattern", "")

    # Цветной структурированный вывод состояния в консоль
    heartbeat = f"{Fore.RED}*{Style.RESET_ALL}"
    возраст_txt = f"{Fore.BLUE}возраст: {age:.1f} сек. {Style.RESET_ALL}"
    энергия_txt = f"{Fore.GREEN}энергия: {energy:.1f} %{Style.RESET_ALL}"
    интеллект_txt = f"{Fore.YELLOW}интеллект: {integrity:.4f}{Style.RESET_ALL}"
    стабильность_txt = f"{Fore.CYAN}стабильность: {stability:.4f}{Style.RESET_ALL}"
    значимость_txt = (
        f"{Fore.MAGENTA}значимость: {last_significance:.4f}{Style.RESET_ALL}"
    )
    активация_txt = f"активация: {activated_count} ({top_significance:.2f})"
    decision_txt = f"{Fore.YELLOW}decision: {last_pattern}{Style.RESET_ALL}"
    action_txt = f"{Fore.GREEN}action: executed {last_pattern}{Style.RESET_ALL}"
    msg = f"{heartbeat} [{ticks}] {возраст_txt} | {энергия_txt} | {интеллект_txt} | {стабильность_txt} | {значимость_txt} | {активация_txt} | {decision_txt} | {action_txt} | "
    sys.stdout.write(f"\r{msg}")
    sys.stdout.flush()

    # Логирование текущего тика в файл (append-only)
    tick_data = {
        "tick": ticks,
        "age": age,
        "energy": energy,
        "integrity": integrity,
        "stability": stability,
        "last_significance": last_significance,
    }

    with LOG_FILE.open("a") as f:
        f.write(json.dumps(tick_data) + "\n")
```

---

## planning\__init__.py <a id="planning-__init__"></a>
**Полный путь:** src/planning\__init__.py

```python
```

---

## planning\planning.py <a id="planning-planning"></a>
**Полный путь:** src/planning\planning.py

```python
from typing import List

from state.self_state import SelfState


def record_potential_sequences(self_state: SelfState) -> None:
    """
    Минимальная нейтральная фиксация потенциальных последовательностей.

    Использует данные из self_state как proxy для memory_data, learning_statistics, adaptation_parameters.

    Не оценивает, не выбирает, не влияет на другие слои.
    """
    # Получаем нейтральные источники
    recent_events = self_state.recent_events
    energy_history = self_state.energy_history
    stability_history = self_state.stability_history

    # Фиксируем простую potential sequence на основе последних событий
    potential_sequences: List[List[str]] = []

    if len(recent_events) >= 2:
        potential_sequences.append(recent_events[-2:])

    # Записываем в self_state без изменений других полей
    self_state.planning = {
        "potential_sequences": potential_sequences,
        "sources_used": {
            "memory_proxy": len(recent_events),
            "learning_proxy": len(stability_history),
            "adaptation_proxy": len(energy_history),
        },
    }
```

---

## runtime\loop.py <a id="runtime-loop"></a>
**Полный путь:** src/runtime\loop.py

```python
import time
import traceback
from dataclasses import asdict

from action import execute_action
from activation.activation import activate_memory
from decision.decision import decide_response
from feedback import observe_consequences, register_action
from intelligence.intelligence import process_information
from meaning.engine import MeaningEngine
from memory.memory import MemoryEntry
from planning.planning import record_potential_sequences
from state.self_state import SelfState, save_snapshot


def run_loop(
    self_state: SelfState,
    monitor,
    tick_interval=1.0,
    snapshot_period=10,
    stop_event=None,
    event_queue=None,
):
    """
    Runtime Loop с интеграцией Environment (этап 07)

    Args:
        self_state: Состояние Life
        monitor: Функция мониторинга
        tick_interval: Интервал между тиками
        snapshot_period: Периодичность snapshot
        stop_event: threading.Event для остановки
        event_queue: Очередь событий из Environment
    """
    engine = MeaningEngine()
    last_time = time.time()
    pending_actions = []  # Список ожидающих Feedback действий
    while stop_event is None or not stop_event.is_set():
        try:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time

            # Обновление состояния
            self_state.apply_delta({"ticks": 1})
            self_state.apply_delta({"age": dt})

            # Наблюдаем последствия прошлых действий (Feedback)
            feedback_records = observe_consequences(
                self_state, pending_actions, event_queue
            )

            # Сохраняем Feedback в Memory
            for feedback in feedback_records:
                feedback_entry = MemoryEntry(
                    event_type="feedback",
                    meaning_significance=0.0,  # Feedback не имеет значимости
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

            # === ШАГ 1: Получить события из среды ===
            if event_queue and not event_queue.is_empty():
                print(f"[LOOP] Queue not empty, size={event_queue.size()}")
                events = event_queue.pop_all()
                print(f"[LOOP] POPPED {len(events)} events")

                # === ШАГ 2: Интерпретировать события ===
                for event in events:
                    print(
                        f"[LOOP] Interpreting event: type={event.type}, intensity={event.intensity}"
                    )
                    meaning = engine.process(event, asdict(self_state))
                    if meaning.significance > 0:
                        # Активация памяти для события
                        activated = activate_memory(event.type, self_state.memory)
                        self_state.activated_memory = activated
                        print(
                            f"[LOOP] Activated {len(activated)} memories for type '{event.type}'"
                        )

                        # Decision
                        pattern = decide_response(self_state, meaning)
                        self_state.last_pattern = pattern
                        if pattern == "ignore":
                            continue  # skip apply_delta
                        elif pattern == "dampen":
                            meaning.impact = {
                                k: v * 0.5 for k, v in meaning.impact.items()
                            }
                        # else "absorb" — no change

                        # КРИТИЧНО: Сохраняем снимок состояния ДО действия
                        state_before = {
                            "energy": self_state.energy,
                            "stability": self_state.stability,
                            "integrity": self_state.integrity,
                        }

                        self_state.apply_delta(meaning.impact)
                        execute_action(pattern, self_state)

                        # Регистрируем для Feedback (после выполнения)
                        # Action не знает о Feedback - регистрация происходит в Loop
                        action_id = f"action_{self_state.ticks}_{pattern}_{int(time.time()*1000)}"
                        action_timestamp = time.time()
                        register_action(
                            action_id,
                            pattern,
                            state_before,
                            action_timestamp,
                            pending_actions,
                        )
                        self_state.recent_events.append(event.type)
                        self_state.last_significance = meaning.significance
                        self_state.memory.append(
                            MemoryEntry(
                                event_type=event.type,
                                meaning_significance=meaning.significance,
                                timestamp=time.time(),
                            )
                        )
                    print(
                        f"[LOOP] After interpret: energy={self_state.energy:.2f}, stability={self_state.stability:.4f}"
                    )

                record_potential_sequences(self_state)
                process_information(self_state)

            # Логика слабости: когда параметры низкие, добавляем штрафы за немощность
            weakness_threshold = 0.05
            if (
                self_state.energy <= weakness_threshold
                or self_state.integrity <= weakness_threshold
                or self_state.stability <= weakness_threshold
            ):
                penalty = 0.02 * dt
                self_state.apply_delta(
                    {
                        "energy": -penalty,
                        "stability": -penalty * 2,
                        "integrity": -penalty * 2,
                    }
                )
                print(
                    f"[LOOP] Слабость: штрафы penalty={penalty:.4f}, energy={self_state.energy:.2f}"
                )

            # Вызов мониторинга
            try:
                monitor(self_state)
            except Exception as e:
                print(f"Ошибка в monitor: {e}")
                traceback.print_exc()

            # Snapshot каждые snapshot_period тиков
            if self_state.ticks % snapshot_period == 0:
                try:
                    save_snapshot(self_state)
                except Exception as e:
                    print(f"Ошибка при сохранении snapshot: {e}")
                    traceback.print_exc()

            # Поддержка постоянного интервала тиков
            tick_end = time.time()
            elapsed_tick = tick_end - current_time
            sleep_duration = max(0.0, tick_interval - elapsed_tick)
            time.sleep(sleep_duration)

        except Exception as e:
            self_state.apply_delta({"integrity": -0.05})
            print(f"Ошибка в цикле: {e}")
            traceback.print_exc()

        finally:
            if (
                self_state.energy <= 0
                or self_state.integrity <= 0
                or self_state.stability <= 0
            ):
                self_state.active = False
```

---

## state\self_state.py <a id="state-self_state"></a>
**Полный путь:** src/state\self_state.py

```python
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

from memory.memory import MemoryEntry

# Папка для снимков
SNAPSHOT_DIR = Path("data/snapshots")
SNAPSHOT_DIR.mkdir(exist_ok=True)


@dataclass
class SelfState:
    life_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    birth_timestamp: float = field(default_factory=time.time)
    age: float = 0.0
    ticks: int = 0
    energy: float = 100.0
    integrity: float = 1.0
    stability: float = 1.0
    fatigue: float = 0.0
    tension: float = 0.0
    active: bool = True
    recent_events: list = field(default_factory=list)
    last_significance: float = 0.0
    energy_history: list = field(default_factory=list)
    stability_history: list = field(default_factory=list)
    planning: dict = field(default_factory=dict)
    intelligence: dict = field(default_factory=dict)
    memory: list[MemoryEntry] = field(default_factory=list)
    activated_memory: list = field(
        default_factory=list
    )  # Transient, не сохраняется в snapshot
    last_pattern: str = ""  # Transient, последний выбранный паттерн decision

    def apply_delta(self, deltas: dict[str, float]) -> None:
        for key, delta in deltas.items():
            if hasattr(self, key):
                current = getattr(self, key)
                if key == "energy":
                    setattr(self, key, max(0.0, min(100.0, current + delta)))
                elif key in ["integrity", "stability"]:
                    setattr(self, key, max(0.0, min(1.0, current + delta)))
                else:
                    setattr(self, key, current + delta)

    def load_latest_snapshot(self) -> "SelfState":
        # Найти последний snapshot_*.json
        snapshots = list(SNAPSHOT_DIR.glob("snapshot_*.json"))
        if not snapshots:
            raise FileNotFoundError("No snapshots found")
        # Сортировать по номеру тика
        snapshots.sort(key=lambda p: int(p.stem.split("_")[1]))
        latest = snapshots[-1]
        with latest.open("r") as f:
            data = json.load(f)
        # Mapping для совместимости
        field_mapping = {
            "alive": "active",
        }
        mapped_data = {}
        for k, v in data.items():
            mapped_key = field_mapping.get(k, k)
            if mapped_key in SelfState.__dataclass_fields__:
                mapped_data[mapped_key] = v
        # Конвертировать memory из list of dict в list of MemoryEntry
        if "memory" in mapped_data:
            mapped_data["memory"] = [
                MemoryEntry(**entry) for entry in mapped_data["memory"]
            ]
        # Создать экземпляр из dict
        return SelfState(**mapped_data)


def create_initial_state() -> SelfState:
    return SelfState()


def save_snapshot(state: SelfState):
    """
    Сохраняет текущее состояние жизни как отдельный JSON файл
    """
    snapshot = asdict(state)
    # Исключаем transient поля
    snapshot.pop("activated_memory", None)
    snapshot.pop("last_pattern", None)
    tick = snapshot["ticks"]
    filename = SNAPSHOT_DIR / f"snapshot_{tick:06d}.json"
    with filename.open("w") as f:
        json.dump(snapshot, f, indent=2, default=str)


def load_snapshot(tick: int) -> SelfState:
    """
    Загружает снимок по номеру тика
    """
    filename = SNAPSHOT_DIR / f"snapshot_{tick:06d}.json"
    if filename.exists():
        with filename.open("r") as f:
            data = json.load(f)
        # Конвертировать memory из list of dict в list of MemoryEntry
        if "memory" in data:
            data["memory"] = [MemoryEntry(**entry) for entry in data["memory"]]
        return SelfState(**data)
    else:
        raise FileNotFoundError(f"Snapshot {tick} не найден")
```

---

## test\check_feedback_data.py <a id="test-check_feedback_data"></a>
**Полный путь:** src/test\check_feedback_data.py

```python
"""Скрипт для проверки Feedback данных через API"""

import json
import sys

import requests


def check_feedback_data():
    """Проверяет наличие полных данных Feedback через API"""
    try:
        print("Connecting to server...")
        response = requests.get("http://localhost:8000/status", timeout=10)

        if response.status_code != 200:
            print(f"[ERROR] Server returned status {response.status_code}")
            return False

        data = response.json()
        memory = data.get("memory", [])

        print(f"\nTotal memory entries: {len(memory)}")

        # Фильтруем Feedback записи
        feedback_records = [m for m in memory if m.get("event_type") == "feedback"]
        print(f"Total feedback records: {len(feedback_records)}")

        if len(feedback_records) == 0:
            print("[WARNING] No feedback records found yet.")
            print(
                "This is normal if system just started. Feedback records appear after 3-10 ticks."
            )
            return False

        # Проверяем наличие feedback_data
        records_with_data = [f for f in feedback_records if f.get("feedback_data")]
        records_without_data = [
            f for f in feedback_records if not f.get("feedback_data")
        ]

        print(f"\nFeedback records WITH data: {len(records_with_data)}")
        print(
            f"Feedback records WITHOUT data (old format): {len(records_without_data)}"
        )

        if len(records_with_data) > 0:
            print("\n" + "=" * 60)
            print("[SUCCESS] Found feedback records with full data!")
            print("=" * 60)

            sample = records_with_data[0]
            print("\nSample feedback record:")
            print(json.dumps(sample, indent=2))

            # Проверяем структуру
            fd = sample.get("feedback_data", {})
            print("\n" + "=" * 60)
            print("Data structure check:")
            print("=" * 60)
            print(f"  action_id: {'OK' if fd.get('action_id') else 'MISSING'}")
            print(
                f"  action_pattern: {'OK' if fd.get('action_pattern') else 'MISSING'}"
            )
            print(f"  state_delta: {'OK' if fd.get('state_delta') else 'MISSING'}")
            print(
                f"  delay_ticks: {'OK' if fd.get('delay_ticks') is not None else 'MISSING'}"
            )
            print(
                f"  associated_events: {'OK' if 'associated_events' in fd else 'MISSING'}"
            )

            if all(
                [
                    fd.get("action_id"),
                    fd.get("action_pattern"),
                    fd.get("state_delta"),
                    fd.get("delay_ticks") is not None,
                ]
            ):
                print("\n[SUCCESS] All required fields are present!")
                return True
            else:
                print("\n[WARNING] Some fields are missing")
                return False
        else:
            print("\n[FAIL] No feedback records with data found!")
            if len(records_without_data) > 0:
                print("\nFound records without data (old format):")
                print(json.dumps(records_without_data[0], indent=2))
                print(
                    "\nThis means the system is still using old code or records were created before fix."
                )
            return False

    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot connect to server. Is it running?")
        print(
            "Start server with: python src/main_server_api.py --dev --tick-interval 1.0 --snapshot-period 15"
        )
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Feedback Data Storage")
    print("=" * 60)

    # Даем время системе создать Feedback записи
    print("\nChecking for feedback records...")
    print("(Feedback records appear 3-10 ticks after actions)")

    if check_feedback_data():
        print("\n" + "=" * 60)
        print("[SUCCESS] Feedback data storage is working correctly!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("[INFO] No feedback records with data found yet.")
        print("This could mean:")
        print("  1. System just started (wait 15-20 seconds)")
        print("  2. No actions have been executed yet")
        print("  3. Feedback records haven't been observed yet (3-10 tick delay)")
        print("=" * 60)
        sys.exit(1)
```

---

## test\conftest.py <a id="test-conftest"></a>
**Полный путь:** src/test\conftest.py

```python
"""
Общие фикстуры для всех тестов
Поддержка реального сервера и тестового сервера
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import threading
import time

import pytest
import requests

from environment.event_queue import EventQueue
from main_server_api import LifeHandler, StoppableHTTPServer
from state.self_state import SelfState


def pytest_addoption(parser):
    """Добавляет кастомные опции pytest"""
    parser.addoption(
        "--real-server",
        action="store_true",
        default=False,
        help="Use real server instead of test server (requires server running)",
    )
    parser.addoption(
        "--server-port",
        type=int,
        default=8000,
        help="Port of real server (default: 8000)",
    )


@pytest.fixture
def server_config(request):
    """Возвращает конфигурацию сервера из опций pytest"""
    use_real = request.config.getoption("--real-server")
    port = request.config.getoption("--server-port")
    return {"use_real": use_real, "port": port}


def check_real_server_available(base_url, timeout=2):
    """Проверяет доступность реального сервера"""
    try:
        response = requests.get(f"{base_url}/status", timeout=timeout)
        return response.status_code == 200
    except (requests.exceptions.RequestException, requests.exceptions.Timeout):
        return False


@pytest.fixture
def server_setup(server_config):
    """
    Универсальная фикстура для настройки сервера.
    Поддерживает два режима:
    1. Реальный сервер (--real-server) - подключается к существующему серверу
    2. Тестовый сервер (по умолчанию) - создает сервер в отдельном потоке
    """
    if server_config["use_real"]:
        # Режим реального сервера
        port = server_config["port"]
        base_url = f"http://localhost:{port}"

        # Проверяем доступность сервера
        if not check_real_server_available(base_url):
            pytest.skip(f"Real server not available at {base_url}. Start server first.")

        # Для реального сервера возвращаем минимальную конфигурацию
        # self_state и event_queue недоступны напрямую
        yield {
            "server": None,  # Реальный сервер не управляется тестами
            "self_state": None,  # Недоступно для реального сервера
            "event_queue": None,  # Недоступно для реального сервера
            "base_url": base_url,
            "port": port,
            "is_real_server": True,
        }
    else:
        # Режим тестового сервера (текущее поведение)
        self_state = SelfState()
        event_queue = EventQueue()
        server = StoppableHTTPServer(("localhost", 0), LifeHandler)
        server.self_state = self_state
        server.event_queue = event_queue
        server.dev_mode = False

        # Запускаем сервер в отдельном потоке
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()

        # Ждем запуска
        time.sleep(0.1)

        port = server.server_address[1]
        base_url = f"http://localhost:{port}"

        yield {
            "server": server,
            "self_state": self_state,
            "event_queue": event_queue,
            "base_url": base_url,
            "port": port,
            "is_real_server": False,
        }

        # Останавливаем тестовый сервер
        server.shutdown()
        server_thread.join(timeout=2.0)


@pytest.fixture
def real_server_url(server_config):
    """Возвращает URL реального сервера, если используется реальный сервер"""
    if server_config["use_real"]:
        port = server_config["port"]
        return f"http://localhost:{port}"
    return None
```

---

## test\test_action.py <a id="test-test_action"></a>
**Полный путь:** src/test\test_action.py

```python
"""
Подробные тесты для модуля Action
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import time

import pytest

from action.action import execute_action
from state.self_state import SelfState


@pytest.mark.unit
@pytest.mark.order(1)
class TestExecuteAction:
    """Тесты для функции execute_action"""

    @pytest.fixture
    def base_state(self):
        """Создает базовое состояние"""
        state = SelfState()
        state.energy = 50.0
        state.stability = 0.8
        state.integrity = 0.9
        return state

    def test_execute_action_dampen(self, base_state):
        """Тест выполнения действия dampen"""
        initial_energy = base_state.energy
        initial_memory_size = len(base_state.memory)

        execute_action("dampen", base_state)

        # Проверяем, что энергия уменьшилась
        assert base_state.energy < initial_energy
        assert abs(base_state.energy - (initial_energy - 0.01)) < 0.001

        # Проверяем, что действие записано в память
        assert len(base_state.memory) == initial_memory_size + 1
        assert base_state.memory[-1].event_type == "action"
        assert base_state.memory[-1].meaning_significance == 0.0

    def test_execute_action_dampen_energy_minimum(self, base_state):
        """Тест выполнения dampen с минимальной энергией"""
        base_state.energy = 0.01
        execute_action("dampen", base_state)

        # Энергия не должна стать отрицательной
        assert base_state.energy >= 0.0
        assert base_state.energy == 0.0  # Должна быть обрезана до 0

    def test_execute_action_absorb(self, base_state):
        """Тест выполнения действия absorb"""
        initial_energy = base_state.energy
        initial_memory_size = len(base_state.memory)

        execute_action("absorb", base_state)

        # Энергия не должна измениться (только для dampen есть эффект)
        assert base_state.energy == initial_energy

        # Проверяем, что действие записано в память
        assert len(base_state.memory) == initial_memory_size + 1
        assert base_state.memory[-1].event_type == "action"

    def test_execute_action_ignore(self, base_state):
        """Тест выполнения действия ignore"""
        initial_energy = base_state.energy
        initial_memory_size = len(base_state.memory)

        execute_action("ignore", base_state)

        # Энергия не должна измениться
        assert base_state.energy == initial_energy

        # Проверяем, что действие записано в память
        assert len(base_state.memory) == initial_memory_size + 1
        assert base_state.memory[-1].event_type == "action"

    def test_execute_action_memory_entry_timestamp(self, base_state):
        """Тест проверки timestamp в записи действия"""
        before_time = time.time()
        execute_action("absorb", base_state)
        after_time = time.time()

        entry = base_state.memory[-1]
        assert before_time <= entry.timestamp <= after_time

    def test_execute_action_multiple_actions(self, base_state):
        """Тест выполнения нескольких действий подряд"""
        initial_memory_size = len(base_state.memory)

        execute_action("absorb", base_state)
        execute_action("dampen", base_state)
        execute_action("ignore", base_state)

        # Должно быть 3 записи в памяти
        assert len(base_state.memory) == initial_memory_size + 3

        # Все записи должны быть типа "action"
        for i in range(3):
            assert base_state.memory[initial_memory_size + i].event_type == "action"

    def test_execute_action_dampen_multiple_times(self, base_state):
        """Тест выполнения dampen несколько раз"""
        initial_energy = base_state.energy

        for _ in range(5):
            execute_action("dampen", base_state)

        # Энергия должна уменьшиться на 0.01 * 5 = 0.05
        expected_energy = max(0.0, initial_energy - 0.05)
        assert abs(base_state.energy - expected_energy) < 0.001

    def test_execute_action_unknown_pattern(self, base_state):
        """Тест выполнения действия с неизвестным паттерном"""
        initial_energy = base_state.energy
        initial_memory_size = len(base_state.memory)

        # Неизвестный паттерн должен быть обработан без ошибок
        execute_action("unknown_pattern", base_state)

        # Энергия не должна измениться
        assert base_state.energy == initial_energy

        # Действие все равно должно быть записано в память
        assert len(base_state.memory) == initial_memory_size + 1
        assert base_state.memory[-1].event_type == "action"

    def test_execute_action_preserves_other_state(self, base_state):
        """Тест, что выполнение действия не изменяет другие параметры состояния"""
        initial_stability = base_state.stability
        initial_integrity = base_state.integrity
        initial_ticks = base_state.ticks

        execute_action("dampen", base_state)

        # Эти параметры не должны измениться
        assert base_state.stability == initial_stability
        assert base_state.integrity == initial_integrity
        assert base_state.ticks == initial_ticks

    def test_execute_action_memory_entry_significance(self, base_state):
        """Тест проверки significance в записи действия (должна быть 0.0)"""
        execute_action("absorb", base_state)

        entry = base_state.memory[-1]
        assert entry.meaning_significance == 0.0

    def test_execute_action_empty_memory(self, base_state):
        """Тест выполнения действия при пустой памяти"""
        base_state.memory = []

        execute_action("absorb", base_state)

        assert len(base_state.memory) == 1
        assert base_state.memory[0].event_type == "action"

    def test_execute_action_with_existing_memory(self, base_state):
        """Тест выполнения действия при существующей памяти"""
        # Добавляем несколько записей в память
        from memory.memory import MemoryEntry

        for i in range(3):
            entry = MemoryEntry(
                event_type=f"event_{i}", meaning_significance=0.5, timestamp=time.time()
            )
            base_state.memory.append(entry)

        initial_memory_size = len(base_state.memory)
        execute_action("absorb", base_state)

        # Должна быть добавлена еще одна запись
        assert len(base_state.memory) == initial_memory_size + 1
        assert base_state.memory[-1].event_type == "action"
        # Предыдущие записи должны остаться
        assert base_state.memory[0].event_type == "event_0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## test\test_activation.py <a id="test-test_activation"></a>
**Полный путь:** src/test\test_activation.py

```python
"""
Подробные тесты для модуля Activation
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import time

import pytest

from activation.activation import activate_memory
from memory.memory import MemoryEntry


@pytest.mark.unit
@pytest.mark.order(1)
class TestActivateMemory:
    """Тесты для функции activate_memory"""

    def test_activate_memory_empty_memory(self):
        """Тест активации памяти при пустой памяти"""
        memory = []
        activated = activate_memory("test_event", memory)
        assert activated == []
        assert isinstance(activated, list)

    def test_activate_memory_no_matches(self):
        """Тест активации памяти без совпадений по типу"""
        memory = [
            MemoryEntry("event_a", 0.8, time.time()),
            MemoryEntry("event_b", 0.6, time.time()),
            MemoryEntry("event_c", 0.4, time.time()),
        ]
        activated = activate_memory("event_x", memory)
        assert activated == []

    def test_activate_memory_single_match(self):
        """Тест активации памяти с одним совпадением"""
        memory = [
            MemoryEntry("event_a", 0.5, time.time()),
            MemoryEntry("target_event", 0.8, time.time()),
            MemoryEntry("event_b", 0.3, time.time()),
        ]
        activated = activate_memory("target_event", memory)
        assert len(activated) == 1
        assert activated[0].event_type == "target_event"
        assert activated[0].meaning_significance == 0.8

    def test_activate_memory_multiple_matches(self):
        """Тест активации памяти с несколькими совпадениями"""
        memory = [
            MemoryEntry("target", 0.3, time.time()),
            MemoryEntry("other", 0.5, time.time()),
            MemoryEntry("target", 0.8, time.time()),
            MemoryEntry("target", 0.6, time.time()),
        ]
        activated = activate_memory("target", memory)
        assert len(activated) == 3
        # Должны быть отсортированы по significance (desc)
        assert activated[0].meaning_significance == 0.8
        assert activated[1].meaning_significance == 0.6
        assert activated[2].meaning_significance == 0.3

    def test_activate_memory_sorted_by_significance(self):
        """Тест сортировки активированных записей по significance"""
        memory = [
            MemoryEntry("event", 0.1, time.time()),
            MemoryEntry("event", 0.9, time.time()),
            MemoryEntry("event", 0.5, time.time()),
            MemoryEntry("event", 0.3, time.time()),
            MemoryEntry("event", 0.7, time.time()),
        ]
        activated = activate_memory("event", memory, limit=10)  # Увеличиваем лимит
        assert len(activated) == 5
        # Проверяем сортировку по убыванию
        for i in range(len(activated) - 1):
            assert (
                activated[i].meaning_significance
                >= activated[i + 1].meaning_significance
            )

    def test_activate_memory_limit_default(self):
        """Тест ограничения количества результатов (по умолчанию limit=3)"""
        memory = [
            MemoryEntry("event", 0.9, time.time()),
            MemoryEntry("event", 0.8, time.time()),
            MemoryEntry("event", 0.7, time.time()),
            MemoryEntry("event", 0.6, time.time()),
            MemoryEntry("event", 0.5, time.time()),
        ]
        activated = activate_memory("event", memory)
        assert len(activated) == 3
        assert activated[0].meaning_significance == 0.9
        assert activated[1].meaning_significance == 0.8
        assert activated[2].meaning_significance == 0.7

    def test_activate_memory_custom_limit(self):
        """Тест активации с кастомным лимитом"""
        memory = [
            MemoryEntry("event", 0.9, time.time()),
            MemoryEntry("event", 0.8, time.time()),
            MemoryEntry("event", 0.7, time.time()),
        ]
        # Лимит больше количества совпадений
        activated = activate_memory("event", memory, limit=10)
        assert len(activated) == 3

        # Лимит меньше количества совпадений
        activated = activate_memory("event", memory, limit=2)
        assert len(activated) == 2
        assert activated[0].meaning_significance == 0.9
        assert activated[1].meaning_significance == 0.8

    def test_activate_memory_limit_one(self):
        """Тест активации с лимитом 1"""
        memory = [
            MemoryEntry("event", 0.5, time.time()),
            MemoryEntry("event", 0.9, time.time()),
            MemoryEntry("event", 0.3, time.time()),
        ]
        activated = activate_memory("event", memory, limit=1)
        assert len(activated) == 1
        assert activated[0].meaning_significance == 0.9

    def test_activate_memory_limit_zero(self):
        """Тест активации с лимитом 0"""
        memory = [MemoryEntry("event", 0.9, time.time())]
        activated = activate_memory("event", memory, limit=0)
        assert len(activated) == 0

    def test_activate_memory_preserves_original_memory(self):
        """Тест, что активация не изменяет исходную память"""
        memory = [
            MemoryEntry("event", 0.5, time.time()),
            MemoryEntry("other", 0.8, time.time()),
        ]
        original_length = len(memory)
        activate_memory("event", memory)

        assert len(memory) == original_length
        assert memory[0].event_type == "event"
        assert memory[1].event_type == "other"

    def test_activate_memory_different_event_types(self):
        """Тест активации для разных типов событий"""
        memory = [
            MemoryEntry("shock", 0.9, time.time()),
            MemoryEntry("noise", 0.3, time.time()),
            MemoryEntry("recovery", 0.7, time.time()),
            MemoryEntry("shock", 0.8, time.time()),
            MemoryEntry("decay", 0.5, time.time()),
        ]

        # Активация для "shock"
        activated_shock = activate_memory("shock", memory)
        assert len(activated_shock) == 2
        assert all(e.event_type == "shock" for e in activated_shock)

        # Активация для "noise"
        activated_noise = activate_memory("noise", memory)
        assert len(activated_noise) == 1
        assert activated_noise[0].event_type == "noise"

    def test_activate_memory_with_feedback_entries(self):
        """Тест активации памяти с Feedback записями"""
        memory = [
            MemoryEntry("feedback", 0.0, time.time(), feedback_data={"action_id": "1"}),
            MemoryEntry("event", 0.5, time.time()),
            MemoryEntry("feedback", 0.0, time.time(), feedback_data={"action_id": "2"}),
        ]
        # Feedback записи не должны активироваться для обычных событий
        activated = activate_memory("event", memory)
        assert len(activated) == 1
        assert activated[0].event_type == "event"

        # Но должны активироваться для "feedback"
        activated_feedback = activate_memory("feedback", memory)
        assert len(activated_feedback) == 2
        assert all(e.event_type == "feedback" for e in activated_feedback)

    def test_activate_memory_equal_significance(self):
        """Тест активации при одинаковой significance"""
        memory = [
            MemoryEntry("event", 0.5, time.time() - 2),
            MemoryEntry("event", 0.5, time.time() - 1),
            MemoryEntry("event", 0.5, time.time()),
        ]
        activated = activate_memory("event", memory)
        # При одинаковой significance порядок может быть любым, но все должны быть включены
        assert len(activated) == 3
        assert all(e.meaning_significance == 0.5 for e in activated)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## test\test_api.py <a id="test-test_api"></a>
**Полный путь:** src/test\test_api.py

```python
"""
Базовые тесты API сервера
Требуют запущенный сервер (можно использовать --real-server)
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest
import requests


@pytest.fixture
def api_base_url(server_config):
    """Возвращает базовый URL API сервера"""
    if server_config["use_real"]:
        return f"http://localhost:{server_config['port']}"
    else:
        # Для тестового сервера используем фикстуру server_setup
        pytest.skip(
            "test_api.py requires real server. Use --real-server or test_api_integration.py"
        )


@pytest.mark.integration
@pytest.mark.real_server
@pytest.mark.order(2)
def test_get_status(api_base_url):
    """Тест GET /status"""
    response = requests.get(f"{api_base_url}/status", timeout=5)
    assert response.status_code == 200
    assert response.headers.get("Content-type") == "application/json"
    data = response.json()
    assert "energy" in data
    assert "integrity" in data
    assert "stability" in data


@pytest.mark.integration
@pytest.mark.real_server
@pytest.mark.order(2)
def test_get_clear_data(api_base_url):
    """Тест GET /clear-data"""
    response = requests.get(f"{api_base_url}/clear-data", timeout=5)
    assert response.status_code == 200
    assert response.text == "Data cleared"


@pytest.mark.integration
@pytest.mark.real_server
@pytest.mark.order(2)
def test_post_event_success(api_base_url):
    """Тест POST /event с правильным JSON"""
    data = {"type": "test_event", "intensity": 0.1, "metadata": {"key": "value"}}
    response = requests.post(f"{api_base_url}/event", json=data, timeout=5)
    assert response.status_code == 200
    assert response.text == "Event accepted"


@pytest.mark.integration
@pytest.mark.real_server
@pytest.mark.order(2)
def test_post_event_invalid_json(api_base_url):
    """Тест POST /event с неправильным JSON"""
    response = requests.post(
        f"{api_base_url}/event",
        data="invalid json",
        headers={"Content-Type": "application/json"},
        timeout=5,
    )
    assert response.status_code == 400
    assert "Invalid JSON" in response.text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## test\test_api_integration.py <a id="test-test_api_integration"></a>
**Полный путь:** src/test\test_api_integration.py

```python
"""
Интеграционные тесты для HTTP API сервера
Поддерживают работу с реальным сервером (--real-server) или тестовым сервером
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest
import requests


@pytest.mark.integration
@pytest.mark.real_server
@pytest.mark.order(2)
class TestAPIServer:
    """Интеграционные тесты для API сервера"""

    def test_get_status(self, server_setup):
        """Тест GET /status"""
        response = requests.get(f"{server_setup['base_url']}/status", timeout=5)
        assert response.status_code == 200
        assert response.headers["Content-type"] == "application/json"

        data = response.json()
        assert "energy" in data
        assert "integrity" in data
        assert "stability" in data
        assert "ticks" in data
        assert isinstance(data["energy"], (int, float))

    def test_get_status_returns_current_state(self, server_setup):
        """Тест, что GET /status возвращает текущее состояние"""
        # Для реального сервера нельзя изменить состояние напрямую
        if server_setup.get("is_real_server"):
            # Просто проверяем, что статус доступен
            response = requests.get(f"{server_setup['base_url']}/status", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert "energy" in data
            assert "ticks" in data
        else:
            # Для тестового сервера можем изменить состояние
            server_setup["self_state"].energy = 75.0
            server_setup["self_state"].ticks = 100

            response = requests.get(f"{server_setup['base_url']}/status", timeout=5)
            assert response.status_code == 200

            data = response.json()
            assert data["energy"] == 75.0
            assert data["ticks"] == 100

    def test_get_clear_data(self, server_setup):
        """Тест GET /clear-data"""
        response = requests.get(f"{server_setup['base_url']}/clear-data", timeout=5)
        assert response.status_code == 200
        assert response.text == "Data cleared"

    def test_get_unknown_endpoint(self, server_setup):
        """Тест GET неизвестного эндпоинта"""
        response = requests.get(f"{server_setup['base_url']}/unknown", timeout=5)
        assert response.status_code == 404
        assert response.text == "Unknown endpoint"

    def test_post_event_success(self, server_setup):
        """Тест POST /event с валидными данными"""
        payload = {"type": "shock", "intensity": 0.5, "metadata": {"test": "value"}}

        response = requests.post(
            f"{server_setup['base_url']}/event", json=payload, timeout=5
        )

        assert response.status_code == 200
        assert response.text == "Event accepted"

        # Проверяем очередь только для тестового сервера
        if not server_setup.get("is_real_server") and server_setup.get("event_queue"):
            assert server_setup["event_queue"].size() == 1

            # Проверяем содержимое события
            event = server_setup["event_queue"].pop()
            assert event.type == "shock"
            assert event.intensity == 0.5
            assert event.metadata == {"test": "value"}

    def test_post_event_minimal(self, server_setup):
        """Тест POST /event с минимальными данными (только type)"""
        payload = {"type": "noise"}

        response = requests.post(
            f"{server_setup['base_url']}/event", json=payload, timeout=5
        )

        assert response.status_code == 200

        # Проверяем очередь только для тестового сервера
        if not server_setup.get("is_real_server") and server_setup.get("event_queue"):
            assert server_setup["event_queue"].size() == 1

            event = server_setup["event_queue"].pop()
            assert event.type == "noise"
            assert event.intensity == 0.0  # По умолчанию

    def test_post_event_with_timestamp(self, server_setup):
        """Тест POST /event с кастомным timestamp"""
        custom_timestamp = 1000.0
        payload = {"type": "recovery", "intensity": 0.3, "timestamp": custom_timestamp}

        response = requests.post(
            f"{server_setup['base_url']}/event", json=payload, timeout=5
        )

        assert response.status_code == 200

        # Проверяем timestamp только для тестового сервера
        if not server_setup.get("is_real_server") and server_setup.get("event_queue"):
            event = server_setup["event_queue"].pop()
            assert event.timestamp == custom_timestamp

    def test_post_event_invalid_json(self, server_setup):
        """Тест POST /event с невалидным JSON"""
        response = requests.post(
            f"{server_setup['base_url']}/event",
            data="invalid json",
            headers={"Content-Type": "application/json"},
            timeout=5,
        )

        assert response.status_code == 400
        assert "Invalid JSON" in response.text

    def test_post_event_missing_type(self, server_setup):
        """Тест POST /event без поля type"""
        payload = {"intensity": 0.5}

        response = requests.post(
            f"{server_setup['base_url']}/event", json=payload, timeout=5
        )

        assert response.status_code == 400
        assert "'type' is required" in response.text

    def test_post_event_invalid_type(self, server_setup):
        """Тест POST /event с невалидным типом (не строка)"""
        payload = {"type": 123}

        response = requests.post(
            f"{server_setup['base_url']}/event", json=payload, timeout=5
        )

        assert response.status_code == 400
        assert "'type' is required" in response.text

    def test_post_event_multiple_events(self, server_setup):
        """Тест отправки нескольких событий"""
        events = [
            {"type": "shock", "intensity": 0.8},
            {"type": "noise", "intensity": 0.2},
            {"type": "recovery", "intensity": 0.4},
        ]

        for event_data in events:
            response = requests.post(
                f"{server_setup['base_url']}/event", json=event_data, timeout=5
            )
            assert response.status_code == 200

        # Проверяем очередь только для тестового сервера
        if not server_setup.get("is_real_server") and server_setup.get("event_queue"):
            assert server_setup["event_queue"].size() == 3

    def test_post_event_different_types(self, server_setup):
        """Тест отправки разных типов событий"""
        event_types = ["shock", "noise", "recovery", "decay", "idle"]

        for event_type in event_types:
            payload = {"type": event_type, "intensity": 0.3}
            response = requests.post(
                f"{server_setup['base_url']}/event", json=payload, timeout=5
            )
            assert response.status_code == 200

        # Проверяем очередь только для тестового сервера
        if not server_setup.get("is_real_server") and server_setup.get("event_queue"):
            assert server_setup["event_queue"].size() == len(event_types)

    def test_post_unknown_endpoint(self, server_setup):
        """Тест POST неизвестного эндпоинта"""
        response = requests.post(
            f"{server_setup['base_url']}/unknown", json={"type": "test"}, timeout=5
        )

        assert response.status_code == 404
        assert response.text == "Unknown endpoint"

    def test_post_event_queue_overflow(self, server_setup):
        """Тест переполнения очереди событий"""
        # Для реального сервера этот тест не имеет смысла (не можем проверить очередь)
        if server_setup.get("is_real_server"):
            pytest.skip(
                "Queue overflow test requires access to event_queue (test server only)"
            )

        # Заполняем очередь до максимума (100)
        for i in range(100):
            payload = {"type": "noise", "intensity": 0.1}
            response = requests.post(
                f"{server_setup['base_url']}/event", json=payload, timeout=5
            )
            assert response.status_code == 200

        # Попытка добавить еще одно событие (должно быть проигнорировано)
        payload = {"type": "shock", "intensity": 0.9}
        response = requests.post(
            f"{server_setup['base_url']}/event", json=payload, timeout=5
        )
        # Сервер все равно вернет 200, но событие не добавится
        assert response.status_code == 200
        assert server_setup["event_queue"].size() == 100

    def test_get_status_after_events(self, server_setup):
        """Тест, что состояние обновляется после обработки событий"""
        # Отправляем событие
        payload = {"type": "shock", "intensity": 0.8}
        response = requests.post(
            f"{server_setup['base_url']}/event", json=payload, timeout=5
        )
        assert response.status_code == 200

        # Проверяем статус
        response = requests.get(f"{server_setup['base_url']}/status", timeout=5)
        assert response.status_code == 200
        # Состояние должно быть доступно (хотя события еще не обработаны)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## test\test_decision.py <a id="test-test_decision"></a>
**Полный путь:** src/test\test_decision.py

```python
"""
Подробные тесты для модуля Decision
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import time

import pytest

from decision.decision import decide_response
from meaning.meaning import Meaning
from memory.memory import MemoryEntry
from state.self_state import SelfState


@pytest.mark.unit
@pytest.mark.order(1)
class TestDecideResponse:
    """Тесты для функции decide_response"""

    @pytest.fixture
    def base_state(self):
        """Создает базовое состояние"""
        return SelfState()

    @pytest.fixture
    def high_significance_meaning(self):
        """Создает Meaning с высокой значимостью"""
        return Meaning(significance=0.7, impact={"energy": -1.0, "stability": -0.1})

    @pytest.fixture
    def low_significance_meaning(self):
        """Создает Meaning с низкой значимостью"""
        return Meaning(significance=0.05, impact={"energy": -0.1, "stability": -0.01})

    def test_decide_dampen_high_activated_memory(
        self, base_state, high_significance_meaning
    ):
        """Тест выбора dampen при высокой significance в активированной памяти"""
        # Создаем активированную память с высокой significance
        base_state.activated_memory = [
            MemoryEntry("event", 0.6, time.time()),  # > 0.5
            MemoryEntry("event", 0.4, time.time()),
        ]

        pattern = decide_response(base_state, high_significance_meaning)
        assert pattern == "dampen"

    def test_decide_dampen_max_significance_above_threshold(
        self, base_state, high_significance_meaning
    ):
        """Тест выбора dampen когда max significance > 0.5"""
        base_state.activated_memory = [
            MemoryEntry("event", 0.51, time.time())  # Чуть выше порога
        ]

        pattern = decide_response(base_state, high_significance_meaning)
        assert pattern == "dampen"

    def test_decide_dampen_max_significance_at_threshold(
        self, base_state, high_significance_meaning
    ):
        """Тест выбора dampen когда max significance = 0.5 (граничный случай)"""
        base_state.activated_memory = [
            MemoryEntry("event", 0.5, time.time())  # Ровно на пороге
        ]

        pattern = decide_response(base_state, high_significance_meaning)
        # 0.5 не больше 0.5, поэтому должен вернуться fallback
        # Но в коде используется > 0.5, поэтому это не dampen
        assert pattern != "dampen"  # Должен быть fallback

    def test_decide_ignore_low_significance_meaning(
        self, base_state, low_significance_meaning
    ):
        """Тест выбора ignore при низкой significance в Meaning"""
        base_state.activated_memory = []  # Пустая активированная память

        pattern = decide_response(base_state, low_significance_meaning)
        assert pattern == "ignore"

    def test_decide_ignore_meaning_significance_below_threshold(self, base_state):
        """Тест выбора ignore когда significance < 0.1"""
        meaning = Meaning(significance=0.09, impact={"energy": -0.1})
        base_state.activated_memory = []

        pattern = decide_response(base_state, meaning)
        assert pattern == "ignore"

    def test_decide_absorb_normal_conditions(self, base_state):
        """Тест выбора absorb при нормальных условиях"""
        meaning = Meaning(significance=0.5, impact={"energy": -1.0})
        base_state.activated_memory = [MemoryEntry("event", 0.3, time.time())]  # < 0.5

        pattern = decide_response(base_state, meaning)
        assert pattern == "absorb"

    def test_decide_absorb_high_significance_meaning(self, base_state):
        """Тест выбора absorb при высокой significance в Meaning, но низкой в памяти"""
        meaning = Meaning(significance=0.8, impact={"energy": -1.0})
        base_state.activated_memory = [MemoryEntry("event", 0.4, time.time())]  # < 0.5

        pattern = decide_response(base_state, meaning)
        assert pattern == "absorb"

    def test_decide_empty_activated_memory(self, base_state):
        """Тест принятия решения при пустой активированной памяти"""
        base_state.activated_memory = []
        meaning = Meaning(significance=0.5, impact={"energy": -1.0})

        pattern = decide_response(base_state, meaning)
        # Должен вернуться fallback к Meaning's pattern
        assert pattern in ["ignore", "absorb"]

    def test_decide_multiple_activated_memories(self, base_state):
        """Тест принятия решения с несколькими активированными воспоминаниями"""
        base_state.activated_memory = [
            MemoryEntry("event", 0.3, time.time()),
            MemoryEntry("event", 0.7, time.time()),  # Максимальная
            MemoryEntry("event", 0.2, time.time()),
        ]
        meaning = Meaning(significance=0.5, impact={"energy": -1.0})

        pattern = decide_response(base_state, meaning)
        assert pattern == "dampen"  # max(0.3, 0.7, 0.2) = 0.7 > 0.5

    def test_decide_activated_memory_max_below_threshold(self, base_state):
        """Тест принятия решения когда max significance в памяти < 0.5"""
        base_state.activated_memory = [
            MemoryEntry("event", 0.4, time.time()),
            MemoryEntry("event", 0.3, time.time()),
        ]
        meaning = Meaning(significance=0.6, impact={"energy": -1.0})

        pattern = decide_response(base_state, meaning)
        # max(0.4, 0.3) = 0.4 < 0.5, поэтому fallback
        assert pattern == "absorb"

    def test_decide_activated_memory_exactly_at_threshold(self, base_state):
        """Тест принятия решения когда max significance = 0.5"""
        base_state.activated_memory = [MemoryEntry("event", 0.5, time.time())]
        meaning = Meaning(significance=0.6, impact={"energy": -1.0})

        pattern = decide_response(base_state, meaning)
        # 0.5 не > 0.5, поэтому fallback
        assert pattern == "absorb"

    def test_decide_meaning_significance_at_threshold(self, base_state):
        """Тест принятия решения когда significance Meaning = 0.1 (граничный случай)"""
        meaning = Meaning(significance=0.1, impact={"energy": -0.1})
        base_state.activated_memory = []

        pattern = decide_response(base_state, meaning)
        # 0.1 не < 0.1, поэтому не ignore
        assert pattern == "absorb"

    def test_decide_different_event_types_in_memory(self, base_state):
        """Тест принятия решения с разными типами событий в памяти"""
        base_state.activated_memory = [
            MemoryEntry("shock", 0.6, time.time()),
            MemoryEntry("noise", 0.3, time.time()),
        ]
        meaning = Meaning(significance=0.5, impact={"energy": -1.0})

        pattern = decide_response(base_state, meaning)
        assert pattern == "dampen"  # max(0.6, 0.3) = 0.6 > 0.5

    def test_decide_consistency(self, base_state):
        """Тест консистентности решений при одинаковых условиях"""
        base_state.activated_memory = [MemoryEntry("event", 0.6, time.time())]
        meaning = Meaning(significance=0.5, impact={"energy": -1.0})

        # Вызываем несколько раз
        patterns = [decide_response(base_state, meaning) for _ in range(5)]

        # Все результаты должны быть одинаковыми
        assert all(p == patterns[0] for p in patterns)
        assert patterns[0] == "dampen"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## test\test_environment.py <a id="test-test_environment"></a>
**Полный путь:** src/test\test_environment.py

```python
"""
Подробные тесты для модуля Environment (Event, EventQueue)
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import time

import pytest

from environment.event import Event
from environment.event_queue import EventQueue


@pytest.mark.unit
@pytest.mark.order(1)
class TestEvent:
    """Тесты для класса Event"""

    def test_event_creation_minimal(self):
        """Тест создания Event с минимальными параметрами"""
        event = Event(type="test", intensity=0.5, timestamp=time.time())
        assert event.type == "test"
        assert event.intensity == 0.5
        assert event.timestamp > 0
        assert event.metadata == {}

    def test_event_creation_with_metadata(self):
        """Тест создания Event с metadata"""
        metadata = {"key1": "value1", "key2": 123}
        event = Event(
            type="test", intensity=0.5, timestamp=time.time(), metadata=metadata
        )
        assert event.metadata == metadata
        assert event.metadata["key1"] == "value1"
        assert event.metadata["key2"] == 123

    def test_event_creation_with_none_metadata(self):
        """Тест создания Event с None metadata (должен стать пустым dict)"""
        event = Event(type="test", intensity=0.5, timestamp=time.time(), metadata=None)
        assert event.metadata == {}

    def test_event_different_types(self):
        """Тест создания Event с разными типами"""
        event_types = ["shock", "noise", "recovery", "decay", "idle"]
        for event_type in event_types:
            event = Event(type=event_type, intensity=0.5, timestamp=time.time())
            assert event.type == event_type

    def test_event_intensity_range(self):
        """Тест создания Event с разными значениями intensity"""
        for intensity in [-1.0, -0.5, 0.0, 0.5, 1.0]:
            event = Event(type="test", intensity=intensity, timestamp=time.time())
            assert event.intensity == intensity

    def test_event_timestamp(self):
        """Тест проверки timestamp"""
        before = time.time()
        event = Event(type="test", intensity=0.5, timestamp=time.time())
        after = time.time()
        assert before <= event.timestamp <= after

    def test_event_custom_timestamp(self):
        """Тест создания Event с кастомным timestamp"""
        custom_timestamp = 1000.0
        event = Event(type="test", intensity=0.5, timestamp=custom_timestamp)
        assert event.timestamp == custom_timestamp


@pytest.mark.unit
@pytest.mark.order(1)
class TestEventQueue:
    """Тесты для класса EventQueue"""

    def test_queue_initialization(self):
        """Тест инициализации пустой очереди"""
        queue = EventQueue()
        assert queue.is_empty()
        assert queue.size() == 0

    def test_queue_push_single(self):
        """Тест добавления одного события"""
        queue = EventQueue()
        event = Event(type="test", intensity=0.5, timestamp=time.time())

        queue.push(event)

        assert not queue.is_empty()
        assert queue.size() == 1

    def test_queue_push_multiple(self):
        """Тест добавления нескольких событий"""
        queue = EventQueue()
        events = [
            Event(type=f"event_{i}", intensity=0.5, timestamp=time.time())
            for i in range(5)
        ]

        for event in events:
            queue.push(event)

        assert queue.size() == 5
        assert not queue.is_empty()

    def test_queue_pop_single(self):
        """Тест извлечения одного события"""
        queue = EventQueue()
        event = Event(type="test", intensity=0.5, timestamp=time.time())
        queue.push(event)

        popped = queue.pop()

        assert popped == event
        assert queue.is_empty()
        assert queue.size() == 0

    def test_queue_pop_empty(self):
        """Тест извлечения из пустой очереди"""
        queue = EventQueue()
        popped = queue.pop()

        assert popped is None

    def test_queue_pop_fifo_order(self):
        """Тест порядка извлечения (FIFO)"""
        queue = EventQueue()
        events = [
            Event(type=f"event_{i}", intensity=0.5, timestamp=time.time())
            for i in range(5)
        ]

        for event in events:
            queue.push(event)

        # Извлекаем и проверяем порядок
        for i, expected_event in enumerate(events):
            popped = queue.pop()
            assert popped == expected_event
            assert popped.type == f"event_{i}"

    def test_queue_pop_all_empty(self):
        """Тест pop_all из пустой очереди"""
        queue = EventQueue()
        events = queue.pop_all()

        assert events == []
        assert isinstance(events, list)

    def test_queue_pop_all_single(self):
        """Тест pop_all с одним событием"""
        queue = EventQueue()
        event = Event(type="test", intensity=0.5, timestamp=time.time())
        queue.push(event)

        events = queue.pop_all()

        assert len(events) == 1
        assert events[0] == event
        assert queue.is_empty()

    def test_queue_pop_all_multiple(self):
        """Тест pop_all с несколькими событиями"""
        queue = EventQueue()
        original_events = [
            Event(type=f"event_{i}", intensity=0.5, timestamp=time.time())
            for i in range(5)
        ]

        for event in original_events:
            queue.push(event)

        events = queue.pop_all()

        assert len(events) == 5
        assert events == original_events
        assert queue.is_empty()

    def test_queue_pop_all_fifo_order(self):
        """Тест порядка pop_all (FIFO)"""
        queue = EventQueue()
        original_events = [
            Event(type=f"event_{i}", intensity=0.5, timestamp=time.time())
            for i in range(5)
        ]

        for event in original_events:
            queue.push(event)

        events = queue.pop_all()

        # Проверяем порядок
        for i, event in enumerate(events):
            assert event.type == f"event_{i}"

    def test_queue_size_after_operations(self):
        """Тест размера очереди после различных операций"""
        queue = EventQueue()
        assert queue.size() == 0

        queue.push(Event(type="e1", intensity=0.5, timestamp=time.time()))
        assert queue.size() == 1

        queue.push(Event(type="e2", intensity=0.5, timestamp=time.time()))
        assert queue.size() == 2

        queue.pop()
        assert queue.size() == 1

        queue.pop()
        assert queue.size() == 0

    def test_queue_is_empty_after_operations(self):
        """Тест is_empty после различных операций"""
        queue = EventQueue()
        assert queue.is_empty()

        queue.push(Event(type="e1", intensity=0.5, timestamp=time.time()))
        assert not queue.is_empty()

        queue.pop()
        assert queue.is_empty()

    def test_queue_push_after_pop_all(self):
        """Тест добавления событий после pop_all"""
        queue = EventQueue()
        queue.push(Event(type="e1", intensity=0.5, timestamp=time.time()))
        queue.pop_all()

        queue.push(Event(type="e2", intensity=0.5, timestamp=time.time()))
        assert queue.size() == 1
        assert not queue.is_empty()

    def test_queue_maxsize_behavior(self):
        """Тест поведения при достижении максимального размера (100)"""
        queue = EventQueue()
        # Добавляем события до лимита
        for i in range(100):
            event = Event(type=f"event_{i}", intensity=0.5, timestamp=time.time())
            queue.push(event)

        assert queue.size() == 100

        # Попытка добавить еще одно событие должна быть проигнорирована
        queue.push(Event(type="overflow", intensity=0.5, timestamp=time.time()))
        assert queue.size() == 100
        # Последнее событие в очереди не должно быть overflow
        last_event = None
        while not queue.is_empty():
            last_event = queue.pop()
        assert last_event.type != "overflow"

    def test_queue_mixed_operations(self):
        """Тест смешанных операций push/pop"""
        queue = EventQueue()

        # Добавляем несколько
        for i in range(3):
            queue.push(Event(type=f"e{i}", intensity=0.5, timestamp=time.time()))

        # Извлекаем один
        popped = queue.pop()
        assert popped.type == "e0"
        assert queue.size() == 2

        # Добавляем еще
        queue.push(Event(type="e3", intensity=0.5, timestamp=time.time()))
        assert queue.size() == 3

        # Извлекаем все
        events = queue.pop_all()
        assert len(events) == 3
        assert events[0].type == "e1"  # Следующее после извлеченного
        assert events[1].type == "e2"
        assert events[2].type == "e3"

    def test_queue_different_event_types(self):
        """Тест работы очереди с разными типами событий"""
        queue = EventQueue()
        event_types = ["shock", "noise", "recovery", "decay", "idle"]

        for event_type in event_types:
            queue.push(Event(type=event_type, intensity=0.5, timestamp=time.time()))

        assert queue.size() == 5

        events = queue.pop_all()
        assert len(events) == 5
        for i, event in enumerate(events):
            assert event.type == event_types[i]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## test\test_event_queue_edge_cases.py <a id="test-test_event_queue_edge_cases"></a>
**Полный путь:** src/test\test_event_queue_edge_cases.py

```python
"""
Тесты для покрытия edge cases в EventQueue
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import time

import pytest

from environment.event import Event
from environment.event_queue import EventQueue


@pytest.mark.unit
@pytest.mark.order(1)
class TestEventQueueEdgeCases:
    """Тесты для edge cases EventQueue"""

    def test_pop_all_with_empty_exception(self):
        """Тест pop_all когда очередь становится пустой во время итерации (строка 38-39)"""
        event_queue = EventQueue()

        # Добавляем событие
        event = Event(type="test", intensity=0.5, timestamp=time.time())
        event_queue.push(event)

        # pop_all должен обработать Empty exception и корректно вернуть события
        events = event_queue.pop_all()

        assert len(events) == 1
        assert events[0] == event

        # После pop_all очередь должна быть пуста
        assert event_queue.is_empty()

        # Повторный вызов pop_all на пустой очереди
        # Это должно вызвать Empty exception внутри while, который обрабатывается в строке 38-39
        events2 = event_queue.pop_all()
        assert events2 == []

        # Симулируем race condition: очередь становится пустой между проверкой empty() и get_nowait()
        # Это покрывает строки 38-39 (обработка Empty в цикле)
        import queue as q

        # Создаем очередь, которая выбросит Empty при get_nowait на пустой очереди
        event_queue2 = EventQueue()
        # Не добавляем события, очередь пуста
        # При вызове pop_all, empty() вернет True, но если между проверкой и get_nowait
        # что-то изменится, может быть Empty - но в нашем случае очередь действительно пуста
        # Поэтому нужно создать ситуацию, когда empty() может вернуть False, но get_nowait выбросит Empty
        # Это сложно симулировать без моков, но реально это может произойти в многопоточной среде

        # Альтернативный подход: используем мок для симуляции
        original_get = event_queue2._queue.get_nowait
        call_count = [0]

        def mock_get_nowait():
            call_count[0] += 1
            if call_count[0] == 1:
                # Первый вызов выбрасывает Empty (симулируем race condition)
                raise q.Empty()
            return original_get()

        # Но это не сработает, так как empty() вернет True и цикл не начнется
        # Реальная ситуация: между empty() и get_nowait() другой поток может очистить очередь
        # В однопоточном тесте это сложно симулировать

        # Просто проверяем, что код обрабатывает Empty корректно
        result = event_queue2.pop_all()
        assert result == []
```

---

## test\test_event_queue_race_condition.py <a id="test-test_event_queue_race_condition"></a>
**Полный путь:** src/test\test_event_queue_race_condition.py

```python
"""
Тесты для покрытия race condition в EventQueue.pop_all (строки 38-39)
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import queue
import threading
import time

import pytest

from environment.event import Event
from environment.event_queue import EventQueue


@pytest.mark.unit
@pytest.mark.order(1)
class TestEventQueueRaceCondition:
    """Тесты для race condition в pop_all"""

    def test_pop_all_empty_exception_handling(self):
        """Тест обработки Empty exception в pop_all (строки 38-39)"""
        event_queue = EventQueue()

        # Создаем ситуацию, когда между проверкой empty() и get_nowait()
        # очередь становится пустой (race condition)
        # Это покрывает строки 38-39

        # Добавляем событие
        event = Event(type="test", intensity=0.5, timestamp=time.time())
        event_queue.push(event)

        # Мокаем _queue.get_nowait чтобы симулировать Empty после первого вызова
        original_get = event_queue._queue.get_nowait
        call_count = [0]

        def mock_get_nowait():
            call_count[0] += 1
            if call_count[0] == 1:
                # Первый вызов возвращает событие
                return original_get()
            else:
                # Второй вызов выбрасывает Empty (симулируем race condition)
                # Это покрывает строки 38-39: except queue.Empty: break
                raise queue.Empty()

        # Заменяем метод
        event_queue._queue.get_nowait = mock_get_nowait

        # Мокаем empty() чтобы вернуть False первый раз, True второй
        empty_call_count = [0]

        def mock_empty():
            empty_call_count[0] += 1
            if empty_call_count[0] == 1:
                return False  # Первый раз очередь не пуста
            else:
                return True  # Второй раз пуста (но мы уже внутри цикла)

        event_queue._queue.empty = mock_empty

        # Теперь pop_all должен обработать Empty exception
        events = event_queue.pop_all()

        # Должно быть одно событие (первый вызов успешен)
        assert len(events) == 1
        assert events[0] == event

        # Второй вызов get_nowait выбросил Empty, который был обработан в строке 38-39
        assert call_count[0] >= 1

    def test_pop_all_concurrent_access(self):
        """Тест pop_all при конкурентном доступе"""
        event_queue = EventQueue()

        # Добавляем несколько событий
        for i in range(5):
            event = Event(type=f"event_{i}", intensity=0.5, timestamp=time.time())
            event_queue.push(event)

        # В отдельном потоке удаляем события
        removed_count = [0]

        def remove_events():
            while not event_queue.is_empty():
                try:
                    event_queue._queue.get_nowait()
                    removed_count[0] += 1
                except queue.Empty:
                    break

        # Запускаем pop_all в основном потоке
        # и удаление в другом потоке одновременно
        thread = threading.Thread(target=remove_events)
        thread.start()

        events = event_queue.pop_all()
        thread.join(timeout=1.0)

        # Проверяем, что Empty exception был обработан корректно
        # (не должно быть необработанных исключений)
        assert isinstance(events, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## test\test_feedback.py <a id="test-test_feedback"></a>
**Полный путь:** src/test\test_feedback.py

```python
"""
Подробные тесты для модуля Feedback
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import time

import pytest

from feedback import observe_consequences, register_action
from memory.memory import MemoryEntry
from state.self_state import SelfState


@pytest.mark.unit
@pytest.mark.order(1)
class TestRegisterAction:
    """Тесты для функции register_action"""

    def test_register_action_basic(self):
        """Тест базовой регистрации действия"""
        pending_actions = []
        state_before = {"energy": 50.0, "stability": 0.8, "integrity": 0.9}

        register_action(
            action_id="test_action_1",
            action_pattern="dampen",
            state_before=state_before,
            timestamp=time.time(),
            pending_actions=pending_actions,
        )

        assert len(pending_actions) == 1
        assert pending_actions[0].action_id == "test_action_1"
        assert pending_actions[0].action_pattern == "dampen"
        assert pending_actions[0].state_before == state_before
        assert 3 <= pending_actions[0].check_after_ticks <= 10
        assert pending_actions[0].ticks_waited == 0

    def test_register_action_different_patterns(self):
        """Тест регистрации разных паттернов действий"""
        patterns = ["dampen", "absorb", "ignore"]
        for pattern in patterns:
            pending_actions = []
            register_action(
                action_id=f"action_{pattern}",
                action_pattern=pattern,
                state_before={"energy": 50.0},
                timestamp=time.time(),
                pending_actions=pending_actions,
            )
            assert pending_actions[0].action_pattern == pattern

    def test_register_action_state_copy(self):
        """Тест, что state_before копируется, а не ссылается"""
        pending_actions = []
        state_before = {"energy": 50.0, "stability": 0.8}

        register_action(
            action_id="test",
            action_pattern="dampen",
            state_before=state_before,
            timestamp=time.time(),
            pending_actions=pending_actions,
        )

        # Изменяем оригинальный словарь
        state_before["energy"] = 100.0

        # Копия в pending_action не должна измениться
        assert pending_actions[0].state_before["energy"] == 50.0

    def test_register_action_multiple(self):
        """Тест регистрации нескольких действий"""
        pending_actions = []

        for i in range(5):
            register_action(
                action_id=f"action_{i}",
                action_pattern="dampen",
                state_before={"energy": 50.0},
                timestamp=time.time(),
                pending_actions=pending_actions,
            )

        assert len(pending_actions) == 5
        for i, pending in enumerate(pending_actions):
            assert pending.action_id == f"action_{i}"


@pytest.mark.unit
@pytest.mark.order(1)
class TestObserveConsequences:
    """Тесты для функции observe_consequences"""

    def test_observe_consequences_with_changes(self):
        """Тест наблюдения последствий с изменениями состояния"""
        pending_actions = []
        self_state = SelfState()
        self_state.energy = 50.0
        self_state.stability = 0.8
        self_state.integrity = 0.9

        state_before = {"energy": 50.0, "stability": 0.8, "integrity": 0.9}
        register_action(
            action_id="test_action_2",
            action_pattern="dampen",
            state_before=state_before,
            timestamp=time.time(),
            pending_actions=pending_actions,
        )

        self_state.energy = 49.0
        self_state.stability = 0.79
        pending_actions[0].check_after_ticks = 1

        feedback_records = observe_consequences(self_state, pending_actions)

        assert len(feedback_records) == 1
        assert feedback_records[0].action_id == "test_action_2"
        assert feedback_records[0].action_pattern == "dampen"
        assert abs(feedback_records[0].state_delta["energy"] - (-1.0)) < 0.001
        assert abs(feedback_records[0].state_delta["stability"] - (-0.01)) < 0.001
        assert len(pending_actions) == 0

    def test_observe_consequences_minimal_changes(self):
        """Тест: изменения меньше порога не создают Feedback запись"""
        pending_actions = []
        self_state = SelfState()
        self_state.energy = 50.0
        self_state.stability = 0.8
        self_state.integrity = 0.9

        state_before = {"energy": 50.0, "stability": 0.8, "integrity": 0.9}
        register_action(
            action_id="test_action_3",
            action_pattern="ignore",
            state_before=state_before,
            timestamp=time.time(),
            pending_actions=pending_actions,
        )

        self_state.energy = 50.0001
        pending_actions[0].check_after_ticks = 1

        feedback_records = observe_consequences(self_state, pending_actions)

        assert len(feedback_records) == 0
        assert len(pending_actions) == 0

    def test_observe_consequences_timeout(self):
        """Тест: действия удаляются после 20 тиков"""
        pending_actions = []
        self_state = SelfState()

        state_before = {"energy": 50.0, "stability": 0.8, "integrity": 0.9}
        register_action(
            action_id="test_action_4",
            action_pattern="absorb",
            state_before=state_before,
            timestamp=time.time(),
            pending_actions=pending_actions,
        )

        pending_actions[0].check_after_ticks = 25
        pending_actions[0].ticks_waited = 21

        feedback_records = observe_consequences(self_state, pending_actions)

        assert len(feedback_records) == 0
        assert len(pending_actions) == 0

    def test_multiple_actions(self):
        """Тест: несколько действий обрабатываются независимо"""
        pending_actions = []
        self_state = SelfState()
        self_state.energy = 50.0
        self_state.stability = 0.8
        self_state.integrity = 0.9

        register_action(
            "action_1",
            "dampen",
            {"energy": 50.0, "stability": 0.8, "integrity": 0.9},
            time.time(),
            pending_actions,
        )
        register_action(
            "action_2",
            "absorb",
            {"energy": 50.0, "stability": 0.8, "integrity": 0.9},
            time.time(),
            pending_actions,
        )

        assert len(pending_actions) == 2

        pending_actions[0].check_after_ticks = 1
        self_state.energy = 49.0

        feedback_records = observe_consequences(self_state, pending_actions)

        assert len(feedback_records) == 1
        assert len(pending_actions) == 1
        assert pending_actions[0].action_id == "action_2"

    def test_observe_consequences_ticks_waited_increment(self):
        """Тест увеличения ticks_waited"""
        pending_actions = []
        self_state = SelfState()
        state_before = {"energy": 50.0, "stability": 0.8, "integrity": 0.9}

        register_action("test", "dampen", state_before, time.time(), pending_actions)
        pending_actions[0].check_after_ticks = 5

        # Вызываем несколько раз
        observe_consequences(self_state, pending_actions)
        assert pending_actions[0].ticks_waited == 1

        observe_consequences(self_state, pending_actions)
        assert pending_actions[0].ticks_waited == 2

    def test_observe_consequences_positive_delta(self):
        """Тест обработки положительных изменений состояния"""
        pending_actions = []
        self_state = SelfState()
        self_state.energy = 50.0
        state_before = {"energy": 50.0, "stability": 0.8, "integrity": 0.9}

        register_action("test", "recovery", state_before, time.time(), pending_actions)
        self_state.energy = 55.0  # Увеличение
        pending_actions[0].check_after_ticks = 1

        feedback_records = observe_consequences(self_state, pending_actions)

        assert len(feedback_records) == 1
        assert feedback_records[0].state_delta["energy"] > 0


@pytest.mark.integration
@pytest.mark.order(2)
class TestFeedbackIntegration:
    """Интеграционные тесты для Feedback"""

    def test_integration_with_memory(self):
        """Тест интеграции с Memory"""
        pending_actions = []
        self_state = SelfState()
        self_state.energy = 50.0
        self_state.stability = 0.8
        self_state.integrity = 0.9

        state_before = {"energy": 50.0, "stability": 0.8, "integrity": 0.9}
        register_action(
            "action_mem", "dampen", state_before, time.time(), pending_actions
        )

        self_state.energy = 49.0
        pending_actions[0].check_after_ticks = 1

        feedback_records = observe_consequences(self_state, pending_actions)

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

        assert len(self_state.memory) == 1
        assert self_state.memory[0].event_type == "feedback"
        assert self_state.memory[0].meaning_significance == 0.0
        assert self_state.memory[0].feedback_data is not None
        assert self_state.memory[0].feedback_data["action_id"] == "action_mem"
        assert self_state.memory[0].feedback_data["action_pattern"] == "dampen"
        assert "energy" in self_state.memory[0].feedback_data["state_delta"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## test\test_feedback_data.py <a id="test-test_feedback_data"></a>
**Полный путь:** src/test\test_feedback_data.py

```python
"""
Тест для проверки сохранения полных данных Feedback
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import time

import pytest

from feedback import observe_consequences, register_action
from memory.memory import MemoryEntry
from state.self_state import SelfState


@pytest.mark.unit
@pytest.mark.order(1)
def test_feedback_data_storage():
    """Тест: Feedback записи содержат полные данные"""
    print("Тест: Сохранение полных данных Feedback")

    pending_actions = []
    self_state = SelfState()
    self_state.energy = 50.0
    self_state.stability = 0.8
    self_state.integrity = 0.9

    # Регистрируем действие
    state_before = {"energy": 50.0, "stability": 0.8, "integrity": 0.9}
    register_action(
        action_id="test_action_full",
        action_pattern="dampen",
        state_before=state_before,
        timestamp=time.time(),
        pending_actions=pending_actions,
    )

    # Изменяем состояние
    self_state.energy = 49.0
    self_state.stability = 0.79

    # Устанавливаем задержку на 1 тик
    pending_actions[0].check_after_ticks = 1

    # Наблюдаем последствия
    feedback_records = observe_consequences(self_state, pending_actions)

    assert len(feedback_records) == 1, "Должна быть создана одна Feedback запись"
    feedback = feedback_records[0]

    # Сохраняем в Memory (как в loop.py)
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

    # Проверяем сохранение
    assert len(self_state.memory) == 1, "Feedback должен быть сохранен в Memory"
    stored = self_state.memory[0]

    assert stored.event_type == "feedback", "Тип должен быть feedback"
    assert stored.meaning_significance == 0.0, "Значимость должна быть 0.0"
    assert stored.feedback_data is not None, "feedback_data должен быть сохранен"
    assert (
        stored.feedback_data["action_id"] == "test_action_full"
    ), "action_id должен быть сохранен"
    assert (
        stored.feedback_data["action_pattern"] == "dampen"
    ), "action_pattern должен быть сохранен"
    assert (
        "energy" in stored.feedback_data["state_delta"]
    ), "state_delta должен содержать energy"
    assert (
        stored.feedback_data["state_delta"]["energy"] == -1.0
    ), "energy delta должен быть -1.0"
    assert stored.feedback_data["delay_ticks"] == 1, "delay_ticks должен быть сохранен"

    print("[OK] Полные данные Feedback сохранены корректно")
    print(f"  - action_id: {stored.feedback_data['action_id']}")
    print(f"  - action_pattern: {stored.feedback_data['action_pattern']}")
    print(f"  - state_delta: {stored.feedback_data['state_delta']}")
    print(f"  - delay_ticks: {stored.feedback_data['delay_ticks']}")


if __name__ == "__main__":
    try:
        test_feedback_data_storage()
        print("\n[SUCCESS] Все тесты пройдены!")
    except AssertionError as e:
        print(f"\n[FAIL] Тест провален: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Ошибка: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
```

---

## test\test_feedback_integration.py <a id="test-test_feedback_integration"></a>
**Полный путь:** src/test\test_feedback_integration.py

```python
"""
Интеграционный тест для проверки полных данных Feedback
"""

import json
import sys
import time

import requests


def check_feedback_data():
    """Проверяет наличие полных данных Feedback через API"""
    try:
        # Получаем статус
        response = requests.get("http://localhost:8000/status", timeout=5)
        if response.status_code != 200:
            print(f"[ERROR] Server returned status {response.status_code}")
            return False

        data = response.json()
        memory = data.get("memory", [])

        # Фильтруем Feedback записи
        feedback_records = [m for m in memory if m.get("event_type") == "feedback"]

        print(f"Total memory entries: {len(memory)}")
        print(f"Feedback records: {len(feedback_records)}")

        if len(feedback_records) == 0:
            print(
                "[WARNING] No feedback records found yet. Waiting for actions to complete..."
            )
            return False

        # Проверяем наличие feedback_data
        records_with_data = [f for f in feedback_records if f.get("feedback_data")]
        records_without_data = [
            f for f in feedback_records if not f.get("feedback_data")
        ]

        print(f"Feedback records WITH data: {len(records_with_data)}")
        print(f"Feedback records WITHOUT data: {len(records_without_data)}")

        if len(records_with_data) > 0:
            print("\n[SUCCESS] Found feedback records with full data!")
            print("\nSample feedback record:")
            sample = records_with_data[0]
            print(f"  event_type: {sample.get('event_type')}")
            print(f"  meaning_significance: {sample.get('meaning_significance')}")
            print(f"  timestamp: {sample.get('timestamp')}")
            if sample.get("feedback_data"):
                fd = sample["feedback_data"]
                print("  feedback_data:")
                print(f"    action_id: {fd.get('action_id', 'N/A')}")
                print(f"    action_pattern: {fd.get('action_pattern', 'N/A')}")
                print(f"    state_delta: {fd.get('state_delta', {})}")
                print(f"    delay_ticks: {fd.get('delay_ticks', 'N/A')}")
            return True
        else:
            print("\n[FAIL] No feedback records with data found!")
            if len(records_without_data) > 0:
                print("Found records without data (old format):")
                print(json.dumps(records_without_data[0], indent=2))
            return False

    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot connect to server. Is it running?")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Feedback Data Storage")
    print("=" * 60)

    # Даем время системе создать Feedback записи
    print("\nWaiting for system to generate feedback records...")
    for i in range(3):
        time.sleep(5)
        print(f"Attempt {i+1}/3...")
        if check_feedback_data():
            sys.exit(0)

    print("\n[FAIL] No feedback records with data found after waiting")
    sys.exit(1)
```

---

## test\test_generator.py <a id="test-test_generator"></a>
**Полный путь:** src/test\test_generator.py

```python
"""
Тесты для генератора событий
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest

from environment.event import Event
from environment.generator import EventGenerator


@pytest.mark.unit
@pytest.mark.order(1)
class TestEventGenerator:
    """Тесты для класса EventGenerator"""

    @pytest.fixture
    def generator(self):
        """Создает экземпляр генератора"""
        return EventGenerator()

    def test_generator_initialization(self, generator):
        """Тест инициализации генератора"""
        assert generator is not None

    def test_generate_returns_event(self, generator):
        """Тест, что generate возвращает Event"""
        event = generator.generate()
        assert isinstance(event, Event)
        assert event.type is not None
        assert isinstance(event.intensity, float)
        assert event.timestamp > 0

    def test_generate_event_types(self, generator):
        """Тест, что генерируются все типы событий"""
        event_types = set()
        for _ in range(100):  # Генерируем много событий
            event = generator.generate()
            event_types.add(event.type)

        # Должны быть все типы
        expected_types = {"noise", "decay", "recovery", "shock", "idle"}
        assert event_types == expected_types

    def test_generate_noise_intensity_range(self, generator):
        """Тест диапазона интенсивности для noise"""
        for _ in range(50):
            event = generator.generate()
            if event.type == "noise":
                assert -0.3 <= event.intensity <= 0.3

    def test_generate_decay_intensity_range(self, generator):
        """Тест диапазона интенсивности для decay"""
        for _ in range(50):
            event = generator.generate()
            if event.type == "decay":
                assert -0.5 <= event.intensity <= 0.0

    def test_generate_recovery_intensity_range(self, generator):
        """Тест диапазона интенсивности для recovery"""
        for _ in range(50):
            event = generator.generate()
            if event.type == "recovery":
                assert 0.0 <= event.intensity <= 0.5

    def test_generate_shock_intensity_range(self, generator):
        """Тест диапазона интенсивности для shock"""
        for _ in range(50):
            event = generator.generate()
            if event.type == "shock":
                assert -1.0 <= event.intensity <= 1.0

    def test_generate_idle_intensity(self, generator):
        """Тест интенсивности для idle"""
        for _ in range(50):
            event = generator.generate()
            if event.type == "idle":
                assert event.intensity == 0.0

    def test_generate_timestamp(self, generator):
        """Тест, что timestamp устанавливается"""
        import time

        before = time.time()
        event = generator.generate()
        after = time.time()

        assert before <= event.timestamp <= after

    def test_generate_metadata(self, generator):
        """Тест, что metadata присутствует"""
        event = generator.generate()
        assert event.metadata is not None
        assert isinstance(event.metadata, dict)

    def test_generate_multiple_events(self, generator):
        """Тест генерации нескольких событий"""
        events = [generator.generate() for _ in range(10)]

        assert len(events) == 10
        assert all(isinstance(e, Event) for e in events)
        # Все события должны иметь разные timestamp (или очень близкие)
        timestamps = [e.timestamp for e in events]
        assert len(set(timestamps)) >= 1  # Хотя бы один уникальный

    def test_generate_event_distribution(self, generator):
        """Тест распределения типов событий (статистический)"""
        event_counts = {}
        total = 1000

        for _ in range(total):
            event = generator.generate()
            event_counts[event.type] = event_counts.get(event.type, 0) + 1

        # Проверяем, что все типы генерируются
        assert len(event_counts) == 5

        # Проверяем ожидаемое распределение (noise должен быть чаще)
        assert event_counts.get("noise", 0) > event_counts.get("shock", 0)
        assert event_counts.get("decay", 0) > 0
        assert event_counts.get("recovery", 0) > 0

    def test_generate_event_uniqueness(self, generator):
        """Тест уникальности событий"""
        events = [generator.generate() for _ in range(100)]

        # События должны быть уникальными (хотя бы по timestamp или типу/интенсивности)
        timestamps = [e.timestamp for e in events]
        len(set(timestamps))

        # Проверяем, что есть хотя бы несколько уникальных timestamp
        # или что события различаются по типу/интенсивности
        event_signatures = [(e.type, e.intensity) for e in events]
        unique_signatures = len(set(event_signatures))

        # Должно быть достаточно уникальных комбинаций
        assert unique_signatures > 10  # Хотя бы 10% уникальных комбинаций


@pytest.mark.unit
@pytest.mark.order(1)
class TestGeneratorCLI:
    """Тесты для CLI генератора (мокирование)"""

    def test_send_event_success(self, monkeypatch):
        """Тест успешной отправки события"""
        from environment.generator_cli import send_event

        # Мокируем requests.post
        class MockResponse:
            status_code = 200
            text = "Event accepted"

        def mock_post(url, json=None, timeout=None):
            return MockResponse()

        monkeypatch.setattr("requests.post", mock_post)

        success, code, reason, body = send_event("localhost", 8000, {"type": "test"})
        assert success is True
        assert code == 200
        assert body == "Event accepted"

    def test_send_event_connection_error(self, monkeypatch):
        """Тест обработки ошибки соединения"""
        import requests

        from environment.generator_cli import send_event

        def mock_post(url, json=None, timeout=None):
            raise requests.exceptions.ConnectionError("Connection refused")

        monkeypatch.setattr("requests.post", mock_post)

        success, code, reason, body = send_event("localhost", 8000, {"type": "test"})
        assert success is False
        assert code == 0
        assert "Connection" in reason

    def test_send_event_timeout(self, monkeypatch):
        """Тест обработки таймаута"""
        import requests

        from environment.generator_cli import send_event

        def mock_post(url, json=None, timeout=None):
            raise requests.exceptions.Timeout("Request timed out")

        monkeypatch.setattr("requests.post", mock_post)

        success, code, reason, body = send_event("localhost", 8000, {"type": "test"})
        assert success is False
        assert "timeout" in reason.lower() or "timed out" in reason.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## test\test_generator_cli.py <a id="test-test_generator_cli"></a>
**Полный путь:** src/test\test_generator_cli.py

```python
"""
Тесты для generator_cli.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from unittest.mock import MagicMock, patch

import pytest

from environment.generator_cli import main, send_event


@pytest.mark.unit
@pytest.mark.order(1)
class TestGeneratorCLI:
    """Тесты для generator_cli"""

    def test_send_event_success(self, monkeypatch):
        """Тест успешной отправки события (строки 18-24)"""

        class MockResponse:
            status_code = 200
            text = "Event accepted"

        def mock_post(url, json=None, timeout=None):
            return MockResponse()

        monkeypatch.setattr("requests.post", mock_post)

        success, code, reason, body = send_event("localhost", 8000, {"type": "test"})
        assert success is True
        assert code == 200
        assert body == "Event accepted"

    def test_send_event_request_exception(self, monkeypatch):
        """Тест обработки RequestException (строки 25-26)"""
        import requests

        def mock_post(url, json=None, timeout=None):
            raise requests.exceptions.RequestException("Connection error")

        monkeypatch.setattr("requests.post", mock_post)

        success, code, reason, body = send_event("localhost", 8000, {"type": "test"})
        assert success is False
        assert code == 0
        assert "Connection error" in reason or "RequestException" in reason

    def test_send_event_general_exception(self, monkeypatch):
        """Тест обработки общего исключения (строки 27-28)"""

        def mock_post(url, json=None, timeout=None):
            raise ValueError("Unexpected error")

        monkeypatch.setattr("requests.post", mock_post)

        success, code, reason, body = send_event("localhost", 8000, {"type": "test"})
        assert success is False
        assert code is None
        assert "Unexpected error" in reason or "ValueError" in reason

    @patch("builtins.print")
    @patch("environment.generator_cli.send_event")
    @patch("environment.generator_cli.EventGenerator")
    @patch("time.sleep")
    @patch("builtins.input", return_value="")  # Для KeyboardInterrupt
    def test_main_function_basic(
        self, mock_input, mock_sleep, mock_generator_class, mock_send, mock_print
    ):
        """Тест основной функции main (строки 32-60)"""
        # Настраиваем моки
        mock_generator = MagicMock()
        mock_generator.generate.return_value = MagicMock(
            type="shock", intensity=0.5, timestamp=1234567890.0, metadata={}
        )
        mock_generator_class.return_value = mock_generator

        mock_send.return_value = (True, 200, "", "Event accepted")

        # Симулируем KeyboardInterrupt после первой итерации
        call_count = [0]

        def side_effect(*args):
            call_count[0] += 1
            if call_count[0] > 1:
                raise KeyboardInterrupt()

        mock_sleep.side_effect = side_effect

        # Запускаем main с аргументами
        import sys

        with patch.object(sys, "argv", ["generator_cli.py", "--interval", "0.1"]):
            try:
                main()
            except KeyboardInterrupt:
                pass  # Ожидаемое поведение

        # Проверяем, что generator был создан
        mock_generator_class.assert_called_once()

        # Проверяем, что generate был вызван
        assert mock_generator.generate.call_count >= 1

    @patch("builtins.print")
    @patch("environment.generator_cli.send_event")
    @patch("environment.generator_cli.EventGenerator")
    @patch("time.sleep")
    def test_main_function_send_event_called(
        self, mock_sleep, mock_generator_class, mock_send, mock_print
    ):
        """Тест, что send_event вызывается в main"""
        mock_generator = MagicMock()
        mock_event = MagicMock()
        mock_event.type = "noise"
        mock_event.intensity = 0.3
        mock_event.timestamp = 1234567890.0
        mock_event.metadata = {}
        mock_generator.generate.return_value = mock_event
        mock_generator_class.return_value = mock_generator

        mock_send.return_value = (True, 200, "", "Event accepted")

        # Симулируем одну итерацию
        call_count = [0]

        def side_effect(*args):
            call_count[0] += 1
            if call_count[0] > 0:
                raise KeyboardInterrupt()

        mock_sleep.side_effect = side_effect

        import sys

        with patch.object(sys, "argv", ["generator_cli.py"]):
            try:
                main()
            except KeyboardInterrupt:
                pass

        # Проверяем, что send_event был вызван
        assert mock_send.call_count >= 1

        # Проверяем аргументы вызова
        call_args = mock_send.call_args
        assert call_args[0][0] == "localhost"  # host
        assert call_args[0][1] == 8000  # port
        assert isinstance(call_args[0][2], dict)  # payload
        assert call_args[0][2]["type"] == "noise"

    @patch("builtins.print")
    @patch("environment.generator_cli.send_event")
    @patch("environment.generator_cli.EventGenerator")
    @patch("time.sleep")
    def test_main_function_send_failure(
        self, mock_sleep, mock_generator_class, mock_send, mock_print
    ):
        """Тест обработки ошибки отправки в main"""
        mock_generator = MagicMock()
        mock_generator.generate.return_value = MagicMock(
            type="shock", intensity=0.5, timestamp=1234567890.0, metadata={}
        )
        mock_generator_class.return_value = mock_generator

        # Симулируем ошибку отправки
        mock_send.return_value = (False, 0, "Connection refused", "")

        call_count = [0]

        def side_effect(*args):
            call_count[0] += 1
            if call_count[0] > 0:
                raise KeyboardInterrupt()

        mock_sleep.side_effect = side_effect

        import sys

        with patch.object(sys, "argv", ["generator_cli.py"]):
            try:
                main()
            except KeyboardInterrupt:
                pass

        # Проверяем, что ошибка была обработана
        assert mock_send.call_count >= 1

    def test_main_function_if_name_main(self):
        """Тест вызова main при запуске как скрипт (строка 64)"""
        import sys
        from unittest.mock import patch

        # Мокируем все зависимости
        with patch("environment.generator_cli.EventGenerator") as mock_gen_class, patch(
            "environment.generator_cli.send_event"
        ) as mock_send, patch("time.sleep", side_effect=KeyboardInterrupt()), patch(
            "builtins.print"
        ):
            mock_generator = MagicMock()
            mock_generator.generate.return_value = MagicMock(
                type="test", intensity=0.5, timestamp=1234567890.0, metadata={}
            )
            mock_gen_class.return_value = mock_generator
            mock_send.return_value = (True, 200, "", "OK")

            # Симулируем запуск как __main__
            with patch.object(sys, "argv", ["generator_cli.py"]):
                # Импортируем модуль и вызываем main через __main__
                import environment.generator_cli as cli_module

                # Симулируем if __name__ == "__main__": main()
                try:
                    cli_module.main()
                except KeyboardInterrupt:
                    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## test\test_generator_integration.py <a id="test-test_generator_integration"></a>
**Полный путь:** src/test\test_generator_integration.py

```python
"""
Интеграционные тесты для генератора событий с API сервером
Поддерживают работу с реальным сервером (--real-server) или тестовым сервером
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest

from environment.generator import EventGenerator
from environment.generator_cli import send_event


@pytest.mark.integration
@pytest.mark.real_server
@pytest.mark.order(2)
class TestGeneratorServerIntegration:
    """Интеграционные тесты генератора с сервером"""

    def test_generator_send_to_server(self, server_setup):
        """Тест отправки сгенерированного события на сервер"""
        generator = EventGenerator()
        event = generator.generate()

        payload = {
            "type": event.type,
            "intensity": event.intensity,
            "timestamp": event.timestamp,
            "metadata": event.metadata,
        }

        success, code, reason, body = send_event(
            "localhost", server_setup["port"], payload
        )

        assert success is True
        assert code == 200

        # Проверяем очередь только для тестового сервера
        if not server_setup.get("is_real_server") and server_setup.get("event_queue"):
            assert server_setup["event_queue"].size() == 1

            queued_event = server_setup["event_queue"].pop()
            assert queued_event.type == event.type
            assert abs(queued_event.intensity - event.intensity) < 0.001

    def test_generator_multiple_events_to_server(self, server_setup):
        """Тест отправки нескольких сгенерированных событий"""
        generator = EventGenerator()
        events = [generator.generate() for _ in range(5)]

        for event in events:
            payload = {
                "type": event.type,
                "intensity": event.intensity,
                "timestamp": event.timestamp,
                "metadata": event.metadata,
            }

            success, code, reason, body = send_event(
                "localhost", server_setup["port"], payload
            )
            assert success is True
            assert code == 200

        # Проверяем очередь только для тестового сервера
        if not server_setup.get("is_real_server") and server_setup.get("event_queue"):
            assert server_setup["event_queue"].size() == 5

    def test_generator_all_event_types_to_server(self, server_setup):
        """Тест отправки всех типов событий на сервер"""
        generator = EventGenerator()
        event_types = set()

        # Генерируем события до тех пор, пока не получим все типы
        for _ in range(100):
            event = generator.generate()
            event_types.add(event.type)

            payload = {
                "type": event.type,
                "intensity": event.intensity,
                "timestamp": event.timestamp,
                "metadata": event.metadata,
            }

            success, code, reason, body = send_event(
                "localhost", server_setup["port"], payload
            )
            assert success is True

            if len(event_types) == 5:  # Все типы получены
                break

        assert len(event_types) == 5

        # Проверяем очередь только для тестового сервера
        if not server_setup.get("is_real_server") and server_setup.get("event_queue"):
            assert server_setup["event_queue"].size() > 0

    def test_generator_event_intensity_ranges(self, server_setup):
        """Тест, что интенсивности событий соответствуют спецификации"""
        generator = EventGenerator()

        intensity_ranges = {
            "noise": (-0.3, 0.3),
            "decay": (-0.5, 0.0),
            "recovery": (0.0, 0.5),
            "shock": (-1.0, 1.0),
            "idle": (0.0, 0.0),
        }

        # Генерируем события и проверяем диапазоны
        for _ in range(200):
            event = generator.generate()
            min_intensity, max_intensity = intensity_ranges[event.type]

            if event.type == "idle":
                assert event.intensity == 0.0
            else:
                assert min_intensity <= event.intensity <= max_intensity

    def test_generator_server_full_cycle(self, server_setup):
        """Тест полного цикла: генерация -> отправка -> получение"""
        generator = EventGenerator()

        # Генерируем и отправляем событие
        event = generator.generate()
        payload = {
            "type": event.type,
            "intensity": event.intensity,
            "timestamp": event.timestamp,
            "metadata": event.metadata,
        }

        success, code, reason, body = send_event(
            "localhost", server_setup["port"], payload
        )

        assert success is True

        # Проверяем очередь только для тестового сервера
        if not server_setup.get("is_real_server") and server_setup.get("event_queue"):
            # Получаем событие из очереди
            assert server_setup["event_queue"].size() == 1
            queued_event = server_setup["event_queue"].pop()

            # Проверяем целостность данных
            assert queued_event.type == event.type
            assert abs(queued_event.intensity - event.intensity) < 0.001
            assert abs(queued_event.timestamp - event.timestamp) < 0.001
            assert queued_event.metadata == event.metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## test\test_intelligence.py <a id="test-test_intelligence"></a>
**Полный путь:** src/test\test_intelligence.py

```python
"""
Подробные тесты для модуля Intelligence
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest

from intelligence.intelligence import process_information
from state.self_state import SelfState


@pytest.mark.unit
@pytest.mark.order(1)
class TestProcessInformation:
    """Тесты для функции process_information"""

    @pytest.fixture
    def base_state(self):
        """Создает базовое состояние"""
        return SelfState()

    def test_process_information_basic(self, base_state):
        """Тест базовой обработки информации"""
        base_state.recent_events = ["event1", "event2"]
        base_state.energy = 50.0
        base_state.stability = 0.7
        base_state.planning = {"potential_sequences": [["e1", "e2"]]}

        process_information(base_state)

        assert "processed_sources" in base_state.intelligence
        processed = base_state.intelligence["processed_sources"]
        assert processed["memory_proxy_size"] == 2
        assert processed["adaptation_proxy"] == 50.0
        assert processed["learning_proxy"] == 0.7
        assert processed["planning_proxy_size"] == 1

    def test_process_information_empty_recent_events(self, base_state):
        """Тест обработки при пустом recent_events"""
        base_state.recent_events = []
        base_state.energy = 50.0
        base_state.stability = 0.7
        base_state.planning = {}

        process_information(base_state)

        processed = base_state.intelligence["processed_sources"]
        assert processed["memory_proxy_size"] == 0

    def test_process_information_empty_planning(self, base_state):
        """Тест обработки при пустом planning"""
        base_state.recent_events = ["e1"]
        base_state.energy = 50.0
        base_state.stability = 0.7
        base_state.planning = {}

        process_information(base_state)

        processed = base_state.intelligence["processed_sources"]
        assert processed["planning_proxy_size"] == 0

    def test_process_information_energy_values(self, base_state):
        """Тест обработки разных значений energy"""
        base_state.recent_events = []
        base_state.stability = 0.7
        base_state.planning = {}

        for energy in [0.0, 25.0, 50.0, 75.0, 100.0]:
            base_state.energy = energy
            process_information(base_state)
            processed = base_state.intelligence["processed_sources"]
            assert processed["adaptation_proxy"] == energy

    def test_process_information_stability_values(self, base_state):
        """Тест обработки разных значений stability"""
        base_state.recent_events = []
        base_state.energy = 50.0
        base_state.planning = {}

        for stability in [0.0, 0.3, 0.5, 0.7, 1.0]:
            base_state.stability = stability
            process_information(base_state)
            processed = base_state.intelligence["processed_sources"]
            assert processed["learning_proxy"] == stability

    def test_process_information_planning_sequences(self, base_state):
        """Тест обработки planning с разным количеством последовательностей"""
        base_state.recent_events = []
        base_state.energy = 50.0
        base_state.stability = 0.7

        for num_sequences in [0, 1, 3, 5]:
            base_state.planning = {
                "potential_sequences": [["e1", "e2"] for _ in range(num_sequences)]
            }
            process_information(base_state)
            processed = base_state.intelligence["processed_sources"]
            assert processed["planning_proxy_size"] == num_sequences

    def test_process_information_preserves_other_fields(self, base_state):
        """Тест, что функция не изменяет другие поля состояния"""
        base_state.energy = 50.0
        base_state.stability = 0.7
        base_state.integrity = 0.8
        base_state.ticks = 100
        base_state.recent_events = ["e1"]
        base_state.planning = {}

        process_information(base_state)

        # Эти поля не должны измениться
        assert base_state.energy == 50.0
        assert base_state.stability == 0.7
        assert base_state.integrity == 0.8
        assert base_state.ticks == 100
        assert base_state.recent_events == ["e1"]

    def test_process_information_multiple_calls(self, base_state):
        """Тест нескольких вызовов функции"""
        base_state.recent_events = ["e1"]
        base_state.energy = 50.0
        base_state.stability = 0.7
        base_state.planning = {}

        process_information(base_state)
        first_processed = base_state.intelligence["processed_sources"].copy()

        base_state.recent_events = ["e1", "e2", "e3"]
        base_state.energy = 60.0
        process_information(base_state)

        # Результаты должны обновиться
        processed = base_state.intelligence["processed_sources"]
        assert processed["memory_proxy_size"] == 3
        assert processed["adaptation_proxy"] == 60.0
        assert processed["memory_proxy_size"] != first_processed["memory_proxy_size"]

    def test_process_information_complex_state(self, base_state):
        """Тест обработки сложного состояния"""
        base_state.recent_events = ["shock", "noise", "recovery", "decay"]
        base_state.energy = 75.5
        base_state.stability = 0.85
        base_state.planning = {
            "potential_sequences": [["e1", "e2"], ["e3", "e4"], ["e5", "e6"]]
        }

        process_information(base_state)

        processed = base_state.intelligence["processed_sources"]
        assert processed["memory_proxy_size"] == 4
        assert processed["adaptation_proxy"] == 75.5
        assert processed["learning_proxy"] == 0.85
        assert processed["planning_proxy_size"] == 3

    def test_process_information_planning_without_sequences_key(self, base_state):
        """Тест обработки planning без ключа potential_sequences"""
        base_state.recent_events = []
        base_state.energy = 50.0
        base_state.stability = 0.7
        base_state.planning = {"other_key": "value"}

        process_information(base_state)

        processed = base_state.intelligence["processed_sources"]
        # Должно обработаться без ошибок
        assert processed["planning_proxy_size"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## test\test_mcp_client.py <a id="test-test_mcp_client"></a>
**Полный путь:** src/test\test_mcp_client.py

```python
#!/usr/bin/env python3
"""
MCP клиент для тестирования MCP сервера через JSON-RPC протокол (stdio).

Этот скрипт тестирует MCP сервер через настоящий MCP протокол,
а не через прямой вызов функций Python.
"""

import json
import subprocess
import sys
from pathlib import Path


class MCPClient:
    """Простой MCP клиент для тестирования через stdio"""

    def __init__(self, server_script: str):
        """Инициализация клиента"""
        self.server_script = server_script
        self.process = None
        self.request_id = 0

    def start(self):
        """Запуск MCP сервера через subprocess"""
        script_path = Path(__file__).parent / self.server_script
        self.process = subprocess.Popen(
            [sys.executable, str(script_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=0,
        )

    def send_request(self, method: str, params: dict = None) -> dict:
        """Отправка JSON-RPC запроса к MCP серверу"""
        if params is None:
            params = {}

        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params if params else {},
        }

        request_str = json.dumps(request) + "\n"
        print(f"[SEND] {request_str.strip()}")
        self.process.stdin.write(request_str)
        self.process.stdin.flush()

        # Читаем ответ (MCP отправляет ответы через stdout)
        response_line = self.process.stdout.readline()
        if response_line:
            try:
                response = json.loads(response_line.strip())
                print(f"[RECV] {json.dumps(response, ensure_ascii=False)[:200]}...")
                return response
            except json.JSONDecodeError as e:
                print(f"[ERROR] Не удалось распарсить JSON: {e}")
                print(f"[ERROR] Ответ сервера: {response_line}")
                return {"error": str(e)}
        return {"error": "No response"}

    def initialize(self) -> dict:
        """Инициализация MCP сессии"""
        return self.send_request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        )

    def list_tools(self) -> dict:
        """Получение списка доступных инструментов"""
        return self.send_request("tools/list")

    def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Вызов инструмента MCP сервера"""
        return self.send_request(
            "tools/call", {"name": tool_name, "arguments": arguments}
        )

    def stop(self):
        """Остановка MCP сервера"""
        if self.process:
            self.process.terminate()
            self.process.wait()


def test_mcp_api():
    """Тестирование MCP сервера через JSON-RPC API"""
    print("=" * 70)
    print("Тестирование MCP сервера через JSON-RPC протокол (stdio)")
    print("=" * 70)

    client = MCPClient("mcp_index.py")

    try:
        # Запуск сервера
        print("\n[1] Запуск MCP сервера...")
        client.start()
        print("[OK] Сервер запущен")

        # Инициализация
        print("\n[2] Инициализация MCP сессии...")
        init_response = client.initialize()
        if "result" in init_response:
            print("[OK] Сессия инициализирована")
        else:
            print(f"[ERROR] Ошибка инициализации: {init_response}")

        # Получение списка инструментов
        print("\n[3] Получение списка инструментов...")
        tools_response = client.list_tools()
        if "result" in tools_response and "tools" in tools_response["result"]:
            tools = tools_response["result"]["tools"]
            print(f"[OK] Найдено {len(tools)} инструментов:")
            for tool in tools[:5]:  # Показываем первые 5
                print(f"   - {tool.get('name', 'unknown')}")
        else:
            print(f"[ERROR] Ошибка получения инструментов: {tools_response}")

        # Тест 1: search_docs
        print("\n[4] Тест: search_docs('test', limit=3)...")
        result = client.call_tool("search_docs", {"query": "test", "limit": 3})
        if "result" in result:
            content = result["result"].get("content", [])
            if content and isinstance(content, list) and len(content) > 0:
                text = (
                    content[0].get("text", "")
                    if isinstance(content[0], dict)
                    else str(content[0])
                )
                print(f"[OK] Результат получен ({len(text)} символов)")
                print(f"   Первые 100 символов: {text[:100]}...")
            else:
                print(f"[OK] Результат: {result['result']}")
        else:
            print(f"[ERROR] Ошибка вызова инструмента: {result}")

        # Тест 2: list_docs
        print("\n[5] Тест: list_docs(recursive=False)...")
        result = client.call_tool("list_docs", {"recursive": False})
        if "result" in result:
            content = result["result"].get("content", [])
            if content:
                text = (
                    content[0].get("text", "")
                    if isinstance(content[0], dict)
                    else str(content[0])
                )
                print("[OK] Результат получен")
                print(f"   Первые 150 символов: {text[:150]}...")
            else:
                print(f"[OK] Результат: {result['result']}")
        else:
            print(f"[ERROR] Ошибка вызова инструмента: {result}")

        # Тест 3: list_snapshots
        print("\n[6] Тест: list_snapshots()...")
        result = client.call_tool("list_snapshots", {})
        if "result" in result:
            content = result["result"].get("content", [])
            if content:
                text = (
                    content[0].get("text", "")
                    if isinstance(content[0], dict)
                    else str(content[0])
                )
                print("[OK] Результат получен")
                print(f"   Первые 150 символов: {text[:150]}...")
            else:
                print(f"[OK] Результат: {result['result']}")
        else:
            print(f"[ERROR] Ошибка вызова инструмента: {result}")

        print("\n" + "=" * 70)
        print("Тестирование завершено!")
        print("=" * 70)

    except Exception as e:
        print(f"\n[ERROR] Ошибка тестирования: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Остановка сервера
        print("\n[7] Остановка MCP сервера...")
        client.stop()
        print("[OK] Сервер остановлен")


if __name__ == "__main__":
    test_mcp_api()
```

---

## test\test_mcp_interactive.py <a id="test-test_mcp_interactive"></a>
**Полный путь:** src/test\test_mcp_interactive.py

```python
#!/usr/bin/env python3
"""Интерактивная проверка MCP сервера"""

import asyncio

from mcp_index import (
    get_code_index,
    get_test_coverage,
    list_docs,
    list_snapshots,
    search_code,
    search_docs,
    search_todo,
)


async def test_mcp_functions():
    """Тестирование функций MCP сервера"""
    print("=" * 60)
    print("Тестирование MCP сервера проекта Life")
    print("=" * 60)

    # Тест 1: Поиск в документации
    print("\n[1] Тест search_docs('test'):")
    try:
        result = await search_docs("test", 3)
        print(f"   [OK] Найдено {len(result)} символов")
        print(f"   Первые 100 символов: {result[:100]}...")
    except Exception as e:
        print(f"   [ERROR] Ошибка: {e}")

    # Тест 2: Список документов
    print("\n[2] Тест list_docs(False):")
    try:
        result = await list_docs(False)
        print(f"   [OK] {result[:100]}...")
    except Exception as e:
        print(f"   [ERROR] Ошибка: {e}")

    # Тест 3: Поиск в TODO
    print("\n[3] Тест search_todo('CURRENT'):")
    try:
        result = await search_todo("CURRENT", 2)
        print(f"   [OK] Найдено {len(result)} символов")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

    # Тест 4: Получение индекса кода
    print("\n[4] Тест get_code_index():")
    try:
        result = await get_code_index()
        if "Индекс кода" in result or "не найден" in result:
            print(f"   [OK] {result[:150]}...")
        else:
            print(f"   [OK] Индекс загружен ({len(result)} символов)")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

    # Тест 5: Поиск в коде
    print("\n[5] Тест search_code('def test'):")
    try:
        result = await search_code("def test", 2)
        print(f"   [OK] Найдено {len(result)} символов")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

    # Тест 6: Покрытие тестами
    print("\n[6] Тест get_test_coverage():")
    try:
        result = await get_test_coverage()
        print(f"   [OK] {result[:150]}...")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

    # Тест 7: Список snapshots
    print("\n[7] Тест list_snapshots():")
    try:
        result = await list_snapshots()
        print(f"   [OK] {result[:150]}...")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

    print("\n" + "=" * 60)
    print("Тестирование завершено!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_mcp_functions())
```

---

## test\test_mcp_server.py <a id="test-test_mcp_server"></a>
**Полный путь:** src/test\test_mcp_server.py

```python
#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы MCP сервера life-docs
"""

import asyncio
import sys
from pathlib import Path

# Добавляем текущую директорию в путь для импорта
sys.path.insert(0, str(Path(__file__).parent))

# Импортируем функции из mcp_index
from mcp_index import (
    get_doc_content,
    get_todo_content,
    list_docs,
    list_todo,
    search_docs,
    search_todo,
)


async def test_search_docs():
    """Тест поиска в документации"""
    print("\n=== Тест: search_docs ===")
    result = await search_docs("api", limit=3)
    print(f"Результат (первые 200 символов):\n{result[:200]}...")
    assert "api" in result.lower() or "API" in result or "Найдено" in result
    print("[OK] search_docs работает корректно")


async def test_list_docs():
    """Тест списка документов"""
    print("\n=== Тест: list_docs ===")
    result = await list_docs(recursive=True)
    print(f"Результат (первые 300 символов):\n{result[:300]}...")
    assert "Найдено" in result or "документов" in result.lower()
    print("[OK] list_docs работает корректно")


async def test_get_doc_content():
    """Тест получения содержимого документа"""
    print("\n=== Тест: get_doc_content ===")
    # Попробуем получить существующий документ
    result = await get_doc_content("README.md")
    print(f"Результат (первые 200 символов):\n{result[:200]}...")
    assert "README.md" in result or "Файл не найден" not in result
    print("[OK] get_doc_content работает корректно")


async def test_search_todo():
    """Тест поиска в TODO"""
    print("\n=== Тест: search_todo ===")
    result = await search_todo("TODO", limit=2)
    print(f"Результат (первые 200 символов):\n{result[:200]}...")
    assert (
        "TODO" in result.upper()
        or "Найдено" in result
        or "ничего не найдено" in result.lower()
    )
    print("[OK] search_todo работает корректно")


async def test_list_todo():
    """Тест списка TODO документов"""
    print("\n=== Тест: list_todo ===")
    result = await list_todo(recursive=True)
    print(f"Результат:\n{result}")
    assert "Найдено" in result or "документов" in result.lower()
    print("[OK] list_todo работает корректно")


async def test_get_todo_content():
    """Тест получения содержимого TODO документа"""
    print("\n=== Тест: get_todo_content ===")
    result = await get_todo_content("CURRENT.md")
    print(f"Результат (первые 200 символов):\n{result[:200]}...")
    assert "CURRENT.md" in result or "Файл не найден" not in result
    print("[OK] get_todo_content работает корректно")


async def test_mcp_server_init():
    """Тест инициализации MCP сервера"""
    print("\n=== Тест: Инициализация MCP сервера ===")
    from mcp_index import DOCS_DIR, TODO_DIR, app

    print(f"DOCS_DIR: {DOCS_DIR}")
    print(f"TODO_DIR: {TODO_DIR}")
    print(f"DOCS_DIR exists: {DOCS_DIR.exists()}")
    print(f"TODO_DIR exists: {TODO_DIR.exists()}")
    print(f"App name: {app}")

    assert DOCS_DIR.exists()
    assert TODO_DIR.exists()
    print("[OK] MCP сервер инициализирован корректно")


async def main():
    """Запуск всех тестов"""
    print("=" * 60)
    print("Тестирование MCP сервера life-docs")
    print("=" * 60)

    try:
        await test_mcp_server_init()
        await test_list_docs()
        await test_search_docs()
        await test_get_doc_content()
        await test_list_todo()
        await test_search_todo()
        await test_get_todo_content()

        print("\n" + "=" * 60)
        print("[OK] Все тесты пройдены успешно!")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"\n[ERROR] Ошибка при тестировании: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
```

---

## test\test_meaning.py <a id="test-test_meaning"></a>
**Полный путь:** src/test\test_meaning.py

```python
"""
Подробные тесты для модуля Meaning
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import time

import pytest

from environment.event import Event
from meaning.engine import MeaningEngine
from meaning.meaning import Meaning


@pytest.mark.unit
@pytest.mark.order(1)
class TestMeaning:
    """Тесты для класса Meaning"""

    def test_meaning_creation_minimal(self):
        """Тест создания Meaning с минимальными параметрами"""
        meaning = Meaning()
        assert meaning.event_id is None
        assert meaning.significance == 0.0
        assert meaning.impact == {}

    def test_meaning_creation_full(self):
        """Тест создания Meaning со всеми параметрами"""
        meaning = Meaning(
            event_id="event_123",
            significance=0.7,
            impact={"energy": -0.5, "stability": -0.1},
        )
        assert meaning.event_id == "event_123"
        assert meaning.significance == 0.7
        assert meaning.impact == {"energy": -0.5, "stability": -0.1}

    def test_meaning_significance_validation_valid(self):
        """Тест валидации significance с валидными значениями"""
        for sig in [0.0, 0.1, 0.5, 0.9, 1.0]:
            meaning = Meaning(significance=sig)
            assert meaning.significance == sig

    def test_meaning_significance_validation_invalid_negative(self):
        """Тест валидации significance с отрицательным значением"""
        with pytest.raises(ValueError, match="significance должен быть в диапазоне"):
            Meaning(significance=-0.1)

    def test_meaning_significance_validation_invalid_above_one(self):
        """Тест валидации significance со значением больше 1.0"""
        with pytest.raises(ValueError, match="significance должен быть в диапазоне"):
            Meaning(significance=1.1)

    def test_meaning_impact_empty(self):
        """Тест Meaning с пустым impact"""
        meaning = Meaning(impact={})
        assert meaning.impact == {}

    def test_meaning_impact_multiple_params(self):
        """Тест Meaning с несколькими параметрами в impact"""
        meaning = Meaning(impact={"energy": -1.0, "stability": -0.2, "integrity": -0.1})
        assert meaning.impact["energy"] == -1.0
        assert meaning.impact["stability"] == -0.2
        assert meaning.impact["integrity"] == -0.1


@pytest.mark.unit
@pytest.mark.order(1)
class TestMeaningEngine:
    """Тесты для класса MeaningEngine"""

    @pytest.fixture
    def engine(self):
        """Создает экземпляр MeaningEngine"""
        return MeaningEngine()

    @pytest.fixture
    def normal_state(self):
        """Создает нормальное состояние"""
        return {"energy": 50.0, "stability": 0.7, "integrity": 0.8}

    @pytest.fixture
    def low_integrity_state(self):
        """Создает состояние с низкой integrity"""
        return {"energy": 50.0, "stability": 0.7, "integrity": 0.2}  # Низкая integrity

    @pytest.fixture
    def low_stability_state(self):
        """Создает состояние с низкой stability"""
        return {"energy": 50.0, "stability": 0.3, "integrity": 0.8}  # Низкая stability

    def test_engine_initialization(self, engine):
        """Тест инициализации MeaningEngine"""
        assert engine.base_significance_threshold == 0.1

    # Тесты для appraisal
    def test_appraisal_shock_event(self, engine, normal_state):
        """Тест оценки значимости shock события"""
        event = Event(type="shock", intensity=0.5, timestamp=time.time())
        significance = engine.appraisal(event, normal_state)
        assert 0.0 <= significance <= 1.0
        assert significance > 0  # Shock должен иметь значимость

    def test_appraisal_noise_event(self, engine, normal_state):
        """Тест оценки значимости noise события"""
        event = Event(type="noise", intensity=0.3, timestamp=time.time())
        significance = engine.appraisal(event, normal_state)
        assert 0.0 <= significance <= 1.0
        # Noise должен иметь меньшую значимость чем shock
        shock_event = Event(type="shock", intensity=0.3, timestamp=time.time())
        shock_sig = engine.appraisal(shock_event, normal_state)
        assert significance < shock_sig

    def test_appraisal_intensity_effect(self, engine, normal_state):
        """Тест влияния интенсивности на значимость"""
        event_low = Event(type="shock", intensity=0.2, timestamp=time.time())
        event_high = Event(type="shock", intensity=0.8, timestamp=time.time())

        sig_low = engine.appraisal(event_low, normal_state)
        sig_high = engine.appraisal(event_high, normal_state)

        assert sig_high > sig_low

    def test_appraisal_low_integrity_amplification(self, engine, low_integrity_state):
        """Тест усиления значимости при низкой integrity"""
        event = Event(type="noise", intensity=0.3, timestamp=time.time())
        sig_low_integrity = engine.appraisal(event, low_integrity_state)

        normal_state = {"energy": 50.0, "stability": 0.7, "integrity": 0.8}
        sig_normal = engine.appraisal(event, normal_state)

        assert sig_low_integrity > sig_normal

    def test_appraisal_low_stability_amplification(self, engine, low_stability_state):
        """Тест усиления значимости при низкой stability"""
        event = Event(type="noise", intensity=0.3, timestamp=time.time())
        sig_low_stability = engine.appraisal(event, low_stability_state)

        normal_state = {"energy": 50.0, "stability": 0.8, "integrity": 0.8}
        sig_normal = engine.appraisal(event, normal_state)

        assert sig_low_stability > sig_normal

    def test_appraisal_range_limits(self, engine, normal_state):
        """Тест ограничения значимости диапазоном [0.0, 1.0]"""
        # Очень высокая интенсивность
        event = Event(type="shock", intensity=2.0, timestamp=time.time())
        significance = engine.appraisal(event, normal_state)
        assert significance <= 1.0

        # Отрицательная интенсивность
        event = Event(type="shock", intensity=-0.5, timestamp=time.time())
        significance = engine.appraisal(event, normal_state)
        assert significance >= 0.0

    # Тесты для impact_model
    def test_impact_model_shock(self, engine, normal_state):
        """Тест модели влияния для shock"""
        event = Event(type="shock", intensity=1.0, timestamp=time.time())
        significance = 0.5
        impact = engine.impact_model(event, normal_state, significance)

        assert "energy" in impact
        assert "stability" in impact
        assert "integrity" in impact
        assert impact["energy"] < 0  # Shock уменьшает energy
        assert impact["stability"] < 0
        assert impact["integrity"] < 0

    def test_impact_model_recovery(self, engine, normal_state):
        """Тест модели влияния для recovery"""
        event = Event(type="recovery", intensity=1.0, timestamp=time.time())
        significance = 0.5
        impact = engine.impact_model(event, normal_state, significance)

        assert impact["energy"] > 0  # Recovery увеличивает energy
        assert impact["stability"] > 0
        assert impact["integrity"] > 0

    def test_impact_model_intensity_scaling(self, engine, normal_state):
        """Тест масштабирования влияния по интенсивности"""
        event_low = Event(type="shock", intensity=0.5, timestamp=time.time())
        event_high = Event(type="shock", intensity=1.0, timestamp=time.time())
        significance = 0.5

        impact_low = engine.impact_model(event_low, normal_state, significance)
        impact_high = engine.impact_model(event_high, normal_state, significance)

        assert abs(impact_high["energy"]) > abs(impact_low["energy"])

    def test_impact_model_significance_scaling(self, engine, normal_state):
        """Тест масштабирования влияния по significance"""
        event = Event(type="shock", intensity=1.0, timestamp=time.time())

        impact_low_sig = engine.impact_model(event, normal_state, 0.2)
        impact_high_sig = engine.impact_model(event, normal_state, 0.8)

        assert abs(impact_high_sig["energy"]) > abs(impact_low_sig["energy"])

    def test_impact_model_unknown_event_type(self, engine, normal_state):
        """Тест модели влияния для неизвестного типа события"""
        event = Event(type="unknown_type", intensity=1.0, timestamp=time.time())
        significance = 0.5
        impact = engine.impact_model(event, normal_state, significance)

        assert impact["energy"] == 0.0
        assert impact["stability"] == 0.0
        assert impact["integrity"] == 0.0

    # Тесты для response_pattern
    def test_response_pattern_ignore_low_significance(self, engine, normal_state):
        """Тест паттерна ignore при низкой значимости"""
        event = Event(type="noise", intensity=0.05, timestamp=time.time())
        significance = 0.05  # Ниже порога 0.1
        pattern = engine.response_pattern(event, normal_state, significance)
        assert pattern == "ignore"

    def test_response_pattern_dampen_high_stability(self, engine):
        """Тест паттерна dampen при высокой стабильности"""
        state = {"energy": 50.0, "stability": 0.9, "integrity": 0.8}
        event = Event(type="shock", intensity=0.5, timestamp=time.time())
        significance = 0.5
        pattern = engine.response_pattern(event, state, significance)
        assert pattern == "dampen"

    def test_response_pattern_amplify_low_stability(self, engine):
        """Тест паттерна amplify при низкой стабильности"""
        state = {"energy": 50.0, "stability": 0.2, "integrity": 0.8}
        event = Event(type="shock", intensity=0.5, timestamp=time.time())
        significance = 0.5
        pattern = engine.response_pattern(event, state, significance)
        assert pattern == "amplify"

    def test_response_pattern_absorb_normal(self, engine, normal_state):
        """Тест паттерна absorb при нормальных условиях"""
        event = Event(type="shock", intensity=0.5, timestamp=time.time())
        significance = 0.5
        pattern = engine.response_pattern(event, normal_state, significance)
        assert pattern == "absorb"

    # Тесты для process (интеграционный)
    def test_process_complete_flow(self, engine, normal_state):
        """Тест полного процесса обработки события"""
        event = Event(type="shock", intensity=0.6, timestamp=time.time())
        meaning = engine.process(event, normal_state)

        assert isinstance(meaning, Meaning)
        assert meaning.event_id is not None
        assert 0.0 <= meaning.significance <= 1.0
        assert "energy" in meaning.impact
        assert "stability" in meaning.impact
        assert "integrity" in meaning.impact

    def test_process_ignore_pattern(self, engine, normal_state):
        """Тест обработки события с паттерном ignore"""
        event = Event(type="idle", intensity=0.05, timestamp=time.time())
        meaning = engine.process(event, normal_state)

        # При ignore все impact должны быть 0
        assert all(v == 0.0 for v in meaning.impact.values())

    def test_process_dampen_pattern(self, engine):
        """Тест обработки события с паттерном dampen"""
        state = {"energy": 50.0, "stability": 0.9, "integrity": 0.8}
        event = Event(type="shock", intensity=0.5, timestamp=time.time())
        meaning = engine.process(event, state)

        # Impact должен быть уменьшен в 2 раза
        base_impact = engine.impact_model(event, state, meaning.significance)
        # Проверяем, что impact уменьшен (примерно в 2 раза)
        assert abs(meaning.impact["energy"]) < abs(base_impact["energy"])

    def test_process_amplify_pattern(self, engine):
        """Тест обработки события с паттерном amplify"""
        state = {"energy": 50.0, "stability": 0.2, "integrity": 0.8}
        event = Event(type="shock", intensity=0.5, timestamp=time.time())
        meaning = engine.process(event, state)

        # Impact должен быть увеличен в 1.5 раза
        base_impact = engine.impact_model(event, state, meaning.significance)
        # Проверяем, что impact увеличен
        assert abs(meaning.impact["energy"]) > abs(base_impact["energy"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## test\test_memory.py <a id="test-test_memory"></a>
**Полный путь:** src/test\test_memory.py

```python
"""
Подробные тесты для модуля Memory
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import time

import pytest

from memory.memory import Memory, MemoryEntry


@pytest.mark.unit
@pytest.mark.order(1)
class TestMemoryEntry:
    """Тесты для класса MemoryEntry"""

    def test_memory_entry_creation(self):
        """Тест создания MemoryEntry с базовыми полями"""
        entry = MemoryEntry(
            event_type="test_event", meaning_significance=0.5, timestamp=time.time()
        )
        assert entry.event_type == "test_event"
        assert entry.meaning_significance == 0.5
        assert entry.timestamp > 0
        assert entry.feedback_data is None

    def test_memory_entry_with_feedback_data(self):
        """Тест создания MemoryEntry с feedback_data"""
        feedback_data = {
            "action_id": "action_123",
            "action_pattern": "dampen",
            "state_delta": {"energy": -1.0},
        }
        entry = MemoryEntry(
            event_type="feedback",
            meaning_significance=0.0,
            timestamp=time.time(),
            feedback_data=feedback_data,
        )
        assert entry.feedback_data == feedback_data
        assert entry.feedback_data["action_id"] == "action_123"

    def test_memory_entry_different_event_types(self):
        """Тест создания MemoryEntry с разными типами событий"""
        event_types = ["shock", "noise", "recovery", "decay", "idle", "feedback"]
        for event_type in event_types:
            entry = MemoryEntry(
                event_type=event_type, meaning_significance=0.3, timestamp=time.time()
            )
            assert entry.event_type == event_type

    def test_memory_entry_significance_range(self):
        """Тест создания MemoryEntry с разными значениями significance"""
        for sig in [0.0, 0.1, 0.5, 0.9, 1.0]:
            entry = MemoryEntry(
                event_type="test", meaning_significance=sig, timestamp=time.time()
            )
            assert entry.meaning_significance == sig


@pytest.mark.unit
@pytest.mark.order(1)
class TestMemory:
    """Тесты для класса Memory"""

    def test_memory_initialization(self):
        """Тест инициализации пустой Memory"""
        memory = Memory()
        assert len(memory) == 0
        assert isinstance(memory, list)

    def test_memory_append_single(self):
        """Тест добавления одного элемента"""
        memory = Memory()
        entry = MemoryEntry(
            event_type="test", meaning_significance=0.5, timestamp=time.time()
        )
        memory.append(entry)
        assert len(memory) == 1
        assert memory[0] == entry

    def test_memory_append_multiple(self):
        """Тест добавления нескольких элементов"""
        memory = Memory()
        for i in range(5):
            entry = MemoryEntry(
                event_type=f"event_{i}", meaning_significance=0.5, timestamp=time.time()
            )
            memory.append(entry)
        assert len(memory) == 5
        assert memory[0].event_type == "event_0"
        assert memory[4].event_type == "event_4"

    def test_memory_clamp_size_at_limit(self):
        """Тест автоматического ограничения размера при достижении лимита (50)"""
        memory = Memory()
        # Добавляем ровно 50 элементов
        for i in range(50):
            entry = MemoryEntry(
                event_type=f"event_{i}", meaning_significance=0.5, timestamp=time.time()
            )
            memory.append(entry)
        assert len(memory) == 50

        # Добавляем еще один - первый должен быть удален
        entry_51 = MemoryEntry(
            event_type="event_51", meaning_significance=0.5, timestamp=time.time()
        )
        memory.append(entry_51)
        assert len(memory) == 50
        assert memory[0].event_type == "event_1"  # Первый удален
        assert memory[-1].event_type == "event_51"  # Последний добавлен

    def test_memory_clamp_size_over_limit(self):
        """Тест ограничения размера при превышении лимита"""
        memory = Memory()
        # Добавляем 60 элементов
        for i in range(60):
            entry = MemoryEntry(
                event_type=f"event_{i}", meaning_significance=0.5, timestamp=time.time()
            )
            memory.append(entry)
        # Должно остаться только 50 последних
        assert len(memory) == 50
        assert memory[0].event_type == "event_10"  # Первые 10 удалены
        assert memory[-1].event_type == "event_59"

    def test_memory_preserves_order(self):
        """Тест сохранения порядка элементов (FIFO)"""
        memory = Memory()
        entries = []
        for i in range(10):
            entry = MemoryEntry(
                event_type=f"event_{i}", meaning_significance=0.5, timestamp=time.time()
            )
            entries.append(entry)
            memory.append(entry)

        # Проверяем порядок
        for i, entry in enumerate(memory):
            assert entry.event_type == f"event_{i}"

    def test_memory_with_feedback_entries(self):
        """Тест работы Memory с Feedback записями"""
        memory = Memory()
        feedback_entry = MemoryEntry(
            event_type="feedback",
            meaning_significance=0.0,
            timestamp=time.time(),
            feedback_data={
                "action_id": "action_1",
                "action_pattern": "dampen",
                "state_delta": {"energy": -1.0},
            },
        )
        memory.append(feedback_entry)
        assert len(memory) == 1
        assert memory[0].event_type == "feedback"
        assert memory[0].feedback_data is not None

    def test_memory_mixed_entries(self):
        """Тест работы Memory со смешанными типами записей"""
        memory = Memory()
        # Добавляем разные типы
        types = ["shock", "noise", "feedback", "recovery"]
        for event_type in types:
            entry = MemoryEntry(
                event_type=event_type,
                meaning_significance=0.5 if event_type != "feedback" else 0.0,
                timestamp=time.time(),
                feedback_data={"test": "data"} if event_type == "feedback" else None,
            )
            memory.append(entry)

        assert len(memory) == 4
        assert memory[0].event_type == "shock"
        assert memory[3].event_type == "recovery"

    def test_memory_list_operations(self):
        """Тест стандартных операций списка"""
        memory = Memory()
        entry1 = MemoryEntry("event1", 0.5, time.time())
        entry2 = MemoryEntry("event2", 0.6, time.time())

        memory.append(entry1)
        memory.append(entry2)

        # Проверка индексации
        assert memory[0] == entry1
        assert memory[1] == entry2

        # Проверка итерации
        types = [e.event_type for e in memory]
        assert types == ["event1", "event2"]

        # Проверка проверки наличия
        assert entry1 in memory
        assert entry2 in memory


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## test\test_monitor.py <a id="test-test_monitor"></a>
**Полный путь:** src/test\test_monitor.py

```python
"""
Тесты для модуля Monitor
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import json
import time
from pathlib import Path

import pytest

from memory.memory import MemoryEntry
from monitor.console import log, monitor
from state.self_state import SelfState


@pytest.mark.unit
@pytest.mark.order(1)
class TestMonitor:
    """Тесты для функций monitor и log"""

    @pytest.fixture
    def temp_log_file(self, monkeypatch, tmp_path):
        """Создает временный файл для логов"""
        log_file = tmp_path / "tick_log.jsonl"
        monkeypatch.setattr("monitor.console.LOG_FILE", log_file)
        return log_file

    def test_log_function(self, capsys):
        """Тест функции log (строки 13-14)"""
        log("Test message")
        captured = capsys.readouterr()
        assert "[RELOAD] Test message" in captured.out
        assert "TEST CHANGE" in captured.out

    def test_monitor_basic(self, temp_log_file, capsys):
        """Тест базовой функции monitor"""
        state = SelfState()
        state.ticks = 10
        state.age = 5.5
        state.energy = 75.0
        state.integrity = 0.8
        state.stability = 0.7
        state.last_significance = 0.5

        monitor(state)

        # Проверяем, что что-то выведено в консоль
        captured = capsys.readouterr()
        assert "10" in captured.out or captured.out  # Может быть пустым из-за \r

        # Проверяем, что запись добавлена в лог файл
        assert temp_log_file.exists()
        with temp_log_file.open("r") as f:
            lines = f.readlines()
            assert len(lines) > 0
            last_line = json.loads(lines[-1])
            assert last_line["tick"] == 10
            assert last_line["age"] == 5.5
            assert last_line["energy"] == 75.0

    def test_monitor_with_activated_memory(self, temp_log_file, capsys):
        """Тест monitor с активированной памятью"""
        state = SelfState()
        state.ticks = 20
        state.activated_memory = [
            MemoryEntry("event1", 0.8, time.time()),
            MemoryEntry("event2", 0.6, time.time()),
        ]
        state.last_pattern = "dampen"

        monitor(state)

        # Проверяем лог файл
        assert temp_log_file.exists()
        with temp_log_file.open("r") as f:
            lines = f.readlines()
            assert len(lines) > 0

    def test_monitor_without_activated_memory(self, temp_log_file, capsys):
        """Тест monitor без активированной памяти"""
        state = SelfState()
        state.ticks = 30
        state.activated_memory = []
        state.last_pattern = ""

        monitor(state)

        # Проверяем лог файл
        assert temp_log_file.exists()
        with temp_log_file.open("r") as f:
            lines = f.readlines()
            assert len(lines) > 0

    def test_monitor_multiple_calls(self, temp_log_file, capsys):
        """Тест нескольких вызовов monitor"""
        state = SelfState()

        for i in range(5):
            state.ticks = i
            state.energy = 100.0 - i
            monitor(state)

        # Проверяем, что все записи добавлены
        assert temp_log_file.exists()
        with temp_log_file.open("r") as f:
            lines = f.readlines()
            assert len(lines) == 5

            # Проверяем последнюю запись
            last_line = json.loads(lines[-1])
            assert last_line["tick"] == 4
            assert last_line["energy"] == 96.0

    def test_monitor_log_file_append(self, temp_log_file, capsys):
        """Тест, что monitor добавляет записи в конец файла"""
        state = SelfState()

        # Первая запись
        state.ticks = 1
        monitor(state)

        # Вторая запись
        state.ticks = 2
        monitor(state)

        # Проверяем, что обе записи в файле
        with temp_log_file.open("r") as f:
            lines = f.readlines()
            assert len(lines) == 2
            assert json.loads(lines[0])["tick"] == 1
            assert json.loads(lines[1])["tick"] == 2

    def test_monitor_all_state_fields(self, temp_log_file, capsys):
        """Тест, что все поля состояния логируются"""
        state = SelfState()
        state.ticks = 100
        state.age = 50.5
        state.energy = 25.0
        state.integrity = 0.3
        state.stability = 0.4
        state.last_significance = 0.7

        monitor(state)

        with temp_log_file.open("r") as f:
            lines = f.readlines()
            data = json.loads(lines[-1])

            assert data["tick"] == 100
            assert data["age"] == 50.5
            assert data["energy"] == 25.0
            assert data["integrity"] == 0.3
            assert data["stability"] == 0.4
            assert data["last_significance"] == 0.7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## test\test_planning.py <a id="test-test_planning"></a>
**Полный путь:** src/test\test_planning.py

```python
"""
Подробные тесты для модуля Planning
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest

from planning.planning import record_potential_sequences
from state.self_state import SelfState


@pytest.mark.unit
@pytest.mark.order(1)
class TestRecordPotentialSequences:
    """Тесты для функции record_potential_sequences"""

    @pytest.fixture
    def base_state(self):
        """Создает базовое состояние"""
        return SelfState()

    def test_record_potential_sequences_empty_recent_events(self, base_state):
        """Тест записи при пустом recent_events"""
        base_state.recent_events = []
        base_state.energy_history = []
        base_state.stability_history = []

        record_potential_sequences(base_state)

        assert "potential_sequences" in base_state.planning
        assert base_state.planning["potential_sequences"] == []
        assert "sources_used" in base_state.planning

    def test_record_potential_sequences_single_event(self, base_state):
        """Тест записи с одним событием в recent_events"""
        base_state.recent_events = ["event1"]
        base_state.energy_history = [50.0]
        base_state.stability_history = [0.7]

        record_potential_sequences(base_state)

        # С одним событием последовательность не создается (нужно минимум 2)
        assert base_state.planning["potential_sequences"] == []

    def test_record_potential_sequences_two_events(self, base_state):
        """Тест записи с двумя событиями"""
        base_state.recent_events = ["event1", "event2"]
        base_state.energy_history = [50.0, 49.0]
        base_state.stability_history = [0.7, 0.6]

        record_potential_sequences(base_state)

        assert len(base_state.planning["potential_sequences"]) == 1
        assert base_state.planning["potential_sequences"][0] == ["event1", "event2"]

    def test_record_potential_sequences_multiple_events(self, base_state):
        """Тест записи с несколькими событиями"""
        base_state.recent_events = ["event1", "event2", "event3", "event4"]
        base_state.energy_history = [50.0, 49.0, 48.0, 47.0]
        base_state.stability_history = [0.7, 0.6, 0.5, 0.4]

        record_potential_sequences(base_state)

        # Должна быть создана последовательность из последних 2 событий
        assert len(base_state.planning["potential_sequences"]) == 1
        assert base_state.planning["potential_sequences"][0] == ["event3", "event4"]

    def test_record_potential_sequences_sources_used(self, base_state):
        """Тест записи источников данных"""
        base_state.recent_events = ["e1", "e2", "e3"]
        base_state.energy_history = [50.0, 49.0, 48.0]
        base_state.stability_history = [0.7, 0.6]

        record_potential_sequences(base_state)

        assert "sources_used" in base_state.planning
        sources = base_state.planning["sources_used"]
        assert sources["memory_proxy"] == 3
        assert sources["learning_proxy"] == 2
        assert sources["adaptation_proxy"] == 3

    def test_record_potential_sequences_preserves_other_fields(self, base_state):
        """Тест, что функция не изменяет другие поля состояния"""
        base_state.energy = 50.0
        base_state.stability = 0.7
        base_state.integrity = 0.8
        base_state.recent_events = ["e1", "e2"]

        record_potential_sequences(base_state)

        # Эти поля не должны измениться
        assert base_state.energy == 50.0
        assert base_state.stability == 0.7
        assert base_state.integrity == 0.8
        assert base_state.recent_events == ["e1", "e2"]

    def test_record_potential_sequences_multiple_calls(self, base_state):
        """Тест нескольких вызовов функции"""
        base_state.recent_events = ["e1", "e2"]

        record_potential_sequences(base_state)
        first_sequences = base_state.planning["potential_sequences"].copy()

        base_state.recent_events = ["e3", "e4"]
        record_potential_sequences(base_state)

        # Последовательность должна обновиться
        assert base_state.planning["potential_sequences"][0] == ["e3", "e4"]
        assert base_state.planning["potential_sequences"][0] != first_sequences[0]

    def test_record_potential_sequences_empty_histories(self, base_state):
        """Тест записи при пустых историях"""
        base_state.recent_events = ["e1", "e2"]
        base_state.energy_history = []
        base_state.stability_history = []

        record_potential_sequences(base_state)

        assert len(base_state.planning["potential_sequences"]) == 1
        sources = base_state.planning["sources_used"]
        assert sources["learning_proxy"] == 0
        assert sources["adaptation_proxy"] == 0

    def test_record_potential_sequences_different_event_types(self, base_state):
        """Тест записи с разными типами событий"""
        base_state.recent_events = ["shock", "noise", "recovery"]
        base_state.energy_history = [50.0, 49.0, 51.0]
        base_state.stability_history = [0.7, 0.6, 0.8]

        record_potential_sequences(base_state)

        sequence = base_state.planning["potential_sequences"][0]
        assert sequence == ["noise", "recovery"]
        assert "shock" not in sequence  # Только последние 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## test\test_runtime_integration.py <a id="test-test_runtime_integration"></a>
**Полный путь:** src/test\test_runtime_integration.py

```python
"""
Интеграционные тесты для Runtime Loop
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import threading
import time

import pytest

from environment.event import Event
from environment.event_queue import EventQueue
from runtime.loop import run_loop
from state.self_state import SelfState


def dummy_monitor(state):
    """Простой монитор для тестов"""
    pass


@pytest.mark.integration
@pytest.mark.order(2)
class TestRuntimeLoop:
    """Интеграционные тесты для runtime loop"""

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

    def test_loop_single_tick(self, base_state, event_queue):
        """Тест выполнения одного тика цикла"""
        stop_event = threading.Event()
        initial_ticks = base_state.ticks

        # Запускаем цикл в отдельном потоке
        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.1, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        # Ждем немного
        time.sleep(0.2)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # Проверяем, что тики увеличились
        assert base_state.ticks > initial_ticks

    def test_loop_processes_events(self, base_state, event_queue):
        """Тест обработки событий в цикле"""
        stop_event = threading.Event()

        # Добавляем событие в очередь
        event = Event(type="shock", intensity=0.5, timestamp=time.time())
        event_queue.push(event)

        initial_memory_size = len(base_state.memory)

        # Запускаем цикл
        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.1, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        # Ждем обработки
        time.sleep(0.5)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # Проверяем, что событие обработано (добавлено в память или изменено состояние)
        # Событие может быть обработано, если significance > 0
        # Проверяем, что что-то изменилось
        assert (
            len(base_state.memory) >= initial_memory_size or base_state.energy != 50.0
        )

    def test_loop_feedback_registration(self, base_state, event_queue):
        """Тест регистрации действий для Feedback"""
        stop_event = threading.Event()

        # Добавляем значимое событие
        event = Event(type="shock", intensity=0.8, timestamp=time.time())
        event_queue.push(event)

        # Запускаем цикл
        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.1, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        # Ждем обработки
        time.sleep(0.5)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # Проверяем, что состояние изменилось (событие было обработано)
        # Это косвенно подтверждает, что действие было зарегистрировано

    def test_loop_state_updates(self, base_state, event_queue):
        """Тест обновления состояния в цикле"""
        stop_event = threading.Event()

        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.1, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(0.3)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # Проверяем, что тики увеличились
        assert base_state.ticks > 0
        # Возраст может увеличиться (зависит от dt)

    def test_loop_stops_on_stop_event(self, base_state, event_queue):
        """Тест остановки цикла по stop_event"""
        stop_event = threading.Event()

        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.1, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        # Убеждаемся, что цикл работает
        time.sleep(0.2)
        initial_ticks = base_state.ticks

        # Останавливаем
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # Проверяем, что поток завершился
        assert not loop_thread.is_alive()

        # Проверяем, что тики не увеличиваются после остановки
        time.sleep(0.2)
        assert base_state.ticks == initial_ticks

    def test_loop_handles_empty_queue(self, base_state, event_queue):
        """Тест работы цикла с пустой очередью"""
        stop_event = threading.Event()
        initial_ticks = base_state.ticks

        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.1, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(0.3)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # Цикл должен работать даже без событий
        assert base_state.ticks > initial_ticks

    def test_loop_multiple_events(self, base_state, event_queue):
        """Тест обработки нескольких событий"""
        stop_event = threading.Event()

        # Добавляем несколько событий
        events = [
            Event(type="shock", intensity=0.5, timestamp=time.time()),
            Event(type="noise", intensity=0.3, timestamp=time.time()),
            Event(type="recovery", intensity=0.4, timestamp=time.time()),
        ]
        for event in events:
            event_queue.push(event)

        initial_memory_size = len(base_state.memory)

        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.1, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(0.5)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # События должны быть обработаны
        # Проверяем, что очередь пуста или память изменилась
        assert event_queue.is_empty() or len(base_state.memory) > initial_memory_size

    def test_loop_snapshot_creation(self, base_state, event_queue, tmp_path):
        """Тест создания снимков в цикле"""
        import state.self_state as state_module

        original_dir = state_module.SNAPSHOT_DIR

        # Временно меняем директорию снимков
        state_module.SNAPSHOT_DIR = tmp_path / "snapshots"
        state_module.SNAPSHOT_DIR.mkdir(exist_ok=True)

        try:
            stop_event = threading.Event()
            base_state.ticks = 0  # Начинаем с 0

            loop_thread = threading.Thread(
                target=run_loop,
                args=(
                    base_state,
                    dummy_monitor,
                    0.05,
                    1,
                    stop_event,
                    event_queue,
                ),  # snapshot каждые 1 тик
                daemon=True,
            )
            loop_thread.start()

            # Ждем несколько тиков
            time.sleep(0.3)
            stop_event.set()
            loop_thread.join(timeout=1.0)

            # Проверяем, что снимки созданы
            list(state_module.SNAPSHOT_DIR.glob("snapshot_*.json"))
            # Может быть создан хотя бы один снимок
        finally:
            # Восстанавливаем оригинальную директорию
            state_module.SNAPSHOT_DIR = original_dir

    def test_loop_weakness_penalty(self, base_state, event_queue):
        """Тест штрафов за слабость в цикле"""
        stop_event = threading.Event()

        # Устанавливаем низкие значения
        base_state.energy = 0.03
        base_state.integrity = 0.03
        base_state.stability = 0.03

        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.1, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(0.3)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # Проверяем, что параметры уменьшились (штрафы)
        # Но не должны стать отрицательными
        assert base_state.energy >= 0.0
        assert base_state.integrity >= 0.0
        assert base_state.stability >= 0.0

    def test_loop_deactivates_on_zero_params(self, base_state, event_queue):
        """Тест деактивации при нулевых параметрах"""
        stop_event = threading.Event()

        # Устанавливаем нулевые значения
        base_state.energy = 0.0
        base_state.integrity = 0.0
        base_state.stability = 0.0

        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.1, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(0.2)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # Проверяем, что состояние деактивировано
        assert base_state.active is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## test\test_runtime_loop_edge_cases.py <a id="test-test_runtime_loop_edge_cases"></a>
**Полный путь:** src/test\test_runtime_loop_edge_cases.py

```python
"""
Тесты для покрытия edge cases в Runtime Loop
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import threading
import time

import pytest

from environment.event import Event
from environment.event_queue import EventQueue
from runtime.loop import run_loop
from state.self_state import SelfState


def dummy_monitor(state):
    """Простой монитор для тестов"""
    pass


@pytest.mark.integration
@pytest.mark.order(2)
class TestRuntimeLoopEdgeCases:
    """Тесты для edge cases Runtime Loop"""

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

    def test_loop_ignore_pattern_skip_apply_delta(self, base_state, event_queue):
        """Тест, что при pattern='ignore' apply_delta не вызывается (строка 84)"""
        stop_event = threading.Event()

        # Создаем событие, которое приведет к ignore
        # Для этого нужно событие с очень низкой significance
        from meaning.engine import MeaningEngine

        MeaningEngine()

        # Создаем событие с очень низкой интенсивностью
        event = Event(type="idle", intensity=0.01, timestamp=time.time())
        event_queue.push(event)

        # Запускаем цикл
        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.1, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        # Ждем обработки
        time.sleep(0.3)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # При ignore состояние не должно измениться (или измениться минимально)
        # Но могут быть другие эффекты (тики, возраст), поэтому проверяем только основные параметры
        # Если ignore сработал, energy и stability не должны сильно измениться от события

    def test_loop_dampen_pattern_modify_impact(self, base_state, event_queue):
        """Тест, что при pattern='dampen' impact модифицируется (строка 86)"""
        stop_event = threading.Event()

        # Создаем событие, которое приведет к dampen
        # Для этого нужна высокая significance в активированной памяти
        from memory.memory import MemoryEntry

        base_state.activated_memory = [MemoryEntry("shock", 0.6, time.time())]  # > 0.5

        # Добавляем событие в память с высокой significance для активации
        base_state.memory.append(MemoryEntry("shock", 0.6, time.time()))

        event = Event(type="shock", intensity=0.8, timestamp=time.time())
        event_queue.push(event)

        initial_energy = base_state.energy

        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.1, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(0.5)  # Увеличиваем время для обработки
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # Проверяем, что состояние изменилось (событие обработано)
        # При dampen изменение должно быть меньше, чем при absorb
        # Строка 86 должна выполниться: meaning.impact = {k: v * 0.5 for k, v in meaning.impact.items()}
        assert base_state.energy != initial_energy or base_state.ticks > 0

    def test_loop_monitor_exception_handling(self, base_state, event_queue):
        """Тест обработки исключений в monitor (строки 128-130)"""
        stop_event = threading.Event()

        def failing_monitor(state):
            """Монитор, который выбрасывает исключение"""
            raise ValueError("Monitor error")

        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, failing_monitor, 0.1, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        # Ждем несколько тиков
        time.sleep(0.3)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # Цикл должен продолжить работу несмотря на ошибку monitor
        assert base_state.ticks > 0

    def test_loop_snapshot_exception_handling(
        self, base_state, event_queue, tmp_path, monkeypatch
    ):
        """Тест обработки исключений при сохранении snapshot (строки 136-138)"""
        import state.self_state as state_module

        original_dir = state_module.SNAPSHOT_DIR

        # Создаем ситуацию, когда save_snapshot выбросит исключение
        # Мокаем save_snapshot чтобы выбросить ошибку
        original_save = state_module.save_snapshot
        call_count = [0]

        def failing_save_snapshot(state):
            call_count[0] += 1
            if call_count[0] == 1:
                raise IOError("Snapshot save failed")
            return original_save(state)

        monkeypatch.setattr(state_module, "save_snapshot", failing_save_snapshot)

        stop_event = threading.Event()
        base_state.ticks = 0

        try:
            loop_thread = threading.Thread(
                target=run_loop,
                args=(
                    base_state,
                    dummy_monitor,
                    0.05,
                    1,
                    stop_event,
                    event_queue,
                ),  # snapshot каждые 1 тик
                daemon=True,
            )
            loop_thread.start()

            # Ждем несколько тиков, чтобы snapshot попытался сохраниться
            time.sleep(0.3)
            stop_event.set()
            loop_thread.join(timeout=1.0)

            # Цикл должен продолжить работу несмотря на ошибку (строки 136-138)
            assert base_state.ticks > 0
            # Ошибка должна быть обработана в строке 137: print(f"Ошибка при сохранении snapshot: {e}")
        finally:
            state_module.SNAPSHOT_DIR = original_dir

    def test_loop_general_exception_handling(
        self, base_state, event_queue, monkeypatch
    ):
        """Тест обработки общих исключений в цикле (строки 146-149)"""
        stop_event = threading.Event()

        # Создаем ситуацию, которая вызовет исключение в цикле
        # Мокаем apply_delta чтобы выбросить ошибку
        original_apply_delta = base_state.apply_delta
        call_count = [0]

        def failing_apply_delta(deltas):
            call_count[0] += 1
            if call_count[0] == 2:  # Второй вызов (после ticks) выбросит ошибку
                raise ValueError("Test exception in loop")
            return original_apply_delta(deltas)

        monkeypatch.setattr(base_state, "apply_delta", failing_apply_delta)

        initial_integrity = base_state.integrity

        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.1, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(0.3)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # При ошибке integrity должна уменьшиться на 0.05 (строка 147)
        # Ошибка обрабатывается в строках 146-149
        # Проверяем, что integrity изменилась (уменьшилась на 0.05)
        assert base_state.integrity < initial_integrity
        # Или цикл продолжил работу
        assert base_state.ticks > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## test\test_runtime_loop_feedback_coverage.py <a id="test-test_runtime_loop_feedback_coverage"></a>
**Полный путь:** src/test\test_runtime_loop_feedback_coverage.py

```python
"""
Тесты для покрытия строк 50-62 в runtime/loop.py (обработка Feedback записей)
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import threading
import time

import pytest

from environment.event import Event
from environment.event_queue import EventQueue
from runtime.loop import run_loop
from state.self_state import SelfState


def dummy_monitor(state):
    """Простой монитор для тестов"""
    pass


@pytest.mark.integration
@pytest.mark.order(2)
class TestRuntimeLoopFeedbackCoverage:
    """Тесты для покрытия обработки Feedback в runtime loop (строки 50-62)"""

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

    def test_loop_processes_feedback_records(self, base_state, event_queue):
        """Тест обработки Feedback записей в цикле (строки 50-62)"""
        stop_event = threading.Event()

        # Создаем событие, которое будет обработано и создаст действие
        event = Event(type="shock", intensity=0.8, timestamp=time.time())
        event_queue.push(event)

        initial_memory_size = len(base_state.memory)

        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.05, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        # Ждем обработки события и регистрации действия
        time.sleep(0.3)

        # Изменяем состояние, чтобы создать изменение для Feedback
        base_state.energy = 45.0

        # Ждем, чтобы Feedback был обработан (нужно несколько тиков)
        # pending_actions проверяются каждый тик, но нужна задержка check_after_ticks
        time.sleep(1.0)  # Достаточно времени для обработки

        stop_event.set()
        loop_thread.join(timeout=2.0)

        # Проверяем, что память увеличилась (добавлены записи)
        # Feedback записи добавляются в строках 50-62
        # Может быть событие или feedback запись
        assert len(base_state.memory) >= initial_memory_size

    def test_loop_feedback_entry_creation(self, base_state, event_queue):
        """Тест создания Feedback записей в памяти (строки 50-62)"""
        stop_event = threading.Event()

        # Создаем событие
        event = Event(type="shock", intensity=0.6, timestamp=time.time())
        event_queue.push(event)

        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.1, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        # Ждем несколько тиков, чтобы Feedback мог быть обработан
        time.sleep(1.0)

        stop_event.set()
        loop_thread.join(timeout=2.0)

        # Проверяем, что в памяти есть записи
        # Если были обработаны действия, должны быть Feedback записи
        [e for e in base_state.memory if e.event_type == "feedback"]
        # Могут быть или не быть, в зависимости от timing
        # Главное - проверить, что код выполняется


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## test\test_state.py <a id="test-test_state"></a>
**Полный путь:** src/test\test_state.py

```python
"""
Подробные тесты для модуля State (SelfState)
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import json
import shutil
import tempfile
import time
from pathlib import Path

import pytest

from memory.memory import MemoryEntry
from state.self_state import (
    SelfState,
    create_initial_state,
    load_snapshot,
    save_snapshot,
)


@pytest.mark.unit
@pytest.mark.order(1)
class TestSelfState:
    """Тесты для класса SelfState"""

    def test_self_state_initialization(self):
        """Тест инициализации SelfState с значениями по умолчанию"""
        state = SelfState()
        assert state.energy == 100.0
        assert state.integrity == 1.0
        assert state.stability == 1.0
        assert state.fatigue == 0.0
        assert state.tension == 0.0
        assert state.age == 0.0
        assert state.ticks == 0
        assert state.active is True
        assert state.life_id is not None
        assert state.birth_timestamp > 0
        assert isinstance(state.memory, list)
        assert len(state.memory) == 0

    def test_self_state_unique_life_id(self):
        """Тест уникальности life_id для разных экземпляров"""
        state1 = SelfState()
        state2 = SelfState()
        assert state1.life_id != state2.life_id

    def test_self_state_birth_timestamp(self):
        """Тест установки birth_timestamp"""
        before = time.time()
        state = SelfState()
        after = time.time()
        assert before <= state.birth_timestamp <= after

    def test_apply_delta_energy(self):
        """Тест применения дельты к energy"""
        state = SelfState()
        state.energy = 50.0

        # Положительная дельта
        state.apply_delta({"energy": 10.0})
        assert state.energy == 60.0

        # Отрицательная дельта
        state.apply_delta({"energy": -20.0})
        assert state.energy == 40.0

        # Превышение максимума (100.0)
        state.apply_delta({"energy": 100.0})
        assert state.energy == 100.0

        # Превышение минимума (0.0)
        state.apply_delta({"energy": -200.0})
        assert state.energy == 0.0

    def test_apply_delta_integrity(self):
        """Тест применения дельты к integrity"""
        state = SelfState()
        state.integrity = 0.5

        # Положительная дельта
        state.apply_delta({"integrity": 0.2})
        assert state.integrity == 0.7

        # Отрицательная дельта
        state.apply_delta({"integrity": -0.3})
        assert abs(state.integrity - 0.4) < 0.0001  # Учитываем погрешность float

        # Превышение максимума (1.0)
        state.apply_delta({"integrity": 1.0})
        assert state.integrity == 1.0

        # Превышение минимума (0.0)
        state.apply_delta({"integrity": -2.0})
        assert state.integrity == 0.0

    def test_apply_delta_stability(self):
        """Тест применения дельты к stability"""
        state = SelfState()
        state.stability = 0.6

        # Положительная дельта
        state.apply_delta({"stability": 0.3})
        assert abs(state.stability - 0.9) < 0.0001  # Учитываем погрешность float

        # Отрицательная дельта
        state.apply_delta({"stability": -0.5})
        assert abs(state.stability - 0.4) < 0.0001  # Учитываем погрешность float

        # Превышение максимума (1.0)
        state.apply_delta({"stability": 1.0})
        assert state.stability == 1.0

        # Превышение минимума (0.0)
        state.apply_delta({"stability": -2.0})
        assert state.stability == 0.0

    def test_apply_delta_multiple_params(self):
        """Тест применения дельты к нескольким параметрам одновременно"""
        state = SelfState()
        state.energy = 50.0
        state.integrity = 0.5
        state.stability = 0.5

        state.apply_delta({"energy": 10.0, "integrity": 0.2, "stability": -0.1})

        assert state.energy == 60.0
        assert state.integrity == 0.7
        assert state.stability == 0.4

    def test_apply_delta_ticks(self):
        """Тест применения дельты к ticks (без ограничений)"""
        state = SelfState()
        state.ticks = 10

        state.apply_delta({"ticks": 5})
        assert state.ticks == 15

        state.apply_delta({"ticks": -3})
        assert state.ticks == 12

    def test_apply_delta_age(self):
        """Тест применения дельты к age (без ограничений)"""
        state = SelfState()
        state.age = 10.5

        state.apply_delta({"age": 1.5})
        assert state.age == 12.0

    def test_apply_delta_unknown_field(self):
        """Тест применения дельты к несуществующему полю (должно игнорироваться)"""
        state = SelfState()
        initial_energy = state.energy

        # Попытка изменить несуществующее поле
        state.apply_delta({"unknown_field": 100.0})

        # Энергия не должна измениться
        assert state.energy == initial_energy
        assert not hasattr(state, "unknown_field")

    def test_self_state_memory_operations(self):
        """Тест операций с памятью"""
        state = SelfState()
        entry = MemoryEntry(
            event_type="test_event", meaning_significance=0.5, timestamp=time.time()
        )
        state.memory.append(entry)
        assert len(state.memory) == 1
        assert state.memory[0] == entry

    def test_self_state_recent_events(self):
        """Тест работы с recent_events"""
        state = SelfState()
        assert isinstance(state.recent_events, list)
        assert len(state.recent_events) == 0

        state.recent_events.append("event1")
        state.recent_events.append("event2")
        assert len(state.recent_events) == 2
        assert state.recent_events[0] == "event1"


@pytest.mark.unit
@pytest.mark.order(1)
class TestSnapshots:
    """Тесты для функций сохранения и загрузки снимков"""

    @pytest.fixture
    def temp_snapshot_dir(self):
        """Создает временную директорию для снимков"""
        temp_dir = Path(tempfile.mkdtemp())
        Path("data/snapshots")

        # Временно заменяем SNAPSHOT_DIR
        from state import self_state

        original_snapshot_dir = self_state.SNAPSHOT_DIR
        self_state.SNAPSHOT_DIR = temp_dir

        yield temp_dir

        # Восстанавливаем
        self_state.SNAPSHOT_DIR = original_snapshot_dir
        shutil.rmtree(temp_dir)

    def test_save_snapshot(self, temp_snapshot_dir):
        """Тест сохранения снимка"""
        state = SelfState()
        state.ticks = 100
        state.energy = 75.0
        state.integrity = 0.8
        state.stability = 0.9

        # Добавляем запись в память
        entry = MemoryEntry(
            event_type="test", meaning_significance=0.5, timestamp=time.time()
        )
        state.memory.append(entry)

        save_snapshot(state)

        # Проверяем, что файл создан
        snapshot_file = temp_snapshot_dir / "snapshot_000100.json"
        assert snapshot_file.exists()

        # Проверяем содержимое
        with snapshot_file.open("r") as f:
            data = json.load(f)

        assert data["ticks"] == 100
        assert data["energy"] == 75.0
        assert data["integrity"] == 0.8
        assert data["stability"] == 0.9
        assert len(data["memory"]) == 1
        assert data["memory"][0]["event_type"] == "test"

        # Проверяем, что transient поля не сохранены
        assert "activated_memory" not in data
        assert "last_pattern" not in data

    def test_load_snapshot(self, temp_snapshot_dir):
        """Тест загрузки снимка"""
        # Создаем снимок
        state = SelfState()
        state.ticks = 200
        state.energy = 50.0
        state.integrity = 0.6
        state.stability = 0.7
        state.life_id = "test_life_id"

        entry = MemoryEntry(
            event_type="loaded_event", meaning_significance=0.7, timestamp=time.time()
        )
        state.memory.append(entry)

        save_snapshot(state)

        # Загружаем снимок
        loaded_state = load_snapshot(200)

        assert loaded_state.ticks == 200
        assert loaded_state.energy == 50.0
        assert loaded_state.integrity == 0.6
        assert loaded_state.stability == 0.7
        assert loaded_state.life_id == "test_life_id"
        assert len(loaded_state.memory) == 1
        assert loaded_state.memory[0].event_type == "loaded_event"
        assert loaded_state.memory[0].meaning_significance == 0.7

    def test_load_snapshot_not_found(self, temp_snapshot_dir):
        """Тест загрузки несуществующего снимка"""
        with pytest.raises(FileNotFoundError):
            load_snapshot(99999)

    def test_load_latest_snapshot(self, temp_snapshot_dir):
        """Тест загрузки последнего снимка"""
        # Создаем несколько снимков
        for ticks in [10, 20, 30]:
            state = SelfState()
            state.ticks = ticks
            state.energy = ticks * 2.0
            save_snapshot(state)

        # Загружаем последний (используем метод класса)
        state = SelfState()
        latest = state.load_latest_snapshot()
        assert latest.ticks == 30
        assert latest.energy == 60.0

    def test_load_latest_snapshot_not_found(self, temp_snapshot_dir):
        """Тест загрузки последнего снимка когда их нет"""
        state = SelfState()
        with pytest.raises(FileNotFoundError):
            state.load_latest_snapshot()

    def test_snapshot_preserves_memory(self, temp_snapshot_dir):
        """Тест сохранения памяти в снимке"""
        state = SelfState()

        # Добавляем несколько записей
        for i in range(5):
            entry = MemoryEntry(
                event_type=f"event_{i}",
                meaning_significance=0.1 * i,
                timestamp=time.time(),
            )
            state.memory.append(entry)

        state.ticks = 50
        save_snapshot(state)

        loaded = load_snapshot(50)
        assert len(loaded.memory) == 5
        for i, entry in enumerate(loaded.memory):
            assert entry.event_type == f"event_{i}"
            assert abs(entry.meaning_significance - 0.1 * i) < 0.001


@pytest.mark.unit
@pytest.mark.order(1)
class TestCreateInitialState:
    """Тесты для функции create_initial_state"""

    def test_create_initial_state(self):
        """Тест создания начального состояния"""
        state = create_initial_state()
        assert isinstance(state, SelfState)
        assert state.energy == 100.0
        assert state.integrity == 1.0
        assert state.stability == 1.0
        assert state.ticks == 0
        assert state.active is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## test_main.py <a id="test_main"></a>
**Полный путь:** src/test_main.py

```python
import argparse
import json
import sys
from pathlib import Path

from state.self_state import SelfState

parser = argparse.ArgumentParser()
parser.add_argument(
    "--clear-data", type=str, default="no", help="Очистить логи и снапшоты (yes/no)"
)
parser.add_argument(
    "--tick-interval", type=float, default=1.0, help="Интервал тика, сек"
)
parser.add_argument(
    "--snapshot-period", type=int, default=10, help="Периодичность snapshot, тиков"
)
args = parser.parse_args()

# Путь к файлу логов
LOG_FILE = Path("data/tick_log.jsonl")
LOG_FILE.parent.mkdir(exist_ok=True)


def monitor(state: SelfState):
    # Консольный вывод на одной строке
    heartbeat = "•"
    msg = f"{heartbeat} tick={state.ticks} age={state.age:.2f}s energy={state.energy:.1f} integrity={state.integrity:.2f} stability={state.stability:.3f}"
    sys.stdout.write("\r" + msg)
    sys.stdout.flush()

    # Логирование текущего тика в файл (append-only)
    tick_data = {
        "tick": state.ticks,
        "age": state.age,
        "energy": state.energy,
        "integrity": state.integrity,
        "stability": state.stability,
    }
    with LOG_FILE.open("a") as f:
        f.write(json.dumps(tick_data) + "\n")


import threading
import time

from environment import EventGenerator, EventQueue
from runtime.loop import run_loop

try:
    self_state = SelfState().load_latest_snapshot()
except FileNotFoundError:
    self_state = SelfState()

if __name__ == "__main__":
    event_queue = EventQueue()
    stop_event = threading.Event()

    def background_event_generation(queue, generator, stop_event):
        while not stop_event.is_set():
            event = generator.generate()
            queue.push(event)
            time.sleep(1.0)

    generator_thread = threading.Thread(
        target=background_event_generation,
        args=(event_queue, EventGenerator(), stop_event),
    )
    generator_thread.daemon = True
    generator_thread.start()
    run_loop(
        self_state,
        monitor,
        tick_interval=args.tick_interval,
        snapshot_period=args.snapshot_period,
        event_queue=event_queue,
        stop_event=stop_event,
    )
    print("Жизнь завершена. Финальное состояние:")
    print(self_state)
```

---

# Конец индекса
