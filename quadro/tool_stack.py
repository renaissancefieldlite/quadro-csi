from __future__ import annotations

import importlib.metadata
import importlib.util
import os
import platform
import shutil
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path

from .band_config import load_agent_config, missing_agent_configs
from .featherless_client import featherless_status
from .hermes_client import hermes_status

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "audit" / "quadro_memory.sqlite3"
DEFAULT_AUDIT = ROOT / "audit" / "quadro_local_room.jsonl"
LIVE_BAND_AUDIT = ROOT / "audit" / "band_live_run_2026-05-31.json"


@dataclass
class StackEntry:
    name: str
    status: str
    description: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def get_tool_stack(
    db_path: Path = DEFAULT_DB,
    audit_path: Path = DEFAULT_AUDIT,
) -> list[dict[str, str]]:
    entries = [
        _external_hermes(),
        _persistent_memory(db_path, audit_path),
        _evidence_rag(db_path),
        _aimlapi_provider(),
        _featherless_provider(),
        _browser_control(),
        _band_network(),
        _package_entry(
            name="Hermes Agent",
            packages=["hermes-agent", "hermes"],
            modules=["hermes"],
            description="Tool gateway lane for skills, memory, and messaging.",
        ),
        _package_entry(
            name="browser-use",
            packages=["browser-use"],
            modules=["browser_use"],
            description="Python browser-agent layer over Playwright.",
        ),
        _package_entry(
            name="Browser Use Cloud SDK",
            packages=["browser-use-sdk"],
            modules=["browser_use_sdk"],
            description="Optional managed browser session SDK.",
        ),
        _package_entry(
            name="Playwright",
            packages=["playwright"],
            modules=["playwright"],
            description="Browser automation runtime.",
        ),
        _package_entry(
            name="LangGraph",
            packages=["langgraph"],
            modules=["langgraph"],
            description="Read-act-reread graph orchestration.",
        ),
        _package_entry(
            name="LangChain",
            packages=["langchain"],
            modules=["langchain"],
            description="Agent/tool abstraction and model glue.",
        ),
        _package_entry(
            name="PyTorch",
            packages=["torch"],
            modules=["torch"],
            description="Model/runtime tensor layer.",
        ),
        _package_entry(
            name="Transformers",
            packages=["transformers"],
            modules=["transformers"],
            description="Model loading and tokenizer stack.",
        ),
        _package_entry(
            name="PEFT",
            packages=["peft"],
            modules=["peft"],
            description="Adapter readiness lane.",
        ),
        _package_entry(
            name="MLX",
            packages=["mlx"],
            modules=["mlx"],
            description="Apple Silicon local model runtime lane.",
        ),
        _package_entry(
            name="MLX LM",
            packages=["mlx-lm", "mlx_lm"],
            modules=["mlx_lm"],
            description="MLX language-model serving and generation helpers.",
        ),
        _package_entry(
            name="Band SDK",
            packages=["thenvoi", "band-sdk"],
            modules=["thenvoi"],
            description="Band agent SDK/API integration lane.",
        ),
    ]
    return [entry.to_dict() for entry in entries]


def _external_hermes() -> StackEntry:
    status_read = hermes_status(timeout=0.35)
    if status_read.live:
        status = "ACTIVE"
        detail = (
            f"model={status_read.model}; "
            f"backend={status_read.health.get('loaded_backend') or status_read.health.get('active_backend') or 'unknown'}"
        )
    elif status_read.enabled:
        status = "OFFLINE"
        detail = status_read.reason
    else:
        status = "PENDING"
        detail = "set QUADRO_USE_HERMES=1 to enable local model readouts"
    return StackEntry(
        name="External Hermes runtime",
        status=status,
        description="Quadro-owned adapter calling local Hermes /api/generate.",
        detail=detail,
    )


def _persistent_memory(db_path: Path, audit_path: Path) -> StackEntry:
    doc_count = _count_docs(db_path)
    audit_state = "jsonl ready" if audit_path.parent.exists() else "jsonl pending"
    status = "ACTIVE" if db_path.exists() else "READY"
    return StackEntry(
        name="Persistent memory",
        status=status,
        description="SQLite/FTS evidence memory plus JSONL audit.",
        detail=f"{doc_count} docs indexed; {audit_state}",
    )


def _evidence_rag(db_path: Path) -> StackEntry:
    doc_count = _count_docs(db_path)
    return StackEntry(
        name="Evidence/RAG",
        status="ACTIVE" if doc_count else "READY",
        description="Source packets retrieved into agent evidence turns.",
        detail=f"{doc_count} indexed source packets",
    )


def _browser_control() -> StackEntry:
    active = platform.system() == "Darwin" and shutil.which("osascript")
    return StackEntry(
        name="Chrome/Safari control",
        status="AVAILABLE" if active else "PENDING",
        description="AppleScript lane for browser open/search/read/click/type.",
        detail="available on this Mac; asks before live browser actions",
    )


def _aimlapi_provider() -> StackEntry:
    key = os.getenv("AIMLAPI_KEY") or os.getenv("AIML_API_KEY")
    model = os.getenv("AIMLAPI_MODEL", "")
    max_tokens = os.getenv("AIMLAPI_MAX_TOKENS", "96")
    status = "READY" if key and model else "PENDING"
    detail = (
        f"model={model}; max_output={max_tokens} tokens"
        if model
        else "hold: support reply or $10 controlled top-up, then one verifier call"
    )
    return StackEntry(
        name="AI/ML API",
        status=status,
        description="Partner-prize model lane for reasoning, extraction, and summaries.",
        detail=detail,
    )


def _featherless_provider() -> StackEntry:
    status_read = featherless_status()
    status = "READY" if status_read.configured else "PENDING"
    detail = (
        f"model={status_read.model}; max_output={status_read.max_tokens} tokens"
        if status_read.configured
        else "set FEATHERLESS_API_KEY and QUADRO_USE_FEATHERLESS=1 for verifier lane"
    )
    return StackEntry(
        name="Featherless AI",
        status=status,
        description="Open-model inference lane for verifier summaries and partner proof.",
        detail=detail,
    )


def _band_network() -> StackEntry:
    configs = load_agent_config()
    ready = not missing_agent_configs(configs)
    if LIVE_BAND_AUDIT.exists():
        status = "ACTIVE"
        detail = "live Band chat d526bd08-bef8-44dc-bbf8-e216e4d2c57f verified"
    elif ready:
        status = "READY"
        detail = "four remote-agent credentials configured"
    else:
        status = "PENDING"
        detail = "create Band account and four remote-agent keys"
    return StackEntry(
        name="Band network",
        status=status,
        description="Real Band room, remote agents, messages, and events.",
        detail=detail,
    )


def _package_entry(
    name: str,
    packages: list[str],
    modules: list[str],
    description: str,
) -> StackEntry:
    version = _first_version(packages)
    module_available = any(importlib.util.find_spec(module) for module in modules)
    if version:
        status = "ACTIVE"
        detail = f"v{version}"
    elif module_available:
        status = "AVAILABLE"
        detail = "module import path available"
    else:
        status = "PENDING"
        detail = "optional package not installed; core Quadro path still runs"
    return StackEntry(
        name=name,
        status=status,
        description=description,
        detail=detail,
    )


def _first_version(packages: list[str]) -> str | None:
    for package in packages:
        try:
            return importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            continue
    return None


def _count_docs(db_path: Path) -> int:
    if not db_path.exists():
        return 0
    try:
        with sqlite3.connect(db_path) as conn:
            row = conn.execute("select count(*) from documents").fetchone()
            return int(row[0]) if row else 0
    except sqlite3.Error:
        return 0
