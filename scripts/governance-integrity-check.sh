#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

echo "[governance] strict WBS validation"
python3 .governance/wbs_cli.py validate --strict

echo "[governance] packet schema validation"
python3 .governance/wbs_cli.py validate-packet .governance/wbs.json

echo "[governance] dependency graph check"
python3 .governance/wbs_cli.py graph >/tmp/wbs-graph.txt

echo "[governance] log integrity check"
python3 .governance/wbs_cli.py verify-log >/tmp/wbs-verify-log.txt

echo "[governance] session context generation"
python3 scripts/generate-session-brief.py >/tmp/wbs-session-brief.txt

echo "[governance] packet bundle smoke"
ready_packet=$(python3 .governance/wbs_cli.py ready --json | python3 -c 'import json,sys;d=json.load(sys.stdin);print((d.get("ready") or [{}])[0].get("id",""))')
if [[ -n "${ready_packet}" ]]; then
  python3 scripts/generate-packet-bundle.py "${ready_packet}" >/tmp/wbs-packet-bundle.txt
fi

echo "governance-integrity-check: OK"
