# Substrate - Claude Code Integration

This project uses packet-based governance for multi-agent coordination.
Constitutional baseline: `constitution.md`.

## Your Role as Claude

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
python3 .governance/wbs_cli.py claim <PACKET_ID> claude
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
python3 .governance/wbs_cli.py done <PACKET_ID> claude "Created X, validated Y, evidence in Z" --risk none
```

## Packet Execution Rules

Read `AGENTS.md` for the full operating contract. Key rules:
- scope adherence: execute packet-defined required actions only
- evidence requirement: every `done` includes artifact paths + validation summary
- no silent scope expansion
- adhere to the core definitions in docs/ontology.md and do not invent new domain entities
- validation expected before completion
- if blocked or invalid, use `fail` with explicit reason

## Skills Available

Custom Claude skills are in `.claude/skills/`:
- `claim-packet`
- `complete-packet`
- `wbs-status`
- `wbs-log`

These are wrappers around the governance CLI.

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
3. `claim <id> claude`
4. execute packet scope
5. run validation checks
6. `done <id> claude "evidence" --risk none`
7. report result

## Error Handling

- if claim fails due dependencies: run `status` or `ready`
- if completion fails: fix validation gaps and retry
- if blocked: mark packet `failed` with reason
- if session must transfer mid-packet: use `handover` then next session uses `resume`

See `docs/PLAYBOOK.md` and `docs/governance-workflow-codex.md` for recovery patterns.

## Governance Enforcement

This project uses Claude Code hooks (`.claude/hooks.json`) to enforce constitutional rules:

- **Protected files**: Direct edits to `wbs-state.json`, `wbs.json`, `constitution.md` are blocked
- **Governance code**: CLI and server code cannot be modified without review
- **Session start**: Governance status displayed automatically
- **Post-completion**: State validation runs after `done` commands

These hooks implement constitution.md Article IV (Protected Resources).

## MCP Server Integration

An MCP server (`.governance/mcp_server.py`) exposes governance operations as native tools:

| MCP Tool | Description |
|----------|-------------|
| `wbs_ready` | List claimable packets |
| `wbs_status` | Current state by status |
| `wbs_claim` | Claim a packet |
| `wbs_done` | Complete with evidence |
| `wbs_fail` | Mark failed with reason |
| `wbs_scope` | View packet requirements |
| `wbs_log` | Activity log |
| `wbs_progress` | Completion metrics |

To enable, add to your MCP configuration or use CLI commands directly.

## Plan Mode for Complex Packets

For packets requiring architectural decisions, use Claude Code's plan mode:

1. Review packet scope: `python3 .governance/wbs_cli.py scope <ID>`
2. Enter plan mode: "Let's plan the approach for packet X"
3. Explore codebase and draft implementation approach
4. Get human approval on plan
5. Claim packet and execute approved plan
6. Complete with evidence

See `docs/plan-mode-guide.md` for detailed workflow.

## Agent Teams (Opus 4.6)

This project supports Claude Code Agent Teams for parallel packet execution. Agent Teams are enabled in `.claude/settings.json`.

### Team Lead Role

As team lead, you:
- Coordinate packet assignment across teammates
- Monitor progress: `python3 .governance/wbs_cli.py status`
- Validate evidence quality before accepting completion
- Synthesize results across parallel work streams
- Use **delegate mode** (Shift+Tab) to focus on coordination

### Teammate Role

As a teammate, you:
- Claim your assigned packet: `python3 .governance/wbs_cli.py claim <ID> <your-name>`
- Execute within packet scope only
- Complete with evidence: `python3 .governance/wbs_cli.py done <ID> <your-name> "evidence" --risk none`
- Message lead when blocked or finished

### When to Use Agent Teams

| Use Teams | Use Single Agent |
|-----------|------------------|
| 2+ packets ready with no dependencies | Sequential packet dependencies |
| Different domains (frontend/backend/tests) | Same files need editing |
| Research/review parallelization | Simple, focused tasks |
| Cross-cutting concerns | Tight coordination required |

### Spinning Up a Team

```
Create an agent team for parallel packet execution:
- Teammate "docs": Claim UPG-001, execute docs work
- Teammate "code": Claim UPG-002, execute implementation
- Teammate "tests": Claim UPG-003, execute test coverage

Each teammate must claim their packet before work.
Require plan approval for complex packets.
```

See `.claude/skills/agent-teams/SKILL.md` for full documentation.

## Opus 4.6 Features

This project is configured for Claude Opus 4.6 with:

- **Adaptive thinking**: Claude decides when and how much to reason
- **Effort level**: Set to `high` by default (options: low, medium, high, max)
- **128K output tokens**: Longer responses for comprehensive evidence
- **Agent team hooks**: `TeammateIdle` and `TaskCompleted` enforce governance

### Thinking Effort by Packet Type

| Packet Type | Recommended Effort |
|-------------|-------------------|
| Simple docs/config | `low` |
| Standard implementation | `high` (default) |
| Complex architecture | `max` |
| Research/exploration | `high` with plan mode |
