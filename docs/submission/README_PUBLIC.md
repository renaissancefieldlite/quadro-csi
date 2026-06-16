# Quadro CSI

Quadro CSI is a Band-connected multi-agent workflow for regulated customer
escalations. It turns a customer request, source documents, consent state, and
policy requirements into an audit-ready decision packet.

## What It Does

Quadro coordinates four specialized agents:

- **Customer Intake** frames the request, consent owner, and decision question.
- **Evidence Spine** retrieves source-backed support and missing evidence.
- **Policy/Risk** checks consent, policy blockers, and escalation needs.
- **Decision Packet** returns `APPROVE`, `SAY_NO`, or `NEED_MORE_INFO`.

The agents coordinate through Band as the shared collaboration layer. The UI
shows the handoff trail, evidence state, policy gate, final recommendation, and
whether the current run published to Band.

## Why It Matters

High-stakes customer workflows often cross support, compliance, finance, legal,
insurance, or operations teams. Quadro keeps the decision path visible so a team
can see what was reviewed, what was missing, what policy required, and why the
workflow was approved, stopped, or sent back for more information.

## Acceptance Tests

Quadro includes public-safe regulated workflow packs that test specific gates:

- approve clean refund;
- say no when consent is revoked;
- need more info when approval evidence is missing;
- rerun the chain when consent changes;
- insurance, banking, legal, government procurement, and cybersecurity cases.

Run:

```bash
.venv/bin/python scripts/run_document_sets.py
```

## Local Demo

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[band,aimlapi]"
.venv/bin/python -m quadro.server
```

Open:

```text
http://127.0.0.1:8867
```

## Environment

Copy `.env.example` to `.env` for local configuration. Keep API keys and Band
agent credentials out of Git.

AI/ML API is optional and should be used as a verifier/explanation lane, not as
the decision authority. Quadro's approval gates remain evidence and policy
driven.

