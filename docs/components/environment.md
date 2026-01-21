# 07_ENVIRONMENT.md — Внешняя среда

## Назначение
Environment — это источник внешних событий для Life.
Life не существует в вакууме; она существует в среде, которая постоянно воздействует на неё.

## Текущий статус
✅ **Реализован** (v1.0)
*   Файлы: [`src/environment/`](../../src/environment/)
*   Реализованы: `Event`, `EventQueue`, `EventGenerator`.

## Компоненты

### 1. Event (Событие)
Атомарная единица воздействия.
*   `type` (str): Тип события (`noise`, `shock`, `recovery`, `decay`, `idle`).
*   `intensity` (float): Сила воздействия.
*   `timestamp` (float): Время возникновения.

### 2. EventQueue (Очередь событий)
Thread-safe очередь, куда попадают события из внешнего мира.
Runtime Loop забирает все события из очереди в начале каждого такта.

### 3. EventGenerator (Генератор)
Инструмент для симуляции внешнего мира. Генерирует случайные события с заданными вероятностями.

## Типы событий

| Тип | Описание | Влияние (по умолчанию) |
|-----|----------|------------------------|
| `noise` | Фоновый шум | Незначительное влияние на стабильность. |
| `shock` | Резкий удар | Снижает целостность (`integrity`) и стабильность. |
| `recovery` | Восстановление | Повышает энергию. |
| `decay` | Естественный распад | Снижает энергию (энтропия). |
| `idle` | Тишина | Ничего не происходит. |
| `memory_echo` | Спонтанное воспоминание | Мягкое рефлексивное влияние (внутренняя гармония). |

## Использование

### Внешний генератор (CLI)
Можно запустить отдельный процесс, который будет "бомбардировать" Life событиями:

```bash
python -m src.environment.generator_cli --interval 1.0
```

### Программное создание событий
```python
from environment.event import Event
from environment.event_queue import EventQueue

queue = EventQueue()
event = Event(type="shock", intensity=0.8, timestamp=time.time())
queue.push(event)
```

### Внутренние события (Memory Echoes)
Life может генерировать внутренние события спонтанно, независимо от внешней среды.

**Memory Echoes** - спонтанные всплывания воспоминаний:
- Генерируются [`InternalEventGenerator`](src/environment/internal_generator.py)
- Интегрированы в runtime loop для периодической генерации
- Имеют мягкое рефлексивное влияние на состояние
- Записываются в историю памяти как обычные события

```python
from src.environment.internal_generator import InternalEventGenerator

generator = InternalEventGenerator(memory_echo_probability=0.02)
event = generator.generate_memory_echo(memory_stats)
if event:
    # Событие добавляется в очередь для обработки
    event_queue.push(event)
```
