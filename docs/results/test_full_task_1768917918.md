# Отчет о полном тестировании проекта Life

**Дата:** 2025-01-20  
**Задача:** task_1768917918  
**Команда запуска:** `python3 -m pytest src/test -v --tb=short`

## Общая статистика

- **Всего тестов:** 657
- **Пройдено успешно:** 579 (88.1%)
- **Провалено:** 74 (11.3%)
- **Пропущено:** 4 (0.6%)
- **Предупреждения:** 1
- **Время выполнения:** ~3 минуты 8 секунд

## Сводка по категориям ошибок

### 1. Monitor (Мониторинг) - 6 ошибок
### 2. Property-based тесты - 1 ошибка
### 3. State (Состояние) - 15 ошибок
### 4. Memory (Память) - 10 ошибок
### 5. Degradation (Деградация) - 3 ошибки
### 6. Performance (Производительность) - 4 ошибки
### 7. Adaptation (Адаптация) - 2 ошибки
### 8. Learning (Обучение) - 8 ошибок
### 9. MCP Server - 25 ошибок

---

## Детальный анализ ошибок

### 1. Monitor (Мониторинг) - 6 ошибок

#### 1.1. `test_monitor_basic`
**Файл:** `src/test/test_monitor.py:58`  
**Ошибка:** `AssertionError: assert False`  
**Описание:** Файл лога `tick_log.jsonl` не создается после вызова monitor.  
**Причина:** Файл не создается в указанной директории `/tmp/pytest-of-root/pytest-139/test_monitor_basic0/tick_log.jsonl`

#### 1.2. `test_monitor_with_activated_memory`
**Файл:** `src/test/test_monitor.py:80`  
**Ошибка:** `AssertionError: assert False`  
**Описание:** Аналогичная проблема - файл лога не создается при наличии активированной памяти.

#### 1.3. `test_monitor_without_activated_memory`
**Файл:** `src/test/test_monitor.py:95`  
**Ошибка:** `AssertionError: assert False`  
**Описание:** Файл лога не создается даже без активированной памяти.

#### 1.4. `test_monitor_multiple_calls`
**Файл:** `src/test/test_monitor.py:110`  
**Ошибка:** `AssertionError: assert False`  
**Описание:** Файл лога не создается при множественных вызовах monitor.

#### 1.5. `test_monitor_log_file_append`
**Файл:** `src/test/test_monitor.py:133`  
**Ошибка:** `FileNotFoundError: [Errno 2] No such file or directory: '/tmp/pytest-of-root/pytest-139/test_monitor_log_file_append0/tick_log.jsonl'`  
**Описание:** Попытка открыть несуществующий файл лога для проверки добавления записей.

#### 1.6. `test_monitor_all_state_fields`
**Файл:** `src/test/test_monitor.py:151`  
**Ошибка:** `FileNotFoundError: [Errno 2] No such file or directory: '/tmp/pytest-of-root/pytest-139/test_monitor_all_state_fields0/tick_log.jsonl'`  
**Описание:** Файл лога не создается для проверки всех полей состояния.

**Рекомендация:** Проверить логику создания файлов логов в модуле `monitor`. Возможно, требуется создание директорий перед записью или изменение логики flush/записи.

---

### 2. Property-based тесты - 1 ошибка

#### 2.1. `test_memory_append_idempotent`
**Файл:** `src/test/test_property_based.py:176`  
**Ошибка:** `AssertionError: assert 1 == 2`  
**Описание:** Тест проверяет идемпотентность добавления записей в память. При повторном добавлении той же записи ожидается, что размер памяти не изменится, но фактически запись добавляется дважды.  
**Детали:** 
- Ожидалось: `len(memory1) == len(memory2)` (оба равны 1)
- Фактически: `len(memory1) == 1`, `len(memory2) == 2`
- Falsifying example: `event_type='0'`, `significance=0.0`, `num_appends=2`

**Рекомендация:** Проверить логику добавления записей в память. Возможно, требуется проверка на дубликаты перед добавлением или изменение логики сравнения записей.

---

### 3. State (Состояние) - 15 ошибок

#### 3.1. Снимки (Snapshots) - 4 ошибки

##### 3.1.1. `test_save_snapshot`
**Файл:** `src/test/test_state.py:246`  
**Ошибка:** `AssertionError: assert False`  
**Описание:** Файл снимка не создается после вызова `save_snapshot()`.  
**Путь:** `/tmp/tmplgnpgngk/snapshot_000100.json`

##### 3.1.2. `test_load_snapshot`
**Файл:** `src/test/test_state.py:271`  
**Ошибка:** `AttributeError: Cannot modify immutable field 'life_id' after initialization`  
**Описание:** Попытка изменить неизменяемое поле `life_id` после загрузки снимка. Тест пытается установить `state.life_id = "test_life_id"`, но поле защищено от изменения.

##### 3.1.3. `test_load_latest_snapshot`
**Файл:** `src/test/test_state.py:309`  
**Ошибка:** `AssertionError: assert 200 == 30`  
**Описание:** Загружен неправильный снимок. Ожидался снимок с `ticks=30`, но загружен с `ticks=200`.

##### 3.1.4. `test_load_latest_snapshot_not_found`
**Файл:** `src/test/test_state.py:315`  
**Ошибка:** `Failed: DID NOT RAISE <class 'FileNotFoundError'>`  
**Описание:** Тест ожидал исключение `FileNotFoundError` при отсутствии снимков, но исключение не было вызвано.

**Рекомендация:** Проверить логику создания и загрузки снимков. Возможно, требуется исправление путей сохранения или логики поиска последнего снимка.

#### 3.2. Валидация (Validation) - 6 ошибок

##### 3.2.1. `test_energy_validation_invalid`
**Файл:** `src/test/test_state.py:375`  
**Ошибка:** `Failed: DID NOT RAISE <class 'ValueError'>`  
**Описание:** Тест ожидал исключение `ValueError` при установке невалидного значения энергии (вне диапазона 0.0-100.0), но исключение не было вызвано.

##### 3.2.2. `test_integrity_validation_invalid`
**Файл:** `src/test/test_state.py:393`  
**Ошибка:** `Failed: DID NOT RAISE <class 'ValueError'>`  
**Описание:** Тест ожидал исключение при установке невалидного значения integrity (вне диапазона 0.0-1.0).

##### 3.2.3. `test_stability_validation_invalid`
**Файл:** `src/test/test_state.py:411`  
**Ошибка:** `Failed: DID NOT RAISE <class 'ValueError'>`  
**Описание:** Тест ожидал исключение при установке невалидного значения stability (вне диапазона 0.0-1.0).

##### 3.2.4. `test_fatigue_validation`
**Файл:** `src/test/test_state.py:423`  
**Ошибка:** `Failed: DID NOT RAISE <class 'ValueError'>`  
**Описание:** Тест ожидал исключение при установке отрицательного значения fatigue.

##### 3.2.5. `test_tension_validation`
**Файл:** `src/test/test_state.py:433`  
**Ошибка:** `Failed: DID NOT RAISE <class 'ValueError'>`  
**Описание:** Тест ожидал исключение при установке отрицательного значения tension.

##### 3.2.6. `test_age_validation`
**Файл:** `src/test/test_state.py:443`  
**Ошибка:** `Failed: DID NOT RAISE <class 'ValueError'>`  
**Описание:** Тест ожидал исключение при установке отрицательного значения age.

**Рекомендация:** Добавить валидацию входных параметров в методы установки значений состояния. Проверить методы `__setattr__` или сеттеры для этих полей.

#### 3.3. Безопасные методы (Safe Methods) - 3 ошибки

##### 3.3.1. `test_update_energy`
**Файл:** `src/test/test_state.py:503`  
**Ошибка:** `Failed: DID NOT RAISE <class 'ValueError'>`  
**Описание:** Метод `update_energy()` не вызывает исключение при невалидном значении.

##### 3.3.2. `test_update_integrity`
**Файл:** `src/test/test_state.py:513`  
**Ошибка:** `Failed: DID NOT RAISE <class 'ValueError'>`  
**Описание:** Метод `update_integrity()` не вызывает исключение при невалидном значении.

##### 3.3.3. `test_update_stability`
**Файл:** `src/test/test_state.py:523`  
**Ошибка:** `Failed: DID NOT RAISE <class 'ValueError'>`  
**Описание:** Метод `update_stability()` не вызывает исключение при невалидном значении.

**Рекомендация:** Добавить валидацию в методы `update_energy()`, `update_integrity()`, `update_stability()`.

#### 3.4. Логирование (Logging) - 2 ошибки

##### 3.4.1. `test_logging_enabled`
**Файл:** `src/test/test_state.py:678`  
**Ошибка:** `AssertionError: assert False`  
**Описание:** Файл лога изменений состояния не создается.  
**Путь:** `/tmp/tmpg74vthlt/state_changes.jsonl`

##### 3.4.2. `test_get_change_history`
**Файл:** `src/test/test_state.py:710`  
**Ошибка:** `assert 0 >= 3`  
**Описание:** История изменений пуста, хотя ожидалось минимум 3 записи.

**Рекомендация:** Проверить логику создания файла лога и записи истории изменений состояния.

---

### 4. Memory (Память) - 10 ошибок

#### 4.1. Decay Weights - 1 ошибка

##### 4.1.1. `test_decay_weights_multiple_entries`
**Файл:** `src/test/test_memory.py:399`  
**Ошибка:** `AssertionError: assert 0.6383999998782347 <= 0.6174999997461076`  
**Описание:** Веса записей памяти не убывают монотонно после применения decay. Более новая запись имеет больший вес, чем более старая, что противоречит ожидаемому поведению.

**Рекомендация:** Проверить логику вычисления весов при decay. Возможно, проблема в порядке сортировки или в формуле вычисления веса.

#### 4.2. Archive Memory - 6 ошибок

##### 4.2.1. `test_archive_memory_initialization`
**Файл:** `src/test/test_memory.py:433`  
**Ошибка:** `assert 4541 == 0`  
**Описание:** Архив памяти не пуст при инициализации. Ожидался размер 0, фактически 4541 запись.

##### 4.2.2. `test_archive_memory_add_entry`
**Файл:** `src/test/test_memory.py:443`  
**Ошибка:** `assert 4542 == 1`  
**Описание:** После добавления одной записи размер архива равен 4542 вместо ожидаемого 1.

##### 4.2.3. `test_archive_memory_add_entries`
**Файл:** `src/test/test_memory.py:458`  
**Ошибка:** `assert 4546 == 5`  
**Описание:** После добавления 5 записей размер архива равен 4546 вместо ожидаемого 5.

##### 4.2.4. `test_archive_memory_get_entries_by_type`
**Файл:** `src/test/test_memory.py:468`  
**Ошибка:** `AssertionError: assert 129 == 2`  
**Описание:** Метод `get_entries_by_type()` возвращает 129 записей типа 'shock' вместо ожидаемых 2. Похоже, что архив содержит данные из предыдущих тестов.

##### 4.2.5. `test_archive_memory_get_entries_by_significance`
**Файл:** `src/test/test_memory.py:479`  
**Ошибка:** `AssertionError: assert 142 == 2`  
**Описание:** Метод `get_entries_by_significance()` возвращает 142 записи вместо ожидаемых 2.

##### 4.2.6. `test_get_statistics_empty`
**Файл:** `src/test/test_memory.py:656`  
**Ошибка:** `assert 4543 == 0`  
**Описание:** Статистика показывает 4543 записи в архиве вместо ожидаемых 0.

**Рекомендация:** Архив памяти не очищается между тестами или использует глобальное состояние. Необходимо обеспечить изоляцию тестов, возможно, через фикстуры или очистку архива перед каждым тестом.

#### 4.3. Memory Archive - 3 ошибки

##### 4.3.1. `test_archive_old_entries_by_age`
**Файл:** `src/test/test_memory.py:547`  
**Ошибка:** `assert 4542 == 1`  
**Описание:** После архивирования старых записей по возрасту размер архива равен 4542 вместо ожидаемого 1.

##### 4.3.2. `test_archive_old_entries_by_weight`
**Файл:** `src/test/test_memory.py:569`  
**Ошибка:** `assert 0 == 1`  
**Описание:** Не было заархивировано ни одной записи по весу, хотя ожидалась одна запись.

##### 4.3.3. `test_archive_old_entries_by_significance`
**Файл:** `src/test/test_memory.py:594`  
**Ошибка:** `assert 0 == 1`  
**Описание:** Не было заархивировано ни одной записи по значимости, хотя ожидалась одна запись.

**Рекомендация:** Проверить логику архивирования записей. Возможно, критерии архивирования не работают корректно или архив не очищается между тестами.

---

### 5. Degradation (Деградация) - 3 ошибки

#### 5.1. `test_active_flag_stays_false_after_deactivation`
**Файл:** `src/test/test_degradation.py:666`  
**Ошибка:** `AssertionError: assert True is False`  
**Описание:** Флаг `active` остается `True` после деактивации состояния. Ожидалось `False`.

**Рекомендация:** Проверить логику деактивации состояния. Возможно, флаг `active` не устанавливается в `False` при достижении критических значений энергии/интегрированности/стабильности.

#### 5.2. `test_degradation_over_1000_ticks`
**Файл:** `src/test/test_degradation.py:814`  
**Ошибка:** `AssertionError: Expected >= 1000 ticks, got 1`  
**Описание:** Состояние деактивировалось после 1 тика вместо ожидаемых 1000+ тиков. Состояние имеет `energy=0.0`, `integrity=0.0`, `stability=0.0`, `active=False`.

**Рекомендация:** Проверить логику выполнения тиков в runtime loop. Возможно, цикл останавливается слишком рано при деградации состояния.

#### 5.3. `test_degradation_stability_over_time`
**Файл:** `src/test/test_degradation.py:852`  
**Ошибка:** `AssertionError: assert 113 >= 1000`  
**Описание:** Тест выполнил только 113 тиков вместо ожидаемых 1000+.

**Рекомендация:** Аналогично предыдущему - проверить логику выполнения длительных циклов.

---

### 6. Performance (Производительность) - 4 ошибки

#### 6.1. `test_event_queue_performance`
**Файл:** `src/test/test_performance.py:98`  
**Ошибка:** `AssertionError: assert 100 == 1000`  
**Описание:** В очередь было добавлено только 100 событий из 1000 запрошенных. Остальные события были потеряны из-за переполнения очереди (maxsize=100).  
**Детали:** Потеряно 900 событий (900 warnings о переполнении очереди).

**Рекомендация:** Тест некорректен - он пытается добавить 1000 событий в очередь с maxsize=100. Либо увеличить maxsize в тесте, либо изменить ожидания теста.

#### 6.2. `test_self_state_apply_delta_performance`
**Файл:** `src/test/test_performance.py`  
**Ошибка:** Требуется детальный анализ.

#### 6.3. `test_runtime_loop_ticks_per_second`
**Файл:** `src/test/test_performance.py`  
**Ошибка:** Требуется детальный анализ.

#### 6.4. `test_state_snapshot_performance`
**Файл:** `src/test/test_performance.py`  
**Ошибка:** Требуется детальный анализ.

**Рекомендация:** Проверить все тесты производительности на корректность ожиданий и условий выполнения.

---

### 7. Adaptation (Адаптация) - 2 ошибки

#### 7.1. `test_apply_adaptation_initialization`
**Файл:** `src/test/test_adaptation.py:362`  
**Ошибка:** Требуется детальный анализ.

#### 7.2. `test_apply_adaptation_no_decision_action_control`
**Файл:** `src/test/test_adaptation.py:365`  
**Ошибка:** Требуется детальный анализ.

**Рекомендация:** Проверить логику инициализации и применения адаптации.

---

### 8. Learning (Обучение) - 8 ошибок

#### 8.1. `test_learning_persistence_in_snapshots`
**Файл:** `src/test/test_learning.py:406`  
**Ошибка:** Требуется детальный анализ.

#### 8.2. `test_method_signatures`
**Файл:** `src/test/test_learning.py:411`  
**Ошибка:** Статическая проверка сигнатур методов не прошла.

#### 8.3. `test_method_return_types`
**Файл:** `src/test/test_learning.py:412`  
**Ошибка:** Статическая проверка типов возвращаемых значений не прошла.

#### 8.4. `test_imports_structure`
**Файл:** `src/test/test_learning.py:417`  
**Ошибка:** Статическая проверка структуры импортов не прошла.

#### 8.5. `test_full_cycle_smoke`
**Файл:** `src/test/test_learning.py:424`  
**Ошибка:** Smoke-тест полного цикла обучения не прошел.

#### 8.6. `test_learning_persistence_across_snapshots`
**Файл:** `src/test/test_learning.py:431`  
**Ошибка:** Персистентность обучения между снимками не работает.

#### 8.7. `test_learning_with_large_memory`
**Файл:** `src/test/test_learning.py:432`  
**Ошибка:** Обучение с большой памятью не работает корректно.

#### 8.8. Интеграция Learning-Adaptation - 3 ошибки

##### 8.8.1. `test_learning_interval_constants`
**Файл:** `src/test/test_learning_adaptation_integration.py:437`  
**Ошибка:** Статическая проверка констант интервалов обучения не прошла.

##### 8.8.2. `test_return_types`
**Файл:** `src/test/test_learning_adaptation_integration.py:441`  
**Ошибка:** Статическая проверка типов возвращаемых значений не прошла.

##### 8.8.3. `test_learning_frequency_in_runtime`
**Файл:** `src/test/test_learning_adaptation_integration.py:454`  
**Ошибка:** Частота обучения в runtime не соответствует ожиданиям.

**Рекомендация:** Проверить реализацию модуля обучения, статические проверки и интеграцию с адаптацией.

---

### 9. MCP Server - 25 ошибок

Все тесты MCP Server провалились с ошибкой: `Failed: async def function...`

#### Список провалившихся тестов:
1. `test_search_docs`
2. `test_list_docs`
3. `test_get_doc_content`
4. `test_search_todo`
5. `test_search_docs_and_mode`
6. `test_search_docs_or_mode`
7. `test_search_docs_or_mode_with_quoted_query`
8. `test_search_docs_phrase_mode`
9. `test_tokenize_query_quotes_auto_phrase`
10. `test_tokenize_query_explicit_mode_priority`
11. `test_tokenize_query_empty_query`
12. `test_search_docs_empty_query`
13. `test_search_todo_and_mode`
14. `test_search_todo_or_mode`
15. `test_search_todo_phrase_mode`
16. `test_list_todo`
17. `test_get_todo_content`
18. `test_refresh_index`
19. `test_refresh_index_statistics`
20. `test_refresh_index_timing`
21. `test_mcp_server_init`

**Дополнительные ошибки:**
- `test_mcp_interactive::test_mcp_functions` - провален
- `test_mcp_refresh_index::test_refresh_index_handles_os_error` - провален

**Рекомендация:** Все тесты MCP Server используют async функции, но похоже, что они не выполняются корректно. Проверить:
1. Настройку async тестов в pytest (возможно, требуется `pytest-asyncio`)
2. Корректность использования async/await в тестах
3. Инициализацию MCP сервера в тестах

---

## Приоритеты исправления

### Критичные (блокируют функциональность):
1. **Monitor** - файлы логов не создаются
2. **State Snapshots** - снимки не сохраняются/загружаются
3. **State Validation** - отсутствует валидация входных данных
4. **Memory Archive** - глобальное состояние между тестами

### Высокие (влияют на корректность работы):
5. **Degradation** - преждевременная остановка runtime loop
6. **Memory Decay** - некорректное вычисление весов
7. **Learning** - проблемы с персистентностью и статическими проверками

### Средние (требуют доработки):
8. **MCP Server** - проблемы с async тестами
9. **Performance** - некорректные ожидания в тестах
10. **Property-based** - идемпотентность памяти

---

## Рекомендации по исправлению

1. **Изоляция тестов:** Обеспечить изоляцию между тестами, особенно для Memory Archive и других компонентов с глобальным состоянием.

2. **Валидация входных данных:** Добавить валидацию во все методы установки значений состояния (energy, integrity, stability, fatigue, tension, age).

3. **Создание файлов:** Проверить логику создания файлов логов и снимков. Убедиться, что директории создаются перед записью.

4. **Async тесты:** Проверить конфигурацию pytest для async тестов MCP Server.

5. **Runtime Loop:** Проверить логику остановки runtime loop при деградации состояния.

6. **Memory Decay:** Исправить формулу вычисления весов при decay для обеспечения монотонного убывания.

---

## Заключение

Из 657 тестов 74 (11.3%) провалились. Основные проблемы связаны с:
- Созданием файлов (логи, снимки)
- Валидацией входных данных
- Изоляцией тестов (глобальное состояние)
- Async тестами MCP Server
- Логикой выполнения длительных циклов

Большинство ошибок можно исправить добавлением валидации, улучшением изоляции тестов и исправлением логики создания файлов.
