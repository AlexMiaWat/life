import json
import sys
from pathlib import Path

import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)
from src.state.self_state import SelfState

LOG_FILE = Path("data/tick_log.jsonl")
LOG_FILE.parent.mkdir(exist_ok=True)


def log(message):
    print(f"[RELOAD] {message}")
    print("TEST CHANGE")


def monitor(state: SelfState, log_file_path: Path = None):
    """
    Мониторинг состояния системы Life

    Args:
        state: Текущее состояние системы
        log_file_path: Путь к файлу логов (если None, используется LOG_FILE)
    """
    if log_file_path is None:
        log_file_path = LOG_FILE

    ticks = state.ticks
    age = state.age
    energy = state.energy
    integrity = state.integrity
    stability = state.stability
    last_significance = state.last_significance
    activated_count = len(getattr(state, "activated_memory", []))
    top_significance = max(
        [e.meaning_significance for e in getattr(state, "activated_memory", [])],
        default=0.0,
    )
    last_pattern = getattr(state, "last_pattern", "")

    # Цветной структурированный вывод состояния в консоль
    heartbeat = f"{Fore.RED}*{Style.RESET_ALL}"
    возраст_txt = f"{Fore.BLUE}возраст: {age:.1f} сек. {Style.RESET_ALL}"
    энергия_txt = f"{Fore.GREEN}энергия: {energy:.1f} %{Style.RESET_ALL}"
    интеллект_txt = f"{Fore.YELLOW}интеллект: {integrity:.4f}{Style.RESET_ALL}"
    стабильность_txt = f"{Fore.CYAN}стабильность: {stability:.4f}{Style.RESET_ALL}"
    значимость_txt = (
        f"{Fore.MAGENTA}значимость: {last_significance:.4f}{Style.RESET_ALL}"
    )
    активация_txt = f"активация: {activated_count} ({top_significance:.2f})"
    decision_txt = f"{Fore.YELLOW}decision: {last_pattern}{Style.RESET_ALL}"
    action_txt = f"{Fore.GREEN}action: executed {last_pattern}{Style.RESET_ALL}"
    msg = f"{heartbeat} [{ticks}] {возраст_txt} | {энергия_txt} | {интеллект_txt} | {стабильность_txt} | {значимость_txt} | {активация_txt} | {decision_txt} | {action_txt} | "
    sys.stdout.write(f"\r{msg}")
    sys.stdout.flush()

    # Логирование текущего тика в файл (append-only)
    tick_data = {
        "tick": ticks,
        "age": age,
        "energy": energy,
        "integrity": integrity,
        "stability": stability,
        "last_significance": last_significance,
    }

    with log_file_path.open("a") as f:
        f.write(json.dumps(tick_data) + "\n")
