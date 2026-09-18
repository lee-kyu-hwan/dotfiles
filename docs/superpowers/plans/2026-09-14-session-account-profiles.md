# Session Account Profiles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** role profile과 인증 account profile을 독립적으로 결합하고, 결정적 선택·검증 뒤 provider별 credential home을 한 번만 바인딩하는 launcher를 구현한다.

**Architecture:** chezmoi가 배포하는 TOML에는 비밀이 아닌 account 선언과 scope/default 매핑만 둔다. 단일 Python launcher는 순수 선택 로직과 외부 verifier JSON 계약을 제공하고, 검증 성공 뒤 `CODEX_HOME` 또는 `CLAUDE_CONFIG_DIR`을 설정해 대상 process로 `exec`한다. 아직 없는 #94/#95/#103 레지스트리는 읽기 전용 task-binding/verifier adapter 경계로만 연결한다.

**Tech Stack:** Python 3.11+ 표준 라이브러리(`argparse`, `json`, `tomllib`, `subprocess`, `os.execvpe`), `unittest`, TOML

**Spec:** https://github.com/lee-kyu-hwan/dotfiles/issues/111

## Global Constraints

- OAuth token, API key, 이메일, account ID, Keychain reference를 저장소·로그·fixture·tmux metadata에 기록하지 않는다.
- consumer 계정 자동 fallback·usage ranking·세션 중 재선택을 구현하지 않는다.
- API/PAYG는 registry opt-in, 명시적 account 선택, 양수 비용 한도가 모두 있을 때만 허용한다.
- 실제 인증 저장소와 기본 HOME을 읽거나 변경하지 않고 테스트는 임시 HOME과 fake verifier/child만 사용한다.
- `create-worktree` 및 열린 #94/#95/#103의 상태 저장소를 수정하지 않는다.

---

### Task 1: 레지스트리와 결정적 선택기

**Files:**
- Create: `tests/test_ai_session.py`
- Create: `dot_local/bin/executable_ai-session`
- Create: `dot_config/ai-session/accounts.toml`

**Interfaces:**
- Consumes: registry TOML, 선택적인 task-binding JSON, provider/role/task/epic/repository/organization/directory context
- Produces: `select_account(registry, context) -> Binding`, `validate_scope(account, context)`, 비밀 없는 JSON selection 결과

- [x] 충돌, scope 위반, provider 불일치, 명시→task/epic→scope→default 우선순위, 가장 구체적인 scope, PAYG 거부 테스트를 먼저 작성한다.
- [x] `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_ai_session.py -v`가 production 파일 부재로 실패하는지 확인한다.
- [x] strict TOML schema와 선택 로직을 최소 구현한다.
- [x] 같은 명령으로 Task 1 테스트 통과를 확인한다.

### Task 2: fail-closed verifier와 고정 launcher binding

**Files:**
- Modify: `tests/test_ai_session.py`
- Modify: `dot_local/bin/executable_ai-session`

**Interfaces:**
- Consumes: verifier executable의 strict JSON `{provider, account_profile, login_status, identity_status, usage_status, cost_limit_status}`
- Produces: 성공 시 provider별 credential-home 환경과 role/account metadata를 가진 단일 child process

- [x] 미로그인, identity drift, `usage_unknown`, `blocked_usage`, malformed verifier, provider/profile 불일치와 성공 exec 테스트를 먼저 추가한다.
- [x] 새 테스트가 verifier/launch 기능 부재로 실패하는지 확인한다.
- [x] verifier stdout을 노출하지 않고 strict 상태를 판정하며 성공 시 `os.execvpe`하는 최소 구현을 추가한다.
- [x] fake child가 시작 뒤 `cd`해도 최초 credential home과 role/account binding이 유지되는지 확인한다.

### Task 3: 운영 문서와 좁은 후속 연동 계약

**Files:**
- Create: `docs/session-account-profiles.md`
- Modify: `README.md`
- Modify: `tests/test_ai_session.py`

**Interfaces:**
- Consumes: `ai-session select|launch`와 task-binding/verifier adapter schema
- Produces: login을 수행하지 않는 설정·선택 점검 절차와 #94/#95/#103 후속 항목

- [x] 샘플 registry가 strict validator를 통과하고 repository에 비밀 키가 없는지 검증하는 테스트를 먼저 추가한다.
- [x] 테스트 실패를 확인한 뒤 실제 비밀 없는 registry와 운영 문서를 작성한다.
- [x] AI 미실행 `create-worktree` 경로가 launcher/verifier를 호출하지 않는 현재 구조를 문서화한다.

### Task 4: 전체 검증, 신선한 Codex 리뷰, 커밋

**Files:**
- Modify: 리뷰에서 발견된 Critical/High 문제와 해당 회귀 테스트에 한함

**Interfaces:**
- Consumes: `66bee66373327c9797712efbcf95dc9bc94c3f94..HEAD` 또는 working-tree diff
- Produces: 검증 근거와 한국어 feature-branch commit

- [x] account-profile 테스트, 관련 Python/Node suite, Python compile, `git diff --check`, gitleaks/비밀 패턴 검사를 실행한다.
- [x] `codex exec`의 신선한 `gpt-5.6-sol` read-only 컨텍스트로 diff와 #111 요구사항을 독립 리뷰한다.
- [x] Critical/High 발견은 실패 테스트를 먼저 추가해 수정하고 검증을 반복한다.
- [x] 사용자 작업과 변경 범위를 확인한 뒤 한국어 커밋을 만든다. push·PR·merge·chezmoi apply는 실행하지 않는다.
