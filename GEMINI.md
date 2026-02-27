# Substrate - Gemini CLI Integration

This project uses packet-based governance for multi-agent coordination.
Constitutional baseline: `constitution.md`.

## Your Role as Gemini

You are an execution agent working within a governed workflow. You:
- claim packets via CLI before starting work
- execute within packet scope only
- mark packets done with evidence
- cannot skip validation or dependency rules

## Quick Start

0. If this is a fresh project clone, initialize scaffold:
```bash
scripts/init-scaffold.sh templates/wbs-codex-minimal.json
```

1. Bootstrap session context:
```bash
python3 .governance/wbs_cli.py briefing --format json
```

2. See available work:
```bash
python3 .governance/wbs_cli.py ready
```

3. Claim a packet:
```bash
python3 .governance/wbs_cli.py claim <PACKET_ID> gemini
```

4. Inspect packet context bundle:
```bash
python3 .governance/wbs_cli.py context <PACKET_ID> --format json --max-events 40 --max-notes-bytes 4000
```

5. Check current status:
```bash
python3 .governance/wbs_cli.py status
```

6. Mark complete with evidence:
```bash
python3 .governance/wbs_cli.py done <PACKET_ID> gemini "Created X, validated Y, evidence in Z" --risk none
```

## Packet Execution Rules

Read `AGENTS.md` for the full operating contract. Key rules:
- scope adherence: execute packet-defined required actions only
- evidence requirement: every `done` includes artifact paths + validation summary
- no silent scope expansion
- validation expected before completion
- if blocked or invalid, use `fail` with explicit reason

## Skills Available

Custom Gemini skills are in `scripts/`:
- `gc-ready`: Check for available packets
- `gc-claim`: Claim a packet
- `gc-done`: Mark a packet as done with evidence
- `gc-status`: Check project status

These are wrappers around the governance CLI.

### Advanced Skills (Agent-Only)
- `wbs-report`: Generate a comprehensive markdown status report.
- `deep-code-review`: Perform a deep, context-aware code review of recent changes.
- `architecture-check`: Verify code changes align with documented architecture and WBS.


## File Locations

- governance CLI: `.governance/wbs_cli.py`
- packet definitions: `.governance/wbs.json`
- runtime state: `.governance/wbs-state.json` (do not edit directly)
- packet schema: `.governance/packet-schema.json`
- agent profiles: `.governance/agents.json`

## What Not To Do

- do not modify `.governance/wbs-state.json` directly
- do not edit packet lifecycle state outside CLI commands
- do not claim multiple packets without user approval
- do not mark packets done without concrete evidence

## Typical Workflow

1. `ready`
2. user confirms packet
3. `claim <id> gemini`
4. execute packet scope
5. run validation checks
6. `done <id> gemini "evidence" --risk none`
7. report result

## Error Handling

- if claim fails due dependencies: run `status` or `ready`
- if completion fails: fix validation gaps and retry
- if blocked: mark packet `failed` with reason
- if session must transfer mid-packet: use `handover` then next session uses `resume`

See `docs/PLAYBOOK.md` and `docs/governance-workflow-codex.md` for recovery patterns.
