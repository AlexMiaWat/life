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

from src.environment import Event, EventQueue
from src.logging_config import get_logger, setup_logging
from src.monitor.console import monitor
from src.runtime.loop import run_loop
from src.state.self_state import SelfState

init()

from typing import Any

# Настройка логирования
logger = get_logger(__name__)

HOST = "localhost"
PORT = 8000


class StoppableHTTPServer(HTTPServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self_state больше не нужен - API читает из snapshots
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
        if self.path.startswith("/status"):
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()

            # Парсим query-параметры для ограничения больших полей
            from urllib.parse import parse_qs, urlparse

            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)

            # Извлекаем лимиты из query-параметров
            limits = {}
            if "memory_limit" in query_params:
                try:
                    limits["memory_limit"] = int(query_params["memory_limit"][0])
                except (ValueError, IndexError):
                    pass
            if "events_limit" in query_params:
                try:
                    limits["events_limit"] = int(query_params["events_limit"][0])
                except (ValueError, IndexError):
                    pass
            if "energy_history_limit" in query_params:
                try:
                    limits["energy_history_limit"] = int(
                        query_params["energy_history_limit"][0]
                    )
                except (ValueError, IndexError):
                    pass
            if "stability_history_limit" in query_params:
                try:
                    limits["stability_history_limit"] = int(
                        query_params["stability_history_limit"][0]
                    )
                except (ValueError, IndexError):
                    pass
            if "adaptation_history_limit" in query_params:
                try:
                    limits["adaptation_history_limit"] = int(
                        query_params["adaptation_history_limit"][0]
                    )
                except (ValueError, IndexError):
                    pass

            # Получаем текущее состояние
            # Сначала пробуем взять из сервера (для тестов), иначе из snapshot
            if (
                hasattr(self.server, "self_state")
                and self.server.self_state is not None
            ):
                self_state = self.server.self_state
            else:
                try:
                    self_state = SelfState().load_latest_snapshot()
                except FileNotFoundError:
                    self_state = SelfState()

            safe_status = self_state.get_safe_status_dict(limits=limits)
            self.wfile.write(json.dumps(safe_status).encode())
        elif self.path == "/refresh-cache":
            # В текущей реализации состояние читается из snapshots при каждом запросе,
            # поэтому кэширование не требуется. Просто возвращаем успех.
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(
                b'{"message": "Cache refreshed (no-op in current implementation)"}'
            )
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
            logger.debug(
                f"Получен POST /event: type='{event_type}', intensity={intensity}"
            )
            event = Event(
                type=event_type,
                intensity=intensity,
                timestamp=timestamp,
                metadata=metadata,
            )
            self.server.event_queue.push(event)
            logger.debug(
                f"Event PUSHED to queue. Size now: {self.server.event_queue.size()}"
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
                logger.debug(Fore.CYAN + "=" * 80 + Style.RESET_ALL)
                logger.debug(Fore.GREEN + "ВХОДЯЩИЙ HTTP-ЗАПРОС" + Style.RESET_ALL)
                logger.debug(
                    Fore.YELLOW
                    + f"Время: {self.log_date_time_string()}"
                    + Style.RESET_ALL
                )
                logger.debug(
                    Fore.YELLOW
                    + f"Клиент IP: {self.client_address[0]}"
                    + Style.RESET_ALL
                )
                logger.debug(
                    Fore.YELLOW + f"Запрос: {self.requestline}" + Style.RESET_ALL
                )
                logger.debug(Fore.MAGENTA + f"Статус ответа: {code}" + Style.RESET_ALL)
                if isinstance(size, (int, float)) and size > 0:
                    logger.debug(
                        Fore.MAGENTA + f"Размер ответа: {size} байт" + Style.RESET_ALL
                    )
                logger.debug(Fore.CYAN + "=" * 80 + Style.RESET_ALL)
            except UnicodeEncodeError:
                # Fallback to plain text if color output fails
                logger.debug("=" * 80)
                logger.debug("ВХОДЯЩИЙ HTTP-ЗАПРОС")
                logger.debug(f"Время: {self.log_date_time_string()}")
                logger.debug(f"Клиент IP: {self.client_address[0]}")
                logger.debug(f"Запрос: {self.requestline}")
                logger.debug(f"Статус ответа: {code}")
                if isinstance(size, (int, float)) and size > 0:
                    logger.debug(f"Размер ответа: {size} байт")
                logger.debug("=" * 80)
            sys.stdout.flush()


def start_api_server(event_queue, dev_mode):
    global server
    server = StoppableHTTPServer((HOST, PORT), LifeHandler)
    # self_state больше не передается - API читает из snapshots
    server.event_queue = event_queue
    server.dev_mode = dev_mode
    logger.info(f"API server running on http://{HOST}:{PORT}")
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
            logger.debug(f"Watching {f}")
        except Exception as e:
            logger.error(f"Error watching {f}: {e}")

    logger.info("Reloader initialized, starting poll loop")

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
            logger.info("Detected change, reloading modules...")

            # Остановка API сервера
            if server:
                server.shutdown()
                if api_thread:
                    api_thread.join(timeout=5.0)
                    if api_thread.is_alive():
                        logger.warning(
                            "[RELOAD] api_thread не завершился за 5 секунд, продолжается перезагрузка"
                        )

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

            logger.debug(
                f"Reloaded loop_module.run_loop: firstlineno={loop_module.run_loop.__code__.co_firstlineno}, argcount={loop_module.run_loop.__code__.co_argcount}"
            )
            logger.debug(
                f"New run_loop code file: {loop_module.run_loop.__code__.co_filename}"
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
                args=(event_queue, True),
                daemon=True,
            )
            api_thread.start()

            logger.info("Modules reloaded and server restarted")

            # Restart runtime loop
            if loop_thread and loop_thread.is_alive():
                loop_stop.set()
                loop_thread.join(timeout=5.0)
                logger.info("[RELOAD] Old loop stopped")

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
            logger.info("[RELOAD] New loop started")


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

    # Настройка уровня логирования в зависимости от режима
    setup_logging(verbose=dev_mode)

    config = {
        "tick_interval": args.tick_interval,
        "snapshot_period": args.snapshot_period,
    }

    if args.clear_data.lower() == "yes":
        logger.info("Очистка данных при старте...")
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
        logger.info("--dev mode enabled, starting reloader")
        threading.Thread(target=reloader_thread, daemon=True).start()

    # Start API thread
    api_thread = threading.Thread(
        target=start_api_server, args=(event_queue, dev_mode), daemon=True
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

    loop_thread.join()
    logger.info("Loop ended. Server still running. Press Enter to stop.")
    input()
    logger.info("\nЖизнь завершена. Финальное состояние:")
    logger.info(str(self_state))
