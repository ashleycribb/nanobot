"""Cursor management for Mochat channel."""

from __future__ import annotations

import json
from datetime import datetime
import asyncio
from typing import Any
from pathlib import Path

from loguru import logger
from nanobot.utils.helpers import get_data_path
from nanobot.channels.mochat.types import CURSOR_SAVE_DEBOUNCE_S


class MochatCursorManager:
    """Manages session cursors for reliable message tracking."""

    def __init__(self):
        self._state_dir = get_data_path() / "mochat"
        self._cursor_path = self._state_dir / "session_cursors.json"
        self._session_cursor: dict[str, int] = {}
        self._save_task: asyncio.Task | None = None

    async def load(self) -> None:
        """Load cursors from disk."""
        self._state_dir.mkdir(parents=True, exist_ok=True)
        if not self._cursor_path.exists():
            return

        try:
            content = self._cursor_path.read_text("utf-8")
            data = json.loads(content)
        except Exception as e:
            logger.warning(f"Failed to read Mochat cursor file: {e}")
            return

        cursors = data.get("cursors")
        if isinstance(cursors, dict):
            for sid, cur in cursors.items():
                if isinstance(sid, str) and isinstance(cur, int) and cur >= 0:
                    self._session_cursor[sid] = cur

    def get(self, session_id: str) -> int:
        """Get current cursor for a session."""
        return self._session_cursor.get(session_id, 0)

    def contains(self, session_id: str) -> bool:
        """Check if a session has a stored cursor."""
        return session_id in self._session_cursor

    def mark(self, session_id: str, cursor: int) -> None:
        """Update cursor for a session if newer."""
        if cursor < 0 or cursor < self.get(session_id):
            return

        self._session_cursor[session_id] = cursor
        if not self._save_task or self._save_task.done():
            self._save_task = asyncio.create_task(self._save_debounced())

    def get_all(self) -> dict[str, int]:
        """Get all cursors."""
        return self._session_cursor.copy()

    async def _save_debounced(self) -> None:
        """Save cursors to disk after a short delay."""
        await asyncio.sleep(CURSOR_SAVE_DEBOUNCE_S)
        await self.save()

    async def save(self) -> None:
        """Persist cursors to disk immediately."""
        try:
            data = {
                "schemaVersion": 1,
                "updatedAt": datetime.utcnow().isoformat(),
                "cursors": self._session_cursor,
            }
            content = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
            self._cursor_path.write_text(content, "utf-8")
        except Exception as e:
            logger.warning(f"Failed to save Mochat cursor file: {e}")

    async def close(self) -> None:
        """Clean up and ensure final save."""
        if self._save_task:
            self._save_task.cancel()
            try:
                await self._save_task
            except asyncio.CancelledError:
                pass
            self._save_task = None
        await self.save()
