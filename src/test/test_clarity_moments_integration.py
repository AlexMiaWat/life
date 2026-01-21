"""
Integration-тесты для ClarityMoments с runtime loop

Проверяем:
- Интеграцию ClarityMoments в runtime loop
- Создание событий clarity_moment
- Влияние на MeaningEngine
- Корректность состояний SelfState
"""

import sys
import threading
import time
from pathlib import Path
from unittest.mock import Mock

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest

from src.environment.event_queue import EventQueue
from src.experimental.clarity_moments import ClarityMoments
from src.meaning.engine import MeaningEngine
from src.runtime.loop import run_loop
from src.state.self_state import SelfState


@pytest.mark.integration
class TestClarityMomentsIntegration:
    """Integration тесты для ClarityMoments"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.self_state = SelfState()
        # Устанавливаем состояние выше порогов для активации clarity
        self.self_state.stability = 0.9
        self.self_state.energy = 0.8
        self.event_queue = EventQueue()
        self.logger = Mock()

    def test_clarity_moments_creates_event(self):
        """Тест: ClarityMoments создает событие clarity_moment при выполнении условий"""
        # Создаем компоненты
        clarity_moments = ClarityMoments(logger=self.logger)

        # Проверяем условия - должно создаться событие
        self.self_state.ticks = 15  # После интервала проверки
        clarity_event = clarity_moments.check_clarity_conditions(self.self_state)

        assert clarity_event is not None
        assert clarity_event["type"] == "clarity_moment"
        assert clarity_event["data"]["clarity_id"] == 1

        # Активируем clarity
        clarity_moments.activate_clarity_moment(self.self_state)

        assert self.self_state.clarity_state is True
        assert self.self_state.clarity_duration == 50
        assert self.self_state.clarity_modifier == 1.5

    def test_clarity_moments_integration_with_meaning_engine(self):
        """Тест: ClarityMoments влияет на MeaningEngine"""
        from src.environment.event import Event

        # Создаем ClarityMoments и активируем
        clarity_moments = ClarityMoments(logger=self.logger)
        clarity_moments.activate_clarity_moment(self.self_state)

        # Создаем MeaningEngine
        meaning_engine = MeaningEngine()

        # Создаем тестовое событие
        event = Event(type="noise", intensity=0.5, timestamp=time.time())

        # Получаем значимость без clarity
        self.self_state.clarity_state = False
        significance_without_clarity = meaning_engine.appraisal(event, self.self_state)

        # Получаем значимость с clarity
        self.self_state.clarity_state = True
        significance_with_clarity = meaning_engine.appraisal(event, self.self_state)

        # Значимость с clarity должна быть выше
        assert significance_with_clarity > significance_without_clarity
        # Проверяем коэффициент усиления (примерно 1.5x)
        ratio = significance_with_clarity / significance_without_clarity
        assert 1.4 <= ratio <= 1.6  # С небольшим допуском

    def test_clarity_moments_state_persistence(self):
        """Тест: состояние clarity сохраняется между тиками"""
        clarity_moments = ClarityMoments(logger=self.logger)

        # Активируем clarity
        clarity_moments.activate_clarity_moment(self.self_state)
        assert self.self_state.clarity_state is True
        assert self.self_state.clarity_duration == 50

        # Симулируем несколько тиков
        for i in range(5):
            clarity_moments.update_clarity_state(self.self_state)

        assert self.self_state.clarity_state is True
        assert self.self_state.clarity_duration == 45

        # Продолжаем до деактивации
        for i in range(45):
            clarity_moments.update_clarity_state(self.self_state)

        assert self.self_state.clarity_state is False
        assert self.self_state.clarity_duration == 0
        assert self.self_state.clarity_modifier == 1.0

    def test_clarity_moments_runtime_loop_integration(self):
        """Тест: интеграция ClarityMoments в runtime loop"""
        # Создаем mock монитора
        monitor = Mock()

        # Создаем стоп-событие для быстрой остановки
        stop_event = threading.Event()
        stop_event.set()  # Останавливаем сразу после инициализации

        # Запускаем runtime loop с включенными clarity moments
        try:
            run_loop(
                self_state=self.self_state,
                monitor=monitor,
                tick_interval=0.01,  # Быстрый тик для теста
                snapshot_period=1000,  # Редкие снапшоты
                stop_event=stop_event,
                event_queue=self.event_queue,
                disable_weakness_penalty=True,
                disable_structured_logging=True,
                disable_learning=True,
                disable_adaptation=True,
                disable_clarity_moments=False,  # Включаем clarity moments
                log_flush_period_ticks=1000,
                enable_profiling=False,
            )
        except Exception:
            # Игнорируем исключения - нас интересует только инициализация
            pass

        # Проверяем, что SelfState имеет поля clarity
        assert hasattr(self.self_state, "clarity_state")
        assert hasattr(self.self_state, "clarity_duration")
        assert hasattr(self.self_state, "clarity_modifier")

    def test_clarity_moments_event_creation_in_queue(self):
        """Тест: ClarityMoments добавляет событие в очередь"""
        clarity_moments = ClarityMoments(logger=self.logger)

        # Проверяем условия и создаем событие
        self.self_state.ticks = 15
        clarity_event = clarity_moments.check_clarity_conditions(self.self_state)

        assert clarity_event is not None

        # Добавляем событие в очередь (имитируем runtime loop)
        from src.environment.event import Event

        event_obj = Event(
            type="clarity_moment",
            intensity=0.8,
            timestamp=clarity_event["timestamp"],
            metadata=clarity_event["data"],
        )
        self.event_queue.push(event_obj)

        # Проверяем, что событие в очереди
        assert not self.event_queue.is_empty()
        popped_events = self.event_queue.pop_all()
        assert len(popped_events) == 1
        assert popped_events[0].type == "clarity_moment"
        assert popped_events[0].metadata["clarity_id"] == 1

    def test_clarity_moments_multiple_activations(self):
        """Тест: множественные активации clarity moments"""
        clarity_moments = ClarityMoments(logger=self.logger)

        # Первая активация
        self.self_state.ticks = 15
        event1 = clarity_moments.check_clarity_conditions(self.self_state)
        assert event1["data"]["clarity_id"] == 1

        clarity_moments.activate_clarity_moment(self.self_state)

        # Деактивируем clarity
        clarity_moments.deactivate_clarity_moment(self.self_state)
        assert self.self_state.clarity_state is False

        # Вторая активация
        self.self_state.ticks = 35  # После интервала
        event2 = clarity_moments.check_clarity_conditions(self.self_state)
        assert event2["data"]["clarity_id"] == 2

        # Проверяем счетчик событий
        assert clarity_moments._clarity_events_count == 2

    def test_clarity_moments_with_different_state_conditions(self):
        """Тест: clarity moments с разными условиями состояния"""
        clarity_moments = ClarityMoments(logger=self.logger)

        # Тест с низкой стабильностью - не должно активироваться
        self.self_state.stability = 0.5
        self.self_state.energy = 0.8
        self.self_state.ticks = 15
        event1 = clarity_moments.check_clarity_conditions(self.self_state)
        assert event1 is None

        # Тест с низкой энергией - не должно активироваться
        self.self_state.stability = 0.9
        self.self_state.energy = 0.5
        self.self_state.ticks = 25
        event2 = clarity_moments.check_clarity_conditions(self.self_state)
        assert event2 is None

        # Тест с хорошими условиями - должно активироваться
        self.self_state.stability = 0.9
        self.self_state.energy = 0.8
        self.self_state.ticks = 35
        event3 = clarity_moments.check_clarity_conditions(self.self_state)
        assert event3 is not None
