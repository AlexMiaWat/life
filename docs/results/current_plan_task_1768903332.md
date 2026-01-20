# План выполнения задачи: Определение контракта `/status` endpoint

**Задача:** Определить контракт: что именно возвращает `/status` (только безопасные поля, без transient/внутренних)

**Дата создания:** 2026-01-20

## Анализ текущей ситуации

### Текущие реализации `/status`:

1. **`main_server_api.py`** (основной API сервер):
   - Возвращает: `json.dumps(asdict(self.server.self_state))`
   - Проблема: возвращает ВСЕ поля SelfState, включая transient и внутренние

2. **`api.py`** (FastAPI с аутентификацией):
   - Возвращает: `StatusResponse` модель с полями: `active`, `ticks`, `age`, `energy`, `stability`, `integrity`
   - Проблема: слишком ограниченный набор полей

### Структура SelfState:

**Transient поля (не сохраняются в snapshot):**
- `activated_memory` (list) - активированные записи памяти для текущего события
- `last_pattern` (str) - последний выбранный паттерн decision

**Внутренние поля (начинаются с `_`):**
- `_initialized` (bool) - флаг инициализации
- `_logging_enabled` (bool) - флаг логирования
- `_log_only_critical` (bool) - режим логирования только критичных изменений
- `_log_buffer` (list) - буфер логов
- `_log_buffer_size` (int) - размер буфера логов

**Не сериализуется напрямую:**
- `archive_memory` (ArchiveMemory) - архивная память

**Потенциально большие/чувствительные поля:**
- `memory` (Memory) - может содержать много записей
- `recent_events` (list) - список последних событий
- `energy_history` (list) - история значений энергии
- `stability_history` (list) - история значений стабильности
- `adaptation_history` (list) - история адаптаций

## Определение безопасного контракта

### Безопасные поля для публичного API:

#### 1. Основные метрики (Vital Parameters):
- `active` (bool) - флаг активности
- `energy` (float) - энергия [0-100]
- `integrity` (float) - целостность [0-1]
- `stability` (float) - стабильность [0-1]

#### 2. Временные метрики:
- `ticks` (int) - количество тиков
- `age` (float) - возраст в секундах
- `subjective_time` (float) - субъективное время

#### 3. Внутренняя динамика:
- `fatigue` (float) - усталость
- `tension` (float) - напряжение

#### 4. Идентификация:
- `life_id` (str) - уникальный идентификатор (обычно безопасно, но может быть чувствительным в некоторых случаях)
- `birth_timestamp` (float) - время рождения

#### 5. Параметры обучения и адаптации:
- `learning_params` (dict) - параметры обучения
- `adaptation_params` (dict) - параметры адаптации

#### 6. Последние значения:
- `last_significance` (float) - значимость последнего события
- `last_event_intensity` (float) - интенсивность последнего события

#### 7. Когнитивные слои (ограниченные):
- `planning` (dict) - планирование (обычно безопасно)
- `intelligence` (dict) - результаты обработки (обычно безопасно)

#### 8. Параметры субъективного времени:
- `subjective_time_base_rate` (float)
- `subjective_time_rate_min` (float)
- `subjective_time_rate_max` (float)
- `subjective_time_intensity_coeff` (float)
- `subjective_time_stability_coeff` (float)

### Поля, которые НЕ должны быть в контракте:

1. **Transient поля:**
   - `activated_memory`
   - `last_pattern`

2. **Внутренние поля (начинаются с `_`):**
   - `_initialized`
   - `_logging_enabled`
   - `_log_only_critical`
   - `_log_buffer`
   - `_log_buffer_size`

3. **Не сериализуемые:**
   - `archive_memory`

4. **Потенциально большие/чувствительные (опционально исключить или ограничить):**
   - `memory` - может быть большим, можно ограничить количество записей или исключить
   - `recent_events` - может быть большим, можно ограничить
   - `energy_history` - может быть большим, можно ограничить или исключить
   - `stability_history` - может быть большим, можно ограничить или исключить
   - `adaptation_history` - может быть большим, можно ограничить или исключить

## Рекомендуемый контракт `/status`

### Минимальный контракт (как в `api.py`):
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

### Расширенный контракт (рекомендуемый):
```json
{
  "life_id": "uuid-string",
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
  "learning_params": {...},
  "adaptation_params": {...},
  "planning": {...},
  "intelligence": {...},
  "subjective_time_base_rate": 1.0,
  "subjective_time_rate_min": 0.1,
  "subjective_time_rate_max": 3.0,
  "subjective_time_intensity_coeff": 1.0,
  "subjective_time_stability_coeff": 0.5
}
```

### Опциональные поля (можно добавить с ограничениями):
- `memory` - ограничить последние N записей (например, 10)
- `recent_events` - ограничить последние N событий (например, 10)
- `energy_history` - ограничить последние N значений (например, 50)
- `stability_history` - ограничить последние N значений (например, 50)

## План действий

1. ✅ Изучить текущую реализацию `/status` в обоих API серверах
2. ✅ Проанализировать структуру SelfState и определить transient/внутренние поля
3. ✅ Определить безопасные поля для публичного API
4. ✅ Создать документ с определением контракта
5. ⏳ (Следующий шаг) Реализовать фильтрацию полей в `main_server_api.py`
6. ⏳ (Следующий шаг) Обновить `StatusResponse` в `api.py` для расширенного контракта
7. ⏳ (Следующий шаг) Добавить опциональные параметры для ограничения больших полей
8. ⏳ (Следующий шаг) Обновить тесты для проверки контракта
9. ⏳ (Следующий шаг) Обновить документацию API

## Выводы

Текущая реализация в `main_server_api.py` возвращает все поля SelfState, включая transient и внутренние поля, что является проблемой безопасности и производительности.

Рекомендуется:
1. Создать функцию фильтрации полей для `/status`
2. Исключить все transient и внутренние поля
3. Опционально ограничить размер больших полей (memory, history)
4. Документировать контракт в API документации
