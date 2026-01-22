import time
from typing import Dict, List, Optional, Tuple
from collections import deque

from .event import Event


class EventDependencyManager:
    """
    Менеджер зависимостей между событиями.

    Отслеживает паттерны событий и модифицирует вероятности генерации
    новых событий на основе недавней истории. Создает естественные
    "цепочки" и "паттерны" в потоке событий.

    Основные паттерны зависимостей:
    1. Confusion → Insight (путаница приводит к озарению)
    2. Isolation → Connection (одиночество приводит к поиску связи)
    3. Curiosity → Insight или Confusion (любопытство приводит к пониманию или путанице)
    4. Void → Meaning_found или Acceptance (пустота приводит к поиску смысла или принятию)
    5. Insight → Curiosity (озарение стимулирует дальнейшее любопытство)
    """

    def __init__(self, history_size: int = 10, decay_factor: float = 0.9):
        """
        Args:
            history_size: Размер истории событий для анализа зависимостей
            decay_factor: Фактор затухания влияния старых событий (0.0-1.0)
        """
        self.history_size = history_size
        self.decay_factor = decay_factor

        # История недавних событий с временными метками
        self.event_history: deque[Tuple[Event, float]] = deque(maxlen=history_size)

        # Матрица зависимостей: event_type -> {dependent_type: modifier}
        # modifier > 1.0 увеличивает вероятность, < 1.0 уменьшает
        self.dependency_matrix = self._initialize_dependency_matrix()

        # Счетчики для статистики зависимостей
        self.dependency_stats = {
            "chains_created": 0,
            "patterns_detected": 0,
            "total_modifications": 0
        }

    def _initialize_dependency_matrix(self) -> Dict[str, Dict[str, float]]:
        """
        Инициализация матрицы зависимостей между событиями.

        Returns:
            Матрица зависимостей с модификаторами вероятностей
        """
        return {
            # Confusion часто приводит к Insight или Curiosity
            "confusion": {
                "insight": 2.5,      # Путаница часто разрешается озарением
                "curiosity": 1.8,    # Путаница стимулирует любопытство
                "confusion": 0.3,    # Меньше шансов на повторную путаницу
                "acceptance": 1.2,   # Или приводит к принятию
            },

            # Insight стимулирует дальнейшее исследование
            "insight": {
                "curiosity": 2.2,    # Озарение рождает любопытство
                "insight": 0.4,      # Меньше шансов на повторное озарение подряд
                "meaning_found": 1.6, # Может привести к нахождению смысла
                "confusion": 0.6,    # Но иногда вызывает новую путаницу
            },

            # Isolation мотивирует поиск связи
            "isolation": {
                "connection": 2.8,   # Одиночество сильно мотивирует поиск связи
                "isolation": 0.2,    # Меньше шансов на повторное одиночество
                "void": 1.4,         # Может привести к чувству пустоты
                "curiosity": 1.3,    # Или к любопытству о других
            },

            # Connection укрепляет социальные паттерны
            "connection": {
                "connection": 0.5,   # Меньше шансов на повторную связь подряд
                "isolation": 0.3,    # Но может привести к новому одиночеству
                "joy": 1.5,          # Часто сопровождается радостью
                "calm": 1.3,         # Или спокойствием
            },

            # Curiosity может привести к различным исходам
            "curiosity": {
                "insight": 1.9,      # Любопытство часто приводит к озарению
                "confusion": 1.4,    # Или к путанице
                "curiosity": 0.7,    # Умеренное повторение любопытства
                "meaning_found": 1.2, # Иногда к нахождению смысла
            },

            # Void часто приводит к поиску смысла или принятию
            "void": {
                "meaning_found": 2.0, # Пустота мотивирует поиск смысла
                "acceptance": 1.8,   # Или приводит к принятию
                "void": 0.4,         # Меньше шансов на повторную пустоту
                "isolation": 1.3,    # Может усилить чувство изоляции
            },

            # Meaning_found укрепляет положительные паттерны
            "meaning_found": {
                "acceptance": 1.7,   # Нахождение смысла приводит к принятию
                "connection": 1.5,   # И к поиску связей
                "meaning_found": 0.3, # Редко повторяется подряд
                "joy": 1.6,          # Часто сопровождается радостью
            },

            # Acceptance стабилизирует состояние
            "acceptance": {
                "calm": 1.8,         # Принятие приводит к спокойствию
                "acceptance": 0.5,   # Умеренное повторение
                "comfort": 1.4,      # И комфорту
                "connection": 1.3,   # Может привести к связям
            },

            # Эмоциональные состояния влияют на социальные
            "joy": {
                "connection": 1.6,   # Радость способствует связям
                "curiosity": 1.4,    # И любопытству
                "joy": 0.6,          # Умеренное повторение
            },

            "sadness": {
                "isolation": 1.5,    # Грусть может привести к изоляции
                "void": 1.3,         # Или пустоте
                "acceptance": 1.4,   # Или принятию
            },

            "fear": {
                "isolation": 1.7,    # Страх приводит к изоляции
                "confusion": 1.3,    # И путанице
                "fear": 0.5,         # Умеренное повторение
            },

            "calm": {
                "acceptance": 1.5,   # Спокойствие способствует принятию
                "insight": 1.3,      # И озарениям
                "calm": 0.7,         # Может повторяться
            },

            # Физические состояния влияют на экзистенциальные
            "fatigue": {
                "void": 1.4,         # Усталость может привести к пустоте
                "acceptance": 1.3,   # Или принятию
                "confusion": 1.2,    # Или путанице
            },

            "comfort": {
                "connection": 1.3,   # Комфорт способствует связям
                "calm": 1.5,         # И спокойствию
                "acceptance": 1.4,   # И принятию
            },

            # Креативные состояния
            "inspiration": {
                "curiosity": 1.8,    # Вдохновение стимулирует любопытство
                "insight": 1.6,      # И озарения
                "meaning_found": 1.4, # И поиск смысла
                "inspiration": 0.4,   # Редко повторяется подряд
            },

            "creative_dissonance": {
                "confusion": 1.6,    # Творческий тупик приводит к путанице
                "curiosity": 1.5,    # Или любопытству
                "insight": 1.3,      # Иногда к озарению
                "void": 1.2,         # Или пустоте
            },
        }

    def record_event(self, event: Event) -> None:
        """
        Записывает событие в историю для анализа зависимостей.

        Args:
            event: Новое событие для записи
        """
        current_time = time.time()
        self.event_history.append((event, current_time))

        # Очищаем старую историю если превышен размер
        while len(self.event_history) > self.history_size:
            self.event_history.popleft()

    def get_probability_modifiers(self) -> Dict[str, float]:
        """
        Вычисляет модификаторы вероятностей для всех типов событий
        на основе недавней истории.

        Returns:
            Словарь {event_type: probability_modifier}
        """
        if not self.event_history:
            return {}

        modifiers = {}
        current_time = time.time()

        # Обрабатываем последние несколько событий с затуханием по времени
        for i, (event, event_time) in enumerate(reversed(self.event_history)):
            if i >= 5:  # Ограничиваем анализ последними 5 событиями
                break

            # Вычисляем фактор затухания по времени (более старые события меньше влияют)
            time_decay = self.decay_factor ** (current_time - event_time)
            # Вычисляем фактор затухания по позиции (более недавние события больше влияют)
            position_decay = self.decay_factor ** i

            combined_decay = time_decay * position_decay

            # Получаем зависимости для этого типа события
            dependencies = self.dependency_matrix.get(event.type, {})

            for dependent_type, base_modifier in dependencies.items():
                # Применяем затухание
                final_modifier = 1.0 + (base_modifier - 1.0) * combined_decay

                # Накопительный эффект (модификаторы перемножаются)
                if dependent_type in modifiers:
                    modifiers[dependent_type] *= final_modifier
                else:
                    modifiers[dependent_type] = final_modifier

                self.dependency_stats["total_modifications"] += 1

        # Ограничиваем модификаторы разумными пределами
        for event_type in modifiers:
            modifiers[event_type] = max(0.1, min(3.0, modifiers[event_type]))

        return modifiers

    def detect_pattern(self, recent_events: List[Event]) -> Optional[str]:
        """
        Обнаруживает паттерны в последовательности событий.

        Args:
            recent_events: Список последних событий

        Returns:
            Название обнаруженного паттерна или None
        """
        if len(recent_events) < 3:
            return None

        # Преобразуем события в типы для анализа
        event_types = [e.type for e in recent_events[-3:]]

        # Паттерны поиска
        patterns = {
            "confusion_to_insight": ["confusion", "curiosity", "insight"],
            "isolation_to_connection": ["isolation", "curiosity", "connection"],
            "void_to_meaning": ["void", "curiosity", "meaning_found"],
            "learning_cycle": ["confusion", "insight", "curiosity"],
            "social_cycle": ["isolation", "connection", "acceptance"],
            "existential_crisis": ["void", "confusion", "meaning_found"],
        }

        for pattern_name, pattern_sequence in patterns.items():
            if event_types == pattern_sequence:
                self.dependency_stats["patterns_detected"] += 1
                return pattern_name

        return None

    def get_chain_probability(self, event_types: List[str]) -> float:
        """
        Вычисляет вероятность цепочки событий на основе зависимостей.

        Args:
            event_types: Последовательность типов событий

        Returns:
            Вероятность цепочки (0.0-1.0)
        """
        if len(event_types) < 2:
            return 0.5

        probability = 1.0

        for i in range(len(event_types) - 1):
            current_type = event_types[i]
            next_type = event_types[i + 1]

            dependencies = self.dependency_matrix.get(current_type, {})
            modifier = dependencies.get(next_type, 1.0)

            # Нормализуем модификатор в вероятность
            probability *= min(1.0, modifier / 2.0)  # Максимум 50% от базовой

        return probability

    def get_dependency_stats(self) -> Dict:
        """
        Возвращает статистику работы системы зависимостей.

        Returns:
            Статистика зависимостей
        """
        return self.dependency_stats.copy()

    def reset_stats(self) -> None:
        """Сбрасывает статистику зависимостей."""
        self.dependency_stats = {
            "chains_created": 0,
            "patterns_detected": 0,
            "total_modifications": 0
        }