# Submission Requirements Checklist

Verified against the live lablab.ai event page and lablab.ai hackathon
guidelines on 2026-06-12. Submission assets refreshed on 2026-06-16.

## Required By The Event Page

| Requirement | Quadro artifact | Status |
| --- | --- | --- |
| Project title | `Quadro CSI` | Ready |
| Short description | `docs/public/SUBMISSION_FORM_COPY.md` | Ready |
| Long description | `docs/public/SUBMISSION_FORM_COPY.md` | Ready |
| Technology and category tags | `docs/public/SUBMISSION_FORM_COPY.md` | Ready |
| Cover image | `app/static/assets/quadro-cover.png` | Check before final submit |
| Video presentation | `submission_video/capcut_voiceover_pack/FINALVOICEOVERFROMABLETONLEFTRANSCRIPT.mp4` | Ready; upload to lablab/video host |
| Slide presentation | `docs/public/quadro_csi_submission_deck.pptx` | Ready |
| Public GitHub repository | README and public docs prepared | Needs final publish |
| Demo application platform | Hosting plan required | Needs final host |
| Application URL | Hosted app URL | Needs final host |

## Written Overview To Include

Use this order in the long description, slide deck, or project README:

1. Problem: regulated customer escalations lose consent, evidence, and policy
   state across handoffs.
2. Solution: Quadro coordinates role-specialized agents through Band.
3. Custom feature: input cohesion stabilizes the request, source scope,
   consent/correction signals, missing evidence cues, and next gate before the
   agents run.
4. Agent flow: Customer Intake -> Evidence Spine -> Policy/Risk -> Decision
   Packet.
5. Demo workflow: revoked consent customer export stops as `SAY_NO`.
6. Proof: nine public-safe acceptance packs plus the input-cohesion A/B
   comparison.
7. Partner model lanes: AI/ML API and Featherless AI can provide verifier
   commentary after the deterministic decision packet is computed.

## Judging Alignment

| Judging area | Quadro answer |
| --- | --- |
| Application of Technology | Band is the coordination layer for role-specific agents, structured state, handoffs, and events. |
| Presentation | The demo shows the problem, agent roles, Band room flow, input cohesion, audit trail, and final gate. |
| Business Value | Quadro reduces manual coordination in regulated customer decisions and keeps humans in control of signoff. |
| Originality | Input cohesion plus consent-aware reroute goes beyond a chatbot or simple automation. |

## Final Submit Gate

Before submitting:

```bash
.venv/bin/python scripts/run_document_sets.py
.venv/bin/python scripts/compare_input_cohesion.py
.venv/bin/python scripts/run_submission_demo_capture.py --providers aimlapi featherless --live
.venv/bin/python -m unittest discover -s tests
.venv/bin/python scripts/check_public_boundary.py
```

Then confirm:

- the public repository excludes private raw files and local credentials;
- the demo URL opens from a clean browser session;
- the video is under the final lablab duration and file limits;
- the slide deck uses the same story as the demo;
- any AI/ML API or Featherless AI partner claim has a real captured run from
  `scripts/run_submission_demo_capture.py --live`.

Current captured partner proof:

```text
audit/submission_demo_20260616T051948Z.json
Band publish: true / 4 events
Featherless verifier: true
AI/ML API verifier: true
Partner errors: {}
```
