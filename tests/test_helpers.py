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
