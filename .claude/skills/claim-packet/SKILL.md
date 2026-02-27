---
name: claim-packet
description: Claim a packet after checking ready scope and confirming with user
disable-model-invocation: true
allowed-tools: Bash(python3 .governance/wbs_cli.py *)
argument-hint: "[packet-id]"
---

# Claim Packet Skill

Use this skill when the user asks to start packet work.

## Workflow

1. Check available packets:
```bash
python3 .governance/wbs_cli.py ready
```

2. Confirm packet id with user (do not auto-claim multiple packets).

3. Claim packet:
```bash
python3 .governance/wbs_cli.py claim <PACKET_ID> claude
```

4. Inspect scope/details:
```bash
python3 .governance/wbs_cli.py scope <PACKET_ID>
```

## Evidence Tracking

Track during execution:
- files created/modified
- validation commands run
- command outputs relevant to completion

## Halt Path

If blocked or unable to deliver within scope:
```bash
python3 .governance/wbs_cli.py fail <PACKET_ID> claude "reason"
```
