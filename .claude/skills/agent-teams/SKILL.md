---
name: agent-teams
description: Spin up governed agent teams for parallel packet execution
allowed_tools:
  - Bash
  - Read
  - Task
  - TaskCreate
  - TaskUpdate
---

# Governed Agent Teams

Coordinate multiple Claude Code instances to execute WBS packets in parallel with constitutional governance.

## Overview

This skill leverages Claude Code's Agent Teams feature (Opus 4.6) to parallelize packet execution while maintaining governance invariants:

- **Team lead**: Coordinates work, assigns packets, synthesizes results
- **Teammates**: Execute individual packets independently
- **Shared governance**: All agents use the same WBS CLI and state

## When to Use Agent Teams

Use agent teams when:
- Multiple packets are ready with no dependencies between them
- Packets involve different domains (frontend, backend, tests)
- Research/review tasks benefit from parallel exploration
- Cross-cutting concerns need simultaneous attention

Do NOT use agent teams when:
- Packets have sequential dependencies
- Same files need to be edited by multiple packets
- Work is simple enough for a single agent

## Pre-Flight Checks

Before spinning up a team, verify:

```bash
# Check ready packets (must have 2+ for parallel work)
python3 .governance/wbs_cli.py ready

# Verify no blocking dependencies between target packets
python3 .governance/wbs_cli.py status
```

## Team Formation

### Option 1: Natural Language (Recommended)

Tell Claude to create a governed team:

```
Create an agent team to execute these packets in parallel:
- UPG-001: Lead kickoff prompt (teammate: docs-writer)
- UPG-002: Teammate kickoff prompt (teammate: docs-writer-2)
- UPG-004: WBS template (teammate: template-dev)

Each teammate should:
1. Claim their packet using: python3 .governance/wbs_cli.py claim <PACKET_ID> <teammate-name>
2. Execute within packet scope only
3. Mark done with evidence: python3 .governance/wbs_cli.py done <PACKET_ID> <teammate-name> "evidence"

Require plan approval before implementation.
```

### Option 2: Structured Assignment

```
Spawn an agent team with these roles:

Team Lead: Coordinate packet execution, validate evidence, synthesize deliverables
- Monitor: python3 .governance/wbs_cli.py status
- Validate: python3 .governance/wbs_cli.py validate

Teammate "frontend": Execute UPG-005
- Scope: src/components/, src/styles/
- Claim: python3 .governance/wbs_cli.py claim UPG-005 frontend

Teammate "backend": Execute UPG-006
- Scope: src/api/, src/services/
- Claim: python3 .governance/wbs_cli.py claim UPG-006 backend

Teammate "tests": Execute UPG-007
- Scope: tests/
- Claim: python3 .governance/wbs_cli.py claim UPG-007 tests
```

## Governance Rules for Teammates

All teammates must follow constitution.md. Key rules:

1. **Claim before work**: `python3 .governance/wbs_cli.py claim <ID> <agent-name>`
2. **Scope adherence**: Execute only packet's `required_actions`
3. **Evidence required**: Specific artifacts, not vague completion claims
4. **No cross-packet edits**: Each teammate owns their packet's files
5. **Fail explicitly**: `python3 .governance/wbs_cli.py fail <ID> <agent-name> "reason"`

## Team Lead Responsibilities

The team lead should:

1. **Check readiness** before spawning teammates:
   ```bash
   python3 .governance/wbs_cli.py ready
   ```

2. **Monitor progress** during execution:
   ```bash
   python3 .governance/wbs_cli.py status
   python3 .governance/wbs_cli.py log 10
   ```

3. **Validate evidence** when teammates complete:
   - Check evidence references specific artifacts
   - Verify validation checks were run
   - Confirm exit criteria satisfied

4. **Synthesize results** after all packets complete:
   ```bash
   python3 .governance/wbs_cli.py progress
   ```

## Teammate Workflow

Each teammate executes this workflow:

```bash
# 1. Claim the packet
python3 .governance/wbs_cli.py claim <PACKET_ID> <my-name>

# 2. Read scope
python3 .governance/wbs_cli.py scope <PACKET_ID>

# 3. Execute required_actions (implementation work)

# 4. Run validation_checks

# 5. Complete with evidence
python3 .governance/wbs_cli.py done <PACKET_ID> <my-name> "Created X, validated Y, tests pass"
```

## File Conflict Prevention

To avoid teammates editing the same files:

1. **Assign by domain**: frontend/, backend/, tests/
2. **Check packet scope**: Packets should define non-overlapping file sets
3. **Use delegate mode**: Lead coordinates, doesn't implement

If conflicts occur:
- Lead arbitrates which teammate owns the file
- Other teammate waits or works on different scope

## Hooks for Quality Gates

The following hooks enforce governance during team execution:

- **TeammateIdle**: Validates governance state when a teammate goes idle
- **TaskCompleted**: Checks for in_progress packets before marking complete

These hooks use exit code 2 to send feedback and keep teammates working if governance checks fail.

## Example: Parallel Documentation Sprint

```
Create an agent team for documentation packets:

Lead: Coordinate the sprint, review all deliverables
- Run: python3 .governance/wbs_cli.py ready (filter docs packets)

Teammates (spawn 3):
1. "api-docs": Claim UPG-010, write API documentation
2. "user-guide": Claim UPG-011, write user guide
3. "arch-docs": Claim UPG-012, write architecture docs

All teammates must:
- Claim packet before starting
- Include file paths in evidence
- Run markdown lint validation
- Notify lead when done

Wait for all teammates before synthesizing.
```

## Troubleshooting

### Teammate claims wrong packet
```bash
python3 .governance/wbs_cli.py reset <PACKET_ID>  # Lead only
```

### Evidence quality too low
Lead sends feedback via teammate messaging, teammate adds notes:
```bash
python3 .governance/wbs_cli.py note <PACKET_ID> <agent> "Additional evidence: ..."
```

### Dependency not met
Teammate cannot claim packet with unmet dependencies. Check:
```bash
python3 .governance/wbs_cli.py ready
```

## See Also

- `constitution.md` - Governance invariants
- `AGENTS.md` - Agent operating contract
- `docs/plan-mode-guide.md` - Plan mode integration
- [Claude Code Agent Teams](https://code.claude.com/docs/en/agent-teams) - Official documentation
