"""
Внешний наблюдатель за системой Life.

Этот модуль предоставляет инструменты для пассивного наблюдения и анализа
поведения системы Life на основе логов, метрик и сохраненных состояний.

Не вмешивается в runtime системы, работает только с внешними данными.
"""

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """Метрики производительности и состояния системы."""
    timestamp: float = field(default_factory=time.time)

    # Базовые метрики
    cycle_count: int = 0
    uptime_seconds: float = 0.0
    memory_entries_count: int = 0

    # Метрики компонентов
    learning_effectiveness: float = 0.0
    adaptation_rate: float = 0.0
    decision_success_rate: float = 0.0

    # Метрики стабильности
    error_count: int = 0
    integrity_score: float = 1.0
    energy_level: float = 1.0

    # Метрики активности
    action_count: int = 0
    event_processing_rate: float = 0.0  # событий в секунду
    state_change_frequency: float = 0.0  # изменений состояния в секунду


@dataclass
class BehaviorPattern:
    """Паттерн поведения системы."""
    pattern_type: str
    description: str
    frequency: float
    impact_score: float
    first_observed: float
    last_observed: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ObservationReport:
    """Отчет внешнего наблюдения."""
    observation_period: Tuple[float, float]  # start_time, end_time
    metrics_summary: SystemMetrics
    behavior_patterns: List[BehaviorPattern]
    trends: Dict[str, str]  # metric_name -> trend_direction
    anomalies: List[Dict[str, Any]]
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать отчет в словарь для сериализации."""
        return {
            "observation_period": self.observation_period,
            "metrics_summary": {
                "cycle_count": self.metrics_summary.cycle_count,
                "uptime_seconds": self.metrics_summary.uptime_seconds,
                "memory_entries_count": self.metrics_summary.memory_entries_count,
                "learning_effectiveness": self.metrics_summary.learning_effectiveness,
                "adaptation_rate": self.metrics_summary.adaptation_rate,
                "decision_success_rate": self.metrics_summary.decision_success_rate,
                "error_count": self.metrics_summary.error_count,
                "integrity_score": self.metrics_summary.integrity_score,
                "energy_level": self.metrics_summary.energy_level,
                "action_count": self.metrics_summary.action_count,
                "event_processing_rate": self.metrics_summary.event_processing_rate,
                "state_change_frequency": self.metrics_summary.state_change_frequency,
            },
            "behavior_patterns": [
                {
                    "pattern_type": p.pattern_type,
                    "description": p.description,
                    "frequency": p.frequency,
                    "impact_score": p.impact_score,
                    "first_observed": p.first_observed,
                    "last_observed": p.last_observed,
                    "metadata": p.metadata,
                }
                for p in self.behavior_patterns
            ],
            "trends": self.trends,
            "anomalies": self.anomalies,
            "recommendations": self.recommendations,
        }


class ExternalObserver:
    """
    Внешний наблюдатель за системой Life.

    Анализирует логи, метрики и паттерны поведения без вмешательства в систему.
    """

    def __init__(self, logs_directory: Optional[Path] = None, snapshots_directory: Optional[Path] = None):
        self.logs_directory = logs_directory or Path("logs")
        self.snapshots_directory = snapshots_directory or Path("data/snapshots")
        self.observation_history: List[ObservationReport] = []

    def observe_from_logs(self, start_time: Optional[float] = None, end_time: Optional[float] = None) -> ObservationReport:
        """
        Проанализировать поведение системы на основе логов.

        Args:
            start_time: Начало периода наблюдения (timestamp)
            end_time: Конец периода наблюдения (timestamp)

        Returns:
            Отчет наблюдения
        """
        if start_time is None:
            start_time = time.time() - 3600  # Последний час по умолчанию
        if end_time is None:
            end_time = time.time()

        # Собираем метрики из логов
        metrics = self._extract_metrics_from_logs(start_time, end_time)

        # Анализируем паттерны поведения
        patterns = self._analyze_behavior_patterns(start_time, end_time)

        # Определяем тренды
        trends = self._calculate_trends(metrics)

        # Ищем аномалии
        anomalies = self._detect_anomalies(metrics, patterns)

        # Формируем рекомендации
        recommendations = self._generate_recommendations(metrics, trends, anomalies)

        report = ObservationReport(
            observation_period=(start_time, end_time),
            metrics_summary=metrics,
            behavior_patterns=patterns,
            trends=trends,
            anomalies=anomalies,
            recommendations=recommendations,
        )

        self.observation_history.append(report)
        return report

    def observe_from_snapshots(self, snapshot_paths: List[Path]) -> ObservationReport:
        """
        Проанализировать поведение системы на основе снимков состояний.

        Args:
            snapshot_paths: Список путей к файлам снимков

        Returns:
            Отчет наблюдения
        """
        if not snapshot_paths:
            raise ValueError("Необходимо указать хотя бы один файл снимка")

        # Загружаем и анализируем снимки
        snapshots_data = []
        for path in snapshot_paths:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    snapshots_data.append(data)
            except Exception as e:
                logger.warning(f"Не удалось загрузить снимок {path}: {e}")

        if not snapshots_data:
            raise ValueError("Не удалось загрузить ни один снимок")

        # Анализируем временной ряд
        start_time = min(s['timestamp'] for s in snapshots_data)
        end_time = max(s['timestamp'] for s in snapshots_data)

        # Собираем метрики из снимков
        metrics = self._extract_metrics_from_snapshots(snapshots_data)

        # Анализируем паттерны
        patterns = self._analyze_snapshot_patterns(snapshots_data)

        # Определяем тренды
        trends = self._calculate_snapshot_trends(snapshots_data)

        # Ищем аномалии
        anomalies = self._detect_snapshot_anomalies(snapshots_data)

        # Формируем рекомендации
        recommendations = self._generate_snapshot_recommendations(snapshots_data, trends, anomalies)

        report = ObservationReport(
            observation_period=(start_time, end_time),
            metrics_summary=metrics,
            behavior_patterns=patterns,
            trends=trends,
            anomalies=anomalies,
            recommendations=recommendations,
        )

        self.observation_history.append(report)
        return report

    def save_report(self, report: ObservationReport, output_path: Path) -> Path:
        """Сохранить отчет в файл."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info(f"Отчет сохранен: {output_path}")
        return output_path

    def get_observation_history_summary(self) -> Dict[str, Any]:
        """Получить сводку по истории наблюдений."""
        if not self.observation_history:
            return {"error": "История наблюдений пуста"}

        total_observations = len(self.observation_history)

        # Собираем статистику по метрикам
        avg_metrics = {}
        metric_fields = [
            'cycle_count', 'uptime_seconds', 'memory_entries_count',
            'learning_effectiveness', 'adaptation_rate', 'decision_success_rate',
            'error_count', 'integrity_score', 'energy_level',
            'action_count', 'event_processing_rate', 'state_change_frequency'
        ]

        for field in metric_fields:
            values = [getattr(obs.metrics_summary, field) for obs in self.observation_history]
            if values:
                avg_metrics[field] = sum(values) / len(values)

        # Анализируем тренды
        recent_trends = {}
        if len(self.observation_history) >= 2:
            latest = self.observation_history[-1]
            previous = self.observation_history[-2]

            for field in ['integrity_score', 'energy_level', 'error_count']:
                latest_val = getattr(latest.metrics_summary, field)
                prev_val = getattr(previous.metrics_summary, field)

                if latest_val > prev_val:
                    trend = "improving" if field in ['integrity_score', 'energy_level'] else "worsening"
                elif latest_val < prev_val:
                    trend = "worsening" if field in ['integrity_score', 'energy_level'] else "improving"
                else:
                    trend = "stable"

                recent_trends[field] = trend

        return {
            "total_observations": total_observations,
            "average_metrics": avg_metrics,
            "recent_trends": recent_trends,
            "observation_period": {
                "earliest": min(obs.observation_period[0] for obs in self.observation_history),
                "latest": max(obs.observation_period[1] for obs in self.observation_history),
            }
        }

    def _extract_metrics_from_logs(self, start_time: float, end_time: float) -> SystemMetrics:
        """
        Извлечь метрики из логов.

        Args:
            start_time: Начало периода анализа
            end_time: Конец периода анализа

        Returns:
            SystemMetrics с извлеченными данными или значениями по умолчанию при ошибках
        """
        try:
            # TODO: Реализовать анализ реальных логов
            # Пока возвращаем демо-данные с обработкой ошибок

            # Имитация чтения логов
            logs_data = self._read_logs_safely(start_time, end_time)

            if logs_data:
                return SystemMetrics(
                    cycle_count=logs_data.get('cycle_count', 1000),
                    uptime_seconds=end_time - start_time,
                    memory_entries_count=logs_data.get('memory_count', 500),
                    learning_effectiveness=max(0.0, min(1.0, logs_data.get('learning_eff', 0.75))),
                    adaptation_rate=max(0.0, min(1.0, logs_data.get('adaptation_rate', 0.6))),
                    decision_success_rate=max(0.0, min(1.0, logs_data.get('decision_rate', 0.85))),
                    error_count=max(0, logs_data.get('error_count', 5)),
                    integrity_score=max(0.0, min(1.0, logs_data.get('integrity', 0.95))),
                    energy_level=max(0.0, min(1.0, logs_data.get('energy', 0.8))),
                    action_count=max(0, logs_data.get('action_count', 200)),
                    event_processing_rate=max(0.0, logs_data.get('event_rate', 2.5)),
                    state_change_frequency=max(0.0, logs_data.get('change_rate', 1.2)),
                )
            else:
                logger.warning("Не удалось прочитать логи, используем значения по умолчанию")
                return self._get_default_metrics(start_time, end_time)

        except Exception as e:
            logger.error(f"Ошибка при извлечении метрик из логов: {e}")
            return self._get_default_metrics(start_time, end_time)

    def _read_logs_safely(self, start_time: float, end_time: float) -> Optional[Dict[str, Any]]:
        """
        Безопасно прочитать логи за указанный период.

        Returns:
            Словарь с данными логов или None при ошибке
        """
        try:
            # Проверяем существование директории логов
            if not self.logs_directory.exists():
                logger.warning(f"Директория логов не существует: {self.logs_directory}")
                return None

            # TODO: Реализовать чтение и анализ реальных логов
            # Пока имитируем успешное чтение
            return {
                'cycle_count': 1000,
                'memory_count': 500,
                'learning_eff': 0.75,
                'adaptation_rate': 0.6,
                'decision_rate': 0.85,
                'error_count': 5,
                'integrity': 0.95,
                'energy': 0.8,
                'action_count': 200,
                'event_rate': 2.5,
                'change_rate': 1.2,
            }

        except Exception as e:
            logger.error(f"Ошибка при чтении логов: {e}")
            return None

    def _get_default_metrics(self, start_time: float, end_time: float) -> SystemMetrics:
        """Получить метрики по умолчанию при ошибках."""
        return SystemMetrics(
            cycle_count=0,
            uptime_seconds=end_time - start_time,
            memory_entries_count=0,
            learning_effectiveness=0.5,  # Нейтральное значение
            adaptation_rate=0.5,
            decision_success_rate=0.5,
            error_count=0,
            integrity_score=0.5,
            energy_level=0.5,
            action_count=0,
            event_processing_rate=0.0,
            state_change_frequency=0.0,
        )

    def _extract_metrics_from_snapshots(self, snapshots: List[Dict]) -> SystemMetrics:
        """Извлечь метрики из снимков. Заглушка для реализации."""
        # TODO: Реализовать анализ снимков
        return SystemMetrics(
            cycle_count=len(snapshots),
            uptime_seconds=snapshots[-1]['timestamp'] - snapshots[0]['timestamp'],
            memory_entries_count=500,
            learning_effectiveness=0.75,
            adaptation_rate=0.6,
            decision_success_rate=0.85,
            error_count=2,
            integrity_score=0.95,
            energy_level=0.8,
            action_count=100,
            event_processing_rate=2.0,
            state_change_frequency=1.0,
        )

    def _analyze_behavior_patterns(self, start_time: float, end_time: float) -> List[BehaviorPattern]:
        """
        Анализировать паттерны поведения на основе доступных данных.

        Args:
            start_time: Начало периода анализа
            end_time: Конец периода анализа

        Returns:
            Список паттернов поведения или пустой список при ошибках
        """
        try:
            patterns = []

            # TODO: Реализовать анализ реальных паттернов из логов
            # Пока возвращаем демо-паттерны с проверкой корректности

            # Проверяем корректность временных интервалов
            duration = end_time - start_time
            if duration <= 0:
                logger.warning("Некорректный временной интервал для анализа паттернов")
                return patterns

            # Имитируем обнаружение паттернов
            patterns.extend([
                BehaviorPattern(
                    pattern_type="learning_cycle",
                    description="Регулярные циклы обучения каждые 75 тиков",
                    frequency=min(1.0, max(0.0, 0.8)),  # Ограничиваем диапазон
                    impact_score=min(1.0, max(0.0, 0.7)),
                    first_observed=max(start_time, start_time + 10),  # Не раньше start_time
                    last_observed=min(end_time, end_time - 10),  # Не позже end_time
                    metadata={"confidence": 0.85, "occurrences": 12}
                ),
                BehaviorPattern(
                    pattern_type="adaptation_burst",
                    description="Периоды интенсивной адаптации при изменении условий",
                    frequency=min(1.0, max(0.0, 0.3)),
                    impact_score=min(1.0, max(0.0, 0.8)),
                    first_observed=max(start_time, start_time + 100),
                    last_observed=min(end_time, end_time - 50),
                    metadata={"confidence": 0.72, "occurrences": 3}
                ),
            ])

            # Фильтруем паттерны с некорректными данными
            valid_patterns = []
            for pattern in patterns:
                if (pattern.first_observed < pattern.last_observed and
                    pattern.frequency >= 0 and pattern.frequency <= 1 and
                    pattern.impact_score >= 0 and pattern.impact_score <= 1):
                    valid_patterns.append(pattern)
                else:
                    logger.warning(f"Пропущен некорректный паттерн: {pattern.pattern_type}")

            logger.info(f"Обнаружено {len(valid_patterns)} паттернов поведения")
            return valid_patterns

        except Exception as e:
            logger.error(f"Ошибка при анализе паттернов поведения: {e}")
            return []

    def _analyze_snapshot_patterns(self, snapshots: List[Dict]) -> List[BehaviorPattern]:
        """Анализировать паттерны в снимках. Заглушка для реализации."""
        return [
            BehaviorPattern(
                pattern_type="memory_growth",
                description="Постепенный рост количества записей в памяти",
                frequency=1.0,
                impact_score=0.6,
                first_observed=snapshots[0]['timestamp'],
                last_observed=snapshots[-1]['timestamp'],
            ),
        ]

    def _calculate_trends(self, metrics: SystemMetrics) -> Dict[str, str]:
        """Рассчитать тренды. Заглушка для реализации."""
        return {
            "integrity_score": "stable",
            "energy_level": "declining",
            "error_count": "increasing",
            "learning_effectiveness": "improving",
        }

    def _calculate_snapshot_trends(self, snapshots: List[Dict]) -> Dict[str, str]:
        """Рассчитать тренды по снимкам. Заглушка для реализации."""
        return {
            "memory_growth": "increasing",
            "energy_level": "stable",
            "adaptation_rate": "improving",
        }

    def _detect_anomalies(self, metrics: SystemMetrics, patterns: List[BehaviorPattern]) -> List[Dict[str, Any]]:
        """
        Обнаружить аномалии в метриках и паттернах.

        Args:
            metrics: Метрики системы
            patterns: Обнаруженные паттерны поведения

        Returns:
            Список обнаруженных аномалий
        """
        anomalies = []

        try:
            # Проверяем базовые метрики на аномалии
            if metrics.error_count > 10:
                anomalies.append({
                    "type": "high_error_rate",
                    "description": f"Высокий уровень ошибок: {metrics.error_count}",
                    "severity": "high",
                    "timestamp": metrics.timestamp,
                    "metric": "error_count",
                    "value": metrics.error_count,
                    "threshold": 10,
                })

            # Проверяем уровень энергии
            if metrics.energy_level < 0.2:
                anomalies.append({
                    "type": "low_energy_level",
                    "description": ".2f",
                    "severity": "medium",
                    "timestamp": metrics.timestamp,
                    "metric": "energy_level",
                    "value": metrics.energy_level,
                    "threshold": 0.2,
                })

            # Проверяем уровень integrity
            if metrics.integrity_score < 0.3:
                anomalies.append({
                    "type": "low_integrity_score",
                    "description": ".2f",
                    "severity": "critical",
                    "timestamp": metrics.timestamp,
                    "metric": "integrity_score",
                    "value": metrics.integrity_score,
                    "threshold": 0.3,
                })

            # Проверяем экстремальные значения других метрик
            checks = [
                (metrics.learning_effectiveness < 0.1, "very_low_learning", "Критически низкая эффективность обучения", "critical"),
                (metrics.adaptation_rate < 0.1, "very_low_adaptation", "Критически низкая скорость адаптации", "high"),
                (metrics.decision_success_rate < 0.2, "very_low_decision_success", "Критически низкая успешность решений", "critical"),
                (metrics.event_processing_rate > 50, "high_event_rate", "Аномально высокая скорость обработки событий", "medium"),
            ]

            for condition, anomaly_type, description, severity in checks:
                if condition:
                    anomalies.append({
                        "type": anomaly_type,
                        "description": description,
                        "severity": severity,
                        "timestamp": metrics.timestamp,
                    })

            # Проверяем паттерны на аномалии
            for pattern in patterns:
                if pattern.frequency > 0.95:  # Слишком частый паттерн
                    anomalies.append({
                        "type": "dominant_pattern",
                        "description": f"Доминирующий паттерн поведения: {pattern.pattern_type}",
                        "severity": "low",
                        "timestamp": metrics.timestamp,
                        "pattern": pattern.pattern_type,
                        "frequency": pattern.frequency,
                    })

            logger.info(f"Обнаружено {len(anomalies)} аномалий")
            return anomalies

        except Exception as e:
            logger.error(f"Ошибка при обнаружении аномалий: {e}")
            return []

    def _detect_snapshot_anomalies(self, snapshots: List[Dict]) -> List[Dict[str, Any]]:
        """Обнаружить аномалии в снимках. Заглушка для реализации."""
        return []

    def _generate_recommendations(self, metrics: SystemMetrics, trends: Dict[str, str],
                                anomalies: List[Dict]) -> List[str]:
        """
        Сгенерировать рекомендации на основе метрик, трендов и аномалий.

        Args:
            metrics: Метрики системы
            trends: Тренды метрик
            anomalies: Обнаруженные аномалии

        Returns:
            Список рекомендаций
        """
        recommendations = []

        try:
            # Рекомендации на основе трендов
            trend_recommendations = {
                "energy_level": {
                    "declining": "Проверить энергопотребление системы и источники энергии",
                    "stable": "Уровень энергии стабильный - положительный показатель",
                    "improving": "Энергия системы растет - хорошая динамика"
                },
                "integrity_score": {
                    "declining": "Критично: проверить целостность системы и механизмы валидации",
                    "stable": "Целостность системы стабильна",
                    "improving": "Целостность системы улучшается"
                },
                "error_count": {
                    "increasing": "Растет количество ошибок - требуется анализ логов",
                    "stable": "Количество ошибок стабильно",
                    "decreasing": "Количество ошибок уменьшается - положительная динамика"
                },
                "learning_effectiveness": {
                    "improving": "Обучение работает эффективно, продолжить наблюдение",
                    "stable": "Эффективность обучения стабильна",
                    "declining": "Эффективность обучения падает - проверить механизмы обучения"
                }
            }

            for metric, trend in trends.items():
                if metric in trend_recommendations and trend in trend_recommendations[metric]:
                    recommendations.append(trend_recommendations[metric][trend])

            # Рекомендации на основе метрик
            if metrics.error_count > 0:
                recommendations.append("Проанализировать причины ошибок в логах системы")

            if metrics.energy_level < 0.5:
                recommendations.append("Мониторить уровень энергии - он ниже среднего")

            if metrics.integrity_score < 0.8:
                recommendations.append("Обратить внимание на целостность системы")

            if metrics.learning_effectiveness > 0.8:
                recommendations.append("Механизмы обучения работают очень эффективно")

            # Рекомендации на основе аномалий
            severity_actions = {
                "critical": "Немедленно проанализировать и устранить",
                "high": "Приоритизировать анализ и исправление",
                "medium": "Запланировать проверку в ближайшее время",
                "low": "Мониторить ситуацию"
            }

            for anomaly in anomalies:
                severity = anomaly.get("severity", "medium")
                action = severity_actions.get(severity, "Проверить")
                anomaly_type = anomaly.get("type", "unknown")
                recommendations.append(f"{action}: аномалия '{anomaly_type}' ({severity} приоритет)")

            # Общие рекомендации
            if not anomalies:
                recommendations.append("Система работает стабильно без критических проблем")

            if len(recommendations) > 10:
                # Ограничиваем количество рекомендаций
                recommendations = recommendations[:10]
                recommendations.append("... и еще несколько рекомендаций (полный список в отчете)")

            logger.info(f"Сгенерировано {len(recommendations)} рекомендаций")
            return recommendations

        except Exception as e:
            logger.error(f"Ошибка при генерации рекомендаций: {e}")
            return ["Произошла ошибка при генерации рекомендаций - требуется ручной анализ"]

    def _generate_snapshot_recommendations(self, snapshots: List[Dict], trends: Dict[str, str],
                                         anomalies: List[Dict]) -> List[str]:
        """Сгенерировать рекомендации по снимкам. Заглушка для реализации."""
        return ["Продолжить мониторинг состояния системы"]