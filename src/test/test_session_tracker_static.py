"""
Static tests for session_tracker.py - basic functionality validation
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import json
from datetime import datetime
from src.session_tracker import SessionTracker


def test_session_tracker_init():
    """Test SessionTracker initialization"""
    with patch('src.session_tracker.SessionTracker._load_session_data') as mock_load:
        mock_load.return_value = {}

        with patch('pathlib.Path.exists', return_value=False):
            with patch('builtins.open', mock_open()):
                tracker = SessionTracker(Path("/tmp/test"))

                assert tracker.project_dir == Path("/tmp/test")
                assert tracker.tracker_file.name == ".codeagent_sessions.json"
                assert tracker.backup_file.name == ".codeagent_sessions.json.backup"


def test_generate_session_id():
    """Test _generate_session_id method"""
    with patch('src.session_tracker.SessionTracker._load_session_data') as mock_load:
        mock_load.return_value = {}

        with patch('pathlib.Path.exists', return_value=False):
            tracker = SessionTracker(Path("/tmp/test"))

            session_id = tracker._generate_session_id()

            # Should be in YYYYMMDD_HHMMSS format
            assert len(session_id) == 15  # YYYYMMDD_HHMMSS = 8 + 1 + 6 = 15
            assert session_id[8] == '_'  # Separator

            # Should be parseable as datetime components
            date_part, time_part = session_id.split('_')
            assert len(date_part) == 8
            assert len(time_part) == 6


def test_load_session_data_new_file():
    """Test _load_session_data with new file"""
    with patch('src.session_tracker.SessionTracker._load_session_data') as mock_load:
        mock_load.return_value = {}

        with patch('pathlib.Path.exists', return_value=False):
            tracker = SessionTracker(Path("/tmp/test"))

            data = tracker._load_session_data()

            # Should return default structure
            assert "sessions" in data
            assert "current_session" in data
            assert "last_update" in data
            assert isinstance(data["sessions"], dict)


def test_load_session_data_existing_file():
    """Test _load_session_data with existing file"""
    test_data = {
        "sessions": {"session1": {"start_time": "2023-01-01"}},
        "current_session": "session1",
        "last_update": "2023-01-01T10:00:00"
    }

    with patch('src.session_tracker.SessionTracker._load_session_data') as mock_load:
        mock_load.return_value = {}

        with patch('builtins.open', mock_open(read_data=json.dumps(test_data))):
            with patch('pathlib.Path.exists', return_value=True):
                tracker = SessionTracker(Path("/tmp/test"))

                data = tracker._load_session_data()
                assert data == test_data


def test_load_session_data_corrupted_file():
    """Test _load_session_data with corrupted JSON"""
    with patch('src.session_tracker.SessionTracker._load_session_data') as mock_load:
        mock_load.return_value = {}

        with patch('builtins.open', mock_open(read_data="invalid json")):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('json.load', side_effect=json.JSONDecodeError("error", "doc", 0)):
                    tracker = SessionTracker(Path("/tmp/test"))

                    data = tracker._load_session_data()

                    # Should return default data
                    assert "sessions" in data
                    assert "current_session" in data


def test_save_session_data():
    """Test _save_session_data method"""
    with patch('src.session_tracker.SessionTracker._load_session_data') as mock_load, \
         patch('pathlib.Path.mkdir'), \
         patch('builtins.open', mock_open()) as mock_file, \
         patch('json.dump') as mock_json_dump:

        mock_load.return_value = {}

        with patch('pathlib.Path.exists', return_value=False):
            tracker = SessionTracker(Path("/tmp/test"))

            tracker._save_session_data()

            # Should update last_update timestamp
            assert "last_update" in tracker.session_data

            # Should call json.dump
            mock_json_dump.assert_called_once()


def test_start_session():
    """Test start_session method"""
    with patch('src.session_tracker.SessionTracker._load_session_data') as mock_load, \
         patch('src.session_tracker.SessionTracker._save_session_data') as mock_save:

        mock_load.return_value = {}

        with patch('pathlib.Path.exists', return_value=False):
            tracker = SessionTracker(Path("/tmp/test"))

            session_id = "test_session_123"
            tracker.start_session(session_id, {"type": "test"})

            # Should set current session
            assert tracker.session_data["current_session"] == session_id

            # Should add session to sessions dict
            assert session_id in tracker.session_data["sessions"]
            session_data = tracker.session_data["sessions"][session_id]
            assert session_data["metadata"] == {"type": "test"}
            assert "start_time" in session_data

            mock_save.assert_called_once()


def test_end_session():
    """Test end_session method"""
    with patch('src.session_tracker.SessionTracker._load_session_data') as mock_load, \
         patch('src.session_tracker.SessionTracker._save_session_data') as mock_save:

        mock_load.return_value = {}

        with patch('pathlib.Path.exists', return_value=False):
            tracker = SessionTracker(Path("/tmp/test"))

            # Start a session first
            session_id = "test_session_123"
            tracker.start_session(session_id)

            # End the session
            tracker.end_session({"result": "success"})

            # Should add end_time and result to session
            session_data = tracker.session_data["sessions"][session_id]
            assert "end_time" in session_data
            assert session_data["result"] == {"result": "success"}

            mock_save.assert_called_once()


def test_end_session_no_current():
    """Test end_session when no current session"""
    with patch('src.session_tracker.SessionTracker._load_session_data') as mock_load, \
         patch('src.session_tracker.SessionTracker._save_session_data') as mock_save:

        mock_load.return_value = {}

        with patch('pathlib.Path.exists', return_value=False):
            tracker = SessionTracker(Path("/tmp/test"))

            # Try to end session without starting one
            tracker.end_session()

            # Should not crash, but also shouldn't save
            mock_save.assert_not_called()


def test_get_current_session():
    """Test get_current_session method"""
    with patch('src.session_tracker.SessionTracker._load_session_data') as mock_load:
        mock_load.return_value = {}

        with patch('pathlib.Path.exists', return_value=False):
            tracker = SessionTracker(Path("/tmp/test"))

            # No current session
            assert tracker.get_current_session() is None

            # Start a session
            session_id = "test_session"
            tracker.start_session(session_id, {"type": "test"})

            # Should return current session data
            current = tracker.get_current_session()
            assert current is not None
            assert current["session_id"] == session_id
            assert current["metadata"] == {"type": "test"}


def test_get_session_history():
    """Test get_session_history method"""
    with patch('src.session_tracker.SessionTracker._load_session_data') as mock_load:
        mock_load.return_value = {}

        with patch('pathlib.Path.exists', return_value=False):
            tracker = SessionTracker(Path("/tmp/test"))

            # Add some sessions
            tracker.start_session("session1", {"type": "test1"})
            tracker.end_session({"result": "success1"})

            tracker.start_session("session2", {"type": "test2"})
            tracker.end_session({"result": "success2"})

            history = tracker.get_session_history()

            assert len(history) == 2
            assert "session1" in history
            assert "session2" in history
            assert history["session1"]["metadata"]["type"] == "test1"
            assert history["session2"]["result"]["result"] == "success2"


def test_get_session_stats():
    """Test get_session_stats method"""
    with patch('src.session_tracker.SessionTracker._load_session_data') as mock_load:
        mock_load.return_value = {}

        with patch('pathlib.Path.exists', return_value=False):
            tracker = SessionTracker(Path("/tmp/test"))

            # Add sessions with different results
            tracker.start_session("success_session", {"type": "success"})
            tracker.end_session({"success": True})

            tracker.start_session("failure_session", {"type": "failure"})
            tracker.end_session({"success": False})

            tracker.start_session("running_session", {"type": "running"})
            # Don't end this one

            stats = tracker.get_session_stats()

            assert stats["total_sessions"] == 3
            assert stats["completed_sessions"] == 2
            assert stats["running_sessions"] == 1
            assert stats["success_rate"] == 0.5  # 1 success out of 2 completed


def test_cleanup_old_sessions():
    """Test cleanup_old_sessions method"""
    with patch('src.session_tracker.SessionTracker._load_session_data') as mock_load, \
         patch('src.session_tracker.SessionTracker._save_session_data') as mock_save:

        mock_load.return_value = {}

        with patch('pathlib.Path.exists', return_value=False):
            tracker = SessionTracker(Path("/tmp/test"))

            # Add many sessions (simulate old sessions)
            for i in range(150):
                session_id = f"old_session_{i}"
                tracker.session_data["sessions"][session_id] = {
                    "start_time": "2023-01-01T00:00:00",
                    "metadata": {"type": "old"}
                }

            # Add a recent session
            tracker.session_data["sessions"]["recent_session"] = {
                "start_time": datetime.now().isoformat(),
                "metadata": {"type": "recent"}
            }

            # Cleanup keeping only 10
            tracker.cleanup_old_sessions(keep_last_n=10)

            sessions = tracker.session_data["sessions"]
            assert len(sessions) == 10
            # Should keep the most recent ones
            assert "recent_session" in sessions

            mock_save.assert_called_once()


def test_is_session_active():
    """Test is_session_active method"""
    with patch('src.session_tracker.SessionTracker._load_session_data') as mock_load:
        mock_load.return_value = {}

        with patch('pathlib.Path.exists', return_value=False):
            tracker = SessionTracker(Path("/tmp/test"))

            # No active session
            assert tracker.is_session_active() is False

            # Start a session
            tracker.start_session("active_session")

            # Should be active
            assert tracker.is_session_active() is True

            # End the session
            tracker.end_session()

            # Should not be active
            assert tracker.is_session_active() is False


def test_get_active_session_duration():
    """Test get_active_session_duration method"""
    with patch('src.session_tracker.SessionTracker._load_session_data') as mock_load:
        mock_load.return_value = {}

        with patch('pathlib.Path.exists', return_value=False):
            tracker = SessionTracker(Path("/tmp/test"))

            # No active session
            duration = tracker.get_active_session_duration()
            assert duration == 0.0

            # Start a session
            tracker.start_session("duration_test")

            # Should return some duration (> 0)
            duration = tracker.get_active_session_duration()
            assert duration >= 0.0


def test_session_data_integrity():
    """Test that session data maintains integrity across operations"""
    with patch('src.session_tracker.SessionTracker._load_session_data') as mock_load, \
         patch('src.session_tracker.SessionTracker._save_session_data') as mock_save:

        mock_load.return_value = {}

        with patch('pathlib.Path.exists', return_value=False):
            tracker = SessionTracker(Path("/tmp/test"))

            # Perform various operations
            tracker.start_session("integrity_test", {"test": "data"})
            tracker.end_session({"result": "ok"})

            # Check data structure integrity
            sessions = tracker.session_data["sessions"]
            assert "integrity_test" in sessions

            session = sessions["integrity_test"]
            required_fields = ["start_time", "end_time", "metadata", "result"]
            for field in required_fields:
                assert field in session

            assert session["metadata"] == {"test": "data"}
            assert session["result"] == {"result": "ok"}