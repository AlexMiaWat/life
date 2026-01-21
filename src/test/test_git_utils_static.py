"""
Static tests for git_utils.py - basic functionality validation without external dependencies
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import subprocess
from src.git_utils import execute_git_command, get_current_branch, get_last_commit_info, GitError


# Test GitError exception
def test_git_error_exception():
    """Test GitError exception can be raised and caught"""
    with pytest.raises(GitError):
        raise GitError("Test error")


# Test execute_git_command function
def test_execute_git_command_success():
    """Test execute_git_command with successful command"""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "output"
    mock_result.stderr = ""

    with patch('subprocess.run', return_value=mock_result) as mock_run:
        success, stdout, stderr = execute_git_command(["git", "status"])

        assert success is True
        assert stdout == "output"
        assert stderr == ""

        mock_run.assert_called_once()


def test_execute_git_command_failure():
    """Test execute_git_command with failed command"""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "error message"

    with patch('subprocess.run', return_value=mock_result) as mock_run:
        success, stdout, stderr = execute_git_command(["git", "invalid"])

        assert success is False
        assert stdout == ""
        assert stderr == "error message"


def test_execute_git_command_timeout():
    """Test execute_git_command with timeout"""
    with patch('subprocess.run', side_effect=subprocess.TimeoutExpired("timeout", 30)) as mock_run:
        success, stdout, stderr = execute_git_command(["git", "slow-command"], timeout=30)

        assert success is False
        assert stdout == ""
        assert "Таймаут" in stderr


def test_execute_git_command_exception():
    """Test execute_git_command with general exception"""
    with patch('subprocess.run', side_effect=Exception("test error")) as mock_run:
        success, stdout, stderr = execute_git_command(["git", "command"])

        assert success is False
        assert stdout == ""
        assert stderr == "test error"


def test_execute_git_command_with_working_dir():
    """Test execute_git_command with working directory"""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "ok"
    mock_result.stderr = ""

    with patch('subprocess.run', return_value=mock_result) as mock_run:
        work_dir = Path("/tmp/test")
        success, stdout, stderr = execute_git_command(["git", "status"], working_dir=work_dir)

        assert success is True
        # Verify cwd parameter was passed
        call_args = mock_run.call_args
        assert call_args[1]['cwd'] == str(work_dir)


# Test get_current_branch function
def test_get_current_branch_success():
    """Test get_current_branch with successful execution"""
    with patch('src.git_utils.execute_git_command', return_value=(True, "main", "")):
        branch = get_current_branch()
        assert branch == "main"


def test_get_current_branch_failure():
    """Test get_current_branch with failed execution"""
    with patch('src.git_utils.execute_git_command', return_value=(False, "", "error")):
        branch = get_current_branch()
        assert branch is None


def test_get_current_branch_empty_output():
    """Test get_current_branch with empty output"""
    with patch('src.git_utils.execute_git_command', return_value=(True, "", "")):
        branch = get_current_branch()
        assert branch is None


# Test get_last_commit_info function
def test_get_last_commit_info_success():
    """Test get_last_commit_info with successful execution"""
    mock_responses = [
        (True, "abc123456789", ""),  # hash
        (True, "def123", ""),        # short hash
        (True, "Test commit", ""),   # subject
        (True, "Author Name", ""),   # author
        (True, "2023-01-01", ""),    # date
    ]

    with patch('src.git_utils.execute_git_command', side_effect=mock_responses):
        info = get_last_commit_info()

        assert info is not None
        assert info['hash'] == "abc123456789"
        assert info['short_hash'] == "def123"
        assert info['subject'] == "Test commit"
        assert info['author'] == "Author Name"
        assert info['date'] == "2023-01-01"


def test_get_last_commit_info_partial_failure():
    """Test get_last_commit_info with partial command failures"""
    mock_responses = [
        (False, "", "error"),  # hash fails
        (True, "def123", ""),  # short hash succeeds
        (True, "subject", ""), # subject succeeds
        (False, "", "error"),  # author fails
        (True, "date", ""),    # date succeeds
    ]

    with patch('src.git_utils.execute_git_command', side_effect=mock_responses):
        info = get_last_commit_info()

        assert info is None  # Should return None if critical info missing


def test_get_last_commit_info_all_success():
    """Test get_last_commit_info with all commands successful"""
    mock_responses = [
        (True, "full_hash_here", ""),
        (True, "short", ""),
        (True, "Commit subject", ""),
        (True, "Author Name", ""),
        (True, "2023-12-25", ""),
    ]

    with patch('src.git_utils.execute_git_command', side_effect=mock_responses):
        info = get_last_commit_info()

        expected = {
            'hash': 'full_hash_here',
            'short_hash': 'short',
            'subject': 'Commit subject',
            'author': 'Author Name',
            'date': '2023-12-25'
        }
        assert info == expected


# Test function signatures and imports
def test_module_functions_available():
    """Test that all expected functions are available"""
    import src.git_utils as git_utils_module

    # Test functions exist
    assert hasattr(git_utils_module, 'execute_git_command')
    assert hasattr(git_utils_module, 'get_current_branch')
    assert hasattr(git_utils_module, 'get_last_commit_info')
    assert hasattr(git_utils_module, 'GitError')

    # Test they are callable
    assert callable(git_utils_module.execute_git_command)
    assert callable(git_utils_module.get_current_branch)
    assert callable(git_utils_module.get_last_commit_info)


def test_function_signatures():
    """Test function signatures are correct"""
    import inspect

    # Test execute_git_command signature
    sig = inspect.signature(execute_git_command)
    expected_params = ['command', 'working_dir', 'timeout']
    assert list(sig.parameters.keys()) == expected_params

    # Test get_current_branch signature
    sig = inspect.signature(get_current_branch)
    expected_params = ['working_dir']
    assert list(sig.parameters.keys()) == expected_params

    # Test get_last_commit_info signature
    sig = inspect.signature(get_last_commit_info)
    expected_params = ['working_dir']
    assert list(sig.parameters.keys()) == expected_params