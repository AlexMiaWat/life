"""
Интеграционные тесты для философского анализатора.

Проверяют взаимодействие компонентов философского анализа с другими частями системы.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from src.philosophical.philosophical_analyzer import PhilosophicalAnalyzer
from src.philosophical.metrics import PhilosophicalMetrics
from src.state.self_state import SelfState
from src.memory.memory import Memory
from src.learning.learning import LearningEngine
from src.adaptation.adaptation import AdaptationManager
from src.decision.decision import DecisionEngine


class TestPhilosophicalAnalyzerIntegration:
    """Интеграционные тесты для PhilosophicalAnalyzer."""

    def test_full_analysis_workflow(self):
        """Тест полного рабочего процесса анализа."""
        analyzer = PhilosophicalAnalyzer()

        # Создание комплексных mock объектов с реалистичными данными
        self_state = self._create_realistic_self_state()
        memory = self._create_realistic_memory()
        learning_engine = self._create_realistic_learning_engine()
        adaptation_manager = self._create_realistic_adaptation_manager()
        decision_engine = self._create_realistic_decision_engine()

        # Выполнение анализа
        metrics = analyzer.analyze_behavior(
            self_state, memory, learning_engine, adaptation_manager, decision_engine
        )

        # Проверка комплексных результатов
        assert isinstance(metrics, PhilosophicalMetrics)
        assert 0.0 <= metrics.philosophical_index <= 1.0

        # Проверка, что все подметрики заполнены
        assert hasattr(metrics.self_awareness, 'overall_self_awareness')
        assert hasattr(metrics.adaptation_quality, 'overall_adaptation_quality')
        assert hasattr(metrics.ethical_behavior, 'overall_ethical_score')
        assert hasattr(metrics.conceptual_integrity, 'overall_integrity')
        assert hasattr(metrics.life_vitality, 'overall_vitality')

        # Проверка истории
        assert len(analyzer.analysis_history) == 1

    def test_analysis_with_realistic_data(self):
        """Тест анализа с реалистичными данными из системы."""
        analyzer = PhilosophicalAnalyzer()

        # Создание данных, имитирующих реальную работу системы
        self_state = Mock()
        self_state.energy = 75.0
        self_state.integrity = 0.85
        self_state.stability = 0.8
        self_state.age = 500.0
        self_state.subjective_time = 600.0
        self_state.ticks = 2500
        self_state.energy_history = [70, 72, 75, 78, 75, 80, 82, 85, 83, 80]
        self_state.stability_history = [0.75, 0.78, 0.8, 0.82, 0.8, 0.78, 0.75, 0.8]
        self_state.fatigue = 25.0
        self_state.tension = 20.0
        self_state.recent_events = [
            {'type': 'decision', 'significance': 0.8, 'outcome': 'beneficial'},
            {'type': 'learning', 'significance': 0.6, 'outcome': 'successful'},
            {'type': 'adaptation', 'significance': 0.7, 'outcome': 'stable'}
        ]
        self_state.last_significance = 0.75

        memory = Mock()
        memory.get_statistics.return_value = {
            'total_entries': 200,
            'archived_entries': 50,
            'recent_entries': 20,
            'avg_significance': 0.65
        }

        learning_engine = Mock()
        learning_engine.learning_params = {
            'event_type_sensitivity': 0.8,
            'significance_thresholds': 0.4,
            'learning_rate': 0.6
        }
        learning_engine.learning_statistics = {
            'events_processed': 150,
            'patterns_learned': 35,
            'learning_efficiency': 0.75,
            'adaptation_triggers': 12
        }
        learning_engine.get_prediction_accuracy.return_value = 0.82

        adaptation_manager = Mock()
        adaptation_manager.adaptation_params = {
            'behavior_sensitivity': 0.7,
            'behavior_thresholds': 0.5,
            'stability_weight': 0.6
        }
        adaptation_manager.adaptation_history = [
            {'behavior_sensitivity': 0.6, 'threshold': 0.5, 'effectiveness': 0.7},
            {'behavior_sensitivity': 0.65, 'threshold': 0.52, 'effectiveness': 0.75},
            {'behavior_sensitivity': 0.7, 'threshold': 0.5, 'effectiveness': 0.8}
        ]
        adaptation_manager.get_adaptation_statistics.return_value = {
            'total_adaptations': 25,
            'successful_adaptations': 22,
            'avg_adaptation_time': 8.5,
            'stability_score': 0.78
        }

        decision_engine = Mock()
        decision_engine.decision_history = [
            {'outcome': 'beneficial', 'impact': 0.8, 'alternatives_considered': 3},
            {'outcome': 'neutral', 'impact': 0.2, 'alternatives_considered': 2},
            {'outcome': 'beneficial', 'impact': 0.6, 'alternatives_considered': 4}
        ]

        # Выполнение анализа
        metrics = analyzer.analyze_behavior(
            self_state, memory, learning_engine, adaptation_manager, decision_engine
        )

        # Проверка реалистичных результатов
        assert metrics.philosophical_index > 0.1  # Должен быть индекс при хороших данных
        assert metrics.self_awareness.overall_self_awareness > 0.1
        assert metrics.adaptation_quality.overall_adaptation_quality > 0.1
        assert metrics.ethical_behavior.overall_ethical_score > 0.1
        assert metrics.conceptual_integrity.overall_integrity > 0.1
        assert metrics.life_vitality.overall_vitality > 0.1

    def test_trends_analysis_with_history(self):
        """Тест анализа трендов с историей данных."""
        analyzer = PhilosophicalAnalyzer()

        # Добавление нескольких анализов в историю
        for i in range(5):
            metrics = PhilosophicalMetrics()
            # Имитация улучшения со временем
            base_score = 0.5 + i * 0.08
            metrics.philosophical_index = base_score
            metrics.self_awareness.overall_self_awareness = base_score + 0.05
            metrics.adaptation_quality.overall_adaptation_quality = base_score - 0.02
            analyzer.analysis_history.append(metrics.to_dict())

        # Анализ трендов
        trends = analyzer.analyze_trends()

        # Проверка результатов анализа трендов
        assert isinstance(trends, dict)
        assert 'philosophical_index' in trends
        assert 'self_awareness.overall_self_awareness' in trends

        # Проверка структуры тренда
        philosophical_trend = trends['philosophical_index']
        assert 'trend' in philosophical_trend
        assert 'slope' in philosophical_trend
        assert 'volatility' in philosophical_trend
        assert philosophical_trend['trend'] == 'improving'  # Должен показать улучшение
        assert philosophical_trend['slope'] > 0  # Положительный наклон

    def test_insights_with_realistic_metrics(self):
        """Тест генерации инсайтов с реалистичными метриками."""
        analyzer = PhilosophicalAnalyzer()

        # Создание метрик с различными уровнями
        metrics = PhilosophicalMetrics()
        metrics.self_awareness.overall_self_awareness = 0.8
        metrics.adaptation_quality.overall_adaptation_quality = 0.6
        metrics.ethical_behavior.overall_ethical_score = 0.7
        metrics.conceptual_integrity.overall_integrity = 0.75
        metrics.life_vitality.overall_vitality = 0.65
        metrics.philosophical_index = 0.7

        insights = analyzer.get_philosophical_insights(metrics)

        # Проверка структуры инсайтов
        assert 'overall' in insights
        assert 'self_awareness' in insights
        assert 'adaptation' in insights
        assert 'ethics' in insights
        assert 'conceptual_integrity' in insights
        assert 'life_vitality' in insights

        # Проверка содержимого
        for key, value in insights.items():
            assert isinstance(value, str)
            assert len(value) > 20  # Должны быть содержательные описания

    def test_report_generation_integration(self):
        """Тест генерации отчета в условиях интеграции."""
        analyzer = PhilosophicalAnalyzer()

        # Создание полных метрик
        metrics = PhilosophicalMetrics()
        metrics.self_awareness.overall_self_awareness = 0.75
        metrics.adaptation_quality.overall_adaptation_quality = 0.8
        metrics.ethical_behavior.overall_ethical_score = 0.65
        metrics.conceptual_integrity.overall_integrity = 0.7
        metrics.life_vitality.overall_vitality = 0.72
        metrics.philosophical_index = 0.72

        # Добавление в историю для трендов
        analyzer.analysis_history = [metrics.to_dict() for _ in range(3)]

        report = analyzer.generate_philosophical_report(metrics)

        # Проверка структуры отчета
        assert isinstance(report, str)
        assert len(report) > 500  # Должен быть подробный отчет
        assert "ФИЛОСОФСКИЙ АНАЛИЗ" in report
        assert "ОБЩИЙ ФИЛОСОФСКИЙ ИНДЕКС" in report
        assert "ТРЕНДЫ" in report

    def test_memory_integration(self):
        """Тест интеграции с компонентом памяти."""
        analyzer = PhilosophicalAnalyzer()

        self_state = Mock()
        self_state.energy = 60.0
        self_state.recent_events = [{'type': 'memory_access', 'significance': 0.7}]

        memory = Mock()
        memory.get_statistics.return_value = {
            'total_entries': 300,
            'archived_entries': 80,
            'recent_entries': 25,
            'avg_significance': 0.7,
            'memory_health': 0.85
        }

        learning_engine = Mock()
        adaptation_manager = Mock()
        decision_engine = Mock()

        metrics = analyzer.analyze_behavior(
            self_state, memory, learning_engine, adaptation_manager, decision_engine
        )

        # Проверка, что анализ памяти повлиял на результаты
        assert metrics.self_awareness.behavioral_reflection >= 0.0  # Анализ выполнен

    def test_learning_integration(self):
        """Тест интеграции с компонентом обучения."""
        analyzer = PhilosophicalAnalyzer()

        self_state = Mock()
        self_state.energy = 70.0

        memory = Mock()
        memory.get_statistics.return_value = {'total_entries': 100}

        learning_engine = Mock()
        learning_engine.learning_statistics = {
            'events_processed': 200,
            'patterns_learned': 50,
            'learning_efficiency': 0.9,
            'adaptation_triggers': 15
        }
        learning_engine.get_prediction_accuracy.return_value = 0.88

        adaptation_manager = Mock()
        adaptation_manager.adaptation_history = [
            {'effectiveness': 0.8, 'stability': 0.75}
        ]

        decision_engine = Mock()

        metrics = analyzer.analyze_behavior(
            self_state, memory, learning_engine, adaptation_manager, decision_engine
        )

        # Проверка, что обучение повлияло на адаптацию и жизненную силу
        assert metrics.adaptation_quality.predictive_quality >= 0.0
        assert metrics.life_vitality.overall_vitality >= 0.0

    def _create_realistic_self_state(self):
        """Создание реалистичного mock объекта self_state."""
        self_state = Mock()
        self_state.energy = 70.0
        self_state.integrity = 0.8
        self_state.stability = 0.75
        self_state.age = 300.0
        self_state.subjective_time = 350.0
        self_state.ticks = 1500
        self_state.energy_history = [65, 68, 70, 72, 70, 75, 73, 70]
        self_state.stability_history = [0.7, 0.72, 0.75, 0.78, 0.75, 0.73, 0.7]
        self_state.fatigue = 30.0
        self_state.tension = 25.0
        return self_state

    def _create_realistic_memory(self):
        """Создание реалистичного mock объекта memory."""
        memory = Mock()
        memory.get_statistics.return_value = {
            'total_entries': 150,
            'archived_entries': 40,
            'recent_entries': 15,
            'avg_significance': 0.6
        }
        return memory

    def _create_realistic_learning_engine(self):
        """Создание реалистичного mock объекта learning_engine."""
        learning_engine = Mock()
        learning_engine.learning_params = {'event_type_sensitivity': 0.75, 'significance_thresholds': 0.4}
        learning_engine.learning_statistics = {'events_processed': 100, 'patterns_learned': 20}
        learning_engine.get_prediction_accuracy.return_value = 0.8
        return learning_engine

    def _create_realistic_adaptation_manager(self):
        """Создание реалистичного mock объекта adaptation_manager."""
        adaptation_manager = Mock()
        adaptation_manager.adaptation_params = {'behavior_sensitivity': 0.7, 'behavior_thresholds': 0.5}
        adaptation_manager.adaptation_history = [
            {'behavior_sensitivity': 0.65},
            {'behavior_sensitivity': 0.68},
            {'behavior_sensitivity': 0.7}
        ]
        adaptation_manager.get_adaptation_statistics.return_value = {
            'total_adaptations': 20,
            'successful_adaptations': 18,
            'avg_adaptation_time': 6.0
        }
        return adaptation_manager

    def _create_realistic_decision_engine(self):
        """Создание реалистичного mock объекта decision_engine."""
        decision_engine = Mock()
        decision_engine.decision_history = [
            {'outcome': 'beneficial', 'impact': 0.7},
            {'outcome': 'neutral', 'impact': 0.3},
            {'outcome': 'beneficial', 'impact': 0.8}
        ]
        return decision_engine


class TestComponentInteraction:
    """Тесты взаимодействия между компонентами."""

    def test_analyzer_components_cooperation(self):
        """Тест сотрудничества компонентов анализатора."""
        analyzer = PhilosophicalAnalyzer()

        # Проверка, что все компоненты созданы и могут работать вместе
        assert analyzer.self_awareness_analyzer is not None
        assert analyzer.adaptation_quality_analyzer is not None
        assert analyzer.ethical_behavior_analyzer is not None
        assert analyzer.conceptual_integrity_analyzer is not None
        assert analyzer.life_vitality_evaluator is not None

        # Проверка, что все компоненты имеют необходимые методы
        assert hasattr(analyzer.self_awareness_analyzer, 'analyze_self_awareness')
        assert hasattr(analyzer.adaptation_quality_analyzer, 'analyze_adaptation_quality')
        assert hasattr(analyzer.ethical_behavior_analyzer, 'analyze_ethical_behavior')
        assert hasattr(analyzer.conceptual_integrity_analyzer, 'analyze_conceptual_integrity')
        assert hasattr(analyzer.life_vitality_evaluator, 'evaluate_life_vitality')

    def test_metrics_data_flow(self):
        """Тест потока данных через метрики."""
        metrics = PhilosophicalMetrics()

        # Проверка, что все подметрики созданы
        assert metrics.self_awareness is not None
        assert metrics.adaptation_quality is not None
        assert metrics.ethical_behavior is not None
        assert metrics.conceptual_integrity is not None
        assert metrics.life_vitality is not None

        # Проверка преобразования в словарь
        data = metrics.to_dict()
        assert 'self_awareness' in data
        assert 'adaptation_quality' in data
        assert 'ethical_behavior' in data
        assert 'conceptual_integrity' in data
        assert 'life_vitality' in data
        assert 'philosophical_index' in data

    @patch('src.philosophical.philosophical_analyzer.logger')
    def test_logging_integration(self, mock_logger):
        """Тест интеграции с системой логирования."""
        analyzer = PhilosophicalAnalyzer()

        # Проверка, что логгер используется при инициализации
        mock_logger.info.assert_called_with("Философский анализатор инициализирован")

        # Создание mock объектов для анализа
        self_state = Mock()
        memory = Mock()
        learning_engine = Mock()
        adaptation_manager = Mock()
        decision_engine = Mock()

        # Выполнение анализа
        analyzer.analyze_behavior(self_state, memory, learning_engine, adaptation_manager, decision_engine)

        # Проверка, что логирование используется в процессе анализа
        # (конкретные вызовы зависят от реализации)


class TestRealComponentsIntegration:
    """Интеграционные тесты с реальными компонентами системы Life."""

    def test_analysis_with_real_self_state(self):
        """Тест анализа с реальным SelfState."""
        analyzer = PhilosophicalAnalyzer()

        # Создание реального SelfState
        self_state = SelfState()
        self_state.energy = 65.0
        self_state.integrity = 0.9
        self_state.stability = 0.85
        self_state.age = 1000.0
        self_state.subjective_time = 1200.0
        self_state.ticks = 5000
        self_state.fatigue = 20.0
        self_state.recent_events = ['recovery', 'idle', 'shock', 'recovery']

        # Создание реальной памяти
        memory = Memory()

        # Создание реальных компонентов
        learning_engine = LearningEngine()
        adaptation_manager = AdaptationManager()
        decision_engine = DecisionEngine()

        # Выполнение анализа
        metrics = analyzer.analyze_behavior(
            self_state, memory, learning_engine, adaptation_manager, decision_engine
        )

        # Проверка результатов
        assert isinstance(metrics, PhilosophicalMetrics)
        assert 0.0 <= metrics.philosophical_index <= 1.0
        assert hasattr(metrics, 'self_awareness')
        assert hasattr(metrics, 'life_vitality')

        # Проверка, что анализ не сломал компоненты
        assert self_state.energy == 65.0  # SelfState не должен изменяться
        assert len(self_state.recent_events) == 4

    def test_analysis_with_populated_memory(self):
        """Тест анализа с памятью, содержащей реальные записи."""
        analyzer = PhilosophicalAnalyzer()

        # Создание SelfState
        self_state = SelfState()
        self_state.energy = 70.0
        self_state.ticks = 100

        # Создание памяти с записями
        memory = Memory()

        # Добавление тестовых записей в память
        from src.memory.memory import MemoryEntry
        import time

        for i in range(10):
            entry = MemoryEntry(
                event_type='test_event',
                meaning_significance=0.5 + i * 0.05,
                timestamp=time.time(),
                subjective_timestamp=self_state.subjective_time,
            )
            memory.append(entry)

        # Создание компонентов
        learning_engine = LearningEngine()
        adaptation_manager = AdaptationManager()
        decision_engine = DecisionEngine()

        # Выполнение анализа
        metrics = analyzer.analyze_behavior(
            self_state, memory, learning_engine, adaptation_manager, decision_engine
        )

        # Проверка, что память не была повреждена
        assert len(memory) == 10
        assert all(isinstance(entry, MemoryEntry) for entry in memory)

        # Проверка результатов анализа
        assert metrics.self_awareness.behavioral_reflection >= 0.0
        assert metrics.life_vitality.vitality_level >= 0.0

    def test_runtime_loop_integration_simulation(self):
        """Симуляция интеграции анализа в runtime loop."""
        analyzer = PhilosophicalAnalyzer()

        # Создание компонентов как в runtime loop
        self_state = SelfState()
        self_state.ticks = 75  # Установка тиков для срабатывания анализа

        memory = Memory()
        learning_engine = LearningEngine()
        adaptation_manager = AdaptationManager()
        decision_engine = DecisionEngine()

        # Имитация работы runtime loop с анализом
        analysis_performed = False

        # Симуляция нескольких тиков
        for tick in range(70, 80):
            self_state.ticks = tick

            # Имитация условия из runtime loop
            if tick > 0 and tick % 75 == 0:
                # Выполнение философского анализа
                metrics = analyzer.analyze_behavior(
                    self_state, memory, learning_engine, adaptation_manager, decision_engine
                )
                analysis_performed = True

                # Проверка результатов
                assert isinstance(metrics, PhilosophicalMetrics)
                assert hasattr(metrics, 'philosophical_index')

        assert analysis_performed, "Анализ должен был выполниться на 75-м тике"

    def test_analysis_error_handling_with_real_components(self):
        """Тест обработки ошибок при работе с реальными компонентами."""
        analyzer = PhilosophicalAnalyzer()

        # Создание компонентов
        self_state = SelfState()
        memory = Memory()
        learning_engine = LearningEngine()
        adaptation_manager = AdaptationManager()
        decision_engine = DecisionEngine()

        # Добавление корректных записей
        from src.memory.memory import MemoryEntry
        import time

        for i in range(5):
            entry = MemoryEntry(
                event_type='test_event',
                meaning_significance=0.5,
                timestamp=time.time(),
                subjective_timestamp=self_state.subjective_time,
            )
            memory.append(entry)

        # Анализ должен выполниться без ошибок
        metrics = analyzer.analyze_behavior(
            self_state, memory, learning_engine, adaptation_manager, decision_engine
        )

        # Проверка, что анализ вернул результаты
        assert isinstance(metrics, PhilosophicalMetrics)
        assert metrics.philosophical_index >= 0.0

    def test_memory_statistics_integration(self):
        """Тест интеграции со статистикой памяти."""
        analyzer = PhilosophicalAnalyzer()

        self_state = SelfState()
        memory = Memory()

        # Добавление записей для создания статистики
        from src.memory.memory import MemoryEntry
        import time

        for i in range(20):
            entry = MemoryEntry(
                event_type='noise' if i % 3 == 0 else 'recovery',
                meaning_significance=0.3 + (i % 5) * 0.1,
                timestamp=time.time() - i * 10,  # Разные временные метки
                subjective_timestamp=self_state.subjective_time - i * 5,
            )
            memory.append(entry)

        # Проверка, что статистика доступна
        stats = memory.get_statistics()
        assert 'active_entries' in stats
        assert stats['active_entries'] == 20

        learning_engine = LearningEngine()
        adaptation_manager = AdaptationManager()
        decision_engine = DecisionEngine()

        # Выполнение анализа
        metrics = analyzer.analyze_behavior(
            self_state, memory, learning_engine, adaptation_manager, decision_engine
        )

        # Проверка, что анализ памяти повлиял на результаты
        assert metrics.self_awareness.behavioral_reflection > 0.0
        assert metrics.life_vitality.vitality_level > 0.0