---
name: wbs-status
description: Inspect readiness, status, and progress for governed execution
allowed-tools: Bash(python3 .governance/wbs_cli.py *)
---

# WBS Status Skill

## Commands

```bash
python3 .governance/wbs_cli.py status
python3 .governance/wbs_cli.py ready
python3 .governance/wbs_cli.py progress
python3 .governance/wbs_cli.py log 20
python3 .governance/wbs_cli.py --json status
```

## Use Cases

- find next claimable packet
- inspect in-progress ownership
- review completion progress
- collect structured state for automation (`--json`)
