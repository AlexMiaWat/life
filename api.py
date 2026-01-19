"""
REST API с аутентификацией для проекта Life.

Использует FastAPI с JWT токенами для аутентификации.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
from passlib.context import CryptContext
import os

# Конфигурация
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Инициализация
app = FastAPI(
    title="Life API",
    description="REST API с аутентификацией для проекта Life",
    version="1.0.0"
)

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
    active: bool
    ticks: int
    age: float
    energy: float
    stability: float
    integrity: float


# База данных пользователей (в продакшене использовать реальную БД)
fake_users_db: dict[str, UserInDB] = {
    "admin": UserInDB(
        username="admin",
        email="admin@example.com",
        full_name="Administrator",
        hashed_password=pwd_context.hash("admin123"),
        disabled=False
    ),
    "user": UserInDB(
        username="user",
        email="user@example.com",
        full_name="Regular User",
        hashed_password=pwd_context.hash("user123"),
        disabled=False
    )
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


def authenticate_user(fake_db: dict, username: str, password: str) -> Optional[UserInDB]:
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


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
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
            "event": "/event"
        }
    }


@app.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Регистрация нового пользователя."""
    if user_data.username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    hashed_password = get_password_hash(user_data.password)
    user_in_db = UserInDB(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        disabled=False
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


@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Получение информации о текущем пользователе."""
    return current_user


@app.get("/protected")
async def protected_route(current_user: User = Depends(get_current_active_user)):
    """Пример защищенного endpoint."""
    return {
        "message": f"Привет, {current_user.username}! Это защищенный endpoint.",
        "user": current_user.username,
        "email": current_user.email
    }


@app.get("/status", response_model=StatusResponse)
async def get_status(current_user: User = Depends(get_current_active_user)):
    """Получение статуса системы (защищенный endpoint)."""
    # Здесь можно интегрировать с существующим SelfState
    # Пока возвращаем примерные данные
    return StatusResponse(
        active=True,
        ticks=100,
        age=100.5,
        energy=85.0,
        stability=0.95,
        integrity=0.98
    )


@app.post("/event", response_model=EventResponse)
async def create_event(
    event: EventCreate,
    current_user: User = Depends(get_current_active_user)
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
        message=f"Событие '{event.type}' успешно создано пользователем {current_user.username}"
    )


@app.get("/users", response_model=List[User])
async def list_users(current_user: User = Depends(get_current_active_user)):
    """Список всех пользователей (только для аутентифицированных)."""
    return [User(**user.dict()) for user in fake_users_db.values()]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
