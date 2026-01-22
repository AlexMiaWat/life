# AsyncDataSink - Асинхронный сборщик данных

## Обзор

`AsyncDataSink` - асинхронный компонент для сбора данных наблюдений. Использует `AsyncDataQueue` для асинхронной обработки данных без блокировки runtime loop. Обновлен для улучшения совместимости с тестами.

## Архитектурный статус

⚠️ **Устаревший компонент** - рекомендуется использовать `StructuredLogger` как основной компонент наблюдаемости.

Несмотря на статус, AsyncDataSink поддерживается для совместимости с существующими тестами и legacy кодом.

## Основные возможности

### Инициализация

```python
from src.observability.async_data_sink import AsyncDataSink

# Базовая инициализация
sink = AsyncDataSink(
    data_directory="data",
    enabled=True,
    max_queue_size=1000,
    flush_interval=5.0
)

# С дополнительными параметрами для тестов
sink = AsyncDataSink(
    data_directory="data",
    enabled=True,
    max_queue_size=1000,
    flush_interval=5.0,
    processing_interval=5.0  # Для совместимости с тестами
)
```

### Фабричная функция

```python
from src.observability.async_data_sink import create_async_data_sink

# Создание через фабричную функцию
sink = create_async_data_sink(
    data_directory="data",
    enabled=True,
    max_queue_size=1000,
    flush_interval=5.0,
    processing_interval=5.0
)
```

### Получение недавних данных

```python
# Получение всех недавних данных
recent_data = sink.get_recent_data()

# Получение ограниченного количества
last_10_events = sink.get_recent_data(limit=10)
```

## Совместимость с тестами

AsyncDataSink был обновлен для улучшения совместимости с автоматизированными тестами:

- **processing_interval**: Параметр для управления интервалом обработки
- **get_recent_data()**: Метод для получения недавних данных в тестах
- **create_async_data_sink()**: Фабричная функция для унифицированного создания

## Использование в тестах

```python
import pytest
from src.observability.async_data_sink import create_async_data_sink

@pytest.fixture
def async_sink():
    """Фикстура для тестирования AsyncDataSink."""
    return create_async_data_sink(
        data_directory="test_data",
        enabled=True,
        max_queue_size=100,
        flush_interval=1.0,
        processing_interval=1.0
    )

def test_async_data_collection(async_sink):
    """Тест сбора данных."""
    # Тестирование логирования
    async_sink.log_event({"test": "data"})

    # Получение данных для проверки
    recent = async_sink.get_recent_data()
    assert len(recent) > 0
```

## Миграция на StructuredLogger

Для новых разработок рекомендуется использовать `StructuredLogger`:

```python
# Вместо AsyncDataSink
from src.observability.structured_logger import StructuredLogger

logger = StructuredLogger()
logger.log_event({
    "stage": "test",
    "data": {"test": "value"},
    "correlation_id": "test-123"
})
```

## Архитектурные ограничения

- **Не рекомендуется для production**: Используйте `StructuredLogger`
- **Ограниченная функциональность**: Поддерживается только базовый сбор данных
- **Без анализа**: Только сбор, без обработки или интерпретации данных

## Будущие планы

AsyncDataSink планируется к удалению в будущих версиях. Все новые возможности наблюдаемости должны реализовываться через `StructuredLogger`.