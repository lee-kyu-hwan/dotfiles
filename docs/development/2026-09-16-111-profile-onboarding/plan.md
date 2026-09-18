# Quality Goal Implementation Plan

- Task ID: 20260916T025114Z-111-claude-code-2-1-273-auth-status-호환성-f224ab4d
- Mode: strict
- Status: PLAN_REVIEW
- Created: 2026-09-16
- Updated: 2026-09-16
- Source goal: #111 Claude Code 2.1.273 auth status 호환성, identity enrollment/verifier 계약, profile2 비밀 없는 공용 스킬 배포, profile setup/admission backend 계약을 구현한다

## Spec link

승인 대상은 [spec.md](./spec.md)이며 이 Plan이 고정하는 SHA-256은 `471cce1a2877250190047fbfb0857382b7fa5a38a61b76c698efc857f45c3486`이다. 구현 중 Spec 본문이나 digest가 달라지면 구현을 중단하고 quality-goal의 가장 이른 영향 단계로 돌아간다. 확정 입력은 [authoritative-inputs.md](./authoritative-inputs.md), 범위 변경 근거는 [scope-change-2026-09-16.md](./scope-change-2026-09-16.md), 구현 전 검증 기준은 [baseline-verification.md](./baseline-verification.md)다.

## Global constraints

- 구현 변경은 아래 File map의 modify/create 경계 안에서만 한다. `dot_agents/skills/create-worktree/**`, `dot_claude/skills/create-worktree/**`, `docs/development/2026-09-16-118-profile-aware-create-worktree/**`, create-worktree profile path resolver, workmux 생성 adapter는 #118 소유이므로 읽기만 하고 변경하지 않는다.
- 모든 동작 검증은 `TemporaryDirectory`, temp `HOME`, synthetic registry/digest/rendered home, fake provider/verifier, `AI_SESSION_SYNTHETIC_TEST=1`, `AI_SESSION_SYNTHETIC_STATUS_JSON`만 사용한다. 실제 login/logout, browser OAuth, account 전환, credential/token/account-home 읽기·복사·rename·symlink, identity enrollment, provider network/process 기동, 실행 중 worktree/tmux 이동을 실행하지 않는다.
- 자동 검증에서 실제 `chezmoi` 바이너리와 `chezmoi apply`를 호출하지 않는다. 기존 `test_chezmoi_fixture_render`의 복사 기반 render simulation으로 격리된 synthetic source/destination의 diff를 만들고, `test_high_risk_e2e`의 live-action sentinel이 `chezmoi` 호출을 차단한다.
- test-first 기록은 각 태스크에서 지정한 테스트 메서드를 먼저 추가하고 CMD-1 또는 CMD-2의 실패를 보존한 뒤 최소 구현을 하고 같은 명령의 exit 0을 기록하는 순서다. 이 저장소에는 pytest·CI·type check·build가 없고 `pre-commit` 실행기도 설치돼 있지 않다. 최종 판정은 저장소에서 확인된 두 unittest 파일 entrypoint인 CMD-1, CMD-2뿐이다.
- provider JSON, stderr, email, OAuth URL/code, token, account/subject/org ID 원문, identity canonical bytes/digest, config/auth/home path는 verifier/status/public record/test failure에 출력하지 않는다. 실패 assertion도 sentinel의 부재와 호출 횟수만 보고 원문을 echo하지 않는다.
- strict registry에는 implicit contract default가 없다. schema/contract/field/domain/provider 조합이 하나라도 맞지 않으면 verifier 호출 전 `blocked_contract`로 닫고, legacy non-strict `version=1` selection unit path만 별도로 유지한다.
- `identity_contract="unavailable"`과 usage 이중 동의는 독립적인 정확 일치 예외다. 어느 예외도 binding, resolved scope, login, verifier exact-field, cost gate를 건너뛰거나 `unavailable`을 `matched`로, `usage_unknown`을 `sufficient`로 바꾸지 않는다.
- Claude 선택 경계는 개인이 아니라 기존 `authMethod`+`orgId`+`subscriptionType` 조직 컨텍스트다. canonical 구성과 v2 digest는 바꾸지 않고, `matched`는 enrollment 시점과 같은 조직 컨텍스트만 뜻한다. 같은 조직의 서로 다른 사용자는 구분할 수 없으며 email 원문·HMAC·salt·키·파생 digest를 만들지 않는다.
- `duplicate_mapping` 비교는 launcher/classifier 프로세스가 직접 digest를 읽는 방식이 아니라 Claude verifier child가 수행한다. launcher의 `active_claude_identity_digest_paths(registry, binding)`는 strict v2에서 selection 가능한 `Registry.accounts` 중 다른 Claude `claude_auth_status_v1` profile만 registry 기반으로 열거하고, 선택 profile과 같은 identity root(기본 `~/.local/share/ai-account-profiles/identities`, synthetic fixture에서는 `AI_SESSION_IDENTITY_ROOT`) 아래 `claude/<public-alias>.sha256` 절대 경로를 만든다. 정렬된 path 배열은 compact JSON 환경변수 `AI_OTHER_ACTIVE_CLAUDE_IDENTITY_DIGEST_FILES`로 `verify_admission()`이 verifier child에만 주입한다. `[legacy_records]`, registry에서 제거되었거나 selection 불가능한 비활성 profile, 선택 profile 자체는 열거하지 않고 고정 디렉터리 전체를 scan하지 않는다.
- Claude verifier는 선택 profile이 자체 valid v2 enrollment와 `matched`인 뒤에만 위 목록을 검사한다. 다른 active profile의 valid v2만 constant-time 비교 후보이며 같은 값이면 `duplicate_mapping`이다. 다른 profile의 파일 부재와 exact v1 legacy file은 valid v2 mapping이 아니므로 비교에서 제외하고, 존재하지만 owner/mode/type/symlink/format이 부정형이면 uniqueness를 증명하지 못한 것으로 `blocked_verifier`에 닫는다. 환경변수 누락·malformed·목록 밖 경로도 `blocked_verifier`이며 전체 digest와 목록은 public payload/record/log에 노출하지 않는다.
- Explicit enrollment helper는 같은 strict registry 기준으로 다른 active Claude path를 직접 구성하고, 새 v2 line을 쓰기 전에 같은 `find_duplicate_enrollment()`를 호출한다. equal valid v2이면 secret-free `duplicate_mapping`/exit 3으로 종료하고 directory/temp/destination write를 0회 유지한다. 비활성/v1/missing/unsafe 처리는 verifier flow와 같고 enrollment helper도 고정 디렉터리 전체를 scan하지 않는다.

Spec 리뷰 finding은 다음과 같이 해소한다.

| Finding | 확정 계약 | 구현/검증 태스크 |
|---|---|---|
| SPEC-001 | `AI_AUTH_KIND`를 `Binding.auth_kind`에서 verifier child에만 계속 주입한다. `AI_IDENTITY_CONTRACT`, `AI_USAGE_CONTRACT`도 verifier child 전용이고 provider child에는 세 contract env를 새로 전달하지 않는다. consumer/organization adapter의 유효한 공식 상태 결과는 `cost_limit_status="not_applicable"`, malformed/unknown은 `unknown`이다. 두 official adapter의 api_payg 결과는 공식 cost 증거가 없으므로 항상 `unknown`이며 `enforced`를 합성하거나 provider JSON에서 읽지 않는다. 배포 registry에 PAYG account를 추가하거나 PAYG official adapter admission을 여는 일은 non-goal이다. classifier의 기존 PAYG `enforced` 요구는 유지되어 official adapter 경로를 fail closed한다. Spec 본문에 이 세부 산출 규칙이 없더라도 이 행이 구현 handoff의 권위 있는 규칙이다. | T2의 `test_verifier_auth_kind_cost_contract`, T3의 `test_admission_precedence_and_dual_consent`, CMD-1·CMD-2 |
| SPEC-002 | `AdmissionDecision.public_status`와 launch failure record의 status 문자열은 아래 대응표로만 변환한다. `dot_local/bin/executable_ai-session`의 신설 `decision_to_launch_error()`가 launch 변환의 단일 지점이고, `status()`는 `public_status`를 그대로 직렬화한다. 기존 `error_status()`와 `failure_record()`는 변환 결과를 exit/public record에 보존한다. 이 표와 단일 변환 지점은 그대로 구현 handoff 권위를 가진다. | T3의 `test_status_to_launch_failure_mapping`, T5의 운영 문서 표, CMD-1·CMD-2 |
| SPEC-003 | v1은 exact `64 lowercase hex + LF`인 65바이트, v2는 exact `v2: + 64 lowercase hex + LF`인 68바이트다. `read_digest_file()`은 69바이트까지 읽어 trailing byte를 탐지하고 별도 v1/v2 fullmatch로 구분한다. | T2의 `test_identity_digest_version_boundaries`, CMD-2 |
| SPEC-004 | cross-profile 중복 비교의 수행자는 Claude verifier child다. launcher가 strict registry의 다른 active Claude profile을 열거해 `AI_OTHER_ACTIVE_CLAUDE_IDENTITY_DIGEST_FILES`를 verifier에만 주입하며, 다른 profile의 valid v2만 비교하고 inactive/v1/missing/unsafe 처리는 위 Global constraints대로 고정한다. | T2의 `test_org_context_identity_boundaries`, T3의 `test_duplicate_mapping_admission`, CMD-1·CMD-2 |

두 public surface의 1:1 상태 대응은 다음과 같다. `blocked_contract|blocked_binding|blocked_policy`는 selection/registry/policy exception에서 직접 생기고 나머지는 admission decision에서 생긴다.

| Status facade `status` | Launch failure record `status` | Exit | 변환/동작 |
|---|---|---:|---|
| `ready` | 해당 없음 | 0 | status는 JSON을 반환하고 launch만 provider exec 직전 단계로 진행한다. |
| `login_required` | `not_logged_in` | 3 | `decision_to_launch_error()`가 기존 launch 공개 문자열로 변환한다. |
| `enrollment_required` | `blocked_verifier` | 3 | v1/missing enrollment의 상세 상태는 status에만 보이고 launch는 기존 fail-closed 문자열을 유지한다. |
| `blocked_verifier` | `blocked_verifier` | 3 | 그대로 유지한다. |
| `identity_drift` | `identity_drift` | 3 | 그대로 유지한다. |
| `identity_unverifiable` | `identity_unverifiable` | 3 | schema 변화나 required field 부재를 그대로 보존하고 commands는 비운다. |
| `duplicate_mapping` | `duplicate_mapping` | 3 | 다른 active Claude profile과 같은 valid v2 mapping을 그대로 보존하고 provider를 시작하지 않는다. |
| `usage_unknown` | `usage_unknown` | 3 | consent가 없을 때 그대로 유지한다. |
| `blocked_usage` | `blocked_usage` | 3 | 그대로 유지한다. |
| `blocked_contract` | `blocked_contract` | 2 | `error_status()`의 기존 contract exit를 유지한다. |
| `blocked_binding` | `blocked_binding` | 4 | `error_status()`의 기존 binding exit를 유지한다. |
| `blocked_policy` | `blocked_policy` | 4 | `error_status()`의 기존 policy exit를 유지한다. |

## File map

| 경로 | 작업 | 책임과 정확한 인터페이스 |
|---|---|---|
| `dot_local/bin/executable_ai-session` | modify | 보존된 strict registry v2와 immutable `AdmissionDecision` 위에 registry 기반 `active_claude_identity_digest_paths()`, verifier-only `AI_OTHER_ACTIVE_CLAUDE_IDENTITY_DIGEST_FILES`, `identity_unverifiable|duplicate_mapping` precedence/status-launch mapping, launch/status 양쪽 usage consent parser 전달을 완성한다. |
| `dot_local/bin/executable_ai-role-session` | modify | `ROLE_CONTRACT_ID="orchestrator-permission-profiles-v2"`로 올려 role manifest·launcher·startup record의 compatible-set token을 맞춘다. 다른 role/policy 동작은 유지한다. |
| `dot_local/libexec/executable_ai-session-verify-claude` | modify | 보존된 Claude 2.1.273 projection에서 required field 부재·구조 변화를 `identity_unverifiable`로 분리하고, 자체 v2 match 뒤 verifier-only 목록의 다른 active valid v2를 비교해 `duplicate_mapping`을 반환한다. |
| `dot_local/libexec/executable_ai-session-verify-codex` | modify | Codex 0.154.0 `checks["auth.credentials"]`를 strict하게 투영하고 identity `unavailable`, usage `usage_unknown`, auth-kind cost 계약을 반환한다. identity file은 import/read하지 않는다. |
| `dot_local/libexec/ai_session_identity.py` | modify | 완료된 canonical/schema 2/65·68-byte 경계는 변경 없이 보존하고, digest를 반환·출력하지 않는 `find_duplicate_enrollment(current, other_paths)`가 valid v2 constant-time compare 및 missing/v1/unsafe 처리를 소유한다. |
| `dot_local/libexec/executable_ai-session-enroll-identity` | modify | 완료된 Claude-only explicit enrollment 위에 같은 registry-derived other-active path 열거와 pre-write duplicate helper를 추가한다. collision은 `duplicate_mapping`/exit 3과 write 0회, Codex unavailable은 기존처럼 write 전 거부다. |
| `dot_config/ai-session/accounts.toml` | modify | `schema_version=2`, `contract_id="orchestrator-permission-profiles-v2"`; 세 active account에 명시적 provider별 `identity_contract`과 `usage_contract="none"`을 선언한다. |
| `dot_config/ai-session/roles.toml` | modify | 네 role의 `registry_contract`를 v2 token으로 함께 올려 mixed deployment를 fail closed한다. |
| `dot_local/share/ai-account-profiles/claude/profile2/agents/quality-reviewer.md` | create | `dot_claude/agents/quality-reviewer.md`와 byte-identical regular non-symlink mirror다. |
| `dot_local/share/ai-account-profiles/claude/profile2/skills/quality-goal/**` | create | `dot_claude/skills/quality-goal/**` 아래 모든 regular file의 상대 경로·file set·bytes를 그대로 가진 regular non-symlink mirror다. canonical source는 수정하지 않는다. |
| `.chezmoiignore` | modify | profile2 target의 settings, `.claude.json`, credential/token, session/project/history/backup/file-history/debug/todos/plans/plugins deny pattern을 명시하고 기존 기본-home `.claude/settings.json` deny를 유지한다. |
| `tests/test_ai_session.py` | modify | 보존된 registry/admission fixture에 launch·status 각각의 usage 2×2, registry-derived duplicate input, identity 차단 precedence, exact status/launch mapping과 side-effect count를 추가한다. |
| `tests/test_orchestrator_profiles.py` | modify | 보존된 official adapter/canonical/enrollment/profile2 fixture에 org-context 의미·schema drift·duplicate mapping·문서·수동 게이트 계약을 추가하고 기존 복사 기반 render 및 live-action sentinel을 재사용한다. |
| `tests/check_installed_orchestrator_cli_contract.py` | modify | 존재하지 않는 #103 evidence 경로를 실제 존재하는 `docs/development/2026-09-15-103-orchestrator-permission-profiles-2/authoritative-inputs.md`로 교체한다. 이 파일에 고정된 Codex 0.154.0/Claude 2.1.272 help-only 증거와 checker의 기존 기대 version은 함께 유지한다. |
| `docs/session-account-profiles.md` | modify | 보존된 재작성본에 조직 컨텍스트 선택 경계, 개인 식별 한계, duplicate/unverifiable 처리, 동일 email·다른 org 허용, Keychain 동시 실행 수동 게이트 절차를 추가한다. |
| `docs/orchestrator-permission-profiles.md` | modify | status facade와 launch failure 1:1 표에 두 신설 차단 상태를 반영하고 registry 기반 duplicate 입력, profile2/#118/recovery 및 수동 게이트 완료 조건을 문서화한다. |
| `docs/development/2026-09-16-111-profile-onboarding/report.md` | create by quality-goal orchestrator after implementation | 자동 CMD 결과와 별개로 사람이 수행한 Keychain 동시 실행 수동 게이트의 PASS/FAIL과 시각만 기록한다. raw identity, 전체 digest, credential은 기록하지 않고 PASS 전에는 완료 상태로 전환하지 않는다. |
| `docs/development/2026-09-16-111-profile-onboarding/**` | inspect-only during implementation | 승인 Spec·확정 입력·baseline·Plan을 구현 근거로 읽는다. 별도 quality-goal 단계가 만드는 review/report 외에는 구현 태스크가 이 디렉터리를 수정하지 않는다. |
| `dot_claude/skills/quality-goal/**`, `dot_claude/agents/quality-reviewer.md` | inspect-only | profile2 mirror의 canonical file set/bytes 원본이다. |
| `dot_agents/skills/create-worktree/**`, `dot_claude/skills/create-worktree/**`, `docs/development/2026-09-16-118-profile-aware-create-worktree/**` | inspect-only | #118 소유 경계이며 changed-file count 0 assertion의 대상이다. |

## Task dependencies

보존된 구현에서 T1은 registry v2·legacy v1·baseline harness까지 완료됐고 T2는 official projection·identity contract 분리·65/68-byte enrollment v2까지 완료됐다. 이 두 태스크를 처음부터 다시 구현하지 않는다. T2에는 이번 Spec 개정에 필요한 `identity_unverifiable`, 조직 컨텍스트 의미 fixture, duplicate helper delta만 추가한다. 오케스트레이터가 보존 상태에서 직접 관측한 체크포인트는 CMD-1 `Ran 19 tests, OK`, CMD-2 `Ran 83 tests, OK`다. 이는 신설 AC 완료 증거가 아니므로 남은 delta 뒤 CMD-1·CMD-2를 다시 판정한다.

남은 순서는 `T2 delta → T3 completion → T4 verification/delta → T5 completion`이다. T3에는 `decision_to_launch_error()` 등 일부 구현만 존재한다. T4에는 profile2 mirror 45개 파일이 이미 있으므로 재생성하지 않고 canonical set/bytes 및 복사 기반 render를 검증해 drift가 있을 때만 동기화한다. T5의 `docs/session-account-profiles.md` 재작성본은 보존하고 신설 의미·수동 게이트 문언만 보완한다. T4는 T2/T3와 코드상 독립적이지만 같은 `tests/test_orchestrator_profiles.py`를 수정하므로 실제 편집은 직렬화한다.

T1에서 이미 갱신한 `BASE_REVISION=72ad4f24e9df5919773cb877de01007f641ae163`, `T15_ALLOWED_FILES`, `T15_ALLOWED_PREFIXES`, `test_file_ownership.expected_files`, 실제 `...-2/authoritative-inputs.md` evidence 경로를 그대로 유지한다. T4의 45개 mirror leaf ownership도 유지한다. #118 prefix는 어떤 allowlist에도 추가하지 않아 accidental modification이 계속 실패하게 한다. 공유 충돌 후보 `tests/test_orchestrator_profiles.py`, `dot_config/ai-session/accounts.toml`, `.chezmoiignore`, `docs/session-account-profiles.md`는 #118 merge 후 rebase 대상으로 유지한다.

## Tasks

### T1. Baseline harness와 registry v2 compatible set 고정

대상 AC: AC-5, AC-19 — `CMD-1` `CMD-2` `test_strict_registry_v2_contracts_and_legacy_v1_compatibility` `test_registry_contract_mixed_deployment` `test_changed_path_allowlist` `test_file_ownership` `test_portable_cli_contract`

1. **완료 상태 보존:** registry v2, legacy v1 parser, compatible-set token, current base/ownership/allowlist/evidence fixture 구현은 완료됐고 보존 체크포인트에서 CMD-1 19건과 CMD-2 83건이 통과했다. 이번 개정에서 T1 production/harness 계약을 다시 작성하지 않는다.
2. **최종 통과 검증 기록:** 남은 태스크가 끝난 뒤 CMD-1과 CMD-2를 표 순서대로 실행해 strict v2 missing/unknown/provider mismatch/strict-v1이 `blocked_contract`, verifier/provider 0회이고 legacy v1 selection과 current base/file ownership이 유지되는지 기록한다.
3. **실패/복구:** 신설 identity branch가 registry contract를 느슨하게 만들면 T1을 재설계하지 않고 해당 T2/T3 delta를 고쳐 기존 exact pairing을 회복한다. baseline fixture로 unexpected path를 숨기지 않고 File map과 #118 경계 밖 변경은 계속 실패시킨다.

### T2. Official adapter, provider별 identity와 enrollment v2 구현

대상 AC: AC-1, AC-2, AC-3, AC-6, AC-7, AC-21, AC-24 — `CMD-2` `test_claude_official_status_contract` `test_identity_canonicalization` `test_codex_doctor_status_contract` `test_identity_digest_version_boundaries` `test_identity_enrollment` `test_org_context_identity_boundaries` `test_claude_identity_unverifiable` `test_verifier_auth_kind_cost_contract` `test_identity_state_nonpromotion` `test_verifier_redaction`

1. **완료 상태 보존:** official Claude/Codex projection, provider별 identity contract, unchanged six-key canonical schema 2, exact v1 65-byte/v2 68-byte enrollment reader/writer와 atomic permission 경계는 완료됐다. email 기반 canonical/HMAC 방향이나 새 digest version을 추가하지 않는다.
2. **실패 검증 기록:** CMD-2에 `test_org_context_identity_boundaries`와 `test_claude_identity_unverifiable`을 먼저 추가한다. 같은 email·다른 org는 다른 기존 v2 digest, 다른 email·같은 canonical 3-field는 같은 digest, email/HMAC/salt/key 생성 0회를 판정한다. `loggedIn=true` 뒤 required field missing/wrong type/nesting 변화가 `identity_unverifiable`, matched/provider exec 0회인지 판정한다. 기존 `test_identity_enrollment`에는 other active equal v2가 `duplicate_mapping`/exit 3과 directory/temp/destination write 0회인지 먼저 추가한다.
3. **최소 delta:** canonical/enrollment bytes는 바꾸지 않는다. Claude adapter가 official field projection 실패를 `identity_unverifiable`로 반환하게 하고, identity helper에 `find_duplicate_enrollment(current, other_paths)`를 추가한다. helper는 자체 match 뒤 다른 valid v2만 constant-time 비교하고 missing·exact v1은 건너뛰며 unsafe existing file은 예외로 fail closed한다. enrollment helper는 strict registry에서 같은 other-path set을 만들어 `_ensure_owner_directory()`와 `_atomic_write_digest()`보다 먼저 helper를 호출한다. digest 값과 email은 반환·출력하지 않는다.
4. **통과 검증 기록:** CMD-2 exit 0을 기록한다. 기존 official/Codex/cost/enrollment matrix와 함께 조직 컨텍스트 의미, 개인 식별 한계, schema drift 비승격, 65/68-byte 호환이 모두 통과해야 한다.
5. **실패/복구:** required field 또는 다른 active digest metadata가 판정 불가이면 fallback field·email·이전 digest로 보완하지 않는다. 선택 profile schema drift는 `identity_unverifiable`, 다른 existing digest의 unsafe metadata는 `blocked_verifier`로 닫고 기존 enrollment를 삭제·overwrite하지 않는다.

### T3. Shared admission decision과 read-only status facade 구현

대상 AC: AC-4, AC-8, AC-9, AC-10, AC-14, AC-15, AC-16, AC-22, AC-23 — `CMD-1` `CMD-2` `test_verifier_redaction` `test_status_redaction` `test_unavailable_identity_admission` `test_codex_doctor_status_contract` `test_admission_precedence_and_dual_consent` `test_status_is_read_only` `test_status_schema_exit_and_commands` `test_status_to_launch_failure_mapping` `test_duplicate_mapping_admission` `test_identity_state_nonpromotion` `test_admission_fail_closed_exceptions`

1. **실패 검증 기록:** 보존된 partial T3 위에 `test_duplicate_mapping_admission`과 확장된 precedence/status tests를 먼저 추가한다. selected own v2 match+다른 active valid v2 equal, 다른 profile v1/missing/inactive, unsafe existing digest, malformed injected list를 status와 launch에서 판정하고 enrollment write 0회 증거도 결합한다. `test_admission_precedence_and_dual_consent`는 launch와 status 각각 `none|provider_status × flag absent|present` 2×2를 모두 덮고, launch flag가 `--` 뒤 remainder로 흡수되는 잘못된 호출은 동의로 인정하지 않는다.
2. **최소 구현:** 기존 partial `classify_verifier_payload()`/`AdmissionDecision`을 완성해 순서를 login→identity drift/enrollment/identity unverifiable/duplicate mapping/contract→cost→blocked usage→usage unknown→ready로 고정한다. unavailable은 Codex+registry exact pair에서만 통과하고, unknown usage는 registry `none`+현재 호출 flag에서만 마지막 usage gate를 통과한다.
3. **최소 구현:** `active_claude_identity_digest_paths(registry, binding)`가 strict `Registry.accounts`의 selection 가능한 다른 Claude contract만 열거한다. `verify_admission()`은 registry를 받아 `AI_AUTH_KIND`, `AI_IDENTITY_CONTRACT`, `AI_USAGE_CONTRACT`를 verifier child에 주입하고, Claude contract에만 선택 profile의 `AI_IDENTITY_DIGEST_FILE`과 정렬된 compact JSON 배열 `AI_OTHER_ACTIVE_CLAUDE_IDENTITY_DIGEST_FILES`를 추가한다. 다섯 값을 `VERIFIER_ONLY_ENVIRONMENT_VARIABLES`에 두어 parent spoof 값을 덮고 provider child에서는 제거하며 Codex에는 두 digest-path env를 주입하지 않는다. 고정 디렉터리 scan과 alias/email/digest 값 env는 쓰지 않는다.
4. **최소 구현:** `build_parser()`의 `status` subparser와 `launch` subparser 양쪽에 optional `--accept-usage-unknown`을 둔다. launch의 `program`은 `argparse.REMAINDER`이므로 동의 flag는 반드시 `--` 앞에서 parse하고, 두 command 모두 `arguments.accept_usage_unknown`을 `verify_admission()`과 classifier로 전달한다. `status()`는 program remainder와 exec/write path를 갖지 않고 exact JSON을 한 줄로 반환한다.
5. **최소 구현:** `status_commands()`는 허용 네 command ID만 만들고 ready/blocked/`identity_unverifiable`/`duplicate_mapping`에는 빈 배열을 만든다. `decision_to_launch_error()`를 Global constraints의 표에 대한 유일한 launch 변환 지점으로 유지하고 status는 `public_status`를 그대로 쓴다. selection 전 contract/binding/policy failure는 account profile null인 status JSON으로 직렬화하고 기존 2/4 exit를 유지한다.
6. **통과 검증 기록:** CMD-1·CMD-2 exit 0을 기록한다. launch/status 양쪽 2×2에서 only `none+flag`가 ready/provider 시작 가능하고, identity 차단이 consent보다 먼저이며, duplicate/unverifiable은 exit 3·empty commands·provider/fallback/reselection 0회다. consented output은 `usage_unknown`, Codex output은 `unavailable`로 남고 전체 digest sentinel은 0개여야 한다.
7. **실패/복구:** serialization이나 unexpected side effect sentinel이 발생하면 provider를 시작하지 않고 redacted `blocked_verifier`/exit 3으로 닫는다. ready 불일치가 나면 status에 별도 우회 로직을 붙이지 않고 shared decision의 최초 분기부터 고친다.

### T4. Profile2 public quality bundle을 regular-file mirror로 배포

대상 AC: AC-11, AC-12, AC-13 — `CMD-2` `test_profile2_quality_bundle_mirror` `test_profile2_public_asset_denylist` `test_chezmoi_fixture_render` `test_profile2_chezmoi_diff_redaction` `test_high_risk_e2e` `test_public_asset_private_boundary`

1. **완료 상태 보존:** profile2 mirror 45개 파일과 관련 denylist/test 산출물이 보존돼 있다. canonical reviewer/quality-goal regular file set과 다를 때만 기존 mirror를 동기화하며 runtime copy script, template, symlink를 추가하지 않는다.
2. **검증 방식 고정:** `test_chezmoi_fixture_render`의 기존 복사 기반 source→synthetic destination render simulation으로 target tree와 diff를 만든다. 실제 `chezmoi` 바이너리를 호출하지 않으며 `test_high_risk_e2e`가 PATH의 `chezmoi` live-action sentinel 호출 0회를 강제한다. 같은 fixture에서 canonical/profile2 source/rendered set·bytes·type, reviewer relative resolution, denylist, actual HOME access 0회를 검사한다.
3. **통과 검증 기록:** isolated temp HOME/source/destination에서 CMD-2 exit 0을 기록한다. source와 rendered target의 file set/bytes/type가 canonical과 같고 deployed skill의 `../../agents/quality-reviewer.md`가 regular file로 resolve되며 forbidden target/symlink/sentinel/actual HOME access/실제 chezmoi 호출이 모두 0이어야 한다.
4. **실패/복구:** canonical set에 파일이 추가·삭제되었는데 mirror가 다르면 배포를 중단하고 mirror set을 다시 동기화한다. forbidden path나 sentinel이 하나라도 보이면 target에서 지우는 runtime action을 하지 않고 source allow/deny 경계를 수정한 뒤 synthetic fixture를 새로 만든다.

### T5. 운영 문서와 #118 단방향 integration 계약 고정

대상 AC: AC-17, AC-18, AC-20, AC-25, AC-26 — `CMD-1` `CMD-2` `test_118_status_dependency_and_owned_paths` `test_profile_onboarding_documentation_contract` `test_registry_exception_boundaries` `test_identity_state_nonpromotion` `test_admission_fail_closed_exceptions` `test_public_asset_private_boundary`; [문서] `docs/session-account-profiles.md` `docs/orchestrator-permission-profiles.md` `report.md`

1. **실패 검증 기록:** 보존된 `docs/session-account-profiles.md` 재작성본 위에 두 운영 문서의 조직 컨텍스트 의미, 같은 조직의 서로 다른 사용자 구분 불가, 동일 email·다른 org 허용, email HMAC 방향 폐기, duplicate input/상태, identity unverifiable, Keychain 수동 게이트를 검사하는 `test_profile_onboarding_documentation_contract` assertion을 먼저 추가한다. #118 순서·ready-only progression·owned path 0개·네 rebase 파일도 유지한다.
2. **최소 구현:** 두 운영 문서에 registry/canonical/enrollment v2와 Global constraints의 exact status→launch 표를 유지하면서 신설 의미와 registry-based duplicate flow를 추가한다. `not_logged_in` launch와 `login_required` status를 구분하고, #118 성공 result의 provider/public alias/resolved real worktree를 status input으로 넘기는 단방향 dependency만 기록한다.
3. **통과 검증 기록:** CMD-2 exit 0을 기록한다. 기본 fail-closed+exact dual-consent, 개인 식별 한계, duplicate/unverifiable empty-command 차단, 실제 recovery/OAuth/private path 부재, #118-owned path changed-file count 0을 확인한다.
4. **실패/복구:** 코드와 문서 enum/table이 다르면 문서에서 추측하지 않고 T1~T3의 tested interface를 권위로 맞춘다. #118 result schema가 아직 확정되지 않은 부분은 명시적 dependency로 남기고 fallback resolver나 adapter를 이 작업에 추가하지 않는다.
5. **수동 게이트 완료 기록:** 자동 CMD-1·CMD-2가 통과한 뒤에도 완료로 전환하지 않는다. 사람이 별도 전경에서 두 Claude profile을 동시에 실행하고 실행 중 각 조직 컨텍스트가 의도한 enrollment와 일치하는지 read-only로 재확인한다. 운영 문서 절차를 따라 PASS/FAIL·시각만 `report.md`에 기록하고 raw identity·전체 digest·credential은 기록하지 않는다. PASS가 아니거나 수행되지 않으면 AC-26은 미완료이며 rollout/completion을 중단한다.
6. **최종 cross-regression 검토:** CMD-1 다음 CMD-2를 다시 실행해 duplicate input과 `identity_unverifiable`이 login/binding/scope/cost/usage 순서를 우회하지 않는지, unavailable이 앞선 gate를 우회하지 않는지, launch/status dual consent가 drift/enrollment/duplicate/unverifiable을 덮지 않는지, ready가 unavailable/unknown을 matched/sufficient로 바꾸지 않는지, profile2 배포가 새 fail-open 기본값이나 private ingress를 만들지 않는지 확인한다. baseline의 기존 3 failures가 모두 사라지고 두 full suite가 exit 0이어야 한다. `git status --short`와 `git diff --name-only 72ad4f24e9df5919773cb877de01007f641ae163 --`는 read-only evidence로만 보고 File map 밖 변경과 #118-owned 변경이 0인지 대조한다. 하나라도 실패하면 실제 account로 보완하지 않고 전체 compatible set rollout을 중단한다.

## Verification commands

| ID | 순서 | 명령 | 기대 성공 결과 |
|---|---:|---|---|
| CMD-1 | 1 | `python3 tests/test_ai_session.py` | legacy selection/launch와 registry v2, launch/status dual-consent 2×2, unavailable, duplicate mapping, precedence, exact status/launch mapping, read-only/cross-regression tests가 모두 통과하고 exit 0이다. |
| CMD-2 | 2 | `python3 tests/test_orchestrator_profiles.py` | official adapters, unchanged canonical/enrollment v2, identity unverifiable/org-context 경계, registry/mixed deployment, 복사 기반 profile2 render/denylist, status/docs/ownership/cross-regression 전체가 통과하고 exit 0이다. |

CMD-1과 CMD-2는 각 태스크의 RED/GREEN에 같은 명령으로 사용하고 최종에는 표 순서대로 다시 실행한다. pytest, type check, build, CI는 repository에 구성돼 있지 않으므로 통과로 표시하지 않고 “not configured”로 기록한다. lint는 `.pre-commit-config.yaml`의 gitleaks hook 하나뿐이나 `pre-commit` 실행기가 이 환경에 없으므로 별도 판정 명령을 만들지 않는다. 검증 output에는 sentinel 원문이나 provider raw output을 보존하지 않는다.

## Rollout and rollback

Rollout은 자동 배포가 아니라 reviewed source set 준비다. 먼저 #118이 아직 merge되지 않았다면 이 branch의 구현/검증을 끝낸 뒤 #118 merge 결과를 rebase하고, 이미 merge됐다면 구현 전에 최신 base에 맞춰 rebase한다. 두 경우 모두 공유 충돌 후보 `tests/test_orchestrator_profiles.py`, `dot_config/ai-session/accounts.toml`, `.chezmoiignore`, `docs/session-account-profiles.md`를 수동으로 다시 대조하고 #118-owned path changed-file count 0을 CMD-2로 재검증한다.

registry v2, role manifest/dispatcher token, launcher/status, two adapters, shared identity/enrollment, tests, docs, profile2 public assets, `.chezmoiignore`는 하나의 compatible source set으로만 내보낸다. mixed v1/v2는 verifier 전에 `blocked_contract`가 되어야 한다. source review 후 실제 `chezmoi apply`, foreground login/enrollment, #118 worktree/TUI 실행은 이 자동 workflow 밖에서 사용자가 별도로 결정한다. 자동 판정 통과 뒤에도 T5의 Keychain 동시 실행 수동 게이트 PASS와 secret-free `report.md` 기록 전에는 완료로 전환하지 않는다.

관측은 six-field verifier JSON, exact status JSON, 기존 redacted binding/startup/launch-failure record, exit code와 CMD-1·CMD-2 결과로 제한한다. rollout 중 false-positive login, digest instability, duplicate input 누락, identity unverifiable/duplicate/unavailable의 matched 승격, unknown/sufficient 승격, single-consent admission, secret/path leakage, forbidden profile2 file/symlink, status side effect, #118-owned change가 하나라도 보이면 source set rollout을 중단한다.

Rollback은 별도 reviewed change로 registry/role token, launcher/adapters/identity helper, profile2 mirror/denylist, docs/tests를 마지막 compatible source set으로 함께 되돌린다. 일부 파일만 v1으로 섞지 않는다. rollback은 실행 중 process, account home, credential, identity file, session history, worktree/tmux를 건드리지 않으며 v2 enrollment file을 v1으로 downgrade·삭제·overwrite하지 않는다. 기존 v1 digest도 그대로 보존하고 이전 compatible code가 읽을 수 없는 경우 operator에게 새 process 전 점검을 요구한다.

## Acceptance-criteria traceability

| Criterion | Task | Verification command | Expected outcome |
|---|---|---|---|
| AC-1 | T2 | `CMD-2` `test_claude_official_status_contract` | camelCase success/false/error matrix가 exact six fields와 auth-kind cost 상태를 반환한다. |
| AC-2 | T2 | `CMD-2` `test_claude_official_status_contract` `test_identity_canonicalization` | required official fields가 엄격하고 excluded PII/path 변화는 canonical bytes/digest를 바꾸지 않는다. |
| AC-3 | T2 | `CMD-2` `test_codex_doctor_status_contract` | nested auth fixture만 login을 결정하며 flat/malformed/conflict는 unknown이고 private fields를 추론하지 않는다. |
| AC-4 | T3 | `CMD-1` `CMD-2` `test_verifier_redaction` `test_status_redaction` | 두 adapter와 status/launch record에 sentinel/extra field/provider exec가 0이다. |
| AC-5 | T1 | `CMD-1` `CMD-2` `test_strict_registry_v2_contracts_and_legacy_v1_compatibility` `test_registry_contract_mixed_deployment` | shipped v2가 parse되고 malformed/strict-v1은 verifier 전 차단되며 legacy v1 unit path는 유지된다. |
| AC-6 | T2 | `CMD-2` `test_identity_canonicalization` | normalization 동치 입력은 같은 v2 digest, 의미 변경은 다른 digest이며 invalid UUID/control은 거부된다. |
| AC-7 | T2 | `CMD-2` `test_identity_digest_version_boundaries` `test_identity_enrollment` | missing/v1/v2/unsafe 경계와 exact 68-byte 0600/0700 atomic enrollment가 판정된다. |
| AC-8 | T3 | `CMD-1` `CMD-2` `test_unavailable_identity_admission` `test_codex_doctor_status_contract` | Codex unavailable이 digest I/O 없이 그대로 보존되고 계약 모순은 provider 전 차단된다. |
| AC-9 | T3 | `CMD-1` `CMD-2` `test_admission_precedence_and_dual_consent` | launch/status 양쪽 2×2 중 `none+flag`만 admission되고 unknown 상태가 payload/env/record/status에 유지된다. |
| AC-10 | T3 | `CMD-1` `CMD-2` `test_admission_precedence_and_dual_consent` | login/drift/enrollment가 consent보다 먼저이며 verifier 1회, provider/fallback/reselection 0회다. |
| AC-11 | T4 | `CMD-2` `test_profile2_quality_bundle_mirror` | canonical과 profile2 source/rendered file set·bytes·regular-file type 및 reviewer resolution이 일치한다. |
| AC-12 | T4 | `CMD-2` `test_profile2_public_asset_denylist` | explicit forbidden target와 symlink가 0이고 두 settings deny 경계가 유지된다. |
| AC-13 | T4 | `CMD-2` `test_chezmoi_fixture_render` `test_profile2_chezmoi_diff_redaction` `test_high_risk_e2e` | 복사 기반 isolated diff만 사용하며 public asset 외 sentinel/source leak/actual HOME/실제 chezmoi 호출이 0이다. |
| AC-14 | T3 | `CMD-1` `CMD-2` `test_status_is_read_only` | status는 verifier를 한 번 쓰고 provider/helper/write를 0회 유지하며 program 인자를 거부한다. |
| AC-15 | T3 | `CMD-1` `CMD-2` `test_status_schema_exit_and_commands` `test_status_to_launch_failure_mapping` | 모든 status/exit가 exact JSON으로 구분되고 ready는 launch admission과 동치며 하위 unknown/unavailable이 보존된다. |
| AC-16 | T3 | `CMD-1` `CMD-2` `test_status_schema_exit_and_commands` `test_status_redaction` | top-level/nested exact fields, 상태별 command ID, blocked/ready empty commands와 sentinel 0개가 확인된다. |
| AC-17 | T5 | `CMD-2` `test_118_status_dependency_and_owned_paths` | #118 result→status→ready-only foreground 순서, owned path 0-change, 네 rebase 파일이 확인된다. |
| AC-18 | T5 | `CMD-2` `test_profile_onboarding_documentation_contract` | 두 운영 문서가 신설 조직 컨텍스트 의미를 포함한 v2/status/profile2/recovery/no-fallback 계약을 기록한다. |
| AC-19 | T1 | `CMD-1` `CMD-2` `test_changed_path_allowlist` `test_file_ownership` `test_portable_cli_contract` | current base/allowlist/evidence fixture가 task 범위와 일치하고 두 full suite가 synthetic-only exit 0이다. |
| AC-20 | T5 | `CMD-1` `CMD-2` `test_registry_exception_boundaries` `test_identity_state_nonpromotion` `test_admission_fail_closed_exceptions` `test_public_asset_private_boundary` | cross-regression이 identity/usage 상태 비승격, admission 순서와 private deployment 경계를 보존한다. |
| AC-21 | T2 | `CMD-2` `test_org_context_identity_boundaries` | same-email/different-org는 허용되고 same-org/different-email은 같은 digest이며 email 파생물 생성이 0이다. |
| AC-22 | T3 | `CMD-1` `CMD-2` `test_duplicate_mapping_admission` | registry 기반 다른 active valid v2가 같으면 status/launch 모두 duplicate mapping, exit 3, empty commands, provider/enrollment write 0회다. |
| AC-23 | T3 | `CMD-1` `CMD-2` `test_identity_state_nonpromotion` `test_admission_fail_closed_exceptions` | identity unverifiable/duplicate/unavailable이 matched로 승격되지 않고 consent가 identity 차단을 덮지 않는다. |
| AC-24 | T2 | `CMD-2` `test_claude_identity_unverifiable` | required field missing/wrong type/nesting 변화가 identity unverifiable, exit 3, empty commands, provider 0회로 닫힌다. |
| AC-25 | T5 | `CMD-2` `test_profile_onboarding_documentation_contract` | 운영 문서가 matched의 조직 컨텍스트 의미, 개인 식별 한계, email 방향 폐기와 same-email/different-org 허용을 명시한다. |
| AC-26 | T5 | [문서] `docs/session-account-profiles.md` `docs/orchestrator-permission-profiles.md` `report.md` | 사람이 전경에서 수행한 Keychain 동시 실행 수동 게이트 PASS를 비밀 없이 기록한 뒤에만 완료한다. |

<!-- strict-only:start -->

This block is required only for strict work. Any inapplicable subsection must be removed for non-strict work; within strict work, mark it as not applicable with a reason before review.

### Threat and trust boundaries

- trusted reviewed source는 registry/role v2 선언, two adapters, shared identity module, explicit CLI consent, canonical quality bundle이다. provider JSON/stdout/stderr, parent env, digest object metadata, account-home settings/runtime data, malformed registry, TUI arguments와 existing target data는 untrusted다.
- exact field/type/domain, provider-contract pairing, captured/redacted I/O, owner/mode/no-follow/versioned digest, registry-derived verifier-only other-profile path 목록, dual consent, regular-file byte mirror와 explicit denylist가 경계를 만든다.
- PII/path/token/digest leakage, schema downgrade, duplicate-list spoofing, digest confusion, fake matched/sufficient promotion, consent laundering, status side effect, symlink을 통한 private tree ingress, #118 input mismatch를 CMD-1·CMD-2의 negative sentinel/counter로 판정한다.

### Authorization and tenant isolation

여기서 tenant 경계는 provider+public account alias+resolved real workspace scope+binding generation이다. unavailable/consent 예외는 선택된 한 binding에만 적용되고 다른 provider/account/root로 fallback·ranking·rotation하지 않는다.

허용 case는 synthetic Codex binding의 exact `identity_contract="unavailable"`와 exact payload, 선택 account `usage_contract="none"`와 현재 호출 flag의 pair, 또는 own v2 match와 다른 active valid v2 collision 0개인 Claude profile뿐이며 CMD-1·CMD-2에서 판정한다. 거부 case는 provider mismatch, Claude+unavailable, Codex+matched, scope mismatch, stale binding, missing declaration, duplicate mapping, identity unverifiable, single consent, PAYG `unknown` cost이며 같은 명령에서 provider/fallback 0회와 exact 차단 status를 확인한다. OS-level tenant isolation은 해당 없음: 이 CLI는 account-selection policy이고 filesystem sandbox를 새로 제공하지 않으므로 검증은 추가 권한이 생기지 않는지만 판정한다.

### Migration, compatibility, and rollback

strict registry/role contract는 v2로 atomic하게 올리고 non-strict legacy `version=1` parser는 유지한다. official adapters는 PAYG `enforced`를 생성하지 않으므로 배포되지 않은 PAYG path는 닫혀 있다. v1 65-byte digest는 stale로 읽기만 하고 v2 68-byte로 자동 migration하지 않는다.

CMD-1·CMD-2와 mixed-deployment test가 source-set compatibility evidence다. rollback trigger와 전체 set 복구 절차는 Rollout and rollback 절을 따른다. 실제 enrollment data migration은 해당 없음: 자동 workflow가 identity file을 쓰지 않고 현 host에는 enrollment directory가 없으며, 예기치 않은 v1/v2 file은 보존하는 것이 요구사항이다.

### Failure recovery and observability

`login_required`는 operator foreground login 안내, `enrollment_required`는 official identity 확인 뒤 foreground enrollment 안내, `identity_drift`는 intended account 재확인 안내, `usage_unknown`은 policy/explicit consent 결정 안내만 반환한다. backend는 이 조치를 실행하지 않는다. `blocked_verifier|identity_unverifiable|duplicate_mapping|blocked_contract|blocked_binding|blocked_policy|blocked_usage`에는 command descriptor를 주지 않고 reviewed input repair 후 새 process에서 재시도한다.

관측 evidence는 redacted six-field payload, exact status JSON, 기존 binding/startup/launch-failure record, exit code, verifier/provider/write/access counter와 두 suite 결과다. 별도 network telemetry, retry metric, daemon alerting은 해당 없음: host-local CLI이며 자동 retry/service가 없고 추가 telemetry가 오히려 secret/path 경계를 넓힌다.

### High-risk end-to-end verification

필수 high-risk path는 synthetic `registry v2 → selection/binding → registry-derived other-profile paths → official adapter → identity/usage/cost decision → status 또는 launch public record`와 `canonical quality bundle → profile2 chezmoi source → copy-based isolated rendered regular files → reviewer relative resolution`이다. CMD-1과 CMD-2를 순서대로 실행해 둘 다 exit 0, secret/path/provider/write/access/actual-chezmoi negative sentinel 0, #118-owned change 0, duplicate/unverifiable/unavailable/unknown 상태 불변성을 증명해야 한다. 자동 검증 뒤 T5의 별도 사람 수동 게이트 PASS도 필요하다. 실패 시 실제 account, network 또는 `chezmoi apply`로 자동 검증을 보완하지 않고 rollout을 중단한다.

### No production mutation confirmation

자동 workflow에는 production mutation이 없다. 실제 login/logout/browser OAuth, identity enrollment, account switch, credential/token/account-home/session history 읽기·복제·rename·symlink, provider network/process, `chezmoi apply`, worktree/tmux 생성·이동, commit/push/merge/deploy를 실행하지 않는다. 모든 판정은 temp synthetic fixture와 비밀 없는 official schema contract로만 수행한다.

<!-- strict-only:end -->
