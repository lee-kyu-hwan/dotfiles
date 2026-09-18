# Quality Goal Report

- Task ID: 20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900
- Mode: strict
- Status: COMPLETED
- Created: 2026-09-11
- Updated: 2026-09-15
- Source goal: #105 dual-review 실행 결함 수정 (실행 2): 실행 1이 REVIEW_OUTPUT_INVALID로 BLOCKED된 뒤 기존 strict Spec과 실증 증거를 재사용해 모델 선택·producer stdin 즉시 전달·strict schema 계약·chezmoi 설치본 패키징을 마무리한다

## Classification

strict. 자동 라우팅의 strict 트리거 셋이 걸렸고 근거는 모두 저장소와 실행으로 확인했다.

- **외부 API 호환성**: `schemas/{reviewer,critique,synthesis}.schema.json` 은 Codex `--output-schema` 와 Claude `--json-schema` 로 전달되는 structured-output 계약이다. 세 파일 모두 루트·중첩 object 에 `additionalProperties` 제약이 없었고, `critique.schema.json` 의 `new_findings.items` 는 속성 없는 bare object 였다. 실측된 거부: `"code": "invalid_json_schema"`, `"status": 400`.
- **동시성 정확성**: `_round_zero()` 가 여섯 reviewer 프로세스를 모두 start 한 뒤에야 read 하는데, `SubprocessAdapter.start()` 는 `Popen` 만 하고 프롬프트 전달을 `read()` 의 `communicate()` 까지 미뤘다. 직접 재현: 지연 0초 exit 0, 지연 6초 exit 1 (`no stdin data received in 3s`).
- **광범위한 실패 모드**: 리뷰 파이프라인 전체가 실패했고 기록된 세 브랜치 모두 `termination_reason=reviewer_failure` 였다.
- standard 조건도 충족한다: `SKILL.md`, 세 schema, `scripts/review_state.py`, tests, references 등 여러 계층이 함께 바뀐다.
- 패키징 계약 실패도 재현했다. 설치본에서 `test_packaging_contract` 가 `schemas/.gitkeep` 부재로 실패(93건 중 1건), 소스 트리에서는 93건 전부 통과 — 소스·설치본 배포 계약의 결함이다.
- 이슈 라벨은 비어 있어 분류 근거로 쓰지 않았다. 사용자가 지정한 Codex 모델 `gpt-5.6-sol` 은 strict 라우트(sol/high)와 일치한다.

## Review history

| 산출물 | 라운드 | verdict | blocker | digest |
|---|---|---|---|---|
| Spec | 1 | REVISE | SPEC-001, SPEC-002 | `d3d5f399…89c4ac` |
| Spec | 2 | PASS | 없음 | `186e1eb4…6cee4e` |
| Plan | 1 | REVISE | PLAN-001 | `c809e91f…8d5adfab` |
| Plan | 2 | PASS | 없음 | `91505df2…f574a68a4d` |
| Code | 1 | REVISE (76) | CODE-001 | `e53a8339…82534ae4` |
| Code | 2 | REVISE (78) | CODE-006 | `dcf1693c…1d18e791` |
| Code | 3 | **PASS (87)** | 없음 | `a18f1b32…3febf023` |

Spec 라운드 2 는 `spec-r2b.json`, Plan 라운드 2 는 `plan-r2b.json` 이 최종 PASS 기록이다. 두 산출물 모두 `revision_check` 가 개정 근거를 확인했다.

라운드 사이의 변화:
- SPEC-001 은 `codex exec` 의 stdin 계약을 "마지막 `-` 가 필수" 로 규정하려 했으나, P7 실험(`evidence/p7-codex-stdin-dash/`)이 `-` 없이도 파이프된 stdin 을 소비함을 보여 실제 계약은 **stdin 이 EOF 에 도달하는 것**으로 정정됐다.
- SPEC-002 는 무소견 표지의 배타성 조건이 빠져 있었고, 라운드 2 에서 `NO_FINDINGS` 단독 stdout 만 수용하고 혼합 출력을 `nonexclusive_no_findings_marker` 로 구분하는 계약이 추가됐다.
- PLAN-001 은 태스크가 AC 를 전부 덮지 않은 문제였고, 라운드 2 에서 `T1`~`T8` 의 대상 AC 합집합이 `AC-1`~`AC-20` 을 빠짐없이 덮도록 재작성됐다.

## Blocking-finding resolutions

| ID | 해소 | 검증 증거 |
|---|---|---|
| SPEC-001 | stdin 계약을 "EOF 도달" 로 재정의하고 `build_codex_command()` 의 마지막 `-` 는 유지하되 판정 근거에서 분리 | `evidence/p7-codex-stdin-dash/FINDING.md` — child exit 0, 8.03초, 토큰 `ZEBRA7713` 왕복 |
| SPEC-002 | `NO_FINDINGS` 배타 계약과 네 가지 reason 분기 명문화 | `test_no_findings_marker_requires_exact_stdout_and_preserves_diagnostics` (CMD-3) |
| PLAN-001 | 태스크-AC 매핑 재작성, traceability 20행 | Plan 독립 형식 검사, `restart-budget-decisions.md` §2 |
| CODE-006 | 대상을 동일 커밋의 clean detached worktree 로 옮겨 CMD-8 을 최종 코드 상태에서 실제로 통과시켰다. 증거 채택 논증 자체를 철회했다 | run `e7a6d2872362a4d6-000009` exit 0, `live-e2e-summary.json` 기록됨, `cmd8-clean-target-identity.md` |
| CODE-001 | `operation.md` 의 확인 기능 목록에 `--setting-sources` 추가, 하니스 전용 세 flag 를 전용 절에만 명시, 세 절을 각각 잘라 검사하는 독립 assertion 3묶음 추가 | CMD-2 재실행 exit 0 (`Ran 15 tests OK`), 전체 122 tests OK |

## Plan approval

- Approval timestamp: 2026-09-11T07:26:26Z
- Plan digest: `91505df2c25e62411e65c4552715913e8d846b7b166094d348ba2cf574a68a4d`

## Changed files

| 파일 | 의도한 변경 |
|---|---|
| `.chezmoiignore` | `.claude/skills/dual-review/**/__pycache__` 제외 추가. 배포본에 바이트코드 캐시가 섞이지 않게 한다 |
| `dot_claude/skills/dual-review/SKILL.md` | frontmatter `model: claude` → `model: opus`. `claude` 는 인식되지 않는 식별자였다(P0 전사: `[claude-code:unrecognized_model]`). 계약 변경을 반영해 `version: 1.2.0` → `1.3.0` (코드 리뷰 CODE-004) |
| `references/operation.md` | 확인 기능 아홉(`--setting-sources` 포함)·production emit·CMD-6 하니스 전용 세 flag 를 각각 별도 절로 분리하고, `--allowedTools` 가변 인자와 stdin 전용 prompt 규칙을 두 경계 각각에 명시. fingerprint 범위가 git 추적 파일이라는 사실과 그 잔여 위험도 서술 |
| `references/verification.md` | 자체 표를 `DRV-1` 부터 재번호하고 신규 gate 와 Python 버전 evidence 를 반영 |
| `schemas/critique.schema.json` | 루트·중첩 object 를 `additionalProperties: false` + `required == properties` 로 폐쇄. `new_findings.items` 에 실제 속성 부여 |
| `schemas/reviewer.schema.json` | 동일한 strict 폐쇄 |
| `schemas/synthesis.schema.json` | 동일한 strict 폐쇄 |
| `schemas/.gitkeep`, `scripts/.gitkeep` | 삭제. chezmoi archive 가 이 파일들을 배포하지 않아 설치본 계약 테스트가 실패했다 |
| `scripts/review_state.py` | 본문 수정 7건. 아래 표 참조 |
| `tests/test_contracts.py` | 정적 계약 assertion 확대(모델 식별자, 두 Codex command 변형, 세 Claude command 변형, 문서 식별자 체계, live 하니스 계약) |
| `tests/test_execution.py` | 실행 계약 테스트 확대 |
| `tests/live_e2e.py` *(신규)* | landing-noindex 실증 E2E 하니스. 표준 라이브러리만 사용 |
| `tests/test_live_api.py` *(신규)* | opt-in production structured-output 스키마 라이브 probe |

`review_state.py` 의 변경 내역:

| # | 변경 | 근거 |
|---|---|---|
| 1 | `build_claude_command()` / `build_codex_command()` 의 정확한 argv 고정 | AC-1, AC-2 |
| 2 | `SubprocessAdapter.start()` 가 regular-file stdin 으로 프롬프트를 **즉시** 전달하고 임시 자원을 정리 | AC-4, AC-5, AC-6 |
| 3 | `NO_FINDINGS` 배타 계약과 producer 별 유효성 판정, 여섯 producer gate, `main()` 종료 코드 | AC-12 ~ AC-14 |
| 4 | `tree_fingerprint()` 범위를 git 추적 파일로 한정 (승인 후 범위 변경 1) | `scope-change-fingerprint.md` |
| 5 | round-zero 프롬프트가 confidence 어휘를 광고하고 literal `Label:` 을 금지 | 아래 "실행 중 발견" |
| 6 | phase 별 timeout 분리: reviewer 300s, critique·synthesis 1800s | 아래 "실행 중 발견" |
| 7 | critique·synthesis 의 원시 출력 보존 (승인 후 범위 변경 2) | `scope-change-phase-raw-evidence.md` |
| 8 | `_prepare_producer_response()` 를 legacy `"claude"` alias 까지 확장해 validity helper 와 일치시킴 | 코드 리뷰 CODE-002 |
| 9 | `tree_fingerprint()` 가 추적 파일 0건이면 전체 트리 walk 로 후퇴 | 코드 리뷰 CODE-003 |

## 실행 중 발견해 수정한 결함

승인된 Plan 을 실행하는 과정에서 세 개의 결함이 추가로 드러났다. 전부 실증 E2E(CMD-8)를 실제로 돌려야만 도달하는 경로였고, 각각 근거와 함께 기록했다.

### A. tree_fingerprint 범위 (`scope-change-fingerprint.md`)

읽기 전용 가드가 `node_modules/.vite` 빌드 캐시의 변화를 대상 훼손으로 오판해 유효한 리뷰 여섯 건을 전부 폐기했다. fingerprint 대상 121,404 파일 대 git 추적 7,036 파일, 1회 18.3초. git 추적 파일로 한정했고 git 저장소가 아니면 기존 동작으로 후퇴한다.

### B. confidence 어휘 부재

프롬프트가 Severity 어휘만 광고하고 Confidence 형식은 말하지 않아 producer 가 `Confidence: high` 를 냈고 `float("high")` 가 실패해 전 항목이 거부돼 `all_findings_rejected` 가 됐다. 프롬프트가 confidence 어휘를 광고하도록 고치고 literal `Label:` 접두를 금지했다.

### C. 단일 timeout

교차 검토 프롬프트가 58.7KB / 20 findings 였는데 reviewer 와 같은 300초를 써서 Codex 방향이 `exit 124` 로 죽었다. 측정에 근거해 reviewer 300s, critique·synthesis 1800s 로 분리했다.

### D. critique·synthesis 원시 출력 미보존 (`scope-change-phase-raw-evidence.md`)

A~C 를 고친 뒤의 실행 `e7a6d2872362a4d6-000005` 는 round zero 여섯 producer 와 양방향 교차 검토를 **모두 통과**하고 `synthesis-input.json` 까지 만든 뒤 종합 단계에서만 실패했다. 그런데 남은 근거는 이것뿐이었다.

```json
"synthesis_status": {"attempts": 0, "exit_code": 1, "phase": "synthesis",
                     "reason": "error", "source": "fresh-claude", "status": "error", "stderr": ""}
```

`_round_zero()` 는 producer 마다 시도별 원시 stdout 을 `raw-<producer>.json` 에 남기지만 critique·synthesis 는 `_call_status()` 요약만 남기고 응답의 `raw` 를 버렸다. `claude -p` 는 한도 거부를 **stdout 단독 · 빈 stderr · exit 1** 로 보고하므로, 이 비대칭이 실패를 정보 없는 숫자 하나로 만들었다.

원인 규명은 세 가지 독립 근거로 닫혔다.

1. 보존된 run `e7a6d2872362a4d6-000003` 의 `raw-claude.json` 이 같은 서명을 남겼다: `exit_code=1`, `stderr=''`, `raw[1]: You've hit your weekly limit · resets Sep 15 at 4am (Asia/Seoul)`.
2. 실패한 `synthesis.json`·`provenance.json` 의 mtime(11:20)과 같은 분에 오케스트레이터가 동일 계정의 `session limit · resets 2:50pm (Asia/Seoul)` 을 받았다.
3. 2026-09-15 14:37 의 CMD-7 재시도가 한도 거부의 **구조화된 원문**을 잡았다: `api_error_status: 429`, `terminal_reason: "api_error"`, `is_error: true`, exit 1, stderr 공백, 메시지는 `result` 필드에만.

그리고 보존된 `synthesis-input.json`(58,421바이트 프롬프트, findings 26 · critiques 23)으로 **동일한 command·schema** 를 재현하니 exit 0 과 스키마를 지키는 `decisions` 가 돌아왔다(`evidence/synthesis-replay-2026-09-15/`). 입력·스키마·adapter 의 결정적 결함이 아니라 일시적 한도 거부였다.

따라서 수정 대상은 종합 로직이 아니라 **증거 보존**이다. `run_dual_review()` 가 critique 와 synthesis 의 모든 호출에 대해 `raw-critiques.json`(호출 순서 배열)과 `raw-synthesis.json` 을 쓴다. 성공·실패·건너뜀을 가리지 않는다. `provenance.json`·`report.md`·종료 판정·재시도 정책·timeout 값은 바꾸지 않았다.

## Verification evidence

전체 기록은 `.claude/quality-state/<task-id>/verification.json` 이다.

| ID | 명령 요지 | exit | 증거 |
|---|---|---|---|
| CMD-1 | adapter 수명주기 타깃 테스트 5건 | 0 | `Ran 5 tests in 0.553s OK` |
| CMD-2 | `test_contracts.py` 전체 | 0 | `Ran 15 tests in 0.193s OK` |
| CMD-3 | ingestion 계약 타깃 9건 | 0 | `Ran 9 tests in 0.040s OK` |
| CMD-4 | Python 3.14.7 확인 + 소스 트리 전체 discover | 0 | `Ran 122 tests OK (skipped=1)` |
| CMD-5 | `chezmoi archive` 배포본 동등성 + 배포본 전체 discover | 0 | `Ran 122 tests OK (skipped=1)`, `.gitkeep`·`__pycache__`·`.pyc` 멤버 0건 |
| CMD-6 | slash 진입점 라이브 호출 (`/dual-review --base HEAD`) | 0 | run 디렉터리 정확히 1개, `termination_reason == "no_changes"`, 모델 선택 오류 문자열 0건 |
| CMD-7 | production structured-output 스키마 라이브 probe | 0 | `Ran 1 test in 33.255s OK`, 증거 `evidence/schema-live-final/` |
| CMD-8 | landing-noindex 실증 독립 리뷰 → 교차 검토 → 종합 E2E | 0 | 최종 코드 상태에서 clean detached worktree 를 대상으로 통과. run `e7a6d2872362a4d6-000009` — 아래 별도 절 |

CMD-8 의 채택 결과는 run `e7a6d2872362a4d6-000009` 하나다. 상세와 근거는 바로 아래 절에 있다.
(이전 실행 `-000006` 은 라운드 2 에서 채택이 기각돼 **판정 근거가 아니다.** 기록은 보존하지만 인용하지 않는다.)

### CMD-8 — 대상을 clean detached worktree 로 옮겨 통과시켰다

코드 리뷰 라운드 1 수정 뒤의 첫 재실행은 실증 대상 `~/code/zambaguni-front-landing-noindex` 가
깨끗하지 않아(#1406 창의 진행 중 사용자 작업) 모델 호출 전에 거부됐다. 그때는 15:0x 의 통과 실행을
채택하려 했으나 **코드 리뷰 라운드 2 가 `CODE-006`(High) 으로 그 채택을 기각했다.** 두 델타의 도달 불가는
인정됐지만 "델타가 정확히 둘" 이라는 완전성 전제가 저장된 증거로 검증되지 않았고(`events.json` 에
구조화된 patch 기록이 없다), 승인된 Spec 277행의 strict 조항이 precondition 실패만으로도 E2E 실패로
정하기 때문이다. 리뷰어가 제시한 기계적 대안은 그 시점 파일 바이트가 보존돼 있지 않아 실행 불가능했다.

사용자 지시에 따라 **#1406 의 변경을 건드리지 않고** 같은 커밋을 가리키는 별도의 detached clean
worktree 를 만들어 대상으로 삼았다. 근거·실측·사후 처리 전문은 `cmd8-clean-target-identity.md` 에 있다.

대상 identity 는 사전에 실측해 고정했고, 사후에 **보존된 산출물만으로 다시 세웠다**
(`evidence/cmd8-clean-target/identity.json`). HEAD `0a753e2d…4252f9d9a`, merge-base
`88d1f4f1…2bb032a67`, 변경 파일 3개, unified=0 diff 18,505 바이트, 그리고 **diff 내용의 sha256
`b1ebde1c03fe879f8eb0a2a32b3070bf09aaa6d7e9fc0aedec60760a2b36ec6c`** 가 기존 worktree 와 모두 같다.
사후 재구성의 출처는 (1) 지금 다시 계측한 #1406 worktree, (2) 통과한 run `-000009` 의
`snapshot.json` 에 남은 **리뷰어들이 실제로 받은 diff 원문**, (3) 하니스가 실행 직전 남긴
`gen3-passed/live-e2e-pre.json` 이다. 실행 전 계측본은 오케스트레이터가 재실행 직전 evidence
디렉터리를 비우면서 삭제했고(코드 리뷰 CODE-011), 그 사실을 `identity.json` 첫머리에 적어 뒀다.
재구성본이 오히려 더 강한 근거다 — 삭제된 파일은 "실행 전에 잰 값" 이었지만 `snapshot.json` 의
diff 는 **리뷰어가 실제로 본 바이트** 이기 때문이다. 다른 것은 `git status --porcelain`(clean 대 사용자 작업)과
브랜치 이름(detached 대 `1406-improvement/landing-noindex`) 둘뿐이다. `review_state.py` 의 snapshot 은
base·head 두 커밋에서만 계산되고 작업 트리를 읽지 않으므로 두 worktree 의 snapshot 은 정의상 같고,
diff digest 일치가 이를 실측으로 확인한다. `--expected-branch` 를 `""` 로 바꾼 것은 약화가 아니다.
브랜치 이름보다 커밋 SHA 와 diff digest 가 강한 식별자이며 그 셋을 모두 사전 고정했다.

git-crypt 키는 만들지도 읽지도 옮기지도 않았다. smudge 필터만 `cat` 으로 대체해 암호화 blob 다섯 개를
암호문 그대로 체크아웃했고, 그 다섯은 전부 리뷰 대상 diff 밖이다.

세 세대를 실행했고 전부 보존했다.

| 세대 | run | 결과 | 원인 |
|---|---|---|---|
| 1 | `-000007` | exit 1 | Codex 교차 검토가 provider capacity 로 실패 |
| 2 | `-000008` | exit 1 | round zero 에서 `pr-review-toolkit:code-reviewer` timeout(exit 124, 재시도 포함 2회) |
| 3 | `-000009` | **exit 0** | 통과 |

**세대 1 은 이 태스크가 고친 결함의 실동작 검증이다.** `raw-critiques.json` 의 codex 레코드가
`{"type":"error","message":"Selected model is at capacity. Please try a different model."}` 와
`turn.failed` 를 원문 그대로 보존했다. 수정 전이었다면 `exit_code: 1` 이라는 숫자만 남아 원인을
귀속시킬 수 없었을 실패다 — 실제로 그 상태가 이전 세션을 막았다.

세대 2 는 AC-16 의 "하나라도 실패하면 전체 실패" 게이트가 작동함을 보여 준다. 다섯 producer 가
유효했지만 하나가 timeout 이므로 빈 findings 로 조용히 통과하지 않고 실패했다.
어느 재시도에서도 모델이나 설정을 바꾸지 않았다.

통과한 세대 3 의 관측:

```json
{"producer_count": 6, "cross_critique_calls": 2, "synthesis_calls": 1,
 "run_id": "e7a6d2872362a4d6-000009", "termination_reason": "no_new_high",
 "synthesis_status": {"status": "ok", "exit_code": 0, "reason": "", "stderr": "", "attempts": 0}}
```

- 여섯 `started:` 가 모두 첫 `read:` 보다 앞선다 (AC-4).
- reviewer 두 source 모두 `valid`, 교차 검토 양방향 `ok`/exit 0, 종합 `ok`/exit 0 (AC-16).
- 신규 산출물이 성공 경로에서도 채워졌다: `raw-critiques.json` 2 레코드(claude 2,153B / codex 103,449B),
  `raw-synthesis.json` 20,452B, 전부 `status: ok`, `exit_code: 0`.
- `live-e2e-summary.json` 이 기록됐다. `live_e2e.py` 는 before/after HEAD 동일, before/after porcelain 동일,
  보존 run digest 동일, `returncode == 0`, `run_id == expected_run_id` 가 **모두 통과한 뒤에만** 이 파일을
  쓰므로 그 존재 자체가 AC-17 을 증명한다.
- 보존 run `-000001` 의 digest 가 실행 후에도 원본 #1406 사본과 동일하다
  (`gen3-passed/preserve-run-check.json`).

사후 처리: `git worktree remove --force` 와 `git worktree prune` 으로 임시 worktree 를 제거했다.
#1406 worktree 는 수정 파일·HEAD·브랜치·보존 run 여섯 개가 **모두 그대로**다. 세 세대의 run 디렉터리와
evidence 는 `evidence/cmd8-clean-target/gen{1,2,3}-*/` 에 남겼다.

### CMD-8 증거 세대 훼손 공개 (CODE-007)

`tests/live_e2e.py` 의 `run()` 은 `live-e2e-pre.json` 을 `validate_preconditions()` **보다 먼저**
고정 경로에 쓴다. 그래서 precondition 에서 거부된 15:52 재실행이 그때까지의 pre 기록을 덮어썼다.
세대 구분과 보존본은 `evidence/live-e2e-generations/` 에 있고, 이후 CMD-8 실행은 세대마다 별도
evidence 디렉터리(`cmd8-clean-target-gen{2,3}`)를 써서 같은 훼손이 재발하지 않게 했다.

AC-17 자체는 성립한다. `live-e2e-summary.json` 은 위의 다섯 `require()` 가 모두 통과한 뒤에만 쓰이고,
`live-e2e-command.json` 이 실행 번호를 독립 보존한다.

이 write-before-validate 는 거부되는 모든 호출마다 이전 증거를 파괴하는 **스킬 소스 안의 결함**이다.
리뷰가 판정한 코드 상태를 다시 흔들지 않기 위해 이번 범위에서는 고치지 않고 별도 티켓 권고로 남긴다.

구성돼 있지 않은 검증 범주(모두 `not configured`, passed 로 기록하지 않음):

| 범주 | 참조한 저장소 근거 |
|---|---|
| type check | `package.json` 없음, `tsconfig.json` 없음, `Makefile` 없음, `.github/workflows` 없음 |
| lint | `package.json` 없음, ruff/flake8 설정 없음, `Makefile` 없음, `.github/workflows` 없음 |
| build | `package.json` 없음, `Makefile` 없음. 배포 동등성은 CMD-5 의 `chezmoi archive` 재현이 대신한다 |

## Execution watchdog

승인 후 실행한 Codex 호출의 watchdog 기록이다. 전부 빈 tmux pane 에서 foreground 로 띄웠고 모델 PID 가 pane shell 의 자손이다.

| Execution ID | child exit | elapsed (s) | result / schema | watchdog reason | signals | residual PIDs |
|---|---|---|---|---|---|---|
| `impl-b1` (T1~T2) | 0 | 390.9 | true / passed | — | [] | [] |
| `impl-b2` (T3~T4) | 0 | 503.8 | true / passed | — | [] | [] |
| `impl-t3b` | 0 | 113.8 | true / passed | — | [] | [] |
| `impl-b3` (T5~T7) | 1 | 232.8 | false / not_run | `child_exited_no_result` | [] | [] |
| `impl-t7` | 0 | 282.6 | true / passed | — | [] | [] |
| `impl-t7b` | 0 | 187.3 | true / passed | — | [] | [] |
| `impl-fingerprint` | 0 | 284.1 | true / passed | — | [] | [] |
| `impl-confidence` | 0 | 307.3 | true / passed | — | [] | [] |
| `impl-timeout` | 0 | 170.3 | true / passed | — | [] | [] |
| `impl-phase-raw` | 0 | 229.0 | true / passed | — | [] | [] |
| `fix-code-r1` | 0 | 335.2 | true / passed | — | [] | [] |

`impl-b3` 은 Codex 사용 한도 도달이다(`blocker-codex-usage-limit.md`). events 스트림에 `You've hit your usage limit ... try again at Sep 17th, 2026 8:21 PM` 과 `turn.failed` 가 남아 있다. 한도 해제 뒤 `impl-t7`·`impl-t7b` 로 좁혀 재개했고 T5~T7 을 완료했다.

## Watchdog restart budget

- Initial / remaining: null / null (이 실행에서 `--retry-budget` 를 부여하지 않았다)
- Exactly-once consumption: 0
- Restart attempted / stopped: false / false

`restart_candidate: true` 였던 두 건(`spec-author-r2` hard_timeout 900.558s, `plan-author-r1` hard_timeout 900.358s)은 부모가 **재시작하지 않기로** 판단했다. 근거와 대안(범위를 좁힌 후속 호출, 오케스트레이터 독립 형식 검사)은 `restart-budget-decisions.md` 에 전부 기록돼 있다. 두 건의 보존 번들과 원시 로그는 삭제하지 않았다.

## Remaining advisory findings

- **`raw-critiques.json` 의 Codex 레코드가 커질 수 있다.** 채택된 run `-000009` 에서는 103,449 바이트였지만, 같은 대상에 대한 다른 실행에서는 1,191,198 바이트까지 나왔다. Codex 의 `--json` 이벤트 스트림 전체가 그대로 들어가기 때문이다. run 디렉터리는 `.gitignore` 대상이라 저장소에는 영향이 없지만, 장기적으로는 보존 상한이나 요약 전략이 필요할 수 있다. 영향: 디스크 사용량만. 후속 판단 대상.
- **CMD-6 의 명령 문자열에 덮어쓰기 가드가 없다** (코드 리뷰 CODE-005). `tests/test_live_api.py` 는 `mkdir(exist_ok=False)` 로 기존 증거를 지키는데 CMD-6 의 `slash-no-changes.*` 는 매 실행마다 덮어쓴다. 승인된 판정 명령의 문자열을 바꾸는 것은 또 한 번의 범위 변경이므로 하지 않았고, 대신 재실행 직전에 직전 세대를 `evidence/cmd6-transcripts/` 로 복사해 보존하고 `verification.json` 의 CMD-6 `evidence` 를 실제 전사 발췌로 채웠다. 영향: 증거 회귀 추적. 후속으로 CMD-6 명령 문자열에도 비덮어쓰기 증거 디렉터리를 도입하는 것이 바람직하며 별도 티켓 대상이다.
- **`tests/live_e2e.py` 의 write-before-validate 가 출하 코드에 남아 있다** (코드 리뷰 CODE-013). `run()` 이 `live-e2e-pre.json` 을 `validate_preconditions()` 보다 먼저 고정 경로에 쓰므로, precondition 에서 거부되는 모든 호출이 직전 세대의 pre 기록을 파괴한다. 이번에 실제로 한 번 일어났다. 리뷰가 판정한 코드 상태를 다시 흔들지 않기 위해 고치지 않았고, 운영상으로는 세대별 evidence 디렉터리로 회피했다. 수정 방향 두 가지를 `evidence/live-e2e-generations/README.md` 에 적었다. 영향: 거부된 실행마다 증거 손실. 별도 티켓 대상.
- **`preserve-run-check.json` 이 불리언만 담는다** (코드 리뷰 CODE-014). 보존 run digest 동일성을 `true` 한 글자로만 기록해 제3자가 재계산으로 검증할 수 없다. 원본 run 디렉터리들은 양쪽 모두 남아 있어 재계산은 가능하다. 영향: 증거 자기완결성. 후속 개선 대상.
- **critique·synthesis 에 재시도가 없다.** round zero 는 transport 실패를 1회 재시도하지만 critique·synthesis 는 하지 않는다. 그래서 한 번의 429 가 20분짜리 실행 전체를 버리게 만들었다. 이번 범위에서는 종료 판정을 건드리지 않기로 해 도입하지 않았다. 영향: 일시적 실패에 대한 비용. 후속 판단 대상.

## 라운드 3 PASS 이후의 advisory 처리

라운드 3 은 blocker 없이 PASS(87) 했다. 남긴 advisory 지적 중 문서 정확성에 해당하는 넷은 이 보고서와
증거를 확정하기 전에 바로 반영했다. 코드(스킬 패키지) 소스는 한 줄도 바뀌지 않았다.

| ID | 등급 | 처리 |
|---|---|---|
| CODE-010 | Medium | 철회된 run `-000006` 을 CMD-8 대표 결과로 제시하던 블록을 삭제하고, 채택 결과가 `-000009` 하나임을 명시했다. advisory 의 Codex 레코드 크기 수치도 `-000009` 의 103,449 바이트로 고쳤다 |
| CODE-011 | Medium | 인용하던 `identity.json` 이 실제로는 오케스트레이터의 evidence 정리로 삭제돼 있었다. 보존된 `run-000009/snapshot.json` 의 diff 원문과 재계측한 #1406 로 동등성을 다시 세워 그 경로에 기록하고, 삭제 사실을 파일 첫머리와 `cmd8-clean-target-identity.md` 에 공개했다 |
| CODE-012 | Medium | CMD-8 파라미터 3개 변경을 `verification.json` 의 `scope_changes` 대장에 등록하고, 철회된 논증을 담은 `blocker-cmd8-target-precondition.md` 항목을 `superseded: true` 로 표시했다 |
| CODE-009 | Low | 정정했다. `.claude/quality-state/` 는 `.gitignore:25` 로 무시되지만 **`.claude/profile-migration/` 은 무시되지 않는다.** untracked 이며 태스크 변경도 `initial_dirty_paths` 도 아니다. 커밋 대상이 아니므로 staging 에서 명시적으로 제외한다. `verification.json` 의 `workspace_paths` 에 기록했다 |

나머지 셋(CODE-005, CODE-013, CODE-014)은 아래 Remaining advisory findings 에 후속 대상으로 남긴다.

## Final status

- Status: `completed`
- Machine-readable reason: `completed`
- CMD-1 ~ CMD-8 전부 최종 코드 상태에서 exit 0 이다.
