---
name: wbs-log
description: Review activity log for audit and unblock analysis
allowed-tools: Bash(python3 .governance/wbs_cli.py *)
argument-hint: "[count]"
---

# WBS Log Skill

## Commands

```bash
python3 .governance/wbs_cli.py log 20
python3 .governance/wbs_cli.py log 50
python3 .governance/wbs_cli.py --json log 30
```

## Use Cases

- identify blocking event chains
- confirm upstream completion timestamps
- gather evidence for delivery reporting
