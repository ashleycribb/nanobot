import pytest
from pathlib import Path
from nanobot.agent.memory import MemoryStore

def test_write_long_term(tmp_path: Path):
    store = MemoryStore(tmp_path)
    store.write_long_term("Hello World!")

    assert store.memory_file.exists()
    assert store.memory_file.read_text(encoding="utf-8") == "Hello World!"

def test_append_history(tmp_path: Path):
    store = MemoryStore(tmp_path)
    store.append_history("Entry 1")
    store.append_history("Entry 2")

    assert store.history_file.exists()
    assert store.history_file.read_text(encoding="utf-8") == "Entry 1\n\nEntry 2\n\n"

def test_read_long_term(tmp_path: Path):
    store = MemoryStore(tmp_path)
    assert store.read_long_term() == ""

    store.write_long_term("Hello World!")
    assert store.read_long_term() == "Hello World!"

def test_get_memory_context(tmp_path: Path):
    store = MemoryStore(tmp_path)
    assert store.get_memory_context() == ""

    store.write_long_term("Some memory")
    assert store.get_memory_context() == "## Long-term Memory\nSome memory"

@pytest.mark.asyncio
async def test_aread_long_term(tmp_path: Path):
    store = MemoryStore(tmp_path)
    assert await store.aread_long_term() == ""

    store.write_long_term("Async Memory")
    assert await store.aread_long_term() == "Async Memory"

@pytest.mark.asyncio
async def test_aget_memory_context(tmp_path: Path):
    store = MemoryStore(tmp_path)
    assert await store.aget_memory_context() == ""

    store.write_long_term("Async Context")
    assert await store.aget_memory_context() == "## Long-term Memory\nAsync Context"
