"""
Инструменты визуализации философских метрик системы Life.

Модуль предоставляет функции для создания графиков и диаграмм
философских метрик и их трендов.
"""

try:
    import matplotlib.pyplot as plt
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    plt = None
    np = None

from typing import Dict, List, Optional
import time


class PhilosophicalVisualizer:
    """
    Визуализатор философских метрик.

    Создает графики и диаграммы для анализа философских аспектов поведения системы.
    """

    def __init__(self, style: str = 'default'):
        """Инициализация визуализатора."""
        if HAS_MATPLOTLIB:
            plt.style.use(style)
        self.colors = {
            'self_awareness': '#1f77b4',      # Синий
            'adaptation_quality': '#ff7f0e',  # Оранжевый
            'ethical_behavior': '#2ca02c',    # Зеленый
            'conceptual_integrity': '#d62728', # Красный
            'life_vitality': '#9467bd',       # Фиолетовый
            'philosophical_index': '#8c564b'  # Коричневый
        }

    def plot_philosophical_radar(self, metrics, save_path: Optional[str] = None):
        """
        Создать радарную диаграмму философских метрик.

        Args:
            metrics: Объект PhilosophicalMetrics
            save_path: Путь для сохранения графика (опционально)
        """
        if not HAS_MATPLOTLIB:
            print("Matplotlib не установлен. Визуализация недоступна.")
            return

        # Подготавливаем данные
        categories = ['Самоосознание', 'Адаптация', 'Этика', 'Целостность', 'Жизненность']
        values = [
            metrics.self_awareness.overall_self_awareness,
            metrics.adaptation_quality.overall_adaptation_quality,
            metrics.ethical_behavior.overall_ethical_score,
            metrics.conceptual_integrity.overall_integrity,
            metrics.life_vitality.overall_vitality
        ]

        # Замыкаем круг
        values += values[:1]
        categories += categories[:1]

        # Создаем радарную диаграмму
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=True)

        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))

        ax.plot(angles, values, 'o-', linewidth=2, color=self.colors['philosophical_index'])
        ax.fill(angles, values, alpha=0.25, color=self.colors['philosophical_index'])

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories[:-1])
        ax.set_ylim(0, 1)
        ax.set_title('Философский профиль системы Life', size=16, pad=20)
        ax.grid(True)

        # Добавляем значения на график
        for angle, value, category in zip(angles[:-1], values[:-1], categories[:-1]):
            ax.text(angle, value + 0.05, '.2f',
                   ha='center', va='center', fontsize=10, fontweight='bold')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Радарная диаграмма сохранена: {save_path}")
        else:
            plt.show()

    def plot_metrics_trends(self, analyzer, time_window: int = 20, save_path: Optional[str] = None):
        """
        Создать график трендов философских метрик.

        Args:
            analyzer: Объект PhilosophicalAnalyzer с историей анализов
            time_window: Количество последних анализов для отображения
            save_path: Путь для сохранения графика (опционально)
        """
        if not HAS_MATPLOTLIB:
            print("Matplotlib не установлен. Визуализация недоступна.")
            return

        if not analyzer.analysis_history:
            print("Нет данных для построения трендов")
            return

        # Получаем тренды
        trends = analyzer.analyze_trends(time_window)
        if not trends:
            print("Недостаточно данных для анализа трендов")
            return

        # Подготавливаем данные
        history = analyzer.analysis_history[-time_window:]
        timestamps = [record.get('timestamp', i) for i, record in enumerate(history)]

        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        axes = axes.flatten()

        # Метрики для отображения
        metrics_info = [
            ('philosophical_index', 'Общий индекс', 'philosophical_index'),
            ('self_awareness.overall_self_awareness', 'Самоосознание', 'self_awareness'),
            ('adaptation_quality.overall_adaptation_quality', 'Адаптация', 'adaptation_quality'),
            ('ethical_behavior.overall_ethical_score', 'Этика', 'ethical_behavior'),
            ('conceptual_integrity.overall_integrity', 'Целостность', 'conceptual_integrity'),
            ('life_vitality.overall_vitality', 'Жизненность', 'life_vitality')
        ]

        for i, (metric_path, title, color_key) in enumerate(metrics_info):
            ax = axes[i]

            # Извлекаем значения метрики
            values = []
            for record in history:
                value = self._extract_nested_value(record, metric_path)
                values.append(value if value is not None else 0)

            if values:
                ax.plot(timestamps, values, 'o-', color=self.colors[color_key],
                       linewidth=2, markersize=4)

                # Добавляем тренд если доступен
                if metric_path in trends:
                    trend_info = trends[metric_path]
                    slope = trend_info.get('slope', 0)
                    if abs(slope) > 0.0001:  # Значимый тренд
                        # Создаем линию тренда
                        x_trend = np.array([timestamps[0], timestamps[-1]])
                        y_trend = np.array([values[0], values[0] + slope * (len(values) - 1)])
                        ax.plot(x_trend, y_trend, '--', color='red', alpha=0.7,
                               label=f'Тренд: {slope:.4f}')

                ax.set_title(title)
                ax.set_ylim(0, 1)
                ax.grid(True, alpha=0.3)

                # Добавляем информацию о тренде
                if metric_path in trends:
                    trend_info = trends[metric_path]
                    trend_text = trend_info.get('trend', 'unknown')
                    ax.text(0.02, 0.98, f'Тренд: {trend_text}',
                           transform=ax.transAxes, fontsize=9,
                           verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        plt.suptitle('Тренды философских метрик системы Life', fontsize=16)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"График трендов сохранен: {save_path}")
        else:
            plt.show()

    def plot_philosophical_heatmap(self, analyzer, save_path: Optional[str] = None):
        """
        Создать тепловую карту корреляций между философскими метриками.

        Args:
            analyzer: Объект PhilosophicalAnalyzer с историей анализов
            save_path: Путь для сохранения графика (опционально)
        """
        if not HAS_MATPLOTLIB:
            print("Matplotlib не установлен. Визуализация недоступна.")
            return

        if len(analyzer.analysis_history) < 5:
            print("Недостаточно данных для построения тепловой карты")
            return

        # Извлекаем данные метрик
        metrics_data = {
            'Самоосознание': [],
            'Адаптация': [],
            'Этика': [],
            'Целостность': [],
            'Жизненность': [],
            'Общий индекс': []
        }

        metric_paths = {
            'Самоосознание': 'self_awareness.overall_self_awareness',
            'Адаптация': 'adaptation_quality.overall_adaptation_quality',
            'Этика': 'ethical_behavior.overall_ethical_score',
            'Целостность': 'conceptual_integrity.overall_integrity',
            'Жизненность': 'life_vitality.overall_vitality',
            'Общий индекс': 'philosophical_index'
        }

        for record in analyzer.analysis_history:
            for name, path in metric_paths.items():
                value = self._extract_nested_value(record, path)
                if value is not None:
                    metrics_data[name].append(value)

        # Находим минимальную длину для выравнивания
        min_length = min(len(values) for values in metrics_data.values())
        if min_length < 3:
            print("Недостаточно данных для корреляционного анализа")
            return

        # Выравниваем данные
        aligned_data = {}
        for name, values in metrics_data.items():
            aligned_data[name] = values[-min_length:]

        # Вычисляем корреляционную матрицу
        data_matrix = np.array([aligned_data[name] for name in metrics_data.keys()])
        correlation_matrix = np.corrcoef(data_matrix)

        # Создаем тепловую карту
        fig, ax = plt.subplots(figsize=(10, 8))

        im = ax.imshow(correlation_matrix, cmap='RdYlBu_r', vmin=-1, vmax=1)

        # Добавляем подписи
        metric_names = list(metrics_data.keys())
        ax.set_xticks(np.arange(len(metric_names)))
        ax.set_yticks(np.arange(len(metric_names)))
        ax.set_xticklabels(metric_names, rotation=45, ha='right')
        ax.set_yticklabels(metric_names)

        # Добавляем значения корреляций
        for i in range(len(metric_names)):
            for j in range(len(metric_names)):
                text = ax.text(j, i, '.2f',
                             ha='center', va='center',
                             color='white' if abs(correlation_matrix[i, j]) > 0.5 else 'black',
                             fontweight='bold')

        ax.set_title('Корреляции между философскими метриками', pad=20)
        plt.colorbar(im, ax=ax, label='Коэффициент корреляции')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Тепловая карта корреляций сохранена: {save_path}")
        else:
            plt.show()

    def create_comprehensive_report(self, analyzer, output_dir: str = 'philosophical_reports'):
        """
        Создать комплексный визуальный отчет.

        Args:
            analyzer: Объект PhilosophicalAnalyzer
            output_dir: Директория для сохранения отчетов
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        timestamp = time.strftime('%Y%m%d_%H%M%S')

        print("Создание комплексного философского отчета...")

        # Получаем последние метрики
        if analyzer.analysis_history:
            # Создаем график трендов
            print("  - Создание графика трендов...")
            trends_path = os.path.join(output_dir, f'philosophical_trends_{timestamp}.png')
            try:
                self.plot_metrics_trends(analyzer, save_path=trends_path)
                print(f"    ✓ Тренды сохранены: {trends_path}")
            except Exception as e:
                print(f"    ✗ Ошибка создания трендов: {e}")

            # Создаем тепловую карту корреляций
            print("  - Создание тепловой карты корреляций...")
            heatmap_path = os.path.join(output_dir, f'philosophical_correlations_{timestamp}.png')
            try:
                self.plot_philosophical_heatmap(analyzer, save_path=heatmap_path)
                print(f"    ✓ Корреляции сохранены: {heatmap_path}")
            except Exception as e:
                print(f"    ✗ Ошибка создания корреляций: {e}")

            print(f"✓ Комплексный отчет сохранен в директории: {output_dir}")
        else:
            print("Нет данных для создания отчета")

    def _extract_nested_value(self, data: Dict, path: str) -> Optional[float]:
        """
        Извлечь вложенное значение из словаря.

        Args:
            data: Словарь с данными
            path: Путь к значению

        Returns:
            Optional[float]: Значение или None
        """
        keys = path.split('.')
        current = data

        try:
            for key in keys:
                current = current[key]
            return float(current) if current is not None else None
        except (KeyError, TypeError, ValueError):
            return None