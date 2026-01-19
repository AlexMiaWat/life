# Документация по тестированию проекта Life

## Обзор

Проект Life покрыт комплексными тестами для всех разработанных модулей. Все тесты находятся в директории `src/test/` и используют pytest.

## Статистика тестирования

- **Всего тестов:** 226
- **Все тесты проходят:** ✅ 226/226
- **Покрытие кода:** 96%
- **Основные модули:** 100% покрытие

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

- `test_memory.py` - Тесты модуля Memory (MemoryEntry, Memory) + нагрузочные тесты
- `test_state.py` - Тесты модуля State (SelfState, snapshots)
- `test_activation.py` - Тесты модуля Activation
- `test_meaning.py` - Тесты модуля Meaning (Meaning, MeaningEngine)
- `test_decision.py` - Тесты модуля Decision
- `test_action.py` - Тесты модуля Action
- `test_environment.py` - Тесты модуля Environment (Event, EventQueue)
- `test_feedback.py` - Тесты модуля Feedback
- `test_planning.py` - Тесты модуля Planning
- `test_intelligence.py` - Тесты модуля Intelligence
- `test_runtime_integration.py` - Интеграционные тесты для Runtime Loop
- `test_api_integration.py` - Интеграционные тесты API сервера
- `test_generator.py` - Тесты генератора событий
- `test_generator_integration.py` - Интеграционные тесты генератора с сервером
- `test_monitor.py` - Тесты модуля Monitor
- `test_runtime_loop_edge_cases.py` - Edge cases Runtime Loop
- `test_runtime_loop_feedback_coverage.py` - Тесты обработки Feedback в Loop
- `test_event_queue_edge_cases.py` - Edge cases EventQueue
- `test_event_queue_race_condition.py` - Race conditions в EventQueue
- `test_generator_cli.py` - Тесты CLI генератора
- `test_degradation.py` - Тесты на деградацию системы + длительная работа
- `test_property_based.py` - Property-based тесты (hypothesis) - **НОВЫЙ**
- `test_performance.py` - Тесты производительности (benchmarks) - **НОВЫЙ**

## Покрытие модулей

### Полностью покрытые модули (100%)

1. **action/action.py** - 100%
2. **activation/activation.py** - 100%
3. **decision/decision.py** - 100%
4. **feedback/feedback.py** - 100%
5. **intelligence/intelligence.py** - 100%
6. **meaning/meaning.py** - 100%
7. **meaning/engine.py** - 100%
8. **memory/memory.py** - 100%
9. **planning/planning.py** - 100%
10. **state/self_state.py** - 100%
11. **environment/generator.py** - 100%
12. **environment/event.py** - 100%
13. **monitor/console.py** - 100%
14. **environment/generator_cli.py** - 100%

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
- API эндпоинты: 100% ✅
- Генератор событий: 100% ✅
- Runtime Loop: ~95-100% ✅
- Monitor: 100% ✅
- EventQueue: 93% ✅

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
