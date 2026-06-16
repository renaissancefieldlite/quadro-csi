#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from quadro.band_adapter import BandAdapter  # noqa: E402
from quadro.band_config import ROLE_ORDER, load_agent_config, missing_agent_configs  # noqa: E402
from quadro.demo import load_case, run_quadro_workflow  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare or run Quadro Band agents.")
    parser.add_argument("--chat-id", default=os.getenv("QUADRO_BAND_CHAT_ID", ""))
    parser.add_argument(
        "--create-chat",
        action="store_true",
        help="create a real Band chat room with the first configured agent",
    )
    parser.add_argument("--live", action="store_true", help="send to Band Request API")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    _load_dotenv(ROOT / ".env")
    configs = load_agent_config(ROOT / "agent_config.yaml")
    missing = missing_agent_configs(configs)
    workflow = run_quadro_workflow(case=load_case(), audit_path=None, db_path=ROOT / "audit" / "quadro_band_prep.sqlite3")

    results = {
        "mode": "live" if args.live else "dry_run",
        "chat_id": args.chat_id,
        "missing_agent_configs": missing,
        "workflow_gate": workflow["final_packet"]["current_gate"],
        "workflow_recommendation": workflow["final_packet"]["recommendation"],
        "created_chat": False,
        "participants_added": [],
        "events_prepared": [],
    }

    if args.live and missing:
        results["blocked"] = "live mode requires complete agent_config.yaml"
        _print(results, args.json)
        raise SystemExit(2)

    if args.live and not (args.chat_id or args.create_chat):
        results["blocked"] = "live mode requires --chat-id or --create-chat"
        _print(results, args.json)
        raise SystemExit(2)

    if not configs:
        results["blocked"] = "agent_config.yaml missing; copy agent_config.example.yaml first"
        _print(results, args.json)
        raise SystemExit(2)

    ordered_configs = [(key, configs[key]) for key in ROLE_ORDER if key in configs]
    chat_id = args.chat_id or "dry-run-chat"

    if args.create_chat:
        coordinator_key, coordinator_config = ordered_configs[0]
        coordinator = BandAdapter(coordinator_config, dry_run=not args.live)
        create_result = coordinator.sdk_create_chat()
        results["created_chat"] = create_result.ok
        results["create_chat_result"] = _redact_result(create_result)
        if not create_result.ok:
            results["blocked"] = "Band chat creation failed"
            _print(results, args.json)
            raise SystemExit(2)
        chat_id = _extract_id(create_result.response) or chat_id
        results["chat_id"] = chat_id

        if args.live and not chat_id:
            results["blocked"] = "Band chat creation returned no chat id"
            _print(results, args.json)
            raise SystemExit(2)

        for key, config in ordered_configs[1:]:
            add_result = coordinator.sdk_add_participant(chat_id, config.agent_id)
            results["participants_added"].append(
                {
                    "agent": key,
                    "ok": add_result.ok,
                    "mode": add_result.mode,
                    "status_code": add_result.status_code,
                    "response": add_result.response,
                }
            )

    for key, config in ordered_configs:
        adapter = BandAdapter(config, dry_run=not args.live)
        content, event_type, metadata = _agent_event_payload(key, config.name, workflow)
        send_result = adapter.sdk_event(
            chat_id=chat_id,
            content=content,
            message_type=event_type,
            metadata=metadata,
        )
        results["events_prepared"].append(
            {
                "agent": key,
                "ok": send_result.ok,
                "mode": send_result.mode,
                "status_code": send_result.status_code,
                "payload": send_result.payload,
                "response": send_result.response,
            }
        )

    _print(results, args.json)


def _print(results: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(results, indent=2, sort_keys=True))
        return
    print("Quadro Band agent preparation")
    print(f"Mode: {results['mode']}")
    print(f"Missing configs: {', '.join(results['missing_agent_configs']) or 'none'}")
    print(f"Workflow gate: {results['workflow_gate']}")
    print(f"Chat id: {results['chat_id']}")
    print(f"Created chat: {results['created_chat']}")
    print(f"Participants added: {len(results.get('participants_added', []))}")
    print(f"Events prepared: {len(results.get('events_prepared', []))}")
    if "blocked" in results:
        print(f"Blocked: {results['blocked']}")


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def _agent_event_payload(
    key: str,
    agent_name: str,
    workflow: dict,
) -> tuple[str, str, dict]:
    final_packet = workflow["final_packet"]
    state_path = workflow["state_path"]
    workflow_id = final_packet["task_id"]
    evidence_count = len(state_path["evidence_state"]["items"])
    blocking_issue_count = len(state_path["policy_state"]["blockers"])
    if key == "quadro_intake":
        return (
            "Quadro Customer Intake framed the live hackathon readiness case and consent scope.",
            "task",
            {
                "system": "quadro_csi",
                "workflow_id": workflow_id,
                "agent_name": agent_name,
                "agent_key": key,
                "gate": final_packet["current_gate"],
                "consent_revision": final_packet["consent_revision"],
            },
        )
    if key == "quadro_evidence":
        return (
            "Quadro Evidence Spine attached source-backed artifacts and local audit state.",
            "tool_result",
            {
                "system": "quadro_csi",
                "workflow_id": workflow_id,
                "agent_name": agent_name,
                "agent_key": key,
                "evidence_count": evidence_count,
                "manifest_id": state_path["evidence_state"]["manifest_id"],
            },
        )
    if key == "quadro_policy":
        return (
            "Quadro Policy Risk checked consent, scope, and escalation blockers.",
            "thought",
            {
                "system": "quadro_csi",
                "workflow_id": workflow_id,
                "agent_name": agent_name,
                "agent_key": key,
                "blocking_issue_count": blocking_issue_count,
                "risk_level": state_path["policy_state"]["risk_level"],
            },
        )
    return (
        "Quadro Decision Packet synthesized the auditable recommendation.",
        "task",
        {
            "system": "quadro_csi",
            "workflow_id": workflow_id,
            "agent_name": agent_name,
            "agent_key": key,
            "recommendation": final_packet["recommendation"],
            "required_approvals": final_packet["required_approvals"],
        },
    )


def _extract_id(value: object) -> str | None:
    if isinstance(value, dict):
        for key in ("id", "chat_id", "room_id"):
            found = value.get(key)
            if isinstance(found, str) and found:
                return found
        for child in value.values():
            found = _extract_id(child)
            if found:
                return found
    if isinstance(value, list):
        for child in value:
            found = _extract_id(child)
            if found:
                return found
    return None


def _redact_result(result) -> dict:
    return {
        "ok": result.ok,
        "mode": result.mode,
        "status_code": result.status_code,
        "payload": result.payload,
        "response": result.response,
    }


if __name__ == "__main__":
    main()
