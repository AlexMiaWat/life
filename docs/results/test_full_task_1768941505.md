# Отчет о тестировании - 2026-01-20 21:03:02

## Общая статистика

- **Всего тестов:** 175
- **Пройдено:** 170
- **Провалено:** 5
- **Ошибки:** 0
- **Пропущено:** 0
- **Время выполнения:** 8.19 секунд

## Статус тестирования

❌ **ОБНАРУЖЕНЫ ПРОБЛЕМЫ:** 5 тестов не прошли

## Детали проваленных тестов

### 1. src/test/test_generator.py::TestGeneratorCLI::test_send_event_success

**Время выполнения:** 0.001 сек

**Ошибка:**

```
src/test/test_generator.py:152: in test_send_event_success
    from environment.generator_cli import send_event
src/environment/generator_cli.py:17: in <module>
    from ..logging_config import get_logger, setup_logging
E   ImportError: attempted relative import beyond top-level package
```

### 2. src/test/test_generator.py::TestGeneratorCLI::test_send_event_connection_error

**Время выполнения:** 0.001 сек

**Ошибка:**

```
src/test/test_generator.py:173: in test_send_event_connection_error
    from environment.generator_cli import send_event
src/environment/generator_cli.py:17: in <module>
    from ..logging_config import get_logger, setup_logging
E   ImportError: attempted relative import beyond top-level package
```

### 3. src/test/test_generator.py::TestGeneratorCLI::test_send_event_timeout

**Время выполнения:** 0.001 сек

**Ошибка:**

```
src/test/test_generator.py:189: in test_send_event_timeout
    from environment.generator_cli import send_event
src/environment/generator_cli.py:17: in <module>
    from ..logging_config import get_logger, setup_logging
E   ImportError: attempted relative import beyond top-level package
```

### 4. src/test/test_generator_cli.py::TestGeneratorCLI::test_main_function_if_name_main

**Время выполнения:** 0.001 сек

**Ошибка:**

```
src/test/test_generator_cli.py:201: in test_main_function_if_name_main
    with patch("environment.generator_cli.EventGenerator") as mock_gen_class, patch(
/usr/lib/python3.10/unittest/mock.py:1431: in __enter__
    self.target = self.getter()
/usr/lib/python3.10/unittest/mock.py:1618: in <lambda>
    getter = lambda: _dot_lookup(target)
/usr/lib/python3.10/unittest/mock.py:1261: in _importer
    thing = _dot_lookup(thing, comp, import_path)
/usr/lib/python3.10/unittest/mock.py:1250: in _dot_lookup
    __import__(import_path)
src/environment/generator_cli.py:17: in <module>
    from ..logging_config import get_logger, setup_logging
E   ImportError: attempted relative import beyond top-level package
```

### 5. src/test/test_property_based.py::TestMemoryPropertyBased::test_memory_append_idempotent

**Время выполнения:** 0.003 сек

**Ошибка:**

```
src/test/test_property_based.py:152: in test_memory_append_idempotent
    event_type=st.text(min_size=1, max_size=20),
src/test/test_property_based.py:176: in test_memory_append_idempotent
    assert len(memory1) == len(memory2)
E   AssertionError: assert 1 == 2
E    +  where 1 = len([MemoryEntry(event_type='0', meaning_significance=0.0, timestamp=1768942657.521243, weight=1.0, feedback_data=None, subjective_timestamp=None)])
E    +  and   2 = len([MemoryEntry(event_type='0', meaning_significance=0.0, timestamp=1768942657.521243, weight=1.0, feedback_data=None, subjective_timestamp=None), MemoryEntry(event_type='0', meaning_significance=0.0, timestamp=1768942657.521243, weight=1.0, feedback_data=None, subjective_timestamp=None)])
E   Falsifying example: test_memory_append_idempotent(
E       self=<test_property_based.TestMemoryPropertyBased object at 0x7009a3a2e0e0>,
E       event_type='0',
E       significance=0.0,
E       num_appends=2,
E   )
```

## Статистика по файлам тестов

| Файл | Всего | Пройдено | Провалено |
|------|-------|----------|-----------|
| test_generator.py | 17 | 14 | 3 |
| test_generator_cli.py | 7 | 6 | 1 |
| test_property_based.py | 8 | 7 | 1 |
| test_action.py | 12 | 12 | 0 |
| test_activation.py | 11 | 11 | 0 |
| test_decision.py | 13 | 13 | 0 |
| test_environment.py | 23 | 23 | 0 |
| test_event_queue_edge_cases.py | 1 | 1 | 0 |
| test_event_queue_race_condition.py | 2 | 2 | 0 |
| test_feedback.py | 11 | 11 | 0 |
| test_feedback_data.py | 1 | 1 | 0 |
| test_intelligence.py | 10 | 10 | 0 |
| test_meaning.py | 25 | 25 | 0 |
| test_memory.py | 17 | 17 | 0 |
| test_monitor.py | 8 | 8 | 0 |
| test_planning.py | 9 | 9 | 0 |
| test_state.py | 20 | 20 | 0 |
| test_subjective_time.py | 9 | 9 | 0 |
| test_api.py | 4 | 0 | 0 |
| test_api_integration.py | 15 | 15 | 0 |
| test_feedback.py | 1 | 1 | 0 |
| test_generator_integration.py | 5 | 5 | 0 |
| test_memory.py | 27 | 27 | 0 |
| test_runtime_integration.py | 10 | 10 | 0 |
| test_runtime_loop_edge_cases.py | 5 | 5 | 0 |
| test_runtime_loop_feedback_coverage.py | 1 | 1 | 0 |

## Рекомендации

- Исправить проблемы с импортами в модулях generator_cli - проблема с относительными импортами при запуске из тестовой среды
- Исправить логику в тесте test_memory_append_idempotent - тест ожидает идемпотентность, но append операция не является идемпотентной
- Проверить логику и реализации соответствующих функций
- Возможно, требуется обновление структуры импортов или конфигурации тестирования

---

*Отчет создан автоматически*
