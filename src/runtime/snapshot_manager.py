"""
SnapshotManager: управление снапшотами состояния Life.

Инкапсулирует логику периодического сохранения снапшотов,
изолируя I/O операции от основного runtime loop.
"""
import logging
from typing import Callable

from src.state.self_state import SelfState

logger = logging.getLogger(__name__)


class SnapshotManager:
    """
    Менеджер снапшотов состояния Life.
    
    Управляет периодичностью создания снапшотов на основе количества тиков,
    изолирует обработку ошибок и I/O операции от основного цикла.
    """
    
    def __init__(self, period_ticks: int, saver: Callable[[SelfState], None]):
        """
        Инициализация менеджера снапшотов.
        
        Args:
            period_ticks: Периодичность снапшотов (каждые N тиков)
            saver: Функция сохранения снапшота (например, save_snapshot)
            
        Raises:
            ValueError: Если saver равен None или period_ticks <= 0
        """
        if saver is None:
            raise ValueError("saver cannot be None")
        if period_ticks <= 0:
            raise ValueError("period_ticks must be positive")
        
        self.period_ticks = period_ticks
        self.saver = saver
    
    def should_snapshot(self, ticks: int) -> bool:
        """
        Проверяет, нужно ли делать снапшот на текущем тике.
        
        Args:
            ticks: Текущее количество тиков
            
        Returns:
            True если нужно сделать снапшот, False иначе
        """
        return ticks > 0 and ticks % self.period_ticks == 0
    
    def maybe_snapshot(self, self_state: SelfState) -> bool:
        """
        Делает снапшот, если нужно по периодичности.
        
        Обрабатывает исключения внутри менеджера, не роняя основной цикл.
        
        Args:
            self_state: Состояние Life для сохранения
            
        Returns:
            True если снапшот был сделан, False иначе
        """
        if self.should_snapshot(self_state.ticks):
            try:
                self.saver(self_state)
                return True
            except Exception as e:
                logger.error(f"Ошибка при сохранении snapshot: {e}", exc_info=True)
                return False
        return False
