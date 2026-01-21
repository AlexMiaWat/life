# ADR 011: SelfState Improvements

## Статус
✅ Принято

## Дата
2026-01-20

## Контекст

Проект Life требовал надежного управления состоянием системы SelfState. Исходная реализация имела критические проблемы:

### Проблемы до улучшений
- **Отсутствие валидации**: поля могли принимать некорректные значения (energy > 100, integrity < 0)
- **Нет защиты от изменений**: прямой доступ к полям без контроля
- **Отсутствие логирования**: невозможно отследить изменения состояния
- **Нет проверки жизнеспособности**: неясно, когда система "мертва"
- **Thread-safety проблемы**: конкурентный доступ к состоянию через API

### Архитектурные требования
- **Целостность данных**: валидация всех изменений состояния
- **Thread-safety**: безопасный доступ из разных потоков
- **Наблюдаемость**: логирование изменений для отладки
- **Надежность**: защита от некорректных состояний
- **Производительность**: минимальный overhead на валидацию

## Решение

### Архитектура улучшений SelfState

#### 1. Централизованная валидация через FieldValidator

```python
class FieldValidator:
    """Валидатор полей SelfState с поддержкой clamping"""

    FIELD_BOUNDS = {
        "energy": (0.0, 100.0),
        "integrity": (0.0, 1.0),
        "stability": (0.0, 1.0),
        "last_event_intensity": (0.0, 1.0),
    }

    NON_NEGATIVE_FIELDS = [
        "fatigue", "tension", "age", "subjective_time",
        "subjective_time_base_rate", "subjective_time_rate_min"
    ]

    INT_FIELDS = ["ticks", "clarity_duration"]
```

#### 2. Защита полей через переопределение __setattr__

```python
def __setattr__(self, name: str, value) -> None:
    """Переопределение setattr для валидации и защиты полей"""

    # Валидация и clamping для числовых полей
    if name in ["energy", "integrity", "stability"]:
        value = self._validate_field(name, value, clamp=True)

    # Защита immutable полей
    if name in ["life_id", "birth_timestamp"] and self._initialized:
        raise AttributeError(f"Cannot modify immutable field '{name}'")

    # Thread-safety через RLock
    with self._api_lock:
        object.__setattr__(self, name, value)
        self._log_change(name, old_value, value)
```

#### 3. Метод apply_delta с безопасным обновлением

```python
def apply_delta(self, deltas: dict[str, float]) -> None:
    """Применение дельт с clamping и логированием"""
    with self._api_lock:
        for key, delta in deltas.items():
            current = getattr(self, key)
            new_value = current + delta

            # Clamping для vital параметров
            if key in ["energy", "integrity", "stability"]:
                clamped_value = max(0.0, min({"energy": 100.0, "integrity": 1.0, "stability": 1.0}[key], new_value))
                object.__setattr__(self, key, clamped_value)
                self._log_change(key, current, clamped_value)
```

#### 4. Проверка жизнеспособности is_active/is_viable

```python
def is_active(self) -> bool:
    """Проверка жизнеспособности - vital параметры выше порогов"""
    return self.is_viable()

def is_viable(self) -> bool:
    """Строгая проверка: energy > 0, integrity > 0, stability > 0"""
    return (
        self.energy > 0 and
        self.integrity > 0 and
        self.stability > 0
    )
```

#### 5. Append-only логирование изменений

```python
def _log_change(self, field_name: str, old_value, new_value) -> None:
    """Логирование в append-only JSONL файл"""
    log_entry = {
        "timestamp": time.time(),
        "life_id": self.life_id,
        "field": field_name,
        "old_value": old_value,
        "new_value": new_value
    }
    self._log_buffer.append(log_entry)
    if len(self._log_buffer) >= self._log_buffer_size:
        self._flush_log_buffer()
```

#### 6. Thread-safety через RLock

```python
_api_lock: threading.RLock = field(default_factory=threading.RLock)

# Все изменения состояния защищены блокировкой
with self._api_lock:
    # критическая секция
    object.__setattr__(self, name, value)
```

### Ключевые компоненты

#### FieldValidator
- **Централизованная логика**: все правила валидации в одном месте
- **Поддержка clamping**: обрезание значений вместо исключений
- **Типобезопасность**: проверка типов для int/float полей
- **Расширяемость**: легкое добавление новых полей

#### Защита immutable полей
- **life_id и birth_timestamp**: устанавливаются при создании, не изменяются
- **Валидация при загрузке**: корректная обработка при load_snapshot
- **Исключения при попытке изменения**: четкая индикация ошибки

#### Логирование изменений
- **Append-only**: невозможно потерять или изменить историю
- **Батчинг**: буфер для производительности
- **Ротация**: автоматическое управление размером файлов
- **Фильтрация**: опция логирования только критичных полей

#### Thread-safety
- **RLock**: рекурсивная блокировка для API доступа
- **Минимальный scope**: блокировки только на время изменения
- **API совместимость**: не ломает существующий код

### Интеграция в систему

#### Runtime Loop
```python
# Каждый тик обновляется состояние с валидацией
self_state.apply_delta({"ticks": 1})
self_state.apply_delta({"age": dt})
self_state.apply_delta({"subjective_time": dt})
```

#### API Endpoints
```python
# Thread-safe доступ к состоянию
@app.get("/status")
def get_status():
    with self_state._api_lock:
        return self_state.to_dict()
```

#### Snapshot система
```python
# Валидация при загрузке из snapshot
def _load_snapshot_from_data(self, data: dict) -> SelfState:
    # Валидация learning_params и adaptation_params
    validated_learning = self._validate_learning_params(data.get("learning_params", {}))
    validated_adaptation = self._validate_adaptation_params(data.get("adaptation_params", {}))
```

## Обоснование

### За выбранное решение

#### ✅ Целостность данных
- **Валидация всех изменений**: невозможны некорректные состояния
- **Clamping вместо исключений**: graceful degradation при ошибках
- **Type safety**: защита от неправильных типов данных

#### ✅ Thread-safety
- **RLock для API**: безопасный конкурентный доступ
- **Минимальный overhead**: блокировки только при изменении
- **Backward compatibility**: существующий код работает без изменений

#### ✅ Наблюдаемость и отладка
- **Полная история изменений**: append-only логи всех модификаций
- **Фильтрация по критичности**: возможность логирования только vital параметров
- **Performance monitoring**: возможность анализа паттернов изменений

#### ✅ Надежность системы
- **Защита immutable полей**: life_id и birth_timestamp не изменяются
- **Проверка жизнеспособности**: явные методы is_active/is_viable
- **Graceful handling**: система продолжает работать при проблемах

#### ✅ Производительность
- **Батчинг логов**: накопление записей перед записью на диск
- **Ленивая ротация**: проверка размера файла только при записи
- **Опциональное логирование**: возможность отключения для тестов

### Против альтернатив

#### Альтернатива 1: Валидация через сеттеры
- **Против**: Требует изменения всех мест использования
- **Против**: Легко обойти валидацию прямым доступом
- **Против**: Не обеспечивает thread-safety

#### Альтернатива 2: Immutable SelfState
- **Против**: Требует создания нового объекта при каждом изменении
- **Против**: Высокий overhead на сборку мусора
- **Против**: Сложность для больших объектов

#### Альтернатива 3: Валидация только в API слое
- **Против**: Не защищает от изменений внутри системы
- **Против**: Runtime loop может создать некорректное состояние
- **Против**: Нет гарантии целостности

## Последствия

### Положительные

#### ✅ Надежность системы
- **Невозможны некорректные состояния**: energy не может быть > 100 или < 0
- **Thread-safe API**: безопасный доступ из веб-интерфейса
- **Graceful degradation**: система работает даже при проблемах

#### ✅ Улучшенная отладка
- **Полная traceability**: каждое изменение состояния логируется
- **Исторический анализ**: возможность анализа паттернов поведения
- **Performance profiling**: отслеживание частоты изменений

#### ✅ Лучшая архитектура
- **Separation of concerns**: валидация отделена от бизнес-логики
- **Testability**: легкое тестирование валидации изолированно
- **Maintainability**: централизованная логика валидации

#### ✅ API совместимость
- **Backward compatible**: существующий код работает без изменений
- **Опциональные фичи**: логирование можно отключить
- **Performance tuning**: настройка буфера и фильтрации

### Отрицательные

#### ⚠️ Overhead на валидацию
- **Каждое изменение**: проходит через __setattr__ с валидацией
- **Блокировка**: RLock добавляет небольшие задержки
- **Логирование**: запись на диск при каждом изменении

#### ⚠️ Сложность отладки
- **Рекурсивные блокировки**: возможны deadlock при неправильном использовании
- **Логи в разных местах**: state_changes.jsonl + обычные логи
- **Большие лог-файлы**: ротация нужна для управления размером

#### ⚠️ Изменение поведения
- **Строгая валидация**: старый код может начать падать при некорректных значениях
- **Immutable поля**: некоторые тесты могут требовать переписывания
- **Thread-safety**: возможны проблемы с производительностью при высокой нагрузке

### Риски

#### Риск производительности
- **Описание**: Валидация на каждом изменении может замедлить систему
- **Митигация**: опциональное отключение логирования, батчинг
- **Вероятность**: Низкая (валидация минимальна)

#### Риск сложности
- **Описание**: Переопределение __setattr__ делает код сложнее
- **Митигация**: хорошая документация, тесты, code review
- **Вероятность**: Средняя

#### Риск потери логов
- **Описание**: Сбой при записи может потерять буфер логов
- **Митигация**: регулярный flush, обработка исключений
- **Вероятность**: Низкая

## Связанные документы

- [docs/architecture/overview.md](../architecture/overview.md) — обзор архитектуры
- [src/state/self_state.py](../../src/state/self_state.py) — реализация SelfState
- [src/validation/field_validator.py](../../src/validation/field_validator.py) — FieldValidator
- [src/test/test_state.py](../../src/test/test_state.py) — тесты SelfState
- [src/runtime/loop.py](../../src/runtime/loop.py) — использование в runtime loop
- [src/main_server_api.py](../../src/main_server_api.py) — API с thread-safety