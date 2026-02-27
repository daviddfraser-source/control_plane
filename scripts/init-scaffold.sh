#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

WBS_TEMPLATE="${1:-.governance/wbs.json}"
WBS_FILE=".governance/wbs.json"
STATE_FILE=".governance/wbs-state.json"

if [[ ! -f "${WBS_TEMPLATE}" ]]; then
  echo "Missing WBS template: ${WBS_TEMPLATE}"
  exit 1
fi

if [[ "${WBS_TEMPLATE}" != "${WBS_FILE}" ]]; then
  echo "Installing scaffold definition into ${WBS_FILE}..."
  cp "${WBS_TEMPLATE}" "${WBS_FILE}"
else
  echo "Using resident scaffold definition: ${WBS_FILE}"
fi

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
