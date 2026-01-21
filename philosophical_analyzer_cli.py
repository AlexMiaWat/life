#!/usr/bin/env python3
"""
CLI инструмент для внешнего философского анализа системы Life.

Использование:
    python philosophical_analyzer_cli.py --snapshot-path /path/to/snapshot.json
    python philosophical_analyzer_cli.py --live-analysis --snapshot-dir /path/to/snapshots
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
    from src.philosophical.external_philosophical_analyzer import ExternalPhilosophicalAnalyzer
except ImportError as e:
    logger.error(f"Failed to import ExternalPhilosophicalAnalyzer: {e}")
    logger.error("Make sure you're running from the project root directory")
    sys.exit(1)


def load_snapshot_from_file(snapshot_path: Path) -> Optional[dict]:
    """Загрузить снимок из файла."""
    try:
        with open(snapshot_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load snapshot from {snapshot_path}: {e}")
        return None


def find_latest_snapshot(snapshot_dir: Path) -> Optional[Path]:
    """Найти последний снимок в директории."""
    try:
        snapshot_files = list(snapshot_dir.glob('*.json'))
        if not snapshot_files:
            return None

        # Сортируем по времени модификации
        snapshot_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return snapshot_files[0]
    except Exception as e:
        logger.error(f"Failed to find latest snapshot in {snapshot_dir}: {e}")
        return None


def create_mock_components_from_snapshot(snapshot_data: dict):
    """Создать mock-компоненты из данных снимка."""
    # Mock SelfState
    class MockSelfState:
        def __init__(self, data):
            for key, value in data.items():
                setattr(self, key, value)

    # Mock Memory
    class MockMemory:
        def __init__(self, stats):
            self._stats = stats

        def get_statistics(self):
            return self._stats

    # Mock LearningEngine
    class MockLearningEngine:
        def __init__(self, params):
            self.learning_params = params
            self.parameter_history = []

    # Mock AdaptationManager
    class MockAdaptationManager:
        def __init__(self, params):
            self.adaptation_params = params

    # Mock DecisionEngine
    class MockDecisionEngine:
        def __init__(self, history):
            self.decision_history = history

    # Извлекаем данные из снимка
    self_state_data = snapshot_data.get('self_state', {})
    memory_stats = snapshot_data.get('memory_stats', {})
    learning_params = snapshot_data.get('learning_params', {})
    adaptation_params = snapshot_data.get('adaptation_params', {})
    decision_history = snapshot_data.get('decision_history', [])

    return (
        MockSelfState(self_state_data),
        MockMemory(memory_stats),
        MockLearningEngine(learning_params),
        MockAdaptationManager(adaptation_params),
        MockDecisionEngine(decision_history)
    )


def analyze_snapshot_file(snapshot_path: Path, output_path: Optional[Path] = None) -> bool:
    """Проанализировать снимок из файла."""
    logger.info(f"Loading snapshot from: {snapshot_path}")

    snapshot_data = load_snapshot_from_file(snapshot_path)
    if snapshot_data is None:
        return False

    try:
        # Создаем компоненты из снимка
        components = create_mock_components_from_snapshot(snapshot_data)
        self_state, memory, learning_engine, adaptation_manager, decision_engine = components

        # Создаем анализатор
        analyzer = ExternalPhilosophicalAnalyzer()

        # Захватываем снимок
        logger.info("Capturing system snapshot...")
        snapshot = analyzer.capture_system_snapshot(
            self_state, memory, learning_engine, adaptation_manager, decision_engine
        )

        # Проводим анализ
        logger.info("Performing philosophical analysis...")
        report = analyzer.analyze_snapshot(snapshot)

        # Сохраняем отчет
        if output_path is None:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            output_path = Path(f'philosophical_analysis_{timestamp}.json')

        saved_path = analyzer.save_report(report, output_path)
        logger.info(f"Analysis complete! Report saved to: {saved_path}")

        # Выводим краткую сводку
        assessment = report.overall_assessment
        if 'overall_score' in assessment:
            score = assessment['overall_score']
            interpretation = assessment.get('assessment', 'unknown')
            print(f"Score: {score:.3f}")
            print(f"Assessment: {interpretation.upper()}")
            print(f"Metrics analyzed: {assessment.get('metrics_count', 0)}")

        return True

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return False


def perform_live_analysis(snapshot_dir: Path, output_path: Optional[Path] = None) -> bool:
    """Выполнить анализ на основе последнего снимка."""
    logger.info(f"Looking for latest snapshot in: {snapshot_dir}")

    latest_snapshot = find_latest_snapshot(snapshot_dir)
    if latest_snapshot is None:
        logger.error(f"No snapshot files found in {snapshot_dir}")
        return False

    logger.info(f"Found latest snapshot: {latest_snapshot}")
    return analyze_snapshot_file(latest_snapshot, output_path)


def show_history_summary():
    """Показать сводку по истории анализов."""
    try:
        analyzer = ExternalPhilosophicalAnalyzer()
        summary = analyzer.get_analysis_history_summary()

        if 'error' in summary:
            logger.error(f"Failed to get history summary: {summary['error']}")
            return False

        print("=== PHILOSOPHICAL ANALYSIS HISTORY SUMMARY ===")
        print(f"Total analyses performed: {summary.get('total_analyses', 0)}")

        if 'average_scores' in summary:
            print("\nAverage Scores:")
            for category, score in summary['average_scores'].items():
                print(".3f")

        if 'recent_trends' in summary:
            print("\nRecent Trends:")
            for category, trend in summary['recent_trends'].items():
                print(f"  {category}: {trend.upper()}")

        return True

    except Exception as e:
        logger.error(f"Failed to show history summary: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="External Philosophical Analysis Tool for Life System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a specific snapshot file
  python philosophical_analyzer_cli.py --snapshot-path data/snapshots/snapshot_001.json

  # Perform live analysis using latest snapshot
  python philosophical_analyzer_cli.py --live-analysis --snapshot-dir data/snapshots

  # Show analysis history summary
  python philosophical_analyzer_cli.py --history-summary

  # Specify output file
  python philosophical_analyzer_cli.py --snapshot-path snapshot.json --output report.json
        """
    )

    parser.add_argument(
        '--snapshot-path',
        type=Path,
        help='Path to snapshot file for analysis'
    )

    parser.add_argument(
        '--live-analysis',
        action='store_true',
        help='Perform live analysis using latest snapshot'
    )

    parser.add_argument(
        '--snapshot-dir',
        type=Path,
        default=Path('data/snapshots'),
        help='Directory containing snapshots (default: data/snapshots)'
    )

    parser.add_argument(
        '--output',
        type=Path,
        help='Output path for analysis report'
    )

    parser.add_argument(
        '--history-summary',
        action='store_true',
        help='Show summary of analysis history'
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
    if args.history_summary:
        success = show_history_summary()
    elif args.live_analysis:
        success = perform_live_analysis(args.snapshot_dir, args.output)
    elif args.snapshot_path:
        success = analyze_snapshot_file(args.snapshot_path, args.output)
    else:
        parser.print_help()
        return 1

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())