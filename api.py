"""
Простой REST API для проекта Life - эксперимента непрерывной жизни.

API без аутентификации пользователей, предназначен для наблюдения за экспериментом.
Опциональная защита через API ключ для предотвращения случайного доступа.
"""

import os
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Header, Query, status
from pydantic import BaseModel, ConfigDict

# Конфигурация
API_KEY = os.getenv("LIFE_API_KEY", None)  # Опциональный API ключ для защиты

# Инициализация
app = FastAPI(
    title="Life Experiment API",
    description="API для наблюдения за экспериментом непрерывной жизни Life",
    version="1.0.0",
)


def verify_api_key(x_api_key: Optional[str] = Header(None)) -> bool:
    """Проверка API ключа (опциональная)."""
    if API_KEY is None:
        return True  # Если ключ не настроен, доступ открыт для экспериментов
    if x_api_key is None:
        return False
    return x_api_key == API_KEY


# Модели данных
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
    """Базовый статус системы Life."""
    active: bool
    ticks: int
    age: float
    energy: float
    stability: float
    integrity: float
    subjective_time: float
    fatigue: float
    tension: float


class ExtendedStatusResponse(BaseModel):
    """Расширенный статус с дополнительной информацией."""
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

    model_config = ConfigDict(extra="allow")


# Импортируем SnapshotReader для чтения состояния из snapshots
from src.runtime.snapshot_reader import read_life_status


def check_api_access(x_api_key: Optional[str] = Header(None)):
    """Проверка доступа к API."""
    if not verify_api_key(x_api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key"
        )


@app.get("/")
async def root():
    """Корневой endpoint эксперимента Life."""
    return {
        "message": "Life Experiment API - наблюдение за непрерывной жизнью",
        "version": "1.0.0",
        "experiment": "Непрерывная жизнь автономной системы",
        "docs": "/docs",
        "endpoints": {
            "status": "/status - состояние системы",
            "event": "/event - создание события",
            "health": "/health - проверка здоровья API",
        },
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья API."""
    # Проверяем доступность snapshots вместо живого объекта
    from src.runtime.snapshot_reader import get_snapshot_reader
    snapshot_available = get_snapshot_reader().read_latest_snapshot() is not None

    return {
        "status": "healthy",
        "experiment": "Life continuous existence",
        "api_version": "1.0.0",
        "snapshot_available": snapshot_available
    }


@app.get("/status", response_model=ExtendedStatusResponse)
async def get_status(
    x_api_key: Optional[str] = Header(None),
    minimal: bool = Query(False, description="Минимальный статус"),
    memory_limit: Optional[int] = Query(None, description="Лимит записей памяти"),
    events_limit: Optional[int] = Query(None, description="Лимит последних событий"),
):
    """Получение статуса системы Life."""
    check_api_access(x_api_key)

    # Читаем статус из snapshot файла вместо живого объекта
    status_data = read_life_status(
        include_optional=not minimal,
        limits={
            "memory_limit": memory_limit,
            "events_limit": events_limit,
        }
    )

    if status_data is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Life system snapshot not available"
        )

    return ExtendedStatusResponse(**status_data)


@app.post("/event", response_model=EventResponse)
async def create_event(
    event: EventCreate,
    x_api_key: Optional[str] = Header(None)
):
    """Создание события в системе Life."""
    check_api_access(x_api_key)

    # Импортируем здесь чтобы избежать циклических импортов
    from src.runtime.loop import add_external_event

    # Добавляем событие в систему
    result = add_external_event(event.type, event.intensity, event.metadata)

    return EventResponse(
        type=event.type,
        intensity=event.intensity,
        timestamp=event.timestamp or result.get("timestamp", 0),
        metadata=event.metadata,
        message=f"Event '{event.type}' added to Life system"
    )


# API теперь читает состояние из snapshot файлов,
# поэтому установка ссылки на живой объект больше не требуется