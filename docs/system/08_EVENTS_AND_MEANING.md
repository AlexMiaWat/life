# 08_EVENTS_AND_MEANING.md — Интерпретация событий

## Назначение
Meaning Engine — это модуль, который превращает объективные события (`Event`) в субъективный опыт (`Meaning`).
Одно и то же событие может быть воспринято по-разному в зависимости от текущего состояния Life.

## Текущий статус
⚠️ **Частично реализован**
*   Код движка готов: [`src/meaning/`](../../src/meaning/)
*   **Не интегрирован** полностью в Runtime Loop (используется упрощенная заглушка `_interpret_event`).

## Архитектура Meaning Engine

Процесс интерпретации состоит из трех шагов:

### 1. Appraisal (Оценка значимости)
Определяет, насколько событие важно *сейчас*.
*   *Вход:* Событие + Текущее состояние.
*   *Логика:* Если `integrity` низкая, даже слабый `shock` становится критически важным.

### 2. Impact Model (Модель влияния)
Рассчитывает конкретные изменения параметров.
*   *Пример:* `shock` (intensity 0.5) -> `energy` -5, `integrity` -0.1.

### 3. Response Pattern (Паттерн реакции)
Определяет стратегию реакции.
*   `ignore`: Игнорировать (если значимость низкая).
*   `absorb`: Принять как есть.
*   `dampen`: Смягчить удар (если высокая стабильность).
*   `amplify`: Усилить эффект (если система нестабильна).

## Структура Meaning

Результат работы движка — объект `Meaning`:

```python
@dataclass
class Meaning:
    event_id: str
    significance: float       # [0.0, 1.0]
    impact: Dict[str, float]  # {"energy": -0.5, ...}
```

## Планы по интеграции

Необходимо заменить функцию `_interpret_event` в `src/runtime/loop.py` на вызов `MeaningEngine`.

```python
# Было:
_interpret_event(event, self_state)

# Станет:
meaning = meaning_engine.process(event, self_state)
apply_impact(self_state, meaning.impact)
```
