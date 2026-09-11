# Quality Goal Report

- Task ID: 20260906T125225Z-79-다른-저장소의-기여-후보-탐색-검증-스킬-verifying-open-ec840cba
- Mode: strict
- Status: NEEDS_REDESIGN
- Created: 2026-09-06T12:52:25Z
- Updated: 2026-09-06T14:00:42Z
- Source goal: #79 다른 저장소의 기여 후보 탐색·검증 스킬 verifying-open-source-contribution-candidates 설계·구현

## Classification

요청 모드 auto → 분류 **strict**. 근거: (1) 신뢰하지 않는 외부 저장소 코드의 clone·실행 권한 경계, 네트워크·비밀정보 격리, 프롬프트 인젝션 방어라는 보안 통제 설계(#79 범위, 설계문서 § 12); (2) 보안 민감 후보(취약점 재현 정보)의 비공개 분리 규칙(#79 완료기준, 설계문서 § 7); (3) CAN-* 계약은 #80~#82 가 소비하는 스킬 간 호환 계약. standard 조건(다층 신규 디렉터리·새 인터페이스)도 동시에 존재. 이슈 라벨 contribution-research 는 위험 라벨이 아니며, strict/standard 불확실성은 routing-rules 6항으로 상위 모드 선택. 기준 커밋 6d60011cbdaead7946b191d3f12029eef5c141c8, 초기 dirty 경로 없음. 설치 quality-goal v5.0.0(~/.claude/skills/quality-goal, 저장소 소스와 tests 만 상이). Codex gpt-5.6-sol preflight 종료 코드 0.

## Review history

| 산출물 | 라운드 | 점수 | 판정 | 변화 |
|---|---|---|---|---|
| spec | 1 | 77 | REVISE | SPEC-001(High) + SPEC-002~010(Medium) + SPEC-011~015(Low) |
| spec | 2 | 90 | PASS | SPEC-001~015 전부 해소 확인. 신규 advisory SPEC-016·017(Medium), SPEC-018(Low). revision_check exit 0 |
| plan | 1 | 74 | REVISE | PLAN-001(High) + PLAN-002~008(Medium) + PLAN-009~011(Low) |
| plan | 2 | 87 | REVISE | PLAN-001~006·008~011 해소 확인, PLAN-007 Low 잔여. 신규 blocker PLAN-012(High, 개정에서 발생) + PLAN-013(Medium). Plan 라운드 한도(2) 도달 → NEEDS_REDESIGN |

Spec 최종 digest: e672be97c1d547eb59f1b3cb4ff3d1f826f2af5a61735951c97389c0afd85947. Plan 최종 digest: 92430b9d5794dd19589be3ca47cdfa119e11db9ffe7206e16d304bc733e825a8.

## Blocking-finding resolutions

- SPEC-001(실패 저장소 조합의 후보 데이터 모델 미정의): R3.1·R3.6·R5.4·R6.7·AC-8·D10 개정으로 "조회 실패 저장소는 후보를 만들지 않고 failed_scopes 로만" 확정. 라운드 2 리뷰어가 해소 확인.
- PLAN-001(AC-3 의 recheck 절을 판정하는 단계 부재): AC-3 소유를 T6 으로 이동해 discover(clone)·recheck 를 함께 판정. 라운드 2 리뷰어가 해소 확인.
- PLAN-012(예산 소진 저장소 `outcome: failed` 와 종료 코드 4 규칙 충돌): **미해소**. PLAN-003 해소를 위해 라운드 2 에 새로 넣은 두 문장이 충돌. 리뷰어 제안 해법: 종료 코드 4 는 모든 저장소의 `GET /repos` 가 R3.1 네 실패 분류로 끝난 경우로 한정하고 예산 소진은 항상 3(또는 소진 저장소에 별도 outcome `budget-exhausted`). 한 문단 수준의 수정이지만 Plan 라운드 한도로 이 작업 안에서는 반영할 수 없다.

## Plan approval

- Approval timestamp: 없음(승인 단계에 도달하지 않음)
- Plan digest: 92430b9d5794dd19589be3ca47cdfa119e11db9ffe7206e16d304bc733e825a8 (라운드 2 REVISE 상태의 digest, 승인 digest 아님)

## Changed files

이 작업은 구현에 들어가지 않았다. 변경 파일은 문서 디렉터리 하나다.

- docs/development/2026-09-06-79-verifying-open-source-contribution-candidates/spec.md — Spec(라운드 2 PASS)
- docs/development/2026-09-06-79-verifying-open-source-contribution-candidates/spec-revision-notes.md — Spec 라운드 2 개정 노트
- docs/development/2026-09-06-79-verifying-open-source-contribution-candidates/plan.md — Plan(라운드 2 REVISE, PLAN-012·013·007 잔여)
- docs/development/2026-09-06-79-verifying-open-source-contribution-candidates/plan-revision-notes.md — Plan 라운드 2 개정 노트
- docs/development/2026-09-06-79-verifying-open-source-contribution-candidates/report.md — 이 보고서

`dot_codex/skills/verifying-open-source-contribution-candidates/` 는 만들어지지 않았다. 형제 스킬·설치본·GitHub 는 변경 없음.

## Verification evidence

실제 실행한 명령과 결과(모두 2026-09-06):

- `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_codex/skills/analyzing-open-source-pr-patterns/tests -t … -p 'test_*.py'` → 종료 0, `Ran 30 tests`, OK
- 같은 명령, `collecting-recent-closed-prs` → 종료 0, `Ran 108 tests`, OK
- 같은 명령, `dot_claude/skills/quality-goal/tests`(저장소 소스) → 종료 0, `Ran 310 tests`, OK
- `codex exec -C <worktree> --sandbox read-only --ephemeral --model gpt-5.6-sol -c 'model_reasoning_effort="low"' "Reply with one non-empty line."` → 종료 0, 응답 "Acknowledged."
- `/opt/homebrew/bin/python3 -c 'import yaml'` → PyYAML 6.0.3
- `… -m unittest discover … -k no_such_name_xyz` → 종료 5
- 임시 저장소에서 `git checkout -- <미추적 디렉터리>` → 종료 1(pathspec 오류); `git clean -fdq -- <디렉터리>` → 종료 0, 디렉터리 제거
- `git check-ignore -v .claude/quality-state/<task-id>/live/discovery.json` → 종료 0(.gitignore:25)
- `revision_check.py --artifact spec … --state …` (r2) → 종료 0, passed true; `--artifact plan … --spec …` (r2) → 종료 0, passed true
- `validate_review.py validate/gate`: spec r1 valid/REVISE(3), spec r2 valid/PASS(0), plan r1 valid/REVISE(3), plan r2 valid/REVISE(3)

CMD-1·2·4·6·7(새 스킬 대상)은 스킬 파일이 없어 실행하지 않았다(not executed — implementation not started). lint·type check·build·E2E: not configured(확인 파일: .pre-commit-config.yaml 은 gitleaks 만, pyproject/Makefile 없음). 제한된 실제 실행(AC-47): not executed — 계획 승인 단계에 도달하지 않아 사용자에게 대상·예산을 묻지 못했다. 통과로 표시하지 않는다.

## Remaining advisory findings

- SPEC-016(Medium): R5.1 "recheck 는 (b) 를 바꾸지 않는다" 와 R7.1 충돌 — Plan 이 RECHECK_MUTABLE_FIELDS 아홉으로 흡수(리뷰어 확인). Spec 원문은 미수정.
- SPEC-017(Medium): AC-13 산식이 정책 파일 요청 누락 — Plan 이 요청 순서 ①~⑧ 로 흡수했으나 그 과정에서 PLAN-012 발생.
- SPEC-018(Low): duplicate_verdict 보존 경로 — Plan 이 스냅숏 evidence 승계 필드로 흡수(리뷰어 확인).
- PLAN-013(Medium): T8 에 CMD-6 재실행 누락. 후속 Plan 에서 한 줄 추가.
- PLAN-007(Low): strict-only Migration 절의 롤백 문장과 성공 판정 문구 잔여.
- DEV-1(오케스트레이터 편차): Spec r2 에서 validate/gate 성공 전에 record-review 를 실행. 원인은 `--prior` 형식 오류로 validate 가 실패한 뒤 후속 명령이 이어진 것. 직후 올바른 형식으로 validate/gate 재실행해 통과 확인(.claude/quality-state/<task-id>/orchestrator-deviations.md).
- quality-goal 관찰(문제 아님, 메모): `classify --reasons` 는 JSON 배열 파일 경로를 받으며 긴 문자열을 주면 "File name too long"; `set-artifact` 는 artifact_digests 를 채우지 않는다. 문서화 여지.

## Final status

- Status: needs_redesign
- Machine-readable reason: REVIEW_LIMIT_EXHAUSTED:plan (state.json status_reason; plan round 2 REVISE, blocker PLAN-012)

다음 결정(사용자): (a) 이 Spec(PASS)을 그대로 쓰고 PLAN-012·013·007 을 반영한 Plan 으로 새 quality-goal 작업을 시작 — Spec 재작성 없이 Plan 리뷰만 다시 받는 경로가 가장 짧다. (b) Spec 의 advisory 세 건까지 Spec 본문에 반영해 Spec 부터 다시 리뷰. (c) 중단.
