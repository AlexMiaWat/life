from typing import Dict, Any

def process_information(self_state: dict) -> None:
    """
    Минимальная нейтральная обработка информации.

    Фиксирует потенциал обработки из нейтральных источников без интерпретации,
    оценки, предсказаний или влияния на другие слои.
    """
    # Получаем нейтральные источники (proxy)
    recent_events = self_state.get('recent_events', [])
    energy = self_state.get('energy', 0.0)
    stability = self_state.get('stability', 0.0)
    planning = self_state.get('planning', {})

    # Нейтральная обработка: фиксация размеров/значений источников
    processed = {
        'memory_proxy_size': len(recent_events),
        'adaptation_proxy': energy,
        'learning_proxy': stability,
        'planning_proxy_size': len(planning.get('potential_sequences', []))
    }

    # Записываем в self_state без изменений других полей
    self_state['intelligence'] = {
        'processed_sources': processed
    }