# Отчет: Определение контракта `/status` endpoint

**Задача:** Определить контракт: что именно возвращает `/status` (только безопасные поля, без transient/внутренних)

**Дата:** 2026-01-20

## 1. Анализ текущей реализации

### 1.1. Реализация в `main_server_api.py`

**Файл:** `src/main_server_api.py`, строка 62

```python
self.wfile.write(json.dumps(asdict(self.server.self_state)).encode())
```

**Проблема:** Используется `asdict()` из `dataclasses`, который возвращает ВСЕ поля `SelfState`, включая:
- Transient поля (не сохраняются в snapshot)
- Внутренние поля (начинаются с `_`)
- Не сериализуемые объекты (например, `ArchiveMemory`)
- Потенциально большие структуры данных

### 1.2. Реализация в `api.py`

**Файл:** `api.py`, строки 80-86, 248-255

```python
class StatusResponse(BaseModel):
    active: bool
    ticks: int
    age: float
    energy: float
    stability: float
    integrity: float
```

**Проблема:** Слишком ограниченный набор полей, не отражает полную картину состояния системы.

## 2. Анализ структуры SelfState

### 2.1. Все поля SelfState (из `src/state/self_state.py`)

#### Основные метрики (Vital Parameters):
- `active` (bool) - флаг активности
- `energy` (float) - энергия [0-100]
- `integrity` (float) - целостность [0-1]
- `stability` (float) - стабильность [0-1]

#### Временные метрики:
- `ticks` (int) - количество тиков
- `age` (float) - возраст в секундах
- `subjective_time` (float) - субъективное время

#### Внутренняя динамика:
- `fatigue` (float) - усталость
- `tension` (float) - напряжение

#### Идентификация:
- `life_id` (str) - уникальный идентификатор
- `birth_timestamp` (float) - время рождения

#### Параметры обучения и адаптации:
- `learning_params` (dict) - параметры обучения
- `adaptation_params` (dict) - параметры адаптации

#### Последние значения:
- `last_significance` (float) - значимость последнего события
- `last_event_intensity` (float) - интенсивность последнего события

#### Когнитивные слои:
- `planning` (dict) - планирование
- `intelligence` (dict) - результаты обработки

#### Параметры субъективного времени:
- `subjective_time_base_rate` (float)
- `subjective_time_rate_min` (float)
- `subjective_time_rate_max` (float)
- `subjective_time_intensity_coeff` (float)
- `subjective_time_stability_coeff` (float)

#### Потенциально большие/чувствительные поля:
- `memory` (Memory) - может содержать много записей
- `recent_events` (list) - список последних событий
- `energy_history` (list) - история значений энергии
- `stability_history` (list) - история значений стабильности
- `adaptation_history` (list) - история адаптаций

### 2.2. Transient поля (НЕ сохраняются в snapshot)

**Определение:** Поля, которые не сохраняются в snapshot и используются только во время выполнения.

- `activated_memory` (list) - активированные записи памяти для текущего события (строка 273-275)
- `last_pattern` (str) - последний выбранный паттерн decision (строка 276)

**Причина исключения:** Эти поля временные и не имеют смысла вне контекста текущего выполнения.

### 2.3. Внутренние поля (начинаются с `_`)

**Определение:** Поля, используемые для внутренней логики класса, не являются частью состояния.

- `_initialized` (bool) - флаг инициализации (строка 50)
- `_logging_enabled` (bool) - флаг логирования (строка 51)
- `_log_only_critical` (bool) - режим логирования только критичных изменений (строка 52)
- `_log_buffer` (list) - буфер логов (строка 53)
- `_log_buffer_size` (int) - размер буфера логов (строка 54)

**Причина исключения:** Внутренние поля не должны быть частью публичного API.

### 2.4. Не сериализуемые объекты

- `archive_memory` (ArchiveMemory) - архивная память (строка 45-47)

**Причина исключения:** Объект `ArchiveMemory` не поддерживает прямую JSON сериализацию и не должен быть частью публичного API.

## 3. Определение безопасного контракта

### 3.1. Безопасные поля для публичного API

#### Группа 1: Основные метрики (Vital Parameters) - ОБЯЗАТЕЛЬНЫЕ
```json
{
  "active": true,
  "energy": 95.5,
  "integrity": 1.0,
  "stability": 0.98
}
```

#### Группа 2: Временные метрики - ОБЯЗАТЕЛЬНЫЕ
```json
{
  "ticks": 150,
  "age": 75.0,
  "subjective_time": 80.5
}
```

#### Группа 3: Внутренняя динамика - РЕКОМЕНДУЕМЫЕ
```json
{
  "fatigue": 10.0,
  "tension": 5.0
}
```

#### Группа 4: Идентификация - ОПЦИОНАЛЬНЫЕ
```json
{
  "life_id": "uuid-string",
  "birth_timestamp": 1700000000.0
}
```

**Примечание:** `life_id` может быть чувствительным в некоторых случаях, но обычно безопасен для публичного API.

#### Группа 5: Параметры обучения и адаптации - РЕКОМЕНДУЕМЫЕ
```json
{
  "learning_params": {
    "event_type_sensitivity": {...},
    "significance_thresholds": {...},
    "response_coefficients": {...}
  },
  "adaptation_params": {
    "behavior_sensitivity": {...},
    "behavior_thresholds": {...},
    "behavior_coefficients": {...}
  }
}
```

#### Группа 6: Последние значения - РЕКОМЕНДУЕМЫЕ
```json
{
  "last_significance": 0.7,
  "last_event_intensity": 0.5
}
```

#### Группа 7: Когнитивные слои - РЕКОМЕНДУЕМЫЕ
```json
{
  "planning": {...},
  "intelligence": {...}
}
```

#### Группа 8: Параметры субъективного времени - ОПЦИОНАЛЬНЫЕ
```json
{
  "subjective_time_base_rate": 1.0,
  "subjective_time_rate_min": 0.1,
  "subjective_time_rate_max": 3.0,
  "subjective_time_intensity_coeff": 1.0,
  "subjective_time_stability_coeff": 0.5
}
```

### 3.2. Поля, которые НЕ должны быть в контракте

#### Transient поля:
- ❌ `activated_memory` - временное поле, не имеет смысла вне контекста выполнения
- ❌ `last_pattern` - временное поле, не имеет смысла вне контекста выполнения

#### Внутренние поля (начинаются с `_`):
- ❌ `_initialized` - внутренний флаг
- ❌ `_logging_enabled` - внутренний флаг
- ❌ `_log_only_critical` - внутренний флаг
- ❌ `_log_buffer` - внутренний буфер
- ❌ `_log_buffer_size` - внутренний параметр

#### Не сериализуемые:
- ❌ `archive_memory` - не поддерживает JSON сериализацию

#### Потенциально большие/чувствительные (опционально исключить или ограничить):
- ⚠️ `memory` - может быть большим, рекомендуется ограничить количество записей или исключить
- ⚠️ `recent_events` - может быть большим, рекомендуется ограничить
- ⚠️ `energy_history` - может быть большим, рекомендуется ограничить или исключить
- ⚠️ `stability_history` - может быть большим, рекомендуется ограничить или исключить
- ⚠️ `adaptation_history` - может быть большим, рекомендуется ограничить или исключить

## 4. Рекомендуемый контракт `/status`

### 4.1. Минимальный контракт (как в `api.py`)

**Использование:** Для простых случаев мониторинга.

```json
{
  "active": true,
  "ticks": 150,
  "age": 75.0,
  "energy": 95.5,
  "stability": 0.98,
  "integrity": 1.0
}
```

### 4.2. Расширенный контракт (рекомендуемый)

**Использование:** Для полного мониторинга состояния системы.

```json
{
  "life_id": "550e8400-e29b-41d4-a716-446655440000",
  "birth_timestamp": 1700000000.0,
  "active": true,
  "ticks": 150,
  "age": 75.0,
  "subjective_time": 80.5,
  "energy": 95.5,
  "integrity": 1.0,
  "stability": 0.98,
  "fatigue": 10.0,
  "tension": 5.0,
  "last_significance": 0.7,
  "last_event_intensity": 0.5,
  "learning_params": {
    "event_type_sensitivity": {
      "noise": 0.2,
      "decay": 0.2,
      "recovery": 0.2,
      "shock": 0.2,
      "idle": 0.2
    },
    "significance_thresholds": {
      "noise": 0.1,
      "decay": 0.1,
      "recovery": 0.1,
      "shock": 0.1,
      "idle": 0.1
    },
    "response_coefficients": {
      "dampen": 0.5,
      "absorb": 1.0,
      "ignore": 0.0
    }
  },
  "adaptation_params": {
    "behavior_sensitivity": {
      "noise": 0.2,
      "decay": 0.2,
      "recovery": 0.2,
      "shock": 0.2,
      "idle": 0.2
    },
    "behavior_thresholds": {
      "noise": 0.1,
      "decay": 0.1,
      "recovery": 0.1,
      "shock": 0.1,
      "idle": 0.1
    },
    "behavior_coefficients": {
      "dampen": 0.5,
      "absorb": 1.0,
      "ignore": 0.0
    }
  },
  "planning": {},
  "intelligence": {},
  "subjective_time_base_rate": 1.0,
  "subjective_time_rate_min": 0.1,
  "subjective_time_rate_max": 3.0,
  "subjective_time_intensity_coeff": 1.0,
  "subjective_time_stability_coeff": 0.5
}
```

### 4.3. Опциональные поля (можно добавить с ограничениями)

Для полей, которые могут быть большими, рекомендуется добавить параметры запроса для ограничения:

- `memory` - ограничить последние N записей (например, `?memory_limit=10`)
- `recent_events` - ограничить последние N событий (например, `?events_limit=10`)
- `energy_history` - ограничить последние N значений (например, `?energy_history_limit=50`)
- `stability_history` - ограничить последние N значений (например, `?stability_history_limit=50`)
- `adaptation_history` - ограничить последние N значений (например, `?adaptation_history_limit=50`)

**Пример запроса с ограничениями:**
```
GET /status?memory_limit=10&events_limit=10&energy_history_limit=50
```

## 5. Сравнение с текущей реализацией

### 5.1. Текущая реализация (`main_server_api.py`)

**Проблемы:**
1. Возвращает все поля, включая transient (`activated_memory`, `last_pattern`)
2. Возвращает внутренние поля (`_initialized`, `_logging_enabled`, и т.д.)
3. Может вызвать ошибку при попытке сериализации `archive_memory`
4. Может вернуть очень большой ответ из-за `memory`, `recent_events`, `energy_history`, и т.д.

### 5.2. Текущая реализация (`api.py`)

**Проблемы:**
1. Слишком ограниченный набор полей
2. Не отражает полную картину состояния системы
3. Не включает важные метрики (`subjective_time`, `fatigue`, `tension`, и т.д.)

## 6. Рекомендации по реализации

### 6.1. Создать функцию фильтрации полей

Рекомендуется создать функцию `get_safe_status_dict(state: SelfState, include_optional: bool = True, limits: dict = None) -> dict`, которая:

1. Исключает все transient поля
2. Исключает все внутренние поля (начинающиеся с `_`)
3. Исключает не сериализуемые объекты (`archive_memory`)
4. Опционально ограничивает размер больших полей (`memory`, `recent_events`, `energy_history`, и т.д.)

### 6.2. Обновить `main_server_api.py`

Заменить:
```python
json.dumps(asdict(self.server.self_state))
```

На:
```python
json.dumps(get_safe_status_dict(self.server.self_state))
```

### 6.3. Обновить `StatusResponse` в `api.py`

Расширить модель `StatusResponse` для поддержки расширенного контракта или создать новую модель `ExtendedStatusResponse`.

### 6.4. Добавить опциональные параметры запроса

Добавить поддержку query-параметров для ограничения больших полей:
- `memory_limit` (int, optional)
- `events_limit` (int, optional)
- `energy_history_limit` (int, optional)
- `stability_history_limit` (int, optional)
- `adaptation_history_limit` (int, optional)

## 7. Выводы

1. **Текущая реализация в `main_server_api.py` небезопасна** - возвращает transient и внутренние поля, что является проблемой безопасности и производительности.

2. **Текущая реализация в `api.py` слишком ограничена** - не отражает полную картину состояния системы.

3. **Рекомендуется создать функцию фильтрации полей** для безопасного извлечения только публичных полей из `SelfState`.

4. **Рекомендуется использовать расширенный контракт** с опциональными параметрами для ограничения больших полей.

5. **Контракт должен быть документирован** в API документации для ясности для пользователей API.

## 8. Следующие шаги

1. ✅ Определить контракт (выполнено)
2. ⏳ Реализовать функцию фильтрации полей в `main_server_api.py`
3. ⏳ Обновить `StatusResponse` в `api.py` для расширенного контракта
4. ⏳ Добавить опциональные параметры для ограничения больших полей
5. ⏳ Обновить тесты для проверки контракта
6. ⏳ Обновить документацию API

Отчет завершен!
