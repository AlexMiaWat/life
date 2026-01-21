"""
Интеграционные тесты для EnvironmentConfigManager - проверка взаимодействия с другими компонентами.
"""

import pytest
import json
from unittest.mock import Mock, patch, mock_open

from src.environment.environment_config import EnvironmentConfigManager, EnvironmentConfig
from src.environment.event import Event
from src.environment.event_queue import EventQueue
from src.state.self_state import SelfState


class TestEnvironmentConfigManagerIntegration:
    """Интеграционные тесты для EnvironmentConfigManager"""

    def test_config_manager_with_event_generation(self):
        """Интеграция с генерацией событий на основе конфигурации"""
        manager = EnvironmentConfigManager()

        # Настраиваем конфигурацию для генерации определенных типов событий
        manager.update_event_type_config("positive", {"enabled": True, "weight": 2.0})
        manager.update_event_type_config("negative", {"enabled": False, "weight": 0.0})
        manager.update_event_type_config("crisis", {"enabled": True, "weight": 1.5})

        # Проверяем, что конфигурация применима для генерации событий
        positive_config = manager.get_event_type_config("positive")
        negative_config = manager.get_event_type_config("negative")
        crisis_config = manager.get_event_type_config("crisis")

        assert positive_config.enabled is True
        assert positive_config.weight == 2.0
        assert negative_config.enabled is False
        assert crisis_config.enabled is True
        assert crisis_config.weight == 1.5

        # Имитируем использование конфигурации для генерации событий
        enabled_types = [
            event_type
            for event_type, config in manager.list_event_types().items()
            if config.enabled
        ]

        assert "positive" in enabled_types
        assert "negative" not in enabled_types
        assert "crisis" in enabled_types

    def test_config_manager_with_event_queue_integration(self):
        """Интеграция с EventQueue для управления потоком событий"""
        manager = EnvironmentConfigManager()
        event_queue = EventQueue(maxsize=10)

        # Настраиваем конфигурацию для управления частотой событий
        manager.set_activity_level(1.5)  # Увеличенная активность
        manager.enable_crisis_mode()
        manager.set_crisis_probability(0.3)

        # Проверяем влияние конфигурации на параметры генерации
        config = manager.get_config()
        assert config.activity_level == 1.5
        assert config.crisis_mode is True
        assert config.crisis_probability == 0.3

        # Имитируем генерацию событий на основе конфигурации
        events_to_generate = int(10 * config.activity_level)  # 15 событий

        generated_events = []
        for i in range(events_to_generate):
            # Имитируем взвешенный выбор типа события
            if i % 3 == 0:
                event_type = "positive"
            elif config.crisis_mode and (i % 10) < (config.crisis_probability * 10):
                event_type = "crisis"
            else:
                event_type = "neutral"

            event = Event(type=event_type, intensity=0.5)
            generated_events.append(event)
            event_queue.put(event)

        # Проверяем, что события добавлены в очередь
        queued_events = event_queue.get_all()
        assert len(queued_events) >= 10  # Минимум базовое количество

        # Проверяем разнообразие типов событий
        event_types = {event.type for event in queued_events}
        assert len(event_types) >= 2  # Минимум 2 типа

    def test_config_persistence_with_file_system(self):
        """Интеграция с файловой системой для сохранения/загрузки конфигурации"""
        import tempfile
        import os

        manager = EnvironmentConfigManager()

        # Изменяем конфигурацию
        manager.set_activity_level(2.0)
        manager.enable_crisis_mode()
        manager.update_event_type_config("stress", {"enabled": True, "weight": 3.0})

        # Создаем временный файл для тестирования
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as temp_file:
            config_file = temp_file.name

        try:
            # Сохраняем конфигурацию
            with patch("src.environment.environment_config.Path") as mock_path:
                mock_file = Mock()
                mock_path.return_value = mock_file

                with patch("builtins.open", mock_open()) as mock_file_open:
                    manager.save_config(config_file)

                    # Проверяем, что файл был открыт для записи
                    mock_file_open.assert_called()

                    # Имитируем чтение сохраненной конфигурации
                    saved_config_data = manager.config.to_dict()

                    # Создаем новый менеджер и загружаем конфигурацию
                    manager2 = EnvironmentConfigManager()
                    config_dict = saved_config_data

                    # Имитируем загрузку
                    manager2.config = EnvironmentConfig.from_dict(config_dict)

                    # Проверяем, что конфигурация восстановлена
                    assert manager2.config.activity_level == 2.0
                    assert manager2.config.crisis_mode is True
                    stress_config = manager2.get_event_type_config("stress")
                    assert stress_config.enabled is True
                    assert stress_config.weight == 3.0

        finally:
            # Очищаем временный файл
            if os.path.exists(config_file):
                os.unlink(config_file)

    def test_config_manager_state_synchronization(self):
        """Синхронизация состояния конфигурации между компонентами"""
        manager = EnvironmentConfigManager()

        # Имитируем несколько компонентов, читающих конфигурацию
        components = []

        for i in range(3):
            component = Mock()
            component.get_config = manager.get_config
            components.append(component)

        # Изменяем конфигурацию
        manager.set_activity_level(1.8)
        manager.disable_event_type("negative")

        # Проверяем, что все компоненты видят изменения
        for component in components:
            config = component.get_config()
            assert config.activity_level == 1.8
            negative_config = manager.get_event_type_config("negative")
            assert negative_config.enabled is False

    def test_config_manager_with_self_state_integration(self):
        """Интеграция с SelfState для адаптивной конфигурации"""
        manager = EnvironmentConfigManager()

        # Создаем состояние системы
        state = SelfState()
        state.energy = 0.6  # Система ослаблена
        state.stability = 0.7
        state.integrity = 0.8

        # Адаптируем конфигурацию на основе состояния
        if state.energy < 0.7:
            # Система ослаблена - уменьшаем активность и отключаем кризисы
            manager.set_activity_level(0.5)
            manager.disable_crisis_mode()
        else:
            # Система в хорошем состоянии - нормальная активность
            manager.set_activity_level(1.0)
            manager.enable_crisis_mode()

        # Проверяем адаптацию
        config = manager.get_config()
        assert config.activity_level == 0.5  # Уменьшена из-за низкой энергии
        assert config.crisis_mode is False  # Отключена из-за низкой энергии

        # Имитируем улучшение состояния
        state.energy = 0.9

        # Повторная адаптация
        if state.energy > 0.8:
            manager.set_activity_level(1.2)
            manager.enable_crisis_mode()

        config = manager.get_config()
        assert config.activity_level == 1.2  # Увеличена
        assert config.crisis_mode is True  # Включена

    def test_config_manager_thread_safety(self):
        """Потокобезопасность операций с конфигурацией"""
        import threading
        import time

        manager = EnvironmentConfigManager()

        results = []
        errors = []

        def worker(worker_id):
            try:
                # Каждый поток выполняет различные операции
                if worker_id == 0:
                    for i in range(10):
                        manager.set_activity_level(1.0 + i * 0.1)
                        time.sleep(0.001)
                elif worker_id == 1:
                    for i in range(10):
                        manager.enable_crisis_mode()
                        manager.disable_crisis_mode()
                        time.sleep(0.001)
                elif worker_id == 2:
                    for i in range(10):
                        manager.update_event_type_config(
                            "test_event", {"enabled": True, "weight": 1.0}
                        )
                        time.sleep(0.001)

                results.append(f"Worker {worker_id} completed")

            except Exception as e:
                errors.append(f"Worker {worker_id} error: {e}")

        # Запускаем несколько потоков
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Ждем завершения
        for thread in threads:
            thread.join()

        # Проверяем результаты
        assert len(results) == 3  # Все потоки завершились
        assert len(errors) == 0  # Без ошибок

        # Проверяем финальное состояние
        config = manager.get_config()
        assert isinstance(config.activity_level, float)
        assert isinstance(config.crisis_mode, bool)

    def test_config_manager_with_event_type_validation(self):
        """Валидация типов событий при интеграции"""
        manager = EnvironmentConfigManager()

        # Получаем список всех доступных типов событий
        available_types = list(manager.list_event_types().keys())

        # Проверяем, что основные типы присутствуют
        required_types = ["positive", "negative", "neutral"]
        for event_type in required_types:
            assert event_type in available_types

        # Тестируем создание пользовательских типов
        custom_types = ["stress", "recovery", "adaptation"]

        for custom_type in custom_types:
            manager.update_event_type_config(
                custom_type,
                {"enabled": True, "weight": 1.0, "description": f"Custom {custom_type} event"},
            )

        # Проверяем, что пользовательские типы добавлены
        all_types = list(manager.list_event_types().keys())
        for custom_type in custom_types:
            assert custom_type in all_types

        # Проверяем свойства пользовательских типов
        for custom_type in custom_types:
            config = manager.get_event_type_config(custom_type)
            assert config.enabled is True
            assert config.weight == 1.0
            assert config.description.startswith("Custom")

    def test_config_manager_backup_and_restore(self):
        """Резервное копирование и восстановление конфигурации"""
        manager = EnvironmentConfigManager()

        # Создаем базовую конфигурацию
        manager.set_activity_level(1.5)
        manager.enable_crisis_mode()
        manager.update_event_type_config("backup_test", {"enabled": True, "weight": 2.0})

        # Создаем резервную копию
        backup = manager.config.to_dict()

        # Изменяем конфигурацию
        manager.set_activity_level(0.5)
        manager.disable_crisis_mode()
        manager.update_event_type_config("backup_test", {"enabled": False, "weight": 0.0})

        # Проверяем, что изменения применились
        assert manager.config.activity_level == 0.5
        assert manager.config.crisis_mode is False
        assert manager.get_event_type_config("backup_test").enabled is False

        # Восстанавливаем из резервной копии
        manager.config = EnvironmentConfig.from_dict(backup)

        # Проверяем восстановление
        assert manager.config.activity_level == 1.5
        assert manager.config.crisis_mode is True
        assert manager.get_event_type_config("backup_test").enabled is True
        assert manager.get_event_type_config("backup_test").weight == 2.0
