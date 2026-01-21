"""
Тесты для системы performance baseline (новая функциональность).

Проверяем:
- Управление baseline значениями
- Проверку регрессий производительности
- Сохранение и загрузку baseline данных
- Автоматическое обновление baseline при улучшениях
"""

import os
import sys
import tempfile
import time
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.test.performance_baseline import PerformanceBaseline, performance_baseline


@pytest.mark.performance
class TestPerformanceBaseline:
    """Тесты для системы PerformanceBaseline"""

    # ============================================================================
    # Performance Baseline Tests
    # ============================================================================

    def test_performance_baseline_instantiation(self):
        """Тест создания экземпляра PerformanceBaseline"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            baseline_file = f.name

        try:
            baseline = PerformanceBaseline(baseline_file)
            assert baseline is not None
            assert isinstance(baseline, PerformanceBaseline)
            assert baseline.baseline_file == Path(baseline_file)
        finally:
            if os.path.exists(baseline_file):
                os.unlink(baseline_file)

    def test_performance_baseline_load_empty_file(self):
        """Тест загрузки пустого baseline файла"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            baseline_file = f.name

        try:
            baseline = PerformanceBaseline(baseline_file)
            assert baseline.baselines == {}
        finally:
            if os.path.exists(baseline_file):
                os.unlink(baseline_file)

    def test_performance_baseline_get_nonexistent_baseline(self):
        """Тест получения несуществующего baseline значения"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            baseline_file = f.name

        try:
            baseline = PerformanceBaseline(baseline_file)
            value = baseline.get_baseline("test_func", "elapsed")
            assert value is None
        finally:
            if os.path.exists(baseline_file):
                os.unlink(baseline_file)

    def test_performance_baseline_set_and_get(self):
        """Тест установки и получения baseline значения"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            baseline_file = f.name

        try:
            baseline = PerformanceBaseline(baseline_file)

            # Устанавливаем значение
            baseline.set_baseline("test_func", "elapsed", 1.5)

            # Получаем значение
            value = baseline.get_baseline("test_func", "elapsed")
            assert value == 1.5

            # Проверяем сохранение на диск
            baseline2 = PerformanceBaseline(baseline_file)
            value2 = baseline2.get_baseline("test_func", "elapsed")
            assert value2 == 1.5

        finally:
            if os.path.exists(baseline_file):
                os.unlink(baseline_file)

    def test_performance_baseline_check_regression_time_based_no_baseline(self):
        """Тест проверки регрессии для временной метрики без baseline"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            baseline_file = f.name

        try:
            baseline = PerformanceBaseline(baseline_file)

            result = baseline.check_regression("test_func", "elapsed", 1.0)

            assert result["is_regression"] is False
            assert result["baseline_value"] is None
            assert result["current_value"] == 1.0
            assert result["deviation_percent"] is None
            assert "Нет baseline значения" in result["message"]

        finally:
            if os.path.exists(baseline_file):
                os.unlink(baseline_file)

    def test_performance_baseline_check_regression_time_based_improvement(self):
        """Тест проверки регрессии для временной метрики с улучшением"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            baseline_file = f.name

        try:
            baseline = PerformanceBaseline(baseline_file)

            # Устанавливаем baseline
            baseline.set_baseline("test_func", "elapsed", 2.0)

            # Проверяем улучшение (1.0 < 2.0)
            result = baseline.check_regression("test_func", "elapsed", 1.0)

            assert result["is_regression"] is False
            assert result["baseline_value"] == 2.0
            assert result["current_value"] == 1.0
            assert result["deviation_percent"] == -50.0  # (1.0-2.0)/2.0 * 100
            assert "OK" in result["message"]

        finally:
            if os.path.exists(baseline_file):
                os.unlink(baseline_file)

    def test_performance_baseline_check_regression_time_based_regression(self):
        """Тест проверки регрессии для временной метрики с регрессией"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            baseline_file = f.name

        try:
            baseline = PerformanceBaseline(baseline_file)

            # Устанавливаем baseline
            baseline.set_baseline("test_func", "elapsed", 1.0)

            # Проверяем регрессию (2.5 > 1.0 * 1.15)
            result = baseline.check_regression("test_func", "elapsed", 2.5, threshold_percent=15.0)

            assert result["is_regression"] is True
            assert result["baseline_value"] == 1.0
            assert result["current_value"] == 2.5
            assert result["deviation_percent"] == 150.0  # (2.5-1.0)/1.0 * 100
            assert "РЕГРЕССИЯ" in result["message"]

        finally:
            if os.path.exists(baseline_file):
                os.unlink(baseline_file)

    def test_performance_baseline_check_regression_performance_based_improvement(self):
        """Тест проверки регрессии для метрики производительности с улучшением"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            baseline_file = f.name

        try:
            baseline = PerformanceBaseline(baseline_file)

            # Устанавливаем baseline (ticks_per_second)
            baseline.set_baseline("test_func", "ticks_per_second", 50.0)

            # Проверяем улучшение (60.0 > 50.0)
            result = baseline.check_regression("test_func", "ticks_per_second", 60.0)

            assert result["is_regression"] is False
            assert result["baseline_value"] == 50.0
            assert result["current_value"] == 60.0
            assert result["deviation_percent"] == -20.0  # (50.0-60.0)/50.0 * 100 = -20% (улучшение)
            assert "OK" in result["message"]

        finally:
            if os.path.exists(baseline_file):
                os.unlink(baseline_file)

    def test_performance_baseline_check_regression_performance_based_regression(self):
        """Тест проверки регрессии для метрики производительности с регрессией"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            baseline_file = f.name

        try:
            baseline = PerformanceBaseline(baseline_file)

            # Устанавливаем baseline (ticks_per_second)
            baseline.set_baseline("test_func", "ticks_per_second", 100.0)

            # Проверяем регрессию (80.0 < 100.0 * 0.9)
            result = baseline.check_regression(
                "test_func", "ticks_per_second", 80.0, threshold_percent=10.0
            )

            assert result["is_regression"] is True
            assert result["baseline_value"] == 100.0
            assert result["current_value"] == 80.0
            assert result["deviation_percent"] == 20.0  # (100.0-80.0)/100.0 * 100
            assert "РЕГРЕССИЯ" in result["message"]

        finally:
            if os.path.exists(baseline_file):
                os.unlink(baseline_file)

    def test_performance_baseline_update_baseline_if_needed_no_baseline(self):
        """Тест обновления baseline при отсутствии baseline"""
        from src.test.performance_baseline import update_baseline_if_needed

        with tempfile.NamedTemporaryFile(delete=False) as f:
            baseline_file = f.name

        try:
            # Создаем временный baseline объект
            baseline = PerformanceBaseline(baseline_file)

            # Обновляем глобальный объект для теста
            import src.test.performance_baseline

            src.test.performance_baseline.performance_baseline = baseline

            # Вызываем функцию обновления
            metrics = {"elapsed": 1.5, "ticks_per_second": 100.0}
            update_baseline_if_needed("test_func", metrics, force_update=False)

            # Проверяем, что baseline установлен
            assert baseline.get_baseline("test_func", "elapsed") == 1.5
            assert baseline.get_baseline("test_func", "ticks_per_second") == 100.0

        finally:
            if os.path.exists(baseline_file):
                os.unlink(baseline_file)

    def test_performance_baseline_update_baseline_if_needed_force_update(self):
        """Тест принудительного обновления baseline"""
        from src.test.performance_baseline import update_baseline_if_needed

        with tempfile.NamedTemporaryFile(delete=False) as f:
            baseline_file = f.name

        try:
            baseline = PerformanceBaseline(baseline_file)

            # Устанавливаем начальное значение
            baseline.set_baseline("test_func", "elapsed", 2.0)

            # Обновляем глобальный объект
            import src.test.performance_baseline

            src.test.performance_baseline.performance_baseline = baseline

            # Принудительно обновляем
            metrics = {"elapsed": 1.0}
            update_baseline_if_needed("test_func", metrics, force_update=True)

            # Проверяем обновление
            assert baseline.get_baseline("test_func", "elapsed") == 1.0

        finally:
            if os.path.exists(baseline_file):
                os.unlink(baseline_file)

    def test_performance_baseline_update_baseline_significant_improvement(self):
        """Тест автоматического обновления baseline при значительном улучшении"""
        from src.test.performance_baseline import update_baseline_if_needed

        with tempfile.NamedTemporaryFile(delete=False) as f:
            baseline_file = f.name

        try:
            baseline = PerformanceBaseline(baseline_file)

            # Устанавливаем начальное значение
            baseline.set_baseline("test_func", "elapsed", 2.0)

            # Обновляем глобальный объект
            import src.test.performance_baseline

            src.test.performance_baseline.performance_baseline = baseline

            # Имитируем значительное улучшение (>20%)
            metrics = {"elapsed": 1.5}  # 2.0 * 0.75 = 1.5, что > 20% улучшения
            update_baseline_if_needed("test_func", metrics, force_update=False)

            # Проверяем, что baseline обновился
            assert baseline.get_baseline("test_func", "elapsed") == 1.5

        finally:
            if os.path.exists(baseline_file):
                os.unlink(baseline_file)

    def test_performance_baseline_update_baseline_no_significant_change(self):
        """Тест отсутствия обновления baseline при незначительном изменении"""
        from src.test.performance_baseline import update_baseline_if_needed

        with tempfile.NamedTemporaryFile(delete=False) as f:
            baseline_file = f.name

        try:
            baseline = PerformanceBaseline(baseline_file)

            # Устанавливаем начальное значение
            baseline.set_baseline("test_func", "elapsed", 2.0)

            # Обновляем глобальный объект
            import src.test.performance_baseline

            src.test.performance_baseline.performance_baseline = baseline

            # Незначительное изменение (<20%)
            metrics = {"elapsed": 1.9}  # Только 5% улучшения
            update_baseline_if_needed("test_func", metrics, force_update=False)

            # Проверяем, что baseline не обновился
            assert baseline.get_baseline("test_func", "elapsed") == 2.0

        finally:
            if os.path.exists(baseline_file):
                os.unlink(baseline_file)

    def test_performance_baseline_multiple_metrics(self):
        """Тест работы с множественными метриками"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            baseline_file = f.name

        try:
            baseline = PerformanceBaseline(baseline_file)

            # Устанавливаем несколько метрик
            baseline.set_baseline("test_func", "elapsed", 1.0)
            baseline.set_baseline("test_func", "ticks_per_second", 100.0)
            baseline.set_baseline("test_func", "memory_usage", 50.0)

            # Проверяем получение
            assert baseline.get_baseline("test_func", "elapsed") == 1.0
            assert baseline.get_baseline("test_func", "ticks_per_second") == 100.0
            assert baseline.get_baseline("test_func", "memory_usage") == 50.0

            # Проверяем сохранение
            baseline2 = PerformanceBaseline(baseline_file)
            assert baseline2.get_baseline("test_func", "elapsed") == 1.0
            assert baseline2.get_baseline("test_func", "ticks_per_second") == 100.0

        finally:
            if os.path.exists(baseline_file):
                os.unlink(baseline_file)

    def test_performance_baseline_different_test_names(self):
        """Тест изоляции baseline значений между разными тестами"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            baseline_file = f.name

        try:
            baseline = PerformanceBaseline(baseline_file)

            # Устанавливаем значения для разных тестов
            baseline.set_baseline("test_func1", "elapsed", 1.0)
            baseline.set_baseline("test_func2", "elapsed", 2.0)

            # Проверяем изоляцию
            assert baseline.get_baseline("test_func1", "elapsed") == 1.0
            assert baseline.get_baseline("test_func2", "elapsed") == 2.0

        finally:
            if os.path.exists(baseline_file):
                os.unlink(baseline_file)
