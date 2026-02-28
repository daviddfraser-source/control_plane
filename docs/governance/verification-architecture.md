# Verification Architecture

## Runtime Architecture

```mermaid
flowchart LR
  CLI[CLI] --> ENG[Governance Engine]
  API[API Server] --> ENG
  ENG --> ST[State Store]
  ENG --> DCL[DCL Commit Store]
  ENG --> LOG[Activity Log]
  DCL --> VRFY[verify/doctor]
  ST --> VRFY
```

## Packet Transition + Commit Flow

```mermaid
sequenceDiagram
  participant A as Actor (CLI/API)
  participant E as Engine
  participant S as Runtime State
  participant C as DCL

  A->>E: transition request
  E->>S: read pre-state
  E->>E: validate transition rules
  E->>S: write post-state
  E->>C: write DCL commit (locked, journaled)
  E-->>A: success + transition result
```

## Startup Verification Flow

```mermaid
flowchart TD
  START[process start] --> CFG[load dcl-config]
  CFG --> LOCK[validate config lock]
  LOCK --> RECOVER[recover journals]
  RECOVER --> VERIFY[verify DCL chains]
  VERIFY --> BIND[bind runtime state to HEAD post_state_hash]
  BIND --> REPORT[integrity report]
  REPORT --> DECIDE{strict mode?}
  DECIDE -- yes + failed --> EXIT[abort startup]
  DECIDE -- no --> SERVE[start service]
```

## Data Model Summary

- Runtime state: `.governance/wbs-state.json`
- WBS definition: `.governance/wbs.json`
- DCL config lock: `.governance/dcl-config.json`
- DCL commits: `.governance/dcl/packets/<packet_id>/commits/*.json`
- DCL head pointer: `.governance/dcl/packets/<packet_id>/HEAD`
