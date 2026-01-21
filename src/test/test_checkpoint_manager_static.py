"""
Static tests for checkpoint_manager.py - basic functionality validation without external dependencies
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import json
import tempfile
from datetime import datetime
from src.checkpoint_manager import CheckpointManager, TaskState


# Test TaskState enum
def test_task_state_enum():
    """Test TaskState enum values"""
    assert TaskState.PENDING.value == "pending"
    assert TaskState.IN_PROGRESS.value == "in_progress"
    assert TaskState.COMPLETED.value == "completed"
    assert TaskState.FAILED.value == "failed"
    assert TaskState.ROLLED_BACK.value == "rolled_back"

    # Test all enum values are strings
    for state in TaskState:
        assert isinstance(state.value, str)


# Test CheckpointManager initialization
def test_checkpoint_manager_init_basic():
    """Test CheckpointManager basic initialization"""
    with patch('src.checkpoint_manager.CheckpointManager._load_checkpoint') as mock_load, \
         patch('src.checkpoint_manager.CheckpointManager._save_checkpoint') as mock_save, \
         patch('pathlib.Path.exists', return_value=False):

        mock_load.return_value = {"version": "1.0", "tasks": []}

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir))

            assert manager.project_dir == Path(temp_dir)
            assert manager.checkpoint_file.name == ".codeagent_checkpoint.json"
            assert manager.backup_file.name == ".codeagent_checkpoint.json.backup"

            # Verify checkpoint was loaded and saved (for new file)
            mock_load.assert_called_once()
            mock_save.assert_called_once()


def test_checkpoint_manager_init_with_custom_file():
    """Test CheckpointManager with custom checkpoint file"""
    with patch('src.checkpoint_manager.CheckpointManager._load_checkpoint') as mock_load, \
         patch('src.checkpoint_manager.CheckpointManager._save_checkpoint') as mock_save, \
         patch('pathlib.Path.exists', return_value=False):

        mock_load.return_value = {"version": "1.0", "tasks": []}

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir), "custom_checkpoint.json")

            assert manager.checkpoint_file.name == "custom_checkpoint.json"
            assert manager.backup_file.name == "custom_checkpoint.json.backup"


# Test checkpoint loading
def test_load_checkpoint_new_file():
    """Test _load_checkpoint with new file (no existing checkpoint)"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = CheckpointManager(Path(temp_dir))

        # Simulate no existing file
        with patch('pathlib.Path.exists', return_value=False):
            data = manager._load_checkpoint()

            # Check default structure
            assert data["version"] == "1.0"
            assert "server_state" in data
            assert "tasks" in data
            assert "current_task" in data
            assert "session_id" in data
            assert "last_update" in data

            # Check server_state defaults
            server_state = data["server_state"]
            assert server_state["last_start_time"] is None
            assert server_state["last_stop_time"] is None
            assert server_state["iteration_count"] == 0
            assert server_state["clean_shutdown"] is True


def test_load_checkpoint_existing_file():
    """Test _load_checkpoint with existing file"""
    test_data = {
        "version": "1.0",
        "server_state": {
            "last_start_time": "2023-01-01T10:00:00",
            "clean_shutdown": False
        },
        "tasks": [{"id": "task1", "state": "completed"}]
    }

    with patch('builtins.open', mock_open(read_data=json.dumps(test_data))), \
         patch('pathlib.Path.exists', return_value=True):

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir))
            data = manager._load_checkpoint()

            assert data == test_data


def test_load_checkpoint_corrupted_file():
    """Test _load_checkpoint with corrupted JSON file"""
    with patch('builtins.open', mock_open(read_data="invalid json")), \
         patch('pathlib.Path.exists', side_effect=[True, False]), \
         patch('json.load', side_effect=json.JSONDecodeError("Test error", "doc", 0)):

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir))
            data = manager._load_checkpoint()

            # Should return default data
            assert data["version"] == "1.0"
            assert data["tasks"] == []


def test_load_checkpoint_backup_recovery():
    """Test _load_checkpoint backup recovery when main file is corrupted"""
    backup_data = {
        "version": "1.0",
        "server_state": {"clean_shutdown": True},
        "tasks": [{"id": "backup_task"}]
    }

    with patch('pathlib.Path.exists', side_effect=[True, True]), \
         patch('builtins.open') as mock_file, \
         patch('json.load', side_effect=[Exception("Main corrupted"), backup_data]):

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir))
            data = manager._load_checkpoint()

            # Should return backup data
            assert data == backup_data


# Test checkpoint saving
def test_save_checkpoint_basic():
    """Test _save_checkpoint basic functionality"""
    with patch('pathlib.Path.mkdir'), \
         patch('builtins.open', mock_open()) as mock_file, \
         patch('json.dump') as mock_json_dump:

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir))

            manager._save_checkpoint(create_backup=False)

            # Verify JSON dump was called
            mock_json_dump.assert_called_once()
            args, kwargs = mock_json_dump.call_args
            assert "last_update" in args[0]  # Should have updated timestamp


def test_save_checkpoint_with_backup():
    """Test _save_checkpoint with backup creation"""
    with patch('pathlib.Path.mkdir'), \
         patch('pathlib.Path.exists', return_value=True), \
         patch('builtins.open', mock_open()), \
         patch('json.dump'), \
         patch('shutil.copy2') as mock_copy:

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir))

            manager._save_checkpoint(create_backup=True)

            # Verify backup was created
            mock_copy.assert_called_once()


# Test server state management
def test_mark_server_start():
    """Test mark_server_start method"""
    with patch('src.checkpoint_manager.CheckpointManager._save_checkpoint') as mock_save:

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir))

            session_id = "test_session_123"
            manager.mark_server_start(session_id)

            # Verify state changes
            server_state = manager.checkpoint_data["server_state"]
            assert server_state["clean_shutdown"] is False
            assert manager.checkpoint_data["session_id"] == session_id
            assert "last_start_time" in server_state

            # Verify save was called
            mock_save.assert_called_once()


def test_mark_server_stop_clean():
    """Test mark_server_stop with clean shutdown"""
    with patch('src.checkpoint_manager.CheckpointManager._save_checkpoint') as mock_save:

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir))

            manager.mark_server_stop(clean=True)

            # Verify clean shutdown
            server_state = manager.checkpoint_data["server_state"]
            assert server_state["clean_shutdown"] is True
            assert "last_stop_time" in server_state

            mock_save.assert_called_once()


def test_mark_server_stop_unclean():
    """Test mark_server_stop with unclean shutdown"""
    with patch('src.checkpoint_manager.CheckpointManager._save_checkpoint') as mock_save:

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir))

            manager.mark_server_stop(clean=False)

            # Verify unclean shutdown
            server_state = manager.checkpoint_data["server_state"]
            assert server_state["clean_shutdown"] is False

            mock_save.assert_called_once()


def test_increment_iteration():
    """Test increment_iteration method"""
    with patch('src.checkpoint_manager.CheckpointManager._save_checkpoint') as mock_save:

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir))

            initial_count = manager.get_iteration_count()
            manager.increment_iteration()

            assert manager.get_iteration_count() == initial_count + 1
            mock_save.assert_called_once()


def test_get_iteration_count():
    """Test get_iteration_count method"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = CheckpointManager(Path(temp_dir))

        count = manager.get_iteration_count()
        assert isinstance(count, int)
        assert count >= 0


def test_was_clean_shutdown():
    """Test was_clean_shutdown method"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = CheckpointManager(Path(temp_dir))

        # Initially should be clean (default)
        assert manager.was_clean_shutdown() is True

        # Mark unclean start
        manager.mark_server_start("test")
        assert manager.was_clean_shutdown() is False

        # Mark clean stop
        manager.mark_server_stop(clean=True)
        assert manager.was_clean_shutdown() is True


# Test task management
def test_add_task():
    """Test add_task method"""
    with patch('src.checkpoint_manager.CheckpointManager._save_checkpoint') as mock_save:

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir))

            task_id = "task_123"
            task_text = "Test task"
            metadata = {"priority": "high"}

            manager.add_task(task_id, task_text, metadata)

            # Verify task was added
            tasks = manager.checkpoint_data["tasks"]
            assert len(tasks) == 1

            task = tasks[0]
            assert task["id"] == task_id
            assert task["text"] == task_text
            assert task["state"] == TaskState.PENDING.value
            assert task["metadata"] == metadata
            assert "created_at" in task
            assert "attempts" in task

            mock_save.assert_called_once()


def test_mark_task_start():
    """Test mark_task_start method"""
    with patch('src.checkpoint_manager.CheckpointManager._save_checkpoint') as mock_save:

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir))

            # Add a task first
            task_id = "task_123"
            manager.add_task(task_id, "Test task")

            # Mark it as started
            manager.mark_task_start(task_id)

            # Verify state change
            task = manager.checkpoint_data["tasks"][0]
            assert task["state"] == TaskState.IN_PROGRESS.value
            assert task["started_at"] is not None
            assert manager.checkpoint_data["current_task"] == task_id

            mock_save.assert_called_once()


def test_mark_task_completed():
    """Test mark_task_completed method"""
    with patch('src.checkpoint_manager.CheckpointManager._save_checkpoint') as mock_save:

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir))

            # Add and start a task
            task_id = "task_123"
            manager.add_task(task_id, "Test task")
            manager.mark_task_start(task_id)

            # Mark as completed
            result = {"output": "success"}
            manager.mark_task_completed(task_id, result)

            # Verify completion
            task = manager.checkpoint_data["tasks"][0]
            assert task["state"] == TaskState.COMPLETED.value
            assert task["completed_at"] is not None
            assert task["result"] == result
            assert manager.checkpoint_data["current_task"] is None

            mock_save.assert_called_once()


def test_mark_task_failed():
    """Test mark_task_failed method"""
    with patch('src.checkpoint_manager.CheckpointManager._save_checkpoint') as mock_save:

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir))

            # Add and start a task
            task_id = "task_123"
            manager.add_task(task_id, "Test task")
            manager.mark_task_start(task_id)

            # Mark as failed
            error_msg = "Test error"
            manager.mark_task_failed(task_id, error_msg)

            # Verify failure
            task = manager.checkpoint_data["tasks"][0]
            assert task["state"] == TaskState.FAILED.value
            assert task["error_message"] == error_msg
            assert task["attempts"] == 1
            assert manager.checkpoint_data["current_task"] is None

            mock_save.assert_called_once()


def test_get_current_task():
    """Test get_current_task method"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = CheckpointManager(Path(temp_dir))

        # No current task initially
        assert manager.get_current_task() is None

        # Add and start a task
        task_id = "task_123"
        manager.add_task(task_id, "Test task")
        manager.mark_task_start(task_id)

        # Should return the task
        current = manager.get_current_task()
        assert current is not None
        assert current["id"] == task_id


def test_get_incomplete_tasks():
    """Test get_incomplete_tasks method"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = CheckpointManager(Path(temp_dir))

        # Add tasks with different states
        manager.add_task("task1", "Task 1")
        manager.add_task("task2", "Task 2")
        manager.add_task("task3", "Task 3")

        manager.mark_task_start("task2")
        manager.mark_task_completed("task3")

        incomplete = manager.get_incomplete_tasks()

        # Should return pending and in_progress tasks
        assert len(incomplete) == 2
        task_ids = [t["id"] for t in incomplete]
        assert "task1" in task_ids
        assert "task2" in task_ids
        assert "task3" not in task_ids


def test_get_failed_tasks():
    """Test get_failed_tasks method"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = CheckpointManager(Path(temp_dir))

        # Add tasks and fail some
        manager.add_task("task1", "Task 1")
        manager.add_task("task2", "Task 2")
        manager.mark_task_failed("task1", "Error 1")

        failed = manager.get_failed_tasks()

        assert len(failed) == 1
        assert failed[0]["id"] == "task1"
        assert failed[0]["error_message"] == "Error 1"


def test_should_retry_task():
    """Test should_retry_task method"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = CheckpointManager(Path(temp_dir))

        # Add a task
        task_id = "task1"
        manager.add_task(task_id, "Test task")

        # Initially should retry
        assert manager.should_retry_task(task_id, max_attempts=3) is True

        # Fail the task multiple times
        manager.mark_task_failed(task_id, "Error 1")
        assert manager.should_retry_task(task_id, max_attempts=3) is True

        manager.mark_task_failed(task_id, "Error 2")
        assert manager.should_retry_task(task_id, max_attempts=3) is True

        manager.mark_task_failed(task_id, "Error 3")
        assert manager.should_retry_task(task_id, max_attempts=3) is False  # Exceeded max attempts


def test_is_task_completed():
    """Test is_task_completed method"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = CheckpointManager(Path(temp_dir))

        # Add tasks
        manager.add_task("task1", "Task 1")
        manager.add_task("task2", "Task 2")
        manager.mark_task_completed("task2")

        # Test completion check
        assert manager.is_task_completed("Task 1") is False
        assert manager.is_task_completed("Task 2") is True
        assert manager.is_task_completed("Non-existent task") is False


def test_get_recovery_info():
    """Test get_recovery_info method"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = CheckpointManager(Path(temp_dir))

        # Add some tasks with different states
        manager.add_task("task1", "Task 1")
        manager.add_task("task2", "Task 2")
        manager.mark_task_start("task2")
        manager.mark_task_failed("task2", "Error")

        recovery_info = manager.get_recovery_info()

        # Check structure
        assert "incomplete_tasks" in recovery_info
        assert "failed_tasks" in recovery_info
        assert "current_task" in recovery_info
        assert "server_state" in recovery_info

        assert len(recovery_info["incomplete_tasks"]) == 2  # task1 pending, task2 failed
        assert len(recovery_info["failed_tasks"]) == 1


def test_clear_old_tasks():
    """Test clear_old_tasks method"""
    with patch('src.checkpoint_manager.CheckpointManager._save_checkpoint') as mock_save:

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir))

            # Add many tasks
            for i in range(150):
                manager.add_task(f"task{i}", f"Task {i}")

            # Clear to keep only last 100
            manager.clear_old_tasks(keep_last_n=100)

            assert len(manager.checkpoint_data["tasks"]) == 100
            mock_save.assert_called_once()


def test_get_statistics():
    """Test get_statistics method"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = CheckpointManager(Path(temp_dir))

        # Add tasks with different states
        for i in range(10):
            manager.add_task(f"task{i}", f"Task {i}")

        # Change some task states
        manager.mark_task_completed("task0")
        manager.mark_task_completed("task1")
        manager.mark_task_failed("task2")
        manager.mark_task_start("task3")

        stats = manager.get_statistics()

        # Check statistics structure
        assert "total_tasks" in stats
        assert "completed_tasks" in stats
        assert "failed_tasks" in stats
        assert "in_progress_tasks" in stats
        assert "pending_tasks" in stats

        assert stats["total_tasks"] == 10
        assert stats["completed_tasks"] == 2
        assert stats["failed_tasks"] == 1
        assert stats["in_progress_tasks"] == 1
        assert stats["pending_tasks"] == 6