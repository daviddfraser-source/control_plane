# Ontology

This file defines the core governance ontology for Substrate itself.
For domain-specific projects, start from `docs/ontology-infrastructure-template.md` and `docs/ontology-templates/infrastructure_delivery_ontology.json`.

## Canonical Entities

### packet
A governed work unit in the WBS lifecycle.
Required attributes: packet_id, title, scope, status.

### review_assessment
Independent validation artifact tied to a packet in review state.
Required attributes: verdict, findings, risk_flags.

## Controlled Vocabulary

### milestone
Approved aliases: gate, checkpoint
Anti-aliases: deliverable

### deliverable
Approved aliases: output
Anti-aliases: milestone

## Relationship Constraints

- Work_Area CONTAINS [1..*] Packet
- Packet MAY_REQUIRE [0..1] Preflight_Assessment
- Packet MAY_REQUIRE [0..1] Review_Assessment
- Packet PRODUCES [0..*] Template

## Common Conflation Warnings

- Milestone is not Deliverable because milestone is temporal and deliverable is an artifact.
- Reviewer is not Executor because two-person integrity requires identity separation.

## Invariant Assertions

- Every DONE packet has exactly one execution owner.
- A packet cannot be in both DONE and FAILED status.
- A review-required packet cannot transition directly from IN_PROGRESS to DONE.

## Validation Profile (Current Runtime)

- Deterministic checks only (no NLP semantic inference).
- Entity checks: token-boundary presence (not raw substring match).
- Vocabulary checks: anti-alias usage detection.
- Anti-conflation checks: canonical + prohibited pair co-occurrence warnings.
- Relationship checks: direction/inversion phrase checks from ontology schema.
- Invariants: evaluated via optional `ontology_assertions` hooks in packet runtime state.

## Drift Check Profile (Current Runtime)

- `ontology check-drift` currently runs heuristic checks:
  - notes coverage for active packets
  - shared-token consistency heuristics across active packets
- This is advisory telemetry, not full semantic contradiction inference.
- Configurable modes:
  - `coverage_only`
  - `token_heuristic` (default)
  - `semantic_future` (roadmap marker)
