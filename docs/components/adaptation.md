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
*   Критические исправления: [`src/test/test_critical_fixes.py`](../../src/test/test_critical_fixes.py)

### Критические исправления (task_1768908574)

#### Унификация обработки `None` в `store_history()`

**Проблема:** В методе `store_history()` значения `None` молча игнорировались, что создавало несогласованность с методом `apply_adaptation()`, где при обнаружении `None` выбрасывается исключение.

**Решение:** Добавлено логирование предупреждения при обнаружении `None` значений с последующим пропуском параметра:
```python
if old_value is None or new_value is None:
    logger.warning(
        f"Параметр {key}.{param_name} имеет значение None: "
        f"old_value={old_value}, new_value={new_value}. Пропускаем."
    )
    continue
```

**Обоснование:** Унифицированная обработка `None` с логированием для отслеживания проблем, но без остановки выполнения системы.

#### Улучшение типобезопасности

**Изменение:** Добавлены type hints для параметра `self_state` в методе `store_history()`:
```python
def store_history(
    self, old_params: Dict, new_params: Dict, self_state: "SelfState"
) -> None:
```

#### Константы

Все константы Adaptation Manager определены в модуле и имеют документацию с обоснованием выбора значений:
- `MAX_ADAPTATION_DELTA = 0.01` - максимальное изменение параметра за один вызов
- `MIN_ADAPTATION_DELTA = 0.001` - минимальное изменение для применения
- `_VALIDATION_TOLERANCE = 0.001` - допуск для проверки изменений параметров
- `MAX_HISTORY_SIZE = 50` - максимальный размер истории адаптаций

### ✅ Интеграция параметров

**Параметры Adaptation теперь используются в системе:**

Параметры `adaptation_params` (behavior_sensitivity, behavior_thresholds, behavior_coefficients) изменяются Adaptation Manager и **активно применяются** в:
- ✅ MeaningEngine (интерпретация событий) - `appraisal()`, `response_pattern()`, `process()`
- ✅ Decision Engine (выбор паттернов реакции) - `decide_response()`
- ✅ Action Engine (выполнение действий) - `execute_action()`

**Как используются параметры:**

1. **`behavior_sensitivity`** - используется в `MeaningEngine.appraisal()` для дополнительной модификации значимости событий на основе адаптированной чувствительности
2. **`behavior_thresholds`** - используется в `MeaningEngine.response_pattern()` и `Decision.decide_response()` для определения адаптированных порогов значимости
3. **`behavior_coefficients`** - используется в `MeaningEngine.process()` и `Action.execute_action()` для модификации коэффициентов реакции (приоритет над `learning_params.response_coefficients`)

**Интеграция с Learning:**
- Adaptation использует параметры Learning для медленной перестройки поведения
- Adaptation создает `adaptation_params` на основе `learning_params`
- Оба набора параметров используются в системе, при этом `adaptation_params` имеет приоритет

**Статус:** Параметры полностью интегрированы и влияют на поведение системы.

### Детальное описание влияния параметров на поведение

#### 1. `behavior_sensitivity` - Дополнительное влияние на значимость событий

**Где используется:** `MeaningEngine.appraisal()`

**Как работает:**
- Работает совместно с `learning_params.event_type_sensitivity`
- Значение параметра в диапазоне [0.0, 1.0] преобразуется в модификатор [0.5, 1.0]
- Модификаторы от Learning и Adaptation усредняются для предотвращения квадратичного эффекта
- Высокое значение → событие становится более значимым
- Низкое значение → событие становится менее значимым

**Пример:**
- `behavior_sensitivity["shock"] = 0.9` + `event_type_sensitivity["shock"] = 0.8` → средний модификатор ≈ 0.85
- Это предотвращает резкие изменения значимости (макс. 1.5x)

**Ограничение:** Максимальное изменение значимости ограничено 1.5x для соблюдения принципа медленного изменения.

#### 2. `behavior_thresholds` - Адаптированные пороги для реакций

**Где используется:** `MeaningEngine.response_pattern()`, `Decision.decide_response()`

**Как работает:**
- Определяет адаптированные пороги значимости для типов событий
- Используется вместо `learning_params.significance_thresholds` при наличии
- Высокий порог → больше событий игнорируется или требуют dampen
- Низкий порог → меньше событий игнорируется

**Пример:**
- `behavior_thresholds["noise"] = 0.4` → события noise с значимостью < 0.4 игнорируются
- В `Decision.decide_response()` используется среднее значение порогов для модификации порога dampen

#### 3. `behavior_coefficients` - Приоритетные коэффициенты для паттернов

**Где используется:** `MeaningEngine.process()`, `Action.execute_action()`

**Как работает:**
- Определяет коэффициенты модификации эффектов паттернов реакции
- **Имеет приоритет** над `learning_params.response_coefficients`
- Применяется к `impact` событий при обработке паттернов
- Высокий коэффициент → эффект усиливается
- Низкий коэффициент → эффект ослабляется

**Пример:**
- `behavior_coefficients["dampen"] = 0.4` → эффект dampen уменьшается в 0.4 раза (приоритет над learning)
- `behavior_coefficients["amplify"] = 1.3` → эффект amplify увеличивается в 1.3 раза

**Приоритет:** `behavior_coefficients` имеет приоритет над `response_coefficients` из Learning.

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

**ВАЖНО:** Параметры сохраняются и активно используются другими компонентами (MeaningEngine, Decision, Action).

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

## Механизм обратимости адаптаций

### Назначение

Механизм обратимости позволяет откатывать параметры адаптации к предыдущим состояниям без нарушения архитектурных принципов. Откат **НЕ является** оптимизацией или улучшением поведения — это только восстановление сохраненных состояний.

### Архитектурные принципы отката

- **Откат только назад во времени** — запрещен откат "вперед" или к будущим состояниям
- **Соблюдение медленных изменений** — откат не нарушает лимит MAX_ADAPTATION_DELTA (0.01)
- **Без интерпретации** — откат не анализирует эффективность или выбирает "лучшие" состояния
- **Только восстановление** — откат восстанавливает параметры из истории без модификации

### Методы отката

#### `get_rollback_options(self_state) -> List[Dict]`

Возвращает доступные варианты отката из истории адаптаций.

```python
options = adaptation_manager.get_rollback_options(self_state)
# Возвращает список с timestamp, tick, time_diff_seconds, description
```

#### `rollback_to_timestamp(timestamp, self_state, structured_logger=None) -> Dict`

Откатывает параметры к состоянию на указанное время.

```python
result = adaptation_manager.rollback_to_timestamp(timestamp, self_state)
# Возвращает {"success": bool, "rolled_back_params": Dict, "error": str}
```

#### `rollback_steps(steps, self_state, structured_logger=None) -> Dict`

Откатывает параметры на указанное количество шагов назад.

```python
result = adaptation_manager.rollback_steps(2, self_state)  # Откат на 2 шага назад
```

### Валидация отката

Откат проходит многоуровневую валидацию:

1. **Временная валидация** — откат только к прошлым состояниям
2. **Доступность данных** — проверка наличия записей в истории
3. **Лимит изменений** — откат не нарушает принцип медленных изменений (<= 0.01)
4. **Структурная валидация** — параметры соответствуют ожидаемой структуре

### HTTP API для отката

#### GET /adaptation/rollback/options

Получить доступные варианты отката.

```bash
curl http://localhost:8000/adaptation/rollback/options
```

**Ответ:**
```json
{
  "options": [
    {
      "timestamp": 1705708800.0,
      "tick": 100,
      "changes_count": 2,
      "time_diff_seconds": 300.5,
      "description": "behavior_sensitivity.noise, behavior_thresholds.shock"
    }
  ],
  "total_options": 1
}
```

#### GET /adaptation/history

Получить историю адаптаций.

```bash
curl http://localhost:8000/adaptation/history
```

#### POST /adaptation/rollback

Выполнить откат.

```bash
# Откат к timestamp
curl -X POST http://localhost:8000/adaptation/rollback \
  -H "Content-Type: application/json" \
  -d '{"type": "timestamp", "timestamp": 1705708800.0}'

# Откат на 2 шага назад
curl -X POST http://localhost:8000/adaptation/rollback \
  -H "Content-Type: application/json" \
  -d '{"type": "steps", "steps": 2}'
```

**Ответ при успехе:**
```json
{
  "success": true,
  "rolled_back_params": {
    "behavior_sensitivity": {"noise": 0.15},
    "behavior_thresholds": {"noise": 0.08},
    "behavior_coefficients": {"dampen": 0.45}
  },
  "target_timestamp": 1705708800.0,
  "actual_timestamp": 1705708800.0,
  "tick": 100
}
```

### Логирование откатов

Все операции отката логируются через StructuredLogger в формате:

```json
{
  "timestamp": 1705708800.0,
  "stage": "adaptation_rollback",
  "correlation_id": "chain_123",
  "success": true,
  "target_timestamp": 1705708800.0,
  "actual_timestamp": 1705708800.0,
  "tick": 100,
  "rolled_back_params": {...}
}
```

### Примеры использования

#### Пример 1: Откат после нежелательных изменений

```python
# Получить доступные варианты отката
options = adaptation_manager.get_rollback_options(self_state)
print(f"Доступно {len(options)} вариантов отката")

# Выполнить откат к первому варианту
if options:
    result = adaptation_manager.rollback_to_timestamp(
        options[0]["timestamp"], self_state
    )
    if result["success"]:
        print("Откат выполнен успешно")
        self_state.save_snapshot()  # Сохранить изменения
```

#### Пример 2: API откат через HTTP

```bash
# Проверить доступные варианты
curl http://localhost:8000/adaptation/rollback/options

# Выполнить откат на 3 шага назад
curl -X POST http://localhost:8000/adaptation/rollback \
  -H "Content-Type: application/json" \
  -d '{"type": "steps", "steps": 3}'
```

### Ограничения и безопасность

- **Максимальная история**: 50 записей (configurable через MAX_HISTORY_SIZE)
- **Лимит изменений**: откат ограничен MAX_ADAPTATION_DELTA (0.01) для предотвращения резких изменений
- **Временные ограничения**: откат только к прошлым состояниям
- **Архитектурная защита**: откат не затрагивает Decision/Action и не является оптимизацией

### Тестирование механизма отката

Механизм отката покрыт комплексными тестами:

- **Unit-тесты**: валидация, откат к timestamp/steps, проверка лимитов
- **Integration-тесты**: API endpoints, работа с реальным состоянием
- **Validation-тесты**: проверка безопасности и соответствия архитектуре

```bash
# Запуск тестов отката
pytest src/test/test_adaptation.py::TestAdaptationRollback -v
pytest src/test/test_adaptation_rollback_api.py -v
```

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
- **2026-01-26:** Интегрированы параметры в систему:
  - Параметры `adaptation_params` теперь используются в MeaningEngine, Decision и Action
  - Добавлены тесты на использование параметров при деградации
  - Добавлены тесты на восстановление параметров из snapshot
  - Обновлена документация с описанием интеграции
- **2026-01-21:** Реализован механизм обратимости адаптаций (v1.1):
  - Добавлены методы `get_rollback_options()`, `rollback_to_timestamp()`, `rollback_steps()`
  - Интегрирован StructuredLogger для логирования операций отката
  - Добавлена многоуровневая валидация отката (временная, структурная, лимит изменений)
  - Создан HTTP API: GET /adaptation/rollback/options, GET /adaptation/history, POST /adaptation/rollback
  - Написаны комплексные тесты для механизма отката (unit и integration)
  - Обновлена документация с примерами использования и API
