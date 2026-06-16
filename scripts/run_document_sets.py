#!/usr/bin/env python3
from pathlib import Path
import json
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quadro.document_sets import load_document_set, load_document_sets, run_document_set


def main() -> None:
    packs = (
        [load_document_set(sys.argv[1])]
        if len(sys.argv) > 1
        else load_document_sets()
    )
    results = []
    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        for pack in packs:
            result = run_document_set(
                pack,
                audit_path=temp / f"{pack['id']}.jsonl",
                db_path=temp / f"{pack['id']}.sqlite3",
            )
            summary = {
                "id": pack["id"],
                "title": pack["title"],
                "outcome": result["final_packet"].get("outcome"),
                "gate": result["final_packet"]["current_gate"],
                "recommendation": result["final_packet"]["recommendation"],
                "risk_level": result["state_path"]["policy_state"].get("risk_level"),
                "evidence_items": len(result["state_path"]["evidence_state"].get("items", [])),
                "failures": result["document_set"]["failures"],
            }
            results.append(summary)

    print(json.dumps({"document_sets": results}, indent=2, sort_keys=True))
    if any(item["failures"] for item in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
