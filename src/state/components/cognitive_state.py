from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class CognitiveState:
    """
    Компонент состояния, отвечающий за когнитивные аспекты системы Life.

    Включает планирование, интеллект, сознание и экспериментальные когнитивные параметры.
    """

    # Высокоуровневые когнитивные структуры
    planning: Dict[str, Any] = field(default_factory=dict)      # Планирование
    intelligence: Dict[str, Any] = field(default_factory=dict)  # Интеллект

    # Параметры сознания
    consciousness_level: float = 0.5  # Уровень сознания [0, 1]
    clarity_type: Optional[str] = None # Тип ясности (если активна)

    # История когнитивных состояний
    clarity_history: List[Any] = field(default_factory=list)  # История моментов ясности
    state_transition_history: List[Any] = field(default_factory=list)  # История переходов состояний

    def update_planning_state(self, key: str, value: Any) -> None:
        """Обновляет состояние планирования."""
        self.planning[key] = value

    def update_intelligence_state(self, key: str, value: Any) -> None:
        """Обновляет состояние интеллекта."""
        self.intelligence[key] = value

    def get_planning_context(self) -> Dict[str, Any]:
        """Возвращает контекст планирования."""
        return self.planning.copy()

    def get_intelligence_context(self) -> Dict[str, Any]:
        """Возвращает контекст интеллекта."""
        return self.intelligence.copy()

    def set_consciousness_level(self, level: float) -> None:
        """Устанавливает уровень сознания с валидацией."""
        self.consciousness_level = max(0.0, min(1.0, level))

    def activate_clarity(self, clarity_type: str) -> None:
        """Активирует состояние ясности."""
        self.clarity_type = clarity_type

    def deactivate_clarity(self) -> None:
        """Деактивирует состояние ясности."""
        self.clarity_type = None

    def is_clarity_active(self) -> bool:
        """Проверяет, активно ли состояние ясности."""
        return self.clarity_type is not None

    def get_cognitive_stats(self) -> Dict[str, Any]:
        """Возвращает статистику когнитивного состояния."""
        return {
            "consciousness_level": self.consciousness_level,
            "clarity_active": self.is_clarity_active(),
            "clarity_type": self.clarity_type,
            "planning_items": len(self.planning),
            "intelligence_items": len(self.intelligence)
        }