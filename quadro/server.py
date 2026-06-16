from __future__ import annotations

import json
import os
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .demo import run_quadro_workflow
from .document_sets import document_set_summaries, load_document_set
from .env import load_dotenv
from .band_publish import publish_workflow_to_band
from .tool_stack import get_tool_stack

ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT / "app" / "static"
LIVE_BAND_AUDIT = ROOT / "audit" / "band_live_run_2026-05-31.json"


class QuadroHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path in {"/", "/index.html"}:
            self._send_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
            return
        if self.path == "/app.js":
            self._send_file(STATIC_DIR / "app.js", "application/javascript")
            return
        if self.path == "/styles.css":
            self._send_file(STATIC_DIR / "styles.css", "text/css")
            return
        if self.path.startswith("/assets/"):
            asset_path = (STATIC_DIR / self.path.lstrip("/")).resolve()
            if not asset_path.is_relative_to((STATIC_DIR / "assets").resolve()):
                self.send_error(404)
                return
            content_type = (
                mimetypes.guess_type(asset_path.name)[0] or "application/octet-stream"
            )
            self._send_file(asset_path, content_type)
            return
        if self.path == "/api/status":
            self._send_json(
                {
                    "ok": True,
                    "system": "Quadro",
                    "mode": os.getenv("QUADRO_MODE", "local"),
                    "gate": (
                        "band_live_room_verified"
                        if LIVE_BAND_AUDIT.exists()
                        else "local_persistent_runtime_until_band_credentials"
                    ),
                }
            )
            return
        if self.path == "/api/tool-stack":
            self._send_json({"stack": get_tool_stack()})
            return
        if self.path == "/api/document-sets":
            self._send_json({"document_sets": document_set_summaries()})
            return
        if self.path.startswith("/api/document-sets/"):
            set_id = self.path.rsplit("/", 1)[-1]
            try:
                self._send_json(load_document_set(set_id))
            except FileNotFoundError:
                self.send_error(404)
            return
        self.send_error(404)

    def do_POST(self) -> None:
        if self.path == "/api/run-workflow":
            body = self._json_body()
            result = run_quadro_workflow(
                revisit=True,
                operator_message=body.get("message", ""),
                uploaded_docs=body.get("documents", []),
            )
            result["band_publish"] = publish_workflow_to_band(result)
            self._send_json(result)
            return
        if self.path == "/api/run-workflow/no-revisit":
            body = self._json_body()
            result = run_quadro_workflow(
                revisit=False,
                operator_message=body.get("message", ""),
                uploaded_docs=body.get("documents", []),
            )
            result["band_publish"] = publish_workflow_to_band(result)
            self._send_json(result)
            return
        if self.path == "/api/intake-assist":
            body = self._json_body()
            self._send_json(
                run_quadro_workflow(
                    revisit=False,
                    operator_message=body.get("message", ""),
                    task_mode="intake_assist",
                    uploaded_docs=body.get("documents", []),
                )
            )
            return
        self.send_error(404)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send_file(self, path: Path, content_type: str) -> None:
        if not path.exists():
            self.send_error(404)
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload: object) -> None:
        body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if not length:
            return {}
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}


def main() -> None:
    load_dotenv(ROOT / ".env")
    host = os.getenv("QUADRO_HOST", "127.0.0.1")
    port = int(os.getenv("QUADRO_PORT", "8867"))
    server = ThreadingHTTPServer((host, port), QuadroHandler)
    print(f"Quadro server running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
