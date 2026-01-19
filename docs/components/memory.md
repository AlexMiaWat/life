# 09.1_Memory_Entry.md — Запись памяти (MemoryEntry)

## Текущий статус
✅ **Реализован** (v1.0)
*   Файл: [`src/memory/memory.py`](../../src/memory/memory.py)
*   Интегрирован в [`src/state/self_state.py`](../../src/state/self_state.py)
*   Поддерживает хранение эпизодов с типом события, значимостью и временной меткой.
*   Ограничение размера памяти до 50 записей.

### Описание реализации
Memory как `list[MemoryEntry]` в SelfState, append после MeaningEngine если significance >0, clamp_size=50 (drop oldest).

#### Пример структуры MemoryEntry
```python
@dataclass
class MemoryEntry:
    event_type: str  # Тип события (например, 'decay', 'recovery')
    meaning_significance: float  # Значимость события для памяти
    timestamp: datetime  # Время создания записи
```

#### Принципы
- Только значимый опыт: Записи добавляются только если significance > 0 после обработки MeaningEngine.
- Нет активации/влияния на state: Память хранит опыт, но не влияет на текущее состояние или поведение.

## Текущая реализация

### MemoryEntry
Класс [`MemoryEntry`](../../src/memory/memory.py) представляет единицу памяти:
*   `event_type: str` — тип события (например, 'decay', 'recovery').
*   `meaning_significance: float` — значимость события для памяти.
*   `timestamp: datetime` — время создания записи.

### Memory
Класс [`Memory`](../../src/memory/memory.py) наследует от `list` и управляет коллекцией записей:
*   `append(item)` — добавляет запись и автоматически ограничивает размер.
*   `clamp_size()` — поддерживает максимум 50 записей, удаляя самые старые при превышении.

### Интеграция в SelfState
Память интегрирована в [`SelfState`](../../src/state/self_state.py) как поле `memory: list[MemoryEntry]`, что позволяет сохранять и загружать состояние памяти вместе с остальным состоянием жизни.

## Пример использования

```python
from src.memory.memory import MemoryEntry, Memory
from datetime import datetime

# Создание записи памяти
entry = MemoryEntry(
    event_type="decay",
    meaning_significance=0.8,
    timestamp=datetime.now()
)

# Создание объекта памяти
memory = Memory()
memory.append(entry)

# Память автоматически ограничивает размер до 50 записей
print(f"Размер памяти: {len(memory)}")
```

## Связь с другими модулями

*   **Meaning Engine:** Создает материал для памяти (см. [`src/meaning/`](../../src/meaning/)).
*   **Activation:** Механизм извлечения памяти (см. [10.1_ACTIVATION_Memory.md](10.1_ACTIVATION_Memory.md)).
