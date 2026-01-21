"""
Система отчетов и визуализаций для внешнего наблюдения.

Генерирует детальные отчеты о поведении системы Life
с графиками, диаграммами и аналитикой трендов.
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import base64
from io import BytesIO

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from jinja2 import Template

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None
    mdates = None
    Template = None

if not MATPLOTLIB_AVAILABLE:
    logger = logging.getLogger(__name__)
    logger.warning("matplotlib или jinja2 не установлены. Визуализации будут недоступны.")

from .external_observer import ExternalObserver, ObservationReport, SystemMetrics

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Генератор отчетов для внешнего наблюдения за системой Life.
    """

    def __init__(self, template_dir: Optional[Path] = None):
        self.template_dir = template_dir or Path(__file__).parent / "templates"
        self.template_dir.mkdir(exist_ok=True)

        # Создаем базовый HTML шаблон если его нет
        self._ensure_template_exists()

    def generate_html_report(
        self, report: ObservationReport, output_path: Optional[Path] = None
    ) -> Path:
        """
        Сгенерировать полный HTML отчет с визуализациями.

        Args:
            report: Отчет наблюдения
            output_path: Путь для сохранения отчета

        Returns:
            Путь к сохраненному отчету
        """
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("matplotlib и jinja2 требуются для генерации HTML отчетов")

        # Генерируем графики
        charts = self._generate_charts(report)

        # Подготавливаем данные для шаблона
        template_data = self._prepare_template_data(report, charts)

        # Загружаем и рендерим шаблон
        template = self._load_template()
        html_content = template.render(**template_data)

        # Сохраняем отчет
        if output_path is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_path = Path(f"observation_report_{timestamp}.html")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"HTML отчет сохранен: {output_path}")
        return output_path

    def generate_summary_report(
        self, reports: List[ObservationReport], output_path: Optional[Path] = None
    ) -> Path:
        """
        Сгенерировать сводный отчет по нескольким наблюдениям.

        Args:
            reports: Список отчетов наблюдения
            output_path: Путь для сохранения отчета

        Returns:
            Путь к сохраненному отчету
        """
        if not reports:
            raise ValueError("Необходимо предоставить хотя бы один отчет")

        # Анализируем тренды по времени
        trend_data = self._analyze_trends_over_time(reports)

        # Генерируем графики трендов
        trend_charts = self._generate_trend_charts(reports)

        # Подготавливаем сводные данные
        summary_data = {
            "total_reports": len(reports),
            "observation_period": (
                min(r.observation_period[0] for r in reports),
                max(r.observation_period[1] for r in reports),
            ),
            "average_metrics": self._calculate_average_metrics(reports),
            "trend_analysis": trend_data,
            "charts": trend_charts,
            "generated_at": time.time(),
        }

        # Генерируем HTML
        from jinja2 import Environment

        env = Environment()
        env.filters["datetime"] = datetime_filter
        template = env.from_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Life System Observation Summary Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
                .metric { background: #e8f4f8; padding: 10px; margin: 10px 0; border-radius: 3px; }
                .chart { margin: 20px 0; text-align: center; }
                .trend { padding: 10px; margin: 10px 0; border-left: 4px solid #007acc; }
                .positive { border-left-color: #28a745; }
                .negative { border-left-color: #dc3545; }
                .neutral { border-left-color: #6c757d; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Life System Observation Summary Report</h1>
                <p>Generated: {{ generated_at|datetime }}</p>
                <p>Period: {{ observation_period[0]|datetime }} - {{ observation_period[1]|datetime }}</p>
                <p>Total reports analyzed: {{ total_reports }}</p>
            </div>

            <h2>Average Metrics</h2>
            {% for key, value in average_metrics.items() %}
            <div class="metric">
                <strong>{{ key|title }}:</strong> {{ "%.3f"|format(value) if value is number else value }}
            </div>
            {% endfor %}

            <h2>Trend Analysis</h2>
            {% for trend in trend_analysis %}
            <div class="trend {{ trend.direction }}">
                <strong>{{ trend.metric|title }}</strong>: {{ trend.description }}
                ({{ "%.2f"|format(trend.change_percent) }}% change)
            </div>
            {% endfor %}

            <h2>Charts</h2>
            {% for chart_name, chart_data in charts.items() %}
            <div class="chart">
                <h3>{{ chart_name|title }}</h3>
                <img src="data:image/png;base64,{{ chart_data }}" alt="{{ chart_name }}">
            </div>
            {% endfor %}
        </body>
        </html>
        """)

        html_content = template.render(**summary_data)

        # Сохраняем отчет
        if output_path is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_path = Path(f"summary_report_{timestamp}.html")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"Сводный отчет сохранен: {output_path}")
        return output_path

    def _generate_charts(self, report: ObservationReport) -> Dict[str, str]:
        """Генерировать графики для отчета."""
        charts = {}

        try:
            # График метрик
            fig, axes = plt.subplots(2, 2, figsize=(12, 8))
            fig.suptitle("System Metrics Overview")

            metrics = report.metrics_summary

            # Метрики производительности
            axes[0, 0].bar(
                ["Cycles", "Actions", "Memory"],
                [metrics.cycle_count, metrics.action_count, metrics.memory_entries_count],
            )
            axes[0, 0].set_title("Activity Metrics")
            axes[0, 0].tick_params(axis="x", rotation=45)

            # Эффективность компонентов
            axes[0, 1].bar(
                ["Learning", "Adaptation", "Decision"],
                [
                    metrics.learning_effectiveness,
                    metrics.adaptation_rate,
                    metrics.decision_success_rate,
                ],
            )
            axes[0, 1].set_title("Component Effectiveness")
            axes[0, 1].set_ylim(0, 1)

            # Уровни здоровья
            axes[1, 0].bar(
                ["Integrity", "Energy", "Errors"],
                [metrics.integrity_score, metrics.energy_level, metrics.error_count],
            )
            axes[1, 0].set_title("System Health")
            axes[1, 0].tick_params(axis="x", rotation=45)

            # Скорости обработки
            axes[1, 1].bar(
                ["Events/sec", "Changes/sec"],
                [metrics.event_processing_rate, metrics.state_change_frequency],
            )
            axes[1, 1].set_title("Processing Rates")

            plt.tight_layout()
            charts["metrics_overview"] = self._fig_to_base64(fig)
            plt.close(fig)

            # График паттернов поведения
            if report.behavior_patterns:
                fig, ax = plt.subplots(figsize=(10, 6))
                patterns = report.behavior_patterns[:10]  # Ограничиваем до 10 паттернов
                names = [p.pattern_type for p in patterns]
                frequencies = [p.frequency for p in patterns]
                impacts = [p.impact_score for p in patterns]

                x = range(len(patterns))
                ax.bar(x, frequencies, alpha=0.7, label="Frequency")
                ax.scatter(x, impacts, color="red", label="Impact", s=50)
                ax.set_xticks(x)
                ax.set_xticklabels(names, rotation=45, ha="right")
                ax.set_title("Behavior Patterns")
                ax.legend()

                charts["behavior_patterns"] = self._fig_to_base64(fig)
                plt.close(fig)

        except Exception as e:
            logger.warning(f"Ошибка генерации графиков: {e}")

        return charts

    def _generate_trend_charts(self, reports: List[ObservationReport]) -> Dict[str, str]:
        """Генерировать графики трендов для сводного отчета."""
        charts = {}

        try:
            if len(reports) < 2:
                return charts

            # Сортируем отчеты по времени
            sorted_reports = sorted(reports, key=lambda r: r.metrics_summary.timestamp)

            timestamps = [
                datetime.fromtimestamp(r.metrics_summary.timestamp) for r in sorted_reports
            ]

            # График изменения метрик со временем
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))
            fig.suptitle("Metrics Trends Over Time")

            # Integrity и Energy
            integrity_scores = [r.metrics_summary.integrity_score for r in sorted_reports]
            energy_levels = [r.metrics_summary.energy_level for r in sorted_reports]

            axes[0, 0].plot(timestamps, integrity_scores, "b-o", label="Integrity")
            axes[0, 0].plot(timestamps, energy_levels, "g-s", label="Energy")
            axes[0, 0].set_title("System Health Trends")
            axes[0, 0].legend()
            axes[0, 0].tick_params(axis="x", rotation=45)

            # Learning и Adaptation
            learning_eff = [r.metrics_summary.learning_effectiveness for r in sorted_reports]
            adaptation_rate = [r.metrics_summary.adaptation_rate for r in sorted_reports]

            axes[0, 1].plot(timestamps, learning_eff, "r-o", label="Learning")
            axes[0, 1].plot(timestamps, adaptation_rate, "m-s", label="Adaptation")
            axes[0, 1].set_title("Component Effectiveness Trends")
            axes[0, 1].legend()
            axes[0, 1].tick_params(axis="x", rotation=45)

            # Activity metrics
            cycle_counts = [r.metrics_summary.cycle_count for r in sorted_reports]
            action_counts = [r.metrics_summary.action_count for r in sorted_reports]

            axes[1, 0].plot(timestamps, cycle_counts, "c-o", label="Cycles")
            axes[1, 0].plot(timestamps, action_counts, "y-s", label="Actions")
            axes[1, 0].set_title("Activity Trends")
            axes[1, 0].legend()
            axes[1, 0].tick_params(axis="x", rotation=45)

            # Error rate
            error_counts = [r.metrics_summary.error_count for r in sorted_reports]

            axes[1, 1].plot(timestamps, error_counts, "r-o", label="Errors")
            axes[1, 1].set_title("Error Trends")
            axes[1, 1].legend()
            axes[1, 1].tick_params(axis="x", rotation=45)

            plt.tight_layout()
            charts["trends_overview"] = self._fig_to_base64(fig)
            plt.close(fig)

        except Exception as e:
            logger.warning(f"Ошибка генерации графиков трендов: {e}")

        return charts

    def _prepare_template_data(
        self, report: ObservationReport, charts: Dict[str, str]
    ) -> Dict[str, Any]:
        """Подготовить данные для HTML шаблона."""
        return {
            "report": report,
            "metrics": report.metrics_summary,
            "patterns": report.behavior_patterns,
            "trends": report.trends,
            "anomalies": report.anomalies,
            "recommendations": report.recommendations,
            "charts": charts,
            "generated_at": time.time(),
            "observation_start": datetime.fromtimestamp(report.observation_period[0]),
            "observation_end": datetime.fromtimestamp(report.observation_period[1]),
        }

    def _load_template(self) -> Template:
        """Загрузить HTML шаблон."""
        template_path = self.template_dir / "observation_report.html"

        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()
        else:
            # Используем встроенный шаблон
            template_content = self._get_default_template()

        # Создаем Environment с кастомными фильтрами
        from jinja2 import Environment

        env = Environment()
        env.filters["datetime"] = datetime_filter
        return env.from_string(template_content)

    def _get_default_template(self) -> str:
        """Получить встроенный HTML шаблон."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Life System Observation Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { text-align: center; border-bottom: 2px solid #007acc; padding-bottom: 20px; margin-bottom: 30px; }
                .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }
                .metric-card { background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #007acc; }
                .metric-value { font-size: 24px; font-weight: bold; color: #007acc; }
                .metric-label { font-size: 14px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; }
                .section { margin: 40px 0; }
                .section h2 { color: #333; border-bottom: 1px solid #ddd; padding-bottom: 10px; }
                .chart { margin: 20px 0; text-align: center; background: #f8f9fa; padding: 20px; border-radius: 8px; }
                .pattern-list { list-style: none; padding: 0; }
                .pattern-item { background: #e8f4f8; margin: 10px 0; padding: 15px; border-radius: 5px; border-left: 4px solid #17a2b8; }
                .trend-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
                .trend-item { padding: 10px; border-radius: 5px; text-align: center; }
                .trend-improving { background: #d4edda; border-left: 4px solid #28a745; }
                .trend-declining { background: #f8d7da; border-left: 4px solid #dc3545; }
                .trend-stable { background: #fff3cd; border-left: 4px solid #ffc107; }
                .anomaly-list { background: #f8d7da; padding: 15px; border-radius: 5px; margin: 10px 0; }
                .recommendations { background: #d1ecf1; padding: 20px; border-radius: 8px; }
                .recommendation-item { margin: 10px 0; padding: 10px; background: white; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Life System Observation Report</h1>
                    <p>Generated: {{ generated_at|datetime }}</p>
                    <p>Observation Period: {{ observation_start }} - {{ observation_end }}</p>
                </div>

                <div class="section">
                    <h2>System Metrics</h2>
                    <div class="metrics-grid">
                        <div class="metric-card">
                            <div class="metric-value">{{ "%.0f"|format(metrics.cycle_count) }}</div>
                            <div class="metric-label">Total Cycles</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{{ "%.1f"|format(metrics.uptime_seconds / 3600) }}h</div>
                            <div class="metric-label">Uptime</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{{ metrics.memory_entries_count }}</div>
                            <div class="metric-label">Memory Entries</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{{ "%.1f"|format(metrics.integrity_score * 100) }}%</div>
                            <div class="metric-label">Integrity Score</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{{ "%.1f"|format(metrics.energy_level * 100) }}%</div>
                            <div class="metric-label">Energy Level</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{{ metrics.error_count }}</div>
                            <div class="metric-label">Error Count</div>
                        </div>
                    </div>
                </div>

                {% if charts.metrics_overview %}
                <div class="section">
                    <h2>Metrics Overview</h2>
                    <div class="chart">
                        <img src="data:image/png;base64,{{ charts.metrics_overview }}" alt="Metrics Overview" style="max-width: 100%;">
                    </div>
                </div>
                {% endif %}

                <div class="section">
                    <h2>Behavior Patterns</h2>
                    <ul class="pattern-list">
                    {% for pattern in patterns %}
                        <li class="pattern-item">
                            <strong>{{ pattern.pattern_type|title }}</strong><br>
                            {{ pattern.description }}<br>
                            <small>Frequency: {{ "%.2f"|format(pattern.frequency) }} | Impact: {{ "%.2f"|format(pattern.impact_score) }}</small>
                        </li>
                    {% endfor %}
                    </ul>
                </div>

                {% if charts.behavior_patterns %}
                <div class="section">
                    <h2>Behavior Patterns Chart</h2>
                    <div class="chart">
                        <img src="data:image/png;base64,{{ charts.behavior_patterns }}" alt="Behavior Patterns" style="max-width: 100%;">
                    </div>
                </div>
                {% endif %}

                <div class="section">
                    <h2>Trends</h2>
                    <div class="trend-grid">
                    {% for key, value in trends.items() %}
                        <div class="trend-item trend-{{ value|lower }}">
                            <strong>{{ key|title }}</strong><br>
                            {{ value|title }}
                        </div>
                    {% endfor %}
                    </div>
                </div>

                {% if anomalies %}
                <div class="section">
                    <h2>Anomalies Detected</h2>
                    {% for anomaly in anomalies %}
                    <div class="anomaly-list">
                        <strong>{{ anomaly.type|title }}</strong>: {{ anomaly.description }}
                        <br><small>Severity: {{ anomaly.severity|title }}</small>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}

                {% if recommendations %}
                <div class="section">
                    <h2>Recommendations</h2>
                    <div class="recommendations">
                    {% for rec in recommendations %}
                        <div class="recommendation-item">• {{ rec }}</div>
                    {% endfor %}
                    </div>
                </div>
                {% endif %}
            </div>
        </body>
        </html>
        """

    def _ensure_template_exists(self):
        """Убедиться, что базовый шаблон существует."""
        template_path = self.template_dir / "observation_report.html"
        if not template_path.exists():
            template_path.parent.mkdir(parents=True, exist_ok=True)
            with open(template_path, "w", encoding="utf-8") as f:
                f.write(self._get_default_template())
            logger.info(f"Создан базовый шаблон: {template_path}")

    def _fig_to_base64(self, fig) -> str:
        """Преобразовать matplotlib фигуру в base64 строку."""
        buffer = BytesIO()
        fig.savefig(buffer, format="png", dpi=100, bbox_inches="tight")
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        buffer.close()
        return image_base64

    def _analyze_trends_over_time(self, reports: List[ObservationReport]) -> List[Dict[str, Any]]:
        """Анализировать тренды по нескольким отчетам."""
        if len(reports) < 2:
            return []

        sorted_reports = sorted(reports, key=lambda r: r.metrics_summary.timestamp)
        first = sorted_reports[0].metrics_summary
        last = sorted_reports[-1].metrics_summary

        trends = []

        # Анализируем ключевые метрики
        metrics_to_check = [
            ("integrity_score", "Integrity Score"),
            ("energy_level", "Energy Level"),
            ("learning_effectiveness", "Learning Effectiveness"),
            ("adaptation_rate", "Adaptation Rate"),
            ("error_count", "Error Count"),
        ]

        for metric_attr, display_name in metrics_to_check:
            first_val = getattr(first, metric_attr)
            last_val = getattr(last, metric_attr)

            if first_val == 0:
                change_percent = 0
            else:
                change_percent = ((last_val - first_val) / first_val) * 100

            if abs(change_percent) < 1:
                direction = "stable"
                description = f"{display_name} remains stable"
            elif change_percent > 0:
                if metric_attr == "error_count":
                    direction = "worsening"
                    description = f"{display_name} is increasing"
                else:
                    direction = "improving"
                    description = f"{display_name} is improving"
            else:
                if metric_attr == "error_count":
                    direction = "improving"
                    description = f"{display_name} is decreasing"
                else:
                    direction = "declining"
                    description = f"{display_name} is declining"

            trends.append(
                {
                    "metric": metric_attr,
                    "display_name": display_name,
                    "change_percent": change_percent,
                    "direction": direction,
                    "description": description,
                }
            )

        return trends

    def _calculate_average_metrics(self, reports: List[ObservationReport]) -> Dict[str, float]:
        """Рассчитать средние значения метрик по всем отчетам."""
        if not reports:
            return {}

        metrics_attrs = [
            "cycle_count",
            "uptime_seconds",
            "memory_entries_count",
            "learning_effectiveness",
            "adaptation_rate",
            "decision_success_rate",
            "error_count",
            "integrity_score",
            "energy_level",
            "action_count",
            "event_processing_rate",
            "state_change_frequency",
        ]

        averages = {}
        for attr in metrics_attrs:
            values = [getattr(r.metrics_summary, attr) for r in reports]
            averages[attr] = sum(values) / len(values)

        return averages


# Фильтр для Jinja2
def datetime_filter(timestamp: float) -> str:
    """Jinja2 фильтр для форматирования timestamp."""
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


# Фильтры настраиваются при создании Environment в методах класса
