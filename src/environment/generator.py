import random
import time
from typing import Any, Optional

from .event import Event
from .event_dependency_manager import EventDependencyManager
from .environment_config import EnvironmentConfigManager


class EventGenerator:
    def __init__(self):
        """Инициализация генератора с системой зависимостей событий."""
        self.dependency_manager = EventDependencyManager()
        self.config_manager = EnvironmentConfigManager()

    def generate(self) -> Event:
        """
        Генерирует событие согласно спецификации этапа 07.

        Диапазоны интенсивности:
        - noise: [-0.3, 0.3]
        - decay: [-0.5, 0.0]
        - recovery: [0.0, 0.5]
        - shock: [-1.0, 1.0]
        - idle: 0.0
        - memory_echo: [-0.2, 0.2] (внутренняя генерация)
        - social_presence: [-0.4, 0.4] (социальное присутствие)
        - social_conflict: [-0.6, 0.0] (социальный конфликт)
        - social_harmony: [0.0, 0.6] (социальная гармония)
        - cognitive_doubt: [-0.5, 0.0] (когнитивное сомнение)
        - cognitive_clarity: [0.0, 0.5] (когнитивная ясность)
        - cognitive_confusion: [-0.4, 0.0] (когнитивная путаница)
        - existential_void: [-0.7, 0.0] (экзистенциальная пустота)
        - existential_purpose: [0.0, 0.7] (экзистенциальное ощущение цели)
        - existential_finitude: [-0.6, 0.0] (осознание конечности)
        - connection: [0.0, 0.8] (ощущение связи с другими)
        - isolation: [-0.7, 0.0] (ощущение изоляции, одиночества)
        - insight: [0.0, 0.6] (момент озарения, понимания)
        - confusion: [-0.5, 0.0] (состояние замешательства, непонимания)
        - curiosity: [-0.3, 0.4] (интерес, желание узнать больше)
        - meaning_found: [0.0, 0.9] (ощущение нахождения смысла)
        - void: [-0.8, 0.0] (ощущение пустоты, отсутствия содержания)
        - acceptance: [0.0, 0.5] (принятие текущего состояния)
        - silence: [-0.4, 0.6] (осознание тишины - комфортная или тревожная)
        - joy: [0.0, 0.8] (радость, положительное эмоциональное состояние)
        - sadness: [-0.7, 0.0] (грусть, печаль)
        - fear: [-0.8, 0.0] (страх, тревога)
        - calm: [0.0, 0.6] (спокойствие, умиротворение)
        - discomfort: [-0.6, 0.0] (физический дискомфорт)
        - comfort: [0.0, 0.7] (физический комфорт)
        - fatigue: [-0.5, 0.0] (усталость, истощение)
        - anticipation: [-0.3, 0.5] (ожидание - может быть положительным или отрицательным)
        - boredom: [-0.4, 0.0] (скука, отсутствие стимуляции)
        - inspiration: [0.0, 0.9] (вдохновение, творческий подъем)
        - creative_dissonance: [-0.5, 0.0] (творческий тупик, отсутствие идей)
        """
        types = [
            "noise",
            "decay",
            "recovery",
            "shock",
            "idle",
            "memory_echo",
            "social_presence",
            "social_conflict",
            "social_harmony",
            "cognitive_doubt",
            "cognitive_clarity",
            "cognitive_confusion",
            "existential_void",
            "existential_purpose",
            "existential_finitude",
            "connection",
            "isolation",
            "insight",
            "confusion",
            "curiosity",
            "meaning_found",
            "void",
            "acceptance",
            "silence",
            "joy",
            "sadness",
            "fear",
            "calm",
            "discomfort",
            "comfort",
            "fatigue",
            "anticipation",
            "boredom",
            "inspiration",
            "creative_dissonance",
        ]
        # Базовые веса событий
        base_weights = [
            0.250,  # noise (скорректирован для новых типов)
            0.180,  # decay (скорректирован для новых типов)
            0.130,  # recovery (скорректирован для новых типов)
            0.030,  # shock (скорректирован для новых типов)
            0.030,  # idle (скорректирован для новых типов)
            0.0,  # memory_echo (генерируется только внутренне)
            0.010,  # social_presence (скорректирован для новых типов)
            0.006,  # social_conflict (скорректирован для новых типов)
            0.006,  # social_harmony (скорректирован для новых типов)
            0.010,  # cognitive_doubt (скорректирован для новых типов)
            0.006,  # cognitive_clarity (скорректирован для новых типов)
            0.010,  # cognitive_confusion (скорректирован для новых типов)
            0.005,  # existential_void (скорректирован для новых типов)
            0.004,  # existential_purpose (скорректирован для новых типов)
            0.006,  # existential_finitude (скорректирован для новых типов)
            0.025,  # connection (увеличен для социальных и экзистенциальных типов - 14.3% от потока)
            0.020,  # isolation (увеличен для социальных и экзистенциальных типов - 14.3% от потока)
            0.018,  # insight (увеличен для социальных и экзистенциальных типов - 14.3% от потока)
            0.022,  # confusion (увеличен для социальных и экзистенциальных типов - 14.3% от потока)
            0.019,  # curiosity (увеличен для социальных и экзистенциальных типов - 14.3% от потока)
            0.015,  # meaning_found (увеличен для социальных и экзистенциальных типов - 14.3% от потока)
            0.012,  # void (увеличен для социальных и экзистенциальных типов - 14.3% от потока)
            0.012,  # acceptance (увеличен для социальных и экзистенциальных типов - 14.3% от потока)
            0.003,  # silence (низкая вероятность, генерируется преимущественно детектором)
            0.015,  # joy (новый тип)
            0.012,  # sadness (новый тип)
            0.010,  # fear (новый тип)
            0.016,  # calm (новый тип)
            0.012,  # discomfort (новый тип)
            0.015,  # comfort (новый тип)
            0.014,  # fatigue (новый тип)
            0.013,  # anticipation (новый тип)
            0.011,  # boredom (новый тип)
            0.017,  # inspiration (новый тип)
            0.010,  # creative_dissonance (новый тип)
        ]

        # Получаем модификаторы вероятностей от менеджера зависимостей
        probability_modifiers = self.dependency_manager.get_probability_modifiers()

        # Применяем модификаторы к базовым весам
        adjusted_weights = []
        for i, base_weight in enumerate(base_weights):
            event_type = types[i]
            modifier = probability_modifiers.get(event_type, 1.0)
            adjusted_weight = base_weight * modifier
            adjusted_weights.append(adjusted_weight)

        # Нормализуем веса чтобы сумма была равна сумме базовых весов
        total_base = sum(base_weights)
        total_adjusted = sum(adjusted_weights)
        if total_adjusted > 0:
            normalization_factor = total_base / total_adjusted
            adjusted_weights = [w * normalization_factor for w in adjusted_weights]

        event_type = random.choices(types, weights=adjusted_weights)[0]

        # Генерируем базовую интенсивность согласно спецификации
        base_intensity = self._generate_base_intensity(event_type)

        # Применяем адаптивные модификаторы интенсивности
        # (пока базовая логика - в будущем можно интегрировать состояние Life)
        intensity = self._adapt_intensity(event_type, base_intensity, context_state=None)

        timestamp = time.time()
        metadata: dict[str, Any] = {}

        # Создаем событие
        event = Event(type=event_type, intensity=intensity, timestamp=timestamp, metadata=metadata)

        # Записываем событие в менеджер зависимостей для будущих модификаций
        self.dependency_manager.record_event(event)

        return event

    def _generate_base_intensity(self, event_type: str) -> float:
        """
        Генерирует базовую интенсивность для типа события на основе конфигурации.

        Args:
            event_type: Тип события

        Returns:
            Базовая интенсивность события
        """
        # Получаем диапазон интенсивности из конфигурации
        config = self.config_manager.get_config()
        min_intensity, max_intensity = config.get_intensity_range(event_type)

        # Генерируем случайную интенсивность в диапазоне
        if min_intensity == max_intensity:
            return min_intensity  # Для событий с фиксированной интенсивностью (например, idle)
        else:
            return random.uniform(min_intensity, max_intensity)

    def _adapt_intensity(self, event_type: str, base_intensity: float, context_state: Optional[Any] = None) -> float:
        """
        Адаптирует интенсивность события на основе контекста и ограничивает диапазоном.

        Args:
            event_type: Тип события
            base_intensity: Базовая интенсивность
            context_state: Контекстное состояние (опционально, для будущей интеграции)

        Returns:
            Адаптированная интенсивность, ограниченная диапазоном типа события
        """
        # Пока простая адаптация на основе паттернов зависимостей
        # В будущем можно интегрировать:
        # - Состояние energy/stability/integrity системы Life
        # - Недавнюю историю событий
        # - Циркадные ритмы

        modifier = 1.0

        # Увеличиваем интенсивность событий, которые часто генерируются по зависимостям
        dependency_modifiers = self.dependency_manager.get_probability_modifiers()

        if event_type in dependency_modifiers:
            dep_modifier = dependency_modifiers[event_type]
            # Преобразуем модификатор вероятности в модификатор интенсивности
            # Если событие более вероятно, оно может быть менее интенсивным (нормализация)
            # Если событие менее вероятно, оно может быть более интенсивным (усиление)
            intensity_modifier = 1.0 + (1.0 - dep_modifier) * 0.3  # 0.7-1.3 диапазон
            modifier *= intensity_modifier

        # Специальные правила для новых социальных и экзистенциальных событий
        if event_type in ["connection", "isolation", "insight", "confusion", "curiosity", "meaning_found", "void", "acceptance"]:
            # Эти события могут быть более интенсивными в определенных контекстах
            # Пока базовая логика - в будущем можно улучшить
            if event_type in ["meaning_found", "insight"]:
                # Значимые события могут быть немного интенсивнее
                modifier *= 1.1
            elif event_type in ["void", "isolation"]:
                # Негативные экзистенциальные события могут быть интенсивнее
                modifier *= 1.05

        adapted_intensity = base_intensity * modifier

        # Ограничиваем результат диапазоном типа события
        config = self.config_manager.get_config()
        min_intensity, max_intensity = config.get_intensity_range(event_type)

        return max(min_intensity, min(max_intensity, adapted_intensity))

    def get_dependency_stats(self) -> dict[str, Any]:
        """
        Получить статистику работы системы зависимостей событий.

        Returns:
            Статистика зависимостей
        """
        return self.dependency_manager.get_dependency_stats()

    def reset_dependency_stats(self) -> None:
        """
        Сбросить статистику зависимостей событий.
        """
        self.dependency_manager.reset_stats()
