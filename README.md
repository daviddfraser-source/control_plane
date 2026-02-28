# Substrate

[![CI](https://github.com/daviddfraser-source/Substrate/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/daviddfraser-source/Substrate/actions/workflows/test.yml)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](#get-started)
[![Open in GitHub Codespaces](https://img.shields.io/badge/dev-GitHub%20Codespaces-24292f?logo=github)](https://codespaces.new/daviddfraser-source/Substrate)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Formal packet/state-machine orchestration for multi-agent software delivery, with dependency gating, file-backed state, and auditable lifecycle logs.

Constitutional governance baseline: `constitution.md`.

![WBS Dashboard](docs/assets/wbs-dashboard.png)

## Why This Exists

Teams using agentic workflows need deterministic coordination mechanics when multiple actors touch the same work graph.

This project provides a technical control plane for common failure modes:
- work drift between planned and delivered outcomes
- race conditions during packet claiming/completion
- weak audit trails for ownership, transitions, and evidence

The approach is intentionally simple and inspectable:
- explicit packet lifecycle (`pending`, `preflight`, `in_progress`, `stalled`, `review`, `escalated`, `done`, `failed`, `blocked`)
- dependency graph gating before execution
- file-based state in `.governance/wbs-state.json`
- append-only activity log entries on lifecycle events
- atomic writes and lock-aware update flows

Operational defaults:
- heartbeat interval default: `900s` (15 minutes)
- stall threshold default: `2x` heartbeat interval (`1800s`)
- preflight timeout default: `3600s` (returns packet to `pending`)

## Get Started

Primary product UX is the Next.js app in `ui`.

```bash
cd ui
npm install
npm run dev -- --port 3001
```

Open `http://localhost:3001`.

Control-plane dashboard (`python3 start.py --dashboard`) is still available for governance operations, but it is not the primary app UX.
`/dev/*` routes are enabled by default in local development and feature-gated in production (`ENABLE_DEV_CONTROL_PLANE=1` or `NEXT_PUBLIC_ENABLE_DEV_CONTROL_PLANE=1`).

### New Project Initialization (3 Steps)

```bash
# 1) Bootstrap from the canonical WBS definition
scripts/init-scaffold.sh

# 2) Confirm first ready packet
python3 .governance/wbs_cli.py ready

# 3) Execute first packet lifecycle
python3 .governance/wbs_cli.py claim <PACKET_ID> <agent>
python3 .governance/wbs_cli.py done <PACKET_ID> <agent> "evidence summary" --risk none
python3 .governance/wbs_cli.py note <PACKET_ID> <agent> "Evidence: <paths>"
```

Re-initialize quickly during setup:

```bash
scripts/reset-scaffold.sh
```


## How It Works

### Packet Lifecycle

```text
PENDING --claim--> PREFLIGHT --approve--> IN_PROGRESS --done--> REVIEW --approve--> DONE
   |                                      |  ^                      |                   |
   |                                      |  | heartbeat resume     | reject            |
   |                                      v  |                      v                   |
   +-------------- claim (no preflight) STALLED                 IN_PROGRESS        unblocks
                                                                                     downstream
IN_PROGRESS --fail--> FAILED ---> BLOCKED
```

### Runtime Architecture

```mermaid
flowchart LR
  A[Packet Definition\n.governance/wbs.json] --> B[State Machine\n.wbs_cli.py]
  B --> C[State Store\n.governance/wbs-state.json]
  B --> D[Activity Log\nstate.log[]]
  B --> E[Dependency Gate]
  E --> B
  B --> F[Dashboard/API\n.governance/wbs_server.py]
  C --> F
```

Locking and write safety:
- packet transitions write via temp file + atomic replace
- state mutations use lock-aware flows where supported
- CLI remains source-of-truth for lifecycle transitions

### Project Structure (Where to put your code)

This repository separates **governance tooling** from **user code**:

- `src/governed_platform/`: Contains the core Substrate logic (CLI, Server, State Machine). **Do not modify** unless you are upgrading the governance system itself.
- `src/app/`: **[YOUR CODE HERE]**. This is where your application logic, business rules, and agent implementations should reside.
- `tests/`: Add your application tests here.
- `.meta/`: Local workspace/session artifacts. **Delete before publishing** template forks or release bundles.


## Commands

```bash
python3 .governance/wbs_cli.py ready
python3 .governance/wbs_cli.py claim IMP-001 codex-lead --context-attestation '["constitution.md","AGENTS.md"]'
python3 .governance/wbs_cli.py preflight IMP-001 codex-lead --assessment docs/governance/examples/preflight.json
python3 .governance/wbs_cli.py done IMP-001 codex-lead "Implemented and tested" --risk none
python3 .governance/wbs_cli.py review-claim IMP-001 codex-review
python3 .governance/wbs_cli.py review-submit IMP-001 codex-review --verdict APPROVE --assessment docs/governance/examples/review.json
python3 .governance/wbs_cli.py note IMP-001 codex-lead "Evidence: docs/path.md"
python3 .governance/wbs_cli.py risk-list --status open
python3 .governance/wbs_cli.py status
```

## Agent Support

### Claude Code

Claude reads `CLAUDE.md` at project open.

```bash
scripts/cc-ready
scripts/cc-claim <PACKET_ID>
scripts/cc-done <PACKET_ID> "evidence"
scripts/cc-status
```

Guide: `docs/claude-code-guide.md`

### Gemini

Gemini reads `GEMINI.md` at project open.

```bash
scripts/gc-ready
scripts/gc-claim <PACKET_ID>
scripts/gc-done <PACKET_ID> "evidence"
scripts/gc-status
```

### Codex

Use the same governance CLI directly:

```bash
python3 .governance/wbs_cli.py ready
python3 .governance/wbs_cli.py claim <PACKET_ID> codex-lead
```

### Human Operators

```bash
cd ui
npm run dev -- --port 3001
```

### Other LLM Agents

Any agent that can execute shell commands can use:

```bash
python3 .governance/wbs_cli.py <command>
```

## Skills

| Skill | Technical Purpose |
|---|---|
| [`skills/agent-eval`](skills/agent-eval) | Prompt/eval harness integration for regression checks |
| [`skills/security-gates`](skills/security-gates) | Static/security scanning gate patterns |
| [`skills/pr-review-automation`](skills/pr-review-automation) | Automated reviewdog-style PR review workflows |
| [`skills/precommit-governance`](skills/precommit-governance) | Pre-commit governance and repository checks |
| [`skills/ui-regression`](skills/ui-regression) | Playwright critical-path UI regression workflow |
| [`skills/observability-baseline`](skills/observability-baseline) | Baseline telemetry and trace pipeline setup |
| [`skills/skill-authoring`](skills/skill-authoring) | Scaffold and lint custom skill packages |
| [`skills/mcp-catalog-curation`](skills/mcp-catalog-curation) | Evaluate and curate MCP/tool catalog entries |

## WBS Definition

Single canonical definition:

| File | Use Case |
|---|---|
| `.governance/wbs.json` | Active WBS definition used by scaffold/init and governance CLI |

```bash
scripts/init-scaffold.sh
scripts/reset-scaffold.sh
python3 .governance/wbs_cli.py validate
```

Internal Substrate upgrade roadmap packets are archived in:
`docs/codex-migration/packets/substrate-internal-upgrade-roadmap-wbs-2026-02-17.json`.

## Scaffold vs Runtime Artifacts

Scaffold artifacts (safe to ship/commit):
- `.governance/wbs.json` (baseline packet definition)
- `scripts/init-scaffold.sh`, `scripts/reset-scaffold.sh`, `scripts/scaffold-check.sh`
- `docs/*`, `prompts/*`, `skills/*`, `src/*`

Runtime artifacts (generated during execution; do not ship):
- `.governance/wbs-state.json`
- `.governance/activity-log.jsonl` (legacy runtime log if present)
- `.governance/residual-risk-register.json`

Publishing hygiene:
- Remove `.meta/` before publishing downstream template forks or release bundles.
- Remove generated local artifact snapshots with `scripts/clean-local-artifacts.sh`.
- Preview removable release artifacts with `scripts/clean-release-artifacts.sh` (dry-run).
- Remove removable release artifacts with `scripts/clean-release-artifacts.sh --apply`.
- Run `python3 .governance/wbs_cli.py validate` before release.

## Shipping Policy

Use source-only shipping for this clone-and-own repository. Do not ship installed dependencies or generated build artifacts.

- Policy document: `docs/shipping/source-only-shipping-contract.md`
- Release bundles must be produced from git history (commit/tag), not workspace snapshots.
- Packaging command: `scripts/package-source-release.sh [<git-ref>] [<output-dir>]`

## Troubleshooting

- `Packet viewer API unavailable (HTTP 404)`
  - This affects control-plane routes only.
  - Start control-plane server with `python3 start.py --dashboard --port 8090` or `python3 .governance/wbs_server.py 8090`.

- `Failed to execute 'json' on 'Response'` / `Unexpected end of JSON input`
  - This affects control-plane API routes (WBS server), not the primary product app routes.
  - Restart the control-plane server and retry on the correct port.

- `Not initialized. Run: python3 .governance/wbs_cli.py init .governance/wbs.json`
  - Initialize state file before dashboard/CLI lifecycle commands.

- Dependency not met when claiming a packet
  - Run `python3 .governance/wbs_cli.py ready` and complete upstream dependencies first.

- State file appears inconsistent after interruption
  - Re-open status with `python3 .governance/wbs_cli.py status`.
  - Re-run `python3 .governance/wbs_cli.py validate` and inspect `.governance/wbs-state.json` + recent log entries.

## Architecture Notes

Governance enhancement design is in `docs/governance/prd-sub-2026-002-execution-contract.md`.
State/event contract is in `docs/governance/state-machine-v2.md` and `.governance/event-schema.v2.json`.
Ontology guidance is in `docs/ontology.md` and `docs/ontology.json`.

Ontology enforcement depth (current):
- deterministic token and phrase checks only (no NLP semantic inference)
- checks include entity token presence, anti-alias usage, anti-conflation pairs, relationship direction/inversion phrases, and invariant assertion hooks
- drift check mode is heuristic (`token-consistency-heuristic` + notes coverage), not full semantic drift inference

## Testing

```bash
python3 -m unittest discover -s tests -v
```

## License

MIT.
