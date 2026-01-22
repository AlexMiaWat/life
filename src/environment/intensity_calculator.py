"""
Intensity Calculator - независимый компонент для расчета интенсивностей событий.

Отвечает за адаптацию базовой интенсивности события на основе:
- состояния системы Life
- паттернов событий
- циркадного ритма
- субъективного времени
- категорийных правил

Архитектурный контракт:
- Вход: event_type (str), base_intensity (float), context (Context)
- Выход: адаптированная интенсивность (float) в диапазоне [0.1, 3.0]
- Гарантии: детерминированный расчет, thread-safe, обработка ошибок
"""

from typing import Dict, Optional, Protocol
from dataclasses import dataclass
from ..state.self_state import SelfState


class Context(Protocol):
    """Протокол контекста для расчета интенсивности."""
    energy: float
    stability: float
    integrity: float
    recent_events: list[str]
    subjective_time_intensity_coeff: float
    subjective_time_stability_coeff: float
    subjective_time_energy_coeff: float
    circadian_phase: float
    recovery_efficiency: float


@dataclass
class IntensityContract:
    """Контракт для расчета интенсивности событий."""

    # Диапазоны входных значений
    input_ranges = {
        'base_intensity': (0.0, 1.0),
        'energy': (0.0, 100.0),
        'stability': (0.0, 2.0),
        'integrity': (0.0, 1.0)
    }

    # Гарантии выходных значений
    output_guarantees = {
        'intensity': (0.1, 3.0),  # Минимум 0.1, максимум 3.0
        'precision': 0.001        # Точность расчета
    }

    # Обработка ошибок
    error_handling = {
        'invalid_input': 'clamp_to_range',
        'calculation_error': 'fallback_to_base_intensity'
    }


class IntensityCalculator:
    """
    Независимый калькулятор интенсивностей событий.

    Композиция из специализированных компонентов:
    - StateBasedModifier: модификация на основе состояния Life
    - PatternModifier: модификация на основе паттернов
    - TimeBasedModifier: модификация на основе времени
    - CategoryModifier: категориальные правила
    """

    def __init__(self):
        self.contract = IntensityContract()
        self.state_modifier = StateBasedModifier()
        self.pattern_modifier = PatternModifier()
        self.time_modifier = TimeBasedModifier()
        self.category_modifier = CategoryModifier()

    def calculate(self, event_type: str, base_intensity: float, context: Optional[Context] = None) -> float:
        """
        Рассчитать адаптированную интенсивность события.

        Args:
            event_type: Тип события
            base_intensity: Базовая интенсивность [0.0, 1.0]
            context: Контекст состояния Life

        Returns:
            Адаптированная интенсивность [0.1, 3.0]

        Raises:
            ValueError: при нарушении контракта входных данных
        """
        # Валидация входных данных
        self._validate_inputs(event_type, base_intensity, context)

        try:
            # Применяем все модификаторы последовательно
            modifier = 1.0

            modifier *= self.state_modifier.calculate(event_type, context)
            modifier *= self.pattern_modifier.calculate(event_type, context)
            modifier *= self.time_modifier.calculate(event_type, context)
            modifier *= self.category_modifier.calculate(event_type, context)

            # Применяем модификатор к базовой интенсивности
            adapted_intensity = base_intensity * modifier

            # Ограничиваем диапазон согласно контракту
            min_intensity, max_intensity = self.contract.output_guarantees['intensity']
            adapted_intensity = max(min_intensity, min(max_intensity, adapted_intensity))

            return round(adapted_intensity, 3)  # Гарантируем точность

        except Exception as e:
            # Fallback согласно контракту
            print(f"Intensity calculation error for {event_type}: {e}")
            return max(self.contract.output_guarantees['intensity'][0], base_intensity)

    def _validate_inputs(self, event_type: str, base_intensity: float, context: Optional[Context]):
        """Валидация входных данных согласно контракту."""
        if not isinstance(event_type, str) or not event_type:
            raise ValueError(f"Invalid event_type: {event_type}")

        min_base, max_base = self.contract.input_ranges['base_intensity']
        if not (min_base <= base_intensity <= max_base):
            if self.contract.error_handling['invalid_input'] == 'clamp_to_range':
                base_intensity = max(min_base, min(max_base, base_intensity))
            else:
                raise ValueError(f"base_intensity {base_intensity} out of range [{min_base}, {max_base}]")

        if context:
            # Валидация контекста если предоставлен
            energy_min, energy_max = self.contract.input_ranges['energy']
            if not (energy_min <= context.energy <= energy_max):
                raise ValueError(f"context.energy {context.energy} out of range [{energy_min}, {energy_max}]")


class StateBasedModifier:
    """Модификатор интенсивности на основе состояния Life."""

    def calculate(self, event_type: str, context: Optional[Context]) -> float:
        if not context:
            return 1.0

        rules = self._get_state_rules()
        modifier = 1.0

        # Применяем правила для энергии
        energy_rule = rules.get((event_type, "energy"))
        if energy_rule:
            modifier *= energy_rule(context.energy / 100.0)  # Нормализуем к [0,1]

        # Применяем правила для стабильности
        stability_rule = rules.get((event_type, "stability"))
        if stability_rule:
            modifier *= stability_rule(context.stability)

        return modifier

    def _get_state_rules(self) -> Dict[tuple, callable]:
        """Получить правила модификации на основе состояния."""
        return {
            # Энергия: положительные события усиливаются при низкой энергии
            ("recovery", "energy"): lambda e: 0.8 + (1.0 - e) * 0.5,
            ("comfort", "energy"): lambda e: 0.8 + (1.0 - e) * 0.5,
            ("joy", "energy"): lambda e: 0.8 + (1.0 - e) * 0.5,
            ("calm", "energy"): lambda e: 0.8 + (1.0 - e) * 0.5,

            # Энергия: негативные события усиливаются при низкой энергии
            ("decay", "energy"): lambda e: 0.9 + (1.0 - e) * 0.4,
            ("fatigue", "energy"): lambda e: 0.9 + (1.0 - e) * 0.4,
            ("discomfort", "energy"): lambda e: 0.9 + (1.0 - e) * 0.4,

            # Энергия: креативные события усиливаются при высокой энергии
            ("inspiration", "energy"): lambda e: 1.0 + max(0, (e - 0.6)) * 0.5,
            ("curiosity", "energy"): lambda e: 1.0 + max(0, (e - 0.6)) * 0.5,
            ("insight", "energy"): lambda e: 1.0 + max(0, (e - 0.6)) * 0.5,

            # Стабильность: хаотичные события усиливаются при низкой стабильности
            ("shock", "stability"): lambda s: 1.0 + (1.0 - s) * 0.6,
            ("fear", "stability"): lambda s: 1.0 + (1.0 - s) * 0.6,
            ("cognitive_confusion", "stability"): lambda s: 1.0 + (1.0 - s) * 0.6,
            ("confusion", "stability"): lambda s: 1.0 + (1.0 - s) * 0.6,

            # Стабильность: спокойные события усиливаются при высокой стабильности
            ("cognitive_clarity", "stability"): lambda s: 0.9 + s * 0.3,
            ("insight", "stability"): lambda s: 0.9 + s * 0.3,
            ("calm", "stability"): lambda s: 0.9 + s * 0.3,
            ("acceptance", "stability"): lambda s: 0.9 + s * 0.3,
        }


class PatternModifier:
    """Модификатор интенсивности на основе паттернов событий."""

    def calculate(self, event_type: str, context: Optional[Context]) -> float:
        if not context or not context.recent_events:
            return 1.0

        # Анализ паттернов: повторяющиеся события усиливаются
        recent_count = sum(1 for e in context.recent_events[-10:] if e == event_type)
        pattern_factor = 1.0 + (recent_count * 0.1)  # +10% за каждое повторение

        # Но не более 2x усиления
        return min(2.0, pattern_factor)


class TimeBasedModifier:
    """Модификатор интенсивности на основе субъективного времени."""

    def calculate(self, event_type: str, context: Optional[Context]) -> float:
        if not context:
            return 1.0

        modifier = 1.0

        # Модификатор субъективного времени
        time_modifier = (
            context.subjective_time_intensity_coeff +
            context.subjective_time_stability_coeff * context.stability +
            context.subjective_time_energy_coeff * (context.energy / 100.0)
        )

        # Циркадный ритм
        circadian_factor = self._calculate_circadian_factor(context.circadian_phase, event_type)

        # Эффективность восстановления
        recovery_factor = context.recovery_efficiency

        modifier *= time_modifier * circadian_factor * recovery_factor

        return modifier

    def _calculate_circadian_factor(self, phase: float, event_type: str) -> float:
        """Расчет влияния циркадного ритма."""
        # Упрощенная модель: активность выше днем, ниже ночью
        day_night_factor = 0.8 + 0.4 * abs(phase - 0.5) * 2  # 0.8-1.2

        # Некоторые события сильнее ночью (экзистенциальные)
        if event_type.startswith('existential'):
            return day_night_factor * 1.2
        # Некоторые события сильнее днем (активные)
        elif event_type in ['curiosity', 'inspiration', 'joy']:
            return day_night_factor * 0.9

        return day_night_factor


class CategoryModifier:
    """Категорийный модификатор интенсивности."""

    def calculate(self, event_type: str, context: Optional[Context]) -> float:
        if not context:
            return 1.0

        # Категориальные правила на основе типа события
        categories = {
            'emotional_positive': ['joy', 'comfort', 'calm', 'acceptance'],
            'emotional_negative': ['sadness', 'fear', 'discomfort', 'fatigue'],
            'cognitive': ['cognitive_clarity', 'cognitive_confusion', 'insight', 'confusion'],
            'social': ['social_presence', 'social_conflict', 'social_harmony', 'connection', 'isolation'],
            'existential': ['existential_void', 'existential_purpose', 'existential_finitude'],
            'creative': ['inspiration', 'curiosity', 'creative_dissonance'],
        }

        # Находим категорию события
        event_category = None
        for category, events in categories.items():
            if event_type in events:
                event_category = category
                break

        if not event_category:
            return 1.0

        # Применяем категориальные правила
        if event_category == 'emotional_positive':
            # Положительные эмоции усиливаются при высокой стабильности
            return 0.9 + context.stability * 0.3
        elif event_category == 'emotional_negative':
            # Негативные эмоции усиливаются при низкой стабильности
            return 1.0 + (1.0 - context.stability) * 0.4
        elif event_category == 'cognitive':
            # Когнитивные события зависят от целостности
            return 0.8 + context.integrity * 0.4
        elif event_category == 'social':
            # Социальные события зависят от энергии
            energy_factor = context.energy / 100.0
            return 0.9 + energy_factor * 0.3
        elif event_category == 'existential':
            # Экзистенциальные события усиливаются при низкой энергии
            return 1.0 + (1.0 - context.energy / 100.0) * 0.5
        elif event_category == 'creative':
            # Креативные события усиливаются при средней энергии
            energy_factor = context.energy / 100.0
            optimal_factor = 1.0 - abs(energy_factor - 0.7) * 2  # Максимум при 70% энергии
            return 0.8 + optimal_factor * 0.4

        return 1.0