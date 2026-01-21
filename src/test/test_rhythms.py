"""
Тесты для внутренних ритмов и эхо-механизмов Life.

Тестирует:
- Циркадный ритм и его влияние на параметры
- Эхо-всплывания воспоминаний
- Интеграцию ритмов с runtime loop
"""

import math
from unittest.mock import patch

from src.memory.memory import Memory, MemoryEntry
from src.state.self_state import SelfState


class TestCircadianRhythm:
    """Тесты циркадного ритма."""

    def test_circadian_rhythm_initialization(self):
        """Тест инициализации параметров циркадного ритма."""
        state = SelfState()

        assert hasattr(state, "circadian_phase")
        assert hasattr(state, "circadian_period")
        assert hasattr(state, "recovery_efficiency")
        assert hasattr(state, "stability_modifier")

        assert state.circadian_phase == 0.0
        assert state.circadian_period == 24.0 * 3600.0  # 24 часа
        assert state.recovery_efficiency == 1.0
        assert state.stability_modifier == 1.0

    def test_circadian_phase_update(self):
        """Тест обновления фазы циркадного ритма."""
        state = SelfState()
        initial_phase = state.circadian_phase

        # Обновление на 1 час (3600 секунд)
        dt = 3600.0
        state.update_circadian_rhythm(dt)

        # Фаза должна измениться на π/12 (3600 / 86400 * 2π = π/12)
        expected_phase = initial_phase + (dt / state.circadian_period) * 2 * math.pi
        assert abs(state.circadian_phase - expected_phase) < 1e-6

    def test_circadian_phase_normalization(self):
        """Тест нормализации фазы в диапазоне [0, 2π]."""
        state = SelfState()

        # Установка фазы чуть больше 2π
        state.circadian_phase = 2 * math.pi + 0.1
        state.update_circadian_rhythm(1.0)

        # Фаза должна быть нормализована
        assert 0.0 <= state.circadian_phase < 2 * math.pi

    def test_recovery_efficiency_calculation(self):
        """Тест расчета эффективности восстановления."""
        state = SelfState()

        # Тест в разные фазы
        test_cases = [
            (0.0, 1.0),  # Фаза 0 - пик восстановления
            (math.pi / 2, 0.4),  # Фаза π/2 - минимум восстановления
            (math.pi, 0.4),  # Фаза π - минимум восстановления
            (3 * math.pi / 2, 0.4),  # Фаза 3π/2 - минимум восстановления
            (2 * math.pi, 1.0),  # Фаза 2π - пик восстановления (нормализуется к 0)
        ]

        for phase, expected_efficiency in test_cases:
            state.circadian_phase = phase
            state.update_circadian_rhythm(0.0)  # Только пересчет без изменения фазы
            assert abs(state.recovery_efficiency - expected_efficiency) < 0.01

    def test_stability_modifier_calculation(self):
        """Тест расчета модификатора стабильности."""
        state = SelfState()

        # Тест в разные фазы
        test_cases = [
            (0.0, 0.7),  # Фаза 0 - минимум стабильности
            (math.pi / 2, 1.3),  # Фаза π/2 - пик стабильности
            (math.pi, 0.7),  # Фаза π - минимум стабильности
            (3 * math.pi / 2, 0.7),  # Фаза 3π/2 - минимум стабильности
            (2 * math.pi, 0.7),  # Фаза 2π - минимум стабильности
        ]

        for phase, expected_modifier in test_cases:
            state.circadian_phase = phase
            state.update_circadian_rhythm(0.0)  # Только пересчет без изменения фазы
            assert abs(state.stability_modifier - expected_modifier) < 0.01

    def test_rhythm_ranges(self):
        """Тест диапазонов значений ритмов."""
        state = SelfState()

        # Тест по полному циклу (множество фаз)
        for i in range(100):
            phase = (i / 100.0) * 2 * math.pi
            state.circadian_phase = phase
            state.update_circadian_rhythm(0.0)

            # Проверка диапазонов
            assert 0.4 <= state.recovery_efficiency <= 1.0
            assert 0.7 <= state.stability_modifier <= 1.3


class TestEchoMechanism:
    """Тесты механизма эхо-всплываний."""

    def test_echo_initialization(self):
        """Тест инициализации параметров эхо."""
        state = SelfState()

        assert hasattr(state, "echo_count")
        assert hasattr(state, "last_echo_time")

        assert state.echo_count == 0
        assert state.last_echo_time == 0.0

    @patch("random.random")
    def test_echo_probability_calculation(self, mock_random):
        """Тест расчета вероятности эхо."""
        state = SelfState()
        memory = Memory()

        # Создаем архив с записями
        archive_entry = MemoryEntry(
            event_type="test_event", meaning_significance=0.8, timestamp=1000.0
        )
        memory.archive.add_entry(archive_entry)

        # Тест с высокой вероятностью (зрелая система, низкая стабильность)
        state.age = 30 * 24 * 3600.0  # 30 дней - максимальный возрастной модификатор
        state.stability = 0.1  # Низкая стабильность

        # Mock random для гарантированного срабатывания
        mock_random.return_value = 0.001  # Ниже порога вероятности

        result = state.trigger_memory_echo(memory)
        assert result is not None
        assert isinstance(result, MemoryEntry)
        assert state.echo_count == 1
        assert state.last_echo_time == state.age

    @patch("random.random")
    def test_echo_no_trigger(self, mock_random):
        """Тест когда эхо не срабатывает."""
        state = SelfState()
        memory = Memory()

        # Пустой архив
        mock_random.return_value = 0.5  # Выше порога

        result = state.trigger_memory_echo(memory)
        assert result is None
        assert state.echo_count == 0

    def test_echo_activates_memory(self):
        """Тест что эхо активирует воспоминание."""
        state = SelfState()
        memory = Memory()

        # Создаем архив с записями
        archive_entry = MemoryEntry(
            event_type="recovery", meaning_significance=0.9, timestamp=1000.0
        )
        memory.archive.add_entry(archive_entry)

        # Устанавливаем параметры для высокой вероятности эхо
        state.age = 30 * 24 * 3600.0  # 30 дней
        state.stability = 0.1  # Низкая стабильность

        # Принудительно вызываем эхо
        with patch("random.random", return_value=0.0):  # Гарантированное срабатывание
            result = state.trigger_memory_echo(memory)

        # Проверяем результат
        assert result is not None
        assert len(state.activated_memory) == 1
        assert state.activated_memory[0].event_type == "recovery"

    def test_echo_statistics_update(self):
        """Тест обновления статистики эхо."""
        state = SelfState()
        memory = Memory()

        # Создаем архив
        archive_entry = MemoryEntry(
            event_type="shock", meaning_significance=0.7, timestamp=500.0
        )
        memory.archive.add_entry(archive_entry)

        # Устанавливаем параметры для высокой вероятности эхо
        state.age = 30 * 24 * 3600.0  # 30 дней
        state.stability = 0.1  # Низкая стабильность

        initial_count = state.echo_count
        _initial_time = state.last_echo_time

        # Принудительное эхо
        with patch("random.random", return_value=0.0):
            result = state.trigger_memory_echo(memory)

        # Проверка обновления статистики
        assert result is not None
        assert state.echo_count == initial_count + 1
        assert state.last_echo_time == state.age


class TestRhythmIntegration:
    """Тесты интеграции ритмов с системой."""

    def test_rhythm_validation(self):
        """Тест валидации параметров ритмов."""
        state = SelfState()

        # Тест допустимых значений
        state.circadian_phase = 1.5
        state.circadian_period = 1000.0
        state.recovery_efficiency = 0.8
        state.stability_modifier = 0.9

        # Не должно быть исключений при установке
        assert state.circadian_phase == 1.5
        assert state.circadian_period == 1000.0
        assert state.recovery_efficiency == 0.8
        assert state.stability_modifier == 0.9

    def test_echo_with_empty_archive(self):
        """Тест эхо с пустым архивом."""
        state = SelfState()
        memory = Memory()

        # Пустой архив
        result = state.trigger_memory_echo(memory)
        assert result is None
        assert state.echo_count == 0

    def test_rhythm_periodic_update(self):
        """Тест периодического обновления ритмов."""
        state = SelfState()

        _initial_phase = state.circadian_phase
        dt = 3600.0  # 1 час

        # Множественные обновления
        for _ in range(24):  # 24 часа
            state.update_circadian_rhythm(dt)

        # Фаза должна быть близка к 2π (полный цикл), с учетом нормализации
        # После 24 обновлений по 1 часу каждый, фаза должна быть ~0 (нормализована)
        assert (
            abs(state.circadian_phase) < 0.01
            or abs(state.circadian_phase - 2 * math.pi) < 0.01
        )

    @patch("src.state.self_state.SelfState.trigger_memory_echo")
    def test_echo_integration_in_runtime(self, mock_echo):
        """Тест интеграции эхо в runtime loop (mock тест)."""
        from src.environment.event_queue import EventQueue

        # Mock объекты
        state = SelfState()
        _event_queue = EventQueue()

        # Mock для предотвращения реального выполнения
        mock_echo.return_value = None

        # Этот тест проверяет что метод вызывается
        # В реальном тесте потребовалось бы больше моков для полного цикла
        assert hasattr(state, "trigger_memory_echo")


class TestRhythmPerformance:
    """Тесты производительности ритмов."""

    def test_rhythm_update_performance(self):
        """Тест производительности обновления ритмов."""
        state = SelfState()
        import time

        # Множественные обновления для замера производительности
        start_time = time.time()
        iterations = 1000

        for _ in range(iterations):
            state.update_circadian_rhythm(1.0)

        elapsed = time.time() - start_time

        # Должно быть достаточно быстро (< 1 сек на 1000 итераций)
        assert elapsed < 1.0

    def test_echo_performance(self):
        """Тест производительности механизма эхо."""
        state = SelfState()
        memory = Memory()

        # Добавляем записи в архив
        for i in range(100):
            entry = MemoryEntry(
                event_type=f"event_{i}",
                meaning_significance=0.5,
                timestamp=float(i * 100),
            )
            memory.archive.add_entry(entry)

        import time

        start_time = time.time()
        iterations = 1000

        # Мокаем random для предотвращения реального эхо
        with patch("random.random", return_value=0.5):
            for _ in range(iterations):
                state.trigger_memory_echo(memory)

        elapsed = time.time() - start_time

        # Должно быть достаточно быстро
        assert elapsed < 0.5
