---
name: Глубокое развитие Life — сделать жизнь живой
overview: "Углубление и расширение существующих слоев для придания системе \"живости\": добавление субъективного времени, lifecycle этапов, полной структуры Self-State, забывания памяти и восстановления из snapshots."
todos:
  - id: deepen-self-state
    content: "Расширить SelfState: добавить error_count, downtime, noise, drift, subjective_time, version. Реализовать субъективное время в runtime loop"
    status: pending
  - id: lifecycle-system
    content: Создать lifecycle модуль (lifecycle.py) с этапами INIT/RUN/DEGRADE и хуками on_birth/on_tick/on_degrade. Интегрировать в runtime loop
    status: pending
    dependencies:
      - deepen-self-state
  - id: snapshot-recovery
    content: Реализовать автоматическую загрузку последнего snapshot при старте в main_server_api.py. Обновить lifecycle для восстановленных состояний
    status: pending
    dependencies:
      - lifecycle-system
  - id: memory-decay
    content: "Реализовать забывание памяти: decay_memory() с уменьшением significance со временем и удалением записей с significance < 0.01. Интегрировать в runtime loop"
    status: pending
    dependencies:
      - deepen-self-state
  - id: internal-dynamics
    content: "Добавить обновление noise/drift в runtime loop: накопление noise от событий, затухание, дрейф к равновесию"
    status: pending
    dependencies:
      - deepen-self-state
  - id: update-docs
    content: "Обновить документацию: self-state.md (новые поля), создать lifecycle.md, обновить status.md"
    status: pending
    dependencies:
      - lifecycle-system
      - memory-decay
---

# План: Глубокое развитие Life — сделать жизнь живой

## Философия плана

Жизнь должна стать **живой** через:

- **Субъективность**: Субъективное время, которое течет по-разному
- **Непрерывность**: Восстановление из snapshots при старте
- **Глубину**: Полная структура Self-State с внутренней динамикой
- **Жизненные циклы**: Этапы жизни (рождение, существование, слабость)
- **Забывание**: Деградация памяти как признак живой системы

## Этап 1: Расширение Self-State — внутренняя глубина

### 1.1 Добавить недостающие поля в SelfState

**Файл:** [`src/state/self_state.py`](src/state/self_state.py)

Добавить в `SelfState`:

- `error_count: int = 0` — счетчик ошибок (инкрементируется при исключениях)
- `downtime: float = 0.0` — время простоя/деградации
- `noise: float = 0.0` — внутренний шум (накапливается от событий)
- `drift: float = 0.0` — дрейф состояния (медленный уход от равновесия)
- `subjective_time: float = 0.0` — субъективное время жизни
- `version: str = "1.0"` — версия состояния

### 1.2 Субъективное время

**Логика:** В `runtime/loop.py` после обновления `age` вычислять `subjective_time`:

```python
# Субъективное время течет быстрее при высокой энергии/стабильности
time_multiplier = (self_state.energy / 100.0) * (self_state.stability + 0.5)
self_state.subjective_time += dt * time_multiplier
```

### 1.3 Обновить apply_delta для новых полей

Добавить валидацию и ограничения для `noise`, `drift`, `error_count`.

## Этап 2: Lifecycle — этапы жизни

### 2.1 Создать модуль lifecycle

**Файл:** [`src/runtime/lifecycle.py`](src/runtime/lifecycle.py) (новый)

Реализовать:

- `LifePhase`: Enum (`INIT`, `RUN`, `DEGRADE`)
- `LifecycleManager`: управление этапами и переходами
- Хуки: `on_birth()`, `on_tick()`, `on_degrade()`

### 2.2 Интеграция в Runtime Loop

**Файл:** [`src/runtime/loop.py`](src/runtime/loop.py)

- В начале `run_loop()`: вызвать `on_birth()` если первый запуск
- Проверка перехода в `DEGRADE` при `energy/integrity/stability <= 0.05`
- При переходе в `DEGRADE`: вызвать `on_degrade()` (логирование, специальные эффекты)

## Этап 3: Восстановление из snapshots — непрерывность

### 3.1 Автоматическая загрузка при старте

**Файл:** [`src/main_server_api.py`](src/main_server_api.py)

В `main()` добавить:

```python
try:
    self_state = SelfState.load_latest_snapshot()
    print(f"[LIFE] Восстановлено из snapshot, ticks={self_state.ticks}")
except FileNotFoundError:
    self_state = create_initial_state()
    print(f"[LIFE] Новая жизнь, life_id={self_state.life_id}")
```

### 3.2 Обновить lifecycle для восстановленных состояний

При восстановлении из snapshot:

- Не вызывать `on_birth()` (жизнь уже существует)
- Вызвать `on_tick()` с флагом `is_resumed=True`

## Этап 4: Забывание памяти — деградация опыта

### 4.1 Добавить механизм забывания в Memory

**Файл:** [`src/memory/memory.py`](src/memory/memory.py)

Реализовать:

- `decay_memory(memory_entries, dt, state)` — уменьшение значимости со временем
- Формула: `significance *= exp(-decay_rate * dt / subjective_time_factor)`
- Удаление записей с `significance < 0.01`

### 4.2 Интеграция в Runtime Loop

**Файл:** [`src/runtime/loop.py`](src/runtime/loop.py)

После обработки событий вызывать `decay_memory()` для всех записей в `self_state.memory`.

## Этап 5: Внутренняя динамика — шум и дрейф

### 5.1 Обновить обработку событий для noise/drift

**Файл:** [`src/runtime/loop.py`](src/runtime/loop.py)

- При событиях типа `noise`: увеличивать `self_state.noise`
- Каждый тик: `noise *= 0.95` (затухание)
- Каждый тик: `drift += (stability - 0.5) * 0.001` (дрейф к равновесию)

### 5.2 Влияние noise/drift на восприятие

**Файл:** [`src/meaning/engine.py`](src/meaning/engine.py) (опционально)

Модифицировать оценку значимости:

```python
effective_intensity = event.intensity * (1.0 - state.noise * 0.1)
```

## Этап 6: Обновление документации

### 6.1 Обновить Self-State документацию

**Файл:** [`docs/components/self-state.md`](docs/components/self-state.md)

Добавить описание новых полей и субъективного времени.

### 6.2 Создать документацию Lifecycle

**Файл:** [`docs/components/lifecycle.md`](docs/components/lifecycle.md) (новый)

Описать этапы жизни, переходы, хуки.

### 6.3 Обновить статус проекта

**Файл:** [`docs/development/status.md`](docs/development/status.md)

Отметить расширение Self-State и добавление Lifecycle.

## Приоритеты реализации

1. **P0 (Критично)**: Этап 1 (Self-State расширение) + Этап 3 (Snapshots восстановление)
2. **P1 (Важно)**: Этап 2 (Lifecycle) + Этап 4 (Забывание памяти)
3. **P2 (Улучшение)**: Этап 5 (Внутренняя динамика)
4. **P3 (Документация)**: Этап 6

## Метрики успеха

- Self-State содержит все поля из спецификации
- При старте система восстанавливается из последнего snapshot
- Память деградирует со временем (старые записи теряют значимость)
- Субъективное время отличается от физического
- Система переходит в этап DEGRADE при низких параметрах

## Риски и ограничения

- **Совместимость snapshots**: Старые snapshots без новых полей должны загружаться (использовать значения по умолчанию)
- **Производительность**: Забывание памяти не должно замедлять тики
- **Тестирование**: Нужны тесты для lifecycle переходов и забывания
