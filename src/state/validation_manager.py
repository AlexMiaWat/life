"""
Validation Manager - валидация и логирование параметров состояния.

Отвечает за валидацию значений параметров, логирование изменений
и поддержание истории изменений.
"""

import json
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .core_state import CoreState


@dataclass
class ParameterChange:
    """
    Структура для отслеживания изменений параметров системы.
    """

    timestamp: float
    tick: int
    parameter_name: str
    old_value: Any
    new_value: Any
    reason: str  # "delta_application", "learning_update", "adaptation_update", etc.
    context: Dict[str, Any] = None

    def __post_init__(self):
        if self.context is None:
            self.context = {}


class ValidationManager:
    """
    Менеджер валидации и логирования параметров.

    Отвечает за:
    - Валидацию значений параметров
    - Логирование изменений состояния
    - Управление историей изменений
    """

    def __init__(self, core_state: CoreState):
        """
        Инициализация менеджера валидации.

        Args:
            core_state: Ссылка на базовое состояние
        """
        self.core_state = core_state

        # Thread-safety
        self._api_lock = threading.RLock()

        # Logging configuration
        self._logging_enabled = True
        self._log_only_critical = False
        self._log_buffer: List[dict] = []
        self._log_buffer_size: int = 100
        self._loading_from_snapshot = False

        # Log file management
        self._state_changes_log_dir = Path("data/logs")
        self._state_changes_log_dir.mkdir(parents=True, exist_ok=True)
        self._state_changes_log_file = self._state_changes_log_dir / "state_changes.jsonl"
        self._max_log_file_size = 10 * 1024 * 1024  # 10MB

    def validate_field(self, field_name: str, value: float, clamp: bool = False) -> float:
        """
        Валидация значения поля с учетом его границ.

        Args:
            field_name: Имя поля
            value: Значение для валидации
            clamp: Если True, обрезать значение до границ вместо выбрасывания ошибки

        Returns:
            Валидированное значение
        """
        # Импортируем здесь чтобы избежать циклических зависимостей
        from ..validation.field_validator import FieldValidator

        return FieldValidator.validate_field(field_name, value, clamp)

    def _is_critical_field(self, field_name: str) -> bool:
        """Проверка, является ли поле критичным (vital параметры)"""
        return field_name in ["energy", "integrity", "stability"]

    def _record_parameter_change(
        self, parameter_name: str, old_value, new_value, reason: str, context: dict = None
    ) -> None:
        """
        Записывает изменение параметра в parameter_history.

        Args:
            parameter_name: Имя измененного параметра
            old_value: Старое значение
            new_value: Новое значение
            reason: Причина изменения
            context: Дополнительная информация
        """
        if context is None:
            context = {}

        change = ParameterChange(
            timestamp=time.time(),
            tick=self.core_state.ticks,
            parameter_name=parameter_name,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            context=context,
        )

        # Thread-safe добавление в историю
        with self._api_lock:
            self.core_state.parameter_history.append(change)

            # Ограничиваем размер истории (последние 1000 изменений)
            if len(self.core_state.parameter_history) > 1000:
                self.core_state.parameter_history = self.core_state.parameter_history[-1000:]

    def _log_change(self, field_name: str, old_value, new_value) -> None:
        """
        Логирование изменения поля в append-only лог.
        """
        if not self._logging_enabled:
            return

        # Если включен режим "только критичные", пропускаем некритичные поля
        if self._log_only_critical and not self._is_critical_field(field_name):
            return

        try:
            # Записываем в parameter_history
            self._record_parameter_change(field_name, old_value, new_value, "field_update")

            log_entry = {
                "timestamp": time.time(),
                "life_id": self.core_state.life_id,
                "tick": self.core_state.ticks,
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
            # Игнорируем ошибки логирования
            pass

    def _flush_log_buffer(self) -> None:
        """Запись буфера логов на диск"""
        if not self._log_buffer:
            return

        try:
            # Проверяем размер файла и ротируем при необходимости
            self._rotate_log_if_needed()

            with self._state_changes_log_file.open("a") as f:
                for log_entry in self._log_buffer:
                    f.write(json.dumps(log_entry, default=str) + "\n")

            # Очищаем буфер
            self._log_buffer.clear()
        except Exception:
            # Игнорируем ошибки логирования
            pass

    def _rotate_log_if_needed(self) -> None:
        """Ротация лог-файла при достижении максимального размера"""
        if not self._state_changes_log_file.exists():
            return

        try:
            file_size = self._state_changes_log_file.stat().st_size
            if file_size >= self._max_log_file_size:
                # Создаем резервную копию с timestamp
                timestamp = int(time.time())
                backup_file = self._state_changes_log_dir / f"state_changes_{timestamp}.jsonl.backup"
                self._state_changes_log_file.rename(backup_file)
                # Создаем новый пустой файл
                self._state_changes_log_file.touch()

                # Очищаем старые резервные копии
                self._cleanup_old_backups()
        except Exception:
            pass

    def _cleanup_old_backups(self, max_age_days: int = 30, max_backups: int = 10) -> None:
        """Очистка старых резервных копий логов"""
        try:
            backup_files = list(self._state_changes_log_dir.glob("state_changes_*.jsonl.backup"))

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
                        pass

            # Ограничиваем количество копий
            if len(backup_files) > max_backups:
                for backup_file in backup_files[max_backups:]:
                    try:
                        backup_file.unlink()
                    except Exception:
                        pass
        except Exception:
            pass

    def enable_logging(self) -> None:
        """Включить логирование изменений"""
        self._logging_enabled = True
        self._flush_log_buffer()

    def disable_logging(self) -> None:
        """Отключить логирование изменений"""
        self._flush_log_buffer()
        self._logging_enabled = False

    def set_log_only_critical(self, enabled: bool = True) -> None:
        """Установить режим логирования только критичных изменений"""
        self._log_only_critical = enabled

    def set_log_buffer_size(self, size: int) -> None:
        """Установить размер буфера для батчинга логов"""
        if size < 1:
            raise ValueError("Buffer size must be >= 1")
        self._log_buffer_size = size
        if len(self._log_buffer) >= size:
            self._flush_log_buffer()

    def apply_delta(self, deltas: dict[str, float]) -> None:
        """Применение дельт к полям с потокобезопасностью"""
        with self._api_lock:
            for key, delta in deltas.items():
                if hasattr(self.core_state, key):
                    current = getattr(self.core_state, key)
                    if isinstance(current, (int, float)):
                        new_value = current + delta
                        # Clamp для performance тестов
                        if key in ["energy", "integrity", "stability"]:
                            clamped_value = max(0.0, min(100.0 if key == "energy" else 1.0, new_value))
                        elif key in ["fatigue", "tension", "age", "subjective_time"]:
                            clamped_value = max(0.0, new_value)
                        elif key == "ticks":
                            clamped_value = max(0, int(new_value))
                        else:
                            clamped_value = new_value

                        # Устанавливаем без дополнительной валидации
                        object.__setattr__(self.core_state, key, clamped_value)

                        # Логируем изменение вручную
                        if self.core_state.__class__.__name__ == "SelfState" and current != clamped_value:
                            self._log_change(key, current, clamped_value)
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