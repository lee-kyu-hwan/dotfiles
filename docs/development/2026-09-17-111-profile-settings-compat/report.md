# Quality Goal Report

- Task ID: 20260917T002844Z-111-프로필별-실경로-smoke의-기본-claude-설정-호환성-결함-f76eb54a
- Mode: strict
- Status: NEEDS_REDESIGN
- Created: 2026-09-17
- Updated: 2026-09-17
- Source goal: #111 프로필별 실경로 smoke의 기본 Claude 설정 호환성 결함(profile1 blocked_policy·profile2 enrollment_required)을 안전하게 해결한다

## Classification

선택 모드는 `strict`이며 사용자가 `--mode=strict`를 명시했다. risk scan 결과가 같은 등급이므로 downgrade 확인은 필요하지 않았다.

- **인증·authorization·계정 격리**: `ai-session` launcher의 Claude 인증 home prescan(`prescan_selected_claude_home`, `dot_local/bin/executable_ai-session:1030-1041`)과 identity·usage admission 판정(`launch:1517`, `status:1558-1559`)을 변경 대상으로 삼는다.
- **보안 통제·secrets**: `BENIGN_CLAUDE_SETTING_TYPES`(`:104-108`)는 `hooks`·`env`·`mcpServers` 등 임의 명령 실행이 가능한 설정 키를 fail-closed로 차단하는 security control이며, 완화 시 credential home 신뢰 경계가 직접 영향을 받는다.
- **cross-account 격리**: `claude-profile1`(provider-default home `~/.claude`)과 `claude-profile2`(`~/.local/share/ai-account-profiles/claude/profile2`) 사이 자격증명·세션 혼입 차단이 목표다.
- **관측 증거**: `~/.claude/settings.json`의 16개 키 중 allowlist와 이름·타입이 모두 일치하는 키는 `theme` 하나뿐이라 profile1이 `blocked_policy`(exit 4)로 차단된다.

## Review history

| 산출물 | 라운드 | 점수 | verdict | blocker | 비고 |
|---|---|---|---|---|---|
| Spec | 1 | 86 | REVISE | 0 | SPEC-001~006 (Medium 3, Low 3). 결정적 게이트 `acceptance_criteria_objective=false` |
| Spec | 2 | 93 | **PASS** | 0 | SPEC-001~006 전부 resolved. 신규 비차단 SPEC-007(Medium)·SPEC-008(Low) |
| Plan | 1 | 74 | REVISE | 2 | PLAN-001(Critical), PLAN-002(High), PLAN-003·004(Medium), PLAN-005·006(Low) |
| Plan | 2 | 78 | REVISE | 1 | PLAN-001~006 전부 resolved. **신규 PLAN-007(Critical)** — 라운드 한도 소진 |

advisory readiness(Codex Sol, read-only): Spec 라운드 1·2 모두 `READY`, score 100, 체크리스트 C1~C8 전부 pass. readiness는 어떤 상태 전이도 결정하지 않는다.

결정적 검사: `revision_check.py --artifact spec` 라운드 2 exit 0, `--artifact plan` 라운드 2 exit 0(`passed: true`, 빈 칸 0, 누락 note 행 0).

## Blocking-finding resolutions

| Finding | 심각도 | 해소 | 검증 증거 |
|---|---|---|---|
| PLAN-001 | Critical | T1에 "fixture 선행 갱신" 단계를 추가해 `make_fake_executable()`(`tests/test_orchestrator_profiles.py:164-192`)의 하드코딩된 Claude `--help`(3옵션)를 5옵션 기본값 + 테스트별 override로 교체. G12가 허용 편집을 정확히 2곳으로 한정. File map 행을 "수정(추가 + 계약 동기화 2곳)"으로 정정 | Plan 라운드 2 리뷰 evidence에서 resolved 판정 |
| PLAN-002 | High | T1 step 3 ④에 기존 `test_portable_cli_contract`의 `expected_contracts["claude"]["cli_required_options"]`(`:5130-5132`) 동기화를 명시하고 step 4에서 CMD-5로 92개 보존을 확인하도록 기술 | Plan 라운드 2 리뷰 evidence에서 resolved 판정 |
| **PLAN-007** | **Critical** | **미해소.** Plan 라운드 한도(2) 소진으로 이번 실행에서 수정할 수 없다 | 아래 "미해소 blocker" 절 참조 |

### 미해소 blocker — PLAN-007

**주장**: T1의 5-option CLI 계약 확장은 Plan이 인정한 두 지점 외에 **세 번째 하드코딩 계약 지점**을 깨뜨린다.

**오케스트레이터 독립 확인(리뷰어는 명령을 실행할 수 없어 정적 추론만 제시했다)**:

- `tests/fixtures/orchestrator-profiles/cli/executable_fake-cli-in-range:9`의 `--help` 출력은 정확히
  `--model --sandbox --ask-for-approval --append-system-prompt --settings --plugin-dir`이며 `--setting-sources`와 `--strict-mcp-config`를 광고하지 않는다.
- `tests/test_orchestrator_profiles.py:5191-5210`이 그 fixture를 PATH의 `claude`로 `shutil.copy2`한 뒤 `ai-claude` 엔트리포인트를 실행하고 `self.assertEqual(0, result.returncode, result.stderr)`를 단언한다.
- `dot_local/bin/executable_ai-role-session:1013`의 `claude_command()`가 `verify_provider_cli_contract()`를 호출하고 `:787-793`이 required option 누락 시 `blocked_cli_contract`를 던진다.
- 따라서 T1이 required-option을 5개로 올리는 순간 이 in-range 케이스는 exit 0이 아니라 exit 4가 되어 **결정적으로 실패**한다.
- `tests/fixtures/...` 경로는 Spec `R3.3`의 exact 변경 범위 10개 파일과 Plan `G7` 허용 집합 어디에도 없다(두 문서에서 `tests/fixtures` 문자열 0건).

**결론**: Plan대로 구현하면 (a) fixture를 고치지 않아 `CMD-5`/`AC-14`가 실패하거나, (b) fixture를 고쳐 `AC-15` scope checker와 Spec `R3.3`을 위반하거나 둘 중 하나가 반드시 발생한다. 이는 Plan 문구 수정만으로 닫히지 않고 **승인된 Spec의 `R3.3` 변경 범위와 `AC-15` 판정 기준을 함께 고쳐야** 하므로 Plan 라운드 안에서 해소할 수 없다.

## Plan approval

- Approval timestamp: 해당 없음 — `AWAITING_PLAN_APPROVAL`에 도달하지 못했다. Plan 게이트가 통과하지 못해 사용자 구현 승인 요청을 하지 않았다.
- Plan digest: `b633529091d9605dae75c879eae73388f80085bec9643e7ac0fac4c41326a950` (라운드 2 심사 대상, 미승인)

## Changed files

구현은 시작하지 않았다. 소스·테스트·운영 문서 변경은 0건이다. 이번 실행이 만든 파일은 quality-goal 산출물뿐이다.

| 파일 | 변경 내용 |
|---|---|
| `docs/development/2026-09-17-111-profile-settings-compat/spec.md` | strict Spec. 요구사항 10개(R1.1~R3.3), 수용 기준 18개(AC-1~AC-18), 판정 명령 5개. 라운드 2 PASS |
| `docs/development/2026-09-17-111-profile-settings-compat/spec-revision-notes.md` | Spec 라운드 2 개정 note |
| `docs/development/2026-09-17-111-profile-settings-compat/plan.md` | 구현 Plan. 태스크 9개(T1~T9). 라운드 2 REVISE로 미승인 |
| `docs/development/2026-09-17-111-profile-settings-compat/plan-revision-notes.md` | Plan 라운드 2 개정 note |
| `docs/development/2026-09-17-111-profile-settings-compat/report.md` | 이 보고서 |

`dot_local/**`, `dot_config/**`, `tests/**`, `docs/session-account-profiles.md`, `docs/orchestrator-permission-profiles.md`는 **변경하지 않았다**. `~/.claude`, `~/.local/share/ai-account-profiles/**`, `~/.config/ai-session/**`도 변경하지 않았다. `#118` 소유 경로와 직전 실행 산출물 `docs/development/2026-09-16-111-profile-onboarding/**`도 변경하지 않았다.

## Verification evidence

구현이 없었으므로 Plan의 `CMD-1`~`CMD-5`는 실행하지 않았다. 아래는 실제로 실행한 명령이다. Python은 모두 `/opt/homebrew/bin/python3.14`다.

| 명령 | exit | 증거 |
|---|---|---|
| `python3.14 tests/test_ai_session.py` (baseline) | 0 | `Ran 29 tests in 18.069s` `OK` — `evidence/baseline-tests.txt` |
| `python3.14 tests/test_orchestrator_profiles.py` (baseline) | 0 | `Ran 92 tests in 41.038s` `OK` — `evidence/baseline-tests.txt` |
| `python3.14 dot_local/bin/executable_ai-session select/status` (profile1, profile2, 읽기 전용) | select 0 / status 4·3 | profile1 `{"status":"blocked_policy"}` exit 4, profile2 `{"status":"enrollment_required","commands":[{"command_id":"identity_enroll_foreground"}]}` exit 3 — `evidence/repro-baseline.txt` |
| `claude --setting-sources "" --strict-mcp-config auth status --json` 및 baseline (읽기 전용, 키 이름만 기록) | 0 / 0 | 두 argv 모두 동일 JSON 키 집합 반환 — `evidence/probe-argv.txt` |
| `claude` 하드닝 플래그 5개 조합 probe (읽기 전용) | 전부 0 | baseline·`--setting-sources ""`·`--safe-mode`·`--restricted`·`--setting-sources "" --strict-mcp-config` 모두 동일 키 집합 — `evidence/probe-flags.txt` |
| `AI_SESSION_CLI_PROBE_MODE=help-only python3.14 tests/check_installed_orchestrator_cli_contract.py` | **1** | `claude installed version differs from frozen evidence` — `evidence/checker-baseline.txt`. **이번 변경 이전부터 실패**하며 이 작업과 무관하다 |
| `revision_check.py --artifact spec` (라운드 2) | 0 | `passed: true` |
| `revision_check.py --artifact plan` (라운드 2) | 0 | `passed: true`, 빈 칸 0, 누락 note 행 0 |
| Codex preflight `gpt-5.6-sol` | 0 | 6.03초, 비어 있지 않은 응답 |

검증 카테고리 중 type check, lint, build는 이 저장소에 `not configured`다. 확인한 저장소 증거: `tests/` 디렉터리에 unittest 스위트와 `check_installed_orchestrator_cli_contract.py`만 존재하고, 저장소 루트에 타입 검사·린트·빌드 설정 파일이 없다. 어느 카테고리도 통과로 기록하지 않았다.

E2E와 high-risk 검증도 실행하지 않았다. Plan이 승인되지 않아 구현이 시작되지 않았기 때문이다.

## Execution watchdog

Codex 실행 세 건 모두 `execution_watchdog.py`로 감싸 실행했고 abort·reap·잔여 프로세스가 없었다.

- Execution ID: `preflight-001`, `spec-author-001`, `readiness-spec-r1`, `readiness-spec-r2`, `spec-author-002`
- PID / PGID: `preflight-001` 7185 / 7185, `spec-author-001` 68691 / 68691 (나머지 실행도 각각 자기 pid를 pgid로 소유)
- Start / end / elapsed: `preflight-001` 2026-09-17T00:29:23Z / 2026-09-17T00:29:29Z / 6.03s, `spec-author-001` 2026-09-17T00:37:39Z / 2026-09-17T00:50:28Z / 767.67s
- Child exit code: 모든 실행 0
- Result exists / schema validation: `preflight-001` false / `not_run`(preflight는 result 경로가 없다), 그 밖의 실행 true / `passed`
- Start confirmed / watchdog reason: true / `null`
- Signals / preservation bundle: `[]` / `null` (`preservation_status: not_needed`)
- Abort: `attempted: false`, `outcome: not_needed`, `candidate: false`
- Reap: `attempted: false`, `outcome: not_needed`, `candidate: false`
- Residual PIDs: `[]`

## Watchdog restart budget

- Initial / remaining: `null` / `null` — 재시작 후보가 한 건도 발생하지 않아 예산을 개설하지 않았다. preflight는 원래 이 예산을 소비하지 않는다.
- Exactly-once consumption: 0
- Restart attempted / stopped: false / false

## Remaining advisory findings

| ID | 심각도 | 내용 | 후속 |
|---|---|---|---|
| SPEC-007 | Medium | AC-15 scope checker가 비교하는 경로 집합이 Spec에 고정되지 않았다 | Plan `G7`이 비교 집합과 제외 집합을 확정했다. 다만 PLAN-007이 드러냈듯 그 허용 집합 자체가 불완전하므로 재설계 시 Spec `R3.3`과 함께 다시 정해야 한다 |
| SPEC-008 | Low | AC-17의 "provider 호출 0회"가 `verify_provider_cli_contract()`의 필수 `--version`·`--help` probe와 문자 그대로 충돌한다 | Plan `G8`이 금지 대상을 provider session exec으로 확정했다. 재설계 시 Spec AC-17 문구 자체를 고치는 편이 낫다 |
| PLAN-003 파생 | Medium | `tests/check_installed_orchestrator_cli_contract.py`의 `EXPECTED_VERSIONS["claude"]`가 `2.1.272`로 고정돼 설치본 2.1.274에서 이미 실패한다. 갱신하려면 `docs/development/2026-09-15-103-orchestrator-permission-profiles-2/authoritative-inputs.md:81`의 동결 버전 문자열도 함께 올려야 한다 | **별도 승인이 필요한 후속 작업.** 이번 실행 범위 밖이며 이 작업의 회귀가 아니다 |
| 비차단 관찰 | Low | Plan `Global constraints` 번호 순서가 G1~G10, G12, G13, G11로 어긋난다 | 재설계 시 정렬 |

## Final status

- Status: `NEEDS_REDESIGN`
- Machine-readable reason: Plan 리뷰가 허용된 2라운드를 소진했으나 통과 게이트에 도달하지 못했다. 마지막 라운드에서 Critical `PLAN-007`이 새로 확정됐고, 그 해소는 승인된 Spec의 `R3.3` 변경 범위와 `AC-15` 판정 기준을 함께 고쳐야 하므로 Plan 개정만으로 닫을 수 없다.

### 재설계 시 선택지

PLAN-007을 닫는 길은 두 가지이며 둘 다 Spec 수준의 결정이 필요하다.

1. **범위 확장**: Spec `R3.3`의 exact 변경 범위와 `AC-15` 비교 집합에 `tests/fixtures/orchestrator-profiles/cli/executable_fake-cli-in-range`를 추가하고, 그 fixture의 Claude `--help` 광고를 다섯 옵션으로 올린다. `executable_fake-cli-lower`·`-upper`·`-missing-option` fixture의 기대 `blocked_cli_contract`는 바뀌지 않아야 한다.
2. **허용 집합 안에서 해결**: `test_portable_cli_contract`의 claude in-range 케이스가 온디스크 fixture 대신 허용된 `tests/test_orchestrator_profiles.py` 안에서 fake CLI를 생성하도록 바꾸고, 그 편집을 기존 테스트 편집 허용 목록에 명시한다. 이 경우 `tests/fixtures/**`는 손대지 않는다.

어느 쪽이든 `CMD-5`(전체 92개 통과)와 `AC-15`(scope checker 통과)가 **동시에** 성립하는 단일 경로가 Spec과 Plan에 명시돼야 한다.

### 사용자 수동 게이트 (자동 실행하지 않음)

- **profile2 identity enrollment**: `claude-profile2`의 `enrollment_required`/exit 3은 설계된 정상 상태이며 결함이 아니다. `ready`로 올리려면 사용자가 전경 pane에서 직접 `ai-session-enroll-identity`를 실행해야 한다. 이 실행은 자동으로 수행하지 않았다.
- **PR #124**: draft 상태를 유지했다. 머지·`chezmoi apply`는 수행하지 않았다. 잔여 blocker(PLAN-007)가 있으므로 머지·apply 금지 조건이 계속 유효하다.
