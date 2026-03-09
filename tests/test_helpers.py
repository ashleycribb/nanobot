import pytest
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
