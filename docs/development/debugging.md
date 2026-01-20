# Руководство по отладке и troubleshooting

> **Назначение:** Инструкции по диагностике проблем и отладке системы Life

## Общие принципы отладки

### 1. Уровни диагностики

- **Мониторинг**: Наблюдение за состоянием системы в реальном времени
- **Логирование**: Анализ истории работы и ошибок
- **Тестирование**: Проверка отдельных компонентов
- **Профилирование**: Анализ производительности

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

## Отладка с тестами

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

## Профилирование производительности

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

### Логирование отладки

```python
import logging

# Включить подробное логирование
logging.basicConfig(level=logging.DEBUG)

# Логирование в коде
logger = logging.getLogger(__name__)
logger.debug(f"Processing event: {event}")
logger.info(f"Memory size: {len(memory)}")
```

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

---

*Это руководство регулярно обновляется на основе опыта отладки системы.*
