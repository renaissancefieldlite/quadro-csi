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

Live Render URL:

```text
https://quadro-csi-private-demo.onrender.com
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
https://quadro-csi-private-demo.onrender.com

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

## 2026-07-15 Render Verification Receipt

- GitHub commit deployed by Render: `5ddc6b9`.
- Render Blueprint ID: `exs-d9c06imcjfls738pjlfg`.
- Render Service ID: `srv-d9c06s6cjfls738pk5o0`.
- Render dashboard showed the deploy as `live`.
- Live service URL:
  - `https://quadro-csi-private-demo.onrender.com`
- Live smoke checks passed:
  - `/api/demo-session` returned `200`, `gate_enabled: true`, `authenticated: false`, `remaining: 2`.
  - unauthenticated `/api/status` returned `401` with `demo_password_required`.
  - `/api/demo-login` accepted the approved password and returned `authenticated: true`.
  - authenticated `/api/status` returned `ok: true`, `system: Quadro`.
  - one live workflow run returned `200` and decremented the private-demo session to `1` run remaining.
