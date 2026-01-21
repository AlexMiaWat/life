# ADR 015: Runtime Loop Refactoring

## Статус
✅ Принято

## Дата
2026-01-20

## Контекст

Runtime loop в проекте Life выполнял слишком много ответственностей, что приводило к проблемам с поддержкой, тестированием и производительностью. Основной цикл `run_loop()` содержал:

### Проблемы до рефакторинга
- **Монолитный код**: весь runtime loop в одной функции ~900 строк
- **Смешанные ответственности**: snapshot, logging, policy, monitoring в одном месте
- **Трудно тестировать**: невозможно изолированно тестировать отдельные аспекты
- **Hot-path проблемы**: I/O операции (snapshot, logging) в основном цикле
- **Сложность поддержки**: изменения в одном аспекте затрагивали весь цикл

### Архитектурные требования
- **Separation of concerns**: разделение ответственностей между компонентами
- **Testability**: возможность изолированного тестирования каждого аспекта
- **Performance**: вынос I/O операций из hot-path
- **Maintainability**: упрощение поддержки и модификации
- **Configurability**: явные политики и настройки для каждого аспекта

## Решение

### Архитектура рефакторинга

#### 1. Выделение менеджеров из runtime loop

##### SnapshotManager
```python
class SnapshotManager:
    """
    Менеджер снапшотов состояния Life.

    Управляет периодичностью создания снапшотов на основе количества тиков,
    изолирует обработку ошибок и I/O операции от основного цикла.
    """

    def __init__(self, period_ticks: int, saver: Callable[[SelfState], None]):
        self.period_ticks = period_ticks
        self.saver = saver
        # Статус операций для мониторинга
        self.last_operation_success: Optional[bool] = None
        self.last_operation_error: Optional[str] = None

    def should_snapshot(self, ticks: int) -> bool:
        """Проверяет необходимость снапшота (тик 0 исключен намеренно)"""
        return ticks > 0 and ticks % self.period_ticks == 0

    def maybe_snapshot(self, self_state: SelfState) -> bool:
        """Делает снапшот с обработкой исключений"""
        if self.should_snapshot(self_state.ticks):
            try:
                self.saver(self_state)
                self.last_operation_success = True
                return True
            except Exception as e:
                logger.error(f"Ошибка при сохранении snapshot: {e}")
                self.last_operation_success = False
                self.last_operation_error = str(e)
                return False
        return False
```

##### LogManager + FlushPolicy
```python
class FlushPolicy:
    """
    Политика сброса буфера логов.

    Определяет условия flush:
    - По периодичности (раз в N тиков)
    - Перед/после снапшота
    - При исключениях
    - При завершении
    """

class LogManager:
    """
    Менеджер логирования и буферизации.

    Управляет политикой сброса буфера логов,
    убирая регулярный I/O из hot-path runtime loop.
    """

    def __init__(self, flush_policy: FlushPolicy, flush_fn: Callable[[], None]):
        self.flush_policy = flush_policy
        self.flush_fn = flush_fn
        self.last_flush_tick = -flush_policy.flush_period_ticks

    def maybe_flush(self, self_state, *, phase: Literal["tick", "before_snapshot", ...]):
        """Сбрасывает буфер логов по политике"""
        should_flush = False

        if phase == "tick":
            should_flush = (
                self_state.ticks - self.last_flush_tick >= self.flush_policy.flush_period_ticks
            )
        elif phase == "before_snapshot":
            should_flush = self.flush_policy.flush_before_snapshot
        elif phase == "after_snapshot":
            should_flush = self.flush_policy.flush_after_snapshot
        elif phase == "exception":
            should_flush = self.flush_policy.flush_on_exception
        elif phase == "shutdown":
            should_flush = self.flush_policy.flush_on_shutdown

        if should_flush:
            self.flush_fn()
            self.last_flush_tick = self_state.ticks
```

##### LifePolicy
```python
class LifePolicy:
    """
    Политика "слабости" и штрафов для Life.

    Определяет пороги слабости и коэффициенты штрафов,
    применяемых когда система находится в состоянии слабости.
    """

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
        """Проверяет состояние слабости"""
        return (
            self_state.energy <= self.weakness_threshold
            or self_state.integrity <= self.weakness_threshold
            or self_state.stability <= self.weakness_threshold
        )

    def weakness_penalty(self, dt: float) -> dict[str, float]:
        """Вычисляет штрафы за слабость"""
        penalty = self.penalty_k * dt
        return {
            "energy": -penalty,
            "stability": -penalty * self.stability_multiplier,
            "integrity": -penalty * self.integrity_multiplier,
        }
```

#### 2. Упрощение runtime loop

```python
def run_loop(self_state, monitor, tick_interval=1.0, snapshot_period=10, ...):
    """
    Runtime Loop с интеграцией Environment (этап 07)
    """

    # Инициализация менеджеров
    snapshot_manager = SnapshotManager(
        period_ticks=snapshot_period, saver=save_snapshot
    )

    flush_policy = FlushPolicy(
        flush_period_ticks=log_flush_period_ticks,
        flush_before_snapshot=True,
        flush_after_snapshot=False,
        flush_on_exception=True,
        flush_on_shutdown=True,
    )

    log_manager = LogManager(
        flush_policy=flush_policy,
        flush_fn=self_state._flush_log_buffer,
    )

    life_policy = LifePolicy()  # Значения по умолчанию

    # Основной цикл (значительно упрощен)
    while not stop_event.is_set():
        # Обновление состояния
        self_state.apply_delta({"ticks": 1})
        self_state.apply_delta({"age": dt})

        # Обработка событий и компонентов
        # (Meaning, Decision, Action, Learning, Adaptation, etc.)

        # Применение штрафов за слабость через LifePolicy
        if life_policy.is_weak(self_state):
            penalty_deltas = life_policy.weakness_penalty(dt)
            self_state.apply_delta(penalty_deltas)

        # Flush логов перед снапшотом
        log_manager.maybe_flush(self_state, phase="before_snapshot")

        # Snapshot через SnapshotManager
        snapshot_was_made = snapshot_manager.maybe_snapshot(self_state)

        # Flush логов после снапшота
        if snapshot_was_made:
            log_manager.maybe_flush(self_state, phase="after_snapshot")

        # Flush логов по периодичности
        log_manager.maybe_flush(self_state, phase="tick")
```

### Преимущества архитектуры

#### 1. Separation of Concerns
- **SnapshotManager**: только снапшоты
- **LogManager**: только буферизация логов
- **LifePolicy**: только политика слабости
- **Runtime Loop**: только оркестрация компонентов

#### 2. Изоляция I/O операций
- **Hot-path чистый**: только бизнес-логика в основном цикле
- **Условный I/O**: snapshot и logging только по необходимости
- **Обработка ошибок**: исключения не роняют основной цикл

#### 3. Конфигурируемость
- **Явные политики**: FlushPolicy определяет когда сбрасывать логи
- **Настраиваемые параметры**: периоды, пороги, коэффициенты
- **Test-friendly**: каждый менеджер можно тестировать изолированно

#### 4. Мониторинг и отладка
- **Статус операций**: SnapshotManager отслеживает успех/неудачу
- **Метрики**: возможность добавления метрик для каждого менеджера
- **Логирование**: детальное логирование операций с timestamps

## Обоснование

### За выбранное решение

#### ✅ Архитектурная чистота
- **Single Responsibility**: каждый менеджер отвечает за одну задачу
- **Dependency Injection**: менеджеры передаются в runtime loop
- **Interface contracts**: четкие интерфейсы между компонентами

#### ✅ Производительность
- **Hot-path optimization**: I/O вынесен из основного цикла
- **Conditional execution**: операции только когда нужно
- **Buffering**: накопление логов перед сбросом

#### ✅ Тестируемость
- **Unit testing**: каждый менеджер тестируется изолированно
- **Mock injection**: возможность подмены менеджеров в тестах
- **Deterministic behavior**: предсказуемое поведение с явными политиками

#### ✅ Поддерживаемость
- **Modular changes**: изменения в одном менеджере не затрагивают другие
- **Configuration**: политики вынесены в конфигурируемые объекты
- **Error isolation**: ошибки в одном менеджере не влияют на другие

### Против альтернатив

#### Альтернатива 1: Полный рефакторинг в event-driven архитектуру
- **Против**: Требует значительных изменений в архитектуре
- **Против**: Увеличивает сложность системы
- **Против**: Не соответствует текущим требованиям

#### Альтернатива 2: Microservices подход
- **Против**: Overkill для monolithic системы
- **Против**: Увеличивает latency межпроцессного взаимодействия
- **Против**: Усложняет развертывание и мониторинг

#### Альтернатива 3: Оставить монолитный loop
- **Против**: Продолжение проблем с поддержкой
- **Против**: Невозможность изолированного тестирования
- **Против**: I/O в hot-path снижает производительность

## Последствия

### Положительные

#### ✅ Улучшенная архитектура
- **Четкое разделение**: каждый компонент имеет четкую ответственность
- **Снижение связности**: изменения в одном менеджере не затрагивают другие
- **Повышение cohesion**: каждый класс сфокусирован на одной задаче

#### ✅ Лучшая тестируемость
- **Изолированное тестирование**: каждый менеджер можно тестировать отдельно
- **Mock-friendly**: легкая подмена зависимостей в тестах
- **Coverage improvement**: возможность 100% покрытия для каждого компонента

#### ✅ Производительность и надежность
- **I/O isolation**: hot-path содержит только бизнес-логику
- **Error resilience**: исключения в менеджерах не роняют систему
- **Configurable policies**: возможность оптимизации под разные сценарии

#### ✅ Улучшенная поддержка
- **Easier debugging**: проблемы локализованы в конкретных менеджерах
- **Feature isolation**: новые возможности добавляются в соответствующие менеджеры
- **Code navigation**: проще найти нужный код

### Отрицательные

#### ⚠️ Увеличение количества компонентов
- **Больше файлов**: 4 новых модуля вместо одного большого
- **Сложность понимания**: нужно изучить несколько компонентов
- **Интеграционное тестирование**: требуется тестирование взаимодействия

#### ⚠️ Overhead на инициализацию
- **Создание объектов**: дополнительные объекты в памяти
- **Инициализация**: overhead при старте системы
- **Configuration**: больше параметров для настройки

#### ⚠️ Изменения в runtime loop
- **Refactoring complexity**: значительные изменения в основном цикле
- **Regression risk**: возможность внесения ошибок при рефакторинге
- **Migration effort**: необходимость обновления всех зависимостей

### Риски

#### Риск регрессии
- **Описание**: Рефакторинг может внести ошибки в runtime loop
- **Митигация**: comprehensive testing, gradual rollout, monitoring
- **Вероятность**: Средняя (тщательное тестирование)

#### Риск производительности
- **Описание**: Дополнительные вызовы методов могут замедлить цикл
- **Митигация**: profiling, optimization, caching где возможно
- **Вероятность**: Низкая (менеджеры минимальны)

#### Риск сложности
- **Описание**: Увеличение количества компонентов усложняет понимание
- **Митигация**: documentation, training, code organization
- **Вероятность**: Низкая (четкое разделение ответственности)

## Связанные документы

- [docs/architecture/overview.md](../architecture/overview.md) — обзор архитектуры
- [src/runtime/loop.py](../../src/runtime/loop.py) — рефакторинг runtime loop
- [src/runtime/snapshot_manager.py](../../src/runtime/snapshot_manager.py) — SnapshotManager
- [src/runtime/log_manager.py](../../src/runtime/log_manager.py) — LogManager и FlushPolicy
- [src/runtime/life_policy.py](../../src/runtime/life_policy.py) — LifePolicy
- [src/test/test_runtime_managers.py](../../src/test/test_runtime_managers.py) — тесты менеджеров