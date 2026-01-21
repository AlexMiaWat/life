#!/usr/bin/env python3
"""
CLI инструмент для технического мониторинга системы Life.

Анализирует технические метрики производительности системы на основе логов и снимков
без вмешательства в runtime. Фокусируется исключительно на технических аспектах.

Использование:
    python technical_monitor_cli.py --logs-analysis --start-time 3600
    python technical_monitor_cli.py --snapshots-analysis --snapshot-dir data/snapshots
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Optional

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from src.observability.external_observer import TechnicalBehaviorMonitor
except ImportError as e:
    logger.error(f"Failed to import TechnicalBehaviorMonitor: {e}")
    logger.error("Make sure you're running from the project root directory")
    sys.exit(1)


def analyze_from_logs(start_time_offset: float, end_time: Optional[float] = None,
                     output_path: Optional[Path] = None) -> bool:
    """Проанализировать поведение системы на основе логов."""
    logger.info("Starting log-based analysis...")

    start_time = time.time() - start_time_offset
    if end_time is None:
        end_time = time.time()

    try:
        observer = TechnicalBehaviorMonitor()

        # Выполняем анализ
        logger.info(f"Analyzing logs from {start_time} to {end_time}")
        report = observer.observe_from_logs(start_time, end_time)

        # Сохраняем отчет
        if output_path is None:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            output_path = Path(f'technical_report_{timestamp}.json')

        saved_path = observer.save_report(report, output_path)
        logger.info(f"Analysis complete! Report saved to: {saved_path}")

        # Выводим краткую сводку
        metrics = report.metrics_summary
        print("
=== TECHNICAL MONITORING SUMMARY ==="        print(".2f"        print(".2f"        print(f"Errors detected: {metrics.error_count}")
        print(f"Technical patterns: {len(report.behavior_patterns)}")
        print(f"Anomalies found: {len(report.anomalies)}")
        print(f"Recommendations: {len(report.recommendations)}")

        if report.recommendations:
            print("
Key recommendations:"            for rec in report.recommendations[:3]:  # Показываем первые 3
                print(f"  • {rec}")

        return True

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return False


def analyze_from_snapshots(snapshot_dir: Path, output_path: Optional[Path] = None) -> bool:
    """Проанализировать поведение системы на основе снимков."""
    logger.info(f"Starting snapshot-based analysis from: {snapshot_dir}")

    try:
        # Находим файлы снимков
        snapshot_files = list(snapshot_dir.glob('*.json'))
        if not snapshot_files:
            logger.error(f"No snapshot files found in {snapshot_dir}")
            return False

        # Сортируем по времени модификации (новые сначала)
        snapshot_files.sort(key=lambda x: x.stat().st_mtime)

        logger.info(f"Found {len(snapshot_files)} snapshot files")

        observer = TechnicalBehaviorMonitor()

        # Выполняем анализ
        report = observer.observe_from_snapshots(snapshot_files)

        # Сохраняем отчет
        if output_path is None:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            output_path = Path(f'snapshot_analysis_{timestamp}.json')

        saved_path = observer.save_report(report, output_path)
        logger.info(f"Analysis complete! Report saved to: {saved_path}")

        # Выводим краткую сводку
        metrics = report.metrics_summary
        print("
=== SNAPSHOT ANALYSIS SUMMARY ==="        print(".2f"        print(f"Snapshots analyzed: {len(snapshot_files)}")
        print(f"Technical patterns: {len(report.behavior_patterns)}")
        print(f"Anomalies found: {len(report.anomalies)}")

        return True

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return False


def show_observation_history() -> bool:
    """Показать историю наблюдений."""
    try:
        observer = TechnicalBehaviorMonitor()
        summary = observer.get_observation_history_summary()

        if 'error' in summary:
            logger.error(f"Failed to get history summary: {summary['error']}")
            return False

        print("=== TECHNICAL MONITORING HISTORY SUMMARY ===")
        print(f"Total observations: {summary.get('total_observations', 0)}")

        if 'average_metrics' in summary:
            avg = summary['average_metrics']
            print("
Average Metrics:"            print(".2f"            print(".3f"            print(".2f"            print(f"  Error count: {avg.get('error_count', 0):.1f}")

        if 'recent_trends' in summary:
            print("
Recent Trends:"            for metric, trend in summary['recent_trends'].items():
                print(f"  {metric}: {trend.upper()}")

        if 'observation_period' in summary:
            period = summary['observation_period']
            print("
Observation Period:"            print(f"  From: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(period['earliest']))}")
            print(f"  To: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(period['latest']))}")

        return True

    except Exception as e:
        logger.error(f"Failed to show history summary: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Technical Behavior Monitor for Life System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze recent logs (last hour)
  python technical_monitor_cli.py --logs-analysis --start-time 3600

  # Analyze logs for specific time period
  python technical_monitor_cli.py --logs-analysis --start-time 86400 --end-time $(date +%s)

  # Analyze snapshots from directory
  python technical_monitor_cli.py --snapshots-analysis --snapshot-dir data/snapshots

  # Show observation history
  python technical_monitor_cli.py --history

  # Specify output file
  python technical_monitor_cli.py --logs-analysis --start-time 3600 --output my_report.json
        """
    )

    parser.add_argument(
        '--logs-analysis',
        action='store_true',
        help='Perform analysis based on system logs'
    )

    parser.add_argument(
        '--start-time',
        type=float,
        help='Start time offset in seconds from now (for logs analysis)'
    )

    parser.add_argument(
        '--end-time',
        type=float,
        help='End time as Unix timestamp (optional, defaults to now)'
    )

    parser.add_argument(
        '--snapshots-analysis',
        action='store_true',
        help='Perform analysis based on system snapshots'
    )

    parser.add_argument(
        '--snapshot-dir',
        type=Path,
        default=Path('data/snapshots'),
        help='Directory containing snapshot files (default: data/snapshots)'
    )

    parser.add_argument(
        '--output', '-o',
        type=Path,
        help='Output path for analysis report'
    )

    parser.add_argument(
        '--history',
        action='store_true',
        help='Show summary of observation history'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Проверяем аргументы
    if args.history:
        success = show_observation_history()
    elif args.logs_analysis:
        if args.start_time is None:
            logger.error("--start-time is required for logs analysis")
            return 1
        success = analyze_from_logs(args.start_time, args.end_time, args.output)
    elif args.snapshots_analysis:
        success = analyze_from_snapshots(args.snapshot_dir, args.output)
    else:
        parser.print_help()
        return 1

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())