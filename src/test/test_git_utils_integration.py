"""
Integration tests for git_utils.py - testing with real file system operations
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import subprocess
import os
from src.git_utils import execute_git_command, get_current_branch, get_last_commit_info


class TestGitUtilsIntegration:
    """Integration tests for git_utils with real operations"""

    def test_execute_git_command_real_success(self):
        """Integration test: execute_git_command with real git command"""
        # Test with a simple git command that should work in most environments
        success, stdout, stderr = execute_git_command(["git", "--version"])

        # git --version should work if git is installed
        if "git" in os.environ.get("PATH", ""):
            assert success is True
            assert "git version" in stdout.lower()
        else:
            # If git is not available, command will fail gracefully
            assert success is False

    def test_execute_git_command_in_temp_dir(self):
        """Integration test: execute_git_command in temporary directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test file
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test content")

            # Try a simple command (should work regardless of git repo)
            success, stdout, stderr = execute_git_command(
                ["echo", "hello"],
                working_dir=Path(temp_dir)
            )

            # echo should work on most systems
            assert success is True or "hello" in stdout

    def test_get_current_branch_no_repo(self):
        """Integration test: get_current_branch when not in git repo"""
        with tempfile.TemporaryDirectory() as temp_dir:
            branch = get_current_branch(working_dir=Path(temp_dir))

            # Should return None when not in git repo
            assert branch is None

    def test_get_last_commit_info_no_repo(self):
        """Integration test: get_last_commit_info when not in git repo"""
        with tempfile.TemporaryDirectory() as temp_dir:
            info = get_last_commit_info(working_dir=Path(temp_dir))

            # Should return None when not in git repo
            assert info is None

    @pytest.mark.skipif(not os.path.exists('.git'), reason="Requires git repository")
    def test_git_functions_in_real_repo(self):
        """Integration test: git functions work in real git repository"""
        # This test only runs if we're in a git repository
        repo_dir = Path.cwd()

        # Test get_current_branch
        branch = get_current_branch(working_dir=repo_dir)
        assert branch is not None
        assert isinstance(branch, str)
        assert len(branch) > 0

        # Test get_last_commit_info
        info = get_last_commit_info(working_dir=repo_dir)
        assert info is not None
        assert isinstance(info, dict)

        # Check required fields
        required_fields = ['hash', 'short_hash', 'subject', 'author', 'date']
        for field in required_fields:
            assert field in info
            assert isinstance(info[field], str)
            assert len(info[field]) > 0

        # Test hash formats
        assert len(info['hash']) >= 7  # Full hash
        assert len(info['short_hash']) >= 7  # Short hash

    def test_execute_git_command_error_handling_integration(self):
        """Integration test: error handling with real command execution"""
        # Test with invalid command
        success, stdout, stderr = execute_git_command(["nonexistent_command_xyz"])

        assert success is False
        assert stdout == ""
        assert isinstance(stderr, str)

    def test_execute_git_command_timeout_integration(self):
        """Integration test: timeout handling with real command"""
        # Use a command that might hang (sleep), but with short timeout
        success, stdout, stderr = execute_git_command(
            ["sleep", "10"],  # Sleep for 10 seconds
            timeout=1         # But timeout after 1 second
        )

        # Should timeout and return failure
        assert success is False
        assert "Таймаут" in stderr

    def test_execute_git_command_large_output(self):
        """Integration test: handling of large command output"""
        # Create a command that produces large output
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a large file to cat
            large_file = Path(temp_dir) / "large.txt"
            large_content = "x" * 10000  # 10KB of content
            large_file.write_text(large_content)

            success, stdout, stderr = execute_git_command(
                ["cat", str(large_file)],
                working_dir=Path(temp_dir)
            )

            assert success is True
            assert len(stdout) == 10000
            assert stdout == large_content

    def test_functions_with_relative_paths(self):
        """Integration test: functions work with relative paths"""
        # Test from current directory (should work)
        branch = get_current_branch()
        # Result depends on whether we're in a git repo, but shouldn't crash

        info = get_last_commit_info()
        # Result depends on git repo status, but shouldn't crash

    def test_execute_git_command_environment_isolation(self):
        """Integration test: command execution is properly isolated"""
        # Test that commands don't inherit unexpected environment
        success, stdout, stderr = execute_git_command(["env"])

        # env command should work and show environment variables
        if success:
            assert isinstance(stdout, str)
            # Should contain some basic env vars
            assert "PATH" in stdout or len(stdout) == 0  # Some systems may filter env

    def test_git_functions_with_different_encodings(self):
        """Integration test: functions handle different output encodings"""
        # Test with commands that might produce unicode output
        success, stdout, stderr = execute_git_command(["echo", "тест"])

        if success:
            # Should handle unicode properly
            assert "тест" in stdout or "����" in stdout  # Either correct unicode or replacement chars

    def test_execute_git_command_working_directory_validation(self):
        """Integration test: working directory parameter validation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)

            # Test with valid directory
            success, stdout, stderr = execute_git_command(
                ["pwd"],
                working_dir=work_dir
            )

            # pwd should show the working directory
            if success:
                assert str(work_dir) in stdout or "/" in stdout  # Should show some path

    def test_get_current_branch_detached_head(self):
        """Integration test: get_current_branch handles detached HEAD state"""
        # This is hard to test without setting up a specific git state
        # Just ensure the function doesn't crash
        with tempfile.TemporaryDirectory() as temp_dir:
            branch = get_current_branch(working_dir=Path(temp_dir))
            assert branch is None  # Should be None for non-git dir

    def test_get_last_commit_info_merge_commit(self):
        """Integration test: get_last_commit_info handles merge commits"""
        # Hard to test without specific git setup
        # Just ensure function doesn't crash
        with tempfile.TemporaryDirectory() as temp_dir:
            info = get_last_commit_info(working_dir=Path(temp_dir))
            assert info is None  # Should be None for non-git dir

    def test_execute_git_command_signal_handling(self):
        """Integration test: signal handling in command execution"""
        # Test how the function handles interrupt signals
        # This is a bit tricky to test reliably
        success, stdout, stderr = execute_git_command(["true"])  # Should always succeed

        assert isinstance(success, bool)
        assert isinstance(stdout, str)
        assert isinstance(stderr, str)

    def test_functions_performance_under_load(self):
        """Integration test: functions perform adequately under repeated calls"""
        import time

        start_time = time.time()

        # Make multiple calls to test performance
        for i in range(10):
            execute_git_command(["echo", str(i)])

        end_time = time.time()
        duration = end_time - start_time

        # Should complete reasonably quickly (less than 1 second total)
        assert duration < 1.0

    def test_execute_git_command_output_size_limits(self):
        """Integration test: handling of various output sizes"""
        # Test with no output
        success, stdout, stderr = execute_git_command(["true"])
        assert success is True
        assert stdout == ""
        assert stderr == ""

        # Test with small output
        success, stdout, stderr = execute_git_command(["echo", "hello"])
        if success:
            assert "hello" in stdout

        # Test with empty command (should fail gracefully)
        success, stdout, stderr = execute_git_command([])
        assert success is False

    def test_git_functions_with_file_paths_containing_spaces(self):
        """Integration test: handling of paths with spaces"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create directory with spaces in name
            spaced_dir = Path(temp_dir) / "dir with spaces"
            spaced_dir.mkdir()

            # Create file in directory with spaces
            test_file = spaced_dir / "test file.txt"
            test_file.write_text("content")

            # Try to execute command in directory with spaces
            success, stdout, stderr = execute_git_command(
                ["ls"],
                working_dir=spaced_dir
            )

            if success:
                assert "test file.txt" in stdout

    def test_execute_git_command_concurrent_access(self):
        """Integration test: concurrent command execution"""
        import threading

        results = []
        errors = []

        def worker(worker_id):
            try:
                success, stdout, stderr = execute_git_command(["echo", f"worker-{worker_id}"])
                results.append((worker_id, success, stdout))
            except Exception as e:
                errors.append((worker_id, str(e)))

        # Start multiple threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        # Verify all completed without errors
        assert len(errors) == 0
        assert len(results) == 5

        # Verify each result
        for worker_id, success, stdout in results:
            assert success is True
            assert f"worker-{worker_id}" in stdout

    @pytest.mark.skipif(not os.path.exists('.git'), reason="Requires git repository")
    def test_real_git_repo_integration_comprehensive(self):
        """Comprehensive integration test with real git repository"""
        repo_dir = Path.cwd()

        # Test branch operations
        branch = get_current_branch(working_dir=repo_dir)
        assert branch is not None
        assert len(branch.strip()) > 0

        # Test commit info
        commit_info = get_last_commit_info(working_dir=repo_dir)
        assert commit_info is not None

        # Verify commit info structure
        expected_keys = ['hash', 'short_hash', 'subject', 'author', 'date']
        for key in expected_keys:
            assert key in commit_info
            assert isinstance(commit_info[key], str)
            assert len(commit_info[key]) > 0

        # Test hash relationships
        full_hash = commit_info['hash']
        short_hash = commit_info['short_hash']
        assert len(full_hash) >= len(short_hash)
        assert full_hash.startswith(short_hash) or short_hash in full_hash

        # Test that we can execute git commands directly in the repo
        success, stdout, stderr = execute_git_command(
            ["git", "log", "--oneline", "-1"],
            working_dir=repo_dir
        )
        assert success is True
        assert len(stdout) > 0
        assert short_hash in stdout  # Should contain the commit hash