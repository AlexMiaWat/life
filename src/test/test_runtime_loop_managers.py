"""
Unit-тесты для менеджеров runtime loop: SnapshotManager, LogManager, LifePolicy.

Проверяем:
- Делегирование ответственности менеджерам
- Отсутствие регрессий поведения
- Корректность политик и расчетов
"""
import sys
from pathlib import Path
from unittest.mock import Mock, call

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest

from src.runtime.snapshot_manager import SnapshotManager
from src.runtime.log_manager import LogManager, FlushPolicy
from src.runtime.life_policy import LifePolicy
from src.state.self_state import SelfState


@pytest.mark.unit
class TestSnapshotManager:
    """Тесты для SnapshotManager"""

    def test_should_snapshot_period(self):
        """Тест: снапшот делается строго по периоду"""
        manager = SnapshotManager(period_ticks=10, saver=Mock())
        
        # На тике 0 не должно быть снапшота
        assert manager.should_snapshot(0) is False
        
        # На тике 10 должен быть снапшот
        assert manager.should_snapshot(10) is True
        
        # На тике 20 должен быть снапшот
        assert manager.should_snapshot(20) is True
        
        # На тике 15 не должно быть снапшота
        assert manager.should_snapshot(15) is False

    def test_maybe_snapshot_calls_saver(self):
        """Тест: maybe_snapshot вызывает saver при нужном тике"""
        saver = Mock()
        manager = SnapshotManager(period_ticks=10, saver=saver)
        self_state = SelfState()
        self_state.ticks = 10
        
        result = manager.maybe_snapshot(self_state)
        
        assert result is True
        saver.assert_called_once_with(self_state)

    def test_maybe_snapshot_skips_when_not_needed(self):
        """Тест: maybe_snapshot не вызывает saver когда не нужно"""
        saver = Mock()
        manager = SnapshotManager(period_ticks=10, saver=saver)
        self_state = SelfState()
        self_state.ticks = 5
        
        result = manager.maybe_snapshot(self_state)
        
        assert result is False
        saver.assert_not_called()

    def test_maybe_snapshot_handles_errors(self):
        """Тест: ошибки снапшота не роняют менеджер"""
        saver = Mock(side_effect=Exception("Snapshot error"))
        manager = SnapshotManager(period_ticks=10, saver=saver)
        self_state = SelfState()
        self_state.ticks = 10
        
        result = manager.maybe_snapshot(self_state)
        
        # Менеджер должен вернуть False при ошибке, но не упасть
        assert result is False
        saver.assert_called_once()

    def test_snapshot_manager_validation(self):
        """Тест: валидация параметров SnapshotManager"""
        saver = Mock()
        
        # Проверка на None для saver
        with pytest.raises(ValueError, match="saver cannot be None"):
            SnapshotManager(period_ticks=10, saver=None)
        
        # Проверка на неположительный period_ticks
        with pytest.raises(ValueError, match="period_ticks must be positive"):
            SnapshotManager(period_ticks=0, saver=saver)
        
        with pytest.raises(ValueError, match="period_ticks must be positive"):
            SnapshotManager(period_ticks=-1, saver=saver)


@pytest.mark.unit
class TestLogManager:
    """Тесты для LogManager"""

    def test_flush_on_shutdown(self):
        """Тест: flush вызывается при shutdown"""
        flush_fn = Mock()
        policy = FlushPolicy(flush_on_shutdown=True)
        manager = LogManager(flush_policy=policy, flush_fn=flush_fn)
        self_state = SelfState()
        self_state.ticks = 5
        
        manager.maybe_flush(self_state, phase="shutdown")
        
        flush_fn.assert_called_once()
        assert manager.last_flush_tick == 5

    def test_flush_on_exception(self):
        """Тест: flush вызывается при exception (если политика требует)"""
        flush_fn = Mock()
        policy = FlushPolicy(flush_on_exception=True)
        manager = LogManager(flush_policy=policy, flush_fn=flush_fn)
        self_state = SelfState()
        self_state.ticks = 3
        
        manager.maybe_flush(self_state, phase="exception")
        
        flush_fn.assert_called_once()

    def test_flush_not_on_exception_if_disabled(self):
        """Тест: flush не вызывается при exception если политика отключена"""
        flush_fn = Mock()
        policy = FlushPolicy(flush_on_exception=False)
        manager = LogManager(flush_policy=policy, flush_fn=flush_fn)
        self_state = SelfState()
        
        manager.maybe_flush(self_state, phase="exception")
        
        flush_fn.assert_not_called()

    def test_flush_periodic(self):
        """Тест: flush вызывается раз в N тиков"""
        flush_fn = Mock()
        policy = FlushPolicy(flush_period_ticks=5)
        manager = LogManager(flush_policy=policy, flush_fn=flush_fn)
        self_state = SelfState()
        
        # Первый flush на тике 5 (last_flush_tick инициализирован как -5)
        self_state.ticks = 5
        manager.maybe_flush(self_state, phase="tick")
        assert flush_fn.call_count == 1
        assert manager.last_flush_tick == 5
        
        # Не должен flush на тике 7 (прошло только 2 тика)
        self_state.ticks = 7
        manager.maybe_flush(self_state, phase="tick")
        assert flush_fn.call_count == 1  # Не изменилось
        
        # Должен flush на тике 10 (прошло 5 тиков с последнего flush)
        self_state.ticks = 10
        manager.maybe_flush(self_state, phase="tick")
        assert flush_fn.call_count == 2
        assert manager.last_flush_tick == 10

    def test_flush_before_snapshot(self):
        """Тест: flush вызывается перед снапшотом (если политика требует)"""
        flush_fn = Mock()
        policy = FlushPolicy(flush_before_snapshot=True)
        manager = LogManager(flush_policy=policy, flush_fn=flush_fn)
        self_state = SelfState()
        
        manager.maybe_flush(self_state, phase="before_snapshot")
        
        flush_fn.assert_called_once()

    def test_flush_handles_errors(self):
        """Тест: ошибки flush не роняют менеджер"""
        flush_fn = Mock(side_effect=Exception("Flush error"))
        policy = FlushPolicy(flush_on_shutdown=True)
        manager = LogManager(flush_policy=policy, flush_fn=flush_fn)
        self_state = SelfState()
        
        # Не должно упасть
        manager.maybe_flush(self_state, phase="shutdown")
        
        flush_fn.assert_called_once()

    def test_flush_after_snapshot(self):
        """Тест: flush вызывается после снапшота (если политика требует)"""
        flush_fn = Mock()
        policy = FlushPolicy(flush_after_snapshot=True)
        manager = LogManager(flush_policy=policy, flush_fn=flush_fn)
        self_state = SelfState()
        
        manager.maybe_flush(self_state, phase="after_snapshot")
        
        flush_fn.assert_called_once()

    def test_flush_not_after_snapshot_if_disabled(self):
        """Тест: flush не вызывается после снапшота если политика отключена"""
        flush_fn = Mock()
        policy = FlushPolicy(flush_after_snapshot=False)
        manager = LogManager(flush_policy=policy, flush_fn=flush_fn)
        self_state = SelfState()
        
        manager.maybe_flush(self_state, phase="after_snapshot")
        
        flush_fn.assert_not_called()

    def test_flush_after_snapshot_in_tick_phase(self):
        """Тест: flush после снапшота в фазе tick с snapshot_was_made=True"""
        flush_fn = Mock()
        policy = FlushPolicy(flush_after_snapshot=True, flush_period_ticks=10)
        manager = LogManager(flush_policy=policy, flush_fn=flush_fn)
        self_state = SelfState()
        self_state.ticks = 3
        
        # Flush после снапшота должен произойти даже если не прошло достаточно тиков
        manager.maybe_flush(self_state, phase="tick", snapshot_was_made=True)
        
        flush_fn.assert_called_once()

    def test_log_manager_validation(self):
        """Тест: валидация параметров LogManager"""
        policy = FlushPolicy(flush_period_ticks=10)
        
        # Проверка на None для flush_fn
        with pytest.raises(ValueError, match="flush_fn cannot be None"):
            LogManager(flush_policy=policy, flush_fn=None)
        
        # Проверка на неположительный flush_period_ticks
        invalid_policy = FlushPolicy(flush_period_ticks=0)
        with pytest.raises(ValueError, match="flush_period_ticks must be positive"):
            LogManager(flush_policy=invalid_policy, flush_fn=Mock())
        
        invalid_policy = FlushPolicy(flush_period_ticks=-1)
        with pytest.raises(ValueError, match="flush_period_ticks must be positive"):
            LogManager(flush_policy=invalid_policy, flush_fn=Mock())


@pytest.mark.unit
class TestLifePolicy:
    """Тесты для LifePolicy"""

    def test_is_weak_at_threshold(self):
        """Тест: is_weak на границе порога"""
        policy = LifePolicy(weakness_threshold=0.05)
        self_state = SelfState()
        
        # На границе порога - должна быть слабость
        self_state.energy = 0.05
        self_state.integrity = 1.0
        self_state.stability = 1.0
        assert policy.is_weak(self_state) is True
        
        # Чуть выше порога - не должна быть слабость
        self_state.energy = 0.0501
        assert policy.is_weak(self_state) is False
        
        # Чуть ниже порога - должна быть слабость
        self_state.energy = 0.0499
        assert policy.is_weak(self_state) is True

    def test_is_weak_any_parameter(self):
        """Тест: слабость определяется по любому параметру"""
        policy = LifePolicy(weakness_threshold=0.05)
        self_state = SelfState()
        
        # Слабость по energy
        self_state.energy = 0.04
        self_state.integrity = 1.0
        self_state.stability = 1.0
        assert policy.is_weak(self_state) is True
        
        # Слабость по integrity
        self_state.energy = 1.0
        self_state.integrity = 0.04
        self_state.stability = 1.0
        assert policy.is_weak(self_state) is True
        
        # Слабость по stability
        self_state.energy = 1.0
        self_state.integrity = 1.0
        self_state.stability = 0.04
        assert policy.is_weak(self_state) is True

    def test_weakness_penalty_calculation(self):
        """Тест: корректные дельты penalties как функция от dt"""
        policy = LifePolicy(
            penalty_k=0.02,
            stability_multiplier=2.0,
            integrity_multiplier=2.0,
        )
        
        dt = 1.0
        penalty_deltas = policy.weakness_penalty(dt)
        
        expected_penalty = 0.02 * dt  # 0.02
        assert penalty_deltas["energy"] == -expected_penalty
        assert penalty_deltas["stability"] == -expected_penalty * 2.0
        assert penalty_deltas["integrity"] == -expected_penalty * 2.0

    def test_weakness_penalty_monotonicity(self):
        """Тест: монотонность - при большем dt штраф не меньше по модулю"""
        policy = LifePolicy(penalty_k=0.02)
        
        dt1 = 0.5
        dt2 = 1.0
        
        penalty1 = policy.weakness_penalty(dt1)
        penalty2 = policy.weakness_penalty(dt2)
        
        # По модулю penalty2 должен быть больше или равен penalty1
        assert abs(penalty2["energy"]) >= abs(penalty1["energy"])
        assert abs(penalty2["stability"]) >= abs(penalty1["stability"])
        assert abs(penalty2["integrity"]) >= abs(penalty1["integrity"])

    def test_weakness_penalty_multipliers(self):
        """Тест: множители для stability/integrity применяются корректно"""
        policy = LifePolicy(
            penalty_k=0.02,
            stability_multiplier=2.0,
            integrity_multiplier=3.0,
        )
        
        dt = 1.0
        penalty_deltas = policy.weakness_penalty(dt)
        
        base_penalty = 0.02 * dt
        
        assert penalty_deltas["energy"] == -base_penalty
        assert penalty_deltas["stability"] == -base_penalty * 2.0
        assert penalty_deltas["integrity"] == -base_penalty * 3.0

    def test_default_values_match_old_constants(self):
        """Тест: значения по умолчанию совпадают с предыдущими константами"""
        policy = LifePolicy()
        
        # Проверяем значения по умолчанию
        assert policy.weakness_threshold == 0.05
        assert policy.penalty_k == 0.02
        assert policy.stability_multiplier == 2.0
        assert policy.integrity_multiplier == 2.0

    def test_life_policy_validation(self):
        """Тест: валидация параметров LifePolicy"""
        # Проверка на отрицательные значения
        with pytest.raises(ValueError, match="weakness_threshold must be non-negative"):
            LifePolicy(weakness_threshold=-0.1)
        
        with pytest.raises(ValueError, match="penalty_k must be non-negative"):
            LifePolicy(penalty_k=-0.1)
        
        with pytest.raises(ValueError, match="stability_multiplier must be non-negative"):
            LifePolicy(stability_multiplier=-1.0)
        
        with pytest.raises(ValueError, match="integrity_multiplier must be non-negative"):
            LifePolicy(integrity_multiplier=-1.0)
        
        # Нулевые значения должны быть допустимы
        policy = LifePolicy(
            weakness_threshold=0.0,
            penalty_k=0.0,
            stability_multiplier=0.0,
            integrity_multiplier=0.0,
        )
        assert policy.weakness_threshold == 0.0
        assert policy.penalty_k == 0.0


@pytest.mark.unit
class TestRuntimeLoopDelegation:
    """Интеграционные unit-тесты: проверка делегирования в run_loop"""

    def test_snapshot_manager_integration(self):
        """Тест: SnapshotManager вызывается в нужных местах"""
        # Этот тест проверяет концепцию делегирования
        # В реальном run_loop менеджер должен вызываться вместо inline логики
        saver = Mock()
        manager = SnapshotManager(period_ticks=10, saver=saver)
        self_state = SelfState()
        
        # Симулируем несколько тиков
        for tick in [5, 10, 15, 20]:
            self_state.ticks = tick
            manager.maybe_snapshot(self_state)
        
        # Должно быть 2 вызова: на тике 10 и 20
        assert saver.call_count == 2
        saver.assert_has_calls([call(self_state), call(self_state)])

    def test_log_manager_integration(self):
        """Тест: LogManager не вызывает flush на каждом тике"""
        flush_fn = Mock()
        policy = FlushPolicy(flush_period_ticks=5)
        manager = LogManager(flush_policy=policy, flush_fn=flush_fn)
        self_state = SelfState()
        
        # Симулируем несколько тиков
        # last_flush_tick инициализирован как -5, поэтому:
        # Тик 1: 1 - (-5) = 6 >= 5 -> flush (первый flush)
        # Тик 2: 2 - 1 = 1 < 5 -> нет flush
        # Тик 3: 3 - 1 = 2 < 5 -> нет flush
        # Тик 4: 4 - 1 = 3 < 5 -> нет flush
        # Тик 5: 5 - 1 = 4 < 5 -> нет flush
        # Тик 6: 6 - 1 = 5 >= 5 -> flush (второй flush)
        # Тик 7: 7 - 6 = 1 < 5 -> нет flush
        for tick in range(1, 8):
            self_state.ticks = tick
            manager.maybe_flush(self_state, phase="tick")
        
        # Должно быть 2 flush (на тике 1 и 6), а не 7 (не на каждом тике)
        assert flush_fn.call_count == 2

    def test_life_policy_integration(self):
        """Тест: LifePolicy применяет штрафы корректно"""
        policy = LifePolicy()
        self_state = SelfState()
        
        # Устанавливаем слабость
        self_state.energy = 0.04
        self_state.integrity = 1.0
        self_state.stability = 1.0
        
        # Проверяем слабость
        assert policy.is_weak(self_state) is True
        
        # Применяем штрафы
        dt = 1.0
        penalty_deltas = policy.weakness_penalty(dt)
        
        # Сохраняем исходные значения
        initial_energy = self_state.energy
        initial_stability = self_state.stability
        initial_integrity = self_state.integrity
        
        # Применяем дельты
        self_state.apply_delta(penalty_deltas)
        
        # Проверяем, что значения уменьшились
        assert self_state.energy < initial_energy
        assert self_state.stability < initial_stability
        assert self_state.integrity < initial_integrity
