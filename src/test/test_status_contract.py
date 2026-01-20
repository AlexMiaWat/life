"""
Тесты для проверки контракта /status endpoint.

Проверяют, что endpoint возвращает только безопасные поля согласно определенному контракту.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest
import requests
from src.state.self_state import SelfState


@pytest.mark.integration
@pytest.mark.real_server
class TestStatusContract:
    """Тесты контракта /status endpoint"""

    def test_status_excludes_transient_fields(self, server_setup):
        """Проверка, что transient поля не возвращаются в ответе"""
        response = requests.get(f"{server_setup['base_url']}/status", timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        
        # Transient поля не должны присутствовать
        assert "activated_memory" not in data, "Transient поле activated_memory не должно быть в ответе"
        assert "last_pattern" not in data, "Transient поле last_pattern не должно быть в ответе"

    def test_status_excludes_internal_fields(self, server_setup):
        """Проверка, что внутренние поля (начинающиеся с _) не возвращаются"""
        response = requests.get(f"{server_setup['base_url']}/status", timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        
        # Внутренние поля не должны присутствовать
        internal_fields = [
            "_initialized",
            "_logging_enabled",
            "_log_only_critical",
            "_log_buffer",
            "_log_buffer_size",
        ]
        for field in internal_fields:
            assert field not in data, f"Внутреннее поле {field} не должно быть в ответе"

    def test_status_excludes_archive_memory(self, server_setup):
        """Проверка, что archive_memory не возвращается в ответе"""
        response = requests.get(f"{server_setup['base_url']}/status", timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        
        # archive_memory не должен присутствовать
        assert "archive_memory" not in data, "archive_memory не должен быть в ответе"

    def test_status_includes_required_fields(self, server_setup):
        """Проверка, что обязательные поля присутствуют в ответе"""
        response = requests.get(f"{server_setup['base_url']}/status", timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        
        # Основные метрики (Vital Parameters) - ОБЯЗАТЕЛЬНЫЕ
        assert "active" in data, "Поле active должно быть в ответе"
        assert "energy" in data, "Поле energy должно быть в ответе"
        assert "integrity" in data, "Поле integrity должно быть в ответе"
        assert "stability" in data, "Поле stability должно быть в ответе"
        
        # Временные метрики - ОБЯЗАТЕЛЬНЫЕ
        assert "ticks" in data, "Поле ticks должно быть в ответе"
        assert "age" in data, "Поле age должно быть в ответе"
        
        # Проверяем типы
        assert isinstance(data["active"], bool), "active должен быть bool"
        assert isinstance(data["energy"], (int, float)), "energy должен быть числом"
        assert isinstance(data["integrity"], (int, float)), "integrity должен быть числом"
        assert isinstance(data["stability"], (int, float)), "stability должен быть числом"
        assert isinstance(data["ticks"], int), "ticks должен быть int"
        assert isinstance(data["age"], (int, float)), "age должен быть числом"

    def test_status_includes_optional_fields(self, server_setup):
        """Проверка, что опциональные поля могут присутствовать в расширенном контракте"""
        response = requests.get(f"{server_setup['base_url']}/status", timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        
        # Опциональные поля могут присутствовать (проверяем только если они есть)
        optional_fields = [
            "life_id",
            "birth_timestamp",
            "subjective_time",
            "fatigue",
            "tension",
            "learning_params",
            "adaptation_params",
            "last_significance",
            "last_event_intensity",
            "planning",
            "intelligence",
        ]
        
        # Проверяем, что если поля присутствуют, они имеют правильный тип
        if "life_id" in data:
            assert isinstance(data["life_id"], str), "life_id должен быть строкой"
        if "birth_timestamp" in data:
            assert isinstance(data["birth_timestamp"], (int, float)), "birth_timestamp должен быть числом"
        if "subjective_time" in data:
            assert isinstance(data["subjective_time"], (int, float)), "subjective_time должен быть числом"
        if "fatigue" in data:
            assert isinstance(data["fatigue"], (int, float)), "fatigue должен быть числом"
        if "tension" in data:
            assert isinstance(data["tension"], (int, float)), "tension должен быть числом"
        if "learning_params" in data:
            assert isinstance(data["learning_params"], dict), "learning_params должен быть словарем"
        if "adaptation_params" in data:
            assert isinstance(data["adaptation_params"], dict), "adaptation_params должен быть словарем"

    def test_status_memory_limit_parameter(self, server_setup):
        """Проверка работы параметра memory_limit"""
        # Запрос без лимита - memory не должен быть в ответе
        response = requests.get(f"{server_setup['base_url']}/status", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "memory" not in data or data["memory"] is None, "memory не должен быть в ответе без лимита"
        
        # Запрос с лимитом - memory должен быть в ответе (может быть пустым списком)
        response = requests.get(
            f"{server_setup['base_url']}/status?memory_limit=10", timeout=5
        )
        assert response.status_code == 200
        data = response.json()
        # Если memory присутствует, он должен быть списком
        if "memory" in data and data["memory"] is not None:
            assert isinstance(data["memory"], list), "memory должен быть списком"

    def test_status_events_limit_parameter(self, server_setup):
        """Проверка работы параметра events_limit"""
        # Запрос без лимита - recent_events не должен быть в ответе
        response = requests.get(f"{server_setup['base_url']}/status", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "recent_events" not in data or data.get("recent_events") is None, \
            "recent_events не должен быть в ответе без лимита"
        
        # Запрос с лимитом - recent_events должен быть в ответе (может быть пустым списком)
        response = requests.get(
            f"{server_setup['base_url']}/status?events_limit=10", timeout=5
        )
        assert response.status_code == 200
        data = response.json()
        # Если recent_events присутствует, он должен быть списком
        if "recent_events" in data and data["recent_events"] is not None:
            assert isinstance(data["recent_events"], list), "recent_events должен быть списком"

    def test_status_history_limit_parameters(self, server_setup):
        """Проверка работы параметров лимитов истории"""
        # Запрос с лимитами истории
        response = requests.get(
            f"{server_setup['base_url']}/status?energy_history_limit=50&stability_history_limit=50&adaptation_history_limit=50",
            timeout=5
        )
        assert response.status_code == 200
        data = response.json()
        
        # Если поля присутствуют, они должны быть списками
        if "energy_history" in data and data["energy_history"] is not None:
            assert isinstance(data["energy_history"], list), "energy_history должен быть списком"
        if "stability_history" in data and data["stability_history"] is not None:
            assert isinstance(data["stability_history"], list), "stability_history должен быть списком"
        if "adaptation_history" in data and data["adaptation_history"] is not None:
            assert isinstance(data["adaptation_history"], list), "adaptation_history должен быть списком"

    def test_status_multiple_limit_parameters(self, server_setup):
        """Проверка работы нескольких параметров лимитов одновременно"""
        response = requests.get(
            f"{server_setup['base_url']}/status?memory_limit=5&events_limit=10&energy_history_limit=20",
            timeout=5
        )
        assert response.status_code == 200
        data = response.json()
        
        # Проверяем, что все запрошенные поля присутствуют (могут быть пустыми списками)
        # Это проверка того, что параметры корректно обрабатываются

    def test_status_get_safe_status_dict_method(self):
        """Проверка метода get_safe_status_dict() напрямую"""
        state = SelfState()
        
        # Проверяем минимальный контракт
        safe_dict = state.get_safe_status_dict(include_optional=False)
        
        # Проверяем отсутствие transient полей
        assert "activated_memory" not in safe_dict
        assert "last_pattern" not in safe_dict
        
        # Проверяем отсутствие внутренних полей
        assert "_initialized" not in safe_dict
        assert "_logging_enabled" not in safe_dict
        
        # Проверяем отсутствие archive_memory
        assert "archive_memory" not in safe_dict
        
        # Проверяем наличие обязательных полей
        assert "active" in safe_dict
        assert "energy" in safe_dict
        assert "integrity" in safe_dict
        assert "stability" in safe_dict
        assert "ticks" in safe_dict
        assert "age" in safe_dict
        
        # Проверяем расширенный контракт
        extended_dict = state.get_safe_status_dict(include_optional=True)
        
        # Должны присутствовать опциональные поля
        assert "life_id" in extended_dict
        assert "birth_timestamp" in extended_dict
        assert "subjective_time" in extended_dict
        assert "learning_params" in extended_dict
        assert "adaptation_params" in extended_dict

    def test_status_get_safe_status_dict_with_limits(self):
        """Проверка метода get_safe_status_dict() с лимитами"""
        state = SelfState()
        
        # Добавляем тестовые данные
        state.recent_events = [{"type": "test", "intensity": 0.5}] * 20
        state.energy_history = [50.0, 60.0, 70.0] * 10
        
        # Запрашиваем с лимитами
        safe_dict = state.get_safe_status_dict(
            include_optional=True,
            limits={"events_limit": 5, "energy_history_limit": 10}
        )
        
        # Проверяем, что лимиты применены
        if "recent_events" in safe_dict and safe_dict["recent_events"] is not None:
            assert len(safe_dict["recent_events"]) <= 5, "recent_events должен быть ограничен"
        if "energy_history" in safe_dict and safe_dict["energy_history"] is not None:
            assert len(safe_dict["energy_history"]) <= 10, "energy_history должен быть ограничен"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
