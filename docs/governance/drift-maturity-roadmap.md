# Drift Detection Maturity Roadmap

## Modes

- `coverage_only`
  - Checks only whether active packets have notes available for drift review.
- `token_heuristic`
  - Includes coverage checks + shared-token consistency heuristics across active packets.
- `semantic_future`
  - Emits roadmap marker for contradiction-inference mode (not yet implemented).

## CLI

- `python3 .governance/wbs_cli.py ontology check-drift`
- `python3 .governance/wbs_cli.py ontology check-drift --mode coverage_only`
- `python3 .governance/wbs_cli.py ontology check-drift --mode token_heuristic`
- `python3 .governance/wbs_cli.py ontology check-drift --mode semantic_future`

## Claim Boundaries

Current runtime does not claim NLP semantic contradiction inference.
Current runtime claims deterministic heuristic consistency checks only.
