from src.state.self_state import SelfState


def process_information(self_state: SelfState) -> None:
    """
    Минимальная нейтральная обработка информации.

    Фиксирует потенциал обработки из нейтральных источников без интерпретации,
    оценки, предсказаний или влияния на другие слои.

    ИНТЕГРАЦИЯ: Добавляет метрики субъективного времени и модифицирует набор
    источников в зависимости от восприятия времени для фиксации потенциала обработки.
    """
    # Получаем нейтральные источники (proxy)
    recent_events = self_state.recent_events
    energy = self_state.energy
    stability = self_state.stability
    planning = self_state.planning

    # Расчет метрик восприятия времени
    time_ratio = self_state.subjective_time / self_state.age if self_state.age > 0 else 1.0
    time_perception = (
        "accelerated" if time_ratio >= 1.1 else "normal" if time_ratio > 0.9 else "slowed"
    )

    # Циркадные метрики
    import math
    circadian_phase_rad = self_state.circadian_phase
    if circadian_phase_rad < math.pi / 2:
        circadian_phase = "dawn"
        processing_intensity = 0.8  # Пониженная интенсивность обработки
    elif circadian_phase_rad < math.pi:
        circadian_phase = "day"
        processing_intensity = 1.4  # Повышенная интенсивность обработки
    elif circadian_phase_rad < 3 * math.pi / 2:
        circadian_phase = "dusk"
        processing_intensity = 1.0  # Нормальная интенсивность обработки
    else:
        circadian_phase = "night"
        processing_intensity = 0.6  # Минимальная интенсивность обработки

    # Проверяем момент ясности для усиления обработки
    clarity_active = getattr(self_state, 'clarity_moment_active', False)
    clarity_boost = 1.3 if clarity_active else 1.0

    # Модификация обработки в зависимости от восприятия времени и циркадных ритмов
    base_sources = {
        "memory_proxy_size": len(recent_events),
        "adaptation_proxy": energy,
        "circadian_phase": circadian_phase,
        "processing_intensity": processing_intensity * clarity_boost,
        "clarity_active": clarity_active,
    }

    # Улучшенная логика выбора источников с учетом моментов ясности
    if (time_perception == "accelerated" and processing_intensity * clarity_boost > 1.0) or clarity_active:
        # При ускоренном восприятии, высокой активности или моменте ясности - расширенный набор
        processed = {
            **base_sources,
            "learning_proxy": stability,
            "planning_proxy_size": len(planning.get("potential_sequences", [])),
            "subjective_time_metrics": {
                "current_subjective_time": self_state.subjective_time,
                "time_ratio": time_ratio,
                "time_perception": time_perception,
                "intensity_smoothed": self_state.last_event_intensity,
                "clarity_enhanced": clarity_active,
            },
            "processing_mode": "enhanced" if clarity_active else "accelerated",
        }
    elif time_perception == "slowed" or processing_intensity * clarity_boost < 0.8:
        # При замедленном восприятии или низкой активности - минимальный набор
        processed = {
            **base_sources,
            "subjective_time_metrics": {
                "time_perception": time_perception,
                "time_ratio": time_ratio,
                "minimal_mode": True,
            },
        }
    else:
        # Нормальное восприятие - адаптивный набор с учетом циркадной интенсивности и ясности
        enhanced_intensity = processing_intensity * clarity_boost
        processed = {
            **base_sources,
            "learning_proxy": stability,
            "planning_proxy_size": len(planning.get("potential_sequences", [])),
            "subjective_time_metrics": {
                "current_subjective_time": self_state.subjective_time,
                "time_perception": time_perception,
                "intensity_smoothed": self_state.last_event_intensity,
                **({"time_ratio": time_ratio} if time_perception in ["accelerated", "slowed"] else {}),
                "adaptive_mode": True,
            },
            "processing_mode": "normal",
        }

    # Записываем в self_state без изменений других полей
    self_state.intelligence = {"processed_sources": processed}
