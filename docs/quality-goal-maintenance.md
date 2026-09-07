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

readiness 점검에서는 `codex exec` 호출에 `--skip-git-repo-check`, `--dangerously-bypass-approvals-and-sandbox`, `--dangerously-bypass-hook-trust`, `--approve-for-me`, `--ignore-rules`, `--ignore-user-config`, `--add-dir`, `--yolo`를 쓰지 않는 금지 계약을 확인한다. `schemas/readiness-result.schema.json` 결과 스키마와 `references/model-routing.md`의 `Spec author (standard)`·`Spec author (strict)`·`readiness reviewer (fresh)` 라우팅 모델을 확인하고, 그 라우팅 문서와 `references/readiness-policy.md`의 절차 문맥이 동기화되어 있는지도 확인한다.

## 판정 명령 표

이 표는 quality-goal 판정 명령 표의 정본이다. `QG_PY`는 3.12 이상 인터프리터를 가리키고 `QG_BASE`는 `6d60011cbdaead7946b191d3f12029eef5c141c8`로 설정한다.

| ID | 명령 | 통과 조건 |
|---|---|---|
| CMD-1 | `"$QG_PY" dot_claude/skills/quality-goal/tests/assert_python_version.py && PYTHONDONTWRITEBYTECODE=1 "$QG_PY" -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_*.py'` | 종료 코드 0, `OK` |
| CMD-2 | `"$QG_PY" dot_claude/skills/quality-goal/tests/assert_python_version.py && PYTHONDONTWRITEBYTECODE=1 "$QG_PY" -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_*.py' -k <테스트 이름>` | 종료 코드 0 |
| CMD-3 | `wc -l < dot_claude/skills/quality-goal/SKILL.md` | 500 미만 |
| CMD-4 | `"$QG_PY" dot_claude/skills/quality-goal/tests/assert_preserved_sections.py "$QG_BASE"` | 종료 코드 0, `보존 대상 절 불변` |
| CMD-5 | `"$QG_PY" -c "import json; d=json.load(open('dot_claude/skills/quality-goal/schemas/readiness-result.schema.json')); assert d['type']=='object'; assert d['additionalProperties'] is False; print('OK')"` | 종료 코드 0, `OK` |
| CMD-6 | `"$QG_PY" dot_claude/skills/quality-goal/tests/assert_tests_preserved.py "$QG_BASE"` | 종료 코드 0, `기존 테스트 보존` |
| CMD-7 | `OLD_PY=/usr/bin/python3; "$OLD_PY" -c 'import sys; raise SystemExit(0 if sys.version_info<(3,12) else 1)' && "$QG_PY" dot_claude/skills/quality-goal/tests/assert_python_version.py && ! "$OLD_PY" dot_claude/skills/quality-goal/tests/assert_python_version.py` | 종료 코드 0 |

테스트 스위트의 최소 인터프리터 버전은 3.12다. `enterContext`는 Python 3.11에 도입됐고, `NO TESTS RAN`의 종료 코드 5는 Python 3.12에 도입됐으므로 CMD-1·CMD-2는 공용 `tests/assert_python_version.py`로 이 전제를 먼저 확인한다.

스킬을 수정한 뒤에는 반드시 CMD-1 통과를 확인하고, 배포는 `chezmoi apply`로 한다.

## 평가

현재 `evals/evals.json`은 비표준 형식이고 수동 실행만 가능하다. `claude plugin eval`로의 이관은 이슈 #36으로 추적된다. 이관되면 이 절에 실제 명령을 적는다.

## 추적 중인 후속 작업

- #36 평가 이관
- #39 Codex 모델 리네이밍 대비
- #43은 이 작업이 의도적으로 손대지 않은 인접 결함이다.

권위 목록은 GitHub의 열린 이슈다. 다음 명령으로 조회한다.

```bash
gh issue list --state open --search 'quality-goal in:title'
```

상세 근거는 `docs/development/2026-08-25-quality-goal/deviations.md`(D-1~D-16)와 같은 디렉터리의 `report.md`를 참고한다.

## 버전 정책

SemVer를 따른다.

- 게이트 규칙이나 상태 머신 계약 변경: MAJOR
- 지시·정책 추가: MINOR
- 문구 정정: PATCH

## 개정 후 자기 회귀 점검

개정본을 리뷰에 기록하기 전 다음과 같이 점검한다.

```bash
python3 dot_claude/skills/quality-goal/scripts/revision_check.py --artifact spec --current /absolute/spec.md --state /absolute/state.json --out /absolute/revision-check-spec.json
```

Plan은 `--spec /absolute/spec.md`도 준다. 라운드 2 이상은 `snapshots/`의
직전 산출물과 digest를 대조하며, 성공 JSON을 `record-review --revision-check`에
넘긴다. `revision_checks` 키가 없는 기존 상태는 호환성을 위해 면제다.
