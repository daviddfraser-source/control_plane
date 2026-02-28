# Packet Standard

Canonical schema source: `.governance/packet-schema.json`

## Baseline Fields

- `id`, `wbs_ref`, `area_id`, `title`, `scope`

## Enhancement Fields (Optional)

- `preflight_required`: bool
- `review_required`: bool
- `heartbeat_required`: bool
- `heartbeat_interval_seconds`: int
- `context_manifest`: array of `{file, priority, required}`
- `template_ref`: string
- `ontology_required`: bool

## Runtime Evidence Fields

Persisted in `.governance/wbs-state.json` packet state:

- `context_attestation`
- `preflight`
- `last_heartbeat_at`, `last_heartbeat`
- `review`
