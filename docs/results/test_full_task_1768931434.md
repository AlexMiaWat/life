# Отчет о тестировании - 2026-01-20 18:59:07

## Общая статистика

- **Всего тестов:** 1
- **Пройдено:** 0
- **Провалено:** 0
- **Ошибки:** 1
- **Пропущено:** 0
- **Время выполнения:** 5.95 секунд

## Статус тестирования

❌ **ОБНАРУЖЕНЫ ПРОБЛЕМЫ:** 1 тестов не прошли

## Детали проваленных тестов

### 1. ::src.test.test_degradation

**Время выполнения:** 0.000 сек

**Ошибка:**

```
collection failure
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
/usr/local/lib/python3.10/dist-packages/_pytest/assertion/rewrite.py:188: in exec_module
    source_stat, co = _rewrite_test(fn, self.config)
/usr/local/lib/python3.10/dist-packages/_pytest/assertion/rewrite.py:357: in _rewrite_test
    tree = ast.parse(source, filename=strfn)
/usr/lib/python3.10/ast.py:50: in parse
    return compile(source, filename, mode, flags,
E     File "/workspace/src/test/test_degradation.py", line 810
E       state.disable_logging()
E       ^^^^^
E   IndentationError: expected an indented block after 'try' statement on line 808
```

## Статистика по файлам тестов

| Файл | Всего | Пройдено | Провалено |
|------|-------|----------|-----------|

## Рекомендации

- Исправить ошибки в коде тестов или зависимостях
- Проверить импорты и структуру проекта

---
*Отчет создан автоматически*