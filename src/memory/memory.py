import json
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional

from .index_engine import MemoryIndexEngine, MemoryQuery
from .memory_types import MemoryEntry
from .memory_interface import EpisodicMemoryInterface, MemoryStatistics

# Папка для архивов
ARCHIVE_DIR = Path("data/archive")
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


class ArchiveMemory(EpisodicMemoryInterface):
    """
    Архивная память для долгосрочного хранения записей.
    Хранит записи, которые были перенесены из активной памяти.
    """

    def __init__(
        self,
        archive_file: Optional[Path] = None,
        load_existing: bool = False,
        ignore_existing_file: bool = False,
    ):
        """
        Инициализация архивной памяти.

        Args:
            archive_file: Путь к файлу архива. Если None, используется дефолтный.
            load_existing: Загружать ли существующие данные из файла. По умолчанию False.
            ignore_existing_file: Игнорировать существующий файл, даже если load_existing=True. По умолчанию False.
        """
        if archive_file is None:
            archive_file = ARCHIVE_DIR / "memory_archive.json"
        self.archive_file = archive_file
        self._entries: List[MemoryEntry] = []
        self._index_engine = MemoryIndexEngine()  # Индекс для архивных записей
        if load_existing and not ignore_existing_file:
            self._load_archive()

    def _load_archive(self):
        """Загружает архив из файла, если он существует."""
        if self.archive_file.exists():
            try:
                with self.archive_file.open("r") as f:
                    data = json.load(f)
                    self._entries = [MemoryEntry(**entry) for entry in data.get("entries", [])]
                    # Индексируем загруженные записи
                    for entry in self._entries:
                        self._index_engine.add_entry(entry)
            except (json.JSONDecodeError, KeyError, TypeError):
                # Если файл поврежден, начинаем с пустого архива
                self._entries = []

    def add_entry(self, entry: MemoryEntry):
        """
        Добавляет запись в архив.

        Args:
            entry: Запись памяти для архивации
        """
        self._entries.append(entry)
        self._index_engine.add_entry(entry)

    def add_entries(self, entries: List[MemoryEntry]):
        """
        Добавляет несколько записей в архив.

        Args:
            entries: Список записей памяти для архивации
        """
        self._entries.extend(entries)
        for entry in entries:
            self._index_engine.add_entry(entry)

    def get_entries(
        self,
        event_type: Optional[str] = None,
        min_significance: Optional[float] = None,
        start_timestamp: Optional[float] = None,
        end_timestamp: Optional[float] = None,
        limit: Optional[int] = None,
    ) -> List[MemoryEntry]:
        """
        Получает записи из архива с фильтрацией.

        Args:
            event_type: Фильтр по типу события
            min_significance: Минимальная значимость
            start_timestamp: Начало временного диапазона
            end_timestamp: Конец временного диапазона

        Returns:
            Список отфильтрованных записей
        """
        # Используем оптимизированный поиск через индексы
        query = MemoryQuery(
            event_type=event_type,
            min_significance=min_significance,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
        )
        results = self._index_engine.search(query)

        # Применяем ограничение по количеству
        if limit is not None:
            results = results[:limit]

        return results

    def get_all_entries(self) -> List[MemoryEntry]:
        """Возвращает все записи из архива."""
        return self._entries.copy()

    def search_entries(self, query: MemoryQuery) -> List[MemoryEntry]:
        """
        Поиск записей в архивной памяти с использованием индексов.

        Args:
            query: Запрос для поиска

        Returns:
            Список найденных записей, отсортированный по запросу
        """
        return self._index_engine.search(query)

    def size(self) -> int:
        """Возвращает количество записей в архиве."""
        return len(self._entries)

    def get_statistics(self) -> MemoryStatistics:
        """
        Получить статистику архивной памяти.

        Returns:
            MemoryStatistics: Статистика использования
        """
        if not self._entries:
            return MemoryStatistics(
                total_entries=0,
                memory_type="archive"
            )

        total_significance = sum(entry.meaning_significance for entry in self._entries)
        timestamps = [entry.timestamp for entry in self._entries]

        return MemoryStatistics(
            total_entries=len(self._entries),
            archived_entries=len(self._entries),
            average_significance=total_significance / len(self._entries),
            oldest_timestamp=min(timestamps),
            newest_timestamp=max(timestamps),
            memory_type="archive"
        )

    def validate_integrity(self) -> bool:
        """
        Проверить целостность архивной памяти.

        Returns:
            bool: True если данные корректны
        """
        try:
            # Проверяем, что все записи имеют правильную структуру
            for entry in self._entries:
                if not hasattr(entry, 'event_type') or not hasattr(entry, 'timestamp'):
                    return False
                if not isinstance(entry.meaning_significance, (int, float)):
                    return False
                if not isinstance(entry.weight, (int, float)):
                    return False
            return True
        except Exception:
            return False

    def clear(self) -> None:
        """Очистить архив (используется с осторожностью)."""
        self._entries = []
        self._index_engine = MemoryIndexEngine()

    def is_empty(self) -> bool:
        """
        Проверить, пуст ли архив.

        Returns:
            bool: True если архив пуст
        """
        return len(self._entries) == 0

    def archive_old_entries(
        self,
        max_age: Optional[float] = None,
        min_weight: Optional[float] = None,
        min_significance: Optional[float] = None,
    ) -> int:
        """
        Архивная память уже содержит архивированные записи.
        Этот метод не применим для ArchiveMemory.

        Returns:
            int: Всегда возвращает 0
        """
        # ArchiveMemory - это уже архив, метод не применим
        return 0

    def save_archive(self):
        """Сохраняет архив в файл."""
        data = {"entries": [asdict(entry) for entry in self._entries]}
        with self.archive_file.open("w") as f:
            json.dump(data, f, indent=2, default=str)

    def clear(self):
        """Очищает архив (используется с осторожностью)."""
        self._entries = []
        self._index_engine = MemoryIndexEngine()  # Создаем новый индекс


class Memory(list, EpisodicMemoryInterface):
    """
    Активная память с поддержкой архивации и оптимизацией сериализации.
    """

    def __init__(
        self,
        archive: Optional[ArchiveMemory] = None,
        load_existing_archive: bool = False,
        ignore_existing_archive_file: bool = False,
    ):
        """
        Инициализация памяти.

        Args:
            archive: Экземпляр ArchiveMemory для архивации. Если None, создается новый.
            load_existing_archive: Загружать ли существующие данные архива. По умолчанию False.
            ignore_existing_archive_file: Игнорировать существующий файл архива. По умолчанию False.
        """
        super().__init__()
        if archive is None:
            archive = ArchiveMemory(
                load_existing=load_existing_archive,
                ignore_existing_file=ignore_existing_archive_file,
            )
        self.archive = archive
        self._max_size = 50  # Максимальный размер активной памяти
        self._min_weight_threshold = 0.1  # Порог веса для автоматического удаления
        self._serialized_cache = None  # Кэш сериализованных записей для оптимизации snapshot

        # Индексный движок для быстрого поиска
        self._index_engine = MemoryIndexEngine()

    def append(self, item):
        super().append(item)
        self._invalidate_cache()
        self._index_engine.add_entry(item)
        self.clamp_size()

    def _invalidate_cache(self):
        """Инвалидирует кэш сериализованных данных при изменении памяти."""
        self._serialized_cache = None

    def get_serialized_entries(self) -> List[Dict]:
        """
        Возвращает сериализованные записи памяти с кэшированием для производительности.

        Returns:
            Список сериализованных записей для snapshot
        """
        if self._serialized_cache is None:
            self._serialized_cache = [
                {
                    "event_type": entry.event_type,
                    "meaning_significance": entry.meaning_significance,
                    "timestamp": entry.timestamp,
                    "weight": entry.weight,
                    "feedback_data": entry.feedback_data,
                }
                for entry in self
            ]
        return self._serialized_cache

    def get_archived_entries(self) -> List[MemoryEntry]:
        """
        Получить список архивных записей для эхо-всплываний.

        Returns:
            Список всех записей из архивной памяти
        """
        return self.archive.get_all_entries()

    def search_entries(self, query: MemoryQuery) -> List[MemoryEntry]:
        """
        Поиск записей в активной памяти с использованием индексов.

        Args:
            query: Запрос для поиска

        Returns:
            Список найденных записей, отсортированный по запросу
        """
        return self._index_engine.search(query)

    def clamp_size(self):
        """Ограничивает размер памяти, удаляя записи с наименьшим весом и ниже порога."""
        self._invalidate_cache()  # Инвалидируем кэш перед изменениями

        # Сначала удаляем записи с весом ниже порога
        self[:] = [entry for entry in self if entry.weight >= self._min_weight_threshold]

        # Затем ограничиваем размер, удаляя записи с наименьшим весом
        if len(self) > self._max_size:
            # Оптимизация: сортируем один раз вместо поиска минимума на каждой итерации
            self.sort(key=lambda x: x.weight)
            # Удаляем записи с наименьшими весами из индекса
            entries_to_remove = self[: len(self) - self._max_size]
            for entry in entries_to_remove:
                self._index_engine.remove_entry(entry)
            # Удаляем записи с наименьшими весами
            del self[: len(self) - self._max_size]

    def archive_old_entries(
        self,
        max_age: Optional[float] = None,
        min_weight: Optional[float] = None,
        min_significance: Optional[float] = None,
    ) -> int:
        """
        Переносит старые записи из активной памяти в архив.

        Args:
            max_age: Максимальный возраст записи для архивации (в секундах от текущего времени)
            min_weight: Минимальный вес записи (если вес < min_weight, запись архивируется)
            min_significance: Минимальная значимость (записи с меньшей значимостью архивируются)

        Returns:
            Количество заархивированных записей

        Raises:
            ValueError: При некорректных параметрах
            RuntimeError: При ошибке сохранения архива
        """
        # Валидация параметров
        if max_age is not None and max_age < 0:
            raise ValueError("max_age должен быть неотрицательным")
        if min_weight is not None and not (0.0 <= min_weight <= 1.0):
            raise ValueError("min_weight должен быть в диапазоне [0.0, 1.0]")
        if min_significance is not None and not (0.0 <= min_significance <= 1.0):
            raise ValueError("min_significance должен быть в диапазоне [0.0, 1.0]")
        """
        Переносит старые записи из активной памяти в архив.

        Args:
            max_age: Максимальный возраст записи для архивации (в секундах от текущего времени)
            min_weight: Минимальный вес записи (если вес < min_weight, запись архивируется)
            min_significance: Минимальная значимость (записи с меньшей значимостью архивируются)

        Returns:
            Количество заархивированных записей
        """
        from src.runtime.performance_metrics import measure_time

        with measure_time("archive_old_entries"):
            import time

            self._invalidate_cache()  # Инвалидируем кэш перед изменениями

            current_time = time.time()
            entries_to_archive = []

            # Собираем записи для архивации (оптимизация: не удаляем во время итерации)
            for entry in self[:]:
                should_archive = False

                # Проверка по возрасту
                if max_age is not None:
                    age = current_time - entry.timestamp
                    if age > max_age:
                        should_archive = True

                # Проверка по весу
                if min_weight is not None:
                    if entry.weight < min_weight:
                        should_archive = True

                # Проверка по значимости
                if min_significance is not None:
                    if entry.meaning_significance < min_significance:
                        should_archive = True

                if should_archive:
                    entries_to_archive.append(entry)

            # Оптимизация: удаляем все записи за один проход
            for entry in entries_to_archive:
                self.remove(entry)
                self._index_engine.remove_entry(entry)

            # Добавляем записи в архив
            if entries_to_archive:
                try:
                    self.archive.add_entries(entries_to_archive)
                    self.archive.save_archive()
                except Exception as e:
                    # В случае ошибки сохранения архива, возвращаем записи в активную память
                    # чтобы не потерять данные
                    self.extend(entries_to_archive)
                    raise RuntimeError(f"Ошибка при сохранении архива: {e}") from e

                return len(entries_to_archive)

            # Если нет записей для архивации, возвращаем 0
            return 0

    def decay_weights(self, decay_factor: float = 0.99, min_weight: float = 0.0) -> int:
        """
        Применяет затухание весов ко всем записям памяти.

        Args:
            decay_factor: Коэффициент затухания (0.0-1.0). Вес умножается на этот коэффициент.
            min_weight: Минимальный вес после затухания. Веса ниже этого значения устанавливаются в min_weight.

        Returns:
            Количество записей, вес которых достиг минимума
        """
        from src.runtime.performance_metrics import measure_time

        with measure_time("decay_weights"):
            if not self:
                return 0

            import time

            current_time = time.time()
            min_weight_count = 0

            self._invalidate_cache()  # Инвалидируем кэш перед изменениями

            for entry in self:
                # Базовое затухание
                entry.weight *= decay_factor

                # Учитываем возраст записи (старые записи забываются быстрее)
                age = current_time - entry.timestamp
                age_factor = 1.0 / (
                    1.0 + age / 86400.0
                )  # Дополнительное затухание для записей старше дня
                entry.weight *= age_factor

                # Учитываем значимость (более значимые записи забываются медленнее)
                significance_factor = 0.5 + 0.5 * entry.meaning_significance  # От 0.5 до 1.0
                entry.weight *= significance_factor

                # Ограничиваем минимальным весом
                if entry.weight < min_weight:
                    entry.weight = min_weight
                    min_weight_count += 1

            return min_weight_count

    def get_statistics(self) -> MemoryStatistics:
        """
        Возвращает статистику использования памяти.

        Returns:
            MemoryStatistics: Статистика памяти
        """
        # Оптимизация: кэшируем часто используемые значения
        active_entries_count = len(self)
        archive_size = self.archive.size() if hasattr(self.archive, 'size') else 0

        if not self:
            return MemoryStatistics(
                total_entries=archive_size,
                active_entries=0,
                archived_entries=archive_size,
                memory_type="episodic"
            )

        # Оптимизация: один проход для подсчета статистики
        total_significance = 0.0
        event_types = {}
        oldest_timestamp = float('inf')
        newest_timestamp = float('-inf')

        for entry in self:
            total_significance += entry.meaning_significance
            event_types[entry.event_type] = event_types.get(entry.event_type, 0) + 1
            # Оптимизация: находим min/max за один проход
            oldest_timestamp = min(oldest_timestamp, entry.timestamp)
            newest_timestamp = max(newest_timestamp, entry.timestamp)

        avg_significance = total_significance / active_entries_count
        return MemoryStatistics(
            total_entries=active_entries_count + archive_size,
            active_entries=active_entries_count,
            archived_entries=archive_size,
            average_significance=avg_significance,
            oldest_timestamp=oldest_timestamp if oldest_timestamp != float('inf') else None,
            newest_timestamp=newest_timestamp if newest_timestamp != float('-inf') else None,
            memory_type="episodic",
            event_types=event_types,
            avg_significance=avg_significance
        )

    def validate_integrity(self) -> bool:
        """
        Проверить целостность эпизодической памяти.

        Returns:
            bool: True если данные корректны
        """
        try:
            # Проверяем активную память
            for entry in self:
                if not hasattr(entry, 'event_type') or not hasattr(entry, 'timestamp'):
                    return False
                if not isinstance(entry.meaning_significance, (int, float)):
                    return False
                if not isinstance(entry.weight, (int, float)):
                    return False

            # Проверяем архив, если он есть
            if hasattr(self.archive, 'validate_integrity'):
                return self.archive.validate_integrity()

            return True
        except Exception:
            return False

    @property
    def size(self) -> int:
        """Получить общий размер памяти (активная + архив)."""
        archive_size = self.archive.size if hasattr(self.archive, 'size') else 0
        return len(self) + archive_size

    def is_empty(self) -> bool:
        """
        Проверить, пустая ли память.

        Returns:
            bool: True если память полностью пуста
        """
        return len(self) == 0 and (not hasattr(self.archive, 'size') or self.archive.size() == 0)
