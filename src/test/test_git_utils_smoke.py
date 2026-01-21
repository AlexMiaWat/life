"""
Smoke tests for git_utils.py - basic functionality validation with minimal external dependencies
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess
from src.git_utils import execute_git_command, get_current_branch, get_last_commit_info


class TestGitUtilsSmoke:
    """Smoke tests for git_utils functionality"""

    def test_execute_git_command_basic_call(self):
        """Smoke test: execute_git_command can be called"""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "success"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            success, stdout, stderr = execute_git_command(["git", "status"])

            assert isinstance(success, bool)
            assert isinstance(stdout, str)
            assert isinstance(stderr, str)

    def test_execute_git_command_error_handling(self):
        """Smoke test: execute_git_command handles errors gracefully"""
        with patch('subprocess.run', side_effect=Exception("test error")):
            success, stdout, stderr = execute_git_command(["git", "invalid"])

            assert success is False
            assert stdout == ""
            assert "test error" in stderr

    def test_get_current_branch_basic_call(self):
        """Smoke test: get_current_branch can be called"""
        with patch('src.git_utils.execute_git_command', return_value=(True, "main", "")):
            branch = get_current_branch()
            assert isinstance(branch, str) or branch is None

    def test_get_current_branch_with_working_dir(self):
        """Smoke test: get_current_branch with working directory"""
        with patch('src.git_utils.execute_git_command') as mock_exec:
            mock_exec.return_value = (True, "develop", "")

            work_dir = Path("/tmp/test")
            branch = get_current_branch(working_dir=work_dir)

            # Verify working directory was passed
            call_args = mock_exec.call_args
            assert call_args[0][1] == work_dir  # working_dir parameter

    def test_get_last_commit_info_basic_call(self):
        """Smoke test: get_last_commit_info can be called"""
        mock_responses = [
            (True, "hash123", ""),
            (True, "short", ""),
            (True, "subject", ""),
            (True, "author", ""),
            (True, "date", ""),
        ]

        with patch('src.git_utils.execute_git_command', side_effect=mock_responses):
            info = get_last_commit_info()
            assert isinstance(info, dict) or info is None

    def test_execute_git_command_timeout_handling(self):
        """Smoke test: timeout handling works"""
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired("timeout", 30)):
            success, stdout, stderr = execute_git_command(["git", "slow"], timeout=30)

            assert success is False
            assert "Таймаут" in stderr

    def test_execute_git_command_different_timeouts(self):
        """Smoke test: different timeout values work"""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "ok"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            # Test with default timeout
            execute_git_command(["git", "status"])

            # Test with custom timeout
            execute_git_command(["git", "log"], timeout=60)

            # Verify timeout parameter was passed
            calls = mock_run.call_args_list
            assert len(calls) == 2

    def test_get_current_branch_error_cases(self):
        """Smoke test: get_current_branch handles various error cases"""
        # Test command failure
        with patch('src.git_utils.execute_git_command', return_value=(False, "", "error")):
            branch = get_current_branch()
            assert branch is None

        # Test empty output
        with patch('src.git_utils.execute_git_command', return_value=(True, "", "")):
            branch = get_current_branch()
            assert branch is None

        # Test whitespace-only output
        with patch('src.git_utils.execute_git_command', return_value=(True, "   ", "")):
            branch = get_current_branch()
            assert branch == "   "  # Should return as-is

    def test_get_last_commit_info_error_cases(self):
        """Smoke test: get_last_commit_info handles error cases"""
        # Test complete failure
        with patch('src.git_utils.execute_git_command', return_value=(False, "", "error")):
            info = get_last_commit_info()
            assert info is None

        # Test partial success (missing critical info)
        mock_responses = [
            (False, "", "error"),  # hash fails
            (True, "short", ""),   # short hash succeeds
            (True, "subject", ""), # subject succeeds
            (True, "author", ""),  # author succeeds
            (True, "date", ""),    # date succeeds
        ]

        with patch('src.git_utils.execute_git_command', side_effect=mock_responses):
            info = get_last_commit_info()
            assert info is None  # Should fail due to missing hash

    def test_execute_git_command_output_processing(self):
        """Smoke test: output processing works correctly"""
        # Test with various output formats
        test_cases = [
            (0, "normal output", ""),
            (0, "", "normal stderr"),
            (0, "output with\nnewlines", "stderr with\nnewlines"),
            (1, "", "error message"),
            (0, "  spaced output  ", "  spaced stderr  "),
        ]

        for returncode, stdout, stderr in test_cases:
            with patch('subprocess.run') as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = returncode
                mock_result.stdout = stdout
                mock_result.stderr = stderr
                mock_run.return_value = mock_result

                success, out, err = execute_git_command(["git", "test"])

                expected_success = returncode == 0
                expected_out = stdout.strip() if stdout else ""
                expected_err = stderr.strip() if stderr else ""

                assert success == expected_success
                assert out == expected_out
                assert err == expected_err

    def test_functions_with_none_working_dir(self):
        """Smoke test: functions work with None working directory"""
        with patch('src.git_utils.execute_git_command') as mock_exec:
            mock_exec.return_value = (True, "main", "")

            # Should work with None
            branch = get_current_branch(working_dir=None)
            assert branch == "main"

            # Verify None was passed through
            call_args = mock_exec.call_args
            assert call_args[0][1] is None

    def test_get_last_commit_info_complete_success(self):
        """Smoke test: get_last_commit_info with complete successful response"""
        expected_info = {
            'hash': 'abc123def456',
            'short_hash': 'abc123d',
            'subject': 'Fix critical bug',
            'author': 'Developer Name',
            'date': '2023-01-15'
        }

        mock_responses = [
            (True, expected_info['hash'], ""),
            (True, expected_info['short_hash'], ""),
            (True, expected_info['subject'], ""),
            (True, expected_info['author'], ""),
            (True, expected_info['date'], ""),
        ]

        with patch('src.git_utils.execute_git_command', side_effect=mock_responses):
            info = get_last_commit_info()

            assert info is not None
            assert info == expected_info

    def test_module_error_handling_robustness(self):
        """Smoke test: module handles various error conditions robustly"""
        # Test that functions don't crash with unexpected inputs
        with patch('subprocess.run', side_effect=OSError("System error")):
            success, stdout, stderr = execute_git_command(["git", "status"])
            assert success is False
            assert "System error" in stderr

        # Test with non-list command (should still work as subprocess handles it)
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "ok"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            # This should work even with unexpected command format
            success, stdout, stderr = execute_git_command("git status")  # String instead of list
            assert success is True

    def test_functions_return_types_consistency(self):
        """Smoke test: functions return consistent types"""
        # execute_git_command always returns (bool, str, str)
        with patch('subprocess.run', side_effect=Exception("error")):
            result = execute_git_command(["git", "fail"])
            assert isinstance(result, tuple)
            assert len(result) == 3
            assert isinstance(result[0], bool)
            assert isinstance(result[1], str)
            assert isinstance(result[2], str)

        # get_current_branch returns str or None
        with patch('src.git_utils.execute_git_command', return_value=(True, "branch", "")):
            result = get_current_branch()
            assert isinstance(result, str) or result is None

        # get_last_commit_info returns dict or None
        with patch('src.git_utils.execute_git_command', return_value=(False, "", "error")):
            result = get_last_commit_info()
            assert isinstance(result, dict) or result is None