# Infrastructure Domain Ontology Template (Reference)

This is a domain ontology starter for regulated infrastructure delivery projects.
Use it as a project-local template and adapt identifiers/rules through governed ontology proposals.

## Canonical Entities

### program
Collection of related projects managed under shared outcomes and governance.
Required attributes: program_id, sponsor, portfolio, status.

### infrastructure_project
Discrete funded project delivering a physical asset or infrastructure capability.
Required attributes: project_id, sponsor, delivery_phase, approval_status.

### work_package
Scoped execution package inside a project.
Required attributes: work_package_id, project_id, owner, status.

### deliverable
Tangible output produced by a work package.
Required attributes: deliverable_id, work_package_id, acceptance_status.

### milestone
Point-in-time governance checkpoint.
Required attributes: milestone_id, project_id, gate_type, gate_date.

### risk
Potential event with impact on delivery/compliance.
Required attributes: risk_id, owner, likelihood, impact, treatment_status.

### approval
Formal decision record for funding/scope/phase transition.
Required attributes: approval_id, approver, decision, decision_date.

## Controlled Vocabulary

- `milestone` aliases: `gate`, `checkpoint`; anti-alias: `deliverable`
- `deliverable` aliases: `output`; anti-alias: `milestone`

## Relationship Constraints

- Program CONTAINS [1..*] Infrastructure_Project
- Infrastructure_Project CONTAINS [1..*] Work_Package
- Work_Package PRODUCES [1..*] Deliverable
- Infrastructure_Project HAS [1..*] Milestone
- Infrastructure_Project HAS [0..*] Risk
- Infrastructure_Project REQUIRES [1..*] Approval

## Invariant Assertions

- Every Deliverable traces to exactly one Work_Package.
- Every Risk has exactly one Risk Owner.
- A project cannot be both Active and Closed.
- A Milestone is not a Deliverable.
