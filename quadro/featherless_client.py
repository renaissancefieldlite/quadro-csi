from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_BASE_URL = "https://api.featherless.ai/v1"
DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct"
DEFAULT_REFERER = "https://lablab.ai/ai-hackathons/band-of-agents-hackathon"
DEFAULT_TITLE = "Quadro CSI"
DEFAULT_USER_AGENT = "QuadroCSI/0.1 (+https://lablab.ai/ai-hackathons/band-of-agents-hackathon)"


@dataclass
class FeatherlessStatus:
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
class FeatherlessResult:
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


def featherless_status() -> FeatherlessStatus:
    key = _api_key()
    base_url = os.getenv("FEATHERLESS_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    model = os.getenv("FEATHERLESS_MODEL", DEFAULT_MODEL)
    max_tokens = _int_env("FEATHERLESS_MAX_TOKENS", 240)
    prompt_char_limit = _int_env("FEATHERLESS_PROMPT_CHAR_LIMIT", 4000)
    if not key:
        return FeatherlessStatus(
            configured=False,
            base_url=base_url,
            model=model,
            reason="missing FEATHERLESS_API_KEY",
            max_tokens=max_tokens,
            prompt_char_limit=prompt_char_limit,
        )
    if not model:
        return FeatherlessStatus(
            configured=False,
            base_url=base_url,
            model=model,
            reason="missing FEATHERLESS_MODEL",
            max_tokens=max_tokens,
            prompt_char_limit=prompt_char_limit,
        )
    return FeatherlessStatus(
        configured=True,
        base_url=base_url,
        model=model,
        reason="configured",
        max_tokens=max_tokens,
        prompt_char_limit=prompt_char_limit,
    )


def featherless_summary(prompt: str, timeout: float = 30.0) -> str:
    return featherless_summary_result(prompt, timeout=timeout).content


def featherless_summary_result(
    prompt: str,
    timeout: float = 30.0,
) -> FeatherlessResult:
    status = featherless_status()
    if not status.configured:
        raise RuntimeError(status.reason)
    prompt = prompt[: status.prompt_char_limit]

    payload = {
        "model": status.model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are Quadro's Featherless open-model verifier lane. "
                    "Summarize only the provided state path. Return exactly "
                    "four concise bullets under 120 words total: outcome, gate, "
                    "evidence basis, and human next step. Do not invent facts."
                ),
            },
            {"role": "user", "content": prompt},
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
            "HTTP-Referer": os.getenv("FEATHERLESS_HTTP_REFERER", DEFAULT_REFERER),
            "X-Title": os.getenv("FEATHERLESS_X_TITLE", DEFAULT_TITLE),
            "User-Agent": os.getenv("FEATHERLESS_USER_AGENT", DEFAULT_USER_AGENT),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Featherless AI HTTP {exc.code}: {error_body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Featherless AI connection failed: {exc}") from exc

    try:
        content = body["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Featherless AI response shape unexpected: {body}") from exc
    return FeatherlessResult(
        content=content,
        model=str(body.get("model") or status.model),
        usage=body.get("usage") if isinstance(body.get("usage"), dict) else {},
        prompt_chars=len(prompt),
    )


def _api_key() -> str:
    return os.getenv("FEATHERLESS_API_KEY") or os.getenv("FEATHERLESS_KEY") or ""


def _int_env(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return max(1, value)
