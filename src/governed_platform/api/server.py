import argparse
import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from governed_platform.governance.dcl import (
    DCL_DEFAULT_CONFIG,
    history as dcl_history,
    recover_all_journals as dcl_recover_all_journals,
    validate_config_lock as dcl_validate_config_lock,
    verify_all_detailed as dcl_verify_all_detailed,
    verify_packet_detailed as dcl_verify_packet_detailed,
)
from governed_platform.governance.engine import GovernanceEngine
from governed_platform.governance.state_manager import StateManager
from governed_platform.governance.rbac import role_allows


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_definition(repo_root: Path) -> dict:
    return json.loads((repo_root / ".governance" / "wbs.json").read_text())


def _load_state(repo_root: Path) -> dict:
    state_path = repo_root / ".governance" / "wbs-state.json"
    if not state_path.exists():
        return {}
    try:
        return json.loads(state_path.read_text())
    except Exception:
        return {}


def _load_dcl_config(repo_root: Path) -> dict:
    path = repo_root / ".governance" / "dcl-config.json"
    merged = dict(DCL_DEFAULT_CONFIG)
    if not path.exists():
        return merged
    try:
        payload = json.loads(path.read_text())
    except Exception:
        return merged
    if isinstance(payload, dict):
        merged.update(payload)
    return merged


def _integrity_report(repo_root: Path, mode: str = "fast") -> dict:
    state = _load_state(repo_root)
    state_packets = state.get("packets", {}) if isinstance(state, dict) else {}
    schema_version = str((state or {}).get("schema_version", "") or "")
    dcl_cfg = _load_dcl_config(repo_root)
    config_issues = dcl_validate_config_lock(dcl_cfg, expected_state_schema=schema_version)
    journal_reports = dcl_recover_all_journals(repo_root)
    journal_issues = [row for row in journal_reports if row.get("status") == "blocked"]

    if mode == "full":
        ok, details = dcl_verify_all_detailed(repo_root, state_packets=state_packets)
    else:
        details = {}
        ok = True
        for packet_id, packet_state in sorted(state_packets.items()):
            if not dcl_history(repo_root, packet_id):
                continue
            detail = dcl_verify_packet_detailed(repo_root, packet_id, state_packet=packet_state)
            details[packet_id] = detail
            if detail.get("issues"):
                ok = False

    verify_issues = {
        packet_id: list(payload.get("issues", []))
        for packet_id, payload in details.items()
        if payload.get("issues")
    }
    commits_verified = sum(int(payload.get("checked_commits", 0) or 0) for payload in details.values())
    return {
        "ok": bool(ok and not config_issues and not journal_issues),
        "mode": mode,
        "packet_count": len(state_packets),
        "packets_checked": len(details),
        "commits_verified": commits_verified,
        "integrity_errors": len(config_issues) + len(journal_issues) + sum(len(v) for v in verify_issues.values()),
        "config_lock": {
            "canonicalization_version": dcl_cfg.get("canonicalization_version"),
            "hash_algorithm": dcl_cfg.get("hash_algorithm"),
            "dcl_version": dcl_cfg.get("dcl_version"),
            "state_schema_version": dcl_cfg.get("state_schema_version"),
            "issues": config_issues,
        },
        "journal_recovery": {
            "reports": journal_reports,
            "issues": journal_issues,
        },
        "verification_issues": verify_issues,
    }


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
        if self.path == "/v1/integrity":
            payload = getattr(self.server, "integrity_report", {"ok": False, "message": "integrity not initialized"})
            status = HTTPStatus.OK if payload.get("ok") else HTTPStatus.SERVICE_UNAVAILABLE
            self._json(status, payload)
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
    parser.add_argument("--integrity-mode", choices=["fast", "full"], default=os.environ.get("GOV_API_INTEGRITY_MODE", "fast"))
    parser.add_argument("--integrity-strict", dest="integrity_strict", action="store_true")
    parser.add_argument("--no-integrity-strict", dest="integrity_strict", action="store_false")
    parser.set_defaults(integrity_strict=os.environ.get("GOV_API_INTEGRITY_STRICT", "1").strip().lower() not in ("0", "false", "no"))
    args = parser.parse_args()

    repo_root = _repo_root()
    report = _integrity_report(repo_root, mode=args.integrity_mode)
    if not report.get("ok") and args.integrity_strict:
        print("Startup integrity check failed (strict mode):")
        print(json.dumps(report, indent=2))
        raise SystemExit(2)
    if not report.get("ok"):
        print("Startup integrity check warning (non-strict mode):")
        print(json.dumps(report, indent=2))

    server = ThreadingHTTPServer((args.host, args.port), GovernanceApiHandler)
    server.integrity_report = report
    print(f"Governance API server listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
