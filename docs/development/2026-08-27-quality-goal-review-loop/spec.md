# Quality Goal Specification

- Task ID: 20260827T112608Z-44-37-38-quality-goal-리뷰-루프-결함-3건-수정-pri-f553db5a
- Mode: standard
- Status: SPEC_REVIEW (round 2)
- Created: 2026-08-27T11:26:08Z
- Updated: 2026-08-27T12:10:00Z
- Source goal: #44 #37 #38 quality-goal 리뷰 루프 결함 3건 수정: --prior 입력 확장, 미검증 REVISE 라운드 정책, no-PASS 결정적 게이트 승격
- Base revision: 6d8ccad16b4f8345130fe56913a2eead4169030f (상태 파일의 `base_revision`)

## Problem and context

`quality-goal` 스킬 v1.0.0의 리뷰 루프에 서로 맞물린 결함 3건이 실전 사용에서 드러났다.
세 결함은 모두 "리뷰어가 무엇을 검증했는지"를 시스템이 알 수 없다는 하나의 공백에서
파생한다. 네 번째 항목(라운드 한도)은 그 공백이 만든 종결 비용을 실측한 결과다.

**#44 — 라운드 2+ 리뷰 계약이 finding ID만 전달한다.**
`SKILL.md:246`은 라운드 2 이상에서 "prior open finding IDs"만 리뷰어에게 보내라고
규정한다. 설명 원문·증거 위치·오케스트레이터가 취한 조치가 전달되지 않으므로 리뷰어는
이전 finding이 해소됐는지 판정할 수 없다. 실측(2026-08-27, 실행
`20260827T080329Z-28-35-create-worktree-…`): Spec 라운드 2 리뷰어가
SPEC-005·006·007·008·010을 검증하지 못했고, 자신의 새 findings가 이전 항목의
재진술인지 배제할 수 없다고 기록했다. 근거는
`/Users/lee-kyu-hwan/code/dotfiles/docs/development/2026-08-27-create-worktree-pr-session/report.md:74-81`
("프로세스 관찰" 절)이다. 이 문서는 해당 실행이 `NEEDS_REDESIGN`으로 종료되며 `main`
체크아웃에 untracked 상태로 남아 있어 이 저장소에는 커밋되어 있지 않다.

더 나쁜 것은 오케스트레이터가 보낼 수 있는 정보 자체가 blocker로 한정된다는 점이다.
`quality_state.py:583`은 `open_finding_ids[artifact] = list(blockers)`로 blocker만
보존한다. 위 실측에서 검증되지 못한 5건은 모두 Medium·Low여서 애초에 blocker가 아니었고,
따라서 상태에서 완전히 사라졌다.

**#37 — 미검증 사유 REVISE가 리뷰 라운드를 소모한다.**
`quality-reviewer.md:61`은 "적용 가능한 게이트 조건이나 루브릭 항목을 검증하지 못했다면
verdict는 PASS가 아니어야 한다"를 요구한다(`deviations.md` D-16 FIX 2 회귀 대응. 그 규칙
없이는 턴 소진된 리뷰가 PASS로 게이트를 통과했다 — fail-open). 그런데 오케스트레이터 측
처리가 없다. `SKILL.md:264-269`는 malformed 출력과 리뷰어 기동 실패만 다룬다. 실체가
결함이 아니라 "X를 검증하지 못했다"뿐인 well-formed REVISE는 스키마 검증을 통과해
`record-review`로 기록되고(`quality_state.py:581-584`) 라운드를 1개 소모한다. 반복되면
`ROUND_LIMITS`(`quality_state.py:69`)에 걸려 `NEEDS_REDESIGN`으로 종결되고, **리뷰어
역량 실패가 코드·설계 실패로 귀속된다**. 리뷰어 예산 소진은 가설이 아니다 — D-16 FIX 2가
`maxTurns: 12`에서 출력 없이 멈춘 실측을 기록하고 있다.

**#38 — no-PASS-when-unverified가 지시문 준수에만 의존한다.**
`evaluate_gate`(`validate_review.py:292-334`)는 `verdict`·`blockers`·severity·checks만
읽고 `evidence` 배열을 전혀 보지 않는다. `review.schema.json:52`의 evidence 항목은
`{claim, location}`뿐이라 "이건 검증 못 했다"를 기계가 알 수단이 없다. code 아티팩트는
점수 임계도 없으므로(`validate_review.py:309` — spec/plan만 임계 적용) 게이트의 실질은
리뷰어 verdict + 오케스트레이터 자기 체크 4개가 전부다. 리뷰어가 미검증 조건을 "적용되지
않음"으로 재분류하면 검증과 게이트를 모두 통과한다.

**이 Spec의 라운드 1 리뷰가 #38을 직접 실증했다.** 라운드 1 리뷰어는 evidence 19건 중
2건을 명시적 `NOT VERIFIED`로 기록했다 — 180개 테스트 스위트의 exit 0(리뷰어는
Read/Grep/Glob만 보유해 실행 불가)과 오케스트레이터 checks JSON 미공급. 그 미검증 표시는
`claim` 문자열 안의 산문 `"NOT VERIFIED:"`로만 존재했고, 스키마·게이트가 읽을 수 있는
구조화된 필드는 없었다. 리뷰어가 정직해서 규칙이 작동했을 뿐이다.

**#R6 — spec 리뷰 라운드 한도 2가 수렴 직전에 실행을 절단한다.**
실전 3회의 소진 기록: spec은 2회 실행에서 2/2 전부 소진, plan은 한도 도달조차 못 함,
code는 소진 0회. 재실행
(`/Users/lee-kyu-hwan/code/dotfiles/docs/development/2026-08-27-create-worktree-pr-session-2/report.md`)의
정확한 인과는 이렇다 — **라운드 2 게이트가 실질 사유 2건(`verdict_not_pass`,
`check_failed:acceptance_criteria_objective`)으로 실패했고 점수·심각도 기준은 통과했으며
(88점 / 통과선 85 초과, 블로커 0건, Critical·High 0건), 해법이 이미 적힌 Medium 2건을
고칠 라운드가 남아 있지 않아 `NEEDS_REDESIGN`이 됐다.** "한도 때문에만 실패했다"는 사실이
아니다. 선행 실행도 75 → 82로 개선 중에 잘렸다. 즉 2/2 소진은 예외적 안전망이 아니라
상시 제약이며, 실패 비용은 실행 전체의 폐기다.

세 결함은 상호작용한다. #44가 중복 findings를 만들고, #37이 그 중복으로 라운드를
소모하며, #38이 그 어느 것도 결정적으로 잡지 못하고, 한도 2가 그 손실을 회복 불가로
만든다.

## Goals

1. 라운드 2 이상의 리뷰어가 이전 라운드 open findings의 **설명 원문·증거 위치·요구
   해소책과 오케스트레이터의 해소 주장**을 받아, 각 항목의 해소 여부를 판정할 수 있다.
   blocker가 아닌 open finding도 전달 가능하다.
2. 실체가 결함이 아니라 미검증 사유뿐인 REVISE가 리뷰 라운드를 소모하지 않고, 범위를
   좁힌 재수행으로 처리되며, 반복 시 리뷰어 역량 한계를 명시한 `BLOCKED`로 종결된다.
   이 경로가 남용될 수 없도록 결정적으로 강제되고, 폐기된 리뷰의 advisory findings가
   유실되지 않는다.
3. "미검증 조건이 있으면 PASS 금지"가 지시문이 아니라 `validate_review.py`의 결정적
   규칙이 된다. 미검증 표시가 스키마에 구조화되어 기계가 읽을 수 있다.
4. spec 리뷰가 3라운드를 얻어, 점수·심각도 기준을 넘긴 개선 궤적이 남은 소수 findings
   때문에 폐기되지 않는다. plan(2)·code(3)는 실측 근거가 없으므로 불변이다.
5. 세 루브릭의 라운드 수가 각각 결정적으로 고정되어, 한 루브릭의 편집이 다른 루브릭으로
   번지거나 조용히 통과하지 못한다.
6. 위 변경이 스킬 번들 계약을 바꾸므로 SemVer MAJOR(1.0.0 → 2.0.0)로 표기되고, 기존
   180개 결정적 테스트가 계속 통과하며 신규 회귀 테스트가 각 변경의 비공허성을 증명한다.

## Non-goals

1. **#43(record-review의 자동 터미널 전이)은 고치지 않는다.** 같은 파일
   (`quality_state.py`)을 만지지만 `record_review`의 자동 전이 블록
   (`recurring = next(...)`부터 `REVIEW_LIMIT_EXHAUSTED`까지, 현재 `:588-596`)은
   base revision과 바이트 동일해야 한다. R6은 그 블록이 참조하는 상수
   `ROUND_LIMITS`의 **값**만 바꾸고 블록 자체는 건드리지 않는다. 다만 이 작업이 새로
   추가하는 실패 경로는 같은 결함을 재생산하지 않아야 한다(D3 참조).
2. **배포하지 않는다.** `chezmoi apply`를 실행하지 않는다. 다른 세션이 배포본
   `~/.claude/skills/quality-goal`을 실행 중이다. 배포는 머지 후 사용자가 결정한다.
3. **머지하지 않는다.** PR 생성까지만 수행한다.
4. **`evaluate_gate`에 `unverified_evidence_present` 게이트 사유를 추가하지 않는다**
   (D4 참조 — 검증 단계에서 이미 거부되므로 도달 불가 코드가 된다).
5. **리뷰어 프롬프트 전달 내용 자체의 기계 검증은 하지 않는다.** 서브에이전트 프롬프트는
   외부에서 검사할 수 없다. 결정적 강제는 `--prior` 파일 형태와 게이트 규칙에 둔다
   (D2 참조).
6. **상태 파일 `schema_version`을 올리지 않는다.** 추가되는 상태 키는 관용적 읽기
   (`state.get(...)`)로 접근하므로 기존 상태 파일이 계속 로드된다.
7. **조건부 계속 진행 로직을 넣지 않는다.** "라운드 3은 진전이 있을 때만" 류의 판단
   분기는 검토 후 기각했다(D11).
8. **spec 한도를 4 이상으로 올리지 않는다.** 3이 필요했던 실측만 존재한다.
9. **요구사항 래칫 대응(수렴 규칙·추상화 이탈 감지)은 이 작업에 넣지 않는다.** 별개
   주제다.
10. **plan·code 루브릭의 라운드 수를 바꾸지 않는다.** `plan-rubric.md:33`은 2,
    `code-rubric.md:30`은 3으로 유지한다. `SKILL.md`의 plan(2)·code(3) 서술도 불변이다.
11. `evals/evals.json` 이관(#36), Codex 모델 리네이밍 대비(#39)는 범위 밖이다.
12. **변경 파일 allow-list.** 변경은 `dot_claude/skills/quality-goal/`,
    `dot_claude/agents/quality-reviewer.md`, `docs/` **세 경로 아래로만** 허용한다. 그
    밖의 어떤 경로도 변경하지 않는다(`.gitignore`, 다른 스킬, chezmoi 소스의 다른 파일
    포함).
13. **리뷰어에게 오케스트레이터 checks JSON을 공급하지 않는다.** `SKILL.md`의 리뷰 호출
    계약이 열거하는 입력에 없다. 라운드 1 리뷰어가 이를 미검증 사유로 기록했으나
    설계상 checks는 오케스트레이터 자신의 결정이며, 계약 확장은 이 작업 범위 밖의
    후속 후보다(D12).

## Requirements

### R1. #44 — `--prior` 입력 확장 (구조화된 이전 라운드 findings)

- **R1.1** `validate_review.py`의 prior 입력이 기존 필수 필드 `open_finding_ids`
  (문자열 배열) 외에 선택 필드 `open_findings`(객체 배열)와
  `resolved_finding_ids`(문자열 배열)를 받는다.
- **R1.2** `open_findings`의 각 항목은 다음 7개 필드를 모두 가진다:
  `id`, `severity`, `description`, `evidence_location`, `required_resolution`,
  `resolution_claim`, `resolution_evidence`.
  - 앞 5개(`id`, `severity`, `description`, `evidence_location`,
    `required_resolution`)는 **비어 있지 않은 문자열**이어야 한다. 공백만인 문자열도
    거부한다.
  - `severity`는 `Critical|High|Medium|Low` 중 하나여야 한다.
  - `resolution_claim`과 `resolution_evidence`는 **문자열 또는 `null`**이다. `null`은
    "해소 주장이 없다"를 뜻하는 유효한 값이다. 그 밖의 타입(정수·불리언·배열·객체)은
    거부한다.
- **R1.3** `open_findings`의 각 항목에 위 7개 외의 키가 있으면 검증 오류다
  (기존 payload·finding·evidence의 unknown-key 처리와 동일한 fail-closed 방향).
- **R1.4** `open_findings`의 `id`는 중복될 수 없다.
- **R1.5** `open_findings`가 존재하면 `open_finding_ids`의 모든 ID가 `open_findings`에
  나타나야 한다(커버리지). **역방향은 요구하지 않는다** — blocker가 아닌 open finding
  (Medium·Low)도 전달하는 것이 이 요구사항의 목적이므로 `open_findings`는 상위집합일 수
  있다(D5).
- **R1.6** `resolved_finding_ids`가 존재하면 **문자열 배열**이어야 하고(원소가 문자열이
  아니면 거부), **중복이 없어야 하며**, `open_finding_ids`와 **교집합이 없어야 한다**
  (같은 ID가 동시에 open이고 resolved일 수 없다).
- **R1.7** 위 확장은 하위 호환이어야 한다. `{"open_finding_ids": []}`만 담은 기존 형태의
  prior 파일과, `record_review`가 내부적으로 만드는
  `{"open_finding_ids": [...]}`(`quality_state.py:541`)가 계속 유효해야 한다.
- **R1.8** `SKILL.md`의 Review invocation contract가 라운드 2 이상에서 리뷰어에게
  보내는 입력을 "prior open finding IDs"에서 **"각 open finding의 ID·심각도·설명·증거
  위치·요구 해소책과 오케스트레이터의 해소 주장·해소 증거"**로 확장한다. 해소가 확인된
  항목은 ID만 `resolved_finding_ids`로 전달한다(리뷰어 컨텍스트 비용 절충 —
  이슈 #44 "수정 방향" 문단).
- **R1.9** `SKILL.md`가 오케스트레이터에게 그 구조화된 prior의 출처를 지시한다: 상태의
  `reviews[artifact][*].path`에 기록된 이전 라운드 리뷰 JSON 파일에서 findings를 읽고,
  거기에 오케스트레이터 자신의 해소 주장을 더해 조립한다. blocker만 남기는
  `open_finding_ids`에 의존하지 않는다.
- **R1.10** `quality-reviewer.md`가 라운드 2 이상에서 전달받은 각 open finding에 대해
  해소 여부를 판정하고, 그 판정을 `evidence`에 기록하도록 계약을 갱신한다. 새 finding이
  전달받은 open finding의 재진술이면 기존 ID를 재사용하고 새 ID를 만들지 않는다.
- **R1.11** prior 객체의 **최상위 unknown 키는 검증 오류**다. 현재
  `_prior_open_finding_ids`(`validate_review.py:70-93`)는 unknown-key 검사를 하지 않으므로
  `open_finding`·`openFindings`·`resolvedFindingIds` 같은 오타가 구조화된 prior 검증을
  **조용히 전부 무력화**하고 검증은 valid를 반환한다 — 리뷰어는 ID만 받는 #44 상태로
  되돌아간다. 기존 payload(`:105-106`)·finding(`:169-172`)·evidence(`:248-249`)의
  unknown-key 처리와 동일하게 fail-closed로 맞춘다. 오류 메시지는 문제된 키 이름을
  포함한다.

### R2. #37 — 미검증 사유 REVISE의 라운드 비소모 재수행

- **R2.1** `SKILL.md`가 **미검증 사유 REVISE**를 기계 판정 가능한 조건으로 정의한다:
  `verdict == "REVISE"` **이고** `blockers == []` **이고** `evidence`에
  `verified == false` 항목이 1개 이상 있다.
- **R2.2** 그 조건을 만족하는 리뷰는 `record-review`로 기록하지 않는다. 대신
  `quality_state.py`의 신규 서브커맨드 `record-review-unverified`로 시도를 기록하고,
  **같은 라운드 번호로** 새 quality-reviewer를 기동한다. 라운드는 소모되지 않는다.
  재수행 입력은 기존 계약 입력에 **다음 두 가지를 추가**한 것이다:
  - 미검증으로 표시된 각 조건을 해소할 **증거 경로**(이슈 #37이 요구하는 "범위를 좁힌
    입력");
  - 폐기되는 리뷰의 **비-blocking findings 전문**(R2.11).
  재수행 중 대상 아티팩트를 개정하지 않는다 — 같은 라운드의 재수행이므로 리뷰 대상이
  바뀌면 안 된다. 이 불변은 R2.4의 digest 검사로 결정적으로 강제된다.
- **R2.3** `record-review-unverified`는 전달된 리뷰가 R2.1 조건을 실제로 만족하는지
  스스로 검증한다. 만족하지 않으면 거부한다(exit 2). 실체 있는 REVISE를 무료 재수행으로
  세탁할 수 없어야 한다.
- **R2.4** `record-review-unverified`의 전제 조건을 **명시적으로 열거한다**(「`record_review`와
  동일」같은 포괄 서술을 쓰지 않는다). 다음 6개를 모두 검사한다:
  1. `--artifact-digest`가 소문자 SHA-256 hexdigest 형식이다. **필수 인자다.**
  2. spec·plan 아티팩트인 경우, 등록된 아티팩트 파일의 현재 digest가 그 값과 일치한다
     (`record_review`와 동일한 교차 검사). 이것이 R2.2의 "재수행 중 아티팩트 개정 금지"를
     결정적으로 강제한다. code 아티팩트는 `record_review`와 같이 이 비교를 하지 않는다.
  3. 리뷰의 `artifact`에 대응하는 리뷰 스테이지가 현재 스테이지다.
  4. 리뷰 payload가 `validate_review` 스키마 검증을 통과한다. 통과하지 못하면 exit 2로
     거부한다 — malformed 응답은 무료 재수행이 아니라 기존 `record-review-error`
     경로로 가야 한다.
  5. `round == rounds[artifact] + 1`(아직 기록되지 않은 라운드).
  6. `round`가 `ROUND_LIMITS[artifact]`를 초과하면 `TransitionError`(exit 3)다
     (`record_review:530`과 동일한 방향).
- **R2.5** 재수행은 (아티팩트, 라운드)당 **정확히 1회**다. 같은 (아티팩트, 라운드)에 대한
  두 번째 `record-review-unverified` 호출은 거부되고(exit 3), 그 오류 메시지가
  `REVIEWER_UNVERIFIED_PERSISTS`를 명시한다.
- **R2.6** `record-review-unverified`는 **스스로 터미널 상태로 전이하지 않는다.**
  두 번째 미검증 응답 시 오케스트레이터가 보고서를 렌더링·등록한 뒤 명시적으로
  `transition --to BLOCKED --reason REVIEWER_UNVERIFIED_PERSISTS:<artifact>`를 호출한다.
- **R2.7** 시도 기록은 상태의 신규 키 `review_unverified_retry`에 저장한다:
  `{artifact, round, attempts, unverified_claims, discarded_reviews}`.
  - `unverified_claims`는 그 리뷰에서 `verified == false`였던 evidence 항목의 `claim`
    문자열 목록이다.
  - `discarded_reviews`는 폐기된 리뷰 JSON의 **경로 목록**이며 시도마다 append된다.
    `record-review`를 건너뛰므로 `reviews[artifact]`에 항목이 추가되지 않아, 이 필드가
    없으면 `REVIEWER_UNVERIFIED_PERSISTS` 종결 시 상태 파일이 폐기된 리뷰를 전혀
    가리키지 못한다 — `SKILL.md:232-238`이 상태 파일을 권위 기록으로 선언하는 것과
    모순된다.
- **R2.8** `review_unverified_retry`는 `record_review`가 해당 아티팩트의 라운드를
  정상 기록할 때 `None`으로 초기화된다(`review_validation_retry`와 동일한 수명).
- **R2.9** `SKILL.md`가 R2.1~R2.6의 정책과 `BLOCKED` 종결 사유를 명시하고, 그 종결이
  코드·설계 실패가 아니라 리뷰어 역량 한계임을 기록하도록 지시한다.
- **R2.10** `quality-reviewer.md`가 미검증 조건을 알릴 때 `verified == false` evidence
  항목을 사용하도록 계약을 갱신한다(R3와 연결).
- **R2.11** 폐기되는 리뷰의 **비-blocking findings는 유실되지 않는다.** R2.1의 트리거는
  `blockers == []`이므로, advisory findings(Medium·Low)만으로 정당화된 REVISE도 이
  경로를 탄다. `SKILL.md`가 재수행 입력에 그 findings 전문을 담도록 지시하고, 라운드 2
  이상이면 추가로 prior의 `open_findings`에 포함하도록 지시한다(R1.5의 상위집합 허용이
  이를 가능하게 한다). 이것이 없으면 goal 1이 막으려는 advisory finding 유실을 이
  경로가 다시 만든다.

### R3. #38 — no-PASS-when-unverified의 결정적 승격

- **R3.1** `review.schema.json`의 evidence 항목에 `verified`(boolean)를 추가하고
  **필수 필드**로 만든다. `additionalProperties: false`는 유지한다.
- **R3.2** `validate_review.py`의 `EVIDENCE_FIELDS`에 `"verified"`를 추가한다. 단
  현재 `EVIDENCE_FIELDS`는 세 개의 루프를 동시에 구동한다 — 필수 키 검사(`:245`),
  unknown 키 검사(`:248`), **비어 있지 않은 문자열 검사**(`:251`). 세 번째 루프를 그대로
  두면 boolean `verified`가 항상 검증 오류가 되어 AC-1·AC-30과 모순된다. 따라서:
  - 필수 키 검사와 unknown 키 검사는 `EVIDENCE_FIELDS` 전체(`claim`, `location`,
    `verified`)를 대상으로 한다.
  - 비어 있지 않은 문자열 검사는 **문자열 타입 필드에만** 적용한다. 이를 위해
    `EVIDENCE_STRING_FIELDS = ("claim", "location")` 상수를 도입한다.
  - `verified`는 별도로 **boolean 타입 검사**를 받는다. 문자열 `"false"`나 정수 `0`은
    거부한다.
- **R3.3** `verdict == "PASS"`이면서 `verified == false`인 evidence 항목이 1개 이상
  있으면 **검증 오류**다. 오류 메시지는 미검증 항목이 존재함을 명시한다.
- **R3.4** `verdict != "PASS"`인 리뷰의 미검증 evidence는 오류가 아니다(#37이 요구하는
  정상 신호다).
- **R3.5** `SchemaDriftTests`가 계속 성립해야 한다 — 스키마의 evidence 필수 필드 집합과
  Python 상수 `EVIDENCE_FIELDS`가 일치해야 한다. 그 테스트의 `minLength` 루프는
  `("claim", "location")`을 하드코딩하므로(`test_validate_review.py:341-385`) boolean
  필드 추가와 충돌하지 않는다.
- **R3.6** `quality-reviewer.md`가 모든 evidence 항목에 `verified`를 채우고, `false`일
  때 그 이유를 `claim`에 적도록 계약을 갱신한다. BLOCKED payload의 단일 evidence 항목도
  같은 규칙을 따른다.
- **R3.7** `record_review`는 `validate_review`를 이미 호출하므로
  (`quality_state.py:543`) R3.3이 상태 기록 경로에도 자동 적용된다. 별도 코드 추가 없이
  이 성질이 성립함을 테스트로 고정한다.

### R4. 버전·문서 요구사항

- **R4.1** `SKILL.md` frontmatter의 `version`을 `1.0.0` → `2.0.0`으로 바꾼다
  (`docs/quality-goal-maintenance.md:54` "게이트 규칙이나 상태 머신 계약 변경: MAJOR").
- **R4.2** `test_content_contracts.py:723`의 frontmatter 고정 기대값을 `2.0.0`으로
  갱신한다. frontmatter 키 집합은 바뀌지 않는다.
- **R4.3** `docs/quality-goal-maintenance.md`의 "추적 중인 후속 작업" 목록을 갱신한다.
  **현재 목록은 `#36`, `#37`, `#38`, `#39` 4개이며 `#43`·`#44` 항목은 존재하지 않는다**
  (`:41-46` 실측). 따라서 조치는: `#37`·`#38` 항목을 **제거**하고, `#43`을 미해소
  항목으로 **신규 추가**한다. `#44`는 이번에 해소되므로 항목을 만들지 않는다.
- **R4.4** 이 작업의 산출물 문서 3개(`spec.md`, `plan.md`, `report.md`)를
  `docs/development/2026-08-27-quality-goal-review-loop/`에 만든다.

### R5. 호환성·회귀 요구사항

- **R5.1** 기존 180개 테스트가 계속 통과한다. evidence 형태를 고정한 지점은 정확히
  **4곳**이며 새 필수 필드를 반영해 갱신한다:
  `tests/fixtures/review-valid-plan.json:8-13`,
  `tests/fixtures/review-high-finding.json:20-25`,
  `tests/test_validate_review.py:29-44`의 `valid_review()`,
  `tests/test_quality_state.py:65-82`의 `valid_review()`.
  `tests/fixtures/verification-pass.json`은 **evidence 배열이 없으므로 영향받지 않는다.**
- **R5.2** `tests/test_quality_state.py:210`의 상태 키 집합 고정 테스트에
  `review_unverified_retry`를 추가한다.
- **R5.3** `review.schema.json`은 `codex exec --output-schema`에 전달되지 않는다.
  실측 확인: `--output-schema` 인자로 쓰이는 유일한 스키마는
  `references/model-routing.md:19-30`의 `codex-result.schema.json`이며,
  `deviations.md:231-232`가 "`review.schema.json`은 로컬 `validate_review.py` 전용이라
  API로 전송되지 않으므로 `uniqueItems`가 유효하다"를 명시한다. 따라서 OpenAI
  structured-output 제약(`uniqueItems`·정규식 lookaround HTTP 400 거부, 그 실측은
  `deviations.md` **D-15**에 기록됨)은 이 스키마 확장에 적용되지 않는다. 그럼에도 이번
  확장은 `uniqueItems`를 새로 도입하지 않고 정규식을 쓰지 않는다.
- **R5.4** 각 신규 규칙에 회귀 테스트를 붙인다.
- **R5.5** 신규 규칙 각각에 **변이 검증**을 수행한다 — 해당 구현을 되돌리면 대응 테스트가
  실패해야 한다. 대상은 AC-42가 열거하는 목록과 정확히 일치한다.

### R6. spec 리뷰 라운드 한도 2 → 3

- **R6.1** `quality_state.py:69`의 `ROUND_LIMITS`를
  `{"spec": 2, "plan": 2, "code": 3}` → `{"spec": 3, "plan": 2, "code": 3}`으로 바꾼다.
  `plan`과 `code`는 불변이다.
- **R6.2** `references/spec-rubric.md:33`의
  `- After round 2 without a passing gate, stop and record \`NEEDS_REDESIGN\`.`를
  `round 3`으로 바꾼다. **`plan-rubric.md:33`은 이 문장과 바이트 동일하므로**(실측
  확인) `replace_all`이나 행 번호 기반 일괄 편집을 쓰지 않고 파일별로 개별 편집한다.
  `code-rubric.md:30`(round 3)도 건드리지 않는다.
- **R6.3** `SKILL.md`의 spec 라운드 수 서술 3곳을 3으로 동기화한다: `:114`(스테이지 표
  SPEC_REVIEW), `:137`("The Spec review has at most 2 rounds"), `:144-145`("Revise only
  within the Spec limit of at most 2 rounds"). plan(`:116`, `:155`, `:162`)과
  code(`:120`, `:225`) 서술은 불변이다.
- **R6.4** 한도 값을 고정하는 기존 테스트를 갱신한다: `tests/test_quality_state.py:156`의
  `{"spec": 2, "plan": 2, "code": 3}` → `{"spec": 3, "plan": 2, "code": 3}`. 그리고
  `tests/test_content_contracts.py:914`
  `test_review_round_limits_and_reviewer_isolation_contract`의 `(("spec", 2), ("plan", 2),
  ("code", 3))` 튜플을 spec 3으로 갱신한다.
- **R6.5** `record_review_validation_failure`의 라운드 상한 검사
  (`quality_state.py:610`, `1 <= round_number <= ROUND_LIMITS[artifact]`)는 상수를
  참조하므로 spec에 대해 자동으로 3까지 허용된다. 코드 변경은 없으며 이 성질을
  테스트로 고정한다.
- **R6.6** 조건부 계속 진행 로직을 넣지 않는다(Non-goal 7, D11).

### R7. 루브릭 라운드 수의 결정적 고정

- **R7.1** 세 루브릭 계약 테스트의 라운드 단언을 **대체**한다. 현재 형태는
  `assertRegex(lower, r"stop.{0,100}round N|after round N.{0,100}stop")`이며
  `test_content_contracts.py:231`(spec)·`:282`(plan)·`:321`(code)에 있다. 이를
  `re.findall(r"after round (\d+) without a passing gate", lower)`가 정확히
  spec `["3"]`, plan `["2"]`, code `["3"]`인지 보는 단언으로 바꾼다. 개수와 값을 동시에
  고정한다.
- **R7.2** 좁힌 패턴을 쓰는 이유를 실측으로 못 박는다.
  - 넓은 패턴 `after round (\d+)`는 세 루브릭에서 각각 `['1','2']`, `['1','2']`,
    `['1','3']`을 반환한다 — 각 루브릭의 "A new blocker after Round 1 must be Critical or
    High…" 문장이 먼저 잡히기 때문이다. 따라서 `== ["3"]` 단언은 그대로 쓰면 깨진다.
  - `without a passing gate`로 좁히면 파일당 정확히 1개가 된다(실측: spec `['2']`,
    plan `['2']`, code `['3']`).
  - 기존 단언의 좌변 `stop.{0,100}round N`은 **어느 루브릭에서도 매치되지 않는다**
    (실측 전부 False). 현재 통과는 전적으로 우변 `after round N.{0,100}stop`에 의존하며,
    좌변은 순수한 잠재 오탐 여지다. 그래서 추가가 아니라 대체가 맞다.
- **R7.3** 두 오편집 시나리오를 **구분해** 기록한다. 뭉개면 서술이 과장되거나 축소된다.
  - **치환 후 테스트 미갱신**: spec-rubric을 3으로 바꾸고 `:231` 단언을 갱신하지 않으면
    정상적으로 깨진다(실측 시뮬레이션 결과 매치 False). 조용한 통과가 아니다.
  - **치환 없이 추가**: 한 루브릭에 `after round 2`와 `after round 3` 문장이 공존하면,
    기존 우변 양성 단언은 남은 round 2 문장으로 매치되어 **통과한다.** 이쪽이 실현
    가능한 조용한 통과이며 R7.1의 개수 고정이 이를 막는다.
- **R7.4** 편집 후 `grep -n 'After round' dot_claude/skills/quality-goal/references/*.md`로
  spec=3·plan=2·code=3을 눈으로 확인하는 절차를 검증 단계에 포함한다.

## Acceptance criteria

각 기준은 명시된 명령의 종료 코드 또는 출력으로 판정한다. `$SK`는
`dot_claude/skills/quality-goal`, `$V`는 `$SK/scripts/validate_review.py`,
`$Q`는 `$SK/scripts/quality_state.py`, `$BASE`는
`6d8ccad16b4f8345130fe56913a2eead4169030f`를 가리킨다.

### #44 (R1)

- **AC-1** [실행] `open_findings` 7필드를 모두 갖춘 유효한 prior와 라운드 2 리뷰로
  `python3 $V validate --input <r2> --artifact plan --prior <prior>` → exit 0,
  `{"valid":true,"errors":[]}`.
- **AC-2** [실행] `open_findings[0]`에서 7필드 중 하나를 제거하면 exit 2이고 errors에
  그 필드명이 나타난다. 7필드 각각에 대해 반복한다(`subTest`).
- **AC-3** [실행] `open_findings[0].severity`를 `"Trivial"`로 바꾸면 exit 2.
- **AC-4** [실행] `open_findings[0]`에 `extra` 키를 넣으면 exit 2이고 errors에
  `'extra'`가 나타난다 (R1.3).
- **AC-5** [실행] `open_findings`에 같은 `id`가 2개면 exit 2 (R1.4).
- **AC-6** [실행] `open_finding_ids: ["PLAN-001"]`인데 `open_findings`에 `PLAN-001`이
  없으면 exit 2 (R1.5 커버리지).
- **AC-7** [실행] `open_finding_ids: ["PLAN-001"]`이고 `open_findings`가
  `PLAN-001`(blocker) + `PLAN-002`(Medium, 비-blocker)를 담으면 exit 0 — 상위집합 허용
  (R1.5 역방향 비요구).
- **AC-8** [실행] `resolved_finding_ids`가 `open_finding_ids`와 ID를 공유하면 exit 2
  (R1.6 교집합).
- **AC-9** [실행] `{"open_finding_ids": []}`만 담은 prior로 라운드 2 리뷰 검증 → exit 0
  (R1.7 하위 호환).
- **AC-10** [실행] `record-review` 라운드 2 경로(내부 prior가 ID만 담는 경로)가 계속
  성공한다 (R1.7).
- **AC-11** [문서+테스트] `SKILL.md` 본문이 라운드 2+ 리뷰어 입력으로 open finding의
  설명·증거 위치·요구 해소책·해소 주장을 보내라고 지시하고, 해소된 항목은 ID만 보낸다고
  명시한다. `test_content_contracts.py`의 계약 테스트가 이를 단정한다 (R1.8).
- **AC-12** [문서+테스트] `SKILL.md`가 구조화된 prior를 `reviews[artifact][*].path`의
  이전 리뷰 JSON에서 조립하라고 지시하고, 계약 테스트가 이를 단정한다 (R1.9).
- **AC-13** [문서+테스트] `quality-reviewer.md`가 라운드 2+에서 전달받은 각 open
  finding의 해소 여부를 판정해 `evidence`에 기록하고 재진술 시 기존 ID를 재사용하도록
  규정하며, 계약 테스트가 이를 단정한다 (R1.10).
- **AC-46** [실행] prior에 최상위 unknown 키(`open_finding`)를 넣으면 exit 2이고 errors에
  `'open_finding'`이 나타난다 (R1.11).
- **AC-47** [실행] `open_findings[0]`의 앞 5개 문자열 필드 각각을 `""`와 `"   "`로 두면
  exit 2 (R1.2 비어 있지 않은 문자열, `subTest` 10회).
- **AC-48** [실행] `resolution_claim`·`resolution_evidence`를 `null`로 두면 exit 0이고,
  정수 `1`로 두면 exit 2 (R1.2 문자열-또는-null).
- **AC-49** [실행] `resolved_finding_ids`에 같은 ID가 2개면 exit 2, 원소가 정수면 exit 2
  (R1.6 중복·타입).

### #37 (R2)

- **AC-14** [실행] `verdict=REVISE`, `blockers=[]`, `verified:false` evidence 1개를
  담은 리뷰로 `python3 $Q record-review-unverified --state S --review R --artifact-digest D`
  → exit 0. 결과 상태의 `review_unverified_retry`가
  `{artifact, round, attempts: 1, unverified_claims: [...], discarded_reviews: [R]}`이고,
  `rounds[artifact]`가 **증가하지 않는다** (R2.2, R2.7).
- **AC-15** [실행] 같은 입력에서 `blockers`가 비어 있지 않으면 exit 2 (R2.3).
- **AC-16** [실행] 같은 입력에서 모든 evidence의 `verified`가 `true`면 exit 2 (R2.3).
- **AC-17** [실행] `verdict`가 `PASS` 또는 `BLOCKED`면 exit 2 (R2.3).
- **AC-18** [실행] 잘못된 스테이지(예: `IMPLEMENTING`)에서 호출하면 exit 2 (R2.4-3).
- **AC-19** [실행] `round`가 `rounds[artifact] + 1`이 아니면 exit 2 (R2.4-5).
- **AC-20** [실행] AC-14 성공 직후 같은 (아티팩트, 라운드)로 다시 호출하면 exit 3이고
  stderr가 `REVIEWER_UNVERIFIED_PERSISTS`를 담는다 (R2.5).
- **AC-21** [실행] AC-20의 거부 후에도 상태 `stage`는 리뷰 스테이지 그대로이며 터미널이
  아니다 → 이후 `set-artifact --kind report`가 exit 0으로 성공한다 (R2.6, #43 재생산
  방지). 근거: `set_artifact`는 `_require_active`를 호출해 터미널 스테이지에서
  `TransitionError`를 던진다(`quality_state.py:108-113`, `:288-312`).
- **AC-22** [실행] AC-14 후 정상 리뷰로 `record-review`를 호출하면 exit 0이고 결과
  상태의 `review_unverified_retry`가 `null`이다 (R2.8).
- **AC-23** [문서+테스트] `SKILL.md`가 R2.1의 세 조건(REVISE·blockers 비어 있음·미검증
  evidence 존재)과 "라운드를 소모하지 않는다"·"같은 라운드로 재기동"·"(아티팩트,
  라운드)당 1회"·"반복 시 REVIEWER_UNVERIFIED_PERSISTS로 BLOCKED"를 명시하고, 계약
  테스트가 이를 단정한다 (R2.9).
- **AC-24** [문서+테스트] `SKILL.md`가 그 BLOCKED 종결이 리뷰어 역량 한계이며
  코드·설계 실패가 아님을 기록하도록 지시하고, 계약 테스트가 이를 단정한다 (R2.9).
- **AC-25** [문서+테스트] `quality-reviewer.md`가 미검증 조건을 `verified: false`
  evidence로 표시하도록 규정하고, 계약 테스트가 이를 단정한다 (R2.10).
- **AC-50** [문서+테스트] `SKILL.md`가 재수행 입력에 (a) 미검증 조건을 해소할 증거 경로와
  (b) 재수행 중 아티팩트 개정 금지를 명시하고, 계약 테스트가 이를 단정한다 (R2.2).
- **AC-51** [실행] 스키마 위반 리뷰(예: `evidence` 항목에서 `claim` 제거)를
  `record-review-unverified`에 넘기면 exit 2이고 상태 파일이 바이트 동일하게 유지된다
  (R2.4-4).
- **AC-52** [실행] `--artifact-digest`를 생략하면 argparse가 exit 2로 거부한다. spec
  아티팩트에서 등록된 파일의 실제 digest와 다른 값을 넘기면 exit 2이고 상태가 불변이다
  (R2.4-1, R2.4-2 → R2.2 강제).
- **AC-53** [실행] `rounds[artifact]`가 이미 `ROUND_LIMITS[artifact]`인 상태에서
  호출하면 exit 3이다 (R2.4-6).
- **AC-54** [실행] 두 번째 시도가 거부되기 전, `discarded_reviews`가 첫 시도의 리뷰 경로를
  담고 있다 (R2.7).
- **AC-55** [문서+테스트] `SKILL.md`가 폐기된 리뷰의 비-blocking findings를 재수행 입력에
  담고 라운드 2+에서는 prior의 `open_findings`에도 포함하도록 지시하며, 계약 테스트가
  이를 단정한다. 아울러 그 상위집합 prior가 검증을 통과함을 AC-7이 이미 보장한다 (R2.11).

### #38 (R3)

- **AC-26** [실행] `review.schema.json`을 로드해 evidence 항목의 `required`가
  `{claim, location, verified}`(집합 동등)이고 `properties.verified.type == "boolean"`
  이며 `additionalProperties`가 `false`임을 단정 → 성공 (R3.1).
- **AC-27** [실행] evidence 항목에서 `verified`를 뺀 리뷰 검증 → exit 2, errors에
  `verified`가 나타난다 (R3.2).
- **AC-28** [실행] `verified`를 문자열 `"false"` 또는 정수 `0`으로 두면 exit 2 (R3.2).
- **AC-29** [실행] `verdict=PASS`이고 evidence에 `verified:false`가 1개 있으면 exit 2,
  errors가 미검증 항목 존재를 명시한다 (R3.3).
- **AC-30** [실행] `verdict=REVISE`이고 evidence에 `verified:false`가 있으면 exit 0
  (R3.4).
- **AC-31** [실행] `SchemaDriftTests`가 통과한다 — 스키마 evidence 필수 필드 집합 ==
  `EVIDENCE_FIELDS` (R3.5).
- **AC-32** [문서+테스트] `quality-reviewer.md`가 모든 evidence 항목에 `verified`를
  채우고 `false`일 때 이유를 `claim`에 적도록, BLOCKED payload에도 같은 규칙이
  적용되도록 규정하며, 계약 테스트가 이를 단정한다 (R3.6).
- **AC-33** [실행] `verdict=PASS` + `verified:false` 리뷰로 `record-review`를 호출하면
  exit 2로 거부되고, `rounds[artifact]`가 증가하지 않는다 (R3.7).
- **AC-56** [실행] `verified: true`(boolean)가 정상 통과하는 동시에 같은 evidence 항목의
  `claim`을 `""`로 두면 exit 2다 — 비어 있지 않은 문자열 검사가 문자열 필드에만
  적용되고 boolean 필드에는 적용되지 않음을 증명한다 (R3.2 `EVIDENCE_STRING_FIELDS`).

### 버전·문서 (R4)

- **AC-34** [실행] `SKILL.md` frontmatter의 `version`이 `2.0.0`이다 (R4.1).
- **AC-35** [실행] `test_content_contracts.py`의 frontmatter 고정 테스트가 통과하고,
  기대 키 집합이 `{name, version, description, argument-hint,
  disable-model-invocation, model, effort}` 그대로다 (R4.2).
- **AC-36** [실행] `docs/quality-goal-maintenance.md`의 "추적 중인 후속 작업" 목록이
  `#36`, `#39`, `#43`을 담고 `#37`·`#38`·`#44`를 담지 않는다 (R4.3).
- **AC-37** [실행] `docs/development/2026-08-27-quality-goal-review-loop/`에 `spec.md`,
  `plan.md`, `report.md`가 존재한다 (R4.4).

### 라운드 한도 (R6)

- **AC-57** [실행] `quality_state.ROUND_LIMITS == {"spec": 3, "plan": 2, "code": 3}`
  이고 `tests/test_quality_state.py`의 상수 고정 테스트가 이를 단정한다 (R6.1, R6.4).
- **AC-58** [실행] spec 아티팩트에서 라운드 1·2를 REVISE로 기록한 뒤 라운드 3을
  `record-review`로 기록하면 exit 0으로 성공한다. 라운드 3이 REVISE·blocker면 그 시점에
  `NEEDS_REDESIGN`으로 전이한다(한도 도달). 라운드 4는 exit 3으로 거부된다 (R6.1).
- **AC-59** [실행] `grep -n 'After round' $SK/references/*.md`가 정확히 3줄을 내고
  spec=3, plan=2, code=3이다. 아울러 `SKILL.md`의 spec 서술 3곳이 3이고 plan 서술
  3곳이 2, code 서술 2곳이 3이다 (R6.2, R6.3, R7.4).
- **AC-60** [실행] `record-review-error`가 spec 아티팩트에 대해 `--round 3`을 수용한다
  (R6.5).

### 루브릭 단언 (R7)

- **AC-61** [실행] 세 루브릭 계약 테스트가
  `re.findall(r"after round (\d+) without a passing gate", lower)`로 각각
  `["3"]`, `["2"]`, `["3"]`을 단정하며, 기존 `stop.{0,100}round N|…` 형태의
  `assertRegex`는 **남아 있지 않다** (R7.1, R7.2).
- **AC-62** [실행] 변이 검증: `spec-rubric.md`에
  `- After round 9 without a passing gate, stop and record \`NEEDS_REDESIGN\`.` 문장을
  **추가**(치환 아님)하면 AC-61의 spec 단언이 `["3","9"]`로 실패한다. 즉 R7.3의
  "치환 없이 추가" 시나리오가 잡힌다. 확인 후 즉시 복원한다 (R7.3).
- **AC-63** [실행] 변이 검증: `plan-rubric.md:33`을 `round 3`으로 바꾸면 AC-61의 plan
  단언이 실패한다. 즉 R6.2가 경고하는 교차 오편집이 잡힌다. 확인 후 즉시 복원한다
  (R6.2, Non-goal 10).

### 호환성·회귀 (R5)

- **AC-38** [실행] `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s
  dot_claude/skills/quality-goal/tests -p 'test_*.py'` → exit 0, 실패 0건, 총 테스트
  수가 180 초과 (R5.1, R5.4).
- **AC-39** [실행] evidence 형태를 고정한 **4곳**이 모두 `verified`를 갖는다:
  `tests/fixtures/review-valid-plan.json`, `tests/fixtures/review-high-finding.json`,
  `tests/test_validate_review.py`의 `valid_review()`,
  `tests/test_quality_state.py`의 `valid_review()`.
  `tests/fixtures/verification-pass.json`은 evidence 배열이 없으므로 변경 대상이
  아니며, 변경되지 않았음을 확인한다 (R5.1).
- **AC-40** [실행] `tests/test_quality_state.py`의 상태 키 집합 단언에
  `review_unverified_retry`가 포함된다 (R5.2).
- **AC-41** [실행] `grep -rn 'output-schema' $SK` 결과에 `review.schema.json`이
  나타나지 않는다 (R5.3).
- **AC-42** [실행] 변이 검증을 **신규 규칙 전수**에 수행한다. 대상 목록(R5.5와 동일):
  (1) R1.5 커버리지, (2) R1.11 prior unknown 키, (3) R1.2 문자열-또는-null,
  (4) R1.6 교집합, (5) R2.3 트리거 조건 검사, (6) R2.4-2 digest 교차 검사,
  (7) R2.5 1회 상한, (8) R3.3 PASS 금지, (9) R3.2 boolean 타입 검사,
  (10) R6.1 한도 값, (11) R7.1 루브릭 개수 단언(AC-62·AC-63이 담당).
  각 항목을 소스에서 무력화하면 대응 테스트가 실패해야 하고, 확인 후 즉시 복원한다.
- **AC-43** [실행] **변경 파일 allow-list 준수.** 최종 커밋 후 PR 생성 전에
  `git diff --name-only $BASE...HEAD`를 실행하고 그 출력을
  `grep -vE '^(dot_claude/skills/quality-goal/|dot_claude/agents/quality-reviewer\.md$|docs/)'`로
  거른 결과가 **비어 있다**(grep exit 1). base revision 기준이므로 커밋 후에도 공허하지
  않다 (Non-goal 12).
- **AC-44** [실행] **#43 블록 불변.** 최종 커밋 후 다음이 exit 0이다 — 행 번호가 아니라
  내용으로 앵커한다:
  ```
  git show $BASE:dot_claude/skills/quality-goal/scripts/quality_state.py \
    | sed -n '/^    recurring = next/,/REVIEW_LIMIT_EXHAUSTED/p' > base-block.txt
  sed -n '/^    recurring = next/,/REVIEW_LIMIT_EXHAUSTED/p' \
    dot_claude/skills/quality-goal/scripts/quality_state.py > head-block.txt
  diff base-block.txt head-block.txt
  ```
  두 앵커가 base revision과 작업 트리에서 동일한 9줄 블록을 추출함을 실측 확인했다
  (Non-goal 1).
- **AC-45** [실행] **배포본 불변.** `grep '^version:'
  ~/.claude/skills/quality-goal/SKILL.md`가 `version: 1.0.0`을 낸다. 그리고
  `report.md`의 실행 명령 표에 `chezmoi apply`가 없다. 세션 명령 이력은 어떤 명령으로도
  감사할 수 없으므로 기준에서 제외한다 (Non-goal 2).
- **AC-64** [문서] 아래 "요구사항 전수 대응 확인" 표가 R1.1–R7.4의 모든 요구사항을
  하나 이상의 AC에 대응시키며 누락이 없다.

## 요구사항 전수 대응 확인

| 요구사항 | 대응 AC |
|---|---|
| R1.1 | AC-1 |
| R1.2 | AC-2, AC-3, AC-47, AC-48 |
| R1.3 | AC-4 |
| R1.4 | AC-5 |
| R1.5 | AC-6, AC-7, AC-42(1) |
| R1.6 | AC-8, AC-49, AC-42(4) |
| R1.7 | AC-9, AC-10 |
| R1.8 | AC-11 |
| R1.9 | AC-12 |
| R1.10 | AC-13 |
| R1.11 | AC-46, AC-42(2) |
| R2.1 | AC-14, AC-15, AC-16, AC-17, AC-23 |
| R2.2 | AC-14, AC-50, AC-52 |
| R2.3 | AC-15, AC-16, AC-17, AC-42(5) |
| R2.4 | AC-18, AC-19, AC-51, AC-52, AC-53, AC-42(6) |
| R2.5 | AC-20, AC-42(7) |
| R2.6 | AC-21 |
| R2.7 | AC-14, AC-54 |
| R2.8 | AC-22 |
| R2.9 | AC-23, AC-24 |
| R2.10 | AC-25 |
| R2.11 | AC-55, AC-7 |
| R3.1 | AC-26 |
| R3.2 | AC-27, AC-28, AC-56, AC-42(9) |
| R3.3 | AC-29, AC-42(8) |
| R3.4 | AC-30 |
| R3.5 | AC-31 |
| R3.6 | AC-32 |
| R3.7 | AC-33 |
| R4.1 | AC-34 |
| R4.2 | AC-35 |
| R4.3 | AC-36 |
| R4.4 | AC-37 |
| R5.1 | AC-38, AC-39 |
| R5.2 | AC-40 |
| R5.3 | AC-41 |
| R5.4 | AC-38 |
| R5.5 | AC-42 |
| R6.1 | AC-57, AC-58, AC-42(10) |
| R6.2 | AC-59, AC-63 |
| R6.3 | AC-59 |
| R6.4 | AC-57 |
| R6.5 | AC-60 |
| R6.6 | Non-goal 7 (구현 부재로 판정 — AC-42에 대응 규칙 없음) |
| R7.1 | AC-61, AC-42(11) |
| R7.2 | AC-61 |
| R7.3 | AC-62 |
| R7.4 | AC-59 |

R6.6은 "무엇을 넣지 않는다"는 부정 요구사항이므로 실행 기준이 아니라 Non-goal 7의
범위 확인(AC-43의 allow-list와 코드 리뷰)으로 판정한다. 그 밖의 모든 요구사항은 하나
이상의 실행 가능한 AC에 대응한다.

## Architecture

네 항목은 **하나의 데이터 흐름**을 공유한다.

```
quality-reviewer (fresh context)
   │ review JSON (review.schema.json)
   ▼
validate_review.py validate --prior ──┐
   │                                   │ (#44) prior 입력 형태 + unknown 키
   │ (#38) evidence[].verified 규칙     │
   ▼                                   │
validate_review.py gate                │
   │                                   │
   ▼                                   │
quality_state.py record-review ────────┘  (라운드 소모, 한도 = ROUND_LIMITS ← R6)
   또는
quality_state.py record-review-unverified (#37, 라운드 비소모)
```

**#38이 기반이다.** `evidence[].verified`가 "무엇을 검증하지 못했는가"를 기계가 읽을 수
있는 유일한 신호이며, #37의 트리거 조건(R2.1)이 그 신호를 소비한다. 그래서 스키마 확장이
없으면 #37은 지시문 수준에 머문다. 반대로 구현 순서는 사용자가 지정한
#44 → #37 → #38이며, 이는 **파일 충돌 최소화 순서**다(#44가 prior 검증 함수를,
#37이 상태 머신을, #38이 스키마·evidence 검증을 각각 만진다 — 세 지점이 겹치지 않는다).
#37의 트리거 조건이 #38의 필드를 참조하므로 #37 단계에서 그 필드를 전제로 코드를 쓰고,
#38 단계에서 필드를 실제로 도입한 뒤 전체 스위트로 검증한다(D7).

**R6·R7은 독립적이다.** R6은 상수 1개와 문서·테스트의 라운드 수 동기화이고, R7은 테스트
단언 형태 교체다. 어느 것도 #44·#37·#38의 코드 경로와 교차하지 않으므로 마지막 단계에
배치한다.

### 책임 경계

| 컴포넌트 | 이 작업에서의 책임 | 바뀌지 않는 것 |
|---|---|---|
| `review.schema.json` | evidence에 `verified` 필수 필드 추가 | 나머지 필드·enum·`additionalProperties: false`·기존 `uniqueItems` 2곳 |
| `validate_review.py` | prior 확장 검증과 unknown 키(R1), `verified` 검증·PASS 금지·문자열 필드 분리(R3) | `evaluate_gate`의 게이트 사유 목록, 점수 임계 |
| `quality_state.py` | `record-review-unverified` 서브커맨드 + `review_unverified_retry` 상태 키 + `ROUND_LIMITS["spec"]` 값 | `record_review`의 자동 전이 블록(#43), `ALLOWED_TRANSITIONS`, `TERMINAL_STATES`, plan·code 한도 |
| `SKILL.md` | 리뷰 호출 계약 확장(R1.8·R1.9), 미검증 REVISE 정책 신설(R2.9·R2.11), spec 라운드 수 3(R6.3), version 2.0.0 | 스테이지 표의 나머지, 승인 게이트, Codex 계약, 안전 규칙, plan·code 라운드 수 |
| `quality-reviewer.md` | prior 소비 규칙(R1.10), `verified` 기입 규칙(R3.6) | frontmatter, 도구 목록, BLOCKED payload 8필드 규칙 |
| `references/spec-rubric.md` | 라운드 3 (R6.2) | 점수 배분, 심각도 정의, 나머지 문장 |
| `references/plan-rubric.md`, `code-rubric.md` | 없음 | 전부 |
| `tests/` | 기존 evidence 형태·한도·라운드 단언 갱신 + 신규 회귀 테스트 | 기존 테스트의 의도 |

### 왜 `record-review-unverified`가 자체 서브커맨드인가

기존 `record_review_validation_failure`(`quality_state.py:600`)가 malformed 출력에
대해 같은 모양(1회 재시도 → 종결)을 이미 구현한다. 그러나 두 경로는 의미가 다르다.
malformed은 **스키마 위반**이고 미검증 REVISE는 **스키마를 통과한 유효한 리뷰**다. 같은
상태 키를 공유하면 `REVIEW_OUTPUT_INVALID`와 `REVIEWER_UNVERIFIED_PERSISTS`가 섞여
종결 사유가 부정확해지고, 이는 #37이 고치려는 바로 그 문제(잘못된 종결 사유 귀속)를
재생산한다. 그래서 별도 키·별도 서브커맨드로 분리한다.

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
- **최상위 unknown 키는 오류다**(R1.11).
- 하위 호환: 두 선택 필드가 없으면 기존 동작과 동일.

### I2. `review.schema.json` evidence 항목 (확장 후)

```json
{ "claim": "…", "location": "…", "verified": true }
```

`verified == false`는 그 claim을 확인하지 못했다는 뜻이며, 이유는 `claim` 안에 적는다.
`claim`·`location`은 비어 있지 않은 문자열, `verified`는 boolean이다.

### I3. `record-review-unverified` CLI

```
python3 quality_state.py record-review-unverified \
  --state <state.json> --review <review.json> --artifact-digest <sha256>
```

| 조건 | 종료 코드 | 효과 |
|---|---|---|
| R2.1 만족 + R2.4 전제 6개 통과, 첫 시도 | 0 | `review_unverified_retry.attempts = 1`, `discarded_reviews`에 리뷰 경로 append, 상태 JSON을 stdout에 출력, 라운드 불변 |
| R2.1 불만족(blockers 있음 / 미검증 없음 / verdict 부적합) | 2 | 상태 불변 |
| digest 형식 오류 또는 등록 아티팩트와 불일치 | 2 | 상태 불변 |
| 스테이지 불일치 / 스키마 위반 / 라운드 불일치 | 2 | 상태 불변 |
| `round > ROUND_LIMITS[artifact]` | 3 | 상태 불변 |
| 같은 (아티팩트, 라운드) 두 번째 시도 | 3 | 상태 불변, stderr에 `REVIEWER_UNVERIFIED_PERSISTS` |
| `--artifact-digest` 누락 | 2 | argparse 거부, 상태 불변 |

종료 코드는 기존 매핑(`StateError` → 2, `TransitionError` → 3)을 그대로 따른다
(`quality_state.py:1189-1194`).

### I4. 상태 키 (추가)

```json
"review_unverified_retry": null
```

또는

```json
"review_unverified_retry": {
  "artifact": "code",
  "round": 2,
  "attempts": 1,
  "unverified_claims": ["결정적 명령을 재실행하지 못했다 — Read/Grep/Glob만 보유."],
  "discarded_reviews": [".claude/quality-state/<task-id>/code-review-round2-a.json"]
}
```

`record_review` 성공 시 `None`으로 초기화된다.

### I5. 오케스트레이터 흐름 (라운드 2 이상)

1. 이전 라운드 리뷰 JSON들을 `reviews[artifact][*].path`에서 읽는다. 폐기된 리뷰가
   있으면 `review_unverified_retry.discarded_reviews`도 읽는다.
2. open findings(blocker + 미해소 advisory + 폐기 리뷰의 비-blocking findings)를 골라
   I1의 `open_findings`를 조립하고, 각 항목에 자신의 해소 주장·증거를 붙인다. 해소
   확인된 ID는 `resolved_finding_ids`로.
3. 그 내용을 리뷰어 프롬프트에 넣어 새 quality-reviewer를 기동한다.
4. 반환 JSON을 태스크 상태 디렉터리에 저장한다.
5. R2.1 조건이면 → `record-review-unverified` → (3)으로 같은 라운드 재기동, 이때 미검증
   조건의 증거 경로와 폐기 리뷰의 비-blocking findings를 추가한다. 두 번째면 보고서
   등록 후 `transition --to BLOCKED --reason REVIEWER_UNVERIFIED_PERSISTS:<artifact>`.
6. 아니면 → `validate` (I1 prior 전달) → `gate` → `record-review`.

## Failure behavior

| 실패 | 발현 | 처리 |
|---|---|---|
| prior의 `open_findings` 형태 위반 | `validate` exit 2, errors에 경로·필드명 | 오케스트레이터가 prior 조립을 고쳐 재실행. 리뷰어 응답 문제가 아니므로 `record-review-error` 대상이 아니다 |
| prior 최상위 unknown 키 | `validate` exit 2, errors에 키 이름 | 같음. 오타로 구조화 prior가 조용히 무력화되는 것을 막는다 |
| `open_finding_ids` 커버리지 위반 | `validate` exit 2 | 같음. 상태가 보존한 blocker를 prior에서 빠뜨렸다는 신호 |
| 리뷰에 `verified` 누락 또는 비-boolean | `validate` exit 2 / `record-review` exit 2 | 리뷰어 응답 계약 위반 → `record-review-error` → 1회 재시도 → `BLOCKED`/`REVIEW_OUTPUT_INVALID`(기존 경로) |
| PASS + 미검증 evidence | `validate` exit 2, `record-review` exit 2 | 같음. 라운드는 소모되지 않는다 |
| 미검증 사유 REVISE 1회 | `record-review-unverified` exit 0 | 같은 라운드로 범위 좁힌 재기동. 라운드 불변. 폐기 리뷰 경로와 비-blocking findings 보존 |
| 미검증 사유 REVISE 2회 | `record-review-unverified` exit 3 | 보고서 렌더링·등록 후 `transition --to BLOCKED --reason REVIEWER_UNVERIFIED_PERSISTS:<artifact>`. 리뷰어 역량 한계로 기록 |
| 실체 있는 REVISE를 재수행으로 세탁 시도 | `record-review-unverified` exit 2 | 정상 `record-review` 경로로 되돌린다 |
| 재수행 중 아티팩트를 개정 | `record-review-unverified` exit 2 (digest 불일치) | 개정을 되돌리거나, 개정이 정당하면 정상 라운드로 기록한다 |
| spec 라운드 3 후에도 게이트 실패 | `record-review`가 `NEEDS_REDESIGN`으로 전이 | 한도 도달. 기존 동작이며 R6은 한도 값만 3으로 올린다 |
| 루브릭 오편집(plan을 3으로) | AC-61의 plan 단언 실패 | 편집 되돌리고 `grep -n 'After round'`로 재확인 |
| 루브릭 문장 추가(치환 누락) | AC-61의 개수 단언 실패 | 기존 문장을 제거해 파일당 1개로 만든다 |
| 신규 테스트가 기존 180개를 깨뜨림 | `unittest` 실패 | 원인이 fixture 형태면 갱신(R5.1), 원인이 계약 모순이면 되돌리고 Spec 개정 |
| 기존 상태 파일에 `review_unverified_retry` 없음 | 없음 | `state.get(...)`으로 관용적 읽기. `schema_version`은 1 유지 |

**롤백.** 커밋 단위 `git revert` 또는 `git branch -D fix/quality-goal-review-loop`.
배포하지 않으므로 `~/.claude/` 배포본은 영향받지 않는다. 파괴적 작업·마이그레이션·외부
상태 변경이 없다.

## Security and risk

- **시크릿 없음.** 변경 파일은 Markdown 지침·JSON 스키마·Python 검증기·테스트다.
  자격증명을 읽거나 쓰지 않는다. `.gitignore`의 시크릿 규칙(`:1-11`)을 건드리지 않으며,
  Non-goal 12의 allow-list가 `.gitignore` 자체를 변경 대상에서 제외한다.
- **신뢰 경계.** 리뷰어 출력은 신뢰하지 않는 입력으로 계속 취급한다. 이번 변경은 그
  불신을 **강화**한다(#38: PASS 주장을 evidence와 교차 검증). prior 입력은
  오케스트레이터가 만들므로 내부 데이터이나, 형태 검증과 unknown 키 거부(R1.11)를 붙여
  조립 오류를 조용히 넘기지 않는다.
- **최대 위험 — fail-open 도입.** `record-review-unverified`가 라운드를 소모하지 않으므로
  잘못 설계하면 무한 재수행이 된다. 완화: (a) (아티팩트, 라운드)당 1회 상한을 상태에
  기록해 결정적으로 강제(R2.5), (b) 트리거 조건을 서브커맨드가 스스로 검사해 세탁을
  차단(R2.3), (c) 재수행 중 아티팩트 개정을 digest로 차단(R2.4-2), (d) 두 번째 시도는
  `TransitionError`(exit 3)로 거부.
- **두 번째 위험 — #43 재생산.** 새 실패 경로가 스스로 터미널 전이하면 보고서 등록 시점이
  다시 사라진다. 완화: R2.6이 자동 전이를 금지하고 AC-21이 보고서 등록 가능성을 실증한다.
- **세 번째 위험 — advisory finding 유실.** R2.1의 트리거가 `blockers == []`이므로
  advisory findings만으로 정당화된 REVISE도 폐기 경로를 탄다. 완화: R2.7의
  `discarded_reviews`와 R2.11의 재수행 입력 승계.
- **네 번째 위험 — `verified` 필수화의 파급.** 기존 fixture·헬퍼·테스트가 evidence 형태를
  고정한다. 완화: R5.1이 정확히 4곳을 열거하고 AC-38·AC-39가 실측한다. 필수 대신 선택
  필드로 두는 대안은 fail-open이므로 기각한다(D1).
- **다섯 번째 위험 — 루브릭 교차 오편집.** `spec-rubric.md:33`과 `plan-rubric.md:33`이
  바이트 동일하다(실측). 완화: R6.2의 개별 편집 규칙, R7.1의 값·개수 고정 단언,
  AC-63의 변이 검증, R7.4의 `grep` 눈 확인.
- **여섯 번째 위험 — 배포본과의 혼선.** 이 실행 자체가 배포된 v1.0.0으로 돌고 다른
  세션도 같은 배포본을 쓴다. 소스의 R6 한도 상향은 **이번 실행에 적용되지 않는다** —
  이번 Spec 리뷰는 여전히 2라운드 제약을 받는다. 완화: `chezmoi apply` 금지(Non-goal 2),
  AC-45가 배포본 version이 `1.0.0`으로 남았음을 실측.
- **프로덕션 변경 없음.** 이 워크플로는 프로덕션 자원을 변경하지 않는다. `git push`는
  브랜치 push와 PR 생성으로 한정되며 머지하지 않는다.

## Test strategy

### 결정적 명령 (단일 기준선)

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s dot_claude/skills/quality-goal/tests -p 'test_*.py'
```

현재 기준선: **180개 통과**(2026-08-27 실측, exit 0). 정적 교차 확인: 세 테스트 파일의
`def test_` 개수 합이 180(47 + 39 + 94). 완료 시 이 값을 초과하며 실패 0건.

### 테스트 배치

| 파일 | 추가·수정 |
|---|---|
| `tests/test_validate_review.py` | prior 확장 수용·거부(AC-1~AC-9, AC-46~AC-49), `verified` 검증(AC-27·AC-28·AC-56), PASS 금지(AC-29)·REVISE 허용(AC-30), `SchemaDriftTests` evidence 필수 필드(AC-26·AC-31), `valid_review()` 헬퍼 갱신 |
| `tests/test_quality_state.py` | `record-review-unverified` 수용·거부 경로(AC-14~AC-22, AC-51~AC-54), 상태 키 집합(AC-40), `record-review`의 PASS+미검증 거부(AC-33), 한도 상수·라운드 3 기록·라운드 4 거부(AC-57·AC-58·AC-60), `valid_review()` 헬퍼 갱신 |
| `tests/test_content_contracts.py` | frontmatter version 2.0.0(AC-35), SKILL.md 계약(AC-11·AC-12·AC-23·AC-24·AC-50·AC-55), 리뷰어 계약(AC-13·AC-25·AC-32), spec 라운드 수(AC-59), 루브릭 단언 교체(AC-61) |
| `tests/fixtures/*.json` | 두 리뷰 fixture의 evidence에 `verified` 추가(AC-39). `verification-pass.json`은 불변 |

### 보조 검증 (테스트 외)

- 스키마 JSON 파싱: `python3 -m json.tool $SK/schemas/review.schema.json`.
- 문법: `python3 -m py_compile` 두 스크립트.
- 루브릭 라운드 수: `grep -n 'After round' $SK/references/*.md` (AC-59).
- **범위 확인은 base revision 기준으로 한다** — `git diff --name-only $BASE...HEAD`
  (AC-43)과 `git show $BASE:… | sed -n …` 블록 비교(AC-44). 작업 트리 대비 명령
  (`git status --porcelain`, 인자 없는 `git diff`)은 커밋 후 공허해지므로 범위 기준으로
  쓰지 않는다.
- 배포본 불변: `grep '^version:' ~/.claude/skills/quality-goal/SKILL.md` (AC-45).
- 변이 검증(AC-42, AC-62, AC-63): 신규 규칙 11개를 각각 임시로 무력화해 대응 테스트가
  실패함을 관찰하고 즉시 복원한다.

### 검증 카테고리 (저장소 실측)

이 저장소에는 `package.json`·`Makefile`·`justfile`·`.github/workflows`가 없다. 타입
체크·린트·빌드는 `not configured`로 기록한다(`.pre-commit-config.yaml`은 gitleaks 시크릿
스캔 전용). E2E는 스킬 번들 성격상 해당 없으며, 대신 위 보조 검증과 변이 검증이 그
역할을 한다.

## Decisions

**D1 — `verified`를 evidence의 필수 필드로 만든다 (선택 필드 기각).**
선택 필드로 두고 "없으면 검증됨"으로 해석하면, 새 계약을 무시하는 리뷰어가 기존
fail-open 동작을 그대로 얻는다 — #38이 고치려는 결함이 그대로 남는다. 필수화하면 누락이
검증 오류가 되어 기존 malformed 경로(1회 재시도 → BLOCKED)로 fail-closed하게 흘러간다.
비용은 **두 리뷰 fixture와 두 헬퍼**(총 4곳, R5.1) 갱신이며,
`tests/fixtures/verification-pass.json`은 evidence 배열이 없어 영향받지 않는다.
SemVer MAJOR가 이미 예정되어 있으므로 파괴적 변경이 허용된다.

**D2 — #38의 강제를 `validate_review`(검증)에 두고 `evaluate_gate`(게이트)에 두지 않는다.**
검증 오류로 두면 `record-review`가 리뷰를 아예 기록하지 않으므로 **라운드가 소모되지
않는다**. 게이트 실패로 두면 리뷰가 먼저 기록되어(라운드 소모) 게이트가 실패한다 — 즉
리뷰어의 계약 위반 비용을 코드 쪽 라운드로 지불하게 되고, 이는 #37이 없애려는 바로 그
현상이다. 또한 `evaluate_gate`는 `validate_review`를 먼저 호출해 오류 시 예외를 던지므로
(`validate_review.py:294-296`), 게이트에 별도 사유를 추가하면 도달할 수 없는 코드가 된다
(Non-goal 4).

**D3 — `record-review-unverified`는 자동 터미널 전이를 하지 않는다.**
기존 `record_review_validation_failure`는 두 번째 실패에서 스스로 `BLOCKED`로 전이한다
(`quality_state.py:632-633`). 그 패턴이 #43의 결함 — 전이 후
`set-artifact --kind report`가 `_require_active`의 터미널 검사에 막혀 보고서 포인터가
유실된다(실측 재현: exit 3, `.../2026-08-27-create-worktree-pr-session/report.md:196-213`).
새 경로에서 그 패턴을 복제하면 결함을 확산시키므로, 거부 사유만 반환하고 전이는
오케스트레이터에게 맡긴다. 이는 #43의 권장 수정 방향(1안)과 정합하며, #43
자체(`record_review`의 전이)는 건드리지 않는다(Non-goal 1).

**D4 — `open_findings`는 선택 필드이며 커버리지만 요구한다(필수화 기각).**
필수화하면 `record_review`가 내부적으로 만드는 prior
(`{"open_finding_ids": [...]}`, `quality_state.py:541`)가 즉시 무효가 된다. 이를
살리려면 `record_review`가 이전 라운드 리뷰 파일들을 로드해 구조화된 prior를 조립해야
하는데, (a) 리뷰 파일 부재라는 새 실패 모드가 생기고, (b) 변경이 `record_review`
내부로 확장되어 #43과 인접한 코드의 위험이 커진다. 대신 선택 필드 + 커버리지 제약 +
최상위 unknown 키 거부(R1.11)로 두고, "리뷰어에게 반드시 구조화된 prior를 보낸다"는
요구는 `SKILL.md` 계약과 계약 테스트로 고정한다. **한계를 명시한다**: 서브에이전트
프롬프트의 실제 내용은 외부에서 기계 검증할 수 없으므로 이 지점의 강제는 지시문
수준이다(Non-goal 5). 결정적 강제가 실제로 필요한 곳(PASS 남용)은 D2가 담당한다.

**D5 — `open_findings`는 `open_finding_ids`의 상위집합일 수 있다.**
집합 동등을 요구하면 blocker만 전달 가능해지고, #44의 실측 피해자
(SPEC-005·006·007·008·010은 Medium·Low)를 여전히 전달할 수 없다. 상태의
`open_finding_ids`가 blocker만 보존하기 때문이다(`quality_state.py:583`). 따라서 커버리지
(모든 blocker가 포함됨)만 요구하고 추가 항목을 허용한다. 이 허용이 R2.11의 폐기 리뷰
findings 승계도 가능하게 한다.

**D6 — #37의 트리거 조건에 `blockers == []`를 넣는다.**
`verified == false`만으로 트리거하면, 실체 있는 blocker를 가진 리뷰도 미검증 항목이
하나 있으면 무료 재수행을 얻는다. blocker가 있으면 그 라운드는 정당하게 소모되어야
한다. 반대로 blocker가 없는데 REVISE인 경우, 그 REVISE를 정당화하는 것은 미검증 조건
또는 Medium·Low findings뿐이며, 전자라면 라운드를 소모할 이유가 없다. 후자가 섞여
있을 수 있으므로 R2.11이 그 findings를 승계한다.

**D7 — 구현 순서는 #44 → #37 → #38 → R6 → R7을 유지한다.**
앞 세 항목의 순서는 사용자 지시이며 파일 충돌 최소화 순서다. #37의 트리거 조건이 #38의
`verified` 필드를 참조하는 역방향 의존이 있으므로, #37 단계에서는 그 필드를 전제로
코드를 쓰고 #38 단계 직후 전체 스위트로 두 변경의 결합을 검증한다. #37 단계 종료
시점에는 `verified`가 아직 없어 #37 신규 테스트가 실패할 수 있으며, 이는 예상된 중간
상태다 — 완료 판정은 모든 단계가 끝난 뒤의 AC-38로만 한다. R6·R7은 코드 경로가 겹치지
않으므로 마지막에 둔다.

**D8 — `review.schema.json`에는 OpenAI structured-output 제약이 적용되지 않는다.**
실측 확인: `--output-schema` 인자로 전달되는 스키마는
`references/model-routing.md:19-30`의 `codex-result.schema.json`뿐이고,
`deviations.md:231-232`가 `review.schema.json`을 "로컬 `validate_review.py` 전용이라
API로 전송되지 않으므로 `uniqueItems`가 유효하다"로 기록한다. 실제로 현재
`review.schema.json`은 이미 `uniqueItems`를 2곳(`blockers`, `evidence`)에서 쓰고 있으며
정상 동작한다 — 제약이 적용된다면 불가능한 상태다. **정정**: `uniqueItems`·lookaround의
HTTP 400 실측은 `deviations.md` **D-15**(`:217-237`)에 기록되어 있으며 D-16이 아니다.
D-16 FIX 2를 인용한 `maxTurns: 12` 턴 소진 실측과 no-PASS 규칙의 유래는 정확하다.
그럼에도 이번 확장은 `uniqueItems`를 새로 도입하지 않고 정규식 lookaround를 쓰지 않는다.

**D9 — strict-only 블록은 제거한다.**
이 작업은 standard이며 인증·인가·테넌시, 마이그레이션·백필, 프로덕션 관측성, 고위험
E2E 경로가 없다. 위협·신뢰 경계와 롤백은 위 "Security and risk"·"Failure behavior"에서
비-strict 수준으로 다뤘다. 프로덕션 변경 없음은 같은 절에 명시했다.

**D10 — 이 실행 자체의 결함 발현을 기록한다.**
이 실행은 수정 대상인 배포본 v1.0.0으로 돈다. 실제로 세 가지가 발현했고 모두
`report.md`에 기록한다 — 우회하지 않고 기록하는 것이 수정의 실증 근거이기 때문이다.
(a) Spec 리뷰 라운드 1의 첫 리뷰어가 최종 JSON 없이 idle 종료해 계약상 1회 재시도를
소비했다(D-16 FIX 2가 기록한 턴 소진과 같은 계열). (b) 재시도 리뷰어도 산출물을
Agent 결과로 전달하지 못해 트랜스크립트에서 회수해야 했다 — 리뷰어의 도구가
`Read, Grep, Glob`뿐이라 응답 채널이 최종 메시지 하나뿐인 구조적 결과다.
(c) 회수된 라운드 1 리뷰가 evidence 19건 중 2건을 산문 `"NOT VERIFIED:"`로만 표시했고
구조화된 필드가 없었다 — #38의 실증. 보고서 등록이 실패하면 보고서 파일 경로를 최종
보고에 남긴다.

**D11 — 라운드 3의 조건부 계속 진행 로직을 넣지 않는다.**
"진전이 있을 때만 라운드 3" 같은 판단 분기를 검토하고 기각했다. 그 로직이 들어갈 자리는
`record_review`이고, 거기가 #43의 자동 전이 결함이 있는 함수이며 #43은 이 작업 범위에서
제외됐다. 깨진 것을 알면서 손대지 않기로 한 함수에 판단 분기를 더하지 않는다. 또 그
조건이 막으려는 "정체된 실행"은 실전 2회 모두 개선 궤적(75→82, 80→88)이어서 관측된
적이 없다. 한도를 4 이상으로 올리지도 않는다 — 3이 필요했던 실측만 존재한다.

**D12 — 리뷰어에게 checks JSON을 공급하지 않는다.**
라운드 1 리뷰어가 "오케스트레이터 checks JSON이 공급되지 않아
`material_decisions_resolved`와 `acceptance_criteria_objective`를 교차 확인할 수 없었다"를
미검증 사유로 기록했다. 이는 설계상 정확한 관찰이나 계약 위반은 아니다 —
`SKILL.md`의 리뷰 호출 계약이 열거하는 입력에 checks가 없고, checks는 오케스트레이터
자신의 결정적 판정이기 때문이다. 리뷰어에게 그것을 보내면 리뷰어가 오케스트레이터의
판정을 재확인하는 순환이 생긴다. 계약을 넓힐지는 별건의 후속 후보로 남긴다(Non-goal 13).
