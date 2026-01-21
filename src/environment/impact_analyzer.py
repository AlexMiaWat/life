"""
Анализатор воздействий на систему Life.

Предоставляет возможность предсказания влияния событий на состояние системы
без фактического применения изменений.
"""

import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from copy import deepcopy

from src.environment.event import Event
from src.state.self_state import SelfState
from src.meaning.engine import MeaningEngine
from src.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ImpactPrediction:
    """Предсказание влияния события"""

    event: Event
    meaning_significance: float
    meaning_impact: Dict[str, float]  # Изменения energy, stability, integrity
    final_energy: float
    final_stability: float
    final_integrity: float
    response_pattern: str  # ignore, absorb, dampen, amplify
    confidence: float  # Уверенность предсказания [0, 1]


@dataclass
class BatchImpactAnalysis:
    """Анализ пакета событий"""

    events: List[Event]
    predictions: List[ImpactPrediction]
    cumulative_impact: Dict[str, float]
    final_state: Dict[str, float]
    risk_assessment: str  # low, medium, high, critical


class ImpactAnalyzer:
    """Анализатор воздействий"""

    def __init__(self):
        self.meaning_engine = MeaningEngine()
        # Кэш для оптимизации повторных анализов
        self._analysis_cache: Dict[str, Tuple[ImpactPrediction, float]] = {}
        self._cache_ttl = 30.0  # 30 секунд TTL для кэша

    def analyze_single_event(self, event: Event, self_state: SelfState) -> ImpactPrediction:
        """
        Проанализировать влияние одиночного события

        Args:
            event: Событие для анализа
            self_state: Текущее состояние системы

        Returns:
            ImpactPrediction: Предсказание влияния события
        """
        # Создаем ключ кэша
        cache_key = f"{event.type}_{event.intensity:.3f}_{self_state.energy:.1f}_{self_state.stability:.3f}_{self_state.integrity:.3f}"

        # Проверяем кэш
        current_time = time.time()
        if cache_key in self._analysis_cache:
            cached_prediction, cache_time = self._analysis_cache[cache_key]
            if current_time - cache_time < self._cache_ttl:
                return cached_prediction

        try:
            # Получаем интерпретацию события через MeaningEngine
            meaning = self.meaning_engine.process(event, self_state)

            # Предсказываем финальные значения состояния
            final_energy = max(
                0.0, min(100.0, self_state.energy + meaning.impact.get("energy", 0.0))
            )
            final_stability = max(
                0.0, min(1.0, self_state.stability + meaning.impact.get("stability", 0.0))
            )
            final_integrity = max(
                0.0, min(1.0, self_state.integrity + meaning.impact.get("integrity", 0.0))
            )

            # Определяем паттерн реакции
            response_pattern = self._determine_response_pattern(meaning, self_state)

            # Рассчитываем уверенность предсказания
            confidence = self._calculate_confidence(meaning, self_state)

            prediction = ImpactPrediction(
                event=event,
                meaning_significance=meaning.significance,
                meaning_impact=meaning.impact,
                final_energy=final_energy,
                final_stability=final_stability,
                final_integrity=final_integrity,
                response_pattern=response_pattern,
                confidence=confidence,
            )

            # Кэшируем результат
            self._analysis_cache[cache_key] = (prediction, current_time)

            return prediction

        except Exception as e:
            logger.error(f"Error analyzing event impact: {e}")
            # Возвращаем безопасное предсказание при ошибке
            return ImpactPrediction(
                event=event,
                meaning_significance=0.0,
                meaning_impact={},
                final_energy=self_state.energy,
                final_stability=self_state.stability,
                final_integrity=self_state.integrity,
                response_pattern="ignore",
                confidence=0.0,
            )

    def analyze_batch_events(
        self, events: List[Event], self_state: SelfState
    ) -> BatchImpactAnalysis:
        """
        Проанализировать влияние пакета событий

        Args:
            events: Список событий для анализа
            self_state: Исходное состояние системы

        Returns:
            BatchImpactAnalysis: Анализ пакета событий
        """
        predictions = []
        cumulative_impact = {"energy": 0.0, "stability": 0.0, "integrity": 0.0}

        # Создаем копию состояния для симуляции
        simulated_state = deepcopy(self_state)

        for event in events:
            prediction = self.analyze_single_event(event, simulated_state)
            predictions.append(prediction)

            # Накопительный эффект
            cumulative_impact["energy"] += prediction.meaning_impact.get("energy", 0.0)
            cumulative_impact["stability"] += prediction.meaning_impact.get("stability", 0.0)
            cumulative_impact["integrity"] += prediction.meaning_impact.get("integrity", 0.0)

            # Обновляем симулированное состояние
            simulated_state.energy = prediction.final_energy
            simulated_state.stability = prediction.final_stability
            simulated_state.integrity = prediction.final_integrity

        # Финальное состояние после всех событий
        final_state = {
            "energy": simulated_state.energy,
            "stability": simulated_state.stability,
            "integrity": simulated_state.integrity,
        }

        # Оценка рисков
        risk_assessment = self._assess_risk(cumulative_impact, final_state)

        # Рекомендации удалены согласно ADR 001 - пассивное наблюдение

        return BatchImpactAnalysis(
            events=events,
            predictions=predictions,
            cumulative_impact=cumulative_impact,
            final_state=final_state,
            risk_assessment=risk_assessment,
        )

    def _determine_response_pattern(self, meaning, self_state: SelfState) -> str:
        """Определить паттерн реакции на основе meaning и состояния"""
        significance = meaning.significance
        stability = self_state.stability

        if significance < 0.1:
            return "ignore"
        elif significance > 0.7 or stability < 0.3:
            return "amplify"
        elif stability > 0.8:
            return "dampen"
        else:
            return "absorb"

    def _calculate_confidence(self, meaning, self_state: SelfState) -> float:
        """Рассчитать уверенность предсказания"""
        # Базовая уверенность на основе значимости
        base_confidence = min(meaning.significance * 2.0, 1.0)

        # Корректировка на основе стабильности состояния
        stability_factor = 1.0 if self_state.stability > 0.5 else 0.7

        # Корректировка на основе энергии
        energy_factor = 1.0 if self_state.energy > 20.0 else 0.8

        return min(base_confidence * stability_factor * energy_factor, 1.0)

    def _assess_risk(
        self, cumulative_impact: Dict[str, float], final_state: Dict[str, float]
    ) -> str:
        """Оценить уровень риска воздействия"""
        # Критические пороги
        energy_drop = cumulative_impact.get("energy", 0.0)
        stability_drop = cumulative_impact.get("stability", 0.0)
        integrity_drop = cumulative_impact.get("integrity", 0.0)

        final_energy = final_state.get("energy", 100.0)
        final_stability = final_state.get("stability", 1.0)
        final_integrity = final_state.get("integrity", 1.0)

        # Критический риск
        if (
            final_energy < 5.0
            or final_integrity < 0.1
            or energy_drop < -50.0
            or integrity_drop < -0.5
        ):
            return "critical"

        # Высокий риск
        if (
            final_energy < 20.0
            or final_stability < 0.2
            or final_integrity < 0.3
            or energy_drop < -30.0
            or stability_drop < -0.4
        ):
            return "high"

        # Средний риск
        if (
            final_energy < 40.0
            or final_stability < 0.4
            or energy_drop < -20.0
            or stability_drop < -0.2
        ):
            return "medium"

        return "low"


    def get_sensitivity_analysis(self, self_state: SelfState) -> Dict[str, Any]:
        """
        Провести анализ чувствительности к различным типам событий

        Args:
            self_state: Текущее состояние системы

        Returns:
            Dict с анализом чувствительности по типам событий
        """
        event_types = [
            "noise",
            "decay",
            "recovery",
            "shock",
            "idle",
            "social_presence",
            "social_conflict",
            "social_harmony",
            "cognitive_doubt",
            "cognitive_clarity",
            "cognitive_confusion",
            "existential_void",
            "existential_purpose",
            "existential_finitude",
            "connection",
            "isolation",
            "insight",
            "confusion",
            "curiosity",
            "meaning_found",
            "void",
            "acceptance",
        ]

        sensitivity = {}

        for event_type in event_types:
            # Создаем тестовое событие средней интенсивности
            test_event = Event(type=event_type, intensity=0.5, timestamp=time.time())
            prediction = self.analyze_single_event(test_event, self_state)

            sensitivity[event_type] = {
                "predicted_significance": prediction.meaning_significance,
                "energy_impact": prediction.meaning_impact.get("energy", 0.0),
                "stability_impact": prediction.meaning_impact.get("stability", 0.0),
                "integrity_impact": prediction.meaning_impact.get("integrity", 0.0),
                "response_pattern": prediction.response_pattern,
                "confidence": prediction.confidence,
            }

        # Сортировка по степени влияния
        sorted_types = sorted(
            sensitivity.items(),
            key=lambda x: abs(x[1]["energy_impact"])
            + abs(x[1]["stability_impact"])
            + abs(x[1]["integrity_impact"]),
            reverse=True,
        )

        return {
            "current_state": {
                "energy": self_state.energy,
                "stability": self_state.stability,
                "integrity": self_state.integrity,
            },
            "sensitivity_by_type": dict(sorted_types),
            "most_sensitive_types": [t[0] for t in sorted_types[:5]],
            "least_sensitive_types": [t[0] for t in sorted_types[-5:]],
        }
