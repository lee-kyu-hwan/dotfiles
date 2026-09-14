# AI 세션 account profile

`ai-session`은 모델·권한을 정하는 `role_profile`과 인증·결제 범위를 정하는
`account_profile`을 별도 값으로 선택한다. chezmoi는
`~/.config/ai-session/accounts.toml`에 비밀이 아닌 선언만 배포한다. OAuth token,
API key, 이메일, account ID, Keychain reference와 provider 인증 파일은 이 파일이나
Git, 로그, tmux metadata에 넣지 않는다.

## 선택 계약

선택 순서는 다음과 같다.

1. 명시적 `--account-profile`
2. `--binding-file`의 일치하는 task/epic binding
3. repository, organization, directory scope mapping
4. provider 기본값

repository는 organization보다 구체적이며 directory mapping끼리는 가장 긴 실제 상위
경로가 우선한다. 같은 단계·구체성에서 서로 다른 profile이 나오면 추측하지 않고
종료한다. 선택 뒤에는 profile의 `allowed_scopes`를 다시 대조하므로 높은 우선순위의
명시값도 scope를 우회할 수 없다.

인증을 조회하지 않는 선택 점검 예시는 다음과 같다.

```bash
ai-session select \
  --registry ~/.config/ai-session/accounts.toml \
  --provider codex \
  --role-profile general \
  --repository lee-kyu-hwan/dotfiles
```

출력 JSON에는 provider, role/account profile 별칭, 허용 scope, 선택 출처와 이유만
포함한다. `config_home`은 task registry용 출력에 포함하지 않는다.

## task registry adapter

#94/#95의 공통 레지스트리는 아직 구현되지 않았다. 현재 `--binding-file`은 그 후속
연동을 위한 읽기 전용 adapter이며 자체 상태 저장소나 task ID를 만들지 않는다.

```json
{
  "version": 1,
  "bindings": [
    {
      "kind": "task",
      "id": "111",
      "provider": "codex",
      "account_profile": "codex-dotfiles"
    }
  ]
}
```

허용 필드 외의 값은 거부한다. #94/#95가 구현될 때 이 adapter를 실제 registry 조회로
교체하고, 기존 worktree의 account binding·generation과 새 선택이 다르면 새 process를
시작하지 않는 재사용 충돌 검사를 추가해야 한다.

## 시작 전 verifier 계약

`launch`는 host-local verifier의 절대경로를 필수로 받는다. verifier는 선택된
`AI_PROVIDER`, `AI_ACCOUNT_PROFILE`, provider별 config home과 비밀이 아닌 binding
환경을 사용해 실제 로그인, identity, 사용량을 확인해야 한다. stdout에는 아래 필드만
있는 JSON object를 반환한다.

```json
{
  "provider": "codex",
  "account_profile": "codex-dotfiles",
  "login_status": "logged_in",
  "identity_status": "matched",
  "usage_status": "sufficient",
  "cost_limit_status": "not_applicable"
}
```

- `login_status`: `logged_in`만 허용한다. 미로그인은 중단한다.
- `identity_status`: `matched`만 허용한다. `identity_drift`나 확인 불가는 중단한다.
- `usage_status`: `sufficient`만 허용한다. `usage_unknown`과 `blocked_usage`는 중단한다.
- `cost_limit_status`: consumer/organization은 `not_applicable`, PAYG는 `enforced`여야 한다.

verifier의 원시 stdout/stderr는 로그로 전달하지 않는다. provider/profile 불일치,
추가 필드, malformed JSON, 비정상 종료, 10초 timeout도 모두 중단한다. provider별 공식
상태 조회를 실제로 수행하는 verifier는 #103 launcher 연동과 함께 구현·검증할 후속
항목이다. 그러므로 현재 repository에는 가짜 성공 상태를 만드는 기본 verifier가 없고,
`select`만으로 실제 AI를 시작할 수 없다.

검증된 verifier가 준비된 이후의 호출 형태는 다음과 같다.

```bash
ai-session launch \
  --registry ~/.config/ai-session/accounts.toml \
  --provider codex \
  --role-profile general \
  --repository lee-kyu-hwan/dotfiles \
  --verifier /absolute/path/to/verified-account-probe \
  -- codex
```

검증 성공 시 launcher는 부모의 `CODEX_HOME`과 `CLAUDE_CONFIG_DIR`을 모두 제거한 뒤
Codex에는 선택 profile의 `CODEX_HOME`만, Claude에는 `CLAUDE_CONFIG_DIR`만 설정한다.
그 환경으로 대상 command를 `exec`하므로 account binding은 launcher process 시작 시
한 번만 정해진다. child가 `cd`하거나 이후 사용량이 바뀌어도 선택기를 다시 호출하거나
다른 consumer profile로 전환하지 않는다.

## 계정 준비와 복구

chezmoi 적용은 profile 선언만 복원한다. 각 `config_home`은 host에서 직접 만들고 해당
provider의 공식 login 흐름을 그 환경에 대해 별도로 완료해야 한다. token, refresh token,
인증 디렉터리를 다른 profile이나 Mac에서 복사·snapshot·symlink하지 않는다. logout,
relogin, token refresh도 해당 profile의 환경에서만 수행하고 다른 실행 중 profile을
건드리지 않는다.

미로그인이나 identity drift가 보고되면 대상 process를 시작하지 말고 그 profile의 로그인
상태를 별도로 복구한 뒤 verifier부터 다시 실행한다. `usage_unknown`은 확인 가능한 공식
상태가 생길 때까지, `blocked_usage`는 reset/credit을 기다리거나 같은 계정의 명시적인
모델·effort 변경을 결정할 때까지 유지한다.

## PAYG와 비범위

PAYG profile은 기본값이나 scope/task mapping으로 선택할 수 없다. registry에서
`auth_kind = "api_payg"`, `enabled = true`, 양수 `max_cost_usd`를 선언하고, 호출에서 그
profile과 `--cost-limit-usd`를 명시하며 verifier가 `cost_limit_status = "enforced"`를
증명해야만 시작한다. 배포 registry에는 PAYG profile을 두지 않는다.

현재 구현하지 않은 항목은 다음과 같다.

- consumer 계정 사이 사용량 ranking, fallback, rotation
- 세션 중 account 전환이나 credential directory 변경
- #94의 영구 task/session binding·generation 저장과 resume 검증
- #95의 create-worktree 생성/재사용 등록
- #103의 role별 실제 Claude/Codex launcher와 live verifier

현재 `create-worktree` 경로는 수정하지 않았다. 따라서 AI 자동 실행을 요청하지 않은 기존
worktree 생성은 account login이나 usage 조회 없이 계속 동작한다.
