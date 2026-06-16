# Quadro CSI Judge Overview

Verified against the live lablab.ai event page on 2026-06-12.

## One-Line Summary

Quadro CSI is a Band-connected multi-agent review workspace that turns
regulated customer escalations into consent-aware, source-backed,
audit-ready decision packets.

## Track

Primary track:

```text
Track 3 - Regulated & High-Stakes Workflows
```

Secondary fit:

```text
Track 1 - Internal Enterprise Workflows
```

Quadro fits Track 3 because regulated customer work needs traceability,
escalation, careful review, and clear decision state. It also fits Track 1
because it moves work across intake, evidence review, policy/risk, and final
decision handoff.

## Problem

Enterprise customer escalations often cross teams before a decision is made.
A support owner may need to approve a refund, release a disclosure, send an
export, approve a payout, or route a policy exception. In those workflows,
consent, source evidence, approval state, and policy blockers can drift across
handoffs.

Quadro keeps those review lanes together.

## Agent System

Quadro uses one custom stabilization layer plus four specialized agents.

| Layer | Responsibility |
| --- | --- |
| Input Cohesion | Stabilizes the request, source scope, consent signals, correction markers, missing evidence cues, and next gate before agent handoff. |
| Customer Intake | Frames the requested action, owner, consent scope, and task mode. |
| Evidence Spine | Retrieves source-backed evidence, records missing support, and builds the evidence manifest. |
| Policy/Risk | Checks consent state, approval requirements, policy prohibitions, escalation needs, and blockers. |
| Decision Packet | Returns approve, say no, or need more information with an audit-ready state packet. |

## Custom Feature: Input Cohesion

Input cohesion is Quadro's public-safe state-stabilization feature.

It exists because multi-agent workflows can fail when the first agent sees one
version of a request, the second agent sees a different implied scope, and the
final decision loses a consent change or correction. Input cohesion creates a
shared starting packet before the agents collaborate.

It records:

- the stabilized review request;
- user-provided source titles and source count;
- consent, approval, disclosure, financial, and policy-blocker signals;
- correction markers such as revoked, revised, updated, or do not proceed;
- open questions and required evidence scopes;
- the next review gate.

The feature is derived from Renaissance Field Lite's internal work on keeping
long-running AI workflows coherent, but the Quadro implementation is standalone
and public-safe. It does not include private prompts, private memory stores,
model checkpoints, raw captures, or protected internal mechanics.

## Band Usage

Band is used as the collaboration layer for the review chain. Quadro maps each
role to a Band remote agent identity, publishes role-specific messages and
events, and keeps task state visible across the handoff.

The target collaboration flow is:

```text
Customer Owner
-> Input Cohesion
-> Customer Intake
-> Evidence Spine
-> Policy/Risk
-> Decision Packet
-> Customer Owner
```

This is not a final-notification wrapper. Band is part of the role handoff and
state coordination story.

## Testing Story

Quadro includes nine public-safe regulated workflow acceptance packs:

- scoped refund approval;
- revoked consent block;
- missing financial approval;
- narrowed-consent reroute;
- insurance claim approval;
- banking/KYC missing approval;
- legal authority revoked;
- government procurement policy block;
- cybersecurity disclosure needing more information.

Each pack declares an expected outcome, and the test runner fails if Quadro
returns the wrong gate.

Side-by-side input cohesion comparison:

```text
Baseline passed: 9/9
Stabilized passed: 9/9
Decision outcome changes: 0
Stabilization packets added: 9
Total evidence item lift: 25
Average evidence item lift: 2.78
```

The result is intentionally conservative: input cohesion did not change correct
decisions. It improved source coverage, review observability, and state control.

## Business Value

Quadro helps teams make high-stakes customer decisions with less manual
coordination debt:

- the review request is explicit;
- evidence is attached to the decision path;
- consent changes can reroute the workflow;
- policy blockers stop unsafe actions;
- final packets are easier to audit;
- humans still own signoff.

## Partner Model Lanes

Quadro can use AI/ML API or Featherless AI after the deterministic agent review
has already produced a decision packet. These partner lanes are verifier
commentary paths: they summarize the state path, evidence basis, final gate, and
human signoff requirement.

Partner model output is intentionally not decision authority.

Partner verifier status:

```text
Standalone verifier proof captured: audit/partner_capture_20260612T192004Z.json
Latest integrated submission capture: audit/submission_demo_20260616T051948Z.json
Current integrated gate: Band publish, Featherless verifier, and AI/ML API verifier passed.
Featherless model: Qwen/Qwen2.5-7B-Instruct; usage: 1065 total tokens.
AI/ML API model: gpt-4o-mini-2024-07-18; usage: 656 total tokens.
Partner errors: {}
```

## Demo Script Anchor

The cleanest demo is a revoked-consent customer export:

1. Add the customer request and source document.
2. Run the agent review.
3. Show input cohesion catching the consent/correction signal.
4. Show Intake, Evidence, Policy/Risk, and Decision handoffs.
5. Show the final `SAY_NO` decision and stopped consent gate.
6. Show the Band publish/live room evidence.
7. Show the Featherless AI and AI/ML API verifier readouts as post-decision
   partner model commentary.
