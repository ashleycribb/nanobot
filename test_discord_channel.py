import asyncio
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path
import sys

# Mock dependencies heavily due to broken manager.py
sys.modules['loguru'] = MagicMock()
sys.modules['nanobot.bus.events'] = MagicMock()
sys.modules['nanobot.bus.queue'] = MagicMock()

# Need to mock the base class so we can instantiate DiscordChannel correctly
class BaseChannelMock:
    def __init__(self, config, bus):
        pass
    def is_allowed(self, sender_id):
        return True

mock_base = MagicMock()
mock_base.BaseChannel = BaseChannelMock
sys.modules['nanobot.channels.base'] = mock_base
sys.modules['nanobot.config.schema'] = MagicMock()
sys.modules['nanobot.channels'] = MagicMock()
sys.modules['nanobot.channels.manager'] = MagicMock()
sys.modules['httpx'] = MagicMock()
sys.modules['websockets'] = MagicMock()

# Avoid importing from nanobot.channels directly, load via file path
import importlib.util
spec = importlib.util.spec_from_file_location("discord", "nanobot/channels/discord.py")
discord = importlib.util.module_from_spec(spec)
sys.modules["discord"] = discord
spec.loader.exec_module(discord)

DiscordChannel = discord.DiscordChannel

class MockResponse:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        pass

async def main():
    config = MagicMock()
    bus = MagicMock()
    channel = DiscordChannel(config, bus)
    channel._http = AsyncMock()
    channel._http.get.return_value = MockResponse(b"test data")
    channel._start_typing = AsyncMock()
    channel._handle_message = AsyncMock()
    channel.is_allowed = MagicMock(return_value=True)

    payload = {
        "author": {"id": "123", "bot": False},
        "channel_id": "456",
        "content": "hello",
        "attachments": [
            {"url": "http://example.com/1", "filename": "1.txt", "id": "id1", "size": 10},
            {"url": "http://example.com/2", "filename": "2.txt", "id": "id2", "size": 10},
        ]
    }

    await channel._handle_message_create(payload)

    # Check that _handle_message was called with aggregated media
    channel._handle_message.assert_called_once()
    kwargs = channel._handle_message.call_args[1]

    print("Content:", kwargs["content"])
    print("Media:", kwargs["media"])

    assert "hello" in kwargs["content"]
    assert "[attachment:" in kwargs["content"]
    assert len(kwargs["media"]) == 2

    print("Test passed!")

if __name__ == "__main__":
    asyncio.run(main())
