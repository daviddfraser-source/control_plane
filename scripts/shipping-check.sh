#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

REF="HEAD"
CHECK_WORKSPACE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ref)
      if [[ $# -lt 2 ]]; then
        echo "Usage: $0 [--ref <git-ref>] [--workspace]"
        exit 2
      fi
      REF="$2"
      shift 2
      ;;
    --workspace)
      CHECK_WORKSPACE=1
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [--ref <git-ref>] [--workspace]"
      echo "  --ref <git-ref>   Validate archive content from this ref (default: HEAD)"
      echo "  --workspace       Also fail if forbidden local artifact directories currently exist"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--ref <git-ref>] [--workspace]"
      exit 2
      ;;
  esac
done

if ! command -v git >/dev/null 2>&1; then
  echo "[SHIP-CHECK] git is required"
  exit 2
fi

if ! git rev-parse --verify "${REF}^{commit}" >/dev/null 2>&1; then
  echo "[SHIP-CHECK] Invalid git ref: ${REF}"
  exit 2
fi

# Forbidden artifact patterns in shipped source trees.
FORBIDDEN_REGEX='(^|/)node_modules/|(^|/)\\.next/|(^|/)dist/|(^|/)build/|(^|/)substrate/'

FAIL=0

print_remediation() {
  cat <<'TXT'
[SHIP-CHECK] Remediation:
  - Remove generated/install artifacts from release contents.
  - Use source-only packaging (git archive) rather than zipping the working directory.
  - For local cleanup run: scripts/clean-release-artifacts.sh (or scripts/clean-local-artifacts.sh).
TXT
}

echo "[SHIP-CHECK] Checking tracked files at ${REF}..."
TRACKED_HITS="$(git ls-files | rg -n "${FORBIDDEN_REGEX}" || true)"
if [[ -n "${TRACKED_HITS}" ]]; then
  echo "[SHIP-CHECK] Forbidden tracked paths detected:"
  echo "${TRACKED_HITS}"
  FAIL=1
else
  echo "[SHIP-CHECK] OK: no forbidden tracked paths"
fi

echo "[SHIP-CHECK] Checking source archive content at ${REF}..."
TMP_TAR="$(mktemp -t ship-check-XXXXXX.tar)"
trap 'rm -f "${TMP_TAR}"' EXIT

git archive --format=tar "${REF}" > "${TMP_TAR}"
ARCHIVE_HITS="$(tar -tf "${TMP_TAR}" | rg -n "${FORBIDDEN_REGEX}" || true)"
if [[ -n "${ARCHIVE_HITS}" ]]; then
  echo "[SHIP-CHECK] Forbidden paths present in archive:"
  echo "${ARCHIVE_HITS}"
  FAIL=1
else
  echo "[SHIP-CHECK] OK: archive excludes forbidden artifacts"
fi

if [[ ${CHECK_WORKSPACE} -eq 1 ]]; then
  echo "[SHIP-CHECK] Checking local workspace for forbidden artifact directories..."
  WORKSPACE_HITS=""
  while IFS= read -r path; do
    [[ -z "${path}" ]] && continue
    if [[ -d "${path}" ]]; then
      WORKSPACE_HITS+="${path}"$'\n'
    fi
  done <<'PATHS'
node_modules
ui/node_modules
.next
ui/.next
dist
ui/dist
build
ui/build
substrate
PATHS

  if [[ -n "${WORKSPACE_HITS}" ]]; then
    echo "[SHIP-CHECK] Forbidden local directories exist:"
    printf '%s' "${WORKSPACE_HITS}"
    FAIL=1
  else
    echo "[SHIP-CHECK] OK: no forbidden local artifact directories"
  fi
fi

if [[ ${FAIL} -ne 0 ]]; then
  print_remediation
  exit 1
fi

echo "[SHIP-CHECK] PASS"
