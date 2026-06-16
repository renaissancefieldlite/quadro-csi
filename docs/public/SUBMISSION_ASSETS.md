# Submission Assets

Last refreshed: 2026-06-16.

## Submit Here

Use the logged-in lablab team page and click `Submit Project`:

```text
https://lablab.ai/ai-hackathons/band-of-agents-hackathon/renaissance-field-lite
```

If the team page does not show the button, open the hackathon page and use the
same account/team:

```text
https://lablab.ai/ai-hackathons/band-of-agents-hackathon
```

## Required Upload / Link Fields

```text
Project title: Quadro CSI
Team: Renaissance Field Lite
Primary track: Track 3 - Regulated & High-Stakes Workflows
```

| Field | Quadro asset |
| --- | --- |
| Cover image | `app/static/assets/quadro-cover.png` |
| Video presentation | `submission_video/capcut_voiceover_pack/FINALVOICEOVERFROMABLETONLEFTRANSCRIPT.mp4` |
| Slide presentation | `docs/public/quadro_csi_submission_deck.pptx` |
| Public GitHub repository | Pending final publish |
| Demo platform / Application URL | Pending host or GitHub Pages fallback |
| Form copy | `docs/public/SUBMISSION_FORM_COPY.md` |
| Proof readout | `docs/public/SUBMISSION_DEMO_PROOF.md` |

## Current Proof Claim

```text
Latest integrated capture: audit/submission_demo_20260616T051948Z.json
Quadro outcome: SAY_NO
Gate: stopped_consent_revoked
Band publish: true / 4 events
Featherless verifier: true
AI/ML API verifier: true
Partner errors: {}
```

## GitHub Status

The local repo is public-package ready but not yet published.

```text
Current local state: no commits yet on main
Current remote: none
Recommended public repo name: quadro-csi
```

Before pushing, run the public gate:

```bash
.venv/bin/python -m unittest discover -s tests
.venv/bin/python scripts/run_document_sets.py
.venv/bin/python scripts/compare_input_cohesion.py
.venv/bin/python scripts/check_public_boundary.py
```
