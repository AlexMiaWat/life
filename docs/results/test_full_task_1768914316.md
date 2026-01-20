# Отчет о полном тестировании - 1768914316

## Общая статистика тестирования

**Дата и время:** 20 января 2026 г.
**Общее количество тестов:** 627
**Пройденные тесты:** 549
**Проваленные тесты:** 74
**Пропущенные тесты:** 4
**Предупреждения:** 1

## Проваленные тесты и ошибки

### 1. Модуль адаптации (test_adaptation.py) - 2 проваленных теста

**Проблемы:**
1. Несоответствие ожидаемого значения параметра noise в адаптации
2. Отсутствие ожидаемого исключения ValueError

**Детали ошибок:**
```
AssertionError: assert 0.21000000000000002 == 0.3
ValueError: DID NOT RAISE <class 'ValueError'>
```

**Затронутые тесты:**
- `test_apply_adaptation_initialization`
- `test_apply_adaptation_no_decision_action_control`

**Анализ:** Проблемы с логикой инициализации параметров адаптации и обработкой исключений.

### 2. Модуль деградации (test_degradation.py) - 3 проваленных теста

**Проблемы:**
1. Флаг active остается True после деактивации
2. Недостаточное количество тиков в длительном тестировании деградации
3. Недостаточное количество тиков в тестировании стабильности

**Детали ошибок:**
```
AssertionError: assert True is False
AssertionError: assert 1 >= 1000
AssertionError: assert 108 >= 1000
```

**Затронутые тесты:**
- `test_active_flag_stays_false_after_deactivation`
- `test_degradation_over_1000_ticks`
- `test_degradation_stability_over_time`

**Анализ:** Проблемы с управлением жизненным циклом и логикой деградации состояния.

### 3. Модуль обучения (test_learning.py) - 7 проваленных тестов

**Проблемы:**
1. Отсутствие импорта json
2. Неправильное количество параметров метода
3. ValueError при пустых параметрах
4. Несоответствие структуры импортов
5. Отсутствие ключа 'learning_params' в состоянии
6. Несоответствие ожидаемого количества записей
7. Отсутствие ключа 'learning_params' в загруженном состоянии

**Детали ошибок:**
```
NameError: name 'json' is not defined
AssertionError: assert 1 == 2
ValueError: current_params не может быть пустым
AssertionError: assert <class 'learning.learning.LearningEngine'> == LearningEngine
AssertionError: assert 'learning_params' in {...}
AssertionError: assert 50 == 120
AssertionError: assert 'learning_params' in {...}
```

**Затронутые тесты:**
- `test_learning_persistence_in_snapshots`
- `test_method_signatures`
- `test_method_return_types`
- `test_imports_structure`
- `test_full_cycle_smoke`
- `test_learning_persistence_across_snapshots`
- `test_learning_with_large_memory`

**Анализ:** Критические проблемы в системе обучения, включая сериализацию, сигнатуры методов и структуру данных.

### 4. Модуль интеграции обучения и адаптации (test_learning_adaptation_integration.py) - 3 проваленных теста

**Проблемы:**
1. Отсутствие константы learning_interval в коде
2. ValueError при пустых параметрах
3. NameError для переменной learning_interval

**Детали ошибок:**
```
AssertionError: assert 'learning_interval' in '...'
ValueError: current_params не может быть пустым
NameError: name 'learning_interval' is not defined
```

**Затронутые тесты:**
- `test_learning_interval_constants`
- `test_return_types`
- `test_learning_frequency_in_runtime`

**Анализ:** Проблемы с константами и интеграцией между модулями обучения и адаптации.

### 5. Модуль MCP интерактив (test_mcp_interactive.py) - 1 проваленный тест

**Проблема:** Отсутствие поддержки асинхронных функций в pytest

**Детали ошибки:**
```
Failed: async def functions are not natively supported.
You need to install a suitable plugin for your async framework, for example:
  - anyio
  - pytest-asyncio
  - pytest-tornasync
  - pytest-trio
  - pytest-twisted
```

**Затронутый тест:** `test_mcp_functions`

**Анализ:** Необходима установка плагина для поддержки асинхронных тестов.

### 6. Модуль MCP обновления индекса (test_mcp_refresh_index.py) - 1 проваленный тест

**Проблема:** Неправильная проверка сообщения об ошибке файловой системы

**Детали ошибки:**
```
AssertionError: assert ('файловой системе' in '...' or 'доступа' in '...')
```

**Затронутый тест:** `test_refresh_index_handles_os_error`

**Анализ:** Локализация текста ошибки не соответствует ожидаемому.

### 7. Модуль MCP сервера (test_mcp_server.py) - 21 проваленный тест

**Проблема:** Отсутствие поддержки асинхронных функций во всех тестах

**Детали ошибки:**
```
Failed: async def functions are not natively supported.
You need to install a suitable plugin for your async framework, for example:
  - anyio
  - pytest-asyncio
  - pytest-tornasync
  - pytest-trio
  - pytest-twisted
```

**Затронутые тесты:** Все тесты модуля (21 тест)

**Анализ:** Все тесты MCP сервера требуют поддержки асинхронных функций.

### 8. Модуль памяти (test_memory.py) - 10 проваленных тестов

**Проблемы:**
1. Неправильный порядок весов при decay
2. Неправильный размер архивной памяти после инициализации
3. Неправильный размер после добавления записи
4. Неправильный размер после добавления нескольких записей
5. Неправильное количество записей по типу события
6. Неправильное количество записей по значимости
7. Неправильный размер архивной памяти
8. Отсутствие архивированных записей
9. Отсутствие архивированных записей по значимости
10. Неправильная статистика пустой памяти

**Детали ошибок:**
```
AssertionError: assert 0.6383999998545583 <= 0.6174999997137322
AssertionError: assert 3899 == 0
AssertionError: assert 3900 == 1
AssertionError: assert 3904 == 5
AssertionError: assert 129 == 2
AssertionError: assert 112 == 2
AssertionError: assert 3900 == 1
AssertionError: assert 0 == 1
AssertionError: assert 0 == 1
AssertionError: assert 3901 == 0
```

**Затронутые тесты:**
- `test_decay_weights_multiple_entries`
- `test_archive_memory_initialization`
- `test_archive_memory_add_entry`
- `test_archive_memory_add_entries`
- `test_archive_memory_get_entries_by_type`
- `test_archive_memory_get_entries_by_significance`
- `test_archive_old_entries_by_age`
- `test_archive_old_entries_by_weight`
- `test_archive_old_entries_by_significance`
- `test_get_statistics_empty`

**Анализ:** Критические проблемы с логикой архивной памяти и decay weights.

### 9. Модуль мониторинга (test_monitor.py) - 6 проваленных тестов

**Проблема:** Лог-файлы не создаются при вызове функции monitor()

**Детали ошибки:**
```
AssertionError: assert False
where False = exists()
where exists = PosixPath('/tmp/pytest-of-root/pytest-*/tick_log.jsonl').exists
```

**Затронутые тесты:**
- `test_monitor_basic`
- `test_monitor_with_activated_memory`
- `test_monitor_without_activated_memory`
- `test_monitor_multiple_calls`
- `test_monitor_log_file_append`
- `test_monitor_all_state_fields`

**Анализ:** Функция monitor() не создает ожидаемые лог-файлы.

### 10. Модуль производительности (test_performance.py) - 4 проваленных теста

**Проблемы:**
1. Недостаточное количество событий в очереди
2. Слишком медленная операция apply_delta
3. Недостаточная скорость тиков в секунду
4. Слишком медленное сохранение снимков

**Детали ошибок:**
```
AssertionError: assert 100 == 1000
AssertionError: apply_delta too slow: 3.361s for 10000 operations
AssertionError: Loop too slow: 68.8 ticks/sec (expected >= 100)
AssertionError: Snapshot save too slow: 8.959s for 100 snapshots
```

**Затронутые тесты:**
- `test_event_queue_performance`
- `test_self_state_apply_delta_performance`
- `test_runtime_loop_ticks_per_second`
- `test_state_snapshot_performance`

**Анализ:** Критические проблемы с производительностью системы.

### 11. Модуль property-based тестирования (test_property_based.py) - 1 проваленный тест

**Проблема:** Нарушение идемпотентности при добавлении записей в память

**Детали ошибки:**
```
AssertionError: assert 1 == 2
```

**Затронутый тест:** `test_memory_append_idempotent`

**Анализ:** Повторное добавление одинаковых записей приводит к дублированию вместо замены.

### 12. Модуль состояния (test_state.py) - 15 проваленных тестов

**Проблемы:**
1. Снимок состояния не сохраняется
2. Невозможно изменить неизменяемое поле life_id
3. Неожиданное количество тиков в загруженном состоянии
4. FileNotFoundError при загрузке несуществующего снимка
5. Отсутствие валидации для некорректных значений энергии
6. Отсутствие валидации для некорректных значений integrity
7. Отсутствие валидации для некорректных значений stability
8. Отсутствие валидации для некорректных значений fatigue
9. Отсутствие валидации для некорректных значений tension
10. Отсутствие валидации для некорректных значений age
11. Отсутствие исключения при установке недопустимой энергии
12. Отсутствие исключения при установке недопустимой integrity
13. Отсутствие исключения при установке недопустимой stability
14. Лог-файл изменений состояния не создается
15. Пустая история изменений состояния

**Детали ошибок:**
```
AssertionError: assert False
AttributeError: Cannot modify immutable field 'life_id' after initialization
AssertionError: assert 200 == 30
Failed: DID NOT RAISE <class 'FileNotFoundError'>
Failed: DID NOT RAISE <class 'ValueError'>
(и другие аналогичные ошибки валидации)
AssertionError: assert False
AssertionError: assert 0 >= 3
```

**Затронутые тесты:**
- `test_save_snapshot`
- `test_load_snapshot`
- `test_load_latest_snapshot`
- `test_load_latest_snapshot_not_found`
- `test_energy_validation_invalid`
- `test_integrity_validation_invalid`
- `test_stability_validation_invalid`
- `test_fatigue_validation`
- `test_tension_validation`
- `test_age_validation`
- `test_update_energy`
- `test_update_integrity`
- `test_update_stability`
- `test_logging_enabled`
- `test_get_change_history`

**Анализ:** Критические проблемы с системой состояния, включая сохранение, загрузку, валидацию и логирование.

## Пропущенные тесты

**4 теста пропущены** - информация о пропущенных тестах отсутствует в выводе pytest.

## Предупреждения

**1 предупреждение** - информация о предупреждениях отсутствует в выводе pytest.

## Рекомендации по исправлению

### 1. Исправить систему обучения
- Добавить импорт json в соответствующие модули
- Исправить сигнатуры методов LearningEngine
- Реализовать правильную обработку пустых параметров
- Исправить структуру данных learning_params
- Добавить константу learning_interval

### 2. Исправить систему памяти
- Исправить логику decay weights
- Переработать ArchiveMemory для корректного учета размера
- Исправить логику архивирования записей
- Реализовать идемпотентность операций добавления

### 3. Исправить систему состояния
- Реализовать сохранение снимков состояния
- Убрать ограничения на изменение life_id или изменить логику тестирования
- Исправить логику загрузки последних снимков
- Реализовать валидацию параметров состояния
- Исправить систему логирования изменений

### 4. Исправить систему мониторинга
- Реализовать создание лог-файлов в функции monitor()
- Проверить пути к файлам и права доступа

### 5. Исправить производительность
- Оптимизировать операции apply_delta
- Увеличить скорость runtime loop
- Оптимизировать сохранение снимков
- Исправить логику генерации событий

### 6. Исправить адаптацию и деградацию
- Исправить логику инициализации параметров адаптации
- Реализовать правильный жизненный цикл активации/деактивации
- Исправить логику длительной деградации

### 7. Настроить асинхронное тестирование
- Установить pytest-asyncio
- Переписать асинхронные тесты MCP с использованием плагина

### 8. Исправить локализацию ошибок
- Проверить сообщения об ошибках в MCP модулях

## Статус проекта

Проект имеет обширную тестовую базу (627 тестов), но содержит критические баги в основных системах:
- Обучение и адаптация (12 тестов провалено)
- Память (10 тестов провалено)
- Состояние (15 тестов провалено)
- Производительность (4 теста провалено)

Требуется комплексное исправление основных компонентов системы перед следующим этапом разработки.

Тестирование завершено!