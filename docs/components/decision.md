# 11_DECISION

## Статус: ✅ Реализован (v2.1)

**v2.0:** Добавлен DecisionEngine с историей решений и статистикой
**v2.1:** Улучшена логика принятия решений с анализом эмоций и типов событий (primary_emotion), более точный анализ значимости памяти (max_significance), улучшенные правила выбора паттернов

## Описание

Функция decide_response (выбор паттерна на основе activated_memory + meaning.significance), интеграция в loop.py (модификация impact перед apply_delta).

### Принципы

Детерминированный минимальный выбор, fallback на Meaning, в limits (см. [decision-limits.md](../archive/limits/decision-limits.md)).

### Пример

Код функции (v2.1 с улучшенной логикой):

```python
def _simple_pattern_selection(self_state: SelfState, meaning: Meaning) -> str:
    """
    Улучшенная логика выбора паттерна реакции с анализом эмоций и значимости.

    - Анализирует тип события через primary_emotion (joy, fear, anger, etc.)
    - Использует max_significance вместо avg для более точного анализа памяти
    - Положительные события усиливаются, негативные гасятся
    - Высокая значимость в meaning всегда приводит к гашению
    """
    # Базовые условия состояния
    energy_low = self_state.energy < 30
    stability_low = self_state.stability < 0.3
    integrity_low = self_state.integrity < 0.3

    # Анализ активированной памяти
    activated = self_state.activated_memory or []
    if activated:
        max_significance = max(entry.meaning_significance for entry in activated)
        avg_significance = sum(entry.meaning_significance for entry in activated) / len(activated)
        high_significance = max_significance > 0.5
    else:
        max_significance = 0.0
        avg_significance = 0.0
        high_significance = False

    # Определение типа события из meaning
    event_type = getattr(meaning, 'primary_emotion', 'neutral')
    is_positive = event_type in ['joy', 'hope', 'love', 'curiosity', 'insight']
    is_negative = event_type in ['fear', 'anger', 'sadness', 'confusion', 'void']

    # Анализ significance из meaning
    meaning_high_significance = meaning.significance >= 0.5

    # Правила выбора паттерна:
    # 1. При низкой энергии и стабильности - консервативный подход
    # 2. При низкой целостности - осторожный подход
    # 3. Положительные события - усиливать
    # 4. Негативные события - гасить
    # 5. Высокая значимость в meaning - гасить
    # 6. Высокая значимость в памяти - гасить
    # 7. По умолчанию - поглощать

    return "dampen"  # или "amplify", "absorb", "ignore"
```

### Логика паттернов реакции

- **dampen**: Уменьшает impact события (консервативный/защитный подход)
- **amplify**: Усиливает положительное воздействие события
- **absorb**: Применяет событие без изменений (нейтральный подход)
- **ignore**: Полностью игнорирует событие (при очень низкой значимости)

## DecisionEngine (v2.0)

Класс `DecisionEngine` предоставляет инфраструктуру для отслеживания и анализа принятых решений в системе.

### Основные возможности

- **История решений**: Автоматическое сохранение всех принятых решений с контекстом
- **Статистика**: Метрики успешности решений и производительности
- **Анализ паттернов**: Инструменты для выявления паттернов в принятии решений

### Основные методы

```python
class DecisionEngine:
    def record_decision(
        self,
        decision_type: str,
        context: Dict,
        outcome: str = None,
        success: bool = None,
        execution_time: float = None
    ) -> None:
        """
        Записать решение в историю.

        Args:
            decision_type: Тип решения ('response_selection', 'action_choice', etc.)
            context: Контекст принятия решения
            outcome: Результат решения
            success: Успешность решения (True/False)
            execution_time: Время выполнения решения
        """

    def get_recent_decisions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получить недавние решения.

        Returns:
            Список последних решений с полной информацией
        """

    def get_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику принятия решений.

        Returns:
            Dict со статистикой: общее количество решений,
            успешность, среднее время выполнения, точность
        """
```

### Примеры использования

```python
from src.decision.decision import DecisionEngine

# Создание движка принятия решений
decision_engine = DecisionEngine()

# Запись решения
decision_engine.record_decision(
    decision_type="response_selection",
    context={
        "meaning_significance": 0.8,
        "event_type": "shock",
        "current_energy": 0.7,
        "current_stability": 0.9
    },
    outcome="dampen",
    execution_time=0.015
)

# Получение статистики
stats = decision_engine.get_statistics()
print(f"Всего решений: {stats['total_decisions']}")
print(f"Точность: {stats['accuracy']:.2f}")
print(f"Среднее время: {stats['average_time']:.3f}s")

# Получение недавних решений
recent = decision_engine.get_recent_decisions(limit=10)
for decision in recent:
    print(f"{decision['type']}: {decision['outcome']} "
          f"(success: {decision['success']})")
```

### Интеграция в Runtime Loop

DecisionEngine интегрирован в основной цикл системы (`src/runtime/loop.py`) для автоматического отслеживания решений:

```python
# В runtime loop
decision_start_time = time.time()
pattern = decide_response(self_state, meaning)
decision_time = time.time() - decision_start_time

# Запись в DecisionEngine
decision_engine.record_decision(
    decision_type="response_selection",
    context={
        "meaning_significance": meaning.significance,
        "event_type": event.type,
        "current_energy": self_state.energy,
        "current_stability": self_state.stability,
    },
    outcome=pattern,
    execution_time=decision_time,
)
```

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

### Правила принятия решений для типов событий (v1.1)

В версии 1.1 добавлена поддержка специфических правил для различных типов событий. Каждый тип события имеет свой набор характеристик, которые влияют на выбор паттерна реакции.

#### Социально-эмоциональные события

**`connection`** (Связь):
- **Может усиливаться**: Положительное событие, которое можно усиливать
- **Предпочитает поглощение**: Полное принятие эффекта связи
- **Контекстуально зависимо**: Учитывает текущее состояние изоляции

**`isolation`** (Изоляция):
- **Не усиливается**: Негативное событие, которое не следует усиливать
- **Предпочитает смягчение**: Активное снижение эффекта изоляции
- **Консервативный порог**: Реагирует при значимости > 0.25 (более чувствительно)

#### Когнитивные события

**`insight`** (Озарение):
- **Может усиливаться**: Позитивное когнитивное событие
- **Предпочитает поглощение**: Полное принятие момента озарения
- **Консервативный порог**: Реагирует при значимости > 0.2 для значимых моментов

**`confusion`** (Путаница):
- **Не усиливается**: Негативное когнитивное состояние
- **Предпочитает смягчение**: Активное снижение эффекта путаницы
- **Может игнорироваться**: Легкую путаницу (значимость < 0.15) можно игнорировать

**`curiosity`** (Любопытство):
- **Может усиливаться**: Позитивное когнитивное состояние
- **Контекстуально зависимо**: Учитывает текущее когнитивное состояние

#### Экзистенциальные события

**`meaning_found`** (Нахождение смысла):
- **Может усиливаться**: Глубокое позитивное экзистенциальное событие
- **Предпочитает поглощение**: Полное принятие момента нахождения смысла
- **Очень консервативный порог**: Реагирует при значимости > 0.15

**`void`** (Пустота):
- **Не усиливается**: Глубокое негативное экзистенциальное состояние
- **Предпочитает смягчение**: Активное снижение эффекта пустоты
- **Консервативный порог**: Реагирует при значимости > 0.2

**`acceptance`** (Принятие):
- **Может усиливаться**: Позитивное состояние принятия
- **Предпочитает поглощение**: Полное принятие момента принятия
- **Контекстуально зависимо**: Зависит от предыдущего состояния системы

#### Примеры работы с новыми типами событий

```python
from src.decision.decision import decide_response
from src.state.self_state import SelfState
from src.meaning.meaning import Meaning

# Пример 1: Положительное социально-эмоциональное событие
state = SelfState()
meaning_connection = Meaning(
    event_id="connection_event",
    significance=0.7,
    impact={"energy": 0.8, "stability": 0.1}
)
meaning_connection.event_type = "connection"

decision_connection = decide_response(state, meaning_connection)
print(f"Connection: {decision_connection}")  # Может быть "amplify" или "absorb"

# Пример 2: Негативное когнитивное событие
meaning_confusion = Meaning(
    event_id="confusion_event",
    significance=0.6,
    impact={"energy": -0.3, "stability": -0.1}
)
meaning_confusion.event_type = "confusion"

decision_confusion = decide_response(state, meaning_confusion)
print(f"Confusion: {decision_confusion}")  # "dampen"

# Пример 3: Глубокое экзистенциальное событие
meaning_void = Meaning(
    event_id="void_event",
    significance=0.8,
    impact={"energy": -1.2, "stability": -0.15}
)
meaning_void.event_type = "void"

decision_void = decide_response(state, meaning_void)
print(f"Void: {decision_void}")  # "dampen"
```

## Limits

См. [decision-limits.md](../archive/limits/decision-limits.md) для архитектурных ограничений.
