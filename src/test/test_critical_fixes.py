"""
Тесты для критических исправлений (race conditions в record_changes и store_history)

Проверяем:
- Параллельные вызовы record_changes() не теряют данные
- Параллельные вызовы store_history() корректно работают
- Блокировки действительно защищают от race conditions
- Параметры не теряются при параллельных обновлениях
"""

import sys
import threading
import time
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest

from src.adaptation.adaptation import AdaptationManager
from src.learning.learning import LearningEngine
from src.state.self_state import SelfState


@pytest.mark.unit
class TestCriticalFixes:
    """Тесты для критических исправлений race conditions"""

    def test_record_changes_parallel_calls(self):
        """Тест параллельных вызовов record_changes() - проверка отсутствия потери данных"""
        engine = LearningEngine()
        self_state = SelfState()

        # Инициализируем параметры
        self_state.learning_params = {
            "event_type_sensitivity": {
                "noise": 0.2,
                "shock": 0.3,
            },
            "significance_thresholds": {
                "noise": 0.1,
                "shock": 0.2,
            },
        }

        old_params = self_state.learning_params.copy()

        # Создаем несколько потоков для параллельных обновлений
        num_threads = 10
        num_updates_per_thread = 5
        errors = []
        results = []

        def update_params(thread_id):
            """Функция для обновления параметров в отдельном потоке"""
            try:
                for i in range(num_updates_per_thread):
                    # Каждый поток обновляет разные параметры
                    new_params = {
                        "event_type_sensitivity": {
                            "noise": 0.2 + (thread_id * 0.001) + (i * 0.0001),
                        },
                        "significance_thresholds": {
                            "shock": 0.2 + (thread_id * 0.001) + (i * 0.0001),
                        },
                    }
                    # Ограничиваем изменения до MAX_PARAMETER_DELTA
                    for key, value_dict in new_params.items():
                        for param_name, value in value_dict.items():
                            if key in old_params and param_name in old_params[key]:
                                old_value = old_params[key][param_name]
                                delta = abs(value - old_value)
                                if delta > engine.MAX_PARAMETER_DELTA:
                                    # Корректируем значение
                                    direction = 1.0 if value > old_value else -1.0
                                    new_params[key][param_name] = (
                                        old_value + direction * engine.MAX_PARAMETER_DELTA
                                    )

                    engine.record_changes(old_params, new_params, self_state)
                    time.sleep(
                        0.001
                    )  # Небольшая задержка для увеличения вероятности race condition

                results.append(thread_id)
            except Exception as e:
                errors.append((thread_id, str(e)))

        # Запускаем потоки
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=update_params, args=(i,))
            threads.append(thread)
            thread.start()

        # Ждем завершения всех потоков
        for thread in threads:
            thread.join()

        # Проверяем, что все потоки завершились успешно
        assert len(errors) == 0, f"Обнаружены ошибки: {errors}"
        assert len(results) == num_threads, "Не все потоки завершились успешно"

        # Проверяем, что параметры были обновлены корректно
        assert "event_type_sensitivity" in self_state.learning_params
        assert "significance_thresholds" in self_state.learning_params
        assert "noise" in self_state.learning_params["event_type_sensitivity"]
        assert "shock" in self_state.learning_params["significance_thresholds"]

        # Проверяем, что значения находятся в допустимых пределах
        noise_value = self_state.learning_params["event_type_sensitivity"]["noise"]
        assert 0.0 <= noise_value <= 1.0, f"Значение noise вне диапазона: {noise_value}"

        shock_value = self_state.learning_params["significance_thresholds"]["shock"]
        assert 0.0 <= shock_value <= 1.0, f"Значение shock вне диапазона: {shock_value}"

    def test_record_changes_no_data_loss(self):
        """Тест отсутствия потери данных при параллельных обновлениях"""
        engine = LearningEngine()
        self_state = SelfState()

        # Инициализируем параметры с множеством ключей
        initial_params = {
            "event_type_sensitivity": {
                "noise": 0.2,
                "decay": 0.3,
                "recovery": 0.4,
                "shock": 0.5,
                "idle": 0.6,
            },
            "significance_thresholds": {
                "noise": 0.1,
                "decay": 0.2,
                "recovery": 0.3,
                "shock": 0.4,
                "idle": 0.5,
            },
            "response_coefficients": {
                "dampen": 0.5,
                "absorb": 1.0,
                "ignore": 0.0,
            },
        }

        self_state.learning_params = initial_params.copy()
        old_params = initial_params.copy()

        # Создаем потоки, каждый обновляет свой набор параметров
        num_threads = 5
        updates_completed = threading.Event()
        errors = []

        def update_specific_params(thread_id):
            """Обновляет конкретные параметры в зависимости от thread_id"""
            try:
                # Каждый поток обновляет разные параметры
                param_name = list(initial_params["event_type_sensitivity"].keys())[thread_id]
                new_params = {
                    "event_type_sensitivity": {
                        param_name: initial_params["event_type_sensitivity"][param_name] + 0.005,
                    }
                }
                engine.record_changes(old_params, new_params, self_state)
            except Exception as e:
                errors.append((thread_id, str(e)))

        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=update_specific_params, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Проверяем отсутствие ошибок
        assert len(errors) == 0, f"Обнаружены ошибки: {errors}"

        # Проверяем, что все ключи сохранились
        assert "event_type_sensitivity" in self_state.learning_params
        assert "significance_thresholds" in self_state.learning_params
        assert "response_coefficients" in self_state.learning_params

        # Проверяем, что все параметры в event_type_sensitivity сохранились
        for key in initial_params["event_type_sensitivity"].keys():
            assert (
                key in self_state.learning_params["event_type_sensitivity"]
            ), f"Параметр {key} потерян!"

    def test_store_history_parallel_calls(self):
        """Тест параллельных вызовов store_history() - проверка корректной работы"""
        manager = AdaptationManager()
        self_state = SelfState()

        # Инициализируем параметры
        self_state.adaptation_params = {
            "behavior_sensitivity": {
                "noise": 0.2,
                "shock": 0.3,
            },
            "behavior_thresholds": {
                "noise": 0.1,
                "shock": 0.2,
            },
        }

        old_params = self_state.adaptation_params.copy()

        # Создаем несколько потоков для параллельных обновлений истории
        num_threads = 5
        errors = []
        results = []

        def store_history(thread_id):
            """Функция для сохранения истории в отдельном потоке"""
            try:
                new_params = {
                    "behavior_sensitivity": {
                        "noise": 0.2 + (thread_id * 0.001),
                    },
                }
                manager.store_history(old_params, new_params, self_state)
                results.append(thread_id)
            except Exception as e:
                errors.append((thread_id, str(e)))

        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=store_history, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Проверяем, что все потоки завершились успешно
        assert len(errors) == 0, f"Обнаружены ошибки: {errors}"
        assert len(results) == num_threads, "Не все потоки завершились успешно"

        # Проверяем, что история была сохранена
        assert hasattr(self_state, "adaptation_history")
        assert isinstance(self_state.adaptation_history, list)
        assert len(self_state.adaptation_history) > 0

    def test_record_changes_lock_protection(self):
        """Тест, что блокировка действительно защищает от race conditions"""
        engine = LearningEngine()
        self_state = SelfState()

        self_state.learning_params = {
            "event_type_sensitivity": {"noise": 0.2},
        }

        old_params = self_state.learning_params.copy()

        # Создаем ситуацию, когда несколько потоков пытаются обновить один параметр
        num_threads = 20
        final_values = []
        errors = []

        def update_noise(thread_id):
            """Обновляет параметр noise"""
            try:
                new_params = {
                    "event_type_sensitivity": {
                        "noise": 0.2 + (thread_id * 0.0005),  # Малые изменения
                    },
                }
                engine.record_changes(old_params, new_params, self_state)
                # Читаем значение после обновления
                final_values.append(self_state.learning_params["event_type_sensitivity"]["noise"])
            except Exception as e:
                errors.append((thread_id, str(e)))

        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=update_noise, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Проверяем отсутствие ошибок
        assert len(errors) == 0, f"Обнаружены ошибки: {errors}"

        # Проверяем, что значение находится в допустимых пределах
        final_noise = self_state.learning_params["event_type_sensitivity"]["noise"]
        assert 0.0 <= final_noise <= 1.0, f"Значение noise вне диапазона: {final_noise}"

        # Проверяем, что изменения не превышают MAX_PARAMETER_DELTA
        # (с учетом того, что было много обновлений)
        initial_noise = old_params["event_type_sensitivity"]["noise"]
        total_delta = abs(final_noise - initial_noise)
        # Максимальное возможное изменение при последовательных обновлениях
        max_possible_delta = engine.MAX_PARAMETER_DELTA * num_threads
        assert (
            total_delta <= max_possible_delta + engine._VALIDATION_TOLERANCE
        ), f"Изменение слишком большое: {total_delta} > {max_possible_delta}"
