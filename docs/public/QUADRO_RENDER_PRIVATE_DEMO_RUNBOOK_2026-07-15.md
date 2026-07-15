# Quadro CSI Render Private Demo Runbook

Created: 2026-07-15

## Purpose

This is the buyer-facing private Quadro CSI demo route for direct pilot outreach.
It uses the existing Quadro runtime, public-safe sample packets, a password gate,
and a two-workflow-run limit per browser session.

## Render Settings

Use the repository:

```text
/Users/renaissancefieldlite1.0/Documents/Playground/band_of_agents_quadro
```

Render blueprint:

```text
render.yaml
```

Environment:

```text
QUADRO_HOST=0.0.0.0
QUADRO_DEMO_GATE=1
QUADRO_DEMO_PASSWORD=<set in Render during Blueprint creation>
QUADRO_DEMO_MAX_USES=2
```

Render sets `PORT` automatically. The server now reads `PORT` first, then falls
back to `QUADRO_PORT`.

`QUADRO_DEMO_PASSWORD` is declared with `sync: false` in `render.yaml`, so the
public repo does not carry the demo password. For the current pilot gate, enter
the approved password in the Render dashboard when prompted.

## Prospect Test Instructions

Send this after the Render URL exists:

```text
Private Quadro CSI pilot demo:
<RENDER_URL>

Password:
rfl123

How to test:
1. Open the link.
2. Enter the password.
3. In "Load Acceptance Set", choose a sample case.
4. Click "Load Set".
5. Click "Send".
6. Watch the intake -> evidence -> policy -> decision packet chain.

The private demo allows two workflow runs per browser session. The packets use
sample/public-safe data only.
```

## Buyer Framing

This is not the whole product. It is a controlled sample showing the workflow:

- intake.
- evidence spine.
- policy / risk review.
- human signoff logic.
- decision packet.
- optional handoff to HubSpot, Zendesk, Slack, or email in a paid pilot.

## Local Smoke Test

From the repo:

```bash
QUADRO_DEMO_GATE=1 \
QUADRO_DEMO_PASSWORD=rfl123 \
QUADRO_DEMO_MAX_USES=2 \
QUADRO_PORT=8868 \
python3 -m quadro.server
```

Open:

```text
http://127.0.0.1:8868
```

## 2026-07-15 Local Verification Receipt

- `python3 -m py_compile quadro/server.py` passed.
- `node --check app/static/app.js` passed.
- `render.yaml` parsed and includes `QUADRO_DEMO_PASSWORD` as `sync: false`.
- Local gated server tested on `127.0.0.1:8876` with:
  - unauthenticated `/api/status` blocked with `demo_password_required`.
  - `/api/demo-login` accepted the approved password.
  - authenticated `/api/status` returned `ok: true`.
  - one workflow run completed and decremented the session from `2` runs remaining to `1`.
