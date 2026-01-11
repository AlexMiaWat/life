import argparse
import glob
import importlib
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from monitor.console import monitor, log
from runtime.loop import run_loop
from monitor.console import monitor
import runtime.loop
import state.self_state
from environment import Event, EventQueue
from colorama import Fore, Style, init
init()

from typing import Any

print(f"[ДИАГ] Тип monitor: {type(monitor).__name__}")
print(f"[ДИАГ] monitor вызываемая функция? {callable(monitor)}")
if hasattr(monitor, '__file__'):
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
    server: Any  # Добавляем, чтобы IDE знала, что у server могут быть кастомные атрибуты

    def do_GET(self):
        if self.path == "/status":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(self.server.self_state).encode())
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
            print(f"[API] Получен POST /event: type='{event_type}', intensity={intensity}")
            event = Event(type=event_type, intensity=intensity, timestamp=timestamp, metadata=metadata)
            self.server.event_queue.push(event)
            print(f"[API] Event PUSHED to queue. Size now: {self.server.event_queue.size()}")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Event accepted")
        except Exception as exc:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(f"Invalid event: {exc}".encode("utf-8"))

    def log_request(self, code, size=-1):
        if self.server.dev_mode:
            print(Fore.CYAN + "═" * 80 + Style.RESET_ALL)
            print(Fore.GREEN + "🟢 ВХОДЯЩИЙ HTTP-ЗАПРОС" + Style.RESET_ALL)
            print(Fore.YELLOW + f"⏰ Время: {self.log_date_time_string()}" + Style.RESET_ALL)
            print(Fore.YELLOW + f"🌐 Клиент IP: {self.client_address[0]}" + Style.RESET_ALL)
            print(Fore.YELLOW + f"📥 Запрос: {self.requestline}" + Style.RESET_ALL)
            print(Fore.MAGENTA + f"✅ Статус ответа: {code}" + Style.RESET_ALL)
            if isinstance(size, (int, float)) and size > 0:
                print(Fore.MAGENTA + f"📊 Размер ответа: {size} байт" + Style.RESET_ALL)
            print(Fore.CYAN + "═" * 80 + Style.RESET_ALL)
            sys.stdout.flush()

def start_api_server(self_state, event_queue, dev_mode):
    global server
    server = StoppableHTTPServer((HOST, PORT), LifeHandler)
    server.self_state = self_state
    server.event_queue = event_queue
    server.dev_mode = dev_mode
    print(f"API server running on http://{HOST}:{PORT}")
    server.serve_forever()

def reloader_thread():
    """
    Отслеживает изменения в исходных файлах проекта и перезагружает их "горячо".
    Перезапускает API сервер при изменении модулей.
    """
    global self_state, server, api_thread, monitor, log, loop_thread, loop_stop, config, event_queue

    # Файлы для отслеживания
    files_to_watch = [
        'src/main_server_api.py',
        'src/monitor/console.py',
        'src/runtime/loop.py',
        'src/state/self_state.py',
        'src/environment/event.py',
        'src/environment/event_queue.py',
        'src/environment/generator.py',
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
            import monitor.console as console_module
            import runtime.loop as loop_module
            import state.self_state as state_module
            import environment.event as event_module
            import environment.event_queue as event_queue_module
            import environment.generator as generator_module
        
            importlib.reload(console_module)
            importlib.reload(loop_module)
            importlib.reload(state_module)
            importlib.reload(event_module)
            importlib.reload(event_queue_module)
            importlib.reload(generator_module)
        
            print(f"[RELOAD DIAG] Reloaded loop_module.run_loop: firstlineno={loop_module.run_loop.__code__.co_firstlineno}, argcount={loop_module.run_loop.__code__.co_argcount}")
            print(f"[RELOAD DIAG] New run_loop code file: {loop_module.run_loop.__code__.co_filename}")
        
            # Обновляем ссылки на функции
            monitor = console_module.monitor
            log = console_module.log
            run_loop = loop_module.run_loop
            self_state = state_module.self_state if hasattr(state_module, 'self_state') else self_state

            # Перезапуск API сервера
            api_thread = threading.Thread(target=start_api_server, args=(self_state, event_queue, True), daemon=True)
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
                args=(self_state, monitor, config['tick_interval'], config['snapshot_period'], loop_stop, event_queue),
                daemon=True
            )
            loop_thread.start()
            log("[RELOAD] New loop started")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--clear-data", type=str, default="no")
    parser.add_argument("--tick-interval", type=float, default=1.0)
    parser.add_argument("--snapshot-period", type=int, default=10)
    parser.add_argument("--dev", action="store_true", help="Enable development mode with auto-reload")
    args = parser.parse_args()
    dev_mode = args.dev
    
    config = {
        'tick_interval': args.tick_interval,
        'snapshot_period': args.snapshot_period
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

    self_state = {
        'alive': True,
        'ticks': 0,
        'age': 0.0,
        'energy': 100.0,
        'stability': 1.0,
        'integrity': 1.0,
        'recent_events': [],
        'planning': {},
        'intelligence': {}
    }

    server = None
    api_thread = None
    
    # Инициализация Environment
    event_queue = EventQueue()

    if args.dev:
        log("--dev mode enabled, starting reloader")
        threading.Thread(target=reloader_thread, daemon=True).start()

    # Start API thread
    api_thread = threading.Thread(target=start_api_server, args=(self_state, event_queue, dev_mode), daemon=True)
    api_thread.start()

    # Start loop thread
    loop_stop = threading.Event()
    loop_thread = threading.Thread(
        target=run_loop,
        args=(self_state, monitor, config['tick_interval'], config['snapshot_period'], loop_stop, event_queue),
        daemon=True
    )
    loop_thread.start()

    print("monitor:", monitor, type(monitor) if 'monitor' in locals() else "NOT DEFINED")

    loop_thread.join()
    print("Loop ended. Server still running. Press Enter to stop.")
    input()
    print("\nЖизнь завершена. Финальное состояние:")
    print(self_state)
