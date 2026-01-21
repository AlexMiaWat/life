# 08_EVENTS_AND_MEANING.md — Интерпретация событий

## Назначение
Meaning Engine — это модуль, который превращает объективные события (`Event`) в субъективный опыт (`Meaning`).
Одно и то же событие может быть воспринято по-разному в зависимости от текущего состояния Life.

## Текущий статус
✅ **Реализован и интегрирован** (v1.0)
*   Код движка готов: [`src/meaning/`](../../src/meaning/)
*   **Полностью интегрирован** в Runtime Loop (`src/runtime/loop.py`).
*   Используется для обработки всех событий из Environment.

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

## Интеграция в Runtime Loop

Meaning Engine интегрирован в Runtime Loop следующим образом:

```python
# В src/runtime/loop.py:
engine = MeaningEngine()
meaning = engine.process(event, asdict(self_state))
if meaning.significance > 0:
    # Активация памяти, принятие решения, применение impact
    ...
```

Движок обрабатывает все события из EventQueue и создает объекты Meaning, которые используются для:
- Активации релевантной памяти
- Принятия решений о паттерне реакции
- Применения изменений к Self-State

## Специальная обработка Memory Echo событий

Meaning Engine имеет расширенную поддержку для `memory_echo` событий с конкретными воспоминаниями.

### Формат Memory Echo события

```python
Event(
    type="memory_echo",
    intensity=0.5,  # Рассчитывается на основе значимости воспоминания
    metadata={
        "internal": True,
        "source": "spontaneous_recall",
        "echo_type": "specific_memory",  # или "abstract_memory"
        "original_memory": {  # Только для specific_memory
            "event_type": "recovery",
            "meaning_significance": 0.8,
            "timestamp": 1234567890.0,
            "age_days": 2.5,
            "emotional_impact": "positive"  # "positive", "negative", "neutral"
        }
    }
)
```

### Эмоциональное влияние воспоминаний

При обработке `memory_echo` с конкретными воспоминаниями Meaning Engine применяет дополнительное эмоциональное влияние:

#### Позитивные воспоминания
- **recovery**: +energy 0.3, +stability 0.05, +integrity 0.02
- **social_harmony**: +energy 0.2, +stability 0.08, +integrity 0.03
- **learning_achievement**: +energy 0.25, +stability 0.06, +integrity 0.04

#### Негативные воспоминания
- **shock**: -energy 0.2, -stability 0.03, -integrity 0.01
- **decay**: -energy 0.15, -stability 0.02, -integrity 0.02
- **crisis**: -energy 0.25, -stability 0.04, -integrity 0.03

#### Нейтральные воспоминания
- Минимальное влияние: ±0.05 energy, ±0.01 stability

### Контекстуальная модификация

Влияние воспоминаний модифицируется в зависимости от текущего состояния:

- **Низкая стабильность** (<0.3): Позитивные воспоминания усиливаются ×1.5
- **Низкая энергия** (<30): Recovery воспоминания усиливаются ×1.3
- **Высокая усталость** (>0.7): Social harmony усиливается ×1.2

### Graceful Degradation

При отсутствии конкретных данных воспоминания (abstract_memory) используется базовое влияние memory_echo события.
