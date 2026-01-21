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
*   **v2.3:** Реализована многоуровневая система индексации для быстрого поиска - MemoryIndexEngine с LRU кэшированием, primary и composite индексы.

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

### Многоуровневая индексация (v2.3)

Реализована высокопроизводительная система индексации для быстрого поиска по памяти:

#### Архитектура индексов
```
Уровень 1: Primary Indexes
├── event_type_index: dict[str, set[int]] - быстрый поиск по типу события
├── timestamp_entries: list[tuple] - сортированные записи по времени
├── significance_entries: list[tuple] - сортированные записи по значимости
└── weight_entries: list[tuple] - сортированные записи по весу

Уровень 2: Composite Indexes (опционально)
├── event_type + timestamp: комбинированные индексы для сложных запросов
└── event_type + significance: оптимизация для фильтров по типу + значимости

Уровень 3: Query Cache (LRU)
├── Хэши запросов -> кэшированные результаты
└── Автоматическое удаление редко используемых результатов
```

#### MemoryIndexEngine
Класс `MemoryIndexEngine` обеспечивает:
*   **Быстрый поиск:** O(1) для поиска по event_type, O(log n) для range запросов
*   **LRU кэширование:** Автоматическое кэширование результатов повторяющихся запросов
*   **Мониторинг:** Детальная статистика производительности и использования кэша
*   **Оптимизация памяти:** Эффективное использование памяти с ограничением размера кэша

#### Производительность
*   **Запросов в секунду:** до 800+ для 10k записей с повторяющимися запросами
*   **Cache hit rate:** до 98% для типичных сценариев использования
*   **Ускорение:** 10-100x по сравнению с линейным поиском для больших объемов данных

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

### Индексированный поиск (v2.3)
```python
from src.memory.memory import Memory, ArchiveMemory, MemoryEntry
from src.memory.index_engine import MemoryQuery
import time

# Создание памяти с индексацией
memory = Memory()
archive = ArchiveMemory()
memory = Memory(archive=archive)

# Добавление большого количества записей
event_types = ["decay", "recovery", "shock", "learning"]
for i in range(1000):
    entry = MemoryEntry(
        event_type=random.choice(event_types),
        meaning_significance=random.uniform(0.1, 1.0),
        timestamp=time.time() - random.uniform(0, 86400 * 30),  # Последние 30 дней
        weight=random.uniform(0.1, 1.0)
    )
    memory.append(entry)

# Быстрый поиск по типу события
query = MemoryQuery(event_type="decay")
decay_events = memory.search_entries(query)
print(f"Найдено decay событий: {len(decay_events)}")

# Поиск по временному диапазону (последние 7 дней)
week_ago = time.time() - 7 * 86400
query = MemoryQuery(start_timestamp=week_ago)
recent_events = memory.search_entries(query)
print(f"Событий за неделю: {len(recent_events)}")

# Сложный запрос: decay события с высокой значимостью
query = MemoryQuery(
    event_type="decay",
    min_significance=0.8,
    limit=10,
    sort_by="significance",
    sort_order="desc"
)
important_decay = memory.search_entries(query)
print(f"Важных decay событий: {len(important_decay)}")

# Поиск в архиве с индексацией
archived_learning = archive.search_entries(
    MemoryQuery(event_type="learning", min_significance=0.5)
)
print(f"Архивных learning событий: {len(archived_learning)}")

# Статистика индексации
from src.memory.index_engine import performance_metrics
search_time = performance_metrics.get_average_time("memory_index_search")
if search_time:
    print(f"Среднее время индексированного поиска: {search_time:.6f}s")
```

## Реализация

### Файлы компонента
*   **`src/memory/types.py`** — определения типов данных (MemoryEntry)
*   **`src/memory/memory.py`** — основная реализация Memory и ArchiveMemory
*   **`src/memory/index_engine.py`** — многоуровневый индексный движок
*   **`src/test/test_memory.py`** — unit-тесты для базовой функциональности
*   **`src/test/test_memory_index_engine.py`** — тесты индексного движка
*   **`src/test/benchmark_memory_indexing.py`** — нагрузочное тестирование

## Связь с другими модулями

*   **Meaning Engine:** Создает материал для памяти (см. [`src/meaning/`](../../src/meaning/)).
*   **Activation:** Механизм извлечения памяти (см. [10.1_ACTIVATION_Memory.md](10.1_ACTIVATION_Memory.md)).
*   **Runtime Loop:** Использует индексированный поиск для активации памяти (см. [`src/runtime/loop.py`](../../src/runtime/loop.py)).
*   **Performance Metrics:** Мониторит производительность индексации (см. [`src/runtime/performance_metrics.py`](../../src/runtime/performance_metrics.py)).
