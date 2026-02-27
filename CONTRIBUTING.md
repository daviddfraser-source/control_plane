# Contributing

## Prerequisites

- Python 3.8+
- Repository checked out at project root

## Local Development

```bash
python3 start.py --status
python3 .governance/wbs_cli.py validate
```

## Testing

Run the full suite:

```bash
python3 -m unittest discover -s tests -v
```

Quick smoke path:

```bash
./test.sh
```

## Code Style

- Python follows PEP 8 and should remain dependency-light.
- Keep governance behavior deterministic and file-backed unless a packet explicitly changes architecture.
- Prefer small, reviewable commits aligned to packet scope.

## Governance Expectations

- Use `.governance/wbs_cli.py` as the lifecycle source of truth.
- Keep packet notes updated with evidence paths.
- Do not mark a packet done without validation evidence (tests, lint, or command output reference).

## Pull Request Process

1. Link scope to packet(s) or WBS refs.
2. Describe behavior change and impacted files.
3. Include validation evidence (exact commands run).
4. Call out residual risks or known follow-up work.

## Review Criteria

PRs are evaluated on:
- correctness and regressions
- governance contract compatibility
- test and validation evidence quality
- clarity of operational impact

## Where To Start

Good first contributions:
- docs clarity fixes
- test gap closure
- actionable error-message improvements
- packet schema/example hygiene
