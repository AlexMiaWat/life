"""
REST API для внешнего наблюдения за системой Life.

Предоставляет endpoints для получения отчетов о поведении системы,
метриках производительности и паттернах активности.
"""

import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .external_observer import ExternalObserver, ObservationReport

logger = logging.getLogger(__name__)

# Pydantic модели для API
class MetricsResponse(BaseModel):
    """Ответ с метриками системы."""
    timestamp: float
    cycle_count: int
    uptime_seconds: float
    memory_entries_count: int
    learning_effectiveness: float
    adaptation_rate: float
    decision_success_rate: float
    error_count: int
    integrity_score: float
    energy_level: float
    action_count: int
    event_processing_rate: float
    state_change_frequency: float


class BehaviorPatternResponse(BaseModel):
    """Ответ с паттерном поведения."""
    pattern_type: str
    description: str
    frequency: float
    impact_score: float
    first_observed: float
    last_observed: float
    metadata: Dict[str, Any]


class ObservationReportResponse(BaseModel):
    """Полный отчет наблюдения."""
    observation_period: tuple[float, float]
    metrics_summary: MetricsResponse
    behavior_patterns: List[BehaviorPatternResponse]
    trends: Dict[str, str]
    anomalies: List[Dict[str, Any]]
    recommendations: List[str]


class HealthResponse(BaseModel):
    """Ответ о состоянии API."""
    status: str = Field(..., description="Статус API")
    timestamp: float = Field(..., description="Время ответа")
    version: str = Field(..., description="Версия API")
    uptime: float = Field(..., description="Время работы API")


class ErrorResponse(BaseModel):
    """Ответ об ошибке."""
    error: str
    detail: Optional[str] = None
    timestamp: float


# Создаем FastAPI приложение
app = FastAPI(
    title="Life System External Observation API",
    description="API для внешнего наблюдения и анализа поведения системы Life",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Глобальный экземпляр наблюдателя
observer = ExternalObserver()

# Время запуска API
api_start_time = time.time()


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Проверка состояния API."""
    return HealthResponse(
        status="healthy",
        timestamp=time.time(),
        version="1.0.0",
        uptime=time.time() - api_start_time
    )


@app.get("/observe/logs", response_model=ObservationReportResponse)
async def observe_from_logs(
    start_time_offset: float = Query(3600, description="Время в секундах от текущего момента для начала анализа"),
    end_time: Optional[float] = Query(None, description="Время окончания анализа (timestamp)")
):
    """
    Выполнить наблюдение на основе логов системы.

    - **start_time_offset**: Время в секундах от текущего момента
    - **end_time**: Опциональное время окончания (по умолчанию - сейчас)
    """
    try:
        start_time = time.time() - start_time_offset
        if end_time is None:
            end_time = time.time()

        report = observer.observe_from_logs(start_time, end_time)

        # Преобразуем в Pydantic модель
        return ObservationReportResponse(
            observation_period=report.observation_period,
            metrics_summary=MetricsResponse(
                timestamp=report.metrics_summary.timestamp,
                cycle_count=report.metrics_summary.cycle_count,
                uptime_seconds=report.metrics_summary.uptime_seconds,
                memory_entries_count=report.metrics_summary.memory_entries_count,
                learning_effectiveness=report.metrics_summary.learning_effectiveness,
                adaptation_rate=report.metrics_summary.adaptation_rate,
                decision_success_rate=report.metrics_summary.decision_success_rate,
                error_count=report.metrics_summary.error_count,
                integrity_score=report.metrics_summary.integrity_score,
                energy_level=report.metrics_summary.energy_level,
                action_count=report.metrics_summary.action_count,
                event_processing_rate=report.metrics_summary.event_processing_rate,
                state_change_frequency=report.metrics_summary.state_change_frequency,
            ),
            behavior_patterns=[
                BehaviorPatternResponse(
                    pattern_type=p.pattern_type,
                    description=p.description,
                    frequency=p.frequency,
                    impact_score=p.impact_score,
                    first_observed=p.first_observed,
                    last_observed=p.last_observed,
                    metadata=p.metadata,
                )
                for p in report.behavior_patterns
            ],
            trends=report.trends,
            anomalies=report.anomalies,
            recommendations=report.recommendations,
        )

    except Exception as e:
        logger.error(f"Ошибка при анализе логов: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка анализа: {str(e)}")


@app.get("/observe/snapshots", response_model=ObservationReportResponse)
async def observe_from_snapshots(
    snapshot_dir: str = Query("data/snapshots", description="Директория с файлами снимков"),
    limit: Optional[int] = Query(None, description="Ограничение количества снимков для анализа")
):
    """
    Выполнить наблюдение на основе снимков состояния системы.

    - **snapshot_dir**: Директория с файлами снимков
    - **limit**: Максимальное количество снимков для анализа
    """
    try:
        snapshot_path = Path(snapshot_dir)
        if not snapshot_path.exists():
            raise HTTPException(status_code=404, detail=f"Директория {snapshot_dir} не найдена")

        # Находим файлы снимков
        snapshot_files = list(snapshot_path.glob('*.json'))
        if not snapshot_files:
            raise HTTPException(status_code=404, detail=f"Файлы снимков не найдены в {snapshot_dir}")

        # Сортируем по времени модификации
        snapshot_files.sort(key=lambda x: x.stat().st_mtime)

        # Применяем ограничение
        if limit:
            snapshot_files = snapshot_files[-limit:]

        if not snapshot_files:
            raise HTTPException(status_code=400, detail="Нет подходящих файлов снимков")

        report = observer.observe_from_snapshots(snapshot_files)

        # Преобразуем в Pydantic модель
        return ObservationReportResponse(
            observation_period=report.observation_period,
            metrics_summary=MetricsResponse(
                timestamp=report.metrics_summary.timestamp,
                cycle_count=report.metrics_summary.cycle_count,
                uptime_seconds=report.metrics_summary.uptime_seconds,
                memory_entries_count=report.metrics_summary.memory_entries_count,
                learning_effectiveness=report.metrics_summary.learning_effectiveness,
                adaptation_rate=report.metrics_summary.adaptation_rate,
                decision_success_rate=report.metrics_summary.decision_success_rate,
                error_count=report.metrics_summary.error_count,
                integrity_score=report.metrics_summary.integrity_score,
                energy_level=report.metrics_summary.energy_level,
                action_count=report.metrics_summary.action_count,
                event_processing_rate=report.metrics_summary.event_processing_rate,
                state_change_frequency=report.metrics_summary.state_change_frequency,
            ),
            behavior_patterns=[
                BehaviorPatternResponse(
                    pattern_type=p.pattern_type,
                    description=p.description,
                    frequency=p.frequency,
                    impact_score=p.impact_score,
                    first_observed=p.first_observed,
                    last_observed=p.last_observed,
                    metadata=p.metadata,
                )
                for p in report.behavior_patterns
            ],
            trends=report.trends,
            anomalies=report.anomalies,
            recommendations=report.recommendations,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при анализе снимков: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка анализа: {str(e)}")


@app.get("/metrics/current", response_model=MetricsResponse)
async def get_current_metrics():
    """Получить текущие метрики системы из последнего наблюдения."""
    try:
        if not observer.observation_history:
            # Выполняем быстрое наблюдение за последним часом
            report = observer.observe_from_logs(time.time() - 3600, time.time())
        else:
            report = observer.observation_history[-1]

        return MetricsResponse(
            timestamp=report.metrics_summary.timestamp,
            cycle_count=report.metrics_summary.cycle_count,
            uptime_seconds=report.metrics_summary.uptime_seconds,
            memory_entries_count=report.metrics_summary.memory_entries_count,
            learning_effectiveness=report.metrics_summary.learning_effectiveness,
            adaptation_rate=report.metrics_summary.adaptation_rate,
            decision_success_rate=report.metrics_summary.decision_success_rate,
            error_count=report.metrics_summary.error_count,
            integrity_score=report.metrics_summary.integrity_score,
            energy_level=report.metrics_summary.energy_level,
            action_count=report.metrics_summary.action_count,
            event_processing_rate=report.metrics_summary.event_processing_rate,
            state_change_frequency=report.metrics_summary.state_change_frequency,
        )

    except Exception as e:
        logger.error(f"Ошибка при получении метрик: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения метрик: {str(e)}")


@app.get("/patterns", response_model=List[BehaviorPatternResponse])
async def get_behavior_patterns():
    """Получить текущие паттерны поведения системы."""
    try:
        if not observer.observation_history:
            raise HTTPException(status_code=404, detail="История наблюдений пуста")

        latest_report = observer.observation_history[-1]

        return [
            BehaviorPatternResponse(
                pattern_type=p.pattern_type,
                description=p.description,
                frequency=p.frequency,
                impact_score=p.impact_score,
                first_observed=p.first_observed,
                last_observed=p.last_observed,
                metadata=p.metadata,
            )
            for p in latest_report.behavior_patterns
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении паттернов: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения паттернов: {str(e)}")


@app.get("/history/summary")
async def get_history_summary():
    """Получить сводку по истории наблюдений."""
    try:
        summary = observer.get_observation_history_summary()

        if 'error' in summary:
            raise HTTPException(status_code=500, detail=summary['error'])

        return JSONResponse(content=summary)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении истории: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения истории: {str(e)}")


@app.get("/anomalies")
async def get_anomalies():
    """Получить список текущих аномалий."""
    try:
        if not observer.observation_history:
            raise HTTPException(status_code=404, detail="История наблюдений пуста")

        latest_report = observer.observation_history[-1]
        return JSONResponse(content={
            "anomalies": latest_report.anomalies,
            "count": len(latest_report.anomalies),
            "timestamp": latest_report.metrics_summary.timestamp
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении аномалий: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения аномалий: {str(e)}")


@app.get("/recommendations")
async def get_recommendations():
    """Получить текущие рекомендации по улучшению системы."""
    try:
        if not observer.observation_history:
            raise HTTPException(status_code=404, detail="История наблюдений пуста")

        latest_report = observer.observation_history[-1]
        return JSONResponse(content={
            "recommendations": latest_report.recommendations,
            "count": len(latest_report.recommendations),
            "timestamp": latest_report.metrics_summary.timestamp
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении рекомендаций: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения рекомендаций: {str(e)}")


# Обработчик ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Глобальный обработчик исключений."""
    logger.error(f"Необработанная ошибка: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc),
            timestamp=time.time()
        ).dict()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)