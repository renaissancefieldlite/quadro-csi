# GitLab Transcend Devpost Copy

## Project Title

Quadro CSI

## Short Description

Quadro CSI gives GitLab Duo a consent-aware review skill that turns issues,
work items, merge requests, and source documents into source-backed decision
packets.

## Long Description

Quadro CSI is a regulated review workspace adapted for the GitLab Duo Agent
Platform. It helps a team decide whether a GitLab work item, issue, merge
request, or Orbit-facing delivery decision is ready to proceed.

The core workflow is a multi-agent audit chain. Input Cohesion first stabilizes
the request, source scope, approval signals, correction markers, missing
evidence cues, policy-blocker cues, and next gate. Customer Intake frames the
requested action and owner. Evidence Spine retrieves source-backed support and
flags missing evidence. Policy/Risk checks consent, authorization, approval
requirements, escalation needs, and blockers. Decision Packet returns approve,
say no, or need more information with a plain-English audit packet.

For the GitLab Transcend Showcase track, Quadro is packaged with a project-level
`AGENTS.md` file and a GitLab Duo Agent Skill at
`skills/quadro-orbit-review/SKILL.md`. The skill is slash-command ready as
`/quadro-orbit-review` where GitLab Duo custom skills are enabled.

The project includes a runnable proof path, not a static mockup. The local demo
runs nine public-safe acceptance packs covering approval, revoked consent,
missing approval, insurance, banking, legal authority, government procurement,
cybersecurity disclosure, and consent reroute cases. The same review story is
shown in the local UI and public demo assets.

## Built With

- GitLab Duo Agent Platform project instructions
- GitLab Agent Skills
- Python
- SQLite / FTS
- JSONL audit logs
- Public-safe acceptance packs
- Optional Band, Featherless AI, and AI/ML API verifier lanes

## Run

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run_quadro_demo.py
```

Expected result:

```text
Quadro demo passed: all acceptance sets returned expected outcomes.
```

## Links

- GitLab project: `https://gitlab.com/gitlab-ai-hackathon/transcend/39470572`
- Public website demo: `https://renaissancefieldlite.com/quadro-csi/`
- GitHub mirror: `https://github.com/renaissancefieldlite/quadro-csi`
