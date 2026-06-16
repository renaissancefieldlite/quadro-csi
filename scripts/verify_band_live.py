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


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate live Band remote agents.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    _load_dotenv(ROOT / ".env")
    configs = load_agent_config(ROOT / "agent_config.yaml")
    missing = missing_agent_configs(configs)
    results = {
        "sdk": _sdk_status(),
        "missing_agent_configs": missing,
        "agents": [],
    }

    if missing:
        results["blocked"] = "missing Band agent configs"
        _print(results, args.json)
        raise SystemExit(2)

    for key in ROLE_ORDER:
        config = configs[key]
        adapter = BandAdapter(config, dry_run=False)
        result = adapter.sdk_identity()
        identity = result.response if isinstance(result.response, dict) else {}
        results["agents"].append(
            {
                "agent": key,
                "ok": result.ok,
                "mode": result.mode,
                "status_code": result.status_code,
                "identity_name": identity.get("name"),
                "identity_id_matches": identity.get("id") == config.agent_id,
                "response": result.response if not result.ok else None,
            }
        )

    if not all(agent["ok"] for agent in results["agents"]):
        results["blocked"] = "one or more Band Agent API identity checks failed"
        _print(results, args.json)
        raise SystemExit(2)

    _print(results, args.json)


def _sdk_status() -> str:
    try:
        import thenvoi  # noqa: F401
        import thenvoi_rest  # noqa: F401
    except ImportError as exc:
        return f"missing: {exc}"
    return "available"


def _print(results: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(results, indent=2, sort_keys=True))
        return
    print("Band live check")
    print(f"SDK: {results['sdk']}")
    print(f"Missing configs: {', '.join(results['missing_agent_configs']) or 'none'}")
    for agent in results["agents"]:
        print(
            f"{agent['agent']}: ok={agent['ok']} "
            f"status={agent['status_code']} "
            f"name={agent['identity_name']} "
            f"id_match={agent['identity_id_matches']}"
        )
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


if __name__ == "__main__":
    main()
