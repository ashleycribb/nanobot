import sys
import re
from unittest.mock import MagicMock, patch
import importlib.util
import pytest

# Since some unrelated files have indentation errors, we still need to mock them
# to allow importing SlackChannel.

@pytest.fixture(scope="session", autouse=True)
def mock_broken_dependencies():
    # Mock everything that might be imported and is broken
    with patch.dict("sys.modules", {
        "loguru": MagicMock(),
        "slack_sdk": MagicMock(),
        "slack_sdk.socket_mode.websockets": MagicMock(),
        "slack_sdk.socket_mode.request": MagicMock(),
        "slack_sdk.socket_mode.response": MagicMock(),
        "slack_sdk.web.async_client": MagicMock(),
        "slackify_markdown": MagicMock(),
        "nanobot.bus.events": MagicMock(),
        "nanobot.bus.queue": MagicMock(),
        "nanobot.channels.base": MagicMock(),
        "nanobot.config.schema": MagicMock(),
        "nanobot.channels.manager": MagicMock(), # Skip broken manager
    }):
        # Mock the base class specifically so SlackChannel can inherit from it
        class BaseChannel:
            def __init__(self, config, bus):
                pass
        sys.modules["nanobot.channels.base"].BaseChannel = BaseChannel

        # Manually load the module from its path to avoid triggering broken imports in the package
        spec = importlib.util.spec_from_file_location("nanobot.channels.slack", "nanobot/channels/slack.py")
        slack_mod = importlib.util.module_from_spec(spec)
        sys.modules["nanobot.channels.slack"] = slack_mod
        spec.loader.exec_module(slack_mod)

        yield slack_mod

@pytest.fixture
def slack_channel_cls(mock_broken_dependencies):
    return mock_broken_dependencies.SlackChannel

def test_convert_table_basic(slack_channel_cls):
    table = """| H1 | H2 |
|---|---|
| R1C1 | R1C2 |
| R2C1 | R2C2 |"""
    match = slack_channel_cls._TABLE_RE.search(table)
    assert match is not None
    result = slack_channel_cls._convert_table(match)
    expected = "**H1**: R1C1 · **H2**: R1C2\n**H1**: R2C1 · **H2**: R2C2"
    assert result == expected

def test_convert_table_empty_cells(slack_channel_cls):
    table = """| H1 | H2 |
|---|---|
| | R1C2 |
| R2C1 | |
| | |"""
    match = slack_channel_cls._TABLE_RE.search(table)
    assert match is not None
    result = slack_channel_cls._convert_table(match)
    expected = "**H2**: R1C2\n**H1**: R2C1"
    assert result == expected

def test_convert_table_extra_cells(slack_channel_cls):
    table = """| H1 | H2 |
|---|---|
| R1C1 | R1C2 | R1C3 |"""
    match = slack_channel_cls._TABLE_RE.search(table)
    assert match is not None
    result = slack_channel_cls._convert_table(match)
    expected = "**H1**: R1C1 · **H2**: R1C2"
    assert result == expected

def test_convert_table_missing_cells(slack_channel_cls):
    table = """| H1 | H2 | H3 |
|---|---|---|
| R1C1 | R1C2 |"""
    match = slack_channel_cls._TABLE_RE.search(table)
    assert match is not None
    result = slack_channel_cls._convert_table(match)
    expected = "**H1**: R1C1 · **H2**: R1C2"
    assert result == expected

def test_convert_table_no_data_rows(slack_channel_cls):
    table = """| H1 | H2 |
|---|---|"""
    match = slack_channel_cls._TABLE_RE.search(table)
    assert match is not None
    result = slack_channel_cls._convert_table(match)
    assert result == ""

def test_to_mrkdwn_integration(slack_channel_cls):
    with patch("nanobot.channels.slack.slackify_markdown", side_effect=lambda x: x):
        text = "Here is a table:\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\nCool?"
        result = slack_channel_cls._to_mrkdwn(text)
        assert "**A**: 1 · **B**: 2" in result
        assert "Here is a table:" in result
        assert "Cool?" in result
        assert "| A | B |" not in result

def test_to_mrkdwn_multiple_tables(slack_channel_cls):
    with patch("nanobot.channels.slack.slackify_markdown", side_effect=lambda x: x):
        text = """Table 1:
| T1H1 |
|---|
| T1R1 |

Table 2:
| T2H1 |
|---|
| T2R1 |"""
        result = slack_channel_cls._to_mrkdwn(text)
        assert "**T1H1**: T1R1" in result
        assert "**T2H1**: T2R1" in result
