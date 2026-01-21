#!/usr/bin/env python3
"""
CLI инструмент для генерации отчетов внешнего наблюдения.

Создает HTML отчеты с визуализациями поведения системы Life.

Использование:
    python generate_report_cli.py --logs-analysis --output report.html
    python generate_report_cli.py --snapshots-analysis --snapshot-dir data/snapshots
    python generate_report_cli.py --summary --report-dir reports/
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import List, Optional

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from src.observability.external_observer import ExternalObserver, ObservationReport
    from src.observability.reporting import ReportGenerator
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Make sure you're running from the project root directory")
    sys.exit(1)


def load_reports_from_directory(report_dir: Path) -> List[ObservationReport]:
    """Загрузить все отчеты из директории."""
    reports = []

    if not report_dir.exists():
        logger.error(f"Report directory does not exist: {report_dir}")
        return reports

    # Ищем JSON файлы отчетов
    json_files = list(report_dir.glob('observation_report_*.json'))

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Преобразуем данные обратно в ObservationReport
            # Это упрощенная версия - в реальности нужна более полная десериализация
            report = create_report_from_dict(data)
            if report:
                reports.append(report)

        except Exception as e:
            logger.warning(f"Failed to load report {json_file}: {e}")

    logger.info(f"Loaded {len(reports)} reports from {report_dir}")
    return reports


def create_report_from_dict(data: dict) -> Optional[ObservationReport]:
    """Создать ObservationReport из словаря. Заглушка для реализации."""
    # В реальной реализации нужно правильно десериализовать все поля
    # Пока возвращаем None для простоты
    return None


def generate_single_report_from_logs(start_time_offset: float, output_path: Optional[Path] = None) -> bool:
    """Сгенерировать отчет на основе логов."""
    logger.info("Generating report from logs...")

    try:
        # Создаем наблюдателя и генератор отчетов
        observer = ExternalObserver()
        generator = ReportGenerator()

        # Выполняем наблюдение
        start_time = time.time() - start_time_offset
        report = observer.observe_from_logs(start_time, time.time())

        # Генерируем HTML отчет
        saved_path = generator.generate_html_report(report, output_path)

        logger.info(f"Report generated successfully: {saved_path}")

        # Краткая сводка
        print("
=== REPORT SUMMARY ==="        print(f"Generated: {saved_path}")
        print(f"Observation period: {start_time_offset/3600:.1f} hours")
        print(f"Major patterns: {len(report.behavior_patterns)}")
        print(f"Anomalies detected: {len(report.anomalies)}")

        return True

    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        return False


def generate_single_report_from_snapshots(snapshot_dir: Path, output_path: Optional[Path] = None) -> bool:
    """Сгенерировать отчет на основе снимков."""
    logger.info(f"Generating report from snapshots in {snapshot_dir}...")

    try:
        # Проверяем наличие снимков
        snapshot_files = list(snapshot_dir.glob('*.json'))
        if not snapshot_files:
            logger.error(f"No snapshot files found in {snapshot_dir}")
            return False

        # Создаем наблюдателя и генератор отчетов
        observer = ExternalObserver()
        generator = ReportGenerator()

        # Выполняем наблюдение
        report = observer.observe_from_snapshots(snapshot_files)

        # Генерируем HTML отчет
        saved_path = generator.generate_html_report(report, output_path)

        logger.info(f"Report generated successfully: {saved_path}")

        # Краткая сводка
        print("
=== REPORT SUMMARY ==="        print(f"Generated: {saved_path}")
        print(f"Snapshots analyzed: {len(snapshot_files)}")
        print(f"Major patterns: {len(report.behavior_patterns)}")
        print(f"Anomalies detected: {len(report.anomalies)}")

        return True

    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        return False


def generate_summary_report(report_dir: Path, output_path: Optional[Path] = None) -> bool:
    """Сгенерировать сводный отчет по нескольким наблюдениям."""
    logger.info(f"Generating summary report from {report_dir}...")

    try:
        # Загружаем отчеты
        reports = load_reports_from_directory(report_dir)

        if not reports:
            logger.error("No valid reports found for summary generation")
            return False

        # Создаем генератор отчетов
        generator = ReportGenerator()

        # Генерируем сводный отчет
        saved_path = generator.generate_summary_report(reports, output_path)

        logger.info(f"Summary report generated successfully: {saved_path}")

        # Краткая сводка
        print("
=== SUMMARY REPORT ==="        print(f"Generated: {saved_path}")
        print(f"Reports analyzed: {len(reports)}")
        print(f"Time span: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(min(r.observation_period[0] for r in reports)))} - {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(max(r.observation_period[1] for r in reports)))}")

        return True

    except Exception as e:
        logger.error(f"Failed to generate summary report: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Generate HTML reports for Life System external observation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate report from recent logs (last hour)
  python generate_report_cli.py --logs-analysis --start-time 3600

  # Generate report from logs for specific period
  python generate_report_cli.py --logs-analysis --start-time 86400 --output my_report.html

  # Generate report from snapshots
  python generate_report_cli.py --snapshots-analysis --snapshot-dir data/snapshots

  # Generate summary report from multiple observation reports
  python generate_report_cli.py --summary --report-dir reports/

  # Specify output directory
  python generate_report_cli.py --logs-analysis --start-time 3600 --output-dir reports/
        """
    )

    parser.add_argument(
        '--logs-analysis',
        action='store_true',
        help='Generate report based on system logs'
    )

    parser.add_argument(
        '--start-time',
        type=float,
        help='Start time offset in seconds from now (for logs analysis)'
    )

    parser.add_argument(
        '--snapshots-analysis',
        action='store_true',
        help='Generate report based on system snapshots'
    )

    parser.add_argument(
        '--snapshot-dir',
        type=Path,
        default=Path('data/snapshots'),
        help='Directory containing snapshot files (default: data/snapshots)'
    )

    parser.add_argument(
        '--summary',
        action='store_true',
        help='Generate summary report from multiple observation reports'
    )

    parser.add_argument(
        '--report-dir',
        type=Path,
        default=Path('reports'),
        help='Directory containing observation reports for summary (default: reports)'
    )

    parser.add_argument(
        '--output', '-o',
        type=Path,
        help='Output path for the generated report'
    )

    parser.add_argument(
        '--output-dir',
        type=Path,
        help='Output directory for the generated report (alternative to --output)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Определяем выходной путь
    output_path = args.output
    if args.output_dir and not output_path:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        if args.logs_analysis:
            output_path = args.output_dir / f'logs_report_{timestamp}.html'
        elif args.snapshots_analysis:
            output_path = args.output_dir / f'snapshots_report_{timestamp}.html'
        elif args.summary:
            output_path = args.output_dir / f'summary_report_{timestamp}.html'

    # Проверяем аргументы
    if args.logs_analysis:
        if args.start_time is None:
            logger.error("--start-time is required for logs analysis")
            return 1
        success = generate_single_report_from_logs(args.start_time, output_path)
    elif args.snapshots_analysis:
        success = generate_single_report_from_snapshots(args.snapshot_dir, output_path)
    elif args.summary:
        success = generate_summary_report(args.report_dir, output_path)
    else:
        parser.print_help()
        return 1

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())