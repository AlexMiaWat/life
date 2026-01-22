"""
Observation API - REST API для внешнего наблюдения за системой Life.

Предоставляет endpoints для доступа к данным наблюдений через HTTP.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel

# All observation is handled by StructuredLogger in runtime loop

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application."""
    logger.warning("Observation API is deprecated. Use StructuredLogger for active observation.")
    yield
    logger.warning("Observation API is deprecated. Use StructuredLogger for active observation.")

# Создаем FastAPI приложение
app = FastAPI(
    title="Life System Observation API",
    description="API для внешнего наблюдения за системой Life",
    version="1.0.0",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобальные компоненты для хранения данных
# All observation is handled by StructuredLogger in runtime loop
# All observation is handled by StructuredLogger - no raw access needed


class ObservationRequest(BaseModel):
    """Модель запроса для добавления наблюдения."""
    event_type: str
    data: Dict[str, Any]
    source: str
    metadata: Optional[Dict[str, Any]] = None


class StatisticsResponse(BaseModel):
    """Модель ответа со статистикой."""
    total_received: int
    current_entries: int
    sources: List[str]
    event_types: List[str]


class MetricsResponse(BaseModel):
    """Модель ответа с метриками наблюдений."""
    total_observations: int
    active_sources: int
    event_types_count: int
    avg_observations_per_minute: float
    last_observation_timestamp: Optional[float] = None
    memory_usage_mb: float


@app.post("/observations/", response_model=Dict[str, str])
async def add_observation(observation: ObservationRequest):
    """
    DEPRECATED: This API endpoint is deprecated.

    All observation is handled by StructuredLogger in runtime loop.
    """
    logger.warning("Observation API is deprecated. Use StructuredLogger for active observation.")
    try:
        return {"status": "deprecated", "message": "This API is deprecated. Use StructuredLogger for active observation."}

    except Exception as e:
        logger.error(f"Ошибка при добавлении наблюдения: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@app.get("/observations/", response_model=List[Dict[str, Any]])
async def get_observations(
    limit: Optional[int] = Query(None, description="Максимальное количество записей"),
    source: Optional[str] = Query(None, description="Фильтр по источнику"),
    event_type: Optional[str] = Query(None, description="Фильтр по типу события")
):
    """
    DEPRECATED: This API endpoint is deprecated.

    All observation is handled by StructuredLogger in runtime loop.
    """
    logger.warning("Observation API is deprecated. Use StructuredLogger for active observation.")
    return []


@app.get("/observations/summary", response_model=Dict[str, Any])
async def get_observations_summary():
    """
    Получить сводку по наблюдениям.

    Возвращает статистическую информацию о хранимых данных.
    """
    try:
        # All observation is handled by StructuredLogger - return empty summary
        return {
            "total_observations": 0,
            "active_sources": 0,
            "event_types_count": 0,
            "avg_observations_per_minute": 0.0,
            "last_observation_timestamp": None,
            "memory_usage_mb": 0.0
        }

    except Exception as e:
        logger.error(f"Ошибка при получении сводки: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@app.get("/observations/export")
async def export_observations(
    format: str = Query("json", description="Формат экспорта (json, jsonl, csv)"),
    source: Optional[str] = Query(None, description="Фильтр по источнику"),
    event_type: Optional[str] = Query(None, description="Фильтр по типу события")
):
    "DEPRECATED: This API is deprecated."
    try:
        if format not in ["json", "jsonl", "csv"]:
            raise HTTPException(status_code=400, detail="Неподдерживаемый формат экспорта")

        # All observation is handled by StructuredLogger - return empty data
        if format == "json":
            export_data = "{}"
        elif format == "jsonl":
            export_data = ""
        elif format == "csv":
            export_data = "timestamp,event_type,data\n"

        # Определяем MIME тип
        mime_types = {
            "json": "application/json",
            "jsonl": "application/x-ndjson",
            "csv": "text/csv"
        }

        from fastapi.responses import Response
        return Response(
            content=export_data,
            media_type=mime_types[format],
            headers={"Content-Disposition": f"attachment; filename=observations.{format}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при экспорте наблюдений: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@app.get("/statistics/", response_model=Dict[str, Any])
async def get_statistics():
    "DEPRECATED: This API is deprecated.    "
    logger.warning("Observation API is deprecated. Use StructuredLogger for active observation.")
    return {}


@app.delete("/observations/")
async def clear_observations():
    "DEPRECATED: This API is deprecated."
    logger.warning("Observation API is deprecated. Use StructuredLogger for active observation.")
    return {"status": "deprecated", "message": "This API is deprecated. Use StructuredLogger for active observation."}

