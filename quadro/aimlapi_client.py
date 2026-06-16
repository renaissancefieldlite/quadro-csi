from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_BASE_URL = "https://api.aimlapi.com/v1"


@dataclass
class AIMLAPIStatus:
    configured: bool
    base_url: str
    model: str
    reason: str
    max_tokens: int
    prompt_char_limit: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "configured": self.configured,
            "base_url": self.base_url,
            "model": self.model,
            "reason": self.reason,
            "max_tokens": self.max_tokens,
            "prompt_char_limit": self.prompt_char_limit,
        }


@dataclass
class AIMLAPIResult:
    content: str
    model: str
    usage: dict[str, Any]
    prompt_chars: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "model": self.model,
            "usage": self.usage,
            "prompt_chars": self.prompt_chars,
        }


def aimlapi_status() -> AIMLAPIStatus:
    key = _api_key()
    base_url = os.getenv("AIMLAPI_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    model = os.getenv("AIMLAPI_MODEL", "")
    max_tokens = _int_env("AIMLAPI_MAX_TOKENS", 96)
    prompt_char_limit = _int_env("AIMLAPI_PROMPT_CHAR_LIMIT", 2500)
    if not key:
        return AIMLAPIStatus(
            configured=False,
            base_url=base_url,
            model=model,
            reason="missing AIMLAPI_KEY",
            max_tokens=max_tokens,
            prompt_char_limit=prompt_char_limit,
        )
    if not model:
        return AIMLAPIStatus(
            configured=False,
            base_url=base_url,
            model=model,
            reason="missing AIMLAPI_MODEL",
            max_tokens=max_tokens,
            prompt_char_limit=prompt_char_limit,
        )
    return AIMLAPIStatus(
        configured=True,
        base_url=base_url,
        model=model,
        reason="configured",
        max_tokens=max_tokens,
        prompt_char_limit=prompt_char_limit,
    )


def partner_summary(prompt: str, timeout: float = 30.0) -> str:
    return partner_summary_result(prompt, timeout=timeout).content


def partner_summary_result(prompt: str, timeout: float = 30.0) -> AIMLAPIResult:
    status = aimlapi_status()
    if not status.configured:
        raise RuntimeError(status.reason)
    prompt = prompt[: status.prompt_char_limit]

    payload = {
        "model": status.model,
        "messages": [
            {
                "role": "user",
                "content": (
                    "You are Quadro's partner model lane. Summarize only the "
                    "provided source-backed workflow state. Keep it concise and "
                    f"do not invent facts.\n\n{prompt}"
                ),
            },
        ],
        "temperature": 0.2,
        "max_tokens": status.max_tokens,
        "stream": False,
    }
    request = urllib.request.Request(
        f"{status.base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {_api_key()}",
            "Content-Type": "application/json",
            "User-Agent": "QuadroSubmissionVerifier/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"AI/ML API HTTP {exc.code}: {error_body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"AI/ML API connection failed: {exc}") from exc

    try:
        content = body["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"AI/ML API response shape unexpected: {body}") from exc
    return AIMLAPIResult(
        content=content,
        model=str(body.get("model") or status.model),
        usage=body.get("usage") if isinstance(body.get("usage"), dict) else {},
        prompt_chars=len(prompt),
    )


def _api_key() -> str:
    return os.getenv("AIMLAPI_KEY") or os.getenv("AIML_API_KEY") or ""


def _int_env(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return max(1, value)
