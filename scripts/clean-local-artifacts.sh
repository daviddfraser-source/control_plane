#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

ARTIFACT_DIR="substrate"

if [[ -d "${ARTIFACT_DIR}" ]]; then
  find "${ARTIFACT_DIR}" -type f -delete
  find "${ARTIFACT_DIR}" -depth -type d -empty -delete
  echo "Removed local artifact tree: ${ARTIFACT_DIR}"
else
  echo "No local artifact tree found: ${ARTIFACT_DIR}"
fi
