"""
Smoke tests for todo_manager.py - basic functionality validation with minimal external dependencies
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import os


class TestTodoManagerSmoke:
    """Smoke tests for TodoManager functionality"""

    def test_todo_manager_creation_smoke(self):
        """Smoke test: TodoManager can be created"""
        from src.todo_manager import TodoManager

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TodoManager(Path(temp_dir))
            assert manager is not None
            assert isinstance(manager, TodoManager)

    def test_todo_manager_with_custom_params_smoke(self):
        """Smoke test: TodoManager creation with custom parameters"""
        from src.todo_manager import TodoManager

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TodoManager(
                Path(temp_dir),
                todo_format="yaml",
                max_file_size=500_000
            )
            assert manager is not None
            assert manager.todo_format == "yaml"
            assert manager.max_file_size == 500_000

    def test_todo_item_creation_smoke(self):
        """Smoke test: TodoItem can be created"""
        from src.todo_manager import TodoItem

        item = TodoItem("Test task")
        assert item is not None
        assert item.text == "Test task"
        assert item.done is False

    def test_todo_item_with_all_params_smoke(self):
        """Smoke test: TodoItem with all parameters"""
        from src.todo_manager import TodoItem

        parent = TodoItem("Parent")
        item = TodoItem(
            text="Child task",
            level=1,
            done=True,
            parent=parent,
            comment="Test comment"
        )
        assert item is not None
        assert item.text == "Child task"
        assert item.level == 1
        assert item.done is True
        assert item.parent == parent
        assert item.comment == "Test comment"

    def test_get_pending_tasks_smoke(self):
        """Smoke test: get_pending_tasks works"""
        from src.todo_manager import TodoManager, TodoItem

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TodoManager(Path(temp_dir))

            # Add some test items
            manager.items = [
                TodoItem("Task 1", done=False),
                TodoItem("Task 2", done=True),
                TodoItem("Task 3", done=False),
            ]

            pending = manager.get_pending_tasks()
            assert isinstance(pending, list)
            assert len(pending) == 2

    def test_get_all_tasks_smoke(self):
        """Smoke test: get_all_tasks works"""
        from src.todo_manager import TodoManager, TodoItem

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TodoManager(Path(temp_dir))

            manager.items = [
                TodoItem("Task 1"),
                TodoItem("Task 2"),
            ]

            all_tasks = manager.get_all_tasks()
            assert isinstance(all_tasks, list)
            assert len(all_tasks) == 2

    def test_mark_task_done_smoke(self):
        """Smoke test: mark_task_done works"""
        from src.todo_manager import TodoManager, TodoItem

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TodoManager(Path(temp_dir))

            manager.items = [
                TodoItem("Task 1", done=False),
                TodoItem("Task 2", done=False),
            ]

            result = manager.mark_task_done("Task 1")
            assert result is True
            assert manager.items[0].done is True

    def test_mark_task_done_not_found_smoke(self):
        """Smoke test: mark_task_done handles not found task"""
        from src.todo_manager import TodoManager, TodoItem

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TodoManager(Path(temp_dir))

            manager.items = [TodoItem("Task 1")]

            result = manager.mark_task_done("Non-existent")
            assert result is False

    def test_get_task_hierarchy_smoke(self):
        """Smoke test: get_task_hierarchy works"""
        from src.todo_manager import TodoManager, TodoItem

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TodoManager(Path(temp_dir))

            manager.items = [
                TodoItem("Task 1", done=False),
                TodoItem("Task 2", done=True),
            ]

            hierarchy = manager.get_task_hierarchy()
            assert isinstance(hierarchy, dict)
            assert "total_tasks" in hierarchy
            assert "completed_tasks" in hierarchy
            assert "pending_tasks" in hierarchy
            assert hierarchy["total_tasks"] == 2
            assert hierarchy["completed_tasks"] == 1
            assert hierarchy["pending_tasks"] == 1

    def test_find_todo_file_no_files_smoke(self):
        """Smoke test: _find_todo_file when no files exist"""
        from src.todo_manager import TodoManager

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TodoManager(Path(temp_dir))

            result = manager._find_todo_file()
            assert result is None

    def test_find_todo_file_with_file_smoke(self):
        """Smoke test: _find_todo_file when file exists"""
        from src.todo_manager import TodoManager

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a todo file
            todo_file = Path(temp_dir) / "todo.txt"
            todo_file.write_text("Test task")

            manager = TodoManager(Path(temp_dir))

            result = manager._find_todo_file()
            assert result is not None
            assert result == todo_file

    def test_detect_file_format_smoke(self):
        """Smoke test: _detect_file_format works"""
        from src.todo_manager import TodoManager

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TodoManager(Path(temp_dir))

            # Test without file
            manager.todo_file = None
            assert manager._detect_file_format() == "txt"

            # Test with txt file
            manager.todo_file = Path(temp_dir) / "todo.txt"
            assert manager._detect_file_format() == "txt"

            # Test with yaml file
            manager.todo_file = Path(temp_dir) / "todo.yaml"
            assert manager._detect_file_format() == "yaml"

            # Test with md file
            manager.todo_file = Path(temp_dir) / "todo.md"
            assert manager._detect_file_format() == "md"

    def test_load_from_text_smoke(self):
        """Smoke test: _load_from_text works"""
        from src.todo_manager import TodoManager

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TodoManager(Path(temp_dir))

            # Create test file
            test_file = Path(temp_dir) / "todo.txt"
            test_file.write_text("Task 1\nTask 2\n# Comment")

            manager.todo_file = test_file
            manager._load_from_text()

            assert len(manager.items) == 2
            assert manager.items[0].text == "Task 1"
            assert manager.items[1].text == "Task 2"

    def test_load_from_markdown_smoke(self):
        """Smoke test: _load_from_markdown works"""
        from src.todo_manager import TodoManager

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TodoManager(Path(temp_dir))

            # Create test markdown file
            test_file = Path(temp_dir) / "todo.md"
            test_file.write_text("- [ ] Task 1\n- [x] Task 2")

            manager.todo_file = test_file
            manager._load_from_markdown()

            assert len(manager.items) == 2
            assert manager.items[0].text == "Task 1"
            assert manager.items[0].done is False
            assert manager.items[1].text == "Task 2"
            assert manager.items[1].done is True

    def test_load_from_yaml_smoke(self):
        """Smoke test: _load_from_yaml works"""
        from src.todo_manager import TodoManager

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TodoManager(Path(temp_dir))

            # Create test YAML file
            test_file = Path(temp_dir) / "todo.yaml"
            test_file.write_text("""
tasks:
  - text: "Task 1"
    done: false
  - text: "Task 2"
    done: true
""")

            manager.todo_file = test_file
            manager._load_from_yaml()

            assert len(manager.items) == 2
            assert manager.items[0].text == "Task 1"
            assert manager.items[0].done is False
            assert manager.items[1].text == "Task 2"
            assert manager.items[1].done is True

    def test_save_todos_smoke(self):
        """Smoke test: _save_todos works"""
        from src.todo_manager import TodoManager, TodoItem

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test file first
            test_file = Path(temp_dir) / "todo.txt"
            test_file.write_text("")

            manager = TodoManager(Path(temp_dir))
            manager.todo_file = test_file
            manager.items = [TodoItem("Test task")]

            # This should not raise an exception
            manager._save_todos()

    def test_load_todos_no_file_smoke(self):
        """Smoke test: _load_todos handles missing file"""
        from src.todo_manager import TodoManager

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TodoManager(Path(temp_dir))

            # Should not raise exception when no file exists
            manager._load_todos()
            assert manager.items == []

    def test_file_size_limit_smoke(self):
        """Smoke test: respects file size limits"""
        from src.todo_manager import TodoManager

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a large file
            test_file = Path(temp_dir) / "todo.txt"
            large_content = "x" * 2_000_000  # 2MB file
            test_file.write_text(large_content)

            # Create manager with small limit
            manager = TodoManager(Path(temp_dir), max_file_size=1_000_000)

            # Should handle large file gracefully
            manager._load_todos()
            # Items should be empty due to size limit
            assert manager.items == []

    def test_unicode_handling_smoke(self):
        """Smoke test: handles unicode content"""
        from src.todo_manager import TodoManager

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TodoManager(Path(temp_dir))

            # Create file with unicode content
            test_file = Path(temp_dir) / "todo.txt"
            test_file.write_text("Задача 1\nTask 2\nПривет мир")

            manager.todo_file = test_file
            manager._load_from_text()

            assert len(manager.items) == 3
            assert "Задача 1" in [item.text for item in manager.items]
            assert "Привет мир" in [item.text for item in manager.items]

    def test_mixed_formats_smoke(self):
        """Smoke test: handles mixed task formats"""
        from src.todo_manager import TodoManager

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TodoManager(Path(temp_dir))

            # Create file with mixed formats
            test_file = Path(temp_dir) / "todo.txt"
            test_file.write_text("""
1. Numbered task
- Bullet task
* Another bullet
  Indented task
Task with comment  # This is a comment
""")

            manager.todo_file = test_file
            manager._load_from_text()

            # Should parse all tasks
            assert len(manager.items) >= 4
            assert any("Numbered task" in item.text for item in manager.items)
            assert any("Bullet task" in item.text for item in manager.items)