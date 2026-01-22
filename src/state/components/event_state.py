from dataclasses import dataclass, field
from typing import List, Any


@dataclass
class EventState:
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