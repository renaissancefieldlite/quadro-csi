---
name: quadro-orbit-review
description: Review GitLab Orbit work items, issues, merge requests, or delivery decisions with Quadro CSI's consent-aware multi-agent audit chain.
metadata:
  slash-command: enabled
---

# Quadro Orbit Review

Use this skill when a user asks GitLab Duo to review a GitLab Orbit work item,
issue, merge request, agent, flow, skill, or delivery decision that needs a
source-backed go/no-go packet.

Quadro is not a single chatbot. It is a review chain:

1. **Input Cohesion** stabilizes the request, source scope, approval signals,
   correction markers, missing evidence cues, policy-blocker cues, and next
   gate.
2. **Customer Intake** identifies the requester, owner, requested action,
   consent or approval scope, and task mode.
3. **Evidence Spine** retrieves source-backed evidence from the repo, work
   item, issue, merge request, policy files, docs, and acceptance packs.
4. **Policy/Risk** checks approval state, consent state, policy blockers,
   escalation needs, and risk.
5. **Decision Packet** returns exactly one gate: approve, say no, or need more
   information.

## Review Contract

When this skill is active, produce a clear audit packet:

```text
Decision:
Evidence used:
Missing evidence:
Policy / risk read:
Recommended next step:
Human signoff needed:
```

Use plain English for the decision. Avoid unexplained internal labels. If a
machine state is useful, define it once and then translate it into a human
readable result.

## Evidence Rules

- Prefer real GitLab project context: the current issue, work item, merge
  request, branch diff, repository files, pipeline status, docs, and linked
  Orbit artifacts.
- If the user supplies source documents, cite them by filename or GitLab URL.
- If evidence is missing, return `need more information` instead of inventing
  facts.
- If consent or authorization is revoked, withdrawn, or out of scope, return
  `say no`.
- If policy requires approval and approval evidence is absent, return
  `need more information`.
- If a policy prohibits the requested action, return `say no`.
- If the evidence is present, consent or authorization is current, and no
  blocker exists, return `approve` with the required human signoff.

## Runnable Quadro Proof

The local Quadro proof path is:

```bash
python3 run_quadro_demo.py
python3 scripts/check_public_boundary.py
python3 -m unittest discover -s tests
```

Expected core demo receipt:

```text
Quadro demo passed: all acceptance sets returned expected outcomes.
```

The public acceptance packs live in `data/evaluation_sets/` and cover approval,
revoked consent, missing approval, insurance, banking, legal authority,
government procurement, cybersecurity disclosure, and consent reroute cases.

## Public Boundary

Do not expose private prompts, private memory stores, raw captures, API keys,
model checkpoints, or protected project internals. The public Quadro abstraction
is:

```text
request -> consent state -> evidence manifest -> policy read -> decision packet
-> consent revision -> re-review packet
```
