# Quality Goal Report

- Task ID: 20260915T045020Z-103-account-workspace-directory-기반-codex-0b1ffbac
- Mode: strict
- Status: CODE_REVIEW
- Created: 2026-09-15T04:50:20Z
- Updated: 2026-09-15
- Source goal: #103 account workspace directory 기반 Codex·Claude 역할·계정 프로필 launcher와 cross-profile worktree 이동 계약을 구현

## Classification

strict. 기록된 근거는 여섯 가지다.

- #103과 #111이 Codex·Claude launcher의 역할 기반 authorization과 계정 선택 경계를 동시에 바꾼다.
- account workspace directory가 계정 선택 경계가 되고 filesystem permission 경계와 분리되어야 하므로 권한 상승 표면이 새로 생긴다.
- cross-profile worktree 이동이 Git metadata 교차 접근, stale binding, stale `PWD`, 새 `binding_generation`을 fail-closed로 다뤄야 한다.
- `CLAUDE_CONFIG_DIR` 격리가 credential뿐 아니라 settings·plugin·session transcript를 분리하므로 복원 계약을 잘못 만들면 credential 복제 유혹이 생긴다.
- 두 root 밖 Claude 자동 실행과 미로그인·usage 미확인 계정은 provider 실행 전에 차단해야 한다.
- 이슈 라벨: orchestration, enhancement, task, tmux, worktree. multi-provider 외부 CLI launch 표면이다.

## Review history

### Spec, 한도 3라운드 중 2라운드 사용

| 라운드 | digest | verdict | score | blockers |
|---|---|---|---|---|
| 1 | `ffa1251b…` | REVISE | 84 | `SPEC-001` |
| 2 | `db0eb8f6…` | **PASS** | 93 | 없음 |

advisory readiness는 네 번 실행해 두 개의 High 결함을 공식 라운드 소비 전에 걸러냈다. `READY-001`은 두 Claude root 밖 fail-closed 계약과 "reviewed mapping" 예외가 모순된 문제였고, `READY-002`는 `claude-profile2`의 home 경로가 registry에 존재해야 하는데 모든 config-home 경로 노출을 금지해 구현 불가능했던 자기모순이었다. 한 번은 `activity_stall`로 중단되어 phase restart 예산으로 재시작했다.

### Plan, 한도 2라운드 모두 사용

| 라운드 | digest | verdict | score | blockers |
|---|---|---|---|---|
| 1 | `d0789c3f…` | REVISE | 83 | `PLAN-001` |
| 2 | `41393f8a…` | **PASS** | 93 | 없음 |

독립 대칭 점검을 두 번 돌려 공식 라운드 전에 High 다섯 건을 제거했다. 명목상 AC 소유, 가짜 test-first와 역방향 의존, authorization을 dispatcher에 배정한 오류, 기존 회귀 테스트와 legacy 정책의 충돌, 실행 불가능한 rollback이다.

## Blocking-finding resolutions

| finding | 해소 | 검증 근거 |
|---|---|---|
| `SPEC-001` | 배포된 `claude-dotfiles`·`codex-dotfiles` 항목을 byte 보존·non-mappable·non-selectable legacy record로 확정하고, 새 스키마에 `defaults`·`scope_bindings`가 없으며 path mapping이 이를 대체함을 명시. `AC-45`가 판정 가능해지도록 필수 선언과 보존 record의 속성을 열거 | Spec 리뷰 라운드 2가 resolved로 확인 |
| `PLAN-001` | `test_account_registry_schema`와 `test_path_selection_regression`을 각각 소유 태스크의 선작성 테스트·red assertion·focused green selector에 배정하고, 모든 `CMD` 행의 selector가 어떤 태스크에서든 생성되어야 하며 `Ran 0 tests`는 green 증거가 아니라는 전역 제약을 추가 | Plan 리뷰 라운드 2가 resolved로 확인. 오케스트레이터 전수 검사: CMD 표의 79개 distinct selector 전부 태스크 본문에 존재 |

`SPEC-002`~`SPEC-007`, `PLAN-002`도 같은 라운드에서 모두 resolved로 확인됐다.

## Plan approval

- Approval timestamp: `plan_approval` 기록 참조
- Plan digest: `41393f8a48be69c4ac5f6868d7dd6cda63cf0ec3b8f67a8258c38db49ad9fddd`
- 근거: 사용자가 사전 위임했다. 상세와 정확한 승인 대상은 `.claude/quality-state/…/plan-approval-record.md`에 기록했다.

## Changed files

| 경로 | 상태 | 내용 |
|---|---|---|
| `dot_config/ai-session/accounts.toml` | 수정 | strict active 스키마, `workspace_directory_mappings`, task/session binding과 generation, opaque `legacy_records` |
| `dot_local/bin/executable_ai-session` | 수정 | 경로 전용 선택 엔진, directory-only authorization, exact 19-key scrub, home mode, 단일 실패 분류기, Git write allow set |
| `tests/test_ai_session.py` | 수정 | `test_deployed_registry_selects_provider_specific_dotfiles_profiles` 한 메서드만 새 배포 현실로 교체. 나머지 18개 메서드 무변경 |
| `dot_config/ai-session/roles.toml` | 신규 | strict role 스키마, 네 role의 model·effort·permission·capability, CLI 호환 범위 |
| `dot_config/ai-session/skill-policies.toml` | 신규 | 역할별 Skill·plugin allow/deny |
| `dot_claude/settings.json` | 신규 | 비밀 없는 공통 settings 레이어 |
| `dot_config/ai-session/claude/*.settings.json` | 신규 | 네 role settings |
| `dot_config/ai-session/instructions/*.md` | 신규 | provider·role별 additive instruction 여덟 개 |
| `dot_local/bin/executable_ai-role-session` | 신규 | role dispatcher |
| `dot_local/bin/symlink_ai-*` | 신규 | 여덟 진입점 |
| `dot_local/libexec/**` | 신규 | provider verifier, shared identity parser, enrollment helper |
| `tests/test_orchestrator_profiles.py` | 신규 | portable 계약 스위트 |
| `tests/check_installed_orchestrator_cli_contract.py` | 신규 | 이 Mac의 help-only release gate |
| `tests/fixtures/**` | 신규 | synthetic home, fake 실행 파일, fake `workmux` |
| `docs/orchestrator-permission-profiles.md` | 신규 | 운영·migration 문서 |

기준 revision `fcfb47ee2a0514518d150554ee491aae87d26d52` 대비 `dot_claude/skills/create-worktree/**`, `dot_config/workmux/**`, `dot_tmux.conf.tmpl`, `dot_zshrc.tmpl`은 byte-identical이다. 사전 존재하던 미추적 경로 `.claude/profile-migration/`와 `docs/development/2026-09-15-103-orchestrator-permission-profiles/`는 초기 dirty path로 기록돼 한 번도 수정·되돌림·삭제되지 않았다.

## Verification evidence

전사는 `.claude/quality-state/…/verification/transcript.txt`에 있다.

| 명령 | exit | 근거 |
|---|---|---|
| CMD-12 preserved-path diff | 0 | 네 보존 대상이 기준 revision과 byte-identical |
| CMD-13 portable suites | 0 | 96 tests, OK |
| CMD-14 repository discovery + `git diff --check` | 0 | 96 tests OK, whitespace 오류 없음 |
| CMD-9 installed release gate | 0 | help-only, 인증·network 없음 |
| CMD-11 network-denied high-risk E2E | 0 | 1 test, OK |
| CMD-15 sensitive-data hygiene 외 3종 | 0 | 4 tests, OK |
| changed-path allowlist, file ownership | 0 | 2 tests, OK |

카테고리별 상태는 다음과 같다.

- targeted tests: passed
- full suite: passed, 96 tests
- type check: `not configured`. 저장소 루트와 `.pre-commit-config.yaml`에 type checker 설정이 없다
- lint: `not configured`. 같은 근거
- build: `not configured`. 빌드 산출물이 없는 chezmoi dotfiles 저장소다
- E2E: passed, network 차단 고위험 경로

## Execution watchdog

정본 watchdog으로 감싼 열여섯 번의 구현 실행 기록이다.

| execution | elapsed | child exit | watchdog reason | result |
|---|---|---|---|---|
| `impl-t1` | 430s | 0 | - | yes |
| `impl-t2` | 812s | 0 | - | yes |
| `impl-t3` | 405s | 1 | `child_exited_no_result` | no |
| `impl-t3-resume` | 588s | 0 | - | yes |
| `impl-t4` | 790s | 0 | - | yes |
| `impl-t5` | 901s | unknown | `hard_timeout` | no |
| `impl-t6` | 784s | 0 | - | yes |
| `impl-t7` | 835s | 0 | - | yes |
| `impl-t8` | 474s | 0 | - | yes |
| `impl-t9` | 780s | 0 | - | yes |
| `impl-t10` | 698s | 0 | - | yes |
| `impl-t11` | 515s | 0 | - | yes |
| `impl-t12` | 441s | 0 | - | yes |
| `impl-t13` | 900s | unknown | `hard_timeout` | no |
| `impl-t14` | 434s | 0 | - | yes |
| `impl-t15` | 900s | unknown | `hard_timeout` | no |

모든 실행에서 `residual_pids`는 비어 있다. `hard_timeout` 세 건은 SIGTERM으로 중단되고 preservation bundle을 만들었으며, 잃은 것은 작업자의 자기보고 JSON뿐이다. 세 경우 모두 산출물은 완성돼 있었고 green 여부는 오케스트레이터가 독립 실행으로 확인했다.

`impl-t3`은 provider 사용량 한도로 결과 없이 종료했다. 원문은 "You've hit your usage limit." 이었다. 모델을 임의로 대체하지 않고 `IMPLEMENTING` 단계를 유지한 채 사용자에게 보고했고, 사용자 지시로 재시도한 `impl-t3-resume`이 기존 RED 테스트를 보존한 채 구현만 추가해 성공했다.

## Watchdog restart budget

- Initial / remaining: 구현 phase별 1 / 소비 없음
- Exactly-once consumption: 구현 단계에서는 0회. readiness phase에서 `activity_stall` 재시작으로 1회 소비
- Restart attempted / stopped: false / false. `hard_timeout` 세 건은 산출물이 완성돼 재시작 대신 독립 검증으로 확인했다

## Remaining advisory findings

| 항목 | 성격 | 후속 |
|---|---|---|
| registry의 `task_bindings`·`session_bindings` | #103이 요구하는 "#94/#95 공통 등록 계약, 별도 중복 레지스트리 금지"와의 긴장 | account-binding 메타데이터로 읽히며, #94 또는 #95가 단일 권위 저장소를 정의하면 그리로 이동한다. `scope-audit-2026-09-15-1233.md`와 운영 문서에 기록 |
| `.claude/agents/`와 `.claude/settings.json`이 gitignore 대상 아님 | 위생 | `.claude/quality-state/`만 무시된다. 이후 project-level 파일 추가 시 변경 경로 allowlist 오염에 주의 |
| 이 세션의 공식 리뷰어 경로 | 편차 | 아래 참조 |

## Deviations

- **리뷰어 에이전트 타입.** 이 pane은 `CLAUDE_CONFIG_DIR`가 분리 프로필로 설정돼 있고 그 프로필에 `agents/` 디렉터리가 없어 저장소의 `quality-reviewer` 에이전트가 등록되지 않았다. 저장소의 비밀 없는 에이전트 정의를 프로필에 배치했지만 에이전트 목록은 세션 시작 시 고정되므로 이 세션에는 반영되지 않았다. 따라서 공식 Spec·Plan 리뷰는 모델을 Opus로 유지한 채 `general-purpose` 타입으로 실행하고, 저장소의 `quality-reviewer.md` 정의를 직접 읽고 따르도록 지시했으며, fresh context·one-shot·unnamed 성질과 리뷰 계약 입력을 동일하게 유지했다. 잃은 것은 도구 수준의 강제 읽기 전용성이며, 프롬프트의 hard constraint와 리뷰 전후 artifact digest 대조로 보완했다. 네 번의 리뷰 모두 digest가 불변이었다.
- **`impl-t1`의 일시적 설치본 실행.** 작업자가 중간 green 시도에서 fake executable의 shebang을 들여쓰기해 설치본 `ai-session`이 대신 실행됐다. 해당 스크립트는 Python import 단계에서 종료되어 selector·verifier·provider·auth·network·process 변경 이전에 멈췄다. fixture 생성기를 고쳐 재검증했고, 이후 모든 태스크 프롬프트에 설치본 실행 금지와 shebang 요건을 명시했다.
- **T5·T13·T15의 `result.json` 부재.** 세 실행이 900초 hard timeout에 걸려 자기보고 JSON을 남기지 못했다. 산출물과 green은 오케스트레이터가 독립 실행으로 확인했다.
- **Plan 형식 수정 두 건을 오케스트레이터가 직접 수행.** 판정 명령이 표가 아니라 번호 목록이어서 `CMD` ID가 해석되지 않았고, `대상 AC:` 줄에 판정수단 토큰이 없었다. `SKILL.md`의 Codex-author 요구는 Spec 전용이므로 Plan의 기계적 형식 수정은 직접 처리해 라운드 예산을 아꼈다.

## Code review round 1 and its fixes

Round 1 returned `REVISE`, score 70, with three High blockers and one Medium finding. All four were resolved before round 2.

| finding | 내용 | 해소 |
|---|---|---|
| `CODE-001` High | untrusted settings pre-scan이 dispatcher 환경의 `CLAUDE_CONFIG_DIR`를 읽어, `ai-session`이 선택·scrub한 **실제 계정 home을 한 번도 검사하지 않았다.** 기존 테스트는 프로덕션이 만들 수 없는 상태를 주입해 통과하고 있었다 | 계정 home 검사를 `prescan_selected_claude_home()`으로 분리해 **admitted phase**에서 실행하도록 이동. project·local 검사는 기존 위치 유지 |
| `CODE-002` High | `roles.toml`이 chezmoi **source** 경로를 기록해 배포 레이아웃에서는 `$HOME/dot_claude/...`로 해석돼 존재하지 않았고, `.chezmoiignore`가 `.claude/settings.json`을 제외해 공통 레이어가 애초에 배포되지 않았다. 배포 후 모든 launcher가 `blocked_policy`로 실행 불가 상태였다 | `roles.toml`을 배포 대상 상대 경로로 바꾸고 `layout_relative_path` 헬퍼로 소스·배포 양쪽을 해석. `.chezmoiignore`에서 해당 제외를 제거해 공통 레이어가 실제로 배포되게 함. 렌더된 home에서 dispatcher를 실행하는 테스트 추가 |
| `CODE-003` High | `blocked_binding`이 `ai-session`에서 exit 2로 나와 Spec이 `blocked_contract`에 배정한 코드와 충돌했고, dispatcher는 같은 상태를 exit 4로 내보내 한 public status가 두 exit code를 가졌다 | `error_status`가 `blocked_binding`·`blocked_permission`에 exit 4를 반환하도록 수정하고 exit 2를 단언하던 fixture 갱신 |
| `CODE-004` Medium | 검토된 settings에 미렌더 `{{ .chezmoi.homeDir }}` 템플릿이 남아, `--settings`로 직접 전달되는 문서의 notification hook이 리터럴 중괄호로 시작하는 명령을 실행하게 되어 있었다 | 템플릿 제거 |

`CODE-002`는 이 세션이 `chezmoi apply`를 수행하기 직전에 잡혔다. 소스 트리 안에서는 96개 테스트가 모두 통과하는데 배포된 launcher는 전부 실행 불가였으므로, 적용했다면 실사용이 깨졌을 것이다. 모든 테스트가 `cwd=ROOT`로 소스 트리에서만 실행되던 것이 원인이고, 렌더된 home에서 실행하는 테스트를 추가해 같은 부류를 닫았다.

`.chezmoiignore` 변경은 의도적 편차다. 기존 주석은 공통 설정을 `docs/claude-settings-reference.json`에 두고 새 머신에서 수동 입력하라는 것이었으나, 이번 작업이 검토된 공통 레이어를 배포 대상으로 요구하므로 제외를 제거하고 주석을 갱신했다. 그 source 파일에는 머신 고유 값이나 비밀을 넣지 않는다는 제약은 그대로다.

### Re-verification after the fixes

전사는 `.claude/quality-state/…/verification/transcript-r2.txt`에 있다. CMD-12 보존 경로 byte-identical, CMD-13·CMD-14 96 tests OK, `git diff --check` exit 0, CMD-9 release gate ok, CMD-11 network 차단 E2E OK, CMD-15 위생 4 tests OK, CMD-10 render OK.

## Code review round 2 and its fixes

Round 2 returned `REVISE`, score 80, with one High blocker and two lower findings.

| finding | 내용 | 해소 |
|---|---|---|
| `CODE-005` High | 라운드 1의 두 수정이 배포 레이아웃에서 충돌했다. `claude-profile1`은 provider-default라 pre-scan이 `~/.claude`로 폴백하는데, `.chezmoiignore` 제외를 제거한 탓에 policy를 담은 공통 레이어가 정확히 그 경로로 렌더되어 모든 `ai-claude*` 실행이 `blocked_policy`로 차단될 상태였다 | Spec R4.5가 account-home settings를 예외 없이 untrusted로 규정하므로, 공통 레이어를 계정 home에 배포하지 않도록 제외를 복원하고 composition source로만 유지. 렌더된 home에서 stub이 아닌 실제 `ai-session`→`admitted_main` 경로로 provider-default 실행을 검증하는 테스트 추가 |
| `CODE-007` Medium | account-home 검사가 `admitted_main`으로 이동하면서 verifier가 미검증 home을 대상으로 provider 바이너리를 한 번 실행한 뒤에 검사가 일어났다 | 검사를 `ai-session`의 child environment 구성과 `verify_admission` 사이로 옮겨 verifier 이전에 차단. admitted 단계의 방어도 유지 |
| `CODE-006` Low | `blocked_contract`가 `ai-session`에서 exit 2, dispatcher에서 exit 4로 한 status에 두 exit code | dispatcher를 exit 2로 통일 |

`CODE-005`는 내가 라운드 1에서 지시한 두 수정이 서로 부딪힌 사례다. 각각은 옳았으나 교차 검증하는 테스트가 없어 green 스위트를 통과했다. 렌더 테스트가 `ai-session`을 stub해 `admitted_main`에 도달하지 않은 것이 원인이고, 실제 경로를 타는 테스트를 추가해 같은 부류를 닫았다.

### 운영자에게 남는 필수 migration 단계

현재 `~/.claude/settings.json`에는 `env`, `permissions`, `hooks`가 있다. Spec R4.5 아래에서 이 파일은 untrusted account-home 입력이므로, **그 내용을 검토된 공통 레이어로 옮기고 계정 home 파일을 비우거나 benign allowlist(`$schema`, `spinnerTipsEnabled`, `theme`) 수준으로 줄이기 전까지 `claude-profile1` 실행은 fail closed한다.** 이 workflow는 실제 home을 수정하지 않았고, 절차는 `docs/orchestrator-permission-profiles.md`에 기록했다. `chezmoi apply` 전에 사용자 확인이 필요한 사항이다.

구현 중 관측된 편차 하나를 기록한다. 첫 full-suite 실행에서 테스트 환경이 실제 `HOME`을 상속해 새 account-home pre-scan이 실제 `~/.claude/settings.json`을 검사하고 `blocked_policy`로 종료했다. 내용은 출력·보존되지 않았고 어떤 mutation도 없었다. 이후 모든 테스트 subprocess의 `HOME`을 임시 디렉터리로 격리하고 전체 검증을 다시 수행했다.

## Final status

- Status: CODE_REVIEW 라운드 3 대기
- Machine-readable reason: `CODE_REVIEW_ROUND_2_FIXES_APPLIED`
