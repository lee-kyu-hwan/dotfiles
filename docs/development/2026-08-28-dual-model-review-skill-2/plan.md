# Quality Goal Implementation Plan

- Task ID: 20260828T021938Z-42-claude-codex-이중-리뷰-종합-pr-게시-스킬-추가-55cca675
- Mode: strict
- Status: REVISED (round 2)
- Created: 2026-08-28
- Updated: 2026-08-28
- Source goal: #42 Claude+Codex 이중 리뷰 → 종합 → PR 게시 스킬 추가

## Spec link

승인 대상 Spec: `docs/development/2026-08-28-dual-model-review-skill-2/spec.md`
SHA-256: `bf75e7f1156818cd130da19bbdde2f18b1795b5b1f7c09834695e5c02d586407`
Spec 리뷰: 라운드 1 78점 REVISE(High 3) → 라운드 2 93점 PASS(blocker 0, Critical/High 0). 잔여 advisory는 SPEC-007(Medium) 1건이며 이 Plan의 "잔여 advisory 처리"에서 다룬다.

## Global constraints

- 저장소 관례: chezmoi. 산출물은 `dot_claude/skills/dual-review/` 아래에 두며 `~/.claude/skills/dual-review/`로 배치된다. 소스 파일을 직접 편집하므로 배포는 `chezmoi apply`가 필요하다.
- 두 스크립트는 Python 3 표준 라이브러리만 import한다(Spec R8.3). 외부 패키지·requirements 파일을 추가하지 않는다.
- `pr-review-toolkit`·`codex` 플러그인 파일을 수정하지 않는다(Spec N8). 두 플러그인은 읽기 전용 참조 대상이다.
- 자동 커밋·푸시·머지·배포를 하지 않는다. GitHub에 대한 쓰기를 구현 중에 수행하지 않는다.
- `--full-auto`·`--yolo`·`--skip-git-repo-check`·샌드박스 우회 문자열을 산출물 어디에도 쓰지 않는다(Spec R3.2, AC-29).
- `GH_TOKEN`·`GITHUB_TOKEN`·`Authorization` 문자열을 스크립트에 쓰지 않는다(Spec R8.4, AC-31).
- `schemas/reviewer-output.schema.json`에 `uniqueItems`와 정규식 lookaround를 쓰지 않는다(Spec R3.8, AC-44). 나머지 세 스키마에는 제약이 없다.
- 허용 변경 경로: `dot_claude/skills/dual-review/**`, `docs/dual-review-maintenance.md`, `.gitignore`. 그 밖의 파일을 만들거나 고치지 않는다.
- 초기 dirty 경로 `docs/development/2026-08-28-dual-model-review-skill/`(선행 실행 산출물)과 `docs/development/2026-08-28-dual-model-review-skill-2/`(이 실행의 문서)를 바이트 단위로 보존한다. 되돌리거나 이 작업의 변경에 포함하지 않는다.
- test-first: 각 태스크는 실패하는 테스트를 먼저 기록하고, 최소 구현을 넣고, 통과를 기록한다.

## File map

| 파일 | 책임 | 인터페이스·행동 |
|---|---|---|
| `dot_claude/skills/dual-review/SKILL.md` | 단계 표, 두 승인 게이트, 참조 로딩 지시 | frontmatter 7필드(`name`, `version`, `description`, `argument-hint`, `disable-model-invocation: true`, `model: inherit`, `effort: high`), `version`은 `0.1.0` |
| `references/reviewer-contract.md` | 리뷰어 공통 계약, 에이전트 선택 매핑·임계값 상수, Codex 호출 템플릿, 출력 형식 우선순위 선언 문구, 입력 규모 임계값 | `CODE_EXT` 집합, 확장자별 주석 토큰 표, `comment-analyzer` 임계 3건, 파일 100개·diff 20,000줄 |
| `references/cross-critique.md` | 라운드 규칙, 새 근거 정의, 추상화 이탈 신호, 종료 규칙 | 기준선에 1차 리뷰 evidence 포함, 첫 라운드 drift 불가 |
| `references/synthesis-contract.md` | 종합자 계약, 5축 판정, 4분류, 잔존 한계 2건 | 출처 은닉 전제, 편향·본문 누출 한계 명시 |
| `references/publish-contract.md` | SHA 고정, 마커, 3단계 게시, lifecycle, 3튜플 화이트리스트, verdict 정책, 롤백 한계 | 게시물 본문 형식, 요약 첫 줄 형식 |
| `schemas/reviewer-output.schema.json` | 리뷰어 산출 계약 | 루트 object, `{verdict, summary, findings[]}`, `additionalProperties: false`, `uniqueItems`·lookaround 없음 |
| `schemas/critique.schema.json` | 교차비평 산출 계약 | 루트 object, 각 반박의 `evidence`가 `required` + `minItems: 1` |
| `schemas/synthesis.schema.json` | 종합 산출 계약 | 루트 object, 5축 전부 `required`, 분류 4값 `enum` |
| `schemas/publish-plan.schema.json` | `plan.json` 계약 | 루트 object, `additionalProperties: false`, `base_mismatch` 포함 |
| `scripts/review_state.py` | 상태 머신, 에이전트 선택, 위치 실측, 라운드 판정, 은닉·셔플 | 아래 "review_state.py 인터페이스" |
| `scripts/publish_findings.py` | `plan`/`apply`, finding_id·병합·lifecycle·3단계 게시 | 아래 "publish_findings.py 인터페이스" |
| `tests/test_review_state.py` | AC-4, AC-5, AC-17~AC-25, AC-45(프롬프트 출력), AC-50, AC-53 | 임시 git 저장소 픽스처. **Spec Test strategy가 정본이며 이 표가 그 사본이다** |
| `tests/test_publish_findings.py` | AC-1~AC-3, AC-6~AC-16, AC-39, AC-46, AC-47, AC-49, AC-51, AC-52, AC-54 | fake GitHub 클라이언트. AC-51·AC-54는 이 파일이 담당한다 |
| `tests/test_content_contracts.py` | AC-26, AC-28~AC-33, AC-38, AC-40~AC-45(계약 문구), AC-48 | 파일 계약 검사. AC-32는 이 파일이 담당한다 |
| `tests/fixtures/` | 스키마 유효·무효 픽스처, 리뷰어 산출물 표본, **상태 계약 픽스처** `state-*.json` | T2가 생성해 커밋하고 T7·T8이 소비한다. 두 스크립트 사이의 상태 필드 계약을 고정하는 유일한 산출물이다 |
| `docs/dual-review-maintenance.md` | 유지보수 runbook 4절 | 갱신 신호, 의존 점검, 테스트 명령, 버전 정책 |
| `.gitignore` | 런타임 상태 무시 | `.claude/dual-review-state/` 한 줄 추가 |

### review_state.py 인터페이스

CLI 서브커맨드. 모두 JSON을 stdout으로 낸다.

| 서브커맨드 | 인자 | 반환·효과 |
|---|---|---|
| `init` | `--root`, `--repo`, `--pr`, `--base-sha`, `--head-sha`, `--changed-files`, `--requested-base` | 상태 생성. `repo`·`pr_number`·`base_sha`·`head_sha`·`changed_files` 고정, `base_mismatch` 판정 |
| `select-agents` | `--state`, `--diff` | 선택된 에이전트 목록과 유발 신호·매치 건수를 기록하고 반환 |
| `check-scale` | `--state` | 파일 수·diff 라인 수와 임계값 초과 여부. 초과 시 `requires_user_decision: true` |
| `reduce-scope` | `--state`, `--paths` | 축소 경로 집합과 제외 파일 수를 기록 |
| `record-reviewer` | `--state`, `--reviewer`, `--output`, `--schema` | 스키마 검증 → 실패 시 `retry_count` 증가, 2회째 `excluded`. 성공 시 위치 실측·diff 범위 판정 후 정규화 finding 반환 |
| `approve-single-reviewer` | `--state`, `--reason` | 단일 리뷰 승인 기록 |
| `record-critique` | `--state`, `--round`, `--output` | 새 근거 수, 추상화 이탈 신호, 종료 사유를 계산해 반환 |
| `normalize` | `--state`, `--out` | 출처 제거 + `head_sha` 시드 결정적 셔플 결과를 파일로 |
| `record-synthesis` | `--state`, `--synthesis` | 스키마 검증 후 기록. 실행 형태별 허용 분류 위반 시 오류 |
| `show` | `--state` | 상태 전체 |

`init`은 stdout JSON에 `state_path`(생성된 상태 파일 절대 경로)를 포함한다. 검증 명령이 그 경로를 이어받는다.

모듈 함수로 노출하는 것 둘:

- `build_agent_prompt(agent, context) -> str` — AC-18(상대 산출물 부재)과 AC-45(우선순위 선언 문구)의 검증 대상.
- `validate_against_schema(data, schema_path) -> list[str]` — JSON Schema 2020-12의 부분집합(`type`, `required`, `properties`, `additionalProperties`, `enum`, `items`, `minItems`, `minimum`, `pattern`)을 해석하는 최소 검증기. 오류 문자열 목록을 반환하며 빈 목록이 유효를 뜻한다. `publish_findings.py`가 이것을 import해 쓰므로 `scripts/` 아래 파일은 두 개로 유지된다(AC-30의 "두 스크립트"와 일치).

### publish_findings.py 인터페이스

| 서브커맨드 | 인자 | 반환·효과 |
|---|---|---|
| `plan` | `--state`, `--synthesis`, `--out`, `--calls-out`(선택), `--client`(선택) | 읽기 전용. 기존 게시물 완전 조회 → lifecycle 분류 → `plan.json` 산출. `--calls-out`은 기록된 `(kind, method, target)` 3튜플 목록을 JSON 배열로 덤프한다 |
| `apply` | `--plan`, `--state`, `--calls-out`(선택), `--client`(선택) | 계획 스키마 검증 → head SHA 재확인 → 3단계 게시 → 단계별 완료 기록. `--calls-out`은 `plan`과 같은 형식 |

GitHub 접근은 `GitHubClient` 프로토콜의 아홉 메서드로만 한다. `--client fake:<경로>`로 테스트에서 주입하고, 생략하면 `gh` CLI 기반 실제 클라이언트를 쓴다. 모든 호출은 실제·fake 구분 없이 `(kind, method, target)` 3튜플로 `client.calls`에 기록되며 `--calls-out`으로 덤프할 수 있다. 이 덤프가 AC-14·AC-37의 쓰기 0건 판정 수단이다.

## Task dependencies

```
T1 스키마 ──→ T2 상태·대상 ──→ T3 위치실측 ──→ T4 라운드 ──→ T5 은닉·분류
                 │                                              │
                 │ (tests/fixtures/state-*.json 생성)           │
                 ↓                                              ↓
T1 ──→ T6 식별자·병합 ────────────────────→ T7 plan ──→ T8 apply
                                                            │
T9 references·SKILL.md ─────────────────────────────────────┤
T10 문서·gitignore ─────────────────────────────────────────┤
                                                            ↓
                                                      T11 통합 검증
```

- T1은 다른 모든 태스크의 선행이다. 스키마가 확정돼야 상태 기록과 계획 산출의 계약이 고정된다.
- T2~T5는 `review_state.py` 한 파일을 순차로 키운다. 서로 다른 서브커맨드라 테스트는 독립이다.
- **T7은 T5에 의존한다.** T7의 테스트가 `base_mismatch`(T2), `scope_reduction`(T2), `location_valid`·`in_diff_range`·hunk 경계(T3), `record-synthesis` 결과(T5)를 입력으로 요구하기 때문이다. 상태 파일이 두 스크립트 사이의 인터페이스인데 그 계약을 고정하는 스키마가 없으므로, **T2가 `tests/fixtures/state-*.json`을 실제 `review_state.py` 출력으로 생성해 커밋하고 T3·T5가 각자 담당 필드를 그 픽스처에 채운다.** T7·T8은 그 픽스처만 읽고 `review_state.py`를 호출하지 않으므로, 픽스처가 갱신되면 T7·T8 테스트가 즉시 어긋남을 드러낸다.
- T6은 T1 이후 T2~T5와 병렬이 가능하다. `finding_id`·`anchor_fingerprint`·병합은 상태에 의존하지 않는 순수 계산이다.
- T8은 T7의 계획 구조에 의존한다.
- T9·T10은 스크립트에 의존하지 않으므로 T1 이후 언제든 가능하나, T9의 계약 문구가 T4의 `build_agent_prompt` 출력과 일치해야 하므로 T5 이후에 확정한다.
- T11은 전부에 의존한다.

## Tasks

### T1. 스키마 4종과 픽스처

1. 실패 기록: `tests/test_content_contracts.py`에 스키마 4종의 루트 object 검사, `reviewer-output`의 `uniqueItems`·lookaround 부재 검사, `critique`의 `evidence` `minItems: 1` 검사, `synthesis`의 5축 required·4값 enum 검사를 작성하고 실행한다. 스키마 파일이 없으므로 실패한다.
   - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_content_contracts.py'` → 실패(파일 없음)
2. 구현: 네 스키마와 `tests/fixtures/` 아래 유효·무효 픽스처를 작성한다. `synthesis`의 분류 enum은 `["agreed","disputed","unresolved","single_source"]`, 5축은 `truth`·`introduced_by_pr`·`location_validity`·`evidence`·`actionability`.
3. 통과 기록: 같은 명령 → 통과.

만족 AC: AC-26, AC-41(스키마 부분), AC-42, AC-43, AC-44.

### T2. review_state.py — 상태 고정, 에이전트 선택, 규모 판정

1. 실패 기록: **`tests/test_review_state.py`**에 `select-agents`의 매핑 표 일치와 `code-simplifier` 미선택(AC-17), `check-scale`의 임계 초과 시 `requires_user_decision`과 **사용자 결정이 기록되기 전에는 다음 단계 전이가 거부됨**(AC-25), `reduce-scope`의 축소 경로 집합·제외 파일 수 기록(AC-25)을 작성한다. **`tests/test_content_contracts.py`**에 상태 경로 무시 여부 경고 분기(AC-32)를 작성한다. 실행 → 실패.
2. 구현: 위 서브커맨드와 `check-scale` 이후의 전이 가드를 구현한다. 에이전트 선택은 `CODE_EXT`, 확장자별 주석 토큰 표, `comment-analyzer` 3건 임계를 상수로 둔다. `init`은 다섯 값을 고정하고 `state_path`를 stdout JSON에 담으며 `--requested-base`가 PR 실제 base와 다르면 `base_mismatch`를 설정한다.
3. 통과 기록.
4. **상태 픽스처 생성:** `review_state.py`의 실제 출력으로 `tests/fixtures/state-minimal.json`(기본 경로), `state-base-mismatch.json`, `state-scope-reduced.json` 세 개를 만들어 커밋한다. T3·T5가 각자 담당 필드를 이 픽스처에 채우고, T7·T8은 이것만 읽는다.

만족 AC: AC-17, AC-25(전이 가드·상태 기록), AC-32.
AC-51·AC-54의 단정은 T7의 `test_publish_findings.py`가 담당한다(File map 정본). T2는 그 단정이 참이 되도록 구현하고 픽스처를 공급한다.

### T3. review_state.py — 위치 실측과 diff 범위

1. 실패 기록: 임시 git 저장소 픽스처를 만들고 R4.2의 네 조건(파일 부재, `line_start` 초과, `line_end` 초과, `line_start > line_end`) 각각에 대해 `location_valid=false`를, 네 조건 모두 불성립일 때만 `true`를 단정하는 테스트(AC-4)와 diff hunk 범위 밖 라인의 `in_diff_range=false`(AC-5)를 작성해 실행 → 실패.
2. 구현: `record-reviewer`의 위치 실측·diff 범위 판정을 구현한다. 파일 라인 수는 `git show <head_sha>:<path>`로 얻는다.
3. 통과 기록.
4. T2가 만든 상태 픽스처에 `location_valid`·`in_diff_range`·hunk 경계 정보를 실제 출력으로 채워 갱신한다.

만족 AC: AC-4, AC-5.

### T4. review_state.py — 리뷰어 등록 재시도와 교차비평 판정

1. 실패 기록: 스키마 위반 1회 재요청 후 2회째 `excluded`와 3회째 재요청 부재(AC-19), 단일 리뷰 승인 없이 다음 단계 전이 거부(AC-20), `build_agent_prompt` 출력에 상대 산출물 부재(AC-18), 새 근거 0건 조기 종료와 첫 라운드 기준선에 1차 리뷰 evidence 포함(AC-21), 추상화 이탈 두 조건과 첫 라운드 미발생(AC-22), `--rounds 0`의 라운드 0회·critique 미생성(AC-53), 빈 `evidence` 반박 미채택(AC-41의 행동 부분)을 작성해 실행 → 실패.
2. 구현: `record-reviewer`의 재시도·제외, `approve-single-reviewer`, `record-critique`를 구현한다.
3. 통과 기록.

만족 AC: AC-18, AC-19, AC-20, AC-21, AC-22, AC-41(행동), AC-53.

### T5. review_state.py — 은닉·셔플·종합 기록

1. 실패 기록: `normalize` 출력에 `source` 부재와 알려진 식별자 문자열(`codex`, `gpt-5.6`, `pr-review-toolkit`, 에이전트 6종 이름) 부재(AC-23), 동일 입력·동일 `head_sha`의 셔플 재현성과 다른 `head_sha`의 순서 차이(AC-24), 실행 형태별 허용 분류 집합(AC-50)을 작성해 실행 → 실패.
2. 구현: `normalize`(시드 = `head_sha`)와 `record-synthesis`(실행 형태별 분류 검증)를 구현한다.
3. 통과 기록.
4. 상태 픽스처에 `record-synthesis` 결과를 채워 갱신한다. **이 시점에 픽스처가 완성되고 T7이 시작 가능하다.**

만족 AC: AC-23, AC-24, AC-50.

### T6. publish_findings.py — 식별자와 병합

1. 실패 기록: `tests/test_publish_findings.py`에 제목 노이즈 불변성(AC-1), 라인 무관·경로/카테고리 민감(AC-2), `anchor_fingerprint`의 라인 번호 무관성(AC-3), 동일 `finding_id` 병합과 대표 위치·`additional_locations`(AC-6)를 작성해 실행 → 실패.
2. 구현: `finding_id`(`sha256(normalized_path \0 category \0 normalized_title)[:12]`), `anchor_fingerprint`, 병합 규칙을 구현한다.
3. 통과 기록.

만족 AC: AC-1, AC-2, AC-3, AC-6.

### T7. publish_findings.py — plan

1. 실패 기록: fake 클라이언트를 작성하고 **T2~T5가 만든 `tests/fixtures/state-*.json`을 입력으로** 다음을 단정하는 테스트를 `tests/test_publish_findings.py`에 작성해 실행 → 실패. `review_state.py`를 호출하지 않고 픽스처만 읽는다.
   - `plan` 경로의 쓰기 호출 0건과 `apply` 미호출(AC-15)
   - 3튜플 화이트리스트 부분집합(AC-14)
   - sticky 마커 존재 시 갱신 계획(AC-12)
   - `resolved` 분류와 `resolveReviewThread` 계획, 스레드 답글 호출 부재(AC-10)
   - 요약 첫 줄 형식과 `head_sha` 인용(AC-39)
   - inline 원소 필드 구성과 hunk 경계 축소(AC-46)
   - 조회 결과의 6필드 상태 기록(AC-47)
   - 2페이지째 마커의 `persisting` 분류와 순회 오류 전파(AC-49)
   - `--base` 불일치 시 `inline_review.skip`과 요약 본문 기재(AC-54)
   - 축소 범위의 요약 본문 기재(AC-25의 요약 부분)
   - 상태의 다섯 값만 사용하고 PR 메타 재조회가 없음(AC-51)
   - 요약 본문에 리뷰어 `excluded` 사유(Spec R3.5), 단일 리뷰어 사실(Spec R3.7), `single_source`와 `unresolved`의 구별(Spec R6.3)이 각각 포함됨
2. 구현: 목록 조회 세 메서드의 전체 페이지 순회, lifecycle 분류, 계획 산출을 구현한다.
3. 통과 기록.

만족 AC: AC-10, AC-12, AC-14, AC-15, AC-25(요약), AC-39, AC-46, AC-47, AC-49, AC-51, AC-54.

### T8. publish_findings.py — apply

1. 실패 기록: 두 번째 `apply`의 쓰기 0건과 종료 코드 0(AC-7), 2단계 실패 후 재실행의 마커 대조 단일 호출 또는 0건(AC-8), 1·2단계 완료 후 3단계만 재시도(AC-9), head SHA 불일치 시 종료 코드 != 0과 쓰기 0건(AC-11), 모든 리뷰 생성의 `event == COMMENT`와 소스의 두 문자열 0회(AC-13), `--no-publish`의 쓰기 0건(AC-16), 무효 계획 거부(AC-52)를 작성해 실행 → 실패.
2. 구현: 계획 스키마 검증, head SHA 재확인, 3단계 게시와 단계별 완료 기록, 멱등 재실행을 구현한다.
3. 통과 기록.

만족 AC: AC-7, AC-8, AC-9, AC-11, AC-13, AC-16, AC-52.

### T9. references 4종과 SKILL.md

1. 실패 기록: **`tests/test_content_contracts.py`**에 다음을 단정하는 테스트를 작성해 실행 → 실패.
   - `SKILL.md` frontmatter 7필드와 `version` SemVer 형식, 참조 경로 실재, 네 플래그·프리플라이트·두 게이트 문구(AC-28)
   - 금지 플래그 0건과 모델·effort 존재(AC-29)
   - `--sandbox read-only` 존재, 다른 `--sandbox` 값 부재, 나머지 호출 플래그 존재(AC-48)
   - 종합자 계약의 한계 2건(AC-40)
   - **Spec Failure behavior 표의 오케스트레이터 경로 네 개가 `SKILL.md`에 문구로 존재**: `gh` 미설치·미인증 시 상태를 만들지 않고 중단, 대상 PR 없음 시 중단, 두 리뷰어 모두 실패 시 게시하지 않고 중단, Claude 에이전트 일부 실패 시 커버리지 결손을 게시 요약에 남김
   - **`tests/test_review_state.py`**에 `build_agent_prompt` 출력의 우선순위 선언 문구가 `reviewer-contract.md`의 상수와 문자열 동일함(AC-45)
2. 구현: 네 references와 `SKILL.md`를 작성한다. `build_agent_prompt`가 쓰는 선언 문구를 `reviewer-contract.md`에 상수로 두고 스크립트가 그것과 같은 문자열을 쓰게 한다.
3. 통과 기록.

만족 AC: AC-28, AC-29, AC-40, AC-45, AC-48. Spec Failure behavior 표의 네 오케스트레이터 경로도 이 태스크가 담당한다.

### T10. 유지보수 문서와 gitignore

1. 실패 기록: **`tests/test_content_contracts.py`**에 `docs/dual-review-maintenance.md`의 4절 존재와 버전 정책의 세 자리 기술(AC-38), 디렉터리 5구성 존재·`templates/`·`evals/` 부재(AC-33), 표준 라이브러리 import(AC-30), 토큰 문자열 부재(AC-31)를 단정하는 테스트를 작성해 실행 → 실패.
2. 구현: 유지보수 문서를 작성하고 `.gitignore`에 `.claude/dual-review-state/` 한 줄을 추가한다.
3. 통과 기록. 추가로 `git check-ignore -v .claude/dual-review-state/` 종료 코드 0(AC-36).

만족 AC: AC-30, AC-31, AC-33, AC-36, AC-38.

### T11. 통합 검증

1. 전체 테스트: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'` → 종료 코드 0(AC-34).
2. codex 스키마 수락(AC-27): 아래 "검증 명령"의 명령을 1회 실행해 종료 코드 0과 스키마 만족 결과를 확인한다. 실행 자체가 불가능하면 `blocked`로 기록하고 통과로 적지 않는다.
3. 배치 확인(AC-35): `chezmoi diff` 출력에 `dual-review` 경로가 포함되는지 확인한다. `chezmoi apply`는 실행하지 않는다.
4. 실 API `plan`(AC-37): `gh pr list --state open --limit 1 --json number`로 얻은 PR에 빈 finding 집합으로 `plan`을 실행해 종료 코드 0, 계획 스키마 유효, 쓰기 3튜플 0건을 확인한다. 열린 PR이 없으면 `not applicable`로 기록한다.

## Verification commands

순서대로 실행한다. 모든 명령은 저장소 루트를 cwd로 하며 자리표시자를 포함하지 않는다.

| # | 명령 | 기대 결과 |
|---|---|---|
| 1 | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'` | 종료 코드 0, 실패·오류 0건 |
| 2 | `grep -REn -- '--full-auto\|--yolo\|--skip-git-repo-check' dot_claude/skills/dual-review/ \| wc -l` | `0` |
| 3 | `grep -rEoh -- '--sandbox[ =]+[a-z-]+' dot_claude/skills/dual-review/ \| sed -E 's/--sandbox[ =]+//' \| sort -u \| grep -v '^read-only$' \| wc -l` | `0` — `read-only` 이외의 `--sandbox` 값이 등호 형태를 포함해 하나도 없음 |
| 4 | `grep -REn 'GH_TOKEN\|GITHUB_TOKEN\|Authorization' dot_claude/skills/dual-review/scripts/ \| wc -l` | `0` |
| 5 | `D=dot_claude/skills/dual-review; test -f $D/SKILL.md && test -d $D/references && test -d $D/schemas && test -d $D/scripts && test -d $D/tests && ! test -d $D/templates && ! test -d $D/evals; echo $?` | `0` — 다섯 구성 존재, 두 디렉터리 부재 |
| 6 | `git check-ignore -v .claude/dual-review-state/` | 종료 코드 0, `.gitignore` 행 출력 |
| 7 | `chezmoi --source "$PWD" target-path dot_claude/skills/dual-review/SKILL.md` | 종료 코드 0, 출력 `/Users/lee-kyu-hwan/.claude/skills/dual-review/SKILL.md`. `--source`가 필요한 이유는 `chezmoi source-path`가 `/Users/lee-kyu-hwan/code/dotfiles`(main 체크아웃)를 가리켜 이 워크트리의 새 파일을 보지 못하기 때문이다(실측 확인) |
| 8 | `codex exec -C "$PWD" --sandbox read-only --ephemeral --model gpt-5.6-terra -c 'model_reasoning_effort="low"' --output-schema dot_claude/skills/dual-review/schemas/reviewer-output.schema.json --output-last-message /tmp/dr-preflight.json --json - <<< 'Return verdict "approve", a one-line summary, and an empty findings array.'` | 종료 코드 0, `/tmp/dr-preflight.json` 생성. 실행 불가(미설치·모델 거부·네트워크 실패) 시 `blocked`로 기록하고 통과로 적지 않는다 |
| 9 | `python3 -c "import sys,json,pathlib; sys.path.insert(0,'dot_claude/skills/dual-review/scripts'); from review_state import validate_against_schema; e=validate_against_schema(json.loads(pathlib.Path('/tmp/dr-preflight.json').read_text()),'dot_claude/skills/dual-review/schemas/reviewer-output.schema.json'); print(e); sys.exit(1 if e else 0)"` | 종료 코드 0, 출력 `[]` — 검증 8의 결과가 스키마를 만족 |
| 10 | 아래 "검증 10 스크립트" | 종료 코드 0. 열린 PR이 없으면 `not applicable: no open PR`을 출력하고 종료 코드 0 |

### 검증 10 스크립트 (AC-37)

```bash
set -euo pipefail
PR=$(gh pr list --state open --limit 1 --json number --jq '.[0].number // empty')
if [ -z "$PR" ]; then echo "not applicable: no open PR"; exit 0; fi
REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
BASE=$(gh pr view "$PR" --json baseRefOid --jq .baseRefOid)
HEAD=$(gh pr view "$PR" --json headRefOid --jq .headRefOid)
FILES=$(gh pr view "$PR" --json files --jq '[.files[].path] | join(",")')
WORK=$(mktemp -d)
S=dot_claude/skills/dual-review/scripts
python3 "$S/review_state.py" init --root "$WORK/state" --repo "$REPO" --pr "$PR" \
  --base-sha "$BASE" --head-sha "$HEAD" --changed-files "$FILES" > "$WORK/init.json"
STATE=$(python3 -c "import json;print(json.load(open('$WORK/init.json'))['state_path'])")
printf '%s' '{"findings":[],"classification":{}}' > "$WORK/synthesis.json"
python3 "$S/publish_findings.py" plan --state "$STATE" --synthesis "$WORK/synthesis.json" \
  --out "$WORK/plan.json" --calls-out "$WORK/calls.json"
python3 - "$WORK" <<'PY'
import json, pathlib, sys
work = pathlib.Path(sys.argv[1])
sys.path.insert(0, "dot_claude/skills/dual-review/scripts")
from review_state import validate_against_schema
errs = validate_against_schema(
    json.loads((work / "plan.json").read_text()),
    "dot_claude/skills/dual-review/schemas/publish-plan.schema.json",
)
assert not errs, f"plan.json schema errors: {errs}"
writes = [c for c in json.loads((work / "calls.json").read_text())
          if c["method"] in {"POST", "PATCH", "MUTATION"}]
assert not writes, f"unexpected write calls: {writes}"
print("AC-37 ok: plan schema valid, write calls 0")
PY
```

`plan`은 읽기 전용이므로 이 스크립트는 GitHub에 아무것도 쓰지 않는다. 마지막 단정이 그것을 3튜플 기록으로 증명한다.

미구성 검증 범주와 그 근거:

- 타입 체크: **not configured.** 저장소 루트에 `tsconfig.json`·`pyproject.toml`·`mypy.ini`가 없다.
- 린트: **not configured.** 저장소 루트에 린터 설정 파일이 없다.
- 빌드: **not configured.** 저장소 루트에 `Makefile`·`package.json`·빌드 스크립트가 없다.

## Spec Failure behavior 매핑

Spec의 Failure behavior 표 각 행이 어느 산출물·태스크의 책임인지 고정한다. 오케스트레이터 경로는 `SKILL.md` 문구로만 존재하므로 T9의 계약 테스트가 그 존재를 단정한다.

| Spec 실패 행 | 담당 산출물 | 담당 태스크 | 강제 수단 |
|---|---|---|---|
| `gh` 미설치·미인증 → 상태 생성 없이 중단 | `SKILL.md` | T9 | 계약 테스트 문구 단정 |
| 대상 PR 없음 → 중단 | `SKILL.md` | T9 | 계약 테스트 문구 단정 |
| 입력 규모 임계 초과 → 사용자 결정 | `review_state.py check-scale` + 전이 가드 | T2 | AC-25 |
| Codex 프리플라이트 실패 → 단일 리뷰 승인 경로 | `SKILL.md` + `approve-single-reviewer` | T9, T4 | 계약 테스트 문구 + AC-20 |
| Claude 에이전트 일부 실패 → 커버리지 결손을 게시 요약에 | `SKILL.md` + `plan` 요약 본문 | T9, T7 | 계약 테스트 문구 + T7 요약 문구 테스트 |
| 리뷰어 출력 스키마 위반 → 1회 재요청 후 제외 | `record-reviewer` | T4 | AC-19 |
| 두 리뷰어 모두 실패 → 게시하지 않고 중단 | `SKILL.md` | T9 | 계약 테스트 문구 단정 |
| 위치 검증 실패 → 요약 강등 | `record-reviewer` | T3 | AC-4 |
| 교차비평 무진전 → `no_new_evidence` | `record-critique` | T4 | AC-21 |
| 추상화 이탈 신호 → 사용자에게 종료 제안 | `record-critique` + `SKILL.md` | T4, T9 | AC-22 + 계약 테스트 문구 |
| `apply` 직전 head SHA 불일치 → 중단 | `apply` | T8 | AC-11 |
| 게시 1·2·3단계 실패 → 단계별 처리 | `apply` | T8 | AC-8, AC-9 |
| `--base` 불일치 → inline 금지·요약 강등 | `init` + `plan` | T2, T7 | AC-54 |
| 목록 순회 실패 → 부분 목록 대신 오류 | `plan` | T7 | AC-49 |
| 상태 경로 미무시 → 경고 후 계속 | `review_state.py` | T2 | AC-32 |

## Rollout and rollback

롤아웃: 구현 → 검증 → 코드 리뷰 → 사용자가 직접 `chezmoi apply`. 이 워크플로는 `chezmoi apply`를 실행하지 않는다. 배포 전에는 `~/.claude/skills/`에 `dual-review`가 없으므로 기존 동작에 영향이 없다.

| 롤백 트리거 | 조치 |
|---|---|
| 구현 중 태스크 실패로 중단 | 해당 태스크가 만든 파일만 삭제한다. 태스크가 파일 단위로 분리돼 있어 부분 되돌리기가 가능하다 |
| 검증 실패가 설계 결함에서 옴 | 구현을 진행하지 않고 PLAN_REVIEW로 되돌린다 |
| 배포 후 스킬이 오작동 | 커밋 되돌리기 후 `chezmoi apply`. 런타임 상태는 무시 경로에 있어 삭제만 하면 된다 |
| 스킬이 잘못 게시한 PR 코멘트 | **자동 롤백 없음.** 사용자가 GitHub UI 또는 `gh`로 직접 삭제·최소화한다. 이 한계를 `references/publish-contract.md`에 명시한다 |

호환성 점검 대상 셋을 `docs/dual-review-maintenance.md`에 기록한다: `pr-review-toolkit` 에이전트 이름 6종, `codex exec` 플래그와 모델 식별자 `gpt-5.6-terra`, GitHub REST/GraphQL 필드.

## Acceptance-criteria traceability

| Criterion | Task | Verification command | Expected outcome |
|---|---|---|---|
| AC-1 | T6 | 검증 1 | 제목 노이즈 3형태에서 동일 `finding_id` |
| AC-2 | T6 | 검증 1 | 라인 변경 시 동일, 경로·카테고리 변경 시 상이 |
| AC-3 | T6 | 검증 1 | 라인 번호 무관하게 동일 `anchor_fingerprint` |
| AC-4 | T3 | 검증 1 | 네 조건 각각 `location_valid=false`, 전부 불성립 시 `true` |
| AC-5 | T3 | 검증 1 | hunk 밖 라인 `in_diff_range=false`, 요약으로 분류 |
| AC-6 | T6 | 검증 1 | 병합 1건, 대표 위치 최소, 나머지 `additional_locations` |
| AC-7 | T8 | 검증 1 | 2회째 `apply`의 쓰기 0건, 종료 코드 0 |
| AC-8 | T8 | 검증 1 | 마커 대조 후 단일 호출 1건 또는 0건 |
| AC-9 | T8 | 검증 1 | 1·2단계 호출 0건, 3단계 미해결만 처리 |
| AC-10 | T7 | 검증 1 | `resolved` 분류, resolve 계획 포함, 답글 호출 0건 |
| AC-11 | T8 | 검증 1 | 종료 코드 != 0, 쓰기 0건 |
| AC-12 | T7 | 검증 1 | 갱신 호출 계획, 생성 계획 없음 |
| AC-13 | T8 | 검증 1 | 모든 `event == COMMENT`, 소스의 두 문자열 각 0회 |
| AC-14 | T7 | 검증 1 | 기록 3튜플이 화이트리스트 부분집합, `plan`에 쓰기 0건 |
| AC-15 | T7 | 검증 1 | `plan` 쓰기 0건, AST상 `apply` 호출 경로 없음 |
| AC-16 | T8 | 검증 1 | `--no-publish` 시 쓰기 0건 |
| AC-17 | T2 | 검증 1 | 매핑 표와 일치, `code-simplifier` 미선택, 신호·건수 기록 |
| AC-18 | T4 | 검증 1 | 프롬프트에 상대 산출물 경로·내용 부재 |
| AC-19 | T4 | 검증 1 | 2회째 `excluded`, 3회째 재요청 없음 |
| AC-20 | T4 | 검증 1 | 승인 없으면 전이 거부 |
| AC-21 | T4 | 검증 1 | `no_new_evidence` 기록, 라운드 ≤ 2, 첫 라운드 성립 |
| AC-22 | T4 | 검증 1 | 두 조건 참에서만 `abstraction_drift`, 첫 라운드 미발생 |
| AC-23 | T5 | 검증 1 | `source` 부재, 식별자 문자열 0건 |
| AC-24 | T5 | 검증 1 | 동일 시드 재현, 다른 시드 상이 |
| AC-25 | T2, T7 | 검증 1 | 전이 가드 거부 + 상태 기록 + 요약 본문 기재 세 단정 모두 통과 |
| AC-26 | T1 | 검증 1 | 네 스키마 루트 object, 유효 통과·무효 실패 |
| AC-27 | T11 | 검증 8 + 검증 9 | 8이 종료 코드 0, 9가 `[]` 출력. 8 실행 불가 시 `blocked` |
| AC-28 | T9 | 검증 1 | frontmatter 7필드·SemVer, 경로 실재, 문구 존재 |
| AC-29 | T9 | 검증 2 + 검증 1 | 2가 `0`, 1의 계약 테스트가 `gpt-5.6-terra`·`model_reasoning_effort="high"` 존재 단정 |
| AC-30 | T10 | 검증 1 | 모든 import가 `sys.stdlib_module_names`에 속함 |
| AC-31 | T10 | 검증 4 | `0` |
| AC-32 | T2 | 검증 1 | 무시 안 됨 → 경고, 무시됨 → 경고 없음 |
| AC-33 | T10 | 검증 5 + 검증 1 | 5가 `0`, 1의 계약 테스트가 다섯 구성 존재를 별도 단정 |
| AC-34 | T11 | 검증 1 | 종료 코드 0 |
| AC-35 | T11 | 검증 7 | 종료 코드 0, 출력이 `~/.claude/skills/dual-review/SKILL.md` |
| AC-36 | T10 | 검증 6 | 종료 코드 0 |
| AC-37 | T11 | 검증 10 | 종료 코드 0, 계획 스키마 유효, 쓰기 3튜플 0건. PR 없으면 `not applicable` |
| AC-38 | T10 | 검증 1 | 4절 존재, 버전 정책이 세 자리 기술 |
| AC-39 | T7 | 검증 1 | 첫 줄 형식 일치, `head_sha` 인용 |
| AC-40 | T9 | 검증 1 | 한계 2건 명시 |
| AC-41 | T1, T4 | 검증 1 | `evidence` required·`minItems: 1`, 빈 반박 미채택 |
| AC-42 | T1 | 검증 1 | 5축 required, 누락 픽스처 실패 |
| AC-43 | T1 | 검증 1 | 4값 enum, 그 밖의 값 실패 |
| AC-44 | T1 | 검증 1 | `uniqueItems` 부재, lookaround 부재 |
| AC-45 | T9 | 검증 1 | 선언 문구가 `reviewer-contract.md` 상수와 문자열 동일 |
| AC-46 | T7 | 검증 1 | 단일/여러 줄/hunk 경계 세 경우, `position` 부재 |
| AC-47 | T7 | 검증 1 | 6필드 상태 기록 |
| AC-48 | T9 | 검증 3 + 검증 1 | 3이 `0`, 1의 계약 테스트가 여섯 플래그 존재를 별도 단정 |
| AC-49 | T7 | 검증 1 | 2페이지 마커 `persisting`, 오분류 없음, 오류 전파 |
| AC-50 | T5 | 검증 1 | 세 실행 형태 각각 허용 분류만 산출 |
| AC-51 | T7 | 검증 1 | 다섯 값 기록, PR 메타 재조회 부재 |
| AC-52 | T8 | 검증 1 | 종료 코드 != 0, 쓰기 0건 |
| AC-53 | T4 | 검증 1 | 라운드 0회, critique 미생성, `critique_rounds` 빈 목록 |
| AC-54 | T7 | 검증 1 | `skip` 참, 전부 `summary_only_findings`, 요약에 두 ref |

## 잔여 advisory 처리

Spec 라운드 2의 SPEC-007(Medium)은 R10.3의 "리포트에 명시" 하위 조항에 대응 AC가 없다는 지적이다. 같은 계열 조항이 R3.5·R3.7·R6.3·R6.4에도 있다. 이 Plan은 그 조항들을 **두 부류로 나눠** 처리한다.

**게시 요약 절반은 결정적으로 강제한다.** R3.5(리뷰어 `excluded` 사유), R3.7(단일 리뷰어 사실), R6.3(`single_source`와 `unresolved`의 구별), R10.3(축소 경로 집합·제외 파일 수)이 요구하는 **게시 요약 본문** 문구는 `publish_findings.py plan`이 만드는 스크립트 산출물이다. AC-25·AC-39·AC-54와 같은 방식으로 판정 가능하므로 T7의 테스트 항목에 넣었다. Spec에 대응 AC 번호가 없는 것은 사실이지만, 이 Plan이 그 단정을 T7에 배치함으로써 구현이 강제된다.

**리포트 산문 절반만 문서 지시로 남긴다.** 리포트는 스킬 실행 시 오케스트레이터가 대화형으로 산출하는 산문이고 스크립트가 만드는 파일이 아니므로 단위 테스트의 대상이 아니다. 이 범위 구분을 `references/publish-contract.md`에 명시해 구현자가 게시 요약 쪽을 누락으로 오해하지 않게 한다.

라운드 1의 PLAN-006이 지적한 것이 정확히 이 구분의 부재였다. 원래 서술은 네 조항을 일괄해 문서 지시로 취급했는데, 그중 게시 요약 절반은 스크립트 산출물이라 판정 가능했다.

<!-- strict-only:start -->

### Threat and trust boundaries

구현과 검증이 보존해야 할 경계:

- 리뷰어 출력을 미신뢰 데이터로 취급한다. T3의 위치 실측과 T7의 diff 범위 판정을 통과한 finding만 inline 계획에 들어간다. 테스트가 네 실격 조건을 각각 단정한다(AC-4).
- 엔드포인트 화이트리스트를 3튜플로 강제한다. fake 클라이언트가 모든 호출을 기록하고 테스트가 부분집합을 단정한다(AC-14).
- 승인 게이트 두 곳을 코드 경로로 강제한다: `apply`는 `plan`에서 호출되지 않고(AC-15), 단일 리뷰 승인 없이 전이하지 않는다(AC-20).
- Codex는 `--sandbox read-only`로만 호출한다(AC-48). 다른 샌드박스 값이 산출물에 등장하면 검증이 실패한다.
- 토큰을 다루지 않는다(AC-31). 인증은 `gh` CLI에 위임한다.

### Authorization and tenant isolation

멀티테넌시가 없으므로 테넌트 격리는 해당 없다. 대응 개념인 **대상 격리**를 검증한다.

| 케이스 | 검증 명령 | 기대 결과 |
|---|---|---|
| 상태의 다섯 값만 사용 (허용) | 검증 1의 AC-51 테스트 | fake 클라이언트 기록에 PR 메타 재조회 없음 |
| 게시 직전 head SHA 재확인 (허용, 1회) | 검증 1의 AC-11 테스트 | `apply` 경로에 `get_pr_meta` 정확히 1회 |
| head SHA 불일치 시 게시 (거부) | 검증 1의 AC-11 테스트 | 종료 코드 != 0, 쓰기 3튜플 0건 |
| 화이트리스트 밖 호출 (거부) | 검증 1의 AC-14 테스트 | 기록 3튜플이 화이트리스트 부분집합 |

권한 상승이나 새 자격 증명 생성은 구현에 없다.

### Migration, compatibility, and rollback

데이터 마이그레이션·백필이 없다. 신규 파일만 추가하고 기존 파일 중 고치는 것은 `.gitignore` 한 줄뿐이다.

호환성 점검 대상과 그 증거:

| 대상 | 확인 방법 | 배포 전 요구 |
|---|---|---|
| `pr-review-toolkit` 에이전트 이름 6종 | 설치본 `agents/*.md` 파일명 | T9 계약 테스트가 참조 이름을 상수로 고정 |
| `codex exec` 플래그·모델 | 검증 8 | 종료 코드 0 |
| GitHub REST/GraphQL 필드 | 검증 9 | 계획 스키마 유효 |

롤백은 위 "Rollout and rollback" 표를 따른다. 게시된 코멘트의 자동 롤백이 없다는 것이 유일한 비가역 지점이며, 이 워크플로에서는 실제 게시를 하지 않으므로 발생하지 않는다.

### Failure recovery and observability

- 각 태스크의 실패는 그 태스크가 만든 파일에 국한된다. 태스크 경계가 파일 경계와 일치하도록 T1~T10을 나눴다.
- 스크립트의 관측 수단: 상태 파일의 단계별 기록, fake 클라이언트의 호출 기록, 테스트 실패 출력.
- 부분 실패 복구는 AC-8·AC-9가 단정한다: 완료 기록된 단계는 재실행되지 않고, 남은 것만 처리된다.
- 순회 실패 시 부분 목록을 반환하지 않고 예외를 전파한다(AC-49). 조용한 재게시보다 드러나는 실패를 택한다.

### High-risk end-to-end verification

고위험 경로는 PR 게시다. 셋으로 나눈다.

1. **fake 클라이언트 통합 검증(자동, 필수).** 검증 1이 AC-7~AC-16과 AC-49를 실행한다. lifecycle 전체, 단계별 부분 실패 후 재실행 멱등, head SHA 불일치 중단, 화이트리스트 준수, verdict 고정, 다중 페이지 순회를 포함한다. **중단 조건: 하나라도 실패하면 구현을 진행하지 않고 원인을 고친 뒤 다시 돌린다.**
2. **읽기 전용 실 API 검증(자동, 조건부).** 검증 9. 열린 PR이 없으면 `not applicable`로 기록하고 리포트에 남긴다.
3. **실 게시 E2E(이 워크플로에서 실행하지 않음).** 실제 `apply`는 외부 비가역 쓰기이므로 자동 검증에 포함하지 않는다. 사용자가 스킬을 처음 실전 사용할 때 승인 게이트를 거쳐 수행한다. **이 항목이 검증되지 않은 채 남는다는 사실을 리포트에 명시한다.**

### No production mutation confirmation

이 구현 워크플로는 프로덕션을 변경하지 않는다. 산출물은 `dot_claude/skills/dual-review/` 아래 파일들, `docs/dual-review-maintenance.md`, `.gitignore` 한 줄이다. 구현 중 자동 커밋·푸시·머지·배포를 하지 않고 `chezmoi apply`도 실행하지 않는다. 검증 8은 `codex exec`를 실행하지만 `--sandbox read-only`라 저장소를 바꾸지 않는다. 검증 9는 GitHub를 읽기만 하고 쓰기 3튜플이 0건임을 함께 단정한다.

<!-- strict-only:end -->
