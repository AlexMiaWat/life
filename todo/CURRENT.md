# P1: Docs (Документация)
- [x] Обновить [`03_SELF_STATE.md`](docs/system/03_SELF_STATE.md) с планом добавления уровней 0-4 (identity, vital, temporal, internal, memory) и классом SelfState с валидацией
- [x] Добавить в [`02_RUNTIME_LOOP.md`](docs/system/02_RUNTIME_LOOP.md) раздел "Модульная рефакторинг" для выноса perceive/decide/act в отдельные функции/модули
- [ ] Обновить [`07_ENVIRONMENT.md`](docs/system/07_ENVIRONMENT.md) с интеграцией MeaningEngine и заменой _interpret_event на engine.process()
- [ ] Добавить в [`08_EVENTS_AND_MEANING.md`](docs/system/08_EVENTS_AND_MEANING.md) раздел "Интеграция в Loop" для замены _interpret_event на MeaningEngine.process()
- [ ] Обновить [`now.md`](docs/meta/NOW.md): "Изучены индексы. Выявлены несоответствия в Self-State и Loop. Следующий: интеграция Meaning в Loop (этап 08)."
- [ ] Создать [`skeptic_12.01.26.md`](docs/skeptic/skeptic_12.01.26.md) с повтором failures и верификацией кода (запустить [`main_server_api.py`](src/main_server_api.py), показать логи до energy<0)
- [ ] Обновить [`todo_07-18.md`](todo/ROADMAP.md): отметить [x] для интеграции Meaning; добавить задачи по Memory (этап 09)
- [ ] Обновить [`_project_tree.md`](docs/meta/PROJECT_TREE.md): добавить master_*.md в docs/ как индексы
- [ ] Добавить в [`auto-reload-plan.md`](docs/meta/AUTO_RELOAD_PLAN.md): "Переход на process-restart" для решения проблем с reload и идентичностью

# P2: Код (Code)
- [ ] Реализовать в [`self_state.py`](src/state/self_state.py) класс SelfState как dataclass с уровнями 0-4 (identity, vital, temporal, internal, memory)
- [ ] Создать [`steps.py`](src/runtime/steps.py) с функциями perceive/decide/act для модульной рефакторинга loop
- [ ] В [`loop.py`](src/runtime/loop.py) заменить _interpret_event на вызов MeaningEngine.process()
- [ ] Интегрировать MeaningEngine в run_loop вместо старой _interpret_event

# P3: Тесты (Tests)
- [ ] Запустить [`main_server_api.py`](src/main_server_api.py), показать логи до energy<0 для верификации
- [ ] Тест: запустить с [`generator_cli.py`](src/environment/generator_cli.py), проверить влияние significance на дельты
- [ ] Запустить систему, мониторить 100 тиков. Если стабильность <0.3 — остановить и анализировать

# P4: Позже (Later)
- [ ] Отметить [x] для изученных высших слоев (09-18) в [`todo_07-18.md`](todo/ROADMAP.md), не трогать пока не завершены 07-08
- [ ] Решить tooling проблемы: dev-mode/reloader (висящие серверы), API как канал среды (не админка), reload ломает идентичность (Self-State mutable dict)
- [ ] Регулярно проверять актуальность ссылок в документации после изменений структуры

# now.md — Текущее состояние проекта Life на 11.01.2026

## Общий статус
- Этап 00–02: Документация стабилизирована (VISION, ARCHITECTURE, RUNTIME_LOOP с модульностью).
- Этап 03: SelfState описан в docs, но не реализован в коде — следующий приоритет.
- Этап 07–08: Environment готов, MeaningEngine готов, но интеграция в loop только спланирована.
- Этапы 09+: Не начаты, ждём завершения 03–08.
- Tooling: API работает, но reload ломает идентичность (SelfState как dict — временно).

## Что сделано недавно
- Обновлена структура SelfState (уровни 0–4 с валидацией).
- Модульный рефакторинг Runtime Loop описан (steps.py, интеграция Meaning).
- Индексы master_* проанализированы — несоответствия выявлены и задокументированы.

## Текущие риски (из skeptic)
- SelfState mutable dict → потеря идентичности при reload.
- Нет тестов на деградацию → ручные запуски ненадёжны.
- Преждевременная интеграция высших слоев → остановлено.

## Следующий шаг
1. Реализовать SelfState как dataclass в src/state/self_state.py (с валидацией).
2. Интегрировать в runtime/loop.py.
