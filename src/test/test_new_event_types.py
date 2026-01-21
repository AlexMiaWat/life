"""
Тесты для новых типов событий (социальные, когнитивные, экзистенциальные)
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest

from src.environment.event import Event
from src.environment.generator import EventGenerator
from src.meaning.engine import MeaningEngine
from src.state.self_state import SelfState


@pytest.mark.unit
@pytest.mark.order(1)
class TestNewEventTypes:
    """Тесты для новых типов событий"""

    @pytest.fixture
    def generator(self):
        """Создает экземпляр генератора"""
        return EventGenerator()

    @pytest.fixture
    def meaning_engine(self):
        """Создает экземпляр MeaningEngine"""
        return MeaningEngine()

    @pytest.fixture
    def self_state(self):
        """Создает базовое состояние для тестов"""
        return SelfState()

    def test_new_event_types_in_generator(self, generator):
        """Тест, что генератор включает все новые типы событий"""
        event_types = set()
        # Генерируем достаточно событий для покрытия всех типов
        for _ in range(5000):
            event = generator.generate()
            event_types.add(event.type)

        # Проверяем наличие всех новых типов
        new_types = {
            "social_presence",
            "social_conflict",
            "social_harmony",
            "cognitive_doubt",
            "cognitive_clarity",
            "cognitive_confusion",
            "existential_void",
            "existential_purpose",
            "existential_finitude",
            "connection",
            "isolation",
            "insight",
            "confusion",
            "curiosity",
            "meaning_found",
            "void",
            "acceptance",
        }

        for new_type in new_types:
            assert new_type in event_types, f"Тип события {new_type} не генерируется"

    @pytest.mark.parametrize(
        "event_type,expected_min,expected_max",
        [
            # Социальные события
            ("social_presence", -0.4, 0.4),
            ("social_conflict", -0.6, 0.0),
            ("social_harmony", 0.0, 0.6),
            # Когнитивные события
            ("cognitive_doubt", -0.5, 0.0),
            ("cognitive_clarity", 0.0, 0.5),
            ("cognitive_confusion", -0.4, 0.0),
            # Экзистенциальные события
            ("existential_void", -0.7, 0.0),
            ("existential_purpose", 0.0, 0.7),
            ("existential_finitude", -0.6, 0.0),
            # Новые социально-эмоциональные события
            ("connection", 0.0, 0.8),
            ("isolation", -0.7, 0.0),
            # Новые когнитивные события
            ("insight", 0.0, 0.6),
            ("confusion", -0.5, 0.0),
            ("curiosity", -0.3, 0.4),
            # Новые экзистенциальные события
            ("meaning_found", 0.0, 0.9),
            ("void", -0.8, 0.0),
            ("acceptance", 0.0, 0.5),
        ],
    )
    def test_new_event_intensity_ranges(
        self, generator, event_type, expected_min, expected_max
    ):
        """Тест диапазонов интенсивности для новых типов событий"""
        # Генерируем много событий нужного типа
        intensities = []
        for _ in range(1000):
            event = generator.generate()
            if event.type == event_type:
                intensities.append(event.intensity)

        # Проверяем, что есть хотя бы несколько событий этого типа
        assert (
            len(intensities) > 0
        ), f"Не сгенерировано ни одного события типа {event_type}"

        # Проверяем диапазон
        for intensity in intensities:
            assert (
                expected_min <= intensity <= expected_max
            ), f"Интенсивность {intensity} для {event_type} вне диапазона [{expected_min}, {expected_max}]"

    def test_new_event_types_in_meaning_engine(self, meaning_engine, self_state):
        """Тест, что MeaningEngine обрабатывает все новые типы событий"""
        new_types = [
            "social_presence",
            "social_conflict",
            "social_harmony",
            "cognitive_doubt",
            "cognitive_clarity",
            "cognitive_confusion",
            "existential_void",
            "existential_purpose",
            "existential_finitude",
            "connection",
            "isolation",
            "insight",
            "confusion",
            "curiosity",
            "meaning_found",
            "void",
            "acceptance",
        ]

        for event_type in new_types:
            event = Event(type=event_type, intensity=0.5, timestamp=1000.0)
            meaning = meaning_engine.process(event, self_state)

            # Проверяем, что Meaning создан
            assert meaning is not None
            assert hasattr(meaning, "significance")
            assert hasattr(meaning, "impact")
            assert isinstance(meaning.significance, float)
            assert isinstance(meaning.impact, dict)

    def test_new_event_types_impact_calculation(self, meaning_engine, self_state):
        """Тест корректности расчета impact для новых типов событий"""
        test_cases = [
            # (event_type, intensity, expected_energy_sign, expected_stability_sign, expected_integrity_sign)
            ("social_presence", 0.2, "negative", "negative", "zero"),
            ("social_conflict", -0.3, "negative", "negative", "negative"),
            ("social_harmony", 0.4, "positive", "positive", "positive"),
            ("cognitive_doubt", -0.2, "zero", "negative", "negative"),
            ("cognitive_clarity", 0.3, "positive", "positive", "positive"),
            ("cognitive_confusion", -0.3, "negative", "negative", "negative"),
            ("existential_void", -0.5, "negative", "negative", "negative"),
            ("existential_purpose", 0.4, "positive", "positive", "positive"),
            ("existential_finitude", -0.3, "negative", "negative", "negative"),
            # Новые типы
            ("connection", 0.5, "positive", "positive", "positive"),
            ("isolation", -0.4, "negative", "negative", "negative"),
            ("insight", 0.3, "positive", "positive", "positive"),
            ("confusion", -0.3, "negative", "negative", "negative"),
            ("curiosity", 0.2, "negative", "negative", "zero"),
            ("meaning_found", 0.6, "positive", "positive", "positive"),
            ("void", -0.5, "negative", "negative", "negative"),
            ("acceptance", 0.3, "positive", "positive", "positive"),
        ]

        def check_sign(value, expected_sign):
            if expected_sign == "positive":
                return value > 0
            elif expected_sign == "negative":
                return value < 0
            elif expected_sign == "zero":
                return abs(value) < 0.001
            return True

        for (
            event_type,
            intensity,
            energy_sign,
            stability_sign,
            integrity_sign,
        ) in test_cases:
            event = Event(type=event_type, intensity=intensity, timestamp=1000.0)
            meaning = meaning_engine.process(event, self_state)

            impact = meaning.impact
            assert "energy" in impact
            assert "stability" in impact
            assert "integrity" in impact

            assert check_sign(
                impact["energy"], energy_sign
            ), f"Неверный знак energy для {event_type}: {impact['energy']}"
            assert check_sign(
                impact["stability"], stability_sign
            ), f"Неверный знак stability для {event_type}: {impact['stability']}"
            assert check_sign(
                impact["integrity"], integrity_sign
            ), f"Неверный знак integrity для {event_type}: {impact['integrity']}"

    def test_new_event_types_significance_weights(self, meaning_engine, self_state):
        """Тест корректности весов значимости для новых типов событий"""
        test_cases = [
            # (event_type, expected_weight_range)
            ("social_presence", (0.8, 1.0)),  # 0.9
            ("social_conflict", (1.1, 1.3)),  # 1.2
            ("social_harmony", (1.0, 1.2)),  # 1.1
            ("cognitive_doubt", (0.7, 0.9)),  # 0.8
            ("cognitive_clarity", (0.9, 1.1)),  # 1.0
            ("cognitive_confusion", (0.6, 0.8)),  # 0.7
            ("existential_void", (1.2, 1.4)),  # 1.3
            ("existential_purpose", (1.3, 1.5)),  # 1.4
            ("existential_finitude", (1.0, 1.2)),  # 1.1
            # Новые типы
            ("connection", (1.0, 1.2)),  # 1.1
            ("isolation", (0.9, 1.1)),  # 1.0
            ("insight", (1.1, 1.3)),  # 1.2
            ("confusion", (0.7, 0.9)),  # 0.8
            ("curiosity", (0.6, 0.8)),  # 0.7
            ("meaning_found", (1.3, 1.5)),  # 1.4
            ("void", (1.2, 1.4)),  # 1.3
            ("acceptance", (0.8, 1.0)),  # 0.9
        ]

        for event_type, (min_weight, max_weight) in test_cases:
            event = Event(type=event_type, intensity=0.5, timestamp=1000.0)
            significance = meaning_engine.appraisal(event, self_state)

            # Нормализуем значимость (без учета интенсивности)
            normalized_significance = significance / abs(event.intensity)

            assert (
                min_weight <= normalized_significance <= max_weight
            ), f"Вес значимости {normalized_significance} для {event_type} вне диапазона [{min_weight}, {max_weight}]"

    @pytest.mark.parametrize(
        "event_type",
        [
            "social_presence",
            "social_conflict",
            "social_harmony",
            "cognitive_doubt",
            "cognitive_clarity",
            "cognitive_confusion",
            "existential_void",
            "existential_purpose",
            "existential_finitude",
            "connection",
            "isolation",
            "insight",
            "confusion",
            "curiosity",
            "meaning_found",
            "void",
            "acceptance",
        ],
    )
    def test_new_event_types_response_patterns(
        self, meaning_engine, self_state, event_type
    ):
        """Тест, что для новых типов событий корректно определяются паттерны реакции"""
        event = Event(type=event_type, intensity=0.5, timestamp=1000.0)
        pattern = meaning_engine.response_pattern(event, self_state, 0.5)

        # Паттерн должен быть одной из допустимых строк
        valid_patterns = ["ignore", "absorb", "dampen", "amplify"]
        assert (
            pattern in valid_patterns
        ), f"Неверный паттерн реакции для {event_type}: {pattern}"

    def test_new_event_types_architecture_compliance(self, meaning_engine, self_state):
        """Тест соответствия новых типов событий архитектурным принципам"""
        # Проверяем, что события не содержат активного управления
        for event_type in [
            "social_presence",
            "social_conflict",
            "social_harmony",
            "cognitive_doubt",
            "cognitive_clarity",
            "cognitive_confusion",
            "existential_void",
            "existential_purpose",
            "existential_finitude",
            "connection",
            "isolation",
            "insight",
            "confusion",
            "curiosity",
            "meaning_found",
            "void",
            "acceptance",
        ]:
            event = Event(type=event_type, intensity=0.5, timestamp=1000.0)
            meaning = meaning_engine.process(event, self_state)

            # Проверяем, что impact содержит только разрешенные поля
            allowed_fields = {"energy", "stability", "integrity"}
            assert (
                set(meaning.impact.keys()) == allowed_fields
            ), f"Недопустимые поля в impact для {event_type}: {meaning.impact.keys()}"

            # Проверяем, что изменения не превышают разумные пределы
            for field, delta in meaning.impact.items():
                assert (
                    abs(delta) <= 2.0
                ), f"Слишком большое изменение {delta} для {field} в {event_type}"

    def test_new_event_types_probability_distribution(self, generator):
        """Тест вероятностного распределения новых типов событий"""
        event_counts = {}
        total_events = 10000

        # Считаем частоту каждого типа
        for _ in range(total_events):
            event = generator.generate()
            event_counts[event.type] = event_counts.get(event.type, 0) + 1

        # Проверяем, что новые типы генерируются с правильной частотой
        expected_percentages = {
            "social_presence": 0.019,
            "social_conflict": 0.014,
            "social_harmony": 0.014,
            "cognitive_doubt": 0.019,
            "cognitive_clarity": 0.014,
            "cognitive_confusion": 0.019,
            "existential_void": 0.009,
            "existential_purpose": 0.008,
            "existential_finitude": 0.011,
            # Новые типы с весом 0.01 каждый
            "connection": 0.01,
            "isolation": 0.01,
            "insight": 0.01,
            "confusion": 0.01,
            "curiosity": 0.01,
            "meaning_found": 0.01,
            "void": 0.01,
            "acceptance": 0.01,
        }

        total_new_events = sum(
            event_counts.get(t, 0) for t in expected_percentages.keys()
        )
        total_events_with_new = sum(event_counts.values())

        # Общая доля новых событий должна быть около 21%
        new_events_ratio = total_new_events / total_events_with_new
        assert (
            0.18 <= new_events_ratio <= 0.24
        ), f"Доля новых событий {new_events_ratio:.3f} вне ожидаемого диапазона [0.18, 0.24]"
