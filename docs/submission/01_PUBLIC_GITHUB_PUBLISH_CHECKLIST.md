# Public GitHub Publish Checklist

This repo was built in a private workspace first. Before publishing, keep the
public repo focused on Quadro CSI and remove internal operator logs or
private-project boundary notes.

## Publish

- `README_PUBLIC.md` copied/renamed to `README.md` for the public repo.
- `LICENSE`
- `pyproject.toml`
- `app/static/`
- `quadro/`
- `scripts/`
- `tests/`
- `data/evaluation_sets/`
- `data/real_cases/quadro_product_review_case.json`
- `docs/submission/`
- `docs/public/` if created.
- `.env.example`
- `agent_config.example.yaml`
- `Launch Quadro.command` only if the public repo is meant for macOS local demo users.

## Do Not Publish

- `.env`
- `agent_config.yaml`
- `.venv/`
- `audit/`
- `private_raw_DO_NOT_UPLOAD/`
- `AGENTS.md`
- `docs/QUADRO_OPERATOR_LOG.md`
- `docs/source_packets/`
- `data/real_cases/quadro_hackathon_readiness_case.json`
- internal Band account logs with local/browser setup details
- any private memory database, raw capture, private prompt, or neighboring project artifact

## Public Boundary

The public repo should say:

```text
Quadro CSI is an original clean-room hackathon implementation for regulated
multi-agent review workflows. It uses generic engineering patterns such as
RAG, SQLite/FTS retrieval, JSONL audit logs, and role-based agent handoffs.
```

The public repo should not mention or describe private architecture layers,
private internal projects, raw captures, private memory stores, or protected
runtime mechanics.

## Publish Steps

1. Create a fresh public GitHub repo named `quadro-csi` or `quadro-band-agents`.
2. Copy only the publish list above into a clean release directory or branch.
3. Replace public README with `docs/submission/README_PUBLIC.md`.
4. Run:

```bash
.venv/bin/python -m unittest discover -s tests
.venv/bin/python scripts/run_document_sets.py
node --check app/static/app.js
.venv/bin/python scripts/check_public_boundary.py
```

5. Push to GitHub.
6. Add repo URL to lablab submission.
7. Keep secrets in hosting environment variables, not GitHub.

