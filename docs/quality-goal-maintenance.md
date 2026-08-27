# quality-goal 유지보수 runbook

## 갱신 신호 추적

Claude Code changelog RSS를 확인한다: <https://code.claude.com/docs/en/changelog/rss.xml>

다음 변경을 확인한다.

- `SKILL.md`·agent frontmatter 지원 필드
- 도구 이름
- 슬래시 명령 계약

실제로 계약이 깨진 전례: Todo/Task 도구 제거, Bash 입력 리다이렉션 승인 요구, Agent SDK의 와일드카드 스킬명 거부.

## 의존 CLI 점검 (분기별, 또는 버전이 바뀐 것을 알아차렸을 때)

```bash
claude --version
codex --version
command -v codex
```

codex는 brew가 아니라 nvm/npm 설치본이므로 node 버전이 바뀌면 함께 바뀐다. 이 저장소에서는 PATH 우선순위 변경으로 `0.149.1`(homebrew)에서 `0.150.0`(nvm)으로 조용히 전환된 적이 있다.

스킬이 의존하는 `codex exec` 플래그가 살아 있는지 확인한다: `--output-schema`, `--ephemeral`, `--output-last-message`, `--json`, `--sandbox`.

라우팅 모델이 프리플라이트와 같은 조건으로 응답하는지 확인한다: `--sandbox read-only`, `model_reasoning_effort="low"`, 한 줄 프롬프트.

## 결정적 테스트

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_*.py'
```

스킬을 수정한 뒤에는 반드시 통과를 확인하고, 배포는 `chezmoi apply`로 한다.

## 평가

현재 `evals/evals.json`은 비표준 형식이고 수동 실행만 가능하다. `claude plugin eval`로의 이관은 이슈 #36으로 추적된다. 이관되면 이 절에 실제 명령을 적는다.

## 추적 중인 후속 작업

- #36 평가 이관
- #37 CODE-009
- #38 CODE-008
- #39 Codex 모델 리네이밍 대비

상세 근거는 `docs/development/2026-08-25-quality-goal/deviations.md`(D-1~D-16)와 같은 디렉터리의 `report.md`를 참고한다.

## 버전 정책

SemVer를 따른다.

- 게이트 규칙이나 상태 머신 계약 변경: MAJOR
- 지시·정책 추가: MINOR
- 문구 정정: PATCH
