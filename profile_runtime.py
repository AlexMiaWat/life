#!/usr/bin/env python3
"""
Скрипт для профилирования runtime loop Life
"""
import cProfile
import os
import pstats
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.environment.event_queue import EventQueue
from src.monitor.console import monitor
from src.runtime.loop import run_loop
from src.state.self_state import SelfState


def profile_runtime():
    """Профилирование runtime loop"""

    # Настройка SelfState
    self_state = SelfState()

    # Настройка EventQueue
    event_queue = EventQueue()

    # Создание профиля
    profiler = cProfile.Profile()

    print("Запуск профилирования runtime loop...")

    try:
        # Запуск профилирования
        profiler.enable()

        # Запуск runtime loop на короткое время
        import threading

        stop_event = threading.Event()

        # Запуск в отдельном потоке
        loop_thread = threading.Thread(
            target=run_loop,
            args=(
                self_state,
                monitor,
                0.01,  # очень быстрый тик
                100,  # snapshot каждые 100 тиков
                stop_event,
                event_queue,
                False,  # disable_weakness_penalty
                False,  # disable_structured_logging
                False,  # disable_learning
                False,  # disable_adaptation
                False,  # disable_clarity_moments
                1,  # log_flush_period_ticks
                False,  # enable_profiling (False, потому что мы профилируем снаружи)
            ),
            daemon=True,
        )

        loop_thread.start()

        # Ждем 5 секунд
        time.sleep(5)

        # Останавливаем
        stop_event.set()
        loop_thread.join(timeout=2)

    finally:
        # Останавливаем профилирование
        profiler.disable()

        # Сохраняем результаты
        os.makedirs("data", exist_ok=True)
        profile_filename = f"data/runtime_loop_profile_{int(time.time())}.prof"
        profiler.dump_stats(profile_filename)
        print(f"Профиль сохранен в {profile_filename}")

        # Выводим статистику
        stats = pstats.Stats(profiler, stream=sys.stdout)
        stats.sort_stats("cumulative")
        print("\n=== Топ 20 функций по cumulative time ===")
        stats.print_stats(20)

        print("\n=== Топ 20 функций по time ===")
        stats.sort_stats("time")
        stats.print_stats(20)


if __name__ == "__main__":
    profile_runtime()
