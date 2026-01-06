import json
from pathlib import Path
from copy import deepcopy

# Папка для снимков
SNAPSHOT_DIR = Path("data/snapshots")
SNAPSHOT_DIR.mkdir(exist_ok=True)

def save_snapshot(state):
    """
    Сохраняет текущее состояние жизни как отдельный JSON файл
    """
    # Копия состояния, чтобы не зависеть от ссылок
    snapshot = deepcopy(state)
    tick = snapshot.get('ticks', 0)
    filename = SNAPSHOT_DIR / f"snapshot_{tick:06d}.json"
    with filename.open("w") as f:
        json.dump(snapshot, f, indent=2)

def load_snapshot(tick):
    """
    Загружает снимок по номеру тика
    """
    filename = SNAPSHOT_DIR / f"snapshot_{tick:06d}.json"
    if filename.exists():
        with filename.open("r") as f:
            return json.load(f)
    else:
        raise FileNotFoundError(f"Snapshot {tick} не найден")
