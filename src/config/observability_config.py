"""
Конфигурация системы наблюдаемости Life.

Загружает настройки из config/observability.yaml и предоставляет
типизированный доступ к конфигурационным параметрам.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

try:
    import yaml
except ImportError:
    yaml = None
    logger.warning("PyYAML not available, using fallback config loading")


@dataclass
class StructuredLoggingConfig:
    """Конфигурация структурированного логирования."""
    enabled: bool = True
    log_file: str = "data/structured_log.jsonl"
    flush_period_ticks: int = 10
    max_file_size_mb: int = 100
    backup_count: int = 5


@dataclass
class PassiveDataSinkConfig:
    """Конфигурация пассивного приемника данных."""
    enabled: bool = True
    data_directory: str = "data"
    observations_file: str = "passive_observations.jsonl"
    max_file_age_days: int = 30


@dataclass
class RawDataCollectorConfig:
    """Конфигурация сборщика сырых данных."""
    enabled: bool = True
    logs_directory: str = "logs"
    snapshots_directory: str = "data/snapshots"
    structured_log_file: str = "data/structured_log.jsonl"
    default_observation_hours: int = 24
    max_time_range_days: int = 30


@dataclass
class DataAccessConfig:
    """Конфигурация доступа к данным."""
    enabled: bool = True
    data_directory: str = "data"
    observations_file: str = "passive_observations.jsonl"
    snapshots_directory: str = "data/snapshots"
    export_hours_default: int = 24
    max_export_hours: int = 168


@dataclass
class UnifiedAPIConfig:
    """Конфигурация единого API."""
    enabled: bool = True
    data_directory: str = "data"
    logs_directory: str = "logs"
    snapshots_directory: str = "data/snapshots"
    structured_log_file: str = "data/structured_log.jsonl"
    emergency_collection_hours: int = 1


@dataclass
class ErrorHandlingConfig:
    """Конфигурация обработки ошибок."""
    graceful_degradation: bool = True
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    disable_on_persistent_errors: bool = True
    error_log_file: str = "logs/observability_errors.log"


@dataclass
class PerformanceConfig:
    """Конфигурация производительности."""
    buffer_size: int = 1000
    flush_interval_seconds: float = 30.0
    async_queue_size: int = 1000
    thread_pool_size: int = 4


@dataclass
class SecurityConfig:
    """Конфигурация безопасности."""
    allow_file_access: bool = True
    restrict_paths: bool = True
    allowed_directories: List[str] = field(default_factory=lambda: ["data", "logs", "metrics"])
    deny_patterns: List[str] = field(default_factory=lambda: [
        "**/*.env", "**/credentials*", "**/secrets*"
    ])


@dataclass
class ObservabilityConfig:
    """Основная конфигурация системы наблюдаемости."""

    # Основные настройки
    enabled: bool = True
    data_directory: str = "data"
    logs_directory: str = "logs"

    # Компонентные конфигурации
    structured_logging: StructuredLoggingConfig = field(default_factory=StructuredLoggingConfig)
    passive_data_sink: PassiveDataSinkConfig = field(default_factory=PassiveDataSinkConfig)
    raw_data_collector: RawDataCollectorConfig = field(default_factory=RawDataCollectorConfig)
    data_access: DataAccessConfig = field(default_factory=DataAccessConfig)
    unified_api: UnifiedAPIConfig = field(default_factory=UnifiedAPIConfig)
    error_handling: ErrorHandlingConfig = field(default_factory=ErrorHandlingConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ObservabilityConfig':
        """Создать конфигурацию из словаря."""
        # Извлечь основные настройки
        enabled = config_dict.get('observability', {}).get('enabled', True)
        data_directory = config_dict.get('observability', {}).get('data_directory', 'data')
        logs_directory = config_dict.get('observability', {}).get('logs_directory', 'logs')

        # Создать конфигурации компонентов
        structured_logging = StructuredLoggingConfig(**config_dict.get('structured_logging', {}))
        passive_data_sink = PassiveDataSinkConfig(**config_dict.get('passive_data_sink', {}))
        raw_data_collector = RawDataCollectorConfig(**config_dict.get('raw_data_collector', {}))
        data_access = DataAccessConfig(**config_dict.get('data_access', {}))
        unified_api = UnifiedAPIConfig(**config_dict.get('unified_api', {}))
        error_handling = ErrorHandlingConfig(**config_dict.get('error_handling', {}))
        performance = PerformanceConfig(**config_dict.get('performance', {}))
        security = SecurityConfig(**config_dict.get('security', {}))

        return cls(
            enabled=enabled,
            data_directory=data_directory,
            logs_directory=logs_directory,
            structured_logging=structured_logging,
            passive_data_sink=passive_data_sink,
            raw_data_collector=raw_data_collector,
            data_access=data_access,
            unified_api=unified_api,
            error_handling=error_handling,
            performance=performance,
            security=security
        )

    @classmethod
    def load_from_file(cls, config_path: Optional[str] = None) -> 'ObservabilityConfig':
        """
        Загрузить конфигурацию из файла.

        Args:
            config_path: Путь к файлу конфигурации (по умолчанию config/observability.yaml)

        Returns:
            Загруженная конфигурация
        """
        if config_path is None:
            config_path = "config/observability.yaml"

        config_path = Path(config_path)

        if not config_path.exists():
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return cls()

        try:
            if yaml is not None:
                # Использовать YAML если доступен
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_dict = yaml.safe_load(f) or {}
            else:
                # Fallback: простой текстовый парсинг (ограниченная функциональность)
                logger.warning("YAML not available, using basic config parsing")
                config_dict = cls._parse_basic_config(config_path)

            return cls.from_dict(config_dict)

        except Exception as e:
            logger.error(f"Failed to load observability config from {config_path}: {e}")
            logger.warning("Using default configuration")
            return cls()

    @staticmethod
    def _parse_basic_config(config_path: Path) -> Dict[str, Any]:
        """Базовый парсинг конфигурации без YAML (fallback)."""
        config_dict = {}

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('#') or not line:
                        continue

                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()

                        # Простой парсинг значений
                        if value.lower() in ('true', 'false'):
                            value = value.lower() == 'true'
                        elif value.isdigit():
                            value = int(value)
                        elif value.replace('.', '').isdigit():
                            value = float(value)

                        config_dict[key] = value

        except Exception as e:
            logger.warning(f"Failed to parse basic config: {e}")

        return config_dict

    def validate_security(self, path: str) -> bool:
        """
        Проверить путь на соответствие настройкам безопасности.

        Args:
            path: Путь для проверки

        Returns:
            True если путь разрешен
        """
        if not self.security.restrict_paths:
            return True

        path_obj = Path(path)

        # Проверить запрещенные паттерны
        for pattern in self.security.deny_patterns:
            if path_obj.match(pattern):
                return False

        # Проверить разрешенные директории
        for allowed_dir in self.security.allowed_directories:
            try:
                path_obj.relative_to(allowed_dir)
                return True
            except ValueError:
                continue

        return False


# Глобальная конфигурация
_config_instance: Optional[ObservabilityConfig] = None


def get_observability_config() -> ObservabilityConfig:
    """Получить глобальную конфигурацию observability."""
    global _config_instance

    if _config_instance is None:
        _config_instance = ObservabilityConfig.load_from_file()

    return _config_instance


def reload_observability_config() -> ObservabilityConfig:
    """Перезагрузить конфигурацию observability."""
    global _config_instance
    _config_instance = ObservabilityConfig.load_from_file()
    logger.info("Observability configuration reloaded")
    return _config_instance