# PRD-SUB-2026-002 v2 Delta Contract

Date: 2026-02-28
Status: Implementation scope freeze

## Already Delivered (Baseline)

Enhancements 1-6 from PRD v1 are already implemented in this repository:
- preflight lifecycle
- heartbeat + stalled state
- review/two-person integrity
- context governance
- golden templates
- ontology governance (deterministic profile)

## v2 Delta Scope

New implementation scope in this program:
- Deterministic Commitment Layer (DCL)
- project-level checkpoints and proof exports
- verifier-first CI posture (`verify --all`)
- API boundary for governance mutations
- database-backed state manager foundation
- RBAC/auth identity model foundation
- server-side Git audit integration service

## Non-goals for this WBS area

- Deterministic LLM output claims
- Full semantic contradiction inference engine
- Production hosted deployment automation

## Compatibility Clarification

Multi-user architecture is not only a deployment concern. It requires code changes:
- API server and transport layer
- alternate StateManager implementation (database)
- RBAC/identity policy enforcement
- workflow parity updates across CLI and UI
