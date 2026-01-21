"""
Подробные тесты для модуля Intelligence
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest

from src.intelligence.intelligence import process_information
from src.state.self_state import SelfState


@pytest.mark.unit
@pytest.mark.order(1)
class TestProcessInformation:
    """Тесты для функции process_information"""

    @pytest.fixture
    def base_state(self):
        """Создает базовое состояние"""
        return SelfState()

    def test_process_information_basic(self, base_state):
        """Тест базовой обработки информации"""
        base_state.recent_events = ["event1", "event2"]
        base_state.energy = 50.0
        base_state.stability = 0.7
        base_state.planning = {"potential_sequences": [["e1", "e2"]]}

        process_information(base_state)

        assert "processed_sources" in base_state.intelligence
        processed = base_state.intelligence["processed_sources"]
        assert processed["memory_proxy_size"] == 2
        assert processed["adaptation_proxy"] == 50.0
        assert processed["learning_proxy"] == 0.7
        assert processed["planning_proxy_size"] == 1

    def test_process_information_empty_recent_events(self, base_state):
        """Тест обработки при пустом recent_events"""
        base_state.recent_events = []
        base_state.energy = 50.0
        base_state.stability = 0.7
        base_state.planning = {}

        process_information(base_state)

        processed = base_state.intelligence["processed_sources"]
        assert processed["memory_proxy_size"] == 0

    def test_process_information_empty_planning(self, base_state):
        """Тест обработки при пустом planning"""
        base_state.recent_events = ["e1"]
        base_state.energy = 50.0
        base_state.stability = 0.7
        base_state.planning = {}

        process_information(base_state)

        processed = base_state.intelligence["processed_sources"]
        assert processed["planning_proxy_size"] == 0

    def test_process_information_energy_values(self, base_state):
        """Тест обработки разных значений energy"""
        base_state.recent_events = []
        base_state.stability = 0.7
        base_state.planning = {}

        for energy in [0.0, 25.0, 50.0, 75.0, 100.0]:
            base_state.energy = energy
            process_information(base_state)
            processed = base_state.intelligence["processed_sources"]
            assert processed["adaptation_proxy"] == energy

    def test_process_information_stability_values(self, base_state):
        """Тест обработки разных значений stability"""
        base_state.recent_events = []
        base_state.energy = 50.0
        base_state.planning = {}

        for stability in [0.0, 0.3, 0.5, 0.7, 1.0]:
            base_state.stability = stability
            process_information(base_state)
            processed = base_state.intelligence["processed_sources"]
            assert processed["learning_proxy"] == stability

    def test_process_information_planning_sequences(self, base_state):
        """Тест обработки planning с разным количеством последовательностей"""
        base_state.recent_events = []
        base_state.energy = 50.0
        base_state.stability = 0.7

        for num_sequences in [0, 1, 3, 5]:
            base_state.planning = {
                "potential_sequences": [["e1", "e2"] for _ in range(num_sequences)]
            }
            process_information(base_state)
            processed = base_state.intelligence["processed_sources"]
            assert processed["planning_proxy_size"] == num_sequences

    def test_process_information_preserves_other_fields(self, base_state):
        """Тест, что функция не изменяет другие поля состояния"""
        base_state.energy = 50.0
        base_state.stability = 0.7
        base_state.integrity = 0.8
        base_state.ticks = 100
        base_state.recent_events = ["e1"]
        base_state.planning = {}

        process_information(base_state)

        # Эти поля не должны измениться
        assert base_state.energy == 50.0
        assert base_state.stability == 0.7
        assert base_state.integrity == 0.8
        assert base_state.ticks == 100
        assert base_state.recent_events == ["e1"]

    def test_process_information_multiple_calls(self, base_state):
        """Тест нескольких вызовов функции"""
        base_state.recent_events = ["e1"]
        base_state.energy = 50.0
        base_state.stability = 0.7
        base_state.planning = {}

        process_information(base_state)
        first_processed = base_state.intelligence["processed_sources"].copy()

        base_state.recent_events = ["e1", "e2", "e3"]
        base_state.energy = 60.0
        process_information(base_state)

        # Результаты должны обновиться
        processed = base_state.intelligence["processed_sources"]
        assert processed["memory_proxy_size"] == 3
        assert processed["adaptation_proxy"] == 60.0
        assert processed["memory_proxy_size"] != first_processed["memory_proxy_size"]

    def test_process_information_complex_state(self, base_state):
        """Тест обработки сложного состояния"""
        base_state.recent_events = ["shock", "noise", "recovery", "decay"]
        base_state.energy = 75.5
        base_state.stability = 0.85
        base_state.planning = {"potential_sequences": [["e1", "e2"], ["e3", "e4"], ["e5", "e6"]]}

        process_information(base_state)

        processed = base_state.intelligence["processed_sources"]
        assert processed["memory_proxy_size"] == 4
        assert processed["adaptation_proxy"] == 75.5
        assert processed["learning_proxy"] == 0.85
        assert processed["planning_proxy_size"] == 3

    def test_process_information_planning_without_sequences_key(self, base_state):
        """Тест обработки planning без ключа potential_sequences"""
        base_state.recent_events = []
        base_state.energy = 50.0
        base_state.stability = 0.7
        base_state.planning = {"other_key": "value"}

        process_information(base_state)

        processed = base_state.intelligence["processed_sources"]
        # Должно обработаться без ошибок
        assert processed["planning_proxy_size"] == 0

    def test_process_information_subjective_time_accelerated(self, base_state):
        """Тест обработки информации при ускоренном восприятии времени"""
        base_state.recent_events = ["event1", "event2"]
        base_state.energy = 50.0
        base_state.stability = 0.7
        base_state.planning = {"potential_sequences": [["e1", "e2"]]}
        base_state.subjective_time = 2.2  # Ускоренное восприятие
        base_state.age = 2.0
        base_state.last_event_intensity = 0.8

        process_information(base_state)

        processed = base_state.intelligence["processed_sources"]
        # При ускоренном восприятии должны быть все источники + расширенные метрики
        assert processed["memory_proxy_size"] == 2
        assert processed["adaptation_proxy"] == 50.0
        assert processed["learning_proxy"] == 0.7
        assert processed["planning_proxy_size"] == 1
        assert "subjective_time_metrics" in processed
        metrics = processed["subjective_time_metrics"]
        assert metrics["time_perception"] == "accelerated"
        assert metrics["time_ratio"] == 1.1
        assert metrics["current_subjective_time"] == 2.2
        assert metrics["intensity_smoothed"] == 0.8

    def test_process_information_subjective_time_slowed(self, base_state):
        """Тест обработки информации при замедленном восприятии времени"""
        base_state.recent_events = ["event1", "event2"]
        base_state.energy = 50.0
        base_state.stability = 0.7
        base_state.planning = {"potential_sequences": [["e1", "e2"]]}
        base_state.subjective_time = 0.8  # Замедленное восприятие
        base_state.age = 2.0

        process_information(base_state)

        processed = base_state.intelligence["processed_sources"]
        # При замедленном восприятии - только базовые источники + минимальные метрики
        assert processed["memory_proxy_size"] == 2
        assert processed["adaptation_proxy"] == 50.0
        assert "learning_proxy" not in processed  # Не должно быть
        assert "planning_proxy_size" not in processed  # Не должно быть
        assert "subjective_time_metrics" in processed
        metrics = processed["subjective_time_metrics"]
        assert metrics["time_perception"] == "slowed"
        assert metrics["time_ratio"] == 0.4
        assert "current_subjective_time" not in metrics  # Не должно быть в минимальном наборе

    def test_process_information_subjective_time_normal(self, base_state):
        """Тест обработки информации при нормальном восприятии времени"""
        base_state.recent_events = ["event1", "event2"]
        base_state.energy = 50.0
        base_state.stability = 0.7
        base_state.planning = {"potential_sequences": [["e1", "e2"]]}
        base_state.subjective_time = 1.0  # Нормальное восприятие
        base_state.age = 1.0

        process_information(base_state)

        processed = base_state.intelligence["processed_sources"]
        # При нормальном восприятии - все источники + базовые метрики времени
        assert processed["memory_proxy_size"] == 2
        assert processed["adaptation_proxy"] == 50.0
        assert processed["learning_proxy"] == 0.7
        assert processed["planning_proxy_size"] == 1
        assert "subjective_time_metrics" in processed
        metrics = processed["subjective_time_metrics"]
        assert metrics["time_perception"] == "normal"
        assert metrics["current_subjective_time"] == 1.0
        assert "time_ratio" not in metrics  # Не должно быть в базовом наборе

    def test_process_information_subjective_time_zero_age(self, base_state):
        """Тест обработки информации при нулевом возрасте"""
        base_state.recent_events = ["event1"]
        base_state.energy = 50.0
        base_state.stability = 0.7
        base_state.planning = {}
        base_state.subjective_time = 1.0
        base_state.age = 0.0  # Нулевой возраст

        process_information(base_state)

        processed = base_state.intelligence["processed_sources"]
        # При нулевом возрасте должен быть нормальный режим (ratio = 1.0)
        assert processed["memory_proxy_size"] == 1
        assert processed["adaptation_proxy"] == 50.0
        assert processed["learning_proxy"] == 0.7
        assert processed["planning_proxy_size"] == 0
        assert "subjective_time_metrics" in processed
        metrics = processed["subjective_time_metrics"]
        assert metrics["time_perception"] == "normal"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
