"""
Статические тесты для API с аутентификацией (api.py)

Проверяем:
- Структуру модуля и константы
- Сигнатуры функций и методов
- Типы возвращаемых значений
- Валидацию моделей данных
- Архитектурные ограничения аутентификации
"""

import inspect
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from api import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    SECRET_KEY,
    ExtendedStatusResponse,
    EventCreate,
    EventResponse,
    StatusResponse,
    Token,
    TokenData,
    User,
    UserCreate,
    UserInDB,
    app,
    authenticate_user,
    create_access_token,
    fake_users_db,
    get_current_active_user,
    get_current_user,
    get_password_hash,
    get_user,
    pwd_context,
    verify_password,
)


@pytest.mark.static
class TestAPIAuthStatic:
    """Статические тесты для API с аутентификацией"""

    # ============================================================================
    # Constants and Configuration
    # ============================================================================

    def test_constants_defined(self):
        """Проверка что все константы определены"""
        assert SECRET_KEY is not None
        assert ALGORITHM == "HS256"
        assert ACCESS_TOKEN_EXPIRE_MINUTES == 30

    def test_constants_types(self):
        """Проверка типов констант"""
        assert isinstance(SECRET_KEY, str)
        assert isinstance(ALGORITHM, str)
        assert isinstance(ACCESS_TOKEN_EXPIRE_MINUTES, int)

    def test_pwd_context_configuration(self):
        """Проверка конфигурации контекста хеширования паролей"""
        assert pwd_context is not None
        assert hasattr(pwd_context, "schemes")
        assert "bcrypt" in pwd_context.schemes

    # ============================================================================
    # Pydantic Models
    # ============================================================================

    def test_user_model_structure(self):
        """Проверка структуры модели User"""
        assert hasattr(User, "model_fields")
        fields = User.model_fields

        # Обязательные поля
        assert "username" in fields
        assert "email" in fields
        assert "disabled" in fields

        # Опциональные поля
        assert "full_name" in fields

        # Проверяем типы полей
        assert fields["username"].annotation == str
        from pydantic import EmailStr
        assert fields["email"].annotation == EmailStr
        assert fields["disabled"].annotation == bool
        from typing import Union
        assert fields["full_name"].annotation == Union[str, type(None)]

    def test_user_create_model(self):
        """Проверка модели UserCreate"""
        fields = UserCreate.model_fields

        assert "username" in fields
        assert "email" in fields
        assert "password" in fields
        assert "full_name" in fields

        # Проверяем обязательность полей
        assert fields["username"].is_required()
        assert fields["email"].is_required()
        assert fields["password"].is_required()
        assert not fields["full_name"].is_required()

    def test_user_in_db_model(self):
        """Проверка модели UserInDB"""
        fields = UserInDB.model_fields

        # Должен наследовать все поля от User
        assert "username" in fields
        assert "email" in fields
        assert "disabled" in fields
        assert "full_name" in fields

        # И иметь дополнительное поле
        assert "hashed_password" in fields
        assert fields["hashed_password"].annotation == str

    def test_token_models(self):
        """Проверка моделей токенов"""
        # Token
        token_fields = Token.model_fields
        assert "access_token" in token_fields
        assert "token_type" in token_fields
        assert token_fields["access_token"].annotation == str
        assert token_fields["token_type"].annotation == str

        # TokenData
        token_data_fields = Token.model_fields
        assert "username" in token_data_fields
        assert token_data_fields["username"].default is None  # Optional

    def test_event_models(self):
        """Проверка моделей событий"""
        # EventCreate
        create_fields = EventCreate.model_fields
        assert "type" in create_fields
        assert "intensity" in create_fields
        assert "timestamp" in create_fields
        assert "metadata" in create_fields

        assert create_fields["type"].annotation == str
        assert create_fields["intensity"].allow_none is True
        assert create_fields["timestamp"].allow_none is True
        assert create_fields["metadata"].allow_none is True

        # EventResponse
        response_fields = EventResponse.model_fields
        assert "type" in response_fields
        assert "intensity" in response_fields
        assert "timestamp" in response_fields
        assert "metadata" in response_fields
        assert "message" in response_fields

    def test_status_response_models(self):
        """Проверка моделей ответов статуса"""
        # StatusResponse (minimal)
        min_fields = StatusResponse.model_fields
        required_fields = ["active", "ticks", "age", "energy", "stability", "integrity"]
        for field in required_fields:
            assert field in min_fields
            assert min_fields[field].is_required()

        # ExtendedStatusResponse
        ext_fields = ExtendedStatusResponse.model_fields

        # Основные метрики (обязательные)
        vital_fields = ["active", "energy", "integrity", "stability", "ticks", "age", "subjective_time"]
        for field in vital_fields:
            assert field in ext_fields

        # Опциональные поля
        optional_fields = [
            "life_id", "birth_timestamp", "learning_params", "adaptation_params",
            "last_significance", "last_event_intensity", "planning", "intelligence",
            "subjective_time_base_rate", "memory", "recent_events"
        ]
        for field in optional_fields:
            assert field in ext_fields
            assert not ext_fields[field].is_required()

    # ============================================================================
    # Utility Functions
    # ============================================================================

    def test_verify_password_function(self):
        """Проверка функции verify_password"""
        sig = inspect.signature(verify_password)
        assert len(sig.parameters) == 2
        assert "plain_password" in sig.parameters
        assert "hashed_password" in sig.parameters

        # Функция должна возвращать bool
        assert callable(verify_password)

    def test_get_password_hash_function(self):
        """Проверка функции get_password_hash"""
        sig = inspect.signature(get_password_hash)
        assert len(sig.parameters) == 1
        assert "password" in sig.parameters

        # Функция должна возвращать строку
        result = get_password_hash("test")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_user_function(self):
        """Проверка функции get_user"""
        sig = inspect.signature(get_user)
        assert len(sig.parameters) == 2
        assert "db" in sig.parameters
        assert "username" in sig.parameters

        # Функция может возвращать UserInDB или None
        result = get_user({}, "nonexistent")
        assert result is None

        result = get_user(fake_users_db, "admin")
        assert isinstance(result, UserInDB)
        assert result.username == "admin"

    def test_authenticate_user_function(self):
        """Проверка функции authenticate_user"""
        sig = inspect.signature(authenticate_user)
        assert len(sig.parameters) == 3
        assert "fake_db" in sig.parameters
        assert "username" in sig.parameters
        assert "password" in sig.parameters

        # Правильная аутентификация
        result = authenticate_user(fake_users_db, "admin", "admin123")
        assert isinstance(result, UserInDB)
        assert result.username == "admin"

        # Неправильный пароль
        result = authenticate_user(fake_users_db, "admin", "wrong")
        assert result is None

        # Несуществующий пользователь
        result = authenticate_user(fake_users_db, "nonexistent", "password")
        assert result is None

    def test_create_access_token_function(self):
        """Проверка функции create_access_token"""
        sig = inspect.signature(create_access_token)
        assert len(sig.parameters) == 2
        assert "data" in sig.parameters
        assert "expires_delta" in sig.parameters

        # Функция должна возвращать строку (JWT токен)
        result = create_access_token({"sub": "test"})
        assert isinstance(result, str)
        assert len(result) > 0

        # Токен должен содержать точки (структура JWT)
        assert result.count(".") == 2

    # ============================================================================
    # Dependency Functions
    # ============================================================================

    def test_get_current_user_dependency(self):
        """Проверка зависимости get_current_user"""
        sig = inspect.signature(get_current_user)
        assert len(sig.parameters) == 1
        assert "token" in sig.parameters

        # Это async функция
        assert inspect.iscoroutinefunction(get_current_user)

    def test_get_current_active_user_dependency(self):
        """Проверка зависимости get_current_active_user"""
        sig = inspect.signature(get_current_active_user)
        assert len(sig.parameters) == 1
        assert "current_user" in sig.parameters

        assert inspect.iscoroutinefunction(get_current_active_user)

    # ============================================================================
    # FastAPI Application
    # ============================================================================

    def test_fastapi_app_structure(self):
        """Проверка структуры FastAPI приложения"""
        assert app is not None
        assert hasattr(app, "title")
        assert hasattr(app, "description")
        assert hasattr(app, "version")

        assert app.title == "Life API"
        assert "аутентификацией" in app.description
        assert app.version == "1.0.0"

    def test_fastapi_app_routes(self):
        """Проверка маршрутов FastAPI приложения"""
        routes = [route.path for route in app.routes]

        # Проверяем наличие основных маршрутов
        assert "/" in routes
        assert "/register" in routes
        assert "/token" in routes
        assert "/protected" in routes
        assert "/status" in routes
        assert "/event" in routes
        assert "/users" in routes

    # ============================================================================
    # Model Validation
    # ============================================================================

    def test_user_model_validation(self):
        """Проверка валидации модели User"""
        # Корректные данные
        user = User(username="test", email="test@example.com")
        assert user.username == "test"
        assert user.email == "test@example.com"
        assert user.disabled is False
        assert user.full_name is None

        # С полным именем
        user = User(username="test", email="test@example.com", full_name="Test User", disabled=True)
        assert user.full_name == "Test User"
        assert user.disabled is True

    def test_user_model_validation_errors(self):
        """Проверка ошибок валидации модели User"""
        # Пустое имя пользователя
        with pytest.raises(ValidationError):
            User(username="", email="test@example.com")

        # Некорректный email
        with pytest.raises(ValidationError):
            User(username="test", email="not-an-email")

    def test_user_create_validation(self):
        """Проверка валидации UserCreate"""
        # Минимальные данные
        user = UserCreate(username="test", email="test@example.com", password="password")
        assert user.username == "test"
        assert user.password == "password"

        # С полным именем
        user = UserCreate(username="test", email="test@example.com", password="password", full_name="Test User")
        assert user.full_name == "Test User"

    def test_event_create_validation(self):
        """Проверка валидации EventCreate"""
        # Только тип
        event = EventCreate(type="noise")
        assert event.type == "noise"
        assert event.intensity == 0.0  # По умолчанию
        assert event.timestamp is None
        assert event.metadata == {}  # По умолчанию

        # Полные данные
        event = EventCreate(
            type="shock",
            intensity=-0.8,
            timestamp=123456.0,
            metadata={"source": "test"}
        )
        assert event.intensity == -0.8
        assert event.timestamp == 123456.0
        assert event.metadata == {"source": "test"}

    def test_token_validation(self):
        """Проверка валидации Token"""
        token = Token(access_token="jwt.token.here", token_type="bearer")
        assert token.access_token == "jwt.token.here"
        assert token.token_type == "bearer"

    # ============================================================================
    # Security and Authentication Architecture
    # ============================================================================

    def test_password_hashing_security(self):
        """Проверка безопасности хеширования паролей"""
        password = "mysecretpassword"

        # Хеш должен быть уникальным
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert hash1 != hash2  # bcrypt добавляет соль

        # Верификация должна работать
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

        # Неправильный пароль не должен верифицироваться
        assert not verify_password("wrongpassword", hash1)

    def test_fake_users_db_structure(self):
        """Проверка структуры базы данных пользователей"""
        assert isinstance(fake_users_db, dict)
        assert len(fake_users_db) >= 2  # admin и user

        # Проверяем структуру пользователей
        for username, user in fake_users_db.items():
            assert isinstance(user, UserInDB)
            assert user.username == username
            assert isinstance(user.hashed_password, str)
            assert len(user.hashed_password) > 0
            assert isinstance(user.email, str)
            assert "@" in user.email

    def test_jwt_token_structure(self):
        """Проверка структуры JWT токенов"""
        import jwt

        # Создаем токен
        data = {"sub": "testuser", "exp": 2000000000}
        token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

        # Декодируем и проверяем
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["sub"] == "testuser"

    # ============================================================================
    # API Endpoints Structure
    # ============================================================================

    def test_endpoints_have_proper_auth(self):
        """Проверка что защищенные эндпоинты требуют аутентификации"""
        # Находим маршруты, требующие аутентификации
        protected_routes = []
        for route in app.routes:
            if hasattr(route, "dependant"):
                # Проверяем зависимости маршрута
                for dependency in route.dependant.dependencies:
                    if "get_current" in str(dependency.call):
                        protected_routes.append(route.path)

        # Эти маршруты должны требовать аутентификации
        expected_protected = ["/protected", "/status", "/event", "/users"]
        for route in expected_protected:
            assert route in protected_routes, f"Route {route} should be protected"

    def test_public_endpoints_no_auth(self):
        """Проверка что публичные эндпоинты не требуют аутентификации"""
        public_routes = ["/", "/register", "/token"]

        protected_routes = []
        for route in app.routes:
            if hasattr(route, "dependant"):
                for dependency in route.dependant.dependencies:
                    if "get_current" in str(dependency.call):
                        protected_routes.append(route.path)

        for route in public_routes:
            assert route not in protected_routes, f"Route {route} should be public"

    # ============================================================================
    # Error Handling Structure
    # ============================================================================

    def test_http_exception_structure(self):
        """Проверка структуры HTTP исключений"""
        # Импортируем типы исключений
        from fastapi import HTTPException, status

        # Проверяем что используем правильные коды статусов
        assert hasattr(status, "HTTP_401_UNAUTHORIZED")
        assert hasattr(status, "HTTP_400_BAD_REQUEST")
        assert hasattr(status, "HTTP_201_CREATED")

    def test_dependency_error_handling(self):
        """Проверка обработки ошибок в зависимостях"""
        # Mock токена для тестирования
        from fastapi.security import HTTPBearer

        # HTTPBearer должен быть настроен
        assert http_bearer is not None
        assert isinstance(http_bearer, HTTPBearer)

    # ============================================================================
    # Response Models Consistency
    # ============================================================================

    def test_response_models_consistency(self):
        """Проверка консистентности моделей ответов"""
        # StatusResponse должен быть подмножеством ExtendedStatusResponse
        min_fields = set(StatusResponse.model_fields.keys())
        ext_fields = set(ExtendedStatusResponse.model_fields.keys())

        # Все поля минимального ответа должны быть в расширенном
        assert min_fields.issubset(ext_fields)

    def test_event_response_structure(self):
        """Проверка структуры EventResponse"""
        # EventResponse должен содержать все поля EventCreate плюс message
        create_fields = set(EventCreate.model_fields.keys())
        response_fields = set(EventResponse.model_fields.keys())

        # response должен содержать все поля create плюс message
        assert create_fields.issubset(response_fields)
        assert "message" in response_fields
        assert EventResponse.model_fields["message"].annotation == str