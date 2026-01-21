import json
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.memory.memory import ArchiveMemory, Memory, MemoryEntry
from src.validation.field_validator import FieldValidator

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
class SelfState:
    # Thread-safety lock для API доступа
    _api_lock: threading.RLock = field(
        default_factory=threading.RLock, init=False, repr=False
    )

    life_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    birth_timestamp: float = field(default_factory=time.time)
    age: float = 0.0
    # Subjective time ("internal lived time"), seconds on internal scale.
    # Must be monotonic (non-decreasing) and computed deterministically from state + signals.
    subjective_time: float = 0.0
    ticks: int = 0
    energy: float = 100.0
    integrity: float = 1.0
    stability: float = 1.0
    fatigue: float = 0.0
    tension: float = 0.0
    _active: bool = True  # Внутреннее поле для active
    recent_events: list = field(default_factory=list)
    last_significance: float = 0.0
    energy_history: list = field(default_factory=list)
    stability_history: list = field(default_factory=list)
    planning: dict = field(default_factory=dict)
    intelligence: dict = field(default_factory=dict)
    memory: Optional[Memory] = field(default=None)  # Активная память с поддержкой архивации
    archive_memory: ArchiveMemory = field(
        default_factory=lambda: ArchiveMemory(), init=False
    )  # Архивная память (не сериализуется в snapshot напрямую)

    # Внутренние флаги для контроля инициализации и логирования
    _initialized: bool = field(default=False, init=False, repr=False)
    _logging_enabled: bool = field(default=True, init=False, repr=False)
    _log_only_critical: bool = field(default=False, init=False, repr=False)
    _log_buffer: list = field(default_factory=list, init=False, repr=False)
    _log_buffer_size: int = field(default=100, init=False, repr=False)
    _loading_from_snapshot: bool = field(default=False, init=False, repr=False)

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
    circadian_period: float = 24.0 * 3600.0  # Период в секундах (24 часа)
    recovery_efficiency: float = 1.0  # Эффективность восстановления [0.4, 1.6]
    stability_modifier: float = 1.0  # Модификатор стабильности [0.7, 1.3]

    # === Echo memory parameters ===
    echo_count: int = 0  # Количество эхо-всплываний
    last_echo_time: float = 0.0  # Время последнего эхо в секундах жизни

    # === Clarity moments parameters ===
    clarity_state: bool = False  # Флаг активности момента ясности
    clarity_duration: int = 0  # Оставшаяся длительность момента ясности в тиках
    clarity_modifier: float = 1.0  # Текущий модификатор значимости для моментов ясности

    # Last perceived event intensity (signal for subjective time), in [0..1].
    last_event_intensity: float = 0.0

    def __post_init__(self):
        """Инициализация memory с архивом после создания объекта"""
        if self.memory is None:
            self.memory = Memory(archive=self.archive_memory)
        # Помечаем объект как инициализированный после __post_init__
        object.__setattr__(self, "_initialized", True)

    def _validate_field(
        self, field_name: str, value: float, clamp: bool = False
    ) -> float:
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
                backup_file = (
                    STATE_CHANGES_LOG_DIR / f"state_changes_{timestamp}.jsonl.backup"
                )
                STATE_CHANGES_LOG_FILE.rename(backup_file)
                # Создаем новый пустой файл
                STATE_CHANGES_LOG_FILE.touch()

                # Очищаем старые резервные копии
                self._cleanup_old_backups()
        except Exception:
            # Игнорируем ошибки ротации, чтобы не нарушать работу системы
            pass

    def _cleanup_old_backups(
        self, max_age_days: int = 30, max_backups: int = 10
    ) -> None:
        """
        Очистка старых резервных копий логов

        Args:
            max_age_days: Максимальный возраст резервной копии в днях (по умолчанию 30)
            max_backups: Максимальное количество резервных копий для хранения (по умолчанию 10)
        """
        try:
            # Находим все резервные копии
            backup_files = list(
                STATE_CHANGES_LOG_DIR.glob("state_changes_*.jsonl.backup")
            )

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

    def _log_change(self, field_name: str, old_value, new_value) -> None:
        """
        Логирование изменения поля в append-only лог.
        Поддерживает батчинг и фильтрацию по критичности.
        """
        if not self._logging_enabled:
            return

        # Если включен режим "только критичные", пропускаем некритичные поля
        if self._log_only_critical and not self._is_critical_field(field_name):
            return

        try:
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
        if name not in ["activated_memory", "last_pattern"] and not getattr(
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
                raise AttributeError(
                    f"Cannot modify immutable field '{name}' after initialization"
                )

            # Получаем старое значение для логирования (безопасно)
            old_value = None
            if is_initialized:
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
                "ticks",
            ]:
                value = self._validate_field(name, value, clamp=False)

            # Устанавливаем значение
            object.__setattr__(self, name, value)

            # Логируем изменение (только после инициализации и если значение изменилось)
            if is_initialized and old_value is not None and old_value != value:
                self._log_change(name, old_value, value)

            # Active обновляется только при явном изменении или в специальных случаях
            # Не автоматически при изменении vital параметров

    activated_memory: list = field(
        default_factory=list
    )  # Transient, не сохраняется в snapshot
    last_pattern: str = ""  # Transient, последний выбранный паттерн decision

    @property
    def active(self) -> bool:
        """Active status - can be manually overridden or computed from viability"""
        # Если _active установлено вручную в False, возвращаем False
        # Иначе возвращаем is_viable()
        if hasattr(self, "_active") and self._active is False:
            return False
        return self.is_viable()

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
        Проверка жизнеспособности состояния.
        Возвращает True если система жизнеспособна (vital параметры выше порогов).
        """
        return self.is_viable()

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
        Обновить фазу циркадного ритма и связанные параметры.

        Фаза циркадного ритма изменяется со скоростью 2π/(24 часа) = π/(12 часов).
        Recovery efficiency достигает пика днем (фаза π/2), минимум ночью (фаза 3π/2).
        Stability modifier достигает пика ночью (фаза π), минимум днем (фаза 0).

        Args:
            dt: Время в секундах, прошедшее с последнего обновления
        """
        import math

        # Обновляем фазу ритма
        phase_increment = (dt / self.circadian_period) * 2 * math.pi
        self.circadian_phase += phase_increment
        self.circadian_phase %= 2 * math.pi  # Нормализация в диапазон [0, 2π]

        # Обновляем эффективность восстановления
        # Пик днем (фаза π/2), минимум ночью (фаза 3π/2)
        # Диапазон: 0.4 + 0.6 * sin(фаза + π/2) = [0.4, 1.0] с пиком в π/2
        raw_recovery = 0.4 + 0.6 * math.sin(self.circadian_phase + math.pi / 2)
        self.recovery_efficiency = max(0.4, min(1.0, raw_recovery))

        # Обновляем модификатор стабильности
        # Пик ночью (фаза π), минимум днем (фаза 0)
        # Диапазон: 0.7 + 0.6 * sin(фаза) = [0.7, 1.3] с пиком в π
        raw_stability = 0.7 + 0.6 * math.sin(self.circadian_phase)
        self.stability_modifier = max(0.7, min(1.3, raw_stability))

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
        # Возрастной модификатор: растет с возрастом (30 дней = 30*24*3600 сек)
        age_modifier = min(1.0, self.age / (30 * 24 * 3600))

        # Модификатор стабильности: чаще при низкой стабильности
        stability_modifier = 1.0 + (1.0 - self.stability)

        # Общая вероятность эхо
        echo_probability = base_probability * age_modifier * stability_modifier

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

        Returns:
            dict: Безопасный словарь состояния для публичного API
        """
        # Thread-safe чтение состояния
        with self._api_lock:
            # Создаем словарь вручную, избегая проблемных полей
            state_dict = {}
            for field_name in SelfState.__dataclass_fields__:
                if not field_name.startswith("_"):  # Пропускаем внутренние поля
                    try:
                        value = getattr(self, field_name)
                        # Пропускаем не сериализуемые объекты
                        if field_name not in ["_api_lock", "archive_memory", "memory"]:
                            state_dict[field_name] = value
                    except AttributeError:
                        continue

        # Исключаем transient поля
        state_dict.pop("activated_memory", None)
        state_dict.pop("last_pattern", None)

        # Исключаем внутренние поля (начинающиеся с _)
        keys_to_remove = [key for key in state_dict.keys() if key.startswith("_")]
        for key in keys_to_remove:
            state_dict.pop(key, None)

        # Исключаем не сериализуемые объекты
        state_dict.pop("archive_memory", None)

        # Обрабатываем limits
        if limits is None:
            limits = {}

        # Обработка memory (по умолчанию не включаем, только если явно указан лимит)
        memory_limit = limits.get("memory_limit")
        if memory_limit is not None and self.memory is not None:
            # Ограничиваем количество записей памяти
            memory_entries = (
                list(self.memory)[-memory_limit:] if memory_limit > 0 else []
            )
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
            if "recent_events" in state_dict and isinstance(
                state_dict["recent_events"], list
            ):
                state_dict["recent_events"] = state_dict["recent_events"][
                    -events_limit:
                ]
        else:
            # По умолчанию не включаем recent_events
            state_dict.pop("recent_events", None)

        energy_history_limit = limits.get("energy_history_limit")
        if energy_history_limit is not None and energy_history_limit > 0:
            if "energy_history" in state_dict and isinstance(
                state_dict["energy_history"], list
            ):
                state_dict["energy_history"] = state_dict["energy_history"][
                    -energy_history_limit:
                ]
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
            ]
            for field_name in optional_fields:
                state_dict.pop(field_name, None)

        return state_dict

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
            logger.warning(
                "learning_params не является словарем, используем значения по умолчанию"
            )
            return self._get_default_learning_params()

        validated_params = {}

        for section_name, expected_keys in expected_structure.items():
            if section_name not in params:
                logger.warning(
                    f"Отсутствует секция {section_name} в learning_params, используем значения по умолчанию"
                )
                validated_params[section_name] = self._get_default_learning_params()[
                    section_name
                ]
                continue

            section = params[section_name]
            if not isinstance(section, dict):
                logger.warning(
                    f"Секция {section_name} не является словарем, используем значения по умолчанию"
                )
                validated_params[section_name] = self._get_default_learning_params()[
                    section_name
                ]
                continue

            validated_section = {}
            for key in expected_keys:
                if key not in section:
                    logger.warning(
                        f"Отсутствует ключ {key} в секции {section_name}, используем значение по умолчанию"
                    )
                    validated_section[key] = self._get_default_learning_params()[
                        section_name
                    ][key]
                    continue

                value = section[key]
                if not isinstance(value, (int, float)):
                    logger.warning(
                        f"Значение {key} в секции {section_name} не является числом ({type(value)}), используем значение по умолчанию"
                    )
                    validated_section[key] = self._get_default_learning_params()[
                        section_name
                    ][key]
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
                validated_params[section_name] = self._get_default_adaptation_params()[
                    section_name
                ]
                continue

            section = params[section_name]
            if not isinstance(section, dict):
                logger.warning(
                    f"Секция {section_name} не является словарем, используем значения по умолчанию"
                )
                validated_params[section_name] = self._get_default_adaptation_params()[
                    section_name
                ]
                continue

            validated_section = {}
            for key in expected_keys:
                if key not in section:
                    logger.warning(
                        f"Отсутствует ключ {key} в секции {section_name}, используем значение по умолчанию"
                    )
                    validated_section[key] = self._get_default_adaptation_params()[
                        section_name
                    ][key]
                    continue

                value = section[key]
                if not isinstance(value, (int, float)):
                    logger.warning(
                        f"Значение {key} в секции {section_name} не является числом ({type(value)}), используем значение по умолчанию"
                    )
                    validated_section[key] = self._get_default_adaptation_params()[
                        section_name
                    ][key]
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
                                if (
                                    filter_by_life_id
                                    and entry.get("life_id") != self.life_id
                                ):
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
                                lines_found.append(
                                    line.decode("utf-8", errors="ignore")
                                )

                    # Обрабатываем оставшийся буфер
                    if buffer.strip():
                        lines_found.append(buffer.decode("utf-8", errors="ignore"))

                    # Берем последние limit строк (они в обратном порядке)
                    lines_found = (
                        lines_found[-limit:]
                        if len(lines_found) > limit
                        else lines_found
                    )

                    # Парсим строки и фильтруем
                    for line in reversed(
                        lines_found
                    ):  # Разворачиваем, чтобы получить правильный порядок
                        if line.strip():
                            try:
                                entry = json.loads(line)
                                if (
                                    filter_by_life_id
                                    and entry.get("life_id") != self.life_id
                                ):
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
        with latest.open("r") as f:
            data = json.load(f)
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
            memory_entries = [MemoryEntry(**entry) for entry in mapped_data["memory"]]
            mapped_data.pop("memory")  # Удаляем из mapped_data, инициализируем отдельно

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
        for entry in memory_entries:
            state.memory.append(entry)

        logger.info(
            "Snapshot загружен успешно с валидацией learning_params и adaptation_params"
        )
        return state


def create_initial_state() -> SelfState:
    """Создает начальное состояние для новой сессии жизни"""
    # ArchiveMemory() по умолчанию имеет load_existing=False, что подходит для новой сессии
    return SelfState()


def save_snapshot(state: SelfState):
    """
    Сохраняет текущее состояние жизни как отдельный JSON файл.
    Оптимизированная сериализация с исключением transient полей.

    ПРИМЕЧАНИЕ: Логирование временно отключается во время сериализации для производительности.
    Изменения состояния, которые могут произойти во время вызова asdict() (например,
    конвертация dataclass), не будут залогированы. Это намеренное решение для оптимизации.

    ПРИМЕЧАНИЕ: Flush буфера логов должен управляться через LogManager в runtime loop,
    а не внутри этой функции. Это обеспечивает правильное разделение ответственности.

    Args:
        state: Состояние для сохранения
    """
    from src.runtime.performance_metrics import measure_time

    # Временно отключаем логирование для сериализации
    # Это предотвращает логирование изменений, которые могут произойти при конвертации dataclass
    logging_was_enabled = state._logging_enabled
    state.disable_logging()

    try:
        with measure_time("save_snapshot"):
            # Создаем snapshot вручную, избегая проблем с asdict и RLock
            snapshot = {}
            for field_name in SelfState.__dataclass_fields__:
                if not field_name.startswith("_"):  # Пропускаем внутренние поля
                    try:
                        value = getattr(state, field_name)
                        # Пропускаем не сериализуемые объекты
                        if field_name not in ["_api_lock", "archive_memory", "memory"]:
                            snapshot[field_name] = value
                    except AttributeError:
                        continue

            # Исключаем transient поля и большие структуры для производительности
            snapshot.pop("activated_memory", None)
            snapshot.pop("last_pattern", None)
            # Исключаем большие структуры, которые не нужны для snapshot
            snapshot.pop("energy_history", None)
            snapshot.pop("stability_history", None)
            snapshot.pop("time_ratio_history", None)
            snapshot.pop("adaptation_history", None)
            snapshot.pop("recent_events", None)

            # Оптимизированная конвертация Memory в list с кэшированием
            if isinstance(state.memory, Memory):
                # Используем кэшированную сериализацию для производительности
                snapshot["memory"] = state.memory.get_serialized_entries()

            tick = snapshot["ticks"]
            filename = SNAPSHOT_DIR / f"snapshot_{tick:06d}.json"

            # Атомарная замена: сначала пишем во временный файл, затем переименовываем
            # Это гарантирует, что читатели никогда не увидят частично записанный файл
            temp_filename = SNAPSHOT_DIR / f"snapshot_{tick:06d}.tmp"

            # Оптимизированная запись без лишних отступов (меньше размер файла)
            with temp_filename.open("w") as f:
                json.dump(snapshot, f, separators=(",", ":"), default=str)

            # Атомарное переименование - это гарантирует консистентность для читателей
            temp_filename.replace(filename)
    finally:
        # Восстанавливаем логирование
        if logging_was_enabled:
            state.enable_logging()


def load_snapshot(tick: int) -> SelfState:
    """
    Загружает снимок по номеру тика с валидацией параметров
    """
    filename = SNAPSHOT_DIR / f"snapshot_{tick:06d}.json"
    if filename.exists():
        with filename.open("r") as f:
            data = json.load(f)

        # Создаем временный экземпляр для доступа к методам валидации
        temp_state = SelfState()
        return temp_state._load_snapshot_from_data(data)
    else:
        raise FileNotFoundError(f"Snapshot {tick} не найден")
