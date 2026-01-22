"""
Memory Echo Selector - компонент для интеллектуального выбора воспоминаний для эхо-всплываний.

Отвечает за выбор конкретных воспоминаний из архивной памяти на основе:
- Возраста воспоминания (>7 дней предпочтительнее)
- Значимости события (более значимые чаще всплывают)
- Типа события (эмоциональные предпочтительнее нейтральных)
- Текущего контекста состояния (при низкой стабильности - тревожные воспоминания)
"""

import random
import time
import math
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from src.memory.memory import Memory
from src.memory.memory_types import MemoryEntry
from src.state.self_state import SelfState
from src.runtime.subjective_time import compute_subjective_time_rate


@dataclass
class EchoCandidate:
    """
    Кандидат для эхо-всплывания с вычисленным весом.

    Attributes:
        memory_entry: Запись памяти
        weight: Вычисленный вес для выбора
        age_days: Возраст в днях
        emotional_intensity: Эмоциональная интенсивность (0.0-1.0)
        contextual_modifier: Модификатор контекста
        subjective_time_modifier: Модификатор субъективного времени
        subjective_age: Реальный субъективный возраст воспоминания (в единицах субъективного времени)
    """
    memory_entry: MemoryEntry
    weight: float
    age_days: float
    emotional_intensity: float
    contextual_modifier: float
    subjective_time_modifier: float = 1.0
    subjective_age: float = 0.0


class MemoryEchoSelector:
    """
    Селектор воспоминаний для эхо-всплываний.

    Реализует вероятностную логику выбора воспоминаний на основе
    множественных факторов: возраст, значимость, тип события, контекст состояния.
    """

    def __init__(self):
        """Инициализация селектора"""
        # Параметры для расчета весов
        self.age_preference_threshold_days = 7.0  # Возраст >7 дней предпочтительнее
        self.max_age_days = 365.0  # Максимальный возраст для учета (1 год)

        # Весовые коэффициенты для разных факторов
        self.age_weight = 0.3
        self.significance_weight = 0.4
        self.emotional_weight = 0.2
        self.contextual_weight = 0.1
        self.subjective_time_weight = 0.2  # Вес для субъективного времени

        # Параметры кэширования для оптимизации производительности
        self._candidates_cache: Optional[List[EchoCandidate]] = None
        self._cache_timestamp: float = 0.0
        self._cache_ttl_seconds = 60.0  # Время жизни кэша в секундах

        # Мэппинг типов событий к эмоциональной интенсивности
        self.emotional_mapping = {
            # Позитивные события
            "recovery": 0.8,
            "social_harmony": 0.7,
            "learning_achievement": 0.6,

            # Негативные события
            "shock": 0.9,
            "decay": 0.7,
            "crisis": 0.8,
            "disruption": 0.6,

            # Нейтральные события
            "idle": 0.1,
            "noise": 0.2,
            "adaptation": 0.3,
            "routine": 0.2,
        }

    def select_memory_for_echo(self, memory: Memory, context_state: SelfState) -> Optional[MemoryEntry]:
        """
        Выбирает воспоминание для эхо-всплывания на основе контекста состояния.

        Args:
            memory: Объект памяти с доступом к архиву
            context_state: Текущее состояние системы для контекстуального выбора

        Returns:
            MemoryEntry или None, если подходящих воспоминаний нет
        """
        # Получаем кандидатов (с использованием кэша)
        candidates = self._get_echo_candidates(memory, context_state)

        if not candidates:
            return None

        # Взвешенный случайный выбор
        return self._weighted_random_selection(candidates)

    def _get_echo_candidates(self, memory: Memory, context_state: SelfState) -> List[EchoCandidate]:
        """
        Получает список кандидатов для эхо с вычисленными весами.

        Использует кэширование для оптимизации производительности.
        """
        current_time = time.time()

        # Проверяем актуальность кэша
        if (self._candidates_cache is not None and
            current_time - self._cache_timestamp < self._cache_ttl_seconds):
            return self._candidates_cache

        # Получаем все записи из архива
        archived_entries = memory.get_archived_entries()

        if not archived_entries:
            self._candidates_cache = []
            self._cache_timestamp = current_time
            return []

        # Создаем кандидатов с вычисленными весами
        candidates = []
        for entry in archived_entries:
            candidate = self._create_echo_candidate(entry, context_state, current_time)
            if candidate.weight > 0:  # Только кандидаты с положительным весом
                candidates.append(candidate)

        # Сортируем по весу для оптимизации выбора
        candidates.sort(key=lambda c: c.weight, reverse=True)

        # Кэшируем результат
        self._candidates_cache = candidates
        self._cache_timestamp = current_time

        return candidates

    def _create_echo_candidate(self, entry: MemoryEntry, context_state: SelfState, current_time: float) -> EchoCandidate:
        """
        Создает кандидата для эхо с вычисленным весом, включая субъективное время.

        Args:
            entry: Запись памяти
            context_state: Текущее состояние
            current_time: Текущее время для расчета возраста

        Returns:
            EchoCandidate с вычисленными параметрами
        """
        # Вычисляем возраст в днях
        age_seconds = current_time - entry.timestamp
        age_days = age_seconds / (24 * 3600)

        # Вычисляем субъективный темп времени для контекста
        subjective_rate = self._calculate_current_subjective_rate(context_state)

        # Вычисляем реальный субъективный возраст воспоминания
        subjective_age = 0.0
        if hasattr(entry, 'subjective_timestamp') and entry.subjective_timestamp is not None:
            subjective_age = context_state.subjective_time - entry.subjective_timestamp

        # Вычисляем воспринимаемый возраст для обратной совместимости (будет удален)
        perceived_age_days = age_days / subjective_rate if subjective_rate > 0 else age_days

        # Вычисляем компоненты веса
        age_weight = self._calculate_age_weight(age_days, subjective_age if subjective_age > 0 else perceived_age_days)
        significance_weight = entry.meaning_significance
        emotional_intensity = self._get_emotional_intensity(entry.event_type)
        contextual_modifier = self._calculate_contextual_modifier(entry.event_type, context_state)
        subjective_time_modifier = self._calculate_subjective_time_modifier(entry, context_state, subjective_rate, subjective_age if subjective_age > 0 else perceived_age_days)

        # Общий вес как взвешенная сумма компонентов
        total_weight = (
            self.age_weight * age_weight +
            self.significance_weight * significance_weight +
            self.emotional_weight * emotional_intensity +
            self.contextual_weight * contextual_modifier +
            self.subjective_time_weight * subjective_time_modifier
        )

        return EchoCandidate(
            memory_entry=entry,
            weight=max(0.0, total_weight),  # Гарантируем неотрицательный вес
            age_days=age_days,
            emotional_intensity=emotional_intensity,
            contextual_modifier=contextual_modifier,
            subjective_time_modifier=subjective_time_modifier,
            subjective_age=subjective_age
        )

    def _calculate_age_weight(self, age_days: float, subjective_age: Optional[float] = None) -> float:
        """
        Вычисляет вес на основе возраста воспоминания.

        Воспоминания старше определенного субъективного возраста получают более высокий вес,
        но слишком старые получают пониженный вес.
        Использует реальный субъективный возраст воспоминания.

        Args:
            age_days: Хронологический возраст в днях (для обратной совместимости)
            subjective_age: Реальный субъективный возраст воспоминания (в единицах субъективного времени)

        Returns:
            Вес от 0.0 до 1.0
        """
        # Используем субъективный возраст если доступен, иначе хронологический
        effective_age = subjective_age if subjective_age is not None and subjective_age > 0 else age_days

        # Конвертируем субъективный возраст в "эквивалент дней" для порогов
        # Предполагаем, что 100 единиц субъективного времени ≈ 1 дню
        effective_age_days = effective_age / 100.0 if subjective_age is not None and subjective_age > 0 else effective_age

        if effective_age_days < 1.0:
            # Совсем свежие воспоминания получают низкий вес
            return 0.1
        elif effective_age_days < self.age_preference_threshold_days:
            # Воспоминания 1-7 дней получают средний вес
            return 0.5
        elif effective_age_days < self.max_age_days:
            # Воспоминания 7 дней - 1 год получают высокий вес
            # Легкое затухание с возрастом
            age_factor = 1.0 - (effective_age_days - self.age_preference_threshold_days) / (self.max_age_days - self.age_preference_threshold_days)
            return 0.8 + 0.2 * age_factor
        else:
            # Слишком старые воспоминания получают низкий вес
            return 0.2

    def _get_emotional_intensity(self, event_type: str) -> float:
        """
        Определяет эмоциональную интенсивность типа события.

        Args:
            event_type: Тип события

        Returns:
            Эмоциональная интенсивность от 0.0 до 1.0
        """
        return self.emotional_mapping.get(event_type, 0.3)  # Значение по умолчанию для неизвестных типов

    def _calculate_contextual_modifier(self, event_type: str, context_state: SelfState) -> float:
        """
        Вычисляет контекстуальный модификатор на основе текущего состояния и циркадных ритмов.

        При низкой стабильности предпочитает воспоминания, которые могут помочь:
        - При низкой стабильности: позитивные воспоминания получают бонус
        - При высокой усталости: успокаивающие воспоминания
        - При высоком напряжении: отвлекающие воспоминания
        - Учитывает циркадные ритмы для более естественных всплытий

        Args:
            event_type: Тип события
            context_state: Текущее состояние

        Returns:
            Модификатор веса от -0.5 до 0.5
        """
        modifier = 0.0

        # Модификатор стабильности
        stability_modifier = self._get_stability_modifier(event_type, context_state.stability)
        modifier += stability_modifier

        # Модификатор энергии/усталости
        energy_modifier = self._get_energy_modifier(event_type, context_state.energy, context_state.fatigue)
        modifier += energy_modifier * 0.3  # Меньший вес

        # Модификатор напряжения
        tension_modifier = self._get_tension_modifier(event_type, context_state.tension)
        modifier += tension_modifier * 0.2  # Еще меньший вес

        # Модификатор циркадного ритма
        circadian_modifier = self._get_circadian_memory_modifier(event_type, context_state)
        modifier += circadian_modifier * 0.4  # Значительный вес для ритма

        # Ограничиваем диапазон
        return max(-0.5, min(0.5, modifier))

    def _get_stability_modifier(self, event_type: str, stability: float) -> float:
        """
        Модификатор на основе стабильности состояния.

        Args:
            event_type: Тип события
            stability: Текущая стабильность (0.0-1.0)

        Returns:
            Модификатор веса
        """
        if stability < 0.3:  # Низкая стабильность
            # Предпочитаем позитивные воспоминания для поднятия настроения
            if event_type in ["recovery", "social_harmony", "learning_achievement"]:
                return 0.4
            elif event_type in ["shock", "decay", "crisis"]:
                return -0.3  # Избегаем негативных воспоминаний
        elif stability > 0.8:  # Высокая стабильность
            # Можно позволить более разнообразные воспоминания
            return 0.0
        else:
            # Средняя стабильность - нейтральный модификатор
            return 0.0

        return 0.0

    def _get_energy_modifier(self, event_type: str, energy: float, fatigue: float) -> float:
        """
        Модификатор на основе уровня энергии и усталости.

        Args:
            event_type: Тип события
            energy: Текущая энергия (0-100)
            fatigue: Текущая усталость (0+)

        Returns:
            Модификатор веса
        """
        # При низкой энергии предпочитаем энергизующие воспоминания
        if energy < 30.0 and event_type in ["recovery", "learning_achievement"]:
            return 0.3

        # При высокой усталости предпочитаем успокаивающие воспоминания
        if fatigue > 0.7 and event_type in ["social_harmony", "idle"]:
            return 0.2

        return 0.0

    def _get_tension_modifier(self, event_type: str, tension: float) -> float:
        """
        Модификатор на основе уровня напряжения.

        Args:
            event_type: Тип события
            tension: Текущее напряжение (0+)

        Returns:
            Модификатор веса
        """
        # При высоком напряжении предпочитаем отвлекающие воспоминания
        if tension > 0.6 and event_type in ["learning_achievement", "social_harmony"]:
            return 0.2

        # При низком напряжении можно позволить более интенсивные воспоминания
        if tension < 0.2 and event_type in ["shock", "crisis"]:
            return 0.1

        return 0.0

    def _get_circadian_memory_modifier(self, event_type: str, context_state: SelfState) -> float:
        """
        Вычисляет модификатор на основе циркадного ритма для типа воспоминания.

        Разные типы воспоминаний более естественны в разные периоды суток:
        - Утро: воспоминания о целях, достижениях
        - День: нейтральные воспоминания
        - Вечер: размышления о прошедшем дне
        - Ночь: глубокие эмоциональные воспоминания

        Args:
            event_type: Тип события воспоминания
            context_state: Текущее состояние

        Returns:
            Модификатор веса
        """
        if not hasattr(context_state, 'circadian_phase'):
            return 0.0

        phase = context_state.circadian_phase

        # Определяем период суток
        if 0.2 <= phase <= 0.33:  # Раннее утро (5-8 часов)
            # Предпочитаем мотивирующие воспоминания
            if event_type in ["recovery", "learning_achievement", "social_harmony"]:
                return 0.3
            elif event_type in ["shock", "decay"]:
                return -0.2  # Избегаем негативных утром

        elif 0.75 <= phase <= 0.92:  # Вечер (18-22 часов)
            # Предпочитаем размышления о прошедшем дне
            if event_type in ["idle", "adaptation", "routine"]:
                return 0.25
            # Меньше шоковых воспоминаний вечером
            elif event_type in ["shock", "crisis"]:
                return -0.15

        elif phase >= 0.92 or phase <= 0.17:  # Ночь (22-4 часов)
            # Глубокие эмоциональные воспоминания
            if event_type in ["shock", "crisis", "social_harmony"]:
                return 0.4
            # Нейтральные воспоминания получают небольшой бонус ночью
            elif event_type in ["idle", "noise"]:
                return 0.15

        # Для дневного периода (остальное время) - нейтральный модификатор
        return 0.0

    def _weighted_random_selection(self, candidates: List[EchoCandidate]) -> Optional[MemoryEntry]:
        """
        Выполняет взвешенный случайный выбор из кандидатов.

        Args:
            candidates: Список кандидатов с весами

        Returns:
            Выбранная запись памяти или None
        """
        if not candidates:
            return None

        # Извлекаем веса
        weights = [candidate.weight for candidate in candidates]

        # Нормализуем веса
        total_weight = sum(weights)
        if total_weight == 0:
            # Если все веса нулевые, выбираем случайно
            return random.choice(candidates).memory_entry

        # Взвешенный случайный выбор
        r = random.uniform(0, total_weight)
        cumulative = 0.0

        for candidate, weight in zip(candidates, weights):
            cumulative += weight
            if r <= cumulative:
                return candidate.memory_entry

        # Fallback (не должно происходить)
        return candidates[-1].memory_entry

    def _calculate_current_subjective_rate(self, context_state: SelfState) -> float:
        """
        Вычисляет текущий субъективный темп времени.

        Args:
            context_state: Текущее состояние

        Returns:
            Субъективный темп времени
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
            return 1.0

    def _calculate_subjective_time_modifier(self, entry: MemoryEntry, context_state: SelfState, subjective_rate: float, subjective_age: float) -> float:
        """
        Вычисляет модификатор веса на основе субъективного времени.

        Args:
            entry: Запись памяти
            context_state: Текущее состояние
            subjective_rate: Текущий субъективный темп времени
            subjective_age: Реальный субъективный возраст воспоминания

        Returns:
            Модификатор веса (-0.5 до 0.5)
        """
        modifier = 0.0

        # Конвертируем субъективный возраст в дни для сравнения с порогами
        subjective_age_days = subjective_age / 100.0 if subjective_age > 0 else 0

        # Модификатор на основе субъективного темпа времени
        if subjective_rate < 0.7:  # Замедленное субъективное время
            # При замедленном времени чаще всплывают глубокие воспоминания
            if subjective_age_days > 30:  # Старые воспоминания
                modifier += 0.3
        elif subjective_rate > 1.5:  # Ускоренное субъективное время
            # При ускоренном времени - свежие воспоминания
            if subjective_age_days < 7:  # Недавние воспоминания
                modifier += 0.2

        # Модификатор на основе субъективной временной метки записи
        if subjective_age > 0:
            # Нормализуем возраст (старше 1000 единиц субъективного времени = 1.0)
            normalized_subjective_age = min(1.0, subjective_age / 1000.0)
            # Предпочитаем воспоминания, субъективно не слишком старые и не слишком свежие
            if 0.1 <= normalized_subjective_age <= 0.8:
                modifier += 0.2

        # Модификатор на основе циркадного ритма и субъективного времени
        if hasattr(context_state, 'circadian_phase'):
            phase = context_state.circadian_phase
            # Ночью субъективное время часто замедляется, способствуя глубоким воспоминаниям
            if (phase >= 0.92 or phase <= 0.17) and subjective_rate < 0.8:
                if entry.meaning_significance > 0.5:  # Значимые воспоминания
                    modifier += 0.3

        return max(-0.5, min(0.5, modifier))

    def get_statistics(self) -> Dict[str, Any]:
        """
        Возвращает статистику работы селектора.

        Returns:
            Словарь со статистикой
        """
        if self._candidates_cache is None:
            return {"candidates_count": 0, "cache_age_seconds": 0}

        cache_age = time.time() - self._cache_timestamp

        return {
            "candidates_count": len(self._candidates_cache),
            "cache_age_seconds": cache_age,
            "total_weights_sum": sum(c.weight for c in self._candidates_cache) if self._candidates_cache else 0,
            "avg_weight": sum(c.weight for c in self._candidates_cache) / len(self._candidates_cache) if self._candidates_cache else 0,
        }