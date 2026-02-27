---
name: init-wbs
description: Initialize WBS database from JSON definition
disable-model-invocation: true
allowed-tools: Bash(python3 .governance/wbs_cli.py *)
argument-hint: "[path-to-wbs.json]"
---

# Initialize WBS Database

```bash
python3 .governance/wbs_cli.py init .governance/wbs.json
python3 .governance/wbs_cli.py init --wizard   # Interactive setup
```

Creates SQLite database, loads work areas/packets, sets up dependencies.

Re-initialization is safe — preserves execution state, updates definitions.
