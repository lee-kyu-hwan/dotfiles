# Revision-check policy

## Identifier grammar and extraction

- (a) **정의 문법** — 요구사항 `R<n>.<m>` 은 `- **R<n>.<m>**` 로 시작하는 줄, AC `AC-<n>` 은 `- **AC-<n>**` 로 시작하는 줄, 결정 `D<n>` 은 `### D<n>.` 헤딩, 태스크 `T<n>` 은 `### T<n>.` 헤딩, 판정 명령 `CMD-<n>` 은 첫째 또는 둘째 셀이 그 ID 인 표 행이다.
- (b) **추출 범위 셋** — ① 정의 범위: 펜스 코드 블록 밖의 줄. ② 참조 범위: 펜스 코드 블록과 인라인 코드 스팬(백틱 1개 또는 2개로 감싼 구간) 밖의 텍스트. 다른 문서의 식별자나 예시를 인용할 때는 백틱으로 감싸 참조에서 제외한다. ③ 판정 수단 범위: Spec AC 본문은 코드 스팬 밖에 있는 마지막 `[실행]`/`[문서]` 표기를 고르고, `[실행]` 이면 그 뒤 괄호 안 전체를, `[문서]` 이면 그 뒤 줄 끝까지를(둘 다 코드 스팬 포함) 읽으며, Plan 추적표의 판정 수단 셀과 태스크 본문의 `CMD-<n>` 참조는 백틱을 제거한 전체 문자열을 읽는다. 관행상 판정 수단은 코드 스팬 안에 쓰이기 때문이다(#70 `plan.md:394` 의 `` `CMD-2 -k test_…` ``).
- (c) **판정 수단 토큰** — ③ 범위의 문자열에서 백틱을 제거하고 공백으로 나눈 조각 중, `CMD-<n>` 에 정확히 일치하는 것, `test_` 로 시작하는 `\w+`, `[\w./-]+\.[A-Za-z0-9]+` 에 일치하는 파일명 형태(`spec.md`, `docs/quality-goal-maintenance.md`)의 셋이다. `-k`·`§`·서술어 같은 나머지 조각은 토큰이 아니다.
- (d) **정의 수 하한** — spec 은 요구사항 정의 0 또는 AC 정의 0, plan 은 태스크 절 0 또는 추적표 AC 행 0 이면 `문법 미충족` 종류의 `empty` 칸 하나를 기록해 종료 코드 `1` 을 만든다. 하한 미달 산출물은 다른 칸이 하나도 없어도 `passed` 가 `true` 가 될 수 없다. 이것이 없으면 정의가 0 인 산출물이 `empty_cells == 0` 으로 공허하게 통과한다.

## Cells

Spec cells are `R→추적행`, `R→AC`, `추적행 AC 존재`, `추적행→R`, `R 수=추적 행 수`, `AC→R`, `AC→판정수단`, `AC→CMD 존재`, `AC 번호 연속`, `중복 정의`, `참조 무결성`, and `문법 미충족`.

Plan cells are `Spec AC→Plan 추적행`, `Plan 추적행→Spec AC`, `AC→태스크`, `태스크 존재`, `태스크 대상 AC→추적행`, `추적행→태스크 대상 AC`, `AC 등장 행에 판정수단 동반`, and `추적행 CMD 존재`. A Plan task-body `CMD-<n>` reference is the code-span exception: it must resolve in the Plan verification-command table. The diff layer also emits `파급표` when any required ripple value is absent.

## Revision notes

For round two or later, write the exact section heading `## 라운드 <n> 개정` and this exact header:

`| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |`

`요구사항` names the touched requirement. `해소 finding` records the finding resolved. `함께 바뀐 항목` 셋째 열에서 `ripple[].acceptance_criteria` 의 각 AC ID 가 단어 경계로 등장하고, 그 등장 중 하나 이상의 바로 뒤 괄호가 `일치`/`모순` 으로 시작하면 충족; 빠진 AC 는 `<R>/<AC>`, 토큰 없는 AC 는 `<R>/<AC>/판정` 을 missing_rows 에. `상호작용 판정` states in one sentence whether this resolution breaks another resolution's premise or creates a new gap. `치환 근거` records why an earlier resolution was replaced; use `자체 개정` and `치환 없음` when they apply. Empty, whitespace-only, `-`, and `—` cells are invalid.

## Exit codes and rounds

- Exit `0`: no empty cells and complete required notes.
- Exit `1`: an empty cell, missing note row, blank note cell, or missing required note section.
- Exit `2`: an unreadable input, malformed state, missing snapshot, or snapshot digest mismatch.

Round 1 has no base snapshot and is exempt from revision notes. Later rounds use `snapshots/<artifact>-r<N>.md` as the base and its SHA-256 must equal the last recorded review digest. A legacy state without the `revision_checks` key is exempt. Otherwise `record-review` for Spec or Plan round 2+ requires a revision-check JSON: it validates schema, artifact, expected round, current digest, and `passed: true`, then records its absolute path and digests. Code reviews reject that option.

## Security and risk

| 사례 | 성격 | 기계 포착 | 칸 종류 또는 미포착 사유 |
|---|---|---|---|
| #70 1~5 (readiness a2·a4·a6, Plan b2·b3) | 같은 사실을 말하는 다른 곳의 문언 발산 | 부분 | 식별자를 옮긴 경우만 `참조 무결성`(예: `READY-05` 의 `R4.3`→`R6.10` 참조 오류). 문언만 다른 경우는 미포착 — R5 `상호작용 판정` 열 |
| #70 6 (`SPEC-17`) | 신설 상태·명령에 거부 계약이 없어 닫힌 구멍이 새 경로로 되살아남 | 미포착 | 설계 판단. 파급표(R4.3)가 신설 요구사항의 AC 를 열거하지만 거부 계약의 유무는 리뷰어 몫 — R5 `상호작용 판정` 열 |
| #70 7 (Plan b2 Critical) | 오케스트레이터 프롬프트의 digest 자리 오기 | 범위 밖 | 산출물이 아니라 프롬프트 파일의 결함. Non-goal 이 아닌 대상 외 |
| #70 8 (`PLAN-02`) | 태스크 본문이 축약 표기를 써 67 AC 의 테스트 이름이 어디에도 없음 | 포착 | `AC 등장 행에 판정수단 동반` — 추적행의 테스트 이름이 태스크 본문의 AC 등장 행에 없음 |
| #70 9 (`PLAN-06`) | 같은 요구사항의 짝 AC 판정 대상 불일치 | 포착(실측) | `AC 등장 행에 판정수단 동반`, 파급표가 `R9.9` 의 세 AC 를 열거 |
| #42 `PLAN-009` | 번호 이동 뒤 옛 번호 참조 잔존 | 포착 | `참조 무결성`(정의 없는 ID 참조), `removed_ids` |
| #42 `PLAN-010` | 두 해소의 교차점에 픽스처 정의 공백 | 미포착 | Non-goal 2(File map 완전성) — R5 `함께 바뀐 항목`·`상호작용 판정` 열 |
| #42 `PLAN-012` | 자리표시자 치환의 근거 부재 | 형식만 | R5 `치환 근거` 열의 빈 칸 금지. 근거의 진위는 Non-goal 4 |
| #61 코멘트 3 (`AC-31` 누락) | 바꾼 요구사항을 참조하는 AC 를 파급 분석에서 빠뜨림 | 포착 | 파급표(R4.3)가 건드린 요구사항의 모든 AC 를 자동 열거 |
