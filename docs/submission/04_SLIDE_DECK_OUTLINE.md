# Slide Deck Outline

Target: 7-9 slides.

## 1. Title

```text
Quadro CSI
Consent-aware multi-agent review for regulated customer escalations
Renaissance Field Lite
```

Use `app/static/assets/quadro-cover.png` as the hero/cover asset.

## 2. Problem

- Customer escalations cross teams.
- Consent, evidence, policy, and decision state often fragment.
- High-stakes workflows need traceability before action.

## 3. Solution

- Four specialized agents.
- Shared Band coordination layer.
- Source-backed evidence manifest.
- Deterministic consent and policy gates.
- Audit-ready decision packet.

## 4. Agent Chain

```text
Customer Owner
-> Input Cohesion
-> Customer Intake
-> Evidence Spine
-> Policy/Risk
-> Decision Packet
-> Customer Owner
```

## 5. Band Collaboration

- Directed handoffs.
- Structured event payloads.
- Shared room state.
- Current run publish status.
- At least four Band events in the live product path.

## 6. Revisit Consent

- Consent can be narrowed or revoked.
- Quadro reroutes affected agents.
- Final packet records current revision and gate.

## 6a. State-Path Stabilization

- Input cohesion runs before the agent chain.
- It stabilizes review request, source scope, consent signals, correction markers, and next gate.
- Agents receive a shared state path instead of a loose prompt.
- Model-provider lanes can explain the packet, but they do not override policy gates.

## 7. Acceptance Testing

Show the nine public-safe packs:

- refund approve
- revoked consent say no
- missing approval need more info
- consent reroute approve
- insurance approve
- banking need more info
- legal authority say no
- government procurement say no
- cybersecurity need more info

## 8. AI/ML API Lane

- Optional model-provider lane.
- Extraction, summary, verifier explanation.
- Decision authority remains evidence/policy gates.
- Include model/cost only after a real captured run.

## 9. Business Value

- Faster escalation review.
- Cleaner handoffs.
- Fewer unsafe approvals.
- Better audit trail.
- Useful in support, finance, legal, insurance, compliance, and operations.
