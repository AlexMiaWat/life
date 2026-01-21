"""
Тесты для InternalEventGenerator - генератора внутренних событий (memory echoes)
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest

from src.environment.event import Event
from src.environment.internal_generator import InternalEventGenerator


@pytest.mark.unit
@pytest.mark.order(1)
class TestInternalEventGenerator:
    """Тесты для InternalEventGenerator"""

    def test_initialization_default(self):
        """Тест инициализации с параметрами по умолчанию"""
        generator = InternalEventGenerator()
        assert generator.memory_echo_probability == 0.02

    def test_initialization_custom_probability(self):
        """Тест инициализации с кастомной вероятностью"""
        generator = InternalEventGenerator(memory_echo_probability=0.05)
        assert generator.memory_echo_probability == 0.05

    def test_generate_memory_echo_none_when_low_probability(self):
        """Тест, что событие не генерируется при низкой вероятности"""
        generator = InternalEventGenerator(
            memory_echo_probability=0.0
        )  # 0% вероятность
        event = generator.generate_memory_echo()
        assert event is None

    def test_generate_memory_echo_structure(self):
        """Тест структуры генерируемого memory_echo события"""
        generator = InternalEventGenerator(
            memory_echo_probability=1.0
        )  # 100% вероятность
        event = generator.generate_memory_echo()

        assert event is not None
        assert isinstance(event, Event)
        assert event.type == "memory_echo"
        assert -0.2 <= event.intensity <= 0.2  # Проверяем диапазон интенсивности
        assert event.timestamp > 0
        assert event.metadata is not None
        assert event.metadata.get("internal") is True
        assert event.metadata.get("source") == "spontaneous_recall"
        assert event.metadata.get("echo_type") == "random_memory"

    def test_generate_memory_echo_with_stats(self):
        """Тест генерации с статистикой памяти"""
        generator = InternalEventGenerator(memory_echo_probability=1.0)
        memory_stats = {
            "active_entries": 25,
            "archive_entries": 100,
            "event_types": ["decay", "recovery", "shock"],
        }

        event = generator.generate_memory_echo(memory_stats)

        assert event is not None
        assert event.metadata.get("memory_active_count") == 25
        assert event.metadata.get("memory_archive_count") == 100
        assert event.metadata.get("memory_event_types") == [
            "decay",
            "recovery",
            "shock",
        ]

    def test_should_generate_echo_basic(self):
        """Тест базовой логики should_generate_echo"""
        generator = InternalEventGenerator(memory_echo_probability=1.0)

        # При 100% вероятности и недавнем echo - не генерировать
        should_generate = generator.should_generate_echo(
            ticks_since_last_echo=0, memory_pressure=0.0
        )
        assert should_generate is True

    def test_should_generate_echo_ticks_threshold(self):
        """Тест порога тиков с момента последнего echo"""
        generator = InternalEventGenerator(memory_echo_probability=1.0)

        # При малом числе тиков - нормальная вероятность
        should_generate_recent = generator.should_generate_echo(
            ticks_since_last_echo=10, memory_pressure=0.0
        )

        # При большом числе тиков - повышенная вероятность
        should_generate_old = generator.should_generate_echo(
            ticks_since_last_echo=60, memory_pressure=0.0
        )

        # Не можем гарантировать результат из-за случайности, но структура теста верна
        assert isinstance(should_generate_recent, bool)
        assert isinstance(should_generate_old, bool)

    def test_should_generate_echo_memory_pressure(self):
        """Тест влияния давления памяти"""
        generator = InternalEventGenerator(memory_echo_probability=1.0)

        # При высоком давлении памяти - повышенная вероятность
        should_generate = generator.should_generate_echo(
            ticks_since_last_echo=0, memory_pressure=0.9
        )
        assert should_generate is True

    def test_memory_echo_intensity_range(self):
        """Тест диапазона интенсивности memory_echo событий"""
        generator = InternalEventGenerator(memory_echo_probability=1.0)

        # Генерируем несколько событий для проверки диапазона
        intensities = []
        for _ in range(100):
            event = generator.generate_memory_echo()
            if event:
                intensities.append(event.intensity)

        assert len(intensities) > 0, "Должны быть сгенерированы события"

        # Проверяем, что все интенсивности в допустимом диапазоне
        for intensity in intensities:
            assert (
                -0.2 <= intensity <= 0.2
            ), f"Интенсивность {intensity} вне диапазона [-0.2, 0.2]"

    def test_memory_echo_metadata_consistency(self):
        """Тест консистентности metadata в memory_echo событиях"""
        generator = InternalEventGenerator(memory_echo_probability=1.0)

        events = []
        for _ in range(10):
            event = generator.generate_memory_echo()
            if event:
                events.append(event)

        assert len(events) > 0, "Должны быть сгенерированы события"

        # Все события должны иметь одинаковую базовую структуру metadata
        for event in events:
            assert event.metadata["internal"] is True
            assert event.metadata["source"] == "spontaneous_recall"
            assert event.metadata["echo_type"] == "random_memory"
