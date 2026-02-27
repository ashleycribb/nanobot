from pathlib import Path
from nanobot.utils.helpers import get_workspace_path

def test_get_workspace_path_default(monkeypatch, tmp_path):
    """Test get_workspace_path with default arguments (uses home dir)."""
    # Mock Path.home() to return tmp_path
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    expected_path = tmp_path / ".nanobot" / "workspace"
    assert not expected_path.exists()

    result = get_workspace_path()

    assert result == expected_path
    assert result.exists()
    assert result.is_dir()

def test_get_workspace_path_custom(tmp_path):
    """Test get_workspace_path with a custom path."""
    custom_ws = tmp_path / "custom_workspace"
    assert not custom_ws.exists()

    result = get_workspace_path(str(custom_ws))

    assert result == custom_ws
    assert result.exists()
    assert result.is_dir()
