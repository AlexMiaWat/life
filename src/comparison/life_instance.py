"""
LifeInstance - обертка для управления одним экземпляром Life

Этот класс предоставляет интерфейс для:
- Запуска Life в отдельном процессе
- Управления жизненным циклом (start/stop/restart)
- Сбора данных и логов от инстанса
- Отправки команд и получения состояния
"""

import json
import multiprocessing
import os
import signal
import subprocess
import sys
import time
import threading
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from pathlib import Path

from src.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class LifeConfig:
    """Конфигурация для одного инстанса Life"""

    instance_id: str
    tick_interval: float = 1.0
    snapshot_period: int = 10
    port: int = 8000
    data_dir: str = "data"
    clear_data_on_start: bool = False
    dev_mode: bool = False
    enable_profiling: bool = False
    disable_weakness_penalty: bool = False
    disable_structured_logging: bool = False
    disable_learning: bool = False
    disable_adaptation: bool = False
    disable_clarity_moments: bool = False
    log_flush_period_ticks: int = 10


class LifeInstance:
    """
    Управляет одним экземпляром Life, запущенным в отдельном процессе.

    Предоставляет интерфейс для запуска, остановки и мониторинга инстанса,
    а также для получения данных о его состоянии и поведении.
    """

    def __init__(self, config: LifeConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.is_running = False
        self.start_time: Optional[float] = None
        self.stop_event = threading.Event()

        # Создаем директорию для данных инстанса
        self.instance_data_dir = Path(f"{self.config.data_dir}/instances/{self.config.instance_id}")
        self.instance_data_dir.mkdir(parents=True, exist_ok=True)

        # Пути к логам и snapshots
        self.structured_log_path = self.instance_data_dir / "structured_log.jsonl"
        self.tick_log_path = self.instance_data_dir / "tick_log.jsonl"
        self.snapshots_dir = self.instance_data_dir / "snapshots"
        self.snapshots_dir.mkdir(exist_ok=True)

        logger.info(f"LifeInstance '{self.config.instance_id}' initialized")

    def start(self) -> bool:
        """
        Запускает инстанс Life в отдельном процессе.

        Returns:
            bool: True если запуск успешен, False иначе
        """
        if self.is_running:
            logger.warning(f"Instance '{self.config.instance_id}' is already running")
            return False

        try:
            # Формируем команду запуска
            cmd = self._build_command()

            # Настраиваем переменные окружения для изоляции данных
            env = os.environ.copy()
            env.update(
                {
                    "LIFE_INSTANCE_ID": self.config.instance_id,
                    "LIFE_DATA_DIR": str(self.instance_data_dir),
                    "LIFE_PORT": str(self.config.port),
                }
            )

            logger.info(
                f"Starting Life instance '{self.config.instance_id}' with command: {' '.join(cmd)}"
            )

            # Запускаем процесс
            self.process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.getcwd(),
            )

            self.start_time = time.time()
            self.is_running = True

            # Запускаем мониторинг процесса в отдельном потоке
            threading.Thread(
                target=self._monitor_process, daemon=True, name=f"monitor-{self.config.instance_id}"
            ).start()

            logger.info(
                f"Life instance '{self.config.instance_id}' started successfully (PID: {self.process.pid})"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to start Life instance '{self.config.instance_id}': {e}")
            return False

    def stop(self, timeout: float = 5.0) -> bool:
        """
        Останавливает инстанс Life.

        Args:
            timeout: Максимальное время ожидания остановки в секундах

        Returns:
            bool: True если остановка успешна, False иначе
        """
        if not self.is_running or self.process is None:
            logger.warning(f"Instance '{self.config.instance_id}' is not running")
            return True

        try:
            logger.info(
                f"Stopping Life instance '{self.config.instance_id}' (PID: {self.process.pid})"
            )

            # Посылаем сигнал SIGTERM
            self.process.terminate()

            # Ждем завершения
            try:
                self.process.wait(timeout=timeout)
                self.is_running = False
                logger.info(f"Life instance '{self.config.instance_id}' stopped successfully")
                return True
            except subprocess.TimeoutExpired:
                logger.warning(
                    f"Life instance '{self.config.instance_id}' didn't stop gracefully, killing..."
                )
                self.process.kill()
                self.process.wait(timeout=2.0)
                self.is_running = False
                logger.info(f"Life instance '{self.config.instance_id}' killed")
                return True

        except Exception as e:
            logger.error(f"Error stopping Life instance '{self.config.instance_id}': {e}")
            return False

    def restart(self) -> bool:
        """
        Перезапускает инстанс Life.

        Returns:
            bool: True если перезапуск успешен, False иначе
        """
        logger.info(f"Restarting Life instance '{self.config.instance_id}'")

        if not self.stop():
            logger.error(f"Failed to stop instance '{self.config.instance_id}' for restart")
            return False

        time.sleep(1.0)  # Небольшая пауза

        return self.start()

    def is_alive(self) -> bool:
        """
        Проверяет, жив ли процесс инстанса.

        Returns:
            bool: True если процесс работает, False иначе
        """
        if self.process is None:
            return False

        return self.process.poll() is None

    def get_status(self) -> Dict[str, Any]:
        """
        Получает статус инстанса Life.

        Returns:
            Dict с информацией о статусе инстанса
        """
        return {
            "instance_id": self.config.instance_id,
            "is_running": self.is_running,
            "is_alive": self.is_alive(),
            "start_time": self.start_time,
            "uptime": time.time() - self.start_time if self.start_time else 0,
            "pid": self.process.pid if self.process else None,
            "port": self.config.port,
            "data_dir": str(self.instance_data_dir),
            "config": {
                "tick_interval": self.config.tick_interval,
                "snapshot_period": self.config.snapshot_period,
                "dev_mode": self.config.dev_mode,
                "profiling": self.config.enable_profiling,
            },
        }

    def get_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        """
        Получает последний snapshot от инстанса.

        Returns:
            Dict с данными snapshot или None если нет snapshots
        """
        try:
            snapshot_files = list(self.snapshots_dir.glob("snapshot_*.json"))
            if not snapshot_files:
                return None

            # Находим самый свежий snapshot
            latest_snapshot = max(snapshot_files, key=lambda p: p.stat().st_mtime)

            with open(latest_snapshot, "r", encoding="utf-8") as f:
                return json.load(f)

        except Exception as e:
            logger.error(f"Error reading snapshot for instance '{self.config.instance_id}': {e}")
            return None

    def get_structured_logs(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Получает структурированные логи от инстанса.

        Args:
            limit: Максимальное количество записей (None для всех)

        Returns:
            List с записями логов
        """
        logs = []

        try:
            if not self.structured_log_path.exists():
                return logs

            with open(self.structured_log_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f):
                    if limit is not None and line_num >= limit:
                        break

                    line = line.strip()
                    if line:
                        try:
                            logs.append(json.loads(line))
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON in log line {line_num}: {line}")

        except Exception as e:
            logger.error(
                f"Error reading structured logs for instance '{self.config.instance_id}': {e}"
            )

        return logs

    def _build_command(self) -> List[str]:
        """Формирует команду для запуска Life инстанса."""
        cmd = [
            sys.executable,
            "src/main_server_api.py",
            "--tick-interval",
            str(self.config.tick_interval),
            "--snapshot-period",
            str(self.config.snapshot_period),
        ]

        if self.config.clear_data_on_start:
            cmd.extend(["--clear-data", "yes"])

        if self.config.dev_mode:
            cmd.append("--dev")

        if self.config.enable_profiling:
            cmd.append("--profile")

        return cmd

    def _monitor_process(self):
        """Мониторит процесс инстанса в отдельном потоке."""
        if self.process is None:
            return

        try:
            # Читаем stdout и stderr
            while self.is_running and not self.stop_event.is_set():
                if self.process.poll() is not None:
                    # Процесс завершился
                    stdout, stderr = self.process.communicate()

                    if stdout:
                        logger.info(f"Life instance '{self.config.instance_id}' stdout: {stdout}")
                    if stderr:
                        logger.error(f"Life instance '{self.config.instance_id}' stderr: {stderr}")

                    self.is_running = False
                    break

                time.sleep(0.1)

        except Exception as e:
            logger.error(f"Error monitoring Life instance '{self.config.instance_id}': {e}")
            self.is_running = False

    def __str__(self) -> str:
        status = self.get_status()
        return (
            f"LifeInstance(id='{status['instance_id']}', "
            f"running={status['is_running']}, "
            f"alive={status['is_alive']}, "
            f"uptime={status['uptime']:.1f}s)"
        )
