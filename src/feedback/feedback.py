from dataclasses import dataclass, field
from typing import List, Dict, Optional
import random
import time
from state.self_state import SelfState
from environment.event_queue import EventQueue


@dataclass
class PendingAction:
    action_id: str
    action_pattern: str
    state_before: Dict[str, float]
    timestamp: float
    check_after_ticks: int
    ticks_waited: int = 0


@dataclass
class FeedbackRecord:
    action_id: str
    action_pattern: str
    state_delta: Dict[str, float]
    timestamp: float
    delay_ticks: int
    associated_events: List[str] = field(default_factory=list)


def register_action(action_id: str, action_pattern: str, 
                   state_before: Dict[str, float], timestamp: float,
                   pending_actions: List[PendingAction]) -> None:
    """
    Регистрирует действие для последующего наблюдения Feedback.
    
    Args:
        action_id: Уникальный идентификатор действия
        action_pattern: Паттерн действия ("dampen", "absorb", "ignore")
        state_before: Снимок состояния до действия
        timestamp: Время выполнения действия
        pending_actions: Список ожидающих действий (изменяется in-place)
    """
    pending = PendingAction(
        action_id=action_id,
        action_pattern=action_pattern,
        state_before=state_before.copy(),
        timestamp=timestamp,
        check_after_ticks=random.randint(3, 10)
    )
    pending_actions.append(pending)


def observe_consequences(self_state: SelfState, 
                        pending_actions: List[PendingAction],
                        event_queue: Optional[EventQueue] = None) -> List[FeedbackRecord]:
    """
    Наблюдает последствия действий и создает Feedback записи.
    
    Args:
        self_state: Текущее состояние Life
        pending_actions: Список ожидающих действий (изменяется in-place)
        event_queue: Очередь событий для сбора связанных событий (опционально)
    
    Returns:
        Список созданных Feedback записей
    """
    feedback_records = []
    to_remove = []
    
    for pending in pending_actions:
        pending.ticks_waited += 1
        
        if pending.ticks_waited >= pending.check_after_ticks:
            # Вычисляем изменения состояния
            state_after = {
                'energy': self_state.energy,
                'stability': self_state.stability,
                'integrity': self_state.integrity
            }
            
            state_delta = {
                k: state_after.get(k, 0) - pending.state_before.get(k, 0)
                for k in ['energy', 'stability', 'integrity']
            }
            
            # Проверяем минимальный порог изменений
            if any(abs(v) > 0.001 for v in state_delta.values()):
                # Собираем связанные события (опционально)
                # Примечание: для v1.0 не потребляем события из очереди, так как они нужны основному циклу
                # В полной реализации можно отслеживать события по timestamp или использовать отдельный механизм
                associated_events = []
                
                # Создаем Feedback запись
                feedback = FeedbackRecord(
                    action_id=pending.action_id,
                    action_pattern=pending.action_pattern,
                    state_delta=state_delta,
                    timestamp=time.time(),
                    delay_ticks=pending.ticks_waited,
                    associated_events=associated_events
                )
                feedback_records.append(feedback)
            
            to_remove.append(pending)
        elif pending.ticks_waited > 20:
            # Слишком долго ждали, удаляем
            to_remove.append(pending)
    
    # Удаляем обработанные записи
    for pending in to_remove:
        pending_actions.remove(pending)
    
    return feedback_records
