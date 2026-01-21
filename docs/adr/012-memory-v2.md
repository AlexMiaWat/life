# ADR 012: Memory v2.0

## Статус
✅ Принято

## Дата
2026-01-20

## Контекст

Проект Life нуждался в расширении системы памяти для поддержки долгосрочного хранения, забывания и эффективной работы с большим объемом данных. Первоначальная реализация Memory (v1.0) имела ограничения:

### Проблемы v1.0
- **Отсутствие забывания**: записи оставались в памяти вечно
- **Нет архивации**: старые записи не переносились в долгосрочное хранилище
- **Ограниченная емкость**: память росла бесконечно
- **Нет индексации**: медленный поиск по большим объемам данных
- **Отсутствие статистики**: невозможно анализировать использование памяти

### Архитектурные требования
- **Забывание**: механизм постепенного уменьшения весов записей
- **Архивация**: перенос старых/менее значимых записей в долгосрочное хранилище
- **Ограниченная емкость**: автоматическое управление размером активной памяти
- **Эффективный поиск**: индексация и фильтрация по различным критериям
- **Статистика**: мониторинг и анализ использования памяти

## Решение

### Архитектура Memory v2.0

#### 1. Расширение MemoryEntry

```python
@dataclass
class MemoryEntry:
    event_type: str
    meaning_significance: float
    timestamp: float
    weight: float = 1.0  # Вес для механизма забывания
    feedback_data: Optional[Dict] = None  # Данные Feedback
    subjective_timestamp: Optional[float] = None  # Субъективное время
```

#### 2. ArchiveMemory - долгосрочное хранилище

```python
class ArchiveMemory:
    """Архивная память для долгосрочного хранения"""

    def __init__(self, archive_file: Optional[Path] = None, load_existing: bool = False):
        self.archive_file = archive_file or ARCHIVE_DIR / "memory_archive.json"
        self._entries: List[MemoryEntry] = []

    def add_entry(self, entry: MemoryEntry):
        """Добавляет запись в архив"""

    def get_entries(self, event_type=None, min_significance=None,
                   start_timestamp=None, end_timestamp=None) -> List[MemoryEntry]:
        """Получает записи с фильтрацией"""

    def save_archive(self):
        """Сохраняет архив в JSON файл"""
```

#### 3. Memory с поддержкой архивации

```python
class Memory(list):
    """Активная память с поддержкой архивации"""

    def __init__(self, archive: Optional[ArchiveMemory] = None):
        super().__init__()
        self.archive = archive or ArchiveMemory()
        self._max_size = 50  # Максимальный размер активной памяти
        self._min_weight_threshold = 0.1  # Порог веса для удаления
```

### Механизмы забывания и архивации

#### 1. Decay Weights - затухание весов

```python
def decay_weights(self, decay_factor: float = 0.99, min_weight: float = 0.0) -> int:
    """
    Применяет затухание весов ко всем записям.

    - Базовое затухание: weight *= decay_factor
    - Возрастной фактор: старые записи забываются быстрее
    - Фактор значимости: значимые записи забываются медленнее
    """
    for entry in self:
        entry.weight *= decay_factor

        # Возрастной фактор (записи старше дня забываются быстрее)
        age = current_time - entry.timestamp
        age_factor = 1.0 / (1.0 + age / 86400.0)
        entry.weight *= age_factor

        # Фактор значимости (0.5-1.0 в зависимости от significance)
        significance_factor = 0.5 + 0.5 * entry.meaning_significance
        entry.weight *= significance_factor

        # Ограничение минимальным весом
        entry.weight = max(entry.weight, min_weight)
```

#### 2. Archive Old Entries - перенос в архив

```python
def archive_old_entries(self, max_age=None, min_weight=None, min_significance=None) -> int:
    """
    Переносит записи в архив по критериям:

    - max_age: записи старше указанного возраста
    - min_weight: записи с весом ниже порога
    - min_significance: записи с низкой значимостью
    """
    entries_to_archive = []
    current_time = time.time()

    for entry in self[:]:
        should_archive = False

        if max_age and (current_time - entry.timestamp) > max_age:
            should_archive = True
        if min_weight and entry.weight < min_weight:
            should_archive = True
        if min_significance and entry.meaning_significance < min_significance:
            should_archive = True

        if should_archive:
            entries_to_archive.append(entry)

    # Удаляем из активной памяти и добавляем в архив
    for entry in entries_to_archive:
        self.remove(entry)
    self.archive.add_entries(entries_to_archive)
    self.archive.save_archive()

    return len(entries_to_archive)
```

#### 3. Clamp Size - ограничение размера

```python
def clamp_size(self):
    """Ограничивает размер памяти"""

    # Удаляем записи с весом ниже порога
    self[:] = [entry for entry in self if entry.weight >= self._min_weight_threshold]

    # Если все еще слишком много, удаляем записи с наименьшими весами
    if len(self) > self._max_size:
        self.sort(key=lambda x: x.weight)
        del self[:len(self) - self._max_size]
```

### Оптимизации производительности

#### 1. Кэширование сериализации

```python
def get_serialized_entries(self) -> List[Dict]:
    """Возвращает сериализованные записи с кэшированием"""
    if self._serialized_cache is None:
        self._serialized_cache = [{
            "event_type": entry.event_type,
            "meaning_significance": entry.meaning_significance,
            "timestamp": entry.timestamp,
            "weight": entry.weight,
            "feedback_data": entry.feedback_data,
        } for entry in self]
    return self._serialized_cache
```

#### 2. Инвалидация кэша при изменениях

```python
def append(self, item):
    super().append(item)
    self._invalidate_cache()
    self.clamp_size()

def _invalidate_cache(self):
    self._serialized_cache = None
```

### Интеграция в Runtime Loop

```python
# Константы для интервалов
DECAY_INTERVAL = 10      # Decay каждые 10 тиков
ARCHIVE_INTERVAL = 50    # Archive каждые 50 тиков
MEMORY_DECAY_FACTOR = 0.99
MEMORY_MIN_WEIGHT = 0.1
MEMORY_MAX_AGE_SECONDS = 7 * 24 * 3600  # 7 дней

# В runtime loop:
if self_state.ticks % DECAY_INTERVAL == 0:
    self_state.memory.decay_weights(decay_factor=MEMORY_DECAY_FACTOR)

if self_state.ticks % ARCHIVE_INTERVAL == 0:
    archived_count = self_state.memory.archive_old_entries(
        max_age=MEMORY_MAX_AGE_SECONDS,
        min_weight=MEMORY_MIN_WEIGHT
    )
```

### Статистика и мониторинг

```python
def get_statistics(self) -> Dict:
    """Возвращает статистику использования памяти"""
    return {
        "active_entries": len(self),
        "archive_entries": self.archive.size(),
        "event_types": event_types_count,
        "avg_significance": total_significance / len(self),
        "oldest_timestamp": min(timestamps),
        "newest_timestamp": max(timestamps),
    }
```

## Обоснование

### За выбранное решение

#### ✅ Реалистичная модель памяти
- **Забывание**: постепенное уменьшение весов со временем
- **Архивация**: перенос в долгосрочное хранилище
- **Ограниченная емкость**: автоматическое управление размером
- **Многофакторное забывание**: учитывает возраст, значимость, вес

#### ✅ Эффективность и масштабируемость
- **Кэширование**: оптимизация сериализации для snapshot
- **Батчинг**: групповые операции для производительности
- **Инвалидация кэша**: корректность при изменениях
- **Ленивая загрузка**: архив загружается по требованию

#### ✅ Надежность данных
- **Транзакционность**: записи возвращаются в память при ошибке архивации
- **Валидация**: проверка параметров перед операциями
- **Резервное копирование**: JSON сериализация с fallback
- **Отказоустойчивость**: graceful handling ошибок

#### ✅ Интеграция с архитектурой
- **Совместимость**: работает с существующими компонентами
- **Расширяемость**: легкое добавление новых критериев архивации
- **Мониторинг**: статистика для анализа поведения
- **Оптимизация**: разные интервалы для разных операций

### Против альтернатив

#### Альтернатива 1: Простое ограничение размера
- **Против**: Нет забывания, резкое удаление записей
- **Против**: Потеря важной исторической информации
- **Против**: Не отражает естественные процессы памяти

#### Альтернатива 2: Внешняя база данных
- **Против**: Дополнительная зависимость и сложность
- **Против**: Overkill для требований проекта
- **Против**: Увеличение latency операций

#### Альтернатива 3: Только активная память без архива
- **Против**: Потеря долгосрочной памяти
- **Против**: Невозможность эхо-всплываний из прошлого
- **Против**: Ограниченные возможности обучения

## Последствия

### Положительные

#### ✅ Реалистичная модель поведения
- **Забывание**: имитация естественных процессов памяти человека
- **Архив**: возможность вспоминания старых событий
- **Динамика**: память эволюционирует со временем
- **Контекст**: привязка к субъективному времени

#### ✅ Улучшенная производительность
- **Ограниченный размер**: постоянная сложность операций
- **Кэширование**: оптимизация частых операций
- **Интервальное выполнение**: равномерная нагрузка на систему
- **Оптимизации**: минимизация аллокаций и копирований

#### ✅ Расширенные возможности
- **Поиск**: фильтрация по типам, времени, значимости
- **Статистика**: анализ паттернов использования памяти
- **Мониторинг**: отслеживание эффективности забывания
- **Отладка**: возможность анализа содержимого памяти

#### ✅ Архитектурная зрелость
- **Модульность**: разделение активной и архивной памяти
- **Тестируемость**: изолированное тестирование компонентов
- **Расширяемость**: легкое добавление новых механизмов
- **Совместимость**: интеграция с существующими компонентами

### Отрицательные

#### ⚠️ Сложность реализации
- **Множественные критерии**: сложная логика архивации
- **Взаимосвязи**: зависимости между decay и archive
- **Оптимизации**: дополнительные механизмы кэширования
- **Отладка**: сложность анализа поведения системы

#### ⚠️ Overhead на операции
- **Валидация**: проверки на каждом изменении
- **Кэширование**: дополнительная память для cache
- **Сериализация**: JSON dump при каждом snapshot
- **Статистика**: вычисления при каждом запросе

#### ⚠️ Конфигурационные сложности
- **Множество параметров**: интервалы, пороги, факторы
- **Балансировка**: оптимальные значения требуют настройки
- **Зависимости**: параметры влияют друг на друга
- **Мониторинг**: необходимость отслеживания эффективности

### Риски

#### Риск потери данных
- **Описание**: Ошибки в архивации могут привести к потере записей
- **Митигация**: транзакционность, бэкап, тестирование
- **Вероятность**: Низкая (транзакционная безопасность)

#### Риск производительности
- **Описание**: Decay и archive могут замедлить runtime loop
- **Митигация**: интервальное выполнение, оптимизации, профилирование
- **Вероятность**: Низкая (интервалы оптимизированы)

#### Риск переусложнения
- **Описание**: Слишком много параметров и логики
- **Митигация**: модульное тестирование, документация, рефакторинг
- **Вероятность**: Средняя

## Связанные документы

- [docs/architecture/overview.md](../architecture/overview.md) — обзор архитектуры
- [src/memory/memory.py](../../src/memory/memory.py) — реализация Memory v2.0
- [src/state/self_state.py](../../src/state/self_state.py) — интеграция Memory в SelfState
- [src/runtime/loop.py](../../src/runtime/loop.py) — использование в runtime loop
- [src/test/test_memory.py](../../src/test/test_memory.py) — тесты памяти
- [docs/components/memory.md](../components/memory.md) — документация компонента