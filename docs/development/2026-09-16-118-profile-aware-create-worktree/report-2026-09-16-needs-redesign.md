# Quality Goal Report

- Task ID: 20260916T003638Z-118-create-worktree에서-workspace-profile별-1ea3c575
- Mode: strict
- Status: NEEDS_REDESIGN
- Created: 2026-09-16
- Updated: 2026-09-16
- Source goal: #118 create-worktree에서 workspace profile별 작업 경로 생성·검증

## Classification

요청 모드 strict, risk scan 결과 strict. 요청이 결과보다 낮지 않으므로 downgrade 확인 절차는 발생하지 않았다.

- 인증/계정 격리 및 tenancy: workspace profile별 destination root와 provider별 account binding을 결정한다. 근거 `dot_config/ai-session/accounts.toml:1-49`, `dot_local/bin/executable_ai-session:625` `matching_allowed_scope`, `:733` `select_workspace_mapping`, `:788` `select_strict_account`.
- 보안 제어/비밀: `config_home`·token·이메일·account ID·인증 파일 경로의 출력 및 Git/tmux metadata 기록 금지. 근거 `dot_local/bin/executable_ai-session:69-89`, `docs/session-account-profiles.md:1-8`.
- 경로 격리 fail-closed: 문자열 prefix 비교 금지, path-component 단위 검증, `~/code/profile2-evil`·symlink escape·`..` 거부. 근거 `dot_local/bin/executable_ai-session:591` `directory_contains`.
- 되돌리기 어려운 조작: git worktree, 로컬 branch, git config, tmux window를 영속 생성한다.
- 이슈 라벨 `worktree`, `orchestration`, `quality-goal`, `enhancement`, `task`, `P2-medium` 은 보조 근거이며 위 risk scan이 단독으로 strict를 성립시킨다.

## Review history

### Spec (3/3 라운드, 최종 PASS)

| 라운드 | digest | verdict | score | blockers | 결과 |
|---|---|---|---|---|---|
| 1 | `8d6932ce…` | REVISE | 78 | `SPEC-001`, `SPEC-002` | High 2, Medium 3, Low 4 |
| 2 | `e02da8d1…` | REVISE | 83 | `SPEC-010` | 라운드 1의 9건 전부 resolved 확인, 개정이 만든 회귀 1건 신규 |
| 3 | `b57c4f7b…` | **PASS** | 96 | 없음 | 게이트 `passed: true`, open findings 0, Low advisory 1건(`SPEC-012`) |

라운드 3은 첫 응답이 `validate_review.py` 에서 "PASS reviews must not contain unverified evidence" 로 거부돼 `record-review-error` 로 검증 재시도 1회를 기록한 뒤 재호출했다. 재호출 응답은 동일 판정(PASS/96/`SPEC-012`)을 유지하면서 미실행 명령 항목을 확인 가능한 정적 관찰로 바꿔 검증을 통과했다. severity 변경이나 finding 신설은 없었다.

advisory readiness(Codex `gpt-5.6-sol`, read-only)는 세 라운드 모두 `READY`/100/C1~C8 pass 였고 어떤 상태 전이도 결정하지 않았다.

### Plan (2/2 라운드, 한도 소진)

| 라운드 | digest | verdict | score | blockers | 결과 |
|---|---|---|---|---|---|
| 1 | `fb0bc126…` | REVISE | 78 | `PLAN-001` | High 1, Medium 4, Low 2 |
| 2 | `aa9ef3fb…` | REVISE | 82 | `PLAN-008` | 라운드 1의 7건 전부 resolved 확인, 개정이 만든 회귀 1건 신규 + Medium 1, Low 2 |

Plan rubric은 "After round 2 without a passing gate, stop and record `NEEDS_REDESIGN`" 을 규정한다. 라운드 2가 통과하지 못했으므로 워크플로는 여기서 정지한다.

## Blocking-finding resolutions

| ID | 단계 | 해소 | 검증 |
|---|---|---|---|
| `SPEC-001` | Spec r1 | `task-handle` 의 권위 출처를 adapter dry-run 출력으로 단일화하고 backend 의 독립 계산 범위를 repository parent 로 한정 | Spec r2 리뷰가 "round-1 required resolution (option b) 는 문자 그대로 충족" 판정 |
| `SPEC-002` | Spec r1 | 오케스트레이터 실측 P1~P3 을 근거로 인용하고 cold-start 전용 `AC-49`+`CMD-16` 신설 | Spec r2 리뷰가 resolved 판정. 실측은 `coldstart-probe-evidence.md` |
| `SPEC-010` | Spec r2 | `destination_basename`(dry-run 출처)과 `workmux_handle`(`workmux list --json` exact-path 매칭 출처)로 두 식별자 분리 | Spec r3 리뷰가 (a)~(e) 다섯 항목 전부 resolved 판정. `task_handle` 잔존 0건 |
| `PLAN-001` | Plan r1 | 신규 `T0` 선행 태스크로 #103 전용 게이트 정리를 첫 중간 `CMD-12`/`CMD-13` 실행보다 앞에 배치 | Plan r2 리뷰가 `AC-43`/`AC-44` 기준 resolved 판정. 자기참조 폐쇄 주장은 오케스트레이터가 독립 검증 |
| `PLAN-008` | Plan r2 | **미해소.** 라운드 한도 소진 | 아래 참조 |

### `PLAN-008` (미해소 blocker)

승인된 Spec 의 `CMD-15` 는 `tests/test_create_worktree.py -k test_changed_path_allowlist -k test_no_persistent_or_external_mutation` 를 고정 명령으로 정한다(`spec.md:289`). 그러나 라운드 2 Plan 의 어떤 태스크도 `tests/test_create_worktree.py` 안에 `test_changed_path_allowlist` 를 작성하지 않는다. `T0` 는 기존 `tests/test_orchestrator_profiles.py` 의 동명 케이스만 수정하고, 라운드 1 의 `T9` 1단계에 있던 작성 지시가 라운드 2 에서 제거됐다.

오케스트레이터 독립 실측으로 그 결과를 확인했다. `unittest` 의 `-k` 가 0개를 선택하면 `NO TESTS RAN` 이지만 실패가 아니고, 하나만 매칭돼도 `OK` 다. 따라서 `CMD-15` 는 #118 소유 changed-path 단언이 한 번도 실행되지 않은 채 조용히 통과하며 `AC-46` 이 충족되지 않는다.

리뷰어가 제시한 `new_blocker_evidence` 도 확인했다. 라운드 1 스냅샷 `snapshots/plan-r1.md:161` 의 `T9` 1단계는 세 테스트를 함께 작성하도록 지시했고, 라운드 2 `plan.md:182` 가 그중 하나를 제거하면서 `T0` 를 근거로 들었다. 즉 이 공백은 라운드 2 개정이 새로 만든 회귀이며 라운드 1 시점에는 지적할 수 없었다.

## Plan approval

- Approval timestamp: 해당 없음
- Plan digest: 해당 없음

Plan 이 리뷰 게이트를 통과하지 못했으므로 `AWAITING_PLAN_APPROVAL` 에 도달하지 않았고 사용자 승인 게이트는 열리지 않았다. `approve-plan` 은 호출되지 않았다.

## Changed files

구현은 시작되지 않았다. base revision `72ad4f24e9df5919773cb877de01007f641ae163` 대비 tracked 변경은 **0건**이며, 워크트리에는 아래 문서 산출물만 untracked 로 존재한다.

| 경로 | 내용 |
|---|---|
| `docs/development/2026-09-16-118-profile-aware-create-worktree/spec.md` | 승인 가능 상태로 PASS 한 strict Spec. 요구사항 36개(R1.1~R10.3), AC 51개, 판정 명령 17개 |
| `docs/development/2026-09-16-118-profile-aware-create-worktree/spec-revision-notes.md` | Spec 라운드 2·3 개정 note |
| `docs/development/2026-09-16-118-profile-aware-create-worktree/plan.md` | 라운드 2 Plan. 태스크 T0~T9, 판정 명령 20개. `PLAN-008` 미해소 |
| `docs/development/2026-09-16-118-profile-aware-create-worktree/plan-revision-notes.md` | Plan 라운드 2 개정 note |
| `docs/development/2026-09-16-118-profile-aware-create-worktree/report.md` | 이 문서 |

`.claude/quality-state/` 의 런타임 상태는 `.gitignore:25` 로 무시된다. 소스 코드, 테스트, 배포 설정은 한 줄도 변경되지 않았다.

## Verification evidence

구현 검증은 수행되지 않았다. 구현이 시작되지 않았기 때문이다. 아래는 오케스트레이터가 **실제로 실행한** 명령이다.

| 명령 | exit | 근거 |
|---|---|---|
| `codex exec --model gpt-5.6-sol -c model_reasoning_effort="low" --sandbox read-only` (preflight) | 0 | 모델 응답 확인 |
| `python3 revision_check.py --artifact spec` (r1/r2/r3) | 0 / 0 / 0 | 빈 칸 0, 유령 참조 0 |
| `python3 revision_check.py --artifact plan --spec` (r1/r2) | 0 / 0 | 빈 칸 0 |
| `python3 validate_review.py validate` (spec r1/r2/r3-retry, plan r1/r2) | 0 | spec r3 첫 응답만 실패 후 재시도 통과 |
| `python3 validate_review.py gate` (spec r3) | 0 | `{"passed":true,"reasons":[]}` |
| `python3 validate_review.py gate` (plan r2) | 3 | `passed:false` — score·verdict·blocker·High |
| `python3 -m unittest discover -s tests -p 'test_*.py'` | **실패** | **Ran 97 tests, FAILED (failures=3)** — 구현 착수 전 baseline |
| `python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_changed_path_allowlist` | 실패 | stale allowlist 재현 |
| `workmux add --config <missing-parent> --dry-run` (임시 저장소) | 0 | P1: 상위 경로 부재에도 성공, 생성 0건 |
| `git worktree add` (임시 저장소, 없는 상위 경로) | 0 | P2: 상위 디렉터리 전체 암묵 생성 |
| `git worktree remove` (임시 저장소) | 0 | P3: 중간 빈 디렉터리 잔류 |
| `workmux add --config <literal worktree_dir> --dry-run` | 0 | Q1: dirname 이 override 값과 byte-identical |
| `workmux add --name X --dry-run` | 0 | Q2: `Handle:` 줄 출력 |
| `workmux list --json` (읽기 전용) | 0 | Q4: `handle` 과 `path` 둘 다 제공 |
| `python3 -m unittest -k <미존재 이름>` (임시 저장소) | 실패 아님 | `NO TESTS RAN` — `PLAN-008` 의 근거 |

### not configured 로 기록하는 검증 범주

- 타입 검사: 이 저장소에 타입 검사 설정이 없다. 확인한 파일 `.pre-commit-config.yaml`(gitleaks 훅만), `CLAUDE.md`, 저장소 루트 목록. **not configured.**
- 린트: 동일 근거로 린트 설정이 없다. **not configured.**
- 빌드: chezmoi source 저장소이며 빌드 단계가 없다. **not configured.**
- E2E: Spec 이 요구한 격리 tmux E2E 는 구현이 없어 실행되지 않았다. **미실행** (통과로 기록하지 않는다).

## Remaining advisory findings

| ID | severity | 내용 | 후속 |
|---|---|---|---|
| `SPEC-012` | Low | 어댑터가 등록을 마친 뒤 `R5.4` exact-path 조회 전에 실패하는 창의 보고 완전성 공백 | Plan 라운드 2 의 `T6`·`CMD-18` 이 실질적으로 닫았다고 Plan r2 리뷰가 판정 |
| `PLAN-009` | Medium | `CMD-20` 이 `tests/test_ai_session.py` 를 인자로 받지만 네 `-k` 이름이 모두 `tests/test_orchestrator_profiles.py` 에만 존재한다. 오케스트레이터가 직접 확인(각각 0건 / 1건). `T1` 이 추가하는 `test_ai_session.py` 케이스가 해당 태스크 안에서 red→green 으로 실행되지 않는다 | 재설계 시 반영 |
| `PLAN-010` | Low | `T1` 이 "옮길 심볼" 로 제시한 18개 중 8개(`parse_strict_registry`, `parse_legacy_registry`, `normalize_directory`, `resolve_with_missing_tail`, `validate_safe_component`, `validate_provider_scope_coherence`, `WorkspaceProfile`, `RepositoryPlacement`)가 현재 소스에 존재하지 않는다. 이동이 아니라 신규 작성이므로 작업량과 회귀 위험이 다르다 | 재설계 시 이동/신규를 분리 |
| `PLAN-011` | Low | `T2` 가 고정한 chezmoi 호출의 `--override-data-file`·`--config-format none` 플래그가 저장소 근거로 확인되지 않았다 | 설치된 `chezmoi execute-template --help` 로 확인 후 반영 |

### 이 이슈 범위 밖 follow-up (Report 기록 전용)

1. **저장소 테스트 스위트가 main 에서 red.** `tests/test_orchestrator_profiles.py` 의 #103 작업 전용 게이트 3건(`test_changed_path_allowlist`, `test_file_ownership`, `test_portable_cli_contract`)이 clean `origin/main` 에서 실패한다. 원인은 stale `BASE_REVISION`(#111/#114 머지에 고정, 이후 #105/#117 의 25개 경로 미반영)과 커밋된 적 없는 `docs/development/2026-09-15-103-orchestrator-permission-profiles/installed-cli-contract-evidence.md` 에 대한 하드 의존이다. 사용자 결정으로 이 정리는 #118 범위에 포함됐고 Plan `T0` 에 설계돼 있으나 구현은 시작되지 않았다. 상세는 `baseline-suite-evidence.md`.
2. **launcher 의 Claude auth verifier 필드 불일치.** 설치된 Claude Code 2.1.273 의 공식 JSON 필드(`loggedIn`/`authMethod`/`orgId`)와 구현 계약(`logged_in`/`auth_kind`/`subject_id`/`tenant_id`)이 어긋나고 `usage_status` 가 `usage_unknown` 으로 하드코딩돼 launcher 실행을 차단한다. 근거 `dot_local/libexec/executable_ai-session-verify-claude`. 사용자 지시에 따라 #118 구현 범위에서 제외했고 Spec 의 Non-goals 에도 명시돼 있다.
3. **profile2 config home 배포 공백.** `dot_claude/agents/*` 와 `dot_claude/skills/*` 가 `~/.claude/` 로만 배포되어 `CLAUDE_CONFIG_DIR` 가 다른 profile2 세션에서는 `quality-reviewer` 에이전트와 `quality-goal` 스킬을 쓸 수 없다. 이번 세션에서는 사용자 승인을 받아 `~/.local/share/ai-account-profiles/claude/profile2/agents/quality-reviewer.md` 하나만 저장소 source 와 byte-identical 하게 설치했다. #103 프로필 분리가 남긴 공백이며 #118 범위 밖이다.
4. **skill 문서와 설치된 helper 의 state root 불일치.** `SKILL.md` 는 `.Codex/quality-state` 를 지시하지만 설치된 `quality_state.py:74` 는 `STATE_DIR_RELATIVE = ".claude/quality-state"` 를 지문에서 제외한다. `.Codex/` 로 init 하면 스크립트가 "state files re-enter the workspace fingerprint" 경고를 낸다. `SKILL.md` 가 밝힌 근거와 `.gitignore:25` 를 따라 `.claude/quality-state` 를 사용했다. `.gitignore` 는 승인 범위 밖이라 수정하지 않았다.

## Final status

- Status: NEEDS_REDESIGN
- Machine-readable reason: PLAN_REVIEW_ROUND_LIMIT_REACHED_WITH_OPEN_BLOCKER (`PLAN-008`)

Spec 은 PASS 상태로 확정돼 있고(digest `b57c4f7bd74f594070a5a907bd79cc76b2d8c5c76497e3404af1ccb8cb180387`) 재사용 가능하다. 정지 지점은 Plan 한 곳이며, 미해소 blocker 는 `tests/test_create_worktree.py` 안에 `test_changed_path_allowlist` 를 작성하는 태스크 단계 하나가 빠진 것으로 좁게 한정된다. 소스 변경이 0건이므로 롤백할 대상이 없다.
