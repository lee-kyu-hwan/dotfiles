# Spec Review Rubric

## Score

| Weight | Criterion |
|---:|---|
| 15 | Problem, scope, and non-goals |
| 20 | Requirement clarity |
| 25 | Acceptance criteria and testability |
| 20 | Architecture, interfaces, and data flow |
| 20 | Feasibility, failure handling, and risk |
| **100** | **Total** |

## Pass gate

A Spec passes only when the score is at least 85, zero Critical/High findings remain, `required_sections` are present, `material_decisions_resolved` confirms zero unresolved material decisions, and `acceptance_criteria_objective` confirms objectively verifiable acceptance criteria for every requirement.

## Findings and severity

Every finding uses the `SPEC-` namespace and has a stable finding ID, severity, concise description, evidence location, violated rubric item, and required resolution. IDs stay stable across rounds: preserve an existing ID when the same material issue remains, and create a new ID only for a distinct finding.

- **Critical:** a fundamental safety, correctness, authorization, data-integrity, or feasibility failure that makes approval unsafe.
- **High:** a material requirement, interface, acceptance, risk, or failure-handling defect that prevents reliable implementation or verification.
- **Medium:** a meaningful quality gap that does not by itself block the gate unless it violates an explicit acceptance criterion.
- **Low:** a minor clarity, maintainability, or polish issue; advisory unless an explicit requirement makes it blocking.

Unsupported opinion without repository or requirement evidence cannot block the gate.

## Review rounds

- Round 1 is a full review of the Spec against every rubric item and required section.
- Later rounds verify open findings and regressions introduced by revisions. A new blocker after Round 1 must be Critical or High and include `new_blocker_evidence` showing that it was newly introduced or could not reasonably have been identified earlier.
- After round 2 without a passing gate, stop and record `NEEDS_REDESIGN`.
- If the same blocking finding ID recurs twice, stop and record `NEEDS_REDESIGN`, even if the round limit has not otherwise been reached.
