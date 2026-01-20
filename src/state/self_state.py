import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

from src.memory.memory import ArchiveMemory, Memory, MemoryEntry

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

    # Внутренние флаги для контроля инициализации и логирования
    _initialized: bool = field(default=False, init=False, repr=False)
    _logging_enabled: bool = field(default=True, init=False, repr=False)
    _log_only_critical: bool = field(default=False, init=False, repr=False)
    _log_buffer: list = field(default_factory=list, init=False, repr=False)
    _log_buffer_size: int = field(default=100, init=False, repr=False)

    # === Subjective time modulation parameters (defaults) ===
    subjective_time_base_rate: float = 1.0
    subjective_time_rate_min: float = 0.1
    subjective_time_rate_max: float = 3.0
    subjective_time_intensity_coeff: float = 1.0
    subjective_time_stability_coeff: float = 0.5

    # Last perceived event intensity (signal for subjective time), in [0..1].
    last_event_intensity: float = 0.0

    def __post_init__(self):
        """Инициализация memory с архивом после создания объекта"""
        if self.memory is None:
            self.memory = Memory(archive=self.archive_memory)
        # Помечаем объект как инициализированный после __post_init__
        object.__setattr__(self, "_initialized", True)

    def _validate_field(self, field_name: str, value: float) -> float:
        """Валидация значения поля с учетом его границ (обрезает значения до границ)"""
        if field_name == "energy":
            # Обрезаем значение до допустимого диапазона
            return max(0.0, min(100.0, value))
        elif field_name in ["integrity", "stability"]:
            # Обрезаем значение до допустимого диапазона
            return max(0.0, min(1.0, value))
        elif field_name == "last_event_intensity":
            return max(0.0, min(1.0, value))
        elif field_name in ["fatigue", "tension", "age"]:
            # Обрезаем значение до минимума (не может быть отрицательным)
            return max(0.0, value)
        elif field_name == "subjective_time":
            return max(0.0, value)
        elif field_name == "ticks":
            if value < 0:
                raise ValueError(f"ticks must be >= 0, got {value}")
            return int(value)
        return value

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
        """Переопределение setattr для валидации и защиты полей"""
        # Разрешаем установку внутренних полей без валидации
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return

        # Проверяем, инициализирован ли объект (безопасно через hasattr)
        is_initialized = hasattr(self, "_initialized") and self._initialized

        # Защита неизменяемых полей (только после инициализации)
        if is_initialized and name in ["life_id", "birth_timestamp"]:
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
            "last_event_intensity",
            "ticks",
        ]:
            value = self._validate_field(name, value)

        # Устанавливаем значение
        object.__setattr__(self, name, value)

        # Логируем изменение (только после инициализации и если значение изменилось)
        if is_initialized and old_value is not None and old_value != value:
            self._log_change(name, old_value, value)

        # Автоматически обновляем active при изменении vital параметров (только после инициализации)
        if is_initialized and name in ["energy", "integrity", "stability"]:
            object.__setattr__(self, "active", self.is_active())

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

    def is_active(self) -> bool:
        """
        Проверка жизнеспособности состояния.
        Возвращает True если все vital параметры > 0.
        """
        return self.energy > 0.0 and self.integrity > 0.0 and self.stability > 0.0

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
        """Применение дельт к полям с валидацией"""
        for key, delta in deltas.items():
            if hasattr(self, key):
                current = getattr(self, key)
                if isinstance(current, (int, float)):
                    new_value = current + delta
                    # Валидация происходит автоматически через __setattr__
                    setattr(self, key, new_value)
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
                logger.warning(f"Отсутствует секция {section_name} в learning_params, используем значения по умолчанию")
                validated_params[section_name] = self._get_default_learning_params()[section_name]
                continue

            section = params[section_name]
            if not isinstance(section, dict):
                logger.warning(f"Секция {section_name} не является словарем, используем значения по умолчанию")
                validated_params[section_name] = self._get_default_learning_params()[section_name]
                continue

            validated_section = {}
            for key in expected_keys:
                if key not in section:
                    logger.warning(f"Отсутствует ключ {key} в секции {section_name}, используем значение по умолчанию")
                    validated_section[key] = self._get_default_learning_params()[section_name][key]
                    continue

                value = section[key]
                if not isinstance(value, (int, float)):
                    logger.warning(f"Значение {key} в секции {section_name} не является числом ({type(value)}), используем значение по умолчанию")
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
            logger.warning("adaptation_params не является словарем, используем значения по умолчанию")
            return self._get_default_adaptation_params()

        validated_params = {}

        for section_name, expected_keys in expected_structure.items():
            if section_name not in params:
                logger.warning(f"Отсутствует секция {section_name} в adaptation_params, используем значения по умолчанию")
                validated_params[section_name] = self._get_default_adaptation_params()[section_name]
                continue

            section = params[section_name]
            if not isinstance(section, dict):
                logger.warning(f"Секция {section_name} не является словарем, используем значения по умолчанию")
                validated_params[section_name] = self._get_default_adaptation_params()[section_name]
                continue

            validated_section = {}
            for key in expected_keys:
                if key not in section:
                    logger.warning(f"Отсутствует ключ {key} в секции {section_name}, используем значение по умолчанию")
                    validated_section[key] = self._get_default_adaptation_params()[section_name][key]
                    continue

                value = section[key]
                if not isinstance(value, (int, float)):
                    logger.warning(f"Значение {key} в секции {section_name} не является числом ({type(value)}), используем значение по умолчанию")
                    validated_section[key] = self._get_default_adaptation_params()[section_name][key]
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
        return self._load_snapshot_from_data(data)

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
        }
        mapped_data = {}
        for k, v in data.items():
            mapped_key = field_mapping.get(k, k)
            if mapped_key in SelfState.__dataclass_fields__:
                mapped_data[mapped_key] = v

        # Валидация и исправление learning_params
        if "learning_params" in mapped_data:
            mapped_data["learning_params"] = self._validate_learning_params(mapped_data["learning_params"])
        else:
            logger.info("learning_params отсутствуют в snapshot, будут использованы значения по умолчанию")

        # Валидация и исправление adaptation_params
        if "adaptation_params" in mapped_data:
            mapped_data["adaptation_params"] = self._validate_adaptation_params(mapped_data["adaptation_params"])
        else:
            logger.info("adaptation_params отсутствуют в snapshot, будут использованы значения по умолчанию")

        # Удаляем поля, которые не должны передаваться в __init__
        if "archive_memory" in mapped_data:
            mapped_data.pop("archive_memory")

        # Конвертировать memory из list of dict в list of MemoryEntry
        memory_entries = []
        if "memory" in mapped_data:
            memory_entries = [MemoryEntry(**entry) for entry in mapped_data["memory"]]
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

        logger.info("Snapshot загружен успешно с валидацией learning_params и adaptation_params")
        return state


def create_initial_state() -> SelfState:
    state = SelfState()
    # Инициализируем архивную память
    state.archive_memory = ArchiveMemory()
    # Инициализируем memory с архивом (__post_init__ уже создал memory, но пересоздадим с правильным архивом)
    state.memory = Memory(archive=state.archive_memory)
    return state


def save_snapshot(state: SelfState, compress: bool = False):
    """
    Сохраняет текущее состояние жизни как отдельный JSON файл.
    Оптимизированная сериализация с исключением transient полей.

    ПРИМЕЧАНИЕ: Логирование временно отключается во время сериализации для производительности.
    Изменения состояния, которые могут произойти во время вызова asdict() (например,
    конвертация dataclass), не будут залогированы. Это намеренное решение для оптимизации.

    Args:
        state: Состояние для сохранения
        compress: Если True, использовать сжатие gzip (не реализовано пока)
    """
    # Сбрасываем буфер логов перед сериализацией
    state._flush_log_buffer()

    # Временно отключаем логирование для сериализации
    # Это предотвращает логирование изменений, которые могут произойти при конвертации dataclass
    logging_was_enabled = state._logging_enabled
    state.disable_logging()

    try:
        snapshot = asdict(state)
        # Исключаем transient поля
        snapshot.pop("activated_memory", None)
        snapshot.pop("last_pattern", None)
        snapshot.pop("_initialized", None)
        snapshot.pop("_logging_enabled", None)
        snapshot.pop("_log_only_critical", None)
        snapshot.pop("_log_buffer", None)
        snapshot.pop("_log_buffer_size", None)

        # Оптимизированная конвертация Memory в list
        if isinstance(state.memory, Memory):
            # Используем более эффективную сериализацию
            snapshot["memory"] = [
                {
                    "event_type": entry.event_type,
                    "meaning_significance": entry.meaning_significance,
                    "timestamp": entry.timestamp,
                    "weight": entry.weight,
                    "feedback_data": entry.feedback_data,
                }
                for entry in state.memory
            ]

        tick = snapshot["ticks"]
        filename = SNAPSHOT_DIR / f"snapshot_{tick:06d}.json"

        # Оптимизированная запись без лишних отступов (меньше размер файла)
        with filename.open("w") as f:
            json.dump(snapshot, f, separators=(",", ":"), default=str)
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
