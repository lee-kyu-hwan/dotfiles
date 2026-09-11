# Quality Goal Specification

- Task ID: 20260911T033338Z-55-completion-integrity-resume
- Mode: strict
- Status: SPEC_REVIEW
- Created: 2026-09-11
- Updated: 2026-09-11
- Source goal: #55 completion-time actual workspace fingerprint revalidation and #50-B untracked lstat type/permissions, resumed after bounded reviewer-unverified block

## Problem and context

현재 `quality_state.py`의 순수 상태 전이 함수는 `CODE_REVIEW`에서 `COMPLETED`로 갈 때 저장된 verification fingerprint와 마지막 code review의 `artifact_digest`가 같은지만 확인한다. verification과 review가 끝난 뒤 워크스페이스의 tracked content, executable mode 또는 Git `HEAD`가 바뀌어도 완료 CLI는 실제 워크스페이스를 다시 관찰하지 않으므로 오래된 증거로 완료를 저장할 수 있다. issue #55는 실제 병렬 작업 중 이 위험이 발생할 수 있음을 기록하며, 현재 코드의 completion guard도 Git/filesystem 관찰 없이 저장값만 비교한다.

현재 workspace fingerprint는 Git `HEAD`, tracked unstaged/staged diff, 정렬된 untracked 경로와 untracked regular-file content 또는 symlink target을 해시한다. 그러나 untracked entry의 `lstat` file type과 permission bits를 해시하지 않아 content가 같은 untracked 파일의 `chmod` 변화와 일부 종류 변화가 fingerprint에 반영되지 않는다. 또한 재귀 탐색 중 발견한 일반 nested untracked directory 자체는 어떤 frame도 남기지 않는다. 반면 existing/broken symlink는 target을 역참조하지 않고 `readlink` 결과를 해시하며, special file은 content를 읽지 않는 안전 속성을 유지해야 한다.

이 작업의 무결성 경계는 완료 CLI가 state에 기록된 `project_root`를 다시 측정하는 시점이다. 상태 머신의 순수 전이 규칙과 CLI의 Git/filesystem 어댑터 책임을 분리하고, 기존 state schema를 늘리지 않으면서 측정값·verification·review의 삼자 일치를 강제한다. 제품과 코드의 지원 계약은 Python 3.12+이며, 이번 작업의 실제 판정 범위는 이 macOS worktree에 존재하는 `/opt/homebrew/bin/python3.12`의 `Python 3.12.14` 한 환경이다.

## Goals

- 완료 CLI가 완료 state 저장 직전에 `state.project_root`의 현재 workspace fingerprint를 직접 재계산한다.
- 현재 fingerprint, 유효한 verification fingerprint, 마지막으로 기록된 code review record 자체가 PASS인 `artifact_digest`가 모두 같고 기존 completion gate도 통과할 때만 `COMPLETED`를 저장한다.
- 모든 untracked entry에서 path, `lstat` 종류, permissions, payload/marker 순서를 length-frame하고, top-level regular directory, nested regular directory, symlink-directory의 계약을 명확히 한다.
- deterministic ordering, existing/broken symlink 비역참조, special-file 비읽기, 기존 state/CLI 호환성을 보존한다.
- Python 3.12+ 지원 계약을 유지하면서 이번 실제 Python 3.12.14 검증, 집중 회귀 테스트, 보존 runbook, 문법 검사 및 사용자-facing exact guarantee의 기계적 content contract를 통과한다.

## Non-goals

- #50-A의 state read-modify-write 동시성 제어, #50-C의 `required_sections` 권위 목록, #50-D의 `__pycache__` runbook 보강, #50-E의 세션 scratch 경로 규칙은 포함하지 않는다.
- #49, #85의 요구사항은 포함하지 않는다.
- completion과 workspace 변경을 하나의 원자적 임계 구역으로 묶는 전역 RMW lock, generation counter, lease 또는 동시성 프로토콜을 추가하지 않는다.
- 새 검사 token, completion nonce, CLI의 새 필수 인자, state field 또는 state schema version을 추가하지 않는다.
- Git diff 구성, `.claude/quality-state` 제외 규칙, verification 생성 절차, code-review 라운드 정책 또는 transition graph를 변경하지 않는다.
- Linux/macOS의 모든 지원 환경에 `/opt/homebrew/bin/python3.12`가 존재한다고 주장하거나, 이번 한 번의 실행으로 Python 3.12+의 모든 patch version과 platform을 검증했다고 주장하지 않는다.
- fingerprint를 보안 서명이나 적대적 로컬 관리자에 대한 변조 방지 수단으로 확장하지 않는다.
- completion integrity와 #50-B에 필요하지 않은 리팩터링, 테스트 이름 정리 또는 문서 개편을 수행하지 않는다.

## Requirements

- **R1.1** 완료 CLI의 기존 `transition --state <path> --to COMPLETED` 경로는 새 인자를 받지 않고 state를 로드한 뒤 `state.project_root`를 입력으로 `compute_workspace_fingerprint`를 호출하며, 완료 state를 저장하기 직전에 얻은 현재 fingerprint를 사용해야 한다.
- **R1.2** completion은 기존 completion gate에 더해 현재 fingerprint, `verification.workspace_fingerprint`, 마지막으로 기록된 code review record 자체가 PASS인 `artifact_digest`가 동일한 유효한 lowercase SHA-256 값일 때만 허용해야 한다. 마지막 record 자체가 PASS가 아니면 더 이른 PASS를 역탐색하거나 대신 사용해서는 안 된다.
- **R1.3** verification 이후 tracked content, untracked executable mode 또는 Git `HEAD`가 바뀌거나 세 값 중 하나라도 다르면 completion CLI는 완료를 거부하고 state 파일을 `COMPLETED`로 저장하지 않아야 한다.
- **R1.4** 순수 `transition(state, target, reason)`과 그 상태 기반 guard에는 Git/filesystem I/O를 넣지 않아야 한다. 현재 fingerprint 재계산과 삼자 일치의 CLI-only 검사는 state 저장 어댑터 경계에 두며 검사 token이나 새 state schema를 도입하지 않아야 한다.
- **R1.5** `state.project_root`가 missing, empty 또는 non-string이면 `StateError`, CLI 종료 코드 2로 거부하고 state 파일을 저장하지 않아 실행 전후 bytes를 동일하게 보존해야 한다. 유효한 문자열이지만 non-Git, no-commit이거나 Git/filesystem 관찰이 실패하면 기존 `GitError`/`FilesystemError`, 종료 코드 4를 유지한다. mismatch를 포함한 모든 completion 거부에서 영속 state는 완료 전 값으로 보존되어야 한다.
- **R2.1** fingerprint에 포함되는 모든 untracked filesystem entry는 top-level regular directory, 재귀 탐색으로 발견한 일반 nested regular directory 및 symlink-directory를 포함하여 path frame 뒤에 `os.lstat`에서 얻은 `stat.S_IFMT(st_mode)` file type과 `stat.S_IMODE(st_mode)` permissions를 길이 프레이밍된 고정 ASCII 표현으로 해시해야 한다. 세 frame은 regular-file content, directory marker, symlink target 또는 special-file marker보다 먼저 들어가야 한다.
- **R2.2** untracked regular file은 metadata 다음에 기존 content bytes를 읽어 해시하고, existing/broken symlink와 directory symlink는 metadata 다음에 `os.readlink`의 target bytes만 해시하며 target을 역참조하지 않아야 한다. FIFO, socket, character/block device와 기타 special file은 종류·permissions와 marker만 해시하고 content open/read 또는 `readlink`를 호출하지 않아야 한다.
- **R2.3** 모든 untracked entry는 정확히 `path -> lstat type -> permissions -> payload/marker` 순서를 따른다. 각 directory 안의 nested regular directory, symlink-directory, regular file 및 그 밖의 entry는 kind와 무관하게 repository-relative byte path의 단일 lexicographic 순서로 방출한다. regular directory는 그 순서에서 walk가 해당 directory에 진입할 때 자신의 path/type/permissions/directory marker를 먼저 기록한 뒤 같은 규칙으로 정렬된 child walk를 계속하고, symlink-directory는 path/type/permissions/symlink-target만 기록한 뒤 역참조하지 않고 prune한다. 따라서 directory subtree는 진입 시점부터 연속된 depth-first canonical stream을 이루며, 동일한 filesystem/Git 상태의 반복 계산은 같은 fingerprint를 반환해야 한다.
- **R2.4** top-level untracked regular file 또는 directory와 nested untracked regular directory의 permissions만 변경하면 fingerprint가 달라지고 원래 permissions로 복원하면 fingerprint도 원래 값으로 복구되어야 한다. metadata 추가가 기존 tracked content/mode/HEAD 탐지와 `.claude/quality-state` 제외를 약화해서는 안 된다.
- **R3.1** `SKILL.md`는 non-protected top-level `## Completion integrity` 절을 새로 만들고, 이를 `## Independent verification` 바로 앞에 배치하여 completion CLI의 authoritative exact guarantee를 단정형으로 명시해야 한다. 그 절과 기존 `QualityGoalSkillContentTests` 또는 동등하게 명확한 content-contract assertion은 다섯 요소인 완료 저장 직전의 재계산 시점, `state.project_root` 직접 측정, current/valid verification/마지막으로 기록된 record 자체가 PASS인 code review digest의 삼자 일치, 실패 시 non-completion, lock/generation 부재 때문에 측정 직후 동시 변경을 보장하지 않는다는 한계를 기계적으로 고정해야 한다. `assert_preserved_sections.py`가 보호하는 모든 기존 절은 `QG_BASE`와 byte-identical하게 유지하며, 기존 protected `## Independent verification`의 “last passing code review” 문구는 새 절과 함께 읽을 때 마지막 `reviews.code[-1]` record 자체가 PASS여야 한다는 뜻이고 이전 PASS 역탐색을 결코 허용하지 않는다고 새 절에서 명시적으로 한정한다. `QG_BASE`를 rebase하거나 protected section 목록을 축소해서는 안 된다.
- **R3.2** 기존 CLI 명령과 인자, transition graph, state schema/version은 호환되어야 한다. 새 fingerprint 규칙 때문에 기존 저장 fingerprint가 현재 값과 달라진 경우에는 자동 변환하지 않고 현재 workspace에서 verification과 code review를 다시 수행해야 한다.
- **R4.1** 임시 Git repository 기반 테스트는 unchanged completion 성공과 verification 이후 tracked content, untracked executable mode, Git `HEAD` 각각의 변경에 대한 completion 거부를 검증하고, 각 거부 뒤 영속 stage가 `COMPLETED`가 아니며 state bytes가 동일함을 검증해야 한다. 마지막 record 판정 fixture는 더 이른 PASS가 있어도 마지막 record가 REVISE인 경우와 마지막 record가 PASS이지만 그 digest가 current/verification과 다른 경우를 각각 포함해야 한다.
- **R4.2** fingerprint 집중 테스트는 untracked regular-file 및 top-level/nested regular-directory `chmod` 변경/복원, 모든 entry의 path/type/permission/payload frame 순서, mixed-kind sibling을 repository-relative byte path 하나로 lexicographic 정렬하고 directory 진입 시 frame한 뒤 depth-first로 이어지는 canonical stream, existing/broken symlink와 non-dereferenced/pruned symlink-directory, special-file 비읽기 및 반복 결정성을 검증해야 한다.
- **R4.3** 제품과 코드의 최소 지원 계약은 Python 3.12+로 유지해야 한다. 이번 작업의 실제 판정은 `/opt/homebrew/bin/python3.12 --version`이 출력한 정확한 `Python 3.12.14` interpreter로 기존 테스트와 신설 테스트를 포함한 전체 suite, runbook 보존 명령 및 수정 Python 파일을 읽는 `ast.parse` 문법 검사를 실행하며, evidence에는 resolved interpreter path `/opt/homebrew/bin/python3.12`와 version `Python 3.12.14`를 기록해야 한다.
- **R4.4** `transition --to COMPLETED` CLI에 actual workspace fingerprint의 mandatory equality gate를 새로 강제하는 것은 pure transition graph와 state schema를 보존하더라도 gate/state-machine 계약 변경이므로, `SKILL.md` frontmatter의 `version`을 정확히 `6.0.0`으로 올려야 한다. 이 bump와 함께 기존 `test_frontmatter_contract` expected map의 exact `version` 값을 `6.0.0`으로, 기존 `test_skill_version_is_major_bumped`의 major expectation을 `6`으로 in-place 갱신하는 것은 명시적 범위 안이며 두 test name을 보존한다. 별도 중복 version test는 추가하지 않는다. `assert_tests_preserved.py`는 test name만 비교하므로 이 두 assertion body 갱신은 AC-19/CMD-6의 기존 테스트 보존 계약을 만족한다. MAJOR `6.0.0`은 concurrent #85의 planned MINOR `5.2.0`을 integration에서 subsume하며 최종 combined version도 `6.0.0`이다.

## Acceptance criteria

- **AC-1** R1.1과 R1.2에 대해 임시 Git repository에서 verification과 마지막으로 기록된 PASS code review에 동일 fingerprint를 기록한 뒤 아무 변경 없이 completion CLI를 실행하면 종료 코드 0이고 저장된 stage가 정확히 `COMPLETED`이다. [실행](CMD-2)
- **AC-2** R1.1, R1.2, R1.3에 대해 verification과 PASS review 기록 후 tracked 파일 content를 변경하면 completion CLI가 종료 코드 3으로 거부되고 저장된 stage가 `COMPLETED`가 아니다. [실행](CMD-2)
- **AC-3** R1.1, R1.2, R1.3에 대해 verification과 PASS review 기록 후 content가 같은 untracked regular file을 `0644`에서 `0755`로 변경하면 completion CLI가 종료 코드 3으로 거부되고 저장된 stage가 `COMPLETED`가 아니다. [실행](CMD-2)
- **AC-4** R1.1, R1.2, R1.3에 대해 verification과 PASS review 기록 후 새 commit으로 Git `HEAD`를 변경하면 completion CLI가 종료 코드 3으로 거부되고 저장된 stage가 `COMPLETED`가 아니다. [실행](CMD-2)
- **AC-5** R1.2에 대해 fixture에 더 이른 PASS record가 존재하더라도 마지막으로 기록된 code review record가 REVISE이면 그 이전 PASS를 역탐색하지 않고 completion을 거부하며, 별도 fixture에서 마지막으로 기록된 record 자체가 PASS여도 그 `artifact_digest`가 current/verification fingerprint와 다르면 completion을 거부한다. [실행](CMD-2)
- **AC-6** R1.4에 대해 `transition(state, "COMPLETED")` 단위 테스트는 Git 실행과 fingerprint 함수가 호출되지 않음을 mock으로 증명하면서 기존 저장 digest 기반 guard의 성공·실패를 유지하고, state key set과 schema version 및 CLI parser 인자가 늘지 않았음을 검증한다. [실행](CMD-2)
- **AC-7** R1.3과 R1.5에 대해 mismatch는 종료 코드 3, missing/empty/non-string `state.project_root`는 `StateError`와 종료 코드 2, non-Git/no-commit/Git/filesystem fingerprint 실패는 종료 코드 4를 반환하며 모든 경우 completion 실행 전후 state 파일 bytes가 동일하고 stage가 `COMPLETED`가 아니다. [실행](CMD-2)
- **AC-8** R2.1에 대해 frame-spy 테스트는 untracked regular file, top-level regular directory, nested regular directory, symlink-directory, 그 밖의 symlink 및 special entry 각각에서 path, file type, permissions frame이 해당 content, directory marker, target 또는 special marker frame보다 먼저 한 번씩 입력됨을 검증한다. [실행](CMD-2)
- **AC-9** R2.1과 R2.4에 대해 임시 repository의 untracked regular file을 `0644 -> 0755 -> 0644`로 `chmod +x` 토글하면 중간 fingerprint가 원본과 다르고 복원 fingerprint는 원본과 정확히 같다. [실행](CMD-2)
- **AC-10** R2.2에 대해 existing symlink와 broken symlink 및 symlink-directory의 target 문자열 변경은 fingerprint를 바꾸고 어느 경우에도 target content를 읽거나 symlink-directory를 walk하지 않으며, special-file 테스트는 content read/open 또는 `readlink` 호출 없이 종료한다. [실행](CMD-2)
- **AC-11** R2.3과 R2.4에 대해 이름 순서와 kind 순서가 교차하는 nested regular directory, symlink-directory, regular file sibling fixture의 frame-spy 결과가 kind와 무관한 repository-relative byte path 단일 lexicographic 순서이며, 각 regular directory frame 직후 그 subtree를 depth-first로 방출하고 symlink-directory는 frame 뒤 prune함을 검증한다. untracked entry 생성 순서가 달라도 이 canonical stream과 fingerprint는 같고, 동일 repository의 반복 계산도 같으며 기존 tracked content/mode/HEAD 변화와 state-path 제외 테스트가 계속 통과한다. [실행](CMD-2)
- **AC-12** R3.1에 대해 `QualityGoalSkillContentTests.test_completion_current_workspace_exact_guarantee` 또는 의미가 동일한 명시적 content-contract test가 `## Completion integrity`가 `## Independent verification` 바로 앞에 정확히 한 번 존재함과 그 절의 다섯 요소인 재계산 시점, `state.project_root` 직접 측정, current/valid verification/마지막 `reviews.code[-1]` record 자체가 PASS인 code review digest의 삼자 일치 및 backward search 금지, 실패 시 non-completion, lock/generation 부재에 따른 측정 직후 동시 변경 비보장을 각각 독립 assertion으로 고정하고 실행 판정을 통과한다. [실행](CMD-2)
- **AC-13** R3.2에 대해 기존 state fixture를 migration 없이 로드하고 기존 transition graph, terminal states, parser의 기존 command/argument surface가 보존되며 새 key나 schema-version 증가가 없다. [실행](CMD-2)
- **AC-14** R4.1과 R4.2의 집중 회귀 클래스와 R3.1의 content-contract test가 모두 통과한다. [실행](CMD-2)
- **AC-15** R4.3에 대해 이번 검증 환경에서 `QG_PY`가 정확히 `/opt/homebrew/bin/python3.12`로 resolve되고 `--version`이 정확히 `Python 3.12.14`를 출력하며, 그 interpreter로 기존 테스트와 신설 테스트를 포함한 전체 suite가 종료 코드 0과 `OK`를 출력한다. 최종 evidence는 resolved path와 version 출력 및 suite 결과를 함께 기록한다. [실행](CMD-8 CMD-1)
- **AC-16** R4.3에 대해 `SKILL.md`가 500줄 미만이다. [실행](CMD-3)
- **AC-17** R3.1과 R4.3에 대해 `QG_BASE` rebase나 protected section 목록 축소 없이 새 non-protected 절을 추가한 뒤에도 모든 보호 절의 byte-identical 보존 검사가 통과한다. [실행](CMD-4)
- **AC-18** R4.3에 대해 이번 실제 검증 interpreter `/opt/homebrew/bin/python3.12`가 수정된 Python source와 test module을 읽어 각각 `ast.parse`하는 read-only 문법 검사를 통과한다. [실행](CMD-5)
- **AC-19** R4.3에 대해 기존 테스트 보존 검사가 통과한다. [실행](CMD-6)
- **AC-20** R2.1, R2.3, R2.4에 대해 child file을 가진 일반 nested untracked directory를 `0755 -> 0700 -> 0755`로 변경하면 중간 fingerprint가 원본과 다르고 복원 fingerprint는 원본과 정확히 같으며, 모든 계산에서 nested directory가 repository-relative byte path 순서상의 진입 지점에 frame되고 바로 이어지는 child entry frame을 포함한다. [실행](CMD-2)
- **AC-21** R4.4에 대해 기존 `QualityGoalSkillContentTests.test_frontmatter_contract`가 `SKILL.md` frontmatter의 exact `version` 값 `6.0.0`을 검증하고 기존 `test_skill_version_is_major_bumped`가 major `6`을 검증하며, 두 기존 test name을 그대로 유지한 채 함께 통과한다. 별도 중복 version test는 존재하지 않는다. [실행](CMD-2)

## Requirements traceability

This table maps every requirement to acceptance criteria and the judgement method that proves the mapping.

| Requirement | Acceptance criteria | Judgement method |
|---|---|---|
| R1.1 | AC-1, AC-2, AC-3, AC-4 | CMD-2 completion CLI integration tests |
| R1.2 | AC-1, AC-2, AC-3, AC-4, AC-5 | CMD-2 triple-equality and last-record-only tests |
| R1.3 | AC-2, AC-3, AC-4, AC-7 | CMD-2 mutation and persisted-state tests |
| R1.4 | AC-6, AC-13 | CMD-2 transition purity and compatibility tests |
| R1.5 | AC-7 | CMD-2 exit-code, StateError, and byte-identity tests |
| R2.1 | AC-8, AC-9, AC-20 | CMD-2 all-entry metadata framing and chmod tests |
| R2.2 | AC-10 | CMD-2 symlink-directory, symlink, and special-file safety tests |
| R2.3 | AC-8, AC-11, AC-20 | CMD-2 mixed-kind repository-relative byte-path order, enter-directory frame/depth-first walk, prune, and deterministic-repeat tests |
| R2.4 | AC-9, AC-11, AC-20 | CMD-2 regular-file/directory restoration and existing coverage tests |
| R3.1 | AC-12, AC-14, AC-17 | CMD-2 exact-guarantee placement/five-element/last-record assertions and CMD-4 protected-section byte identity |
| R3.2 | AC-13 | CMD-2 compatibility assertions |
| R4.1 | AC-5, AC-14, AC-15 | CMD-2 focused suite and CMD-1 full suite |
| R4.2 | AC-8, AC-9, AC-10, AC-11, AC-14, AC-20 | CMD-2 metadata, mixed-kind canonical stream, safe-prune focused suite and CMD-1 full suite |
| R4.3 | AC-15, AC-16, AC-17, AC-18, AC-19 | CMD-8 interpreter identity, CMD-1 full suite, CMD-3, CMD-4, CMD-5, CMD-6 |
| R4.4 | AC-21 | CMD-2 existing exact-frontmatter and major-bump assertions with preserved test names |

## Architecture

완료 경로는 세 책임으로 나눈다.

1. `compute_workspace_fingerprint(project_root)`는 Git과 filesystem을 읽는 어댑터다. 기존 Git `HEAD`, unstaged diff, staged diff, untracked tree 순서를 유지하고 #50-B metadata만 추가한다.
2. `transition(state, target, reason)`과 `_validate_transition_request`는 전달된 state만 검사·변경하는 순수 상태 계층이다. 기존 review/verification digest guard와 transition graph를 유지하며 Git/filesystem I/O를 수행하지 않는다.
3. CLI `transition --to COMPLETED` 분기는 loaded state의 non-empty string `project_root`를 검증하고 그 값으로 현재 fingerprint를 직접 계산한다. 현재 값, valid verification 값, 마지막으로 기록된 code review record 자체가 PASS인 digest를 대조한 후에만 순수 transition을 호출한다. `_mutating_result`의 atomic state save는 이 검사와 transition이 성공한 뒤 수행되며, 다른 transition target은 기존 경로를 그대로 사용한다.
4. `SKILL.md` 문서 어댑터는 non-protected top-level `## Completion integrity`를 `## Independent verification` 직전에 추가한다. 새 절이 exact completion CLI contract의 정본이며, 보호된 기존 절은 `QG_BASE`와 byte-identical하게 남는다. 새 절은 보호 문구 “last passing code review”를 마지막 `reviews.code[-1]` record 자체의 PASS로만 해석하고 backward search를 금지하는 엄격한 한정으로 함께 읽힌다.

untracked metadata의 canonical encoding은 모든 entry의 path를 먼저 length-frame하고, 해당 path의 `os.lstat` 결과에서 `stat.S_IFMT(st_mode)`를 6자리 ASCII octal, `stat.S_IMODE(st_mode)`를 4자리 ASCII octal로 표현하여 각각 기존 `_frame` 방식의 `lstat-type`, `lstat-permissions` label로 length-frame하는 것이다. 그 다음 entry 종류별 payload/marker를 frame한다. regular file은 기존 `file` content, top-level 및 nested regular directory는 `dir` marker, symlink와 symlink-directory는 `symlink` target, special file은 `special` empty marker를 사용한다. 각 directory의 immediate child는 kind별 bucket 없이 repository-relative byte path의 단일 lexicographic 순서로 선택한다. regular directory가 그 순서에서 선택되면 진입하면서 자신의 네 frame을 기록하고 그 subtree를 같은 규칙으로 depth-first 방출한 뒤 다음 sibling으로 진행한다. symlink-directory는 target을 역참조하지 않고 frame한 자리에서 prune한다. 모든 entry 종류 판정은 `lstat` 기준이며 symlink target의 종류·mode는 관찰하지 않는다.

이 구조는 top-level directory가 Git 출력에서 직접 발견되는지, nested regular directory가 재귀 walk에서 발견되는지, symlink-directory가 `dirnames`에서 분리되는지와 무관하게 각 entry에 같은 path/type/permissions/payload 계약을 적용한다. 새 state 필드, token, nonce, 필수 CLI 인자, schema version 또는 전역 RMW lock은 없다.

## Interfaces and data flow

입력 인터페이스는 기존 명령 `quality_state.py transition --state STATE --to COMPLETED` 그대로다. 별도의 current-fingerprint 인자나 검사 token은 없다.

데이터 흐름은 다음과 같다.

1. CLI가 state JSON을 읽되 아직 수정하거나 저장하지 않는다.
2. 현재 stage와 target이 completion 후보임을 확인하고 `state.project_root`가 non-empty string인지 검사한다. 부적합하면 `StateError`로 중단한다.
3. CLI가 검증된 `state.project_root`를 fingerprint 함수에 직접 전달한다.
4. fingerprint 함수가 Git `HEAD`, tracked diff 두 종류, 모든 untracked entry의 path/type/permissions/payload 또는 marker를 읽어 lowercase SHA-256 digest를 반환한다. 각 directory에서는 kind와 무관한 repository-relative byte path 단일 lexicographic 순서로 entry를 선택하고, regular directory는 진입 시 frame 후 subtree를 depth-first로 계속하며 symlink-directory는 frame 후 non-dereferenced 상태로 prune한다.
5. CLI completion guard가 기존 gate와 함께 `current == verification.workspace_fingerprint == reviews.code[-1].artifact_digest`를 검사하고, `reviews.code[-1]` 자체의 PASS verdict, 빈 blockers, 빈 open finding 목록, valid verification도 요구한다. 더 이른 PASS record는 조회하지 않는다.
6. 모든 검사가 성공하면 순수 transition이 stage와 timestamp를 변경하고 atomic save가 `COMPLETED`를 영속화한다. 실패하면 save를 호출하지 않는다.

Exact CLI guarantee는 다음과 같다: 완료 CLI는 state를 `COMPLETED`로 저장하기 직전에 `state.project_root`의 workspace fingerprint를 직접 다시 계산하며, 그 current 값과 valid verification fingerprint와 마지막으로 기록된 code review record 자체가 PASS인 `artifact_digest`가 모두 같고 기존 completion gate도 통과할 때만 완료를 저장한다. 재계산 또는 비교가 실패하면 완료를 저장하지 않는다. 이 보증은 재계산이 관찰한 시점의 snapshot에 한정되며, lock/generation이 없으므로 측정 직후 별도 프로세스가 만든 동시 변경까지 원자적으로 배제한다고 주장하지 않는다. 이 계약은 `SKILL.md`의 새 non-protected `## Completion integrity` 절에 그대로 수록하며, 바로 뒤 protected `## Independent verification`의 “last passing code review”는 오직 마지막 `reviews.code[-1]` 자체가 PASS인 경우만 뜻하고 이전 PASS 검색을 허용하지 않는다는 새 절의 한정과 함께 읽는다.

## Failure behavior

- 삼자 digest mismatch, 마지막 record의 non-PASS, invalid verification 또는 기존 completion gate 실패는 `TransitionError`로 처리해 CLI 종료 코드 3과 구체적인 stderr를 내고 state 파일을 저장하지 않는다.
- `state.project_root`가 missing, empty 또는 non-string이면 fingerprint 호출 전에 `StateError`로 처리해 종료 코드 2를 내고 state 파일을 저장하지 않아 실행 전후 byte identity를 보존한다.
- `project_root`가 유효한 문자열이지만 Git repository가 아니거나 commit이 없거나 Git 명령이 실패하면 기존 `GitError` 계약과 종료 코드 4를 유지한다.
- untracked entry의 `lstat`, regular-file read 또는 symlink `readlink`가 실패하면 경로를 포함한 `FilesystemError`, 종료 코드 4를 유지한다. special file은 payload를 읽지 않으므로 blocking read를 시도하지 않는다.
- 거부된 completion은 verification을 암묵적으로 invalidate하거나 stage를 demote하지 않는다. 모든 종료 코드 2/3/4 거부에서 영속 state bytes를 보존해 사용자가 원인을 진단할 수 있게 한다.
- 회복 절차는 workspace를 review된 상태로 복원하거나, 현재 workspace fingerprint에서 verification과 code review를 다시 실행한 뒤 completion을 재시도하는 것이다. fingerprint 규칙 변경으로 기존 저장값이 달라진 경우에도 같은 절차를 사용한다. canonical traversal 구현이 mixed-kind repository-relative byte-path 순서, enter-directory frame/depth-first walk 또는 symlink-directory prune 계약을 어기면 호환 가능한 대체 digest로 간주하지 않고 테스트 실패로 처리한다.
- 자동 retry는 없다. 동일한 stale evidence 또는 더 이른 PASS record를 반복 제출해 완료되는 경로도 없다.

## Security and risk

fingerprint는 로컬 무결성 비교값이지 서명이나 인증 token이 아니다. `state.project_root`, Git output, 파일명, mode, content, symlink target은 신뢰하지 않는 입력으로 취급하고 length framing으로 연결 모호성을 막는다. symlink는 `lstat`와 `readlink`만 사용해 repository 밖 target을 읽지 않는다. FIFO/socket/device는 payload를 열지 않아 block, device side effect, 권한 상승 표면을 피한다.

주요 잔여 위험은 fingerprint 계산과 atomic state save 사이의 TOCTOU다. lock/generation이 명시적 범위 밖이므로 새 `SKILL.md` `## Completion integrity` 정본과 content contract에서 이 한계를 공개하고, 테스트는 측정 전에 발생한 변화를 반드시 거부하는 데 초점을 둔다. 기존 protected “last passing code review” 문구를 단독으로 읽어 backward search로 오해할 위험은 새 절의 `reviews.code[-1]` PASS-only 한정과 정확한 인접 배치 assertion으로 통제한다. mode 표현은 permission bits만 포함하며 uid/gid, timestamps, ACL, xattr는 이 범위의 fingerprint 입력이 아니다. 기존 fingerprint와의 값 호환성은 untracked entry가 있는 경우 의도적으로 깨질 수 있으나 state schema 호환성은 유지한다.

## Test strategy

제품과 코드의 지원 계약은 Python 3.12+다. 이번 작업의 실제 검증에 한해 실행 전에 `QG_PY=/opt/homebrew/bin/python3.12`, `QG_BASE=6d60011cbdaead7946b191d3f12029eef5c141c8`로 설정한다. `command -v "$QG_PY"`가 `/opt/homebrew/bin/python3.12`, `"$QG_PY" --version`이 `Python 3.12.14`를 출력하는지 확인하고 최종 evidence에 두 출력과 각 판정 명령의 exit code를 기록한다. 이는 해당 exact interpreter에서의 검증이며 다른 platform에 그 절대 경로가 존재한다는 주장이 아니다.

아래 판정 명령 표는 이 작업의 로컬 정본이다. `CMD-2`와 `CMD-5`만 이 작업에서 `docs/quality-goal-maintenance.md`의 동명 정본 항목을 명시적으로 재정의하고 override한다. `CMD-1`, `CMD-3`, `CMD-4`, `CMD-6`은 위 환경 변수 바인딩 아래에서 maintenance runbook 정본의 동명 명령과 통과 조건을 그대로 사용한다. `CMD-8`은 canonical runbook 표가 `CMD-7`에서 끝나므로 그 표에는 존재하지 않는 새 task-local ID이며, 이번 검증 환경의 interpreter identity를 고정한다. canonical `CMD-7`은 unsupported pre-3.12 rejection contract를 검증하지만 이 작업은 supported/tested Python 3.12.14 binding을 판정하므로 의도적으로 범위 밖이다.

### 판정 명령 표

| ID | 명령 | 통과 조건 |
|---|---|---|
| CMD-1 | `"$QG_PY" dot_claude/skills/quality-goal/tests/assert_python_version.py && PYTHONDONTWRITEBYTECODE=1 "$QG_PY" -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_*.py'` | 종료 코드 0, `OK` |
| CMD-2 | `"$QG_PY" dot_claude/skills/quality-goal/tests/assert_python_version.py && PYTHONDONTWRITEBYTECODE=1 "$QG_PY" dot_claude/skills/quality-goal/tests/test_quality_state.py CompletionIntegrityCLITests FingerprintMetadataTests TransitionPurityTests && PYTHONDONTWRITEBYTECODE=1 "$QG_PY" -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_content_contracts.py' -k test_completion_current_workspace_exact_guarantee -k test_frontmatter_contract -k test_skill_version_is_major_bumped` | 종료 코드 0, 세 집중 회귀 클래스와 exact-guarantee 및 두 기존 version contract test 전체 `OK` |
| CMD-3 | `wc -l < dot_claude/skills/quality-goal/SKILL.md` | 500 미만 |
| CMD-4 | `"$QG_PY" dot_claude/skills/quality-goal/tests/assert_preserved_sections.py "$QG_BASE"` | 종료 코드 0, `보존 대상 절 불변` |
| CMD-5 | `"$QG_PY" -c 'import ast, pathlib; paths = ("dot_claude/skills/quality-goal/scripts/quality_state.py", "dot_claude/skills/quality-goal/tests/test_quality_state.py", "dot_claude/skills/quality-goal/tests/test_content_contracts.py"); [ast.parse(pathlib.Path(path).read_text(encoding="utf-8"), filename=path) for path in paths]'` | 종료 코드 0, 세 파일 모두 syntax error가 없고 bytecode 또는 repository-local `__pycache__` 생성 없음 |
| CMD-6 | `"$QG_PY" dot_claude/skills/quality-goal/tests/assert_tests_preserved.py "$QG_BASE"` | 종료 코드 0, `기존 테스트 보존` |
| CMD-8 | `resolved=$(command -v "$QG_PY") && version=$("$QG_PY" --version 2>&1) && test "$resolved" = /opt/homebrew/bin/python3.12 && test "$version" = 'Python 3.12.14' && printf '%s\n%s\n' "$resolved" "$version"` | 종료 코드 0, `/opt/homebrew/bin/python3.12`와 `Python 3.12.14`를 차례로 출력 |

집중 테스트는 새 `CompletionIntegrityCLITests`, `FingerprintMetadataTests`, `TransitionPurityTests` 클래스와 `QualityGoalSkillContentTests.test_completion_current_workspace_exact_guarantee`로 구성한다. 모든 filesystem 시나리오는 임시 directory와 임시 Git repository만 사용하고 전역 Git 설정이나 실제 사용자 repository를 변경하지 않는다. completion-ready fixture는 더 이른 PASS 뒤 마지막 REVISE인 history와 마지막 PASS digest mismatch history를 별도로 만들며, completion logic이 `reviews.code[-1]`만 읽고 이전 PASS를 back-search하지 않음을 spy 또는 결과 assertion으로 고정한다. 거부 case는 exit code, error class, state file byte identity와 non-completed stage를 함께 assert한다.

metadata test는 regular file과 top-level/nested regular directory permissions를 원복한 뒤 최초 digest로 복구되는 metamorphic assertion을 사용한다. frame ordering은 digest 최종값에만 의존하지 않고 `_frame` 호출 순서를 관찰해 모든 entry에서 path/type/permissions가 payload/marker보다 먼저임을 증명한다. 이름과 kind 순서가 교차하는 nested regular directory, symlink-directory, regular file sibling을 만들어 repository-relative byte path 하나의 lexicographic 순서, directory 진입 frame 직후의 depth-first child stream, symlink-directory frame 뒤 prune를 정확한 expected sequence로 검증한다. symlink fixture는 file target, 없는 target, directory target을 포함하며 target content read와 symlink-directory walk를 spy로 금지한다. special-file 검증은 지원 platform에서는 FIFO를 사용하고, platform 차이가 있는 kind는 `lstat`/reader mock으로 payload 비읽기 계약을 결정적으로 검증한다.

exact-guarantee content-contract test는 새 non-protected top-level `## Completion integrity`의 단일 존재와 `## Independent verification` 바로 앞 배치를 검사하고, 하나의 포괄적 substring 대신 R3.1의 다섯 요소와 protected “last passing code review”의 `reviews.code[-1]` PASS-only/no-backward-search 한정을 독립 assertion 또는 명명된 pattern으로 확인한다. 모든 protected 절은 `QG_BASE`와 byte-identical하게 남고 CMD-4가 이를 판정하며, `QG_BASE` rebase나 protected list 축소는 허용하지 않는다. version 검증은 별도 중복 test를 추가하지 않고 기존 `test_frontmatter_contract` expected version을 exact `6.0.0`으로, 기존 `test_skill_version_is_major_bumped` expectation을 major `6`으로 in-place 갱신한다. test name이 보존되므로 CMD-6을 만족하며 CMD-2는 exact-guarantee test와 이 두 기존 test를 함께 선택한다. CMD-1은 신설 테스트뿐 아니라 기존 suite 전체의 회귀를 검증한다. CMD-5는 세 수정 Python 파일을 읽어 `ast.parse`하여 import나 bytecode 생성 없이 syntax 유효성을 확인한다.

## Decisions

### D1. CLI adapter에서 pre-save 재계산과 비교 수행 — 채택

완료 target일 때만 CLI orchestration이 state의 `project_root`를 직접 측정하고 삼자 일치를 검사한 뒤 순수 transition과 save를 호출한다. 이는 current fingerprint를 caller가 주입할 수 없게 하고, Git I/O를 상태 머신에서 격리하며, 기존 command surface와 state schema를 보존한다.

### D2. 순수 transition에 current fingerprint 인자 전달 — 기각

`transition`에 선택적 fingerprint 인자를 더하면 함수 자체는 I/O 없이 유지할 수 있지만 기존 interface가 넓어지고, CLI 외 caller가 오래되거나 조작된 값을 공급할 수 있으며 새 검사 token과 유사한 우회 표면이 생긴다. 새 인자 금지와 직접 재계산 요구에 맞지 않는다.

### D3. transition 내부에서 Git fingerprint 계산 — 기각

상태 전이가 `state.project_root`를 읽게 하면 호출 지점은 단순하지만 단위 테스트의 결정성이 떨어지고 순수 transition에 Git I/O를 넣지 말라는 경계를 위반한다.

### D4. untracked metadata canonicalization — 채택

platform의 native integer bytes나 `repr` 대신 `S_IFMT` 6자리 octal과 `S_IMODE` 4자리 octal의 ASCII를 length-frame한다. 모든 entry에 path/type/permissions/payload 또는 marker 순서를 적용한다. 각 directory의 mixed-kind child를 repository-relative byte path 하나로 lexicographic 정렬하고, regular directory는 그 순서에서 진입하며 marker 뒤 subtree를 depth-first로 계속하고 symlink-directory는 frame 후 prune한다. 값의 경계와 표현이 명시적이며 fingerprint format version은 추가하지 않는다.

<!-- strict-only:start -->

This block is required only for strict work. Any inapplicable subsection must be removed for non-strict work; within strict work, mark it as not applicable with a reason before review.

### Threat and trust boundaries

신뢰 경계 안에는 현재 프로세스의 비교 로직, SHA-256 구현, 성공적으로 atomic-replace된 state 파일만 둔다. operator가 선택한 state 파일, 그 안의 `project_root`, Git repository 상태, untracked 경로와 metadata/content, symlink target, verification/review JSON은 경계 밖 입력이다. 로컬에서 state 자체를 쓸 수 있는 적대자는 digest도 바꿀 수 있으므로 이 기능은 그 공격자를 막는 인증 수단이 아니다.

통제는 CLI가 caller-supplied current digest를 받지 않는 것, state의 root를 직접 측정하는 것, 마지막 record만 사용하는 세 digest의 정확한 동등성, 모든 entry의 length framing, symlink 비역참조, special-file 비읽기, 오류 시 no-save다. repository 밖으로 향하는 symlink는 target 문자열만 관찰한다. malformed `project_root`와 Git/filesystem read 실패는 각각 명시된 오류 분류로 fail closed 한다.

### Authorization and tenant isolation

해당 없음. 이 CLI는 로컬 단일-user state/repository 도구이며 tenant, 원격 principal 또는 권한 부여 API가 없다. 이번 변경은 권한 모델을 추가하지 않는다. 격리 검증 대신 CLI는 state에 기록된 정확한 `project_root` 하나만 fingerprint하고 symlink target을 따라 다른 filesystem 영역을 읽지 않는 경계 테스트를 수행한다.

### Migration, compatibility, and rollback

state schema/version, command 이름, 인자, transition graph에는 migration이나 backfill이 없다. #50-B로 untracked entry가 있는 workspace의 fingerprint 값은 바뀔 수 있다. 저장 verification/review digest를 자동 재작성하지 않고 completion을 거부하여, 사용자가 새 알고리즘으로 verification과 code review를 다시 수행하게 한다. 이는 오래된 증거를 새 값으로 승격하지 않는 fail-closed 호환 정책이다.

문서 migration은 기존 보호 절을 수정하지 않고 non-protected top-level `## Completion integrity`를 `SKILL.md`의 `## Independent verification` 바로 앞에 정확히 한 번 삽입하는 additive 방식이다. 새 절은 authoritative exact completion CLI contract의 다섯 요소를 담고, 바로 뒤 protected 절의 “last passing code review”가 최종 `reviews.code[-1]` record 자체의 PASS만 뜻하며 backward search를 결코 허용하지 않는다고 명시한다. old protected prose는 이 stricter clarification과 함께 읽되 `QG_BASE`와 byte-identical하게 유지한다. `QG_BASE` rebase와 protected section list 축소는 migration 또는 rollback 수단이 아니다.

저장소 SemVer 정책에서 gate 규칙이나 state machine 계약 변경은 MAJOR이다. 이 작업은 pure transition graph와 state schema는 보존하지만 completion CLI에 actual workspace fingerprint의 mandatory equality gate를 신설하므로 최종 `SKILL.md` frontmatter version은 `6.0.0`이다. 이에 맞춰 기존 `test_frontmatter_contract` exact version과 기존 `test_skill_version_is_major_bumped` major expectation만 assertion body에서 in-place 갱신하고 test name은 유지한다. 별도 MINOR 변경인 concurrent #85의 planned `5.2.0`은 integration에서 이 MAJOR에 subsume되며 final combined version은 `5.2.0`이 아니라 `6.0.0`이다. 양쪽이 같은 frontmatter line을 중복 변경하지 않도록 통합 충돌을 한 번만 `6.0.0`으로 해소해야 한다. #85 기능 자체는 이 작업 범위에 포함하지 않는다.

rollback trigger는 전체 suite/보존 검사 실패, unchanged completion 회귀, mutation completion 허용, mixed-kind canonical order 또는 nested directory 진입 frame 누락, symlink target 역참조/prune 실패, special-file read 또는 정상 repository에서의 비결정 fingerprint다. rollback은 completion CLI orchestration과 metadata framing 변경을 함께 이전 구현으로 되돌리고 새 non-protected 문서 보증과 그 content assertion 및 version assertion body 갱신도 이전 동작에 맞게 되돌리는 것이다. 보호 절, `QG_BASE`, protected list는 rollback 전후 모두 건드리지 않는다. 새 schema/data migration이 없으므로 state 파일 복구 작업은 필요 없다. rollback 뒤 이미 새 fingerprint로 기록된 in-progress state는 verification/review를 다시 수행해야 하며 자동 digest 변환은 하지 않는다.

### Failure recovery and observability

사용자 관찰 신호는 CLI exit code와 stderr, 그리고 변경되지 않은 state stage/bytes다. malformed `project_root`는 종료 코드 2, digest/gate mismatch는 종료 코드 3, Git/filesystem 측정 실패는 종료 코드 4로 구분한다. 오류 메시지는 completion에 필요한 삼자 일치 실패인지 state 입력 오류인지 repository 측정 실패인지 식별할 수 있어야 하지만 fingerprint 원문 외 민감한 file content를 출력하지 않는다.

상시 service가 아니므로 alert, metric, distributed trace는 해당 없음이다. 회복은 stderr 원인을 확인하고 malformed state를 올바른 workflow state로 복구하거나 workspace 복원 또는 verification/review 재실행 후 수동 재시도한다. 테스트 실패 시 배포를 중단하고 rollback 조건을 평가한다.

### High-risk end-to-end verification

고위험 경로는 오래된 증거로 terminal completion을 영속화하는 경로다. CMD-2에서 실제 CLI와 임시 Git repository/state file을 사용해 unchanged 성공, verification 뒤 tracked content 변경, untracked `chmod +x` 변경, empty commit에 의한 HEAD 변경, 마지막 REVISE 앞의 이전 PASS, 마지막 PASS digest mismatch, malformed `project_root`, Git 측정 실패를 각각 실행한다. 모든 거부 case는 지정된 nonzero exit, state byte identity, non-completed stage를 동시에 요구한다.

fingerprint 경로는 regular file과 top-level/nested regular directory의 permissions 변경/복원, 모든 entry의 path/type/permissions/payload 순서, mixed-kind repository-relative byte-path 단일 lexicographic 순서, directory 진입 frame 뒤 depth-first child walk, existing/broken symlink와 non-dereferenced/pruned symlink-directory, special-file 비읽기 및 반복 결정성을 함께 검증한다. exact-guarantee content test는 새 절의 위치, 다섯 문서 요소 및 protected 문구의 last-record-only 해석을 독립적으로 고정하고, CMD-4는 보호 절 byte identity를 별도로 고정한다.

CMD-2의 어느 case라도 완료를 잘못 저장하거나 nested directory를 누락하거나 hang/read side effect가 발생하면 즉시 중단 조건이다. 그 다음 CMD-8, read-only `ast.parse` 검사인 CMD-5, CMD-1, CMD-3, CMD-4, CMD-6 순서로 검증하고 하나라도 실패하면 완료 또는 배포를 주장하지 않는다. 최종 evidence에는 `QG_PY`의 resolved path와 `Python 3.12.14` version, 각 명령, exit code, 전체 test count와 `OK`/보존 메시지를 기록한다.

### No production mutation confirmation

자동 검증 중 filesystem 변경은 임시 directory의 임시 Git repository와 fixture state에만 발생한다. CMD-5는 세 repository Python 파일을 읽어 `ast.parse`만 수행하며 bytecode나 repository-local `__pycache__`를 생성하지 않는다. 실제 사용자 repository, 배포된 home directory, 원격 Git, production state 또는 외부 service를 mutate하지 않는다. `chezmoi apply`, commit, push, checkout, reset, clean, release, migration은 이 Spec의 자동 workflow에 포함되지 않는다.

<!-- strict-only:end -->
