"""
Подробные тесты для модуля Feedback
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import time
import pytest
from feedback import register_action, observe_consequences, PendingAction, FeedbackRecord
from state.self_state import SelfState
from environment.event_queue import EventQueue
from memory.memory import MemoryEntry


class TestRegisterAction:
    """Тесты для функции register_action"""
    
    def test_register_action_basic(self):
        """Тест базовой регистрации действия"""
        pending_actions = []
        state_before = {'energy': 50.0, 'stability': 0.8, 'integrity': 0.9}
        
        register_action(
            action_id="test_action_1",
            action_pattern="dampen",
            state_before=state_before,
            timestamp=time.time(),
            pending_actions=pending_actions
        )
        
        assert len(pending_actions) == 1
        assert pending_actions[0].action_id == "test_action_1"
        assert pending_actions[0].action_pattern == "dampen"
        assert pending_actions[0].state_before == state_before
        assert 3 <= pending_actions[0].check_after_ticks <= 10
        assert pending_actions[0].ticks_waited == 0
    
    def test_register_action_different_patterns(self):
        """Тест регистрации разных паттернов действий"""
        patterns = ["dampen", "absorb", "ignore"]
        for pattern in patterns:
            pending_actions = []
            register_action(
                action_id=f"action_{pattern}",
                action_pattern=pattern,
                state_before={'energy': 50.0},
                timestamp=time.time(),
                pending_actions=pending_actions
            )
            assert pending_actions[0].action_pattern == pattern
    
    def test_register_action_state_copy(self):
        """Тест, что state_before копируется, а не ссылается"""
        pending_actions = []
        state_before = {'energy': 50.0, 'stability': 0.8}
        
        register_action(
            action_id="test",
            action_pattern="dampen",
            state_before=state_before,
            timestamp=time.time(),
            pending_actions=pending_actions
        )
        
        # Изменяем оригинальный словарь
        state_before['energy'] = 100.0
        
        # Копия в pending_action не должна измениться
        assert pending_actions[0].state_before['energy'] == 50.0
    
    def test_register_action_multiple(self):
        """Тест регистрации нескольких действий"""
        pending_actions = []
        
        for i in range(5):
            register_action(
                action_id=f"action_{i}",
                action_pattern="dampen",
                state_before={'energy': 50.0},
                timestamp=time.time(),
                pending_actions=pending_actions
            )
        
        assert len(pending_actions) == 5
        for i, pending in enumerate(pending_actions):
            assert pending.action_id == f"action_{i}"


class TestObserveConsequences:
    """Тесты для функции observe_consequences"""
    
    def test_observe_consequences_with_changes(self):
        """Тест наблюдения последствий с изменениями состояния"""
        pending_actions = []
        self_state = SelfState()
        self_state.energy = 50.0
        self_state.stability = 0.8
        self_state.integrity = 0.9
        
        state_before = {'energy': 50.0, 'stability': 0.8, 'integrity': 0.9}
        register_action(
            action_id="test_action_2",
            action_pattern="dampen",
            state_before=state_before,
            timestamp=time.time(),
            pending_actions=pending_actions
        )
        
        self_state.energy = 49.0
        self_state.stability = 0.79
        pending_actions[0].check_after_ticks = 1
        
        feedback_records = observe_consequences(self_state, pending_actions)
        
        assert len(feedback_records) == 1
        assert feedback_records[0].action_id == "test_action_2"
        assert feedback_records[0].action_pattern == "dampen"
        assert abs(feedback_records[0].state_delta['energy'] - (-1.0)) < 0.001
        assert abs(feedback_records[0].state_delta['stability'] - (-0.01)) < 0.001
        assert len(pending_actions) == 0


    def test_observe_consequences_minimal_changes(self):
        """Тест: изменения меньше порога не создают Feedback запись"""
        pending_actions = []
        self_state = SelfState()
        self_state.energy = 50.0
        self_state.stability = 0.8
        self_state.integrity = 0.9
        
        state_before = {'energy': 50.0, 'stability': 0.8, 'integrity': 0.9}
        register_action(
            action_id="test_action_3",
            action_pattern="ignore",
            state_before=state_before,
            timestamp=time.time(),
            pending_actions=pending_actions
        )
        
        self_state.energy = 50.0001
        pending_actions[0].check_after_ticks = 1
        
        feedback_records = observe_consequences(self_state, pending_actions)
        
        assert len(feedback_records) == 0
        assert len(pending_actions) == 0


    def test_observe_consequences_timeout(self):
        """Тест: действия удаляются после 20 тиков"""
        pending_actions = []
        self_state = SelfState()
        
        state_before = {'energy': 50.0, 'stability': 0.8, 'integrity': 0.9}
        register_action(
            action_id="test_action_4",
            action_pattern="absorb",
            state_before=state_before,
            timestamp=time.time(),
            pending_actions=pending_actions
        )
        
        pending_actions[0].check_after_ticks = 25
        pending_actions[0].ticks_waited = 21
        
        feedback_records = observe_consequences(self_state, pending_actions)
        
        assert len(feedback_records) == 0
        assert len(pending_actions) == 0


    def test_multiple_actions(self):
        """Тест: несколько действий обрабатываются независимо"""
        pending_actions = []
        self_state = SelfState()
        self_state.energy = 50.0
        self_state.stability = 0.8
        self_state.integrity = 0.9
        
        register_action("action_1", "dampen", {'energy': 50.0, 'stability': 0.8, 'integrity': 0.9}, time.time(), pending_actions)
        register_action("action_2", "absorb", {'energy': 50.0, 'stability': 0.8, 'integrity': 0.9}, time.time(), pending_actions)
        
        assert len(pending_actions) == 2
        
        pending_actions[0].check_after_ticks = 1
        self_state.energy = 49.0
        
        feedback_records = observe_consequences(self_state, pending_actions)
        
        assert len(feedback_records) == 1
        assert len(pending_actions) == 1
        assert pending_actions[0].action_id == "action_2"
    
    def test_observe_consequences_ticks_waited_increment(self):
        """Тест увеличения ticks_waited"""
        pending_actions = []
        self_state = SelfState()
        state_before = {'energy': 50.0, 'stability': 0.8, 'integrity': 0.9}
        
        register_action("test", "dampen", state_before, time.time(), pending_actions)
        pending_actions[0].check_after_ticks = 5
        
        # Вызываем несколько раз
        observe_consequences(self_state, pending_actions)
        assert pending_actions[0].ticks_waited == 1
        
        observe_consequences(self_state, pending_actions)
        assert pending_actions[0].ticks_waited == 2
    
    def test_observe_consequences_positive_delta(self):
        """Тест обработки положительных изменений состояния"""
        pending_actions = []
        self_state = SelfState()
        self_state.energy = 50.0
        state_before = {'energy': 50.0, 'stability': 0.8, 'integrity': 0.9}
        
        register_action("test", "recovery", state_before, time.time(), pending_actions)
        self_state.energy = 55.0  # Увеличение
        pending_actions[0].check_after_ticks = 1
        
        feedback_records = observe_consequences(self_state, pending_actions)
        
        assert len(feedback_records) == 1
        assert feedback_records[0].state_delta['energy'] > 0


class TestFeedbackIntegration:
    """Интеграционные тесты для Feedback"""
    
    def test_integration_with_memory(self):
        """Тест интеграции с Memory"""
        pending_actions = []
        self_state = SelfState()
        self_state.energy = 50.0
        self_state.stability = 0.8
        self_state.integrity = 0.9
        
        state_before = {'energy': 50.0, 'stability': 0.8, 'integrity': 0.9}
        register_action("action_mem", "dampen", state_before, time.time(), pending_actions)
        
        self_state.energy = 49.0
        pending_actions[0].check_after_ticks = 1
        
        feedback_records = observe_consequences(self_state, pending_actions)
        
        for feedback in feedback_records:
            feedback_entry = MemoryEntry(
                event_type="feedback",
                meaning_significance=0.0,
                timestamp=feedback.timestamp,
                feedback_data={
                    "action_id": feedback.action_id,
                    "action_pattern": feedback.action_pattern,
                    "state_delta": feedback.state_delta,
                    "delay_ticks": feedback.delay_ticks,
                    "associated_events": feedback.associated_events
                }
            )
            self_state.memory.append(feedback_entry)
        
        assert len(self_state.memory) == 1
        assert self_state.memory[0].event_type == "feedback"
        assert self_state.memory[0].meaning_significance == 0.0
        assert self_state.memory[0].feedback_data is not None
        assert self_state.memory[0].feedback_data["action_id"] == "action_mem"
        assert self_state.memory[0].feedback_data["action_pattern"] == "dampen"
        assert "energy" in self_state.memory[0].feedback_data["state_delta"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
