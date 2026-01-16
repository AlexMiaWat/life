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
- [ ] **PRIORITY: Реализовать Feedback слой (этап 13)** — см. [`13.1_FEEDBACK_Work.md`](docs/system/13.1_FEEDBACK_Work.md):
  - [ ] Создать модуль `src/feedback/` с файлами:
    - [ ] `src/feedback/feedback.py` — функции `register_action()`, `observe_consequences()`, классы `PendingAction`, `FeedbackRecord`
    - [ ] `src/feedback/__init__.py` — экспорт функций и классов
  - [ ] Интегрировать в `src/runtime/loop.py`:
    - [ ] Добавить импорты Feedback модуля
    - [ ] Инициализировать `pending_actions = []` в начале `run_loop()`
    - [ ] Сохранить `state_before` ДО `execute_action()` (строка ~64)
    - [ ] Вызвать `register_action()` после `execute_action()` (строка ~65)
    - [ ] Вызвать `observe_consequences()` в начале каждого тика (после обработки событий, строка ~73)
    - [ ] Сохранить Feedback записи в Memory
  - [ ] Протестировать: регистрация действий, наблюдение через 3-10 тиков, сохранение в Memory
- [ ] Реализовать в [`self_state.py`](src/state/self_state.py) класс SelfState как dataclass с уровнями 0-4 (identity, vital, temporal, internal, memory)
- [ ] Создать [`steps.py`](src/runtime/steps.py) с функциями perceive/decide/act для модульной рефакторинга loop
- [ ] В [`loop.py`](src/runtime/loop.py) заменить _interpret_event на вызов MeaningEngine.process()
- [ ] Интегрировать MeaningEngine в run_loop вместо старой _interpret_event

# P3: Тесты (Tests)
- [ ] **PRIORITY: Тестирование Feedback**:
  - [ ] Запустить систему с Feedback, проверить регистрацию действий
  - [ ] Проверить создание FeedbackRecord после 3-10 тиков
  - [ ] Проверить сохранение Feedback записей в Memory
  - [ ] Проверить, что Action не знает о Feedback (нет импортов в action.py)
  - [ ] Проверить удаление PendingAction после обработки или через 20 тиков
- [ ] Запустить [`main_server_api.py`](src/main_server_api.py), показать логи до energy<0 для верификации
- [ ] Тест: запустить с [`generator_cli.py`](src/environment/generator_cli.py), проверить влияние significance на дельты
- [ ] Запустить систему, мониторить 100 тиков. Если стабильность <0.3 — остановить и анализировать

# P4: Позже (Later)
- [ ] Отметить [x] для изученных высших слоев (09-18) в [`todo_07-18.md`](todo/ROADMAP.md), не трогать пока не завершены 07-08
- [ ] Решить tooling проблемы: dev-mode/reloader (висящие серверы), API как канал среды (не админка), reload ломает идентичность (Self-State mutable dict)
- [ ] Регулярно проверять актуальность ссылок в документации после изменений структуры

# Текущее состояние проекта Life (обновлено 13.01.2026)

## Общий статус
- Этап 00–02: Документация стабилизирована (VISION, ARCHITECTURE, RUNTIME_LOOP с модульностью).
- Этап 03: SelfState реализован как dataclass.
- Этап 07–08: Environment и MeaningEngine полностью интегрированы в Runtime Loop.
- Этап 09: Memory v1.0 реализован и интегрирован.
- Этап 10.1: Activation v1.0 реализован и интегрирован.
- Этап 11.1: Decision v1.0 реализован и интегрирован.
- Этап 12.1: Action v1.0 реализован и интегрирован.
- Этап 13: **Feedback — архитектурная спецификация готова, готово к реализации**.
- Этапы 17–18: Planning и Intelligence v1.0 реализованы и интегрированы.
- Tooling: API работает, reload сохраняет идентичность (SelfState как dataclass).

## Что сделано недавно
- **Архитектурная работа**: Создана полная спецификация Feedback (13.1_FEEDBACK_Work.md).
- Обновлены основные документы: PROJECT_PLAN.md, ARCHITECTURE.md, INDEX.md, MANIFEST.md.
- Все связи между слоями документированы.

## Текущие риски (из skeptic)
- Минимальные реализации слоев могут быть недостаточными для долгосрочной эволюции.
- Нет тестов на деградацию → ручные запуски ненадёжны.
- Необходимость расширения Memory для забывания и архивации.

## Следующий шаг (для Implementer)
1. **Реализовать Feedback слой (этап 13)** согласно спецификации в `docs/system/13.1_FEEDBACK_Work.md`:
   - Создать модуль `src/feedback/`
   - Интегрировать в `src/runtime/loop.py`
   - Протестировать работу
2. Расширить Memory с механизмами забывания и архивации (опционально).
3. Добавить тесты на деградацию и устойчивость системы.
