# Observation API - Устаревшая документация

## Важное уведомление

⚠️ **Эта документация устарела после архитектурных изменений 2026-01-22**

Система observability была полностью переработана для обеспечения **истинной пассивности**. Все API endpoints были удалены, чтобы исключить любое влияние на runtime loop системы Life.

## Новые принципы (после изменений)

- **Нет API endpoints** - система полностью пассивна
- **Только raw counters** - без интерпретации или derived metrics
- **Внешний анализ** - данные анализируются внешними инструментами
- **PassiveDataSink** - только принимает данные при явном вызове

## Доступ к данным

Для доступа к данным наблюдений используйте новый компонент `RawDataAccess`:

```python
from src.observability.developer_reports import RawDataAccess

# Создание экземпляра для доступа к данным
data_access = RawDataAccess()

# Получение raw наблюдений за последние часы
observations = data_access.get_raw_observation_data(hours=24)

# Получение последнего snapshot
latest_snapshot = data_access.get_raw_snapshot_data()

# Экспорт данных для внешнего анализа
data_access.export_raw_data(hours=24, output_path="raw_data_export.json")
```

## Архитектурные изменения

### Удаленные компоненты
- ❌ Все REST API endpoints (`/health`, `/metrics/current`, etc.)
- ❌ `ObservationAPI` класс
- ❌ Синхронные вызовы из runtime loop

### Новые компоненты
- ✅ `PassiveDataSink` - истинно пассивный сборщик данных
- ✅ `AsyncDataSink` - асинхронная версия с очередью и фоновой обработкой
- ✅ `AsyncObservationAPI` - единая точка входа для async операций
- ✅ `UnifiedObservationAPI` с async методами для высокопроизводительных сценариев
- ✅ `RawDataAccess` - доступ к raw данным без интерпретации
- ✅ `RawSystemCounters` - только сырые счетчики
- ✅ Внешняя интеграция без влияния на runtime

### Асинхронная архитектура (2026-01-21)

**AsyncDataSink** - асинхронная версия PassiveDataSink для высокопроизводительных сценариев:

```python
from src.observability import AsyncDataSink

# Создание асинхронного sink
async_sink = AsyncDataSink(
    data_directory="data",
    enabled=True,
    queue_size=1000  # Размер внутренней очереди
)

# Асинхронный прием данных (не блокируется)
await async_sink.accept_data_point_async({
    "timestamp": time.time(),
    "type": "high_priority_event",
    "data": {"value": 42}
}, priority=2)  # priority: 0=normal, 1=high, 2=critical

# Запуск фоновой обработки
await async_sink.start()

# Остановка с graceful shutdown
await async_sink.stop()
```

**AsyncObservationAPI** - единая точка входа для асинхронных операций:

```python
from src.observability import AsyncObservationAPI

# Создание async API
async_api = AsyncObservationAPI()

# Async context manager для автоматического управления жизненным циклом
async with async_api:
    # Асинхронное логирование события
    correlation_id = await async_api.log_event_async(event_object)

    # Асинхронный сбор данных
    success = await async_api.accept_data_point_async(data, priority=1)

    # Пакетная обработка
    accepted_count = await async_api.accept_batch_async(data_points, priority=0)
```

**UnifiedObservationAPI с async поддержкой:**

```python
from src.observability import UnifiedObservationAPI

# Создание unified API
api = UnifiedObservationAPI()

# Включение async поддержки
api.enable_async_support()

# Async context manager для управления жизненным циклом
async with api:
    # Async методы доступны параллельно с sync
    await api.accept_data_point_async(data, priority=1)
    await api.log_event_async(event)

    # Получение статуса включая async метрики
    status = await api.get_async_status()
```

#### Принципы асинхронной архитектуры:
1. **Не-блокирующий прием**: Операции никогда не блокируются на I/O
2. **Фоновая обработка**: I/O операции выполняются в фоне с батчингом
3. **Приоритизация**: Важные данные обрабатываются первыми (normal/high/critical)
4. **Graceful degradation**: Fallback на sync при проблемах
5. **Изоляция**: Async компоненты не влияют на sync операции

## Запуск сервера

```bash
# Базовый запуск на localhost:8000
python run_observation_api.py

# Запуск на определенном хосте/порту
python run_observation_api.py --host 0.0.0.0 --port 8080

# Режим разработки с перезагрузкой
python run_observation_api.py --reload
```

## Базовые endpoints

### Health Check

```http
GET /health
```

Проверка состояния API сервера.

**Ответ:**
```json
{
  "status": "healthy",
  "timestamp": 1704567890.123,
  "version": "1.0.0",
  "uptime": 3600.5
}
```

### Текущие метрики

```http
GET /metrics/current
```

Получение текущих метрик системы из последнего наблюдения.

**Ответ:**
```json
{
  "timestamp": 1704567890.123,
  "cycle_count": 1000,
  "uptime_seconds": 7200.5,
  "memory_entries_count": 500,
  "learning_effectiveness": 0.85,
  "adaptation_rate": 0.75,
  "decision_success_rate": 0.92,
  "error_count": 3,
  "integrity_score": 0.96,
  "energy_level": 0.88,
  "action_count": 250,
  "event_processing_rate": 2.5,
  "state_change_frequency": 1.8
}
```

## Анализ данных

### Анализ логов

```http
GET /observe/logs?start_time_offset=3600&end_time=1704567890.123
```

Выполнение анализа на основе логов системы.

**Параметры:**
- `start_time_offset` (float): Время в секундах от текущего момента (по умолчанию: 3600)
- `end_time` (float, optional): Время окончания анализа (timestamp)

**Ответ:** Полный отчет наблюдения (см. структуру ниже)

### Анализ снимков

```http
GET /observe/snapshots?snapshot_dir=data/snapshots&limit=50
```

Выполнение анализа на основе снимков состояния системы.

**Параметры:**
- `snapshot_dir` (str): Директория с файлами снимков (по умолчанию: "data/snapshots")
- `limit` (int, optional): Максимальное количество снимков для анализа

**Ответ:** Полный отчет наблюдения (см. структуру ниже)

## Специализированные endpoints

### Паттерны поведения

```http
GET /patterns
```

Получение текущих паттернов поведения системы.

**Ответ:**
```json
[
  {
    "pattern_type": "learning_cycle",
    "description": "Регулярные циклы обучения каждые 75 тиков",
    "frequency": 0.8,
    "impact_score": 0.7,
    "first_observed": 1704560000.0,
    "last_observed": 1704567890.123,
    "metadata": {
      "confidence": 0.85,
      "occurrences": 12
    }
  }
]
```

### Аномалии

```http
GET /anomalies
```

Получение списка текущих аномалий.

**Ответ:**
```json
{
  "anomalies": [
    {
      "type": "high_error_rate",
      "description": "Высокий уровень ошибок: 15",
      "severity": "high",
      "timestamp": 1704567890.123,
      "metric": "error_count",
      "value": 15,
      "threshold": 10
    }
  ],
  "count": 1,
  "timestamp": 1704567890.123
}
```

### Рекомендации

```http
GET /recommendations
```

Получение текущих рекомендаций по улучшению системы.

**Ответ:**
```json
{
  "recommendations": [
    "Проверить энергопотребление системы",
    "Проанализировать причины ошибок в логах"
  ],
  "count": 2,
  "timestamp": 1704567890.123
}
```

### История наблюдений

```http
GET /history/summary
```

Получение сводки по истории наблюдений.

**Ответ:**
```json
{
  "total_observations": 5,
  "average_metrics": {
    "cycle_count": 1250.0,
    "integrity_score": 0.92,
    "error_count": 2.5
  },
  "recent_trends": {
    "integrity_score": "stable",
    "energy_level": "improving",
    "error_count": "declining"
  },
  "observation_period": {
    "earliest": 1704500000.0,
    "latest": 1704567890.123
  }
}
```

## Структура данных

### Полный отчет наблюдения (ObservationReport)

```json
{
  "observation_period": [1704560000.0, 1704567890.123],
  "metrics_summary": {
    "timestamp": 1704567890.123,
    "cycle_count": 1000,
    "uptime_seconds": 7200.5,
    "memory_entries_count": 500,
    "learning_effectiveness": 0.85,
    "adaptation_rate": 0.75,
    "decision_success_rate": 0.92,
    "error_count": 3,
    "integrity_score": 0.96,
    "energy_level": 0.88,
    "action_count": 250,
    "event_processing_rate": 2.5,
    "state_change_frequency": 1.8
  },
  "behavior_patterns": [
    {
      "pattern_type": "learning_cycle",
      "description": "Регулярные циклы обучения",
      "frequency": 0.8,
      "impact_score": 0.7,
      "first_observed": 1704560000.0,
      "last_observed": 1704567890.123,
      "metadata": {}
    }
  ],
  "trends": {
    "integrity_score": "stable",
    "energy_level": "improving",
    "error_count": "declining"
  },
  "anomalies": [
    {
      "type": "high_error_rate",
      "description": "Высокий уровень ошибок: 15",
      "severity": "high",
      "timestamp": 1704567890.123
    }
  ],
  "recommendations": [
    "Проверить энергопотребление системы",
    "Проанализировать причины ошибок в логах"
  ]
}
```

## Ошибки и обработка

API использует стандартные HTTP коды ошибок:

- `200`: Успешный запрос
- `400`: Некорректные параметры запроса
- `404`: Ресурс не найден
- `500`: Внутренняя ошибка сервера

**Структура ответа об ошибке:**
```json
{
  "error": "Описание ошибки",
  "detail": "Дополнительная информация",
  "timestamp": 1704567890.123
}
```

## Примеры использования

### Python клиент

```python
import requests
import json

# Получение текущих метрик
response = requests.get("http://localhost:8000/metrics/current")
metrics = response.json()
print(f"Integrity Score: {metrics['integrity_score']:.2%}")

# Анализ логов за последний час
response = requests.get("http://localhost:8000/observe/logs?start_time_offset=3600")
report = response.json()
print(f"Patterns found: {len(report['behavior_patterns'])}")

# Получение рекомендаций
response = requests.get("http://localhost:8000/recommendations")
recommendations = response.json()
for rec in recommendations['recommendations']:
    print(f"• {rec}")
```

### curl примеры

```bash
# Проверка здоровья
curl http://localhost:8000/health

# Текущие метрики
curl http://localhost:8000/metrics/current

# Анализ логов
curl "http://localhost:8000/observe/logs?start_time_offset=3600"

# Паттерны поведения
curl http://localhost:8000/patterns

# История наблюдений
curl http://localhost:8000/history/summary
```

### JavaScript клиент

```javascript
// Получение метрик
fetch('http://localhost:8000/metrics/current')
  .then(response => response.json())
  .then(metrics => {
    console.log(`System integrity: ${metrics.integrity_score}`);
  });

// Анализ снимков
fetch('http://localhost:8000/observe/snapshots?snapshot_dir=data/snapshots')
  .then(response => response.json())
  .then(report => {
    console.log(`Analysis complete. Anomalies: ${report.anomalies.length}`);
  });
```

## Производительность

### Ограничения
- **Анализ логов**: Ограничен последними 24 часами для производительности
- **Анализ снимков**: Максимум 100 снимков за один запрос
- **Rate limiting**: Не более 10 запросов в минуту для тяжелых операций

### Оптимизации
- **Кэширование**: Результаты анализа кэшируются на 5 минут
- **Асинхронная обработка**: Длительные операции выполняются в фоне
- **Streaming**: Поддержка потоковой обработки больших объемов данных

## Безопасность

### Аутентификация
API не требует аутентификации для базового доступа. Для продакшена рекомендуется добавить:

- API ключи
- JWT токены
- OAuth 2.0

### Валидация
- Все входные параметры валидируются
- SQL injection protection встроена в FastAPI
- XSS protection через автоматическое экранирование

### Мониторинг
- Все запросы логируются
- Метрики производительности собираются автоматически
- Алерты при высокой нагрузке

## Интеграция с другими системами

### Prometheus метрики

API может экспортировать метрики в формате Prometheus:

```bash
curl http://localhost:8000/metrics/prometheus
```

### Webhook уведомления

Настройка webhook для алертов:

```python
webhook_config = {
    "url": "https://your-monitoring.com/webhook",
    "triggers": {
        "integrity_score": {"threshold": 0.3, "condition": "below"},
        "error_count": {"threshold": 10, "condition": "above"}
    }
}
```

### Интеграция с Grafana

API совместим с Grafana для создания дашбордов:

1. Настройте источник данных JSON API
2. Используйте endpoints для получения метрик
3. Создайте панели для визуализации трендов

## Тестирование API

### Unit тесты

```bash
# Запуск тестов API
pytest src/test/test_observation_api.py -v
```

### Integration тесты

```python
def test_api_endpoints():
    # Тест всех основных endpoints
    response = requests.get("http://localhost:8000/health")
    assert response.status_code == 200

    response = requests.get("http://localhost:8000/metrics/current")
    assert response.status_code == 200

    # Тест с некорректными параметрами
    response = requests.get("http://localhost:8000/observe/logs?start_time_offset=-1")
    assert response.status_code == 400
```

### Load testing

```bash
# Тестирование производительности
ab -n 1000 -c 10 http://localhost:8000/metrics/current
```

## Мониторинг API

### Метрики сервера
- **Response time**: Среднее время ответа
- **Error rate**: Процент ошибочных ответов
- **Throughput**: Количество запросов в секунду

### Логи
```
2026-01-21 10:30:15 INFO API request: GET /metrics/current - 200 OK - 45ms
2026-01-21 10:30:16 INFO API request: GET /observe/logs - 200 OK - 1250ms
2026-01-21 10:30:17 ERROR API request: GET /observe/snapshots - 404 Not Found - Invalid snapshot directory
```

### Алерты
- Response time > 5 секунд
- Error rate > 5%
- Server unavailable

## Расширение API

### Добавление новых endpoints

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/custom/metrics")
async def get_custom_metrics():
    # Кастомная логика анализа
    return {"custom_metric": 42}

# Регистрация роутера
app.include_router(router, prefix="/custom")
```

### Кастомные middleware

```python
from fastapi.middleware.base import BaseHTTPMiddleware

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Логика middleware
        response = await call_next(request)
        return response

app.add_middleware(LoggingMiddleware)
```

## Troubleshooting

### Распространенные проблемы

**500 Internal Server Error**
- Проверьте логи сервера
- Убедитесь в доступности файлов логов/снимков
- Проверьте права доступа к директориям

**404 Not Found**
- Проверьте корректность URL
- Убедитесь, что сервер запущен на правильном порту
- Проверьте конфигурацию маршрутов

**Timeout errors**
- Увеличьте timeout для длительных операций
- Оптимизируйте запросы (меньше данных)
- Рассмотрите асинхронную обработку

### Debug режим

```bash
# Запуск с подробным логированием
python run_observation_api.py --debug

# Проверка логов
tail -f observation_api.log
```

## Будущие улучшения

### Планируемые фичи
- **WebSocket поддержка**: Реальное время обновления метрик
- **GraphQL API**: Более гибкие запросы данных
- **API versioning**: Поддержка нескольких версий API
- **Rate limiting**: Защита от перегрузки
- **Caching layer**: Redis для кэширования результатов

### Совместимость
- **OpenAPI 3.0**: Полная спецификация API
- **REST стандарты**: Соблюдение REST принципов
- **JSON Schema**: Валидация структур данных

## См. также

- [ExternalObserver](external_observer.md) - Основной компонент наблюдения
- [Reporting System](reporting.md) - Генерация отчетов
- [Analysis Tools](analysis_tools.md) - CLI инструменты анализа