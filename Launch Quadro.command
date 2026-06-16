#!/bin/zsh
set -u

REPO="/Users/renaissancefieldlite1.0/Documents/Playground/band_of_agents_quadro"
PORT="${QUADRO_PORT:-8867}"
URL="http://127.0.0.1:${PORT}"
LOG_PATH="${REPO}/audit/quadro_server_desktop.log"

cd "$REPO" || exit 1
mkdir -p audit

if ! /usr/sbin/lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  if [[ -x ".venv/bin/python" ]]; then
    PYTHON=".venv/bin/python"
  else
    PYTHON="$(command -v python3)"
  fi

  QUADRO_PORT="$PORT" nohup "$PYTHON" -m quadro.server > "$LOG_PATH" 2>&1 &
  sleep 1
fi

/usr/bin/open "$URL"

echo "Quadro opened at $URL"
echo "Repo: $REPO"
echo "Server log: $LOG_PATH"
echo
echo "You can close this window after the browser opens."
