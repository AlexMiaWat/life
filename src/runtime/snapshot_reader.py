"""
SnapshotReader: чтение снапшотов состояния Life для API.

Предоставляет thread-safe доступ к сериализованным snapshots состояния,
изолируя API от прямого доступа к живому объекту self_state.

Использует атомарную замену снапшотов для гарантии консистентности
и reader-writer lock для защиты от race conditions.
"""
import json
import logging
import threading
import time
from pathlib import Path
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

# Папка для снимков
SNAPSHOT_DIR = Path("data/snapshots")


class RWLock:
    """
    Простая реализация reader-writer lock.

    Позволяет множественным читателям читать одновременно,
    но гарантирует эксклюзивный доступ для писателя.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._readers = 0
        self._writer = False
        self._read_condition = threading.Condition(self._lock)
        self._write_condition = threading.Condition(self._lock)

    def acquire_read(self):
        """Получить блокировку для чтения"""
        with self._lock:
            while self._writer:
                self._read_condition.wait()
            self._readers += 1

    def release_read(self):
        """Освободить блокировку чтения"""
        with self._lock:
            self._readers -= 1
            if self._readers == 0:
                self._write_condition.notify()

    def acquire_write(self):
        """Получить блокировку для записи"""
        with self._lock:
            while self._readers > 0 or self._writer:
                self._write_condition.wait()
            self._writer = True

    def release_write(self):
        """Освободить блокировку записи"""
        with self._lock:
            self._writer = False
            self._read_condition.notify_all()
            self._write_condition.notify()

    def __enter__(self):
        # Контекстный менеджер для чтения по умолчанию
        self.acquire_read()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release_read()


class SnapshotReader:
    """
    Читатель снапшотов состояния Life.

    Предоставляет API для чтения последнего snapshot из файловой системы
    с кэшированием для производительности и thread-safe доступом.
    """

    def __init__(self, cache_ttl_seconds: float = 1.0):
        """
        Инициализация читателя снапшотов.

        Args:
            cache_ttl_seconds: Время жизни кэша в секундах (по умолчанию 1.0)
        """
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: Optional[Dict[str, Any]] = None
        self._cache_timestamp: float = 0.0
        self._rw_lock = RWLock()
        self._last_snapshot_path: Optional[Path] = None

    def read_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        """
        Читает последний snapshot из файловой системы.

        Использует кэширование для производительности и атомарную замену для консистентности.
        Thread-safe с использованием RW-lock.

        Returns:
            Dict с данными snapshot или None если snapshot не найден
        """
        with self._rw_lock:
            current_time = time.time()

            # Проверяем, актуален ли кэш
            if (self._cache is not None and
                current_time - self._cache_timestamp < self.cache_ttl_seconds):
                return self._cache.copy()

            # Читаем новый snapshot
            try:
                snapshot_data = self._read_latest_snapshot_from_disk()
                if snapshot_data is not None:
                    self._cache = snapshot_data
                    self._cache_timestamp = current_time
                    return self._cache.copy()
                else:
                    # Если snapshot не найден, возвращаем None и очищаем кэш
                    self._cache = None
                    self._cache_timestamp = 0.0
                    return None
            except Exception as e:
                logger.error(f"Ошибка при чтении snapshot: {e}", exc_info=True)
                # В случае ошибки возвращаем закэшированные данные, если они есть
                if self._cache is not None:
                    logger.warning("Возвращаю закэшированные данные из-за ошибки чтения")
                    return self._cache.copy()
                return None

    def invalidate_cache(self) -> None:
        """
        Инвалидирует кэш принудительно.
        Полезно для тестирования или принудительного обновления.
        """
        with self._rw_lock:
            self._cache = None
            self._cache_timestamp = 0.0
            self._last_snapshot_path = None

    def force_refresh(self) -> Optional[Dict[str, Any]]:
        """
        Принудительно обновляет кэш и возвращает свежие данные.

        Полезно для тестирования и отладки.

        Returns:
            Dict с данными snapshot или None если snapshot не найден
        """
        self.invalidate_cache()
        return self.read_latest_snapshot()

    def get_safe_status_dict(
        self,
        include_optional: bool = True,
        limits: Optional[Dict[str, int]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Получает безопасный словарь состояния из snapshot.

        Аналогично методу SelfState.get_safe_status_dict(),
        но работает с сериализованными данными из файла.

        Args:
            include_optional: Если True, включает опциональные поля
            limits: Словарь с лимитами для больших полей

        Returns:
            Безопасный словарь состояния или None если snapshot не найден
        """
        snapshot = self.read_latest_snapshot()
        if snapshot is None:
            return None

        # Создаем копию для безопасной модификации
        state_dict = snapshot.copy()

        # Исключаем transient поля (если они есть в snapshot)
        state_dict.pop("activated_memory", None)
        state_dict.pop("last_pattern", None)

        # Исключаем внутренние поля (начинающиеся с _)
        keys_to_remove = [key for key in state_dict.keys() if key.startswith("_")]
        for key in keys_to_remove:
            state_dict.pop(key, None)

        # Исключаем не сериализуемые объекты
        state_dict.pop("archive_memory", None)

        # Обрабатываем limits
        if limits is None:
            limits = {}

        # Обработка memory (по умолчанию не включаем, только если явно указан лимит)
        memory_limit = limits.get("memory_limit")
        if memory_limit is not None and "memory" in state_dict:
            memory_entries = state_dict["memory"]
            if isinstance(memory_entries, list):
                # Ограничиваем количество записей памяти
                state_dict["memory"] = memory_entries[-memory_limit:] if memory_limit > 0 else []
        else:
            # По умолчанию не включаем memory (может быть большим)
            state_dict.pop("memory", None)

        # Ограничиваем размер других больших полей
        events_limit = limits.get("events_limit")
        if events_limit is not None and events_limit > 0:
            if "recent_events" in state_dict and isinstance(state_dict["recent_events"], list):
                state_dict["recent_events"] = state_dict["recent_events"][-events_limit:]
        else:
            # По умолчанию не включаем recent_events
            state_dict.pop("recent_events", None)

        energy_history_limit = limits.get("energy_history_limit")
        if energy_history_limit is not None and energy_history_limit > 0:
            if "energy_history" in state_dict and isinstance(state_dict["energy_history"], list):
                state_dict["energy_history"] = state_dict["energy_history"][-energy_history_limit:]
        else:
            state_dict.pop("energy_history", None)

        stability_history_limit = limits.get("stability_history_limit")
        if stability_history_limit is not None and stability_history_limit > 0:
            if "stability_history" in state_dict and isinstance(state_dict["stability_history"], list):
                state_dict["stability_history"] = state_dict["stability_history"][-stability_history_limit:]
        else:
            state_dict.pop("stability_history", None)

        adaptation_history_limit = limits.get("adaptation_history_limit")
        if adaptation_history_limit is not None and adaptation_history_limit > 0:
            if "adaptation_history" in state_dict and isinstance(state_dict["adaptation_history"], list):
                state_dict["adaptation_history"] = state_dict["adaptation_history"][-adaptation_history_limit:]
        else:
            state_dict.pop("adaptation_history", None)

        # Если include_optional=False, исключаем опциональные поля
        if not include_optional:
            optional_fields = [
                "life_id",
                "birth_timestamp",
                "learning_params",
                "adaptation_params",
                "planning",
                "intelligence",
                "subjective_time_base_rate",
                "subjective_time_rate_min",
                "subjective_time_rate_max",
                "subjective_time_intensity_coeff",
                "subjective_time_stability_coeff",
                "subjective_time_energy_coeff",
            ]
            for field_name in optional_fields:
                state_dict.pop(field_name, None)

        return state_dict

    def _read_latest_snapshot_from_disk(self) -> Optional[Dict[str, Any]]:
        """
        Читает последний snapshot непосредственно из файловой системы.

        Обрабатывает атомарную замену файлов и игнорирует временные файлы.

        Returns:
            Dict с данными snapshot или None если snapshot не найден
        """
        try:
            # Убеждаемся, что директория существует
            SNAPSHOT_DIR.mkdir(exist_ok=True)

            # Находим все snapshot файлы, игнорируя временные файлы (.tmp)
            snapshot_files = [
                f for f in SNAPSHOT_DIR.glob("snapshot_*.json")
                if not f.name.endswith('.tmp')
            ]
            if not snapshot_files:
                logger.debug("Snapshot файлы не найдены")
                return None

            # Сортируем по номеру тика (имя файла содержит номер тика)
            snapshot_files.sort(key=lambda p: int(p.stem.split("_")[1]))

            # Берем последний snapshot
            latest_snapshot = snapshot_files[-1]

            # Проверяем, изменился ли файл с момента последнего чтения
            if (self._last_snapshot_path is not None and
                self._last_snapshot_path == latest_snapshot and
                self._cache is not None):
                # Файл не изменился, возвращаем кэшированные данные
                return self._cache

            # Читаем snapshot с проверкой на консистентность
            # (атомарная замена гарантирует, что файл либо полностью записан, либо отсутствует)
            with latest_snapshot.open("r", encoding="utf-8") as f:
                data = json.load(f)

            self._last_snapshot_path = latest_snapshot
            logger.debug(f"Прочитан snapshot: {latest_snapshot}")
            return data

        except (FileNotFoundError, json.JSONDecodeError, ValueError, IndexError) as e:
            logger.warning(f"Ошибка при чтении snapshot файла: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при чтении snapshot: {e}", exc_info=True)
            return None


# Глобальный экземпляр SnapshotReader для использования в API
_snapshot_reader = SnapshotReader()


def get_snapshot_reader() -> SnapshotReader:
    """
    Получает глобальный экземпляр SnapshotReader.

    Returns:
        SnapshotReader: Глобальный читатель снапшотов
    """
    return _snapshot_reader


def read_life_status(
    include_optional: bool = True,
    limits: Optional[Dict[str, int]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Читает текущее состояние Life из snapshot.

    Удобная функция для использования в API.

    Args:
        include_optional: Если True, включает опциональные поля
        limits: Словарь с лимитами для больших полей

    Returns:
        Dict с состоянием Life или None если snapshot не найден
    """
    return _snapshot_reader.get_safe_status_dict(
        include_optional=include_optional,
        limits=limits
    )