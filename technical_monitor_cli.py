#!/usr/bin/env python3
"""
CLI инструмент для технического мониторинга системы Life.

Предоставляет командную строку для анализа технических аспектов поведения системы Life,
включая производительность, стабильность, адаптивность и целостность.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

# Добавляем src в путь для импорта
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from technical_monitor import TechnicalBehaviorMonitor

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TechnicalMonitorCLI:
    """CLI инструмент для технического мониторинга."""

    def __init__(self):
        self.monitor = TechnicalBehaviorMonitor()

    def create_parser(self) -> argparse.ArgumentParser:
        """Создать парсер аргументов командной строки."""
        parser = argparse.ArgumentParser(
            description="Technical Monitor CLI для системы Life",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Примеры использования:

  # Анализ файла с данными системы
  python technical_monitor_cli.py analyze --input snapshot.json --output report.json

  # Анализ трендов из нескольких файлов
  python technical_monitor_cli.py trends --input-dir ./metrics --hours 24

  # Создание снимка из живой системы (требует доступа к компонентам)
  python technical_monitor_cli.py snapshot --output snapshot.json
            """
        )

        subparsers = parser.add_subparsers(dest='command', help='Доступные команды')

        # Команда analyze
        analyze_parser = subparsers.add_parser(
            'analyze',
            help='Анализ технических метрик из файла'
        )
        analyze_parser.add_argument(
            '--input', '-i',
            required=True,
            help='Путь к файлу с данными системы'
        )
        analyze_parser.add_argument(
            '--output', '-o',
            help='Путь для сохранения отчета (по умолчанию: stdout)'
        )
        analyze_parser.add_argument(
            '--format',
            choices=['json', 'text'],
            default='text',
            help='Формат вывода (по умолчанию: text)'
        )

        # Команда trends
        trends_parser = subparsers.add_parser(
            'trends',
            help='Анализ трендов из нескольких файлов'
        )
        trends_parser.add_argument(
            '--input-dir', '-d',
            required=True,
            help='Директория с файлами отчетов'
        )
        trends_parser.add_argument(
            '--hours', '-t',
            type=int,
            default=24,
            help='Период анализа в часах (по умолчанию: 24)'
        )
        trends_parser.add_argument(
            '--output', '-o',
            help='Путь для сохранения анализа трендов'
        )

        # Команда snapshot
        snapshot_parser = subparsers.add_parser(
            'snapshot',
            help='Создание снимка состояния системы'
        )
        snapshot_parser.add_argument(
            '--output', '-o',
            required=True,
            help='Путь для сохранения снимка'
        )

        return parser

    def run(self, args: List[str]) -> int:
        """Запустить CLI с заданными аргументами."""
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)

        if not parsed_args.command:
            parser.print_help()
            return 1

        try:
            if parsed_args.command == 'analyze':
                return self._analyze_command(parsed_args)
            elif parsed_args.command == 'trends':
                return self._trends_command(parsed_args)
            elif parsed_args.command == 'snapshot':
                return self._snapshot_command(parsed_args)
            else:
                logger.error(f"Неизвестная команда: {parsed_args.command}")
                return 1

        except Exception as e:
            logger.error(f"Ошибка выполнения команды: {e}")
            return 1

    def _analyze_command(self, args) -> int:
        """Обработать команду analyze."""
        try:
            # Загружаем данные из файла
            with open(args.input, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Создаем mock-объекты из данных
            self_state = self._create_mock_self_state(data.get('self_state', {}))
            memory = self._create_mock_memory(data.get('memory_stats', {}))
            learning_engine = self._create_mock_learning_engine(data.get('learning_params', {}))
            adaptation_manager = self._create_mock_adaptation_manager(data.get('adaptation_params', {}))
            decision_engine = self._create_mock_decision_engine(data.get('decision_history', []))

            # Создаем снимок и анализируем
            snapshot = self.monitor.capture_system_snapshot(
                self_state=self_state,
                memory=memory,
                learning_engine=learning_engine,
                adaptation_manager=adaptation_manager,
                decision_engine=decision_engine
            )

            report = self.monitor.analyze_snapshot(snapshot)

            # Выводим результат
            if args.output:
                self.monitor.save_report(report, args.output)
                logger.info(f"Отчет сохранен в: {args.output}")
            else:
                if args.format == 'json':
                    print(json.dumps({
                        'performance': report.performance,
                        'stability': report.stability,
                        'adaptability': report.adaptability,
                        'integrity': report.integrity,
                        'overall_assessment': report.overall_assessment
                    }, indent=2, ensure_ascii=False))
                else:
                    self._print_text_report(report)

            return 0

        except FileNotFoundError:
            logger.error(f"Файл не найден: {args.input}")
            return 1
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка чтения JSON: {e}")
            return 1
        except Exception as e:
            logger.error(f"Ошибка анализа: {e}")
            return 1

    def _trends_command(self, args) -> int:
        """Обработать команду trends."""
        try:
            input_dir = Path(args.input_dir)
            if not input_dir.exists() or not input_dir.is_dir():
                logger.error(f"Директория не существует: {args.input_dir}")
                return 1

            # Загружаем все отчеты из директории
            report_files = list(input_dir.glob("technical_report_*.json"))
            if not report_files:
                logger.error(f"Не найдено файлов отчетов в директории: {args.input_dir}")
                return 1

            # Сортируем по времени (имя файла содержит timestamp)
            report_files.sort(key=lambda x: x.stat().st_mtime)

            # Загружаем последние отчеты
            for report_file in report_files[-50:]:  # Ограничиваем 50 последними
                try:
                    report = self.monitor.load_report(str(report_file))
                    if report:
                        self.monitor.report_history.append(report)
                except Exception as e:
                    logger.warning(f"Ошибка загрузки отчета {report_file}: {e}")

            if len(self.monitor.report_history) < 2:
                logger.error("Недостаточно данных для анализа трендов")
                return 1

            # Анализируем тренды
            trends = self.monitor.get_trends(hours=args.hours)

            # Выводим результат
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(trends, f, indent=2, ensure_ascii=False)
                logger.info(f"Анализ трендов сохранен в: {args.output}")
            else:
                print("=== АНАЛИЗ ТРЕНДОВ ===")
                print(f"Период: {args.hours} часов")
                print(f"Количество отчетов: {len(self.monitor.report_history)}")
                print()

                for metric, trend_data in trends.items():
                    if metric == 'error':
                        print(f"Ошибка: {trend_data}")
                        continue

                    direction = trend_data.get('direction', 'stable')
                    magnitude = trend_data.get('magnitude', 0.0)

                    direction_text = {
                        'improving': 'улучшается',
                        'declining': 'ухудшается',
                        'stable': 'стабильно'
                    }.get(direction, 'неизвестно')

                    print(f"{metric}: {direction_text} (сила: {magnitude:.2f})")

            return 0

        except Exception as e:
            logger.error(f"Ошибка анализа трендов: {e}")
            return 1

    def _snapshot_command(self, args) -> int:
        """Обработать команду snapshot."""
        logger.error("Команда snapshot требует интеграции с живой системой Life")
        logger.error("Используйте автоматический сбор метрик в runtime loop")
        return 1

    def _create_mock_self_state(self, data: Dict[str, Any]) -> Any:
        """Создать mock-объект self_state."""
        class MockSelfState:
            def __init__(self, data: Dict[str, Any]):
                for key, value in data.items():
                    setattr(self, key, value)

        return MockSelfState(data)

    def _create_mock_memory(self, stats: Dict[str, Any]) -> Any:
        """Создать mock-объект memory."""
        class MockMemory:
            def __init__(self, stats: Dict[str, Any]):
                self._stats = stats

            def get_statistics(self) -> Dict[str, Any]:
                return self._stats

        return MockMemory(stats)

    def _create_mock_learning_engine(self, params: Dict[str, Any]) -> Any:
        """Создать mock-объект learning_engine."""
        class MockLearningEngine:
            def __init__(self, params: Dict[str, Any]):
                self._params = params

            def get_parameters(self) -> Dict[str, Any]:
                return self._params

        return MockLearningEngine(params)

    def _create_mock_adaptation_manager(self, params: Dict[str, Any]) -> Any:
        """Создать mock-объект adaptation_manager."""
        class MockAdaptationManager:
            def __init__(self, params: Dict[str, Any]):
                self._params = params

            def get_parameters(self) -> Dict[str, Any]:
                return self._params

        return MockAdaptationManager(params)

    def _create_mock_decision_engine(self, history: List[Dict[str, Any]]) -> Any:
        """Создать mock-объект decision_engine."""
        class MockDecisionEngine:
            def __init__(self, history: List[Dict[str, Any]]):
                self._history = history

            def get_recent_decisions(self, limit: int = 100) -> List[Dict[str, Any]]:
                return self._history[-limit:] if self._history else []

            def get_statistics(self) -> Dict[str, Any]:
                return {
                    'total_decisions': len(self._history),
                    'average_time': 0.01,
                    'accuracy': 0.8
                }

        return MockDecisionEngine(history)

    def _print_text_report(self, report: Any) -> None:
        """Вывести текстовый отчет."""
        print("=== ТЕХНИЧЕСКИЙ ОТЧЕТ СИСТЕМЫ LIFE ===")
        print(f"Время: {report.timestamp}")
        print()

        print("ПРОИЗВОДИТЕЛЬНОСТЬ:")
        perf = report.performance
        print(f"  Эффективность памяти: {perf.get('memory_efficiency', 0.0):.2f}")
        print(f"  Прогресс обучения: {perf.get('learning_progress', 0.0):.2f}")
        print(f"  Скорость решений: {perf.get('decision_speed', 0.0):.4f}")
        print(f"  Точность решений: {perf.get('decision_accuracy', 0.0):.2f}")
        print(f"  Общая производительность: {perf.get('overall_performance', 0.0):.2f}")
        print()

        print("СТАБИЛЬНОСТЬ:")
        stab = report.stability
        print(f"  Согласованность состояния: {stab.get('state_consistency', 0.0):.2f}")
        print(f"  Предсказуемость поведения: {stab.get('behavior_predictability', 0.0):.2f}")
        print(f"  Стабильность параметров: {stab.get('parameter_stability', 0.0):.2f}")
        print(f"  Общая стабильность: {stab.get('overall_stability', 0.0):.2f}")
        print()

        print("АДАПТИВНОСТЬ:")
        adapt = report.adaptability
        print(f"  Скорость обучения: {adapt.get('learning_rate', 0.0):.2f}")
        print(f"  Скорость адаптации: {adapt.get('adaptation_rate', 0.0):.2f}")
        print(f"  Отклик на изменения: {adapt.get('change_responsiveness', 0.0):.2f}")
        print(f"  Общая адаптивность: {adapt.get('overall_adaptability', 0.0):.2f}")
        print()

        print("ЦЕЛОСТНОСТЬ:")
        integ = report.integrity
        print(f"  Согласованность данных: {integ.get('data_consistency', 0.0):.2f}")
        print(f"  Структурная целостность: {integ.get('structural_integrity', 0.0):.2f}")
        print(f"  Логическая согласованность: {integ.get('logical_coherence', 0.0):.2f}")
        print(f"  Общая целостность: {integ.get('overall_integrity', 0.0):.2f}")
        print()

        print("ОБЩАЯ ОЦЕНКА:")
        assess = report.overall_assessment
        print(f"  Общий балл: {assess.get('overall_score', 0.0):.2f}")
        print(f"  Статус: {assess.get('status', 'unknown')}")


def main() -> int:
    """Главная функция CLI."""
    cli = TechnicalMonitorCLI()
    return cli.run(sys.argv[1:])


if __name__ == '__main__':
    sys.exit(main())