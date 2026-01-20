# 09.1_Memory_Entry.md — Запись памяти (MemoryEntry)

## Текущий статус
✅ **Реализован** (v2.2)
*   Файл: [`src/memory/memory.py`](../../src/memory/memory.py)
*   Интегрирован в [`src/state/self_state.py`](../../src/state/self_state.py)
*   Поддерживает хранение эпизодов с типом события, значимостью и временной меткой.
*   Ограничение размера памяти до 50 записей.
*   **v2.0:** Добавлена архивная память, механизм забывания с весами, статистика использования.
*   **v2.1:** Добавлено субъективное время как сквозная ось жизни.
*   **v2.2:** Добавлены оптимизации производительности - кэширование сериализации, метрики производительности, оптимизированная clamp_size().

### Описание реализации
Memory как `list[MemoryEntry]` в SelfState, append после MeaningEngine если significance >0, clamp_size=50 (удаление по весу). Поддержка архивации старых записей.

#### Пример структуры MemoryEntry
```python
@dataclass
class MemoryEntry:
    event_type: str  # Тип события (например, 'decay', 'recovery')
    meaning_significance: float  # Значимость события для памяти
    timestamp: float  # Время создания записи (Unix timestamp)
    weight: float = 1.0  # Вес записи для механизма забывания (v2.0)
    feedback_data: Optional[Dict] = None  # Для Feedback записей
    subjective_timestamp: Optional[float] = None  # Субъективное время в момент создания записи (v2.1)
```

#### Принципы
- Только значимый опыт: Записи добавляются только если significance > 0 после обработки MeaningEngine.
- Нет активации/влияния на state: Память хранит опыт, но не влияет на текущее состояние или поведение.

## Текущая реализация

### MemoryEntry (v2.1)
Класс [`MemoryEntry`](../../src/memory/memory.py) представляет единицу памяти:
*   `event_type: str` — тип события (например, 'decay', 'recovery').
*   `meaning_significance: float` — значимость события для памяти.
*   `timestamp: float` — время создания записи (Unix timestamp).
*   `weight: float` — вес записи для механизма забывания (по умолчанию 1.0). Записи с низким весом удаляются первыми.
*   `feedback_data: Optional[Dict]` — дополнительные данные для Feedback записей (сериализованный FeedbackRecord).
*   `subjective_timestamp: Optional[float]` — субъективное время в момент создания записи (v2.1). Дополняет физическое время второй шкалой времени, отражающей внутренний опыт системы.

### Memory (v2.2)
Класс [`Memory`](../../src/memory/memory.py) наследует от `list` и управляет коллекцией записей с оптимизацией производительности:
*   `append(item)` — добавляет запись и автоматически ограничивает размер, инвалидируя кэш сериализации.
*   `clamp_size()` — поддерживает максимум 50 записей, удаляя записи с наименьшим весом и ниже порога (0.1). Оптимизирована для производительности с однократной сортировкой.
*   `decay_weights(decay_factor, min_weight)` — применяет затухание весов ко всем записям с измерением производительности. Учитывает возраст записи и значимость (более значимые записи забываются медленнее).
*   `archive_old_entries(max_age, min_weight, min_significance)` — переносит старые записи в архив по критериям возраста, веса или значимости с измерением производительности. Включает обработку ошибок при сохранении архива.
*   `get_statistics()` — возвращает статистику использования памяти (количество активных/архивных записей, типы событий, средняя значимость).
*   `get_serialized_entries()` — возвращает кэшированные сериализованные записи для оптимизации snapshot (v2.2).
*   `_invalidate_cache()` — инвалидирует кэш сериализованных данных при изменениях (v2.2).
*   `_serialized_cache` — внутренний кэш для оптимизации сериализации snapshot (v2.2).

### ArchiveMemory (v2.0)
Класс [`ArchiveMemory`](../../src/memory/memory.py) для долгосрочного хранения записей:
*   `add_entry(entry)` — добавляет запись в архив.
*   `add_entries(entries)` — добавляет несколько записей в архив.
*   `get_entries(event_type, min_significance, start_timestamp, end_timestamp)` — получает записи из архива с фильтрацией.
*   `get_all_entries()` — возвращает все записи из архива.
*   `size()` — возвращает количество записей в архиве.
*   `save_archive()` — сохраняет архив в файл `data/archive/memory_archive.json`.
*   `_load_archive()` — загружает архив из файла при инициализации.

**Механизм архивации:**
- Архив хранится в `data/archive/memory_archive.json`
- Автоматически загружается при создании ArchiveMemory
- Сохраняется при добавлении записей через `archive_old_entries()`

### Интеграция в SelfState
Память интегрирована в [`SelfState`](../../src/state/self_state.py):
*   `memory: Memory` — активная память с поддержкой архивации (до 50 записей). Является экземпляром класса `Memory`, а не простым списком.
*   `archive_memory: ArchiveMemory` — архивная память для долгосрочного хранения (v2.0).
*   `memory` инициализируется с `archive=archive_memory` при создании SelfState.
*   Архив автоматически загружается при создании SelfState и при загрузке snapshot.

### Оптимизации производительности (v2.2)
*   **Кэширование сериализации:** Метод `get_serialized_entries()` кэширует сериализованные записи для многократного использования в snapshot. Кэш инвалидируется при любых изменениях памяти.
*   **Оптимизированная clamp_size():** Вместо поиска минимума на каждой итерации выполняется однократная сортировка с последующим удалением лишних элементов.
*   **Метрики производительности:** Все критические операции (`archive_old_entries`, `decay_weights`) измеряют время выполнения с помощью `PerformanceMetrics`.
*   **Атомарные изменения:** Изменения кэша и памяти происходят атомарно для обеспечения консистентности.

## Пример использования

### Базовое использование (v1.0)
```python
from src.memory.memory import MemoryEntry, Memory
import time

# Создание записи памяти
entry = MemoryEntry(
    event_type="decay",
    meaning_significance=0.8,
    timestamp=time.time()
)

# Создание объекта памяти
memory = Memory()
memory.append(entry)

# Память автоматически ограничивает размер до 50 записей
print(f"Размер памяти: {len(memory)}")
```

### Использование архивации (v2.0)
```python
from src.memory.memory import MemoryEntry, Memory, ArchiveMemory
import time

# Создание памяти с архивом
archive = ArchiveMemory()
memory = Memory(archive=archive)

# Добавление записей
for i in range(100):
    entry = MemoryEntry(
        event_type="decay",
        meaning_significance=0.5 + i * 0.01,
        timestamp=time.time() - (100 - i) * 3600,  # Старые записи
        weight=1.0 - i * 0.01  # Уменьшаем вес
    )
    memory.append(entry)

# Затухание весов (механизм забывания)
# Вызывается автоматически в runtime loop каждые 10 тиков
min_weight_count = memory.decay_weights(decay_factor=0.99, min_weight=0.0)
print(f"Записей с минимальным весом: {min_weight_count}")

# Архивация старых записей (старше 1 дня или с весом < 0.3)
# Вызывается автоматически в runtime loop каждые 50 тиков
archived_count = memory.archive_old_entries(
    max_age=86400,  # 1 день в секундах
    min_weight=0.3
)
print(f"Заархивировано записей: {archived_count}")

# Получение статистики
stats = memory.get_statistics()
print(f"Активных записей: {stats['active_entries']}")
print(f"Архивных записей: {stats['archive_entries']}")
print(f"Типы событий: {stats['event_types']}")

# Поиск в архиве
old_entries = archive.get_entries(
    event_type="decay",
    min_significance=0.7
)
print(f"Найдено в архиве: {len(old_entries)}")
```

## Связь с другими модулями

*   **Meaning Engine:** Создает материал для памяти (см. [`src/meaning/`](../../src/meaning/)).
*   **Activation:** Механизм извлечения памяти (см. [10.1_ACTIVATION_Memory.md](10.1_ACTIVATION_Memory.md)).
