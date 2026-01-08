import sys

self_state = {
    'alive': True,
    'ticks': 0,
    'age': 0.0,
    'energy': 100.0,
    'stability': 1.0,
    'integrity': 1.0
}

import sys
import json
from pathlib import Path

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--clear-data", type=str, default="no", help="Очистить логи и снапшоты (yes/no)")
parser.add_argument("--tick-interval", type=float, default=1.0, help="Интервал тика, сек")
parser.add_argument("--snapshot-period", type=int, default=10, help="Периодичность snapshot, тиков")
args = parser.parse_args()

# Путь к файлу логов
LOG_FILE = Path("data/tick_log.jsonl")
LOG_FILE.parent.mkdir(exist_ok=True)

def monitor(state):
    # Консольный вывод на одной строке
    heartbeat = '•'
    msg = f"{heartbeat} tick={state['ticks']} age={state['age']:.2f}s energy={state['energy']:.1f} integrity={state['integrity']:.2f} stability={state['stability']:.3f}"
    sys.stdout.write('\r' + msg)
    sys.stdout.flush()

    # Логирование текущего тика в файл (append-only)
    tick_data = {
        "tick": state['ticks'],
        "age": state['age'],
        "energy": state['energy'],
        "integrity": state['integrity'],
        "stability": state['stability']
    }
    with LOG_FILE.open("a") as f:
        f.write(json.dumps(tick_data) + "\n")
    
from runtime.loop import run_loop
from environment import EventQueue, EventGenerator
import threading
import time

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
        args=(event_queue, EventGenerator(), stop_event)
    )
    generator_thread.daemon = True
    generator_thread.start()
    run_loop(self_state, monitor, event_queue=event_queue)
    print("Жизнь завершена. Финальное состояние:")
    print(self_state)
