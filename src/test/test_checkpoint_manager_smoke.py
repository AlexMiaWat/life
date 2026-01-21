"""
Smoke tests for checkpoint_manager.py - basic functionality validation with minimal external dependencies
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import json
import os


class TestCheckpointManagerSmoke:
    """Smoke tests for CheckpointManager functionality"""

    def test_checkpoint_manager_creation_smoke(self):
        """Smoke test: CheckpointManager can be created"""
        from src.checkpoint_manager import CheckpointManager

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir))
            assert manager is not None
            assert isinstance(manager, CheckpointManager)

    def test_checkpoint_manager_with_custom_file_smoke(self):
        """Smoke test: CheckpointManager with custom file name"""
        from src.checkpoint_manager import CheckpointManager

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir), "my_checkpoint.json")
            assert manager is not None
            assert manager.checkpoint_file.name == "my_checkpoint.json"

    def test_task_state_enum_smoke(self):
        """Smoke test: TaskState enum works"""
        from src.checkpoint_manager import TaskState

        # Test all states exist
        assert TaskState.PENDING
        assert TaskState.IN_PROGRESS
        assert TaskState.COMPLETED
        assert TaskState.FAILED
        assert TaskState.ROLLED_BACK

        # Test string values
        assert isinstance(TaskState.PENDING.value, str)
        assert isinstance(TaskState.COMPLETED.value, str)

    def test_basic_checkpoint_operations_smoke(self):
        """Smoke test: basic checkpoint operations work"""
        from src.checkpoint_manager import CheckpointManager

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir))

            # Test basic getters
            iteration_count = manager.get_iteration_count()
            assert isinstance(iteration_count, int)

            clean_shutdown = manager.was_clean_shutdown()
            assert isinstance(clean_shutdown, bool)

            current_task = manager.get_current_task()
            # Can be None initially

    def test_server_lifecycle_smoke(self):
        """Smoke test: server start/stop lifecycle"""
        from src.checkpoint_manager import CheckpointManager

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir))

            # Test server start
            manager.mark_server_start("test_session_123")
            assert manager.checkpoint_data["session_id"] == "test_session_123"

            # Test server stop
            manager.mark_server_stop(clean=True)
            assert manager.was_clean_shutdown() is True

    def test_iteration_increment_smoke(self):
        """Smoke test: iteration increment works"""
        from src.checkpoint_manager import CheckpointManager

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir))

            initial_count = manager.get_iteration_count()
            manager.increment_iteration()
            new_count = manager.get_iteration_count()

            assert new_count == initial_count + 1

    def test_task_management_smoke(self):
        """Smoke test: basic task management works"""
        from src.checkpoint_manager import CheckpointManager

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir))

            # Add a task
            task_id = "smoke_test_task"
            manager.add_task(task_id, "Smoke test task")

            # Verify task was added
            tasks = manager.checkpoint_data["tasks"]
            assert len(tasks) == 1
            assert tasks[0]["id"] == task_id

            # Mark task as started
            manager.mark_task_start(task_id)

            # Check current task
            current = manager.get_current_task()
            assert current is not None
            assert current["id"] == task_id

            # Mark task as completed
            manager.mark_task_completed(task_id)

            # Check completion
            assert manager.is_task_completed("Smoke test task") is True

    def test_task_failure_handling_smoke(self):
        """Smoke test: task failure handling works"""
        from src.checkpoint_manager import CheckpointManager

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir))

            # Add and fail a task
            task_id = "fail_test_task"
            manager.add_task(task_id, "Fail test task")
            manager.mark_task_failed(task_id, "Test failure")

            # Check failed tasks
            failed_tasks = manager.get_failed_tasks()
            assert len(failed_tasks) == 1
            assert failed_tasks[0]["id"] == task_id

            # Check retry logic
            should_retry = manager.should_retry_task(task_id, max_attempts=3)
            assert isinstance(should_retry, bool)

    def test_incomplete_tasks_smoke(self):
        """Smoke test: incomplete tasks retrieval works"""
        from src.checkpoint_manager import CheckpointManager

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir))

            # Add multiple tasks with different states
            manager.add_task("task1", "Task 1")  # pending
            manager.add_task("task2", "Task 2")  # pending
            manager.add_task("task3", "Task 3")  # pending

            manager.mark_task_start("task2")     # in progress
            manager.mark_task_completed("task3") # completed

            # Get incomplete tasks
            incomplete = manager.get_incomplete_tasks()
            assert len(incomplete) == 2  # task1 (pending) and task2 (in progress)

            task_ids = [t["id"] for t in incomplete]
            assert "task1" in task_ids
            assert "task2" in task_ids
            assert "task3" not in task_ids

    def test_recovery_info_smoke(self):
        """Smoke test: recovery info generation works"""
        from src.checkpoint_manager import CheckpointManager

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir))

            # Add some tasks
            manager.add_task("task1", "Task 1")
            manager.mark_task_failed("task1", "Error")

            # Get recovery info
            recovery = manager.get_recovery_info()
            assert isinstance(recovery, dict)
            assert "incomplete_tasks" in recovery
            assert "failed_tasks" in recovery
            assert "current_task" in recovery
            assert "server_state" in recovery

    def test_statistics_smoke(self):
        """Smoke test: statistics generation works"""
        from src.checkpoint_manager import CheckpointManager

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir))

            # Add tasks with different states
            manager.add_task("task1", "Task 1")  # pending
            manager.add_task("task2", "Task 2")  # pending
            manager.mark_task_start("task2")     # in progress
            manager.add_task("task3", "Task 3")  # pending
            manager.mark_task_completed("task3") # completed
            manager.add_task("task4", "Task 4")  # pending
            manager.mark_task_failed("task4", "Error")  # failed

            # Get statistics
            stats = manager.get_statistics()
            assert isinstance(stats, dict)

            # Check expected keys
            expected_keys = [
                "total_tasks", "completed_tasks", "failed_tasks",
                "in_progress_tasks", "pending_tasks"
            ]
            for key in expected_keys:
                assert key in stats
                assert isinstance(stats[key], int)

            # Verify counts
            assert stats["total_tasks"] == 4
            assert stats["completed_tasks"] == 1
            assert stats["failed_tasks"] == 1
            assert stats["in_progress_tasks"] == 1
            assert stats["pending_tasks"] == 1

    def test_checkpoint_file_operations_smoke(self):
        """Smoke test: checkpoint file operations work"""
        from src.checkpoint_manager import CheckpointManager

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir))

            # File should exist after initialization
            assert manager.checkpoint_file.exists()

            # Read the file content
            content = manager.checkpoint_file.read_text()
            data = json.loads(content)

            # Verify basic structure
            assert "version" in data
            assert "server_state" in data
            assert "tasks" in data
            assert isinstance(data["tasks"], list)

    def test_backup_file_creation_smoke(self):
        """Smoke test: backup file operations work"""
        from src.checkpoint_manager import CheckpointManager

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir))

            # Manually trigger save with backup
            manager._save_checkpoint(create_backup=True)

            # Backup file should exist
            assert manager.backup_file.exists()

    def test_clear_old_tasks_smoke(self):
        """Smoke test: clearing old tasks works"""
        from src.checkpoint_manager import CheckpointManager

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir))

            # Add many tasks
            for i in range(50):
                manager.add_task(f"task{i}", f"Task {i}")

            initial_count = len(manager.checkpoint_data["tasks"])
            assert initial_count == 50

            # Clear to keep only 10
            manager.clear_old_tasks(keep_last_n=10)

            final_count = len(manager.checkpoint_data["tasks"])
            assert final_count == 10

    def test_reset_interrupted_task_smoke(self):
        """Smoke test: reset interrupted task works"""
        from src.checkpoint_manager import CheckpointManager

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir))

            # Add and start a task
            task_id = "interrupted_task"
            manager.add_task(task_id, "Interrupted task")
            manager.mark_task_start(task_id)

            # Verify it's in progress
            assert manager.get_current_task() is not None

            # Reset interrupted task
            manager.reset_interrupted_task()

            # Should clear current task
            assert manager.get_current_task() is None

    def test_instruction_progress_tracking_smoke(self):
        """Smoke test: instruction progress tracking works"""
        from src.checkpoint_manager import CheckpointManager

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir))

            # Add a task
            task_id = "progress_task"
            manager.add_task(task_id, "Progress test task")

            # Update instruction progress
            manager.update_instruction_progress(task_id, 5, 10)

            # Get progress
            progress = manager.get_instruction_progress(task_id)
            assert progress is not None
            assert progress["current"] == 5
            assert progress["total"] == 10
            assert "percentage" in progress

    def test_file_permission_handling_smoke(self):
        """Smoke test: handles file permission issues gracefully"""
        from src.checkpoint_manager import CheckpointManager

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create manager
            manager = CheckpointManager(Path(temp_dir))

            # Make checkpoint file unreadable (simulate permission issue)
            if os.name != 'nt':  # Skip on Windows
                try:
                    os.chmod(manager.checkpoint_file, 0o000)
                    # Try to load - should handle gracefully
                    data = manager._load_checkpoint()
                    # Should return default data
                    assert "version" in data
                finally:
                    # Restore permissions for cleanup
                    try:
                        os.chmod(manager.checkpoint_file, 0o644)
                    except:
                        pass

    def test_corrupted_json_recovery_smoke(self):
        """Smoke test: recovers from corrupted JSON gracefully"""
        from src.checkpoint_manager import CheckpointManager

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir))

            # Corrupt the checkpoint file
            manager.checkpoint_file.write_text("invalid json content")

            # Try to load - should recover gracefully
            data = manager._load_checkpoint()

            # Should return default data structure
            assert "version" in data
            assert "server_state" in data
            assert "tasks" in data

    def test_concurrent_access_simulation_smoke(self):
        """Smoke test: handles simulated concurrent access"""
        from src.checkpoint_manager import CheckpointManager

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir))

            # Simulate rapid operations that could conflict
            for i in range(20):
                manager.add_task(f"rapid_task_{i}", f"Rapid task {i}")
                manager.increment_iteration()

            # Verify data integrity
            tasks = manager.checkpoint_data["tasks"]
            assert len(tasks) == 20

            iteration_count = manager.get_iteration_count()
            assert iteration_count == 20

    def test_large_task_data_smoke(self):
        """Smoke test: handles large amounts of task data"""
        from src.checkpoint_manager import CheckpointManager

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CheckpointManager(Path(temp_dir))

            # Add tasks with large metadata
            large_metadata = {"data": "x" * 1000, "numbers": list(range(100))}

            for i in range(10):
                manager.add_task(
                    f"large_task_{i}",
                    f"Large task {i}",
                    metadata=large_metadata
                )

            # Verify all tasks were added
            tasks = manager.checkpoint_data["tasks"]
            assert len(tasks) == 10

            # Verify metadata was preserved
            for task in tasks:
                assert "metadata" in task
                assert task["metadata"]["data"] == "x" * 1000