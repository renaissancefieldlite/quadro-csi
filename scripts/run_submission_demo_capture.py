#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from quadro.aimlapi_client import aimlapi_status  # noqa: E402
from quadro.aimlapi_client import partner_summary_result  # noqa: E402
from quadro.band_publish import publish_workflow_to_band  # noqa: E402
from quadro.document_sets import load_document_set, run_document_set  # noqa: E402
from quadro.demo import _partner_prompt  # noqa: E402
from quadro.env import load_dotenv  # noqa: E402
from quadro.featherless_client import featherless_status  # noqa: E402
from quadro.featherless_client import featherless_summary_result  # noqa: E402


DEFAULT_DOCUMENT_SET = "02_block_revoked_consent"


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run Quadro's full submission demo capture: local agent chain, "
            "Band publish, partner verifier, and public proof summary."
        )
    )
    parser.add_argument(
        "--document-set",
        default=DEFAULT_DOCUMENT_SET,
        help="evaluation document set id to use for the demo",
    )
    parser.add_argument(
        "--providers",
        nargs="+",
        choices=["aimlapi", "featherless"],
        default=["featherless"],
        help="partner verifier providers to call during this capture",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="call live Band and partner providers",
    )
    parser.add_argument(
        "--no-band",
        action="store_true",
        help="skip live Band publish and capture it as disabled",
    )
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    providers = set(args.providers)
    provider_status = {
        "aimlapi": aimlapi_status().to_dict(),
        "featherless": featherless_status().to_dict(),
    }
    _fail_if_requested_provider_missing(providers, provider_status)

    os.environ["QUADRO_USE_AIMLAPI"] = "0"
    os.environ["QUADRO_USE_FEATHERLESS"] = "0"

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    audit_dir = ROOT / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)

    pack = load_document_set(args.document_set)
    workflow = run_document_set(
        pack,
        audit_path=audit_dir / f"submission_demo_{stamp}.jsonl",
        db_path=audit_dir / f"submission_demo_{stamp}.sqlite3",
    )
    band_publish = publish_workflow_to_band(
        workflow,
        live=args.live and not args.no_band,
    )
    workflow["band_publish"] = band_publish
    partner_capture = _partner_capture(workflow, providers, args.live)
    summary = _summary(workflow)
    summary["aimlapi_readout_present"] = bool(partner_capture["aimlapi_readout"])
    summary["featherless_readout_present"] = bool(partner_capture["featherless_readout"])

    capture = {
        "captured_at_utc": stamp,
        "document_set": args.document_set,
        "live": args.live,
        "providers_requested": sorted(providers),
        "provider_status": provider_status,
        "summary": summary,
        "band_publish": band_publish,
        "aimlapi_usage": partner_capture["aimlapi_usage"],
        "aimlapi_readout": partner_capture["aimlapi_readout"],
        "featherless_usage": partner_capture["featherless_usage"],
        "featherless_readout": partner_capture["featherless_readout"],
        "partner_errors": partner_capture["partner_errors"],
        "full_result": workflow,
    }

    output_path = audit_dir / f"submission_demo_{stamp}.json"
    output_path.write_text(json.dumps(capture, indent=2, sort_keys=True), encoding="utf-8")
    latest_path = audit_dir / "submission_demo_latest.json"
    latest_path.write_text(json.dumps(capture, indent=2, sort_keys=True), encoding="utf-8")

    proof_path = ROOT / "docs" / "public" / "SUBMISSION_DEMO_PROOF.md"
    proof_path.write_text(_public_proof(capture, output_path), encoding="utf-8")

    print(json.dumps(capture["summary"], indent=2, sort_keys=True))
    print(f"\nCapture JSON: {output_path}")
    print(f"Latest JSON: {latest_path}")
    print(f"Public proof: {proof_path}")

    if capture["summary"]["document_set_failures"]:
        raise SystemExit(1)
    if args.live and not band_publish.get("ok"):
        raise SystemExit(1)


def _fail_if_requested_provider_missing(
    providers: set[str],
    provider_status: dict[str, dict[str, Any]],
) -> None:
    missing = []
    for provider in providers:
        status = provider_status[provider]
        if not status["configured"]:
            missing.append(f"{provider}: {status['reason']}")
    if missing:
        print("Submission capture blocked by missing provider configuration:")
        for item in missing:
            print(f"- {item}")
        raise SystemExit(2)


def _summary(workflow: dict[str, Any]) -> dict[str, Any]:
    final_packet = workflow.get("final_packet", {})
    state = workflow.get("state_path", {})
    policy_state = state.get("policy_state", {})
    evidence_state = state.get("evidence_state", {})
    cohesion_state = state.get("cohesion_state", {})
    band_publish = workflow.get("band_publish", {})
    return {
        "outcome": final_packet.get("outcome"),
        "gate": final_packet.get("current_gate"),
        "recommendation": final_packet.get("recommendation"),
        "risk_level": policy_state.get("risk_level"),
        "evidence_items": len(evidence_state.get("items", [])),
        "input_cohesion_status": cohesion_state.get("status"),
        "input_cohesion_next_gate": cohesion_state.get("next_gate"),
        "document_set_failures": workflow.get("document_set", {}).get("failures", []),
        "band_ok": bool(band_publish.get("ok")),
        "band_mode": band_publish.get("mode"),
        "band_event_count": len(band_publish.get("events", [])),
        "featherless_readout_present": False,
        "aimlapi_readout_present": False,
    }


def _partner_capture(
    workflow: dict[str, Any],
    providers: set[str],
    live: bool,
) -> dict[str, Any]:
    capture: dict[str, Any] = {
        "aimlapi_usage": None,
        "aimlapi_readout": None,
        "featherless_usage": None,
        "featherless_readout": None,
        "partner_errors": {},
    }
    if not live:
        return capture

    prompt = _partner_prompt(workflow.get("state_path", {}))
    if "aimlapi" in providers:
        try:
            result = partner_summary_result(prompt)
            capture["aimlapi_usage"] = result.to_dict()
            capture["aimlapi_readout"] = result.content
        except Exception as exc:  # Provider failures are capture evidence.
            capture["partner_errors"]["aimlapi"] = str(exc)

    if "featherless" in providers:
        try:
            result = featherless_summary_result(prompt)
            capture["featherless_usage"] = result.to_dict()
            capture["featherless_readout"] = result.content
        except Exception as exc:  # Provider failures are capture evidence.
            capture["partner_errors"]["featherless"] = str(exc)
    return capture


def _public_proof(capture: dict[str, Any], output_path: Path) -> str:
    summary = capture["summary"]
    featherless_usage = capture.get("featherless_usage") or {}
    featherless_tokens = (
        featherless_usage.get("usage", {}).get("total_tokens")
        if isinstance(featherless_usage.get("usage"), dict)
        else None
    )
    featherless_model = featherless_usage.get("model") if featherless_usage else None
    readout = capture.get("featherless_readout") or "not captured"
    aimlapi_usage = capture.get("aimlapi_usage") or {}
    aimlapi_tokens = (
        aimlapi_usage.get("usage", {}).get("total_tokens")
        if isinstance(aimlapi_usage.get("usage"), dict)
        else None
    )
    aimlapi_model = aimlapi_usage.get("model") if aimlapi_usage else None
    aimlapi_readout = capture.get("aimlapi_readout") or "not captured"
    partner_errors = capture.get("partner_errors", {})
    provider_status = capture.get("provider_status", {})
    aimlapi_status = provider_status.get("aimlapi", {})
    aimlapi_gate_note = (
        "AI/ML API was captured in this integrated proof after `AIMLAPI_KEY` "
        "and `AIMLAPI_MODEL` were configured."
        if capture.get("aimlapi_readout")
        else (
            "AI/ML API should be captured only after `AIMLAPI_KEY` and "
            "`AIMLAPI_MODEL` are configured."
        )
    )
    return f"""# Submission Demo Proof

Generated by:

```bash
.venv/bin/python scripts/run_submission_demo_capture.py --providers {' '.join(capture['providers_requested'])} --live
```

Captured artifact:

```text
{output_path}
```

## Integrated Demo Result

| Lane | Result |
| --- | --- |
| Document set | `{capture['document_set']}` |
| Quadro outcome | `{summary['outcome']}` |
| Gate | `{summary['gate']}` |
| Recommendation | `{summary['recommendation']}` |
| Risk | `{summary['risk_level']}` |
| Evidence items | `{summary['evidence_items']}` |
| Input cohesion | `{summary['input_cohesion_status']}` -> `{summary['input_cohesion_next_gate']}` |
| Band publish | `{summary['band_ok']}` / `{summary['band_event_count']}` events |
| Featherless verifier | `{bool(capture.get('featherless_readout'))}` |
| AI/ML API verifier | `{bool(capture.get('aimlapi_readout'))}` |

## Featherless Verifier

```text
Model: {featherless_model or 'not captured'}
Usage: {featherless_tokens if featherless_tokens is not None else 'not returned'} total tokens
```

```text
{readout}
```

## AI/ML API Verifier

```text
Model: {aimlapi_model or 'not captured'}
Usage: {aimlapi_tokens if aimlapi_tokens is not None else 'not returned'} total tokens
```

```text
{aimlapi_readout}
```

## Partner Errors

```text
{json.dumps(partner_errors, indent=2, sort_keys=True)}
```

## AI/ML API Gate

```text
Configured: {aimlapi_status.get('configured')}
Reason: {aimlapi_status.get('reason')}
```

{aimlapi_gate_note}
"""


if __name__ == "__main__":
    main()
