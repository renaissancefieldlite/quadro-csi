# Dataset Acceptance

Quadro CSI includes public-safe regulated workflow packs that test the review
chain against specific decision conditions.

These are not private customer records. They are acceptance packs with
manifests, source documents, CSV/JSON/log rows, and expected outcomes.

Run:

```bash
.venv/bin/python scripts/run_document_sets.py
```

For the side-by-side stabilization comparison, run:

```bash
.venv/bin/python scripts/compare_input_cohesion.py
```

## Matrix

| Pack | Domain | Expected outcome | Condition tested |
| --- | --- | --- | --- |
| `01_pass_scoped_refund` | Customer refund | `APPROVE` | Consent, amount, and approval policy are present. |
| `02_block_revoked_consent` | Data export | `SAY_NO` | Customer authorization was withdrawn. |
| `03_block_missing_approval_policy` | Financial credit | `NEED_MORE_INFO` | Financial action lacks approval-policy evidence. |
| `04_revisit_consent_narrowed` | Consent reroute | `APPROVE` | Consent changes and agents rerun the review. |
| `05_insurance_claim_approve` | Insurance | `APPROVE` | Covered claim has consent, loss estimate, and policy. |
| `06_banking_kyc_missing_approval` | Banking | `NEED_MORE_INFO` | Wire exception lacks KYC approval evidence. |
| `07_legal_authority_revoked` | Legal | `SAY_NO` | Client authority was withdrawn. |
| `08_government_procurement_policy_block` | Government procurement | `SAY_NO` | Vendor screen hits a policy prohibition. |
| `09_cybersecurity_incident_need_more_info` | Cybersecurity disclosure | `NEED_MORE_INFO` | External disclosure lacks legal/compliance approval. |

## Demo Wording

```text
Quadro was pre-tested against nine public-safe regulated workflow packs. Each
pack declares an expected decision gate, and the runner fails if the agent chain
returns the wrong outcome.
```

```text
Quadro was also run with input cohesion off and on against the same packs. Both
paths kept the correct decisions; the stabilized path added nine state packets
and 25 more evidence hits with zero outcome drift.
```
