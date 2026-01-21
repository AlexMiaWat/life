"""
Static tests for todo_manager.py - basic functionality validation without external dependencies
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import yaml


# Test TodoItem class
def test_todo_item_creation():
    """Test TodoItem basic creation"""
    from src.todo_manager import TodoItem

    item = TodoItem("Test task")
    assert item.text == "Test task"
    assert item.level == 0
    assert item.done is False
    assert item.parent is None
    assert item.children == []
    assert item.comment is None


def test_todo_item_with_parameters():
    """Test TodoItem creation with all parameters"""
    from src.todo_manager import TodoItem

    parent = TodoItem("Parent task")
    item = TodoItem(
        text="  Test task with spaces  ",
        level=2,
        done=True,
        parent=parent,
        comment="Test comment"
    )

    assert item.text == "Test task with spaces"  # Should be stripped
    assert item.level == 2
    assert item.done is True
    assert item.parent == parent
    assert item.children == []
    assert item.comment == "Test comment"


def test_todo_item_repr():
    """Test TodoItem string representation"""
    from src.todo_manager import TodoItem

    # Test pending task
    pending = TodoItem("Pending task", level=1)
    assert str(pending) == "  ○ Pending task"

    # Test completed task
    completed = TodoItem("Completed task", level=0, done=True)
    assert str(completed) == "✓ Completed task"

    # Test nested task
    nested = TodoItem("Nested task", level=2)
    assert str(nested) == "    ○ Nested task"


# Test TodoManager class
def test_todo_manager_constants():
    """Test TodoManager constants"""
    from src.todo_manager import TodoManager

    assert TodoManager.DEFAULT_MAX_FILE_SIZE == 1_000_000


def test_todo_manager_init_basic():
    """Test TodoManager basic initialization"""
    from src.todo_manager import TodoManager

    with patch('src.todo_manager.TodoManager._find_todo_file', return_value=None), \
         patch('src.todo_manager.TodoManager._load_todos'):

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TodoManager(Path(temp_dir))

            assert manager.project_dir == Path(temp_dir)
            assert manager.todo_format == "txt"
            assert manager.max_file_size == TodoManager.DEFAULT_MAX_FILE_SIZE
            assert manager.todo_file is None
            assert manager.items == []


def test_todo_manager_init_with_params():
    """Test TodoManager initialization with custom parameters"""
    from src.todo_manager import TodoManager

    with patch('src.todo_manager.TodoManager._find_todo_file', return_value=None), \
         patch('src.todo_manager.TodoManager._load_todos'):

        with tempfile.TemporaryDirectory() as temp_dir:
            custom_max_size = 500_000
            manager = TodoManager(
                Path(temp_dir),
                todo_format="yaml",
                max_file_size=custom_max_size
            )

            assert manager.todo_format == "yaml"
            assert manager.max_file_size == custom_max_size


@patch('pathlib.Path.exists')
def test_find_todo_file_root(mock_exists):
    """Test _find_todo_file in root directory"""
    from src.todo_manager import TodoManager

    # Mock file exists in root
    mock_exists.side_effect = lambda: True

    with tempfile.TemporaryDirectory() as temp_dir:
        manager = TodoManager(Path(temp_dir), todo_format="txt")

        # Mock the exists check to return True for todo.txt
        with patch.object(Path, 'exists') as mock_path_exists:
            mock_path_exists.return_value = True
            result = manager._find_todo_file()

            assert result is not None
            assert result.name == "todo.txt"


@patch('pathlib.Path.exists')
def test_find_todo_file_todo_dir(mock_exists):
    """Test _find_todo_file in todo/ subdirectory"""
    from src.todo_manager import TodoManager

    with tempfile.TemporaryDirectory() as temp_dir:
        manager = TodoManager(Path(temp_dir), todo_format="md")

        # Mock: root files don't exist, but todo/ dir exists with CURRENT.md
        def exists_side_effect(self):
            if str(self).endswith('todo.md') or str(self).endswith('TODO.txt'):
                return False
            if str(self).endswith('todo') and self.is_dir():
                return True
            if str(self).endswith('CURRENT.md'):
                return True
            return False

        with patch.object(Path, 'exists', exists_side_effect), \
             patch.object(Path, 'is_dir', return_value=True):

            result = manager._find_todo_file()
            assert result is not None
            assert result.name == "CURRENT.md"


def test_detect_file_format_yaml():
    """Test _detect_file_format for YAML files"""
    from src.todo_manager import TodoManager

    with tempfile.TemporaryDirectory() as temp_dir:
        manager = TodoManager(Path(temp_dir), todo_format="txt")

        # Test YAML by extension
        manager.todo_file = Path(temp_dir) / "todo.yaml"
        assert manager._detect_file_format() == "yaml"

        # Test YAML by .yml extension
        manager.todo_file = Path(temp_dir) / "todo.yml"
        assert manager._detect_file_format() == "yaml"


def test_detect_file_format_markdown():
    """Test _detect_file_format for Markdown files"""
    from src.todo_manager import TodoManager

    with tempfile.TemporaryDirectory() as temp_dir:
        manager = TodoManager(Path(temp_dir), todo_format="txt")

        # Test MD by extension
        manager.todo_file = Path(temp_dir) / "todo.md"
        assert manager._detect_file_format() == "md"

        # Test Markdown by extension
        manager.todo_file = Path(temp_dir) / "todo.markdown"
        assert manager._detect_file_format() == "md"


def test_detect_file_format_text():
    """Test _detect_file_format for text files"""
    from src.todo_manager import TodoManager

    with tempfile.TemporaryDirectory() as temp_dir:
        manager = TodoManager(Path(temp_dir), todo_format="txt")

        # Test TXT by extension
        manager.todo_file = Path(temp_dir) / "todo.txt"
        assert manager._detect_file_format() == "txt"

        # Test file without extension (defaults to txt)
        manager.todo_file = Path(temp_dir) / "TODO"
        assert manager._detect_file_format() == "txt"


def test_detect_file_format_by_content():
    """Test _detect_file_format by content analysis"""
    from src.todo_manager import TodoManager

    with tempfile.TemporaryDirectory() as temp_dir:
        manager = TodoManager(Path(temp_dir), todo_format="txt")

        # Test YAML content detection
        manager.todo_file = Path(temp_dir) / "unknown.ext"
        with patch('builtins.open', mock_open(read_data="---\ntasks:\n  - item1")):
            assert manager._detect_file_format() == "yaml"

        # Test Markdown content detection
        with patch('builtins.open', mock_open(read_data="- [ ] Task item\n# Header")):
            assert manager._detect_file_format() == "md"

        # Test fallback to txt
        with patch('builtins.open', mock_open(read_data="Plain text content")):
            assert manager._detect_file_format() == "txt"


def test_get_pending_tasks():
    """Test get_pending_tasks method"""
    from src.todo_manager import TodoManager, TodoItem

    with patch('src.todo_manager.TodoManager._find_todo_file', return_value=None), \
         patch('src.todo_manager.TodoManager._load_todos'):

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TodoManager(Path(temp_dir))

            # Set up test items
            manager.items = [
                TodoItem("Task 1", done=False),
                TodoItem("Task 2", done=True),
                TodoItem("Task 3", done=False),
            ]

            pending = manager.get_pending_tasks()
            assert len(pending) == 2
            assert all(not item.done for item in pending)
            assert "Task 1" in [item.text for item in pending]
            assert "Task 3" in [item.text for item in pending]


def test_get_all_tasks():
    """Test get_all_tasks method"""
    from src.todo_manager import TodoManager, TodoItem

    with patch('src.todo_manager.TodoManager._find_todo_file', return_value=None), \
         patch('src.todo_manager.TodoManager._load_todos'):

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TodoManager(Path(temp_dir))

            # Set up test items
            manager.items = [
                TodoItem("Task 1"),
                TodoItem("Task 2"),
                TodoItem("Task 3"),
            ]

            all_tasks = manager.get_all_tasks()
            assert len(all_tasks) == 3
            assert all_tasks == manager.items


def test_mark_task_done():
    """Test mark_task_done method"""
    from src.todo_manager import TodoManager, TodoItem

    with patch('src.todo_manager.TodoManager._find_todo_file', return_value=None), \
         patch('src.todo_manager.TodoManager._load_todos'), \
         patch('src.todo_manager.TodoManager._save_todos'):

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TodoManager(Path(temp_dir))

            # Set up test items
            manager.items = [
                TodoItem("Task 1", done=False),
                TodoItem("Task 2", done=False),
            ]

            # Mark task as done
            result = manager.mark_task_done("Task 1", "Completed successfully")
            assert result is True

            # Check task was marked done
            assert manager.items[0].done is True
            assert manager.items[0].comment == "Completed successfully"
            assert manager.items[1].done is False  # Other task unchanged


def test_mark_task_done_not_found():
    """Test mark_task_done when task not found"""
    from src.todo_manager import TodoManager, TodoItem

    with patch('src.todo_manager.TodoManager._find_todo_file', return_value=None), \
         patch('src.todo_manager.TodoManager._load_todos'), \
         patch('src.todo_manager.TodoManager._save_todos'):

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TodoManager(Path(temp_dir))

            manager.items = [TodoItem("Task 1")]

            # Try to mark non-existent task
            result = manager.mark_task_done("Non-existent task")
            assert result is False


def test_get_task_hierarchy():
    """Test get_task_hierarchy method"""
    from src.todo_manager import TodoManager, TodoItem

    with patch('src.todo_manager.TodoManager._find_todo_file', return_value=None), \
         patch('src.todo_manager.TodoManager._load_todos'):

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TodoManager(Path(temp_dir))

            # Set up hierarchical test items
            root1 = TodoItem("Root 1", level=0)
            child1 = TodoItem("Child 1", level=1)
            child2 = TodoItem("Child 2", level=1)
            root2 = TodoItem("Root 2", level=0)

            root1.children = [child1, child2]
            child1.parent = root1
            child2.parent = root1

            manager.items = [root1, child1, child2, root2]

            hierarchy = manager.get_task_hierarchy()

            # Check structure
            assert "total_tasks" in hierarchy
            assert "completed_tasks" in hierarchy
            assert "pending_tasks" in hierarchy
            assert "hierarchy" in hierarchy

            assert hierarchy["total_tasks"] == 4
            assert hierarchy["completed_tasks"] == 0  # All tasks are pending
            assert hierarchy["pending_tasks"] == 4


# Test loading methods
def test_load_from_text_basic():
    """Test _load_from_text with basic content"""
    from src.todo_manager import TodoManager

    with patch('src.todo_manager.TodoManager._find_todo_file', return_value=None), \
         patch('src.todo_manager.TodoManager._load_todos'):

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TodoManager(Path(temp_dir))

            # Create test file
            test_file = Path(temp_dir) / "todo.txt"
            test_file.write_text("Task 1\nTask 2\n# Comment\n\nTask 3")

            manager.todo_file = test_file
            manager._load_from_text()

            assert len(manager.items) == 3
            assert manager.items[0].text == "Task 1"
            assert manager.items[1].text == "Task 2"
            assert manager.items[2].text == "Task 3"


def test_load_from_text_with_levels():
    """Test _load_from_text with indentation levels"""
    from src.todo_manager import TodoManager

    with patch('src.todo_manager.TodoManager._find_todo_file', return_value=None), \
         patch('src.todo_manager.TodoManager._load_todos'):

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TodoManager(Path(temp_dir))

            # Create test file with indentation
            test_file = Path(temp_dir) / "todo.txt"
            test_file.write_text("Root task\n  Subtask 1\n  Subtask 2\nAnother root")

            manager.todo_file = test_file
            manager._load_from_text()

            assert len(manager.items) == 4
            assert manager.items[0].level == 0
            assert manager.items[1].level == 1
            assert manager.items[2].level == 1
            assert manager.items[3].level == 0


def test_load_from_markdown_checkboxes():
    """Test _load_from_markdown with checkboxes"""
    from src.todo_manager import TodoManager

    with patch('src.todo_manager.TodoManager._find_todo_file', return_value=None), \
         patch('src.todo_manager.TodoManager._load_todos'):

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TodoManager(Path(temp_dir))

            # Create test markdown file
            test_file = Path(temp_dir) / "todo.md"
            test_file.write_text("""
- [ ] Task 1
- [x] Completed task
- [ ] Task with comment <!-- This is a comment -->
  - [ ] Subtask
""")

            manager.todo_file = test_file
            manager._load_from_markdown()

            assert len(manager.items) == 4
            assert manager.items[0].text == "Task 1"
            assert manager.items[0].done is False
            assert manager.items[1].text == "Completed task"
            assert manager.items[1].done is True
            assert manager.items[2].comment == "This is a comment"
            assert manager.items[3].level == 1


def test_load_from_yaml():
    """Test _load_from_yaml method"""
    from src.todo_manager import TodoManager

    with patch('src.todo_manager.TodoManager._find_todo_file', return_value=None), \
         patch('src.todo_manager.TodoManager._load_todos'):

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TodoManager(Path(temp_dir))

            # Create test YAML file
            test_file = Path(temp_dir) / "todo.yaml"
            yaml_content = """
tasks:
  - text: "Task 1"
    done: false
  - text: "Task 2"
    done: true
    comment: "Completed"
  - text: "Task 3"
    level: 1
"""
            test_file.write_text(yaml_content)

            manager.todo_file = test_file
            manager._load_from_yaml()

            assert len(manager.items) == 3
            assert manager.items[0].text == "Task 1"
            assert manager.items[0].done is False
            assert manager.items[1].done is True
            assert manager.items[1].comment == "Completed"
            assert manager.items[2].level == 1