import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional

# Папка для архивов
ARCHIVE_DIR = Path("data/archive")
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class MemoryEntry:
    event_type: str
    meaning_significance: float
    timestamp: float
    weight: float = 1.0  # Вес записи для механизма забывания
    feedback_data: Optional[
        Dict
    ] = None  # Для Feedback записей (сериализованный FeedbackRecord)
    subjective_timestamp: Optional[float] = None  # Субъективное время в момент создания записи


class ArchiveMemory:
    """
    Архивная память для долгосрочного хранения записей.
    Хранит записи, которые были перенесены из активной памяти.
    """

    def __init__(self, archive_file: Optional[Path] = None, load_existing: bool = False):
        """
        Инициализация архивной памяти.

        Args:
            archive_file: Путь к файлу архива. Если None, используется дефолтный.
            load_existing: Загружать ли существующие данные из файла. По умолчанию False.
        """
        if archive_file is None:
            archive_file = ARCHIVE_DIR / "memory_archive.json"
        self.archive_file = archive_file
        self._entries: List[MemoryEntry] = []
        if load_existing:
            self._load_archive()

    def _load_archive(self):
        """Загружает архив из файла, если он существует."""
        if self.archive_file.exists():
            try:
                with self.archive_file.open("r") as f:
                    data = json.load(f)
                    self._entries = [
                        MemoryEntry(**entry) for entry in data.get("entries", [])
                    ]
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

    def add_entries(self, entries: List[MemoryEntry]):
        """
        Добавляет несколько записей в архив.

        Args:
            entries: Список записей памяти для архивации
        """
        self._entries.extend(entries)

    def get_entries(
        self,
        event_type: Optional[str] = None,
        min_significance: Optional[float] = None,
        start_timestamp: Optional[float] = None,
        end_timestamp: Optional[float] = None,
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
        result = self._entries

        if event_type:
            result = [e for e in result if e.event_type == event_type]

        if min_significance is not None:
            result = [e for e in result if e.meaning_significance >= min_significance]

        if start_timestamp is not None:
            result = [e for e in result if e.timestamp >= start_timestamp]

        if end_timestamp is not None:
            result = [e for e in result if e.timestamp <= end_timestamp]

        return result

    def get_all_entries(self) -> List[MemoryEntry]:
        """Возвращает все записи из архива."""
        return self._entries.copy()

    def size(self) -> int:
        """Возвращает количество записей в архиве."""
        return len(self._entries)

    def save_archive(self):
        """Сохраняет архив в файл."""
        data = {"entries": [asdict(entry) for entry in self._entries]}
        with self.archive_file.open("w") as f:
            json.dump(data, f, indent=2, default=str)

    def clear(self):
        """Очищает архив (используется с осторожностью)."""
        self._entries = []


class Memory(list):
    """
    Активная память с поддержкой архивации.
    """

    def __init__(self, archive: Optional[ArchiveMemory] = None, load_existing_archive: bool = False):
        """
        Инициализация памяти.

        Args:
            archive: Экземпляр ArchiveMemory для архивации. Если None, создается новый.
            load_existing_archive: Загружать ли существующие данные архива. По умолчанию False.
        """
        super().__init__()
        if archive is None:
            archive = ArchiveMemory(load_existing=load_existing_archive)
        self.archive = archive
        self._max_size = 50  # Максимальный размер активной памяти
        self._min_weight_threshold = 0.1  # Порог веса для автоматического удаления

    def append(self, item):
        super().append(item)
        self.clamp_size()

    def clamp_size(self):
        """Ограничивает размер памяти, удаляя записи с наименьшим весом и ниже порога."""
        # Сначала удаляем записи с весом ниже порога
        self[:] = [
            entry for entry in self if entry.weight >= self._min_weight_threshold
        ]

        # Затем ограничиваем размер, удаляя записи с наименьшим весом
        while len(self) > self._max_size:
            # Находим запись с наименьшим весом
            if not self:
                break
            min_weight_entry = min(self, key=lambda x: x.weight)
            self.remove(min_weight_entry)

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
        import time

        current_time = time.time()
        entries_to_archive = []

        # Собираем записи для архивации
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
                self.remove(entry)

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

    def decay_weights(self, decay_factor: float = 0.99, min_weight: float = 0.0) -> int:
        """
        Применяет затухание весов ко всем записям памяти.

        Args:
            decay_factor: Коэффициент затухания (0.0-1.0). Вес умножается на этот коэффициент.
            min_weight: Минимальный вес после затухания. Веса ниже этого значения устанавливаются в min_weight.

        Returns:
            Количество записей, вес которых достиг минимума
        """
        if not self:
            return 0

        import time

        current_time = time.time()
        min_weight_count = 0

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
            significance_factor = (
                0.5 + 0.5 * entry.meaning_significance
            )  # От 0.5 до 1.0
            entry.weight *= significance_factor

            # Ограничиваем минимальным весом
            if entry.weight < min_weight:
                entry.weight = min_weight
                min_weight_count += 1

        return min_weight_count

    def get_statistics(self) -> Dict:
        """
        Возвращает статистику использования памяти.

        Returns:
            Словарь со статистикой
        """
        if not self:
            return {
                "active_entries": 0,
                "archive_entries": self.archive.size(),
                "event_types": {},
                "avg_significance": 0.0,
                "oldest_timestamp": None,
                "newest_timestamp": None,
            }

        event_types = {}
        total_significance = 0.0
        timestamps = []

        for entry in self:
            event_types[entry.event_type] = event_types.get(entry.event_type, 0) + 1
            total_significance += entry.meaning_significance
            timestamps.append(entry.timestamp)

        return {
            "active_entries": len(self),
            "archive_entries": self.archive.size(),
            "event_types": event_types,
            "avg_significance": total_significance / len(self) if self else 0.0,
            "oldest_timestamp": min(timestamps) if timestamps else None,
            "newest_timestamp": max(timestamps) if timestamps else None,
        }
