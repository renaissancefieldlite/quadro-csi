# AI/ML API Partner Gate

AI/ML API should be used as a model-provider lane, not the source of Quadro's
decision authority.

## Role In Quadro

Use AI/ML API for:

- evidence extraction from source material;
- evidence manifest summarization;
- policy/decision explanation;
- verifier commentary on an already-computed decision packet.

Do not use AI/ML API to override:

- consent revoked;
- missing approval evidence;
- policy prohibition;
- deterministic `APPROVE`, `SAY_NO`, or `NEED_MORE_INFO` gates.

## Wait Until June 12 Kickoff

Do not spend the coupon or paid credits until kickoff confirms:

- final partner-prize rules;
- allowed models;
- whether a single verifier call is enough for meaningful use;
- any required screenshots, usage logs, or model names.

## Minimal Proof Run

After kickoff, run one capped proof:

1. Run a passing Quadro review.
2. Send only the compact evidence/policy/decision packet to AI/ML API.
3. Ask for an audit explanation.
4. Save model ID, response, token/cost usage, and timestamp.
5. Show it in the UI/video as `AI/ML verifier`, not as the decision-maker.

## Environment Variables

```text
AIMLAPI_KEY=<secret>
AIMLAPI_BASE_URL=https://api.aimlapi.com/v1
AIMLAPI_MODEL=<kickoff-approved model>
QUADRO_USE_AIMLAPI=1
```

Return to safe mode:

```text
QUADRO_USE_AIMLAPI=0
```

