# P1: Docs (Документация)
- [X] Обновить [`03_SELF_STATE.md`](docs/03_SELF_STATE.md) с планом добавления уровней 0-4 (identity, vital, temporal, internal, memory) и классом SelfState с валидацией
- [X] Добавить в [`02_RUNTIME_LOOP.md`](docs/02_RUNTIME_LOOP.md) раздел "Модульная рефакторинг" для выноса perceive/decide/act в отдельные функции/модули
- [ ] Обновить [`07_ENVIRONMENT.md`](docs/07_ENVIRONMENT.md) с интеграцией MeaningEngine и заменой _interpret_event на engine.process()
- [ ] Добавить в [`08_EVENTS_AND_MEANING.md`](docs/08_EVENTS_AND_MEANING.md) раздел "Интеграция в Loop" для замены _interpret_event на MeaningEngine.process()
- [ ] Обновить [`now.md`](docs/now.md): "Изучены индексы. Выявлены несоответствия в Self-State и Loop. Следующий: интеграция Meaning в Loop (этап 08)."
- [ ] Создать [`skeptic_12.01.26.md`](docs/skeptic/skeptic_12.01.26.md) с повтором failures и верификацией кода (запустить [`main_server_api.py`](src/main_server_api.py), показать логи до energy<0)
- [ ] Обновить [`todo_07-18.md`](docs/todo_07-18.md): отметить [x] для интеграции Meaning; добавить задачи по Memory (этап 09)
- [ ] Обновить [`_project_tree.md`](docs/_project_tree.md): добавить master_*.md в docs/ как индексы
- [ ] Добавить в [`auto-reload-plan.md`](docs/auto-reload-plan.md): "Переход на process-restart" для решения проблем с reload и идентичностью

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
- [ ] Отметить [x] для изученных высших слоев (09-18) в [`todo_07-18.md`](docs/todo_07-18.md), не трогать пока не завершены 07-08
- [ ] Решить tooling проблемы: dev-mode/reloader (висящие серверы), API как канал среды (не админка), reload ломает идентичность (Self-State mutable dict)