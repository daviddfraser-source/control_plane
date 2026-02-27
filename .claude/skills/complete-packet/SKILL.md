---
name: complete-packet
description: Complete a claimed packet with explicit evidence
disable-model-invocation: true
allowed-tools: Bash(python3 .governance/wbs_cli.py *)
argument-hint: "[packet-id] [evidence]"
---

# Complete Packet Skill

Use when work is complete and validated.

## Completion Checklist

- required actions executed
- required outputs produced
- relevant validation checks run
- exit criteria satisfied
- no unresolved halt conditions

## Evidence Standard

Evidence should include:
- concrete file paths
- validation command/results
- artifact location(s)

Good:
```text
Updated src/api/auth.py and tests/test_auth.py. Ran python3 -m unittest tests.test_auth -v (12 tests, all passed). Docs: docs/auth.md.
```

Bad:
```text
Done
```

## Completion Command

```bash
python3 .governance/wbs_cli.py done <PACKET_ID> claude "Evidence string"
```

## Add Supplemental Evidence

```bash
python3 .governance/wbs_cli.py note <PACKET_ID> claude "Additional evidence"
```
