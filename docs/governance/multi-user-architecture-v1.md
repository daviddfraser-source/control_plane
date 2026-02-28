# Multi-User Architecture v1 Foundation

## Layers

1. API boundary (`src/governed_platform/api/server.py`)
2. Engine policy layer (unchanged GovernanceEngine)
3. Pluggable state manager (file + database)
4. Git audit service for governance events
5. Role model (`operator`, `reviewer`, `supervisor`, `admin`)

## Transport

- CLI local mode (default): direct engine/file mode
- CLI API mode: `WBS_API_URL` enabled for mutation calls

## Data Stores

- file mode: `.governance/wbs-state.json`
- db mode foundation: sqlite-backed `DatabaseStateManager`
- postgres compatibility remains staged follow-on

## Security and Role Boundaries

- role-action map in `rbac.py`
- two-person integrity remains engine-enforced
- supervisor/admin gates are additive constraints in API mode
