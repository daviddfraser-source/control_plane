---
name: reset-packet
description: Return a stuck packet to pending status
disable-model-invocation: true
allowed-tools: Bash(python3 .governance/wbs_cli.py *)
argument-hint: "[packet-id]"
---

# Reset a WBS Packet

Return an in-progress packet to pending.

```bash
python3 .governance/wbs_cli.py reset EXE-001
```

## When to Use

- Agent stuck or abandoned work
- Need to reassign to different agent
- Claim made in error

## Finding Stale Packets

```bash
python3 .governance/wbs_cli.py stale 30   # In-progress >30 min
```
