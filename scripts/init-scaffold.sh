#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

WBS_FILE=".governance/wbs.json"
STATE_FILE=".governance/wbs-state.json"

if [[ $# -gt 0 ]]; then
  echo "init-scaffold now uses a single canonical WBS definition: ${WBS_FILE}"
  echo "Remove template arguments and rerun."
  exit 1
fi

if [[ ! -f "${WBS_FILE}" ]]; then
  echo "Missing canonical WBS definition: ${WBS_FILE}"
  exit 1
fi

echo "Using canonical scaffold definition: ${WBS_FILE}"

echo "Validating scaffold definition before init..."
python3 .governance/wbs_cli.py validate
python3 .governance/wbs_cli.py validate-packet "${WBS_FILE}"

echo "Initializing scaffold from ${WBS_FILE}..."
python3 .governance/wbs_cli.py init "${WBS_FILE}"

echo "Generating session context artifacts..."
python3 scripts/generate-session-brief.py

if command -v pre-commit >/dev/null 2>&1 && [[ -f ".pre-commit-config.yaml" ]]; then
  echo "Installing pre-commit hooks..."
  pre-commit install
fi

echo
echo "Scaffold initialized."
echo "WBS:   ${WBS_FILE}"
echo "State: ${STATE_FILE}"
echo
echo "Briefing:"
python3 .governance/wbs_cli.py briefing
