# Quality Goal Specification

- Task ID: 20260916T025114Z-111-claude-code-2-1-273-auth-status-호환성-f224ab4d
- Mode: strict
- Status: SPEC_REVIEW
- Created: 2026-09-16
- Updated: 2026-09-16
- Source goal: #111 Claude Code 2.1.273 auth status 호환성, identity enrollment/verifier 계약, profile2 비밀 없는 공용 스킬 배포, profile setup/admission backend 계약을 구현한다

## Problem and context

Claude Code 2.1.273의 공식 `claude auth status --json` 명령에서 실측된 JSON은 `loggedIn`, `authMethod`, `orgId`, `subscriptionType`을 제공하지만 현재 adapter는 `logged_in`, `auth_kind`, `subject_id`, `tenant_id`를 읽는다. Codex 0.154.0의 `codex doctor --json`도 최상위 평면 field가 아니라 `checks["auth.credentials"]`의 중첩 구조인데 현재 adapter는 Claude와 같은 평면 field를 예상한다. 그 결과 두 adapter는 `login_status="unknown"`을 반환하고 launcher는 `blocked_verifier`로 중단한다. 실측 key와 현재 불일치는 `authoritative-inputs.md:23-92`, 현재 adapter 로직은 `dot_local/libexec/executable_ai-session-verify-claude:35-80`과 `dot_local/libexec/executable_ai-session-verify-codex:35-85`, 중단 지점은 `dot_local/bin/executable_ai-session:1184-1237`에 있다. 명령과 JSON 출력 형식은 문서화돼 있지만 조직 컨텍스트에 필요한 개별 field 구성은 공식 안정 schema로 보지 않는다.

현재 `canonical_identity`는 모든 provider에 `subject_id`를 요구하고 organization에만 `tenant_id`를 추가한다(`dot_local/libexec/ai_session_identity.py:29-60`). 그러나 두 공식 status surface에 `subject_id`가 없고, Codex에는 안정적 subject/org 식별자 자체가 없다(`authoritative-inputs.md:58-70,106-116`). 또한 현재 연결은 digest file 부재·부정형·구 schema를 모두 `unknown`으로 압축한다(`dot_local/libexec/ai_session_identity.py:67-103`). 따라서 사용자가 로그인, 미등록, drift, adapter 고장을 구분해 복구할 수 없다.

승인 뒤 실증에서 `authMethod`+`orgId`+`subscriptionType` canonical digest는 같은 조직의 서로 다른 사용자를 구분하지 못한다는 전제가 확인됐다. 반대로 현재 두 profile은 같은 email을 쓰지만 `orgId`가 달라 서로 다른 digest를 만든다(`scope-change-2026-09-16.md:8-42`). 따라서 이 digest의 선택 경계는 개인이 아니라 profile에 배정된 조직 컨텍스트이며, `matched`는 enrollment 시점과 같은 조직 컨텍스트라는 뜻으로만 사용해야 한다. 같은 digest를 두 profile에 매핑하는 경우는 차단해야 하고, `claude auth status --json`의 비공식 field 구조가 달라져 판정할 수 없는 경우도 성공으로 강등해서는 안 된다.

usage/quota field는 두 공식 surface에 없다(`authoritative-inputs.md:40-42,70`). 현재 launcher가 `usage_unknown`을 언제나 fail-closed하는 것은 안전하지만(`dot_local/bin/executable_ai-session:1220-1236`), 확정 결정 D1은 account 선언과 호출 동의가 모두 있는 정확한 경우에만 이 알려진 불가용성을 수용하라고 한다(`authoritative-inputs.md:138-148`). 한쪽 동의만으로 통과하거나 `usage_unknown`을 `sufficient`로 바꾸면 fail-closed 기본값을 우회한다.

`claude-profile2`의 `CLAUDE_CONFIG_DIR`은 `~/.local/share/ai-account-profiles/claude/profile2`이지만, quality-goal은 기본 `~/.claude/skills/`에, quality-reviewer는 기본 `~/.claude/agents/`에만 chezmoi 배포된다. Claude Code가 `agents/`와 `skills/`를 `CLAUDE_CONFIG_DIR`에 상대적으로 탐색하므로 profile2에서 strict review loop가 끊긴다(`authoritative-inputs.md:118-124`; 배포 네이밍은 `CLAUDE.md:34-46`). 다만 account home의 `settings.json`은 permissions·sandbox·hooks를 가진 untrusted input이며 배포 대상이 아니다(`.chezmoiignore:21-24`; `docs/orchestrator-permission-profiles.md:22-34`). 공용 실행 자산 배포를 credential/session 복제로 확장해서는 안 된다.

마지막으로 account 선택은 보다 엄격해졌지만(`dot_local/bin/executable_ai-session:788-868`), TUI가 소비할 수 있는 읽기 전용 setup/admission 상태 API가 없다. 현재 `select`는 auth를 조회하지 않고 `launch`는 성공 시 provider를 바로 `exec`한다(`dot_local/bin/executable_ai-session:1870-1928`). 확정 결정 D4는 상태만 조회하고 실제 login/enrollment는 사람의 전경 pane에 남겨야 한다(`authoritative-inputs.md:165-175`).

## Goals

1. Claude Code 2.1.273과 Codex 0.154.0의 공식 명령에서 실측한 machine-readable auth 출력을 정확히 redacted six-field verifier 계약으로 변환한다.
2. account registry에 provider별 identity/usage 계약을 명시하고, Claude 조직 컨텍스트 digest의 match·drift·중복 매핑·판정 불가, Codex identity unavailable, usage 이중 동의를 서로 혼동하지 않는 fail-closed admission으로 구현한다.
3. profile2에 quality-goal과 quality-reviewer를 정규 실파일로 배포하되 account settings, credential, token, identity 원문, session history는 chezmoi/Git/diff 경계 밖에 둔다.
4. TUI가 사용할 수 있는 읽기 전용 `ai-session status` 계약을 제공하고, #118 backend 후순위 dependency를 명시하되 #118 소유 코드는 건드리지 않는다.
5. synthetic fixture로 모든 상태·보안 경계·교차 회귀를 재현하고 실제 login/logout/account 전환없이 판정한다.

## Non-goals

- 실제 Claude/Codex logout, login, browser OAuth, account 전환, credential/token 조회, identity enrollment, `chezmoi apply`, provider process 기동을 이 자동 검증에서 수행하지 않는다.
- usage/quota를 로그인 상태, TUI scraping, private endpoint, 추정치로 생성하지 않고 consumer account ranking, fallback, rotation, session 중 hot-swap을 추가하지 않는다.
- Codex에 없는 subject/org identity를 auth file path, 이메일, 저장 모드 또는 account 별칭에서 추론하지 않는다.
- Claude 조직 컨텍스트 digest로 개인 동일성을 증명하지 않고, email 원문 또는 email HMAC·salt·키·파생 digest를 canonical identity나 중복 판정에 추가하지 않는다.
- 시작 전 digest 검사로 실행 중 Keychain 격리를 보증한다고 주장하지 않는다. 동시 실행 검증은 자동 workflow 밖의 사람 전경 수동 게이트로 판정한다.
- profile2에 `settings.json`, `.claude.json`, credential, token, plugins, transcript/history 또는 기존 account-home 디렉터리를 복제·rename·symlink하지 않는다.
- `dot_agents/skills/create-worktree/**`, `dot_claude/skills/create-worktree/**`, `docs/development/2026-09-16-118-profile-aware-create-worktree/**`, create-worktree profile path resolver, workmux 생성 adapter를 수정하지 않는다.
- #118의 worktree 생성/resolve UI, pane lifecycle, foreground login/enrollment 실행 UI를 이 작업에서 구현하지 않는다. 연동은 순서와 JSON interface dependency로만 정의한다.
- `authoritative-inputs.md:126-134`의 quality-goal state-root 불일치를 이 작업에서 수정하지 않는다.

## Requirements

- **R1.1** Claude verifier는 `claude auth status --json`을 한 번만 10초 timeout, captured stdout/stderr, `close_fds=True`, empty `pass_fds`로 실행하고, boolean `loggedIn`을 `logged_in|not_logged_in|unknown`으로 변환한다. `loggedIn=true`일 때만 non-empty string `authMethod`, UUID 형태 `orgId`, non-empty string `subscriptionType`을 identity projection에 전달한다. 이 세 필드가 누락되거나 타입·구조가 달라 조직 컨텍스트를 판정할 수 없으면 `identity_unverifiable`로 차단하며 `matched`로 강등하지 않는다. `email`, `configDirectory`, `projectsDirectory`, `orgName`, raw stdout/stderr는 canonical identity, verifier JSON, public status, 로그에 절대 넣지 않는다. [근거: `authoritative-inputs.md:23-42`; `scope-change-2026-09-16.md:72-77`; `dot_local/libexec/executable_ai-session-verify-claude:35-80`]
- **R1.2** Codex verifier는 `codex doctor --json`을 R1.1과 같은 subprocess 경계로 한 번만 실행하고 `checks["auth.credentials"]` object의 `category="auth"`, `details["stored auth mode"]`, 정확한 string boolean `stored API key|stored ChatGPT tokens|stored agent identity`만 읽는다. 현재 배포 consumer account는 mode `chatgpt`이고 ChatGPT token 또는 agent identity가 `"true"`이면 `logged_in`, 세 credential signal이 모두 `"false"`이면 `not_logged_in`, 구조·타입·mode 모순은 `unknown`이다. `auth file`, summary, remediation, generatedAt, raw output은 출력하지 않고 identity/usage를 추론하지 않는다. [근거: `authoritative-inputs.md:44-70,82-92`; `dot_local/libexec/executable_ai-session-verify-codex:35-85`]
- **R1.3** provider adapter의 stdout은 기존 exact six-field set `provider`, `account_profile`, `login_status`, `identity_status`, `usage_status`, `cost_limit_status`만 가진 compact JSON 한 줄이어야 한다. nonzero/timeout/malformed/contract mismatch는 raw provider 출력을 전파하지 않고 `unknown` 또는 판정 가능한 `identity_unverifiable`을 포함한 redacted result로 닫히며 launcher의 exact field, provider/profile, status-domain 검사를 통과하지 못하면 `blocked_verifier`다. `identity_unverifiable`·`duplicate_mapping`·`unavailable`은 `matched`로 승격되지 않는다. [근거: `scope-change-2026-09-16.md:105-117`; `dot_local/libexec/executable_ai-session-verify-claude:14-32,84-89`; `dot_local/libexec/executable_ai-session-verify-codex:14-32,89-94`; `dot_local/bin/executable_ai-session:1173-1223`]
- **R2.1** strict `accounts.toml`은 `schema_version=2`, `contract_id="orchestrator-permission-profiles-v2"`로 올리고 각 active account에 required `identity_contract` 및 `usage_contract`을 선언한다. 허용 identity 조합은 Claude의 `claude_auth_status_v1`, Codex의 `unavailable`이고, usage domain은 `none|provider_status`이다. 현재 세 active account는 공식 usage field가 없으므로 `usage_contract="none"`을 선언한다. missing, unknown, provider/contract 불일치, v1 strict registry는 verifier 실행 전 `blocked_contract`로 거부하고 implicit default를 두지 않는다. legacy `version=1` parser는 기존 호환 path로 별도 유지한다. [근거: `dot_local/bin/executable_ai-session:34-53,295-383,436-447`; `dot_config/ai-session/accounts.toml:1-31`; `authoritative-inputs.md:138-157`]
- **R2.2** shared `canonical_identity(raw, identity_contract)`는 `claude_auth_status_v1`에 대해 canonical schema 2 object `{schema_version:2, identity_contract:"claude_auth_status_v1", provider:"claude", auth_method, org_id, subscription_type}`만 만든다. 이 구성은 조직 컨텍스트 digest로 변경 없이 재사용한다. 문자열은 NFC, ASCII edge trim, control-character 거부를 적용하고 `orgId`는 UUID parse 후 lowercase hyphen 표현으로 고정한다. compact UTF-8, sorted-key bytes의 SHA-256이 동일 조직 컨텍스트에 대해 항상 동일해야 하며 `email`, `configDirectory`, `projectsDirectory` 변경은 digest를 바꾸지 않는다. [근거: `dot_local/libexec/ai_session_identity.py:20-64`; `authoritative-inputs.md:150-157`; `scope-change-2026-09-16.md:50-54`]
- **R2.3** enrollment file 형식은 raw identity 없이 `v2:<64 lowercase hex>\n`만 저장하고 현재 0700 owner directory, 0600 regular non-symlink file, atomic replace 규칙을 유지한다. 기존 `64hex\n`은 legacy v1으로 식별해 `stale_enrollment`, file 부재는 `not_enrolled`, valid v2 조직 컨텍스트 일치는 `matched`, 불일치는 `identity_drift`, mode/owner/type/symlink/format 오류는 `unknown`으로 구분한다. `matched`는 개인 동일성이 아니라 enrollment 시점과 같은 조직 컨텍스트라는 뜻이다. `stale_enrollment|not_enrolled`는 public `enrollment_required`, `unknown`은 `blocked_verifier`로 mapping하며 자동 overwrite/re-enroll하지 않는다. [근거: `dot_local/libexec/ai_session_identity.py:16-17,67-103`; `dot_local/libexec/executable_ai-session-enroll-identity:117-199`; `authoritative-inputs.md:106-116,150-157`; `scope-change-2026-09-16.md:56-60`]
- **R2.4** `identity_contract="unavailable"`인 Codex account의 verifier는 valid login을 확인한 후 `identity_status="unavailable"`을 반환하고 digest file을 읽거나 enrollment을 허용하지 않는다. admission은 binding의 선언과 payload의 `unavailable`이 정확히 짝을 이룰 때만 별도 branch로 identity gate를 통과하되 verifier payload, internal admission result, status JSON에서는 계속 `unavailable`이어야 하고 `matched`로 재기록하지 않는다. 기존 account-binding/startup record schema에는 identity field를 추가하지 않는다. 미선언, Claude+unavailable, Codex+matched 위조는 `blocked_verifier`다. [근거: `authoritative-inputs.md:150-157`; 현재 matched-only gate `dot_local/bin/executable_ai-session:1205-1219`; 기존 record `dot_local/bin/executable_ai-session:1261-1279,1302-1308`]
- **R2.5** `usage_status="usage_unknown"`은 기본 `usage_unknown` 실패다. 선택 account의 `usage_contract` 값이 exact `none`이고 현재 `status`나 `launch` 호출에 `--accept-usage-unknown`이 명시된 두 조건이 모두 참일 때만 admission을 허용한다. 선언만, flag만, `provider_status`+unknown은 모두 차단한다. 통과해도 verifier payload, `AI_USAGE_ADMISSION_STATUS`, binding/startup record, status JSON의 value는 `usage_unknown`을 유지하고 `sufficient`로 승격하지 않는다. [근거: `dot_local/bin/executable_ai-session:1220-1237,1294-1318`; `authoritative-inputs.md:138-148`]
- **R2.6** identity unavailable branch와 usage 이중 동의 branch는 account 선택·scope·binding, login, provider/profile exact match, consumer/PAYG cost gate의 순서를 우회하지 않는다. 우선순위는 login failure → identity drift/enrollment/identity unverifiable/duplicate mapping/contract failure → cost contract failure → blocked usage/usage unknown이며, consumer account 자동 fallback·ranking·rotation·session 중 전환은 계속 0회여야 한다. [근거: `dot_local/bin/executable_ai-session:788-868,1184-1237`; `docs/session-account-profiles.md:100-117,126-135`; `authoritative-inputs.md:146-148`; `scope-change-2026-09-16.md:62-77`]
- **R3.1** chezmoi source에 `dot_local/share/ai-account-profiles/claude/profile2/agents/quality-reviewer.md`와 `dot_local/share/ai-account-profiles/claude/profile2/skills/quality-goal/**`를 추가하고, 각 leaf를 regular non-symlink 실파일로 둔다. 배포 대상은 canonical `dot_claude/agents/quality-reviewer.md` 한 파일과 `dot_claude/skills/quality-goal/**`의 모든 regular file에 대한 byte-for-byte mirror이며 누락·추가·drift가 없어야 한다. `.tmpl`, source symlink, runtime copy script는 사용하지 않는다. [근거: `authoritative-inputs.md:118-124,159-163`; `CLAUDE.md:34-46`]
- **R3.2** profile2 공용 allowlist는 R3.1의 reviewer/skill mirror뿐이다. `settings.json`, `.claude.json`, `.credentials.json`, `credentials*`, `tokens*`, `sessions/**`, `projects/**`, `history.jsonl`, `backups/**`, `file-history/**`, `debug/**`, `todos/**`, `plans/**`, `plugins/**`, OAuth URL/code, account/identity 원문은 절대 배포 대상이 아니며 복제·rename·symlink하지 않는다. `.chezmoiignore`에 최소한 `settings.json`, `.claude.json`, credential/token, 위 runtime/history directory의 profile2 target deny pattern을 명시하고 기존 `.claude/settings.json` untrusted-input deny를 유지한다. [근거: `.chezmoiignore:21-24`; `docs/session-account-profiles.md:3-7,106-117`; `authoritative-inputs.md:159-163`]
- **R3.3** synthetic rendered-home 검사는 profile2의 allowlisted asset이 정확한 target에 실파일로 존재하고 quality-goal이 `../../agents/quality-reviewer.md`를 resolve하는지 확인한다. 같은 fixture의 `chezmoi diff` 출력과 Git 추적 source 전체에 sentinel email/token/account ID/config-home/session text가 0개이고 denylist target과 symlink가 0개임을 검사한다. 실제 account home은 읽지 않는다. [근거: `dot_claude/skills/quality-goal/SKILL.md:70-73`; `authoritative-inputs.md:159-163,177-186`]
- **R4.1** `executable_ai-session`에 read-only `status` subcommand를 추가한다. `status`는 `select`와 동일한 registry/provider/role/account/task/session/directory selection input, required absolute regular non-symlink `--verifier`, optional `--accept-usage-unknown`만 받고 program 인자를 받지 않는다. selection·home pre-scan·verifier를 한 번 수행하지만 provider exec, login, enrollment, registry/digest/account-home/worktree/tmux 쓰기를 수행하지 않는다. [근거: `dot_local/bin/executable_ai-session:881-918,1132-1181,1870-1928`; `authoritative-inputs.md:165-181`]
- **R4.2** `status` stdout은 exact fields `schema_version=1`, `event="profile_status"`, `provider`, `account_profile`, `status`, `login_status`, `identity_status`, `usage_status`, `cost_limit_status`, `commands`를 가진 compact JSON 한 줄이다. `provider`는 요청 provider 문자열이고 `account_profile`은 선택 성공 시 public alias, 선택 전 실패 시 JSON null이다. public `status`는 최소 `ready|login_required|enrollment_required|blocked_verifier|identity_drift|identity_unverifiable|duplicate_mapping|usage_unknown`을 구분하고 `blocked_usage|blocked_contract|blocked_binding|blocked_policy`를 추가로 허용한다. `ready`는 launch가 provider exec 직전까지 같은 admission을 통과할 때만 가능하며, 이중 동의로 ready인 경우에도 `usage_status="usage_unknown"`, Codex에는 `identity_status="unavailable"`을 유지한다. `identity_unverifiable`·`duplicate_mapping`·`unavailable`을 `matched`로 재기록하지 않는다. ready는 exit 0, 인식된 non-ready admission state는 exit 3, contract failure는 2, binding/policy failure는 기존 4 exit semantics를 유지한다. [근거: `dot_local/bin/executable_ai-session:1247-1279`; `authoritative-inputs.md:165-175`; `scope-change-2026-09-16.md:105-117`]
- **R4.3** `commands`는 secret-free descriptor 배열이며 각 descriptor의 exact fields는 `command_id`, `provider`, `account_profile`이다. 허용 `command_id`는 `provider_login_foreground`, `identity_enroll_foreground`, `inspect_identity_foreground`, `retry_with_usage_consent`뿐이다. backend는 descriptor만 반환하고 실행하지 않으며 OAuth URL/code, token, email, raw account/org ID, digest, config-home path, raw provider reason/output을 어떤 status에도 넣지 않는다. `blocked_verifier|identity_unverifiable|duplicate_mapping|blocked_contract|blocked_binding|blocked_policy|blocked_usage|ready`의 commands는 빈 배열이어야 하여 불안전하거나 불필요한 자동 복구를 제안하지 않는다. [근거: `dot_local/bin/executable_ai-session:1240-1279`; `authoritative-inputs.md:165-175`; `scope-change-2026-09-16.md:62-77`]
- **R4.4** TUI 순서는 `#118 create-worktree backend -> resolved profile/worktree result -> ai-session status -> foreground operator action`의 dependency다. #118이 provider, account-profile alias, resolved real worktree를 반환한 뒤 TUI가 그 값을 status input으로 넘기고, status가 ready일 때만 다음 launch를 검토한다. 이 작업은 #118 구현을 import·수정·대체하지 않는다. 예상 공유 충돌 파일 `tests/test_orchestrator_profiles.py`, `dot_config/ai-session/accounts.toml`, `.chezmoiignore`, `docs/session-account-profiles.md`는 #118 merge 후 rebase 대상으로 남긴다. [근거: `authoritative-inputs.md:177-186`; `baseline-verification.md:75-91`]
- **R5.1** `docs/session-account-profiles.md`와 `docs/orchestrator-permission-profiles.md`는 registry v2 field/domain, Claude/Codex projection, enrollment v2/stale migration, `matched`의 조직 컨텍스트 의미와 개인 식별 한계, duplicate mapping·identity unverifiable·unavailable semantics, usage 이중 동의, `status` schema/exit/commands, profile2 public/private allowlist, human-only recovery, no-fallback 규칙, Keychain 동시 실행 수동 게이트를 구현과 동일하게 문서화한다. 기존 `usage_unknown`은 항상 차단한다는 문언(`docs/session-account-profiles.md:59-86,106-117`; `docs/orchestrator-permission-profiles.md:80-88,293-313`)은 D1의 이중 동의 예외와 기본 fail-closed를 둘 다 반영하도록 갱신한다. 같은 조직의 서로 다른 사용자를 구분할 수 없다는 한계와 시작 전 digest 검사가 실행 중 Keychain 격리를 보증하지 않는다는 한계를 명시한다.
- **R5.2** 검증은 temp HOME, synthetic registry/digest/rendered home, fake provider/verifier, `AI_SESSION_SYNTHETIC_TEST=1` 및 `AI_SESSION_SYNTHETIC_STATUS_JSON`을 사용하고 실제 credential/account home과 network/login/logout/account 전환을 사용하지 않는다. `tests/test_ai_session.py`의 temporary verifier 관행과 `tests/test_orchestrator_profiles.py`의 fake executable/rendered-home 관행을 유지한다. stale task-scoped allowlist/base/evidence-path fixture는 현 base `72ad4f24e9df5919773cb877de01007f641ae163`와 이 작업 소유 파일에 맞게 갱신하여 두 판정 명령이 모두 0으로 종료해야 한다. [근거: `dot_local/libexec/executable_ai-session-enroll-identity:79-114`; `tests/test_ai_session.py:73-161`; `tests/test_orchestrator_profiles.py:33-92,2770-2786`; `baseline-verification.md:6-25,27-77`]
- **R6.1** Claude profile 선택 경계는 개인이 아니라 조직 컨텍스트다. 기존 `authMethod`+`orgId`+`subscriptionType` canonical 구성과 v2 digest 형식은 변경하지 않고, `matched`는 enrollment 시점과 같은 조직 컨텍스트라는 사실만 뜻한다. 같은 조직의 서로 다른 사용자는 구분할 수 없으며 email은 canonical에 넣지 않고 email HMAC·salt·키·파생 digest를 만들지 않는다. [근거: `scope-change-2026-09-16.md:46-60,67-70`]
- **R6.2** 선택된 Claude profile의 현재 org-context digest가 자체 valid v2 enrollment와 일치한 뒤, 다른 active Claude profile의 valid v2 enrollment digest와 내부 비교해 하나라도 같으면 `duplicate_mapping`으로 차단·보고한다. status와 launch 모두 provider를 시작하지 않고, enrollment도 다른 profile과 같은 digest를 새로 매핑하지 않는다. 비교에 사용한 전체 digest는 Git, verifier/status JSON, stdout/stderr, 로그, tmux에 출력하지 않는다. [근거: `scope-change-2026-09-16.md:62-65`]
- **R6.3** `claude auth status --json`의 field 구성은 공식 안정 schema로 간주하지 않는다. `loggedIn=true`인데 조직 컨텍스트에 필요한 field가 누락되거나 타입·구조가 달라지면 `identity_unverifiable`로 차단하고, fallback field·email·이전 값으로 `matched`를 합성하지 않는다. `identity_unverifiable`·`duplicate_mapping`·`unavailable`은 어느 admission/status branch에서도 `matched`로 승격되지 않는다. [근거: `scope-change-2026-09-16.md:72-77,105-117`; https://code.claude.com/docs/en/cli-usage]
- **R6.4** 시작 전 digest 검사는 프로세스 시작 시점의 조직 컨텍스트만 검사하며 실행 중 Keychain 격리를 보증하지 않는다. 자동 완료와 별도로, 사람이 두 Claude profile을 전경에서 동시에 실행하고 각 profile의 조직 컨텍스트가 실행 중에도 의도한 enrollment와 일치하는지 read-only로 재확인하는 수동 게이트가 PASS여야 완료할 수 있다. `CLAUDE_CONFIG_DIR`별 Keychain 분리를 전제로 삼지 않고, 결과에는 원문 identity·전체 digest·credential을 기록하지 않는다. [근거: `scope-change-2026-09-16.md:79-86`; https://github.com/anthropics/claude-code/issues/20553]

## Acceptance criteria

- **AC-1** R1.1의 Claude synthetic matrix가 실측 camelCase success, `loggedIn=false`, missing/wrong-type key, malformed/nonzero/timeout을 구분하고 success에서 exact six fields, `logged_in`, expected identity result, `usage_unknown`, `not_applicable`을 반환한다. [실행] (CMD-2)
- **AC-2** R1.1·R2.2의 fixture에서 `loggedIn=true`인데 `authMethod|orgId|subscriptionType` 중 하나가 없거나 부정형이면 `identity_unverifiable`이고 matched가 아니며, `email|configDirectory|projectsDirectory|orgName` 값만 바꿔도 canonical bytes/digest가 동일하다. [실행] (CMD-2)
- **AC-3** R1.2의 Codex nested `auth.credentials` fixture가 chatgpt credential true, all-false, missing check, flat legacy keys, malformed string boolean, mode conflict를 각각 `logged_in`, `not_logged_in`, 또는 `unknown`으로 결정하고 auth file/summary/remediation로 identity·usage를 생성하지 않는다. [실행] (CMD-2)
- **AC-4** R1.3의 두 adapter와 status/launch 경로에 PII/token/path/digest/raw-stderr sentinel을 넣은 fixture가 stdout+stderr+public record에 sentinel 0개, extra verifier field 0개, provider process 기동 0회를 확인한다. [실행] (CMD-1 CMD-2)
- **AC-5** R2.1의 배포 registry v2가 세 active account의 provider별 identity contract과 `usage_contract="none"`을 모두 parse하고, 필드 누락·unknown·provider mismatch·strict v1 fixture는 verifier sentinel 0회와 `blocked_contract`을 보인다. legacy `version=1` unit fixture의 기존 selection test는 계속 통과한다. [실행] (CMD-1 CMD-2)
- **AC-6** R2.2의 canonicalization이 key order, 동등 UUID case, NFC, ASCII edge whitespace 변형에 동일 v2 bytes/digest를 내고 auth/org/subscription 중 한 값의 의미 변경에는 다른 digest를 내며 control character·invalid UUID를 거부한다. [실행] (CMD-2)
- **AC-7** R2.3의 fixture가 missing file→`not_enrolled`/`enrollment_required`, legacy 64hex→`stale_enrollment`/`enrollment_required`, v2 조직 컨텍스트 match→`matched`, v2 mismatch→`identity_drift`, unsafe mode/owner/type/symlink/format→`unknown`/`blocked_verifier`를 확인하고 enrollment success file은 exact `v2:<64hex>\n`, mode 0600, parent 0700이다. [실행] (CMD-2)
- **AC-8** R2.4의 Codex unavailable fixture가 digest path read/write 0회, verifier/internal admission/status에서 exact `unavailable`을 보이고 `matched`를 포함하지 않으며 기존 binding/startup record field set을 바꾸지 않는다. 미선언·Claude unavailable·Codex matched 계약 모순은 provider process 0회와 `blocked_verifier`다. [실행] (CMD-1 CMD-2)
- **AC-9** R2.5의 2×2 matrix(account `none|provider_status` × flag absent|present)에서 exact `none+present`만 provider 시작 또는 status ready가 가능하고 나머지 세 조합은 `usage_unknown`으로 차단된다. 허용 조합의 payload, child env, binding/startup record, status JSON은 모두 `usage_unknown`이며 `sufficient`를 생성하지 않는다. [실행] (CMD-1 CMD-2)
- **AC-10** R2.6의 교차 matrix가 login failure에서 unavailable/usage consent를 주어도 `login_required`, Claude drift에서 usage consent를 주어도 `identity_drift`, enrollment 부재에서 usage consent를 주어도 `enrollment_required`를 반환한다. 각 case의 verifier는 1회, provider/fallback/reselection은 0회이다. [실행] (CMD-1 CMD-2)
- **AC-11** R3.1의 profile2 source mirror와 synthetic deployed tree의 file set·bytes·regular/non-symlink 여부가 canonical quality-goal tree와 quality-reviewer에 정확히 일치하고, deployed skill에서 reviewer relative path가 regular file로 resolve된다. [실행] (CMD-2)
- **AC-12** R3.2의 profile2 source/deployed allowlist 검사가 `settings.json`, `.claude.json`, `.credentials.json`, credential/token glob, `sessions`, `projects`, `history.jsonl`, `backups`, `file-history`, `debug`, `todos`, `plans`, `plugins`, symlink을 각각 0개로 확인하고 `.chezmoiignore`의 기존 기본-home settings deny와 profile2 deny를 둘 다 확인한다. [실행] (CMD-2)
- **AC-13** R3.3의 temp HOME/chezmoi fixture에서 source→profile2 target diff는 allowlisted public asset만 포함하고 synthetic email/token/account-id/config-home/session sentinel은 diff와 Git-source scan에 0개이며 실제 HOME/account home access sentinel은 호출 0회이다. [실행] (CMD-2)
- **AC-14** R4.1의 `status` fixture가 launch와 동일 binding/verifier input을 1회 소비하되 provider exec, browser/login helper, enrollment helper, digest/registry/account-home/worktree/tmux write sentinel을 모두 0회로 유지하고 program 인자를 거부한다. [실행] (CMD-1 CMD-2)
- **AC-15** R4.2의 table-driven fixture가 `ready`, `login_required`, `enrollment_required`, `blocked_verifier`, `identity_drift`, `identity_unverifiable`, `duplicate_mapping`, `usage_unknown`, `blocked_usage`, `blocked_contract`, `blocked_binding`, `blocked_policy`를 각각 exact status JSON/exit code로 구분하고 모든 ready case가 launch admission 판정과 일치한다. 선택 전 실패는 null account profile을 가지며 consented unknown/Codex ready의 하위 status는 각각 `usage_unknown`/`unavailable`로 남는다. [실행] (CMD-1 CMD-2)
- **AC-16** R4.3의 모든 status output이 exact top-level/nested field set을 지키고 login/enrollment/drift/usage case에 상태별 허용 command ID만 반환하며 ready/blocked/identity unverifiable/duplicate mapping case의 commands는 empty이다. OAuth URL/code, token, email, account/org ID, digest, config-home path, raw reason/output sentinel은 stdout+stderr에 0개이다. [실행] (CMD-1 CMD-2)
- **AC-17** R4.4의 integration contract test/documentation이 #118 result를 status input으로 넘기는 순서와 ready 후에만 foreground action을 허용하는 규칙을 확인하고, #118 소유 경로의 changed-file count가 0이며 네 공유 충돌 파일이 rebase 대상으로 문서에 나열된다. [실행] (CMD-2)
- **AC-18** R5.1의 두 운영 문서에 registry/canonical v2, `matched`의 조직 컨텍스트 의미와 개인 식별 한계, duplicate mapping, identity unverifiable/unavailable, dual-consent matrix, status schema/status/exit/commands, profile2 allowlist/denylist, human-only foreground recovery, no fallback, Keychain 동시 실행 수동 게이트가 모두 존재하고 항상-block 문언이 dual-consent 예외를 누락하지 않는다. [실행] (CMD-2)
- **AC-19** R5.2의 두 판정 명령이 temp/synthetic fixture만으로 각각 exit 0이고, test source에서 real login/logout/account switch/credential copy·rename·symlink/실제 provider network 실행이 0개이며 현 base·file ownership fixture가 이 task 범위와 일치한다. [실행] (CMD-1 CMD-2)
- **AC-20** R1.1–R6.4 교차 회귀 matrix에서 unavailable·identity unverifiable·duplicate mapping은 matched로, consented usage unknown은 sufficient로 변경되지 않고, 좁아진 matched 의미와 각 예외 branch가 login·binding·scope·cost·exact-contract gate를 우회하지 않으며 public asset 배포가 untrusted settings/secret/history 경계를 넓히지 않는다. [실행] (CMD-1 CMD-2)
- **AC-21** R6.1 fixture에서 같은 email이고 서로 다른 `orgId`인 두 profile은 서로 다른 기존 v2 digest를 만들며 중복으로 오판되지 않고, 서로 다른 email이고 같은 `authMethod`·`orgId`·`subscriptionType`인 두 입력은 같은 digest를 만든다. 후자의 `matched`는 같은 조직 컨텍스트만 뜻하고 개인 동일성을 주장하지 않으며 email HMAC·salt·키·파생 digest 생성은 0회이다. [실행] (CMD-2)
- **AC-22** R6.2 fixture에서 선택 profile의 current digest가 자체 enrollment와 일치하지만 다른 active Claude profile의 valid v2 enrollment와도 같으면 status와 launch가 exact `duplicate_mapping`/exit 3, empty commands, provider exec 0회를 보이고 enrollment write도 0회이다. 전체 digest sentinel은 Git 추적 source, status JSON, stdout/stderr, 로그, tmux fixture에 0개이다. [실행] (CMD-1 CMD-2)
- **AC-23** R1.3·R2.6·R4.2·R4.3·R6.2·R6.3의 교차 matrix에서 `identity_unverifiable`, `duplicate_mapping`, `unavailable`이 어느 payload/admission/status branch에서도 `matched`가 되지 않고, usage consent를 주어도 앞선 identity 차단을 덮지 않으며 provider/fallback/reselection은 0회이다. [실행] (CMD-1 CMD-2)
- **AC-24** R1.1·R4.2·R6.3의 Claude fixture에서 `loggedIn=true` 이후 required field 누락, wrong type, nesting 변화 각각은 exact `identity_unverifiable`/exit 3, empty commands, provider exec 0회이고 fallback field·email·이전 digest로 `matched`를 만들지 않는다. [실행] (CMD-2)
- **AC-25** R5.1·R6.1의 두 운영 문서는 `matched`가 enrollment 시점과 같은 조직 컨텍스트라는 뜻이며 개인 동일성을 증명하지 않고 같은 조직의 서로 다른 사용자를 구분할 수 없다는 한계를 명시한다. 또한 email canonical/HMAC 방향이 폐기됐고 같은 email의 서로 다른 조직 profile을 허용해야 함을 명시한다. [실행] (CMD-2)
- **AC-26** R5.1·R6.4의 완료 기록은 자동 CMD-1·CMD-2와 별도로 사람이 두 Claude profile을 전경에서 동시에 실행해 실행 중 각 조직 컨텍스트를 read-only로 재확인한 수동 게이트의 PASS를 포함한다. PASS 전에는 완료로 판정하지 않고, 운영 문서의 절차와 완료 기록에는 raw identity·전체 digest·credential이 없어야 한다. [문서] `docs/session-account-profiles.md` 와 `docs/orchestrator-permission-profiles.md` 와 `report.md` 의 Keychain 동시 실행 수동 게이트 절차·결과

## Requirements traceability

This table maps every requirement to acceptance criteria and the judgement method that proves the mapping.

| Requirement | Acceptance criteria | Judgement method |
|---|---|---|
| R1.1 | AC-1, AC-2, AC-4, AC-20, AC-24 | CMD-2의 Claude official-status/schema-drift/redaction/cross-regression fixture |
| R1.2 | AC-3, AC-4, AC-20 | CMD-2의 Codex nested doctor/redaction/cross-regression fixture |
| R1.3 | AC-1, AC-3, AC-4, AC-16, AC-23 | CMD-1·CMD-2의 exact payload, malformed, non-promotion, leakage fixture |
| R2.1 | AC-5, AC-20 | CMD-1·CMD-2의 registry v2/legacy/fail-before-verifier fixture |
| R2.2 | AC-2, AC-6, AC-20, AC-21 | CMD-2의 unchanged org-context canonical bytes/digest property matrix |
| R2.3 | AC-7, AC-20, AC-21 | CMD-2의 enrollment format/status/permission/meaning matrix |
| R2.4 | AC-8, AC-10, AC-15, AC-20 | CMD-1·CMD-2의 unavailable exact-state/admission matrix |
| R2.5 | AC-9, AC-10, AC-15, AC-20 | CMD-1·CMD-2의 dual-consent 2×2/admission matrix |
| R2.6 | AC-10, AC-20, AC-22, AC-23 | CMD-1·CMD-2의 identity-blocking precedence/no-fallback cross matrix |
| R3.1 | AC-11, AC-20 | CMD-2의 canonical/mirror/deployed-file equality fixture |
| R3.2 | AC-12, AC-20 | CMD-2의 explicit denylist/symlink/source fixture |
| R3.3 | AC-13, AC-20 | CMD-2의 isolated chezmoi diff and sentinel scan |
| R4.1 | AC-14, AC-20 | CMD-1·CMD-2의 read-only status side-effect sentinel |
| R4.2 | AC-15, AC-20, AC-22, AC-23, AC-24 | CMD-1·CMD-2의 extended status/exit/admission-equivalence table |
| R4.3 | AC-16, AC-20, AC-22, AC-23 | CMD-1·CMD-2의 blocked command descriptor/redaction schema check |
| R4.4 | AC-17, AC-20 | CMD-2의 dependency/order/changed-path contract check |
| R5.1 | AC-18, AC-20, AC-25, AC-26 | CMD-2 문서 계약 assertion과 운영 문서·완료 기록의 수동 게이트 판정 |
| R5.2 | AC-19, AC-20 | CMD-1·CMD-2 full suites and synthetic-only source assertions |
| R6.1 | AC-20, AC-21, AC-25 | CMD-1·CMD-2의 org-context 교차 회귀·경계 fixture와 운영 문서 의미·한계 assertion |
| R6.2 | AC-20, AC-22, AC-23 | CMD-1·CMD-2의 duplicate mapping 차단·비노출·우선순위 matrix |
| R6.3 | AC-20, AC-23, AC-24 | CMD-1·CMD-2의 schema drift fail-closed/non-promotion matrix |
| R6.4 | AC-20, AC-26 | CMD-1·CMD-2의 자동 경계 비우회와 운영 문서·완료 기록의 Keychain 동시 실행 수동 게이트 PASS 판정 |

## Architecture

구현은 다섯 경계로 나눈다.

1. **Registry and selection boundary**: `accounts.toml` v2가 account 별 `identity_contract`과 `usage_contract`을 권위 선언한다. `load_strict_registry`가 조합을 검증하고 `Account`→`Binding`으로 두 값을 전파한다. 동적 추론과 implicit default는 없다.
2. **Official-status adapters**: Claude/Codex adapter는 공식 명령의 실측 raw JSON에서 계약에 필요한 비밀 없는 최소 field만 투영하고 exact six-field payload를 반환한다. raw stdout/stderr와 불필요 field는 adapter process 밖으로 나가지 않는다.
3. **Identity and admission core**: `ai_session_identity.py`가 Claude contract의 변경 없는 canonical v2/digest/read/compare와 active Claude profile 간 digest 중복 비교를 단일 구현한다. `classify_verifier_payload`는 Binding 선언과 explicit call consent를 결합해 identity/usage/cost를 한 번 판정하고 immutable `AdmissionDecision`을 반환한다. 이 decision의 exact fields는 `login_status`, `identity_status`, `usage_status`, `cost_limit_status`, `public_status`, `exit_code`, `admitted`이다. schema 판정 불가는 `identity_unverifiable`, profile 중복은 `duplicate_mapping`, 그 밖의 malformed/exact-contract failure는 redacted `VerificationError("blocked_verifier")`로 닫힌다. launch는 non-admitted decision을 기존 public error/exit로 변환하고 admitted decision의 원래 usage status를 child environment에 전달하며, status는 같은 decision을 직렬화한다. 두 consumer가 별도 precedence를 구현하지 않는다.
4. **Public read-only status facade**: `ai-session status`는 selection/pre-scan/verifier/classifier를 재사용하지만 exec/write path를 가지지 않는다. internal detailed state를 정해진 public enum과 secret-free command descriptor로만 projection한다.
5. **Chezmoi public-asset mirror**: canonical quality-goal/reviewer source와 profile2 target source는 전송 디렉터리만 다른 byte-identical regular-file set이다. test가 set/byte/type equality를 강제하여 수동 mirror drift를 즉시 탐지한다. denylist가 account-owned/runtime data와의 경계를 보강한다.

Admission의 핵심 invariant는 `binding valid AND login logged_in AND identity contract satisfied AND unique profile mapping AND cost contract satisfied AND usage admitted`이다. identity contract satisfied는 Claude에서만 enrollment 시점과 같은 조직 컨텍스트를 뜻하는 `matched`, Codex의 explicit unavailable contract에서는 `unavailable`이지만 두 상태를 서로 치환하지 않는다. Claude의 `matched`도 다른 active Claude profile과 digest가 중복되면 admission되지 않는다. usage admitted는 `sufficient` 또는 exact dual consent이지만 두 상태를 서로 치환하지 않는다.

## Interfaces and data flow

### Registry v2

Active account의 추가 required fields와 shipped value는 다음과 같다.

| Account | `identity_contract` | `usage_contract` |
|---|---|---|
| `codex-default` | `unavailable` | `none` |
| `claude-profile1` | `claude_auth_status_v1` | `none` |
| `claude-profile2` | `claude_auth_status_v1` | `none` |

`Account`/`Binding`은 두 contract를 immutable string으로 소유한다. verifier child에는 `AI_IDENTITY_CONTRACT`, `AI_USAGE_CONTRACT`, Claude에만 digest path를 주입하고 provider child에는 contract env를 새로 노출하지 않는다. Codex unavailable에는 digest path를 주입하지 않는다.

`AdmissionDecision.admitted`는 `public_status == "ready"`와 동치이고 이때만 exit 0이다. `usage_status="usage_unknown"` 또는 `identity_status="unavailable"`이어도 explicit contract/consent로 모든 gate를 통과했다면 admitted일 수 있지만 원래 상태 문자열은 decision 안에서 바뀌지 않는다. launch가 decision을 error로 바꾸는 adapter와 status가 JSON으로 바꾸는 adapter는 이 불변식을 검증하고 새로운 성공 상태를 합성하지 않는다.

### Verifier and enrollment flow

Claude flow는 `observed auth-status JSON -> loggedIn gate -> required-field schema gate -> unchanged shared org-context canonical projection -> own versioned digest compare -> cross-profile duplicate compare -> six-field redacted payload`이다. enrollment helper도 동일 projection과 duplicate compare를 사용하여 verifier/enroller field drift 및 중복 매핑을 막는다. required field가 없거나 구조가 달라지면 `identity_unverifiable`로 닫는다. Codex flow는 `doctor JSON -> auth.credentials login projection -> identity_status=unavailable -> usage_unknown -> six-field redacted payload`이며 identity helper를 호출하지 않는다.

Verifier domain은 다음과 같다.

| Field | Allowed values |
|---|---|
| `login_status` | `logged_in`, `not_logged_in`, `unknown` |
| `identity_status` | `matched`, `not_enrolled`, `stale_enrollment`, `identity_drift`, `identity_unverifiable`, `duplicate_mapping`, `unavailable`, `unknown` |
| `usage_status` | `sufficient`, `usage_unknown`, `blocked_usage` |
| `cost_limit_status` | `not_applicable`, `enforced`, `unknown` |

### Status CLI

호출 형태는 `ai-session status <selection args> --verifier <absolute path> [--accept-usage-unknown]`이다. status는 launcher의 shared admission result를 exec하지 않고 직렬화한다. 예시적 safe shape은 다음과 같으며 값은 alias/status만이지 raw provider identity/path가 아니다.

```json
{"account_profile":"claude-profile2","commands":[{"account_profile":"claude-profile2","command_id":"retry_with_usage_consent","provider":"claude"}],"cost_limit_status":"not_applicable","event":"profile_status","identity_status":"matched","login_status":"logged_in","provider":"claude","schema_version":1,"status":"usage_unknown","usage_status":"usage_unknown"}
```

State precedence는 `selection/contract -> login -> identity unverifiable -> identity drift -> enrollment -> duplicate mapping -> identity contract -> cost -> blocked_usage -> usage_unknown -> ready`이다. `--accept-usage-unknown`은 final usage decision에만 영향을 주며 앞 gate를 덮지 않는다.

| Public status | `commands` |
|---|---|
| `login_required` | `provider_login_foreground` 한 개 |
| `enrollment_required` | `identity_enroll_foreground` 한 개 |
| `identity_drift` | `inspect_identity_foreground` 한 개 |
| `usage_unknown` + selected account `usage_contract="none"` | `retry_with_usage_consent` 한 개 |
| `usage_unknown` + 다른 usage contract | 빈 배열 |
| `ready`, `identity_unverifiable`, `duplicate_mapping`, `blocked_verifier`, `blocked_usage`, `blocked_contract`, `blocked_binding`, `blocked_policy` | 빈 배열 |

### #118 dependency

#118이 소유한 create-worktree backend의 성공 result에서 `provider`, `account_profile`, resolved real worktree path를 소비한다. 정확한 #118 JSON schema는 #118의 권위이며 이 Spec에서 재정의하지 않는다. TUI adapter는 그 값을 `ai-session status`에 넘기는 단방향 dependency만 가진다. status의 command descriptor는 TUI가 사람이 보는 foreground pane에서 다음 조치를 안내하는 신호이지 실행 권한이 아니다.

## Failure behavior

- Official command nonzero, timeout, malformed JSON, unknown enum, extra verifier field, provider/profile mismatch는 raw detail 없이 `blocked_verifier`로 fail closed한다. Claude가 `loggedIn=true`인 뒤 조직 컨텍스트 required field가 누락되거나 타입·구조가 달라진 경우는 exact `identity_unverifiable`로 fail closed한다. 어느 경우도 retry/fallback은 없고 새 process에서만 재시도한다.
- `loggedIn=false` 또는 Codex credential all-false는 `login_required`다. backend은 `provider_login_foreground` descriptor만 제공하고 login/browser를 실행하지 않는다.
- Claude digest 미생성·legacy v1은 `enrollment_required`, valid v2 mismatch는 `identity_drift`, 자체 match 뒤 다른 active Claude profile과 같은 digest는 `duplicate_mapping`, unsafe digest object은 `blocked_verifier`다. drift와 duplicate mapping은 자동 overwrite하지 않고 사람이 조직 컨텍스트를 확인하기 전에 enrollment을 권유하지 않는다.
- Codex `unavailable`은 오류가 아니라 선언된 capability limit이지만 `matched`가 아니다. registry/payload 둘 중 하나라도 다르면 `blocked_verifier`다.
- `usage_unknown`은 dual consent 부재 시 exit 3이고 provider를 시작하지 않는다. exact dual consent 시에도 상태를 unknown으로 보존하고 automatic retry/fallback을 생성하지 않는다.
- status path에서 예상하지 못한 write/exec 시도나 schema serialization failure가 나면 provider를 시작하지 않고 redacted `blocked_verifier`로 닫힌다.
- profile2 mirror drift, forbidden path, symlink, secret sentinel, canonical asset 누락은 test failure이며 해당 chezmoi source set을 배포하지 않는다.
- #118 result가 없거나 그 result와 status selection이 모순하면 TUI는 status/backend을 추측하지 않고 중단한다. 이 작업은 #118 code에 fallback resolver를 추가하지 않는다.
- 자동 CMD-1·CMD-2가 통과해도 Keychain 동시 실행 수동 게이트가 PASS가 아니면 완료하지 않는다. 수동 게이트 실패 시 두 profile 동시 운용을 중단하고 `CLAUDE_CONFIG_DIR`별 Keychain 격리를 가정한 우회로를 만들지 않는다.

## Security and risk

PII/sensitive 경계에는 email과 그 파생값, OAuth URL/code, access/refresh/API token, account/subject/org ID 원문, config/auth file/home path, raw provider stdout/stderr, identity canonical bytes/digest, session/project/history/backup/plugin state가 포함된다. `orgId`는 Claude 조직 컨텍스트 drift와 duplicate mapping 탐지를 위해 process 내부 canonical digest input으로만 읽을 수 있지만 원문과 전체 digest는 Git·상태 JSON·stdout/stderr·로그·tmux에 저장·출력하지 않는다. host-local enrollment file에는 기존 version marker와 SHA-256 digest만 0600으로 저장하며 email HMAC·salt·키·파생 digest는 만들지 않는다.

기본값은 fail closed다. missing/unknown registry contract, malformed provider data, required-field schema drift, unsafe digest, duplicate mapping, unavailable/identity contract mismatch, missing usage consent은 모두 시작을 차단한다. 두 예외은 provider에 제한된 exact branch이다. Codex unavailable은 registry와 payload가 함께 일치할 때만 identity gate를 대체하고, usage unknown은 registry `none`과 call flag가 함께 있을 때만 final usage gate를 대체한다. 둘 다 login, binding, scope, cost, verifier exactness, Claude duplicate mapping 차단을 우회하지 않는다.

Claude org-context digest는 account-selection control이며 개인 인증 증명이 아니다. 같은 조직의 서로 다른 사용자는 같은 digest를 만들 수 있으므로 구분하지 못한다. 시작 전 digest 검사는 실행 중 credential source가 바뀌지 않는다는 보장도 제공하지 않는다. 이 잔여 위험은 운영 문서의 명시적 한계와 사람의 Keychain 동시 실행 수동 게이트로 관리한다.

Profile separation은 account-selection policy이지 security sandbox가 아니다(`docs/orchestrator-permission-profiles.md:37-64`). profile2 asset mirror는 코드/문서/fixture로 이루어진 공용 quality-goal bundle과 reviewer만 허용한다. account `settings.json`은 비밀이 없어도 permissions/hooks 입력이므로 untrusted이며 공용 asset으로 재분류하지 않는다. symlink 금지는 source가 account-owned/runtime tree를 간접 가리키는 경로도 차단한다.

주요 risk와 완화는 다음과 같다.

- Official CLI schema drift: strict type/domain 검사와 `identity_unverifiable` 또는 unknown→blocked mapping, synthetic schema matrix로 완화한다.
- Digest schema confusion: v2 prefix와 legacy v1 explicit stale state로 완화한다.
- Individual identity confusion: `matched`를 같은 조직 컨텍스트로 한정하고 같은 조직의 서로 다른 사용자를 구분하지 못함을 문서화해 완화한다.
- Duplicate profile mapping: active Claude profile 간 내부 digest 비교, `duplicate_mapping` 차단, 전체 digest 비노출로 완화한다.
- Keychain cross-profile coupling: 시작 시점 검사와 실행 중 격리를 구분하고 별도 사람 전경 동시 실행 게이트로 완화한다.
- Codex identity confusion: unavailable를 matched로 표시하지 않고 provider-specific registry pairing으로 완화한다.
- Usage consent laundering: 2×2 negative matrix와 output-state immutability로 완화한다.
- Public asset drift/secret ingress: exact file-set/byte equality, denylist, sentinel scan, no-symlink 검사로 완화한다.
- #118 merge conflict: 소유 경로 0-change 검사와 명시된 네 공유 파일 rebase 목록으로 완화한다.

## Test strategy

### 판정 명령 표

| ID | 명령 | 통과 조건 |
|---|---|---|
| CMD-1 | `python3 tests/test_ai_session.py` | `tests/test_ai_session.py`의 legacy selection/launch와 신규 registry, dual-consent, unavailable, status/redaction unit matrix가 모두 통과하고 exit 0이다. |
| CMD-2 | `python3 tests/test_orchestrator_profiles.py` | provider official-status adapter, canonical/enrollment, profile2 chezmoi asset, status backend, docs, cross-regression full contract suite가 모두 통과하고 exit 0이다. |

이 저장소에는 pytest 설정/모듈이 없고 `python3 -m pytest`는 실제로 실행되지 않는다. 두 파일은 `unittest.main()` entrypoint를 갖춘다. 따라서 존재하지 않는 명령을 만들지 않고 저장소에서 실제 동작이 확인된 파일 직접 실행을 판정 명령으로 쓴다(`baseline-verification.md:6-25`). 현 baseline의 CMD-1은 19 tests OK이고 CMD-2의 3 failures는 stale #103 allowlist/base/evidence path fixture이므로, 구현은 fixture를 현 base/task scope로 갱신한 후 두 suite 모두 exit 0을 요구한다(`baseline-verification.md:27-77`).

테스트는 다음 layer를 반드시 포함한다.

- Unit/contract: provider JSON 타입·구조 matrix, 변경 없는 org-context canonical property matrix, versioned digest file·cross-profile duplicate matrix, registry v2 domain, six-field payload, admission 우선순위, usage 2×2, status enum/exit/command schema.
- Integration: temp HOME에 fake provider/verifier/enrollment executable을 배치하고 launcher/status의 invocation count, environment scrub, no provider exec, no write를 sentinel로 판정한다.
- Deployment: isolated chezmoi source/destination에서 profile2 mirror set/bytes/type, denylist, diff content, reviewer resolution을 판정한다.
- Documentation/scope: `matched`의 조직 컨텍스트 의미, 개인 식별 한계, email HMAC 폐기, Keychain 수동 게이트와 exact phrases/schema table을 검사하고 #118-owned prefix의 changed-file count 0과 shared rebase list를 판정한다.
- Cross-regression: `unavailable != matched`, `identity_unverifiable != matched`, `duplicate_mapping != matched`, `usage_unknown != sufficient`, login/binding/scope/cost/duplicate precedence, public asset allowlist≠account state의 짝 matrix를 두 suite에 반복해 한 해소가 다른 전제를 깨지 않는지 확인한다.

모든 fixture는 `TemporaryDirectory`, synthetic registry/digest/home, fake binaries, `AI_SESSION_SYNTHETIC_TEST=1`, `AI_SESSION_SYNTHETIC_STATUS_JSON`을 사용한다. 실제 HOME의 account config, credential, login state, identity file을 읽거나 바꾸지 않고 실제 provider/network/account 전환을 실행하지 않는다. 기존 enrollment hook은 provider raw fixture를 injection하는 목적에 적합하므로 유지하되 camelCase/nested payload를 받도록 계약을 갱신한다.

CMD-1·CMD-2와 별도로 AC-26의 Keychain 동시 실행 검증은 사람이 실제 두 profile을 전경에서 동시에 실행해 read-only 상태를 재확인하는 수동 완료 게이트다. 자동 fixture가 이 게이트를 대체하거나 `CLAUDE_CONFIG_DIR`별 Keychain 격리를 증명했다고 간주하지 않는다.

## Decisions

### D1. Usage admission은 확정된 이중 동의로만 연다

`usage_contract="none"` 선언과 `--accept-usage-unknown` 호출 flag가 둘 다 있을 때만 연다. 선언만으로 항상 여는 방식, flag만으로 registry policy를 무시하는 방식, 로그인을 usage로 추론하는 방식은 모두 기각한다. 선택 근거는 `authoritative-inputs.md:138-148`이며 unknown 상태 보존은 operator가 capability limit을 계속 볼 수 있게 한다.

### D2. Identity는 Claude digest contract와 Codex unavailable contract로 나눈다

모든 provider에 subject ID를 요구하는 공통 스키마, Codex auth file path를 identity로 쓰는 방식, unavailable을 matched로 위장하는 방식을 기각한다. Claude는 현재 실측된 required field만 digest하고 schema가 달라지면 fail closed하며, Codex는 선언·표시 모두 unavailable로 남긴다. 선택 근거는 `authoritative-inputs.md:150-157`과 `scope-change-2026-09-16.md:72-77`이다.

### D3. Profile2에는 chezmoi regular-file mirror만 배포한다

runtime copy, symlink, 공유 `~/.agents` 경로에 대한 우연한 의존을 기각한다. `CLAUDE_CONFIG_DIR`에 상대적인 정규 target에 reviewed regular files를 놓고 byte equality test로 중복 drift를 제어한다. 선택 근거는 `authoritative-inputs.md:159-163`이며 `settings.json`은 공용 asset이 아닌 untrusted account input으로 계속 배제한다.

### D4. Setup/admission backend는 `ai-session status` read-only facade로 둔다

별도 binary, launch의 dry-run flag, TUI 내 verifier 재구현을 비교했다. 별도 binary는 selection/admission 논리를 중복하고, dry-run은 exec path와 side-effect 경계가 모호하며, TUI 재구현은 drift를 만든다. 기존 `ai-session`의 shared selection/classifier를 쓰되 exec/write branch가 없는 subcommand가 가장 작은 권한 표면이다. 선택 근거는 `authoritative-inputs.md:165-175`이다.

### D5. Registry와 identity digest를 명시적 v2로 versioning한다

기존 schema 1 의미를 묵시적으로 바꾸는 방식은 구 digest와 새 digest를 구별할 수 없고 old registry가 unsafe default로 통과할 수 있어 기각한다. strict registry v1은 명시적 deployment incompatibility로 차단하고, digest v1은 읽되 통과시키지 않은 `stale_enrollment`로 mapping한다. 현 host에 enrollment directory가 없다는 실측(`authoritative-inputs.md:106-116`)로 data-loss migration은 필요 없지만, 예상 밖 host의 old file도 조용히 drift로 오판하지 않는다.

### D6. Public status는 행동 가능성과 원시 capability 상태를 동시에 보존한다

top-level `ready`는 다음 launch가 admission될 수 있음을 뜻하고, 하위 `identity_status`/`usage_status`는 `unavailable`/`usage_unknown`을 그대로 보존한다. ready를 identity/usage success와 동의어로 쓰는 방식과 non-ready를 모두 generic blocked로 압축하는 방식을 기각한다. 이 분리가 D1/D2의 “승격 금지”와 TUI의 행동 결정을 둘 다 만족한다.

### D7. Command 안내는 alias-only descriptor로 제공한다

literal shell command에 config-home를 넣는 방식은 출력 금지를 깨고, backend가 직접 login/enrollment하는 방식은 read-only 경계를 깨므로 기각한다. command ID+provider+public alias descriptor만 반환하고 #118/TUI가 이미 해석한 profile context의 foreground pane에서 사람에게 제시한다. blocked contract/verifier에는 자동 복구 command를 제공하지 않는다.

### D8. 판정는 실재하는 unittest entrypoint와 synthetic fixture만 사용한다

pytest를 새 dependency로 추가하거나 실행되지 않는 명령을 기록하는 방식을 기각한다. `baseline-verification.md:6-25`의 실측과 기존 test fixture 관행을 따른다. stale #103 scaffolding은 현 base/task ownership으로 갱신하되 product behavior를 변경하는 workaround을 추가하지 않는다.

### D9. 선택 경계는 조직 컨텍스트다

Claude profile이 구분하는 단위는 개인 사용자가 아니라 profile에 배정된 조직 컨텍스트다. 같은 조직의 서로 다른 사용자를 구분할 수 없다는 한계를 공개 계약과 운영 문서에 남긴다.

### D10. 기존 digest를 그대로 재사용한다

`authMethod`+`orgId`+`subscriptionType` canonical 구성과 schema 2 digest를 변경하지 않는다. email은 canonical에 넣지 않고 email 원문이나 HMAC·salt·키·파생 digest를 만들지 않는다. 같은 email이면서 다른 조직인 현재 두 profile을 중복으로 오판하는 폐기된 email fingerprint 방향을 채택하지 않는다.

### D11. `matched`는 같은 조직 컨텍스트만 뜻한다

`matched`는 현재 digest가 해당 profile의 enrollment 시점 org-context digest와 같다는 뜻이다. 개인 동일성을 증명하거나 같은 조직 안의 사용자를 구분한다는 의미로 사용하지 않는다.

### D12. 중복 조직 컨텍스트 매핑은 차단한다

선택 profile의 digest가 다른 active Claude profile의 valid v2 enrollment digest와 같으면 `duplicate_mapping`으로 차단한다. 비교는 process 내부에서만 수행하고 전체 digest를 Git, 상태 JSON, stdout/stderr, 로그, tmux에 노출하지 않는다.

### D13. 개인 식별 한계는 공개 계약이다

같은 조직의 서로 다른 사용자는 구분할 수 없다는 한계를 Spec, 두 운영 문서, 완료 판정에 숨김없이 명시한다. 이 한계를 `matched` 성공 상태로 덮지 않는다.

### D14. 비공식 auth status schema 변화는 fail closed한다

공식 CLI 문서는 `claude auth status`가 JSON을 출력한다고 설명하지만 조직 컨텍스트에 필요한 field 구성을 안정 schema로 보장하지 않는다. required field 누락이나 구조 변화는 `identity_unverifiable`로 차단하고 fallback identity를 합성하지 않는다. 근거는 `scope-change-2026-09-16.md:72-77`과 https://code.claude.com/docs/en/cli-usage 다.

### D15. Keychain 동시 실행 검증은 별도 수동 게이트다

시작 전 digest 검사는 실행 시점 1회 검사이며 실행 중 Keychain 격리를 보증하지 않는다. `CLAUDE_CONFIG_DIR`별 Keychain 분리를 가정하지 않고, 사람이 두 profile을 전경에서 동시에 실행해 read-only로 조직 컨텍스트를 재확인하는 AC-26을 별도 완료 게이트로 둔다. 근거는 `scope-change-2026-09-16.md:79-86`과 https://github.com/anthropics/claude-code/issues/20553 다.

### D16. 라운드 2는 전제 오류만 최소 수정한다

canonical 구성, strict registry v2, adapter 공식 field projection, enrollment 형식과 0700/0600·atomic replace, admission 순서, usage 이중 동의, Codex unavailable, profile2 regular-file mirror, read-only status backend, CMD-1·CMD-2와 baseline 사실은 유지한다. 개정은 `matched` 의미, duplicate mapping 차단, 알려진 한계, schema fail-closed, Keychain 수동 게이트에 한정한다.

미해결 material decision은 0개다.

<!-- strict-only:start -->

This block is required only for strict work. Any inapplicable subsection must be removed for non-strict work; within strict work, mark it as not applicable with a reason before review.

### Threat and trust boundaries

- **Trusted reviewed inputs**: repository의 registry v2, provider adapter, shared identity module, canonical quality-goal/reviewer source, explicit CLI flags, #118이 정의한 성공 result schema.
- **Untrusted inputs**: provider JSON/stdout/stderr, parent environment, account-home `settings.json` 및 모든 runtime file, digest path object/metadata, malformed registry, TUI 호출 인자, chezmoi target의 기존 개인 data.
- **Boundary controls**: exact field/domain/type checking, environment scrub, captured/redacted provider I/O, owner/mode/no-follow digest read, version marker, exact registry pairing, dual consent, regular-file mirror allowlist, explicit denylist, no-symlink check.
- **Threats**: PII leakage, path disclosure, digest substitution, schema downgrade/confusion, 개인 identity로 과대 해석된 matched, duplicate profile mapping, 비공식 schema drift의 success 강등, fake matched/sufficient promotion, consent laundering, 실행 중 Keychain profile coupling, public asset 경로를 통한 settings/credential ingress, #118 input mismatch. 각 자동 판정 threat는 AC-4, AC-5, AC-7–AC-13, AC-16, AC-20–AC-25로 판정하고 Keychain coupling은 AC-26 수동 게이트로 판정한다.

### Authorization and tenant isolation

tenant는 account profile alias+provider+resolved real workspace scope+binding generation이다. Claude의 org-context digest는 이 선택 경계를 보강하지만 개인 identity나 OS security tenant는 아니다. status/launch의 identity/usage 예외은 선택된 단일 account에만 적용되며 다른 account/provider/root에 fallback할 권한을 주지 않는다. duplicate mapping은 다른 active Claude profile과의 digest equality만 내부 확인하고 해당 profile의 identity 원문이나 전체 digest를 공개하지 않는다. explicit/stored selection도 current real path scope를 우회하지 못한다(`dot_local/bin/executable_ai-session:788-868`). profile2 공용 자산은 실행 코드/문서일 뿐 account credential tenant를 공유하지 않는다. profile separation이 OS security isolation이 아니므로 이 Spec은 account root에 추가 filesystem 권한을 부여하지 않는다.

### Migration, compatibility, and rollback

Source rollout은 registry v2, launcher/parser, two adapters, shared identity/enrollment, tests, docs, profile2 public assets, `.chezmoiignore`를 하나의 compatible set으로 배포한다. mixed deployment에서 strict registry v1/v2 불일치는 provider 전 `blocked_contract`로 닫힌다. legacy non-strict `version=1` unit path는 별도 유지한다.

Claude v1 digest file은 삭제·자동 overwrite하지 않고 `stale_enrollment`으로 보고한다. 사람이 선택 profile의 현재 조직 컨텍스트를 확인한 뒤 foreground enrollment를 명시 실행해야 v2로 대체된다. 현 host에 identity directory가 없으므로 자동 backfill은 없다.

Rollback trigger는 official JSON false-positive login, identity digest instability, org-context matched의 개인 동일성 오표시, identity unverifiable/duplicate mapping/unavailable의 matched 승격, single-consent admission, secret/path/digest leakage, profile2 forbidden-file deployment, status side effect, #118-owned path 변경이다. rollback은 reviewed source set을 전체로 이전 compatible version으로 되돌리는 별도 변경이며 running process, account home, credential, identity file, session history, worktree를 변경하지 않는다. v2 enrollment file을 v1으로 자동 downgrade하지 않는다.

### Failure recovery and observability

Observability는 verifier six-field JSON, status exact JSON, 기존 redacted launch failure/account binding/startup record, CLI exit code로 제한한다. raw provider JSON/stderr, digest, identity value, account/config path는 log/metric/trace로 전파하지 않는다. 별도 network telemetry, retry metric, production alerting은 해당 없음: 이 도구는 host-local CLI이고 자동 retry/service daemon이 아니므로 public state+exit code+test evidence가 관측 계약이다.

Recovery는 `login_required`의 provider login, `enrollment_required`의 조직 컨텍스트 확인 후 explicit enrollment, `identity_drift`의 intended organization 재확인, `identity_unverifiable`의 reviewed adapter/schema repair, `duplicate_mapping`의 profile-to-organization 배정 재확인, `usage_unknown`의 policy/explicit consent 결정, `blocked_verifier`의 reviewed adapter/metadata repair를 사람이 foreground에서 수행한 후 새 status process를 시작하는 순서다. backend은 recovery를 실행하거나 account를 바꾸지 않으며 unverifiable/duplicate 상태에는 자동 command descriptor를 제공하지 않는다.

### High-risk end-to-end verification

High-risk path은 `registry v2 -> provider adapter -> org-context own/duplicate comparison -> identity/usage classifier -> status/launch -> public record` 전체와 `canonical source -> chezmoi profile2 regular files -> quality-goal reviewer resolve` 전체다. CMD-1과 CMD-2 둘 다 exit 0이고 AC-4, AC-7–AC-10, AC-12–AC-16, AC-20–AC-25의 negative sentinel/assertion이 모두 통과하며 AC-26 수동 게이트도 PASS여야 한다. 하나라도 실패하면 중단하고 자동 fixture를 실제 account 검증의 대체물로 간주하지 않는다.

최종 cross-regression은 다음 여섯 쌍을 반드시 재검토한다: (1) 좁아진 org-context `matched`가 개인 동일성을 주장하거나 duplicate mapping을 우회하지 않는지, (2) identity unavailable admission이 login/binding/scope/cost를 우회하지 않는지, (3) usage dual consent가 identity unverifiable/duplicate mapping/drift를 덮지 않는지, (4) ready가 unavailable/identity unverifiable/duplicate mapping/usage unknown을 matched/sufficient로 재기록하지 않는지, (5) 새 차단 상태가 admission 순서나 fallback 0회 계약을 바꾸지 않는지, (6) profile2 배포의 기본 fail-closed와 settings/credential/session 경계를 넓히지 않는지. 자동 교차 판정 근거는 AC-20·AC-22·AC-23/CMD-1/CMD-2이고 실행 중 Keychain 격리는 AC-26 수동 게이트로 별도 판정한다.

### No production mutation confirmation

자동 workflow에 production mutation은 없다. 실제 login/logout/browser OAuth, identity enrollment, account switch, credential/token/account-home/session history 읽기·복제·rename·symlink, `chezmoi apply`, worktree/tmux 생성·이동, commit/push/merge/deploy를 실행하지 않는다. 자동 검증은 temp synthetic state와 비밀 없는 상태 계약만 사용한다. AC-26은 사람이 전경에서 수행하는 read-only 동시 실행 완료 게이트이며 자동 workflow가 인증을 조작할 권한을 주지 않는다. 미래의 실제 source apply, foreground login/enrollment, #118 worktree 생성은 이 automated workflow 밖의 별도 사용자 행위다.

<!-- strict-only:end -->
