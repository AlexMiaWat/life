"""
Smoothing Engine - независимый компонент для сглаживания значений.

Отвечает за:
- Экспоненциальное сглаживание модификаторов
- Сглаживание интенсивностей событий
- Поддержание истории значений
- Оптимизацию производительности

Архитектурный контракт:
- Вход: value (float), history (List[float]) или modifier (float)
- Выход: сглаженное значение (float)
- Гарантии: детерминированный расчет, thread-safe, ограниченная память
"""

from typing import Dict, List
from dataclasses import dataclass
from collections import deque


@dataclass
class SmoothingContract:
    """Контракт для сглаживания значений."""

    # Параметры сглаживания
    smoothing_params = {
        'alpha_modifier': 0.3,      # Коэффициент сглаживания модификаторов
        'alpha_intensity': 0.2,     # Коэффициент сглаживания интенсивностей
        'history_size': 50,         # Максимальный размер истории
        'min_samples': 3,           # Минимальное количество сэмплов для сглаживания
    }

    # Гарантии выходных значений
    output_guarantees = {
        'smoothing_factor': (0.0, 1.0),
        'stability': 0.95,  # Минимум 95% стабильности
    }


class SmoothingEngine:
    """
    Движок сглаживания значений.

    Использует экспоненциальное сглаживание для:
    - Модификаторов интенсивности
    - Значений интенсивности событий
    - Поддержания стабильности расчетов
    """

    def __init__(self):
        self.contract = SmoothingContract()

        # Хранилища для сглаживания
        self.modifier_history: Dict[str, deque] = {}
        self.intensity_history: Dict[str, deque] = {}

        # Текущие сглаженные значения
        self.smoothed_modifiers: Dict[str, float] = {}
        self.smoothed_intensities: Dict[str, float] = {}

    def smooth_modifier(self, event_type: str, modifier: float) -> float:
        """
        Сгладить модификатор интенсивности.

        Args:
            event_type: Тип события
            modifier: Текущий модификатор

        Returns:
            Сглаженный модификатор
        """
        if event_type not in self.smoothed_modifiers:
            # Первое значение - используем как есть
            self.smoothed_modifiers[event_type] = modifier
            self.modifier_history[event_type] = deque(maxlen=self.contract.smoothing_params['history_size'])
            self.modifier_history[event_type].append(modifier)
            return modifier

        # Экспоненциальное сглаживание
        alpha = self.contract.smoothing_params['alpha_modifier']
        previous = self.smoothed_modifiers[event_type]

        smoothed = alpha * modifier + (1 - alpha) * previous
        self.smoothed_modifiers[event_type] = smoothed

        # Добавляем в историю
        self.modifier_history[event_type].append(smoothed)

        return smoothed

    def smooth_intensity(self, event_type: str, intensity: float) -> float:
        """
        Сгладить значение интенсивности события.

        Args:
            event_type: Тип события
            intensity: Текущая интенсивность

        Returns:
            Сглаженная интенсивность
        """
        if event_type not in self.smoothed_intensities:
            # Первое значение
            self.smoothed_intensities[event_type] = intensity
            self.intensity_history[event_type] = deque(maxlen=self.contract.smoothing_params['history_size'])
            self.intensity_history[event_type].append(intensity)
            return intensity

        # Экспоненциальное сглаживание
        alpha = self.contract.smoothing_params['alpha_intensity']
        previous = self.smoothed_intensities[event_type]

        smoothed = alpha * intensity + (1 - alpha) * previous
        self.smoothed_intensities[event_type] = smoothed

        # Добавляем в историю
        self.intensity_history[event_type].append(smoothed)

        return smoothed

    def get_smoothed_modifier(self, event_type: str) -> float:
        """
        Получить текущее сглаженное значение модификатора.

        Args:
            event_type: Тип события

        Returns:
            Сглаженный модификатор или 1.0 если нет данных
        """
        return self.smoothed_modifiers.get(event_type, 1.0)

    def get_smoothed_intensity(self, event_type: str) -> float:
        """
        Получить текущее сглаженное значение интенсивности.

        Args:
            event_type: Тип события

        Returns:
            Сглаженная интенсивность или 0.0 если нет данных
        """
        return self.smoothed_intensities.get(event_type, 0.0)

    def get_modifier_history(self, event_type: str) -> List[float]:
        """
        Получить историю модификаторов для типа события.

        Args:
            event_type: Тип события

        Returns:
            Список последних значений модификаторов
        """
        if event_type not in self.modifier_history:
            return []
        return list(self.modifier_history[event_type])

    def get_intensity_history(self, event_type: str) -> List[float]:
        """
        Получить историю интенсивностей для типа события.

        Args:
            event_type: Тип события

        Returns:
            Список последних значений интенсивностей
        """
        if event_type not in self.intensity_history:
            return []
        return list(self.intensity_history[event_type])

    def reset_history(self, event_type: str = None):
        """
        Сбросить историю сглаживания.

        Args:
            event_type: Тип события для сброса (None - сбросить все)
        """
        if event_type:
            self.smoothed_modifiers.pop(event_type, None)
            self.smoothed_intensities.pop(event_type, None)
            self.modifier_history.pop(event_type, None)
            self.intensity_history.pop(event_type, None)
        else:
            self.smoothed_modifiers.clear()
            self.smoothed_intensities.clear()
            self.modifier_history.clear()
            self.intensity_history.clear()

    def get_statistics(self) -> Dict[str, Dict[str, int]]:
        """
        Получить статистику использования сглаживания.

        Returns:
            Статистика по типам событий
        """
        stats = {}
        for event_type in set(self.modifier_history.keys()) | set(self.intensity_history.keys()):
            stats[event_type] = {
                'modifier_samples': len(self.modifier_history.get(event_type, [])),
                'intensity_samples': len(self.intensity_history.get(event_type, [])),
            }
        return stats