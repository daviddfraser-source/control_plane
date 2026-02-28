# Source-Only Shipping Contract

## Purpose
Define the release boundary for this clone-and-own repository so no installable/generated library payloads are shipped.

## Release Principle
- Ship source-only artifacts from git history.
- Never ship from ad-hoc workspace snapshots.

## Allowed Artifacts (ship)
- Source files (`src/**`, `ui/app/**`, `ui/components/**`, `ui/lib/**`, scripts, docs)
- Governance definitions and tools (`.governance/**`, excluding runtime state artifacts)
- Dependency manifests and lockfiles (for reproducible install):
  - `ui/package.json`
  - `ui/package-lock.json`

## Forbidden Artifacts (do not ship)
- Installed dependency payloads:
  - `**/node_modules/**`
- Frontend/generated build output:
  - `**/.next/**`
  - `**/dist/**`
  - `**/build/**`
- Local packaging/export snapshots:
  - `/substrate/**`
- Runtime state and logs:
  - `.governance/wbs-state.json`
  - `.governance/activity-log.jsonl`
  - `.governance/residual-risk-register.json`

## Canonical Release Method
1. Validate repository policy and quality gates.
2. Package from git commit/tag (for example via `git archive`), not from working directory zip.
3. Verify produced archive excludes forbidden artifacts.

## Operator Checklist (pre-release)
- Run shipping hygiene gate: `scripts/shipping-check.sh`
- Ensure no generated/install directories are staged/tracked.
- Build release bundle from git commit/tag only.

## Enforcement
- CI must run shipping checks on pull requests and release workflows.
- Release workflow must fail if forbidden artifacts are detected.
