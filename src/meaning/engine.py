from typing import Dict

from environment.event import Event

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

        Returns:
            pattern (str): название паттерна
        """
        if significance < self.base_significance_threshold:
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
        final_impact = base_impact.copy()
        if pattern == "ignore":
            final_impact = {k: 0.0 for k in final_impact}
        elif pattern == "dampen":
            final_impact = {k: v * 0.5 for k, v in final_impact.items()}
        elif pattern == "amplify":
            final_impact = {k: v * 1.5 for k, v in final_impact.items()}
        # "absorb" оставляет impact без изменений

        # 5. Создание Meaning
        return Meaning(
            event_id=str(id(event)), significance=significance, impact=final_impact
        )
