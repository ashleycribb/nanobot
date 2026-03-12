import pytest
from nanobot.utils.helpers import safe_filename

def test_safe_filename_valid():
    """Test that valid filenames are returned unchanged."""
    assert safe_filename("valid_filename.txt") == "valid_filename.txt"
    assert safe_filename("my-file-name") == "my-file-name"
    assert safe_filename("Document 1") == "Document 1"

def test_safe_filename_unsafe_chars():
    """Test that unsafe characters are replaced with underscore."""
    # unsafe = '<>:"/\\|?*'
    assert safe_filename("file<name") == "file_name"
    assert safe_filename("file>name") == "file_name"
    assert safe_filename("file:name") == "file_name"
    assert safe_filename('file"name') == "file_name"
    assert safe_filename("file/name") == "file_name"
    assert safe_filename("file\\name") == "file_name"
    assert safe_filename("file|name") == "file_name"
    assert safe_filename("file?name") == "file_name"
    assert safe_filename("file*name") == "file_name"

def test_safe_filename_mixed_unsafe():
    """Test mixed unsafe characters."""
    assert safe_filename('bad<file>:name/test\\here|what?*') == "bad_file__name_test_here_what__"

def test_safe_filename_whitespace():
    """Test that leading/trailing whitespace is stripped."""
    assert safe_filename("  filename.txt  ") == "filename.txt"
    assert safe_filename("\tfilename.txt\n") == "filename.txt"

def test_safe_filename_combined():
    """Test combination of unsafe chars and whitespace."""
    assert safe_filename("  <bad:file>  ") == "_bad_file_"

def test_safe_filename_edge_cases():
    """Test edge cases like empty strings or all unsafe chars."""
    assert safe_filename("") == ""
    assert safe_filename("   ") == ""
    # Test all unsafe characters in one string
    assert safe_filename("<>:\"/\\|?*") == "_" * 9
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

def test_get_workspace_path_expanded(monkeypatch, tmp_path):
    """Test get_workspace_path with a path that needs expanding."""
    def mock_expanduser(self):
        return tmp_path / str(self)[2:] if str(self).startswith("~") else self

    monkeypatch.setattr(Path, "expanduser", mock_expanduser)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    custom_ws = "~/my_expanded_workspace"

    expected_path = tmp_path / "my_expanded_workspace"
    assert not expected_path.exists()

    result = get_workspace_path(custom_ws)

    assert result == expected_path
    assert result.exists()
    assert result.is_dir()

def test_get_workspace_path_none(monkeypatch, tmp_path):
    """Test get_workspace_path with None explicitly."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    expected_path = tmp_path / ".nanobot" / "workspace"
    assert not expected_path.exists()

    result = get_workspace_path(None)

    assert result == expected_path
    assert result.exists()
    assert result.is_dir()

