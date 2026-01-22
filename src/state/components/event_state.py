from dataclasses import dataclass, field
from typing import List, Any, Dict
from ...contracts.serialization_contract import Serializable


@dataclass
class EventState(Serializable):
    """
    Компонент состояния, отвечающий за события и историю системы Life.

    Включает недавние события, историю параметров и метрики значимости.
    """

    # События и история
    recent_events: List[Any] = field(default_factory=list)  # Недавние события
    last_significance: float = 0.0  # Последняя значимость события

    def add_event(self, event: Any) -> None:
        """Добавляет событие в историю недавних событий."""
        self.recent_events.append(event)
        # Ограничиваем размер истории (последние 50 событий)
        if len(self.recent_events) > 50:
            self.recent_events.pop(0)

    def get_recent_events(self, limit: int = 10) -> List[Any]:
        """Возвращает недавние события (ограниченное количество)."""
        return self.recent_events[-limit:] if limit > 0 else self.recent_events

    def clear_events(self) -> None:
        """Очищает историю событий."""
        self.recent_events.clear()

    def get_event_count(self) -> int:
        """Возвращает количество сохраненных событий."""
        return len(self.recent_events)

    def update_significance(self, significance: float) -> None:
        """Обновляет метрику значимости."""
        self.last_significance = significance

    def get_last_significance(self) -> float:
        """Возвращает последнюю значимость."""
        return self.last_significance

    def to_dict(self, max_age_seconds: float = 3600.0, min_significance: float = 0.1) -> Dict[str, Any]:
        """
        Сериализует состояние событий с фильтрацией устаревших записей.

        Args:
            max_age_seconds: Максимальный возраст событий в секундах (по умолчанию 1 час)
            min_significance: Минимальная значимость для включения события (по умолчанию 0.1)

        Returns:
            Dict[str, Any]: Словарь с состоянием событий
        """
        import time
        current_time = time.time()

        # Фильтруем события по возрасту и значимости
        filtered_events = []
        for event in self.recent_events:
            try:
                # Проверяем возраст события (если есть timestamp)
                if hasattr(event, 'timestamp') and (current_time - event.timestamp) > max_age_seconds:
                    continue

                # Проверяем значимость события (если есть significance)
                if hasattr(event, 'significance') and event.significance < min_significance:
                    continue

                # Добавляем отфильтрованное событие
                filtered_events.append(event)
            except (AttributeError, TypeError):
                # Пропускаем события с некорректной структурой
                continue

        return {
            "recent_events": filtered_events[-20:],  # Последние 20 отфильтрованных событий
            "event_count": self.get_event_count(),
            "filtered_event_count": len(filtered_events),
            "last_significance": self.last_significance,
            "filter_applied": True,
            "max_age_seconds": max_age_seconds,
            "min_significance": min_significance
        }