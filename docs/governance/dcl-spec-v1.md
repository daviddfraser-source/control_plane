# Deterministic Commitment Layer (DCL) v1

## Canonical Serialization

- UTF-8 JSON
- sorted keys
- separators: `(',', ':')`
- no NaN/Infinity
- array order preserved
- datetime normalized to UTC ISO-8601 Z

## Commit Object

- `commit_id`
- `packet_id`
- `seq`
- `prev_commit_hash`
- `action_hash`
- `pre_state_hash`
- `post_state_hash`
- `constitution_hash`
- `diff` (mandatory)
- `created_at`
- `commit_hash`

## Verification

- genesis commit uses `prev_commit_hash = GENESIS`
- each commit hash recomputed from canonical payload
- each commit links to previous commit hash
- current pre-state hash must equal previous post-state hash

## Atomic File-Mode Write Protocol

- write journal intent
- write commit file
- update HEAD pointer
- clear journal
- recover from journal on startup/verification

## Heartbeat Commit Policy

- default: `transition_only`
- no commit for non-transition heartbeat updates
- transition heartbeat events (stalled/in_progress) commit
