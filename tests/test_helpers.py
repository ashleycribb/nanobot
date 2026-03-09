import pytest
from pathlib import Path
from nanobot.utils.helpers import get_sessions_path

def test_get_sessions_path(tmp_path, monkeypatch):
    """Test get_sessions_path returns the correct path and ensures directory exists."""
    # Mock Path.home() to return the temporary directory
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    # Call the function
    sessions_path = get_sessions_path()

    # Expected path is ~/.nanobot/sessions, where ~ is tmp_path
    expected_path = tmp_path / ".nanobot" / "sessions"

    # Assert the returned path matches the expected path
    assert sessions_path == expected_path

    # Assert the directory was actually created
    assert sessions_path.exists()
    assert sessions_path.is_dir()
