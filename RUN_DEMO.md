# Run Quadro CSI

This project is meant to be run as a repository, not as a single copied Python
file. The scripts import the local `quadro/` package and load acceptance sets
from `data/evaluation_sets/`.

## Fastest Core Demo

Requirements:

- Python 3.11 or newer
- No API keys required
- No paid provider credits required

```bash
git clone https://github.com/renaissancefieldlite/quadro-csi.git
cd quadro-csi
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run_quadro_demo.py
```

Expected result:

```text
Quadro demo passed: all acceptance sets returned expected outcomes.
```

The command runs public-safe document sets that cover:

- approve scoped refund;
- say no when consent is revoked;
- need more information when approval evidence is missing;
- approve after consent is narrowed and rerouted;
- insurance, banking, legal, government procurement, and cybersecurity gates.

## Local UI Demo

After the setup above:

```bash
.venv/bin/python -m quadro.server
```

Open:

```text
http://127.0.0.1:8867
```

In the UI:

1. Choose a set under `Load Acceptance Set`.
2. Click `Load Set`.
3. Click `Send`.
4. Watch the intake, evidence, policy, and decision handoff chain update.

## Optional Live Provider / Band Setup

The core demo above is the runnable proof path. Live Band publishing, AI/ML API,
and Featherless verifier lanes are optional. They require provider credentials
and should not be required to judge the local workflow.

```bash
.venv/bin/python -m pip install -r requirements-live.txt
cp .env.example .env
```

Then add only the keys you intend to test:

```text
QUADRO_PUBLISH_TO_BAND=1
QUADRO_BAND_CHAT_ID=<band chat id>

QUADRO_USE_AIMLAPI=1
AIMLAPI_KEY=<secret>
AIMLAPI_MODEL=<model>

QUADRO_USE_FEATHERLESS=1
FEATHERLESS_API_KEY=<secret>
```

Do not commit `.env`.
