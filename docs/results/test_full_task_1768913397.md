# Отчет о полном тестировании проекта

**Дата:** 2025-01-20  
**Задача:** test_full_task_1768913397  
**Каталог тестов:** `src/test`

## Общая статистика

- **Всего тестов:** 608
- **Пройдено:** 534 (87.8%)
- **Провалено:** 74 (12.2%)
- **Пропущено:** 4 (0.7%)
- **Время выполнения:** 175.32 секунд (~2 минуты 55 секунд)

## Сводка по модулям

| Модуль | Всего | Пройдено | Провалено | Процент успеха |
|--------|-------|----------|-----------|----------------|
| test_action | 12 | 12 | 0 | 100% |
| test_activation | 13 | 13 | 0 | 100% |
| test_adaptation | 2 | 0 | 2 | 0% |
| test_decision | 14 | 14 | 0 | 100% |
| test_degradation | 3 | 0 | 3 | 0% |
| test_environment | 25 | 25 | 0 | 100% |
| test_feedback | 10 | 10 | 0 | 100% |
| test_generator | 16 | 16 | 0 | 100% |
| test_intelligence | 10 | 10 | 0 | 100% |
| test_learning | 7 | 0 | 7 | 0% |
| test_learning_adaptation_integration | 3 | 0 | 3 | 0% |
| test_mcp_interactive | 1 | 0 | 1 | 0% |
| test_mcp_refresh_index | 1 | 0 | 1 | 0% |
| test_mcp_server | 21 | 0 | 21 | 0% |
| test_memory | 10 | 0 | 10 | 0% |
| test_monitor | 6 | 0 | 6 | 0% |
| test_performance | 4 | 0 | 4 | 0% |
| test_property_based | 1 | 0 | 1 | 0% |
| test_state | 15 | 0 | 15 | 0% |
| test_meaning | 30 | 30 | 0 | 100% |
| test_planning | 9 | 9 | 0 | 100% |
| test_runtime | 3 | 3 | 0 | 100% |
| test_subjective_time | 10 | 10 | 0 | 100% |

## Детальный анализ ошибок

### 1. Модуль: test_adaptation (2 ошибки)

#### test_apply_adaptation_initialization
- **Ошибка:** `assert 0.21000000000000002 == 0.3`
- **Описание:** Неверное значение параметра `behavior_sensitivity["noise"]` после инициализации адаптации
- **Файл:** `src/test/test_adaptation.py:92`
- **Причина:** Ожидается значение 0.3, но получается 0.21

#### test_apply_adaptation_no_decision_action_control
- **Ошибка:** `Failed: DID NOT RAISE <class 'ValueError'>`
- **Описание:** Тест ожидает исключение ValueError при отсутствии контроля действий решения, но исключение не возникает
- **Файл:** `src/test/test_adaptation.py:151`
- **Причина:** Отсутствует валидация входных данных в методе адаптации

### 2. Модуль: test_degradation (3 ошибки)

#### test_active_flag_stays_false_after_deactivation
- **Ошибка:** `AssertionError: assert True is False`
- **Описание:** Флаг `active` остается `True` после деактивации деградации
- **Файл:** `src/test/test_degradation.py:666`
- **Причина:** Неправильная логика деактивации флага

#### test_degradation_over_1000_ticks
- **Ошибка:** `AssertionError: Expected >= 1000 ticks, got 1`
- **Описание:** Тест ожидает выполнение 1000 тиков, но выполняется только 1
- **Файл:** `src/test/test_degradation.py:814`
- **Причина:** Проблема с циклом выполнения или условием остановки

#### test_degradation_stability_over_time
- **Ошибка:** `AssertionError: assert 108 >= 1000`
- **Описание:** Выполняется только 108 тиков вместо ожидаемых 1000
- **Файл:** `src/test/test_degradation.py:852`
- **Причина:** Аналогично предыдущей ошибке - проблема с циклом выполнения

### 3. Модуль: test_learning (7 ошибок)

#### test_learning_persistence_in_snapshots
- **Ошибка:** `NameError: name 'json' is not defined`
- **Описание:** Отсутствует импорт модуля `json`
- **Файл:** `src/test/test_learning.py:590`
- **Причина:** Не добавлен `import json` в начало файла теста

#### test_method_signatures
- **Ошибка:** `assert 1 == 2`
- **Описание:** Неверное количество параметров в сигнатуре метода
- **Файл:** `src/test/test_learning.py:712`
- **Причина:** Ожидается 2 параметра (self + memory), но фактически только 1

#### test_method_return_types
- **Ошибка:** `ValueError: current_params не может быть пустым`
- **Описание:** Метод `adjust_parameters` не принимает пустые параметры
- **Файл:** `src/test/test_learning.py:737`
- **Причина:** Тест передает пустые словари, но метод требует валидные параметры

#### test_imports_structure
- **Ошибка:** `AssertionError: assert <class 'learning.learning.LearningEngine'> == LearningEngine`
- **Описание:** Проблема с импортом класса LearningEngine
- **Файл:** `src/test/test_learning.py:892`
- **Причина:** Неправильное сравнение классов из разных модулей

#### test_full_cycle_smoke
- **Ошибка:** `AssertionError: assert 'learning_params' in {...}`
- **Описание:** Ожидается ключ 'learning_params' в словаре параметров
- **Файл:** `src/test/test_learning.py:986`
- **Причина:** Структура данных не соответствует ожиданиям теста

#### test_learning_persistence_across_snapshots
- **Ошибка:** `AssertionError: assert 'learning_params' in {...}`
- **Описание:** Аналогично предыдущей ошибке - отсутствует ключ 'learning_params'
- **Файл:** `src/test/test_learning.py:1216`

#### test_learning_with_large_memory
- **Ошибка:** `assert 50 == 120`
- **Описание:** Ожидается 120 записей в памяти, но фактически 50
- **Файл:** `src/test/test_learning.py:1261`
- **Причина:** Проблема с обработкой большого объема данных в памяти

### 4. Модуль: test_learning_adaptation_integration (3 ошибки)

#### test_learning_interval_constants
- **Ошибка:** `assert 'learning_interval' in source_code`
- **Описание:** Константа `learning_interval` не найдена в исходном коде
- **Файл:** `src/test/test_learning_adaptation_integration.py:111`
- **Причина:** Константа не определена или имеет другое имя

#### test_return_types
- **Ошибка:** `ValueError: current_params не может быть пустым`
- **Описание:** Аналогично ошибке в test_learning
- **Файл:** `src/test/test_learning_adaptation_integration.py:198`

#### test_learning_frequency_in_runtime
- **Ошибка:** `NameError: name 'learning_interval' is not defined`
- **Описание:** Переменная `learning_interval` не определена
- **Файл:** `src/test/test_learning_adaptation_integration.py:450`
- **Причина:** Отсутствует импорт или определение константы

### 5. Модуль: test_mcp_interactive (1 ошибка)

#### test_mcp_functions
- **Ошибка:** `Failed: async def functions are not natively supported`
- **Описание:** Асинхронные функции не поддерживаются без плагина
- **Файл:** `src/test/test_mcp_interactive.py`
- **Причина:** Требуется установка плагина для async (pytest-asyncio, anyio и т.д.)

### 6. Модуль: test_mcp_refresh_index (1 ошибка)

#### test_refresh_index_handles_os_error
- **Ошибка:** `AssertionError: assert ('файловой системе' in ...)`
- **Описание:** Сообщение об ошибке не содержит ожидаемых фраз
- **Файл:** `src/test/test_mcp_refresh_index.py:128`
- **Причина:** Изменился формат сообщений об ошибках

### 7. Модуль: test_mcp_server (21 ошибка)

Все 21 тест имеют одинаковую ошибку:
- **Ошибка:** `Failed: async def functions are not natively supported`
- **Описание:** Асинхронные функции не поддерживаются без плагина pytest
- **Причина:** Требуется установка плагина для async (pytest-asyncio, anyio и т.д.)

**Затронутые тесты:**
- test_search_docs
- test_list_docs
- test_get_doc_content
- test_search_todo
- test_search_docs_and_mode
- test_search_docs_or_mode
- test_search_docs_or_mode_with_quoted_query
- test_search_docs_phrase_mode
- test_tokenize_query_quotes_auto_phrase
- test_tokenize_query_explicit_mode_priority
- test_tokenize_query_empty_query
- test_search_docs_empty_query
- test_search_todo_and_mode
- test_search_todo_or_mode
- test_search_todo_phrase_mode
- test_list_todo
- test_get_todo_content
- test_refresh_index
- test_refresh_index_statistics
- test_refresh_index_timing
- test_mcp_server_init

### 8. Модуль: test_memory (10 ошибок)

#### test_decay_weights_multiple_entries
- **Ошибка:** `AssertionError: assert 0.6383999998545583 <= 0.6174999997137322`
- **Описание:** Веса записей не упорядочены правильно после затухания
- **Файл:** `src/test/test_memory.py:399`
- **Причина:** Проблема с алгоритмом затухания весов

#### test_archive_memory_initialization
- **Ошибка:** `assert 3899 == 0`
- **Описание:** Архив памяти не пуст при инициализации
- **Файл:** `src/test/test_memory.py:433`
- **Причина:** Архив содержит данные из предыдущих тестов (проблема изоляции)

#### test_archive_memory_add_entry
- **Ошибка:** `assert 3900 == 1`
- **Описание:** Размер архива не соответствует ожидаемому после добавления записи
- **Файл:** `src/test/test_memory.py:443`
- **Причина:** Архив не очищается между тестами

#### test_archive_memory_add_entries
- **Ошибка:** `assert 3904 == 5`
- **Описание:** Аналогично предыдущей ошибке
- **Файл:** `src/test/test_memory.py:458`

#### test_archive_memory_get_entries_by_type
- **Ошибка:** `AssertionError: assert 129 == 2`
- **Описание:** Найдено 129 записей вместо ожидаемых 2
- **Файл:** `src/test/test_memory.py:468`
- **Причина:** Архив содержит данные из других тестов

#### test_archive_memory_get_entries_by_significance
- **Ошибка:** `AssertionError: assert 112 == 2`
- **Описание:** Аналогично предыдущей ошибке
- **Файл:** `src/test/test_memory.py:479`

#### test_archive_old_entries_by_age
- **Ошибка:** `assert 3900 == 1`
- **Описание:** Проблема с архивацией по возрасту
- **Файл:** `src/test/test_memory.py:547`

#### test_archive_old_entries_by_weight
- **Ошибка:** `assert 0 == 1`
- **Описание:** Архивация по весу не работает
- **Файл:** `src/test/test_memory.py:569`

#### test_archive_old_entries_by_significance
- **Ошибка:** `assert 0 == 1`
- **Описание:** Архивация по значимости не работает
- **Файл:** `src/test/test_memory.py:594`

#### test_get_statistics_empty
- **Ошибка:** `assert 3901 == 0`
- **Описание:** Статистика показывает непустой архив
- **Файл:** `src/test/test_memory.py:656`

### 9. Модуль: test_monitor (6 ошибок)

Все 6 тестов имеют схожую ошибку:
- **Ошибка:** `FileNotFoundError` или `AssertionError: assert False` (файл не существует)
- **Описание:** Файлы логов не создаются функцией мониторинга
- **Причина:** Функция мониторинга не создает файлы логов или создает их в другом месте

**Затронутые тесты:**
- test_monitor_basic
- test_monitor_with_activated_memory
- test_monitor_without_activated_memory
- test_monitor_multiple_calls
- test_monitor_log_file_append
- test_monitor_all_state_fields

### 10. Модуль: test_performance (4 ошибки)

#### test_event_queue_performance
- **Ошибка:** `AssertionError: assert 100 == 1000`
- **Описание:** Обработано только 100 событий вместо 1000
- **Файл:** `src/test/test_performance.py:98`
- **Причина:** Ограничение размера очереди событий

#### test_self_state_apply_delta_performance
- **Ошибка:** `AssertionError: apply_delta too slow: 3.361s for 10000 operations`
- **Описание:** Операция `apply_delta` слишком медленная (ожидается < 0.5s)
- **Файл:** `src/test/test_performance.py:121`
- **Причина:** Проблемы с производительностью метода

#### test_runtime_loop_ticks_per_second
- **Ошибка:** `AssertionError: Loop too slow: 68.8 ticks/sec (expected >= 100)`
- **Описание:** Цикл выполнения слишком медленный
- **Файл:** `src/test/test_performance.py:155`
- **Причина:** Неоптимальная реализация runtime loop

#### test_state_snapshot_performance
- **Ошибка:** `AssertionError: Snapshot save too slow: 8.959s for 100 snapshots`
- **Описание:** Сохранение снимков состояния слишком медленное (ожидается < 1.0s)
- **Файл:** `src/test/test_performance.py:217`
- **Причина:** Проблемы с производительностью сериализации

### 11. Модуль: test_property_based (1 ошибка)

#### test_memory_append_idempotent
- **Ошибка:** `AssertionError: assert 1 == 2`
- **Описание:** Операция добавления в память не является идемпотентной
- **Файл:** `src/test/test_property_based.py:176`
- **Причина:** Повторное добавление той же записи увеличивает размер памяти

### 12. Модуль: test_state (15 ошибок)

#### test_save_snapshot
- **Ошибка:** `AssertionError: assert False` (файл не существует)
- **Описание:** Файл снимка состояния не создается
- **Файл:** `src/test/test_state.py:246`
- **Причина:** Функция сохранения не создает файл или создает в другом месте

#### test_load_snapshot
- **Ошибка:** `AttributeError: Cannot modify immutable field 'life_id' after initialization`
- **Описание:** Нельзя изменить поле `life_id` после инициализации
- **Файл:** `src/test/test_state.py:271`
- **Причина:** Поле помечено как неизменяемое

#### test_load_latest_snapshot
- **Ошибка:** `AssertionError: assert 200 == 30`
- **Описание:** Загружен неправильный снимок (200 тиков вместо 30)
- **Файл:** `src/test/test_state.py:309`
- **Причина:** Неправильная логика выбора последнего снимка

#### test_load_latest_snapshot_not_found
- **Ошибка:** `Failed: DID NOT RAISE <class 'FileNotFoundError'>`
- **Описание:** Исключение не возникает при отсутствии снимков
- **Файл:** `src/test/test_state.py:315`
- **Причина:** Отсутствует обработка случая отсутствия файлов

#### test_energy_validation_invalid
- **Ошибка:** `Failed: DID NOT RAISE <class 'ValueError'>`
- **Описание:** Валидация не работает для недопустимых значений energy
- **Файл:** `src/test/test_state.py:375`
- **Причина:** Отсутствует валидация входных данных

#### test_integrity_validation_invalid
- **Ошибка:** `Failed: DID NOT RAISE <class 'ValueError'>`
- **Описание:** Аналогично предыдущей ошибке для integrity
- **Файл:** `src/test/test_state.py:393`

#### test_stability_validation_invalid
- **Ошибка:** `Failed: DID NOT RAISE <class 'ValueError'>`
- **Описание:** Аналогично для stability
- **Файл:** `src/test/test_state.py:411`

#### test_fatigue_validation
- **Ошибка:** `Failed: DID NOT RAISE <class 'ValueError'>`
- **Описание:** Аналогично для fatigue
- **Файл:** `src/test/test_state.py:423`

#### test_tension_validation
- **Ошибка:** `Failed: DID NOT RAISE <class 'ValueError'>`
- **Описание:** Аналогично для tension
- **Файл:** `src/test/test_state.py:433`

#### test_age_validation
- **Ошибка:** `Failed: DID NOT RAISE <class 'ValueError'>`
- **Описание:** Аналогично для age
- **Файл:** `src/test/test_state.py:443`

#### test_update_energy
- **Ошибка:** `Failed: DID NOT RAISE <class 'ValueError'>`
- **Описание:** Метод не валидирует входные данные
- **Файл:** `src/test/test_state.py:503`

#### test_update_integrity
- **Ошибка:** `Failed: DID NOT RAISE <class 'ValueError'>`
- **Описание:** Аналогично для integrity
- **Файл:** `src/test/test_state.py:513`

#### test_update_stability
- **Ошибка:** `Failed: DID NOT RAISE <class 'ValueError'>`
- **Описание:** Аналогично для stability
- **Файл:** `src/test/test_state.py:523`

#### test_logging_enabled
- **Ошибка:** `AssertionError: assert False` (файл не существует)
- **Описание:** Файл логов изменений состояния не создается
- **Файл:** `src/test/test_state.py:678`
- **Причина:** Логирование не работает или файл создается в другом месте

#### test_get_change_history
- **Ошибка:** `assert 0 >= 3`
- **Описание:** История изменений пуста
- **Файл:** `src/test/test_state.py:710`
- **Причина:** История изменений не записывается

## Рекомендации по исправлению

### Критические проблемы

1. **Асинхронные тесты (22 теста):**
   - Установить плагин `pytest-asyncio` или `anyio`
   - Добавить декораторы `@pytest.mark.asyncio` для async тестов

2. **Изоляция тестов памяти:**
   - Обеспечить очистку архива памяти между тестами
   - Использовать фикстуры pytest для изоляции состояния

3. **Валидация данных:**
   - Добавить валидацию входных параметров в методы SelfState
   - Реализовать проверки диапазонов значений

### Важные проблемы

4. **Производительность:**
   - Оптимизировать метод `apply_delta`
   - Улучшить производительность runtime loop
   - Оптимизировать сохранение снимков состояния

5. **Логирование:**
   - Исправить создание файлов логов в функции мониторинга
   - Обеспечить запись истории изменений состояния

6. **Архивация памяти:**
   - Исправить алгоритм архивации по весу и значимости
   - Обеспечить правильную работу затухания весов

### Средние проблемы

7. **Learning и Adaptation:**
   - Исправить структуру параметров learning_params
   - Добавить недостающие константы (learning_interval)
   - Исправить импорты и сигнатуры методов

8. **Снимки состояния:**
   - Исправить создание файлов снимков
   - Улучшить логику выбора последнего снимка
   - Добавить обработку отсутствующих файлов

9. **Деградация:**
   - Исправить логику деактивации флага active
   - Улучшить цикл выполнения для длительных тестов

## Заключение

Тестирование выявило **74 проваленных теста** из 608, что составляет **12.2%** от общего количества. Большинство ошибок связано с:

1. Отсутствием поддержки асинхронных тестов (22 теста)
2. Проблемами изоляции тестов (архив памяти)
3. Отсутствием валидации входных данных (15 тестов)
4. Проблемами с логированием и файлами (9 тестов)
5. Проблемами производительности (4 теста)

**87.8% тестов прошли успешно**, что указывает на стабильность основной функциональности системы. Требуется исправление указанных проблем для достижения 100% прохождения тестов.

---

**Тестирование завершено!**
