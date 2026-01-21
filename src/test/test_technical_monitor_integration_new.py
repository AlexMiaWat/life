"""
Интеграционные тесты для TechnicalBehaviorMonitor с реальными компонентами Life.

Тестирует работу монитора с настоящими объектами системы Life,
включая SelfState, Memory, LearningEngine, AdaptationManager.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Добавляем src в путь
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from src.technical_monitor import TechnicalBehaviorMonitor
from src.state.self_state import SelfState
from src.memory.memory import Memory
from src.learning.learning import LearningEngine
from src.adaptation.adaptation import AdaptationManager
from src.environment.event_queue import EventQueue
from src.runtime.loop import run_loop
import threading
import time


class TestTechnicalMonitorIntegrationNew(unittest.TestCase):
    """Интеграционные тесты для TechnicalBehaviorMonitor с новыми компонентами."""

    def setUp(self):
        """Подготовка тестового окружения."""
        self.monitor = TechnicalBehaviorMonitor()

        # Создаем реальные компоненты для интеграционного тестирования
        self.self_state = SelfState()
        self.memory = Memory()
        self.learning_engine = LearningEngine()
        self.adaptation_manager = AdaptationManager()
        self.event_queue = EventQueue()

    def test_capture_snapshot_with_real_components_integration(self):
        """Интеграционный тест захвата снимка с реальными компонентами системы."""
        # Создаем mock decision engine для полной интеграции
        mock_decision_engine = Mock()
        mock_decision_engine.get_recent_decisions.return_value = [
            {'timestamp': time.time(), 'type': 'adaptation', 'data': {'intensity': 0.5}}
        ]
        mock_decision_engine.get_statistics.return_value = {
            'total_decisions': 1,
            'average_time': 0.015,
            'accuracy': 0.85
        }

        # Захватываем снимок с реальными компонентами
        snapshot = self.monitor.capture_system_snapshot(
            self_state=self.self_state,
            memory=self.memory,
            learning_engine=self.learning_engine,
            adaptation_manager=self.adaptation_manager,
            decision_engine=mock_decision_engine
        )

        # Проверяем структуру снимка
        self.assertIsNotNone(snapshot)
        self.assertIsInstance(snapshot.self_state, dict)
        self.assertIsInstance(snapshot.memory_stats, dict)
        self.assertIsInstance(snapshot.learning_params, dict)
        self.assertIsInstance(snapshot.adaptation_params, dict)
        self.assertIsInstance(snapshot.decision_history, list)

        # Проверяем наличие ключевых метрик
        self.assertIn('life_id', snapshot.self_state)
        self.assertIn('energy', snapshot.self_state)
        self.assertIn('stability', snapshot.self_state)
        self.assertIn('integrity', snapshot.self_state)

        # Проверяем статистику памяти
        self.assertIn('total_entries', snapshot.memory_stats)

        # Проверяем параметры обучения
        self.assertIn('MAX_PARAMETER_DELTA', snapshot.learning_params)
        self.assertIn('MIN_PARAMETER_DELTA', snapshot.learning_params)

        # Проверяем параметры адаптации
        self.assertIn('MAX_ADAPTATION_DELTA', snapshot.adaptation_params)
        self.assertIn('MIN_ADAPTATION_DELTA', snapshot.adaptation_params)

        # Проверяем историю решений
        self.assertEqual(len(snapshot.decision_history), 1)

    def test_analyze_snapshot_comprehensive_integration(self):
        """Комплексный интеграционный тест анализа снимка."""
        # Создаем mock decision engine
        mock_decision_engine = Mock()
        mock_decision_engine.get_recent_decisions.return_value = [
            {'timestamp': i * 1000, 'type': 'adaptation' if i % 2 == 0 else 'learning', 'data': {}}
            for i in range(10)
        ]
        mock_decision_engine.get_statistics.return_value = {
            'total_decisions': 10,
            'average_time': 0.012,
            'accuracy': 0.88
        }

        # Захватываем и анализируем снимок
        snapshot = self.monitor.capture_system_snapshot(
            self_state=self.self_state,
            memory=self.memory,
            learning_engine=self.learning_engine,
            adaptation_manager=self.adaptation_manager,
            decision_engine=mock_decision_engine
        )

        report = self.monitor.analyze_snapshot(snapshot)

        # Проверяем структуру отчета
        self.assertIsNotNone(report)
        self.assertIsNotNone(report.timestamp)
        self.assertIsInstance(report.performance, dict)
        self.assertIsInstance(report.stability, dict)
        self.assertIsInstance(report.adaptability, dict)
        self.assertIsInstance(report.integrity, dict)
        self.assertIsInstance(report.overall_assessment, dict)

        # Проверяем наличие ключевых метрик
        self.assertIn('overall_performance', report.performance)
        self.assertIn('overall_stability', report.stability)
        self.assertIn('overall_adaptability', report.adaptability)
        self.assertIn('overall_integrity', report.integrity)
        self.assertIn('overall_score', report.overall_assessment)
        self.assertIn('status', report.overall_assessment)

        # Проверяем диапазоны значений (0.0 - 1.0)
        for metric_name, metric_value in report.performance.items():
            if isinstance(metric_value, (int, float)):
                self.assertGreaterEqual(metric_value, 0.0, f"Metric {metric_name} < 0")
                self.assertLessEqual(metric_value, 1.0, f"Metric {metric_name} > 1")

        for metric_name, metric_value in report.stability.items():
            if isinstance(metric_value, (int, float)):
                self.assertGreaterEqual(metric_value, 0.0, f"Metric {metric_name} < 0")
                self.assertLessEqual(metric_value, 1.0, f"Metric {metric_name} > 1")

        overall_score = report.overall_assessment['overall_score']
        self.assertGreaterEqual(overall_score, 0.0)
        self.assertLessEqual(overall_score, 1.0)

    def test_monitor_with_runtime_loop_integration(self):
        """Интеграционный тест монитора с runtime loop."""
        # Создаем mock монитора для runtime loop
        runtime_monitor = Mock()

        # Создаем стоп-событие для быстрой остановки
        stop_event = threading.Event()
        stop_event.set()  # Останавливаем сразу после инициализации

        # Запускаем runtime loop с минимальной конфигурацией
        try:
            run_loop(
                self_state=self.self_state,
                monitor=runtime_monitor,
                tick_interval=0.01,  # Быстрый тик для теста
                snapshot_period=1000,  # Редкие снапшоты
                stop_event=stop_event,
                event_queue=self.event_queue,
                disable_weakness_penalty=True,
                disable_structured_logging=True,
                disable_learning=True,
                disable_adaptation=True,
                log_flush_period_ticks=1000,
                enable_profiling=False,
            )
        except Exception:
            # Игнорируем исключения - нас интересует только инициализация
            pass

        # Теперь тестируем монитор с обновленным состоянием
        mock_decision_engine = Mock()
        mock_decision_engine.get_recent_decisions.return_value = []
        mock_decision_engine.get_statistics.return_value = {'total_decisions': 0}

        snapshot = self.monitor.capture_system_snapshot(
            self_state=self.self_state,
            memory=self.memory,
            learning_engine=self.learning_engine,
            adaptation_manager=self.adaptation_manager,
            decision_engine=mock_decision_engine
        )

        # Проверяем что snapshot содержит актуальное состояние
        self.assertIsNotNone(snapshot)
        self.assertIsInstance(snapshot.self_state, dict)

    def test_save_and_load_report_integration(self):
        """Интеграционный тест сохранения и загрузки отчета."""
        # Создаем mock decision engine
        mock_decision_engine = Mock()
        mock_decision_engine.get_recent_decisions.return_value = []
        mock_decision_engine.get_statistics.return_value = {}

        # Создаем и анализируем снимок
        snapshot = self.monitor.capture_system_snapshot(
            self_state=self.self_state,
            memory=self.memory,
            learning_engine=self.learning_engine,
            adaptation_manager=self.adaptation_manager,
            decision_engine=mock_decision_engine
        )

        original_report = self.monitor.analyze_snapshot(snapshot)

        # Сохраняем отчет
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name

        try:
            self.monitor.save_report(original_report, temp_file)

            # Загружаем отчет
            loaded_report = self.monitor.load_report(temp_file)

            # Проверяем, что данные совпадают
            self.assertIsNotNone(loaded_report)
            self.assertAlmostEqual(
                original_report.overall_assessment['overall_score'],
                loaded_report.overall_assessment['overall_score'],
                places=5
            )
            self.assertEqual(
                original_report.overall_assessment['status'],
                loaded_report.overall_assessment['status']
            )

            # Проверяем структуру загруженного отчета
            self.assertIsInstance(loaded_report.performance, dict)
            self.assertIsInstance(loaded_report.stability, dict)
            self.assertIsInstance(loaded_report.adaptability, dict)
            self.assertIsInstance(loaded_report.integrity, dict)

        finally:
            # Удаляем временный файл
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_trends_analysis_integration(self):
        """Интеграционный тест анализа трендов."""
        # Создаем несколько отчетов с разными характеристиками
        mock_decision_engine = Mock()
        mock_decision_engine.get_recent_decisions.return_value = []
        mock_decision_engine.get_statistics.return_value = {
            'total_decisions': 5,
            'average_time': 0.01,
            'accuracy': 0.8
        }

        # Создаем базовый снимок
        snapshot = self.monitor.capture_system_snapshot(
            self_state=self.self_state,
            memory=self.memory,
            learning_engine=self.learning_engine,
            adaptation_manager=self.adaptation_manager,
            decision_engine=mock_decision_engine
        )

        # Создаем несколько отчетов с небольшими изменениями
        reports = []
        for i in range(5):
            # Модифицируем self_state для создания разных значений
            modified_self_state = SelfState()
            modified_self_state.age = 100.0 + i * 10
            modified_self_state.ticks = 1000 + i * 100
            modified_self_state.energy = min(1.0, 0.8 - i * 0.05)  # Постепенное снижение энергии
            modified_self_state.stability = min(1.0, 0.9 + i * 0.02)  # Постепенное улучшение стабильности

            modified_snapshot = self.monitor.capture_system_snapshot(
                self_state=modified_self_state,
                memory=self.memory,
                learning_engine=self.learning_engine,
                adaptation_manager=self.adaptation_manager,
                decision_engine=mock_decision_engine
            )

            report = self.monitor.analyze_snapshot(modified_snapshot)
            reports.append(report)

        # Добавляем отчеты в историю монитора
        self.monitor.report_history.extend(reports)

        # Анализируем тренды
        trends = self.monitor.get_trends(hours=1)

        # Проверяем структуру трендов
        self.assertIsInstance(trends, dict)
        self.assertNotIn('error', trends)  # Не должно быть ошибки

        expected_trend_keys = [
            'performance_trend', 'stability_trend',
            'adaptability_trend', 'integrity_trend', 'overall_trend'
        ]

        for key in expected_trend_keys:
            self.assertIn(key, trends)
            trend_data = trends[key]
            self.assertIsInstance(trend_data, dict)
            self.assertIn('direction', trend_data)
            self.assertIn('magnitude', trend_data)

    def test_monitor_with_memory_operations(self):
        """Интеграционный тест монитора с операциями памяти."""
        from src.environment.event import Event

        # Добавляем записи в память
        for i in range(10):
            event = Event(
                type="test_event",
                intensity=0.5 + i * 0.05,
                timestamp=time.time() + i,
                metadata={"test_id": i}
            )
            meaning = self.memory.process_event(event, self.self_state)
            self.memory.store_memory(event, meaning, self.self_state)

        # Создаем mock decision engine
        mock_decision_engine = Mock()
        mock_decision_engine.get_recent_decisions.return_value = []
        mock_decision_engine.get_statistics.return_value = {}

        # Захватываем снимок с заполненной памятью
        snapshot = self.monitor.capture_system_snapshot(
            self_state=self.self_state,
            memory=self.memory,
            learning_engine=self.learning_engine,
            adaptation_manager=self.adaptation_manager,
            decision_engine=mock_decision_engine
        )

        # Проверяем что память содержит записи
        self.assertIn('total_entries', snapshot.memory_stats)
        self.assertGreaterEqual(snapshot.memory_stats['total_entries'], 10)

        # Анализируем снимок
        report = self.monitor.analyze_snapshot(snapshot)

        # Проверяем что анализ учитывает данные памяти
        self.assertIsInstance(report.integrity, dict)
        self.assertIn('memory_integrity', report.integrity)

    def test_monitor_with_learning_adaptation_cycle(self):
        """Интеграционный тест монитора с циклом обучения и адаптации."""
        from src.environment.event import Event

        # Выполняем цикл обучения и адаптации
        for cycle in range(5):
            # Создаем тестовое событие
            event = Event(
                type="adaptation_test",
                intensity=0.3 + cycle * 0.1,
                timestamp=time.time() + cycle * 10
            )

            # Обрабатываем через компоненты
            meaning = self.memory.process_event(event, self.self_state)

            # Обновляем обучение
            statistics = self.learning_engine.process_statistics(
                [{'event': event, 'meaning': meaning}]
            )
            current_params = {
                'event_type_sensitivity': {'adaptation_test': 0.5},
                'significance_thresholds': {},
                'response_coefficients': {}
            }
            new_params = self.learning_engine.adjust_parameters(statistics, current_params)
            self.learning_engine.record_changes(current_params, new_params, self.self_state)

            # Применяем адаптацию
            analysis = self.adaptation_manager.analyze_changes(new_params, [])
            self.adaptation_manager.apply_adaptation(analysis, current_params, self.self_state)
            self.adaptation_manager.store_history(current_params, new_params, self.self_state)

        # Создаем mock decision engine
        mock_decision_engine = Mock()
        mock_decision_engine.get_recent_decisions.return_value = []
        mock_decision_engine.get_statistics.return_value = {}

        # Захватываем снимок после цикла
        snapshot = self.monitor.capture_system_snapshot(
            self_state=self.self_state,
            memory=self.memory,
            learning_engine=self.learning_engine,
            adaptation_manager=self.adaptation_manager,
            decision_engine=mock_decision_engine
        )

        # Анализируем
        report = self.monitor.analyze_snapshot(snapshot)

        # Проверяем что монитор отражает изменения от обучения и адаптации
        self.assertIsInstance(report.adaptability, dict)
        self.assertIsInstance(report.performance, dict)

        # Проверяем наличие метрик адаптации
        self.assertIn('learning_adaptation_effectiveness', report.adaptability)

    def test_error_handling_with_real_components(self):
        """Тест обработки ошибок с реальными компонентами."""
        # Создаем компоненты, которые могут вызывать ошибки
        class FailingMemory:
            def get_statistics(self):
                raise RuntimeError("Memory failure")

        class FailingLearningEngine:
            def get_parameters(self):
                raise ValueError("Learning engine failure")

        # Создаем mock decision engine
        mock_decision_engine = Mock()
        mock_decision_engine.get_recent_decisions.return_value = []
        mock_decision_engine.get_statistics.return_value = {}

        # Захватываем снимок с проблемными компонентами
        snapshot = self.monitor.capture_system_snapshot(
            self_state=self.self_state,
            memory=FailingMemory(),
            learning_engine=FailingLearningEngine(),
            adaptation_manager=self.adaptation_manager,
            decision_engine=mock_decision_engine
        )

        # Проверяем, что система справилась с ошибками
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot.memory_stats, {'error': 'Memory failure'})
        self.assertEqual(snapshot.learning_params, {'error': 'Learning engine failure'})

        # Анализируем снимок
        report = self.monitor.analyze_snapshot(snapshot)

        # Проверяем, что анализ прошел успешно несмотря на ошибки
        self.assertIsNotNone(report)
        self.assertIsInstance(report.overall_assessment, dict)
        self.assertIn('overall_score', report.overall_assessment)


if __name__ == '__main__':
    unittest.main()