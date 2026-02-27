import pytest
from nanobot.utils.helpers import truncate_string

def test_truncate_string_no_truncation():
    """Test that short strings are not truncated."""
    s = "hello"
    assert truncate_string(s, max_len=10) == "hello"
    assert truncate_string(s, max_len=5) == "hello"

def test_truncate_string_basic():
    """Test basic truncation with default suffix."""
    s = "hello world"
    # max_len=8, suffix="..." (len 3) -> keep 5 chars: "hello" + "..."
    assert truncate_string(s, max_len=8) == "hello..."
    assert len(truncate_string(s, max_len=8)) == 8

def test_truncate_string_custom_suffix():
    """Test truncation with a custom suffix."""
    s = "hello world"
    # max_len=8, suffix=".." (len 2) -> keep 6 chars: "hello " + ".."
    assert truncate_string(s, max_len=8, suffix="..") == "hello .."
    assert len(truncate_string(s, max_len=8, suffix="..")) == 8

def test_truncate_string_exact_length():
    """Test when string length equals max_len."""
    s = "hello"
    assert truncate_string(s, max_len=5) == "hello"

def test_truncate_string_suffix_longer_than_max_len():
    """Test edge case where suffix is longer than max_len."""
    s = "hello world"
    # max_len=2, suffix="..." (len 3).
    # Current implementation might fail this check or produce wrong length.
    # Desired behavior: return string of max_len, maybe just suffix truncated or hard truncation.
    # Let's assume we want hard truncation if suffix doesn't fit.
    result = truncate_string(s, max_len=2, suffix="...")
    assert len(result) <= 2

def test_truncate_string_max_len_equals_suffix_len():
    """Test when max_len equals suffix length."""
    s = "hello world"
    # max_len=3, suffix="..."
    # Should result in just "..."
    assert truncate_string(s, max_len=3, suffix="...") == "..."

def test_truncate_string_zero_max_len():
    """Test with max_len=0."""
    s = "hello"
    assert truncate_string(s, max_len=0) == ""

def test_truncate_string_empty_string():
    """Test with empty string."""
    assert truncate_string("", max_len=5) == ""
