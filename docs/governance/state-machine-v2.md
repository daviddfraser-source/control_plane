# Governance State Machine v2

Date: 2026-02-28
Schema: `.governance/event-schema.v2.json`

## Runtime Statuses

- `pending`
- `preflight`
- `in_progress`
- `stalled`
- `review`
- `escalated`
- `done`
- `failed`
- `blocked`

## Transition Rules

- `pending -> preflight` when `preflight_required=true` on claim.
- `pending -> in_progress` on claim without preflight requirement.
- `preflight -> in_progress` on `preflight-approve`.
- `preflight -> pending` on `preflight-return`.
- `in_progress -> stalled` when heartbeat threshold exceeded.
- `stalled -> in_progress` on heartbeat resume.
- `in_progress -> review` when `review_required=true` and done is submitted.
- `review -> done` on `review-submit APPROVE`.
- `review -> in_progress` on `review-submit REJECT`.
- `review -> escalated` on `review-submit ESCALATE` or max reject cycles.

## Event Families

- `preflight_*`
- `heartbeat`, `stalled`, `resumed_from_stalled`
- `review_*`
- `template_*`
- `ontology_*`
- Existing lifecycle events (`started`, `completed`, `failed`, `noted`) remain valid.
