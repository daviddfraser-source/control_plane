---
name: wbs-report
description: Generate a markdown summary report of WBS status
allowed-tools: Bash(python3 .governance/wbs_cli.py *)
---

# WBS Report

Generate project status report by running these commands and formatting output:

```bash
python3 .governance/wbs_cli.py progress   # Counts
python3 .governance/wbs_cli.py status     # Full state
python3 .governance/wbs_cli.py log 10     # Recent activity
python3 .governance/wbs_cli.py ready      # Available work
```

## Required Sections

Always include:

1. Progress stats (`done/in_progress/pending/failed/blocked`)
2. Completed work summary (packet IDs + short note)
3. Current blockers/risks
4. Immediate next steps (from ready queue)

## Output Template

```markdown
## WBS Progress
- done: X
- in_progress: X
- pending: X
- failed: X
- blocked: X

## Completed Work
- PACKET-ID — title — completion note

## Blockers / Risks
- [if none, state: None currently detected]

## Next Steps
- Ready: PACKET-ID — title
```

## Status Icons (Optional)

| Status | Icon |
|--------|------|
| Done | ✅ |
| In Progress | 🔄 |
| Pending | ⏳ |
| Failed | ❌ |
| Blocked | 🚫 |
