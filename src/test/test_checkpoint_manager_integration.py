"""
Integration tests for checkpoint_manager.py - testing with real file system operations
"""

import pytest
from pathlib import Path
from src.checkpoint_manager import CheckpointManager, TaskState
import tempfile
import json
import os
import time
from datetime import datetime


class TestCheckpointManagerIntegration:
    """Integration tests for CheckpointManager with real file operations"""

    def test_full_checkpoint_lifecycle(self):
        """Integration test: full checkpoint save/load lifecycle"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Create manager and add some data
            manager = CheckpointManager(project_dir)

            # Add server session
            session_id = "integration_test_session"
            manager.mark_server_start(session_id)

            # Add tasks
            manager.add_task("task1", "Integration test task 1")
            manager.add_task("task2", "Integration test task 2")

            # Start and complete a task
            manager.mark_task_start("task1")
            manager.mark_task_completed("task1", {"result": "success"})

            # Fail another task
            manager.mark_task_failed("task2", "Integration test error")

            # Force save
            manager._save_checkpoint()

            # Verify file exists and is valid JSON
            assert manager.checkpoint_file.exists()
            content = manager.checkpoint_file.read_text()
            data = json.loads(content)

            # Verify structure
            assert data["version"] == "1.0"
            assert data["session_id"] == session_id
            assert len(data["tasks"]) == 2

            # Verify task states
            task1 = next(t for t in data["tasks"] if t["id"] == "task1")
            task2 = next(t for t in data["tasks"] if t["id"] == "task2")

            assert task1["state"] == TaskState.COMPLETED.value
            assert task1["result"] == {"result": "success"}
            assert task2["state"] == TaskState.FAILED.value
            assert task2["error_message"] == "Integration test error"

    def test_checkpoint_persistence_across_instances(self):
        """Integration test: checkpoint data persists across manager instances"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # First manager instance
            manager1 = CheckpointManager(project_dir)
            manager1.add_task("persistent_task", "Task that should persist")
            manager1.mark_task_start("persistent_task")
            manager1.increment_iteration()

            # Force save
            manager1._save_checkpoint()

            # Create second manager instance (simulates restart)
            manager2 = CheckpointManager(project_dir)

            # Verify data was loaded correctly
            tasks = manager2.checkpoint_data["tasks"]
            assert len(tasks) == 1
            assert tasks[0]["id"] == "persistent_task"
            assert tasks[0]["state"] == TaskState.IN_PROGRESS.value

            # Verify iteration count
            assert manager2.get_iteration_count() == 1

    def test_backup_recovery_integration(self):
        """Integration test: backup recovery when main file is corrupted"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Create manager and add data
            manager = CheckpointManager(project_dir)
            manager.add_task("backup_test_task", "Task for backup testing")
            manager._save_checkpoint()  # Creates backup

            # Verify backup exists
            assert manager.backup_file.exists()

            # Corrupt main checkpoint file
            manager.checkpoint_file.write_text("corrupted json data { invalid")

            # Create new manager instance - should recover from backup
            manager2 = CheckpointManager(project_dir)

            # Verify recovery worked
            tasks = manager2.checkpoint_data["tasks"]
            assert len(tasks) == 1
            assert tasks[0]["id"] == "backup_test_task"

    def test_server_state_persistence_integration(self):
        """Integration test: server state persistence across restarts"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # First session
            manager1 = CheckpointManager(project_dir)
            manager1.mark_server_start("session_1")

            # Simulate some work
            for i in range(5):
                manager1.increment_iteration()

            manager1.mark_server_stop(clean=True)

            # Second session (restart)
            manager2 = CheckpointManager(project_dir)
            manager2.mark_server_start("session_2")

            # Verify previous session data was preserved
            server_state = manager2.checkpoint_data["server_state"]
            assert server_state["iteration_count"] == 5
            assert server_state["clean_shutdown"] is True
            assert "last_stop_time" in server_state

            # Verify new session
            assert manager2.checkpoint_data["session_id"] == "session_2"

    def test_task_workflow_integration(self):
        """Integration test: complete task workflow with file persistence"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            manager = CheckpointManager(project_dir)

            # Create a complex task workflow
            tasks_to_create = [
                ("feature_dev", "Develop new feature"),
                ("testing", "Write comprehensive tests"),
                ("documentation", "Update documentation"),
                ("deployment", "Deploy to production")
            ]

            # Add all tasks
            for task_id, task_text in tasks_to_create:
                manager.add_task(task_id, task_text)

            # Simulate workflow progress
            manager.mark_task_start("feature_dev")
            time.sleep(0.01)  # Small delay for timestamps
            manager.mark_task_completed("feature_dev")

            manager.mark_task_start("testing")
            manager.update_instruction_progress("testing", 50, 100)  # 50% complete

            # Save and reload
            manager._save_checkpoint()
            manager2 = CheckpointManager(project_dir)

            # Verify workflow state was preserved
            tasks = manager2.checkpoint_data["tasks"]
            assert len(tasks) == 4

            # Find specific tasks
            dev_task = next(t for t in tasks if t["id"] == "feature_dev")
            test_task = next(t for t in tasks if t["id"] == "testing")

            assert dev_task["state"] == TaskState.COMPLETED.value
            assert "completed_at" in dev_task

            assert test_task["state"] == TaskState.IN_PROGRESS.value
            assert manager2.get_current_task()["id"] == "testing"

            # Check progress tracking
            progress = manager2.get_instruction_progress("testing")
            assert progress["current"] == 50
            assert progress["total"] == 100
            assert progress["percentage"] == 50.0

    def test_failure_recovery_workflow_integration(self):
        """Integration test: failure and recovery workflow"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            manager = CheckpointManager(project_dir)

            # Create tasks that will fail and be retried
            manager.add_task("unstable_task", "Task that fails intermittently")

            # First attempt - fails
            manager.mark_task_start("unstable_task")
            manager.mark_task_failed("unstable_task", "Connection timeout")

            # Second attempt - also fails
            manager.mark_task_start("unstable_task")
            manager.mark_task_failed("unstable_task", "Network error")

            # Check failure tracking
            failed_tasks = manager.get_failed_tasks()
            assert len(failed_tasks) == 1
            assert failed_tasks[0]["attempts"] == 2

            # Check retry logic
            should_retry = manager.should_retry_task("unstable_task", max_attempts=3)
            assert should_retry is True  # Still within limit

            # Third attempt - succeeds
            manager.mark_task_start("unstable_task")
            manager.mark_task_completed("unstable_task")

            # Verify final state
            task = manager.checkpoint_data["tasks"][0]
            assert task["state"] == TaskState.COMPLETED.value
            assert task["attempts"] == 3

            # Verify retry check now returns False
            should_retry_after = manager.should_retry_task("unstable_task", max_attempts=3)
            assert should_retry_after is False

    def test_statistics_accuracy_integration(self):
        """Integration test: statistics accuracy with real task states"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            manager = CheckpointManager(project_dir)

            # Create tasks in various states
            states_to_create = [
                ("pending1", TaskState.PENDING),
                ("pending2", TaskState.PENDING),
                ("in_progress1", TaskState.IN_PROGRESS),
                ("completed1", TaskState.COMPLETED),
                ("completed2", TaskState.COMPLETED),
                ("failed1", TaskState.FAILED),
                ("failed2", TaskState.FAILED),
                ("failed3", TaskState.FAILED),
            ]

            # Add tasks and set their states
            for task_id, target_state in states_to_create:
                manager.add_task(task_id, f"Task {task_id}")

                if target_state == TaskState.IN_PROGRESS:
                    manager.mark_task_start(task_id)
                elif target_state == TaskState.COMPLETED:
                    manager.mark_task_start(task_id)
                    manager.mark_task_completed(task_id)
                elif target_state == TaskState.FAILED:
                    manager.mark_task_start(task_id)
                    manager.mark_task_failed(task_id, "Test error")

            # Get statistics
            stats = manager.get_statistics()

            # Verify accuracy
            assert stats["total_tasks"] == 8
            assert stats["pending_tasks"] == 2
            assert stats["in_progress_tasks"] == 1
            assert stats["completed_tasks"] == 2
            assert stats["failed_tasks"] == 3

    def test_recovery_info_completeness_integration(self):
        """Integration test: recovery info provides complete state"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            manager = CheckpointManager(project_dir)

            # Set up complex state for recovery
            manager.mark_server_start("recovery_test_session")

            # Add various tasks
            manager.add_task("critical_task", "Critical pending task")
            manager.add_task("in_progress_task", "Task in progress")
            manager.mark_task_start("in_progress_task")

            manager.add_task("failed_task", "Failed task")
            manager.mark_task_start("failed_task")
            manager.mark_task_failed("failed_task", "Critical failure")

            manager.add_task("completed_task", "Completed task")
            manager.mark_task_start("completed_task")
            manager.mark_task_completed("completed_task")

            # Get recovery info
            recovery = manager.get_recovery_info()

            # Verify completeness
            assert len(recovery["incomplete_tasks"]) == 2  # critical_task + failed_task
            assert len(recovery["failed_tasks"]) == 1
            assert recovery["current_task"] == "in_progress_task"
            assert recovery["server_state"]["clean_shutdown"] is False

    def test_clear_old_tasks_file_operations_integration(self):
        """Integration test: clearing old tasks updates files correctly"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            manager = CheckpointManager(project_dir)

            # Add many tasks
            for i in range(150):
                manager.add_task(f"task_{i:03d}", f"Task number {i}")

            # Verify all were added
            assert len(manager.checkpoint_data["tasks"]) == 150

            # Clear old tasks
            manager.clear_old_tasks(keep_last_n=50)

            # Verify only recent tasks remain
            assert len(manager.checkpoint_data["tasks"]) == 50

            # Verify file was updated
            manager2 = CheckpointManager(project_dir)
            assert len(manager2.checkpoint_data["tasks"]) == 50

    def test_instruction_progress_persistence_integration(self):
        """Integration test: instruction progress persists across sessions"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # First session
            manager1 = CheckpointManager(project_dir)
            manager1.add_task("progress_task", "Task with progress tracking")

            # Update progress multiple times
            manager1.update_instruction_progress("progress_task", 25, 100)
            manager1.update_instruction_progress("progress_task", 50, 100)
            manager1.update_instruction_progress("progress_task", 75, 100)

            # Second session (reload)
            manager2 = CheckpointManager(project_dir)

            # Verify progress was preserved
            progress = manager2.get_instruction_progress("progress_task")
            assert progress is not None
            assert progress["current"] == 75
            assert progress["total"] == 100
            assert progress["percentage"] == 75.0

    def test_file_permission_error_handling_integration(self):
        """Integration test: handles file permission errors gracefully"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            manager = CheckpointManager(project_dir)

            # Make directory read-only (if possible)
            if os.name != 'nt':  # Skip on Windows
                try:
                    # Make checkpoint file unreadable
                    os.chmod(manager.checkpoint_file, 0o000)

                    # Try operations - should handle gracefully
                    manager.add_task("permission_test", "Task during permission error")
                    # Operation should complete without crashing

                    # Verify task was added to memory (even if save failed)
                    assert len(manager.checkpoint_data["tasks"]) == 1

                finally:
                    # Restore permissions
                    try:
                        os.chmod(manager.checkpoint_file, 0o644)
                    except:
                        pass

    def test_corrupted_backup_recovery_integration(self):
        """Integration test: recovers when both main and backup files are corrupted"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Create manager with good data
            manager1 = CheckpointManager(project_dir)
            manager1.add_task("survivor_task", "Task that survives corruption")
            manager1._save_checkpoint()  # Creates backup

            # Corrupt both files
            manager1.checkpoint_file.write_text("corrupted main file { invalid json")
            manager1.backup_file.write_text("corrupted backup file { also invalid")

            # Create new manager - should handle corruption gracefully
            manager2 = CheckpointManager(project_dir)

            # Should have default data, not crash
            assert "version" in manager2.checkpoint_data
            assert "tasks" in manager2.checkpoint_data
            # Survivor task should be lost due to corruption, but system should work

    def test_large_checkpoint_file_handling_integration(self):
        """Integration test: handles large checkpoint files efficiently"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            manager = CheckpointManager(project_dir)

            # Add tasks with large amounts of metadata
            large_data = {
                "description": "x" * 1000,
                "history": ["event"] * 100,
                "metadata": {"key": "value"} * 50
            }

            for i in range(100):
                manager.add_task(
                    f"large_task_{i}",
                    f"Large task {i}",
                    metadata=large_data
                )

            # Force save
            manager._save_checkpoint()

            # Verify file exists and is readable
            assert manager.checkpoint_file.exists()
            file_size = manager.checkpoint_file.stat().st_size
            assert file_size > 10000  # Should be reasonably large

            # Verify data integrity by reloading
            manager2 = CheckpointManager(project_dir)
            assert len(manager2.checkpoint_data["tasks"]) == 100

            # Verify a sample task
            sample_task = manager2.checkpoint_data["tasks"][50]
            assert len(sample_task["metadata"]["description"]) == 1000

    def test_concurrent_file_access_simulation_integration(self):
        """Integration test: simulates concurrent file access scenarios"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            manager = CheckpointManager(project_dir)

            # Simulate rapid operations that could cause file access conflicts
            import threading

            errors = []

            def worker(worker_id):
                try:
                    for i in range(10):
                        manager.add_task(f"worker_{worker_id}_task_{i}", f"Task {i} from worker {worker_id}")
                        manager.increment_iteration()
                        # Small delay to increase chance of conflicts
                        time.sleep(0.001)
                except Exception as e:
                    errors.append(f"Worker {worker_id}: {e}")

            # Start multiple threads
            threads = []
            for i in range(5):
                t = threading.Thread(target=worker, args=(i,))
                threads.append(t)
                t.start()

            # Wait for completion
            for t in threads:
                t.join()

            # Verify no errors occurred
            assert len(errors) == 0

            # Verify all operations completed
            tasks = manager.checkpoint_data["tasks"]
            assert len(tasks) == 50  # 5 workers * 10 tasks each

            iteration_count = manager.get_iteration_count()
            assert iteration_count == 50  # 5 workers * 10 increments each

    def test_timestamp_accuracy_integration(self):
        """Integration test: timestamp accuracy in operations"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            manager = CheckpointManager(project_dir)

            # Record time before operations
            start_time = datetime.now()

            # Perform operations with timestamps
            manager.mark_server_start("timestamp_test")
            manager.add_task("timestamp_task", "Task with timestamps")
            manager.mark_task_start("timestamp_task")

            time.sleep(0.01)  # Ensure some time passes

            manager.mark_task_completed("timestamp_task")

            # Check timestamps are reasonable
            server_state = manager.checkpoint_data["server_state"]
            start_time_str = server_state["last_start_time"]
            start_datetime = datetime.fromisoformat(start_time_str)

            # Should be after our recorded start time
            assert start_datetime >= start_time

            # Check task timestamps
            task = manager.checkpoint_data["tasks"][0]
            assert "created_at" in task
            assert "started_at" in task
            assert "completed_at" in task

            created_time = datetime.fromisoformat(task["created_at"])
            started_time = datetime.fromisoformat(task["started_at"])
            completed_time = datetime.fromisoformat(task["completed_at"])

            # Verify chronological order
            assert created_time <= started_time <= completed_time