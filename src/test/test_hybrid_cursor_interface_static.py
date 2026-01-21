"""
Static tests for hybrid_cursor_interface.py - basic functionality validation
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.hybrid_cursor_interface import (
    HybridCursorInterface, TaskComplexity, HybridExecutionResult
)


def test_task_complexity_enum():
    """Test TaskComplexity enum values"""
    assert TaskComplexity.SIMPLE.value == "simple"
    assert TaskComplexity.COMPLEX.value == "complex"
    assert TaskComplexity.AUTO.value == "auto"


def test_hybrid_execution_result_dataclass():
    """Test HybridExecutionResult dataclass"""
    result = HybridExecutionResult(
        success=True,
        method_used="cli",
        output="test output"
    )

    assert result.success is True
    assert result.method_used == "cli"
    assert result.output == "test output"
    assert result.error_message is None
    assert result.side_effects_verified is False


def test_hybrid_cursor_interface_constants():
    """Test HybridCursorInterface class constants"""
    assert hasattr(HybridCursorInterface, 'SIMPLE_KEYWORDS')
    assert hasattr(HybridCursorInterface, 'COMPLEX_KEYWORDS')

    assert isinstance(HybridCursorInterface.SIMPLE_KEYWORDS, list)
    assert isinstance(HybridCursorInterface.COMPLEX_KEYWORDS, list)

    assert len(HybridCursorInterface.SIMPLE_KEYWORDS) > 0
    assert len(HybridCursorInterface.COMPLEX_KEYWORDS) > 0


@patch('src.hybrid_cursor_interface.CursorCLIInterface')
@patch('src.hybrid_cursor_interface.CursorFileInterface')
def test_hybrid_cursor_interface_init(mock_file_interface, mock_cli_interface):
    """Test HybridCursorInterface initialization"""
    mock_cli = MagicMock()
    mock_file = MagicMock()
    mock_cli_interface.return_value = mock_cli
    mock_file_interface.return_value = mock_file

    interface = HybridCursorInterface()

    assert interface.cli_interface == mock_cli
    assert interface.file_interface == mock_file
    assert interface.prefer_cli is False
    assert interface.verify_side_effects is True


@patch('src.hybrid_cursor_interface.HybridCursorInterface._determine_complexity')
def test_execute_task_complexity_detection():
    """Test execute_task complexity detection"""
    with patch('src.hybrid_cursor_interface.CursorCLIInterface') as mock_cli_class, \
         patch('src.hybrid_cursor_interface.CursorFileInterface') as mock_file_class:

        mock_cli = MagicMock()
        mock_file = MagicMock()
        mock_cli_class.return_value = mock_cli
        mock_file_class.return_value = mock_file

        interface = HybridCursorInterface()

        # Mock complexity determination
        interface._determine_complexity.return_value = TaskComplexity.SIMPLE

        # Mock CLI execution success
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.output = "success"
        mock_cli.execute_instruction.return_value = mock_result

        result = interface.execute_task("test task")

        assert result.success is True
        interface._determine_complexity.assert_called_once_with("test task")


def test_determine_complexity_simple_keywords():
    """Test _determine_complexity with simple keywords"""
    with patch('src.hybrid_cursor_interface.CursorCLIInterface'), \
         patch('src.hybrid_cursor_interface.CursorFileInterface'):

        interface = HybridCursorInterface()

        # Test simple keywords
        for keyword in ['что', 'how', 'explain', 'find']:
            task = f"{keyword} something"
            complexity = interface._determine_complexity(task)
            assert complexity == TaskComplexity.SIMPLE


def test_determine_complexity_complex_keywords():
    """Test _determine_complexity with complex keywords"""
    with patch('src.hybrid_cursor_interface.CursorCLIInterface'), \
         patch('src.hybrid_cursor_interface.CursorFileInterface'):

        interface = HybridCursorInterface()

        # Test complex keywords
        for keyword in ['создай', 'create', 'modify', 'fix']:
            task = f"{keyword} something"
            complexity = interface._determine_complexity(task)
            assert complexity == TaskComplexity.COMPLEX


def test_determine_complexity_auto_mode():
    """Test _determine_complexity with AUTO mode"""
    with patch('src.hybrid_cursor_interface.CursorCLIInterface'), \
         patch('src.hybrid_cursor_interface.CursorFileInterface'):

        interface = HybridCursorInterface()

        # Test ambiguous task (no clear keywords)
        task = "do something unclear"
        complexity = interface._determine_complexity(task)
        # Should default to COMPLEX for safety
        assert complexity == TaskComplexity.COMPLEX


@patch('src.hybrid_cursor_interface.HybridCursorInterface._execute_via_cli')
@patch('src.hybrid_cursor_interface.HybridCursorInterface._execute_via_file')
def test_execute_simple_task(mock_file_exec, mock_cli_exec):
    """Test _execute_simple_task method"""
    with patch('src.hybrid_cursor_interface.CursorCLIInterface'), \
         patch('src.hybrid_cursor_interface.CursorFileInterface'):

        interface = HybridCursorInterface()

        mock_cli_exec.return_value = HybridExecutionResult(
            success=True, method_used="cli", output="cli result"
        )

        result = interface._execute_simple_task("simple task")

        assert result.success is True
        assert result.method_used == "cli"
        mock_cli_exec.assert_called_once_with("simple task")


@patch('src.hybrid_cursor_interface.HybridCursorInterface._execute_via_cli')
@patch('src.hybrid_cursor_interface.HybridCursorInterface._execute_via_file')
def test_execute_complex_task(mock_file_exec, mock_cli_exec):
    """Test _execute_complex_task method"""
    with patch('src.hybrid_cursor_interface.CursorCLIInterface'), \
         patch('src.hybrid_cursor_interface.CursorFileInterface'):

        interface = HybridCursorInterface()

        mock_file_exec.return_value = HybridExecutionResult(
            success=True, method_used="file", output="file result"
        )

        result = interface._execute_complex_task("complex task")

        assert result.success is True
        assert result.method_used == "file"
        mock_file_exec.assert_called_once_with("complex task")


def test_execute_via_cli_success():
    """Test _execute_via_cli with success"""
    with patch('src.hybrid_cursor_interface.CursorCLIInterface') as mock_cli_class:

        mock_cli = MagicMock()
        mock_cli_class.return_value = mock_cli

        interface = HybridCursorInterface(cli_interface=mock_cli)

        # Mock successful CLI execution
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.output = "success"
        mock_cli.execute_instruction.return_value = mock_result

        result = interface._execute_via_cli("test task")

        assert result.success is True
        assert result.method_used == "cli"
        assert result.cli_result == mock_result


def test_execute_via_cli_failure():
    """Test _execute_via_cli with failure"""
    with patch('src.hybrid_cursor_interface.CursorCLIInterface') as mock_cli_class:

        mock_cli = MagicMock()
        mock_cli_class.return_value = mock_cli

        interface = HybridCursorInterface(cli_interface=mock_cli)

        # Mock failed CLI execution
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.output = ""
        mock_result.error_message = "CLI failed"
        mock_cli.execute_instruction.return_value = mock_result

        result = interface._execute_via_cli("test task")

        assert result.success is False
        assert result.method_used == "cli"
        assert result.error_message == "CLI failed"


def test_execute_via_file_success():
    """Test _execute_via_file with success"""
    with patch('src.hybrid_cursor_interface.CursorFileInterface') as mock_file_class:

        mock_file = MagicMock()
        mock_file_class.return_value = mock_file

        interface = HybridCursorInterface(file_interface=mock_file)

        # Mock successful file execution
        mock_result = {"success": True, "output": "file success"}
        mock_file.execute_instruction.return_value = mock_result

        result = interface._execute_via_file("test task")

        assert result.success is True
        assert result.method_used == "file"
        assert result.file_result == mock_result


def test_execute_via_file_failure():
    """Test _execute_via_file with failure"""
    with patch('src.hybrid_cursor_interface.CursorFileInterface') as mock_file_class:

        mock_file = MagicMock()
        mock_file_class.return_value = mock_file

        interface = HybridCursorInterface(file_interface=mock_file)

        # Mock failed file execution
        mock_result = {"success": False, "error": "file failed"}
        mock_file.execute_instruction.return_value = mock_result

        result = interface._execute_via_file("test task")

        assert result.success is False
        assert result.method_used == "file"
        assert "file failed" in result.error_message


def test_prefer_cli_mode():
    """Test prefer_cli mode functionality"""
    with patch('src.hybrid_cursor_interface.CursorCLIInterface') as mock_cli_class, \
         patch('src.hybrid_cursor_interface.CursorFileInterface') as mock_file_class:

        mock_cli = MagicMock()
        mock_file = MagicMock()
        mock_cli_class.return_value = mock_cli
        mock_file_class.return_value = mock_file

        interface = HybridCursorInterface(prefer_cli=True)

        # Mock CLI failure then file success
        mock_cli_result = MagicMock()
        mock_cli_result.success = False
        mock_cli.execute_instruction.return_value = mock_cli_result

        mock_file_result = {"success": True, "output": "fallback success"}
        mock_file.execute_instruction.return_value = mock_file_result

        result = interface._execute_complex_task("complex task")

        # Should try CLI first, then fallback to file
        assert result.success is True
        assert result.method_used == "cli_with_fallback"
        mock_cli.execute_instruction.assert_called_once()
        mock_file.execute_instruction.assert_called_once()


def test_module_imports():
    """Test that module imports work correctly"""
    # Should be able to import all required classes
    from src.hybrid_cursor_interface import (
        HybridCursorInterface, TaskComplexity, HybridExecutionResult
    )

    assert HybridCursorInterface is not None
    assert TaskComplexity is not None
    assert HybridExecutionResult is not None