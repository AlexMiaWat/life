import time
from typing import Any, Dict, List, Optional

from ..state.self_state import SelfState
from ..utils.performance_monitor import performance_monitor
from .intensity_adapter_interface import IntensityAdapterInterface, IntensityModifier
from .smoothing_engine_interface import SmoothingEngineInterface


class IntensityAdapter(IntensityAdapterInterface):
    """
    Адаптер интенсивности событий на основе состояния Life и паттернов.

    Отвечает за модификацию базовой интенсивности события с учетом:
    - состояния системы Life (энергия, стабильность, целостность)
    - паттернов событий
    - циркадного ритма
    - субъективного времени
    - категорийных правил
    """

    def __init__(self, smoothing_engine: Optional[SmoothingEngineInterface] = None):
        """Инициализация адаптера интенсивности."""
        # Используем внешний SmoothingEngine или создаем свой
        self.smoothing_engine = smoothing_engine or SmoothingEngine()

        # Кэши для оптимизации производительности
        self._state_modifier_cache: Dict[tuple, float] = {}
        self._category_modifier_cache: Dict[tuple, float] = {}
        self._subjective_time_cache: Dict[tuple, float] = {}
        self._cache_timestamp = 0.0
        self._cache_ttl = 1.0  # TTL кэша в секундах

    def adapt_intensity(self, event_type: str, base_intensity: float,
                       context_state: Optional[SelfState] = None,
                       pattern_modifier: float = 1.0,
                       dependency_modifier: float = 1.0) -> float:
        """
        Адаптирует интенсивность события на основе всех факторов.
        Оптимизированная версия с кэшированием, fast path и мониторингом производительности.

        Args:
            event_type: Тип события
            base_intensity: Базовая интенсивность
            context_state: Текущее состояние системы Life
            pattern_modifier: Модификатор на основе паттернов
            dependency_modifier: Модификатор на основе зависимостей

        Returns:
            Адаптированная интенсивность
        """
        with performance_monitor.measure("intensity_adapter.adapt_intensity"):
            # Fast path: если нет состояния и стандартные модификаторы, возвращаем базовую интенсивность
            if (context_state is None and
                pattern_modifier == 1.0 and
                dependency_modifier == 1.0):
                return base_intensity

            # Вычисляем комбинированный модификатор с оптимизациями
            state_modifier = self._get_cached_state_modifier(event_type, context_state)
            category_modifier = self._get_cached_category_modifier(event_type, context_state)
            subjective_modifier = self._get_cached_subjective_time_modifier(event_type, context_state)

            combined_modifier = (
                state_modifier *
                pattern_modifier *
                dependency_modifier *
                category_modifier *
                subjective_modifier
            )

            # Применяем экспоненциальное сглаживание через SmoothingEngine
            smoothed_modifier = self.smoothing_engine.smooth_modifier(event_type, combined_modifier)

            adapted_intensity = base_intensity * smoothed_modifier

            # Сохраняем историю интенсивностей через SmoothingEngine (оптимизировано)
            if not hasattr(self, '_history_counter'):
                self._history_counter = {}
            if event_type not in self._history_counter:
                self._history_counter[event_type] = 0

            self._history_counter[event_type] += 1
            if self._history_counter[event_type] % 10 == 0:  # Каждый 10-й вызов
                self.smoothing_engine.smooth_intensity(event_type, adapted_intensity)

            return adapted_intensity

    def _get_state_modifier(self, event_type: str, context_state: Optional[SelfState]) -> float:
        """
        Получить модификатор на основе состояния системы.
        Упрощенная версия с таблицей правил.

        Args:
            event_type: Тип события
            context_state: Текущее состояние системы

        Returns:
            Модификатор интенсивности
        """
        if not context_state:
            return 1.0

        # Простые правила на основе типа события и состояния
        rules = {
            # Положительные события усиливаются при низкой энергии
            ("recovery", "energy"): lambda e: 0.8 + (1.0 - e/100.0) * 0.5,
            ("comfort", "energy"): lambda e: 0.8 + (1.0 - e/100.0) * 0.5,
            ("joy", "energy"): lambda e: 0.8 + (1.0 - e/100.0) * 0.5,
            ("calm", "energy"): lambda e: 0.8 + (1.0 - e/100.0) * 0.5,

            # Негативные события усиливаются при низкой энергии
            ("decay", "energy"): lambda e: 0.9 + (1.0 - e/100.0) * 0.4,
            ("fatigue", "energy"): lambda e: 0.9 + (1.0 - e/100.0) * 0.4,
            ("discomfort", "energy"): lambda e: 0.9 + (1.0 - e/100.0) * 0.4,
            ("sadness", "energy"): lambda e: 0.9 + (1.0 - e/100.0) * 0.4,

            # Креативные события усиливаются при высокой энергии
            ("inspiration", "energy"): lambda e: 1.0 + max(0, (e/100.0 - 0.6)) * 0.5,
            ("curiosity", "energy"): lambda e: 1.0 + max(0, (e/100.0 - 0.6)) * 0.5,
            ("insight", "energy"): lambda e: 1.0 + max(0, (e/100.0 - 0.6)) * 0.5,

            # Хаотичные события усиливаются при низкой стабильности
            ("shock", "stability"): lambda s: 1.0 + (1.0 - s) * 0.6,
            ("fear", "stability"): lambda s: 1.0 + (1.0 - s) * 0.6,
            ("cognitive_confusion", "stability"): lambda s: 1.0 + (1.0 - s) * 0.6,
            ("confusion", "stability"): lambda s: 1.0 + (1.0 - s) * 0.6,

            # Спокойные события усиливаются при высокой стабильности
            ("cognitive_clarity", "stability"): lambda s: 0.9 + s * 0.3,
            ("insight", "stability"): lambda s: 0.9 + s * 0.3,
            ("calm", "stability"): lambda s: 0.9 + s * 0.3,
            ("acceptance", "stability"): lambda s: 0.9 + s * 0.3,
        }

        modifier = 1.0

        # Применяем правила для энергии
        energy_rule = (event_type, "energy")
        if energy_rule in rules:
            modifier *= rules[energy_rule](context_state.energy)

        # Применяем правила для стабильности
        stability_rule = (event_type, "stability")
        if stability_rule in rules:
            modifier *= rules[stability_rule](context_state.stability)

        # Применяем правила для целостности
        integrity_rule = (event_type, "integrity")
        if integrity_rule in rules:
            modifier *= rules[integrity_rule](context_state.integrity)

        return max(0.1, min(3.0, modifier))

    def get_modifiers(self,
                     event_type: str,
                     context_state: Optional[SelfState] = None,
                     pattern_modifier: float = 1.0,
                     dependency_modifier: float = 1.0) -> IntensityModifier:
        """
        Возвращает все модификаторы интенсивности для анализа.

        Реализует метод интерфейса IntensityAdapterInterface.
        """
        state_modifier = self._get_cached_state_modifier(event_type, context_state)
        category_modifier = self._get_cached_category_modifier(event_type, context_state)
        subjective_time_modifier = self._get_cached_subjective_time_modifier(event_type, context_state)
        smoothing_modifier = self._calculate_smoothed_modifier(event_type, 1.0)  # Базовый модификатор для сглаживания

        return IntensityModifier(
            state_modifier=state_modifier,
            pattern_modifier=pattern_modifier,
            dependency_modifier=dependency_modifier,
            category_modifier=category_modifier,
            subjective_time_modifier=subjective_time_modifier,
            smoothing_modifier=smoothing_modifier
        )

    def _get_cached_state_modifier(self, event_type: str, context_state: Optional[SelfState]) -> float:
        """Кэшированная версия получения модификатора состояния."""
        import time

        current_time = time.time()
        cache_key = (event_type, getattr(context_state, 'energy', 100),
                    getattr(context_state, 'stability', 1.0),
                    getattr(context_state, 'integrity', 1.0))

        # Проверяем кэш
        if (cache_key in self._state_modifier_cache and
            current_time - self._cache_timestamp < self._cache_ttl):
            return self._state_modifier_cache[cache_key]

        # Вычисляем и кэшируем
        modifier = self._get_state_modifier(event_type, context_state)
        self._state_modifier_cache[cache_key] = modifier
        self._cache_timestamp = current_time

        return modifier

    def _get_cached_category_modifier(self, event_type: str, context_state: Optional[SelfState]) -> float:
        """Кэшированная версия получения категориального модификатора."""
        # Категориальные модификаторы не зависят от состояния, кэшируем просто по типу
        cache_key = (event_type, 'category')

        if cache_key in self._category_modifier_cache:
            return self._category_modifier_cache[cache_key]

        modifier = self._get_category_modifier(event_type, context_state)
        self._category_modifier_cache[cache_key] = modifier

        return modifier

    def _get_cached_subjective_time_modifier(self, event_type: str, context_state: Optional[SelfState]) -> float:
        """Кэшированная версия получения модификатора субъективного времени."""
        import time

        current_time = time.time()
        # Субъективное время меняется медленно, кэшируем на основе типа события
        cache_key = (event_type, 'subjective_time')

        if (cache_key in self._subjective_time_cache and
            current_time - self._cache_timestamp < self._cache_ttl):
            return self._subjective_time_cache[cache_key]

        modifier = self._get_subjective_time_modifier(event_type, context_state)
        self._subjective_time_cache[cache_key] = modifier
        self._cache_timestamp = current_time

        return modifier


    def _get_category_modifier(self, event_type: str, context_state: Optional[SelfState] = None) -> float:
        """
        Получить модификатор для категории события.
        Упрощенная версия с базовыми правилами.

        Args:
            event_type: Тип события
            context_state: Текущее состояние системы

        Returns:
            Модификатор интенсивности
        """
        # Базовые модификаторы по категориям (значительно упрощено)
        category_modifiers = {
            # Экзистенциальные события - слегка усиливаются
            "meaning_found": 1.15,
            "insight": 1.15,
            "existential_purpose": 1.15,

            # Эмоциональные события - умеренное усиление
            "joy": 1.1,
            "inspiration": 1.1,

            # Негативные эмоции - умеренное усиление при проблемах
            "sadness": 1.05 if (context_state and context_state.energy < 50) else 1.0,
            "fear": 1.05 if (context_state and context_state.stability < 0.5) else 1.0,
        }

        return category_modifiers.get(event_type, 1.0)


    def _get_subjective_time_modifier(self, event_type: str, context_state: Optional[SelfState]) -> float:
        """
        Получить модификатор на основе субъективного времени.
        Упрощенная версия.

        Args:
            event_type: Тип события
            context_state: Текущее состояние системы

        Returns:
            Модификатор интенсивности
        """
        if not context_state:
            return 1.0

        # Простые правила для субъективного времени
        base_rate = getattr(context_state, 'subjective_time_base_rate', 1.0)

        # Разные типы событий реагируют по-разному
        if event_type in ["shock", "fear", "confusion"]:
            # Хаотичные события - инвертированная реакция
            return 1.0 + (1.0 - base_rate) * 0.2
        elif event_type in ["calm", "acceptance", "silence"]:
            # Спокойные события - прямая реакция
            return 1.0 + (base_rate - 1.0) * 0.15
        elif event_type in ["inspiration", "insight", "meaning_found"]:
            # Значимые события - оптимальны при нормальном темпе
            if 0.9 <= base_rate <= 1.1:
                return 1.2
            else:
                return 0.95

        return 1.0  # Без изменений для большинства событий


    def get_intensity_history_stats(self) -> Dict[str, Dict[str, Any]]:
        """Возвращает статистику истории интенсивностей и модификаторов через SmoothingEngine."""
        return self.smoothing_engine.get_smoothing_stats()

    def _calculate_volatility(self, values: List[float]) -> float:
        """Вычисляет волатильность (стандартное отклонение) ряда значений."""
        if len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5

    def get_intensity_stats(self) -> Dict[str, Any]:
        """
        Возвращает статистику работы адаптера.

        Реализует метод интерфейса IntensityAdapterInterface.
        """
        return self.get_intensity_history_stats()

    def reset_stats(self) -> None:
        """
        Сбрасывает внутреннюю статистику адаптера.

        Реализует метод интерфейса IntensityAdapterInterface.
        """
        self.smoothing_engine.reset_history()
        self._state_modifier_cache.clear()
        self._category_modifier_cache.clear()
        self._subjective_time_cache.clear()

    @property
    def supported_event_types(self) -> list[str]:
        """
        Список поддерживаемых типов событий.

        Реализует метод интерфейса IntensityAdapterInterface.
        """
        # Все типы событий из EventGenerator поддерживаются
        return [
            "noise", "decay", "recovery", "shock", "idle", "memory_echo",
            "social_presence", "social_conflict", "social_harmony",
            "cognitive_doubt", "cognitive_clarity", "cognitive_confusion",
            "existential_void", "existential_purpose", "existential_finitude",
            "connection", "isolation", "insight", "confusion", "curiosity",
            "meaning_found", "void", "acceptance", "silence", "joy", "sadness",
            "fear", "calm", "discomfort", "comfort", "fatigue", "anticipation",
            "boredom", "inspiration", "creative_dissonance",
        ]

    def is_event_type_supported(self, event_type: str) -> bool:
        """
        Проверяет, поддерживается ли данный тип события.

        Реализует метод интерфейса IntensityAdapterInterface.
        """
        return event_type in self.supported_event_types