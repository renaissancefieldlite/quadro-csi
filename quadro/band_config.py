from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "agent_config.yaml"
ROLE_ORDER = [
    "quadro_intake",
    "quadro_evidence",
    "quadro_policy",
    "quadro_decision",
]


@dataclass
class RemoteAgentConfig:
    key: str
    name: str
    role: str
    agent_id: str
    api_key: str

    @property
    def configured(self) -> bool:
        placeholders = ["<", ">", "your-"]
        if not self.agent_id or not self.api_key:
            return False
        return not any(token in self.agent_id or token in self.api_key for token in placeholders)


def load_agent_config(path: Path = DEFAULT_CONFIG) -> dict[str, RemoteAgentConfig]:
    if not path.exists():
        return {}
    parsed = _parse_simple_yaml(path.read_text(encoding="utf-8"))
    configs: dict[str, RemoteAgentConfig] = {}
    for key, values in parsed.items():
        configs[key] = RemoteAgentConfig(
            key=key,
            name=values.get("name", key),
            role=values.get("role", key),
            agent_id=values.get("agent_id", ""),
            api_key=values.get("api_key", ""),
        )
    return configs


def missing_agent_configs(configs: dict[str, RemoteAgentConfig]) -> list[str]:
    missing: list[str] = []
    for key in ROLE_ORDER:
        config = configs.get(key)
        if not config or not config.configured:
            missing.append(key)
    return missing


def _parse_simple_yaml(text: str) -> dict[str, dict[str, str]]:
    current_key: str | None = None
    parsed: dict[str, dict[str, str]] = {}
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if not raw_line.startswith(" ") and raw_line.rstrip().endswith(":"):
            current_key = raw_line.rstrip()[:-1]
            parsed[current_key] = {}
            continue
        if current_key and ":" in raw_line:
            key, value = raw_line.strip().split(":", 1)
            parsed[current_key][key] = value.strip().strip('"').strip("'")
    return parsed
