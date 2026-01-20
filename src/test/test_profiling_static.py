"""
Статические тесты для профилирования runtime loop (новая функциональность)

Проверяем:
- Структуру скрипта profile_runtime.py
- Правильность импортов
- Наличие основных функций
"""

import inspect
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


@pytest.mark.static
class TestProfilingStatic:
    """Статические тесты для профилирования runtime loop"""

    def test_profile_runtime_script_structure(self):
        """Проверка структуры скрипта profile_runtime.py"""
        # Импортируем скрипт как модуль
        import profile_runtime

        # Проверяем наличие основной функции
        assert hasattr(profile_runtime, "profile_runtime")
        assert callable(profile_runtime.profile_runtime)

    def test_profile_runtime_function_signature(self):
        """Проверка сигнатуры функции profile_runtime"""
        import profile_runtime

        sig = inspect.signature(profile_runtime.profile_runtime)
        assert len(sig.parameters) == 0  # Нет параметров
        assert sig.return_annotation == type(None)

    def test_profile_runtime_imports(self):
        """Проверка импортов в profile_runtime.py"""
        import profile_runtime

        # Проверяем наличие необходимых импортов
        assert hasattr(profile_runtime, "cProfile")
        assert hasattr(profile_runtime, "pstats")
        assert hasattr(profile_runtime, "time")

        # Проверяем импорты из src
        assert hasattr(profile_runtime, "SelfState")
        assert hasattr(profile_runtime, "EventQueue")
        assert hasattr(profile_runtime, "run_loop")
        assert hasattr(profile_runtime, "monitor")

    def test_profile_runtime_docstring(self):
        """Проверка наличия docstring"""
        import profile_runtime

        assert profile_runtime.__doc__ is not None
        assert profile_runtime.profile_runtime.__doc__ is not None

    def test_profile_runtime_source_analysis(self):
        """Анализ исходного кода profile_runtime.py"""
        import profile_runtime

        source_code = inspect.getsource(profile_runtime)

        # Проверяем наличие ключевых элементов
        assert "cProfile.Profile()" in source_code
        assert "profiler.enable()" in source_code
        assert "profiler.disable()" in source_code
        assert "pstats.Stats" in source_code
        assert "run_loop" in source_code

        # Проверяем отсутствие запрещенных паттернов
        forbidden_patterns = [
            "print(",  # Должен использовать logging
            "sys.exit",  # Не должен завершать процесс
            "subprocess",  # Не должен запускать другие процессы
        ]

        for pattern in forbidden_patterns:
            assert pattern not in source_code, f"Запрещенный паттерн найден: {pattern}"
