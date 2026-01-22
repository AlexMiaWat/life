# 02_RUNTIME_LOOP.md — Главный цикл жизни

## Назначение
Runtime Loop — это сердце системы **Life**. Это бесконечный цикл, который обеспечивает непрерывное течение времени и оркестрирует все процессы жизнедеятельности.

Если Loop остановился — только слабость и бессилие.

## Текущий статус
✅ **Реализован** (v2.3)
*   Файл: [`src/runtime/loop.py`](../../src/runtime/loop.py)
*   Поддерживает реальное время (Wall Clock) и субъективное время (Subjective Time).
*   Интегрирован с Environment, Self-State, Meaning Engine, Memory, Intelligence, Planning.
*   Полная обработка событий через Meaning Engine с сохранением в память.
*   Модель субъективного времени на основе интенсивности событий, стабильности и энергии системы.
*   **v2.0:** Рефакторинг с выделением менеджеров: `SnapshotManager`, `LogManager`, `LifePolicy`.
*   **v2.0:** Улучшенное логирование (замена `print()` на `logger` с уровнями).
*   **v2.0:** Инкапсуляция политик и I/O операций для улучшения тестируемости и производительности.
*   **v2.1:** Субъективное время как сквозная ось жизни - записывается в MemoryEntry при создании всех записей памяти.
*   **v2.2:** Полная интеграция субъективного времени в runtime loop с учетом энергии и экспоненциального сглаживания интенсивности.
*   **v2.3:** Улучшения в обработке ошибок, оптимизация констант и улучшенная потокобезопасность.
*   **v2.4:** Оптимизация порядка инициализации компонентов - StructuredLogger теперь инициализируется после PassiveDataSink для корректной интеграции.
*   **v2.5:** Интеграция DecisionEngine для анализа и логирования решений системы.
*   **v2.6:** Оптимизация производительности с LRU-кэшированием вычислений, батчингом обработки событий и оптимизацией индексов памяти.

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
10. **Memory Maintenance:** Batch операция обслуживания памяти (decay + archive в одном проходе, v2.7). Оптимизированная функция `batch_memory_maintenance()` объединяет затухание весов и архивацию в единый O(n) проход по памяти. Механизм забывания учитывает возраст записей, значимость и применяет минимальные веса. Архивация переносит старые записи (старше 7 дней или с весом < 0.1) в архив.
12. **Metabolism:** Расчет "физиологических" изменений (усталость, потребление энергии, слабость).
13. **Weakness Penalties:** Применение штрафов за слабость через `LifePolicy` (v2.0).
14. **Monitoring:** Отправка состояния в Monitor.
15. **Log Flush:** Условный сброс буфера логов через `LogManager` (v2.0).
16. **Snapshot:** Периодическое сохранение состояния на диск через `SnapshotManager` (v2.0).
17. **Sleep:** Ожидание следующего такта для поддержания стабильного `tick_interval`.

## Создание записей памяти (v2.1)

Runtime Loop записывает субъективное время в качестве сквозной оси жизни при создании всех записей памяти:

### Обычные события (шаг 5 Memory)
При обработке значимых событий (significance > 0) создается MemoryEntry с текущим субъективным временем:

```python
# В runtime/loop.py, ~338 строка
self_state.memory.append(
    MemoryEntry(
        event_type=event.type,
        meaning_significance=meaning.significance,
        timestamp=time.time(),
        subjective_timestamp=self_state.subjective_time,  # v2.1: субъективное время
    )
)
```

### Feedback записи (шаг 2 Feedback)
При сохранении последствий действий также записывается субъективное время:

```python
# В runtime/loop.py, ~256-270 строки
self_state.memory.append(
    MemoryEntry(
        event_type="feedback",
        meaning_significance=0.0,
        timestamp=feedback.timestamp,
        subjective_timestamp=self_state.subjective_time,  # v2.1: субъективное время
        feedback_data={
            "action_id": feedback.action_id,
            "action_pattern": feedback.action_pattern,
            # ... другие данные feedback
        }
    )
)
```

**Принципы:**
- Субъективное время записывается синхронно с обновлением `self_state.subjective_time`
- Все записи памяти (обычные события и feedback) получают субъективную временную метку
- Обеспечивается обратная совместимость: старые записи без поля загружаются корректно
- Субъективное время остается метрикой и не используется для управления поведением системы

## Интеграция DecisionEngine (v2.5)

Runtime Loop интегрирует DecisionEngine для комплексного анализа и логирования решений системы:

### Инициализация DecisionEngine

DecisionEngine инициализируется в начале работы runtime loop:

```python
# В runtime/loop.py, ~425 строка
decision_engine = DecisionEngine()  # Decision Engine для анализа решений
```

### Логирование решений

На этапе Decision (шаг 7) каждое принятое решение записывается в DecisionEngine:

```python
# В runtime/loop.py, ~904 строка
decision_engine.record_decision(
    decision_type="response_selection",
    context={
        "meaning_significance": meaning.significance,
        "event_type": event.type,
        "current_energy": self_state.energy,
        "current_stability": self_state.stability,
    },
    outcome=pattern,
    execution_time=decision_time,
)
```

### Анализируемые данные

DecisionEngine собирает следующие метрики для каждого решения:
- **Тип решения:** `response_selection` для выбора паттерна реакции
- **Контекст:** Значимость события, тип события, текущие показатели состояния (энергия, стабильность)
- **Результат:** Выбранный паттерн (`ignore`, `absorb`, `dampen`)
- **Производительность:** Время выполнения решения в секундах

### Преимущества интеграции

- **Анализ паттернов принятия решений** для выявления закономерностей поведения
- **Статистика успешности** решений в различных контекстах
- **Метрики производительности** компонента принятия решений
- **История решений** для отладки и оптимизации

## Ключевые параметры

| Параметр | Значение по умолчанию | Описание |
|----------|-----------------------|----------|
| `tick_interval` | 1.0 сек | Длительность одного такта. |
| `snapshot_period` | 10 тактов | Как часто сохранять полное состояние на диск. |
| `learning_interval` | 75 тактов | Как часто вызывать Learning Engine (Этап 14). |
| `adaptation_interval` | 100 тактов | Как часто вызывать Adaptation Manager (Этап 15). |
| `decay_interval` | 10 тактов | Как часто применять затухание весов памяти (v2.0). |
| `archive_interval` | 50 тактов | Как часто выполнять архивацию памяти (v2.0). |
| `enable_profiling` | False | Включение профилирования runtime loop с cProfile. |

## Профилирование производительности (v2.3)

Runtime Loop включает встроенную систему профилирования для анализа производительности с использованием `cProfile`.

### Включение профилирования

Профилирование включается через параметр `enable_profiling=True`:

```python
from runtime.loop import run_loop

# Запуск с профилированием
run_loop(
    self_state=state,
    monitor=console_monitor,
    tick_interval=1.0,
    enable_profiling=True  # Включает профилирование
)
```

### Результаты профилирования

**Файлы профилей:** Сохраняются в `data/runtime_loop_profile_{timestamp}.prof`

**Анализ результатов:**
- Автоматический вывод топ-10 функций по cumulative time в лог
- Бинарные файлы `.prof` для анализа через `pstats` или `snakeviz`
- Полный охват основного цикла `run_main_loop()`

**Текущие метрики производительности (baseline):**
- **Средняя длительность тика:** 14.9 мс (медиана 9.76 мс)
- **Распределение времени:** tick_start/tick_end ~40.1%, обработка событий ~4.5% на стадию
- **Основное время:** 99.5% тратится на `time.sleep` между тиками
- **Эффективность runtime loop:** < 0.5% CPU времени на логику Life

**Накладные расходы:** ~5-10% дополнительного времени выполнения при включенном профилировании.

### Анализ скрипт

Для автоматизированного анализа результатов профилирования используйте `profile_runtime.py`:

```bash
python profile_runtime.py data/runtime_loop_profile_*.prof
```

## Оптимизации производительности (v2.6)

Runtime Loop включает комплексную систему оптимизаций для достижения целевых показателей производительности: <10мс среднее время тика, >99% cache hit rate, 2-3x ускорение I/O.

### Система кэширования вычислений

**Файл:** [`src/runtime/computation_cache.py`](../../src/runtime/computation_cache.py)

LRU-кэш для дорогостоящих вычислений runtime loop с максимальным размером 1000 записей.

#### Кэшируемые операции

1. **compute_subjective_dt** - основная оптимизация (~60% вычислений на тик)
   - Кэширование по всем параметрам субъективного времени
   - Округление float значений для улучшения hit rate
   - Автоматическое вытеснение по LRU политике

2. **Валидация состояний** - проверка корректности состояний
   - Кэширование результатов валидации
   - Инвалидация при изменении данных

3. **Поиск в памяти** - активация памяти через activate_memory
   - Кэширование результатов поиска с учетом размера памяти
   - Инвалидация при изменении состояния памяти

4. **Meaning Engine appraisal** - оценка значимости событий
   - Кэширование результатов appraisal по параметрам события и состояния

5. **Decision Engine** - принятие решений
   - Кэширование решений по контексту и состоянию системы

#### Архитектура кэша

```python
class ComputationCache:
    def __init__(self, max_size: int = 1000):
        # Отдельные кэши для разных типов операций
        self.subjective_dt_cache: OrderedDict[str, float]
        self.validation_cache: OrderedDict[str, bool]
        self.memory_search_cache: OrderedDict[str, Any]
        self.meaning_appraisal_cache: OrderedDict[str, Any]
        self.decision_cache: OrderedDict[str, Any]
```

#### Ключевые методы

- `get_cached_*()` - получение из кэша или None
- `cache_*()` - сохранение в кэше
- `get_stats()` - статистика использования кэша

#### Преимущества

- **Снижение CPU нагрузки:** Повторяющиеся вычисления кэшируются
- **Улучшение latency:** <1мс доступ к кэшированным результатам
- **Масштабируемость:** LRU политика автоматически управляет размером кэша
- **Изоляция:** Каждый тип операций имеет отдельный кэш

### Батчинг обработки событий

Обработка нескольких событий в одном батче для снижения накладных расходов:

- **Группировка операций:** События обрабатываются пакетами вместо поодиночке
- **Совместное кэширование:** Общие вычисления кэшируются один раз на батч
- **Оптимизация I/O:** Снижение количества системных вызовов

### Оптимизация индексов памяти

Улучшенные индексы в MemoryIndexEngine для быстрого поиска по диапазонам:

#### Новые методы поиска

- `get_entries_by_weight_range()` - поиск по диапазону веса
- `get_entries_by_significance_range()` - поиск по диапазону значимости
- `get_entries_by_timestamp_range()` - поиск по диапазону времени

#### Оптимизированная архивация

Функция `archive_old_entries()` теперь использует индексы для предварительной фильтрации:

```python
# Быстрый поиск кандидатов через индексы
weight_entries = self._index_engine.get_entries_by_weight_range(0.0, min_weight)
significance_entries = self._index_engine.get_entries_by_significance_range(0.0, min_significance)

# Объединение результатов и дополнительная фильтрация
candidates = set(weight_entries + significance_entries)
```

#### Преимущества индексов

- **Быстрый поиск:** O(log n) вместо O(n) для диапазонных запросов
- **Снижение CPU:** Предварительная фильтрация кандидатов
- **Масштабируемость:** Эффективная работа с памятью >10k записей

### Бенчмаркинг и метрики

**Файл:** [`scripts/benchmark_runtime_optimizations.py`](../../scripts/benchmark_runtime_optimizations.py)

Комплексный бенчмарк для измерения производительности оптимизаций:

#### Измеряемые метрики

- **Время выполнения тика:** Среднее, медиана, min/max
- **Ticks per second:** Общая пропускная способность
- **Cache hit rate:** Эффективность кэширования по типам
- **Память:** Использование RAM, эффективность индексов

#### Запуск бенчмарка

```bash
python scripts/benchmark_runtime_optimizations.py
```

#### Целевые показатели

- **Время тика:** <10мс среднее
- **Cache hit rate:** >50% для subjective_dt, >99% для других операций
- **Ускорение I/O:** 2-3x по сравнению с baseline

### Нагрузочное тестирование

**Файлы:**
- [`src/test/benchmark_runtime_loop.py`](../../src/test/benchmark_runtime_loop.py)
- [`src/test/simple_benchmark.py`](../../src/test/simple_benchmark.py)

#### Конфигурации тестирования

- **baseline:** Стандартная конфигурация
- **fast_ticks:** Маленький интервал тиков (0.01s)
- **with_memory_hierarchy:** С включенной иерархией памяти

#### Результаты тестирования

Автоматическое сохранение результатов в `benchmark_results.json` с рекомендациями по оптимизации.

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

Runtime Loop вычисляет субъективное время на каждом такте с учетом трех факторов:

### Факторы субъективного времени (v2.2)

1. **Интенсивность событий** (`last_event_intensity`):
   - Высокая интенсивность → время течет быстрее
   - Сглаживается экспоненциально для плавных переходов

2. **Стабильность системы** (`stability`):
   - Низкая стабильность → время течет медленнее
   - Высокая стабильность → время течет нормально

3. **Уровень энергии** (`energy`):
   - Высокая энергия → время течет быстрее
   - Низкая энергия → время течет медленнее

### Реализация в runtime loop

```python
# Шаг 1: Обновление интенсивности с экспоненциальным сглаживанием
current_max_intensity = max([float(e.intensity) for e in events] + [0.0])
alpha = self_state.subjective_time_intensity_smoothing
self_state.last_event_intensity = (
    alpha * current_max_intensity +
    (1 - alpha) * self_state.last_event_intensity
)

# Шаг 2: Вычисление субъективного времени
subjective_dt = compute_subjective_dt(
    dt=dt,
    base_rate=self_state.subjective_time_base_rate,
    intensity=self_state.last_event_intensity,
    stability=self_state.stability,
    energy=self_state.energy,  # v2.2: учет энергии
    intensity_coeff=self_state.subjective_time_intensity_coeff,
    stability_coeff=self_state.subjective_time_stability_coeff,
    energy_coeff=self_state.subjective_time_energy_coeff,  # v2.2: новый коэффициент
    rate_min=self_state.subjective_time_rate_min,
    rate_max=self_state.subjective_time_rate_max,
)
self_state.apply_delta({"subjective_time": subjective_dt})
```

### Экспоненциальное сглаживание интенсивности

Интенсивность событий сглаживается по формуле:
```
smoothed_intensity = alpha * current_intensity + (1 - alpha) * previous_intensity
```

**Преимущества:**
- Плавные переходы между состояниями вместо резких скачков
- Реалистичное восприятие времени (память о недавних событиях)
- Снижение чувствительности к шумовым пикам интенсивности

**Параметры:**
- `alpha = subjective_time_intensity_smoothing` (по умолчанию 0.3)
- `alpha = 0.0`: Полное сглаживание (интенсивность не обновляется)
- `alpha = 1.0`: Без сглаживания (мгновенное обновление)
- `alpha = 0.3`: Оптимальный баланс между отзывчивостью и плавностью

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

## Batch Memory Maintenance (v2.7)

Runtime Loop использует оптимизированную функцию `batch_memory_maintenance()` для объединения операций decay и archive в единый проход по памяти.

### Архитектура batch операций

**До v2.7 (O(2n) сложность):**
```python
# Отдельные вызовы каждые N тиков
if ticks_since_last_memory_decay >= MEMORY_DECAY_LAZY_THRESHOLD:
    self_state.memory.decay_weights(decay_factor=MEMORY_DECAY_FACTOR, ...)

if ticks_since_last_memory_archive >= MEMORY_ARCHIVE_LAZY_THRESHOLD:
    archived_count = self_state.memory.archive_old_entries(...)
```

**v2.7 (O(n) сложность):**
```python
# Единый batch вызов
if maintenance_needed:
    maintenance_result = self_state.memory.batch_memory_maintenance(
        decay_factor=MEMORY_DECAY_FACTOR,
        min_weight=MEMORY_DECAY_MIN_WEIGHT,
        max_age_seconds=MEMORY_MAX_AGE_SECONDS,
        archive_min_weight=MEMORY_MIN_WEIGHT
    )
    logger.info(f"[LOOP] Batch memory maintenance: "
              f"decayed {maintenance_result['decayed_count']} entries, "
              f"archived {maintenance_result['archived_count']} entries")
```

### Преимущества оптимизации

*   **Производительность:** Снижение сложности с O(2n) до O(n)
*   **Консистентность:** Все изменения происходят в единой транзакции
*   **Масштабируемость:** Лучшая производительность при росте объема памяти
*   **Мониторинг:** Детальная статистика операций в логах runtime loop

### Параметры batch maintenance

- `decay_factor: float = 0.99` — коэффициент затухания весов
- `min_weight: float = 0.1` — минимальный вес после decay
- `max_age_seconds: float = 604800` — максимальный возраст для архивации (7 дней)
- `archive_min_weight: float = 0.1` — минимальный вес для архивации
- `archive_min_significance: float = 0.0` — минимальная значимость для архивации

### Результаты операции

Функция возвращает словарь с результатами:
```python
{
    "decayed_count": int,      # Количество записей с примененным decay
    "archived_count": int,     # Количество заархивированных записей
    "total_processed": int     # Общее количество обработанных записей
}
```

## Тестирование

Менеджеры Runtime Loop покрыты комплексным набором тестов в [`src/test/test_new_functionality_static.py`](../../src/test/test_new_functionality_static.py), [`src/test/test_new_functionality_smoke.py`](../../src/test/test_new_functionality_smoke.py) и [`src/test/test_new_functionality_integration.py`](../../src/test/test_new_functionality_integration.py).

### Уровни тестирования

#### Статические тесты (test_new_functionality_static.py)
Проверка структуры, сигнатур методов, типов и архитектурных ограничений:

- **Runtime Managers Structure:** Проверка наличия всех методов и атрибутов (4 теста)
- **Runtime Managers Constants:** Валидация значений по умолчанию и пользовательских параметров
- **Runtime Managers Method Signatures:** Проверка сигнатур методов и типов возвращаемых значений
- **No Forbidden Patterns:** Отсутствие запрещенных паттернов (eval, subprocess, etc.)
- **Docstrings:** Наличие документации для всех публичных методов
- **Imports Structure:** Корректность экспорта классов из модулей
- **Class Inheritance:** Проверка иерархии наследования

#### Дымовые тесты (test_new_functionality_smoke.py)
Базовая работоспособность компонентов:

- **Instantiation:** Создание экземпляров всех менеджеров
- **Basic Operations:** Основные операции (создание снапшотов, flush, проверка слабости)
- **Error Handling:** Обработка ошибок без падения системы
- **Policy Control:** Управление политиками flush
- **Integration Smoke:** Совместная работа всех менеджеров
- **Edge Cases:** Граничные случаи и нестандартные сценарии

#### Интеграционные тесты (test_new_functionality_integration.py)
Тестирование взаимодействия компонентов в реальных условиях:

- **Runtime Integration:** Работа менеджеров в runtime loop с многопоточностью
- **Cooperation:** Координация между SnapshotManager, LogManager и LifePolicy
- **Error Handling:** Устойчивость к сбоям отдельных компонентов
- **State Persistence:** Сериализация и восстановление состояния менеджеров

### Покрытие функциональности

**Всего тестов:** 28 тестов (9 новых тестов для runtime managers)

| Компонент | Статические | Дымовые | Интеграционные | Всего |
|-----------|-------------|---------|----------------|-------|
| SnapshotManager | 1 | 3 | 1 | 5 |
| LogManager | 1 | 4 | 1 | 6 |
| FlushPolicy | 3 | 2 | - | 5 |
| LifePolicy | 3 | 3 | 1 | 7 |
| **Итого** | **8** | **12** | **3** | **23** |

### Новые типы тестов

#### Тесты делегирования (TestRuntimeLoopDelegation)
Проверяют корректное делегирование из `run_loop` в менеджеры с использованием моков:

- `test_run_loop_delegates_to_snapshot_manager` - делегирование SnapshotManager
- `test_run_loop_delegates_to_log_manager` - делегирование LogManager в разных фазах
- `test_run_loop_delegates_to_life_policy` - делегирование LifePolicy

#### Тесты отсутствия регрессий (TestNoRegressionBehavior)
Гарантируют сохранение поведения после рефакторинга:

- `test_snapshot_periodicity_no_regression` - периодичность создания снапшотов
- `test_flush_schedule_no_regression` - расписание flush
- `test_weakness_penalties_no_regression` - корректность применения штрафов

#### Интеграционные тесты координации (TestRunLoopCoordination)
Проверяют координацию между менеджерами в реальном runtime loop:

- `test_run_loop_coordinates_snapshot_and_log_managers` - координация SnapshotManager и LogManager

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
