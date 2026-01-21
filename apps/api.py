"""
Простой REST API для проекта Life - эксперимента непрерывной жизни.

API без аутентификации пользователей, предназначен для наблюдения за экспериментом.
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


# Модели для экспериментальных endpoints
class MemoryHierarchyResponse(BaseModel):
    """Ответ с информацией о иерархии памяти."""
    status: str
    hierarchy_manager: dict
    sensory_buffer: dict
    episodic_memory: dict
    semantic_store: dict
    procedural_store: dict
    message: str


class ConsciousnessStateResponse(BaseModel):
    """Ответ с информацией о состоянии сознания."""
    consciousness_level: float
    current_state: str
    self_reflection_score: float
    meta_cognition_depth: float
    neural_activity: float
    energy_level: float
    stability: float
    recent_events_count: int
    message: str


class MemoryTransferResponse(BaseModel):
    """Ответ со статистикой переноса данных в памяти."""
    sensory_to_episodic_transfers: int
    episodic_to_semantic_transfers: int
    semantic_to_procedural_transfers: int
    last_semantic_consolidation: float
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


# Экспериментальные endpoints
@app.get("/experimental/memory-hierarchy", response_model=MemoryHierarchyResponse)
async def get_memory_hierarchy(x_api_key: Optional[str] = Header(None)):
    """Получение статуса иерархии памяти."""
    check_api_access(x_api_key)

    # Заглушка: в реальной реализации нужно получить доступ к memory_hierarchy из runtime
    # Пока возвращаем пример структуры
    return MemoryHierarchyResponse(
        status="experimental_feature",
        hierarchy_manager={
            "transfers_sensory_to_episodic": 0,
            "transfers_episodic_to_semantic": 0,
            "transfers_semantic_to_procedural": 0,
            "last_semantic_consolidation": 0.0
        },
        sensory_buffer={
            "available": False,
            "status": "not_initialized",
            "buffer_size": 0
        },
        episodic_memory={
            "available": True,
            "status": "integrated",
            "entries_count": 0  # Нужно получить из self_state.memory
        },
        semantic_store={
            "available": False,
            "status": "not_implemented",
            "concepts_count": 0
        },
        procedural_store={
            "available": False,
            "status": "not_implemented",
            "patterns_count": 0
        },
        message="Memory hierarchy status retrieved (experimental feature)"
    )


@app.get("/experimental/consciousness-state", response_model=ConsciousnessStateResponse)
async def get_consciousness_state(x_api_key: Optional[str] = Header(None)):
    """Получение текущего состояния сознания."""
    check_api_access(x_api_key)

    # Заглушка: в реальной реализации нужно получить доступ к consciousness_engine
    # Пока возвращаем базовые значения
    return ConsciousnessStateResponse(
        consciousness_level=0.0,
        current_state="uninitialized",
        self_reflection_score=0.0,
        meta_cognition_depth=0.0,
        neural_activity=0.0,
        energy_level=0.0,
        stability=0.0,
        recent_events_count=0,
        message="Consciousness state retrieved (experimental feature)"
    )


@app.get("/experimental/memory-transfer", response_model=MemoryTransferResponse)
async def get_memory_transfer_stats(x_api_key: Optional[str] = Header(None)):
    """Получение статистики переноса данных между уровнями памяти."""
    check_api_access(x_api_key)

    # Заглушка: в реальной реализации нужно получить доступ к memory_hierarchy
    return MemoryTransferResponse(
        sensory_to_episodic_transfers=0,
        episodic_to_semantic_transfers=0,
        semantic_to_procedural_transfers=0,
        last_semantic_consolidation=0.0,
        message="Memory transfer statistics retrieved (experimental feature)"
    )


@app.post("/experimental/trigger-consciousness-state")
async def trigger_consciousness_state(
    target_state: str = Query(..., description="Целевое состояние сознания"),
    x_api_key: Optional[str] = Header(None)
):
    """Ручной триггер перехода в указанное состояние сознания."""
    check_api_access(x_api_key)

    valid_states = ["awake", "flow", "reflective", "meta", "dreaming", "unconscious"]

    if target_state not in valid_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid target state. Valid states: {', '.join(valid_states)}"
        )

    # Заглушка: в реальной реализации нужно вызвать соответствующий метод consciousness_engine
    return {
        "message": f"Consciousness state transition triggered to '{target_state}' (experimental feature)",
        "target_state": target_state,
        "status": "triggered_but_not_implemented"
    }


# Совместимость с тестами - пустая база пользователей для упрощенного API
fake_users_db = {}


# API теперь читает состояние из snapshot файлов,
# поэтому установка ссылки на живой объект больше не требуется
