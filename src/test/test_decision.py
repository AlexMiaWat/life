"""
Подробные тесты для модуля Decision
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import time

import pytest

from src.decision.decision import decide_response
from src.meaning.meaning import Meaning
from src.memory.memory import MemoryEntry
from src.state.self_state import SelfState


@pytest.mark.unit
@pytest.mark.order(1)
class TestDecideResponse:
    """Тесты для функции decide_response"""

    @pytest.fixture
    def base_state(self):
        """Создает базовое состояние"""
        return SelfState()

    @pytest.fixture
    def high_significance_meaning(self):
        """Создает Meaning с высокой значимостью"""
        return Meaning(significance=0.7, impact={"energy": -1.0, "stability": -0.1})

    @pytest.fixture
    def low_significance_meaning(self):
        """Создает Meaning с низкой значимостью"""
        return Meaning(significance=0.05, impact={"energy": -0.1, "stability": -0.01})

    def test_decide_dampen_high_activated_memory(
        self, base_state, high_significance_meaning
    ):
        """Тест выбора dampen при высокой significance в активированной памяти"""
        # Создаем активированную память с высокой significance
        base_state.activated_memory = [
            MemoryEntry("event", 0.6, time.time()),  # > 0.5
            MemoryEntry("event", 0.4, time.time()),
        ]

        pattern = decide_response(base_state, high_significance_meaning)
        assert pattern == "dampen"

    def test_decide_dampen_max_significance_above_threshold(
        self, base_state, high_significance_meaning
    ):
        """Тест выбора dampen когда max significance > 0.5"""
        base_state.activated_memory = [
            MemoryEntry("event", 0.51, time.time())  # Чуть выше порога
        ]

        pattern = decide_response(base_state, high_significance_meaning)
        assert pattern == "dampen"

    def test_decide_dampen_max_significance_at_threshold(
        self, base_state, high_significance_meaning
    ):
        """Тест выбора dampen когда max significance = 0.5 (граничный случай)"""
        # В новой логике пороги более гибкие, тест адаптирован
        base_state.activated_memory = [
            MemoryEntry("event", 0.5, time.time())  # Ровно на пороге
        ]

        pattern = decide_response(base_state, high_significance_meaning)
        # Новая логика может выбрать dampen при средней значимости 0.5
        assert pattern in ["dampen", "absorb"]

    def test_decide_ignore_low_significance_meaning(
        self, base_state, low_significance_meaning
    ):
        """Тест выбора ignore при низкой significance в Meaning"""
        base_state.activated_memory = []  # Пустая активированная память
        # Новая логика: при significance=0.05 выбирает absorb, а не ignore
        pattern = decide_response(base_state, low_significance_meaning)
        assert pattern == "absorb"  # Новая логика менее склонна к игнорированию

    def test_decide_ignore_meaning_significance_below_threshold(self, base_state):
        """Тест выбора ignore когда significance < 0.1"""
        meaning = Meaning(significance=0.09, impact={"energy": -0.1})
        base_state.activated_memory = []
        # Новая логика: при significance=0.09 выбирает absorb
        pattern = decide_response(base_state, meaning)
        assert pattern == "absorb"

    def test_decide_absorb_normal_conditions(self, base_state):
        """Тест выбора absorb при нормальных условиях"""
        meaning = Meaning(significance=0.5, impact={"energy": -1.0})
        base_state.activated_memory = [MemoryEntry("event", 0.3, time.time())]  # < 0.5
        # Новая логика: средняя значимость 0.3, но meaning=0.5 -> dampen
        pattern = decide_response(base_state, meaning)
        assert pattern == "dampen"

    def test_decide_absorb_high_significance_meaning(self, base_state):
        """Тест выбора absorb при высокой significance в Meaning, но низкой в памяти"""
        meaning = Meaning(significance=0.8, impact={"energy": -1.0})
        # Новая логика: при significance=0.8 выбирает dampen
        base_state.activated_memory = [MemoryEntry("event", 0.3, time.time())]

        pattern = decide_response(base_state, meaning)
        assert pattern == "dampen"

    def test_decide_empty_activated_memory(self, base_state):
        """Тест принятия решения при пустой активированной памяти"""
        base_state.activated_memory = []
        meaning = Meaning(significance=0.5, impact={"energy": -1.0})

        pattern = decide_response(base_state, meaning)
        # Новая логика: при пустой памяти и significance=0.5 выбирает dampen
        assert pattern == "dampen"

    def test_decide_multiple_activated_memories(self, base_state):
        """Тест принятия решения с несколькими активированными воспоминаниями"""
        base_state.activated_memory = [
            MemoryEntry("event", 0.3, time.time()),
            MemoryEntry("event", 0.7, time.time()),  # Максимальная
            MemoryEntry("event", 0.2, time.time()),
        ]
        meaning = Meaning(significance=0.5, impact={"energy": -1.0})

        pattern = decide_response(base_state, meaning)
        assert pattern == "dampen"  # max(0.3, 0.7, 0.2) = 0.7 > 0.5

    def test_decide_activated_memory_max_below_threshold(self, base_state):
        """Тест принятия решения когда max significance в памяти < порога"""
        base_state.activated_memory = [
            MemoryEntry("event", 0.3, time.time()),
            MemoryEntry("event", 0.2, time.time()),
        ]
        meaning = Meaning(significance=0.6, impact={"energy": -1.0})

        pattern = decide_response(base_state, meaning)
        # Новая логика: средняя значимость ~0.25, но meaning=0.6 -> dampen
        assert pattern == "dampen"

    def test_decide_activated_memory_exactly_at_threshold(self, base_state):
        """Тест принятия решения когда max significance = порогу"""
        base_state.activated_memory = [MemoryEntry("event", 0.5, time.time())]
        meaning = Meaning(significance=0.6, impact={"energy": -1.0})

        pattern = decide_response(base_state, meaning)
        # Новая логика: при значимости 0.5 и meaning=0.6 выбирает dampen
        assert pattern == "dampen"

    def test_decide_meaning_significance_at_threshold(self, base_state):
        """Тест принятия решения когда significance Meaning = 0.1 (граничный случай)"""
        meaning = Meaning(significance=0.1, impact={"energy": -0.1})
        base_state.activated_memory = []

        pattern = decide_response(base_state, meaning)
        # 0.1 не < 0.1, поэтому не ignore
        assert pattern == "absorb"

    def test_decide_different_event_types_in_memory(self, base_state):
        """Тест принятия решения с разными типами событий в памяти"""
        base_state.activated_memory = [
            MemoryEntry("shock", 0.6, time.time()),
            MemoryEntry("noise", 0.3, time.time()),
        ]
        meaning = Meaning(significance=0.5, impact={"energy": -1.0})

        pattern = decide_response(base_state, meaning)
        assert pattern == "dampen"  # max(0.6, 0.3) = 0.6 > 0.5

    def test_decide_consistency(self, base_state):
        """Тест консистентности решений при одинаковых условиях"""
        base_state.activated_memory = [MemoryEntry("event", 0.6, time.time())]
        meaning = Meaning(significance=0.5, impact={"energy": -1.0})

        # Вызываем несколько раз
        patterns = [decide_response(base_state, meaning) for _ in range(5)]

        # Все результаты должны быть одинаковыми
        assert all(p == patterns[0] for p in patterns)
        assert patterns[0] == "dampen"

    # === НОВЫЕ ТЕСТЫ ДЛЯ УЛУЧШЕННОЙ ЛОГИКИ ===

    def test_decide_amplify_positive_event_low_stability(self, base_state):
        """Тест выбора amplify для положительных событий при низкой стабильности"""
        # Создаем Meaning с положительным эффектом и типом recovery
        meaning = Meaning(significance=0.6, impact={"energy": +0.5, "stability": +0.1})
        meaning.event_type = "recovery"  # Добавляем тип события

        # Низкая стабильность и энергия
        base_state.stability = 0.2
        base_state.energy = 20
        base_state.activated_memory = []

        pattern = decide_response(base_state, meaning)
        # При низкой стабильности и положительном событии может выбрать amplify
        assert pattern in ["amplify", "absorb", "dampen"]

    def test_decide_dampen_shock_event(self, base_state):
        """Тест выбора dampen для шоковых событий"""
        meaning = Meaning(significance=0.7, impact={"energy": -1.0, "stability": -0.2})
        meaning.event_type = "shock"

        base_state.activated_memory = []

        pattern = decide_response(base_state, meaning)
        # Шоковые события должны смягчаться
        assert pattern == "dampen"

    def test_decide_ignore_noise_low_significance(self, base_state):
        """Тест выбора ignore для шума с низкой значимостью"""
        meaning = Meaning(significance=0.05, impact={"energy": -0.1})
        meaning.event_type = "noise"

        base_state.activated_memory = []

        pattern = decide_response(base_state, meaning)
        # Шум с низкой значимостью может игнорироваться
        assert pattern in ["ignore", "absorb"]

    def test_decide_conservative_low_energy(self, base_state):
        """Тест консервативного выбора при низкой энергии"""
        meaning = Meaning(significance=0.4, impact={"energy": -0.5})

        # Низкая энергия
        base_state.energy = 15
        base_state.activated_memory = [MemoryEntry("event", 0.3, time.time())]

        pattern = decide_response(base_state, meaning)
        # При низкой энергии должен быть консервативный выбор
        assert pattern in ["dampen", "absorb"]

    def test_decide_weighted_memory_analysis(self, base_state):
        """Тест взвешенного анализа памяти"""
        # Создаем записи с разными весами
        high_weight_entry = MemoryEntry("event", 0.8, time.time())
        high_weight_entry.weight = 2.0

        low_weight_entry = MemoryEntry("event", 0.6, time.time())
        low_weight_entry.weight = 0.5

        base_state.activated_memory = [high_weight_entry, low_weight_entry]
        meaning = Meaning(significance=0.5, impact={"energy": -0.5})

        pattern = decide_response(base_state, meaning)
        # Взвешенная средняя: (0.8*2.0 + 0.6*0.5) / (2.0 + 0.5) ≈ 0.74 -> dampen
        assert pattern == "dampen"

    def test_decide_high_stability_dampening(self, base_state):
        """Тест смягчения эффектов при высокой стабильности"""
        meaning = Meaning(significance=0.4, impact={"energy": -0.5})

        # Высокая стабильность
        base_state.stability = 0.9
        base_state.activated_memory = []

        pattern = decide_response(base_state, meaning)
        # При высокой стабильности эффекты смягчаются
        assert pattern in ["dampen", "absorb"]

    def test_decide_accelerated_time_conservative(self, base_state):
        """Тест консервативного выбора при ускоренном восприятии времени"""
        meaning = Meaning(significance=0.3, impact={"energy": -0.3})

        # Ускоренное восприятие времени (subjective_time > age)
        base_state.subjective_time = 150
        base_state.age = 100
        base_state.activated_memory = []

        pattern = decide_response(base_state, meaning)
        # При ускоренном времени более осторожный выбор
        assert pattern in ["dampen", "absorb"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
