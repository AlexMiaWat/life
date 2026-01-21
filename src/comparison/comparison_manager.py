"""
ComparisonManager - центральный менеджер системы сравнения жизней

Управляет множественными инстансами Life, координирует их запуск,
сбор данных и остановку. Предоставляет интерфейс для анализа
и сравнения поведения разных жизней.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path

from src.logging_config import get_logger
from .life_instance import LifeInstance, LifeConfig

logger = get_logger(__name__)


@dataclass
class ComparisonConfig:
    """Конфигурация для системы сравнения"""

    max_instances: int = 5
    default_tick_interval: float = 1.0
    default_snapshot_period: int = 10
    data_collection_interval: float = 5.0  # секунды
    auto_cleanup: bool = True
    port_range_start: int = 8001  # Начиная с 8001, чтобы не конфликтовать с основным API


class ComparisonManager:
    """
    Центральный менеджер для системы сравнения жизней.

    Управляет жизненным циклом множественных инстансов Life,
    собирает данные для анализа и предоставляет интерфейс
    для сравнения их поведения.
    """

    def __init__(self, config: ComparisonConfig = None):
        self.config = config or ComparisonConfig()
        self.instances: Dict[str, LifeInstance] = {}
        self.lock = threading.RLock()
        self.data_collectors: Dict[str, threading.Thread] = {}
        self.is_collecting = False
        self.collection_stop_event = threading.Event()

        # Статистика
        self.stats = {
            "total_instances_created": 0,
            "active_instances": 0,
            "failed_starts": 0,
            "data_collection_cycles": 0,
        }

        logger.info("ComparisonManager initialized")

    def create_instance(
        self,
        instance_id: str,
        tick_interval: Optional[float] = None,
        snapshot_period: Optional[int] = None,
        **kwargs,
    ) -> Optional[LifeInstance]:
        """
        Создает новый инстанс Life с указанной конфигурацией.

        Args:
            instance_id: Уникальный идентификатор инстанса
            tick_interval: Интервал между тиками
            snapshot_period: Период сохранения snapshots
            **kwargs: Дополнительные параметры конфигурации

        Returns:
            LifeInstance или None если создание не удалось
        """
        with self.lock:
            if instance_id in self.instances:
                logger.warning(f"Instance '{instance_id}' already exists")
                return None

            if len(self.instances) >= self.config.max_instances:
                logger.error(f"Maximum instances limit reached ({self.config.max_instances})")
                return None

            try:
                # Определяем порт для инстанса
                port = self._get_next_available_port()

                # Создаем конфигурацию
                config = LifeConfig(
                    instance_id=instance_id,
                    tick_interval=tick_interval or self.config.default_tick_interval,
                    snapshot_period=snapshot_period or self.config.default_snapshot_period,
                    port=port,
                    **kwargs,
                )

                # Создаем инстанс
                instance = LifeInstance(config)
                self.instances[instance_id] = instance
                self.stats["total_instances_created"] += 1

                logger.info(f"Created Life instance '{instance_id}' (port: {port})")
                return instance

            except Exception as e:
                logger.error(f"Failed to create instance '{instance_id}': {e}")
                self.stats["failed_starts"] += 1
                return None

    def start_instance(self, instance_id: str) -> bool:
        """
        Запускает указанный инстанс Life.

        Args:
            instance_id: Идентификатор инстанса

        Returns:
            bool: True если запуск успешен
        """
        with self.lock:
            instance = self.instances.get(instance_id)
            if not instance:
                logger.error(f"Instance '{instance_id}' not found")
                return False

            if instance.start():
                self.stats["active_instances"] += 1
                return True
            else:
                return False

    def stop_instance(self, instance_id: str, timeout: float = 5.0) -> bool:
        """
        Останавливает указанный инстанс Life.

        Args:
            instance_id: Идентификатор инстанса
            timeout: Таймаут остановки

        Returns:
            bool: True если остановка успешна
        """
        with self.lock:
            instance = self.instances.get(instance_id)
            if not instance:
                logger.error(f"Instance '{instance_id}' not found")
                return False

            if instance.stop(timeout):
                self.stats["active_instances"] -= 1
                return True
            else:
                return False

    def start_all_instances(self) -> Dict[str, bool]:
        """
        Запускает все созданные инстансы параллельно.

        Returns:
            Dict с результатами запуска для каждого инстанса
        """
        results = {}

        with ThreadPoolExecutor(max_workers=self.config.max_instances) as executor:
            futures = {}
            for instance_id, instance in self.instances.items():
                future = executor.submit(self.start_instance, instance_id)
                futures[future] = instance_id

            for future in as_completed(futures):
                instance_id = futures[future]
                try:
                    results[instance_id] = future.result()
                except Exception as e:
                    logger.error(f"Error starting instance '{instance_id}': {e}")
                    results[instance_id] = False

        return results

    def stop_all_instances(self, timeout: float = 5.0) -> Dict[str, bool]:
        """
        Останавливает все активные инстансы параллельно.

        Args:
            timeout: Таймаут остановки для каждого инстанса

        Returns:
            Dict с результатами остановки для каждого инстанса
        """
        results = {}

        with ThreadPoolExecutor(max_workers=self.config.max_instances) as executor:
            futures = {}
            for instance_id in self.instances.keys():
                future = executor.submit(self.stop_instance, instance_id, timeout)
                futures[future] = instance_id

            for future in as_completed(futures):
                instance_id = futures[future]
                try:
                    results[instance_id] = future.result()
                except Exception as e:
                    logger.error(f"Error stopping instance '{instance_id}': {e}")
                    results[instance_id] = False

        return results

    def get_instance_status(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает статус указанного инстанса.

        Args:
            instance_id: Идентификатор инстанса

        Returns:
            Dict со статусом инстанса или None
        """
        with self.lock:
            instance = self.instances.get(instance_id)
            if not instance:
                return None

            return instance.get_status()

    def get_all_instances_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Получает статус всех инстансов.

        Returns:
            Dict со статусами всех инстансов
        """
        with self.lock:
            return {
                instance_id: instance.get_status()
                for instance_id, instance in self.instances.items()
            }

    def collect_comparison_data(self) -> Dict[str, Any]:
        """
        Собирает данные от всех активных инстансов для сравнения.

        Returns:
            Dict с агрегированными данными от всех инстансов
        """
        data = {"timestamp": time.time(), "instances": {}, "summary": {}}

        with self.lock:
            for instance_id, instance in self.instances.items():
                if instance.is_running and instance.is_alive():
                    try:
                        # Получаем snapshot
                        snapshot = instance.get_latest_snapshot()

                        # Получаем последние логи
                        logs = instance.get_structured_logs(limit=100)

                        data["instances"][instance_id] = {
                            "status": instance.get_status(),
                            "snapshot": snapshot,
                            "recent_logs": logs,
                        }

                    except Exception as e:
                        logger.error(f"Error collecting data from instance '{instance_id}': {e}")
                        data["instances"][instance_id] = {
                            "status": instance.get_status(),
                            "error": str(e),
                        }

        # Вычисляем сводную статистику
        data["summary"] = self._compute_summary_stats(data["instances"])

        self.stats["data_collection_cycles"] += 1
        return data

    def start_data_collection(self, callback: Optional[Callable] = None):
        """
        Запускает фоновый сбор данных для сравнения.

        Args:
            callback: Функция обратного вызова для обработки собранных данных
        """
        if self.is_collecting:
            logger.warning("Data collection is already running")
            return

        self.is_collecting = True
        self.collection_stop_event.clear()

        def collect_loop():
            logger.info("Starting data collection loop")

            while not self.collection_stop_event.is_set():
                try:
                    data = self.collect_comparison_data()

                    if callback:
                        callback(data)

                    time.sleep(self.config.data_collection_interval)

                except Exception as e:
                    logger.error(f"Error in data collection loop: {e}")
                    time.sleep(1.0)

            logger.info("Data collection loop stopped")

        thread = threading.Thread(target=collect_loop, daemon=True, name="data-collection")
        thread.start()

        logger.info("Data collection started")

    def stop_data_collection(self):
        """Останавливает сбор данных."""
        if not self.is_collecting:
            logger.warning("Data collection is not running")
            return

        logger.info("Stopping data collection...")
        self.collection_stop_event.set()
        self.is_collecting = False

        # Ждем небольшую паузу для корректного завершения
        time.sleep(0.1)

    def cleanup_instances(self, force: bool = False) -> Dict[str, bool]:
        """
        Очищает завершившиеся инстансы.

        Args:
            force: Принудительно остановить все инстансы перед очисткой

        Returns:
            Dict с результатами очистки
        """
        results = {}

        with self.lock:
            instances_to_remove = []

            for instance_id, instance in self.instances.items():
                should_remove = False

                if force:
                    # Принудительно останавливаем все
                    instance.stop(timeout=2.0)
                    should_remove = True
                elif not instance.is_running and not instance.is_alive():
                    # Удаляем завершившиеся
                    should_remove = True

                if should_remove:
                    instances_to_remove.append(instance_id)
                    results[instance_id] = True
                else:
                    results[instance_id] = False

            # Удаляем инстансы
            for instance_id in instances_to_remove:
                del self.instances[instance_id]
                logger.info(f"Cleaned up instance '{instance_id}'")

        return results

    def get_comparison_stats(self) -> Dict[str, Any]:
        """
        Возвращает статистику работы системы сравнения.

        Returns:
            Dict со статистикой
        """
        with self.lock:
            active_count = sum(1 for i in self.instances.values() if i.is_running and i.is_alive())

            return {
                "manager_stats": self.stats.copy(),
                "active_instances": active_count,
                "total_instances": len(self.instances),
                "is_collecting": self.is_collecting,
                "config": {
                    "max_instances": self.config.max_instances,
                    "data_collection_interval": self.config.data_collection_interval,
                },
            }

    def _get_next_available_port(self) -> int:
        """Определяет следующий доступный порт для инстанса."""
        used_ports = {instance.config.port for instance in self.instances.values()}

        port = self.config.port_range_start
        while port in used_ports:
            port += 1

        return port

    def _compute_summary_stats(self, instances_data: Dict[str, Any]) -> Dict[str, Any]:
        """Вычисляет сводную статистику по данным инстансов."""
        summary = {
            "total_instances": len(instances_data),
            "active_instances": 0,
            "avg_uptime": 0.0,
            "total_ticks": 0,
            "avg_energy": 0.0,
            "avg_stability": 0.0,
            "avg_integrity": 0.0,
        }

        uptimes = []
        energies = []
        stabilities = []
        integrities = []

        for instance_data in instances_data.values():
            if "status" in instance_data:
                status = instance_data["status"]
                if status.get("is_running") and status.get("is_alive"):
                    summary["active_instances"] += 1
                    uptimes.append(status.get("uptime", 0))

            if "snapshot" in instance_data and instance_data["snapshot"]:
                snapshot = instance_data["snapshot"]
                energies.append(snapshot.get("energy", 0))
                stabilities.append(snapshot.get("stability", 0))
                integrities.append(snapshot.get("integrity", 0))
                summary["total_ticks"] += snapshot.get("ticks", 0)

        if uptimes:
            summary["avg_uptime"] = sum(uptimes) / len(uptimes)
        if energies:
            summary["avg_energy"] = sum(energies) / len(energies)
        if stabilities:
            summary["avg_stability"] = sum(stabilities) / len(stabilities)
        if integrities:
            summary["avg_integrity"] = sum(integrities) / len(integrities)

        return summary

    def __str__(self) -> str:
        stats = self.get_comparison_stats()
        return (
            f"ComparisonManager(active={stats['active_instances']}, "
            f"total={stats['total_instances']}, "
            f"collecting={stats['is_collecting']})"
        )
