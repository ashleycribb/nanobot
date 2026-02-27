"""Mochat channel implementation using refactored components."""

from __future__ import annotations

import asyncio
from typing import Any

from loguru import logger

from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.channels.base import BaseChannel
from nanobot.config.schema import MochatConfig
from nanobot.channels.mochat.types import MochatBufferedEntry
from nanobot.channels.mochat.utils import (
    resolve_mochat_target, normalize_mochat_content, normalize_id_list,
    str_field, safe_dict, parse_timestamp, make_synthetic_event,
    read_group_id, resolve_was_mentioned, resolve_require_mention,
    build_buffered_body
)
from nanobot.channels.mochat.http import MochatHTTPClient
from nanobot.channels.mochat.cursor import MochatCursorManager
from nanobot.channels.mochat.buffering import MochatBuffer
from nanobot.channels.mochat.socket import MochatSocketClient, SOCKETIO_AVAILABLE


class MochatChannel(BaseChannel):
    """Mochat channel using socket.io with fallback polling workers."""

    name = "mochat"

    def __init__(self, config: MochatConfig, bus: MessageBus):
        super().__init__(config, bus)
        self.config: MochatConfig = config

        # Components
        self.http = MochatHTTPClient(config)
        self.cursor_mgr = MochatCursorManager()
        self.buffer = MochatBuffer(config)
        self.socket = MochatSocketClient(
            config,
            on_connect=self._on_socket_connect,
            on_disconnect=self._on_socket_disconnect,
            on_session_event=lambda p: self._handle_watch_payload(p, "session"),
            on_panel_event=lambda p: self._handle_watch_payload(p, "panel"),
            on_notify=self._handle_notify
        )

        # State
        self._ws_ready = False
        self._session_set: set[str] = set()
        self._panel_set: set[str] = set()
        self._auto_discover_sessions = False
        self._auto_discover_panels = False
        self._cold_sessions: set[str] = set()
        self._session_by_converse: dict[str, str] = {}
        self._target_locks: dict[str, asyncio.Lock] = {}

        # Fallback & Refresh
        self._fallback_mode = False
        self._session_fallback_tasks: dict[str, asyncio.Task] = {}
        self._panel_fallback_tasks: dict[str, asyncio.Task] = {}
        self._refresh_task: asyncio.Task | None = None

    # ---- lifecycle ---------------------------------------------------------

    async def start(self) -> None:
        """Start Mochat channel workers and websocket connection."""
        if not self.config.claw_token:
            logger.error("Mochat claw_token not configured")
            return

        self._running = True
        await self.http.start()
        await self.cursor_mgr.load()

        self._seed_targets_from_config()
        await self._refresh_targets(subscribe_new=False)

        connected = False
        if SOCKETIO_AVAILABLE:
            connected = await self.socket.connect()

        if not connected:
            await self._ensure_fallback_workers()

        self._refresh_task = asyncio.create_task(self._refresh_loop())
        while self._running:
            await asyncio.sleep(1)

    async def stop(self) -> None:
        """Stop all workers and clean up resources."""
        self._running = False

        if self._refresh_task:
            self._refresh_task.cancel()
            self._refresh_task = None

        await self._stop_fallback_workers()
        await self.buffer.cancel_all()
        await self.socket.disconnect()
        await self.cursor_mgr.close()
        await self.http.stop()

        self._ws_ready = False

    async def send(self, msg: OutboundMessage) -> None:
        """Send outbound message to session or panel."""
        if not self.config.claw_token:
            logger.warning("Mochat claw_token missing, skip send")
            return

        parts = ([msg.content.strip()] if msg.content and msg.content.strip() else [])
        if msg.media:
            parts.extend(m for m in msg.media if isinstance(m, str) and m.strip())
        content = "\n".join(parts).strip()
        if not content:
            return

        target = resolve_mochat_target(msg.chat_id)
        if not target.id:
            logger.warning("Mochat outbound target is empty")
            return

        is_panel = (target.is_panel or target.id in self._panel_set) and not target.id.startswith("session_")

        try:
            await self.http.send_message(
                target.id, content, msg.reply_to, is_panel,
                read_group_id(msg.metadata)
            )
        except Exception as e:
            logger.error(f"Failed to send Mochat message: {e}")

    # ---- config / init helpers ---------------------------------------------

    def _seed_targets_from_config(self) -> None:
        sessions, self._auto_discover_sessions = normalize_id_list(self.config.sessions)
        panels, self._auto_discover_panels = normalize_id_list(self.config.panels)

        self._session_set.update(sessions)
        self._panel_set.update(panels)

        for sid in sessions:
            if not self.cursor_mgr.contains(sid):
                self._cold_sessions.add(sid)

    # ---- websocket handlers ------------------------------------------------

    async def _on_socket_connect(self) -> None:
        self._ws_ready = False
        subscribed = await self._subscribe_all()
        self._ws_ready = subscribed

        if subscribed:
            await self._stop_fallback_workers()
        else:
            await self._ensure_fallback_workers()

    async def _on_socket_disconnect(self) -> None:
        self._ws_ready = False
        if self._running:
            await self._ensure_fallback_workers()

    async def _handle_notify(self, event_name: str, payload: Any) -> None:
        if event_name == "notify:chat.inbox.append":
            await self._handle_notify_inbox_append(payload)
        elif event_name.startswith("notify:chat.message."):
            await self._handle_notify_chat_message(payload)

    # ---- subscribe ---------------------------------------------------------

    async def _subscribe_all(self) -> bool:
        ok = await self._subscribe_sessions(sorted(self._session_set))
        ok = await self._subscribe_panels(sorted(self._panel_set)) and ok

        if self._auto_discover_sessions or self._auto_discover_panels:
            await self._refresh_targets(subscribe_new=True)

        return ok

    async def _subscribe_sessions(self, session_ids: list[str]) -> bool:
        if not session_ids:
            return True

        # Mark unknown sessions as cold
        for sid in session_ids:
            if not self.cursor_mgr.contains(sid):
                self._cold_sessions.add(sid)

        ack = await self.socket.call("com.claw.im.subscribeSessions", {
            "sessionIds": session_ids,
            "cursors": self.cursor_mgr.get_all(),
            "limit": self.config.watch_limit,
        })

        if not ack.get("result"):
            logger.error(f"Mochat subscribeSessions failed: {ack.get('message', 'unknown error')}")
            return False

        data = ack.get("data")
        items: list[dict[str, Any]] = []
        if isinstance(data, list):
            items = [i for i in data if isinstance(i, dict)]
        elif isinstance(data, dict):
            sessions = data.get("sessions")
            if isinstance(sessions, list):
                items = [i for i in sessions if isinstance(i, dict)]
            elif "sessionId" in data:
                items = [data]

        for p in items:
            await self._handle_watch_payload(p, "session")
        return True

    async def _subscribe_panels(self, panel_ids: list[str]) -> bool:
        if not self._auto_discover_panels and not panel_ids:
            return True

        ack = await self.socket.call("com.claw.im.subscribePanels", {"panelIds": panel_ids})
        if not ack.get("result"):
            logger.error(f"Mochat subscribePanels failed: {ack.get('message', 'unknown error')}")
            return False
        return True

    # ---- refresh / discovery -----------------------------------------------

    async def _refresh_loop(self) -> None:
        interval_s = max(1.0, self.config.refresh_interval_ms / 1000.0)
        while self._running:
            await asyncio.sleep(interval_s)
            try:
                await self._refresh_targets(subscribe_new=self._ws_ready)
            except Exception as e:
                logger.warning(f"Mochat refresh failed: {e}")
            if self._fallback_mode:
                await self._ensure_fallback_workers()

    async def _refresh_targets(self, subscribe_new: bool) -> None:
        if self._auto_discover_sessions:
            await self._refresh_sessions_directory(subscribe_new)
        if self._auto_discover_panels:
            await self._refresh_panels(subscribe_new)

    async def _refresh_sessions_directory(self, subscribe_new: bool) -> None:
        sessions = await self.http.list_sessions()

        new_ids: list[str] = []
        for s in sessions:
            sid = str_field(s, "sessionId")
            if not sid:
                continue

            if sid not in self._session_set:
                self._session_set.add(sid)
                new_ids.append(sid)
                if not self.cursor_mgr.contains(sid):
                    self._cold_sessions.add(sid)

            cid = str_field(s, "converseId")
            if cid:
                self._session_by_converse[cid] = sid

        if not new_ids:
            return

        if self._ws_ready and subscribe_new:
            await self._subscribe_sessions(new_ids)
        if self._fallback_mode:
            await self._ensure_fallback_workers()

    async def _refresh_panels(self, subscribe_new: bool) -> None:
        panels = await self.http.list_panels()

        new_ids: list[str] = []
        for p in panels:
            pt = p.get("type")
            if isinstance(pt, int) and pt != 0:
                continue

            pid = str_field(p, "id", "_id")
            if pid and pid not in self._panel_set:
                self._panel_set.add(pid)
                new_ids.append(pid)

        if not new_ids:
            return

        if self._ws_ready and subscribe_new:
            await self._subscribe_panels(new_ids)
        if self._fallback_mode:
            await self._ensure_fallback_workers()

    # ---- fallback workers --------------------------------------------------

    async def _ensure_fallback_workers(self) -> None:
        if not self._running:
            return

        self._fallback_mode = True

        # Start session watchers
        for sid in sorted(self._session_set):
            t = self._session_fallback_tasks.get(sid)
            if not t or t.done():
                self._session_fallback_tasks[sid] = asyncio.create_task(
                    self._session_watch_worker(sid)
                )

        # Start panel pollers
        for pid in sorted(self._panel_set):
            t = self._panel_fallback_tasks.get(pid)
            if not t or t.done():
                self._panel_fallback_tasks[pid] = asyncio.create_task(
                    self._panel_poll_worker(pid)
                )

    async def _stop_fallback_workers(self) -> None:
        self._fallback_mode = False
        tasks = [*self._session_fallback_tasks.values(), *self._panel_fallback_tasks.values()]
        for t in tasks:
            t.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._session_fallback_tasks.clear()
        self._panel_fallback_tasks.clear()

    async def _session_watch_worker(self, session_id: str) -> None:
        while self._running and self._fallback_mode:
            try:
                payload = await self.http.watch_session(
                    session_id,
                    self.cursor_mgr.get(session_id),
                    self.config.watch_timeout_ms,
                    self.config.watch_limit
                )
                await self._handle_watch_payload(payload, "session")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Mochat watch fallback error ({session_id}): {e}")
                await asyncio.sleep(max(0.1, self.config.retry_delay_ms / 1000.0))

    async def _panel_poll_worker(self, panel_id: str) -> None:
        sleep_s = max(1.0, self.config.refresh_interval_ms / 1000.0)
        while self._running and self._fallback_mode:
            try:
                resp = await self.http.poll_panel_messages(
                    panel_id, min(100, max(1, self.config.watch_limit))
                )
                msgs = resp.get("messages")
                if isinstance(msgs, list):
                    for m in reversed(msgs):
                        if not isinstance(m, dict):
                            continue
                        evt = make_synthetic_event(
                            message_id=str(m.get("messageId") or ""),
                            author=str(m.get("author") or ""),
                            content=m.get("content"),
                            meta=m.get("meta"),
                            group_id=str(resp.get("groupId") or ""),
                            converse_id=panel_id,
                            timestamp=m.get("createdAt"),
                            author_info=m.get("authorInfo"),
                        )
                        await self._process_inbound_event(panel_id, evt, "panel")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Mochat panel polling error ({panel_id}): {e}")
            await asyncio.sleep(sleep_s)

    # ---- inbound event processing ------------------------------------------

    async def _handle_watch_payload(self, payload: dict[str, Any], target_kind: str) -> None:
        if not isinstance(payload, dict):
            return

        target_id = str_field(payload, "sessionId")
        if not target_id:
            return

        lock = self._target_locks.setdefault(f"{target_kind}:{target_id}", asyncio.Lock())
        async with lock:
            prev = self.cursor_mgr.get(target_id) if target_kind == "session" else 0

            pc = payload.get("cursor")
            if target_kind == "session" and isinstance(pc, int) and pc >= 0:
                self.cursor_mgr.mark(target_id, pc)

            raw_events = payload.get("events")
            if not isinstance(raw_events, list):
                return

            if target_kind == "session" and target_id in self._cold_sessions:
                self._cold_sessions.discard(target_id)
                return

            for event in raw_events:
                if not isinstance(event, dict):
                    continue

                seq = event.get("seq")
                if target_kind == "session" and isinstance(seq, int):
                    current_cursor = self.cursor_mgr.get(target_id)
                    # Use prev captured cursor for logic if needed, but here we just check against store
                    if seq > current_cursor:
                        self.cursor_mgr.mark(target_id, seq)

                if event.get("type") == "message.add":
                    await self._process_inbound_event(target_id, event, target_kind)

    async def _process_inbound_event(self, target_id: str, event: dict[str, Any], target_kind: str) -> None:
        payload = event.get("payload")
        if not isinstance(payload, dict):
            return

        author = str_field(payload, "author")
        if not author or (self.config.agent_user_id and author == self.config.agent_user_id):
            return
        if not self.is_allowed(author):
            return

        message_id = str_field(payload, "messageId")
        seen_key = f"{target_kind}:{target_id}"

        if message_id and self.buffer.is_duplicate(seen_key, message_id):
            return

        raw_body = normalize_mochat_content(payload.get("content")) or "[empty message]"
        ai = safe_dict(payload.get("authorInfo"))
        sender_name = str_field(ai, "nickname", "email")
        sender_username = str_field(ai, "agentId")

        group_id = str_field(payload, "groupId")
        is_group = bool(group_id)

        was_mentioned = resolve_was_mentioned(payload, self.config.agent_user_id)
        require_mention = target_kind == "panel" and is_group and resolve_require_mention(self.config, target_id, group_id)
        use_delay = target_kind == "panel" and self.config.reply_delay_mode == "non-mention"

        if require_mention and not was_mentioned and not use_delay:
            return

        entry = MochatBufferedEntry(
            raw_body=raw_body, author=author, sender_name=sender_name,
            sender_username=sender_username, timestamp=parse_timestamp(event.get("timestamp")),
            message_id=message_id, group_id=group_id,
        )

        if use_delay:
            delay_key = seen_key
            if was_mentioned:
                await self.buffer.flush(delay_key, target_id, target_kind, "mention", entry, self._dispatch_entries)
            else:
                await self.buffer.enqueue(delay_key, target_id, target_kind, entry, self._dispatch_entries)
            return

        await self._dispatch_entries(target_id, target_kind, [entry], was_mentioned)

    async def _dispatch_entries(self, target_id: str, target_kind: str,
                              entries: list[MochatBufferedEntry], was_mentioned: bool) -> None:
        if not entries:
            return

        last = entries[-1]
        is_group = bool(last.group_id)
        body = build_buffered_body(entries, is_group) or "[empty message]"

        await self._handle_message(
            sender_id=last.author,
            chat_id=target_id,
            content=body,
            metadata={
                "message_id": last.message_id,
                "timestamp": last.timestamp,
                "is_group": is_group,
                "group_id": last.group_id,
                "sender_name": last.sender_name,
                "sender_username": last.sender_username,
                "target_kind": target_kind,
                "was_mentioned": was_mentioned,
                "buffered_count": len(entries),
            },
        )

    # ---- notify handlers ---------------------------------------------------

    async def _handle_notify_chat_message(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return

        group_id = str_field(payload, "groupId")
        panel_id = str_field(payload, "converseId", "panelId")
        if not group_id or not panel_id:
            return

        if self._panel_set and panel_id not in self._panel_set:
            return

        evt = make_synthetic_event(
            message_id=str(payload.get("_id") or payload.get("messageId") or ""),
            author=str(payload.get("author") or ""),
            content=payload.get("content"),
            meta=payload.get("meta"),
            group_id=group_id,
            converse_id=panel_id,
            timestamp=payload.get("createdAt"),
            author_info=payload.get("authorInfo"),
        )
        await self._process_inbound_event(panel_id, evt, "panel")

    async def _handle_notify_inbox_append(self, payload: Any) -> None:
        if not isinstance(payload, dict) or payload.get("type") != "message":
            return

        detail = payload.get("payload")
        if not isinstance(detail, dict):
            return

        if str_field(detail, "groupId"):
            return

        converse_id = str_field(detail, "converseId")
        if not converse_id:
            return

        session_id = self._session_by_converse.get(converse_id)
        if not session_id:
            await self._refresh_sessions_directory(self._ws_ready)
            session_id = self._session_by_converse.get(converse_id)
        if not session_id:
            return

        evt = make_synthetic_event(
            message_id=str(detail.get("messageId") or payload.get("_id") or ""),
            author=str(detail.get("messageAuthor") or ""),
            content=str(detail.get("messagePlainContent") or detail.get("messageSnippet") or ""),
            meta={"source": "notify:chat.inbox.append", "converseId": converse_id},
            group_id="",
            converse_id=converse_id,
            timestamp=payload.get("createdAt"),
        )
        await self._process_inbound_event(session_id, evt, "session")
