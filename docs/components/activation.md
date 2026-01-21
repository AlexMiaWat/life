# 10.1_ACTIVATION_Memory.md — Активация памяти

## Текущий статус
✅ **Реализован** (v1.1)
*   Файл: [`src/activation/activation.py`](../../src/activation/activation.py)
*   Интегрирован в [`src/state/self_state.py`](../../src/state/self_state.py)
*   Интегрирован в [`src/runtime/loop.py`](../../src/runtime/loop.py)
*   Мониторинг в [`src/monitor/console.py`](../../src/monitor/console.py)
*   **ИНТЕГРАЦИЯ:** Поддержка субъективного времени для динамического лимита активации

### Описание реализации
Активация памяти происходит после обработки событий в runtime loop. Функция `activate_memory` фильтрует память по совпадению `event_type` и возвращает топ-3 по `meaning_significance`. Результат сохраняется в transient поле `activated_memory` SelfState, которое не сохраняется в snapshot.

#### Пример структуры activated_memory
```python
activated_memory: list[MemoryEntry]  # Transient поле, очищается при load
```

#### Принципы
- Минимальное сходство: Совпадение по `event_type`, сортировка по `meaning_significance`.
- Transient: Активированные воспоминания не сохраняются между сессиями.
- Ограничение: Топ-3 воспоминания для предотвращения перегрузки.

## Концепция
Активация делает память полезной, превращая пассивное хранилище в активный контекст для текущих решений.

## Принципы работы

1.  **Триггер по событию:** Активация происходит после обработки каждого пакета событий.
2.  **Сходство по типу:** Воспоминания активируются если `event_type` совпадает с текущим событием.
3.  **Ранжирование по значимости:** Среди совпадающих выбираются наиболее значимые.
4.  **Ограниченный объём:** Не более 3 воспоминаний для поддержания фокуса.

## Текущая реализация

### Функция activate_memory
Функция [`activate_memory`](../../src/activation/activation.py) реализует логику активации с учетом субъективного времени:
*   Вход: `current_event_type: str`, `memory: List[MemoryEntry]`, `limit: Optional[int] = None`, `self_state: Optional[SelfState] = None`
*   Выход: `List[MemoryEntry]` — топ воспоминаний по значимости с динамическим лимитом

#### Интеграция субъективного времени (v1.1)

Функция анализирует восприятие времени системой и динамически регулирует количество активируемых воспоминаний:

**Логика динамического лимита:**
- **Ускоренное восприятие времени** (`time_ratio >= 1.1`): лимит = `min(5, len(matching))` - система более внимательна, активирует до 5 воспоминаний
- **Замедленное восприятие времени** (`time_ratio <= 0.9`): лимит = `min(2, len(matching))` - система менее внимательна, активирует максимум 2 воспоминания
- **Нормальное восприятие времени** (`0.9 < time_ratio < 1.1`): лимит = `min(3, len(matching))` - стандартный режим

**Расчет time_ratio:**
```python
time_ratio = self_state.subjective_time / self_state.age if self_state.age > 0 else 1.0
```

### Интеграция в SelfState
Поле `activated_memory` добавлено в [`SelfState`](../../src/state/self_state.py) как transient поле:
*   Не сохраняется в snapshot (исключается в `save_snapshot`)
*   Очищается при загрузке состояния

### Интеграция в Runtime Loop
В [`loop.py`](../../src/runtime/loop.py) после обработки событий:
*   Вызывается `activate_memory` с типом последнего события
*   Результат присваивается `self_state.activated_memory`

### Мониторинг
В [`console.py`](../../src/monitor/console.py) добавлен вывод:
*   Количество активированных воспоминаний
*   Максимальная значимость среди активированных

## Ограничения (Limits)

1.  **Простое сходство:** Только по `event_type`, без сложных ассоциаций.
2.  **Фиксированный лимит:** Топ-3, без динамического регулирования.
3.  **Нет TTL:** Активированные воспоминания остаются до следующей активации.

## Код реализации

### Функция activate_memory

```python
from typing import List
from memory.memory import MemoryEntry

def activate_memory(current_event_type: str, memory: List[MemoryEntry], limit: int = 3) -> List[MemoryEntry]:
    """
    Минимальная активация: возвращает топ-N воспоминаний с совпадающим event_type,
    отсортированных по significance (desc).
    Если нет совпадений — пустой список.
    """
    matching = [entry for entry in memory if entry.event_type == current_event_type]
    matching.sort(key=lambda e: e.meaning_significance, reverse=True)
    return matching[:limit]
```

### Использование в loop.py

```python
# Активация памяти после обработки событий
if events:
    # Используем тип последнего события для активации
    last_event_type = events[-1].type
    activated = activate_memory(last_event_type, self_state.memory)
    self_state.activated_memory = activated
    print(f"[LOOP] Activated {len(activated)} memories for type '{last_event_type}'")
```

## Пример использования

```python
from src.activation.activation import activate_memory
from src.memory.memory import MemoryEntry

# Пример активации
memory = [
    MemoryEntry(event_type="decay", meaning_significance=0.8, timestamp=1.0),
    MemoryEntry(event_type="decay", meaning_significance=0.6, timestamp=2.0),
    MemoryEntry(event_type="recovery", meaning_significance=0.9, timestamp=3.0),
]

activated = activate_memory("decay", memory)
print(f"Активировано: {len(activated)}")  # 2
print(f"Топ значимость: {activated[0].meaning_significance}")  # 0.8
```

## Связь с другими модулями

*   **Memory:** Предоставляет данные для активации (см. [`src/memory/`](../../src/memory/)).
*   **Decision:** Использует activated_memory как input для выбора паттерна реакции (см. [`src/decision/`](../../src/decision/)).
*   **Monitor:** Отображает статус активации (см. [`src/monitor/`](../../src/monitor/)).
*   **Subjective Time:** Влияет на количество активируемых воспоминаний через `self_state.subjective_time` (см. [`src/runtime/subjective_time.py`](../../src/runtime/subjective_time.py)).
