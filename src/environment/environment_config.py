"""
Конфигурация параметров внешней среды для API.

Управление настройками генерации событий и режимами активности среды.
"""

import json
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path

from logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class EventTypeConfig:
    """Конфигурация типа события"""

    enabled: bool = True
    weight: float = 1.0
    intensity_min: float = 0.0
    intensity_max: float = 1.0
    description: str = ""


@dataclass
class EnvironmentConfig:
    """Конфигурация внешней среды"""

    # Режим активности среды
    activity_level: float = 1.0  # [0.0, 2.0] - множитель частоты генерации

    # Режим кризиса
    crisis_mode: bool = False
    crisis_probability: float = 0.05  # Вероятность перехода в кризис

    # Настройки типов событий
    event_types: Dict[str, EventTypeConfig] = field(default_factory=dict)

    # Пользовательские параметры генерации
    custom_weights: Optional[Dict[str, float]] = None

    def __post_init__(self):
        """Инициализация конфигурации"""
        if not self.event_types:
            self._initialize_default_event_types()

    def _initialize_default_event_types(self):
        """Инициализировать конфигурацию типов событий по умолчанию"""
        default_configs = {
            # Физические события
            "noise": EventTypeConfig(
                weight=0.352, intensity_min=-0.3, intensity_max=0.3, description="Фоновый шум"
            ),
            "decay": EventTypeConfig(
                weight=0.244,
                intensity_min=-0.5,
                intensity_max=0.0,
                description="Естественный распад",
            ),
            "recovery": EventTypeConfig(
                weight=0.180, intensity_min=0.0, intensity_max=0.5, description="Восстановление"
            ),
            "shock": EventTypeConfig(
                weight=0.040, intensity_min=-1.0, intensity_max=1.0, description="Резкий удар"
            ),
            "idle": EventTypeConfig(
                weight=0.040, intensity_min=0.0, intensity_max=0.0, description="Тишина"
            ),
            # Социальные события
            "social_presence": EventTypeConfig(
                weight=0.014,
                intensity_min=-0.4,
                intensity_max=0.4,
                description="Ощущение присутствия других",
            ),
            "social_conflict": EventTypeConfig(
                weight=0.010,
                intensity_min=-0.6,
                intensity_max=0.0,
                description="Социальный конфликт",
            ),
            "social_harmony": EventTypeConfig(
                weight=0.010,
                intensity_min=0.0,
                intensity_max=0.6,
                description="Социальная гармония",
            ),
            # Когнитивные события
            "cognitive_doubt": EventTypeConfig(
                weight=0.014,
                intensity_min=-0.5,
                intensity_max=0.0,
                description="Когнитивное сомнение",
            ),
            "cognitive_clarity": EventTypeConfig(
                weight=0.010,
                intensity_min=0.0,
                intensity_max=0.5,
                description="Когнитивная ясность",
            ),
            "cognitive_confusion": EventTypeConfig(
                weight=0.014,
                intensity_min=-0.4,
                intensity_max=0.0,
                description="Когнитивная путаница",
            ),
            # Экзистенциальные события
            "existential_void": EventTypeConfig(
                weight=0.007,
                intensity_min=-0.7,
                intensity_max=0.0,
                description="Экзистенциальная пустота",
            ),
            "existential_purpose": EventTypeConfig(
                weight=0.006,
                intensity_min=0.0,
                intensity_max=0.7,
                description="Экзистенциальное ощущение цели",
            ),
            "existential_finitude": EventTypeConfig(
                weight=0.008,
                intensity_min=-0.6,
                intensity_max=0.0,
                description="Осознание конечности",
            ),
            # Другие события
            "connection": EventTypeConfig(
                weight=0.007, intensity_min=0.0, intensity_max=0.8, description="Ощущение связи"
            ),
            "isolation": EventTypeConfig(
                weight=0.007, intensity_min=-0.7, intensity_max=0.0, description="Ощущение изоляции"
            ),
            "insight": EventTypeConfig(
                weight=0.007, intensity_min=0.0, intensity_max=0.6, description="Момент озарения"
            ),
            "confusion": EventTypeConfig(
                weight=0.007,
                intensity_min=-0.5,
                intensity_max=0.0,
                description="Состояние замешательства",
            ),
            "curiosity": EventTypeConfig(
                weight=0.007, intensity_min=-0.3, intensity_max=0.4, description="Любопытство"
            ),
            "meaning_found": EventTypeConfig(
                weight=0.007, intensity_min=0.0, intensity_max=0.9, description="Нахождение смысла"
            ),
            "void": EventTypeConfig(
                weight=0.007, intensity_min=-0.8, intensity_max=0.0, description="Ощущение пустоты"
            ),
            "acceptance": EventTypeConfig(
                weight=0.007, intensity_min=0.0, intensity_max=0.5, description="Принятие состояния"
            ),
        }

        self.event_types = default_configs

    def get_enabled_event_types(self) -> List[str]:
        """Получить список включенных типов событий"""
        return [event_type for event_type, config in self.event_types.items() if config.enabled]

    def get_event_weights(self) -> Dict[str, float]:
        """Получить веса для генерации событий"""
        if self.custom_weights:
            # Используем пользовательские веса, но только для включенных типов
            weights = {}
            for event_type, config in self.event_types.items():
                if config.enabled:
                    weights[event_type] = self.custom_weights.get(event_type, config.weight)
            return weights
        else:
            # Используем веса из конфигурации
            return {
                event_type: config.weight
                for event_type, config in self.event_types.items()
                if config.enabled
            }

    def get_intensity_range(self, event_type: str) -> tuple[float, float]:
        """Получить диапазон интенсивности для типа события"""
        if event_type in self.event_types:
            config = self.event_types[event_type]
            return (config.intensity_min, config.intensity_max)
        return (0.0, 1.0)  # Дефолтный диапазон

    def set_activity_mode(self, mode: str) -> bool:
        """Установить режим активности среды"""
        mode_configs = {
            "quiet": {"activity_level": 0.2, "crisis_probability": 0.01},
            "normal": {"activity_level": 1.0, "crisis_probability": 0.05},
            "active": {"activity_level": 1.5, "crisis_probability": 0.08},
            "storm": {"activity_level": 2.0, "crisis_probability": 0.15, "crisis_mode": True},
        }

        if mode not in mode_configs:
            return False

        config = mode_configs[mode]
        self.activity_level = config["activity_level"]
        self.crisis_probability = config["crisis_probability"]
        self.crisis_mode = config.get("crisis_mode", False)

        logger.info(
            f"Environment mode set to '{mode}': activity={self.activity_level}, crisis_prob={self.crisis_probability}"
        )
        return True

    def update_event_type_config(self, event_type: str, **kwargs) -> bool:
        """Обновить конфигурацию типа события"""
        if event_type not in self.event_types:
            return False

        config = self.event_types[event_type]
        valid_fields = ["enabled", "weight", "intensity_min", "intensity_max", "description"]

        updated = False
        for field_name, value in kwargs.items():
            if field_name in valid_fields:
                setattr(config, field_name, value)
                updated = True

        if updated:
            logger.info(f"Updated configuration for event type '{event_type}': {kwargs}")

        return updated

    def reset_to_defaults(self):
        """Сбросить конфигурацию к значениям по умолчанию"""
        self.activity_level = 1.0
        self.crisis_mode = False
        self.crisis_probability = 0.05
        self.custom_weights = None
        self._initialize_default_event_types()
        logger.info("Environment configuration reset to defaults")

    def to_dict(self) -> Dict[str, Any]:
        """Сериализовать конфигурацию в словарь"""
        return {
            "activity_level": self.activity_level,
            "crisis_mode": self.crisis_mode,
            "crisis_probability": self.crisis_probability,
            "custom_weights": self.custom_weights,
            "event_types": {
                event_type: {
                    "enabled": config.enabled,
                    "weight": config.weight,
                    "intensity_min": config.intensity_min,
                    "intensity_max": config.intensity_max,
                    "description": config.description,
                }
                for event_type, config in self.event_types.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnvironmentConfig":
        """Создать конфигурацию из словаря"""
        config = cls()
        config.activity_level = data.get("activity_level", 1.0)
        config.crisis_mode = data.get("crisis_mode", False)
        config.crisis_probability = data.get("crisis_probability", 0.05)
        config.custom_weights = data.get("custom_weights", None)

        # Загружаем конфигурации типов событий
        event_types_data = data.get("event_types", {})
        for event_type, type_data in event_types_data.items():
            if event_type in config.event_types:
                config.event_types[event_type] = EventTypeConfig(
                    enabled=type_data.get("enabled", True),
                    weight=type_data.get("weight", 1.0),
                    intensity_min=type_data.get("intensity_min", 0.0),
                    intensity_max=type_data.get("intensity_max", 1.0),
                    description=type_data.get("description", ""),
                )

        return config


class EnvironmentConfigManager:
    """Менеджер конфигурации среды"""

    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or Path("data/environment_config.json")
        self.config = EnvironmentConfig()
        self.lock = threading.RLock()

        # Загружаем сохраненную конфигурацию
        self.load_config()

    def load_config(self):
        """Загрузить конфигурацию из файла"""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.config = EnvironmentConfig.from_dict(data)
                logger.info(f"Loaded environment configuration from {self.config_file}")
            else:
                logger.info("Using default environment configuration")
        except Exception as e:
            logger.error(f"Failed to load environment configuration: {e}")
            logger.info("Using default environment configuration")

    def save_config(self):
        """Сохранить конфигурацию в файл"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config.to_dict(), f, indent=2, ensure_ascii=False)
            logger.info(f"Saved environment configuration to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save environment configuration: {e}")
            return False

    def get_config(self) -> EnvironmentConfig:
        """Получить текущую конфигурацию"""
        with self.lock:
            return self.config

    def update_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Обновить конфигурацию"""
        with self.lock:
            updated_fields = []

            # Обновляем основные параметры
            if "activity_level" in updates:
                self.config.activity_level = max(0.0, min(2.0, updates["activity_level"]))
                updated_fields.append("activity_level")

            if "crisis_mode" in updates:
                self.config.crisis_mode = bool(updates["crisis_mode"])
                updated_fields.append("crisis_mode")

            if "crisis_probability" in updates:
                self.config.crisis_probability = max(0.0, min(1.0, updates["crisis_probability"]))
                updated_fields.append("crisis_probability")

            if "custom_weights" in updates:
                self.config.custom_weights = updates["custom_weights"]
                updated_fields.append("custom_weights")

            # Обновляем режим активности
            if "activity_mode" in updates:
                if self.config.set_activity_mode(updates["activity_mode"]):
                    updated_fields.append("activity_mode")

            # Обновляем конфигурации типов событий
            if "event_types" in updates:
                event_types_updates = updates["event_types"]
                for event_type, type_updates in event_types_updates.items():
                    if self.config.update_event_type_config(event_type, **type_updates):
                        updated_fields.append(f"event_type_{event_type}")

            # Сохраняем изменения
            if updated_fields:
                self.save_config()
                return {
                    "success": True,
                    "updated_fields": updated_fields,
                    "message": f"Updated {len(updated_fields)} configuration fields",
                }
            else:
                return {"success": False, "error": "No valid fields to update"}

    def reset_config(self) -> Dict[str, Any]:
        """Сбросить конфигурацию к значениям по умолчанию"""
        with self.lock:
            self.config.reset_to_defaults()
            self.save_config()
            return {"success": True, "message": "Configuration reset to defaults"}

    def get_available_modes(self) -> List[str]:
        """Получить список доступных режимов активности"""
        return ["quiet", "normal", "active", "storm"]

    def get_config_summary(self) -> Dict[str, Any]:
        """Получить сводку текущей конфигурации"""
        with self.lock:
            enabled_types = self.config.get_enabled_event_types()
            return {
                "activity_level": self.config.activity_level,
                "crisis_mode": self.config.crisis_mode,
                "crisis_probability": self.config.crisis_probability,
                "enabled_event_types_count": len(enabled_types),
                "total_event_types_count": len(self.config.event_types),
                "has_custom_weights": self.config.custom_weights is not None,
                "enabled_event_types_sample": enabled_types[:10],  # Первые 10 для preview
            }
