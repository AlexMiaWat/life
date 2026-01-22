import random
import time
import math
from typing import Any, Dict, Optional

from .event import Event
from .memory_echo_selector import MemoryEchoSelector
from src.state.self_state import SelfState
from src.runtime.subjective_time import compute_subjective_time_rate


class InternalEventGenerator:
    """
    Генератор внутренних событий для системы Life.

    Отвечает за генерацию спонтанных внутренних событий,
    таких как memory echoes (всплывания воспоминаний).
    Интегрирует субъективное время и внутренние ритмы для более естественных всплытий.
    """

    def __init__(self, memory_echo_probability: float = 0.02, memory=None):
        """
        Args:
            memory_echo_probability: Базовая вероятность генерации memory_echo события на тик (0.02 = 2%)
            memory: Объект Memory для доступа к архивной памяти (опционально)
        """
        self.memory_echo_probability = memory_echo_probability
        self.memory = memory
        self.echo_selector = MemoryEchoSelector() if memory is not None else None

        # Параметры для спонтанных всплытий
        self.spontaneous_echo_chance = 0.15  # Шанс спонтанного всплытия при подходящих условиях
        self.rhythm_echo_boost = 2.0  # Множитель вероятности во время пиков ритма
        self.low_energy_echo_boost = 1.8  # Множитель при низкой энергии (мечты/размышления)
        self.quiet_period_boost = 1.5  # Множитель в тихие периоды

    def set_memory(self, memory):
        """
        Устанавливает объект памяти для доступа к архивным воспоминаниям.

        Args:
            memory: Объект Memory
        """
        self.memory = memory
        if memory is not None and not self.echo_selector:
            self.echo_selector = MemoryEchoSelector()

    def generate_memory_echo(
        self, context_state: Optional[SelfState] = None, memory_stats: Optional[Dict[str, Any]] = None
    ) -> Optional[Event]:
        """
        Генерирует событие memory_echo на основе состояния памяти с интеграцией субъективного времени.

        Args:
            context_state: Текущее состояние системы для контекстуального выбора воспоминания
            memory_stats: Статистика памяти для выбора воспоминания

        Returns:
            Event или None если событие не сгенерировано
        """
        if not context_state:
            # Fallback к базовой вероятности без контекста
            if random.random() > self.memory_echo_probability:
                return None
            return self._create_basic_echo(memory_stats)

        # Вычисляем модификатор вероятности на основе субъективного времени и ритмов
        probability_modifier = self._calculate_echo_probability_modifier(context_state)
        effective_probability = self.memory_echo_probability * probability_modifier

        # Проверяем эффективную вероятность генерации
        if random.random() > effective_probability:
            return None

        # Создаем базовую metadata
        metadata = {
            "internal": True,
            "source": "spontaneous_recall",
            "subjective_time_integrated": True,
            "probability_modifier": probability_modifier,
        }

        # Если есть память и селектор, пытаемся выбрать конкретное воспоминание
        selected_memory = None
        if self.memory is not None and self.echo_selector:
            selected_memory = self.echo_selector.select_memory_for_echo(self.memory, context_state)

        if selected_memory:
            # Генерируем интенсивность с учетом субъективного времени
            base_intensity = selected_memory.meaning_significance * 0.4  # 0.0 - 0.4

            # Модифицируем интенсивность на основе субъективного темпа времени
            subjective_rate = self._get_current_subjective_rate(context_state)
            intensity_modifier = 0.5 + 0.5 * subjective_rate  # 0.5-1.0 для нормализации
            base_intensity *= intensity_modifier

            intensity = random.uniform(-base_intensity, base_intensity)

            # Вычисляем возраст в днях с учетом субъективного времени
            age_seconds = time.time() - selected_memory.timestamp
            age_days = age_seconds / (24 * 3600)

            # Корректируем воспринимаемый возраст на основе субъективного времени
            perceived_age_days = age_days / subjective_rate

            # Определяем эмоциональный тип на основе event_type
            emotional_impact = self._get_emotional_impact(selected_memory.event_type)

            # Определяем тип всплытия на основе контекста
            echo_trigger_type = self._determine_echo_trigger_type(context_state)

            # Создаем расширенную metadata с данными конкретного воспоминания
            metadata.update({
                "echo_type": "specific_memory",
                "trigger_type": echo_trigger_type,
                "subjective_rate": subjective_rate,
                "original_memory": {
                    "event_type": selected_memory.event_type,
                    "meaning_significance": selected_memory.meaning_significance,
                    "timestamp": selected_memory.timestamp,
                    "subjective_timestamp": selected_memory.subjective_timestamp,
                    "weight": selected_memory.weight,
                    "age_days": age_days,
                    "perceived_age_days": perceived_age_days,
                    "emotional_impact": emotional_impact,
                }
            })
        else:
            # Fallback к абстрактному эхо при отсутствии воспоминаний
            intensity = random.uniform(-0.2, 0.2)
            # Определяем причину отсутствия конкретного воспоминания
            if self.memory is None:
                reason = "no_memory_access"
            elif not self.memory.get_archived_entries():
                reason = "no_archived_memories"
            else:
                reason = "selector_failed"  # MemoryEchoSelector не смог выбрать

            metadata.update({
                "echo_type": "abstract_memory",
                "reason": reason
            })

        # Если есть статистика памяти, добавляем дополнительную информацию
        if memory_stats:
            metadata.update(
                {
                    "memory_active_count": memory_stats.get("active_entries", 0),
                    "memory_archive_count": memory_stats.get("archive_entries", 0),
                    "memory_event_types": memory_stats.get("event_types", []),
                }
            )

        return Event(
            type="memory_echo",
            intensity=intensity,
            timestamp=time.time(),
            metadata=metadata,
        )

    def _calculate_echo_probability_modifier(self, context_state: SelfState) -> float:
        """
        Вычисляет модификатор вероятности всплытия воспоминаний на основе контекста.

        Args:
            context_state: Текущее состояние системы

        Returns:
            Модификатор вероятности (>= 1.0)
        """
        modifier = 1.0

        # Модификатор на основе циркадного ритма (пики воспоминаний)
        circadian_modifier = self._get_circadian_echo_modifier(context_state)
        modifier *= circadian_modifier

        # Модификатор на основе энергии (при низкой энергии чаще мечты/размышления)
        if context_state.energy < 40.0:
            modifier *= self.low_energy_echo_boost

        # Модификатор на основе стабильности (при низкой стабильности - больше размышлений)
        if context_state.stability < 0.4:
            modifier *= 1.3

        # Модификатор на основе активности (в тихие периоды чаще воспоминания)
        recent_activity = len(context_state.recent_events) if hasattr(context_state, 'recent_events') else 0
        if recent_activity < 2:  # Мало недавней активности
            modifier *= self.quiet_period_boost

        # Модификатор на основе субъективного темпа времени (при замедленном времени чаще воспоминания)
        subjective_rate = self._get_current_subjective_rate(context_state)
        if subjective_rate < 0.8:  # Замедленное субъективное время
            modifier *= 1.4

        return modifier

    def _get_circadian_echo_modifier(self, context_state: SelfState) -> float:
        """
        Вычисляет модификатор на основе циркадного ритма.

        Вспоминания чаще происходят в определенные фазы суточного цикла:
        - Раннее утро (после сна) - пики воспоминаний
        - Вечер (перед сном) - размышления о прошедшем дне
        - Ночь - сны и глубокие воспоминания

        Args:
            context_state: Текущее состояние

        Returns:
            Модификатор вероятности
        """
        if not hasattr(context_state, 'circadian_phase'):
            return 1.0

        phase = context_state.circadian_phase  # 0.0-1.0 (0 = полночь, 0.5 = полдень)

        # Пиковые периоды для воспоминаний:
        # 1. Раннее утро (5-8 часов): phase ≈ 0.2-0.33
        # 2. Вечер (18-22 часов): phase ≈ 0.75-0.92
        # 3. Глубокая ночь (22-4 часов): phase ≈ 0.92-1.0 и 0.0-0.17

        if 0.2 <= phase <= 0.33:  # Раннее утро
            return self.rhythm_echo_boost
        elif 0.75 <= phase <= 0.92:  # Вечер
            return self.rhythm_echo_boost * 0.8
        elif phase >= 0.92 or phase <= 0.17:  # Глубокая ночь
            return self.rhythm_echo_boost * 1.2
        else:
            return 1.0

    def _get_current_subjective_rate(self, context_state: SelfState) -> float:
        """
        Вычисляет текущий субъективный темп времени.

        Args:
            context_state: Текущее состояние

        Returns:
            Субъективный темп времени (0.0-2.0+)
        """
        try:
            return compute_subjective_time_rate(
                base_rate=getattr(context_state, 'subjective_time_base_rate', 1.0),
                intensity=getattr(context_state, 'last_event_intensity', 0.0),
                stability=context_state.stability,
                energy=context_state.energy,
                intensity_coeff=getattr(context_state, 'subjective_time_intensity_coeff', 0.5),
                stability_coeff=getattr(context_state, 'subjective_time_stability_coeff', -0.3),
                energy_coeff=getattr(context_state, 'subjective_time_energy_coeff', 0.2),
                rate_min=getattr(context_state, 'subjective_time_rate_min', 0.1),
                rate_max=getattr(context_state, 'subjective_time_rate_max', 3.0),
            )
        except Exception:
            # Fallback в случае ошибки
            return 1.0

    def _determine_echo_trigger_type(self, context_state: SelfState) -> str:
        """
        Определяет тип триггера всплытия воспоминания на основе контекста.

        Args:
            context_state: Текущее состояние

        Returns:
            Тип триггера: "circadian_peak", "low_energy", "quiet_reflection", "stability_disturbance", "normal_spontaneous"
        """
        # Проверяем циркадный пик
        circadian_mod = self._get_circadian_echo_modifier(context_state)
        if circadian_mod > 1.5:
            return "circadian_peak"

        # Проверяем низкую энергию
        if context_state.energy < 40.0:
            return "low_energy"

        # Проверяем тихий период
        recent_activity = len(context_state.recent_events) if hasattr(context_state, 'recent_events') else 0
        if recent_activity < 2:
            return "quiet_reflection"

        # Проверяем низкую стабильность
        if context_state.stability < 0.4:
            return "stability_disturbance"

        # Нормальное спонтанное всплытие
        return "normal_spontaneous"

    def _create_basic_echo(self, memory_stats: Optional[Dict[str, Any]] = None) -> Event:
        """
        Создает базовое echo событие без контекста состояния.

        Args:
            memory_stats: Статистика памяти

        Returns:
            Базовое Event echo
        """
        metadata = {
            "internal": True,
            "source": "basic_fallback",
            "echo_type": "abstract_memory",
            "reason": "no_context_state"
        }

        if memory_stats:
            metadata.update({
                "memory_active_count": memory_stats.get("active_entries", 0),
                "memory_archive_count": memory_stats.get("archive_entries", 0),
                "memory_event_types": memory_stats.get("event_types", []),
            })

        return Event(
            type="memory_echo",
            intensity=random.uniform(-0.1, 0.1),
            timestamp=time.time(),
            metadata=metadata,
        )

    def should_generate_echo(self, ticks_since_last_echo: int, memory_pressure: float, context_state: Optional[SelfState] = None) -> bool:
        """
        Определяет, следует ли генерировать memory echo на основе контекста.

        Args:
            ticks_since_last_echo: Тиков с момента последнего echo
            memory_pressure: Давление памяти (0.0 - 1.0, где 1.0 = память полна)
            context_state: Текущее состояние для расчета модификаторов

        Returns:
            True если следует генерировать echo
        """
        # Базовая вероятность
        base_prob = self.memory_echo_probability

        # Увеличиваем вероятность если давно не было echo
        if ticks_since_last_echo > 50:  # Каждые ~50 тиков минимум
            base_prob *= 2.0

        # Увеличиваем вероятность при высоком давлении памяти
        if memory_pressure > 0.8:  # Память почти полна
            base_prob *= 1.5

        # Применяем модификаторы на основе состояния (если доступно)
        if context_state:
            probability_modifier = self._calculate_echo_probability_modifier(context_state)
            base_prob *= probability_modifier

        return random.random() < base_prob

    def _get_emotional_impact(self, event_type: str) -> str:
        """
        Определяет эмоциональный тип события для metadata.

        Args:
            event_type: Тип события

        Returns:
            "positive", "negative" или "neutral"
        """
        positive_events = {"recovery", "social_harmony", "learning_achievement"}
        negative_events = {"shock", "decay", "crisis", "disruption"}

        if event_type in positive_events:
            return "positive"
        elif event_type in negative_events:
            return "negative"
        else:
            return "neutral"
