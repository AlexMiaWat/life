"""
Pattern Analyzer - независимый компонент для анализа паттернов событий.

Отвечает за:
- Анализ повторяющихся паттернов в событиях
- Вычисление модификаторов на основе паттернов
- Обнаружение аномалий в последовательностях

Архитектурный контракт:
- Вход: event_type (str), recent_events (List[str])
- Выход: модификатор паттерна (float) в диапазоне [0.5, 2.0]
- Гарантии: детерминированный анализ, thread-safe
"""

from typing import List, Dict
from dataclasses import dataclass
from collections import Counter


@dataclass
class PatternContract:
    """Контракт для анализа паттернов событий."""

    # Диапазоны входных значений
    input_ranges = {
        'recent_events_count': (0, 100),  # Максимум 100 последних событий
        'analysis_window': (5, 50),       # Окно анализа 5-50 событий
    }

    # Гарантии выходных значений
    output_guarantees = {
        'pattern_modifier': (0.5, 2.0),  # Диапазон модификатора
        'confidence': (0.0, 1.0),        # Уверенность в анализе
    }


class PatternAnalyzer:
    """
    Анализатор паттернов событий.

    Обнаруживает:
    - Повторяющиеся последовательности
    - Циклические паттерны
    - Аномалии в частотах
    - Тренды изменения интенсивности
    """

    def __init__(self):
        self.contract = PatternContract()
        self.frequency_analyzer = FrequencyAnalyzer()
        self.sequence_analyzer = SequenceAnalyzer()
        self.trend_analyzer = TrendAnalyzer()

    def analyze(self, event_type: str, recent_events: List[str]) -> Dict[str, float]:
        """
        Полный анализ паттернов для типа события.

        Args:
            event_type: Тип анализируемого события
            recent_events: Список последних событий

        Returns:
            Словарь с результатами анализа:
            - pattern_modifier: модификатор интенсивности
            - confidence: уверенность анализа
            - frequency_factor: фактор частоты
            - sequence_factor: фактор последовательности
        """
        if not recent_events:
            return {
                'pattern_modifier': 1.0,
                'confidence': 0.0,
                'frequency_factor': 1.0,
                'sequence_factor': 1.0
            }

        # Валидация входных данных
        self._validate_inputs(recent_events)

        try:
            # Анализ частоты
            frequency_result = self.frequency_analyzer.analyze(event_type, recent_events)

            # Анализ последовательностей
            sequence_result = self.sequence_analyzer.analyze(event_type, recent_events)

            # Комбинированный модификатор
            pattern_modifier = (
                frequency_result['modifier'] * 0.6 +
                sequence_result['modifier'] * 0.4
            )

            # Ограничиваем диапазон
            min_mod, max_mod = self.contract.output_guarantees['pattern_modifier']
            pattern_modifier = max(min_mod, min(max_mod, pattern_modifier))

            # Общая уверенность
            confidence = (frequency_result['confidence'] + sequence_result['confidence']) / 2.0

            return {
                'pattern_modifier': round(pattern_modifier, 3),
                'confidence': round(confidence, 3),
                'frequency_factor': round(frequency_result['modifier'], 3),
                'sequence_factor': round(sequence_result['modifier'], 3)
            }

        except Exception as e:
            print(f"Pattern analysis error for {event_type}: {e}")
            return {
                'pattern_modifier': 1.0,
                'confidence': 0.0,
                'frequency_factor': 1.0,
                'sequence_factor': 1.0
            }

    def _validate_inputs(self, recent_events: List[str]):
        """Валидация входных данных."""
        if len(recent_events) > self.contract.input_ranges['recent_events_count'][1]:
            raise ValueError(f"Too many recent events: {len(recent_events)}")


class FrequencyAnalyzer:
    """Анализатор частоты событий."""

    def analyze(self, event_type: str, recent_events: List[str]) -> Dict[str, float]:
        """
        Анализ частоты события в последних событиях.

        Args:
            event_type: Тип события
            recent_events: Список последних событий

        Returns:
            Результат анализа частоты
        """
        if not recent_events:
            return {'modifier': 1.0, 'confidence': 0.0}

        # Подсчет частоты
        total_events = len(recent_events)
        event_count = recent_events.count(event_type)
        frequency = event_count / total_events

        # Базовая частота для сравнения (ожидаемая)
        expected_frequency = 1.0 / len(set(recent_events)) if recent_events else 0.1

        # Модификатор: редкие события усиливаются, частые - ослабляются
        if frequency < expected_frequency:
            modifier = 1.0 + (expected_frequency - frequency) * 2.0  # Усиление редких
        else:
            modifier = 1.0 - (frequency - expected_frequency) * 1.5  # Ослабление частых

        # Уверенность растет с количеством событий
        confidence = min(1.0, total_events / 20.0)

        return {
            'modifier': modifier,
            'confidence': confidence
        }


class SequenceAnalyzer:
    """Анализатор последовательностей событий."""

    def analyze(self, event_type: str, recent_events: List[str]) -> Dict[str, float]:
        """
        Анализ последовательностей событий.

        Args:
            event_type: Тип события
            recent_events: Список последних событий

        Returns:
            Результат анализа последовательности
        """
        if len(recent_events) < 3:
            return {'modifier': 1.0, 'confidence': 0.0}

        # Ищем повторяющиеся паттерны
        pattern_score = 0.0
        window_size = min(5, len(recent_events))

        for i in range(len(recent_events) - window_size + 1):
            window = recent_events[i:i + window_size]
            if event_type in window:
                # Проверяем, является ли это повторяющимся паттерном
                pattern_repeats = 0
                for j in range(i + window_size, len(recent_events) - window_size + 1, window_size):
                    next_window = recent_events[j:j + window_size]
                    if next_window == window:
                        pattern_repeats += 1

                if pattern_repeats > 0:
                    pattern_score += 0.2 * pattern_repeats

        # Модификатор на основе паттернов
        modifier = 1.0 + pattern_score

        # Уверенность
        confidence = min(1.0, len(recent_events) / 30.0)

        return {
            'modifier': modifier,
            'confidence': confidence
        }


class TrendAnalyzer:
    """Анализатор трендов (резерв для будущих расширений)."""

    def analyze(self, event_type: str, recent_events: List[str]) -> Dict[str, float]:
        """Анализ трендов (пока заглушка)."""
        return {'modifier': 1.0, 'confidence': 0.0}