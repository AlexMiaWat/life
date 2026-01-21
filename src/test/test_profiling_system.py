"""
Тесты для системы профилирования runtime loop (новая функциональность).

Проверяем:
- Включение профилирования через флаг --profile
- Создание .prof файлов
- Анализ результатов профилирования
- Интеграцию с cProfile
"""

import cProfile
import os
import pstats
import sys
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.runtime.loop import run_loop
from src.state.self_state import SelfState


@pytest.mark.profiling
class TestProfilingSystem:
    """Тесты для системы профилирования runtime loop"""

    # ============================================================================
    # Profiling System Tests
    # ============================================================================

    def test_profiling_enabled_flag(self):
        """Тест включения профилирования через enable_profiling=True"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Создаем mock состояние и очередь
            state = SelfState()
            stop_event = threading.Event()

            # Имитируем короткий запуск с профилированием
            with patch("cProfile.Profile") as mock_profile_class:
                mock_profile = mock_profile_class.return_value
                mock_profile.__enter__ = mock_profile
                mock_profile.__exit__ = lambda *args: None

                # Запускаем runtime loop с профилированием
                thread = threading.Thread(
                    target=run_loop,
                    args=(
                        state,
                        lambda s: None,  # monitor
                        0.01,  # tick_interval
                        1000,  # snapshot_period
                        stop_event,
                        None,  # event_queue
                        False,  # disable_weakness_penalty
                        False,  # disable_structured_logging
                        False,  # disable_learning
                        False,  # disable_adaptation
                        True,  # disable_philosophical_analysis
                        False,  # disable_philosophical_reports
                        True,  # disable_clarity_moments
                        10,  # log_flush_period_ticks
                        True,  # enable_profiling
                    ),
                )
                thread.start()

                # Даем запуститься
                time.sleep(0.05)
                stop_event.set()
                thread.join(timeout=1.0)

                # Проверяем, что cProfile был использован
                mock_profile_class.assert_called_once()
                mock_profile.enable.assert_called()
                mock_profile.disable.assert_called()

    def test_profiling_disabled_by_default(self):
        """Тест, что профилирование отключено по умолчанию"""
        with tempfile.TemporaryDirectory() as temp_dir:
            state = SelfState()
            stop_event = threading.Event()

            # Запускаем без флага профилирования
            with patch("cProfile.Profile") as mock_profile_class:
                thread = threading.Thread(
                    target=run_loop,
                    args=(
                        state,
                        lambda s: None,
                        0.01,
                        1000,
                        stop_event,
                        None,
                        False,
                        False,
                        False,
                        False,
                        True,
                        False,
                        True,
                        10,
                        False,  # enable_profiling = False
                    ),
                )
                thread.start()
                time.sleep(0.05)
                stop_event.set()
                thread.join(timeout=1.0)

                # Проверяем, что cProfile НЕ был использован
                mock_profile_class.assert_not_called()

    def test_profiling_performance_impact(self):
        """Тест оценки накладных расходов профилирования"""
        state = SelfState()
        stop_event = threading.Event()

        # Замеряем время без профилирования
        start_time = time.time()
        stop_event.clear()

        thread1 = threading.Thread(
            target=run_loop,
            args=(
                state,
                lambda s: None,
                0.01,
                1000,
                stop_event,
                None,
                False,
                False,
                False,
                False,
                True,
                False,
                True,
                10,
                False,
            ),
        )
        thread1.start()
        time.sleep(0.1)
        stop_event.set()
        thread1.join(timeout=1.0)

        time_without_profiling = time.time() - start_time

        # Замеряем время с профилированием
        state2 = SelfState()
        stop_event2 = threading.Event()
        start_time = time.time()
        stop_event2.clear()

        thread2 = threading.Thread(
            target=run_loop,
            args=(
                state2,
                lambda s: None,
                0.01,
                1000,
                stop_event2,
                None,
                False,
                False,
                False,
                False,
                True,
                False,
                True,
                10,
                True,
            ),
        )
        thread2.start()
        time.sleep(0.1)
        stop_event2.set()
        thread2.join(timeout=1.0)

        time_with_profiling = time.time() - start_time

        # Профилирование должно добавлять накладные расходы, но не катастрофические
        overhead_ratio = time_with_profiling / time_without_profiling

        # Накладные расходы должны быть разумными (< 50%)
        assert (
            overhead_ratio < 1.5
        ), f"Слишком большие накладные расходы профилирования: {overhead_ratio:.2f}x"

    def test_profiling_basic_functionality(self):
        """Тест базовой функциональности профилирования"""
        # Создаем простой профиль для проверки работоспособности
        profiler = cProfile.Profile()
        profiler.enable()

        # Выполняем некоторую работу
        result = sum(range(1000))

        profiler.disable()

        # Проверяем, что профилирование захватило вызовы
        assert result == 499500  # Проверка что работа была выполнена

        # Проверяем что профиль содержит данные
        stats = pstats.Stats(profiler)
        assert stats.total_calls > 0

    def test_profiling_analysis_output(self):
        """Тест анализа результатов профилирования"""
        # Создаем временный .prof файл для теста
        with tempfile.NamedTemporaryFile(suffix=".prof", delete=False) as f:
            prof_file = f.name

        try:
            # Создаем простой профиль для теста
            profiler = cProfile.Profile()
            profiler.enable()

            # Имитируем некоторую работу
            for i in range(1000):
                _ = i * i

            profiler.disable()
            profiler.dump_stats(prof_file)

            # Читаем и анализируем профиль
            stats = pstats.Stats(prof_file)
            stats.sort_stats("cumulative")

            # Проверяем, что профиль содержит данные
            assert stats.total_calls > 0

            # Получаем топ функций
            top_functions = []
            for func in stats.fcn_list[:5]:  # Топ 5 функций
                cc, nc, tt, ct, callers = stats.stats[func]
                top_functions.append((func, ct))  # cumulative time

            # Проверяем, что есть хотя бы одна функция
            assert len(top_functions) > 0

            # Проверяем, что cumulative time - число
            for func, cum_time in top_functions:
                assert isinstance(cum_time, float)
                assert cum_time >= 0

        finally:
            if os.path.exists(prof_file):
                os.unlink(prof_file)
