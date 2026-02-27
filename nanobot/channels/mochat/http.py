"""Mochat HTTP client wrapper."""

from __future__ import annotations

import httpx
from typing import Any

from nanobot.config.schema import MochatConfig
from nanobot.channels.mochat.utils import str_field


class MochatHTTPClient:
    """Handles HTTP communication with the Mochat API."""

    def __init__(self, config: MochatConfig):
        self.config = config
        self._http: httpx.AsyncClient | None = None

    async def start(self) -> None:
        """Initialize the HTTP client."""
        self._http = httpx.AsyncClient(timeout=30.0)

    async def stop(self) -> None:
        """Close the HTTP client."""
        if self._http:
            await self._http.aclose()
            self._http = None

    async def post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Perform a POST request and return JSON response."""
        if not self._http:
            raise RuntimeError("Mochat HTTP client not initialized")

        url = f"{self.config.base_url.strip().rstrip('/')}{path}"
        response = await self._http.post(url, headers={
            "Content-Type": "application/json",
            "X-Claw-Token": self.config.claw_token,
        }, json=payload)

        if not response.is_success:
            raise RuntimeError(f"Mochat HTTP {response.status_code}: {response.text[:200]}")

        try:
            parsed = response.json()
        except Exception:
            parsed = response.text

        if isinstance(parsed, dict) and isinstance(parsed.get("code"), int):
            if parsed["code"] != 200:
                msg = str(parsed.get("message") or parsed.get("name") or "request failed")
                raise RuntimeError(f"Mochat API error: {msg} (code={parsed['code']})")
            data = parsed.get("data")
            return data if isinstance(data, dict) else {}

        return parsed if isinstance(parsed, dict) else {}

    async def send_message(self, target_id: str, content: str, reply_to: str | None,
                          is_panel: bool, group_id: str | None = None) -> dict[str, Any]:
        """Send a message to a session or panel."""
        if is_panel:
            return await self._api_send(
                "/api/claw/groups/panels/send", "panelId", target_id,
                content, reply_to, group_id
            )
        else:
            return await self._api_send(
                "/api/claw/sessions/send", "sessionId", target_id,
                content, reply_to
            )

    async def _api_send(self, path: str, id_key: str, id_val: str,
                       content: str, reply_to: str | None,
                       group_id: str | None = None) -> dict[str, Any]:
        """Unified send helper."""
        body: dict[str, Any] = {id_key: id_val, "content": content}
        if reply_to:
            body["replyTo"] = reply_to
        if group_id:
            body["groupId"] = group_id
        return await self.post_json(path, body)

    async def list_sessions(self) -> list[dict[str, str]]:
        """Fetch list of active sessions."""
        try:
            response = await self.post_json("/api/claw/sessions/list", {})
            sessions = response.get("sessions")
            if not isinstance(sessions, list):
                return []

            results = []
            for s in sessions:
                if not isinstance(s, dict):
                    continue
                sid = str_field(s, "sessionId")
                if sid:
                    results.append(s)
            return results
        except Exception:
            return []

    async def list_panels(self) -> list[dict[str, Any]]:
        """Fetch list of available panels."""
        try:
            response = await self.post_json("/api/claw/groups/get", {})
            raw_panels = response.get("panels")
            if not isinstance(raw_panels, list):
                return []
            return [p for p in raw_panels if isinstance(p, dict)]
        except Exception:
            return []

    async def watch_session(self, session_id: str, cursor: int,
                           timeout_ms: int, limit: int) -> dict[str, Any]:
        """Watch session events (fallback polling)."""
        return await self.post_json("/api/claw/sessions/watch", {
            "sessionId": session_id,
            "cursor": cursor,
            "timeoutMs": timeout_ms,
            "limit": limit,
        })

    async def poll_panel_messages(self, panel_id: str, limit: int) -> dict[str, Any]:
        """Poll recent messages from a panel."""
        return await self.post_json("/api/claw/groups/panels/messages", {
            "panelId": panel_id,
            "limit": limit,
        })
