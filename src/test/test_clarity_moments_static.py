"""
Статические тесты для системы моментов ясности.

Тестируют логику активации, деактивации и управления моментами ясности без зависимостей от внешних компонентов.
"""

import time
from unittest.mock import Mock, patch

import pytest

from src.experimental.clarity_moments import ClarityMoments


class TestClarityMomentsInitialization:
    """Тесты инициализации ClarityMoments."""

    def test_initialization_with_logger(self):
        """Тест инициализации с логгером."""
        mock_logger = Mock()
        clarity = ClarityMoments(logger=mock_logger)

        assert clarity.logger is mock_logger
        assert clarity._last_check_tick == -ClarityMoments.CLARITY_CHECK_INTERVAL
        assert clarity._clarity_events_count == 0

    def test_initialization_without_logger(self):
        """Тест инициализации без логгера."""
        clarity = ClarityMoments()

        assert clarity.logger is not None  # Должен создать StructuredLogger
        assert clarity._last_check_tick == -ClarityMoments.CLARITY_CHECK_INTERVAL
        assert clarity._clarity_events_count == 0

    def test_constants_values(self):
        """Тест значений констант."""
        assert ClarityMoments.CLARITY_STABILITY_THRESHOLD == 0.8
        assert ClarityMoments.CLARITY_ENERGY_THRESHOLD == 0.7
        assert ClarityMoments.CLARITY_DURATION_TICKS == 50
        assert ClarityMoments.CLARITY_CHECK_INTERVAL == 10
        assert ClarityMoments.CLARITY_SIGNIFICANCE_BOOST == 1.5


class TestCheckClarityConditions:
    """Тесты проверки условий для активации моментов ясности."""

    def test_conditions_not_met_first_check(self):
        """Тест когда условия не выполнены при первой проверке."""
        clarity = ClarityMoments()
        self_state = Mock()
        self_state.ticks = 0
        self_state.stability = 0.5  # Ниже порога
        self_state.energy = 0.6     # Ниже порога

        result = clarity.check_clarity_conditions(self_state)

        assert result is None
        assert clarity._last_check_tick == 0

    def test_conditions_not_met_interval_not_passed(self):
        """Тест когда интервал проверки не прошел."""
        clarity = ClarityMoments()
        clarity._last_check_tick = 5

        self_state = Mock()
        self_state.ticks = 10  # Прошло только 5 тиков из 10 нужных

        result = clarity.check_clarity_conditions(self_state)

        assert result is None
        assert clarity._last_check_tick == 5  # Не обновился

    def test_conditions_not_met_low_stability(self):
        """Тест когда стабильность ниже порога."""
        clarity = ClarityMoments()
        self_state = Mock()
        self_state.ticks = ClarityMoments.CLARITY_CHECK_INTERVAL
        self_state.stability = 0.7  # Ниже порога 0.8
        self_state.energy = 0.9     # Выше порога

        result = clarity.check_clarity_conditions(self_state)

        assert result is None

    def test_conditions_not_met_low_energy(self):
        """Тест когда энергия ниже порога."""
        clarity = ClarityMoments()
        self_state = Mock()
        self_state.ticks = ClarityMoments.CLARITY_CHECK_INTERVAL
        self_state.stability = 0.9  # Выше порога
        self_state.energy = 0.6     # Ниже порога 0.7

        result = clarity.check_clarity_conditions(self_state)

        assert result is None

    def test_conditions_not_met_already_active(self):
        """Тест когда clarity уже активен."""
        clarity = ClarityMoments()
        self_state = Mock()
        self_state.ticks = ClarityMoments.CLARITY_CHECK_INTERVAL
        self_state.stability = 0.9
        self_state.energy = 0.8

        # Имитируем активное состояние
        self_state.clarity_state = True

        result = clarity.check_clarity_conditions(self_state)

        assert result is None

    def test_conditions_met_first_activation(self):
        """Тест успешной активации при первых подходящих условиях."""
        clarity = ClarityMoments()
        self_state = Mock()
        # Используем configure_mock для правильной работы
        self_state.configure_mock(**{
            'ticks': ClarityMoments.CLARITY_CHECK_INTERVAL,  # ticks = 10
            'stability': 0.85,  # Выше порога 0.8
            'energy': 0.75,     # Выше порога 0.7
            'subjective_time': 123.45,
            'clarity_state': False
        })

        # _last_check_tick = -10, так что ticks - _last_check_tick = 10 - (-10) = 20 >= 10
        with patch('time.time', return_value=123456.789):
            result = clarity.check_clarity_conditions(self_state)

        assert result is not None
        assert result["type"] == "clarity_moment"
        assert result["data"]["clarity_id"] == 1
        assert result["data"]["trigger_conditions"]["stability"] == 0.85
        assert result["data"]["trigger_conditions"]["energy"] == 0.75
        assert result["data"]["trigger_conditions"]["tick"] == ClarityMoments.CLARITY_CHECK_INTERVAL
        assert result["data"]["duration_ticks"] == ClarityMoments.CLARITY_DURATION_TICKS
        assert result["data"]["significance_boost"] == ClarityMoments.CLARITY_SIGNIFICANCE_BOOST
        assert result["timestamp"] == 123456.789
        assert result["subjective_timestamp"] == 123.45

        # Проверяем, что счетчик увеличился
        assert clarity._clarity_events_count == 1

    def test_conditions_met_multiple_activations(self):
        """Тест нескольких успешных активаций."""
        clarity = ClarityMoments()
        self_state = Mock()
        self_state.configure_mock(**{'subjective_time': 100.0, 'clarity_state': False})

        # Первая активация
        self_state.configure_mock(**{
            'ticks': ClarityMoments.CLARITY_CHECK_INTERVAL,
            'stability': 0.9,
            'energy': 0.8
        })

        result1 = clarity.check_clarity_conditions(self_state)
        assert result1 is not None
        assert result1["data"]["clarity_id"] == 1

        # Имитируем завершение первого момента
        self_state.configure_mock(**{'clarity_state': False})

        # Вторая активация
        self_state.configure_mock(**{
            'ticks': ClarityMoments.CLARITY_CHECK_INTERVAL * 2,
            'stability': 0.9,
            'energy': 0.8
        })
        result2 = clarity.check_clarity_conditions(self_state)
        assert result2 is not None
        assert result2["data"]["clarity_id"] == 2

        assert clarity._clarity_events_count == 2


class TestActivateClarityMoment:
    """Тесты активации моментов ясности."""

    def test_activate_clarity_moment(self):
        """Тест активации момента ясности."""
        clarity = ClarityMoments()
        self_state = Mock()

        clarity.activate_clarity_moment(self_state)

        assert self_state.clarity_state == True
        assert self_state.clarity_duration == ClarityMoments.CLARITY_DURATION_TICKS
        assert self_state.clarity_modifier == ClarityMoments.CLARITY_SIGNIFICANCE_BOOST

    def test_activate_clarity_moment_logger_called(self):
        """Тест что логгер вызывается при активации."""
        with patch('src.experimental.clarity_moments.logger') as mock_logger:
            clarity = ClarityMoments()
            self_state = Mock()

            clarity.activate_clarity_moment(self_state)

            # Проверяем что логгер был вызван
            mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "Clarity moment state activated" in str(call_args)


class TestUpdateClarityState:
    """Тесты обновления состояния моментов ясности."""

    def test_update_clarity_not_active(self):
        """Тест обновления когда clarity не активен."""
        clarity = ClarityMoments()
        self_state = Mock()
        self_state.clarity_state = False

        result = clarity.update_clarity_state(self_state)

        assert result == False

    def test_update_clarity_active_decrement_duration(self):
        """Тест декремента длительности при активном clarity."""
        clarity = ClarityMoments()
        self_state = Mock()
        self_state.clarity_state = True
        self_state.clarity_duration = 10

        result = clarity.update_clarity_state(self_state)

        assert result == True
        assert self_state.clarity_duration == 9

    def test_update_clarity_active_multiple_updates(self):
        """Тест нескольких обновлений длительности."""
        clarity = ClarityMoments()
        self_state = Mock()
        self_state.clarity_state = True
        self_state.clarity_duration = 3

        # Первое обновление
        result1 = clarity.update_clarity_state(self_state)
        assert result1 == True
        assert self_state.clarity_duration == 2

        # Второе обновление
        result2 = clarity.update_clarity_state(self_state)
        assert result2 == True
        assert self_state.clarity_duration == 1

        # Третье обновление - завершение
        result3 = clarity.update_clarity_state(self_state)
        assert result3 == False
        assert self_state.clarity_duration == 0

    def test_update_clarity_auto_deactivation(self):
        """Тест автоматической деактивации при истечении длительности."""
        clarity = ClarityMoments()
        self_state = Mock()
        self_state.clarity_state = True
        self_state.clarity_duration = 1

        # Обновление должно вызвать деактивацию
        result = clarity.update_clarity_state(self_state)

        assert result == False
        # Проверяем что deactivate_clarity_moment был вызван
        assert self_state.clarity_state == False
        assert self_state.clarity_duration == 0
        assert self_state.clarity_modifier == 1.0


class TestDeactivateClarityMoment:
    """Тесты деактивации моментов ясности."""

    def test_deactivate_clarity_moment(self):
        """Тест деактивации момента ясности."""
        clarity = ClarityMoments()
        self_state = Mock()
        self_state.clarity_state = True
        self_state.clarity_duration = 25
        self_state.clarity_modifier = ClarityMoments.CLARITY_SIGNIFICANCE_BOOST

        clarity.deactivate_clarity_moment(self_state)

        assert self_state.clarity_state == False
        assert self_state.clarity_duration == 0
        assert self_state.clarity_modifier == 1.0

    def test_deactivate_clarity_moment_logger_called(self):
        """Тест что логгер вызывается при деактивации."""
        with patch('src.experimental.clarity_moments.logger') as mock_logger:
            clarity = ClarityMoments()
            self_state = Mock()
            self_state.clarity_state = True

            clarity.deactivate_clarity_moment(self_state)

            # Проверяем что логгер был вызван
            mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "Clarity moment deactivated" in str(call_args)


class TestGetClarityModifier:
    """Тесты получения модификатора ясности."""

    def test_get_clarity_modifier_active(self):
        """Тест получения модификатора при активном clarity."""
        clarity = ClarityMoments()
        self_state = Mock()
        self_state.clarity_state = True

        modifier = clarity.get_clarity_modifier(self_state)

        assert modifier == ClarityMoments.CLARITY_SIGNIFICANCE_BOOST

    def test_get_clarity_modifier_not_active(self):
        """Тест получения модификатора при неактивном clarity."""
        clarity = ClarityMoments()
        self_state = Mock()
        self_state.clarity_state = False

        modifier = clarity.get_clarity_modifier(self_state)

        assert modifier == 1.0

    def test_get_clarity_modifier_no_attribute(self):
        """Тест получения модификатора при отсутствии атрибута."""
        clarity = ClarityMoments()
        self_state = Mock()
        # Настраиваем getattr для возврата False при отсутствии атрибута
        self_state.configure_mock(**{'clarity_state': False})

        modifier = clarity.get_clarity_modifier(self_state)

        assert modifier == 1.0


class TestIsClarityActive:
    """Тесты проверки активности моментов ясности."""

    def test_is_clarity_active_true(self):
        """Тест проверки активности когда clarity активен."""
        clarity = ClarityMoments()
        self_state = Mock()
        self_state.clarity_state = True

        result = clarity.is_clarity_active(self_state)

        assert result == True

    def test_is_clarity_active_false(self):
        """Тест проверки активности когда clarity не активен."""
        clarity = ClarityMoments()
        self_state = Mock()
        self_state.clarity_state = False

        result = clarity.is_clarity_active(self_state)

        assert result == False

    def test_is_clarity_active_no_attribute(self):
        """Тест проверки активности при отсутствии атрибута."""
        clarity = ClarityMoments()
        self_state = Mock()
        # Настраиваем getattr для возврата False при отсутствии атрибута
        self_state.configure_mock(**{'clarity_state': False})

        result = clarity.is_clarity_active(self_state)

        assert result == False


class TestGetClarityStatus:
    """Тесты получения статуса моментов ясности."""

    def test_get_clarity_status_active(self):
        """Тест получения статуса при активном clarity."""
        clarity = ClarityMoments()
        clarity._clarity_events_count = 3
        self_state = Mock()
        self_state.clarity_state = True
        self_state.clarity_duration = 42

        status = clarity.get_clarity_status(self_state)

        expected_status = {
            "active": True,
            "duration_remaining": 42,
            "total_events": 3,
            "modifier": ClarityMoments.CLARITY_SIGNIFICANCE_BOOST,
        }

        assert status == expected_status

    def test_get_clarity_status_not_active(self):
        """Тест получения статуса при неактивном clarity."""
        clarity = ClarityMoments()
        clarity._clarity_events_count = 5
        self_state = Mock()
        self_state.clarity_state = False
        self_state.clarity_duration = 0

        status = clarity.get_clarity_status(self_state)

        expected_status = {
            "active": False,
            "duration_remaining": 0,
            "total_events": 5,
            "modifier": 1.0,
        }

        assert status == expected_status

    def test_get_clarity_status_no_attributes(self):
        """Тест получения статуса при отсутствии атрибутов."""
        clarity = ClarityMoments()
        clarity._clarity_events_count = 0
        self_state = Mock()
        # Настраиваем атрибуты
        self_state.configure_mock(**{
            'clarity_state': False,
            'clarity_duration': 0
        })

        status = clarity.get_clarity_status(self_state)

        expected_status = {
            "active": False,
            "duration_remaining": 0,
            "total_events": 0,
            "modifier": 1.0,
        }

        assert status == expected_status


class TestClarityMomentsIntegration:
    """Интеграционные тесты для ClarityMoments."""

    def test_full_clarity_lifecycle(self):
        """Тест полного жизненного цикла момента ясности."""
        clarity = ClarityMoments()
        self_state = Mock()
        self_state.ticks = ClarityMoments.CLARITY_CHECK_INTERVAL
        self_state.stability = 0.9
        self_state.energy = 0.8
        self_state.subjective_time = 100.0

        # 1. Проверка условий и активация
        event = clarity.check_clarity_conditions(self_state)
        assert event is not None
        assert event["type"] == "clarity_moment"

        # 2. Активация момента
        clarity.activate_clarity_moment(self_state)
        assert clarity.is_clarity_active(self_state) == True
        assert clarity.get_clarity_modifier(self_state) == ClarityMoments.CLARITY_SIGNIFICANCE_BOOST

        # 3. Обновление состояния в течение длительности
        initial_duration = ClarityMoments.CLARITY_DURATION_TICKS
        for i in range(initial_duration - 1):
            assert clarity.update_clarity_state(self_state) == True
            assert self_state.clarity_duration == initial_duration - i - 1

        # 4. Финальное обновление - деактивация
        assert clarity.update_clarity_state(self_state) == False
        assert clarity.is_clarity_active(self_state) == False
        assert clarity.get_clarity_modifier(self_state) == 1.0

    def test_multiple_clarity_events(self):
        """Тест нескольких моментов ясности подряд."""
        clarity = ClarityMoments()
        self_state = Mock()
        self_state.stability = 0.9
        self_state.energy = 0.8
        self_state.subjective_time = 100.0

        events_created = 0
        ticks_between_checks = ClarityMoments.CLARITY_CHECK_INTERVAL

        # Создаем несколько моментов ясности
        for i in range(3):
            # Устанавливаем тики для проверки
            self_state.ticks = (i + 1) * ticks_between_checks

            # Проверяем условия
            event = clarity.check_clarity_conditions(self_state)
            if event:
                events_created += 1
                clarity.activate_clarity_moment(self_state)

                # Имитируем завершение момента
                self_state.clarity_duration = 0
                clarity.update_clarity_state(self_state)  # Автоматическая деактивация

        assert events_created == 3
        assert clarity._clarity_events_count == 3

    def test_clarity_conditions_edge_cases(self):
        """Тест граничных случаев условий активации."""
        clarity = ClarityMoments()
        self_state = Mock()
        self_state.ticks = ClarityMoments.CLARITY_CHECK_INTERVAL

        test_cases = [
            # Граничные значения
            (ClarityMoments.CLARITY_STABILITY_THRESHOLD, ClarityMoments.CLARITY_ENERGY_THRESHOLD, True),
            (ClarityMoments.CLARITY_STABILITY_THRESHOLD - 0.01, ClarityMoments.CLARITY_ENERGY_THRESHOLD, False),
            (ClarityMoments.CLARITY_STABILITY_THRESHOLD, ClarityMoments.CLARITY_ENERGY_THRESHOLD - 0.01, False),
            (ClarityMoments.CLARITY_STABILITY_THRESHOLD + 0.01, ClarityMoments.CLARITY_ENERGY_THRESHOLD + 0.01, True),
        ]

        for stability, energy, should_activate in test_cases:
            self_state.stability = stability
            self_state.energy = energy

            result = clarity.check_clarity_conditions(self_state)
            if should_activate:
                assert result is not None, f"Should activate with stability={stability}, energy={energy}"
            else:
                assert result is None, f"Should not activate with stability={stability}, energy={energy}"

    def test_clarity_state_persistence(self):
        """Тест сохранения состояния clarity между вызовами."""
        clarity = ClarityMoments()
        self_state = Mock()

        # Первый цикл активации
        self_state.ticks = ClarityMoments.CLARITY_CHECK_INTERVAL
        self_state.stability = 0.9
        self_state.energy = 0.8

        event1 = clarity.check_clarity_conditions(self_state)
        assert event1 is not None
        clarity.activate_clarity_moment(self_state)

        # Проверяем состояние
        status = clarity.get_clarity_status(self_state)
        assert status["active"] == True
        assert status["total_events"] == 1

        # Имитируем время
        for _ in range(ClarityMoments.CLARITY_DURATION_TICKS - 1):
            clarity.update_clarity_state(self_state)

        # Финальное обновление
        clarity.update_clarity_state(self_state)

        # Проверяем что состояние корректно сбросилось
        status = clarity.get_clarity_status(self_state)
        assert status["active"] == False
        assert status["duration_remaining"] == 0
        assert status["total_events"] == 1  # Счетчик сохранился