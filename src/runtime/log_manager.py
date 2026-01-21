"""
LogManager: управление буферизацией и сбросом логов.

Инкапсулирует политику flush буфера логов, убирая регулярный I/O
из hot-path runtime loop.
"""

import logging
from typing import Callable, Literal

from src.state.self_state import SelfState

logger = logging.getLogger(__name__)


class FlushPolicy:
    """
    Политика сброса буфера логов.

    Определяет, когда нужно сбрасывать буфер логов на диск:
    - По периодичности (раз в N тиков)
    - Перед снапшотом (точка консистентности)
    - После снапшота (если был сделан снапшот)
    - При исключениях (сохранение логов при ошибках)
    - При завершении (обязательный flush)
    """

    def __init__(
        self,
        flush_period_ticks: int = 10,
        flush_before_snapshot: bool = True,
        flush_after_snapshot: bool = False,
        flush_on_exception: bool = True,
        flush_on_shutdown: bool = True,
    ):
        """
        Инициализация политики flush.

        Args:
            flush_period_ticks: Flush раз в N тиков (по умолчанию 10)
            flush_before_snapshot: Flush перед снапшотом (по умолчанию True)
            flush_after_snapshot: Flush после снапшота (по умолчанию False)
            flush_on_exception: Flush при исключении (по умолчанию True)
            flush_on_shutdown: Flush при завершении (по умолчанию True, обязательно)
        """
        self.flush_period_ticks = flush_period_ticks
        self.flush_before_snapshot = flush_before_snapshot
        self.flush_after_snapshot = flush_after_snapshot
        self.flush_on_exception = flush_on_exception
        self.flush_on_shutdown = flush_on_shutdown


class LogManager:
    """
    Менеджер логирования и буферизации.

    Управляет политикой сброса буфера логов, убирая регулярный I/O
    из hot-path runtime loop. Flush происходит по расписанию, а не на каждом тике.
    """

    def __init__(
        self,
        flush_policy: FlushPolicy,
        flush_fn: Callable[[], None],
    ):
        """
        Инициализация менеджера логов.

        Args:
            flush_policy: Политика flush буфера
            flush_fn: Функция сброса буфера (например, self_state._flush_log_buffer)

        Raises:
            ValueError: Если flush_fn равен None или flush_policy.flush_period_ticks <= 0
        """
        if flush_fn is None:
            raise ValueError("flush_fn cannot be None")
        if flush_policy.flush_period_ticks <= 0:
            raise ValueError("flush_period_ticks must be positive")

        self.flush_policy = flush_policy
        self.flush_fn = flush_fn
        # Инициализируем так, чтобы первый flush был на тике flush_period_ticks, а не на тике 0.
        # Это намеренное решение для избежания flush при инициализации системы.
        # Например, если flush_period_ticks=10, то last_flush_tick=-10, и первый flush произойдет на тике 10.
        self.last_flush_tick = -flush_policy.flush_period_ticks

    def maybe_flush(
        self,
        self_state: SelfState,
        *,
        phase: Literal["tick", "before_snapshot", "after_snapshot", "exception", "shutdown"],
    ) -> None:
        """
        Сбрасывает буфер логов, если нужно по политике.

        Args:
            self_state: Состояние для проверки тиков (не может быть None)
            phase: Фаза выполнения (tick/before_snapshot/after_snapshot/exception/shutdown)

        Raises:
            ValueError: Если self_state равен None (для консистентности с SnapshotManager)

        Note:
            - Инициализация `last_flush_tick = -flush_period_ticks` обеспечивает первый flush
              на тике `flush_period_ticks`, а не на тике 0. Это намеренное решение для
              избежания flush при инициализации системы.
            - При ошибке flush `last_flush_tick` не обновляется, что обеспечивает retry-механизм:
              на следующем тике flush попытается выполниться снова.
            - Flush после снапшота обрабатывается только в фазе "after_snapshot", а не в фазе "tick",
              чтобы избежать двойного flush.
        """
        if self_state is None:
            raise ValueError("self_state cannot be None")

        should_flush = False

        if phase == "shutdown" and self.flush_policy.flush_on_shutdown:
            should_flush = True
        elif phase == "exception" and self.flush_policy.flush_on_exception:
            should_flush = True
        elif phase == "before_snapshot" and self.flush_policy.flush_before_snapshot:
            should_flush = True
        elif phase == "after_snapshot" and self.flush_policy.flush_after_snapshot:
            should_flush = True
        elif phase == "tick":
            # Flush раз в N тиков (периодический flush)
            # Примечание: flush после снапшота обрабатывается только в фазе "after_snapshot",
            # чтобы избежать двойного flush, когда snapshot_was_made=True передается в фазу "tick".
            ticks_since_flush = self_state.ticks - self.last_flush_tick
            if ticks_since_flush >= self.flush_policy.flush_period_ticks:
                should_flush = True

        if should_flush:
            try:
                self.flush_fn()
                self.last_flush_tick = self_state.ticks
            except Exception as e:
                # При ошибке flush не обновляем last_flush_tick, чтобы обеспечить retry-механизм:
                # на следующем тике flush попытается выполниться снова.
                # Это важно для надежности логирования, особенно при временных проблемах с I/O.
                logger.warning(f"Ошибка при flush логов: {e}", exc_info=True)
