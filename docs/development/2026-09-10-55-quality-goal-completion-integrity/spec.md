# Quality Goal Specification

- Task ID: 20260910T120000Z-55-completion-integrity
- Mode: strict
- Status: SPEC_REVIEW
- Created: 2026-09-10
- Updated: 2026-09-10
- Source goal: #55 완료 시점 실제 워크스페이스 fingerprint 재검증 및 #50-B untracked mode/type fingerprint 반영

## Problem and context

현재 `quality_state.py`의 순수 상태 전이 함수는 `CODE_REVIEW`에서 `COMPLETED`로 갈 때 저장된 verification fingerprint와 마지막 code review의 `artifact_digest`가 같은지만 확인한다. verification과 review가 끝난 뒤 워크스페이스의 tracked content, executable mode 또는 Git `HEAD`가 바뀌어도 완료 CLI는 실제 워크스페이스를 다시 관찰하지 않으므로 오래된 증거로 완료를 저장할 수 있다. 이는 완료 상태가 현재 코드 상태를 보증한다는 사용자의 기대를 위반한다.

현재 workspace fingerprint는 Git `HEAD`, tracked unstaged/staged diff, 정렬된 untracked 경로와 untracked regular-file content 또는 symlink target을 해시한다. 그러나 untracked entry의 `lstat` file type과 permission bits를 해시하지 않아 content가 같은 untracked 파일의 `chmod` 변화와 일부 종류 변화가 fingerprint에 반영되지 않는다. 반면 existing/broken symlink는 target을 역참조하지 않고 `readlink` 결과를 해시하며, special file은 content를 읽지 않는 안전 속성을 유지해야 한다.

이 작업의 무결성 경계는 완료 CLI가 state에 기록된 `project_root`를 다시 측정하는 시점이다. 상태 머신의 순수 전이 규칙과 CLI의 Git/filesystem 어댑터 책임을 분리하고, 기존 state schema를 늘리지 않으면서 측정값·verification·review의 삼자 일치를 강제한다.

## Goals

- 완료 CLI가 완료 state 저장 직전에 `state.project_root`의 현재 workspace fingerprint를 직접 재계산한다.
- 현재 fingerprint, 유효한 verification fingerprint, 마지막 최종 PASS code review digest가 모두 같고 기존 completion gate도 통과할 때만 `COMPLETED`를 저장한다.
- untracked entry의 `lstat` 종류와 permissions를 payload보다 먼저 fingerprint에 반영해 mode/type 변화를 탐지한다.
- deterministic ordering, existing/broken symlink 비역참조, special-file 비읽기, 기존 state/CLI 호환성을 보존한다.
- Python 3.12+ 전체 기준 suite와 집중 회귀 테스트, 보존 runbook, 문법 검사를 통과하고 사용자-facing exact guarantee를 문서화한다.

## Non-goals

- #50-A의 state read-modify-write 동시성 제어, #50-C의 `required_sections` 권위 목록, #50-D의 `__pycache__` runbook 보강, #50-E의 세션 scratch 경로 규칙은 포함하지 않는다.
- #49, #85의 요구사항은 포함하지 않는다.
- completion과 workspace 변경을 하나의 원자적 임계 구역으로 묶는 lock, generation counter, lease 또는 동시성 프로토콜을 추가하지 않는다.
- 새 검사 토큰, completion nonce, CLI의 새 필수 인자, state field 또는 state schema version을 추가하지 않는다.
- Git diff 구성, `.claude/quality-state` 제외 규칙, verification 생성 절차, code-review 라운드 정책 또는 transition graph를 변경하지 않는다.
- fingerprint를 보안 서명이나 적대적 로컬 관리자에 대한 변조 방지 수단으로 확장하지 않는다.
- completion integrity와 #50-B에 필요하지 않은 리팩터링, 테스트 이름 정리 또는 문서 개편을 수행하지 않는다.

## Requirements

- **R1.1** 완료 CLI의 기존 `transition --state <path> --to COMPLETED` 경로는 새 인자를 받지 않고 state를 로드한 뒤 `state.project_root`를 입력으로 `compute_workspace_fingerprint`를 호출하며, 완료 state를 저장하기 직전에 얻은 현재 fingerprint를 사용해야 한다.
- **R1.2** completion은 기존 completion gate에 더해 현재 fingerprint, `verification.workspace_fingerprint`, 마지막으로 기록된 code review record의 PASS `artifact_digest`가 동일한 유효한 lowercase SHA-256 값일 때만 허용해야 한다. 마지막 record 자체가 PASS가 아니면 이전 PASS를 역탐색해 사용해서는 안 된다.
- **R1.3** verification 이후 tracked content, untracked executable mode 또는 Git `HEAD`가 바뀌거나 세 값 중 하나라도 다르면 completion CLI는 완료를 거부하고 state 파일을 `COMPLETED`로 저장하지 않아야 한다.
- **R1.4** 순수 `transition(state, target, reason)`과 그 상태 기반 guard에는 Git/filesystem I/O를 넣지 않아야 한다. 현재 fingerprint 재계산과 삼자 일치의 CLI-only 검사는 state 저장 어댑터 경계에 두며 검사 토큰이나 새 state schema를 도입하지 않아야 한다.
- **R1.5** fingerprint 계산이 non-Git, no-commit, unreadable entry 또는 기타 Git/filesystem 오류로 실패하면 기존 오류 분류를 유지하고, mismatch를 포함한 모든 completion 거부에서 영속 state는 완료 전 값으로 보존되어야 한다.
- **R2.1** fingerprint에 포함되는 모든 untracked filesystem entry는 `os.lstat`에서 얻은 `stat.S_IFMT(st_mode)` file type과 `stat.S_IMODE(st_mode)` permissions를 길이 프레이밍된 고정 ASCII 표현으로 해시해야 한다. 두 metadata frame은 regular-file content, symlink target 또는 special-file marker보다 먼저 들어가야 한다.
- **R2.2** untracked regular file은 metadata 다음에 기존 content bytes를 읽어 해시하고, existing/broken symlink와 directory symlink는 metadata 다음에 `os.readlink`의 target bytes만 해시하며 target을 역참조하지 않아야 한다. FIFO, socket, character/block device와 기타 special file은 종류·permissions와 marker만 해시하고 content open/read 또는 `readlink`를 호출하지 않아야 한다.
- **R2.3** top-level untracked paths, 재귀 directory entries, symlink-directory entries 모두 기존의 deterministic path sorting과 length framing을 유지해야 하며, 동일한 filesystem/Git 상태의 반복 계산은 같은 fingerprint를 반환해야 한다.
- **R2.4** untracked entry의 permissions만 변경하면 fingerprint가 달라지고 원래 permissions로 복원하면 fingerprint도 원래 값으로 복구되어야 한다. metadata 추가가 기존 tracked content/mode/HEAD 탐지와 `.claude/quality-state` 제외를 약화해서는 안 된다.
- **R3.1** `SKILL.md`는 completion CLI의 exact guarantee를 명시해야 한다. 문구는 재계산 시점, `state.project_root` 직접 측정, 현재·verification·마지막 최종 PASS review digest의 삼자 일치, 실패 시 non-completion, 그리고 lock/generation 부재에 따른 측정 직후 동시 변경 비보장까지 포함해야 한다.
- **R3.2** 기존 CLI 명령과 인자, transition graph, state schema/version은 호환되어야 한다. 새 fingerprint 규칙 때문에 기존 저장 fingerprint가 현재 값과 달라진 경우에는 자동 변환하지 않고 현재 workspace에서 verification과 code review를 다시 수행해야 한다.
- **R4.1** 임시 Git repository 기반 테스트는 unchanged completion 성공과 verification 이후 tracked content, untracked executable mode, Git `HEAD` 각각의 변경에 대한 completion 거부를 검증하고, 각 거부 뒤 영속 stage가 `COMPLETED`가 아님을 검증해야 한다.
- **R4.2** fingerprint 집중 테스트는 untracked `chmod` 변경/복원, type/permission frame 순서, existing/broken symlink, special-file 비읽기, deterministic sorting을 검증해야 한다.
- **R4.3** Python 3.12+에서 기존 테스트와 신설 테스트를 포함한 전체 suite, runbook의 보존 명령 CMD-3, CMD-4, CMD-6, 그리고 수정 Python 파일을 읽어 수행하는 `ast.parse` 문법 검사를 모두 통과해야 한다.

## Acceptance criteria

- **AC-1** R1.1과 R1.2에 대해 임시 Git repository에서 verification과 마지막 code review에 동일 fingerprint를 기록한 뒤 아무 변경 없이 completion CLI를 실행하면 종료 코드 0이고 저장된 stage가 정확히 `COMPLETED`이다. [실행](CMD-2)
- **AC-2** R1.1, R1.2, R1.3에 대해 verification과 PASS review 기록 후 tracked 파일 content를 변경하면 completion CLI가 종료 코드 3으로 거부되고 저장된 stage가 `COMPLETED`가 아니다. [실행](CMD-2)
- **AC-3** R1.1, R1.2, R1.3에 대해 verification과 PASS review 기록 후 content가 같은 untracked regular file을 `0644`에서 `0755`로 변경하면 completion CLI가 종료 코드 3으로 거부되고 저장된 stage가 `COMPLETED`가 아니다. [실행](CMD-2)
- **AC-4** R1.1, R1.2, R1.3에 대해 verification과 PASS review 기록 후 새 commit으로 Git `HEAD`를 변경하면 completion CLI가 종료 코드 3으로 거부되고 저장된 stage가 `COMPLETED`가 아니다. [실행](CMD-2)
- **AC-5** R1.2에 대해 마지막 code review record가 PASS가 아니거나, 마지막 PASS record의 digest와 verification/current fingerprint 중 하나가 다르면 이전 PASS record가 있어도 completion은 거부된다. [실행](CMD-2)
- **AC-6** R1.4에 대해 `transition(state, "COMPLETED")` 단위 테스트는 Git 실행과 fingerprint 함수가 호출되지 않음을 mock으로 증명하면서 기존 저장 digest 기반 guard의 성공·실패를 유지하고, state key set과 schema version 및 CLI parser 인자가 늘지 않았음을 검증한다. [실행](CMD-2)
- **AC-7** R1.3과 R1.5에 대해 mismatch는 종료 코드 3, Git/filesystem fingerprint 실패는 종료 코드 4를 반환하며 두 경우 모두 completion 실행 전후 state 파일 bytes가 동일하고 stage가 `COMPLETED`가 아니다. [실행](CMD-2)
- **AC-8** R2.1에 대해 frame-spy 테스트는 untracked regular file, directory, symlink, special entry 각각에서 file type과 permissions frame이 해당 content, target 또는 marker frame보다 먼저 입력됨을 검증한다. [실행](CMD-2)
- **AC-9** R2.1과 R2.4에 대해 임시 repository의 untracked regular file을 `0644 -> 0755 -> 0644`로 `chmod +x` 토글하면 중간 fingerprint가 원본과 다르고 복원 fingerprint는 원본과 정확히 같다. [실행](CMD-2)
- **AC-10** R2.2에 대해 existing symlink와 broken symlink의 target 문자열 변경은 fingerprint를 바꾸고 어느 경우에도 target content를 읽지 않으며, special-file 테스트는 content read/open 또는 `readlink` 호출 없이 종료한다. [실행](CMD-2)
- **AC-11** R2.3과 R2.4에 대해 untracked entry 생성 순서가 달라도 정렬된 동일 tree는 같은 fingerprint를 만들고, 동일 repository의 반복 계산도 같은 fingerprint를 만들며 기존 tracked content/mode/HEAD 변화와 state-path 제외 테스트가 계속 통과한다. [실행](CMD-2)
- **AC-12** R3.1의 exact guarantee가 재계산 시점, `state.project_root`, 삼자 일치, non-completion failure, 동시 변경 비보장을 빠짐없이 단정형으로 기술하고 구현 동작과 일치한다. [문서] dot_claude/skills/quality-goal/SKILL.md
- **AC-13** R3.2에 대해 기존 state fixture를 migration 없이 로드하고 기존 transition graph, terminal states, parser의 기존 command/argument surface가 보존되며 새 key나 schema-version 증가가 없다. [실행](CMD-2)
- **AC-14** R4.1과 R4.2의 집중 회귀 클래스가 모두 통과한다. [실행](CMD-2)
- **AC-15** R4.3에 대해 Python 3.12+에서 기존 테스트를 보존하면서 신설 테스트를 포함한 전체 suite가 모두 실행되고 종료 코드 0과 `OK`를 출력한다. [실행](CMD-1)
- **AC-16** R4.3에 대해 `SKILL.md`가 500줄 미만이다. [실행](CMD-3)
- **AC-17** R4.3에 대해 보존 대상 절 검사가 통과한다. [실행](CMD-4)
- **AC-18** R4.3에 대해 `/opt/homebrew/bin/python3.12`가 수정된 Python source와 test module을 읽어 각각 `ast.parse`하는 read-only 문법 검사를 통과한다. [실행](CMD-5)
- **AC-19** R4.3에 대해 기존 테스트 보존 검사가 통과한다. [실행](CMD-6)

## Requirements traceability

This table maps every requirement to acceptance criteria and the judgement method that proves the mapping.

| Requirement | Acceptance criteria | Judgement method |
|---|---|---|
| R1.1 | AC-1, AC-2, AC-3, AC-4 | CMD-2 completion CLI integration tests |
| R1.2 | AC-1, AC-2, AC-3, AC-4, AC-5 | CMD-2 triple-equality and final-review tests |
| R1.3 | AC-2, AC-3, AC-4, AC-7 | CMD-2 mutation and persisted-state tests |
| R1.4 | AC-6, AC-13 | CMD-2 transition purity and compatibility tests |
| R1.5 | AC-7 | CMD-2 exit-code and byte-identity tests |
| R2.1 | AC-8, AC-9 | CMD-2 metadata framing and chmod tests |
| R2.2 | AC-10 | CMD-2 symlink and special-file safety tests |
| R2.3 | AC-11 | CMD-2 ordering and deterministic-repeat tests |
| R2.4 | AC-9, AC-11 | CMD-2 restoration and existing coverage tests |
| R3.1 | AC-12 | dot_claude/skills/quality-goal/SKILL.md exact-guarantee review |
| R3.2 | AC-13 | CMD-2 compatibility assertions |
| R4.1 | AC-14, AC-15 | CMD-2 focused suite and CMD-1 full suite |
| R4.2 | AC-14, AC-15 | CMD-2 focused suite and CMD-1 full suite |
| R4.3 | AC-15, AC-16, AC-17, AC-18, AC-19 | CMD-1, CMD-3, CMD-4, CMD-5, CMD-6 |

## Architecture

완료 경로는 세 책임으로 나눈다.

1. `compute_workspace_fingerprint(project_root)`는 Git과 filesystem을 읽는 어댑터다. 기존 Git `HEAD`, unstaged diff, staged diff, untracked tree 순서를 유지하고 #50-B metadata만 추가한다.
2. `transition(state, target, reason)`과 `_validate_transition_request`는 전달된 state만 검사·변경하는 순수 상태 계층이다. 기존 review/verification digest guard와 transition graph를 유지한다.
3. CLI `transition --to COMPLETED` 분기는 loaded state의 `project_root`로 현재 fingerprint를 직접 계산하고, 이를 저장된 verification fingerprint와 마지막 최종 PASS code review digest에 대조한 후에만 순수 transition을 호출한다. `_mutating_result`의 atomic state save는 이 검사와 transition이 성공한 뒤 수행된다. 다른 transition target은 기존 경로를 그대로 사용한다.

untracked metadata의 canonical encoding은 각 entry의 `os.lstat` 결과에서 `stat.S_IFMT(st_mode)`를 6자리 ASCII octal, `stat.S_IMODE(st_mode)`를 4자리 ASCII octal로 표현하고 각각 기존 `_frame` 방식의 `lstat-type`, `lstat-permissions` label로 해시하는 것이다. path frame 뒤, payload frame 앞이라는 순서는 고정한다. regular file은 그 뒤 기존 `file` content frame, symlink는 기존 `symlink` target frame, directory는 directory marker 뒤 정렬된 children, special file은 기존 `special` empty marker만 뒤따른다. 모든 entry 종류 판정은 `lstat` 기준이며 symlink target의 종류·mode는 관찰하지 않는다.

## Interfaces and data flow

입력 인터페이스는 기존 명령 `quality_state.py transition --state STATE --to COMPLETED` 그대로다. 별도의 current-fingerprint 인자나 검사 토큰은 없다.

데이터 흐름은 다음과 같다.

1. CLI가 state JSON을 읽되 아직 수정하거나 저장하지 않는다.
2. 현재 stage와 target이 completion 후보임을 확인하고 state의 non-empty `project_root`를 fingerprint 함수에 직접 전달한다.
3. fingerprint 함수가 Git `HEAD`, tracked diff 두 종류, 정렬된 untracked entry의 path/type/permissions/payload를 읽어 lowercase SHA-256 digest를 반환한다.
4. CLI completion guard가 기존 gate와 함께 `current == verification.workspace_fingerprint == reviews.code[-1].artifact_digest`를 검사하고, 마지막 review 자체의 PASS verdict, 빈 blockers, 빈 open finding 목록, valid verification도 요구한다.
5. 모든 검사가 성공하면 순수 transition이 stage와 timestamp를 변경하고 atomic save가 `COMPLETED`를 영속화한다. 실패하면 save를 호출하지 않는다.

Exact CLI guarantee는 다음과 같다: 완료 CLI는 state를 `COMPLETED`로 저장하기 직전에 `state.project_root`의 workspace fingerprint를 직접 다시 계산하며, 그 현재 값과 유효한 verification fingerprint와 마지막 최종 PASS code review digest가 모두 같고 기존 completion gate도 통과할 때만 완료를 저장한다. 재계산 또는 비교가 실패하면 완료를 저장하지 않는다. 이 보증은 재계산이 관찰한 시점의 snapshot에 한정되며, lock/generation이 없으므로 측정 직후 별도 프로세스가 만든 동시 변경까지 원자적으로 배제한다고 주장하지 않는다.

## Failure behavior

- 삼자 digest mismatch, non-PASS final review, invalid verification 또는 기존 completion gate 실패는 `TransitionError`로 처리해 CLI 종료 코드 3과 구체적인 stderr를 내고 state 파일을 저장하지 않는다.
- `project_root`가 Git repository가 아니거나 commit이 없거나 Git 명령이 실패하면 기존 `GitError` 계약과 종료 코드 4를 유지한다.
- untracked entry의 `lstat`, regular-file read 또는 symlink `readlink`가 실패하면 경로를 포함한 `FilesystemError`, 종료 코드 4를 유지한다. special file은 payload를 읽지 않으므로 blocking read를 시도하지 않는다.
- 거부된 completion은 verification을 암묵적으로 invalidate하거나 stage를 demote하지 않는다. 영속 state bytes를 보존해 사용자가 원인을 진단할 수 있게 한다.
- 회복 절차는 workspace를 review된 상태로 복원하거나, 현재 workspace fingerprint에서 verification과 code review를 다시 실행한 뒤 completion을 재시도하는 것이다. fingerprint 규칙 변경으로 기존 저장값이 달라진 경우에도 같은 절차를 사용한다.
- 자동 retry는 없다. 동일한 stale evidence를 반복 제출해 완료되는 경로도 없다.

## Security and risk

fingerprint는 로컬 무결성 비교값이지 서명이나 인증 토큰이 아니다. `state.project_root`, Git output, 파일명, mode, content, symlink target은 신뢰하지 않는 입력으로 취급하고 length framing으로 연결 모호성을 막는다. symlink는 `lstat`와 `readlink`만 사용해 repository 밖 target을 읽지 않는다. FIFO/socket/device는 payload를 열지 않아 block, device side effect, 권한 상승 표면을 피한다.

주요 잔여 위험은 fingerprint 계산과 atomic state save 사이의 TOCTOU다. lock/generation이 명시적 범위 밖이므로 exact guarantee에서 이 한계를 공개하고, 테스트는 측정 전에 발생한 변화를 반드시 거부하는 데 초점을 둔다. mode 표현은 permission bits만 포함하며 uid/gid, timestamps, ACL, xattr는 이 범위의 fingerprint 입력이 아니다. 기존 fingerprint와의 값 호환성은 untracked entry가 있는 경우 의도적으로 깨질 수 있으나 state schema 호환성은 유지한다.

## Test strategy

검증 인터프리터는 `/opt/homebrew/bin/python3.12`를 직접 사용하고 `QG_BASE`는 `6d60011cbdaead7946b191d3f12029eef5c141c8`로 설정한다. 집중 테스트는 새 `CompletionIntegrityCLITests`, `FingerprintMetadataTests`, `TransitionPurityTests` 클래스로 구성해 CMD-2가 누락 없이 직접 실행할 수 있게 한다. 모든 filesystem 시나리오는 임시 directory와 임시 Git repository만 사용하고 전역 Git 설정이나 실제 사용자 repository를 변경하지 않는다. CMD-5는 두 Python 파일을 읽고 `ast.parse`만 호출하므로 bytecode나 repository-local `__pycache__`를 만들지 않는 read-only 검사다.

### 판정 명령 표

| ID | 명령 | 통과 조건 |
|---|---|---|
| CMD-1 | `/opt/homebrew/bin/python3.12 dot_claude/skills/quality-goal/tests/assert_python_version.py && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.12 -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_*.py'` | 종료 코드 0, 기존 테스트와 신설 테스트가 모두 실행되고 `OK` |
| CMD-2 | `/opt/homebrew/bin/python3.12 dot_claude/skills/quality-goal/tests/assert_python_version.py && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.12 dot_claude/skills/quality-goal/tests/test_quality_state.py CompletionIntegrityCLITests FingerprintMetadataTests TransitionPurityTests` | 종료 코드 0, 세 집중 회귀 클래스 전체 `OK` |
| CMD-3 | `wc -l < dot_claude/skills/quality-goal/SKILL.md` | 종료 코드 0, 출력이 500 미만 |
| CMD-4 | `/opt/homebrew/bin/python3.12 dot_claude/skills/quality-goal/tests/assert_preserved_sections.py "$QG_BASE"` | 종료 코드 0, `보존 대상 절 불변` |
| CMD-5 | `/opt/homebrew/bin/python3.12 -c 'import ast, pathlib; paths = ("dot_claude/skills/quality-goal/scripts/quality_state.py", "dot_claude/skills/quality-goal/tests/test_quality_state.py"); [ast.parse(pathlib.Path(path).read_text(encoding="utf-8"), filename=path) for path in paths]'` | 종료 코드 0, 두 파일 모두 syntax error가 없고 bytecode 또는 repository-local `__pycache__` 생성 없음 |
| CMD-6 | `/opt/homebrew/bin/python3.12 dot_claude/skills/quality-goal/tests/assert_tests_preserved.py "$QG_BASE"` | 종료 코드 0, `기존 테스트 보존` |

테스트 fixture는 helper를 통해 clean committed repository와 completion-ready state를 만든다. 각 mutation case는 verification/review 직후 하나의 변화만 적용해 원인을 격리한다. HEAD case는 empty commit, mode case는 content가 같은 untracked regular file의 `0644 -> 0755` 변경, content case는 tracked file bytes 변경을 사용한다. 거부 case는 exit code뿐 아니라 state file byte identity와 non-completed stage를 함께 assert한다.

metadata test는 permissions를 원복한 뒤 최초 digest로 복구되는 metamorphic assertion을 사용한다. frame ordering은 digest 최종값에만 의존하지 않고 `_frame` 호출 순서를 관찰해 type/permissions가 payload보다 먼저임을 증명한다. symlink fixture는 존재 target과 없는 target을 모두 포함하며 target content read를 spy로 금지한다. special-file 검증은 지원 플랫폼에서는 FIFO를 사용하고, 플랫폼 차이가 있는 kind는 `lstat`/reader mock으로 payload 비읽기 계약을 결정적으로 검증한다.

CMD-1은 신설 테스트뿐 아니라 기존 suite 전체의 회귀를 검증한다. CMD-3, CMD-4, CMD-6은 유지보수 runbook의 명령을 그대로 사용하고 CMD-5는 두 수정 Python 파일을 읽어 `ast.parse`하여 import나 bytecode 생성 없이 syntax 유효성을 확인한다.

## Decisions

### D1. CLI adapter에서 pre-save 재계산과 비교 수행 — 권고안

완료 target일 때만 CLI orchestration이 state의 `project_root`를 직접 측정하고 삼자 일치를 검사한 뒤 순수 transition과 save를 호출한다. 이는 현재 fingerprint를 caller가 주입할 수 없게 하고, Git I/O를 상태 머신에서 격리하며, 기존 command surface와 state schema를 보존한다. 이 설계를 채택한다.

### D2. 순수 transition에 current fingerprint 인자 전달 — 기각

`transition`에 선택적 fingerprint 인자를 더하면 함수 자체는 I/O 없이 유지할 수 있지만 기존 interface가 넓어지고, CLI 외 caller가 오래되거나 조작된 값을 공급할 수 있으며 새 검사 토큰과 유사한 우회 표면이 생긴다. 새 인자 금지와 직접 재계산 요구에 맞지 않아 기각한다.

### D3. transition 내부에서 Git fingerprint 계산 — 기각

상태 전이가 `state.project_root`를 읽게 하면 호출 지점은 단순하지만 단위 테스트의 결정성이 떨어지고 순수 transition에 Git I/O를 넣지 말라는 경계를 위반한다. 기각한다.

### D4. untracked metadata canonicalization

플랫폼의 native integer bytes나 `repr` 대신 `S_IFMT` 6자리 octal과 `S_IMODE` 4자리 octal의 ASCII를 length-frame한다. 값의 경계와 표현이 명시적이며 kind와 permissions를 payload보다 먼저 넣는 순서를 테스트할 수 있다. fingerprint format version은 추가하지 않는다.

<!-- strict-only:start -->

This block is required only for strict work. Any inapplicable subsection must be removed for non-strict work; within strict work, mark it as not applicable with a reason before review.

### Threat and trust boundaries

신뢰 경계 안에는 현재 프로세스의 비교 로직, SHA-256 구현, 성공적으로 atomic-replace된 state 파일만 둔다. operator가 선택한 state 파일, 그 안의 `project_root`, Git repository 상태, untracked 경로와 metadata/content, symlink target, verification/review JSON은 경계 밖 입력이다. 로컬에서 state 자체를 쓸 수 있는 적대자는 digest도 바꿀 수 있으므로 이 기능은 그 공격자를 막는 인증 수단이 아니다.

통제는 CLI가 caller-supplied current digest를 받지 않는 것, state의 root를 직접 측정하는 것, 세 digest의 정확한 동등성, length framing, symlink 비역참조, special-file 비읽기, 오류 시 no-save다. repository 밖으로 향하는 symlink는 target 문자열만 관찰한다. Git/filesystem read 실패는 fail closed 한다.

### Authorization and tenant isolation

해당 없음. 이 CLI는 로컬 단일-user state/repository 도구이며 tenant, 원격 principal 또는 권한 부여 API가 없다. 이번 변경은 권한 모델을 추가하지 않는다. 격리 검증 대신 CLI는 state에 기록된 정확한 `project_root` 하나만 fingerprint하고 symlink target을 따라 다른 filesystem 영역을 읽지 않는 경계 테스트를 수행한다.

### Migration, compatibility, and rollback

state schema/version, command 이름, 인자, transition graph에는 migration이나 backfill이 없다. #50-B로 untracked entry가 있는 workspace의 fingerprint 값은 바뀔 수 있다. 저장 verification/review digest를 자동 재작성하지 않고 completion을 거부하여, 사용자가 새 알고리즘으로 verification과 code review를 다시 수행하게 한다. 이는 오래된 증거를 새 값으로 승격하지 않는 fail-closed 호환 정책이다.

rollback trigger는 전체 suite/보존 검사 실패, unchanged completion 회귀, mutation completion 허용, symlink target 역참조, special-file read 또는 정상 repository에서의 비결정 fingerprint다. rollback은 completion CLI orchestration과 metadata framing 변경을 함께 이전 구현으로 되돌리고 신설 문서 보증도 이전 동작에 맞게 되돌리는 것이다. 새 schema/data migration이 없으므로 state 파일 복구 작업은 필요 없다. rollback 뒤 이미 새 fingerprint로 기록된 in-progress state는 verification/review를 다시 수행해야 하며 자동 digest 변환은 하지 않는다.

### Failure recovery and observability

사용자 관찰 신호는 CLI exit code와 stderr, 그리고 변경되지 않은 state stage다. digest/gate mismatch는 종료 코드 3, Git/filesystem 측정 실패는 종료 코드 4로 구분한다. 오류 메시지는 completion에 필요한 삼자 일치 실패인지 repository 측정 실패인지 식별할 수 있어야 하지만 fingerprint 원문 외 민감한 file content를 출력하지 않는다.

상시 service가 아니므로 alert, metric, distributed trace는 해당 없음이다. 회복은 stderr 원인을 확인하고 workspace 복원 또는 verification/review 재실행 후 수동 재시도한다. 테스트 실패 시 배포를 중단하고 rollback 조건을 평가한다.

### High-risk end-to-end verification

고위험 경로는 오래된 증거로 terminal completion을 영속화하는 경로다. CMD-2에서 실제 CLI와 임시 Git repository/state file을 사용해 unchanged 성공, verification 뒤 tracked content 변경, untracked `chmod +x` 변경, empty commit에 의한 HEAD 변경, digest mismatch, Git 측정 실패를 각각 실행한다. 모든 변경 case는 nonzero exit, state byte identity, non-completed stage를 동시에 요구한다. fingerprint 경로는 `0644 -> 0755 -> 0644` 변경/복원, existing/broken symlink, special-file 비읽기, 정렬 결정성을 함께 검증한다.

CMD-2의 어느 case라도 완료를 잘못 저장하거나 hang/read side effect가 발생하면 즉시 중단 조건이다. 그 다음 read-only `ast.parse` 검사인 CMD-5, CMD-1, CMD-3, CMD-4, CMD-6 순서로 검증하고 하나라도 실패하면 완료 또는 배포를 주장하지 않는다. 최종 evidence에는 각 명령, exit code, 전체 test count와 `OK`/보존 메시지를 기록한다.

### No production mutation confirmation

자동 검증 중 filesystem 변경은 임시 directory의 임시 Git repository와 fixture state에만 발생한다. CMD-5는 두 repository Python 파일을 읽어 `ast.parse`만 수행하며 bytecode나 repository-local `__pycache__`를 생성하지 않는다. 실제 사용자 repository, 배포된 home directory, 원격 Git, production state 또는 외부 service를 mutate하지 않는다. `chezmoi apply`, commit, push, release, migration은 이 Spec의 자동 workflow에 포함되지 않는다.

<!-- strict-only:end -->
