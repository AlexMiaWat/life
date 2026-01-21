# Пример: Сравнение разных "жизней"

Этот документ показывает, как использовать систему сравнения для анализа поведения нескольких экземпляров Life.

## Быстрый старт

### 1. Запуск системы сравнения

```bash
# Запуск API сервера системы сравнения
python src/comparison_cli.py --api --api-port 8001
```

### 2. Открытие веб-интерфейса

Откройте в браузере: `http://localhost:8001/dashboard`

### 3. Создание и сравнение жизней

1. **Создать тестовые инстансы**: Нажмите "Create Test Instances"
2. **Запустить все инстансы**: Нажмите "Start All Instances"
3. **Начать сравнение**: Нажмите "Start Comparison (30s)"

Через 30 секунд вы увидите:
- Графики текущих состояний всех инстансов
- Анализ паттернов решений
- Метрики схожести и разнообразия

## Программное использование

### Создание сравнения из кода

```python
from src.comparison import ComparisonManager, PatternAnalyzer, ComparisonMetrics

# 1. Создать менеджер сравнения
manager = ComparisonManager()

# 2. Создать несколько инстансов с разными настройками
configs = [
    {"instance_id": "conservative", "tick_interval": 2.0, "snapshot_period": 20},
    {"instance_id": "aggressive", "tick_interval": 0.5, "snapshot_period": 5},
    {"instance_id": "balanced", "tick_interval": 1.0, "snapshot_period": 10}
]

for config in configs:
    manager.create_instance(**config)

# 3. Запустить все инстансы
start_results = manager.start_all_instances()
print("Started instances:", start_results)

# 4. Подождать немного для накопления данных
import time
time.sleep(10)

# 5. Собрать данные для сравнения
comparison_data = manager.collect_comparison_data()
print(f"Collected data from {len(comparison_data['instances'])} instances")

# 6. Проанализировать паттерны
analyzer = PatternAnalyzer()
analysis = analyzer.analyze_comparison_data(comparison_data)

# 7. Вычислить метрики сравнения
metrics = ComparisonMetrics()
summary = metrics.get_summary_report(comparison_data['instances'])

# 8. Вывести результаты
print("\\n=== PATTERN ANALYSIS ===")
for instance_id, instance_analysis in analysis['instances_analysis'].items():
    patterns = instance_analysis['decision_patterns']['patterns']
    print(f"{instance_id}: {patterns}")

print("\\n=== SIMILARITY METRICS ===")
similarity = summary['similarity_metrics']['overall_similarity']
for pair, score in similarity.items():
    print(f"{pair}: {score:.3f}")

print("\\n=== DIVERSITY METRICS ===")
diversity = summary['diversity_metrics']
print(f"Pattern diversity: {diversity['pattern_diversity']}")
print(f"Diversity score: {diversity['diversity_score']:.3f}")

# 9. Остановить все инстансы
stop_results = manager.stop_all_instances()
print("Stopped instances:", stop_results)
```

### Результаты сравнения

```
=== PATTERN ANALYSIS ===
conservative: {'ignore': 28, 'absorb': 15, 'dampen': 7}
aggressive: {'ignore': 15, 'absorb': 22, 'dampen': 18}
balanced: {'ignore': 22, 'absorb': 18, 'dampen': 12}

=== SIMILARITY METRICS ===
conservative_vs_aggressive: 0.723
conservative_vs_balanced: 0.845
aggressive_vs_balanced: 0.789

=== DIVERSITY METRICS ===
Pattern diversity: 3
Diversity score: 0.634
```

## Интерпретация результатов

### Паттерны поведения

- **Conservative** (консервативный): Больше игнорирует события, меньше реагирует
- **Aggressive** (агрессивный): Чаще использует dampen для смягчения событий
- **Balanced** (сбалансированный): Среднее поведение между двумя другими

### Метрики схожести

- **0.723-0.845**: Средняя-высокая схожесть, инстансы развиваются похоже
- **Высокая схожесть** между conservative и balanced указывает на общие паттерны
- **Низкая схожесть** между conservative и aggressive показывает разные стратегии

### Разнообразие

- **Pattern diversity = 3**: Все три типа паттернов используются
- **Diversity score = 0.634**: Умеренное разнообразие поведения

## Продвинутые сценарии

### Сравнение с разными начальными состояниями

```python
# Создание инстансов с разными начальными энергиями
manager.create_instance("weak_start", tick_interval=1.0, snapshot_period=10)
manager.create_instance("strong_start", tick_interval=1.0, snapshot_period=10)

# После запуска можно анализировать, как разные стартовые условия
# влияют на долгосрочное поведение и адаптацию
```

### Длительное сравнение

```python
# Запуск API для длительного мониторинга
from src.comparison import ComparisonAPI

api = ComparisonAPI(port=8001)
api.run_in_background()

# Теперь можно управлять сравнением через API
# или использовать веб-интерфейс для визуального мониторинга
```

### Анализ эволюции

```python
# Многократный сбор данных для анализа трендов
historical_data = []
for i in range(10):
    data = manager.collect_comparison_data()
    historical_data.append(data)
    time.sleep(5)

# Анализ, как менялись паттерны со временем
evolution_analyzer = PatternAnalyzer()
for data in historical_data:
    analysis = evolution_analyzer.analyze_comparison_data(data)
    # Сохранить или проанализировать тренды
```

## Визуализация результатов

### Веб-dashboard

Откройте `http://localhost:8001/dashboard` для интерактивной визуализации:

- **Графики состояний**: Столбчатые диаграммы energy/stability/integrity
- **Анализ паттернов**: Распределение решений по инстансам
- **Метрики**: Таблицы с подробными показателями сравнения

### Экспорт данных

```python
import json

# Сохранить результаты сравнения
with open('comparison_results.json', 'w') as f:
    json.dump({
        'comparison_data': comparison_data,
        'analysis': analysis,
        'metrics': summary
    }, f, indent=2, ensure_ascii=False)

print("Results saved to comparison_results.json")
```

## Следующие шаги

1. **Изучите документацию**: [Comparison System](../components/comparison-system.md)
2. **Экспериментируйте**: Попробуйте разные конфигурации инстансов
3. **Анализируйте**: Изучайте, как меняются паттерны в зависимости от условий
4. **Расширяйте**: Добавляйте свои метрики и анализаторы

---

**Сложность**: Средняя
**Время выполнения**: 5-15 минут
**Требуемые знания**: Основы Python, HTTP API