"""
Process Restarter - безопасный перезапуск процесса вместо hot reload.

Модуль отслеживает изменения в исходных файлах и инициирует перезапуск
вместо использования importlib.reload, что обеспечивает чистое состояние
без проблем с идентичностью объектов и висячими потоками.
"""

import json
import os
import sys
import threading
import time
from typing import Any, Dict, Optional

from src.logging_config import get_logger

logger = get_logger(__name__)


class StateSerializer:
    """
    Сериализатор состояния для сохранения и восстановления при перезапуске.
    """

    RESTART_STATE_FILE = "data/restart_state.json"

    def __init__(self):
        self._lock = threading.Lock()
        os.makedirs("data", exist_ok=True)

    def save_restart_state(self, self_state: Any, event_queue: Any, config: Dict[str, Any]) -> bool:
        """
        Сохраняет состояние системы для восстановления после перезапуска.

        Args:
            self_state: Объект состояния системы
            event_queue: Очередь событий
            config: Конфигурация системы

        Returns:
            bool: True если сохранение успешно
        """
        try:
            with self._lock:
                state_data = {
                    "restart_marker": True,
                    "timestamp": time.time(),
                    "self_state": self_state.to_dict() if hasattr(self_state, "to_dict") else {},
                    "event_queue": event_queue.to_dict() if hasattr(event_queue, "to_dict") else [],
                    "config": config,
                }

                # Атомарная запись через временный файл
                temp_file = f"{self.RESTART_STATE_FILE}.tmp"
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(state_data, f, ensure_ascii=False, indent=2)

                os.rename(temp_file, self.RESTART_STATE_FILE)
                logger.info(f"Restart state saved to {self.RESTART_STATE_FILE}")
                return True

        except Exception as e:
            logger.error(f"Failed to save restart state: {e}")
            return False

    def load_restart_state(self) -> Optional[Dict[str, Any]]:
        """
        Загружает сохраненное состояние после перезапуска.

        Returns:
            Dict с данными состояния или None если файл не найден/поврежден
        """
        if not os.path.exists(self.RESTART_STATE_FILE):
            return None

        try:
            with open(self.RESTART_STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not data.get("restart_marker"):
                logger.warning("Invalid restart state file: missing restart_marker")
                return None

            logger.info(f"Restart state loaded from {self.RESTART_STATE_FILE}")
            return data

        except Exception as e:
            logger.error(f"Failed to load restart state: {e}")
            return None

    def cleanup_restart_state(self):
        """Удаляет файл состояния перезапуска после успешной загрузки."""
        try:
            if os.path.exists(self.RESTART_STATE_FILE):
                os.remove(self.RESTART_STATE_FILE)
                logger.debug("Restart state file cleaned up")
        except Exception as e:
            logger.warning(f"Failed to cleanup restart state: {e}")


class GracefulShutdownManager:
    """
    Менеджер корректного завершения всех компонентов системы.
    """

    def __init__(self, shutdown_timeout: float = 10.0):
        self.shutdown_timeout = shutdown_timeout
        self._shutdown_event = threading.Event()
        self._components = []

    def register_component(
        self, component_name: str, shutdown_func, join_func=None, timeout: float = 5.0
    ):
        """
        Регистрирует компонент для graceful shutdown.

        Args:
            component_name: Имя компонента для логирования
            shutdown_func: Функция для инициирования завершения
            join_func: Функция для ожидания завершения (thread.join)
            timeout: Таймаут ожидания в секундах
        """
        self._components.append(
            {
                "name": component_name,
                "shutdown_func": shutdown_func,
                "join_func": join_func,
                "timeout": timeout,
            }
        )

    def initiate_shutdown(self) -> bool:
        """
        Инициирует graceful shutdown всех зарегистрированных компонентов.

        Returns:
            bool: True если все компоненты завершились корректно
        """
        logger.info("Initiating graceful shutdown...")

        # Устанавливаем флаг завершения
        self._shutdown_event.set()

        success = True

        for component in self._components:
            try:
                logger.debug(f"Shutting down {component['name']}...")

                # Вызываем функцию завершения
                if component["shutdown_func"]:
                    component["shutdown_func"]()

                # Ждем завершения если есть join_func
                if component["join_func"]:
                    start_time = time.time()
                    component["join_func"](timeout=component["timeout"])

                    if time.time() - start_time >= component["timeout"]:
                        logger.warning(
                            f"{component['name']} did not shutdown within {component['timeout']}s"
                        )
                        success = False

            except Exception as e:
                logger.error(f"Error shutting down {component['name']}: {e}")
                success = False

        if success:
            logger.info("Graceful shutdown completed successfully")
        else:
            logger.warning("Graceful shutdown completed with some issues")

        return success

    def is_shutdown_requested(self) -> bool:
        """Проверяет, был ли запрошен shutdown."""
        return self._shutdown_event.is_set()


class ProcessRestarter:
    """
    Мониторит изменения файлов и управляет перезапуском процесса.
    """

    # Файлы для отслеживания изменений
    FILES_TO_WATCH = [
        "src/main_server_api.py",
        "src/monitor/console.py",
        "src/runtime/loop.py",
        "src/state/self_state.py",
        "src/environment/event.py",
        "src/environment/event_queue.py",
        "src/environment/generator.py",
        "src/dev/process_restarter.py",  # Сам себя тоже отслеживаем
    ]

    def __init__(self, check_interval: float = 1.0):
        self.check_interval = check_interval
        self._running = False
        self._thread = None
        self._file_mtimes = {}
        self._shutdown_manager = GracefulShutdownManager()
        self._state_serializer = StateSerializer()

        # Инициализация отслеживания
        self._init_file_tracking()

    def _init_file_tracking(self):
        """Инициализирует отслеживание файлов."""
        for file_path in self.FILES_TO_WATCH:
            try:
                if os.path.exists(file_path):
                    self._file_mtimes[file_path] = os.stat(file_path).st_mtime
                    logger.debug(f"Watching {file_path}")
                else:
                    logger.warning(f"File to watch not found: {file_path}")
            except Exception as e:
                logger.error(f"Error initializing watch for {file_path}: {e}")

    def _check_file_changes(self) -> bool:
        """
        Проверяет изменения в отслеживаемых файлах.

        Returns:
            bool: True если найдены изменения
        """
        changed = False

        for file_path in self.FILES_TO_WATCH:
            try:
                if os.path.exists(file_path):
                    current_mtime = os.stat(file_path).st_mtime
                    if current_mtime != self._file_mtimes.get(file_path, 0):
                        logger.info(f"File changed: {file_path}")
                        self._file_mtimes[file_path] = current_mtime
                        changed = True
                else:
                    # Файл исчез - считаем это изменением
                    if file_path in self._file_mtimes:
                        logger.info(f"File removed: {file_path}")
                        del self._file_mtimes[file_path]
                        changed = True
            except Exception as e:
                logger.error(f"Error checking {file_path}: {e}")

        return changed

    def register_component(
        self, component_name: str, shutdown_func, join_func=None, timeout: float = 5.0
    ):
        """
        Регистрирует компонент для graceful shutdown.
        """
        self._shutdown_manager.register_component(component_name, shutdown_func, join_func, timeout)

    def save_state_for_restart(
        self, self_state: Any, event_queue: Any, config: Dict[str, Any]
    ) -> bool:
        """
        Сохраняет состояние системы перед перезапуском.
        """
        return self._state_serializer.save_restart_state(self_state, event_queue, config)

    def _restart_process(self):
        """Перезапускает процесс с сохранением аргументов командной строки."""
        try:
            logger.info("Restarting process...")

            # Добавляем флаг --restart к аргументам
            restart_args = [sys.executable] + sys.argv + ["--restart"]

            logger.debug(f"Execv args: {restart_args}")
            os.execv(sys.executable, restart_args)

        except Exception as e:
            logger.error(f"Failed to restart process: {e}")
            # В случае ошибки завершаем процесс
            sys.exit(1)

    def _monitor_loop(self):
        """Основной цикл мониторинга и перезапуска."""
        logger.info("Process restarter started")

        while self._running and not self._shutdown_manager.is_shutdown_requested():
            try:
                time.sleep(self.check_interval)

                if self._check_file_changes():
                    logger.info("Changes detected, initiating restart...")

                    # Инициируем graceful shutdown
                    if self._shutdown_manager.initiate_shutdown():
                        # Ждем дополнительное время для завершения
                        time.sleep(2.0)

                        # Перезапускаем процесс
                        self._restart_process()
                    else:
                        logger.error("Graceful shutdown failed, aborting restart")

            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(self.check_interval)

        logger.info("Process restarter stopped")

    def start(self):
        """Запускает мониторинг в отдельном потоке."""
        if self._running:
            logger.warning("Process restarter is already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("Process restarter thread started")

    def stop(self):
        """Останавливает мониторинг."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)


# Глобальные экземпляры для использования в main_server_api.py
_process_restarter = None
_state_serializer = None


def get_process_restarter() -> ProcessRestarter:
    """Получить глобальный экземпляр ProcessRestarter."""
    global _process_restarter
    if _process_restarter is None:
        _process_restarter = ProcessRestarter()
    return _process_restarter


def get_state_serializer() -> StateSerializer:
    """Получить глобальный экземпляр StateSerializer."""
    global _state_serializer
    if _state_serializer is None:
        _state_serializer = StateSerializer()
    return _state_serializer


def is_restart() -> bool:
    """
    Проверяет, был ли процесс перезапущен (наличие флага --restart).

    Returns:
        bool: True если это перезапуск
    """
    return "--restart" in sys.argv


def load_restart_state_if_available():
    """
    Загружает состояние после перезапуска, если оно доступно.

    Returns:
        Tuple[dict, bool]: (состояние, был_ли_перезапуск)
    """
    serializer = get_state_serializer()
    state = serializer.load_restart_state()

    if state:
        # Очищаем файл после загрузки
        serializer.cleanup_restart_state()
        logger.info("Restart state loaded and cleaned up")
        return state, True

    return None, False
