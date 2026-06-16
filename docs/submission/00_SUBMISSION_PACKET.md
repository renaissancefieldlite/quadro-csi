# Quadro CSI Submission Packet

Use this as the working submission spine for the Band of Agents Hackathon.
Live event details were refreshed after kickoff; final asset map refreshed on
2026-06-16.

## Project

```text
Title: Quadro CSI
Team: Renaissance Field Lite
Primary track: Track 3 - Regulated & High-Stakes Workflows
Secondary fit: Track 1 - Internal Enterprise Workflows
```

## Short Description

```text
Quadro CSI coordinates four Band-connected agents to turn regulated customer escalations into consent-aware, source-backed, audit-ready decision packets.
```

## Long Description

```text
Customer escalations often move across support, compliance, policy, and operations without carrying the consent state, source evidence, and decision rationale with them. Quadro CSI turns that handoff into a visible multi-agent review chain.

Quadro uses an input-cohesion pass plus four specialized agents. Input Cohesion stabilizes the request, source scope, consent signals, correction markers, and next gate before handoff. Customer Intake frames the request and consent owner, Evidence Spine retrieves source-backed support and missing items, Policy/Risk checks blockers and escalation gates, and Decision Packet returns approve, say no, or need more info. The agents coordinate through Band as the shared collaboration layer, with directed handoffs, structured state, and audit events.

The signature workflow is consent-aware re-review. If consent is revoked or narrowed, Quadro routes the review back through the affected agents instead of letting the first pass stand. The final packet shows the current gate, evidence count, risk level, blockers, recommendation, and Band publish status.

Quadro was tested with public-safe regulated workflow packs covering refund, consent revocation, missing approval, insurance, banking, legal authority, government procurement, cybersecurity disclosure, and consent reroute cases.
```

## Technology Tags

```text
Band
Multi-agent workflow
Regulated workflow
Customer escalation
Consent review
RAG
SQLite/FTS
JSONL audit trail
Python
JavaScript
AI/ML API
```

AI/ML API is now supported by a real capped verifier run captured on
2026-06-16.

## Required Assets

- Public GitHub repository.
- Hosted demo URL.
- Application URL if the form separates it from hosted demo.
- 16:9 cover image: `app/static/assets/quadro-cover.png`.
- Video presentation: `submission_video/capcut_voiceover_pack/FINALVOICEOVERFROMABLETONLEFTRANSCRIPT.mp4`.
- Slide presentation: `docs/public/quadro_csi_submission_deck.pptx`.
- README with setup, demo path, and architecture.
- Dataset acceptance story.
- Band proof story.
- AI/ML API proof: `audit/submission_demo_20260616T051948Z.json` and
  `docs/public/SUBMISSION_DEMO_PROOF.md`.

## Demo Story

1. Show the Quadro workspace.
2. Ask a normal question to show chat mode does not fake a review.
3. Paste or attach a revoked-consent customer export packet.
4. Run the review.
5. Show Input Cohesion stabilizing request, source scope, consent signal, and next gate.
6. Show Intake -> Evidence -> Policy/Risk -> Decision handoffs.
7. Show `SAY_NO`, high risk, and stopped consent gate.
8. Show Band published four agent events.
9. Mention the nine acceptance packs and their expected gates.
10. Show AI/ML API and Featherless verifier readouts as model-provider lanes, not decision authority.
