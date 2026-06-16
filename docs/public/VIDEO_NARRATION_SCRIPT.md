# Video Narration Script

Target length: 3-4 minutes.

## Opening

```text
This is Quadro CSI by Renaissance Field Lite. Quadro is a Band-connected
multi-agent review workspace for regulated customer escalations where consent,
evidence, policy, and decision state have to move together.
```

## Problem

```text
In real escalation workflows, context moves across teams but the audit trail
often breaks. A team may need to release a file, refund a customer, send a
disclosure, or approve a payout, but the consent state and evidence support are
not always visible in one place.
```

## Product

```text
Quadro separates the review into four agents. Customer Intake frames the request
and consent owner. Evidence Spine retrieves source-backed documents and flags
missing support. Policy/Risk checks blockers and escalation gates. Decision
Packet returns approve, say no, or need more info with an audit-ready reason.
Before those handoffs, Quadro runs an input-cohesion pass that stabilizes the
review request, source scope, consent signals, correction markers, and next gate.
```

## Demo

```text
Here is a customer export request where authorization was withdrawn. Quadro
should not approve this. It should route through the agents, detect the consent
problem, and stop the workflow.
```

Show:

- the submission capture command or local app run;
- Customer Intake, Evidence Spine, Policy/Risk, and Decision Packet handoffs;
- the final `SAY_NO`, stopped consent gate, high risk, and evidence count;
- Band publish status with four agent handoff events;
- Featherless and AI/ML API verifier output after Quadro computes the decision;
- `SUBMISSION_DEMO_PROOF.md` as the saved proof artifact.

## Testing

```text
Before submission, Quadro was tested against nine public-safe regulated workflow
packs covering approval, revoked consent, missing approval evidence, insurance,
banking, legal authority, government procurement, cybersecurity disclosure, and
consent reroute.
```

```text
We also ran the same packs with input cohesion off and on. Both paths kept the
correct decisions, but the stabilized path added nine state packets and 25 more
evidence hits with zero decision drift.
```

## Close

```text
Quadro turns high-stakes customer review into a visible Band-coordinated
workflow: source-backed, consent-aware, policy-gated, and audit-ready.
```
