"""Memory system for persistent agent memory."""

import asyncio
from pathlib import Path

from nanobot.utils.helpers import ensure_dir


class MemoryStore:
    """Two-layer memory: MEMORY.md (long-term facts) + HISTORY.md (grep-searchable log)."""

    def __init__(self, workspace: Path):
        self.memory_dir = ensure_dir(workspace / "memory")
        self.memory_file = self.memory_dir / "MEMORY.md"
        self.history_file = self.memory_dir / "HISTORY.md"

    async def read_long_term(self) -> str:
        def _read():
            if self.memory_file.exists():
                return self.memory_file.read_text(encoding="utf-8")
            return ""
        return await asyncio.to_thread(_read)

    async def write_long_term(self, content: str) -> None:
        await asyncio.to_thread(self.memory_file.write_text, content, encoding="utf-8")

    async def append_history(self, entry: str) -> None:
        def _append():
            with open(self.history_file, "a", encoding="utf-8") as f:
                f.write(entry.rstrip() + "\n\n")
        await asyncio.to_thread(_append)

    async def get_memory_context(self) -> str:
        long_term = await self.read_long_term()
        return f"## Long-term Memory\n{long_term}" if long_term else ""
