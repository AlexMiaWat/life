import json
import sys
from pathlib import Path
import colorama
from colorama import Fore, Style
colorama.init(autoreset=True)

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
    
    # Цветной структурированный вывод состояния в консоль
    heartbeat = f"{Fore.RED}*{Style.RESET_ALL}"
    возраст_txt = f"{Fore.BLUE}возраст: {age:.1f} сек. {Style.RESET_ALL}"
    энергия_txt = f"{Fore.GREEN}энергия: {energy:.1f} %{Style.RESET_ALL}"
    интеллект_txt = f"{Fore.YELLOW}интеллект: {integrity:.4f}{Style.RESET_ALL}"
    стабильность_txt = f"{Fore.CYAN}стабильность: {stability:.4f}{Style.RESET_ALL}"
    msg = f"{heartbeat} [{ticks}] {возраст_txt} | {энергия_txt} | {интеллект_txt} | {стабильность_txt} | "
    sys.stdout.write(f'\r{msg}')
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
