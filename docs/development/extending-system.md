# Руководство по расширению системы

> **Назначение:** Инструкции для разработчиков по добавлению новых модулей и компонентов в систему Life

## Общие принципы

### Архитектурные ограничения

Перед добавлением нового модуля убедитесь, что он соответствует философии проекта:

1. **Нет целей и оптимизации** — модуль не должен стремиться к достижению целей или оптимизировать поведение
2. **Нет активного управления** — модуль не должен напрямую управлять другими модулями
3. **Медленные изменения** — изменения должны происходить постепенно (макс. 0.01 за раз)
4. **Без интерпретации** — модуль фиксирует факты, но не оценивает их эффективность

### Структура модуля

Каждый новый модуль должен:

1. Находиться в отдельной папке `src/<module_name>/`
2. Содержать файл `__init__.py` для экспорта основных функций
3. Иметь документацию в `docs/components/<module_name>.md`
4. Иметь тесты в `src/test/test_<module_name>.py`

## Шаги добавления нового модуля

### Шаг 1: Создание структуры модуля

```bash
mkdir -p src/new_module
touch src/new_module/__init__.py
touch src/new_module/new_module.py
```

### Шаг 2: Реализация базового класса/функций

Пример структуры модуля:

```python
# src/new_module/new_module.py
from typing import Dict, Any
from state.self_state import SelfState

class NewModule:
    """Описание назначения модуля."""

    def __init__(self):
        """Инициализация модуля."""
        pass

    def process(self, self_state: SelfState) -> Dict[str, Any]:
        """
        Основной метод обработки.

        Args:
            self_state: Текущее состояние системы

        Returns:
            Словарь с результатами обработки
        """
        # Реализация логики
        return {}
```

### Шаг 3: Интеграция в Runtime Loop

Добавьте вызов модуля в `src/runtime/loop.py`:

```python
from new_module.new_module import NewModule

# В функции run_loop():
new_module = NewModule()
new_module_interval = 50  # Вызов раз в N тиков

# В цикле тиков:
if self_state.ticks > 0 and self_state.ticks % new_module_interval == 0:
    try:
        result = new_module.process(self_state)
        # Обработка результата
    except Exception as e:
        # Обработка ошибок (уменьшение integrity)
        self_state.apply_delta({"integrity": -0.01})
        print(f"[ERROR] NewModule failed: {e}")
```

### Шаг 4: Добавление полей в SelfState

Если модуль требует хранения состояния, добавьте поля в `src/state/self_state.py`:

```python
@dataclass
class SelfState:
    # ... существующие поля ...
    new_module_data: Dict[str, Any] = field(default_factory=dict)
```

### Шаг 5: Создание документации

Создайте файл `docs/components/new-module.md`:

```markdown
# New Module

## Назначение
Описание назначения модуля.

## Текущий статус
✅ **Реализован** (v1.0)

## Архитектурные ограничения
- Что модуль НЕ делает
- Что модуль делает

## Пример использования
[Примеры кода]

## Интеграция
[Описание интеграции в runtime loop]
```

### Шаг 6: Написание тестов

Создайте файл `src/test/test_new_module.py`:

```python
import pytest
from src.new_module.new_module import NewModule
from src.state.self_state import SelfState

def test_new_module_basic():
    """Базовый тест модуля."""
    module = NewModule()
    state = SelfState()
    result = module.process(state)
    assert isinstance(result, dict)

def test_new_module_integration():
    """Интеграционный тест с SelfState."""
    # Тест интеграции
    pass
```

### Шаг 7: Обновление INDEX.md

Добавьте ссылку на новый модуль в `docs/INDEX.md`:

```markdown
- [**New Module**](components/new-module.md) — описание модуля
```

## Примеры расширений

### Пример 1: Добавление нового типа события

1. Добавьте тип в `src/environment/generator.py`:

```python
EVENT_TYPES = {
    "noise": 0.4,
    "decay": 0.3,
    "recovery": 0.2,
    "shock": 0.05,
    "idle": 0.05,
    "new_event": 0.1,  # Новый тип
}
```

2. Обновите `MeaningEngine` для обработки нового типа
3. Добавьте тесты

### Пример 2: Добавление нового паттерна реакции

1. Добавьте паттерн в `src/decision/decision.py`:

```python
def decide_response(self_state, meaning):
    # ... существующая логика ...
    if new_condition:
        return "new_pattern"
```

2. Добавьте обработку в `src/action/action.py`:

```python
def execute_action(pattern, self_state):
    if pattern == "new_pattern":
        # Обработка нового паттерна
        pass
```

3. Обновите документацию и тесты

## Интеграция с существующими модулями

### Использование Memory

```python
from memory.memory import MemoryEntry

# Чтение памяти
for entry in self_state.memory:
    if entry.event_type == "target_type":
        # Обработка
        pass

# Запись в память
entry = MemoryEntry(
    event_type="event_type",
    meaning_significance=0.5,
    timestamp=time.time()
)
self_state.memory.append(entry)
```

### Использование Learning/Adaptation параметров

```python
# Чтение параметров Learning
learning_params = self_state.learning_params
sensitivity = learning_params.get("event_type_sensitivity", {})

# Чтение параметров Adaptation
adaptation_params = self_state.adaptation_params
behavior_sensitivity = adaptation_params.get("behavior_sensitivity", {})
```

### Использование Feedback

```python
from feedback import register_action, observe_consequences

# Регистрация действия
register_action(
    action_id="action_123",
    pattern="dampen",
    state_before={"energy": 50.0},
    timestamp=time.time(),
    pending_actions=pending_actions
)

# Наблюдение последствий (в runtime loop)
feedback_records = observe_consequences(
    self_state, pending_actions, event_queue
)
```

## Проверка соответствия архитектуре

Перед коммитом убедитесь:

- [ ] Модуль не содержит оптимизацию или цели
- [ ] Модуль не управляет другими модулями напрямую
- [ ] Изменения медленные (<= 0.01 за раз)
- [ ] Модуль не интерпретирует эффективность
- [ ] Добавлены тесты (unit + integration)
- [ ] Обновлена документация
- [ ] Обновлен INDEX.md
- [ ] Код соответствует стилю проекта

## Полезные ссылки

- [Архитектура системы](../architecture/overview.md) — общая архитектура
- [Статус проекта](status.md) — текущий статус всех модулей
- [Инструкции для LLM](llm-instructions.md) — инструкции для AI-агентов
- [Концепции](../concepts/) — концептуальные документы

## Вопросы и поддержка

При возникновении вопросов:

1. Изучите существующие модули как примеры
2. Проверьте архитектурные ограничения в `docs/concepts/`
3. Обратитесь к документации компонентов
4. Проверьте тесты существующих модулей
