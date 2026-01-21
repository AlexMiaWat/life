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
    time_perception = "accelerated" if time_ratio >= 1.1 else "normal" if time_ratio > 0.9 else "slowed"

    # Модификация обработки в зависимости от восприятия времени
    if time_perception == "accelerated":
        # При ускоренном восприятии - учитывать все доступные источники + метрики времени
        processed = {
            "memory_proxy_size": len(recent_events),
            "adaptation_proxy": energy,
            "learning_proxy": stability,
            "planning_proxy_size": len(planning.get("potential_sequences", [])),
            "subjective_time_metrics": {
                "current_subjective_time": self_state.subjective_time,
                "time_ratio": time_ratio,
                "time_perception": time_perception,
                "intensity_smoothed": self_state.last_event_intensity
            }
        }
    elif time_perception == "slowed":
        # При замедленном восприятии - минимальный набор источников + базовые метрики времени
        processed = {
            "memory_proxy_size": len(recent_events),
            "adaptation_proxy": energy,
            "subjective_time_metrics": {
                "time_perception": time_perception,
                "time_ratio": time_ratio
            }
        }
    else:
        # Нормальное восприятие - стандартный набор с базовыми метриками времени
        processed = {
            "memory_proxy_size": len(recent_events),
            "adaptation_proxy": energy,
            "learning_proxy": stability,
            "planning_proxy_size": len(planning.get("potential_sequences", [])),
            "subjective_time_metrics": {
                "current_subjective_time": self_state.subjective_time,
                "time_perception": time_perception
            }
        }

    # Записываем в self_state без изменений других полей
    self_state.intelligence = {"processed_sources": processed}
