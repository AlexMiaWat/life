# 12.1 ACTION Work

## Статус: v1.0

## Описание

Модуль действия реализует механизм выполнения внутренних действий системы на основе принятых решений. Действия ограничены внутренними эффектами на состояние системы, без взаимодействия с внешним миром.

## Принципы

- **Внутренние эффекты только**: Действия влияют исключительно на внутреннее состояние системы (энергия, память и т.д.)
- **Минимальная реализация**: Простые, предсказуемые эффекты для обеспечения автономности
- **Запись в память**: Каждое действие фиксируется в памяти для последующего анализа
- **Интеграция с циклом**: Выполняется после принятия решения в основном цикле

## Реализация

Создан модуль `src/action/` с функцией `execute_action(pattern: str, self_state)` для выполнения внутренних действий на основе паттерна decision.

### Файлы:
- `src/action/__init__.py` - экспорт функции
- `src/action/action.py` - реализация функции execute_action

### Логика:
- Для паттерна "dampen": уменьшает энергию на 0.01 (минимальный внутренний эффект)
- Для других паттернов ("absorb", "ignore"): только запись в память без дополнительных изменений
- Интегрировано в loop.py после apply_delta

### Пример кода функции execute_action

```python
from memory.memory import MemoryEntry
import time

def execute_action(pattern: str, self_state):
    """
    Execute action based on pattern.
    Minimal implementation: record action in memory and apply minor state update if applicable.

    ИНТЕГРАЦИЯ: Использует learning_params.response_coefficients и adaptation_params.behavior_coefficients
    для модификации эффектов действий.
    """
    # Record action in memory
    action_entry = MemoryEntry(
        event_type="action",
        meaning_significance=0.0,
        timestamp=time.time()
    )
    self_state.memory.append(action_entry)

    # ИНТЕГРАЦИЯ: Используем параметры для модификации эффектов действий
    learning_params = getattr(self_state, "learning_params", {})
    response_coefficients = learning_params.get("response_coefficients", {})
    adaptation_params = getattr(self_state, "adaptation_params", {})
    behavior_coefficients = adaptation_params.get("behavior_coefficients", {})

    # Получаем коэффициент для паттерна (приоритет adaptation_params)
    coefficient = behavior_coefficients.get(
        pattern, response_coefficients.get(pattern, 1.0)
    )

    # Minimal state update for dampen
    if pattern == "dampen":
        # Minor fatigue effect (assuming energy represents vitality)
        # Модифицируем эффект на основе коэффициента
        fatigue_effect = 0.01 * (1.0 - coefficient)  # Чем выше коэффициент, тем меньше усталость
        new_energy = max(0.0, self_state.energy - fatigue_effect)
        self_state.update_energy(new_energy)

    # Для absorb: если коэффициент низкий, может быть небольшой эффект усталости
    elif pattern == "absorb":
        # Небольшой эффект усталости, если коэффициент низкий
        if coefficient < 0.8:
            fatigue_effect = 0.005 * (1.0 - coefficient)
            new_energy = max(0.0, self_state.energy - fatigue_effect)
            self_state.update_energy(new_energy)

    # For ignore, no additional state changes
```

### Интеграция с Learning и Adaptation

Action модуль интегрирован с Learning Engine (Этап 14) и Adaptation Manager (Этап 15):
- Использует `learning_params.response_coefficients` для базовых коэффициентов эффектов
- Использует `adaptation_params.behavior_coefficients` для адаптированных коэффициентов (приоритет)
- Эффекты действий модифицируются на основе этих коэффициентов

### Безопасное обновление состояния

Action модуль использует безопасные методы обновления состояния:
- `self_state.update_energy()` вместо прямого присваивания
- Это обеспечивает автоматическую валидацию и логирование изменений (см. [self-state.md](self-state.md))

### Пример логов

```
action: executed dampen
```

(выводится зелёным цветом в консоли)

### Ограничения:
- Только внутренние эффекты, без внешних действий (согласно archive/12_action_limits.md)
- Минимальная реализация для автономного выполнения
