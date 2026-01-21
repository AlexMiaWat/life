"""
ComparisonMetrics - метрики для сравнения жизней

Вычисляет различные метрики для сравнения поведения,
эволюции и характеристик разных инстансов Life.
"""

import statistics
from typing import Dict, List, Any, Optional
from collections import defaultdict

from src.logging_config import get_logger

logger = get_logger(__name__)


class ComparisonMetrics:
    """
    Вычисляет метрики сравнения между разными инстансами Life.

    Метрики включают:
    - Метрики сходства эволюционных траекторий
    - Сравнение эффективности адаптации
    - Метрики разнообразия поведения
    - Статистические показатели производительности
    """

    def __init__(self):
        self.historical_data = defaultdict(list)

    def compute_similarity_metrics(
        self, instances_data: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Вычисляет метрики сходства между инстансами.

        Args:
            instances_data: Данные от всех инстансов

        Returns:
            Dict с метриками сходства
        """
        metrics = {
            "state_similarity": {},
            "behavior_similarity": {},
            "evolution_similarity": {},
            "overall_similarity": {},
        }

        instance_ids = list(instances_data.keys())
        if len(instance_ids) < 2:
            return metrics

        # Сравниваем попарно
        for i, id1 in enumerate(instance_ids):
            for id2 in instance_ids[i + 1 :]:
                pair_key = f"{id1}_vs_{id2}"

                data1 = instances_data[id1]
                data2 = instances_data[id2]

                # Сходство состояний
                state_sim = self._compute_state_similarity(data1, data2)
                metrics["state_similarity"][pair_key] = state_sim

                # Сходство поведения
                behavior_sim = self._compute_behavior_similarity(data1, data2)
                metrics["behavior_similarity"][pair_key] = behavior_sim

                # Сходство эволюции
                evolution_sim = self._compute_evolution_similarity(id1, id2)
                metrics["evolution_similarity"][pair_key] = evolution_sim

                # Общая схожесть
                overall = (state_sim + behavior_sim + evolution_sim) / 3.0
                metrics["overall_similarity"][pair_key] = overall

        return metrics

    def compute_performance_metrics(
        self, instances_data: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Вычисляет метрики производительности инстансов.

        Args:
            instances_data: Данные от всех инстансов

        Returns:
            Dict с метриками производительности
        """
        metrics = {
            "survival_rates": {},
            "adaptation_efficiency": {},
            "resource_usage": {},
            "stability_metrics": {},
        }

        for instance_id, data in instances_data.items():
            status = data.get("status", {})
            snapshot = data.get("snapshot")

            if not snapshot:
                continue

            # Выживаемость
            is_alive = status.get("is_alive", False)
            uptime = status.get("uptime", 0)
            metrics["survival_rates"][instance_id] = {
                "is_alive": is_alive,
                "uptime": uptime,
                "ticks_survived": snapshot.get("ticks", 0),
            }

            # Эффективность адаптации (нормализованная сумма всех параметров)
            stability = snapshot.get("stability", 0)
            integrity = snapshot.get("integrity", 0)
            energy = snapshot.get("energy", 0)

            # Нормализуем energy к диапазону 0-1
            normalized_energy = energy / 100.0
            adaptation_score = (stability + integrity + normalized_energy) / 3.0
            metrics["adaptation_efficiency"][instance_id] = adaptation_score

            # Использование ресурсов (прокси через ticks и logs)
            logs = data.get("recent_logs") or []
            metrics["resource_usage"][instance_id] = {
                "events_processed": len([l for l in logs if l.get("stage") == "event"]),
                "decisions_made": len([l for l in logs if l.get("stage") == "decision"]),
                "actions_taken": len([l for l in logs if l.get("stage") == "action"]),
            }

            # Стабильность
            state_history = self.historical_data[instance_id]
            if len(state_history) >= 3:
                stability_values = [s.get("stability", 0) for s in state_history[-10:]]
                stability_variance = (
                    statistics.variance(stability_values) if len(stability_values) > 1 else 0
                )
                metrics["stability_metrics"][instance_id] = {
                    "variance": stability_variance,
                    "trend": self._calculate_trend(stability_values),
                    "consistency": 1.0 - min(stability_variance, 1.0),
                }

        # Сохраняем исторические данные
        for instance_id, data in instances_data.items():
            if "snapshot" in data:
                self.historical_data[instance_id].append(data["snapshot"])

        # Ограничиваем историю (последние 100 записей)
        for instance_id in self.historical_data:
            if len(self.historical_data[instance_id]) > 100:
                self.historical_data[instance_id] = self.historical_data[instance_id][-100:]

        return metrics

    def compute_diversity_metrics(
        self, instances_data: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Вычисляет метрики разнообразия поведения инстансов.

        Args:
            instances_data: Данные от всех инстансов

        Returns:
            Dict с метриками разнообразия
        """
        metrics = {
            "behavior_diversity": 0.0,
            "state_diversity": 0.0,
            "pattern_diversity": 0.0,
            "unique_behaviors": set(),
            "diversity_score": 0.0,
        }

        # Собираем данные о поведении
        behaviors = []
        states = []
        patterns = set()

        for data in instances_data.values():
            logs = data.get("recent_logs") or []
            snapshot = data.get("snapshot")

            # Поведение (последовательности решений)
            decisions = [
                l.get("data", {}).get("pattern") for l in logs if l.get("stage") == "decision"
            ]
            if decisions:
                behaviors.append(tuple(decisions[-10:]))  # Последние 10 решений

            # Состояния
            if snapshot:
                state_vector = (
                    snapshot.get("energy", 0),
                    snapshot.get("stability", 0),
                    snapshot.get("integrity", 0),
                )
                states.append(state_vector)

            # Паттерны
            decision_patterns = set()
            if logs:
                for log in logs:
                    if log.get("stage") == "decision":
                        pattern = log.get("data", {}).get("pattern")
                        if pattern:
                            decision_patterns.add(pattern)
            patterns.update(decision_patterns)

        # Вычисляем разнообразие
        if behaviors:
            unique_behaviors = len(set(behaviors))
            total_behaviors = len(behaviors)
            # Для случая одного инстанса diversity = 1.0 (максимальное разнообразие в рамках одного поведения)
            metrics["behavior_diversity"] = (
                unique_behaviors / total_behaviors if total_behaviors > 0 else 0.0
            )

        if states and len(states) >= 2:
            # Вычисляем среднее расстояние между состояниями
            distances = []
            for i, s1 in enumerate(states):
                for s2 in states[i + 1 :]:
                    distance = sum((a - b) ** 2 for a, b in zip(s1, s2)) ** 0.5
                    distances.append(distance)

            if distances:
                metrics["state_diversity"] = statistics.mean(distances)

        metrics["pattern_diversity"] = len(patterns)
        metrics["unique_behaviors"] = patterns

        # Общий score разнообразия
        diversity_components = [
            metrics["behavior_diversity"],
            min(metrics["state_diversity"] / 10.0, 1.0) if metrics["state_diversity"] else 0,
            min(metrics["pattern_diversity"] / 5.0, 1.0),
        ]

        metrics["diversity_score"] = (
            statistics.mean(diversity_components) if diversity_components else 0.0
        )

        return metrics

    def compute_evolution_metrics(
        self, instances_data: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Вычисляет метрики эволюции инстансов со временем.

        Args:
            instances_data: Данные от всех инстансов

        Returns:
            Dict с метриками эволюции
        """
        metrics = {
            "growth_rates": {},
            "adaptation_curves": {},
            "survival_curves": {},
            "convergence_analysis": {},
        }

        for instance_id, data in instances_data.items():
            history = self.historical_data.get(instance_id, [])

            if len(history) < 2:
                continue

            # Темпы роста
            ticks = [h.get("ticks", 0) for h in history]
            energies = [h.get("energy", 0) for h in history]
            stabilities = [h.get("stability", 0) for h in history]

            energy_trend = self._calculate_trend(energies)
            stability_trend = self._calculate_trend(stabilities)

            metrics["growth_rates"][instance_id] = {
                "energy_growth": energy_trend,
                "stability_growth": stability_trend,
                "overall_growth": (energy_trend + stability_trend) / 2.0,
            }

            # Кривая адаптации
            adaptation_scores = []
            for h in history:
                score = (h.get("stability", 0) + h.get("integrity", 0)) / 2.0
                adaptation_scores.append(score)

            metrics["adaptation_curves"][instance_id] = {
                "scores": adaptation_scores,
                "trend": self._calculate_trend(adaptation_scores),
                "final_score": adaptation_scores[-1] if adaptation_scores else 0,
            }

        # Анализ сходимости (если есть несколько инстансов)
        if len(metrics["adaptation_curves"]) >= 2:
            final_scores = [data["final_score"] for data in metrics["adaptation_curves"].values()]
            metrics["convergence_analysis"] = {
                "mean_final_score": statistics.mean(final_scores),
                "std_final_score": statistics.stdev(final_scores) if len(final_scores) > 1 else 0,
                "convergence": (
                    1.0 - (statistics.stdev(final_scores) / statistics.mean(final_scores))
                    if final_scores
                    else 0
                ),
            }

        return metrics

    def get_summary_report(self, instances_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Генерирует сводный отчет по всем метрикам сравнения.

        Args:
            instances_data: Данные от всех инстансов

        Returns:
            Dict со сводным отчетом
        """
        return {
            "similarity_metrics": self.compute_similarity_metrics(instances_data),
            "performance_metrics": self.compute_performance_metrics(instances_data),
            "diversity_metrics": self.compute_diversity_metrics(instances_data),
            "evolution_metrics": self.compute_evolution_metrics(instances_data),
            "timestamp": (
                instances_data.get("timestamp")
                if isinstance(instances_data, dict) and "timestamp" in instances_data
                else None
            ),
        }

    def _compute_state_similarity(self, data1: Dict[str, Any], data2: Dict[str, Any]) -> float:
        """Вычисляет схожесть состояний двух инстансов."""
        snapshot1 = data1.get("snapshot")
        snapshot2 = data2.get("snapshot")

        if not snapshot1 or not snapshot2:
            return 0.0

        # Сравниваем ключевые параметры состояния
        params = ["energy", "stability", "integrity"]
        similarities = []

        for param in params:
            val1 = snapshot1.get(param, 0)
            val2 = snapshot2.get(param, 0)
            # Нормализованная схожесть (0-1, где 1 - полное совпадение)
            similarity = 1.0 - min(abs(val1 - val2) / 100.0, 1.0)
            similarities.append(similarity)

        return statistics.mean(similarities) if similarities else 0.0

    def _compute_behavior_similarity(self, data1: Dict[str, Any], data2: Dict[str, Any]) -> float:
        """Вычисляет схожесть поведения двух инстансов."""
        logs1 = data1.get("recent_logs", [])
        logs2 = data2.get("recent_logs", [])

        # Извлекаем последовательности решений
        decisions1 = [
            l.get("data", {}).get("pattern") for l in logs1 if l.get("stage") == "decision"
        ]
        decisions2 = [
            l.get("data", {}).get("pattern") for l in logs2 if l.get("stage") == "decision"
        ]

        if not decisions1 or not decisions2:
            return 0.0

        # Сравниваем распределения паттернов
        from collections import Counter

        count1 = Counter(decisions1)
        count2 = Counter(decisions2)

        all_patterns = set(count1.keys()) | set(count2.keys())
        similarities = []

        for pattern in all_patterns:
            freq1 = count1.get(pattern, 0) / len(decisions1)
            freq2 = count2.get(pattern, 0) / len(decisions2)
            similarity = 1.0 - abs(freq1 - freq2)
            similarities.append(similarity)

        return statistics.mean(similarities) if similarities else 0.0

    def _compute_evolution_similarity(self, instance_id1: str, instance_id2: str) -> float:
        """Вычисляет схожесть эволюционных траекторий."""
        history1 = self.historical_data.get(instance_id1, [])
        history2 = self.historical_data.get(instance_id2, [])

        if len(history1) < 2 or len(history2) < 2:
            return 0.0

        # Сравниваем тренды изменения состояний
        params = ["energy", "stability", "integrity"]
        similarities = []

        for param in params:
            values1 = [h.get(param, 0) for h in history1]
            values2 = [h.get(param, 0) for h in history2]

            trend1 = self._calculate_trend(values1)
            trend2 = self._calculate_trend(values2)

            # Нормализованная схожесть трендов
            max_trend = max(abs(trend1), abs(trend2), 0.001)  # Избегаем деления на 0
            similarity = 1.0 - min(abs(trend1 - trend2) / max_trend, 1.0)
            similarities.append(similarity)

        return statistics.mean(similarities) if similarities else 0.0

    def _calculate_trend(self, values: List[float]) -> float:
        """Вычисляет тренд значений (наклон линии регрессии)."""
        if len(values) < 2:
            return 0.0

        n = len(values)
        x = list(range(n))
        y = values

        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_xx = sum(xi * xi for xi in x)

        denominator = n * sum_xx - sum_x * sum_x
        if denominator == 0:
            return 0.0

        return (n * sum_xy - sum_x * sum_y) / denominator
