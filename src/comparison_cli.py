#!/usr/bin/env python3
"""
CLI для системы сравнения жизней Life

Позволяет запускать и управлять системой сравнения через командную строку.
"""

import argparse
import json
import sys
import time
from pathlib import Path

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent))

from src.comparison import ComparisonManager, ComparisonAPI
from src.logging_config import setup_logging, get_logger

logger = get_logger(__name__)


def create_instances(manager: ComparisonManager, count: int, prefix: str = "life"):
    """Создать несколько инстансов Life."""
    instances = []

    for i in range(count):
        instance_id = f"{prefix}_{i+1}"
        instance = manager.create_instance(
            instance_id=instance_id,
            tick_interval=1.0,
            snapshot_period=5
        )
        if instance:
            instances.append(instance_id)
            logger.info(f"Created instance: {instance_id}")
        else:
            logger.error(f"Failed to create instance: {instance_id}")

    return instances


def run_comparison(manager: ComparisonManager, instances: list, duration: float):
    """Запустить сравнение инстансов."""
    logger.info(f"Starting comparison for {len(instances)} instances: {instances}")

    # Запускаем все инстансы
    start_results = manager.start_all_instances()
    logger.info(f"Start results: {start_results}")

    # Ждем запуска
    time.sleep(2)

    # Запускаем сбор данных
    comparison_data = []
    def data_callback(data):
        comparison_data.append(data)
        logger.info(f"Collected data from {len(data.get('instances', {}))} instances")

    manager.start_data_collection(callback=data_callback)

    # Ждем указанное время
    logger.info(f"Running comparison for {duration} seconds...")
    time.sleep(duration)

    # Останавливаем сбор данных
    manager.stop_data_collection()

    # Останавливаем все инстансы
    stop_results = manager.stop_all_instances()
    logger.info(f"Stop results: {stop_results}")

    return comparison_data


def print_comparison_summary(data_list):
    """Вывести сводку по результатам сравнения."""
    if not data_list:
        logger.warning("No comparison data available")
        return

    # Берем последние данные
    latest_data = data_list[-1]

    print("\n" + "="*80)
    print("COMPARISON SUMMARY")
    print("="*80)

    instances = latest_data.get('instances', {})
    summary = latest_data.get('summary', {})

    print(f"Total instances: {len(instances)}")
    print(f"Active instances: {summary.get('active_instances', 0)}")
    print(f"Average uptime: {summary.get('avg_uptime', 0):.1f}s")
    print(f"Average energy: {summary.get('avg_energy', 0):.1f}")
    print(f"Average stability: {summary.get('avg_stability', 0):.3f}")
    print(f"Average integrity: {summary.get('avg_integrity', 0):.3f}")
    print(f"Total ticks: {summary.get('total_ticks', 0)}")

    print("\nInstance details:")
    for instance_id, data in instances.items():
        status = data.get('status', {})
        print(f"  {instance_id}: alive={status.get('is_alive')}, uptime={status.get('uptime', 0):.1f}s")


def main():
    parser = argparse.ArgumentParser(description="Life Comparison System CLI")
    parser.add_argument("--instances", type=int, default=3, help="Number of Life instances to create")
    parser.add_argument("--duration", type=float, default=30, help="Comparison duration in seconds")
    parser.add_argument("--prefix", default="life", help="Instance name prefix")
    parser.add_argument("--api", action="store_true", help="Start API server instead of CLI comparison")
    parser.add_argument("--api-host", default="localhost", help="API server host")
    parser.add_argument("--api-port", type=int, default=8001, help="API server port")
    parser.add_argument("--output", type=str, help="Output file for comparison results")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    # Настройка логирования
    setup_logging(verbose=args.verbose)

    if args.api:
        # Запуск API сервера
        logger.info(f"Starting Comparison API on {args.api_host}:{args.api_port}")
        api = ComparisonAPI(host=args.api_host, port=args.api_port)
        api.start_server()
    else:
        # Запуск CLI сравнения
        logger.info("Starting CLI comparison mode")

        # Создаем менеджер
        manager = ComparisonManager()

        # Создаем инстансы
        instances = create_instances(manager, args.instances, args.prefix)

        if not instances:
            logger.error("Failed to create any instances")
            return 1

        # Запускаем сравнение
        comparison_data = run_comparison(manager, instances, args.duration)

        # Выводим результаты
        print_comparison_summary(comparison_data)

        # Сохраняем результаты если указано
        if args.output:
            output_data = {
                'config': {
                    'instances_count': len(instances),
                    'duration': args.duration,
                    'prefix': args.prefix
                },
                'instances': instances,
                'comparison_data': comparison_data
            }

            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Results saved to {args.output}")

        # Очистка
        manager.cleanup_instances(force=True)
        logger.info("Comparison completed")

    return 0


if __name__ == "__main__":
    sys.exit(main())