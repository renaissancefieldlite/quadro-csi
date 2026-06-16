from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .schemas import ConsentState, utc_now


@dataclass
class StatePath:
    cohesion_state: dict[str, Any] = field(default_factory=dict)
    task_state: dict[str, Any] = field(default_factory=dict)
    consent_state: dict[str, Any] = field(default_factory=dict)
    evidence_state: dict[str, Any] = field(default_factory=dict)
    policy_state: dict[str, Any] = field(default_factory=dict)
    decision_state: dict[str, Any] = field(default_factory=dict)
    revision_state: list[dict[str, Any]] = field(default_factory=list)

    def checkpoint(self, lane: str, value: Any) -> None:
        if lane == "revision_state":
            self.revision_state.append(_pack(value))
            return
        if not hasattr(self, lane):
            raise ValueError(f"unknown state lane: {lane}")
        setattr(self, lane, _pack(value))

    def revisit_consent(self, consent: ConsentState, reason: str) -> None:
        self.consent_state = _pack(consent)
        self.revision_state.append(
            {
                "created_at": utc_now(),
                "kind": "consent_revision",
                "revision": consent.revision,
                "reason": reason,
                "scope": consent.scope,
                "status": consent.status,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _pack(value: Any) -> dict[str, Any]:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, dict):
        return value
    return {"value": value}
