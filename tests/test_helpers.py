import pytest
from nanobot.utils.helpers import truncate_string

def test_truncate_string_happy_path():
    """Test truncate_string with normal values."""
    # String shorter than max_len
    assert truncate_string("hello", max_len=10) == "hello"

    # String exactly max_len
    assert truncate_string("hello", max_len=5) == "hello"

    # String longer than max_len
    assert truncate_string("hello world", max_len=8) == "hello..."

def test_truncate_string_edge_case():
    """Test truncate_string when max_len < len(suffix).

    When max_len is less than the length of the suffix, it should return
    the suffix truncated to max_len.
    """
    # suffix is "..." (length 3). max_len is 2.
    result = truncate_string("hello", max_len=2, suffix="...")
    assert result == ".."

    # suffix is "---" (length 3). max_len is 1.
    result = truncate_string("hello", max_len=1, suffix="---")
    assert result == "-"

    # suffix is "..." (length 3). max_len is 0.
    result = truncate_string("hello", max_len=0, suffix="...")
    assert result == ""
def test_truncate_string_shorter_than_max():
    """Test string shorter than max_len."""
    s = "hello"
    assert truncate_string(s, max_len=10) == "hello"

def test_truncate_string_exactly_max():
    """Test string exactly max_len."""
    s = "helloworld"
    assert truncate_string(s, max_len=10) == "helloworld"

def test_truncate_string_longer_than_max():
    """Test string longer than max_len."""
    s = "helloworld test"
    assert truncate_string(s, max_len=10) == "hellowo..."

def test_truncate_string_custom_suffix():
    """Test string longer than max_len with custom suffix."""
    s = "helloworld test"
    assert truncate_string(s, max_len=10, suffix="..") == "hellowor.."

def test_truncate_string_empty():
    """Test empty string."""
    assert truncate_string("", max_len=10) == ""

def test_truncate_string_max_len_less_than_suffix():
    """Test edge case where max_len < len(suffix). Document existing behavior."""
    # Existing behavior: s[: max_len - len(suffix)] + suffix
    # s[: 2 - 3] + "..." -> s[: -1] + "..." -> "he" + "..." -> "he..."
    s = "hello"
    assert truncate_string(s, max_len=2, suffix="...") == "hell..."

def test_truncate_string_max_len_less_than_suffix_case2():
    """Test edge case where max_len < len(suffix). Document existing behavior."""
    s = "helloworld"
    assert truncate_string(s, max_len=2, suffix="...") == "helloworl..."
from nanobot.utils.helpers import parse_session_key

def test_parse_session_key_success():
    """Test parsing a valid session key."""
    channel, chat_id = parse_session_key("slack:U12345")
    assert channel == "slack"
    assert chat_id == "U12345"

    # Test with multiple colons, it should only split on the first one
    channel, chat_id = parse_session_key("telegram:123:456")
    assert channel == "telegram"
    assert chat_id == "123:456"

def test_parse_session_key_invalid():
    """Test parsing an invalid session key raises ValueError."""
    with pytest.raises(ValueError, match="Invalid session key: nosplit"):
        parse_session_key("nosplit")

    with pytest.raises(ValueError, match="Invalid session key: "):
        parse_session_key("")
from nanobot.utils.helpers import truncate_string

def test_truncate_string_basic():
    """Test basic truncation functionality."""
    text = "hello world"
    # max_len=5, suffix="..." (len 3)
    # expected: "he" + "..." = "he..."
    assert truncate_string(text, max_len=5) == "he..."
    assert len(truncate_string(text, max_len=5)) == 5

def test_truncate_string_no_truncation():
    """Test that short strings are not truncated."""
    text = "hello"
    assert truncate_string(text, max_len=10) == "hello"
    assert truncate_string(text, max_len=5) == "hello"

def test_truncate_string_exact_length():
    """Test boundary condition where string length equals max_len."""
    text = "12345"
    assert truncate_string(text, max_len=5) == "12345"

def test_truncate_string_custom_suffix():
    """Test truncation with a custom suffix."""
    text = "hello world"
    # max_len=6, suffix=".." (len 2)
    # expected: "hell" + ".." = "hell.."
    assert truncate_string(text, max_len=6, suffix="..") == "hell.."

def test_truncate_string_empty():
    """Test with empty string."""
    assert truncate_string("", max_len=5) == ""

def test_truncate_string_small_max_len():
    """Test cases where max_len is small but valid."""
    text = "hello"
    # max_len=3, suffix="..." (len 3). 3-3=0. "" + "..." = "..."
    assert truncate_string(text, max_len=3, suffix="...") == "..."

    # max_len=4, suffix="..." (len 3). 4-3=1. "h" + "..." = "h..."
    assert truncate_string(text, max_len=4, suffix="...") == "h..."
from nanobot.utils.helpers import truncate_string, parse_session_key

def test_truncate_string_shorter():
    assert truncate_string("hello", 10) == "hello"

def test_truncate_string_exact_length():
    assert truncate_string("hello", 5) == "hello"

def test_truncate_string_longer():
    assert truncate_string("hello world", 8) == "hello..."

def test_truncate_string_custom_suffix():
    assert truncate_string("hello world", 8, suffix="..") == "hello .."

def test_truncate_string_empty():
    assert truncate_string("", 5) == ""

def test_truncate_string_edge_cases():
    # max_len equal to length of suffix
    assert truncate_string("long string", 3) == "..."

    # max_len smaller than length of suffix (negative slicing behavior)
    assert truncate_string("long", 2) == "lon..."

def test_truncate_string_negative_max_len():
    # max_len is negative, max_len - len(suffix) -> -1 - 3 = -4
    # "hello world"[:-4] -> "hello w" + "..." -> "hello w..."
    assert truncate_string("hello world", -1) == "hello w..."

def test_parse_session_key_valid():
    channel, chat_id = parse_session_key("slack:12345")
    assert channel == "slack"
    assert chat_id == "12345"

def test_parse_session_key_invalid():
    with pytest.raises(ValueError, match="Invalid session key: slack_12345"):
        parse_session_key("slack_12345")

    with pytest.raises(ValueError, match="Invalid session key: slack"):
        parse_session_key("slack")
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
    """Test get_workspace_path with no arguments uses default path."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    expected_path = tmp_path / ".nanobot" / "workspace"

    # Ensure it doesn't exist before
    """Test get_workspace_path with default arguments (uses home dir)."""
    # Mock Path.home() to return tmp_path
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    expected_path = tmp_path / ".nanobot" / "workspace"
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
