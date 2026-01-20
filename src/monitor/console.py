import json
import logging
import sys
from pathlib import Path

import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)
from src.state.self_state import SelfState

logger = logging.getLogger(__name__)

LOG_FILE = Path("data/tick_log.jsonl")
LOG_FILE.parent.mkdir(exist_ok=True)


def log(message: str):
    """
    Отладочная функция для логирования сообщений
    """
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

    # Убедимся, что директория существует
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    ticks = state.ticks
    age = state.age
    subjective_time = state.subjective_time
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

    # Расчет метрик субъективного времени
    time_ratio = subjective_time / age if age > 0 else 1.0

    # Добавляем в историю соотношений
    time_ratio_history = getattr(state, "time_ratio_history", [])
    time_ratio_history.append(time_ratio)
    # Ограничиваем историю последними 10 значениями
    if len(time_ratio_history) > 10:
        time_ratio_history.pop(0)
    state.time_ratio_history = time_ratio_history

    # Вычисляем тренд на основе последних значений
    time_trend = "→"  # Стабильный
    if len(time_ratio_history) >= 3:
        recent_ratios = time_ratio_history[-3:]
        avg_recent = sum(recent_ratios) / len(recent_ratios)
        avg_earlier = sum(time_ratio_history[:-3]) / len(time_ratio_history[:-3]) if len(time_ratio_history) > 3 else avg_recent

        if avg_recent > avg_earlier * 1.05:  # Рост более 5%
            time_trend = "↗"  # Тренд на ускорение
        elif avg_recent < avg_earlier * 0.95:  # Падение более 5%
            time_trend = "↘"  # Тренд на замедление

    # Скорость изменения субъективного времени
    subjective_rate = getattr(state, "subjective_time_base_rate", 1.0)

    # Цветной структурированный вывод состояния в консоль
    heartbeat = f"{Fore.RED}*{Style.RESET_ALL}"
    # Показываем physical vs subjective time с соотношением и трендом
    время_txt = f"{Fore.BLUE}физ: {age:.1f}с | субъект: {subjective_time:.1f}с (x{time_ratio:.2f}{time_trend}){Style.RESET_ALL}"
    энергия_txt = f"{Fore.GREEN}энергия: {energy:.1f} %{Style.RESET_ALL}"
    интеллект_txt = f"{Fore.YELLOW}интеллект: {integrity:.4f}{Style.RESET_ALL}"
    стабильность_txt = f"{Fore.CYAN}стабильность: {stability:.4f}{Style.RESET_ALL}"
    значимость_txt = (
        f"{Fore.MAGENTA}значимость: {last_significance:.4f}{Style.RESET_ALL}"
    )
    активация_txt = f"активация: {activated_count} ({top_significance:.2f})"
    decision_txt = f"{Fore.YELLOW}decision: {last_pattern}{Style.RESET_ALL}"
    action_txt = f"{Fore.GREEN}action: executed {last_pattern}{Style.RESET_ALL}"
    msg = f"{heartbeat} [{ticks}] {время_txt} | {энергия_txt} | {интеллект_txt} | {стабильность_txt} | {значимость_txt} | {активация_txt} | {decision_txt} | {action_txt} | "
    sys.stdout.write(f"\r{msg}")
    sys.stdout.flush()

    # Логирование текущего тика в файл (append-only)
    tick_data = {
        "tick": ticks,
        "age": age,
        "subjective_time": subjective_time,
        "time_ratio": time_ratio,
        "time_trend": time_trend,
        "time_ratio_history": time_ratio_history.copy(),
        "subjective_rate": subjective_rate,
        "energy": energy,
        "integrity": integrity,
        "stability": stability,
        "last_significance": last_significance,
        "activated_memory_count": activated_count,
        "top_activated_significance": top_significance,
        "last_decision_pattern": last_pattern,
    }

    with log_file_path.open("a") as f:
        f.write(json.dumps(tick_data) + "\n")
