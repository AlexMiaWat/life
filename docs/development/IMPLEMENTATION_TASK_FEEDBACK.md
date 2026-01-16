# Задача реализации: Feedback (Этап 13)

**Статус:** Готово к реализации
**Приоритет:** Высокий
**Дата создания:** 13.01.2026

## Описание задачи

Реализовать слой Feedback согласно архитектурной спецификации в [`docs/components/feedback.md`](../components/feedback.md).

## Архитектурная спецификация

**Основной документ:** [`docs/components/feedback.md`](../components/feedback.md)

**Связанные документы:**
- [`docs/concepts/feedback-concept.md`](../concepts/feedback-concept.md) — Концепция Feedback
- [`docs/archive/12.3_ACTION_FEEDBACK_INTERFACE.md`](../archive/12.3_ACTION_FEEDBACK_INTERFACE.md) — Границы между Action и Feedback

## Что нужно реализовать

### 1. Создать модуль `src/feedback/`

#### Файл: `src/feedback/feedback.py`

Реализовать:
- Класс `PendingAction` (dataclass)
- Класс `FeedbackRecord` (dataclass)
- Функцию `register_action(action_id, action_pattern, state_before, timestamp, pending_actions)`
- Функцию `observe_consequences(self_state, pending_actions, event_queue) -> List[FeedbackRecord]`

**Примеры кода:** См. раздел "Интерфейс реализации" в [`feedback.md`](../components/feedback.md)

#### Файл: `src/feedback/__init__.py`

Экспортировать:
- `register_action`
- `observe_consequences`
- `PendingAction`
- `FeedbackRecord`

### 2. Интегрировать в `src/runtime/loop.py`

#### Импорты (в начале файла):
```python
from feedback import register_action, observe_consequences, FeedbackRecord
```

#### Инициализация (в начале функции `run_loop`):
```python
pending_actions = []  # Список ожидающих Feedback действий
```

#### Регистрация действия (после `execute_action()`, строка ~65):
```python
# КРИТИЧНО: Сохранить state_before ДО execute_action()
state_before = {
    'energy': self_state.energy,
    'stability': self_state.stability,
    'integrity': self_state.integrity
}

# Выполнить действие
execute_action(pattern, self_state)

# Зарегистрировать для Feedback
action_id = f"action_{self_state.ticks}_{pattern}_{int(time.time()*1000)}"
register_action(action_id, pattern, state_before, time.time(), pending_actions)
```

#### Наблюдение последствий (в начале каждого тика, после обработки событий, строка ~73):
```python
# Наблюдаем последствия прошлых действий
feedback_records = observe_consequences(
    self_state,
    pending_actions,
    event_queue
)

# Сохраняем Feedback в Memory
for feedback in feedback_records:
    feedback_entry = MemoryEntry(
        event_type="feedback",
        meaning_significance=0.0,  # Feedback не имеет значимости
        timestamp=feedback.timestamp
    )
    self_state.memory.append(feedback_entry)
```

## Критические требования

### Архитектурные принципы (НЕ нарушать!)

1. **Action не знает о Feedback:**
   - ❌ НЕ добавлять импорты Feedback в `src/action/action.py`
   - ✅ Регистрация происходит только в `loop.py`

2. **Feedback только записывает факты:**
   - ❌ НЕ добавлять флаги `success` или `failure`
   - ❌ НЕ оценивать результаты действий
   - ❌ НЕ влиять на Decision
   - ✅ Только фиксировать изменения состояния

3. **Асинхронность:**
   - ✅ Задержка 3-10 тиков перед наблюдением
   - ✅ Удаление записей после 20 тиков без проверки

## Тестирование

После реализации проверить:

1. **Регистрация действия:**
   - После `execute_action()` создается `PendingAction`
   - `state_before` корректно сохраняет состояние ДО действия
   - `action_id` уникален

2. **Наблюдение последствий:**
   - После 3-10 тиков создается `FeedbackRecord`
   - `state_delta` корректно вычисляется (после - до)
   - Записи удаляются после обработки

3. **Хранение в Memory:**
   - `FeedbackRecord` сохраняется в Memory
   - Записи не перезаписываются (append-only)

4. **Граничные случаи:**
   - Если прошло >20 тиков без проверки, запись удаляется
   - Если изменения <0.001, запись не создается

5. **Архитектурная целостность:**
   - Action не знает о Feedback (нет импортов, нет вызовов)
   - Feedback не содержит оценок (success/failure)
   - Feedback не влияет на Decision

## Чек-лист реализации

- [ ] Создан модуль `src/feedback/feedback.py` с классами и функциями
- [ ] Создан файл `src/feedback/__init__.py` с экспортами
- [ ] Добавлены импорты в `src/runtime/loop.py`
- [ ] Инициализирован `pending_actions` в `run_loop()`
- [ ] Сохранение `state_before` ДО `execute_action()`
- [ ] Вызов `register_action()` после `execute_action()`
- [ ] Вызов `observe_consequences()` в начале каждого тика
- [ ] Сохранение Feedback записей в Memory
- [ ] Протестирована регистрация действий
- [ ] Протестировано наблюдение через 3-10 тиков
- [ ] Протестировано сохранение в Memory
- [ ] Проверена архитектурная целостность (Action не знает о Feedback)

## Вопросы?

Если возникают вопросы по архитектуре или спецификации:
1. Проверьте [`docs/components/feedback.md`](../components/feedback.md)
2. Проверьте [`docs/archive/12.3_ACTION_FEEDBACK_INTERFACE.md`](../archive/12.3_ACTION_FEEDBACK_INTERFACE.md)
3. При необходимости запросите переключение на Architect для уточнений

## После реализации

После успешной реализации:
1. Обновить статус в `docs/development/status.md` (изменить на "✅ Implemented")
3. Создать или обновить `docs/components/feedback.md` с разделом "Реализация" (если нужно)
