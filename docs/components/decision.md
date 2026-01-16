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

## Limits

См. [decision-limits.md](../archive/limits/decision-limits.md) для архитектурных ограничений.
