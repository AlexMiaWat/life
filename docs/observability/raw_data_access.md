# RawDataAccess - Компонент доступа к raw данным

## Обзор

`RawDataAccess` - компонент для унифицированного доступа к raw данным наблюдений. Предоставляет интерфейс для агрегации, фильтрации и экспорта данных из множественных источников наблюдений.

## Архитектурные принципы

### ✅ Унифицированный доступ
- **Множественные источники**: Поддержка различных источников данных наблюдений
- **Единый интерфейс**: Стандартизированные методы для всех типов источников
- **Фильтрация и агрегация**: Гибкие возможности фильтрации по типам, источникам и времени
- **Экспорт данных**: Поддержка различных форматов экспорта

### ❌ Ограничения
- **Без интерпретации**: Только предоставление доступа к данным без анализа
- **Без модификации**: Не изменяет данные источников
- **Без кэширования**: Работает непосредственно с источниками данных

## Структура данных

### ObservationData

```python
@dataclass
class ObservationData:
    """Структура данных наблюдения."""
    timestamp: float      # Время наблюдения
    event_type: str       # Тип события
    data: Any            # Данные наблюдения
    source: str          # Источник данных
    metadata: Dict[str, Any] = field(default_factory=dict)  # Метаданные
```

## Основные возможности

### Добавление источников данных

```python
from src.observability.raw_data_access import RawDataAccess
from src.observability.passive_data_sink import PassiveDataSink

# Создание компонента доступа
data_access = RawDataAccess()

# Добавление источников данных
data_access.add_data_source(passive_sink_1)
data_access.add_data_source(passive_sink_2)

# Удаление источника
data_access.remove_data_source(passive_sink_1)
```

### Получение raw данных с фильтрами

```python
# Получение всех данных
all_data = data_access.get_raw_data()

# Фильтрация по источнику
source_data = data_access.get_raw_data(source_filter="environment")

# Фильтрация по типу события
event_data = data_access.get_raw_data(event_type_filter="noise")

# Фильтрация по времени (последние 5 минут)
recent_data = data_access.get_raw_data(time_window=300.0)

# Комбинированная фильтрация с лимитом
filtered_data = data_access.get_raw_data(
    source_filter="consciousness",
    event_type_filter="insight",
    time_window=600.0,
    limit=100
)
```

**Обновление логики получения данных (2026-01-22):**
Метод `get_raw_data()` теперь сначала получает все доступные данные от источников, а затем применяет лимит. Это обеспечивает более предсказуемое поведение при работе с множественными источниками данных.

### Получение данных за временной интервал

```python
# Получение данных за последние 10 минут
recent_data = data_access.get_data_by_time_window(time_window_seconds=600)
```

### Экспорт данных

```python
# Экспорт в JSON (по умолчанию)
json_file = data_access.export_data(filepath="export.json")

# Экспорт в JSONL
jsonl_file = data_access.export_data(format_type="jsonl", filepath="export.jsonl")

# Экспорт в CSV
csv_file = data_access.export_data(format_type="csv", filepath="export.csv")

# Экспорт с фильтрами
filtered_export = data_access.export_data(
    format_type="json",
    source_filter="environment",
    time_window=3600.0,
    filepath="environment_last_hour.json"
)
```

### Анализ распределения

```python
# Распределение по типам событий
event_distribution = data_access.get_event_type_distribution()
print("Распределение событий:")
for event_type, count in event_distribution.items():
    print(f"  {event_type}: {count}")

# Распределение по источникам
source_distribution = data_access.get_source_distribution()
print("Распределение источников:")
for source, count in source_distribution.items():
    print(f"  {source}: {count}")
```

### Итерация по данным батчами

```python
# Итерация батчами по 50 записей
for batch in data_access.iterate_data(chunk_size=50):
    print(f"Обработка батча из {len(batch)} записей")
    # Обработка батча данных
```

### Сводная информация

```python
# Получение сводной статистики
summary = data_access.get_data_summary()

print(f"Всего записей: {summary['total_records']}")
print(f"Источники: {summary['sources']}")
print(f"Типы событий: {summary['event_types']}")
if summary['time_range']:
    tr = summary['time_range']
    print(f"Временной диапазон: {tr['oldest']} - {tr['newest']} ({tr['duration']:.1f} сек)")
```

## Работа с mock объектами

RawDataAccess поддерживает работу с mock объектами для тестирования:

```python
from unittest.mock import MagicMock
from src.observability.raw_data_access import RawDataAccess

# Создание mock источника
mock_source = MagicMock()
mock_source.get_recent_data.return_value = [
    ObservationData(timestamp=1000.0, event_type="test", data={"value": 1}, source="mock")
]

# Добавление mock источника
data_access.add_data_source(mock_source)

# Получение данных из mock
data = data_access.get_raw_data()
assert len(data) == 1
assert data[0].event_type == "test"
```

## Примеры использования

### Мониторинг системы в реальном времени

```python
from src.observability.raw_data_access import RawDataAccess
import time

# Создание компонента для мониторинга
monitor = RawDataAccess()

# Добавление всех доступных источников
for sink in [async_sink, passive_sink, custom_sink]:
    monitor.add_data_source(sink)

# Мониторинг последних 5 минут
while True:
    recent_data = monitor.get_data_by_time_window(300.0)

    # Анализ активности
    event_types = monitor.get_event_type_distribution()
    total_events = sum(event_types.values())

    print(f"Активность за 5 мин: {total_events} событий")
    print(f"Типы событий: {event_types}")

    time.sleep(60)  # Проверка каждую минуту
```

### Экспорт данных для анализа

```python
from src.observability.raw_data_access import RawDataAccess

# Создание компонента для экспорта
exporter = RawDataAccess()

# Добавление источников
exporter.add_data_source(data_sink)

# Экспорт данных разных типов событий за последний час
for event_type in ["noise", "decay", "recovery", "insight"]:
    filename = f"{event_type}_last_hour.jsonl"
    exporter.export_data(
        format_type="jsonl",
        event_type_filter=event_type,
        time_window=3600.0,
        filepath=filename
    )
    print(f"Экспортировано {event_type} в {filename}")
```

### Агрегация данных из нескольких источников

```python
from src.observability.raw_data_access import RawDataAccess

# Создание агрегатора
aggregator = RawDataAccess()

# Добавление множественных источников
sources = ["environment", "consciousness", "memory", "learning"]
for source_name in sources:
    # Получение соответствующего sink для каждого источника
    sink = get_sink_for_source(source_name)
    aggregator.add_data_source(sink)

# Получение агрегированной статистики
summary = aggregator.get_data_summary()
print("Агрегированная статистика:")
print(f"- Всего источников: {len(summary['sources'])}")
print(f"- Всего записей: {summary['total_records']}")
print(f"- Уникальных типов событий: {len(summary['event_types'])}")

# Экспорт всех данных
aggregator.export_data(filepath="aggregated_data.json")
```

## Интеграция с тестами

RawDataAccess разработан с учетом совместимости с тестами:

```python
import pytest
from src.observability.raw_data_access import RawDataAccess
from unittest.mock import MagicMock

@pytest.fixture
def mock_data_access():
    """Фикстура для тестирования RawDataAccess."""
    access = RawDataAccess()

    # Создание mock источников
    mock_sink = MagicMock()
    mock_sink.get_entries.return_value = [
        ObservationData(1000.0, "test_event", {"data": "test"}, "mock_source")
    ]

    access.add_data_source(mock_sink)
    return access

def test_get_raw_data(mock_data_access):
    """Тест получения raw данных."""
    data = mock_data_access.get_raw_data()
    assert len(data) == 1
    assert data[0].event_type == "test_event"

def test_export_formats(mock_data_access):
    """Тест экспорта в различные форматы."""
    # JSON экспорт
    json_file = mock_data_access.export_data(format_type="json")
    assert json_file.endswith(".json")

    # CSV экспорт
    csv_file = mock_data_access.export_data(format_type="csv")
    assert csv_file.endswith(".csv")
```

## Производительность и оптимизации

### Эффективная работа с большими объемами данных

```python
# Использование итератора для обработки больших объемов
data_access = RawDataAccess()
data_access.add_data_source(large_data_sink)

# Обработка батчами для предотвращения перегрузки памяти
processed_count = 0
for batch in data_access.iterate_data(chunk_size=1000):
    # Обработка батча
    process_batch(batch)
    processed_count += len(batch)
    print(f"Обработано: {processed_count} записей")
```

### Оптимизированные фильтры

```python
# Эффективная фильтрация по нескольким критериям
filtered_data = data_access.get_raw_data(
    source_filter="environment",    # Фильтр по источнику
    event_type_filter="noise",      # Фильтр по типу
    time_window=3600.0,             # Временное окно
    limit=1000                      # Ограничение количества
)
```

## Будущие улучшения

1. **Кэширование данных** - Добавление опционального кэширования для часто запрашиваемых данных
2. **Расширенные фильтры** - Поддержка сложных запросов с логическими операторами
3. **Потоковая обработка** - Поддержка real-time потоков данных
4. **Метрики производительности** - Добавление метрик для анализа эффективности запросов
5. **Компрессия экспорта** - Поддержка сжатых форматов экспорта