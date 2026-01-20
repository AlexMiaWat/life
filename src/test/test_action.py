"""
Подробные тесты для модуля Action
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import time

import pytest

from src.action.action import execute_action
from src.state.self_state import SelfState


@pytest.mark.unit
@pytest.mark.order(1)
class TestExecuteAction:
    """Тесты для функции execute_action"""

    @pytest.fixture
    def base_state(self):
        """Создает базовое состояние"""
        state = SelfState()
        state.energy = 50.0
        state.stability = 0.8
        state.integrity = 0.9
        return state

    def test_execute_action_dampen(self, base_state):
        """Тест выполнения действия dampen"""
        initial_energy = base_state.energy
        initial_memory_size = len(base_state.memory)

        # Получаем коэффициент для dampen (по умолчанию 0.5)
        learning_params = getattr(base_state, "learning_params", {})
        response_coefficients = learning_params.get("response_coefficients", {})
        adaptation_params = getattr(base_state, "adaptation_params", {})
        behavior_coefficients = adaptation_params.get("behavior_coefficients", {})
        coefficient = behavior_coefficients.get(
            "dampen", response_coefficients.get("dampen", 1.0)
        )
        # Эффект усталости: 0.01 * (1.0 - coefficient)
        expected_effect = 0.01 * (1.0 - coefficient)

        execute_action("dampen", base_state)

        # Проверяем, что энергия уменьшилась
        assert base_state.energy < initial_energy
        assert abs(base_state.energy - (initial_energy - expected_effect)) < 0.001

        # Проверяем, что действие записано в память
        assert len(base_state.memory) == initial_memory_size + 1
        assert base_state.memory[-1].event_type == "action"
        assert base_state.memory[-1].meaning_significance == 0.0

    def test_execute_action_dampen_energy_minimum(self, base_state):
        """Тест выполнения dampen с минимальной энергией"""
        base_state.energy = 0.01
        execute_action("dampen", base_state)

        # Энергия не должна стать отрицательной
        assert base_state.energy >= 0.0
        # Энергия должна быть уменьшена, но не обязательно до 0 (зависит от коэффициента)
        assert base_state.energy <= 0.01

    def test_execute_action_absorb(self, base_state):
        """Тест выполнения действия absorb"""
        initial_energy = base_state.energy
        initial_memory_size = len(base_state.memory)

        execute_action("absorb", base_state)

        # Энергия не должна измениться (только для dampen есть эффект)
        assert base_state.energy == initial_energy

        # Проверяем, что действие записано в память
        assert len(base_state.memory) == initial_memory_size + 1
        assert base_state.memory[-1].event_type == "action"

    def test_execute_action_ignore(self, base_state):
        """Тест выполнения действия ignore"""
        initial_energy = base_state.energy
        initial_memory_size = len(base_state.memory)

        execute_action("ignore", base_state)

        # Энергия не должна измениться
        assert base_state.energy == initial_energy

        # Проверяем, что действие записано в память
        assert len(base_state.memory) == initial_memory_size + 1
        assert base_state.memory[-1].event_type == "action"

    def test_execute_action_memory_entry_timestamp(self, base_state):
        """Тест проверки timestamp в записи действия"""
        before_time = time.time()
        execute_action("absorb", base_state)
        after_time = time.time()

        entry = base_state.memory[-1]
        assert before_time <= entry.timestamp <= after_time

    def test_execute_action_multiple_actions(self, base_state):
        """Тест выполнения нескольких действий подряд"""
        initial_memory_size = len(base_state.memory)

        execute_action("absorb", base_state)
        execute_action("dampen", base_state)
        execute_action("ignore", base_state)

        # Должно быть 3 записи в памяти
        assert len(base_state.memory) == initial_memory_size + 3

        # Все записи должны быть типа "action"
        for i in range(3):
            assert base_state.memory[initial_memory_size + i].event_type == "action"

    def test_execute_action_dampen_multiple_times(self, base_state):
        """Тест выполнения dampen несколько раз"""
        initial_energy = base_state.energy

        # Получаем коэффициент для dampen
        learning_params = getattr(base_state, "learning_params", {})
        response_coefficients = learning_params.get("response_coefficients", {})
        adaptation_params = getattr(base_state, "adaptation_params", {})
        behavior_coefficients = adaptation_params.get("behavior_coefficients", {})
        coefficient = behavior_coefficients.get(
            "dampen", response_coefficients.get("dampen", 1.0)
        )
        # Эффект усталости за один раз: 0.01 * (1.0 - coefficient)
        effect_per_action = 0.01 * (1.0 - coefficient)

        for _ in range(5):
            execute_action("dampen", base_state)

        # Энергия должна уменьшиться на effect_per_action * 5
        expected_energy = max(0.0, initial_energy - effect_per_action * 5)
        assert abs(base_state.energy - expected_energy) < 0.001

    def test_execute_action_unknown_pattern(self, base_state):
        """Тест выполнения действия с неизвестным паттерном"""
        initial_energy = base_state.energy
        initial_memory_size = len(base_state.memory)

        # Неизвестный паттерн должен быть обработан без ошибок
        execute_action("unknown_pattern", base_state)

        # Энергия не должна измениться
        assert base_state.energy == initial_energy

        # Действие все равно должно быть записано в память
        assert len(base_state.memory) == initial_memory_size + 1
        assert base_state.memory[-1].event_type == "action"

    def test_execute_action_preserves_other_state(self, base_state):
        """Тест, что выполнение действия не изменяет другие параметры состояния"""
        initial_stability = base_state.stability
        initial_integrity = base_state.integrity
        initial_ticks = base_state.ticks

        execute_action("dampen", base_state)

        # Эти параметры не должны измениться
        assert base_state.stability == initial_stability
        assert base_state.integrity == initial_integrity
        assert base_state.ticks == initial_ticks

    def test_execute_action_memory_entry_significance(self, base_state):
        """Тест проверки significance в записи действия (должна быть 0.0)"""
        execute_action("absorb", base_state)

        entry = base_state.memory[-1]
        assert entry.meaning_significance == 0.0

    def test_execute_action_empty_memory(self, base_state):
        """Тест выполнения действия при пустой памяти"""
        base_state.memory = []

        execute_action("absorb", base_state)

        assert len(base_state.memory) == 1
        assert base_state.memory[0].event_type == "action"

    def test_execute_action_with_existing_memory(self, base_state):
        """Тест выполнения действия при существующей памяти"""
        # Добавляем несколько записей в память
        from memory.memory import MemoryEntry

        for i in range(3):
            entry = MemoryEntry(
                event_type=f"event_{i}", meaning_significance=0.5, timestamp=time.time()
            )
            base_state.memory.append(entry)

        initial_memory_size = len(base_state.memory)
        execute_action("absorb", base_state)

        # Должна быть добавлена еще одна запись
        assert len(base_state.memory) == initial_memory_size + 1
        assert base_state.memory[-1].event_type == "action"
        # Предыдущие записи должны остаться
        assert base_state.memory[0].event_type == "event_0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
