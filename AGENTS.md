# Quadro Agent Instructions

This repo is the clean public build for Quadro CSI. Quadro is a regulated
customer review workspace that turns a request, source documents, consent
state, and policy requirements into an audit-ready decision packet.

## Public Boundary

- Keep Quadro public-safe and hackathon-ready.
- Do not copy private Golden Mark internals, private prompts, memory stores,
  model checkpoints, adapter code, raw captures, or claim-sensitive mechanics.
- Use the public state-path abstraction only: request, consent, evidence,
  policy, decision, revision, and audit trail.
- No toy-data support claims. Support language must point to real source
  documents, public-safe acceptance packs, local run artifacts, or captured
  provider proof.

## GitLab Transcend Showcase Context

This repository also contains a GitLab Duo Agent Platform showcase layer for
the GitLab Transcend Hackathon. The showcase layer is not a separate product:
it adapts Quadro's review chain to GitLab work items, issues, merge requests,
and Orbit-facing delivery decisions.

Use this flow when reviewing GitLab work:

1. Input Cohesion stabilizes the request, source scope, consent/approval
   signals, blocker cues, and next gate.
2. Customer Intake frames the requested action, owner, consent scope, and task
   mode.
3. Evidence Spine retrieves source-backed support and flags missing evidence.
4. Policy/Risk checks consent, approval, policy blockers, risk, and escalation.
5. Decision Packet returns one of: approve, say no, or need more information,
   with a short audit-ready reason.

The GitLab Duo skill lives at:

```text
skills/quadro-orbit-review/SKILL.md
```

Use `/quadro-orbit-review` in GitLab Duo contexts where supported, or instruct
the agent to use the Quadro Orbit Review skill by name.

## Verification

Before public submission claims, run:

```bash
python3 run_quadro_demo.py
python3 scripts/check_public_boundary.py
python3 -m unittest discover -s tests
```

The expected core demo receipt is:

```text
Quadro demo passed: all acceptance sets returned expected outcomes.
```
