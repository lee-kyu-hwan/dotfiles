# Quality Goal Specification

- Task ID: 20260828T011459Z-42-claude-codex-이중-리뷰-종합-pr-게시-스킬-추가-55cca675
- Mode: strict
- Status: REVISED (round 2 findings applied post-gate)
- Created: 2026-08-28
- Updated: 2026-08-28
- Source goal: #42 Claude+Codex 이중 리뷰 → 종합 → PR 게시 스킬 추가

## Problem and context

PR 리뷰를 수동으로 이렇게 운영해 왔다 (이슈 #42 본문). (1) `pr-review-toolkit`의 Claude 에이전트와 Codex 리뷰를 각각 독립 실행하고, (2) 둘이 끝나면 한쪽 에이전트에 두 결과를 넘겨 종합한 뒤, (3) 종합 리뷰를 PR에 게시한다. 매번 손으로 프롬프트를 조립하고, 어느 커밋 기준 리뷰인지 사람이 기억하며, 재실행 시 같은 지적이 중복 게시된다.

저장소 실측으로 확인한 제약:

- `pr-review-toolkit`(설치본 `~/.claude/plugins/cache/claude-plugins-official/pr-review-toolkit/e33a9ec0973a`)의 6개 에이전트(`code-reviewer`, `pr-test-analyzer`, `comment-analyzer`, `silent-failure-hunter`, `type-design-analyzer`, `code-simplifier`)와 `commands/review-pr.md`는 **자유형식 마크다운 리포트**만 산출한다. 구조화 출력 계약이 없으므로 호출 측이 스키마를 프롬프트로 주입해야 한다.
- `codex` 플러그인 1.0.5의 `schemas/review-output.schema.json`은 **루트가 object**(`additionalProperties: false`, `verdict`/`summary`/`findings`/`next_steps` required)다. `quality-goal`의 `schemas/codex-result.schema.json`도 루트 object다. 구조화 출력 스키마의 루트는 object여야 한다.
- 이슈 #29(`codex-review-loop`)는 **OPEN·미구현**이고 `dot_claude/skills/`에 존재하지 않는다. 코드 의존이 불가능하므로 원칙만 이식한다.
- `gh` 2.98.0, 계정 `lee-kyu-hwan`, 토큰 스코프에 `repo` 포함. GraphQL Mutation에 `resolveReviewThread`/`unresolveReviewThread`/`minimizeComment`가 존재함을 `gh api graphql` 인트로스펙션으로 확인했다.
- 저장소 스킬 관례는 `dot_claude/skills/quality-goal/`이 정한다: `SKILL.md` + `references/` + `schemas/` + `scripts/` + `tests/` (+ `templates/`, `evals/`), 유지보수 runbook은 `docs/quality-goal-maintenance.md`, 결정적 테스트는 `python3 -m unittest discover`.
- `quality-goal`의 `references/model-routing.md`는 Codex 호출에 정확한 모델과 `model_reasoning_effort`를 고정하고, 프리플라이트와 무단 모델 대체 금지를 계약으로 둔다.

이슈 코멘트의 Codex deep research가 확정한 사실 중 설계를 구속하는 것:

- 교차비평 효과는 **조건부·비대칭**이다 (Claude가 Codex 초안 검토 시 71.6→89.7%, 반대 방향은 91.4→82.8%, arXiv 2607.21656). 라운드를 늘릴수록 좋아진다는 주장은 반박됐다 (Nature s41598-026-42705-7).
- LLM judge의 자기선호 편향은 반복 확인됐다 (GPT-4 약 10%, Claude-v1 약 25%, arXiv 2306.05685). judge ensemble은 완화하되 제거하지 못한다 (arXiv 2604.06996).
- AI 리뷰 봇의 사실상 관례는 **비차단 `COMMENT`**다. Copilot·Claude Code Review 모두 merge를 차단하지 않고, Rust LLM 정책도 비차단을 요구한다.
- 유지보수자가 거부하는 주된 이유는 false positive만이 아니라 redundant·out-of-scope 제안이다 (CodeRabbit 실사용 31,073 feedback pair 중 56.3% rejected, arXiv 2607.03316).

## Goals

- G1. `pr-review-toolkit`(Claude)과 Codex를 서로의 결과를 모르는 채 실행하고, 양쪽 모두 하나의 리뷰어 출력 스키마로 산출하게 한다.
- G2. 교차비평 라운드를 통해 근거를 코드 실측으로 대지 못하는 finding을 걸러내고, 이득이 사라지면 조기 종료한다.
- G3. 종합 단계에서 finding의 출처(리뷰어·모델)를 숨기고 순서를 결정적으로 섞어, 합의·불일치·미결을 구분한 리포트를 만든다.
- G4. PR 게시의 멱등성을 결정적 스크립트로 보장한다: 중복 게시 없음, 리뷰 기준 커밋 SHA 고정·게시 직전 재확인, 해소된 지적의 스레드 정리.
- G5. 게시는 항상 비차단 `COMMENT`이며 사용자의 명시적 승인 이후에만 실행된다.
- G6. 리뷰어가 주장한 파일·라인을 저장소 실측으로 검증한 뒤에만 inline으로 게시한다.

## Non-goals

- N1. SARIF export 및 SARIF 매핑 (사용자 결정으로 1차 범위에서 제외, 후속 이슈로 이관).
- N2. 별도 bot 계정 게시 및 `GH_TOKEN` 분기 (사용자 결정: 본인 계정 + AI 표시).
- N3. 리뷰 결과의 자동 코드 반영·수정·커밋·푸시. `code-simplifier` 에이전트는 리뷰가 아니라 수정 도구이므로 호출하지 않는다.
- N4. 이슈 #29 `codex-review-loop`의 구현·확장, 또는 그것에 대한 코드 의존.
- N5. `APPROVE`/`REQUEST_CHANGES` verdict 자동 발행, merge 차단, required check 등록.
- N6. GitHub Actions·CI 통합, webhook, 서버 상주 실행.
- N7. 문서(설계서·이슈 초안) 대상 반복 리뷰 — 그것은 #29의 영역이다.
- N8. `pr-review-toolkit`·`codex` 플러그인 파일의 수정. 두 플러그인은 외부 의존으로 유지하고 호출만 한다.
- N9. 다중 PR 일괄 리뷰, 리뷰 결과의 장기 축적·통계.
- N10. `evals/` 디렉터리. `quality-goal`의 `evals/evals.json`은 비표준 형식이고 자동 실행 수단이 없어 이슈 #36으로 이관 대기 중이다. 같은 부채를 새 스킬에 복제하지 않는다.
- N11. `templates/` 디렉터리. 이 스킬은 durable 문서를 렌더링하지 않는다. 게시물 본문 형식은 `references/publish-contract.md`가 정의한다.
- N12. 대형 diff의 자동 분할·샘플링 리뷰. 임계값 초과 시 사용자에게 결정을 넘긴다(R10).

## Requirements

### R1. 스킬 배치와 형태

- R1.1 스킬은 `dot_claude/skills/dual-review/`에 두고 chezmoi가 `~/.claude/skills/dual-review/`로 배치한다.
- R1.2 구성은 `SKILL.md`, `references/`, `schemas/`, `scripts/`, `tests/`다. `templates/`와 `evals/`는 두지 않으며 그 근거는 N10·N11에 있다.
- R1.3 `SKILL.md` frontmatter는 `name`, `version`, `description`, `argument-hint`, `disable-model-invocation: true`, `model: inherit`, `effort: high`를 갖는다. 사용자가 명시적으로 호출하는 고비용 도구이므로 모델 자동 호출을 막는다.
- R1.4 호출 계약: `/dual-review [--pr <번호>] [--base <ref>] [--rounds 0|1|2] [--no-publish]`. `--pr` 없으면 현재 브랜치의 PR을 쓰고, 없으면 중단한다.

### R2. 대상 고정

- R2.1 실행 시작 시 대상 저장소(`owner/name`), PR 번호, `base_sha`, `head_sha`, 변경 파일 목록을 상태 파일에 고정한다.
- R2.2 이후 모든 단계(리뷰·교차비평·종합·게시)는 고정된 `head_sha`만 참조한다. 실행 중 브랜치가 갱신돼도 대상은 바뀌지 않는다.
- R2.3 런타임 상태는 대상 저장소 루트의 `.claude/dual-review-state/<run_id>/`에만 쓴다. INTAKE에서 `git check-ignore`로 해당 경로의 무시 여부를 확인하고, 무시되지 않으면 경고를 출력한 뒤 계속 진행한다. `.gitignore`를 임의로 수정하지 않는다.
- R2.4 이 저장소(dotfiles) `.gitignore`에는 `.claude/dual-review-state/`를 추가한다.

### R3. 독립 이중 리뷰

- R3.1 Claude 측은 `references/reviewer-contract.md`의 결정적 매핑 표에 따라 적용되는 `pr-review-toolkit` 에이전트만 선택해 병렬 실행한다. 매핑은 다음과 같다.

  신호는 **코드 확장자 집합** `CODE_EXT = {.py, .js, .jsx, .ts, .tsx, .go, .rs, .java, .kt, .swift, .c, .h, .cpp, .rb, .sh, .zsh, .bash, .lua}` 안의 변경 파일에서만 센다. `.md`·`.txt`·`.json`·`.yaml`·`.toml`·`.html`·`.css`는 신호 계산에서 제외한다.

  | 변경 신호 | 임계 | 에이전트 |
  |---|---|---|
  | 항상 | — | `code-reviewer` |
  | 경로가 `*test*` 또는 `*spec*` 패턴에 일치하는 변경 파일이 있음 | 1건 이상 | `pr-test-analyzer` |
  | `CODE_EXT` 파일의 diff 추가 라인에서 **그 확장자의 주석 토큰**이 매치 | **3건 이상** | `comment-analyzer` |
  | `CODE_EXT` 파일의 diff 추가·삭제 라인에 `try`, `catch`, `except`, `rescue`, `recover` 중 하나가 있음 | 1건 이상 | `silent-failure-hunter` |
  | 확장자가 `{.ts, .tsx, .py, .go, .rs, .java, .kt, .swift}`인 파일의 diff 추가 라인에 타입 선언 토큰(`interface `, `type `, `class `, `struct `, `enum `, `@dataclass`, `TypedDict`) 중 하나가 있음 | 1건 이상 | `type-design-analyzer` |

  확장자별 주석 토큰:

  | 확장자 | 주석 토큰 |
  |---|---|
  | `.py` | `#`, `"""`, `'''` |
  | `.js`, `.jsx`, `.ts`, `.tsx`, `.go`, `.rs`, `.java`, `.kt`, `.swift`, `.c`, `.h`, `.cpp` | `//`, `/*` |
  | `.rb`, `.sh`, `.zsh`, `.bash` | `#` |
  | `.lua` | `--` |

  `code-simplifier`는 호출하지 않는다(N3). 선택된 에이전트 목록과 각 선택을 유발한 신호·매치 건수를 상태에 기록한다. 임계값과 확장자 집합은 `references/reviewer-contract.md`에 상수로 기록한다.
- R3.2 Codex 측은 `codex exec`를 `--sandbox read-only --ephemeral --model gpt-5.6-terra -c model_reasoning_effort="high" --output-schema --output-last-message --json`으로 호출한다. `--full-auto`, `--yolo`, `--skip-git-repo-check`, 샌드박스 우회 플래그는 스킬의 어떤 파일에도 등장하지 않는다.
- R3.3 INTAKE에서 R3.2가 지정한 모델로 프리플라이트한다(`--sandbox read-only`, `model_reasoning_effort="low"`, 한 줄 프롬프트). 실패하면 모델을 임의로 대체하지 않고 사용자에게 알린 뒤 R3.7의 단일 리뷰 경로를 따른다.
- R3.4 두 리뷰어는 상대의 산출물을 입력으로 받지 않는다. 1차 리뷰 프롬프트에는 상대 산출물의 경로도 내용도 포함되지 않으며, 상태 조회 인터페이스는 CRITIQUE 단계 이전에 상대 산출물을 반환하지 않는다.
- R3.5 양쪽 산출물은 `schemas/reviewer-output.schema.json`을 만족해야 한다. 스키마 위반 시 검증 오류만 덧붙여 1회 재요청하고, 2회째도 실패하면 그 리뷰어의 결과를 제외한 채 진행하며 리포트에 제외 사실과 사유를 남긴다.
- R3.6 `pr-review-toolkit`의 다섯 에이전트는 각자 본문에 자유형식 마크다운을 지시하는 **자체 `Output Format` 절**을 갖고 있다(설치본 실측: `code-reviewer.md:43`, `pr-test-analyzer.md:58`, `silent-failure-hunter.md:99`, `type-design-analyzer.md:56`). 호출 프롬프트는 그 절보다 이 스킬의 스키마 계약이 **우선한다는 것을 명시적으로 선언**해야 한다. 플러그인 파일은 수정하지 않으므로(N8) 충돌 해소는 호출 측 프롬프트의 책임이며, 그 문구는 `references/reviewer-contract.md`에 고정한다.
- R3.7 한쪽 리뷰어가 완전히 실패하면 자동으로 단일 리뷰로 진행하지 않는다. 사용자에게 단일 리뷰 계속 여부를 묻고, 상태에 단일 리뷰 승인이 기록되기 전에는 다음 단계로 전이하지 않는다. 승인 시 리포트와 게시 요약에 "단일 리뷰어" 사실을 명시한다.
- R3.8 `codex exec --output-schema`에 주입되는 스키마는 그 API가 거부하는 구성을 쓰지 않는다. `gpt-5.6-terra`로 실측된 거부 대상은 두 가지이며 둘 다 HTTP 400이다: **`uniqueItems`**(`'uniqueItems' is not permitted`)와 **정규식 lookaround**(`regex lookaround is not supported`). 근거는 `docs/development/2026-08-25-quality-goal/deviations.md`의 **D-15**다. `schemas/reviewer-output.schema.json`은 이 두 구성을 포함하지 않는다. 경로 탈출을 막는 패턴이 필요하면 같은 편차에서 9개 경로로 동등성이 검증된 lookaround-free 형태 `^([^/~.].*|\.[^/.].*)$`를 쓴다. 이 제약은 API로 전송되는 스키마에만 적용되므로, 로컬 검증 전용인 `critique`·`synthesis`·`publish-plan` 스키마에서는 `uniqueItems`를 써도 된다.

### R4. 위치 실측 검증

- R4.1 리뷰어 출력은 신뢰할 수 없는 데이터로 취급한다. 모든 finding의 `file`/`line_start`/`line_end`를 `head_sha` 기준 저장소 실측으로 검증한다.
- R4.2 파일이 없거나 `line_start`가 파일 라인 수를 초과하면 `location_valid=false`로 표기하고 inline 게시에서 제외한다. 요약에는 "위치 미검증"으로 남긴다.
- R4.3 `base_sha..head_sha` diff의 hunk 범위 밖 라인은 `in_diff_range=false`로 표기한다. GitHub inline 코멘트는 diff 범위 안에서만 성립하므로 이 finding은 요약으로 강등한다.
- R4.4 R4.2/R4.3 판정은 LLM이 아니라 `scripts/review_state.py`가 결정적으로 수행한다.

### R5. 교차비평

- R5.1 기본 1라운드, 최대 2라운드. `--rounds 0`은 교차비평을 건너뛴다.
- R5.2 각 리뷰어에게 상대 findings를 넘겨 반박을 요구한다. 반박은 `schemas/critique.schema.json`의 `evidence` 항목으로 파일·라인·인용을 제시해야 하며, `evidence`가 빈 반박은 채택하지 않는다.
- R5.3 **새 근거**는 다음과 같이 계산한다: critique 산출물의 각 `evidence` 항목을 `(path, line_start, line_end, normalized_quote)` 튜플로 정규화하고(`normalized_quote`는 연속 공백 축약 + 양끝 공백 제거), 이전 라운드까지의 튜플 합집합에 없는 원소의 개수를 센다. 이 값이 0이면 다음 라운드를 실행하지 않고 종료 사유 `no_new_evidence`를 상태에 기록한다. 계산은 `scripts/review_state.py`가 수행한다.
- R5.4 **추상화 이탈 신호**도 스크립트가 결정적으로 계산한다: 한 라운드 반박의 `evidence` 항목 중 `path`가 상태의 `changed_files`에 없는 것의 비율이 0.5 이상이고, 동시에 그 라운드의 반박 건수가 직전 라운드 이하로 줄지 않은 경우 신호가 참이다. 신호가 참이면 스크립트는 종료 사유 후보 `abstraction_drift`를 반환하고, 오케스트레이터는 라운드를 중단한 뒤 사용자에게 종료를 제안한다. 사용자 응답 없이 자동으로 계속하지 않는다.

### R6. 종합

- R6.1 종합자에게 전달되는 것은 정규화된 finding 객체 배열뿐이다. `source`·모델명·에이전트명 필드를 제거하고, `head_sha`를 시드로 하는 결정적 셔플로 순서를 섞는다. 이 변환은 `scripts/review_state.py`가 수행한다.
- R6.2 종합자는 각 finding을 다섯 축으로 독립 판정한다: `truth`(실제 결함인가), `introduced_by_pr`(이 PR이 도입했는가), `location_validity`(위치가 맞는가), `evidence`(근거가 있는가), `actionability`(조치 가능한가).
- R6.3 결과를 `agreed`(두 리뷰어 합의), `disputed`(반박으로 갈린 지점), `unresolved`(근거 부족으로 미결)로 분류한다. `disputed`와 `unresolved`는 버리지 않고 "두 리뷰어가 갈린 지점"으로 게시물에 남긴다.
- R6.4 은닉은 **필드 수준**에서만 보장된다. finding의 `body`·`recommendation` 텍스트가 문체나 표현으로 출처를 암시할 가능성은 남는 한계이며, 종합자가 Claude이므로 자기선호 편향도 잔존한다. 두 한계를 리포트에 명시하고, 편향이 merge 결정으로 전파되지 않도록 종합자에게 blocking 판단 권한을 주지 않는다(R7.1).

### R7. PR 게시 계약

- R7.1 게시 review 이벤트는 항상 `COMMENT`다. `APPROVE`/`REQUEST_CHANGES`를 발행하는 코드 경로를 두지 않는다.
- R7.2 게시는 `plan`(읽기 전용 계획 산출)과 `apply`(실제 게시) 두 서브커맨드로 나눈다. `apply`는 사용자 승인 이후 명시적으로만 호출되며, `plan`이나 리뷰 파이프라인이 `apply`를 호출하지 않는다.
- R7.3 `finding_id`는 `sha256(normalized_path \0 category \0 normalized_title)`의 앞 12자다. `normalized_title`은 소문자화·연속 공백 축약·양끝 구두점 제거를 거친다. 라인 번호는 포함하지 않는다.
- R7.4 `anchor_fingerprint`는 `head_sha` 기준 해당 라인의 소스 텍스트를 공백 정규화한 값의 해시다. 라인 이동을 추적하는 보조 키이며 `finding_id`를 대체하지 않는다.
- R7.5 **같은 실행 안에서 `finding_id`가 충돌하면 병합한다.** 대표 위치는 `(line_start, line_end)` 오름차순 첫 항목이고, 나머지 위치는 병합 결과의 `additional_locations` 배열에 담는다. inline 코멘트는 대표 위치에만 달고, 모든 위치는 요약 코멘트에 나열한다. 병합은 결정적이며 스크립트가 수행한다.
- R7.6 lifecycle 분류: 이전 게시에 없으면 `new`, 이전에도 있고 지금도 있으면 `persisting`(새 댓글 생성 금지), 이전에 있었으나 지금 없으면 `resolved`.
- R7.7 `resolved` finding은 (a) 요약 코멘트의 "해소됨" 목록에 기재하고, (b) 해당 리뷰 스레드를 `resolveReviewThread`로 해결한다. 스레드에 별도 답글 코멘트를 남기지 않는다. 이는 R7.14 화이트리스트 안의 수단만 사용하기 위한 결정이다.
- R7.8 요약은 PR당 하나의 sticky 코멘트다. 본문에 `<!-- dual-review:summary -->` 마커를 두고, 존재하면 새로 만들지 않고 갱신한다.
- R7.9 inline 코멘트 본문 끝에 `<!-- dual-review:finding:<finding_id> -->` 마커를 둔다. 이것이 dedup의 근거다.
- R7.10 요약 첫 줄은 `AI-generated review — Claude + Codex — reviewed commit: <head_sha>`로 시작한다.
- R7.11 `apply` 실행 직전 실제 PR head SHA를 다시 조회한다. 고정된 `head_sha`와 다르면 아무것도 게시하지 않고 비정상 종료한다.
- R7.12 **게시는 세 단계로 나뉘며 각 단계의 완료 여부를 상태에 기록한다.**
  1. 요약 코멘트 생성 또는 갱신 (단일 호출)
  2. inline 리뷰 생성 — `POST /repos/{o}/{r}/pulls/{n}/reviews`에 `event: "COMMENT"`와 `comments` 배열을 담는 **단일 원자적 호출**. 부분 성공은 발생하지 않는다.
  3. `resolved` 스레드 해결 — 스레드당 하나의 GraphQL 호출. 성공한 스레드 ID를 개별 기록한다.
- R7.13 `apply`는 멱등이다. 재실행 시 (a) 완료 기록된 단계는 다시 실행하지 않고, (b) 2단계는 기존 코멘트의 `finding_id` 마커를 대조해 이미 게시된 finding을 `comments` 배열에서 제외하며 남는 항목이 없으면 호출 자체를 생략하고, (c) 3단계는 아직 해결되지 않은 스레드만 처리한다.
- R7.14 GitHub 접근은 전부 주입 가능한 클라이언트 인터페이스(R8.2)를 거치고, 클라이언트는 각 호출을 `(kind, method, target)` **3튜플**로 기록한다. `kind`는 `rest`/`graphql`/`cli`, `method`는 REST의 HTTP 메서드 또는 `QUERY`/`MUTATION`/`EXEC`, `target`은 REST 경로 템플릿·GraphQL 오퍼레이션명·`gh` 서브커맨드다. 기록된 모든 3튜플은 화이트리스트(Interfaces 절)의 부분집합이어야 하며, 목록 밖 호출(라벨·상태·머지·assignee 변경, 스레드 답글 등)을 수행하지 않는다.
- R7.15 `--no-publish`는 `plan`까지만 수행하고 `apply`를 실행하지 않으며 게시 호출을 0건으로 만든다.
- R7.16 inline 코멘트 원소는 `path`, `line`, `side`, `body`를 싣고 `body` 끝에 `finding_id` 마커를 둔다. `line`은 finding의 `line_end`, `side`는 `RIGHT`(추가·수정된 쪽)다. `line_start < line_end`인 finding은 `start_line`(= `line_start`)과 `start_side`를 함께 실어 여러 줄 코멘트로 만들고, `line_start == line_end`이면 두 필드를 생략한다. `start_line`이 `line`과 **같은 diff hunk 안에 없으면** 여러 줄 코멘트를 만들지 않고 `line` 단일 라인으로 축소하며, 축소 사실을 상태에 기록한다. deprecated인 `position`·`original_position`은 쓰지 않는다.
- R7.17 기존 게시물 조회 결과에서 각 리뷰 코멘트의 `id`, `node_id`, `pull_request_review_id`, `path`, `line`, `original_line`을 상태에 기록한다. `node_id`는 GraphQL 리뷰 스레드와의 연결 키이고, `original_line`은 라인 이동 후에도 `anchor_fingerprint` 대조를 보조한다.

### R8. 결정적 스크립트

- R8.1 `scripts/review_state.py`는 실행 상태(대상 고정, 에이전트 선택 기록, 리뷰어 산출물 등록과 재시도 카운트, 위치 실측 검증, 교차비평 새 근거·추상화 이탈 계산, 출처 은닉·셔플, 단일 리뷰 승인 기록, 종합 결과 기록)를 담당한다.
- R8.2 `scripts/publish_findings.py`는 `plan`/`apply` 서브커맨드로 게시 계획 산출과 게시를 담당한다. GitHub 접근은 주입 가능한 클라이언트 인터페이스를 거쳐 테스트에서 fake로 대체할 수 있어야 하며, 인터페이스는 정확히 다음 아홉 메서드만 노출한다. 각 메서드는 호출을 R7.14의 3튜플로 기록한다.

  | 메서드 | 3튜플 |
  |---|---|
  | `get_pr_meta(repo, number)` | `(cli, EXEC, pr view)` |
  | `list_open_prs(repo, limit)` | `(cli, EXEC, pr list)` |
  | `list_issue_comments(repo, number)` | `(rest, GET, /repos/{o}/{r}/issues/{n}/comments)` |
  | `list_review_comments(repo, number)` | `(rest, GET, /repos/{o}/{r}/pulls/{n}/comments)` |
  | `list_review_threads(repo, number)` | `(graphql, QUERY, reviewThreads)` |
  | `create_issue_comment(repo, number, body)` | `(rest, POST, /repos/{o}/{r}/issues/{n}/comments)` |
  | `update_issue_comment(repo, comment_id, body)` | `(rest, PATCH, /repos/{o}/{r}/issues/comments/{id})` |
  | `create_review(repo, number, commit_id, event, comments)` | `(rest, POST, /repos/{o}/{r}/pulls/{n}/reviews)` |
  | `resolve_review_thread(thread_id)` | `(graphql, MUTATION, resolveReviewThread)` |

  쓰기 메서드는 뒤의 네 개뿐이다. `plan` 경로는 앞의 다섯 개만 호출한다.
- R8.3 두 스크립트는 Python 3 표준 라이브러리만 import한다(`quality_state.py` 선례). 외부 패키지를 추가하지 않는다.
- R8.4 스크립트는 GitHub 토큰을 읽거나 저장하거나 출력하지 않는다. 인증은 `gh` CLI에 위임하며 소스에 `GH_TOKEN`·`GITHUB_TOKEN`·`Authorization` 문자열이 등장하지 않는다.
- R8.5 `plan`이 산출하는 `plan.json`은 `schemas/publish-plan.schema.json`(루트 object, `additionalProperties: false`)을 만족한다. `apply`는 이 스키마를 만족하지 않는 계획 파일을 거부하고 아무것도 게시하지 않는다.

### R9. 문서와 유지보수

- R9.1 `docs/dual-review-maintenance.md`에 유지보수 runbook을 작성한다. 최소 네 개 절을 포함한다: 갱신 신호 추적, 의존 CLI·플러그인 점검, 결정적 테스트 실행 명령, 버전 정책.
- R9.2 `quality-goal`과 마찬가지로 SemVer를 따른다. `SKILL.md` frontmatter의 `version` 값은 `MAJOR.MINOR.PATCH` 형식이고, `docs/dual-review-maintenance.md`의 "버전 정책" 절이 어떤 변경이 어느 자리를 올리는지 명시하며, 같은 문서에 후속 작업(SARIF 이관 등)을 기록한다.

### R10. 입력 규모 한계

- R10.1 INTAKE에서 변경 파일 수와 diff 라인 수를 계산한다. 기본 임계값은 파일 100개, diff 20,000줄이며 `references/`에 상수로 기록한다.
- R10.2 임계값을 넘으면 자동 진행하지 않는다. 사용자에게 규모를 알리고 (a) 중단 또는 (b) 사용자가 지정한 경로 부분집합으로 범위 축소 중 하나를 선택하게 한다.
- R10.3 어떤 경우에도 무언의 절단을 하지 않는다. 범위를 축소했다면 축소된 경로 집합과 제외된 파일 수를 상태·리포트·게시 요약에 명시한다.

## Acceptance criteria

각 기준은 지정된 검증으로 객관적으로 판정한다. 기준 경로는 저장소 루트이고, 단위 테스트는 모두 `dot_claude/skills/dual-review/tests/` 아래에 있다.

### 식별자와 위치

- AC-1 `finding_id`는 제목의 대소문자·연속 공백·양끝 구두점 차이에 대해 동일한 값을 낸다. 검증: 단위 테스트.
- AC-2 `finding_id`는 `line_start`가 달라져도 동일하고, `path` 또는 `category`가 달라지면 달라진다. 검증: 단위 테스트.
- AC-3 `anchor_fingerprint`는 같은 소스 라인 텍스트에 대해 라인 번호와 무관하게 동일하다. 검증: 단위 테스트.
- AC-4 존재하지 않는 파일 또는 파일 라인 수를 초과하는 `line_start`를 가진 finding은 `location_valid=false`가 되고 inline 게시 계획에 포함되지 않는다. 검증: 임시 git 저장소 픽스처 단위 테스트.
- AC-5 diff hunk 범위 밖 라인의 finding은 `in_diff_range=false`가 되고 inline이 아니라 요약 항목으로 분류된다. 검증: 단위 테스트.
- AC-6 같은 실행에 동일 `finding_id`가 둘 이상 있으면 하나로 병합되고, 대표 위치는 `(line_start, line_end)` 오름차순 첫 항목이며, 나머지 위치가 `additional_locations`에 모두 담긴다. 검증: 단위 테스트.

### 게시 멱등성과 안전

- AC-7 동일한 plan을 두 번 `apply`하면 두 번째 실행의 GitHub 쓰기 호출이 0건이고 종료 코드가 0이다. 검증: fake 클라이언트 단위 테스트.
- AC-8 2단계(inline 리뷰 생성)가 실패한 뒤 재실행하면, 기존 코멘트의 `finding_id` 마커를 대조해 이미 게시된 finding을 제외하고 남은 것만 담은 단일 리뷰 호출이 1건 발생한다. 남는 항목이 없으면 호출이 0건이다. 검증: fake 클라이언트 단위 테스트.
- AC-9 1·2단계가 완료 기록된 뒤 3단계에서 실패한 상태로 재실행하면, 1·2단계 호출이 0건이고 3단계의 미해결 스레드만 처리된다. 검증: fake 클라이언트 단위 테스트.
- AC-10 이전 게시에 있었고 현재 리뷰에 없는 `finding_id`는 `resolved`로 분류되며, 계획에 요약의 "해소됨" 기재와 `resolveReviewThread` 호출이 포함되고 스레드 답글 호출은 포함되지 않는다. 검증: 단위 테스트.
- AC-11 `apply` 직전 조회한 head SHA가 고정된 `head_sha`와 다르면 종료 코드가 0이 아니고 GitHub 쓰기 호출이 0건이다. 검증: fake 클라이언트 단위 테스트.
- AC-12 `<!-- dual-review:summary -->` 마커를 가진 기존 코멘트가 있으면 신규 생성이 아니라 갱신 호출이 계획된다. 검증: 단위 테스트.
- AC-13 fake 클라이언트가 수신한 모든 리뷰 생성 호출의 `event` 값이 `COMMENT`다. 추가로 `grep -c 'REQUEST_CHANGES' dot_claude/skills/dual-review/scripts/publish_findings.py`가 0이다. 검증: 단위 테스트 + grep.
- AC-14 fake 클라이언트가 기록한 모든 `(kind, method, target)` 3튜플이 화이트리스트의 부분집합이고, `plan` 경로의 기록에는 쓰기 메서드 네 개의 3튜플이 하나도 없다. 검증: 단위 테스트가 화이트리스트를 상수로 두고 대조한다.
- AC-15 `plan` 실행 경로에서 GitHub 쓰기 호출이 0건이고, `publish_findings.py`의 `plan` 진입점이 `apply` 진입점을 호출하지 않는다. 검증: fake 클라이언트 단위 테스트 + AST로 호출 그래프 확인.
- AC-16 `--no-publish`로 실행하면 파이프라인 전체에서 GitHub 쓰기 호출이 0건이다. 검증: 단위 테스트.

### 리뷰 파이프라인

- AC-17 R3.1 매핑 표의 각 신호에 대해 선택되는 에이전트 집합이 표와 일치하고, `code-simplifier`는 어떤 입력에서도 선택되지 않는다. 선택 결과와 유발 신호가 상태에 기록된다. 검증: 단위 테스트.
- AC-18 1차 리뷰 프롬프트 구성 함수의 출력에 상대 리뷰어의 산출물 경로·내용이 포함되지 않고, CRITIQUE 이전 단계의 상태 조회가 상대 산출물을 반환하지 않는다. 검증: 단위 테스트.
- AC-19 스키마 위반 산출물은 1회 재요청 후 2회째 실패에서 해당 리뷰어가 `excluded` 상태가 되고 사유가 기록된다. 3회째 재요청은 발생하지 않는다. 검증: 단위 테스트.
- AC-20 단일 리뷰 승인이 상태에 기록되지 않은 채로는 리뷰어 하나가 실패한 실행이 SYNTHESIS 단계로 전이하지 않는다. 검증: 단위 테스트.
- AC-21 새 근거 수가 0인 라운드 뒤에는 다음 라운드가 실행되지 않고 종료 사유 `no_new_evidence`가 기록된다. 라운드 수는 2를 초과할 수 없다. 검증: 단위 테스트.
- AC-22 R5.4의 두 조건이 모두 참인 입력에서 `abstraction_drift`가 반환되고, 하나라도 거짓이면 반환되지 않는다. 검증: 단위 테스트.
- AC-23 종합자 입력 페이로드에 `source` 필드가 없고, 알려진 리뷰어·모델 식별자 문자열(`codex`, `gpt-5.6`, `pr-review-toolkit`, 에이전트 이름 6종)이 어떤 키나 값에도 등장하지 않는다. 검증: 단위 테스트.
- AC-24 동일 입력과 동일 `head_sha`에 대해 셔플 순서가 재현되고, `head_sha`가 다르면 순서가 달라진다. 검증: 단위 테스트.
- AC-25 R10.1 임계값을 넘는 입력에서 파이프라인이 사용자 결정 없이 다음 단계로 전이하지 않고, 범위를 축소한 경우 축소된 경로 집합과 제외 파일 수가 상태에 기록된다. 검증: 단위 테스트.

### 계약과 배치

- AC-26 `schemas/` 아래 네 개 스키마(`reviewer-output`, `critique`, `synthesis`, `publish-plan`) 전부의 루트가 `"type": "object"`이고, 각각 유효 픽스처는 통과하고 무효 픽스처는 실패한다. 검증: 단위 테스트.
- AC-27 `codex exec`가 `schemas/reviewer-output.schema.json`을 `--output-schema`로 수락한다. 검증: 최소 프롬프트로 실제 `codex exec`를 1회 실행해 종료 코드 0과 스키마를 만족하는 결과 파일을 얻는다. 이 실행은 `--sandbox read-only`다. `codex` CLI 미설치·모델 거부·네트워크 실패로 실행 자체가 불가능하면 이 기준을 `blocked`로 기록하고 그 사실과 실패 출력을 리포트에 남긴다. 실행하지 못한 것을 통과로 기록하지 않는다.
- AC-28 `SKILL.md` frontmatter가 R1.3의 일곱 필드를 모두 갖고 `version` 값이 `MAJOR.MINOR.PATCH` 형식이며, `SKILL.md`가 참조하는 모든 상대 경로 파일이 실재하고, 다음 지시 문구가 모두 존재한다: R1.4의 네 플래그(`--pr`, `--base`, `--rounds`, `--no-publish`), R3.3의 Codex 프리플라이트 단계와 실패 시 단일 리뷰 승인 경로, R3.7의 단일 리뷰 승인 게이트, R7.2의 게시 승인 게이트. 검증: 계약 테스트.
- AC-29 스킬 디렉터리 전체에서 `--full-auto`, `--yolo`, `--skip-git-repo-check` 문자열이 0건이고, `gpt-5.6-terra`와 `model_reasoning_effort="high"`가 Codex 호출 계약 문서에 존재한다. 검증: `grep -REn -- '--full-auto|--yolo|--skip-git-repo-check' dot_claude/skills/dual-review/` 매치 0건 + 계약 테스트.
- AC-30 두 스크립트가 import하는 모든 최상위 모듈이 Python 표준 라이브러리 집합에 속한다. 검증: `ast`로 import를 추출해 `sys.stdlib_module_names`와 대조하는 단위 테스트.
- AC-31 두 스크립트 소스에 `GH_TOKEN`, `GITHUB_TOKEN`, `Authorization` 문자열이 등장하지 않는다. 검증: 계약 테스트.
- AC-32 `.claude/dual-review-state/` 무시 여부 확인 분기가 무시되지 않은 경우 경고를 산출하고, 무시된 경우 경고를 산출하지 않는다. 검증: 단위 테스트.
- AC-33 `dot_claude/skills/dual-review/` 아래에 `templates/`와 `evals/` 디렉터리가 없다. 검증: 계약 테스트.
- AC-34 전체 결정적 테스트가 통과한다. 검증: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'` 종료 코드 0.
- AC-35 `chezmoi diff`가 `dot_claude/skills/dual-review/` 아래 파일들을 `~/.claude/skills/dual-review/`로 배치하는 것으로 나타난다. 검증: `chezmoi diff` 출력에 해당 경로가 포함된다.
- AC-36 `.claude/dual-review-state/`가 이 저장소에서 무시된다. 검증: `git check-ignore -v .claude/dual-review-state/` 종료 코드 0.
- AC-37 `plan`이 실제 GitHub 응답으로 동작한다. 검증: 검증 시점에 `gh pr list --state open --limit 1 --json number`로 조회한 열린 PR을 대상으로 `publish_findings.py plan`을 빈 finding 집합으로 실행해 종료 코드 0을 얻고, 산출된 `plan.json`이 `schemas/publish-plan.schema.json`을 만족하며, 기록된 3튜플에 쓰기 메서드가 0건임을 확인한다. 열린 PR이 없으면 이 기준을 `not applicable`로 기록하고 그 사실을 리포트에 남긴다.
- AC-38 `docs/dual-review-maintenance.md`가 존재하고 R9.1의 네 절(갱신 신호 추적, 의존 CLI·플러그인 점검, 결정적 테스트 실행 명령, 버전 정책)을 모두 포함하며, "버전 정책" 절이 MAJOR·MINOR·PATCH 세 자리 각각에 어떤 변경이 대응하는지 기술한다. 검증: 계약 테스트.
- AC-39 `plan`이 생성한 요약 코멘트 본문의 첫 줄이 `AI-generated review — Claude + Codex — reviewed commit: ` 로 시작하고 그 뒤에 상태의 `head_sha`가 온다. 검증: 단위 테스트.
- AC-40 `references/synthesis-contract.md`가 R6.4의 두 잔존 한계(텍스트 본문을 통한 출처 누출, 종합자 자기선호 편향)를 모두 명시한다. 검증: 계약 테스트.
- AC-41 `schemas/critique.schema.json`이 각 반박 항목에 `evidence`를 `required`로 요구하고 `minItems: 1`을 강제하며, `evidence`가 빈 반박은 스키마 검증에서 실패해 채택 대상에서 제외된다. 검증: 유효·무효 픽스처 단위 테스트 + 빈 반박이 새 근거 계산과 채택 목록 어디에도 반영되지 않음을 확인하는 단위 테스트.
- AC-42 `schemas/synthesis.schema.json`이 각 finding 판정에 다섯 축(`truth`, `introduced_by_pr`, `location_validity`, `evidence`, `actionability`)을 모두 `required`로 강제하고, 하나라도 빠진 픽스처는 검증에 실패한다. 검증: 유효·무효 픽스처 단위 테스트.
- AC-43 `schemas/synthesis.schema.json`이 각 finding의 분류를 `agreed`/`disputed`/`unresolved` 세 값의 `enum`으로 강제하고, 그 밖의 값을 가진 픽스처는 검증에 실패한다. 검증: 유효·무효 픽스처 단위 테스트.
- AC-44 `schemas/reviewer-output.schema.json`에 `uniqueItems` 키가 없고, 어떤 `pattern` 값에도 정규식 lookaround(`(?=`, `(?!`, `(?<=`, `(?<!`)가 없다. 검증: 계약 테스트가 스키마를 재귀 순회해 확인한다.
- AC-45 Claude 에이전트 호출 프롬프트를 구성하는 함수의 출력이, 에이전트 자체 `Output Format` 절보다 스키마 계약이 우선한다는 선언 문구를 포함하고 그 문구가 `references/reviewer-contract.md`의 상수와 일치한다. 검증: 단위 테스트 + 계약 테스트.
- AC-46 `line_start == line_end`인 finding의 코멘트 원소에는 `start_line`·`start_side`가 없고, `line_start < line_end`이면서 두 라인이 같은 hunk 안인 finding의 원소에는 `start_line == line_start`와 `start_side`가 있으며, 두 라인이 서로 다른 hunk에 있으면 `start_line`이 없고 축소 사실이 상태에 기록된다. 어떤 원소에도 `position` 키가 없다. 검증: 단위 테스트.
- AC-47 기존 리뷰 코멘트 조회 결과로부터 `id`·`node_id`·`pull_request_review_id`·`path`·`line`·`original_line`이 상태에 기록된다. 검증: fake 클라이언트 단위 테스트.

### 요구사항 추적

모든 요구사항이 하나 이상의 수용 기준에 대응한다. 대응이 없는 요구사항은 존재하지 않는다.

| 요구사항 | 수용 기준 | 요구사항 | 수용 기준 |
|---|---|---|---|
| R1.1 | AC-35 | R7.1 | AC-13 |
| R1.2 | AC-33 | R7.2 | AC-15 |
| R1.3 | AC-28 | R7.3 | AC-1, AC-2 |
| R1.4 | AC-28 | R7.4 | AC-3 |
| R2.1 | AC-11, AC-14 | R7.5 | AC-6 |
| R2.2 | AC-11 | R7.6 | AC-10 |
| R2.3 | AC-32 | R7.7 | AC-10 |
| R2.4 | AC-36 | R7.8 | AC-12 |
| R3.1 | AC-17 | R7.9 | AC-8 |
| R3.2 | AC-29 | R7.10 | AC-39 |
| R3.3 | AC-28, AC-20 | R7.11 | AC-11 |
| R3.4 | AC-18 | R7.12 | AC-8, AC-9 |
| R3.5 | AC-19 | R7.13 | AC-7, AC-8, AC-9 |
| R3.6 | AC-45 | R7.14 | AC-14 |
| R3.7 | AC-20 | R7.15 | AC-16 |
| R3.8 | AC-44 | R7.16 | AC-46 |
| | | R7.17 | AC-47 |
| R4.1 | AC-4 | R8.1 | AC-4, AC-5, AC-17~AC-25 |
| R4.2 | AC-4 | R8.2 | AC-14, AC-15 |
| R4.3 | AC-5 | R8.3 | AC-30 |
| R4.4 | AC-4, AC-5 | R8.4 | AC-31 |
| R5.1 | AC-21 | R8.5 | AC-26, AC-37 |
| R5.2 | AC-41 | R9.1 | AC-38 |
| R5.3 | AC-21 | R9.2 | AC-28, AC-38 |
| R5.4 | AC-22 | R10.1 | AC-25 |
| R6.1 | AC-23, AC-24 | R10.2 | AC-25 |
| R6.2 | AC-42 | R10.3 | AC-25 |
| R6.3 | AC-43 | | |
| R6.4 | AC-40 | | |

AC-27(codex 구조화 출력 수락)과 AC-34(전체 결정적 테스트 통과)는 개별 요구사항이 아니라 R3.8·R8.5의 실행 가능성과 스위트 전체를 검증하는 메타 기준이므로 표에 별도 행을 두지 않는다.

## Architecture

### 컴포넌트

| 컴포넌트 | 책임 | 형태 |
|---|---|---|
| `SKILL.md` | 단계 표, 각 단계의 필수 행동, 두 승인 게이트, 참조 파일 로딩 지시 | 마크다운 지시서 |
| `references/reviewer-contract.md` | 두 리뷰어 공통 계약(구조화 출력, 근거 규율, finding bar), 에이전트 선택 매핑 표, Codex 호출 템플릿과 모델·effort, 입력 규모 임계값 | 마크다운 |
| `references/cross-critique.md` | 교차비평 라운드 규칙, 새 근거 정의, 추상화 이탈 신호 정의, 종료 규칙 | 마크다운 |
| `references/synthesis-contract.md` | 종합자 계약(은닉 전제, 5축 판정, 분류 규칙, 잔존 한계) | 마크다운 |
| `references/publish-contract.md` | 게시 계약(SHA 고정, 마커, 3단계 게시, lifecycle, 엔드포인트 화이트리스트, verdict 정책, 게시물 본문 형식, 롤백 한계) | 마크다운 |
| `schemas/reviewer-output.schema.json` | 리뷰어 산출 (루트 object, `{"findings": [...]}`). `uniqueItems`·lookaround 미사용 | JSON Schema 2020-12 |
| `schemas/critique.schema.json` | 교차비평 산출 (루트 object). `evidence` required, `minItems: 1` | JSON Schema 2020-12 |
| `schemas/synthesis.schema.json` | 종합 산출 (루트 object). 다섯 축 required, 분류 enum | JSON Schema 2020-12 |
| `schemas/publish-plan.schema.json` | `plan.json` 계약 (루트 object) | JSON Schema 2020-12 |
| `scripts/review_state.py` | 상태 머신, 에이전트 선택, 위치 실측 검증, 라운드 판정, 은닉·셔플 | Python 3 표준 라이브러리 |
| `scripts/publish_findings.py` | `plan`/`apply`, finding_id·병합·lifecycle, 3단계 게시 | Python 3 표준 라이브러리 |
| `tests/` | 결정적 단위 테스트와 픽스처 | unittest |

### 단계

```
INTAKE        대상 PR·base_sha·head_sha·변경 파일 고정, 규모 임계값 확인,
              gh/codex(gpt-5.6-terra) 프리플라이트, 상태 경로 무시 확인
   ↓
REVIEW        Claude 에이전트(매핑 선택) + Codex — 서로의 결과를 모름
   ↓
VALIDATE      스크립트가 스키마·파일·라인 실측 검증, diff 범위 판정, ID 병합
   ↓
CRITIQUE      상대 findings 반박 (기본 1회, 최대 2회)
              새 근거 0건 → 조기 종료 / 추상화 이탈 신호 → 사용자에게 종료 제안
   ↓
SYNTHESIS     출처 은닉 + 결정적 셔플 → 5축 판정 → agreed/disputed/unresolved
   ↓
PLAN          publish_findings.py plan (읽기 전용) — new/persisting/resolved 분류
   ↓
[승인 게이트]  사용자에게 계획을 보이고 명시적 승인을 받는다
   ↓
APPLY         publish_findings.py apply — head SHA 재확인 후 3단계 게시, 멱등
```

리뷰어 하나가 실패한 경우 REVIEW 단계에서 추가 승인 게이트가 발생한다(R3.8). 이것과 게시 승인(R7.2)이 이 스킬의 두 승인 게이트다.

### 아키텍처 결정과 대안

**결정 A1 — 멱등성을 스크립트로 구현한다.**
대안 (a) 순수 문서 스킬: Claude가 `gh` 명령으로 직접 dedup. 가볍지만 멱등성이 LLM 준수에 의존하고 회귀 테스트가 불가능하다. (b) 스크립트: `finding_id` 계산·기존 게시물 대조·lifecycle 분류를 결정적으로 수행하고 단위 테스트로 고정한다. strict 등급이고 게시가 비가역 외부 쓰기이므로 (b)를 선택한다.

**결정 A2 — 게시를 `plan`/`apply`로 분리한다.**
대안 (a) 단일 명령 + 내부 확인 프롬프트: 스크립트가 대화형 입력을 받아야 하고 자동화 경로에서 우회되기 쉽다. (b) 두 서브커맨드: `plan`은 읽기 전용이라 언제든 안전하고, `apply`만 쓰기 권한을 행사한다. 승인 게이트가 두 호출 사이에 놓인다. (b)를 선택한다.

**결정 A3 — `finding_id`에 라인 번호를 넣지 않는다.**
대안 (a) 라인 포함: 같은 결함이 라인 이동만으로 새 finding이 되어 중복 게시가 발생한다. (b) 라인 제외: 라인 이동에 강하지만 두 방향의 약점이 생긴다 — 제목 표현이 흔들리면 같은 결함이 다른 ID를 얻고(중복), 같은 파일·category에 같은 제목의 별개 finding이 있으면 다른 결함이 같은 ID를 얻는다(충돌). 전자는 제목 정규화(R7.3)로 완화하고, 후자는 병합 규칙(R7.5)으로 결정적으로 처리한다. 중복 게시가 더 큰 해악이므로 (b)를 선택한다.

**결정 A4 — inline 게시를 단일 원자적 리뷰 호출로 한다.**
대안 (a) 코멘트를 개별 생성: 부분 성공 상태가 생기고 실패 지점 추적이 복잡해진다. (b) `POST /pulls/{n}/reviews`에 `comments` 배열을 담아 한 번에: 전부 성공하거나 전부 실패하므로 재실행 판단이 단순하다. (b)를 선택하고, 멱등성은 단계 완료 기록과 마커 대조로 확보한다(R7.13).

**결정 A5 — 종합자를 제3 모델로 두지 않는다.**
이슈 조사는 blocking 판단을 제3 judge나 인간에게 넘기라고 권한다. 이 스킬은 애초에 blocking verdict를 발행하지 않으므로(R7.1) 종합자의 편향이 merge 결정으로 전파되지 않는다. 제3 모델 추가는 비용과 실패 지점을 늘리는 대신 얻는 것이 적다. 대신 출처 은닉·셔플(R6.1)로 완화하고 잔존 편향을 명시한다(R6.4).

**결정 A6 — Codex 리뷰어 모델은 `gpt-5.6-terra`, effort `high`.**
`quality-goal`의 라우팅에서 `gpt-5.6-sol`은 고위험 **구현**에 배정된다. 이 스킬의 Codex 역할은 읽기 전용 리뷰이고 산출물이 구조화 finding이므로 `terra`/`high`가 적합하다. 모델을 임의로 대체하지 않고, 프리플라이트 실패는 단일 리뷰 승인 경로로 처리한다(R3.3).

## Interfaces and data flow

### 리뷰어 출력 (`schemas/reviewer-output.schema.json`)

루트는 object다. `{"verdict": "...", "summary": "...", "findings": [...]}`이며 `additionalProperties: false`다. `findings` 원소의 필드:

| 필드 | 타입 | 설명 |
|---|---|---|
| `category` | string | `correctness`, `error-handling`, `tests`, `types`, `comments`, `security`, `performance` 중 하나 |
| `severity` | string | `critical`/`high`/`medium`/`low` |
| `confidence` | number | 0~1 |
| `file` | string | 저장소 상대 경로 |
| `line_start`, `line_end` | integer | 1 이상 |
| `title` | string | 한 줄 |
| `body` | string | 무엇이 잘못됐고 왜 그 경로가 취약한지 |
| `failure_scenario` | string | 구체 입력·상태 → 잘못된 출력·크래시 |
| `recommendation` | string | 구체적 수정 방향 |
| `evidence` | array | `{path, line_start, line_end, quote}` — 코드 실측 인용 |

이 스키마는 `codex exec --output-schema`에 그대로 주입되고, Claude 에이전트에게는 프롬프트로 같은 계약을 요구한다.

### 정규화 finding (내부, `scripts/review_state.py` 산출)

리뷰어 출력의 필드에 스크립트가 다음을 덧붙인 형태다: `finding_id`, `anchor_fingerprint`, `location_valid`, `in_diff_range`, `additional_locations`. 종합 단계 이전에는 `source`(리뷰어 식별자)도 갖지만, 종합자 전달 시 제거된다(R6.1). 이 구조는 별도 스키마 파일 없이 스크립트와 테스트가 계약을 고정한다.

### 게시 계획 (`schemas/publish-plan.schema.json`)

`plan`이 산출하고 `apply`가 소비하는 계약이다. 루트 object, `additionalProperties: false`.

| 필드 | 타입 | 설명 |
|---|---|---|
| `repo`, `pr_number` | string, integer | 대상 고정값 |
| `base_sha`, `reviewed_sha` | string | 상태의 고정값. `reviewed_sha`가 요약 첫 줄에 인용된다 |
| `summary_action` | object | `{kind: "create"|"update", comment_id: integer|null, body: string}` |
| `inline_review` | object | `{skip: boolean, comments: [...]}`. `skip`이 참이면 2단계를 호출하지 않는다 |
| `thread_resolutions` | array | `[{thread_id, finding_id}]` |
| `summary_only_findings` | array | `location_valid=false` 또는 `in_diff_range=false`로 강등된 finding |
| `lifecycle` | object | `{new: [finding_id], persisting: [finding_id], resolved: [finding_id]}` |

`inline_review.comments` 원소의 구성은 실측으로 확정했다(R7.16). `{path, line, side, body, finding_id}`가 필수이고, finding이 여러 줄에 걸치면 `start_line`·`start_side`를 함께 싣는다.

### 상태 파일

`.claude/dual-review-state/<run_id>/state.json`은 `run_id`, `repo`, `pr_number`, `base_sha`, `head_sha`, `changed_files`, `scope_reduction`, `selected_agents`, `reviewers`(산출물 경로·재시도 횟수·`excluded` 사유), `single_reviewer_approval`, `critique_rounds`, `termination_reason`, `synthesis`, `publish_stages`(3단계 완료 기록), `published_findings`, `resolved_threads`를 갖는다.

### GitHub 엔드포인트 화이트리스트 (R7.14)

모든 항목이 `(kind, method, target)` 단일 표기다. 클라이언트가 기록하는 3튜플이 이 집합의 부분집합인지를 AC-14가 대조한다.

| 목적 | kind | method | target | 쓰기 |
|---|---|---|---|---|
| PR 메타·head SHA 조회 | `cli` | `EXEC` | `pr view` | 아니오 |
| 열린 PR 조회 | `cli` | `EXEC` | `pr list` | 아니오 |
| 기존 이슈 코멘트 조회 | `rest` | `GET` | `/repos/{o}/{r}/issues/{n}/comments` | 아니오 |
| 기존 리뷰 코멘트 조회 | `rest` | `GET` | `/repos/{o}/{r}/pulls/{n}/comments` | 아니오 |
| 리뷰 스레드 상태 조회 | `graphql` | `QUERY` | `reviewThreads` | 아니오 |
| 요약 코멘트 생성 | `rest` | `POST` | `/repos/{o}/{r}/issues/{n}/comments` | 예 |
| 요약 코멘트 갱신 | `rest` | `PATCH` | `/repos/{o}/{r}/issues/comments/{id}` | 예 |
| inline 리뷰 생성 | `rest` | `POST` | `/repos/{o}/{r}/pulls/{n}/reviews` (event=`COMMENT`) | 예 |
| 해소 스레드 정리 | `graphql` | `MUTATION` | `resolveReviewThread` | 예 |

GraphQL 계약은 인트로스펙션으로 실측했다. `ResolveReviewThreadInput`의 필수 입력은 `threadId`(`ID!`) 하나이고 `resolutionReason`(enum)과 `clientMutationId`는 선택이다. `PullRequestReviewThread`는 `id`·`isResolved`·`isOutdated`·`path`·`line`·`originalLine`·`comments`·`viewerCanResolve`를 노출하므로, 마커 파싱(`comments`의 body)·lifecycle 판정(`isResolved`)·해결 가능 여부 사전 확인(`viewerCanResolve`)에 필요한 것이 모두 갖춰져 있다. `apply`는 `viewerCanResolve`가 거짓인 스레드를 건너뛰고 그 사실을 상태에 기록한다.

목록 밖의 호출은 수행하지 않는다. 스레드 답글 엔드포인트는 의도적으로 제외했고, 해소 사실은 요약 코멘트에 기재한다(R7.7). `gh` CLI 경유 읽기 호출도 같은 3튜플로 기록되므로 화이트리스트 검사에서 빠지지 않는다.

### 데이터 흐름

```
git diff(base..head) ─┬─→ Claude 에이전트(매핑 선택) ─→ reviewer-output(A) ─┐
                      └─→ codex exec(terra/high)     ─→ reviewer-output(B) ─┤
                                                                            ↓
                                          review_state.py validate
                              (스키마, 파일·라인 실측, diff 범위, ID 병합)
                                                                            ↓
                                   findings(A)⇄findings(B) 교차비평 (0~2회)
                                                                            ↓
                                  review_state.py normalize (은닉 + 셔플)
                                                                            ↓
                                              종합자 → synthesis.json
                                                                            ↓
                          publish_findings.py plan (기존 게시물 대조) → plan.json
                                                                            ↓
                                                [사용자 승인]
                                                                            ↓
                                publish_findings.py apply → GitHub (3단계)
```

## Failure behavior

| 실패 | 동작 |
|---|---|
| `gh` 미설치·미인증 | INTAKE에서 중단하고 인증 방법을 안내한다. 상태를 만들지 않는다. |
| 대상 PR 없음 | 중단하고 `--pr` 지정을 요구한다. |
| 입력 규모 임계값 초과 | 자동 진행하지 않고 중단 또는 범위 축소를 사용자에게 묻는다. 무언의 절단을 하지 않는다(R10). |
| Codex 프리플라이트 실패·모델 거부 | 모델을 임의로 대체하지 않는다. 사용자에게 알리고 단일 리뷰 승인 경로를 따른다(R3.3, R3.6). |
| Claude 에이전트 일부 실패 | 실패한 에이전트를 리포트에 명시하고 나머지로 진행한다. 커버리지 결손을 게시 요약에 남긴다. |
| 리뷰어 출력 스키마 위반 | 검증 오류만 덧붙여 1회 재요청. 2회째 실패 시 해당 리뷰어를 `excluded`로 표시하고 사유를 남긴다(R3.5). |
| 두 리뷰어 모두 실패 | 게시하지 않고 중단한다. |
| 위치 검증 실패 | 해당 finding을 inline에서 제외하고 요약에 "위치 미검증"으로 남긴다. 리뷰 전체를 실패시키지 않는다. |
| 교차비평 무진전 | 다음 라운드를 실행하지 않고 종료 사유 `no_new_evidence`를 기록한다. |
| 추상화 이탈 신호 | 라운드를 중단하고 사용자에게 종료를 제안한다. 자동으로 계속하지 않는다. |
| `apply` 직전 head SHA 불일치 | 아무것도 게시하지 않고 비정상 종료한다. 새 SHA로 리뷰를 다시 시작해야 한다. |
| 게시 1단계 실패 | 2·3단계를 실행하지 않고 비정상 종료한다. 재실행 시 1단계부터 다시 시도한다. |
| 게시 2단계 실패 | 원자적 호출이므로 부분 게시가 없다. 3단계를 실행하지 않고 비정상 종료한다. 재실행 시 1단계는 건너뛰고 2단계를 마커 대조 후 재시도한다(R7.13). |
| 게시 3단계 일부 실패 | 성공한 스레드 ID를 기록하고 비정상 종료한다. 재실행 시 미해결 스레드만 처리한다. |
| 상태 디렉터리가 git에 무시되지 않음 | 경고를 출력하고 계속 진행한다. `.gitignore`를 임의 수정하지 않는다. |

## Security and risk

**신뢰 경계.** 리뷰어(LLM) 출력은 미신뢰 데이터다. 스키마 검증과 파일·라인 실측 검증(R4)을 통과한 것만 inline으로 게시한다. 리뷰 대상 diff에 프롬프트 인젝션 문구가 있어도, 스킬은 그것으로 게시 정책·승인 게이트·엔드포인트 화이트리스트·모델 선택을 바꾸지 않는다.

**게시 텍스트의 전파.** 게시 본문은 리뷰어가 생성한 텍스트와 diff 인용을 포함한다. 인용 대상은 이미 해당 PR에 존재하는 코드이므로 새로운 노출은 아니다. 저장소 밖 경로 인용은 위치 검증에서 걸러진다.

**자격 증명.** 스크립트는 토큰을 읽거나 저장하거나 출력하지 않고 `gh` CLI 인증에 위임한다(R8.4). 상태 파일·로그·게시물에 토큰이 들어가지 않으며, 소스에 토큰 환경변수명이 등장하지 않는 것을 AC-31로 고정한다.

**권한 범위.** 활성 토큰 스코프는 `gist, project, read:org, repo, user, workflow`다. `repo`는 게시에 필요한 최소보다 넓지만 축소는 사용자 계정 설정의 영역이며 이 작업의 범위 밖이다. 대신 엔드포인트 화이트리스트(R7.14)와 그 준수를 강제하는 AC-14로 실제 행사 범위를 좁힌다.

**대상 오지정.** 잘못된 저장소·PR에 게시하는 것이 가장 비싼 실패다. 저장소와 PR 번호를 INTAKE에서 상태에 고정하고, `apply`가 상태의 값만 사용하며 실행 직전 head SHA까지 재확인한다(R7.11).

**리스크와 완화.**

| 리스크 | 완화 |
|---|---|
| 중복·스팸 댓글로 PR 오염 | `finding_id` 마커 dedup, sticky summary, `persisting` 재게시 없음, 단계 완료 기록 |
| stale SHA 기준 리뷰 게시 | SHA 고정 + 게시 직전 재확인, 요약 첫 줄에 SHA 명시 |
| false positive 게시 | 교차비평 + 5축 판정 + 위치 실측, 근거 없는 finding은 `unresolved`로 강등 |
| 종합자 자기선호 편향 | 출처 필드 은닉·셔플, blocking verdict 없음, 잔존 한계 명시 |
| 리뷰가 merge를 차단 | verdict를 `COMMENT`로 고정, 발행 경로 부재를 테스트로 고정 |
| 승인 없는 게시 | `apply` 분리, 자동 호출 경로 부재를 AST 검사로 고정 |
| 대형 diff의 조용한 커버리지 결손 | 임계값 초과 시 사용자 결정 요구, 축소 범위를 상태·리포트·게시에 명시 |

## Test strategy

결정적 테스트는 `dot_claude/skills/dual-review/tests/`에 두고 `quality-goal` 선례와 같은 방식으로 실행한다.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'
```

- `test_publish_findings.py` — AC-1~AC-3, AC-6~AC-16, AC-39. GitHub 접근은 호출 기록을 남기는 fake 클라이언트로 대체하고, 화이트리스트 대조·verdict 고정·쓰기 호출 0건을 그 기록으로 판정한다.
- `test_review_state.py` — AC-4, AC-5, AC-17~AC-25. 임시 git 저장소 픽스처를 만들어 파일·라인·diff 범위를 실측한다.
- `test_content_contracts.py` — AC-26, AC-28~AC-33, AC-38, AC-40~AC-44. 네 스키마의 루트 형태와 필드 요건(critique의 `evidence` minItems, synthesis의 다섯 축·세 분류 enum), `SKILL.md` frontmatter·`version` 형식·플래그·프리플라이트·두 게이트 문구와 참조 경로, 금지 플래그 부재, 구조화 출력 금지 구성(`uniqueItems`·lookaround) 부재, 표준 라이브러리 import, 토큰 문자열 부재, 디렉터리 구성, 유지보수 문서 절 구성, 종합자 계약의 한계 명시를 확인한다.

스크립트 밖 검증:

- **AC-27** — 최소 프롬프트로 `codex exec --sandbox read-only --model gpt-5.6-terra --output-schema schemas/reviewer-output.schema.json`을 1회 실행해 스키마 수락을 확인한다.
- **AC-34** — 위 unittest 명령.
- **AC-35** — `chezmoi diff`.
- **AC-36** — `git check-ignore -v .claude/dual-review-state/`.
- **AC-37** — `gh pr list --state open --limit 1`로 얻은 PR에 대한 읽기 전용 `plan` 실행. 열린 PR이 없으면 `not applicable`로 기록한다.

이 저장소에는 타입 체크·린트·빌드 설정이 없다. 해당 검증 범주는 "not configured"로 기록하며, 근거는 저장소 루트에 `package.json`·`pyproject.toml`·`Makefile`·CI 워크플로가 없다는 사실이다.

## Decisions

- D1. 스킬 이름은 `dual-review`, 배치는 `dot_claude/skills/dual-review/`. 이슈 #42가 지정한 `dot_claude/skills/`를 따른다.
- D2. 멱등성은 결정적 스크립트로 구현한다(결정 A1, 사용자 확인).
- D3. 게시 주체는 사용자 본인 계정이고 요약 첫 줄에 AI 생성 사실과 리뷰 대상 SHA를 표시한다(사용자 확인). 별도 bot 계정은 비목표다.
- D4. SARIF export는 1차 범위에서 제외하고 후속 이슈로 이관한다(사용자 확인). 내부 정규화 finding에는 후속 매핑에 필요한 `finding_id`·`evidence`·분류 필드를 유지한다.
- D5. 교차비평은 기본 1회, 최대 2회. 이슈 조사가 확정한 "회차 증가가 항상 이득은 아니다"(Nature s41598-026-42705-7)와 비대칭 결과(arXiv 2607.21656)를 근거로 한다.
- D6. verdict는 항상 `COMMENT`. Copilot·Claude Code Review·Rust LLM 정책의 비차단 관례를 따른다.
- D7. `pr-review-toolkit` 에이전트에는 구조화 출력 계약을 호출 측 프롬프트로 주입한다. 플러그인 파일은 수정하지 않는다(N8).
- D8. 이슈 #29에 코드 의존하지 않는다. #29가 OPEN·미구현임을 저장소 실측으로 확인했다. 이식하는 것은 원칙(2라운드 연속 조용, 실측 근거 요구, 추상화 이탈 감지)뿐이다.
- D9. Codex 호출은 `model-routing.md`의 안전 플래그 집합을 쓰되, 리뷰는 읽기 전용이므로 `--sandbox read-only`를 쓰고 모델은 `gpt-5.6-terra`, effort는 `high`로 고정한다(결정 A6).
- D10. 리뷰어 출력 스키마의 루트는 object다. codex 1.0.5의 `review-output.schema.json`과 `quality-goal`의 `codex-result.schema.json`이 모두 루트 object이며, 구조화 출력 계약이 루트 배열을 수락한다는 근거가 없다. 파생 필드는 스키마 밖 내부 표현에만 붙인다.
- D11. inline 게시는 단일 원자적 리뷰 호출이다(결정 A4). 부분 게시 상태가 존재하지 않으므로 멱등성은 단계 완료 기록과 마커 대조로 확보한다.
- D12. `resolved` finding은 스레드 답글 대신 요약 기재 + `resolveReviewThread`로 처리한다. 화이트리스트를 넓히지 않기 위한 결정이며, 부수 효과로 스레드 스팸도 줄인다.
- D13. `templates/`와 `evals/`를 두지 않는다(N10, N11).

- D14. `codex exec --output-schema`가 거부하는 구성을 스키마에서 배제한다(R3.8). `uniqueItems`와 정규식 lookaround가 HTTP 400으로 거절되는 것은 `docs/development/2026-08-25-quality-goal/deviations.md` **D-15**의 실측 결과이고, 실측 모델이 이 스킬이 쓸 `gpt-5.6-terra`와 같아 그대로 적용된다. 제약 대상은 API로 전송되는 스키마뿐이며, 같은 편차가 로컬 전용 스키마(`review.schema.json`)에서는 `uniqueItems`가 유효하다고 명시한다. AC-44는 그래서 `reviewer-output.schema.json`만 대상으로 한다.
- D15. GitHub 접근 표기를 `(kind, method, target)` 3튜플로 통일하고 클라이언트 인터페이스를 아홉 메서드로 못박는다(R7.14, R8.2). `gh` CLI·REST·GraphQL이 한 검사 체계 안에 들어와야 AC-14가 실제로 화이트리스트를 강제할 수 있다.

- D16. `pr-review-toolkit` 에이전트의 자체 `Output Format` 절과 이 스킬의 스키마 계약이 충돌한다. 플러그인을 수정하지 않기로 했으므로(N8) 호출 프롬프트가 우선순위를 명시적으로 선언하는 방식으로 해소한다(R3.6, AC-45). 대안이던 "플러그인 포크 후 출력 절 교체"는 외부 의존을 유지한다는 이슈 #42의 배치 결정과 어긋나 채택하지 않았다.
- D17. `code-reviewer` 에이전트만 frontmatter에 `model: opus`가 고정돼 있고 나머지 넷은 `model: inherit`이다(설치본 실측). 이 스킬은 그 설정을 바꾸지 않으므로, `code-reviewer`가 항상 선택되는 R3.1 매핑상 매 실행에 Opus 호출이 최소 1회 포함된다. 비용 상한을 별도로 두지 않고 실행 비용 산정의 전제로만 기록한다.

- D18. inline 코멘트 필드 구성은 실측으로 확정했다. `zambaguni/zambaguni-front`의 PR #1255·#1211·#1313에서 리뷰 코멘트 79건의 응답 키 집합을 조회해(본문·코드 내용은 취득하지 않고 키 이름만) 세 PR 모두 동일한 구성임을 확인했다: `path`, `line`, `side`, `start_line`, `start_side`, `body`, `commit_id`, `id`, `node_id`, `pull_request_review_id`, `original_line`, `original_start_line`, `subject_type`, `diff_hunk`, 그리고 deprecated인 `position`·`original_position`. 이에 따라 R7.16·R7.17을 확정했고, 여러 줄 코멘트를 지원하되 hunk 경계를 넘으면 단일 라인으로 축소한다.

미해결 결정 없음.

<!-- strict-only:start -->

### Threat and trust boundaries

| 행위자 | 신뢰 | 경계 |
|---|---|---|
| 사용자 | 신뢰 | 스킬을 호출하고 두 게이트를 승인한다 |
| 저장소 코드·diff | 미신뢰 데이터 | 리뷰 입력. 인젝션 문구가 있어도 정책을 바꾸지 못한다 |
| Claude 리뷰 에이전트 출력 | 미신뢰 | 스키마 + 위치 실측 검증 통과 후에만 게시 |
| Codex 출력 | 미신뢰 | 스키마 + 위치 실측 검증 후에만 게시 |
| GitHub API 응답 | 신뢰(전송) / 미신뢰(내용) | 기존 코멘트 본문은 마커 파싱에만 쓰고 지시로 해석하지 않는다 |
| `gh` 인증 토큰 | 신뢰, 미노출 | 스크립트가 직접 다루지 않는다(AC-31) |

통제와 그 검증: 엔드포인트 화이트리스트(AC-14), 승인 게이트(AC-15, AC-20, AC-28), 위치 실측(AC-4, AC-5), verdict 고정(AC-13), 샌드박스·금지 플래그(AC-29), 토큰 미취급(AC-31).

### Authorization and tenant isolation

멀티테넌시가 없는 단일 사용자 CLI 도구이므로 테넌트 격리는 해당 없다. 대응하는 격리 개념은 **대상 격리**다: 저장소와 PR 번호를 INTAKE에서 고정하고 `apply`가 상태의 값만 사용해, 다른 저장소·다른 PR에 게시되는 경로를 없앤다. 검증은 AC-11(SHA 재확인)과 AC-14(화이트리스트 대조)가 담당한다. 권한은 사용자의 기존 `gh` 토큰 권한을 넘지 않으며, 스킬이 권한을 상승시키거나 새 자격 증명을 만들지 않는다.

### Migration, compatibility, and rollback

신규 스킬이므로 데이터 마이그레이션·백필이 없다. 호환성 대상은 세 외부 계약이다: `pr-review-toolkit` 에이전트 이름 6종, `codex exec` 플래그(`--output-schema`, `--ephemeral`, `--output-last-message`, `--json`, `--sandbox`, `--model`)와 모델 식별자 `gpt-5.6-terra`, GitHub REST/GraphQL 필드. 셋 다 `docs/dual-review-maintenance.md`의 점검 대상으로 기록한다.

롤백 트리거와 절차:

| 트리거 | 절차 |
|---|---|
| 스킬 자체를 되돌림 | 커밋 되돌리기 후 `chezmoi apply`. 런타임 상태는 무시 경로에 있으므로 삭제만 하면 된다 |
| 잘못 게시된 코멘트 | **자동 롤백을 제공하지 않는다.** 게시된 코멘트의 삭제·최소화는 사용자가 GitHub UI 또는 `gh`로 직접 수행한다. 이 한계를 `references/publish-contract.md`에 명시한다 |
| 게시 중 중단 | 단계 완료 기록이 남으므로 재실행이 멱등하다(R7.13, AC-8, AC-9) |

### Failure recovery and observability

- 관측 지점: `.claude/dual-review-state/<run_id>/`의 `state.json`, 리뷰어 산출물 JSON, Codex 이벤트·stderr 로그, `plan.json`, 게시 단계 기록.
- 각 GitHub 쓰기 호출의 대상·응답 상태·생성된 코멘트 ID를 상태에 기록해, 부분 실패 후 무엇이 게시됐는지 재실행 없이 알 수 있게 한다.
- 리뷰어별 성공·실패·`excluded` 사유, 선택된 에이전트와 유발 신호, 범위 축소 내역을 리포트와 게시 요약에 남겨 커버리지 결손이 조용히 숨지 않게 한다.
- 알림·메트릭·트레이스는 대화형 CLI 도구에 해당하지 않는다. 사용자에게 직접 출력하는 것이 관측 수단이다.

### High-risk end-to-end verification

고위험 경로는 **PR 게시**다. 검증을 셋으로 나눈다.

1. **fake 클라이언트 통합 검증(자동).** 게시 lifecycle 전체(new → persisting → resolved), 각 단계 실패 후 재실행 멱등, head SHA 불일치 중단, 화이트리스트 준수, verdict 고정을 fake GitHub 클라이언트로 실행한다. AC-7~AC-16이 이 경로다. 중단 조건: 하나라도 실패하면 게시 계약을 고친 뒤 다시 돌린다.
2. **읽기 전용 실 API 검증(자동).** 검증 시점에 조회한 열린 PR을 대상으로 `plan`을 빈 finding 집합으로 실행해 실제 GitHub 응답 파싱을 검증한다(AC-37). 게시하지 않는다. 열린 PR이 없으면 `not applicable`로 기록한다.
3. **실 게시 E2E(수동, 이 워크플로에서 실행하지 않음).** 실제 `apply`는 외부 비가역 쓰기이므로 이 구현 워크플로의 자동 검증에 포함하지 않는다. 사용자가 스킬을 처음 실전 사용할 때 승인 게이트를 거쳐 수행하고, 그 결과(중복 없음, 재실행 시 신규 0건)를 확인하는 것으로 완료한다. **이 항목이 검증되지 않은 채 남는다는 사실을 리포트에 명시한다.**

### No production mutation confirmation

이 구현 워크플로는 프로덕션을 변경하지 않는다. 산출물은 `dot_claude/skills/dual-review/` 아래의 문서·스키마·스크립트·테스트, `docs/dual-review-maintenance.md`, `.gitignore` 한 줄이다. 구현 중 자동 커밋·푸시·머지·배포를 하지 않는다. GitHub에 대한 유일한 쓰기 경로는 스킬이 나중에 실행될 때의 PR 코멘트 게시이며, 그것도 사용자 승인 이후에만 일어난다. 이 워크플로의 검증 단계에서는 실제 게시를 수행하지 않는다(위 3항). AC-27은 `codex exec`를 실행하지만 `--sandbox read-only`이며 저장소를 변경하지 않는다.

<!-- strict-only:end -->
