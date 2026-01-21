"""
PatternAnalyzer - анализатор паттернов поведения жизней

Анализирует паттерны поведения разных инстансов Life на основе
их структурированных логов, snapshots и эволюции состояний.
"""

from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter

from src.logging_config import get_logger

logger = get_logger(__name__)


class PatternAnalyzer:
    """
    Анализатор паттернов поведения Life инстансов.

    Анализирует:
    - Распределение паттернов решений (ignore/absorb/dampen)
    - Частоту различных типов событий
    - Эволюцию состояний со временем
    - Корреляции между событиями и реакциями
    """

    def __init__(self):
        self.pattern_stats = defaultdict(Counter)
        self.event_stats = defaultdict(Counter)
        self.state_evolution = defaultdict(list)

    def analyze_instance_data(self, instance_id: str, instance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Анализирует данные одного инстанса.

        Args:
            instance_id: Идентификатор инстанса
            instance_data: Данные инстанса (статус, snapshot, логи)

        Returns:
            Dict с результатами анализа
        """
        analysis = {
            'instance_id': instance_id,
            'decision_patterns': {},
            'event_types': {},
            'state_trends': {},
            'correlations': {}
        }

        try:
            # Анализируем логи
            logs = instance_data.get('recent_logs', [])
            analysis['decision_patterns'] = self._analyze_decision_patterns(logs)
            analysis['event_types'] = self._analyze_event_types(logs)

            # Анализируем состояние
            snapshot = instance_data.get('snapshot')
            if snapshot:
                analysis['state_trends'] = self._analyze_state_trends(instance_id, snapshot)

            # Ищем корреляции
            analysis['correlations'] = self._analyze_correlations(logs)

        except Exception as e:
            logger.error(f"Error analyzing instance '{instance_id}': {e}")
            analysis['error'] = str(e)

        return analysis

    def analyze_comparison_data(self, comparison_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Анализирует данные сравнения от всех инстансов.

        Args:
            comparison_data: Данные от ComparisonManager

        Returns:
            Dict с результатами сравнительного анализа
        """
        analysis = {
            'timestamp': comparison_data.get('timestamp'),
            'instances_analysis': {},
            'comparison_metrics': {},
            'patterns_comparison': {},
            'diversity_metrics': {}
        }

        instances_data = comparison_data.get('instances', {})

        # Анализируем каждый инстанс
        for instance_id, instance_data in instances_data.items():
            analysis['instances_analysis'][instance_id] = self.analyze_instance_data(instance_id, instance_data)

        # Вычисляем метрики сравнения
        analysis['comparison_metrics'] = self._compute_comparison_metrics(analysis['instances_analysis'])
        analysis['patterns_comparison'] = self._compare_patterns(analysis['instances_analysis'])
        analysis['diversity_metrics'] = self._compute_diversity_metrics(analysis['instances_analysis'])

        return analysis

    def _analyze_decision_patterns(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Анализирует паттерны принятия решений."""
        decisions = []

        for log in logs:
            if log.get('stage') == 'decision':
                data = log.get('data', {})
                pattern = data.get('pattern')
                if pattern:
                    decisions.append(pattern)

        if not decisions:
            return {'total_decisions': 0, 'patterns': {}}

        pattern_counts = Counter(decisions)
        total = len(decisions)

        return {
            'total_decisions': total,
            'patterns': dict(pattern_counts),
            'most_common': pattern_counts.most_common(3),
            'pattern_distribution': {
                pattern: count / total
                for pattern, count in pattern_counts.items()
            }
        }

    def _analyze_event_types(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Анализирует типы событий."""
        events = []

        for log in logs:
            if log.get('stage') == 'event':
                data = log.get('data', {})
                event_type = data.get('type')
                if event_type:
                    events.append(event_type)

        if not events:
            return {'total_events': 0, 'types': {}}

        type_counts = Counter(events)
        total = len(events)

        return {
            'total_events': total,
            'types': dict(type_counts),
            'most_common': type_counts.most_common(3),
            'type_distribution': {
                event_type: count / total
                for event_type, count in type_counts.items()
            }
        }

    def _analyze_state_trends(self, instance_id: str, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Анализирует тренды состояния."""
        # Сохраняем историю состояний
        state = {
            'energy': snapshot.get('energy', 0),
            'stability': snapshot.get('stability', 0),
            'integrity': snapshot.get('integrity', 0),
            'ticks': snapshot.get('ticks', 0),
            'age': snapshot.get('age', 0)
        }

        self.state_evolution[instance_id].append(state)

        # Анализируем тренд (последние 10 состояний)
        history = self.state_evolution[instance_id][-10:]

        if len(history) < 2:
            return {'trend': 'insufficient_data', 'current': state}

        # Вычисляем тренды
        energy_trend = self._calculate_trend([s['energy'] for s in history])
        stability_trend = self._calculate_trend([s['stability'] for s in history])
        integrity_trend = self._calculate_trend([s['integrity'] for s in history])

        return {
            'current': state,
            'trends': {
                'energy': energy_trend,
                'stability': stability_trend,
                'integrity': integrity_trend
            },
            'stability': 'stable' if all(abs(t) < 0.1 for t in [energy_trend, stability_trend, integrity_trend]) else 'changing'
        }

    def _analyze_correlations(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Ищет корреляции между событиями и решениями."""
        correlations = defaultdict(lambda: defaultdict(int))

        # Группируем логи по correlation_id
        correlation_chains = defaultdict(list)

        for log in logs:
            correlation_id = log.get('correlation_id')
            if correlation_id:
                correlation_chains[correlation_id].append(log)

        # Анализируем цепочки
        for chain in correlation_chains.values():
            event_types = []
            decision_patterns = []

            for log in chain:
                if log.get('stage') == 'event':
                    data = log.get('data', {})
                    event_types.append(data.get('type'))
                elif log.get('stage') == 'decision':
                    data = log.get('data', {})
                    decision_patterns.append(data.get('pattern'))

            # Считаем корреляции
            for event_type in event_types:
                for pattern in decision_patterns:
                    correlations[event_type][pattern] += 1

        return dict(correlations)

    def _compute_comparison_metrics(self, instances_analysis: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Вычисляет метрики сравнения между инстансами."""
        metrics = {
            'pattern_similarity': {},
            'performance_comparison': {},
            'behavior_diversity': {}
        }

        if len(instances_analysis) < 2:
            return metrics

        # Сравниваем паттерны решений
        pattern_distributions = {}
        for instance_id, analysis in instances_analysis.items():
            patterns = analysis.get('decision_patterns', {}).get('pattern_distribution', {})
            pattern_distributions[instance_id] = patterns

        # Вычисляем схожесть паттернов (простая метрика)
        instance_ids = list(instances_analysis.keys())
        for i, id1 in enumerate(instance_ids):
            for id2 in instance_ids[i+1:]:
                similarity = self._calculate_pattern_similarity(
                    pattern_distributions.get(id1, {}),
                    pattern_distributions.get(id2, {})
                )
                metrics['pattern_similarity'][f'{id1}_vs_{id2}'] = similarity

        return metrics

    def _compare_patterns(self, instances_analysis: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Сравнивает паттерны поведения между инстансами."""
        comparison = {
            'pattern_usage_comparison': {},
            'unique_patterns': {},
            'common_patterns': set()
        }

        # Собираем паттерны от всех инстансов
        all_patterns = set()
        pattern_usage = defaultdict(dict)

        for instance_id, analysis in instances_analysis.items():
            patterns = analysis.get('decision_patterns', {}).get('patterns', {})
            pattern_usage[instance_id] = patterns
            all_patterns.update(patterns.keys())

        comparison['common_patterns'] = all_patterns

        # Сравниваем использование паттернов
        for pattern in all_patterns:
            usage = {}
            for instance_id in instances_analysis.keys():
                usage[instance_id] = pattern_usage[instance_id].get(pattern, 0)
            comparison['pattern_usage_comparison'][pattern] = usage

        return comparison

    def _compute_diversity_metrics(self, instances_analysis: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Вычисляет метрики разнообразия поведения."""
        diversity = {
            'pattern_diversity': 0.0,
            'behavior_variance': 0.0,
            'unique_behaviors': 0
        }

        # Вычисляем разнообразие паттернов
        pattern_sets = []
        for analysis in instances_analysis.values():
            patterns = set(analysis.get('decision_patterns', {}).get('patterns', {}).keys())
            pattern_sets.append(patterns)

        if pattern_sets:
            # Shannon diversity index для паттернов
            all_patterns = set()
            for p_set in pattern_sets:
                all_patterns.update(p_set)

            pattern_counts = Counter()
            for p_set in pattern_sets:
                for pattern in p_set:
                    pattern_counts[pattern] += 1

            total_instances = len(pattern_sets)
            diversity_score = 0.0
            for count in pattern_counts.values():
                p = count / total_instances
                if p > 0:
                    diversity_score -= p * (p ** 0.5)  # Упрощенная энтропия

            diversity['pattern_diversity'] = diversity_score
            diversity['unique_behaviors'] = len(all_patterns)

        return diversity

    def _calculate_trend(self, values: List[float]) -> float:
        """Вычисляет тренд значений (простая линейная регрессия)."""
        if len(values) < 2:
            return 0.0

        n = len(values)
        x = list(range(n))
        y = values

        # Вычисляем коэффициент наклона
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_xx = sum(xi * xi for xi in x)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)
        return slope

    def _calculate_pattern_similarity(self, dist1: Dict[str, float], dist2: Dict[str, float]) -> float:
        """Вычисляет схожесть распределений паттернов."""
        all_patterns = set(dist1.keys()) | set(dist2.keys())

        similarity = 0.0
        for pattern in all_patterns:
            p1 = dist1.get(pattern, 0.0)
            p2 = dist2.get(pattern, 0.0)
            similarity += 1.0 - abs(p1 - p2)

        return similarity / len(all_patterns) if all_patterns else 0.0