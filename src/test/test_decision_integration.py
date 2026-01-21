"""
Интеграционные тесты для Decision модуля с реальными сценариями
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


@pytest.mark.integration
class TestDecisionIntegration:
    """Интеграционные тесты Decision модуля"""

    def test_stress_scenario_shock_response(self):
        """Тест реакции на шок в стрессовой ситуации"""
        state = SelfState()
        state.energy = 25  # Низкая энергия
        state.stability = 0.3  # Низкая стабильность
        state.integrity = 0.4  # Поврежденная целостность

        # Предыдущий опыт со шоком
        state.activated_memory = [
            MemoryEntry("shock", 0.8, time.time(), weight=1.5),
            MemoryEntry("shock", 0.6, time.time(), weight=1.0),
        ]

        # Новый шоковый event
        meaning = Meaning(significance=0.9, impact={"energy": -2.0, "stability": -0.3})
        meaning.event_type = "shock"

        pattern = decide_response(state, meaning)
        # В стрессовой ситуации должен выбрать dampen для защиты
        assert pattern == "dampen"

    def test_recovery_scenario_positive_response(self):
        """Тест реакции на восстановление при низкой энергии"""
        state = SelfState()
        state.energy = 20  # Очень низкая энергия
        state.stability = 0.2  # Низкая стабильность

        # Предыдущий опыт с восстановлением
        state.activated_memory = [
            MemoryEntry("recovery", 0.7, time.time(), weight=1.2),
        ]

        # Положительное событие восстановления
        meaning = Meaning(significance=0.8, impact={"energy": +1.5, "stability": +0.2})
        meaning.event_type = "recovery"

        pattern = decide_response(state, meaning)
        # При низкой энергии и стабильности может усилить положительные эффекты
        assert pattern in ["amplify", "absorb"]

    def test_noise_filtering_high_stability(self):
        """Тест фильтрации шума при высокой стабильности"""
        state = SelfState()
        state.energy = 80  # Высокая энергия
        state.stability = 0.9  # Высокая стабильность
        state.integrity = 0.95  # Высокая целостность

        # Активная память с предыдущим шумом
        state.activated_memory = [
            MemoryEntry("noise", 0.2, time.time(), weight=0.8),
        ]

        # Новый шумовой event низкой значимости
        meaning = Meaning(significance=0.15, impact={"energy": -0.1})
        meaning.event_type = "noise"

        pattern = decide_response(state, meaning)
        # При высокой стабильности шум может игнорироваться
        assert pattern in ["ignore", "absorb"]

    def test_adaptive_learning_response(self):
        """Тест адаптивной реакции с учетом learning параметров"""
        state = SelfState()
        state.energy = 60
        state.stability = 0.7

        # Настроенные параметры обучения
        state.learning_params = {
            "event_type_sensitivity": {"shock": 0.8, "noise": 0.2},
            "significance_thresholds": {"shock": 0.3, "noise": 0.1},
        }

        state.adaptation_params = {
            "behavior_thresholds": {"shock": 0.4, "noise": 0.15},
            "behavior_sensitivity": {"shock": 0.9},
        }

        # Активная память
        state.activated_memory = [
            MemoryEntry("shock", 0.6, time.time(), weight=1.0),
        ]

        # Событие шока
        meaning = Meaning(significance=0.5, impact={"energy": -1.0})
        meaning.event_type = "shock"

        pattern = decide_response(state, meaning)
        # С учетом параметров обучения должен выбрать dampen
        assert pattern == "dampen"

    def test_subjective_time_influence(self):
        """Тест влияния субъективного времени на решение"""
        # Замедленное восприятие времени
        state_slow = SelfState()
        state_slow.subjective_time = 50
        state_slow.age = 100  # age > subjective_time = замедленное время
        state_slow.energy = 70

        # Ускоренное восприятие времени
        state_fast = SelfState()
        state_fast.subjective_time = 150
        state_fast.age = 100  # age < subjective_time = ускоренное время
        state_fast.energy = 70

        meaning = Meaning(significance=0.4, impact={"energy": -0.5})

        pattern_slow = decide_response(state_slow, meaning)
        pattern_fast = decide_response(state_fast, meaning)

        # При замедленном времени более смелый выбор
        # При ускоренном времени более осторожный выбор
        # Но конкретные паттерны зависят от других факторов
        assert pattern_slow in ["ignore", "absorb", "dampen"]
        assert pattern_fast in ["absorb", "dampen"]

    def test_social_event_context_sensitivity(self):
        """Тест контекстной чувствительности для социальных событий"""
        # Высокая стабильность - гармония
        state_stable = SelfState()
        state_stable.stability = 0.9
        state_stable.energy = 70

        meaning_harmony = Meaning(significance=0.7, impact={"stability": +0.1})
        meaning_harmony.event_type = "social_harmony"

        pattern_stable = decide_response(state_stable, meaning_harmony)
        # При высокой стабильности социальная гармония может смягчаться
        assert pattern_stable in ["dampen", "absorb"]

        # Низкая стабильность - гармония
        state_unstable = SelfState()
        state_unstable.stability = 0.2
        state_unstable.energy = 70

        pattern_unstable = decide_response(state_unstable, meaning_harmony)
        # При низкой стабильности может усилить положительные социальные эффекты
        assert pattern_unstable in ["amplify", "absorb", "dampen"]

    def test_cognitive_clarity_amplification(self):
        """Тест усиления когнитивной ясности"""
        state = SelfState()
        state.energy = 50
        state.stability = 0.5

        # Момент ясности активен
        state.clarity_state = True
        state.clarity_modifier = 1.5

        meaning = Meaning(significance=0.6, impact={"stability": +0.1, "integrity": +0.05})
        meaning.event_type = "cognitive_clarity"

        pattern = decide_response(state, meaning)
        # При моменте ясности может усилить когнитивные положительные эффекты
        assert pattern in ["amplify", "absorb"]

    def test_long_term_memory_influence(self):
        """Тест влияния долгосрочной памяти на решение"""
        state = SelfState()

        # Создаем записи с разными весами (имитируя долгосрочную память)
        recent_high_weight = MemoryEntry("shock", 0.9, time.time(), weight=2.0)
        old_low_weight = MemoryEntry("shock", 0.8, time.time() - 3600, weight=0.3)  # 1 час назад

        state.activated_memory = [recent_high_weight, old_low_weight]

        meaning = Meaning(significance=0.7, impact={"energy": -1.0})
        meaning.event_type = "shock"

        pattern = decide_response(state, meaning)
        # Недавний опыт с высоким весом должен влиять сильнее
        assert pattern == "dampen"

    def test_existential_crisis_conservative_response(self):
        """Тест консервативной реакции на экзистенциальный кризис"""
        state = SelfState()
        state.integrity = 0.3  # Низкая целостность
        state.energy = 40

        meaning = Meaning(significance=0.85, impact={"integrity": -0.1, "stability": -0.2})
        meaning.event_type = "existential_void"

        pattern = decide_response(state, meaning)
        # Экзистенциальные кризисы должны смягчаться
        assert pattern == "dampen"

    def test_full_system_integration_scenario(self):
        """Комплексный сценарий полной интеграции"""
        state = SelfState()
        state.energy = 35  # Низкая энергия
        state.stability = 0.4  # Средняя стабильность
        state.integrity = 0.6  # Средняя целостность
        state.age = 120
        state.subjective_time = 140  # Ускоренное восприятие

        # Параметры обучения
        state.learning_params = {
            "event_type_sensitivity": {"recovery": 0.8, "shock": 0.9},
            "significance_thresholds": {"recovery": 0.2, "shock": 0.3},
        }

        state.adaptation_params = {
            "behavior_thresholds": {"recovery": 0.25, "shock": 0.35},
            "behavior_sensitivity": {"recovery": 0.7},
        }

        # Активная память с предыдущим опытом
        state.activated_memory = [
            MemoryEntry("recovery", 0.6, time.time(), weight=1.5),
            MemoryEntry("shock", 0.8, time.time() - 300, weight=1.2),  # 5 мин назад
        ]

        # Тест разных типов событий
        # Учитываем влияние activated_memory с recovery (0.6 значимости)
        test_cases = [
            (
                "recovery",
                0.7,
                {"energy": +1.0},
                ["amplify", "absorb", "dampen"],
            ),  # dampen из-за памяти
            ("shock", 0.8, {"energy": -1.5}, ["dampen"]),
            (
                "noise",
                0.1,
                {"energy": -0.05},
                ["ignore", "absorb", "dampen"],
            ),  # dampen из-за памяти
        ]

        for event_type, significance, impact, expected_patterns in test_cases:
            meaning = Meaning(significance=significance, impact=impact)
            meaning.event_type = event_type

            pattern = decide_response(state, meaning)
            assert pattern in expected_patterns, f"Unexpected pattern {pattern} for {event_type}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
