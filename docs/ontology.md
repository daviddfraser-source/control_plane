# Ontology

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
