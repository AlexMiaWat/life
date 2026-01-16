"""
Подробные тесты для модуля Decision
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import time
import pytest
from decision.decision import decide_response
from state.self_state import SelfState
from meaning.meaning import Meaning
from memory.memory import MemoryEntry


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
        return Meaning(
            significance=0.7,
            impact={"energy": -1.0, "stability": -0.1}
        )
    
    @pytest.fixture
    def low_significance_meaning(self):
        """Создает Meaning с низкой значимостью"""
        return Meaning(
            significance=0.05,
            impact={"energy": -0.1, "stability": -0.01}
        )
    
    def test_decide_dampen_high_activated_memory(self, base_state, high_significance_meaning):
        """Тест выбора dampen при высокой significance в активированной памяти"""
        # Создаем активированную память с высокой significance
        base_state.activated_memory = [
            MemoryEntry("event", 0.6, time.time()),  # > 0.5
            MemoryEntry("event", 0.4, time.time())
        ]
        
        pattern = decide_response(base_state, high_significance_meaning)
        assert pattern == "dampen"
    
    def test_decide_dampen_max_significance_above_threshold(self, base_state, high_significance_meaning):
        """Тест выбора dampen когда max significance > 0.5"""
        base_state.activated_memory = [
            MemoryEntry("event", 0.51, time.time())  # Чуть выше порога
        ]
        
        pattern = decide_response(base_state, high_significance_meaning)
        assert pattern == "dampen"
    
    def test_decide_dampen_max_significance_at_threshold(self, base_state, high_significance_meaning):
        """Тест выбора dampen когда max significance = 0.5 (граничный случай)"""
        base_state.activated_memory = [
            MemoryEntry("event", 0.5, time.time())  # Ровно на пороге
        ]
        
        pattern = decide_response(base_state, high_significance_meaning)
        # 0.5 не больше 0.5, поэтому должен вернуться fallback
        # Но в коде используется > 0.5, поэтому это не dampen
        assert pattern != "dampen"  # Должен быть fallback
    
    def test_decide_ignore_low_significance_meaning(self, base_state, low_significance_meaning):
        """Тест выбора ignore при низкой significance в Meaning"""
        base_state.activated_memory = []  # Пустая активированная память
        
        pattern = decide_response(base_state, low_significance_meaning)
        assert pattern == "ignore"
    
    def test_decide_ignore_meaning_significance_below_threshold(self, base_state):
        """Тест выбора ignore когда significance < 0.1"""
        meaning = Meaning(significance=0.09, impact={"energy": -0.1})
        base_state.activated_memory = []
        
        pattern = decide_response(base_state, meaning)
        assert pattern == "ignore"
    
    def test_decide_absorb_normal_conditions(self, base_state):
        """Тест выбора absorb при нормальных условиях"""
        meaning = Meaning(significance=0.5, impact={"energy": -1.0})
        base_state.activated_memory = [
            MemoryEntry("event", 0.3, time.time())  # < 0.5
        ]
        
        pattern = decide_response(base_state, meaning)
        assert pattern == "absorb"
    
    def test_decide_absorb_high_significance_meaning(self, base_state):
        """Тест выбора absorb при высокой significance в Meaning, но низкой в памяти"""
        meaning = Meaning(significance=0.8, impact={"energy": -1.0})
        base_state.activated_memory = [
            MemoryEntry("event", 0.4, time.time())  # < 0.5
        ]
        
        pattern = decide_response(base_state, meaning)
        assert pattern == "absorb"
    
    def test_decide_empty_activated_memory(self, base_state):
        """Тест принятия решения при пустой активированной памяти"""
        base_state.activated_memory = []
        meaning = Meaning(significance=0.5, impact={"energy": -1.0})
        
        pattern = decide_response(base_state, meaning)
        # Должен вернуться fallback к Meaning's pattern
        assert pattern in ["ignore", "absorb"]
    
    def test_decide_multiple_activated_memories(self, base_state):
        """Тест принятия решения с несколькими активированными воспоминаниями"""
        base_state.activated_memory = [
            MemoryEntry("event", 0.3, time.time()),
            MemoryEntry("event", 0.7, time.time()),  # Максимальная
            MemoryEntry("event", 0.2, time.time())
        ]
        meaning = Meaning(significance=0.5, impact={"energy": -1.0})
        
        pattern = decide_response(base_state, meaning)
        assert pattern == "dampen"  # max(0.3, 0.7, 0.2) = 0.7 > 0.5
    
    def test_decide_activated_memory_max_below_threshold(self, base_state):
        """Тест принятия решения когда max significance в памяти < 0.5"""
        base_state.activated_memory = [
            MemoryEntry("event", 0.4, time.time()),
            MemoryEntry("event", 0.3, time.time())
        ]
        meaning = Meaning(significance=0.6, impact={"energy": -1.0})
        
        pattern = decide_response(base_state, meaning)
        # max(0.4, 0.3) = 0.4 < 0.5, поэтому fallback
        assert pattern == "absorb"
    
    def test_decide_activated_memory_exactly_at_threshold(self, base_state):
        """Тест принятия решения когда max significance = 0.5"""
        base_state.activated_memory = [
            MemoryEntry("event", 0.5, time.time())
        ]
        meaning = Meaning(significance=0.6, impact={"energy": -1.0})
        
        pattern = decide_response(base_state, meaning)
        # 0.5 не > 0.5, поэтому fallback
        assert pattern == "absorb"
    
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
            MemoryEntry("noise", 0.3, time.time())
        ]
        meaning = Meaning(significance=0.5, impact={"energy": -1.0})
        
        pattern = decide_response(base_state, meaning)
        assert pattern == "dampen"  # max(0.6, 0.3) = 0.6 > 0.5
    
    def test_decide_consistency(self, base_state):
        """Тест консистентности решений при одинаковых условиях"""
        base_state.activated_memory = [
            MemoryEntry("event", 0.6, time.time())
        ]
        meaning = Meaning(significance=0.5, impact={"energy": -1.0})
        
        # Вызываем несколько раз
        patterns = [decide_response(base_state, meaning) for _ in range(5)]
        
        # Все результаты должны быть одинаковыми
        assert all(p == patterns[0] for p in patterns)
        assert patterns[0] == "dampen"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
