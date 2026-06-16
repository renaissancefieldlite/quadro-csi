# Video Narration Script

Target length: 3-4 minutes.

## 0:00 - 0:20 Opening

```text
This is Quadro CSI by Renaissance Field Lite. Quadro is a Band-connected
multi-agent review workspace for regulated customer escalations where consent,
evidence, policy, and decision state all have to move together.
```

## 0:20 - 0:45 Problem

```text
In real escalation workflows, context moves across teams but the audit trail
often breaks. A support owner may ask to release a file, refund a customer,
send a disclosure, or approve a payout, but the consent state, evidence source,
and policy requirement are not always visible in one place.
```

## 0:45 - 1:25 Product Walkthrough

```text
Quadro separates the review into four agents. Customer Intake frames the request
and consent owner. Evidence Spine retrieves source-backed documents and flags
missing support. Policy/Risk checks blockers and escalation gates. Decision
Packet returns approve, say no, or need more info with an audit-ready reason.
```

On screen:

- Show `Ask or Review`.
- Ask `What can you do?`.
- Show Quadro answers without running a decision review.

## 1:25 - 2:20 Regulated Review Demo

```text
Now I am pasting a customer export request where the account admin withdrew
authorization. Quadro should not approve this. It should route through the
agents, find the consent problem, and stop the workflow.
```

On screen:

- Paste revoked-consent packet.
- Click `Send`.
- Show Intake, Evidence, Policy/Risk, Decision handoffs.
- Show result: `Say no`, `Stopped consent revoked`, risk `High`.

## 2:20 - 2:50 Band Proof

```text
This is not just a final notification. Quadro publishes the agent handoff path
to Band, with separate events for intake, evidence, policy, and decision. Band
is the collaboration layer where the agents coordinate and preserve shared
state.
```

On screen:

- Show Band publish status.
- Optionally show Band chat/events.

## 2:50 - 3:25 Test Coverage

```text
Before submission, Quadro was tested against nine public-safe regulated workflow
packs. The tests cover approval, consent revocation, missing approval evidence,
insurance payout, banking wire exception, legal authority withdrawal, barred
vendor procurement, cybersecurity disclosure, and consent reroute.
```

On screen:

- Show dataset table or terminal output.

## 3:25 - 3:50 AI/ML API Lane

```text
Quadro's decision gates remain deterministic and evidence-driven. AI/ML API is
used as an optional model-provider lane for extraction, summarization, and
verifier explanations after the core workflow has already produced its audit
packet.
```

Use only after a real AI/ML API proof call exists.

## 3:50 - 4:00 Close

```text
Quadro turns high-stakes customer review into a visible Band-coordinated
workflow: source-backed, consent-aware, policy-gated, and audit-ready.
```

