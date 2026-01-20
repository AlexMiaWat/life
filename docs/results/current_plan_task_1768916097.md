# План выполнения задачи: Разгрузить `src/runtime/loop.py` (менеджеры + политика + hot-path)

**Задача:** Разгрузить `src/runtime/loop.py`: выделить менеджеры и убрать "скрытые" расходы

**Дата создания:** 2026-01-20  
**ID задачи:** 1768916097  
**Источник:** [docs/planning/task_2_20260120_094041.md](../planning/task_2_20260120_094041.md)

## Анализ текущей ситуации

### Текущее состояние `src/runtime/loop.py`

Файл `src/runtime/loop.py` содержит монолитный runtime loop с множеством смешанных обязанностей:

1. **Оркестрация слоев** (основная функция)
2. **Управление снапшотами** (inline логика каждые `snapshot_period` тиков)
3. **Управление логированием** (`_flush_log_buffer()` вызывается в `finally` на каждом тике)
4. **Политика "слабости"** (зашитые пороги и коэффициенты штрафов)
5. **Обработка событий** (интерпретация, активация памяти, decision, action)
6. **Learning/Adaptation** (периодические вызовы)
7. **Архивация/decay памяти** (периодические операции)
8. **Мониторинг** (вызов monitor функции)
9. **Обработка исключений** (try/except блоки)
10. **Регистрация feedback-действий**

### Выявленные проблемы

#### 1. Смешение обязанностей
- В одном месте находятся все аспекты runtime: оркестрация, I/O, политика, обработка ошибок
- Сложно понять, какая часть кода отвечает за что
- Трудно тестировать отдельные компоненты

#### 2. Скрытые расходы в hot-path
- **Проблема:** `self_state._flush_log_buffer()` вызывается в `finally` на каждом тике (строка 581)
- **Влияние:** При активном логировании это влечет регулярный дисковый I/O и снижает стабильность интервала тика
- **Решение:** Вынести в `LogManager` с политикой flush (не на каждом тике)

#### 3. Много `print()` в hot-path
- **Проблема:** Множество `print()` вызовов в runtime loop (строки 265, 267, 278, 286, 331, 427, 550, 575)
- **Влияние:** Увеличивает задержки и создает шум в выводе
- **Решение:** Заменить на `logger` с уровнями (debug/info/warning/error), выключенными по умолчанию

#### 4. Политика "слабости" размазана и нет конфигурации
- **Проблема:** Пороги и коэффициенты зашиты в код (строки 36-40, 537-552)
  - `WEAKNESS_THRESHOLD = 0.05`
  - `WEAKNESS_PENALTY_COEFFICIENT = 0.02`
  - `WEAKNESS_STABILITY_INTEGRITY_MULTIPLIER = 2.0`
- **Влияние:** Непрозрачно, как изменять пороги/коэффициенты без редактирования runtime
- **Решение:** Вынести в `LifePolicy` с конфигурируемыми параметрами

#### 5. Трудно тестировать
- Из-за монолитности `run_loop` сложно unit-тестами доказать, что изменения не меняют поведение
- Нет изоляции компонентов для тестирования

## Цели задачи

1. **Вынести снапшоты в `SnapshotManager`**
   - Инкапсулировать периодичность (ticks-based)
   - Изолировать I/O операции
   - Обработка исключений внутри менеджера

2. **Вынести логирование/буферизацию в `LogManager`**
   - Политика flush: не на каждом тике, а по расписанию
   - Flush на "границах": перед/после снапшота, раз в N тиков, при exception, при завершении
   - Убрать `finally: self_state._flush_log_buffer()` из hot-path

3. **Вынести "weakness/penalties" в `LifePolicy`**
   - Единая политика с конфигурируемыми параметрами
   - Чистая логика (без I/O)
   - Тестируемость

4. **Убрать `print()` из hot-path**
   - Заменить на `logger` с уровнями
   - По умолчанию подробные сообщения выключены

5. **Добавить unit-тесты**
   - Делегирование (loop вызывает менеджеры)
   - Отсутствие регрессий (ключевые инварианты)

## Архитектура решения

### Структура компонентов

```
src/runtime/
├── loop.py                    # Координатор (упрощенный)
├── snapshot_manager.py        # Управление снапшотами
├── log_manager.py             # Управление логированием
└── life_policy.py             # Политика "слабости"
```

### Компонент 1: SnapshotManager

**Файл:** `src/runtime/snapshot_manager.py`

**Ответственность:**
- Управление периодичностью снапшотов (ticks-based)
- Вызов `save_snapshot(self_state)`
- Обработка исключений (логировать и продолжать, не ронять loop)

**API:**
```python
class SnapshotManager:
    def __init__(self, period_ticks: int, saver: Callable[[SelfState], None]):
        self.period_ticks = period_ticks
        self.saver = saver
    
    def should_snapshot(self, ticks: int) -> bool:
        """Проверяет, нужно ли делать снапшот на текущем тике."""
        return ticks > 0 and ticks % self.period_ticks == 0
    
    def maybe_snapshot(self, self_state: SelfState) -> bool:
        """
        Делает снапшот, если нужно.
        Returns: True если снапшот был сделан, False иначе.
        """
        if self.should_snapshot(self_state.ticks):
            try:
                self.saver(self_state)
                return True
            except Exception as e:
                logger.error(f"Ошибка при сохранении snapshot: {e}", exc_info=True)
                return False
        return False
```

### Компонент 2: LogManager

**Файл:** `src/runtime/log_manager.py`

**Ответственность:**
- Управление политикой flush буфера логов
- Не вызывать flush на каждом тике
- Flush по расписанию: раз в N тиков, перед/после снапшота, при exception, при shutdown

**API:**
```python
from typing import Literal

class FlushPolicy:
    """Политика сброса буфера логов."""
    def __init__(
        self,
        flush_period_ticks: int = 10,  # Flush раз в N тиков
        flush_before_snapshot: bool = True,  # Flush перед снапшотом
        flush_on_exception: bool = True,  # Flush при исключении
        flush_on_shutdown: bool = True,  # Flush при завершении
    ):
        self.flush_period_ticks = flush_period_ticks
        self.flush_before_snapshot = flush_before_snapshot
        self.flush_on_exception = flush_on_exception
        self.flush_on_shutdown = flush_on_shutdown

class LogManager:
    def __init__(
        self,
        flush_policy: FlushPolicy,
        flush_fn: Callable[[], None],
    ):
        self.flush_policy = flush_policy
        self.flush_fn = flush_fn
        self.last_flush_tick = 0
    
    def maybe_flush(
        self,
        self_state: SelfState,
        *,
        phase: Literal["tick", "before_snapshot", "exception", "shutdown"],
        snapshot_was_made: bool = False,
    ) -> None:
        """
        Сбрасывает буфер логов, если нужно по политике.
        
        Args:
            self_state: Состояние для проверки тиков
            phase: Фаза выполнения (tick/before_snapshot/exception/shutdown)
            snapshot_was_made: Был ли сделан снапшот (для flush после снапшота)
        """
        should_flush = False
        
        if phase == "shutdown" and self.flush_policy.flush_on_shutdown:
            should_flush = True
        elif phase == "exception" and self.flush_policy.flush_on_exception:
            should_flush = True
        elif phase == "before_snapshot" and self.flush_policy.flush_before_snapshot:
            should_flush = True
        elif phase == "tick":
            # Flush раз в N тиков
            ticks_since_flush = self_state.ticks - self.last_flush_tick
            if ticks_since_flush >= self.flush_policy.flush_period_ticks:
                should_flush = True
        
        if should_flush:
            try:
                self.flush_fn()
                self.last_flush_tick = self_state.ticks
            except Exception as e:
                logger.warning(f"Ошибка при flush логов: {e}", exc_info=True)
```

### Компонент 3: LifePolicy

**Файл:** `src/runtime/life_policy.py`

**Ответственность:**
- Единая политика "weakness/penalties"
- Конфигурируемые пороги и коэффициенты
- Чистая логика (без I/O, без side effects)

**API:**
```python
class LifePolicy:
    def __init__(
        self,
        weakness_threshold: float = 0.05,
        penalty_k: float = 0.02,
        stability_multiplier: float = 2.0,
        integrity_multiplier: float = 2.0,
    ):
        self.weakness_threshold = weakness_threshold
        self.penalty_k = penalty_k
        self.stability_multiplier = stability_multiplier
        self.integrity_multiplier = integrity_multiplier
    
    def is_weak(self, self_state: SelfState) -> bool:
        """
        Проверяет, находится ли система в состоянии слабости.
        
        Returns:
            True если хотя бы один из параметров (energy/integrity/stability) <= threshold
        """
        return (
            self_state.energy <= self.weakness_threshold
            or self_state.integrity <= self.weakness_threshold
            or self_state.stability <= self.weakness_threshold
        )
    
    def weakness_penalty(self, dt: float) -> dict[str, float]:
        """
        Вычисляет штрафы за слабость как функцию от dt.
        
        Args:
            dt: Прошедшее время с последнего тика (секунды)
        
        Returns:
            Словарь с дельтами для apply_delta: {"energy": -penalty, "stability": -penalty*mult, ...}
        """
        penalty = self.penalty_k * dt
        return {
            "energy": -penalty,
            "stability": -penalty * self.stability_multiplier,
            "integrity": -penalty * self.integrity_multiplier,
        }
```

## План реализации

### Этап 0: Зафиксировать наблюдаемое поведение (до рефакторинга)

**Цель:** Понять текущее поведение для предотвращения регрессий

**Задачи:**
1. Собрать список "точек ответственности" в `src/runtime/loop.py`:
   - Снапшоты (строки 560-565): каждые `snapshot_period` тиков
   - Flush логов (строка 581): на каждом тике в `finally`
   - Weakness penalties (строки 537-552): при низких параметрах
   - Вывод/логирование (`print()`): строки 265, 267, 278, 286, 331, 427, 550, 575
   - Обработка исключений: try/except блоки

2. Выделить минимальные сценарии для unit-тестов:
   - Снапшот делается каждые N тиков
   - Flush вызывается на каждом тике (текущее поведение)
   - Weakness penalties применяются при пороге
   - `print()` выводят сообщения

**Результат:** Документация текущего поведения (можно в комментариях или отдельном файле)

### Этап 1: Вынести снапшоты в `SnapshotManager`

**Цель:** Изолировать логику снапшотов от основного цикла

**Задачи:**

1. **Создать `src/runtime/snapshot_manager.py`**
   - Реализовать класс `SnapshotManager` с методами `should_snapshot()` и `maybe_snapshot()`
   - Обработка исключений внутри менеджера
   - Логирование ошибок

2. **Интегрировать в `run_loop()`**
   - Создать экземпляр `SnapshotManager` в начале функции
   - Заменить блок снапшота (строки 560-565) на вызов `snapshot_manager.maybe_snapshot(self_state)`
   - Убрать inline логику снапшотов

**Проверка:**
- Снапшоты делаются с той же периодичностью
- Ошибки снапшотов не роняют loop
- Логирование ошибок работает

### Этап 2: Вынести логирование/буферизацию в `LogManager`

**Цель:** Убрать flush из hot-path (finally на каждом тике)

**Задачи:**

1. **Создать `src/runtime/log_manager.py`**
   - Реализовать класс `FlushPolicy` с параметрами политики
   - Реализовать класс `LogManager` с методом `maybe_flush()`
   - Поддержка разных фаз: tick, before_snapshot, exception, shutdown

2. **Интегрировать в `run_loop()`**
   - Создать экземпляр `LogManager` в начале функции
   - Убрать `finally: self_state._flush_log_buffer()` (строка 581)
   - Добавить вызовы `log_manager.maybe_flush()`:
     - В конце тика (редко, по политике)
     - Перед снапшотом (если политика требует)
     - В except блоке (если политика требует)
     - В конце функции (shutdown, обязательно)

**Проверка:**
- Flush не вызывается на каждом тике
- Flush вызывается по расписанию (раз в N тиков)
- Flush вызывается при shutdown
- Flush вызывается при исключениях (если политика требует)

### Этап 3: Вынести "weakness/penalties" в `LifePolicy`

**Цель:** Сделать политику слабости явной и конфигурируемой

**Задачи:**

1. **Создать `src/runtime/life_policy.py`**
   - Реализовать класс `LifePolicy` с параметрами по умолчанию (совпадают с текущими константами)
   - Метод `is_weak()` для проверки слабости
   - Метод `weakness_penalty()` для расчета штрафов (чистая функция)

2. **Интегрировать в `run_loop()`**
   - Создать экземпляр `LifePolicy` в начале функции
   - Заменить блок weakness penalties (строки 537-552) на:
     ```python
     if policy.is_weak(self_state):
         self_state.apply_delta(policy.weakness_penalty(dt))
     ```
   - Убрать константы `WEAKNESS_THRESHOLD`, `WEAKNESS_PENALTY_COEFFICIENT`, `WEAKNESS_STABILITY_INTEGRITY_MULTIPLIER` из `loop.py`

**Проверка:**
- Штрафы применяются с теми же значениями
- Пороги работают так же
- Политика конфигурируема

### Этап 4: Убрать `print()` из hot-path runtime

**Цель:** Заменить `print()` на структурированное логирование

**Задачи:**

1. **Заменить `print()` на `logger` в `run_loop()`**
   - Строка 265: `logger.debug("[LOOP] Queue not empty, size=...")`
   - Строка 267: `logger.debug("[LOOP] POPPED {len(events)} events")`
   - Строка 278: `logger.debug("[LOOP] Interpreting event: type=..., intensity=...")`
   - Строка 286: `logger.debug("[LOOP] Activated {len(activated)} memories...")`
   - Строка 331: `logger.debug("[LOOP] After interpret: energy=..., stability=...")`
   - Строка 427: `logger.info("[LOOP] Заархивировано {archived_count} записей памяти")` (info, т.к. редкое событие)
   - Строка 550: `logger.debug("[LOOP] Слабость: штрафы penalty=..., energy=...")`
   - Строка 575: `logger.error("[LOOP] Ошибка в цикле: {e}")` (error, т.к. это исключение)

2. **Настроить уровни логирования**
   - По умолчанию `logger.debug` выключен (не спамит)
   - `logger.info` для важных редких событий
   - `logger.error` для ошибок

**Проверка:**
- Нет `print()` в `run_loop()` (кроме крайних случаев, если есть)
- Логирование работает через `logger`
- По умолчанию нет спама в консоль

### Этап 5: Добавить unit-тесты (делегирование + отсутствие регрессий)

**Цель:** Доказать корректность делегирования и отсутствие регрессий

**Файл:** `src/test/test_runtime_loop_managers.py`

**Задачи:**

1. **Тест 5.1: `SnapshotManager` вызывает `save_snapshot` строго по периоду**
   - Создать mock для `save_snapshot`
   - Проверить, что снапшот делается каждые N тиков
   - Проверить, что ошибки не роняют менеджер

2. **Тест 5.2: `LogManager` не вызывает flush каждый тик**
   - Создать mock для `flush_fn`
   - Проверить, что flush вызывается раз в N тиков (по политике)
   - Проверить, что flush вызывается при shutdown
   - Проверить, что flush вызывается при exception (если политика требует)

3. **Тест 5.3: `LifePolicy`**
   - Проверить `is_weak()` на границе порога (0.05, 0.0501, 0.0499)
   - Проверить корректные дельты penalties как функцию от dt
   - Проверить монотонность (при большем dt штраф не меньше по модулю)
   - Проверить множители для stability/integrity

4. **Тест 5.4: Интеграционный unit-уровень: `run_loop` делегирует менеджерам**
   - Использовать spy-объекты для менеджеров
   - Проверить, что `run_loop` вызывает менеджеры в нужных местах
   - Проверить отсутствие регрессий для ключевых инвариантов:
     - Снапшоты вызываются по периодам
     - Flush не дергается на каждом тике
     - Weakness penalties применяются при пороге

**Проверка:**
- Все тесты проходят
- Покрытие новых компонентов > 90%

### Этап 6: Чистка и сверка с документацией

**Цель:** Убедиться, что изменения не ломают существующие тесты и соответствуют документации

**Задачи:**

1. **Запустить существующие тесты**
   - `pytest src/test/ -v`
   - Убедиться, что все тесты проходят

2. **Обновить документацию (если нужно)**
   - Проверить `docs/components/runtime-loop.md`
   - Обновить, если обнаружено расхождение с реальным поведением
   - Упомянуть новые менеджеры и политику

3. **Проверить стиль кода**
   - Соответствие стилю проекта
   - Docstrings для новых классов/методов

**Проверка:**
- Все существующие тесты проходят
- Документация актуальна
- Код соответствует стилю проекта

## Критерии приемки

### Функциональные критерии

✅ **FC1:** В `src/runtime/loop.py` больше нет inline-логики снапшотов — используется `SnapshotManager`

✅ **FC2:** В `src/runtime/loop.py` больше нет "flush на каждом тике" — используется `LogManager` с политикой flush

✅ **FC3:** В `src/runtime/loop.py` логика "weakness/penalties" вынесена в `LifePolicy` (единые пороги/коэффициенты)

✅ **FC4:** `print()` удалены из hot-path `run_loop` и заменены на `logger`

✅ **FC5:** Добавлены unit-тесты на делегирование и отсутствие регрессий поведения

### Нефункциональные критерии

✅ **NFC1:** Hot-path не выполняет регулярный дисковый I/O на каждом тике (кроме случаев, явно заданных политикой)

✅ **NFC2:** Код `run_loop` читабелен как оркестратор слоев (соответствует ADR 002)

✅ **NFC3:** Все существующие тесты проходят; новые тесты покрывают вынесенные компоненты

## Риски и митигация

### Риск 1: Регрессия поведения из-за рефакторинга

**Вероятность:** Средняя  
**Влияние:** Высокое

**Митигация:**
- Unit-тесты на делегирование и расчеты (Этап 5)
- Минимальные изменения логики: перенос кода без изменения формул/порогов
- Сравнение ключевых побочных эффектов (когда делается snapshot, когда применяется penalty)

### Риск 2: Потеря логов из-за менее частого flush

**Вероятность:** Средняя  
**Влияние:** Среднее/Высокое (зависит от требований к трассируемости)

**Митигация:**
- Flush на shutdown обязателен
- Flush перед снапшотом (как точка консистентности)
- Настраиваемая политика flush (ticks-based)
- Документировать компромисс "батчинг vs риск потери данных при падении"

### Риск 3: Сложность конфигурации политики

**Вероятность:** Низкая  
**Влияние:** Среднее

**Митигация:**
- Значения по умолчанию совпадают с текущими константами в loop
- Явная структура параметров в `LifePolicy`
- Минимальный public API

### Риск 4: Логирование станет слишком шумным или слишком тихим

**Вероятность:** Средняя  
**Влияние:** Среднее

**Митигация:**
- `logger.debug` для спама, `logger.info` только для редких событий
- Единообразный префикс/контекст в сообщениях
- Тесты не зависят от логов

## Выводы

Рефакторинг `src/runtime/loop.py` обеспечит:

1. **Разделение ответственности:** Оркестрация ≠ политика ≠ I/O
2. **Производительность:** Убраны скрытые расходы из hot-path (flush на каждом тике)
3. **Читаемость:** Код `run_loop` становится координатором, а не монолитом
4. **Тестируемость:** Компоненты изолированы и легко тестируются
5. **Конфигурируемость:** Политики можно менять без редактирования runtime

Это соответствует принципам проекта:
- **Архитектура:** Сохраняем "слоеный пирог" и роль Loop как координатора, уменьшая его связанность и сложность
- **Принципы проекта:** Без оптимизации/целей; изменения — структурные, не поведенческие
- **Зависимости:** Новые менеджеры зависят только от минимального API (`SelfState`, `save_snapshot`, `logger`)
