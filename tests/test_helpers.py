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
def test_truncate_string_very_short_max_len():
    """
    Test behavior when max_len is very short.
    """
    text = "Hello"
    assert truncate_string(text, max_len=2, suffix="...") == ".."
    # max_len=2, suffix="..." (len 3). 2-3=-1. text[:-1] -> "Hell". Result: "Hell..."
    # This is a known issue/behavior of the current implementation.
    # The requirement is to 'Add unit tests', so we document current behavior.
    # However, ideally, it should probably return just the suffix truncated or something else.
    # But let's stick to validating existing behavior unless we want to fix it.
    # Given the instructions "Pure function... simple logic", I assume it's meant to be simple.

    # Let's verify what happens:
    # truncate_string("Hello", max_len=2, suffix="...") -> ".." (len 2)
    assert truncate_string(text, max_len=2, suffix="...") == ".."
    assert truncate_string(text, max_len=2, suffix="...") == ".."
    # max_len=2, suffix="..." (len 3). max_len < len(suffix), so return text[:2] -> "He"
    assert truncate_string(text, max_len=2, suffix="...") == "He"

    result = get_workspace_path(None)

    assert result == expected_path
    assert result.exists()
    assert result.is_dir()

from nanobot.utils.helpers import truncate_string

def test_truncate_string_shorter_than_max_len():
    """Test that a string shorter than max_len is returned unchanged."""
    s = "hello"
    assert truncate_string(s, max_len=10) == "hello"

def test_truncate_string_equal_to_max_len():
    """Test that a string equal to max_len is returned unchanged."""
    s = "hello"
    assert truncate_string(s, max_len=5) == "hello"

def test_truncate_string_longer_than_max_len():
    """Test that a string longer than max_len is truncated and suffix is appended."""
    s = "hello world"
    result = truncate_string(s, max_len=8, suffix="...")
    assert result == "hello..."
    assert len(result) == 8

def test_truncate_string_empty():
    """Test that an empty string is handled correctly."""
    assert truncate_string("", max_len=10) == ""

def test_truncate_string_custom_suffix():
    """Test that a custom suffix works correctly."""
    s = "hello world"
    result = truncate_string(s, max_len=8, suffix="!!")
    assert result == "hello !!"
    assert len(result) == 8

def test_truncate_string_max_len_smaller_than_suffix():
    """
    Test edge case where max_len is smaller than the length of the suffix.
    """
    s = "hello world"
    result = truncate_string(s, max_len=2, suffix="...")
    assert result == ".."
    # max_len (2) < len("...") (3)
    # 2 - 3 = -1, so it returns suffix[:2] -> ".."
    result = truncate_string(s, max_len=2, suffix="...")
    assert result == ".."
    assert len(result) <= 2
    result = truncate_string(s, max_len=2, suffix="...")
    assert result == ".."
    # should return s[:2] -> "he"
    result = truncate_string(s, max_len=2, suffix="...")
    assert result == "he"
    assert len(result) == 2

def test_truncate_string_default_args():
    """Test truncate_string with default arguments."""
    s = "a" * 150
    result = truncate_string(s)
    assert len(result) == 100
    assert result.endswith("...")
    assert result.startswith("a" * 97)
