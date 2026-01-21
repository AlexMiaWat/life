"""
SnapshotManager: управление снапшотами состояния Life.

Инкапсулирует логику периодического сохранения снапшотов,
изолируя I/O операции от основного runtime loop.
"""

import logging
from typing import Any, Callable, Dict, Optional

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

        # Статус последней операции
        self.last_operation_success: Optional[bool] = None
        self.last_operation_error: Optional[str] = None
        self.last_operation_timestamp: Optional[float] = None

    def should_snapshot(self, ticks: int) -> bool:
        """
        Проверяет, нужно ли делать снапшот на текущем тике.

        Тик 0 исключен из снапшотов намеренно: при инициализации системы
        состояние еще не стабилизировалось, поэтому первый снапшот делается
        только после первого полного цикла (на тике period_ticks).

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

        Raises:
            ValueError: Если self_state равен None
        """
        if self_state is None:
            raise ValueError("self_state cannot be None")

        import time

        if self.should_snapshot(self_state.ticks):
            try:
                self.saver(self_state)
                # Записываем успешную операцию
                self.last_operation_success = True
                self.last_operation_error = None
                self.last_operation_timestamp = time.time()
                return True
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Ошибка при сохранении snapshot: {error_msg}", exc_info=True)
                # Записываем неудачную операцию
                self.last_operation_success = False
                self.last_operation_error = error_msg
                self.last_operation_timestamp = time.time()
                return False

        # Сброс статуса если снапшот не делался
        self.last_operation_success = None
        self.last_operation_error = None
        return False

    def get_last_operation_status(self) -> Dict[str, Optional[Any]]:
        """
        Получает статус последней операции сохранения снапшота.

        Returns:
            Dict с информацией о последней операции:
            - success: True/False/None (None если операция не выполнялась)
            - error: Сообщение об ошибке или None
            - timestamp: Время последней операции или None
        """
        return {
            "success": self.last_operation_success,
            "error": self.last_operation_error,
            "timestamp": self.last_operation_timestamp,
        }

    def was_last_operation_successful(self) -> Optional[bool]:
        """
        Проверяет, была ли последняя операция успешной.

        Returns:
            True если последняя операция была успешной,
            False если была ошибка,
            None если операция не выполнялась
        """
        return self.last_operation_success
