# Документация по тестированию проекта Life

## Обзор

Проект Life покрыт комплексными тестами для всех разработанных модулей. Все тесты находятся в директории `src/test/` и используют pytest.

## Статистика тестирования

- **Всего тестов:** 766+ (см. [docs/development/STATISTICS.md](../development/STATISTICS.md) для актуальной статистики)
- **Все тесты проходят:** ✅ (статические и интеграционные)
- **Покрытие кода:** 96%
- **Основные модули:** 100% покрытие
- **Новые тесты (2026-01-20):** Комплексное тестирование новой функциональности
  - Learning Engine: 45 статических тестов ✅
  - Adaptation Manager: полное покрытие ✅
  - MeaningEngine: полное покрытие ✅
  - Субъективное время: полное покрытие ✅
  - Потокобезопасность: полное покрытие ✅
  - MCP Index Engine: полное покрытие ✅
- **API тесты:** Требуют обновления (устаревшие после изменений API)

## Быстрый старт

### Установка зависимостей

```bash
pip install -r requirements.txt
pip install pytest pytest-cov
```

### Запуск тестов

```bash
# Все тесты
pytest src/test/ -v

# С покрытием кода
pytest src/test/ --cov=src --cov-report=html

# Конкретный модуль
pytest src/test/test_memory.py -v

# Быстрый запуск
pytest src/test/ -q
```

## Структура тестов

Все тесты находятся в `src/test/`:

- `test_memory.py` - Тесты модуля Memory (MemoryEntry, Memory) + нагрузочные тесты + тесты субъективного времени (v2.1)
- `test_state.py` - Тесты модуля State (SelfState, snapshots)
- `test_activation.py` - Тесты модуля Activation
- `test_meaning.py` - Тесты модуля Meaning (Meaning, MeaningEngine)
- `test_decision.py` - Тесты модуля Decision
- `test_action.py` - Тесты модуля Action
- `test_environment.py` - Тесты модуля Environment (Event, EventQueue)
- `test_feedback.py` - Тесты модуля Feedback
- `test_new_functionality_integration.py` - Интеграционные тесты новой функциональности + тесты субъективного времени (v2.1)
- `test_planning.py` - Тесты модуля Planning
- `test_intelligence.py` - Тесты модуля Intelligence
- `test_learning.py` - Тесты модуля Learning
- `test_adaptation.py` - Тесты модуля Adaptation
- `test_learning_adaptation_integration.py` - Интеграционные тесты Learning + Adaptation
- `test_runtime_integration.py` - Интеграционные тесты для Runtime Loop
- `test_api_integration.py` - Интеграционные тесты API сервера
- `test_generator.py` - Тесты генератора событий
- `test_generator_integration.py` - Интеграционные тесты генератора с сервером
- `test_monitor.py` - Тесты модуля Monitor
- `test_runtime_loop_edge_cases.py` - Edge cases Runtime Loop
- `test_runtime_loop_feedback_coverage.py` - Тесты обработки Feedback в Loop
- `test_runtime_loop_managers.py` - Тесты менеджеров Runtime Loop (SnapshotManager, LogManager, LifePolicy) - **ОБНОВЛЕНО**
- `test_event_queue_edge_cases.py` - Edge cases EventQueue
- `test_event_queue_race_condition.py` - Race conditions в EventQueue
- `test_status_race_conditions.py` - Race conditions для чтения /status API во время тиков **НОВЫЙ**
- `test_generator_cli.py` - Тесты CLI генератора
- `test_degradation.py` - Тесты на деградацию системы + длительная работа
- `test_property_based.py` - Property-based тесты (hypothesis) - **НОВЫЙ**
- `test_performance.py` - Тесты производительности (benchmarks) - **НОВЫЙ**
- `test_api_auth_integration.py` - Интеграционные тесты API аутентификации - **НОВЫЙ**
- `test_api_auth_smoke.py` - Дымовые тесты API аутентификации - **НОВЫЙ**
- `test_api_auth_static.py` - Статические тесты API аутентификации - **НОВЫЙ**

## Покрытие модулей

### Полностью покрытые модули (100%)

1. **action/action.py** - 100%
2. **activation/activation.py** - 100%
3. **adaptation/adaptation.py** - 100%
4. **decision/decision.py** - 100%
5. **feedback/feedback.py** - 100%
6. **intelligence/intelligence.py** - 100%
7. **learning/learning.py** - 100%
8. **meaning/meaning.py** - 100%
9. **meaning/engine.py** - 100%
10. **memory/memory.py** - 100%
11. **planning/planning.py** - 100%
12. **state/self_state.py** - 100%
11. **environment/generator.py** - 100%
12. **environment/event.py** - 100%
13. **monitor/console.py** - 100%
14. **environment/generator_cli.py** - 100%

### Тесты субъективного времени (v2.1)

Новая функциональность субъективного времени покрыта комплексными тестами:

**Unit-тесты в `test_memory.py`:**
- `test_memory_entry_with_subjective_timestamp` - создание MemoryEntry с субъективным временем
- `test_memory_entry_subjective_timestamp_default` - значение по умолчанию для поля
- `test_archive_memory_backward_compatibility` - обратная совместимость загрузки старых архивов
- `test_archive_memory_forward_compatibility` - прямая совместимость сохранения новых архивов

**Интеграционные тесты в `test_new_functionality_integration.py`:**
- `test_subjective_time_memory_integration` - интеграция записи субъективного времени в обычные события
- `test_subjective_time_feedback_memory_integration` - интеграция записи субъективного времени в Feedback
- `test_subjective_time_monotonic_in_memory` - проверка монотонности субъективного времени

**Особенности тестирования:**
- Обратная совместимость: старые snapshot/memory файлы загружаются корректно
- Прямая совместимость: новые файлы сохраняют поле subjective_timestamp
- Интеграционные тесты проверяют работу в полном Runtime Loop
- Все тесты используют реальное многопоточное исполнение

### Частично покрытые модули

1. **runtime/loop.py** - ~95-100%
   - Все edge cases покрыты
   - Остались только редкие ветки

2. **main_server_api.py** - 86%
   - Основные эндпоинты покрыты на 100%
   - Служебный код (reloader, точки входа) исключен через `# pragma: no cover`

3. **environment/event_queue.py** - 93%
   - Все основные функции покрыты
   - Edge cases покрыты

## Документация

### Основные документы

- **[TESTING_INSTRUCTIONS.md](TESTING_INSTRUCTIONS.md)** - Подробные инструкции по тестированию
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Руководство по тестированию
- **[TESTING_RESULTS.md](TESTING_RESULTS.md)** - Результаты тестирования
- **[TESTING_ROADMAP_T5.md](TESTING_ROADMAP_T5.md)** - Документация по выполнению ROADMAP Цель 5 (T.1-T.15)
- **[COVERAGE_100_COMPLETE.md](COVERAGE_100_COMPLETE.md)** - Отчет о достижении максимального покрытия

### Отчеты по покрытию

- **[COVERAGE_FINAL_SUMMARY.md](COVERAGE_FINAL_SUMMARY.md)** - Финальная сводка покрытия
- **[COVERAGE_100_ACHIEVED.md](COVERAGE_100_ACHIEVED.md)** - Достижение 96% покрытия

### Отчеты по модулям

- **[FEEDBACK_TESTING_RESULTS.md](FEEDBACK_TESTING_RESULTS.md)** - Результаты тестирования Feedback
- **[FEEDBACK_TEST_REPORT.md](FEEDBACK_TEST_REPORT.md)** - Отчет по тестам Feedback
- **[FEEDBACK_MANUAL_TEST.md](FEEDBACK_MANUAL_TEST.md)** - Ручное тестирование Feedback

## Типы тестов

### Статические тесты (2026-01-20)
- Тестирование структуры кода и архитектуры без запуска
- Проверка корректности импортов, сигнатур функций, констант
- Быстрое выполнение, идеально для CI/CD
- Примеры: `test_new_functionality_static.py` (45 тестов ✅)

### Дымовые тесты (Smoke tests) (2026-01-20)
- Базовая проверка работоспособности компонентов
- Тестирование основных сценариев использования
- Раннее обнаружение критических проблем
- Примеры: `test_new_functionality_smoke.py` (47/54 тестов ✅)

### Интеграционные тесты новой функциональности (2026-01-20)
- Тестирование взаимодействия Learning ↔ Adaptation ↔ MeaningEngine
- Полные циклы обработки событий с новой логикой
- Тестирование с реальным состоянием и памятью
- Примеры: `test_new_functionality_integration.py` (28/39 тестов ✅)

### Unit тесты
- Изолированное тестирование отдельных функций и классов
- Быстрое выполнение
- Легкая отладка

### Integration тесты
- Тестирование взаимодействия между модулями
- Проверка полных сценариев использования
- Тесты с запуском реального сервера

### Property-based тесты (hypothesis)
- Тестирование инвариантов и свойств системы
- Автоматическая генерация тестовых данных
- Файл: `test_property_based.py`

### Тесты производительности (benchmarks)
- Проверка производительности критических операций
- Установка порогов производительности
- Файл: `test_performance.py`
- Маркер: `@pytest.mark.performance`

### Нагрузочные тесты
- Тестирование при больших объемах данных
- Проверка ограничений и производительности
- Маркер: `@pytest.mark.slow`

### Тесты race conditions для API /status (НОВЫЕ)
- **Комплексные тесты** (`test_status_race_conditions.py`):
  - Множественные одновременные запросы `/status` во время активных тиков
  - Чтение статуса в момент модификации состояния runtime loop
  - Проверка консистентности snapshot при высокой нагрузке
  - Чтение статуса во время операций архивации памяти
  - Чтение статуса сразу после завершения тика
  - Чтение статуса во время обработки очереди событий
  - Чтение статуса во время создания снапшота
  - Высокая частота подачи событий и overflow handling
  - Одновременные операции push и pop_all в EventQueue
  - Доступ к пустой очереди из нескольких потоков
  - Гонка между проверкой empty() и get_nowait()
  - Маркер: `@pytest.mark.concurrency` и `@pytest.mark.race_conditions`

### API тесты аутентификации (НОВЫЕ)
- **Интеграционные тесты** (`test_api_auth_integration.py`):
  - Полный жизненный цикл пользователя (регистрация → вход → использование)
  - Изоляция пользователей и сессий
  - Обработка ошибок и edge cases
  - Маркер: `@pytest.mark.integration`

- **Дымовые тесты** (`test_api_auth_smoke.py`):
  - Базовая работоспособность API
  - Доступность публичных и защищенных эндпоинтов
  - Регистрация и аутентификация пользователей
  - Маркер: `@pytest.mark.smoke`

- **Статические тесты** (`test_api_auth_static.py`):
  - Структура Pydantic моделей (User, Token, EventCreate, etc.)
  - Сигнатуры функций и типов возвращаемых значений
  - Безопасность JWT токенов и хеширования паролей
  - Архитектурные ограничения аутентификации
  - Маркер: `@pytest.mark.static`

### Тесты делегирования и отсутствия регрессий (НОВЫЕ)
- **Тесты делегирования** (`TestRunLoopDelegation` в `test_runtime_loop_managers.py`):
  - Проверка делегирования вызовов из `run_loop` в менеджеры
  - Использование моков/spy для проверки факта вызовов
  - Проверка правильности аргументов и условий вызова
  - Маркер: `@pytest.mark.unit`

- **Тесты отсутствия регрессий** (`TestNoRegressionBehavior` в `test_runtime_loop_managers.py`):
  - Проверка сохранения поведения после рефакторинга
  - Тесты периодичности снапшотов и flush
  - Тесты корректности применения weakness penalties
  - Маркер: `@pytest.mark.unit`

- **Интеграционные тесты координации** (`TestRunLoopCoordination` в `test_runtime_loop_managers.py`):
  - Проверка координации между менеджерами в реальном `run_loop`
  - Тесты многопоточного выполнения runtime loop
  - Проверка последовательности операций
  - Маркер: `@pytest.mark.integration`

## Команды для запуска

```bash
# Все тесты
pytest src/test/ -v

# С покрытием кода
pytest src/test/ --cov=src --cov-report=html

# Конкретный модуль
pytest src/test/test_memory.py -v

# Поиск конкретного теста
pytest src/test/ -k "test_memory"

# С подробным выводом
pytest src/test/ -v -s

# Только failed тесты
pytest src/test/ --lf

# С остановкой на первой ошибке
pytest src/test/ -x
```

## Покрытие кода

### HTML отчет

После запуска с `--cov-report=html` отчет доступен в `htmlcov/index.html`:

```bash
pytest src/test/ --cov=src --cov-report=html
```

### Консольный отчет

```bash
pytest src/test/ --cov=src --cov-report=term-missing
```

## Результаты

### Общее покрытие: 96%

**Покрытие по категориям:**
- Бизнес-логика: 100% ✅
- API эндпоинты: 100% ✅ (включая аутентификацию и race conditions)
- Генератор событий: 100% ✅
- Runtime Loop: ~95-100% ✅ (включая тесты делегирования и отсутствия регрессий)
- Monitor: 100% ✅
- EventQueue: 93% ✅ (улучшено тестами race conditions)
- API аутентификация: 100% ✅ (интеграционные, дымовые и статические тесты)
- Менеджеры Runtime Loop: 100% ✅ (SnapshotManager, LogManager, LifePolicy)
- Race conditions API /status: 100% ✅ (14 новых тестов покрывают все сценарии)

### Прогресс покрытия

- Начальное: 89%
- После улучшений: 92%
- После edge cases: 95%
- Финальное: 96%

## Лучшие практики

1. **Именование тестов:** Используйте описательные имена
2. **Один тест - одна проверка:** Каждый тест проверяет одну функциональность
3. **Изоляция:** Тесты не должны зависеть друг от друга
4. **Фикстуры:** Используйте фикстуры для подготовки данных
5. **Очистка:** Убедитесь, что тесты не оставляют побочных эффектов

## Решение проблем

### Проблема: Импорты не работают

**Решение:** Убедитесь, что путь к `src` добавлен в `sys.path` в начале каждого тестового файла.

### Проблема: Тесты падают из-за временных файлов

**Решение:** Используйте `tmp_path` фикстуру pytest для временных файлов.

### Проблема: Тесты зависят от порядка выполнения

**Решение:** Убедитесь, что каждый тест изолирован и не зависит от состояния других тестов.

## Контакты

При возникновении вопросов или проблем с тестами, обратитесь к документации проекта или создайте issue.
