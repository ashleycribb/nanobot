"""Message buffering and deduplication for Mochat channel."""

from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from nanobot.channels.mochat.types import MAX_SEEN_MESSAGE_IDS, MochatBufferedEntry, DelayState
from nanobot.config.schema import MochatConfig


class MochatBuffer:
    """Handles message buffering, deduplication, and delayed dispatch."""

    def __init__(self, config: MochatConfig):
        self.config = config
        self._seen_set: dict[str, set[str]] = {}
        self._seen_queue: dict[str, deque[str]] = {}
        self._delay_states: dict[str, DelayState] = {}

    def is_duplicate(self, key: str, message_id: str) -> bool:
        """Check if message ID has been seen for the given target key."""
        if not message_id:
            return False

        seen_set = self._seen_set.setdefault(key, set())
        seen_queue = self._seen_queue.setdefault(key, deque())

        if message_id in seen_set:
            return True

        seen_set.add(message_id)
        seen_queue.append(message_id)
        while len(seen_queue) > MAX_SEEN_MESSAGE_IDS:
            seen_set.discard(seen_queue.popleft())
        return False

    async def enqueue(self, key: str, target_id: str, target_kind: str,
                     entry: MochatBufferedEntry, callback: Any) -> None:
        """Enqueue an entry for delayed dispatch."""
        state = self._delay_states.setdefault(key, DelayState())
        async with state.lock:
            state.entries.append(entry)
            if state.timer:
                state.timer.cancel()
            state.timer = asyncio.create_task(
                self._flush_after_delay(key, target_id, target_kind, callback)
            )

    async def flush(self, key: str, target_id: str, target_kind: str,
                   reason: str, entry: MochatBufferedEntry | None,
                   callback: Any) -> None:
        """Flush buffered entries immediately."""
        state = self._delay_states.setdefault(key, DelayState())
        entries: list[MochatBufferedEntry] = []

        async with state.lock:
            if entry:
                state.entries.append(entry)

            # Cancel any pending timer unless we are running inside it
            current = asyncio.current_task()
            if state.timer and state.timer is not current:
                state.timer.cancel()
            state.timer = None

            entries = state.entries[:]
            state.entries.clear()

        if entries:
            await callback(target_id, target_kind, entries, reason == "mention")

    async def _flush_after_delay(self, key: str, target_id: str,
                                target_kind: str, callback: Any) -> None:
        """Wait for delay then flush."""
        await asyncio.sleep(max(0, self.config.reply_delay_ms) / 1000.0)
        await self.flush(key, target_id, target_kind, "timer", None, callback)

    async def cancel_all(self) -> None:
        """Cancel all pending delay timers."""
        for state in self._delay_states.values():
            if state.timer:
                state.timer.cancel()
        self._delay_states.clear()
