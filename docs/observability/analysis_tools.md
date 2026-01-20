# Инструменты анализа структурированных логов

## Обзор

Система структурированного логирования Life генерирует JSONL логи, которые можно анализировать различными инструментами. Этот документ описывает основные подходы и инструменты для анализа логов.

## Основные инструменты

### 1. jq - Командная строка

`jq` - мощный инструмент для обработки JSON в командной строке.

#### Основные команды

```bash
# Просмотр логов в реальном времени
tail -f data/structured_log.jsonl | jq '.'

# Фильтрация по стадии
cat data/structured_log.jsonl | jq 'select(.stage == "event")'

# Фильтрация по типу события
cat data/structured_log.jsonl | jq 'select(.stage == "event" and .data.type == "shock")'

# Извлечение метрик производительности
cat data/structured_log.jsonl | jq -r 'select(.stage == "tick_end") | .data.tick_duration_ms'

# Поиск по correlation_id
cat data/structured_log.jsonl | jq 'select(.correlation_id == "chain_001")'

# Сортировка по времени
cat data/structured_log.jsonl | jq -s 'sort_by(.timestamp)[]'
```

#### Аналитические запросы

```bash
# Статистика по стадиям
cat data/structured_log.jsonl | jq -r '.stage' | sort | uniq -c | sort -nr

# Средняя длительность тика
cat data/structured_log.jsonl | jq -r 'select(.stage == "tick_end") | .data.tick_duration_ms' | awk '{sum+=$1; count++} END {if(count>0) print "Среднее:", sum/count, "мс"}'

# Распределение паттернов решений
cat data/structured_log.jsonl | jq -r 'select(.stage == "decision") | .data.pattern' | sort | uniq -c | sort -nr

# Анализ событий по типам
cat data/structured_log.jsonl | jq -r 'select(.stage == "event") | .data.type' | sort | uniq -c | sort -nr
```

### 2. Python скрипты

#### Базовый анализ

```python
import json
from collections import Counter, defaultdict
from datetime import datetime
import statistics

def analyze_logs(log_path="data/structured_log.jsonl"):
    """Анализ структурированных логов"""

    stages = Counter()
    correlations = defaultdict(list)
    tick_durations = []
    event_types = Counter()
    patterns = Counter()

    with open(log_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            try:
                entry = json.loads(line.strip())

                # Подсчет стадий
                stages[entry['stage']] += 1

                # Группировка по correlation_id
                if 'correlation_id' in entry:
                    correlations[entry['correlation_id']].append(entry)

                # Сбор метрик производительности
                if entry['stage'] == 'tick_end' and 'data' in entry:
                    if 'tick_duration_ms' in entry['data']:
                        tick_durations.append(entry['data']['tick_duration_ms'])

                # Анализ событий
                if entry['stage'] == 'event' and 'data' in entry:
                    if 'type' in entry['data']:
                        event_types[entry['data']['type']] += 1

                # Анализ решений
                if entry['stage'] == 'decision' and 'data' in entry:
                    if 'pattern' in entry['data']:
                        patterns[entry['data']['pattern']] += 1

            except json.JSONDecodeError as e:
                print(f"Ошибка парсинга строки {line_num}: {e}")
                continue

    return {
        'stages': dict(stages),
        'total_correlations': len(correlations),
        'tick_stats': {
            'count': len(tick_durations),
            'mean': statistics.mean(tick_durations) if tick_durations else 0,
            'median': statistics.median(tick_durations) if tick_durations else 0,
            'min': min(tick_durations) if tick_durations else 0,
            'max': max(tick_durations) if tick_durations else 0
        },
        'event_types': dict(event_types),
        'decision_patterns': dict(patterns)
    }

if __name__ == "__main__":
    results = analyze_logs()
    print("=== АНАЛИЗ СТРУКТУРИРОВАННЫХ ЛОГОВ ===")
    print(f"Всего записей: {sum(results['stages'].values())}")
    print(f"Стадии: {results['stages']}")
    print(f"Корреляционных цепочек: {results['total_correlations']}")

    stats = results['tick_stats']
    print(".2f"
          ".2f"
          ".2f"
          ".2f")

    print(f"Типы событий: {results['event_types']}")
    print(f"Паттерны решений: {results['decision_patterns']}")
```

#### Анализ цепочек обработки

```python
def analyze_correlation_chains(log_path="data/structured_log.jsonl"):
    """Анализ полных цепочек обработки по correlation_id"""

    chains = defaultdict(list)

    # Сбор всех записей по correlation_id
    with open(log_path, 'r') as f:
        for line in f:
            entry = json.loads(line.strip())
            if 'correlation_id' in entry:
                chains[entry['correlation_id']].append(entry)

    # Сортировка записей в каждой цепочке по времени
    for chain_id, entries in chains.items():
        chains[chain_id] = sorted(entries, key=lambda x: x['timestamp'])

    # Анализ цепочек
    chain_analysis = {}
    stage_order = ['event', 'meaning', 'decision', 'action', 'feedback']

    for chain_id, entries in chains.items():
        # Проверка полноты цепочки
        stages_present = set(entry['stage'] for entry in entries)
        completeness = len(stages_present.intersection(stage_order)) / len(stage_order)

        # Вычисление времени обработки цепочки
        if entries:
            start_time = min(entry['timestamp'] for entry in entries)
            end_time = max(entry['timestamp'] for entry in entries)
            duration = end_time - start_time
        else:
            duration = 0

        chain_analysis[chain_id] = {
            'stages': sorted(stages_present),
            'completeness': completeness,
            'duration': duration,
            'entry_count': len(entries)
        }

    return chain_analysis

def print_chain_analysis():
    """Вывод анализа цепочек"""
    chains = analyze_correlation_chains()

    print("=== АНАЛИЗ ЦЕПОЧЕК ОБРАБОТКИ ===")
    print(f"Всего цепочек: {len(chains)}")

    # Статистика полноты
    completeness_values = [info['completeness'] for info in chains.values()]
    print(".2%")

    # Статистика длительности
    durations = [info['duration'] for info in chains.values() if info['duration'] > 0]
    if durations:
        print(".2f")
        print(".2f")

    # Примеры цепочек
    print("\nПримеры полных цепочек:")
    complete_chains = [(cid, info) for cid, info in chains.items()
                      if info['completeness'] >= 0.8]

    for chain_id, info in complete_chains[:5]:  # Показать первые 5
        print(f"  {chain_id}: stages={info['stages']}, duration={info['duration']:.3f}s")

if __name__ == "__main__":
    print_chain_analysis()
```

### 3. Веб-интерфейс для анализа (предложение)

Для продвинутого анализа можно создать простой веб-интерфейс:

```python
# analysis_server.py - простой веб-сервер для анализа логов
from flask import Flask, jsonify, render_template
import json
from collections import Counter, defaultdict
import statistics

app = Flask(__name__)

def load_log_data():
    """Загрузка и предварительная обработка данных логов"""
    data = []
    with open('data/structured_log.jsonl', 'r') as f:
        for line in f:
            data.append(json.loads(line.strip()))
    return data

@app.route('/')
def dashboard():
    """Главная страница дашборда"""
    data = load_log_data()

    # Базовая статистика
    stages = Counter(entry['stage'] for entry in data)
    tick_durations = [entry['data']['tick_duration_ms']
                     for entry in data
                     if entry['stage'] == 'tick_end' and 'tick_duration_ms' in entry.get('data', {})]

    stats = {
        'total_entries': len(data),
        'stages': dict(stages),
        'avg_tick_duration': statistics.mean(tick_durations) if tick_durations else 0,
        'total_chains': len(set(entry.get('correlation_id', '')
                               for entry in data if 'correlation_id' in entry))
    }

    return render_template('dashboard.html', stats=stats)

@app.route('/api/chains')
def get_chains():
    """API для получения данных о цепочках"""
    data = load_log_data()
    chains = defaultdict(list)

    for entry in data:
        if 'correlation_id' in entry:
            chains[entry['correlation_id']].append(entry)

    # Анализ цепочек
    chain_data = []
    for chain_id, entries in chains.items():
        stages = [e['stage'] for e in sorted(entries, key=lambda x: x['timestamp'])]
        duration = max(e['timestamp'] for e in entries) - min(e['timestamp'] for e in entries)

        chain_data.append({
            'id': chain_id,
            'stages': stages,
            'duration': duration,
            'count': len(entries)
        })

    return jsonify(chain_data)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
```

## Мониторинг в реальном времени

### Следование за логами

```bash
# Мониторинг новых записей
tail -f data/structured_log.jsonl | jq '.stage + " at " + (.timestamp | strftime("%H:%M:%S"))'

# Мониторинг производительности
tail -f data/structured_log.jsonl | jq -r 'select(.stage == "tick_end") | "Tick \(.data.tick)ms: \(.data.tick_duration_ms)ms"'

# Мониторинг ошибок
tail -f data/structured_log.jsonl | jq 'select(.stage == "error")'
```

### Алёрты и уведомления

```bash
# Алёрт при медленных тиках (>50мс)
tail -f data/structured_log.jsonl | jq -r 'select(.stage == "tick_end" and .data.tick_duration_ms > 50) | "SLOW TICK: \(.data.tick_duration_ms)ms"'

# Алёрт при ошибках
tail -f data/structured_log.jsonl | jq -r 'select(.stage == "error") | "ERROR: \(.data.error)"'
```

## Производительность анализа

### Оптимизации для больших файлов

```bash
# Параллельная обработка с GNU parallel
cat data/structured_log.jsonl | parallel --pipe jq 'select(.stage == "event")' > events.jsonl

# Индексация с помощью jq
jq -c 'select(.correlation_id) | {id: .correlation_id, stage: .stage, ts: .timestamp}' data/structured_log.jsonl > index.jsonl

# Агрегация без загрузки всего файла в память
cat data/structured_log.jsonl | jq -r 'select(.stage == "tick_end") | .data.tick_duration_ms' | awk '{sum+=$1; count++} END {print sum/count}'
```

### Кэширование результатов

```python
import pickle
import os
from pathlib import Path

CACHE_FILE = 'data/log_analysis_cache.pkl'

def get_cached_analysis(log_path="data/structured_log.jsonl"):
    """Получение анализа с кэшированием"""

    log_mtime = os.path.getmtime(log_path)
    cache_mtime = os.path.getmtime(CACHE_FILE) if os.path.exists(CACHE_FILE) else 0

    if log_mtime > cache_mtime:
        # Пересчет анализа
        results = analyze_logs(log_path)

        # Сохранение в кэш
        with open(CACHE_FILE, 'wb') as f:
            pickle.dump({'mtime': log_mtime, 'results': results}, f)

        return results
    else:
        # Загрузка из кэша
        with open(CACHE_FILE, 'rb') as f:
            cached = pickle.load(f)
            return cached['results']
```

## Рекомендации по использованию

1. **Для разработки:** Используйте jq для быстрого анализа и отладки
2. **Для мониторинга:** Настройте алёрты на ключевые метрики
3. **Для исследования:** Используйте Python скрипты для глубокого анализа
4. **Для больших объемов:** Рассмотрите базы данных (Elasticsearch, ClickHouse) для хранения и анализа логов

## Следующие шаги

- **Визуализация цепочек:** Создание графического представления цепочек обработки
- **Автоматическая аналитика:** ML-модели для выявления аномалий
- **Интеграция с мониторингом:** Подключение к системам типа Grafana/Prometheus
- **API для анализа:** REST API для программного доступа к аналитике
