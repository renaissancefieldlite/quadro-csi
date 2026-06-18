#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> int:
    if sys.version_info < (3, 11):
        print("Quadro requires Python 3.11 or newer.", file=sys.stderr)
        return 2

    sys.path.insert(0, str(ROOT))

    try:
        from quadro.document_sets import load_document_sets, run_document_set
    except ModuleNotFoundError as exc:
        print(
            "Could not import Quadro. Run this from the repository root, or install "
            "with: python -m pip install -r requirements.txt",
            file=sys.stderr,
        )
        print(f"Import error: {exc}", file=sys.stderr)
        return 2

    results = []
    failures = []
    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        for pack in load_document_sets():
            result = run_document_set(
                pack,
                audit_path=temp / f"{pack['id']}.jsonl",
                db_path=temp / f"{pack['id']}.sqlite3",
            )
            summary = {
                "id": pack["id"],
                "title": pack["title"],
                "expected": pack.get("expected", {}).get("outcome"),
                "outcome": result["final_packet"].get("outcome"),
                "gate": result["final_packet"].get("current_gate"),
                "risk_level": result["state_path"]["policy_state"].get("risk_level"),
                "failures": result["document_set"]["failures"],
            }
            results.append(summary)
            failures.extend(f"{pack['id']}: {item}" for item in summary["failures"])

    print(json.dumps({"document_sets": results}, indent=2, sort_keys=True))
    if failures:
        print("\nQuadro demo failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("\nQuadro demo passed: all acceptance sets returned expected outcomes.")
    print("Launch the UI with: python -m quadro.server")
    print("Then open: http://127.0.0.1:8867")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
