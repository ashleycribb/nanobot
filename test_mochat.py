import sys
from unittest.mock import MagicMock

# Mock out broken manager to avoid IndentationError
sys.modules['nanobot.channels.manager'] = MagicMock()

import asyncio
import json
from pathlib import Path

# Fix up the manager mock
import nanobot.channels
nanobot.channels.ChannelManager = MagicMock()

from nanobot.channels.mochat import MochatChannel
from nanobot.config.schema import MochatConfig

async def test_load_session_cursors():
    # Setup mock config
    config = MagicMock(spec=MochatConfig)
    config.claw_token = "dummy"
    config.socket_disable_msgpack = True
    config.groups = {}
    config.mention = MagicMock()
    config.mention.require_in_groups = False
    bus = MagicMock()
    channel = MochatChannel(config, bus)

    # create a dummy file
    channel._cursor_path = Path("test_cursor_mock.json")
    channel._cursor_path.write_text(json.dumps({"cursors": {"session_1": 42}}))

    await channel._load_session_cursors()

    assert channel._session_cursor["session_1"] == 42
    print("Test passed: cursors loaded correctly async!")

    # cleanup
    channel._cursor_path.unlink()

if __name__ == "__main__":
    asyncio.run(test_load_session_cursors())
