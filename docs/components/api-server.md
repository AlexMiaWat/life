# 06_API_SERVER.md — API Сервер

## Назначение
API Server предоставляет HTTP интерфейс для управления системой Life и получения её состояния из внешних приложений.

## Текущий статус
✅ **Реализован** (v2.0 - упрощенная версия)
*   Основной файл: [`src/main_server_api.py`](../../src/main_server_api.py)
*   **Упрощенное API:** Убрана аутентификация, JWT токены и регистрация пользователей
*   Фреймворк: FastAPI
*   Запускается в отдельном потоке (Daemon), параллельно с Runtime Loop
*   **Текущие тесты:** Статические, дымовые и интеграционные тесты для упрощенного API

## API Server

### Основной API Server (`src/main_server_api.py`)

Единый API сервер для работы с Life системой (упрощенная версия без аутентификации).

**Endpoints:**

#### GET /status
Возвращает текущее состояние Life (Self-State).

**⚠️ Важно:** Текущая реализация возвращает все поля SelfState, включая transient и внутренние поля. Это может быть проблемой безопасности и производительности. Рекомендуется использовать фильтрацию полей (см. раздел "Контракт `/status` endpoint" ниже).

**Ответ (текущая реализация):**
```json
{
  "active": true,
  "ticks": 150,
  "age": 75.0,
  "energy": 95.5,
  "integrity": 1.0,
  "stability": 0.98,
  "subjective_time": 80.5,
  "fatigue": 10.0,
  "tension": 5.0,
  "life_id": "uuid-string",
  "birth_timestamp": 1700000000.0,
  "last_significance": 0.7,
  "last_event_intensity": 0.5,
  "learning_params": {...},
  "adaptation_params": {...},
  "planning": {...},
  "intelligence": {...},
  "subjective_time_base_rate": 1.0,
  "subjective_time_rate_min": 0.1,
  "subjective_time_rate_max": 3.0,
  "subjective_time_intensity_coeff": 1.0,
  "subjective_time_stability_coeff": 0.5,
  "subjective_time_energy_coeff": 0.5,
  "subjective_time_intensity_smoothing": 0.3,
  "memory": [...],
  "recent_events": [...],
  "energy_history": [...],
  "stability_history": [...],
  "adaptation_history": [...],
  "activated_memory": [...],  // ⚠️ Transient поле
  "last_pattern": "...",      // ⚠️ Transient поле
  "_initialized": true,       // ⚠️ Внутреннее поле
  "_logging_enabled": true,   // ⚠️ Внутреннее поле
  ...
}
```

**Контракт `/status` endpoint:**

Endpoint `/status` должен возвращать только безопасные поля SelfState, исключая:
- **Transient поля** (не сохраняются в snapshot):
  - `activated_memory` - активированные записи памяти для текущего события
  - `last_pattern` - последний выбранный паттерн decision
- **Внутренние поля** (начинаются с `_`):
  - `_initialized`, `_logging_enabled`, `_log_only_critical`, `_log_buffer`, `_log_buffer_size`
- **Не сериализуемые поля:**
  - `archive_memory` - архивная память

**Безопасные поля для публичного API:**

**Основные метрики:**
- `active` (bool) - флаг активности
- `energy` (float) - энергия [0-100]
- `integrity` (float) - целостность [0-1]
- `stability` (float) - стабильность [0-1]

**Временные метрики:**
- `ticks` (int) - количество тиков
- `age` (float) - возраст в секундах
- `subjective_time` (float) - субъективное время

**Внутренняя динамика:**
- `fatigue` (float) - усталость
- `tension` (float) - напряжение

**Идентификация:**
- `life_id` (str) - уникальный идентификатор
- `birth_timestamp` (float) - время рождения

**Параметры обучения и адаптации:**
- `learning_params` (dict) - параметры обучения
- `adaptation_params` (dict) - параметры адаптации

**Последние значения:**
- `last_significance` (float) - значимость последнего события
- `last_event_intensity` (float) - интенсивность последнего события

**Когнитивные слои:**
- `planning` (dict) - планирование
- `intelligence` (dict) - результаты обработки

**Параметры субъективного времени:**
- `subjective_time_base_rate`, `subjective_time_rate_min`, `subjective_time_rate_max`
- `subjective_time_intensity_coeff`, `subjective_time_stability_coeff`, `subjective_time_energy_coeff`
- `subjective_time_intensity_smoothing`

**Опциональные поля** (можно добавить с ограничениями):
- `memory` - ограничить последние N записей (например, 10)
- `recent_events` - ограничить последние N событий (например, 10)
- `energy_history` - ограничить последние N значений (например, 50)
- `stability_history` - ограничить последние N значений (например, 50)
- `adaptation_history` - ограничить последние N значений (например, 50)

**Рекомендуемый минимальный контракт:**
```json
{
  "active": true,
  "ticks": 150,
  "age": 75.0,
  "energy": 95.5,
  "integrity": 1.0,
  "stability": 0.98
}
```

**Рекомендуемый расширенный контракт:**
Включает все безопасные поля, перечисленные выше, исключая transient и внутренние поля.

#### GET /refresh-cache
Принудительно обновляет кэш снапшотов (для тестирования и отладки).
Полезно для немедленного обновления состояния после изменений в файловой системе.

**Пример запроса:**
```bash
curl http://localhost:8000/refresh-cache
```

**Ответ (успех):**
```json
{
  "status": "cache_refreshed",
  "snapshot_ticks": 150
}
```

**Ответ (ошибка):**
```json
{
  "error": "Could not refresh snapshot cache"
}
```

#### GET /clear-data
Очищает все накопленные данные (логи, снапшоты).
Полезно для сброса "памяти" между экспериментами без перезапуска сервера.

**Пример запроса:**
```bash
curl http://localhost:8000/clear-data
```

**Ответ:**
```json
"Data cleared"
```

#### POST /event
Отправляет событие в систему Life для обработки.

**Тело запроса:**
```json
{
  "type": "noise",
  "intensity": 0.1,
  "timestamp": 1704987654.321,
  "metadata": {
    "source": "manual",
    "description": "Тестовое событие"
  }
}
```

**Параметры:**
- `type` (string, required): Тип события (`noise`, `decay`, `recovery`, `shock`, `idle`, `memory_echo`, `social_presence`, `social_conflict`, `social_harmony`, `cognitive_doubt`, `cognitive_clarity`, `cognitive_confusion`, `existential_void`, `existential_purpose`, `existential_finitude`, `connection`, `isolation`, `insight`, `confusion`, `curiosity`, `meaning_found`, `void`, `acceptance`)
- `intensity` (float, optional): Интенсивность события (-1.0 до 1.0)
- `timestamp` (float, optional): Временная метка (Unix timestamp)
- `metadata` (object, optional): Дополнительные данные

**Примеры запросов:**

1. **Простое событие:**
```bash
curl -X POST http://localhost:8000/event \
  -H "Content-Type: application/json" \
  -d '{"type":"noise","intensity":0.5}'
```

2. **Событие с метаданными:**
```bash
curl -X POST http://localhost:8000/event \
  -H "Content-Type: application/json" \
  -d '{"type":"shock","intensity":-0.8,"metadata":{"source":"test","reason":"experiment"}}'
```

**Ответ:**
```json
"Event accepted"
```

**Ошибки:**
- `400 Bad Request`: Неверный формат данных
- `422 Unprocessable Entity`: Неверные значения параметров

**Запуск:**
```bash
python src/main_server_api.py --tick-interval 0.5
```

*   Порт по умолчанию: `8000`
*   Документация API (Swagger): `http://localhost:8000/docs`

## Архитектура

Сервер работает в режиме "Sidecar" для Runtime Loop:
1.  Loop обновляет `Self-State` (словарь).
2.  API читает этот же словарь (по ссылке) и отдает клиенту.
3.  Благодаря GIL в Python, чтение атомарных значений безопасно, но для сложных структур может потребоваться блокировка (пока не реализована).

## Dev-режим и Hot Reload

### Автоматическая перезагрузка

В dev-режиме (`--dev`) система использует механизм hot reload через `importlib.reload()` для автоматической перезагрузки модулей при изменении файлов.

**⚠️ Важно:** Текущая реализация hot reload имеет известные проблемы, задокументированные в `docs/development/HOT_RELOAD_PROBLEMS.md` и `todo/DEBT.md` (#10).

### Известные проблемы

1. **Идентичность объектов:** При перезагрузке создаются новые классы, но старые ссылки остаются, что может привести к неконсистентному состоянию между компонентами.
2. **Висящие потоки/серверы:** Старые потоки могут не завершиться корректно, создавая множественные экземпляры и утечки ресурсов.
3. **Непредсказуемость:** Отсутствие синхронизации создает race conditions и делает поведение системы непредсказуемым.

**Рекомендации:**
- Для production используйте обычный режим (без `--dev`)
- В dev-режиме будьте готовы к возможным проблемам и перезапускайте процесс при необходимости
- См. `docs/development/HOT_RELOAD_PROBLEMS.md` для детального описания проблем и рекомендаций по решению

### Использование dev-режима

```bash
# Запуск с автоматической перезагрузкой
python src/main_server_api.py --dev --tick-interval 1.0
```

При изменении отслеживаемых файлов (`src/main_server_api.py`, `src/monitor/console.py`, `src/runtime/loop.py`, `src/state/self_state.py`) система автоматически перезагрузит модули и перезапустит API сервер.

## Логирование

### Централизованное логирование

API сервер использует централизованную систему логирования для управления выводом диагностической информации. Все компоненты проекта используют унифицированную конфигурацию логирования из модуля `src/logging_config.py`.

### Уровни логирования

Уровень логирования настраивается автоматически в зависимости от режима работы:

- **Dev-режим (`--dev`)**: `DEBUG` уровень — выводится вся диагностическая информация
- **Production режим**: `INFO` уровень — выводятся только важные информационные сообщения

### Категории логирования

#### DEBUG уровень (только в dev-режиме)
- Детальное логирование HTTP-запросов (в `log_request()`)
- Диагностика обработки событий (POST /event)
- Информация о перезагрузке модулей
- Отслеживание изменений файлов

#### INFO уровень
- Запуск API сервера
- Инициализация reloader
- Обнаружение изменений файлов
- Перезагрузка модулей
- Очистка данных при старте
- Завершение работы

#### WARNING уровень
- Предупреждения о незавершенных потоках при перезагрузке

#### ERROR уровень
- Ошибки при отслеживании файлов
- Ошибки обработки запросов

### Настройка логирования

Логирование настраивается через централизованную функцию `setup_logging()`:

```python
from src.logging_config import setup_logging

# В dev-режиме (verbose=True)
setup_logging(verbose=True)  # DEBUG уровень

# В production режиме (verbose=False)
setup_logging(verbose=False)  # INFO уровень по умолчанию
```

### Модуль logging_config.py

Централизованная конфигурация логирования обеспечивает:

1. **Консистентность**: Все компоненты используют одинаковый формат и уровни
2. **Производительность**: DEBUG логи внешних библиотек подавляются в production
3. **Гибкость**: Легко изменять конфигурацию в одном месте

```python
# src/logging_config.py
def setup_logging(verbose: bool = False) -> None:
    """Настройка логирования для приложения."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Подавление verbose логов внешних библиотек в production
    if not verbose:
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
```

### Примеры использования

**В dev-режиме:**
```bash
python src/main_server_api.py --dev
# Выводятся все DEBUG сообщения, включая детальное логирование HTTP-запросов
```

**В production режиме:**
```bash
python src/main_server_api.py
# Выводятся только INFO, WARNING и ERROR сообщения
```

### Преимущества централизованного логирования

1. **Управляемость**: Уровень детализации контролируется через настройки logging
2. **Гибкость**: Легко переключаться между режимами без изменения кода
3. **Чистота кода**: Удалены диагностические print-блоки, которые засоряли вывод
4. **Стандартизация**: Все компоненты используют унифицированную систему логирования
5. **Производительность**: Автоматическое подавление verbose логов внешних библиотек

## Зависимости

API сервер использует минимальный набор зависимостей FastAPI:
- `fastapi` — веб-фреймворк
- `uvicorn` — ASGI сервер
- `requests` — для HTTP запросов в тестах

Все зависимости указаны в `requirements.txt`.
