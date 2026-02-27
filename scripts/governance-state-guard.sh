#!/usr/bin/env bash
set -euo pipefail

TARGET_FILES=(
  ".governance/wbs-state.json"
  ".governance/activity-log.jsonl"
  ".governance/residual-risk-register.json"
)
OVERRIDE_TOKEN="[allow-wbs-state-edit]"

MODE="staged"
COMMIT_MSG_FILE=""
RANGE=""
CHANGED_TARGETS=()

if [[ "${1:-}" == "--ci" ]]; then
  MODE="ci"
elif [[ "${1:-}" == "--commit-msg" ]]; then
  MODE="commit-msg"
  COMMIT_MSG_FILE="${2:-}"
elif [[ "${1:-}" == "--check-tracked" ]]; then
  MODE="tracked"
fi

get_changed_files() {
  if [[ -n "${GOV_STATE_GUARD_CHANGED_FILES:-}" ]]; then
    printf "%s\n" "${GOV_STATE_GUARD_CHANGED_FILES}"
    return 0
  fi

  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "governance-state-guard: git worktree not detected; skipping"
    return 0
  fi

  case "${MODE}" in
    staged|commit-msg)
      git diff --cached --name-only
      ;;
    ci)
      if [[ -n "${GITHUB_BASE_REF:-}" ]]; then
        git fetch --no-tags --depth=1 origin "${GITHUB_BASE_REF}" >/dev/null 2>&1 || true
        RANGE="origin/${GITHUB_BASE_REF}...HEAD"
      elif git rev-parse HEAD~1 >/dev/null 2>&1; then
        RANGE="HEAD~1..HEAD"
      else
        RANGE="HEAD"
      fi
      git diff --name-only "${RANGE}"
      ;;
    *)
      git diff --cached --name-only
      ;;
  esac
}

find_changed_targets() {
  local changed_files="$1"
  CHANGED_TARGETS=()
  for target in "${TARGET_FILES[@]}"; do
    if printf "%s\n" "${changed_files}" | grep -Fxq "${target}"; then
      CHANGED_TARGETS+=("${target}")
    fi
  done
}

check_tracked_runtime_files() {
  local tracked=()

  if [[ -n "${GOV_STATE_GUARD_TRACKED_FILES:-}" ]]; then
    while IFS= read -r line; do
      [[ -n "${line}" ]] && tracked+=("${line}")
    done <<< "${GOV_STATE_GUARD_TRACKED_FILES}"
  else
    if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
      echo "governance-state-guard: git worktree not detected; skipping"
      return 0
    fi
    for target in "${TARGET_FILES[@]}"; do
      if git ls-files --error-unmatch "${target}" >/dev/null 2>&1; then
        tracked+=("${target}")
      fi
    done
  fi

  if [[ "${#tracked[@]}" -eq 0 ]]; then
    exit 0
  fi

  cat >&2 <<EOF
ERROR: runtime governance artifacts are tracked in git.
Tracked runtime files:
$(printf " - %s\n" "${tracked[@]}")

Required fix:
1) Remove tracked runtime artifacts from index:
   git rm --cached ${tracked[0]}
2) Keep runtime artifacts ignored in .gitignore.
EOF
  exit 1
}

if [[ "${MODE}" == "tracked" ]]; then
  check_tracked_runtime_files
fi

changed_files="$(get_changed_files)"
find_changed_targets "${changed_files}"
if [[ "${#CHANGED_TARGETS[@]}" -eq 0 ]]; then
  exit 0
fi

if [[ "${ALLOW_WBS_STATE_EDIT:-0}" == "1" || "${ALLOW_RUNTIME_STATE_EDIT:-0}" == "1" ]]; then
  echo "governance-state-guard: override accepted via ALLOW_WBS_STATE_EDIT=1 or ALLOW_RUNTIME_STATE_EDIT=1"
  exit 0
fi

if [[ "${MODE}" == "commit-msg" && -n "${COMMIT_MSG_FILE}" && -f "${COMMIT_MSG_FILE}" ]]; then
  if grep -Fqi "${OVERRIDE_TOKEN}" "${COMMIT_MSG_FILE}"; then
    echo "governance-state-guard: override token accepted from commit message"
    exit 0
  fi
fi

if [[ "${MODE}" == "ci" ]]; then
  commit_messages="${GOV_STATE_GUARD_COMMIT_MESSAGES:-}"
  if [[ -z "${commit_messages}" && -n "${RANGE}" ]] && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    commit_messages="$(git log --format=%B "${RANGE}" 2>/dev/null || true)"
  fi
  if [[ -n "${commit_messages}" ]] && grep -Fqi "${OVERRIDE_TOKEN}" <<<"${commit_messages}"; then
    echo "governance-state-guard: override token accepted from CI commit range"
    exit 0
  fi
fi

cat >&2 <<EOF
ERROR: direct changes to ${CHANGED_TARGETS[0]} are blocked by governance guard.
Protected runtime files:
$(printf " - %s\n" "${TARGET_FILES[@]}")

Allowed paths:
1) Run lifecycle commands through the CLI (preferred):
   python3 .governance/wbs_cli.py <claim|done|note|fail|reset|closeout-l2> ...
2) For emergency/manual corrections, include override token in commit message:
   ${OVERRIDE_TOKEN}
3) For local one-off bypass, set:
   ALLOW_WBS_STATE_EDIT=1
EOF
exit 1
