from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .schemas import RoomEvent


class PersistentRoom:
    """Persistent local room runtime while Band credentials are pending."""

    def __init__(self, room_name: str, audit_path: Path | None = None) -> None:
        self.room_name = room_name
        self.audit_path = audit_path
        self.events: list[RoomEvent] = []
        if self.audit_path:
            self.audit_path.parent.mkdir(parents=True, exist_ok=True)

    def post_message(
        self,
        sender: str,
        content: str,
        mentions: list[str] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> RoomEvent:
        return self._append(
            RoomEvent.create(
                kind="message",
                sender=sender,
                mentions=mentions,
                content=content,
                payload=payload,
            )
        )

    def post_event(
        self,
        sender: str,
        kind: str,
        content: str,
        mentions: list[str] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> RoomEvent:
        return self._append(
            RoomEvent.create(
                kind=kind,
                sender=sender,
                mentions=mentions,
                content=content,
                payload=payload,
            )
        )

    def context_for(self, agent_name: str) -> list[RoomEvent]:
        return [
            event
            for event in self.events
            if event.sender == agent_name or agent_name in event.mentions
        ]

    def transcript(self) -> list[dict[str, Any]]:
        return [event.to_dict() for event in self.events]

    def _append(self, event: RoomEvent) -> RoomEvent:
        self.events.append(event)
        if self.audit_path:
            with self.audit_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(asdict(event), sort_keys=True) + "\n")
        return event


LocalBandRoom = PersistentRoom
