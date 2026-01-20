# Отчет о тестировании - 2026-01-20 21:23:00

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

### 1. src.test.test_generator.TestGeneratorCLI::test_send_event_success

**Время выполнения:** 0.037 сек

**Ошибка:**

```
ImportError: attempted relative import beyond top-level package
src/test/test_generator.py:152: in test_send_event_success
    from environment.generator_cli import send_event
src/environment/generator_cli.py:17: in <module>
    from ..logging_config import get_logger, setup_logging
E   ImportError: attempted relative import beyond top-level package
```

### 2. src.test.test_generator.TestGeneratorCLI::test_send_event_connection_error

**Время выполнения:** 0.009 сек

**Ошибка:**

```
ImportError: attempted relative import beyond top-level package
src/test/test_generator.py:173: in test_send_event_connection_error
    from environment.generator_cli import send_event
src/environment/generator_cli.py:17: in <module>
    from ..logging_config import get_logger, setup_logging
E   ImportError: attempted relative import beyond top-level package
```

### 3. src.test.test_generator.TestGeneratorCLI::test_send_event_timeout

**Время выполнения:** 0.008 сек

**Ошибка:**

```
ImportError: attempted relative import beyond top-level package
src/test/test_generator.py:189: in test_send_event_timeout
    from environment.generator_cli import send_event
src/environment/generator_cli.py:17: in <module>
    from ..logging_config import get_logger, setup_logging
E   ImportError: attempted relative import beyond top-level package
```

### 4. src.test.test_generator_cli.TestGeneratorCLI::test_main_function_if_name_main

**Время выполнения:** 0.007 сек

**Ошибка:**

```
ImportError: attempted relative import beyond top-level package
/usr/lib/python3.10/unittest/mock.py:1248: in _dot_lookup
    return getattr(thing, comp)
E   AttributeError: module 'environment' has no attribute 'generator_cli'. Did you mean: 'generator'?

During handling of the above exception, another exception occurred:
src/test/test_generator_cli.py:201: in test_main_function_if_name_main
    with patch("environment.generator_cli.EventGenerator") as mock_gen_class, patch(
/usr/lib/python3.10/unittest/mock.py:1431: in __enter__
    self.target = self.getter()
/usr/lib/python3.10/unittest/mock.py:1618: in <lambda>
    getter = lambda: _importer(target)
/usr/lib/python3.10/unittest/mock.py:1261: in _importer
    thing = _dot_lookup(thing, comp, import_path)
/usr/lib/python3.10/unittest/mock.py:1250: in _dot_lookup
    __import__(import_path)
src/environment/generator_cli.py:17: in <module>
    from ..logging_config import get_logger, setup_logging
E   ImportError: attempted relative import beyond top-level package
```

### 5. src.test.test_property_based.TestMemoryPropertyBased::test_memory_append_idempotent

**Время выполнения:** 0.150 сек

**Ошибка:**

```
AssertionError: assert 1 == 2
 +  where 1 = len([MemoryEntry(event_type='0', meaning_significance=0.0, timestamp=1768942657.521243, weight=1.0, feedback_data=None, subjective_timestamp=None)])
 +  and   2 = len([MemoryEntry(event_type='0', meaning_significance=0.0, timestamp=1768942657.521243, weight=1.0, feedback_data=None, subjective_timestamp=None), MemoryEntry(event_type='0', meaning_significance=0.0, timestamp=1768942657.521243, weight=1.0, feedback_data=None, subjective_timestamp=None)])
Falsifying example: test_memory_append_idempotent(
    self=<test_property_based.TestMemoryPropertyBased object at 0x7009a3a2e0e0>,
    event_type='0',
    significance=0.0,
    num_appends=2,
)
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
| test | 175 | 170 | 5 |

## Рекомендации

- Необходимо исправить проваленные тесты
- Проверить логику и реализации соответствующих функций
- Возможно, требуется обновление зависимостей или конфигурации

---
*Отчет создан автоматически*
