# Code Review Rubric

## Review score

Record the code-review score for observability. The score is advisory and can never override a failed deterministic command or a Critical/High finding.

## Pass gate

Code passes only when `required_commands_passed` confirms all approved verification commands exit successfully, zero Critical/High findings remain, `acceptance_criteria_met` confirms acceptance criteria with evidence, `unrelated_changes_absent` confirms no unrelated changes are included, and `documentation_current` confirms documentation is updated for the change.

## Advisory scoring dimensions

Use holistic 0–100 judgment dimensions for correctness versus the approved Plan, test evidence quality, scope adherence, failure/error handling, and documentation currency. No fixed weights are defined by design: the design's code gate is hard-condition-only. The score is advisory observability data. Each finding's `rubric_item` must cite one of this file's named gate conditions or scoring dimensions.

## Findings and severity

Every finding uses the `CODE-` namespace and has a stable ID, severity, concise description, evidence location, violated acceptance or rubric item, and required resolution. IDs remain stable across rounds for the same issue.

- **Critical:** a correctness, security, data-integrity, or production-safety defect that makes the change unsafe.
- **High:** a material acceptance-criteria, regression, interface, or error-handling defect.
- **Medium:** a meaningful quality issue that is advisory unless it violates an explicit acceptance criterion.
- **Low:** a minor maintainability, clarity, or documentation issue.

Deterministic failures are never waivable by the reviewer; the reviewer cannot waive a failed command or use a score to override it.

## Review rounds

- Round 1 is a full review of the implementation, approved scope, verification evidence, acceptance criteria, and documentation.
- Later rounds verify open findings and regressions introduced by fixes. A new blocker after Round 1 must be Critical or High and include `new_blocker_evidence`.
- After round 3 without a passing gate, stop and record `NEEDS_REDESIGN`.
- If the same blocking finding ID recurs twice, stop and record `NEEDS_REDESIGN`.
