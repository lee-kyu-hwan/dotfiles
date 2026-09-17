# Quality Goal Report

- Task ID: 20260916T025114Z-111-claude-code-2-1-273-auth-status-호환성-f224ab4d
- Mode: strict
- Status: COMPLETED
- Created: 2026-09-16
- Updated: 2026-09-16
- Source goal: #111 Claude Code 2.1.273 auth status 호환성, identity enrollment/verifier 계약, profile2 비밀 없는 공용 스킬 배포, profile setup/admission backend 계약을 구현한다

## Classification

`strict`. 사용자가 `--mode=strict` 를 명시했고 `routing-rules.md` 의 risk scan 결과가 동일해
downgrade 확인 절차가 불필요했다. 트리거와 저장소 근거는 다음과 같다.

| strict 트리거 | 근거 |
|---|---|
| 인증·권한·테넌시 | `dot_local/bin/executable_ai-session:1184-1237` 의 `classify_verifier_payload` 가 identity·usage admission 을 fail-closed 판정 |
| PII·보안 통제·비밀 | 실측한 `claude auth status --json` 키에 `email`·`orgId`·`orgName` 포함 |
| 외부 API 호환성 | 공식 `loggedIn`/`authMethod`/`orgId` 와 배포된 verifier 의 `logged_in`/`auth_kind`/`subject_id`/`tenant_id` 불일치 |
| 광범위 실패 모드 | `executable_ai-session:1233-1234` 가 `usage_unknown` 을 무조건 차단해 Claude role launcher 가 기동 불가 |

이슈 라벨(enhancement·task·orchestration·worktree·tmux)은 증거로 인용했으나 risk scan 결과를 대체하지 않았다.

## Review history

| 산출물 | 라운드 | 점수 | 판정 | 비고 |
|---|---:|---:|---|---|
| Spec | 1 (1차 응답) | 89 | PASS 였으나 **출력 검증 거부** | `PASS reviews must not contain unverified evidence`. `record-review-error` 로 기록, 라운드 미소비 |
| Spec | 1 (재시도) | 95 | **PASS** | blocker 0, 근거 37건 전부 verified |
| Spec | 2 | 93 | **PASS** | 승인 후 전제 오류(SCOPE-001) 개정. blocker 0 |
| Plan | 1 | 88 | **PASS** | blocker 0, Medium 3 · Low 3 |
| Plan | 2 | 92 | **PASS** | Spec r2 반영 + SPEC-004 확정. blocker 0 |
| Code | 1 | 76 | **REVISE** | blocker `CODE-001` (High) |
| Code | 2 | 88 | **PASS** | blocker 0, Low 2 잔존 |

라운드 소비: spec 2/3, plan 2/2, code 2/3.

### 라운드 사이에 바뀐 findings

- **Spec r1 → r2**: `SPEC-003` 해소. `SPEC-001`·`SPEC-002` 는 Plan 이 권위를 갖는 것으로 판정돼 Spec 층에서는 Medium/Low 자문으로 유지. `SPEC-004`(duplicate 비교 입력 경로 미확정) 신설.
- **Plan r1 → r2**: `PLAN-001`·`PLAN-002`·`PLAN-003` 해소, `SPEC-004` 확정. `PLAN-007`(identity root 불일치) 신설 — Medium.
- **Code r1 → r2**: `CODE-001`~`CODE-006`·`CODE-008` 해소. `CODE-007` 부분 해소로 Low 유지, `CODE-009` 신설 Low.

### 승인 후 범위 변경 (SCOPE-001)

`IMPLEMENTING` 단계에서 **승인된 Spec 의 전제 오류**가 발견됐다. canonical identity
(`authMethod`+`orgId`+`subscriptionType`)가 **같은 조직의 서로 다른 사용자를 구분하지 못한다**.
합성 입력으로 실증했다(alice/bob 동일 digest `59cfbeb90da8da81…`).

`quality-goal` scope-change 절차대로 `invalidate-verification` 후
`IMPLEMENTING → SPEC_REVIEW` 로 복귀했다. 구현 변경은 전부 보존했다(handoff patch 2,764줄).

1차 재설계안(email 기반 HMAC subject fingerprint)은 **사용자의 read-only 실측으로 폐기**됐다.
두 Claude profile 이 **같은 email, 다른 orgId** 를 써서 email 지문이 두 profile 을
중복으로 오판하기 때문이다. 확정된 설계는 `scope-change-2026-09-16.md` 에 있다.

## Blocking-finding resolutions

| finding | 해소 | 검증 근거 |
|---|---|---|
| `CODE-001` (High) | `test_profile2_chezmoi_diff_redaction` 이 자기 생성 문자열만 검사해 **구조적으로 실패 불가**였다. `git ls-files --cached --others --exclude-standard` 로 실제 Git 관리 source 를 열거하고 source·target **파일 바이트**를 sentinel 검사하도록 재작성. 무의미하던 `assertFalse(access_sentinel.exists())` 제거 후 경로 봉쇄 검증으로 대체 | **오케스트레이터 결함 주입 실증**: mirror 파일에 sentinel 삽입 → `FAILED (failures=1)`, exit 1. 복원 후 digest byte-identical, exit 0 (`verification-run-r2.log:18-54`) |

Spec·Plan 리뷰에서는 blocker 가 발생하지 않았다.

## Plan approval

- Approval timestamp: `2026-09-16T11:22:42Z`
- Plan digest: `1ca020c00a89171ad931d021f9c24fc74f08637496a279f8c529ba778df36cd1`

최초 승인(`2026-09-16T07:39:14Z`, digest `91a6a067…`)은 SCOPE-001 개정으로 무효화됐고,
개정본 승인 전에 변경 내역 7항목(신설 요구사항 R6.1~R6.4, AC 20→26개, `matched` 의미 축소,
신설 차단 상태 2종, 신설 env 와 함수, Keychain 수동 게이트)을 사용자에게 명시했다.

## Changed files

추적 파일 14건 (`git diff HEAD`, +2144 / −510 기준 최종 3,690줄 diff):

| 파일 | 의도한 변경 |
|---|---|
| `dot_config/ai-session/accounts.toml` | strict registry v2 (`schema_version=2`, `contract_id=…-v2`), account 별 `identity_contract`·`usage_contract` 선언 |
| `dot_config/ai-session/roles.toml` | 네 role 의 `registry_contract` v2 상향 |
| `dot_local/bin/executable_ai-session` | registry v2 파서, `AdmissionDecision`+`failure_reason`, `active_claude_identity_digest_paths()`, `decision_to_launch_error()`, 읽기 전용 `status` subcommand, launch·status 양쪽 `--accept-usage-unknown` |
| `dot_local/bin/executable_ai-role-session` | `ROLE_CONTRACT_ID` v2 상향 |
| `dot_local/libexec/ai_session_identity.py` | schema-2 canonical projection, v1(65B)/v2(68B) digest 구분, `find_duplicate_enrollment()` |
| `dot_local/libexec/executable_ai-session-verify-claude` | 공식 camelCase 투영, `identity_unverifiable`, `duplicate_mapping` |
| `dot_local/libexec/executable_ai-session-verify-codex` | `checks["auth.credentials"]` 중첩 구조 투영, `identity_status="unavailable"` |
| `dot_local/libexec/executable_ai-session-enroll-identity` | Claude 전용 v2 enrollment, 중복 매핑 pre-write 차단 |
| `.chezmoiignore` | profile2 target deny pattern, `__pycache__`·`*.pyc` 제외 |
| `tests/test_ai_session.py` | 19 → 29건 |
| `tests/test_orchestrator_profiles.py` | 78 → 92건 |
| `tests/check_installed_orchestrator_cli_contract.py` | stale #103 evidence 경로 교체 |
| `docs/session-account-profiles.md` | v2 계약·조직 컨텍스트 의미·한계·수동 게이트 문서화 |
| `docs/orchestrator-permission-profiles.md` | status↔launch 대응표, profile2 경계, 복구 절차 |

신규 파일: `dot_local/share/ai-account-profiles/claude/profile2/**` mirror 45건
(`agents/quality-reviewer.md` 1 + `skills/quality-goal/**` 44), 이 디렉터리의 문서 8건.

## Verification evidence

오케스트레이터가 직접 실행한 결과다. Codex 주장을 그대로 받지 않았다.

| 명령 | exit | 결과 |
|---|---:|---|
| `python3 tests/test_ai_session.py` | **0** | `Ran 29 tests in 18.636s` — OK |
| `python3 tests/test_orchestrator_profiles.py` | **0** | `Ran 92 tests in 40.875s` — OK |

baseline(`72ad4f2`)은 CMD-1 19건 OK, CMD-2 **78건 중 3 실패**
(`test_changed_path_allowlist`, `test_file_ownership`, `test_portable_cli_contract`)였고
stale #103 fixture 가 원인이었다. T1 에서 해소됐고 재발하지 않았다.

**결함 주입 검증** (CODE-001 해소 실증):

| 단계 | 관측 |
|---|---|
| 주입 전 digest | `90bf2f8f12768d350224d062c1dde8a53ce9dc47367e5e5809171c45e6498d27` |
| sentinel 삽입 후 | 테스트 `FAILED (failures=1)`, exit 1 |
| 복원 후 digest | `90bf2f8f12768d350224d062c1dde8a53ce9dc47367e5e5809171c45e6498d27` — byte-identical |
| 복원 후 테스트 | exit 0 |

### 미구성 검증 범주 — 통과로 표시하지 않음

| 범주 | 상태 | 확인한 저장소 근거 |
|---|---|---|
| type check | **not configured** | `pyproject.toml`·`setup.cfg`·`tox.ini`·`mypy.ini` 부재 |
| build | **not configured** | 빌드 정의 파일 부재 |
| CI | **not configured** | `.github/workflows` 부재 |
| lint | **not configured (판정 명령 아님)** | `.pre-commit-config.yaml` 에 `gitleaks` 훅 하나뿐 |
| 자동 E2E | **통과** | CMD-2 의 `test_high_risk_e2e` (synthetic·live-action sentinel 기반) |
| **Keychain 동시 실행 수동 게이트 (AC-26)** | **미실행** | 아래 참조 |

### AC-26 수동 게이트 — 미실행

사람이 전경에서 두 Claude profile 을 동시 실행해 실행 중 각 조직 컨텍스트를
read-only 로 재확인하는 절차다. 이 워크플로는 실제 login/logout·account 전환을 금지하므로
수행하지 않았다. 절차는 두 운영 문서에 기록됐고 **PASS 전에는 완료로 판정하지 않는다.**
자동 테스트가 이 게이트를 대체하지 않으며 이를 완료로 판정하는 코드도 없다.

### 경계 준수

- 승인 Spec `471cce1a…`, Plan `1ca020c0…` digest 불변
- `#118` 소유 경로 변경 **0건** (tracked·untracked 모두)
- HEAD `72ad4f2` 불변, 커밋·푸시 없음
- 실제 login/logout, account 전환, credential 읽기·복사·rename·symlink: **수행하지 않음**
- Codex 가 주장한 `changed_files` 대비 **허위 주장 0건**

### 머지 전 보완 — 작업 시점 게이트를 영구 회귀 스위트에서 분리 (2026-09-17)

위 `경계 준수` 의 범위 검사는 **이 실행의 작업 시점 게이트**였고 영구 회귀 테스트가 아니다.
그런데 그 판정이 `tests/test_orchestrator_profiles.py` 에 영구 테스트로 남아 있어, 작업 트리에
`72ad4f2` 이후 허용 목록 밖의 추적 변경이나 미추적 파일이 있으면 계약과 무관하게 실패했다.
머지 전 PR 브랜치 자체에서도 미추적 작업 산출물 디렉터리 때문에 이미 실패하고 있었다.
PR 을 현재 `origin/main` 에 머지한 스크래치 검증에서도 main 에 먼저 들어온 무관한 파일 때문에 1건이
실패했고, 이후 main 의 무관한 커밋이나 `#118` 머지에서도 계속 실패하는 구조였다.
그래서 다음 세 단언을 영구 스위트에서 제거했다.

| 제거한 단언 | 작업 시점 사실인 이유 |
|---|---|
| `test_changed_path_allowlist` 전체 | `BASE_REVISION`(`72ad4f2`) 이후 변경이 이 실행의 허용 목록 안에 있는지 판정했다. 미추적 파일도 포함해 작업 공간 상태에 따라 결과가 달라진다 |
| `test_118_status_dependency_and_owned_paths` 의 뒷부분 | `72ad4f2` 이후 `#118` 소유 경로 변경이 0건인지 판정했다. `#118` 이 머지되는 순간 실패한다 |
| `test_full_auto_compatibility` 의 앞부분 | `dot_codex/private_full_auto.config.toml` 이 커밋 `fcfb47ee` 시점과 바이트 동일한지 판정했다. 그 파일을 정당하게 고치는 순간 실패하고 전체 이력이 없는 clone 에서도 실패한다 |

계약 단언은 유지했다. `test_118_status_dependency_and_owned_paths` 는 운영 문서의 `#118`
단방향 status 의존 순서와 공유 파일 언급을, `test_full_auto_compatibility` 는 role manifest·
skill policy·dispatcher·selector 가 full-auto 설정을 참조하지 않는다는 계약을 계속 검사한다.
사용처가 0 이 된 모듈 상수 `BASE_REVISION`, `T15_ALLOWED_FILES`, `T15_ALLOWED_PREFIXES`,
`INITIAL_DIRTY_PREFIXES`, `WORKFLOW_ARTIFACT_PREFIXES` 를 함께 정리했고, `test_file_ownership` 이
쓰는 `PRESERVED_PATHS` 는 남겼다.

## Remaining advisory findings

| finding | 심각도 | 영향 | 후속 |
|---|---|---|---|
| `CODE-007` | Low | `AI_SESSION_IDENTITY_ROOT` override 는 `AI_SESSION_SYNTHETIC_TEST=1` 로 gating 되어 production 신뢰 구멍은 닫혔으나, gate flag 자체가 gating 없는 상속 변수이고 두 변수가 provider child 에서 제거되지 않는다 | 두 변수를 `child_environment` 의 제거 집합에 추가하거나 전달 허용 근거를 문서화 |
| `CODE-009` | Low | `test_profile2_chezmoi_diff_redaction` 이 실제 `chezmoi` 를 호출하지 않아 template 렌더링·ignore 규칙을 관측하지 못한다. 바이트 sentinel scan 자체는 결함 주입으로 검증됨 | 테스트 이름을 실제 동작에 맞게 바꾸거나 실제 렌더링으로 구동 |
| `SPEC-001` | Medium (Spec 층) | `cost_limit_status` 산출 규칙이 Spec 본문이 아닌 Plan 에만 있다 | Spec 개정 시 규칙을 본문에 올리거나 위임 사실을 명시 |
| `SPEC-002` | Low (Spec 층) | non-ready 상태의 status↔launch 1:1 대응표가 Spec 에 없다(Plan 에는 있음) | 동일 |
| `PLAN-004`~`PLAN-006`, `PLAN-008` | Low | pre-commit 주장 근거, `__pycache__` 규칙, version 불일치 수용 명시, T4 RED 사유 | 구현 단계에서 모두 처리됨 |

### 이 실행 밖의 후속 항목

1. **`quality-goal` 스킬 문서 불일치**: `SKILL.md` 는 state root 를 `.Codex/quality-state` 라고
   적지만 설치된 `scripts/quality_state.py` 는 `.claude/quality-state` 를 canonical 로 강제하며
   다른 경로에 "state files re-enter the workspace fingerprint" 경고를 낸다.
   `references/model-routing.md` 도 `.claude/quality-state` 라고 적는다.
   이 실행은 fingerprint 정확성을 위해 `.claude/quality-state` 를 사용했다.
2. **리뷰어 턴 한도**: 코드 리뷰 라운드 1·2 모두 quality-reviewer 가 24턴 한도에서
   보고 없이 중단돼 `SendMessage` 로 보고서를 요청해야 했다. 3,690줄 diff 에 AC 26개를
   검증시키는 부하가 한도를 넘는다.
3. **설치 계약 checker**: `tests/check_installed_orchestrator_cli_contract.py:22` 의 기대
   Claude version `2.1.272` 와 실측 설치본 `2.1.273` 불일치는 승인된 수용 위험이며
   이 checker 는 판정 명령이 아니다.
4. **`#118` 머지 후 rebase 대상**: `tests/test_orchestrator_profiles.py`,
   `dot_config/ai-session/accounts.toml`, `.chezmoiignore`,
   `docs/session-account-profiles.md`.

## Final status

- Status: `completed`
- Machine-readable reason: `CODE_REVIEW_PASSED`

두 판정 명령이 모두 exit 0 이고 마지막 코드 리뷰가 blocker 0 으로 통과했으며
검증된 workspace fingerprint `5c802543…` 가 그 리뷰의 artifact digest 와 일치한다.

**단, Spec `AC-26` 의 Keychain 동시 실행 수동 게이트는 미실행 상태다.**
사용자가 전경에서 이를 수행해 PASS 를 기록하기 전까지 운영 배포 완료로 간주하지 않는다.
