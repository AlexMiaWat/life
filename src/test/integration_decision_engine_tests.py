"""
Интеграционные тесты для DecisionEngine с реальными компонентами.

Тестируют полную интеграцию DecisionRecorder, DecisionAnalyzer и ResponseSelector.
"""
import pytest
import time
from unittest.mock import Mock

from src.decision.decision import DecisionEngine, decide_response
from src.decision.decision_recorder import DecisionRecorder
from src.decision.decision_analyzer import DecisionAnalyzer
from src.decision.response_selector import ResponseSelector, Pattern
from src.state.self_state import SelfState
from src.meaning.meaning import Meaning
from src.memory.memory import MemoryEntry


class TestDecisionEngineIntegration:
    """Интеграционные тесты для DecisionEngine."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.engine = DecisionEngine(enable_logging=True)

    def test_full_decision_flow(self):
        """Тест полного цикла принятия решения."""
        # Создаем тестовые данные
        self_state = SelfState()
        self_state.energy = 50
        self_state.stability = 0.7
        self_state.integrity = 0.8

        # Добавляем активированную память
        memory_entry = MemoryEntry(
            event_type="cognitive_event",
            meaning_significance=0.6,
            weight=1.0,
            timestamp=time.time(),
            feedback_data={"type": "test"}
        )
        self_state.activated_memory = [memory_entry]

        # Создаем meaning
        meaning = Meaning()
        meaning.significance = 0.4
        meaning.event_type = "cognitive_clarity"

        # Принимаем решение
        pattern = decide_response(self_state, meaning, enable_performance_monitoring=False)

        # Проверяем, что вернулось корректное значение
        assert pattern in ["ignore", "absorb", "dampen", "amplify"]

        # Записываем решение для тестирования логирования
        self.engine.record_decision(
            decision_type="response_selection",
            context={"pattern": pattern, "test": True},
            success=True
        )

        # Проверяем, что решение записано в историю
        recent = self.engine.get_recent_decisions(limit=1)
        assert len(recent) == 1
        assert recent[0]["type"] == "response_selection"
        assert recent[0]["pattern"] == pattern

    def test_performance_monitoring(self):
        """Тест мониторинга производительности."""
        self_state = SelfState()
        meaning = Meaning()

        # Замеряем время выполнения
        start_time = time.time()
        pattern = decide_response(self_state, meaning, enable_performance_monitoring=True)
        end_time = time.time()

        execution_time = end_time - start_time
        # Проверяем, что выполнение не занимает слишком много времени
        assert execution_time < 1.0  # Должно быть быстрее 1 секунды

    def test_statistics_tracking(self):
        """Тест отслеживания статистики решений."""
        # Создаем несколько решений
        self_state = SelfState()
        meaning = Meaning()

        for i in range(10):
            pattern = decide_response(self_state, meaning)
            # Имитируем успех/неуспех
            success = i % 2 == 0  # Каждый второй успешен
            self.engine.record_decision(
                decision_type="test",
                context={"pattern": pattern},
                success=success,
                execution_time=0.01
            )

        # Проверяем статистику
        stats = self.engine.get_statistics()
        assert stats["total_decisions"] == 10
        assert stats["successful_decisions"] == 5
        assert stats["accuracy"] == 0.5

    def test_memory_pressure_handling(self):
        """Тест работы под нагрузкой памяти."""
        # Создаем много записей
        for i in range(1200):  # Больше максимального размера истории
            self.engine.record_decision(
                decision_type=f"test_{i}",
                context={"index": i},
                success=True,
                execution_time=0.001
            )

        # Проверяем, что история ограничена
        recent = self.engine.get_recent_decisions(limit=2000)
        assert len(recent) <= 1000  # Максимальный размер истории


class TestDecisionRecorderIntegration:
    """Интеграционные тесты для DecisionRecorder."""

    def test_feature_flag_control(self):
        """Тест управления логированием через feature flag."""
        # С выключенным логированием
        recorder_disabled = DecisionRecorder(enable_logging=False)
        recorder_disabled.record_decision("test", {}, "ignore")

        assert len(recorder_disabled.get_recent_decisions()) == 0

        # С включенным логированием
        recorder_enabled = DecisionRecorder(enable_logging=True)
        recorder_enabled.record_decision("test", {}, "ignore")

        assert len(recorder_enabled.get_recent_decisions()) == 1

    def test_pattern_analysis(self):
        """Тест анализа паттернов решений."""
        recorder = DecisionRecorder(enable_logging=True)

        # Добавляем решения с разными паттернами
        patterns = ["ignore", "absorb", "dampen", "amplify"] * 5

        for pattern in patterns:
            recorder.record_decision("test", {"type": "test"}, pattern, success=True)

        # Анализируем паттерны
        analysis = recorder.analyze_patterns()
        assert "pattern_trends" in analysis
        assert "success_rates" in analysis
        assert "avg_times" in analysis

        # Проверяем распределение паттернов
        trends = analysis["pattern_trends"]
        for pattern in ["ignore", "absorb", "dampen", "amplify"]:
            assert trends[pattern] == 5


class TestDecisionAnalyzerIntegration:
    """Интеграционные тесты для DecisionAnalyzer."""

    def test_memory_analysis_integration(self):
        """Тест интеграции анализа памяти."""
        analyzer = DecisionAnalyzer()

        # Создаем тестовые записи памяти
        entries = [
            MemoryEntry("1", "content1", 0.8, 1.0, time.time(), {}),
            MemoryEntry("2", "content2", 0.3, 0.5, time.time(), {}),
            MemoryEntry("3", "content3", 0.9, 1.5, time.time(), {}),
        ]

        analysis = analyzer.analyze_activated_memory(entries)

        assert "weighted_avg" in analysis
        assert "max_sig" in analysis
        assert "distribution" in analysis

        # Проверяем корректность расчетов
        expected_weighted_avg = (0.8 * 1.0 + 0.3 * 0.5 + 0.9 * 1.5) / (1.0 + 0.5 + 1.5)
        assert abs(analysis["weighted_avg"] - expected_weighted_avg) < 0.001
        assert analysis["max_sig"] == 0.9
        assert analysis["distribution"] == "high_concentrated"

    def test_system_context_analysis(self):
        """Тест анализа системного контекста."""
        analyzer = DecisionAnalyzer()

        # Создаем состояние системы
        self_state = SelfState()
        self_state.energy = 20  # Низкая энергия
        self_state.stability = 0.8  # Высокая стабильность
        self_state.integrity = 0.9
        self_state.subjective_time = 100
        self_state.age = 120  # Замедленное восприятие времени

        # Создаем meaning
        meaning = Meaning()
        meaning.significance = 0.5
        meaning.event_type = "cognitive_clarity"

        analysis = analyzer.analyze_system_context(self_state, meaning)

        assert analysis["energy_level"] == "low"
        assert analysis["stability_level"] == "high"
        assert analysis["time_perception"] == "slowed"
        assert analysis["event_type"] == "cognitive_clarity"


class TestResponseSelectorIntegration:
    """Интеграционные тесты для ResponseSelector."""

    def test_rule_based_selection(self):
        """Тест выбора на основе правил."""
        selector = ResponseSelector()

        # Тест экстренного игнорирования
        context = {
            "energy_level": "low",
            "weighted_avg": 0.05,
            "meaning_significance": 0.03,
            "dynamic_ignore_threshold": 0.1,
            "distribution": "low",
        }

        pattern = selector.select_pattern({}, context, Mock(), Mock())
        assert pattern == "ignore"

    def test_high_memory_concentration(self):
        """Тест правила высокой концентрации памяти."""
        selector = ResponseSelector()

        context = {
            "distribution": "high_concentrated",
            "max_sig": 0.9,
            "energy_level": "high",
            "stability_level": "medium",
        }

        pattern = selector.select_pattern({}, context, Mock(), Mock())
        assert pattern == "dampen"

    def test_circadian_rhythms(self):
        """Тест циркадных ритмов."""
        selector = ResponseSelector()

        # Ночной контекст
        night_context = {
            "circadian_phase": "night",
            "weighted_avg": 0.05,
            "meaning_significance": 0.03,
            "dynamic_ignore_threshold": 0.1,
            "energy_level": "high",
            "stability_level": "medium",
        }

        pattern = selector.select_pattern({}, night_context, Mock(), Mock())
        assert pattern == "ignore"

    def test_event_type_rules(self):
        """Тест правил по типу события."""
        selector = ResponseSelector()

        # Контекст для шока
        shock_context = {
            "event_type": "shock",
            "weighted_avg": 0.4,
            "meaning_significance": 0.3,
            "dynamic_dampen_threshold": 0.3,
            "energy_level": "high",
            "stability_level": "medium",
        }

        pattern = selector.select_pattern({}, shock_context, Mock(), Mock())
        assert pattern == "dampen"


class TestPerformanceBenchmarks:
    """Тесты производительности для новой архитектуры."""

    def test_decision_speed(self):
        """Тест скорости принятия решений."""
        self_state = SelfState()
        meaning = Meaning()

        # Прогреваем систему
        for _ in range(10):
            decide_response(self_state, meaning)

        # Замеряем производительность
        iterations = 100
        start_time = time.time()

        for _ in range(iterations):
            decide_response(self_state, meaning)

        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / iterations

        # Проверяем, что среднее время меньше 10ms
        assert avg_time < 0.01

        print(f"Performance benchmark: {avg_time:.6f}s per decision")

    def test_memory_efficiency(self):
        """Тест эффективности использования памяти."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Создаем много решений
        engine = DecisionEngine(enable_logging=True)
        self_state = SelfState()
        meaning = Meaning()

        for i in range(1000):
            pattern = decide_response(self_state, meaning)
            engine.record_decision("benchmark", {"pattern": pattern}, success=True)

        final_memory = process.memory_info().rss
        memory_delta = final_memory - initial_memory

        # Проверяем, что прирост памяти разумный (< 50MB)
        assert memory_delta < 50 * 1024 * 1024

        print(f"Memory usage delta: {memory_delta / 1024 / 1024:.2f} MB")


if __name__ == "__main__":
    pytest.main([__file__])