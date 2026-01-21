# Отчет о тестировании - 2026-01-21 12:43:04

## Общая статистика

- **Всего тестов:** 5
- **Пройдено:** 0
- **Провалено:** 0
- **Ошибки:** 5
- **Пропущено:** 0
- **Время выполнения:** 7.64 секунд

## Статус тестирования

❌ **ОБНАРУЖЕНЫ ПРОБЛЕМЫ:** 5 тестов не прошли

## Детали проваленных тестов

### 1. ::src.test.test_external_observer

**Время выполнения:** 0.000 сек

**Ошибка:**

```
collection failure
ImportError while importing test module '/workspace/src/test/test_external_observer.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/local/lib/python3.10/dist-packages/_pytest/python.py:507: in importtestmodule
    mod = import_path(
/usr/local/lib/python3.10/dist-packages/_pytest/pathlib.py:587: in import_path
    importlib.import_module(module_name)
/usr/lib/python3.10/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1050: in _gcd_import
    ???
<frozen importlib._bootstrap>:1027: in _find_and_load
    ???
<frozen importlib._bootstrap>:1006: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:688: in _load_unlocked
    ???
/usr/local/lib/python3.10/dist-packages/_pytest/assertion/rewrite.py:197: in exec_module
    exec(co, module.__dict__)
src/test/test_external_observer.py:13: in <module>
    from src.observability.external_observer import (
E   ImportError: cannot import name 'ExternalObserver' from 'src.observability.external_observer' (/workspace/src/observability/external_observer.py)
```

### 2. ::src.test.test_external_observer_integration_new

**Время выполнения:** 0.000 сек

**Ошибка:**

```
collection failure
ImportError while importing test module '/workspace/src/test/test_external_observer_integration_new.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/local/lib/python3.10/dist-packages/_pytest/python.py:507: in importtestmodule
    mod = import_path(
/usr/local/lib/python3.10/dist-packages/_pytest/pathlib.py:587: in import_path
    importlib.import_module(module_name)
/usr/lib/python3.10/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1050: in _gcd_import
    ???
<frozen importlib._bootstrap>:1027: in _find_and_load
    ???
<frozen importlib._bootstrap>:1006: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:688: in _load_unlocked
    ???
/usr/local/lib/python3.10/dist-packages/_pytest/assertion/rewrite.py:197: in exec_module
    exec(co, module.__dict__)
src/test/test_external_observer_integration_new.py:18: in <module>
    from src.observability.external_observer import (
E   ImportError: cannot import name 'ExternalObserver' from 'src.observability.external_observer' (/workspace/src/observability/external_observer.py)
```

### 3. ::src.test.test_external_observer_smoke

**Время выполнения:** 0.000 сек

**Ошибка:**

```
collection failure
ImportError while importing test module '/workspace/src/test/test_external_observer_smoke.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/local/lib/python3.10/dist-packages/_pytest/python.py:507: in importtestmodule
    mod = import_path(
/usr/local/lib/python3.10/dist-packages/_pytest/pathlib.py:587: in import_path
    importlib.import_module(module_name)
/usr/lib/python3.10/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1050: in _gcd_import
    ???
<frozen importlib._bootstrap>:1027: in _find_and_load
    ???
<frozen importlib._bootstrap>:1006: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:688: in _load_unlocked
    ???
/usr/local/lib/python3.10/dist-packages/_pytest/assertion/rewrite.py:197: in exec_module
    exec(co, module.__dict__)
src/test/test_external_observer_smoke.py:23: in <module>
    from src.observability.external_observer import (
E   ImportError: cannot import name 'ExternalObserver' from 'src.observability.external_observer' (/workspace/src/observability/external_observer.py)
```

### 4. ::src.test.test_external_observer_static

**Время выполнения:** 0.000 сек

**Ошибка:**

```
collection failure
ImportError while importing test module '/workspace/src/test/test_external_observer_static.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/local/lib/python3.10/dist-packages/_pytest/python.py:507: in importtestmodule
    mod = import_path(
/usr/local/lib/python3.10/dist-packages/_pytest/pathlib.py:587: in import_path
    importlib.import_module(module_name)
/usr/lib/python3.10/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1050: in _gcd_import
    ???
<frozen importlib._bootstrap>:1027: in _find_and_load
    ???
<frozen importlib._bootstrap>:1006: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:688: in _load_unlocked
    ???
/usr/local/lib/python3.10/dist-packages/_pytest/assertion/rewrite.py:197: in exec_module
    exec(co, module.__dict__)
src/test/test_external_observer_static.py:23: in <module>
    from src.observability.external_observer import (
E   ImportError: cannot import name 'ExternalObserver' from 'src.observability.external_observer' (/workspace/src/observability/external_observer.py)
```

### 5. ::src.test.test_reporting

**Время выполнения:** 0.000 сек

**Ошибка:**

```
collection failure
ImportError while importing test module '/workspace/src/test/test_reporting.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/local/lib/python3.10/dist-packages/_pytest/python.py:507: in importtestmodule
    mod = import_path(
/usr/local/lib/python3.10/dist-packages/_pytest/pathlib.py:587: in import_path
    importlib.import_module(module_name)
/usr/lib/python3.10/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1050: in _gcd_import
    ???
<frozen importlib._bootstrap>:1027: in _find_and_load
    ???
<frozen importlib._bootstrap>:1006: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:688: in _load_unlocked
    ???
/usr/local/lib/python3.10/dist-packages/_pytest/assertion/rewrite.py:197: in exec_module
    exec(co, module.__dict__)
src/test/test_reporting.py:13: in <module>
    from src.observability.external_observer import (
E   ImportError: cannot import name 'ExternalObserver' from 'src.observability.external_observer' (/workspace/src/observability/external_observer.py)
```

## Статистика по файлам тестов

| Файл | Всего | Пройдено | Провалено |
|------|-------|----------|-----------|

## Рекомендации

- Исправить ошибки в коде тестов или зависимостях
- Проверить импорты и структуру проекта

---
*Отчет создан автоматически*