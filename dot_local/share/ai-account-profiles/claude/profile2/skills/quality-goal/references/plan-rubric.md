# Plan Review Rubric

## Score

| Weight | Criterion |
|---:|---|
| 25 | Spec-to-task traceability |
| 20 | Task ordering, boundaries, and dependencies |
| 15 | File and interface precision |
| 25 | Tests and deterministic verification |
| 15 | Failure, rollout, rollback, and risk handling |
| **100** | **Total** |

## Pass gate

A Plan passes only when the score is at least 85, zero Critical/High findings remain, `required_sections` confirms required file, interface, test, and rollback details are present when applicable, `traceability_complete` confirms every acceptance criterion in the Spec maps to an implementation task and a verification step, and `placeholders_absent` confirms placeholder text is absent.

## Findings and severity

Every finding uses the `PLAN-` namespace and has a stable ID, severity, concise description, evidence location, violated rubric item, and required resolution. IDs stay stable across rounds: preserve an existing ID for the same material issue and create a new ID only for a distinct finding.

- **Critical:** a plan defect that makes implementation unsafe, non-reproducible, impossible to verify, or incompatible with an approved requirement.
- **High:** a missing task, mapping, interface, test, rollback detail, or dependency that materially threatens correct implementation.
- **Medium:** a meaningful planning gap that does not independently block the gate unless it violates an explicit acceptance criterion.
- **Low:** a minor precision or maintainability issue; advisory unless an explicit requirement makes it blocking.

Unsupported opinion without evidence cannot block the gate.

## Review rounds

- Round 1 is a full review of the Plan against the Spec and every rubric item.
- Later rounds verify open findings and regressions introduced by revisions. A new blocker after Round 1 must be Critical or High and include `new_blocker_evidence` showing that it was newly introduced or could not reasonably have been identified earlier.
- After round 2 without a passing gate, stop and record `NEEDS_REDESIGN`.
- If the same blocking finding ID recurs twice, stop and record `NEEDS_REDESIGN`.
