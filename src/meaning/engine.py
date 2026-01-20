import logging
from typing import Dict, Union

from src.environment.event import Event
from src.state.self_state import SelfState

from .meaning import Meaning

logger = logging.getLogger(__name__)


class MeaningEngine:
    """
    Движок интерпретации событий.

    Преобразует Event + SelfState в Meaning.

    Компоненты:
    1. Appraisal — первичная оценка значимости
    2. ImpactModel — расчёт влияния на состояние
    3. ResponsePattern — формирование паттерна реакции
    """

    # Коэффициент для линейной интерполяции модификаторов чувствительности
    # Используется для преобразования sensitivity [0.0, 1.0] в модификатор [0.5, 1.0]
    # Формула: modifier = SENSITIVITY_INTERPOLATION_BASE + sensitivity * SENSITIVITY_INTERPOLATION_RANGE
    SENSITIVITY_INTERPOLATION_BASE = 0.5
    SENSITIVITY_INTERPOLATION_RANGE = 0.5

    # Максимальный модификатор значимости для соблюдения принципа медленного изменения
    # Ограничивает максимальное изменение значимости до 1.5x от исходной
    MAX_SIGNIFICANCE_MODIFIER = 1.5

    # Порог integrity для контекстуальной модификации значимости
    # Если integrity ниже этого порога, события становятся более значимыми
    LOW_INTEGRITY_THRESHOLD = 0.3

    # Множитель значимости при низкой integrity
    # Применяется когда integrity < LOW_INTEGRITY_THRESHOLD
    LOW_INTEGRITY_SIGNIFICANCE_MULTIPLIER = 1.5

    def __init__(self):
        """Инициализация движка с базовыми настройками"""
        self.base_significance_threshold = 0.1

    def _get_learning_and_adaptation_params(
        self, self_state: Union[SelfState, Dict]
    ) -> tuple[Dict, Dict]:
        """
        Получить learning_params и adaptation_params из self_state.

        Поддерживает как объект SelfState, так и словарь (для обратной совместимости).

        Args:
            self_state: SelfState или словарь с параметрами

        Returns:
            tuple[Dict, Dict]: (learning_params, adaptation_params)
        """
        if isinstance(self_state, SelfState):
            learning_params = getattr(self_state, "learning_params", {})
            adaptation_params = getattr(self_state, "adaptation_params", {})
        else:
            learning_params = self_state.get("learning_params", {})
            adaptation_params = self_state.get("adaptation_params", {})

        # Проверяем, что параметры действительно словари
        if not isinstance(learning_params, dict):
            logger.warning(
                f"learning_params имеет некорректный тип {type(learning_params)}, "
                "заменяем на пустой словарь"
            )
            learning_params = {}
        if not isinstance(adaptation_params, dict):
            logger.warning(
                f"adaptation_params имеет некорректный тип {type(adaptation_params)}, "
                "заменяем на пустой словарь"
            )
            adaptation_params = {}

        return learning_params, adaptation_params

    def appraisal(self, event: Event, self_state: Union[SelfState, Dict]) -> float:
        """
        Первичная оценка: насколько это событие важно?

        Логика:
        - Учитывает тип события
        - Учитывает интенсивность
        - Учитывает текущее состояние Life
        - Использует learning_params.event_type_sensitivity для модификации чувствительности
        - Использует adaptation_params.behavior_sensitivity для дополнительной модификации

        Returns:
            significance (float): [0.0, 1.0]
        """
        # Базовая значимость из интенсивности события
        base_significance = abs(event.intensity)

        # Модификация на основе типа события
        type_weight = {
            "shock": 1.5,  # Шоки всегда значимы
            "noise": 0.5,  # Шум часто игнорируется
            "recovery": 1.0,  # Восстановление нормально
            "decay": 1.0,  # Распад нормален
            "idle": 0.2,  # Бездействие почти не значимо
        }

        weight = type_weight.get(event.type, 1.0)
        significance = base_significance * weight

        # ИНТЕГРАЦИЯ: Используем learning_params.event_type_sensitivity
        # ВАЖНО: Используем среднее значение для избежания квадратичного эффекта
        # и соблюдения принципа медленного изменения
        learning_params, adaptation_params = self._get_learning_and_adaptation_params(
            self_state
        )

        event_sensitivity = learning_params.get("event_type_sensitivity", {})
        behavior_sensitivity = adaptation_params.get("behavior_sensitivity", {})

        # Вычисляем модификаторы чувствительности
        learning_modifier = 1.0
        adaptation_modifier = 1.0

        if event.type in event_sensitivity:
            # Модифицируем значимость на основе обученной чувствительности
            # Используем линейную интерполяцию вместо умножения для мягкого эффекта
            sensitivity = event_sensitivity[event.type]
            learning_modifier = (
                self.SENSITIVITY_INTERPOLATION_BASE
                + sensitivity * self.SENSITIVITY_INTERPOLATION_RANGE
            )  # Диапазон [0.5, 1.0]

        if event.type in behavior_sensitivity:
            # Дополнительная модификация на основе адаптированной чувствительности
            behavior_sens = behavior_sensitivity[event.type]
            adaptation_modifier = (
                self.SENSITIVITY_INTERPOLATION_BASE
                + behavior_sens * self.SENSITIVITY_INTERPOLATION_RANGE
            )  # Диапазон [0.5, 1.0]

        # Используем среднее значение модификаторов вместо умножения
        # Это предотвращает квадратичный эффект и соблюдает принцип медленного изменения
        # Максимальное изменение: (1.0 + 1.0) / 2 = 1.0 (без изменения)
        # Минимальное изменение: (0.5 + 0.5) / 2 = 0.5 (уменьшение в 2 раза)
        combined_modifier = (learning_modifier + adaptation_modifier) / 2.0

        # Ограничиваем максимальное изменение значимости для соблюдения принципа медленного изменения
        # Максимальное изменение не должно превышать MAX_SIGNIFICANCE_MODIFIER от исходной значимости
        combined_modifier = min(combined_modifier, self.MAX_SIGNIFICANCE_MODIFIER)

        significance *= combined_modifier

        # Контекстуальная модификация на основе состояния
        # Если integrity низкая — даже малые события становятся важнее
        integrity = (
            getattr(self_state, "integrity", self_state.get("integrity", 1.0))
            if isinstance(self_state, SelfState)
            else self_state.get("integrity", 1.0)
        )
        if integrity < self.LOW_INTEGRITY_THRESHOLD:
            significance *= self.LOW_INTEGRITY_SIGNIFICANCE_MULTIPLIER

        # Если stability низкая — события ощущаются сильнее
        stability = (
            getattr(self_state, "stability", self_state.get("stability", 1.0))
            if isinstance(self_state, SelfState)
            else self_state.get("stability", 1.0)
        )
        if stability < 0.5:
            significance *= 1.2

        # Ограничение диапазона
        return max(0.0, min(1.0, significance))

    def impact_model(
        self, event: Event, self_state: Union[SelfState, Dict], significance: float
    ) -> Dict[str, float]:
        """
        Расчёт влияния: как это событие изменит состояние?

        Логика:
        - Базовые дельты зависят от типа события
        - Масштабируются на интенсивность и significance
        - Учитывают текущие параметры состояния
        - Используют learning_params и adaptation_params для модификации влияния

        Returns:
            impact (Dict[str, float]): {"energy": delta, "stability": delta, "integrity": delta}
        """
        # Базовые паттерны воздействия по типам событий
        base_impacts = {
            "shock": {"energy": -1.5, "stability": -0.10, "integrity": -0.05},
            "noise": {"energy": -0.3, "stability": -0.02, "integrity": 0.0},
            "recovery": {"energy": +1.0, "stability": +0.05, "integrity": +0.02},
            "decay": {"energy": -0.5, "stability": -0.01, "integrity": -0.01},
            "idle": {"energy": -0.1, "stability": 0.0, "integrity": 0.0},
        }

        base_impact = base_impacts.get(
            event.type, {"energy": 0.0, "stability": 0.0, "integrity": 0.0}
        )

        # Масштабирование на интенсивность и significance
        scaled_impact = {}
        for param, delta in base_impact.items():
            scaled_delta = delta * abs(event.intensity) * significance
            scaled_impact[param] = scaled_delta

        # ИНТЕГРАЦИЯ: Используем adaptation_params.behavior_coefficients для модификации влияния
        # (коэффициенты применяются позже в response_pattern, но здесь можем учесть базовую модификацию)
        # Коэффициенты применяются в response_pattern, здесь только базовая модификация

        return scaled_impact

    def response_pattern(
        self, event: Event, self_state: Union[SelfState, Dict], significance: float
    ) -> str:
        """
        Определение паттерна реакции.

        Возможные паттерны:
        - "ignore"       — событие игнорируется
        - "absorb"       — событие поглощается с полным эффектом
        - "dampen"       — событие ослабляется
        - "amplify"      — событие усиливается

        Использует learning_params.significance_thresholds и adaptation_params.behavior_thresholds
        для определения порогов значимости.

        Returns:
            pattern (str): название паттерна
        """
        # ИНТЕГРАЦИЯ: Используем learning_params.significance_thresholds
        learning_params, adaptation_params = self._get_learning_and_adaptation_params(
            self_state
        )

        significance_thresholds = learning_params.get("significance_thresholds", {})
        event_threshold = significance_thresholds.get(
            event.type, self.base_significance_threshold
        )

        # ИНТЕГРАЦИЯ: Используем adaptation_params.behavior_thresholds
        behavior_thresholds = adaptation_params.get("behavior_thresholds", {})
        behavior_threshold = behavior_thresholds.get(event.type, event_threshold)

        # Используем адаптированный порог
        effective_threshold = behavior_threshold

        if significance < effective_threshold:
            return "ignore"

        # При высокой стабильности — ослабление эффектов
        stability = (
            getattr(self_state, "stability", self_state.get("stability", 1.0))
            if isinstance(self_state, SelfState)
            else self_state.get("stability", 1.0)
        )
        if stability > 0.8:
            return "dampen"

        # При низкой стабильности — усиление эффектов
        if stability < 0.3:
            return "amplify"

        # По умолчанию — нормальное поглощение
        return "absorb"

    def process(self, event: Event, self_state: Union[SelfState, Dict]) -> Meaning:
        """
        Основной метод обработки события.

        Этапы:
        1. Appraisal — оценка значимости
        2. ImpactModel — расчёт влияния
        3. ResponsePattern — определение паттерна реакции
        4. Создание объекта Meaning

        Args:
            event: событие из Environment
            self_state: текущее состояние Life

        Returns:
            Meaning: интерпретированное значение
        """
        # 1. Оценка значимости
        significance = self.appraisal(event, self_state)

        # 2. Расчёт базового влияния
        base_impact = self.impact_model(event, self_state, significance)

        # 3. Определение паттерна реакции
        pattern = self.response_pattern(event, self_state, significance)

        # 4. Модификация impact на основе паттерна
        # ИНТЕГРАЦИЯ: Используем learning_params.response_coefficients и adaptation_params.behavior_coefficients
        learning_params, adaptation_params = self._get_learning_and_adaptation_params(
            self_state
        )

        response_coefficients = learning_params.get("response_coefficients", {})
        behavior_coefficients = adaptation_params.get("behavior_coefficients", {})

        final_impact = base_impact.copy()
        if pattern == "ignore":
            final_impact = {k: 0.0 for k in final_impact}
        elif pattern == "dampen":
            # Используем коэффициент из параметров, если доступен
            coefficient = behavior_coefficients.get(
                "dampen", response_coefficients.get("dampen", 0.5)
            )
            final_impact = {k: v * coefficient for k, v in final_impact.items()}
        elif pattern == "amplify":
            # Используем коэффициент из параметров, если доступен
            coefficient = behavior_coefficients.get(
                "amplify", response_coefficients.get("amplify", 1.5)
            )
            final_impact = {k: v * coefficient for k, v in final_impact.items()}
        elif pattern == "absorb":
            # Используем коэффициент из параметров, если доступен
            coefficient = behavior_coefficients.get(
                "absorb", response_coefficients.get("absorb", 1.0)
            )
            final_impact = {k: v * coefficient for k, v in final_impact.items()}

        # 5. Создание Meaning
        return Meaning(
            event_id=str(id(event)), significance=significance, impact=final_impact
        )
