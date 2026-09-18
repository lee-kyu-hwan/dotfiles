# Quality Goal Report

- Task ID: 20260911T033338Z-55-completion-integrity-resume
- Mode: strict
- Status: CODE_REVIEW
- Created: 2026-09-11
- Updated: 2026-09-11
- Source goal: #55 completion-time actual workspace fingerprint revalidation and #50-B untracked lstat type/permissions, resumed after bounded reviewer-unverified block

## Classification

strict로 분류했다. 완료 시점 실제 workspace와 저장된 verification·code-review digest의 일치를 강제하는 변경은 외부 프로세스가 verification 뒤 workspace를 바꾸는 시간축 무결성 문제를 다룬다. untracked entry의 lstat 종류·권한과 재귀 directory 자체를 fingerprint에 넣는 변경은 실행 의미가 달라진 파일을 이전 evidence로 완료하지 못하게 하는 경계다. CLI gate, fingerprint encoding, 테스트, 스킬 계약을 함께 바꾸므로 다중 파일 내부 인터페이스 변경이다.

pure transition graph와 state schema는 유지했다. `transition --to COMPLETED` CLI에 mandatory actual-workspace gate를 추가하는 것은 `docs/quality-goal-maintenance.md`의 “게이트 규칙이나 상태 머신 계약 변경: MAJOR”에 해당하므로 `SKILL.md` version을 `5.1.0`에서 `6.0.0`으로 올렸다. 별도 #85의 `5.2.0` 변경과 통합할 때 최종 version은 `6.0.0`이며, #85 기능 자체는 이 branch 범위에 넣지 않았다.

## Review history

- Spec round 1: actual Claude Opus, score 83, `REVISE`. `SPEC-007`은 두 기존 version assertion 갱신 범위 누락, `SPEC-008`은 보호 절과 새 completion 보장 문구의 배치 충돌이었다. Low `SPEC-009`–`SPEC-011`도 함께 제시됐다.
- Spec round 2 readiness: actual Claude Opus, score 91, `READY`. formal round 1 findings와 readiness `READY-001`–`READY-004` 해소를 확인했고, Low `READY-005`(root trailing slash 표현)와 `READY-006`(보호 절 whitespace 경계)을 남겼다.
- Spec round 2 formal 최초 출력: actual Claude Opus, score 92, `PASS`였으나 실행하지 않은 미래 code command를 `verified:false` evidence로 담아 validator가 `PASS reviews must not contain unverified evidence`로 거부했다. 원문 `spec-review-r2-invalid-a1.json`과 validation error를 보존하고 같은 round를 fresh Opus로 한 번 재시도했다.
- Spec round 2 formal 재시도: actual Claude Opus, score 92, `PASS`, blockers 0. 모든 evidence가 verified였고 Low `SPEC-012`만 root slash 표현을 더 고정하라고 권고했다. State에 기록된 passing Spec digest는 `4cac17bd4be94ef0504b2ce51f793150b4a1a4adabbedcffbe64d03d3ea8f0fe`다.
- Plan round 1: actual Claude Opus, score 92, `PASS`, blockers 0. `PLAN-001` creation-order fixture 누락을 Medium으로, `PLAN-002`–`PLAN-005`를 Low로 제시했다. 구현은 같은 T1/AC-11 범위에서 서로 다른 생성 순서의 두 repository가 동일 stream·fingerprint를 만드는 테스트를 추가했고, embedded repository로 실제 `d/` discovery를 만들었으며, helper 이름을 `_validate_completion_workspace(state)`로 고정했다. 구현 기간에는 merge/rebase/HEAD 이동을 하지 않았다.
- Code review round 1: actual Claude Opus, score 76, `REVISE`. `CODE-001`은 새 completion gate와 기존 terminal report 작성 순서가 충돌하는 High blocker였다. Low `CODE-002`는 deep untracked tree의 Python recursion limit, `CODE-003`은 path frame을 생략할 수 있는 dead switch, `CODE-004`는 Git이 ordinary untracked directory를 file-by-file로 열거하는 discovery 한계였다.
- Fix round 2: actual `gpt-5.6-sol` medium이 `CODE-001`–`CODE-003`을 bounded fix로 처리했다. terminal ordering을 세 non-protected 문서 위치에 고정하고, walker를 explicit iterative DFS로 바꾸고, path frame 우회 인자를 제거했다. `CODE-004`는 이 report의 residual risk로 정확히 기록했다. 이 report는 round 2 formal code review 전에 final bytes로 동결한다. 이후 review와 guarded terminal transition 결과는 ignored authoritative state `.claude/quality-state/20260911T033338Z-55-completion-integrity-resume/state.json`에만 기록하며 passing review 뒤 이 report를 수정하지 않는다.

## Blocking-finding resolutions

- `SPEC-007`: R4.4와 Plan T6에 기존 `test_frontmatter_contract`의 exact version과 기존 `test_skill_version_is_major_bumped`의 major 기대값을 각각 `6.0.0`, `6`으로 in-place 갱신하도록 명시했다. 새 중복 version test는 만들지 않았고 CMD-6은 기존 test 이름 보존을 확인했다.
- `SPEC-008`: 모든 기존 protected section을 byte-identical로 유지하고 현재 `## Independent verification` 첫 byte에 새 non-protected `## Completion integrity`를 삽입했다. 새 절은 save 직전 재계산, `state.project_root` 직접 측정, current/valid verification/final `reviews.code[-1]` PASS digest의 삼자 일치와 backward-search 금지, 실패 시 non-completion, lock/generation이 없는 측정 직후 TOCTOU 한계를 모두 단정형으로 기록한다. CMD-4가 `QG_BASE=6d60011cbdaead7946b191d3f12029eef5c141c8` 대비 보호 절 불변을 확인했다.
- `SPEC-009`/`SPEC-012`/`READY-005`: Git의 top-level trailing slash는 discovery marker로만 사용하고 frame·sort 전에 제거한다. root와 nested 모두 normalized repository-relative byte path 하나로 kind와 무관하게 정렬하며, regular directory frame 뒤 children을 depth-first로 걷는다. `d/` 대 `d.txt`, nested mixed kinds, 서로 다른 생성 순서의 동일 entry set을 테스트했다.
- `SPEC-010`: CMD-8은 canonical runbook에 없는 task-local interpreter identity check이며 runbook은 CMD-7에서 끝난다. unsupported pre-3.12 rejection contract인 canonical CMD-7은 범위 밖으로 유지했다.
- `SPEC-011`: version 검증은 두 기존 테스트를 사용하며 중복 test를 추가하지 않았다.
- `READY-006`: 새 heading은 protected `## Codex invocation contract` 뒤의 blank line을 포함한 모든 preceding byte를 바꾸지 않고 기존 `## Independent verification` 시작 위치에 들어간다. content contract가 단일 배치와 중간 top-level heading 부재를 확인하고 CMD-4가 byte identity를 증명했다.
- `CODE-001`: stage table, non-protected `### Terminal`, `## Completion integrity` 세 곳에서 `report.md`와 모든 fingerprint 대상 durable file을 `record-verification`의 fingerprint 측정과 formal review 전에 final bytes로 확정하도록 했다. verification 또는 review 뒤 fingerprint 대상 write가 있으면 fresh verification과 fresh code review를 다시 요구한다. content contract가 세 위치의 순서를 각각 검사한다.
- `CODE-002`: recursive directory walker를 explicit LIFO work stack 기반 deterministic DFS로 바꿨다. mock tree 1,050단계에서도 Python call stack을 소비하지 않고, 기존 canonical ordering과 symlink prune 테스트도 함께 통과한다.
- `CODE-003`: `_read_untracked_value`의 사용되지 않는 `include_path` 매개변수를 제거하고 path frame을 무조건 기록하도록 했다. signature 회귀 테스트가 path framing 우회 surface가 없음을 고정한다.
- `CODE-004`: 승인된 Git discovery 경계는 확장하지 않았다. 아래 Remaining advisory findings에 실제 적용 범위를 명시해 과도한 보장 해석을 막는다.

## Plan approval

- Approval timestamp: 2026-09-11T05:33:51Z
- Plan digest: 13033fe869bfbb996516ace1903c9fb8864c4b025c48db914b9d281b6e7c30f8

## Changed files

- `dot_claude/skills/quality-goal/scripts/quality_state.py`: untracked entry의 normalized path, lstat type, permissions, payload/marker를 length-frame하고 directory를 entry 시점에 frame한 뒤 explicit stack으로 canonical depth-first traversal한다. path frame은 생략할 수 없다. CLI-side `_validate_completion_workspace(state)`가 actual fingerprint를 다시 계산하고 final-record-only 삼자 일치를 강제한다.
- `dot_claude/skills/quality-goal/tests/test_quality_state.py`: `FingerprintMetadataTests`, `CompletionIntegrityCLITests`, `TransitionPurityTests`를 추가해 entry framing, chmod restore, symlink prune, special no-read, creation-order independence, root slash normalization, 1,050단계 stack traversal, path-framing surface, exit 2/3/4와 no-save, HEAD/tracked/untracked mutation, final record no-back-search, pure transition과 schema/parser 불변을 검증한다.
- `dot_claude/skills/quality-goal/tests/test_content_contracts.py`: completion 보장 다섯 요소, terminal report/fingerprint/review 순서, 정확한 section 경계를 기계적으로 고정하고 두 기존 version assertion을 `6.0.0`/major `6`으로 갱신한다.
- `dot_claude/skills/quality-goal/SKILL.md`: frontmatter를 `6.0.0`으로 올리고 non-protected `## Completion integrity` 절과 terminal ordering을 갱신한다. 현재 434줄이며 r1의 421줄에서 13줄 증가했다.
- `docs/development/2026-09-11-55-quality-goal-completion-integrity-resume/spec.md`: passing strict Spec. digest `4cac17bd4be94ef0504b2ce51f793150b4a1a4adabbedcffbe64d03d3ea8f0fe`.
- `docs/development/2026-09-11-55-quality-goal-completion-integrity-resume/spec-revision-notes.md`: formal Spec round 2 revision notes. digest `61e7833a8d015b60cc9d3810f7bca62d104cc9b266d2f58ea42723cd29c96b65`.
- `docs/development/2026-09-11-55-quality-goal-completion-integrity-resume/plan.md`: approved strict Plan. digest `13033fe869bfbb996516ace1903c9fb8864c4b025c48db914b9d281b6e7c30f8`.
- `docs/development/2026-09-11-55-quality-goal-completion-integrity-resume/report.md`: 최종 verification·review 대상에 포함되는 이 frozen report.

기존 dirty `docs/development/2026-09-10-55-quality-goal-completion-integrity/spec.md`와 `report.md`는 각각 SHA-256 `751e15d7040c32564a5587ff333dffe0954ff49c714ee1ccc32981b6e81d6ed3`, `5a124842af49b648b7c485007d82ea8b1e186d5ad7c35ea58c93420dc55211cb`로 byte-identical하게 보존했고 staging 대상에서 제외한다.

## Verification evidence

- Actual model preflight: `gpt-5.6-sol` one-line response check, exit 0. 이후 Spec/Plan author와 implementation은 actual Sol, formal reviews는 actual Claude Opus를 사용했다. 최초 구현 foreground ancestry는 tmux pane `%90` PID 11913 → visible runner 61097 → script 61098 → Codex node/native 61099/61100이었다. fix round 2는 `%90` PID 11913 → visible runner 86167 → script 86168 → Codex node 86169에서 actual Sol medium으로 실행됐다.
- Test-first metadata red: `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.12 .../test_quality_state.py FingerprintMetadataTests`, exit 1. 7 tests가 metadata frame 누락, chmod 비민감, directory discovery 미정규화를 의도대로 드러냈다. 최초 test-only fixture `ValueError`를 assertion failure로 고친 뒤 canonical red를 다시 확보했다.
- Test-first completion/purity red: `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.12 .../test_quality_state.py CompletionIntegrityCLITests TransitionPurityTests`, exit 1. 11 tests 중 10개가 변경 workspace, malformed root, observation failure를 기존 CLI가 잘못 완료하는 동작을 드러냈다.
- Test-first content red: `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.12 -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_content_contracts.py' -k test_completion_current_workspace_exact_guarantee -k test_frontmatter_contract -k test_skill_version_is_major_bumped`, exit 1. completion 절 부재와 기존 5.1.0/major 5 assertion이 실패했다.
- Focused green: 같은 세 명령을 다시 실행해 각각 7 tests `OK`, 11 tests `OK`, 4 selected tests `OK`, 모두 exit 0.
- Fix round 2 test-first red: path-framing bypass signature test exit 1, 1,050단계 mock walker test exit 1(`RecursionError`), 세 문서 위치의 terminal ordering content contract exit 1이었다. 구현 뒤 focused 두 fingerprint test, 전체 `FingerprintMetadataTests` 9개, ordering content contract가 모두 `OK`였다. Sol의 최초 결합 green shell은 앞선 deep test가 실패했지만 마지막 content command가 성공해 shell exit 0이었으므로 성공 증거로 사용하지 않았고, 잔존 recursive call을 제거한 뒤 개별 명령을 다시 통과시켰다.
- CMD-2 round 2: `/opt/homebrew/bin/python3.12 assert_python_version.py` 뒤 세 focused state class와 selected content contracts 실행, exit 0. 20 state tests와 4 content tests가 모두 `OK`였다. 로그: ignored state의 `final-r2-cmd2.log`.
- CMD-8 round 2: resolved interpreter와 version을 검사·출력, exit 0. `/opt/homebrew/bin/python3.12`, `Python 3.12.14`. 지원 계약은 Python 3.12+이며 이 절대 경로와 exact patch version은 이번 macOS verification 환경에만 해당한다. 로그: `final-r2-cmd8.log`.
- CMD-5 round 2: `/opt/homebrew/bin/python3.12 -c 'import ast, pathlib; ... ast.parse(...)'`, exit 0. 세 modified Python file을 bytecode 생성 없이 parse했다. 로그: `final-r2-cmd5.log`. 추가 `py_compile` 독립 증거도 task-state 내부 고유 `pycache-fix-r2-independent/`로 실행해 exit 0이었다. Sol은 같은 보조 검사를 공유 `/tmp/qg-fix-r2-pycache`로 실행했으므로 경로 이탈로 기록하며 해당 `/tmp`를 삭제하지 않았다.
- CMD-1 round 2: `/opt/homebrew/bin/python3.12 assert_python_version.py && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.12 -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_*.py'`, exit 0. 406 tests, `OK`. 예상 error-path stderr가 test 중 출력됐지만 suite failure는 없었다. 로그: `final-r2-cmd1.log`.
- CMD-3 round 2: `wc -l < dot_claude/skills/quality-goal/SKILL.md`, exit 0, `434`로 500 미만. 로그: `final-r2-cmd3.log`.
- CMD-4 round 2: `/opt/homebrew/bin/python3.12 dot_claude/skills/quality-goal/tests/assert_preserved_sections.py 6d60011cbdaead7946b191d3f12029eef5c141c8`, exit 0, `보존 대상 절 불변`. 로그: `final-r2-cmd4.log`.
- CMD-6 round 2: `/opt/homebrew/bin/python3.12 dot_claude/skills/quality-goal/tests/assert_tests_preserved.py 6d60011cbdaead7946b191d3f12029eef5c141c8`, exit 0, `기존 테스트 보존`. 로그: `final-r2-cmd6.log`.
- Scope/bytes round 2: old dirty 두 파일과 passing Spec/Plan/revision-note digest를 비교하고 `git diff --check`와 `git status --short --untracked-files=all`을 실행한다. tracked diff는 네 허용 구현 파일뿐이며 old dirty 두 파일은 untracked 상태로 그대로 남는다. 정본 로그는 ignored state의 `final-r2-scope.log`다.
- Plan structure: canonical `revision_check.py --artifact plan` 실행, exit 0, `passed=true`, `empty_cells=0`, AC-1–AC-21 trace가 완전하다. author 최초 임시 revision check는 task-local token 배치 문제로 exit 1이었고 plan.md만 보정한 뒤 통과했다. 정본 evidence는 ignored state의 `plan-structure-r1.json`이다.
- 별도 type-check, lint, build category는 not configured다. `pyproject.toml`, `setup.cfg`, `tox.ini`, `mypy.ini`, Ruff/Flake8/Pyright config, Makefile, package/requirements/lock 파일을 `rg --files`로 조사했으며 이 quality-goal Python module에 적용할 별도 정본을 찾지 못했다. 이 category를 passed로 표기하지 않는다.
- Production mutation은 없었다. `chezmoi apply`, deploy, merge, rebase, checkout/reset/clean, global Git 설정 변경을 실행하지 않았다.

## Remaining advisory findings

- `PLAN-003`은 red-test task와 green implementing task 중 trace row의 primary owner 표현이 불명확하다는 Low 문서 권고다. 각 AC의 실제 passing command는 Plan trace와 이 report에 기록됐고 code behavior에는 영향이 없다. 후속 Plan 문구 수정은 frozen approved digest를 바꾸므로 하지 않았다.
- `PLAN-005`는 Plan의 일반 금지 목록에 rebase를 명시하라는 Low 권고다. 승인된 구현 프롬프트와 실제 실행에서 merge/rebase/모든 HEAD 이동을 금지했고 수행하지 않았다. 통합은 root owner가 final PR 단계에서 맡는다.
- Residual TOCTOU: 새 CLI는 save 직전에 actual workspace를 재계산하지만 lock이나 generation counter가 없으므로 측정 직후 동시 변경까지 원자적으로 보장하지 않는다. `SKILL.md`와 content contract에 이 한계를 명시했다.
- `CODE-004`: lstat type/permission frame은 Git이 untracked entry로 실제 열거한 경로와 그 경로가 regular directory일 때 재귀로 발견한 children에 적용된다. 일반 untracked directory는 `git ls-files --others --exclude-standard`가 보통 내부 파일을 개별 경로로 열거하므로 그 directory 자체의 mode는 frame되지 않을 수 있다. embedded repository처럼 Git이 trailing slash directory record를 내는 경우와 그 children은 frame된다.
- 구현 호출에 제공된 worktree root의 `AGENTS.md` 실제 파일은 존재하지 않았다. 세션에 주입된 repository 지침과 passing Spec/Plan/implementation prompt가 동일한 worktree·언어·금지 범위를 직접 고정했으며 product behavior에는 영향이 없다.
- Fix round 2의 visible runner `--log`는 `implementation-fix-r2-visible.log`, Codex stdout은 `implementation-fix-r2-events.jsonl`로 서로 달라 pane에는 heartbeat만 보였다. 실제 foreground ancestry와 events/result는 보존했고 호출을 중단·중복하지 않았다. 다음 formal review는 runner와 reviewer가 동일한 events 경로를 사용한다.
- Spec author의 한 revision check가 `/tmp`에 출력된 runtime-location deviation이 있었고 원본을 삭제하지 않았다. 이후 canonical task-state `revision-check-spec-r2.json`과 `plan-structure-r1.json`을 생성해 검증·review에 사용했다.

## Final status

이 파일은 completion-integrity 계약 때문에 formal code review 전에 완성·동결된 역사적 snapshot이다. 이후 report를 수정하면 fingerprint가 바뀌어 passing review를 재사용할 수 없으므로 terminal 결과는 authoritative ignored state에만 추가 기록한다.

- Status: completion candidate frozen; formal code review and guarded transition follow this snapshot
- Machine-readable reason: AWAITING_FORMAL_CODE_REVIEW_AT_REPORT_FREEZE
