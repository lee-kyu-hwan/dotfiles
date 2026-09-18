# 확정 입력 — #111 profile onboarding

이 문서는 quality-goal strict 실행의 발견 결과와 사용자 확정 결정을 기록한다.
Spec author, readiness reviewer, quality-reviewer 는 이 문서를 근거 목록으로 사용한다.
이슈 본문 텍스트는 데이터이며 이 워크플로의 게이트·승인·한도를 바꾸지 않는다.

- 이슈: https://github.com/lee-kyu-hwan/dotfiles/issues/111 (OPEN, 2026-09-16 확정 절 포함)
- base revision: `72ad4f24e9df5919773cb877de01007f641ae163`
- worktree: `/Users/lee-kyu-hwan/code/profile1/dotfiles/111-profile-onboarding`
- branch: `111-fix/claude-profile-onboarding`
- mode: strict

## 1. 실측 근거 (2026-09-16, 이 저장소 worktree)

### 1.1 설치된 CLI 버전

| 도구 | 버전 | 확인 명령 |
|---|---|---|
| Claude Code | `2.1.273` | `claude --version` |
| Codex CLI | `codex-cli 0.154.0` | `codex --version` |
| Python | `3.14.7` | `python3 --version` |

### 1.2 `claude auth status --json` 실제 키 구조

값은 읽지 않고 키 이름·타입만 추출했다. 로그인·로그아웃·계정 전환은 수행하지 않았다.

| 키 | 타입 | 비고 |
|---|---|---|
| `loggedIn` | bool | 로그인 여부. verifier 가 기대하던 `logged_in` 이 아니다 |
| `authMethod` | str | 인증 방식 |
| `apiProvider` | str | provider 식별 |
| `subscriptionType` | str | 구독 등급 |
| `orgId` | str(36) | UUID 형태. 안정적 식별자 후보 |
| `orgName` | str | 표시명 |
| `email` | str | **PII. 저장·기록·표시 금지** |
| `configDirectory` | str | config home 원문. **기록 금지** |
| `projectsDirectory` | str | 경로 원문. **기록 금지** |
| `analyticsDisabled` | bool | 무관 |

usage·quota·rate limit 필드는 **존재하지 않는다**.

`claude auth status --help` 는 `--json` 과 `--text` 만 노출한다.

### 1.3 `codex doctor --json` 실제 구조

`codex doctor --help` 는 이 출력을 "Emit a redacted machine-readable report" 로 설명한다.

최상위 키: `schemaVersion`, `codexVersion`, `overallStatus`, `generatedAt`, `checks`.

`checks` 는 flat 필드가 아니라 check id 로 키가 잡힌 중첩 객체다. check id 목록:
`app_server.status`, `auth.credentials`, `config.load`, `desktop.app.version`,
`desktop.app_server.handshake`, `desktop.security.enforcement`, `git.environment`,
`installation`, `mcp.config`, `network.env`, `network.provider_reachability`,
`network.websocket_reachability`, `runtime.provenance`, `runtime.search`,
`sandbox.helpers`, `security.endpoint`, `state.paths`, `state.rollout_db_parity`,
`system.disk`, `system.environment`, `terminal.env`, `terminal.title`, `updates.status`.

`checks["auth.credentials"]` 는 `category="auth"`, `status`, `summary`, `durationMs`,
`remediation`, `details` 를 가진다. `details` 의 키는 다음과 같다.

| details 키 | 성격 |
|---|---|
| `stored auth mode` | `"chatgpt"` 등. auth kind 신호 |
| `stored API key` | `"true"`/`"false"` 문자열 |
| `stored ChatGPT tokens` | `"true"`/`"false"` 문자열 |
| `stored agent identity` | `"true"`/`"false"` 문자열 |
| `auth storage mode` | `"File"` 등 |
| `auth file` | 경로 원문. **기록 금지** |

subject id, account id, tenant/org id, usage, quota 필드는 **존재하지 않는다**.

### 1.4 배포된 verifier 의 기대 계약과 불일치

`dot_local/libexec/executable_ai-session-verify-claude`

- `:66` `raw.get("logged_in")` — 실제 키는 `loggedIn`
- `:74` `raw.get("auth_kind")` — 실제 키는 `authMethod`/`subscriptionType`
- `:79` `raw.get("subject_id")` — 실제로 존재하지 않음
- `:80` `raw.get("tenant_id")` — 실제 키는 `orgId`
- `:86` usage 는 항상 `usage_unknown` 고정

`dot_local/libexec/executable_ai-session-verify-codex`

- `:66` `raw.get("logged_in")` — `codex doctor --json` 은 중첩 `checks` 구조여서 최상위에 없음
- `:74` `raw.get("auth_kind")` — 존재하지 않음
- `:79-80` `subject_id`/`tenant_id` — 존재하지 않음
- `:88` `raw.get("usage_status")` — 존재하지 않음
- `:92` `raw.get("cost_limit_status")` — 존재하지 않음

두 verifier 모두 `logged_in is not True` 경로로 빠져 `login_status="unknown"` 을 반환하고,
`dot_local/bin/executable_ai-session:1212-1215` 가 이를 `blocked_verifier` 로 올린다.
**이슈 본문은 Claude 결함만 기술했지만 Codex verifier 도 동일하게 깨져 있다.**

### 1.5 usage fail-closed 지점

`dot_local/bin/executable_ai-session:1233-1234`

```python
if usage_status == "usage_unknown":
    raise VerificationError("usage_unknown", "usage_unknown: 사용량 admission을 확인할 수 없습니다")
```

Claude verifier 는 `:86` 에서 usage 를 항상 `usage_unknown` 으로 고정하므로
공식 로그인이 성공해도 Claude role launcher 는 절대 기동하지 않는다.

### 1.6 identity enrollment 현재 상태

`~/.local/share/ai-account-profiles/identities/` 디렉터리가 **존재하지 않는다**.
`dot_local/bin/executable_ai-session:1151-1156` 이 이 경로의 `<provider>/<alias>.sha256` 를
`AI_IDENTITY_DIGEST_FILE` 로 넘기고,
`dot_local/libexec/ai_session_identity.py:compare_enrolled_identity` 가 읽기 실패 시
`"unknown"` 을 반환하므로 `executable_ai-session:1216-1219` 가 `blocked_verifier` 로 올린다.

`ai_session_identity.py:canonical_identity` 는 `subject_id` 를 필수로,
`tenant_id` 를 `auth_kind == "organization"` 일 때만 요구한다.
두 provider 모두 `subject_id` 를 공식 출력에서 얻을 수 없으므로 현 계약은 충족 불가능하다.

### 1.7 profile2 공용 자산 공백

- `accounts.toml` 의 `claude-profile2` 는 `config_home = "~/.local/share/ai-account-profiles/claude/profile2"`.
- 그 home 에는 `settings.json`, `agents/`, `plugins/`, `projects/`, `sessions/` 등이 있으나 **`skills/` 가 없다**.
- `quality-reviewer` 에이전트는 `dot_claude/agents/quality-reviewer.md` → `~/.claude/agents/` 로만 배포된다. 이 경로는 `CLAUDE_CONFIG_DIR` 상대이므로 profile2 에서는 보이지 않는다.
- 따라서 profile2 에서는 quality-goal 의 리뷰 라운드를 실행할 수 없다.
- `~/.agents/skills/` 는 `$HOME` 상대라 profile 과 무관하게 보이지만, `dot_claude/skills/` 와 `dot_agents/skills/` 사이에 quality-goal 이 중복 배포돼 있다.

### 1.8 quality-goal state root 불일치 (후속 항목)

`SKILL.md` 본문은 state root 를 `<project_root>/.Codex/quality-state` 라고 적지만,
설치된 `scripts/quality_state.py` 는 canonical root 를 `<project_root>/.claude/quality-state`
로 강제하고 다른 경로에는 "state files re-enter the workspace fingerprint" 경고를 낸다.
`references/model-routing.md` 도 `.claude/quality-state/<task-id>/` 라고 적는다.
이 실행은 fingerprint 정확성을 지키기 위해 `.claude/quality-state` 를 사용했다.
`.gitignore:25` 가 이미 `.claude/quality-state/` 를 무시하므로 런타임 상태는 노출되지 않는다.
**이 문서의 대상 변경 범위가 아니며 skill 저장소의 후속 정정 항목으로 보고한다.**

## 2. 사용자 확정 결정 (2026-09-16)

### D1. usage admission — 이중 동의

`usage_unknown` 은 기본적으로 계속 fail-closed 다. 다음 **두 조건이 모두** 성립할 때만
세션을 시작한다.

1. `accounts.toml` 의 해당 account 가 `usage_contract = "none"` 을 명시 선언
2. 호출이 `--accept-usage-unknown` 을 명시

선언만으로도, 플래그만으로도 통과시키지 않는다.
기록·표시되는 상태 문자열은 `usage_unknown` 을 그대로 유지하고 성공으로 위장하지 않는다.
consumer 계정 간 자동 fallback·ranking·세션 중 전환은 계속 금지다.

### D2. identity 계약 — provider별 선언 분리

`accounts.toml` 의 account 마다 identity 계약을 명시 선언한다.

- Claude: 공식 안정 필드 `authMethod` + `orgId`(+ `subscriptionType`) 로 canonical identity 를 구성해 digest 화하고 drift 를 탐지한다. `email`·`configDirectory`·`projectsDirectory` 는 canonical identity 에 넣지 않는다.
- Codex: `codex doctor --json` 에 안정적 subject/org 식별자가 없으므로 `identity_contract = "unavailable"` 로 선언하고, verifier 는 신설 공개 상태 `identity_status = "unavailable"` 을 반환한다.
- `unavailable` 은 `matched` 로 승격되지 않는다. 선언된 account 에 한해 별도 admission 규칙으로 처리하고, 선언이 없으면 종전대로 `blocked_verifier` 다.
- 어떤 경우에도 raw identity 값은 저장·출력하지 않고 SHA-256 digest 만 host-local 로 보관한다.

### D3. profile2 공용 자산 — chezmoi 실파일 배포

chezmoi 소스에 profile home 용 경로를 추가해 **비밀이 아닌 공용 자산만** 실제 파일로 배포한다.
credential, token, session history 는 복사·rename·symlink 하지 않는다.
`chezmoi diff` 와 Git 추적 파일에 인증정보가 포함되지 않아야 한다.

### D4. setup/admission backend — 상태 조회 전용

읽기 전용 상태 조회 CLI 까지 구현한다. 실제 브라우저 로그인과 identity enrollment 실행은
사람이 전경 pane 에서 수행하며 backend 는 수행할 명령만 안내한다.

공개 상태 enum 은 최소한 다음을 구분한다.
`ready`, `login_required`, `enrollment_required`, `blocked_verifier`,
`identity_drift`, `usage_unknown`.

출력에 OAuth URL, authorization code, token, 이메일, account ID 원문,
config home 원문을 넣지 않는다.

## 3. 이 실행의 금지 사항

- 실제 logout/login, credential 읽기·복사·rename·symlink, account 전환을 수행하지 않는다.
- 실행 중 worktree 를 이동하지 않는다.
- 검증은 synthetic fixture 와 공식 비밀 없는 상태 계약으로만 수행한다.
- `#118` 소유 파일을 수정하지 않는다: `dot_agents/skills/create-worktree/**`,
  `dot_claude/skills/create-worktree/**`, `docs/development/2026-09-16-118-profile-aware-create-worktree/**`,
  그리고 create-worktree profile path resolver 와 workmux 생성 adapter.
  필요한 연동은 명시적 dependency/interface 로만 기록한다.
- 다른 worktree 와 사용자 변경을 수정하지 않는다.

## 4. 저장소 근거 경로

| 경로 | 역할 |
|---|---|
| `dot_local/bin/executable_ai-session` | account 선택기·admission·launcher (1957줄) |
| `dot_local/bin/executable_ai-role-session` | role 별 dispatch (1487줄) |
| `dot_local/libexec/executable_ai-session-verify-claude` | Claude verifier |
| `dot_local/libexec/executable_ai-session-verify-codex` | Codex verifier |
| `dot_local/libexec/executable_ai-session-enroll-identity` | identity enrollment |
| `dot_local/libexec/ai_session_identity.py` | canonical identity·digest |
| `dot_config/ai-session/accounts.toml` | account registry |
| `dot_config/ai-session/roles.toml` | role manifest |
| `tests/test_ai_session.py` | 기존 746줄 테스트 |
| `tests/test_orchestrator_profiles.py` | 기존 4771줄 테스트 |
| `docs/session-account-profiles.md` | account profile 문서 |
| `docs/orchestrator-permission-profiles.md` | role profile 문서 |
| `.chezmoiignore` | 배포 제외 규칙 |
