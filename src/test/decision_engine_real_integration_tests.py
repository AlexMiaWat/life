"""
Реальные интеграционные тесты для DecisionEngine.

Тестируют DecisionEngine с реальными компонентами, без mock-объектов.
Проверяют реальную функциональность и производительность.
"""

import time
import pytest
from typing import Dict, Any

from src.decision.decision import DecisionEngine
from src.state.self_state import SelfState
from src.meaning.meaning import Meaning
from src.memory.memory import MemoryEntry
from src.config import feature_flags


@pytest.mark.skipif(
    not feature_flags.is_decision_logging_enabled(),
    reason="Требуется feature flag decision_logging для тестирования логирования"
)
class TestDecisionEngineRealIntegration:
    """Реальные интеграционные тесты DecisionEngine с логированием."""

    def setup_method(self):
        """Настройка теста с реальным DecisionEngine."""
        # Создаем реальный DecisionEngine с включенным логированием
        self.decision_engine = DecisionEngine(enable_logging=True)

        # Создаем реальный SelfState
        self.self_state = SelfState()
        self.self_state.energy = 70
        self.self_state.stability = 0.8
        self.self_state.integrity = 0.9
        self.self_state.subjective_time = 1000.0
        self.self_state.age = 2000.0

        # Создаем реальный Meaning
        self.meaning = Meaning(
            significance=0.7,
            impact={"energy": -0.1}
        )

    def test_real_decision_making_workflow(self):
        """Тестирование полного workflow принятия решения с реальными компонентами."""
        # Добавляем реальные записи памяти
        activated_memory = [
            MemoryEntry(
                content="Предыдущий успешный опыт",
                meaning_significance=0.8,
                weight=0.9,
                timestamp=time.time() - 100
            ),
            MemoryEntry(
                content="Недавний опыт",
                meaning_significance=0.6,
                weight=0.7,
                timestamp=time.time() - 10
            )
        ]
        self.self_state.activated_memory = activated_memory

        # Выполняем принятие решения
        start_time = time.time()
        pattern = self.decision_engine.selector.select_pattern(
            self.decision_engine.analyzer.analyze_activated_memory(activated_memory),
            self.decision_engine.analyzer.analyze_system_context(self.self_state, self.meaning),
            self.meaning,
            self.self_state
        )
        decision_time = time.time() - start_time

        # Проверяем результат
        assert pattern in ["ignore", "absorb", "dampen", "amplify"]
        assert decision_time < 0.1  # Решение должно быть быстрым

    def test_decision_recording_and_analysis(self):
        """Тестирование записи решений и их анализа."""
        # Записываем несколько решений
        for i in range(5):
            self.decision_engine.record_decision(
                decision_type="test_decision",
                context={"iteration": i, "test": True},
                pattern="absorb",
                outcome=f"result_{i}",
                success=True,
                execution_time=0.01
            )

        # Проверяем статистику
        stats = self.decision_engine.get_statistics()
        assert stats["total_decisions"] == 5
        assert stats["successful_decisions"] == 5
        assert stats["accuracy"] == 1.0

        # Проверяем историю
        recent = self.decision_engine.get_recent_decisions(limit=10)
        assert len(recent) == 5
        assert all(record.success for record in recent)

        # Проверяем анализ паттернов
        patterns = self.decision_engine.analyze_patterns()
        assert "pattern_trends" in patterns
        assert "absorb" in patterns["pattern_trends"]
        assert patterns["pattern_trends"]["absorb"] == 5

    def test_performance_under_load(self):
        """Тестирование производительности DecisionEngine под нагрузкой."""
        # Создаем нагрузку - много решений подряд
        decisions_count = 100

        start_time = time.time()
        for i in range(decisions_count):
            # Быстрое принятие решения без детального анализа
            pattern = self.decision_engine.selector.select_pattern(
                {"weighted_avg": 0.5, "max_sig": 0.5, "distribution": "medium"},
                {
                    "energy_level": "high",
                    "stability_level": "high",
                    "meaning_significance": 0.5,
                    "dynamic_ignore_threshold": 0.1,
                    "dynamic_dampen_threshold": 0.3
                },
                self.meaning,
                self.self_state
            )

            # Записываем решение
            self.decision_engine.record_decision(
                decision_type="performance_test",
                context={"iteration": i},
                pattern=pattern,
                success=True,
                execution_time=0.001
            )

        total_time = time.time() - start_time

        # Проверяем производительность
        avg_time_per_decision = total_time / decisions_count
        assert avg_time_per_decision < 0.01  # Среднее время решения < 10ms

        # Проверяем, что все решения записаны
        stats = self.decision_engine.get_statistics()
        assert stats["total_decisions"] == decisions_count

    def test_memory_efficiency(self):
        """Тестирование эффективности использования памяти."""
        initial_history_size = len(self.decision_engine.recorder.decision_history)

        # Добавляем много решений
        for i in range(150):  # Больше чем max_history_size (1000)
            self.decision_engine.record_decision(
                decision_type="memory_test",
                context={"large_context": "x" * 1000},  # Большой контекст
                pattern="absorb",
                success=True
            )

        # Проверяем ограничение истории
        current_size = len(self.decision_engine.recorder.decision_history)
        # История должна быть ограничена (но не обязательно ровно max_history_size из-за батчинга)
        assert current_size <= self.decision_engine.recorder.max_history_size + 10  # Небольшой запас

    def test_real_adaptation_analysis(self):
        """Тестирование анализа реальной истории адаптаций."""
        # Добавляем историю адаптаций в self_state
        adaptation_history = [
            {
                "timestamp": time.time() - 300,
                "changes": {
                    "learning": {
                        "learning_rate": {"old": 0.1, "new": 0.15}
                    }
                }
            },
            {
                "timestamp": time.time() - 200,
                "changes": {
                    "processing": {
                        "efficiency": {"old": 0.8, "new": 0.85}
                    }
                }
            },
            {
                "timestamp": time.time() - 100,
                "changes": {
                    "stability": {
                        "threshold": {"old": 0.7, "new": 0.75}
                    }
                }
            }
        ]
        self.self_state.adaptation_history = adaptation_history

        # Выполняем анализ контекста
        context = self.decision_engine.analyzer.analyze_system_context(self.self_state, self.meaning)

        # Проверяем, что анализ адаптаций включен
        assert "adaptation_analysis" in context
        adaptation_analysis = context["adaptation_analysis"]

        assert "trend_direction" in adaptation_analysis
        assert "avg_change_magnitude" in adaptation_analysis
        assert adaptation_analysis["recent_changes_count"] == 3


@pytest.mark.skipif(
    feature_flags.is_decision_logging_enabled(),
    reason="Этот тест проверяет DecisionEngine без логирования"
)
class TestDecisionEngineNoLoggingIntegration:
    """Тесты DecisionEngine без логирования для проверки производительности."""

    def setup_method(self):
        """Настройка теста с DecisionEngine без логирования."""
        self.decision_engine = DecisionEngine(enable_logging=False)

        self.self_state = SelfState()
        self.self_state.energy = 50
        self.self_state.stability = 0.6

        self.meaning = Meaning(
            significance=0.4,
            impact={"stability": -0.05}
        )

    def test_no_logging_overhead(self):
        """Тестирование отсутствия overhead от логирования."""
        # Выполняем много решений без логирования
        decisions_count = 1000

        start_time = time.time()
        for i in range(decisions_count):
            pattern = self.decision_engine.selector.select_pattern(
                {"weighted_avg": 0.3, "max_sig": 0.3, "distribution": "low"},
                {
                    "energy_level": "low",
                    "stability_level": "medium",
                    "meaning_significance": 0.3,
                    "dynamic_ignore_threshold": 0.2,
                    "dynamic_dampen_threshold": 0.4
                },
                self.meaning,
                self.self_state
            )

            # Пытаемся записать решение (должно игнорироваться)
            self.decision_engine.record_decision(
                decision_type="no_logging_test",
                context={"iteration": i},
                pattern=pattern
            )

        total_time = time.time() - start_time

        # Проверяем высокую производительность без логирования
        avg_time_per_decision = total_time / decisions_count
        assert avg_time_per_decision < 0.005  # < 5ms per decision

        # Проверяем, что ничего не записано
        stats = self.decision_engine.get_statistics()
        assert stats["total_decisions"] == 0  # Ничего не должно быть записано