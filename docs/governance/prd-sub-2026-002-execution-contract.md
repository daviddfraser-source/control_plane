# PRD-SUB-2026-002 Execution Contract

Date: 2026-02-28
Owner: governance-program

## Deterministic Decisions

- Identity model:
  - `executor`: agent that moved packet into execution (`in_progress`).
  - `reviewer`: agent that claims review; must not equal executor identity.
  - `supervisor`: actor that approves/returns preflight and handles escalations.
- Gating boundaries:
  - Hard blocks: missing dependencies, missing required context attestation, invalid preflight assessment, same-identity review claim, ontology invariant errors.
  - Soft warnings: optional context files missing, ontology anti-conflation warnings, template non-conformance.
- Migration/version policy:
  - Runtime state stays `version: 1.0` with `schema_version: 1.2` capability fields.
  - New fields are additive and backward compatible.
  - Packets without enhancement fields keep legacy behavior.
- Authority model:
  - Claiming/execution remains agent-driven.
  - Preflight decisions and escalation actions require supervisor identity.
  - Review policy defaults to `any_different_agent` with configurable max cycles.

## Lifecycle Contract

- `pending -> preflight -> in_progress -> review -> done`
- `in_progress <-> stalled`
- `review -> in_progress` (reject)
- `review -> escalated` (manual or max-cycle auto escalation)
- Existing `failed` and `blocked` paths remain valid.

## Runtime Contracts

- Preflight assessment required keys:
  - `context_confirmation`
  - `ambiguity_register`
  - `risk_flags`
  - `execution_plan`
- Heartbeat payload keys:
  - `status`
  - `decisions`
  - `obstacles`
  - `completion_estimate`
- Review assessment required keys:
  - `exit_criteria_assessment`
  - `findings`
  - `risk_flags`

## Backward Compatibility

- `preflight_required`, `review_required`, `heartbeat_required`, and `context_manifest` are opt-in packet fields.
- Repositories without `docs/ontology.json` skip ontology enforcement.
- Existing CLI flows still work for packets that do not opt in.
