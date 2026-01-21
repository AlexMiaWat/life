"""
Модуль памяти системы Life.

Предоставляет различные типы памяти: эпизодическую, семантическую, процедурную,
а также унифицированные интерфейсы для работы с ними.
"""

from .memory import ArchiveMemory, Memory
from .memory_types import MemoryEntry
from .memory_interface import (
    MemoryInterface,
    EpisodicMemoryInterface,
    SemanticMemoryInterface,
    ProceduralMemoryInterface,
    MemoryStatistics,
)

__all__ = [
    "ArchiveMemory",
    "Memory",
    "MemoryEntry",
    "MemoryInterface",
    "EpisodicMemoryInterface",
    "SemanticMemoryInterface",
    "ProceduralMemoryInterface",
    "MemoryStatistics",
]