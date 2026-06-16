# Demo Hosting Plan

## Key Point

GitHub Pages can host a static landing page, screenshots, docs, and the video
embed. It cannot run Quadro's Python backend, SQLite workflow, Band SDK calls,
or live API routes.

For the actual interactive app, use a small web host that can run Python.

## Recommended Setup

```text
Public GitHub repo: https://github.com/renaissancefieldlite/quadro-csi
GitHub Pages: https://renaissancefieldlite.com/quadro-csi/
Render or Railway: live Quadro Python server
Lablab Application URL: GitHub Pages fallback unless a live Render/Railway URL is added
Lablab Repository URL: public GitHub repo
```

## Render / Railway Service Shape

Start command:

```bash
python -m quadro.server
```

Required environment:

```text
QUADRO_HOST=0.0.0.0
QUADRO_PORT=<platform-provided port if required>
QUADRO_USE_AIMLAPI=0
QUADRO_PUBLISH_TO_BAND=0
```

If live Band publish is shown in the hosted demo, configure Band credentials as
platform secrets and never commit them.

## GitHub-Only Fallback

If we cannot deploy an interactive backend before submission:

- Use GitHub Pages for the project page.
- Include the screen-recorded demo video.
- Include command-line reproduction instructions.
- Include the dataset acceptance output in README/slides.

This is weaker than a live hosted app, but acceptable as a fallback if the video
clearly shows the working local product and Band run.
