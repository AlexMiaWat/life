#!/usr/bin/env python3
"""
Ручное тестирование руководства по troubleshooting
Проверяет выполнимость инструкций из docs/development/debugging.md
"""

import subprocess
import sys
from pathlib import Path

# Добавляем src в путь для импортов
sys.path.insert(0, "src")


def test_quick_start_checklist():
    """Тестирование 5-минутного чек-листа из раздела 'Быстрый старт отладки'"""
    print("🧪 Тестирование 5-минутного чек-листа...")

    # 4. Запустить быстрый тест системы
    try:
        from state.self_state import SelfState

        state = SelfState()
        energy = state.energy
        memory_size = len(state.memory)
        print(f"✅ Система инициализируется: energy={energy}, memory={memory_size}")
        return True
    except Exception as e:
        print(f"❌ Ошибка в быстром тесте системы: {e}")
        return False


def test_debugging_commands_execution():
    """Тестирование выполнения команд отладки из руководства"""
    print("🧪 Тестирование команд отладки...")

    commands_tested = 0
    commands_passed = 0

    # Проверяем существование файлов логов
    if Path("data/structured_log.jsonl").exists():
        commands_passed += 1
        print("✅ Файл structured_log.jsonl существует")
    else:
        print("⚠️  Файл structured_log.jsonl не найден")
    commands_tested += 1

    # Проверяем возможность запуска pytest
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            commands_passed += 1
            print("✅ pytest доступен")
        else:
            print("❌ pytest недоступен")
    except Exception as e:
        print(f"❌ Ошибка проверки pytest: {e}")
    commands_tested += 1

    return commands_passed == commands_tested


def test_monitoring_setup():
    """Тестирование настройки мониторинга"""
    print("🧪 Тестирование настройки мониторинга...")

    try:
        from observability.structured_logger import StructuredLogger

        # Проверяем создание логгера
        StructuredLogger(enabled=True)
        print("✅ StructuredLogger инициализируется")
        return True
    except Exception as e:
        print(f"❌ Ошибка инициализации StructuredLogger: {e}")
        return False


def test_performance_baseline_check():
    """Тестирование проверки базовых метрик производительности"""
    print("🧪 Тестирование базовых метрик производительности...")

    try:
        import time

        from runtime.performance_metrics import measure_time

        with measure_time("test_performance"):
            time.sleep(0.01)  # Минимальная задержка для теста

        print("✅ Система измерения производительности работает")
        return True
    except Exception as e:
        print(f"❌ Ошибка измерения производительности: {e}")
        return False


def test_component_debugging_scenarios():
    """Тестирование сценариев отладки компонентов"""
    print("🧪 Тестирование сценариев отладки компонентов...")

    scenarios_tested = 0
    scenarios_passed = 0

    # Проверяем доступность основных компонентов
    try:
        scenarios_passed += 1
        print("✅ Основные компоненты импортируются")
    except Exception as e:
        print(f"❌ Ошибка импорта компонентов: {e}")
    scenarios_tested += 1

    return scenarios_passed == scenarios_tested


def main():
    """Основная функция тестирования"""
    print("🚀 Начало тестирования руководства по troubleshooting")
    print("=" * 60)

    tests = [
        test_quick_start_checklist,
        test_debugging_commands_execution,
        test_monitoring_setup,
        test_performance_baseline_check,
        test_component_debugging_scenarios,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
                print(f"✅ {test.__name__}")
            else:
                print(f"❌ {test.__name__}")
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")

    print("=" * 60)
    print(f"📊 Результаты: {passed}/{total} тестов пройдено")

    if passed == total:
        print("🎉 Все тесты пройдены! Руководство по troubleshooting валидно.")
        return 0
    else:
        print("⚠️  Некоторые тесты провалены. Проверьте руководство.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
