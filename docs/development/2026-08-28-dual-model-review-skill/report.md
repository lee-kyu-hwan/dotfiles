# Quality Goal Report

- Task ID: 20260828T011459Z-42-claude-codex-이중-리뷰-종합-pr-게시-스킬-추가-55cca675
- Mode: strict
- Status: NEEDS_REDESIGN
- Created: 2026-08-28
- Updated: 2026-08-28
- Source goal: #42 Claude+Codex 이중 리뷰 → 종합 → PR 게시 스킬 추가

## Classification

`auto` 요청에 대해 `strict`가 선택됐다. 근거:

- **외부 API 쓰기 + 멱등성(strict 트리거).** 스킬이 `gh pr review`/`gh pr comment`로 GitHub PR에 게시하는 계약을 정의하고, 이슈 #42 본문이 "중복 게시 방지, 어느 커밋 SHA 기준 리뷰인지 명시, 재실행 시 갱신 정책"을 핵심 차별점으로 지목한다. `routing-rules.md`의 `Public or external API compatibility ... idempotency` 트리거에 해당한다.
- **비가역 외부 노출.** 게시 계약이 틀리면 실제 PR에 되돌리기 어려운 중복·stale 댓글이 남는다. 이슈 코멘트의 CodeRabbit 실측(feedback pair 31,073건 중 56.3% rejected)이 오게시 비용을 뒷받침한다.
- **다층·다파일 변경(standard 조건).** `SKILL.md` + `references/` + `schemas/` + `scripts/` + `tests/`를 `dot_claude/skills/` 아래 신설하고 `pr-review-toolkit`·`codex` 두 외부 플러그인을 오케스트레이션한다.
- **요구사항 명시 필요(standard 조건).** 교차비평 라운드 수, synthesizer 자기편향 완화, 종료 규칙, verdict 정책을 Spec으로 확정해야 한다.
- 이슈 라벨 `enhancement`는 신규 기능임을 확인해 주지만 모드를 낮추지 않는다.
- `standard`와 `strict` 사이에서 불확실할 때 상위 모드를 선택하는 `routing-rules.md` 6번 규칙을 적용했다.

## Review history

| 아티팩트 | 라운드 | 점수 | verdict | blockers | Critical/High | 게이트 |
|---|---|---|---|---|---|---|
| Spec | 1 | 73 | REVISE | SPEC-001~004 | 4건(High) | 실패 — `score_below_85`, `verdict_not_pass`, `blockers_present`, `critical_or_high_finding`, `check_failed:acceptance_criteria_objective`, `check_failed:material_decisions_resolved` |
| Spec | 2 | 89 | REVISE | 없음 | 0건 | 실패 — `verdict_not_pass`, `check_failed:acceptance_criteria_objective` |

라운드 1에서 라운드 2로 바뀐 것:

- 점수 73 → 89.
- blocker 4건 전부 해소, Critical/High 0건.
- 라운드 1의 Medium/Low 9건(SPEC-005~SPEC-013) 전부 해소. 라운드 2 리뷰어가 각 항목의 해소를 저장소 실측 인용과 함께 확인했다.
- 라운드 2에서 새로 제기된 것은 SPEC-014·SPEC-015(Medium), SPEC-016·SPEC-017(Low)이고, SPEC-001은 잔여분이 남아 Medium으로 강등된 채 유지됐다.
- Plan 리뷰는 실행되지 않았다. Spec이 게이트를 통과하지 못해 PLAN_REVIEW 단계에 도달하지 못했다.

## Blocking-finding resolutions

| ID | 라운드 1 지적 | 적용한 해소 | 라운드 2 검증 증거 |
|---|---|---|---|
| SPEC-001 | R3.2·R3.3·R3.4·R3.5·R7.12·R7.13·R8.3·R8.4·R2.3에 결정적 수용 기준 없음 | 9건 중 8건에 AC 신설(AC-29, AC-18, AC-19, AC-7~AC-9, AC-30, AC-31, AC-32). AC를 1~22개에서 40개로 확장 | **부분 해소.** R3.3(Codex 프리플라이트)에 대응 AC가 여전히 없고, 개정에서 새로 도입한 R5.2·R6.2·R6.3·R9.2도 판정 수단이 없다. High → Medium으로 강등된 채 잔존 |
| SPEC-002 | 리뷰어 출력 스키마 루트가 배열이나 `codex --output-schema` 선례는 루트 object | 루트를 `{"verdict","summary","findings"}` object로 재정의(D10), 파생 필드는 스키마 밖 내부 표현으로 분리, 실제 `codex exec` 수락 확인 AC-27 신설 | **해소.** 라운드 2가 `codex/1.0.5/schemas/review-output.schema.json:1-11`과 대조해 선례 일치를 확인 |
| SPEC-003 | R7.6의 해소 코멘트 엔드포인트가 화이트리스트에 없음 | R7.7을 화이트리스트 범위로 축소 — 스레드 답글 대신 요약 코멘트 "해소됨" 기재 + `resolveReviewThread`(D12) | **해소.** 라운드 2가 R7.7·화이트리스트·AC-10의 정합을 확인 |
| SPEC-004 | AC-7의 "inline 3건 중 2번째 실패"가 단일 원자적 호출에서 발생 불가 | 게시를 3단계로 명시하고 inline을 `POST /pulls/{n}/reviews` 단일 원자적 호출로 확정(D11, 결정 A4). AC-7·AC-8·AC-9를 실제 실패 모드에 맞게 재작성 | **해소.** 라운드 2가 실패 표 2단계 행까지 정합함을 확인 |

## Plan approval

- Approval timestamp: 없음 — AWAITING_PLAN_APPROVAL 단계에 도달하지 못했다
- Plan digest: 없음 — Plan을 작성하지 않았다

## Changed files

구현은 시작되지 않았다. 저장소에 대한 변경은 durable 문서 두 개뿐이다.

| 파일 | 변경 |
|---|---|
| `docs/development/2026-08-28-dual-model-review-skill/spec.md` | 신규. strict Spec 개정본(466행). R1~R10, AC-1~AC-40, 결정 A1~A6, D1~D13, strict 전용 6절 |
| `docs/development/2026-08-28-dual-model-review-skill/report.md` | 신규. 이 리포트 |

`dot_claude/skills/dual-review/`는 만들어지지 않았다. `.gitignore`는 변경되지 않았다. 커밋·푸시·PR 생성은 수행하지 않았다.

## Verification evidence

구현 전 단계에서 실제로 실행한 명령과 결과:

| 명령 | 종료 코드 | 증거 |
|---|---|---|
| `gh issue view 42 --json title,body,labels,comments` | 0 | 이슈 본문과 Codex deep research 코멘트를 요구사항 입력으로 확보 |
| `gh issue view 29 --json title,state,body` | 0 | #29가 `OPEN`·미구현임을 확인 → D8의 근거 |
| `git rev-parse --show-toplevel`, `git status --porcelain` | 0 | 워크트리 루트 확인, dirty 경로 0건 |
| `codex --version` | 0 | `codex-cli 0.150.1` |
| `codex exec --sandbox read-only --ephemeral --model gpt-5.6-sol -c model_reasoning_effort="low" "Reply with one non-empty line."` | 0 | 모델 응답 `Acknowledged.` — strict 라우팅 모델 프리플라이트 통과 |
| `gh --version` | 0 | `gh version 2.98.0` |
| `gh auth status` | 0 | 계정 `lee-kyu-hwan`, 스코프 `gist, project, read:org, repo, user, workflow` |
| `gh api graphql`(Mutation 인트로스펙션) | 0 | `resolveReviewThread`·`unresolveReviewThread`·`minimizeComment` 존재 확인 → R7.7의 실현 가능성 근거 |
| `gh pr list --limit 5 --json number,title,headRefName` | 0 | 열린 PR #31·#32 확인. 현재 브랜치에는 PR 없음 |
| `git check-ignore -v .claude/quality-state/` | 0 | `.gitignore:25`에 등록됨 — 런타임 상태가 `git status`에 노출되지 않음 |
| `quality_state.py capture-baseline` | 0 | `base_revision=6d8ccad16b4f8345130fe56913a2eead4169030f`, `initial_dirty_paths=[]` |
| Spec 섹션·플레이스홀더 자체 검증(`grep`) | 0 | 템플릿의 17개 절 전부 존재, 플레이스홀더 0건, strict 블록 유지, AC 번호 중복 0건 |
| `validate_review.py validate`(Spec 라운드 1) | 0 | `{"valid":true,"errors":[]}` |
| `validate_review.py gate`(Spec 라운드 1) | 3 | `passed:false` — 6개 사유 |
| `validate_review.py validate --prior`(Spec 라운드 2) | 0 | `{"valid":true,"errors":[]}` |
| `validate_review.py gate --prior`(Spec 라운드 2) | 3 | `passed:false` — `verdict_not_pass`, `check_failed:acceptance_criteria_objective` |

구현이 없으므로 코드 검증 범주는 전부 미실행이다.

- 단위 테스트: **not configured / 미실행.** `dot_claude/skills/dual-review/tests/`가 아직 존재하지 않는다. 저장소의 기존 결정적 테스트는 `dot_claude/skills/quality-goal/tests/`이며 이번 변경 범위 밖이다.
- 타입 체크: **not configured.** 저장소 루트에 `package.json`·`pyproject.toml`·`tsconfig.json`이 없다.
- 린트: **not configured.** 저장소 루트에 린터 설정 파일이 없다.
- 빌드: **not configured.** 저장소 루트에 `Makefile`·빌드 스크립트가 없다.
- E2E: **미실행.** Spec의 고위험 E2E 검증(AC-27, AC-37, 수동 게시 E2E)은 모두 구현 이후 단계이므로 도달하지 못했다.

## Remaining advisory findings

| ID | 심각도 | 내용 | 영향 | 후속 조치 |
|---|---|---|---|---|
| SPEC-001(잔여) | Medium | R3.3(Codex 프리플라이트), R5.2(빈 evidence 반박 미채택), R6.2(5축 판정), R6.3(3분류), R9.2(SemVer)에 결정적 수용 기준이 없다 | 게이트 조건 `acceptance_criteria_objective`가 확인되지 않는 직접 원인 | R3.3은 AC-28 계약 테스트 항목에 프리플라이트 지시 문구를 포함. R5.2는 critique 스키마가 비어 있지 않은 `evidence`를 required로 강제하고 빈 반박 미채택을 단위 테스트로 고정. R6.2·R6.3은 `schemas/synthesis.schema.json`이 다섯 축 필드와 `agreed\|disputed\|unresolved` enum을 required로 강제하도록 스펙에 명시하고 픽스처 테스트로 확인. R9.2는 AC-38의 절 검사에 버전 정책을 포함 |
| SPEC-014 | Medium | 엔드포인트 화이트리스트가 `gh` CLI 명령·REST `(method, path)`·GraphQL 오퍼레이션명 세 층위를 한 표에 섞고, AC-14는 `(method, path)`만 판정한다 | `gh` CLI와 GraphQL 호출이 화이트리스트 검사에서 빠질 수 있다 | 화이트리스트를 `(kind, method, path_or_operation)` 3튜플 단일 표기로 정규화하고, 주입 가능한 GitHub 클라이언트 인터페이스의 메서드 집합을 스펙에 열거한 뒤 AC-14를 그 표기 기준으로 재작성 |
| SPEC-015 | Medium | AC-37이 "스키마 유효 계획 JSON"을 판정 조건으로 삼지만 `plan.json`의 스키마가 정의돼 있지 않다 | AC-37의 합격 조건이 기계적으로 판정 불가능 | `schemas/publish-plan.schema.json`(루트 object)을 추가해 AC-26 검사 대상에 포함하거나, AC-37을 이미 판정 가능한 술어(종료 코드 0 + 쓰기 호출 0건 + 최상위 키 집합 존재)로 대체 |
| SPEC-016 | Low | AC-27이 실제 `codex exec`를 요구하면서 CLI 미설치·모델 거부·네트워크 실패 시의 기록 규칙을 정의하지 않았다 | 외부 의존 불가 시 검증 결과를 무엇으로 기록할지 불명확 | AC-27에 `blocked`/`not verified` 기록 규칙을 추가하고 임의 통과를 금지 |
| SPEC-017 | Low | R3.1 매핑의 토큰 신호(`#`, `type `, `class `)가 과도하게 넓어 `comment-analyzer`·`type-design-analyzer`가 사실상 상시 선택된다 | 실행 비용 증가, out-of-scope 제안 비율 상승(이슈가 인용한 CodeRabbit 56.3% rejected와 같은 방향) | 파일 확장자별 주석 토큰 표로 한정하거나 최소 매치 건수 임계값을 도입 |

리뷰어가 명시한 검증 한계: 라운드 1 시점의 `spec.md` 원본이 같은 경로에 덮어써져 보존되지 않아, 라운드 2의 신규 지적이 개정으로 새로 도입된 것인지 라운드 1에도 존재했는지 확인할 수 없었다. 그래서 어느 것도 신규 blocker로 승격되지 않았고 `new_blocker_evidence`는 전부 `null`이다.

## Final status

- Status: `NEEDS_REDESIGN`
- Machine-readable reason: `REVIEW_LIMIT_EXHAUSTED:spec` (상태 파일의 `status_reason` 실제 값)

Spec 리뷰의 라운드 한도(최대 2)를 소진했고 라운드 2의 게이트가 `verdict_not_pass`와 `check_failed:acceptance_criteria_objective`로 실패했다. `spec-rubric.md`의 "After round 2 without a passing gate, stop and record `NEEDS_REDESIGN`" 규칙에 따라 워크플로를 중단했다.

이것은 설계가 틀렸다는 판정이 아니다. 라운드 2 결과는 점수 89(임계 85 이상), blocker 0건, Critical/High 0건이었고, 남은 것은 Medium 3건·Low 2건의 자문성 지적이다. 워크플로가 중단된 이유는 그 지적들이 `acceptance_criteria_objective` 게이트 조건에 직접 걸리는데 남은 개정 라운드가 없기 때문이다.

다음 결정은 사용자의 것이다. 새 워크플로를 시작하면 이 Spec 개정본(466행, AC-40개)이 출발점이 되고, 위 "Remaining advisory findings" 표의 후속 조치 5건이 첫 라운드에서 반영해야 할 목록이다.

## 게이트 후 Spec 개정 (2026-08-28, 사용자 지시)

워크플로가 `NEEDS_REDESIGN`으로 종료된 뒤, 사용자 결정에 따라 남은 자문성 지적 5건을 게이트 없이 Spec에 반영했다. 이 실행은 터미널 상태라 `state.json`의 `artifact_digests.spec`(`d73311b5…`)에 묶이지 않으므로, 개정본은 **다음 워크플로의 입력**이지 이번 실행의 산출물이 아니다.

개정 후 Spec: 572행, 요구사항 55건(R1.1~R10.3), 수용 기준 47건(AC-1~AC-47), SHA-256 `e113dcd2b9d922dc4eb11c95732c38d0be96257e9f44e0e9501615e0b567fdee`. 요구사항 55건 전부가 추적표에 등재되고 표가 참조하는 AC 47건이 전부 실재함을 기계 검사로 확인했다(누락 0, 유령 0).

| finding | 반영 내용 |
|---|---|
| SPEC-001 (잔여) | 판정 수단이 없던 5개 요구사항을 각각 닫았다. **R3.3** → AC-28에 Codex 프리플라이트 단계와 실패 시 단일 리뷰 승인 경로의 지시 문구 존재 검사를 추가. **R5.2** → AC-41 신설: `critique.schema.json`이 `evidence`를 `required` + `minItems: 1`로 강제하고, 빈 반박이 새 근거 계산·채택 목록 어디에도 반영되지 않음을 단위 테스트로 확인. **R6.2** → AC-42 신설: `synthesis.schema.json`이 다섯 축(`truth`, `introduced_by_pr`, `location_validity`, `evidence`, `actionability`)을 전부 `required`로 강제. **R6.3** → AC-43 신설: 분류를 `agreed`/`disputed`/`unresolved` `enum`으로 강제. **R9.2** → R9.2 자체를 판정 가능하게 재작성(`version`이 `MAJOR.MINOR.PATCH` 형식, "버전 정책" 절이 세 자리 각각의 대응을 기술)하고 AC-28·AC-38에 반영 |
| SPEC-014 | 화이트리스트를 `(kind, method, target)` **3튜플 단일 표기**로 정규화했다. `gh` CLI 읽기 호출도 `(cli, EXEC, pr view)` 형태로 같은 체계에 들어와 검사에서 빠지지 않는다. R8.2에 주입 가능한 클라이언트 인터페이스의 **아홉 메서드**를 3튜플과 함께 표로 못박았고(쓰기는 뒤 네 개뿐, `plan`은 앞 다섯 개만 호출), AC-14를 3튜플 기준으로 재작성하면서 "`plan` 경로 기록에 쓰기 3튜플 0건" 조건을 추가했다. 결정 D15로 기록 |
| SPEC-015 | `schemas/publish-plan.schema.json`(루트 object, `additionalProperties: false`)을 신설하고 R8.5로 계약을 고정했다. `apply`는 이 스키마를 만족하지 않는 계획 파일을 거부하고 아무것도 게시하지 않는다. 필드 구조(`summary_action`, `inline_review`, `thread_resolutions`, `summary_only_findings`, `lifecycle`)를 Interfaces 절에 표로 명시하고, AC-26의 검사 대상을 네 스키마로 확장했으며 AC-37의 합격 조건을 이 스키마 기준으로 다시 썼다 |
| SPEC-016 | AC-27에 외부 의존 사용 불가 시 기록 규칙을 추가했다: `codex` CLI 미설치·모델 거부·네트워크 실패로 실행 자체가 불가능하면 `blocked`로 기록하고 실패 출력을 리포트에 남기며, **실행하지 못한 것을 통과로 기록하지 않는다** |
| SPEC-017 | R3.1 매핑을 좁혔다. 신호를 코드 확장자 집합 `CODE_EXT` 안에서만 세고 `.md`·`.json`·`.yaml`·`.html`·`.css`는 제외한다. `comment-analyzer`는 **확장자별 주석 토큰**이 **3건 이상** 매치될 때만, `type-design-analyzer`는 타입 언어 8종 확장자로 한정해 선택한다. 확장자→주석 토큰 표를 요구사항에 넣고 임계값·확장자 집합을 `references/reviewer-contract.md`의 상수로 기록하게 했다 |

추가로 반영한 것 — 지적 목록 밖:

- **구조화 출력 제약(R3.7, D14, AC-44).** `codex exec --output-schema`가 `uniqueItems`(`'uniqueItems' is not permitted`)와 정규식 lookaround(`regex lookaround is not supported`)를 HTTP 400으로 거부한다는 실측을 요구사항으로 못박고, 스키마를 재귀 순회해 두 구성의 부재를 확인하는 계약 테스트를 AC-44로 추가했다. 이 제약을 모른 채 스키마를 설계하면 구현 단계에서 Codex 리뷰어가 통째로 실패한다.

  이 편차의 번호는 전달받은 **D-16이 아니라 D-15**다(`deviations.md:217`). 원문을 직접 확인해 세 가지를 더 얻었다. (1) 실측 모델이 `gpt-5.6-terra`로, 이 스킬이 쓰기로 한 모델과 같아 제약이 그대로 적용된다. (2) 경로 탈출 차단이 필요할 때 쓸 lookaround-free 대체 패턴 `^([^/~.].*|\.[^/.].*)$`가 9개 경로로 동등성이 검증돼 있어 재사용할 수 있다. (3) 제약은 **API로 전송되는 스키마에만** 적용된다 — 같은 편차가 로컬 검증 전용 `review.schema.json`에서는 `uniqueItems`가 유효하다고 명시한다. 그래서 AC-44의 대상을 `reviewer-output.schema.json` 하나로 한정하고, 나머지 세 스키마에는 제약을 걸지 않았다.

- **에이전트 출력 계약 충돌(R3.6, D16, AC-45) — 지적 목록에 없던 구현 위험.** `pr-review-toolkit`의 다섯 에이전트가 각자 본문에 자유형식 마크다운을 지시하는 자체 `Output Format` 절을 갖고 있다(`code-reviewer.md:43`, `pr-test-analyzer.md:58`, `silent-failure-hunter.md:99`, `type-design-analyzer.md:56`). 이 스킬은 호출 프롬프트로 JSON 스키마를 주입하므로 두 지시가 정면으로 충돌한다. 플러그인을 수정하지 않기로 했으므로(N8) 호출 프롬프트가 우선순위를 명시적으로 선언하는 것으로 해소하고, 그 문구를 `references/reviewer-contract.md`의 상수로 고정한 뒤 AC-45로 검증한다. 이걸 모른 채 구현하면 R3.5의 "스키마 위반 → 1회 재요청 → 제외" 경로가 상시 발동해 Claude 측 리뷰가 통째로 비어버린다.

- **`code-reviewer`의 모델 고정(D17).** 다섯 에이전트 중 `code-reviewer`만 frontmatter가 `model: opus`이고 나머지 넷은 `model: inherit`이다. R3.1 매핑상 `code-reviewer`는 항상 선택되므로 매 실행에 Opus 호출이 최소 1회 포함된다. 설정을 바꾸지 않고 비용 산정의 전제로만 기록했다.

- **GraphQL 스레드 계약 실측.** `ResolveReviewThreadInput`의 필수 입력이 `threadId`(`ID!`) 하나임을 인트로스펙션으로 확인했다. `PullRequestReviewThread`가 `comments`(마커 파싱)·`isResolved`(lifecycle 판정)·`viewerCanResolve`(해결 권한 사전 확인)·`isOutdated`·`path`·`line`·`originalLine`을 모두 노출하므로 R7.7이 계획대로 구현 가능하다. `viewerCanResolve`가 거짓인 스레드를 건너뛰고 기록하는 동작을 Interfaces 절에 추가했다.
- **요구사항 추적표.** Acceptance criteria 절 끝에 52개 요구사항 → 수용 기준 전수 매핑 표를 넣었다. `acceptance_criteria_objective` 게이트 조건이 매 라운드 수작업 대조를 요구했고 그것이 라운드 1·2 모두에서 실패 원인이었으므로, 표로 만들어 기계적으로 판정 가능하게 했다. 검증: 요구사항 정의 52건 = 표 등재 52건, 표가 참조하는 AC 전부가 실제로 정의됨(누락 0). AC-27·AC-34는 개별 요구사항이 아닌 메타 기준이라 표 아래 주석으로 사유를 남겼다.

- **inline 코멘트 필드 구성 실측 완료(R7.16, R7.17, D18, AC-46, AC-47).** 처음에는 이 저장소의 열린 PR(#31)에 리뷰 코멘트가 0건이라 표본을 얻지 못해 미검증 가정으로 남겼으나, 표본이 있는 PR을 안내받아 해소했다. `zambaguni/zambaguni-front`의 PR #1255·#1211·#1313에서 리뷰 코멘트 79건의 **응답 키 집합만** 조회했다(본문·코드 내용은 취득하지 않음). 세 PR 모두 동일한 구성이었다.

  확정한 것: `line`은 `line_end`, `side`는 `RIGHT`를 쓰고, `line_start < line_end`이면 `start_line`·`start_side`를 실어 여러 줄 코멘트로 만든다. deprecated인 `position`·`original_position`은 쓰지 않는다. 실측에서 새로 얻은 제약도 반영했다 — `start_line`과 `line`이 **서로 다른 diff hunk에 있으면** 여러 줄 코멘트가 성립하지 않으므로 단일 라인으로 축소하고 그 사실을 기록한다(R7.16, AC-46). 그리고 응답의 `node_id`(GraphQL 스레드 연결 키)·`pull_request_review_id`·`original_line`(라인 이동 후 `anchor_fingerprint` 대조 보조)을 상태에 기록하도록 R7.17을 신설했다. 이 세 필드는 실측 전에는 설계에 없었다.

이 절의 `#43` 관련 내용은 동료 세션이 이슈에 코멘트로 게시했다: <https://github.com/lee-kyu-hwan/dotfiles/issues/43#issuecomment-5447541892>. 실전 6회 재현 통계가 함께 붙었다.

## 워크플로 도구 결함 (quality-goal 후속 과제)

이 실행에서 `quality-goal` 스킬 자체의 계약 불일치가 드러났다.

`SKILL.md`의 Terminal 절은 "render report.md ... and register it with `set-artifact --kind report` (absolute path) **BEFORE** transitioning into COMPLETED, BLOCKED, NEEDS_REDESIGN, or CANCELLED"를 요구한다. 그러나 `quality_state.py record-review`는 라운드 한도 소진을 감지하면 **그 자리에서** 스스로 `NEEDS_REDESIGN`으로 전이시킨다. 전이 후에는 `set-artifact`가 `error: terminal state is immutable: NEEDS_REDESIGN`(종료 코드 3)으로 거부되므로, 지시대로 따르는 것이 구조적으로 불가능하다.

결과: 이 리포트 파일은 작성돼 durable 문서 디렉터리에 존재하지만 `state.json`의 `artifacts.report`는 `null`로 남았다.

재현: strict 또는 standard 모드에서 Spec 라운드 2가 게이트를 통과하지 못하도록 두고 `record-review`를 호출하면 된다. 같은 문제가 Plan 라운드 2와 code 라운드 3에서도 발생할 것으로 보인다(동일한 한도 소진 경로).

해소 방향 후보: (a) `record-review`가 자동 전이하지 않고 한도 소진 사실만 반환해 오케스트레이터가 리포트 등록 후 전이하게 한다, (b) `set-artifact --kind report`만 터미널 상태에서 허용한다, (c) `SKILL.md`의 순서 지시를 헬퍼의 실제 동작에 맞춰 바꾼다. `docs/quality-goal-maintenance.md`의 "추적 중인 후속 작업"에 추가할 항목이다.
