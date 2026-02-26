import pytest
from pathlib import Path
from datetime import datetime
from nanobot.utils.helpers import (
    ensure_dir,
    get_data_path,
    get_workspace_path,
    get_sessions_path,
    get_skills_path,
    timestamp,
    truncate_string,
    safe_filename,
    parse_session_key,
)

def test_ensure_dir_creates_dir(tmp_path):
    """Test that ensure_dir creates a directory that does not exist."""
    d = tmp_path / "new_dir"
    assert not d.exists()
    result = ensure_dir(d)
    assert d.exists()
    assert d.is_dir()
    assert result == d

def test_ensure_dir_creates_parents(tmp_path):
    """Test that ensure_dir creates parent directories if necessary."""
    d = tmp_path / "parent" / "child" / "grandchild"
    assert not d.parent.exists()
    result = ensure_dir(d)
    assert d.exists()
    assert d.is_dir()
    assert result == d

def test_ensure_dir_existing_dir(tmp_path):
    """Test that ensure_dir does not fail if the directory already exists."""
    d = tmp_path / "existing_dir"
    d.mkdir()
    assert d.exists()
    result = ensure_dir(d)
    assert d.exists()
    assert d.is_dir()
    assert result == d

def test_get_data_path(tmp_path, monkeypatch):
    """Test get_data_path returns and ensures ~/.nanobot."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    expected = tmp_path / ".nanobot"
    assert not expected.exists()
    result = get_data_path()
    assert result == expected
    assert expected.exists()
    assert expected.is_dir()

def test_get_workspace_path_default(tmp_path, monkeypatch):
    """Test get_workspace_path with default path."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    expected = tmp_path / ".nanobot" / "workspace"
    assert not expected.exists()
    result = get_workspace_path()
    assert result == expected
    assert expected.exists()

def test_get_workspace_path_custom(tmp_path):
    """Test get_workspace_path with custom path."""
    custom_path = tmp_path / "my_workspace"
    result = get_workspace_path(str(custom_path))
    assert result == custom_path
    assert custom_path.exists()

def test_get_sessions_path(tmp_path, monkeypatch):
    """Test get_sessions_path."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    expected = tmp_path / ".nanobot" / "sessions"
    result = get_sessions_path()
    assert result == expected
    assert expected.exists()

def test_get_skills_path_default(tmp_path, monkeypatch):
    """Test get_skills_path with default workspace."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    expected = tmp_path / ".nanobot" / "workspace" / "skills"
    result = get_skills_path()
    assert result == expected
    assert expected.exists()

def test_get_skills_path_custom(tmp_path):
    """Test get_skills_path with custom workspace."""
    ws = tmp_path / "ws"
    expected = ws / "skills"
    result = get_skills_path(ws)
    assert result == expected
    assert expected.exists()

def test_timestamp():
    """Test timestamp format."""
    ts = timestamp()
    # Should be ISO format, try to parse it
    dt = datetime.fromisoformat(ts)
    assert isinstance(dt, datetime)

def test_truncate_string():
    """Test truncate_string."""
    assert truncate_string("hello world", 11) == "hello world"
    assert truncate_string("hello world", 10) == "hello w..."
    assert truncate_string("hello world", 5, "..") == "hel.."
    assert truncate_string("abc", 5) == "abc"

def test_safe_filename():
    """Test safe_filename."""
    assert safe_filename("hello world.txt") == "hello world.txt"
    assert safe_filename("hello/world.txt") == "hello_world.txt"
    assert safe_filename("<tag>|?*") == "_tag____"
    assert safe_filename("  spaces  ") == "spaces"

def test_parse_session_key():
    """Test parse_session_key."""
    assert parse_session_key("telegram:12345") == ("telegram", "12345")
    assert parse_session_key("slack:C123:U456") == ("slack", "C123:U456")

    with pytest.raises(ValueError, match="Invalid session key"):
        parse_session_key("invalid_key")

    with pytest.raises(ValueError, match="Invalid session key"):
        parse_session_key("key_without_colon")
