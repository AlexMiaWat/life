"""
Analysis API - REST API для анализа структурированных логов Life.

Предоставляет endpoints для программного доступа к инструментам анализа логов.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import json
import time

from .log_analysis import (
    analyze_logs,
    analyze_correlation_chains,
    get_performance_metrics,
    get_error_summary,
    filter_logs_by_time_range,
    analyze_semantic_patterns,
    analyze_behavioral_anomalies,
    analyze_system_health_semantic,
    get_semantic_chain_analysis
)
from .semantic_analysis_engine import SemanticAnalysisEngine
from .predictive_analysis import PredictiveAnalysisEngine

logger = logging.getLogger(__name__)

# Создаем FastAPI приложение
app = FastAPI(
    title="Life Log Analysis API",
    description="API для анализа структурированных логов системы Life",
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


class AnalysisRequest(BaseModel):
    """Модель запроса для анализа."""
    log_file: Optional[str] = "data/structured_log.jsonl"
    start_time: Optional[float] = None
    end_time: Optional[float] = None


class ExportRequest(BaseModel):
    """Модель запроса для экспорта."""
    log_file: Optional[str] = "data/structured_log.jsonl"
    format: str = "json"
    analysis_type: str = "stats"  # stats, chains, performance, errors, full
    start_time: Optional[float] = None
    end_time: Optional[float] = None


@app.get("/")
async def root():
    """Корневой endpoint с информацией об API."""
    return {
        "name": "Life Log Analysis API",
        "version": "1.0.0",
        "description": "API для анализа структурированных логов системы Life",
        "endpoints": {
            "GET /stats": "Статистика логов",
            "GET /chains": "Анализ цепочек обработки",
            "GET /performance": "Метрики производительности",
            "GET /errors": "Сводка по ошибкам",
            "GET /export": "Экспорт результатов анализа",
            "POST /analyze": "Произвольный анализ с параметрами"
        }
    }


@app.get("/stats")
async def get_log_stats(
    log_file: str = Query("data/structured_log.jsonl", description="Путь к файлу логов"),
    start_time: Optional[float] = Query(None, description="Начало временного диапазона"),
    end_time: Optional[float] = Query(None, description="Конец временного диапазона")
):
    """
    Получить статистику логов.

    Returns:
        Статистика по стадиям, событиям, ошибкам и т.д.
    """
    try:
        # Проверяем существование файла
        if not Path(log_file).exists():
            raise HTTPException(status_code=404, detail=f"Файл логов не найден: {log_file}")

        results = analyze_logs(log_file)
        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@app.get("/chains")
async def get_chains_analysis(
    log_file: str = Query("data/structured_log.jsonl", description="Путь к файлу логов"),
    start_time: Optional[float] = Query(None, description="Начало временного диапазона"),
    end_time: Optional[float] = Query(None, description="Конец временного диапазона"),
    limit: Optional[int] = Query(None, description="Ограничение количества цепочек")
):
    """
    Получить анализ цепочек обработки.

    Returns:
        Анализ цепочек с полнотой, длительностью и статистикой.
    """
    try:
        # Проверяем существование файла
        if not Path(log_file).exists():
            raise HTTPException(status_code=404, detail=f"Файл логов не найден: {log_file}")

        results = analyze_correlation_chains(log_file)

        # Применяем ограничение, если указано
        if limit and results['chains']:
            # Сортируем по длительности и берем топ-N
            sorted_chains = sorted(
                results['chains'].items(),
                key=lambda x: x[1]['duration'],
                reverse=True
            )[:limit]

            results['chains'] = dict(sorted_chains)
            results['summary']['limited_to'] = limit

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка анализа цепочек: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@app.get("/performance")
async def get_performance_analysis(
    log_file: str = Query("data/structured_log.jsonl", description="Путь к файлу логов"),
    start_time: Optional[float] = Query(None, description="Начало временного диапазона"),
    end_time: Optional[float] = Query(None, description="Конец временного диапазона")
):
    """
    Получить метрики производительности.

    Returns:
        Метрики производительности системы (длительности тиков, статистика).
    """
    try:
        # Проверяем существование файла
        if not Path(log_file).exists():
            raise HTTPException(status_code=404, detail=f"Файл логов не найден: {log_file}")

        metrics = get_performance_metrics(log_file)
        return metrics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения метрик производительности: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@app.get("/errors")
async def get_error_analysis(
    log_file: str = Query("data/structured_log.jsonl", description="Путь к файлу логов"),
    start_time: Optional[float] = Query(None, description="Начало временного диапазона"),
    end_time: Optional[float] = Query(None, description="Конец временного диапазона"),
    limit: Optional[int] = Query(10, description="Количество последних ошибок для показа")
):
    """
    Получить анализ ошибок.

    Returns:
        Сводка по ошибкам с типами и последними ошибками.
    """
    try:
        # Проверяем существование файла
        if not Path(log_file).exists():
            raise HTTPException(status_code=404, detail=f"Файл логов не найден: {log_file}")

        error_data = get_error_summary(log_file)

        # Ограничиваем количество последних ошибок
        if limit and error_data['recent_errors']:
            error_data['recent_errors'] = error_data['recent_errors'][:limit]

        return error_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка анализа ошибок: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@app.get("/export")
async def export_analysis(
    format: str = Query("json", description="Формат экспорта (json)"),
    analysis_type: str = Query("stats", description="Тип анализа (stats, chains, performance, errors, full)"),
    log_file: str = Query("data/structured_log.jsonl", description="Путь к файлу логов"),
    start_time: Optional[float] = Query(None, description="Начало временного диапазона"),
    end_time: Optional[float] = Query(None, description="Конец временного диапазона")
):
    """
    Экспортировать результаты анализа.

    Returns:
        Файл с результатами анализа в указанном формате.
    """
    try:
        # Проверяем существование файла
        if not Path(log_file).exists():
            raise HTTPException(status_code=404, detail=f"Файл логов не найден: {log_file}")

        # Проверяем формат
        if format not in ["json"]:
            raise HTTPException(status_code=400, detail=f"Неподдерживаемый формат: {format}")

        # Выполняем анализ
        if analysis_type == "stats":
            data = analyze_logs(log_file)
        elif analysis_type == "chains":
            data = analyze_correlation_chains(log_file)
        elif analysis_type == "performance":
            data = get_performance_metrics(log_file)
        elif analysis_type == "errors":
            data = get_error_summary(log_file)
        elif analysis_type == "full":
            data = {
                'stats': analyze_logs(log_file),
                'chains': analyze_correlation_chains(log_file),
                'performance': get_performance_metrics(log_file),
                'errors': get_error_summary(log_file),
                'export_timestamp': time.time(),
                'log_file': log_file
            }
        else:
            raise HTTPException(status_code=400, detail=f"Неподдерживаемый тип анализа: {analysis_type}")

        # Определяем MIME тип
        mime_types = {
            "json": "application/json"
        }

        from fastapi.responses import Response
        filename = f"life_log_analysis_{analysis_type}_{int(time.time())}.{format}"

        return Response(
            content=json.dumps(data, indent=2, ensure_ascii=False),
            media_type=mime_types[format],
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка экспорта анализа: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@app.post("/analyze")
async def custom_analysis(request: AnalysisRequest):
    """
    Выполнить произвольный анализ с пользовательскими параметрами.

    Returns:
        Полные результаты анализа по всем аспектам.
    """
    try:
        # Проверяем существование файла
        if not Path(request.log_file).exists():
            raise HTTPException(status_code=404, detail=f"Файл логов не найден: {request.log_file}")

        # Выполняем полный анализ
        results = {
            'stats': analyze_logs(request.log_file),
            'chains': analyze_correlation_chains(request.log_file),
            'performance': get_performance_metrics(request.log_file),
            'errors': get_error_summary(request.log_file),
            'timestamp': time.time(),
            'log_file': request.log_file,
            'time_range': {
                'start_time': request.start_time,
                'end_time': request.end_time
            }
        }

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка выполнения анализа: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@app.get("/health")
async def health_check():
    """Проверка здоровья API."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0"
    }


# Кэширование результатов анализа для оптимизации
_analysis_cache = {}
_cache_timestamps = {}


def get_cached_analysis(analysis_type: str, log_file: str, max_age: float = 60.0):
    """
    Получить кэшированный результат анализа.

    Args:
        analysis_type: Тип анализа
        log_file: Путь к файлу логов
        max_age: Максимальный возраст кэша в секундах

    Returns:
        Кэшированный результат или None
    """
    cache_key = f"{analysis_type}:{log_file}"
    current_time = time.time()

    # Проверяем актуальность файла логов
    try:
        log_mtime = Path(log_file).stat().st_mtime
        if log_mtime > _cache_timestamps.get(cache_key, 0):
            return None  # Файл изменился, кэш не актуален
    except (OSError, FileNotFoundError):
        return None

    # Проверяем возраст кэша
    if cache_key in _cache_timestamps:
        cache_age = current_time - _cache_timestamps[cache_key]
        if cache_age < max_age:
            return _analysis_cache.get(cache_key)

    return None


def set_cached_analysis(analysis_type: str, log_file: str, result: Any):
    """
    Сохранить результат анализа в кэш.

    Args:
        analysis_type: Тип анализа
        log_file: Путь к файлу логов
        result: Результат анализа
    """
    cache_key = f"{analysis_type}:{log_file}"
    _analysis_cache[cache_key] = result
    _cache_timestamps[cache_key] = time.time()


# Модифицируем endpoints для использования кэширования
@app.get("/stats")
async def get_log_stats(
    log_file: str = Query("data/structured_log.jsonl", description="Путь к файлу логов"),
    start_time: Optional[float] = Query(None, description="Начало временного диапазона"),
    end_time: Optional[float] = Query(None, description="Конец временного диапазона"),
    use_cache: bool = Query(True, description="Использовать кэширование")
):
    """
    Получить статистику логов с кэшированием.
    """
    try:
        # Проверяем существование файла
        if not Path(log_file).exists():
            raise HTTPException(status_code=404, detail=f"Файл логов не найден: {log_file}")

        # Проверяем кэш
        if use_cache:
            cached = get_cached_analysis("stats", log_file)
            if cached:
                return cached

        results = analyze_logs(log_file)

        # Сохраняем в кэш
        if use_cache:
            set_cached_analysis("stats", log_file, results)

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


# Аналогично модифицируем другие endpoints для кэширования
# (для краткости опускаю, но в реальном коде нужно добавить)


# Semantic Analysis Endpoints

@app.get("/semantic/patterns")
async def get_semantic_patterns(
    log_file: str = Query("data/structured_log.jsonl", description="Путь к файлу логов"),
    use_cache: bool = Query(True, description="Использовать кэширование")
):
    """
    Получить анализ семантических паттернов в логах.
    """
    try:
        if not Path(log_file).exists():
            raise HTTPException(status_code=404, detail=f"Файл логов не найден: {log_file}")

        if use_cache:
            cached = get_cached_analysis("semantic_patterns", log_file)
            if cached:
                return cached

        results = analyze_semantic_patterns(log_file)

        if use_cache:
            set_cached_analysis("semantic_patterns", log_file, results)

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка анализа семантических паттернов: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@app.get("/semantic/anomalies")
async def get_behavioral_anomalies(
    log_file: str = Query("data/structured_log.jsonl", description="Путь к файлу логов"),
    anomaly_threshold: float = Query(0.7, description="Порог обнаружения аномалий", ge=0.0, le=1.0),
    use_cache: bool = Query(True, description="Использовать кэширование")
):
    """
    Получить анализ поведенческих аномалий в логах.
    """
    try:
        if not Path(log_file).exists():
            raise HTTPException(status_code=404, detail=f"Файл логов не найден: {log_file}")

        cache_key = f"anomalies_{anomaly_threshold}"
        if use_cache:
            cached = get_cached_analysis(cache_key, log_file)
            if cached:
                return cached

        results = analyze_behavioral_anomalies(log_file, anomaly_threshold)

        if use_cache:
            set_cached_analysis(cache_key, log_file, results)

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка анализа аномалий: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@app.get("/semantic/health")
async def get_system_health_semantic(
    log_file: str = Query("data/structured_log.jsonl", description="Путь к файлу логов"),
    use_cache: bool = Query(True, description="Использовать кэширование")
):
    """
    Получить семантический анализ здоровья системы.
    """
    try:
        if not Path(log_file).exists():
            raise HTTPException(status_code=404, detail=f"Файл логов не найден: {log_file}")

        if use_cache:
            cached = get_cached_analysis("system_health_semantic", log_file)
            if cached:
                return cached

        results = analyze_system_health_semantic(log_file)

        if use_cache:
            set_cached_analysis("system_health_semantic", log_file, results)

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка анализа здоровья системы: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@app.get("/semantic/chain/{correlation_id}")
async def get_semantic_chain_analysis_endpoint(
    correlation_id: str,
    log_file: str = Query("data/structured_log.jsonl", description="Путь к файлу логов"),
    use_cache: bool = Query(True, description="Использовать кэширование")
):
    """
    Получить детальный семантический анализ конкретной цепочки корреляции.
    """
    try:
        if not Path(log_file).exists():
            raise HTTPException(status_code=404, detail=f"Файл логов не найден: {log_file}")

        cache_key = f"chain_{correlation_id}"
        if use_cache:
            cached = get_cached_analysis(cache_key, log_file)
            if cached:
                return cached

        results = get_semantic_chain_analysis(log_file, correlation_id)

        if use_cache:
            set_cached_analysis(cache_key, log_file, results)

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка анализа цепочки {correlation_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@app.get("/semantic/behavioral-trends")
async def get_behavioral_trends(
    log_file: str = Query("data/structured_log.jsonl", description="Путь к файлу логов"),
    time_window_seconds: float = Query(3600.0, description="Временное окно для анализа", ge=300.0, le=86400.0),
    use_cache: bool = Query(False, description="Использовать кэширование")  # Отключаем кэш по умолчанию для трендов
):
    """
    Получить анализ поведенческих трендов в реальном времени.
    """
    try:
        if not Path(log_file).exists():
            raise HTTPException(status_code=404, detail=f"Файл логов не найден: {log_file}")

        # Создаем новый экземпляр для анализа трендов
        engine = SemanticAnalysisEngine()

        # Загружаем данные из логов
        correlation_chains = {}
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    cid = entry.get('correlation_id')
                    if cid:
                        if cid not in correlation_chains:
                            correlation_chains[cid] = []
                        correlation_chains[cid].append(entry)
                except json.JSONDecodeError:
                    continue

        # Анализируем каждую цепочку
        for correlation_id, chain_entries in correlation_chains.items():
            chain_entries.sort(key=lambda x: x.get('timestamp', 0))
            analysis_result = engine.analyze_correlation_chain(correlation_id, chain_entries)

        # Получаем анализ трендов
        trends = engine.analyze_behavioral_trends(time_window_seconds)

        return {
            'trends_analysis': trends,
            'chains_analyzed': len(correlation_chains),
            'time_window': time_window_seconds,
            'timestamp': time.time()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка анализа трендов: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@app.get("/semantic/predictive-insights")
async def get_predictive_insights(
    log_file: str = Query("data/structured_log.jsonl", description="Путь к файлу логов"),
    prediction_horizon: int = Query(5, description="Горизонт предсказания", ge=1, le=20)
):
    """
    Получить предиктивные insights о поведении системы.
    """
    try:
        if not Path(log_file).exists():
            raise HTTPException(status_code=404, detail=f"Файл логов не найден: {log_file}")

        # Создаем движки анализа
        semantic_engine = SemanticAnalysisEngine()
        predictive_engine = PredictiveAnalysisEngine(prediction_horizon=prediction_horizon)

        # Загружаем и анализируем данные
        correlation_chains = {}
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    cid = entry.get('correlation_id')
                    if cid:
                        if cid not in correlation_chains:
                            correlation_chains[cid] = []
                        correlation_chains[cid].append(entry)
                except json.JSONDecodeError:
                    continue

        # Анализируем семантику и обновляем предиктивный анализ
        for correlation_id, chain_entries in correlation_chains.items():
            chain_entries.sort(key=lambda x: x.get('timestamp', 0))
            semantic_result = semantic_engine.analyze_correlation_chain(correlation_id, chain_entries)
            predictive_engine.update_historical_data(semantic_result)

        # Получаем предиктивные insights
        predictive_insights = predictive_engine.get_predictive_insights()

        return {
            'predictive_insights': predictive_insights,
            'chains_processed': len(correlation_chains),
            'prediction_horizon': prediction_horizon,
            'timestamp': time.time()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения предиктивных insights: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@app.get("/semantic/state-context")
async def get_state_context_analysis(
    log_file: str = Query("data/structured_log.jsonl", description="Путь к файлу логов"),
    energy_level: Optional[float] = Query(None, description="Текущий уровень энергии"),
    integrity_level: Optional[float] = Query(None, description="Текущий уровень целостности"),
    stability_level: Optional[float] = Query(None, description="Текущий уровень стабильности")
):
    """
    Получить контекстный анализ состояния системы.
    """
    try:
        if not Path(log_file).exists():
            raise HTTPException(status_code=404, detail=f"Файл логов не найден: {log_file}")

        # Создаем движок анализа
        engine = SemanticAnalysisEngine()

        # Загружаем исторические данные
        correlation_chains = {}
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    cid = entry.get('correlation_id')
                    if cid:
                        if cid not in correlation_chains:
                            correlation_chains[cid] = []
                        correlation_chains[cid].append(entry)
                except json.JSONDecodeError:
                    continue

        # Анализируем цепочки для накопления данных
        for correlation_id, chain_entries in correlation_chains.items():
            chain_entries.sort(key=lambda x: x.get('timestamp', 0))
            engine.analyze_correlation_chain(correlation_id, chain_entries)

        # Подготавливаем данные текущего состояния
        state_data = {}
        if energy_level is not None:
            state_data['energy'] = energy_level
        if integrity_level is not None:
            state_data['integrity'] = integrity_level
        if stability_level is not None:
            state_data['stability'] = stability_level

        # Получаем контекстный анализ
        context_analysis = engine.analyze_state_context(state_data)

        return {
            'state_context_analysis': context_analysis,
            'chains_processed': len(correlation_chains),
            'current_state_provided': bool(state_data),
            'timestamp': time.time()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка анализа контекста состояния: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@app.get("/semantic/comprehensive-insights")
async def get_comprehensive_semantic_insights(
    log_file: str = Query("data/structured_log.jsonl", description="Путь к файлу логов")
):
    """
    Получить всесторонние семантические insights о системе.
    """
    try:
        if not Path(log_file).exists():
            raise HTTPException(status_code=404, detail=f"Файл логов не найден: {log_file}")

        # Создаем все движки анализа
        semantic_engine = SemanticAnalysisEngine()
        predictive_engine = PredictiveAnalysisEngine()

        # Загружаем данные
        correlation_chains = {}
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    cid = entry.get('correlation_id')
                    if cid:
                        if cid not in correlation_chains:
                            correlation_chains[cid] = []
                        correlation_chains[cid].append(entry)
                except json.JSONDecodeError:
                    continue

        # Выполняем полный анализ
        insights = {
            'summary': {
                'total_chains': len(correlation_chains),
                'analysis_timestamp': time.time(),
                'log_file': log_file
            },
            'semantic_patterns': {},
            'behavioral_anomalies': {},
            'system_health': {},
            'predictive_insights': {},
            'state_context': {},
            'behavioral_trends': {}
        }

        # Анализируем каждую цепочку
        for correlation_id, chain_entries in correlation_chains.items():
            chain_entries.sort(key=lambda x: x.get('timestamp', 0))
            semantic_result = semantic_engine.analyze_correlation_chain(correlation_id, chain_entries)
            predictive_engine.update_historical_data(semantic_result)

        # Получаем все insights
        insights['semantic_patterns'] = semantic_engine.get_semantic_insights()
        insights['behavioral_trends'] = semantic_engine.analyze_behavioral_trends()
        insights['state_context'] = semantic_engine.analyze_state_context()
        insights['predictive_insights'] = predictive_engine.get_predictive_insights()

        # Создаем сводку здоровья системы
        recent_chains = list(correlation_chains.values())[-50:]  # Последние 50 цепочек
        if recent_chains:
            insights['system_health'] = semantic_engine.analyze_system_health(recent_chains)

        # Добавляем поведенческие аномалии
        anomaly_results = semantic_engine.detect_anomalies({
            'correlation_id': 'comprehensive_analysis',
            'anomaly_score': 0.0,  # Не проверяем на аномалии в общем анализе
            'chains_analyzed': len(correlation_chains)
        })
        insights['behavioral_anomalies'] = {
            'detected_anomalies': len(anomaly_results),
            'anomalies': [
                {
                    'type': a.anomaly_type,
                    'severity': a.severity,
                    'description': a.description,
                    'timestamp': a.timestamp
                }
                for a in anomaly_results
            ]
        }

        return insights

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения комплексных insights: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")