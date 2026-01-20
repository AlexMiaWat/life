from typing import Dict

from src.environment.event import Event

from .meaning import Meaning


class MeaningEngine:
    """
    Движок интерпретации событий.

    Преобразует Event + SelfState в Meaning.

    Компоненты:
    1. Appraisal — первичная оценка значимости
    2. ImpactModel — расчёт влияния на состояние
    3. ResponsePattern — формирование паттерна реакции
    """

    def __init__(self):
        """Инициализация движка с базовыми настройками"""
        self.base_significance_threshold = 0.1

    def appraisal(self, event: Event, self_state: Dict) -> float:
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
        learning_params = self_state.get("learning_params", {})
        event_sensitivity = learning_params.get("event_type_sensitivity", {})
        adaptation_params = self_state.get("adaptation_params", {})
        behavior_sensitivity = adaptation_params.get("behavior_sensitivity", {})

        # Вычисляем модификаторы чувствительности
        learning_modifier = 1.0
        adaptation_modifier = 1.0

        if event.type in event_sensitivity:
            # Модифицируем значимость на основе обученной чувствительности
            # Используем линейную интерполяцию вместо умножения для мягкого эффекта
            sensitivity = event_sensitivity[event.type]
            learning_modifier = 0.5 + sensitivity * 0.5  # Диапазон [0.5, 1.0]

        if event.type in behavior_sensitivity:
            # Дополнительная модификация на основе адаптированной чувствительности
            behavior_sens = behavior_sensitivity[event.type]
            adaptation_modifier = 0.5 + behavior_sens * 0.5  # Диапазон [0.5, 1.0]

        # Используем среднее значение модификаторов вместо умножения
        # Это предотвращает квадратичный эффект и соблюдает принцип медленного изменения
        # Максимальное изменение: (1.0 + 1.0) / 2 = 1.0 (без изменения)
        # Минимальное изменение: (0.5 + 0.5) / 2 = 0.5 (уменьшение в 2 раза)
        combined_modifier = (learning_modifier + adaptation_modifier) / 2.0

        # Ограничиваем максимальное изменение значимости для соблюдения принципа медленного изменения
        # Максимальное изменение не должно превышать 1.5x от исходной значимости
        max_modifier = 1.5
        combined_modifier = min(combined_modifier, max_modifier)

        significance *= combined_modifier

        # Контекстуальная модификация на основе состояния
        # Если integrity низкая — даже малые события становятся важнее
        if self_state["integrity"] < 0.3:
            significance *= 1.5

        # Если stability низкая — события ощущаются сильнее
        if self_state["stability"] < 0.5:
            significance *= 1.2

        # Ограничение диапазона
        return max(0.0, min(1.0, significance))

    def impact_model(
        self, event: Event, self_state: Dict, significance: float
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
        self, event: Event, self_state: Dict, significance: float
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
        learning_params = self_state.get("learning_params", {})
        significance_thresholds = learning_params.get("significance_thresholds", {})
        event_threshold = significance_thresholds.get(
            event.type, self.base_significance_threshold
        )

        # ИНТЕГРАЦИЯ: Используем adaptation_params.behavior_thresholds
        adaptation_params = self_state.get("adaptation_params", {})
        behavior_thresholds = adaptation_params.get("behavior_thresholds", {})
        behavior_threshold = behavior_thresholds.get(event.type, event_threshold)

        # Используем адаптированный порог
        effective_threshold = behavior_threshold

        if significance < effective_threshold:
            return "ignore"

        # При высокой стабильности — ослабление эффектов
        if self_state["stability"] > 0.8:
            return "dampen"

        # При низкой стабильности — усиление эффектов
        if self_state["stability"] < 0.3:
            return "amplify"

        # По умолчанию — нормальное поглощение
        return "absorb"

    def process(self, event: Event, self_state: Dict) -> Meaning:
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
        learning_params = self_state.get("learning_params", {})
        response_coefficients = learning_params.get("response_coefficients", {})
        adaptation_params = self_state.get("adaptation_params", {})
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
