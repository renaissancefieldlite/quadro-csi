# Quadro CSI for GitLab Transcend Showcase

## Project

Quadro CSI is a consent-aware multi-agent review workspace for regulated
customer and delivery decisions. For GitLab Transcend, Quadro is packaged as a
GitLab Duo Agent Platform showcase layer that can review GitLab Orbit work
items, issues, merge requests, and delivery decisions through a source-backed
audit chain.

## Track Fit

Showcase Track: build an agent, flow, or skill on the GitLab Duo Agent
Platform.

Quadro contributes:

- a project-level `AGENTS.md` context file;
- a GitLab Duo skill at `skills/quadro-orbit-review/SKILL.md`;
- a slash-command ready review workflow: `/quadro-orbit-review`;
- a runnable local proof path with nine public-safe acceptance packs.

## Agent Chain

Quadro uses a stabilization layer plus four role-specialized agents:

| Layer | Responsibility |
| --- | --- |
| Input Cohesion | Stabilizes the request, source scope, consent/approval signals, correction markers, missing evidence cues, and next gate. |
| Customer Intake | Frames the requested action, owner, consent scope, and task mode. |
| Evidence Spine | Retrieves source-backed support and builds the evidence manifest. |
| Policy/Risk | Checks consent, authorization, policy blockers, escalation needs, and risk. |
| Decision Packet | Returns approve, say no, or need more information with an audit-ready packet. |

## GitLab Orbit Use Case

A GitLab team can ask Quadro to review whether a work item, issue, merge
request, or agent/flow update is ready to proceed. The Quadro Orbit Review skill
turns the visible GitLab context into:

```text
Decision:
Evidence used:
Missing evidence:
Policy / risk read:
Recommended next step:
Human signoff needed:
```

This is useful when Orbit-facing work needs traceability across issue context,
repo docs, approval evidence, policy requirements, and final delivery handoff.

## Runnable Proof

From the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run_quadro_demo.py
.venv/bin/python scripts/check_public_boundary.py
.venv/bin/python -m unittest discover -s tests
```

Expected demo receipt:

```text
Quadro demo passed: all acceptance sets returned expected outcomes.
```

## Acceptance Packs

The proof sets live in `data/evaluation_sets/` and exercise the core gates:

- approve scoped refund;
- say no when consent is revoked;
- need more information when approval evidence is missing;
- approve after consent is narrowed and rerouted;
- insurance claim approval;
- banking/KYC missing approval;
- legal authority revoked;
- government procurement policy block;
- cybersecurity disclosure needing more information.

## Demo Assets

- Local UI: `http://127.0.0.1:8867`
- Cover image: `app/static/assets/quadro-cover.png`
- Public proof doc: `docs/public/SUBMISSION_DEMO_PROOF.md`
- Judge overview: `docs/public/JUDGES_OVERVIEW.html`
- Demo video: `docs/public/media/quadro_submission_demo.mp4`

## Public Boundary

Quadro is a standalone public-safe implementation. It does not publish private
prompts, private memory stores, raw captures, model checkpoints, API keys, or
protected project internals.
