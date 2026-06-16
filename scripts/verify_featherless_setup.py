#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from quadro.env import load_dotenv  # noqa: E402
from quadro.featherless_client import (  # noqa: E402
    featherless_status,
    featherless_summary_result,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify Quadro Featherless setup.")
    parser.add_argument("--live", action="store_true", help="send a live API call")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    status = featherless_status()
    print("Featherless AI setup check")
    print(f"Configured: {status.configured}")
    print(f"Base URL: {status.base_url}")
    print(f"Model: {status.model or 'missing'}")
    print(f"Reason: {status.reason}")
    print(f"Max output tokens: {status.max_tokens}")
    print(f"Prompt char limit: {status.prompt_char_limit}")

    if not status.configured:
        raise SystemExit(2)

    if args.live:
        result = featherless_summary_result(
            "Return one sentence confirming Quadro Featherless verifier lane is live."
        )
        print(f"Live response: {result.content}")
        print(f"Usage: {result.usage or 'not returned'}")
        print(f"Prompt chars sent: {result.prompt_chars}")


if __name__ == "__main__":
    main()
