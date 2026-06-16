# Public Boundary Review

## Direct Answer

Quadro does not use a private Mirror Architecture implementation layer in the
public product build. It uses normal public-safe engineering patterns:

- role-based agents;
- RAG/evidence retrieval;
- SQLite/FTS memory;
- JSONL audit logs;
- deterministic consent and policy gates;
- Band room/event handoffs.

The broader private architecture helped inspire the concept and discipline of
state continuity, but no private mechanics, raw captures, protected prompts, or
private memory stores should be published.

## Public Wording

Use:

```text
Quadro CSI is a clean-room multi-agent workflow for regulated customer review.
It uses source-backed retrieval, structured state, and Band handoffs to preserve
consent, evidence, policy, and decision context.
```

Avoid:

```text
Mirror Architecture
Golden Mark internals
B.A.S.I.S. internals
Rick/operator logs
private memory stores
raw captures
patent-sensitive mechanics
```

## Current Repo Risk

The working repo contains internal/private planning docs that mention protected
project boundaries and operator context. Those files are useful locally but
should not be published in the public GitHub repo.

Use `01_PUBLIC_GITHUB_PUBLISH_CHECKLIST.md` before pushing.

