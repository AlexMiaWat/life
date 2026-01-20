# План выполнения: Вынести сохранение snapshot в `SnapshotManager` (политика периодичности, ошибки, формат)

> **Задача:** Вынести сохранение snapshot в `SnapshotManager` (политика периодичности, ошибки, формат)
> **ID задачи:** task_1768916863
> **Дата создания:** 2026-01-20
> **Статус:** ✅ Выполнено

## 1. Контекст и анализ текущего состояния

### 1.1. Текущая реализация

После изучения кодовой базы установлено, что задача **уже выполнена**:

1. **`SnapshotManager` реализован** (`src/runtime/snapshot_manager.py`):
   - Класс инкапсулирует логику периодичности через `period_ticks`
   - Метод `should_snapshot(ticks: int)` проверяет необходимость снапшота
   - Метод `maybe_snapshot(self_state: SelfState)` выполняет сохранение с обработкой ошибок
   - Ошибки логируются и не роняют основной цикл

2. **Интеграция в `loop.py`**:
   - `SnapshotManager` создается в начале `run_loop()`
   - Используется вместо inline-логики снапшотов
   - Вызывается через `snapshot_manager.maybe_snapshot(self_state)`

3. **Формат сохранения**:
   - Остается в `save_snapshot()` в `src/state/self_state.py` (как и должно быть по документации)
   - `SnapshotManager` делегирует форматирование функции `saver`

4. **Тесты**:
   - Unit-тесты в `src/test/test_runtime_loop_managers.py`
   - Покрытие: периодичность, обработка ошибок, валидация параметров

### 1.2. Соответствие требованиям

✅ **Политика периодичности**: Реализована через `period_ticks` и `should_snapshot()`
✅ **Обработка ошибок**: Реализована в `maybe_snapshot()` с try/except и логированием
✅ **Формат**: Остается в `save_snapshot()` (не изменяется, как требуется)

## 2. Архитектура решения

### 2.1. Структура `SnapshotManager`

```python
class SnapshotManager:
    def __init__(self, period_ticks: int, saver: Callable[[SelfState], None])
    def should_snapshot(self, ticks: int) -> bool
    def maybe_snapshot(self, self_state: SelfState) -> bool
```

**Ответственность:**
- Управление периодичностью (ticks-based)
- Изоляция I/O операций от основного цикла
- Обработка ошибок без падения цикла

**Разделение ответственности:**
- `SnapshotManager`: "когда" и "как обрабатывать ошибки"
- `save_snapshot()`: "как сохранять" (формат, сериализация, путь к файлу)

### 2.2. Интеграция в Runtime Loop

В `src/runtime/loop.py`:
```python
# Создание менеджера
snapshot_manager = SnapshotManager(period_ticks=snapshot_period, saver=save_snapshot)

# Использование в цикле
snapshot_was_made = snapshot_manager.maybe_snapshot(self_state)
```

## 3. План выполнения (ретроспектива)

### Этап 1: Создание SnapshotManager ✅
- [x] Реализован класс `SnapshotManager` с методами `should_snapshot()` и `maybe_snapshot()`
- [x] Добавлена валидация параметров (проверка на None для `saver`, положительное значение для `period_ticks`)
- [x] Реализована обработка ошибок с логированием

### Этап 2: Интеграция в Runtime Loop ✅
- [x] Создан экземпляр `SnapshotManager` в начале `run_loop()`
- [x] Заменена inline-логика снапшотов на вызов менеджера
- [x] Убраны inline проверки периодичности и обработки ошибок

### Этап 3: Тестирование ✅
- [x] Добавлены unit-тесты для периодичности
- [x] Добавлены тесты для обработки ошибок
- [x] Добавлены тесты для валидации параметров
- [x] Добавлены интеграционные тесты делегирования

### Этап 4: Документация ✅
- [x] Обновлена документация в `docs/components/runtime-loop.md`
- [x] Создан ADR 005: Runtime Loop Managers
- [x] Документированы API и использование менеджеров

## 4. Критерии приемки

✅ **FC1:** В `src/runtime/loop.py` больше нет inline-логики снапшотов — используется `SnapshotManager`
✅ **FC2:** Периодичность snapshot соответствует прежней (ticks-based, дефолт 10)
✅ **FC3:** Ошибки snapshot логируются и не останавливают loop
✅ **FC4:** Формат snapshot не изменен (всё по-прежнему через `save_snapshot(self_state)`)
✅ **FC5:** Добавлены unit-тесты на периодичность и обработку ошибок

## 5. Результаты выполнения

### 5.1. Реализованные компоненты

1. **`src/runtime/snapshot_manager.py`**:
   - Класс `SnapshotManager` с полной инкапсуляцией логики снапшотов
   - Валидация параметров при инициализации
   - Обработка ошибок с логированием

2. **Интеграция в `src/runtime/loop.py`**:
   - Использование `SnapshotManager` вместо inline-логики
   - Чистый код без смешения ответственности

3. **Тесты в `src/test/test_runtime_loop_managers.py`**:
   - `test_should_snapshot_period` — проверка периодичности
   - `test_maybe_snapshot_calls_saver` — проверка вызова saver
   - `test_maybe_snapshot_skips_when_not_needed` — проверка пропуска
   - `test_maybe_snapshot_handles_errors` — проверка обработки ошибок
   - `test_snapshot_manager_validation` — проверка валидации

### 5.2. Преимущества решения

- ✅ **Разделение ответственности**: SnapshotManager отвечает только за управление снапшотами
- ✅ **Тестируемость**: Легко тестировать отдельно от основного цикла
- ✅ **Изоляция ошибок**: Ошибки снапшотов не роняют основной цикл
- ✅ **Производительность**: I/O операции изолированы от hot-path
- ✅ **Читаемость**: Код `run_loop` стал чище и понятнее

## 6. Связанные документы

- `docs/planning/task_2_20260120_094041.md` — исходная документация задачи
- `docs/results/current_plan_task_1768899141.md` — предыдущий план выполнения
- `docs/adr/005-runtime-loop-managers.md` — архитектурное решение
- `docs/components/runtime-loop.md` — документация Runtime Loop
- `src/runtime/snapshot_manager.py` — реализация SnapshotManager
- `src/test/test_runtime_loop_managers.py` — тесты менеджеров

## 7. Выводы

Задача **полностью выполнена**. `SnapshotManager` успешно инкапсулирует:
- ✅ Политику периодичности (через `period_ticks` и `should_snapshot()`)
- ✅ Обработку ошибок (в `maybe_snapshot()` с try/except)
- ✅ Делегирование форматирования функции `save_snapshot()` (формат не изменен)

Все критерии приемки выполнены, код протестирован и задокументирован.

---

**Автор плана:** AI Agent (Project Executor)
**Дата:** 2026-01-20
