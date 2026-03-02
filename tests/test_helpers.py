import pytest
from nanobot.utils.helpers import truncate_string

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
