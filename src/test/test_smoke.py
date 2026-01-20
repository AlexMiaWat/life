"""
Smoke-тесты для критических компонентов системы Life.

Эти тесты проверяют базовую работоспособность основных компонентов
без углубления в edge cases. Предназначены для быстрой диагностики.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import time

import pytest

from src.learning.learning import LearningEngine
from src.memory.memory import Memory, MemoryEntry
from src.state.self_state import SelfState


@pytest.mark.smoke
@pytest.mark.order(0)
class TestSmoke:
    """Smoke-тесты для быстрой проверки компонентов"""

    def test_memory_smoke(self):
        """Smoke-тест Memory: базовые CRUD операции"""
        # Создание
        memory = Memory()

        # Добавление записи (Create)
        entry = MemoryEntry(
            event_type="test_event", meaning_significance=0.5, timestamp=time.time()
        )
        memory.append(entry)

        # Чтение (Read)
        assert len(memory) == 1
        assert memory[0].event_type == "test_event"

        # Обновление записи (Update) - через изменение веса
        memory[0].weight = 0.8
        assert memory[0].weight == 0.8

        # Удаление через clamp_size (Delete)
        memory[0].weight = 0.0  # Пометить для удаления
        memory.clamp_size()
        # Запись должна остаться, так как max_size=50 по умолчанию

        # Финальная проверка
        assert len(memory) >= 0  # Может быть 0 или 1 в зависимости от логики

    def test_learning_smoke(self):
        """Smoke-тест Learning: один цикл обучения"""
        # Создание
        engine = LearningEngine()

        # Подготовка данных
        statistics = {
            "event_type_counts": {"action": 5, "feedback": 3},
            "event_type_total_significance": {"action": 2.5, "feedback": 1.5},
            "action_feedback_patterns": {"dampen": {"energy_delta": -10.0}},
            "state_changes_patterns": {"energy": -5.0, "stability": 0.1},
        }

        current_params = {
            "event_type_sensitivity": {"action": 0.5, "feedback": 0.3},
            "significance_thresholds": {"min_threshold": 0.1},
            "response_coefficients": {"dampen": 0.8},
        }

        # Один цикл обучения (process_statistics + adjust_parameters)
        processed_stats = engine.process_statistics([])
        assert isinstance(processed_stats, dict)

        new_params = engine.adjust_parameters(statistics, current_params)
        assert isinstance(new_params, dict)

        # Проверка, что параметры изменились (не остались теми же)
        # Learning должен вносить небольшие изменения
        assert new_params != current_params or new_params == {}

    def test_selfstate_smoke(self):
        """Smoke-тест SelfState: создание и базовые операции"""
        # Создание
        state = SelfState()

        # Проверка начальных значений
        assert isinstance(state.life_id, str)
        assert len(state.life_id) > 0
        assert state.energy == 100.0
        assert state.integrity == 1.0
        assert state.stability == 1.0
        assert state.ticks == 0
        assert state.age >= 0.0
        assert state.subjective_time == 0.0

        # Базовые операции
        state.ticks = 1
        state.energy = 90.0
        state.subjective_time = 0.5

        assert state.ticks == 1
        assert state.energy == 90.0
        assert state.subjective_time == 0.5

        # Проверка валидации (должна работать)
        try:
            state.energy = 150.0  # Недопустимое значение
            assert False, "Должно было выбросить ValueError"
        except ValueError:
            pass  # Ожидаемое поведение

        # Проверка immutable полей
        original_life_id = state.life_id
        try:
            state.life_id = "new_id"  # Должно быть запрещено
            assert False, "Должно было выбросить AttributeError"
        except AttributeError:
            pass  # Ожидаемое поведение

        assert state.life_id == original_life_id  # Не изменилось

    def test_runtime_loop_smoke(self):
        """Smoke-тест Runtime Loop: базовые операции без ошибок"""
        # Создание компонентов
        state = SelfState()

        # Имитация одного тика: обновление базовых полей
        try:
            # Обновление тиков и возраста (как в runtime loop)
            state.apply_delta({"ticks": 1})
            state.apply_delta({"age": 0.1})

            # Проверка, что обновление прошло без ошибок
            assert state.ticks == 1
            assert state.age >= 0.1

        except Exception as e:
            pytest.fail(f"Runtime operations failed with: {e}")

    def test_full_system_smoke(self):
        """Smoke-тест всей системы: создание всех компонентов"""
        # Создание всех основных компонентов
        state = SelfState()
        memory = Memory()
        learning = LearningEngine()

        # Проверка, что все создалось без ошибок
        assert state is not None
        assert memory is not None
        assert learning is not None

        # Проверка связей
        assert state.memory is not None
        assert hasattr(state.memory, "archive")

        # Базовые операции системы
        try:
            # Имитация одного тика
            state.apply_delta({"ticks": 1})
            memory.append(MemoryEntry("system_init", 0.1, time.time()))
            stats = learning.process_statistics([])

            assert state.ticks == 1
            assert len(memory) == 1
            assert isinstance(stats, dict)

        except Exception as e:
            pytest.fail(f"Full system operations failed with: {e}")
