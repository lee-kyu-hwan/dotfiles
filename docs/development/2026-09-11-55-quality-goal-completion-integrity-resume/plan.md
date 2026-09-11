# Quality Goal Implementation Plan

- Task ID: 20260911T033338Z-55-completion-integrity-resume
- Mode: strict
- Status: PLAN_REVIEW
- Created: 2026-09-11
- Updated: 2026-09-11
- Source goal: #55 completion-time actual workspace fingerprint revalidation and #50-B untracked lstat type/permissions, resumed after bounded reviewer-unverified block

## Spec link

이 Plan은 [passing Spec](./spec.md)의 SHA-256 `4cac17bd4be94ef0504b2ce51f793150b4a1a4adabbedcffbe64d03d3ea8f0fe`를 구현 기준으로 사용한다. 구현 중 Spec digest가 달라지면 작업과 verification을 중단하고 해당 artifact를 다시 review하는 정상 quality-goal 절차로 돌아간다.

## Global constraints

- 작업 위치는 `/Users/lee-kyu-hwan/code/dotfiles__worktrees/55-fix-quality-goal-completion-integrity` 하나로 제한한다. 구현 허용 파일은 `dot_claude/skills/quality-goal/scripts/quality_state.py`, `dot_claude/skills/quality-goal/tests/test_quality_state.py`, `dot_claude/skills/quality-goal/tests/test_content_contracts.py`, `dot_claude/skills/quality-goal/SKILL.md`이며, durable evidence로 이 artifact directory의 `report.md`를 만든다. Plan review round 2가 생길 때만 같은 directory의 `plan-revision-notes.md`를 revision grammar에 맞게 만든다.
- `docs/development/2026-09-10-55-quality-goal-completion-integrity/`의 기존 dirty `spec.md`와 `report.md`는 시작 bytes를 기록해 두고 구현·검증·staging·rollback 어느 단계에서도 수정하거나 포함하지 않는다. 시작 SHA-256은 각각 `751e15d7040c32564a5587ff333dffe0954ff49c714ee1ccc32981b6e81d6ed3`, `5a124842af49b648b7c485007d82ea8b1e186d5ad7c35ea58c93420dc55211cb`다. 기존 `spec.md`, SHA-256 `61e7833a8d015b60cc9d3810f7bca62d104cc9b266d2f58ea42723cd29c96b65`인 `spec-revision-notes.md`, `.claude/quality-state/**`의 prior artifact도 수동으로 수정·삭제하지 않는다.
- test-first 순서를 지킨다. 새 test class/method가 의도한 이유로 실패하는 것을 먼저 확인하고, 최소 구현 후 같은 명령이 성공하는 것을 확인한다. unrelated test rename, broad refactor, fixture cleanup은 하지 않는다.
- pure `transition(state, target, reason)` 및 `_validate_transition_request`에는 Git/filesystem I/O를 추가하지 않는다. 새 completion-time observation은 CLI adapter에서 state를 저장하기 직전에 수행하며, 새 state field, schema version, token, nonce, generation counter, lock 또는 required CLI argument를 도입하지 않는다.
- completion은 `reviews.code[-1]`만 사용한다. 이 final record 자체가 PASS가 아니면 earlier PASS를 검색하지 않는다. current actual fingerprint, valid verification fingerprint, final PASS record의 `artifact_digest` 세 값이 모두 같은 유효 lowercase SHA-256일 때만 기존 pure guard와 save로 진행한다.
- malformed `project_root` missing/empty/non-string은 fingerprint 호출 전에 `StateError`, exit 2로 처리한다. mismatch/non-PASS/invalid verification은 `TransitionError`, exit 3이며, non-Git/no-commit/Git/filesystem observation 실패는 `GitError`/`FilesystemError`, exit 4를 유지한다. 모든 거부는 save 전이어야 하고 state file bytes가 실행 전과 동일해야 한다.
- untracked canonical stream은 모든 entry를 `path -> lstat type -> permissions -> payload/marker`로 length-frame한다. Git이 top-level directory discovery에 붙인 trailing slash는 입력 marker일 뿐이다. 모든 top-level repository-relative directory path는 path framing과 sorting 전에 trailing slash를 제거하며, repository root와 하위 directory 모두 normalized repository-relative byte path 하나의 lexicographic ordering을 kind와 무관하게 사용한다. regular directory는 선택된 위치에서 directory frame을 기록한 뒤 children을 depth-first로 걷고, symlink-directory는 target만 frame한 뒤 prune한다.
- `os.lstat`로 entry 자체만 분류한다. regular file만 payload를 읽고, symlink는 existing/broken/directory 여부와 무관하게 `os.readlink` target bytes만 읽으며 dereference하지 않는다. FIFO/socket/device 등 special entry는 payload를 open/read하거나 `readlink`하지 않고 marker만 기록한다.
- `SKILL.md`에는 현재 `## Independent verification` heading의 정확한 첫 byte 위치에 새 non-protected `## Completion integrity` heading을 삽입한다. 그 앞의 protected `## Codex invocation contract` chunk는 경계 blank line을 포함해 byte-identical해야 하며, 모든 protected section과 `QG_BASE=6d60011cbdaead7946b191d3f12029eef5c141c8` 및 preservation 목록은 수정하지 않는다.
- 새 문서 절은 다섯 요소를 기계적으로 검사할 수 있는 단정형 문장으로 기록한다: save 직전 재계산, `state.project_root` 직접 측정, current/valid verification/final `reviews.code[-1]` PASS digest의 삼자 일치와 backward-search 금지, 실패 시 non-completion, lock/generation 부재로 측정 직후 동시 변경까지 보장하지 않는 한계. protected prose의 “last passing code review”는 final record 자체가 PASS라는 뜻으로만 한정한다.
- `SKILL.md` version은 gate/state-machine 계약 변경 때문에 정확히 `6.0.0`으로 올린다. 기존 `test_frontmatter_contract`의 exact version과 기존 `test_skill_version_is_major_bumped`의 major 기대값만 각각 `6.0.0`, `6`으로 in-place 수정하고 별도 version test를 만들지 않는다. concurrent #85의 계획된 `5.2.0`은 integration 시 `6.0.0`에 subsume되며 #85 behavior는 이 branch 범위가 아니다.
- 지원 계약은 Python 3.12+다. 이 task의 판정만 resolved `/opt/homebrew/bin/python3.12`와 exact `Python 3.12.14`에서 수행하며, 그 path가 다른 지원 system에도 있다고 문서화하지 않는다. repository에 별도 type-check, lint, build configuration이 없으므로 그 category는 final evidence에 “not configured”와 조사한 경로를 기록하고 passed로 표시하지 않는다.
- `chezmoi apply`, commit, push, merge, deploy, production mutation, 전역 Git 설정 변경을 하지 않는다. eventual commit 준비가 승인되면 explicit path staging만 사용하고 old dirty artifact와 `.claude/quality-state/**`는 포함하지 않는다.

## File map

| File | 작업 | 책임과 interface boundary |
|---|---|---|
| `dot_claude/skills/quality-goal/scripts/quality_state.py` | 수정 | `_read_untracked_value`, `_walk_untracked_directory`, `compute_workspace_fingerprint`의 normalized path/metadata/canonical traversal; `_build_parser`의 기존 surface 보존; `main`의 `transition --to COMPLETED` CLI-only pre-save actual fingerprint gate; pure `transition` guard와 exit mapping 보존 |
| `dot_claude/skills/quality-goal/tests/test_quality_state.py` | 수정 | 기존 temporary Git helpers를 재사용해 새 `FingerprintMetadataTests`, `CompletionIntegrityCLITests`, `TransitionPurityTests`와 명명된 regression methods를 추가; 기존 `FingerprintTests` 및 state/schema/parser tests를 그대로 유지 |
| `dot_claude/skills/quality-goal/tests/test_content_contracts.py` | 수정 | 새 `test_completion_current_workspace_exact_guarantee`; 기존 `test_frontmatter_contract` version을 `6.0.0`으로, 기존 `test_skill_version_is_major_bumped` major를 `6`으로 in-place 갱신; duplicate version test 금지 |
| `dot_claude/skills/quality-goal/SKILL.md` | 수정 | frontmatter `version: 6.0.0`; protected `## Codex invocation contract` 뒤/current `## Independent verification` 첫 byte에 non-protected `## Completion integrity` 삽입; 다섯 요소 exact guarantee와 final-record-only 해석 기록 |
| `dot_claude/skills/quality-goal/tests/assert_preserved_sections.py` | 검사만 | `QG_BASE`의 protected chunks를 byte 비교하는 기존 checker; section 목록과 checker logic은 변경 금지 |
| `dot_claude/skills/quality-goal/tests/assert_tests_preserved.py` | 검사만 | existing test name preservation 판정; 두 version assertion body 수정이 name set을 바꾸지 않음을 판정 |
| `docs/quality-goal-maintenance.md` | 검사만 | canonical command table source. 이 task에서는 local CMD-2와 CMD-5만 same-name command를 override하고 CMD-8만 새 local command이며 canonical pre-3.12 command는 범위 밖 |
| `docs/development/2026-09-11-55-quality-goal-completion-integrity-resume/spec.md` | 검사만 | digest가 고정된 passing requirement/AC source; 구현 중 수정 금지 |
| `docs/development/2026-09-11-55-quality-goal-completion-integrity-resume/spec-revision-notes.md` | 검사만 | prior Spec revision evidence; byte-identical 보존 |
| `docs/development/2026-09-11-55-quality-goal-completion-integrity-resume/plan.md` | 생성 후 review 대상 | 이 implementation handoff. approval 뒤 수정되면 verification을 invalidate하고 PLAN_REVIEW로 복귀 |
| `docs/development/2026-09-11-55-quality-goal-completion-integrity-resume/plan-revision-notes.md` | Plan round 2에서만 생성 | PLAN finding과 touched AC ripple을 revision grammar의 exact heading/table로 기록 |
| `docs/development/2026-09-11-55-quality-goal-completion-integrity-resume/report.md` | 구현 완료 검증 뒤 생성 | command/exit/output, interpreter identity, unchanged dirty-path evidence, not-configured categories, residual risk를 담는 durable final report; final fingerprint 전에 완성·동결 |
| `.claude/quality-state/20260911T033338Z-55-completion-integrity-resume/**` | orchestrator 기록만 | ignored workflow state/review/verification evidence. 수동 state edit 또는 fingerprint fabrication에 사용하지 않으며 task commit에 staging하지 않음 |
| `docs/development/2026-09-10-55-quality-goal-completion-integrity/**` | 보존 검사만 | pre-existing dirty artifact; 시작 bytes와 종료 bytes를 비교하며 수정·staging 금지 |

## Task dependencies

`T1 -> T2 -> T3 -> T4 -> T5 -> T6 -> T7` 순서로 실행한다. T1이 normalized canonical frame stream의 executable contract를 먼저 고정하고 T2가 그 contract를 구현한다. T3의 completion CLI fixtures는 T2의 mode-sensitive fingerprint를 사용하며, T4는 T3의 failure evidence를 만족시키는 CLI-only adapter gate를 구현한다. T5는 documentation/version change를 먼저 실패시키고 T6가 exact byte-boundary insertion과 version bump를 수행한다. T7은 모든 task 결과를 통합 검증하고 durable report를 완성·동결한 뒤에만 final actual fingerprint와 formal code review digest를 생성한다.

각 task는 앞 task의 passing command를 prerequisite로 소비한다. T2와 T4가 공유하는 `quality_state.py`, T1/T3가 공유하는 `test_quality_state.py`, T5/T6가 공유하는 `test_content_contracts.py`와 `SKILL.md` 때문에 병렬 수정하지 않는다. failure가 발생하면 해당 task에서 멈추고 후속 task를 시작하지 않으며, test가 잘못된 이유로 실패하면 fixture/expectation을 먼저 바로잡아 intended red state를 다시 확인한다.

T7 report가 완성된 뒤 tracked/untracked durable file을 수정하지 않는다. 이후 허용되는 기록은 fingerprint에서 제외되는 `.claude/quality-state/**`의 orchestrator state/review files뿐이다. report 또는 implementation artifact를 고쳐야 하면 verification을 invalidate하고 필요한 task와 전체 T7 순서를 다시 수행한다. formal review가 PASS여도 그 뒤 workspace fingerprint에 영향을 주는 staging, report edit 또는 implementation edit가 생기면 그 PASS digest를 사용해 completion하지 않고 verification/review를 다시 수행한다.

## Tasks

### T1. untracked metadata와 canonical traversal test를 먼저 고정

대상 AC: AC-8, AC-9, AC-10, AC-11, AC-20 — `CMD-2 test_untracked_entry_frames_path_type_permissions_before_payload test_regular_file_permissions_change_and_restore_fingerprint test_symlinks_are_not_dereferenced_and_symlink_directories_are_pruned test_special_files_are_never_opened_or_readlinked test_root_and_nested_mixed_kinds_use_normalized_byte_path_depth_first_order test_metadata_fingerprint_is_repeatable_and_preserves_existing_inputs test_top_level_and_nested_directory_permissions_change_and_restore_fingerprint`

- `test_quality_state.py`에 `FingerprintMetadataTests`를 만들고 다음 methods를 추가한다: `test_untracked_entry_frames_path_type_permissions_before_payload`, `test_regular_file_permissions_change_and_restore_fingerprint`, `test_top_level_and_nested_directory_permissions_change_and_restore_fingerprint`, `test_root_and_nested_mixed_kinds_use_normalized_byte_path_depth_first_order`, `test_symlinks_are_not_dereferenced_and_symlink_directories_are_pruned`, `test_special_files_are_never_opened_or_readlinked`, `test_metadata_fingerprint_is_repeatable_and_preserves_existing_inputs`.
- root discriminating fixture는 Git discovery가 `d/`를 반환하게 하는 top-level regular directory `d/`와 regular file `d.txt`를 함께 두고, sort/frame expected path를 trailing slash 없는 `b"d"`, `b"d.txt"` 순서로 고정한다. nested fixture도 name order와 kind order가 교차하는 regular directory, symlink-directory, regular file, special entry를 두어 normalized repository-relative bytes 하나로 정렬되는 exact frame sequence를 assert한다.
- frame spy는 entry마다 `path`, `lstat-type` 6자리 ASCII octal, `lstat-permissions` 4자리 ASCII octal, kind payload/marker가 정확히 한 번 그 순서로 들어오는지 검사한다. regular directory는 `dir` marker 직후 child subtree, symlink-directory는 `symlink` target 직후 prune되는지 검사한다.
- chmod metamorphic fixtures는 regular file `0644 -> 0755 -> 0644`, top-level/nested regular directory `0755 -> 0700 -> 0755`에서 changed/restored digest를 검사하고 nested child frame이 항상 directory frame 직후 존재하는지 확인한다. symlink fixtures는 existing, broken, directory target의 target string 변경을 다루며 payload read와 walk를 patch로 금지한다. FIFO는 지원 platform에서 사용하고 special reader/readlink 호출 금지는 mock으로 결정적으로 검사한다.
- 실패 명령: `QG_PY=/opt/homebrew/bin/python3.12; "$QG_PY" dot_claude/skills/quality-goal/tests/assert_python_version.py && PYTHONDONTWRITEBYTECODE=1 "$QG_PY" dot_claude/skills/quality-goal/tests/test_quality_state.py FingerprintMetadataTests`. 예상 결과는 exit 1, 새 class의 ordering/metadata/directory framing assertions가 current implementation의 missing type/permissions frames, slash-bearing root frame, kind bucket ordering 또는 missing nested-directory frame 때문에 실패하며 hang이나 special payload read가 없는 것이다.
- recovery: platform이 symlink/FIFO 생성을 지원하지 않는 경우 safety contract 자체를 생략하지 않고 lstat/stat mode와 reader를 mock한 deterministic case로 분리한다. fixture가 Git discovery 형태를 만들지 못하면 `git ls-files --others --exclude-standard -z` output을 assertion에 기록하고 embedded-repository fixture로 `d/` marker를 만든 뒤 다시 red를 확인한다.

### T2. normalized lstat metadata canonical stream 구현

대상 AC: AC-14 — `CMD-2`

- `quality_state.py`에서 Git top-level discovery path를 normalization하는 helper boundary를 두어 directory trailing slash를 제거한 repository-relative bytes를 path frame과 root sort key 모두에 사용한다. root와 recursive children을 동일한 normalized byte comparison으로 정렬하며 kind별 `dirnames`/`filenames` emission bucket을 제거한다.
- `_read_untracked_value`는 한 번의 `os.lstat` 결과로 `path`, `lstat-type`, `lstat-permissions`를 먼저 frame하고 regular file=`file` bytes, regular directory=`dir` marker, symlink=`symlink` target bytes, special=`special` empty marker를 이어 붙인다. recursive walker는 regular directory를 entry 위치에서 frame한 후 children을 depth-first로 방문하고 symlink-directory를 dereference하지 않고 prune한다.
- existing Git component 순서는 `head -> diff -> cached-diff -> untracked stream` 그대로 두고 `.claude/quality-state` exclusion을 root와 nested traversal 모두에서 유지한다. tracked diff construction이나 fingerprint digest algorithm 자체는 바꾸지 않는다.
- 통과 명령: `QG_PY=/opt/homebrew/bin/python3.12; "$QG_PY" dot_claude/skills/quality-goal/tests/assert_python_version.py && PYTHONDONTWRITEBYTECODE=1 "$QG_PY" dot_claude/skills/quality-goal/tests/test_quality_state.py FingerprintMetadataTests FingerprintTests`. 예상 결과는 exit 0와 `OK`; 새 exact stream/mode/safety tests 및 기존 HEAD/tracked/untracked/state-exclusion/determinism tests가 모두 통과한다.
- failure handling: `lstat`, regular read, `readlink`, traversal error는 offending path를 포함한 기존 `FilesystemError`로 변환한다. special entry에는 open/read/readlink를 호출하지 않는다. duplicate frame 또는 discovery alias가 보이면 normalized path set으로 조용히 숨기지 말고 fixture로 재현한 뒤 entry당 exactly-once contract를 만족하도록 discovery/walk 경계를 수정한다.

### T3. completion CLI actual-fingerprint gate와 purity test를 먼저 고정

대상 AC: AC-6, AC-13 — `CMD-2 test_pure_completion_transition_performs_no_git_or_filesystem_io test_pure_completion_transition_keeps_stored_digest_guard test_state_schema_and_transition_parser_surface_are_unchanged`

- `test_quality_state.py`에 `CompletionIntegrityCLITests`를 만들고 `test_unchanged_workspace_completes_with_current_verified_final_pass_digest`, `test_tracked_change_after_verification_refuses_without_saving`, `test_untracked_mode_change_after_verification_refuses_without_saving`, `test_head_change_after_verification_refuses_without_saving`, `test_final_revise_never_back_searches_an_earlier_pass`, `test_final_pass_digest_mismatch_refuses_without_saving`, `test_malformed_project_root_returns_two_without_saving`, `test_repository_observation_failures_return_four_without_saving`을 추가한다.
- completion-ready fixture는 temporary Git repo의 actual fingerprint를 valid verification과 final review digest에 기록한다. 거부 test마다 invocation 직전 state bytes를 저장하고 exit code, stderr의 error category, post-invocation byte identity, non-`COMPLETED` stage를 함께 assert한다. malformed root는 missing/empty/non-string subtests, observation failure는 non-Git/no-commit/patched Git failure/patched filesystem failure subtests로 구체화한다.
- `TransitionPurityTests`에 `test_pure_completion_transition_performs_no_git_or_filesystem_io`, `test_pure_completion_transition_keeps_stored_digest_guard`, `test_state_schema_and_transition_parser_surface_are_unchanged`를 추가한다. fingerprint/Git/filesystem functions를 호출 시 fail하도록 patch하고 pure transition의 기존 stored digest success/failure를 유지하며 initial/final state key set, `schema_version == 1`, `_build_parser()`의 transition option set이 늘지 않았음을 검사한다.
- 실패 명령: `QG_PY=/opt/homebrew/bin/python3.12; "$QG_PY" dot_claude/skills/quality-goal/tests/assert_python_version.py && PYTHONDONTWRITEBYTECODE=1 "$QG_PY" dot_claude/skills/quality-goal/tests/test_quality_state.py CompletionIntegrityCLITests TransitionPurityTests`. 예상 결과는 exit 1; purity/schema compatibility assertions는 유지되지만 current CLI가 verification 뒤 mutation을 재측정하지 않아 at least tracked/untracked-mode/HEAD refusal tests가 실패한다.
- recovery: mutation refusal이 fixture setup에서 먼저 막히면 final review record, valid verification path, empty blockers/open findings를 확인해 fixture가 기존 gate를 통과하는 상태인지 먼저 고친다. state bytes 비교는 JSON 재직렬화가 아니라 `Path.read_bytes()` 전후 exact bytes를 사용한다.

### T4. CLI-only pre-save 삼자 일치 gate 구현

대상 AC: AC-1, AC-2, AC-3, AC-4, AC-5, AC-7 — `CMD-2 test_unchanged_workspace_completes_with_current_verified_final_pass_digest test_tracked_change_after_verification_refuses_without_saving test_untracked_mode_change_after_verification_refuses_without_saving test_head_change_after_verification_refuses_without_saving test_final_revise_never_back_searches_an_earlier_pass test_final_pass_digest_mismatch_refuses_without_saving test_malformed_project_root_returns_two_without_saving test_repository_observation_failures_return_four_without_saving`

- `quality_state.py`의 `main` transition dispatch가 target `COMPLETED`이며 current stage가 `CODE_REVIEW`인 candidate를 save 전에 별도 CLI adapter helper로 처리하도록 한다. helper는 pure `_validate_transition_request`로 stage/target과 기존 stored gate를 먼저 확인하되 state를 mutate하지 않고, non-empty string `state.project_root`를 검증한 뒤 그 exact value로 `compute_workspace_fingerprint`를 호출한다.
- helper는 actual current digest, `verification.workspace_fingerprint`, `reviews.code[-1].artifact_digest`가 모두 valid lowercase SHA-256이고 같으며 verification valid/final record PASS/empty blockers/empty open findings인지 확인한다. earlier review iteration이나 “last PASS” search helper를 사용하지 않는다. 성공 후에만 기존 pure `transition(state, target, reason)`을 호출하고 `_mutating_result`가 atomic save한다.
- malformed root에는 `StateError("project_root must be a non-empty string")` 계열의 식별 가능한 메시지, mismatch/non-final-PASS에는 삼자 일치/final PASS failure를 구별 가능한 `TransitionError` 메시지를 사용하되 file content나 raw fingerprint를 stderr에 출력하지 않는다. Git/filesystem exceptions는 existing main mapping으로 exit 4가 되게 그대로 전달한다.
- 통과 명령: `QG_PY=/opt/homebrew/bin/python3.12; "$QG_PY" dot_claude/skills/quality-goal/tests/assert_python_version.py && PYTHONDONTWRITEBYTECODE=1 "$QG_PY" dot_claude/skills/quality-goal/tests/test_quality_state.py CompletionIntegrityCLITests FingerprintMetadataTests TransitionPurityTests TransitionTests CLITests`. 예상 결과는 exit 0와 `OK`; unchanged completion은 exit 0/`COMPLETED`, mismatch cases는 exit 3, malformed root는 exit 2, observation failures는 exit 4이며 모든 refusal state bytes가 동일하다.
- failure handling: adapter check 중 state object가 잠시라도 mutate되거나 `_mutating_result`가 refusal을 save하면 구조를 되돌려 operation 성공 뒤에만 save하는 boundary를 복구한다. completion 이외 target은 기존 lambda path와 결과를 유지한다.

### T5. completion guarantee와 version content contract를 먼저 실패시킴

대상 AC: AC-12 — `CMD-2 test_completion_current_workspace_exact_guarantee`

- `test_content_contracts.py`에 `QualityGoalSkillContentTests.test_completion_current_workspace_exact_guarantee`를 추가한다. `## Completion integrity` 단일 존재, `## Independent verification` 바로 앞 adjacency, 현재 insertion byte 앞의 `## Codex invocation contract` protected chunk 보존 전제를 검사한다.
- 같은 method에서 다섯 요소를 각각 독립 assertion/pattern으로 검사한다: save 직전 recomputation, direct `state.project_root`, current/valid verification/final `reviews.code[-1]` 자체 PASS digest equality와 no backward search, failure non-completion, lock/generation 부재의 post-measurement concurrency limitation. protected “last passing code review”를 final-record-only로 한정하는 문구도 별도 assertion으로 고정한다.
- 기존 `test_frontmatter_contract` expected version만 `6.0.0`, 기존 `test_skill_version_is_major_bumped` major expectation만 `6`으로 변경한다. 두 method 이름을 유지하고 duplicate version test를 만들지 않는다.
- 실패 명령: `QG_PY=/opt/homebrew/bin/python3.12; PYTHONDONTWRITEBYTECODE=1 "$QG_PY" -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_content_contracts.py' -k test_completion_current_workspace_exact_guarantee -k test_frontmatter_contract -k test_skill_version_is_major_bumped`. 예상 결과는 exit 1; new section 부재와 current `5.1.0`/major `5` 때문에 세 selected contracts가 실패한다.
- recovery: broad substring 하나로 우연히 통과하지 않도록 heading-delimited section을 추출하고 각 guarantee를 독립 subtest/assertion으로 유지한다. protected prose 자체를 새 expected text로 바꾸지 않는다.

### T6. exact boundary 문서 guarantee와 major version 구현

대상 AC: AC-16, AC-17, AC-19, AC-21 — `CMD-3 CMD-4 CMD-6 CMD-2 test_frontmatter_contract test_skill_version_is_major_bumped`

- `SKILL.md` frontmatter의 version 한 줄을 `6.0.0`으로 바꾸고, 현재 `## Independent verification` heading이 시작하는 정확한 byte에 새 `## Completion integrity` section을 삽입한다. insertion 앞 bytes는 그대로 두어 preceding protected `## Codex invocation contract` chunk의 trailing blank line까지 변경하지 않는다.
- 새 section에 T5가 검사하는 다섯 요소와 protected phrase의 final `reviews.code[-1]` PASS-only/no-backward-search 뜻을 명시한다. pure guard/schema/CLI surface가 유지되고 observation-save 사이 TOCTOU를 lock/generation 없이 원자적으로 보장하지 않는다는 한계를 분명히 한다.
- 통과 명령 1: `QG_PY=/opt/homebrew/bin/python3.12; PYTHONDONTWRITEBYTECODE=1 "$QG_PY" -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_content_contracts.py' -k test_completion_current_workspace_exact_guarantee -k test_frontmatter_contract -k test_skill_version_is_major_bumped`. 예상 결과는 exit 0와 `OK`.
- 통과 명령 2: `QG_PY=/opt/homebrew/bin/python3.12; QG_BASE=6d60011cbdaead7946b191d3f12029eef5c141c8; "$QG_PY" dot_claude/skills/quality-goal/tests/assert_preserved_sections.py "$QG_BASE" && test "$(wc -l < dot_claude/skills/quality-goal/SKILL.md)" -lt 500 && "$QG_PY" dot_claude/skills/quality-goal/tests/assert_tests_preserved.py "$QG_BASE"`. 예상 결과는 exit 0, `보존 대상 절 불변`, line count 500 미만, `기존 테스트 보존`이다.
- failure handling: preservation check가 실패하면 `QG_BASE`나 checker/list를 바꾸지 않고 `git diff --word-diff=porcelain -- SKILL.md`와 base/current section bytes로 accidental whitespace change를 찾아 새 section 밖의 hunk만 복구한다. line limit 실패 시 protected prose가 아닌 새 section을 의미 손실 없이 압축한다.

### T7. 전체 검증, durable report 동결, final fingerprint와 formal review handoff

대상 AC: AC-15, AC-18 — `CMD-8 CMD-1 CMD-5`

- 아래 Verification commands를 순서대로 실행한다. 각 command의 exact stdout/stderr 요약과 exit code, CMD-1 test count/`OK`, CMD-8 resolved path/version을 수집한다. old dirty directory의 pre/post file digest와 `git status --short --untracked-files=all`, allowed-path `git diff`를 비교해 scope를 확인한다.
- T7의 test-first prerequisite는 T1, T3, T5에 기록된 세 exact red commands가 구현 전 exit 1과 의도한 assertion failure를 남긴 evidence다. 이 evidence가 없으면 final passing sequence를 실행해도 test-first completion으로 판정하지 않는다.
- repository inspection상 별도 type-check, lint, build configuration이 없음을 `report.md`에 consulted paths와 함께 “not configured”로 기록한다. CMD-2는 strict high-risk end-to-end path, CMD-5는 read-only syntax check, CMD-1은 relevant full suite다. configured되지 않은 category를 passed로 표기하지 않는다.
- 모든 command가 성공한 뒤 `report.md`를 완성한다. report에는 Spec/Plan digest, changed files, AC 결과, command evidence, Python 3.12.14 한 환경이라는 한계, exit 2/3/4 recovery, TOCTOU residual risk, no production mutation, old dirty/prior artifact preservation을 기록한다. 이 시점 이후 report와 모든 fingerprint-included tracked/untracked file을 동결한다.
- report 동결 후 `"$QG_PY" dot_claude/skills/quality-goal/scripts/quality_state.py fingerprint --project-root "$PWD"`로 actual digest를 계산하고, 같은 값을 ignored workflow evidence의 valid verification fingerprint로 `record-verification`한다. digest를 수동 편집하거나 추정하지 않는다.
- formal code review에는 frozen workspace의 changed-file list, unified diff, verification JSON path, base revision, 방금 계산해 verification에 기록한 exact workspace fingerprint를 `artifact_digest`로 전달한다. completion candidate는 반드시 final `reviews.code[-1]`가 PASS이고 그 record digest와 valid verification과 completion CLI가 재계산한 current digest가 같은 상태여야 한다.
- formal review가 REVISE이면 completion하지 않고 fix task로 돌아가 T7 전체를 다시 실행해 report를 다시 완성·동결하고 새 fingerprint/verification/review를 만든다. PASS 뒤에도 report edit, implementation edit, staging 등 fingerprint 변화가 있으면 stale PASS를 사용하지 않고 verification/review를 다시 수행한다. final PASS와 current digest가 유지된 때만 기존 `transition --state <path> --to COMPLETED`를 실행하며 exit 0와 saved `COMPLETED`를 요구한다.

## Verification commands

아래 표는 이 task의 exact 실행 순서다. `CMD-2`와 `CMD-5`만 `docs/quality-goal-maintenance.md` canonical same-name command를 local override한다. `CMD-1`, `CMD-3`, `CMD-4`, `CMD-6`은 canonical command/condition을 이 task의 environment binding으로 사용한다. canonical table은 `CMD-7`에서 끝나며 CMD-8은 task-local interpreter identity command다. unsupported pre-3.12 contract인 canonical `CMD-7`은 이번 supported Python 3.12.14 판정 범위 밖이므로 실행하지 않는다.

실행 전 같은 shell에서 `QG_PY=/opt/homebrew/bin/python3.12`와 `QG_BASE=6d60011cbdaead7946b191d3f12029eef5c141c8`를 설정한다.

| ID | 순서와 exact command | 성공 판정 |
|---|---|---|
| CMD-2 | `"$QG_PY" dot_claude/skills/quality-goal/tests/assert_python_version.py && PYTHONDONTWRITEBYTECODE=1 "$QG_PY" dot_claude/skills/quality-goal/tests/test_quality_state.py CompletionIntegrityCLITests FingerprintMetadataTests TransitionPurityTests && PYTHONDONTWRITEBYTECODE=1 "$QG_PY" -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_content_contracts.py' -k test_completion_current_workspace_exact_guarantee -k test_frontmatter_contract -k test_skill_version_is_major_bumped` | 첫째. exit 0, 세 집중 regression class와 exact guarantee 및 두 existing version contract가 `OK`; completion scenarios의 내부 expected exits는 success 0/refusal 2·3·4 |
| CMD-8 | `resolved=$(command -v "$QG_PY") && version=$("$QG_PY" --version 2>&1) && test "$resolved" = /opt/homebrew/bin/python3.12 && test "$version" = 'Python 3.12.14' && printf '%s\n%s\n' "$resolved" "$version"` | 둘째. exit 0, `/opt/homebrew/bin/python3.12`, `Python 3.12.14` 순서로 출력 |
| CMD-5 | `"$QG_PY" -c 'import ast, pathlib; paths = ("dot_claude/skills/quality-goal/scripts/quality_state.py", "dot_claude/skills/quality-goal/tests/test_quality_state.py", "dot_claude/skills/quality-goal/tests/test_content_contracts.py"); [ast.parse(pathlib.Path(path).read_text(encoding="utf-8"), filename=path) for path in paths]'` | 셋째. exit 0, 세 modified Python files가 syntax error 없이 parse되고 bytecode/repository-local `__pycache__`를 만들지 않음 |
| CMD-1 | `"$QG_PY" dot_claude/skills/quality-goal/tests/assert_python_version.py && PYTHONDONTWRITEBYTECODE=1 "$QG_PY" -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_*.py'` | 넷째. exit 0, full suite test count와 `OK` |
| CMD-3 | `wc -l < dot_claude/skills/quality-goal/SKILL.md` | 다섯째. exit 0, numeric output 500 미만 |
| CMD-4 | `"$QG_PY" dot_claude/skills/quality-goal/tests/assert_preserved_sections.py "$QG_BASE"` | 여섯째. exit 0, `보존 대상 절 불변` |
| CMD-6 | `"$QG_PY" dot_claude/skills/quality-goal/tests/assert_tests_preserved.py "$QG_BASE"` | 일곱째. exit 0, `기존 테스트 보존` |

CMD-6 뒤 scope/byte-preservation read-only 확인을 실행하고 durable `report.md`를 완성한다. report가 final bytes가 된 다음에만 fingerprint CLI와 `record-verification`을 실행하고 그 동일 digest로 formal code review를 기록한다. formal review의 final record가 PASS인 뒤 workspace-affecting write 없이 completion CLI를 실행한다. 어느 deterministic command도 실패하면 report에 success를 기록하거나 fingerprint/review/completion 단계로 진행하지 않는다.

scope/byte-preservation 확인의 exact command는 `test "$(shasum -a 256 docs/development/2026-09-10-55-quality-goal-completion-integrity/spec.md | awk '{print $1}')" = 751e15d7040c32564a5587ff333dffe0954ff49c714ee1ccc32981b6e81d6ed3 && test "$(shasum -a 256 docs/development/2026-09-10-55-quality-goal-completion-integrity/report.md | awk '{print $1}')" = 5a124842af49b648b7c485007d82ea8b1e186d5ad7c35ea58c93420dc55211cb && test "$(shasum -a 256 docs/development/2026-09-11-55-quality-goal-completion-integrity-resume/spec-revision-notes.md | awk '{print $1}')" = 61e7833a8d015b60cc9d3810f7bca62d104cc9b266d2f58ea42723cd29c96b65 && git status --short --untracked-files=all && git diff --check -- dot_claude/skills/quality-goal/scripts/quality_state.py dot_claude/skills/quality-goal/tests/test_quality_state.py dot_claude/skills/quality-goal/tests/test_content_contracts.py dot_claude/skills/quality-goal/SKILL.md`다. expected exit은 0이며, 세 preservation hash가 그대로이고 status에는 old dirty files가 untracked로 남되 implementation diff에는 포함되지 않으며 `git diff --check`가 whitespace error를 출력하지 않아야 한다.

## Rollout and rollback

rollout은 local test-only implementation, complete verification, durable report freeze, fingerprint/verification binding, formal code review, completion 순서다. production deploy와 `chezmoi apply`는 없다. 새 fingerprint encoding은 untracked entry가 있는 기존 in-progress state의 stored digest와 달라질 수 있으며 migration/backfill하지 않는다. mismatch이면 fail closed하고 current algorithm으로 verification과 code review를 다시 수행한다. schema/version, parser arguments, transition graph, persisted key set은 그대로다.

rollback trigger는 unchanged completion 실패, changed workspace completion 허용, wrong exit/no-save behavior, root 또는 nested canonical order 불일치, directory frame 누락, symlink dereference, special payload access/hang, nondeterministic digest, protected-byte drift, full-suite/preservation failure다. trigger가 발생하면 completion/fingerprint changes, their tests, 새 content contract/section, `6.0.0` assertion/frontmatter changes를 하나의 task-scoped reverse patch로 함께 되돌린다. protected prose, preservation checker/list, `QG_BASE`, passing Spec/Plan/prior state, old dirty directory는 rollback patch 대상에 넣지 않는다. durable report는 rollback outcome을 기록한 뒤 workflow policy에 따라 갱신하되, 다시 final fingerprint를 잡기 전 완성·동결한다.

pre-commit rollback은 `git diff --`로 네 implementation paths와 new artifact directory를 명시해 task-owned hunks만 확인한 후 reverse patch를 적용한다. post-commit rollback이 필요하면 별도 사용자 승인 아래 task commit 하나만 `git revert`하고 verification/review를 다시 수행한다. rollback 후에도 이미 저장된 fingerprint를 변환하거나 state를 수동 편집하지 않는다.

eventual commit 준비는 workflow completion 뒤 별도 단계다. `git status --short --untracked-files=all`로 old dirty와 task paths를 구분하고 다음 explicit path set만 staging한다: 네 implementation files, 새 directory의 `spec.md`, `spec-revision-notes.md`, `plan.md`, `report.md`, 그리고 실제 Plan round 2에서 생성된 경우에만 `plan-revision-notes.md`. `git add .`, directory-wide broad staging, old dirty directory, `.claude/quality-state/**` staging은 금지한다. staging을 completion 전에 수행했다면 fingerprint가 변한 것으로 보고 T7 verification/review를 다시 실행한다.

## Acceptance-criteria traceability

| Criterion | Task | Verification command | Expected outcome |
|---|---|---|---|
| AC-1 | T4 | `CMD-2 test_unchanged_workspace_completes_with_current_verified_final_pass_digest` | current=valid verification=final PASS digest인 unchanged repo에서 exit 0, persisted `COMPLETED` |
| AC-2 | T4 | `CMD-2 test_tracked_change_after_verification_refuses_without_saving` | tracked mutation 뒤 exit 3, non-completed stage와 exact state byte identity |
| AC-3 | T4 | `CMD-2 test_untracked_mode_change_after_verification_refuses_without_saving` | untracked `0644 -> 0755` 뒤 exit 3, no save |
| AC-4 | T4 | `CMD-2 test_head_change_after_verification_refuses_without_saving` | new commit/HEAD change 뒤 exit 3, no save |
| AC-5 | T4 | `CMD-2 test_final_revise_never_back_searches_an_earlier_pass test_final_pass_digest_mismatch_refuses_without_saving` | earlier PASS를 사용하지 않고 final REVISE와 final digest mismatch를 각각 exit 3으로 거부 |
| AC-6 | T3 | `CMD-2 test_pure_completion_transition_performs_no_git_or_filesystem_io test_pure_completion_transition_keeps_stored_digest_guard test_state_schema_and_transition_parser_surface_are_unchanged` | pure transition I/O 없음, stored guard 보존, schema/parser/state keys 불변 |
| AC-7 | T4 | `CMD-2 test_malformed_project_root_returns_two_without_saving test_repository_observation_failures_return_four_without_saving` | malformed root exit 2, repository/Git/filesystem failure exit 4, mismatch exit 3, 모두 byte-identical no-save |
| AC-8 | T1 | `CMD-2 test_untracked_entry_frames_path_type_permissions_before_payload` | 모든 entry kind에서 path/type/permissions/payload-marker exact order와 exactly-once framing |
| AC-9 | T1 | `CMD-2 test_regular_file_permissions_change_and_restore_fingerprint` | file chmod에서 digest change 후 exact restore |
| AC-10 | T1 | `CMD-2 test_symlinks_are_not_dereferenced_and_symlink_directories_are_pruned test_special_files_are_never_opened_or_readlinked` | symlink target만 frame/prune, special payload/readlink 호출 없음 |
| AC-11 | T1 | `CMD-2 test_root_and_nested_mixed_kinds_use_normalized_byte_path_depth_first_order test_metadata_fingerprint_is_repeatable_and_preserves_existing_inputs` | `d/`와 `d.txt`를 포함한 root/nested normalized byte sort, directory-first frame/depth-first subtree, repeatability와 기존 inputs 보존 |
| AC-12 | T5 | `CMD-2 test_completion_current_workspace_exact_guarantee` | 새 section 단일/정확 인접 배치와 다섯 요소, final-record PASS-only/no-back-search를 독립 assertion으로 고정 |
| AC-13 | T3 | `CMD-2 test_state_schema_and_transition_parser_surface_are_unchanged` | existing state migration 없이 load, graph/terminal/parser surface/schema/key set 불변 |
| AC-14 | T2 | `CMD-2` | 세 focused regression classes와 content-contract/version tests 전체 exit 0, `OK` |
| AC-15 | T7 | `CMD-8 CMD-1` | exact interpreter path/version 출력 뒤 Python 3.12.14 full suite exit 0, test count와 `OK` |
| AC-16 | T6 | `CMD-3` | `SKILL.md` line count 500 미만 |
| AC-17 | T6 | `CMD-4` | `QG_BASE`/preserved list 변경 없이 모든 protected section 및 preceding protected chunk byte-identical |
| AC-18 | T7 | `CMD-5` | 세 modified Python file read-only `ast.parse` exit 0, bytecode/cache 없음 |
| AC-19 | T6 | `CMD-6` | existing test names 전부 보존 |
| AC-20 | T1 | `CMD-2 test_top_level_and_nested_directory_permissions_change_and_restore_fingerprint test_root_and_nested_mixed_kinds_use_normalized_byte_path_depth_first_order` | nested directory `0755 -> 0700 -> 0755` digest change/restore, entry point frame 직후 child stream |
| AC-21 | T6 | `CMD-2 test_frontmatter_contract test_skill_version_is_major_bumped` | 두 existing names가 exact `6.0.0`/major `6`을 판정하고 duplicate version test 없음 |

<!-- strict-only:start -->

This block is required only for strict work. Any inapplicable subsection must be removed for non-strict work; within strict work, mark it as not applicable with a reason before review.

### Threat and trust boundaries

`state.project_root`, Git output, filesystem names/modes/content, symlink target은 untrusted local inputs다. length framing과 normalized repository-relative bytes로 concatenation/order ambiguity를 막고, `lstat`/`readlink`로 repository 밖 target dereference를 금지한다. special file payload access를 금지해 blocking/device side effect를 피한다. state evidence는 신뢰하지 않고 completion 직전 actual workspace를 다시 관찰한다. 단, global lock/generation이 없으므로 observation과 save 사이 TOCTOU는 공개된 residual risk이며 이를 과장해 원자성으로 표현하지 않는다.

completion authority boundary는 CLI adapter의 pre-save check다. pure transition은 persisted facts만 검증하고 I/O하지 않는다. formal review authority는 final `reviews.code[-1]` record 자체이며 earlier PASS는 authority가 아니다. `.claude/quality-state` record는 orchestrator가 갱신할 수 있지만 ignored evidence라는 이유로 수동 state 수정이나 fabricated digest를 신뢰하지 않는다.

### Authorization and tenant isolation

multi-tenant service와 사용자별 authorization surface가 없는 local CLI이므로 tenant-isolation case는 적용되지 않는다. 대신 허용 경계 test는 `state.project_root`로 지정된 temporary repository만 관찰하고, denied boundary는 symlink target directory를 dereference/walk하지 않으며 special device/FIFO payload를 열지 않는 T1/CMD-2 tests로 판정한다. production/home directory mutation이나 external authorization은 수행하지 않는다.

### Migration, compatibility, and rollback

state data migration, schema bump, backfill은 없다. old stored fingerprint가 new canonical encoding과 다르면 completion exit 3으로 fail closed하고 current workspace에서 verification/review를 다시 수행한다. parser/transition graph/state key set compatibility는 `test_state_schema_and_transition_parser_surface_are_unchanged`로 판정한다.

rollback은 behavior, focused tests, exact-guarantee section/test, version/frontmatter assertions를 atomic task unit으로 되돌린다. protected section/checker/list/`QG_BASE`, prior artifacts, old dirty directory는 rollback하지 않는다. rollback 전후 `git status`와 explicit allowed-path diff, old dirty file digests를 evidence로 남기고 새 fingerprint evidence를 변환하지 않는다.

### Failure recovery and observability

관찰 신호는 CLI exit code, category-specific stderr, unchanged persisted stage/bytes, focused/full suite output이다. exit 2는 malformed state를 정상 workflow로 재생성/복구한 뒤 재시도하고, exit 3은 reviewed workspace로 복원하거나 current workspace에서 verification/review를 다시 실행하며, exit 4는 repository/commit/access/Git/filesystem 원인을 고친 뒤 재시도한다. error output에는 raw file payload나 credentials를 포함하지 않는다.

상시 service metric/alert/trace는 적용되지 않는다. final `report.md`가 interpreter identity, commands/exits, test count, preservation evidence, not-configured categories, residual risk를 durable하게 기록한다. failure가 있으면 PASS/completion을 주장하지 않고 rollback trigger를 평가한다.

### High-risk end-to-end verification

CMD-2가 실제 CLI, temporary Git repository, on-disk state를 사용해 unchanged success와 tracked/untracked-mode/HEAD mutation refusal, earlier PASS/final REVISE refusal, final PASS digest mismatch, malformed root, non-Git/no-commit/Git/filesystem failure를 판정한다. 각 refusal은 expected exit 2/3/4, stderr category, stage non-completion, exact state byte identity를 함께 요구한다.

같은 CMD-2가 root `d/`와 `d.txt` 및 nested mixed-kind fixture를 통해 trailing slash normalization, global normalized-byte ordering, directory-entry frame/depth-first subtree, symlink-directory prune, special no-read, chmod restore, deterministic repeat를 판정한다. 이어 CMD-8, CMD-5, CMD-1, CMD-3, CMD-4, CMD-6을 통과하고 report를 동결한 후에만 final fingerprint/verification/formal review/completion을 수행한다.

### No production mutation confirmation

자동 workflow의 filesystem mutation은 implementation 허용 파일, 새 durable artifact directory, temporary test repositories, ignored orchestrator state에만 한정된다. deployed home, remote Git, production state/service는 변경하지 않으며 `chezmoi apply`, commit, push, merge, deploy, migration을 실행하지 않는다. eventual staging은 workflow 밖에서 explicit task paths만 대상으로 한다.

<!-- strict-only:end -->
