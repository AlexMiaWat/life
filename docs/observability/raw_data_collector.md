# RawDataCollector - Сборщик сырых данных

## Обзор

`RawDataCollector` - компонент для сбора исключительно сырых счетчиков системы Life из логов и снимков состояний. **Не выполняет никакой интерпретации или анализа данных**.

## Архитектурные принципы

### ✅ Чистые raw данные
- **Только счетчики**: cycle_count, error_count, action_count и т.д.
- **Без расчетов**: Нет rate, frequency, efficiency или других derived metrics
- **Без интерпретации**: Только подсчет событий по типам
- **Без паттернов**: Не анализирует поведение или тренды

### ❌ Исключает derived metrics
- event_processing_rate (событий/сек)
- state_change_frequency (изменений/сек)
- learning_effectiveness (эффективность обучения)
- decision_success_rate (успешность решений)
- adaptation_rate (скорость адаптации)
- integrity_score (уровень целостности)

## Структура данных

### RawSystemCounters

```python
@dataclass
class RawSystemCounters:
    """Сырые счетчики состояния системы - только raw данные без интерпретации."""

    timestamp: float = field(default_factory=time.time)

    # Только raw counters - никаких расчетов rate/frequency
    cycle_count: int = 0          # Количество выполненных циклов (тиков)
    uptime_seconds: float = 0.0   # Время работы в секундах
    memory_entries_count: int = 0 # Количество записей в памяти
    error_count: int = 0          # Количество ошибок
    action_count: int = 0         # Количество выполненных действий
    event_count: int = 0          # Количество обработанных событий
    state_change_count: int = 0   # Количество изменений состояния
```

### RawDataReport

```python
@dataclass
class RawDataReport:
    """Отчет с сырыми данными - только counters без интерпретации."""

    observation_period: Tuple[float, float]  # start_time, end_time
    raw_counters: RawSystemCounters

    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать отчет в словарь для сериализации."""
```

## Использование

### Сбор данных из логов

```python
from src.observability import RawDataCollector

# Создание сборщика
collector = RawDataCollector(
    logs_directory=Path("logs"),          # Директория с логами
    snapshots_directory=Path("data/snapshots")  # Директория со снимками
)

# Сбор счетчиков из структурированных логов
report = collector.collect_raw_counters_from_logs(
    start_time=time.time() - 3600,  # Последний час
    end_time=time.time()
)

print(f"Циклы: {report.raw_counters.cycle_count}")
print(f"События: {report.raw_counters.event_count}")
print(f"Ошибки: {report.raw_counters.error_count}")
```

### Сбор данных из снимков

```python
# Сбор счетчиков из снимков состояний
snapshot_paths = [
    Path("data/snapshots/snapshot_001.json"),
    Path("data/snapshots/snapshot_002.json")
]

report = collector.collect_raw_counters_from_snapshots(snapshot_paths)
```

### Сохранение отчета

```python
# Сохранение отчета в файл
output_path = collector.save_raw_data_report(
    report,
    Path("reports/raw_counters_20260122.json")
)
```

## Чтение логов

RawDataCollector читает структурированные логи из `data/structured_log.jsonl` и подсчитывает события по стадиям:

- **event**: Увеличивает `event_count`
- **action**: Увеличивает `action_count`
- **tick_end**: Увеличивает `cycle_count`
- **error_***: Увеличивает `error_count`
- **adaptation_rollback**: Увеличивает `state_change_count`

### Формат логов

```json
{"timestamp": 1704327000.0, "stage": "event", "correlation_id": "chain_123", "event_type": "shock"}
{"timestamp": 1704327010.0, "stage": "action", "correlation_id": "chain_123", "pattern": "dampen"}
{"timestamp": 1704327020.0, "stage": "tick_end", "tick_number": 100, "duration_ms": 15.7}
```

## Чтение снимков

Для снимков состояний извлекаются счетчики из последнего доступного снимка:

```json
{
  "self_state": {
    "ticks": 1500,
    "age": 150.5
  },
  "memory_stats": {
    "total_entries": 250
  }
}
```

## Graceful degradation

При проблемах с чтением данных RawDataCollector:

- Возвращает пустые счетчики (все поля = 0)
- Логирует предупреждения, но не выбрасывает исключения
- Продолжает работу системы без сбоя

## Тестирование

```python
from src.observability import RawDataCollector
import tempfile

# Создание тестового сборщика
with tempfile.TemporaryDirectory() as temp_dir:
    collector = RawDataCollector(logs_directory=Path(temp_dir))

    # Сбор данных (вернет пустые счетчики при отсутствии данных)
    report = collector.collect_raw_counters_from_logs()

    assert report.raw_counters.cycle_count == 0
    assert report.raw_counters.error_count == 0
```

## Миграция с ExternalObserver

ExternalObserver имел derived metrics и анализ паттернов. RawDataCollector:

- Убирает все derived metrics (rate, frequency, effectiveness)
- Убирает анализ паттернов поведения
- Убирает рекомендации и интерпретацию
- Оставляет только чистый подсчет raw counters

```python
# Старый код (ExternalObserver)
observer = ExternalObserver()
report = observer.observe_from_logs(start_time, end_time)
metrics = report.metrics_summary  # Содержал derived metrics

# Новый код (RawDataCollector)
collector = RawDataCollector()
report = collector.collect_raw_counters_from_logs(start_time, end_time)
counters = report.raw_counters  # Только raw counters
```