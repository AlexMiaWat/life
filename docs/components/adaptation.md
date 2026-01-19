# 15 — Adaptation Manager

## Назначение

Adaptation Manager — это механизм медленной перестройки поведения на основе статистики Learning без оптимизации, целей или активного управления поведением.

**ВАЖНО:** Adaptation НЕ является:
- ❌ Оптимизацией или reinforcement learning
- ❌ Активным контролем или управлением поведением
- ❌ Системой с целями и намерениями
- ❌ Оценкой эффективности действий
- ❌ Прямым управлением Decision/Action

Adaptation — это только **медленная перестройка внутренних параметров поведения** на основе статистики из Learning.

## Текущий статус

✅ **Реализован** (v1.0, Этап 15)
*   Файл: [`src/adaptation/adaptation.py`](../../src/adaptation/adaptation.py)
*   Интегрирован в Runtime Loop
*   Протестирован: [`src/test/test_adaptation.py`](../../src/test/test_adaptation.py)

### ⚠️ Текущие ограничения

**Параметры Adaptation пока не используются в системе:**

Параметры `adaptation_params` (behavior_sensitivity, behavior_thresholds, behavior_coefficients) изменяются Adaptation Manager, но **в текущей версии НЕ применяются** в:
- Decision Engine (выбор паттернов реакции)
- Action Engine (выполнение действий)
- MeaningEngine (интерпретация событий)

Это означает, что Adaptation изменяет параметры "в пустоту" - они сохраняются в SelfState и в snapshots, но не влияют на поведение системы.

**Планы на будущее:**
- Параметры могут быть использованы другими компонентами (если это не нарушит архитектурные ограничения)
- Или интегрированы напрямую в Decision/MeaningEngine (если это не нарушит архитектурные ограничения)

**Статус:** Это подготовка к будущей интеграции, а не баг. Параметры корректно изменяются и сохраняются.

### Логика "медленного копирования" Learning

Adaptation реализует логику **медленного приближения** к значениям параметров Learning, а не собственной адаптации:

1. **Механизм:** Adaptation сравнивает текущие значения `adaptation_params` с соответствующими значениями `learning_params`
2. **Изменение:** Если есть разница, Adaptation медленно приближает `adaptation_params` к `learning_params` (макс. 0.01 за раз)
3. **Направление:** Направление изменения определяется знаком разницы (learning_value - current_value)
4. **Ограничение:** Изменение ограничено `MAX_ADAPTATION_DELTA = 0.01` за один вызов

**Почему это не оптимизация:**
- Adaptation не оценивает эффективность изменений Learning
- Adaptation не выбирает "лучшие" значения
- Adaptation просто медленно следует за изменениями Learning
- Это соответствует архитектурным ограничениям: Adaptation не имеет собственной логики оценки, только реакция на изменения Learning

**Пример:**
- Learning изменил `event_type_sensitivity["noise"]` с 0.2 до 0.25 (delta = 0.05)
- Adaptation имеет `behavior_sensitivity["noise"] = 0.2`
- Adaptation медленно приближается: 0.2 → 0.21 (delta = 0.01, первый вызов)
- На следующем вызове: 0.21 → 0.22 (delta = 0.01, второй вызов)
- И так далее, пока не достигнет 0.25

**Это не баг, а намеренное ограничение:** Adaptation не имеет собственной логики адаптации, только медленное следование за Learning.

## Архитектурные ограничения

### Абсолютные запреты

1. **Запрет на активное изменение поведения**
   - ❌ Не инициирует новые действия
   - ❌ Не корректирует прошлые действия
   - ❌ Не управляет Decision или Action напрямую

2. **Запрет на цели и оптимизацию**
   - ❌ Не направлено на достижение результата
   - ❌ Не улучшает выбор вариантов
   - ❌ Не использует reward / utility / scoring

3. **Запрет на циклы обратной связи**
   - ❌ Не строит цепочки Decision → Action → Feedback → Adaptation → Decision
   - ❌ Не инициирует корректирующие действия

4. **Запрет на внешние зависимости**
   - ❌ Не зависит от метрик или KPI
   - ❌ Не оценивает среду для корректировки поведения

### Разрешённый минимум

Adaptation **может**:
- ✅ Медленно изменять внутренние параметры поведения (макс. 0.01 за раз)
- ✅ Фиксировать изменения без интерпретации
- ✅ Использовать внутреннюю статистику из Learning
- ✅ Хранить историю адаптаций для обратимости

Adaptation **не может**:
- ❌ Оценивать эффективность изменений
- ❌ Вмешиваться в Decision или Action
- ❌ Инициировать Feedback
- ❌ Управлять поведением напрямую

## Реализация

### Основные методы

#### `analyze_changes(learning_params: Dict, adaptation_history: List) -> Dict`

Анализирует изменения параметров от Learning:
- Сравнивает текущие `learning_params` с историей изменений
- Извлекает паттерны изменений (без интерпретации)
- Возвращает словарь с анализом изменений

**ВАЖНО:** Без оценки эффективности, без выбора "лучших" изменений. Только фиксирует факты изменений.

#### `apply_adaptation(analysis: Dict, current_behavior_params: Dict, self_state) -> Dict`

Медленно перестраивает параметры поведения на основе анализа:
- Изменение чувствительности к типам событий (`behavior_sensitivity`)
- Изменение порогов для реакций (`behavior_thresholds`)
- Изменение коэффициентов для паттернов (`behavior_coefficients`)

**Ограничения:**
- Максимальное изменение: `MAX_ADAPTATION_DELTA = 0.01` за раз
- Минимальное изменение: `MIN_ADAPTATION_DELTA = 0.001` (чтобы избежать микро-изменений)
- Изменения основаны на данных Learning, НЕ на оценке эффективности
- **НЕ изменяет** Decision или Action напрямую

**Реализованные вспомогательные методы:**
- `_adapt_behavior_sensitivity()` - адаптация чувствительности к типам событий
- `_adapt_behavior_thresholds()` - адаптация порогов для реакций
- `_adapt_behavior_coefficients()` - адаптация коэффициентов для паттернов
- `_init_behavior_sensitivity()` - инициализация чувствительности
- `_init_behavior_thresholds()` - инициализация порогов
- `_init_behavior_coefficients()` - инициализация коэффициентов

#### `store_history(old_params: Dict, new_params: Dict, self_state) -> None`

Хранит историю адаптаций для обратимости:
- Сохраняет изменения в `self_state.adaptation_history`
- Фиксирует timestamp и изменения без интерпретации
- Ограничивает размер истории (максимум 50 записей)

**ВАЖНО:** Только хранение фактов, без интерпретации и оптимизации.

### Параметры Adaptation

Параметры хранятся в `SelfState.adaptation_params`:

```python
adaptation_params = {
    "behavior_sensitivity": {
        "noise": 0.2,
        "decay": 0.2,
        "recovery": 0.2,
        "shock": 0.2,
        "idle": 0.2,
    },
    "behavior_thresholds": {
        "noise": 0.1,
        "decay": 0.1,
        "recovery": 0.1,
        "shock": 0.1,
        "idle": 0.1,
    },
    "behavior_coefficients": {
        "dampen": 0.5,
        "absorb": 1.0,
        "ignore": 0.0,
    },
}
```

История адаптаций хранится в `SelfState.adaptation_history`:

```python
adaptation_history = [
    {
        "timestamp": float,  # Время адаптации
        "tick": int,  # Номер тика
        "old_params": Dict,  # Параметры до адаптации
        "new_params": Dict,  # Параметры после адаптации
        "changes": Dict,  # Только измененные параметры
        "learning_params_snapshot": Dict  # Снимок learning_params на момент адаптации
    }
]
```

### Интеграция в Runtime Loop

Adaptation вызывается периодически (раз в 100 тиков, реже чем Learning - 75 тиков):

```python
if self_state.ticks > 0 and self_state.ticks % adaptation_interval == 0:
    # Анализируем изменения от Learning
    analysis = adaptation_manager.analyze_changes(
        self_state.learning_params,
        getattr(self_state, "adaptation_history", []),
    )
    
    # Применяем адаптацию
    new_behavior_params = adaptation_manager.apply_adaptation(
        analysis,
        getattr(self_state, "adaptation_params", {}),
        self_state
    )
    
    # Сохраняем историю
    if new_behavior_params:
        adaptation_manager.store_history(
            current_behavior_params,
            new_behavior_params,
            self_state
        )
```

**Порядок вызова:**
1. Feedback (наблюдение последствий)
2. Learning (раз в 75 тиков) - изменение `learning_params`
3. Adaptation (раз в 100 тиков) - перестройка поведения на основе `learning_params`
4. Planning/Intelligence

## Примеры использования

### Пример 1: Адаптация чувствительности к событиям

Если Learning изменил `event_type_sensitivity` для `noise` с 0.2 до 0.25, Adaptation медленно адаптирует `behavior_sensitivity` для `noise` (макс. +0.01 за раз).

**БЕЗ оценки эффективности**, только медленное приближение к значению Learning.

### Пример 2: Адаптация порогов для реакций

Если Learning изменил `significance_thresholds` для `shock` с 0.1 до 0.15, Adaptation медленно адаптирует `behavior_thresholds` для `shock` (макс. +0.01 за раз).

**БЕЗ оценки эффективности**, только медленное приближение к значению Learning.

### Пример 3: Адаптация коэффициентов для паттернов

Если Learning изменил `response_coefficients` для `dampen` с 0.5 до 0.6, Adaptation медленно адаптирует `behavior_coefficients` для `dampen` (макс. +0.01 за раз).

**БЕЗ оценки эффективности**, только медленное приближение к значению Learning.

## Тестирование

### Unit тесты

- `test_analyze_changes_*` — проверка анализа изменений от Learning
- `test_apply_adaptation_*` — проверка медленного изменения параметров поведения
- `test_store_history_*` — проверка хранения истории адаптаций
- `test_no_optimization_methods` — проверка отсутствия запрещенных методов
- `test_no_goals_or_rewards` — проверка отсутствия целей и reward
- `test_no_direct_decision_action_control` — проверка отсутствия прямого управления Decision/Action

### Интеграционные тесты

- `test_adaptation_uses_learning_params` — Adaptation использует параметры Learning
- `test_adaptation_reacts_to_learning_changes` — Adaptation реагирует на изменения Learning
- `test_adaptation_frequency_in_runtime` — частота вызова Adaptation в runtime loop
- `test_adaptation_order_with_learning` — порядок вызова Adaptation после Learning
- `test_adaptation_persistence_in_snapshots` — сохранение в snapshots

### Статические тесты

- `test_forbidden_patterns` — проверка отсутствия запрещенных паттернов в коде
- `test_slow_changes_enforced` — принудительное медленное изменение (<= 0.01)

## Взаимодействие с другими компонентами

### Learning

Adaptation использует Learning как источник статистики:
- Читает `learning_params` для анализа изменений
- Использует изменения Learning для медленной адаптации параметров поведения
- **НЕ изменяет** Learning напрямую
- **НЕ зависит** от Learning (может работать с пустыми параметрами)

### Memory

Adaptation **НЕ использует** Memory напрямую:
- Adaptation работает только с данными Learning
- Memory используется Learning, а не Adaptation

### SelfState

Adaptation обновляет `self_state.adaptation_params` и `self_state.adaptation_history`:
- Медленно изменяет параметры поведения (<= 0.01 за раз)
- Сохраняет параметры и историю в snapshots
- **НЕ изменяет** другие поля SelfState (energy, stability, integrity, learning_params)

**ВАЖНО:** Параметры сохраняются, но в текущей версии НЕ используются другими компонентами.

## Контрольное правило

> **Adaptation не отвечает на вопрос "что делать дальше".**

Он отвечает только на вопрос:

> **"изменились ли внутренние параметры поведения медленно и нейтрально"**

И даже это без интерпретации.

## Архитектурный стоп-сигнал

Если при развитии Adaptation появляется ощущение, что:
- Life «самокорректируется»
- Life «оптимизирует поведение»
- Life «действует целенаправленно»

→ развитие слоя Adaptation **немедленно останавливается**.

Adaptation — не воля.  
Adaptation — не оптимизация.  
Adaptation — не контроль.  
Adaptation — медленное внутреннее изменение без цели.

## Документация ограничений

Подробные архитектурные ограничения описаны в:
- [Adaptation Limits](../concepts/adaptation.md) — концептуальные ограничения

## История

- **2026-01-26:** Реализован Adaptation Manager (v1.0)
- **2026-01-26:** Добавлены тесты (unit, integration, static)
- **2026-01-26:** Интегрирован в Runtime Loop (раз в 100 тиков, после Learning)
- **2026-01-26:** Добавлены поля `adaptation_params` и `adaptation_history` в SelfState
- **2026-01-19:** Исправлены проблемы из отчета Скептика:
  - Улучшена проверка на запрещенные параметры (явная проверка ключей вместо str())
  - Исправлена логика обновления параметров в loop.py (глубокое объединение)
  - Исправлена передача параметров в store_history() (актуальные параметры)
  - Убраны избыточные проверки hasattr/getattr
  - Исправлена инициализация параметров (использование self_state.adaptation_params)
  - Добавлены тесты на частичное обновление параметров и корректность истории
  - Документирована логика "медленного копирования" Learning
