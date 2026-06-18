# Quadro

Quadro CSI is a Band-connected multi-agent workflow for customer-facing
regulated reviews. It turns a customer escalation, source documents, consent
state, and policy requirements into an audit-ready decision packet by having
four agents coordinate through a shared room:

- Input Cohesion
- Intake Agent
- Evidence Agent
- Policy Agent
- Decision Agent

## Judge Quickstart

Run Quadro from the repository root. Do not copy one Python file into a separate
interpreter; the demo imports the local `quadro/` package and loads document
sets from `data/evaluation_sets/`.

Core runnable path, no API keys required:

```bash
git clone https://github.com/renaissancefieldlite/quadro-csi.git
cd quadro-csi
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run_quadro_demo.py
```

Expected result:

```text
Quadro demo passed: all acceptance sets returned expected outcomes.
```

Launch the local UI:

```bash
.venv/bin/python -m quadro.server
```

Open:

```text
http://127.0.0.1:8867
```

In the UI, choose `Load Acceptance Set`, click `Load Set`, then click `Send`.
The intake, evidence, policy, and decision agents will write the visible audit
trail.

More detail: [Run Quadro CSI](RUN_DEMO.md).

The signature workflow is `Revisit Consent`. A human can reopen, narrow, or
revoke consent after the workflow has started. Quadro then re-routes the room so
the relevant agents re-check scope, evidence, policy, and the final decision
packet instead of pretending the first pass is still valid.

## Hackathon Fit

Primary track: regulated and high-stakes workflows.

Secondary fit: internal enterprise workflows.

Team page:

```text
https://lablab.ai/ai-hackathons/band-of-agents-hackathon/renaissance-field-lite
```

Quadro is strongest as Track 3 because its core value is customer traceability,
consent revision, scoped re-review, evidence support, and audit-ready decision
state. It also fits Track 1 because it moves work across roles, approvals, and
handoffs.

Band requirement target:

- at least three agents collaborating through Band;
- role-specialized handoffs through a shared room;
- structured context passed between agents;
- visible audit trail of messages, events, decisions, and consent revisions.

## Current Build State

This repo has a local runtime and a live Band integration path: persistent
room log, SQLite/FTS evidence memory, JSONL audit, four Band remote agents,
and a verified Band chat/event run.

```bash
.venv/bin/python run_quadro_demo.py
```

Optional local web preview:

```bash
.venv/bin/python -m quadro.server
```

Then open:

```text
http://127.0.0.1:8867
```

Live Band gate:

```bash
.venv/bin/python -m pip install -r requirements-live.txt
.venv/bin/python scripts/verify_band_live.py --json
.venv/bin/python scripts/run_band_agents.py --live --create-chat --json
```

Verified Band room:

```text
https://app.band.ai/chat/d526bd08-bef8-44dc-bbf8-e216e4d2c57f
```

The live run created a Band chat, added all four Quadro remote agents, and
posted role-specific Band events for intake, evidence, policy, and decision.
The audit summary is stored locally under `audit/band_live_run_2026-05-31.json`.

## Public Boundary

Quadro uses a public-safe review-state pattern:

```text
request -> consent state -> evidence manifest -> policy read -> decision packet
-> consent revision -> re-review packet
```

This repo uses original Quadro code for persistent memory, retrieval,
state checkpoints, and agent handoffs. It does not include private prompts,
private memory stores, raw captures, model checkpoints, or protected runtime
mechanics from any other project.

## No Toy Data Rule

Quadro does not rely on a single happy-path demo. It includes public-safe
regulated workflow acceptance packs that test approval, revoked consent,
missing approval evidence, insurance, banking, legal authority, government
procurement, cybersecurity disclosure, and consent reroute cases.

See:

- [Judge overview](docs/public/JUDGES_OVERVIEW.md)
- [Submission checklist](docs/public/SUBMISSION_REQUIREMENTS_CHECKLIST.md)
- [Public dataset story](docs/public/DATASET_ACCEPTANCE.md)
- [State-path stabilization](docs/public/STATE_PATH_STABILIZATION.md)
- [Input cohesion comparison](docs/public/INPUT_COHESION_COMPARISON.md)
- [Public AI/ML API lane](docs/public/AI_ML_API_LANE.md)
- [Featherless AI lane](docs/public/FEATHERLESS_AI_LANE.md)
- [Public demo script](docs/public/VIDEO_NARRATION_SCRIPT.md)
- [Slide deck outline](docs/public/SLIDE_DECK_OUTLINE.md)

## How The Agents Are Built

Quadro separates the workflow into role contracts:

```text
Customer Owner
  -> Input Cohesion
  -> QuadroIntake
  -> QuadroEvidence
  -> QuadroPolicy
  -> QuadroDecision
  -> Customer Owner
```

Each role has:

- a message contract;
- a structured payload contract;
- a state-path lane;
- a retrieval/memory responsibility;
- a next-agent handoff.

Local mode runs the four role workers against the same persistent room and
SQLite/FTS memory. Band mode maps each role to its own Band remote agent with
its own API key, then keeps the same customer-case handoff protocol through
Band messages and events.

Band docs call this a remote/external agent connection: the agent runs in our
environment and uses Band room tools for messages, events, participants, and
peer lookup.
