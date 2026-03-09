import pytest
import base64
from pathlib import Path
from nanobot.agent.context import ContextBuilder

# Since ContextBuilder requires a workspace with memory files
@pytest.fixture
def workspace(tmp_path):
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / "memory").mkdir()
    (ws / "skills").mkdir()
    return ws

@pytest.mark.asyncio
async def test_build_user_content_no_media(workspace):
    builder = ContextBuilder(workspace)
    content = await builder._build_user_content("hello", None)
    assert content == "hello"

@pytest.mark.asyncio
async def test_build_user_content_with_media(workspace):
    builder = ContextBuilder(workspace)

    # Create a dummy image
    img_path = workspace / "test.png"
    img_content = b"fakeimagecontent"
    img_path.write_bytes(img_content)

    media = [str(img_path)]
    content = await builder._build_user_content("hello", media)

    assert isinstance(content, list)
    assert len(content) == 2
    assert content[0]["type"] == "image_url"
    assert content[0]["image_url"]["url"].startswith("data:image/png;base64,")

    # Verify base64 content
    expected_b64 = base64.b64encode(img_content).decode()
    assert expected_b64 in content[0]["image_url"]["url"]

    assert content[1]["type"] == "text"
    assert content[1]["text"] == "hello"

@pytest.mark.asyncio
async def test_build_messages(workspace):
    builder = ContextBuilder(workspace)
    history = [{"role": "user", "content": "hi"}]
    messages = await builder.build_messages(history, "hello")

    assert len(messages) >= 3 # system, history(1), user(1)
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"] == "hello"
