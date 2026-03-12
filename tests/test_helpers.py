import pytest
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
