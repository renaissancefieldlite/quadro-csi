# Submission Form Copy

Submission copy refreshed on 2026-06-16. Confirm any lablab field limits in the
logged-in submit form before final paste.

## Project Title

```text
Quadro CSI
```

## Short Description

```text
Quadro CSI coordinates four Band-connected agents to turn regulated customer escalations into consent-aware, source-backed, audit-ready decision packets.
```

## Long Description

```text
Customer escalations often move across support, compliance, policy, and operations without carrying the consent state, source evidence, and decision rationale with them. Quadro CSI turns that handoff into a visible multi-agent review chain.

Quadro uses an input-cohesion pass plus four specialized agents. Input cohesion stabilizes the review request, source scope, consent signals, correction markers, and next gate before handoff. Customer Intake frames the request and consent owner, Evidence Spine retrieves source-backed support and missing items, Policy/Risk checks blockers and escalation gates, and Decision Packet returns approve, say no, or need more info. The agents coordinate through Band as the shared collaboration layer, with directed handoffs, structured state, and audit events.

The signature workflow is consent-aware re-review. If consent is revoked or narrowed, Quadro routes the review back through the affected agents instead of letting the first pass stand. The final packet shows the current gate, evidence count, risk level, blockers, recommendation, and Band publish status.

Quadro was tested with public-safe regulated workflow packs covering refund, consent revocation, missing approval, insurance, banking, legal authority, government procurement, cybersecurity disclosure, and consent reroute cases. A live integrated partner verifier run was captured against the revoked-consent pack after Quadro computed the deterministic SAY_NO decision and published the four-agent handoff to Band. Featherless AI and AI/ML API both returned post-decision verifier readouts from the same saved decision packet; neither provider is used as the decision authority.

We also ran a side-by-side comparison with input cohesion off and on. Both paths passed all nine packs with zero decision drift; the stabilized path added nine state packets and 25 more evidence hits, making the agent handoff easier to audit without changing correct outcomes.
```

## Judge Overview Paragraph

```text
Quadro's custom feature is input cohesion: a pre-handoff stabilization layer that turns messy customer requests and source documents into a shared review state before the agents collaborate. It captures the request, source scope, consent/correction signals, missing evidence cues, policy-blocker cues, and next gate. This gives the Band room a stable state packet before Customer Intake, Evidence Spine, Policy/Risk, and Decision Packet exchange context and produce the final gate.
```

## Tags

```text
Band
AI agents
Multi-agent systems
Regulated workflows
Compliance
Customer support
RAG
SQLite
Audit trail
Python
JavaScript
AI/ML API
Featherless AI
```

## Local Submission Assets

```text
Cover image: app/static/assets/quadro-cover.png
Video presentation: submission_video/capcut_voiceover_pack/FINALVOICEOVERFROMABLETONLEFTRANSCRIPT.mp4
Slide deck: docs/public/quadro_csi_submission_deck.pptx
Integrated proof readout: docs/public/SUBMISSION_DEMO_PROOF.md
Public GitHub repository: https://github.com/renaissancefieldlite/quadro-csi
Application URL: https://renaissancefieldlite.com/quadro-csi/
```
