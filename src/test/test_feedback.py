"""
Тесты для модуля Feedback
"""
import sys
from pathlib import Path
# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import time
from feedback import register_action, observe_consequences, PendingAction, FeedbackRecord
from state.self_state import SelfState
from environment.event_queue import EventQueue


def test_register_action():
    """Тест регистрации действия"""
    print("Тест 1: Регистрация действия")
    pending_actions = []
    state_before = {'energy': 50.0, 'stability': 0.8, 'integrity': 0.9}
    
    register_action(
        action_id="test_action_1",
        action_pattern="dampen",
        state_before=state_before,
        timestamp=time.time(),
        pending_actions=pending_actions
    )
    
    assert len(pending_actions) == 1, "Действие должно быть зарегистрировано"
    assert pending_actions[0].action_id == "test_action_1"
    assert pending_actions[0].action_pattern == "dampen"
    assert pending_actions[0].state_before == state_before
    assert 3 <= pending_actions[0].check_after_ticks <= 10, "Задержка должна быть 3-10 тиков"
    assert pending_actions[0].ticks_waited == 0
    print("[OK] Регистрация действия работает корректно")


def test_observe_consequences_with_changes():
    """Тест наблюдения последствий с изменениями состояния"""
    print("\nТест 2: Наблюдение последствий с изменениями")
    pending_actions = []
    self_state = SelfState()
    self_state.energy = 50.0
    self_state.stability = 0.8
    self_state.integrity = 0.9
    
    # Регистрируем действие
    state_before = {'energy': 50.0, 'stability': 0.8, 'integrity': 0.9}
    register_action(
        action_id="test_action_2",
        action_pattern="dampen",
        state_before=state_before,
        timestamp=time.time(),
        pending_actions=pending_actions
    )
    
    # Изменяем состояние (симулируем последствия действия)
    self_state.energy = 49.0  # Изменение > 0.001
    self_state.stability = 0.79
    
    # Устанавливаем задержку на 1 тик для быстрого теста
    pending_actions[0].check_after_ticks = 1
    
    # Наблюдаем последствия
    feedback_records = observe_consequences(self_state, pending_actions)
    
    assert len(feedback_records) == 1, "Должна быть создана одна Feedback запись"
    assert feedback_records[0].action_id == "test_action_2"
    assert feedback_records[0].action_pattern == "dampen"
    assert abs(feedback_records[0].state_delta['energy'] - (-1.0)) < 0.001
    assert abs(feedback_records[0].state_delta['stability'] - (-0.01)) < 0.001
    assert len(pending_actions) == 0, "Обработанное действие должно быть удалено"
    print("[OK] Наблюдение последствий работает корректно")


def test_observe_consequences_minimal_changes():
    """Тест: изменения меньше порога не создают Feedback запись"""
    print("\nТест 3: Минимальные изменения (не создают Feedback)")
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
    
    # Изменяем состояние очень незначительно (< 0.001)
    self_state.energy = 50.0001
    
    pending_actions[0].check_after_ticks = 1
    
    feedback_records = observe_consequences(self_state, pending_actions)
    
    assert len(feedback_records) == 0, "Минимальные изменения не должны создавать Feedback"
    assert len(pending_actions) == 0, "Действие должно быть удалено даже без Feedback"
    print("[OK] Минимальные изменения корректно игнорируются")


def test_observe_consequences_timeout():
    """Тест: действия удаляются после 20 тиков"""
    print("\nТест 4: Таймаут после 20 тиков")
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
    
    # Устанавливаем большую задержку, но симулируем 21 тик
    pending_actions[0].check_after_ticks = 25  # Больше 20
    pending_actions[0].ticks_waited = 21  # Превысили лимит
    
    feedback_records = observe_consequences(self_state, pending_actions)
    
    assert len(feedback_records) == 0, "Таймаут не должен создавать Feedback"
    assert len(pending_actions) == 0, "Действие должно быть удалено по таймауту"
    print("[OK] Таймаут работает корректно")


def test_multiple_actions():
    """Тест: несколько действий обрабатываются независимо"""
    print("\nТест 5: Несколько действий")
    pending_actions = []
    self_state = SelfState()
    self_state.energy = 50.0
    self_state.stability = 0.8
    self_state.integrity = 0.9
    
    # Регистрируем два действия
    register_action("action_1", "dampen", {'energy': 50.0, 'stability': 0.8, 'integrity': 0.9}, time.time(), pending_actions)
    register_action("action_2", "absorb", {'energy': 50.0, 'stability': 0.8, 'integrity': 0.9}, time.time(), pending_actions)
    
    assert len(pending_actions) == 2
    
    # Первое действие готово к проверке
    pending_actions[0].check_after_ticks = 1
    self_state.energy = 49.0  # Изменение для первого действия
    
    feedback_records = observe_consequences(self_state, pending_actions)
    
    assert len(feedback_records) == 1, "Только первое действие должно быть обработано"
    assert len(pending_actions) == 1, "Одно действие должно остаться"
    assert pending_actions[0].action_id == "action_2"
    print("[OK] Несколько действий обрабатываются независимо")


def test_integration_with_memory():
    """Тест интеграции с Memory"""
    print("\nТест 6: Интеграция с Memory")
    from memory.memory import MemoryEntry
    
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
    
    # Сохраняем в Memory (как в loop.py)
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
    
    assert len(self_state.memory) == 1, "Feedback должен быть сохранен в Memory"
    assert self_state.memory[0].event_type == "feedback"
    assert self_state.memory[0].meaning_significance == 0.0
    assert self_state.memory[0].feedback_data is not None, "feedback_data должен быть сохранен"
    assert self_state.memory[0].feedback_data["action_id"] == "action_mem"
    assert self_state.memory[0].feedback_data["action_pattern"] == "dampen"
    assert "energy" in self_state.memory[0].feedback_data["state_delta"]
    print("[OK] Интеграция с Memory работает корректно (с полными данными)")


if __name__ == "__main__":
    print("=" * 60)
    print("Тестирование модуля Feedback")
    print("=" * 60)
    
    try:
        test_register_action()
        test_observe_consequences_with_changes()
        test_observe_consequences_minimal_changes()
        test_observe_consequences_timeout()
        test_multiple_actions()
        test_integration_with_memory()
        
        print("\n" + "=" * 60)
        print("[OK] Все тесты пройдены успешно!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n[FAIL] Тест провален: {e}")
        raise
    except Exception as e:
        print(f"\n[ERROR] Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()
        raise
