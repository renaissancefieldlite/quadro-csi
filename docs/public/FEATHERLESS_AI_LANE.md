# Featherless AI Lane

Featherless AI is an optional open-model inference lane for Quadro CSI.

It can be used for:

- verifier commentary after Quadro computes a decision packet;
- source-state summarization;
- evidence and policy explanation;
- partner-prize proof that Quadro can call an open-source model provider.

Quadro's final decision authority remains the consent, evidence, and policy
gate. Featherless can explain the packet, but it cannot override revoked
consent, missing approval evidence, or a policy prohibition.

## Why Featherless Fits Quadro

The Band hackathon page describes Featherless AI as serverless inference for
open-source models that can be integrated into agents, workflows, and real-time
applications. The Featherless docs describe the API as OpenAI-compatible.

That means Quadro can use Featherless with a small provider swap:

```text
base_url: https://api.featherless.ai/v1
endpoint: /chat/completions
auth: Bearer FEATHERLESS_API_KEY
```

## Environment

```bash
FEATHERLESS_API_KEY=
FEATHERLESS_BASE_URL=https://api.featherless.ai/v1
FEATHERLESS_MODEL=Qwen/Qwen2.5-7B-Instruct
FEATHERLESS_MAX_TOKENS=240
FEATHERLESS_PROMPT_CHAR_LIMIT=4000
FEATHERLESS_HTTP_REFERER=https://lablab.ai/ai-hackathons/band-of-agents-hackathon
FEATHERLESS_X_TITLE=Quadro CSI
FEATHERLESS_USER_AGENT=QuadroCSI/0.1 (+https://lablab.ai/ai-hackathons/band-of-agents-hackathon)
QUADRO_USE_FEATHERLESS=0
```

Set `QUADRO_USE_FEATHERLESS=1` only when ready to spend credits on a captured
partner proof run.

## Minimal Partner Proof

After Featherless access is activated:

1. Run a normal Quadro review.
2. Let Quadro compute the deterministic decision packet first.
3. Send only the compact state path to Featherless.
4. Ask Featherless to summarize the decision, evidence basis, and human gate.
5. Save model ID, response, timestamp, and usage if returned.
6. Show the result as `Featherless AI verifier`, not as the source of the
   decision.

## Verify Setup

Dry setup check:

```bash
.venv/bin/python scripts/verify_featherless_setup.py
```

Live capped check:

```bash
.venv/bin/python scripts/verify_featherless_setup.py --live
```

The live check should be run only after the promo/access flow is complete.

## Captured Proof And Current Gate

Quadro captured a standalone Featherless verifier run on 2026-06-12:

```text
Artifact: audit/partner_capture_20260612T192004Z.json
Model: Qwen/Qwen2.5-7B-Instruct
Dataset: 02_block_revoked_consent
Quadro outcome: SAY_NO
Gate: stopped_consent_revoked
Evidence items: 13
Featherless usage: 1072 total tokens
```

Verifier readout:

```text
- Outcome: SAY_NO due to revoked consent.
- Gate: stopped_consent_revoked.
- Evidence Basis: Consent was withdrawn by the Customer Account Admin, requiring new written authorization.
- Human Next Step: Collect new written authorization from the customer before proceeding.
```

The latest integrated submission capture reached Band successfully and
Featherless returned a live post-decision verifier readout:

```text
Artifact: audit/submission_demo_20260616T051948Z.json
Band publish: true, 4 events
Quadro outcome: SAY_NO
Featherless verifier: true
Model: Qwen/Qwen2.5-7B-Instruct
Usage: 1065 total tokens
Partner errors: {}
```

The repeatable capture command is:

```bash
.venv/bin/python scripts/run_submission_demo_capture.py --providers featherless --live
```

## Combined Partner Capture

When AI/ML API and Featherless are both configured, run one combined proof:

```bash
.venv/bin/python scripts/run_submission_demo_capture.py --providers aimlapi featherless --live
```

That capture keeps the deterministic Quadro decision packet first, then records
each partner verifier readout beside the same review.

Latest integrated proof:

```text
Artifact: audit/submission_demo_20260616T051948Z.json
Featherless verifier: true
AI/ML API verifier: true
Partner errors: {}
```
