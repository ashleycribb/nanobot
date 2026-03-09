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
