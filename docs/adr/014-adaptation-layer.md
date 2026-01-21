# ADR 014: Adaptation Layer

## Статус
✅ Принято

## Дата
2026-01-20

## Контекст

Проект Life нуждался в механизме медленной перестройки поведения на основе статистики Learning. Требовалось реализовать слой Adaptation (Этап 15), который бы постепенно адаптировал параметры поведения без прямого управления Decision и Action.

### Архитектурные ограничения
- **❌ Запрещено**: оптимизация, цели, намерения, reward, utility, scoring
- **❌ Запрещено**: оценка эффективности действий, корректировка поведения
- **❌ Запрещено**: циклы обратной связи, внешние метрики
- **❌ Запрещено**: прямое управление Decision, Action или Feedback
- **✅ Разрешено**: постепенное изменение внутренних параметров поведения (макс. 0.01 за раз)
- **✅ Разрешено**: фиксация изменений без интерпретации
- **✅ Разрешено**: использование внутренней статистики из Learning

### Проблема
Learning изменяет параметры, но нет механизма постепенной адаптации поведения на основе этих изменений. Система остается статичной в поведенческом плане.

## Решение

### Архитектура Adaptation Layer

#### 1. AdaptationManager - основной класс

```python
class AdaptationManager:
    """
    Adaptation Manager - медленная перестройка поведения на основе статистики Learning.

    ВАЖНО: Adaptation не отвечает на вопрос "что делать дальше".
    Adaptation только медленно перестраивает внутренние параметры поведения без интерпретации.
    """

    # Максимальное изменение параметра за один вызов
    MAX_ADAPTATION_DELTA = 0.01
    MIN_ADAPTATION_DELTA = 0.001

    # Максимальный размер истории адаптаций
    MAX_HISTORY_SIZE = 50
```

#### 2. Параметры adaptation_params в SelfState

```python
# Параметры, изменяемые Adaptation (влияют на поведение)
adaptation_params: Dict[str, Dict[str, float]] = field(default_factory=dict)

# Структура параметров:
adaptation_params = {
    "behavior_sensitivity": {  # Чувствительность поведения к типам событий
        "noise": 0.2,
        "decay": 0.2,
        "recovery": 0.2,
        "shock": 0.2,
        "idle": 0.2,
    },
    "behavior_thresholds": {  # Пороги для поведенческих реакций
        "noise": 0.1,
        "decay": 0.1,
        "recovery": 0.1,
        "shock": 0.1,
        "idle": 0.1,
    },
    "behavior_coefficients": {  # Коэффициенты для паттернов поведения
        "dampen": 0.5,
        "absorb": 1.0,
        "ignore": 0.0,
    }
}

# История адаптаций для анализа
adaptation_history: List[Dict] = field(default_factory=list)
```

#### 3. Интеграция в Runtime Loop

```python
ADAPTATION_INTERVAL = 100  # Вызов Adaptation раз в 100 тиков

# В runtime loop:
if self_state.ticks % ADAPTATION_INTERVAL == 0:
    analysis = adaptation_manager.analyze_changes(
        self_state.learning_params, self_state.adaptation_history
    )
    new_behavior_params = adaptation_manager.apply_adaptation(
        analysis, old_behavior_params, self_state
    )
    if new_behavior_params:
        adaptation_manager.store_history(
            old_behavior_params, new_behavior_params, self_state
        )
```

### Методы AdaptationManager

#### 1. analyze_changes - анализ изменений Learning

```python
def analyze_changes(self, learning_params: Dict, adaptation_history: List[Dict]) -> Dict:
    """
    Анализирует изменения параметров от Learning без интерпретации.

    Сравнивает текущие learning_params с историей изменений.
    Извлекает паттерны изменений (без оценки "лучше/хуже").
    """
    analysis = {
        "learning_params_snapshot": learning_params.copy(),
        "recent_changes": {},
        "change_patterns": {},
    }

    # Сравнение с последней адаптацией
    if adaptation_history:
        last_adaptation = adaptation_history[-1]
        last_learning_snapshot = last_adaptation.get("learning_params_snapshot", {})

        for key, current_value_dict in learning_params.items():
            if key in last_learning_snapshot:
                # Фиксируем изменения без интерпретации
                changes = self._compare_params(current_value_dict, last_learning_snapshot[key])
                if changes:
                    analysis["recent_changes"][key] = changes

    # Извлечение паттернов изменений
    if adaptation_history:
        change_frequency = {}
        for entry in adaptation_history[-10:]:  # Последние 10 адаптаций
            # Подсчет частоты изменений параметров
            changes = entry.get("changes", {})
            for param_key, param_changes in changes.items():
                # Фиксируем факты без оценки
                change_frequency[param_key] = change_frequency.get(param_key, 0) + 1
        analysis["change_patterns"] = change_frequency

    return analysis
```

#### 2. apply_adaptation - применение адаптации

```python
def apply_adaptation(self, analysis: Dict, current_behavior_params: Dict, self_state) -> Dict:
    """
    Медленно перестраивает параметры поведения на основе анализа.

    Изменяет параметры, которые влияют на поведение (не Decision/Action напрямую).
    Максимальное изменение: не более 0.01 за раз.
    """

    # Строгая проверка: нет прямого управления Decision/Action
    def _check_forbidden_keys(params_dict: Dict, path: str = "") -> None:
        forbidden_keys_exact = {"decision", "action"}
        for key, value in params_dict.items():
            key_lower = str(key).lower()
            if key_lower in forbidden_keys_exact:
                raise ValueError(f"Adaptation не может напрямую изменять Decision/Action: {key}")
            if isinstance(value, dict):
                _check_forbidden_keys(value, f"{path}.{key}")

    new_params = {}

    # Получаем актуальные learning_params из анализа
    learning_params = analysis.get("learning_params_snapshot", {})

    # 1. Адаптация чувствительности поведения
    if "behavior_sensitivity" in current_behavior_params:
        new_params["behavior_sensitivity"] = self._adapt_behavior_sensitivity(
            learning_params, current_behavior_params["behavior_sensitivity"]
        )
    else:
        # Инициализация при первом запуске
        new_params["behavior_sensitivity"] = self._init_behavior_sensitivity(learning_params)

    # 2. Адаптация порогов реакций
    if "behavior_thresholds" in current_behavior_params:
        new_params["behavior_thresholds"] = self._adapt_behavior_thresholds(
            learning_params, current_behavior_params["behavior_thresholds"]
        )
    else:
        new_params["behavior_thresholds"] = self._init_behavior_thresholds(learning_params)

    # 3. Адаптация коэффициентов паттернов
    if "behavior_coefficients" in current_behavior_params:
        new_params["behavior_coefficients"] = self._adapt_behavior_coefficients(
            learning_params, current_behavior_params["behavior_coefficients"]
        )
    else:
        new_params["behavior_coefficients"] = self._init_behavior_coefficients(learning_params)

    # Проверка медленных изменений (<= 0.01)
    for key, new_value_dict in new_params.items():
        for param_name, new_value in new_value_dict.items():
            old_value = current_behavior_params[key][param_name]
            delta = abs(new_value - old_value)
            if delta > self.MAX_ADAPTATION_DELTA + self._VALIDATION_TOLERANCE:
                raise ValueError(f"Изменение слишком большое: {delta}")

    # Финальная проверка запрещенных ключей
    _check_forbidden_keys(new_params)

    return new_params
```

#### 3. store_history - хранение истории

```python
def store_history(self, old_params: Dict, new_params: Dict, self_state) -> None:
    """
    Хранит историю адаптаций для анализа и возможной обратимости.

    Защищено блокировкой от параллельных вызовов.
    """
    with self._lock:
        changes = {}
        for key, new_value_dict in new_params.items():
            if key in old_params:
                param_changes = {}
                for param_name, new_value in new_value_dict.items():
                    old_value = old_params[key][param_name]
                    if abs(new_value - old_value) >= self.MIN_ADAPTATION_DELTA:
                        param_changes[param_name] = {
                            "old": old_value,
                            "new": new_value,
                            "delta": new_value - old_value,
                        }
                if param_changes:
                    changes[key] = param_changes

        # Создаем запись истории
        history_entry = {
            "timestamp": time.time(),
            "tick": getattr(self_state, "ticks", 0),
            "old_params": old_params.copy(),
            "new_params": new_params.copy(),
            "changes": changes,
            "learning_params_snapshot": getattr(self_state, "learning_params", {}).copy(),
        }

        # Добавляем в историю с ограничением размера
        if not hasattr(self_state, "adaptation_history"):
            self_state.adaptation_history = []

        self_state.adaptation_history.append(history_entry)
        if len(self_state.adaptation_history) > self.MAX_HISTORY_SIZE:
            self_state.adaptation_history = self_state.adaptation_history[-self.MAX_HISTORY_SIZE:]
```

### Алгоритмы адаптации поведения

#### 1. _adapt_behavior_sensitivity

```python
def _adapt_behavior_sensitivity(self, learning_params, current_sensitivity):
    """
    Медленно адаптирует чувствительность поведения к типам событий.

    Использует данные из learning_params.event_type_sensitivity.
    Медленно приближается к значениям Learning.
    """
    new_sensitivity = current_sensitivity.copy()
    learning_sensitivity = learning_params.get("event_type_sensitivity", {})

    for event_type, current_value in current_sensitivity.items():
        if event_type in learning_sensitivity:
            learning_value = learning_sensitivity[event_type]

            # Медленное приближение к значению Learning
            diff = learning_value - current_value
            direction = 1.0 if diff > 0 else -1.0 if diff < 0 else 0.0
            delta = direction * min(abs(diff), self.MAX_ADAPTATION_DELTA)

            new_value = max(0.0, min(1.0, current_value + delta))

            if abs(new_value - current_value) >= self.MIN_ADAPTATION_DELTA:
                new_sensitivity[event_type] = new_value

    return new_sensitivity
```

#### 2. _adapt_behavior_thresholds

```python
def _adapt_behavior_thresholds(self, learning_params, current_thresholds):
    """
    Медленно адаптирует пороги для поведенческих реакций.

    Использует данные из learning_params.significance_thresholds.
    """
    new_thresholds = current_thresholds.copy()
    learning_thresholds = learning_params.get("significance_thresholds", {})

    for event_type, current_value in current_thresholds.items():
        if event_type in learning_thresholds:
            learning_value = learning_thresholds[event_type]

            # Медленное приближение
            diff = learning_value - current_value
            direction = 1.0 if diff > 0 else -1.0 if diff < 0 else 0.0
            delta = direction * min(abs(diff), self.MAX_ADAPTATION_DELTA)

            new_value = max(0.0, min(1.0, current_value + delta))

            if abs(new_value - current_value) >= self.MIN_ADAPTATION_DELTA:
                new_thresholds[event_type] = new_value

    return new_thresholds
```

#### 3. _adapt_behavior_coefficients

```python
def _adapt_behavior_coefficients(self, learning_params, current_coefficients):
    """
    Медленно адаптирует коэффициенты для паттернов поведения.

    Использует данные из learning_params.response_coefficients.
    """
    new_coefficients = current_coefficients.copy()
    learning_coefficients = learning_params.get("response_coefficients", {})

    for pattern, current_value in current_coefficients.items():
        if pattern in learning_coefficients:
            learning_value = learning_coefficients[pattern]

            # Медленное приближение
            diff = learning_value - current_value
            direction = 1.0 if diff > 0 else -1.0 if diff < 0 else 0.0
            delta = direction * min(abs(diff), self.MAX_ADAPTATION_DELTA)

            new_value = max(0.0, min(1.0, current_value + delta))

            if abs(new_value - current_value) >= self.MIN_ADAPTATION_DELTA:
                new_coefficients[pattern] = new_value

    return new_coefficients
```

### Thread-safety и валидация

#### 1. Thread-safety через Lock

```python
def __init__(self):
    self._lock = threading.Lock()

def store_history(self, old_params, new_params, self_state):
    with self._lock:
        # Все изменения истории защищены блокировкой
```

#### 2. Строгая валидация запрещенных действий

```python
def apply_adaptation(self, analysis, current_behavior_params, self_state):
    # Рекурсивная проверка на отсутствие запрещенных ключей
    def _check_forbidden_keys(params_dict, path=""):
        forbidden_keys_exact = {"decision", "action"}
        for key, value in params_dict.items():
            key_lower = str(key).lower()
            if key_lower in forbidden_keys_exact:
                raise ValueError(f"Adaptation не может напрямую изменять {key}")
            if isinstance(value, dict):
                _check_forbidden_keys(value, f"{path}.{key}")

    # Проверяем входные и выходные параметры
    _check_forbidden_keys(current_behavior_params)
    _check_forbidden_keys(new_params)
```

#### 3. Проверка медленных изменений

```python
# В apply_adaptation проверяем, что изменения не превышают MAX_ADAPTATION_DELTA
for key, new_value_dict in new_params.items():
    for param_name, new_value in new_value_dict.items():
        old_value = current_behavior_params[key][param_name]
        delta = abs(new_value - old_value)
        if delta > self.MAX_ADAPTATION_DELTA + self._VALIDATION_TOLERANCE:
            raise ValueError(f"Изменение слишком большое: {delta}")
```

### Использование параметров

#### 1. В MeaningEngine

```python
# behavior_sensitivity используется для модификации appraisal событий
# Чем выше чувствительность, тем больше влияние на meaning
behavior_modifier = adaptation_params.get("behavior_sensitivity", {}).get(event_type, 1.0)
appraisal *= behavior_modifier
```

#### 2. В Decision

```python
# behavior_thresholds используются для модификации порогов выбора паттернов
# Чем ниже порог, тем больше паттернов проходит фильтр
threshold_modifier = adaptation_params.get("behavior_thresholds", {}).get(event_type, 1.0)
effective_threshold = base_threshold * threshold_modifier
```

#### 3. В Action

```python
# behavior_coefficients используются для модификации силы эффектов действий
# Чем выше коэффициент, тем сильнее эффект
coefficient_modifier = adaptation_params.get("behavior_coefficients", {}).get(pattern, 1.0)
effect_strength *= coefficient_modifier
```

## Обоснование

### За выбранное решение

#### ✅ Архитектурная чистота
- **Строгое разделение**: Adaptation не управляет Decision/Action напрямую
- **Отсутствие оптимизации**: нет оценки "эффективности" изменений
- **Медленные изменения**: максимум 0.01 за раз, постепенная адаптация

#### ✅ Thread-safety
- **Lock protection**: все изменения истории защищены блокировкой
- **Deep validation**: проверка всех параметров перед изменениями
- **Error handling**: graceful degradation при проблемах

#### ✅ Надежность и безопасность
- **Forbidden keys check**: невозможность прямого управления Decision/Action
- **Delta validation**: строгий контроль скорости изменений
- **History tracking**: полная traceability всех адаптаций

#### ✅ Интеграция с Learning
- **Analysis first**: анализ изменений Learning перед адаптацией
- **Gradual convergence**: медленное приближение к значениям Learning
- **History awareness**: учет паттернов предыдущих изменений

### Против альтернатив

#### Альтернатива 1: Прямое управление поведением
- **Против**: Нарушает архитектурные ограничения
- **Против**: Создает петли обратной связи
- **Против**: Смешивает адаптацию с принятием решений

#### Альтернатива 2: Копирование параметров Learning
- **Против**: Слишком резкие изменения (мгновенное копирование)
- **Против**: Отсутствие постепенной адаптации
- **Против**: Игнорирует текущее состояние системы

#### Альтернатива 3: Reinforcement learning
- **Против**: Overkill для медленных изменений
- **Против**: Требует reward function и optimization
- **Против**: Не соответствует концепции Life

## Последствия

### Положительные

#### ✅ Постепенная поведенческая адаптация
- **Без резких изменений**: поведение меняется плавно и предсказуемо
- **На основе Learning**: адаптация основана на накопленной статистике
- **Самоорганизация**: система постепенно настраивает свое поведение

#### ✅ Архитектурная целостность
- **Четкие границы**: Adaptation не пересекается с Decision/Action
- **Отсутствие целей**: нет "оптимизации поведения"
- **Статистический подход**: изменения основаны на паттернах Learning

#### ✅ Мониторинг и анализ
- **Полная история**: каждая адаптация фиксируется с timestamp
- **Паттерны изменений**: анализ частоты модификаций параметров
- **Откат при необходимости**: история позволяет анализировать изменения

#### ✅ Расширяемость
- **Новые параметры**: легко добавить новые типы поведенческих параметров
- **Новые алгоритмы**: можно добавить новые методы адаптации
- **Интеграция**: параметры используются в разных компонентах

### Отрицательные

#### ⚠️ Сложность отладки
- **Многослойная логика**: Learning → Analysis → Adaptation → Behavior
- **Опосредованное влияние**: изменения параметров влияют на поведение косвенно
- **Длительная отладка**: эффект виден только через длительное время

#### ⚠️ Overhead
- **Вычислительная нагрузка**: анализ истории при каждом вызове
- **Память**: хранение истории адаптаций
- **Валидация**: множественные проверки запрещенных действий

#### ⚠️ Ограничения подхода
- **Только внутренние параметры**: нельзя напрямую изменять Decision/Action
- **Медленная адаптация**: поведенческие изменения видны не сразу
- **Отсутствие гарантий**: нет уверенности в "правильности" адаптации

### Риски

#### Риск концептуального дрейфа
- **Описание**: Adaptation может начать использоваться для управления поведением
- **Митигация**: строгие проверки запрещенных ключей, архитектурные ограничения
- **Вероятность**: Средняя

#### Риск performance degradation
- **Описание**: Анализ истории может замедлить runtime loop
- **Митигация**: интервальный вызов, оптимизации, ограничение размера истории
- **Вероятность**: Низкая (100 тиков интервал)

#### Риск неправильной адаптации
- **Описание**: Медленные изменения могут привести к нежелательным паттернам
- **Митигация**: monitoring, возможность анализа истории, откат изменений
- **Вероятность**: Низкая (медленные изменения, валидация)

## Связанные документы

- [docs/architecture/overview.md](../architecture/overview.md) — обзор архитектуры
- [src/adaptation/adaptation.py](../../src/adaptation/adaptation.py) — реализация AdaptationManager
- [src/state/self_state.py](../../src/state/self_state.py) — хранение adaptation_params
- [src/runtime/loop.py](../../src/runtime/loop.py) — интеграция в runtime loop
- [src/learning/learning.py](../../src/learning/learning.py) — источник данных для адаптации
- [src/meaning/engine.py](../../src/meaning/engine.py) — использование behavior_sensitivity
- [src/decision/decision.py](../../src/decision/decision.py) — использование behavior_thresholds
- [src/action/action.py](../../src/action/action.py) — использование behavior_coefficients
- [src/test/test_adaptation.py](../../src/test/test_adaptation.py) — тесты Adaptation