# Input Cohesion Comparison

Quadro can run the same document packs with input cohesion off or on.

The comparison answers one product question:

```text
Does the stabilized path improve the review chain without changing correct
decisions?
```

Run:

```bash
.venv/bin/python scripts/compare_input_cohesion.py
```

## Summary

| Metric | Baseline | Input cohesion on |
| --- | ---: | ---: |
| Document packs tested | 9 | 9 |
| Packs passed | 9 | 9 |
| Decision outcome changes | 0 | 0 |
| Stabilization packets recorded | 0 | 9 |
| Total evidence items added | 0 | 25 |
| Average evidence item lift | 0 | 2.78 |

## Read

The baseline already returns the expected decision outcomes across the nine
acceptance packs. Input cohesion does not claim to rescue a broken workflow.

The improvement is audit quality and state control:

- every review receives a stabilized starting packet;
- consent, approval, disclosure, financial, and policy-blocker signals are
  captured before handoff;
- each review records a next gate before the agents run;
- evidence retrieval is broader while final decisions stay stable.

This is the better product behavior: correct outcomes remain unchanged, while
the room has more source coverage and a clearer explanation of why the review
is moving toward approval, refusal, or more information.

## Side-By-Side Results

| Pack | Baseline outcome | Stabilized outcome | Baseline evidence | Stabilized evidence | Evidence lift | Stabilized next gate |
| --- | --- | --- | ---: | ---: | ---: | --- |
| `01_pass_scoped_refund` | `APPROVE` | `APPROVE` | 17 | 21 | +4 | Run agent review |
| `02_block_revoked_consent` | `SAY_NO` | `SAY_NO` | 10 | 13 | +3 | Run review with blocker focus |
| `03_block_missing_approval_policy` | `NEED_MORE_INFO` | `NEED_MORE_INFO` | 10 | 13 | +3 | Run review with missing evidence focus |
| `04_revisit_consent_narrowed` | `APPROVE` | `APPROVE` | 7 | 10 | +3 | Run agent review |
| `05_insurance_claim_approve` | `APPROVE` | `APPROVE` | 12 | 15 | +3 | Run agent review |
| `06_banking_kyc_missing_approval` | `NEED_MORE_INFO` | `NEED_MORE_INFO` | 10 | 13 | +3 | Run review with missing evidence focus |
| `07_legal_authority_revoked` | `SAY_NO` | `SAY_NO` | 6 | 8 | +2 | Run review with blocker focus |
| `08_government_procurement_policy_block` | `SAY_NO` | `SAY_NO` | 8 | 10 | +2 | Run review with blocker focus |
| `09_cybersecurity_incident_need_more_info` | `NEED_MORE_INFO` | `NEED_MORE_INFO` | 5 | 7 | +2 | Run review with missing evidence focus |

## Demo Line

```text
We ran Quadro with stabilization off and on against the same nine acceptance
packs. Both paths kept the correct decisions, but the stabilized path added
nine state packets and 25 more evidence hits with zero outcome drift.
```
