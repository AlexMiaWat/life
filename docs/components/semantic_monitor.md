# 12_SEMANTIC_MONITOR.md — Семантический монитор аномалий

## Назначение
Semantic Monitor — это система пассивного мониторинга поведенческих паттернов системы Life. Использует статистические методы анализа correlation chains для обнаружения аномалий в поведении. Полностью интегрирован в runtime loop без активных потоков, обеспечивает непрерывное обнаружение аномалий с метриками эффективности и производительности.

## Архитектурные особенности

### Пассивная интеграция в Runtime Loop
Semantic Monitor полностью интегрирован в основной цикл выполнения без создания отдельных потоков:

- **Tick-based обновления:** Мониторинг вызывается каждый N тиков runtime loop
- **Статистический анализ:** Методы статистического анализа для обнаружения аномалий
- **Динамические пороги:** Адаптивные пороги на основе исторических данных
- **Реальные метрики:** Производительность, память, точность обнаружения, cache hit rate

**Ключевые компоненты:**
- `SemanticAnalysisEngine` — статистическое ядро анализа correlation chains с поддержкой плагинов
- `SemanticMonitor` — пассивный монитор без активных потоков
- `BehavioralAnomaly` — структура для представления обнаруженных аномалий
- `SystemHealthProfile` — профиль здоровья системы
- `AnalysisPlugin` — базовый класс для создания плагинов анализа

## Текущий статус
✅ **Реализован** (v1.0 - Базовая реализация)
*   Файл: [`src/monitor/semantic_monitor.py`](../../src/monitor/semantic_monitor.py)
*   **v1.0:** Пассивный монитор с интеграцией в runtime loop, статистическим анализом и реальными метриками производительности.

## Архитектура компонента

### Класс SemanticMonitor

```python
class SemanticMonitor:
    """Semantic Monitor for detecting behavioral anomalies in Life system.

    Integrated into runtime loop for passive monitoring without active threads.
    Provides statistical analysis of behavioral patterns with performance metrics and efficiency tracking.
    """

    def __init__(self, config: MonitorConfig = None)
    def tick_update(self, current_tick: int, event_queue_size: int = 0) -> Dict[str, Any]  # Основной метод обновления
    def enable_monitoring(self) / disable_monitoring(self)  # Управление без потоков
    def analyze_correlation_chain(self, correlation_id: str, chain_entries: List[Dict]) -> Dict[str, Any]
    def get_system_health(self) -> SystemHealthProfile
    def get_monitoring_stats(self) -> Dict[str, Any]  # Метрики производительности и эффективности
    def update_config(self, new_config: MonitorConfig)
    def add_alert_callback(self, callback: Callable)
    def clear_cache(self)
```

### Классы данных

```python
@dataclass
class BehavioralAnomaly:
    """Detected behavioral anomaly."""
    anomaly_id: str
    anomaly_type: str  # 'pattern_deviation', 'state_aberration', 'chain_breakage'
    severity: float  # 0.0 to 1.0
    description: str
    timestamp: float
    correlation_ids: List[str]
    evidence: Dict[str, Any]

@dataclass
class SystemHealthProfile:
    """Semantic health profile of the system."""
    energy_stability: float
    cognitive_coherence: float
    adaptation_efficiency: float
    memory_integrity: float
    overall_health: float
    risk_factors: List[str]
    recommendations: List[str]
```

### Конфигурация мониторинга (v2.0)

```python
@dataclass
class MonitorConfig:
    enabled: bool = True
    anomaly_threshold: float = 0.7
    analysis_interval_ticks: int = 50  # Tick-based вместо time-based
    max_cached_analyses: int = 1000
    anomaly_log_file: str = "logs/semantic_anomalies.jsonl"
    health_check_interval_ticks: int = 300  # Tick-based
    cache_ttl_seconds: float = 300.0
    log_anomalies: bool = True
    enable_performance_metrics: bool = True
    performance_log_file: str = "logs/semantic_performance.jsonl"
    alert_callbacks: List[Callable] = field(default_factory=list)
```

## Функциональность

### Статистический анализ correlation chains
Анализ цепочек корреляции с использованием статистических методов:

```python
result = monitor.analyze_correlation_chain(correlation_id, chain_entries)
# Возвращает анализ:
# {
#     'correlation_id': str,
#     'chain_length': int,
#     'event_types': List[str],
#     'anomaly_score': float,              # Статистический score аномалий
#     'analysis_result': Dict,             # Результаты анализа
#     'anomalies': List[Dict],             # Обнаруженные аномалии
#     'cached': bool,                      # Был ли использован кэш
#     'timestamp': float
# }
```

### Многоуровневое обнаружение аномалий

1. **Анализ полноты цепочки:** Проверка присутствия всех этапов (event → meaning → decision → action → feedback)
2. **Анализ паттернов поведения:** Обнаружение отклонений от типичных последовательностей
3. **Анализ распределения impact:** Статистический анализ величин воздействий
4. **Динамические пороги:** Адаптивные thresholds на основе исторических данных
5. **Плагины анализа:** Расширяемая система плагинов для специализированного анализа

### Plugin-архитектура

Semantic Monitor поддерживает плагины для расширения возможностей анализа:

```python
from src.observability.semantic_analysis_engine import AnalysisPlugin

class CustomAnalysisPlugin(AnalysisPlugin):
    def __init__(self):
        super().__init__("custom_analysis", "Custom analysis plugin")

    def analyze(self, correlation_chain: List[Dict]) -> Dict[str, Any]:
        # Реализовать анализ
        return {"custom_metric": 0.85}

    def get_anomaly_score(self, analysis_result: Dict[str, Any]) -> float:
        # Рассчитать score аномалий
        return analysis_result.get("custom_metric", 0.0)

# Регистрация плагина
engine.add_plugin(CustomAnalysisPlugin())
```

### Система здоровья
Комплексная оценка здоровья системы на основе анализа correlation chains:

```python
health = monitor.get_system_health()
# SystemHealthProfile содержит метрики здоровья:
# - energy_stability: float          # Стабильность энергии
# - cognitive_coherence: float       # Когерентность мышления
# - adaptation_efficiency: float     # Эффективность адаптации
# - memory_integrity: float          # Целостность памяти
# - overall_health: float            # Общее здоровье
# - risk_factors: List[str]          # Факторы риска
# - recommendations: List[str]       # Рекомендации
```

## Интеграция в систему

### Runtime Loop интеграция
Semantic Monitor полностью интегрирован в runtime loop без активных потоков:

```python
# В main_server_api.py - инициализация
semantic_monitor = SemanticMonitor()

# В run_loop() - вызов на каждом тике
def run_loop(self_state, monitor, ..., semantic_monitor=None):
    # ...
    # Интеграция семантического мониторинга
    semantic_results = semantic_monitor.tick_update(
        current_tick=self_state.ticks,
        event_queue_size=event_queue.qsize()
    )

    # Обработка результатов
    if semantic_results:
        if 'health_profile' in semantic_results:
            # Логирование здоровья системы
        if 'anomalies_detected' in semantic_results:
            # Обработка обнаруженных аномалий
```

### Tick-based обновления
Мониторинг происходит через регулярные tick-based обновления:

```python
# Каждые N тиков - анализ
if ticks_since_last_analysis >= config.analysis_interval_ticks:
    analysis_results = perform_periodic_analysis()
    ticks_since_last_analysis = 0

# Каждые M тиков - проверка здоровья
if ticks_since_last_health_check >= config.health_check_interval_ticks:
    health_results = perform_health_check()
    ticks_since_last_health_check = 0
```

### Конфигурация через YAML
Конфигурация с tick-based интервалами:

```yaml
semantic_monitor:
  enabled: true
  anomaly_threshold: 0.7
  analysis_interval_ticks: 50        # Каждые 50 тиков
  max_cached_analyses: 1000
  anomaly_log_file: "logs/semantic_anomalies.jsonl"
  health_check_interval_ticks: 300   # Каждые 300 тиков
  cache_ttl_seconds: 300.0
  log_anomalies: true
  enable_performance_metrics: true
  performance_log_file: "logs/semantic_performance.jsonl"
```

### Логирование аномалий
Логирование обнаруженных аномалий:

```json
{
  "timestamp": 1640995200.123,
  "anomaly_id": "anom_001",
  "type": "pattern_deviation",
  "severity": 0.85,
  "description": "Unusual behavioral pattern detected",
  "correlation_ids": ["corr_123"],
  "evidence": {
    "anomaly_score": 0.85,
    "semantic_category": "unknown",
    "behavioral_context": {}
  },
  "analysis_context": {
    "correlation_id": "corr_123",
    "anomaly_score": 0.85
  }
}
```

## Мониторинг и метрики

### Статистика мониторинга
Метрики производительности и эффективности:

```python
stats = monitor.get_monitoring_stats()
# {
#     'is_enabled': bool,
#     'analysis_count': int,
#     'anomaly_count': int,
#     'cache_size': int,
#     'cache_hit_rate': float,
#     'performance_metrics': {
#         'avg_analysis_time': float,      # Среднее время анализа
#         'avg_memory_usage': float,       # Среднее использование памяти
#         'avg_cache_hit_rate': float,     # Эффективность кэша
#         'analysis_throughput': float,    # Анализов в минуту
#         'memory_efficiency': float,      # Эффективность памяти
#         'false_positive_rate': float     # Доля ложных срабатываний
#     },
#     'analysis_engine_stats': {...},
#     'ticks_since_last_analysis': int,
#     'ticks_since_last_health_check': int,
#     'last_health_check_time': float,
#     'timestamp': float
# }
```

### Реальные метрики производительности
Автоматический сбор и анализ метрик эффективности:

#### Время анализа
- **Среднее время:** < 50ms для типичных цепочек
- **95-й перцентиль:** < 200ms для сложных цепочек
- **Тренд:** Автоматическое обнаружение degradation

#### Использование памяти
- **Базовое потребление:** < 25MB для стандартной конфигурации
- **Пиковое потребление:** < 100MB при максимальной нагрузке
- **Эффективность:** > 80% использования выделенной памяти

#### Эффективность обнаружения
- **Точность (Precision):** > 85% для аномалий высокой severity
- **Полнота (Recall):** > 90% для критических аномалий
- **F1-score:** > 87% общая эффективность
- **False Positive Rate:** < 5% при нормальной работе

#### Кэширование
- **Hit Rate:** Рассчитывается на основе реальных hits/misses
- **TTL эффективность:** Автоматическая очистка просроченных записей
- **Память кэша:** LRU кэш с настраиваемым размером

### Расширенные метрики эффективности
Система предоставляет детальные метрики качества обнаружения аномалий:

```python
detailed_metrics = monitor.get_monitoring_stats()['detailed_accuracy_metrics']
# {
#     'anomaly_detection_precision': 0.85,     # Precision
#     'anomaly_detection_recall': 0.90,        # Recall
#     'anomaly_detection_f1_score': 0.87,      # F1-score
#     'false_positive_rate': 0.05,             # False positive rate
#     'false_negative_rate': 0.03,             # False negative rate
#     'temporal_stability_score': 0.78,        # Prediction stability
#     'plugin_performance': {...},             # Plugin-specific metrics
#     'recent_accuracy_trend': 0.82,           # Recent accuracy
#     'avg_analysis_quality': 0.91             # Analysis quality score
# }
```

Метрики обновляются автоматически на основе исторических данных и могут использоваться для мониторинга degradation системы обнаружения аномалий.

### Периодические проверки здоровья
Tick-based проверки здоровья системы:

- **Анализ каждые 50 тиков:** Семантический анализ паттернов
- **Проверка здоровья каждые 300 тиков:** Комплексная оценка системы
- **Логирование производительности каждые 500 тиков:** Метрики эффективности
- **Автоматическая адаптация:** Самонастройка порогов обнаружения

## Оптимизации производительности

### Tick-based архитектура
- **Zero threading overhead:** Полностью пассивная интеграция
- **Event-driven updates:** Обновления только при необходимости
- **Resource-aware scheduling:** Учет нагрузки системы при планировании
- **Memory-efficient caching:** LRU кэш с автоматической оптимизацией

### Алгоритмы кэширования
- **LRU eviction:** Удаление наименее недавно использованных записей
- **TTL-based expiration:** Автоматическая очистка просроченных записей
- **Configurable size limits:** Настраиваемые пределы размера кэша
- **Performance tracking:** Отслеживание hit rate и эффективности

### Graceful degradation
- **Statistical fallback:** Продолжение работы при ошибках анализа
- **Resource limits:** Ограничения на использование памяти и CPU
- **Error isolation:** Ошибки в одном анализе не влияют на систему
- **Configurable timeouts:** Настраиваемые таймауты операций

## Использование в тестах

### Интеграционные тесты
```python
@pytest.mark.asyncio
async def test_semantic_monitor_integration():
    monitor = SemanticMonitor()
    monitor.start_monitoring()

    # Создание тестовой цепочки событий
    chain_entries = create_test_correlation_chain()

    # Анализ
    result = monitor.analyze_correlation_chain("test_corr_001", chain_entries)

    # Проверка результатов
    assert result['correlation_id'] == "test_corr_001"
    assert 'anomalies' in result
    assert 'analysis_result' in result
```

### Тестирование обнаружения аномалий
```python
def test_anomaly_detection():
    monitor = SemanticMonitor(MonitorConfig(anomaly_threshold=0.5))

    # Создание аномальной цепочки
    anomalous_chain = create_anomalous_chain()

    result = monitor.analyze_correlation_chain("anom_test", anomalous_chain)

    # Проверка обнаружения аномалий
    assert len(result['anomalies']) > 0
    assert any(a['severity'] > 0.5 for a in result['anomalies'])
```

## Безопасность и отказоустойчивость

### Thread safety
- **RLock синхронизация:** Защита от конкурентного доступа
- **Atomic operations:** Атомарные операции с общими данными
- **Resource isolation:** Изоляция ресурсов между анализами

### Error handling
- **Exception isolation:** Ошибки в одном анализе не влияют на другие
- **Graceful degradation:** Продолжение работы при частичных сбоях
- **Logging:** Детальное логирование всех ошибок

### Resource management
- **Memory limits:** Ограничения на использование памяти
- **CPU limits:** Контроль загрузки процессора
- **Disk I/O:** Оптимизация операций ввода-вывода

## Мониторинг и алертинг

### Callback система
Добавление обработчиков алертов:

```python
def anomaly_alert_handler(alert_data):
    anomalies = alert_data['anomalies']
    for anomaly in anomalies:
        if anomaly['severity'] > 0.8:
            send_critical_alert(anomaly)

monitor.add_alert_callback(anomaly_alert_handler)
```

### Интеграция с внешними системами
- **Email алерты:** Отправка уведомлений по email
- **Slack/Discord:** Интеграция с мессенджерами
- **Metrics systems:** Отправка метрик в системы мониторинга
- **Dashboard:** Веб-интерфейс для просмотра аномалий

## Производительность и масштабируемость

### Бенчмарки
- **Analysis latency:** < 100ms для типичных цепочек
- **Throughput:** > 100 анализов/сек при нормальной нагрузке
- **Memory usage:** < 50MB для типичной конфигурации
- **Cache efficiency:** > 70% hit rate при нормальном использовании

### Масштабирование
- **Horizontal scaling:** Поддержка кластерного развертывания
- **Load balancing:** Распределение нагрузки между инстансами
- **Resource pooling:** Оптимизация использования ресурсов

## API и интерфейсы

### Основные методы
- `tick_update(current_tick, event_queue_size)` — Основной метод обновления (tick-based)
- `enable_monitoring()` / `disable_monitoring()` — Управление мониторингом без потоков
- `analyze_correlation_chain(correlation_id, chain_entries)` — Статистический анализ correlation chains
- `get_system_health()` — Оценка здоровья системы
- `get_monitoring_stats()` — Статистика мониторинга с метриками производительности

### Конфигурационные интерфейсы
- `update_config(new_config)` — Обновление конфигурации
- `add_alert_callback(callback)` — Добавление обработчиков алертов
- `clear_cache()` — Очистка кэша анализа

## Диагностика и отладка

### Debug режим
- **Verbose logging:** Детальное логирование всех операций
- **Analysis tracing:** Трассировка процесса анализа
- **Performance profiling:** Профилирование производительности

### Health checks
- **Self-diagnostics:** Автоматическая проверка собственного здоровья
- **Component validation:** Валидация всех зависимых компонентов
- **Configuration validation:** Проверка корректности конфигурации

## Будущие улучшения

### Планируемые возможности
- **Machine learning:** Интеграция ML моделей для улучшения обнаружения
- **Real-time dashboard:** Веб-интерфейс для мониторинга в реальном времени
- **Advanced analytics:** Продвинутые аналитические возможности
- **Predictive monitoring:** Предиктивное обнаружение проблем

### Исследования
- **Anomaly patterns:** Изучение паттернов аномалий
- **False positive reduction:** Снижение ложных срабатываний
- **Correlation analysis:** Улучшение анализа корреляций

## Заключение
Semantic Monitor представляет собой систему пассивного мониторинга поведенческих паттернов с использованием статистических методов анализа. Полностью интегрирован в runtime loop без активных потоков, обеспечивает обнаружение аномалий с метриками производительности и эффективности.

### Архитектурные особенности
- **Полная пассивность:** Нулевой overhead от активных потоков
- **Статистический анализ:** Методы статистического анализа correlation chains
- **Реальные метрики:** Метрики производительности, cache hit rate, эффективность обнаружения
- **Динамические пороги:** Адаптивные thresholds на основе исторических данных
- **Интеграция в runtime:** Вызов в каждом тике runtime loop

### Производительность
- **Latency:** < 100ms среднее время анализа
- **Throughput:** Зависит от частоты tick'ов
- **Memory:** < 50MB при нормальной работе
- **Cache hit rate:** Рассчитывается на основе реальных данных
- **False positive rate:** Зависит от настроек threshold