"""
Интеграционные тесты для новой функциональности в runtime loop.

Тестируют интеграцию субъективного времени, технического монитора и моментов ясности.
"""

import tempfile
import time
from unittest.mock import Mock, patch, MagicMock

import pytest

from src.runtime.subjective_time import compute_subjective_dt
from src.technical_monitor import TechnicalBehaviorMonitor
from src.experimental.clarity_moments import ClarityMoments


class TestNewFunctionalityIntegration:
    """Интеграционные тесты новой функциональности."""

    def test_subjective_time_integration_with_self_state(self):
        """Тест интеграции субъективного времени с SelfState."""
        # Имитируем SelfState с атрибутами субъективного времени
        self_state = Mock()
        self_state.subjective_time_base_rate = 1.0
        self_state.last_event_intensity = 0.3
        self_state.stability = 0.85
        self_state.energy = 80.0
        self_state.subjective_time_intensity_coeff = 0.1
        self_state.subjective_time_stability_coeff = 0.2
        self_state.subjective_time_energy_coeff = 0.05
        self_state.subjective_time_rate_min = 0.1
        self_state.subjective_time_rate_max = 2.0
        self_state.subjective_time_intensity_smoothing = 0.3

        # Имитируем dt
        dt = 1.0

        # Расчет субъективного dt должен пройти без ошибок
        subjective_dt = compute_subjective_dt(
            dt=dt,
            base_rate=self_state.subjective_time_base_rate,
            intensity=self_state.last_event_intensity,
            stability=self_state.stability,
            energy=self_state.energy,
            intensity_coeff=self_state.subjective_time_intensity_coeff,
            stability_coeff=self_state.subjective_time_stability_coeff,
            energy_coeff=self_state.subjective_time_energy_coeff,
            rate_min=self_state.subjective_time_rate_min,
            rate_max=self_state.subjective_time_rate_max,
        )

        assert isinstance(subjective_dt, float)
        assert subjective_dt > 0

        # Имитируем применение субъективного времени (как в runtime loop)
        old_subjective_time = 100.0
        new_subjective_time = old_subjective_time + subjective_dt

        assert new_subjective_time > old_subjective_time

    def test_technical_monitor_integration_with_components(self):
        """Тест интеграции технического монитора с компонентами системы."""
        monitor = TechnicalBehaviorMonitor()

        # Создаем mock компоненты
        self_state = Mock()
        self_state.energy = 0.75
        self_state.stability = 0.8
        self_state.ticks = 50

        memory = Mock()
        memory.get_statistics.return_value = {"total_entries": 200, "efficiency": 0.82}

        learning_engine = Mock()
        learning_engine.get_parameters.return_value = {"learning_rate": 0.12, "progress": 0.68}

        adaptation_manager = Mock()
        adaptation_manager.get_parameters.return_value = {
            "adaptation_rate": 0.18,
            "stability": 0.79,
        }

        decision_engine = Mock()
        decision_engine.get_recent_decisions.return_value = [
            {"type": "decision", "timestamp": time.time()},
            {"type": "action", "timestamp": time.time()},
        ]
        decision_engine.get_statistics.return_value = {"average_time": 0.045, "accuracy": 0.87}

        # Полный цикл мониторинга
        snapshot = monitor.capture_system_snapshot(
            self_state, memory, learning_engine, adaptation_manager, decision_engine
        )
        report = monitor.analyze_snapshot(snapshot)

        # Сохранение и загрузка
        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json") as f:
            temp_path = f.name

        try:
            monitor.save_report(report, temp_path)
            loaded_report = monitor.load_report(temp_path)

            assert loaded_report is not None
            assert loaded_report.performance == report.performance
            assert loaded_report.stability == report.stability
            assert loaded_report.adaptability == report.adaptability
            assert loaded_report.integrity == report.integrity

        finally:
            import os

            os.unlink(temp_path)

    def test_clarity_moments_integration_with_runtime(self):
        """Тест интеграции моментов ясности с runtime."""
        clarity = ClarityMoments()
        self_state = Mock()

        # Имитируем несколько тиков runtime
        for tick in range(50):
            self_state.ticks = tick
            self_state.stability = 0.82  # Высокая стабильность
            self_state.energy = 0.78  # Высокая энергия
            self_state.subjective_time = tick * 1.2

            # Проверяем условия активации
            if tick % ClarityMoments.CLARITY_CHECK_INTERVAL == 0:
                event = clarity.check_clarity_conditions(self_state)
                if event:
                    clarity.activate_clarity_moment(self_state)

            # Обновляем состояние clarity
            clarity.update_clarity_state(self_state)

        # Проверяем, что система осталась стабильной
        status = clarity.get_clarity_status(self_state)
        assert isinstance(status, dict)
        assert "total_events" in status
        assert status["total_events"] >= 0

    def test_combined_subjective_time_and_clarity_integration(self):
        """Тест совместной работы субъективного времени и моментов ясности."""
        clarity = ClarityMoments()

        # Имитируем SelfState с атрибутами
        self_state = Mock()
        self_state.subjective_time_base_rate = 1.0
        self_state.last_event_intensity = 0.2
        self_state.stability = 0.88  # Высокая стабильность
        self_state.energy = 0.82  # Высокая энергия
        self_state.subjective_time_intensity_coeff = 0.1
        self_state.subjective_time_stability_coeff = 0.2
        self_state.subjective_time_energy_coeff = 0.05
        self_state.subjective_time_rate_min = 0.1
        self_state.subjective_time_rate_max = 2.0
        self_state.subjective_time_intensity_smoothing = 0.3
        self_state.subjective_time = 0.0

        # Имитируем несколько тиков
        dt = 1.0
        for tick in range(20):
            self_state.ticks = tick

            # Расчет субъективного времени
            subjective_dt = compute_subjective_dt(
                dt=dt,
                base_rate=self_state.subjective_time_base_rate,
                intensity=self_state.last_event_intensity,
                stability=self_state.stability,
                energy=self_state.energy,
                intensity_coeff=self_state.subjective_time_intensity_coeff,
                stability_coeff=self_state.subjective_time_stability_coeff,
                energy_coeff=self_state.subjective_time_energy_coeff,
                rate_min=self_state.subjective_time_rate_min,
                rate_max=self_state.subjective_time_rate_max,
            )

            # Применение субъективного времени
            self_state.subjective_time += subjective_dt

            # Проверка условий clarity
            if tick % ClarityMoments.CLARITY_CHECK_INTERVAL == 0:
                event = clarity.check_clarity_conditions(self_state)
                if event:
                    clarity.activate_clarity_moment(self_state)

            # Обновление clarity
            clarity.update_clarity_state(self_state)

            # Clarity должен влиять на восприятие времени
            if clarity.is_clarity_active(self_state):
                modifier = clarity.get_clarity_modifier(self_state)
                # В clarity время может восприниматься по-другому
                assert modifier > 1.0

        assert self_state.subjective_time > 0
        assert isinstance(self_state.subjective_time, float)

    def test_technical_monitor_with_clarity_events(self):
        """Тест технического монитора с событиями clarity."""
        monitor = TechnicalBehaviorMonitor()
        clarity = ClarityMoments()

        # Создаем SelfState с атрибутами clarity
        self_state = Mock()
        self_state.energy = 0.8
        self_state.stability = 0.85
        self_state.ticks = 0
        self_state.clarity_state = False
        self_state.clarity_duration = 0

        # Имитируем активацию clarity
        self_state.ticks = ClarityMoments.CLARITY_CHECK_INTERVAL
        self_state.stability = ClarityMoments.CLARITY_STABILITY_THRESHOLD + 0.1
        self_state.energy = ClarityMoments.CLARITY_ENERGY_THRESHOLD + 0.1
        self_state.subjective_time = 100.0

        with patch("time.time", return_value=123456.789):
            event = clarity.check_clarity_conditions(self_state)

        if event:
            clarity.activate_clarity_moment(self_state)

        # Мониторинг должен корректно обработать состояние с clarity
        memory = Mock()
        memory.get_statistics.return_value = {"total_entries": 150}

        learning_engine = Mock()
        learning_engine.get_parameters.return_value = {"learning_rate": 0.1}

        adaptation_manager = Mock()
        adaptation_manager.get_parameters.return_value = {"adaptation_rate": 0.2}

        decision_engine = Mock()
        decision_engine.get_recent_decisions.return_value = []
        decision_engine.get_statistics.return_value = {"average_time": 0.05, "accuracy": 0.9}

        snapshot = monitor.capture_system_snapshot(
            self_state, memory, learning_engine, adaptation_manager, decision_engine
        )
        report = monitor.analyze_snapshot(snapshot)

        assert report is not None
        assert isinstance(report.overall_assessment["overall_score"], float)

    def test_full_runtime_simulation(self):
        """Тест полной симуляции работы runtime с новой функциональностью."""
        # Компоненты
        monitor = TechnicalBehaviorMonitor()
        clarity = ClarityMoments()

        # SelfState с полным набором атрибутов
        self_state = Mock()
        self_state.ticks = 0
        self_state.energy = 0.8
        self_state.stability = 0.85
        self_state.subjective_time = 0.0
        self_state.subjective_time_base_rate = 1.0
        self_state.last_event_intensity = 0.1
        self_state.subjective_time_intensity_coeff = 0.1
        self_state.subjective_time_stability_coeff = 0.2
        self_state.subjective_time_energy_coeff = 0.05
        self_state.subjective_time_rate_min = 0.1
        self_state.subjective_time_rate_max = 2.0
        self_state.subjective_time_intensity_smoothing = 0.3

        # Mock компоненты
        memory = Mock()
        memory.get_statistics.return_value = {"total_entries": 100, "efficiency": 0.8}

        learning_engine = Mock()
        learning_engine.get_parameters.return_value = {"learning_rate": 0.1, "progress": 0.6}

        adaptation_manager = Mock()
        adaptation_manager.get_parameters.return_value = {
            "adaptation_rate": 0.15,
            "stability": 0.75,
        }

        decision_engine = Mock()
        decision_engine.get_recent_decisions.return_value = [
            {"type": "decision", "timestamp": time.time()}
        ]
        decision_engine.get_statistics.return_value = {"average_time": 0.04, "accuracy": 0.88}

        # Имитация 10 тиков runtime
        dt = 1.0
        for tick in range(10):
            self_state.ticks = tick

            # 1. Субъективное время
            subjective_dt = compute_subjective_dt(
                dt=dt,
                base_rate=self_state.subjective_time_base_rate,
                intensity=self_state.last_event_intensity,
                stability=self_state.stability,
                energy=self_state.energy,
                intensity_coeff=self_state.subjective_time_intensity_coeff,
                stability_coeff=self_state.subjective_time_stability_coeff,
                energy_coeff=self_state.subjective_time_energy_coeff,
                rate_min=self_state.subjective_time_rate_min,
                rate_max=self_state.subjective_time_rate_max,
            )
            self_state.subjective_time += subjective_dt

            # 2. Clarity moments
            if tick % ClarityMoments.CLARITY_CHECK_INTERVAL == 0:
                event = clarity.check_clarity_conditions(self_state)
                if event:
                    clarity.activate_clarity_moment(self_state)

            clarity.update_clarity_state(self_state)

            # 3. Технический мониторинг (каждые 5 тиков)
            if tick % 5 == 0:
                snapshot = monitor.capture_system_snapshot(
                    self_state, memory, learning_engine, adaptation_manager, decision_engine
                )
                report = monitor.analyze_snapshot(snapshot)
                monitor._add_to_history(report)

        # Проверки финального состояния
        assert self_state.subjective_time > 0
        assert isinstance(self_state.subjective_time, float)

        status = clarity.get_clarity_status(self_state)
        assert isinstance(status, dict)

        trends = monitor.get_trends(hours=1)
        if len(monitor.report_history) >= 2:
            assert isinstance(trends, dict)
            assert "performance_trend" in trends
        else:
            assert "error" in trends

    def test_error_handling_in_integration(self):
        """Тест обработки ошибок при интеграции компонентов."""
        monitor = TechnicalBehaviorMonitor()
        clarity = ClarityMoments()

        # Создаем компоненты, которые вызывают исключения
        self_state = Mock()
        self_state.energy = 0.8
        self_state.stability = 0.85
        self_state.ticks = 5

        memory = Mock()
        memory.get_statistics.side_effect = Exception("Memory error")

        learning_engine = Mock()
        learning_engine.get_parameters.side_effect = Exception("Learning error")

        adaptation_manager = Mock()
        adaptation_manager.get_parameters.side_effect = Exception("Adaptation error")

        decision_engine = Mock()
        decision_engine.get_recent_decisions.side_effect = Exception("Decision error")

        # Система должна продолжать работать несмотря на ошибки компонентов
        snapshot = monitor.capture_system_snapshot(
            self_state, memory, learning_engine, adaptation_manager, decision_engine
        )
        report = monitor.analyze_snapshot(snapshot)

        # Clarity должен работать независимо
        event = clarity.check_clarity_conditions(self_state)
        # event может быть None или dict, но не должно быть исключения

        clarity.update_clarity_state(self_state)
        status = clarity.get_clarity_status(self_state)

        assert report is not None
        assert isinstance(status, dict)

    def test_performance_impact_estimation(self):
        """Тест оценки влияния новой функциональности на производительность."""
        import time

        monitor = TechnicalBehaviorMonitor()
        clarity = ClarityMoments()

        self_state = Mock()
        self_state.energy = 0.8
        self_state.stability = 0.85
        self_state.ticks = 10
        self_state.subjective_time_base_rate = 1.0
        self_state.last_event_intensity = 0.2
        self_state.subjective_time_intensity_coeff = 0.1
        self_state.subjective_time_stability_coeff = 0.2
        self_state.subjective_time_energy_coeff = 0.05
        self_state.subjective_time_rate_min = 0.1
        self_state.subjective_time_rate_max = 2.0

        # Mock компоненты для мониторинга
        memory = Mock()
        memory.get_statistics.return_value = {"total_entries": 100}

        learning_engine = Mock()
        learning_engine.get_parameters.return_value = {"learning_rate": 0.1}

        adaptation_manager = Mock()
        adaptation_manager.get_parameters.return_value = {"adaptation_rate": 0.15}

        decision_engine = Mock()
        decision_engine.get_recent_decisions.return_value = []
        decision_engine.get_statistics.return_value = {"average_time": 0.05, "accuracy": 0.9}

        # Измеряем время выполнения операций
        start_time = time.time()

        # Выполняем операции, аналогичные runtime loop
        for _ in range(50):
            # Субъективное время
            compute_subjective_dt(
                dt=1.0,
                base_rate=self_state.subjective_time_base_rate,
                intensity=self_state.last_event_intensity,
                stability=self_state.stability,
                energy=self_state.energy,
                intensity_coeff=self_state.subjective_time_intensity_coeff,
                stability_coeff=self_state.subjective_time_stability_coeff,
                energy_coeff=self_state.subjective_time_energy_coeff,
                rate_min=self_state.subjective_time_rate_min,
                rate_max=self_state.subjective_time_rate_max,
            )

            # Clarity moments
            clarity.check_clarity_conditions(self_state)
            clarity.update_clarity_state(self_state)

            # Технический мониторинг (реже)
            if _ % 10 == 0:
                snapshot = monitor.capture_system_snapshot(
                    self_state, memory, learning_engine, adaptation_manager, decision_engine
                )
                monitor.analyze_snapshot(snapshot)

        end_time = time.time()
        execution_time = end_time - start_time

        # Проверяем, что выполнение не занимает слишком много времени
        # (приемлемое время для 50 итераций - менее 1 секунды)
        assert execution_time < 1.0, f"Слишком долгое выполнение: {execution_time} сек"
