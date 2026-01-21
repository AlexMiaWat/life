"""
Инструмент философского наблюдения за поведением системы Life.

Модуль предоставляет унифицированный интерфейс для внешнего наблюдения
и анализа поведения системы Life с философской точки зрения.

ВАЖНО: Это инструмент НАБЛЮДЕНИЯ, а не самоанализа системы.
Анализ не влияет на поведение Life и не является частью ее внутренней логики.
"""

import logging
import time
from typing import TYPE_CHECKING, Dict, Optional

from .adaptation_quality import AdaptationQualityAnalyzer
from .conceptual_integrity import ConceptualIntegrityAnalyzer
from .ethical_behavior import EthicalBehaviorAnalyzer
from .life_vitality import LifeVitalityEvaluator
from .metrics import PhilosophicalMetrics
from .self_awareness import SelfAwarenessAnalyzer

if TYPE_CHECKING:
    from src.adaptation.adaptation import AdaptationManager
    from src.decision.decision import DecisionEngine
    from src.learning.learning import LearningEngine
    from src.memory.memory import Memory
    from src.state.self_state import SelfState

logger = logging.getLogger(__name__)


class PhilosophicalAnalyzer:
    """
    Инструмент философского наблюдения.

    Координирует работу всех специализированных анализаторов
    для комплексного внешнего наблюдения за поведением системы Life.

    АРХИТЕКТУРНЫЕ ПРИНЦИПЫ:
    - Анализатор является ВНЕШНИМ ИНСТРУМЕНТОМ наблюдения
    - Не влияет на поведение системы Life
    - Не является частью внутренней логики системы
    - Предоставляет метрики для разработчиков и исследователей
    """

    def __init__(self):
        """Инициализация философского анализатора."""
        # Инициализация специализированных анализаторов
        self.self_awareness_analyzer = SelfAwarenessAnalyzer()
        self.adaptation_quality_analyzer = AdaptationQualityAnalyzer()
        self.ethical_behavior_analyzer = EthicalBehaviorAnalyzer()
        self.conceptual_integrity_analyzer = ConceptualIntegrityAnalyzer()
        self.life_vitality_evaluator = LifeVitalityEvaluator()

        # История анализов
        self.analysis_history = []
        self.max_history_size = 50

        logger.info("Философский анализатор инициализирован")

    def analyze_behavior(
        self,
        self_state: 'SelfState',
        memory: 'Memory',
        learning_engine: 'LearningEngine',
        adaptation_manager: 'AdaptationManager',
        decision_engine: 'DecisionEngine'
    ) -> PhilosophicalMetrics:
        """
        Провести комплексный философский анализ поведения.

        Args:
            self_state: Текущее состояние системы
            memory: Память системы
            learning_engine: Движок обучения
            adaptation_manager: Менеджер адаптации
            decision_engine: Движок принятия решений

        Returns:
            PhilosophicalMetrics: Полные философские метрики
        """
        logger.debug("Начинаем комплексный философский анализ")

        # Создаем объект метрик
        metrics = PhilosophicalMetrics()

        try:
            # Анализ самоосознания
            metrics.self_awareness = self.self_awareness_analyzer.analyze_self_awareness(
                self_state, memory
            )

            # Анализ качества адаптации
            metrics.adaptation_quality = self.adaptation_quality_analyzer.analyze_adaptation_quality(
                self_state, adaptation_manager, learning_engine
            )

            # Анализ этического поведения
            metrics.ethical_behavior = self.ethical_behavior_analyzer.analyze_ethical_behavior(
                self_state, memory, decision_engine
            )

            # Анализ концептуальной целостности
            metrics.conceptual_integrity = self.conceptual_integrity_analyzer.analyze_conceptual_integrity(
                self_state, memory, learning_engine
            )

            # Оценка жизненности
            metrics.life_vitality = self.life_vitality_evaluator.evaluate_life_vitality(
                self_state, memory, adaptation_manager, learning_engine
            )

            # Вычисление обобщенного философского индекса
            metrics.calculate_overall_index()

            logger.info(f"Философский анализ завершен. Общий индекс: {metrics.philosophical_index:.3f}")

        except Exception as e:
            logger.error(f"Ошибка при философском анализе: {e}")
            # Возвращаем базовые метрики при ошибке
            metrics.philosophical_index = 0.0

        # Добавляем в историю
        self.analysis_history.append(metrics.to_dict())
        if len(self.analysis_history) > self.max_history_size:
            self.analysis_history = self.analysis_history[-self.max_history_size:]

        return metrics

    def get_philosophical_insights(self, metrics: PhilosophicalMetrics) -> Dict[str, str]:
        """
        Получить философские insights на основе метрик.

        Args:
            metrics: Философские метрики

        Returns:
            Dict[str, str]: Словарь с insights по различным аспектам
        """
        insights = {}

        # Insights по самоосознанию
        if metrics.self_awareness.overall_self_awareness > 0.8:
            insights['self_awareness'] = "Высокий уровень самоосознания: система демонстрирует глубокое понимание собственного состояния"
        elif metrics.self_awareness.overall_self_awareness > 0.6:
            insights['self_awareness'] = "Хороший уровень самоосознания: система осознает ключевые аспекты своего функционирования"
        elif metrics.self_awareness.overall_self_awareness > 0.4:
            insights['self_awareness'] = "Умеренный уровень самоосознания: базовые механизмы самоконтроля функционируют"
        else:
            insights['self_awareness'] = "Низкий уровень самоосознания: требуется развитие механизмов самоосознания"

        # Insights по адаптации
        if metrics.adaptation_quality.overall_adaptation_quality > 0.8:
            insights['adaptation'] = "Отличная адаптивность: система эффективно приспосабливается к изменениям"
        elif metrics.adaptation_quality.overall_adaptation_quality > 0.6:
            insights['adaptation'] = "Хорошая адаптивность: система демонстрирует стабильную адаптацию"
        elif metrics.adaptation_quality.overall_adaptation_quality > 0.4:
            insights['adaptation'] = "Умеренная адаптивность: базовые механизмы адаптации работают"
        else:
            insights['adaptation'] = "Слабая адаптивность: требуется улучшение адаптационных механизмов"

        # Insights по этическому поведению
        if metrics.ethical_behavior.overall_ethical_score > 0.8:
            insights['ethics'] = "Высокий этический уровень: система демонстрирует последовательное и осознанное поведение"
        elif metrics.ethical_behavior.overall_ethical_score > 0.6:
            insights['ethics'] = "Хороший этический уровень: система следует базовым нормам поведения"
        elif metrics.ethical_behavior.overall_ethical_score > 0.4:
            insights['ethics'] = "Умеренный этический уровень: присутствуют базовые этические механизмы"
        else:
            insights['ethics'] = "Низкий этический уровень: требуется развитие этического сознания"

        # Insights по концептуальной целостности
        if metrics.conceptual_integrity.overall_integrity > 0.8:
            insights['conceptual_integrity'] = "Высокая концептуальная целостность: модель мира согласована и стабильна"
        elif metrics.conceptual_integrity.overall_integrity > 0.6:
            insights['conceptual_integrity'] = "Хорошая концептуальная целостность: основные концепции согласованы"
        elif metrics.conceptual_integrity.overall_integrity > 0.4:
            insights['conceptual_integrity'] = "Умеренная концептуальная целостность: базовые концепции стабильны"
        else:
            insights['conceptual_integrity'] = "Низкая концептуальная целостность: присутствуют концептуальные несоответствия"

        # Insights по жизненности
        if metrics.life_vitality.overall_vitality > 0.8:
            insights['life_vitality'] = "Высокая жизненность: система демонстрирует активное и гармоничное поведение"
        elif metrics.life_vitality.overall_vitality > 0.6:
            insights['life_vitality'] = "Хорошая жизненность: система энергична и адаптивна"
        elif metrics.life_vitality.overall_vitality > 0.4:
            insights['life_vitality'] = "Умеренная жизненность: присутствуют признаки активного поведения"
        else:
            insights['life_vitality'] = "Низкая жизненность: требуется повышение активности и гармонии"

        # Общий философский insight
        philosophical_index = metrics.philosophical_index
        if philosophical_index > 0.8:
            insights['overall'] = "Высочайший философский уровень: система демонстрирует глубокое философское сознание"
        elif philosophical_index > 0.7:
            insights['overall'] = "Очень высокий философский уровень: система близка к философскому идеалу"
        elif philosophical_index > 0.6:
            insights['overall'] = "Высокий философский уровень: система показывает значительный философский потенциал"
        elif philosophical_index > 0.5:
            insights['overall'] = "Средний философский уровень: система развивает философские способности"
        elif philosophical_index > 0.4:
            insights['overall'] = "Умеренный философский уровень: базовые философские механизмы функционируют"
        elif philosophical_index > 0.3:
            insights['overall'] = "Низкий философский уровень: требуется развитие философского сознания"
        else:
            insights['overall'] = "Очень низкий философский уровень: система находится в начале философского развития"

        return insights

    def analyze_trends(self, time_window: Optional[int] = None) -> Dict[str, Dict]:
        """
        Проанализировать тренды философских метрик.

        Args:
            time_window: Окно анализа в количестве последних записей (None = все)

        Returns:
            Dict[str, Dict]: Анализ трендов по различным метрикам
        """
        if not self.analysis_history:
            return {}

        # Определяем окно анализа
        history = self.analysis_history
        if time_window and time_window < len(history):
            history = history[-time_window:]

        trends = {}

        # Анализируем тренды для ключевых метрик
        metrics_to_analyze = [
            'self_awareness.overall_self_awareness',
            'adaptation_quality.overall_adaptation_quality',
            'ethical_behavior.overall_ethical_score',
            'conceptual_integrity.overall_integrity',
            'life_vitality.overall_vitality',
            'philosophical_index'
        ]

        for metric_path in metrics_to_analyze:
            values = []
            for record in history:
                value = self._extract_nested_value(record, metric_path)
                if value is not None:
                    values.append(value)

            if len(values) > 1:
                trend_info = self._calculate_trend(values)
                trends[metric_path] = trend_info

        return trends

    def _extract_nested_value(self, data: Dict, path: str) -> Optional[float]:
        """
        Извлечь вложенное значение из словаря по пути.

        Args:
            data: Словарь с данными
            path: Путь к значению (например, 'self_awareness.overall_self_awareness')

        Returns:
            Optional[float]: Значение или None если не найдено
        """
        keys = path.split('.')
        current = data

        try:
            for key in keys:
                current = current[key]
            return float(current) if current is not None else None
        except (KeyError, TypeError, ValueError):
            return None

    def _calculate_trend(self, values: list) -> Dict:
        """
        Вычислить тренд для последовательности значений.

        Args:
            values: Список значений

        Returns:
            Dict: Информация о тренде
        """
        if len(values) < 2:
            return {'trend': 'insufficient_data'}

        # Вычисляем линейный тренд
        n = len(values)
        x = list(range(n))
        y = values

        # Простая линейная регрессия
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)

        if n * sum_x2 - sum_x * sum_x == 0:
            slope = 0
        else:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)

        # Определяем направление тренда
        if slope > 0.001:
            trend_direction = 'improving'
        elif slope < -0.001:
            trend_direction = 'declining'
        else:
            trend_direction = 'stable'

        # Вычисляем волатильность
        mean_y = sum_y / n
        variance = sum((yi - mean_y) ** 2 for yi in y) / n
        volatility = variance ** 0.5

        return {
            'trend': trend_direction,
            'slope': slope,
            'volatility': volatility,
            'start_value': values[0],
            'end_value': values[-1],
            'change': values[-1] - values[0],
            'change_percent': ((values[-1] - values[0]) / max(abs(values[0]), 0.001)) * 100
        }

    def generate_philosophical_report(self, metrics: PhilosophicalMetrics) -> str:
        """
        Сгенерировать текстовый философский отчет.

        Args:
            metrics: Философские метрики

        Returns:
            str: Текстовый отчет
        """
        insights = self.get_philosophical_insights(metrics)

        report = []
        report.append("=" * 80)
        report.append("ФИЛОСОФСКИЙ АНАЛИЗ ПОВЕДЕНИЯ СИСТЕМЫ LIFE")
        report.append("=" * 80)
        report.append(f"Время анализа: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("." * 80)
        report.append("")

        # Общий индекс
        report.append(f"ОБЩИЙ ФИЛОСОФСКИЙ ИНДЕКС: {metrics.philosophical_index:.3f}")
        report.append(f"Интерпретация: {insights.get('overall', 'Недоступно')}")
        report.append("")

        # Детальный анализ по аспектам
        aspects = [
            ('Самоосознание', 'self_awareness', metrics.self_awareness.overall_self_awareness),
            ('Качество адаптации', 'adaptation', metrics.adaptation_quality.overall_adaptation_quality),
            ('Этическое поведение', 'ethics', metrics.ethical_behavior.overall_ethical_score),
            ('Концептуальная целостность', 'conceptual_integrity', metrics.conceptual_integrity.overall_integrity),
            ('Жизненность', 'life_vitality', metrics.life_vitality.overall_vitality)
        ]

        for aspect_name, insight_key, value in aspects:
            report.append(f"{aspect_name.upper()}: {value:.3f}")
            report.append(f"  {insights.get(insight_key, 'Недоступно')}")
            report.append("")

        # Тренды
        trends = self.analyze_trends(10)  # Анализируем последние 10 записей
        if trends:
            report.append("ТРЕНДЫ (последние 10 анализов):")
            report.append("-" * 40)

            for metric_path, trend_info in trends.items():
                metric_name = metric_path.replace('_', ' ').replace('.', ' - ').title()
                trend_symbol = {
                    'improving': '↗️',
                    'declining': '↘️',
                    'stable': '→'
                }.get(trend_info['trend'], '?')

                report.append(f"{metric_name}: {trend_symbol} {trend_info['trend']} "
                             f"({trend_info['change_percent']:+.1f}%)")
            report.append("")

        report.append("=" * 80)

        return "\n".join(report)