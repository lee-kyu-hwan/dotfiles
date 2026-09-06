# PLAN-06 shape fixture

## Tasks

### T1. First

대상 AC: AC-1, AC-2
AC-1 `docs/quality-goal-maintenance.md`
The separate explanatory paragraph mentions spec.md, but not on the criterion's line.
AC-2 `CMD-1` `test_alpha`

### T2. Second

대상 AC: AC-3, AC-4, AC-5
AC-3 `docs/three.md`
AC-4 `CMD-1` `test_beta`
AC-5 `docs/five.md`

### T3. Third

대상 AC: AC-6, AC-7, AC-8
AC-6 `docs/six.md`
AC-7 `docs/seven.md`
AC-8 `docs/eight.md`

## Verification commands

| CMD-1 | test command |
| command | CMD-2 | second command |

## Acceptance-criteria traceability

| Criterion | Task | Verification command | Expected outcome |
| --- | --- | --- | --- |
| AC-1 | T1 | [문서] `spec.md` § Test strategy | missing on the AC line |
| AC-2 | T1 | `CMD-1` `test_alpha` | ok |
| AC-3 | T2 | `docs/three.md` | ok |
| AC-4 | T2 | `CMD-1` `test_beta` | ok |
| AC-5 | T2 | `docs/five.md` | ok |
| AC-6 | T3 | `docs/six.md` | ok |
| AC-7 | T3 | `docs/seven.md` | ok |
| AC-8 | T3 | `docs/eight.md` | ok |
