"""Tests for utility functions."""
import pytest
from nanobot.utils.helpers import truncate_string

def test_truncate_string_basic():
    """Test basic truncation."""
    s = "hello world"
    assert truncate_string(s, 5) == "he..."

def test_truncate_string_short():
    """Test no truncation when string is short."""
    s = "hi"
    assert truncate_string(s, 5) == "hi"

def test_truncate_string_exact():
    """Test no truncation when string is exact length."""
    s = "hello"
    assert truncate_string(s, 5) == "hello"

def test_truncate_string_custom_suffix():
    """Test custom suffix."""
    s = "hello world"
    assert truncate_string(s, 5, suffix=".") == "hell."

def test_truncate_string_empty():
    """Test empty string."""
    assert truncate_string("", 5) == ""

def test_truncate_string_suffix_too_long():
    """Test when suffix is longer than max_len."""
    s = "hello world"
    # Current implementation might fail this, or return something longer.
    # We expect it to be truncated to max_len, possibly without suffix or with truncated suffix.
    # For now, let's assert it returns max_len chars.
    result = truncate_string(s, 2, suffix="...")
    assert len(result) <= 2
