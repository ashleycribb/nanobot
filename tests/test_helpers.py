import pytest
from pathlib import Path
from nanobot.utils.helpers import get_workspace_path

def test_get_workspace_path_default(monkeypatch, tmp_path):
    """Test get_workspace_path with no arguments uses default path."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    expected_path = tmp_path / ".nanobot" / "workspace"

    # Ensure it doesn't exist before
    assert not expected_path.exists()

    result = get_workspace_path()

    assert result == expected_path
    assert result.exists()
    assert result.is_dir()

def test_get_workspace_path_custom_absolute(tmp_path):
    """Test get_workspace_path with a custom absolute path."""
    custom_path = tmp_path / "custom" / "workspace"

    # Ensure it doesn't exist before
    assert not custom_path.exists()

    result = get_workspace_path(str(custom_path))

    assert result == custom_path
    assert result.exists()
    assert result.is_dir()

def test_get_workspace_path_custom_with_tilde(monkeypatch, tmp_path):
    """Test get_workspace_path with a tilde path."""
    # expanduser uses HOME environment variable
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))

    # Also patch Path.home() just in case
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    expected_path = tmp_path / "custom_tilde_workspace"

    assert not expected_path.exists()

    result = get_workspace_path("~/custom_tilde_workspace")

    assert result == expected_path
    assert result.exists()
    assert result.is_dir()