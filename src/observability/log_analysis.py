"""
Log Analysis Tools - Инструменты анализа структурированных логов Life.

Предоставляет функции для анализа JSONL логов, генерируемых StructuredLogger.
Включает анализ статистики, цепочек обработки и производительности.
"""

import json
import statistics
from collections import Counter, defaultdict
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def analyze_logs(log_path: str = "data/structured_log.jsonl") -> Dict[str, Any]:
    """
    Анализ структурированных логов Life.

    Args:
        log_path: Путь к файлу с логами

    Returns:
        Словарь с результатами анализа
    """
    log_file = Path(log_path)
    if not log_file.exists():
        logger.warning(f"Файл логов не найден: {log_path}")
        return _empty_analysis_result()

    stages = Counter()
    correlations = defaultdict(list)
    tick_durations = []
    event_types = Counter()
    decision_patterns = Counter()
    error_count = 0
    total_entries = 0

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    entry = json.loads(line.strip())
                    total_entries += 1

                    # Подсчет стадий
                    stage = entry.get('stage', 'unknown')
                    stages[stage] += 1

                    # Группировка по correlation_id
                    if 'correlation_id' in entry:
                        correlations[entry['correlation_id']].append(entry)

                    # Анализ событий
                    if stage == 'event':
                        event_type = entry.get('event_type', 'unknown')
                        event_types[event_type] += 1

                    # Анализ решений (если есть в данных)
                    if stage == 'decision' and 'data' in entry:
                        pattern = entry['data'].get('pattern')
                        if pattern:
                            decision_patterns[pattern] += 1

                    # Подсчет ошибок
                    if stage.startswith('error_'):
                        error_count += 1

                except json.JSONDecodeError as e:
                    logger.warning(f"Ошибка парсинга строки {line_num}: {e}")
                    continue

    except Exception as e:
        logger.error(f"Ошибка чтения файла логов: {e}")
        return _empty_analysis_result()

    return {
        'total_entries': total_entries,
        'stages': dict(stages),
        'total_correlations': len(correlations),
        'event_types': dict(event_types),
        'decision_patterns': dict(decision_patterns),
        'error_count': error_count,
        'file_path': str(log_path),
        'analysis_timestamp': json.dumps(None)  # Will be serialized as current time
    }


def analyze_correlation_chains(log_path: str = "data/structured_log.jsonl") -> Dict[str, Any]:
    """
    Анализ полных цепочек обработки по correlation_id.

    Args:
        log_path: Путь к файлу с логами

    Returns:
        Словарь с анализом цепочек
    """
    log_file = Path(log_path)
    if not log_file.exists():
        logger.warning(f"Файл логов не найден: {log_path}")
        return {'chains': {}, 'summary': {}}

    chains = defaultdict(list)

    # Сбор всех записей по correlation_id
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if 'correlation_id' in entry:
                        chains[entry['correlation_id']].append(entry)
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        logger.error(f"Ошибка чтения файла логов: {e}")
        return {'chains': {}, 'summary': {}}

    # Сортировка записей в каждой цепочке по времени
    for chain_id, entries in chains.items():
        chains[chain_id] = sorted(entries, key=lambda x: x['timestamp'])

    # Анализ цепочек
    chain_analysis = {}
    stage_order = ['event', 'meaning', 'decision', 'action', 'feedback']

    for chain_id, entries in chains.items():
        if not entries:
            continue

        # Проверка полноты цепочки
        stages_present = set(entry['stage'] for entry in entries)
        completeness = len(stages_present.intersection(stage_order)) / len(stage_order)

        # Вычисление времени обработки цепочки
        start_time = min(entry['timestamp'] for entry in entries)
        end_time = max(entry['timestamp'] for entry in entries)
        duration = end_time - start_time

        # Определение типа события
        event_type = 'unknown'
        for entry in entries:
            if entry['stage'] == 'event':
                event_type = entry.get('event_type', 'unknown')
                break

        chain_analysis[chain_id] = {
            'stages': sorted(stages_present),
            'completeness': completeness,
            'duration': duration,
            'entry_count': len(entries),
            'event_type': event_type,
            'start_time': start_time,
            'end_time': end_time
        }

    # Сводная статистика
    if chain_analysis:
        durations = [info['duration'] for info in chain_analysis.values() if info['duration'] > 0]
        completeness_values = [info['completeness'] for info in chain_analysis.values()]

        summary = {
            'total_chains': len(chain_analysis),
            'avg_duration': statistics.mean(durations) if durations else 0,
            'median_duration': statistics.median(durations) if durations else 0,
            'min_duration': min(durations) if durations else 0,
            'max_duration': max(durations) if durations else 0,
            'avg_completeness': statistics.mean(completeness_values) if completeness_values else 0,
            'complete_chains': sum(1 for info in chain_analysis.values() if info['completeness'] >= 0.8),
            'incomplete_chains': sum(1 for info in chain_analysis.values() if info['completeness'] < 0.8)
        }
    else:
        summary = {
            'total_chains': 0,
            'avg_duration': 0,
            'median_duration': 0,
            'min_duration': 0,
            'max_duration': 0,
            'avg_completeness': 0,
            'complete_chains': 0,
            'incomplete_chains': 0
        }

    return {
        'chains': chain_analysis,
        'summary': summary
    }


def get_performance_metrics(log_path: str = "data/structured_log.jsonl") -> Dict[str, Any]:
    """
    Извлечение метрик производительности из логов.

    Args:
        log_path: Путь к файлу с логами

    Returns:
        Метрики производительности
    """
    log_file = Path(log_path)
    if not log_file.exists():
        return _empty_performance_metrics()

    tick_starts = {}
    tick_durations = []
    total_ticks = 0

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    stage = entry.get('stage')

                    if stage == 'tick_start':
                        tick_num = entry.get('tick_number')
                        if tick_num is not None:
                            tick_starts[tick_num] = entry['timestamp']
                            total_ticks = max(total_ticks, tick_num)

                    elif stage == 'tick_end':
                        tick_num = entry.get('tick_number')
                        if tick_num in tick_starts:
                            duration = entry['timestamp'] - tick_starts[tick_num]
                            tick_durations.append(duration)

                except json.JSONDecodeError:
                    continue

    except Exception as e:
        logger.error(f"Ошибка чтения файла логов: {e}")
        return _empty_performance_metrics()

    if tick_durations:
        return {
            'total_ticks': len(tick_durations),
            'avg_tick_duration': statistics.mean(tick_durations),
            'median_tick_duration': statistics.median(tick_durations),
            'min_tick_duration': min(tick_durations),
            'max_tick_duration': max(tick_durations),
            'p95_tick_duration': statistics.quantiles(tick_durations, n=20)[18] if len(tick_durations) >= 20 else max(tick_durations),
            'slow_ticks_50ms': sum(1 for d in tick_durations if d > 0.050),  # > 50ms
            'slow_ticks_100ms': sum(1 for d in tick_durations if d > 0.100),  # > 100ms
        }
    else:
        return _empty_performance_metrics()


def filter_logs_by_time_range(
    log_path: str = "data/structured_log.jsonl",
    start_time: Optional[float] = None,
    end_time: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Фильтрация логов по временному диапазону.

    Args:
        log_path: Путь к файлу с логами
        start_time: Начало диапазона (timestamp)
        end_time: Конец диапазона (timestamp)

    Returns:
        Список отфильтрованных записей
    """
    log_file = Path(log_path)
    if not log_file.exists():
        return []

    filtered_entries = []

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    timestamp = entry.get('timestamp')

                    if timestamp is not None:
                        if start_time and timestamp < start_time:
                            continue
                        if end_time and timestamp > end_time:
                            continue

                        filtered_entries.append(entry)

                except json.JSONDecodeError:
                    continue

    except Exception as e:
        logger.error(f"Ошибка чтения файла логов: {e}")
        return []

    return filtered_entries


def get_error_summary(log_path: str = "data/structured_log.jsonl") -> Dict[str, Any]:
    """
    Получение сводки по ошибкам в логах.

    Args:
        log_path: Путь к файлу с логами

    Returns:
        Сводка по ошибкам
    """
    log_file = Path(log_path)
    if not log_file.exists():
        return {'total_errors': 0, 'error_types': {}, 'recent_errors': []}

    error_types = Counter()
    recent_errors = []

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    stage = entry.get('stage', '')

                    if stage.startswith('error_'):
                        error_type = entry.get('error_type', 'unknown')
                        error_types[error_type] += 1

                        # Сохраняем последние 10 ошибок
                        if len(recent_errors) < 10:
                            recent_errors.append({
                                'timestamp': entry.get('timestamp'),
                                'stage': stage,
                                'error_type': error_type,
                                'error_message': entry.get('error_message', ''),
                                'correlation_id': entry.get('correlation_id')
                            })

                except json.JSONDecodeError:
                    continue

    except Exception as e:
        logger.error(f"Ошибка чтения файла логов: {e}")
        return {'total_errors': 0, 'error_types': {}, 'recent_errors': []}

    # Сортируем недавние ошибки по времени (новые сверху)
    recent_errors.sort(key=lambda x: x['timestamp'] or 0, reverse=True)

    return {
        'total_errors': sum(error_types.values()),
        'error_types': dict(error_types),
        'recent_errors': recent_errors
    }


def _empty_analysis_result() -> Dict[str, Any]:
    """Возвращает пустой результат анализа."""
    return {
        'total_entries': 0,
        'stages': {},
        'total_correlations': 0,
        'event_types': {},
        'decision_patterns': {},
        'error_count': 0,
        'file_path': '',
        'analysis_timestamp': None
    }


def _empty_performance_metrics() -> Dict[str, Any]:
    """Возвращает пустые метрики производительности."""
    return {
        'total_ticks': 0,
        'avg_tick_duration': 0,
        'median_tick_duration': 0,
        'min_tick_duration': 0,
        'max_tick_duration': 0,
        'p95_tick_duration': 0,
        'slow_ticks_50ms': 0,
        'slow_ticks_100ms': 0,
    }