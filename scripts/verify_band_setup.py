#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from quadro.band_config import load_agent_config, missing_agent_configs  # noqa: E402

REQUIRED_ENV = [
    "THENVOI_REST_URL",
    "THENVOI_WS_URL",
]

REQUIRED_AGENT_NAMES = [
    "quadro_intake",
    "quadro_evidence",
    "quadro_policy",
    "quadro_decision",
]


def main() -> None:
    _load_dotenv(ROOT / ".env")
    missing_env = [name for name in REQUIRED_ENV if not os.getenv(name)]
    missing_config = missing_agent_configs(load_agent_config(ROOT / "agent_config.yaml"))

    try:
        import thenvoi  # noqa: F401
    except ImportError:
        sdk_status = "PENDING: install with uv sync --extra band"
    else:
        sdk_status = "AVAILABLE"

    print("Band setup check")
    print(f"SDK: {sdk_status}")
    print(f"Missing env: {', '.join(missing_env) if missing_env else 'none'}")
    print(
        "Missing agent config: "
        f"{', '.join(missing_config) if missing_config else 'none'}"
    )

    if missing_env or missing_config or sdk_status.startswith("PENDING"):
        raise SystemExit(2)


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


if __name__ == "__main__":
    main()
