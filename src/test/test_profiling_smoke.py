"""
Дымовые тесты для профилирования runtime loop (новая функциональность)

Проверяем:
- Базовую работоспособность скрипта profile_runtime.py
- Создание профилей
- Анализ результатов профилирования
"""

import os
import sys
import tempfile
import time
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


@pytest.mark.smoke
class TestProfilingSmoke:
    """Дымовые тесты для профилирования runtime loop"""

    def test_profile_runtime_import(self):
        """Тест импорта profile_runtime"""
        import profile_runtime

        assert profile_runtime is not None
        assert hasattr(profile_runtime, "profile_runtime")

    def test_profile_runtime_basic_execution(self):
        """Тест базового выполнения profile_runtime (с коротким временем)"""
        import profile_runtime

        # Модифицируем параметры для быстрого теста
        original_run_loop = profile_runtime.run_loop

        def mock_run_loop(*args, **kwargs):
            # Имитируем короткий запуск
            time.sleep(0.01)
            return

        profile_runtime.run_loop = mock_run_loop

        try:
            # Запускаем профилирование (должно выполниться без ошибок)
            profile_runtime.profile_runtime()
            # Если дошли сюда, значит функция выполнилась без исключений

        finally:
            # Восстанавливаем оригинальную функцию
            profile_runtime.run_loop = original_run_loop

    def test_cProfile_availability(self):
        """Тест доступности cProfile"""
        import cProfile
        import pstats

        # Проверяем, что cProfile работает
        profiler = cProfile.Profile()
        profiler.enable()

        # Выполняем какую-то работу
        for i in range(100):
            _ = i * i

        profiler.disable()

        # Создаем статистику
        stats = pstats.Stats(profiler)
        assert stats is not None

        # Проверяем, что есть данные
        # stats.total_calls должно быть > 0
        assert stats.total_calls > 0

    def test_profile_file_creation(self):
        """Тест создания файлов профилей"""
        import cProfile
        import pstats

        with tempfile.TemporaryDirectory() as temp_dir:
            profile_file = os.path.join(temp_dir, "test_profile.prof")

            # Создаем профиль
            profiler = cProfile.Profile()
            profiler.enable()

            # Выполняем работу
            def test_function():
                result = 0
                for i in range(1000):
                    result += i**2
                return result

            test_function()
            profiler.disable()

            # Сохраняем профиль
            profiler.dump_stats(profile_file)
            assert os.path.exists(profile_file)

            # Загружаем профиль
            loaded_profiler = pstats.Stats(profile_file)
            assert loaded_profiler is not None
            assert loaded_profiler.total_calls > 0

    def test_profile_analysis_functions(self):
        """Тест функций анализа профилей"""
        import cProfile
        import io
        import pstats

        profiler = cProfile.Profile()
        profiler.enable()

        # Выполняем различную работу
        def cpu_intensive():
            return sum(i * i for i in range(10000))

        def memory_allocation():
            return [i for i in range(1000)]

        cpu_intensive()
        memory_allocation()

        profiler.disable()

        # Создаем статистику
        stats = pstats.Stats(profiler)

        # Тестируем различные методы анализа
        # sort_stats
        stats.sort_stats("cumulative")
        stats.sort_stats("time")

        # print_stats
        output = io.StringIO()
        stats.print_stats(10, stream=output)  # Топ 10 функций
        stats_output = output.getvalue()
        assert len(stats_output) > 0
        assert "function calls" in stats_output.lower()

        # Проверяем, что есть информация о наших функциях
        assert "cpu_intensive" in stats_output or "memory_allocation" in stats_output
