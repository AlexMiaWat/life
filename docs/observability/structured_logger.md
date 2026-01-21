# StructuredLogger

## Обзор

`StructuredLogger` - это компонент для структурированного логирования стадий жизненного цикла системы Life. Логирует только факты обработки событий без derived metrics или интерпретации результатов.

**Статус:** 🔄 **Рефакторинг завершен** - убраны derived metrics, только факты обработки

### Изменения в версии 2.0

- ❌ **Убраны derived metrics**: significance, impact, pattern, state_before, delay_ticks
- ✅ **Только факты**: логирование стадий обработки без интерпретации результатов
- ✅ **Чистый API**: упрощенные сигнатуры методов
- ✅ **Raw data only**: подготовка для RawDataCollector

## Расположение

**Файл:** `src/observability/structured_logger.py`

**Инициализация:** Автоматически в `src/runtime/loop.py`

## Архитектура

### Основные компоненты

```python
class StructuredLogger:
    def __init__(self, enabled: bool = True, log_path: str = "data/structured_log.jsonl")
    # ...

    # Методы логирования стадий
    def log_event(self, event) -> str
    def log_meaning(self, event, meaning, correlation_id: str)
    def log_decision(self, pattern: str, correlation_id: str, context: dict)
    def log_action(self, action_id: str, pattern: str, correlation_id: str, state_before: dict)
    def log_feedback(self, feedback, correlation_id: str)

    # Метрики производительности
    def log_tick_start(self, tick: int, queue_size: int)
    def log_tick_end(self, tick: int, duration_ms: float, events_processed: int)

    # Служебные методы
    def log_error(self, error: Exception, correlation_id: str = None)
    def _write_log(self, entry: dict)
```

### Потокобезопасность

- Использование `threading.Lock` для конкурентной записи
- Атомарные операции записи в файл
- Безопасная работа в многопоточной среде runtime loop

## Формат логов

### Общая структура

```json
{
  "timestamp": 1705708800.0,
  "stage": "stage_name",
  "correlation_id": "chain_123",
  "event_id": "unique_id",
  "data": {
    // специфичные для стадии данные
  }
}
```

### Генерация ID

- **correlation_id**: `f"chain_{timestamp}_{random_suffix}"`
- **event_id**: `f"event_{timestamp}_{hash(event)}"`

## Методы логирования

### log_event(event) -> str

Логирует факт получения события (только raw данные события).

```python
correlation_id = logger.log_event(event)
# Возвращает correlation_id для трассировки цепочки
```

**Формат:**
```json
{
  "timestamp": 1705708800.123,
  "stage": "event",
  "correlation_id": "chain_001",
  "event_id": "event_123",
  "event_type": "shock",
  "intensity": 0.8,
  "data": {
    // raw данные события без интерпретации
  }
}
```

### log_meaning(event, meaning, correlation_id)

Логирует факт обработки события MeaningEngine (без результатов интерпретации).

```python
logger.log_meaning(event, meaning, correlation_id)
```

**Формат:**
```json
{
  "timestamp": 1705708800.145,
  "stage": "meaning",
  "correlation_id": "chain_001",
  "event_id": "event_123",
  "event_type": "shock",
  "data": {
    "meaning_type": "Meaning",
    "processed": true
  }
}
```

### log_decision(correlation_id)

Логирует факт принятия решения (без деталей решения).

```python
logger.log_decision(correlation_id)
```

**Формат:**
```json
{
  "timestamp": 1705708800.156,
  "stage": "decision",
  "correlation_id": "chain_001",
  "data": {
    "decision_made": true
  }
}
```

### log_action(action_id, correlation_id)

Логирует факт выполнения действия.

```python
logger.log_action(action_id, correlation_id)
```

**Формат:**
```json
{
  "timestamp": 1705708800.167,
  "stage": "action",
  "correlation_id": "chain_001",
  "action_id": "action_456",
  "data": {
    "action_executed": true
  }
}
```

### log_feedback(feedback, correlation_id)

Логирует факт получения обратной связи (без метрик задержки).

```python
logger.log_feedback(feedback, correlation_id)
```

**Формат:**
```json
{
  "timestamp": 1705708800.178,
  "stage": "feedback",
  "correlation_id": "chain_001",
  "data": {
    "feedback_received": true,
    "feedback_type": "Feedback"
  }
}
```

### Метрики производительности

#### log_tick_start(tick, queue_size)

```python
logger.log_tick_start(current_tick, queue_size)
```

**Формат:**
```json
{
  "timestamp": 1705708800.100,
  "stage": "tick_start",
  "correlation_id": "tick_100",
  "event_id": "tick_100",
  "data": {
    "queue_size": 2
  }
}
```

#### log_tick_end(tick, duration_ms, events_processed)

```python
duration_ms = (time.time() - tick_start_time) * 1000
logger.log_tick_end(current_tick, duration_ms, len(events))
```

**Формат:**
```json
{
  "timestamp": 1705708800.200,
  "stage": "tick_end",
  "correlation_id": "tick_100",
  "event_id": "tick_100",
  "data": {
    "tick_duration_ms": 12.5,
    "events_processed": 1
  }
}
```

## Интеграция в Runtime Loop

### Автоматическое логирование

StructuredLogger интегрирован в `src/runtime/loop.py` для автоматического логирования:

```python
# Инициализация
structured_logger = StructuredLogger(enabled=True)

# Логирование тика
structured_logger.log_tick_start(self_state.ticks, queue_size)

# Логирование событий
for event in events:
    correlation_id = structured_logger.log_event(event)
    # ... обработка события ...
    structured_logger.log_meaning(event, meaning, correlation_id)
    structured_logger.log_decision(pattern, correlation_id, context)
    structured_logger.log_action(action_id, pattern, correlation_id, state_before)

# Логирование feedback
for feedback in feedback_records:
    correlation_id = getattr(feedback, "correlation_id", None) or "feedback_chain"
    structured_logger.log_feedback(feedback, correlation_id)

# Завершение тика
tick_duration = (time.time() - tick_start_time) * 1000
structured_logger.log_tick_end(self_state.ticks, tick_duration, len(events))
```

## Конфигурация

### Параметры инициализации

```python
logger = StructuredLogger(
    enabled=True,        # Включение/отключение логирования
    log_path="data/structured_log.jsonl"  # Путь к файлу логов
)
```

### Условное логирование

```python
if self.enabled:
    self._write_log(entry)
```

Позволяет полностью отключать логирование для улучшения производительности.

## Производительность

### Накладные расходы

- **Базовые**: ~0.5-1мс на тик при включенном логировании
- **На событие**: ~0.1-0.2мс на полную цепочку обработки
- **Память**: Минимальные накладные расходы (только текущий буфер записи)

### Оптимизации

1. **Буферизация**: Запись в файл без промежуточных буферов в памяти
2. **Условное выполнение**: Проверка `enabled` перед созданием логов
3. **Минимальный контекст**: Только необходимые данные в логах

## Отладка и тестирование

### Ручное тестирование

```python
from src.observability.structured_logger import StructuredLogger

logger = StructuredLogger(enabled=True)

# Создание тестового события
test_event = {
    "type": "noise",
    "intensity": 0.3,
    "timestamp": time.time()
}

correlation_id = logger.log_event(test_event)
print(f"Logged event with correlation_id: {correlation_id}")
```

### Проверка корректности JSONL

```bash
# Проверка валидности JSON
cat data/structured_log.jsonl | jq empty

# Подсчет записей по стадиям
cat data/structured_log.jsonl | jq -r '.stage' | sort | uniq -c
```

## Расширение

### Добавление новой стадии логирования

1. Добавить метод в `StructuredLogger`
2. Определить формат данных для стадии
3. Интегрировать вызов в соответствующее место runtime loop
4. Обновить документацию

```python
def log_custom_stage(self, custom_data: dict, correlation_id: str):
    """Логирование кастомной стадии"""
    entry = {
        "timestamp": time.time(),
        "stage": "custom_stage",
        "correlation_id": correlation_id,
        "event_id": f"custom_{int(time.time()*1000)}",
        "data": custom_data
    }
    self._write_log(entry)
```

## Ограничения

- **Файловый I/O**: Синхронная запись может блокировать при высокой нагрузке
- **Размер файла**: JSONL файлы могут расти до больших размеров
- **Парсинг**: Требуется специализированные инструменты для анализа

## См. также

- [Operational Model](operational_model.md) - общее описание системы наблюдаемости
- [Runtime Loop](../../components/runtime-loop.md) - интеграция логирования
- [Тестирование](../../testing/) - тесты системы логирования
