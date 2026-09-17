# Quality Goal Report

- Task ID: 20260916T005447Z-120-claude-deep-research-워크플로를-codex-전용-ee19ae42
- Mode: standard
- Status: COMPLETED
- Created: 2026-09-16
- Updated: 2026-09-16
- Source goal: #120 Claude deep-research 워크플로를 Codex 전용 스킬로 이식

## Classification

요청 mode 는 `auto` 였고 `standard` 가 선택됐다.

strict 위험 스캔은 전부 미해당이다. 인증·인가·테넌시 변경 없음, 결제·정산·포인트 회계 없음,
PII·보안 통제·시크릿 없음, DB/스키마 마이그레이션·백필·파괴적 작업 없음(신규 디렉터리 추가만),
외부 공개 API·웹훅·큐·멱등성·동시성 없음, 프로덕션 인프라 아님(chezmoi 가 사용자 홈
`~/.codex/skills/deep-research` 로 배포).

standard 조건은 네 가지가 성립했다. (1) 다중 파일 변경 — 신규 스킬 두 파일과
`docs/development/2026-09-16-120-codex-deep-research-skill/` 산출물. (2) 비자명한 인터페이스
도입 — 미래 Codex 인스턴스가 별도 대화 맥락 없이 따르는 실행 계약. (3) 요구사항이 대안·비목표·
수용기준의 명시를 필요로 함 — 이슈 완료조건 7개와 사용자 지정 불변조건 12개가 교차하고,
Claude 의 `VOTES_PER_CLAIM=3` / `SUPPORTS_REQUIRED=2` / `REFUTATIONS_REQUIRED=2` 를 Codex
도구 제약 아래 어떻게 재현할지 설계 판단이 필요. (4) 공유 컴포넌트 영향 — 공용 진입점
`dot_agents/skills/deep-research/SKILL.md` 와 `dot_claude/workflows/deep-research.js` 의 기존
동작을 깨뜨리지 않아야 하므로 회귀 검증 필요.

issue #120 라벨은 `enhancement`, `task`, `P2-medium` 으로 strict 트리거를 포함하지 않는다.
라벨만으로 mode 를 조정하지 않았고 위험 스캔 결과가 독립적으로 standard 를 지지한다.
light 는 배제됐다. 변경이 국소적·명백한 카피 수정이 아니고 기존 타깃 검증만으로 증명할 수 없다.

### 이슈 사실 검증에서 발견한 불일치

사용자 지시가 참조한 `AGENTS.md` 는 이 저장소에 존재하지 않는다
(`git ls-files | grep -i agents.md` 가 아무것도 반환하지 않음). 저장소 규칙 문서는 루트
`CLAUDE.md` 이며 한국어 커뮤니케이션·커밋 규칙이 거기에 있다. `CLAUDE.md` 를 규칙 출처로 사용했다.

### Codex 런타임 실측 (codex-cli 0.154.0, 2026-09-16)

설계의 근거가 된 사실은 추측이 아니라 `codex exec --sandbox read-only` 로 직접 질의해 확인했다.

- 도구 목록에 `Workflow` 가 **없다.** `web__run` 과 `collaboration.*` 는 `~/.codex/config.toml`
  에 `tools.web_search` 키가 없는데도 기본 제공된다.
- `web__run` 하위 명령: `search_query`(`domains`·`recency` 필터, 한 호출에 질의 4개까지,
  4개면 `response_length` medium 이상), `open`(검색 ref 또는 원시 URL), `find`, `click`,
  `screenshot` 등. 검색과 원문 열기가 같은 도구의 다른 명령이다.
- `collaboration.spawn_agent` 는 같은 도구를 가진 서브에이전트를 만들고 재spawn 도 가능하다.
- 동시성 상한: 런타임이 "There are 4 available concurrency slots ... including you" 라고
  명시한다. 부모가 1슬롯을 쓰므로 **동시 서브에이전트는 최대 3.**

## Review history

| 산출물 | 라운드 | score | verdict | blocker | 비고 |
|---|---|---|---|---|---|
| Spec | 1 | 80 | REVISE | SPEC-001 | High 1, Medium 4, Low 4 |
| Spec | 2 | 91 | PASS | 없음 | SPEC-001~009 해소. 신규 SPEC-010(M)·011(L)·012(L) |
| Plan | 1 | 88 | PASS | 없음 | Medium 2, Low 5 |
| Plan | 2 | 93 | PASS | 없음 | PLAN-001~008 해소. 신규 PLAN-009(L)·010(L) |
| Code | 1 | 90 | PASS | 없음 | Medium 3(CODE-001·002·003), Low 3(CODE-004·005·006) |
| Code | 2 | 93 | PASS | 없음 | CODE-001~006 해소. 신규 CODE-007(L)·008(L). 오케스트레이터의 `documentation_current` 자체 판정이 false 라 게이트는 미통과 |
| Code | 3 | — | — | — | CODE-007·008 수정 후 최종 심사 |

Spec 라운드 2 는 1차 응답이 `PASS reviews must not contain unverified evidence` 로 스키마
검증에 실패했다. 리뷰어가 명령을 실행할 수 없어 근거 3건을 `verified: false` 로 남긴 것이
원인이다. `record-review-error` 로 기록하고(재시도 1회 소진), 실행 전사를 첨부해 1회 재시도해
모든 근거가 `verified: true` 인 PASS 를 받았다.

Plan 라운드 2 는 선택이 아니라 강제였다. Codex 구현 라운드 1 이 `needs_plan_change` 를
반환해 워크플로 규칙에 따라 `IMPLEMENTING → PLAN_REVIEW` 로 복귀했다.

advisory readiness(Codex `gpt-5.6-sol`, read-only)는 Spec 라운드 1 에서 C1~C8 전부 pass,
score 100, findings 0 이었다. record-only 값이며 어떤 전이도 결정하지 않았다.

## Blocking-finding resolutions

blocker 는 하나였다.

**SPEC-001 (High, Requirement clarity)** — 신뢰도(confidence)가 Spec 어디에도 정의되지 않은 채
폴백 규칙만 "high 신뢰도 금지" 를 말했다. 이식 원본은
`dot_claude/workflows/deep-research.js:1225-1242` 에서 confidence 를 provenance 로만 파생한다.
정의가 없으면 기본 경로에서 모델이 임의로 `high` 를 붙이는 과장 확정이 가능했다.

- 적용한 해소: 요구사항 `R4.4` 신설. 신뢰도는 실제로 연 원문의 출처 품질과 표결이라는
  provenance 에서만 기계적으로 파생한다. `high` = 서로 다른 primary URL 2개 이상 AND 묶음
  전체가 정확히 3-0 `supported`. `medium` = high 가 아니면서 primary 또는 secondary 하나 이상.
  `low` = blog·forum·unreliable 만. 폴백 두 단계에서는 조건을 만족해도 high 를 부여하지 않는다.
  `AC-17` 추가, `R4.3`·Interfaces·`D2` 를 이 정의에 정렬.
- 검증 증거: Spec 라운드 2 리뷰가 `spec.md:88`(R4.4), `spec.md:170`(AC-17),
  `spec.md:237`·`:324`(정렬)을 `verified: true` 로 확인했고, 원본 계산식과의 일치를
  `dot_claude/workflows/deep-research.js:1239` 로 대조했다. 구현 산출물에서는
  `dot_codex/skills/deep-research/references/research-protocol.md:33` 의 `신뢰도 파생` 절이
  같은 조건을 담는다.

## Plan approval

승인은 두 번 받았다. Plan 이 `needs_plan_change` 로 개정되어 digest 가 바뀌었기 때문이다.

- 1차 승인 timestamp: `2026-09-16T02:23:01Z`, Plan digest
  `dab1773211adc287292fb5d3291cb5823925da04ea25a3d1895b230bbdff9571`
- 재승인 timestamp: `2026-09-16T07:01:22Z`, Plan digest
  `b818629f75d3ac9efbddf11ef447719fd43130a7aa0fcf0c30615efb61fb19e1`
- 구현에 사용된 승인 digest: `b818629f75d3ac9efbddf11ef447719fd43130a7aa0fcf0c30615efb61fb19e1`
  (Plan 리뷰 라운드 2 가 심사한 digest 와 일치)

## Changed files

기존 추적 파일은 한 건도 수정하지 않았다. `git diff --stat HEAD --` 가 빈 출력이다.

| 경로 | 상태 | 의도한 변경 |
|---|---|---|
| `dot_codex/skills/deep-research/SKILL.md` | 신규 | Codex 진입점. frontmatter 의 발견 경계와 단일 사실·단순 검색 배제, `요청 분기`·`조사 흐름`·`결과 전달과 한계`·`신뢰 경계`·`저장과 세부 계약`·`산출물 범위` 6개 절 |
| `dot_codex/skills/deep-research/references/research-protocol.md` | 신규 | 조건부 상세 계약. `조사와 원문 확인`·`기본 3표 교차검증`·`판정 임계값`·`동시성 폴백`·`신뢰도 파생`·`검증 예산`·`실패와 커버리지 공개` 7개 절. 코드 리뷰 뒤 검증자 안전 규칙, 가용 슬롯 판정, 부모 조사 상한과 폴백 예산 유보, 확정 후보와 `confirmed` 의 관계, `wait_agent` 거동 정정을 추가했고, 이어서 폴백 두 단계에 이름·순서를 부여해 슬롯 미지 경로를 확정 |
| `docs/development/2026-09-16-120-codex-deep-research-skill/spec.md` | 신규 | 승인 Spec |
| `docs/development/2026-09-16-120-codex-deep-research-skill/spec-revision-notes.md` | 신규 | Spec 라운드 2 개정 기록 |
| `docs/development/2026-09-16-120-codex-deep-research-skill/plan.md` | 신규 | 승인 Plan |
| `docs/development/2026-09-16-120-codex-deep-research-skill/plan-revision-notes.md` | 신규 | Plan 라운드 2 개정 기록 |
| `docs/development/2026-09-16-120-codex-deep-research-skill/report.md` | 신규 | 이 보고서 |

## Verification evidence

전체 전사는 `.claude/quality-state/<task-id>/verification.md` 에 있다(251줄). 아래는 실제로
실행한 명령과 종료 코드다. 작업 디렉터리는 워크트리 루트이며 모두 마지막 수정 라운드 이후
재실행한 값이다.

### 타깃 테스트

신규 산출물은 마크다운 문서 두 개이므로 코드 단위 테스트 대상이 아니다. 대신 Plan 이 정의한
결정적 문서·배포 검사 16종을 타깃 검증으로 쓴다. 아래 "판정 명령" 표가 그 결과다.

### 관련 전체 스위트

| 명령 | 종료 코드 | 결과 |
|---|---|---|
| `node --test tests/deep-research.test.mjs` | 0 | `tests 114` / `pass 114` / `fail 0`. 변경 전 기준선과 동일 |

기준선은 작업 시작 시점(base revision `72ad4f2`, 트리 clean)에 같은 명령으로 측정해
114 pass / 0 fail 이었다. Claude 워크플로 회귀 없음.

### 타입 검사 · 린트 · 빌드

**not configured.** 확인한 저장소 근거: 루트에 `package.json`·`Makefile`·`justfile` 이 없고
`.github/` 디렉터리도 없다. `.pre-commit-config.yaml` 의 유일한 훅은 gitleaks(시크릿 스캔)이다.
이번 변경은 마크다운 문서 두 개라 타입 검사·빌드 대상 자체가 없다. **이 범주를 통과로 기록하지
않는다.** gitleaks 는 커밋 시점 훅이고 이번 검증에서 커밋을 하지 않으므로 실행 대상이 아니다.
두 문서에 자격 증명이 없음은 내용 검토로 확인했다.

### 판정 명령

| ID | 목적 | 종료 코드 | 증거 |
|---|---|---|---|
| CMD-1 | Codex 스킬 정적 검증 | 0 | `Skill is valid!` |
| CMD-2 | Claude 전용 도구·경로 참조 부재 | 0 | `rg` 매치 없음(exit 1), 디렉터리 존재 선확인 통과 |
| CMD-3 | frontmatter 검사 | 0 | `name: deep-research`, 꺾쇠 없음, 1,024자 이하, 허용 키만 |
| CMD-4 | chezmoi 배포 target 경로 | 0 | `/Users/lee-kyu-hwan/.codex/skills/deep-research/SKILL.md` |
| CMD-5 | SKILL.md source-배포 동일성 + 경로 한정 diff | 0 | `chezmoi cat` 비어있지 않음, `diff -u` 무출력 |
| CMD-6 | Claude 워크플로 회귀 | 0 | `pass 114` / `fail 0` |
| CMD-7 | 기존 추적 파일 변경 없음(인덱스 포함) | 0 | `git diff --stat HEAD --` 빈 출력 |
| CMD-8 | 변경 범위가 허용 경로뿐 | 0 | 미추적 두 경로만 존재 |
| CMD-9 | SKILL.md 필수 6개 절 | 0 | 6개 모두 `grep -qx` 일치 |
| CMD-10 | research-protocol.md 필수 7개 절 | 0 | 7개 모두 `grep -qx` 일치 |
| CMD-11 | SKILL.md 가 reference 라우팅 | 0 | 참조 문자열 존재 |
| CMD-12 | `scripts/`·`agents/` 부재 | 0 | 둘 다 없음 |
| CMD-13 | description 에 네 발견 표현 | 0 | `deep research`·`딥 리서치`·`웹조사해서 정리`·`리서치 보고서` |
| CMD-14 | `검증 예산` 절의 수치·중첩 spawn 금지 | 0 | 절 한정 grep 5개 문구 일치 |
| CMD-15 | `동시성 폴백` 절의 refuted 규칙 | 0 | 절 한정 grep 일치 |
| CMD-16 | research-protocol.md source-배포 동일성 | 0 | `diff -u` 무출력 |
| CMD-17 | 배포 매핑 규칙 대조(기존 스킬) | 0 | `/Users/lee-kyu-hwan/.codex/skills/github-work-log/SKILL.md` |

### Plan 보다 엄격하게 수행한 보완 검사

미해소 advisory 를 검증 단계에서 메우기 위해 Plan 이 요구한 것보다 강한 검사를 추가로 돌렸다.

| 보완 검사 | 대응 finding | 종료 코드 | 증거 |
|---|---|---|---|
| `cmp` 로 후행 개행까지 포함한 진짜 byte 비교 | PLAN-010 | 0 | SKILL.md 3,368바이트·research-protocol.md 7,199바이트 모두 바이트 동일(최종 재검증 기준) |
| `검증 예산` 절에 검증자당 `최대 2회`·`최대 3회` 존재 | PLAN-003 | 0 | 절 한정 grep 일치 |
| `동시성 폴백` 절에 확정 조건 문장 존재 | PLAN-009 | 0 | 절 한정 grep `확정 후보로 둔다` 일치 |

`cmp` 결과는 Plan 의 CMD-5·CMD-16 이 명령 치환 때문에 "후행 개행 정규화 후 동일" 만
증명한다는 PLAN-010 의 지적을 실제 byte 동일성 확인으로 메운 것이다.

### AC 내용 위치 인용 (PLAN-002 가 요구한 증거)

명령은 절 제목의 존재만 증명하므로, 내용을 요구하는 AC 는 문장 위치를 직접 인용했다.

| 항목 | 위치 |
|---|---|
| AC-1 목적·제외 문장 | `dot_codex/skills/deep-research/SKILL.md:3` |
| AC-3 부모·검증자 공동 15회 open 예산 | `references/research-protocol.md:5` |
| AC-7 폴백 확정 조건 | `references/research-protocol.md:27` |
| AC-7 폴백 2근거 반박 임계값 | `references/research-protocol.md:27` |
| AC-7 폴백 high 금지 | `references/research-protocol.md:29` |
| AC-9 원문 URL Markdown 링크 | `dot_codex/skills/deep-research/SKILL.md:16` |
| AC-10 커버리지 공개 항목 | `references/research-protocol.md:41` |
| AC-11 신뢰 경계 | `dot_codex/skills/deep-research/SKILL.md:22` |
| AC-12 저장 미요청 시 파일 미생성 | `dot_codex/skills/deep-research/SKILL.md:26` |
| AC-17 신뢰도 high 조건 | `references/research-protocol.md:33` |
| AC-18 검증자당 상한·중첩 spawn 금지·부모 유보 | `references/research-protocol.md:37` |
| AC-19 `agents/openai.yaml` 비생성 근거 | `dot_codex/skills/deep-research/SKILL.md:30` |
| 안전규칙: 도구 실패를 반박으로 바꾸지 않음 | `references/research-protocol.md:21` |
| 안전규칙: 신뢰도는 provenance 계산값 | `references/research-protocol.md:33` |

### 대표 시나리오 네 가지 판정 (실제 웹 조사 미실행)

- **(a) 다중 출처 연구 요청** — 정규화 후 진행(`SKILL.md:8`), 3~6개 관점 분해
  (`research-protocol.md:3`), 검색 요약이 아닌 원문 열기(`:5`), 최대 5개 주장 3표 검증(`:9`),
  확정 finding 의 원문 URL 링크(`SKILL.md:16`), 결과 파일 임의 생성 금지(`SKILL.md:26`).
- **(b) 단일 사실 요청** — 무거운 흐름을 시작하지 않고 바로 검색(`SKILL.md:8`), frontmatter
  배제 문장이 과도한 선택을 막음(`SKILL.md:3`).
- **(c) 출처 충돌** — 2표 임계값과 미달 시 `unverified`(`research-protocol.md:21`), 2-1 을
  만장일치로 서술하지 않음(`:21`), 임계값 동시 성립은 `unverified` + 충돌 공개(`:21`),
  사용자에게 표결 수 공개(`SKILL.md:18`), 만장일치가 아니므로 `high` 불가(`:33`).
- **(d) 일부 fetch 실패** — 무관·paywall·열기 실패를 다른 상태로 보존(`research-protocol.md:5`),
  도구 실패를 반박으로 바꾸지 않음(`:21`), 실패 수치와 잔여 예산 공개(`:41`), 전면 실패는
  결론이 아니라 재시도 권고(`:41`), 증거 부족과 반대 증거 구분(`SKILL.md:16`).

### 변경 대조

Codex 가 결과에 적은 `changed_files` 와 실제 `git status --short` 가 일치한다. 작업 시작
시점의 dirty path 는 이 작업 자신의 문서 디렉터리 하나였고 보존됐다. 읽기 전용 대상
(`dot_agents`, `dot_claude`, `tests`, `.chezmoiignore`, `.gitignore`, `CLAUDE.md`)은
변경되지 않았다.

## Execution watchdog

구현·수정 라운드 5회 모두 정상 종료했다. 중단·보존·신호 전송이 필요한 경우가 없었다.
아래 표는 앞의 세 라운드이며, 코드 리뷰 findings 를 고친 네 번째
라운드(`fix-r1`, elapsed 209.7s)와 다섯 번째 라운드(`fix-r2`, elapsed 78.3s)도 child exit 0,
schema passed, abort·reap·신호 0건으로 같은 결과였다.

| 항목 | impl-r1 | impl-r2 | impl-r3 |
|---|---|---|---|
| Execution ID | impl-r1 | impl-r2 | impl-r3 |
| PID / PGID | 98037 / 98037 | 66064 / 66064 | 93865 / 93865 |
| Start (UTC) | 2026-09-16T02:24:13Z | 2026-09-16T07:02:03Z | 2026-09-16T07:06:21Z |
| End (UTC) | 2026-09-16T02:28:22Z | 2026-09-16T07:03:54Z | 2026-09-16T07:08:02Z |
| Elapsed (s) | 248.8 | 111.4 | 101.3 |
| Child exit code | 0 | 0 | 0 |
| Result exists / schema | true / passed | true / passed | true / passed |
| Start confirmed / reason | true / null | true / null | true / null |
| Signals / preservation | [] / null (`not_needed`) | [] / null (`not_needed`) | [] / null (`not_needed`) |
| Abort | `not_needed` | `not_needed` | `not_needed` |
| Reap | `not_needed` | `not_needed` | `not_needed` |
| Residual PIDs | [] | [] | [] |

Spec author 2회, Spec author 형식 보정 2회, readiness 1회, preflight 1회도 같은 wrapper 로
실행했고 모두 child exit 0 · schema passed 였다. abort 도 reap 도 발생하지 않았다.

## Watchdog restart budget

restart 후보가 한 번도 발생하지 않아 예산이 소비되지 않았다.

- Initial / remaining: null / null (후보 없음이므로 wrapper 가 예산을 기록하지 않음)
- Exactly-once consumption: 0 (세 라운드 모두 `retry_consumed = 0`)
- Restart attempted / stopped: false / false

## Remaining advisory findings

차단 요소는 없으며 아래는 모두 Medium 또는 Low advisory 다.

| ID | 심각도 | 내용 | 영향과 후속 |
|---|---|---|---|
| SPEC-010 | Medium | 부모가 검증자 기동 전에 남길 open 예산의 하한이 Spec 요구사항·AC 에 없고 Architecture·D3 에만 "최대 9회" 로 있었다 | **산출물에서는 해소됐다.** Plan 이 "검증자 수 × 3회(3명이면 9회), 상한이자 하한" 으로 고정했고 `research-protocol.md:37` 에 그렇게 쓰였다. 남은 것은 Spec 문서의 추적 공백뿐이며 구현에는 영향이 없다 |
| SPEC-011 | Low | Spec 의 폴백 계단에 `refuted` 판정 규칙이 없었다 | **산출물에서 해소됐다.** `research-protocol.md:27` 이 2검증자 폴백의 2표 반박과 부모 단독 폴백의 2근거 반박을 명시한다 |
| SPEC-012 | Low | `spec.md` 의 `CMD-8` 표 셀에 이스케이프되지 않은 파이프가 있어 GFM 렌더 시 표 행이 쪼개진다 | **미해소.** 심사받은 Spec digest 를 보존하려고 수정하지 않았다. 산출물에는 영향이 없다. 후속으로 그 셀의 파이프를 이스케이프하거나 명령을 표 아래 코드블록으로 옮기면 된다. Plan 은 같은 실수를 반복하지 않도록 명령 원문을 모두 코드블록에 두었다 |
| PLAN-003 | Low | `CMD-14` 가 검증자당 2회·3회 수치를 검사하지 않는데 통과 조건은 "검증자 상한 고정" 이라고 적어 명령이 증명하는 범위보다 넓게 주장한다 | **검증 단계에서 메웠다.** 절 한정 grep 으로 `최대 2회`·`최대 3회` 존재를 직접 확인(exit 0). 후속으로 CMD-14 의 패턴을 넓히거나 통과 조건 문구를 좁히면 된다 |
| PLAN-009 | Low | Plan 개정 중 부모 단독 폴백의 확정 조건 문장이 삭제됐다 | **산출물에서 해소됐다.** bounded fix 라운드로 `research-protocol.md:27` 에 복원했고 절 한정 grep 으로 확인(exit 0). Plan 문서 자체에는 그 문장이 여전히 없으므로 후속 정리 대상이다 |
| PLAN-010 | Low | `CMD-5`·`CMD-16` 이 명령 치환을 써서 "후행 개행 정규화 후 동일" 만 증명하는데 통과 조건은 byte-identical 이라고 주장한다 | **검증 단계에서 메웠다.** `cmp` 로 후행 개행 포함 byte 동일성을 직접 확인(exit 0, 최종 3,368 / 7,199 바이트). 후속으로 두 명령을 임시 파일 + `cmp` 형태로 바꾸면 주장과 증명이 일치한다 |
| PLAN-004 / PLAN-005 | Low | 라운드 1 Plan 의 T3/T2 오기와 `<워크트리>` 자리표시자 | 라운드 2 개정에서 해소됨 |
| CODE-001 | Medium | 보조 검증자 메시지 계약에 "도구 실패는 반박이 아니다" 와 웹 텍스트 격리 규칙이 없었다. `fork_turns="none"` 이면 검증자가 부모 문맥을 물려받지 않으므로 2표 임계값이 오염될 수 있었다 | **해소.** `research-protocol.md:17` 이 검증자 메시지에 두 규칙을 반드시 포함하도록 명시 |
| CODE-002 | Medium | 가용 보조 에이전트 수 판정 방법이 없고 동시 슬롯 4개가 사실처럼 단정됐다 | **해소.** `research-protocol.md:9` 가 런타임 슬롯 수에서 부모 몫 1을 뺀 값으로 판정하고 알 수 없으면 낮은 단계 폴백을 쓰며 3은 실측 기본값임을 밝힌다 |
| CODE-003 | Medium | 부모 단독 폴백에서 open 예산이 닫히지 않아 커버리지가 예고 없이 붕괴할 수 있었다 | **해소.** `research-protocol.md:37` 이 부모 조사 상한(검증자 3명 기준 6회), 폴백의 `주장 수 × 2회` 유보, 부족 시 주장 수 축소와 `검증 상한 밖` 공개를 규정 |
| CODE-004 | Low | 확정 후보가 `confirmed` 로 승격되는 조건이 정의되지 않았다 | **해소.** `research-protocol.md:21` 이 확정 후보가 곧 `confirmed` 이며 추가 승격 조건이 없음을 명시 |
| CODE-005 | Low | `wait_agent` 가 결과를 모은다는 서술이 실측 거동과 어긋났다 | **해소.** `research-protocol.md:17` 이 `wait_agent` 로 완료를 기다리되 판정·URL·근거는 각 에이전트의 최종 답변에서 읽도록 정정 |
| CODE-007 | Low | Report 의 PLAN-010 행이 수정 전 바이트 수치(5,676)를 들고 있어 현재 산출물(7,199)과 어긋났다 | **해소.** 두 곳 모두 최종 재검증 수치 3,368 / 7,199 로 갱신. cmp 는 두 파일 모두 exit 0 |
| CODE-008 | Low | "슬롯 수를 알 수 없으면 낮은 단계 폴백" 의 지시 대상이 확정되지 않아 실행마다 커버리지가 갈릴 수 있었다 | **해소.** `research-protocol.md:25` 가 폴백 1단계(2검증자)·2단계(부모 단독, 더 보수적)에 이름과 순서를 부여하고 `:9` 가 슬롯 미지 시 폴백 2단계를 적용하도록 확정 |
| CODE-006 | Low | `chezmoi diff` 증거 전사가 잘려 통과 조건이 전사만으로 확인되지 않았다 | **해소하되 새 사실 확인.** 자르지 않고 재측정한 결과 `chezmoi diff <디렉터리>` 는 디렉터리 생성 항목만 보고하고 파일 본문 diff 를 내지 않는다. 파일 경로를 직접 줘야 본문이 나온다. 전사에 두 형태를 모두 기록했고, 적용 예정 내용의 동일성은 `chezmoi cat` + `cmp` 바이트 비교가 증명한다. Plan 의 CMD-5 통과 조건 문구는 후속 정리 대상이다 |

### 운영상 기록해 둘 사건

작업 도중 오케스트레이터가 상태 파일 경로를 공유 `/tmp/qg_state_path.txt` 에 보관한 탓에,
같은 머신에서 동시 실행 중이던 다른 quality-goal 세션(다른 저장소·다른 이슈)이 같은 파일을
덮어썼다. 그 결과 `approve-plan` 과 `transition` 세 명령이 잠시 다른 작업의 state.json 을
대상으로 실행됐다. 세 명령 모두 상태 가드에 걸려 오류로 끝났고 어느 쪽 상태도 오염되지
않았음을 양방향으로 확인했다(상대 state 에 이 작업의 식별자 문자열이 없고, 이 작업 state 는
`AWAITING_PLAN_APPROVAL` 과 라운드 기록이 온전함). 이후 모든 임시 파일을 세션 전용
스크래치패드로 옮기고 공유 `/tmp` 파일을 삭제했다.

## Final status

- Status: `completed`
- Machine-readable reason: `null`

### 남은 한계 — 사용자가 알아야 할 것

1. **`chezmoi apply` 를 실행하지 않았다.** 사용자가 명시적으로 선택한 범위다. 따라서 실제
   계정 홈에 `~/.codex/skills/deep-research/` 가 생성됐고 source 와 동일하다는 사실은 이
   작업에서 증명되지 않았다. 대신 `chezmoi target-path` 로 배포 경로를, `chezmoi cat` 출력과
   source 의 `cmp` byte 비교로 적용될 내용을, 경로 한정 `chezmoi diff` 로 적용 예정 상태를
   확인했다. 이슈 완료조건 7("chezmoi 적용 후 일치")은 이 범위에서 결정적으로 증명됐으나
   apply 자체는 사용자 몫으로 남는다. 덧붙여 `chezmoi diff` 에 디렉터리를 주면 디렉터리 생성
   항목만 나오고 파일 본문 diff 는 파일 경로를 직접 줘야 나온다는 것을 실측으로 확인했다.
   따라서 배포 내용 동일성의 결정적 증거는 `chezmoi cat` 출력과 source 의 `cmp` 비교다.
2. **스킬의 실제 연구 실행을 돌려보지 않았다.** 네 시나리오 판정은 문서가 지시하는 행동과
   그 위치를 확인한 것이지, Codex 가 실제로 웹을 조사해 보고서를 낸 결과가 아니다. 실전
   동작 확인은 사용자가 Codex 에서 `딥 리서치` 요청을 한 번 돌려보는 것으로 끝난다.
3. **동시성 상한 3 은 이 머신의 실측값이다.** 런타임 컨텍스트가 알려주는 값이므로 환경에
   따라 달라질 수 있다. 그래서 스킬은 숫자를 고정하지 않고 가용 슬롯에 따라 3표 → 2표 →
   부모 교차확인으로 내려가는 계단식 폴백을 쓰고, 어느 단계에서도 `high` 신뢰도를 부여하지
   않으며 폴백 사실과 실제 표 수를 공개하도록 했다.
4. **커밋·push·PR 은 실행하지 않았다.** 사용자 승인 범위 밖이다.

---

## 완료 후 추가 변경 — 검증자 모델 배정

이 절은 quality-goal 상태 기계가 `COMPLETED` 로 전이한 **뒤**, 머지 전에 사용자 요청으로
수행한 후속 변경의 기록이다. 승인된 Spec·Plan 이 규정하지 않은 공백을 메운 것이며, 종료된
상태 기계 안에서 검증된 것이 아니라 동일한 결정적 검사와 별도 델타 리뷰로 확인했다.

### 왜 필요했나

이식본은 `collaboration.spawn_agent` 에 `model` 을 지정하지 않아 검증자가 런타임 기본값으로
돌았다. 이식 원본은 검색·수집에 `haiku`, 3표 적대적 검증에 `sonnet` 을 의도적으로 배정한다
(`dot_claude/workflows/deep-research.js:629`, `:747`, `:1011`). 검증은 `confirmed` 와
`refuted` 를 가르는 단계여서 모델 등급이 가장 크게 작용하는데, 이 배분이 이식되지 않았다.
Spec·Plan 어디에도 모델 배정이 없었고 리뷰 다섯 라운드가 모두 이를 놓쳤다.

### 실측 근거 (codex-cli 0.154.0, 2026-09-16)

- `model` 을 지정하지 않고 spawn 하면 자식이 `gpt-5.6-luna` / effort `medium` 을 보고하고
  부모를 상속하지 않는다고 답했다. **자기 보고이며 `--json` 이벤트에 자식 모델 필드가 없어
  독립 확인은 하지 못했다.**
- 없는 모델을 주면 조용한 폴백 없이 오류로 실패하며 오류가 목록을 알려준다:
  `Unknown model <이름> for spawn_agent. Available models: gpt-6-astra, gpt-5.6-sol, gpt-5.6-terra, gpt-5.6-luna, gpt-5.5`
- 없는 effort 를 주면 같은 패턴으로 실패한다:
  `Reasoning effort <값> is not supported for model <모델>. Supported reasoning efforts: low, medium, high, xhigh, max, ultra`

두 오류가 허용값을 스스로 알려주므로, 하드코딩한 식별자가 사라져도 조용히 열화되지 않고
문서에 적은 폴백 절차로 복구된다.

### 추가한 규칙 (`기본 3표 교차검증` 절)

- 검증자 spawn 시 `model` 과 `reasoning_effort` 를 명시한다. 기본값은 `gpt-5.6-terra` 와
  `high` 다. 근거는 런타임 기본 경량값보다 상위 등급을 쓴다는 것이며, 부모 모델이 더 강한
  세션에서는 부모와 같은 등급까지 올려도 된다.
- `model` 이 거부되면 오류 목록에서 `gpt-5.6-sol` → `gpt-6-astra` 중 첫 번째,
  `reasoning_effort` 가 거부되면 `high` → `xhigh` → `max` → `ultra` 중 첫 번째를 고른다.
- 재시도는 1회로 제한한다. 대체값을 고르지 못했거나 재시도도 실패하면 그 표를 실행하지 않고
  `판정 임계값` 의 미실행 규칙에 따라 `unverified` 로 두며 사유를 공개한다.
- 기본값 그대로 성공한 경우를 포함해 실제 검증에 쓴 `model` 과 `reasoning_effort` 를 결과에
  밝히고, `실패와 커버리지 공개` 절의 공개 항목에도 넣어 사용자에게 전달되게 했다.
- 서브에이전트를 쓰지 않는 폴백 2단계(부모 단독)는 이 규칙의 대상이 아니다.

`gpt-5.6-sol`(사용자 기본, xhigh)을 기본값으로 쓰지 않은 이유는 조사 1회마다 검증자 3병렬이
최상위 모델로 도는 비용이 과하다고 판단했기 때문이다. 원본도 검증에 최상위가 아닌 중상위
등급을 썼다.

### 델타 리뷰와 검증

별도 리뷰어가 이 변경만 심사해 PASS(score 87, blocker 없음)를 냈고 finding 다섯 건을
남겼다. 전부 해소했다.

| ID | 심각도 | 내용 | 해소 |
|---|---|---|---|
| MODEL-001 | Low | 미확인 자기 보고를 단정문으로 서술하고 실측 시점·런타임 표기가 없었다 | 관측 서술로 약화하고 codex-cli 0.154.0 / 2026-09-16 출처를 한 번 명시 |
| MODEL-002 | Medium | 폴백의 "가장 가까운 상위 모델" 이 판단 불가, 재시도 상한 없음, 실패 시 처리 미연결 | 대체 순서를 문서가 직접 지정, 재시도 1회 상한, 실패 시 `unverified` + 사유 공개로 연결 |
| MODEL-003 | Low | `reasoning_effort` 거부 시 지시가 없었다 | 허용값을 실측해 폴백 순서를 명시 |
| MODEL-004 | Low | 공개 의무가 사용자 전달 경로(`실패와 커버리지 공개`)에 연결되지 않았다 | 그 절의 공개 항목에 실제 검증 모델·effort 추가 |
| MODEL-005 | Low | "조사·수집보다 한 단계 강한" 근거가 이식본 구조와 어긋났다(수집 하위 에이전트 없음) | 근거를 "런타임 기본 경량값보다 상위 등급" 으로 고치고 부모가 더 강한 경우를 규정 |

이후 문단 중복과 순서를 한 번 더 정리했다.

검증 결과: 판정 명령 CMD-1~CMD-17 전부 exit 0, `node --test tests/deep-research.test.mjs`
114 pass / 0 fail(기준선 동일), `cmp` 배포 byte 동일(9,014 바이트),
`git diff --stat HEAD -- dot_agents dot_claude tests` 빈 출력.

### 이 변경의 한계

- 델타 리뷰는 quality-goal 상태 기계의 코드 리뷰 라운드가 아니다. 상태 기계는 이미
  `COMPLETED` 이며 이 변경은 그 fingerprint 밖에 있다.
- 기본값 `gpt-5.6-terra` 는 이 환경의 실측 로스터를 근거로 한 선택이다. 로스터가 바뀌면
  폴백 절차가 동작하지만, 그 동작 자체는 실제 연구 실행으로 확인되지 않았다.
- 검증자가 실제로 지정한 모델로 뜨는지는 자식의 자기 보고로만 확인했고 이벤트 스트림으로
  독립 확인하지 못했다.
