#!/usr/bin/env python3
"""
Демо скрипт для демонстрации философского анализа поведения системы Life.

Этот скрипт запускает реальную систему Life на короткое время и анализирует
ее поведение с философской точки зрения.

Запуск: python philosophical_analysis_demo.py
"""

import sys
import os
import time
import threading
from pathlib import Path

# Добавляем src в путь для импорта
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from philosophical.philosophical_analyzer import PhilosophicalAnalyzer
from philosophical.visualization import PhilosophicalVisualizer
from environment.event_queue import EventQueue
from state.self_state import SelfState
from runtime.loop import run_loop


def run_life_system_demo(duration_seconds=30):
    """
    Запустить систему Life на короткое время для демонстрации.

    Args:
        duration_seconds: Длительность работы системы в секундах

    Returns:
        tuple: (self_state, event_queue) после работы системы
    """
    print(f"Запуск системы Life на {duration_seconds} секунд для сбора данных...")

    # Создаем реальные компоненты
    self_state = SelfState()
    event_queue = EventQueue()

    # Событие для остановки
    stop_event = threading.Event()

    # Функция мониторинга (пустая для демо)
    def monitor(state):
        pass

    # Запускаем систему в отдельном потоке
    def run_system():
        try:
            run_loop(
                self_state=self_state,
                monitor=monitor,
                tick_interval=0.1,  # Быстрые тики для демо
                snapshot_period=100,  # Редкие снимки
                stop_event=stop_event,
                event_queue=event_queue,
                disable_weakness_penalty=True,  # Отключаем штрафы для стабильности демо
                disable_structured_logging=True,  # Отключаем логирование для чистоты вывода
                disable_learning=False,
                disable_adaptation=False,
                disable_philosophical_analysis=False,  # Включаем анализ
                disable_philosophical_reports=True,  # Отключаем отчеты во время демо
                log_flush_period_ticks=50,
                enable_profiling=False,
            )
        except Exception as e:
            print(f"Ошибка в runtime loop: {e}")

    # Запускаем систему
    system_thread = threading.Thread(target=run_system, daemon=True)
    system_thread.start()

    # Ждем указанное время
    time.sleep(duration_seconds)

    # Останавливаем систему
    stop_event.set()
    system_thread.join(timeout=2)

    print(f"✓ Система Life завершила работу после {self_state.ticks} тиков")
    print(f"  - Возраст: {self_state.age:.1f} сек")
    print(f"  - Энергия: {self_state.energy:.1f}")
    print(f"  - Стабильность: {self_state.stability:.3f}")
    print(f"  - Целостность: {self_state.integrity:.3f}")
    print(f"  - Записей в памяти: {len(self_state.memory)}")

    return self_state, event_queue


def demonstrate_philosophical_analysis():
    """Демонстрировать философский анализ на реальной системе Life."""
    print("=" * 80)
    print("ДЕМОНСТРАЦИЯ ФИЛОСОФСКОГО АНАЛИЗА СИСТЕМЫ LIFE")
    print("Анализ поведения реальной системы (не mock-данных)")
    print("=" * 80)
    print()

    # Создаем анализатор и визуализатор
    analyzer = PhilosophicalAnalyzer()
    visualizer = PhilosophicalVisualizer()
    print("✓ Философский анализатор и визуализатор инициализированы")
    print()

    # Запускаем систему Life для сбора реальных данных
    self_state, event_queue = run_life_system_demo(duration_seconds=15)
    print()

    # Импортируем реальные компоненты для анализа
    from learning.learning import LearningEngine
    from adaptation.adaptation import AdaptationManager
    from decision.decision import DecisionEngine

    memory = self_state.memory
    learning_engine = LearningEngine()
    adaptation_manager = AdaptationManager()
    decision_engine = DecisionEngine()

    print("Выполняем философский анализ реального поведения системы...")
    print()

    # Выполняем анализ несколько раз для демонстрации трендов
    for i in range(3):
        print(f"--- Анализ #{i+1} ---")

        # Немного изменяем состояние между анализами для демонстрации
        if i > 0:
            # Имитируем небольшие изменения в поведении
            self_state.energy = min(100, self_state.energy + (i * 2) - 3)
            self_state.stability = min(1.0, max(0.0, self_state.stability + (i * 0.02) - 0.03))

        # Выполняем анализ
        metrics = analyzer.analyze_behavior(
            self_state, memory, learning_engine, adaptation_manager, decision_engine
        )

        print(f"Наблюдаемые характеристики: {metrics.self_awareness.overall_self_awareness:.3f}")
        print(f"Качество адаптации: {metrics.adaptation_quality.overall_adaptation_quality:.3f}")
        print(f"Этические аспекты поведения: {metrics.ethical_behavior.overall_ethical_score:.3f}")
        print(f"Концептуальная целостность: {metrics.conceptual_integrity.overall_integrity:.3f}")
        print(f"Жизненность поведения: {metrics.life_vitality.overall_vitality:.3f}")
        print(f"Общий индекс наблюдений: {metrics.philosophical_index:.3f}")

        # Показываем insights
        insights = analyzer.get_philosophical_insights(metrics)
        print(f"Вывод: {insights.get('overall', 'Недоступно')}")
        print()

    print("-" * 80)
    print("АНАЛИЗ ТРЕНДОВ НАБЛЮДЕНИЙ")
    print("-" * 80)

    # Анализируем тренды
    trends = analyzer.analyze_trends()
    if trends:
        print("Тренды ключевых наблюдений:")
        for metric_path, trend_info in trends.items():
            metric_name = metric_path.replace('_', ' ').replace('.', ' - ').title()
            trend_symbol = {
                'improving': '↗️ улучшается',
                'declining': '↘️ ухудшается',
                'stable': '→ стабильно'
            }.get(trend_info['trend'], '? неизвестно')

            print(f"  {metric_name}: {trend_symbol}")
    else:
        print("Недостаточно данных для анализа трендов")
    print()

    print("-" * 80)
    print("СОЗДАНИЕ ВИЗУАЛЬНЫХ ОТЧЕТОВ")
    print("-" * 80)

    # Создаем визуальные отчеты
    try:
        visualizer.create_comprehensive_report(analyzer, 'demo_reports')
        print("✓ Визуальные отчеты созданы в директории 'demo_reports'")
    except Exception as e:
        print(f"✗ Ошибка создания визуальных отчетов: {e}")
        print("  (Возможно, не установлен matplotlib)")
    print()

    print("-" * 80)
    print("ПОЛНЫЙ ОТЧЕТ НАБЛЮДЕНИЙ")
    print("-" * 80)

    # Генерируем полный отчет
    final_metrics = analyzer.analyze_behavior(
        self_state, memory, learning_engine, adaptation_manager, decision_engine
    )
    report = analyzer.generate_philosophical_report(final_metrics)

    print(report)

    print()
    print("=" * 80)
    print("ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    print("Система Life была проанализирована как объект внешнего наблюдения,")
    print("а не самоанализ. Анализ не влияет на поведение системы.")
    print("=" * 80)


if __name__ == "__main__":
    try:
        demonstrate_philosophical_analysis()
    except Exception as e:
        print(f"Ошибка при выполнении демонстрации: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)