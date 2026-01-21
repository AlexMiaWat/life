#!/usr/bin/env python3
"""
Ручное тестирование системы моментов ясности.

Запуск: python manual_test_clarity.py
"""

import sys
import time
from pathlib import Path

# Добавляем корневую папку проекта в путь
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from src.experimental.clarity_moments import ClarityMoments
from src.state.self_state import SelfState


def test_clarity_moments_basic():
    """Базовое тестирование ClarityMoments"""
    print("=== Тестирование ClarityMoments ===")

    # Создаем компоненты
    from unittest.mock import Mock

    logger = Mock()  # Mock для тестирования
    clarity_moments = ClarityMoments(logger=logger)
    self_state = SelfState()

    # Устанавливаем состояние ниже порогов
    self_state.stability = 0.5
    self_state.energy = 0.5
    self_state.ticks = 15

    print(
        f"Начальное состояние: stability={self_state.stability}, energy={self_state.energy}"
    )

    # Проверяем - должно вернуть None
    result = clarity_moments.check_clarity_conditions(self_state)
    print(f"Проверка с низкими параметрами: {result}")

    # Устанавливаем высокие параметры
    self_state.stability = 0.9
    self_state.energy = 0.8

    print(
        f"Обновленное состояние: stability={self_state.stability}, energy={self_state.energy}"
    )

    # Проверяем - должно создать событие
    result = clarity_moments.check_clarity_conditions(self_state)
    print(
        f"Проверка с высокими параметрами: {'Событие создано' if result else 'Событие не создано'}"
    )

    if result:
        print(f"  Тип события: {result['type']}")
        print(f"  ID clarity: {result['data']['clarity_id']}")
        print(
            f"  Условия: stability={result['data']['trigger_conditions']['stability']}, energy={result['data']['trigger_conditions']['energy']}"
        )

    # Активируем clarity
    clarity_moments.activate_clarity_moment(self_state)
    print(
        f"После активации: clarity_state={self_state.clarity_state}, duration={self_state.clarity_duration}, modifier={self_state.clarity_modifier}"
    )

    # Симулируем несколько тиков
    for i in range(5):
        clarity_moments.update_clarity_state(self_state)
        print(f"Тик {i+1}: duration={self_state.clarity_duration}")

    print()


def test_clarity_with_meaning_engine():
    """Тестирование интеграции с MeaningEngine"""
    print("=== Тестирование с MeaningEngine ===")

    # Создаем компоненты
    from unittest.mock import Mock

    from src.environment.event import Event
    from src.meaning.engine import MeaningEngine

    logger = Mock()  # Mock для тестирования
    clarity_moments = ClarityMoments(logger=logger)
    meaning_engine = MeaningEngine()
    self_state = SelfState()

    # Создаем тестовое событие
    event = Event(type="noise", intensity=0.5, timestamp=time.time())

    # Тестируем без clarity
    self_state.clarity_state = False
    significance_without = meaning_engine.appraisal(event, self_state)
    print(f"Значимость без clarity: {significance_without:.3f}")

    # Активируем clarity
    clarity_moments.activate_clarity_moment(self_state)

    # Тестируем с clarity
    significance_with = meaning_engine.appraisal(event, self_state)
    print(f"Значимость с clarity: {significance_with:.3f}")

    ratio = significance_with / significance_without if significance_without > 0 else 0
    print(f"Усиление: {ratio:.2f}x (ожидалось ~1.5x)")

    print()


def test_clarity_state_persistence():
    """Тестирование сохранения состояния clarity"""
    print("=== Тестирование сохранения состояния Clarity ===")

    from unittest.mock import Mock

    logger = Mock()
    clarity_moments = ClarityMoments(logger=logger)
    self_state = SelfState()

    # Устанавливаем хорошие параметры
    self_state.stability = 0.9
    self_state.energy = 0.8
    self_state.ticks = 20

    print(f"Начальное состояние: ticks={self_state.ticks}")

    # Создаем событие clarity
    result = clarity_moments.check_clarity_conditions(self_state)
    if result:
        print("✅ Clarity событие создано")
        clarity_moments.activate_clarity_moment(self_state)
        print(
            f"После активации: state={self_state.clarity_state}, duration={self_state.clarity_duration}"
        )

        # Симулируем полный цикл clarity
        initial_duration = self_state.clarity_duration
        for i in range(initial_duration):
            clarity_moments.update_clarity_state(self_state)
            if i % 10 == 0:  # Печатаем каждые 10 тиков
                print(
                    f"Тик {i}: duration={self_state.clarity_duration}, active={self_state.clarity_state}"
                )

        print(
            f"После завершения: state={self_state.clarity_state}, duration={self_state.clarity_duration}"
        )
        print(f"Всего событий clarity: {clarity_moments._clarity_events_count}")
    else:
        print("❌ Clarity событие не создано")

    print()


def main():
    """Основная функция тестирования"""
    print("Ручное тестирование системы моментов ясности")
    print("=" * 50)

    try:
        test_clarity_moments_basic()
        test_clarity_with_meaning_engine()
        test_clarity_state_persistence()

        print("✅ Ручное тестирование завершено успешно")

    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
