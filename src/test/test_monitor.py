"""
Тесты для модуля Monitor
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import json
import time
from pathlib import Path

import pytest

from src.memory.memory import MemoryEntry
from src.monitor.console import log, monitor
from src.state.self_state import SelfState


@pytest.mark.unit
@pytest.mark.order(1)
class TestMonitor:
    """Тесты для функций monitor и log"""

    @pytest.fixture
    def temp_log_file(self, tmp_path):
        """Создает временный файл для логов"""
        log_file = tmp_path / "tick_log.jsonl"
        return log_file

    def test_log_function(self, capsys):
        """Тест функции log (строки 13-14)"""
        log("Test message")
        captured = capsys.readouterr()
        assert "[RELOAD] Test message" in captured.out
        assert "TEST CHANGE" in captured.out

    def test_monitor_basic(self, temp_log_file, capsys):
        """Тест базовой функции monitor"""
        state = SelfState()
        state.ticks = 10
        state.age = 5.5
        state.energy = 75.0
        state.integrity = 0.8
        state.stability = 0.7
        state.last_significance = 0.5

        monitor(state, temp_log_file)

        # Проверяем, что что-то выведено в консоль
        captured = capsys.readouterr()
        assert "10" in captured.out or captured.out  # Может быть пустым из-за \r

        # Проверяем, что запись добавлена в лог файл
        assert temp_log_file.exists()
        with temp_log_file.open("r") as f:
            lines = f.readlines()
            assert len(lines) > 0
            last_line = json.loads(lines[-1])
            assert last_line["tick"] == 10
            assert last_line["age"] == 5.5
            assert last_line["energy"] == 75.0

    def test_monitor_with_activated_memory(self, temp_log_file, capsys):
        """Тест monitor с активированной памятью"""
        state = SelfState()
        state.ticks = 20
        state.activated_memory = [
            MemoryEntry("event1", 0.8, time.time()),
            MemoryEntry("event2", 0.6, time.time()),
        ]
        state.last_pattern = "dampen"

        monitor(state, temp_log_file)

        # Проверяем лог файл
        assert temp_log_file.exists()
        with temp_log_file.open("r") as f:
            lines = f.readlines()
            assert len(lines) > 0

    def test_monitor_without_activated_memory(self, temp_log_file, capsys):
        """Тест monitor без активированной памяти"""
        state = SelfState()
        state.ticks = 30
        state.activated_memory = []
        state.last_pattern = ""

        monitor(state, temp_log_file)

        # Проверяем лог файл
        assert temp_log_file.exists()
        with temp_log_file.open("r") as f:
            lines = f.readlines()
            assert len(lines) > 0

    def test_monitor_multiple_calls(self, temp_log_file, capsys):
        """Тест нескольких вызовов monitor"""
        state = SelfState()

        for i in range(5):
            state.ticks = i
            state.energy = 100.0 - i
            monitor(state, temp_log_file)

        # Проверяем, что все записи добавлены
        assert temp_log_file.exists()
        with temp_log_file.open("r") as f:
            lines = f.readlines()
            assert len(lines) == 5

            # Проверяем последнюю запись
            last_line = json.loads(lines[-1])
            assert last_line["tick"] == 4
            assert last_line["energy"] == 96.0

    def test_monitor_log_file_append(self, temp_log_file, capsys):
        """Тест, что monitor добавляет записи в конец файла"""
        state = SelfState()

        # Первая запись
        state.ticks = 1
        monitor(state, temp_log_file)

        # Вторая запись
        state.ticks = 2
        monitor(state, temp_log_file)

        # Проверяем, что обе записи в файле
        with temp_log_file.open("r") as f:
            lines = f.readlines()
            assert len(lines) == 2
            assert json.loads(lines[0])["tick"] == 1
            assert json.loads(lines[1])["tick"] == 2

    def test_monitor_all_state_fields(self, temp_log_file, capsys):
        """Тест, что все поля состояния логируются"""
        state = SelfState()
        state.ticks = 100
        state.age = 50.5
        state.energy = 25.0
        state.integrity = 0.3
        state.stability = 0.4
        state.last_significance = 0.7

        monitor(state, temp_log_file)

        with temp_log_file.open("r") as f:
            lines = f.readlines()
            data = json.loads(lines[-1])

            assert data["tick"] == 100
            assert data["age"] == 50.5
            assert data["energy"] == 25.0
            assert data["integrity"] == 0.3
            assert data["stability"] == 0.4
            assert data["last_significance"] == 0.7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
