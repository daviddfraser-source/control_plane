# Governance Workflow (Codex)

## Session Start

1. `python3 .governance/wbs_cli.py briefing --format json`
2. `python3 .governance/wbs_cli.py ready`
3. `python3 .governance/wbs_cli.py claim <packet_id> <agent> [--context-attestation '["constitution.md"]']`
4. `python3 .governance/wbs_cli.py context <packet_id> --format json`

## Execution

- If packet enters `preflight`:
  - `python3 .governance/wbs_cli.py preflight <packet_id> <agent> --assessment <assessment.json>`
  - `python3 .governance/wbs_cli.py preflight-approve <packet_id> <supervisor>` or `preflight-return`.
- During long-running execution:
  - `python3 .governance/wbs_cli.py heartbeat <packet_id> <agent> --status "..."`
  - `python3 .governance/wbs_cli.py check-stalled`
  - Defaults: heartbeat interval `900s`, stall threshold `1800s`, preflight timeout `3600s`
- Completion path:
  - `python3 .governance/wbs_cli.py done <packet_id> <agent> "evidence" --risk none`
  - If packet moves to review: `review-claim` then `review-submit`.

## Semantic Governance

- Validate packet output against ontology:
  - `python3 .governance/wbs_cli.py ontology validate <packet_id>`
  - Validation mode is deterministic token/phrase checks and invariant hooks (no NLP inference).
- Submit ontology extensions:
  - `python3 .governance/wbs_cli.py ontology propose --actor <agent> --payload <json>`

## Learning Loop

- Promote stable execution patterns:
  - `python3 .governance/wbs_cli.py promote <packet_id> <supervisor> --template-id <id>`
  - `python3 .governance/wbs_cli.py templates list`
