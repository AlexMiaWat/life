from typing import Dict, Any
from state.self_state import SelfState

def process_information(self_state: SelfState) -> None:
    """
    Минимальная нейтральная обработка информации.

    Фиксирует потенциал обработки из нейтральных источников без интерпретации,
    оценки, предсказаний или влияния на другие слои.
    """
    # Получаем нейтральные источники (proxy)
    recent_events = self_state.recent_events
    energy = self_state.energy
    stability = self_state.stability
    planning = self_state.planning

    # Нейтральная обработка: фиксация размеров/значений источников
    processed = {
        'memory_proxy_size': len(recent_events),
        'adaptation_proxy': energy,
        'learning_proxy': stability,
        'planning_proxy_size': len(planning.get('potential_sequences', []))
    }

    # Записываем в self_state без изменений других полей
    self_state.intelligence = {
        'processed_sources': processed
    }