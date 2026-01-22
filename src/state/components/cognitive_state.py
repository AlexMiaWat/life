from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from ...contracts.serialization_contract import Serializable


@dataclass
class CognitiveState(Serializable):
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

    # Кэш для оптимизации сериализации часто изменяемых полей
    _serialization_cache: Dict[str, Any] = field(default_factory=dict, init=False, repr=False)
    _cache_timestamp: float = field(default=0.0, init=False, repr=False)

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

    def to_dict(self, use_cache: bool = True, cache_ttl: float = 1.0) -> Dict[str, Any]:
        """
        Сериализует когнитивное состояние с оптимизациями для часто изменяемых полей.

        Args:
            use_cache: Использовать ли кэширование для производительности
            cache_ttl: Время жизни кэша в секундах

        Returns:
            Dict[str, Any]: Словарь с когнитивными параметрами
        """
        import time
        current_time = time.time()

        # Проверяем кэш для часто изменяемых полей
        if use_cache and self._serialization_cache and (current_time - self._cache_timestamp) < cache_ttl:
            # Возвращаем кэшированную версию с обновлением только динамических полей
            cached_result = self._serialization_cache.copy()
            cached_result.update({
                "consciousness_level": self.consciousness_level,  # Часто изменяется
                "clarity_type": self.clarity_type,                # Часто изменяется
                "clarity_active": self.is_clarity_active(),       # Вычисляется
                "cache_used": True,
                "cache_age": current_time - self._cache_timestamp
            })
            return cached_result

        # Полная сериализация с кэшированием статических частей
        result = {
            "planning": self._serialize_planning_lightweight(),
            "intelligence": self._serialize_intelligence_lightweight(),
            "consciousness_level": self.consciousness_level,
            "clarity_type": self.clarity_type,
            "clarity_active": self.is_clarity_active(),
            "clarity_history": self.clarity_history[-5:] if self.clarity_history else [],  # Уменьшили до 5
            "state_transition_history": self.state_transition_history[-5:] if self.state_transition_history else [],  # Уменьшили до 5
            "cognitive_stats": self.get_cognitive_stats(),
            "cache_used": False,
            "lightweight_serialization": True
        }

        # Кэшируем результат (без часто изменяемых полей)
        if use_cache:
            self._serialization_cache = {
                "planning": result["planning"].copy(),
                "intelligence": result["intelligence"].copy(),
                "clarity_history": result["clarity_history"].copy(),
                "state_transition_history": result["state_transition_history"].copy(),
                "cognitive_stats": result["cognitive_stats"].copy()
            }
            self._cache_timestamp = current_time

        return result

    def _serialize_planning_lightweight(self) -> Dict[str, Any]:
        """
        Легковесная сериализация планирования - только ключевые метрики.
        """
        planning_copy = self.planning.copy()

        # Упрощаем большие структуры, оставляя только метрики
        if "goals" in planning_copy and isinstance(planning_copy["goals"], list):
            planning_copy["goals_count"] = len(planning_copy["goals"])
            planning_copy["goals"] = planning_copy["goals"][-3:]  # Только последние 3 цели

        if "current_plan" in planning_copy and isinstance(planning_copy["current_plan"], dict):
            # Упрощаем план, оставляя только статус и ключевые метрики
            current_plan = planning_copy["current_plan"]
            planning_copy["current_plan_summary"] = {
                "status": current_plan.get("status", "unknown"),
                "progress": current_plan.get("progress", 0.0),
                "steps_count": len(current_plan.get("steps", []))
            }
            planning_copy.pop("current_plan", None)  # Удаляем полную версию

        return planning_copy

    def _serialize_intelligence_lightweight(self) -> Dict[str, Any]:
        """
        Легковесная сериализация интеллекта - только ключевые показатели.
        """
        intelligence_copy = self.intelligence.copy()

        # Упрощаем большие структуры данных
        if "knowledge_base" in intelligence_copy and isinstance(intelligence_copy["knowledge_base"], dict):
            kb = intelligence_copy["knowledge_base"]
            intelligence_copy["knowledge_base_summary"] = {
                "concepts_count": len(kb.get("concepts", {})),
                "patterns_count": len(kb.get("patterns", {})),
                "last_updated": kb.get("last_updated")
            }
            intelligence_copy.pop("knowledge_base", None)  # Удаляем полную версию

        if "reasoning_history" in intelligence_copy and isinstance(intelligence_copy["reasoning_history"], list):
            intelligence_copy["reasoning_history_count"] = len(intelligence_copy["reasoning_history"])
            intelligence_copy["reasoning_history"] = intelligence_copy["reasoning_history"][-3:]  # Только последние 3

        return intelligence_copy