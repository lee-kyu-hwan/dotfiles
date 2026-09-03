# Quality Goal Specification

- Task ID: 20260903T092537Z-44-37-38-quality-goal-리뷰-루프-결함-3건-수정-라운드-33f2fb89
- Mode: standard
- Status: SPEC_REVIEW (round 2)
- Created: 2026-09-03T09:25:37Z
- Updated: 2026-09-03T10:05:00Z
- Source goal: #44 #37 #38 quality-goal 리뷰 루프 결함 3건 수정 — 라운드 2+ prior findings 전문 전달, 미검증 사유 REVISE의 라운드 소모 방지, no-PASS-when-unverified 결정적 게이트 승격
- Base revision: `5ed7b57387d6a271e8e014091ff8143f488e0d29` (상태 파일의 `base_revision`)

이 Spec은 선행 실행(`docs/development/2026-08-27-quality-goal-review-loop/spec.md`, 952행,
`NEEDS_REDESIGN`)을 초안으로 재사용한다. 그 실행이 다룬 R6(spec 라운드 한도 2→3)과
R7(루브릭 라운드 수 단언 강화)은 **이후 v3.0.0으로 이미 출시됐으므로 이번 범위에서
제외한다**(실측: `scripts/quality_state.py:69`가 `{"spec": 3, "plan": 2, "code": 3}`,
`references/spec-rubric.md:33`이 `After round 3`, `tests/test_content_contracts.py`의 세
루브릭 단언이 `re.findall(r"after round (\d+) without a passing gate", lower)` 형태).
선행 실행의 미해소 findings 중 R6에 종속했던 SPEC-012·SPEC-013·SPEC-015는 함께 소멸했고,
남은 SPEC-006·SPEC-011은 이 Spec이 D3·D4에서 선반영해 해소한다.

## Problem and context

`quality-goal` 스킬 v3.0.0의 리뷰 루프에 서로 맞물린 결함 3건이 실전 사용에서 드러났다.
세 결함은 모두 **"리뷰어가 무엇을 검증했는지를 시스템이 알 수 없다"**는 하나의 공백에서
파생한다.

**#44 — 라운드 2+ 리뷰 계약이 finding ID만 전달한다.**
`SKILL.md:256`은 라운드 2 이상에서 리뷰어에게 보낼 입력을 "prior open finding IDs"로
규정한다. 설명 원문·증거 위치·오케스트레이터가 취한 조치가 전달되지 않으므로 리뷰어는
이전 finding이 해소됐는지 판정할 수 없다. 실측(2026-08-27, 실행
`20260827T080329Z-28-35-create-worktree-…`): Spec 라운드 2 리뷰어가
SPEC-005·006·007·008·010을 검증하지 못했고, 자신의 새 findings가 이전 항목의 재진술인지
배제할 수 없다고 기록했다. 근거는 이슈 #44 본문이 인용하는
`docs/development/2026-08-27-create-worktree-pr-session/report.md`의 "프로세스 관찰" 절이며,
그 문서는 해당 실행이 `NEEDS_REDESIGN`으로 끝나 이 저장소에 커밋되지 않았다.

더 나쁜 것은 **오케스트레이터가 보낼 수 있는 정보 자체가 blocker로 한정된다**는 점이다.
`quality_state.py:649`가 `open_finding_ids[artifact] = list(blockers)`로 blocker만
보존한다. 위 실측에서 검증되지 못한 5건은 모두 Medium·Low여서 애초에 blocker가 아니었고
따라서 상태에서 완전히 사라졌다.

**#37 — 미검증 사유 REVISE가 리뷰 라운드를 소모한다.**
`dot_claude/agents/quality-reviewer.md:61`은 "적용 가능한 게이트 조건이나 루브릭 항목을
검증하지 못했다면 verdict는 PASS가 아니어야 한다"를 요구한다. 그 규칙 자체는 필요했다 —
없으면 턴 소진된 리뷰가 PASS로 게이트를 통과한다(fail-open). 그런데 **오케스트레이터 측
처리가 없다.** `SKILL.md:283-288`은 malformed 출력과 리뷰어 기동 실패만 다룬다. 실체가
결함이 아니라 "X를 검증하지 못했다"뿐인 well-formed REVISE는 스키마 검증을 통과해
`record-review`로 기록되고(`quality_state.py:645-649`) 라운드를 1개 소모한다. 반복되면
`ROUND_LIMITS`(`quality_state.py:69`)에 걸려 `NEEDS_REDESIGN`으로 종결되고, **리뷰어 역량
실패가 코드·설계 실패로 귀속된다.**

**#38 — no-PASS-when-unverified가 지시문 준수에만 의존한다.**
`evaluate_gate`(`validate_review.py:292-334`)는 `verdict`·`blockers`·severity·checks만 읽고
`evidence` 배열을 전혀 보지 않는다. `review.schema.json`의 evidence 항목은
`{claim, location}`뿐이라(`review.schema.json:46-66`) "이건 검증 못 했다"를 기계가 알 수단이 없다. code
아티팩트는 점수 임계도 없으므로(`validate_review.py:309` — spec/plan만 임계 적용) 게이트의
실질은 리뷰어 verdict + 오케스트레이터 자기 체크 4개가 전부다. 리뷰어가 미검증 조건을
"적용되지 않음"으로 재분류하면 검증과 게이트를 모두 통과한다.

**이 결함들은 계속 발현하고 있다.** 선행 실행(2026-08-27)의 라운드 1·2 리뷰어 모두
미검증 항목을 `claim` 문자열 안의 산문 `"NOT VERIFIED:"`로만 표시했다 — 구조화된 필드가
없어서다(#38의 직접 실증). 같은 실행에서 라운드 2 prior를 계약대로 보내면 라운드 1의
10건 중 blocker 1건의 ID만 전달됐을 것이므로, 오케스트레이터가 구조화된 prior를 파일로
만들어 프롬프트에 직접 넣는 우회를 썼고 그 결과 라운드 2 리뷰어가 10건 중 9건의 해소를
개별 증거와 함께 확인했다(#44 수정의 효과 실증). **이번 실행도 같은 우회를 유지한다** —
수정이 배포되기 전까지 배포본 v3.0.0의 계약은 그대로이기 때문이다.

세 결함은 상호작용한다. #44가 중복 findings를 만들고, #37이 그 중복으로 라운드를
소모하며, #38이 그 어느 것도 결정적으로 잡지 못한다.

## Goals

1. 라운드 2 이상의 리뷰어가 이전 라운드 open findings의 **설명 원문·증거 위치·요구
   해소책과 오케스트레이터의 해소 주장**을 받아 각 항목의 해소 여부를 판정할 수 있다.
   blocker가 아닌 open finding도 전달 가능하다.
2. 실체가 결함이 아니라 미검증 사유뿐인 REVISE가 리뷰 라운드를 소모하지 않고, 범위를
   좁힌 재수행으로 처리되며, 반복 시 리뷰어 역량 한계를 명시한 `BLOCKED`로 종결된다.
   이 경로가 남용될 수 없도록 결정적으로 강제되고, 폐기된 리뷰의 advisory findings와
   두 번의 시도 기록이 모두 상태 파일에 남는다.
3. "미검증 조건이 있으면 PASS 금지"가 지시문이 아니라 `validate_review.py`의 결정적
   규칙이 된다. 미검증 표시가 스키마에 구조화되어 기계가 읽을 수 있다.
4. 위 변경이 스킬 번들의 게이트 규칙과 상태 머신 계약을 바꾸므로 SemVer MAJOR
   (3.0.0 → 4.0.0)로 표기되고, 기존 201개 결정적 테스트가 계속 통과하며 신규 회귀
   테스트가 각 변경의 비공허성을 증명한다.

## Non-goals

1. **#43(record-review의 자동 터미널 전이)은 고치지 않는다.** 같은 파일
   (`quality_state.py`)을 만지지만 `record_review`의 자동 전이 블록
   (`recurring = next(...)`부터 `REVIEW_LIMIT_EXHAUSTED`까지)은 base revision과 바이트
   동일해야 한다(AC-57). 다만 이 작업이 새로 추가하는 실패 경로는 같은 결함을 재생산하지
   않아야 한다(D3).
2. **인자 없는 `chezmoi apply`를 실행하지 않는다.** 다른 세션이 배포본
   `~/.claude/skills/quality-goal`을 실행 중일 수 있다. 배포는 변경 파일 경로를 지정한
   `chezmoi apply <path>...`만 허용하며, 사용자 승인 후 최종 단계에서만 수행한다.
3. **커밋 후 머지하지 않는다.** PR 생성까지만 수행하고 URL을 보고한다.
4. **`evaluate_gate`에 `unverified_evidence_present` 게이트 사유를 추가하지 않는다**
   (D2 — 검증 단계에서 이미 거부되므로 도달 불가 코드가 된다).
5. **리뷰어 프롬프트 전달 내용 자체의 기계 검증은 하지 않는다.** 서브에이전트 프롬프트는
   외부에서 검사할 수 없다. 결정적 강제는 `--prior` 파일 형태와 검증 규칙에 둔다(D5).
6. **상태 파일 `schema_version`을 올리지 않는다.** 추가되는 상태 키는 관용적 읽기
   (`state.get(...)`)로 접근하므로 기존 상태 파일이 계속 로드된다.
7. **`ROUND_LIMITS` 값을 바꾸지 않는다.** spec 3·plan 2·code 3은 불변이다. plan 한도
   상향은 별건(#60 OPEN)이다.
8. **루브릭 파일을 변경하지 않는다.** `spec-rubric.md`·`plan-rubric.md`·`code-rubric.md`
   는 전부 불변이다.
9. **`SKILL.md`의 라운드 수 서술과 코드의 드리프트 검출 강화(#57)는 넣지 않는다.**
   이번 실행 시작 시 서술과 `ROUND_LIMITS`가 일치함을 확인했으므로 조치 대상이 없다.
10. **#49·#50·#51·#55·#58·#59·#61은 범위 밖이다.** 이 작업은 #44·#37·#38만 다룬다.
11. **변경 파일 allow-list.** 변경은 `dot_claude/skills/quality-goal/`,
    `dot_claude/agents/quality-reviewer.md`, `docs/` **세 경로 아래로만** 허용한다.
    `.gitignore`, 다른 스킬, chezmoi 소스의 다른 파일은 건드리지 않는다.
12. **리뷰어에게 오케스트레이터 checks JSON을 공급하지 않는다**(D10).
13. **`review.schema.json`에 `$id`·`version` 필드를 도입하지 않는다.** 이 스키마는 로컬
    `validate_review.py` 전용이고 소비자가 번들 내부뿐이라 별도 스키마 버전 축이 필요
    없다. 번들 SemVer(R4.1)가 그 역할을 한다.

## Requirements

### R1. #44 — `--prior` 입력 확장 (구조화된 이전 라운드 findings)

- **R1.1** `validate_review.py`의 prior 입력이 기존 필수 필드 `open_finding_ids`
  (문자열 배열) 외에 선택 필드 `open_findings`(객체 배열)와
  `resolved_finding_ids`(문자열 배열)를 받는다.
- **R1.2** `open_findings`의 각 항목은 다음 7개 필드를 모두 가진다:
  `id`, `severity`, `description`, `evidence_location`, `required_resolution`,
  `resolution_claim`, `resolution_evidence`.
  - 앞 5개는 **비어 있지 않은 문자열**이어야 한다. 공백만인 문자열도 거부한다.
  - `severity`는 `Critical|High|Medium|Low` 중 하나여야 한다.
  - `resolution_claim`과 `resolution_evidence`는 **문자열 또는 `null`**이다. `null`은
    "해소 주장이 없다"는 유효한 값이다. 그 밖의 타입(정수·불리언·배열·객체)은 거부한다.
- **R1.3** `open_findings`의 각 항목에 위 7개 외의 키가 있으면 검증 오류다(기존
  payload·finding·evidence의 unknown-key 처리와 동일한 fail-closed 방향).
- **R1.4** `open_findings`의 `id`는 중복될 수 없다.
- **R1.5** `open_findings`가 존재하면 `open_finding_ids`의 모든 ID가 `open_findings`에
  나타나야 한다(커버리지). **역방향은 요구하지 않는다** — blocker가 아닌 open
  finding(Medium·Low)도 전달하는 것이 이 요구사항의 목적이므로 `open_findings`는
  상위집합일 수 있다(D6).
- **R1.6** `resolved_finding_ids`가 존재하면 **문자열 배열**이어야 하고, **중복이 없어야
  하며**, `open_finding_ids`와 **교집합이 없어야 한다**.
- **R1.7** 위 확장은 하위 호환이어야 한다. `{"open_finding_ids": []}`만 담은 기존 형태와,
  `record_review`가 내부적으로 만드는 `{"open_finding_ids": [...]}`
  (`quality_state.py:607`)가 계속 유효해야 한다.
- **R1.8** prior 객체의 **최상위 unknown 키는 검증 오류**다. 현재
  `_prior_open_finding_ids`(`validate_review.py:70-93`)는 unknown-key 검사를 하지 않으므로
  `open_finding`·`openFindings` 같은 오타가 구조화된 prior 검증을 **조용히 전부
  무력화**하고 검증은 valid를 반환한다 — 리뷰어는 ID만 받는 #44 상태로 되돌아간다.
  오류 메시지는 문제된 키 이름을 포함한다.
- **R1.9** `SKILL.md`의 Review invocation contract가 라운드 2 이상에서 리뷰어에게 보내는
  입력을 "prior open finding IDs"에서 **"각 open finding의 ID·심각도·설명·증거 위치·요구
  해소책과 오케스트레이터의 해소 주장·해소 증거"**로 확장한다. 해소가 확인된 항목은 ID만
  `resolved_finding_ids`로 전달한다(리뷰어 컨텍스트 비용 절충 — 이슈 #44 "수정 방향").
- **R1.10** `SKILL.md`가 그 구조화된 prior의 출처를 지시한다: 상태의
  `reviews[artifact][*].path`에 기록된 이전 라운드 리뷰 JSON에서 findings를 읽고, 거기에
  오케스트레이터 자신의 해소 주장을 더해 조립한다. blocker만 남기는 `open_finding_ids`에
  의존하지 않는다.
- **R1.11** `quality-reviewer.md`가 라운드 2 이상에서 전달받은 각 open finding의 해소
  여부를 판정하고 그 판정을 `evidence`에 기록하도록 계약을 갱신한다. 새 finding이
  전달받은 open finding의 재진술이면 기존 ID를 재사용하고 새 ID를 만들지 않는다.

### R2. #37 — 미검증 사유 REVISE의 라운드 비소모 재수행

- **R2.1** `SKILL.md`가 **미검증 사유 REVISE**를 기계 판정 가능한 조건으로 정의한다:
  `verdict == "REVISE"` **이고** `blockers == []` **이고** `evidence`에
  `verified == false` 항목이 1개 이상 있다.
- **R2.2** 그 조건을 만족하는 리뷰는 `record-review`로 기록하지 않는다. 대신
  `quality_state.py`의 신규 서브커맨드 `record-review-unverified`로 시도를 기록하고,
  **같은 라운드 번호로** 새 quality-reviewer를 기동한다. 라운드는 소모되지 않는다.
  재수행 입력은 기존 계약 입력에 다음 두 가지를 추가한 것이다:
  - 미검증으로 표시된 각 조건을 해소할 **증거 경로**(이슈 #37이 요구하는 "범위를 좁힌 입력");
  - 폐기되는 리뷰의 **비-blocking findings 전문**(R2.11).
- **R2.3** `record-review-unverified`는 전달된 리뷰가 R2.1 조건을 실제로 만족하는지 스스로
  검증한다. 만족하지 않으면 `StateError`로 거부한다(exit 2). 실체 있는 REVISE를 무료
  재수행으로 세탁할 수 없어야 한다.
- **R2.4** `record-review-unverified`의 전제 조건을 **명시적으로 열거하고 평가 순서를
  고정한다.** 순서는 `record_review`(`quality_state.py:561-664`)와 동일하게 맞춰, 같은
  입력이 두 서브커맨드에서 다른 종료 코드를 내지 않게 한다. 먼저 만나는 실패가 종료 코드를
  결정한다:
  1. `--artifact-digest`가 소문자 SHA-256 hexdigest 형식이다. **필수 인자다.** 위반 시
     `StateError`(exit 2).
  2. `--review` 경로가 JSON 객체로 로드된다. 위반 시 `StateError`(exit 2).
  3. 리뷰의 `artifact`가 알려진 값이고 그에 대응하는 리뷰 스테이지가 현재 스테이지다.
     위반 시 `StateError`(exit 2).
  4. spec·plan 아티팩트인 경우, 등록된 아티팩트 파일의 현재 digest가 `--artifact-digest`와
     일치한다(`record_review`의 `quality_state.py:580-586`과 동일한 교차 검사). code
     아티팩트는 `record_review`와 같이 이 비교를 하지 않는다(공급값이 워크스페이스
     지문이므로). 위반 시 `StateError`(exit 2).
  5. `round == rounds[artifact] + 1`(아직 기록되지 않은 라운드). 위반 시
     `StateError`(exit 2). **라운드 일치 검사가 한도 검사보다 먼저다** —
     `record_review`의 `quality_state.py:591-598`과 같은 순서이므로, 라운드가 불일치이면서 동시에 한도를
     초과하는 입력은 exit 2를 낸다.
  6. `round`가 `ROUND_LIMITS[artifact]`를 초과하면 `TransitionError`(exit 3)다.
  7. 리뷰 payload가 `validate_review` 스키마 검증을 통과한다. 위반 시 `StateError`
     (exit 2) — malformed 응답은 무료 재수행이 아니라 기존 `record-review-error` 경로로
     가야 한다.
  8. R2.1의 트리거 조건을 만족한다(R2.3). 위반 시 `StateError`(exit 2).
  9. R2.5의 재수행 회계와 R2.12의 digest 바인딩을 통과한다.
- **R2.4b** **`validate_review` 호출 시 prior를 내부적으로 조립한다.**
  `validate_review`는 `round >= 2`이고 prior가 `None`이면 무조건
  `"prior is required for round >= 2"` 오류를 낸다(`validate_review.py:270-273`). 따라서
  R2.4-7의 검증 호출은 `record_review`(`quality_state.py:599-607`)와 **동일하게**
  `round >= 2`일 때 상태에서 `{"open_finding_ids": list(state["open_finding_ids"][artifact])}`
  를 만들어 넘긴다. **`record-review-unverified`에 `--prior` 인자를 추가하지 않는다** —
  구조화된 prior는 리뷰어 프롬프트로 가는 입력이지 상태 기록 경로의 입력이 아니며
  (D5), CLI에 인자를 늘리면 `record_review`와 검증 입력이 갈라진다. 이 규칙이 없으면
  라운드 2 이상의 미검증 REVISE가 전부 exit 2로 거부되어 #37이 만들려는 경로 자체가
  도달 불가가 된다.
- **R2.5** **재수행 상한은 (아티팩트, 라운드)당 폐기 리뷰 2건이다** — 즉 무료 재수행은
  정확히 1회다.
  - 1번째 호출: exit 0, `attempts = 1`, `exhausted = false`. 오케스트레이터는 같은
    라운드로 리뷰어를 재기동한다.
  - 2번째 호출: **exit 0**, `attempts = 2`, `exhausted = true`, 두 번째 폐기 리뷰 경로가
    `discarded_reviews`에 append된다. 재기동하지 않는다.
  - 3번째 호출: `TransitionError`(exit 3)로 거부되고 오류 메시지가
    `REVIEWER_UNVERIFIED_PERSISTS`를 명시한다. 상태는 불변이다.
  2번째 호출을 성공으로 두는 이유는 D3에 기록한다 — 실패로 두면 `_mutating_result`가
  예외 경로에서 상태를 저장하지 않아(`quality_state.py:1144-1156`, `ApprovalMismatchError`
  만 예외적으로 저장) 두 번째 시도가 상태에 남지 않는다.
- **R2.6** `record-review-unverified`는 **스스로 터미널 상태로 전이하지 않는다.**
  `exhausted == true`를 본 오케스트레이터가 보고서를 렌더링·등록한 뒤 명시적으로
  `transition --to BLOCKED --reason REVIEWER_UNVERIFIED_PERSISTS:<artifact>`를 호출한다.
- **R2.7** 시도 기록은 상태의 신규 키 `review_unverified_retry`에 저장한다:
  `{artifact, round, attempts, exhausted, artifact_digest, unverified_claims,
  discarded_reviews}`.
  - `attempts`는 정수 1 또는 2다. `exhausted`는 불리언이며 `attempts >= 2`와 동치다.
  - `artifact_digest`는 첫 호출이 수용한 digest다(R2.12).
  - `unverified_claims`는 폐기된 각 리뷰에서 `verified == false`였던 evidence 항목의
    `claim` 문자열 목록이며 시도마다 append된다.
  - `discarded_reviews`는 폐기된 리뷰 JSON의 **경로 목록**이며 시도마다 append된다.
    `record-review`를 건너뛰므로 `reviews[artifact]`에 항목이 추가되지 않아, 이 필드가
    없으면 `REVIEWER_UNVERIFIED_PERSISTS` 종결 시 상태 파일이 폐기된 리뷰를 전혀 가리키지
    못한다 — `SKILL.md`가 상태 파일을 권위 기록으로 선언하는 것과 모순된다.
- **R2.8** `review_unverified_retry`는 `record_review`가 해당 아티팩트의 라운드를 정상
  기록할 때 `None`으로 초기화된다(`review_validation_retry`와 동일한 수명).
- **R2.9** `SKILL.md`가 R2.1~R2.6의 정책과 `BLOCKED` 종결 사유를 명시하고, 그 종결이
  코드·설계 실패가 아니라 리뷰어 역량 한계임을 기록하도록 지시한다.
- **R2.10** `quality-reviewer.md`가 미검증 조건을 알릴 때 `verified == false` evidence
  항목을 사용하도록 계약을 갱신한다(R3와 연결).
- **R2.11** 폐기되는 리뷰의 **비-blocking findings는 유실되지 않는다.** R2.1의 트리거가
  `blockers == []`이므로 advisory findings(Medium·Low)만으로 정당화된 REVISE도 이 경로를
  탄다. `SKILL.md`가 재수행 입력에 그 findings 전문을 담도록 지시하고, 라운드 2 이상이면
  추가로 prior의 `open_findings`에 포함하도록 지시한다(R1.5의 상위집합 허용이 이를
  가능하게 한다).
- **R2.12** **재수행 중 아티팩트·워크스페이스 개정을 결정적으로 차단한다.** 첫
  `record-review-unverified` 호출이 수용한 `--artifact-digest`를
  `review_unverified_retry.artifact_digest`에 저장하고, **같은 (아티팩트, 라운드)에 대한
  이후의 `record-review-unverified`와 `record-review`가 동일한 digest를 제시하지 않으면
  거부한다**(`StateError`, exit 2). 그 결과 재수행 중 개정은 어느 쪽으로도 통과하지
  못한다 — 개정 후 옛 digest를 제시하면 spec·plan은 R2.4-4의 현재-파일 교차 검사에
  걸리고, 새 digest를 제시하면 이 바인딩 검사에 걸린다. code 아티팩트는 digest가
  워크스페이스 지문이므로 이 바인딩만으로 개정이 차단된다. 개정이 정당하면 다음 라운드로
  넘어가야 하며, 그 경로는 `record-review`가 정상 라운드를 기록한 뒤 열린다(R2.8).
- **R2.13** **`review_unverified_retry`의 일치 술어와 불일치 시 동작을 고정한다.**
  저장된 기록이 들어오는 호출과 "같은 시도"인지는 **`artifact`와 `round`가 모두 같을
  때에만** 성립한다(형제 함수 `record_review_validation_failure`의
  `quality_state.py:687-691` 가드와 동일한 술어).
  - **일치할 때**: `attempts`를 누적하고(R2.5), R2.12의 digest 바인딩을 적용한다.
  - **불일치할 때**(`artifact`가 다르거나 `round`가 다름): 저장된 기록은 **낡은 것으로
    보고 통째로 대체한다** — 새 `{artifact, round, attempts: 1, exhausted: false,
    artifact_digest: <이번 호출의 digest>, unverified_claims: [...],
    discarded_reviews: [...]}`로 초기화하고 exit 0으로 성공한다. 오류가 아니다.
  - **`record_review`의 R2.12 바인딩 검사도 같은 술어를 쓴다**: 저장된 기록의
    `artifact`가 이번 리뷰의 artifact와 같고 `round`가 `rounds[artifact] + 1`과 같을
    때에만 digest 일치를 요구하고, 그 밖에는 검사를 건너뛴다. 이 조항이 없으면 이전
    라운드에 남은 낡은 기록이 정당한 `record-review`를 영구히 차단한다.
  - `record_review` 성공 시의 `None` 초기화(R2.8)는 이 술어와 무관하게 항상 수행한다 —
    라운드가 기록되면 그 아티팩트의 재수행 회계는 어느 라운드의 것이든 의미를 잃는다.

### R3. #38 — no-PASS-when-unverified의 결정적 승격

- **R3.1** `review.schema.json`의 evidence 항목에 `verified`(boolean)를 추가하고 **필수
  필드**로 만든다. `additionalProperties: false`는 유지한다.
- **R3.2** `validate_review.py`의 `EVIDENCE_FIELDS`에 `"verified"`를 추가한다. 단 현재
  `EVIDENCE_FIELDS`는 세 개의 루프를 동시에 구동한다 — 필수 키 검사(`:245`), unknown 키
  검사(`:248`), **비어 있지 않은 문자열 검사**(`:251`). 세 번째 루프를 그대로 두면 boolean
  `verified`가 항상 검증 오류가 된다. 따라서:
  - 필수 키 검사와 unknown 키 검사는 `EVIDENCE_FIELDS` 전체를 대상으로 한다.
  - 비어 있지 않은 문자열 검사는 **문자열 타입 필드에만** 적용한다. 이를 위해
    `EVIDENCE_STRING_FIELDS = ("claim", "location")` 상수를 도입한다.
  - `verified`는 별도로 **boolean 타입 검사**를 받는다. 문자열 `"false"`나 정수 `0`은
    거부한다(`isinstance(x, bool)` 판정).
- **R3.3** `verdict == "PASS"`이면서 `verified == false`인 evidence 항목이 1개 이상 있으면
  **검증 오류**다. 오류 메시지는 미검증 항목이 존재함을 명시한다.
- **R3.4** `verdict != "PASS"`인 리뷰의 미검증 evidence는 오류가 아니다(#37이 요구하는
  정상 신호다).
- **R3.5** `SchemaDriftTests`가 계속 성립해야 한다 — 스키마의 evidence 필수 필드 집합과
  Python 상수 `EVIDENCE_FIELDS`가 일치해야 한다. 그 테스트의 `minLength` 루프는
  `("claim", "location")`을 하드코딩하므로(`test_validate_review.py:384`) boolean 필드
  추가와 충돌하지 않는다.
- **R3.6** `quality-reviewer.md`가 모든 evidence 항목에 `verified`를 채우고, `false`일 때
  그 이유를 `claim`에 적도록 계약을 갱신한다. BLOCKED payload의 단일 evidence 항목도 같은
  규칙을 따른다.
- **R3.7** `record_review`는 `validate_review`를 이미 호출하므로
  (`quality_state.py:609-613`) R3.3이 상태 기록 경로에도 자동 적용된다. 별도 코드 추가
  없이 이 성질이 성립함을 테스트로 고정한다.

### R4. 버전·문서 요구사항

- **R4.1** `SKILL.md` frontmatter의 `version`을 `3.0.0` → `4.0.0`으로 바꾼다
  (`docs/quality-goal-maintenance.md`의 "게이트 규칙이나 상태 머신 계약 변경: MAJOR").
- **R4.2** `test_content_contracts.py`의 frontmatter 고정 기대값을 `4.0.0`으로 갱신한다.
  frontmatter 키 집합은 바뀌지 않는다.
- **R4.3** `docs/quality-goal-maintenance.md`의 "추적 중인 후속 작업" 목록을 갱신한다.
  **현재 목록은 `#36`, `#37`, `#38`, `#39` 4개이며 나머지 열린 quality-goal 이슈는 전혀
  들어 있지 않다**(실측). 조치는 (a) 이번에 해소되는 `#37`·`#38`을 제거하고, (b) 손으로
  유지하는 열거를 영구 최신으로 만들 수 없다는 사실을 인정해 **권위 목록이 GitHub의 열린
  이슈임을 명시하는 한 줄과 조회 명령을 추가**하며, (c) 이 작업이 의도적으로 손대지 않는
  인접 결함 `#43`을 명시적으로 남긴다. `#44`는 해소되므로 항목을 만들지 않는다(D9).
- **R4.4** 이 작업의 산출물 문서 3개(`spec.md`, `plan.md`, `report.md`)를
  `docs/development/2026-09-03-quality-goal-review-loop/`에 만든다.

### R5. 호환성·회귀 요구사항

- **R5.1** 기존 201개 테스트가 계속 통과한다. evidence 형태를 고정한 지점은 정확히
  **4곳**이며(전수 실측: `grep -rn '"claim"' tests/`) 새 필수 필드를 반영해 갱신한다:
  `tests/fixtures/review-valid-plan.json:9-12`,
  `tests/fixtures/review-high-finding.json:21-24`,
  `tests/test_validate_review.py:37-42`의 `valid_review()`,
  `tests/test_quality_state.py:75-80`의 `valid_review()`.
  `tests/fixtures/verification-pass.json`은 **evidence 배열이 없으므로 영향받지 않는다.**
- **R5.2** `tests/test_quality_state.py:191-215`의 상태 키 집합 고정 테스트에
  `review_unverified_retry`를 추가한다.
- **R5.3** `review.schema.json`은 `codex exec --output-schema`에 전달되지 않는다. 실측:
  `--output-schema` 인자로 쓰이는 유일한 스키마는 `references/model-routing.md`의
  `codex-result.schema.json`이다. 따라서 OpenAI structured-output 제약(`uniqueItems`·정규식
  lookaround의 HTTP 400 거부, `docs/development/2026-08-25-quality-goal/deviations.md`
  D-15에 실측 기록)은 이 스키마 확장에 적용되지 않는다. 그럼에도 이번 확장은
  `uniqueItems`를 새로 도입하지 않고 정규식을 쓰지 않는다.
- **R5.4** 각 신규 규칙에 회귀 테스트를 붙인다.
- **R5.5** 신규 규칙 각각에 **변이 검증**을 수행한다 — 해당 구현을 되돌리면 대응 테스트가
  실패해야 한다. 대상은 AC-55가 열거하는 목록과 정확히 일치한다.
- **R5.6** `SKILL.md`는 500행 미만을 유지한다
  (`test_content_contracts.py:901-904`의 `assertLess(len(text.splitlines()), 500)`).
  현재 342행이므로 여유는 157행이다.

## Acceptance criteria

각 기준은 명시된 명령의 종료 코드 또는 출력으로 판정한다. `$SK`는
`dot_claude/skills/quality-goal`, `$V`는 `$SK/scripts/validate_review.py`, `$Q`는
`$SK/scripts/quality_state.py`, `$BASE`는 `5ed7b57387d6a271e8e014091ff8143f488e0d29`를
가리킨다. 모든 Python 호출에 `PYTHONDONTWRITEBYTECODE=1`을 붙인다.

### #44 (R1)

- **AC-1** [실행] `open_findings` 7필드를 모두 갖춘 유효한 prior와 라운드 2 리뷰로
  `python3 $V validate --input <r2> --artifact plan --prior <prior>` → exit 0,
  `{"valid":true,"errors":[]}`.
- **AC-2** [실행] `open_findings[0]`에서 7필드 중 하나를 제거하면 exit 2이고 errors에 그
  필드명이 나타난다. 7필드 각각에 대해 반복한다(`subTest`).
- **AC-3** [실행] `open_findings[0].severity`를 `"Trivial"`로 바꾸면 exit 2.
- **AC-4** [실행] `open_findings[0]`에 `extra` 키를 넣으면 exit 2이고 errors에 `'extra'`가
  나타난다 (R1.3).
- **AC-5** [실행] `open_findings`에 같은 `id`가 2개면 exit 2 (R1.4).
- **AC-6** [실행] `open_finding_ids: ["PLAN-001"]`인데 `open_findings`에 `PLAN-001`이
  없으면 exit 2 (R1.5 커버리지).
- **AC-7** [실행] `open_finding_ids: ["PLAN-001"]`이고 `open_findings`가
  `PLAN-001`(blocker) + `PLAN-002`(Medium, 비-blocker)를 담으면 exit 0 — 상위집합 허용
  (R1.5 역방향 비요구).
- **AC-8** [실행] `resolved_finding_ids`가 `open_finding_ids`와 ID를 공유하면 exit 2
  (R1.6 교집합).
- **AC-9** [실행] `resolved_finding_ids`에 같은 ID가 2개면 exit 2, 원소가 정수면 exit 2
  (R1.6 중복·타입).
- **AC-10** [실행] `open_findings[0]`의 앞 5개 문자열 필드 각각을 `""`와 `"   "`로 두면
  exit 2 (R1.2, `subTest` 10회).
- **AC-11** [실행] `resolution_claim`·`resolution_evidence`를 `null`로 두면 exit 0이고,
  정수 `1`로 두면 exit 2 (R1.2 문자열-또는-null).
- **AC-12** [실행] `{"open_finding_ids": []}`만 담은 prior로 라운드 2 리뷰 검증 → exit 0
  (R1.7 하위 호환).
- **AC-13** [실행] `record-review` 라운드 2 경로(내부 prior가 ID만 담는 경로)가 계속
  성공한다 (R1.7).
- **AC-14** [실행] prior에 최상위 unknown 키(`open_finding`)를 넣으면 exit 2이고 errors에
  `'open_finding'`이 나타난다 (R1.8).
- **AC-15** [문서+테스트] `SKILL.md` 본문이 라운드 2+ 리뷰어 입력으로 open finding의
  설명·증거 위치·요구 해소책·해소 주장을 보내라고 지시하고, 해소된 항목은 ID만 보낸다고
  명시하며, `test_content_contracts.py`의 계약 테스트가 이를 단정한다 (R1.9).
- **AC-16** [문서+테스트] `SKILL.md`가 구조화된 prior를 `reviews[artifact][*].path`의 이전
  리뷰 JSON에서 조립하라고 지시하고, 계약 테스트가 이를 단정한다 (R1.10).
- **AC-17** [문서+테스트] `quality-reviewer.md`가 라운드 2+에서 전달받은 각 open finding의
  해소 여부를 판정해 `evidence`에 기록하고 재진술 시 기존 ID를 재사용하도록 규정하며,
  계약 테스트가 이를 단정한다 (R1.11).

### #37 (R2)

- **AC-18** [실행] `verdict=REVISE`, `blockers=[]`, `verified:false` evidence 1개를 담은
  리뷰로 `python3 $Q record-review-unverified --state S --review R --artifact-digest D`
  → exit 0. 결과 상태의 `review_unverified_retry`가
  `{artifact, round, attempts: 1, exhausted: false, artifact_digest: D,
  unverified_claims: [...], discarded_reviews: [R]}`이고 `rounds[artifact]`가
  **증가하지 않는다** (R2.2, R2.7).
- **AC-19** [실행] 같은 입력에서 `blockers`가 비어 있지 않으면 exit 2 (R2.3).
- **AC-20** [실행] 같은 입력에서 모든 evidence의 `verified`가 `true`면 exit 2 (R2.3).
- **AC-21** [실행] `verdict`가 `PASS` 또는 `BLOCKED`면 exit 2 (R2.3).
- **AC-22** [실행] 잘못된 스테이지(예: `IMPLEMENTING`)에서 호출하면 exit 2 (R2.4-3).
- **AC-23** [실행] `round`가 `rounds[artifact] + 1`이 아니면 exit 2다. 아울러 **라운드가
  불일치이면서 동시에 `ROUND_LIMITS[artifact]`를 초과하는** 리뷰(예: spec에서
  `rounds.spec = 0`인데 리뷰의 `round`가 `9`)를 넘기면 **exit 2**(exit 3이 아님)이다 —
  R2.4의 고정된 평가 순서에서 라운드 일치 검사가 한도 검사보다 먼저이기 때문이다
  (R2.4-5, R2.4-6 순서).
- **AC-24** [실행] 스키마 위반 리뷰(예: evidence 항목에서 `claim` 제거)를
  `record-review-unverified`에 넘기면 exit 2이고 상태 파일이 바이트 동일하게 유지된다
  (R2.4-7).
- **AC-25** [실행] `--artifact-digest`를 생략하면 argparse가 exit 2로 거부한다. spec
  아티팩트에서 등록된 파일의 실제 digest와 다른 값을 넘기면 exit 2이고 상태가 불변이다
  (R2.4-1, R2.4-4).
- **AC-26** [실행] `rounds[artifact] == ROUND_LIMITS[artifact]`이고 리뷰의 `round`가
  `rounds[artifact] + 1`(= 한도 + 1)인 입력으로 호출하면 **exit 3**이다 — 라운드 일치
  검사를 통과한 뒤 한도 검사에 걸리는 유일한 조합이다. 상태는 불변이다 (R2.4-5, R2.4-6).
- **AC-27** [실행] AC-18 성공 직후 **두 번째** 미검증 리뷰(다른 경로 `R2`)로 같은
  (아티팩트, 라운드)에 다시 호출하면 **exit 0**이고, 상태의
  `review_unverified_retry.attempts == 2`, `exhausted == true`,
  `discarded_reviews == [R, R2]`이며 `unverified_claims`가 두 리뷰의 claim을 모두 담고,
  `rounds[artifact]`는 여전히 증가하지 않는다 (R2.5, R2.7).
- **AC-28** [실행] AC-27 직후 **세 번째** 호출은 exit 3이고 stderr가
  `REVIEWER_UNVERIFIED_PERSISTS`를 담으며 상태 파일이 바이트 동일하게 유지된다 (R2.5).
- **AC-29** [실행] AC-27·AC-28 이후에도 상태 `stage`는 리뷰 스테이지 그대로이며 터미널이
  아니다 → 이어서 `set-artifact --kind report`가 exit 0으로 성공하고, 그 다음
  `transition --to BLOCKED --reason REVIEWER_UNVERIFIED_PERSISTS:spec`이 exit 0이다
  (R2.6, #43 재생산 방지). 근거: `set_artifact`는 `_require_active`를 호출해 터미널
  스테이지에서 `TransitionError`를 던진다(`quality_state.py:107-113`, `:286-311`).
- **AC-30** [실행] AC-18 후 **동일한 digest**를 제시한 정상 리뷰로 `record-review`를
  호출하면 exit 0이고 결과 상태의 `review_unverified_retry`가 `null`이다 (R2.8).
- **AC-31** [실행] AC-18 후 **다른 digest**를 제시한 리뷰로 `record-review`를 호출하면
  exit 2이고 `rounds[artifact]`가 증가하지 않으며 오류 메시지가 재수행 digest 바인딩을
  명시한다. 같은 상황에서 두 번째 `record-review-unverified`가 다른 digest를 제시해도
  exit 2다 (R2.12).
- **AC-32** [실행] AC-31의 spec 시나리오 변형 — 재수행 중 spec 파일을 실제로 개정하고
  digest를 재계산해 제시하면, `record-review`가 R2.12 바인딩 검사로 exit 2를 낸다. 즉
  "digest를 다시 계산하면 통과한다"는 우회가 닫혀 있다 (R2.12).
- **AC-33** [문서+테스트] `SKILL.md`가 R2.1의 세 조건(REVISE·blockers 비어 있음·미검증
  evidence 존재)과 "라운드를 소모하지 않는다"·"같은 라운드로 재기동"·"폐기 리뷰 2건
  상한(무료 재수행 1회)"·"`exhausted`를 본 뒤 보고서 등록 → `BLOCKED`
  `REVIEWER_UNVERIFIED_PERSISTS`"를 명시하고, 계약 테스트가 이를 단정한다 (R2.9).
- **AC-34** [문서+테스트] `SKILL.md`가 그 BLOCKED 종결이 리뷰어 역량 한계이며 코드·설계
  실패가 아님을 기록하도록 지시하고, 계약 테스트가 이를 단정한다 (R2.9).
- **AC-35** [문서+테스트] `SKILL.md`가 재수행 입력에 (a) 미검증 조건을 해소할 증거 경로,
  (b) 폐기 리뷰의 비-blocking findings 전문을 담고 라운드 2+에서는 prior의
  `open_findings`에도 포함하도록 지시하며, (c) 재수행 중 아티팩트·워크스페이스를 개정하지
  않는다고 명시하고, 계약 테스트가 이를 단정한다 (R2.2, R2.11, R2.12).
- **AC-36** [문서+테스트] `quality-reviewer.md`가 미검증 조건을 `verified: false`
  evidence로 표시하도록 규정하고, 계약 테스트가 이를 단정한다 (R2.10).
- **AC-61** [실행] **라운드 2 이상의 미검증 REVISE가 실제로 통한다.** spec 라운드 1을
  blocker `SPEC-A` 1건과 함께 `record-review`로 기록한 뒤(`rounds.spec = 1`,
  `open_finding_ids.spec = ["SPEC-A"]`), `round: 2`이고 `verdict=REVISE`,
  `blockers=[]`, `verified:false` evidence 1건인 리뷰로 `record-review-unverified`를
  호출하면 **exit 0**이고 `rounds.spec`이 **1로 유지**된다. `--prior`를 넘기지 않았음에도
  성공해야 하며, 이는 서브커맨드가 R2.4b대로 내부에서 prior를 조립했음을 증명한다
  (R2.4b).
- **AC-62** [실행] **`--prior` 인자는 존재하지 않는다.**
  `python3 $Q record-review-unverified --help` 출력에 `--prior`가 없고, `--prior`를
  넘기면 argparse가 exit 2로 거부한다 (R2.4b).
- **AC-63** [실행] **낡은 `review_unverified_retry` 기록이 정당한 호출을 막지 않는다.**
  이것은 **방어적 가드**다 — R2.8의 초기화 때문에 정상 CLI 흐름만으로는 불일치 기록이
  거의 남지 않지만, 상태 파일은 외부에서 편집될 수 있고 미래의 새 경로가 그런 기록을
  남길 수 있으므로 동작이 정의되어 있어야 한다. 테스트는 상태 dict에 낡은 기록을
  **직접 심어** 판정한다. `{artifact: "spec", round: 1, attempts: 2,
  exhausted: true, artifact_digest: X, …}`를 심고 `rounds.spec = 1`인 상태에서:
  (a) `round: 2` 미검증 리뷰로 `record-review-unverified`를 호출하면 **exit 0**이고
  기록이 `{artifact: "spec", round: 2, attempts: 1, exhausted: false,
  artifact_digest: <이번 digest>, …}`로 **대체**된다(누적이 아니다);
  (b) 대신 `round: 2` 정상 리뷰로 `record-review`를 `X`와 **다른** digest와 함께
  호출하면 **exit 0**이다 — 저장된 기록의 `round`가 `rounds.spec + 1`과 다르므로
  R2.12 바인딩 검사를 건너뛴다;
  (c) 그 성공 후 `review_unverified_retry`가 `null`이다 (R2.13, R2.8).

### #38 (R3)

- **AC-37** [실행] `review.schema.json`을 로드해 evidence 항목의 `required`가
  `{claim, location, verified}`(집합 동등)이고 `properties.verified.type == "boolean"`이며
  `additionalProperties`가 `false`임을 단정 → 성공 (R3.1).
- **AC-38** [실행] evidence 항목에서 `verified`를 뺀 리뷰 검증 → exit 2, errors에
  `verified`가 나타난다 (R3.2).
- **AC-39** [실행] `verified`를 문자열 `"false"` 또는 정수 `0`으로 두면 exit 2 (R3.2).
- **AC-40** [실행] `verdict=PASS`이고 evidence에 `verified:false`가 1개 있으면 exit 2이고
  errors가 미검증 항목 존재를 명시한다 (R3.3).
- **AC-41** [실행] `verdict=REVISE`이고 evidence에 `verified:false`가 있으면 exit 0 (R3.4).
- **AC-42** [실행] `verified: true`(boolean)가 정상 통과하는 동시에 같은 evidence 항목의
  `claim`을 `""`로 두면 exit 2다 — 비어 있지 않은 문자열 검사가 문자열 필드에만 적용되고
  boolean 필드에는 적용되지 않음을 증명한다 (R3.2 `EVIDENCE_STRING_FIELDS`).
- **AC-43** [실행] `SchemaDriftTests`가 통과한다 — 스키마 evidence 필수 필드 집합 ==
  `EVIDENCE_FIELDS` (R3.5).
- **AC-44** [실행] `verdict=PASS` + `verified:false` 리뷰로 `record-review`를 호출하면
  exit 2로 거부되고 `rounds[artifact]`가 증가하지 않는다 (R3.7).
- **AC-45** [문서+테스트] `quality-reviewer.md`가 모든 evidence 항목에 `verified`를 채우고
  `false`일 때 이유를 `claim`에 적도록, BLOCKED payload에도 같은 규칙이 적용되도록
  규정하며, 계약 테스트가 이를 단정한다 (R3.6).

### 버전·문서 (R4)

- **AC-46** [실행] `SKILL.md` frontmatter의 `version`이 `4.0.0`이다 (R4.1).
- **AC-47** [실행] `test_content_contracts.py`의 frontmatter 고정 테스트가 통과하고,
  기대 키 집합이 `{name, version, description, argument-hint, disable-model-invocation,
  model, effort}` 그대로다 (R4.2).
- **AC-48** [실행] `docs/quality-goal-maintenance.md`의 "추적 중인 후속 작업" 절이
  `#37`·`#38`·`#44`를 담지 않고, `#43`을 담으며, GitHub 열린 이슈가 권위 목록임을 밝히는
  문장과 조회 명령을 담는다 (R4.3).
- **AC-49** [실행] `docs/development/2026-09-03-quality-goal-review-loop/`에 `spec.md`,
  `plan.md`, `report.md`가 존재한다 (R4.4).

### 호환성·회귀 (R5)

- **AC-50** [실행] `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s
  dot_claude/skills/quality-goal/tests -p 'test_*.py'` → exit 0, 실패 0건, 총 테스트 수가
  **201 초과** (R5.1, R5.4).
- **AC-51** [실행] evidence 형태를 고정한 **4곳**이 모두 `verified`를 갖는다:
  `tests/fixtures/review-valid-plan.json`, `tests/fixtures/review-high-finding.json`,
  `tests/test_validate_review.py`의 `valid_review()`,
  `tests/test_quality_state.py`의 `valid_review()`.
  `tests/fixtures/verification-pass.json`은 evidence 배열이 없어 변경 대상이 아니며
  변경되지 않았음을 확인한다.
  판정 명령(파이썬 단정): 위 4개 파일을 로드해 각 파일의 evidence 객체가 모두
  `claim`·`location`·`verified` 세 키를 갖는지 확인한다. 두 fixture는 `json.load` 후
  `payload["evidence"]`를, 두 헬퍼는 `valid_review()`를 호출해 반환 dict의
  `["evidence"]`를 본다. 아울러 `git diff $BASE...HEAD --
  $SK/tests/fixtures/verification-pass.json`이 빈 출력이다.
  **grep 기반 판정을 쓰지 않는다** — `grep -rn '"claim"' $SK/tests/`는 5행을 내며
  다섯 번째(`tests/test_validate_review.py:384`)는 `for field in ("claim", "location")`
  튜플이라 evidence 객체가 아니고, R3.5가 그 줄을 그대로 두라고 요구하므로 결코
  `verified`를 가질 수 없다 (R5.1).
- **AC-52** [실행] `tests/test_quality_state.py`의 상태 키 집합 단언에
  `review_unverified_retry`가 포함되고, `init`이 그 키를 `null`로 만든다 (R5.2).
- **AC-53** [실행] `grep -rn 'output-schema' $SK` 결과에 `review.schema.json`이 나타나지
  않는다 (R5.3).
- **AC-54** [실행] `wc -l $SK/SKILL.md`가 500 미만이다 (R5.6).
- **AC-55** [실행] **변이 검증을 신규 규칙 전수에 수행한다.** 대상 목록(R5.5와 동일):
  (1) R1.5 커버리지, (2) R1.8 prior 최상위 unknown 키, (3) R1.2 문자열-또는-null,
  (4) R1.6 교집합, (5) R2.3 트리거 조건 검사, (6) R2.4-4 digest 현재-파일 교차 검사,
  (7) R2.5 폐기 2건 상한, (8) R2.12 재수행 digest 바인딩, (9) R3.3 PASS 금지,
  (10) R3.2 boolean 타입 검사, (11) R2.8 `review_unverified_retry` 초기화,
  (12) R2.4b 내부 prior 조립(제거하면 AC-61이 실패해야 한다),
  (13) R2.13 (아티팩트, 라운드) 일치 술어(항상 일치로 바꾸면 AC-63이 실패해야 한다).
  각 항목을 소스에서 무력화하면 대응 테스트가 실패해야 하고, 확인 후 즉시 복원한다.
  복원 후 `git diff --stat`이 해당 파일에 대해 변이 이전 상태와 동일해야 하며,
  `find $SK -name '__pycache__' -prune -exec rm -rf {} +`로 바이트코드 캐시를 지운 뒤
  전체 스위트를 재실행한다.
- **AC-56** [실행] **변경 파일 allow-list 준수.** 최종 커밋 후 PR 생성 전에
  `git diff --name-only $BASE...HEAD`를 실행하고 그 출력을
  `grep -vE '^(dot_claude/skills/quality-goal/|dot_claude/agents/quality-reviewer\.md$|docs/)'`
  로 거른 결과가 **비어 있다**(grep exit 1) (Non-goal 11).
- **AC-57** [실행] **#43 블록 불변.** 최종 커밋 후 다음이 exit 0이다 — 행 번호가 아니라
  내용으로 앵커한다:
  ```
  git show $BASE:dot_claude/skills/quality-goal/scripts/quality_state.py \
    | sed -n '/^    recurring = next/,/REVIEW_LIMIT_EXHAUSTED/p' > /tmp/base-block.txt
  sed -n '/^    recurring = next/,/REVIEW_LIMIT_EXHAUSTED/p' \
    dot_claude/skills/quality-goal/scripts/quality_state.py > /tmp/head-block.txt
  diff /tmp/base-block.txt /tmp/head-block.txt
  ```
  (Non-goal 1).
- **AC-58** [실행] **`ROUND_LIMITS`·루브릭 불변.**
  `git diff $BASE...HEAD -- $SK/references/` 가 빈 출력이고,
  `grep -n 'ROUND_LIMITS = ' $SK/scripts/quality_state.py`가
  `{"spec": 3, "plan": 2, "code": 3}`를 낸다 (Non-goal 7, 8).
- **AC-59** [실행] **배포 규율.** `report.md`의 "실행한 명령" 표가 이 실행의 배포 기록
  전체이며, 그 표에서 `chezmoi apply`를 담은 모든 행이 정규식
  `chezmoi apply (?:--[^\s]+ )*[^\s]+` 에 매치한다 — 즉 경로 인자가 최소 1개 있다.
  판정 명령: `grep -n 'chezmoi apply' docs/development/2026-09-03-quality-goal-review-loop/report.md`
  의 각 행이 위 정규식을 만족하는지 확인하고, 인자 없이 끝나는 `chezmoi apply` 행이
  0건임을 단정한다.
  **한계를 명시한다**: 세션의 실제 명령 이력은 어떤 명령으로도 감사할 수 없으므로 이
  기준은 보고서라는 산출물만 판정한다. 배포 자체를 하지 않은 경우 매치 행이 0건이며
  이 역시 통과다 (Non-goal 2).
- **AC-60** [실행] **추적표 전수성.** 아래 "요구사항 전수 대응 확인" 표가 이 Spec이
  정의한 모든 요구사항을 하나 이상의 AC에 대응시킨다. 판정 명령(파이썬 단정):
  `spec.md`에서 `^- \*\*(R\d+\.\d+[a-z]?)\*\*` 로 요구사항 ID 집합을 뽑고, 추적표에서
  `^\| (R\d+\.\d+[a-z]?) \|` 로 행 ID 집합을 뽑아 **두 집합이 같은지** 단정한다. 이어서
  표의 각 행이 `AC-\d+` 를 최소 1개 인용하고 그 번호가 모두 실제 정의된 AC인지
  단정한다. 이 기준은 AC 쪽 전수성(모든 AC가 표에 인용됨)은 요구하지 않는다 —
  Non-goal을 판정하는 AC-56~AC-59와 이 AC-60 자신은 요구사항 행을 갖지 않기
  때문이다.

## 요구사항 전수 대응 확인

| 요구사항 | 대응 AC |
|---|---|
| R1.1 | AC-1 |
| R1.2 | AC-2, AC-3, AC-10, AC-11, AC-55(3) |
| R1.3 | AC-4 |
| R1.4 | AC-5 |
| R1.5 | AC-6, AC-7, AC-55(1) |
| R1.6 | AC-8, AC-9, AC-55(4) |
| R1.7 | AC-12, AC-13 |
| R1.8 | AC-14, AC-55(2) |
| R1.9 | AC-15 |
| R1.10 | AC-16 |
| R1.11 | AC-17 |
| R2.1 | AC-18, AC-19, AC-20, AC-21, AC-33 |
| R2.2 | AC-18, AC-35 |
| R2.3 | AC-19, AC-20, AC-21, AC-55(5) |
| R2.4 | AC-22, AC-23, AC-24, AC-25, AC-26, AC-55(6) |
| R2.4b | AC-61, AC-62, AC-55(12) |
| R2.5 | AC-27, AC-28, AC-55(7) |
| R2.6 | AC-29 |
| R2.7 | AC-18, AC-27 |
| R2.8 | AC-30, AC-63, AC-55(11) |
| R2.9 | AC-33, AC-34 |
| R2.10 | AC-36 |
| R2.11 | AC-35, AC-7 |
| R2.12 | AC-31, AC-32, AC-35, AC-55(8) |
| R2.13 | AC-63, AC-55(13) |
| R3.1 | AC-37 |
| R3.2 | AC-38, AC-39, AC-42, AC-55(10) |
| R3.3 | AC-40, AC-55(9) |
| R3.4 | AC-41 |
| R3.5 | AC-43 |
| R3.6 | AC-45 |
| R3.7 | AC-44 |
| R4.1 | AC-46 |
| R4.2 | AC-47 |
| R4.3 | AC-48 |
| R4.4 | AC-49 |
| R5.1 | AC-50, AC-51 |
| R5.2 | AC-52 |
| R5.3 | AC-53 |
| R5.4 | AC-50 |
| R5.5 | AC-55 |
| R5.6 | AC-54 |

모든 요구사항이 하나 이상의 실행 가능한 AC에 대응한다. 부정 요구사항(Non-goal)은
AC-56·AC-57·AC-58·AC-59가 결정적으로 판정한다.

## Architecture

세 항목은 **하나의 데이터 흐름**을 공유한다.

```
quality-reviewer (fresh, unnamed one-shot task)
   │ review JSON (review.schema.json)
   ▼
validate_review.py validate --prior ──┐
   │                                   │ (#44) prior 입력 형태 + 최상위 unknown 키
   │ (#38) evidence[].verified 규칙     │
   ▼                                   │
validate_review.py gate                │  ← 변경 없음 (Non-goal 4)
   │                                   │
   ▼                                   │
quality_state.py record-review ────────┘  (라운드 소모, 한도 = ROUND_LIMITS, 불변)
   또는
quality_state.py record-review-unverified (#37, 라운드 비소모, 폐기 2건 상한)
```

**#38이 기반이다.** `evidence[].verified`가 "무엇을 검증하지 못했는가"를 기계가 읽을 수
있는 유일한 신호이며 #37의 트리거 조건(R2.1)이 그 신호를 소비한다. 스키마 확장이 없으면
#37은 지시문 수준에 머문다. 반대로 **구현 순서는 사용자가 지정한 #44 → #37 → #38**이며
이는 파일 충돌 최소화 순서다 — #44가 prior 검증 함수를, #37이 상태 머신을, #38이
스키마·evidence 검증을 각각 만져 세 지점이 겹치지 않는다. #37의 트리거 조건이 #38의 필드를
참조하는 역방향 의존이 있으므로 #37 단계에서는 그 필드를 전제로 코드를 쓰고, #38 단계에서
필드를 실제로 도입한 뒤 전체 스위트로 결합을 검증한다(D8).

### 책임 경계

| 컴포넌트 | 이 작업에서의 책임 | 바뀌지 않는 것 |
|---|---|---|
| `review.schema.json` | evidence에 `verified` 필수 필드 추가 | 나머지 필드·enum·`additionalProperties: false`·기존 `uniqueItems` 2곳 |
| `validate_review.py` | prior 확장 검증과 최상위 unknown 키(R1), `verified` 검증·PASS 금지·문자열 필드 분리(R3) | `evaluate_gate`의 게이트 사유 목록, 점수 임계, `REQUIRED_CHECKS` |
| `quality_state.py` | `record-review-unverified` 서브커맨드(내부 prior 조립 포함) + `review_unverified_retry` 상태 키 + `record_review`의 재수행 digest 바인딩 검사·초기화 | `record_review`의 자동 전이 블록(#43), `ALLOWED_TRANSITIONS`, `TERMINAL_STATES`, `ROUND_LIMITS` |
| `SKILL.md` | 리뷰 호출 계약 확장(R1.9·R1.10), 미검증 REVISE 정책 신설(R2.9·R2.11·R2.12), version 4.0.0 | 스테이지 표, 라운드 한도 서술, 승인 게이트, Codex 계약, 안전 규칙 |
| `quality-reviewer.md` | prior 소비 규칙(R1.11), `verified` 기입 규칙(R3.6) | frontmatter, 도구 목록, BLOCKED payload 8필드 규칙 |
| `references/*.md` | 없음 | 전부 (Non-goal 8) |
| `tests/` | 기존 evidence 형태·상태 키 단언 갱신 + 신규 회귀 테스트 | 기존 테스트의 의도 |
| `docs/quality-goal-maintenance.md` | 추적 목록 갱신(R4.3) | 나머지 절 |

### 왜 `record-review-unverified`가 자체 서브커맨드인가

기존 `record_review_validation_failure`(`quality_state.py:666`)가 malformed 출력에 대해
같은 모양(1회 재시도 → 종결)을 이미 구현한다. 그러나 두 경로는 의미가 다르다. malformed은
**스키마 위반**이고 미검증 REVISE는 **스키마를 통과한 유효한 리뷰**다. 같은 상태 키를
공유하면 `REVIEW_OUTPUT_INVALID`와 `REVIEWER_UNVERIFIED_PERSISTS`가 섞여 종결 사유가
부정확해지고, 이는 #37이 고치려는 바로 그 문제(잘못된 종결 사유 귀속)를 재생산한다.

## Interfaces and data flow

### I1. prior 파일 (확장 후)

```json
{
  "open_finding_ids": ["PLAN-001"],
  "open_findings": [
    {
      "id": "PLAN-001",
      "severity": "High",
      "description": "AC-7이 어떤 구현 태스크에도 매핑되지 않았다.",
      "evidence_location": "plan.md#Traceability",
      "required_resolution": "AC-7을 태스크와 검증 명령에 매핑하라.",
      "resolution_claim": "Task 3에 AC-7 매핑과 검증 명령을 추가했다.",
      "resolution_evidence": "plan.md#Task-3"
    },
    {
      "id": "PLAN-004",
      "severity": "Medium",
      "description": "롤백 절차의 실패 처리가 미정의다.",
      "evidence_location": "plan.md#Rollback",
      "required_resolution": "롤백 실패 시 행동을 규정하라.",
      "resolution_claim": null,
      "resolution_evidence": null
    }
  ],
  "resolved_finding_ids": ["PLAN-002", "PLAN-003"]
}
```

- `open_finding_ids`: 필수. 기존 의미 그대로(상태가 보존하는 직전 라운드 blocker).
- `open_findings`: 선택. 존재하면 `open_finding_ids`를 커버해야 하고 상위집합일 수 있다.
- `resolved_finding_ids`: 선택. `open_finding_ids`와 교집합 없음, 중복 없음.
- **최상위 unknown 키는 오류다**(R1.8).
- 하위 호환: 두 선택 필드가 없으면 기존 동작과 동일.

### I2. `review.schema.json` evidence 항목 (확장 후)

```json
{ "claim": "…", "location": "…", "verified": true }
```

`verified == false`는 그 claim을 확인하지 못했다는 뜻이며 이유는 `claim` 안에 적는다.
`claim`·`location`은 비어 있지 않은 문자열, `verified`는 boolean이다.

### I3. `record-review-unverified` CLI

```
python3 quality_state.py record-review-unverified \
  --state <state.json> --review <review.json> --artifact-digest <sha256>
```

인자는 정확히 이 셋이다. **`--prior`는 없다** — `round >= 2`의 스키마 검증에 필요한
prior는 `record_review`와 동일하게 상태에서 내부 조립된다(R2.4b, AC-62).

아래 표는 **R2.4의 고정된 평가 순서대로** 읽는다. 먼저 만나는 실패가 종료 코드를
결정하므로, 여러 조건을 동시에 위반하는 입력의 결과는 표의 위쪽 행이 이긴다.

| # | 조건 | 종료 코드 | 효과 |
|---:|---|---|---|
| — | `--artifact-digest` 누락 | 2 | argparse 거부, 상태 불변 |
| 1 | digest 형식 오류 | 2 | 상태 불변 |
| 2 | `--review`가 JSON 객체로 로드되지 않음 | 2 | 상태 불변 |
| 3 | 알 수 없는 artifact / 스테이지 불일치 | 2 | 상태 불변 |
| 4 | spec·plan 등록 아티팩트의 현재 파일 digest 불일치 | 2 | 상태 불변 |
| 5 | `round != rounds[artifact] + 1` | 2 | 상태 불변 (한도 초과를 겸해도 이 행이 이긴다) |
| 6 | `round > ROUND_LIMITS[artifact]` | 3 | 상태 불변 |
| 7 | 스키마 검증 실패 (`round >= 2`면 내부 조립 prior 포함) | 2 | 상태 불변 |
| 8 | R2.1 불만족(blockers 있음 / 미검증 evidence 없음 / verdict 부적합) | 2 | 상태 불변 |
| 9a | 재수행 바인딩 불일치 — 같은 (아티팩트, 라운드)인데 digest가 저장값과 다름 | 2 | 상태 불변 |
| 9b | 같은 (아티팩트, 라운드) 3번째 시도 | 3 | 상태 불변, stderr에 `REVIEWER_UNVERIFIED_PERSISTS` |
| ✓ | 전부 통과, 저장 기록이 없거나 (아티팩트, 라운드)가 불일치 | 0 | 기록을 `attempts=1`, `exhausted=false`, `artifact_digest=<이번 값>`로 **새로 쓴다**(R2.13) |
| ✓ | 전부 통과, 같은 (아티팩트, 라운드) 2번째 시도 | 0 | `attempts=2`, `exhausted=true`, `discarded_reviews`·`unverified_claims` append. 라운드 불변. 재기동하지 않는다 |

성공 시 갱신된 상태 JSON을 stdout에 출력하며, 어느 경우에도 `rounds[artifact]`는 바뀌지
않는다.

종료 코드는 기존 매핑(`StateError` → 2, `TransitionError` → 3)을 그대로 따른다
(`quality_state.py:1264-1270`). 예외 경로에서 상태가 저장되지 않는 성질은
`_mutating_result`(`:1144-1156`)에서 온다 — `ApprovalMismatchError`만 예외적으로 저장한다.

### I4. 상태 키 (추가)

```json
"review_unverified_retry": null
```

또는

```json
"review_unverified_retry": {
  "artifact": "code",
  "round": 2,
  "attempts": 2,
  "exhausted": true,
  "artifact_digest": "b1946ac9…",
  "unverified_claims": [
    "결정적 명령을 재실행하지 못했다 — Read/Grep/Glob만 보유.",
    "재수행 후에도 같은 조건을 확인하지 못했다."
  ],
  "discarded_reviews": [
    ".claude/quality-state/<task-id>/code-review-round2-a.json",
    ".claude/quality-state/<task-id>/code-review-round2-b.json"
  ]
}
```

`record_review` 성공 시 `None`으로 초기화된다(R2.8).

### I5. 오케스트레이터 흐름 (라운드 2 이상)

1. 이전 라운드 리뷰 JSON들을 `reviews[artifact][*].path`에서 읽는다. 폐기된 리뷰가 있으면
   `review_unverified_retry.discarded_reviews`도 읽는다.
2. open findings(blocker + 미해소 advisory + 폐기 리뷰의 비-blocking findings)를 골라 I1의
   `open_findings`를 조립하고 각 항목에 자신의 해소 주장·증거를 붙인다. 해소 확인된 ID는
   `resolved_finding_ids`로 보낸다.
3. 그 내용을 리뷰어 프롬프트에 넣어 **이름 없는** 새 quality-reviewer를 기동한다.
4. 반환 JSON을 태스크 상태 디렉터리에 저장한다.
5. R2.1 조건이면 → `record-review-unverified`.
   - `exhausted == false`면 (3)으로 같은 라운드 재기동. 이때 미검증 조건의 증거 경로와
     폐기 리뷰의 비-blocking findings를 추가하고, 아티팩트·워크스페이스는 개정하지 않는다.
   - `exhausted == true`면 보고서를 렌더링·등록한 뒤
     `transition --to BLOCKED --reason REVIEWER_UNVERIFIED_PERSISTS:<artifact>`.
6. 아니면 → `validate`(I1 prior 전달) → `gate` → `record-review`(재수행이 있었다면 동일
   digest 제시).

## Failure behavior

| 실패 | 발현 | 처리 |
|---|---|---|
| prior의 `open_findings` 형태 위반 | `validate` exit 2, errors에 경로·필드명 | 오케스트레이터가 prior 조립을 고쳐 재실행. 리뷰어 응답 문제가 아니므로 `record-review-error` 대상이 아니다 |
| prior 최상위 unknown 키 | `validate` exit 2, errors에 키 이름 | 같음. 오타로 구조화 prior가 조용히 무력화되는 것을 막는다 |
| `open_finding_ids` 커버리지 위반 | `validate` exit 2 | 같음. 상태가 보존한 blocker를 prior에서 빠뜨렸다는 신호 |
| 리뷰에 `verified` 누락 또는 비-boolean | `validate` exit 2 / `record-review` exit 2 | 리뷰어 응답 계약 위반 → `record-review-error` → 1회 재시도 → `BLOCKED`/`REVIEW_OUTPUT_INVALID`(기존 경로) |
| PASS + 미검증 evidence | `validate` exit 2, `record-review` exit 2 | 같음. 라운드는 소모되지 않는다 |
| 미검증 사유 REVISE 1회 | `record-review-unverified` exit 0, `exhausted=false` | 같은 라운드로 범위 좁힌 재기동. 라운드 불변. 폐기 리뷰 경로와 비-blocking findings 보존 |
| 미검증 사유 REVISE 2회 | `record-review-unverified` exit 0, `exhausted=true` | 재기동 없음. 보고서 렌더링·등록 후 `transition --to BLOCKED --reason REVIEWER_UNVERIFIED_PERSISTS:<artifact>`. 리뷰어 역량 한계로 기록 |
| 3회째 호출(오케스트레이터가 `exhausted`를 무시) | `record-review-unverified` exit 3 | 결정적 상한. 상태 불변이며 stderr가 종결 사유를 명시한다 |
| 라운드 2+ 미검증 REVISE인데 prior 미조립 | `record-review-unverified` exit 2, errors에 `prior is required for round >= 2` | 구현 결함이다. R2.4b가 내부 조립을 의무화하므로 이 오류가 나오면 서브커맨드가 잘못 구현된 것이다 |
| 낡은 `review_unverified_retry` 기록이 남아 있음 | 없음 | (아티팩트, 라운드) 불일치이므로 R2.13에 따라 새 기록으로 대체되고 `record_review`의 바인딩 검사는 건너뛴다 |
| 실체 있는 REVISE를 재수행으로 세탁 시도 | `record-review-unverified` exit 2 | 정상 `record-review` 경로로 되돌린다 |
| 재수행 중 아티팩트·워크스페이스 개정 | `record-review-unverified`/`record-review` exit 2 (바인딩 또는 현재-파일 digest 불일치) | 개정을 되돌린다. 개정이 정당하면 재수행을 포기하고 정상 라운드로 기록한 뒤 다음 라운드에서 다룬다 |
| 신규 테스트가 기존 201개를 깨뜨림 | `unittest` 실패 | 원인이 fixture 형태면 갱신(R5.1), 원인이 계약 모순이면 되돌리고 Spec 개정 |
| 기존 상태 파일에 `review_unverified_retry` 없음 | 없음 | `state.get(...)`으로 관용적 읽기. `schema_version`은 1 유지 |
| 변이 검증 후 `__pycache__` 오염으로 오판 | 복원했는데도 같은 테스트가 실패 | `find $SK -name '__pycache__' -prune -exec rm -rf {} +` 후 재실행. `.gitignore`가 `__pycache__/`를 덮어 `git status`에 안 보인다 |

**롤백.** 커밋 단위 `git revert` 또는 `git branch -D 44-fix/quality-goal-review-loop`.
배포를 이미 했다면 `git revert` 후 같은 파일 경로로 `chezmoi apply <path>...`를 다시
실행한다. 파괴적 작업·마이그레이션·외부 상태 변경이 없다.

## Security and risk

- **시크릿 없음.** 변경 파일은 Markdown 지침·JSON 스키마·Python 검증기·테스트다.
  자격증명을 읽거나 쓰지 않는다. Non-goal 11의 allow-list가 `.gitignore` 자체를 변경
  대상에서 제외한다.
- **신뢰 경계.** 리뷰어 출력은 신뢰하지 않는 입력으로 계속 취급한다. 이번 변경은 그
  불신을 **강화**한다(#38: PASS 주장을 evidence와 교차 검증). prior 입력은 오케스트레이터가
  만드는 내부 데이터이나, 형태 검증과 최상위 unknown 키 거부(R1.8)를 붙여 조립 오류를
  조용히 넘기지 않는다.
- **최대 위험 — fail-open 도입.** `record-review-unverified`가 라운드를 소모하지 않으므로
  잘못 설계하면 무한 재수행이 된다. 완화: (a) 폐기 리뷰 2건 상한을 상태에 기록해 결정적
  강제하고 3회째는 `TransitionError`로 거부(R2.5), (b) 트리거 조건을 서브커맨드가 스스로
  검사해 세탁을 차단(R2.3), (c) 재수행 digest 바인딩으로 개정 차단(R2.12).
- **두 번째 위험 — #43 재생산.** 새 실패 경로가 스스로 터미널 전이하면 보고서 등록 시점이
  다시 사라진다. 완화: R2.6이 자동 전이를 금지하고 AC-29가 보고서 등록과 명시적 전이
  가능성을 실증한다.
- **세 번째 위험 — advisory finding 유실.** R2.1의 트리거가 `blockers == []`이므로
  advisory findings만으로 정당화된 REVISE도 폐기 경로를 탄다. 완화: R2.7의
  `discarded_reviews`와 R2.11의 재수행 입력 승계.
- **네 번째 위험 — `verified` 필수화의 파급.** 기존 fixture·헬퍼가 evidence 형태를
  고정한다. 완화: R5.1이 정확히 4곳을 전수 실측으로 열거하고 AC-50·AC-51이 판정한다.
  필수 대신 선택 필드로 두는 대안은 fail-open이므로 기각한다(D1).
- **다섯 번째 위험 — 배포본과의 동시 사용.** 이 실행 자체가 배포된 v3.0.0으로 돌고 다른
  세션도 같은 배포본을 쓸 수 있다. 소스 변경은 배포 전까지 이번 실행에 적용되지 않는다.
  완화: 인자 없는 `chezmoi apply` 금지(Non-goal 2), 배포는 변경 파일 경로를 명시한
  `chezmoi apply <path>...`로만 하고 사용자 승인 후 최종 단계에서 수행하며, AC-59가
  이를 판정한다. 배포 시점에 다른 세션이 실행 중이면 그 세션의 다음 리뷰 라운드부터 새
  계약이 적용되므로, 배포 여부와 시점은 사용자 결정 사항으로 보고서에 남긴다.
- **여섯 번째 위험 — 이번 실행에서 #44가 그대로 재현된다.** 배포본 v3.0.0의 리뷰 계약이
  라운드 2+에 finding ID만 보내도록 규정하므로, 이번 실행은 선행 실행과 같은 우회를
  유지한다 — 이전 라운드 리뷰 JSON 전문과 구조화된 prior를 리뷰 컨텍스트에 직접 포함한다.
  이 우회는 보고서에 기록한다.
- **프로덕션 변경 없음.** 이 워크플로는 프로덕션 자원을 변경하지 않는다. `git push`는
  브랜치 push와 PR 생성으로 한정되며 머지하지 않는다.

## Test strategy

### 결정적 명령 (단일 기준선)

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s dot_claude/skills/quality-goal/tests -p 'test_*.py'
```

현재 기준선: **201개 통과**(2026-09-03 실측, exit 0). 정적 교차 확인: 세 테스트 파일의
`def test_` 개수 합이 201(`test_content_contracts.py` 50 + `test_quality_state.py` 112 +
`test_validate_review.py` 39). 완료 시 이 값을 초과하며 실패 0건.

### 테스트 배치

| 파일 | 추가·수정 |
|---|---|
| `tests/test_validate_review.py` | prior 확장 수용·거부(AC-1~AC-14), `verified` 검증(AC-38·39·42), PASS 금지(AC-40)·REVISE 허용(AC-41), `SchemaDriftTests` evidence 필수 필드(AC-37·43), `valid_review()` 헬퍼 갱신 |
| `tests/test_quality_state.py` | `record-review-unverified` 수용·거부 경로(AC-18~AC-32), 상태 키 집합(AC-52), `record-review`의 PASS+미검증 거부(AC-44), 재수행 digest 바인딩(AC-31·32), `valid_review()` 헬퍼 갱신 |
| `tests/test_content_contracts.py` | frontmatter version 4.0.0(AC-47), SKILL.md 계약(AC-15·16·33·34·35), 리뷰어 계약(AC-17·36·45), SKILL.md 행 수(AC-54) |
| `tests/fixtures/*.json` | 두 리뷰 fixture의 evidence에 `verified` 추가(AC-51). `verification-pass.json`은 불변 |

### 보조 검증 (테스트 외)

- 스키마 JSON 파싱: `python3 -m json.tool $SK/schemas/review.schema.json`.
- 문법: `python3 -m py_compile` 두 스크립트.
- **범위 확인은 base revision 기준으로 한다** — `git diff --name-only $BASE...HEAD`
  (AC-56)와 `git show $BASE:… | sed -n …` 블록 비교(AC-57). 작업 트리 대비 명령
  (`git status --porcelain`, 인자 없는 `git diff`)은 커밋 후 공허해지므로 범위 기준으로
  쓰지 않는다.
- 불변 확인: `git diff $BASE...HEAD -- $SK/references/`(AC-58).
- 변이 검증(AC-55): 신규 규칙 11개를 각각 임시로 무력화해 대응 테스트가 실패함을
  관찰하고 즉시 복원한다. 각 사이클 전후로 `__pycache__`를 제거한다.

### 검증 카테고리 (저장소 실측)

이 저장소에는 `package.json`·`Makefile`·`justfile`·`.github/workflows`가 없다. 타입
체크·린트·빌드는 `not configured`로 기록한다(`.pre-commit-config.yaml`은 gitleaks 시크릿
스캔 전용). E2E는 스킬 번들 성격상 해당 없으며, 대신 위 보조 검증과 변이 검증이 그
역할을 한다.

## Decisions

**D1 — `verified`를 evidence의 필수 필드로 만든다(선택 필드 기각).**
선택 필드로 두고 "없으면 검증됨"으로 해석하면, 새 계약을 무시하는 리뷰어가 기존 fail-open
동작을 그대로 얻는다 — #38이 고치려는 결함이 그대로 남는다. 필수화하면 누락이 검증 오류가
되어 기존 malformed 경로(1회 재시도 → BLOCKED)로 fail-closed하게 흘러간다. 비용은 두 리뷰
fixture와 두 헬퍼(총 4곳, R5.1) 갱신이며 SemVer MAJOR가 이미 예정되어 있으므로 파괴적
변경이 허용된다.

**D2 — #38의 강제를 `validate_review`(검증)에 두고 `evaluate_gate`(게이트)에 두지 않는다.**
검증 오류로 두면 `record-review`가 리뷰를 아예 기록하지 않으므로 **라운드가 소모되지
않는다**. 게이트 실패로 두면 리뷰가 먼저 기록되어(라운드 소모) 게이트가 실패한다 — 즉
리뷰어의 계약 위반 비용을 라운드로 지불하게 되고, 이는 #37이 없애려는 바로 그 현상이다.
또한 `evaluate_gate`는 `validate_review`를 먼저 호출해 오류 시 예외를 던지므로
(`validate_review.py:294-296`), 게이트에 별도 사유를 추가하면 도달할 수 없는 코드가 된다
(Non-goal 4).

**D3 — 두 번째 `record-review-unverified`는 exit 0으로 성공하고 3번째가 exit 3으로
거부된다(선행 실행 SPEC-006의 해소).**
선행 Spec은 두 번째 호출을 exit 3 + "상태 불변"으로 규정했는데, 그러면
`REVIEWER_UNVERIFIED_PERSISTS`를 실제로 유발한 리뷰 JSON이 `discarded_reviews`에 남지
않고 `attempts`가 2에 도달할 수 없다 — 상태 파일이 권위 기록이라는 `SKILL.md` 선언과
어긋난다. 형제 함수 `record_review_validation_failure`는 차단 전에 `attempts: 2`를
기록하지만(`quality_state.py:679-694`) 그 함수는 **스스로 BLOCKED로 전이**하기 때문에 그럴
수 있다. 우리는 D4(#43 재생산 금지)에 따라 자동 전이를 하지 않으므로 같은 패턴을 쓸 수
없고, `_mutating_result`는 `ApprovalMismatchError`를 제외한 예외 경로에서 상태를 저장하지
않는다(`:1144-1156`). 따라서 **성공 응답에 `exhausted: true`를 실어 보내는 것이 두 시도를
모두 기록하면서 자동 전이를 피하는 유일한 형태**다. 대안으로 검토하고 기각한 것: (a) 새
예외 타입을 만들어 `_mutating_result`에서 저장 후 재전파 — `ApprovalMismatchError`의
특수 처리를 복제해 상태 저장 규칙이 둘로 갈라진다, (b) 두 번째 리뷰를 `report.md`에서만
참조 — 상태 파일이 여전히 불완전하다. fail-open 우려는 3회째 `TransitionError`가 결정적
상한으로 막는다(AC-28).

**D4 — `record-review-unverified`는 자동 터미널 전이를 하지 않는다.**
기존 `record_review_validation_failure`는 두 번째 실패에서 스스로 `BLOCKED`로 전이한다.
그 패턴이 #43의 결함 — 전이 후 `set-artifact --kind report`가 `_require_active`의 터미널
검사에 막혀 보고서 포인터가 유실된다(`quality_state.py:107-113`, `:286-311`). 새 경로에서
그 패턴을 복제하면 결함을 확산시키므로 상태만 기록하고 전이는 오케스트레이터에게 맡긴다.
이는 #43의 권장 수정 방향과 정합하며 #43 자체는 건드리지 않는다(Non-goal 1).

**D5 — `open_findings`는 선택 필드이며 커버리지만 요구한다(필수화 기각).**
필수화하면 `record_review`가 내부적으로 만드는 prior(`{"open_finding_ids": [...]}`,
`quality_state.py:607`)가 즉시 무효가 된다. 이를 살리려면 `record_review`가 이전 라운드
리뷰 파일들을 로드해 구조화된 prior를 조립해야 하는데, (a) 리뷰 파일 부재라는 새 실패
모드가 생기고, (b) 변경이 `record_review` 내부로 확장되어 #43과 인접한 코드의 위험이
커진다. 대신 선택 필드 + 커버리지 제약 + 최상위 unknown 키 거부(R1.8)로 두고, "리뷰어에게
반드시 구조화된 prior를 보낸다"는 요구는 `SKILL.md` 계약과 계약 테스트로 고정한다.
**한계를 명시한다**: 서브에이전트 프롬프트의 실제 내용은 외부에서 기계 검증할 수 없으므로
이 지점의 강제는 지시문 수준이다(Non-goal 5).

**D6 — `open_findings`는 `open_finding_ids`의 상위집합일 수 있다.**
집합 동등을 요구하면 blocker만 전달 가능해지고, #44의 실측 피해자(Medium·Low 5건)를 여전히
전달할 수 없다. 상태의 `open_finding_ids`가 blocker만 보존하기 때문이다
(`quality_state.py:649`). 따라서 커버리지만 요구하고 추가 항목을 허용한다. 이 허용이
R2.11의 폐기 리뷰 findings 승계도 가능하게 한다.

**D7 — #37의 트리거 조건에 `blockers == []`를 넣는다.**
`verified == false`만으로 트리거하면 실체 있는 blocker를 가진 리뷰도 미검증 항목이 하나
있으면 무료 재수행을 얻는다. blocker가 있으면 그 라운드는 정당하게 소모되어야 한다.
반대로 blocker가 없는데 REVISE인 경우, 그 REVISE를 정당화하는 것은 미검증 조건 또는
Medium·Low findings뿐이며, 전자라면 라운드를 소모할 이유가 없다. 후자가 섞여 있을 수
있으므로 R2.11이 그 findings를 승계한다.

**D8 — 구현 순서는 #44 → #37 → #38을 유지한다.**
사용자 지시이며 파일 충돌 최소화 순서다. #37의 트리거 조건이 #38의 `verified` 필드를
참조하는 역방향 의존이 있으므로, #37 단계에서는 그 필드를 전제로 코드를 쓰고 #38 단계
직후 전체 스위트로 두 변경의 결합을 검증한다. #37 단계 종료 시점에는 `verified`가 아직
없어 #37 신규 테스트가 실패할 수 있으며, 이는 예상된 중간 상태다 — 완료 판정은 모든
단계가 끝난 뒤의 AC-50으로만 한다.

**D9 — 재수행 digest를 상태에 바인딩해 개정을 결정적으로 차단한다(서술 축소 기각).**
선행 실행 SPEC-011이 지적한 대로, `--artifact-digest`를 **현재** 파일과만 비교하면
아티팩트를 개정하고 digest를 재계산한 호출자는 검사를 통과한다 — 무개정 보장은 지시문
수준에 머문다. 대안 (a) "결정적"이라는 서술을 실제 보장 수준으로 축소하는 것은 정직하지만
#37의 핵심 불변(같은 라운드의 재수행은 같은 대상을 본다)을 기계가 지키지 못하게 남긴다.
대안 (b) 첫 호출이 수용한 digest를 `review_unverified_retry.artifact_digest`에 저장하고
같은 (아티팩트, 라운드)의 이후 `record-review-unverified`·`record-review`가 동일 digest를
요구하게 하면, 개정 후 어떤 digest를 제시해도 거부된다. 비용은 상태 필드 1개와
`record_review` 진입부의 검사 1개이며, 그 검사는 Non-goal 1이 동결한 자동 전이 블록과
겹치지 않는다(AC-57이 블록 바이트 동일성을 판정). **(b)를 채택한다.**

**D10 — 리뷰어에게 checks JSON을 공급하지 않는다.**
선행 실행의 라운드 1 리뷰어가 "오케스트레이터 checks JSON이 공급되지 않아
`material_decisions_resolved`와 `acceptance_criteria_objective`를 교차 확인할 수 없었다"를
미검증 사유로 기록했다. 이는 설계상 정확한 관찰이나 계약 위반은 아니다 — `SKILL.md`의 리뷰
호출 계약이 열거하는 입력에 checks가 없고, checks는 오케스트레이터 자신의 결정적 판정이기
때문이다. 리뷰어에게 그것을 보내면 리뷰어가 오케스트레이터의 판정을 재확인하는 순환이
생긴다. 계약을 넓힐지는 별건의 후속 후보로 남긴다(Non-goal 12).

**D11 — `docs/quality-goal-maintenance.md`의 추적 목록을 열거 + 권위 포인터로 바꾼다.**
현재 목록은 `#36`·`#37`·`#38`·`#39` 4개인데 실제 열린 quality-goal 이슈는 그보다 훨씬
많다(#43·#44·#49·#50·#51·#55·#57·#58·#59·#60·#61 등, 2026-09-03 `gh issue list` 실측).
손으로 유지하는 열거는 다음 이슈가 열리는 순간 다시 낡는다. 대안 (a) 이번에 해소되는
2건만 지우기 — 목록이 여전히 사실과 다르다. 대안 (b) 전체 동기화 — 다음 이슈에서 즉시
낡는다. **채택: 해소 항목 제거 + 이 작업이 의도적으로 남기는 `#43` 명시 + "권위 목록은
GitHub 열린 이슈"라는 문장과 조회 명령 추가.** 문서 변경만이라 코드 위험이 없고
Non-goal 11의 allow-list 안이다.

**D12 — strict-only 블록은 제거한다.**
이 작업은 standard이며 인증·인가·테넌시, 마이그레이션·백필, 프로덕션 관측성, 고위험 E2E
경로가 없다. 위협·신뢰 경계와 롤백은 위 "Security and risk"·"Failure behavior"에서
비-strict 수준으로 다뤘고, 프로덕션 변경 없음도 같은 절에 명시했다.

**D14 — `record-review-unverified`는 prior를 내부 조립하고 `--prior` 인자를 만들지
않는다(라운드 1 SPEC-001의 해소).**
`validate_review`가 `round >= 2`에서 prior 부재를 무조건 오류로 만들므로
(`validate_review.py:270-273`), 서브커맨드가 prior를 공급하지 않으면 라운드 2 이상의
미검증 REVISE가 전부 exit 2로 거부되고 #37이 만들려는 경로 자체가 도달 불가가 된다.
대안 (a) `--prior` CLI 인자 추가 — 호출자가 그 파일을 만들어야 하고, `record_review`는
내부 조립을 쓰므로 같은 리뷰가 두 서브커맨드에서 다른 검증 입력을 받는 분기가 생긴다.
대안 (b) `round >= 2`일 때 검증을 건너뛰기 — R2.4-7의 fail-closed 방향을 깨고 malformed
응답이 무료 재수행 경로로 새어 들어온다. **채택: (c) `record_review`
(`quality_state.py:599-607`)와 바이트 동일한 내부 조립.** 두 경로의 검증 입력이 같아지고
CLI 표면이 늘지 않는다. 구조화된 prior(R1)는 리뷰어 프롬프트로 가는 입력이지 상태 기록
경로의 입력이 아니므로(D5) 여기에 들어올 이유가 없다.

**D15 — 전제 조건 평가 순서를 `record_review`와 일치시킨다(라운드 1 SPEC-004의 해소).**
전제 조건이 exit 2와 exit 3 두 가지로 갈리므로 순서가 정해지지 않으면 라운드 불일치와
한도 초과를 동시에 만족하는 입력의 종료 코드가 구현자 재량이 된다. 대안 (a) 한도 검사를
먼저 — 더 "엄격해 보이지만" `record_review`와 반대라 같은 리뷰가 두 서브커맨드에서 다른
코드를 낸다. **채택: (b) `record_review`의 순서 그대로**(라운드 일치 → 한도,
`quality_state.py:591-598`). 두 경로의 관측 가능한 동작이 일치하고, AC-23이 그 결과를
결정적으로 고정한다.

**D13 — 이 실행 자체의 결함 발현을 기록한다.**
이 실행은 수정 대상인 배포본 v3.0.0으로 돈다. #44는 라운드 2+에서 그대로 재현되며 우회를
유지한다(Security and risk 여섯 번째 항목). #43은 라운드 한도 소진이나 recurring blocker가
발생할 때만 발현하며, 발현하면 우회하지 않고 보고서 파일 경로를 최종 보고에 남긴다.
#38은 리뷰어가 미검증 항목을 산문으로만 표시하는 형태로 관측될 수 있으며, 관측되면
보고서에 실증으로 기록한다.
