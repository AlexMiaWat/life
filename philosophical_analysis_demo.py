#!/usr/bin/env python3
"""
Демо скрипт для демонстрации внешнего философского анализа системы Life.

Этот скрипт запускает реальную систему Life, делает снимки ее состояния
во время работы и анализирует поведение с помощью внешнего инструмента наблюдения.

Запуск: python philosophical_analysis_demo.py
"""

import sys
import os
import time
import threading
import json
from pathlib import Path
from typing import List, Dict, Any

# Добавляем src в путь для импорта
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from philosophical.external_philosophical_analyzer import (
    ExternalPhilosophicalAnalyzer,
    SystemSnapshot
)
from environment.event_queue import EventQueue
from state.self_state import SelfState
from runtime.loop import run_loop


def run_life_with_snapshots(duration_seconds=30, snapshot_interval=5):
    """
    Запустить систему Life и делать снимки состояния через регулярные интервалы.

    Args:
        duration_seconds: Длительность работы системы в секундах
        snapshot_interval: Интервал между снимками в секундах

    Returns:
        list: Список снимков состояния системы
    """
    print(f"Запуск системы Life на {duration_seconds} секунд с снимками каждые {snapshot_interval} сек...")

    # Создаем реальные компоненты
    self_state = SelfState()
    event_queue = EventQueue()

    # Импортируем компоненты для анализа
    from learning.learning import LearningEngine
    from adaptation.adaptation import AdaptationManager
    from decision.decision import DecisionEngine

    learning_engine = LearningEngine()
    adaptation_manager = AdaptationManager()
    decision_engine = DecisionEngine()

    # Событие для остановки
    stop_event = threading.Event()

    # Хранилище снимков
    snapshots = []
    snapshots_lock = threading.Lock()

    # Функция мониторинга (сборщик снимков)
    def monitor(state):
        pass  # Мониторинг не нужен для демо

    # Функция создания снимков
    def create_snapshot():
        try:
            analyzer = ExternalPhilosophicalAnalyzer()
            snapshot = analyzer.capture_system_snapshot(
                self_state, self_state.memory, learning_engine,
                adaptation_manager, decision_engine
            )
            with snapshots_lock:
                snapshots.append(snapshot)
            print(f"✓ Снимок создан на тике {self_state.ticks} (энергия: {self_state.energy:.1f})")
        except Exception as e:
            print(f"⚠ Ошибка при создании снимка: {e}")

    # Запускаем систему в отдельном потоке
    def run_system():
        try:
            run_loop(
                self_state=self_state,
                monitor=monitor,
                tick_interval=0.1,  # Быстрые тики для демо
                snapshot_period=100,  # Редкие автоматические снимки
                stop_event=stop_event,
                event_queue=event_queue,
                disable_weakness_penalty=True,  # Отключаем штрафы для стабильности демо
                disable_structured_logging=True,  # Отключаем логирование для чистоты вывода
                disable_learning=False,
                disable_adaptation=False,
                # disable_philosophical_analysis=False,  # УБРАНО: интеграция удалена
                # disable_philosophical_reports=True,  # УБРАНО: внешний инструмент
                log_flush_period_ticks=50,
                enable_profiling=False,
            )
        except Exception as e:
            print(f"Ошибка в runtime loop: {e}")

    # Запускаем систему
    system_thread = threading.Thread(target=run_system, daemon=True)
    system_thread.start()

    # Делаем начальный снимок
    time.sleep(0.5)  # Даем системе инициализироваться
    create_snapshot()

    # Делаем снимки через регулярные интервалы
    start_time = time.time()
    next_snapshot_time = start_time + snapshot_interval

    while time.time() - start_time < duration_seconds:
        if time.time() >= next_snapshot_time:
            create_snapshot()
            next_snapshot_time += snapshot_interval
        time.sleep(0.1)  # Небольшая пауза чтобы не загружать CPU

    # Финальный снимок
    create_snapshot()

    # Останавливаем систему
    stop_event.set()
    system_thread.join(timeout=2)

    print(f"✓ Система Life завершила работу после {self_state.ticks} тиков")
    print(f"  - Возраст: {self_state.age:.1f} сек")
    print(f"  - Энергия: {self_state.energy:.1f}")
    print(f"  - Стабильность: {self_state.stability:.3f}")
    print(f"  - Целостность: {self_state.integrity:.3f}")

    return snapshots


def demonstrate_philosophical_analysis():
    """Демонстрировать внешний философский анализ на реальной системе Life."""
    print("=" * 80)
    print("ДЕМОНСТРАЦИЯ ВНЕШНЕГО ФИЛОСОФСКОГО АНАЛИЗА СИСТЕМЫ LIFE")
    print("Анализ поведения реальной системы через внешний инструмент наблюдения")
    print("=" * 80)
    print()

    # Запускаем систему Life и собираем снимки
    snapshots = run_life_with_snapshots(duration_seconds=20, snapshot_interval=5)
    print(f"✓ Собрано {len(snapshots)} снимков состояния системы")
    print()

    if not snapshots:
        print("❌ Не удалось собрать снимки состояния системы")
        return

    # Создаем внешний анализатор
    analyzer = ExternalPhilosophicalAnalyzer()
    print("✓ Внешний философский анализатор инициализирован")
    print()

    # Анализируем каждый снимок
    reports = []
    print("Анализируем собранные снимки...")
    print()

    for i, snapshot in enumerate(snapshots, 1):
        print(f"Анализ снимка {i}/{len(snapshots)} (время: {snapshot.timestamp:.1f})")
        try:
            report = analyzer.analyze_snapshot(snapshot)
            reports.append(report)

            # Показываем краткую сводку
            assessment = report.overall_assessment
            score = assessment.get('overall_score', 0.0)
            interpretation = assessment.get('assessment', 'unknown')
            print(f"  Оценка: {score:.3f} ({interpretation.upper()})")

        except Exception as e:
            print(f"  ❌ Ошибка анализа: {e}")

    print()

    if not reports:
        print("❌ Не удалось проанализировать ни один снимок")
        return

    # Показываем тренды
    print("ТРЕНДЫ РАЗВИТИЯ СИСТЕМЫ:")
    print("-" * 50)

    if len(reports) > 1:
        # Собираем метрики по времени
        timestamps = [r.timestamp for r in reports]
        self_awareness_scores = [r.self_awareness.get('overall_self_awareness', 0) for r in reports]
        vitality_scores = [r.life_vitality.get('overall_vitality', 0) for r in reports]
        ethical_scores = [r.ethical_behavior.get('overall_ethical_score', 0) for r in reports]
        adaptation_scores = [r.adaptation_quality.get('overall_adaptation_quality', 0) for r in reports]
        integrity_scores = [r.conceptual_integrity.get('overall_integrity', 0) for r in reports]
        overall_scores = [r.overall_assessment.get('overall_score', 0) for r in reports]

        # Показываем начальное и конечное состояние
        print("Самоосознание:  {:.3f} → {:.3f}".format(self_awareness_scores[0], self_awareness_scores[-1]))
        print("Жизненность:    {:.3f} → {:.3f}".format(vitality_scores[0], vitality_scores[-1]))
        print("Этичность:      {:.3f} → {:.3f}".format(ethical_scores[0], ethical_scores[-1]))
        print("Адаптация:      {:.3f} → {:.3f}".format(adaptation_scores[0], adaptation_scores[-1]))
        print("Целостность:    {:.3f} → {:.3f}".format(integrity_scores[0], integrity_scores[-1]))
        print("ОБЩАЯ ОЦЕНКА:   {:.3f} → {:.3f}".format(overall_scores[0], overall_scores[-1]))

        # Определяем тренд
        if overall_scores[-1] > overall_scores[0] + 0.1:
            trend = "ПОЛОЖИТЕЛЬНЫЙ 📈"
        elif overall_scores[-1] < overall_scores[0] - 0.1:
            trend = "ОТРИЦАТЕЛЬНЫЙ 📉"
        else:
            trend = "СТАБИЛЬНЫЙ 📊"

        print(f"Тренд развития: {trend}")

    else:
        # Показываем единственный результат
        report = reports[0]
        assessment = report.overall_assessment
        score = assessment.get('overall_score', 0.0)
        interpretation = assessment.get('assessment', 'unknown')
        print(f"Текущая оценка системы: {score:.3f} ({interpretation.upper()})")

    print()

    # Сохраняем подробный отчет
    print("СОХРАНЕНИЕ ОТЧЕТА...")
    try:
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        output_dir = Path('philosophical_demo_reports')
        output_dir.mkdir(exist_ok=True)

        # Сохраняем последний отчет
        if reports:
            report_path = output_dir / f'demo_analysis_{timestamp}.json'
            analyzer.save_report(reports[-1], report_path)
            print(f"✓ Подробный отчет сохранен: {report_path}")

        # Сохраняем сводку трендов
        summary_path = output_dir / f'demo_summary_{timestamp}.txt'
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("ФИЛОСОФСКИЙ АНАЛИЗ СИСТЕМЫ LIFE - ДЕМОНСТРАЦИЯ\\n")
            f.write("=" * 60 + "\\n\\n")
            f.write(f"Анализ проведен: {time.strftime('%Y-%m-%d %H:%M:%S')}\\n")
            f.write(f"Количество снимков: {len(snapshots)}\\n")
            f.write(f"Длительность наблюдения: 20 секунд\\n\\n")

            if reports:
                final_report = reports[-1]
                f.write("ФИНАЛЬНАЯ ОЦЕНКА:\\n")
                assessment = final_report.overall_assessment
                f.write(f"Общий балл: {assessment.get('overall_score', 0):.3f}\\n")
                f.write(f"Оценка: {assessment.get('assessment', 'unknown').upper()}\\n")
                f.write(f"Метрик проанализировано: {assessment.get('metrics_count', 0)}\\n\\n")

                f.write("ДЕТАЛЬНЫЕ МЕТРИКИ:\\n")
                for category in ['self_awareness', 'life_vitality', 'ethical_behavior', 'adaptation_quality', 'conceptual_integrity']:
                    category_data = getattr(final_report, category)
                    if isinstance(category_data, dict) and 'error' not in category_data:
                        for key, value in category_data.items():
                            if key.startswith('overall_') and isinstance(value, (int, float)):
                                f.write(f"{category}: {value:.3f}\\n")
                                break

        print(f"✓ Сводка трендов сохранена: {summary_path}")

    except Exception as e:
        print(f"⚠ Ошибка сохранения отчета: {e}")

    print()
    print("✓ Демонстрация завершена успешно!")
    print("Философский анализ показал реальное поведение системы Life")

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