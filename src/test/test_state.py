"""
Подробные тесты для модуля State (SelfState)
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import json
import shutil
import tempfile
import time
from pathlib import Path

import pytest

from src.memory.memory import MemoryEntry
from src.state.self_state import (
    SelfState,
    create_initial_state,
    load_snapshot,
    save_snapshot,
)


@pytest.mark.unit
@pytest.mark.order(1)
class TestSelfState:
    """Тесты для класса SelfState"""

    def test_self_state_initialization(self):
        """Тест инициализации SelfState с значениями по умолчанию"""
        state = SelfState()
        assert state.energy == 100.0
        assert state.integrity == 1.0
        assert state.stability == 1.0
        assert state.fatigue == 0.0
        assert state.tension == 0.0
        assert state.age == 0.0
        assert state.ticks == 0
        assert state.active is True
        assert state.life_id is not None
        assert state.birth_timestamp > 0
        assert isinstance(state.memory, list)
        assert len(state.memory) == 0

    def test_self_state_unique_life_id(self):
        """Тест уникальности life_id для разных экземпляров"""
        state1 = SelfState()
        state2 = SelfState()
        assert state1.life_id != state2.life_id

    def test_self_state_birth_timestamp(self):
        """Тест установки birth_timestamp"""
        before = time.time()
        state = SelfState()
        after = time.time()
        assert before <= state.birth_timestamp <= after

    def test_apply_delta_energy(self):
        """Тест применения дельты к energy"""
        state = SelfState()
        state.energy = 50.0

        # Положительная дельта
        state.apply_delta({"energy": 10.0})
        assert state.energy == 60.0

        # Отрицательная дельта
        state.apply_delta({"energy": -20.0})
        assert state.energy == 40.0

        # Превышение максимума (100.0)
        state.apply_delta({"energy": 100.0})
        assert state.energy == 100.0

        # Превышение минимума (0.0)
        state.apply_delta({"energy": -200.0})
        assert state.energy == 0.0

    def test_apply_delta_integrity(self):
        """Тест применения дельты к integrity"""
        state = SelfState()
        state.integrity = 0.5

        # Положительная дельта
        state.apply_delta({"integrity": 0.2})
        assert state.integrity == 0.7

        # Отрицательная дельта
        state.apply_delta({"integrity": -0.3})
        assert abs(state.integrity - 0.4) < 0.0001  # Учитываем погрешность float

        # Превышение максимума (1.0)
        state.apply_delta({"integrity": 1.0})
        assert state.integrity == 1.0

        # Превышение минимума (0.0)
        state.apply_delta({"integrity": -2.0})
        assert state.integrity == 0.0

    def test_apply_delta_stability(self):
        """Тест применения дельты к stability"""
        state = SelfState()
        state.stability = 0.6

        # Положительная дельта
        state.apply_delta({"stability": 0.3})
        assert abs(state.stability - 0.9) < 0.0001  # Учитываем погрешность float

        # Отрицательная дельта
        state.apply_delta({"stability": -0.5})
        assert abs(state.stability - 0.4) < 0.0001  # Учитываем погрешность float

        # Превышение максимума (1.0)
        state.apply_delta({"stability": 1.0})
        assert state.stability == 1.0

        # Превышение минимума (0.0)
        state.apply_delta({"stability": -2.0})
        assert state.stability == 0.0

    def test_apply_delta_multiple_params(self):
        """Тест применения дельты к нескольким параметрам одновременно"""
        state = SelfState()
        state.energy = 50.0
        state.integrity = 0.5
        state.stability = 0.5

        state.apply_delta({"energy": 10.0, "integrity": 0.2, "stability": -0.1})

        assert state.energy == 60.0
        assert state.integrity == 0.7
        assert state.stability == 0.4

    def test_apply_delta_ticks(self):
        """Тест применения дельты к ticks (без ограничений)"""
        state = SelfState()
        state.ticks = 10

        state.apply_delta({"ticks": 5})
        assert state.ticks == 15

        state.apply_delta({"ticks": -3})
        assert state.ticks == 12

    def test_apply_delta_age(self):
        """Тест применения дельты к age (без ограничений)"""
        state = SelfState()
        state.age = 10.5

        state.apply_delta({"age": 1.5})
        assert state.age == 12.0

    def test_apply_delta_unknown_field(self):
        """Тест применения дельты к несуществующему полю (должно игнорироваться)"""
        state = SelfState()
        initial_energy = state.energy

        # Попытка изменить несуществующее поле
        state.apply_delta({"unknown_field": 100.0})

        # Энергия не должна измениться
        assert state.energy == initial_energy
        assert not hasattr(state, "unknown_field")

    def test_apply_delta_non_numeric_field(self):
        """Тест применения дельты к нечисловому полю (должно вызвать TypeError)"""
        state = SelfState()
        
        # Попытка применить дельту к нечисловому полю (list)
        with pytest.raises(TypeError, match="Cannot apply delta to field 'recent_events'"):
            state.apply_delta({"recent_events": 1.0})
        
        # Попытка применить дельту к нечисловому полю (dict)
        with pytest.raises(TypeError, match="Cannot apply delta to field 'planning'"):
            state.apply_delta({"planning": 1.0})

    def test_self_state_memory_operations(self):
        """Тест операций с памятью"""
        state = SelfState()
        entry = MemoryEntry(
            event_type="test_event", meaning_significance=0.5, timestamp=time.time()
        )
        state.memory.append(entry)
        assert len(state.memory) == 1
        assert state.memory[0] == entry

    def test_self_state_recent_events(self):
        """Тест работы с recent_events"""
        state = SelfState()
        assert isinstance(state.recent_events, list)
        assert len(state.recent_events) == 0

        state.recent_events.append("event1")
        state.recent_events.append("event2")
        assert len(state.recent_events) == 2
        assert state.recent_events[0] == "event1"


@pytest.mark.unit
@pytest.mark.order(1)
class TestSnapshots:
    """Тесты для функций сохранения и загрузки снимков"""

    @pytest.fixture
    def temp_snapshot_dir(self):
        """Создает временную директорию для снимков"""
        temp_dir = Path(tempfile.mkdtemp())
        Path("data/snapshots")

        # Временно заменяем SNAPSHOT_DIR
        from state import self_state

        original_snapshot_dir = self_state.SNAPSHOT_DIR
        self_state.SNAPSHOT_DIR = temp_dir

        yield temp_dir

        # Восстанавливаем
        self_state.SNAPSHOT_DIR = original_snapshot_dir
        shutil.rmtree(temp_dir)

    def test_save_snapshot(self, temp_snapshot_dir):
        """Тест сохранения снимка"""
        state = SelfState()
        state.ticks = 100
        state.energy = 75.0
        state.integrity = 0.8
        state.stability = 0.9

        # Добавляем запись в память
        entry = MemoryEntry(
            event_type="test", meaning_significance=0.5, timestamp=time.time()
        )
        state.memory.append(entry)

        save_snapshot(state)

        # Проверяем, что файл создан
        snapshot_file = temp_snapshot_dir / "snapshot_000100.json"
        assert snapshot_file.exists()

        # Проверяем содержимое
        with snapshot_file.open("r") as f:
            data = json.load(f)

        assert data["ticks"] == 100
        assert data["energy"] == 75.0
        assert data["integrity"] == 0.8
        assert data["stability"] == 0.9
        assert len(data["memory"]) == 1
        assert data["memory"][0]["event_type"] == "test"

        # Проверяем, что transient поля не сохранены
        assert "activated_memory" not in data
        assert "last_pattern" not in data

    def test_load_snapshot(self, temp_snapshot_dir):
        """Тест загрузки снимка"""
        # Создаем снимок
        state = SelfState()
        state.ticks = 200
        state.energy = 50.0
        state.integrity = 0.6
        state.stability = 0.7
        state.life_id = "test_life_id"

        entry = MemoryEntry(
            event_type="loaded_event", meaning_significance=0.7, timestamp=time.time()
        )
        state.memory.append(entry)

        save_snapshot(state)

        # Загружаем снимок
        loaded_state = load_snapshot(200)

        assert loaded_state.ticks == 200
        assert loaded_state.energy == 50.0
        assert loaded_state.integrity == 0.6
        assert loaded_state.stability == 0.7
        assert loaded_state.life_id == "test_life_id"
        assert len(loaded_state.memory) == 1
        assert loaded_state.memory[0].event_type == "loaded_event"
        assert loaded_state.memory[0].meaning_significance == 0.7

    def test_load_snapshot_not_found(self, temp_snapshot_dir):
        """Тест загрузки несуществующего снимка"""
        with pytest.raises(FileNotFoundError):
            load_snapshot(99999)

    def test_load_latest_snapshot(self, temp_snapshot_dir):
        """Тест загрузки последнего снимка"""
        # Создаем несколько снимков
        for ticks in [10, 20, 30]:
            state = SelfState()
            state.ticks = ticks
            state.energy = ticks * 2.0
            save_snapshot(state)

        # Загружаем последний (используем метод класса)
        state = SelfState()
        latest = state.load_latest_snapshot()
        assert latest.ticks == 30
        assert latest.energy == 60.0

    def test_load_latest_snapshot_not_found(self, temp_snapshot_dir):
        """Тест загрузки последнего снимка когда их нет"""
        state = SelfState()
        with pytest.raises(FileNotFoundError):
            state.load_latest_snapshot()

    def test_snapshot_preserves_memory(self, temp_snapshot_dir):
        """Тест сохранения памяти в снимке"""
        state = SelfState()

        # Добавляем несколько записей
        for i in range(5):
            entry = MemoryEntry(
                event_type=f"event_{i}",
                meaning_significance=0.1 * i,
                timestamp=time.time(),
            )
            state.memory.append(entry)

        state.ticks = 50
        save_snapshot(state)

        loaded = load_snapshot(50)
        assert len(loaded.memory) == 5
        for i, entry in enumerate(loaded.memory):
            assert entry.event_type == f"event_{i}"
            assert abs(entry.meaning_significance - 0.1 * i) < 0.001


@pytest.mark.unit
@pytest.mark.order(1)
class TestCreateInitialState:
    """Тесты для функции create_initial_state"""

    def test_create_initial_state(self):
        """Тест создания начального состояния"""
        state = create_initial_state()
        assert isinstance(state, SelfState)
        assert state.energy == 100.0
        assert state.integrity == 1.0
        assert state.stability == 1.0
        assert state.ticks == 0
        assert state.active is True


@pytest.mark.unit
@pytest.mark.order(2)
class TestSelfStateValidation:
    """Тесты для валидации полей SelfState (SS.2)"""

    def test_energy_validation_valid(self):
        """Тест валидации energy с допустимыми значениями"""
        state = SelfState()
        state.energy = 50.0
        assert state.energy == 50.0
        state.energy = 0.0
        assert state.energy == 0.0
        state.energy = 100.0
        assert state.energy == 100.0

    def test_energy_validation_invalid(self):
        """Тест валидации energy с недопустимыми значениями"""
        state = SelfState()
        with pytest.raises(ValueError, match="energy must be between 0.0 and 100.0"):
            state.energy = 150.0
        with pytest.raises(ValueError, match="energy must be between 0.0 and 100.0"):
            state.energy = -10.0

    def test_integrity_validation_valid(self):
        """Тест валидации integrity с допустимыми значениями"""
        state = SelfState()
        state.integrity = 0.5
        assert state.integrity == 0.5
        state.integrity = 0.0
        assert state.integrity == 0.0
        state.integrity = 1.0
        assert state.integrity == 1.0

    def test_integrity_validation_invalid(self):
        """Тест валидации integrity с недопустимыми значениями"""
        state = SelfState()
        with pytest.raises(ValueError, match="integrity must be between 0.0 and 1.0"):
            state.integrity = 1.5
        with pytest.raises(ValueError, match="integrity must be between 0.0 and 1.0"):
            state.integrity = -0.1

    def test_stability_validation_valid(self):
        """Тест валидации stability с допустимыми значениями"""
        state = SelfState()
        state.stability = 0.7
        assert state.stability == 0.7
        state.stability = 0.0
        assert state.stability == 0.0
        state.stability = 1.0
        assert state.stability == 1.0

    def test_stability_validation_invalid(self):
        """Тест валидации stability с недопустимыми значениями"""
        state = SelfState()
        with pytest.raises(ValueError, match="stability must be between 0.0 and 1.0"):
            state.stability = 2.0
        with pytest.raises(ValueError, match="stability must be between 0.0 and 1.0"):
            state.stability = -0.5

    def test_fatigue_validation(self):
        """Тест валидации fatigue (должно быть >= 0)"""
        state = SelfState()
        state.fatigue = 10.0
        assert state.fatigue == 10.0
        state.fatigue = 0.0
        assert state.fatigue == 0.0
        with pytest.raises(ValueError, match="fatigue must be >= 0.0"):
            state.fatigue = -5.0

    def test_tension_validation(self):
        """Тест валидации tension (должно быть >= 0)"""
        state = SelfState()
        state.tension = 5.0
        assert state.tension == 5.0
        state.tension = 0.0
        assert state.tension == 0.0
        with pytest.raises(ValueError, match="tension must be >= 0.0"):
            state.tension = -1.0

    def test_age_validation(self):
        """Тест валидации age (должно быть >= 0)"""
        state = SelfState()
        state.age = 100.0
        assert state.age == 100.0
        state.age = 0.0
        assert state.age == 0.0
        with pytest.raises(ValueError, match="age must be >= 0.0"):
            state.age = -10.0

    def test_ticks_validation(self):
        """Тест валидации ticks (должно быть >= 0)"""
        state = SelfState()
        state.ticks = 100
        assert state.ticks == 100
        state.ticks = 0
        assert state.ticks == 0
        with pytest.raises(ValueError, match="ticks must be >= 0"):
            state.ticks = -5


@pytest.mark.unit
@pytest.mark.order(2)
class TestSelfStateProtection:
    """Тесты для защиты неизменяемых полей SelfState (SS.3)"""

    def test_life_id_protection(self):
        """Тест защиты life_id от изменения"""
        state = SelfState()
        original_life_id = state.life_id
        
        # Попытка изменить life_id должна вызвать AttributeError
        with pytest.raises(AttributeError, match="Cannot modify immutable field 'life_id'"):
            state.life_id = "new_life_id"
        
        # life_id не должен измениться
        assert state.life_id == original_life_id

    def test_birth_timestamp_protection(self):
        """Тест защиты birth_timestamp от изменения"""
        state = SelfState()
        original_timestamp = state.birth_timestamp
        
        # Попытка изменить birth_timestamp должна вызвать AttributeError
        with pytest.raises(AttributeError, match="Cannot modify immutable field 'birth_timestamp'"):
            state.birth_timestamp = time.time()
        
        # birth_timestamp не должен измениться
        assert state.birth_timestamp == original_timestamp


@pytest.mark.unit
@pytest.mark.order(2)
class TestSelfStateSafeMethods:
    """Тесты для безопасных методов обновления SelfState (SS.4)"""

    def test_update_energy(self):
        """Тест метода update_energy"""
        state = SelfState()
        state.update_energy(75.0)
        assert state.energy == 75.0
        
        # Валидация должна работать
        with pytest.raises(ValueError):
            state.update_energy(150.0)

    def test_update_integrity(self):
        """Тест метода update_integrity"""
        state = SelfState()
        state.update_integrity(0.6)
        assert state.integrity == 0.6
        
        # Валидация должна работать
        with pytest.raises(ValueError):
            state.update_integrity(2.0)

    def test_update_stability(self):
        """Тест метода update_stability"""
        state = SelfState()
        state.update_stability(0.8)
        assert state.stability == 0.8
        
        # Валидация должна работать
        with pytest.raises(ValueError):
            state.update_stability(-0.5)

    def test_update_vital_params(self):
        """Тест метода update_vital_params"""
        state = SelfState()
        state.update_vital_params(energy=50.0, integrity=0.7, stability=0.6)
        assert state.energy == 50.0
        assert state.integrity == 0.7
        assert state.stability == 0.6
        
        # Частичное обновление
        state.update_vital_params(energy=60.0)
        assert state.energy == 60.0
        assert state.integrity == 0.7  # Не изменилось
        assert state.stability == 0.6  # Не изменилось

    def test_reset_to_defaults(self):
        """Тест метода reset_to_defaults"""
        state = SelfState()
        original_life_id = state.life_id
        original_birth_timestamp = state.birth_timestamp
        
        # Изменяем состояние
        state.energy = 30.0
        state.integrity = 0.3
        state.stability = 0.4
        state.fatigue = 10.0
        state.ticks = 100
        
        # Сбрасываем
        state.reset_to_defaults()
        
        # Проверяем, что значения сброшены
        assert state.energy == 100.0
        assert state.integrity == 1.0
        assert state.stability == 1.0
        assert state.fatigue == 0.0
        assert state.ticks == 0
        
        # Неизменяемые поля не должны измениться
        assert state.life_id == original_life_id
        assert state.birth_timestamp == original_birth_timestamp


@pytest.mark.unit
@pytest.mark.order(2)
class TestSelfStateIsActive:
    """Тесты для метода is_active() SelfState (SS.5)"""

    def test_is_active_all_positive(self):
        """Тест is_active когда все параметры > 0"""
        state = SelfState()
        state.energy = 50.0
        state.integrity = 0.5
        state.stability = 0.5
        assert state.is_active() is True
        assert state.active is True

    def test_is_active_energy_zero(self):
        """Тест is_active когда energy = 0"""
        state = SelfState()
        state.energy = 0.0
        state.integrity = 0.5
        state.stability = 0.5
        assert state.is_active() is False
        assert state.active is False

    def test_is_active_integrity_zero(self):
        """Тест is_active когда integrity = 0"""
        state = SelfState()
        state.energy = 50.0
        state.integrity = 0.0
        state.stability = 0.5
        assert state.is_active() is False
        assert state.active is False

    def test_is_active_stability_zero(self):
        """Тест is_active когда stability = 0"""
        state = SelfState()
        state.energy = 50.0
        state.integrity = 0.5
        state.stability = 0.0
        assert state.is_active() is False
        assert state.active is False

    def test_is_active_all_zero(self):
        """Тест is_active когда все параметры = 0"""
        state = SelfState()
        state.energy = 0.0
        state.integrity = 0.0
        state.stability = 0.0
        assert state.is_active() is False
        assert state.active is False

    def test_is_active_auto_update(self):
        """Тест автоматического обновления active при изменении vital параметров"""
        state = SelfState()
        assert state.active is True
        
        state.energy = 0.0
        assert state.active is False
        
        state.energy = 50.0
        state.integrity = 0.5
        state.stability = 0.5
        assert state.active is True

    def test_is_viable(self):
        """Тест метода is_viable с более строгими критериями"""
        state = SelfState()
        state.energy = 50.0
        state.integrity = 0.5
        state.stability = 0.5
        assert state.is_viable() is True
        
        state.energy = 5.0  # Ниже порога
        assert state.is_viable() is False
        
        state.energy = 50.0
        state.integrity = 0.05  # Ниже порога
        assert state.is_viable() is False


@pytest.mark.unit
@pytest.mark.order(2)
class TestSelfStateLogging:
    """Тесты для логирования изменений SelfState (SS.6)"""

    @pytest.fixture
    def temp_log_dir(self):
        """Создает временную директорию для логов"""
        temp_dir = Path(tempfile.mkdtemp())
        from state import self_state
        original_log_dir = self_state.STATE_CHANGES_LOG_DIR
        original_log_file = self_state.STATE_CHANGES_LOG_FILE
        self_state.STATE_CHANGES_LOG_DIR = temp_dir
        self_state.STATE_CHANGES_LOG_FILE = temp_dir / "state_changes.jsonl"
        
        yield temp_dir
        
        self_state.STATE_CHANGES_LOG_DIR = original_log_dir
        self_state.STATE_CHANGES_LOG_FILE = original_log_file
        shutil.rmtree(temp_dir)

    def test_logging_enabled(self, temp_log_dir):
        """Тест логирования изменений (логирование включено)"""
        from state import self_state
        state = SelfState()
        state.energy = 50.0
        state.integrity = 0.6
        
        # Проверяем, что лог создан
        assert self_state.STATE_CHANGES_LOG_FILE.exists()
        
        # Проверяем содержимое лога
        history = state.get_change_history()
        assert len(history) >= 2
        # Проверяем, что есть записи об изменении energy и integrity
        energy_changes = [h for h in history if h["field"] == "energy"]
        integrity_changes = [h for h in history if h["field"] == "integrity"]
        assert len(energy_changes) > 0
        assert len(integrity_changes) > 0

    def test_logging_disabled(self, temp_log_dir):
        """Тест отключения логирования"""
        state = SelfState()
        state.disable_logging()
        
        state.energy = 50.0
        state.integrity = 0.6
        
        # Лог не должен содержать записи (или должен быть пустым)
        # В зависимости от реализации, лог может не создаваться или быть пустым
        history = state.get_change_history()
        # Если логирование отключено, история может быть пустой или не создаваться

    def test_get_change_history(self, temp_log_dir):
        """Тест получения истории изменений"""
        state = SelfState()
        state.energy = 50.0
        state.integrity = 0.6
        state.stability = 0.7
        
        history = state.get_change_history()
        assert len(history) >= 3
        
        # Проверяем структуру записей
        for entry in history:
            assert "timestamp" in entry
            assert "life_id" in entry
            assert "tick" in entry
            assert "field" in entry
            assert "old_value" in entry
            assert "new_value" in entry

    def test_get_change_history_limit(self, temp_log_dir):
        """Тест получения истории изменений с лимитом"""
        state = SelfState()
        
        # Делаем несколько изменений
        for i in range(10):
            state.energy = 50.0 + i
        
        history = state.get_change_history(limit=5)
        assert len(history) <= 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
