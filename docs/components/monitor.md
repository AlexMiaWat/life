# 04_MONITOR.md — Система наблюдения

## Назначение
Monitor — это инструмент для наблюдения за жизнью **Life** со стороны человека.
Он работает в режиме "только чтение" и не влияет на процессы внутри системы.

## Текущий статус
✅ **Реализован** (v1.2)
*   Файл: [`src/monitor/console.py`](../../src/monitor/console.py)
*   Поддерживает консольный вывод (Heartbeat) и логирование в файл.
*   **Обновления:** Улучшенное логирование в `generator_cli.py` с уровнями и флагами (--verbose)
*   **v1.1:** Отображение субъективного времени наряду с физическим временем
*   **v1.2:** Улучшенное отображение времени с разделением физического и субъективного времени и показом соотношения

## Функции

### 1. Console Heartbeat
Выводит текущее состояние в консоль в реальном времени (одна строка, обновляется каждый такт).

Формат:
```text
• [000123] физ: 60.5с | субъект: 61.2с (x1.01) | энергия: 98.0% | интеллект: 1.00 | стабильность: 0.99 | значимость: 0.85 | активация: 2 (0.92) | decision: pattern_123 | action: executed pattern_123 |
```
*   `•` — индикатор такта (мигает).
*   `[ticks]` — счетчик тактов.
*   `физ: {age}с | субъект: {subjective_time}с (x{ratio})` — физическое и субъективное время с соотношением (v1.1).
*   `энергия`, `интеллект`, `стабильность` — жизненные показатели.
*   `значимость` — уровень значимости активных паттернов.
*   `активация` — количество активных паттернов (максимальная значимость).
*   `decision` — принятое решение.
*   `action` — выполненное действие.

### 2. File Logging
Сохраняет детальную историю каждого такта в JSONL файл.
*   Путь: `data/tick_log.jsonl`
*   Формат: JSON Lines (один объект JSON на строку).

Пример записи:
```json
{
  "timestamp": 1704987654.321,
  "ticks": 123,
  "age": 60.5,
  "subjective_time": 61.2,
  "energy": 98.0,
  "integrity": 1.0,
  "stability": 0.99,
  "active": true
}
```

## Принципы

1.  **Невмешательство:** Монитор никогда не пишет в `Self-State`.
2.  **Объективность:** Монитор показывает цифры, а не интерпретации ("энергия 10%", а не "я устал").
3.  **Отказоустойчивость:** Ошибка в мониторе не должна убивать Life.

## Использование

Монитор подключается к Runtime Loop как callback-функция:

```python
from monitor.console import console_monitor
from runtime.loop import run_loop

run_loop(..., monitor=console_monitor)
```

## Примеры использования

### Базовое использование мониторинга

```python
from src.monitor.console import monitor as console_monitor
from src.state.self_state import create_initial_state
from src.memory.memory import MemoryEntry
import time

# Создание состояния системы
state = create_initial_state()
state.energy = 85.0
state.stability = 0.92
state.integrity = 0.95
state.ticks = 42
state.age = 42.5

# Добавление записей в память для демонстрации
state.memory.append(MemoryEntry("decay", 0.8, time.time()))
state.memory.append(MemoryEntry("recovery", 0.6, time.time()))

# Имитация вызова монитора (в runtime loop это происходит автоматически)
print("Пример вывода монитора:")
console_monitor(state)

# Вывод будет примерно таким:
# • [000042] физ: 42.5с | субъект: 45.2с (x1.06) | энергия: 85.0% | интеллект: 1.00 | стабильность: 0.92 | значимость: 0.85 | активация: 2 (0.70) | decision: absorb | action: executed absorb |
```

### Мониторинг с активированной памятью

```python
from src.monitor.console import monitor as console_monitor
from src.state.self_state import create_initial_state
from src.memory.memory import MemoryEntry
import time

state = create_initial_state()
state.energy = 78.0
state.stability = 0.88
state.ticks = 156
state.age = 156.7
state.subjective_time = 162.3

# Добавление активированной памяти (transient поле)
state.activated_memory = [
    MemoryEntry("shock", 0.9, time.time()),
    MemoryEntry("shock", 0.7, time.time()),
    MemoryEntry("decay", 0.5, time.time())
]

# Установка последнего принятого решения и действия
state.last_pattern = "dampen"

# Имитация последней значимости события
state.last_significance = 0.75

print("Мониторинг с активированной памятью:")
console_monitor(state)

# Вывод покажет количество активированных воспоминаний и их максимальную значимость
```

### Настройка логирования с разными уровнями

```python
import logging
from src.monitor.console import monitor as console_monitor
from src.logging_config import setup_logging
from src.state.self_state import create_initial_state

# Настройка логирования
setup_logging()

# Создание логгера для демонстрации
logger = logging.getLogger(__name__)

# Пример INFO уровня (по умолчанию)
logger.info("start: host=localhost port=8000 interval=1.0s")
logger.info("Монитор инициализирован")

# Создание состояния для демонстрации
state = create_initial_state()
state.energy = 92.0
state.ticks = 89

# Вызов монитора (создает запись в логе)
console_monitor(state)

# Пример DEBUG уровня (с флагом --verbose)
logger.debug("Детальная информация о событии: type=noise, intensity=0.3")
logger.debug("Текущее состояние памяти: 15 записей")
logger.debug("Интенсивность сглажена: 0.45")

print("Логирование настроено. Для просмотра DEBUG сообщений используйте --verbose")
```

### Чтение и анализ логов

```python
import json
import os
from datetime import datetime

# Путь к файлу логов (создается автоматически)
log_file = "data/tick_log.jsonl"

if os.path.exists(log_file):
    print("Анализ последних 5 записей из лога:")
    print("-" * 50)

    with open(log_file, 'r') as f:
        lines = f.readlines()[-5:]  # Последние 5 записей

    for i, line in enumerate(lines, 1):
        try:
            entry = json.loads(line.strip())
            timestamp = datetime.fromtimestamp(entry['timestamp']).strftime('%H:%M:%S')
            print(f"{i}. [{timestamp}] tick={entry['ticks']}, energy={entry['energy']}, active={entry['active']}")
        except json.JSONDecodeError:
            print(f"{i}. Ошибка чтения записи")

    print(f"\nВсего записей в логе: {len(open(log_file).readlines())}")
else:
    print("Файл логов еще не создан. Запустите систему для создания записей.")
```

### Расширенный мониторинг с дополнительными метриками

```python
from src.monitor.console import monitor as console_monitor
from src.state.self_state import create_initial_state
from src.memory.memory import MemoryEntry
from src.intelligence.intelligence import process_information
from src.planning.planning import record_potential_sequences
import time

# Создание полной системы для демонстрации
state = create_initial_state()

# Настройка состояния
state.energy = 67.0
state.stability = 0.76
state.integrity = 0.89
state.ticks = 234
state.age = 234.8
state.subjective_time = 248.6

# Добавление недавних событий
state.recent_events = ["noise", "decay", "recovery", "shock"]

# Добавление памяти
for i in range(8):
    event_type = ["noise", "decay", "recovery", "shock"][i % 4]
    significance = 0.3 + (i * 0.1)
    state.memory.append(MemoryEntry(event_type, significance, time.time() - (i * 60)))

# Запуск Intelligence (добавляет данные в intelligence)
process_information(state)

# Запуск Planning (добавляет данные в planning)
record_potential_sequences(state)

# Активация памяти (имитация)
from src.activation.activation import activate_memory
state.activated_memory = activate_memory("decay", state.memory)

print("Расширенный мониторинг полной системы:")
console_monitor(state)

print("\nДополнительная информация:")
print(f"Записей в памяти: {len(state.memory)}")
print(f"Интеллект (обработанные источники): {state.intelligence.get('processed_sources', {})}")
print(f"Планирование (потенциальные последовательности): {len(state.planning.get('potential_sequences', []))}")
```

## Логирование с уровнями

### Централизованное логирование

Все компоненты мониторинга используют централизованную систему логирования из модуля `src/logging_config.py`. Это обеспечивает консистентность форматов и уровней логирования во всем проекте.

### Улучшенное логирование в Generator CLI

**Файл:** [`src/environment/generator_cli.py`](../../src/environment/generator_cli.py)

**Особенности:**
- Замена `print()` на структурированное логирование с уровнями
- Флаг `--verbose/-v` для включения подробного вывода
- Использование централизованной конфигурации логирования

### Уровни логирования

#### INFO уровень (по умолчанию в production)
- Стартовые сообщения: `logger.info("start: host={} port={} interval={}s")`
- Сообщения о завершении: `logger.info("Stopped")`
- Важная информация без засорения вывода

#### DEBUG уровень (с флагом --verbose или в dev-режиме)
- Детальная информация о каждом отправленном событии
- Сообщения от зависимостей (urllib3, requests)
- Диагностическая информация для отладки

#### WARNING уровень
- Сообщения об ошибках отправки событий
- Предупреждения о проблемах с подключением

### Настройка логирования

Логирование настраивается через централизованную функцию:

```python
from src.logging_config import setup_logging

# В verbose режиме
setup_logging(verbose=True)  # DEBUG уровень

# По умолчанию (production)
setup_logging(verbose=False)  # INFO уровень
```

### Модуль logging_config.py

```python
def setup_logging(verbose: bool = False) -> None:
    """Настройка логирования для приложения."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Подавление verbose логов внешних библиотек в production
    if not verbose:
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
```

### Использование

```bash
# Обычный режим (только INFO и WARNING)
python -m environment.generator_cli --interval 5 --host localhost --port 8000

# Подробный режим (включая DEBUG)
python -m environment.generator_cli --verbose --interval 5 --host localhost --port 8000
```

### Преимущества централизованного логирования

1. **Управляемость:** Уровень детализации контролируется через флаги командной строки
2. **Производительность:** DEBUG логи не влияют на производительность в обычном режиме
3. **Чистота кода:** Убраны диагностические print-блоки, которые засоряли вывод
4. **Стандартизация:** Все компоненты используют унифицированную систему логирования
5. **Консистентность:** Единый формат и поведение логирования во всем проекте
