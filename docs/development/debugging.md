# Расширенное руководство по отладке и troubleshooting

> **Назначение:** Комплексные инструкции по диагностике проблем, отладке и мониторингу системы Life

## Версии и совместимость

- **Дата последнего обновления:** 2026-01-21
- **Версия системы:** Life v2.1 (субъективное время)
- **Совместимость:** Python 3.8+, pytest 7.0+

## Быстрый старт отладки

### 🚀 5-минутный чек-лист первой диагностики

```bash
# 1. Проверить состояние системы
curl http://localhost:8000/status | jq '.'

# 2. Посмотреть последние логи
tail -20 data/structured_log.jsonl | jq '.stage, .timestamp, .data'

# 3. Проверить память и энергию
curl http://localhost:8000/status | jq '{energy: .energy, integrity: .integrity, stability: .stability, memory_size: (.memory | length)}'

# 4. Запустить быстрый тест системы
python -c "
import sys
sys.path.insert(0, 'src')
from state.self_state import SelfState
state = SelfState()
print(f'✅ Система инициализируется: energy={state.energy}, memory={len(state.memory)}')
"

# 5. Проверить покрытие тестами
pytest src/test/ -q --tb=no -x
```

### 🏗️ Архитектура отладки

```
Система Life
├── 🔍 Мониторинг (Runtime Loop + Console Monitor)
├── 📊 Логирование (StructuredLogger + JSONL файлы)
├── 🧪 Тестирование (pytest + 766+ тестов, 96% покрытие)
├── ⚡ Профилирование (cProfile + Performance Baselines)
├── 🔧 Отладочные скрипты (debug_*.py + analyze_*.py)
└── 📈 Анализ (jq, Python скрипты, отчеты)
```

## 🛠️ Инструменты отладки

### Отладочные скрипты (debug_*.py)

Проект включает специализированные отладочные скрипты для быстрой диагностики:

#### `debug_archive.py` - Диагностика ArchiveMemory
```bash
python debug_archive.py
```
**Что проверяет:**
- Наличие файла `data/archive/memory_archive.json`
- Размер и содержимое архива
- Создание новых экземпляров ArchiveMemory

#### `debug_memory.py` - Отладка Memory компонентов
```bash
python debug_memory.py
```
**Что проверяет:**
- Создание ArchiveMemory с временными файлами
- Размер и содержимое памяти
- Путь к файлу архива

#### `debug_signature.py` - Проверка сигнатур методов
```bash
python debug_signature.py
```
**Что проверяет:**
- Сигнатуру метода `process_statistics` в LearningEngine
- Количество параметров и их типы

#### `debug_temp_archive.py` - Тест ArchiveMemory fixtures
```bash
python debug_temp_archive.py
```
**Что проверяет:**
- Создание ArchiveMemory как в pytest fixtures
- Временные файлы и их очистка

### Скрипты анализа (analyze_*.py)

#### `analyze_test_results.py` - Анализ результатов тестирования
```bash
python analyze_test_results.py
```
**Генерирует отчеты:**
- Статистика тестов (пройдено/провалено/пропущено)
- Детали проваленных тестов
- Статистика по файлам тестов

#### `analyze_test_results_custom.py` - Кастомный анализ тестов
Расширенная версия с дополнительными метриками.

### Скрипты запуска (run_*.py)

#### `run_tests.py` - Автоматизированный запуск тестов
```bash
python run_tests.py
```
**Особенности:**
- XML вывод результатов (`test_results.xml`)
- Таймаут 2 минуты
- Сохранение вывода в `test_execution_output.txt`

#### `run_performance_tests.py` - Запуск performance тестов с регрессиями
```bash
# Стандартный запуск
python run_performance_tests.py

# Обновление baseline
python run_performance_tests.py --update-baseline

# Только отчет
python run_performance_tests.py --report-only
```
**Функциональность:**
- Проверка на регрессии производительности
- Автоматическое обновление baseline значений
- Генерация отчетов в `docs/results/performance_regression_report.md`

### Скрипты профилирования (profile_*.py)

#### `profile_runtime.py` - Профилирование Runtime Loop
```bash
python profile_runtime.py
```
**Что делает:**
- cProfile анализ runtime loop
- Сохранение результатов в `data/runtime_loop_profile_*.prof`
- Топ функций по cumulative time
- Мониторинг на 5 секунд работы

### Утилиты индексации и поиска

#### `Index_code.py` & `Index_docs.py` - Индексация кода и документации
```bash
python Index_code.py  # Индексация исходного кода
python Index_docs.py  # Индексация документации
```

#### `mcp_index.py` & `mcp_search_provider.py` - MCP индексация
Интеграция с Model Context Protocol для поиска и индексации.

### 2. Безопасная отладка

- Не изменяйте состояние системы напрямую (используйте API)
- Используйте dev-режим для быстрого тестирования изменений
- Делайте snapshots перед экспериментами

## Мониторинг состояния

### Консольный вывод

Система выводит состояние в реальном времени:
```
• [00123] age=60.5s energy=98.0 int=1.00 stab=0.99 | sig=0.85 | act=3(0.75) | dec=dampen | act=dampen
```

**Расшифровка:**
- `•` — индикатор тика (мигает)
- `[ticks]` — номер тика
- `age` — время жизни в секундах
- `energy` — уровень энергии
- `int` — integrity (целостность)
- `stab` — stability (стабильность)
- `sig` — significance последнего события
- `act` — активированные воспоминания (количество/макс. значимость)
- `dec` — выбранный паттерн decision
- `act` — выполненное действие

### API мониторинга

```bash
# Текущее состояние
curl http://localhost:8000/status

# Очистка данных для чистого эксперимента
curl http://localhost:8000/clear-data
```

### Логи тиков

Файл: `data/tick_log.jsonl`

Каждая строка содержит полный snapshot состояния на момент тика.

**Анализ логов:**
```bash
# Последние 10 тиков
tail -10 data/tick_log.jsonl

# Поиск ошибок
grep "error\|exception" data/tick_log.jsonl

# Анализ изменений энергии
jq -r '.energy' data/tick_log.jsonl | tail -20
```

## Диагностика компонентов

### Runtime Loop

**Симптомы неисправности:**
- Система не отвечает на API запросы
- Консольный вывод остановился
- Высокая загрузка CPU

**Диагностика:**
```bash
# Проверить, что процесс запущен
ps aux | grep main_server_api

# Проверить логи на ошибки
tail -f data/tick_log.jsonl | grep -i error

# Проверить состояние API
curl http://localhost:8000/status
```

### Memory

**Симптомы проблем:**
- Память не растет при значимых событиях
- Активация возвращает пустой список
- Архив не создается

**Диагностика:**
```bash
# Проверить размер памяти
curl http://localhost:8000/status | jq '.memory | length'

# Проверить архив
ls -la data/archive/
cat data/archive/memory_archive.json | jq '. | length'
```

### Learning/Adaptation

**Симптомы проблем:**
- Параметры не изменяются со временем
- Изменения слишком резкие (> 0.01)
- Параметры выходят за допустимые границы

**Диагностика:**
```bash
# Проверить параметры Learning
curl http://localhost:8000/status | jq '.learning_params'

# Проверить параметры Adaptation
curl http://localhost:8000/status | jq '.adaptation_params'

# Найти изменения в логах
grep "learning_params\|adaptation_params" data/tick_log.jsonl | tail -5
```

### Event Processing

**Симптомы проблем:**
- События не обрабатываются
- Meaning всегда возвращает significance = 0
- Decision всегда выбирает "ignore"

**Диагностика:**
```bash
# Отправить тестовое событие
curl -X POST http://localhost:8000/event \
  -H "Content-Type: application/json" \
  -d '{"type":"shock","intensity":-0.5}'

# Проверить логи на обработку
tail -5 data/tick_log.jsonl | jq '.last_significance, .recent_events'
```

## 🧪 Расширенная система тестирования

### Типы тестов и их применение

#### Статические тесты (Static Tests)
```bash
# Запуск всех статических тестов
pytest -m "static" -v

# Примеры: test_new_functionality_static.py (45 тестов)
pytest src/test/test_new_functionality_static.py -v
```
**Назначение:** Проверка структуры кода без запуска системы

#### Дымовые тесты (Smoke Tests)
```bash
# Запуск дымовых тестов
pytest -m "smoke" -v

# Тесты dev-mode E2E
pytest -m "smoke and e2e and dev_mode" -v
```
**Назначение:** Базовая проверка работоспособности компонентов

#### Интеграционные тесты (Integration Tests)
```bash
# Тесты взаимодействия компонентов
pytest -m "integration" -v

# Тесты Learning + Adaptation
pytest src/test/test_learning_adaptation_integration.py -v
```
**Назначение:** Проверка взаимодействия между модулями

#### Тесты производительности (Performance Tests)
```bash
# Performance тесты с проверкой регрессий
python run_performance_tests.py

# Baseline значения производительности
cat data/performance_baseline.json | jq '.'
```
**Назначение:** Мониторинг производительности и обнаружение регрессий

#### Тесты race conditions
```bash
# Тесты многопоточности
pytest -m "concurrency and race_conditions" -v

# Тесты API /status при нагрузке
pytest src/test/test_status_race_conditions.py -v
```
**Назначение:** Проверка потокобезопасности

### Запуск отдельных тестов

```bash
# Тест конкретного модуля
pytest src/test/test_memory.py -v

# Тест с подробным выводом
pytest src/test/test_runtime_integration.py -v -s

# Тест с реальным сервером
python src/main_server_api.py --dev &
pytest src/test/test_api_integration.py --real-server --server-port 8000 -v
```

### Создание отладочных тестов

```python
def test_debug_memory_growth():
    """Тест роста памяти при значимых событиях."""
    # Создаем состояние с пустой памятью
    state = SelfState()

    # Добавляем значимое событие
    event = Event(type="shock", intensity=-0.8, timestamp=time.time())
    meaning = Meaning(significance=0.9, impact=Impact(energy=-0.1, stability=-0.2, integrity=-0.05))

    # Записываем в память
    memory_entry = MemoryEntry(
        event_type=event.type,
        meaning_significance=meaning.significance,
        timestamp=event.timestamp
    )
    state.memory.append(memory_entry)

    # Проверяем рост памяти
    assert len(state.memory) == 1
    assert state.memory[0].meaning_significance == 0.9
```

## ⚡ Расширенное профилирование производительности

### Система Performance Baselines

Проект включает автоматизированную систему мониторинга производительности с baseline значениями:

```bash
# Просмотр текущих baseline значений
cat data/performance_baseline.json | jq '.'

# Структура baseline файла
{
  "test_memory_append_performance": {
    "baseline": 0.00123,
    "threshold": 0.15,
    "unit": "seconds"
  },
  "test_runtime_loop_ticks_per_second": {
    "baseline": 45.67,
    "threshold": 0.10,
    "unit": "ticks_per_second"
  }
}
```

**Правила работы:**
- ✅ **OK**: Производительность в пределах ±10% от baseline
- 🚨 **РЕГРЕССИЯ**: Ухудшение >10-15% от baseline
- 🔄 **ОБНОВЛЕНИЕ**: Улучшение >20% автоматически обновляет baseline

### Инструменты профилирования

#### cProfile анализ
```bash
# Профилирование runtime loop
python profile_runtime.py

# Анализ результатов профилирования
python -c "
import pstats
stats = pstats.Stats('data/runtime_loop_profile_*.prof')
stats.sort_stats('cumulative').print_stats(20)
"
```

#### Memory profiling
```python
import tracemalloc
import psutil
import os

def profile_memory_usage():
    """Профилирование использования памяти."""
    tracemalloc.start()

    # Ваш код здесь
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024

    current, peak = tracemalloc.get_traced_memory()
    print(f"Current memory: {current / 1024 / 1024:.1f} MB")
    print(f"Peak memory: {peak / 1024 / 1024:.1f} MB")
    print(f"RSS memory: {memory_mb:.1f} MB")

    tracemalloc.stop()
```

### Измерение времени выполнения

```python
import time
from runtime.loop import RuntimeLoop

def profile_tick_performance():
    """Профилирование производительности одного тика."""
    loop = RuntimeLoop(...)

    start_time = time.time()
    loop.tick()
    end_time = time.time()

    tick_duration = end_time - start_time
    print(f"Tick duration: {tick_duration:.4f} seconds")

    # Предупреждение если тик занимает > 1 секунды
    if tick_duration > 1.0:
        print("WARNING: Tick is too slow!")
```

### Анализ потребления памяти

```python
import psutil
import os

def monitor_memory_usage():
    """Мониторинг потребления памяти."""
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"Memory usage: {memory_mb:.1f} MB")

    # Предупреждение если > 100MB
    if memory_mb > 100:
        print("WARNING: High memory usage!")
```

## 🔍 Расширенная диагностика проблем

### Диагностика по симптомам

#### Симптом: Высокое потребление CPU при простое
```bash
# Проверить процессы
ps aux | grep main_server_api

# Посмотреть системные ресурсы
top -p $(pgrep main_server_api)

# Профилирование горячих точек
python -c "
import cProfile
import time
from src.runtime.loop import run_loop
# ... профилирование
"
```

#### Симптом: Память постоянно растет (memory leak)
```bash
# Мониторинг роста памяти
watch -n 5 'ps aux | grep main_server_api | awk "{print \$6/1024 \" MB\"}"'

# Анализ содержимого памяти
curl http://localhost:8000/status | jq '.memory | length'

# Проверка на циклические ссылки
python -c "
import gc
gc.collect()
print(f'Objects after GC: {len(gc.get_objects())}')
"
```

#### Симптом: Система перестает реагировать на события
```bash
# Проверить очередь событий
curl http://localhost:8000/status | jq '.event_queue_size'

# Посмотреть логи обработки событий
tail -20 data/structured_log.jsonl | jq 'select(.stage == "event")'

# Отправить тестовое событие и проследить
curl -X POST http://localhost:8000/event \
  -H "Content-Type: application/json" \
  -d '{"type":"test","intensity":0.1}' \
  -v
```

#### Симптом: Learning/Adaptation не работают
```bash
# Проверить параметры
curl http://localhost:8000/status | jq '{learning: .learning_params, adaptation: .adaptation_params}'

# Посмотреть частоту вызовов
grep -c "learning" data/structured_log.jsonl
grep -c "adaptation" data/structured_log.jsonl

# Проверить логи изменений
tail -50 data/structured_log.jsonl | jq 'select(.stage | contains("learning") or contains("adaptation"))'
```

### Диагностика компонентов системы

#### EventQueue диагностика
```python
from src.environment.event_queue import EventQueue

def diagnose_event_queue():
    """Диагностика проблем с EventQueue."""
    queue = EventQueue()

    # Тест базовой функциональности
    queue.push({"type": "test", "intensity": 0.5})
    assert queue.size() == 1

    # Тест многопоточной работы
    import threading
    results = []

    def worker():
        try:
            event = queue.pop_nowait()
            results.append(f"Got event: {event}")
        except:
            results.append("Queue empty")

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads: t.start()
    for t in threads: t.join()

    print("Results:", results)
```

#### Memory диагностика
```python
from src.memory.memory import ArchiveMemory

def diagnose_memory():
    """Диагностика проблем с памятью."""
    memory = ArchiveMemory()

    # Проверить загрузку
    print(f"Loaded {memory.size()} entries")

    # Проверить сохранение
    test_entry = {
        "event_type": "test",
        "meaning_significance": 0.8,
        "timestamp": time.time()
    }

    initial_size = memory.size()
    memory.append(test_entry)
    memory.flush()

    print(f"Size before: {initial_size}, after: {memory.size()}")
    assert memory.size() == initial_size + 1
```

### Автоматизированная диагностика

#### Диагностический скрипт системы
```python
#!/usr/bin/env python3
"""
Автоматизированная диагностика системы Life
"""

import sys
import requests
import time
from pathlib import Path

def full_system_diagnostic():
    """Полная диагностика системы."""

    issues = []

    # 1. Проверка доступности API
    try:
        response = requests.get("http://localhost:8000/status", timeout=5)
        if response.status_code != 200:
            issues.append(f"API недоступен: HTTP {response.status_code}")
    except Exception as e:
        issues.append(f"Не удалось подключиться к API: {e}")

    # 2. Проверка файлов логов
    log_files = [
        "data/structured_log.jsonl",
        "data/tick_log.jsonl",
        "data/archive/memory_archive.json"
    ]

    for log_file in log_files:
        if not Path(log_file).exists():
            issues.append(f"Файл логов не найден: {log_file}")
        else:
            size = Path(log_file).stat().st_size
            if size == 0:
                issues.append(f"Файл логов пустой: {log_file}")

    # 3. Проверка состояния системы
    if not issues:  # Только если API доступен
        try:
            status = response.json()
            if status.get('energy', 1.0) < 0.1:
                issues.append("Критически низкий уровень энергии")
            if status.get('integrity', 1.0) < 0.5:
                issues.append("Проблемы с целостностью системы")
        except:
            issues.append("Не удалось разобрать ответ API")

    # Вывод результатов
    if issues:
        print("🚨 ОБНАРУЖЕНЫ ПРОБЛЕМЫ:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ Система работает нормально")
        return True

if __name__ == "__main__":
    success = full_system_diagnostic()
    sys.exit(0 if success else 1)
```

## Распространенные проблемы и решения

### 1. Система не запускается

**Возможные причины:**
- Неправильная версия Python
- Отсутствующие зависимости
- Занятый порт

**Решения:**
```bash
# Проверить версию Python
python --version

# Установить зависимости
pip install -r requirements.txt

# Проверить порт
netstat -tulpn | grep :8000

# Запустить на другом порту
python src/main_server_api.py --host 0.0.0.0 --port 8001
```

### 2. API возвращает ошибки

**Возможные причины:**
- Сервер не запущен
- Неправильный формат запроса
- Ошибки в обработке

**Решения:**
```bash
# Проверить статус сервера
curl http://localhost:8000/status

# Проверить логи на ошибки
tail -20 data/tick_log.jsonl | grep -i error

# Тестовый запрос с правильным форматом
curl -X POST http://localhost:8000/event \
  -H "Content-Type: application/json" \
  -d '{"type":"noise","intensity":0.1}'
```

### 3. Память не работает

**Возможные причины:**
- События не значимы (significance = 0)
- Ошибки в логике активации
- Проблемы с сериализацией

**Решения:**
```bash
# Проверить значимость событий
tail -5 data/tick_log.jsonl | jq '.last_significance'

# Проверить размер памяти
curl http://localhost:8000/status | jq '.memory | length'

# Отправить высоко значимое событие
curl -X POST http://localhost:8000/event \
  -H "Content-Type: application/json" \
  -d '{"type":"shock","intensity":1.0}'
```

### 4. Learning/Adaptation не работают

**Возможные причины:**
- Редкий вызов (Learning вызывается раз в 50-100 тиков)
- Изменения слишком малы для заметности
- Ошибки в логике

**Решения:**
```bash
# Проверить частоту вызовов
grep -c "learning" data/tick_log.jsonl

# Проверить изменения параметров
curl http://localhost:8000/status | jq '.learning_params.event_type_sensitivity'

# Дать системе поработать дольше
sleep 60  # Подождать минуту работы
curl http://localhost:8000/status | jq '.learning_params'
```

### 5. Высокое потребление ресурсов

**Возможные причины:**
- Слишком частые тики
- Большой размер памяти
- Частое логирование

**Решения:**
```bash
# Увеличить интервал тиков
python src/main_server_api.py --tick-interval 2.0

# Уменьшить частоту snapshots
python src/main_server_api.py --snapshot-period 50

# Проверить размер памяти
du -sh data/
```

## Отладка в dev-режиме

### Автоматическая перезагрузка

```bash
# Запуск в dev-режиме
python src/main_server_api.py --dev --tick-interval 1.0

# Изменение кода в другом терминале
# Система автоматически перезагрузит модули
```

⚠️ **Важно:** Текущая реализация hot reload имеет известные проблемы. См. [`docs/development/HOT_RELOAD_PROBLEMS.md`](HOT_RELOAD_PROBLEMS.md) для детального описания.

**Известные проблемы:**
- Идентичность объектов может нарушаться при перезагрузке
- Висящие потоки/серверы могут создавать множественные экземпляры
- Непредсказуемое поведение из-за race conditions

**Рекомендации:**
- Если возникают проблемы в dev-режиме, перезапустите процесс полностью
- Для критических экспериментов используйте обычный режим (без `--dev`)
- Следите за логами на предмет ошибок перезагрузки

### Логирование отладки

#### API сервер

API сервер (`src/main_server_api.py`) использует управляемое логирование через стандартный Python модуль `logging`. Уровень логирования настраивается автоматически:

- **Dev-режим (`--dev`)**: `DEBUG` уровень — выводится вся диагностическая информация
- **Production режим**: `INFO` уровень — выводятся только важные сообщения

**Примеры логов в dev-режиме:**
```
2026-01-20 14:30:15 - __main__ - INFO - API server running on http://localhost:8000
2026-01-20 14:30:15 - __main__ - DEBUG - Получен POST /event: type='noise', intensity=0.5
2026-01-20 14:30:15 - __main__ - DEBUG - Event PUSHED to queue. Size now: 1
```

**Примеры логов в production режиме:**
```
2026-01-20 14:30:15 - __main__ - INFO - API server running on http://localhost:8000
```

#### Настройка логирования в коде

```python
import logging

# Включить подробное логирование
logging.basicConfig(level=logging.DEBUG)

# Логирование в коде
logger = logging.getLogger(__name__)
logger.debug(f"Processing event: {event}")
logger.info(f"Memory size: {len(memory)}")
logger.warning(f"High memory usage: {memory_mb} MB")
logger.error(f"Error processing event: {error}", exc_info=True)
```

#### Уровни логирования

- **DEBUG**: Детальная диагностическая информация (только в dev-режиме)
- **INFO**: Информационные сообщения о работе системы
- **WARNING**: Предупреждения о потенциальных проблемах
- **ERROR**: Сообщения об ошибках

## Создание отчета об ошибке

При обнаружении бага соберите следующую информацию:

1. **Описание проблемы**
   - Что произошло?
   - Что ожидалось?
   - Шаги для воспроизведения

2. **Системная информация**
   ```bash
   python --version
   pip list | grep -E "(fastapi|uvicorn|pytest)"
   uname -a
   ```

3. **Логи и состояние**
   ```bash
   # Последние логи
   tail -50 data/tick_log.jsonl

   # Текущее состояние
   curl http://localhost:8000/status

   # Конфигурация запуска
   ps aux | grep main_server_api
   ```

4. **Тест для воспроизведения**
   ```python
   def test_reproduce_bug():
       # Шаги для воспроизведения
       pass
   ```

## 🤖 CI/CD и автоматизация отладки

### GitHub Actions диагностика

Проект включает автоматизированные проверки качества кода:

```yaml
# .github/workflows/ci.yml (фрагмент)
- name: Run Tests with Coverage
  run: |
    pytest src/test/ --cov=src --cov-report=xml

- name: Performance Regression Check
  run: |
    python run_performance_tests.py

- name: Lint and Type Check
  run: |
    flake8 src/
    mypy src/
```

### Автоматизированные отчеты

#### Генерация отчетов о тестировании
```bash
# Полный отчет о тестировании
python run_tests.py
python analyze_test_results.py

# Отчет будет создан в docs/results/test_full_task_*.md
```

#### Отчеты о производительности
```bash
# Отчет о регрессиях производительности
python run_performance_tests.py

# Отчет будет создан в docs/results/performance_regression_report.md
```

### Интеграция с системами мониторинга

#### Health checks для оркестраторов
```python
def health_check():
    """Health check для Docker/Kubernetes."""
    try:
        response = requests.get("http://localhost:8000/status", timeout=5)
        data = response.json()

        # Критические показатели
        checks = {
            "api_available": response.status_code == 200,
            "energy_level": data.get("energy", 0) > 0.1,
            "memory_accessible": isinstance(data.get("memory"), list),
            "event_queue_working": data.get("event_queue_size", 0) >= 0
        }

        return all(checks.values()), checks

    except Exception as e:
        return False, {"error": str(e)}
```

#### Метрики для Prometheus
```python
def collect_prometheus_metrics():
    """Сбор метрик для Prometheus."""
    try:
        response = requests.get("http://localhost:8000/status")
        data = response.json()

        metrics = {
            "life_energy_level": data.get("energy", 0),
            "life_integrity_level": data.get("integrity", 1.0),
            "life_stability_level": data.get("stability", 1.0),
            "life_memory_size": len(data.get("memory", [])),
            "life_event_queue_size": data.get("event_queue_size", 0),
            "life_tick_count": data.get("tick_count", 0)
        }

        return metrics

    except Exception as e:
        print(f"Failed to collect metrics: {e}")
        return {}
```

### Отладка в production среде

#### Safe debug mode
```bash
# Запуск с расширенным логированием
python src/main_server_api.py \
  --log-level DEBUG \
  --structured-logging \
  --snapshot-period 5 \
  --tick-interval 1.0
```

#### Memory dump при проблемах
```python
import faulthandler
import signal

# Включить faulthandler для дампов при падениях
faulthandler.enable()

# Дамп по сигналу
def dump_on_signal(signum, frame):
    import tracemalloc
    print("=== MEMORY DUMP ===")
    current, peak = tracemalloc.get_traced_memory()
    print(f"Current: {current/1024/1024:.1f} MB, Peak: {peak/1024/1024:.1f} MB")

    # Топ объектов по памяти
    import gc
    objects = gc.get_objects()
    sizes = [(sys.getsizeof(obj), type(obj).__name__) for obj in objects[:1000]]
    sizes.sort(reverse=True)

    print("Top memory objects:")
    for size, type_name in sizes[:10]:
        print(f"  {type_name}: {size} bytes")

signal.signal(signal.SIGUSR1, dump_on_signal)
```

## Профилактика проблем

### Регулярные проверки

- Запускайте полный набор тестов перед изменениями
- Мониторьте потребление ресурсов
- Проверяйте логи на наличие ошибок

### Архитектурные проверки

- Соблюдайте ограничения компонентов
- Не изменяйте параметры напрямую (только через Learning/Adaptation)
- Тестируйте интеграцию с существующими модулями

### Код ревью

- Проверяйте соответствие архитектуре
- Убеждайтесь в наличии тестов
- Валидируйте изменения документации

## 📚 Ссылки на документацию

### Основные руководства
- **[docs/observability/README.md](../observability/README.md)** - Система наблюдаемости и логирования
- **[docs/testing/README.md](../testing/README.md)** - Полное руководство по тестированию
- **[docs/development/SAFE_DEV_MODE.md](SAFE_DEV_MODE.md)** - Безопасная разработка в dev-режиме

### Специализированные документы
- **[docs/observability/performance_profiling.md](../observability/performance_profiling.md)** - Профилирование производительности
- **[docs/observability/performance_regression_testing.md](../observability/performance_regression_testing.md)** - Тестирование регрессий
- **[docs/testing/TESTING_GUIDE.md](../testing/TESTING_GUIDE.md)** - Подробное руководство по тестированию

### Инструменты и скрипты
- **Отладочные скрипты:** `debug_*.py` в корне проекта
- **Скрипты анализа:** `analyze_*.py`, `run_*.py`
- **Профилирование:** `profile_runtime.py`
- **Индексация:** `Index_*.py`, `mcp_*.py`

### Статистика и метрики
- **Всего тестов:** 766+ (96% покрытие)
- **Производительность:** ~15 мс на тик (медиана 9.76 мс)
- **Компоненты:** Полное покрытие основных модулей
- **Мониторинг:** JSONL логи + структурированное логирование

---

*Это расширенное руководство по отладке регулярно обновляется на основе опыта работы с системой Life. Последнее обновление: 2026-01-21*
