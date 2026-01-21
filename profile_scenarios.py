#!/usr/bin/env python3
"""
Расширенный скрипт для профилирования runtime loop с различными сценариями
"""
import cProfile
import os
import pstats
import sys
import time
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.environment.event_queue import EventQueue
from src.monitor.console import monitor
from src.runtime.loop import run_loop
from src.state.self_state import SelfState


def create_test_scenario(scenario_name, description="", **kwargs):
    """Создать конфигурацию для тестового сценария"""
    base_config = {
        "tick_interval": 0.01,  # очень быстрый тик
        "snapshot_period": 100,  # snapshot каждые 100 тиков
        "stop_event": None,
        "event_queue": EventQueue(),
        "disable_weakness_penalty": False,
        "disable_structured_logging": False,
        "disable_learning": True,  # по умолчанию отключено
        "disable_adaptation": True,  # по умолчанию отключено
        "disable_clarity_moments": True,
        "log_flush_period_ticks": 10,
        "enable_profiling": False,  # False, потому что мы профилируем снаружи
    }

    # Обновляем базовую конфигурацию
    base_config.update(kwargs)

    return {
        "name": scenario_name,
        "config": base_config,
        "description": description or f"Сценарий: {scenario_name}"
    }


def profile_scenario(scenario):
    """Профилирование одного сценария"""
    print(f"\n=== Запуск сценария: {scenario['name']} ===")
    print(f"Описание: {scenario['description']}")

    # Настройка SelfState
    self_state = SelfState()

    # Настройка EventQueue
    event_queue = EventQueue()

    # Создание профиля
    profiler = cProfile.Profile()

    config = scenario['config']
    config['event_queue'] = event_queue

    try:
        # Запуск профилирования
        profiler.enable()

        # Запуск runtime loop на короткое время
        import threading

        stop_event = threading.Event()
        config['stop_event'] = stop_event

        # Запуск в отдельном потоке
        loop_thread = threading.Thread(
            target=run_loop,
            args=(
                self_state,
                monitor,
                config.get('tick_interval', 1.0),
                config.get('snapshot_period', 10),
                config.get('stop_event'),
                config.get('event_queue'),
                config.get('disable_weakness_penalty', False),
                config.get('disable_structured_logging', False),
                config.get('disable_learning', False),
                config.get('disable_adaptation', False),
                config.get('disable_clarity_moments', True),
                config.get('log_flush_period_ticks', 10),
                config.get('enable_profiling', False),
            ),
            daemon=True,
        )

        loop_thread.start()

        # Ждем 2 секунд (меньше времени для более точного профилирования)
        time.sleep(2)

        # Останавливаем
        stop_event.set()
        loop_thread.join(timeout=1)

    finally:
        # Останавливаем профилирование
        profiler.disable()

        # Сохраняем результаты
        os.makedirs("data", exist_ok=True)
        timestamp = int(time.time())
        profile_filename = f"data/runtime_loop_profile_{scenario['name']}_{timestamp}.prof"
        profiler.dump_stats(profile_filename)

        # Анализируем результаты
        stats = pstats.Stats(profiler, stream=sys.stdout)
        stats.sort_stats("cumulative")

        print(f"\nПрофиль сохранен в {profile_filename}")

        # Краткая статистика
        total_time = stats.total_tt
        total_calls = stats.total_calls

        print(".4f")
        print(f"Всего вызовов функций: {total_calls}")

        # Топ функций по времени
        print("\n=== Топ 10 функций по cumulative time ===")
        stats.print_stats(10)

        # Сохраняем метрики для сравнения
        metrics = {
            "scenario": scenario['name'],
            "total_time": total_time,
            "total_calls": total_calls,
            "timestamp": timestamp,
            "profile_file": profile_filename
        }

        return metrics


def run_performance_comparison():
    """Запуск сравнительного профилирования различных сценариев"""

    scenarios = [
        create_test_scenario(
            "baseline_minimal",
            disable_structured_logging=True,
            disable_learning=True,
            disable_adaptation=True,
            log_flush_period_ticks=1000,  # редко
            snapshot_period=1000,  # редко
            description="Базовый сценарий с минимальным логированием"
        ),

        create_test_scenario(
            "with_structured_logging",
            disable_structured_logging=False,
            disable_learning=True,
            disable_adaptation=True,
            log_flush_period_ticks=10,
            snapshot_period=100,
            description="С включенным структурированным логированием"
        ),

        create_test_scenario(
            "with_learning",
            disable_structured_logging=True,
            disable_learning=False,
            disable_adaptation=True,
            log_flush_period_ticks=1000,
            snapshot_period=1000,
            description="С включенным Learning Engine"
        ),

        create_test_scenario(
            "with_adaptation",
            disable_structured_logging=True,
            disable_learning=True,
            disable_adaptation=False,
            log_flush_period_ticks=1000,
            snapshot_period=1000,
            description="С включенным Adaptation Manager"
        ),

        create_test_scenario(
            "full_features",
            disable_structured_logging=False,
            disable_learning=False,
            disable_adaptation=False,
            log_flush_period_ticks=10,
            snapshot_period=100,
            description="Полный набор функций"
        ),
    ]

    results = []

    print("🚀 Начало сравнительного профилирования runtime loop")
    print("=" * 60)

    for scenario in scenarios:
        metrics = profile_scenario(scenario)
        results.append(metrics)

        # Небольшая пауза между запусками
        time.sleep(0.5)

    # Сохраняем сводные результаты
    summary_file = f"data/performance_comparison_{int(time.time())}.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📊 Сводные результаты сохранены в {summary_file}")

    # Выводим сравнение
    print("\n" + "="*60)
    print("📈 СРАВНЕНИЕ ПРОИЗВОДИТЕЛЬНОСТИ")
    print("="*60)

    baseline = next(r for r in results if r['scenario'] == 'baseline_minimal')

    print("<12")
    print("-" * 60)

    for result in results:
        if result['scenario'] != 'baseline_minimal':
            slowdown = result['total_time'] / baseline['total_time']
            print("<12")

    print(f"\n🏆 Baseline сценарий: {baseline['scenario']} ({baseline['total_time']:.4f} сек)")


if __name__ == "__main__":
    run_performance_comparison()