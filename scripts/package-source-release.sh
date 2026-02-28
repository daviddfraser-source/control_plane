#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

REF="${1:-HEAD}"
OUT_DIR="${2:-dist}"

if ! command -v git >/dev/null 2>&1; then
  echo "[PACKAGE] git is required"
  exit 2
fi

if ! git rev-parse --verify "${REF}^{commit}" >/dev/null 2>&1; then
  echo "[PACKAGE] Invalid git ref: ${REF}"
  exit 2
fi

mkdir -p "${OUT_DIR}"

SAFE_REF="${REF//\//-}"
SAFE_REF="${SAFE_REF//:/-}"
OUT_FILE="${OUT_DIR}/source-release-${SAFE_REF}.tar.gz"
PREFIX="orchestrated_codex-${SAFE_REF}/"

TMP_TAR="$(mktemp -t source-release-XXXXXX.tar)"
trap 'rm -f "${TMP_TAR}"' EXIT

git archive --format=tar --prefix="${PREFIX}" "${REF}" > "${TMP_TAR}"
gzip -c "${TMP_TAR}" > "${OUT_FILE}"

echo "[PACKAGE] Created: ${OUT_FILE}"
