# Packet Context Bundle: WBS-14-6

## Packet Summary
- ID: WBS-14-6
- WBS Ref: 14.6
- Title: Standardize optimized session startup workflow
- Area: 14.0
- Priority: HIGH
- Runtime Status: pending

## Scope
Codify startup sequence and tooling to force briefing->claim->context bundle execution discipline.

## Purpose
Codify startup sequence and tooling to force briefing->claim->context bundle execution discipline.

## Preconditions
- WBS-14-3 complete

## Required Inputs
- wbs_cli briefing/context
- AGENTS startup rules

## Required Actions
- Document packet-first startup workflow
- Add helper command/script to open briefing and bundle quickly
- Update governance docs and handoff expectations

## Required Outputs
- Startup workflow guide
- Optional helper script outputs

## Validation Checks
- Startup path is explicit and copy-pasteable
- Session transfer uses same governed context flow

## Exit Criteria
- Token/time spent on session reconstruction is reduced

## Halt Conditions
- Operators continue starting from full-repo context by default

## Dependency Context
- Depends on: none
- Dependents: none

## Recent Events
- none

## Execution Steps
1. Claim packet if not in_progress.
2. Implement only scoped changes.
3. Validate using packet-specific checks.
4. Mark done with evidence and residual risk acknowledgement.
