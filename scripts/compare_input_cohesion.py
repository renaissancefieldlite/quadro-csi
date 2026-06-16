#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from quadro.document_sets import load_document_sets, run_document_set


def main() -> None:
    comparison = compare_document_sets()
    print(json.dumps(comparison, indent=2, sort_keys=True))


def compare_document_sets() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        for pack in load_document_sets():
            baseline = run_document_set(
                pack,
                audit_path=temp / f"{pack['id']}_baseline.jsonl",
                db_path=temp / f"{pack['id']}_baseline.sqlite3",
                use_input_cohesion=False,
            )
            stabilized = run_document_set(
                pack,
                audit_path=temp / f"{pack['id']}_stabilized.jsonl",
                db_path=temp / f"{pack['id']}_stabilized.sqlite3",
                use_input_cohesion=True,
            )
            rows.append(_compare_row(pack["id"], baseline, stabilized))
    evidence_deltas = [row["evidence_delta"] for row in rows]
    return {
        "comparison": "input_cohesion_on_vs_off",
        "summary": {
            "datasets": len(rows),
            "baseline_passed": sum(1 for row in rows if row["baseline_passed"]),
            "stabilized_passed": sum(1 for row in rows if row["stabilized_passed"]),
            "outcome_changes": sum(1 for row in rows if row["outcome_changed"]),
            "total_evidence_delta": sum(evidence_deltas),
            "average_evidence_delta": round(mean(evidence_deltas), 2)
            if evidence_deltas
            else 0,
            "cohesion_packets_added": sum(
                1 for row in rows if row["stabilized_has_cohesion"]
            ),
        },
        "rows": rows,
    }


def _compare_row(
    pack_id: str,
    baseline: dict[str, Any],
    stabilized: dict[str, Any],
) -> dict[str, Any]:
    base_packet = baseline["final_packet"]
    stable_packet = stabilized["final_packet"]
    base_evidence = len(
        baseline.get("state_path", {}).get("evidence_state", {}).get("items", [])
    )
    stable_evidence = len(
        stabilized.get("state_path", {}).get("evidence_state", {}).get("items", [])
    )
    cohesion = stabilized.get("state_path", {}).get("cohesion_state", {})
    return {
        "id": pack_id,
        "baseline_passed": not baseline["document_set"]["failures"],
        "stabilized_passed": not stabilized["document_set"]["failures"],
        "baseline_outcome": base_packet.get("outcome"),
        "stabilized_outcome": stable_packet.get("outcome"),
        "outcome_changed": base_packet.get("outcome") != stable_packet.get("outcome"),
        "baseline_gate": base_packet.get("current_gate"),
        "stabilized_gate": stable_packet.get("current_gate"),
        "baseline_evidence_items": base_evidence,
        "stabilized_evidence_items": stable_evidence,
        "evidence_delta": stable_evidence - base_evidence,
        "stabilized_has_cohesion": bool(cohesion),
        "stabilized_next_gate": cohesion.get("next_gate"),
        "stabilized_confidence": cohesion.get("confidence"),
        "active_signals": [
            name for name, active in cohesion.get("signals", {}).items() if active
        ],
    }


if __name__ == "__main__":
    main()
