#!/usr/bin/env python3
"""
Простой бенчмарк производительности runtime loop.
"""

import time
import threading
import sys
from pathlib import Path

# Настройка путей
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.state.self_state import create_initial_state
from src.runtime.loop import run_loop
from src.monitor import monitor
from src.runtime.performance_metrics import performance_metrics


def simple_runtime_benchmark():
    """Простой бенчмарк runtime loop."""
    print("Запуск простого бенчмарка...")

    # Создание состояния
    state = create_initial_state()
    print(f"Начальное состояние: ticks={state.ticks}")

    # Запуск на 100 тиков
    stop_event = threading.Event()

    def run_loop_thread():
        try:
            run_loop(
                self_state=state,
                monitor=monitor,
                tick_interval=0.1,  # 100ms per tick
                stop_event=stop_event,
                enable_profiling=False
            )
        except Exception as e:
            print(f"Ошибка: {e}")

    start_time = time.time()
    loop_thread = threading.Thread(target=run_loop_thread, daemon=True)
    loop_thread.start()
    loop_thread.join(timeout=30)  # 30 секунд таймаут
    stop_event.set()

    end_time = time.time()
    total_time = end_time - start_time

    ticks_per_second = state.ticks / total_time if total_time > 0 else 0

    print(".2f")
    print(f"Финальное состояние: ticks={state.ticks}, memory_entries={len(state.memory)}")

    return {
        "ticks": state.ticks,
        "time": total_time,
        "ticks_per_second": ticks_per_second
    }


if __name__ == "__main__":
    results = simple_runtime_benchmark()
    print("Бенчмарк завершен!")