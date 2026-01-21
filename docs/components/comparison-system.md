# Система сравнения жизней (Comparison System)

## Обзор

Система сравнения жизней предоставляет инструменты для параллельного запуска нескольких экземпляров Life, анализа их поведения и сравнения паттернов эволюции. Система позволяет исследовать, как разные начальные условия и случайные события влияют на развитие вычислительной жизни.

## Архитектура

### Компоненты системы

```
Comparison System
├── ComparisonManager          # Центральный менеджер инстансов
├── LifeInstance              # Обертка для одного инстанса Life
├── PatternAnalyzer           # Анализатор паттернов поведения
├── ComparisonMetrics         # Метрики сравнения
├── ComparisonAPI             # REST API для управления
└── Web Dashboard             # Веб-интерфейс визуализации
```

### Поток данных

1. **Создание инстансов** → ComparisonManager создает изолированные LifeInstance
2. **Запуск сравнения** → Параллельный запуск нескольких Life процессов
3. **Сбор данных** → Агрегация структурированных логов и snapshots
4. **Анализ паттернов** → PatternAnalyzer извлекает паттерны решений и поведения
5. **Вычисление метрик** → ComparisonMetrics рассчитывает схожесть и разнообразие
6. **Визуализация** → Web Dashboard отображает результаты в реальном времени

## Основные возможности

### Управление инстансами

- **Создание**: `POST /instances` с конфигурацией (tick_interval, snapshot_period)
- **Запуск/остановка**: `POST /instances/{id}/start|stop`
- **Мониторинг**: `GET /instances/{id}/status` - состояние, uptime, ресурсы
- **Изоляция**: Каждый инстанс работает в отдельном процессе с уникальным портом

### Сравнение в реальном времени

- **Автоматический сбор**: Фоновый процесс собирает данные каждые 5 секунд
- **Анализ паттернов**: Распределение решений (ignore/absorb/dampen/amplify)
- **Метрики схожести**: Сравнение эволюционных траекторий состояний
- **Диверсификация**: Оценка разнообразия поведения между инстансами

### Веб-интерфейс

- **Dashboard**: `GET /dashboard` - интерактивная визуализация
- **Графики состояний**: Energy, Stability, Integrity для всех инстансов
- **Анализ паттернов**: Распределение решений по типам
- **Метрики сравнения**: Таблицы с подробными показателями
- **Управление**: Кнопки для создания, запуска и остановки инстансов

## API Reference

### Управление инстансами

#### Создание инстанса
```http
POST /instances
Content-Type: application/json

{
  "instance_id": "life_experiment_1",
  "tick_interval": 1.0,
  "snapshot_period": 10,
  "dev_mode": false,
  "enable_profiling": false
}
```

#### Список инстансов
```http
GET /instances
```

#### Управление инстансом
```http
POST /instances/{instance_id}/start
POST /instances/{instance_id}/stop
DELETE /instances/{instance_id}
```

#### Статус инстанса
```http
GET /instances/{instance_id}/status
GET /instances/{instance_id}/snapshot
GET /instances/{instance_id}/logs?limit=100
```

### Сравнение

#### Запуск сравнения
```http
POST /comparison/start
Content-Type: application/json

{
  "instance_ids": ["life_1", "life_2", "life_3"],
  "duration": 60
}
```

#### Остановка сравнения
```http
POST /comparison/stop
```

#### Результаты сравнения
```http
GET /comparison/results      # Сырые данные
GET /comparison/analysis     # Анализ паттернов
GET /comparison/metrics      # Метрики сравнения
```

## Метрики сравнения

### Схожесть (Similarity Metrics)

- **State Similarity**: Сравнение текущих состояний (energy, stability, integrity)
- **Behavior Similarity**: Схожесть последовательностей решений
- **Evolution Similarity**: Сравнение трендов изменения со временем
- **Overall Similarity**: Общая оценка схожести (0-1, где 1 - идентичны)

### Производительность (Performance Metrics)

- **Survival Rates**: Время жизни, количество пережитых тиков
- **Adaptation Efficiency**: Эффективность адаптации к событиям
- **Resource Usage**: Количество обработанных событий и принятых решений

### Разнообразие (Diversity Metrics)

- **Pattern Diversity**: Количество уникальных паттернов поведения
- **Behavior Diversity**: Разнообразие последовательностей действий
- **State Diversity**: Разброс состояний между инстансами
- **Diversity Score**: Общая оценка разнообразия (0-1)

## Использование

### Быстрый старт

1. **Запуск API сервера**:
   ```bash
   python -m src.comparison_cli --api --api-port 8001
   ```

2. **Открыть dashboard**:
   ```
   http://localhost:8001/dashboard
   ```

3. **Создать тестовые инстансы**:
   - Нажать "Create Test Instances"
   - Запустить инстансы "Start All Instances"
   - Начать сравнение "Start Comparison (30s)"

### Программное использование

```python
from src.comparison import ComparisonManager, PatternAnalyzer, ComparisonMetrics

# Создание менеджера
manager = ComparisonManager()

# Создание инстансов
for i in range(3):
    manager.create_instance(f"life_{i+1}", tick_interval=1.0, snapshot_period=5)

# Запуск всех инстансов
results = manager.start_all_instances()

# Сбор данных для сравнения
comparison_data = manager.collect_comparison_data()

# Анализ паттернов
analyzer = PatternAnalyzer()
analysis = analyzer.analyze_comparison_data(comparison_data)

# Вычисление метрик
metrics = ComparisonMetrics()
summary = metrics.get_summary_report(comparison_data['instances'])

# Остановка
manager.stop_all_instances()
```

## Примеры анализа

### Сравнение паттернов решений

```python
# Получить распределение паттернов для каждого инстанса
for instance_id, instance_analysis in analysis['instances_analysis'].items():
    patterns = instance_analysis['decision_patterns']['patterns']
    print(f"{instance_id}: {patterns}")
    # life_1: {'ignore': 45, 'absorb': 23, 'dampen': 12}
    # life_2: {'ignore': 38, 'absorb': 31, 'dampen': 11}
```

### Метрики схожести

```python
similarity = summary['similarity_metrics']['overall_similarity']
for pair, score in similarity.items():
    print(f"{pair}: similarity = {score:.3f}")
    # life_1_vs_life_2: similarity = 0.785
    # life_1_vs_life_3: similarity = 0.654
    # life_2_vs_life_3: similarity = 0.723
```

## Расширения

### Добавление новых метрик

```python
class CustomMetrics(ComparisonMetrics):
    def compute_custom_metric(self, instances_data):
        # Ваша логика анализа
        return custom_result
```

### Кастомный анализ паттернов

```python
class CustomPatternAnalyzer(PatternAnalyzer):
    def analyze_custom_patterns(self, logs):
        # Анализ специфических паттернов
        return custom_analysis
```

## Производительность

- **Масштабируемость**: Поддержка 5+ параллельных инстансов
- **Изоляция**: Каждый инстанс в отдельном процессе
- **Оптимизация**: Буферизация логов, периодический сбор данных
- **Мониторинг**: Метрики использования ресурсов

## Отладка и troubleshooting

### Логи

- **API логи**: Выводятся в консоль сервера
- **Instance логи**: Сохраняются в `data/instances/{instance_id}/`
- **Comparison логи**: Доступны через `GET /comparison/results`

### Распространенные проблемы

1. **Инстансы не запускаются**: Проверить доступные порты (8001+)
2. **Нет данных сравнения**: Убедиться, что инстансы запущены и собирают логи
3. **Пустые метрики**: Проверить структуру данных instances

### Мониторинг

```bash
# Статус системы
curl http://localhost:8001/status

# Логи инстанса
curl http://localhost:8001/instances/life_1/logs

# Результаты сравнения
curl http://localhost:8001/comparison/results
```

## Связанные компоненты

- [**Self-State**](../components/self-state.md) - внутреннее состояние Life
- [**Environment**](../components/environment.md) - генератор событий
- [**StructuredLogger**](../observability/structured_logger.md) - логирование
- [**Runtime Loop**](../components/runtime-loop.md) - основной цикл

---

**Статус**: ✅ Реализовано и протестировано
**Версия**: 1.0.0
**Дата**: 2026-01-21