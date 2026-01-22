from dataclasses import dataclass, field
from typing import Dict, Optional, Any

from src.memory.memory import ArchiveMemory, Memory
from ...contracts.serialization_contract import Serializable


@dataclass
class MemoryState(Serializable):
    """
    Компонент состояния, отвечающий за память системы Life.

    Включает активную память, архивную память и связанные метрики.
    """

    # Основные компоненты памяти
    memory: Optional[Memory] = field(default=None)  # Активная память
    archive_memory: ArchiveMemory = field(
        default_factory=lambda: ArchiveMemory(load_existing=False, ignore_existing_file=True)
    )

    # Статистика и метрики памяти
    entries_by_type: Dict[str, int] = field(default_factory=dict)  # Статистика по типам записей

    # Параметры эхо-памяти
    echo_count: int = 0          # Количество эхо-всплываний
    last_echo_time: float = 0.0  # Время последнего эхо

    # Экспериментальные параметры памяти
    sensory_buffer_size: int = 0      # Размер сенсорного буфера
    semantic_concepts_count: int = 0  # Количество семантических концепций
    procedural_patterns_count: int = 0  # Количество процедурных паттернов

    def add_memory_entry(self, entry_type: str) -> None:
        """Добавляет запись в статистику по типам."""
        if entry_type not in self.entries_by_type:
            self.entries_by_type[entry_type] = 0
        self.entries_by_type[entry_type] += 1

    def get_total_entries(self) -> int:
        """Возвращает общее количество записей памяти."""
        return sum(self.entries_by_type.values())

    def get_memory_stats(self) -> Dict[str, int]:
        """Возвращает статистику памяти."""
        return {
            "total_entries": self.get_total_entries(),
            "entries_by_type": self.entries_by_type.copy(),
            "echo_count": self.echo_count,
            "sensory_buffer_size": self.sensory_buffer_size,
            "semantic_concepts": self.semantic_concepts_count,
            "procedural_patterns": self.procedural_patterns_count
        }

    def record_echo_event(self) -> None:
        """Записывает событие эхо-памяти."""
        self.echo_count += 1
        self.last_echo_time = self.get_current_time()

    def get_current_time(self) -> float:
        """Возвращает текущее время (для совместимости с существующими вызовами)."""
        import time
        return time.time()

    def has_active_memory(self) -> bool:
        """Проверяет, есть ли активная память."""
        return self.memory is not None

    def has_archive_memory(self) -> bool:
        """Проверяет, есть ли архивная память."""
        return self.archive_memory is not None

    def to_dict(self) -> Dict[str, Any]:
        """
        Сериализует состояние памяти.

        Returns:
            Dict[str, Any]: Словарь с состоянием памяти
        """
        return {
            "has_active_memory": self.has_active_memory(),
            "has_archive_memory": self.has_archive_memory(),
            "entries_by_type": self.entries_by_type.copy(),
            "echo_count": self.echo_count,
            "last_echo_time": self.last_echo_time,
            "sensory_buffer_size": self.sensory_buffer_size,
            "semantic_concepts_count": self.semantic_concepts_count,
            "procedural_patterns_count": self.procedural_patterns_count,
            "memory_stats": self.get_memory_stats() if self.memory else {}
        }