import pytest
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
