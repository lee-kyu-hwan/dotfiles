# Quality Goal Specification

- Task ID: 20260903T160637Z-42-claude-codex-이중-리뷰-종합-pr-게시-스킬-추가-55cca675
- Mode: strict
- Status: IN_REVIEW
- Created: 2026-08-28
- Updated: 2026-09-04
- 판본 이력: 2026-08-28에 선행 실행(`20260828T021938Z-...`)의 Spec 라운드 2에서 93점 PASS를 받은 본을 이 실행의 초안으로 재사용했다. 그 통과는 이 실행의 게이트 판정과 무관하다. 현재 본은 이 실행의 라운드 1 지적 12건과 라운드 2 지적 5건(SPEC-09, SPEC-13~16), `report.md`의 "4차 착수 전 확정된 설계 결정", readiness attempt 1의 READY-01·READY-02를 반영한 개정본이다. Task ID 타임스탬프(`20260903T160637Z`)는 이 실행의 생성 시각, 디렉터리 날짜(`2026-09-04`)는 산출물 배치 날짜, `Updated`는 현재 개정 날짜다.
- Source goal: #42 Claude+Codex 이중 리뷰 → 종합 → PR 게시 스킬 추가

## Problem and context

PR 리뷰를 수동으로 이렇게 운영해 왔다 (이슈 #42 본문). (1) `pr-review-toolkit`의 Claude 에이전트와 Codex 리뷰를 각각 독립 실행하고, (2) 둘이 끝나면 한쪽 에이전트에 두 결과를 넘겨 종합한 뒤, (3) 종합 리뷰를 PR에 게시한다. 매번 손으로 프롬프트를 조립하고, 어느 커밋 기준 리뷰인지 사람이 기억하며, 재실행 시 같은 지적이 중복 게시된다.

저장소 실측으로 확인한 제약:

- `pr-review-toolkit`(2026-09-04 조회 시점 활성 설치본. 경로의 해시는 갱신마다 바뀌므로 `~/.claude/plugins/installed_plugins.json`의 `pr-review-toolkit@claude-plugins-official` 항목이 가리키는 `installPath`로 찾는다)의 6개 에이전트(`code-reviewer`, `pr-test-analyzer`, `comment-analyzer`, `silent-failure-hunter`, `type-design-analyzer`, `code-simplifier`)와 `commands/review-pr.md`는 **자유형식 마크다운 리포트**만 산출한다. 구조화 출력 계약이 없으므로 호출 측이 스키마를 프롬프트로 주입해야 한다.
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
- G4. PR 게시의 멱등성을 결정적 스크립트로 보장한다: 중복 게시 없음, 리뷰 기준 커밋 SHA 고정·게시 직전 재확인, GitHub에 지속한 게시 이력의 실행 간 복원, 실제로 해소된 지적만 스레드 정리.
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
- N9. 다중 PR 일괄 리뷰와 리뷰 결과의 분석용 장기 축적·통계. R7.19의 GitHub 게시 인덱스는 다음 실행의 lifecycle 복원에 필요한 최소 운영 메타데이터이며 분석용 저장소가 아니므로 이 비목표에 해당하지 않는다.
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

- R2.1 실행 시작 시 대상 저장소(`owner/name`), PR 번호, `base_sha`, `head_sha`, 변경 파일 목록 다섯 값을 상태 파일에 고정한다. 이후 모든 단계는 **대상 메타데이터로는** 상태의 이 값만 참조하고 GitHub에서 base·변경 파일·대상 PR을 다시 해석하지 않는다. 허용되는 후속 조회는 R7.19의 이전 게시 이력 네 목록과 R7.11의 게시 직전 head SHA 재확인뿐이며, 둘 다 고정 대상을 바꾸지 않는다.
- R2.1a `--base <ref>`는 diff 계산의 base를 PR의 실제 base 대신 지정한 ref로 덮어쓴다. 지정된 ref가 PR의 실제 base와 다르면 R4.3의 `in_diff_range` 판정이 GitHub가 inline 코멘트를 받아들이는 실제 범위와 어긋난다. 이 경우 **inline 게시를 전면 금지하고 모든 finding을 요약으로 강등**하며, base 불일치 사실과 두 ref를 상태·리포트·게시 요약에 명시한다. `--base`가 없거나 PR의 실제 base와 같으면 정상 경로다.
- R2.2 이후 모든 단계(리뷰·교차비평·종합·게시)는 고정된 `head_sha`만 참조한다. 실행 중 브랜치가 갱신돼도 대상은 바뀌지 않는다.
- R2.3 런타임 상태는 대상 저장소 루트의 `.claude/dual-review-state/<run_id>/`에만 쓴다. INTAKE에서 `git check-ignore`로 해당 경로의 무시 여부를 확인하고, 무시되지 않으면 경고를 출력한 뒤 계속 진행한다. `.gitignore`를 임의로 수정하지 않는다.
- R2.4 이 저장소(dotfiles) `.gitignore`에는 `.claude/dual-review-state/`를 추가한다.
- R2.5 INTAKE의 순서는 이렇다: PR을 조회해 `repo`·`pr_number`·PR의 실제 base SHA·diff 계산에 쓸 `base_sha`·`head_sha`를 메모리에 얻고 → 그것으로 `run_id`를 만들고 → 상태 디렉터리를 열거나 만들고 → R2.1의 다섯 값과 실행 구성 `requested_base_ref`(`--base`를 생략했으면 null, 지정했으면 원문 문자열)·`actual_base_sha`·`rounds`(기본값을 적용한 0~2 정수)를 그 안의 `state.json`에 고정한다. `run_id`는 `<repo_owner>-<repo_name>-pr<pr_number>-<head_sha 앞 12자>` 형식으로 **결정적으로** 생성한다. 같은 PR의 같은 head SHA에 대한 재실행은 같은 `run_id`를 얻어 직전 실행의 상태 디렉터리를 연다. 이때 새 호출의 `requested_base_ref`, 새로 해석한 `base_sha`, `actual_base_sha`, 유효 `rounds` 중 하나라도 상태의 고정값과 다르면 기존 값을 조용히 재사용하거나 덮어쓰지 않고, 단계 실행·상태 변경·GitHub 쓰기 전에 종료 코드 != 0으로 중단해 충돌한 필드와 두 값을 알린다. 따라서 같은 `--base` 문자열이 다른 commit으로 이동한 경우도 침묵하지 않는다. 네 값이 모두 일치할 때만 R7.13(a)의 완료 기록을 이어 쓴다. head SHA가 바뀌면 다른 `run_id`가 되고 로컬 상태를 재사용하지 않는다 — 리뷰 대상이 달라졌기 때문이다. 상태 디렉터리가 없으면 새로 만들고 별도의 재개 플래그는 두지 않는다. 이 로컬 상태는 **한 `run_id` 안의 bookkeeping과 재개에만** 쓰며, head SHA를 넘는 게시 이력은 여기나 git notes에 저장하지 않고 R7.19에 따라 GitHub에서 복원한다.

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

  `code-simplifier`는 호출하지 않는다(N3). 선택된 에이전트 목록과 각 선택을 유발한 신호·매치 건수를 상태에 기록한다. 임계값과 확장자 집합은 `references/reviewer-contract.md`에 상수로 기록한다. 에이전트 선택과 별개인 category 책임 매핑과 일부 실패 시 coverage 계산은 R3.10을 따른다.
- R3.2 Codex 측은 `codex exec`를 `--sandbox read-only --ephemeral --model gpt-5.6-terra -c model_reasoning_effort="high" --output-schema --output-last-message --json`으로 호출한다. `--full-auto`, `--yolo`, `--skip-git-repo-check`, 샌드박스 우회 플래그는 스킬의 어떤 파일에도 등장하지 않는다.
- R3.3 INTAKE에서 R3.2가 지정한 모델로 프리플라이트한다(`--sandbox read-only`, `model_reasoning_effort="low"`, 한 줄 프롬프트). 실패하면 모델을 임의로 대체하지 않고 사용자에게 알린 뒤 R3.7의 단일 리뷰 경로를 따른다.
- R3.4 두 리뷰어는 상대의 산출물을 입력으로 받지 않는다. 1차 리뷰 프롬프트에는 상대 산출물의 경로도 내용도 포함되지 않으며, 상태 조회 인터페이스는 CRITIQUE 단계 이전에 상대 산출물을 반환하지 않는다.
- R3.5 양쪽 산출물은 `schemas/reviewer-output.schema.json`을 만족해야 한다. 스키마 위반 시 검증 오류만 덧붙여 1회 재요청하고, 2회째도 실패하면 그 리뷰어를 `excluded`로 표시하고 리포트에 제외 사실과 사유를 남긴다. **`excluded`는 R3.7이 정의하는 리뷰어 실패의 한 형태이므로 R3.7의 단일 리뷰 승인 게이트를 발동한다** — 제외한 채 REVIEW 단계를 마칠 수는 있으나, 남은 리뷰어가 하나뿐인 상태로 CRITIQUE·SYNTHESIS로 전이하려면 승인이 필요하다.
- R3.6 `pr-review-toolkit`의 다섯 에이전트는 모두 자유형식 마크다운 출력을 지시하지만 형태가 갈린다. 네 개는 명시적 표제를 둔다(설치본 실측: `code-reviewer.md:43` `## Output Format`, `pr-test-analyzer.md:58` `**Output Format:**`, `silent-failure-hunter.md:99` `## Your Output Format`, `type-design-analyzer.md:56` `**Output Format:**`). `comment-analyzer.md`에는 그런 표제가 없고 대신 표제 없이 자유형식 출력 구조를 지시한다. 어느 쪽이든 이 스킬의 스키마 주입과 충돌하므로, 호출 프롬프트는 **다섯 에이전트 모두에 대해** 에이전트 본문의 출력 형식 지시보다 이 스킬의 스키마 계약이 우선한다는 것을 명시적으로 선언해야 한다. 플러그인 파일은 수정하지 않으므로(N8) 충돌 해소는 호출 측 프롬프트의 책임이며, 그 문구는 `references/reviewer-contract.md`에 고정한다.
- R3.7 **리뷰어 실패**는 다음 셋 중 하나다: (a) R3.3의 Codex 프리플라이트 실패 또는 모델 거부, (b) R3.5의 스키마 위반 2회로 인한 `excluded`, (c) 리뷰어 호출 자체가 산출물 없이 끝난 경우. 셋 중 하나라도 발생해 남은 리뷰어가 하나뿐이면 자동으로 단일 리뷰로 진행하지 않는다. 사용자에게 단일 리뷰 계속 여부를 묻고, 상태에 단일 리뷰 승인이 기록되기 전에는 CRITIQUE·SYNTHESIS로 전이하지 않는다. 승인 시 리포트와 게시 요약에 "단일 리뷰어" 사실과 실패 유형을 명시한다. Claude 측 에이전트 **일부**가 실패한 것은 여기 해당하지 않는다(R3.9 참조).
- R3.9 **양쪽 리뷰어가 모두 실패하면**(R3.7의 셋 중 어느 조합이든) 게시하지 않고 중단한다. 단일 리뷰 승인을 묻지 않는다 — 승인해도 종합할 산출물이 없다. Claude 측 에이전트가 **일부만** 실패한 경우는 리뷰어 실패가 아니며, 나머지 에이전트로 진행하되 실패한 에이전트 목록과 R3.10으로 계산한 category coverage를 상태·리포트·게시 요약에 남긴다(R7.6a의 커버리지 결손 처리 대상이 된다).
- R3.8 `codex exec --output-schema`에 주입되는 스키마는 그 API가 거부하는 구성을 쓰지 않는다. `gpt-5.6-terra`로 실측된 거부 대상은 두 가지이며 둘 다 HTTP 400이다: **`uniqueItems`**(`'uniqueItems' is not permitted`)와 **정규식 lookaround**(`regex lookaround is not supported`). 근거는 `docs/development/2026-08-25-quality-goal/deviations.md`의 **D-15**다. `schemas/reviewer-output.schema.json`은 이 두 구성을 포함하지 않는다. 경로 탈출을 막는 패턴이 필요하면 같은 편차에서 9개 경로로 동등성이 검증된 lookaround-free 형태 `^([^/~.].*|\.[^/.].*)$`를 쓴다. 이 제약은 API로 전송되는 스키마에만 적용되므로, 로컬 검증 전용인 `critique`·`synthesis`·`publish-plan` 스키마에서는 `uniqueItems`를 써도 된다.
- R3.10 R3.9 후단의 Claude 에이전트 일부 실패가 남긴 category 결손은 아래 **`AGENT_CATEGORY_MAP_V1`**로만 계산한다. 이것은 에이전트를 선택하는 R3.1 표나 finding이 쓸 수 있는 category를 제한하는 출력 whitelist가 아니라, 선택된 에이전트가 실패했을 때 어떤 review 관점이 비었는지를 판정하는 책임 매핑이다. 다섯 에이전트 key와 일곱 category의 합집합은 닫혀 있고, `code-simplifier`와 알 수 없는 key/category는 허용하지 않는다.

  | Claude 에이전트 | 책임 category |
  |---|---|
  | `code-reviewer` | `correctness`, `security`, `performance` |
  | `pr-test-analyzer` | `tests` |
  | `comment-analyzer` | `comments` |
  | `silent-failure-hunter` | `correctness`, `error-handling` |
  | `type-design-analyzer` | `correctness`, `types` |

  canonical agent 순서는 표의 위→아래이고, canonical category 순서는 reviewer-output enum과 같은 `correctness`, `error-handling`, `tests`, `types`, `comments`, `security`, `performance`다. map의 각 배열과 상태의 agent 배열은 이 두 순서의 부분수열로 직렬화한다.

  역방향으로 보면 `correctness`는 `code-reviewer`·`silent-failure-hunter`·`type-design-analyzer`가 중복 담당하고, 나머지 여섯 category는 표의 단일 에이전트가 담당한다. **중복 담당 판정은 "담당자 전원 성공"이 아니라 "선택된 담당자 중 한 명 이상 성공"이다.** 이번 실행에서 category `c`의 선택 담당자·성공 담당자·실패 담당자를 각각 `S(c)`·`OK(c)`·`FAIL(c)`라 할 때, `S(c)`에는 R3.1로 실제 선택된 에이전트만 들어가고 선택되지 않은 에이전트는 실패로 간주하지 않는다. `agent_category_uncovered(c)`는 `FAIL(c)`가 비어 있지 않고 동시에 `OK(c)`가 비어 있을 때만 참이다. 따라서 `correctness` 담당자 하나가 실패해도 다른 **선택된** 담당자가 성공했으면 covered이고, 선택된 담당자가 모두 실패했을 때만 uncovered다. `code-reviewer`가 실패하면 `security`·`performance`는 항상 uncovered이며, `correctness`는 선택된 두 중복 담당자의 성공 여부에 따라 갈린다.

  `references/reviewer-contract.md`는 위 표를 동일한 이름의 canonical JSON 상수 `AGENT_CATEGORY_MAP_V1`로 싣고 `scripts/review_state.py`의 object 상수와 exact deep equality를 이룬다. 상태에는 그 실행이 사용한 `agent_category_map`과 category별 `{selected_agents, successful_agents, failed_agents, covered}`인 `category_coverage`를 canonical 순서로 기록한다. R7.6a와 게시 계획은 이 상태에서 계산된 `covered`만 소비하며 자체 매핑을 다시 만들지 않는다. 상태의 map이 스크립트 상수와 다르거나 선택된 에이전트의 성공·실패가 coverage에 완전히 반영되지 않았으면 lifecycle을 계산하지 않고 `plan`을 비정상 종료해 GitHub 쓰기를 0건으로 만든다. 이 계약 실패를 여섯 번째 결손 reason으로 꾸며 진행하지 않는다.

### R4. 위치 실측 검증

- R4.1 리뷰어 출력은 신뢰할 수 없는 데이터로 취급한다. 모든 finding의 `file`/`line_start`/`line_end`를 `head_sha` 기준 저장소 실측으로 검증한다.
- R4.2 다음 중 하나라도 참이면 `location_valid=false`로 표기하고 inline 게시에서 제외한다: (a) `head_sha` 기준으로 `file`이 존재하지 않는다, (b) `line_start`가 그 파일의 라인 수를 초과한다, (c) **`line_end`가 그 파일의 라인 수를 초과한다**, (d) **`line_start > line_end`이다**. (c)와 (d)가 필요한 이유는 실제 inline 코멘트에 실리는 라인이 `line_end`이고(R7.16) 여러 줄 코멘트의 `start_line`이 `line_start`이기 때문이다. 두 값 중 하나만 검증하면 잘못된 값이 통과해, 원자적 단일 호출인 2단계 게시(R7.12) 전체를 실패시킨다. 요약에는 "위치 미검증"으로 남긴다.
- R4.3 `base_sha..head_sha` diff의 hunk 범위 밖 라인은 `in_diff_range=false`로 표기한다. GitHub inline 코멘트는 diff 범위 안에서만 성립하므로 이 finding은 요약으로 강등한다.
- R4.4 R4.2/R4.3 판정은 LLM이 아니라 `scripts/review_state.py`가 결정적으로 수행한다. `line_start <= line_end` 같은 필드 간 순서 제약은 JSON Schema로 표현할 수 없으므로 스키마가 아니라 이 스크립트 판정으로만 고정된다.

### R5. 교차비평

- R5.1 기본 1라운드, 최대 2라운드. `--rounds 0`은 교차비평을 건너뛴다.
- R5.2 각 리뷰어에게 상대 findings를 `finding_id`와 함께 넘겨 반박을 요구한다. `schemas/critique.schema.json`의 각 항목은 `target_finding_id`, `stance`(`supports`/`challenges`), `evidence`를 required로 갖는다. `target_finding_id`가 현재 finding 집합에 없거나 `evidence`가 빈 항목은 채택하지 않으며 R6.5의 종합자 입력에도 넣지 않는다. 호출한 상위 reviewer group은 스크립트가 알고 있으므로 모델이 실제 reviewer 이름을 산출물에 되풀이하게 하지 않는다.
- R5.3 **새 근거**는 다음과 같이 계산한다: critique 산출물의 각 `evidence` 항목을 `(path, line_start, line_end, normalized_quote)` 튜플로 정규화하고(`normalized_quote`는 연속 공백 축약 + 양끝 공백 제거), 이전 라운드까지의 튜플 합집합에 없는 원소의 개수를 센다. 이 값이 0이면 다음 라운드를 실행하지 않고 종료 사유 `no_new_evidence`를 상태에 기록한다. **기준선 집합은 1차 리뷰(교차비평 이전) findings의 `evidence` 튜플을 포함한다** — 1차 리뷰가 이미 제시한 근거를 되풀이하는 반박은 새 근거가 아니다. 따라서 첫 교차비평 라운드에서도 `no_new_evidence`가 성립할 수 있다. 계산은 `scripts/review_state.py`가 수행한다.
- R5.4 **추상화 이탈 신호**도 스크립트가 결정적으로 계산한다: 한 라운드 반박의 `evidence` 항목 중 `path`가 상태의 `changed_files`에 없는 것의 비율이 0.5 이상이고, 동시에 그 라운드의 반박 건수가 직전 라운드 이하로 줄지 않은 경우 신호가 참이다. **직전 교차비평 라운드가 없는 첫 라운드에서는 두 번째 조건을 거짓으로 간주한다** — 이 신호는 라운드 간 추세를 보는 것이라 최소 두 라운드가 있어야 성립한다. 따라서 첫 라운드에서는 `abstraction_drift`가 발생하지 않는다. 신호가 참이면 스크립트는 종료 사유 후보 `abstraction_drift`를 반환하고, 오케스트레이터는 라운드를 중단한 뒤 사용자에게 종료를 제안한다. 사용자 응답 없이 자동으로 계속하지 않는다.

### R6. 종합

- R6.1 종합자에게 전달되는 것은 R6.5의 **익명화된 per-finding 입력 객체 배열**뿐이다. 실제 `source`·모델명·에이전트명 필드를 제거하고, finding 순서는 `head_sha`를 시드로 결정적으로 섞는다. 단, 제거는 **종합자 입력 view에만** 적용한다. 원본 출처는 `finding_id`별 정렬·중복 제거한 reviewer ID 배열인 상태의 `finding_provenance` sidecar에 보존하고, 종합 결과와 `finding_id`로 다시 결합해 R7.19의 `src`를 만든다. 종합자는 `finding_provenance`와 실제 reviewer-to-alias 대응표에 접근하지 못한다. 이 변환과 분리는 `scripts/review_state.py`가 수행한다.
- R6.2 종합자는 각 finding을 다섯 축으로 독립 판정한다: `truth`(실제 결함인가), `introduced_by_pr`(이 PR이 도입했는가), `location_validity`(위치가 맞는가), `evidence`(근거가 있는가), `actionability`(조치 가능한가).
- R6.3 결과를 `agreed`(익명 두 reviewer group이 지지), `disputed`(근거 있는 반박으로 갈림), `unresolved`(다섯 축 중 적어도 하나의 근거 부족으로 미결), `single_source`(한 reviewer group만 지지하고 다른 group의 지지·반박이 없음)로 분류한다. `disputed`와 `unresolved`는 버리지 않고 "두 리뷰어가 갈린 지점"으로 게시물에 남긴다. R6.5의 `relation`이 `bilateral`·`contested`·`unilateral`이면 비-`unresolved` 분류는 각각 `agreed`·`disputed`·`single_source`여야 한다. `unresolved`는 어느 relation에서도 가능하지만, 다섯 축 중 근거가 부족한 축과 설명을 `unresolved_reason`에 명시해야 한다. `review_state.py`는 relation과 맞지 않는 분류 또는 근거 없는 `unresolved`를 종합 완료로 수락하지 않는다. 실행 형태에 따라 산출 가능한 분류가 다르다.

  | 실행 형태 | 산출 가능한 분류 |
  |---|---|
  | 두 리뷰어 + 교차비평(기본) | `agreed`, `disputed`, `single_source`, `unresolved` |
  | 두 리뷰어 + `--rounds 0` | `agreed`, `single_source`, `unresolved` — 반박 단계가 없으므로 `disputed`를 산출하지 않는다 |
  | 단일 리뷰어(R3.7의 세 실패 유형 중 하나가 발생하고 단일 리뷰 승인이 기록된 실행. `excluded`도 승인을 거친다) | `single_source`, `unresolved` — `agreed`·`disputed`를 산출하지 않는다 |

  `single_source`는 실행 전체가 단일 리뷰어인 경우뿐 아니라 두 리뷰어 실행에서 한쪽만 해당 finding을 제기하고 상대가 `supports`·`challenges` 어느 쪽도 제시하지 않은 경우에도 "교차 검증되지 않음"을 뜻한다. 근거 부족을 뜻하는 `unresolved`와 구별해 게시 요약에 명시한다.
- R6.4 은닉은 **필드 수준**에서만 보장된다. R6.5 `observations`의 title/body/recommendation/evidence와 `critiques`의 evidence 같은 자유 텍스트가 문체·표현·내용으로 출처를 암시할 가능성은 남는 한계이며, 종합자가 Claude이므로 자기선호 편향도 잔존한다. 두 한계를 리포트에 명시하고, 편향이 merge 결정으로 전파되지 않도록 종합자에게 blocking 판단 권한을 주지 않는다(R7.1).
- R6.5 `review_state.py`는 병합 전 실제 출처를 상위 reviewer group `claude`와 `codex`로 묶고, `sha256("synthesis-alias\0" + head_sha + "\0" + reviewer_group)` 오름차순으로 그룹을 정렬한 뒤 `reviewer-1`, `reviewer-2`를 부여한다. 한 reviewer만 남은 실행에는 `reviewer-1`만 있다. 실제 group→alias 대응인 `reviewer_aliases`는 상태의 비공개 sidecar이고 종합자 입력에는 없다. 여러 Claude 에이전트가 같은 finding을 냈어도 하나의 `claude` observation 아래 source-free `claims` 배열로 모두 보존하고, 세부 agent 출처는 R6.1의 `finding_provenance`에 그대로 남긴다.

  종합자 입력 배열의 각 원소는 정확히 다음 닫힌 계약을 따른다.

  | 필드 | 계약 |
  |---|---|
  | `finding_id` | R7.3의 ID |
  | `finding` | 대표 위치·추가 위치와 category·severity 등 병합된 source-free 정규화 finding |
  | `source_count` | 최초 finding을 낸 익명 상위 reviewer group 수. `observations`의 서로 다른 `reviewer` 수와 같고 1 또는 2 |
  | `observations` | reviewer group별 `{reviewer, claims}`. `reviewer`는 `reviewer-1`/`reviewer-2`뿐이고 중복 alias는 없으며, `claims`는 그 group의 모든 source-free 원 주장 `{title, body, failure_scenario, recommendation, evidence}`을 하나 이상 담는 배열 |
  | `critiques` | R5.2를 통과해 이 `finding_id`를 대상으로 한 `{round, reviewer, stance, evidence}`. reviewer는 alias, stance는 `supports`/`challenges`; `(round, reviewer, stance, normalized_evidence)` 순 |
  | `relation` | 아래 규칙으로 스크립트가 계산한 `bilateral`/`unilateral`/`contested` |

  `observations`는 alias 순, 각 `claims`는 `(normalized_title, normalized_body, normalized_failure_scenario, normalized_recommendation, normalized_evidence)` 순이며 완전히 같은 claim만 중복 제거한다. `supporting_groups`는 non-empty claims를 가진 observation의 alias와 `supports` critique를 낸 alias의 합집합이다. 채택된 `challenges` critique가 하나라도 있으면 `relation=contested`, 그렇지 않고 `supporting_groups`가 둘이면 `bilateral`, 나머지는 `unilateral`이다. 따라서 양쪽이 같은 ID를 독립 제기하거나 한쪽 주장에 다른 쪽이 근거를 들어 지지하면 `bilateral`, 한쪽만 제기하고 상대가 입장을 내지 않으면 `unilateral`, 한 방향 또는 양방향의 근거 있는 반박이 있으면 `contested`다. 같은 `finding_id` 병합은 대표 본문만 남기더라도 `observations`의 모든 claim과 `critiques`를 버리지 않는다. `source_count`만 전달하는 대안은 반박 방향과 근거를 잃으므로 쓰지 않는다.

### R7. PR 게시 계약

- R7.1 게시 review 이벤트는 항상 `COMMENT`다. `APPROVE`/`REQUEST_CHANGES`를 발행하는 코드 경로를 두지 않는다.
- R7.2 게시는 `plan`(읽기 전용 계획 산출)과 `apply`(실제 게시) 두 서브커맨드로 나눈다. `apply`는 사용자 승인 이후 명시적으로만 호출되며, `plan`이나 리뷰 파이프라인이 `apply`를 호출하지 않는다.
- R7.3 `finding_id`는 `sha256(normalized_path \0 category \0 normalized_title)`의 앞 12자다. `normalized_title`은 소문자화·연속 공백 축약·양끝 구두점 제거를 거친다. 라인 번호는 포함하지 않는다.
- R7.4 `anchor_fingerprint`는 위치가 유효하면 `head_sha` 기준 해당 `line_end`의 소스 텍스트를 공백 정규화해 `sha256("source\0" + normalized_source_line)`으로 만든다. 위치가 유효하지 않아 소스 라인을 읽을 수 없으면 `sha256("finding\0" + normalized_title + "\0" + normalized_body)`를 fallback 내용 지문으로 쓴다(`normalized_body`는 연속 공백 축약 + 양끝 공백 제거). 따라서 게시되는 모든 finding에 비어 있지 않은 지문이 있고 두 입력 영역은 domain prefix로 충돌하지 않는다. 지문은 라인 이동을 추적하는 보조 키이며 `finding_id`를 대체하지 않는다.
- R7.5 **같은 실행 안에서 `finding_id`가 충돌하면 병합한다.** 대표 위치는 `(line_start, line_end)` 오름차순 첫 항목이고, 나머지 위치는 병합 결과의 `additional_locations` 배열에 담는다. 출처 reviewer ID는 `finding_provenance[finding_id]`의 정렬·중복 제거 배열로 합쳐 어느 출처도 잃지 않는다. 동시에 R6.5가 상위 reviewer group별 원 주장과 이 finding을 대상으로 한 critique를 `observations`·`critiques`에 보존하므로, 대표 본문 하나를 고르는 과정이 합의·단독·반박 판정 입력을 지우지 않는다. inline 코멘트는 대표 위치에만 달고, 모든 위치는 요약 코멘트에 나열한다. 병합은 결정적이며 스크립트가 수행한다.
- R7.6 lifecycle 분류: 이전 게시의 **활성 집합**에 없으면 `new`, 활성 집합에도 있고 지금도 있으면 `persisting`(새 댓글 생성 금지), 활성 집합에는 있었으나 지금 없으면 **R7.6a의 커버리지 판정을 거쳐** `resolved` 또는 `not_re_reviewed`. 활성 집합은 R7.19 인덱스의 `new`·`persisting`·`not_re_reviewed` record와, lifecycle은 `resolved`지만 연결 스레드가 아직 열린 record다. `resolved`이면서 연결 스레드도 이미 해결됐거나 처음부터 스레드가 없던 record는 종결 이력이라 다음 비교 집합에서 제외한다. 따라서 같은 `finding_id`가 훗날 다시 나타나면 `new`가 되어 해결된 스레드 안에 숨지 않는다.
- R7.6a **커버리지 결손 하에서는 `resolved`로 분류하지 않는다.** finding이 이번 실행의 결과에서 사라지는 원인은 실제 해소만이 아니다. 이 스킬 자신이 규정한 결손 경로는 R3.7의 리뷰어 실패 세 유형, R10.2(b)의 범위 축소, R3.9 후단의 Claude 에이전트 일부 실패까지 다섯이며, 그 경로에 걸린 finding은 "고쳐졌는지 다시 보지 않은 것"이지 "고쳐진 것"이 아니다. 판정 입력은 로컬의 이전 `run_id`가 아니라 R7.19가 GitHub에서 복원한 이전 게시 인덱스의 `src`·`path`·`cat`이다.

  `src`와 실패 단위의 매핑도 고정한다. Codex reviewer는 `codex`, Claude reviewer 전체는 `claude:` 접두사를 가진 모든 원소다. R3.9의 일부 실패 에이전트는 현재 상태에서 정확한 agent key로 식별하고 R3.10의 책임표에 조회하며, 과거 record의 `src`가 그 agent였는지를 결손 조건으로 삼지 않는다. 따라서 reviewer 전체 실패는 과거 `src`로, 일부 에이전트 실패는 과거 `cat`과 현재 `category_coverage`로 판정해 두 단위를 오인하지 않는다.

  | 결손 경로 | 인덱스에 대해 수행할 결정적 판정 | `reason` | 결과 |
  |---|---|---|---|
  | R3.7(a) Codex 프리플라이트 실패·모델 거부 | 이전 record의 `src`가 `codex`를 포함 | `codex_unavailable` | `not_re_reviewed` |
  | R3.7(b) R3.5의 `excluded` | 이전 record의 `src`가 제외된 리뷰어를 포함하고, 이번 실행에서 그 finding을 실제로 다시 낸 다른 출처가 없음 | `reviewer_excluded` | `not_re_reviewed` |
  | R3.7(c) 리뷰어 호출이 산출물 없이 종료 | 이전 record의 `src`가 산출물 없이 끝난 리뷰어를 포함하고, 이번 실행에서 그 finding을 실제로 다시 낸 다른 출처가 없음 | `reviewer_no_output` | `not_re_reviewed` |
  | R10.2(b) 범위 축소 | 이전 record의 `path`가 이번 실행의 명시적 검토 경로 집합 밖 | `path_out_of_scope` | `not_re_reviewed` |
  | R3.9 후단의 Claude 에이전트 일부 실패 | 이전 record의 `cat=c`이고 상태의 `category_coverage[c]`에서 `failed_agents`가 비어 있지 않으며 `successful_agents`가 비어 있음, 즉 R3.10의 `agent_category_uncovered(c)`가 참 | `agent_category_uncovered` | `not_re_reviewed` |

  판정 순서는 결정적이다. (1) R7.19의 복원이 `ok`인지 확인하고, (2) 이전 게시 인덱스에는 있지만 이번 결과에는 없는 finding마다 위 표를 위에서 아래로 확인한다. 하나라도 걸리면 `not_re_reviewed`, 모두 해당하지 않을 때만 `resolved`다. 다섯째 행은 인덱스의 `cat`을 R3.10의 고정 상수로 계산해 상태에 기록한 `category_coverage`에 조회할 뿐, `src`나 임의 fixture 매핑에서 담당 category를 추측하지 않는다. 중복 담당 category는 선택된 담당자 중 하나라도 성공하면 covered이고, 선택된 담당자가 모두 실패해야만 `agent_category_uncovered`다. 인덱스 블록 부재, version 불일치, base64 또는 JSON 디코드 실패, 필수 key·값 결손, 중복 `id` record 때문에 `category`·출처·경로 중 하나라도 복원할 수 없으면 `history_restore.status != "ok"`로 두고 **그 실행에서는 `resolved`를 한 건도 만들지 않는다**. 이때 기존 inline 마커로 식별 가능하면서 이번 결과에는 없는 이전 finding만 reason=`history_unavailable`인 `not_re_reviewed`로 보존한다. 이번 결과에도 같은 ID가 있으면 ID 대조만으로 `persisting`이며, 복원할 수 없는 요약 전용 finding에는 어떤 스레드 쓰기도 시도하지 않는다. 판정은 스크립트가 수행하며 finding별 최초 일치 경로와 사용한 인덱스 필드·값을 상태의 `coverage_gap_evidence`에 기록한다.

  이번 실행에서 `resolved`가 된 finding에 연결된 스레드가 있으면 `isResolved=false`인 열린 스레드만 `thread_resolutions`에 넣는다. 처음부터 inline 스레드가 없던 요약 전용 finding은 이번 요약의 `resolved` 목록에만 두어 GraphQL 쓰기를 만들지 않는다. 직전 실행에 이미 `resolved`로 게시되고 스레드도 해결됐거나 없던 record는 R7.6의 종결 이력 필터에서 빠진다. 이 스레드 상태 필터는 커버리지 판정과 별개이며, `viewerCanResolve` 검사는 그 뒤 R7.18에서 수행한다.
- R7.7 lifecycle 별 게시 동작은 다음과 같다.

  | 분류 | 요약 코멘트 | 리뷰 스레드 |
  |---|---|---|
  | `new` | 신규 항목으로 기재 | inline 코멘트 생성 |
  | `persisting` | 유지 항목으로 기재 | 건드리지 않음(새 댓글 생성 금지) |
  | `resolved` | "해소됨" 목록에 기재 | 연결된 열린 스레드만 `resolveReviewThread`로 해결. 요약 전용·이미 해결된 스레드는 호출 없음 |
  | `not_re_reviewed` | **"이번 실행에서 재검토되지 않음" 목록에 사유와 함께 기재** | **건드리지 않음 — resolve 하지 않는다** |

  `resolved`와 `not_re_reviewed`의 차이가 이 표의 요점이다. 미해소 지적을 "해소됨"으로 게시하고 스레드를 자동 해결하면 되돌리기 어려운 외부 쓰기로 커버리지 결손이 굳는다. 스레드에 별도 답글 코멘트는 어느 분류에서도 남기지 않는다 — R7.14 화이트리스트 안의 수단만 쓰기 위한 결정이다.
- R7.8 요약은 PR당 하나의 sticky 코멘트다. 본문에 `<!-- dual-review:summary -->` 마커를 두고, 존재하면 새로 만들지 않고 갱신한다.
- R7.9 inline 코멘트 본문 끝에 `<!-- dual-review:finding:<finding_id> -->` 마커를 둔다. 이것이 inline dedup과 R7.19 인덱스 record 대조의 키다. 전체 메타데이터는 inline마다 중복하지 않고 sticky 요약의 R7.19 인덱스에 둔다.
- R7.10 요약 첫 줄은 `AI-generated review — Claude + Codex — reviewed commit: <head_sha>`로 시작한다.
- R7.11 `apply` 실행 직전 실제 PR head SHA를 다시 조회한다. 고정된 `head_sha`와 다르면 아무것도 게시하지 않고 비정상 종료한다.
- R7.12 **게시는 세 단계로 나뉘며 각 단계의 완료 여부를 상태에 기록한다.**
  1. 요약 코멘트 생성 또는 갱신 (단일 호출)
  2. inline 리뷰 생성 — `POST /repos/{o}/{r}/pulls/{n}/reviews`에 `event: "COMMENT"`와 `comments` 배열을 담는 **단일 원자적 호출**. 부분 성공은 발생하지 않는다.
  3. `resolved` 스레드 해결 — 스레드당 하나의 GraphQL 호출. 성공한 스레드 ID를 개별 기록한다.
- R7.13 `apply`는 멱등이다. 재실행 시 (a) 완료 기록된 단계는 다시 실행하지 않고, (b) 2단계는 기존 코멘트의 `finding_id` 마커를 대조해 이미 게시된 finding을 `comments` 배열에서 제외하며 남는 항목이 없으면 호출 자체를 생략하고, (c) 3단계는 아직 해결되지 않은 스레드만 처리한다.
- R7.14 GitHub 접근은 전부 주입 가능한 클라이언트 인터페이스(R8.2)를 거치고, 클라이언트는 각 호출을 `(kind, method, target)` **3튜플**로 기록한다. `kind`는 `rest`/`graphql`/`cli`, `method`는 REST의 HTTP 메서드 또는 `QUERY`/`MUTATION`/`EXEC`, `target`은 REST 경로 템플릿·GraphQL 오퍼레이션명·`gh` 서브커맨드다. 기록된 모든 3튜플은 화이트리스트(Interfaces 절)의 부분집합이어야 하며, 목록 밖 호출(라벨·상태·머지·assignee 변경, 스레드 답글 등)을 수행하지 않는다. 화이트리스트는 **호출의 종류**를 제한하는 것이지 횟수를 제한하지 않는다 — R8.2의 페이지 순회로 같은 3튜플이 여러 번 기록되는 것은 위반이 아니다.
- R7.15 `--no-publish`는 `plan`까지만 수행하고 `apply`를 실행하지 않으며 게시 호출을 0건으로 만든다.
- R7.16 inline 코멘트 원소는 `path`, `line`, `side`, `body`를 싣고 `body` 끝에 `finding_id` 마커를 둔다. `line`은 finding의 `line_end`, `side`는 `RIGHT`(추가·수정된 쪽)다. `line_start < line_end`인 finding은 `start_line`(= `line_start`)과 `start_side`를 함께 실어 여러 줄 코멘트로 만들고, `line_start == line_end`이면 두 필드를 생략한다. `start_line`이 `line`과 **같은 diff hunk 안에 없으면** 여러 줄 코멘트를 만들지 않고 `line` 단일 라인으로 축소하며, 축소 사실을 상태에 기록한다. **이 축소 규칙의 근거는 실측이 아니라 보수적 선택이다** — 2026-09-04에 조회한 GitHub 공식 REST 문서는 `side`의 허용값(`LEFT`/`RIGHT`)과 기본값(`RIGHT`)은 명시하지만 `start_line`과 `line`이 같은 hunk 안에 있어야 한다는 제약은 명시하지 않는다. 실제 API 반응을 확인하려면 PR에 코멘트를 생성해야 하고 그것은 외부 쓰기라 이 워크플로에서 수행하지 않았다. 축소는 요청 범위를 넓히지 않고 좁히는 방향이므로 전제가 틀려도 안전하다. deprecated인 `position`·`original_position`은 쓰지 않는다.
- R7.18 `apply`는 `resolveReviewThread` 호출 전에 그 스레드의 `viewerCanResolve`를 확인한다. 거짓이면 호출하지 않고 건너뛰며, 건너뛴 스레드 ID와 사유를 상태에 기록하고 요약 코멘트에 남긴다. 권한 부족을 조용히 삼키지 않는다.
- R7.17 기존 게시물 조회 결과에서 각 리뷰 코멘트의 `id`, `node_id`, `pull_request_review_id`, `path`, `line`, `original_line`을 상태에 기록한다. `node_id`는 GraphQL 리뷰 스레드와의 연결 키이고, `original_line`은 라인 이동·outdated comment 대조를 보조한다. 또한 R7.19의 인덱스에서 복원한 `id`·`cat`·`src`·`path`·`line`·`fp`·`run`·`lifecycle`, 연결된 review의 `id`·`commit_id`·`state`, `history_restore`의 상태와 실패 사유를 함께 기록한다. REST의 `pull_request_review_id`로 comment와 review를 연결한다. inline finding은 marker의 `finding_id`와 인덱스 `id`, REST와 인덱스의 `path`, 인덱스 `line`과 REST의 non-null `line` 또는 `original_line` 중 하나, comment의 `pull_request_review_id`와 review의 `id`가 모두 일치해야 한다. 어느 연결도 없거나 다르면 전체 복원 실패로 처리한다. 요약 전용 finding에는 comment·review 연결을 요구하지 않는다.
- R7.19 **게시 이력의 실행 간 source of truth는 GitHub다.** `plan`은 R8.2의 이슈 코멘트·리뷰 코멘트·review·review thread 조회로 이 스킬이 이전에 게시한 finding 집합을 복원한다. 로컬 상태 파일과 git notes는 실행 간 게시 이력 저장소로 쓰지 않는다. 사람이 작성했거나 다른 봇이 작성해 `dual-review` 마커가 없는 코멘트는 복원·분류·resolve 대상이 아니다.

  sticky 요약 본문에는 가시적 리뷰 내용과 별도로 정확히 하나의 기계 판독 인덱스 블록을 둔다.

  ```text
  <!-- dual-review:index v1 <base64(JSON)> -->
  ```

  payload는 UTF-8 JSON의 **표준 base64** 인코딩이며 알파벳은 `A-Z a-z 0-9 + /`와 끝의 padding `=`만 허용한다(base64url 금지). JSON 루트는 `{"findings": [...]}`이고, `findings`는 이번 요약에 기재되는 inline·요약 전용 finding 전부를 `id`당 정확히 한 record로 담아 `(id, path, line)` 순으로 정렬한다. 중복 `id`는 생성 전에 R7.5로 합쳐야 하며 복원 입력에서 발견하면 `invalid`다. 직렬화는 Python 표준 라이브러리의 `json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)` 결과를 UTF-8로 인코딩해 같은 record 집합이 항상 같은 payload를 만들게 한다. 각 record는 다음 key를 모두 갖고 알 수 없는 key를 허용하지 않는다.

  | key | 값과 용도 |
  |---|---|
  | `id` | `finding_id`; inline 마커와 대조하는 소문자 16진수 12자리 식별자 |
  | `cat` | `category`; reviewer-output의 7값 enum 중 하나이며 해시인 `id`에서 역산하지 않는다 |
  | `src` | 출처 reviewer ID의 정렬된 비어 있지 않은 배열. 원소는 `codex` 또는 R3.1이 실제로 선택할 수 있는 다섯 이름 중 하나를 붙인 `claude:<에이전트명>`이며, 그 밖의 값과 `claude:code-simplifier`는 거부한다. 병합된 finding의 복수 출처를 잃지 않는다 |
  | `path`, `line` | 경로 탈출 없는 정규화 저장소 상대 경로와 1 이상 정수인 `line_end`; inline이 없는 요약 전용 finding도 여기서 복원한다 |
  | `fp` | R7.4의 `anchor_fingerprint`; 위치 유효 여부와 관계없이 비어 있지 않은 64자리 소문자 16진수 문자열 |
  | `run` | 이 record를 게시한 R2.5 형식의 `run_id` |
  | `lifecycle` | 게시 당시의 `new`·`persisting`·`resolved`·`not_re_reviewed` 중 하나 |

  `new`·`persisting` record의 메타데이터는 이번 실행의 finding과 `finding_provenance`에서 만들고, 이번 결과에 없는 `resolved`·`not_re_reviewed` record는 직전 인덱스의 `id`·`cat`·`src`·`path`·`line`·`fp`를 그대로 이어받는다. 모든 record의 `run`과 `lifecycle`만 이번 게시 실행 값으로 갱신한다. 이렇게 해야 결손으로 재검토되지 않은 finding의 판정 입력이 다음 실행까지 계속 남는다.

  유효한 이전 인덱스가 없어 메타데이터를 복원하지 못한 legacy inline marker는 예외다. 알 수 없는 `cat`·`src`·`fp`를 지어내 v1 record로 만들지 않고, 가시적 요약에 `history_unavailable` 경고와 ID만 남긴다. 원래 inline marker가 GitHub에 계속 있으므로 다음 실행도 이를 식별해 자동 resolve하지 않는다. 그 ID가 이후 현재 finding으로 다시 나오면 이번 실행의 완전한 메타데이터로 정상 v1 record를 만들 수 있다.

  요약을 갱신할 때 직전 인덱스를 읽어 lifecycle을 계산한 뒤 현재 실행의 전체 record 집합으로 인덱스를 원자적으로 교체한다. 표준 base64 payload에는 `-`가 없으므로 payload 내부에서 HTML 주석을 닫는 `--`가 생기지 않는다. 파서는 주석 내용을 지시문으로 해석하지 않고 version·base64·JSON shape·필드 타입·허용값을 엄격히 검증한다. 실패 시 부분 집합을 반환하지 않고 R7.6a의 `history_unavailable` 기본값으로 전환한다.

### R8. 결정적 스크립트

- R8.1 `scripts/review_state.py`는 실행 상태(대상 고정, 재실행 인자 충돌 검사, 에이전트 선택 기록, R3.10 category coverage 계산, 리뷰어 산출물 등록과 재시도 카운트, 위치 실측 검증, 교차비평 새 근거·추상화 이탈 계산, `finding_provenance`·`reviewer_aliases` 비공개 sidecar 보존, R6.5의 익명 per-finding 종합 입력 생성·셔플, relation과 종합 분류의 정합성 검증, 단일 리뷰 승인 기록, 종합 결과 기록)를 담당한다.
- R8.2 `scripts/publish_findings.py`는 `plan`/`apply` 서브커맨드로 게시 계획 산출과 게시를 담당한다. GitHub 접근은 주입 가능한 클라이언트 인터페이스를 거쳐 테스트에서 fake로 대체할 수 있어야 하며, 인터페이스는 정확히 다음 열 메서드만 노출한다. 각 메서드는 호출을 R7.14의 3튜플로 기록한다. `--pr`가 없을 때는 `git branch --show-current`로 로컬의 현재 브랜치명을 얻은 뒤 `list_open_prs(repo, head_ref=<현재 브랜치>, limit=2)`를 호출한다. 빈 브랜치명(detached HEAD)이면 클라이언트를 호출하지 않고 중단한다. 구현 명령은 `gh pr list --repo <repo> --state open --head <head_ref> --limit <limit> --json number,headRefName,headRefOid,baseRefName,baseRefOid,url`이며 서버 측 `--head` 필터를 limit보다 먼저 적용한다. 결과가 정확히 1건일 때만 그 번호로 `get_pr_meta`를 호출한다. 0건이면 "현재 브랜치 PR 없음", limit에 찬 2건(즉 2건 이상 존재)이면 "대상 모호"로 상태 생성 전에 중단하고 `--pr` 지정을 요구한다. AC-37의 저장소 전체 열린 PR 탐색만 `head_ref=null, limit=1`을 쓴다.

  | 메서드 | 3튜플 |
  |---|---|
  | `get_pr_meta(repo, number)` | `(cli, EXEC, pr view)` |
  | `list_open_prs(repo, head_ref, limit)` | `(cli, EXEC, pr list)` |
  | `list_issue_comments(repo, number)` | `(rest, GET, /repos/{o}/{r}/issues/{n}/comments)` |
  | `list_review_comments(repo, number)` | `(rest, GET, /repos/{o}/{r}/pulls/{n}/comments)` |
  | `list_reviews(repo, number)` | `(rest, GET, /repos/{o}/{r}/pulls/{n}/reviews)` |
  | `list_review_threads(repo, number)` | `(graphql, QUERY, reviewThreads)` |
  | `create_issue_comment(repo, number, body)` | `(rest, POST, /repos/{o}/{r}/issues/{n}/comments)` |
  | `update_issue_comment(repo, comment_id, body)` | `(rest, PATCH, /repos/{o}/{r}/issues/comments/{id})` |
  | `create_review(repo, number, commit_id, event, comments)` | `(rest, POST, /repos/{o}/{r}/pulls/{n}/reviews)` |
  | `resolve_review_thread(thread_id)` | `(graphql, MUTATION, resolveReviewThread)` |

  쓰기 메서드는 뒤의 네 개뿐이다. `plan` 경로는 앞의 여섯 개만 호출한다.

  **게시 이력 복원에 쓰는 네 목록 조회 메서드(`list_issue_comments`, `list_review_comments`, `list_reviews`, `list_review_threads`)는 전체 페이지를 순회해 완전한 목록을 반환한다.** GitHub의 목록 응답은 기본적으로 부분 페이지이고, 게시 멱등성과 R7.19 복원이 기존 marker·index·review 연결을 빠짐없이 찾는 데 의존하므로 부분 조회는 곧 재게시와 `resolved` 오분류를 뜻한다. REST 세 메서드는 `per_page`를 최대로 두고 `Link` 헤더의 `rel="next"`가 없어질 때까지(또는 `gh api --paginate`로) 순회하고, GraphQL 메서드는 `pageInfo.hasNextPage`가 거짓이 될 때까지 커서를 따라간다. 순회가 중간에 실패하면 부분 목록을 반환하지 않고 오류를 올린다 — 불완전한 목록으로 계획을 세우는 것이 조용한 재게시보다 나쁘다.
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

각 기준은 지정된 검증으로 객관적으로 판정한다. 기준 경로는 저장소 루트이고, 단위 테스트는 모두 `dot_claude/skills/dual-review/tests/` 아래에 있다. 모든 AC의 `[실행]` 표시는 Test strategy의 "판정 명령" 표에 있는 정확한 명령과 연결된다. 각 항목 끝의 `검증:` 문구는 그 명령이 단정해야 할 입력·출력이고, 명령 없이 문서 존재만 눈으로 확인하는 AC는 없다.

### 식별자와 위치

- **AC-1** [실행] `finding_id`는 제목의 대소문자·연속 공백·양끝 구두점 차이에 대해 동일한 값을 낸다. 검증: 단위 테스트.
- **AC-2** [실행] `finding_id`는 `line_start`가 달라져도 동일하고, `path` 또는 `category`가 달라지면 달라진다. 검증: 단위 테스트.
- **AC-3** [실행] `anchor_fingerprint`는 위치가 유효할 때 같은 소스 라인 텍스트에 대해 라인 번호와 무관하게 동일하다. 위치 무효 finding은 같은 정규화 title·body에 대해 같은 fallback 지문을 만들고, source 지문과 fallback 지문은 같은 원문이어도 domain prefix 때문에 다르다. 두 경우 모두 64자리 소문자 16진수다. 검증: 단위 테스트.
- **AC-4** [실행] R4.2의 네 조건 각각에 대해 `location_valid=false`가 되고 inline 게시 계획에서 제외된다: 존재하지 않는 파일, 라인 수를 초과하는 `line_start`, **라인 수를 초과하는 `line_end`**, **`line_start > line_end`인 역전**. 네 조건을 모두 만족하지 않는 finding만 `location_valid=true`가 된다. 검증: 네 조건 각각의 픽스처를 갖는 임시 git 저장소 단위 테스트.
- **AC-5** [실행] diff hunk 범위 밖 라인의 finding은 `in_diff_range=false`가 되고 inline이 아니라 요약 항목으로 분류된다. 검증: 단위 테스트.
- **AC-6** [실행] 같은 실행에 동일 `finding_id`가 둘 이상 있으면 하나로 병합되고, 대표 위치는 `(line_start, line_end)` 오름차순 첫 항목이며, 나머지 위치가 `additional_locations`에 모두 담긴다. 서로 다른 출처가 합쳐지면 `finding_provenance[finding_id]`가 reviewer ID의 정렬·중복 제거 배열이고 어느 출처도 빠지지 않으며, R6.5 입력의 상위 reviewer group별 `observations`와 연결된 `critiques`도 병합 전 개수와 내용을 보존한다. 검증: 양쪽 reviewer가 같은 ID를 낸 입력과 한쪽에 같은 ID가 중복된 입력의 단위 테스트.

### 게시 멱등성과 안전

- **AC-7** [실행] 동일한 plan을 두 번 `apply`하면 두 번째 실행의 GitHub 쓰기 호출이 0건이고 종료 코드가 0이다. 검증: fake 클라이언트 단위 테스트.
- **AC-8** [실행] 2단계(inline 리뷰 생성)가 실패한 뒤 재실행하면, 기존 코멘트의 `finding_id` 마커를 대조해 이미 게시된 finding을 제외하고 남은 것만 담은 단일 리뷰 호출이 1건 발생한다. 남는 항목이 없으면 호출이 0건이다. 검증: fake 클라이언트 단위 테스트.
- **AC-9** [실행] 1·2단계가 완료 기록된 뒤 3단계에서 실패한 상태로 재실행하면, 1·2단계 호출이 0건이고 3단계의 미해결 스레드만 처리된다. 검증: fake 클라이언트 단위 테스트.
- **AC-10** [실행] **커버리지 결손이 없는 실행**(R3.7(a) 프리플라이트 실패·모델 거부 없음, R3.7(b) `excluded` 리뷰어 없음, R3.7(c) 산출물 없는 종료 없음, R10.2(b) 범위 축소 없음, R3.9 후단의 실패 에이전트 없음)에서, R7.19 인덱스 복원이 `ok`이고 이전 활성 집합에는 있었으나 현재 리뷰에 없는 `finding_id`는 `resolved`로 분류된다. 연결된 열린 스레드가 있으면 계획에 요약의 "해소됨" 기재와 `resolveReviewThread` 호출이 포함되고, 요약 전용이면 이번 요약 기재만 포함되며, 어느 경우에도 스레드 답글 호출은 없다. 직전 lifecycle이 `resolved`이고 스레드가 이미 해결됐거나 없는 record는 활성 집합에서 빠져 재처리되지 않으며, 그 `finding_id`가 현재 결과에 다시 나타나면 `new`다. 검증: 열린 스레드·요약 전용·종결 이력·재발 네 fake 픽스처 단위 테스트.
- **AC-11** [실행] `apply` 직전 조회한 head SHA가 고정된 `head_sha`와 다르면 종료 코드가 0이 아니고 GitHub 쓰기 호출이 0건이다. 검증: fake 클라이언트 단위 테스트.
- **AC-12** [실행] `<!-- dual-review:summary -->` 마커를 가진 기존 코멘트가 있으면 신규 생성이 아니라 갱신 호출이 계획된다. 검증: 단위 테스트.
- **AC-13** [실행] fake 클라이언트가 수신한 모든 리뷰 생성 호출의 `event` 값이 `COMMENT`다. 추가로 계약 테스트가 `publish_findings.py` 소스를 읽어 문자열 `REQUEST_CHANGES`와 `APPROVE`의 출현 횟수가 각각 0임을 단정한다. 종료 코드가 아니라 카운트를 단정하는 이유는 `grep -c`가 매치 0건일 때 `0`을 출력하면서 종료 코드 1을 반환해 두 기준이 충돌하기 때문이다. 검증: 단위 테스트 + 계약 테스트.
- **AC-14** [실행] fake 클라이언트가 기록한 모든 `(kind, method, target)` 3튜플이 화이트리스트의 부분집합이고, `plan` 경로의 기록에는 쓰기 메서드 네 개의 3튜플이 하나도 없다. 검증: 단위 테스트가 화이트리스트를 상수로 두고 대조한다.
- **AC-15** [실행] `plan` 실행 경로에서 GitHub 쓰기 호출이 0건이고, `publish_findings.py`의 `plan` 진입점이 `apply` 진입점을 호출하지 않는다. 검증: fake 클라이언트 단위 테스트 + AST로 호출 그래프 확인.
- **AC-16** [실행] `--no-publish`로 실행하면 파이프라인 전체에서 GitHub 쓰기 호출이 0건이다. 검증: 단위 테스트.

### 리뷰 파이프라인

- **AC-17** [실행] R3.1 매핑 표의 각 신호에 대해 선택되는 에이전트 집합이 표와 일치하고, `code-simplifier`는 어떤 입력에서도 선택되지 않는다. 선택 결과와 유발 신호가 상태에 기록된다. 검증: 단위 테스트.
- **AC-18** [실행] 1차 리뷰 프롬프트 구성 함수의 출력에 상대 리뷰어의 산출물 경로·내용이 포함되지 않고, CRITIQUE 이전 단계의 상태 조회가 상대 산출물을 반환하지 않는다. 검증: 단위 테스트.
- **AC-19** [실행] 스키마 위반 산출물은 1회 재요청 후 2회째 실패에서 해당 리뷰어가 `excluded` 상태가 되고 사유가 기록된다. 3회째 재요청은 발생하지 않는다. 검증: 단위 테스트.
- **AC-20** [실행] 단일 리뷰 승인이 상태에 기록되지 않은 채로는 리뷰어 하나가 실패한 실행이 SYNTHESIS 단계로 전이하지 않는다. 검증: 단위 테스트.
- **AC-21** [실행] 새 근거 수가 0인 라운드 뒤에는 다음 라운드가 실행되지 않고 종료 사유 `no_new_evidence`가 기록된다. 라운드 수는 2를 초과할 수 없다. **첫 교차비평 라운드의 기준선 집합이 1차 리뷰 findings의 `evidence` 튜플을 포함해, 1차 리뷰가 이미 댄 근거만 되풀이한 반박에 대해 첫 라운드에서 `no_new_evidence`가 성립한다.** 검증: 단위 테스트.
- **AC-22** [실행] R5.4의 두 조건이 모두 참인 입력에서 `abstraction_drift`가 반환되고, 하나라도 거짓이면 반환되지 않는다. **직전 교차비평 라운드가 없는 첫 라운드 입력에서는 첫 조건이 참이어도 반환되지 않는다.** 검증: 단위 테스트.
- **AC-23** [실행] 종합자 입력 페이로드의 구조화 metadata에는 `source`·`finding_provenance`·`reviewer_aliases` 필드와 실제 reviewer·모델 식별자(`claude`, `codex`, `gpt-5.6`, `pr-review-toolkit`, 에이전트 이름 6종)가 없고, reviewer 식별값은 `reviewer-1`/`reviewer-2`뿐이다. 자유 텍스트 `body`·`recommendation`·`evidence`의 잔존 누출 가능성은 R6.4의 명시된 한계로 별도 취급한다. 같은 입력에서 비공개 상태의 `finding_provenance`에는 각 `finding_id`의 실제 reviewer ID 집합이, `reviewer_aliases`에는 실제 상위 group→alias 대응이 보존되고, 종합 결과와 재결합한 R7.19 record의 `src`는 alias가 아니라 `finding_provenance`의 실제 ID 배열과 일치한다. 검증: 종합자 payload와 두 private sidecar, R7.19 record를 함께 단정하는 단위 테스트.
- **AC-24** [실행] 동일 입력과 동일 `head_sha`에 대해 셔플 순서가 재현되고, `head_sha`가 다르면 순서가 달라진다. 검증: 단위 테스트.
- **AC-25** [실행] R10.1 임계값을 넘는 입력에서 파이프라인이 사용자 결정 없이 다음 단계로 전이하지 않고, 범위를 축소한 경우 축소된 경로 집합과 제외 파일 수가 상태에 기록되며 **`plan`이 생성한 요약 코멘트 본문에도 축소 사실과 제외 파일 수가 포함된다**. 검증: 단위 테스트.

### 계약과 배치

- **AC-26** [실행] `schemas/` 아래 네 개 스키마(`reviewer-output`, `critique`, `synthesis`, `publish-plan`) 전부의 루트가 `"type": "object"`이고, 각각 유효 픽스처는 통과하고 무효 픽스처는 실패한다. 검증: 단위 테스트.
- **AC-27** [실행] `codex exec`가 `schemas/reviewer-output.schema.json`을 `--output-schema`로 수락한다. 검증: 최소 프롬프트로 실제 `codex exec`를 1회 실행해 종료 코드 0과 스키마를 만족하는 결과 파일을 얻는다. 이 실행은 `--sandbox read-only`다. `codex` CLI 미설치·모델 거부·네트워크 실패로 실행 자체가 불가능하면 이 기준을 `blocked`로 기록하고 그 사실과 실패 출력을 리포트에 남긴다. 실행하지 못한 것을 통과로 기록하지 않는다.
- **AC-28** [실행] `SKILL.md` frontmatter가 R1.3의 일곱 필드를 모두 갖고, **파싱된 값이 `disable-model-invocation: true`(불리언 참), `model: "inherit"`, `effort: "high"`와 각각 일치하며**, `version` 값이 `MAJOR.MINOR.PATCH` 형식이고, `SKILL.md`가 참조하는 모든 상대 경로 파일이 실재하고, 다음 지시 문구가 모두 존재한다: R1.4의 네 플래그(`--pr`, `--base`, `--rounds`, `--no-publish`), R3.3의 Codex 프리플라이트 단계와 실패 시 단일 리뷰 승인 경로, R3.7의 단일 리뷰 승인 게이트, R7.2의 게시 승인 게이트. 검증: 계약 테스트.
- **AC-29** [실행] 스킬 디렉터리 전체에서 `--full-auto`, `--yolo`, `--skip-git-repo-check` 문자열이 0건이고, `gpt-5.6-terra`와 `model_reasoning_effort="high"`가 Codex 호출 계약 문서에 존재한다. 검증: `grep -REn -- '--full-auto|--yolo|--skip-git-repo-check' dot_claude/skills/dual-review/` 매치 0건 + 계약 테스트.
- **AC-30** [실행] 두 스크립트가 import하는 모든 최상위 모듈이 **Python 표준 라이브러리이거나 같은 `scripts/` 디렉터리의 형제 모듈**이다. 외부 패키지 import는 0건이다. 검증: `ast`로 import를 추출해 `sys.stdlib_module_names` ∪ {`scripts/` 아래 `.py` 파일의 스템}과 대조하는 단위 테스트. 형제 모듈을 허용하는 이유는 선례인 `quality_state.py`가 `from validate_review import validate_review`로 같은 패턴을 쓰기 때문이며, R8.3이 금지하는 것은 외부 패키지 추가이지 내부 모듈 분리가 아니다.
- **AC-31** [실행] 두 스크립트 소스에 `GH_TOKEN`, `GITHUB_TOKEN`, `Authorization` 문자열이 등장하지 않는다. 검증: 계약 테스트.
- **AC-32** [실행] `.claude/dual-review-state/` 무시 여부 확인 분기가 무시되지 않은 경우 경고를 산출하고, 무시된 경우 경고를 산출하지 않는다. 검증: 단위 테스트.
- **AC-33** [실행] `dot_claude/skills/dual-review/` 아래에 R1.2가 규정한 다섯 구성이 모두 존재하고(`SKILL.md` 파일, `references/`·`schemas/`·`scripts/`·`tests/` 디렉터리), `templates/`와 `evals/` 디렉터리는 없다. 검증: 계약 테스트.
- **AC-34** [실행] 전체 결정적 테스트가 통과한다. 검증: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'` 종료 코드 0.
- **AC-35** [실행] `chezmoi --source "$PWD" target-path dot_claude/skills/dual-review/SKILL.md`가 종료 코드 0이고 `~/.claude/skills/dual-review/SKILL.md`의 절대 경로를 출력한다. 검증: 판정 명령 CHEZMOI. 이 워크트리를 명시하지 않은 `chezmoi diff`는 main checkout을 source로 볼 수 있어 판정에 쓰지 않는다.
- **AC-36** [실행] `.claude/dual-review-state/`가 이 저장소에서 무시된다. 검증: `git check-ignore -v .claude/dual-review-state/` 종료 코드 0.
- **AC-37** [실행] `plan`이 실제 GitHub 응답으로 동작한다. 검증: 검증 시점에 `gh pr list --state open --limit 1 --json number`로 조회한 열린 PR을 대상으로 `publish_findings.py plan`을 빈 finding 집합으로 실행해 종료 코드 0을 얻고, 산출된 `plan.json`이 `schemas/publish-plan.schema.json`을 만족하며, 기록된 3튜플에 쓰기 메서드가 0건임을 확인한다. 열린 PR이 없으면 이 기준을 `not applicable`로 기록하고 그 사실을 리포트에 남긴다.
- **AC-38** [실행] `docs/dual-review-maintenance.md`가 존재하고 R9.1의 네 절(갱신 신호 추적, 의존 CLI·플러그인 점검, 결정적 테스트 실행 명령, 버전 정책)을 모두 포함하며, "버전 정책" 절이 MAJOR·MINOR·PATCH 세 자리 각각에 어떤 변경이 대응하는지 기술한다. 검증: 계약 테스트.
- **AC-39** [실행] `plan`이 생성한 요약 코멘트 본문의 첫 줄이 `AI-generated review — Claude + Codex — reviewed commit: ` 로 시작하고 그 뒤에 상태의 `head_sha`가 온다. 검증: 단위 테스트.
- **AC-40** [실행] `references/synthesis-contract.md`가 R6.4의 두 잔존 한계(텍스트 본문을 통한 출처 누출, 종합자 자기선호 편향)를 모두 명시한다. 검증: 계약 테스트.
- **AC-41** [실행] `schemas/critique.schema.json`이 각 반박 항목에 `target_finding_id`·`stance`·`evidence`를 required로 요구하고, `stance`를 `supports`/`challenges` enum으로, `evidence`를 `minItems: 1`로 강제한다. 빈 evidence나 현재 finding 집합에 없는 target ID는 채택·새 근거 계산·R6.5 `critiques` 어디에도 반영되지 않는다. 검증: 유효·필드별 무효·unknown target 픽스처 단위 테스트.
- **AC-42** [실행] `schemas/synthesis.schema.json`이 각 finding 판정에 다섯 축(`truth`, `introduced_by_pr`, `location_validity`, `evidence`, `actionability`)을 모두 `required`로 강제하고, 하나라도 빠진 픽스처는 검증에 실패한다. 검증: 유효·무효 픽스처 단위 테스트.
- **AC-43** [실행] `schemas/synthesis.schema.json`이 각 finding의 분류를 `agreed`/`disputed`/`unresolved`/`single_source` 네 값의 `enum`으로 강제한다. `unresolved`이면 다섯 축 중 하나를 가리키는 non-empty `unresolved_reason`이 필수이고, 다른 분류에는 그 필드가 없어야 한다. enum 밖 분류·근거 없는 `unresolved`·비-`unresolved`의 잔여 reason 픽스처는 실패한다. 검증: 유효·무효 픽스처 단위 테스트.
- **AC-44** [실행] `schemas/reviewer-output.schema.json`에 `uniqueItems` 키가 없고, 어떤 `pattern` 값에도 정규식 lookaround(`(?=`, `(?!`, `(?<=`, `(?<!`)가 없다. 검증: 계약 테스트가 스키마를 재귀 순회해 확인한다.
- **AC-45** [실행] Claude 에이전트 호출 프롬프트를 구성하는 함수의 출력이, 에이전트 자체 `Output Format` 절보다 스키마 계약이 우선한다는 선언 문구를 포함하고 그 문구가 `references/reviewer-contract.md`의 상수와 일치한다. 검증: 단위 테스트 + 계약 테스트.
- **AC-46** [실행] 생성된 모든 코멘트 원소에서 **`line`이 finding의 `line_end`와 같고 `side`가 `"RIGHT"`다.** 그리고 `line_start == line_end`인 finding의 원소에는 `start_line`·`start_side`가 없고, `line_start < line_end`이면서 두 라인이 같은 hunk 안인 finding의 원소에는 `start_line == line_start`와 `start_side`가 있으며, 두 라인이 서로 다른 hunk에 있으면 `start_line`이 없고 축소 사실이 상태에 기록된다. 어떤 원소에도 `position` 키가 없다. 검증: 단위 테스트.
- **AC-47** [실행] 기존 리뷰 코멘트 조회 결과로부터 `id`·`node_id`·`pull_request_review_id`·`path`·`line`·`original_line`이 상태에 기록되고, `pull_request_review_id`로 연결된 review의 `id`·`commit_id`·`state`, 인덱스에서 복원한 `id`·`cat`·`src`·`path`·`line`·`fp`·`run`·`lifecycle`, `history_restore.status`·실패 사유도 상태에 기록된다. 검증: fake 클라이언트 단위 테스트.
- **AC-48** [실행] Codex 호출 계약 문서와 프롬프트·명령 구성 함수의 출력에 `--sandbox read-only`가 존재하고, `--sandbox`의 다른 값(`workspace-write`, `danger-full-access` 등)이 스킬 디렉터리 어디에도 등장하지 않으며, R3.2가 열거한 `--ephemeral`·`--output-schema`·`--output-last-message`·`--json`·`--model`·`-c model_reasoning_effort`가 모두 존재한다. 검증: 계약 테스트.
- **AC-49** [실행] 게시 이력 목록 조회 메서드 넷이 전체 페이지를 순회한다. 2페이지에 걸친 응답을 반환하는 fake 클라이언트에서, **2페이지째에만 inline `finding_id` 마커·요약 인덱스·연결 review·thread가 있는 finding도 모두 복원되고 `persisting`으로 분류되어 재게시되지 않으며**, 같은 조건에서 `resolved` 판정도 오분류되지 않는다. 네 메서드 중 하나라도 순회 중 오류가 나면 부분 목록을 반환하지 않고 예외가 전파된다. 검증: 메서드별 다중 페이지 fake 클라이언트 단위 테스트.
- **AC-50** [실행] R6.5의 relation과 비-`unresolved` 분류가 `bilateral→agreed`, `unilateral→single_source`, `contested→disputed`로 정확히 대응하고, 다른 조합은 `review_state.py`의 종합 결과 검증에서 거부된다. `--rounds 0` 입력에는 accepted challenge가 없어 `contested`·`disputed`가 없고, 단일 리뷰어 실행에는 `bilateral`·`agreed`가 없다. `unresolved`는 relation과 무관하게 허용하되 유효한 `unresolved_reason`이 있어야 한다. 검증: relation 세 값의 올바른/잘못된 분류 행렬, rounds 0, 단일 리뷰어, unresolved reason 단위 테스트.
- **AC-51** [실행] INTAKE 후 상태에 `repo`·`pr_number`·`base_sha`·`head_sha`·`changed_files` 다섯 값이 모두 기록되고, 이후 단계는 base·변경 파일·대상 PR을 다시 조회하거나 바꾸지 않는다. fake 호출 기록에는 허용된 R7.19의 이력 조회 네 메서드와 R7.11의 head SHA 재확인 1회 외의 메타데이터 재조회가 0건이다. 검증: fake 클라이언트 호출 기록 단위 테스트.
- **AC-52** [실행] `schemas/publish-plan.schema.json`을 만족하지 않는 계획 파일로 `apply`를 실행하면 종료 코드가 0이 아니고 GitHub 쓰기 호출이 0건이다. 검증: fake 클라이언트 단위 테스트.
- **AC-53** [실행] `--rounds 0`으로 실행하면 교차비평 라운드가 0회이고 critique 산출물이 생성되지 않으며, 상태의 `critique_rounds`가 빈 목록이다. 검증: 단위 테스트.
- **AC-54** [실행] `--base`가 PR의 실제 base와 다르면 (a) 상태에 base 불일치 사실과 두 ref(`requested_ref`, `actual_base_sha`)가 기록되고, (b) `plan`의 `base_mismatch`가 non-null이며 그때 `inline_review.skip`이 반드시 참이고, (c) 모든 finding이 `summary_only_findings`로 들어가며, (d) 요약 본문에 base 불일치 사실과 두 ref가 포함된다. 같으면 `base_mismatch`가 null이고 정상 경로로 동작한다. 검증: 단위 테스트.
- **AC-55** [실행] `--pr`가 없을 때 `list_open_prs(repo, head_ref=<현재 브랜치>, limit=2)`가 정확히 1회 호출되고, 결과 1건이면 그 번호로 `get_pr_meta`를 호출해 대상으로 삼는다. 결과가 0건이거나 limit에 찬 2건(2건 이상 존재)이면 상태를 만들지 않고 종료 코드 != 0으로 중단하며 `--pr` 지정을 안내한다. 빈 현재 브랜치명에서는 두 GitHub 메서드 모두 0회다. 전역 `list_open_prs(repo, head_ref=null, ...)`로 현재 브랜치 PR을 추측하지 않는다. 검증: fake 클라이언트 단위 테스트(1건/0건/2건/detached HEAD 네 경우와 호출 인자 단정).
- **AC-56** [실행] `abstraction_drift` 신호가 참인 상태에서 사용자 결정이 상태에 기록되기 전에는 다음 교차비평 라운드도 SYNTHESIS 전이도 일어나지 않는다. 검증: 단위 테스트.
- **AC-57** [실행] R10.1 임계값 초과 시 사용자가 중단을 선택하면 상태가 중단으로 기록되고 이후 단계가 실행되지 않으며 GitHub 쓰기 호출이 0건이다. 검증: 단위 테스트.
- **AC-58** [실행] `viewerCanResolve`가 거짓인 스레드에 대해 `resolveReviewThread` 호출이 발생하지 않고, 건너뛴 스레드 ID와 사유가 상태에 기록되며 요약 본문에 포함된다. 참인 스레드는 정상 호출된다. 검증: fake 클라이언트 단위 테스트.
- **AC-59** [실행] 양쪽 리뷰어가 모두 실패한 실행에서는 단일 리뷰 승인을 묻지 않고 중단하며 GitHub 쓰기 호출이 0건이다. 검증: 단위 테스트.
- **AC-60** [실행] `references/reviewer-contract.md`에 기록된 상수가 스크립트가 실제로 쓰는 값과 일치한다: `CODE_EXT` 집합, 확장자별 주석 토큰 표, `comment-analyzer` 매치 임계 3, 규모 임계값 파일 100개·diff 20,000줄, R3.10의 `AGENT_CATEGORY_MAP_V1`. 마지막 상수는 다섯 agent key가 정확히 일치하고 category 배열도 canonical 순서까지 같으며 합집합이 reviewer-output의 일곱 category와 같다. 상태의 `agent_category_map`은 그 상수와 exact deep equality이고, 중복 `correctness` 담당자 일부 성공/일부 실패 및 전원 실패 픽스처의 `category_coverage`가 R3.10의 집합식과 일치한다. map 불일치·category 누락·선택 agent 상태 누락 각각에서는 `plan`이 비정상 종료하고 lifecycle 결과와 GitHub 쓰기가 0건이다. 검증: 계약 테스트가 문서 canonical JSON·스크립트 상수·생성 상태를 파싱해 대조하고 세 손상 상태를 실행한다.
- **AC-61** [실행] 같은 `repo`·`pr_number`·`head_sha` 입력에 대해 `run_id`가 재현되고, `head_sha`만 다르면 달라진다. 기존 상태 디렉터리가 없으면 새로 만들고, 있으면 새 호출의 `requested_base_ref`·새로 해석한 `base_sha`·`actual_base_sha`·유효 `rounds`가 상태의 고정값과 모두 같은 경우에만 읽어 이어간다. 하나라도 다르면 종료 코드 != 0이고 충돌 필드와 기존값·새 값이 출력되며, 상태 파일은 바뀌지 않고 이후 단계와 GitHub 쓰기 호출은 0건이다. 검증: 정상 재개, `--base` 문자열 충돌, 같은 ref 문자열의 target SHA 이동, PR 실제 base SHA 이동, `--rounds` 충돌 각각의 단위 테스트.
- **AC-62** [실행] R7.6a의 다섯 결손 경로 각각에 대해, R7.19 인덱스에서 복원한 이전 finding이 현재 결과에 없으면 `resolved`가 아니라 `not_re_reviewed`로 분류되고, 그 finding의 스레드에 `resolveReviewThread` 호출이 발생하지 않으며, 요약 본문의 "재검토되지 않음" 목록과 상태의 `coverage_gap_evidence`에 최초 일치 사유와 판정 필드·값이 나타난다. 에이전트 일부 실패 경로는 `code-reviewer→security`, `pr-test-analyzer→tests`, `comment-analyzer→comments`, `silent-failure-hunter→error-handling`, `type-design-analyzer→types`의 다섯 픽스처에서 각각 `agent_category_uncovered`가 되어 이 결과를 만족해야 한다. 중복 `correctness`는 선택된 담당자 중 일부가 실패하고 하나가 성공하면 그 사유가 생기지 않으며, 선택된 담당자 전원이 실패하면 생긴다. 다섯 조건이 모두 해당하지 않고 인덱스 복원이 `ok`일 때만 `resolved`가 된다. 인덱스가 없거나 version·base64·JSON·필수 필드·마커 대조 중 하나가 잘못된 픽스처에서는 `resolved`가 0건이고, inline 마커로 식별 가능하면서 현재 결과에는 없는 이전 finding 전부가 reason=`history_unavailable`인 `not_re_reviewed`이며 `resolveReviewThread` 호출이 0건이다. 현재 결과에도 같은 ID가 있는 finding은 `persisting`이다. 검증: 실제 인덱스 디코드와 실제 `AGENT_CATEGORY_MAP_V1` 상태 계산부터 시작하는 결손·중복 담당·복원 실패 fake 클라이언트 단위 테스트.
- **AC-63** [실행] R3.7이 열거한 세 실패 유형 각각에서 단일 리뷰 승인이 상태에 기록되기 전에는 CRITIQUE·SYNTHESIS로 전이하지 않는다. 특히 R3.5의 `excluded` 경로도 승인 게이트를 발동한다. 검증: 세 유형 각각의 단위 테스트.
- **AC-64** [실행] R7.19 형식으로 만든 요약 인덱스를 **로컬 상태 루트가 비어 있고 git notes가 없는** 다음 head SHA 실행의 `list_issue_comments` 결과로 돌려주면, 디코드 후 `id`·`cat`·`src`·`path`·`line`·`fp`·`run`·`lifecycle` 값과 finding 집합이 원본과 정확히 같고 `history_restore.status == "ok"`다. inline marker ID·REST `path`·REST의 non-null `line` 또는 `original_line`·`pull_request_review_id`가 같은 인덱스 record·review·thread에 연결된다. fake subprocess 기록에 `git notes` 호출과 이전 `run_id` 디렉터리 탐색이 0건이다. 검증: 현재 line 일치, 이동 후 original_line 일치, outdated line=null 세 경우의 생성 → GitHub fake 응답 → 로컬 이력 없는 복원 왕복 단위 테스트.
- **AC-65** [실행] 인덱스 부재, 지원하지 않는 version, 잘못된 base64, 잘못된 JSON, 필수 key/값 결손, unknown key·잘못된 타입·허용 밖 enum, 중복 `id` record, inline marker와 인덱스의 ID·path·line 불일치, comment가 가리키는 review 부재 각각에서 `history_restore.status != "ok"`, `resolved` 0건, `resolveReviewThread` 0건이고, inline marker로 식별 가능하면서 현재 결과에는 없는 이전 finding은 reason=`history_unavailable`인 `not_re_reviewed`다. 현재에도 같은 ID가 있으면 `persisting`이며, 어느 실패도 부분 복원 집합을 반환하지 않는다. 검증: 실패 유형별 fake 클라이언트 단위 테스트.
- **AC-66** [실행] 인덱스 payload가 표준 base64 정규식 `^[A-Za-z0-9+/]+={0,2}$`에 일치하고 payload 자체에는 `-`가 0개이며, 디코드하면 UTF-8 JSON object가 된다. 같은 record 집합은 입력 순서와 무관하게 같은 payload를 만든다. 검증: 문자 `+`·`/`·padding `=`을 실제로 만드는 픽스처와 순서 변이 단위 테스트.
- **AC-67** [실행] `in_diff_range=false` 또는 R2.1a base 불일치로 inline에서 요약으로 강등되어 review comment가 전혀 없는 finding도 인덱스에서 `path`·`line`과 나머지 필드를 복원하고, 다음 실행에 같은 `id`가 있으면 `persisting`으로 분류되어 신규 inline·resolve 호출이 0건이다. 검증: 요약 전용 finding 왕복 fake 클라이언트 단위 테스트.
- **AC-68** [실행] 다섯 결손 경로 테스트는 분류 함수에 `path`·`cat`·`src`나 agent-category 매핑을 직접 주입하지 않고 R7.19의 인코딩된 이전 요약, GitHub comment/review/thread 응답, `review_state.py`가 `AGENT_CATEGORY_MAP_V1`에서 만든 현재 상태만 입력으로 사용한다. 에이전트 일부 실패는 다섯 에이전트 각각의 고유 책임 category와 `correctness` 중복 담당의 일부 성공/전원 실패를 모두 거쳐, 디코드된 `cat`과 상태의 `category_coverage`가 `coverage_gap_evidence`로 이어지고 AC-62의 `not_re_reviewed`·resolve 0건 단정이 성립한다. 검증: 다섯 결손 경로와 에이전트별·중복 담당별 게시 이력 복원 통합 단위 테스트.
- **AC-69** [실행] 같은 raw reviewer-output·critique 입력을 R7.5 병합과 R6.5 변환에 통과시키면 각 synthesis item의 key가 정확히 `finding_id`·`finding`·`source_count`·`observations`·`critiques`·`relation`이고, 각 observation의 key는 정확히 `reviewer`·`claims`이며 `source_count == observations의 고유 reviewer 수`, alias와 중첩 claims/critique 배열 정렬, relation 계산이 R6.5와 일치한다. 병합 전 양쪽의 원 주장, 같은 Claude group 안의 서로 다른 agent 주장, accepted critique는 완전히 같은 claim 외에는 빠지지 않으며 actual reviewer ID는 payload metadata에 없고 private `finding_provenance`·`reviewer_aliases`에만 있다. 검증: 같은 ID의 양쪽 주장, 한쪽 주장, 지지, 한 방향 반박, 양방향 반박, 여러 Claude 에이전트 중복의 변환 단위 테스트 + 중첩 닫힌 key 계약 테스트.
- **AC-70** [실행] raw 입력부터 생성한 **같은 `finding_id`** 세 픽스처가 다음 결과로 이어진다: 양쪽이 독립 제기하고 accepted challenge가 없으면 `relation=bilateral`·`classification=agreed`, 한쪽만 제기하고 상대 입장이 없으면 `relation=unilateral`·`classification=single_source`, 양쪽이 서로 근거 있는 `challenges`를 내면 `relation=contested`·`classification=disputed`. 각 fixture에서 다른 두 비-`unresolved` 분류를 넣은 synthesis 결과는 검증에 실패한다. 별도 근거 부족 fixture의 `unresolved`는 유효한 `unresolved_reason`이 있을 때만 통과한다. 검증: raw reviewer-output → ID 병합 → critique 연결 → 익명화 → synthesis 결과 검증의 end-to-end 단위 테스트.

### 요구사항 추적

모든 요구사항이 하나 이상의 수용 기준에 대응한다. 대응이 없는 요구사항은 존재하지 않는다.

| 요구사항 | 수용 기준 | 요구사항 | 수용 기준 |
|---|---|---|---|
| R1.1 | AC-35 | R6.4 | AC-40 |
| R1.2 | AC-33 | R7.1 | AC-13 |
| R1.3 | AC-28 | R7.2 | AC-15 |
| R1.4 | AC-28, AC-55 | R7.3 | AC-1, AC-2 |
| R2.1 | AC-51 | R7.4 | AC-3 |
| R2.1a | AC-54 | R7.5 | AC-6 |
| R2.2 | AC-51 | R7.6 | AC-10, AC-62 |
| R2.3 | AC-32 | R7.6a | AC-62, AC-65, AC-68 |
| R2.4 | AC-36 | R7.7 | AC-10, AC-62 |
| R2.5 | AC-61, AC-64 | R7.8 | AC-12, AC-64, AC-66 |
| R3.1 | AC-17, AC-60 | R7.9 | AC-8 |
| R3.2 | AC-29, AC-48 | R7.10 | AC-39 |
| R3.3 | AC-28, AC-20 | R7.11 | AC-11 |
| R3.4 | AC-18 | R7.12 | AC-8, AC-9 |
| R3.5 | AC-19, AC-63 | R7.13 | AC-7, AC-8, AC-9, AC-49 |
| R3.6 | AC-45 | R7.14 | AC-14 |
| R3.7 | AC-20, AC-63 | R7.15 | AC-16 |
| R3.8 | AC-44 | R7.16 | AC-46 |
| R3.9 | AC-59, AC-62, AC-68 | R7.17 | AC-47, AC-64, AC-67 |
| R4.1 | AC-4 | R7.18 | AC-58 |
| R4.2 | AC-4 | R8.1 | AC-4, AC-5, AC-17~AC-25, AC-61 |
| R4.3 | AC-5 | R8.2 | AC-14, AC-15, AC-49, AC-55, AC-64 |
| R4.4 | AC-4, AC-5 | R8.3 | AC-30 |
| R5.1 | AC-21, AC-53 | R8.4 | AC-31 |
| R5.2 | AC-41 | R8.5 | AC-26, AC-37, AC-52 |
| R5.3 | AC-21 | R9.1 | AC-38 |
| R5.4 | AC-22, AC-56 | R9.2 | AC-28, AC-38 |
| R6.1 | AC-23, AC-24, AC-69 | R10.1 | AC-25, AC-60 |
| R6.2 | AC-42 | R10.2 | AC-25, AC-57 |
| R6.3 | AC-43, AC-50, AC-70 | R10.3 | AC-25 |
| R3.10 | AC-60, AC-62, AC-68 | R6.5 | AC-23, AC-50, AC-69, AC-70 |
| R7.19 | AC-64~AC-68 | — | — |

R7.6·R7.6a·R7.7의 기존 `AC-10, AC-62` 매핑은 AC-62가 다섯 결손 경로와 복원 실패까지 직접 단정하고 AC-10이 그 보집합을 단정하므로 유지한다. R3.10의 agent-category 상수는 AC-60이 계약을, AC-62·68이 GitHub 복원 뒤 실제 lifecycle 결과를 판정한다. R6.5의 정보 보존은 AC-23·69가 입력 경계를, AC-50·70이 relation→classification 결과를 판정한다. R7.19의 end-to-end 연결은 AC-64~AC-68이 맡는다. AC-27(codex 구조화 출력 수락)과 AC-34(전체 결정적 테스트 통과)는 개별 요구사항이 아니라 R3.8·R8.5의 실행 가능성과 스위트 전체를 검증하는 메타 기준이므로 표에 별도 행을 두지 않는다. 매핑은 요구사항 문언을 실제로 판정하는 기준만 싣는다 — 관련은 있으나 그 문언을 단정하지 못하는 AC는 등재하지 않는다.

## Architecture

### 컴포넌트

| 컴포넌트 | 책임 | 형태 |
|---|---|---|
| `SKILL.md` | 단계 표, 각 단계의 필수 행동, 두 승인 게이트, 참조 파일 로딩 지시 | 마크다운 지시서 |
| `references/reviewer-contract.md` | 두 리뷰어 공통 계약(구조화 출력, 근거 규율, finding bar), 에이전트 선택 표, `AGENT_CATEGORY_MAP_V1`, Codex 호출 템플릿과 모델·effort, 입력 규모 임계값 | 마크다운 |
| `references/cross-critique.md` | 교차비평 라운드 규칙, 새 근거 정의, 추상화 이탈 신호 정의, 종료 규칙 | 마크다운 |
| `references/synthesis-contract.md` | 종합자 계약(R6.5 익명 per-finding 입력, relation→분류 규칙, 5축 판정, 잔존 한계) | 마크다운 |
| `references/publish-contract.md` | 게시 계약(SHA 고정, inline 마커 + 요약 인덱스, GitHub 이력 복원, 다섯 결손 경로, 3단계 게시, lifecycle, 엔드포인트 화이트리스트, verdict 정책, 롤백 한계) | 마크다운 |
| `schemas/reviewer-output.schema.json` | 리뷰어 산출 (루트 object, `{"findings": [...]}`). `uniqueItems`·lookaround 미사용 | JSON Schema 2020-12 |
| `schemas/critique.schema.json` | 교차비평 산출 (루트 object). target ID·stance·non-empty evidence required | JSON Schema 2020-12 |
| `schemas/synthesis.schema.json` | 종합 산출 (루트 object). 다섯 축 required, 분류 4값 enum, 조건부 `unresolved_reason` | JSON Schema 2020-12 |
| `schemas/publish-plan.schema.json` | `plan.json` 계약 (루트 object) | JSON Schema 2020-12 |
| `scripts/review_state.py` | 상태 머신, 에이전트 선택·category coverage, 위치 실측 검증, 라운드 판정, 실제 출처 sidecar와 익명 관측·critique synthesis view 분리·셔플, relation/분류 검증 | Python 3 표준 라이브러리 |
| `scripts/publish_findings.py` | `plan`/`apply`, GitHub 게시 이력 복원, finding_id·병합·다섯 결손 경로 lifecycle, 인덱스 생성, 3단계 게시 | Python 3 표준 라이브러리 |
| `tests/` | 결정적 단위 테스트와 픽스처 | unittest |

### 상태와 게시 이력 경계

로컬 `.claude/dual-review-state/<run_id>/`는 한 `run_id`의 재개와 3단계 게시 bookkeeping만 담당한다. 서로 다른 head SHA의 실행을 잇는 durable 경계는 GitHub다. `publish_findings.py plan`은 sticky 요약의 R7.19 인덱스를 기준 집합으로 읽고, inline comment의 `finding_id`와 REST review metadata를 연결하며, GraphQL thread 상태를 덧붙인다. 인덱스가 완전할 때만 다섯 결손 경로의 `src`·`path`·`cat` 판정을 수행하고, 완전하지 않으면 `resolved` 집합을 공집합으로 강제한다. 따라서 worktree나 로컬 상태가 사라져도 다음 실행의 판정 입력은 사라지지 않으며, 반대로 GitHub 이력이 불완전할 때 로컬 잔여 파일로 추측하지 않는다.

category 책임 매핑은 현재 실행의 Claude 일부 실패 coverage에만 쓰인다. `review_state.py`가 R3.10 상수와 선택·성공·실패 집합에서 `category_coverage`를 한 번 계산하고, `publish_findings.py`는 GitHub 인덱스에서 복원한 `cat`을 그 결과에 조회한다. R7.19 인덱스 형식에는 매핑이나 coverage를 추가하지 않으며 `cat` 일곱 값 계약도 바꾸지 않는다. 따라서 정적 책임표가 GitHub source of truth를 대체하지 않고, GitHub에서 복원한 과거 category와 현재 실행의 실제 coverage가 결합돼야만 결손이 성립한다.

출처 은닉 경계는 종합자 입력에만 있다. `review_state.py`는 상세 `finding_provenance`와 실제 group→alias `reviewer_aliases`를 비공개 상태에 유지하면서, 종합자에게는 alias별 `observations`·근거 있는 `critiques`·결정적 `relation`이 든 R6.5 view를 준다. 같은 ID 병합 전의 양쪽 주장과 반박은 view에 남지만 실제 reviewer 이름은 없다. 종합 뒤에는 `finding_id`로 상세 provenance를 재결합해 게시 인덱스의 `src`를 만든다. 즉 `reviewer-1/2`는 종합 전용이고 GitHub에 지속되지 않으며, 실제 `src`는 종합자에게 노출되지 않는다.

### 단계

```
INTAKE        대상 PR·base_sha·head_sha·변경 파일 고정, 규모 임계값 확인,
              gh/codex(gpt-5.6-terra) 프리플라이트, 상태 경로 무시 확인
   ↓
REVIEW        Claude 에이전트(매핑 선택) + Codex — 서로의 결과를 모름
   ↓
VALIDATE      스크립트가 스키마·파일·라인 실측 검증, diff 범위 판정,
              ID 병합 시 reviewer-group별 원 주장 보존
   ↓
CRITIQUE      상대 findings 반박 (기본 1회, 최대 2회)
              새 근거 0건 → 조기 종료 / 추상화 이탈 신호 → 사용자에게 종료 제안
   ↓
SYNTHESIS     실제 출처 → reviewer-1/2, observations+critiques → relation 계산
              결정적 셔플 → 5축 판정 → relation과 정합한 classification
   ↓
PLAN          GitHub marker/index/review/thread 복원 → 다섯 결손 경로 판정
              publish_findings.py plan → new/persisting/resolved/not_re_reviewed → plan.json
   ↓
[승인 게이트]  사용자에게 계획을 보이고 명시적 승인을 받는다
   ↓
APPLY         publish_findings.py apply — head SHA 재확인 후 3단계 게시, 멱등
```

리뷰어 하나가 실패해 남은 리뷰어가 하나뿐이 되면 REVIEW 단계에서 추가 승인 게이트가 발생한다(R3.7). 실패 유형은 프리플라이트 실패·`excluded`·산출물 없는 종료 셋이며 `excluded`도 포함된다. 양쪽이 모두 실패하면 승인을 묻지 않고 중단한다(R3.9). 규모 초과(R10.2)와 추상화 이탈(R5.4)에서도 사용자 결정을 기다리지만 그것은 진행 방식 선택이지 승인 게이트가 아니다. **승인 게이트는 단일 리뷰 승인(R3.7)과 게시 승인(R7.2) 둘이다.**

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
`quality-goal`의 `model-routing.md` route table은 `Codex light+standard → gpt-5.6-terra/high`, `Codex strict → gpt-5.6-sol/high`, `Bounded redesign only → gpt-5.6-sol/xhigh`로 **quality-goal 자신의 모드 등급**에 따라 구현 모델을 배정하며, "고위험 구현 실패 이후"라는 한정은 xhigh 행에만 붙는다. 이 문서가 `Mode: strict`인 것은 **이 스킬을 만드는 작업**의 등급이지 만들어진 스킬이 실행될 때의 등급이 아니므로, 그 표가 이 선택을 구속하지 않는다. terra를 고르는 독립 근거는 셋이다. (1) 이 스킬의 Codex 역할은 파일을 바꾸지 않는 읽기 전용 리뷰이고 산출물이 구조화 finding이라 sol의 추가 추론 예산이 값을 내기 어렵다. (2) 구조화 출력 제약(R3.8)이 실측된 모델이 `gpt-5.6-terra`이므로 그 제약이 검증된 조합을 그대로 쓴다. (3) 이 스킬은 매 PR마다 반복 실행되는 도구라 회당 비용이 누적된다. 모델을 임의로 대체하지 않고, 프리플라이트 실패는 단일 리뷰 승인 경로로 처리한다(R3.3).

**결정 A7 — 실행 간 게시 이력은 GitHub 자체에 지속한다.**
대안 (a) 각 worktree의 로컬 상태 파일: 구현은 단순하지만 worktree 제거와 head SHA 변경으로 다음 실행이 접근할 수 없다. (b) git notes: 저장소 안에 남지만 별도 fetch/push 규율과 ref 동기화를 요구하고 PR 코멘트의 실제 상태와 이중 source of truth가 된다. (c) GitHub의 inline 마커 + sticky 요약 인덱스: 게시물과 lifecycle 근거가 같은 시스템에 있고 다음 실행이 기존 읽기 API로 복원할 수 있다. (c)를 선택한다. 로컬 상태는 실행 내 재개만 담당하고, GitHub 복원이 불완전하면 로컬이나 git notes로 보완 추측하지 않고 `not_re_reviewed`로 안전하게 떨어진다(R2.5, R7.6a, R7.19).

**결정 A8 — 에이전트 category coverage는 중복 담당자의 합집합으로 계산한다.**
대안 (a) 실패 에이전트 하나라도 category를 담당하면 결손: 안전 측이지만 `correctness`를 함께 본 다른 선택 에이전트의 성공을 무시한다. (b) 선택된 담당자 중 하나라도 성공하면 covered, 성공자가 없고 실패자만 있을 때 uncovered: 실제 실행된 관점을 반영하고 비선택 에이전트를 실패로 오인하지 않는다. (c) `code-reviewer`가 일곱 category 전부를 담당: 전문 에이전트 실패가 항상 가려져 R3.9의 결손 경로가 무의미해진다. R3.10의 제한된 `code-reviewer` 범위와 (b)를 선택한다.

**결정 A9 — 종합자에게 source count만이 아니라 익명 관측과 critique를 함께 준다.**
대안 (a) 실제 출처 ID 유지: 합의 판정은 쉽지만 출처 편향 완화를 잃는다. (b) `source_count`만 유지: 한쪽 단독은 알 수 있으나 누가 무엇을 주장·지지·반박했는지와 근거가 사라진다. (c) run-local alias별 원 주장과 evidence-backed critique를 보존하고 relation을 스크립트가 계산: 정체는 숨기면서 `agreed`·`disputed`·`single_source`의 근거를 유지한다. (c)를 선택하고 실제 ID는 private sidecar와 R7.19 게시 인덱스 경로에만 둔다.

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

리뷰어 출력의 필드에 스크립트가 다음을 덧붙인 형태다: `finding_id`, `anchor_fingerprint`, `location_valid`, `in_diff_range`, `additional_locations`. 종합 단계 이전에는 실제 `source`(Codex 또는 Claude agent ID)와 상위 `reviewer_group`(`codex`/`claude`)도 갖는다. 병합 시 상세 출처는 상태의 `finding_provenance[finding_id]`에 정렬·중복 제거한 배열로 보존하고, 원 주장은 상위 group별 observation으로 보존한다. 종합 결과는 `finding_id`로 상세 sidecar와 재결합되어 R7.19 record의 `src`가 된다(R6.1). 실제 출처 필드는 R6.5 view에서 제거한다.

### 종합자 입력 (내부, `scripts/review_state.py` 산출)

루트는 `{"findings": [...]}`인 닫힌 object이고 `findings` 원소는 R6.5의 `finding_id`·`finding`·`source_count`·`observations`·`critiques`·`relation` 여섯 key만 갖는다. `finding`은 게시에 쓸 대표 source-free 객체이고, `observations`는 병합 전 reviewer-group별 모든 claim을 중첩 배열로 보존하며, `critiques`는 `target_finding_id`로 연결돼 evidence 검증을 통과한 입장이다. 실제 ID는 `reviewer-1`/`reviewer-2`로 치환되며 배열은 R6.5의 정렬 순서를 따른다. `relation`은 스크립트 산출 파생값이라 모델이 수정하지 않는다.

종합 출력의 각 finding은 입력 `finding_id`, 다섯 축, `classification`을 갖는다. `classification=unresolved`일 때만 `unresolved_reason={axis, explanation}`을 필수로 갖고 `axis`는 다섯 축 중 하나다. `review_state.py`는 입력 relation과 비-`unresolved` classification의 R6.3 대응을 검증한 뒤에만 상태의 `synthesis`로 기록한다. 이 입력 계약은 외부 API 스키마가 아니라 `references/synthesis-contract.md`, 스크립트 상수, `test_review_state.py`의 닫힌 key 단정으로 고정한다.

### 게시 계획 (`schemas/publish-plan.schema.json`)

`plan`이 산출하고 `apply`가 소비하는 계약이다. 루트 object, `additionalProperties: false`.

| 필드 | 타입 | 설명 |
|---|---|---|
| `repo`, `pr_number` | string, integer | 대상 고정값 |
| `base_sha`, `reviewed_sha` | string | 상태의 고정값. `reviewed_sha`가 요약 첫 줄에 인용된다 |
| `base_mismatch` | object \| null | `--base`가 PR 실제 base와 다를 때 `{requested_ref, actual_base_sha}`. null이 아니면 `inline_review.skip`이 참이어야 한다(R2.1a) |
| `summary_action` | object | `{kind: "create"|"update", comment_id: integer|null, body: string}` |
| `history_restore` | object | `{status, summary_comment_id, index_version, error}`. `status`는 `ok`/`missing`/`invalid`이고 `status != "ok"`이면 `lifecycle.resolved`는 비어 있어야 한다 |
| `inline_review` | object | `{skip: boolean, comments: [...]}`. `skip`이 참이면 2단계를 호출하지 않는다 |
| `thread_resolutions` | array | `[{thread_id, finding_id}]` |
| `summary_only_findings` | array | `location_valid=false` 또는 `in_diff_range=false`로 강등된 finding |
| `lifecycle` | object | `{new: [...], persisting: [...], resolved: [...], not_re_reviewed: [{finding_id, reason}]}`. `reason`은 R7.6a의 다섯 결손 경로 또는 `history_unavailable` 중 하나 |
| `skipped_threads` | array | `[{thread_id, reason}]` — R7.18로 건너뛴 스레드 |
| `coverage_gap_evidence` | array | `[{finding_id, reason, field, value}]`; `not_re_reviewed`의 결정적 판정 근거 |

`inline_review.comments` 원소의 구성은 실측으로 확정했다(R7.16). `{path, line, side, body, finding_id}`가 필수이고, finding이 여러 줄에 걸치면 `start_line`·`start_side`를 함께 싣는다. `summary_action.body`에는 R7.8 요약 마커와 R7.19 인덱스 블록이 정확히 하나씩 있어야 한다.

### 상태 파일

`.claude/dual-review-state/<run_id>/state.json`은 아래 필드를 갖는다. 이 목록은 상태 스키마의 닫힌 계약이며 구현과 픽스처가 같은 key 집합을 단정한다.

| 필드 | 내용 |
|---|---|
| `run_id`, `repo`, `pr_number` | 실행·대상 식별자 |
| `requested_base_ref`, `actual_base_sha`, `base_sha`, `base_mismatch` | 호출 인자와 PR 실제 base, diff base, R2.1a 판정 |
| `head_sha`, `changed_files`, `rounds` | 고정 리뷰 대상과 유효 교차비평 횟수 |
| `scope_reduction` | 검토 경로 집합과 제외 파일 수 |
| `selected_agents` | 선택 에이전트와 유발 신호·매치 수 |
| `agent_category_map` | 실행이 사용한 R3.10 `AGENT_CATEGORY_MAP_V1`의 exact object |
| `category_coverage` | 일곱 category별 `{selected_agents, successful_agents, failed_agents, covered}`; 배열은 정렬 |
| `reviewers` | 산출물 경로·재시도 횟수·실패 유형·`excluded` 사유 |
| `finding_provenance` | `finding_id`별 정렬·중복 제거한 reviewer ID 배열; 종합자에게는 비공개 |
| `reviewer_aliases` | 실제 상위 reviewer group→`reviewer-1`/`reviewer-2`; 종합자에게는 비공개 |
| `single_reviewer_approval` | R3.7 승인 여부와 기록 시각 |
| `critique_rounds`, `termination_reason` | 실제 group에 연결된 교차비평과 종료 결과; 종합자에게 직접 전달하지 않음 |
| `synthesis_input`, `synthesis` | R6.5의 익명 per-finding 입력과 relation 검증을 통과한 종합 결과 |
| `previous_review_comments` | R7.17의 REST comment 여섯 필드와 inline 마커 파싱 결과 |
| `previous_reviews` | review의 `id`·`commit_id`·`state`와 comment 연결 |
| `history_restore` | `{status, summary_comment_id, index_version, error, findings}`; `findings` 원소는 R7.19의 여덟 key |
| `coverage_gap_evidence` | `[{finding_id, reason, field, value}]`; R7.6a의 결손·복원 실패 근거 |
| `publish_stages` | 요약·inline review·thread resolve 세 단계 완료 기록과 각 쓰기 응답 ID |
| `published_findings`, `resolved_threads` | 같은 `run_id` 재개용 게시·해결 완료 집합 |
| `skipped_threads` | `[{thread_id, reason}]`; R7.18에서 resolve하지 않은 스레드와 사유 |

`history_restore.findings`는 다음 실행의 판정 입력을 **복사해 관측하기 위한 실행 내 캐시**일 뿐 source of truth가 아니다. 다음 head SHA 실행은 이전 로컬 디렉터리를 읽지 않고 GitHub에서 다시 복원한다.

### GitHub 엔드포인트 화이트리스트 (R7.14)

모든 항목이 `(kind, method, target)` 단일 표기다. 클라이언트가 기록하는 3튜플이 이 집합의 부분집합인지를 AC-14가 대조한다.

| 목적 | kind | method | target | 쓰기 |
|---|---|---|---|---|
| PR 메타·head SHA 조회 | `cli` | `EXEC` | `pr view` | 아니오 |
| 열린 PR 조회 | `cli` | `EXEC` | `pr list` | 아니오 |
| 기존 이슈 코멘트 조회 | `rest` | `GET` | `/repos/{o}/{r}/issues/{n}/comments` | 아니오 |
| 기존 리뷰 코멘트 조회 | `rest` | `GET` | `/repos/{o}/{r}/pulls/{n}/comments` | 아니오 |
| 기존 review 메타데이터 조회 | `rest` | `GET` | `/repos/{o}/{r}/pulls/{n}/reviews` | 아니오 |
| 리뷰 스레드 상태 조회 | `graphql` | `QUERY` | `reviewThreads` | 아니오 |
| 요약 코멘트 생성 | `rest` | `POST` | `/repos/{o}/{r}/issues/{n}/comments` | 예 |
| 요약 코멘트 갱신 | `rest` | `PATCH` | `/repos/{o}/{r}/issues/comments/{id}` | 예 |
| inline 리뷰 생성 | `rest` | `POST` | `/repos/{o}/{r}/pulls/{n}/reviews` (event=`COMMENT`) | 예 |
| 해소 스레드 정리 | `graphql` | `MUTATION` | `resolveReviewThread` | 예 |

GraphQL 계약은 인트로스펙션으로 실측했다. `ResolveReviewThreadInput`의 필수 입력은 `threadId`(`ID!`) 하나이고 `resolutionReason`(enum)과 `clientMutationId`는 선택이다. `PullRequestReviewThread`는 `id`·`isResolved`·`isOutdated`·`path`·`line`·`originalLine`·`comments`·`viewerCanResolve`를 노출하므로, 마커 파싱(`comments`의 body)·lifecycle 판정(`isResolved`)·해결 가능 여부 사전 확인(`viewerCanResolve`)에 필요한 것이 모두 갖춰져 있다. REST review 목록의 `id`·`commit_id`·`state`는 review comment의 `pull_request_review_id`와 연결한다. `apply`는 `viewerCanResolve`가 거짓인 스레드를 건너뛰고 그 사실을 상태의 `skipped_threads`와 요약 코멘트에 남긴다(R7.18).

목록 밖의 호출은 수행하지 않는다. 스레드 답글 엔드포인트는 의도적으로 제외했고, 해소 사실은 요약 코멘트에 기재한다(R7.7). `gh` CLI 경유 읽기 호출도 같은 3튜플로 기록되므로 화이트리스트 검사에서 빠지지 않는다.

### 데이터 흐름

```
git diff(base..head) ─┬─→ Claude 에이전트(선택 + category map) → reviewer-output(A) ─┐
                      └─→ codex exec(terra/high)              → reviewer-output(B) ─┤
                                                                                     ↓
                                                   review_state.py validate
                                  (스키마, 위치, diff 범위, group별 관측 보존 + ID 병합)
                                                                                     ↓
                                            findings(A)⇄findings(B) 교차비평 (0~2회)
                                                                                     ↓
                                               review_state.py split
                           ├─ private reviewer_aliases (상태 진단 전용)
                           ├─ private finding_provenance ── 종합 뒤 실제 `src` 재결합 ─┐
                           └─ public aliases+observations+critiques → relation → 종합자 ─┤
                                                        → 검증된 synthesis.json ─────────┤
                                           state.category_coverage ─────────────────────┤
 GitHub issue/review comments + reviews + threads → R7.19 history restore (`cat`) ─────┴─→ publish_findings.py plan
                                                                                           (다섯 결손 경로) → plan.json
                                                                            ↓
                                                [사용자 승인]
                                                                            ↓
                                publish_findings.py apply → GitHub (3단계)
```

## Failure behavior

| 실패 | 동작 |
|---|---|
| `gh` 미설치·미인증 | INTAKE에서 중단하고 인증 방법을 안내한다. 상태를 만들지 않는다. |
| detached HEAD 또는 현재 브랜치 PR 조회가 0건·2건(2건 이상) | 상태를 만들지 않고 중단하며 `--pr` 지정을 요구한다. 전역 열린 PR 목록에서 추측하지 않는다(R8.2). |
| 같은 `run_id` 재실행의 base 구성·`--rounds` 충돌 | `requested_base_ref`·해석된 `base_sha`·`actual_base_sha`·`rounds`를 대조하고, 상태를 읽어 진행하거나 덮어쓰지 않은 채 비정상 종료한다. 충돌 필드와 기존값·새 값을 출력하고 GitHub 쓰기는 0건이다(R2.5). |
| 입력 규모 임계값 초과 | 자동 진행하지 않고 중단 또는 범위 축소를 사용자에게 묻는다. 무언의 절단을 하지 않는다(R10). |
| Codex 프리플라이트 실패·모델 거부 | 모델을 임의로 대체하지 않는다. 사용자에게 알리고 단일 리뷰 승인 경로를 따른다(R3.3, R3.7). |
| Claude 에이전트 일부 실패 | R3.10의 고정 매핑과 선택·성공·실패 집합으로 category coverage를 계산한다. 실패자가 있으면서 성공 담당자가 없는 category만 uncovered로 기록하고 나머지로 진행한다. |
| agent-category map 또는 coverage 상태 불일치 | lifecycle 계획을 만들지 않고 비정상 종료한다. 여섯 번째 결손 reason을 만들거나 GitHub 이력의 값으로 보완하지 않으며 쓰기 호출은 0건이다(R3.10). |
| 리뷰어 출력 스키마 위반 | 검증 오류만 덧붙여 1회 재요청. 2회째 실패 시 해당 리뷰어를 `excluded`로 표시하고 사유를 남긴다(R3.5). |
| 두 리뷰어 모두 실패 | 게시하지 않고 중단한다. 단일 리뷰 승인을 묻지 않는다(R3.9). |
| 다섯 커버리지 결손 중 하나로 finding이 사라짐 | 복원한 `src`·`path`·`cat`과 현재 상태의 `category_coverage`로 `resolved`가 아니라 `not_re_reviewed`로 분류하고 스레드를 건드리지 않으며 상태·요약에 사유를 남긴다(R7.6a). |
| 종합자 입력에서 actual reviewer ID가 발견되거나 관측·critique·relation 계약이 맞지 않음 | 종합자를 호출하지 않고 SYNTHESIS 전에 중단한다. private sidecar를 입력으로 대체하지 않는다(R6.1, R6.5). |
| 종합 결과의 relation·classification 불일치 또는 근거 없는 `unresolved` | 종합 완료로 기록하거나 게시하지 않고 검증 오류를 표면화한다(R6.3). |
| 게시 인덱스 부재·손상·필드 결손·마커 불일치 | 부분 이력을 쓰지 않고 `history_restore.status != "ok"`로 기록한다. `resolved`와 resolve 호출은 0건이며 식별 가능한 이전 finding은 `history_unavailable`로 보존한다(R7.6a, R7.19). |
| `viewerCanResolve`가 거짓인 스레드 | resolve 호출을 하지 않고 건너뛰며 스레드 ID와 사유를 상태·요약에 남긴다(R7.18). |
| 위치 검증 실패 | 해당 finding을 inline에서 제외하고 요약에 "위치 미검증"으로 남긴다. 리뷰 전체를 실패시키지 않는다. |
| 교차비평 무진전 | 다음 라운드를 실행하지 않고 종료 사유 `no_new_evidence`를 기록한다. |
| 추상화 이탈 신호 | 라운드를 중단하고 사용자에게 종료를 제안한다. 자동으로 계속하지 않는다. |
| `apply` 직전 head SHA 불일치 | 아무것도 게시하지 않고 비정상 종료한다. 새 SHA로 리뷰를 다시 시작해야 한다. |
| 게시 1단계 실패 | 2·3단계를 실행하지 않고 비정상 종료한다. 재실행 시 1단계부터 다시 시도한다. |
| 게시 2단계 실패 | 원자적 호출이므로 부분 게시가 없다. 3단계를 실행하지 않고 비정상 종료한다. 재실행 시 1단계는 건너뛰고 2단계를 마커 대조 후 재시도한다(R7.13). |
| 게시 3단계 일부 실패 | 성공한 스레드 ID를 기록하고 비정상 종료한다. 재실행 시 미해결 스레드만 처리한다. |
| `--base`가 PR 실제 base와 다름 | inline 게시를 전면 금지하고 모든 finding을 요약으로 강등한다. 두 ref를 상태·리포트·게시 요약에 명시한다(R2.1a). |
| 목록 조회 페이지 순회 중 실패 | 부분 목록을 반환하지 않고 오류를 올린다. 불완전한 목록으로 세운 계획은 재게시와 `resolved` 오분류를 낳는다(R8.2). |
| 상태 디렉터리가 git에 무시되지 않음 | 경고를 출력하고 계속 진행한다. `.gitignore`를 임의 수정하지 않는다. |

## Security and risk

**신뢰 경계.** 리뷰어(LLM) 출력은 미신뢰 데이터다. 스키마 검증과 파일·라인 실측 검증(R4)을 통과한 것만 inline으로 게시한다. 리뷰 대상 diff에 프롬프트 인젝션 문구가 있어도, 스킬은 그것으로 게시 정책·승인 게이트·엔드포인트 화이트리스트·모델 선택을 바꾸지 않는다.

**게시 텍스트의 전파.** 게시 본문은 리뷰어가 생성한 텍스트와 diff 인용을 포함한다. 인용 대상은 이미 해당 PR에 존재하는 코드이므로 새로운 노출은 아니다. 저장소 밖 경로 인용은 위치 검증에서 걸러진다.

**게시 이력 파싱.** GitHub 코멘트와 review 응답은 전송 채널만 신뢰하고 내용은 미신뢰 데이터로 취급한다. R7.19 파서는 HTML 주석 안 payload를 명령으로 실행하거나 프롬프트로 넘기지 않고, 지원 version·표준 base64·닫힌 JSON key 집합·타입·허용값·inline ID 대조만 수행한다. 하나라도 실패하면 부분 데이터로 resolve하지 않는 것이 안전 경계다. 현재 실행의 agent-category 책임표는 R3.10의 로컬 상수에서만 만들고 GitHub payload가 매핑을 덮어쓰게 하지 않는다.

**종합 입력 경계.** 실제 reviewer ID는 private `finding_provenance`·`reviewer_aliases`에만 있고 종합자 payload에는 전달하지 않는다. 반대로 `source_count`만 남겨 분류 근거를 잃지 않도록 alias별 원 주장과 evidence 검증을 통과한 critique를 전달한다. payload의 닫힌 key·alias 값·relation을 호출 전에 검증하고, 출력 relation과 classification의 정합성을 호출 뒤 다시 검증한다.

**자격 증명.** 스크립트는 토큰을 읽거나 저장하거나 출력하지 않고 `gh` CLI 인증에 위임한다(R8.4). 상태 파일·로그·게시물에 토큰이 들어가지 않으며, 소스에 토큰 환경변수명이 등장하지 않는 것을 AC-31로 고정한다.

**권한 범위.** 활성 토큰 스코프는 `gist, project, read:org, repo, user, workflow`다. `repo`는 게시에 필요한 최소보다 넓지만 축소는 사용자 계정 설정의 영역이며 이 작업의 범위 밖이다. 대신 엔드포인트 화이트리스트(R7.14)와 그 준수를 강제하는 AC-14로 실제 행사 범위를 좁힌다.

**대상 오지정.** 잘못된 저장소·PR에 게시하는 것이 가장 비싼 실패다. 저장소와 PR 번호를 INTAKE에서 상태에 고정하고, `apply`가 상태의 값만 사용하며 실행 직전 head SHA까지 재확인한다(R7.11).

**리스크와 완화.**

| 리스크 | 완화 |
|---|---|
| 중복·스팸 댓글로 PR 오염 | `finding_id` 마커 dedup, sticky summary, `persisting` 재게시 없음, 단계 완료 기록 |
| stale SHA 기준 리뷰 게시 | SHA 고정 + 게시 직전 재확인, 요약 첫 줄에 SHA 명시 |
| false positive 게시 | 교차비평 + 5축 판정 + 위치 실측, 근거 없는 finding은 `unresolved`로 강등 |
| 종합자 자기선호 편향 또는 분류 근거 소실 | actual 출처는 private sidecar로 분리하고 익명 observations·critiques·relation은 보존, relation/classification 검증, blocking verdict 없음, 잔존 한계 명시 |
| 에이전트 일부 실패를 구현별 category 추측으로 누락 | versioned `AGENT_CATEGORY_MAP_V1`, 중복 담당 집합식, 상태 coverage와 문서/상수 대조 테스트 |
| 리뷰가 merge를 차단 | verdict를 `COMMENT`로 고정, 발행 경로 부재를 테스트로 고정 |
| 승인 없는 게시 | `apply` 분리, 자동 호출 경로 부재를 AST 검사로 고정 |
| 대형 diff의 조용한 커버리지 결손 | 임계값 초과 시 사용자 결정 요구, 축소 범위를 상태·리포트·게시에 명시 |
| 이전 게시 인덱스 손상·형식 오염으로 미해소 스레드 resolve | 엄격한 marker/index 검증, 복원 실패 시 `resolved` 0건·`history_unavailable` 기본값 |
| 같은 대상 재개의 다른 `--base`·`--rounds` 묵살 | 상태 고정값 대조 후 충돌 시 변경·쓰기 전 중단 |

## Test strategy

결정적 테스트는 `dot_claude/skills/dual-review/tests/`에 두고 `quality-goal` 선례와 같은 방식으로 실행한다.

### 판정 명령

Acceptance criteria의 `[실행]`은 아래 명령 중 대응 행을 뜻한다. 단위 테스트 AC는 해당 파일 안에 AC 번호를 이름 또는 주석으로 남겨 매핑을 기계적으로 검사할 수 있게 한다.

| 판정 ID | 담당 AC | 저장소 루트에서 실행할 명령 |
|---|---|---|
| PUB | AC-1~3, AC-6~16, AC-23, AC-25, AC-39, AC-46~47, AC-49, AC-51~52, AC-54~55, AC-57~58, AC-61~62, AC-64~68 | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_publish_findings.py'` |
| STATE | AC-4~6, AC-17~25, AC-41, AC-45, AC-50, AC-53, AC-56, AC-59~63, AC-69~70 | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_review_state.py'` |
| CONTRACT | AC-13, AC-26, AC-28~33, AC-38, AC-40~45, AC-48, AC-60, AC-69 | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_content_contracts.py'` |
| ALL | AC-34 | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'` |
| CODEX | AC-27 | 아래 "스크립트 밖 검증"의 실제 `codex exec` 명령 |
| CHEZMOI | AC-35 | `chezmoi --source "$PWD" target-path dot_claude/skills/dual-review/SKILL.md` |
| IGNORE | AC-36 | `git check-ignore -v .claude/dual-review-state/` |
| GH-READ | AC-37 | 아래 "스크립트 밖 검증"의 실제 PR에 대한 읽기 전용 `plan` 명령 |

- `test_publish_findings.py` — PUB 행의 AC. GitHub 접근은 호출 기록을 남기는 fake 클라이언트로 대체하고, 열 메서드 화이트리스트 대조·현재 브랜치 `head_ref` 호출·marker/index 왕복·review 연결·R3.10에서 계산한 실제 category coverage를 쓰는 다섯 결손 경로·복원 실패 기본값·verdict 고정·쓰기 호출 0건·페이지 순회 완전성을 그 기록으로 판정한다.
- `test_review_state.py` — STATE 행의 AC. 임시 git 저장소 픽스처로 파일·라인·diff 범위를 실측하고, `AGENT_CATEGORY_MAP_V1`의 선택/성공/실패 집합 계산, 병합 전 group별 관측 보존, alias 변환, critique 연결, relation 산출, relation/classification 검증을 raw 입력부터 실행한다.
- `test_content_contracts.py` — CONTRACT 행의 AC. 네 스키마의 루트 형태와 필드 요건(critique의 target·stance·evidence, synthesis의 다섯 축·네 분류 enum·`unresolved_reason`, publish-plan의 `history_restore`·`coverage_gap_evidence`·`skipped_threads`), `AGENT_CATEGORY_MAP_V1`의 reviewer-contract/스크립트 일치, R6.5 synthesis-input 닫힌 key, `SKILL.md` frontmatter·`version` 형식·플래그·프리플라이트·두 게이트 문구와 참조 경로, 금지 플래그 부재, 구조화 출력 금지 구성(`uniqueItems`·lookaround) 부재, 표준 라이브러리 import, 토큰 문자열 부재, 디렉터리 구성, 유지보수 문서 절 구성, 종합자 계약의 한계 명시를 확인한다.

스크립트 밖 검증:

- **AC-27** — `DUAL_REVIEW_AC27_DIR=$(mktemp -d)`로 임시 디렉터리를 만든 뒤 최소 프롬프트로 `codex exec --sandbox read-only --ephemeral --model gpt-5.6-terra -c model_reasoning_effort="high" --output-schema "$PWD/dot_claude/skills/dual-review/schemas/reviewer-output.schema.json" --output-last-message "$DUAL_REVIEW_AC27_DIR/result.json" --json 'Return a valid empty review result for schema acceptance testing.'`을 1회 실행한다. 종료 코드 0이고 `result.json`이 같은 스키마를 만족해야 한다.
- **AC-34** — 판정 명령 ALL.
- **AC-35** — 판정 명령 CHEZMOI가 종료 코드 0이고 출력이 `~/.claude/skills/dual-review/SKILL.md`의 절대 경로다. 이 워크트리를 source로 명시해 main checkout을 보는 `chezmoi source-path`의 영향을 제거한다.
- **AC-36** — `git check-ignore -v .claude/dual-review-state/`.
- **AC-37** — `gh pr list --state open --limit 1 --json number`로 얻은 PR 번호를 명시해 `publish_findings.py plan`을 빈 finding 집합으로 실행한다. 종료 코드 0, 유효 `plan.json`, 기록된 쓰기 3튜플 0건을 확인한다. 열린 PR이 없으면 `not applicable`로 기록한다.

이 저장소에는 타입 체크·린트·빌드 설정이 없다. 해당 검증 범주는 "not configured"로 기록하며, 근거는 저장소 루트에 `package.json`·`pyproject.toml`·`Makefile`·CI 워크플로가 없다는 사실이다.

## 개정 조합 검토

이 실행의 라운드 1 지적 12건, 라운드 2의 SPEC-09·13~16, 확정 설계, readiness attempt 1의 READY-01·02를 함께 반영하면서 각각의 수정이 조합될 때 새 결손을 만드는지 다시 점검했다. 선행 Plan의 PLAN-009·010·012처럼 개별 수정은 맞았지만 조합에서 회귀한 사례가 있었으므로, 이번에는 같은 사건 집합·상태 필드·API 메서드·익명화 경계·AC를 양방향으로 대조했다.

| 겹치는 지점 | 관련 finding | 점검 결과 |
|---|---|---|
| R3.7의 실패 셋 ↔ R7.6a의 결손 다섯 ↔ AC-10·62·68 | SPEC-09 | R3.7(a)·(b)·(c)를 모두 결손 표에 넣고 범위 축소·Claude 에이전트 일부 실패를 더해 정확히 다섯으로 맞췄다. AC-10은 다섯 사건이 모두 없는 보집합만 `resolved`로, AC-62·68은 각 사건을 복원된 인덱스 입력부터 `not_re_reviewed`로 판정한다 |
| R3.10 책임표 ↔ R3.9 일부 실패 ↔ R7.6a `agent_category_uncovered` | READY-01 | 다섯 agent와 일곱 category를 완전히 매핑하고 `correctness` 중복 담당을 명시했다. 현재 실행에서 선택된 담당자 중 성공자가 하나라도 있으면 covered, 실패자만 남으면 uncovered라는 한 집합식을 상태와 lifecycle이 공유한다. 각 agent의 고유 category 실패와 `correctness` 일부 성공/전원 실패를 AC-60·62·68이 서로 다른 층에서 판정한다 |
| R3.10 현재 coverage ↔ R7.19 과거 `cat` | READY-01, SPEC-13 | GitHub 인덱스는 기존 여덟 key와 일곱 category enum을 유지한다. `publish_findings.py`가 과거 `cat`을 현재 상태의 `category_coverage`에 조회하므로 정적 매핑을 GitHub 이력에 중복 저장하거나 `src`에서 추측하지 않는다 |
| R6.1 실제 출처 은닉 ↔ R6.5 익명 판정 정보 ↔ R7.19 `src` 지속 | READY-02, SPEC-13 | 종합자 view에는 alias별 observations·critiques·relation을 남기고 실제 ID는 두 private sidecar에만 둔다. 종합 뒤 `finding_id`로 `finding_provenance`를 재결합하므로 분류 정보와 다음 실행의 실제 `src`를 둘 다 잃지 않고, alias는 GitHub에 게시하지 않는다(AC-23·69·70) |
| R7.5 ID 병합 ↔ R6.5 per-finding 입력 | READY-02 | 대표 finding 하나를 고르더라도 상위 reviewer group별 원 주장과 target ID로 연결된 critique는 별도 배열에 보존한다. `source_count`만 남기는 축약을 금지해 양측 합의·한쪽 단독·상호 반박이 각각 `bilateral`·`unilateral`·`contested`로 남는다 |
| R5.2 critique schema ↔ R6.5 relation ↔ R6.3 classification | READY-02 | `target_finding_id`·`stance`·non-empty evidence가 모두 유효한 critique만 relation에 들어간다. relation의 비-미결 분류를 1:1로 검증하고 `unresolved`에는 축별 사유를 요구해 enum만 맞춘 임의 분류를 막는다(AC-41·43·50·70) |
| R7.9 inline marker ↔ R7.19 summary index ↔ R7.17 복원 | SPEC-13 | inline은 기존 ID marker를 유지하고 요약 인덱스가 `cat`·`src`·`path`·`line`·`fp`·`run`·`lifecycle`을 보충한다. inline이 없는 요약 전용 finding도 AC-67로 왕복하고, 복원 실패는 AC-62·65에서 `resolved` 0건으로 닫는다 |
| R2.5 로컬 재개 ↔ R7.19 실행 간 이력 | SPEC-13, SPEC-14 | 로컬은 같은 `run_id` bookkeeping만, GitHub는 head SHA를 넘는 이력만 담당하도록 경계를 분리했다. 같은 `run_id`의 플래그 충돌은 중단하고, 다른 `run_id`의 lifecycle은 GitHub에서 복원하므로 서로 대체하거나 덮어쓰지 않는다 |
| R2.1a `--base` ↔ R2.5 재실행 ↔ AC-54·61 | SPEC-14 | 최초 실행의 base 불일치 강등(AC-54)과 재개 시 고정 인자 충돌 중단(AC-61)을 별도 분기로 고정했다. `--rounds`도 같은 충돌 규칙을 쓴다 |
| R1.4 현재 브랜치 ↔ R8.2 인터페이스 ↔ AC-55 | SPEC-15 | `list_open_prs(repo, head_ref, limit)`의 서버 측 branch 필터를 명시하고 0·1·2건 분기를 고정했다. `get_pr_meta`는 정확히 한 PR 번호가 나온 뒤만 호출한다 |
| R7.6a·R7.17·R7.18 ↔ 상태·plan 스키마 | SPEC-16 | `history_restore`, `coverage_gap_evidence`, `previous_reviews`, `skipped_threads`를 상태 목록에 명시하고 plan에도 복원 상태·결손 근거를 추가했다. 필드 이름과 원소 shape가 요구사항·Interfaces에서 같다 |
| R7.19 읽기 집합 ↔ R7.14 화이트리스트 ↔ R8.2·AC-49 | SPEC-13, SPEC-15 | `/pulls/{n}/reviews` 읽기를 열 번째 메서드·화이트리스트에 함께 추가하고, 게시 이력 네 목록 모두의 pagination과 부분 결과 금지를 AC-49가 판정한다. 쓰기 메서드는 네 개로 그대로다 |
| R7.16 ↔ D18 | SPEC-10 잔여 | D18의 실측 결론은 응답 필드 구성으로 끝내고, cross-hunk 축소는 R7.16이 정한 별도 보수적 정책이라고 다시 분리했다 |
| 요구사항 ↔ AC ↔ Test strategy | 추적 완전성 | 요구사항 63건 전수 등재(누락 0·유령 0), AC 총 70건 중 메타 기준 AC-27·34를 뺀 68건이 추적표에 등장하고, 70건 전부가 판정 명령에 배정되도록 맞췄다. AC 정의 자체도 AC-1부터 AC-70까지 단조 증가하도록 재배치했다 |

조합 결과, 다섯 결손 경로의 개수와 R7.19 v1 인덱스 여덟 key는 바뀌지 않았다. 그중 에이전트 일부 실패 경로만 현재 실행의 고정 category coverage를 추가 입력으로 받아 임의 매핑을 제거했고, coverage가 없거나 GitHub 복원이 실패한 경우는 여전히 자동 resolve로 합류하지 않는다. 종합자용 alias는 실제 `src`를 덮어쓰지 않고, 반대로 상세 provenance는 종합자에게 노출되지 않는다. ID 병합 뒤에도 분류 근거가 남으며, 재실행 충돌 중단·API 화이트리스트·쓰기 surface 네 메서드는 이번 변경의 영향을 받지 않는다.

## Decisions

- D1. 스킬 이름은 `dual-review`, 배치는 `dot_claude/skills/dual-review/`. 이슈 #42가 지정한 `dot_claude/skills/`를 따른다.
- D2. 멱등성은 결정적 스크립트로 구현한다(결정 A1, 사용자 확인).
- D3. 게시 주체는 사용자 본인 계정이고 요약 첫 줄에 AI 생성 사실과 리뷰 대상 SHA를 표시한다(사용자 확인). 별도 bot 계정은 비목표다.
- D4. SARIF export는 1차 범위에서 제외하고 후속 이슈로 이관한다(사용자 확인). 내부 정규화 finding에는 후속 매핑에 필요한 `finding_id`·`evidence`·분류 필드를 유지한다.
- D5. 교차비평은 기본 1회, 최대 2회. 이슈 조사가 확정한 "회차 증가가 항상 이득은 아니다"(Nature s41598-026-42705-7)와 비대칭 결과(arXiv 2607.21656)를 근거로 한다.
- D6. verdict는 항상 `COMMENT`. Copilot·Claude Code Review·Rust LLM 정책의 비차단 관례를 따른다.
- D7. `pr-review-toolkit` 에이전트에는 구조화 출력 계약을 호출 측 프롬프트로 주입한다. 플러그인 파일은 수정하지 않는다(N8).
- D8. 이슈 #29에 코드 의존하지 않는다. #29가 OPEN·미구현임을 저장소 실측으로 확인했다. 이식하는 것은 원칙(2라운드 연속 조용, 실측 근거 요구, 추상화 이탈 감지)뿐이다.
- D9. Codex 호출은 `model-routing.md`의 안전 플래그 집합을 쓰되, 리뷰는 읽기 전용이므로 `--sandbox read-only`를 쓰고 모델은 `gpt-5.6-terra`, effort는 `high`로 고정한다. `model-routing.md`의 route table은 quality-goal 자신의 모드 등급에 따른 **구현** 모델 배정이므로 이 선택을 구속하지 않는다. 근거는 결정 A6의 세 항목이다.
- D10. 리뷰어 출력 스키마의 루트는 object다. codex 1.0.5의 `review-output.schema.json`과 `quality-goal`의 `codex-result.schema.json`이 모두 루트 object이며, 구조화 출력 계약이 루트 배열을 수락한다는 근거가 없다. 파생 필드는 스키마 밖 내부 표현에만 붙인다.
- D11. inline 게시는 단일 원자적 리뷰 호출이다(결정 A4). 부분 게시 상태가 존재하지 않으므로 멱등성은 단계 완료 기록과 마커 대조로 확보한다.
- D12. `resolved` finding은 스레드 답글 대신 요약 기재 + `resolveReviewThread`로 처리한다. 화이트리스트를 넓히지 않기 위한 결정이며, 부수 효과로 스레드 스팸도 줄인다.
- D13. `templates/`와 `evals/`를 두지 않는다(N10, N11).

- D14. `codex exec --output-schema`가 거부하는 구성을 스키마에서 배제한다(R3.8). `uniqueItems`와 정규식 lookaround가 HTTP 400으로 거절되는 것은 `docs/development/2026-08-25-quality-goal/deviations.md` **D-15**의 실측 결과이고, 실측 모델이 이 스킬이 쓸 `gpt-5.6-terra`와 같아 그대로 적용된다. 제약 대상은 API로 전송되는 스키마뿐이며, 같은 편차가 로컬 전용 스키마(`review.schema.json`)에서는 `uniqueItems`가 유효하다고 명시한다. AC-44는 그래서 `reviewer-output.schema.json`만 대상으로 한다.
- D15. GitHub 접근 표기를 `(kind, method, target)` 3튜플로 통일하고 클라이언트 인터페이스를 열 메서드로 못박는다(R7.14, R8.2). 기존 아홉 메서드에 R7.19의 review 연결을 위한 read-only `list_reviews`만 더했다. `gh` CLI·REST·GraphQL이 한 검사 체계 안에 들어와야 AC-14가 실제로 화이트리스트를 강제할 수 있다.

- D16. `pr-review-toolkit` 에이전트의 자체 `Output Format` 절과 이 스킬의 스키마 계약이 충돌한다. 플러그인을 수정하지 않기로 했으므로(N8) 호출 프롬프트가 우선순위를 명시적으로 선언하는 방식으로 해소한다(R3.6, AC-45). 대안이던 "플러그인 포크 후 출력 절 교체"는 외부 의존을 유지한다는 이슈 #42의 배치 결정과 어긋나 채택하지 않았다.
- D17. `code-reviewer` 에이전트만 frontmatter에 `model: opus`가 고정돼 있고 나머지 넷은 `model: inherit`이다(설치본 실측). 이 스킬은 그 설정을 바꾸지 않으므로, `code-reviewer`가 항상 선택되는 R3.1 매핑상 매 실행에 Opus 호출이 최소 1회 포함된다. 비용 상한을 별도로 두지 않고 실행 비용 산정의 전제로만 기록한다.

- D18. inline 코멘트의 **필드 구성**은 실측으로 확정했다. `zambaguni/zambaguni-front`의 PR #1255·#1211·#1313에서 리뷰 코멘트 79건의 응답 키 집합을 조회해(본문·코드 내용은 취득하지 않고 키 이름만) 세 PR 모두 동일한 구성임을 확인했다: `path`, `line`, `side`, `start_line`, `start_side`, `body`, `commit_id`, `id`, `node_id`, `pull_request_review_id`, `original_line`, `original_start_line`, `subject_type`, `diff_hunk`, 그리고 deprecated인 `position`·`original_position`. 이 실측은 R7.16의 요청 필드와 R7.17의 기록 필드를 뒷받침한다. **여기서 cross-hunk 제약이나 축소 규칙은 도출하지 않는다.** hunk 경계를 넘을 때 단일 라인으로 축소하는 동작은 R7.16 본문에 근거를 둔 별도의 보수적 정책이다.

- D19. 종합 분류에 네 번째 값 `single_source`를 둔다. 리뷰어가 하나뿐인 실행뿐 아니라 두 리뷰어 실행에서 한쪽만 finding을 제기하고 상대가 지지·반박하지 않은 경우에도 `agreed`(합의)나 `disputed`(불일치)는 성립하지 않는다. 이를 모두 `unresolved`로 강등하면 "근거가 부족하다"와 "한 출처만 주장했다"가 구별되지 않으므로 후자를 finding-level `single_source`로 보존한다. R6.5의 `unilateral`이 그 판정 근거이고, 근거 자체가 부족할 때만 축별 사유가 있는 `unresolved`를 쓴다(R6.3, AC-50, AC-70).
- D20. 게시 이력 네 목록 조회는 전체 페이지를 순회한다(R8.2). 게시 멱등성과 GitHub 이력 복원이 inline marker·summary index·review·thread의 완전 조회에 의존하는데 GitHub 목록 응답은 기본이 부분 페이지다. 순회 실패 시 부분 목록을 반환하지 않고 오류를 올리는 쪽을 택했다 — 불완전한 목록으로 세운 계획은 조용한 재게시와 `resolved` 오분류를 낳고, 그것이 실패를 드러내는 것보다 나쁘다. 이 결함은 단일 페이지 fake로는 구조적으로 검출되지 않으므로 AC-49가 네 메서드 각각의 다중 페이지 fake를 요구한다.

- D21. `resolved`와 `not_re_reviewed`를 분리한다(R7.6a). 대안은 `resolved` 하나로 두고 요약에 주의 문구만 남기는 것이었으나, 그러면 `resolveReviewThread`가 여전히 호출되어 미해소 지적의 스레드가 닫힌다. 스레드 해결은 되돌리려면 사람이 GitHub에서 직접 열어야 하는 외부 쓰기이므로, 분류 자체를 나눠 호출을 막는 쪽을 택했다. 커버리지 결손 다섯 경로(R3.7(a) 프리플라이트 실패·모델 거부, R3.7(b) `excluded`, R3.7(c) 산출물 없는 종료, R10.2(b) 범위 축소, R3.9의 에이전트 일부 실패)는 R7.19에서 복원한 `src`·`path`·`cat`으로 판정한다. 마지막 경로의 `cat` 책임은 R3.10의 versioned 상수와 현재 실행의 category coverage로만 계산한다. GitHub 복원이 불완전하면 `resolved`를 0건으로 만들고, 책임표/현재 상태 자체가 불일치하면 lifecycle 계산 전에 중단하는 것이 각각의 결정적 기본값이다.
- D22. 리뷰어 "실패"를 세 유형으로 열거하고 `excluded`를 포함시킨다(R3.7). 대안은 `excluded`를 게이트 밖에 두는 것이었으나, R6.3이 두 경로를 같은 단일 리뷰어 상태로 묶는 이상 한쪽만 승인을 요구하면 같은 상태에 두 규칙이 적용된다. 이중 리뷰가 이 스킬의 존재 이유(G1)이므로 단일 리뷰어로 끝나는 모든 경로에 같은 게이트를 건다.
- D23. `run_id`를 `<owner>-<repo>-pr<n>-<head 12자>`로 결정적으로 만들고 별도 재개 플래그를 두지 않는다(R2.5). 대안은 타임스탬프 기반 ID와 `--resume` 플래그였으나, 그러면 재실행이 직전 상태를 찾으려고 디렉터리를 뒤져야 하고 어느 것을 이어갈지가 모호해진다. head SHA를 ID에 넣으면 같은 대상의 완료 기록을 찾을 수 있다. 단, `run_id`에 없는 `requested_base_ref`·해석된 `base_sha`·`actual_base_sha`·`rounds`는 상태 고정값과 대조하고 충돌 시 중단해 낡은 구성을 조용히 재사용하지 않는다(AC-61).
- D24. head SHA를 넘는 게시 이력의 유일한 source of truth는 GitHub다(R7.19, 결정 A7). 로컬 파일은 worktree 제거에 취약하고 git notes는 별도 동기화와 이중 진실을 만들므로 채택하지 않았다. inline marker는 ID dedup을, sticky 요약의 표준-base64 인덱스는 `cat`·`src`·`path`·`line`·`fp`·`run`·`lifecycle` 복원을 맡는다. `src`는 단일 문자열 대신 정렬된 배열로 두어 같은 `finding_id`로 병합된 복수 reviewer 출처를 잃지 않는다.
- D25. `AGENT_CATEGORY_MAP_V1`은 selection 표와 분리된 coverage 책임표다(R3.10, A8). `code-reviewer`를 모든 category의 catch-all로 두면 전문 에이전트 실패가 가려지고, 중복 담당자 전원 성공을 요구하면 실제로 성공한 관점도 무시한다. `code-reviewer`는 correctness/security/performance, 전문 에이전트는 자신의 도메인을 맡되 silent-failure와 type은 correctness를 중복 담당하며, 선택된 담당자 중 하나라도 성공하면 covered로 정했다. 이 표는 finding category 허용 목록이 아니므로 전문 에이전트가 다른 category의 유효 finding을 내는 것을 버리지 않는다.
- D26. 같은 `finding_id` 병합 뒤의 종합자 입력은 실제 출처 제거와 분류 근거 보존을 동시에 만족해야 한다(R6.5, A9). 실제 ID를 유지하는 안은 편향 완화를 깨고, count만 남기는 안은 반박 방향·근거를 잃는다. 그래서 상위 두 reviewer group을 run-local alias로 바꾸고 group별 observations와 evidence-backed critiques를 보존하며 relation을 스크립트가 계산한다. alias 대응은 private state에, 실제 세부 provenance는 R7.19 재결합 경로에만 남긴다.

미해결 결정 없음.

<!-- strict-only:start -->

### Threat and trust boundaries

| 행위자 | 신뢰 | 경계 |
|---|---|---|
| 사용자 | 신뢰 | 스킬을 호출하고 두 게이트를 승인한다 |
| 저장소 코드·diff | 미신뢰 데이터 | 리뷰 입력. 인젝션 문구가 있어도 정책을 바꾸지 못한다 |
| Claude 리뷰 에이전트 출력 | 미신뢰 | 스키마 + 위치 실측 검증 통과 후에만 게시 |
| Codex 출력 | 미신뢰 | 스키마 + 위치 실측 검증 후에만 게시 |
| GitHub API 응답 | 신뢰(전송) / 미신뢰(내용) | 기존 코멘트 본문은 versioned marker/index의 닫힌 데이터 계약으로만 파싱하고 지시로 해석하지 않는다. 불완전하면 resolve를 금지한다 |
| `gh` 인증 토큰 | 신뢰, 미노출 | 스크립트가 직접 다루지 않는다(AC-31) |

통제와 그 검증: 엔드포인트 화이트리스트(AC-14), 승인 게이트(AC-15, AC-20, AC-28), 위치 실측(AC-4, AC-5), 에이전트-category 상수와 coverage 집합식(AC-60, AC-62, AC-68), 익명 종합 입력과 relation 검증(AC-23, AC-50, AC-69, AC-70), 게시 이력 strict parse와 fail-safe(AC-64~68), verdict 고정(AC-13), 금지 플래그 부재(AC-29), 샌드박스 read-only와 나머지 호출 플래그 존재(AC-48), 토큰 미취급(AC-31).

### Authorization and tenant isolation

멀티테넌시가 없는 단일 사용자 CLI 도구이므로 테넌트 격리는 해당 없다. 대응하는 격리 개념은 **대상 격리**다: 저장소와 PR 번호를 INTAKE에서 고정하고 `apply`가 상태의 값만 사용해, 다른 저장소·다른 PR에 게시되는 경로를 없앤다. 검증은 AC-11(SHA 재확인)과 AC-14(화이트리스트 대조)가 담당한다. 권한은 사용자의 기존 `gh` 토큰 권한을 넘지 않으며, 스킬이 권한을 상승시키거나 새 자격 증명을 만들지 않는다.

### Migration, compatibility, and rollback

신규 스킬이므로 자동 데이터 마이그레이션·백필은 없다. R7.19 이전 형식처럼 요약 인덱스가 없는 게시물은 `history_unavailable`로 보이고 자동 resolve되지 않는다. 이후 새로 게시하거나 다시 발견한 finding은 v1 인덱스로 완전 복원되지만, 메타데이터가 끝내 알려지지 않는 legacy inline marker는 ID 경고로 남아 자동 resolve 대상이 되지 않는다. 지원하지 않는 미래 index version도 추측해 읽지 않고 같은 안전 경로를 따른다. 호환성 대상은 네 외부 계약이다: `pr-review-toolkit` 에이전트 이름 6종, `codex exec` 플래그(`--output-schema`, `--ephemeral`, `--output-last-message`, `--json`, `--sandbox`, `--model`)와 모델 식별자 `gpt-5.6-terra`, GitHub REST/GraphQL 필드, `dual-review:index v1` 데이터 계약. 넷 다 `docs/dual-review-maintenance.md`의 점검 대상으로 기록한다. 내부 계약인 `AGENT_CATEGORY_MAP_V1`이나 R6.5 synthesis-input shape가 바뀌면 스킬 MINOR 이상을 올리고 문서·상수·픽스처를 같은 변경에서 갱신한다. 이 내부 변경은 기존 GitHub v1 인덱스의 `cat`·`src` shape를 바꾸지 않는다.

롤백 트리거와 절차:

| 트리거 | 절차 |
|---|---|
| 스킬 자체를 되돌림 | 커밋 되돌리기 후 `chezmoi apply`. 런타임 상태는 무시 경로라 필요하면 사용자가 삭제할 수 있다. 이미 게시된 v1 인덱스는 GitHub에 남지만 이전 버전이 해석하지 않는 inert HTML 주석이며 자동 삭제하지 않는다 |
| 잘못 게시된 코멘트 | **자동 롤백을 제공하지 않는다.** 게시된 코멘트의 삭제·최소화는 사용자가 GitHub UI 또는 `gh`로 직접 수행한다. 이 한계를 `references/publish-contract.md`에 명시한다 |
| 게시 중 중단 | 단계 완료 기록이 남으므로 재실행이 멱등하다(R7.13, AC-8, AC-9) |

### Failure recovery and observability

- 관측 지점: `.claude/dual-review-state/<run_id>/`의 `state.json`(`agent_category_map`·`category_coverage`·private provenance/alias sidecar·`synthesis_input`·`history_restore`·`coverage_gap_evidence`·`skipped_threads` 포함), 리뷰어 산출물 JSON, Codex 이벤트·stderr 로그, `plan.json`, GitHub sticky 요약의 v1 인덱스, 게시 단계 기록.
- 각 GitHub 쓰기 호출의 대상·응답 상태·생성된 코멘트 ID를 상태에 기록해, 부분 실패 후 무엇이 게시됐는지 재실행 없이 알 수 있게 한다.
- 리뷰어별 성공·실패·`excluded` 사유, 선택된 에이전트와 유발 신호, category별 선택/성공/실패/covered 집합, 범위 축소 내역, 게시 이력 복원 상태와 finding별 최초 결손 근거를 상태·리포트·게시 요약에 남겨 커버리지 결손이 조용히 숨지 않게 한다. 종합 입력에는 alias만 남지만 private 상태에서 실제 group 대응을 진단할 수 있다.
- 알림·메트릭·트레이스는 대화형 CLI 도구에 해당하지 않는다. 사용자에게 직접 출력하는 것이 관측 수단이다.

### High-risk end-to-end verification

고위험 경로는 **PR 게시**다. 검증을 셋으로 나눈다.

1. **결정적 통합 검증(자동).** raw reviewer-output에서 시작해 agent-category coverage, ID 병합 후 alias별 observations·critiques 보존, relation→classification 세 사례를 먼저 실행한다(AC-60, AC-69~70). 이어 게시 lifecycle 전체(new → persisting → resolved → not_re_reviewed), index 생성→다음 실행 복원 왕복, 요약 전용 finding, 실제 coverage 상태를 사용하는 다섯 결손 경로와 복원 실패 하 resolve 0건, 네 목록 pagination, 각 게시 단계 실패 후 재실행 멱등, head SHA 불일치 중단, 재개 인자 충돌, 현재 브랜치 PR 해석, 열 메서드 화이트리스트, verdict 고정, `viewerCanResolve` 스킵을 fake GitHub 클라이언트로 실행한다. AC-7~16, AC-49, AC-51~52, AC-54~55, AC-58, AC-61~70이 이 경로다. 중단 조건: 하나라도 실패하면 해당 계약을 고친 뒤 전체 경로를 다시 돌린다.
2. **읽기 전용 실 API 검증(자동).** 검증 시점에 조회한 열린 PR을 대상으로 `plan`을 빈 finding 집합으로 실행해 실제 GitHub 응답 파싱을 검증한다(AC-37). 게시하지 않는다. 열린 PR이 없으면 `not applicable`로 기록한다.
3. **실 게시 E2E(수동, 이 워크플로에서 실행하지 않음).** 실제 `apply`는 외부 비가역 쓰기이므로 이 구현 워크플로의 자동 검증에 포함하지 않는다. 사용자가 스킬을 처음 실전 사용할 때 승인 게이트를 거쳐 첫 head SHA에서 v1 인덱스를 게시하고, 다음 head SHA 실행에서 GitHub만으로 같은 finding 집합이 복원되는지, 중복 없음·재실행 신규 0건인지 확인한다. **이 항목이 검증되지 않은 채 남는다는 사실을 리포트에 명시한다.**

### No production mutation confirmation

이 구현 워크플로는 프로덕션을 변경하지 않는다. 산출물은 `dot_claude/skills/dual-review/` 아래의 문서·스키마·스크립트·테스트, `docs/dual-review-maintenance.md`, `.gitignore` 한 줄이다. 구현 중 자동 커밋·푸시·머지·배포를 하지 않는다. GitHub에 대한 유일한 쓰기 경로는 스킬이 나중에 실행될 때의 PR 코멘트 게시이며, 그것도 사용자 승인 이후에만 일어난다. 이 워크플로의 검증 단계에서는 실제 게시를 수행하지 않는다(위 3항). AC-27은 `codex exec`를 실행하지만 `--sandbox read-only`이며 저장소를 변경하지 않는다.

<!-- strict-only:end -->
