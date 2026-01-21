"""
Дымовые тесты для DataCollector

Проверяем:
- Создание экземпляров классов
- Базовую функциональность методов
- Отсутствие исключений при нормальной работе
- Корректность основных операций
"""

import json
import tempfile
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.observability.data_collector import (
    DataCollector,
    ObservationData,
)


@pytest.mark.smoke
class TestDataCollectorSmoke:
    """Дымовые тесты для DataCollector"""

    def test_data_collector_creation(self):
        """Проверка создания DataCollector"""
        collector = DataCollector()
        assert collector is not None
        assert isinstance(collector, DataCollector)

    def test_data_collector_custom_path(self):
        """Проверка создания DataCollector с кастомным путем"""
        with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
            custom_path = f.name

        try:
            collector = DataCollector(storage_path=custom_path)
            assert str(collector.storage_path) == custom_path
        finally:
            Path(custom_path).unlink(missing_ok=True)

    def test_observation_data_creation(self):
        """Проверка создания ObservationData"""
        data = ObservationData()
        assert data is not None
        assert isinstance(data, ObservationData)

    def test_observation_data_custom_creation(self):
        """Проверка создания ObservationData с кастомными значениями"""
        data = ObservationData(
            data_type="state",
            data={"energy": 0.8, "stability": 0.9}
        )

        assert data.data_type == "state"
        assert data.data["energy"] == 0.8
        assert data.data["stability"] == 0.9

    def test_collect_state_data_basic(self):
        """Проверка базового сбора данных состояния"""
        with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
            temp_path = f.name

        try:
            collector = DataCollector(storage_path=temp_path)
            mock_snapshot = Mock()
            mock_snapshot.to_dict = Mock(return_value={
                "timestamp": 1234567890.0,
                "energy": 0.7,
                "stability": 0.8
            })

            # Сбор данных
            collector.collect_state_data(mock_snapshot)

            # Проверяем что данные попали в буфер
            assert len(collector._buffer) == 1
            assert collector._buffer[0].data_type == "state"

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_collect_component_data_basic(self):
        """Проверка базового сбора данных компонентов"""
        with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
            temp_path = f.name

        try:
            collector = DataCollector(storage_path=temp_path)
            mock_stats = Mock()
            mock_stats.to_dict = Mock(return_value={
                "timestamp": 1234567890.0,
                "memory_size": 100,
                "cpu_usage": 0.5
            })

            # Сбор данных
            collector.collect_component_data(mock_stats)

            # Проверяем что данные попали в буфер
            assert len(collector._buffer) == 1
            assert collector._buffer[0].data_type == "component"

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_buffer_flushing(self):
        """Проверка сброса буфера"""
        with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
            temp_path = f.name

        try:
            collector = DataCollector(storage_path=temp_path)

            # Добавляем данные в буфер
            for i in range(5):
                data = ObservationData(data_type="test", data={"value": i})
                collector._add_to_buffer(data)

            # Буфер должен содержать 5 элементов
            assert len(collector._buffer) == 5

            # Принудительный сброс
            collector.flush()

            # Буфер должен быть пустым
            assert len(collector._buffer) == 0

            # Файл должен содержать данные
            assert Path(temp_path).exists()
            with open(temp_path, 'r') as file:
                lines = file.readlines()
                assert len(lines) == 5

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_auto_buffer_flush(self):
        """Проверка автоматического сброса буфера при переполнении"""
        with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
            temp_path = f.name

        try:
            collector = DataCollector(storage_path=temp_path, )
            collector._buffer_size = 3  # Маленький размер буфера для теста

            # Добавляем данные до переполнения
            for i in range(4):
                data = ObservationData(data_type="test", data={"value": i})
                collector._add_to_buffer(data)

            # Буфер должен быть сброшен автоматически при добавлении 4-го элемента
            assert len(collector._buffer) <= collector._buffer_size

            # Файл должен содержать данные
            assert Path(temp_path).exists()

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_get_recent_data_empty(self):
        """Проверка получения данных из пустого хранилища"""
        with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
            temp_path = f.name

        try:
            collector = DataCollector(storage_path=temp_path)

            # Получение данных из пустого хранилища
            data = collector.get_recent_data()
            assert isinstance(data, list)
            assert len(data) == 0

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_get_recent_data_from_file(self):
        """Проверка получения данных из файла"""
        with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
            temp_path = f.name

        try:
            # Создаем файл с тестовыми данными
            test_data = [
                {"timestamp": 1000.0, "data_type": "state", "data": {"energy": 0.5}},
                {"timestamp": 2000.0, "data_type": "component", "data": {"memory": 100}},
                {"timestamp": 3000.0, "data_type": "state", "data": {"energy": 0.8}},
            ]

            with open(temp_path, 'w') as file:
                for item in test_data:
                    json.dump(item, file)
                    file.write('\n')

            collector = DataCollector(storage_path=temp_path)

            # Получение всех данных
            data = collector.get_recent_data()
            assert len(data) == 3

            # Получение только state данных
            state_data = collector.get_recent_data(data_type="state")
            assert len(state_data) == 2
            assert all(d.data_type == "state" for d in state_data)

            # Получение с ограничением
            limited_data = collector.get_recent_data(limit=1)
            assert len(limited_data) == 1

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_get_data_count(self):
        """Проверка подсчета данных"""
        with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
            temp_path = f.name

        try:
            # Создаем файл с тестовыми данными
            test_data = [
                {"timestamp": 1000.0, "data_type": "state", "data": {"energy": 0.5}},
                {"timestamp": 2000.0, "data_type": "component", "data": {"memory": 100}},
                {"timestamp": 3000.0, "data_type": "state", "data": {"energy": 0.8}},
            ]

            with open(temp_path, 'w') as file:
                for item in test_data:
                    json.dump(item, file)
                    file.write('\n')

            collector = DataCollector(storage_path=temp_path)

            # Подсчет всех данных
            total_count = collector.get_data_count()
            assert total_count == 3

            # Подсчет по типам
            state_count = collector.get_data_count(data_type="state")
            assert state_count == 2

            component_count = collector.get_data_count(data_type="component")
            assert component_count == 1

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_collection_enable_disable(self):
        """Проверка включения/выключения сбора данных"""
        collector = DataCollector()

        # По умолчанию включено
        assert collector.collection_enabled is True

        # Выключаем
        collector.disable_collection()
        assert collector.collection_enabled is False

        # При выключенном сборе методы не должны добавлять данные
        mock_snapshot = Mock()
        mock_snapshot.to_dict = Mock(return_value={"test": "data"})

        collector.collect_state_data(mock_snapshot)
        assert len(collector._buffer) == 0

        # Включаем обратно
        collector.enable_collection()
        assert collector.collection_enabled is True

    def test_clear_data(self):
        """Проверка очистки данных"""
        with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
            temp_path = f.name

        try:
            collector = DataCollector(storage_path=temp_path)

            # Добавляем данные
            data = ObservationData(data_type="test", data={"value": 1})
            collector._add_to_buffer(data)
            collector.flush()

            # Проверяем что файл существует и содержит данные
            assert Path(temp_path).exists()
            with open(temp_path, 'r') as file:
                assert len(file.readlines()) > 0

            # Очищаем данные
            collector.clear_data()

            # Файл должен быть удален
            assert not Path(temp_path).exists()
            # Буфер должен быть пустым
            assert len(collector._buffer) == 0

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_to_dict_functionality(self):
        """Проверка метода to_dict"""
        data = ObservationData(
            data_type="test",
            data={"key": "value", "number": 42}
        )

        result = data.to_dict()

        assert isinstance(result, dict)
        assert result['data_type'] == "test"
        assert result['data']['key'] == "value"
        assert result['data']['number'] == 42
        assert 'timestamp' in result

    def test_error_handling(self):
        """Проверка обработки ошибок"""
        collector = DataCollector()

        # Методы должны обрабатывать исключения gracefully
        mock_snapshot = Mock()
        mock_snapshot.to_dict = Mock(side_effect=Exception("Test error"))

        # Не должно выбрасывать исключения
        collector.collect_state_data(mock_snapshot)
        collector.collect_component_data(mock_snapshot)

        # Методы чтения тоже должны работать
        data = collector.get_recent_data()
        assert isinstance(data, list)

        count = collector.get_data_count()
        assert isinstance(count, int)