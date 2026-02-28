import argparse
import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from governed_platform.governance.engine import GovernanceEngine
from governed_platform.governance.state_manager import StateManager
from governed_platform.governance.rbac import role_allows


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_definition(repo_root: Path) -> dict:
    return json.loads((repo_root / ".governance" / "wbs.json").read_text())


def _build_engine(repo_root: Path) -> GovernanceEngine:
    state_path = repo_root / ".governance" / "wbs-state.json"
    return GovernanceEngine(_load_definition(repo_root), StateManager(state_path))


class GovernanceApiHandler(BaseHTTPRequestHandler):
    server_version = "SubstrateGovernanceAPI/1.0"

    def _json(self, code: int, payload: dict) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        data = self.rfile.read(length) if length > 0 else b"{}"
        return json.loads(data.decode("utf-8"))

    def do_GET(self):
        if self.path == "/healthz":
            self._json(HTTPStatus.OK, {"ok": True})
            return
        self._json(HTTPStatus.NOT_FOUND, {"ok": False, "message": "not found"})

    def do_POST(self):
        repo_root = _repo_root()
        engine = _build_engine(repo_root)
        body = self._read_json()
        role = str(body.get("role") or "operator").lower()
        action = ""
        ok = False
        msg = "unsupported"
        if self.path == "/v1/claim":
            action = "claim"
            if not role_allows(role, action):
                self._json(HTTPStatus.FORBIDDEN, {"ok": False, "message": "forbidden"})
                return
            ok, msg = engine.claim(body["packet_id"], body.get("agent", "api"), body.get("context_attestation"))
        elif self.path == "/v1/done":
            action = "done"
            if not role_allows(role, action):
                self._json(HTTPStatus.FORBIDDEN, {"ok": False, "message": "forbidden"})
                return
            ok, msg = engine.done(body["packet_id"], body.get("agent", "api"), body.get("notes", ""))
        elif self.path == "/v1/note":
            action = "note"
            if not role_allows(role, action):
                self._json(HTTPStatus.FORBIDDEN, {"ok": False, "message": "forbidden"})
                return
            ok, msg = engine.note(body["packet_id"], body.get("agent", "api"), body.get("notes", ""))
        elif self.path == "/v1/fail":
            action = "fail"
            if not role_allows(role, action):
                self._json(HTTPStatus.FORBIDDEN, {"ok": False, "message": "forbidden"})
                return
            ok, msg = engine.fail(body["packet_id"], body.get("agent", "api"), body.get("reason", ""))
        elif self.path == "/v1/status":
            self._json(HTTPStatus.OK, {"ok": True, "state": engine.status()})
            return
        else:
            self._json(HTTPStatus.NOT_FOUND, {"ok": False, "message": "not found"})
            return

        status = HTTPStatus.OK if ok else HTTPStatus.BAD_REQUEST
        self._json(status, {"ok": ok, "action": action, "message": msg})


def main() -> None:
    parser = argparse.ArgumentParser(description="Substrate governance API server")
    parser.add_argument("--host", default=os.environ.get("GOV_API_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("GOV_API_PORT", "8081")))
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), GovernanceApiHandler)
    print(f"Governance API server listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

