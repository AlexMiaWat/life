"""
Response Selector - выбор ответа по правилам

Отвечает за выбор паттерна реакции на основе простых правил с приоритетами.
"""
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class Pattern(Enum):
    """Паттерны реакции системы."""
    IGNORE = "ignore"
    ABSORB = "absorb"
    DAMPEN = "dampen"
    AMPLIFY = "amplify"


@dataclass
class Rule:
    """
    Правило выбора паттерна реакции.

    Правила оцениваются в порядке приоритета (выше приоритет - раньше проверка).
    """
    name: str
    priority: int
    condition: Callable[[Dict[str, Any]], bool]
    pattern: Pattern
    description: str = ""

    def evaluate(self, context: Dict[str, Any]) -> Optional[Pattern]:
        """
        Оценить правило на основе контекста.

        Args:
            context: Контекст принятия решения

        Returns:
            Pattern если правило сработало, None иначе
        """
        if self.condition(context):
            return self.pattern
        return None


class ResponseSelector:
    """
    Выбирает паттерн реакции на основе правил с приоритетами.

    Правила упорядочены по приоритету, первое сработавшее правило определяет паттерн.
    """

    def __init__(self):
        """Инициализация селектора с базовыми правилами."""
        self.rules = self._create_default_rules()

    def select_pattern(
        self,
        memory_analysis: Dict[str, Any],
        context_analysis: Dict[str, Any],
        meaning: Any,
        self_state: Any,
    ) -> str:
        """
        Выбрать паттерн реакции на основе анализа.

        Args:
            memory_analysis: Анализ активированной памяти
            context_analysis: Анализ системного контекста
            meaning: Текущий meaning
            self_state: Текущее состояние системы

        Returns:
            Выбранный паттерн реакции
        """
        # Объединяем контекст для оценки правил
        evaluation_context = {
            **memory_analysis,
            **context_analysis,
            "meaning": meaning,
            "self_state": self_state,
        }

        # Правила отсортированы по приоритету (выше - раньше)
        sorted_rules = sorted(self.rules, key=lambda r: r.priority, reverse=True)

        for rule in sorted_rules:
            pattern = rule.evaluate(evaluation_context)
            if pattern:
                return pattern.value

        # Fallback - absorb по умолчанию
        return Pattern.ABSORB.value

    def _create_default_rules(self) -> List[Rule]:
        """Создать базовый набор правил с приоритетами."""
        return [
            # Правило 1: Высокий приоритет - экстренные ситуации
            Rule(
                name="emergency_ignore",
                priority=100,
                condition=self._emergency_ignore_condition,
                pattern=Pattern.IGNORE,
                description="Игнорировать при критически низкой энергии и незначительных событиях"
            ),

            # Правило 2: Высокая концентрация значимых воспоминаний
            Rule(
                name="high_memory_concentration",
                priority=90,
                condition=self._high_memory_concentration_condition,
                pattern=Pattern.DAMPEN,
                description="Смягчать при высокой концентрации значимых воспоминаний"
            ),

            # Правило 3: Низкая энергия
            Rule(
                name="low_energy_conservative",
                priority=80,
                condition=self._low_energy_condition,
                pattern=Pattern.DAMPEN,
                description="Консервативный подход при низкой энергии"
            ),

            # Правило 4: Высокая стабильность
            Rule(
                name="high_stability_dampen",
                priority=70,
                condition=self._high_stability_condition,
                pattern=Pattern.DAMPEN,
                description="Смягчать эффекты при высокой стабильности"
            ),

            # Правило 5: Низкая стабильность - усиление положительных
            Rule(
                name="low_stability_amplify_positive",
                priority=60,
                condition=self._low_stability_amplify_condition,
                pattern=Pattern.AMPLIFY,
                description="Усиливать положительные события при низкой стабильности"
            ),

            # Правило 6: Низкая целостность
            Rule(
                name="low_integrity_conservative",
                priority=50,
                condition=self._low_integrity_condition,
                pattern=Pattern.DAMPEN,
                description="Осторожный подход при низкой целостности"
            ),

            # Правило 7: Циркадные ритмы - ночь
            Rule(
                name="circadian_night_ignore",
                priority=40,
                condition=self._circadian_night_condition,
                pattern=Pattern.IGNORE,
                description="Игнорировать незначительные события ночью"
            ),

            # Правило 8: Циркадные ритмы - день
            Rule(
                name="circadian_day_amplify",
                priority=40,
                condition=self._circadian_day_condition,
                pattern=Pattern.AMPLIFY,
                description="Усиливать положительные события днем"
            ),

            # Правило 9: Специфические правила по типу события
            Rule(
                name="event_type_rules",
                priority=30,
                condition=self._event_type_condition,
                pattern=Pattern.DAMPEN,  # Определяется динамически
                description="Правила на основе типа события"
            ),

            # Правило 10: Взвешенный анализ (низкий приоритет - fallback)
            Rule(
                name="weighted_analysis",
                priority=10,
                condition=self._weighted_analysis_condition,
                pattern=Pattern.ABSORB,  # Определяется динамически
                description="Финальный взвешенный анализ"
            ),
        ]

    def _emergency_ignore_condition(self, context: Dict[str, Any]) -> bool:
        """Экстренное игнорирование при критической ситуации."""
        energy_level = context.get("energy_level")
        weighted_avg = context.get("weighted_avg", 0.0)
        meaning_sig = context.get("meaning_significance", 0.0)
        dynamic_ignore_threshold = context.get("dynamic_ignore_threshold", 0.1)

        return (
            energy_level == "low"
            and weighted_avg < dynamic_ignore_threshold * 0.5
            and meaning_sig < dynamic_ignore_threshold * 0.5
        )

    def _high_memory_concentration_condition(self, context: Dict[str, Any]) -> bool:
        """Высокая концентрация значимых воспоминаний."""
        distribution = context.get("distribution")
        max_sig = context.get("max_sig", 0.0)
        return distribution == "high_concentrated" or max_sig > 0.8

    def _low_energy_condition(self, context: Dict[str, Any]) -> bool:
        """Низкая энергия."""
        energy_level = context.get("energy_level")
        stability_level = context.get("stability_level")
        weighted_avg = context.get("weighted_avg", 0.0)
        meaning_sig = context.get("meaning_significance", 0.0)
        dynamic_dampen_threshold = context.get("dynamic_dampen_threshold", 0.3)

        if energy_level != "low":
            return False

        # Исключение для положительных событий при низкой стабильности
        event_rules = self._get_event_type_rules(context)
        is_positive_and_unstable = (
            stability_level == "low"
            and event_rules.get("positive_event", False)
            and event_rules.get("can_amplify", True)
            and meaning_sig > dynamic_dampen_threshold
        )

        return not is_positive_and_unstable and (
            weighted_avg > dynamic_dampen_threshold or meaning_sig > dynamic_dampen_threshold
        )

    def _high_stability_condition(self, context: Dict[str, Any]) -> bool:
        """Высокая стабильность."""
        stability_level = context.get("stability_level")
        weighted_avg = context.get("weighted_avg", 0.0)
        meaning_sig = context.get("meaning_significance", 0.0)
        dynamic_dampen_threshold = context.get("dynamic_dampen_threshold", 0.3)

        return (
            stability_level == "high"
            and (weighted_avg > dynamic_dampen_threshold or meaning_sig > dynamic_dampen_threshold)
        )

    def _low_stability_amplify_condition(self, context: Dict[str, Any]) -> bool:
        """Низкая стабильность - усиление положительных."""
        stability_level = context.get("stability_level")
        meaning_sig = context.get("meaning_significance", 0.0)
        dynamic_dampen_threshold = context.get("dynamic_dampen_threshold", 0.3)

        event_rules = self._get_event_type_rules(context)
        return (
            stability_level == "low"
            and event_rules.get("can_amplify", True)
            and event_rules.get("positive_event", False)
            and meaning_sig > dynamic_dampen_threshold
        )

    def _low_integrity_condition(self, context: Dict[str, Any]) -> bool:
        """Низкая целостность."""
        integrity_level = context.get("integrity_level")
        weighted_avg = context.get("weighted_avg", 0.0)
        meaning_sig = context.get("meaning_significance", 0.0)
        dynamic_dampen_threshold = context.get("dynamic_dampen_threshold", 0.3)

        return (
            integrity_level == "low"
            and (weighted_avg > dynamic_dampen_threshold or meaning_sig > dynamic_dampen_threshold)
        )

    def _circadian_night_condition(self, context: Dict[str, Any]) -> bool:
        """Циркадные ритмы - ночь."""
        circadian_phase = context.get("circadian_phase")
        weighted_avg = context.get("weighted_avg", 0.0)
        meaning_sig = context.get("meaning_significance", 0.0)
        dynamic_ignore_threshold = context.get("dynamic_ignore_threshold", 0.1)

        return (
            circadian_phase == "night"
            and weighted_avg < dynamic_ignore_threshold * 1.2
            and meaning_sig < dynamic_ignore_threshold * 1.2
        )

    def _circadian_day_condition(self, context: Dict[str, Any]) -> bool:
        """Циркадные ритмы - день."""
        circadian_phase = context.get("circadian_phase")
        energy_level = context.get("energy_level")
        meaning_sig = context.get("meaning_significance", 0.0)
        dynamic_dampen_threshold = context.get("dynamic_dampen_threshold", 0.3)

        event_rules = self._get_event_type_rules(context)
        return (
            circadian_phase == "day"
            and event_rules.get("can_amplify", True)
            and event_rules.get("positive_event", False)
            and meaning_sig > dynamic_dampen_threshold * 1.1
            and energy_level == "high"
        )

    def _event_type_condition(self, context: Dict[str, Any]) -> bool:
        """Специфические правила по типу события."""
        event_rules = self._get_event_type_rules(context)
        weighted_avg = context.get("weighted_avg", 0.0)
        meaning_sig = context.get("meaning_significance", 0.0)
        dynamic_dampen_threshold = context.get("dynamic_dampen_threshold", 0.3)

        # Динамически устанавливаем паттерн для этого правила
        if event_rules.get("prefer_dampen", False):
            if (
                weighted_avg > dynamic_dampen_threshold or meaning_sig > dynamic_dampen_threshold
            ):
                # Устанавливаем паттерн динамически
                self.rules = [
                    rule if rule.name != "event_type_rules"
                    else Rule(
                        name="event_type_rules",
                        priority=30,
                        condition=self._event_type_condition,
                        pattern=Pattern.DAMPEN,
                        description="Правила на основе типа события"
                    )
                    for rule in self.rules
                ]
                return True

        if event_rules.get("prefer_absorb", False) and weighted_avg <= dynamic_dampen_threshold:
            self.rules = [
                rule if rule.name != "event_type_rules"
                else Rule(
                    name="event_type_rules",
                    priority=30,
                    condition=self._event_type_condition,
                    pattern=Pattern.ABSORB,
                    description="Правила на основе типа события"
                )
                for rule in self.rules
            ]
            return True

        return False

    def _weighted_analysis_condition(self, context: Dict[str, Any]) -> bool:
        """Финальный взвешенный анализ."""
        weighted_avg = context.get("weighted_avg", 0.0)
        meaning_sig = context.get("meaning_significance", 0.0)
        dynamic_ignore_threshold = context.get("dynamic_ignore_threshold", 0.1)
        dynamic_dampen_threshold = context.get("dynamic_dampen_threshold", 0.3)

        # Определяем паттерн на основе порогов
        if weighted_avg < dynamic_ignore_threshold and meaning_sig < dynamic_ignore_threshold:
            self.rules = [
                rule if rule.name != "weighted_analysis"
                else Rule(
                    name="weighted_analysis",
                    priority=10,
                    condition=self._weighted_analysis_condition,
                    pattern=Pattern.IGNORE,
                    description="Финальный взвешенный анализ"
                )
                for rule in self.rules
            ]
            return True
        elif weighted_avg < dynamic_dampen_threshold and meaning_sig < dynamic_dampen_threshold:
            self.rules = [
                rule if rule.name != "weighted_analysis"
                else Rule(
                    name="weighted_analysis",
                    priority=10,
                    condition=self._weighted_analysis_condition,
                    pattern=Pattern.ABSORB,
                    description="Финальный взвешенный анализ"
                )
                for rule in self.rules
            ]
            return True
        else:
            self.rules = [
                rule if rule.name != "weighted_analysis"
                else Rule(
                    name="weighted_analysis",
                    priority=10,
                    condition=self._weighted_analysis_condition,
                    pattern=Pattern.DAMPEN,
                    description="Финальный взвешенный анализ"
                )
                for rule in self.rules
            ]
            return True

    def _get_event_type_rules(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Получить правила для типа события."""
        event_type = context.get("event_type", "unknown")
        meaning = context.get("meaning")

        # Правила по типам событий
        rules = {
            "shock": {"can_amplify": False, "prefer_dampen": True, "conservative_threshold": 0.3},
            "noise": {"can_ignore": True, "ignore_threshold": 0.15, "can_amplify": False},
            "recovery": {"can_amplify": True, "prefer_absorb": True, "positive_event": True},
            "decay": {"can_amplify": False, "prefer_dampen": True, "negative_event": True},
            "idle": {"can_ignore": True, "ignore_threshold": 0.05, "can_amplify": False},
            "social_presence": {"context_sensitive": True, "can_amplify": True, "positive_event": True},
            "social_conflict": {"can_amplify": False, "prefer_dampen": True, "negative_event": True},
            "cognitive_doubt": {"can_ignore": True, "context_sensitive": True, "ignore_threshold": 0.2},
            "cognitive_clarity": {"can_amplify": True, "prefer_absorb": True, "positive_event": True},
            "existential_void": {"can_amplify": False, "prefer_dampen": True, "conservative_threshold": 0.2},
            "existential_purpose": {"can_amplify": True, "prefer_absorb": True, "positive_event": True},
            "connection": {"can_amplify": True, "prefer_absorb": True, "positive_event": True, "context_sensitive": True},
            "isolation": {"can_amplify": False, "prefer_dampen": True, "negative_event": True, "conservative_threshold": 0.25},
            "insight": {"can_amplify": True, "prefer_absorb": True, "positive_event": True, "conservative_threshold": 0.2},
            "confusion": {"can_amplify": False, "prefer_dampen": True, "negative_event": True, "can_ignore": True, "ignore_threshold": 0.15},
            "curiosity": {"can_amplify": True, "context_sensitive": True, "positive_event": True},
            "meaning_found": {"can_amplify": True, "prefer_absorb": True, "positive_event": True, "conservative_threshold": 0.15},
            "void": {"can_amplify": False, "prefer_dampen": True, "negative_event": True, "conservative_threshold": 0.2},
            "acceptance": {"can_amplify": True, "prefer_absorb": True, "positive_event": True, "context_sensitive": True},
        }

        return rules.get(event_type, {"can_amplify": True, "can_ignore": True, "prefer_absorb": True})