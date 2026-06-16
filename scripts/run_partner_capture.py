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
from quadro.document_sets import load_document_set, run_document_set  # noqa: E402
from quadro.env import load_dotenv  # noqa: E402
from quadro.featherless_client import featherless_status  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a single Quadro review and capture partner verifier output."
    )
    parser.add_argument(
        "--document-set",
        default="02_block_revoked_consent",
        help="document set id to run",
    )
    parser.add_argument(
        "--providers",
        nargs="+",
        choices=["aimlapi", "featherless"],
        default=["aimlapi"],
        help="partner providers to enable for this capture",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="actually call configured partner APIs",
    )
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    aimlapi = aimlapi_status()
    featherless = featherless_status()
    status = {
        "aimlapi": aimlapi.to_dict(),
        "featherless": featherless.to_dict(),
    }
    print(json.dumps({"provider_status": status}, indent=2, sort_keys=True))

    requested = set(args.providers)
    missing = []
    if "aimlapi" in requested and not aimlapi.configured:
        missing.append(f"AI/ML API: {aimlapi.reason}")
    if "featherless" in requested and not featherless.configured:
        missing.append(f"Featherless AI: {featherless.reason}")

    if missing:
        print("\nPartner capture blocked:")
        for item in missing:
            print(f"- {item}")
        raise SystemExit(2)

    if not args.live:
        print("\nDry run only. Add --live to spend partner credits.")
        return

    os.environ["QUADRO_USE_AIMLAPI"] = "1" if "aimlapi" in requested else "0"
    os.environ["QUADRO_USE_FEATHERLESS"] = (
        "1" if "featherless" in requested else "0"
    )
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    audit_dir = ROOT / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    pack = load_document_set(args.document_set)
    result = run_document_set(
        pack,
        audit_path=audit_dir / f"partner_capture_{stamp}.jsonl",
        db_path=audit_dir / f"partner_capture_{stamp}.sqlite3",
    )
    capture = {
        "captured_at_utc": stamp,
        "document_set": args.document_set,
        "providers": sorted(requested),
        "provider_status": status,
        "result_summary": _result_summary(result),
        "aimlapi_usage": result.get("aimlapi_usage"),
        "aimlapi_readout": result.get("partner_readout"),
        "featherless_usage": result.get("featherless_usage"),
        "featherless_readout": result.get("featherless_readout"),
        "full_result": result,
    }
    output_path = audit_dir / f"partner_capture_{stamp}.json"
    output_path.write_text(json.dumps(capture, indent=2, sort_keys=True), encoding="utf-8")
    print(f"\nPartner capture written: {output_path}")
    print(json.dumps(capture["result_summary"], indent=2, sort_keys=True))


def _result_summary(result: dict[str, Any]) -> dict[str, Any]:
    final_packet = result.get("final_packet", {})
    policy_state = result.get("state_path", {}).get("policy_state", {})
    evidence_state = result.get("state_path", {}).get("evidence_state", {})
    return {
        "outcome": final_packet.get("outcome"),
        "gate": final_packet.get("current_gate"),
        "recommendation": final_packet.get("recommendation"),
        "risk_level": policy_state.get("risk_level"),
        "evidence_items": len(evidence_state.get("items", [])),
        "document_set_failures": result.get("document_set", {}).get("failures", []),
        "aimlapi_readout_present": bool(result.get("partner_readout")),
        "featherless_readout_present": bool(result.get("featherless_readout")),
    }


if __name__ == "__main__":
    main()
