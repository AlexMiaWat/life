import json
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any, Dict, List

from src.memory.memory import ArchiveMemory, Memory
from src.memory.memory_types import MemoryEntry
from src.validation.field_validator import FieldValidator
from .components.identity_state import IdentityState
from .components.physical_state import PhysicalState
from .components.time_state import TimeState
from .components.memory_state import MemoryState
from .components.cognitive_state import CognitiveState
from .components.event_state import EventState

# Папка для снимков
SNAPSHOT_DIR = Path("data/snapshots")
SNAPSHOT_DIR.mkdir(exist_ok=True)

# Папка для логов изменений состояния
STATE_CHANGES_LOG_DIR = Path("data/logs")
STATE_CHANGES_LOG_DIR.mkdir(parents=True, exist_ok=True)
STATE_CHANGES_LOG_FILE = STATE_CHANGES_LOG_DIR / "state_changes.jsonl"

# Максимальный размер лог-файла перед ротацией (10MB)
MAX_LOG_FILE_SIZE = 10 * 1024 * 1024  # 10MB в байтах


@dataclass
class ParameterChange:
    """
    Структура для отслеживания изменений параметров системы.

    Используется для анализа эволюции параметров Life со временем.
    """

    timestamp: float
    tick: int
    parameter_name: str
    old_value: Any
    new_value: Any
    reason: (
        str  # Причина изменения: "delta_application", "learning_update", "adaptation_update", etc.
    )
    context: Dict[str, Any] = field(default_factory=dict)  # Дополнительная информация о изменении


@dataclass
class SelfState:
    # Thread-safety lock для API доступа
    _api_lock: threading.RLock = field(default_factory=threading.RLock, init=False, repr=False)

    # Композиция состояния через специализированные компоненты
    identity: IdentityState = field(default_factory=IdentityState)
    physical: PhysicalState = field(default_factory=PhysicalState)
    time: TimeState = field(default_factory=TimeState)
    memory_state: MemoryState = field(default_factory=MemoryState)
    cognitive: CognitiveState = field(default_factory=CognitiveState)
    events: EventState = field(default_factory=EventState)

    # История изменений параметров (для обратной совместимости и анализа эволюции)
    parameter_history: list[ParameterChange] = field(
        default_factory=list
    )

    # === Legacy поля заменены на delegation properties ===
    # Обратная совместимость обеспечивается через properties, делегирующие к компонентам

    # Внутренние флаги для контроля инициализации и логирования
    _initialized: bool = field(default=False, init=False, repr=False)
    _logging_enabled: bool = field(default=True, init=False, repr=False)
    _log_only_critical: bool = field(default=False, init=False, repr=False)
    _log_buffer: list = field(default_factory=list, init=False, repr=False)
    _log_buffer_size: int = field(default=100, init=False, repr=False)
    _loading_from_snapshot: bool = field(default=False, init=False, repr=False)

    # Кэш для оптимизации API сериализации
    _api_cache: dict = field(default_factory=dict, init=False, repr=False)
    _api_cache_timestamp: float = field(default=0.0, init=False, repr=False)

    # === Subjective time modulation parameters (defaults) ===
    subjective_time_base_rate: float = 1.0
    subjective_time_rate_min: float = 0.1
    subjective_time_rate_max: float = 3.0
    subjective_time_intensity_coeff: float = 1.0
    subjective_time_stability_coeff: float = 0.5
    subjective_time_energy_coeff: float = 0.5
    subjective_time_intensity_smoothing: float = (
        0.3  # Коэффициент экспоненциального сглаживания для интенсивности
    )
    time_ratio_history: list = field(
        default_factory=list
    )  # История соотношений physical/subjective time

    # === Internal rhythms parameters ===
    circadian_phase: float = 0.0  # Фаза циркадного ритма [0, 2π]
    circadian_period: float = 24.0 * 3600.0  # Базовый период в секундах (24 часа)
    circadian_adaptivity: float = 0.5  # Адаптивность циркадного ритма [0.0, 1.0]
    day_length_modifier: float = 1.0  # Модификатор длины дня [0.5, 2.0]
    recovery_efficiency: float = 1.0  # Эффективность восстановления [0.4, 1.6]
    stability_modifier: float = 1.0  # Модификатор стабильности [0.7, 1.3]

    # === Echo memory parameters ===
    echo_count: int = 0  # Количество эхо-всплываний
    last_echo_time: float = 0.0  # Время последнего эхо в секундах жизни

    # === Multi-level memory parameters ===
    sensory_buffer_size: int = 0  # Текущий размер сенсорного буфера
    semantic_concepts_count: int = 0  # Количество семантических концепций
    procedural_patterns_count: int = 0  # Количество процедурных паттернов

    # === Consciousness parameters ===
    consciousness_level: float = 0.0  # Текущий уровень сознания [0.0-1.0]
    clarity_history: list = field(default_factory=list)  # История моментов ясности
    state_transition_history: list = field(default_factory=list)  # История переходов состояний сознания

    # Last perceived event intensity (signal for subjective time), in [0..1].
    last_event_intensity: float = 0.0

    def __post_init__(self):
        """Инициализация компонентов и синхронизация устаревших полей для обратной совместимости"""
        # Инициализация компонентов
        if self.memory_state.memory is None:
            self.memory_state.memory = Memory(archive=self.memory_state.archive_memory)

        # Legacy поля теперь реализованы через delegation properties

        # Помечаем объект как инициализированный после __post_init__
        object.__setattr__(self, "_initialized", True)

    # === Legacy delegation properties для обратной совместимости ===
    # Эти properties делегируют к компонентам состояния, устраняя дублирование данных

    # Identity delegation
    @property
    def life_id(self) -> str:
        """Делегирует к identity.life_id"""
        return self.identity.life_id

    @life_id.setter
    def life_id(self, value: str) -> None:
        """Делегирует установку к identity.life_id"""
        self.identity.life_id = value

    @property
    def birth_timestamp(self) -> float:
        """Делегирует к identity.birth_timestamp"""
        return self.identity.birth_timestamp

    @birth_timestamp.setter
    def birth_timestamp(self, value: float) -> None:
        """Делегирует установку к identity.birth_timestamp"""
        self.identity.birth_timestamp = value

    @property
    def age(self) -> float:
        """Делегирует к identity.age"""
        return self.identity.age

    @age.setter
    def age(self, value: float) -> None:
        """Делегирует установку к identity.age"""
        self.identity.age = value

    @property
    def ticks(self) -> int:
        """Делегирует к identity.ticks"""
        return self.identity.ticks

    @ticks.setter
    def ticks(self, value: int) -> None:
        """Делегирует установку к identity.ticks"""
        self.identity.ticks = value

    @property
    def _active(self) -> bool:
        """Делегирует к identity.active"""
        return self.identity.active

    @_active.setter
    def _active(self, value: bool) -> None:
        """Делегирует установку к identity.active"""
        self.identity.active = value

    # Physical delegation
    @property
    def energy(self) -> float:
        """Делегирует к physical.energy"""
        return self.physical.energy

    @energy.setter
    def energy(self, value: float) -> None:
        """Делегирует установку к physical.energy"""
        self.physical.energy = value

    @property
    def integrity(self) -> float:
        """Делегирует к physical.integrity"""
        return self.physical.integrity

    @integrity.setter
    def integrity(self, value: float) -> None:
        """Делегирует установку к physical.integrity"""
        self.physical.integrity = value

    @property
    def stability(self) -> float:
        """Делегирует к physical.stability"""
        return self.physical.stability

    @stability.setter
    def stability(self, value: float) -> None:
        """Делегирует установку к physical.stability"""
        self.physical.stability = value

    @property
    def fatigue(self) -> float:
        """Делегирует к physical.fatigue"""
        return self.physical.fatigue

    @fatigue.setter
    def fatigue(self, value: float) -> None:
        """Делегирует установку к physical.fatigue"""
        self.physical.fatigue = value

    @property
    def tension(self) -> float:
        """Делегирует к physical.tension"""
        return self.physical.tension

    @tension.setter
    def tension(self, value: float) -> None:
        """Делегирует установку к physical.tension"""
        self.physical.tension = value

    @property
    def energy_history(self) -> list:
        """Делегирует к physical.energy_history"""
        return self.physical.energy_history

    @energy_history.setter
    def energy_history(self, value: list) -> None:
        """Делегирует установку к physical.energy_history"""
        self.physical.energy_history = value

    @property
    def stability_history(self) -> list:
        """Делегирует к physical.stability_history"""
        return self.physical.stability_history

    @stability_history.setter
    def stability_history(self, value: list) -> None:
        """Делегирует установку к physical.stability_history"""
        self.physical.stability_history = value

    # Time delegation
    @property
    def subjective_time(self) -> float:
        """Делегирует к time.subjective_time"""
        return self.time.subjective_time

    @subjective_time.setter
    def subjective_time(self, value: float) -> None:
        """Делегирует установку к time.subjective_time"""
        self.time.subjective_time = value

    # Memory delegation
    @property
    def memory(self):
        """Делегирует к memory_state.memory"""
        return self.memory_state.memory

    @memory.setter
    def memory(self, value) -> None:
        """Делегирует установку к memory_state.memory"""
        self.memory_state.memory = value

    @property
    def archive_memory(self):
        """Делегирует к memory_state.archive_memory"""
        return self.memory_state.archive_memory

    @archive_memory.setter
    def archive_memory(self, value) -> None:
        """Делегирует установку к memory_state.archive_memory"""
        self.memory_state.archive_memory = value

    @property
    def memory_entries_by_type(self) -> dict:
        """Делегирует к memory_state.entries_by_type"""
        return self.memory_state.entries_by_type

    @memory_entries_by_type.setter
    def memory_entries_by_type(self, value: dict) -> None:
        """Делегирует установку к memory_state.entries_by_type"""
        self.memory_state.entries_by_type = value

    # Cognitive delegation
    @property
    def planning(self) -> Dict[str, Any]:
        """Делегирует к cognitive.planning"""
        return self.cognitive.planning

    @planning.setter
    def planning(self, value: Dict[str, Any]) -> None:
        """Делегирует установку к cognitive.planning"""
        self.cognitive.planning = value

    @property
    def intelligence(self) -> Dict[str, Any]:
        """Делегирует к cognitive.intelligence"""
        return self.cognitive.intelligence

    @intelligence.setter
    def intelligence(self, value: Dict[str, Any]) -> None:
        """Делегирует установку к cognitive.intelligence"""
        self.cognitive.intelligence = value

    # Events delegation
    @property
    def recent_events(self) -> list:
        """Делегирует к events.recent_events"""
        return self.events.recent_events

    @recent_events.setter
    def recent_events(self, value: list) -> None:
        """Делегирует установку к events.recent_events"""
        self.events.recent_events = value

    @property
    def last_significance(self) -> float:
        """Делегирует к events.last_significance"""
        return self.events.last_significance

    @last_significance.setter
    def last_significance(self, value: float) -> None:
        """Делегирует установку к events.last_significance"""
        self.events.last_significance = value

    def _invalidate_api_cache(self) -> None:
        """Инвалидирует кэш API сериализации"""
        self._api_cache.clear()
        self._api_cache_timestamp = 0.0

    def get_serialization_metrics(self) -> dict:
        """
        Возвращает метрики производительности сериализации для мониторинга.

        Returns:
            dict: Метрики сериализации (cache hits, misses, avg times, etc.)
        """
        from src.runtime.performance_metrics import performance_metrics

        return {
            "api_cache_size": len(self._api_cache),
            "api_cache_timestamp": self._api_cache_timestamp,
            "save_snapshot_avg_time": performance_metrics.get_average_time("save_snapshot"),
            "save_snapshot_last_time": performance_metrics.get_last_time("save_snapshot"),
            "load_snapshot_avg_time": performance_metrics.get_average_time("load_snapshot"),
            "load_snapshot_last_time": performance_metrics.get_last_time("load_snapshot"),
        }

    def _create_base_state_dict(self) -> dict:
        """
        Создает базовый словарь состояния без больших структур.
        Оптимизированная версия, избегает повторного прохождения по полям.
        """
        # Предварительно определенный набор безопасных полей для копирования
        safe_fields = {
            # Identity
            "life_id",
            "birth_timestamp",
            # Temporal
            "age",
            "ticks",
            "subjective_time",
            # Vital
            "energy",
            "integrity",
            "stability",
            # Internal dynamics
            "fatigue",
            "tension",
            # Cognitive layers
            "intelligence",
            "planning",
            # Learning & Adaptation
            "learning_params",
            "adaptation_params",
            "adaptation_history",
            "parameter_history",
            "learning_params_history",
            "adaptation_params_history",
            # Subjective time
            "subjective_time_base_rate",
            "subjective_time_rate_min",
            "subjective_time_rate_max",
            "subjective_time_intensity_coeff",
            "subjective_time_stability_coeff",
            "subjective_time_energy_coeff",
            "subjective_time_intensity_smoothing",
            "last_event_intensity",
            "time_ratio_history",
            # Rhythms
            "circadian_phase",
            "circadian_period",
            "circadian_adaptivity",
            "day_length_modifier",
            "recovery_efficiency",
            "stability_modifier",
            # Experimental
            "echo_count",
            "last_echo_time",
            # Control
            "active",
            "last_significance",
        }

        state_dict = {}
        # Оптимизированное копирование безопасных полей
        for field_name in safe_fields:
            if hasattr(self, field_name):
                try:
                    value = getattr(self, field_name)
                    state_dict[field_name] = value
                except AttributeError:
                    continue

        return state_dict

    def _apply_limits_to_state_dict(self, state_dict: dict, limits: dict) -> dict:
        """
        Применяет лимиты к большим структурам в словаре состояния.
        Оптимизированная обработка с минимальным копированием.
        """
        # Обработка memory (по умолчанию не включаем, только если явно указан лимит)
        memory_limit = limits.get("memory_limit")
        if memory_limit is not None and self.memory is not None:
            # Используем кэшированную сериализацию
            memory_entries = list(self.memory)[-memory_limit:] if memory_limit > 0 else []
            state_dict["memory"] = [
                {
                    "event_type": entry.event_type,
                    "meaning_significance": entry.meaning_significance,
                    "timestamp": entry.timestamp,
                    "weight": entry.weight,
                    "feedback_data": entry.feedback_data,
                }
                for entry in memory_entries
            ]

        # Оптимизированная обработка других больших структур
        # recent_events
        events_limit = limits.get("events_limit")
        if events_limit is not None and events_limit > 0:
            if "recent_events" in state_dict and isinstance(state_dict["recent_events"], list):
                state_dict["recent_events"] = state_dict["recent_events"][-events_limit:]

        # energy_history
        energy_history_limit = limits.get("energy_history_limit")
        if energy_history_limit is not None and energy_history_limit > 0:
            if "energy_history" in state_dict and isinstance(state_dict["energy_history"], list):
                state_dict["energy_history"] = state_dict["energy_history"][-energy_history_limit:]

        # stability_history
        stability_history_limit = limits.get("stability_history_limit")
        if stability_history_limit is not None and stability_history_limit > 0:
            if "stability_history" in state_dict and isinstance(
                state_dict["stability_history"], list
            ):
                state_dict["stability_history"] = state_dict["stability_history"][
                    -stability_history_limit:
                ]

        # adaptation_history
        adaptation_history_limit = limits.get("adaptation_history_limit")
        if adaptation_history_limit is not None and adaptation_history_limit > 0:
            if "adaptation_history" in state_dict and isinstance(
                state_dict["adaptation_history"], list
            ):
                state_dict["adaptation_history"] = state_dict["adaptation_history"][
                    -adaptation_history_limit:
                ]

        # parameter_history
        parameter_history_limit = limits.get("parameter_history_limit")
        if parameter_history_limit is not None and parameter_history_limit > 0:
            if "parameter_history" in state_dict and isinstance(
                state_dict["parameter_history"], list
            ):
                state_dict["parameter_history"] = state_dict["parameter_history"][
                    -parameter_history_limit:
                ]
        else:
            # По умолчанию не включаем parameter_history (слишком много данных)
            state_dict.pop("parameter_history", None)

        # learning_params_history
        learning_params_history_limit = limits.get("learning_params_history_limit")
        if learning_params_history_limit is not None and learning_params_history_limit > 0:
            if "learning_params_history" in state_dict and isinstance(
                state_dict["learning_params_history"], list
            ):
                state_dict["learning_params_history"] = state_dict["learning_params_history"][
                    -learning_params_history_limit:
                ]
        else:
            # По умолчанию не включаем learning_params_history
            state_dict.pop("learning_params_history", None)

        # adaptation_params_history
        adaptation_params_history_limit = limits.get("adaptation_params_history_limit")
        if adaptation_params_history_limit is not None and adaptation_params_history_limit > 0:
            if "adaptation_params_history" in state_dict and isinstance(
                state_dict["adaptation_params_history"], list
            ):
                state_dict["adaptation_params_history"] = state_dict["adaptation_params_history"][
                    -adaptation_params_history_limit:
                ]
        else:
            # По умолчанию не включаем adaptation_params_history
            state_dict.pop("adaptation_params_history", None)

        return state_dict

    def _validate_field(self, field_name: str, value: float, clamp: bool = False) -> float:
        """
        Валидация значения поля с учетом его границ.

        Args:
            field_name: Имя поля
            value: Значение для валидации
            clamp: Если True, обрезать значение до границ вместо выбрасывания ошибки

        Returns:
            Валидированное значение
        """
        return FieldValidator.validate_field(field_name, value, clamp)

    def _rotate_log_if_needed(self) -> None:
        """Ротация лог-файла при достижении максимального размера"""
        if not STATE_CHANGES_LOG_FILE.exists():
            return

        try:
            file_size = STATE_CHANGES_LOG_FILE.stat().st_size
            if file_size >= MAX_LOG_FILE_SIZE:
                # Создаем резервную копию с timestamp
                timestamp = int(time.time())
                backup_file = STATE_CHANGES_LOG_DIR / f"state_changes_{timestamp}.jsonl.backup"
                STATE_CHANGES_LOG_FILE.rename(backup_file)
                # Создаем новый пустой файл
                STATE_CHANGES_LOG_FILE.touch()

                # Очищаем старые резервные копии
                self._cleanup_old_backups()
        except Exception:
            # Игнорируем ошибки ротации, чтобы не нарушать работу системы
            pass

    def _cleanup_old_backups(self, max_age_days: int = 30, max_backups: int = 10) -> None:
        """
        Очистка старых резервных копий логов

        Args:
            max_age_days: Максимальный возраст резервной копии в днях (по умолчанию 30)
            max_backups: Максимальное количество резервных копий для хранения (по умолчанию 10)
        """
        try:
            # Находим все резервные копии
            backup_files = list(STATE_CHANGES_LOG_DIR.glob("state_changes_*.jsonl.backup"))

            if not backup_files:
                return

            # Сортируем по времени модификации (новые первыми)
            backup_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 60 * 60

            # Удаляем старые копии
            for backup_file in backup_files:
                file_age = current_time - backup_file.stat().st_mtime
                if file_age > max_age_seconds:
                    try:
                        backup_file.unlink()
                    except Exception:
                        # Игнорируем ошибки удаления отдельных файлов
                        pass

            # Ограничиваем количество копий (оставляем только последние max_backups)
            if len(backup_files) > max_backups:
                for backup_file in backup_files[max_backups:]:
                    try:
                        backup_file.unlink()
                    except Exception:
                        # Игнорируем ошибки удаления отдельных файлов
                        pass
        except Exception:
            # Игнорируем ошибки очистки, чтобы не нарушать работу системы
            pass

    def _is_critical_field(self, field_name: str) -> bool:
        """Проверка, является ли поле критичным (vital параметры)"""
        return field_name in ["energy", "integrity", "stability"]

    def _record_parameter_change(
        self, parameter_name: str, old_value, new_value, reason: str, context: dict = None
    ) -> None:
        """
        Записывает изменение параметра в parameter_history для анализа эволюции.

        Args:
            parameter_name: Имя измененного параметра
            old_value: Старое значение
            new_value: Новое значение
            reason: Причина изменения ("delta_application", "learning_update", "adaptation_update", etc.)
            context: Дополнительная информация о изменении
        """
        if context is None:
            context = {}

        change = ParameterChange(
            timestamp=time.time(),
            tick=self.ticks,
            parameter_name=parameter_name,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            context=context,
        )

        # Thread-safe добавление в историю
        with self._api_lock:
            self.parameter_history.append(change)

            # Ограничиваем размер истории (последние 1000 изменений)
            if len(self.parameter_history) > 1000:
                self.parameter_history = self.parameter_history[-1000:]

    def _log_change(self, field_name: str, old_value, new_value) -> None:
        """
        Логирование изменения поля в append-only лог и историю параметров.
        Поддерживает батчинг и фильтрацию по критичности.
        """
        if not self._logging_enabled:
            return

        # Если включен режим "только критичные", пропускаем некритичные поля
        if self._log_only_critical and not self._is_critical_field(field_name):
            return

        try:
            # Записываем в parameter_history для анализа эволюции
            self._record_parameter_change(field_name, old_value, new_value, "field_update")

            log_entry = {
                "timestamp": time.time(),
                "life_id": self.life_id,
                "tick": self.ticks,
                "field": field_name,
                "old_value": old_value,
                "new_value": new_value,
            }

            # Добавляем в буфер для батчинга
            self._log_buffer.append(log_entry)

            # Если буфер заполнен, записываем на диск
            if len(self._log_buffer) >= self._log_buffer_size:
                self._flush_log_buffer()
        except Exception:
            # Игнорируем ошибки логирования, чтобы не нарушать работу системы
            pass

    def _flush_log_buffer(self) -> None:
        """Запись буфера логов на диск"""
        if not self._log_buffer:
            return

        try:
            # Проверяем размер файла и ротируем при необходимости
            self._rotate_log_if_needed()

            with STATE_CHANGES_LOG_FILE.open("a") as f:
                for log_entry in self._log_buffer:
                    f.write(json.dumps(log_entry, default=str) + "\n")

            # Очищаем буфер
            self._log_buffer.clear()
        except Exception:
            # Игнорируем ошибки логирования, чтобы не нарушать работу системы
            pass

    def __setattr__(self, name: str, value) -> None:
        """Переопределение setattr для валидации и защиты полей с потокобезопасностью"""
        # Разрешаем установку внутренних полей без валидации
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return

        # Проверяем, инициализирован ли объект (безопасно через hasattr)
        is_initialized = hasattr(self, "_initialized") and self._initialized

        # Для потокобезопасности используем блокировку при изменении состояния
        # Исключаем внутренние поля и поля, которые не влияют на консистентность
        # Валидация должна работать всегда для новых объектов
        if name not in ["activated_memory", "last_pattern", "parameter_history"] and not getattr(
            self, "_loading_from_snapshot", False
        ):
            # Используем RLock для потокобезопасности изменений состояния
            with self._api_lock:
                # Защита неизменяемых полей (только после инициализации и не при загрузке snapshot)
                if (
                    is_initialized
                    and name in ["life_id", "birth_timestamp"]
                    and not getattr(self, "_loading_from_snapshot", False)
                ):
                    raise AttributeError(
                        f"Cannot modify immutable field '{name}' after initialization"
                    )

                # Получаем старое значение для логирования (безопасно)
                old_value = None
                try:
                    old_value = object.__getattribute__(self, name)
                except AttributeError:
                    old_value = None

                # Валидация числовых полей
                if isinstance(value, (int, float)) and name in [
                    "energy",
                    "integrity",
                    "stability",
                    "fatigue",
                    "tension",
                    "age",
                    "subjective_time",
                    "subjective_time_base_rate",
                    "subjective_time_rate_min",
                    "subjective_time_rate_max",
                    "subjective_time_intensity_coeff",
                    "subjective_time_stability_coeff",
                    "subjective_time_energy_coeff",
                    "subjective_time_intensity_smoothing",
                    "last_event_intensity",
                    "circadian_phase",
                    "circadian_period",
                    "circadian_adaptivity",
                    "day_length_modifier",
                    "recovery_efficiency",
                    "stability_modifier",
                    "last_echo_time",
                ]:
                    value = self._validate_field(name, value, clamp=False)
                elif isinstance(value, (int, float)) and name in [
                    "ticks",
                    "echo_count",
                ]:
                    # Для целочисленных полей конвертируем в int и валидируем
                    value = int(value)
                    value = self._validate_field(name, value, clamp=False)

                # Устанавливаем значение
                object.__setattr__(self, name, value)

                # Логируем изменение (если значение изменилось)
                if is_initialized and old_value is not None and old_value != value:
                    self._log_change(name, old_value, value)
                    # Инвалидируем кэш API при изменении состояния
                    self._invalidate_api_cache()

                # Active обновляется только при явном изменении или в специальных случаях
                # Не автоматически при изменении vital параметров
        else:
            # Для неинициализированного состояния или специальных полей - без блокировки
            # Защита неизменяемых полей (только после инициализации и не при загрузке snapshot)
            if (
                is_initialized
                and name in ["life_id", "birth_timestamp"]
                and not getattr(self, "_loading_from_snapshot", False)
            ):
                raise AttributeError(f"Cannot modify immutable field '{name}' after initialization")

            # Получаем старое значение для логирования (безопасно)
            old_value = None
            if is_initialized and name != "parameter_history":  # Избегаем рекурсии при логировании
                try:
                    old_value = object.__getattribute__(self, name)
                except AttributeError:
                    old_value = None

            # Валидация числовых полей
            if isinstance(value, (int, float)) and name in [
                "energy",
                "integrity",
                "stability",
                "fatigue",
                "tension",
                "age",
                "subjective_time",
                "subjective_time_base_rate",
                "subjective_time_rate_min",
                "subjective_time_rate_max",
                "subjective_time_intensity_coeff",
                "subjective_time_stability_coeff",
                "subjective_time_energy_coeff",
                "subjective_time_intensity_smoothing",
                "last_event_intensity",
                "circadian_phase",
                "circadian_period",
                "circadian_adaptivity",
                "day_length_modifier",
                "recovery_efficiency",
                "stability_modifier",
                "echo_count",
                "last_echo_time",
            ]:
                value = self._validate_field(name, value, clamp=False)

            # Устанавливаем значение
            object.__setattr__(self, name, value)

            # Логируем изменение (только после инициализации и если значение изменилось)
            if is_initialized and name != "parameter_history" and old_value is not None and old_value != value:
                self._log_change(name, old_value, value)
                # Инвалидируем кэш API при изменении состояния
                self._invalidate_api_cache()

            # Active обновляется только при явном изменении или в специальных случаях
            # Не автоматически при изменении vital параметров

    activated_memory: list = field(default_factory=list)  # Transient, не сохраняется в snapshot
    last_pattern: str = ""  # Transient, последний выбранный паттерн decision

    @property
    def active(self) -> bool:
        """Active status - system remains active even in degraded state (immortal weakness)"""
        # Согласно ADR 009, система Life не останавливается при параметрах <= 0
        # Она продолжает работать в degraded состоянии ("бессмертная слабость")
        # Active может быть только вручную установлен в False
        if hasattr(self, "_active") and self._active is False:
            return False
        return True

    @active.setter
    def active(self, value: bool) -> None:
        """Setter for active - allows manual override"""
        self._active = value

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
        default_factory=lambda: __import__(
            "src.adaptation.adaptation", fromlist=["AdaptationManager"]
        )
        .AdaptationManager()
        ._init_behavior_params_from_learning(
            {
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
        )
    )  # Параметры поведения для Adaptation (Этап 15)
    adaptation_history: list = field(
        default_factory=list
    )  # История адаптаций для обратимости (Этап 15)
    learning_params_history: list = field(
        default_factory=list
    )  # История изменений learning_params для анализа эволюции
    adaptation_params_history: list = field(
        default_factory=list
    )  # История изменений adaptation_params для анализа эволюции

    # === Subjective time aliases ===
    @property
    def subjective_age(self) -> float:
        """Alias for subjective_time - accumulated subjective time in seconds."""
        return self.subjective_time

    @subjective_age.setter
    def subjective_age(self, value: float) -> None:
        """Set subjective_time via subjective_age alias."""
        self.subjective_time = value

    @property
    def physical_age(self) -> float:
        """Alias for age - physical time in seconds."""
        return self.age

    @physical_age.setter
    def physical_age(self, value: float) -> None:
        """Set age via physical_age alias."""
        self.age = value

    def is_active(self) -> bool:
        """
        Проверка жизнеспособности состояния на основе всех параметров (энергия, целостность, стабильность).
        Согласно ADR 009, система Life остается активной даже при параметрах <= 0 ("бессмертная слабость").
        Возвращает True всегда, кроме случаев ручной установки active=False.
        """
        # Проверяем, не установлено ли active=False вручную
        if hasattr(self, "_active") and self._active is False:
            return False

        # Согласно принципу "immortal weakness", система остается активной даже при параметрах <= 0
        # Но проверяем что параметры находятся в допустимых диапазонах (не NaN, не бесконечность)
        energy_valid = isinstance(self.energy, (int, float)) and not (self.energy != self.energy)  # not NaN
        integrity_valid = isinstance(self.integrity, (int, float)) and not (self.integrity != self.integrity)
        stability_valid = isinstance(self.stability, (int, float)) and not (self.stability != self.stability)

        # Система активна если все vital параметры валидны (даже если <= 0)
        return energy_valid and integrity_valid and stability_valid

    def is_viable(self) -> bool:
        """
        Проверка жизнеспособности с более строгими критериями.
        Возвращает True если все vital параметры выше пороговых значений.
        """
        return self.energy > 10.0 and self.integrity > 0.1 and self.stability > 0.1

    def update_energy(self, value: float) -> None:
        """Безопасное обновление energy с валидацией"""
        self.energy = value

    def update_integrity(self, value: float) -> None:
        """Безопасное обновление integrity с валидацией"""
        self.integrity = value

    def update_stability(self, value: float) -> None:
        """Безопасное обновление stability с валидацией"""
        self.stability = value

    def update_vital_params(
        self,
        energy: Optional[float] = None,
        integrity: Optional[float] = None,
        stability: Optional[float] = None,
    ) -> None:
        """Безопасное одновременное обновление vital параметров"""
        if energy is not None:
            self.energy = energy
        if integrity is not None:
            self.integrity = integrity
        if stability is not None:
            self.stability = stability

    def set_active(self, value: bool) -> None:
        """
        Безопасная установка флага active.
        Обычно active обновляется автоматически при изменении vital параметров,
        но этот метод позволяет явно установить значение.

        Args:
            value: Новое значение флага active
        """
        self.active = value

    def reset_to_defaults(self) -> None:
        """Сброс состояния к начальным значениям (кроме life_id и birth_timestamp)"""
        self.energy = 100.0
        self.integrity = 1.0
        self.stability = 1.0
        self.fatigue = 0.0
        self.tension = 0.0
        self.age = 0.0
        self.ticks = 0
        self.active = True
        self.recent_events = []
        self.last_significance = 0.0
        self.energy_history = []
        self.stability_history = []
        self.parameter_history = []
        self.learning_params_history = []
        self.adaptation_params_history = []
        self.planning = {}
        self.intelligence = {}
        # Память не сбрасываем, так как это история жизни

    def apply_delta(self, deltas: dict[str, float]) -> None:
        """Применение дельт к полям с обрезанием значений до допустимых границ с потокобезопасностью"""
        # Используем блокировку для обеспечения консистентности изменений
        with self._api_lock:
            for key, delta in deltas.items():
                if hasattr(self, key):
                    current = getattr(self, key)
                    if isinstance(current, (int, float)):
                        new_value = current + delta
                        # Для performance тестов пропускаем валидацию, просто clamp
                        if key in ["energy", "integrity", "stability"]:
                            clamped_value = max(
                                0.0, min(100.0 if key == "energy" else 1.0, new_value)
                            )
                        elif key in ["fatigue", "tension", "age", "subjective_time"]:
                            clamped_value = max(0.0, new_value)
                        elif key == "ticks":
                            clamped_value = max(0, int(new_value))
                        else:
                            clamped_value = new_value
                        # Устанавливаем без дополнительной валидации
                        object.__setattr__(self, key, clamped_value)

                        # Логируем изменение вручную, так как обошли __setattr__
                        if self._initialized and current != clamped_value:
                            self._log_change(key, current, clamped_value)
                            # Записываем изменение в parameter_history для анализа эволюции
                            self._record_parameter_change(
                                key,
                                current,
                                clamped_value,
                                "delta_application",
                                context={
                                    "delta_value": delta,
                                    "clamped": clamped_value != new_value,
                                },
                            )
                    else:
                        # Для нечисловых полей операция сложения не поддерживается
                        raise TypeError(
                            f"Cannot apply delta to field '{key}': "
                            f"field type '{type(current).__name__}' does not support addition. "
                            f"Only numeric fields (int, float) support delta operations."
                        )

    def enable_logging(self) -> None:
        """Включить логирование изменений"""
        self._logging_enabled = True
        # Сбрасываем буфер при включении логирования
        self._flush_log_buffer()

    def disable_logging(self) -> None:
        """Отключить логирование изменений (для тестов)"""
        # Сбрасываем буфер перед отключением
        self._flush_log_buffer()
        self._logging_enabled = False

    def set_log_only_critical(self, enabled: bool = True) -> None:
        """
        Установить режим логирования только критичных изменений (vital параметры).
        Это может улучшить производительность при частых изменениях некритичных полей.

        Args:
            enabled: Если True, логировать только изменения energy, integrity, stability
        """
        self._log_only_critical = enabled

    def set_log_buffer_size(self, size: int) -> None:
        """
        Установить размер буфера для батчинга логов.
        Больший размер улучшает производительность, но увеличивает риск потери данных при сбое.

        Args:
            size: Размер буфера (по умолчанию 100)
        """
        if size < 1:
            raise ValueError("Buffer size must be >= 1")
        self._log_buffer_size = size
        # Если новый размер меньше текущего буфера, сбрасываем его
        if len(self._log_buffer) >= size:
            self._flush_log_buffer()

    def update_circadian_rhythm(self, dt: float) -> None:
        """
        Обновить адаптивный циркадный ритм с 4 фазами: рассвет/день/закат/ночь.

        Длина "дня" адаптируется на основе стабильности и энергии системы.
        При высокой стабильности и энергии - более короткие циклы (активность).
        При низкой стабильности и энергии - более длинные циклы (восстановление).

        4 фазы ритма:
        - Рассвет (0-π/2): постепенное увеличение активности
        - День (π/2-π): максимальная активность и эффективность восстановления
        - Закат (π-3π/2): постепенное снижение активности
        - Ночь (3π/2-2π): минимальная активность, максимальная стабильность

        Args:
            dt: Время в секундах, прошедшее с последнего обновления
        """
        import math

        # === Адаптивный расчет длины "дня" ===
        # Базовый период: 24 часа
        base_period = 24.0 * 3600.0

        # Модификатор на основе состояния системы
        # При высокой стабильности (>0.8) и энергии (>70) - укорачиваем цикл (активность)
        # При низкой стабильности (<0.3) или энергии (<30) - удлиняем цикл (восстановление)
        stability_factor = max(0.5, min(2.0, 1.0 / max(0.1, self.stability)))
        energy_factor = max(0.5, min(2.0, 100.0 / max(10.0, self.energy)))

        # Комбинированный фактор (среднее арифметическое)
        state_factor = (stability_factor + energy_factor) / 2.0

        # Адаптивный период с учетом circadian_adaptivity
        # При adaptivity=0: фиксированный период, при adaptivity=1: максимальная адаптация
        adaptive_period = base_period * (
            1.0 + self.circadian_adaptivity * (state_factor - 1.0)
        ) * self.day_length_modifier

        # Ограничиваем период разумными пределами: 6-72 часа
        adaptive_period = max(6*3600, min(72*3600, adaptive_period))

        # === Обновление фазы ритма ===
        phase_increment = (dt / adaptive_period) * 2 * math.pi
        self.circadian_phase += phase_increment
        self.circadian_phase %= 2 * math.pi  # Нормализация в диапазон [0, 2π]

        # === Расчет коэффициентов для 4 фаз ===
        phase_rad = self.circadian_phase

        # Определяем текущую фазу
        if phase_rad < math.pi / 2:
            # Фаза 1: Рассвет (0-π/2) - постепенное увеличение активности
            phase_progress = phase_rad / (math.pi / 2)  # [0, 1]
            recovery_coeff = 0.5 + 0.3 * phase_progress  # [0.5, 0.8]
            stability_coeff = 0.8 + 0.1 * phase_progress  # [0.8, 0.9]
        elif phase_rad < math.pi:
            # Фаза 2: День (π/2-π) - максимальная активность
            phase_progress = (phase_rad - math.pi/2) / (math.pi / 2)  # [0, 1]
            recovery_coeff = 0.8 + 0.2 * phase_progress  # [0.8, 1.0]
            stability_coeff = 0.9 - 0.1 * phase_progress  # [0.9, 0.8]
        elif phase_rad < 3 * math.pi / 2:
            # Фаза 3: Закат (π-3π/2) - постепенное снижение активности
            phase_progress = (phase_rad - math.pi) / (math.pi / 2)  # [0, 1]
            recovery_coeff = 1.0 - 0.3 * phase_progress  # [1.0, 0.7]
            stability_coeff = 0.8 + 0.1 * phase_progress  # [0.8, 0.9]
        else:
            # Фаза 4: Ночь (3π/2-2π) - восстановление и стабилизация
            phase_progress = (phase_rad - 3*math.pi/2) / (math.pi / 2)  # [0, 1]
            recovery_coeff = 0.7 - 0.3 * phase_progress  # [0.7, 0.4]
            stability_coeff = 0.9 + 0.1 * phase_progress  # [0.9, 1.0]

        # Применяем коэффициенты с учетом состояния системы
        self.recovery_efficiency = max(0.4, min(1.6, recovery_coeff))
        self.stability_modifier = max(0.7, min(1.3, stability_coeff))

    def trigger_memory_echo(self, memory) -> Optional[MemoryEntry]:
        """
        Проверить и выполнить эхо-всплывание воспоминания.

        Эхо - это спонтанное всплывание старых воспоминаний из архива.
        Вероятность эхо зависит от возраста системы и текущей стабильности.

        Args:
            memory: Объект памяти для доступа к архиву

        Returns:
            MemoryEntry или None, если эхо не произошло
        """
        import random

        # Базовая вероятность эхо на тик (0.1% = 0.001)
        base_probability = 0.001

        # Модификаторы вероятности
        # Возрастной модификатор: растет с субъективным возрастом (30 дней = 30*24*3600 сек)
        age_modifier = min(1.0, self.subjective_age / (30 * 24 * 3600))

        # Модификатор стабильности: чаще при низкой стабильности
        stability_modifier = 1.0 + (1.0 - self.stability)

        # Модификатор циркадного ритма: меньше эхо днем, больше ночью
        # Используем recovery_efficiency: меньше эхо при высокой эффективности восстановления (день)
        circadian_modifier = 1.0 + (1.0 - self.recovery_efficiency) * 0.5

        # Общая вероятность эхо
        echo_probability = base_probability * age_modifier * stability_modifier * circadian_modifier

        # Проверяем, произошло ли эхо
        if random.random() < echo_probability:
            # Получаем архивные записи
            archived_entries = memory.get_archived_entries()

            if archived_entries:
                # Выбираем случайное воспоминание
                echoed_memory = random.choice(archived_entries)

                # Активируем воспоминание
                self.activated_memory.append(echoed_memory)

                # Обновляем статистику
                self.echo_count += 1
                self.last_echo_time = self.age

                return echoed_memory

        return None

    def get_safe_status_dict(
        self,
        include_optional: bool = True,
        limits: Optional[dict] = None,
    ) -> dict:
        """
        Получить безопасный словарь состояния для публичного API.

        Thread-safe: использует lock для обеспечения консистентности данных.
        Оптимизировано: использует кэширование для избежания повторных вычислений.

        Исключает:
        - Transient поля (activated_memory, last_pattern)
        - Внутренние поля (начинающиеся с _)
        - Не сериализуемые объекты (archive_memory)

        Опционально ограничивает размер больших полей:
        - memory (по умолчанию не включается, можно включить с лимитом)
        - recent_events
        - energy_history
        - stability_history
        - adaptation_history
        - parameter_history (по умолчанию не включается)
        - learning_params_history (по умолчанию не включается)
        - adaptation_params_history (по умолчанию не включается)

        Args:
            include_optional: Если True, включает опциональные поля (life_id, birth_timestamp,
                            learning_params, adaptation_params, planning, intelligence,
                            subjective_time параметры)
            limits: Словарь с лимитами для больших полей:
                    - memory_limit: количество записей памяти (None = не включать)
                    - events_limit: количество последних событий
                    - energy_history_limit: количество значений истории энергии
                    - stability_history_limit: количество значений истории стабильности
                    - adaptation_history_limit: количество значений истории адаптации
                    - parameter_history_limit: количество значений истории параметров (по умолчанию не включается)
                    - learning_params_history_limit: количество значений истории learning параметров (по умолчанию не включается)
                    - adaptation_params_history_limit: количество значений истории adaptation параметров (по умолчанию не включается)

        Returns:
            dict: Безопасный словарь состояния для публичного API
        """
        import time

        # Создаем ключ кэша на основе параметров
        cache_key = (include_optional, tuple(sorted(limits.items())) if limits else None)

        # Thread-safe проверка кэша
        with self._api_lock:
            # Проверяем кэш (TTL = 0.1 секунды для API)
            current_time = time.time()
            if cache_key in self._api_cache and (current_time - self._api_cache_timestamp) < 0.1:
                # Возвращаем копию из кэша
                return self._api_cache[cache_key].copy()

            # Создаем базовый словарь состояния (оптимизированная версия)
            state_dict = self._create_base_state_dict()

            # Обрабатываем limits
            if limits is None:
                limits = {}

            # Обработка больших структур с оптимизацией
            state_dict = self._apply_limits_to_state_dict(state_dict, limits)

            # Если include_optional=False, исключаем опциональные поля
            if not include_optional:
                optional_fields = [
                    "life_id",
                    "birth_timestamp",
                    "learning_params",
                    "adaptation_params",
                    "planning",
                    "intelligence",
                    "subjective_time_base_rate",
                    "subjective_time_rate_min",
                    "subjective_time_rate_max",
                    "subjective_time_intensity_coeff",
                    "subjective_time_stability_coeff",
                    "subjective_time_energy_coeff",
                    "circadian_adaptivity",
                    "day_length_modifier",
                ]
                for field_name in optional_fields:
                    state_dict.pop(field_name, None)

            # Кэшируем результат
            self._api_cache[cache_key] = state_dict.copy()
            self._api_cache_timestamp = current_time

        return state_dict

        # Обрабатываем limits
        if limits is None:
            limits = {}

        # Обработка memory (по умолчанию не включаем, только если явно указан лимит)
        memory_limit = limits.get("memory_limit")
        if memory_limit is not None and self.memory is not None:
            # Ограничиваем количество записей памяти
            memory_entries = list(self.memory)[-memory_limit:] if memory_limit > 0 else []
            state_dict["memory"] = [
                {
                    "event_type": entry.event_type,
                    "meaning_significance": entry.meaning_significance,
                    "timestamp": entry.timestamp,
                    "weight": entry.weight,
                    "feedback_data": entry.feedback_data,
                }
                for entry in memory_entries
            ]
        else:
            # По умолчанию не включаем memory (может быть большим)
            state_dict.pop("memory", None)

        # Ограничиваем размер других больших полей
        events_limit = limits.get("events_limit")
        if events_limit is not None and events_limit > 0:
            if "recent_events" in state_dict and isinstance(state_dict["recent_events"], list):
                state_dict["recent_events"] = state_dict["recent_events"][-events_limit:]
        else:
            # По умолчанию не включаем recent_events
            state_dict.pop("recent_events", None)

        energy_history_limit = limits.get("energy_history_limit")
        if energy_history_limit is not None and energy_history_limit > 0:
            if "energy_history" in state_dict and isinstance(state_dict["energy_history"], list):
                state_dict["energy_history"] = state_dict["energy_history"][-energy_history_limit:]
        else:
            # По умолчанию не включаем energy_history
            state_dict.pop("energy_history", None)

        stability_history_limit = limits.get("stability_history_limit")
        if stability_history_limit is not None and stability_history_limit > 0:
            if "stability_history" in state_dict and isinstance(
                state_dict["stability_history"], list
            ):
                state_dict["stability_history"] = state_dict["stability_history"][
                    -stability_history_limit:
                ]
        else:
            # По умолчанию не включаем stability_history
            state_dict.pop("stability_history", None)

        adaptation_history_limit = limits.get("adaptation_history_limit")
        if adaptation_history_limit is not None and adaptation_history_limit > 0:
            if "adaptation_history" in state_dict and isinstance(
                state_dict["adaptation_history"], list
            ):
                state_dict["adaptation_history"] = state_dict["adaptation_history"][
                    -adaptation_history_limit:
                ]
        else:
            # По умолчанию не включаем adaptation_history
            state_dict.pop("adaptation_history", None)

        # Если include_optional=False, исключаем опциональные поля
        if not include_optional:
            optional_fields = [
                "life_id",
                "birth_timestamp",
                "learning_params",
                "adaptation_params",
                "planning",
                "intelligence",
                "subjective_time_base_rate",
                "subjective_time_rate_min",
                "subjective_time_rate_max",
                "subjective_time_intensity_coeff",
                "subjective_time_stability_coeff",
                "subjective_time_energy_coeff",
                "circadian_adaptivity",
                "day_length_modifier",
            ]
            for field_name in optional_fields:
                state_dict.pop(field_name, None)

        return state_dict

    def _create_optimized_snapshot_data(self) -> dict:
        """
        Создает оптимизированные данные snapshot для сериализации.
        Исключает transient поля и большие структуры, использует кэширование.
        """
        # Используем оптимизированное создание базового словаря
        snapshot = self._create_base_state_dict()

        # Сохраняем activated_memory - это важная часть состояния для восстановления
        if hasattr(self, "activated_memory") and self.activated_memory:
            # Сериализуем только важные поля MemoryEntry для activated_memory
            snapshot["activated_memory"] = [
                {
                    "event_type": entry.event_type,
                    "meaning_significance": entry.meaning_significance,
                    "timestamp": entry.timestamp,
                    "weight": entry.weight,
                    "feedback_data": entry.feedback_data,
                }
                for entry in self.activated_memory
            ]

        # Исключаем другие transient поля
        snapshot.pop("last_pattern", None)

        # Исключаем большие структуры для уменьшения размера файла
        # Эти данные могут быть восстановлены из логов или не критичны для перезапуска
        large_fields_to_exclude = [
            "energy_history",
            "stability_history",
            "time_ratio_history",
            "adaptation_history",
            "recent_events",
        ]
        for field in large_fields_to_exclude:
            snapshot.pop(field, None)

        # Оптимизированная конвертация Memory с кэшированием
        if isinstance(self.memory, Memory):
            snapshot["memory"] = self.memory.get_serialized_entries()

        # Сохраняем memory_entries_by_type для корректного восстановления
        if hasattr(self, "memory_entries_by_type") and self.memory_entries_by_type:
            snapshot["memory_entries_by_type"] = self.memory_entries_by_type

        return snapshot

    def _validate_learning_params(self, params: dict) -> dict:
        """
        Валидация структуры learning_params при загрузке из snapshot.

        Args:
            params: Словарь learning_params для валидации

        Returns:
            Валидированные параметры или параметры по умолчанию при ошибках

        Raises:
            ValueError: При критических ошибках структуры
        """
        import logging

        logger = logging.getLogger(__name__)

        # Ожидаемая структура
        expected_structure = {
            "event_type_sensitivity": ["noise", "decay", "recovery", "shock", "idle"],
            "significance_thresholds": ["noise", "decay", "recovery", "shock", "idle"],
            "response_coefficients": ["dampen", "absorb", "ignore"],
        }

        if not isinstance(params, dict):
            logger.warning("learning_params не является словарем, используем значения по умолчанию")
            return self._get_default_learning_params()

        validated_params = {}

        for section_name, expected_keys in expected_structure.items():
            if section_name not in params:
                logger.warning(
                    f"Отсутствует секция {section_name} в learning_params, используем значения по умолчанию"
                )
                validated_params[section_name] = self._get_default_learning_params()[section_name]
                continue

            section = params[section_name]
            if not isinstance(section, dict):
                logger.warning(
                    f"Секция {section_name} не является словарем, используем значения по умолчанию"
                )
                validated_params[section_name] = self._get_default_learning_params()[section_name]
                continue

            validated_section = {}
            for key in expected_keys:
                if key not in section:
                    logger.warning(
                        f"Отсутствует ключ {key} в секции {section_name}, используем значение по умолчанию"
                    )
                    validated_section[key] = self._get_default_learning_params()[section_name][key]
                    continue

                value = section[key]
                if not isinstance(value, (int, float)):
                    logger.warning(
                        f"Значение {key} в секции {section_name} не является числом ({type(value)}), используем значение по умолчанию"
                    )
                    validated_section[key] = self._get_default_learning_params()[section_name][key]
                    continue

                # Валидация диапазонов
                if section_name in ["event_type_sensitivity"]:
                    # Диапазон [0.0, 1.0] для чувствительности
                    validated_section[key] = max(0.0, min(1.0, float(value)))
                elif section_name in ["significance_thresholds"]:
                    # Диапазон [0.0, 1.0] для порогов
                    validated_section[key] = max(0.0, min(1.0, float(value)))
                elif section_name in ["response_coefficients"]:
                    # Диапазон [0.0, 2.0] для коэффициентов (могут быть > 1.0)
                    validated_section[key] = max(0.0, min(2.0, float(value)))
                else:
                    validated_section[key] = float(value)

            validated_params[section_name] = validated_section

        return validated_params

    def _validate_adaptation_params(self, params: dict) -> dict:
        """
        Валидация структуры adaptation_params при загрузке из snapshot.

        Args:
            params: Словарь adaptation_params для валидации

        Returns:
            Валидированные параметры или параметры по умолчанию при ошибках

        Raises:
            ValueError: При критических ошибках структуры
        """
        import logging

        logger = logging.getLogger(__name__)

        # Ожидаемая структура
        expected_structure = {
            "behavior_sensitivity": ["noise", "decay", "recovery", "shock", "idle"],
            "behavior_thresholds": ["noise", "decay", "recovery", "shock", "idle"],
            "behavior_coefficients": ["dampen", "absorb", "ignore"],
        }

        if not isinstance(params, dict):
            logger.warning(
                "adaptation_params не является словарем, используем значения по умолчанию"
            )
            return self._get_default_adaptation_params()

        validated_params = {}

        for section_name, expected_keys in expected_structure.items():
            if section_name not in params:
                logger.warning(
                    f"Отсутствует секция {section_name} в adaptation_params, используем значения по умолчанию"
                )
                validated_params[section_name] = self._get_default_adaptation_params()[section_name]
                continue

            section = params[section_name]
            if not isinstance(section, dict):
                logger.warning(
                    f"Секция {section_name} не является словарем, используем значения по умолчанию"
                )
                validated_params[section_name] = self._get_default_adaptation_params()[section_name]
                continue

            validated_section = {}
            for key in expected_keys:
                if key not in section:
                    logger.warning(
                        f"Отсутствует ключ {key} в секции {section_name}, используем значение по умолчанию"
                    )
                    validated_section[key] = self._get_default_adaptation_params()[section_name][
                        key
                    ]
                    continue

                value = section[key]
                if not isinstance(value, (int, float)):
                    logger.warning(
                        f"Значение {key} в секции {section_name} не является числом ({type(value)}), используем значение по умолчанию"
                    )
                    validated_section[key] = self._get_default_adaptation_params()[section_name][
                        key
                    ]
                    continue

                # Валидация диапазонов (такие же как для learning)
                if section_name in ["behavior_sensitivity"]:
                    validated_section[key] = max(0.0, min(1.0, float(value)))
                elif section_name in ["behavior_thresholds"]:
                    validated_section[key] = max(0.0, min(1.0, float(value)))
                elif section_name in ["behavior_coefficients"]:
                    validated_section[key] = max(0.0, min(2.0, float(value)))
                else:
                    validated_section[key] = float(value)

            validated_params[section_name] = validated_section

        return validated_params

    def _get_default_learning_params(self) -> dict:
        """Получить параметры learning по умолчанию"""
        return {
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

    def _get_default_adaptation_params(self) -> dict:
        """Получить параметры adaptation по умолчанию"""
        return {
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

    def get_change_history(
        self, limit: Optional[int] = None, filter_by_life_id: bool = True
    ) -> list:
        """
        Получить историю изменений состояния из лога

        Оптимизирован для больших файлов: читает с конца файла без загрузки всего файла в память.

        Args:
            limit: Максимальное количество записей для возврата (None = все записи)
            filter_by_life_id: Если True, возвращать только записи для текущего life_id

        Returns:
            Список записей истории изменений (от старых к новым)
        """
        # Сбрасываем буфер перед чтением, чтобы включить последние изменения
        self._flush_log_buffer()

        if not STATE_CHANGES_LOG_FILE.exists():
            return []

        history = []
        try:
            # Если limit не указан, читаем весь файл (старый способ)
            if limit is None:
                with STATE_CHANGES_LOG_FILE.open("r") as f:
                    for line in f:
                        if line.strip():
                            try:
                                entry = json.loads(line)
                                if filter_by_life_id and entry.get("life_id") != self.life_id:
                                    continue
                                history.append(entry)
                            except (json.JSONDecodeError, KeyError):
                                # Пропускаем некорректные строки
                                continue
            else:
                # Оптимизированное чтение с конца файла
                # Читаем файл блоками с конца, чтобы не загружать весь файл в память
                with STATE_CHANGES_LOG_FILE.open("rb") as f:
                    # Перемещаемся в конец файла
                    f.seek(0, 2)  # 2 = SEEK_END
                    file_size = f.tell()

                    # Размер блока для чтения (64KB)
                    block_size = 64 * 1024
                    buffer = b""
                    lines_found = []
                    position = file_size

                    # Читаем блоки с конца, пока не соберем достаточно строк
                    while (
                        position > 0 and len(lines_found) < limit * 2
                    ):  # Берем больше для фильтрации
                        # Определяем размер блока для чтения
                        read_size = min(block_size, position)
                        position -= read_size
                        f.seek(position)

                        # Читаем блок
                        block = f.read(read_size)
                        buffer = block + buffer

                        # Разбиваем на строки
                        while b"\n" in buffer:
                            line, buffer = buffer.rsplit(b"\n", 1)
                            if line.strip():
                                lines_found.append(line.decode("utf-8", errors="ignore"))

                    # Обрабатываем оставшийся буфер
                    if buffer.strip():
                        lines_found.append(buffer.decode("utf-8", errors="ignore"))

                    # Берем последние limit строк (они в обратном порядке)
                    lines_found = lines_found[-limit:] if len(lines_found) > limit else lines_found

                    # Парсим строки и фильтруем
                    for line in reversed(
                        lines_found
                    ):  # Разворачиваем, чтобы получить правильный порядок
                        if line.strip():
                            try:
                                entry = json.loads(line)
                                if filter_by_life_id and entry.get("life_id") != self.life_id:
                                    continue
                                history.append(entry)
                                # Останавливаемся, когда собрали достаточно записей
                                if len(history) >= limit:
                                    break
                            except (json.JSONDecodeError, KeyError):
                                # Пропускаем некорректные строки
                                continue
        except Exception:
            pass

        return history

    def load_latest_snapshot(self) -> "SelfState":
        # Найти последний snapshot_*.json
        snapshots = list(SNAPSHOT_DIR.glob("snapshot_*.json"))
        if not snapshots:
            raise FileNotFoundError("No snapshots found")
        # Сортировать по номеру тика
        snapshots.sort(key=lambda p: int(p.stem.split("_")[1]))
        latest = snapshots[-1]

        import logging

        logger = logging.getLogger(__name__)

        try:
            with latest.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"Failed to parse snapshot file {latest}: {e}")
            # Попробовать предыдущий snapshot, если есть
            if len(snapshots) > 1:
                prev_snapshot = snapshots[-2]
                logger.warning(f"Trying previous snapshot: {prev_snapshot}")
                try:
                    with prev_snapshot.open("r", encoding="utf-8") as f:
                        data = json.load(f)
                    logger.info(f"Successfully loaded previous snapshot: {prev_snapshot}")
                except (json.JSONDecodeError, UnicodeDecodeError) as e2:
                    logger.error(f"Previous snapshot also corrupted: {e2}")
                    raise RuntimeError(
                        f"All available snapshots are corrupted. Latest: {e}, Previous: {e2}"
                    )
            else:
                raise RuntimeError(f"Snapshot file corrupted and no backup available: {e}")

        # Создаем новый экземпляр для загрузки данных
        temp_state = SelfState()
        return temp_state._load_snapshot_from_data(data)

    def _load_snapshot_from_data(self, data: dict) -> "SelfState":
        """
        Загрузка состояния из данных snapshot с валидацией.

        Args:
            data: Данные snapshot из JSON

        Returns:
            SelfState: Загруженное и валидированное состояние
        """
        import logging

        logger = logging.getLogger(__name__)

        # Mapping для совместимости
        field_mapping = {
            "alive": "active",
            "active": "_active",  # active теперь property, сохраняем как _active
        }
        mapped_data = {}
        for k, v in data.items():
            mapped_key = field_mapping.get(k, k)
            if mapped_key in SelfState.__dataclass_fields__:
                mapped_data[mapped_key] = v

        # Валидация и исправление learning_params
        if "learning_params" in mapped_data:
            mapped_data["learning_params"] = self._validate_learning_params(
                mapped_data["learning_params"]
            )
        else:
            logger.info(
                "learning_params отсутствуют в snapshot, будут использованы значения по умолчанию"
            )

        # Валидация и исправление adaptation_params
        if "adaptation_params" in mapped_data:
            mapped_data["adaptation_params"] = self._validate_adaptation_params(
                mapped_data["adaptation_params"]
            )
        else:
            logger.info(
                "adaptation_params отсутствуют в snapshot, будут использованы значения по умолчанию"
            )

        # Удаляем поля, которые не должны передаваться в __init__
        if "archive_memory" in mapped_data:
            mapped_data.pop("archive_memory")

        # Конвертировать memory из list of dict в list of MemoryEntry
        memory_entries = []
        if "memory" in mapped_data:
            logger.info(f"Loading {len(mapped_data['memory'])} memory entries from snapshot")
            for i, entry in enumerate(mapped_data["memory"]):
                try:
                    memory_entries.append(MemoryEntry(**entry))
                    logger.debug(f"Loaded memory entry {i}: {entry['event_type']}")
                except (TypeError, ValueError) as e:
                    logger.warning(f"Skipping corrupted memory entry {i}: {e}. Entry data: {entry}")
                    # Продолжаем с остальными записями
            mapped_data.pop("memory")  # Удаляем из mapped_data, инициализируем отдельно
            logger.info(f"Successfully converted {len(memory_entries)} memory entries")

        # Восстанавливаем activated_memory
        activated_memory_entries = []
        if "activated_memory" in mapped_data:
            for i, entry in enumerate(mapped_data["activated_memory"]):
                try:
                    activated_memory_entries.append(MemoryEntry(**entry))
                except (TypeError, ValueError) as e:
                    logger.warning(f"Skipping corrupted activated_memory entry {i}: {e}. Entry data: {entry}")
            mapped_data.pop("activated_memory")  # Удаляем из mapped_data, инициализируем отдельно

        # Создать экземпляр, разрешив изменение immutable полей для загрузки
        # Сначала создаем экземпляр с флагом загрузки
        state = SelfState()
        # Устанавливаем флаг загрузки из snapshot
        object.__setattr__(state, "_loading_from_snapshot", True)
        try:
            # Теперь можем устанавливать immutable поля
            for name, value in mapped_data.items():
                if hasattr(state, name):
                    setattr(state, name, value)
        finally:
            # Снимаем флаг загрузки
            object.__setattr__(state, "_loading_from_snapshot", False)
        # Создаем архив при загрузке snapshot (без загрузки существующих данных)
        state.archive_memory = ArchiveMemory(load_existing=False)
        # Инициализируем memory с архивом и загруженными записями
        state.memory = Memory(archive=state.archive_memory)
        logger.info(f"Initialized memory object, adding {len(memory_entries)} entries")
        for i, entry in enumerate(memory_entries):
            state.memory.append(entry)
            logger.debug(f"Added memory entry {i}: {entry.event_type}")
        logger.info(f"Memory initialization complete, total entries: {len(state.memory)}")

        # Восстанавливаем activated_memory
        state.activated_memory = activated_memory_entries

        # Восстанавливаем memory_entries_by_type если он был сохранен
        if "memory_entries_by_type" in mapped_data:
            state.memory_entries_by_type = mapped_data.pop("memory_entries_by_type")

        # Финальная валидация загруженного состояния
        if state.energy < 0 or state.energy > 100:
            logger.warning(
                f"Invalid energy value in snapshot: {state.energy}, clamping to [0, 100]"
            )
            state.energy = max(0, min(100, state.energy))

        if state.integrity < 0 or state.integrity > 1:
            logger.warning(
                f"Invalid integrity value in snapshot: {state.integrity}, clamping to [0, 1]"
            )
            state.integrity = max(0, min(1, state.integrity))

        if state.stability < 0 or state.stability > 1:
            logger.warning(
                f"Invalid stability value in snapshot: {state.stability}, clamping to [0, 1]"
            )
            state.stability = max(0, min(1, state.stability))

        if state.ticks < 0:
            logger.warning(f"Invalid ticks value in snapshot: {state.ticks}, setting to 0")
            state.ticks = 0

        logger.info(
            f"Snapshot загружен успешно. Тики: {state.ticks}, Энергия: {state.energy:.1f}, "
            f"Целостность: {state.integrity:.3f}, Стабильность: {state.stability:.3f}, "
            f"Записей памяти: {len(memory_entries)}"
        )
        return state


def create_initial_state() -> SelfState:
    """Создает начальное состояние для новой сессии жизни"""
    # ArchiveMemory() по умолчанию имеет load_existing=False, что подходит для новой сессии
    state = SelfState()
    # Убеждаемся, что ArchiveMemory пустая согласно плану восстановления
    assert (
        state.archive_memory.size() == 0
    ), f"ArchiveMemory should be empty on initialization, but has {state.archive_memory.size()} entries"
    return state


def save_snapshot(state: SelfState, compress_large: bool = True):
    """
    Сохраняет текущее состояние жизни как отдельный JSON файл.
    Оптимизированная сериализация с компрессией больших файлов.

    ПРИМЕЧАНИЕ: Логирование временно отключается во время сериализации для производительности.
    Изменения состояния, которые могут произойти во время вызова asdict() (например,
    конвертация dataclass), не будут залогированы. Это намеренное решение для оптимизации.

    ПРИМЕЧАНИЕ: Flush буфера логов должен управляться через LogManager в runtime loop,
    а не внутри этой функции. Это обеспечивает правильное разделение ответственности.

    Args:
        state: Состояние для сохранения
        compress_large: Если True, использует gzip компрессию для больших snapshots (>50KB)
    """
    import gzip
    from src.runtime.performance_metrics import measure_time

    # Временно отключаем логирование для сериализации
    # Это предотвращает логирование изменений, которые могут произойти при конвертации dataclass
    logging_was_enabled = state._logging_enabled
    state.disable_logging()

    try:
        with measure_time("save_snapshot"):
            # Создаем snapshot с оптимизацией
            snapshot = state._create_optimized_snapshot_data()

            tick = snapshot["ticks"]
            filename = SNAPSHOT_DIR / f"snapshot_{tick:06d}.json"

            # Атомарная замена: сначала пишем во временный файл, затем переименовываем
            temp_filename = SNAPSHOT_DIR / f"snapshot_{tick:06d}.tmp"

            # Проверяем размер данных для решения о компрессии
            json_str = json.dumps(snapshot, separators=(",", ":"), default=str)
            data_size = len(json_str.encode("utf-8"))

            # Компрессия для больших файлов (>50KB)
            if compress_large and data_size > 50 * 1024:
                compressed_filename = SNAPSHOT_DIR / f"snapshot_{tick:06d}.json.gz"
                compressed_temp = SNAPSHOT_DIR / f"snapshot_{tick:06d}.tmp.gz"

                # Пишем сжатый файл
                with gzip.open(compressed_temp, "wt", encoding="utf-8", compresslevel=6) as f:
                    f.write(json_str)

                # Атомарное переименование сжатого файла
                compressed_temp.replace(compressed_filename)

                # Удаляем несжатый файл если существует
                if filename.exists():
                    filename.unlink()

                # Создаем символическую ссылку для обратной совместимости
                try:
                    if not filename.exists():
                        filename.symlink_to(compressed_filename.name + ".gz")
                except OSError:
                    # Игнорируем ошибки создания symlink (например, на Windows)
                    pass
            else:
                # Стандартная запись без компрессии
                with temp_filename.open("w") as f:
                    f.write(json_str)

                # Атомарное переименование
                temp_filename.replace(filename)

                # Удаляем сжатый файл если существует
                compressed_filename = SNAPSHOT_DIR / f"snapshot_{tick:06d}.json.gz"
                if compressed_filename.exists():
                    compressed_filename.unlink()
    finally:
        # Восстанавливаем логирование
        if logging_was_enabled:
            state.enable_logging()

    def get_parameter_evolution(
        self, parameter_name: str, time_range: tuple = None
    ) -> list[ParameterChange]:
        """
        Получить эволюцию конкретного параметра за заданный период времени.

        Args:
            parameter_name: Имя параметра для анализа
            time_range: Кортеж (start_time, end_time) или None для всех записей

        Returns:
            Список изменений параметра в хронологическом порядке
        """
        with self._api_lock:
            changes = [
                change
                for change in self.parameter_history
                if change.parameter_name == parameter_name
            ]

            if time_range:
                start_time, end_time = time_range
                changes = [
                    change for change in changes if start_time <= change.timestamp <= end_time
                ]

            return sorted(changes, key=lambda x: x.timestamp)

    def get_evolution_trends(self, time_window: float = 3600.0) -> dict:
        """
        Анализировать тренды эволюции параметров за заданное временное окно.

        Args:
            time_window: Временное окно в секундах для анализа трендов

        Returns:
            Словарь с трендами по параметрам
        """
        current_time = time.time()
        window_start = current_time - time_window

        with self._api_lock:
            # Фильтруем изменения за временное окно
            recent_changes = [
                change for change in self.parameter_history if change.timestamp >= window_start
            ]

            trends = {}
            for change in recent_changes:
                param = change.parameter_name
                if param not in trends:
                    trends[param] = {
                        "changes_count": 0,
                        "first_value": None,
                        "last_value": None,
                        "avg_change_rate": 0.0,
                        "trend_direction": "stable",
                    }

                trends[param]["changes_count"] += 1

                if trends[param]["first_value"] is None:
                    trends[param]["first_value"] = change.old_value
                trends[param]["last_value"] = change.new_value

            # Вычисляем тренды
            for param, data in trends.items():
                if (
                    data["changes_count"] > 1
                    and data["first_value"] is not None
                    and data["last_value"] is not None
                ):
                    try:
                        # Простая оценка направления тренда
                        if isinstance(data["first_value"], (int, float)) and isinstance(
                            data["last_value"], (int, float)
                        ):
                            delta = data["last_value"] - data["first_value"]
                            if delta > 0.01:
                                data["trend_direction"] = "increasing"
                            elif delta < -0.01:
                                data["trend_direction"] = "decreasing"
                            else:
                                data["trend_direction"] = "stable"
                    except (TypeError, ValueError):
                        data["trend_direction"] = "complex"

        return trends

    def get_parameter_correlations(
        self, param1: str, param2: str, time_window: float = 3600.0
    ) -> dict:
        """
        Анализировать корреляции между изменениями двух параметров.

        Args:
            param1: Первый параметр
            param2: Второй параметр
            time_window: Временное окно для анализа

        Returns:
            Статистика корреляций между параметрами
        """
        current_time = time.time()
        window_start = current_time - time_window

        with self._api_lock:
            changes1 = [
                c
                for c in self.parameter_history
                if c.parameter_name == param1 and c.timestamp >= window_start
            ]
            changes2 = [
                c
                for c in self.parameter_history
                if c.parameter_name == param2 and c.timestamp >= window_start
            ]

            if not changes1 or not changes2:
                return {"correlation": 0.0, "sample_size": 0}

            # Простой анализ совместных изменений
            joint_changes = 0
            total_pairs = min(len(changes1), len(changes2))

            for i in range(total_pairs):
                # Проверяем, происходили ли изменения в близкие моменты времени
                time_diff = abs(changes1[i].timestamp - changes2[i].timestamp)
                if time_diff < 1.0:  # В пределах 1 секунды
                    joint_changes += 1

            correlation = joint_changes / max(total_pairs, 1)

            return {
                "correlation": correlation,
                "sample_size": total_pairs,
                "joint_changes": joint_changes,
            }

    def get_vital_parameters_trends(self, time_window: float = 3600.0) -> dict:
        """
        Анализировать тренды жизненноважных параметров (energy, integrity, stability)
        за заданное временное окно.

        Args:
            time_window: Временное окно в секундах для анализа трендов

        Returns:
            Словарь с трендами жизненноважных параметров
        """
        current_time = time.time()
        window_start = current_time - time_window

        with self._api_lock:
            vital_params = ["energy", "integrity", "stability"]
            trends = {}

            for param in vital_params:
                changes = [
                    c
                    for c in self.parameter_history
                    if c.parameter_name == param and c.timestamp >= window_start
                ]

                if not changes:
                    trends[param] = {
                        "current_value": getattr(self, param, None),
                        "changes_count": 0,
                        "trend": "no_data",
                        "avg_change_rate": 0.0,
                        "min_value": getattr(self, param, None),
                        "max_value": getattr(self, param, None),
                    }
                    continue

                # Сортируем по времени
                changes.sort(key=lambda x: x.timestamp)

                # Вычисляем статистику
                first_value = (
                    changes[0].old_value
                    if changes[0].old_value is not None
                    else changes[0].new_value
                )
                last_value = changes[-1].new_value
                min_value = min(c.new_value for c in changes)
                max_value = max(c.new_value for c in changes)

                # Вычисляем среднюю скорость изменения
                time_span = changes[-1].timestamp - changes[0].timestamp
                if time_span > 0:
                    avg_change_rate = (last_value - first_value) / time_span
                else:
                    avg_change_rate = 0.0

                # Определяем тренд
                if abs(last_value - first_value) < 0.01:
                    trend = "stable"
                elif last_value > first_value:
                    trend = "increasing"
                else:
                    trend = "decreasing"

                trends[param] = {
                    "current_value": getattr(self, param),
                    "changes_count": len(changes),
                    "trend": trend,
                    "avg_change_rate": avg_change_rate,
                    "min_value": min_value,
                    "max_value": max_value,
                    "first_value": first_value,
                    "last_value": last_value,
                }

        return trends

    def get_internal_dynamics_trends(self, time_window: float = 3600.0) -> dict:
        """
        Анализировать тренды внутренних динамических параметров (fatigue, tension)
        за заданное временное окно.

        Args:
            time_window: Временное окно в секундах для анализа трендов

        Returns:
            Словарь с трендами внутренних параметров
        """
        current_time = time.time()
        window_start = current_time - time_window

        with self._api_lock:
            internal_params = ["fatigue", "tension"]
            trends = {}

            for param in internal_params:
                changes = [
                    c
                    for c in self.parameter_history
                    if c.parameter_name == param and c.timestamp >= window_start
                ]

                if not changes:
                    trends[param] = {
                        "current_value": getattr(self, param, None),
                        "changes_count": 0,
                        "trend": "no_data",
                        "volatility": 0.0,
                        "avg_value": getattr(self, param, None),
                    }
                    continue

                # Сортируем по времени
                changes.sort(key=lambda x: x.timestamp)

                values = [c.new_value for c in changes]
                current_value = getattr(self, param)

                # Вычисляем волатильность (стандартное отклонение)
                if len(values) > 1:
                    mean = sum(values) / len(values)
                    volatility = (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5
                else:
                    volatility = 0.0
                    mean = values[0] if values else current_value

                # Определяем тренд на основе волатильности и направления
                if volatility > 0.1:
                    trend = "volatile"
                elif len(changes) >= 2:
                    first_val = changes[0].new_value
                    last_val = changes[-1].new_value
                    if abs(last_val - first_val) < 0.01:
                        trend = "stable"
                    elif last_val > first_val:
                        trend = "increasing"
                    else:
                        trend = "decreasing"
                else:
                    trend = "stable"

                trends[param] = {
                    "current_value": current_value,
                    "changes_count": len(changes),
                    "trend": trend,
                    "volatility": volatility,
                    "avg_value": mean,
                }

        return trends


def load_snapshot(tick: int) -> SelfState:
    """
    Загружает снимок по номеру тика с валидацией параметров.
    Поддерживает как обычные, так и сжатые (gzip) файлы.
    """
    import gzip
    from src.runtime.performance_metrics import measure_time

    filename = SNAPSHOT_DIR / f"snapshot_{tick:06d}.json"
    compressed_filename = SNAPSHOT_DIR / f"snapshot_{tick:06d}.json.gz"

    with measure_time("load_snapshot"):
        # Проверяем обычный файл
        if filename.exists():
            with filename.open("r") as f:
                data = json.load(f)
        # Проверяем сжатый файл
        elif compressed_filename.exists():
            with gzip.open(compressed_filename, "rt", encoding="utf-8") as f:
                data = json.load(f)
        else:
            raise FileNotFoundError(f"Snapshot {tick} не найден")

        # Создаем временный экземпляр для доступа к методам валидации
        temp_state = SelfState()
        return temp_state._load_snapshot_from_data(data)
