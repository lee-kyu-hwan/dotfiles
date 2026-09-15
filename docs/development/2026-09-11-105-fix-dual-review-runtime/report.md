# Quality Goal Report

- Task ID: 20260911T025854Z-105-dual-review-실행-결함-수정-모델-선택-producer-ced012ff
- Mode: strict
- Status: BLOCKED
- Created: 2026-09-11
- Updated: 2026-09-11
- Source goal: #105 dual-review 실행 결함 수정: 모델 선택·producer stdin 즉시 전달·reviewer/critique/synthesis strict schema 계약·chezmoi 설치본 패키징

## Classification

strict. 자동 라우팅의 strict 트리거가 셋 걸렸고 근거는 모두 저장소·실행으로 확인했다.

- 외부 API 호환성: `schemas/{reviewer,critique,synthesis}.schema.json` 은 Codex `--output-schema` 와 Claude `--json-schema` 로 전달되는 structured-output 계약이다. 세 파일 모두 루트·중첩 object 에 `additionalProperties` 가 없고 `critique` 의 `new_findings.items` 는 속성 없는 무제약 object 다.
- 동시성 정확성: `review_state.py:397-406` 이 6개 프로세스를 모두 start 한 뒤 순차 read 하는데 `SubprocessAdapter.start`(`:669-683`)가 프롬프트를 `read()` 까지 미룬다. `MAX_PROMPT_DIFF_BYTES = 262144` 가 64KB 파이프 버퍼를 넘어 단순 write 는 교착 위험이 있다.
- 광범위한 실패 모드: 이슈에 기록된 세 브랜치 모두 `termination_reason: reviewer_failure` 였고, 빈 Findings 를 통과로 오인하지 않을 것이 완료 조건에 명시돼 있다.

standard 조건(다수 파일·계층 변경)도 함께 충족한다. 이슈 라벨은 비어 있어 분류 근거로 쓰지 않았다. 사용자 지정 Codex 모델 `gpt-5.6-sol` 은 strict 라우트와 일치한다.

## Review history

| 산출물 | 라운드 | 결과 | score | blockers | 기록 |
|---|---|---|---|---|---|
| spec (readiness, advisory) | r1 attempt 1 | REVISE | 88 | READY-001, READY-002 | `readiness-spec-r1.result.json`. 체크리스트 C1~C8 전부 pass. 세 건 모두 author 가 해소 |
| spec | 1 | REVISE | 81 | SPEC-001 | `review-spec-r1.json`. 유효 기록. findings 8건 |
| spec | 2 시도 1 | 무효 | 88 | 없음 | `review-spec-r2-discarded1.json`. 검증 오류 `findings[1] missing required field: rubric_item`. `record-review-error` attempts=1 |
| spec | 2 시도 2 | 무효 | 89 | 없음 | `review-spec-r2-discarded2.json`. 검증 오류 `unknown top-level field: 'prior_findings'`, `'resolved_finding_ids'`. `record-review-error` attempts=2 → BLOCKED |

라운드 1 은 SPEC-001(High, blocker)부터 SPEC-008(Low)까지 8건을 냈다. author 개정 뒤 라운드 2 의 두 무효 응답은 모두 8건을 resolved 로 판정하고 SPEC-009(Medium)·SPEC-010(Low)·SPEC-011(Low)을 새로 냈으나, 스키마 검증을 통과하지 못해 게이트 판정 근거가 되지 못한다.

## Blocking-finding resolutions

| ID | severity | 요지 | 적용한 해소 | 검증 증거 |
|---|---|---|---|---|
| SPEC-001 | High | CMD-6 이 `--setting-sources` 근거 없이 의존하고, 스킬이 Python 진입점을 실행할 도구 권한이 없어 실행 불가 | CMD-6 을 실측 성공한 형태로 교체: 프롬프트 stdin, `--setting-sources project`, `--permission-mode default`, `--permission-prompts none`, `--allowedTools "Read,Glob,Grep,Bash(python3:*)"`, bypass flag 0개. 판정을 run 디렉터리 1개 + `provenance.json` 의 `termination_reason == no_changes` + `report.md` 존재로 구조화. Security 절에 이 allowlist 가 검증 하니스 전용이며 `build_claude_command()` 의 `plan` + `Read,Glob,Grep` 계약을 넓히지 않음을 명시 | `evidence/p3-slash-no-changes/`(exit=0, stdout 2225B, run 디렉터리 1개, `provenance.json` → `no_changes`, `report.md`), `evidence/p4-allowedtools-variadic/stderr.txt` |

이 해소는 유효한 라운드 2 리뷰로 확정되지 못했다. 두 무효 응답 모두 SPEC-001 을 resolved 로 판정했으나 기록되지 않았다.

## Plan approval

- Approval timestamp: 없음 — Plan 단계에 도달하지 못했다
- Plan digest: 없음

## Changed files

리뷰 대상 코드 변경은 없다. 구현 단계에 진입하지 않았다. `dot_claude/skills/dual-review/` 는 baseline `067923b` 그대로다.

산출된 문서·상태 파일:

| 경로 | 내용 |
|---|---|
| `docs/development/2026-09-11-105-fix-dual-review-runtime/spec.md` | strict Spec. 요구사항 20, AC 20, 판정 명령 CMD-1~CMD-8 |
| `docs/development/2026-09-11-105-fix-dual-review-runtime/spec-revision-notes.md` | 라운드 2 개정 노트 |
| `docs/development/2026-09-11-105-fix-dual-review-runtime/report.md` | 이 보고서 |
| `.claude/quality-state/<task-id>/` | 상태, 프롬프트, 리뷰, revision check, 증거. 저장소 ignore 대상 |

## Verification evidence

실제로 실행한 명령만 적는다. 이 저장소에는 type check, lint, build 가 구성돼 있지 않다. 근거: `dot_claude/skills/dual-review/references/verification.md` 가 "Type checking, linting, and builds are **not configured** for this repository." 로 명시한다.

| 명령 | exit | 증거 |
|---|---|---|
| `python3 -m unittest discover -s tests` (소스 트리) | 0 | `Ran 93 tests ... OK`. `evidence/p6-baseline-suites/source-suite.*` |
| `python3 -m unittest discover -s tests` (archive 배포본) | 1 | `AssertionError: False is not true : schemas/.gitkeep`, `Ran 93 tests ... FAILED (failures=1)`. `evidence/p6-baseline-suites/archive-suite.*` |
| `chezmoi --source <worktree> archive --format tar ~/.claude/skills/dual-review` | 0 | 멤버 목록에 `.gitkeep` 0건. `evidence/p6-baseline-suites/archive-members.txt` |
| `codex exec ... --output-schema <현행 reviewer.schema.json>` | 비영 | `invalid_json_schema ... 'additionalProperties' is required to be supplied and to be false. (400)`. `evidence/current.json` |
| `codex exec ... --output-schema <strict-closed> --json - < prompt` | 0 | 스키마 준수 payload 반환, 거부 없음. `evidence/strict.json`, `evidence/strict.result.json` |
| `claude -p ... /probeskill` (`model: claude`) | 1 | `[claude-code:unrecognized_model]`. `evidence/p0-frontmatter-model/model-claude.*` |
| `claude -p ... /probeskill` (`model: opus`) | 0 | `PROBE_OK`. `evidence/p0-frontmatter-model/model-opus.*` |
| `printf ... \| claude -p --setting-sources project --permission-mode default --permission-prompts none --allowedTools "Read,Glob,Grep,Bash(python3:*)"` | 0 | run 디렉터리 1개, `termination_reason: no_changes`, 모델 오류 0건. `evidence/p3-slash-no-changes/` |
| `claude -p ... --allowedTools "..." "/probe positional prompt"` | 비영 | `Error: Input must be provided either through stdin or as a prompt argument when using --print`. `evidence/p4-allowedtools-variadic/stderr.txt` |
| `codex exec --model gpt-5.6-sol` preflight | 0 | 비어 있지 않은 응답 |
| `revision_check.py --artifact spec` | 0 | `passed: true`, 빈 칸 0, 노트 section_found true |
| type check | not configured | `references/verification.md` 확인 |
| lint | not configured | `references/verification.md` 확인 |
| build | not configured | `references/verification.md` 확인 |

Python 인터프리터는 3.14.7 이다(`evidence/p6-baseline-suites/python-version.txt`).

## Execution watchdog

- Execution ID: 해당 없음
- PID / PGID: 해당 없음
- Start / end / elapsed: 해당 없음
- Child exit code: 해당 없음
- Result exists / schema validation: 해당 없음
- Start confirmed / watchdog reason: 해당 없음
- Signals / preservation bundle: 해당 없음
- Abort: 해당 없음
- Reap: 해당 없음
- Residual PIDs: 해당 없음

해당 없음 — 이 실행의 모든 Codex 호출은 quality-goal 5.1.x 계약 구간에 이뤄졌고 그때 watchdog 래퍼는 존재하지 않았다. 실행 도중 설치본이 5.2.0 으로 갱신돼 `scripts/execution_watchdog.py` 와 래퍼 템플릿이 추가됐으나, 갱신 이후 새로 실행한 Codex 호출은 없다. 상세는 `.claude/quality-state/<task-id>/skill-version-log.md`.

관련 사실로, 래퍼가 겨냥하는 실패를 이 실행에서 실측했다. 프롬프트를 위치 인자로 주고 `< /dev/null` 을 붙이지 않은 `codex exec`(PID 62112/62114)가 19분 30초 동안 상태 `S` 로 멈췄다. 같은 스키마를 `- < <파일>` 형태로 재호출하니 exit 0 으로 정상 종료했다.

## Watchdog restart budget

- Initial / remaining: 해당 없음 / 해당 없음
- Exactly-once consumption: 해당 없음
- Restart attempted / stopped: 해당 없음 / 해당 없음

해당 없음 — watchdog 호출이 없었다.

## Remaining advisory findings

두 무효 라운드 2 응답이 낸 findings 다. 유효한 리뷰로 기록되지 못했으므로 판정이 확정되지 않았고, 후속 실행에서 다시 판정해야 한다. 근거가 있으므로 waive 하지 않는다.

| ID | severity | 요지 | 후속 조치 |
|---|---|---|---|
| SPEC-009 | Medium | AC-1/CMD-6 실행 가능성의 원시 전사가 Spec 본문에서 인용되지 않는다. `spec.md:16` 의 `unrecognized_model`/`PROBE_OK` 주장도 증거 경로를 붙이지 않았다 | author 가 `evidence/p3-slash-no-changes/`, `evidence/p0-frontmatter-model/` 경로를 Spec 에 인용. 원시 전사 자체는 이미 보존 완료 |
| SPEC-010 | Low | R1.3/AC-3 이 "2.1.268 에서 확인된 CLI 기능 목록" 과 "production `build_claude_command()` 가 emit 하는 flag" 를 구분하지 않아 `operation.md` 의 단정형 문장과 계약 테스트가 거짓 서술을 고정할 수 있다 | author 가 두 목록을 분리 표기하도록 R1.3/AC-3 판정 문구를 한정 |
| SPEC-011 | Low | SPEC-007 해소로 도입한 동적 run-id 접두사 판정이, 해당 접두사의 기존 run 이 없을 때(빈 집합)의 통과·실패를 정의하지 않는다 | author 가 AC-17/CMD-8 에 빈 집합 경우(`-000001`)를 명시 |

readiness 의 READY-001~READY-003 은 author 가 모두 해소했다(경로 `.Codex/quality-state` → `.claude/quality-state`, R2.3 parse 실패 경로 판정 추가, CMD-6 구조화 판정).

## Final status

- Status: BLOCKED
- Machine-readable reason: `REVIEW_OUTPUT_INVALID`

Spec 라운드 2 리뷰가 연속 두 번 `validate_review.py validate` 를 통과하지 못해 `quality_state.py` 의 리뷰 검증 재시도 한도가 소진됐다.

두 실패의 원인은 오케스트레이터의 계약 입력 결함이다. 특히 2차는 오케스트레이터가 라운드 2 프롬프트에서 `prior_findings` 와 `resolved_finding_ids` 를 리뷰어 **출력**으로 요구한 것이 원인이다. 그 둘은 readiness 결과 스키마의 필드이고, review 페이로드의 최상위 필드는 `validate_review.py:15-18` 의 여덟 개뿐이라 거부된다. 스킬의 Review invocation contract 는 이 둘을 오케스트레이터가 보내는 **입력**으로 규정한다. 상세와 귀속은 `.claude/quality-state/<task-id>/orchestrator-incident-spec-r2.md` 에 있다.

상태 기계의 판정(`REVIEW_OUTPUT_INVALID`)과 원인 귀속(오케스트레이터 프롬프트 결함)은 분리해 기록했다. 응답 키를 삭제하거나 상태·재시도 횟수를 직접 고쳐 우회하지 않았다.

재사용 가능한 자산은 모두 보존돼 있다: strict Spec(요구사항 20, AC 20, CMD 8), 개정 노트, 이슈의 네 결함을 전부 실증한 `evidence/`, 라운드 1 리뷰와 두 무효 리뷰, readiness 결과. 후속 실행은 이 Spec 과 증거를 재사용하고 SPEC-009·SPEC-010·SPEC-011 해소부터 이어갈 수 있다.
