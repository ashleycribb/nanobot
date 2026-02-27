"""Mochat WebSocket client wrapper."""

from __future__ import annotations

import asyncio
from typing import Any, Callable

from loguru import logger
from nanobot.config.schema import MochatConfig

try:
    import socketio
    SOCKETIO_AVAILABLE = True
except ImportError:
    socketio = None
    SOCKETIO_AVAILABLE = False

try:
    import msgpack  # noqa: F401
    MSGPACK_AVAILABLE = True
except ImportError:
    MSGPACK_AVAILABLE = False


class MochatSocketClient:
    """Manages Socket.IO connection and events for Mochat."""

    def __init__(self, config: MochatConfig,
                 on_connect: Callable[[], Any],
                 on_disconnect: Callable[[], Any],
                 on_session_event: Callable[[dict[str, Any]], Any],
                 on_panel_event: Callable[[dict[str, Any]], Any],
                 on_notify: Callable[[str, dict[str, Any]], Any]):
        self.config = config
        self._socket: Any = None
        self._on_connect = on_connect
        self._on_disconnect = on_disconnect
        self._on_session_event = on_session_event
        self._on_panel_event = on_panel_event
        self._on_notify = on_notify

    async def connect(self) -> bool:
        """Connect to the Socket.IO server."""
        if not SOCKETIO_AVAILABLE:
            logger.warning("python-socketio not installed, Mochat using polling fallback")
            return False

        serializer = "default"
        if not self.config.socket_disable_msgpack:
            if MSGPACK_AVAILABLE:
                serializer = "msgpack"
            else:
                logger.warning("msgpack not installed but socket_disable_msgpack=false; using JSON")

        client = socketio.AsyncClient(
            reconnection=True,
            reconnection_attempts=self.config.max_retry_attempts or None,
            reconnection_delay=max(0.1, self.config.socket_reconnect_delay_ms / 1000.0),
            reconnection_delay_max=max(0.1, self.config.socket_max_reconnect_delay_ms / 1000.0),
            logger=False, engineio_logger=False, serializer=serializer,
        )

        @client.event
        async def connect() -> None:
            logger.info("Mochat websocket connected")
            if self._on_connect:
                await self._on_connect()

        @client.event
        async def disconnect() -> None:
            logger.warning("Mochat websocket disconnected")
            if self._on_disconnect:
                await self._on_disconnect()

        @client.event
        async def connect_error(data: Any) -> None:
            logger.error(f"Mochat websocket connect error: {data}")

        @client.on("claw.session.events")
        async def on_session_events(payload: dict[str, Any]) -> None:
            if self._on_session_event:
                await self._on_session_event(payload)

        @client.on("claw.panel.events")
        async def on_panel_events(payload: dict[str, Any]) -> None:
            if self._on_panel_event:
                await self._on_panel_event(payload)

        # Register notification handlers
        for ev in ("notify:chat.inbox.append", "notify:chat.message.add",
                   "notify:chat.message.update", "notify:chat.message.recall",
                   "notify:chat.message.delete"):
            client.on(ev, self._build_notify_handler(ev))

        socket_url = (self.config.socket_url or self.config.base_url).strip().rstrip("/")
        socket_path = (self.config.socket_path or "/socket.io").strip().lstrip("/")

        try:
            self._socket = client
            await client.connect(
                socket_url, transports=["websocket"], socketio_path=socket_path,
                auth={"token": self.config.claw_token},
                wait_timeout=max(1.0, self.config.socket_connect_timeout_ms / 1000.0),
            )
            return True
        except Exception as e:
            logger.error(f"Failed to connect Mochat websocket: {e}")
            try:
                await client.disconnect()
            except Exception:
                pass
            self._socket = None
            return False

    def _build_notify_handler(self, event_name: str):
        async def handler(payload: Any) -> None:
            if self._on_notify:
                await self._on_notify(event_name, payload)
        return handler

    async def disconnect(self) -> None:
        """Disconnect from the Socket.IO server."""
        if self._socket:
            try:
                await self._socket.disconnect()
            except Exception:
                pass
            self._socket = None

    async def call(self, event_name: str, payload: dict[str, Any], timeout: int = 10) -> dict[str, Any]:
        """Emit an event and wait for acknowledgment."""
        if not self._socket:
            return {"result": False, "message": "socket not connected"}
        try:
            raw = await self._socket.call(event_name, payload, timeout=timeout)
        except Exception as e:
            return {"result": False, "message": str(e)}
        return raw if isinstance(raw, dict) else {"result": True, "data": raw}

    @property
    def connected(self) -> bool:
        """Check if connected."""
        return self._socket is not None and self._socket.connected
