#!/usr/bin/env python3
"""
Инструмент анализа структурированных логов Life.

Предоставляет командную строку для анализа JSONL логов,
генерируемых StructuredLogger системы Life.

Использование:
    python scripts/analyze_logs.py --help
    python scripts/analyze_logs.py stats
    python scripts/analyze_logs.py chains
    python scripts/analyze_logs.py performance
    python scripts/analyze_logs.py errors
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.observability.log_analysis import (
    analyze_logs,
    analyze_correlation_chains,
    get_performance_metrics,
    get_error_summary,
    filter_logs_by_time_range
)


def print_stats(results: Dict[str, Any]) -> None:
    """Вывод статистики логов."""
    print("=== АНАЛИЗ СТРУКТУРИРОВАННЫХ ЛОГОВ ===")
    print(f"Файл: {results['file_path']}")
    print(f"Всего записей: {results['total_entries']:,}")
    print(f"Корреляционных цепочек: {results['total_correlations']:,}")
    print(f"Ошибок: {results['error_count']:,}")
    print()

    print("Распределение по стадиям:")
    for stage, count in sorted(results['stages'].items(), key=lambda x: x[1], reverse=True):
        percentage = (count / results['total_entries']) * 100 if results['total_entries'] > 0 else 0
        print("20")
    print()

    if results['event_types']:
        print("Типы событий:")
        for event_type, count in sorted(results['event_types'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / sum(results['event_types'].values())) * 100
            print("15")
        print()

    if results['decision_patterns']:
        print("Паттерны решений:")
        for pattern, count in sorted(results['decision_patterns'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / sum(results['decision_patterns'].values())) * 100
            print("15")


def print_chains_analysis(results: Dict[str, Any]) -> None:
    """Вывод анализа цепочек обработки."""
    chains = results['chains']
    summary = results['summary']

    print("=== АНАЛИЗ ЦЕПОЧЕК ОБРАБОТКИ ===")
    print(f"Всего цепочек: {summary['total_chains']:,}")
    print(f"Полных цепочек: {summary['complete_chains']:,}")
    print(f"Неполных цепочек: {summary['incomplete_chains']:,}")
    print(".2%")
    print()

    if summary['total_chains'] > 0:
        print("Статистика длительности:")
        print(".3f")
        print(".3f")
        print(".3f")
        print(".3f")
        print()

    # Показываем топ-10 самых долгих цепочек
    if chains:
        print("Самые долгие цепочки:")
        sorted_chains = sorted(chains.items(), key=lambda x: x[1]['duration'], reverse=True)
        for i, (chain_id, info) in enumerate(sorted_chains[:10], 1):
            print("2")
        print()

    # Показываем примеры полных цепочек
    complete_chains = [(cid, info) for cid, info in chains.items() if info['completeness'] >= 0.8]
    if complete_chains:
        print("Примеры полных цепочек:")
        for chain_id, info in complete_chains[:5]:
            stages_str = ', '.join(info['stages'])
            print("15")


def print_performance_metrics(metrics: Dict[str, Any]) -> None:
    """Вывод метрик производительности."""
    print("=== МЕТРИКИ ПРОИЗВОДИТЕЛЬНОСТИ ===")
    print(f"Всего тиков: {metrics['total_ticks']:,}")

    if metrics['total_ticks'] > 0:
        print(".2f")
        print(".2f")
        print(".2f")
        print(".2f")
        print(".2f")
        print(f"P95 длительность тика: {metrics['p95_tick_duration']*1000:.2f} мс")
        print()

        print("Анализ медленных тиков:")
        print(f"  Тиков > 50мс: {metrics['slow_ticks_50ms']}")
        print(f"  Тиков > 100мс: {metrics['slow_ticks_100ms']}")

        if metrics['total_ticks'] > 0:
            slow_50_pct = (metrics['slow_ticks_50ms'] / metrics['total_ticks']) * 100
            slow_100_pct = (metrics['slow_ticks_100ms'] / metrics['total_ticks']) * 100
            print(".1f")
            print(".1f")


def print_error_summary(error_data: Dict[str, Any]) -> None:
    """Вывод сводки по ошибкам."""
    print("=== СВОДКА ПО ОШИБКАМ ===")
    print(f"Всего ошибок: {error_data['total_errors']:,}")
    print()

    if error_data['error_types']:
        print("Распределение по типам ошибок:")
        for error_type, count in sorted(error_data['error_types'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / error_data['total_errors']) * 100
            print("15")
        print()

    if error_data['recent_errors']:
        print("Последние ошибки:")
        for error in error_data['recent_errors'][:5]:  # Показываем последние 5
            print(f"  Время: {error['timestamp']:.3f}")
            print(f"  Стадия: {error['stage']}")
            print(f"  Тип: {error['error_type']}")
            print(f"  Сообщение: {error['error_message']}")
            if error['correlation_id']:
                print(f"  Цепочка: {error['correlation_id']}")
            print()


def export_json(data: Dict[str, Any], output_file: str) -> None:
    """Экспорт данных в JSON файл."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Результаты экспортированы в: {output_file}")
    except Exception as e:
        print(f"Ошибка экспорта в JSON: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Инструмент анализа структурированных логов Life",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

  # Базовая статистика
  python scripts/analyze_logs.py stats

  # Анализ цепочек обработки
  python scripts/analyze_logs.py chains

  # Метрики производительности
  python scripts/analyze_logs.py performance

  # Сводка по ошибкам
  python scripts/analyze_logs.py errors

  # Анализ конкретного файла
  python scripts/analyze_logs.py stats --log-file data/custom_log.jsonl

  # Экспорт результатов в JSON
  python scripts/analyze_logs.py stats --export results.json

  # Анализ временного диапазона (последние 3600 секунд)
  python scripts/analyze_logs.py stats --since 3600

  # Полный анализ всех аспектов
  python scripts/analyze_logs.py full
        """
    )

    parser.add_argument(
        'command',
        choices=['stats', 'chains', 'performance', 'errors', 'full'],
        help='Команда анализа'
    )

    parser.add_argument(
        '--log-file',
        default='data/structured_log.jsonl',
        help='Путь к файлу логов (default: data/structured_log.jsonl)'
    )

    parser.add_argument(
        '--export',
        help='Экспортировать результаты в JSON файл'
    )

    parser.add_argument(
        '--since',
        type=float,
        help='Анализировать логи за последние N секунд'
    )

    parser.add_argument(
        '--from-time',
        type=float,
        help='Анализировать логи начиная с timestamp'
    )

    parser.add_argument(
        '--to-time',
        type=float,
        help='Анализировать логи до timestamp'
    )

    args = parser.parse_args()

    # Проверяем существование файла логов
    log_path = Path(args.log_file)
    if not log_path.exists():
        print(f"Ошибка: файл логов не найден: {args.log_file}", file=sys.stderr)
        sys.exit(1)

    # Определяем временной диапазон
    end_time = None
    start_time = args.from_time

    if args.since:
        import time
        end_time = time.time()
        start_time = end_time - args.since
    elif args.to_time:
        end_time = args.to_time

    # Фильтруем логи по времени, если нужно
    filtered_logs = None
    if start_time or end_time:
        print(f"Фильтрация логов: start={start_time}, end={end_time}")
        filtered_logs = filter_logs_by_time_range(args.log_file, start_time, end_time)
        print(f"Отфильтровано записей: {len(filtered_logs)}")
        # TODO: Передать filtered_logs в функции анализа
        # Пока что просто игнорируем фильтрацию в анализе

    try:
        if args.command == 'stats':
            results = analyze_logs(args.log_file)
            print_stats(results)
            if args.export:
                export_json(results, args.export)

        elif args.command == 'chains':
            results = analyze_correlation_chains(args.log_file)
            print_chains_analysis(results)
            if args.export:
                export_json(results, args.export)

        elif args.command == 'performance':
            metrics = get_performance_metrics(args.log_file)
            print_performance_metrics(metrics)
            if args.export:
                export_json(metrics, args.export)

        elif args.command == 'errors':
            error_data = get_error_summary(args.log_file)
            print_error_summary(error_data)
            if args.export:
                export_json(error_data, args.export)

        elif args.command == 'full':
            print("=== ПОЛНЫЙ АНАЛИЗ ЛОГОВ ===\n")

            results = analyze_logs(args.log_file)
            print_stats(results)
            print("\n" + "="*50 + "\n")

            chains = analyze_correlation_chains(args.log_file)
            print_chains_analysis(chains)
            print("\n" + "="*50 + "\n")

            metrics = get_performance_metrics(args.log_file)
            print_performance_metrics(metrics)
            print("\n" + "="*50 + "\n")

            errors = get_error_summary(args.log_file)
            print_error_summary(errors)

            if args.export:
                full_results = {
                    'stats': results,
                    'chains': chains,
                    'performance': metrics,
                    'errors': errors
                }
                export_json(full_results, args.export)

    except KeyboardInterrupt:
        print("\nАнализ прерван пользователем", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка анализа: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()