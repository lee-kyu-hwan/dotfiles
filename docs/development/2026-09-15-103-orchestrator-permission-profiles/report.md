# Quality Goal Report

- Task ID: 20260915T004047Z-103-codex-claude-계층별-오케스트레이터-모델-권한-프로필과-edc860c6
- Mode: strict
- Status: NEEDS_REDESIGN
- Created: 2026-09-15T00:40:47Z
- Updated: 2026-09-15
- Source goal: #103 Codex·Claude 계층별 오케스트레이터 모델·권한 프로필과 launcher를 구현하고 #111 account profile과 독립적으로 조합

## Classification

strict. 기록된 분류 근거는 다음과 같다.

- #103은 Codex·Claude launcher의 역할 기반 authorization과 권한 경계를 바꾼다.
- #103은 fail-closed sandbox 통제와 #111의 cross-account `CODEX_HOME`/`CLAUDE_CONFIG_DIR` 격리를 결합한다.
- #103은 identity-drift, scope, usage admission 실패가 launch를 차단하도록 요구한다.
- 이슈 라벨: orchestration, enhancement, task. multi-provider 외부 CLI launch 표면이다.

## Review history

Spec만 검토했고 Plan과 code 단계에는 진입하지 않았다. Spec 공식 라운드 한도는 3이며 2라운드를 소비했다.

| 라운드 | digest | verdict | score | blockers | 남은 findings |
|---|---|---|---|---|---|
| Spec 1 | `ab47238b…` | REVISE | 78 | SPEC-001, SPEC-002, SPEC-003 | SPEC-004 ~ SPEC-008은 후속 초안에서 해소 |
| Spec 2 | `4cfb9af6…` | REVISE | 87 | 없음 | SPEC-009, SPEC-010, SPEC-011 |
| Spec 3 | 실행하지 않음 | — | — | — | 남은 라운드 1개를 소비하지 않고 보존 |

3라운드는 두 번 시도되지 않았다. 최초 시도는 이전 Claude 세션의 session limit으로 리뷰 JSON이 생성되기 전에 실패했고(`spec-review-r3.error.txt`), 이는 공식 라운드로 계산하지 않았다. 이후 요구사항이 바뀌어 사용자가 남은 라운드를 기존 Spec에 쓰지 말라고 지시했다.

advisory readiness는 5회 기록했다. 시도 1·3·4·5는 모두 `READY`/100이고 시도 2는 `invocation_failed`다. 최종 시도 5는 digest `56efae02…`에서 C1~C8 전부 pass, findings 0, 근거 14건 전부 `verified: true`였다.

## Blocking-finding resolutions

| finding | severity | 해소 | 검증 근거 |
|---|---|---|---|
| SPEC-001 | 블로커(라운드 1) | `ai-session` 단일 status 분류기와 strict public JSON 계약으로 해소 | 라운드 2 리뷰가 blockers 0으로 확인 |
| SPEC-002 | 블로커(라운드 1) | Codex project config chain의 policy/unknown key pre-scan 차단으로 해소 | 라운드 2 리뷰가 blockers 0으로 확인 |
| SPEC-003 | 블로커(라운드 1) | pre-exec public record의 config-home 비노출 계약으로 해소 | 라운드 2 리뷰가 blockers 0으로 확인 |

라운드 2 이후 남은 SPEC-009·SPEC-010·SPEC-011은 블로커가 아니며, 라운드 3 공식 판정을 받지 못한 채 advisory readiness 시도 5에서 `resolved`로 판정됐다. 공식 확정은 이 실행에서 이루어지지 않았다.

## Plan approval

Plan 단계에 진입하지 않았으므로 승인이 없다.

- Approval timestamp: 없음
- Plan digest: 없음

## Changed files

이 실행은 저장소 구현 코드를 변경하지 않았다. 변경은 모두 미추적 문서 산출물과 gitignore된 실행 상태에 한정된다.

| 경로 | 내용 |
|---|---|
| `docs/development/2026-09-15-103-orchestrator-permission-profiles/spec.md` | strict Spec. 최종 digest `56efae02…`, 41 요구사항 R1.1~R8.5, 41 AC, 41 추적행, CMD-1~CMD-19 |
| `docs/development/2026-09-15-103-orchestrator-permission-profiles/spec-revision-notes.md` | 라운드 2·3 개정 노트. 최종 digest `91ea5b17…` |
| `docs/development/2026-09-15-103-orchestrator-permission-profiles/installed-cli-contract-evidence.md` | 설치본 Codex 0.154.0 / Claude Code 2.1.272의 help-only 전사와 사용자 보고 환경 사실 |
| `docs/development/2026-09-15-103-orchestrator-permission-profiles/environment-status.md` | 사용자가 적용한 #111 target과 계정 준비 상태 |
| `docs/development/2026-09-15-103-orchestrator-permission-profiles/readiness-evidence-spec-r2.md` | 라운드 2 readiness 근거 |
| `docs/development/2026-09-15-103-orchestrator-permission-profiles/readiness-evidence-spec-r3.md` | 라운드 3 readiness 근거. 시도 4와 시도 5를 모두 기록 |
| `docs/development/2026-09-15-103-orchestrator-permission-profiles/report.md` | 이 보고서 |
| `.claude/quality-state/20260915T004047Z-…-edc860c6/**` | gitignore된 실행 상태, 프롬프트, 결과, 실행 기록, 스냅샷, preservation bundle |

보존 대상 경로는 기준 revision `fcfb47ee2a0514518d150554ee491aae87d26d52` 대비 변경이 없다. `git status --porcelain`은 미추적 디렉터리 두 개만 보고하고 커밋·push·PR·merge는 0건이다.

## Verification evidence

구현 단계에 진입하지 않았으므로 구현 검증 범주는 실행하지 않았다. 실제로 실행한 결정적 명령은 다음과 같다.

| 명령 | exit | 근거 |
|---|---|---|
| `revision_check.py --artifact spec --current … --state …` | 0 | `revision-check-spec-r3-claude-default-unset.json`. `passed: true`, base `4cfb9af6…`, current `56efae02…`, 빈 칸 0, removed_ids 0, 누락 노트 행 0, 빈 노트 셀 0, touched 34 |
| `revision_check.py` (중간 점검) | 1 | `revision-check-spec-r3-partial-probe.json`. 노트 행 11개 누락을 보고했고 후속 개정으로 해소 |
| `git diff --check` | 0 | whitespace 오류 없음 |
| `codex --version` | 0 | `codex-cli 0.154.0` |
| `claude --version`, `claude --help`, `claude auth status --help` | 0 | `installed-cli-contract-evidence.md`. 인증·network 없이 help/version만 읽음 |
| `git status --porcelain` | 0 | 미추적 디렉터리 두 개만 |

- targeted tests: 실행하지 않음. 이 실행은 코드를 만들지 않았다.
- full suite: `python3 -m unittest -v tests/test_ai_session.py`가 이 goal의 baseline 점검으로 19/19 통과한 기록이 있다. 새 코드에 대한 실행은 없다.
- type check: `not configured`. 저장소 루트에 type checker 설정이 없고 `.pre-commit-config.yaml`에도 항목이 없다.
- lint: `not configured`. 같은 근거.
- build: `not configured`. chezmoi dotfiles 저장소로 빌드 산출물이 없다.
- E2E: 실행하지 않음. Spec이 정의한 고위험 E2E는 구현 단계 산출물이다.

## Execution watchdog

이 실행에서 정본 watchdog으로 감싼 마지막 호출은 formal round 3용 readiness다.

- Execution ID: readiness-spec-r3-claude-default-unset
- PID / PGID: 기록됨 / 기록됨
- Start / end / elapsed: 2026-09-15T03:55Z경 / 2026-09-15T04:00Z경 / 318.4s
- Child exit code: 0
- Result exists / schema validation: true / passed
- Start confirmed / watchdog reason: true / null
- Signals / preservation bundle: 없음 / 생성하지 않음
- Abort: 시도하지 않음, 후보 아님
- Reap: 시도하지 않음, 후보 아님
- Residual PIDs: 없음

같은 실행에서 author 호출 두 건이 `hard_timeout`으로 종료됐다. `spec-author-r3-codex-candidate`와 `spec-author-r4-claude-settings-and-default` 모두 900초에서 SIGTERM으로 중단됐고, preservation bundle을 만들었으며 `residual_pids`는 비어 있다. 두 경우 모두 부분 편집이 허용 범위 안에 있었고 이전 bytes는 preservation bundle에 보존됐다. 후속 bounded 호출 `spec-author-r4b-revision-notes`는 effort를 medium으로 낮춰 123초에 exit 0으로 완료했다.

## Watchdog restart budget

- Initial / remaining: author phase별 1 / 마지막 author phase는 소비하지 않음
- Exactly-once consumption: `spec-author-r3-codex-candidate`에서 1회 소비, `spec-author-r4-claude-settings-and-default`에서는 부모가 restart 대신 범위를 좁힌 후속 호출을 선택
- Restart attempted / stopped: false / false

## Remaining advisory findings

| finding | severity | 상태 | 영향과 후속 |
|---|---|---|---|
| SPEC-009 | Medium | 공식 미확정. readiness 시도 5가 resolved로 판정 | 설치본 CLI 근거, model availability 구분, Claude `usage_unknown` 차단 계약. 새 실행의 Spec에 그대로 이월한다 |
| SPEC-010 | Medium | 공식 미확정. readiness 시도 5가 resolved로 판정 | single-exec stdio/TTY 소유와 pre-exec public record 범위. 새 실행의 Spec에 이월한다 |
| SPEC-011 | Low | 공식 미확정. readiness 시도 5가 resolved로 판정 | exact 19-key credential scrub set. 새 실행의 Spec에 이월한다 |

사용자 정정 `USER-ACCOUNT-TOPOLOGY`, `USER-CODEX-CANDIDATE`, `USER-CLAUDE-DEFAULT-UNSET`, `USER-CLAUDE-SETTINGS-ISOLATION`은 이 Spec에 반영돼 있고 readiness가 file-and-line 근거로 확인했다. 이 중 `USER-CLAUDE-DEFAULT-UNSET`과 `USER-CLAUDE-SETTINGS-ISOLATION`은 새 정책에서도 그대로 유효하므로 새 Spec으로 이월한다.

후속 운영 사항 두 가지를 남긴다.

- `.claude/quality-state/`는 `.gitignore:25`로 무시되지만 `.claude/agents/`와 `.claude/settings.json`은 무시되지 않는다. 새 실행에서 project-level 파일을 추가할 때 변경 경로 allowlist를 오염시키지 않도록 주의한다.
- 이 pane은 `CLAUDE_CONFIG_DIR`가 dotfiles 프로필로 설정돼 있고 그 프로필에 `agents/` 디렉터리가 없어 공식 `quality-reviewer`(Opus/high, read-only) 에이전트를 띄울 수 없다. 이는 `USER-CLAUDE-SETTINGS-ISOLATION`이 서술한 격리 회귀가 이 workflow 자체에 나타난 사례이며, 새 실행의 공식 리뷰 전에 해결이 필요하다.

## Final status

기존 요구사항이 repository identity 중심 account 선택을 전제했으나, 2026-09-15 갱신된 이슈 #103과 #111이 이를 account workspace directory 중심 정책과 cross-profile worktree 이동 계약으로 대체했다. 이는 Spec의 선택 축 자체를 바꾸는 material redesign이므로 남은 공식 라운드 하나를 기존 Spec에 쓰지 않고 이 실행을 재설계로 종료한다. 모든 산출물과 실행 상태는 새 실행의 prior evidence로 보존한다.

- Status: NEEDS_REDESIGN
- Machine-readable reason: REQUIREMENTS_REDESIGN:ACCOUNT_WORKSPACE_DIRECTORY_POLICY
