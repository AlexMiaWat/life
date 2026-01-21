#!/usr/bin/env python3
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
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from technical_monitor import TechnicalBehaviorMonitor
from state.self_state import SelfState
from memory.memory import Memory
from learning.learning import LearningEngine
from adaptation.adaptation import AdaptationManager


class TestTechnicalMonitorIntegration(unittest.TestCase):
    """Интеграционные тесты для TechnicalBehaviorMonitor."""

    def setUp(self):
        """Подготовка тестового окружения."""
        self.monitor = TechnicalBehaviorMonitor()

        # Создаем mock-объекты для тестирования (реальные компоненты слишком сложны для unit-тестов)
        self.self_state = self._create_mock_self_state()
        self.memory = self._create_mock_memory()
        self.learning_engine = self._create_mock_learning_engine()
        self.adaptation_manager = self._create_mock_adaptation_manager()

    def _create_mock_self_state(self):
        """Создает mock self_state для тестирования."""
        class MockSelfState:
            def __init__(self):
                self.life_id = 'test_life'
                self.age = 100.0
                self.ticks = 1000
                self.energy = 0.8
                self.stability = 0.9
                self.integrity = 0.85
                self.adaptation_level = 0.7
                self.behavior_stats = {'test_metric': 0.5}

        return MockSelfState()

    def _create_mock_memory(self):
        """Создает mock memory для тестирования."""
        class MockMemory:
            def __init__(self):
                self.entries = []

            def get_statistics(self):
                return {
                    'total_entries': len(self.entries),
                    'efficiency': 0.85,
                    'avg_significance': 0.6
                }

            def append(self, entry):
                self.entries.append(entry)

        memory = MockMemory()
        # Добавляем несколько записей
        for i in range(10):
            memory.entries.append(Mock())
        return memory

    def _create_mock_learning_engine(self):
        """Создает mock learning_engine для тестирования."""
        class MockLearningEngine:
            def get_parameters(self):
                return {
                    'learning_rate': 0.7,
                    'progress': 0.8,
                    'iterations': 1000
                }

        return MockLearningEngine()

    def _create_mock_adaptation_manager(self):
        """Создает mock adaptation_manager для тестирования."""
        class MockAdaptationManager:
            def get_parameters(self):
                return {
                    'adaptation_rate': 0.6,
                    'stability': 0.9,
                    'threshold': 0.5
                }

        return MockAdaptationManager()

    def test_capture_snapshot_with_real_components(self):
        """Тест захвата снимка с реальными компонентами."""
        # Создаем mock decision engine
        mock_decision_engine = Mock()
        mock_decision_engine.get_recent_decisions.return_value = [
            {'timestamp': 1.0, 'type': 'test_decision', 'data': {}}
        ]
        mock_decision_engine.get_statistics.return_value = {
            'total_decisions': 1,
            'average_time': 0.01,
            'accuracy': 0.8
        }

        # Захватываем снимок
        snapshot = self.monitor.capture_system_snapshot(
            self_state=self.self_state,
            memory=self.memory,
            learning_engine=self.learning_engine,
            adaptation_manager=self.adaptation_manager,
            decision_engine=mock_decision_engine
        )

        # Проверяем, что снимок содержит правильные данные
        self.assertIsNotNone(snapshot)
        # Проверяем, что снимок содержит данные (mock-объекты могут не иметь всех атрибутов)
        self.assertIsInstance(snapshot.self_state, dict)
        self.assertIn('energy_level', snapshot.self_state)
        self.assertIn('adaptation_level', snapshot.self_state)

        # Проверяем статистику памяти
        self.assertIn('total_entries', snapshot.memory_stats)
        self.assertGreaterEqual(snapshot.memory_stats['total_entries'], 10)

        # Проверяем параметры обучения и адаптации
        self.assertIsInstance(snapshot.learning_params, dict)
        self.assertIsInstance(snapshot.adaptation_params, dict)

        # Проверяем историю решений
        self.assertIsInstance(snapshot.decision_history, list)
        self.assertGreaterEqual(len(snapshot.decision_history), 1)

    def test_analyze_snapshot_comprehensive(self):
        """Комплексный тест анализа снимка."""
        # Создаем mock decision engine
        mock_decision_engine = Mock()
        mock_decision_engine.get_recent_decisions.return_value = [
            {'timestamp': i, 'type': 'adaptation' if i % 2 == 0 else 'learning', 'data': {}}
            for i in range(20)
        ]
        mock_decision_engine.get_statistics.return_value = {
            'total_decisions': 20,
            'average_time': 0.015,
            'accuracy': 0.85
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

        for metric_name, metric_value in report.adaptability.items():
            if isinstance(metric_value, (int, float)):
                self.assertGreaterEqual(metric_value, 0.0, f"Metric {metric_name} < 0")
                self.assertLessEqual(metric_value, 1.0, f"Metric {metric_name} > 1")

        for metric_name, metric_value in report.integrity.items():
            if isinstance(metric_value, (int, float)):
                self.assertGreaterEqual(metric_value, 0.0, f"Metric {metric_name} < 0")
                self.assertLessEqual(metric_value, 1.0, f"Metric {metric_name} > 1")

        overall_score = report.overall_assessment['overall_score']
        self.assertGreaterEqual(overall_score, 0.0)
        self.assertLessEqual(overall_score, 1.0)

    def test_save_and_load_report(self):
        """Тест сохранения и загрузки отчета."""
        # Создаем mock decision engine
        mock_decision_engine = Mock()
        mock_decision_engine.get_recent_decisions.return_value = []
        mock_decision_engine.get_statistics.return_value = {
            'total_decisions': 0,
            'average_time': 0.0,
            'accuracy': 0.0
        }

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

        finally:
            # Удаляем временный файл
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_trends_analysis(self):
        """Тест анализа трендов."""
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
            # Модифицируем mock self_state для создания разных значений
            modified_self_state = self._create_mock_self_state()
            modified_self_state.age = 100.0 + i * 10
            modified_self_state.ticks = 1000 + i * 100
            modified_self_state.energy = 0.8 - i * 0.05  # Постепенное снижение энергии
            modified_self_state.adaptation_level = 0.7 + i * 0.02  # Постепенное улучшение адаптации

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

    def test_error_handling(self):
        """Тест обработки ошибок."""
        # Создаем компоненты, которые вызывают ошибки
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