"""
Конфигурация структурированного логирования Life.

Загружает настройки из config/observability.yaml для StructuredLogger.
После признания активной архитектуры - упрощенная конфигурация только для логирования.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

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
    log_directory: str = "data/logs"
    log_file: str = "structured_log.jsonl"
    flush_period_ticks: int = 10
    max_file_size_mb: int = 100
    backup_count: int = 5
    enable_console: bool = False
    enable_file: bool = True


@dataclass
class ObservabilityConfig:
    """Основная конфигурация системы наблюдаемости (упрощенная)."""

    # Основные настройки
    enabled: bool = True
    data_directory: str = "data"

    # Единственная компонентная конфигурация
    structured_logging: StructuredLoggingConfig = StructuredLoggingConfig()

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ObservabilityConfig':
        """Создать конфигурацию из словаря."""
        # Извлечь основные настройки
        enabled = config_dict.get('enabled', True)
        data_directory = config_dict.get('data_directory', 'data')

        # Создать конфигурацию структурированного логирования
        structured_logging = StructuredLoggingConfig(**config_dict.get('structured_logging', {}))

        return cls(
            enabled=enabled,
            data_directory=data_directory,
            structured_logging=structured_logging
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
                # Fallback: простые значения по умолчанию
                logger.warning("YAML not available, using defaults")
                config_dict = {}

            return cls.from_dict(config_dict)

        except Exception as e:
            logger.error(f"Failed to load observability config from {config_path}: {e}")
            logger.warning("Using default configuration")
            return cls()


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