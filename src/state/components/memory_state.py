from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List

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

    def to_dict(self, chunk_size: int = 100, max_chunks: int = 10) -> Dict[str, Any]:
        """
        Сериализует состояние памяти с chunked обработкой для производительности.

        Args:
            chunk_size: Размер чанка для сериализации записей памяти (по умолчанию 100)
            max_chunks: Максимальное количество чанков для обработки (по умолчанию 10)

        Returns:
            Dict[str, Any]: Словарь с состоянием памяти
        """
        result = {
            "has_active_memory": self.has_active_memory(),
            "has_archive_memory": self.has_archive_memory(),
            "entries_by_type": self.entries_by_type.copy(),
            "echo_count": self.echo_count,
            "last_echo_time": self.last_echo_time,
            "sensory_buffer_size": self.sensory_buffer_size,
            "semantic_concepts_count": self.semantic_concepts_count,
            "procedural_patterns_count": self.procedural_patterns_count,
            "memory_stats": self.get_memory_stats() if self.memory else {},
            "serialization_chunked": True,
            "chunk_size": chunk_size,
            "max_chunks": max_chunks
        }

        # Chunked сериализация активной памяти
        if self.memory is not None:
            try:
                # Используем оптимизированный метод для chunked сериализации
                result["active_memory_chunks"] = self._serialize_memory_chunks(chunk_size, max_chunks)
                result["active_memory_total_entries"] = len(self.memory)
            except Exception as e:
                # Fallback при ошибке сериализации
                result["active_memory_error"] = f"Serialization failed: {str(e)}"
                result["active_memory_chunks"] = []

        return result

    def _serialize_memory_chunks(self, chunk_size: int, max_chunks: int) -> List[Dict[str, Any]]:
        """
        Сериализует память по чанкам для избежания больших блокировок.

        Args:
            chunk_size: Размер одного чанка
            max_chunks: Максимальное количество чанков

        Returns:
            List[Dict[str, Any]]: Список чанков с сериализованными записями
        """
        if not self.memory:
            return []

        chunks = []
        total_entries = len(self.memory)

        # Обрабатываем записи в обратном порядке (сначала самые свежие)
        for chunk_idx in range(min(max_chunks, (total_entries + chunk_size - 1) // chunk_size)):
            start_idx = chunk_idx * chunk_size
            end_idx = min(start_idx + chunk_size, total_entries)

            chunk_entries = []
            for i in range(start_idx, end_idx):
                entry = self.memory[-(i + 1)]  # Начинаем с самых свежих
                try:
                    chunk_entries.append({
                        "event_type": entry.event_type,
                        "meaning_significance": entry.meaning_significance,
                        "timestamp": entry.timestamp,
                        "weight": entry.weight,
                        "feedback_data": entry.feedback_data if entry.feedback_data else {}
                    })
                except AttributeError:
                    # Пропускаем поврежденные записи
                    continue

            if chunk_entries:  # Добавляем только непустые чанки
                chunks.append({
                    "chunk_index": chunk_idx,
                    "start_index": start_idx,
                    "end_index": end_idx,
                    "entries_count": len(chunk_entries),
                    "entries": chunk_entries
                })

        return chunks