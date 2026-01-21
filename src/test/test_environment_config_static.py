"""
Статические тесты для EnvironmentConfigManager - менеджера конфигурации внешней среды.

Проверяет базовую функциональность управления конфигурацией параметров среды.
"""

import pytest
import json
from unittest.mock import Mock, patch, mock_open

from src.environment.environment_config import (
    EnvironmentConfigManager,
    EnvironmentConfig,
    EventTypeConfig,
)


class TestEventTypeConfig:
    """Тесты для EventTypeConfig"""

    def test_event_type_config_creation(self):
        """Тест создания конфигурации типа события"""
        config = EventTypeConfig(
            enabled=True,
            weight=2.0,
            intensity_min=0.1,
            intensity_max=0.9,
            description="Test event type",
        )

        assert config.enabled is True
        assert config.weight == 2.0
        assert config.intensity_min == 0.1
        assert config.intensity_max == 0.9
        assert config.description == "Test event type"

    def test_event_type_config_defaults(self):
        """Тест значений по умолчанию для EventTypeConfig"""
        config = EventTypeConfig()

        assert config.enabled is True
        assert config.weight == 1.0
        assert config.intensity_min == 0.0
        assert config.intensity_max == 1.0
        assert config.description == ""


class TestEnvironmentConfig:
    """Тесты для EnvironmentConfig"""

    def test_config_creation(self):
        """Тест создания конфигурации среды"""
        event_types = {
            "positive": EventTypeConfig(enabled=True, weight=1.5),
            "negative": EventTypeConfig(enabled=False, weight=0.5),
        }

        config = EnvironmentConfig(
            activity_level=1.5,
            crisis_mode=True,
            crisis_probability=0.1,
            event_types=event_types,
            custom_weights={"stress": 2.0},
        )

        assert config.activity_level == 1.5
        assert config.crisis_mode is True
        assert config.crisis_probability == 0.1
        assert len(config.event_types) == 2
        assert config.event_types["positive"].weight == 1.5
        assert config.event_types["negative"].weight == 0.5
        assert config.custom_weights == {"stress": 2.0}

    def test_config_defaults(self):
        """Тест значений по умолчанию для EnvironmentConfig"""
        config = EnvironmentConfig()

        assert config.activity_level == 1.0
        assert config.crisis_mode is False
        assert config.crisis_probability == 0.05
        assert isinstance(config.event_types, dict)
        assert config.custom_weights is None

    def test_config_post_init(self):
        """Тест инициализации конфигурации"""
        config = EnvironmentConfig()
        config._initialize_default_event_types()

        # Проверяем, что созданы типы событий по умолчанию
        assert len(config.event_types) > 0
        assert "positive" in config.event_types
        assert "negative" in config.event_types
        assert "neutral" in config.event_types

    def test_config_to_dict(self):
        """Тест сериализации конфигурации в словарь"""
        config = EnvironmentConfig(activity_level=1.2, crisis_mode=True, crisis_probability=0.08)

        config_dict = config.to_dict()

        assert config_dict["activity_level"] == 1.2
        assert config_dict["crisis_mode"] is True
        assert config_dict["crisis_probability"] == 0.08
        assert "event_types" in config_dict

    def test_config_from_dict(self):
        """Тест создания конфигурации из словаря"""
        config_dict = {
            "activity_level": 1.5,
            "crisis_mode": True,
            "crisis_probability": 0.1,
            "event_types": {
                "positive": {
                    "enabled": True,
                    "weight": 2.0,
                    "intensity_min": 0.0,
                    "intensity_max": 1.0,
                    "description": "Positive events",
                }
            },
            "custom_weights": {"stress": 1.5},
        }

        config = EnvironmentConfig.from_dict(config_dict)

        assert config.activity_level == 1.5
        assert config.crisis_mode is True
        assert config.crisis_probability == 0.1
        assert config.event_types["positive"].weight == 2.0
        assert config.custom_weights == {"stress": 1.5}


class TestEnvironmentConfigManager:
    """Тесты для EnvironmentConfigManager"""

    def test_manager_creation(self):
        """Тест создания менеджера конфигурации"""
        manager = EnvironmentConfigManager()

        assert isinstance(manager.config, EnvironmentConfig)
        assert manager.config.activity_level == 1.0
        assert manager.is_dirty is False

    @patch("src.environment.environment_config.Path")
    def test_load_config(self, mock_path):
        """Тест загрузки конфигурации из файла"""
        config_data = {"activity_level": 1.5, "crisis_mode": True, "crisis_probability": 0.1}

        mock_file = Mock()
        mock_file.exists.return_value = True
        mock_file.read_text.return_value = json.dumps(config_data)
        mock_path.return_value = mock_file

        manager = EnvironmentConfigManager()
        manager.load_config("config.json")

        assert manager.config.activity_level == 1.5
        assert manager.config.crisis_mode is True
        assert manager.config.crisis_probability == 0.1
        assert manager.is_dirty is False

    @patch("src.environment.environment_config.Path")
    def test_load_config_file_not_exists(self, mock_path):
        """Тест загрузки конфигурации при отсутствии файла"""
        mock_file = Mock()
        mock_file.exists.return_value = False
        mock_path.return_value = mock_file

        manager = EnvironmentConfigManager()
        manager.load_config("nonexistent.json")

        # Должна остаться конфигурация по умолчанию
        assert manager.config.activity_level == 1.0
        assert manager.config.crisis_mode is False

    @patch("src.environment.environment_config.Path")
    @patch("builtins.open", new_callable=mock_open)
    def test_save_config(self, mock_file_open, mock_path):
        """Тест сохранения конфигурации в файл"""
        mock_file = Mock()
        mock_path.return_value = mock_file

        manager = EnvironmentConfigManager()
        manager.config.activity_level = 1.5
        manager.is_dirty = True

        manager.save_config("config.json")

        # Проверяем, что файл был открыт для записи
        mock_file_open.assert_called_once()
        # Проверяем, что is_dirty сброшен
        assert manager.is_dirty is False

    def test_get_config(self):
        """Тест получения текущей конфигурации"""
        manager = EnvironmentConfigManager()
        manager.config.activity_level = 1.3

        config = manager.get_config()

        assert isinstance(config, EnvironmentConfig)
        assert config.activity_level == 1.3

    def test_update_config(self):
        """Тест обновления конфигурации"""
        manager = EnvironmentConfigManager()

        updates = {"activity_level": 1.8, "crisis_mode": True, "crisis_probability": 0.15}

        manager.update_config(updates)

        assert manager.config.activity_level == 1.8
        assert manager.config.crisis_mode is True
        assert manager.config.crisis_probability == 0.15
        assert manager.is_dirty is True

    def test_update_config_partial(self):
        """Тест частичного обновления конфигурации"""
        manager = EnvironmentConfigManager()
        manager.config.activity_level = 1.0

        # Обновляем только один параметр
        updates = {"activity_level": 2.0}

        manager.update_config(updates)

        assert manager.config.activity_level == 2.0
        assert manager.config.crisis_mode is False  # Не изменилось
        assert manager.is_dirty is True

    def test_reset_config(self):
        """Тест сброса конфигурации к значениям по умолчанию"""
        manager = EnvironmentConfigManager()

        # Изменяем конфигурацию
        manager.config.activity_level = 2.0
        manager.config.crisis_mode = True
        manager.is_dirty = True

        # Сбрасываем
        manager.reset_config()

        assert manager.config.activity_level == 1.0
        assert manager.config.crisis_mode is False
        assert manager.is_dirty is False

    def test_get_event_type_config(self):
        """Тест получения конфигурации типа события"""
        manager = EnvironmentConfigManager()

        # Получаем существующую конфигурацию
        config = manager.get_event_type_config("positive")
        assert isinstance(config, EventTypeConfig)
        assert config.enabled is True

        # Получаем несуществующую конфигурацию
        config = manager.get_event_type_config("nonexistent")
        assert config is None

    def test_update_event_type_config(self):
        """Тест обновления конфигурации типа события"""
        manager = EnvironmentConfigManager()

        updates = {
            "enabled": False,
            "weight": 0.5,
            "intensity_min": 0.2,
            "intensity_max": 0.8,
            "description": "Updated description",
        }

        manager.update_event_type_config("positive", updates)

        config = manager.get_event_type_config("positive")
        assert config.enabled is False
        assert config.weight == 0.5
        assert config.intensity_min == 0.2
        assert config.intensity_max == 0.8
        assert config.description == "Updated description"
        assert manager.is_dirty is True

    def test_update_event_type_config_new_type(self):
        """Тест обновления конфигурации нового типа события"""
        manager = EnvironmentConfigManager()

        updates = {"enabled": True, "weight": 3.0, "description": "New event type"}

        manager.update_event_type_config("custom_event", updates)

        config = manager.get_event_type_config("custom_event")
        assert config.enabled is True
        assert config.weight == 3.0
        assert config.description == "New event type"
        assert manager.is_dirty is True

    def test_list_event_types(self):
        """Тест получения списка типов событий"""
        manager = EnvironmentConfigManager()

        event_types = manager.list_event_types()

        assert isinstance(event_types, dict)
        assert len(event_types) > 0
        assert "positive" in event_types
        assert "negative" in event_types
        assert "neutral" in event_types

        # Проверяем структуру
        for event_type, config in event_types.items():
            assert isinstance(config, EventTypeConfig)

    def test_enable_event_type(self):
        """Тест включения типа события"""
        manager = EnvironmentConfigManager()

        # Сначала отключаем
        manager.update_event_type_config("positive", {"enabled": False})
        assert manager.get_event_type_config("positive").enabled is False

        # Включаем
        manager.enable_event_type("positive")
        assert manager.get_event_type_config("positive").enabled is True
        assert manager.is_dirty is True

    def test_disable_event_type(self):
        """Тест отключения типа события"""
        manager = EnvironmentConfigManager()

        # Включаем
        manager.update_event_type_config("positive", {"enabled": True})
        assert manager.get_event_type_config("positive").enabled is True

        # Отключаем
        manager.disable_event_type("positive")
        assert manager.get_event_type_config("positive").enabled is False
        assert manager.is_dirty is True

    def test_set_activity_level(self):
        """Тест установки уровня активности"""
        manager = EnvironmentConfigManager()

        manager.set_activity_level(1.5)
        assert manager.config.activity_level == 1.5
        assert manager.is_dirty is True

    def test_set_activity_level_bounds(self):
        """Тест установки уровня активности с проверкой границ"""
        manager = EnvironmentConfigManager()

        # Тест верхней границы
        manager.set_activity_level(3.0)
        assert manager.config.activity_level == 2.0  # Ограничено

        # Тест нижней границы
        manager.set_activity_level(-1.0)
        assert manager.config.activity_level == 0.0  # Ограничено

    def test_enable_crisis_mode(self):
        """Тест включения режима кризиса"""
        manager = EnvironmentConfigManager()

        manager.enable_crisis_mode()
        assert manager.config.crisis_mode is True
        assert manager.is_dirty is True

    def test_disable_crisis_mode(self):
        """Тест отключения режима кризиса"""
        manager = EnvironmentConfigManager()

        manager.enable_crisis_mode()
        assert manager.config.crisis_mode is True

        manager.disable_crisis_mode()
        assert manager.config.crisis_mode is False
        assert manager.is_dirty is True

    def test_set_crisis_probability(self):
        """Тест установки вероятности кризиса"""
        manager = EnvironmentConfigManager()

        manager.set_crisis_probability(0.2)
        assert manager.config.crisis_probability == 0.2
        assert manager.is_dirty is True

    def test_set_crisis_probability_bounds(self):
        """Тест установки вероятности кризиса с проверкой границ"""
        manager = EnvironmentConfigManager()

        # Тест верхней границы
        manager.set_crisis_probability(1.5)
        assert manager.config.crisis_probability == 1.0

        # Тест нижней границы
        manager.set_crisis_probability(-0.1)
        assert manager.config.crisis_probability == 0.0
