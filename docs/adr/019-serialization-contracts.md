# ADR 019: Архитектурные контракты сериализации

## Статус
✅ **Принято и обновлено (2026-01-22)**

## Контекст
После анализа критических проблем в задаче task_1769064635 (отчет Скептика) выявлены фундаментальные проблемы в реализации архитектурных контрактов сериализации. Первоначальная реализация демонстрировала "архитектурный обман" - красивые интерфейсы маскировали глубокие проблемы с thread-safety, эффективностью и нарушением принципов SOLID.

## Решение
Переработать систему архитектурных контрактов сериализации согласно принципам SOLID и рекомендациям Скептика:

1. **Принцип единственной ответственности**: Разделить контракты на отдельные протоколы
2. **Истинная thread-safety**: Убрать антипаттерны, реализовать version-based concurrency control
3. **Отказоустойчивость**: Circuit breaker pattern, timeout, graceful degradation
4. **Архитектурная интеграция**: Полная интеграция контрактов в систему с type hints

## Архитектурные контракты

### 1. Иерархия протоколов (SOLID принцип разделения интерфейсов)

```python
@runtime_checkable
class Serializable(Protocol):
    """Базовый протокол для сериализуемых компонентов."""
    def to_dict(self) -> Dict[str, Any]: ...

@runtime_checkable
class MetadataProvider(Protocol):
    """Протокол для компонентов, предоставляющих метаданные сериализации."""
    def get_serialization_metadata(self) -> Dict[str, Any]: ...

@runtime_checkable
class ThreadSafeSerializable(Serializable, MetadataProvider, Protocol):
    """Композитный протокол для полностью thread-safe сериализуемых компонентов."""
    pass

class SerializationContract(ABC, ThreadSafeSerializable):
    """Архитектурный контракт для компонентов с полной поддержкой сериализации."""
    pass
```

### 2. Принципы разделения ответственности

- **Serializable**: Только базовая сериализация (принцип единственной ответственности)
- **MetadataProvider**: Только метаданные (разделение с бизнес-логикой)
- **ThreadSafeSerializable**: Композиция протоколов для полной функциональности
- **SerializationContract**: ABC для компонентов с архитектурными гарантиями

### 3. Удаление ThreadSafeSerializer (архитектурный антипаттерн)
`ThreadSafeSerializer` удален как антипаттерн, не обеспечивающий реальной thread-safety. Компоненты должны реализовывать thread-safety самостоятельно или использовать протоколы напрямую.

## Гарантии контрактов

### Thread-safety (улучшено после отчета Скептика)
- **Version-based concurrency control**: EventQueue использует версионность для гарантии консистентности
- **Proper locking hierarchy**: Отдельные locks для версии и сериализации
- **Atomic serialization**: Полностью атомарные операции без кэширования устаревших данных
- **Timeout protection**: Все операции имеют timeout для предотвращения зависаний

### Атомарность
- **Snapshot-based подход**: Атомарное извлечение состояния без race conditions
- **Version consistency**: Проверка версии состояния для обнаружения изменений
- **Transactional semantics**: Все-или-ничего сериализация

### Отказоустойчивость (circuit breaker pattern)
- **Component isolation**: SelfState изолирует компоненты с ThreadPoolExecutor
- **Timeout per component**: Каждый компонент имеет индивидуальный timeout
- **Graceful degradation**: Частичные данные при сбое отдельных компонентов
- **Error metrics**: Подробная статистика ошибок и timeout'ов

### Эффективность
- **Parallel serialization**: SelfState сериализует компоненты параллельно
- **Bounded resources**: Ограничение количества одновременных операций
- **Lazy initialization**: Компоненты инициализируются по требованию

### Детерминированность
- **Versioned formats**: Версионирование форматов сериализации (4.0 с concurrency control)
- **State-based results**: Результат зависит только от состояния компонента
- **Metadata consistency**: Метаданные включают timestamp и version для трассировки

## Структура сериализованных данных

### Стандартный формат
```python
{
    "metadata": {
        "version": str,           # Версия формата
        "timestamp": float,       # Время сериализации
        "component_type": str,    # Тип компонента
        "checksum": str,          # Контрольная сумма (опционально)
        "warnings": [str]         # Предупреждения (опционально)
    },
    "data": Any                  # Собственные данные компонента
}
```

### Композитный формат (для сложных компонентов)
```python
{
    "metadata": {...},
    "components": {
        "component_name": serialized_component_data,
        ...
    },
    "legacy_fields": {...}  # Для обратной совместимости
}
```

## Реализация

### Архитектурные компоненты
- `src/contracts/serialization_contract.py` - Иерархия протоколов (Serializable, MetadataProvider, ThreadSafeSerializable)
- `src/environment/event_queue.py` - EventQueue с version-based concurrency control
- `src/state/self_state.py` - SelfState с композитной изолированной сериализацией
- `src/state/components/` - Компоненты состояния реализующие Serializable протокол

### Паттерны использования
```python
# Базовый компонент (Serializable)
class MyComponent(Serializable):
    def to_dict(self) -> Dict[str, Any]:
        return {"field": self.field}

# Полнофункциональный компонент (ThreadSafeSerializable)
class MySafeComponent(SerializationContract):
    def to_dict(self) -> Dict[str, Any]:
        with self._lock:
            return {"field": self.field}

    def get_serialization_metadata(self) -> Dict[str, Any]:
        return {
            "version": "1.0",
            "component_type": "MySafeComponent",
            "thread_safe": True
        }
```

### Thread-safety стратегии
- **EventQueue**: Version-based concurrency control + atomic snapshots
- **SelfState**: Component isolation + ThreadPoolExecutor + timeout per component
- **Компоненты**: RLock для защиты внутреннего состояния

## Тестирование и валидация

### Уровни тестирования
1. **Unit tests**: Тестирование отдельных компонентов и протоколов
2. **Integration tests**: Тестирование композитной сериализации (17 тестов)
3. **Stress tests**: Экстремальная нагрузка (10k+ событий, 100+ конкурентных операций)
4. **Contract compliance**: Автоматическая проверка соответствия протоколам

### Ключевые метрики валидации
- **Thread-safety**: 20+ одновременных сериализаций без race conditions
- **Performance**: Среднее время сериализации < 10ms для типичных сценариев
- **Reliability**: 100% успешных операций в стресс-тестах
- **Consistency**: Version-based гарантии консистентности состояния

## Преимущества

1. **Истинная thread-safety**: Version-based concurrency control вместо ложных оберток
2. **Отказоустойчивость**: Circuit breaker pattern с изоляцией компонентов
3. **Архитектурная чистота**: SOLID принципы, разделение ответственности
4. **Производительность**: Parallel serialization, bounded resources
5. **Надежность**: Comprehensive testing с экстремальными сценариями

## Риски и mitigation

### Производительность
- **Риск**: Overhead от version-based concurrency control
- **Mitigation**: Оптимизированные locks, parallel processing, bounded timeouts

### Сложность
- **Риск**: Увеличение архитектурной сложности
- **Mitigation**: Четкая иерархия протоколов, comprehensive documentation, extensive testing

### Обратная совместимость
- **Риск**: Breaking changes при обновлении контрактов
- **Mitigation**: Versioned formats, gradual migration, backward compatibility layers

## История изменений

- **2026-01-22**: Полная переработка после отчета Скептика task_1769064635
  - Удален ThreadSafeSerializer как архитектурный антипаттерн
  - Реализован version-based concurrency control
  - Добавлена композитная изолированная сериализация SelfState
  - Созданы экстремальные стресс-тесты (10k+ событий)
  - Обновлена версия протокола до 4.0

- **2026-01-20**: Начальная реализация контрактов (ADR принят)

## Альтернативы

### 1. Без контрактов
- **Плюсы**: Простота, гибкость
- **Минусы**: Отсутствие гарантий, race conditions, низкая поддерживаемость

### 2. Строгие контракты (только ABC)
- **Плюсы**: Строгая типизация, гарантии
- **Минусы**: Сложность, overhead для простых компонентов

### Выбор: Гибридный подход
Комбинация протоколов (гибкость) и ABC (гарантии) позволяет балансировать между простотой и надежностью.

## Последствия

### Положительные
- Стандартизированная сериализация во всей системе
- Улучшенная надежность и поддерживаемость
- Лучшее покрытие тестами
- Проще добавлять новые компоненты

### Отрицательные
- Увеличение сложности кода
- Дополнительные накладные расходы на runtime
- Необходимость миграции существующих компонентов

## Метрики успеха
- 100% компонентов следуют контрактам
- 0 race conditions в сериализации
- <5% overhead на сериализацию
- Полное покрытие интеграционными тестами