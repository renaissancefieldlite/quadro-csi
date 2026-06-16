from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from .demo import DEFAULT_DB, load_case, run_quadro_workflow

ROOT = Path(__file__).resolve().parents[1]
DOCUMENT_SET_DIR = ROOT / "data" / "evaluation_sets"


def load_document_sets(directory: Path = DOCUMENT_SET_DIR) -> list[dict[str, Any]]:
    packs: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*/manifest.json")):
        packs.append(load_document_set(path))
    return packs


def load_document_set(path_or_id: Path | str) -> dict[str, Any]:
    path = _resolve_document_set_path(path_or_id)
    with path.open("r", encoding="utf-8") as handle:
        pack = json.load(handle)
    pack.setdefault("id", path.stem)
    pack["documents"] = _load_dataset_documents(path.parent, pack.get("documents", []))
    return pack


def document_set_summaries() -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for pack in load_document_sets():
        summaries.append(
            {
                "id": pack["id"],
                "title": pack["title"],
                "description": pack.get("description", ""),
                "track": pack.get("track", "Track 3"),
                "expected": pack.get("expected", {}),
            }
        )
    return summaries


def run_document_set(
    pack: dict[str, Any],
    audit_path: Path | None = None,
    db_path: Path | None = None,
    use_input_cohesion: bool = True,
) -> dict[str, Any]:
    case = load_case()
    _deep_merge(case, copy.deepcopy(pack.get("case_overrides", {})))
    result = run_quadro_workflow(
        case=case,
        audit_path=audit_path,
        db_path=db_path or DEFAULT_DB,
        revisit=bool(pack.get("revisit", False)),
        operator_message=pack.get("operator_message", ""),
        uploaded_docs=pack.get("documents", []),
        use_input_cohesion=use_input_cohesion,
    )
    result["document_set"] = {
        "id": pack["id"],
        "title": pack["title"],
        "expected": pack.get("expected", {}),
        "failures": validate_document_set(result, pack.get("expected", {})),
    }
    return result


def validate_document_set(result: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    final_packet = result.get("final_packet", {})
    policy_state = result.get("state_path", {}).get("policy_state", {})

    _expect_equal(
        failures,
        "gate",
        final_packet.get("current_gate"),
        expected.get("gate"),
    )
    _expect_equal(
        failures,
        "outcome",
        final_packet.get("outcome"),
        expected.get("outcome"),
    )
    _expect_equal(
        failures,
        "recommendation",
        final_packet.get("recommendation"),
        expected.get("recommendation"),
    )
    _expect_equal(
        failures,
        "risk_level",
        policy_state.get("risk_level"),
        expected.get("risk_level"),
    )

    for blocker in expected.get("blockers_contain", []):
        if not any(blocker in item for item in policy_state.get("blockers", [])):
            failures.append(f"missing blocker containing {blocker!r}")

    if expected.get("requires_revision_history") and not final_packet.get(
        "revision_history"
    ):
        failures.append("missing revision history")

    minimum_evidence = expected.get("minimum_evidence_items")
    if minimum_evidence is not None:
        count = len(result.get("state_path", {}).get("evidence_state", {}).get("items", []))
        if count < int(minimum_evidence):
            failures.append(f"evidence count {count} below {minimum_evidence}")

    return failures


def _resolve_document_set_path(path_or_id: Path | str) -> Path:
    path = Path(path_or_id)
    if path.exists():
        return path
    candidate = DOCUMENT_SET_DIR / str(path_or_id) / "manifest.json"
    if candidate.exists():
        return candidate
    raise FileNotFoundError(f"Unknown Quadro document set: {path_or_id}")


def _load_dataset_documents(
    dataset_dir: Path,
    document_specs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    for index, spec in enumerate(document_specs, start=1):
        relative_path = Path(spec["path"])
        path = (dataset_dir / relative_path).resolve()
        if not path.is_relative_to(dataset_dir.resolve()):
            raise ValueError(f"Dataset document escapes dataset directory: {relative_path}")
        body = path.read_text(encoding="utf-8")
        documents.append(
            {
                "title": spec.get("title") or path.stem.replace("_", " ").title(),
                "body": body,
                "scope_tags": list(spec.get("scope_tags", [])),
                "source_label": str(path.relative_to(ROOT)),
                "document_kind": spec.get("kind", path.suffix.lstrip(".") or "document"),
            }
        )
    return documents


def _deep_merge(target: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_merge(target[key], value)
        else:
            target[key] = value
    return target


def _expect_equal(
    failures: list[str],
    label: str,
    actual: Any,
    expected: Any,
) -> None:
    if expected is None:
        return
    if actual != expected:
        failures.append(f"{label} expected {expected!r}, got {actual!r}")
