from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_BASE_URL = "http://127.0.0.1:8788"


@dataclass
class HermesStatus:
    enabled: bool
    live: bool
    base_url: str
    model: str
    reason: str
    health: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "live": self.live,
            "base_url": self.base_url,
            "model": self.model,
            "reason": self.reason,
            "health": self.health,
        }


@dataclass
class HermesResult:
    role: str
    content: str
    model: str
    runtime: str
    backend: str
    checkpoint: str
    prompt_chars: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "model": self.model,
            "runtime": self.runtime,
            "backend": self.backend,
            "checkpoint": self.checkpoint,
            "prompt_chars": self.prompt_chars,
        }


def hermes_status(timeout: float = 0.75) -> HermesStatus:
    enabled = _enabled()
    base_url = _base_url()
    model = os.getenv("QUADRO_HERMES_MODEL", "hermes")
    if not enabled:
        return HermesStatus(
            enabled=False,
            live=False,
            base_url=base_url,
            model=model,
            reason="disabled by QUADRO_USE_HERMES",
            health={},
        )

    try:
        health = _request_json("GET", f"{base_url}/health", timeout=timeout)
    except RuntimeError as exc:
        return HermesStatus(
            enabled=True,
            live=False,
            base_url=base_url,
            model=model,
            reason=str(exc),
            health={},
        )

    ready = bool(health.get("generation_ready") or health.get("ready"))
    reason = "ready" if ready else str(health.get("generation_blocker") or "not ready")
    return HermesStatus(
        enabled=True,
        live=ready,
        base_url=base_url,
        model=model,
        reason=reason,
        health=health,
    )


def should_run_hermes_role(role: str) -> bool:
    if not _enabled():
        return False
    raw = os.getenv("QUADRO_HERMES_AGENT_ROLES", "evidence,policy,decision")
    allowed = {part.strip().lower() for part in raw.split(",") if part.strip()}
    return role.strip().lower() in allowed


def hermes_generate(role: str, prompt: str, timeout: float | None = None) -> HermesResult:
    if not _enabled():
        raise RuntimeError("Hermes model lane disabled by QUADRO_USE_HERMES")
    prompt = _trim_prompt(prompt)
    timeout = timeout or _float_env("QUADRO_HERMES_TIMEOUT", 45.0)
    model = os.getenv("QUADRO_HERMES_MODEL", "hermes")
    payload = {
        "model": model,
        "prompt": prompt,
        "options": {
            "max_new_tokens": _int_env("QUADRO_HERMES_MAX_NEW_TOKENS", 96),
            "temperature": _float_env("QUADRO_HERMES_TEMPERATURE", 0.0),
            "top_p": _float_env("QUADRO_HERMES_TOP_P", 0.0),
        },
    }
    body = _request_json(
        "POST",
        f"{_base_url()}/api/generate",
        payload=payload,
        timeout=timeout,
    )
    content = str(body.get("response", "")).strip()
    if not content:
        raise RuntimeError(f"Hermes returned no response text: {body}")
    return HermesResult(
        role=role,
        content=content,
        model=model,
        runtime=str(body.get("runtime") or ""),
        backend=str(body.get("backend") or ""),
        checkpoint=str(body.get("checkpoint") or body.get("runtime_checkpoint") or ""),
        prompt_chars=len(prompt),
    )


def hermes_readout_payload(role: str, prompt: str) -> dict[str, Any] | None:
    if not should_run_hermes_role(role):
        return None
    try:
        return {
            "status": "ACTIVE",
            "provider": "local_hermes",
            **hermes_generate(role=role, prompt=prompt).to_dict(),
        }
    except RuntimeError as exc:
        return {
            "status": "BLOCKED",
            "provider": "local_hermes",
            "role": role,
            "reason": str(exc),
        }


def _request_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Hermes HTTP {exc.code}: {error_body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Hermes connection failed: {exc}") from exc

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Hermes returned non-JSON response: {body[:240]}") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError(f"Hermes response shape unexpected: {parsed}")
    return parsed


def _enabled() -> bool:
    return os.getenv("QUADRO_USE_HERMES", "0") == "1"


def _base_url() -> str:
    return os.getenv("QUADRO_HERMES_URL", DEFAULT_BASE_URL).rstrip("/")


def _trim_prompt(prompt: str) -> str:
    limit = _int_env("QUADRO_HERMES_PROMPT_CHAR_LIMIT", 6000)
    return prompt.strip()[:limit]


def _int_env(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return max(1, value)


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default
