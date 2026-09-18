# AI session account profiles: operator guide

`ai-session`은 role과 account를 따로 선택한다. Registry와 public output에는
provider 및 account의 안전한 별칭만 둔다. Credential, token, 이메일, 원시 account
또는 organization ID, identity digest, config home 경로는 public surface에 넣지 않는다.

## Strict registry v2

배포 registry의 계약 머리는 다음과 같다.

```toml
schema_version = 2
contract_id = "orchestrator-permission-profiles-v2"
```

각 active account는 `identity_enrollment_policy = "explicit_only"`와 함께 다음
계약을 명시한다.

```toml
# Claude
identity_contract = "claude_auth_status_v1"
usage_contract = "none"

# Codex
identity_contract = "unavailable"
usage_contract = "none"
```

Identity contract은 provider와 정확히 짝을 이뤄야 한다. Usage contract domain은
`none|provider_status`다. 누락, 미등록 값, provider 불일치, strict v1 registry는
verifier 실행 전에 `blocked_contract`로 종료한다. Non-strict `version = 1` parser는
기존 selection 호환 경로에서만 유지된다.

선택 우선순위는 `explicit option -> stored task/session binding -> longest directory
mapping -> Codex-only provider default`다. 선택한 profile은 resolved real directory의
allowed scope와 다시 대조한다. 충돌이나 범위 위반에는 추정, ranking, rotation,
account 변경을 하지 않는다.

## Official status projection

Verifier는 exact six-field JSON만 반환한다: `provider`, `account_profile`,
`login_status`, `identity_status`, `usage_status`, `cost_limit_status`.

- Claude adapter는 공식 `loggedIn`, `authMethod`, `orgId`, `subscriptionType`만
  사용한다. Canonical schema 2는 `claude_auth_status_v1`과 이 세 identity field만
  포함한다.
- Codex adapter는 `checks["auth.credentials"]`의 공식 credential signal로 login만
  판정한다. 공식 stable identity가 없으므로 `identity_status="unavailable"`을
  유지하며 auth file이나 account 별칭에서 identity를 추론하지 않는다.
- 두 공식 surface에는 reviewed usage/quota field가 없으므로 현재 active account는
  `usage_status="usage_unknown"`을 반환한다.
- consumer와 organization은 `cost_limit_status="not_applicable"`이다. 공식 adapter는
  PAYG enforcement를 합성하지 않으므로 PAYG는 `unknown`으로 fail closed한다.

Raw provider stdout/stderr와 불필요한 field는 relay하지 않는다. Exact field, enum,
provider 또는 public alias가 다르면 `blocked_verifier`다.

## Enrollment v2

Claude canonical bytes의 SHA-256 enrollment line은 exact
`v2:<64 lowercase hex>` 뒤 LF 형식이다. Parent는 0700, regular non-symlink file은
0600이며 atomic replace를 사용한다.

- file 없음은 `not_enrolled`, legacy `64 lowercase hex + LF`는
  `stale_enrollment`이며 public status는 `enrollment_required`다.
- valid v2 mismatch는 `identity_drift`, unsafe type/mode/owner/symlink/format은
  `unknown`을 거쳐 `blocked_verifier`다.
- launch와 status는 enrollment를 만들거나 갱신하지 않는다. Codex의 unavailable
  contract은 digest를 읽지 않고 enrollment 대상도 아니다.

여기서 `matched`는 enrollment 시점과 **같은 조직 컨텍스트**라는 뜻이다. 개인
동일성을 증명하지 않는다. Canonical identity는 `authMethod`, `orgId`,
`subscriptionType`만 사용하므로 같은 email과 다른 `orgId` 조합은 서로 다른
조직 컨텍스트로 허용된다. 반대로 email이 달라도 세 canonical field가 같으면 같은
digest다. Email 원문이나 email HMAC, salt, key를 만들거나 저장하는 방향은 폐기했다.
같은 조직의 서로 다른 사용자는 구분할 수 없다.

Launcher는 선택 profile과 registry의 다른 active Claude profile 경로를 모두 같은
identity root에서 만든다. 기본 root는
`~/.local/share/ai-account-profiles/identities`이고 synthetic fixture에서는
`AI_SESSION_IDENTITY_ROOT`다. 선택 profile이 자체 v2 enrollment와 일치한 뒤 다른
active valid v2가 같은 경우 `duplicate_mapping`으로 차단한다. 다른 profile의
missing/v1은 비교 후보가 아니며 unsafe file은 `blocked_verifier`로 닫는다.
필수 official field가 없거나 타입/구조가 바뀌면 `identity_unverifiable`이다.
`duplicate_mapping`과 `identity_unverifiable`은 exit 3, 빈 commands이며 provider를
시작하지 않는다.

## Admission order and dual consent

판정 순서는 selection/contract, login, identity drift, enrollment, identity contract,
cost, blocked usage, usage unknown, ready다. 뒤 단계의 예외가 앞 단계 실패를 덮지
않는다. `unavailable`을 `matched`로, `usage_unknown`을 `sufficient`로 승격하지 않는다.

`usage_unknown`은 기본적으로 exit 3이다. 선택 account 선언이 exact
`usage_contract="none"`이고 현재 `status` 또는 `launch` 호출에서
`--accept-usage-unknown`을 명시한 경우에만 provider 직전 admission이 열린다.
`launch`에서는 flag가 program용 `argparse.REMAINDER`의 `--` 앞에 있어야 한다.

| Account usage contract | 호출 동의 | 결과 |
| --- | --- | --- |
| `none` | 없음 | `usage_unknown` |
| `none` | 있음 | `ready` |
| `provider_status` | 없음 | `usage_unknown` |
| `provider_status` | 있음 | `usage_unknown` |

허용된 경우에도 payload, `AI_USAGE_ADMISSION_STATUS`, binding/startup record와 status
JSON은 `usage_unknown`을 그대로 보존한다. Consumer account의 fallback, ranking,
rotation과 실행 중 hot swap은 없다.

## Read-only profile status

`ai-session status`는 selection input, absolute regular non-symlink verifier와 optional
consent만 받는다. Selection, Claude home pre-scan, verifier를 각각 한 번 수행하고
provider, login browser, enrollment helper를 실행하거나 registry, digest, account
home, worktree, tmux를 쓰지 않는다.

`profile_status` JSON의 exact top-level fields는 `schema_version`, `event`, `provider`,
`account_profile`, `status`, `login_status`, `identity_status`, `usage_status`,
`cost_limit_status`, `commands`다. Ready는 exit 0, admission failure는 3,
`blocked_contract`은 2, `blocked_binding|blocked_policy`는 4다.

Command descriptor에는 `command_id`, `provider`, `account_profile`만 있다. 허용 ID는
`provider_login_foreground`, `identity_enroll_foreground`,
`inspect_identity_foreground`, `retry_with_usage_consent`다. Backend는 descriptor를
실행하지 않는다. Ready와 blocked state는 빈 commands를 반환한다.

## Rollout manual gate

자동 판정 명령이 통과해도 **Keychain manual gate**가 PASS하기 전에는 rollout을
완료하지 않는다. 사람이 별도 전경 pane에서 두 Claude profile을 동시에 실행하고,
각 profile의 조직 컨텍스트가 의도한 enrollment와 일치하는지 read-only로 확인한다.
기록에는 PASS/FAIL과 시각만 남기며 raw identity, 전체 digest, credential, account
home은 남기지 않는다. Backend는 이 동시 실행이나 account 전환을 수행하지 않는다.

## Local verification scope

설치 계약 checker의 Claude 기대 version `2.1.272`와 현재 실측 설치본 `2.1.273`의
차이는 **accepted risk**다. Checker의 기대 version은 유지하며 이 checker는 이번
변경의 판정 명령이 아니다. 또한 **pre-commit runner availability is not a judgment
command**다. 저장소에 별도 pytest, type check, build, CI 판정 명령은 없다.
즉 pre-commit 실행기 존재 여부를 판정 명령으로 삼지 않는다.

## Claude account home 권한과 mode

`claude-profile1`과 `claude-profile2`는 모두 `config_home_mode = "explicit"`이며 각각
`~/.local/share/ai-account-profiles/claude/profile1`, `.../profile2`를
`CLAUDE_CONFIG_DIR`로 받는다. Launcher 밖에서 직접 실행한 `claude`는 계속 `~/.claude`를
쓴다. `provider_default` mode의 코드 지원은 남아 있지만, 그 mode는 사용자 `~/.claude`의
`settings.json`과 `settings.local.json`을 pre-scan 대상으로 만들므로 benign allowlist 밖의
키를 가진 풍부한 설정 home에서는 launch와 status가 `blocked_policy`(exit 4)로 끝난다.

Explicit home은 launch와 status 전에 symlink가 아닌 기존 디렉터리여야 하며, 없으면
`blocked_verifier`다. 새 home에는 로그인 상태가 없으므로 사람이 전경 pane에서 그 home으로
로그인하고 enrollment해야 admission을 통과한다(아래 Operator recovery).

Account home 상위 디렉터리는 owner-only(0700)다. Chezmoi source는
`dot_local/share/private_ai-account-profiles/private_claude/private_profile1`처럼 세
디렉터리에 `private_` 속성을 붙여 `~/.local/share/ai-account-profiles`, `.../claude`,
`.../claude/profile1`을 0700으로 렌더링한다. `profile2` home은 source에 배포 자산이 없어
chezmoi가 만들지 않고 mode도 관리하지 않는다(#138). 기존 home은 operator가 `chmod 700`으로
맞춘다.

## Profile2 home 배포 자산

Profile2 home에 source가 배포하는 자산은 없다. 예전에는 `agents/quality-reviewer.md`와
`skills/quality-goal/**`의 canonical byte mirror를 배포했지만, 역할 런처 동결 뒤 그 사본을
읽는 실행 경로가 없어져 #138에서 source와 강제 테스트를 함께 제거했다. quality-goal 정본은
`dot_claude/skills/quality-goal` 한 벌이다. 이미 배포된 두 경로는 한시적 `.chezmoiremove`가
리터럴 경로로 걷어내며, 모든 머신에 적용이 끝나면 그 파일을 제거한다. 제거로 영구 스위트에서
사라진 계약은 `docs/development/2026-09-18-138-remove-profile2-quality-mirror/removed-contracts.md`에
있다.

`settings.json`, `.claude.json`, credential/token, sessions, projects, history, backups,
file-history, debug, todos, plans와 plugins는 private이며 배포하거나 symlink하지 않는다.
두 profile 모두 이 항목을 `.chezmoiignore`에서 대칭으로 제외한다.

## Operator recovery

Recovery는 **human-only foreground recovery**다. Login, enrollment 또는 identity 확인은
사람이 전경 pane에서 별도로 결정하고, backend는 안내 descriptor만 반환한다. Public
status에서 raw provider 이유나 복구 material을 제공하지 않는다.

모든 실패는 선택된 binding에서 새 process로 다시 확인한다. 다른 provider, account,
scope 또는 model로 바꾸는 automatic retry가 없으며 **no fallback** 규칙을 유지한다.
PAYG official enforcement와 consumer usage inference는 현재 non-goal이다.
