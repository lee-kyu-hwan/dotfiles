# Quality Goal Implementation Plan

- Task ID: 20260903T092537Z-44-37-38-quality-goal-리뷰-루프-결함-3건-수정-라운드-33f2fb89
- Mode: standard
- Status: PLAN_REVIEW (round 1)
- Created: 2026-09-03T10:20:00Z
- Updated: 2026-09-03T10:20:00Z
- Source goal: #44 #37 #38 quality-goal 리뷰 루프 결함 3건 수정 — 라운드 2+ prior findings 전문 전달, 미검증 사유 REVISE의 라운드 소모 방지, no-PASS-when-unverified 결정적 게이트 승격

## Spec link

- 승인 대상 Spec: `docs/development/2026-09-03-quality-goal-review-loop/spec.md`
- Spec SHA-256: `35733b1bf51274b696d94c83babeee52ef65fce9eaa7d5c264f8eaef7bc306f6`
  (상태 파일의 `artifact_digests.spec`와 동일한 값이며, spec 리뷰 라운드 2가 PASS를 낸
  바로 그 내용이다)
- Spec 리뷰 결과: 라운드 1 REVISE(84, blocker SPEC-001) → 라운드 2 PASS(93, blocker 0,
  Critical/High 0). 게이트 `{"passed":true,"reasons":[]}`.

### Spec의 미해소 advisory 2건에 대한 이 Plan의 처리

Spec 라운드 2가 Low 2건을 advisory로 남겼다. 통과한 Spec은 동결이므로 편집하지 않고,
이 Plan이 권위 서술을 제공한다.

- **SPEC-006 (Low)** — Spec의 Test strategy 절이 변이 검증 대상을 "신규 규칙 11개"로
  적었으나 AC-55는 13개를 열거한다. R5.5가 AC-55의 목록을 권위로 선언한다.
  **이 Plan은 변이 대상을 13개로 확정한다**(T6 참조). 구현자는 Spec의 Test strategy 절
  숫자가 아니라 AC-55의 (1)~(13)을 따른다.
- **SPEC-007 (Low)** — 두 곳의 Decision 인용이 어긋났고, **둘 다 리뷰어 지적이 맞다.**
  Spec 라운드 2 개정에서 D3(2번째 호출을 exit 0으로 두는 결정)을 새로 끼워넣으면서 이후
  번호가 하나씩 밀렸는데, 본문의 두 인용을 따라 고치지 않은 결과다.
  - Spec R4.3 말미의 `(D9)`는 **D11**이어야 한다. D9는 재수행 digest 바인딩 결정이고,
    유지보수 문서의 추적 목록을 열거 + 권위 포인터로 바꾸는 결정은 D11이다.
    **이 Plan은 T5에서 D11을 근거로 인용한다.**
  - Spec Non-goal 1 말미의 `(D3)`는 **D4**여야 한다. "새 실패 경로가 같은 결함(#43)을
    재생산하지 않아야 한다"를 결정하는 것은 자동 터미널 전이를 금지한 D4(`spec.md:929`)
    이고, D3(`spec.md:913`)은 그 금지 때문에 형제 함수의 persist-then-transition 패턴을
    쓸 수 없다는 **파생 결정**이다. **이 Plan은 T2 전제 2와 T2-3c에서 D4를 근거로
    인용한다.**
  두 인용 오류는 요구사항·AC·설계 내용을 바꾸지 않으므로 통과한 Spec을 편집하지 않고
  이 Plan이 권위 서술을 제공한다.

## Global constraints

1. **변경 파일 allow-list (Spec Non-goal 11).** 변경은 다음 세 경로 아래로만 허용한다:
   `dot_claude/skills/quality-goal/`, `dot_claude/agents/quality-reviewer.md`, `docs/`.
   `.gitignore`, 다른 스킬, chezmoi 소스의 다른 파일은 건드리지 않는다.
2. **#43 블록 동결 (Spec Non-goal 1).** `quality_state.py`의
   `recurring = next(...)`부터 `REVIEW_LIMIT_EXHAUSTED`까지 9줄은 base revision과 바이트
   동일해야 한다. 이 블록 **앞쪽**에 검사를 추가하는 것은 허용되고, 블록 자체의 수정은
   금지다.
3. **`ROUND_LIMITS`·`references/` 동결 (Spec Non-goal 7, 8).** `ROUND_LIMITS`는
   `{"spec": 3, "plan": 2, "code": 3}` 그대로, `references/` 5개 파일은 전부 불변이다.
4. **배포 금지 (Spec Non-goal 2).** 구현·검증·리뷰 단계에서 `chezmoi apply`를 실행하지
   않는다. 인자 없는 `chezmoi apply`는 어느 단계에서도 금지다.
5. **커밋·머지 (Spec Non-goal 3).** Codex는 커밋하지 않는다. 커밋과 PR 생성은
   오케스트레이터가 사용자 승인 이후 수행하고, 머지는 하지 않는다.
6. **`__pycache__` 위생.** 모든 Python 호출에 `PYTHONDONTWRITEBYTECODE=1`을 붙인다.
   변이 검증 사이클마다
   `find dot_claude/skills/quality-goal -name '__pycache__' -type d -prune -exec rm -rf {} +`
   를 실행한다. `.gitignore`가 `__pycache__/`를 덮어 `git status`에 나타나지 않으므로
   오염이 조용히 오판을 만든다.
7. **테스트 우선.** 각 태스크는 실패하는 검증을 먼저 기록하고, 최소 구현을 넣고, 통과를
   기록한다. 예외는 T2뿐이며 그 사유와 승인 근거는 "Task dependencies"에 기록한다.
8. **기준선.** base revision `5ed7b57387d6a271e8e014091ff8143f488e0d29`, 전체 스위트
   201개 통과(exit 0), 사전 dirty 경로 0건. 완료 시 스위트는 201을 초과하고 실패 0건이다.
9. **Codex 실행 규율.** `--skip-git-repo-check`, `--full-auto`, `--yolo`는 금지다.
   샌드박스는 `workspace-write`, 모델은 `gpt-5.6-terra`, effort `high`
   (`references/model-routing.md`의 standard 경로).
10. **Codex 라운드는 1회로 계획한다.** 코드 리뷰 한도가 3라운드이고 Codex 라운드마다
    리뷰 라운드를 1개 소모하므로, 전체 구현을 한 번에 넘기고 남은 2라운드를 bounded fix에
    남긴다.

## File map

| 경로 | 조치 | 책임 / 영향 인터페이스 |
|---|---|---|
| `dot_claude/skills/quality-goal/scripts/validate_review.py` | 수정 | `_prior_open_finding_ids` 확장(R1.1~R1.8), `EVIDENCE_FIELDS`에 `verified` 추가 + `EVIDENCE_STRING_FIELDS` 신설 + boolean 검사(R3.2), PASS+미검증 금지(R3.3). `evaluate_gate`는 불변 |
| `dot_claude/skills/quality-goal/scripts/quality_state.py` | 수정 | `record_review_unverified` 함수 + `record-review-unverified` 서브파서(R2.2~R2.7, R2.4b), 초기 상태에 `review_unverified_retry: None`(R5.2), `record_review`에 R2.12 digest 바인딩 검사와 R2.8 초기화 추가. `record_review`의 자동 전이 블록·`ROUND_LIMITS`·`ALLOWED_TRANSITIONS`·`TERMINAL_STATES`는 불변 |
| `dot_claude/skills/quality-goal/schemas/review.schema.json` | 수정 | evidence 항목에 `verified` boolean 필수 추가(R3.1). `additionalProperties: false`·`uniqueItems` 2곳·나머지 enum 불변 |
| `dot_claude/skills/quality-goal/SKILL.md` | 수정 | Review invocation contract 확장(R1.9·R1.10), 미검증 REVISE 정책 신설(R2.9·R2.11·R2.12), frontmatter `version: 4.0.0`(R4.1). 500행 미만 유지(R5.6) |
| `dot_claude/agents/quality-reviewer.md` | 수정 | 라운드 2+ open finding 해소 판정 규칙(R1.11), `verified` 기입 규칙(R2.10·R3.6). frontmatter·도구 목록·BLOCKED payload 8필드 규칙 불변 |
| `dot_claude/skills/quality-goal/tests/test_validate_review.py` | 수정 | prior 확장 수용·거부, `verified` 검증, PASS 금지, `SchemaDriftTests` evidence 필수 필드, `valid_review()` 헬퍼에 `verified` 추가. **`:384`의 `for field in ("claim", "location")` 루프는 불변**(R3.5) |
| `dot_claude/skills/quality-goal/tests/test_quality_state.py` | 수정 | `record-review-unverified` 수용·거부 전수, 상태 키 집합, digest 바인딩, `record_review`의 PASS+미검증 거부, `valid_review()` 헬퍼에 `verified` 추가 |
| `dot_claude/skills/quality-goal/tests/test_content_contracts.py` | 수정 | frontmatter `version` 기대값 `4.0.0`, SKILL.md 계약 5건, quality-reviewer 계약 3건 |
| `dot_claude/skills/quality-goal/tests/fixtures/review-valid-plan.json` | 수정 | evidence 항목에 `"verified": true` 추가 |
| `dot_claude/skills/quality-goal/tests/fixtures/review-high-finding.json` | 수정 | evidence 항목에 `"verified": true` 추가 |
| `dot_claude/skills/quality-goal/tests/fixtures/verification-pass.json` | **불변** | evidence 배열이 없어 영향 없음. AC-51이 `git diff` 빈 출력으로 확인 |
| `docs/quality-goal-maintenance.md` | 수정 | 추적 목록 갱신(R4.3, 근거 D11) |
| `docs/development/2026-09-03-quality-goal-review-loop/{spec,plan,report}.md` | 생성 | 산출물(R4.4). `spec.md`·`plan.md`는 이미 존재, `report.md`는 종결 직전 생성 |
| `dot_claude/skills/quality-goal/references/*.md` | **불변** | Non-goal 8. AC-58이 `git diff` 빈 출력으로 확인 |

## Task dependencies

```
T1 (#44 prior 확장)      ──┐
                           ├─→ T3 (#38 스키마·evidence) ──→ T6 (통합 검증·변이·범위)
T2 (#37 상태 머신)       ──┘                                    ▲
T4 (문서 계약 + content 테스트) ────────────────────────────────┤
T5 (버전 4.0.0 + 유지보수 문서) ────────────────────────────────┘
```

- **T1 → T3**: 둘 다 `validate_review.py`를 만진다. T1이 prior 검증부(`:70-93` 인근)를,
  T3이 evidence 검증부(`:233-268` 인근)를 만져 코드 영역은 겹치지 않지만, 순차 적용해
  충돌을 없앤다. 사용자 지정 순서 #44 → #37 → #38과도 일치한다.
- **T2 → T3 (역방향 의존, 승인된 예외)**: T2가 구현하는 R2.1 트리거 조건은 T3이
  도입하는 `evidence[].verified`를 참조한다. 따라서 **T2 종료 시점에는 T2의 신규 테스트가
  실패한다** — `verified` 키가 아직 `EVIDENCE_FIELDS`에 없어 `unknown field: 'verified'`
  검증 오류가 나기 때문이다. 이는 Spec D8이 명시한 예상된 중간 상태이며, 전제 7(테스트
  우선)의 유일한 예외다. **T2와 T3은 하나의 검증 단위**이며 녹색 판정은 T3 종료 시점의
  전체 스위트로만 한다. 구현자는 T2에서 그 실패 메시지를 기록하고 T3 직후 같은 테스트가
  통과함을 기록한다.
- **T4·T5는 코드 경로와 독립**이다. T4는 Markdown 계약과 그것을 고정하는 content 테스트만,
  T5는 frontmatter 값과 문서만 만진다. T1~T3과 병렬 가능하나, 단일 Codex 라운드로
  넘기므로 순차 실행한다.
- **T6은 전 태스크 완료 후**에만 의미가 있다. 변이 검증은 최종 소스를 대상으로 한다.

## Tasks

### T1 — #44: `--prior` 입력 확장 (R1.1~R1.8)

**대상**: `scripts/validate_review.py`, `tests/test_validate_review.py`

1. **실패 기록.** `tests/test_validate_review.py`에 AC-1~AC-14의 테스트를 먼저 추가한다.
   `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_validate_review.py'`
   → 신규 테스트가 실패한다(현재 `_prior_open_finding_ids`가 `open_findings`·
   `resolved_finding_ids`·최상위 unknown 키를 전혀 보지 않으므로, 거부를 기대하는 테스트가
   `valid: true`를 받아 실패). 실패 개수와 메시지를 기록한다.
2. **구현.** `_prior_open_finding_ids`를 확장하거나 그 옆에 `_validate_prior`를 신설한다.
   - 상수 `PRIOR_FIELDS = ("open_finding_ids", "open_findings", "resolved_finding_ids")`,
     `OPEN_FINDING_FIELDS = ("id", "severity", "description", "evidence_location",
     "required_resolution", "resolution_claim", "resolution_evidence")`,
     `OPEN_FINDING_STRING_FIELDS = ("id", "severity", "description", "evidence_location",
     "required_resolution")`를 모듈 상단 상수 블록(`:39-48` 인근)에 둔다.
   - 최상위 unknown 키는 기존 `_unknown_keys`/`_format_key` 헬퍼(`:59-67`)를 재사용해
     `prior has unknown field: 'X'` 형태로 오류를 낸다(R1.8).
   - `open_findings` 항목: 7필드 필수·unknown 키 거부·`OPEN_FINDING_STRING_FIELDS`는
     `_is_non_empty_string`·`severity`는 `SEVERITIES` 멤버십·`resolution_claim`과
     `resolution_evidence`는 `None` 또는 `str`·`id` 중복 거부.
   - `open_findings` 존재 시 `open_finding_ids ⊆ {open_findings[*].id}`(R1.5, 역방향
     비요구).
   - `resolved_finding_ids`: 문자열 배열·중복 거부·`open_finding_ids`와 교집합 거부.
   - 기존 반환 계약(`open_finding_ids` 목록)은 유지해 `validate_review`의 라운드 2 blocker
     검사(`:270-287`)가 그대로 동작하게 한다(R1.7).
3. **통과 기록.** 위 targeted 명령 → exit 0. 이어서 전체 스위트 → exit 0, 실패 0건.
   `record-review` 라운드 2 경로(AC-13)가 계속 성공함을 `test_quality_state.py`의 기존
   테스트로 확인한다.

**실패 처리**: 하위 호환 테스트(AC-12·AC-13)가 깨지면 구현이 prior를 필수화한 것이므로
되돌린다 — D5가 선택 필드를 요구한다.

### T2 — #37: `record-review-unverified`와 재수행 회계 (R2.2~R2.8, R2.12, R2.13, R2.4b)

**대상**: `scripts/quality_state.py`, `tests/test_quality_state.py`

1. **실패 기록.** AC-18~AC-32, AC-52, AC-61~AC-63의 테스트를 먼저 추가한다.
   `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_quality_state.py'`
   → 실패한다(서브커맨드 부재 + `verified` 키 미도입). 실패 메시지를 기록한다.
2. **구현 2a — 초기 상태.** `init`이 만드는 상태 dict(`:195-215` 인근)의
   `"review_validation_retry": None` 바로 뒤에 `"review_unverified_retry": None`을 넣는다.
   `schema_version`은 1 그대로다(Non-goal 6).
3. **구현 2b — `record_review_unverified(state, review_path, artifact_digest)`.**
   `record_review`(`:561`) 바로 뒤에 배치하고, R2.4의 9단계 순서를 그대로 구현한다.
   `record_review`와 공통인 앞 6단계는 헬퍼로 추출하지 말고 **명시적으로 같은 순서로
   작성**한다 — `record_review` 본문 편집을 최소화해 전제 2(#43 블록 동결)의 위험을
   낮춘다.
   - 7단계의 `validate_review` 호출은 `round >= 2`일 때
     `{"open_finding_ids": list(state["open_finding_ids"][artifact])}`를 만들어 넘긴다
     (R2.4b, `record_review:599-607`과 동일).
   - 8단계 트리거: `verdict == "REVISE" and not blockers and any(
     item.get("verified") is False for item in review["evidence"])`.
   - 9단계 회계: 저장 기록이 `artifact`·`round` 모두 일치할 때만 누적. 일치 시
     `attempts == 2`면 `TransitionError("... REVIEWER_UNVERIFIED_PERSISTS ...")`,
     `attempts == 1`이면 digest 바인딩 검사 후 `attempts=2`·`exhausted=True`로 갱신하고
     `discarded_reviews`·`unverified_claims`에 append. 불일치·부재면 새 기록으로 대체
     (`attempts=1`, `exhausted=False`, `artifact_digest=<이번 값>`).
   - 어떤 경로에서도 `rounds[artifact]`를 바꾸지 않고 스테이지를 전이하지 않는다(R2.6).
4. **구현 2c — `record_review` 최소 편집.** `record_review` 안에서 두 곳만 바꾼다.
   - **바인딩 검사**: 라운드 일치 검사와 한도 검사 이후, `validate_review` 호출 이전에
     `review_unverified_retry`가 `artifact`와 `expected_round` 모두 일치하면
     `artifact_digest`가 저장값과 같은지 확인하고 다르면 `StateError`(R2.12·R2.13).
   - **초기화**: 기존 `state["review_validation_retry"] = None` 줄 바로 뒤에
     `state["review_unverified_retry"] = None`을 추가한다(R2.8). 이 줄은
     `recurring = next(...)` 블록보다 **위**에 있으므로 전제 2를 침범하지 않는다.
5. **구현 2d — CLI.** `record-review-unverified` 서브파서를 `record-review`
   (`:1086` 인근) 바로 뒤에 추가한다. 인자는 `--state`, `--review`, `--artifact-digest`
   **셋뿐이며 `--prior`를 추가하지 않는다**(R2.4b·AC-62). `--artifact-digest`는
   `required=True`. dispatch는 `_mutating_result`를 쓴다.
6. **통과 기록 (조건부).** targeted 명령을 실행한다. `verified` 키에 의존하지 않는
   테스트(AC-22·AC-23·AC-25·AC-26·AC-52)는 이 시점에 통과해야 한다. `verified`에
   의존하는 테스트(AC-18~AC-21, AC-24, AC-27~AC-32, AC-61, AC-63)는 **실패가 정상이며**
   그 실패 메시지가 `evidence[0] has unknown field: 'verified'` 계열임을 기록한다. 다른
   원인의 실패는 구현 결함이므로 고친다. 최종 녹색 판정은 T3에서 한다.

**실패 처리**: 전제 2 위반(9줄 블록 변경)이 감지되면 즉시 되돌린다 — T6의 AC-57이
결정적으로 잡는다. 새 서브커맨드가 스스로 터미널 전이를 하도록 구현됐다면 그 역시
되돌린다 — **D4**(`spec.md:929`)가 #43 재생산을 막기 위해 자동 전이를 금지하고, AC-29가
전이 이후 `set-artifact --kind report`가 막히지 않음을 실증한다.

### T3 — #38: `evidence[].verified` 도입 (R3.1~R3.7, R5.1)

**대상**: `schemas/review.schema.json`, `scripts/validate_review.py`,
`tests/fixtures/review-valid-plan.json`, `tests/fixtures/review-high-finding.json`,
`tests/test_validate_review.py`, `tests/test_quality_state.py`

1. **실패 기록.** AC-37~AC-44, AC-51의 테스트를 추가하고 targeted 두 명령을 실행한다 →
   실패. T2에서 남긴 red 테스트도 여전히 실패 중임을 확인한다.
2. **구현 3a — 스키마.** `review.schema.json`의 evidence 항목
   (`:46-66`)에서 `required`를 `["claim", "location", "verified"]`로, `properties`에
   `"verified": {"type": "boolean"}`을 추가한다. `additionalProperties: false`와
   배열의 `uniqueItems: true`는 유지한다. 새 `uniqueItems`나 정규식은 도입하지 않는다
   (R5.3).
3. **구현 3b — 검증기.** `validate_review.py`에서
   - `EVIDENCE_FIELDS = ("claim", "location", "verified")`,
     `EVIDENCE_STRING_FIELDS = ("claim", "location")`으로 상수를 분리한다(`:48`).
   - 필수 키 루프(`:245`)와 unknown 키 루프(`:248`)는 `EVIDENCE_FIELDS`를 쓴다.
   - 비어 있지 않은 문자열 루프(`:251`)는 `EVIDENCE_STRING_FIELDS`로 바꾼다.
   - `verified`는 `isinstance(value, bool)` 검사를 별도로 받는다. 문자열 `"false"`와
     정수 `0`은 거부된다.
   - `verdict == "PASS"` 분기(`:266-268`)에 규칙을 추가한다: `evidence`에
     `verified is False`인 항목이 1개 이상이면 `errors.append(...)`로 미검증 항목 존재를
     명시한다(R3.3). `verdict != "PASS"`에는 적용하지 않는다(R3.4).
   - `evaluate_gate`는 손대지 않는다(Non-goal 4).
4. **구현 3c — fixture·헬퍼 4곳.** `review-valid-plan.json:9-12`,
   `review-high-finding.json:21-24`, `test_validate_review.py:37-42`의 `valid_review()`,
   `test_quality_state.py:75-80`의 `valid_review()`에 `"verified": True/true`를 추가한다.
   `verification-pass.json`은 **손대지 않는다**.
   `test_validate_review.py:384`의 `for field in ("claim", "location")` 루프는
   **그대로 둔다**(R3.5).
5. **통과 기록.** 전체 스위트
   `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_*.py'`
   → exit 0, 실패 0건, 총 개수 201 초과. T2가 남긴 red 테스트가 전부 녹색으로 바뀌었음을
   기록한다.

**실패 처리**: `SchemaDriftTests`가 실패하면 스키마와 `EVIDENCE_FIELDS`가 어긋난
것이므로 두 곳을 맞춘다. `verified` boolean이 "비어 있지 않은 문자열" 오류를 받으면
3b의 상수 분리가 누락된 것이다.

### T4 — 문서 계약: `SKILL.md`와 `quality-reviewer.md` (R1.9·R1.10·R1.11, R2.9·R2.10·R2.11·R2.12, R3.6, R5.6)

**대상**: `SKILL.md`, `dot_claude/agents/quality-reviewer.md`,
`tests/test_content_contracts.py`

1. **실패 기록.** AC-15·16·17·33·34·35·36·45·54의 계약 테스트를 먼저 추가한다.
   `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_content_contracts.py'`
   → 실패.
2. **구현 4a — `SKILL.md` Review invocation contract**(`:250-288` 구간).
   - 라운드 2+ 리뷰어 입력을 "prior open finding IDs"에서 각 open finding의 **ID·심각도·
     설명·증거 위치·요구 해소책 + 오케스트레이터의 해소 주장·해소 증거**로 확장하고,
     해소 확인된 항목은 ID만 `resolved_finding_ids`로 보낸다고 명시한다(R1.9).
   - 그 구조화된 prior를 `reviews[artifact][*].path`의 이전 라운드 리뷰 JSON에서 조립하고
     `open_finding_ids`(blocker만 보존)에 의존하지 않는다고 명시한다(R1.10).
   - 미검증 REVISE 정책 문단을 신설한다: 트리거 3조건(`REVISE`·`blockers == []`·
     `verified == false` evidence 존재), 라운드 비소모, 같은 라운드 재기동, 폐기 리뷰
     2건 상한(무료 재수행 1회), `exhausted`를 본 뒤 보고서 등록 → `BLOCKED`
     `REVIEWER_UNVERIFIED_PERSISTS`, 그 종결이 리뷰어 역량 한계이며 코드·설계 실패가
     아니라는 기록 지시(R2.9), 재수행 입력에 미검증 조건의 증거 경로와 폐기 리뷰의
     비-blocking findings 전문을 담고 라운드 2+에서는 prior의 `open_findings`에도
     포함(R2.11), 재수행 중 아티팩트·워크스페이스를 개정하지 않음(R2.12).
   - frontmatter `version`은 T5에서 바꾼다.
   - **500행 미만을 유지한다**(현재 342행, 여유 157행).
3. **구현 4b — `quality-reviewer.md`.**
   - 라운드 2+에서 전달받은 각 open finding의 해소 여부를 판정해 `evidence`에 기록하고,
     새 finding이 전달받은 항목의 재진술이면 기존 ID를 재사용한다(R1.11).
   - 모든 evidence 항목에 `verified`를 채우고 `false`일 때 이유를 `claim`에 적는다.
     BLOCKED payload의 단일 evidence 항목도 같은 규칙을 따른다(R2.10·R3.6).
   - `:61`의 기존 no-PASS 문장은 `test_content_contracts.py:657-660`이 **문자열 전체를
     고정**하므로, 그 문장을 바꾸려면 같은 테스트의 기대 문자열도 함께 바꾼다. 바꿀
     필요가 없다면 문장을 보존하고 `verified` 규칙을 별도 문장으로 추가한다.
   - frontmatter(`name`·`tools`·`model`·`effort`·`maxTurns: 24`)는 불변이다.
4. **통과 기록.** targeted 명령 → exit 0.
   `wc -l dot_claude/skills/quality-goal/SKILL.md` → 500 미만.

**실패 처리**: SKILL.md가 500행을 넘으면 신설 문단을 압축한다. 기존 계약 테스트가 깨지면
문구를 바꾼 것이므로 원문을 복원하고 추가 문장으로 표현한다.

### T5 — 버전과 유지보수 문서 (R4.1~R4.3, 근거 D11)

**대상**: `SKILL.md` frontmatter, `tests/test_content_contracts.py`,
`docs/quality-goal-maintenance.md`

1. **실패 기록.** `test_content_contracts.py`의 frontmatter 기대값을 `4.0.0`으로 바꾸고
   targeted 명령 실행 → 실패(소스가 아직 `3.0.0`).
2. **구현.** `SKILL.md` frontmatter의 `version: 3.0.0` → `version: 4.0.0`
   (`docs/quality-goal-maintenance.md:54` "게이트 규칙이나 상태 머신 계약 변경: MAJOR").
   frontmatter 키 집합은 불변이다.
3. **구현.** `docs/quality-goal-maintenance.md`의 "추적 중인 후속 작업" 절(`:41-46`)을
   갱신한다 — 현재 목록은 `#36`·`#37`·`#38`·`#39` 4개다.
   - `#37`·`#38` 항목을 제거한다(이 PR이 해소).
   - `#44` 항목은 만들지 않는다(이 PR이 해소).
   - `#43`을 "이 작업이 의도적으로 손대지 않은 인접 결함"으로 명시 추가한다.
   - "권위 목록은 GitHub의 열린 이슈"라는 문장과 조회 명령
     `gh issue list --state open --search 'quality-goal in:title'`를 추가한다.
4. **통과 기록.** targeted 명령 → exit 0. AC-48의 grep 판정을 수행한다.

**실패 처리**: frontmatter 키 집합이 바뀌면 되돌린다 — AC-47이 집합 동등을 요구한다.

### T6 — 통합 검증·변이 검증·범위 확인 (R5.1·R5.4·R5.5, Non-goal 1·7·8·11)

**대상**: 소스 변경 없음. 검증 실행과 산출물 문서만.

1. **전체 스위트.** `find`로 `__pycache__` 제거 후
   `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_*.py'`
   → exit 0, 201 초과, 실패 0건(AC-50).
2. **정적 검사.** `python3 -m json.tool` 스키마, `python3 -m py_compile` 두 스크립트,
   `grep -rn 'output-schema'`에 `review.schema.json` 부재(AC-53),
   `wc -l SKILL.md` < 500(AC-54).
3. **변이 검증 13건 (AC-55).** 목록은 AC-55의 (1)~(13)이 권위다 — Spec의 Test strategy
   절이 적은 "11개"는 라운드 2 개정 전 숫자이며 SPEC-006으로 기록됐다.
   각 항목마다: 해당 구현을 임시 무력화 → 대응 테스트 실패 관찰 → 즉시 복원 →
   `__pycache__` 제거 → 전체 스위트 재확인. 사이클마다
   `git diff --stat`이 무력화 전 상태로 돌아왔음을 확인한다.
4. **범위·불변 확인.** 커밋 후 PR 생성 전에 AC-56(allow-list), AC-57(#43 블록 앵커),
   AC-58(`references/` 무변경 + `ROUND_LIMITS` 값), AC-59(보고서 배포 명령 표)를
   실행한다.
5. **추적표 자기 감사.** AC-60의 파이썬 절차를 `spec.md`에 대해 실행한다.
6. **산출물.** `report.md`를 렌더링하고 터미널 전이 **이전에**
   `set-artifact --kind report`로 등록한다(#43 회피 — SKILL.md가 요구하는 순서).

**실패 처리**: 변이 후 복원했는데 같은 테스트가 계속 실패하면 `__pycache__` 오염이므로
`find ... -name '__pycache__' -prune -exec rm -rf {} +` 후 재실행한다. allow-list 위반이
나오면 해당 파일 변경을 되돌린다.

## Verification commands

실행 순서와 기대 결과. `$SK` = `dot_claude/skills/quality-goal`,
`$BASE` = `5ed7b57387d6a271e8e014091ff8143f488e0d29`.
모든 Python 호출 앞에 `PYTHONDONTWRITEBYTECODE=1`을 붙인다.

| # | 명령 | 기대 |
|---:|---|---|
| 1 | `find $SK -name '__pycache__' -type d -prune -exec rm -rf {} +` | exit 0 |
| 2 | `python3 -m unittest discover -s $SK/tests -p 'test_validate_review.py'` | exit 0, `OK` |
| 3 | `python3 -m unittest discover -s $SK/tests -p 'test_quality_state.py'` | exit 0, `OK` |
| 4 | `python3 -m unittest discover -s $SK/tests -p 'test_content_contracts.py'` | exit 0, `OK` |
| 5 | `python3 -m unittest discover -s $SK/tests -p 'test_*.py'` | exit 0, `Ran N tests` with N > 201, `OK` |
| 6 | `python3 -m json.tool $SK/schemas/review.schema.json` | exit 0 |
| 7 | `python3 -m py_compile $SK/scripts/validate_review.py $SK/scripts/quality_state.py` | exit 0 |
| 8 | `wc -l $SK/SKILL.md` | 500 미만 |
| 9 | `grep -rn 'output-schema' $SK` | `review.schema.json` 미등장 |
| 10 | `grep -n 'ROUND_LIMITS = ' $SK/scripts/quality_state.py` | `{"spec": 3, "plan": 2, "code": 3}` |
| 11 | `git diff $BASE...HEAD -- $SK/references/` | 빈 출력 |
| 12 | `git diff $BASE...HEAD -- $SK/tests/fixtures/verification-pass.json` | 빈 출력 |
| 13 | `git diff --name-only $BASE...HEAD \| grep -vE '^(dot_claude/skills/quality-goal/\|dot_claude/agents/quality-reviewer\.md$\|docs/)'` | grep exit 1 (빈 출력) |
| 14 | `git show $BASE:$SK/scripts/quality_state.py \| sed -n '/^    recurring = next/,/REVIEW_LIMIT_EXHAUSTED/p' > /tmp/base-block.txt; sed -n '/^    recurring = next/,/REVIEW_LIMIT_EXHAUSTED/p' $SK/scripts/quality_state.py > /tmp/head-block.txt; diff /tmp/base-block.txt /tmp/head-block.txt` | exit 0, 양쪽 9줄 |
| 15 | `python3 $SK/scripts/quality_state.py record-review-unverified --help` | `--prior` 미등장 |
| 16 | `grep -n 'chezmoi apply' docs/development/2026-09-03-quality-goal-review-loop/report.md` | 매치 행마다 경로 인자 1개 이상, 인자 없는 행 0건 |

명령 1~10은 구현 직후 오케스트레이터의 독립 검증에서 실행한다. 명령 11~16은 커밋 후
PR 생성 전에 실행한다.

**검증 카테고리 (저장소 실측).** 이 저장소에는 `package.json`·`Makefile`·`justfile`·
`tsconfig.json`·`.github/workflows`가 없다(실측 확인). 타입 체크·린트·빌드는
`not configured`로 기록하며 통과로 기록하지 않는다. `.pre-commit-config.yaml`은 gitleaks
훅 하나뿐이라 린트가 아니다. E2E는 스킬 번들 성격상 해당 없으며, 명령 11~16과 변이 검증
13건이 그 역할을 한다.

## Rollout and rollback

**롤아웃.**

1. Codex 구현 라운드 1회(`gpt-5.6-terra`, effort `high`, `--sandbox workspace-write`,
   `--ephemeral`). 프롬프트는 `.claude/quality-state/<task-id>/` 안에 두고 승인된
   Spec·Plan 절대 경로, allow-list, 정확한 검증 명령, 테스트 우선 요구, 초기 dirty 경로
   제외(없음), 결과 스키마 경로를 담는다.
2. 오케스트레이터 독립 검증: `git status`·`git diff`와 Codex가 보고한 `changed_files`
   대조, 명령 1~10 실행, 워크스페이스 지문 계산, `record-verification`.
3. 코드 리뷰 라운드(최대 3). 남은 2라운드는 bounded fix용으로 예약한다.
4. 사용자 승인 후 커밋 → 브랜치 push → PR 생성. **머지하지 않는다.**
5. **배포는 사용자 결정 사항이다.** 수행한다면 변경 파일 경로를 명시한
   `chezmoi apply <path>...`만 쓴다. 인자 없는 `chezmoi apply`는 금지다. 다른 세션이
   배포본 v3.0.0을 실행 중일 수 있으므로, 배포 시점부터 그 세션의 다음 리뷰 라운드에 새
   계약이 적용된다는 점을 보고서에 남긴다.

**롤백 트리거와 조치.**

| 트리거 | 조치 |
|---|---|
| 전체 스위트가 exit 0을 못 냄 | 원인이 fixture 형태면 T3-3c로 복귀. 계약 모순이면 해당 태스크 변경을 `git checkout -- <path>`로 되돌리고 Spec 개정 필요 여부를 판단 |
| allow-list 위반(명령 13) | 위반 파일을 `git checkout $BASE -- <path>`로 복원하고 재검증 |
| #43 블록 변경(명령 14) | `git show $BASE:...`에서 해당 9줄을 복원 |
| `references/` 변경(명령 11) | `git checkout $BASE -- $SK/references/` |
| 커밋 후 결함 발견 | `git revert <commit>`. 브랜치 폐기가 필요하면 `git branch -D 44-fix/quality-goal-review-loop` |
| 배포 후 결함 발견 | `git revert` 후 **같은 파일 경로를 지정한** `chezmoi apply <path>...`를 다시 실행 |
| Codex 모델 거부·미가용 | `BLOCKED_MODEL_UNAVAILABLE`. 현재 스테이지 유지, 사용자에게 대체 모델 승인 요청. 무단 대체 금지 |

**호환성.** 상태 파일 `schema_version`은 1 그대로다. 기존 상태 파일에
`review_unverified_retry`가 없어도 `state.get(...)` 관용 읽기로 동작한다. 파괴적 작업·
데이터 마이그레이션·외부 상태 변경은 없다.

**모니터링.** 이 변경에는 런타임 관측 대상이 없다. 관측 지점은 결정적 명령의 종료 코드와
`.claude/quality-state/<task-id>/state.json`뿐이다.

## Acceptance-criteria traceability

명령 축약: `$SUITE` = `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s $SK/tests -p 'test_*.py'`,
`$TVR` = 같은 형식에 `-p 'test_validate_review.py'`, `$TQS` = `-p 'test_quality_state.py'`,
`$TCC` = `-p 'test_content_contracts.py'`.

| Criterion | Task | Verification command | Expected outcome |
|---|---|---|---|
| AC-1 | T1 | `$TVR` | 확장 prior + 라운드 2 리뷰 검증이 exit 0, `{"valid":true,"errors":[]}` |
| AC-2 | T1 | `$TVR` | 7필드 각각 제거 시 exit 2, errors에 필드명 (subTest 7회) |
| AC-3 | T1 | `$TVR` | `severity="Trivial"` → exit 2 |
| AC-4 | T1 | `$TVR` | `open_findings[0].extra` → exit 2, errors에 `'extra'` |
| AC-5 | T1 | `$TVR` | `open_findings` id 중복 → exit 2 |
| AC-6 | T1 | `$TVR` | 커버리지 위반 → exit 2 |
| AC-7 | T1 | `$TVR` | 상위집합(blocker+Medium) → exit 0 |
| AC-8 | T1 | `$TVR` | resolved ∩ open ≠ ∅ → exit 2 |
| AC-9 | T1 | `$TVR` | resolved 중복 → exit 2, 원소 정수 → exit 2 |
| AC-10 | T1 | `$TVR` | 문자열 5필드 각각 `""`·`"   "` → exit 2 (subTest 10회) |
| AC-11 | T1 | `$TVR` | `resolution_*` null → exit 0, 정수 1 → exit 2 |
| AC-12 | T1 | `$TVR` | `{"open_finding_ids": []}`만 담은 prior → exit 0 |
| AC-13 | T1 | `$TQS` | `record-review` 라운드 2 경로 exit 0 |
| AC-14 | T1 | `$TVR` | prior 최상위 `open_finding` 키 → exit 2, errors에 키 이름 |
| AC-15 | T4 | `$TCC` | SKILL.md가 라운드 2+ 입력으로 설명·증거 위치·요구 해소책·해소 주장을 지시하고 해소분은 ID만 보낸다고 명시 |
| AC-16 | T4 | `$TCC` | SKILL.md가 prior를 `reviews[artifact][*].path`에서 조립하라고 지시 |
| AC-17 | T4 | `$TCC` | quality-reviewer.md가 라운드 2+ 해소 판정과 ID 재사용을 규정 |
| AC-18 | T2 | `$TQS` | 1번째 호출 exit 0, `attempts=1`·`exhausted=false`·`artifact_digest=D`, `rounds` 불변 |
| AC-19 | T2 | `$TQS` | blockers 비어 있지 않음 → exit 2 |
| AC-20 | T2 | `$TQS` | 모든 evidence `verified=true` → exit 2 |
| AC-21 | T2 | `$TQS` | verdict PASS/BLOCKED → exit 2 |
| AC-22 | T2 | `$TQS` | 스테이지 불일치 → exit 2 |
| AC-23 | T2 | `$TQS` | 라운드 불일치 → exit 2; 라운드 불일치 ∧ 한도 초과 → **exit 2** |
| AC-24 | T2 | `$TQS` | 스키마 위반 → exit 2, 상태 바이트 동일 |
| AC-25 | T2 | `$TQS` | `--artifact-digest` 누락 → argparse exit 2; spec digest 불일치 → exit 2, 상태 불변 |
| AC-26 | T2 | `$TQS` | `rounds==limit` ∧ `round==limit+1` → exit 3, 상태 불변 |
| AC-27 | T2 | `$TQS` | 2번째 호출 exit 0, `attempts=2`·`exhausted=true`·`discarded_reviews=[R,R2]`, `rounds` 불변 |
| AC-28 | T2 | `$TQS` | 3번째 호출 exit 3, stderr에 `REVIEWER_UNVERIFIED_PERSISTS`, 상태 바이트 동일 |
| AC-29 | T2 | `$TQS` | 이후 `set-artifact --kind report` exit 0, `transition --to BLOCKED --reason REVIEWER_UNVERIFIED_PERSISTS:spec` exit 0 |
| AC-30 | T2 | `$TQS` | 동일 digest `record-review` exit 0, `review_unverified_retry` null |
| AC-31 | T2 | `$TQS` | 다른 digest `record-review` exit 2, `rounds` 불변; 2번째 unverified도 다른 digest면 exit 2 |
| AC-32 | T2 | `$TQS` | spec 파일 개정 후 digest 재계산 제시 → `record-review` exit 2 |
| AC-33 | T4 | `$TCC` | SKILL.md가 트리거 3조건·라운드 비소모·같은 라운드 재기동·폐기 2건 상한·`exhausted` 후 BLOCKED 경로를 명시 |
| AC-34 | T4 | `$TCC` | SKILL.md가 그 BLOCKED가 리뷰어 역량 한계임을 기록하도록 지시 |
| AC-35 | T4 | `$TCC` | SKILL.md가 재수행 입력의 증거 경로·비-blocking findings 승계·무개정을 명시 |
| AC-36 | T4 | `$TCC` | quality-reviewer.md가 미검증을 `verified: false`로 표시하도록 규정 |
| AC-37 | T3 | `$TVR` | 스키마 evidence `required`가 `{claim,location,verified}`, `verified.type=="boolean"`, `additionalProperties` false |
| AC-38 | T3 | `$TVR` | `verified` 누락 → exit 2, errors에 `verified` |
| AC-39 | T3 | `$TVR` | `verified="false"` 또는 `0` → exit 2 |
| AC-40 | T3 | `$TVR` | PASS ∧ `verified:false` → exit 2, errors가 미검증 존재를 명시 |
| AC-41 | T3 | `$TVR` | REVISE ∧ `verified:false` → exit 0 |
| AC-42 | T3 | `$TVR` | `verified:true` 통과, 같은 항목 `claim=""` → exit 2 |
| AC-43 | T3 | `$TVR` | `SchemaDriftTests` 통과 |
| AC-44 | T3 | `$TQS` | PASS+미검증으로 `record-review` → exit 2, `rounds` 불변 |
| AC-45 | T4 | `$TCC` | quality-reviewer.md가 모든 evidence에 `verified` 기입·`false` 사유·BLOCKED payload 동일 적용을 규정 |
| AC-46 | T5 | `grep '^version:' $SK/SKILL.md` | `version: 4.0.0` |
| AC-47 | T5 | `$TCC` | frontmatter 테스트 통과, 키 집합 7개 불변 |
| AC-48 | T5 | `grep -n '#3[6-9]\|#4[34]\|gh issue list' docs/quality-goal-maintenance.md` | `#37`·`#38`·`#44` 부재, `#43` 존재, 권위 문장과 조회 명령 존재 |
| AC-49 | T6 | `ls docs/development/2026-09-03-quality-goal-review-loop/` | `spec.md`·`plan.md`·`report.md` 존재 |
| AC-50 | T6 | `$SUITE` | exit 0, `Ran N tests` with N > 201, 실패 0건 |
| AC-51 | T3 | 파이썬 단정 + `git diff $BASE...HEAD -- $SK/tests/fixtures/verification-pass.json` | 4곳의 evidence 객체가 모두 `claim`·`location`·`verified` 보유; verification-pass diff 빈 출력 |
| AC-52 | T2 | `$TQS` | 상태 키 집합에 `review_unverified_retry` 포함, `init`이 null로 생성 |
| AC-53 | T6 | `grep -rn 'output-schema' $SK` | `review.schema.json` 미등장 |
| AC-54 | T4 | `wc -l $SK/SKILL.md` | 500 미만 |
| AC-55 | T6 | 변이 13회 × (무력화 → `$SUITE` → 복원 → `find __pycache__` 제거 → `$SUITE`) | 무력화 시 대응 테스트 실패, 복원 시 exit 0 |
| AC-56 | T6 | 검증 명령 13 | grep exit 1 (빈 출력) |
| AC-57 | T6 | 검증 명령 14 | `diff` exit 0, 양쪽 9줄 |
| AC-58 | T6 | 검증 명령 11 + 10 | `references/` diff 빈 출력, `ROUND_LIMITS`가 `{"spec": 3, "plan": 2, "code": 3}` |
| AC-59 | T6 | 검증 명령 16 | `chezmoi apply` 행이 모두 경로 인자 보유, 인자 없는 행 0건(0매치도 통과) |
| AC-60 | T6 | AC-60의 파이썬 절차를 `spec.md`에 실행 | 요구사항 ID 집합 == 추적표 행 집합, 각 행이 실재 AC를 1개 이상 인용 |
| AC-61 | T2 | `$TQS` | spec 라운드 1 기록 후 라운드 2 미검증 REVISE → exit 0, `rounds.spec` 1 유지, `--prior` 없이 성공 |
| AC-62 | T2 | 검증 명령 15 + `$TQS` | `--help`에 `--prior` 부재, `--prior` 전달 시 argparse exit 2 |
| AC-63 | T2 | `$TQS` | (a) 낡은 기록 → 대체·exit 0, (b) 다른 digest `record-review` → exit 0, (c) 이후 `review_unverified_retry` null |
