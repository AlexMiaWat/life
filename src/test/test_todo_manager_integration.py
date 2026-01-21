"""
Integration tests for todo_manager.py - testing with real file system operations
"""

import pytest
from pathlib import Path
from src.todo_manager import TodoManager, TodoItem
import tempfile
import os
import yaml


class TestTodoManagerIntegration:
    """Integration tests for TodoManager with real file operations"""

    def test_full_todo_workflow_txt(self):
        """Integration test: full workflow with text format"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Create todo.txt file
            todo_file = project_dir / "todo.txt"
            todo_file.write_text("""Task 1
Task 2
  Subtask 1
Task 3  # With comment
""")

            # Create manager and load
            manager = TodoManager(project_dir)

            # Verify loading
            assert len(manager.items) == 4
            assert manager.items[0].text == "Task 1"
            assert manager.items[1].text == "Task 2"
            assert manager.items[2].text == "Subtask 1"
            assert manager.items[2].level == 1
            assert manager.items[3].text == "Task 3"
            assert manager.items[3].comment == "With comment"

            # Test get_pending_tasks
            pending = manager.get_pending_tasks()
            assert len(pending) == 4

            # Test mark_task_done
            result = manager.mark_task_done("Task 1", "Completed")
            assert result is True

            # Verify task was marked done and saved
            assert manager.items[0].done is True
            assert manager.items[0].comment == "Completed"

            # Verify file was updated
            content = todo_file.read_text()
            assert "✓ Task 1" in content

    def test_full_todo_workflow_markdown(self):
        """Integration test: full workflow with markdown format"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Create todo.md file
            todo_file = project_dir / "todo.md"
            todo_file.write_text("""# Todo List

- [ ] Task 1
- [ ] Task 2 <!-- Important task -->
  - [ ] Subtask 2.1
- [x] Completed task
""")

            # Create manager and load
            manager = TodoManager(project_dir, todo_format="md")

            # Verify loading
            assert len(manager.items) == 4
            assert manager.items[0].text == "Task 1"
            assert manager.items[0].done is False
            assert manager.items[1].text == "Task 2"
            assert manager.items[1].comment == "Important task"
            assert manager.items[2].text == "Subtask 2.1"
            assert manager.items[2].level == 1
            assert manager.items[3].text == "Completed task"
            assert manager.items[3].done is True

            # Test hierarchy
            hierarchy = manager.get_task_hierarchy()
            assert hierarchy["total_tasks"] == 4
            assert hierarchy["completed_tasks"] == 1
            assert hierarchy["pending_tasks"] == 3

    def test_full_todo_workflow_yaml(self):
        """Integration test: full workflow with YAML format"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Create todo.yaml file
            todo_file = project_dir / "todo.yaml"
            yaml_content = """
tasks:
  - text: "Task 1"
    done: false
  - text: "Task 2"
    done: true
    comment: "Already done"
  - text: "Task 3"
    level: 1
    done: false
"""
            todo_file.write_text(yaml_content)

            # Create manager and load
            manager = TodoManager(project_dir, todo_format="yaml")

            # Verify loading
            assert len(manager.items) == 3
            assert manager.items[0].text == "Task 1"
            assert manager.items[0].done is False
            assert manager.items[1].text == "Task 2"
            assert manager.items[1].done is True
            assert manager.items[1].comment == "Already done"
            assert manager.items[2].text == "Task 3"
            assert manager.items[2].level == 1

            # Test operations
            pending = manager.get_pending_tasks()
            assert len(pending) == 2

            manager.mark_task_done("Task 3")
            assert manager.items[2].done is True

    def test_todo_file_discovery_integration(self):
        """Integration test: todo file discovery in different locations"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Test 1: todo.txt in root
            todo_txt = project_dir / "todo.txt"
            todo_txt.write_text("Root task")

            manager = TodoManager(project_dir)
            assert manager.todo_file == todo_txt
            assert len(manager.items) == 1

            # Clean up
            todo_txt.unlink()

            # Test 2: TODO.md in todo/ directory
            todo_dir = project_dir / "todo"
            todo_dir.mkdir()
            todo_md = todo_dir / "TODO.md"
            todo_md.write_text("- [ ] Directory task")

            manager2 = TodoManager(project_dir)
            assert manager2.todo_file == todo_md
            assert len(manager2.items) == 1

            # Test 3: CURRENT.md in todo/
            current_md = todo_dir / "CURRENT.md"
            current_md.write_text("Current task")

            manager3 = TodoManager(project_dir)
            # Should find CURRENT.md (it's in the search list)
            found_files = [f for f in [todo_md, current_md] if f.exists()]
            assert manager3.todo_file in found_files

    def test_file_format_detection_integration(self):
        """Integration test: automatic file format detection"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Test YAML detection by extension
            yaml_file = project_dir / "todo.yaml"
            yaml_file.write_text("tasks:\n  - text: 'YAML task'")
            manager = TodoManager(project_dir)
            assert manager._detect_file_format() == "yaml"

            # Test Markdown detection by extension
            yaml_file.unlink()
            md_file = project_dir / "todo.md"
            md_file.write_text("- [ ] Markdown task")
            manager2 = TodoManager(project_dir)
            assert manager2._detect_file_format() == "md"

            # Test content-based detection
            md_file.unlink()
            unknown_file = project_dir / "todo.unknown"
            unknown_file.write_text("- [ ] Content-based detection")
            manager3 = TodoManager(project_dir)
            assert manager3._detect_file_format() == "md"

    def test_file_size_limits_integration(self):
        """Integration test: file size limit enforcement"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Create a large file
            large_file = project_dir / "todo.txt"
            large_content = "Large task\n" * 10000  # Very large content
            large_file.write_text(large_content)

            # Create manager with small limit
            manager = TodoManager(project_dir, max_file_size=1000)

            # Should reject large file
            assert len(manager.items) == 0

            # Create manager with large limit
            manager2 = TodoManager(project_dir, max_file_size=10_000_000)
            assert len(manager2.items) > 0

    def test_unicode_file_handling_integration(self):
        """Integration test: unicode file content handling"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Create file with various unicode content
            todo_file = project_dir / "todo.txt"
            unicode_content = """Задача 1
Tâche 2
Aufgabe 3
任务 4
  Подзадача 1.1
"""
            todo_file.write_text(unicode_content, encoding='utf-8')

            manager = TodoManager(project_dir)

            # Verify all unicode tasks were loaded
            assert len(manager.items) == 5
            texts = [item.text for item in manager.items]
            assert "Задача 1" in texts
            assert "Tâche 2" in texts
            assert "Aufgabe 3" in texts
            assert "任务 4" in texts
            assert "Подзадача 1.1" in texts
            assert manager.items[4].level == 1  # Indented task

    def test_file_permission_handling_integration(self):
        """Integration test: file permission handling"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Create readable file
            todo_file = project_dir / "todo.txt"
            todo_file.write_text("Readable task")

            manager = TodoManager(project_dir)
            assert len(manager.items) == 1

            # Make file unreadable
            os.chmod(todo_file, 0o000)

            try:
                manager2 = TodoManager(project_dir)
                # Should handle permission error gracefully
                assert len(manager2.items) == 0
            finally:
                # Restore permissions for cleanup
                os.chmod(todo_file, 0o644)

    def test_save_operations_integration(self):
        """Integration test: save operations preserve data"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Test text format save
            todo_file = project_dir / "todo.txt"
            todo_file.write_text("Original task")

            manager = TodoManager(project_dir)
            original_count = len(manager.items)

            # Add a task programmatically
            manager.items.append(TodoItem("Added task", done=True))
            manager._save_todos()

            # Reload and verify
            manager2 = TodoManager(project_dir)
            assert len(manager2.items) == original_count + 1
            assert any(item.text == "Added task" and item.done for item in manager2.items)

    def test_mark_task_done_preserves_file_format(self):
        """Integration test: mark_task_done preserves original file format"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Test with Markdown
            todo_file = project_dir / "todo.md"
            todo_file.write_text("- [ ] Task 1\n- [ ] Task 2")

            manager = TodoManager(project_dir)
            manager.mark_task_done("Task 1")

            # Verify format is preserved
            content = todo_file.read_text()
            assert "- [x] Task 1" in content
            assert "- [ ] Task 2" in content

    def test_complex_hierarchy_parsing_integration(self):
        """Integration test: complex hierarchy parsing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Create complex nested structure
            todo_file = project_dir / "todo.txt"
            complex_content = """Project Alpha
  Phase 1
    Task 1.1
    Task 1.2
  Phase 2
    Task 2.1
      Subtask 2.1.1
      Subtask 2.1.2
Project Beta
  Setup
"""
            todo_file.write_text(complex_content)

            manager = TodoManager(project_dir)

            # Verify hierarchy
            assert len(manager.items) == 9
            levels = [item.level for item in manager.items]
            assert 0 in levels  # Root level
            assert 1 in levels  # Phase level
            assert 2 in levels  # Task level
            assert 3 in levels  # Subtask level

            # Verify hierarchy data structure
            hierarchy = manager.get_task_hierarchy()
            assert hierarchy["total_tasks"] == 9
            assert "hierarchy" in hierarchy

    def test_multiple_file_formats_coexist(self):
        """Integration test: multiple formats can coexist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Create files of different formats
            txt_file = project_dir / "todo.txt"
            txt_file.write_text("TXT task")

            md_file = project_dir / "todo.md"
            md_file.write_text("- [ ] MD task")

            yaml_file = project_dir / "todo.yaml"
            yaml_file.write_text("tasks:\n  - text: 'YAML task'")

            # Manager should find first match (todo.txt)
            manager = TodoManager(project_dir)
            assert manager.todo_file == txt_file
            assert len(manager.items) == 1
            assert manager.items[0].text == "TXT task"

    def test_empty_and_whitespace_handling_integration(self):
        """Integration test: empty lines and whitespace handling"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            todo_file = project_dir / "todo.txt"
            messy_content = """

Task 1

  Task 2
# Comment
Task 3  # Comment

"""
            todo_file.write_text(messy_content)

            manager = TodoManager(project_dir)

            # Should ignore empty lines and comments
            assert len(manager.items) == 3
            assert all(item.text.strip() for item in manager.items)
            assert manager.items[1].level == 1  # Indented task
            assert manager.items[2].comment == "Comment"

    def test_task_search_and_update_integration(self):
        """Integration test: task search and update operations"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            todo_file = project_dir / "todo.txt"
            todo_file.write_text("""Implement feature A
Fix bug in module B
Write documentation
  Update README
  Update API docs
Deploy to production
""")

            manager = TodoManager(project_dir)

            # Test partial match marking
            result = manager.mark_task_done("Implement feature")
            assert result is True
            assert manager.items[0].done is True

            # Test exact match
            result = manager.mark_task_done("Fix bug in module B")
            assert result is True
            assert manager.items[1].done is True

            # Test hierarchy preservation
            hierarchy = manager.get_task_hierarchy()
            assert hierarchy["completed_tasks"] == 2
            assert hierarchy["pending_tasks"] == 4