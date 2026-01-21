import argparse
import json
import sys
from pathlib import Path

from src.state.self_state import SelfState

parser = argparse.ArgumentParser()
parser.add_argument(
    "--clear-data", type=str, default="no", help="Очистить логи и снапшоты (yes/no)"
)
parser.add_argument(
    "--tick-interval", type=float, default=1.0, help="Интервал тика, сек"
)
parser.add_argument(
    "--snapshot-period", type=int, default=10, help="Периодичность snapshot, тиков"
)
args = parser.parse_args()

# Путь к файлу логов
LOG_FILE = Path("data/tick_log.jsonl")
LOG_FILE.parent.mkdir(exist_ok=True)


def monitor(state: SelfState):
    # Консольный вывод на одной строке
    heartbeat = "•"
    msg = f"{heartbeat} tick={state.ticks} age={state.age:.2f}s energy={state.energy:.1f} integrity={state.integrity:.2f} stability={state.stability:.3f}"
    sys.stdout.write("\r" + msg)
    sys.stdout.flush()

    # Логирование текущего тика в файл (append-only)
    tick_data = {
        "tick": state.ticks,
        "age": state.age,
        "energy": state.energy,
        "integrity": state.integrity,
        "stability": state.stability,
    }
    with LOG_FILE.open("a") as f:
        f.write(json.dumps(tick_data) + "\n")


import threading
import time

from src.environment import EventGenerator, EventQueue
from src.runtime.loop import run_loop

try:
    self_state = SelfState().load_latest_snapshot()
except FileNotFoundError:
    self_state = SelfState()

if __name__ == "__main__":
    event_queue = EventQueue()
    stop_event = threading.Event()

    def background_event_generation(queue, generator, stop_event):
        while not stop_event.is_set():
            event = generator.generate()
            queue.push(event)
            time.sleep(1.0)

    generator_thread = threading.Thread(
        target=background_event_generation,
        args=(event_queue, EventGenerator(), stop_event),
    )
    generator_thread.daemon = True
    generator_thread.start()
    run_loop(
        self_state,
        monitor,
        tick_interval=args.tick_interval,
        snapshot_period=args.snapshot_period,
        event_queue=event_queue,
        stop_event=stop_event,
        disable_weakness_penalty=False,
        disable_structured_logging=False,
        disable_learning=False,
        disable_adaptation=False,
        enable_memory_hierarchy=False,  # Экспериментальная многоуровневая память отключена по умолчанию
        enable_consciousness=False,  # Экспериментальная система сознания отключена по умолчанию
        log_flush_period_ticks=10,
        enable_profiling=False,
    )
    print("Жизнь завершена. Финальное состояние:")
    print(self_state)
