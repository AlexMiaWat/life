import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

from memory.memory import ArchiveMemory, Memory, MemoryEntry

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
    memory: Memory = field(default=None)  # Активная память с поддержкой архивации
    archive_memory: ArchiveMemory = field(
        default_factory=ArchiveMemory, init=False
    )  # Архивная память (не сериализуется в snapshot напрямую)
    
    def __post_init__(self):
        """Инициализация memory с архивом после создания объекта"""
        if self.memory is None:
            self.memory = Memory(archive=self.archive_memory)
    activated_memory: list = field(
        default_factory=list
    )  # Transient, не сохраняется в snapshot
    last_pattern: str = ""  # Transient, последний выбранный паттерн decision
    learning_params: dict = field(
        default_factory=lambda: {
            "event_type_sensitivity": {
                "noise": 0.2,
                "decay": 0.2,
                "recovery": 0.2,
                "shock": 0.2,
                "idle": 0.2,
            },
            "significance_thresholds": {
                "noise": 0.1,
                "decay": 0.1,
                "recovery": 0.1,
                "shock": 0.1,
                "idle": 0.1,
            },
            "response_coefficients": {
                "dampen": 0.5,
                "absorb": 1.0,
                "ignore": 0.0,
            },
        }
    )  # Параметры для Learning (Этап 14)
    adaptation_params: dict = field(
        default_factory=lambda: {
            "behavior_sensitivity": {
                "noise": 0.2,
                "decay": 0.2,
                "recovery": 0.2,
                "shock": 0.2,
                "idle": 0.2,
            },
            "behavior_thresholds": {
                "noise": 0.1,
                "decay": 0.1,
                "recovery": 0.1,
                "shock": 0.1,
                "idle": 0.1,
            },
            "behavior_coefficients": {
                "dampen": 0.5,
                "absorb": 1.0,
                "ignore": 0.0,
            },
        }
    )  # Параметры поведения для Adaptation (Этап 15)
    adaptation_history: list = field(
        default_factory=list
    )  # История адаптаций для обратимости (Этап 15)

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
        memory_entries = []
        if "memory" in mapped_data:
            memory_entries = [
                MemoryEntry(**entry) for entry in mapped_data["memory"]
            ]
            mapped_data.pop("memory")  # Удаляем из mapped_data, инициализируем отдельно
        
        # Создать экземпляр из dict
        state = SelfState(**mapped_data)
        # Загружаем архив при загрузке snapshot
        state.archive_memory = ArchiveMemory()
        state.archive_memory._load_archive()
        # Инициализируем memory с архивом и загруженными записями
        state.memory = Memory(archive=state.archive_memory)
        for entry in memory_entries:
            state.memory.append(entry)
        return state


def create_initial_state() -> SelfState:
    state = SelfState()
    # Инициализируем архивную память
    state.archive_memory = ArchiveMemory()
    # Инициализируем memory с архивом (__post_init__ уже создал memory, но пересоздадим с правильным архивом)
    state.memory = Memory(archive=state.archive_memory)
    return state


def save_snapshot(state: SelfState):
    """
    Сохраняет текущее состояние жизни как отдельный JSON файл
    """
    snapshot = asdict(state)
    # Исключаем transient поля
    snapshot.pop("activated_memory", None)
    snapshot.pop("last_pattern", None)
    # Конвертируем Memory в list для сериализации
    if isinstance(state.memory, Memory):
        snapshot["memory"] = [asdict(entry) for entry in state.memory]
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
        memory_entries = []
        if "memory" in data:
            memory_entries = [MemoryEntry(**entry) for entry in data["memory"]]
            data.pop("memory")  # Удаляем из data, инициализируем отдельно
        
        state = SelfState(**data)
        # Загружаем архив при загрузке snapshot
        state.archive_memory = ArchiveMemory()
        state.archive_memory._load_archive()
        # Инициализируем memory с архивом и загруженными записями
        state.memory = Memory(archive=state.archive_memory)
        for entry in memory_entries:
            state.memory.append(entry)
        return state
    else:
        raise FileNotFoundError(f"Snapshot {tick} не найден")
