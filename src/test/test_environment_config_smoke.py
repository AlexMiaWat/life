"""
Дымовые тесты для EnvironmentConfigManager - проверка базовой функциональности "из коробки".
"""

import pytest
import json
from unittest.mock import Mock, patch, mock_open

from src.environment.environment_config import (
    EnvironmentConfigManager, EnvironmentConfig, EventTypeConfig
)


class TestEnvironmentConfigManagerSmoke:
    """Дымовые тесты для EnvironmentConfigManager"""

    def test_config_manager_creation(self):
        """Создание менеджера конфигурации"""
        manager = EnvironmentConfigManager()

        assert isinstance(manager.config, EnvironmentConfig)
        assert manager.config.activity_level == 1.0
        assert manager.config.crisis_mode is False
        assert isinstance(manager.config.event_types, dict)
        assert not manager.is_dirty

    def test_basic_config_operations(self):
        """Базовые операции с конфигурацией"""
        manager = EnvironmentConfigManager()

        # Получение конфигурации
        config = manager.get_config()
        assert isinstance(config, EnvironmentConfig)

        # Обновление конфигурации
        updates = {
            "activity_level": 1.5,
            "crisis_mode": True,
            "crisis_probability": 0.2
        }

        manager.update_config(updates)
        assert manager.config.activity_level == 1.5
        assert manager.config.crisis_mode is True
        assert manager.config.crisis_probability == 0.2
        assert manager.is_dirty is True

        # Сброс конфигурации
        manager.reset_config()
        assert manager.config.activity_level == 1.0
        assert manager.config.crisis_mode is False
        assert not manager.is_dirty

    def test_event_type_management(self):
        """Управление типами событий"""
        manager = EnvironmentConfigManager()

        # Получение существующего типа события
        positive_config = manager.get_event_type_config("positive")
        assert isinstance(positive_config, EventTypeConfig)
        assert positive_config.enabled is True

        # Обновление типа события
        updates = {
            "enabled": False,
            "weight": 2.0,
            "intensity_min": 0.3,
            "intensity_max": 0.9,
            "description": "Updated positive events"
        }

        manager.update_event_type_config("positive", updates)
        updated_config = manager.get_event_type_config("positive")
        assert updated_config.enabled is False
        assert updated_config.weight == 2.0
        assert updated_config.intensity_min == 0.3
        assert updated_config.intensity_max == 0.9
        assert updated_config.description == "Updated positive events"
        assert manager.is_dirty is True

        # Включение/отключение типа события
        manager.enable_event_type("positive")
        assert manager.get_event_type_config("positive").enabled is True

        manager.disable_event_type("positive")
        assert manager.get_event_type_config("positive").enabled is False

    def test_activity_level_management(self):
        """Управление уровнем активности"""
        manager = EnvironmentConfigManager()

        # Установка уровня активности
        manager.set_activity_level(1.8)
        assert manager.config.activity_level == 1.8
        assert manager.is_dirty is True

        # Проверка границ
        manager.set_activity_level(3.0)  # Превышает максимум
        assert manager.config.activity_level == 2.0  # Ограничено

        manager.set_activity_level(-1.0)  # Ниже минимума
        assert manager.config.activity_level == 0.0  # Ограничено

    def test_crisis_mode_management(self):
        """Управление режимом кризиса"""
        manager = EnvironmentConfigManager()

        # Включение режима кризиса
        manager.enable_crisis_mode()
        assert manager.config.crisis_mode is True
        assert manager.is_dirty is True

        # Установка вероятности кризиса
        manager.set_crisis_probability(0.15)
        assert manager.config.crisis_probability == 0.15

        # Проверка границ вероятности
        manager.set_crisis_probability(1.5)  # Превышает максимум
        assert manager.config.crisis_probability == 1.0

        manager.set_crisis_probability(-0.1)  # Ниже минимума
        assert manager.config.crisis_probability == 0.0

        # Отключение режима кризиса
        manager.disable_crisis_mode()
        assert manager.config.crisis_mode is False

    @patch('src.environment.environment_config.Path')
    def test_config_persistence(self, mock_path):
        """Тест сохранения и загрузки конфигурации"""
        mock_file = Mock()
        mock_path.return_value = mock_file

        # Тест загрузки
        config_data = {
            "activity_level": 1.3,
            "crisis_mode": True,
            "crisis_probability": 0.1,
            "event_types": {
                "custom_event": {
                    "enabled": True,
                    "weight": 1.5,
                    "intensity_min": 0.0,
                    "intensity_max": 1.0,
                    "description": "Custom event type"
                }
            }
        }

        mock_file.exists.return_value = True
        mock_file.read_text.return_value = json.dumps(config_data)

        manager = EnvironmentConfigManager()
        manager.load_config("test_config.json")

        assert manager.config.activity_level == 1.3
        assert manager.config.crisis_mode is True
        assert manager.config.crisis_probability == 0.1
        assert "custom_event" in manager.config.event_types
        assert not manager.is_dirty

        # Тест сохранения
        with patch('builtins.open', mock_open()) as mock_file_open:
            manager.save_config("test_config.json")
            assert not manager.is_dirty

            # Проверяем, что файл был открыт для записи
            mock_file_open.assert_called()

    @patch('src.environment.environment_config.Path')
    def test_config_file_not_exists(self, mock_path):
        """Тест загрузки при отсутствии файла конфигурации"""
        mock_file = Mock()
        mock_file.exists.return_value = False
        mock_path.return_value = mock_file

        manager = EnvironmentConfigManager()
        manager.load_config("nonexistent.json")

        # Должна остаться конфигурация по умолчанию
        assert manager.config.activity_level == 1.0
        assert not manager.config.crisis_mode

    def test_list_event_types(self):
        """Тест получения списка типов событий"""
        manager = EnvironmentConfigManager()

        event_types = manager.list_event_types()

        assert isinstance(event_types, dict)
        assert len(event_types) > 0

        # Проверяем наличие основных типов
        assert "positive" in event_types
        assert "negative" in event_types
        assert "neutral" in event_types

        # Проверяем структуру каждого типа
        for event_type, config in event_types.items():
            assert isinstance(config, EventTypeConfig)
            assert hasattr(config, 'enabled')
            assert hasattr(config, 'weight')
            assert hasattr(config, 'intensity_min')
            assert hasattr(config, 'intensity_max')
            assert hasattr(config, 'description')

    def test_custom_event_type_creation(self):
        """Тест создания пользовательского типа события"""
        manager = EnvironmentConfigManager()

        # Создаем новый тип события
        custom_updates = {
            "enabled": True,
            "weight": 3.0,
            "intensity_min": 0.2,
            "intensity_max": 0.8,
            "description": "Custom high-priority event"
        }

        manager.update_event_type_config("high_priority", custom_updates)

        config = manager.get_event_type_config("high_priority")
        assert config is not None
        assert config.enabled is True
        assert config.weight == 3.0
        assert config.intensity_min == 0.2
        assert config.intensity_max == 0.8
        assert config.description == "Custom high-priority event"
        assert manager.is_dirty is True

    def test_config_to_dict_conversion(self):
        """Тест преобразования конфигурации в словарь"""
        manager = EnvironmentConfigManager()

        # Изменяем конфигурацию
        manager.config.activity_level = 1.7
        manager.config.crisis_mode = True
        manager.update_event_type_config("positive", {"weight": 2.5})

        config_dict = manager.config.to_dict()

        assert config_dict["activity_level"] == 1.7
        assert config_dict["crisis_mode"] is True
        assert config_dict["event_types"]["positive"]["weight"] == 2.5

    def test_config_from_dict_conversion(self):
        """Тест создания конфигурации из словаря"""
        config_dict = {
            "activity_level": 1.9,
            "crisis_mode": False,
            "crisis_probability": 0.05,
            "event_types": {
                "test_event": {
                    "enabled": True,
                    "weight": 1.2,
                    "intensity_min": 0.1,
                    "intensity_max": 0.9,
                    "description": "Test event"
                }
            },
            "custom_weights": {"special": 2.0}
        }

        config = EnvironmentConfig.from_dict(config_dict)

        assert config.activity_level == 1.9
        assert config.crisis_mode is False
        assert config.crisis_probability == 0.05
        assert config.event_types["test_event"].weight == 1.2
        assert config.event_types["test_event"].enabled is True
        assert config.custom_weights == {"special": 2.0}

    def test_error_handling(self):
        """Тест обработки ошибок"""
        manager = EnvironmentConfigManager()

        # Попытка получить несуществующий тип события
        config = manager.get_event_type_config("nonexistent")
        assert config is None

        # Попытка обновить несуществующий тип события (создаст новый)
        manager.update_event_type_config("new_type", {"enabled": True})
        config = manager.get_event_type_config("new_type")
        assert config is not None
        assert config.enabled is True

    def test_config_state_tracking(self):
        """Тест отслеживания состояния конфигурации"""
        manager = EnvironmentConfigManager()

        # Изначально не грязная
        assert not manager.is_dirty

        # После изменения становится грязной
        manager.set_activity_level(1.2)
        assert manager.is_dirty

        # После сброса снова чистая
        manager.reset_config()
        assert not manager.is_dirty

        # После загрузки чистая
        with patch('src.environment.environment_config.Path') as mock_path:
            mock_file = Mock()
            mock_file.exists.return_value = True
            mock_file.read_text.return_value = '{"activity_level": 1.0}'
            mock_path.return_value = mock_file

            manager.load_config("test.json")
            assert not manager.is_dirty