from __future__ import annotations

import json
import mimetypes
import os
import secrets
import time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .demo import run_quadro_workflow
from .document_sets import document_set_summaries, load_document_set
from .env import load_dotenv
from .band_publish import publish_workflow_to_band
from .tool_stack import get_tool_stack

ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT / "app" / "static"
LIVE_BAND_AUDIT = ROOT / "audit" / "band_live_run_2026-05-31.json"
DEMO_SESSIONS: dict[str, dict[str, int | float]] = {}


def demo_gate_enabled() -> bool:
    return os.getenv("QUADRO_DEMO_GATE", "0").strip().lower() in {"1", "true", "yes"}


def demo_password() -> str:
    return os.getenv("QUADRO_DEMO_PASSWORD", "")


def demo_max_uses() -> int:
    return max(1, int(os.getenv("QUADRO_DEMO_MAX_USES", "2")))


class QuadroHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in {"/", "/index.html"}:
            self._send_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
            return
        if path == "/app.js":
            self._send_file(STATIC_DIR / "app.js", "application/javascript")
            return
        if path == "/styles.css":
            self._send_file(STATIC_DIR / "styles.css", "text/css")
            return
        if path.startswith("/assets/"):
            asset_path = (STATIC_DIR / path.lstrip("/")).resolve()
            if not asset_path.is_relative_to((STATIC_DIR / "assets").resolve()):
                self.send_error(404)
                return
            content_type = (
                mimetypes.guess_type(asset_path.name)[0] or "application/octet-stream"
            )
            self._send_file(asset_path, content_type)
            return
        if path == "/api/demo-session":
            self._send_json(self._demo_session_payload())
            return
        if path.startswith("/api/") and not self._demo_authorized():
            self._send_json({"ok": False, "error": "demo_password_required"}, 401)
            return
        if path == "/api/status":
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
        if path == "/api/tool-stack":
            self._send_json({"stack": get_tool_stack()})
            return
        if path == "/api/document-sets":
            self._send_json({"document_sets": document_set_summaries()})
            return
        if path.startswith("/api/document-sets/"):
            set_id = path.rsplit("/", 1)[-1]
            try:
                self._send_json(load_document_set(set_id))
            except FileNotFoundError:
                self.send_error(404)
            return
        self.send_error(404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/demo-login":
            body = self._json_body()
            expected_password = demo_password()
            if not expected_password or body.get("password") != expected_password:
                self._send_json({"ok": False, "error": "incorrect_password"}, 403)
                return
            session_id = secrets.token_urlsafe(24)
            DEMO_SESSIONS[session_id] = {"uses": 0, "created_at": time.time()}
            self._send_json(
                self._demo_session_payload(session_id=session_id),
                headers={
                    "Set-Cookie": (
                        f"quadro_demo={session_id}; Path=/; HttpOnly; "
                        "SameSite=Lax; Max-Age=604800"
                    )
                },
            )
            return
        if path.startswith("/api/") and not self._demo_authorized():
            self._send_json({"ok": False, "error": "demo_password_required"}, 401)
            return
        if path in {"/api/run-workflow", "/api/run-workflow/no-revisit", "/api/intake-assist"}:
            if not self._demo_use_available():
                self._send_json(
                    {
                        "ok": False,
                        "error": "demo_use_limit_reached",
                        "demo_session": self._demo_session_payload(),
                    },
                    429,
                )
                return
        if path == "/api/run-workflow":
            body = self._json_body()
            result = run_quadro_workflow(
                revisit=True,
                operator_message=body.get("message", ""),
                uploaded_docs=body.get("documents", []),
            )
            result["band_publish"] = publish_workflow_to_band(result)
            self._consume_demo_use()
            result["demo_session"] = self._demo_session_payload()
            self._send_json(result)
            return
        if path == "/api/run-workflow/no-revisit":
            body = self._json_body()
            result = run_quadro_workflow(
                revisit=False,
                operator_message=body.get("message", ""),
                uploaded_docs=body.get("documents", []),
            )
            result["band_publish"] = publish_workflow_to_band(result)
            self._consume_demo_use()
            result["demo_session"] = self._demo_session_payload()
            self._send_json(result)
            return
        if path == "/api/intake-assist":
            body = self._json_body()
            result = run_quadro_workflow(
                revisit=False,
                operator_message=body.get("message", ""),
                task_mode="intake_assist",
                uploaded_docs=body.get("documents", []),
            )
            self._consume_demo_use()
            result["demo_session"] = self._demo_session_payload()
            self._send_json(result)
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

    def _send_json(
        self,
        payload: object,
        status: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
        body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        for key, value in (headers or {}).items():
            self.send_header(key, value)
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

    def _demo_session_id(self) -> str | None:
        cookie_header = self.headers.get("Cookie", "")
        if not cookie_header:
            return None
        cookie = SimpleCookie()
        cookie.load(cookie_header)
        if "quadro_demo" not in cookie:
            return None
        session_id = cookie["quadro_demo"].value
        return session_id if session_id in DEMO_SESSIONS else None

    def _demo_session_payload(self, session_id: str | None = None) -> dict:
        gate = demo_gate_enabled()
        session_id = session_id or self._demo_session_id()
        session = DEMO_SESSIONS.get(session_id or "")
        max_uses = demo_max_uses()
        used = int(session.get("uses", 0)) if session else 0
        return {
            "gate_enabled": gate,
            "authenticated": bool(session) or not gate,
            "max_uses": max_uses,
            "used": used,
            "remaining": max(0, max_uses - used),
        }

    def _demo_authorized(self) -> bool:
        return not demo_gate_enabled() or bool(self._demo_session_id())

    def _demo_use_available(self) -> bool:
        if not demo_gate_enabled():
            return True
        session_id = self._demo_session_id()
        if not session_id:
            return False
        return int(DEMO_SESSIONS[session_id]["uses"]) < demo_max_uses()

    def _consume_demo_use(self) -> None:
        if not demo_gate_enabled():
            return
        session_id = self._demo_session_id()
        if session_id:
            DEMO_SESSIONS[session_id]["uses"] = int(DEMO_SESSIONS[session_id]["uses"]) + 1


def main() -> None:
    load_dotenv(ROOT / ".env")
    host = os.getenv("QUADRO_HOST", "127.0.0.1")
    port = int(os.getenv("PORT") or os.getenv("QUADRO_PORT", "8867"))
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
