"""
REST API с аутентификацией для проекта Life.

Использует FastAPI с JWT токенами для аутентификации.
"""

import os
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBearer, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

# Конфигурация
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Инициализация
app = FastAPI(
    title="Life API",
    description="REST API с аутентификацией для проекта Life",
    version="1.0.0",
)

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["sha256_crypt", "bcrypt"], deprecated="auto")

# OAuth2 схема
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
http_bearer = HTTPBearer()


# Модели данных
class User(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    disabled: bool = False


class UserInDB(User):
    hashed_password: str


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class EventCreate(BaseModel):
    type: str
    intensity: Optional[float] = 0.0
    timestamp: Optional[float] = None
    metadata: Optional[dict] = {}


class EventResponse(BaseModel):
    type: str
    intensity: float
    timestamp: float
    metadata: dict
    message: str


class StatusResponse(BaseModel):
    """Минимальный контракт статуса (для обратной совместимости)."""
    active: bool
    ticks: int
    age: float
    energy: float
    stability: float
    integrity: float


class ExtendedStatusResponse(BaseModel):
    """Расширенный контракт статуса с полной информацией о состоянии системы."""
    # Основные метрики (Vital Parameters) - ОБЯЗАТЕЛЬНЫЕ
    active: bool
    energy: float
    integrity: float
    stability: float
    
    # Временные метрики - ОБЯЗАТЕЛЬНЫЕ
    ticks: int
    age: float
    subjective_time: float
    
    # Внутренняя динамика - РЕКОМЕНДУЕМЫЕ
    fatigue: float
    tension: float
    
    # Идентификация - ОПЦИОНАЛЬНЫЕ
    life_id: Optional[str] = None
    birth_timestamp: Optional[float] = None
    
    # Параметры обучения и адаптации - РЕКОМЕНДУЕМЫЕ
    learning_params: Optional[dict] = None
    adaptation_params: Optional[dict] = None
    
    # Последние значения - РЕКОМЕНДУЕМЫЕ
    last_significance: Optional[float] = None
    last_event_intensity: Optional[float] = None
    
    # Когнитивные слои - РЕКОМЕНДУЕМЫЕ
    planning: Optional[dict] = None
    intelligence: Optional[dict] = None
    
    # Параметры субъективного времени - ОПЦИОНАЛЬНЫЕ
    subjective_time_base_rate: Optional[float] = None
    subjective_time_rate_min: Optional[float] = None
    subjective_time_rate_max: Optional[float] = None
    subjective_time_intensity_coeff: Optional[float] = None
    subjective_time_stability_coeff: Optional[float] = None
    
    # Опциональные большие поля (только если запрошены через query-параметры)
    memory: Optional[list] = None
    recent_events: Optional[list] = None
    energy_history: Optional[list] = None
    stability_history: Optional[list] = None
    adaptation_history: Optional[list] = None
    
    class Config:
        # Позволяет использовать модель с дополнительными полями
        extra = "allow"


# База данных пользователей (в продакшене использовать реальную БД)
fake_users_db: dict[str, UserInDB] = {
    "admin": UserInDB(
        username="admin",
        email="admin@example.com",
        full_name="Administrator",
        hashed_password=pwd_context.hash("admin123"[:72]),
        disabled=False,
    ),
    "user": UserInDB(
        username="user",
        email="user@example.com",
        full_name="Regular User",
        hashed_password=pwd_context.hash("user123"),
        disabled=False,
    ),
}


# Утилиты
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Хеширование пароля."""
    return pwd_context.hash(password)


def get_user(db: dict, username: str) -> Optional[UserInDB]:
    """Получение пользователя из базы данных."""
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict.dict())
    return None


def authenticate_user(
    fake_db: dict, username: str, password: str
) -> Optional[UserInDB]:
    """Аутентификация пользователя."""
    user = get_user(fake_db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создание JWT токена."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Получение текущего пользователя из токена."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return User(**user.dict())


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Получение активного пользователя."""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# Endpoints
@app.get("/")
async def root():
    """Корневой endpoint."""
    return {
        "message": "Life API с аутентификацией",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "register": "/register",
            "login": "/token",
            "protected": "/protected",
            "status": "/status",
            "event": "/event",
        },
    }


@app.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Регистрация нового пользователя."""
    if user_data.username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    hashed_password = get_password_hash(user_data.password)
    user_in_db = UserInDB(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        disabled=False,
    )
    fake_users_db[user_data.username] = user_in_db

    return User(**user_in_db.dict())


@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Получение JWT токена для аутентификации."""
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/protected")
async def protected_route(current_user: User = Depends(get_current_active_user)):
    """Пример защищенного endpoint."""
    return {
        "message": f"Привет, {current_user.username}! Это защищенный endpoint.",
        "user": current_user.username,
        "email": current_user.email,
    }


@app.get("/status", response_model=ExtendedStatusResponse)
async def get_status(
    current_user: User = Depends(get_current_active_user),
    memory_limit: Optional[int] = None,
    events_limit: Optional[int] = None,
    energy_history_limit: Optional[int] = None,
    stability_history_limit: Optional[int] = None,
    adaptation_history_limit: Optional[int] = None,
    minimal: bool = False,
):
    """
    Получение статуса системы (защищенный endpoint).
    
    Поддерживает расширенный контракт с опциональными полями.
    
    Query-параметры:
    - memory_limit: ограничить количество записей памяти
    - events_limit: ограничить количество последних событий
    - energy_history_limit: ограничить количество значений истории энергии
    - stability_history_limit: ограничить количество значений истории стабильности
    - adaptation_history_limit: ограничить количество значений истории адаптации
    - minimal: если True, возвращает только минимальный набор полей (для обратной совместимости)
    
    Примечание: В текущей реализации возвращаются примерные данные.
    Для полной интеграции необходимо подключить реальный SelfState.
    """
    # Здесь можно интегрировать с существующим SelfState
    # Пока возвращаем примерные данные с расширенным контрактом
    
    # Формируем лимиты для больших полей
    limits = {}
    if memory_limit is not None:
        limits["memory_limit"] = memory_limit
    if events_limit is not None:
        limits["events_limit"] = events_limit
    if energy_history_limit is not None:
        limits["energy_history_limit"] = energy_history_limit
    if stability_history_limit is not None:
        limits["stability_history_limit"] = stability_history_limit
    if adaptation_history_limit is not None:
        limits["adaptation_history_limit"] = adaptation_history_limit
    
    # Если запрошен минимальный контракт, возвращаем только основные поля
    if minimal:
        return StatusResponse(
            active=True,
            ticks=100,
            age=100.5,
            energy=85.0,
            stability=0.95,
            integrity=0.98,
        )
    
    # Возвращаем расширенный контракт
    return ExtendedStatusResponse(
        # Основные метрики
        active=True,
        energy=85.0,
        integrity=0.98,
        stability=0.95,
        # Временные метрики
        ticks=100,
        age=100.5,
        subjective_time=105.0,
        # Внутренняя динамика
        fatigue=10.0,
        tension=5.0,
        # Идентификация
        life_id="550e8400-e29b-41d4-a716-446655440000",
        birth_timestamp=1700000000.0,
        # Параметры обучения и адаптации
        learning_params={
            "event_type_sensitivity": {
                "noise": 0.2,
                "decay": 0.2,
                "recovery": 0.2,
                "shock": 0.2,
                "idle": 0.2,
            },
            "significance_thresholds": {
                "noise": 0.1,
                "decay": 0.1,
                "recovery": 0.1,
                "shock": 0.1,
                "idle": 0.1,
            },
            "response_coefficients": {
                "dampen": 0.5,
                "absorb": 1.0,
                "ignore": 0.0,
            },
        },
        adaptation_params={
            "behavior_sensitivity": {
                "noise": 0.2,
                "decay": 0.2,
                "recovery": 0.2,
                "shock": 0.2,
                "idle": 0.2,
            },
            "behavior_thresholds": {
                "noise": 0.1,
                "decay": 0.1,
                "recovery": 0.1,
                "shock": 0.1,
                "idle": 0.1,
            },
            "behavior_coefficients": {
                "dampen": 0.5,
                "absorb": 1.0,
                "ignore": 0.0,
            },
        },
        # Последние значения
        last_significance=0.7,
        last_event_intensity=0.5,
        # Когнитивные слои
        planning={},
        intelligence={},
        # Параметры субъективного времени
        subjective_time_base_rate=1.0,
        subjective_time_rate_min=0.1,
        subjective_time_rate_max=3.0,
        subjective_time_intensity_coeff=1.0,
        subjective_time_stability_coeff=0.5,
        # Большие поля (только если запрошены через лимиты)
        memory=[] if memory_limit is not None else None,
        recent_events=[] if events_limit is not None else None,
        energy_history=[] if energy_history_limit is not None else None,
        stability_history=[] if stability_history_limit is not None else None,
        adaptation_history=[] if adaptation_history_limit is not None else None,
    )


@app.post("/event", response_model=EventResponse)
async def create_event(
    event: EventCreate, current_user: User = Depends(get_current_active_user)
):
    """Создание события (защищенный endpoint)."""
    import time

    timestamp = event.timestamp if event.timestamp else time.time()

    # Здесь можно интегрировать с существующей EventQueue
    # Пока возвращаем подтверждение

    return EventResponse(
        type=event.type,
        intensity=event.intensity,
        timestamp=timestamp,
        metadata=event.metadata,
        message=f"Событие '{event.type}' успешно создано пользователем {current_user.username}",
    )


@app.get("/users", response_model=List[User])
async def list_users(current_user: User = Depends(get_current_active_user)):
    """Список всех пользователей (только для аутентифицированных)."""
    return [User(**user.dict()) for user in fake_users_db.values()]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
