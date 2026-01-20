# Отчет о тестировании - 2026-01-20 19:11:41

## Общая статистика

- **Всего тестов:** 2 (только тесты с ошибками сбора)
- **Пройдено:** 0
- **Провалено:** 0
- **Ошибки:** 2
- **Пропущено:** 0
- **Время выполнения:** 4.24 секунд

## Статус тестирования

❌ **ОБНАРУЖЕНЫ ПРОБЛЕМЫ:** 2 тестов не прошли

## Детали проваленных тестов

### 1. src.test.test_api_auth_integration

**Время выполнения:** 0.000 сек

**Ошибка:**

```
ImportError while importing test module '/workspace/src/test/test_api_auth_integration.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.10/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
src/test/test_api_auth_integration.py:25: in <module>
    from api import app, fake_users_db
E   ImportError: cannot import name 'fake_users_db' from 'api' (/workspace/api.py)
```

### 2. src.test.test_api_auth_static

**Время выполнения:** 0.000 сек

**Ошибка:**

```
ImportError while importing test module '/workspace/src/test/test_api_auth_static.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.10/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
src/test/test_api_auth_static.py:24: in <module>
    from api import (
E   ImportError: cannot import name 'ACCESS_TOKEN_EXPIRE_MINUTES' from 'api' (/workspace/api.py)
```

## Статистика по файлам тестов

| Файл | Всего | Пройдено | Провалено |
|------|-------|----------|-----------|
| test_api_auth_integration | 1 | 0 | 1 |
| test_api_auth_static | 1 | 0 | 1 |

## Рекомендации

- Исправить ошибки в коде тестов или зависимостях
- Проверить импорты и структуру проекта
- Проверить содержимое файла api.py на наличие необходимых экспортов (fake_users_db, ACCESS_TOKEN_EXPIRE_MINUTES)
- Возможно, требуется обновление зависимостей или конфигурации

---
*Отчет создан автоматически*