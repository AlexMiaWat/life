# 02_RUNTIME_LOOP.md — Главный цикл жизни

## Назначение
Runtime Loop — это сердце системы **Life**. Это бесконечный цикл, который обеспечивает непрерывное течение времени и оркестрирует все процессы жизнедеятельности.

Если Loop остановился — только слабость и бессилие.

## Текущий статус
✅ **Реализован** (v2.0)
*   Файл: [`src/runtime/loop.py`](../../src/runtime/loop.py)
*   Поддерживает реальное время (Wall Clock) и субъективное время (Subjective Time).
*   Интегрирован с Environment, Self-State, Meaning Engine, Memory, Intelligence, Planning.
*   Полная обработка событий через Meaning Engine с сохранением в память.
*   Модель субъективного времени на основе интенсивности событий и стабильности системы.
*   **v2.0:** Рефакторинг с выделением менеджеров: `SnapshotManager`, `LogManager`, `LifePolicy`.
*   **v2.0:** Улучшенное логирование (замена `print()` на `logger` с уровнями).
*   **v2.0:** Инкапсуляция политик и I/O операций для улучшения тестируемости и производительности.

## Алгоритм такта (Tick)

Каждый такт (Tick) выполняется последовательно:

1.  **Time Update:** Обновление возраста (`age`), счетчика тактов (`ticks`) и субъективного времени (`subjective_time`).
2.  **Feedback:** Наблюдение последствий прошлых действий и сохранение Feedback в Memory.
3.  **Perception:** Получение событий из очереди `EventQueue`.
4.  **Interpretation:** Интерпретация событий через Meaning Engine и обновление `Self-State`.
5.  **Memory:** Сохранение значимых событий в эпизодическую память.
6.  **Planning:** Фиксация потенциальных последовательностей событий.
7.  **Intelligence:** Минимальная обработка информации из нейтральных источников.
8.  **Learning:** Периодический вызов Learning Engine (раз в `learning_interval` тиков).
9.  **Adaptation:** Периодический вызов Adaptation Manager (раз в `adaptation_interval` тиков).
10. **Memory Decay:** Периодическое затухание весов памяти (раз в `decay_interval` тиков, v2.0). Механизм забывания - веса записей уменьшаются со временем, более значимые записи забываются медленнее.
11. **Archive:** Периодическая архивация памяти (раз в `archive_interval` тиков, v2.0). Старые записи (старше 7 дней или с весом < 0.1) автоматически переносятся в архив.
12. **Metabolism:** Расчет "физиологических" изменений (усталость, потребление энергии, слабость).
13. **Weakness Penalties:** Применение штрафов за слабость через `LifePolicy` (v2.0).
14. **Monitoring:** Отправка состояния в Monitor.
15. **Log Flush:** Условный сброс буфера логов через `LogManager` (v2.0).
16. **Snapshot:** Периодическое сохранение состояния на диск через `SnapshotManager` (v2.0).
17. **Sleep:** Ожидание следующего такта для поддержания стабильного `tick_interval`.

## Ключевые параметры

| Параметр | Значение по умолчанию | Описание |
|----------|-----------------------|----------|
| `tick_interval` | 1.0 сек | Длительность одного такта. |
| `snapshot_period` | 10 тактов | Как часто сохранять полное состояние на диск. |
| `learning_interval` | 75 тактов | Как часто вызывать Learning Engine (Этап 14). |
| `adaptation_interval` | 100 тактов | Как часто вызывать Adaptation Manager (Этап 15). |
| `decay_interval` | 10 тактов | Как часто применять затухание весов памяти (v2.0). |
| `archive_interval` | 50 тактов | Как часто выполнять архивацию памяти (v2.0). |

## Обработка сбоев

*   Любое исключение внутри цикла логируется, но не останавливает жизнь (если возможно).
*   Исключения наносят урон `integrity`.

### Критические исправления (task_1768908574)

#### Улучшение обработки ошибок

**Проблема:** Использование `pass` для обработки ошибок означало полное игнорирование ошибок без отслеживания их частоты.

**Решение:** Добавлены счетчики ошибок для отслеживания проблем:
- `learning_errors` - счетчик ошибок в Learning Engine
- `adaptation_errors` - счетчик ошибок в Adaptation Manager
- `max_errors_before_warning = 10` - порог для предупреждения о частых ошибках

При достижении порога выводится предупреждение о возможной деградации функциональности.

**Код:**
```python
learning_errors += 1
logger.error(f"Критическая ошибка в Learning (параметры): {e}", exc_info=True)
if learning_errors >= max_errors_before_warning:
    logger.warning(
        f"Обнаружено {learning_errors} ошибок в Learning. "
        "Возможна деградация функциональности."
    )
```

#### Устранение fallback с временными объектами

**Проблема:** В коде оставались места, где создавались временные объекты `SelfState()` для получения параметров по умолчанию.

**Решение:** Все fallback заменены на использование вспомогательных функций `_get_default_learning_params()` и `_get_default_adaptation_params()` без создания временных объектов.

**Изменения:**
- Убраны все `temp_state = SelfState()` из `runtime/loop.py`
- Используются только вспомогательные функции для получения параметров по умолчанию

#### Константы

Все константы Runtime Loop определены в модуле и имеют документацию:
- Интервалы вызова компонентов (`LEARNING_INTERVAL`, `ADAPTATION_INTERVAL`, и т.д.)
- Константы для работы с памятью (`MEMORY_DECAY_FACTOR`, `MEMORY_MIN_WEIGHT`, и т.д.)
- Константы для обработки ошибок (`ERROR_INTEGRITY_PENALTY`, `MAX_ERRORS_BEFORE_WARNING`)

**Примечание:** Константы для логики слабости были вынесены в `LifePolicy` (v2.0).

*   Если жизненные показатели (`energy`, `integrity`, `stability`) падают до 0, цикл прерывается через `self_state.set_active(False)`.
*   Для обновления vital параметров используется метод `apply_delta()`, который автоматически валидирует изменения через `__setattr__()` (см. [self-state.md](self-state.md)).

### Рефакторинг Runtime Loop (v2.0)

#### Выделение менеджеров

**Проблема:** Runtime Loop содержал слишком много ответственности: управление снапшотами, логирование, политика слабости. Это усложняло тестирование и производительность.

**Решение:** Выделены три специализированных менеджера:

1. **`SnapshotManager`** (`src/runtime/snapshot_manager.py`):
   - Управляет периодичностью создания снапшотов
   - Изолирует I/O операции от основного цикла
   - Обрабатывает ошибки снапшотов без падения цикла

2. **`LogManager`** (`src/runtime/log_manager.py`):
   - Управляет буферизацией и сбросом логов
   - Убирает регулярный I/O из hot-path runtime loop
   - Flush происходит по расписанию (периодически, перед снапшотом, при исключениях, при завершении)

3. **`LifePolicy`** (`src/runtime/life_policy.py`):
   - Инкапсулирует логику определения слабости и расчета штрафов
   - Делает политику явной, конфигурируемой и тестируемой
   - Значения по умолчанию совпадают с предыдущими константами

**Преимущества:**
- Улучшенная тестируемость (каждый менеджер тестируется отдельно)
- Лучшая производительность (I/O операции вынесены из hot-path)
- Явная политика (конфигурируемые параметры вместо констант)
- Изоляция ошибок (ошибки менеджеров не роняют основной цикл)

#### Улучшение логирования

**Проблема:** Использование `print()` в hot-path runtime loop создавало неконтролируемый вывод и влияло на производительность.

**Решение:** Все `print()` заменены на `logger.debug/info/error` с соответствующими уровнями:
- `logger.debug()` для детальной отладочной информации (выключается по умолчанию)
- `logger.info()` для информационных сообщений (например, архивация памяти)
- `logger.error()` для ошибок с полным traceback

**Преимущества:**
- Контролируемый вывод через стандартный logging
- Возможность настройки уровней логирования
- Улучшенная производительность (debug-логи можно отключить)

## Пример использования

```python
from runtime.loop import run_loop
from state.self_state import create_initial_state
from monitor.console import console_monitor

# Инициализация
state = create_initial_state()

# Запуск (блокирует поток)
run_loop(
    self_state=state,
    monitor=console_monitor,
    tick_interval=0.5
)
```

## Субъективное время

Runtime Loop вычисляет субъективное время на основе:
- Физического времени (`dt`)
- Интенсивности последнего события (`last_event_intensity`)
- Стабильности системы (`stability`)
- Параметров субъективного времени из `SelfState`

Субъективное время — это метрика, которая отражает восприятие времени системой:
- Высокая интенсивность → время течет быстрее
- Низкая стабильность → время течет медленнее

Подробнее см. [subjective-time.md](./subjective-time.md).

## Менеджеры Runtime Loop (v2.0)

### SnapshotManager

Управляет периодическим сохранением снапшотов состояния Life.

**Файл:** [`src/runtime/snapshot_manager.py`](../../src/runtime/snapshot_manager.py)

**Основные методы:**
- `should_snapshot(ticks: int) -> bool` — проверяет, нужно ли делать снапшот на текущем тике
- `maybe_snapshot(self_state: SelfState) -> bool` — делает снапшот, если нужно по периодичности

**Особенности:**
- Обрабатывает исключения внутри менеджера, не роняя основной цикл
- Возвращает `True` если снапшот был сделан, `False` иначе
- Валидирует параметры при инициализации (проверка на None для callback-функции, положительное значение для периода)

**Использование:**
```python
from src.runtime.snapshot_manager import SnapshotManager
from src.state.self_state import save_snapshot

# Создание менеджера с периодичностью 10 тиков
snapshot_manager = SnapshotManager(period_ticks=10, saver=save_snapshot)

# В runtime loop:
# Flush логов перед снапшотом (управляется через LogManager)
log_manager.maybe_flush(self_state, phase="before_snapshot")

# Создание снапшота через менеджер
snapshot_was_made = snapshot_manager.maybe_snapshot(self_state)

# Flush логов после снапшота (если был сделан)
if snapshot_was_made:
    log_manager.maybe_flush(self_state, phase="after_snapshot")
```

**Примеры:**

1. **Создание снапшота с периодичностью 5 тиков:**
```python
snapshot_manager = SnapshotManager(period_ticks=5, saver=save_snapshot)
# Снапшоты будут создаваться на тиках: 5, 10, 15, 20, ...
```

2. **Проверка, нужно ли делать снапшот:**
```python
if snapshot_manager.should_snapshot(self_state.ticks):
    # Подготовка к снапшоту
    pass
```

3. **Обработка ошибок:**
```python
# Ошибки автоматически обрабатываются внутри менеджера
snapshot_was_made = snapshot_manager.maybe_snapshot(self_state)
# Если произошла ошибка, snapshot_was_made будет False,
# но менеджер продолжит работать
```

### LogManager

Управляет буферизацией и сбросом логов, убирая регулярный I/O из hot-path runtime loop.

**Файл:** [`src/runtime/log_manager.py`](../../src/runtime/log_manager.py)

**Основные компоненты:**
- `FlushPolicy` — политика сброса буфера логов:
  - `flush_period_ticks` — flush раз в N тиков (по умолчанию 10)
  - `flush_before_snapshot` — flush перед снапшотом (по умолчанию True)
  - `flush_after_snapshot` — flush после снапшота (по умолчанию False)
  - `flush_on_exception` — flush при исключении (по умолчанию True)
  - `flush_on_shutdown` — flush при завершении (по умолчанию True, обязательно)

- `LogManager` — менеджер логирования:
  - `maybe_flush(self_state, phase, snapshot_was_made)` — сбрасывает буфер логов, если нужно по политике
    - `phase`: Фаза выполнения (`tick`/`before_snapshot`/`after_snapshot`/`exception`/`shutdown`)
    - `snapshot_was_made`: Был ли сделан снапшот (используется для flush после снапшота в фазе `tick`)

**Особенности:**
- Flush происходит по расписанию, а не на каждом тике
- Обрабатывает ошибки flush без падения менеджера
- Отслеживает последний тик flush для периодичности
- Поддерживает flush перед и после снапшота для обеспечения консистентности
- Валидирует параметры при инициализации (проверка на None для callback-функций, положительные значения для периодов)

**Разделение ответственности с SelfState:**

`LogManager` управляет **политическими flush** (когда делать flush по расписанию), в то время как `SelfState` выполняет **защитные flush** (критичные для предотвращения потери данных):

- **LogManager (политические flush):**
  - Периодический flush (раз в N тиков)
  - Flush перед/после снапшота
  - Flush при исключениях
  - Flush при завершении

- **SelfState (защитные flush):**
  - Автоматический flush при переполнении буфера (предотвращает потерю данных)
  - Flush при изменении размера буфера (предотвращает потерю данных)
  - Flush при включении/отключении логирования (консистентность состояния)

**Важно:** Защитные flush в `SelfState` **остаются и не заменяются** на использование `LogManager`. Они вызываются синхронно при изменении конфигурации или переполнении буфера и не зависят от политики `LogManager`. Это обеспечивает надежность системы и предотвращает потерю данных независимо от настроек политики flush. `LogManager` дополняет защитные flush, добавляя политические flush для оптимизации производительности (убирая регулярный I/O из hot-path runtime loop).

**Использование:**
```python
flush_policy = FlushPolicy(
    flush_period_ticks=10,
    flush_before_snapshot=True,
    flush_after_snapshot=False,
    flush_on_exception=True,
    flush_on_shutdown=True,
)
log_manager = LogManager(
    flush_policy=flush_policy,
    flush_fn=self_state._flush_log_buffer,
)
log_manager.maybe_flush(self_state, phase="before_snapshot")
snapshot_was_made = snapshot_manager.maybe_snapshot(self_state)
if snapshot_was_made:
    log_manager.maybe_flush(self_state, phase="after_snapshot")
log_manager.maybe_flush(self_state, phase="tick", snapshot_was_made=snapshot_was_made)
log_manager.maybe_flush(self_state, phase="exception")
log_manager.maybe_flush(self_state, phase="shutdown")
```

### LifePolicy

Политика "слабости" и штрафов для Life. Определяет пороги слабости и коэффициенты штрафов.

**Файл:** [`src/runtime/life_policy.py`](../../src/runtime/life_policy.py)

**Основные методы:**
- `is_weak(self_state: SelfState) -> bool` — проверяет, находится ли система в состоянии слабости
- `weakness_penalty(dt: float) -> dict[str, float]` — вычисляет штрафы за слабость как функцию от dt

**Параметры (значения по умолчанию):**
- `weakness_threshold` — порог для определения слабости (0.05)
- `penalty_k` — коэффициент штрафа за слабость (0.02)
- `stability_multiplier` — множитель штрафа для stability (2.0)
- `integrity_multiplier` — множитель штрафа для integrity (2.0)

**Особенности:**
- Чистая функция без side effects
- Возвращает дельты для `apply_delta()`
- Значения по умолчанию совпадают с предыдущими константами
- Валидирует параметры при инициализации (проверка на неотрицательные значения)

**Использование:**
```python
life_policy = LifePolicy()  # Использует значения по умолчанию
if life_policy.is_weak(self_state):
    penalty_deltas = life_policy.weakness_penalty(dt)
    self_state.apply_delta(penalty_deltas)
```

## Тестирование

Все менеджеры покрыты unit-тестами в [`src/test/test_runtime_loop_managers.py`](../../src/test/test_runtime_loop_managers.py).

**Покрытие:**
- **TestSnapshotManager:** Изолированное поведение SnapshotManager (4 теста)
- **TestLogManager:** Изолированное поведение LogManager и интеграция (11 тестов)
- **TestLifePolicy:** Изолированное поведение LifePolicy (6 тестов)
- **TestRuntimeLoopDelegation:** Делегирование из `run_loop` в менеджеры (3 теста) - **НОВЫЙ**
- **TestNoRegressionBehavior:** Отсутствие регрессий поведения (3 теста) - **НОВЫЙ**
- **TestRunLoopCoordination:** Интеграционные тесты координации (1 тест) - **НОВЫЙ**
- Корректность политик и расчетов
- Обработка ошибок

**Всего тестов:** 28 (добавлено 7 новых тестов)

### Новые типы тестов

#### Тесты делегирования (TestRunLoopDelegation)
Проверяют, что `run_loop` правильно делегирует вызовы менеджерам с использованием моков/spy:

- `test_run_loop_delegates_to_snapshot_manager` - проверка делегирования SnapshotManager
- `test_run_loop_delegates_to_log_manager` - проверка делегирования LogManager в разных фазах
- `test_run_loop_delegates_to_life_policy` - проверка делегирования LifePolicy

#### Тесты отсутствия регрессий (TestNoRegressionBehavior)
Проверяют сохранение поведения после рефакторинга:

- `test_snapshot_periodicity_no_regression` - периодичность создания снапшотов
- `test_flush_schedule_no_regression` - расписание flush (не на каждом тике)
- `test_weakness_penalties_no_regression` - корректность применения штрафов

#### Интеграционные тесты координации (TestRunLoopCoordination)
Проверяют координацию между менеджерами в реальном многопоточном `run_loop`:

- `test_run_loop_coordinates_snapshot_and_log_managers` - координация SnapshotManager и LogManager

## Связанные документы

*   [self-state.md](self-state.md) — состояние системы
*   [subjective-time.md](./subjective-time.md) — модель субъективного времени
*   [memory.md](memory.md) — память
*   [meaning-engine.md](meaning-engine.md) — интерпретация событий
*   [intelligence.md](intelligence.md) — обработка информации
*   [planning.md](planning.md) — планирование
*   [learning.md](learning.md) — обучение
*   [adaptation.md](adaptation.md) — адаптация
*   [ADR 005: Runtime Loop Managers](../adr/005-runtime-loop-managers.md) — архитектурное решение о выделении менеджеров
