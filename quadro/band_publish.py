from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .band_adapter import BandAdapter, BandSendResult
from .band_config import ROLE_ORDER, load_agent_config, missing_agent_configs

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "agent_config.yaml"

SENDER_TO_KEY = {
    "QuadroIntake": "quadro_intake",
    "QuadroEvidence": "quadro_evidence",
    "QuadroPolicy": "quadro_policy",
    "QuadroDecision": "quadro_decision",
}

EVENT_TYPES = {
    "quadro_intake": "task",
    "quadro_evidence": "tool_result",
    "quadro_policy": "thought",
    "quadro_decision": "task",
}


def publish_workflow_to_band(
    workflow: dict[str, Any],
    chat_id: str | None = None,
    live: bool | None = None,
    config_path: Path = DEFAULT_CONFIG,
) -> dict[str, Any]:
    """Publish a completed Quadro workflow into Band as agent handoff events."""

    resolved_live = _publish_enabled() if live is None else live
    resolved_chat_id = (chat_id or os.getenv("QUADRO_BAND_CHAT_ID", "")).strip()
    configs = load_agent_config(config_path)
    missing = missing_agent_configs(configs)
    result: dict[str, Any] = {
        "enabled": resolved_live,
        "ok": False,
        "mode": "live_sdk" if resolved_live else "dry_run",
        "chat_id": resolved_chat_id,
        "missing_agent_configs": missing,
        "events": [],
    }

    if workflow.get("task_mode") in {"chat_assist", "intake_assist"}:
        result["mode"] = "local_assist"
        result["blocked"] = (
            "No Band review was published because this turn answered a question "
            "or collected intake instead of running the agent review chain."
        )
        return result

    if missing:
        result["blocked"] = "Band publish requires all four remote agent configs."
        return result
    if resolved_live and not resolved_chat_id:
        result["blocked"] = "Band publish requires QUADRO_BAND_CHAT_ID."
        return result

    event_specs = _event_specs(workflow)
    if not event_specs:
        result["blocked"] = "No Quadro agent events were available to publish."
        return result

    send_ok = True
    for spec in event_specs:
        config = configs[spec["agent_key"]]
        adapter = BandAdapter(config, dry_run=not resolved_live)
        send_result = adapter.sdk_event(
            chat_id=resolved_chat_id or "dry-run-chat",
            content=spec["content"],
            message_type=spec["message_type"],
            metadata=spec["metadata"],
        )
        send_ok = send_ok and send_result.ok
        result["events"].append(_public_send_result(spec, send_result))

    result["ok"] = send_ok
    if not send_ok:
        result["blocked"] = "One or more Band events failed to publish."
    return result


def _publish_enabled() -> bool:
    return os.getenv("QUADRO_PUBLISH_TO_BAND", os.getenv("QUADRO_BAND_PUBLISH", "0")) == "1"


def _event_specs(workflow: dict[str, Any]) -> list[dict[str, Any]]:
    by_sender: dict[str, dict[str, Any]] = {}
    for event in workflow.get("transcript", []):
        sender = event.get("sender")
        if sender in SENDER_TO_KEY:
            by_sender[sender] = event

    state = workflow.get("state_path", {})
    final_packet = workflow.get("final_packet", {})
    evidence_state = state.get("evidence_state", {})
    policy_state = state.get("policy_state", {})
    evidence_count = len(evidence_state.get("items", []))
    blockers = policy_state.get("blockers", [])

    specs: list[dict[str, Any]] = []
    for sender, agent_key in SENDER_TO_KEY.items():
        event = by_sender.get(sender)
        if not event:
            continue
        content = _band_safe_content(sender, event, final_packet, evidence_count, blockers)
        specs.append(
            {
                "agent_key": agent_key,
                "sender": sender,
                "message_type": EVENT_TYPES[agent_key],
                "content": content,
                "metadata": {
                    "system": "quadro_csi",
                    "agent_key": agent_key,
                    "source": "quadro_product_ui",
                    "local_event_id": event.get("event_id"),
                    "task_id": final_packet.get("task_id"),
                    "outcome": final_packet.get("outcome"),
                    "gate": final_packet.get("current_gate"),
                    "recommendation": final_packet.get("recommendation"),
                    "consent_revision": final_packet.get("consent_revision"),
                    "evidence_count": evidence_count,
                    "risk_level": policy_state.get("risk_level"),
                    "blocker_count": len(blockers),
                },
            }
        )
    return specs


def _band_safe_content(
    sender: str,
    event: dict[str, Any],
    final_packet: dict[str, Any],
    evidence_count: int,
    blockers: list[str],
) -> str:
    if sender == "QuadroIntake":
        return "Quadro Intake framed the product UI review packet and consent scope."
    if sender == "QuadroEvidence":
        return f"Quadro Evidence Spine retrieved {evidence_count} scoped evidence item(s)."
    if sender == "QuadroPolicy":
        if blockers:
            return f"Quadro Policy/Risk found {len(blockers)} blocker(s) and held the review."
        return "Quadro Policy/Risk found no deterministic blockers."
    return (
        "Quadro Decision Packet returned "
        f"{final_packet.get('outcome', 'NEED_REVIEW')} at gate "
        f"{final_packet.get('current_gate', 'unknown')}."
    )


def _public_send_result(spec: dict[str, Any], send_result: BandSendResult) -> dict[str, Any]:
    response = send_result.response if not send_result.ok else None
    return {
        "agent": spec["agent_key"],
        "sender": spec["sender"],
        "message_type": spec["message_type"],
        "ok": send_result.ok,
        "mode": send_result.mode,
        "status_code": send_result.status_code,
        "response": response,
    }
