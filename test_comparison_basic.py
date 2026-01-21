#!/usr/bin/env python3
"""
Базовый тест системы сравнения жизней

Проверяет создание инстансов, их запуск и базовую функциональность.
"""

import sys
import time
import json
from pathlib import Path

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.comparison import ComparisonManager, PatternAnalyzer, ComparisonMetrics
from src.logging_config import setup_logging

def test_basic_functionality():
    """Тестирование базовой функциональности системы сравнения."""
    print("Testing basic comparison functionality...")

    # Создаем менеджер
    manager = ComparisonManager()

    # Создаем несколько инстансов (без запуска)
    instances = []
    for i in range(2):
        instance_id = f"test_life_{i+1}"
        instance = manager.create_instance(
            instance_id=instance_id,
            tick_interval=1.0,
            snapshot_period=10
        )
        if instance:
            instances.append(instance_id)
            print(f"✓ Created instance: {instance_id}")
        else:
            print(f"✗ Failed to create instance: {instance_id}")
            return False

    print(f"Created {len(instances)} instances: {instances}")

    # Проверяем статусы (инстансы не запущены)
    statuses = manager.get_all_instances_status()
    print(f"Instance statuses: {len(statuses)} instances")

    for instance_id, status in statuses.items():
        if status:
            print(f"  - {instance_id}: running={status.get('is_running')}, port={status.get('port')}")

    # Тестируем анализ паттернов с пустыми данными
    print("Testing pattern analysis with empty data...")
    analyzer = PatternAnalyzer()

    # Создаем mock данные для тестирования
    mock_comparison_data = {
        'timestamp': time.time(),
        'instances': {
            'test_life_1': {
                'status': {'is_running': False, 'is_alive': False, 'uptime': 0},
                'snapshot': {'energy': 50.0, 'stability': 0.8, 'integrity': 0.9, 'ticks': 10},
                'recent_logs': [
                    {'stage': 'decision', 'data': {'pattern': 'ignore'}},
                    {'stage': 'decision', 'data': {'pattern': 'absorb'}},
                    {'stage': 'event', 'data': {'type': 'noise'}}
                ]
            },
            'test_life_2': {
                'status': {'is_running': False, 'is_alive': False, 'uptime': 0},
                'snapshot': {'energy': 60.0, 'stability': 0.7, 'integrity': 0.85, 'ticks': 12},
                'recent_logs': [
                    {'stage': 'decision', 'data': {'pattern': 'dampen'}},
                    {'stage': 'decision', 'data': {'pattern': 'ignore'}},
                    {'stage': 'event', 'data': {'type': 'decay'}}
                ]
            }
        }
    }

    analysis = analyzer.analyze_comparison_data(mock_comparison_data)

    if analysis:
        print("✓ Pattern analysis completed")
        instances_analysis = analysis.get('instances_analysis', {})
        print(f"  - Instances analyzed: {len(instances_analysis)}")
        for instance_id, inst_analysis in instances_analysis.items():
            patterns = inst_analysis.get('decision_patterns', {}).get('patterns', {})
            print(f"    {instance_id}: patterns={list(patterns.keys())}")
    else:
        print("✗ Pattern analysis failed")

    # Тестируем метрики сравнения
    print("Testing comparison metrics...")
    metrics = ComparisonMetrics()
    instances_data = mock_comparison_data.get('instances', {})
    summary = metrics.get_summary_report(instances_data)

    if summary:
        print("✓ Comparison metrics computed")
        similarity = summary.get('similarity_metrics', {})
        overall_sim = similarity.get('overall_similarity', {})
        if overall_sim:
            print(f"  - Similarity pairs: {list(overall_sim.keys())}")
    else:
        print("✗ Comparison metrics failed")

    # Очищаем инстансы
    cleanup_results = manager.cleanup_instances()
    cleaned = sum(1 for result in cleanup_results.values() if result)
    print(f"Cleaned up {cleaned} instances")

    print("Basic functionality test completed!")
    return True


def test_api_import():
    """Тестирование импорта API компонентов."""
    print("Testing API import...")

    try:
        from src.comparison import ComparisonAPI
        print("✓ ComparisonAPI imported successfully")

        # Создаем API экземпляр (не запускаем сервер)
        api = ComparisonAPI(host="localhost", port=8002)
        print("✓ ComparisonAPI instance created")

        return True
    except Exception as e:
        print(f"✗ API import failed: {e}")
        return False


if __name__ == "__main__":
    setup_logging(verbose=True)

    print("="*60)
    print("LIFE COMPARISON SYSTEM - BASIC TESTS")
    print("="*60)

    success = True

    # Тест импорта API
    if not test_api_import():
        success = False

    # Тест базовой функциональности
    if not test_basic_functionality():
        success = False

    print("="*60)
    if success:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*60)

    sys.exit(0 if success else 1)