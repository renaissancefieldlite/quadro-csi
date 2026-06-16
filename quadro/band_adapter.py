from __future__ import annotations

import asyncio
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from .band_config import RemoteAgentConfig


@dataclass
class BandSendResult:
    ok: bool
    mode: str
    status_code: int | None
    payload: dict[str, Any]
    response: dict[str, Any] | str | None


class BandAdapter:
    """Thin Request API adapter for Quadro Band messages/events."""

    def __init__(
        self,
        agent: RemoteAgentConfig,
        rest_url: str | None = None,
        dry_run: bool = True,
    ) -> None:
        self.agent = agent
        self.rest_url = (rest_url or os.getenv("THENVOI_REST_URL") or "https://app.band.ai/").rstrip("/")
        self.dry_run = dry_run

    def message(
        self,
        chat_id: str,
        content: str,
        mentions: list[str] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> BandSendResult:
        body = {
            "content": content,
            "mentions": mentions or [],
            "metadata": {
                "system": "quadro_csi",
                "role": self.agent.role,
                "payload": payload or {},
            },
        }
        return self._post(f"/api/v1/agent/chats/{chat_id}/messages", body)

    def event(
        self,
        chat_id: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> BandSendResult:
        body = {
            "type": event_type,
            "payload": {
                "system": "quadro_csi",
                "role": self.agent.role,
                **payload,
            },
        }
        return self._post(f"/api/v1/agent/chats/{chat_id}/events", body)

    def sdk_identity(self) -> BandSendResult:
        """Validate this agent through the installed Band/Thenvoi SDK."""
        return asyncio.run(self._sdk_identity())

    def sdk_create_chat(self) -> BandSendResult:
        """Create a Band chat room through the generated SDK client."""
        return asyncio.run(self._sdk_create_chat())

    def sdk_add_participant(self, chat_id: str, participant_id: str) -> BandSendResult:
        """Add a participant to a Band chat room through the SDK client."""
        return asyncio.run(self._sdk_add_participant(chat_id, participant_id))

    def sdk_event(
        self,
        chat_id: str,
        content: str,
        message_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> BandSendResult:
        """Post a Band event through the generated SDK client."""
        return asyncio.run(self._sdk_event(chat_id, content, message_type, metadata))

    async def _sdk_identity(self) -> BandSendResult:
        if self.dry_run:
            return BandSendResult(
                ok=True,
                mode="dry_run",
                status_code=None,
                payload={"agent_id": self.agent.agent_id},
                response="dry run: no network request sent",
            )
        try:
            from thenvoi.client.rest import DEFAULT_REQUEST_OPTIONS
            from thenvoi_rest import AsyncRestClient
            from thenvoi_rest.core.api_error import ApiError
        except ImportError as exc:
            return self._sdk_import_error(exc)

        client = AsyncRestClient(api_key=self.agent.api_key, base_url=self.rest_url)
        try:
            response = await client.agent_api_identity.get_agent_me(
                request_options=DEFAULT_REQUEST_OPTIONS
            )
            data = getattr(response, "data", None)
            return BandSendResult(
                ok=True,
                mode="live_sdk",
                status_code=200,
                payload={"agent_id": self.agent.agent_id},
                response=_safe_model_dump(data),
            )
        except ApiError as exc:
            return self._sdk_api_error(exc, {"agent_id": self.agent.agent_id})

    async def _sdk_create_chat(self) -> BandSendResult:
        if self.dry_run:
            return BandSendResult(
                ok=True,
                mode="dry_run",
                status_code=None,
                payload={"chat": {"task_id": None}},
                response="dry run: no network request sent",
            )
        try:
            from thenvoi.client.rest import DEFAULT_REQUEST_OPTIONS
            from thenvoi_rest import AsyncRestClient, ChatRoomRequest
            from thenvoi_rest.core.api_error import ApiError
        except ImportError as exc:
            return self._sdk_import_error(exc)

        client = AsyncRestClient(api_key=self.agent.api_key, base_url=self.rest_url)
        payload = {"chat": {"task_id": None}}
        try:
            response = await client.agent_api_chats.create_agent_chat(
                chat=ChatRoomRequest(task_id=None),
                request_options=DEFAULT_REQUEST_OPTIONS,
            )
            return BandSendResult(
                ok=True,
                mode="live_sdk",
                status_code=200,
                payload=payload,
                response=_safe_model_dump(getattr(response, "data", response)),
            )
        except ApiError as exc:
            return self._sdk_api_error(exc, payload)

    async def _sdk_add_participant(
        self, chat_id: str, participant_id: str
    ) -> BandSendResult:
        if self.dry_run:
            return BandSendResult(
                ok=True,
                mode="dry_run",
                status_code=None,
                payload={"participant": {"participant_id": participant_id, "role": "member"}},
                response="dry run: no network request sent",
            )
        try:
            from thenvoi.client.rest import DEFAULT_REQUEST_OPTIONS
            from thenvoi_rest import AsyncRestClient, ParticipantRequest
            from thenvoi_rest.core.api_error import ApiError
        except ImportError as exc:
            return self._sdk_import_error(exc)

        client = AsyncRestClient(api_key=self.agent.api_key, base_url=self.rest_url)
        payload = {"participant": {"participant_id": participant_id, "role": "member"}}
        try:
            response = await client.agent_api_participants.add_agent_chat_participant(
                chat_id,
                participant=ParticipantRequest(
                    participant_id=participant_id,
                    role="member",
                ),
                request_options=DEFAULT_REQUEST_OPTIONS,
            )
            return BandSendResult(
                ok=True,
                mode="live_sdk",
                status_code=200,
                payload=payload,
                response=_safe_model_dump(getattr(response, "data", response)),
            )
        except ApiError as exc:
            return self._sdk_api_error(exc, payload)

    async def _sdk_event(
        self,
        chat_id: str,
        content: str,
        message_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> BandSendResult:
        body = {
            "event": {
                "content": content,
                "message_type": message_type,
                "metadata": metadata or {},
            }
        }
        if self.dry_run:
            return BandSendResult(
                ok=True,
                mode="dry_run",
                status_code=None,
                payload=body,
                response="dry run: no network request sent",
            )
        try:
            from thenvoi.client.rest import DEFAULT_REQUEST_OPTIONS
            from thenvoi_rest import AsyncRestClient, ChatEventRequest
            from thenvoi_rest.core.api_error import ApiError
        except ImportError as exc:
            return self._sdk_import_error(exc)

        client = AsyncRestClient(api_key=self.agent.api_key, base_url=self.rest_url)
        try:
            response = await client.agent_api_events.create_agent_chat_event(
                chat_id,
                event=ChatEventRequest(
                    content=content,
                    message_type=message_type,
                    metadata=metadata or {},
                ),
                request_options=DEFAULT_REQUEST_OPTIONS,
            )
            return BandSendResult(
                ok=True,
                mode="live_sdk",
                status_code=200,
                payload=body,
                response=_safe_model_dump(getattr(response, "data", response)),
            )
        except ApiError as exc:
            return self._sdk_api_error(exc, body)

    @staticmethod
    def _sdk_import_error(exc: ImportError) -> BandSendResult:
        return BandSendResult(
            ok=False,
            mode="live_sdk",
            status_code=None,
            payload={},
            response=f"Band SDK import failed: {exc}",
        )

    @staticmethod
    def _sdk_api_error(exc: Any, payload: dict[str, Any]) -> BandSendResult:
        return BandSendResult(
            ok=False,
            mode="live_sdk",
            status_code=getattr(exc, "status_code", None),
            payload=payload,
            response=str(exc),
        )

    def _post(self, path: str, body: dict[str, Any]) -> BandSendResult:
        if self.dry_run:
            return BandSendResult(
                ok=True,
                mode="dry_run",
                status_code=None,
                payload=body,
                response="dry run: no network request sent",
            )
        request = urllib.request.Request(
            f"{self.rest_url}{path}",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "X-API-Key": self.agent.api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read().decode("utf-8")
                try:
                    parsed: dict[str, Any] | str = json.loads(raw) if raw else {}
                except json.JSONDecodeError:
                    parsed = raw
                return BandSendResult(
                    ok=200 <= response.status < 300,
                    mode="live",
                    status_code=response.status,
                    payload=body,
                    response=parsed,
                )
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            return BandSendResult(
                ok=False,
                mode="live",
                status_code=exc.code,
                payload=body,
                response=error_body,
            )


def _safe_model_dump(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "dict"):
        return value.dict()
    return value
