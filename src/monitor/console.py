import json
import sys
from pathlib import Path

LOG_FILE = Path("data/tick_log.jsonl")
LOG_FILE.parent.mkdir(exist_ok=True)

def log(message):
    print(f"[RELOAD] {message}")
    print('TEST CHANGE')

def monitor(state):
    ticks = state.get('ticks', 0)
    age = state.get('age', 0.0)
    energy = state.get('energy', 0.0)
    integrity = state.get('integrity', 1.0)
    stability = state.get('stability', 1.0)
    
    # Консольный вывод на одной строке
    heartbeat = '•'
    msg = f"{heartbeat} [{ticks}] age={age:.1f}s energy={energy:.1f} int={integrity:.2f} stab={stability:.2f}"
    sys.stdout.write('\r' + msg)
    sys.stdout.flush()
    
    # Логирование текущего тика в файл (append-only)
    tick_data = {
        "tick": ticks,
        "age": age,
        "energy": energy,
        "integrity": integrity,
        "stability": stability
    }
    
    with LOG_FILE.open("a") as f:
        f.write(json.dumps(tick_data) + "\n")
