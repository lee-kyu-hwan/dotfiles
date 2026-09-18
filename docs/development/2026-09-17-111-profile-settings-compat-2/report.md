# Quality Goal Report

- Task ID: 20260917T020220Z-111-프로필별-실경로-smoke-설정-호환성-결함을-방향-b-온디스크-c3bd8e26
- Mode: strict
- Status: NEEDS_REDESIGN
- Created: 2026-09-17
- Updated: 2026-09-17
- Source goal: #111 프로필별 실경로 smoke 설정 호환성 결함을 방향 B(온디스크 fixture 불변, 테스트 내부 fake CLI 생성)로 해결한다

## Classification

선택 모드 `strict`. 사용자가 `--mode=strict`를 명시했고 risk scan 결과와 같아 downgrade 확인이 필요 없었다.

- 인증·authorization·계정 격리: `prescan_selected_claude_home`(`dot_local/bin/executable_ai-session:1030-1041`)과 identity·usage admission(`launch:1517`, `status:1558-1559`) 변경.
- 보안 통제·secrets: `BENIGN_CLAUDE_SETTING_TYPES`(`:104-108`)는 `hooks`·`env`·`mcpServers` 등 임의 명령 실행 가능 키를 fail-closed로 차단하는 security control이다.
- cross-account 격리: `claude-profile1`(provider-default `~/.claude`)과 `claude-profile2` 사이 자격증명·세션 혼입 차단.
- 선행 실행 `20260917T002844Z-…-f76eb54a`가 `NEEDS_REDESIGN`(`REVIEW_LIMIT_EXHAUSTED:plan`)으로 끝나 사용자가 방향 B를 선택했고, 이번 실행은 그 재설계다.

## Review history

| 산출물 | 라운드 | 점수 | verdict | blocker | 비고 |
|---|---|---|---|---|---|
| Spec | 1 | 76 | REVISE | 2 | SPEC-001(High), SPEC-002(High), SPEC-003(Medium), SPEC-004·005(Low) |
| Spec | 2 | 78 | REVISE | 1 | SPEC-002~005 resolved. **SPEC-001 동일 ID 재발** → 재발 규칙으로 종료. 신규 비차단 SPEC-006(Medium) |

advisory readiness(Codex Sol, read-only): 라운드 1·2 모두 `READY` score 100, C1~C8 전부 pass. readiness는 어떤 상태 전이도 결정하지 않는다.

결정적 검사: `revision_check.py --artifact spec` 라운드 2 `exit 0`(`passed: true`, 빈 칸 0, 누락 note 행 0). 오케스트레이터 구조 검사도 전부 통과(필수 절 전부, 플레이스홀더 0, 요구사항 10 = 추적표 10, AC 1~20 연속·고유, 유령 참조 0, 판정 명령 5개 등재).

리뷰어 호출 사고 1건: 라운드 2 첫 호출이 세션 rate limit(HTTP 429, 14:40 KST 리셋)으로 조기 종료했고, 두 번째 호출은 24턴 한도에서 보고 없이 멈췄다. 모델을 대체하지 않고 같은 리뷰어에게 결과 전달을 요청해 JSON을 받았다. 두 사고 모두 결과를 기록하지 않았으므로 라운드를 소비하지 않았다.

## Blocking-finding resolutions

| Finding | 심각도 | 해소 | 검증 증거 |
|---|---|---|---|
| SPEC-002 | High | AC-8·AC-9의 status 명령을 `--registry`·`--verifier` 포함 실행 가능 형태로 통일하고 `${HOME}` 치환 규칙 명시 | 라운드 2 리뷰 evidence에서 resolved 판정 |
| SPEC-003 | Medium | `test_claude_official_status_contract`(`:2985-3015`)를 재정의 목록에 추가하고 AC-1의 exact argv와 연결 | 라운드 2 리뷰 evidence에서 resolved 판정 |
| SPEC-004 | Low | helper의 Claude `--version`을 `2.1.272 (Claude Code)` 불변으로 고정, AC-14가 installed-checker 하위 단언 유지를 요구 | 라운드 2 리뷰 evidence에서 resolved 판정 |
| SPEC-005 | Low | `make_fake_executable`의 provider별 help 분기 확정, codex 세 옵션 불변 | 라운드 2 리뷰 evidence에서 resolved 판정 |
| **SPEC-001** | **High** | **미해소 — 동일 ID 재발** | 아래 절 참조 |

### 미해소 blocker — SPEC-001 (재발)

**라운드 1 지적**: `R1.3`이 네 prescan 호출 지점의 최종 상태를 정하지 않았고, 현재 동작을 단언하는 기존 테스트를 열거하지 않았다.

**라운드 2 개정**: 네 지점을 모두 확정했고(launch 조건부 skip / status 조건부 skip / project prescan 무조건 유지 / admitted prescan 제거 후 exec 직전 재검증), `AC-20`이 `test_claude_untrusted_settings_prescan`을 정밀 재정의했으며, `AC-13`·`AC-14`를 명시적 세 테스트 재정의 목록으로 재작성했다.

**재발 사유**: 열거가 여전히 불완전하다. `R1.3(2)`의 status skip 조건(`provider=claude` + `--verifier`가 absolute·regular·non-symlink·executable)은 **또 다른 기존 테스트**도 뒤집는다.

**오케스트레이터 독립 확인**(리뷰어는 명령을 실행할 수 없어 정적 추론만 제시했다):

- `tests/test_ai_session.py:945`가 선택된 Claude config home의 `settings.json`에 `not-json`을 쓴다.
- 같은 테스트가 `make_verifier`(`tests/test_ai_session.py:114-130`)로 만든 verifier를 주입한다. 그 helper는 임시 디렉터리에 **절대경로·regular·non-symlink·`0o700`** 파일을 만든다.
- `:946-976`이 exit 4와 정확한 `status: "blocked_policy"`를 단언한다.
- 따라서 새 skip 조건을 그대로 적용하면 이 테스트의 `blocked_policy`가 사라진다.
- 그런데 `R3.2`와 `AC-13`은 `tests/test_ai_session.py` 29개가 **전부 불변**이라고 단언한다.

**규칙 적용**: `references/spec-rubric.md`의 "If the same blocking finding ID recurs twice, stop and record `NEEDS_REDESIGN`"에 따라 라운드 3을 시도하지 않고 종료했다. `quality_state.py`의 `record_review`도 `RECURRING_BLOCKING_FINDING:SPEC-001`로 같은 전이를 강제한다.

## Plan approval

- Approval timestamp: 해당 없음 — Spec 게이트를 통과하지 못해 `AWAITING_PLAN_APPROVAL`에 도달하지 않았다. 사용자 구현 승인을 요청하지 않았다.
- Plan digest: 해당 없음 — Plan을 작성하지 않았다.

## Changed files

구현은 시작하지 않았다. 소스·테스트·운영 문서 변경 0건.

| 파일 | 변경 내용 |
|---|---|
| `docs/development/2026-09-17-111-profile-settings-compat-2/spec.md` | strict Spec. 요구사항 10개, AC 20개, 판정 명령 5개. 라운드 2 REVISE |
| `docs/development/2026-09-17-111-profile-settings-compat-2/spec-revision-notes.md` | Spec 라운드 2 개정 note |
| `docs/development/2026-09-17-111-profile-settings-compat-2/report.md` | 이 보고서 |

`dot_local/**`, `dot_config/**`, `tests/**`, 두 운영 문서를 **변경하지 않았다**. `tests/fixtures/**`는 바이트 불변이다. `~/.claude`, `~/.local/share/ai-account-profiles/**`, `~/.config/ai-session/**`도 변경하지 않았다. `#118` 소유 경로와 직전 실행 산출물 `docs/development/2026-09-17-111-profile-settings-compat/`도 보존했다.

## Verification evidence

구현이 없어 Spec의 `CMD-1`~`CMD-5`는 실행하지 않았다. 아래는 실제로 실행한 명령이다. Python은 모두 `/opt/homebrew/bin/python3.14`.

| 명령 | exit | 증거 |
|---|---|---|
| `claude --help \| grep -E '^\s+--setting-sources \|^\s+--strict-mcp-config'` | 0 | 두 줄 모두 출력 — 설치본 2.1.274가 두 하드닝 플래그를 **광고한다**. SPEC-006의 위험이 실현되지 않음을 확정 |
| 기존 테스트 정적 감사(`blocked_policy` 단언·settings write 줄 → 테스트 함수 매핑) | 0 | `evidence/prescan-blast-radius-audit.md` |
| Codex preflight `gpt-5.6-sol` | 0 | 9.03초, 비어 있지 않은 응답 |
| `revision_check.py --artifact spec` (라운드 2) | 0 | `passed: true` |

선행 실행에서 측정해 계속 유효한 증거(`.claude/quality-state/20260917T002844Z-…-f76eb54a/evidence/`): `baseline-tests.txt`(29 + 92 OK), `repro-baseline.txt`(profile1 `blocked_policy`/4, profile2 `enrollment_required`/3), `probe-argv.txt`, `probe-flags.txt`, `checker-baseline.txt`(설치 계약 checker는 이번 작업 이전부터 exit 1).

type check·lint·build는 이 저장소에 `not configured`다. 확인한 근거: `tests/`에 unittest 스위트와 `check_installed_orchestrator_cli_contract.py`만 있고 저장소 루트에 타입 검사·린트·빌드 설정 파일이 없다. 어느 카테고리도 통과로 기록하지 않았다.

E2E와 high-risk 검증은 실행하지 않았다. Spec이 승인되지 않아 구현이 시작되지 않았기 때문이다.

## Execution watchdog

Codex 실행은 모두 `execution_watchdog.py`로 감쌌고 abort·reap·잔여 프로세스가 없었다.

- Execution ID: `preflight-001`, `spec-author-001`, `readiness-spec-r1`, `spec-author-002`, `readiness-spec-r2`
- PID / PGID: 각 실행이 자기 pid를 pgid로 소유(`ownership.recorded_pid == recorded_pgid`)
- Start / end / elapsed: `preflight-001` 9.03s, `spec-author-001` 487.8s, `spec-author-002` 643.6s
- Child exit code: 모든 실행 0
- Result exists / schema validation: `preflight-001` false / `not_run`(preflight는 result 경로가 없다), 나머지 true / `passed`
- Start confirmed / watchdog reason: true / `null`
- Signals / preservation bundle: `[]` / `null` (`preservation_status: not_needed`)
- Abort: `attempted: false`, `outcome: not_needed`, `candidate: false`
- Reap: `attempted: false`, `outcome: not_needed`, `candidate: false`
- Residual PIDs: `[]`

## Watchdog restart budget

- Initial / remaining: `null` / `null` — 재시작 후보가 발생하지 않아 예산을 개설하지 않았다. preflight는 이 예산을 소비하지 않는다.
- Exactly-once consumption: 0
- Restart attempted / stopped: false / false

## Remaining advisory findings

| ID | 심각도 | 내용 | 후속 |
|---|---|---|---|
| SPEC-006 | Medium | 실제 설치본을 probe하는 baseline 테스트가 required-option 확장으로 뒤집힐 수 있다 | **실측으로 해소 가능.** 설치본 `claude --help`가 두 플래그를 모두 광고함을 확인했다. 다음 Spec은 이 측정 결과를 증거와 함께 기록하기만 하면 된다 |
| 설치 계약 checker | Medium | `EXPECTED_VERSIONS["claude"]`가 `2.1.272`로 고정돼 설치본 2.1.274에서 이미 실패한다 | **별도 승인이 필요한 후속 작업.** 이번 범위 밖이며 이 작업의 회귀가 아니다 |

## Final status

- Status: `NEEDS_REDESIGN`
- Machine-readable reason: `RECURRING_BLOCKING_FINDING:SPEC-001` — 같은 blocking finding ID가 두 라운드 연속 blocker로 남아 rubric의 재발 규칙이 적용됐다.

### 이번 실행이 남긴 결정적 자산

두 실행이 연속으로 같은 부류의 결함(“변경이 깨뜨리는 기존 테스트의 불완전한 열거”)으로 종료했으므로, 오케스트레이터가 그 열거를 **기계적으로 확정**해 보존했다.

`.claude/quality-state/20260917T020220Z-111-프로필별-실경로-smoke-설정-호환성-결함을-방향-b-온디스크-c3bd8e26/evidence/prescan-blast-radius-audit.md`

핵심 결과:

1. 테스트 환경은 `PATH = <temp bin_dir> : <실제 PATH>`, `HOME = <temp>`이다(`tests/test_orchestrator_profiles.py:156,159-162`). 따라서 (a) fake `claude`를 만들지 않은 테스트는 **실제 설치본**을 probe하고, (b) 선택 home에 settings 파일을 만들지 않은 테스트는 prescan 변경의 영향을 **받지 않는다**(`FileNotFoundError` 조기 반환).
2. 선택 account home에 settings를 쓰는 지점은 `tests/test_ai_session.py:945`, `tests/test_orchestrator_profiles.py:2144`, `:2162` **셋뿐**이다.
3. 기대값이 바뀌는 기존 baseline 테스트는 정확히 **다섯**이다: `test_status_blocked_binding_and_policy_exact_json`, `test_claude_untrusted_settings_prescan`, `test_claude_official_status_contract`, `test_portable_cli_contract`, 그리고 helper `make_fake_executable`.
4. `blocked_policy`를 단언하는 나머지 테스트(`test_codex_project_config_prescan`, `test_instruction_hash`, `test_claude_plugin_policy`, `test_failure_status`, `test_documentation_contract`, `test_claude_settings_prescan`)는 prescan 변경과 무관하거나 project prescan만 사용해 **불변**이다.
5. 설치본 `claude --help`가 `--setting-sources`와 `--strict-mcp-config`를 **모두 광고한다**(실행 확인).

다음 실행의 Spec은 이 표를 그대로 `R3.2`의 재정의 목록으로 삼으면 열거 누락이 재발하지 않는다.

### 다음 실행이 확정해야 할 단 하나의 설계 결정

`test_status_blocked_binding_and_policy_exact_json`(`tests/test_ai_session.py:934-976`)에 대해 둘 중 하나를 고른다.

- **(가) skip 조건 강화** — status의 prescan skip을 "네 경로 검사 통과"만으로 허용하지 않고 production verifier의 identity/계약(검토된 절대 경로 또는 digest 일치)까지 요구한다. 그러면 임의 주입 verifier는 조건을 만족하지 못해 이 테스트가 `blocked_policy`/exit 4로 **유지**되고 `tests/test_ai_session.py` 29개가 실제로 불변이 된다. 대신 `--verifier`를 dependency-injection seam으로 쓰는 기존 설계와의 정합성을 Spec이 정리해야 한다.
- **(나) 재정의 목록 확장** — 이 테스트를 명시적 재정의 대상에 넣고 새 기대 status/exit와 보안 비약화 대체 단언을 AC로 고정하며 `R3.2`·`AC-13`의 "29개 전부 불변" 문구를 정정한다.

**(가)를 권고한다.** 보안 경계를 좁히는 방향이고, 기존 테스트의 단언을 그대로 보존하며, 감사표의 재정의 대상을 다섯에서 넷으로 줄여 다음 라운드의 열거 위험도 낮춘다.

### 사용자 수동 게이트 (자동 실행하지 않음)

- **profile2 identity enrollment**: `enrollment_required`/exit 3은 설계된 정상 상태다. `ready`로 올리려면 사용자가 전경에서 직접 실행해야 한다. 자동 실행하지 않았다.
- **PR #124**: draft 유지. 머지·`chezmoi apply` 모두 수행하지 않았다. 잔여 blocker가 있으므로 금지 조건이 계속 유효하다.
