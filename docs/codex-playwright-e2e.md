# Codex Playwright E2E 프로필

`dot_codex/private_e2e.config.toml`은 Playwright E2E 작업에 필요한 Codex 기본 권한을
머신 간에 동일하게 적용한다. chezmoi는 이 파일을 `~/.codex/e2e.config.toml`로 배포한다.

## 사용법

저장소를 작업 디렉터리로 지정해 `e2e` 프로필을 선택한다.

```bash
codex --profile e2e -C /path/to/repository
```

프로필은 다음 범위만 허용한다.

- 작업 저장소 내부 쓰기
- Playwright 브라우저와 앱/API 서버에 필요한 외부 네트워크 연결
- 샌드박스 밖 실행이 필요할 때 사용자에게 승인 요청

macOS에서 Chromium 프로세스를 실행할 때 필요한 호스트 권한이나 Codex의
`require_escalated` 승인은 프로필과 별개다. 새 세션에서도 승인 요청이 나타날 수 있다.
Playwright MCP 도구 승인 정책 역시 `~/.codex/config.toml`에서 별도로 관리한다.

## 보안

다음 파일은 dotfiles에 추가하지 않는다.

- `~/.codex/auth.json`
- 프로젝트의 Playwright `storageState` 파일(예: `e2e/.auth/user.json`)
- API 토큰이나 테스트 계정 비밀번호

Playwright `storageState`는 각 프로젝트의 `.gitignore`에 추가하고 로컬에서만 생성한다.

## 적용과 확인

```bash
chezmoi diff
chezmoi apply ~/.codex/e2e.config.toml
codex --profile e2e -C /path/to/repository
```

설정 키는 OpenAI 공식 Codex 설정 문서를 따른다.

- [Codex configuration reference](https://developers.openai.com/codex/config-reference/)
