# ADR 013: Learning Layer

## Статус
✅ Принято

## Дата
2026-01-20

## Контекст

Проект Life нуждался в механизме медленного изменения внутренних параметров без оптимизации и целей. Требовалось реализовать слой Learning (Этап 14), который бы постепенно адаптировал внутренние параметры на основе статистики, но без оценки эффективности или управления поведением.

### Архитектурные ограничения
- **❌ Запрещено**: оптимизация, цели, намерения, reward, utility, scoring
- **❌ Запрещено**: оценка эффективности действий, корректировка поведения
- **❌ Запрещено**: циклы обратной связи, внешние метрики
- **✅ Разрешено**: постепенное изменение внутренних параметров (макс. 0.01 за раз)
- **✅ Разрешено**: фиксация изменений без интерпретации
- **✅ Разрешено**: использование внутренней статистики из Memory

### Проблема
Отсутствие механизма постепенного изменения внутренних параметров приводило к:
- **Статичность**: параметры оставались неизменными весь жизненный цикл
- **Отсутствие адаптации**: система не училась на своем опыте
- **Жесткость**: невозможность постепенной настройки чувствительности

## Решение

### Архитектура Learning Layer

#### 1. LearningEngine - основной класс

```python
class LearningEngine:
    """
    Learning Engine - медленное изменение внутренних параметров без оптимизации.

    ВАЖНО: Learning не отвечает на вопрос "что делать дальше".
    Learning только изменяет внутренние параметры без интерпретации.
    """

    # Максимальное изменение параметра за один вызов
    MAX_PARAMETER_DELTA = 0.01
    MIN_PARAMETER_DELTA = 0.001  # Минимальное изменение для применения

    # Пороги для изменения параметров
    HIGH_FREQUENCY_THRESHOLD = 0.2  # 20% всех событий
    LOW_FREQUENCY_THRESHOLD = 0.1   # 10% всех событий
```

#### 2. Параметры learning_params в SelfState

```python
# Параметры, изменяемые Learning (хранятся в SelfState)
learning_params: Dict[str, Dict[str, float]] = field(default_factory=dict)

# Структура параметров:
learning_params = {
    "event_type_sensitivity": {  # Чувствительность к типам событий
        "noise": 0.2,
        "decay": 0.2,
        "recovery": 0.2,
        "shock": 0.2,
        "idle": 0.2,
    },
    "significance_thresholds": {  # Пороги значимости
        "noise": 0.1,
        "decay": 0.1,
        "recovery": 0.1,
        "shock": 0.1,
        "idle": 0.1,
    },
    "response_coefficients": {  # Коэффициенты реакции
        "dampen": 0.5,
        "absorb": 1.0,
        "ignore": 0.0,
    }
}
```

#### 3. Интеграция в Runtime Loop

```python
LEARNING_INTERVAL = 75  # Вызов Learning раз в 75 тиков

# В runtime loop:
if self_state.ticks % LEARNING_INTERVAL == 0:
    statistics = learning_engine.process_statistics(self_state.memory)
    new_params = learning_engine.adjust_parameters(statistics, current_params)
    if new_params:
        learning_engine.record_changes(current_params, new_params, self_state)
```

### Методы LearningEngine

#### 1. process_statistics - сбор статистики

```python
def process_statistics(self, memory: List[MemoryEntry]) -> Dict:
    """
    Анализирует Memory для извлечения статистики без интерпретации.

    Собирает данные о:
    - Типах событий и их частоте
    - Паттернах действий из Feedback
    - Изменениях состояния из Feedback
    """
    statistics = {
        "event_type_counts": {},
        "event_type_total_significance": {},
        "feedback_pattern_counts": {},
        "feedback_state_deltas": {"energy": [], "stability": [], "integrity": []},
        "total_entries": len(memory),
        "feedback_entries": 0,
    }
```

#### 2. adjust_parameters - изменение параметров

```python
def adjust_parameters(self, statistics: Dict, current_params: Dict) -> Dict:
    """
    Медленно изменяет внутренние параметры на основе статистики.

    ВАЖНО: Без оценки эффективности, без целей, только медленное изменение.
    Максимальное изменение: 0.01 за раз.
    """
    new_params = {}

    # Изменение чувствительности к типам событий
    if "event_type_sensitivity" in current_params:
        new_params["event_type_sensitivity"] = self._adjust_event_sensitivity(
            statistics, current_params["event_type_sensitivity"]
        )

    # Изменение порогов значимости
    if "significance_thresholds" in current_params:
        new_params["significance_thresholds"] = self._adjust_significance_thresholds(
            statistics, current_params["significance_thresholds"]
        )

    # Изменение коэффициентов реакции
    if "response_coefficients" in current_params:
        new_params["response_coefficients"] = self._adjust_response_coefficients(
            statistics, current_params["response_coefficients"]
        )

    return new_params
```

#### 3. record_changes - фиксация изменений

```python
def record_changes(self, old_params: Dict, new_params: Dict, self_state: SelfState):
    """
    Фиксирует изменения параметров без интерпретации.

    Выполняет глубокое объединение параметров с thread-safety.
    """
    with self._lock:
        # Проверка медленных изменений (<= 0.01)
        for key, new_value_dict in new_params.items():
            for param_name, new_value in new_value_dict.items():
                old_value = old_params[key][param_name]
                delta = abs(new_value - old_value)
                if delta > self.MAX_PARAMETER_DELTA + self._VALIDATION_TOLERANCE:
                    raise ValueError(f"Изменение слишком большое: {delta}")

        # Глубокое объединение параметров
        updated_params = copy.deepcopy(self_state.learning_params)
        for key, new_value_dict in new_params.items():
            if key not in updated_params:
                updated_params[key] = copy.deepcopy(new_value_dict)
            else:
                for param_name, new_value in new_value_dict.items():
                    updated_params[key][param_name] = new_value

        self_state.learning_params = updated_params
```

### Алгоритмы изменения параметров

#### 1. _adjust_event_sensitivity

```python
def _adjust_event_sensitivity(self, statistics, current_sensitivity):
    """
    Изменяет чувствительность к типам событий на основе частоты.

    Если событие частое (>20% всех событий): увеличиваем чувствительность
    Если событие редкое (<10% всех событий): уменьшаем чувствительность
    """
    for event_type, current_value in current_sensitivity.items():
        count = event_counts.get(event_type, 0)
        frequency = count / total_events

        direction = (
            1.0 if frequency > self.HIGH_FREQUENCY_THRESHOLD
            else -1.0 if frequency < self.LOW_FREQUENCY_THRESHOLD
            else 0.0
        )

        delta = direction * self.MAX_PARAMETER_DELTA
        new_value = max(0.0, min(1.0, current_value + delta))

        if abs(new_value - current_value) >= self.MIN_PARAMETER_DELTA:
            new_sensitivity[event_type] = new_value
```

#### 2. _adjust_significance_thresholds

```python
def _adjust_significance_thresholds(self, statistics, current_thresholds):
    """
    Изменяет пороги значимости на основе средней значимости событий.

    Если средняя значимость высокая (>0.5): снижаем порог
    Если средняя значимость низкая (<0.2): повышаем порог
    """
    for event_type, current_value in current_thresholds.items():
        avg_significance = event_significance.get(event_type, 0.0) / count

        if avg_significance > self.HIGH_SIGNIFICANCE_THRESHOLD:
            direction = -1.0  # Снижаем порог
        elif avg_significance < self.LOW_SIGNIFICANCE_THRESHOLD:
            direction = 1.0   # Повышаем порог
        else:
            direction = 0.0

        delta = direction * self.MAX_PARAMETER_DELTA
        new_value = max(0.0, min(1.0, current_value + delta))

        if abs(new_value - current_value) >= self.MIN_PARAMETER_DELTA:
            new_thresholds[event_type] = new_value
```

#### 3. _adjust_response_coefficients

```python
def _adjust_response_coefficients(self, statistics, current_coefficients):
    """
    Изменяет коэффициенты реакции на основе частоты паттернов.

    Если паттерн часто используется (>30%): увеличиваем коэффициент
    Если паттерн редко используется (<10%): уменьшаем коэффициент
    """
    for pattern, current_value in current_coefficients.items():
        count = pattern_counts.get(pattern, 0)
        frequency = count / total_patterns

        direction = (
            1.0 if frequency > self.HIGH_PATTERN_FREQUENCY_THRESHOLD
            else -1.0 if frequency < self.LOW_PATTERN_FREQUENCY_THRESHOLD
            else 0.0
        )

        delta = direction * self.MAX_PARAMETER_DELTA
        new_value = max(0.0, min(1.0, current_value + delta))

        if abs(new_value - current_value) >= self.MIN_PARAMETER_DELTA:
            new_coefficients[pattern] = new_value
```

### Thread-safety и валидация

#### 1. Thread-safety через Lock

```python
def __init__(self):
    self._lock = threading.Lock()

def record_changes(self, old_params, new_params, self_state):
    with self._lock:
        # Все операции изменения параметров защищены блокировкой
```

#### 2. Валидация параметров

```python
def adjust_parameters(self, statistics, current_params):
    # Валидация типов
    if not isinstance(current_params, dict):
        raise TypeError("current_params должен быть словарем")

    # Нормализация значений к [0.0, 1.0]
    validated_params = {}
    for key, value_dict in current_params.items():
        validated_params[key] = {}
        for param_name, param_value in value_dict.items():
            normalized_value = max(0.0, min(1.0, float(param_value)))
            validated_params[key][param_name] = normalized_value
```

#### 3. Проверка медленных изменений

```python
# В record_changes проверяем, что изменения не превышают MAX_PARAMETER_DELTA
for key, new_value_dict in new_params.items():
    for param_name, new_value in new_value_dict.items():
        old_value = old_params[key][param_name]
        delta = abs(new_value - old_value)
        if delta > self.MAX_PARAMETER_DELTA + self._VALIDATION_TOLERANCE:
            raise ValueError(f"Изменение слишком большое: {delta}")
```

### Использование параметров

#### 1. В MeaningEngine

```python
# event_type_sensitivity используется для модификации значимости событий
# Чем выше чувствительность, тем больше влияние типа события
modified_significance = base_significance * sensitivity_multiplier
```

#### 2. В Decision

```python
# significance_thresholds используются для модификации порогов игнорирования
# Чем ниже порог, тем больше событий проходит через фильтр
if event_significance > threshold:
    process_event(event)
```

#### 3. В Action

```python
# response_coefficients используются для модификации эффектов действий
# Чем выше коэффициент, тем сильнее эффект действия
effect_strength = base_effect * coefficient
```

## Обоснование

### За выбранное решение

#### ✅ Архитектурная чистота
- **Строгое разделение**: Learning только изменяет параметры, не управляет поведением
- **Отсутствие оптимизации**: нет оценки "лучше/хуже", только статистика
- **Медленные изменения**: максимум 0.01 за раз, постепенная адаптация

#### ✅ Thread-safety
- **Lock protection**: все изменения параметров защищены блокировкой
- **Deep copy**: безопасное объединение параметров без race conditions
- **Validation**: проверка корректности изменений перед применением

#### ✅ Надежность и валидация
- **Type checking**: валидация типов входных параметров
- **Bounds checking**: нормализация значений к допустимым диапазонам
- **Delta validation**: проверка медленных изменений
- **Error handling**: graceful degradation при ошибках

#### ✅ Интеграция с архитектурой
- **Statistics from Memory**: использует существующие данные из памяти
- **Parameters in SelfState**: параметры хранятся в состоянии системы
- **Runtime integration**: вызывается по интервалам в runtime loop
- **Feedback loop**: использует данные из Feedback записей

### Против альтернатив

#### Альтернатива 1: Reinforcement Learning
- **Против**: Нарушает архитектурные ограничения (reward, optimization)
- **Против**: Создает петли обратной связи с поведением
- **Против**: Слишком сложно для текущей стадии проекта

#### Альтернатива 2: Rule-based adaptation
- **Против**: Требует жестких правил и экспертного знания
- **Против**: Менее гибко, чем статистический подход
- **Против**: Трудно поддерживать и расширять

#### Альтернатива 3: Genetic algorithms
- **Против**: Overkill для медленных изменений параметров
- **Против**: Требует популяции и селекции
- **Против**: Не подходит для онлайн адаптации

## Последствия

### Положительные

#### ✅ Постепенная адаптация
- **Без резких изменений**: параметры меняются медленно и предсказуемо
- **На основе опыта**: использует реальную статистику из работы системы
- **Самоорганизация**: система постепенно настраивает себя

#### ✅ Архитектурная целостность
- **Четкие границы**: Learning не пересекается с Decision/Action
- **Отсутствие целей**: нет "оптимизации", только постепенное изменение
- **Статистический подход**: изменения основаны на частотах, не на оценках

#### ✅ Мониторинг и отладка
- **Прозрачность**: все изменения логируются и валидируются
- **Thread-safety**: безопасная работа в многопоточной среде
- **Validation**: автоматическая проверка корректности изменений

#### ✅ Расширяемость
- **Новые параметры**: легко добавить новые типы параметров
- **Новые алгоритмы**: можно добавить новые методы изменения
- **Интеграция**: параметры используются в разных компонентах

### Отрицательные

#### ⚠️ Сложность интерпретации
- **Статистический подход**: изменения не всегда интуитивно понятны
- **Медленная адаптация**: эффект виден только через длительное время
- **Отсутствие гарантий**: нет уверенности в "правильности" изменений

#### ⚠️ Overhead
- **Вычислительная нагрузка**: анализ статистики на каждом интервале
- **Память**: хранение статистики и промежуточных данных
- **Thread-safety**: блокировки добавляют latency

#### ⚠️ Ограничения подхода
- **Только частоты**: изменения основаны только на частотах, не на качестве
- **Линейные алгоритмы**: простые правила изменения без сложной логики
- **Отсутствие памяти**: Learning не помнит предыдущие изменения

### Риски

#### Риск концептуального дрейфа
- **Описание**: Learning может начать использоваться для управления поведением
- **Митигация**: строгие архитектурные ограничения, code review, тесты
- **Вероятность**: Средняя

#### Риск performance degradation
- **Описание**: Анализ статистики может замедлить runtime loop
- **Митигация**: интервальный вызов, оптимизации, профилирование
- **Вероятность**: Низкая (75 тиков интервал)

#### Риск неправильных изменений
- **Описание**: Статистические изменения могут привести к нежелательным эффектам
- **Митигация**: ограничение delta, monitoring, возможность rollback
- **Вероятность**: Низкая (медленные изменения, валидация)

## Связанные документы

- [docs/architecture/overview.md](../architecture/overview.md) — обзор архитектуры
- [src/learning/learning.py](../../src/learning/learning.py) — реализация LearningEngine
- [src/state/self_state.py](../../src/state/self_state.py) — хранение learning_params
- [src/runtime/loop.py](../../src/runtime/loop.py) — интеграция в runtime loop
- [src/meaning/engine.py](../../src/meaning/engine.py) — использование event_type_sensitivity
- [src/decision/decision.py](../../src/decision/decision.py) — использование significance_thresholds
- [src/action/action.py](../../src/action/action.py) — использование response_coefficients
- [src/test/test_learning.py](../../src/test/test_learning.py) — тесты Learning