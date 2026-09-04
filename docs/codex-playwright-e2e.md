# Codex Playwright E2E 프로필

`dot_codex/private_e2e.config.toml`은 Playwright E2E 작업에 쓰는 Codex 권한을 한 파일로
선언해 둔 프로필이다. chezmoi는 이 파일을 `~/.codex/e2e.config.toml`로 배포하고,
`private_` 접두사 때문에 권한은 0600이 된다. 파일 자체에 비밀은 없고, 접두사는
`private_full_auto.config.toml`과 관례를 맞춘 것이다.

머신 간에 같아지는 것은 이 파일뿐이다. 실제 세션 권한은 이 프로필과 base
`~/.codex/config.toml`, `~/.codex/rules/default.rules`에 쌓인 승인 규칙,
`[projects.*]`의 `trust_level`이 합쳐져 결정된다. 뒤 셋은 Codex가 런타임에 계속 다시 쓰기
때문에 chezmoi가 관리하지 않는다(`.chezmoiignore`, `docs/codex-config-reference.toml` 참고).
그래서 새 머신에서 권한이 그대로 재현되지는 않는다 — 승인 규칙이 비어 있어 프롬프트가 더
자주 뜬다.

## 사용법

```bash
codex --profile e2e -C /path/to/repository
```

`--profile`은 `$CODEX_HOME/<name>.config.toml`을 base 설정 위에 올린다(overlay). 이 프로필은
base를 대체하지 않고 겹쳐 쓰기만 한다. 모델은 고정하지 않으므로 base 값을 따른다
(`private_full_auto.config.toml`은 모델을 고정하는 점이 다르다).

### 이 프로필이 실제로 바꾸는 것

지금은 아무것도 바꾸지 않는다. 세 값이 모두 이미 유효한 상태다.

| 키 | 값 | 현재 상태 |
|---|---|---|
| `approval_policy` | `on-request` | 버전 관리가 감지될 때의 Codex 기본 모드(Auto)와 같다 |
| `sandbox_mode` | `workspace-write` | 같은 이유로 기본값과 같다 |
| `sandbox_workspace_write.network_access` | `true` | base `config.toml`이 이미 전역으로 켜 두었다 |

그래서 이 파일은 "E2E 세션에 필요한 권한이 무엇인지"를 남겨 두는 선언이다. base에서 전역
네트워크 허용을 회수하면 그때 이 프로필만 네트워크를 갖게 되고, 그 시점에 실효가 생긴다.

### 실제 허용 범위

`workspace-write` + `network_access = true`가 여는 범위는 작업 저장소보다 넓다.

- **파일 읽기는 위치 제한이 없다.** 작업 디렉터리 밖도 읽는다.
- **쓰기는 작업 디렉터리와 `/tmp`, `$TMPDIR`.** `/tmp`를 막으려면 `exclude_slash_tmp = true`,
  `$TMPDIR`은 `exclude_tmpdir_env_var = true`를 프로필에 추가한다.
- 쓰기가 허용된 경로 안이라도 `.git`·`.codex`·`.agents`는 읽기 전용이다.
- **네트워크는 목적지 제한이 없는 outbound다.** Playwright 대상 호스트만 열리는 것이 아니다.
- **`on-request`는 "항상 묻는다"가 아니다.** 모델이 필요하다고 판단할 때 묻고,
  `~/.codex/rules/default.rules`에 저장된 allow 규칙에 걸리는 명령은 재승인 없이 실행된다.
  E2E 작업 중 한 번 "항상 허용"을 누른 명령은 다음 세션에서 그냥 실행된다.

macOS에서 Chromium을 띄울 때 필요한 호스트 권한과, 샌드박스를 벗어나는 명령의 권한 상승
승인(`require_escalated` 계열)은 이 프로필과 별개다. 새 세션에서도 승인 창이 뜰 수 있다.
Playwright MCP 도구 승인 정책도 이 프로필이 아니라 `~/.codex/config.toml`에 있다 — 그 파일은
chezmoi 관리 대상이 아니고, 사람이 정한 값은 `docs/codex-config-reference.toml`에 기록해 둔다.

## 보안

`network_access = true`는 샌드박스에서 데이터가 나가는 것을 막던 차단선을 제거한다. 읽기에
위치 제한이 없으므로, 읽기 전역과 무제한 outbound가 겹치면 승인 없이 임의 파일을 외부로
보낼 수 있는 경로가 생긴다. OpenAI 문서도 이 조합을 elevated risk로 경고한다. 신뢰할 수 없는
페이지나 테스트 픽스처를 브라우징하면 프롬프트 인젝션 표면도 함께 커진다. **이 프로필은
그런 유출을 막지 않는다.** 그래서:

- E2E에는 운영 계정을 쓰지 않는다. 권한을 최소화한 단기 테스트 계정만 쓴다.
- 토큰은 만료를 짧게 두고 주기적으로 회전한다.

### 저장소에 넣지 않을 것

- `~/.codex/auth.json`
- Playwright `storageState` 파일(예: `e2e/.auth/user.json`)
- `test-results/`, `playwright-report/` — trace·video·screenshot·HTML 리포트에는 요청
  헤더(`Authorization`)와 쿠키, 응답 본문이 그대로 담긴다. `storageState`만 막아도 trace로
  세션이 새어나간다.
- `*.har`
- `.env*` — API 토큰, 테스트 계정 비밀번호

각 프로젝트의 `.gitignore`에 위 항목을 넣고 인증 파일은 로컬에서만 생성한다. 단
`.gitignore`는 **커밋만** 막는다. 무시된 파일도 Codex는 읽을 수 있고, 위의 네트워크 허용과
겹치면 유출 경로가 된다. 작업이 끝나면 산출물을 지운다.

이미 커밋한 뒤 알아챘다면 `.gitignore` 추가로는 해결되지 않는다. 히스토리에서 파일을 제거하고
노출된 자격 증명을 회전한다.

Codex 세션 기록(`~/.codex/history.jsonl`, `~/.codex/sessions/`)에도 프롬프트와 도구 출력이
남는다. 터미널에 띄운 토큰은 그 기록에 들어간다고 봐야 한다.

## 적용과 확인

```bash
chezmoi diff
chezmoi apply ~/.codex/e2e.config.toml
codex --profile e2e -C /path/to/repository
```

설정 키는 OpenAI 공식 Codex 설정 문서를 따른다.

- [Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
- [Agent approvals and security](https://learn.chatgpt.com/docs/agent-approvals-security)
