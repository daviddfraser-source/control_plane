# Control Plane Spec

## Product Scope

This repository implements a governance-first orchestration control plane with cryptographic state commitment for multi-agent packet workflows.

## Core System Boundary

Included:
- packet lifecycle governance engine
- CLI/API governance mutation surface
- deterministic commitment layer (DCL)
- verifiable lifecycle audit trail

Excluded:
- deterministic runtime sandbox for arbitrary side effects
- consensus/distributed fault-tolerant execution

## Integrity Model

1. Canonical serialization (`canonical_json_dumps`)
2. SHA-256 hashing for action/state/commit payloads
3. Hash-linked per-packet commit chain
4. HEAD pointer consistency checks
5. Runtime state binding check against latest committed `post_state_hash`
6. Startup integrity checks via `doctor` and API startup gate

## Commands

- `python3 .governance/wbs_cli.py doctor --fast`
- `python3 .governance/wbs_cli.py doctor --full`
- `python3 .governance/wbs_cli.py verify --all`
- `python3 .governance/wbs_cli.py history <packet_id>`
- `python3 .governance/wbs_cli.py export-proof <packet_id> --out <proof.zip>`

## Guarantees

- deterministic packet lifecycle state transition commitment
- tamper-evident governance history
- replay verification of committed transition chains

## Non-Guarantees

- deterministic LLM outputs
- deterministic third-party API responses
- deterministic execution equivalence of external side effects
