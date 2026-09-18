# Quality Goal Specification

- Task ID: 20260917T115927Z-107-dual-review-스킬을-claude-codex-공용-단일-구-6ae8e1d9
- Mode: strict
- Status: SPEC_REVIEW
- Created: 2026-09-17
- Updated: 2026-09-17
- Source goal: GitHub 이슈 #107의 dual-review를 단일 구현 원본과 얇은 도구별 진입점으로 배포하여 Claude와 Codex가 같은 워크플로를 직접 발견·호출하게 한다

## Problem and context

현재 dual-review의 구현과 진입점은 `dot_claude/skills/dual-review/`에 함께 있고 chezmoi는 이를 `~/.claude/skills/dual-review/`에만 배포한다. 따라서 Claude는 스킬을 발견하지만 Codex는 스킬을 직접 발견하거나 호출할 수 없다. 이 문제는 dual-review 파이프라인 내부가 Codex를 읽기 전용 reviewer로 실행하는 현행 동작과 구별된다. 이슈 #107은 호출 주체로서의 Codex를 추가하면서 독립 리뷰, 교차 비평, 새 Claude 종합, 실패 분류, 로컬 보고서 계약을 양쪽 호출에서 동일하게 유지하라고 요구한다.

저장소에는 세 배포 관례가 공존한다. `dot_claude/skills/`는 Claude 전용, `dot_codex/skills/`는 Codex용, `dot_agents/skills/`는 `CLAUDE.md`가 "에이전트 공용 스킬 (Claude Code 외 도구도 읽음)"으로 정의한다. `github-work-log`는 한쪽 실행 파일을 다른 도구의 chezmoi 심링크 템플릿에서 참조하는 선례이고, `dot_agents/skills/create-worktree/agents/openai.yaml`은 Codex 인터페이스 선례다. 다만 현재 설치와 설정만으로 Codex의 실제 발견 루트가 `~/.codex/skills`인지 `~/.agents/skills`인지 확정할 수 없다. 두 디렉터리가 모두 존재하고 `~/.codex/config.toml`에는 임의 `SKILL.md`의 명시 경로만 있을 뿐 전역 탐색 루트 설정은 없다. 이 Spec은 어느 후보도 가정하지 않고 Codex가 주입받은 실제 스킬 카탈로그를 읽는 live 판정으로 루트를 확정한다.

2026-09-17 측정 요약 `~/.local/share/quality-goal/measurements/20260917-107-impact-summary.md`와 그 원시 전사는 다음 위험을 입증했다.

1. base revision `3c68f33ee687e900a6349731f1e4a38a124e326c`에서 기존 source suite는 122 tests, OK, skipped 1이었다. skip은 `DUAL_REVIEW_LIVE_API=1`로만 열리는 production schema live test다.
2. payload를 `dot_claude` 밖으로 옮기고 Claude 트리를 얇은 진입점으로 만든 목표 배치 probe도 똑같이 122 tests, OK, skipped 1이었다. 따라서 기존 suite 통과는 이 작업의 충분성 근거가 아니다.
3. `test_contracts.py`의 캐시 제외 검사는 `dot_claude` 경로 가드가 false가 되면 조용히 사라지고, 패키징 순회는 공용 payload만 보아 얇은 진입점 트리를 검사하지 않으며, `managed_target()` 호출은 이동 전 리터럴을 사용한다. Codex 배포 단언은 없고 문서 검사는 낡은 문자열의 존재만 확인한다.
4. 현 위치에 `symlink_review_state.py.tmpl` 하나만 더한 probe는 거대 `test_packaging_contract`가 `.tmpl` 단언에서 먼저 멈춰 `symlink_` 접두사 위반을 숨겼다. 계약별 독립 test case가 필요하다.
5. chezmoi v2.70.0은 디렉터리 대상 `symlink_<name>.tmpl`을 항목 하나인 디렉터리 심링크로 배포한다. 심링크를 지난 `Path(__file__).resolve().parents[1]`은 공용 payload의 `schemas/`와 `templates/`를 올바르게 가리킨다. 스크립트 파일만 심링크하고 이웃 디렉터리를 진입점 쪽 실디렉터리로 두는 배치는 깨진다.
6. 이동한 원본 경로의 `__pycache__` 제외가 없으면 10개 cache/bytecode 항목이 managed 대상으로 새어 나왔다. 기존 green suite는 이 오염을 잡지 못했다.

이 Spec의 충분성은 위 공백을 직접 겨냥하는 신규 test case, 격리된 rendered-home 검사, 실제 설치본 검사, 양쪽 진입점 live E2E로 판단한다. 기존 122개 suite는 payload 동작의 교차 회귀 신호로만 사용한다.

## Goals

1. dual-review의 실행 payload를 한 공용 원본으로 유지하고 Claude와 실측으로 확정된 Codex 발견 루트에 얇은 진입점을 배포한다.
2. chezmoi 적용 뒤 Claude와 Codex가 각각 dual-review를 발견하고 같은 고정 fixture diff에 대해 실제 전체 파이프라인을 끝까지 실행하게 한다.
3. 원본, rendered deployment, 실제 설치본의 구조와 bytes가 일치하고 설치본에서 deterministic suite가 실행되게 한다.
4. 기존 Claude 호출 문법과 파이프라인 의미, 읽기 전용 경계, 로컬 보고서 계약을 보존한다.
5. 호출법, 필수 CLI와 인증, 종료·실패·미완료 해석, 배포 실패 복구를 운영 문서에서 재현 가능하게 설명한다.

## Non-goals

- dual-review 내부 reviewer 구성, 모델/effort, schema, 익명화, 교차 비평, 종합 알고리즘 또는 보고서 형식을 새로 설계하지 않는다.
- PR 생성·게시·댓글·상태 변경을 구현하지 않는다. 이는 이슈 #106의 범위다.
- 모든 스킬을 공용 저장소로 옮기는 이슈 #97을 선행 구현하거나 다른 스킬의 배포 구조를 정리하지 않는다.
- Codex가 dual-review 내부 reviewer로 동작하는 현행 기능을 이번 문제의 완료로 간주하지 않는다.
- 영구 테스트에 base revision SHA를 고정하거나 작업 기간을 `git diff`로 판정하지 않는다. fixture 저장소가 자기 diff의 동일성을 검사하는 것은 허용한다.
- gitignored task 산출물, credential, token, session transcript를 테스트 입력으로 사용하거나 Git/chezmoi 관리 대상으로 넣지 않는다.
- 실제 GitHub 쓰기, commit, push, merge, release, production 배포를 수행하지 않는다.

## Requirements

- **R1.1** 배치 경로를 확정하거나 HOME 적용을 시작하기 전에 각 후보 root에 서로 다른 nonce 이름의 최소 probe skill을 임시 생성하고, `codex exec`의 새 세션에 주입된 Available skills catalog에서 어느 probe가 실제 노출되는지 machine-readable 결과로 판정한다. 디렉터리 존재나 저장소 문언만으로 발견을 추론하지 않는다. probe는 성공·실패 모두에서 제거하고 두 후보 root의 pre/post file set과 digest가 같아야 한다. 하나 이상이 발견되어야 진행할 수 있고, 둘 다 발견되면 저장소의 공용 스킬 관례인 `~/.agents/skills`를 선택한다. 결과에는 Codex CLI version, 측정 시각, 발견된 후보, 선택한 단일 Codex 배포 target을 기록한다.
- **R1.2** 단일 공용 구현 원본은 `dot_agents/skills/dual-review/`이며 `scripts/`, `schemas/`, `templates/`, `references/`, `tests/`와 Codex-compatible `SKILL.md` 및 필요 시 `agents/openai.yaml`을 소유한다. `dot_claude/skills/dual-review/`는 기존 Claude-compatible `SKILL.md`와 공용 payload 디렉터리를 가리키는 chezmoi 디렉터리 심링크 템플릿만 소유한다. R1.1이 `~/.codex/skills`를 선택한 경우에만 동일한 형태의 `dot_codex/skills/dual-review/` 얇은 Codex 진입점을 추가하고, `~/.agents/skills`가 선택되면 같은 이름의 Codex 중복 진입점을 만들지 않는다.
- **R1.3** 각 얇은 진입점은 파일 하나가 아니라 `scripts`, `schemas`, `templates`, `references`, `tests` 디렉터리 전체를 공용 설치 target에 심링크한다. 실행 파일의 `Path(__file__).resolve().parents[1]`이 항상 공용 payload root가 되어 schema/template/reference/test의 이웃 관계를 보존해야 한다. 구현 Python, schema, template, test 본문을 도구별 tree에 복제하지 않는다.
- **R2.1** Claude 진입점은 현재 `dual-review` 이름, argument contract `[--base <ref>] [--rounds 1|2]`, Claude frontmatter와 `/dual-review` 호출 호환성을 유지한다. Codex 진입점은 `$dual-review`로 발견·호출되고 Codex가 지원하는 frontmatter와 `agents/openai.yaml` 인터페이스만 사용한다. 두 진입점 모두 같은 공용 `scripts/review_state.py`를 대상 저장소에서 실행한다.
- **R2.2** 양쪽 호출은 같은 non-empty fixture diff에서 동일한 base/head, 파일 목록, diff bytes digest를 snapshot으로 사용하고 각각 여섯 round-zero producer start-before-first-read, 양방향 교차 비평, fresh-Claude synthesis, local `report.md` 생성을 실제 CLI와 인증된 모델 호출로 완료한다. findings의 자연어와 run ID는 동일할 필요가 없지만 phase 성공 상태와 target snapshot은 같아야 한다.
- **R2.3** 기존 종료 계약을 보존한다. `reviewer_failure`, `single_reviewer`, `pipeline_failure`는 exit 1의 미완료이고, `no_changes`는 exit 0이어도 검토 대상이 없었다는 뜻이지 전체 리뷰 성공이 아니다. 그 밖의 exit 0 종료도 report를 읽고 findings와 termination reason을 해석해야 하며 결함 부재를 뜻하지 않는다. 누락 CLI, 미인증, timeout, schema 거부는 성공으로 축소하지 않고 reviewer/phase status, stderr, exit code와 로컬 report/provenance에 드러낸다.
- **R3.1** `tests/`는 공용 payload와 모든 설치 진입점에서 접근 가능한 배포 대상에 포함한다. source, 격리 rendered-home, 실제 설치본 각각에서 deterministic suite를 실행할 수 있어야 하며 설치본 test가 공용 implementation bytes를 실제로 import하는지 확인한다.
- **R3.2** 신규 packaging test는 적어도 다음 독립 case를 메서드 단위로 둔다: `test_managed_targets_derive_from_declared_roots`, `test_entrypoint_templates_are_allowed_only_in_thin_trees`, `test_rendered_claude_and_selected_codex_entrypoints_resolve_shared_payload`, `test_cache_ignore_covers_actual_shared_payload_target`, `test_operation_paths_match_declared_layout`, `test_installed_tests_resolve_shared_implementation`. 기존 거대 `test_packaging_contract`의 첫 실패가 뒤 계약을 가리지 않게 각 case가 독립 실행되어야 한다.
- **R3.3** `.chezmoiignore`는 실제 공용 배포 target 아래 모든 `__pycache__`와 `.pyc`를 제외한다. 격리 destination의 `chezmoi managed` 결과에는 cache/bytecode가 0개이고, 얇은 진입점의 의도된 `symlink_*.tmpl`은 source-state 파일로만 허용되며 공용 payload 내부에는 `.tmpl`과 chezmoi state prefix가 0개여야 한다.
- **R3.4** source-to-target mapping test는 source root 종류에서 target root를 파생하며 옮기기 전 `dot_claude/skills/dual-review/SKILL.md` 리터럴을 성공 조건으로 사용하지 않는다. 격리 rendered-home과 실제 설치본에서 각 진입점의 realpath, relative file set, regular-file bytes가 공용 payload와 일치하고 누락·추가·복제 implementation file이 0개여야 한다.
- **R4.1** 실제 `$HOME` 적용 전 새 source를 별도 destination에 render하고 symlink target 존재, dangling link 0개, cache 0개, 두 진입점 resolution, 설치 test 실행을 모두 통과시킨다. 실제 `~/.claude/skills/dual-review`를 교체하기 직전에 regular directory/symlink 유형과 내용을 임시 backup에 보존하고, dual-review 관련 target만 지정해 chezmoi를 적용한다. preflight 실패 시 apply를 시작하지 않는다.
- **R4.2** 실제 적용이 중간 실패하거나 적용 직후 검사가 실패하면 부분 생성된 dual-review target을 제거하고 backup의 원래 유형·내용·symlink를 복원한 뒤 실패로 종료한다. 성공 후에는 backup을 삭제하고 선택되지 않은 Codex 후보에 stale `dual-review`가 없어야 한다. 복구 절차는 다른 skill과 chezmoi source를 건드리지 않고 재실행 가능해야 한다.
- **R5.1** 운영 문서는 Claude `/dual-review`와 Codex `$dual-review`의 호출 예시, `--base`와 `--rounds`, 필수 `python3`·`git`·`claude`·`codex`·`chezmoi` CLI/version 확인, Claude/Codex 인증 확인, 로컬 state/report 위치, R2.3의 종료·실패·미완료 해석, 발견 루트 측정 결과와 재측정법, 설치·rollback 절차를 실제 배치와 일치하게 설명한다.
- **R5.2** 변경 범위는 dual-review 공용 원본과 Claude/선택된 Codex 진입점, `.chezmoiignore`, dual-review 운영·검증 문서, 이 작업의 development 문서로 제한한다. 다른 skill payload, 전역 Codex 설정, reviewer 알고리즘, #97 전체 이동, #106 PR 게시 코드는 수정하지 않는다.

## Acceptance criteria

- **AC-1** R1.1의 live probe가 서로 다른 nonce probe를 Codex 세션의 실제 catalog에서 판별해 두 후보의 발견 여부를 JSON으로 출력하고, 하나 이상의 발견과 정확히 한 선택 target을 보인다. 둘 다 발견된 결과에서는 `~/.agents/skills/dual-review`를 선택하며 어느 것도 발견되지 않거나 출력이 모호하면 nonzero로 중단한다. 성공·실패 fixture 모두 probe가 0개 남고 두 후보 root의 pre/post file set과 digest가 같다. [실행] (CMD-1)
- **AC-2** R1.2·R1.3의 source layout 검사에서 공용 payload의 required file set이 완전하고 Claude 및 선택된 Codex 진입점의 다섯 디렉터리가 공용 설치 target으로 resolve되며, 도구별 tree에 구현 Python/schema/template/test regular-file 복제가 0개이다. [실행] (CMD-2)
- **AC-3** R2.1의 entrypoint contract test가 Claude의 기존 name/arguments/frontmatter와 Codex의 name/frontmatter/`agents/openai.yaml`을 각각 검증하고, 두 `SKILL.md`가 같은 resolved `scripts/review_state.py`를 실행하도록 지시함을 확인한다. [실행] (CMD-2)
- **AC-4** R3.2의 여섯 신규 packaging case가 각각 독립 test로 수집·통과하고, 의도된 thin-tree template 허용과 payload 금지를 별도 assertion으로 모두 평가한다. [실행] (CMD-2)
- **AC-5** R3.3·R3.4·R4.1의 격리된 chezmoi destination 검사에서 Claude, 공용 payload, 선택된 Codex target이 예상 유형으로 render되고 dangling link, cache/bytecode managed entry, payload 내부 source-state name, implementation duplicate, source/deployment byte drift가 모두 0개이다. 이 검사는 실제 `$HOME`을 읽거나 쓰지 않는다. [실행] (CMD-3)
- **AC-6** R3.1의 공용 source suite가 non-empty로 실행되고 기존 deterministic 122개를 포함해 전부 통과한다. 이 결과는 payload 동작의 교차 회귀만 증명하며 AC-1–AC-5와 AC-7–AC-10을 대신하지 않는다. live API skip은 환경변수가 없을 때만 허용한다. [실행] (CMD-4)
- **AC-7** R4.1·R4.2의 opt-in 설치 harness가 backup과 격리 preflight를 먼저 기록하고 dual-review 관련 target만 `chezmoi apply`한 뒤 post-check를 통과한다. 실제 HOME에 적용하기 전 disposable destination의 기존 Claude tree를 복제한 강제 실패 fixture에서 원래 file type과 digest가 byte-for-byte 복원되고 다른 skill target 변화가 0개이며, 실제 적용 성공 시 선택되지 않은 Codex 후보의 stale 동명 entry가 0개이다. [실행] (CMD-5)
- **AC-8** R3.1·R3.4의 실제 설치본 검사에서 공용 payload, Claude entrypoint, 선택된 Codex entrypoint를 각각 경유한 deterministic suite가 non-empty exit 0이고, 세 경로의 tests와 implementation realpath/bytes가 단일 공용 payload로 수렴한다. [실행] (CMD-6)
- **AC-9** R2.1의 실제 Claude 및 Codex 호출 smoke가 각각 `/dual-review`와 `$dual-review`를 명시해 시작되고, 두 CLI의 entrypoint discovery receipt가 선택된 installed `SKILL.md` 절대 경로와 공용 script realpath를 기록한다. 직접 Python script를 시작한 실행은 통과로 인정하지 않는다. [실행] (CMD-7)
- **AC-10** R2.2의 live E2E harness가 임시 Git fixture에 한 번 만든 non-empty diff를 두 entrypoint에 그대로 전달한다. 두 run의 snapshot base/head, file list, diff digest가 같고, 각 run이 여섯 producer start-before-read, 양방향 critique status `ok`, fresh-Claude synthesis status `ok`, report/provenance 생성을 만족하며 fixture HEAD와 porcelain은 실행 전후 동일하다. [실행] (CMD-7)
- **AC-11** R2.3의 table-driven failure tests가 `reviewer_failure|single_reviewer|pipeline_failure`를 exit 1, `no_changes`와 정상 termination을 exit 0으로 유지하고, missing CLI/auth/timeout/schema rejection을 성공 phase로 기록하지 않는다. 운영 문서 assertion은 exit 0의 의미를 리뷰 완료나 결함 부재로 과장하지 않음을 확인한다. [실행] (CMD-8)
- **AC-12** R5.1의 운영 문서에 양쪽 호출 예시, 인자, 필수 CLI/version/auth preflight, state/report path, 발견 재측정, 설치 전 backup, 실패 rollback, 모든 termination reason 해석이 실제 source layout 및 명령과 일치한다. [문서] `dot_agents/skills/dual-review/references/operation.md`와 `dot_agents/skills/dual-review/references/verification.md`
- **AC-13** R5.2의 scope check에서 허용 경로 밖 changed file이 0개이고 GitHub write command와 PR publication 구현이 0개이며 다른 skill tree와 Codex global config 변경이 0개이다. 판정은 고정 SHA나 작업 기간 `git diff`가 아니라 테스트가 선언한 허용 path set과 현재 changed-file list를 비교한다. [실행] (CMD-9)
- **AC-14** R1.2–R5.2의 cross-regression matrix가 Claude thin entrypoint가 payload 이웃 관계를 깨지 않고, cache 제외가 설치 test를 제거하지 않으며, 선택 Codex target이 중복 skill name을 만들지 않고, rollback이 source/deployment sync를 깨지 않으며, 문서 경로가 rendered layout과 다르지 않음을 함께 확인한다. [실행] (CMD-2 CMD-3 CMD-8)

## Requirements traceability

This table maps every requirement to acceptance criteria and the judgement method that proves the mapping.

| Requirement | Acceptance criteria | Judgement method |
|---|---|---|
| R1.1 | AC-1, AC-12 | CMD-1 live catalog probe와 운영 문서의 recorded discovery decision |
| R1.2 | AC-2, AC-4, AC-14 | CMD-2 source layout·독립 packaging cases |
| R1.3 | AC-2, AC-5, AC-14 | CMD-2·CMD-3의 directory realpath와 이웃 관계 검사 |
| R2.1 | AC-3, AC-9, AC-14 | CMD-2 entrypoint contract와 CMD-7 실제 양쪽 invocation receipt |
| R2.2 | AC-10, AC-14 | CMD-7 동일 fixture diff의 두 full-pipeline run 비교 |
| R2.3 | AC-11, AC-12 | CMD-8 failure matrix와 운영 문서 termination table |
| R3.1 | AC-6, AC-8, AC-14 | CMD-4 source suite와 CMD-6 세 설치 경로 suite |
| R3.2 | AC-4, AC-14 | CMD-2의 지명된 여섯 독립 test method |
| R3.3 | AC-5, AC-14 | CMD-3 rendered managed-set/cache/source-state 검사 |
| R3.4 | AC-5, AC-8, AC-14 | CMD-3·CMD-6 source-derived mapping, realpath, bytes 검사 |
| R4.1 | AC-5, AC-7, AC-14 | CMD-3 격리 preflight와 CMD-5 backup-first targeted apply |
| R4.2 | AC-7, AC-14 | CMD-5 forced-failure restore와 success stale-target 검사 |
| R5.1 | AC-11, AC-12, AC-14 | CMD-8 문서 assertion과 지정 운영 문서 직접 검토 |
| R5.2 | AC-13, AC-14 | CMD-9 허용 path/source scan과 cross-regression matrix |

## Architecture

### 구성 요소와 소유권

| 구성 요소 | 책임 | 배치 결정 |
|---|---|---|
| 공용 payload | Python pipeline, schema, template, references, tests, Codex-compatible skill metadata | `dot_agents/skills/dual-review/` → `~/.agents/skills/dual-review/` |
| Claude entrypoint | 기존 Claude frontmatter와 호출 안내, payload 디렉터리 심링크 | `dot_claude/skills/dual-review/` → `~/.claude/skills/dual-review/` |
| Codex entrypoint | `$dual-review` metadata와 payload 연결 | CMD-1이 `.agents`를 선택하면 공용 payload 자체, `.codex`를 선택하면 `dot_codex/skills/dual-review/` thin tree |
| packaging tests | source/rendered/installed topology, cache, bytes, docs contract | 공용 payload의 `tests/` |
| live probes | discovery, local install, dual-entrypoint E2E | 명시적 opt-in인 공용 payload test harness; default suite에서는 모델/실제 HOME 호출 안 함 |

`dot_agents`를 공용 원본으로 선택한 이유는 저장소가 이 디렉터리를 도구 공용 스킬로 정의하고, #97 전체 분리 없이 dual-review 하나만 이동할 수 있으며, 모든 진입점의 directory symlink target을 한 곳으로 고정할 수 있기 때문이다. 공용 payload는 실제 설치 target이므로 얇은 진입점의 symlink가 dangling되지 않는다.

Codex target 선택은 구현자의 판단이 아니라 CMD-1 결과와 다음 결정 함수로 닫힌다.

1. `.agents`가 실제 catalog에 있으면 `.agents`를 선택한다. `.codex`도 함께 발견되더라도 dual-review를 두 곳에 배포하지 않는다.
2. `.agents`가 없고 `.codex`만 발견되면 `.codex` thin entrypoint를 추가한다.
3. 둘 다 없거나 catalog 결과를 parse/검증할 수 없으면 배포 설계를 추측하지 않고 BLOCKED로 중단한다.

각 진입점의 `scripts` symlink를 통해 실행된 `review_state.py`는 `Path(__file__).resolve()`로 공용 실제 파일에 도달한다. 따라서 `parents[1] / schemas`, `parents[1] / templates`는 공용 payload 이웃을 가리킨다. 다섯 payload 디렉터리를 함께 연결하는 조건이 이 불변식을 보장한다.

고려한 대안은 다음과 같다.

- 현 `dot_claude`를 원본으로 두고 Codex만 역방향 심링크: 변경량은 작지만 Claude 전용 tree가 계속 공용 구현을 소유하여 저장소 경계와 어긋나고 향후 도구 추가 시 의존 방향이 틀어진다.
- Claude와 Codex에 payload 복제: 발견은 단순하지만 drift와 이중 수정이 생겨 이슈의 코드 중복 금지를 위반한다.
- #97 전체를 먼저 수행: 가장 넓은 정리는 가능하지만 독립 이슈를 선행 조건으로 만들어 범위를 확대한다.

## Interfaces and data flow

### 발견과 배포 흐름

1. CMD-1은 두 후보 root의 file set과 digest를 기록하고 각 root 아래에 충돌하지 않는 서로 다른 nonce 이름의 최소 probe `SKILL.md`를 만든 뒤 현재 Codex CLI version을 기록하고 read-only `codex exec`를 시작한다.
2. probe prompt는 세션에 이미 주입된 Available skills catalog에서 두 nonce skill의 노출 여부와 catalog path만 JSON schema에 맞춰 반환하게 한다. shell로 후보 디렉터리를 열거한 결과는 발견 증거로 인정하지 않는다.
3. probe는 반환 path와 nonce가 일치하는지 확인하고 R1.1의 결정 함수로 단일 target을 출력한다. `finally` cleanup 뒤 두 후보 root의 file set과 digest가 pre-state와 같지 않으면 판정 자체를 실패시킨다.
4. source layout과 `.chezmoiignore`를 구성한 후 CMD-3이 임시 destination에서 render/managed topology를 검증한다.
5. CMD-5가 현 Claude 설치본을 backup하고 dual-review target만 apply한 뒤 post-check한다. 실패하면 즉시 rollback한다.

### 호출과 pipeline 흐름

Claude 입력은 `/dual-review [--base <ref>] [--rounds 1|2]`, Codex 입력은 `$dual-review [--base <ref>] [--rounds 1|2]`다. 진입점은 target repository에서 공용 `review_state.py`를 실행한다. script는 base를 resolve하고 snapshot을 고정한 뒤 다섯 Claude producer와 한 Codex producer를 모두 시작하고, 결과를 읽은 뒤 양방향 critique와 새 Claude synthesis를 수행해 `.claude/dual-review-state/<run-id>/` 아래 local artifacts와 report를 쓴다.

CMD-7 fixture는 임시 Git repository에 base commit과 한 changed commit을 만든다. 이 SHA들은 실행 때 생성되는 fixture 값이며 source나 영구 테스트에 고정하지 않는다. harness는 같은 base/head/diff digest를 두 CLI에 전달하고 각 entrypoint가 직접 호출됐다는 receipt, 생성된 snapshot/provenance/report, 실행 전후 HEAD/status를 비교한다.

### Test interface

default suite는 외부 모델과 실제 HOME을 건드리지 않는다. `live_discovery.py`, `live_install.py`, `live_entrypoints.py`는 각각 명시적 environment opt-in 없이는 skip 또는 nonzero로 끝난다. 설치 harness는 backup path와 touched target 목록을 receipt로 남기되 credential, model output 원문, session transcript를 source tree에 저장하지 않는다.

## Failure behavior

- Codex discovery probe가 두 후보를 모두 못 찾거나 schema가 잘못되면 source 이동과 HOME apply를 시작하지 않고 BLOCKED로 보고한다. `.codex`를 임의 default로 택하지 않는다.
- 격리 render에서 dangling link, cache managed entry, byte drift, test failure가 하나라도 나오면 실제 HOME을 변경하지 않는다.
- 실제 적용 전 `~/.claude/skills/dual-review`가 directory인지 symlink인지 포함해 전체 tree를 임시 backup에 보존한다. 선택된 Codex target에 기존 동명 entry가 있으면 같은 방식으로 보존한다.
- apply 중단, post-apply test 실패, discovery mismatch가 발생하면 새로 생성된 dual-review target만 제거하고 backup을 원래 path와 file type으로 복원한다. 복원 뒤 digest/type 검사까지 실패하면 backup을 삭제하지 않고 수동 복구 명령과 경로를 출력한다.
- CLI 누락 또는 인증 실패는 설치 성공으로 간주하지 않는다. discovery/install은 실패하고 live E2E는 시작하지 않는다. pipeline 실행 중 발생한 경우 R2.3의 incomplete reason과 process status를 report한다.
- `no_changes`는 정상 exit이지만 review coverage가 없으므로 AC-10의 E2E 증거가 될 수 없다. `reviewer_failure`, `single_reviewer`, `pipeline_failure`는 report가 생성돼도 완료가 아니다.
- 한 entrypoint만 성공하면 양쪽 지원 완료로 판정하지 않는다. 성공한 run artifacts는 진단용으로 보존하고 실패한 쪽을 복구·재실행한다.

## Security and risk

- Claude/Codex model process는 target diff를 읽는다. live E2E는 credential이나 실제 제품 코드를 포함하지 않는 임시 fixture만 사용해 외부 모델에 전달되는 데이터를 제한한다.
- 기존 pipeline의 Claude allowlist `Read,Glob,Grep`, Codex read-only sandbox, target fingerprint guard를 유지한다. entrypoint 추가가 reviewer 권한을 넓히지 않는다.
- `chezmoi apply`는 실제 사용자 HOME의 기존 directory를 symlink 구조로 바꾸므로 가장 큰 운영 위험이다. 격리 preflight, target 한정 apply, type-aware backup, 실패 시 자동 restore, restore verification으로 완화한다.
- cache와 bytecode는 실행 환경 흔적이며 source/deployment에 포함하지 않는다. 실제 공용 target 기반 ignore와 rendered managed-set test로 누출을 막는다.
- discovery 결과에는 nonce가 아닌 candidate root, 선택 path, CLI version만 durable하게 기록한다. probe name/content는 실행 후 제거하고 config, token, 인증 payload, prompt transcript는 durable 문서에 기록하지 않는다.
- GitHub write command, PR publication, commit/push/merge는 entrypoint와 harness에 포함하지 않는다.

## Test strategy

### 판정 명령 표

| ID | 명령 | 통과 조건 |
|---|---|---|
| CMD-1 | `DUAL_REVIEW_DISCOVERY_LIVE=1 python3 dot_agents/skills/dual-review/tests/live_discovery.py --codex-root "$HOME/.codex/skills" --agents-root "$HOME/.agents/skills"` | Codex catalog에서 한 후보 이상을 확인하고 결정 함수가 단일 target, CLI version, 측정 시각을 JSON으로 출력하며 exit 0 |
| CMD-2 | `python3 -m unittest discover -s dot_agents/skills/dual-review/tests -p 'test_deployment.py' -v` | R3.2의 여섯 지명 case와 entrypoint/cross-regression case가 모두 독립 수집되고 exit 0 |
| CMD-3 | `python3 dot_agents/skills/dual-review/tests/verify_rendered_deployment.py --source "$PWD"` | 임시 destination render에서 expected topology, zero dangling/cache/duplicate/drift, installed-path tests가 모두 PASS이고 실제 HOME 접근 0회 |
| CMD-4 | `python3 -m unittest discover -s dot_agents/skills/dual-review/tests -v` | non-empty 전체 source suite exit 0; live test skip은 opt-in 미설정 case만 허용 |
| CMD-5 | `DUAL_REVIEW_HOME_APPLY=1 python3 dot_agents/skills/dual-review/tests/live_install.py --source "$PWD" --apply --verify-rollback` | disposable destination의 forced-failure가 원래 type/bytes를 복원한 뒤 실제 HOME의 backup-first targeted apply와 post-check가 PASS하고 다른 skill 변화 0개 |
| CMD-6 | `python3 "$HOME/.agents/skills/dual-review/tests/verify_installed_entrypoints.py"` | 공용, Claude, 선택 Codex 경로의 suite가 각각 non-empty exit 0이고 realpath/bytes가 공용 payload로 수렴 |
| CMD-7 | `DUAL_REVIEW_LIVE_ENTRYPOINTS=1 python3 "$HOME/.agents/skills/dual-review/tests/live_entrypoints.py" --rounds 2` | 동일 임시 fixture diff를 `/dual-review`와 `$dual-review`가 직접 실행하고 두 full pipeline, snapshot identity, phase status, no target mutation이 PASS |
| CMD-8 | `python3 -m unittest discover -s dot_agents/skills/dual-review/tests -p 'test_contracts.py' -v` | termination/exit/failure surfacing 및 operation/verification 문서 계약 case 전부 exit 0 |
| CMD-9 | `python3 dot_agents/skills/dual-review/tests/verify_change_scope.py --repository "$PWD"` | 선언된 #107 허용 path set 밖 changed path, 다른 skill/global config 변경, GitHub write·PR publication 구현이 모두 0개 |

기존 122개 green은 구조 변경에 무신호였으므로 CMD-4 단독으로 완료를 선언하지 않는다. 구조 충분성은 CMD-2의 여섯 독립 case와 CMD-3의 실제 chezmoi render가 증명하고, 배포 충분성은 CMD-5·CMD-6, 사용자 경로 충분성은 CMD-1·CMD-7이 증명한다.

`test_deployment.py`는 source path를 hard-code한 단일 helper가 아니라 declared source roots와 discovery decision을 fixture로 받아 target을 계산한다. template 허용 검사는 thin entrypoint tree와 payload tree를 별도 subtest로 실행한다. cache 검사는 실제 `__pycache__`와 `.pyc` fixture를 만들고 임시 destination의 `chezmoi managed`에 나타나지 않음을 확인한 뒤 정리한다.

CMD-7은 비용과 인증이 필요한 high-risk opt-in gate다. 양쪽 run 모두 성공하지 않으면 재시도 횟수로 덮지 않고 실패 phase를 남긴다. 자연어 findings 일치는 요구하지 않으며 동일 snapshot, 전체 phase 성공, 로컬 artifacts, target repository 불변성을 요구한다.

## Decisions

### D1. 공용 구현 원본은 `dot_agents`다

저장소가 이미 이 root를 에이전트 공용으로 정의하고 directory symlink의 실제 target으로 사용할 수 있으므로 선택한다. #97의 다른 스킬 이동은 포함하지 않는다.

### D2. Codex 발견 root는 live catalog로 정하고 `.agents`를 우선한다

두 후보의 존재는 발견 증거가 아니다. 서로 다른 nonce probe를 넣은 새 Codex 세션의 catalog 노출을 측정하고 cleanup 후 pre/post 동일성까지 확인한다. `.agents`가 발견되면 공용 payload 자체를 단일 Codex entrypoint로 써 duplicate skill name을 피하고, `.codex`만 발견될 때만 얇은 별도 entrypoint를 만든다.

### D3. payload 디렉터리는 통째로 심링크한다

측정으로 chezmoi v2.70.0의 directory symlink와 `Path.resolve().parents[1]` 이웃 탐색이 성립했다. 파일 단위 script 심링크는 schema/template 이웃 불변식을 깨므로 채택하지 않는다.

### D4. `tests/`는 설치 대상이다

이슈 완료 기준의 설치본 테스트를 실제로 수행하려면 설치본에 test가 있어야 한다. tests도 공용 payload에 한 번만 두고 각 entrypoint에서 directory link로 접근한다.

### D5. 기존 suite는 회귀 검사이며 신규 packaging/live gate가 충분성을 맡는다

목표 배치 probe에서 기존 122개가 모두 green이었던 실측 때문에 기존 suite를 구조 검증으로 해석하지 않는다. 공허했던 다섯 영역을 지명된 신규 case로 나누고 rendered/install/live gate를 별도로 둔다.

### D6. 실제 HOME migration은 backup-first target apply다

Claude 실디렉터리를 symlink 구조로 바꾸는 작업은 부분 실패 시 손실 위험이 있다. 전체 apply보다 dual-review target 한정 apply, type-aware backup, post-check, 자동 restore를 사용한다.

<!-- strict-only:start -->

### Threat and trust boundaries

신뢰하는 경계는 Git-tracked dual-review source, 검증된 chezmoi executable, temporary fixture의 자체 생성 Git history다. Codex/Claude model output, 기존 HOME의 설치 상태, CLI 인증 상태, issue/comment text는 검증 전에는 신뢰하지 않는다. model output은 기존 strict schema와 normalization을 통과해야 하며 discovery output도 전용 JSON schema, path 존재, candidate root 포함 여부를 검사한다.

외부 모델로 넘어가는 경계에는 target diff와 prompt가 있다. high-risk E2E는 합성 fixture만 사용한다. 실제 HOME으로 넘어가는 경계에는 chezmoi rendered files와 symlink가 있다. 격리 destination에서 같은 source를 먼저 render하고 symlink resolution과 managed set을 검사한다. 기존 HOME에서 새 배치로 넘어가는 경계는 backup/restore receipt와 pre/post digest로 묶는다.

### Authorization and tenant isolation

이 기능은 다중 tenant 서비스가 아니며 사용자별 서버 권한 모델이 없어 tenant isolation은 적용되지 않는다. 로컬 사용자 한 명의 HOME과 임시 fixture만 다룬다. 다만 model authentication은 각 CLI의 기존 로그인 context를 사용하며 credential을 읽거나 복제하거나 다른 profile로 전환하지 않는다. 파일 권한은 현재 사용자 범위이고 harness는 repository, temporary directory, dual-review 설치 target 외 경로를 쓰지 않는다.

### Migration, compatibility, and rollback

마이그레이션 순서는 discovery 결정 기록 → 공용 source/entrypoint 구성 → isolated render → source suite → 현 설치 type/digest backup → target-only apply → installed suite → dual-entrypoint E2E다. 기존 Claude invocation과 argument/frontmatter contract는 apply 전후 동일해야 한다. local state path와 report contract도 바꾸지 않는다.

rollback trigger는 apply nonzero, dangling symlink, selected target 불일치, installed suite failure, 한 entrypoint discovery 실패, source/deployment byte drift다. trigger가 발생하면 새 dual-review targets만 제거하고 backup을 원래 type과 bytes로 복원한다. 복원 검증이 끝날 때까지 backup을 유지한다. source rollback은 이 변경의 dual-review 관련 files를 이전 배치로 되돌린 뒤 같은 target-only chezmoi apply를 수행하는 별도 사용자 작업이며 자동 Git 쓰기는 하지 않는다.

### Failure recovery and observability

discovery receipt는 CLI version, timestamp, catalog candidate paths, selected target, decision reason을 기록한다. install receipt는 preflight result, backup path, touched targets, apply exit, post-check, restore result를 기록한다. live E2E receipt는 두 entrypoint command kind, installed skill path, shared script realpath, fixture snapshot digest, run directory, termination reason, producer/critique/synthesis status를 기록한다. credential과 full model transcript는 receipt에서 제외한다.

운영자는 nonzero command, incomplete termination reason, missing phase artifact, pre/post target mutation을 실패 신호로 본다. 자동 retry는 구조·인증 오류를 숨길 수 있으므로 하지 않는다. 인증 복구 후에는 실패한 live command를 새 fixture로 한 번 다시 실행하고 양쪽 결과를 모두 새 evidence로 판정한다.

### High-risk end-to-end verification

고위험 경로는 기존 Claude 설치 디렉터리를 새 symlink topology로 교체하고 두 도구가 실제 모델을 포함한 전체 pipeline을 호출하는 과정이다. CMD-5는 격리 preflight와 backup/rollback을 통과해야 실제 apply를 성공으로 인정한다. 그 다음 CMD-6이 설치 bytes와 test import를 검증하고 CMD-7이 합성 non-empty diff로 양쪽 전체 pipeline을 실행한다.

중단 조건은 discovery ambiguity, preflight failure, backup failure, apply/post-check failure, incomplete termination, 한쪽 entrypoint 미발견, snapshot 불일치, phase failure, fixture HEAD/status 변화다. CMD-5·CMD-6·CMD-7이 모두 현재 배치에서 PASS하기 전에는 완료로 판정하지 않는다.

### No production mutation confirmation

자동 workflow에는 production 시스템, GitHub, 원격 repository mutation이 없다. 계획된 mutation은 명시적 opt-in CMD-5가 수행하는 현재 사용자의 local dual-review 설치 target뿐이며 backup과 rollback 대상이다. live model 검증은 임시 Git fixture를 읽고 local run artifacts만 만든다. commit, push, merge, PR 게시, release, 원격 댓글·상태 변경은 수행하지 않는다.

<!-- strict-only:end -->
