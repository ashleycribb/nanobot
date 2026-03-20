import sys
from unittest.mock import MagicMock

# Mock dependencies that might be missing in the environment
sys.modules['loguru'] = MagicMock()
mock_pydantic = MagicMock()
sys.modules['pydantic'] = mock_pydantic
sys.modules['pydantic.alias_generators'] = MagicMock()
sys.modules['pydantic_settings'] = MagicMock()

import pytest
from nanobot.channels.manager import ChannelManager

def test_enabled_channels_empty():
    """Test that enabled_channels returns an empty list when no channels are present."""
    config = MagicMock()
    # Disable all channels in config
    for attr in ["telegram", "whatsapp", "discord", "feishu", "mochat", "dingtalk", "email", "slack", "qq"]:
        getattr(config.channels, attr).enabled = False

    bus = MagicMock()
    manager = ChannelManager(config, bus)
    # Ensure channels dict is empty
    manager.channels = {}

    assert manager.enabled_channels == []
    assert manager.get_status() == {}

def test_enabled_channels_and_status_with_channels():
    """Test enabled_channels and get_status with populated channels."""
    config = MagicMock()
    for attr in ["telegram", "whatsapp", "discord", "feishu", "mochat", "dingtalk", "email", "slack", "qq"]:
        getattr(config.channels, attr).enabled = False

    bus = MagicMock()
    manager = ChannelManager(config, bus)

    # Manually populate channels to test the property and status method
    mock_channel_running = MagicMock()
    mock_channel_running.is_running = True

    mock_channel_stopped = MagicMock()
    mock_channel_stopped.is_running = False

    manager.channels = {
        "running_channel": mock_channel_running,
        "stopped_channel": mock_channel_stopped
    }

    # Test enabled_channels property
    enabled = manager.enabled_channels
    assert isinstance(enabled, list)
    assert set(enabled) == {"running_channel", "stopped_channel"}

    # Test get_status method
    status = manager.get_status()
    assert status == {
        "running_channel": {
            "enabled": True,
            "running": True
        },
        "stopped_channel": {
            "enabled": True,
            "running": False
        }
    }

def test_get_channel():
    """Test get_channel returns the correct channel or None."""
    config = MagicMock()
    for attr in ["telegram", "whatsapp", "discord", "feishu", "mochat", "dingtalk", "email", "slack", "qq"]:
        getattr(config.channels, attr).enabled = False

    bus = MagicMock()
    manager = ChannelManager(config, bus)

    mock_channel = MagicMock()
    manager.channels = {"test": mock_channel}

    assert manager.get_channel("test") == mock_channel
    assert manager.get_channel("nonexistent") is None
