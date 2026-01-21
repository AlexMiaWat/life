"""
Unit-тесты для модуля ClarityMoments

Проверяем:
- Детекцию условий активации моментов ясности
- Управление состоянием clarity_state и clarity_duration
- Создание событий clarity_moment
- Логирование состояний
- Интеграцию с SelfState
"""

from unittest.mock import Mock

import pytest

from src.experimental.clarity_moments import ClarityMoments
from src.state.self_state import SelfState


@pytest.mark.unit
class TestClarityMoments:
    """Тесты для ClarityMoments"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.logger = Mock()
        self.clarity_moments = ClarityMoments(logger=self.logger)
        self.self_state = SelfState()

    def test_initialization(self):
        """Тест инициализации ClarityMoments"""
        assert self.clarity_moments._clarity_events_count == 0
        assert self.clarity_moments._last_check_tick == -10  # -CLARITY_CHECK_INTERVAL
        assert self.clarity_moments.CLARITY_STABILITY_THRESHOLD == 0.8
        assert self.clarity_moments.CLARITY_ENERGY_THRESHOLD == 0.7
        assert self.clarity_moments.CLARITY_DURATION_TICKS == 50
        assert self.clarity_moments.CLARITY_SIGNIFICANCE_BOOST == 1.5

    def test_check_clarity_conditions_not_met(self):
        """Тест проверки условий - условия не выполнены"""
        # Устанавливаем состояние ниже порогов
        self.self_state.stability = 0.5
        self.self_state.energy = 0.5
        self.self_state.ticks = 10

        result = self.clarity_moments.check_clarity_conditions(self.self_state)
        assert result is None

    def test_check_clarity_conditions_interval_not_reached(self):
        """Тест проверки условий - интервал проверки не достигнут"""
        # Устанавливаем состояние ниже порогов
        self.self_state.stability = 0.5
        self.self_state.energy = 0.5
        self.self_state.ticks = 5  # Меньше CLARITY_CHECK_INTERVAL (10)
        self.clarity_moments._last_check_tick = 0

        result = self.clarity_moments.check_clarity_conditions(self.self_state)
        assert result is None

    def test_check_clarity_conditions_already_active(self):
        """Тест проверки условий - clarity уже активен"""
        self.self_state.clarity_state = True
        self.self_state.stability = 0.9
        self.self_state.energy = 0.8
        self.self_state.ticks = 15

        result = self.clarity_moments.check_clarity_conditions(self.self_state)
        assert result is None

    def test_check_clarity_conditions_met(self):
        """Тест проверки условий - условия выполнены"""
        # Устанавливаем состояние выше порогов
        self.self_state.stability = 0.9
        self.self_state.energy = 0.8
        self.self_state.ticks = 15

        result = self.clarity_moments.check_clarity_conditions(self.self_state)

        assert result is not None
        assert result["type"] == "clarity_moment"
        assert result["data"]["clarity_id"] == 1
        assert result["data"]["trigger_conditions"]["stability"] == 0.9
        assert result["data"]["trigger_conditions"]["energy"] == 0.8
        assert result["data"]["duration_ticks"] == 50
        assert result["data"]["significance_boost"] == 1.5

        # Проверяем логирование
        self.logger.info.assert_called_with(
            "Clarity moment activated",
            {"clarity_id": 1, "stability": 0.9, "energy": 0.8, "tick": 15},
        )

    def test_activate_clarity_moment(self):
        """Тест активации момента ясности"""
        self.clarity_moments.activate_clarity_moment(self.self_state)

        assert self.self_state.clarity_state is True
        assert self.self_state.clarity_duration == 50
        assert self.self_state.clarity_modifier == 1.5

        # Проверяем логирование
        self.logger.info.assert_called_with(
            "Clarity moment state activated",
            {"duration": 50, "significance_boost": 1.5},
        )

    def test_update_clarity_state_not_active(self):
        """Тест обновления состояния - clarity не активен"""
        result = self.clarity_moments.update_clarity_state(self.self_state)
        assert result is False

    def test_update_clarity_state_active(self):
        """Тест обновления состояния - clarity активен"""
        # Активируем clarity
        self.self_state.clarity_state = True
        self.self_state.clarity_duration = 10

        result = self.clarity_moments.update_clarity_state(self.self_state)
        assert result is True
        assert self.self_state.clarity_duration == 9

    def test_update_clarity_state_deactivation(self):
        """Тест обновления состояния - деактивация по истечении времени"""
        # Активируем clarity с длительностью 1
        self.self_state.clarity_state = True
        self.self_state.clarity_duration = 1

        result = self.clarity_moments.update_clarity_state(self.self_state)
        assert result is False
        assert self.self_state.clarity_state is False
        assert self.self_state.clarity_duration == 0
        assert self.self_state.clarity_modifier == 1.0

        # Проверяем логирование
        self.logger.info.assert_called_with(
            "Clarity moment deactivated", {"total_clarity_events": 0}
        )

    def test_deactivate_clarity_moment(self):
        """Тест принудительной деактивации момента ясности"""
        # Активируем clarity
        self.self_state.clarity_state = True
        self.self_state.clarity_duration = 20

        self.clarity_moments.deactivate_clarity_moment(self.self_state)

        assert self.self_state.clarity_state is False
        assert self.self_state.clarity_duration == 0
        assert self.self_state.clarity_modifier == 1.0

        # Проверяем логирование
        self.logger.info.assert_called_with(
            "Clarity moment deactivated", {"total_clarity_events": 0}
        )

    def test_get_clarity_modifier_active(self):
        """Тест получения модификатора - clarity активен"""
        self.self_state.clarity_state = True
        modifier = self.clarity_moments.get_clarity_modifier(self.self_state)
        assert modifier == 1.5

    def test_get_clarity_modifier_not_active(self):
        """Тест получения модификатора - clarity не активен"""
        self.self_state.clarity_state = False
        modifier = self.clarity_moments.get_clarity_modifier(self.self_state)
        assert modifier == 1.0

    def test_is_clarity_active(self):
        """Тест проверки активности clarity"""
        self.self_state.clarity_state = True
        assert self.clarity_moments.is_clarity_active(self.self_state) is True

        self.self_state.clarity_state = False
        assert self.clarity_moments.is_clarity_active(self.self_state) is False

    def test_get_clarity_status(self):
        """Тест получения статуса clarity"""
        # Clarity не активен
        status = self.clarity_moments.get_clarity_status(self.self_state)
        assert status["active"] is False
        assert status["duration_remaining"] == 0
        assert status["total_events"] == 0
        assert status["modifier"] == 1.0

        # Активируем clarity
        self.self_state.clarity_state = True
        self.self_state.clarity_duration = 25

        status = self.clarity_moments.get_clarity_status(self.self_state)
        assert status["active"] is True
        assert status["duration_remaining"] == 25
        assert status["modifier"] == 1.5

    def test_multiple_clarity_events(self):
        """Тест множественных событий clarity"""
        # Первое событие
        self.self_state.stability = 0.9
        self.self_state.energy = 0.8
        self.self_state.ticks = 15

        result1 = self.clarity_moments.check_clarity_conditions(self.self_state)
        assert result1["data"]["clarity_id"] == 1

        # Второе событие (после деактивации первого)
        self.self_state.clarity_state = False
        self.self_state.ticks = 25

        result2 = self.clarity_moments.check_clarity_conditions(self.self_state)
        assert result2["data"]["clarity_id"] == 2

    def test_check_interval_reset(self):
        """Тест сброса интервала проверки"""
        # Первая проверка
        self.self_state.stability = 0.9
        self.self_state.energy = 0.8
        self.self_state.ticks = 15

        result1 = self.clarity_moments.check_clarity_conditions(self.self_state)
        assert result1 is not None
        assert self.clarity_moments._last_check_tick == 15

        # Вторая проверка слишком рано
        self.self_state.ticks = 20  # 20 - 15 = 5 < 10
        result2 = self.clarity_moments.check_clarity_conditions(self.self_state)
        assert result2 is None

        # Третья проверка после интервала
        self.self_state.ticks = 30  # 30 - 15 = 15 >= 10
        result3 = self.clarity_moments.check_clarity_conditions(self.self_state)
        assert result3 is not None
