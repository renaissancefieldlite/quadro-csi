# AI/ML API Lane

AI/ML API is an optional model-provider lane for Quadro CSI.

It can be used for:

- extraction from source material;
- evidence manifest summarization;
- policy and decision explanation;
- verifier commentary on an already-computed decision packet.

Quadro's final decision authority remains the evidence, consent, and policy
gate. A model readout cannot override revoked consent, missing approval
evidence, or a policy prohibition.

## Minimal Partner Proof

Live partner proof has now been captured. The lane should still be presented as
post-decision verifier commentary, not as Quadro's decision authority.

Current integrated proof:

```text
Artifact: audit/submission_demo_20260616T051948Z.json
Model: gpt-4o-mini-2024-07-18
Usage: 656 total tokens
AI/ML API verifier: true
Partner errors: {}
```

Repeatable method:

1. Run a normal Quadro review.
2. Send only the compact evidence, policy, and decision packet to AI/ML API.
3. Ask for an audit explanation.
4. Save model ID, response, timestamp, and token/cost usage.
5. Show the result as `AI/ML verifier`, not as the source of the decision.

## Capture Command

Setup check:

```bash
.venv/bin/python scripts/verify_aimlapi_setup.py
```

Live capped integrated capture:

```bash
.venv/bin/python scripts/run_submission_demo_capture.py --providers aimlapi featherless --live
```

The capture writes a timestamped JSON artifact under `audit/` and refreshes
`docs/public/SUBMISSION_DEMO_PROOF.md`.
