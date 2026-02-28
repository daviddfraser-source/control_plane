# Deterministic Commitment Layer (DCL) v1

## Scope

DCL provides deterministic state commitment for governance transitions. It does not provide deterministic LLM/runtime execution.

## Guarantees

- deterministic packet lifecycle state transition commitment
- canonical JSON serialization for all hashed payloads
- SHA-256 cryptographic commit hashes
- tamper-evident per-packet commit chaining
- replay verification of commit history

## Non-Guarantees

- deterministic model output generation
- deterministic external API behavior
- distributed consensus or byzantine fault tolerance
- full runtime side-effect replay equivalence

## Canonical Serialization Contract

- UTF-8 JSON
- sorted object keys
- compact separators `(',', ':')`
- no NaN/Infinity
- array order preserved
- datetime normalized to UTC ISO-8601 with `Z` suffix
- integer/float distinction preserved

Reference implementation: `src/governed_platform/governance/canonical_json.py`.

## Commit Object (Per Transition)

- `commit_id`
- `packet_id`
- `seq`
- `prev_commit_hash`
- `action_hash`
- `pre_state_hash`
- `post_state_hash`
- `constitution_hash`
- `diff` (mandatory structured diff)
- `created_at`
- `action_envelope`
- `commit_hash`

## File-Mode Storage Layout

```text
.governance/dcl/packets/<packet_id>/
  HEAD
  journal.json (ephemeral, during write)
  commits/000001.json
  commits/000002.json
  ...
```

## Verification Contract

Per packet verification enforces:

- `seq` continuity (`1..N`)
- duplicate sequence rejection
- `prev_commit_hash` linkage
- `pre_state_hash == previous post_state_hash`
- `commit_hash` recomputation consistency
- `HEAD.seq == last.seq`
- `HEAD.commit_hash == last.commit_hash`
- runtime-state binding check when packet runtime state is provided:
  - `sha256(canonical(runtime_packet_state)) == HEAD.post_state_hash`

## Startup/Doctor Integrity Contract

`doctor` and API startup integrity checks enforce:

- DCL config lock:
  - `mode = dcl`
  - `hash_algorithm = sha256`
  - `canonicalization_version = 1.0`
  - `dcl_version = 1.0`
  - `state_schema_version` aligned to runtime state
- journal recovery scan
- DCL verification (fast or full mode)
- machine-readable integrity report

## Atomic Write Protocol (File Mode)

- acquire packet-level file lock
- write journal intent (`prepare`)
- write commit file
- update `HEAD`
- mark journal `done`, then remove journal file

Journal recovery is attempted before verification/startup checks.

## Heartbeat Commit Policy

- default: `transition_only`
- non-transition heartbeat updates do not produce DCL commits
- heartbeat transitions (`stalled <-> in_progress`) produce DCL commits
