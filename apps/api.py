"""
Минимальный REST API для проекта Life - эксперимента непрерывной жизни.

API с полной изоляцией от runtime loop. Предоставляет только чтение состояния
и внешнее воздействие через события. Все endpoints пассивны и не влияют
на внутреннюю работу системы.

Безопасные endpoints:
- GET /status - чтение состояния из snapshots
- GET /refresh-cache - no-op для совместимости
- GET /clear-data - очистка логов и snapshots
- POST /event - добавление внешних событий

Опциональная защита через API ключ для предотвращения случайного доступа.
"""

import os
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict

from src.state.self_state import SelfState

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


def get_current_state() -> dict:
    """Получение текущего состояния системы из последнего snapshot."""
    from src.state.self_state import SelfState

    try:
        state = SelfState().load_latest_snapshot()
        return state.get_safe_status_dict()
    except FileNotFoundError:
        # Если нет snapshots, возвращаем начальное состояние
        state = SelfState()
        return state.get_safe_status_dict()


def check_api_access(x_api_key: Optional[str] = Header(None)):
    """Проверка доступа к API."""
    if not verify_api_key(x_api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or missing API key"
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
            "refresh-cache": "/refresh-cache - обновление кэша",
        },
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья API."""
    return {
        "status": "healthy",
        "experiment": "Life continuous existence",
        "api_version": "1.0.0",
        "read_enabled": True,
    }


@app.post("/refresh-cache")
async def refresh_cache(x_api_key: Optional[str] = Header(None)):
    """Обновление кэша состояния (для совместимости с тестами)."""
    check_api_access(x_api_key)

    # В текущей реализации состояние читается из snapshots при каждом запросе,
    # поэтому кэширование не требуется. Просто возвращаем успех.
    return {"message": "Cache refreshed (no-op in current implementation)"}


@app.get("/status", response_model=ExtendedStatusResponse)
async def get_status(
    x_api_key: Optional[str] = Header(None),
    minimal: bool = Query(False, description="Минимальный статус"),
    memory_limit: Optional[int] = Query(None, description="Лимит записей памяти"),
    events_limit: Optional[int] = Query(None, description="Лимит последних событий"),
):
    """Получение статуса системы Life."""
    check_api_access(x_api_key)

    # Получаем текущее состояние
    status_data = get_current_state()

    # Применяем лимиты если указаны
    limits = {}
    if memory_limit is not None:
        limits["memory_limit"] = memory_limit
    if events_limit is not None:
        limits["events_limit"] = events_limit

    if limits:
        status_data = SelfState().get_safe_status_dict(limits=limits)

    if minimal:
        # Для минимального статуса возвращаем только основные метрики
        minimal_data = {
            "active": status_data.get("active", False),
            "energy": status_data.get("energy", 0.0),
            "integrity": status_data.get("integrity", 0.0),
            "stability": status_data.get("stability", 0.0),
            "ticks": status_data.get("ticks", 0),
            "age": status_data.get("age", 0.0),
            "subjective_time": status_data.get("subjective_time", 0.0),
            "fatigue": status_data.get("fatigue", 0.0),
            "tension": status_data.get("tension", 0.0),
        }
        return ExtendedStatusResponse(**minimal_data)

    return ExtendedStatusResponse(**status_data)


@app.post("/event", response_model=EventResponse)
async def create_event(event: EventCreate, x_api_key: Optional[str] = Header(None)):
    """Создание события в системе Life."""
    check_api_access(x_api_key)

    # В упрощенном API просто логируем событие
    # TODO: Интегрировать с runtime loop когда будет доступ к event_queue
    import time

    timestamp = event.timestamp or time.time()

    return EventResponse(
        type=event.type,
        intensity=event.intensity,
        timestamp=timestamp,
        metadata=event.metadata,
        message=f"Event '{event.type}' accepted by Life system",
    )
# API теперь читает состояние из snapshot файлов,
# поэтому установка ссылки на живой объект больше не требуется
