# Компонент Observability

**Последнее обновление:** 2026-01-22
**Статус:** Только raw counters без derived metrics
**Архитектурное решение:** [ADR 001](decisions/adr_001_passive_observation_boundaries.md)

---

## Обзор

Компонент Observability реализует истинно пассивную систему наблюдения за поведением системы Life. Основан на архитектуре с PassiveDataSink как ядром, обеспечивающим прием данных только при явных вызовах.

**Ключевые принципы:**
- **Истинная пассивность**: система только принимает данные при явных вызовах
- **Только raw counters**: исключительно сырые счетчики без derived metrics
- **Единая точка входа**: UnifiedObservationAPI для всех операций
- **Внешний анализ**: данные для инструментов разработчика, не для автоматизации

## Архитектурные принципы

### 1. Истинная пассивность
- **Нет влияния на производительность**: Компоненты не интегрированы в runtime loop
- **Внешняя интеграция**: Все компоненты работают полностью вне системы Life
- **Опциональность**: Система полностью отключаема без потери функциональности

### 2. Только raw counters
- **Запрещены любые расчеты**: rate, frequency, averages, trends, категоризация
- **Только counters**: исключительно сырые счетчики без агрегации
- **Без интерпретации**: отсутствие какого-либо анализа или выводов

### 3. Внешний анализ
- **Экспорт данных**: Raw данные для внешних инструментов анализа
- **Отдельные инструменты**: любой анализ проводится вне системы Life
- **Без обратной связи**: данные не влияют на поведение системы

## Компоненты системы

### PassiveDataSink
**Файл:** `src/observability/async_passive_observer.py`

Основной компонент истинно пассивного наблюдения. Принимает данные только при явных вызовах `accept_data_point()` и `accept_snapshot_data()`.

**Принципы работы:**
- Полностью пассивен - не имеет фоновых потоков или активного сбора
- Только принимает данные при явных вызовах
- Сохраняет данные в JSONL файлы для последующего анализа
- Не влияет на производительность runtime loop

### RawDataCollector
**Файл:** `src/observability/external_observer.py`

Сборщик исключительно сырых счетчиков из внешних источников (логи, снимки).

**Собираемые данные (только raw counters):**
- `cycle_count`: количество циклов выполнения
- `uptime_seconds`: время работы в секундах
- `memory_entries_count`: количество записей в памяти
- `error_count`: количество ошибок
- `action_count`: количество действий
- `event_count`: количество событий
- `state_change_count`: количество изменений состояния

### UnifiedObservationAPI
**Файл:** `src/observability/unified_observation_api.py`

Единая точка входа для всей системы пассивного наблюдения Life.

**Объединяет компоненты:**
- `PassiveDataSink` - пассивный прием данных
- `RawDataCollector` - сбор сырых счетчиков
- `StructuredLogger` - структурированное логирование (только raw counters)
- `RawDataAccess` - доступ к историческим данным

**Принципы:**
- Единый интерфейс для всех операций наблюдения
- Graceful degradation при ошибках
- Конфигурируемость через YAML
- Полная пассивность системы

### RawDataAccess
**Файл:** `src/observability/developer_reports.py`

Предоставляет доступ к сырым данным наблюдений без какой-либо интерпретации.

**Функциональность:**
- Загрузка raw данных из файлов наблюдений
- Доступ к последнему snapshot
- Экспорт данных в JSON
- Проверка статуса сбора данных

## Архитектурные границы

### ✅ Допустимые паттерны

1. **Внешний сбор данных**
   ```python
   # Чтение существующих snapshot файлов
   snapshot = load_snapshot_from_file()
   ```

2. **Только raw counters**
   ```python
   counters = RawSystemCounters(
       cycle_count=1000,
       error_count=5,
       # Никаких расчетов rate/frequency!
   )
   ```

### ❌ Запрещенные паттерны

1. **Любые расчеты и интерпретация**
   ```python
   # ЗАПРЕЩЕНО: любые derived metrics
   average_events = sum(events) / len(events)  # расчет среднего!
   trend = "increasing"  # интерпретация!
   health_score = calculate_score()  # derived metric!
   ```

2. **Активный сбор данных**
   ```python
   # ЗАПРЕЩЕНО: активный polling
   while True:
       collect_data()  # активный сбор по таймеру!
   ```

3. **Интеграция в runtime**
   ```python
   # ЗАПРЕЩЕНО: влияние на runtime loop
   runtime_loop_with_observability()  # влияет на производительность!
   ```

4. **Обратная связь**
   ```python
   # ЗАПРЕЩЕНО: влияние на поведение
   if observation_data.shows_problem:
       change_system_behavior()
   ```

5. **Анализ и рекомендации**
   ```python
   # ЗАПРЕЩЕНО: интерпретация поведения
   if system_is_learning:
       recommendations = ["увеличить память"]
   ```

## Интеграция

### Полная внешняя интеграция

В соответствии с ADR 001, система observability **полностью исключена** из runtime loop и не имеет никакой интеграции:

```python
# runtime/loop.py - НЕТ компонентов observability
# structured_logger = StructuredLogger()  # Удалено
# technical_monitor = TechnicalBehaviorMonitor()  # Удалено
# data_collection_manager = DataCollectionManager()  # Удалено
```

### Использование внешних инструментов

```python
from src.observability import PassiveDataSink

# Создание пассивного приемника данных
data_sink = PassiveDataSink(data_directory="data", enabled=True)

# Пассивный прием данных (только при явных вызовах)
data_sink.accept_data_point({
    "timestamp": time.time(),
    "event_type": "user_action",
    "action_count": 1
})

# Прием данных снимка состояния
data_sink.accept_snapshot_data({
    "timestamp": time.time(),
    "memory_entries_count": 150,
    "cycle_count": 1000
})
```

## Использование данных

### Доступ к пассивно собранным данным

```python
from src.observability.developer_reports import RawDataAccess

# Создание экземпляра для доступа к данным
data_access = RawDataAccess()

# Получение пассивно собранных наблюдений
observations = data_access.get_raw_observation_data(hours=24)

# Получение последнего snapshot
latest_snapshot = data_access.get_raw_snapshot_data()

# Экспорт данных для внешнего анализа
data_access.export_raw_data(hours=24, output_path="raw_data_export.json")
```

### Единое API для пассивного наблюдения

```python
from src.observability import UnifiedObservationAPI

# Создание единой точки входа
api = UnifiedObservationAPI()

# Пассивный прием данных
api.accept_data_point({"event_type": "user_interaction", "count": 1})

# Структурированное логирование (только raw counters)
api.log_event(some_event)
api.log_tick_end(tick_number=42)  # Только tick_number, без duration_ms!

# Сбор сырых счетчиков из логов
raw_data = api.collect_raw_counters_from_logs()
```

### Только raw counters

Система предоставляет исключительно raw counters без какой-либо интерпретации:

- **Raw счетчики**: только числовые значения (cycle_count, error_count, etc.)
- **Временные метки**: timestamp для каждого наблюдения
- **Внешний анализ**: все интерпретации выполняются внешними инструментами

## Тестирование

### Архитектурные тесты
- **Истинная пассивность**: проверка отсутствия активного сбора данных
- **Только raw counters**: проверка отсутствия derived metrics (duration_ms, etc.)
- **Отсутствие влияния на runtime**: проверка полной внешней интеграции
- **Graceful degradation**: проверка работы при недоступности файлов/директорий

### Функциональные тесты
- **PassiveDataSink**: корректность приема данных при явных вызовах
- **RawDataCollector**: правильность извлечения счетчиков из логов
- **Unified API**: интеграция всех компонентов
- **Data structures**: валидация RawSystemCounters и RawDataReport

## Мониторинг и поддержка

### Метрики использования
- Количество собранных записей
- Размер хранилища данных
- Время работы observer thread

### Логирование
- DEBUG: детали сбора данных
- INFO: статус операций
- WARNING: проблемы с доступом к файлам
- ERROR: критические ошибки

## Риски и ограничения

### Архитектурные ограничения
- **Нет интерпретации**: система не предоставляет анализ или insights
- **Только raw данные**: отсутствие derived metrics или трендов
- **Внешний анализ**: требуется отдельные инструменты для любого анализа

### Надежность
- Graceful degradation при ошибках чтения файлов
- Отсутствие влияния на стабильность системы Life
- Безопасная обработка отсутствующих данных

## Будущие улучшения

### Опционально (очень низкий приоритет)
- Оптимизация чтения больших файлов наблюдений
- Компрессия экспортированных данных
- Интеграция с внешними инструментами анализа (если потребуется)

### Только при необходимости
- Дополнительные raw счетчики (если нужны новые типы counters)
- Оптимизация экспорта для больших объемов данных

---

## Ссылки

- [ADR 001: Границы пассивного наблюдения](decisions/adr_001_passive_observation_boundaries.md)
- [Правила пассивного наблюдения](../concepts/behavior_observation_limits.md)
- [CHANGELOG: История изменений](../../CHANGELOG.md)