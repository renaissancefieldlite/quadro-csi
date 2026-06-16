#!/usr/bin/env python3
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quadro.document_sets import load_document_sets, run_document_set


def main() -> None:
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        for pack in load_document_sets():
            result = run_document_set(
                pack,
                audit_path=temp / f"{pack['id']}.jsonl",
                db_path=temp / f"{pack['id']}.sqlite3",
            )
            outcome = result["final_packet"].get("outcome")
            gate = result["final_packet"].get("current_gate")
            expected = pack.get("expected", {})
            pack_failures = result["document_set"]["failures"]
            status = "PASS" if not pack_failures else "FAIL"
            print(
                f"{status} {pack['id']} -> outcome={outcome} "
                f"gate={gate} expected={expected.get('outcome')}"
            )
            failures.extend(f"{pack['id']}: {item}" for item in pack_failures)

    if failures:
        print("\nSmoke test failures:")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)

    print("\nQuadro smoke test passed: APPROVE / SAY_NO / NEED_MORE_INFO paths work.")


if __name__ == "__main__":
    main()
