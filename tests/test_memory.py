import pytest
import asyncio
from pathlib import Path
from nanobot.agent.memory import MemoryStore

@pytest.fixture
def memory_store(tmp_path):
    """Fixture to provide a MemoryStore instance with a temporary workspace."""
    return MemoryStore(workspace=tmp_path)

@pytest.mark.asyncio
async def test_aget_memory_context_empty(memory_store):
    """Test that an empty memory file returns an empty context string."""
    context = await memory_store.aget_memory_context()
    assert context == ""

@pytest.mark.asyncio
async def test_aget_memory_context_with_content(memory_store):
    """Test that a populated memory file returns the correct context string."""
    test_content = "- User prefers Python.\n- User lives in Tokyo."
    await memory_store.write_long_term(test_content)

    context = await memory_store.aget_memory_context()
    expected_context = f"## Long-term Memory\n{test_content}"
    assert context == expected_context

@pytest.mark.asyncio
async def test_aget_memory_context_nonexistent_file(memory_store):
    """Test that if the memory file does not exist, it returns an empty string."""
    # Ensure it's not there
    if memory_store.memory_file.exists():
        memory_store.memory_file.unlink()

    context = await memory_store.aget_memory_context()
    assert context == ""
