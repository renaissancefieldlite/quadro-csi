from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


ConsentStatus = Literal["granted", "narrowed", "revoked", "needs_review"]
RiskLevel = Literal["low", "medium", "high"]


@dataclass
class ConsentState:
    status: ConsentStatus
    actor: str
    scope: list[str]
    constraints: list[str] = field(default_factory=list)
    revision: int = 0
    reason: str = "initial consent"

    def narrowed(self, new_scope: list[str], reason: str) -> "ConsentState":
        return ConsentState(
            status="narrowed",
            actor=self.actor,
            scope=new_scope,
            constraints=self.constraints + ["prior approval must be re-checked"],
            revision=self.revision + 1,
            reason=reason,
        )


@dataclass
class TaskFrame:
    task_id: str
    title: str
    requester: str
    business_goal: str
    requested_action: str
    consent: ConsentState
    open_questions: list[str] = field(default_factory=list)


@dataclass
class EvidenceItem:
    item_id: str
    title: str
    source: str
    summary: str
    scope_tags: list[str]
    support_status: str = "real_source_packet"


@dataclass
class EvidenceManifest:
    manifest_id: str
    task_id: str
    items: list[EvidenceItem]
    missing_items: list[str]
    valid_scope: list[str]


@dataclass
class PolicyRead:
    policy_id: str
    task_id: str
    consent_revision: int
    risk_level: RiskLevel
    blockers: list[str]
    escalation_required: bool
    recommendation: str


@dataclass
class DecisionPacket:
    packet_id: str
    task_id: str
    consent_revision: int
    outcome: str
    recommendation: str
    rationale: list[str]
    required_approvals: list[str]
    revision_history: list[str]
    current_gate: str


@dataclass
class RoomEvent:
    event_id: str
    created_at: str
    kind: str
    sender: str
    mentions: list[str]
    content: str
    payload: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        kind: str,
        sender: str,
        content: str,
        mentions: list[str] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> "RoomEvent":
        return cls(
            event_id=new_id("evt"),
            created_at=utc_now(),
            kind=kind,
            sender=sender,
            mentions=mentions or [],
            content=content,
            payload=payload or {},
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def to_dict(value: Any) -> dict[str, Any]:
    return asdict(value)
