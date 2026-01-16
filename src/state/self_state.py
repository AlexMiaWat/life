import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

from memory.memory import MemoryEntry

# Папка для снимков
SNAPSHOT_DIR = Path("data/snapshots")
SNAPSHOT_DIR.mkdir(exist_ok=True)


@dataclass
class SelfState:
    life_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    birth_timestamp: float = field(default_factory=time.time)
    age: float = 0.0
    ticks: int = 0
    energy: float = 100.0
    integrity: float = 1.0
    stability: float = 1.0
    fatigue: float = 0.0
    tension: float = 0.0
    active: bool = True
    recent_events: list = field(default_factory=list)
    last_significance: float = 0.0
    energy_history: list = field(default_factory=list)
    stability_history: list = field(default_factory=list)
    planning: dict = field(default_factory=dict)
    intelligence: dict = field(default_factory=dict)
    memory: list[MemoryEntry] = field(default_factory=list)
    activated_memory: list = field(
        default_factory=list
    )  # Transient, не сохраняется в snapshot
    last_pattern: str = ""  # Transient, последний выбранный паттерн decision

    def apply_delta(self, deltas: dict[str, float]) -> None:
        for key, delta in deltas.items():
            if hasattr(self, key):
                current = getattr(self, key)
                if key == "energy":
                    setattr(self, key, max(0.0, min(100.0, current + delta)))
                elif key in ["integrity", "stability"]:
                    setattr(self, key, max(0.0, min(1.0, current + delta)))
                else:
                    setattr(self, key, current + delta)

    def load_latest_snapshot(self) -> "SelfState":
        # Найти последний snapshot_*.json
        snapshots = list(SNAPSHOT_DIR.glob("snapshot_*.json"))
        if not snapshots:
            raise FileNotFoundError("No snapshots found")
        # Сортировать по номеру тика
        snapshots.sort(key=lambda p: int(p.stem.split("_")[1]))
        latest = snapshots[-1]
        with latest.open("r") as f:
            data = json.load(f)
        # Mapping для совместимости
        field_mapping = {
            "alive": "active",
        }
        mapped_data = {}
        for k, v in data.items():
            mapped_key = field_mapping.get(k, k)
            if mapped_key in SelfState.__dataclass_fields__:
                mapped_data[mapped_key] = v
        # Конвертировать memory из list of dict в list of MemoryEntry
        if "memory" in mapped_data:
            mapped_data["memory"] = [
                MemoryEntry(**entry) for entry in mapped_data["memory"]
            ]
        # Создать экземпляр из dict
        return SelfState(**mapped_data)


def create_initial_state() -> SelfState:
    return SelfState()


def save_snapshot(state: SelfState):
    """
    Сохраняет текущее состояние жизни как отдельный JSON файл
    """
    snapshot = asdict(state)
    # Исключаем transient поля
    snapshot.pop("activated_memory", None)
    snapshot.pop("last_pattern", None)
    tick = snapshot["ticks"]
    filename = SNAPSHOT_DIR / f"snapshot_{tick:06d}.json"
    with filename.open("w") as f:
        json.dump(snapshot, f, indent=2, default=str)


def load_snapshot(tick: int) -> SelfState:
    """
    Загружает снимок по номеру тика
    """
    filename = SNAPSHOT_DIR / f"snapshot_{tick:06d}.json"
    if filename.exists():
        with filename.open("r") as f:
            data = json.load(f)
        # Конвертировать memory из list of dict в list of MemoryEntry
        if "memory" in data:
            data["memory"] = [MemoryEntry(**entry) for entry in data["memory"]]
        return SelfState(**data)
    else:
        raise FileNotFoundError(f"Snapshot {tick} не найден")
