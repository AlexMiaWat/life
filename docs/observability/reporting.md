# Reporting System - Система отчетов и визуализаций

## Обзор

Reporting System предоставляет инструменты для генерации детальных HTML отчетов с визуализациями поведения системы Life. Система использует matplotlib для графиков и Jinja2 для шаблонов, создавая интерактивные отчеты для анализа трендов и паттернов.

## Архитектура

### Компоненты

#### ReportGenerator
Основной класс для генерации отчетов:

```python
from src.observability.reporting import ReportGenerator

generator = ReportGenerator(template_dir="custom_templates/")
```

#### Шаблоны
HTML шаблоны на основе Jinja2 с поддержкой:
- Динамических данных
- Кастомных фильтров
- Встроенных графиков

#### Графики
Визуализации на основе matplotlib:
- Метрики производительности
- Тренды во времени
- Паттерны поведения

## Генерация отчетов

### Одиночный отчет

```python
from src.observability.external_observer import ExternalObserver
from src.observability.reporting import ReportGenerator

# Создание наблюдателя и генератора
observer = ExternalObserver()
generator = ReportGenerator()

# Выполнение наблюдения
report = observer.observe_from_logs(time.time() - 3600, time.time())

# Генерация HTML отчета
html_path = generator.generate_html_report(report, Path("report.html"))
```

### Сводный отчет

```python
# Генерация сводного отчета по нескольким наблюдениям
reports = [report1, report2, report3]
summary_path = generator.generate_summary_report(reports, Path("summary.html"))
```

## Структура HTML отчета

### Шапка отчета
```
Life System Observation Report
Generated: 2026-01-21 15:30:45
Observation Period: 2026-01-21 14:30:45 - 2026-01-21 15:30:45
```

### Метрики системы
- **Cycle Count**: 1,250
- **Uptime**: 3.5h
- **Memory Entries**: 500
- **Integrity Score**: 95%
- **Energy Level**: 85%
- **Error Count**: 3

### Графики
1. **Metrics Overview**: Комплексный график всех метрик
2. **Behavior Patterns**: Визуализация паттернов поведения
3. **Trends Over Time**: Графики трендов (для сводных отчетов)

### Анализ
- **Behavior Patterns**: Список обнаруженных паттернов
- **Trends**: Анализ изменений метрик
- **Anomalies**: Выявленные проблемы
- **Recommendations**: Предложения по улучшению

## CLI интерфейс

### Генерация отчета из логов

```bash
# Отчет за последний час
python generate_report_cli.py --logs-analysis --start-time 3600 --output report.html

# Отчет за последние 24 часа
python generate_report_cli.py --logs-analysis --start-time 86400 --output daily_report.html

# Сохранение в определенную директорию
python generate_report_cli.py --logs-analysis --start-time 3600 --output-dir reports/
```

### Генерация отчета из снимков

```bash
# Анализ всех снимков в директории
python generate_report_cli.py --snapshots-analysis --snapshot-dir data/snapshots --output snapshots_report.html

# Ограничение количества снимков
python generate_report_cli.py --snapshots-analysis --snapshot-dir data/snapshots --limit 50 --output limited_report.html
```

### Сводные отчеты

```bash
# Сводный отчет по всем сохраненным отчетам наблюдения
python generate_report_cli.py --summary --report-dir reports/ --output summary_report.html
```

## Кастомизация шаблонов

### Структура шаблонов

```
templates/
├── observation_report.html     # Шаблон одиночного отчета
└── summary_report.html         # Шаблон сводного отчета (опционально)
```

### Переменные шаблона

#### Для одиночного отчета
```jinja2
{{ report.observation_period[0]|datetime }}  # Начало периода
{{ report.observation_period[1]|datetime }}  # Конец периода
{{ metrics.cycle_count }}                    # Метрики системы
{{ patterns|length }}                        # Количество паттернов
{{ trends.integrity_score }}                 # Тренды
{{ anomalies|length }}                       # Количество аномалий
{{ recommendations|join(', ') }}             # Рекомендации
```

#### Графики
```jinja2
<img src="data:image/png;base64,{{ charts.metrics_overview }}" alt="Metrics">
```

### Кастомный шаблон

```html
<!DOCTYPE html>
<html>
<head>
    <title>Custom Life Report</title>
    <style>
        .metric { color: #007acc; }
        .warning { color: #ffc107; }
        .error { color: #dc3545; }
    </style>
</head>
<body>
    <h1>Custom Observation Report</h1>

    <div class="metrics">
        <h2>System Metrics</h2>
        <p class="metric">Cycles: {{ metrics.cycle_count }}</p>
        <p class="metric">Integrity: {{ "%.1f"|format(metrics.integrity_score * 100) }}%</p>

        {% if metrics.error_count > 5 %}
        <p class="error">High error count: {{ metrics.error_count }}</p>
        {% endif %}
    </div>

    {% if charts.metrics_overview %}
    <div class="charts">
        <h2>Visualizations</h2>
        <img src="data:image/png;base64,{{ charts.metrics_overview }}">
    </div>
    {% endif %}

    <div class="recommendations">
        <h2>Recommendations</h2>
        <ul>
        {% for rec in recommendations %}
            <li>{{ rec }}</li>
        {% endfor %}
        </ul>
    </div>
</body>
</html>
```

## Форматы экспорта

### HTML (основной)
- Полнофункциональные интерактивные отчеты
- Встроенные графики (base64 encoded)
- Адаптивный дизайн
- Поддержка печати

### JSON (для программного доступа)
```python
# Экспорт данных для дальнейшей обработки
report_data = report.to_dict()
with open('report.json', 'w') as f:
    json.dump(report_data, f, indent=2)
```

### PDF (предложение)
```python
# Конвертация HTML в PDF (требует дополнительных библиотек)
import pdfkit

pdfkit.from_file('report.html', 'report.pdf')
```

## Анализ трендов

### Временные тренды
- **Integrity Score**: Стабильность/изменения уровня целостности
- **Energy Level**: Динамика энергопотребления
- **Error Rate**: Тренды частоты ошибок
- **Learning Effectiveness**: Эффективность адаптации

### Классификация трендов
- **improving**: Метрика улучшается
- **declining**: Метрика ухудшается
- **stable**: Метрика стабильна
- **volatile**: Метрика сильно колеблется

### Визуализация трендов
```
Integrity Score: improving (+2.3% over period)
Energy Level: declining (-5.1% over period)
Error Count: stable (±1.2% variation)
```

## Обработка аномалий

### Типы аномалий
- **Critical**: Требуют немедленного внимания
- **High**: Высокий приоритет
- **Medium**: Средний приоритет
- **Low**: Низкий приоритет

### Форматирование в отчетах
```html
<div class="anomaly critical">
    <h3>Critical Anomaly: Low Integrity</h3>
    <p>System integrity dropped below 30%</p>
    <small>Severity: critical | Timestamp: 2026-01-21 15:30:45</small>
</div>
```

## Производительность

### Оптимизации генерации
- **Кэширование графиков**: Повторное использование идентичных визуализаций
- **Ленивая загрузка**: Генерация графиков по требованию
- **Компрессия**: Оптимизация размера HTML файлов

### Метрики производительности
```
Report generation time: 2.3 seconds
HTML file size: 1.2 MB
Charts count: 3
Data points processed: 1,250
```

### Масштабируемость
- **Большие отчеты**: Поддержка отчетов с тысячами точек данных
- **Параллельная генерация**: Множественные отчеты одновременно
- **Инкрементальные обновления**: Частичные обновления существующих отчетов

## Интеграция с CI/CD

### Автоматическая генерация
```yaml
# .github/workflows/generate-reports.yml
name: Generate Observation Reports

on:
  schedule:
    - cron: '0 */6 * * *'  # Каждые 6 часов

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Generate Report
        run: python generate_report_cli.py --logs-analysis --start-time 21600 --output report.html
      - name: Upload Report
        uses: actions/upload-artifact@v2
        with:
          name: observation-report
          path: report.html
```

### Качество отчетов
- **Валидация**: Автоматическая проверка корректности данных
- **Тестирование**: Регрессионные тесты на изменения в шаблонах
- **Мониторинг**: Отслеживание метрик генерации отчетов

## Безопасность

### Защита от XSS
- Автоматическое экранирование в Jinja2
- Валидация входных данных
- Сантизация HTML контента

### Контроль доступа
- Ограничение директорий для чтения
- Валидация путей к файлам
- Защита от path traversal

### Аудит
- Логирование генерации отчетов
- Отслеживание доступа к чувствительным данным
- Временные метки всех операций

## Расширение системы

### Добавление новых метрик

```python
# В ReportGenerator
def add_custom_metric(self, report, metric_name, value):
    """Добавить кастомную метрику в отчет"""
    if not hasattr(report.metrics_summary, 'custom_metrics'):
        report.metrics_summary.custom_metrics = {}
    report.metrics_summary.custom_metrics[metric_name] = value
```

### Кастомные визуализации

```python
def generate_custom_chart(self, data):
    """Генерация кастомного графика"""
    fig, ax = plt.subplots()
    ax.plot(data['x'], data['y'])
    ax.set_title(data.get('title', 'Custom Chart'))

    return self._fig_to_base64(fig)
```

### Новые форматы экспорта

```python
def export_to_csv(self, report, output_path):
    """Экспорт в CSV"""
    import csv

    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        # Заголовки
        writer.writerow(['Metric', 'Value'])

        # Метрики
        metrics = report.metrics_summary
        for attr in dir(metrics):
            if not attr.startswith('_'):
                value = getattr(metrics, attr)
                if isinstance(value, (int, float)):
                    writer.writerow([attr, value])
```

## Troubleshooting

### Распространенные проблемы

**Matplotlib не установлен**
```
ImportError: matplotlib is not available
```
Решение: `pip install matplotlib jinja2`

**Права доступа к директории**
```
PermissionError: [Errno 13] Permission denied
```
Решение: Проверить права на директорию или изменить output_path

**Некорректные данные в шаблоне**
```
TemplateSyntaxError: invalid syntax
```
Решение: Проверить синтаксис Jinja2 в шаблоне

### Debug режим

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Детальное логирование генерации
generator = ReportGenerator()
report = generator.generate_html_report(observation_report, Path("debug_report.html"))
```

### Валидация отчетов

```python
def validate_report(report):
    """Валидация структуры отчета"""
    required_fields = ['observation_period', 'metrics_summary', 'behavior_patterns']

    for field in required_fields:
        if not hasattr(report, field):
            raise ValueError(f"Missing required field: {field}")

    # Проверка метрик
    metrics = report.metrics_summary
    if not (0 <= metrics.integrity_score <= 1):
        raise ValueError("Invalid integrity_score range")

    return True
```

## Мониторинг качества

### Метрики отчетов
- **Generation time**: Время генерации отчета
- **File size**: Размер HTML файла
- **Charts count**: Количество графиков
- **Data completeness**: Полнота данных

### Алерты
- Generation time > 30 секунд
- File size > 10 MB
- Missing charts in reports
- Template rendering errors

## Примеры использования

### Ежедневный отчет

```bash
#!/bin/bash
# daily_report.sh

DATE=$(date +%Y%m%d)
REPORT_DIR="reports/$DATE"

mkdir -p "$REPORT_DIR"

# Генерация отчета за последние 24 часа
python generate_report_cli.py \
    --logs-analysis \
    --start-time 86400 \
    --output "$REPORT_DIR/daily_report.html"

# Отправка по email
mail -s "Daily Life System Report" admin@example.com < "$REPORT_DIR/daily_report.html"
```

### Мониторинг аномалий

```python
def monitor_anomalies():
    """Мониторинг и отчет по аномалиям"""
    observer = ExternalObserver()
    generator = ReportGenerator()

    # Получение последнего отчета
    if observer.observation_history:
        report = observer.observation_history[-1]

        # Проверка на критические аномалии
        critical_anomalies = [
            a for a in report.anomalies
            if a.get('severity') == 'critical'
        ]

        if critical_anomalies:
            # Генерация экстренного отчета
            alert_report = generator.generate_html_report(
                report,
                Path("alert_report.html")
            )

            # Отправка алерта
            send_alert("Critical anomalies detected", alert_report)
```

## Будущие улучшения

### Планируемые фичи
- **Interactive charts**: JavaScript графики (Chart.js, D3.js)
- **Real-time reports**: Автообновление отчетов
- **Multi-format export**: PDF, Excel, PNG
- **Report templates**: Галерея шаблонов для разных сценариев
- **Collaborative features**: Комментарии и аннотации в отчетах

### Интеграции
- **Slack/Teams**: Отправка отчетов в чаты
- **Jira/ServiceNow**: Создание тикетов по аномалиям
- **ELK stack**: Интеграция с Elasticsearch для поиска по отчетам
- **PowerBI/Tableau**: Экспорт данных для BI инструментов

## См. также

- [ExternalObserver](external_observer.md) - Компонент наблюдения
- [Observation API](observation_api.md) - REST API
- [Analysis Tools](analysis_tools.md) - CLI инструменты