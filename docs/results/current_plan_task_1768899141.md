# План выполнения: Вынести сохранение snapshot в `SnapshotManager` (периодичность, ошибки, формат)

> **Задача:** Вынести сохранение snapshot в `SnapshotManager` (политика периодичности, ошибки, формат)
> **Контекст:** Рефакторинг Runtime Loop (RL.1 / задача #2 из `todo/GENERATED_20260120_20260120_094041.md`)
> **Источник требований:** `docs/planning/task_2_20260120_094041.md`
> **Дата создания:** 2026-01-20
> **ID:** task_1768899141

## 1. Контекст (что есть сейчас)

- **Где принимается решение “когда сохранять”**: `src/runtime/loop.py` — блок “Snapshot каждые snapshot_period тиков”.
- **Где реализовано “как сохранять / формат”**: `src/state/self_state.py::save_snapshot(state)` — сериализация `SelfState` в JSON, исключение transient полей, special-обработка `memory`, имя файла `data/snapshots/snapshot_{tick:06d}.json`.
- **Как обрабатываются ошибки сейчас**: `src/runtime/loop.py` ловит исключение при `save_snapshot(self_state)` и логирует `logger.error(..., exc_info=True)`.

## 2. Цель и ограничения

### Цель

Сделать `run_loop` чище: вынести scheduling и обработку ошибок snapshot в отдельный компонент `SnapshotManager`, оставив `run_loop` только координатором.

### Ограничения (важно сохранить)

- **Формат снапшота не менять**: `save_snapshot(self_state)` остается единым механизмом сериализации (как зафиксировано в `docs/planning/task_2_20260120_094041.md`).
- **Семантика периодичности не меняется**: ticks-based, по умолчанию “каждые `snapshot_period` тиков”.
- **Ошибки snapshot не должны ронять loop**: логируем и продолжаем.
- **Без новых внешних зависимостей** (только stdlib + текущие сущности проекта).

## 3. План работ (по шагам)

### Шаг 0: Инвентаризация контрактов и точек интеграции

- Зафиксировать текущую семантику: snapshot сохраняется, когда `ticks % snapshot_period == 0`.
- Зафиксировать текущую реакцию на ошибку: исключение ловится, пишется `logger.error`, цикл продолжается.
- Зафиксировать текущий формат файлов: имя, каталог, JSON и исключение transient полей — всё внутри `save_snapshot`.

### Шаг 1: Спроектировать API `SnapshotManager`

Рекомендуемый минимальный API (из документации задачи):

- `SnapshotManager(period_ticks: int, saver: Callable[[SelfState], None])`
- `should_snapshot(ticks: int) -> bool`
- `maybe_snapshot(self_state: SelfState) -> bool`:
  - возвращает `True`, если был выполнен вызов сохранения (даже если saver внутри не пишет из-за своих условий — но у нас saver без условий),
  - внутри ловит исключения и логирует (не пробрасывает).

Параметры/поведение:

- **period_ticks**:
  - `<= 0` трактовать как “snapshot отключен” (или валидировать и падать при инициализации; выбрать вариант и зафиксировать в доке/тестах).
- **saver**:
  - по умолчанию — `src.state.self_state.save_snapshot`.
  - формат/путь/исключение transient полей остаются обязанностью `saver`.

### Шаг 2: Реализовать `src/runtime/snapshot_manager.py`

- Реализовать класс `SnapshotManager` с минимальным состоянием:
  - `period_ticks`
  - `saver`
  - `logger` (использовать `logging.getLogger(__name__)` внутри модуля).
- В `maybe_snapshot`:
  - проверить `should_snapshot(self_state.ticks)`,
  - при необходимости вызвать `self._saver(self_state)` в `try/except`,
  - на ошибке: `logger.error("...", exc_info=True)` и вернуть `False`/`True` согласно выбранному контракту (зафиксировать в тестах).

### Шаг 3: Интегрировать в `src/runtime/loop.py`

- В начале `run_loop` создать менеджер:
  - `snapshot_manager = SnapshotManager(period_ticks=snapshot_period, saver=save_snapshot)`
- Заменить inline-блок:
  - вместо `if ticks % snapshot_period == 0: try: save_snapshot(...) except: ...`
  - вызвать `snapshot_manager.maybe_snapshot(self_state)`.

### Шаг 4: Тесты (unit)

Добавить unit-тесты (ориентир: `docs/planning/task_2_20260120_094041.md`, “Тест 5.1”):

- **Периодичность**: для `period_ticks = 10` `saver` вызывается только на тиках 10, 20, 30, ...
- **Ошибки**: если `saver` кидает исключение, `maybe_snapshot` не пробрасывает его наружу и `saver` может быть вызван повторно на следующем периоде.
- **Формат**: отдельным unit-тестом формат не тестировать (формат уже обязанность `save_snapshot`), но проверить, что `SnapshotManager` вызывает переданный `saver` “как есть” и не модифицирует данные.

### Шаг 5: Сверка с документацией

- Убедиться, что документ `docs/components/runtime-loop.md` всё ещё корректен: “Snapshot: периодическое сохранение состояния на диск” и дефолт `snapshot_period = 10`.
- Если понадобится уточнение (например, “period_ticks <= 0 отключает snapshot”), отразить это в документации задачи/компонента (без расширения функционала).

## 4. Критерии приемки

- ✅ В `src/runtime/loop.py` больше нет inline-логики снапшотов — используется `SnapshotManager`.
- ✅ Периодичность snapshot соответствует прежней (ticks-based, дефолт 10).
- ✅ Ошибки snapshot логируются и не останавливают loop.
- ✅ Формат snapshot не изменен (всё по-прежнему через `save_snapshot(self_state)`).
- ✅ Добавлены unit-тесты на периодичность и обработку ошибок.

---

**Автор плана:** AI Agent (Project Executor)
