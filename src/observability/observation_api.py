"""
Observation API - REST API для внешнего наблюдения за системой Life.

Предоставляет endpoints для доступа к данным наблюдений через HTTP.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .passive_data_sink import PassiveDataSink, ObservationData
from .async_data_sink import AsyncDataSink
from .raw_data_access import RawDataAccess

logger = logging.getLogger(__name__)

# Создаем FastAPI приложение
app = FastAPI(
    title="Life System Observation API",
    description="API для внешнего наблюдения за системой Life",
    version="1.0.0"
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
passive_sink = PassiveDataSink(max_entries=10000)
async_sink = AsyncDataSink(max_queue_size=1000, enabled=True)
raw_access = RawDataAccess(data_sources=[passive_sink, async_sink])

# Глобальный список всех источников данных для RawDataAccess
_all_data_sources = [passive_sink, async_sink]


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
    Добавить новое наблюдение.

    Принимает данные наблюдения и сохраняет их в системе.
    """
    try:
        # Добавляем в пассивный sink
        passive_sink.receive_data(
            event_type=observation.event_type,
            data=observation.data,
            source=observation.source,
            metadata=observation.metadata
        )

        # Добавляем в асинхронный sink (если он активен)
        if async_sink.enabled:
            await async_sink.receive_data_async(
                event_type=observation.event_type,
                data=observation.data,
                source=observation.source,
                metadata=observation.metadata
            )

        return {"status": "observation_added", "message": "Наблюдение успешно добавлено"}

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
    Получить список наблюдений.

    Возвращает недавние наблюдения с возможностью фильтрации.
    """
    try:
        # Получаем данные через RawDataAccess
        observations = raw_access.get_raw_data(
            source_filter=source,
            event_type_filter=event_type,
            limit=limit
        )

        # Конвертируем в словари для JSON ответа
        result = []
        for obs in observations:
            result.append({
                "timestamp": obs.timestamp,
                "event_type": obs.event_type,
                "data": obs.data,
                "source": obs.source,
                "metadata": obs.metadata
            })

        return result

    except Exception as e:
        logger.error(f"Ошибка при получении наблюдений: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@app.get("/observations/summary", response_model=Dict[str, Any])
async def get_observations_summary():
    """
    Получить сводку по наблюдениям.

    Возвращает статистическую информацию о хранимых данных.
    """
    try:
        summary = raw_access.get_data_summary()
        return summary

    except Exception as e:
        logger.error(f"Ошибка при получении сводки: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@app.get("/observations/export")
async def export_observations(
    format: str = Query("json", description="Формат экспорта (json, jsonl, csv)"),
    source: Optional[str] = Query(None, description="Фильтр по источнику"),
    event_type: Optional[str] = Query(None, description="Фильтр по типу события")
):
    """
    Экспортировать наблюдения.

    Возвращает данные в указанном формате.
    """
    try:
        if format not in ["json", "jsonl", "csv"]:
            raise HTTPException(status_code=400, detail="Неподдерживаемый формат экспорта")

        # Экспортируем данные
        export_data = raw_access.export_data(
            format=format,
            source_filter=source,
            event_type_filter=event_type
        )

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
    """
    Получить статистику компонентов наблюдения.

    Возвращает детальную статистику по всем компонентам.
    """
    try:
        stats = {
            "passive_sink": passive_sink.get_statistics(),
            "async_sink": async_sink.get_statistics(),
            "raw_access": {
                "data_sources_count": len(raw_access.data_sources),
                "event_type_distribution": raw_access.get_event_type_distribution(),
                "source_distribution": raw_access.get_source_distribution()
            }
        }

        return stats

    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@app.delete("/observations/")
async def clear_observations():
    """
    Очистить все наблюдения.

    Удаляет все хранимые данные наблюдений.
    """
    try:
        passive_sink.clear_data()
        async_sink.clear_processed_data()

        return {"status": "cleared", "message": "Все наблюдения очищены"}

    except Exception as e:
        logger.error(f"Ошибка при очистке наблюдений: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@app.on_event("startup")
async def startup_event():
    """Действия при запуске сервера."""
    try:
        # Запускаем асинхронный sink
        await async_sink.start()
        logger.info("Observation API запущен")
    except Exception as e:
        logger.error(f"Ошибка при запуске Observation API: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Действия при остановке сервера."""
    try:
        # Останавливаем асинхронный sink
        await async_sink.stop()
        logger.info("Observation API остановлен")
    except Exception as e:
        logger.error(f"Ошибка при остановке Observation API: {e}")