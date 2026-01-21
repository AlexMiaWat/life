"""
Technical Behavior Monitor для системы Life.

Этот модуль предоставляет инструмент технического мониторинга поведения системы Life,
сосредотачиваясь на технических метриках производительности, стабильности и адаптивности.

Технический мониторинг включает:
- Производительность: анализ скорости и эффективности операций
- Стабильность: оценка надежности и предсказуемости поведения
- Адаптивность: измерение способности к изменениям и обучению
- Целостность: проверка согласованности внутренних структур

Использование:
    monitor = TechnicalBehaviorMonitor()
    snapshot = monitor.capture_system_snapshot(self_state, memory, learning_engine, adaptation_manager, decision_engine)
    report = monitor.analyze_snapshot(snapshot)
"""

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from src.runtime.data_collection_manager import DataCollectionManager

logger = logging.getLogger(__name__)


class ComponentInterface(ABC):
    """Базовый интерфейс для компонентов системы."""

    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """Получить параметры компонента."""
        pass

    @abstractmethod
    def validate_state(self) -> bool:
        """Проверить корректность состояния компонента."""
        pass


class MemoryInterface(ABC):
    """Интерфейс для компонента памяти."""

    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику памяти."""
        pass

    @abstractmethod
    def validate_integrity(self) -> bool:
        """Проверить целостность памяти."""
        pass


class DecisionEngineInterface(ABC):
    """Интерфейс для движка принятия решений."""

    @abstractmethod
    def get_recent_decisions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Получить недавние решения."""
        pass

    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику принятия решений."""
        pass


@dataclass
class TechnicalSnapshot:
    """Снимок технического состояния системы для анализа."""

    timestamp: float = field(default_factory=time.time)
    self_state: Dict[str, Any] = field(default_factory=dict)
    memory_stats: Dict[str, Any] = field(default_factory=dict)
    learning_params: Dict[str, Any] = field(default_factory=dict)
    adaptation_params: Dict[str, Any] = field(default_factory=dict)
    decision_history: List[Any] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TechnicalReport:
    """Технический отчет о поведении системы."""

    timestamp: float = field(default_factory=time.time)
    snapshot: TechnicalSnapshot = field(default_factory=TechnicalSnapshot)
    performance: Dict[str, Any] = field(default_factory=dict)
    stability: Dict[str, Any] = field(default_factory=dict)
    adaptability: Dict[str, Any] = field(default_factory=dict)
    integrity: Dict[str, Any] = field(default_factory=dict)
    overall_assessment: Dict[str, Any] = field(default_factory=dict)


class TechnicalBehaviorMonitor:
    """
    Технический монитор поведения системы Life.

    Предоставляет интерфейс для анализа технических аспектов системы
    без философских интерпретаций.
    """

    def __init__(self, data_collection_manager: Optional['DataCollectionManager'] = None):
        """
        Инициализация технического монитора.

        Args:
            data_collection_manager: Менеджер сбора данных для асинхронного сохранения
        """
        # История отчетов для анализа трендов
        self.report_history: List[TechnicalReport] = []
        self.max_history_size = 100

        # Менеджер сбора данных для асинхронных операций
        self.data_collection_manager = data_collection_manager

    def capture_system_snapshot(
        self, self_state, memory, learning_engine, adaptation_manager, decision_engine
    ) -> TechnicalSnapshot:
        """
        Захватить снимок текущего технического состояния системы.

        Args:
            self_state: Текущее состояние системы
            memory: Память системы
            learning_engine: Движок обучения
            adaptation_manager: Менеджер адаптации
            decision_engine: Движок принятия решений

        Returns:
            TechnicalSnapshot: Снимок состояния системы
        """
        snapshot = TechnicalSnapshot()

        try:
            # Захват состояния системы
            snapshot.self_state = self._extract_self_state_data(self_state)
        except Exception as e:
            logger.warning(f"Failed to capture self state: {e}")
            snapshot.self_state = {"error": str(e)}

        try:
            # Захват статистики памяти
            snapshot.memory_stats = memory.get_statistics()
        except Exception as e:
            logger.warning(f"Failed to capture memory stats: {e}")
            snapshot.memory_stats = {"error": str(e)}

        try:
            # Захват параметров обучения
            snapshot.learning_params = learning_engine.get_parameters()
        except Exception as e:
            logger.warning(f"Failed to capture learning params: {e}")
            snapshot.learning_params = {"error": str(e)}

        try:
            # Захват параметров адаптации
            snapshot.adaptation_params = adaptation_manager.get_parameters()
        except Exception as e:
            logger.warning(f"Failed to capture adaptation params: {e}")
            snapshot.adaptation_params = {"error": str(e)}

        try:
            # Захват истории решений (последние 100)
            snapshot.decision_history = decision_engine.get_recent_decisions(limit=100)
        except Exception as e:
            logger.warning(f"Failed to capture decision history: {e}")
            snapshot.decision_history = []

        try:
            # Захват метрик производительности
            snapshot.performance_metrics = self._collect_performance_metrics(
                self_state, memory, learning_engine, adaptation_manager, decision_engine
            )
        except Exception as e:
            logger.warning(f"Failed to collect performance metrics: {e}")
            snapshot.performance_metrics = {"error": str(e)}

        return snapshot

    def _extract_self_state_data(self, self_state: Any) -> Dict[str, Any]:
        """Извлечь данные из self_state для анализа с валидацией."""
        data: Dict[str, Any] = {}

        # Основные параметры состояния с валидацией типов
        try:
            cycle_count = getattr(self_state, "cycle_count", 0)
            data["cycle_count"] = int(cycle_count) if isinstance(cycle_count, (int, float)) else 0
        except (ValueError, TypeError):
            data["cycle_count"] = 0

        try:
            current_phase = getattr(self_state, "current_phase", "unknown")
            data["current_phase"] = (
                str(current_phase) if isinstance(current_phase, str) else "unknown"
            )
        except (ValueError, TypeError):
            data["current_phase"] = "unknown"

        try:
            energy_level = getattr(self_state, "energy_level", 0.0)
            data["energy_level"] = (
                float(energy_level) if isinstance(energy_level, (int, float)) else 0.0
            )
            # Валидация диапазона
            data["energy_level"] = max(0.0, min(1.0, data["energy_level"]))
        except (ValueError, TypeError):
            data["energy_level"] = 0.0

        try:
            adaptation_level = getattr(self_state, "adaptation_level", 0.0)
            data["adaptation_level"] = (
                float(adaptation_level) if isinstance(adaptation_level, (int, float)) else 0.0
            )
            # Валидация диапазона
            data["adaptation_level"] = max(0.0, min(1.0, data["adaptation_level"]))
        except (ValueError, TypeError):
            data["adaptation_level"] = 0.0

        # Статистика поведения с валидацией
        if hasattr(self_state, "behavior_stats") and isinstance(self_state.behavior_stats, dict):
            data["behavior_stats"] = self_state.behavior_stats.copy()
        else:
            data["behavior_stats"] = {}

        return data

    def _collect_performance_metrics(
        self,
        self_state: Any,
        memory: Any,
        learning_engine: Any,
        adaptation_manager: Any,
        decision_engine: Any,
    ) -> Dict[str, Any]:
        """Собрать метрики производительности."""
        metrics = {}

        try:
            # Метрики памяти с валидацией
            if hasattr(memory, "get_statistics") and callable(getattr(memory, "get_statistics")):
                mem_stats = memory.get_statistics()
                if isinstance(mem_stats, dict):
                    metrics["memory_usage"] = int(mem_stats.get("total_entries", 0))
                    metrics["memory_efficiency"] = float(mem_stats.get("efficiency", 0.0))
                    # Валидация диапазона
                    metrics["memory_efficiency"] = max(0.0, min(1.0, metrics["memory_efficiency"]))
                else:
                    metrics["memory_usage"] = 0
                    metrics["memory_efficiency"] = 0.0
            else:
                metrics["memory_usage"] = 0
                metrics["memory_efficiency"] = 0.0
        except Exception as e:
            logger.debug(f"Memory metrics collection failed: {e}")
            metrics["memory_usage"] = 0
            metrics["memory_efficiency"] = 0.0

        try:
            # Метрики обучения с валидацией
            if hasattr(learning_engine, "get_parameters") and callable(
                getattr(learning_engine, "get_parameters")
            ):
                learn_params = learning_engine.get_parameters()
                if isinstance(learn_params, dict):
                    metrics["learning_rate"] = float(learn_params.get("learning_rate", 0.0))
                    metrics["learning_progress"] = float(learn_params.get("progress", 0.0))
                    # Валидация диапазонов
                    metrics["learning_rate"] = max(0.0, min(1.0, metrics["learning_rate"]))
                    metrics["learning_progress"] = max(0.0, min(1.0, metrics["learning_progress"]))
                else:
                    metrics["learning_rate"] = 0.0
                    metrics["learning_progress"] = 0.0
            else:
                metrics["learning_rate"] = 0.0
                metrics["learning_progress"] = 0.0
        except Exception as e:
            logger.debug(f"Learning metrics collection failed: {e}")
            metrics["learning_rate"] = 0.0
            metrics["learning_progress"] = 0.0

        try:
            # Метрики адаптации с валидацией
            if hasattr(adaptation_manager, "get_parameters") and callable(
                getattr(adaptation_manager, "get_parameters")
            ):
                adapt_params = adaptation_manager.get_parameters()
                if isinstance(adapt_params, dict):
                    metrics["adaptation_rate"] = float(adapt_params.get("adaptation_rate", 0.0))
                    metrics["adaptation_stability"] = float(adapt_params.get("stability", 0.0))
                    # Валидация диапазонов
                    metrics["adaptation_rate"] = max(0.0, min(1.0, metrics["adaptation_rate"]))
                    metrics["adaptation_stability"] = max(
                        0.0, min(1.0, metrics["adaptation_stability"])
                    )
                else:
                    metrics["adaptation_rate"] = 0.0
                    metrics["adaptation_stability"] = 0.0
            else:
                metrics["adaptation_rate"] = 0.0
                metrics["adaptation_stability"] = 0.0
        except Exception as e:
            logger.debug(f"Adaptation metrics collection failed: {e}")
            metrics["adaptation_rate"] = 0.0
            metrics["adaptation_stability"] = 0.0

        try:
            # Метрики принятия решений с валидацией
            if hasattr(decision_engine, "get_statistics") and callable(
                getattr(decision_engine, "get_statistics")
            ):
                decision_stats = decision_engine.get_statistics()
                if isinstance(decision_stats, dict):
                    metrics["decision_speed"] = float(decision_stats.get("average_time", 0.0))
                    metrics["decision_accuracy"] = float(decision_stats.get("accuracy", 0.0))
                    # Валидация диапазонов
                    metrics["decision_accuracy"] = max(0.0, min(1.0, metrics["decision_accuracy"]))
                else:
                    metrics["decision_speed"] = 0.0
                    metrics["decision_accuracy"] = 0.0
            else:
                metrics["decision_speed"] = 0.0
                metrics["decision_accuracy"] = 0.0
        except Exception as e:
            logger.debug(f"Decision metrics collection failed: {e}")
            metrics["decision_speed"] = 0.0
            metrics["decision_accuracy"] = 0.0

        return metrics

    def analyze_snapshot(self, snapshot: TechnicalSnapshot) -> TechnicalReport:
        """
        Проанализировать снимок состояния системы.

        Args:
            snapshot: Снимок состояния для анализа

        Returns:
            TechnicalReport: Отчет с техническим анализом
        """
        report = TechnicalReport(snapshot=snapshot)

        # Анализ производительности
        report.performance = self._analyze_performance(snapshot)

        # Анализ стабильности
        report.stability = self._analyze_stability(snapshot)

        # Анализ адаптивности
        report.adaptability = self._analyze_adaptability(snapshot)

        # Анализ целостности
        report.integrity = self._analyze_integrity(snapshot)

        # Общая оценка
        report.overall_assessment = self._calculate_overall_assessment(report)

        # Сохранить в истории
        self._add_to_history(report)

        return report

    def _analyze_performance(self, snapshot: TechnicalSnapshot) -> Dict[str, Any]:
        """Анализ производительности системы."""
        perf_metrics = snapshot.performance_metrics

        analysis = {
            "memory_efficiency": perf_metrics.get("memory_efficiency", 0.0),
            "learning_progress": perf_metrics.get("learning_progress", 0.0),
            "decision_speed": perf_metrics.get("decision_speed", 0.0),
            "decision_accuracy": perf_metrics.get("decision_accuracy", 0.0),
            "overall_performance": 0.0,
        }

        # Расчет общей производительности
        weights = {
            "memory_efficiency": 0.25,
            "learning_progress": 0.25,
            "decision_speed": 0.25,
            "decision_accuracy": 0.25,
        }

        analysis["overall_performance"] = sum(
            analysis[metric] * weight for metric, weight in weights.items()
        )

        return analysis

    def _analyze_stability(self, snapshot: TechnicalSnapshot) -> Dict[str, Any]:
        """Анализ стабильности системы."""
        analysis = {
            "state_consistency": 0.0,
            "behavior_predictability": 0.0,
            "parameter_stability": 0.0,
            "overall_stability": 0.0,
        }

        # Анализ стабильности состояния
        self_state = snapshot.self_state
        if "energy_level" in self_state and "adaptation_level" in self_state:
            energy = self_state["energy_level"]
            adaptation = self_state["adaptation_level"]
            # Стабильность как среднее между энергией и адаптацией
            analysis["state_consistency"] = (energy + adaptation) / 2.0
        else:
            analysis["state_consistency"] = 0.5  # Значение по умолчанию

        # Анализ предсказуемости поведения
        decision_history = snapshot.decision_history
        if len(decision_history) > 10:
            # Простая метрика: стабильность типов решений
            decision_types = [d.get("type", "unknown") for d in decision_history[-20:]]
            unique_types = len(set(decision_types))
            analysis["behavior_predictability"] = max(0.0, 1.0 - (unique_types / 10.0))
        else:
            analysis["behavior_predictability"] = 0.5

        # Анализ стабильности параметров
        adapt_params = snapshot.adaptation_params
        if "adaptation_stability" in adapt_params:
            analysis["parameter_stability"] = adapt_params["adaptation_stability"]
        else:
            analysis["parameter_stability"] = 0.5

        # Общая стабильность
        analysis["overall_stability"] = (
            analysis["state_consistency"] * 0.4
            + analysis["behavior_predictability"] * 0.3
            + analysis["parameter_stability"] * 0.3
        )

        return analysis

    def _analyze_adaptability(self, snapshot: TechnicalSnapshot) -> Dict[str, Any]:
        """Анализ адаптивности системы."""
        analysis = {
            "learning_rate": 0.0,
            "adaptation_rate": 0.0,
            "change_responsiveness": 0.0,
            "overall_adaptability": 0.0,
        }

        # Скорость обучения
        perf_metrics = snapshot.performance_metrics
        analysis["learning_rate"] = perf_metrics.get("learning_rate", 0.0)

        # Скорость адаптации
        analysis["adaptation_rate"] = perf_metrics.get("adaptation_rate", 0.0)

        # Отклик на изменения (на основе истории решений)
        decision_history = snapshot.decision_history
        if len(decision_history) > 5:
            recent_decisions = decision_history[-10:]
            change_count = sum(1 for d in recent_decisions if d.get("type") == "adaptation")
            analysis["change_responsiveness"] = min(1.0, change_count / 5.0)
        else:
            analysis["change_responsiveness"] = 0.0

        # Общая адаптивность
        analysis["overall_adaptability"] = (
            analysis["learning_rate"] * 0.4
            + analysis["adaptation_rate"] * 0.4
            + analysis["change_responsiveness"] * 0.2
        )

        return analysis

    def _analyze_integrity(self, snapshot: TechnicalSnapshot) -> Dict[str, Any]:
        """Анализ целостности системы."""
        analysis = {
            "data_consistency": 0.0,
            "structural_integrity": 0.0,
            "logical_coherence": 0.0,
            "overall_integrity": 0.0,
        }

        # Проверка согласованности данных
        data_errors = 0
        total_checks = 0

        # Проверка self_state
        self_state = snapshot.self_state
        total_checks += 1
        if isinstance(self_state, dict) and "error" not in self_state:
            analysis["data_consistency"] += 0.25
        else:
            data_errors += 1

        # Проверка memory_stats
        memory_stats = snapshot.memory_stats
        total_checks += 1
        if isinstance(memory_stats, dict) and "error" not in memory_stats:
            analysis["data_consistency"] += 0.25
        else:
            data_errors += 1

        # Проверка learning_params
        learning_params = snapshot.learning_params
        total_checks += 1
        if isinstance(learning_params, dict) and "error" not in learning_params:
            analysis["data_consistency"] += 0.25
        else:
            data_errors += 1

        # Проверка adaptation_params
        adaptation_params = snapshot.adaptation_params
        total_checks += 1
        if isinstance(adaptation_params, dict) and "error" not in adaptation_params:
            analysis["data_consistency"] += 0.25
        else:
            data_errors += 1

        analysis["data_consistency"] = max(0.0, 1.0 - (data_errors / total_checks))

        # Структурная целостность (наличие всех компонентов)
        components_present = sum(
            [
                1 if "error" not in snapshot.self_state else 0,
                1 if "error" not in snapshot.memory_stats else 0,
                1 if "error" not in snapshot.learning_params else 0,
                1 if "error" not in snapshot.adaptation_params else 0,
                1 if len(snapshot.decision_history) > 0 else 0,
            ]
        )
        analysis["structural_integrity"] = components_present / 5.0

        # Логическая согласованность (проверка внутренних противоречий)
        analysis["logical_coherence"] = self._check_logical_coherence(snapshot)

        # Общая целостность
        analysis["overall_integrity"] = (
            analysis["data_consistency"] * 0.4
            + analysis["structural_integrity"] * 0.3
            + analysis["logical_coherence"] * 0.3
        )

        return analysis

    def _check_logical_coherence(self, snapshot: TechnicalSnapshot) -> float:
        """Проверка логической согласованности данных."""
        coherence_score = 1.0
        issues = 0

        # Проверка energy_level в допустимых пределах
        energy = snapshot.self_state.get("energy_level", 0.0)
        if not (0.0 <= energy <= 1.0):
            issues += 1

        # Проверка adaptation_level в допустимых пределах
        adaptation = snapshot.self_state.get("adaptation_level", 0.0)
        if not (0.0 <= adaptation <= 1.0):
            issues += 1

        # Проверка, что cycle_count увеличивается
        if len(self.report_history) > 0:
            prev_cycle = self.report_history[-1].snapshot.self_state.get("cycle_count", 0)
            curr_cycle = snapshot.self_state.get("cycle_count", 0)
            if curr_cycle < prev_cycle:
                issues += 1

        # Проверка согласованности истории решений
        decision_history = snapshot.decision_history
        if len(decision_history) > 0:
            # Проверить, что все решения имеют базовую структуру
            valid_decisions = sum(
                1 for d in decision_history if isinstance(d, dict) and "timestamp" in d
            )
            if valid_decisions < len(decision_history) * 0.8:  # Менее 80% валидных решений
                issues += 1

        return max(0.0, 1.0 - (issues * 0.2))

    def _calculate_overall_assessment(self, report: TechnicalReport) -> Dict[str, Any]:
        """Расчет общей оценки системы."""
        assessment = {
            "performance_score": report.performance.get("overall_performance", 0.0),
            "stability_score": report.stability.get("overall_stability", 0.0),
            "adaptability_score": report.adaptability.get("overall_adaptability", 0.0),
            "integrity_score": report.integrity.get("overall_integrity", 0.0),
            "overall_score": 0.0,
            "status": "unknown",
        }

        # Общий балл
        weights = {
            "performance_score": 0.25,
            "stability_score": 0.25,
            "adaptability_score": 0.25,
            "integrity_score": 0.25,
        }

        assessment["overall_score"] = sum(
            assessment[metric] * weight for metric, weight in weights.items()
        )

        # Определение статуса
        score = assessment["overall_score"]
        if score >= 0.8:
            assessment["status"] = "excellent"
        elif score >= 0.6:
            assessment["status"] = "good"
        elif score >= 0.4:
            assessment["status"] = "adequate"
        elif score >= 0.2:
            assessment["status"] = "concerning"
        else:
            assessment["status"] = "critical"

        return assessment

    def _add_to_history(self, report: TechnicalReport):
        """Добавить отчет в историю."""
        self.report_history.append(report)
        if len(self.report_history) > self.max_history_size:
            self.report_history.pop(0)

    def get_trends(self, hours: int = 24) -> Dict[str, Any]:
        """
        Получить тренды за указанный период времени.

        Args:
            hours: Период в часах для анализа трендов

        Returns:
            Dict с трендами по основным метрикам
        """
        cutoff_time = time.time() - (hours * 3600)
        recent_reports = [r for r in self.report_history if r.timestamp >= cutoff_time]

        if len(recent_reports) < 2:
            return {"error": "Недостаточно данных для анализа трендов"}

        trends = {
            "performance_trend": self._calculate_trend(
                [r.performance.get("overall_performance", 0.0) for r in recent_reports]
            ),
            "stability_trend": self._calculate_trend(
                [r.stability.get("overall_stability", 0.0) for r in recent_reports]
            ),
            "adaptability_trend": self._calculate_trend(
                [r.adaptability.get("overall_adaptability", 0.0) for r in recent_reports]
            ),
            "integrity_trend": self._calculate_trend(
                [r.integrity.get("overall_integrity", 0.0) for r in recent_reports]
            ),
            "overall_trend": self._calculate_trend(
                [r.overall_assessment.get("overall_score", 0.0) for r in recent_reports]
            ),
        }

        return trends

    def _calculate_trend(self, values: List[float]) -> Dict[str, Any]:
        """Рассчитать тренд для последовательности значений."""
        if len(values) < 2:
            return {"direction": "stable", "magnitude": 0.0}

        # Линейная регрессия для определения тренда
        n = len(values)
        x = list(range(n))
        y = values

        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_xx = sum(xi * xi for xi in x)

        slope = (
            (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)
            if (n * sum_xx - sum_x * sum_x) != 0
            else 0
        )

        # Нормализация наклона
        magnitude = abs(slope) / max(abs(max(values) - min(values)), 0.01)

        if slope > 0.01:
            direction = "improving"
        elif slope < -0.01:
            direction = "declining"
        else:
            direction = "stable"

        return {"direction": direction, "magnitude": min(magnitude, 1.0), "slope": slope}

    def save_report(self, report: TechnicalReport, filepath: str, async_save: bool = True):
        """
        Сохранить отчет в файл.

        Args:
            report: Отчет для сохранения
            filepath: Путь к файлу
            async_save: Использовать асинхронное сохранение через DataCollectionManager
        """
        data = {
            "timestamp": report.timestamp,
            "performance": report.performance,
            "stability": report.stability,
            "adaptability": report.adaptability,
            "integrity": report.integrity,
            "overall_assessment": report.overall_assessment,
        }

        # Если есть DataCollectionManager и запрошено асинхронное сохранение
        if async_save and self.data_collection_manager:
            success = self.data_collection_manager.save_technical_report(
                report_data=data,
                base_dir=str(Path(filepath).parent),
                filename_prefix=Path(filepath).stem
            )
            if success:
                logger.debug(f"Technical report queued for async save: {filepath}")
            else:
                logger.warning(f"Failed to queue technical report for async save: {filepath}")
                # Fallback to synchronous save
                self._save_report_sync(data, filepath)
        else:
            # Синхронное сохранение
            self._save_report_sync(data, filepath)

    def _save_report_sync(self, data: Dict[str, Any], filepath: str) -> None:
        """
        Синхронное сохранение отчета (fallback метод).

        Args:
            data: Данные отчета
            filepath: Путь к файлу
        """
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Report saved synchronously to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save report synchronously: {e}")

    def load_report(self, filepath: str) -> Optional[TechnicalReport]:
        """
        Загрузить отчет из файла.

        Args:
            filepath: Путь к файлу

        Returns:
            TechnicalReport или None при ошибке
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            report = TechnicalReport()
            report.timestamp = data.get("timestamp", time.time())
            report.performance = data.get("performance", {})
            report.stability = data.get("stability", {})
            report.adaptability = data.get("adaptability", {})
            report.integrity = data.get("integrity", {})
            report.overall_assessment = data.get("overall_assessment", {})

            return report
        except Exception as e:
            logger.error(f"Failed to load report: {e}")
            return None
