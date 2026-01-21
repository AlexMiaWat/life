#!/usr/bin/env python3
"""
Скрипт для инициализации baseline значений производительности.
Используется при первом запуске performance тестов.
"""

import os
import json
from pathlib import Path

# Добавляем src в путь
project_root = Path(__file__).parent
import sys
sys.path.insert(0, str(project_root / "src"))

from src.test.performance_baseline import PerformanceBaseline

def init_baseline():
    """Инициализировать baseline значения производительности"""
    print("🚀 Инициализация baseline значений производительности...")

    # Создаем директорию data если не существует
    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True)

    baseline_file = data_dir / "performance_baseline.json"

    if baseline_file.exists():
        print(f"✅ Baseline файл уже существует: {baseline_file}")
        return True

    try:
        # Создаем базовые значения по умолчанию
        default_baseline = {
            "metadata": {
                "created_at": "2026-01-21T00:00:00Z",
                "python_version": "3.11",
                "platform": "CI",
                "description": "Initial baseline for CI pipeline"
            },
            "benchmarks": {
                "test_memory_append_performance": {
                    "mean": 0.001,
                    "std": 0.0001,
                    "min": 0.0008,
                    "max": 0.0015,
                    "threshold": 0.15
                },
                "test_memory_iteration_performance": {
                    "mean": 0.005,
                    "std": 0.0005,
                    "min": 0.004,
                    "max": 0.006,
                    "threshold": 0.15
                },
                "test_event_queue_performance": {
                    "mean": 0.002,
                    "std": 0.0002,
                    "min": 0.0018,
                    "max": 0.0025,
                    "threshold": 0.15
                },
                "test_self_state_apply_delta_performance": {
                    "mean": 0.003,
                    "std": 0.0003,
                    "min": 0.0025,
                    "max": 0.0035,
                    "threshold": 0.15
                },
                "test_runtime_loop_ticks_per_second": {
                    "mean": 50.0,
                    "std": 5.0,
                    "min": 40.0,
                    "max": 60.0,
                    "threshold": 0.15,
                    "higher_is_better": True
                },
                "test_memory_search_performance": {
                    "mean": 0.01,
                    "std": 0.001,
                    "min": 0.008,
                    "max": 0.012,
                    "threshold": 0.15
                }
            }
        }

        # Сохраняем baseline
        with open(baseline_file, 'w', encoding='utf-8') as f:
            json.dump(default_baseline, f, indent=2, ensure_ascii=False)

        print(f"✅ Baseline файл создан: {baseline_file}")
        print("📊 Использованы значения по умолчанию для начальной настройки")
        print("💡 Рекомендуется обновить baseline после нескольких прогонов тестов")

        return True

    except Exception as e:
        print(f"❌ Ошибка при создании baseline файла: {e}")
        return False

if __name__ == "__main__":
    success = init_baseline()
    exit(0 if success else 1)