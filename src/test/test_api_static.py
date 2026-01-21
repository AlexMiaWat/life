"""
Статические тесты для упрощенного API без аутентификации (api.py)

Проверяем:
- Структуру модуля
- Сигнатуры функций и методов
- Типы возвращаемых значений
- Валидацию моделей данных
"""

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from api import (
    EventCreate,
    EventResponse,
    ExtendedStatusResponse,
    StatusResponse,
    app,
    verify_api_key,
)


@pytest.mark.static
class TestAPISimplifiedStatic:
    """Статические тесты для упрощенного API без аутентификации"""

    # ============================================================================
    # API Configuration
    # ============================================================================

    def test_app_configuration(self):
        """Проверка конфигурации FastAPI приложения"""
        assert app is not None
        assert app.title == "Life Experiment API"
        assert app.version == "1.0.0"

    # ============================================================================
    # Pydantic Models
    # ============================================================================

    def test_event_create_model(self):
        """Проверка модели EventCreate"""
        # Допустимые значения
        event = EventCreate(type="shock", intensity=0.8)
        assert event.type == "shock"
        assert event.intensity == 0.8
        assert event.metadata == {}

        # Значения по умолчанию
        event_default = EventCreate(type="noise")
        assert event_default.intensity == 0.0
        assert event_default.timestamp is None

    def test_event_response_model(self):
        """Проверка модели EventResponse"""
        response = EventResponse(
            type="shock",
            intensity=0.8,
            timestamp=1234567890.0,
            metadata={"test": "data"},
            message="Event processed successfully",
        )
        assert response.type == "shock"
        assert response.intensity == 0.8
        assert response.timestamp == 1234567890.0
        assert response.metadata == {"test": "data"}
        assert response.message == "Event processed successfully"

    def test_status_response_model(self):
        """Проверка модели StatusResponse"""
        status = StatusResponse(
            active=True,
            ticks=1000,
            age=123.45,
            energy=85.5,
            stability=0.92,
            integrity=0.95,
            subjective_time=120.0,
            fatigue=15.0,
            tension=25.0,
        )
        assert status.active is True
        assert status.ticks == 1000
        assert status.age == 123.45
        assert status.energy == 85.5
        assert status.stability == 0.92
        assert status.integrity == 0.95
        assert status.subjective_time == 120.0
        assert status.fatigue == 15.0
        assert status.tension == 25.0

    def test_extended_status_response_model(self):
        """Проверка модели ExtendedStatusResponse"""
        extended = ExtendedStatusResponse(
            active=True,
            energy=85.5,
            integrity=0.95,
            stability=0.92,
            ticks=1000,
            age=123.45,
            subjective_time=120.0,
            fatigue=15.0,
            tension=25.0,
            life_id="test-life-123",
            birth_timestamp=1234567800.0,
            recent_events=["event1", "event2"],
            last_significance=0.8,
        )
        assert extended.active is True
        assert extended.life_id == "test-life-123"
        assert extended.ticks == 1000
        assert extended.energy == 85.5
        assert extended.integrity == 0.95
        assert extended.stability == 0.92
        assert extended.age == 123.45
        assert extended.subjective_time == 120.0
        assert extended.fatigue == 15.0
        assert extended.tension == 25.0
        assert extended.birth_timestamp == 1234567800.0
        assert extended.recent_events == ["event1", "event2"]
        assert extended.last_significance == 0.8

    # ============================================================================
    # Validation Tests
    # ============================================================================

    def test_event_create_validation(self):
        """Проверка создания EventCreate с различными значениями"""
        # Допустимые значения
        event1 = EventCreate(type="shock", intensity=1.0)
        assert event1.type == "shock"
        assert event1.intensity == 1.0

        event2 = EventCreate(type="noise", intensity=0.0)
        assert event2.type == "noise"
        assert event2.intensity == 0.0

        # Пустой тип (Pydantic позволяет пустые строки для str поля)
        event3 = EventCreate(type="", intensity=0.5)
        assert event3.type == ""

        # Отрицательная интенсивность (не валидируется на уровне модели)
        event4 = EventCreate(type="shock", intensity=-0.1)
        assert event4.intensity == -0.1

        # Интенсивность > 1.0 (не валидируется на уровне модели)
        event5 = EventCreate(type="shock", intensity=1.1)
        assert event5.intensity == 1.1

    def test_verify_api_key_function(self):
        """Проверка функции verify_api_key"""
        # Без API ключа - должен работать (опциональная защита)
        assert verify_api_key(None) is True

        # С API ключом - должна работать проверка
        # (поскольку API_KEY не установлен, функция всегда возвращает True)
        assert verify_api_key("any_key") is True

    # ============================================================================
    # Model Structure Tests
    # ============================================================================

    def test_event_response_structure(self):
        """Проверка структуры EventResponse"""
        # EventResponse должен содержать все поля EventCreate плюс message
        create_fields = set(EventCreate.model_fields.keys())
        response_fields = set(EventResponse.model_fields.keys())

        # response должен содержать все поля create плюс message
        assert create_fields.issubset(response_fields)
        assert "message" in response_fields
        assert EventResponse.model_fields["message"].annotation == str
