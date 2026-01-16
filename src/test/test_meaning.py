"""
Подробные тесты для модуля Meaning
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import time

import pytest

from environment.event import Event
from meaning.engine import MeaningEngine
from meaning.meaning import Meaning


@pytest.mark.unit
@pytest.mark.order(1)
class TestMeaning:
    """Тесты для класса Meaning"""

    def test_meaning_creation_minimal(self):
        """Тест создания Meaning с минимальными параметрами"""
        meaning = Meaning()
        assert meaning.event_id is None
        assert meaning.significance == 0.0
        assert meaning.impact == {}

    def test_meaning_creation_full(self):
        """Тест создания Meaning со всеми параметрами"""
        meaning = Meaning(
            event_id="event_123",
            significance=0.7,
            impact={"energy": -0.5, "stability": -0.1},
        )
        assert meaning.event_id == "event_123"
        assert meaning.significance == 0.7
        assert meaning.impact == {"energy": -0.5, "stability": -0.1}

    def test_meaning_significance_validation_valid(self):
        """Тест валидации significance с валидными значениями"""
        for sig in [0.0, 0.1, 0.5, 0.9, 1.0]:
            meaning = Meaning(significance=sig)
            assert meaning.significance == sig

    def test_meaning_significance_validation_invalid_negative(self):
        """Тест валидации significance с отрицательным значением"""
        with pytest.raises(ValueError, match="significance должен быть в диапазоне"):
            Meaning(significance=-0.1)

    def test_meaning_significance_validation_invalid_above_one(self):
        """Тест валидации significance со значением больше 1.0"""
        with pytest.raises(ValueError, match="significance должен быть в диапазоне"):
            Meaning(significance=1.1)

    def test_meaning_impact_empty(self):
        """Тест Meaning с пустым impact"""
        meaning = Meaning(impact={})
        assert meaning.impact == {}

    def test_meaning_impact_multiple_params(self):
        """Тест Meaning с несколькими параметрами в impact"""
        meaning = Meaning(impact={"energy": -1.0, "stability": -0.2, "integrity": -0.1})
        assert meaning.impact["energy"] == -1.0
        assert meaning.impact["stability"] == -0.2
        assert meaning.impact["integrity"] == -0.1


@pytest.mark.unit
@pytest.mark.order(1)
class TestMeaningEngine:
    """Тесты для класса MeaningEngine"""

    @pytest.fixture
    def engine(self):
        """Создает экземпляр MeaningEngine"""
        return MeaningEngine()

    @pytest.fixture
    def normal_state(self):
        """Создает нормальное состояние"""
        return {"energy": 50.0, "stability": 0.7, "integrity": 0.8}

    @pytest.fixture
    def low_integrity_state(self):
        """Создает состояние с низкой integrity"""
        return {"energy": 50.0, "stability": 0.7, "integrity": 0.2}  # Низкая integrity

    @pytest.fixture
    def low_stability_state(self):
        """Создает состояние с низкой stability"""
        return {"energy": 50.0, "stability": 0.3, "integrity": 0.8}  # Низкая stability

    def test_engine_initialization(self, engine):
        """Тест инициализации MeaningEngine"""
        assert engine.base_significance_threshold == 0.1

    # Тесты для appraisal
    def test_appraisal_shock_event(self, engine, normal_state):
        """Тест оценки значимости shock события"""
        event = Event(type="shock", intensity=0.5, timestamp=time.time())
        significance = engine.appraisal(event, normal_state)
        assert 0.0 <= significance <= 1.0
        assert significance > 0  # Shock должен иметь значимость

    def test_appraisal_noise_event(self, engine, normal_state):
        """Тест оценки значимости noise события"""
        event = Event(type="noise", intensity=0.3, timestamp=time.time())
        significance = engine.appraisal(event, normal_state)
        assert 0.0 <= significance <= 1.0
        # Noise должен иметь меньшую значимость чем shock
        shock_event = Event(type="shock", intensity=0.3, timestamp=time.time())
        shock_sig = engine.appraisal(shock_event, normal_state)
        assert significance < shock_sig

    def test_appraisal_intensity_effect(self, engine, normal_state):
        """Тест влияния интенсивности на значимость"""
        event_low = Event(type="shock", intensity=0.2, timestamp=time.time())
        event_high = Event(type="shock", intensity=0.8, timestamp=time.time())

        sig_low = engine.appraisal(event_low, normal_state)
        sig_high = engine.appraisal(event_high, normal_state)

        assert sig_high > sig_low

    def test_appraisal_low_integrity_amplification(self, engine, low_integrity_state):
        """Тест усиления значимости при низкой integrity"""
        event = Event(type="noise", intensity=0.3, timestamp=time.time())
        sig_low_integrity = engine.appraisal(event, low_integrity_state)

        normal_state = {"energy": 50.0, "stability": 0.7, "integrity": 0.8}
        sig_normal = engine.appraisal(event, normal_state)

        assert sig_low_integrity > sig_normal

    def test_appraisal_low_stability_amplification(self, engine, low_stability_state):
        """Тест усиления значимости при низкой stability"""
        event = Event(type="noise", intensity=0.3, timestamp=time.time())
        sig_low_stability = engine.appraisal(event, low_stability_state)

        normal_state = {"energy": 50.0, "stability": 0.8, "integrity": 0.8}
        sig_normal = engine.appraisal(event, normal_state)

        assert sig_low_stability > sig_normal

    def test_appraisal_range_limits(self, engine, normal_state):
        """Тест ограничения значимости диапазоном [0.0, 1.0]"""
        # Очень высокая интенсивность
        event = Event(type="shock", intensity=2.0, timestamp=time.time())
        significance = engine.appraisal(event, normal_state)
        assert significance <= 1.0

        # Отрицательная интенсивность
        event = Event(type="shock", intensity=-0.5, timestamp=time.time())
        significance = engine.appraisal(event, normal_state)
        assert significance >= 0.0

    # Тесты для impact_model
    def test_impact_model_shock(self, engine, normal_state):
        """Тест модели влияния для shock"""
        event = Event(type="shock", intensity=1.0, timestamp=time.time())
        significance = 0.5
        impact = engine.impact_model(event, normal_state, significance)

        assert "energy" in impact
        assert "stability" in impact
        assert "integrity" in impact
        assert impact["energy"] < 0  # Shock уменьшает energy
        assert impact["stability"] < 0
        assert impact["integrity"] < 0

    def test_impact_model_recovery(self, engine, normal_state):
        """Тест модели влияния для recovery"""
        event = Event(type="recovery", intensity=1.0, timestamp=time.time())
        significance = 0.5
        impact = engine.impact_model(event, normal_state, significance)

        assert impact["energy"] > 0  # Recovery увеличивает energy
        assert impact["stability"] > 0
        assert impact["integrity"] > 0

    def test_impact_model_intensity_scaling(self, engine, normal_state):
        """Тест масштабирования влияния по интенсивности"""
        event_low = Event(type="shock", intensity=0.5, timestamp=time.time())
        event_high = Event(type="shock", intensity=1.0, timestamp=time.time())
        significance = 0.5

        impact_low = engine.impact_model(event_low, normal_state, significance)
        impact_high = engine.impact_model(event_high, normal_state, significance)

        assert abs(impact_high["energy"]) > abs(impact_low["energy"])

    def test_impact_model_significance_scaling(self, engine, normal_state):
        """Тест масштабирования влияния по significance"""
        event = Event(type="shock", intensity=1.0, timestamp=time.time())

        impact_low_sig = engine.impact_model(event, normal_state, 0.2)
        impact_high_sig = engine.impact_model(event, normal_state, 0.8)

        assert abs(impact_high_sig["energy"]) > abs(impact_low_sig["energy"])

    def test_impact_model_unknown_event_type(self, engine, normal_state):
        """Тест модели влияния для неизвестного типа события"""
        event = Event(type="unknown_type", intensity=1.0, timestamp=time.time())
        significance = 0.5
        impact = engine.impact_model(event, normal_state, significance)

        assert impact["energy"] == 0.0
        assert impact["stability"] == 0.0
        assert impact["integrity"] == 0.0

    # Тесты для response_pattern
    def test_response_pattern_ignore_low_significance(self, engine, normal_state):
        """Тест паттерна ignore при низкой значимости"""
        event = Event(type="noise", intensity=0.05, timestamp=time.time())
        significance = 0.05  # Ниже порога 0.1
        pattern = engine.response_pattern(event, normal_state, significance)
        assert pattern == "ignore"

    def test_response_pattern_dampen_high_stability(self, engine):
        """Тест паттерна dampen при высокой стабильности"""
        state = {"energy": 50.0, "stability": 0.9, "integrity": 0.8}
        event = Event(type="shock", intensity=0.5, timestamp=time.time())
        significance = 0.5
        pattern = engine.response_pattern(event, state, significance)
        assert pattern == "dampen"

    def test_response_pattern_amplify_low_stability(self, engine):
        """Тест паттерна amplify при низкой стабильности"""
        state = {"energy": 50.0, "stability": 0.2, "integrity": 0.8}
        event = Event(type="shock", intensity=0.5, timestamp=time.time())
        significance = 0.5
        pattern = engine.response_pattern(event, state, significance)
        assert pattern == "amplify"

    def test_response_pattern_absorb_normal(self, engine, normal_state):
        """Тест паттерна absorb при нормальных условиях"""
        event = Event(type="shock", intensity=0.5, timestamp=time.time())
        significance = 0.5
        pattern = engine.response_pattern(event, normal_state, significance)
        assert pattern == "absorb"

    # Тесты для process (интеграционный)
    def test_process_complete_flow(self, engine, normal_state):
        """Тест полного процесса обработки события"""
        event = Event(type="shock", intensity=0.6, timestamp=time.time())
        meaning = engine.process(event, normal_state)

        assert isinstance(meaning, Meaning)
        assert meaning.event_id is not None
        assert 0.0 <= meaning.significance <= 1.0
        assert "energy" in meaning.impact
        assert "stability" in meaning.impact
        assert "integrity" in meaning.impact

    def test_process_ignore_pattern(self, engine, normal_state):
        """Тест обработки события с паттерном ignore"""
        event = Event(type="idle", intensity=0.05, timestamp=time.time())
        meaning = engine.process(event, normal_state)

        # При ignore все impact должны быть 0
        assert all(v == 0.0 for v in meaning.impact.values())

    def test_process_dampen_pattern(self, engine):
        """Тест обработки события с паттерном dampen"""
        state = {"energy": 50.0, "stability": 0.9, "integrity": 0.8}
        event = Event(type="shock", intensity=0.5, timestamp=time.time())
        meaning = engine.process(event, state)

        # Impact должен быть уменьшен в 2 раза
        base_impact = engine.impact_model(event, state, meaning.significance)
        # Проверяем, что impact уменьшен (примерно в 2 раза)
        assert abs(meaning.impact["energy"]) < abs(base_impact["energy"])

    def test_process_amplify_pattern(self, engine):
        """Тест обработки события с паттерном amplify"""
        state = {"energy": 50.0, "stability": 0.2, "integrity": 0.8}
        event = Event(type="shock", intensity=0.5, timestamp=time.time())
        meaning = engine.process(event, state)

        # Impact должен быть увеличен в 1.5 раза
        base_impact = engine.impact_model(event, state, meaning.significance)
        # Проверяем, что impact увеличен
        assert abs(meaning.impact["energy"]) > abs(base_impact["energy"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
