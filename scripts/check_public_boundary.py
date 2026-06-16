#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
PRIVATE_BOUNDARY_TERMS = ROOT / "private_raw_DO_NOT_UPLOAD" / "public_boundary_terms.txt"
FORBIDDEN_IN_CODE = [
    "model.safetensors",
    "openhermes-2.5-mistral-7b-4bit",
]


def main() -> None:
    failures: list[str] = []
    private_terms = _load_private_terms()
    forbidden_in_code = [*FORBIDDEN_IN_CODE, *private_terms]
    for path in list((ROOT / "quadro").rglob("*.py")) + list((ROOT / "app").rglob("*")):
        if path.is_dir():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for forbidden in forbidden_in_code:
            if forbidden in text:
                failures.append(f"{path}: contains protected string {forbidden!r}")
    public_paths = [ROOT / "README.md", *(ROOT / "docs" / "public").rglob("*.md")]
    for path in public_paths:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for forbidden in private_terms:
            if forbidden in text:
                failures.append(f"{path}: contains non-public wording {forbidden!r}")
    if failures:
        print("\n".join(failures))
        raise SystemExit(1)
    print("public boundary check passed")


def _load_private_terms() -> list[str]:
    if not PRIVATE_BOUNDARY_TERMS.exists():
        return []
    return [
        line.strip()
        for line in PRIVATE_BOUNDARY_TERMS.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


if __name__ == "__main__":
    main()
