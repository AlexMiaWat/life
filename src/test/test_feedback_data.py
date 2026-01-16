"""
Тест для проверки сохранения полных данных Feedback
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import time

import pytest

from feedback import observe_consequences, register_action
from memory.memory import MemoryEntry
from state.self_state import SelfState


@pytest.mark.unit
@pytest.mark.order(1)
def test_feedback_data_storage():
    """Тест: Feedback записи содержат полные данные"""
    print("Тест: Сохранение полных данных Feedback")

    pending_actions = []
    self_state = SelfState()
    self_state.energy = 50.0
    self_state.stability = 0.8
    self_state.integrity = 0.9

    # Регистрируем действие
    state_before = {"energy": 50.0, "stability": 0.8, "integrity": 0.9}
    register_action(
        action_id="test_action_full",
        action_pattern="dampen",
        state_before=state_before,
        timestamp=time.time(),
        pending_actions=pending_actions,
    )

    # Изменяем состояние
    self_state.energy = 49.0
    self_state.stability = 0.79

    # Устанавливаем задержку на 1 тик
    pending_actions[0].check_after_ticks = 1

    # Наблюдаем последствия
    feedback_records = observe_consequences(self_state, pending_actions)

    assert len(feedback_records) == 1, "Должна быть создана одна Feedback запись"
    feedback = feedback_records[0]

    # Сохраняем в Memory (как в loop.py)
    feedback_entry = MemoryEntry(
        event_type="feedback",
        meaning_significance=0.0,
        timestamp=feedback.timestamp,
        feedback_data={
            "action_id": feedback.action_id,
            "action_pattern": feedback.action_pattern,
            "state_delta": feedback.state_delta,
            "delay_ticks": feedback.delay_ticks,
            "associated_events": feedback.associated_events,
        },
    )
    self_state.memory.append(feedback_entry)

    # Проверяем сохранение
    assert len(self_state.memory) == 1, "Feedback должен быть сохранен в Memory"
    stored = self_state.memory[0]

    assert stored.event_type == "feedback", "Тип должен быть feedback"
    assert stored.meaning_significance == 0.0, "Значимость должна быть 0.0"
    assert stored.feedback_data is not None, "feedback_data должен быть сохранен"
    assert (
        stored.feedback_data["action_id"] == "test_action_full"
    ), "action_id должен быть сохранен"
    assert (
        stored.feedback_data["action_pattern"] == "dampen"
    ), "action_pattern должен быть сохранен"
    assert (
        "energy" in stored.feedback_data["state_delta"]
    ), "state_delta должен содержать energy"
    assert (
        stored.feedback_data["state_delta"]["energy"] == -1.0
    ), "energy delta должен быть -1.0"
    assert stored.feedback_data["delay_ticks"] == 1, "delay_ticks должен быть сохранен"

    print("[OK] Полные данные Feedback сохранены корректно")
    print(f"  - action_id: {stored.feedback_data['action_id']}")
    print(f"  - action_pattern: {stored.feedback_data['action_pattern']}")
    print(f"  - state_delta: {stored.feedback_data['state_delta']}")
    print(f"  - delay_ticks: {stored.feedback_data['delay_ticks']}")


if __name__ == "__main__":
    try:
        test_feedback_data_storage()
        print("\n[SUCCESS] Все тесты пройдены!")
    except AssertionError as e:
        print(f"\n[FAIL] Тест провален: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Ошибка: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
