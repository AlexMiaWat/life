# 11_DECISION

## Статус: ✅ Реализован (v1.0)

## Описание

Функция decide_response (выбор паттерна на основе activated_memory + meaning.significance), интеграция в loop.py (модификация impact перед apply_delta).

### Принципы

Детерминированный минимальный выбор, fallback на Meaning, в limits (см. [decision-limits.md](../archive/limits/decision-limits.md)).

### Пример

Код функции:

```python
def decide_response(self_state: SelfState, meaning: Meaning) -> str:
    """
    Минимальный выбор паттерна на основе activated_memory.
    - Если max sig в activated >0.5 — "dampen" (опыт учит смягчать).
    - Else return Meaning's pattern (absorb/ignore).
    """
    activated = self_state.activated_memory
    if activated and max(e.meaning_significance for e in activated) > 0.5:
        return "dampen"
    # Fallback to Meaning's logic
    if meaning.significance < 0.1:
        return "ignore"
    return "absorb"
```

Логи поведения: dampen уменьшает impact, ignore пропускает, absorb применяет без изменений.

## Примеры использования

### Базовый пример принятия решения

```python
from src.decision.decision import decide_response
from src.state.self_state import SelfState
from src.meaning.meaning import Meaning

# Создание состояния системы
state = SelfState()

# Создание объекта Meaning
meaning = Meaning(
    event_id="test_event",
    significance=0.8,
    impact={"energy": -0.2, "stability": -0.1}
)

# Принятие решения без активированной памяти
decision = decide_response(state, meaning)
print(f"Решение: {decision}")  # "absorb"
```

### Пример с активированной памятью

```python
from src.decision.decision import decide_response
from src.state.self_state import SelfState
from src.meaning.meaning import Meaning
from src.memory.memory import MemoryEntry

# Создание состояния с активированной памятью
state = SelfState()

# Создание высоко значимых воспоминаний (significance > 0.5)
state.activated_memory = [
    MemoryEntry(event_type="shock", meaning_significance=0.9, timestamp=100.0),
    MemoryEntry(event_type="shock", meaning_significance=0.7, timestamp=200.0),
]

# Создание объекта Meaning
meaning = Meaning(
    event_id="shock_event",
    significance=0.6,
    impact={"energy": -0.5, "stability": -0.3}
)

# Принятие решения - должна быть выбрана "dampen" из-за высокой значимости памяти
decision = decide_response(state, meaning)
print(f"Решение с памятью: {decision}")  # "dampen"
```

### Пример различных сценариев

```python
from src.decision.decision import decide_response
from src.state.self_state import SelfState
from src.meaning.meaning import Meaning
from src.memory.memory import MemoryEntry

# Сценарий 1: Низкая значимость события
meaning_low = Meaning(
    event_id="noise_event",
    significance=0.05,  # < 0.1
    impact={"energy": -0.01}
)

decision1 = decide_response(SelfState(), meaning_low)
print(f"Низкая значимость: {decision1}")  # "ignore"

# Сценарий 2: Высокая значимость с низкой памятью
meaning_high = Meaning(
    event_id="shock_event",
    significance=0.8,
    impact={"energy": -0.5, "integrity": -0.2}
)

decision2 = decide_response(SelfState(), meaning_high)
print(f"Высокая значимость без памяти: {decision2}")  # "absorb"

# Сценарий 3: Средняя значимость с высокой памятью
state_with_memory = SelfState()
state_with_memory.activated_memory = [
    MemoryEntry(event_type="decay", meaning_significance=0.6, timestamp=100.0)
]

meaning_medium = Meaning(
    event_id="decay_event",
    significance=0.4,
    impact={"energy": -0.2}
)

decision3 = decide_response(state_with_memory, meaning_medium)
print(f"Средняя значимость с памятью: {decision3}")  # "dampen"
```

## Limits

См. [decision-limits.md](../archive/limits/decision-limits.md) для архитектурных ограничений.
