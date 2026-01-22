import time
from typing import Any, Dict, List, Optional

from .event import Event
from .event_dependency_manager import EventDependencyManager


class PatternAnalyzer:
    """
    Анализатор паттернов событий для предиктивной адаптации интенсивности.

    Отвечает за:
    - обнаружение паттернов в последовательностях событий
    - вычисление модификаторов интенсивности на основе паттернов
    - интеграцию с системой зависимостей событий
    """

    def __init__(self, dependency_manager: EventDependencyManager):
        """
        Инициализация анализатора паттернов.

        Args:
            dependency_manager: Менеджер зависимостей событий
        """
        self.dependency_manager = dependency_manager

    def analyze_pattern_modifier(self, event_type: str, recent_events: List) -> float:
        """
        Анализирует паттерны событий и возвращает модификатор интенсивности.
        Оптимизированная версия с кэшированием.

        Args:
            event_type: Тип события для анализа
            recent_events: Список последних событий

        Returns:
            Модификатор интенсивности на основе паттернов (0.5-2.0)
        """
        if len(recent_events) < 3:
            return 1.0

        # Создаем быстрый хэш последних событий для кэширования
        # Используем только типы событий для хэша (достаточно для паттерн анализа)
        recent_types = tuple(event.type for event in recent_events[-10:])
        cache_key = (event_type, recent_types)

        # Проверяем кэш паттернов
        if not hasattr(self, '_pattern_cache'):
            self._pattern_cache = {}

        if cache_key in self._pattern_cache:
            return self._pattern_cache[cache_key]

        # Определяем паттерн (только если не в кэше)
        pattern = self.dependency_manager.detect_pattern(recent_events[-10:])

        modifier = 1.0
        if pattern:
            # Предварительно вычисленная таблица модификаторов для быстрого доступа
            pattern_modifiers = self._get_pattern_modifiers_table()

            if pattern in pattern_modifiers and event_type in pattern_modifiers[pattern]:
                modifier = pattern_modifiers[pattern][event_type]

        # Кэшируем результат
        self._pattern_cache[cache_key] = modifier

        # Ограничиваем размер кэша
        if len(self._pattern_cache) > 100:
            # Удаляем случайные 20% записей для предотвращения переполнения
            import random
            keys_to_remove = random.sample(list(self._pattern_cache.keys()),
                                        k=int(len(self._pattern_cache) * 0.2))
            for key in keys_to_remove:
                del self._pattern_cache[key]

        return modifier

    def _get_pattern_modifiers_table(self) -> dict:
        """Возвращает предварительно вычисленную таблицу модификаторов паттернов."""
        return {
            "confusion_to_insight": {
                "insight": 1.5,      # Усиливаем озарение в паттерне путаница->озарение
                "confusion": 0.8,    # Ослабляем путаницу
                "curiosity": 1.2,    # Усиливаем любопытство
            },
            "isolation_to_connection": {
                "connection": 1.6,   # Усиливаем связь в паттерне изоляция->связь
                "isolation": 0.7,    # Ослабляем изоляцию
                "joy": 1.3,          # Усиливаем радость
            },
            "void_to_meaning": {
                "meaning_found": 1.7, # Усиливаем нахождение смысла
                "void": 0.6,         # Ослабляем пустоту
                "acceptance": 1.4,   # Усиливаем принятие
            },
            "learning_cycle": {
                "insight": 1.4,      # Усиливаем озарения в цикле обучения
                "curiosity": 1.3,    # Усиливаем любопытство
                "confusion": 0.9,    # Ослабляем путаницу
            },
            "social_cycle": {
                "connection": 1.5,   # Усиливаем связи в социальном цикле
                "acceptance": 1.3,   # Усиливаем принятие
                "isolation": 0.8,    # Ослабляем изоляцию
            },
            "existential_crisis": {
                "meaning_found": 1.8, # Усиливаем нахождение смысла в кризисе
                "confusion": 0.8,    # Ослабляем путаницу
                "void": 0.7,         # Ослабляем пустоту
            },
        }

    def detect_emotional_patterns(self, recent_events: List) -> Optional[str]:
        """
        Обнаруживает эмоциональные паттерны в последовательности событий.

        Args:
            recent_events: Список последних событий

        Returns:
            Название обнаруженного паттерна или None
        """
        if len(recent_events) < 5:
            return None

        # Получаем типы последних событий
        recent_types = [event.type for event in recent_events[-10:]]

        # Паттерны эмоциональных циклов
        patterns = {
            "stress_recovery": ["fear", "anxiety", "calm", "recovery"],
            "creative_flow": ["boredom", "curiosity", "inspiration", "insight"],
            "social_engagement": ["isolation", "curiosity", "connection", "joy"],
            "existential_search": ["void", "confusion", "curiosity", "meaning_found"],
        }

        for pattern_name, pattern_sequence in patterns.items():
            if self._matches_sequence(recent_types, pattern_sequence):
                return pattern_name

        return None

    def detect_behavioral_patterns(self, recent_events: List) -> Optional[str]:
        """
        Обнаруживает поведенческие паттерны.

        Args:
            recent_events: Список последних событий

        Returns:
            Название обнаруженного паттерна или None
        """
        if len(recent_events) < 7:
            return None

        recent_types = [event.type for event in recent_events[-15:]]

        # Поведенческие паттерны
        patterns = {
            "exploration_cycle": ["curiosity", "insight", "curiosity", "confusion", "insight"],
            "avoidance_pattern": ["fear", "isolation", "silence", "fear"],
            "engagement_burst": ["connection", "joy", "connection", "social_harmony"],
            "rumination_loop": ["confusion", "void", "confusion", "existential_void"],
        }

        for pattern_name, pattern_sequence in patterns.items():
            if self._matches_sequence(recent_types, pattern_sequence):
                return pattern_name

        return None

    def get_pattern_statistics(self) -> Dict[str, Any]:
        """
        Возвращает статистику обнаруженных паттернов.

        Returns:
            Статистика паттернов
        """
        return {
            "dependency_patterns": self.dependency_manager.get_dependency_stats(),
            "supported_patterns": [
                "confusion_to_insight",
                "isolation_to_connection",
                "void_to_meaning",
                "learning_cycle",
                "social_cycle",
                "existential_crisis"
            ]
        }

    def _matches_sequence(self, event_sequence: List[str], pattern: List[str]) -> bool:
        """
        Проверяет, соответствует ли последовательность событий паттерну.

        Args:
            event_sequence: Последовательность типов событий
            pattern: Шаблон паттерна

        Returns:
            True если последовательность соответствует паттерну
        """
        if len(event_sequence) < len(pattern):
            return False

        # Ищем паттерн в конце последовательности
        sequence_end = event_sequence[-len(pattern):]

        # Проверяем соответствие с учетом возможных пропусков
        pattern_index = 0
        for event_type in sequence_end:
            if pattern_index < len(pattern) and event_type == pattern[pattern_index]:
                pattern_index += 1

        return pattern_index == len(pattern)