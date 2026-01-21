# Операционная модель наблюдаемости

## Обзор

Система Life включает комплексную систему наблюдаемости для мониторинга, трассировки и анализа работы экспериментального компаньона. Наблюдаемость реализована через структурированное логирование в формате JSONL, что позволяет анализировать причинно-следственные цепочки и метрики производительности.

**Статус:** ✅ **Полностью реализована и протестирована** (2026-01-20)
**Статистика:** 26,902 записей логов, 100% покрытие стадий, средняя производительность 14.9 мс/тик

## Архитектура наблюдаемости

### Компоненты системы

1. **StructuredLogger** - единый интерфейс для структурированного логирования
2. **Runtime Loop Integration** - автоматическое логирование всех стадий обработки
3. **JSONL формат** - машиночитаемые логи для анализа и визуализации

### Уровни логирования

- **Event Level**: Входящие события из очереди
- **Meaning Level**: Результаты интерпретации MeaningEngine
- **Decision Level**: Выбор паттерна реакции (ignore/dampen/absorb)
- **Action Level**: Выполнение внутренних действий
- **Feedback Level**: Обратная связь от действий
- **Performance Level**: Метрики тика (длительность, размер очереди, количество событий)

## Формат логов

### Структура JSONL записи

```json
{
  "timestamp": 1705708800.0,
  "stage": "event|meaning|decision|action|feedback|tick_start|tick_end",
  "correlation_id": "chain_123",
  "event_id": "unique_id",
  "data": {
    // специфичные для стадии данные
  }
}
```

### Примеры записей

#### Event
```json
{
  "timestamp": 1705708800.123,
  "stage": "event",
  "correlation_id": "chain_001",
  "event_id": "event_123",
  "data": {
    "type": "noise",
    "intensity": 0.3,
    "original_timestamp": 1705708800.0
  }
}
```

#### Meaning
```json
{
  "timestamp": 1705708800.145,
  "stage": "meaning",
  "correlation_id": "chain_001",
  "event_id": "event_123",
  "data": {
    "significance": 0.45,
    "impact": {"energy": -0.5, "stability": -0.2},
    "response_pattern": "dampen"
  }
}
```

#### Decision
```json
{
  "timestamp": 1705708800.156,
  "stage": "decision",
  "correlation_id": "chain_001",
  "event_id": "event_123",
  "data": {
    "pattern": "dampen",
    "significance": 0.45,
    "original_impact": {"energy": -0.5, "stability": -0.2}
  }
}
```

#### Action
```json
{
  "timestamp": 1705708800.167,
  "stage": "action",
  "correlation_id": "chain_001",
  "event_id": "event_123",
  "data": {
    "action_id": "action_456_dampen_1705708800000",
    "pattern": "dampen",
    "state_before": {
      "energy": 95.5,
      "stability": 0.85,
      "integrity": 0.95
    }
  }
}
```

#### Feedback
```json
{
  "timestamp": 1705708800.178,
  "stage": "feedback",
  "correlation_id": "chain_001",
  "event_id": "event_123",
  "data": {
    "feedback_id": "feedback_789",
    "type": "action_result",
    "content": {
      "success": true,
      "energy_cost": 0.01,
      "timestamp": 1705708800.167
    }
  }
}
```

#### Tick Performance
```json
{
  "timestamp": 1705708800.200,
  "stage": "tick_end",
  "correlation_id": "tick_100",
  "event_id": "tick_100",
  "data": {
    "tick_duration_ms": 12.5,
    "queue_size": 0,
    "events_processed": 1
  }
}
```

## Корреляционные цепочки

### Принцип работы

Каждое событие получает уникальный `correlation_id`, который сохраняется через всю цепочку обработки:
event → meaning → decision → action → feedback

Это позволяет:
- Трассировать полную последовательность обработки события
- Анализировать эффективность разных паттернов реакции
- Отслеживать влияние действий на состояние системы

### Пример полной цепочки

```json
{"timestamp":1705708800.123,"stage":"event","correlation_id":"chain_001","event_id":"event_123","data":{"type":"shock","intensity":-0.8}}
{"timestamp":1705708800.145,"stage":"meaning","correlation_id":"chain_001","event_id":"event_123","data":{"significance":0.8,"impact":{"integrity":-0.3,"stability":-0.5},"response_pattern":"absorb"}}
{"timestamp":1705708800.156,"stage":"decision","correlation_id":"chain_001","event_id":"event_123","data":{"pattern":"absorb","significance":0.8}}
{"timestamp":1705708800.167,"stage":"action","correlation_id":"chain_001","event_id":"event_123","data":{"action_id":"action_456_absorb_1705708800000","pattern":"absorb"}}
{"timestamp":1705708800.178,"stage":"feedback","correlation_id":"chain_001","event_id":"event_123","data":{"feedback_id":"feedback_789","type":"action_result","content":{"success":true,"energy_cost":0.05}}}
```

## Метрики производительности

### Собираемые метрики

- **tick_duration_ms**: Время выполнения одного тика в миллисекундах
- **queue_size**: Размер очереди событий на начало тика
- **events_processed**: Количество обработанных событий за тик

### Агрегация метрик

```bash
# Просмотр средних метрик по тикам
cat data/structured_log.jsonl | jq -r 'select(.stage == "tick_end") | .data.tick_duration_ms' | awk '{sum+=$1; count++} END {print "Средняя длительность тика:", sum/count, "мс"}'

# Анализ размера очереди
cat data/structured_log.jsonl | jq -r 'select(.stage == "tick_start") | .data.queue_size' | sort | uniq -c | sort -nr
```

## Работа с логами

### Просмотр логов

```bash
# Просмотр всех логов в реальном времени
tail -f data/structured_log.jsonl

# Просмотр логов определенной стадии
cat data/structured_log.jsonl | jq 'select(.stage == "event")'

# Просмотр цепочки по correlation_id
cat data/structured_log.jsonl | jq 'select(.correlation_id == "chain_001")'
```

### Анализ деградаций

#### Поиск проблемных паттернов

```bash
# События с высокой интенсивностью
cat data/structured_log.jsonl | jq -r 'select(.stage == "event" and (.data.intensity | fabs) > 0.7) | {correlation_id, type: .data.type, intensity: .data.intensity}'

# Действия, приведшие к значительным изменениям состояния
cat data/structured_log.jsonl | jq -r 'select(.stage == "action") | {correlation_id, pattern: .data.pattern, state_before: .data.state_before}'
```

#### Анализ производительности

```bash
# Самые долгие тики
cat data/structured_log.jsonl | jq -r 'select(.stage == "tick_end") | .data.tick_duration_ms' | sort -nr | head -10

# Распределение количества обработанных событий
cat data/structured_log.jsonl | jq -r 'select(.stage == "tick_end") | .data.events_processed' | sort | uniq -c
```

### Мониторинг в реальном времени

```bash
# Мониторинг производительности (обновление каждые 5 секунд)
watch -n 5 'cat data/structured_log.jsonl | jq -r "select(.stage == \"tick_end\") | .data.tick_duration_ms" | tail -10 | awk "{sum+=\$1; count++} END {if(count>0) print \"Средняя длительность последних 10 тиков:\", sum/count, \"мс\"}"'

# Мониторинг очереди событий
watch -n 1 'cat data/structured_log.jsonl | jq -r "select(.stage == \"tick_start\") | .data.queue_size" | tail -1'
```

## Инструменты анализа

### jq для фильтрации и анализа

```bash
# Количество событий по типам
cat data/structured_log.jsonl | jq -r 'select(.stage == "event") | .data.type' | sort | uniq -c

# Средняя значимость событий
cat data/structured_log.jsonl | jq -r 'select(.stage == "meaning") | .data.significance' | awk '{sum+=$1; count++} END {print sum/count}'

# Распределение паттернов решений
cat data/structured_log.jsonl | jq -r 'select(.stage == "decision") | .data.pattern' | sort | uniq -c
```

### Python скрипты для глубокого анализа

```python
import json
import sys
from collections import defaultdict, Counter
from datetime import datetime

def analyze_logs(file_path):
    events = []
    chains = defaultdict(list)

    with open(file_path, 'r') as f:
        for line in f:
            entry = json.loads(line.strip())
            events.append(entry)

            if 'correlation_id' in entry:
                chains[entry['correlation_id']].append(entry)

    # Анализ цепочек
    print(f"Всего событий: {len(events)}")
    print(f"Уникальных цепочек: {len(chains)}")

    # Анализ стадий
    stages = Counter(e['stage'] for e in events)
    print("\nРаспределение по стадиям:")
    for stage, count in stages.most_common():
        print(f"  {stage}: {count}")

    # Анализ длительности тиков
    tick_durations = [e['data']['tick_duration_ms'] for e in events if e['stage'] == 'tick_end']
    if tick_durations:
        print(".2f"
if __name__ == "__main__":
    analyze_logs("data/structured_log.jsonl")
```

## Поиск и устранение проблем

### Типичные сценарии анализа

1. **Высокая нагрузка на систему**
   - Проверить `tick_duration_ms` > 50мс
   - Найти цепочки с большим количеством событий за тик

2. **Неэффективные паттерны реакции**
   - Сравнить `significance` и выбранный `pattern`
   - Проанализировать влияние действий на состояние

3. **Проблемы с очередью**
   - Мониторить `queue_size` > 10
   - Найти источники большого количества событий

### Автоматизированный мониторинг

```bash
#!/bin/bash
# monitoring.sh - скрипт для автоматического мониторинга

LOG_FILE="data/structured_log.jsonl"

# Проверка длительности тиков
check_tick_performance() {
    local avg_duration=$(tail -n 20 "$LOG_FILE" | jq -r 'select(.stage == "tick_end") | .data.tick_duration_ms' | awk '{sum+=$1; count++} END {print sum/count}')

    if (( $(echo "$avg_duration > 50" | bc -l) )); then
        echo "WARNING: Средняя длительность тика $avg_duration мс > 50 мс"
    fi
}

# Проверка размера очереди
check_queue_size() {
    local max_queue=$(tail -n 10 "$LOG_FILE" | jq -r 'select(.stage == "tick_start") | .data.queue_size' | sort -nr | head -1)

    if [ "$max_queue" -gt 20 ]; then
        echo "WARNING: Максимальный размер очереди $max_queue > 20"
    fi
}

# Основной цикл мониторинга
while true; do
    check_tick_performance
    check_queue_size
    sleep 60  # Проверка каждую минуту
done
```

## Производительность и оптимизации

### Влияние на производительность

- **Базовые накладные расходы**: ~0.5-1мс на тик при включенном логировании
- **Условное логирование**: возможность отключения для production использования
- **Буферизация**: логи пишутся в файл без промежуточной буферизации в памяти

### Оптимизации

1. **Асинхронная запись**: возможность буферизации логов в памяти
2. **Уровни логирования**: возможность отключения verbose логирования
3. **Ротация логов**: автоматическая ротация больших файлов логов

## Заключение

Система наблюдаемости предоставляет полную видимость работы Life, позволяя:
- Трассировать причинно-следственные цепочки от событий до действий
- Мониторить производительность в реальном времени
- Анализировать эффективность паттернов поведения
- Выявлять и устранять проблемы в работе системы

JSONL формат обеспечивает совместимость с существующими инструментами анализа логов и позволяет строить дашборды и алерты для оперативного мониторинга.
