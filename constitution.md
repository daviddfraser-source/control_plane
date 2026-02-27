# Substrate Constitution

**Version:** 1.0  
**Repository:** https://github.com/daviddfraser-source/Substrate  
**Authority:** Project governance framework  
**Enforcement:** Automated via `.governance/wbs_cli.py`  
**License:** MIT

## Preamble

This constitution establishes the invariant rules governing agent execution within Substrate projects. All agents—human, LLM-based, or automated—operate under these constraints. Violations are rejected by the enforcement mechanism.

Substrate provides constitutional governance for multi-agent coordination through packet-based execution contracts, formal state machines, and immutable audit trails. This constitution defines the rules that make governance **constitutional** rather than merely procedural.

---

## Article I: Scope Boundaries

### Section 1: Packet Authority
No agent shall execute work outside the scope defined in a claimed packet's `required_actions`.

**Rationale:** Prevents scope creep, ensures work maps to plan.

**Enforcement:** Completion evidence must map to required actions. Evidence review rejects out-of-scope work.

### Section 2: Scope Expansion Prohibition
Agents cannot modify packet definitions to expand scope during execution.

**Rationale:** Prevents agents from redefining their own objectives mid-execution.

**Enforcement:** `.governance/wbs.json` is read-only to agents. Changes require human approval via version control.

### Section 3: Scope Clarification Protocol
If packet scope is ambiguous or incomplete, agent must request human clarification before proceeding with work.

**Rationale:** Ambiguity creates drift. Clarification prevents misaligned execution.

**Enforcement:** Evidence must document clarification request if scope was unclear. No silent assumption-based execution.

### Section 4: Halt Condition Compliance
If any packet `halt_conditions` evaluate to true during execution, agent must immediately mark packet FAILED.

**Rationale:** Prevents wasted effort on doomed work. Makes failure explicit.

**Enforcement:** `wbs_cli.py fail` command requires failure reason. Evidence review verifies halt condition evaluation.

---

## Article II: State Transitions

### Section 1: Atomic Transitions
All state changes must be atomic and logged. No silent state modification.

**Rationale:** Ensures state consistency, enables audit, prevents race conditions.

**Enforcement:** All state changes via CLI with file locking. Direct state file modification is prohibited and detected.

### Section 2: Valid Transition Path
State transitions must follow the formal state machine:
- PENDING → IN_PROGRESS (via `claim`)
- IN_PROGRESS → DONE (via `done`)
- IN_PROGRESS → FAILED (via `fail`)
- IN_PROGRESS → PENDING (via `reset`, human only)
- PENDING → BLOCKED (automatic when dependency fails)

**Rationale:** Enforces workflow integrity, prevents invalid state combinations.

**Enforcement:** CLI rejects invalid transitions with error messages indicating valid next states.

### Section 3: Required Evidence
No packet may transition to DONE without evidence string linking to deliverables and validation results.

**Rationale:** Prevents completion without proof. Makes audit trails concrete.

**Enforcement:** CLI rejects `done` commands with empty or missing evidence parameter.

### Section 4: Dependency Ordering
No packet may be claimed if its dependencies are not in DONE state.

**Rationale:** Enforces execution order, prevents building on incomplete foundations.

**Enforcement:** CLI checks dependency status before allowing `claim`. Returns error listing unmet dependencies.

### Section 5: Immutable Completion
Packets in DONE state cannot transition back to IN_PROGRESS or PENDING.

**Rationale:** Completion is final. Rework requires new packet. Prevents state thrashing.

**Enforcement:** CLI rejects any transition from DONE to non-terminal state. Human reset is logged as governance action.

### Section 6: Transition Logging
Every state transition must be logged with timestamp, agent identifier, and transition reason.

**Rationale:** Creates immutable audit trail for all governance actions.

**Enforcement:** Automatic logging in `.governance/wbs-state.json` log array. Append-only structure.

---

## Article III: Evidence Requirements

### Section 1: Artifact Linkage
Evidence must reference specific artifacts using file paths, test result outputs, or validation command outputs.

**Good evidence examples:**
- `"Created api/auth.py (234 lines), tests/test_auth.py (15 tests passing)"`
- `"Modified config.json, validated with scripts/validate-config.sh (exit 0)"`
- `"Documentation in docs/auth.md, reviewed by lead, approved in PR #42"`

**Bad evidence examples:**
- `"Done"`
- `"Completed the work"`
- `"Everything looks good"`

**Rationale:** Vague evidence enables fabrication. Specific evidence creates accountability.

**Enforcement:** Evidence review during closeout. Automated validation where possible.

### Section 2: Validation Proof
Packets with non-empty `validation_checks` must provide proof that checks were executed and passed.

**Rationale:** Prevents claiming completion without quality verification.

**Enforcement:** Evidence must include validation results. Test failures require `fail` instead of `done`.

### Section 3: Exit Criteria Satisfaction
All items in packet `exit_criteria` must be satisfied before marking DONE.

**Rationale:** Exit criteria define "done." Cannot be done without meeting definition.

**Enforcement:** Human lead verification during evidence review. Automated checks where criteria are machine-testable.

### Section 4: Evidence Chain Integrity
All deliverables must trace back to a packet via evidence string or completion notes.

**Rationale:** Enables audit: "Why does this file exist?" → "Packet X created it, here's evidence."

**Enforcement:** Periodic evidence chain audits, drift assessments at closeout.

### Section 5: Supplementary Notes
Additional evidence may be added after completion via `note` command without changing packet status.

**Rationale:** Allows evidence clarification without reopening completed work.

**Enforcement:** `wbs_cli.py note` appends to packet evidence log with timestamp.

---

## Article IV: Protected Resources

### Section 1: State File Integrity
Agents cannot directly modify `.governance/wbs-state.json`.

**Rationale:** State must only change through governed CLI operations to ensure consistency and logging.

**Enforcement:** 
- File permissions (read-only for agents where possible)
- File locking during CLI operations
- State/schema validation on load

### Section 2: Definition Immutability
Agents cannot modify packet definitions in `.governance/wbs.json` during execution.

**Rationale:** Prevents agents from redefining objectives to make work "easier" or claiming broader completion.

**Enforcement:**
- Read-only file access for agents
- Changes require human commit to version control
- Schema validation on load

### Section 3: Governance Code Protection
Agents cannot modify files in `.governance/` directory.

**Rationale:** Prevents agents from weakening governance enforcement to bypass rules.

**Enforcement:**
- File permissions
- Code review for any `.governance/` changes
- Protected paths documented in agent instructions

### Section 4: Template Integrity
WBS templates in `templates/` are reference implementations and should not be modified during project execution.

**Rationale:** Templates provide known-good patterns. Project-specific changes go in `.governance/wbs.json`.

**Enforcement:** Templates are read-only during execution. Modifications require new template in version control.

---

## Article V: Multi-Agent Coordination

### Section 1: Claim Exclusivity
Only one agent may hold a claim on a packet at any time.

**Rationale:** Prevents duplicate work, race conditions, and ownership confusion.

**Enforcement:** 
- CLI checks current owner before allowing `claim`
- File locking prevents concurrent state modification
- `status` command shows current owners

### Section 2: Stale Work Detection
Packets in IN_PROGRESS state beyond reasonable time bounds may be flagged as stale.

**Rationale:** Prevents work from hanging indefinitely if agent disconnects or stalls.

**Enforcement:** `wbs_cli.py stale <minutes>` command identifies long-running packets. Human lead decides reset action.

### Section 3: No Hidden Work
All agent work must be tracked via claimed packets. No off-the-books execution.

**Rationale:** Untracked work cannot be audited, validated, or coordinated with other agents.

**Enforcement:** Evidence review, deliverables must trace to packets, periodic repository audits.

### Section 4: Agent Identification
All CLI operations must include agent identifier for logging and coordination.

**Rationale:** Enables "who did what" audit trail. Required for multi-agent projects.

**Enforcement:** CLI commands require explicit agent parameter. Agent identity is logged on each transition.

### Section 5: Concurrent Work Isolation
Agents working on independent packets must not create conflicting file modifications.

**Rationale:** Prevents merge conflicts, reduces rework.

**Enforcement:** 
- Packet design should minimize file overlap
- Git-based conflict detection
- Human lead coordinates high-contention areas

---

## Article VI: Human Authority

### Section 1: Ultimate Governance Authority
Human project leads have final authority over packet status, priority, assignment, and governance rule interpretation.

**Rationale:** AI agents are execution resources, not decision-makers. Humans remain accountable.

**Enforcement:** 
- Policy designates lead-only governance actions (reset, emergency override)
- All governance decisions logged with human identifier
- Agents must defer ambiguous cases to human judgment

### Section 2: Constitution Amendment
This constitution may only be amended through human decision and committed change to this file.

**Rationale:** Governance rules must not be self-modifying. Stability requires human deliberation.

**Enforcement:**
- Version control shows amendment history
- Signed commits for constitution changes
- Amendment log at end of this document

### Section 3: Emergency Override
Human leads may reset state, override rules, or intervene in execution in emergency situations.

**Rationale:** Rigid rules must not prevent recovery from edge cases or critical issues.

**Enforcement:**
- `wbs_cli.py reset` command used under lead authority policy
- Emergency overrides logged with justification
- Post-incident review required

### Section 4: Drift Assessment Requirement
Completed work areas (Level-2 WBS sections) require human-led drift assessment comparing expected vs delivered scope.

**Rationale:** Validates that execution matched intent. Identifies systematic drift patterns.

**Enforcement:**
- `wbs_cli.py closeout-l2` command requires drift assessment file
- Assessment must include required sections (see `docs/drift-assessment-template.md`)
- Closeout cannot proceed until assessment complete

---

## Article VII: Audit and Transparency

### Section 1: Immutable Event Log
All state transitions, claims, completions, and governance actions are logged with timestamp, agent, and evidence.

**Rationale:** Creates tamper-evident audit trail for compliance and dispute resolution.

**Enforcement:**
- Append-only log array in `.governance/wbs-state.json`
- No CLI command to delete or modify log entries
- Log integrity checked on load

### Section 2: Evidence Chain Traceability
Every deliverable in the repository must trace back to a packet via evidence string or completion notes.

**Rationale:** Answers "why does this exist?" and "who authorized this?" for every artifact.

**Enforcement:**
- Drift assessments verify evidence chains
- Periodic repository audits
- Orphaned artifacts flagged for review

### Section 3: State Transparency
Current system state (packet status, ownership, progress) must be queryable at any time.

**Rationale:** Enables coordination, prevents duplicate work, supports planning.

**Enforcement:**
- `status` command provides real-time state view
- `log` command provides historical view
- Dashboard provides visual state representation

### Section 4: Progress Visibility
Project progress metrics (completion percentage, packets by state, timeline) must be available to all stakeholders.

**Rationale:** Transparency enables informed decision-making and expectation management.

**Enforcement:**
- `progress` command calculates completion metrics
- Dashboard displays progress visualization
- Reports generated for closeout and reviews

---

## Article VIII: Validation and Quality

### Section 1: Mandatory Validation Execution
If packet defines `validation_checks`, they must be executed before marking DONE.

**Rationale:** Quality gates prevent downstream issues. Skipped validation creates technical debt.

**Enforcement:**
- Evidence must include validation results
- Failed validation requires `fail` instead of `done`
- Evidence review verifies validation occurred

### Section 2: Exit Criteria Verification
All `exit_criteria` in packet definition must be satisfied before completion.

**Rationale:** Exit criteria define completion. Partial completion is not completion.

**Enforcement:**
- Human lead verification during evidence review
- Automated verification where criteria are machine-testable
- Incomplete exit criteria blocks closeout

### Section 3: Precondition Validation
Packet `preconditions` must be true before claiming packet for execution.

**Rationale:** Prevents starting work without necessary prerequisites.

**Enforcement:**
- CLI checks dependencies (a form of precondition)
- Agent responsible for verifying other preconditions
- Evidence should note precondition satisfaction

### Section 4: Quality Standards Inheritance
Packets inherit quality standards from project governance policy unless explicitly overridden.

**Rationale:** Ensures consistent quality baseline across all work.

**Enforcement:**
- Project policy documented in `AGENTS.md` or equivalent
- Packet-specific overrides must be explicit in packet definition
- Evidence must demonstrate standard compliance

---

## Article IX: Failure and Recovery

### Section 1: Explicit Failure Declaration
When work cannot be completed, packet must be marked FAILED with clear reason.

**Rationale:** Prevents false completion claims. Makes blockers visible.

**Enforcement:**
- `wbs_cli.py fail` command requires failure reason
- Failed packets block dependents automatically
- Failure triggers lead notification

### Section 2: Failure Impact Documentation
Failed packets must document impact on dependent packets and project timeline.

**Rationale:** Enables replanning, prioritization, risk mitigation.

**Enforcement:**
- Failure evidence should list affected downstream packets
- Lead reviews failure impact during status meetings
- Recovery plan documented in notes

### Section 3: Recovery Procedures
Failed packets may be reset to PENDING by human lead after addressing failure cause.

**Rationale:** Enables retry without creating duplicate packets.

**Enforcement:**
- `reset` command (lead-only)
- Reset must include justification in log
- Original failure evidence preserved

### Section 4: Lessons Learned
Significant failures should be documented in project knowledge base for future reference.

**Rationale:** Organizational learning, pattern detection, process improvement.

**Enforcement:**
- Closeout reviews include failure retrospectives
- Lessons documented in `docs/lessons-learned.md`
- Process improvements reflected in constitution amendments or templates

---

## Enforcement Mechanisms

This constitution is enforced through multiple layers:

### Layer 1: Code Enforcement
`.governance/wbs_cli.py` implements constitutional rules as hard constraints:
- Invalid state transitions are rejected
- Missing evidence blocks completion
- Dependencies enforce execution order
- File locking prevents race conditions

### Layer 2: File System
Operating system capabilities enforce access control:
- Read-only permissions on governance files
- File locking during concurrent access
- Git protects against unauthorized changes

### Layer 3: Process
Human oversight enforces rules requiring judgment:
- Evidence review for quality and completeness
- Drift assessment comparing expected vs actual
- Closeout verification of exit criteria
- Emergency override authority

### Layer 4: Culture
Agent training and documentation establish expectations:
- `AGENTS.md` defines operating procedures
- `CLAUDE.md` provides agent-specific guidance
- Skills in `.claude/skills/` encode best practices
- This constitution sets the standard

### Violation Handling

**Automated violations** (e.g., invalid state transition):
- CLI rejects operation with error message
- No state change occurs
- Violation logged for review

**Detected violations** (e.g., missing evidence):
- Flagged during evidence review
- Lead investigates and corrects
- Pattern violations trigger process improvement

**Systemic violations** (e.g., consistent drift):
- Identified in closeout assessments
- Root cause analysis performed
- Constitution or process updated if needed

---

## Rationale: Why Constitutional Governance?

This constitution exists because conventional governance approaches fail for AI agents:

### Problem 1: Prompt-Based Governance is Bypassable
**Failure mode:** LLMs can ignore instructions via jailbreaking, context manipulation, or "helpful" scope expansion.

**Constitutional solution:** Rules enforced by code, not prompts. Agents cannot bypass file permissions or state machine validation.

### Problem 2: Shared Context Creates Race Conditions
**Failure mode:** Multiple agents sharing memory or state create consistency issues, duplicate work, and data corruption.

**Constitutional solution:** File locking, atomic state transitions, explicit claim ownership prevent concurrent modification.

### Problem 3: No Accountability Without Evidence
**Failure mode:** Agents claim "I did the work" without proof. Auditors cannot verify what actually happened.

**Constitutional solution:** Evidence requirements with artifact linkage create tamper-evident audit trail.

### Problem 4: Emergent Governance is Fragile
**Failure mode:** Ad-hoc rules emerge through practice but aren't documented or enforced consistently.

**Constitutional solution:** Explicit, versioned, enforced rules create stability and predictability.

### Why "Constitutional" Specifically?
A constitution is a set of **invariant rules that govern governance itself**. 

Not just "how to do work" (that's process), but "what rules can never be violated" (that's constitutional).

Substrate provides the computational substrate on which governed work executes. This constitution defines the rules of that substrate.

---

## Article X: Agent Integration Profiles

### Section 1: Claude Code Profile
Claude Code integrations should use `CLAUDE.md`, `.claude/skills/`, and CLI commands as operational wrappers over constitutional rules.

**Rationale:** Ensures Claude-specific UX does not bypass governance invariants.

**Enforcement:** Claude sessions use `.governance/wbs_cli.py` for all lifecycle transitions; no direct state editing.

### Section 2: Codex Profile
Codex integrations should use `AGENTS.md` and explicit CLI commands as the primary operating contract.

**Rationale:** Codex workflows are strongest when contracts are explicit, deterministic, and repository-local.

**Enforcement:** Codex sessions use `.governance/wbs_cli.py` with explicit agent identifiers and should prefer `--json` when machine-readable output is required.

### Section 3: Agent-Agnostic Engine Requirement
Agent integrations may differ in UX and wrappers, but core governance behavior must remain agent-agnostic.

**Rationale:** Prevents divergent rule sets per model/provider and preserves audit consistency.

**Enforcement:** No hidden caller-based transition logic in governance engine; constitutional rules are applied uniformly.

---

## Relationship to Other Documents

**This Constitution** defines invariant rules (what never changes).

**`AGENTS.md`** defines operating procedures (how to work within the rules).

**`CLAUDE.md`** defines agent-specific integration (how Claude Code uses the rules).

**Codex integration** is governed through `AGENTS.md` and related governance workflow docs.

**`docs/PLAYBOOK.md`** defines error recovery (what to do when things go wrong).

**`.governance/packet-schema.json`** defines packet structure (data format for work units).

**`templates/*.json`** define workflow patterns (common ways to organize work).

All documents must be consistent with this constitution. In case of conflict, constitution takes precedence.

---

## See Also

- **Repository:** https://github.com/daviddfraser-source/Substrate
- **Agent Operating Contract:** `AGENTS.md`
- **Claude Code Integration:** `CLAUDE.md`
- **Codex Governance Workflow:** `docs/governance-workflow-codex.md`
- **Error Recovery Procedures:** `docs/PLAYBOOK.md`
- **Packet Schema:** `.governance/packet-schema.json`
- **State Machine Specification:** `docs/state-machine.md` (when created)
- **Architecture Documentation:** `docs/architecture.md` (when created)

---

## Appendix A: Conformance Matrix

This matrix maps constitutional control domains to current enforcement mode.

Legend:
- `code-enforced`: guaranteed by CLI/server/platform code path
- `process-enforced`: guaranteed by governance process, review, and lead oversight
- `planned`: intended control not yet fully implemented as hard enforcement

| Control Domain | Primary Articles | Current Mode | Evidence / Mechanism |
|---|---|---|---|
| Scope boundaries | Article I | process-enforced | Packet scope, evidence review, delivery reports, closeout drift checks |
| Dependency ordering | Article II §4 | code-enforced | `.governance/wbs_cli.py claim` dependency gate |
| Valid transition path | Article II §2 | code-enforced | Governance engine transition validation in `.governance/wbs_cli.py` + `src/governed_platform/governance/engine.py` |
| Atomic state updates | Article II §1 | code-enforced | temp-file + replace semantics, lock-aware state writes |
| Required completion evidence | Article II §3, Article III | code-enforced + process-enforced | `done` requires notes argument; quality/specificity verified in review/closeout |
| Transition logging | Article II §6, Article VII §1 | code-enforced | append-only lifecycle log in `.governance/wbs-state.json` via CLI/engine |
| State file protection | Article IV §1 | code-enforced + process-enforced | CLI-only mutation path; documented protected paths; no direct state mutation in standard workflows |
| Definition immutability | Article IV §2 | process-enforced | governance policy in `AGENTS.md`/`CLAUDE.md`, human/version-control approval model |
| Governance code protection | Article IV §3 | process-enforced | review policy for `.governance/*`, governance docs restrictions |
| Claim exclusivity | Article V §1 | code-enforced | claim ownership checks + lock-aware updates; concurrency tests |
| Stale work detection | Article V §2 | code-enforced + process-enforced | `wbs_cli.py stale`, lead-driven reset decisions |
| Human override authority | Article VI | process-enforced | lead authority policy, logged reset/override operations |
| Drift assessment closeout | Article VI §4 | code-enforced + process-enforced | `closeout-l2` requires assessment file with required sections; lead-authored assessment |
| Evidence chain traceability | Article VII §2 | process-enforced | evidence notes, packet viewer links, closeout audits |
| Progress/state visibility | Article VII §3-4 | code-enforced | `status`, `progress`, `log`, dashboard API/UI |
| Validation execution | Article VIII | process-enforced + code-enforced (partial) | packet/test validation commands exist; strict per-packet semantic validation remains review-driven |
| Failure declaration/recovery | Article IX | code-enforced + process-enforced | `fail`, automatic blocking, `reset` policy under lead authority |
| Agent integration parity | Article X | code-enforced + process-enforced | shared CLI contract, explicit agent ids, no hidden caller-based transition logic |
| Checksum validation on load | Article IV §1 (superseded detail) | planned | explicit checksums not currently enforced; schema/state validation active |
| Signed constitution amendments | Article VI §2 | planned | version control history active; signed-commit policy not hard-enforced in tooling |

---

## Amendment Log

**Version 1.0** - Initial constitution adopted [Date]
- Established core governance principles
- Defined enforcement mechanisms
- Set standards for evidence and audit

---

## Acknowledgments

This constitution draws on:
- Work Breakdown Structure (WBS) methodology from project management practice
- Formal methods from computer science (state machines, atomic transactions)
- Constitutional AI research from Anthropic
- Production lessons from Queensland Government infrastructure delivery
- Decades of software engineering governance experience

Constitutional governance makes AI agent coordination **safe, auditable, and scalable** by enforcing rules through code rather than hoping agents comply with prompts.

---

**End of Constitution**
