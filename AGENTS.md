# AGENTS.md

## Purpose
Operating contract for Codex sessions in this repository.

Constitutional authority: `constitution.md` (invariant governance rules).

Use this file as executable governance, not background documentation.
- It defines how work is planned, executed, validated, and closed.
- It should be referenced at session start, before major execution, and at closeout.
- If instructions conflict, user instruction wins, then this file, then defaults.
- For governance-rule interpretation conflicts across repo docs, `constitution.md` takes precedence.

## How To Use This File
- New project initialization (day-0):
  - run `scripts/init-scaffold.sh`
  - verify `python3 .governance/wbs_cli.py ready` returns the expected first packet
  - begin lifecycle with `claim` -> `done --risk none` -> `note`
- At session start:
  - run `python3 .governance/wbs_cli.py briefing --format json` and review summary before claiming
  - confirm active WBS scope and ready packet(s)
  - after claim, load packet context with `python3 .governance/wbs_cli.py context <packet_id> --format json`
  - confirm owner and expected output artifact
- During execution:
  - follow packet lifecycle (`claim` -> `preflight` when required -> execute -> `heartbeat` for long runs -> `done`/`fail` -> `review` when required -> `note`)
  - if session transfer is required, use governed continuity commands (`handover` -> `resume`)
  - keep evidence paths current in packet notes
- At closeout:
  - provide full delivery report in chat
  - record Level-2 drift assessment via `closeout-l2` when applicable

## WBS Execution Rules
- Use `.governance/wbs_cli.py` as the source of truth for packet lifecycle updates.
- Do not create or modify packets unless explicitly requested by the user.
- Prefer explicit commands over assistant-specific slash commands.
- Use `.governance/packet-schema.json` as the canonical packet content schema.
- Use `.governance/agents.json` for declared agent capability profiles and enforcement mode.
- Ensure packet definitions include required governance fields (not only title/scope).
- Packet viewer behavior should present the full packet object plus runtime state.
- When `context_manifest` is present, include `--context-attestation` on claim.
- When packets are in `review`, reviewer identity must be different from executor identity.

## Execution Discipline (Latest Practice)
- One packet at a time per agent unless user requests parallelization.
- Execute only the scoped packet intent; do not silently expand scope.
- Adhere to the core definitions in docs/ontology.md; do not invent new domain entities.
- If uncertain, prefer a short clarifying check before changing governance state.
- Every completion claim must include:
  - what changed
  - where the artifact lives
  - how it was validated

## Anti-Drift Controls
- Treat drift as expected risk in long-running agentic work.
- Control drift with:
  - explicit packet scope boundaries
  - evidence-linked completion notes
  - periodic status/log reconciliation (`status`, `log`)
  - Level-2 drift assessments at closeout
- For high-impact changes (governance, API contract, CI, security):
  - require test or command evidence in notes
  - capture residual risk and immediate next action

## Validation and Evals
- Prefer fast local validation before marking done.
- Minimum expectation for code/doc governance changes:
  - syntax/contract validation where relevant
  - impacted tests or smoke checks
- If validation is not run, say so explicitly in notes/report.
- For non-deterministic agent workflows, prefer repeatable eval scripts and persisted reports.
- Use DCL verification as part of governance validation for state-changing programs:
  - `python3 .governance/wbs_cli.py verify --all`

## Required Delivery Reporting
- If the user asks for a WBS delivery report (for a phase, area, or specific WBS ref), output a full report directly in chat.
- A full report must include:
  - Scope covered (for example: `WBS 1.0`, `1.1-1.5`)
  - Completion summary (`done/in_progress/pending/failed/blocked`)
  - Per-packet status lines including packet ID, title, owner, start/completion timestamps, and completion notes
  - Evidence source references (`.governance/wbs-state.json` and recent log entries)
  - Risks/gaps and immediate next actions
- Do not return only a single aggregate count when a full report is requested.

## Closeout Expectations
- After execution steps, report exactly what changed and what remains.
- If an action was requested but not executed, state that clearly.
- Level-2 WBS closeout (for example `1.0`, `2.0`) requires a drift assessment recorded via:
  - `python3 .governance/wbs_cli.py closeout-l2 <area_id|n> <agent> <drift_assessment.md> [notes]`
- `closeout-l2` is valid only when all packets in that Level-2 area are `done`.
- Use `docs/drift-assessment-template.md` as the default template for closeout docs.
- Drift assessment file naming convention:
  - `docs/codex-migration/drift-wbs<N>.md` (for area `<N>.0`)
- Drift assessment documents must include:
  - `## Scope Reviewed`
  - `## Expected vs Delivered`
  - `## Drift Assessment`
  - `## Evidence Reviewed`
  - `## Residual Risks`
  - `## Immediate Next Actions`
- Cryptographic hashing is not required for drift assessments in this system.

## Decision and Escalation Rules
- If blocked:
  - mark packet `failed` with clear reason and dependency impact
  - do not fabricate completion
- If behavior differs from expected contract:
  - document the gap
  - propose concrete corrective action
- If action requested was not executed:
  - state it directly in closeout report

## Operational Hygiene
- Keep commands and examples copy-pasteable.
- Keep governance docs aligned with actual CLI/API behavior.
- Use stable file paths for evidence to keep packet viewer useful.
- Keep `docs/governance-workflow-codex.md` aligned with current CLI behavior.
- Keep DCL documentation (`docs/governance/dcl-spec-v1.md`) aligned with runtime implementation and CLI commands.

## Packet Standard
- Canonical schema: `.governance/packet-schema.json`
- Human-readable standard and examples: `docs/codex-migration/packet-standard.md`

## Claude Code Agents
- Claude Code sessions must follow the same CLI-governed lifecycle as any other agent.
- Preferred execution identity: `claude` (or explicit variants like `claude-1` for multi-agent scenarios).
- Claude should not modify `.governance/wbs-state.json` directly; all lifecycle changes go through `.governance/wbs_cli.py`.
- Claude should not claim multiple packets without explicit user approval.
- Claude should collect file-level evidence and validation results before `done`.
- Claude-specific usage guidance lives in:
  - `CLAUDE.md`
  - `.claude/skills/*`
  - `docs/claude-code-guide.md`

## Gemini Agents
- Gemini sessions must follow the same CLI-governed lifecycle as any other agent.
- Preferred execution identity: `gemini`.
- Gemini should not modify `.governance/wbs-state.json` directly; all lifecycle changes go through `.governance/wbs_cli.py`.
- Gemini should not claim multiple packets without explicit user approval.
- Gemini should collect file-level evidence and validation results before `done`.
- Gemini-specific usage guidance lives in:
  - `GEMINI.md`
  - `scripts/gc-*`
