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

## Status Icons

| Status | Icon |
|--------|------|
| Done | ✅ |
| In Progress | 🔄 |
| Pending | ⏳ |
| Failed | ❌ |
| Blocked | 🚫 |
