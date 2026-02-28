#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

APPLY=0

if [[ "${1:-}" == "--apply" ]]; then
  APPLY=1
elif [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  echo "Usage: $0 [--apply]"
  echo "  default: dry-run (print directories that would be removed)"
  echo "  --apply: remove local generated/install artifacts"
  exit 0
elif [[ $# -gt 0 ]]; then
  echo "Unknown option: $1"
  echo "Usage: $0 [--apply]"
  exit 2
fi

CANDIDATES=(
  "node_modules"
  "ui/node_modules"
  ".next"
  "ui/.next"
  "dist"
  "ui/dist"
  "build"
  "ui/build"
  "substrate"
)

remove_dir() {
  local rel="$1"
  local abs
  abs="$(realpath -m "${ROOT_DIR}/${rel}")"

  # Safety guard: ensure target is inside repo root and not root itself.
  if [[ "${abs}" == "${ROOT_DIR}" || "${abs}" == "/" || "${abs}" == "" ]]; then
    echo "[CLEAN] Skip unsafe path: ${rel}"
    return
  fi
  if [[ "${abs}" != "${ROOT_DIR}"/* ]]; then
    echo "[CLEAN] Skip out-of-repo path: ${rel}"
    return
  fi

  if [[ ! -d "${abs}" ]]; then
    return
  fi

  if [[ ${APPLY} -eq 0 ]]; then
    echo "[CLEAN][dry-run] would remove: ${rel}"
    return
  fi

  find "${abs}" \( -type f -o -type l \) -delete
  find "${abs}" -depth -type d -empty -delete
  if [[ -d "${abs}" ]]; then
    # If directory still exists due to locks/permissions, report it.
    echo "[CLEAN][warn] directory still present after cleanup: ${rel}"
  else
    echo "[CLEAN] removed: ${rel}"
  fi
}

for rel in "${CANDIDATES[@]}"; do
  remove_dir "${rel}"
done

if [[ ${APPLY} -eq 0 ]]; then
  echo "[CLEAN] Dry run complete. Re-run with --apply to remove artifacts."
else
  echo "[CLEAN] Cleanup complete."
fi
