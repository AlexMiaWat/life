# UnifiedObservationAPI

## Обзор

`UnifiedObservationAPI` - единая точка входа для пассивного наблюдения системы Life. Объединяет все компоненты наблюдения в унифицированный интерфейс с четким API.

## Архитектура

API построен на композиции следующих компонентов:

- **PassiveDataSink** - пассивный прием данных
- **RawDataCollector** - сбор сырых счетчиков
- **StructuredLogger** - структурированное логирование
- **RawDataAccess** - доступ к историческим данным

## Инициализация

```python
from src.observability import UnifiedObservationAPI
from src.config.observability_config import get_observability_config

# Использование конфигурации из файла
observer = UnifiedObservationAPI()

# Или с кастомной конфигурацией
config = get_observability_config()
observer = UnifiedObservationAPI(config=config)

# Или с override настроек
observer = UnifiedObservationAPI(
    data_directory="custom_data",
    logs_directory="custom_logs",
    structured_log_file="custom_logs/structured.jsonl",
    enabled=True
)
```

## Конфигурация

API использует конфигурацию из `config/observability.yaml`. Основные параметры:

```yaml
observability:
  enabled: true
  data_directory: "data"
  logs_directory: "logs"

structured_logging:
  enabled: true
  log_file: "data/structured_log.jsonl"

passive_data_sink:
  enabled: true
  data_directory: "data"

raw_data_collector:
  logs_directory: "logs"
  snapshots_directory: "data/snapshots"
```

## Основные методы

### Пассивный прием данных

```python
# Прием точки данных
success = observer.accept_data_point({
    "timestamp": time.time(),
    "type": "custom_event",
    "data": {"value": 42}
})

# Прием данных снимка состояния
success = observer.accept_snapshot_data({
    "timestamp": time.time(),
    "energy": 0.8,
    "memory": {"entries": 150}
})
```

### Структурированное логирование

```python
# Логирование события
correlation_id = observer.log_event(event_object)

# Логирование стадий обработки
observer.log_meaning(event, meaning, correlation_id)
observer.log_decision(correlation_id)
observer.log_action("action_123", correlation_id)
observer.log_feedback(feedback, correlation_id)

# Логирование тиков для метрик производительности
observer.log_tick_start(tick_number=100, queue_size=5)
observer.log_tick_end(tick_number=100, duration_ms=15.7, events_processed=3)

# Логирование ошибок
observer.log_error("meaning_processing", exception, correlation_id)
```

### Сбор сырых данных

```python
# Сбор счетчиков из логов
report = observer.collect_raw_counters_from_logs(
    start_time=time.time() - 3600,  # последний час
    end_time=time.time()
)

# Сбор счетчиков из снимков
report = observer.collect_raw_counters_from_snapshots([
    Path("data/snapshots/snapshot_001.json"),
    Path("data/snapshots/snapshot_002.json")
])

# Сохранение отчета
output_path = observer.save_raw_data_report(report, Path("reports/raw_data.json"))
```

### Доступ к данным

```python
# Получение сырых данных наблюдений
observations = observer.get_raw_observation_data(hours=24)

# Получение последнего снимка
latest_snapshot = observer.get_raw_snapshot_data()

# Экспорт всех данных
export_path = observer.export_raw_data(hours=24, output_path=Path("export.json"))
```

## Управление и статус

```python
# Получение полного статуса системы
status = observer.get_status()
# {
#   "enabled": true,
#   "data_directory": "data",
#   "components": {
#     "data_sink": {...},
#     "data_access": {...},
#     "structured_logger": {...}
#   },
#   "timestamp": 1704327000.0
# }

# Быстрый статус для мониторинга
quick_status = observer.quick_status_report()

# Включение/отключение наблюдения
observer.enable()
observer.disable()
```

## Экстренная диагностика

```python
# Экстренный сбор данных для диагностики проблем
emergency_data = observer.emergency_data_collection()
# Содержит последние счетчики, наблюдения и статус системы
```

## Конфигурация

Все пути и настройки можно конфигурировать:

```python
# Через конструктор
api = UnifiedObservationAPI(
    data_directory="data",           # Директория для данных
    logs_directory="logs",          # Директория с логами
    snapshots_directory="data/snapshots",  # Директория со снимками
    structured_log_file="data/structured_log.jsonl",  # Файл структурированных логов
    enabled=True                    # Включено ли наблюдение
)
```

## Обработка ошибок

API реализует graceful degradation:

- При недоступности логов возвращает пустые счетчики
- При ошибках записи продолжает работу
- Все методы возвращают безопасные значения при ошибках
- Подробные логи ошибок для диагностики

## Примеры использования

### Полный цикл наблюдения

```python
from src.observability import UnifiedObservationAPI

# Инициализация
observer = UnifiedObservationAPI()

# Логирование события
event = {"type": "shock", "intensity": 0.8, "data": {}}
correlation_id = observer.log_event(event)

# Логирование обработки
observer.log_meaning(event, meaning_object, correlation_id)
observer.log_decision("absorb", correlation_id)

# Сбор статистики
report = observer.collect_raw_counters_from_logs()
print(f"Events processed: {report.raw_counters.event_count}")

# Экспорт данных
observer.export_raw_data(hours=1, output_path=Path("hourly_report.json"))
```

### Мониторинг производительности

```python
# В runtime loop
tick_start = time.time()

# ... обработка тика ...

tick_duration = (time.time() - tick_start) * 1000
observer.log_tick_end(current_tick, tick_duration, events_processed)
```

## Миграция с отдельных компонентов

Если вы использовали отдельные компоненты:

```python
# Старый код
data_sink = PassiveDataSink()
logger = StructuredLogger()
collector = RawDataCollector()

# Новый код
observer = UnifiedObservationAPI()
# Все методы доступны через observer.*
```

## Тестирование

```python
# Создание тестового экземпляра
test_observer = UnifiedObservationAPI(
    data_directory="test_data",
    enabled=True
)

# Тестирование функциональности
assert test_observer.accept_data_point({"test": "data"})
status = test_observer.get_status()
assert status["enabled"] == True
```