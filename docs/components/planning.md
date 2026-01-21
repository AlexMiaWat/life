# Planning — Компонент планирования

> **Версия:** v1.1
> **Статус:** Реализован и интегрирован
> **Модуль:** `src/planning/planning.py`
> **Интеграция:** Субъективное время влияет на параметры фиксации последовательностей
> **Интеграция:** Субъективное время влияет на параметры фиксации последовательностей

---

## Обзор

Planning — минимальный компонент фиксации потенциальных последовательностей событий. Реализует нейтральное хранение без оценки, выбора или влияния на поведение системы.

**Ключевой принцип:** Planning не отвечает на вопрос «что делать», он отвечает только на вопрос «какие последовательности возможны».

---

## Назначение

Planning выполняет следующие функции:
- Фиксирует потенциальные последовательности из недавних событий
- Хранит метаданные об используемых источниках (proxy)
- Записывает данные в `self_state.planning` без побочных эффектов

---

## API

### `record_potential_sequences(self_state: SelfState) -> None`

Минимальная нейтральная фиксация потенциальных последовательностей с учетом субъективного времени.

**Параметры:**
- `self_state` — текущее состояние системы

**Возвращает:**
- `None` — записывает данные напрямую в `self_state.planning`

**Новая функциональность (v1.1):**
Функция анализирует восприятие времени и модифицирует параметры фиксации последовательностей:

- **Ускоренное восприятие времени** (`time_ratio >= 1.1`): `min_sequence_length = 3`, `max_sequences = 2`
- **Замедленное восприятие времени** (`time_ratio <= 0.9`): `min_sequence_length = 2`, `max_sequences = 1`
- **Нормальное восприятие времени** (`0.9 < time_ratio < 1.1`): `min_sequence_length = 2`, `max_sequences = 1`

**Пример использования:**

```python
from planning.planning import record_potential_sequences
from state.self_state import SelfState

state = SelfState()
state.recent_events = ["noise", "decay", "recovery"]
state.energy_history = [100, 99, 98]
state.stability_history = [1.0, 0.99, 0.98]

record_potential_sequences(state)

print(state.planning)
# {'potential_sequences': [['decay', 'recovery']],
#  'sources_used': {'memory_proxy': 3, 'learning_proxy': 3, 'adaptation_proxy': 3}}
```

---

## Структура данных

После вызова `record_potential_sequences()` в `self_state.planning` записывается:

```python
{
    'potential_sequences': List[List[str]],  # последовательности разной длины в зависимости от восприятия времени
    'sources_used': {
        'memory_proxy': int,      # количество recent_events
        'learning_proxy': int,    # количество stability_history
        'adaptation_proxy': int   # количество energy_history
    }
}
```

**Динамическая генерация последовательностей:**
- **Ускоренное восприятие**: Создает последовательности длиной 3, 4, ... (до `max_sequences = 2`)
- **Замедленное восприятие**: Создает последовательности длиной 2 (максимум 1 последовательность)
- **Нормальное восприятие**: Создает последовательности длиной 2 (максимум 1 последовательность)

### Поля:

| Поле | Тип | Описание |
|------|-----|----------|
| `potential_sequences` | `List[List[str]]` | Список потенциальных последовательностей событий |
| `sources_used` | `dict` | Метаданные об использованных proxy-источниках |

---

## Интеграция в Runtime Loop

Planning вызывается в `src/runtime/loop.py` после обработки событий MeaningEngine:

```python
# В методе tick() класса RuntimeLoop
from planning.planning import record_potential_sequences

# После обработки событий
record_potential_sequences(self.self_state)
```

---

## Архитектурные ограничения

Planning соблюдает жёсткие архитектурные ограничения (см. `docs/concepts/planning.md`):

### Запрещено:
- Инициировать действия или Decision
- Иметь цели или мотивацию
- Оценивать или ранжировать последовательности
- Влиять на другие слои
- Строить сценарии или предсказания

### Разрешено:
- Хранить потенциальные последовательности как нейтральные структуры
- Фиксироваться в памяти без интерпретации

---

## Тестирование

Тесты находятся в `src/test/test_planning.py`.

```bash
# Запуск тестов Planning
pytest src/test/test_planning.py -v
```

---

## Связанные документы

- [Концепция Planning](../concepts/planning.md) — архитектурные ограничения и философия
- [Self-State](self-state.md) — структура состояния
- [Runtime Loop](runtime-loop.md) — главный цикл интеграции

---

*Документ создан: 2026-01-18*
*Последнее обновление: 2026-01-18*
