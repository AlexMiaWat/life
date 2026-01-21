"""
Unit тесты для ProceduralMemoryStore.
"""

import pytest
import time
from unittest.mock import Mock

from src.experimental.memory_hierarchy.procedural_store import ProceduralMemoryStore, ProceduralPattern, DecisionPattern
from src.observability.structured_logger import StructuredLogger


class TestProceduralPattern:
    """Тесты для ProceduralPattern."""

    def test_pattern_creation(self):
        """Тест создания паттерна."""
        pattern = ProceduralPattern(
            pattern_id="test_pattern_1",
            name="Test Pattern",
            description="A test procedural pattern",
            action_sequence=[
                ("action_1", {"param": "value1"}),
                ("action_2", {"param": "value2"})
            ],
            trigger_conditions={"condition1": "value1"}
        )

        assert pattern.pattern_id == "test_pattern_1"
        assert pattern.name == "Test Pattern"
        assert len(pattern.action_sequence) == 2
        assert pattern.trigger_conditions == {"condition1": "value1"}
        assert pattern.success_count == 0
        assert pattern.failure_count == 0
        assert pattern.automation_level == 0.0

    def test_pattern_execution_success(self):
        """Тест успешного выполнения паттерна."""
        pattern = ProceduralPattern(
            pattern_id="test_pattern_1",
            name="Test Pattern",
            description="A test pattern",
            action_sequence=[("test_action", {"param": "value"})]
        )

        context = {"test": "context"}
        result = pattern.execute(context)

        assert result["success"] is True
        assert result["pattern_id"] == "test_pattern_1"
        assert "execution_time" in result
        assert pattern.success_count == 1
        assert pattern.total_executions == 1
        assert pattern.last_execution > 0

    def test_pattern_execution_failure(self):
        """Тест неудачного выполнения паттерна."""
        pattern = ProceduralPattern(
            pattern_id="test_pattern_1",
            name="Test Pattern",
            description="A test pattern",
            action_sequence=[("failing_action", {"param": "value"})]
        )

        # Имитируем исключение в _execute_sequence
        original_execute = pattern._execute_sequence
        def failing_execute(context):
            raise ValueError("Test failure")
        pattern._execute_sequence = failing_execute

        context = {"test": "context"}
        result = pattern.execute(context)

        assert result["success"] is False
        assert result["error"] == "Test failure"
        assert pattern.failure_count == 1
        assert pattern.total_executions == 1

        # Восстанавливаем метод
        pattern._execute_sequence = original_execute

    def test_automation_eligibility(self):
        """Тест проверки возможности автоматизации."""
        pattern = ProceduralPattern(
            pattern_id="test_pattern_1",
            name="Test Pattern",
            description="A test pattern",
            action_sequence=[("action", {})],
            automation_level=0.5,
            min_automation_threshold=0.8
        )

        # Низкий уровень автоматизации
        assert not pattern.can_automate({})

        # Высокий уровень автоматизации
        pattern.automation_level = 0.9
        pattern.success_count = 5
        pattern.total_executions = 5
        assert pattern.can_automate({})

    def test_effectiveness_calculation(self):
        """Тест расчета эффективности паттерна."""
        pattern = ProceduralPattern(
            pattern_id="test_pattern_1",
            name="Test Pattern",
            description="A test pattern"
        )

        # Без выполнений
        assert pattern.get_effectiveness_score() == 0.0

        # С успешными выполнениями
        pattern.success_count = 8
        pattern.total_executions = 10
        pattern.automation_level = 0.7

        effectiveness = pattern.get_effectiveness_score()
        assert effectiveness > 0
        assert effectiveness <= 1.0


class TestDecisionPattern:
    """Тесты для DecisionPattern."""

    def test_decision_pattern_creation(self):
        """Тест создания паттерна решений."""
        pattern = DecisionPattern(
            pattern_id="decision_1",
            conditions={"energy": "low", "stability": "high"},
            decision="rest",
            outcome="recovered",
            confidence=0.8
        )

        assert pattern.pattern_id == "decision_1"
        assert pattern.conditions == {"energy": "low", "stability": "high"}
        assert pattern.decision == "rest"
        assert pattern.outcome == "recovered"
        assert pattern.confidence == 0.8
        assert pattern.usage_count == 0

    def test_pattern_matching(self):
        """Тест сопоставления паттерна с условиями."""
        pattern = DecisionPattern(
            pattern_id="decision_1",
            conditions={"energy": "low", "stability": "high"},
            decision="rest",
            outcome="recovered"
        )

        # Полное совпадение
        assert pattern.matches({"energy": "low", "stability": "high"}) == 1.0

        # Частичное совпадение
        assert pattern.matches({"energy": "low"}) == 0.5

        # Нет совпадения
        assert pattern.matches({"energy": "high"}) == 0.0

        # Пустые условия
        assert pattern.matches({}) == 0.0


class TestProceduralMemoryStore:
    """Тесты для ProceduralMemoryStore."""

    @pytest.fixture
    def logger(self):
        """Фикстура для логгера."""
        return Mock(spec=StructuredLogger)

    @pytest.fixture
    def store(self, logger):
        """Фикстура для хранилища."""
        return ProceduralMemoryStore(logger=logger)

    def test_store_initialization(self, store):
        """Тест инициализации хранилища."""
        assert len(store._patterns) == 0
        assert len(store._decision_patterns) == 0
        assert store._stats["total_patterns"] == 0
        assert store._stats["total_decision_patterns"] == 0

    def test_add_pattern(self, store, logger):
        """Тест добавления паттерна."""
        pattern = ProceduralPattern(
            pattern_id="test_pattern_1",
            name="Test Pattern",
            description="A test pattern",
            action_sequence=[("action", {"param": "value"})]
        )

        store.add_pattern(pattern)

        assert "test_pattern_1" in store._patterns
        assert store._patterns["test_pattern_1"] == pattern
        assert store._stats["total_patterns"] == 1
        assert ("action",) in store._action_sequences
        logger.log_event.assert_called_once()

    def test_add_duplicate_pattern(self, store):
        """Тест добавления дублирующегося паттерна."""
        pattern1 = ProceduralPattern(
            pattern_id="test_pattern_1",
            name="Test Pattern",
            description="Original",
            action_sequence=[("action", {})],
            success_count=2
        )

        pattern2 = ProceduralPattern(
            pattern_id="test_pattern_1",
            name="Test Pattern",
            description="Updated",
            action_sequence=[("action", {})],
            success_count=3
        )

        store.add_pattern(pattern1)
        store.add_pattern(pattern2)

        # Паттерн должен быть обновлен
        assert store._patterns["test_pattern_1"].success_count == 5  # 2 + 3
        assert store._patterns["test_pattern_1"].description == "Updated"
        assert store._stats["total_patterns"] == 1

    def test_get_pattern(self, store):
        """Тест получения паттерна."""
        pattern = ProceduralPattern(
            pattern_id="test_pattern_1",
            name="Test Pattern",
            description="A test pattern",
            action_sequence=[("action", {})]
        )
        store.add_pattern(pattern)

        retrieved = store.get_pattern("test_pattern_1")
        assert retrieved == pattern

        # Несуществующий паттерн
        assert store.get_pattern("nonexistent") is None

    def test_find_applicable_patterns(self, store):
        """Тест поиска применимых паттернов."""
        pattern1 = ProceduralPattern(
            pattern_id="p1",
            name="Pattern 1",
            description="Pattern with condition A",
            action_sequence=[("action1", {})],
            trigger_conditions={"condition": "A"},
            automation_level=0.9
        )

        pattern2 = ProceduralPattern(
            pattern_id="p2",
            name="Pattern 2",
            description="Pattern with condition B",
            action_sequence=[("action2", {})],
            trigger_conditions={"condition": "B"},
            automation_level=0.5
        )

        store.add_pattern(pattern1)
        store.add_pattern(pattern2)

        # Поиск для условия A
        applicable = store.find_applicable_patterns({"condition": "A"})
        assert len(applicable) == 1
        assert applicable[0][0] == pattern1
        assert applicable[0][1] > 0  # Релевантность

        # Поиск для условия B
        applicable = store.find_applicable_patterns({"condition": "B"})
        assert len(applicable) == 1
        assert applicable[0][0] == pattern2

        # Поиск без подходящих паттернов
        applicable = store.find_applicable_patterns({"condition": "C"})
        assert len(applicable) == 0

    def test_execute_best_pattern(self, store):
        """Тест выполнения лучшего паттерна."""
        pattern = ProceduralPattern(
            pattern_id="p1",
            name="Good Pattern",
            description="A good pattern",
            action_sequence=[("good_action", {})],
            trigger_conditions={"state": "good"},
            automation_level=0.9,
            success_count=5,
            total_executions=5
        )

        store.add_pattern(pattern)

        # Выполнение подходящего паттерна
        result = store.execute_best_pattern({"state": "good"})
        assert result is not None
        assert result["success"] is True
        assert result["pattern_id"] == "p1"
        assert store._stats["automated_executions"] == 1

        # Выполнение неподходящего паттерна
        result = store.execute_best_pattern({"state": "bad"})
        assert result is None
        assert store._stats["manual_executions"] == 1

    def test_learn_from_experience(self, store, logger):
        """Тест обучения на опыте."""
        context = {"situation": "crisis"}
        actions = [("action1", {"param": "value1"})]
        outcome = "resolved"
        success = True

        initial_patterns = len(store._patterns)

        store.learn_from_experience(context, actions, outcome, success)

        # Должен быть добавлен новый паттерн
        assert len(store._patterns) == initial_patterns + 1

        # Проверим созданный паттерн
        new_pattern = list(store._patterns.values())[0]
        assert new_pattern.trigger_conditions == context
        assert new_pattern.action_sequence == actions
        assert new_pattern.success_count == 1
        assert new_pattern.automation_level == 0.3  # Начальный уровень для успешных

        logger.log_event.assert_called_once()

    def test_get_decision_recommendation(self, store):
        """Тест получения рекомендации по решению."""
        pattern = DecisionPattern(
            pattern_id="d1",
            conditions={"energy": "low", "threat": "high"},
            decision="defend",
            outcome="survived",
            confidence=0.9
        )

        store._decision_patterns["hash_key"] = pattern

        # Получение рекомендации
        recommendation = store.get_decision_recommendation({"energy": "low", "threat": "high"})
        assert recommendation == "defend"

        # Нет подходящих рекомендаций
        recommendation = store.get_decision_recommendation({"energy": "high"})
        assert recommendation is None

    def test_optimize_patterns(self, store):
        """Тест оптимизации паттернов."""
        # Эффективный паттерн
        good_pattern = ProceduralPattern(
            pattern_id="good",
            name="Good Pattern",
            description="Good",
            action_sequence=[("action", {})],
            success_count=9,
            total_executions=10,
            automation_level=0.8
        )

        # Неэффективный паттерн
        bad_pattern = ProceduralPattern(
            pattern_id="bad",
            name="Bad Pattern",
            description="Bad",
            action_sequence=[("action", {})],
            success_count=1,
            total_executions=10,
            automation_level=0.1
        )

        store.add_pattern(good_pattern)
        store.add_pattern(bad_pattern)

        initial_count = len(store._patterns)
        removed = store.optimize_patterns()

        # Неэффективный паттерн должен быть удален
        assert len(store._patterns) < initial_count
        assert "bad" not in store._patterns
        assert "good" in store._patterns
        assert removed > 0

    def test_get_statistics(self, store):
        """Тест получения статистики."""
        pattern = ProceduralPattern(
            pattern_id="p1",
            name="Test Pattern",
            description="Test",
            action_sequence=[("action", {})],
            success_count=7,
            total_executions=10,
            automation_level=0.8
        )

        store.add_pattern(pattern)
        store._stats["automated_executions"] = 5
        store._stats["manual_executions"] = 3

        stats = store.get_statistics()

        assert stats["total_patterns"] == 1
        assert stats["automated_executions"] == 5
        assert stats["manual_executions"] == 3
        assert stats["automation_rate"] == 5/8  # 5/(5+3)
        assert stats["average_pattern_effectiveness"] > 0

    def test_clear_store(self, store):
        """Тест очистки хранилища."""
        # Добавляем данные
        pattern = ProceduralPattern(
            pattern_id="p1",
            name="Test Pattern",
            description="Test",
            action_sequence=[("action", {})]
        )
        store.add_pattern(pattern)
        store._learn_decision_pattern({"test": "conditions"}, "decision", "outcome", True)

        # Очищаем
        store.clear_store()

        assert len(store._patterns) == 0
        assert len(store._decision_patterns) == 0
        assert store._stats["total_patterns"] == 0
        assert store._stats["total_decision_patterns"] == 0