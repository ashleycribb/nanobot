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
"""Tests for nanobot.utils.helpers."""

import pytest
from nanobot.utils.helpers import truncate_string


def test_truncate_string_shorter_than_max():
    """String shorter than max_len should return as is."""
    text = "Hello"
    assert truncate_string(text, max_len=10) == "Hello"


def test_truncate_string_exact_max():
    """String equal to max_len should return as is."""
    text = "Hello World"
    assert truncate_string(text, max_len=11) == "Hello World"


def test_truncate_string_longer_than_max():
    """String longer than max_len should be truncated with suffix."""
    text = "Hello World"
    # max_len=8, suffix="..." (len 3). Expect 8-3=5 chars + "..." -> "Hello..."
    assert truncate_string(text, max_len=8) == "Hello..."
    assert len(truncate_string(text, max_len=8)) == 8


def test_truncate_string_custom_suffix():
    """Custom suffix should be used."""
    text = "Hello World"
    # max_len=8, suffix=".." (len 2). Expect 8-2=6 chars + ".." -> "Hello .."
    assert truncate_string(text, max_len=8, suffix="..") == "Hello .."
    assert len(truncate_string(text, max_len=8, suffix="..")) == 8


def test_truncate_string_empty_string():
    """Empty string should be returned as is (length 0 <= max_len)."""
    assert truncate_string("", max_len=5) == ""


def test_truncate_string_suffix_only():
    """If max_len equals suffix length, should return suffix only."""
    text = "Hello World"
    suffix = "..."
    # max_len=3. 3-3=0 chars + suffix -> "..."
    assert truncate_string(text, max_len=3, suffix=suffix) == "..."
    assert len(truncate_string(text, max_len=3, suffix=suffix)) == 3


def test_truncate_string_very_short_max_len():
    """
    Test behavior when max_len is very short.
    Note: Current implementation may produce string longer than max_len
    if max_len < len(suffix). We test the current behavior.
    """
    text = "Hello"
    # max_len=2, suffix="..." (len 3). 2-3=-1. text[:-1] -> "Hell". Result: "Hell..."
    # This is a known issue/behavior of the current implementation.
    # The requirement is to 'Add unit tests', so we document current behavior.
    # However, ideally, it should probably return just the suffix truncated or something else.
    # But let's stick to validating existing behavior unless we want to fix it.
    # Given the instructions "Pure function... simple logic", I assume it's meant to be simple.

    # Let's verify what happens:
    # truncate_string("Hello", max_len=2, suffix="...") -> "Hell..." (len 7)
    assert truncate_string(text, max_len=2, suffix="...") == "Hell..."


def test_truncate_string_default_args():
    """Test default arguments (max_len=100, suffix='...')."""
    text = "a" * 105
    truncated = truncate_string(text)
    assert len(truncated) == 100
    assert truncated.endswith("...")
    assert truncated.startswith("a" * 97)
import pytest

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
    The function does not strictly enforce max_len in this case and returns
    a string longer than max_len due to negative slicing.
    """
    s = "hello world"
    # max_len (2) < len("...") (3)
    # 2 - 3 = -1, so s[:-1] + "..." -> "hello worl..."
    result = truncate_string(s, max_len=2, suffix="...")
    assert result == "hello worl..."
    assert len(result) > 2

def test_truncate_string_default_args():
    """Test truncate_string with default arguments."""
    s = "a" * 150
    result = truncate_string(s)
    assert len(result) == 100
    assert result.endswith("...")
    assert result.startswith("a" * 97)
