# Quality Goal Specification

- Task ID: 20260903T160637Z-42-claude-codex-이중-리뷰-종합-pr-게시-스킬-추가-55cca675
- Mode: strict
- Status: IN_REVIEW
- Created: 2026-08-28
- Updated: 2026-09-05
- 판본 이력: 2026-08-28에 선행 실행(`20260828T021938Z-...`)의 Spec 라운드 2에서 93점 PASS를 받은 본을 이 실행의 초안으로 재사용했다. 그 통과는 이 실행의 게이트 판정과 무관하다. 현재 본은 이 실행의 라운드 1 지적 12건과 라운드 2 지적 5건(SPEC-09, SPEC-13~16), `report.md`의 "4차 착수 전 확정된 설계 결정", readiness attempt 1의 READY-01·READY-02, 4차 실행 Claude 공식 Spec 리뷰 라운드 1의 SPEC-20~27, readiness attempt 3·4의 READY-01을 반영한 개정본이다. Task ID 타임스탬프(`20260903T160637Z`)는 이 실행의 생성 시각, 디렉터리 날짜(`2026-09-04`)는 산출물 배치 날짜, `Updated`는 현재 개정 날짜다.
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
- R2.1a `--base <ref>`는 diff 계산의 base를 PR의 실제 base 대신 지정한 ref로 덮어쓴다. 지정된 ref가 PR의 실제 base와 다르면 R4.3의 `in_diff_range` 판정이 GitHub가 inline 코멘트를 받아들이는 실제 범위와 어긋난다. 이 경우 **inline 게시를 전면 금지하고 모든 finding을 요약으로 강등**하며, base 불일치 사실과 두 ref를 상태·리포트·게시 요약에 명시한다. **lifecycle 판정에도 영향이 있다** — `--base`가 `changed_files`를 좁히면 이전 게시 finding의 경로가 이번 리뷰 표면에서 빠질 수 있으므로, 그런 record는 R7.6a 결손 표 6행(`base_narrowed`)에 걸려 `resolved`가 아니라 `not_re_reviewed`가 되고 `resolveReviewThread`를 호출하지 않는다. `--base`가 없거나 PR의 실제 base와 같으면 정상 경로다.
- R2.2 이후 모든 단계(리뷰·교차비평·종합·게시)는 고정된 `head_sha`만 참조한다. 실행 중 브랜치가 갱신돼도 대상은 바뀌지 않는다.
- R2.3 런타임 상태는 대상 저장소 루트의 `.claude/dual-review-state/<run_id>/`에만 쓴다. INTAKE에서 `git check-ignore`로 해당 경로의 무시 여부를 확인하고, 무시되지 않으면 경고를 출력한 뒤 계속 진행한다. `.gitignore`를 임의로 수정하지 않는다.
- R2.4 이 저장소(dotfiles) `.gitignore`에는 `.claude/dual-review-state/`를 추가한다.
- R2.5 INTAKE의 순서는 이렇다: PR을 조회해 `repo`·`pr_number`·PR의 실제 base SHA·diff 계산에 쓸 `base_sha`·`head_sha`를 메모리에 얻고 → 그것으로 `run_id`를 만들고 → 상태 디렉터리를 열거나 만들고 → R2.1의 다섯 값과 실행 구성 `requested_base_ref`(`--base`를 생략했으면 null, 지정했으면 원문 문자열)·`actual_base_sha`·`rounds`(기본값을 적용한 0~2 정수)를 그 안의 `state.json`에 고정한다. `run_id`는 `<repo_owner>-<repo_name>-pr<pr_number>-<head_sha 앞 12자>` 형식으로 **결정적으로** 생성한다. 같은 PR의 같은 full head SHA에 대한 재실행은 같은 `run_id`를 얻어 직전 실행의 상태 디렉터리를 연다. 이때 새 호출의 full `head_sha`, `requested_base_ref`, 새로 해석한 `base_sha`, `actual_base_sha`, 유효 `rounds` 중 하나라도 상태의 고정값과 다르면 기존 값을 조용히 재사용하거나 덮어쓰지 않고, 단계 실행·상태 변경·GitHub 쓰기 전에 종료 코드 != 0으로 중단해 충돌한 필드와 두 값을 알린다. 따라서 같은 `--base` 문자열이 다른 commit으로 이동한 경우도 침묵하지 않는다. 다섯 값이 모두 일치할 때만 R7.13(a)의 완료 기록을 이어 쓴다. head SHA의 앞 12자가 바뀌면 다른 `run_id`가 되어 로컬 상태를 재사용하지 않는다. 서로 다른 full SHA가 우연히 같은 앞 12자를 가지면 candidate `run_id`는 같지만 full `head_sha` 대조에서 `run_id_prefix_collision`으로 중단하고 기존 상태를 읽어 진행하지 않는다. 상태 디렉터리가 없으면 새로 만들고 별도의 재개 플래그는 두지 않는다. 이 로컬 상태는 **한 `run_id` 안의 bookkeeping과 재개에만** 쓰며, head SHA를 넘는 게시 이력은 여기나 git notes에 저장하지 않고 R7.19에 따라 GitHub에서 복원한다.

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
- R3.5 스키마 변환·검증과 재시도의 **단위는 산출물을 내는 주체**다. Codex reviewer는 하나의 주체이고, Claude reviewer는 R3.1로 선택된 에이전트 **각각**이 별개 주체다. Codex의 `--output-last-message` 파일은 trim한 전체를 JSON object로 파싱한다. Claude 에이전트의 자유형식 마크다운 응답은 에이전트별로 서로 합치기 전에 다음 닫힌 변환을 거친다: trim한 응답 전체가 JSON object면 그대로 파싱하고, 아니면 trim한 전체가 언어 태그가 정확히 소문자 `json`인 단일 fenced code block으로만 구성됐을 때 그 block 내용 전체를 파싱한다. 후자의 fenced 형식에서 fence 밖에 공백 아닌 문자가 있거나 JSON block이 0개·2개 이상이거나, 어느 형식이든 파싱 결과가 object가 아니면 변환 실패다. 변환 성공 object는 `schemas/reviewer-output.schema.json`을 만족해야 한다. 변환 또는 스키마 위반 시 그 주체에게 검증 오류만 덧붙여 1회 재요청하고 2회째도 실패하면 그 **주체**를 실패로 표시한다. 다른 에이전트의 응답이나 LLM 보정으로 실패 산출물을 메우지 않는다.

  **주체 단위 판정을 열거로 고정한다.** 아래가 전부이며 다른 상태는 없다.

  | 판정 | 조건 |
  |---|---|
  | 성공 | 재시도를 포함해 스키마 유효 산출물을 반환했다. **finding 0건인 유효 산출물도 성공이다** |
  | 실패 — `call_error` | 호출 자체가 오류로 끝났다(에이전트 기동 실패, 도구 오류) |
  | 실패 — `timeout` | 응답 없이 시간 초과로 종료했다 |
  | 실패 — `schema_violation` | 1회 재요청 후에도 R3.5의 JSON 변환 또는 스키마 검증을 통과하지 못했다 |
  | 실패 — `empty_output` | 산출물 자체를 반환하지 않았다 |

- R3.5a **리뷰어 단위 `excluded`는 주체 단위 실패의 집계 결과다.** Codex reviewer는 그 주체가 실패하면 곧 `excluded`다. Claude reviewer는 R3.1로 **선택된 에이전트가 전부 실패했을 때만** `excluded`이며, 일부만 실패한 것은 R3.9 후단의 에이전트 일부 실패이지 리뷰어 실패가 아니다. 이 구분이 R3.7 승인 게이트의 발동 여부와 R7.6a의 결손 경로 선택(2·3행이냐 5·6행이냐)을 함께 결정한다. `excluded`는 R3.7이 정의하는 리뷰어 실패의 한 형태이므로 단일 리뷰 승인 게이트를 발동한다 — 제외한 채 REVIEW 단계를 마칠 수는 있으나, 남은 리뷰어가 하나뿐인 상태로 CRITIQUE·SYNTHESIS로 전이하려면 승인이 필요하다.

  주체별 판정 결과는 상태의 `agent_outcomes`에 `{agent_key: {"result": "success"|"call_error"|"timeout"|"schema_violation"|"empty_output", "attempts": n}}`로 기록한다. `agent_key`는 Codex의 `codex` 또는 R3.1의 다섯 Claude 에이전트 이름 중 하나이며, 선택되지 않은 Claude key는 만들지 않는다. `category_coverage`의 `successful_agents`·`failed_agents`는 이 기록에서만 파생한다. 다른 근거로 추정하지 않는다. 집계된 reviewer 실패 유형도 겹치지 않게 고정한다: R3.3에서 중단되면 `preflight_unavailable`; 그 밖에 reviewer가 `excluded`이고 실패 주체 중 `schema_violation`이 하나라도 있으면 `schema_excluded`; `excluded`이지만 `schema_violation`은 없고 모든 실패가 `call_error`·`timeout`·`empty_output` 중 하나면 `no_output`이다. 혼합 실패에서는 이 순서의 최초 조건을 쓰고 상태의 `reviewers.failure_type`에 기록한다.
- R3.6 `pr-review-toolkit`의 다섯 에이전트는 모두 자유형식 마크다운 출력을 지시하지만 형태가 갈린다. 네 개는 명시적 표제를 둔다(설치본 실측: `code-reviewer.md:43` `## Output Format`, `pr-test-analyzer.md:58` `**Output Format:**`, `silent-failure-hunter.md:99` `## Your Output Format`, `type-design-analyzer.md:56` `**Output Format:**`). `comment-analyzer.md`에는 그런 표제가 없고 대신 표제 없이 자유형식 출력 구조를 지시한다. 어느 쪽이든 이 스킬의 스키마 주입과 충돌하므로, 호출 프롬프트는 **다섯 에이전트 모두에 대해** 에이전트 본문의 출력 형식 지시보다 이 스킬의 스키마 계약이 우선한다는 것을 명시적으로 선언해야 한다. 플러그인 파일은 수정하지 않으므로(N8) 충돌 해소는 호출 측 프롬프트의 책임이며, 그 문구는 `references/reviewer-contract.md`에 고정한다.
- R3.7 **리뷰어 실패**는 R3.5a가 겹치지 않게 집계한 다음 셋 중 하나다: (a) `preflight_unavailable` — R3.3의 Codex 프리플라이트 실패 또는 모델 거부, (b) `schema_excluded` — 스키마 위반 2회를 포함한 주체 실패로 reviewer가 `excluded`, (c) `no_output` — reviewer의 모든 주체가 `call_error`·`timeout`·`empty_output` 중 하나여서 `excluded`. 셋 중 하나라도 발생해 남은 리뷰어가 하나뿐이면 자동으로 단일 리뷰로 진행하지 않는다. 사용자에게 단일 리뷰 계속 여부를 묻고, 상태에 단일 리뷰 승인이 기록되기 전에는 CRITIQUE·SYNTHESIS로 전이하지 않는다. 승인 시 리포트와 게시 요약에 "단일 리뷰어" 사실과 실패 유형을 명시한다. Claude 측 에이전트 **일부**가 실패한 것은 여기 해당하지 않는다(R3.9 참조).
- R3.9 **양쪽 리뷰어가 모두 실패하면**(R3.7의 셋 중 어느 조합이든) 게시하지 않고 중단한다. 단일 리뷰 승인을 묻지 않는다 — 승인해도 종합할 산출물이 없다. Claude 측 에이전트가 **일부만** 실패한 경우는 리뷰어 실패가 아니며, 나머지 에이전트로 진행하되 실패한 에이전트 목록과 R3.10으로 계산한 category coverage를 상태·리포트·게시 요약에 남긴다(R7.6a의 커버리지 결손 처리 대상이 된다).
- R3.8 `codex exec --output-schema`에 주입되는 스키마는 그 API가 거부하는 구성을 쓰지 않는다. `gpt-5.6-terra`로 실측된 거부 대상은 두 가지이며 둘 다 HTTP 400이다: **`uniqueItems`**(`'uniqueItems' is not permitted`)와 **정규식 lookaround**(`regex lookaround is not supported`). 근거는 `docs/development/2026-08-25-quality-goal/deviations.md`의 **D-15**다. `schemas/reviewer-output.schema.json`은 이 두 구성을 포함하지 않는다. 경로 탈출을 막는 패턴이 필요하면 같은 편차에서 9개 경로로 동등성이 검증된 lookaround-free 형태 `^([^/~.].*|\.[^/.].*)$`를 쓴다. 이 제약은 API로 전송되는 스키마에만 적용되므로, 로컬 검증 전용인 `critique`·`synthesis`·`publish-plan` 스키마에서는 `uniqueItems`를 써도 된다.
- R3.10 R3.9 후단의 Claude 에이전트 일부 실패와 이번 실행의 담당 에이전트 미선택이 남긴 category 결손은 아래 **`AGENT_CATEGORY_MAP_V1`**로만 계산한다. 이것은 에이전트를 선택하는 R3.1 표나 finding이 쓸 수 있는 category를 제한하는 출력 whitelist가 아니라, 어떤 review 관점이 실패했거나 아예 실행되지 않았는지를 판정하는 책임 매핑이다. 다섯 에이전트 key와 일곱 category의 합집합은 닫혀 있고, `code-simplifier`와 알 수 없는 key/category는 허용하지 않는다.

  | Claude 에이전트 | 책임 category |
  |---|---|
  | `code-reviewer` | `correctness`, `security`, `performance` |
  | `pr-test-analyzer` | `tests` |
  | `comment-analyzer` | `comments` |
  | `silent-failure-hunter` | `correctness`, `error-handling` |
  | `type-design-analyzer` | `correctness`, `types` |

  canonical agent 순서는 표의 위→아래이고, canonical category 순서는 reviewer-output enum과 같은 `correctness`, `error-handling`, `tests`, `types`, `comments`, `security`, `performance`다. map의 각 배열과 상태의 agent 배열은 이 두 순서의 부분수열로 직렬화한다.

  역방향으로 보면 `correctness`는 `code-reviewer`·`silent-failure-hunter`·`type-design-analyzer`가 중복 담당하고, 나머지 여섯 category는 표의 단일 에이전트가 담당한다. **중복 담당 판정은 "담당자 전원 성공"이 아니라 "선택된 담당자 중 한 명 이상 성공"이다.** 이번 실행에서 category `c`의 선택 담당자·성공 담당자·실패 담당자를 각각 `S(c)`·`OK(c)`·`FAIL(c)`라 할 때, `S(c)`에는 R3.1로 실제 선택된 에이전트만 들어가고 선택되지 않은 에이전트는 실패로 간주하지 않는다. `OK(c)`·`FAIL(c)`의 원소 판정은 R3.5의 주체 단위 열거와 R3.5a의 `agent_outcomes` 기록에서만 파생한다. `agent_category_uncovered(c)`는 `FAIL(c)`가 비어 있지 않고 동시에 `OK(c)`가 비어 있을 때만 참이다. 이와 별개로 **`agent_category_unselected(c)`는 `S(c)`가 공집합일 때 참이다** — 담당자가 실패한 것이 아니라 이번 실행에서 아무도 선택되지 않은 경우이며, 두 술어는 `S(c)`의 공집합 여부로 배타적으로 갈린다. 둘 다 커버리지 결손이지만 원인이 달라 R7.6a에서 서로 다른 `reason`을 받는다. 따라서 `correctness` 담당자 하나가 실패해도 다른 **선택된** 담당자가 성공했으면 covered이고, 선택된 담당자가 모두 실패했을 때만 uncovered다. `code-reviewer`가 실패하면 `security`·`performance`는 항상 uncovered이며, `correctness`는 선택된 두 중복 담당자의 성공 여부에 따라 갈린다.

  `references/reviewer-contract.md`는 위 표를 동일한 이름의 canonical JSON 상수 `AGENT_CATEGORY_MAP_V1`로 싣고 `scripts/review_state.py`의 object 상수와 exact deep equality를 이룬다. 상태에는 그 실행이 사용한 `agent_category_map`과 category별 `{selected_agents, successful_agents, failed_agents, covered}`인 `category_coverage`를 canonical 순서로 기록한다. R7.6a와 게시 계획은 이 상태의 `selected_agents` 공집합 여부와 `covered`만 소비하며 자체 매핑을 다시 만들지 않는다. 상태의 map이 스크립트 상수와 다르거나 선택된 에이전트의 성공·실패가 coverage에 완전히 반영되지 않았으면 lifecycle을 계산하지 않고 `plan`을 비정상 종료해 GitHub 쓰기를 0건으로 만든다. 이 계약 실패를 별도 결손 reason으로 꾸며 진행하지 않는다.

### R4. 위치 실측 검증

- R4.1 리뷰어 출력은 신뢰할 수 없는 데이터로 취급한다. 모든 finding의 `file`/`line_start`/`line_end`를 `head_sha` 기준 저장소 실측으로 검증한다.
- R4.2 다음 중 하나라도 참이면 `location_valid=false`로 표기하고 inline 게시에서 제외한다: (a) `head_sha` 기준으로 `file`이 존재하지 않는다, (b) `line_start`가 그 파일의 라인 수를 초과한다, (c) **`line_end`가 그 파일의 라인 수를 초과한다**, (d) **`line_start > line_end`이다**. (c)와 (d)가 필요한 이유는 실제 inline 코멘트에 실리는 라인이 `line_end`이고(R7.16) 여러 줄 코멘트의 `start_line`이 `line_start`이기 때문이다. 두 값 중 하나만 검증하면 잘못된 값이 통과해, 원자적 단일 호출인 2단계 게시(R7.12) 전체를 실패시킨다. 요약에는 "위치 미검증"으로 남긴다.
- R4.3 `base_sha..head_sha` diff의 hunk 범위 밖 라인은 `in_diff_range=false`로 표기한다. GitHub inline 코멘트는 diff 범위 안에서만 성립하므로 이 finding은 요약으로 강등한다.
- R4.4 R4.2/R4.3 판정은 LLM이 아니라 `scripts/review_state.py`가 결정적으로 수행한다. `line_start <= line_end` 같은 필드 간 순서 제약은 JSON Schema로 표현할 수 없으므로 스키마가 아니라 이 스크립트 판정으로만 고정된다.

### R5. 교차비평

- R5.1 기본 1라운드, 최대 2라운드. `--rounds 0`은 교차비평을 건너뛴다.
- R5.2 각 리뷰어에게 상대 findings를 `finding_id`와 함께 넘겨 반박을 요구한다. `schemas/critique.schema.json`의 각 항목은 `target_finding_id`, `stance`(`supports`/`challenges`), `evidence`를 required로 갖는다. `target_finding_id`가 현재 finding 집합에 없거나 `evidence`가 빈 항목은 채택하지 않으며 R6.5의 종합자 입력에도 넣지 않는다. 호출한 상위 reviewer group은 스크립트가 알고 있으므로 모델이 실제 reviewer 이름을 산출물에 되풀이하게 하지 않는다.
- R5.3 **새 근거**는 다음과 같이 계산한다: critique 산출물의 각 `evidence` 항목을 `(path, line_start, line_end, normalized_quote)` 튜플로 정규화하고(`normalized_quote`는 연속 공백 축약 + 양끝 공백 제거), 이전 라운드까지의 튜플 합집합에 없는 원소의 개수를 센다. 이 값이 0이면 다음 라운드를 실행하지 않고 종료 사유 `no_new_evidence`를 상태에 기록한다. **기준선 집합은 1차 리뷰(교차비평 이전) findings의 `evidence` 튜플을 포함한다** — 1차 리뷰가 이미 제시한 근거를 되풀이하는 반박은 새 근거가 아니다. 따라서 첫 교차비평 라운드에서도 `no_new_evidence`가 성립할 수 있다. 계산은 `scripts/review_state.py`가 수행한다.
- R5.4 **추상화 이탈 신호**도 스크립트가 결정적으로 계산한다: 한 라운드 반박의 `evidence` 항목 중 `path`가 상태의 `changed_files`에 없는 것의 비율이 0.5 이상이고, 동시에 `current_critique_count >= previous_critique_count`인 경우 신호가 참이다. 여기서 두 count는 각각 현재·직전 교차비평 라운드에서 스키마와 R5.2의 target/evidence 검증을 통과해 채택된 반박 항목 수다. **직전 교차비평 라운드가 없는 첫 라운드에서는 두 번째 조건을 거짓으로 간주한다** — 이 신호는 라운드 간 추세를 보는 것이라 최소 두 라운드가 있어야 성립한다. 따라서 첫 라운드에서는 `abstraction_drift`가 발생하지 않는다. 신호가 참이면 스크립트는 종료 사유 후보 `abstraction_drift`를 반환하고, 오케스트레이터는 라운드를 중단한 뒤 사용자에게 종료를 제안한다. 사용자 응답 없이 자동으로 계속하지 않는다.

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
- R7.4 `anchor_fingerprint`는 위치가 유효하면 `head_sha` 기준 해당 `line_end`의 소스 텍스트를 공백 정규화해 `sha256("source\0" + normalized_source_line)`으로 만든다. 위치가 유효하지 않아 소스 라인을 읽을 수 없으면 `sha256("finding\0" + normalized_title + "\0" + normalized_body)`를 fallback 내용 지문으로 쓴다(`normalized_body`는 연속 공백 축약 + 양끝 공백 제거). 따라서 게시되는 모든 finding에 비어 있지 않은 지문이 있고 두 입력 영역은 domain prefix로 충돌하지 않는다. 지문은 R7.21의 라인 이동 진단 보조 키이며 `finding_id`를 대체하거나 lifecycle·게시·resolve 판정을 바꾸지 않는다.
- R7.5 **같은 실행 안에서 `finding_id`가 충돌하면 병합한다.** 대표 위치는 `(line_start, line_end)` 오름차순 첫 항목이고, 나머지 위치는 병합 결과의 `additional_locations` 배열에 담는다. 출처 reviewer ID는 `finding_provenance[finding_id]`의 정렬·중복 제거 배열로 합쳐 어느 출처도 잃지 않는다. 동시에 R6.5가 상위 reviewer group별 원 주장과 이 finding을 대상으로 한 critique를 `observations`·`critiques`에 보존하므로, 대표 본문 하나를 고르는 과정이 합의·단독·반박 판정 입력을 지우지 않는다. inline 코멘트는 대표 위치에만 달고, 모든 위치는 R7.20의 `full` tier 요약 코멘트에 나열한다(`compact`·`minimal`의 축약 규칙은 R7.20이 우선한다). 병합은 결정적이며 스크립트가 수행한다.
- R7.6 lifecycle 분류: 이전 게시의 **활성 집합**에 없으면 `new`, 활성 집합에도 있고 지금도 있으면 `persisting`(통상 새 댓글 생성 금지, 단 R7.13의 미완료 inline 복구는 예외), 활성 집합에는 있었으나 **ID로는** 지금 없으면 **R7.6a의 판정을 거친다** — 단계 0의 ID 재대응에 걸리면 ID가 달라도 `persisting`이고, 재대응되지 않으면 결손 표에 따라 `resolved` 또는 `not_re_reviewed`다. 따라서 `persisting`은 ID 동일 경로와 재대응 경로 둘로 들어온다. 활성 집합은 R7.19 인덱스의 `new`·`persisting`·`not_re_reviewed` record와, lifecycle은 `resolved`지만 연결 스레드가 아직 열린 record다. `resolved`이면서 연결 스레드도 이미 해결됐거나 처음부터 스레드가 없던 record는 종결 이력이라 다음 비교 집합에서 제외한다. 따라서 같은 `finding_id`가 훗날 다시 나타나면 `new`가 되어 해결된 스레드 안에 숨지 않는다.

  종결 이력 record는 다음 인덱스에서 탈락하지만 그 finding의 inline 코멘트와 마커는 GitHub에 남는다. 그 **고아 마커는 복원 실패가 아니다** — R7.17이 인덱스 무결성과 마커 대조를 분리해 다루므로, 마커만 남은 finding은 R7.17의 개별 처리 규칙을 따른다.
- R7.6a **커버리지 결손 하에서는 `resolved`로 분류하지 않는다.** finding이 이번 실행의 결과에서 사라지는 원인은 실제 해소만이 아니다. 판정은 두 단계다 — 먼저 **ID 재대응**으로 제목 비결정성 때문에 사라진 것처럼 보이는 record를 되살리고, 그 다음 남은 record에 **결손 표**를 적용한다. 판정 입력은 로컬의 이전 `run_id`가 아니라 R7.19가 GitHub에서 복원한 이전 게시 인덱스의 `src`·`path`·`cat`·`fp`다.

  **단계 0 — ID 재대응.** `finding_id`는 정규화 제목의 해시를 포함하므로(R7.3) 같은 결함을 같은 리뷰어가 다시 찾아도 제목이 한 단어만 달라지면 다른 ID가 된다. ID 차분만으로 비교하면 그 record는 "사라진 것"이 되어 `resolved` + `resolveReviewThread`가 성립하고, 동시에 새 ID로 중복 inline이 게시된다. 이를 막기 위해 ID가 현재 결과에 없는 이전 record마다 `(path, cat, fp)` 세 값이 **모두** 같은 현재 finding을 찾는다.

  | 재대응 결과 | 처리 |
  |---|---|
  | 정확히 1건 일치 | 그 record를 `persisting`으로 확정한다. 이전 스레드를 재사용하고 새 inline을 만들지 않으며 `resolveReviewThread`를 호출하지 않는다. `id_remapped`를 `{old_id, new_id, matched_on: ["path","cat","fp"]}`로 상태에 기록한다 |
  | 0건 또는 2건 이상 | 재대응하지 않고 아래 결손 표로 넘긴다. 2건 이상일 때 임의로 고르지 않는다 |

  `fp`를 이 대조에 쓰는 것은 R7.21의 진단 전용 규정에 대한 **명시된 예외**다. `fp`가 lifecycle에 관여하는 곳은 여기 하나뿐이며, 나머지(연결·inline 위치·요약 tier·dedup·resolve 여부)에서는 여전히 진단 전용이다.

  **단계 1 — 결손 표.** 재대응되지 않은 record마다 아래를 위에서 아래로 확인한다. `src`와 실패 단위의 매핑은 닫힌 술어로 고정한다. `SRC_HAS(codex, src) := ("codex" ∈ src)`, `SRC_HAS(claude, src) := (∃ s ∈ src: s가 "claude:"로 시작)`이며 다른 reviewer 인자는 허용하지 않는다. `SRC_AGENTS(src) := {s ∈ src : s가 "claude:"로 시작}`이고, 어떤 agent key `a`가 **이번 실행에서 성공**했다는 것은 `a ∈ agent_outcomes ∧ agent_outcomes[a].result == "success"`를 뜻한다. 선택되지 않아 `agent_outcomes`에 없는 agent는 성공이 아니다. 이번 실행이 실제로 리뷰한 파일 집합은 `REVIEWED := changed_files(base_sha..head_sha) ∩ (R10.2(b) 범위 축소가 있으면 그 경로 집합, 없으면 전체)`다.

  | # | 결손 경로 | 인덱스에 대해 수행할 결정적 판정 | `reason` | 결과 |
  |---|---|---|---|---|
  | 1 | R3.7(a) `preflight_unavailable` | `reviewers[codex].failure_type == preflight_unavailable ∧ SRC_HAS(codex, record.src)` | `codex_unavailable` | `not_re_reviewed` |
  | 2 | R3.7(b) `schema_excluded` | `∃ r ∈ {codex, claude}: reviewers[r].failure_type == schema_excluded ∧ SRC_HAS(r, record.src)` | `reviewer_excluded` | `not_re_reviewed` |
  | 3 | R3.7(c) `no_output` | `∃ r ∈ {codex, claude}: reviewers[r].failure_type == no_output ∧ SRC_HAS(r, record.src)` | `reviewer_no_output` | `not_re_reviewed` |
  | 4 | 출처 에이전트가 이번에 없음 | `SRC_AGENTS(record.src) ≠ ∅ ∧ ∀ a ∈ SRC_AGENTS(record.src): a가 이번 실행에서 성공하지 않음` | `src_agent_unavailable` | `not_re_reviewed` |
  | 5 | R10.2(b) 범위 축소 | `record.path ∉ REVIEWED ∧ 범위 축소가 있고 record.path ∉ 축소 경로 집합` | `path_out_of_scope` | `not_re_reviewed` |
  | 6 | `--base` 이동으로 좁아진 diff | `record.path ∉ REVIEWED ∧ 5행에 해당하지 않음`(즉 `--base` 때문에 `changed_files`에서 빠진 경우) | `base_narrowed` | `not_re_reviewed` |
  | 7 | R3.9 후단의 Claude 에이전트 일부 실패 | 이전 record의 `cat=c`에 대해 R3.10의 `agent_category_uncovered(c)`가 참 | `agent_category_uncovered` | `not_re_reviewed` |
  | 8 | 담당 에이전트 미선택 | 이전 record의 `cat=c`에 대해 R3.10의 `agent_category_unselected(c)`가 참 | `agent_category_unselected` | `not_re_reviewed` |

  **4행이 왜 필요한가.** 7·8행은 category 단위 판정이라 중복 담당 category에서 구멍이 난다. `correctness`는 `code-reviewer`·`silent-failure-hunter`·`type-design-analyzer`가 함께 담당하고 `code-reviewer`는 항상 선택되므로, 직전 실행에서 `silent-failure-hunter`가 낸 `cat=correctness` record는 이번 diff에 try/catch 토큰이 없어 그 에이전트가 선택되지 않아도 `S(correctness) ≠ ∅ ∧ OK(correctness) ≠ ∅`이 되어 7·8행 모두 거짓이다. 문제를 실제로 본 관점이 이번에 실행되지 않았는데 `resolved`가 된다. D25가 R3.10의 표를 출력 whitelist가 아니라고 명시하므로 전문 에이전트가 담당 밖 category finding을 낼 수 있고, 그러면 `code-reviewer`만 담당하는 `security`·`performance`에서도 같은 경로가 성립한다. 4행은 category가 아니라 **그 finding을 실제로 낸 출처**를 보므로 이 구멍을 닫는다. 7·8행은 `src`가 비었거나 codex만인 record를 위해 남는다.

  **6행이 왜 필요한가.** `--base <ref>`는 diff 계산의 base를 덮어쓰므로(R2.1a) 지정 ref가 PR 실제 base보다 head 쪽에 가까우면 `changed_files`가 좁아지고 그 사이에서만 변경된 파일이 리뷰어 입력에서 사라진다. 사용자가 범위 축소를 하지 않았다면 5행에 걸리지 않으므로, 6행이 없으면 그 파일의 이전 finding이 `resolved`가 되어 스레드가 닫힌다. 5·6행은 같은 술어(`record.path ∉ REVIEWED`)를 공유하고 `reason`만 원인에 따라 갈린다.

  **8행이 왜 필요한가.** R3.1의 에이전트 선택은 이번 diff의 신호에 좌우된다. `comment-analyzer`는 주석 토큰 매치가 3건 이상일 때만 선택되므로, 직전 실행에서 3건이라 선택돼 `comments` finding을 게시한 뒤 이번 실행에서 매치가 2건으로 줄면 선택되지 않는다. 문제의 주석은 그대로인데 아무도 다시 보지 않았고 경로는 여전히 검토 범위 안이라 5·6행에도 걸리지 않는다. 7행은 `FAIL(c)`가 비어 있어 거짓이다.

  1~3행의 판정식은 모두 `reviewers[r].failure_type == <행의 실패 유형> ∧ SRC_HAS(r, record.src)` 형태다(1행의 `r`만 `codex`로 고정).

  **판정 순서와 기록.** (1) R7.19의 복원이 `ok`인지 확인하고, (2) 단계 0의 재대응을 수행하고, (3) 재대응되지 않은 record마다 표를 위에서 아래로 확인한다. 하나라도 걸리면 `not_re_reviewed`, 모두 해당하지 않을 때만 `resolved`다. 7행은 인덱스의 `cat`을 R3.10의 고정 상수로 계산해 상태에 기록한 `category_coverage`에 조회할 뿐 `src`나 임의 fixture 매핑에서 담당 category를 추측하지 않는다. 인덱스 블록 부재, version 불일치, base64 또는 JSON 디코드 실패, 필수 key·값 결손, 중복 `id` record 때문에 `category`·출처·경로·지문 중 하나라도 복원할 수 없으면 `history_restore.status != "ok"`로 두고 **그 실행에서는 `resolved`를 한 건도 만들지 않는다**. 이때 기존 inline 마커로 식별 가능하면서 이번 결과에는 없는 이전 finding만 reason=`history_unavailable`인 `not_re_reviewed`로 보존한다. 이번 결과에도 같은 ID가 있으면 ID 대조만으로 `persisting`이며, 복원할 수 없는 요약 전용 finding에는 어떤 스레드 쓰기도 시도하지 않는다. 판정은 스크립트가 수행하며 finding별 재대응 여부와 최초 일치 경로, 사용한 인덱스 필드·값을 상태의 `coverage_gap_evidence`에 기록한다.

  **잔존 한계.** 단계 0의 재대응은 `(path, cat, fp)` 완전 일치에만 작동한다. 같은 결함이 다른 제목으로 재보고되면서 **동시에** 그 라인의 소스 텍스트도 바뀌어 `fp`까지 달라지면 재대응되지 않고, 결손 표에도 걸리지 않으면 `resolved`가 된다. 이 경우는 해당 코드가 실제로 변경된 상황이므로 재검토가 일어났다고 볼 근거가 있지만 완전한 보장은 아니다. 이 한계를 Security and risk의 리스크 표와 R6.4의 잔존 한계에 함께 기록하고, `id_remapped`가 발생한 실행에서는 그 사실을 게시 요약에 남겨 사람이 확인할 수 있게 한다.

- R7.7 lifecycle 별 게시 동작은 다음과 같다.

  | 분류 | 요약 코멘트 | 리뷰 스레드 |
  |---|---|---|
  | `new` | 신규 항목으로 기재 | inline 코멘트 생성 |
  | `persisting` | 유지 항목으로 기재 | 통상 건드리지 않음. 다만 직전 record의 `placement=inline`이고 파생 상태가 `inline_pending`이며 현재 finding이 inline 가능하면 R7.13에 따라 누락 댓글을 정확히 한 번 복구 |
  | `resolved` | "해소됨" 목록에 기재 | 연결된 열린 스레드만 `resolveReviewThread`로 해결. 요약 전용·이미 해결된 스레드는 호출 없음 |
  | `not_re_reviewed` | **"이번 실행에서 재검토되지 않음" 목록에 사유와 함께 기재** | **건드리지 않음 — resolve 하지 않는다** |

  `resolved`와 `not_re_reviewed`의 차이가 이 표의 요점이다. 미해소 지적을 "해소됨"으로 게시하고 스레드를 자동 해결하면 되돌리기 어려운 외부 쓰기로 커버리지 결손이 굳는다. 스레드에 별도 답글 코멘트는 어느 분류에서도 남기지 않는다 — R7.14 화이트리스트 안의 수단만 쓰기 위한 결정이다.
- R7.8 요약은 PR당 하나의 sticky 코멘트다. 본문에 `<!-- dual-review:summary -->` 마커를 두고, 존재하면 새로 만들지 않고 갱신한다.
- R7.9 inline 코멘트 본문 끝에 `<!-- dual-review:finding:<finding_id> -->` 마커를 둔다. 이것이 inline dedup과 R7.19 인덱스 record 대조의 키다. 전체 메타데이터는 inline마다 중복하지 않고 sticky 요약의 R7.19 인덱스에 둔다.
- R7.10 요약 첫 줄은 `AI-generated review — Claude + Codex — reviewed commit: <head_sha>`로 시작한다.
- R7.11 `apply` 실행 직전 실제 PR head SHA를 다시 조회한다. 고정된 `head_sha`와 다르면 아무것도 게시하지 않고 비정상 종료한다.
- R7.12 **게시는 세 단계로 나뉘며 각 단계의 완료 여부를 상태에 기록한다.**
  1. 요약 코멘트 생성 또는 갱신 (단일 호출). R7.19 인덱스의 `placement`가 각 finding의 의도된 게시 형태를 GitHub에 먼저 지속한다. `placement=inline` 자체는 inline 완료 증거가 아니며, 2단계 marker와 결합해야 완료다.
  2. inline 리뷰 생성 — `POST /repos/{o}/{r}/pulls/{n}/reviews`에 `event: "COMMENT"`와 `comments` 배열을 담는 **단일 원자적 호출**. 부분 성공은 발생하지 않는다. 성공한 각 comment의 R7.9 marker가 `placement=inline`의 완료 증거다.
  3. `resolved` 스레드 해결 — 스레드당 하나의 GraphQL 호출. 성공한 스레드 ID를 개별 기록한다.
- R7.13 `apply`는 멱등이다. 재실행 시 (a) 같은 `run_id`의 로컬 완료 기록이 남아 있으면 완료 단계를 다시 실행하지 않고, (b) 2단계는 기존 코멘트의 `finding_id` marker를 대조해 이미 게시된 finding을 `comments` 배열에서 제외하며 남는 항목이 없으면 호출 자체를 생략하고, (c) 3단계는 아직 해결되지 않은 스레드만 처리한다. 로컬 상태가 사라진 실행 간 복구에서는 R7.17이 GitHub의 `placement`와 marker를 결합해 `inline_pending`을 복원한다. 이전 `placement=inline`인데 같은 ID marker가 0개이고, 현재 결과에 같은 ID의 inline 가능한 finding이 있으면 lifecycle이 `persisting`이어도 현재 `head_sha`의 위치·본문으로 **복구 comment를 정확히 한 번** 2단계 배열에 넣는다. 현재 finding이 없거나 inline 불가능하면 댓글을 만들지 않고 `delivery_states`에 `action=isolate`와 사유를 남기며, 모든 요약 tier에 경고한다. 정확히 하나의 marker가 R7.17 연결 조건까지 만족할 때만 `inline_posted`라 복구하지 않고, 같은 ID marker의 불일치·중복은 복구하지 않고 격리한다.
- R7.14 GitHub 접근은 전부 주입 가능한 클라이언트 인터페이스(R8.2)를 거치고, 클라이언트는 각 호출을 `(kind, method, target)` **3튜플**로 기록한다. `kind`는 `rest`/`graphql`/`cli`, `method`는 REST의 HTTP 메서드 또는 `QUERY`/`MUTATION`/`EXEC`, `target`은 REST 경로 템플릿·GraphQL 오퍼레이션명·`gh` 서브커맨드다. 기록된 모든 3튜플은 화이트리스트(Interfaces 절)의 부분집합이어야 하며, 목록 밖 호출(라벨·상태·머지·assignee 변경, 스레드 답글 등)을 수행하지 않는다. 화이트리스트는 **호출의 종류**를 제한하는 것이지 횟수를 제한하지 않는다 — R8.2의 페이지 순회로 같은 3튜플이 여러 번 기록되는 것은 위반이 아니다.
- R7.15 `--no-publish`는 `plan`까지만 수행하고 `apply`를 실행하지 않으며 게시 호출을 0건으로 만든다.
- R7.16 inline 코멘트 원소는 `path`, `line`, `side`, `body`를 싣고 `body` 끝에 `finding_id` 마커를 둔다. `line`은 finding의 `line_end`, `side`는 `RIGHT`(추가·수정된 쪽)다. `line_start < line_end`인 finding은 `start_line`(= `line_start`)과 `start_side`를 함께 실어 여러 줄 코멘트로 만들고, `line_start == line_end`이면 두 필드를 생략한다. `start_line`이 `line`과 **같은 diff hunk 안에 없으면** 여러 줄 코멘트를 만들지 않고 `line` 단일 라인으로 축소하며, 축소 사실을 상태에 기록한다. **이 축소 규칙의 근거는 실측이 아니라 보수적 선택이다** — 2026-09-04에 조회한 GitHub 공식 REST 문서는 `side`의 허용값(`LEFT`/`RIGHT`)과 기본값(`RIGHT`)은 명시하지만 `start_line`과 `line`이 같은 hunk 안에 있어야 한다는 제약은 명시하지 않는다. 실제 API 반응을 확인하려면 PR에 코멘트를 생성해야 하고 그것은 외부 쓰기라 이 워크플로에서 수행하지 않았다. 축소는 요청 범위를 넓히지 않고 좁히는 방향이므로 전제가 틀려도 안전하다. deprecated인 `position`·`original_position`은 쓰지 않는다.
- R7.18 `apply`는 `resolveReviewThread` 호출 전에 그 스레드의 `viewerCanResolve`를 확인한다. 거짓이면 호출하지 않고 건너뛰며, 건너뛴 스레드 ID와 사유를 상태에 기록하고 요약 코멘트에 남긴다. 권한 부족을 조용히 삼키지 않는다.
- R7.17 기존 게시물 조회 결과에서 각 리뷰 코멘트의 `id`, `node_id`, `pull_request_review_id`, `path`, `line`, `original_line`을 상태에 기록한다. `node_id`는 GraphQL 리뷰 스레드와의 연결 키이고, `original_line`은 라인 이동·outdated comment 대조를 보조한다. 또한 R7.19의 인덱스에서 복원한 `id`·`cat`·`src`·`path`·`line`·`fp`·`run`·`lifecycle`·`placement`, 연결된 review의 `id`·`commit_id`·`state`, `history_restore`의 상태와 실패 사유를 함께 기록한다. REST의 `pull_request_review_id`로 comment와 review를 연결한다. **복원 판정은 인덱스 무결성, record의 의도된 placement와 marker로 계산한 delivery 상태, 인덱스 밖 고아 marker의 세 층으로 나뉜다.**

  **(1) 인덱스 무결성 — 실패하면 전체 복원 실패.** 인덱스 블록 부재, version 불일치, base64 또는 JSON 디코드 실패, 루트 형태 위반, record의 필수 key·값 결손, 중복 `id`. 이 경우 `history_restore.status`를 `invalid`로 두고 R7.6a의 전면 안전 경로를 탄다.

  **(2) `placement` ↔ 게시물 대조 — 미완료와 불일치를 구분한다.** `placement=inline` record의 일치 marker란 marker의 `finding_id`와 record `id`, REST와 record의 `path`, record `line`과 REST의 non-null `line` 또는 `original_line` 중 하나, comment의 `pull_request_review_id`와 review의 `id`가 모두 일치하는 정확히 하나의 comment다. `plan`은 record마다 아래 닫힌 규칙으로 `history_restore.delivery_states`의 `{finding_id, placement, status, action, reason}`을 만든다. `inline_pending`은 R7.12의 정상 도달 가능 중간 상태이지 인덱스 손상이 아니므로 전체 `history_restore.status`는 `ok`를 유지한다.

  | persisted `placement` | marker 대조 | `status` | `action`·`reason` |
  |---|---|---|---|
  | `summary_only` | 같은 ID marker 0개 | `summary_only` | `none`·null — comment/review 연결을 요구하지 않음 |
  | `inline` | 일치 marker 정확히 1개 | `inline_posted` | `none`·null |
  | `inline` | 같은 ID marker 0개 | `inline_pending` | 현재 같은 ID가 inline 가능하면 `retry_inline`·null, 현재 finding이 없으면 `isolate`·`current_missing`, 현재 finding은 있지만 inline 불가능하면 `isolate`·`current_not_inline_eligible` |
  | 어느 값이든 | 같은 ID marker가 있으나 일치 marker가 없거나 2개 이상 | `linkage_invalid` | `isolate`·`marker_mismatch` 또는 `duplicate_markers` |

  `retry_inline`만 R7.13의 복구 comment를 만들 수 있다. `isolate`는 해당 record의 신규 inline·resolve를 모두 0건으로 하고 상태와 요약에 사유를 남기되, orthogonal한 lifecycle은 현재 finding 존재 여부와 R7.6a로 계산한다. `linkage_invalid` record도 다른 정상 record와 전역 `history_restore.status`를 건드리지 않는다. 현재 결과에 같은 ID가 있으면 lifecycle은 `persisting`이지만 inline·resolve를 금지하고, 없으면 기존처럼 `history_unavailable`인 `not_re_reviewed`로 격리한다. `summary_only`인데 marker가 있는 경우도 `marker_mismatch`이며, `inline_pending`을 marker 불일치로 오인해 격리하거나 `summary_only`로 오인해 영구 누락시키지 않는다.

  **(3) 인덱스에 없는 고아 마커.** 이번에 읽은 인덱스의 어떤 record와도 대응하지 않는 `dual-review:finding` 마커가 게시물에 있을 수 있다. 이것은 정상 운용에서 발생한다 — R7.6의 종결 이력 필터가 과거 record를 인덱스에서 떨어뜨린 뒤에도 그 코멘트와 마커는 GitHub에 남기 때문이다. **고아 마커는 전체 복원 실패로 취급하지 않고** 연결된 스레드 상태로 결정적으로 가른다.

  | 고아 마커의 스레드 상태 | 판정 | 쓰기 |
  |---|---|---|
  | 스레드가 이미 `isResolved=true`이거나 스레드가 없음 | 종결 이력으로 간주하고 무시한다 | 없음 |
  | 스레드가 열려 있음(`isResolved=false`) | 정체를 복원할 수 없으므로 `history_unavailable` 사유의 `not_re_reviewed`로 보존한다 | 없음 — 스레드를 건드리지 않는다 |

  이 분리가 없으면 다음 경로가 성립한다: run1 게시 → run2에서 `resolved`가 되고 스레드 해결 → run3에서 R7.6의 종결 이력 필터로 인덱스에서 탈락 → run4부터 남은 고아 마커가 전체 복원 실패를 상시 유발 → 그 이후 모든 실행에서 `resolved`가 0건. 첫 해소 주기 하나만 지나면 G4의 "실제로 해소된 지적만 스레드 정리"가 영구히 도달 불가능해진다. (1)·(2)·(3)의 분리가 그 경로를 끊는다.
- R7.19 **게시 이력의 실행 간 source of truth는 GitHub다.** `plan`은 R8.2의 이슈 코멘트·리뷰 코멘트·review·review thread 조회로 이 스킬이 이전에 게시한 finding 집합을 복원한다. 로컬 상태 파일과 git notes는 실행 간 게시 이력 저장소로 쓰지 않는다. 사람이 작성했거나 다른 봇이 작성해 `dual-review` 마커가 없는 코멘트는 복원·분류·resolve 대상이 아니다.

  sticky 요약 본문에는 가시적 리뷰 내용과 별도로 정확히 하나의 기계 판독 인덱스 블록을 둔다.

  ```text
  <!-- dual-review:index v1 <base64(JSON)> -->
  ```

  payload는 UTF-8 JSON의 **표준 base64** 인코딩이며 알파벳은 `A-Z a-z 0-9 + /`와 끝의 padding `=`만 허용한다(base64url 금지). JSON 루트는 `{"findings": [...]}`이고, `findings`는 이번 요약에 기재되는 inline·요약 전용 finding 전부를 `id`당 정확히 한 record로 담아 `(id, path, line)` 순으로 정렬한다. 중복 `id`는 생성 전에 R7.5로 합쳐야 하며 복원 입력에서 발견하면 `invalid`다. 직렬화는 Python 표준 라이브러리의 `json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)` 결과를 UTF-8로 인코딩해 같은 record 집합이 항상 같은 payload를 만들게 한다. 각 record는 다음 **아홉 key**를 모두 갖고 알 수 없는 key를 허용하지 않는다.

  | key | 값과 용도 |
  |---|---|
  | `id` | `finding_id`; inline 마커와 대조하는 소문자 16진수 12자리 식별자 |
  | `cat` | `category`; reviewer-output의 7값 enum 중 하나이며 해시인 `id`에서 역산하지 않는다 |
  | `src` | 출처 reviewer ID의 정렬된 비어 있지 않은 배열. 원소는 `codex` 또는 R3.1이 실제로 선택할 수 있는 다섯 이름 중 하나를 붙인 `claude:<에이전트명>`이며, 그 밖의 값과 `claude:code-simplifier`는 거부한다. 병합된 finding의 복수 출처를 잃지 않는다 |
  | `path`, `line` | 경로 탈출 없는 정규화 저장소 상대 경로와 1 이상 정수인 `line_end`; inline이 없는 요약 전용 finding도 여기서 복원한다 |
  | `placement` | 의도된 게시 형태 `inline` 또는 `summary_only`. `inline`은 일치 marker가 있어야 완료이고 없으면 `inline_pending`; `summary_only`는 marker가 없는 것이 정상이다. lifecycle과 별개이며 두 값을 추정하지 않는다 |
  | `fp` | R7.4의 `anchor_fingerprint`; 위치 유효 여부와 관계없이 비어 있지 않은 64자리 소문자 16진수 문자열. **형식 검증 뒤 소비처는 둘이다** — R7.6a 단계 0의 ID 재대응 대조 키(`(path, cat, fp)` 완전 일치)와 R7.21의 anchor 변화 진단. 그 밖의 dedup·게시·resolve 판정에는 쓰지 않는다 |
  | `run` | 이 record를 담은 요약을 마지막으로 게시한 R2.5 형식의 `run_id`(최초 발견 run이 아님). **형식 검증 뒤에는 R7.21의 직전 게시 run 진단에만 소비하며 lifecycle·dedup·게시·resolve 판정에는 쓰지 않는다** |
  | `lifecycle` | 게시 당시의 `new`·`persisting`·`resolved`·`not_re_reviewed` 중 하나 |

  `new` record의 `placement`는 이번 계획의 inline eligibility로 정한다. inline comment 후보면 `inline`, R2.1a·R4.2·R4.3 때문에 요약으로 강등됐으면 `summary_only`다. `persisting`은 직전 `placement`를 그대로 이어받는다. 따라서 이전 `summary_only` finding이 단지 위치 가능해졌다는 이유로 신규 댓글을 만들지 않으며, 이전 `inline`의 marker가 없을 때만 R7.13의 제한된 복구 예외가 열린다. 이번 결과에 없는 `resolved`·`not_re_reviewed` record도 직전 인덱스의 `id`·`cat`·`src`·`path`·`line`·`placement`·`fp`를 그대로 이어받는다. 그 밖의 현재 metadata는 이번 finding과 `finding_provenance`에서 만들고 모든 record의 `run`과 `lifecycle`만 이번 게시 실행 값으로 갱신한다. 이렇게 해야 결손으로 재검토되지 않은 finding의 판정 입력과 미완료 inline 의도가 다음 실행까지 계속 남는다.

  유효한 이전 인덱스가 없어 메타데이터를 복원하지 못한 legacy inline marker는 예외다. 알 수 없는 `cat`·`src`·`fp`를 지어내 v1 record로 만들지 않고, 가시적 요약에 `history_unavailable` 경고와 ID만 남긴다. 원래 inline marker가 GitHub에 계속 있으므로 다음 실행도 이를 식별해 자동 resolve하지 않는다. 그 ID가 이후 현재 finding으로 다시 나오면 이번 실행의 완전한 메타데이터로 정상 v1 record를 만들 수 있다.

  요약을 갱신할 때 직전 인덱스를 읽어 lifecycle을 계산한 뒤 현재 실행의 전체 record 집합으로 인덱스를 원자적으로 교체한다. 표준 base64 payload에는 `-`가 없으므로 payload 내부에서 HTML 주석을 닫는 `--`가 생기지 않는다. 파서는 주석 내용을 지시문으로 해석하지 않고 version·base64·JSON shape·필드 타입·허용값을 엄격히 검증한다. 실패 시 부분 집합을 반환하지 않고 R7.6a의 `history_unavailable` 기본값으로 전환한다.

- R7.20 sticky 요약 본문에는 스킬 자체의 보수적 운영 상한 `SUMMARY_BODY_MAX_BYTES = 49_152`를 적용한다. 이 값은 GitHub가 문서화한 플랫폼 상한을 인용하거나 추정한 값이 아니다. 2026-09-04에 확인한 공식 REST 문서가 comment body의 길이 상한을 명시하지 않으므로, 미문서 API·중간 계층 변화에 여유를 남기고 단일 쓰기 요청의 크기를 예측 가능하게 제한하기 위해 스킬이 48 KiB를 독립적으로 선택한다. 크기는 첫 줄, 가시 본문, 공백, `dual-review:summary` 마커와 R7.19 인덱스 블록까지 **최종 body 전체를 UTF-8로 인코딩한 바이트 수** `len(body.encode("utf-8"))`로 계산한다. 문자 수나 base64 payload만 세지 않는다. `references/publish-contract.md`와 `scripts/publish_findings.py`는 같은 이름·값의 상수를 가져야 한다.

  `plan`은 먼저 R7.19의 완전한 v1 record 집합과 인덱스 블록을 만든다. 크기를 맞추려고 record를 버리거나 field를 줄이거나 payload를 자르거나 여러 인덱스·여러 sticky 코멘트로 나누지 않는다. 그 뒤 가시 본문만 아래 tier 순서로 다시 렌더링하고, 각 tier 안의 lifecycle과 finding 순서는 R7.19의 canonical record 순서를 따른다. 다른 요구사항이 노출을 강제한 단일 리뷰, 일부 에이전트 실패, base 불일치, 범위 축소, `history_unavailable`, `inline_pending` 격리, resolve 권한 부족 경고와 **R7.6a 단계 0의 ID 재대응 발생 사실**은 모든 tier에 남긴다.

  | tier | 결정적 가시 본문 |
  |---|---|
  | `full` | 네 lifecycle 절에 모든 finding을 싣는다. 현재 실행의 finding은 ID·category·path:line·title·body·failure scenario·recommendation·evidence·additional locations를 모두 싣고, 이번 결과에 없어 직전 인덱스만으로 이어받은 `resolved`·`not_re_reviewed`는 인덱스에서 복원 가능한 ID·category·path:line과 lifecycle reason을 싣는다 |
  | `compact` | 네 lifecycle 절과 모든 finding을 유지하되 body·failure scenario·recommendation·evidence·additional locations를 먼저 제거한다. **`full`과 같은 방식으로 두 부류를 구분한다** — 현재 실행의 finding은 ID·category·path:line·title을, 이번 결과에 없어 직전 인덱스만으로 이어받은 `resolved`·`not_re_reviewed`는 **title 없이** ID·category·path:line과 lifecycle reason을 남긴다. 후자에 title이 없는 것은 R7.19 v1 record의 아홉 key에 title이 없기 때문이며, 없는 값을 지어내거나 빈 문자열로 채우지 않는다 |
  | `minimal` | 네 lifecycle 절과 모든 finding을 유지하되 일반 finding은 ID만, `not_re_reviewed`는 ID와 reason만 남긴다. 필수 경고의 식별자·사유는 생략하지 않는다 |

  `full` → `compact` → `minimal` 중 최종 UTF-8 바이트 수가 상한 이하인 첫 tier를 선택하고 `summary_render.selected_tier`에 기록한다. 임의 문자 수에서 자르는 동작은 없다. 인덱스 블록 하나만으로 상한을 넘으면 `summary_index_oversize`, 인덱스는 들어가지만 필수 첫 줄·마커·경고·네 최소 목록과 합친 `minimal`도 넘으면 `summary_body_oversize`다. 두 경우 모두 `plan`은 적용 가능한 `plan.json`을 내지 않고 종료 코드 != 0으로 중단하며 계산한 tier별 바이트 수와 오류를 상태·stderr에 남긴다. GitHub 쓰기, inline review 생성, thread resolve는 모두 0건이고, 기존 sticky 코멘트를 그대로 둔다. `apply`도 입력 계획의 body 바이트 수와 인덱스 완전성을 다시 검사해 위반 시 모든 쓰기 전에 거부한다.

- R7.21 유효한 이전 v1 record의 `run`은 판정 입력이 아니라 **진단 입력**으로 실제 소비한다. `fp`는 R7.6a 단계 0의 ID 재대응 대조 키를 겸하므로 그 한 곳에서만 판정 입력이고, 아래 진단에서는 `run`과 같이 진단 입력으로 쓴다. `plan`은 이전 record마다 상태의 `history_diagnostics`에 `{finding_id, source_run_id, run_relation, fingerprint_relation}`을 기록한다. `source_run_id`는 이전 record의 `run`이고, 현재 `run_id`와 같으면 `run_relation=same_run`, 다르면 `different_run`이다. 같은 `finding_id`의 현재 finding이 없으면 `fingerprint_relation=not_comparable`; 있으면 이전·현재 `fp`와 `(path, line)`을 비교해 `fp`와 위치가 모두 같으면 `same_anchor`, `fp`는 같고 위치만 다르면 `anchor_moved`, `fp`가 다르면 `anchor_changed`다. 이 진단은 형식 검증을 통과한 값에만 만들며 최초 발견 run을 추정하지 않는다. `run` 값과 진단 결과는 `finding_id`, R7.6 lifecycle, R7.17 연결, inline 위치, 요약 tier, dedup, thread resolve 여부와 GitHub 쓰기 집합을 바꾸지 않는다. **`fp`에는 예외가 하나 있다** — R7.6a 단계 0의 ID 재대응이 `(path, cat, fp)` 완전 일치를 대조 키로 쓴다. 그 한 곳을 제외하면 `fp`도 진단 전용이며 연결·inline 위치·요약 tier·dedup·resolve 여부를 바꾸지 않는다.

### R8. 결정적 스크립트

- R8.1 `scripts/review_state.py`는 **`finding_id`·`anchor_fingerprint` 계산과 R7.5 병합의 소유 모듈**이며(두 값이 SYNTHESIS 이전에 확정돼야 R6.1·R6.5의 익명 입력이 성립한다), 그 밖에 실행 상태(대상 고정, 재실행 인자 충돌 검사, 에이전트 선택 기록, Claude 마크다운의 주체별 JSON 변환·스키마 검증, 다섯 `agent_outcomes`와 reviewer `failure_type` 집계, R3.10 category coverage 계산, 리뷰어 산출물 등록과 재시도 카운트, 위치 실측 검증, 교차비평 새 근거·추상화 이탈 계산, `finding_provenance`·`reviewer_aliases` 비공개 sidecar 보존, R6.5의 익명 per-finding 종합 입력 생성·셔플, relation과 종합 분류의 정합성 검증, 단일 리뷰 승인 기록, 종합 결과 기록)와 Interfaces 절의 결정적 `render_report(state, synthesis)`를 담당한다. `SKILL.md`는 이 함수가 반환한 Markdown을 실제 사용자 리포트로 그대로 표시하며 자유형식 재작성으로 필수 한계·경고를 제거하지 않는다.
- R8.2 `scripts/publish_findings.py`는 `plan`/`apply` 서브커맨드로 게시 계획 산출과 게시를 담당한다. **`finding_id`·`anchor_fingerprint` 계산과 R7.5 병합은 이 모듈이 소유하지 않는다** — R8.1의 `review_state.py`가 소유하고 이 모듈은 AC-30이 허용하는 형제 모듈 import로 그 함수를 호출한다. 그래야 SYNTHESIS 이전에 병합이 끝나야 하는 R6.1·R6.5의 전제와 게시 단계의 dedup이 같은 구현을 쓴다. 여기에는 R7.19 이력 복원과 `placement`/marker delivery 상태 계산·복구 계획, R7.21 진단 생성, R7.20의 tier별 요약 렌더링·UTF-8 바이트 상한 검사도 포함된다. GitHub 접근은 주입 가능한 클라이언트 인터페이스를 거쳐 테스트에서 fake로 대체할 수 있어야 하며, 인터페이스는 정확히 다음 열 메서드만 노출한다. 각 메서드는 호출을 R7.14의 3튜플로 기록한다. `--pr`가 없을 때는 `git branch --show-current`로 로컬의 현재 브랜치명을 얻은 뒤 `list_open_prs(repo, head_ref=<현재 브랜치>, limit=2)`를 호출한다. 빈 브랜치명(detached HEAD)이면 클라이언트를 호출하지 않고 중단한다. 구현 명령은 `gh pr list --repo <repo> --state open --head <head_ref> --limit <limit> --json number,headRefName,headRefOid,baseRefName,baseRefOid,url`이며 서버 측 `--head` 필터를 limit보다 먼저 적용한다. 결과가 정확히 1건일 때만 그 번호로 `get_pr_meta`를 호출한다. 0건이면 "현재 브랜치 PR 없음", limit에 찬 2건(즉 2건 이상 존재)이면 "대상 모호"로 상태 생성 전에 중단하고 `--pr` 지정을 요구한다. AC-37의 저장소 전체 열린 PR 탐색만 `head_ref=null, limit=1`을 쓴다.

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
- R9.2 `quality-goal`과 마찬가지로 SemVer를 따른다. `SKILL.md` frontmatter의 `version` 값은 `MAJOR.MINOR.PATCH` 형식이고, `docs/dual-review-maintenance.md`의 "버전 정책" 절이 어떤 변경이 어느 자리를 올리는지 명시하며, 같은 문서의 별도 "후속 작업" 절에 SARIF 이관 등 미지원 작업의 현재 상태와 착수 조건 또는 호환성 검토 범위를 기록한다.

### R10. 입력 규모 한계

- R10.1 INTAKE에서 변경 파일 수와 diff 라인 수를 계산한다. 기본 임계값은 파일 100개, diff 20,000줄이며 `references/`에 상수로 기록한다.
- R10.2 임계값을 넘으면 자동 진행하지 않는다. 사용자에게 규모를 알리고 (a) 중단 또는 (b) 사용자가 지정한 경로 부분집합으로 범위 축소 중 하나를 선택하게 한다.
- R10.3 어떤 경우에도 무언의 절단을 하지 않는다. 범위를 축소했다면 축소된 경로 집합과 제외된 파일 수를 상태·리포트·게시 요약에 명시한다.

## Acceptance criteria

각 기준은 지정된 검증으로 객관적으로 판정한다. 기준 경로는 저장소 루트이고, 단위 테스트는 모두 `dot_claude/skills/dual-review/tests/` 아래에 있다. 모든 AC의 `[실행]` 표시는 Test strategy의 "판정 명령" 표에 있는 정확한 명령과 연결된다. 각 항목 끝의 `검증:` 문구는 그 명령이 단정해야 할 입력·출력이고, 명령 없이 문서 존재만 눈으로 확인하는 AC는 없다.

### 식별자와 위치

- **AC-1** [실행] `finding_id`는 제목의 대소문자·연속 공백·양끝 구두점 차이에 대해 동일한 값을 낸다. 검증: 단위 테스트.
- **AC-2** [실행] `finding_id`는 `line_start`가 달라져도 동일하고, `path` 또는 `category`가 달라지면 달라진다. 검증: 단위 테스트.
- **AC-3** [실행] `anchor_fingerprint`는 위치가 유효할 때 고정 `head_sha`의 `line_end` 소스 텍스트로 계산되고 같은 정규화 텍스트에 대해 라인 번호와 무관하게 동일하다. 고정 commit과 dirty worktree의 같은 라인 텍스트가 다른 fixture에서도 지문은 commit 텍스트를 따른다. 위치 무효 finding은 같은 정규화 title·body에 대해 같은 fallback 지문을 만들고, source 지문과 fallback 지문은 같은 원문이어도 domain prefix 때문에 다르다. 두 경우 모두 64자리 소문자 16진수다. 검증: head/worktree 불일치, 라인 이동, source/fallback domain 픽스처 단위 테스트.
- **AC-4** [실행] R4.2의 네 조건 각각에 대해 `location_valid=false`가 되고 inline 게시 계획에서 제외되며 요약에 `위치 미검증`으로 남는다: 존재하지 않는 파일, 라인 수를 초과하는 `line_start`, **라인 수를 초과하는 `line_end`**, **`line_start > line_end`인 역전**. 네 조건을 모두 만족하지 않는 finding만 `location_valid=true`가 된다. 고정 `head_sha` commit의 파일과 dirty worktree 내용이 다른 fixture에서도 판정은 commit 내용을 따라, `file`·두 line 값을 LLM 주장이나 현재 worktree가 아니라 고정 SHA에서 실측함을 단정한다. 검증: 네 무효 조건과 head/worktree 불일치 픽스처를 갖는 임시 git 저장소 단위 테스트.
- **AC-5** [실행] 고정된 `base_sha..head_sha`와 다른 diff 범위를 dirty worktree가 보이는 fixture에서도, 해당 두 SHA의 hunk 범위 밖 라인 finding은 `in_diff_range=false`가 되고 inline이 아니라 요약 항목으로 분류된다. 범위 안 라인은 `true`다. 검증: base/head 고정 diff와 worktree 불일치 단위 테스트.
- **AC-6** [실행] 같은 실행에 동일 `finding_id`가 둘 이상 있으면 하나로 병합되고, 대표 위치는 `(line_start, line_end)` 오름차순 첫 항목이며, 나머지 위치가 `additional_locations`에 모두 담긴다. 서로 다른 출처가 합쳐지면 `finding_provenance[finding_id]`가 reviewer ID의 정렬·중복 제거 배열이고 어느 출처도 빠지지 않으며, R6.5 입력의 상위 reviewer group별 `observations`와 연결된 `critiques`도 병합 전 개수와 내용을 보존한다. 게시 계획의 inline comment는 대표 위치에 정확히 하나이고 `full` tier 요약은 대표·추가 위치를 모두 나열한다. 검증: 양쪽 reviewer가 같은 ID를 낸 입력과 한쪽에 같은 ID가 중복된 입력의 병합→plan 단위 테스트.

### 게시 멱등성과 안전

- **AC-7** [실행] 쓰기가 필요한 최초 `apply`의 호출 기록은 요약 create/update 1건 → `event=COMMENT`인 단일 inline review 0~1건 → 열린 resolved thread별 resolve 순서이고, 각 성공 직후 `publish_stages`의 해당 완료 기록과 응답 ID가 저장된다. 앞 단계 실패 fixture에서는 뒤 단계 호출이 0건이다. 동일한 plan을 두 번 `apply`하면 두 번째 실행의 GitHub 쓰기 호출이 0건이고 종료 코드가 0이다. 검증: 정상 3단계 순서·단계별 실패·완료 상태·두 번째 apply를 대조하는 fake 클라이언트 단위 테스트.
- **AC-8** [실행] 기존 marker가 없는 최초 계획에서는 `new`·`persisting` finding ID가 요약의 각 lifecycle 목록에 나타나고, inline 가능한 `lifecycle.new` finding이 각각 정확히 한 번 단일 review의 comments 배열에 들어간다. 각 inline body의 끝은 정확한 `<!-- dual-review:finding:<finding_id> -->` marker이고 R7.19의 나머지 metadata index는 inline body에 중복되지 않는다. `inline_posted` 또는 `placement=summary_only`인 `persisting`은 새 comments 배열에 들어가지 않고, R7.13의 `inline_pending` 복구만 AC-79의 제한된 예외다. 2단계(inline 리뷰 생성)이 실패한 뒤 같은 로컬 상태로 재실행하면 기존 코멘트의 `finding_id` marker를 대조해 이미 게시된 finding을 제외하고 남은 `new`·`retry_inline`만 담은 단일 리뷰 호출이 1건 발생한다. 남는 항목이 없으면 호출이 0건이다. 검증: 최초 `new`/`persisting` 혼합 및 실패 후 부분 marker fake 클라이언트 단위 테스트.
- **AC-9** [실행] 1·2단계가 완료 기록된 뒤 3단계에서 실패한 상태로 재실행하면, 1·2단계 호출이 0건이고 3단계의 미해결 스레드만 처리된다. 검증: fake 클라이언트 단위 테스트.
- **AC-10** [실행] **커버리지 결손이 없는 실행**(R7.6a 결손 표 여덟 행이 모두 거짓: 프리플라이트 실패·모델 거부 없음, `excluded` 리뷰어 없음, 산출물 없는 종료 없음, **이전 record의 `SRC_AGENTS`에 이번 실행에서 성공한 agent가 하나 이상 있음**, R10.2(b) 범위 축소 없음, **`--base`로 인한 `changed_files` 축소 없음**, R3.9 후단의 실패 에이전트 없음, 이전 record의 각 `cat=c`에 대해 `S(c)`가 비어 있지 않음)이고 **R7.6a 단계 0의 ID 재대응에도 걸리지 않은** finding에 대해, R7.19 인덱스 복원이 `ok`이고 이전 활성 집합에는 있었으나 현재 리뷰에 없는 `finding_id`는 `resolved`로 분류된다. 연결된 열린 스레드가 있으면 계획에 요약의 "해소됨" 기재와 `resolveReviewThread` 호출이 포함되고, 요약 전용이면 이번 요약 기재만 포함되며, 어느 경우에도 스레드 답글 호출은 없다. 직전 lifecycle이 `resolved`이고 스레드가 이미 해결됐거나 없는 record는 활성 집합에서 빠져 재처리되지 않으며, 그 `finding_id`가 현재 결과에 다시 나타나면 `new`다. 검증: 열린 스레드·요약 전용·종결 이력·재발 네 fake 픽스처 단위 테스트.
- **AC-11** [실행] `apply` 직전 조회한 head SHA가 고정된 `head_sha`와 다르면 종료 코드가 0이 아니고 GitHub 쓰기 호출이 0건이다. 검증: fake 클라이언트 단위 테스트.
- **AC-12** [실행] `<!-- dual-review:summary -->` 마커가 없으면 그 마커를 정확히 하나 포함한 sticky 코멘트 생성 1건, 정확히 하나 있으면 해당 comment ID의 갱신 1건과 생성 0건이 계획된다. 두 경로를 적용한 뒤 이 스킬의 summary marker를 가진 코멘트는 PR당 정확히 하나다. 검증: 기존 marker 0개/1개 fake 응답의 plan·apply 호출 수와 최종 코멘트 집합 단위 테스트.
- **AC-13** [실행] fake 클라이언트가 수신한 모든 리뷰 생성 호출의 `event` 값이 `COMMENT`다. 추가로 계약 테스트가 `publish_findings.py` 소스를 읽어 문자열 `REQUEST_CHANGES`와 `APPROVE`의 출현 횟수가 각각 0임을 단정한다. 종료 코드가 아니라 카운트를 단정하는 이유는 `grep -c`가 매치 0건일 때 `0`을 출력하면서 종료 코드 1을 반환해 두 기준이 충돌하기 때문이다. 검증: 단위 테스트 + 계약 테스트.
- **AC-14** [실행] fake 클라이언트가 기록한 모든 `(kind, method, target)` 3튜플이 화이트리스트의 부분집합이고, `plan` 경로의 기록에는 쓰기 메서드 네 개의 3튜플이 하나도 없다. 검증: 단위 테스트가 화이트리스트를 상수로 두고 대조한다.
- **AC-15** [실행] `plan` 실행 경로에서 GitHub 쓰기 호출이 0건이고, `publish_findings.py`의 `plan` 진입점이 `apply` 진입점을 호출하지 않는다. 검증: fake 클라이언트 단위 테스트 + AST로 호출 그래프 확인.
- **AC-16** [실행] `--no-publish`로 실행하면 파이프라인 전체에서 GitHub 쓰기 호출이 0건이다. 검증: 단위 테스트.

### 리뷰 파이프라인

- **AC-17** [실행] R3.1 매핑 표의 각 신호에 대해 선택되는 에이전트 집합이 표와 일치하고, `code-simplifier`는 어떤 입력에서도 선택되지 않는다. 선택 결과와 유발 신호·매치 수가 상태에 기록된다. 복수 에이전트 fixture의 dispatch 기록에서는 선택된 모든 호출이 시작된 뒤 첫 결과를 await하므로 직렬 호출이 아니며, barrier fake에서 최대 동시 실행 수가 2 이상이다. 검증: 신호별 선택·상태 및 병렬 dispatch 단위 테스트.
- **AC-18** [실행] 1차 리뷰 프롬프트 구성 함수의 출력에 상대 리뷰어의 산출물 경로·내용이 포함되지 않고, CRITIQUE 이전 단계의 상태 조회가 상대 산출물을 반환하지 않는다. 검증: 단위 테스트.
- **AC-19** [실행] 각 산출 주체의 변환·스키마 위반은 원래 요청에 그 주체의 검증 오류만 덧붙인 입력으로 정확히 1회 재요청하며, 상대 reviewer나 다른 Claude 에이전트의 산출물은 재요청 입력에 없다. 2회째 실패에서 그 주체의 `agent_outcomes.result=schema_violation`과 attempts=2로 기록되고 3회째 재요청은 발생하지 않는다. Codex 주체이면 Codex reviewer가 `excluded`가 되고, Claude 에이전트 하나이면 다른 선택 Claude 에이전트의 성공 여부를 R3.5a로 집계하므로 그 하나만으로 Claude reviewer를 `excluded`로 만들지 않는다. 검증: Codex와 선택 Claude 에이전트 각각의 retry prompt capture·호출 횟수·집계 단위 테스트.
- **AC-20** [실행] 단일 리뷰 승인이 상태에 기록되지 않은 채로는 리뷰어 하나가 실패한 실행이 SYNTHESIS 단계로 전이하지 않는다. 검증: 단위 테스트.
- **AC-21** [실행] evidence는 `(path, line_start, line_end, normalized_quote)` 튜플로 비교되고 quote의 연속 공백·양끝 공백만 정규화된다. 같은 path/line과 공백만 다른 quote는 중복이고, path·두 line 중 하나 또는 정규화 quote가 다르면 새 근거다. 새 근거 수가 0인 라운드 뒤에는 다음 라운드가 실행되지 않고 종료 사유 `no_new_evidence`가 기록되며 라운드 수는 2를 초과하지 않는다. **첫 교차비평 라운드의 기준선 집합이 1차 리뷰 findings의 evidence 튜플을 포함해, 1차 리뷰가 이미 댄 근거만 되풀이한 반박에 대해 첫 라운드에서 `no_new_evidence`가 성립한다.** 검증: 튜플 각 필드·공백 변이, 1차 기준선, 0/양수 새 근거 단위 테스트.
- **AC-22** [실행] R5.4의 두 조건이 모두 참인 입력에서 `abstraction_drift`가 반환되고, 하나라도 거짓이면 반환되지 않는다. 현재·직전 채택 반박 수가 같은 경계(`current_critique_count == previous_critique_count`)에서는 out-of-scope evidence 비율이 0.5 이상이면 반환되고, 현재 수가 직전보다 작으면 반환되지 않는다. **직전 교차비평 라운드가 없는 첫 라운드 입력에서는 첫 조건이 참이어도 반환되지 않는다.** 검증: `>`·`==`·`<` 및 첫 라운드 단위 테스트.
- **AC-23** [실행] 종합자 입력 페이로드의 구조화 metadata에는 `source`·`finding_provenance`·`reviewer_aliases` 필드와 실제 reviewer·모델 식별자(`claude`, `codex`, `gpt-5.6`, `pr-review-toolkit`, 에이전트 이름 6종)가 없고, reviewer 식별값은 `reviewer-1`/`reviewer-2`뿐이다. 자유 텍스트 `body`·`recommendation`·`evidence`의 잔존 누출 가능성은 R6.4의 명시된 한계로 별도 취급한다. 같은 입력에서 비공개 상태의 `finding_provenance`에는 각 `finding_id`의 실제 reviewer ID 집합이, `reviewer_aliases`에는 실제 상위 group→alias 대응이 보존되고, 종합 결과와 재결합한 R7.19 record의 `src`는 alias가 아니라 `finding_provenance`의 실제 ID 배열과 일치한다. 검증: 종합자 payload와 두 private sidecar, R7.19 record를 함께 단정하는 단위 테스트.
- **AC-24** [실행] 셔플이 결정적이다: (a) 동일 입력과 동일 `head_sha`로 여러 번 실행하면 매번 같은 순서를 낸다, (b) `head_sha`가 다르면 셔플에 들어가는 **시드 재료가 다르다**. 서로 다른 `head_sha`가 항상 서로 다른 최종 순열을 낸다고 요구하지 않는다 — finding이 1건이면 순열이 하나뿐이고, 유한한 순열 집합에 모든 SHA를 단사로 대응시킬 수도 없다. 판정 대상은 시드 유도의 결정성이지 순열의 유일성이 아니다. 검증: 단위 테스트.
- **AC-25** [실행] 변경 파일 100개이면서 diff 20,000줄인 경계 입력은 규모 게이트 없이 진행하고, 파일 101개·diff 20,001줄인 두 초과 입력은 각각 정확한 계산값을 알린 뒤 사용자 결정 없이 다음 단계로 전이하지 않는다. 초과 시 선택지는 중단 또는 사용자가 명시한 경로 부분집합으로의 축소뿐이다. 축소를 택하면 실제 검토 경로 집합이 그 부분집합과 정확히 같고 묵시적으로 더 잘린 경로가 없으며, 축소 경로 집합과 제외 파일 수가 상태와 **`plan`이 생성한 요약 코멘트 본문**에 포함된다. 검증: 두 등호 경계·두 초과 경계·중단/축소 선택과 경로 집합 대조 단위 테스트.

### 계약과 배치

- **AC-26** [실행] `schemas/` 아래 네 개 스키마(`reviewer-output`, `critique`, `synthesis`, `publish-plan`) 전부의 루트가 `"type": "object"`이고, 각각 유효 픽스처는 통과하고 무효 픽스처는 실패한다. 특히 `publish-plan` 루트의 `additionalProperties`는 `false`이고 unknown root key 하나를 더한 계획은 실패한다. 검증: 스키마별 유효·무효 및 publish-plan unknown-key 단위 테스트.
- **AC-27** [실행] `codex exec`가 `schemas/reviewer-output.schema.json`을 `--output-schema`로 수락한다. 검증: 최소 프롬프트로 실제 `codex exec`를 1회 실행해 종료 코드 0과 스키마를 만족하는 결과 파일을 얻는다. 이 실행은 `--sandbox read-only`다. `codex` CLI 미설치·모델 거부·네트워크 실패로 실행 자체가 불가능하면 이 기준을 `blocked`로 기록하고 그 사실과 실패 출력을 리포트에 남긴다. 실행하지 못한 것을 통과로 기록하지 않는다.
- **AC-28** [실행] `SKILL.md` frontmatter가 R1.3의 일곱 필드를 모두 갖고, **파싱된 값이 `disable-model-invocation: true`(불리언 참), `model: "inherit"`, `effort: "high"`와 각각 일치하며**, `version` 값이 `MAJOR.MINOR.PATCH` 형식이고, `SKILL.md`가 참조하는 모든 상대 경로 파일이 실재하고, 다음 지시 문구가 모두 존재한다: R1.4의 네 플래그(`--pr`, `--base`, `--rounds`, `--no-publish`), R3.3의 Codex 프리플라이트 단계와 실패 시 단일 리뷰 승인 경로, R3.7의 단일 리뷰 승인 게이트, R7.2의 게시 승인 게이트. 검증: 계약 테스트.
- **AC-29** [실행] 스킬 디렉터리 전체에서 `--full-auto`, `--yolo`, `--skip-git-repo-check` 문자열이 0건이고, `gpt-5.6-terra`와 `model_reasoning_effort="high"`가 Codex 호출 계약 문서에 존재한다. 검증: `grep -REn -- '--full-auto|--yolo|--skip-git-repo-check' dot_claude/skills/dual-review/` 매치 0건 + 계약 테스트.
- **AC-30** [실행] 두 스크립트가 import하는 모든 최상위 모듈이 **Python 표준 라이브러리이거나 같은 `scripts/` 디렉터리의 형제 모듈**이다. 외부 패키지 import는 0건이다. 검증: `ast`로 import를 추출해 `sys.stdlib_module_names` ∪ {`scripts/` 아래 `.py` 파일의 스템}과 대조하는 단위 테스트. 형제 모듈을 허용하는 이유는 선례인 `quality_state.py`가 `from validate_review import validate_review`로 같은 패턴을 쓰기 때문이며, R8.3이 금지하는 것은 외부 패키지 추가이지 내부 모듈 분리가 아니다.
- **AC-31** [실행] 두 스크립트 소스에 `GH_TOKEN`, `GITHUB_TOKEN`, `Authorization` 문자열이 등장하지 않는다. 검증: 계약 테스트.
- **AC-32** [실행] INTAKE가 대상 저장소 루트에서 `git check-ignore -- .claude/dual-review-state/<run_id>/`를 호출하고 런타임 파일 생성·수정 대상을 그 디렉터리 아래로만 제한한다. 경로가 무시되지 않으면 경고를 출력한 뒤 다음 INTAKE 단계로 계속하고, 무시되면 경고 없이 계속한다. 두 경우 모두 실행 전후 `.gitignore`의 바이트가 같고 스킬이 `.gitignore` 쓰기를 시도한 기록이 0건이다. 검증: ignored/unignored 임시 git 저장소와 filesystem write-spy 단위 테스트.
- **AC-33** [실행] `dot_claude/skills/dual-review/` 아래에 R1.2가 규정한 다섯 구성이 모두 존재하고(`SKILL.md` 파일, `references/`·`schemas/`·`scripts/`·`tests/` 디렉터리), `templates/`와 `evals/` 디렉터리는 없다. 검증: 계약 테스트.
- **AC-34** [실행] 전체 결정적 테스트가 통과한다. 검증: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'` 종료 코드 0.
- **AC-35** [실행] `chezmoi --source "$PWD" target-path dot_claude/skills/dual-review/SKILL.md`가 종료 코드 0이고 `~/.claude/skills/dual-review/SKILL.md`의 절대 경로를 출력한다. 검증: 판정 명령 CHEZMOI. 이 워크트리를 명시하지 않은 `chezmoi diff`는 main checkout을 source로 볼 수 있어 판정에 쓰지 않는다.
- **AC-36** [실행] 이 저장소 루트 `.gitignore`에 `.claude/dual-review-state/`가 정확한 한 줄로 존재하고 `git check-ignore -v .claude/dual-review-state/`가 종료 코드 0이며 출력의 source가 그 `.gitignore`, match pattern이 같은 정확한 문자열이다. 검증: 판정 명령 IGNORE의 source·pattern·종료 코드 대조.
- **AC-37** [실행] `plan`이 실제 GitHub 응답으로 동작한다. 검증: 검증 시점에 `gh pr list --state open --limit 1 --json number`로 조회한 열린 PR을 대상으로 `publish_findings.py plan`을 빈 finding 집합으로 실행해 종료 코드 0을 얻고, 산출된 `plan.json`이 `schemas/publish-plan.schema.json`을 만족하며, 기록된 3튜플에 쓰기 메서드가 0건임을 확인한다. 열린 PR이 없으면 이 기준을 `not applicable`로 기록하고 그 사실을 리포트에 남긴다.
- **AC-38** [실행] `docs/dual-review-maintenance.md`가 존재하고 R9.1의 네 절(갱신 신호 추적, 의존 CLI·플러그인 점검, 결정적 테스트 실행 명령, 버전 정책)을 모두 포함하며, "버전 정책" 절이 MAJOR·MINOR·PATCH 세 자리 각각에 어떤 변경이 대응하는지 기술한다. 검증: 계약 테스트.
- **AC-39** [실행] `plan`이 생성한 요약 코멘트 본문의 첫 줄이 `AI-generated review — Claude + Codex — reviewed commit: ` 로 시작하고 그 뒤에 상태의 `head_sha`가 온다. 검증: 단위 테스트.
- **AC-40** [실행] `references/synthesis-contract.md`가 R6.4의 두 잔존 한계(텍스트 본문을 통한 출처 누출, 종합자 자기선호 편향)를 모두 명시하고, 종합 결과가 advisory이며 종합자에게 merge 차단·`APPROVE`·`REQUEST_CHANGES` 결정 권한이 없다고 규정한다. 실제 사용자 리포트의 표시는 AC-82가 별도로 판정하며 이 문서 검사로 대체하지 않는다. 검증: 계약 테스트.
- **AC-41** [실행] 각 상위 reviewer group의 critique 프롬프트에는 상대 group의 모든 finding과 `finding_id`가 들어가고 자기 group의 finding은 상대 입력으로 가장해 넣지 않으며, 실제 reviewer·모델 이름을 응답 필드로 요구하지 않는다. `schemas/critique.schema.json`은 각 반박 항목에 `target_finding_id`·`stance`·`evidence`를 required로 요구하고, `stance`를 `supports`/`challenges` enum으로, `evidence`를 `minItems: 1`로 강제한다. 빈 evidence나 현재 finding 집합에 없는 target ID는 채택·새 근거 계산·R6.5 `critiques` 어디에도 반영되지 않는다. 검증: 양방향 prompt capture, 유효·필드별 무효·unknown target 픽스처 단위 테스트.
- **AC-42** [실행] `schemas/synthesis.schema.json`이 각 finding 판정에 다섯 축(`truth`, `introduced_by_pr`, `location_validity`, `evidence`, `actionability`)을 모두 `required`로 강제하고, 하나라도 빠진 픽스처는 검증에 실패한다. 검증: 유효·무효 픽스처 단위 테스트.
- **AC-43** [실행] `schemas/synthesis.schema.json`이 각 finding의 분류를 `agreed`/`disputed`/`unresolved`/`single_source` 네 값의 `enum`으로 강제한다. `unresolved`이면 다섯 축 중 하나를 가리키는 non-empty `unresolved_reason`이 필수이고, 다른 분류에는 그 필드가 없어야 한다. enum 밖 분류·근거 없는 `unresolved`·비-`unresolved`의 잔여 reason 픽스처는 실패한다. 검증: 유효·무효 픽스처 단위 테스트.
- **AC-44** [실행] `schemas/reviewer-output.schema.json`에 `uniqueItems` 키가 없고, 어떤 `pattern` 값에도 정규식 lookaround(`(?=`, `(?!`, `(?<=`, `(?<!`)가 없다. 저장소 상대 경로 pattern은 정확히 `^([^/~.].*|\.[^/.].*)$`이고 D-15의 9개 경로 fixture에서 허용/거부 결과가 선행 lookaround 형식과 같다. 이 금지는 API 전송 스키마에만 적용하므로 로컬 전용 세 스키마의 `uniqueItems` 존재 여부로 실패시키지 않는다. 검증: reviewer-output 스키마 재귀 순회, exact pattern과 9경로 동등성 계약 테스트.
- **AC-45** [실행] 선택 가능한 Claude 에이전트 다섯 key 각각에 대해 호출 프롬프트를 구성하는 함수의 출력이, 그 에이전트 자체 `Output Format` 지시보다 스키마 계약이 우선한다는 선언 문구를 포함하고 그 문구가 `references/reviewer-contract.md`의 단일 상수와 일치한다. 검증: 다섯 agent별 prompt capture 단위 테스트 + 계약 테스트.
- **AC-46** [실행] 생성된 모든 코멘트 원소에서 **`line`이 finding의 `line_end`와 같고 `side`가 `"RIGHT"`이며 `body` 끝이 정확한 finding marker다.** `line_start == line_end`인 finding의 원소에는 `start_line`·`start_side`가 없고, `line_start < line_end`이면서 두 라인이 같은 hunk 안인 finding의 원소에는 `start_line == line_start`와 `start_side == "RIGHT"`가 있으며, 두 라인이 서로 다른 hunk에 있으면 두 start 필드가 모두 없고 축소 사실이 상태에 기록된다. 어떤 원소에도 `position`·`original_position` 키가 없다. 검증: 단일 라인·같은 hunk 여러 줄·cross-hunk 단위 테스트와 exact key/body 단정.
- **AC-47** [실행] 기존 리뷰 코멘트 조회 결과로부터 `id`·`node_id`·`pull_request_review_id`·`path`·`line`·`original_line`이 상태에 기록되고, `pull_request_review_id`로 연결된 review의 `id`·`commit_id`·`state`, 인덱스에서 복원한 `id`·`cat`·`src`·`path`·`line`·`placement`·`fp`·`run`·`lifecycle`, `history_restore.status`·실패 사유와 R7.17의 `delivery_states`도 상태에 기록된다. 검증: 두 placement와 marker 유무를 갖는 fake 클라이언트 단위 테스트.
- **AC-48** [실행] Codex 리뷰 명령 구성 함수의 argv가 `--sandbox read-only`, `--ephemeral`, `--model gpt-5.6-terra`, `-c model_reasoning_effort="high"`, `--output-schema <reviewer-output schema>`, `--output-last-message <주체별 경로>`, `--json`을 각각 정확히 한 번 포함한다. 계약 문서도 같은 값을 가지며, `--sandbox`의 다른 값(`workspace-write`, `danger-full-access` 등)은 스킬 디렉터리 어디에도 등장하지 않는다. 검증: argv capture와 문서/구성 함수 exact-value 계약 테스트.
- **AC-49** [실행] 게시 이력 목록 조회 메서드 넷이 전체 페이지를 순회한다. 2페이지에 걸친 응답을 반환하는 fake 클라이언트에서, **2페이지째에만 inline `finding_id` 마커·요약 인덱스·연결 review·thread가 있는 finding도 모두 복원되고 `persisting`으로 분류되어 재게시되지 않으며**, 같은 조건에서 `resolved` 판정도 오분류되지 않는다. 네 메서드 중 하나라도 순회 중 오류가 나면 부분 목록을 반환하지 않고 예외가 전파된다. 검증: 메서드별 다중 페이지 fake 클라이언트 단위 테스트.
- **AC-50** [실행] R6.5의 relation과 비-`unresolved` 분류가 `bilateral→agreed`, `unilateral→single_source`, `contested→disputed`로 정확히 대응하고, 다른 조합은 `review_state.py`의 종합 결과 검증에서 거부된다. `--rounds 0` 입력에는 accepted challenge가 없어 `contested`·`disputed`가 없고, 단일 리뷰어 실행에는 `bilateral`·`agreed`가 없다. `unresolved`는 relation과 무관하게 허용하되 유효한 `unresolved_reason`이 있어야 한다. 검증: relation 세 값의 올바른/잘못된 분류 행렬, rounds 0, 단일 리뷰어, unresolved reason 단위 테스트.
- **AC-51** [실행] INTAKE 후 상태에 `repo`·`pr_number`·`base_sha`·`head_sha`·`changed_files` 다섯 값이 모두 기록된다. 그 뒤 branch와 dirty worktree를 다른 commit·파일 집합으로 바꾼 fixture에서도 REVIEW·CRITIQUE·SYNTHESIS·REPORT·PLAN의 캡처 입력과 게시 계획은 상태의 원래 대상 값만 사용하고 새 branch 값으로 바뀌지 않는다. fake 호출 기록에는 허용된 R7.19의 이력 조회 네 메서드와 R7.11의 head SHA 재확인 1회 외의 base·변경 파일·대상 PR 메타데이터 재조회가 0건이다. 검증: INTAKE 뒤 branch/worktree 변이와 전 단계 입력 capture, fake 클라이언트 호출 기록 단위 테스트.
- **AC-52** [실행] `schemas/publish-plan.schema.json`을 만족하지 않는 계획 파일로 `apply`를 실행하면 종료 코드가 0이 아니고 GitHub 쓰기 호출이 0건이다. 검증: fake 클라이언트 단위 테스트.
- **AC-53** [실행] `--rounds 0`으로 실행하면 교차비평 라운드가 0회이고 critique 산출물이 생성되지 않으며, 상태의 `critique_rounds`가 빈 목록이다. 검증: 단위 테스트.
- **AC-54** [실행] 요청 ref와 PR 실제 base가 서로 다른 commit을 가리키는 fixture에서 `--base <ref>`를 주면 상태의 `base_sha`는 요청 ref를 해석한 SHA이고, R4.3 판정은 PR 실제 base가 아니라 그 `base_sha..head_sha` hunk를 사용한다. **요청 ref가 PR 실제 base보다 head 쪽에 가까워 이전 게시 finding의 `path`가 `changed_files`에서 빠진 fixture에서는 그 record가 `resolved`가 아니라 reason=`base_narrowed`인 `not_re_reviewed`이고 `resolveReviewThread` 호출이 0건이다.** 동시에 (a) 상태에 base 불일치 사실과 `requested_base_ref`·`actual_base_sha`가 기록되고, (b) `plan.base_mismatch`의 `requested_ref`·`actual_base_sha`가 같은 값이며 `inline_review.skip`이 반드시 참이고, (c) 모든 finding이 `summary_only_findings`로 들어가며, (d) 요약 본문에 base 불일치 사실과 두 ref가 포함된다. `--base`를 생략하거나 실제 base와 같은 ref를 주면 `base_mismatch`가 null이고 PR 실제 base SHA를 diff 기준으로 쓰는 정상 경로다. 검증: 요청/실제 base의 hunk가 다른 임시 git 저장소와 생략·동일·불일치 세 경로 단위 테스트.
- **AC-55** [실행] `--pr`가 없을 때 `git branch --show-current`의 출력으로 `list_open_prs(repo, head_ref=<현재 브랜치>, limit=2)`가 정확히 1회 호출되고, 그 구현 argv는 `gh pr list --repo <repo> --state open --head <head_ref> --limit 2 --json number,headRefName,headRefOid,baseRefName,baseRefOid,url`와 정확히 같다. 결과 1건이면 그 번호로 `get_pr_meta`를 호출해 대상으로 삼는다. 결과가 0건이거나 limit에 찬 2건(2건 이상 존재)이면 상태를 만들지 않고 종료 코드 != 0으로 중단하며 `--pr` 지정을 안내한다. 빈 현재 브랜치명에서는 두 GitHub 메서드 모두 0회다. 전역 `list_open_prs(repo, head_ref=null, ...)`로 현재 브랜치 PR을 추측하지 않는다. 검증: argv capture와 fake 클라이언트 단위 테스트(1건/0건/2건/detached HEAD 네 경우와 호출 인자 단정).
- **AC-56** [실행] `abstraction_drift` 신호가 참이면 사용자 출력에 신호의 두 판정값과 라운드 종료 제안이 나타나고, 사용자 결정이 상태에 기록되기 전에는 다음 교차비평 라운드도 SYNTHESIS 전이도 일어나지 않는다. 검증: 사용자 출력 capture와 상태 전이 단위 테스트.
- **AC-57** [실행] R10.1 임계값 초과 시 사용자가 중단을 선택하면 상태가 중단으로 기록되고 이후 단계가 실행되지 않으며 GitHub 쓰기 호출이 0건이다. 검증: 단위 테스트.
- **AC-58** [실행] `viewerCanResolve`가 거짓인 스레드에 대해 `resolveReviewThread` 호출이 발생하지 않고, 건너뛴 스레드 ID와 사유가 상태에 기록되며 요약 본문에 포함된다. 참인 스레드는 정상 호출된다. 검증: fake 클라이언트 단위 테스트.
- **AC-59** [실행] 양쪽 리뷰어가 모두 실패한 실행에서는 단일 리뷰 승인을 묻지 않고 중단하며 GitHub 쓰기 호출이 0건이다. 검증: 단위 테스트.
- **AC-60** [실행] `references/reviewer-contract.md`에 기록된 상수가 스크립트가 실제로 쓰는 값과 일치한다: `CODE_EXT` 집합, 확장자별 주석 토큰 표, `comment-analyzer` 매치 임계 3, 규모 임계값 파일 100개·diff 20,000줄, R3.10의 `AGENT_CATEGORY_MAP_V1`. 마지막 상수는 다섯 agent key가 정확히 일치하고 category 배열도 canonical 순서까지 같으며 합집합이 reviewer-output의 일곱 category와 같다. 상태의 `agent_category_map`은 그 상수와 exact deep equality이고, 중복 `correctness` 담당자 일부 성공/일부 실패 및 전원 실패 픽스처의 `category_coverage`가 R3.10의 집합식과 일치한다. map 불일치·category 누락·선택 agent 상태 누락 각각에서는 `plan`이 비정상 종료하고 lifecycle 결과와 GitHub 쓰기가 0건이다. 검증: 계약 테스트가 문서 canonical JSON·스크립트 상수·생성 상태를 파싱해 대조하고 세 손상 상태를 실행한다.
- **AC-61** [실행] 새 실행의 event spy는 PR 조회로 `repo`·`pr_number`·실제/요청 base SHA·full `head_sha`·변경 파일을 모두 얻은 뒤 `run_id`를 계산하고, 그 뒤에만 상태 디렉터리를 열거나 만들고 최초 `state.json`을 쓰는 순서를 단정한다. 조회 실패에서는 상태 디렉터리 open/create/write가 0건이다. 같은 `repo`·`pr_number`·full `head_sha` 입력에 대해 `run_id`가 재현되고, head SHA의 앞 12자가 다르면 `run_id`도 다르다. 기존 상태 디렉터리가 없으면 새로 만들고, 있으면 새 호출의 full `head_sha`·`requested_base_ref`·새로 해석한 `base_sha`·`actual_base_sha`·유효 `rounds`가 상태의 고정값과 모두 같은 경우에만 읽어 R7.13(a)의 완료 기록을 이어간다. 하나라도 다르면 종료 코드 != 0이고 충돌 필드와 기존값·새 값이 출력되며, 상태 파일은 바뀌지 않고 이후 단계와 GitHub 쓰기 호출은 0건이다. 서로 다른 full SHA의 앞 12자가 같은 fixture는 candidate `run_id`가 같더라도 `run_id_prefix_collision`으로 이 안전 중단을 따른다. 검증: INTAKE event 순서/조회 실패, 정상 재개와 완료 단계 skip, full SHA 12자-prefix 충돌, `--base` 문자열 충돌, 같은 ref 문자열의 target SHA 이동, PR 실제 base SHA 이동, `--rounds` 충돌 각각의 단위 테스트.
- **AC-62** [실행] R7.6a의 여덟 결손 경로 각각에 대해, R7.19 인덱스에서 복원한 이전 finding이 현재 결과에 없으면 `resolved`가 아니라 `not_re_reviewed`로 분류되고, 그 finding의 스레드에 `resolveReviewThread` 호출이 발생하지 않으며, 요약 본문의 "재검토되지 않음" 목록과 상태의 `coverage_gap_evidence`에 최초 일치 사유와 판정 필드·값이 나타난다. 에이전트 일부 실패 경로는 `code-reviewer→security`, `pr-test-analyzer→tests`, `comment-analyzer→comments`, `silent-failure-hunter→error-handling`, `type-design-analyzer→types`의 다섯 픽스처에서 각각 `agent_category_uncovered`가 되어 이 결과를 만족해야 한다. 담당 에이전트 미선택 경로는 선택 신호가 없는 `tests`·`comments`·`error-handling`·`types` 픽스처에서 각각 `agent_category_unselected`가 된다. 중복 `correctness`는 선택된 담당자 중 일부가 실패하고 하나가 성공하면 uncovered 사유가 생기지 않으며, 선택된 담당자 전원이 실패하면 생긴다. **출처 에이전트 미성공 경로는 직전 실행에서 `silent-failure-hunter`가 낸 `cat=correctness` record에 대해 이번 실행에서 그 에이전트가 선택되지 않고 `code-reviewer`만 성공한 픽스처에서 `src_agent_unavailable`이 되어야 하며, 7·8행이 모두 거짓인데도 이 결과가 나와야 한다. `--base` 축소 경로는 이전 record의 `path`가 요청 base로 계산한 `changed_files`에서 빠지고 사용자 범위 축소는 없는 픽스처에서 `base_narrowed`가 된다.** 여덟 조건이 모두 해당하지 않고 인덱스 복원이 `ok`일 때만 `resolved`가 된다. 인덱스가 없거나 version·base64·JSON·필수 필드 중 하나가 잘못된 전체 복원 실패 픽스처에서는 `resolved`가 0건이고, inline 마커로 식별 가능하면서 현재 결과에는 없는 이전 finding 전부가 reason=`history_unavailable`인 `not_re_reviewed`이며 `resolveReviewThread` 호출이 0건이다. 현재 결과에도 같은 ID가 있는 finding은 `persisting`이다. 검증: 실제 인덱스 디코드와 실제 `AGENT_CATEGORY_MAP_V1` 상태 계산부터 시작하는 결손·중복 담당·복원 실패 fake 클라이언트 단위 테스트.
- **AC-63** [실행] R3.7의 `preflight_unavailable`·`schema_excluded`·`no_output` 각각에서 그 failure_type이 상태에 정확히 기록되고, 단일 리뷰 승인이 기록되기 전에는 CRITIQUE·SYNTHESIS로 전이하지 않는다. 특히 R3.5a의 `excluded` 두 경로 모두 승인 게이트를 발동한다. 검증: 세 유형과 mixed subject failure precedence의 단위 테스트.
- **AC-64** [실행] R7.19 형식으로 만든 요약 인덱스를 **로컬 상태 루트가 비어 있고 git notes가 없는** 다음 head SHA 실행의 `list_issue_comments` 결과로 돌려주면, 디코드 후 `id`·`cat`·`src`·`path`·`line`·`placement`·`fp`·`run`·`lifecycle` 값과 finding 집합이 원본과 정확히 같고 `history_restore.status == "ok"`다. `placement=inline`이면 marker ID·REST `path`·REST의 non-null `line` 또는 `original_line`·`pull_request_review_id`가 같은 인덱스 record·review·thread에 연결돼 `inline_posted`이고, `placement=summary_only`이면 marker 없이 `summary_only`다. fake subprocess 기록에 `git notes` 호출과 이전 `run_id` 디렉터리 탐색이 0건이다. 검증: 두 placement와 현재 line 일치, 이동 후 original_line 일치, outdated line=null 경우의 생성 → GitHub fake 응답 → 로컬 이력 없는 복원 왕복 단위 테스트.
- **AC-65** [실행] (a) 인덱스 블록 0개/2개 이상, 지원하지 않는 version, 잘못된 base64·JSON·루트 형태, `placement`를 포함한 필수 key/값 결손, 아홉 key 밖 unknown key, 중복 `id` record는 전체 복원 실패다. record 값 검증은 `id`의 12자리 소문자 hex, 일곱 `cat`, canonical 순서의 non-empty·unique `src`와 허용 reviewer ID, 탈출 없는 상대 `path`, 1 이상 `line`, 두 `placement`, 64자리 소문자 hex `fp`, R2.5 형식 `run`, 네 `lifecycle`을 각각 잘못 만든 fixture로 단정한다. 각 실패에서 `history_restore.status != "ok"`, `resolved` 0건, `resolveReviewThread` 0건이고 부분 복원 집합을 반환하지 않는다. inline marker로 식별 가능하면서 현재 결과에는 없는 이전 finding은 reason=`history_unavailable`인 `not_re_reviewed`이고 현재에도 같은 ID가 있으면 `persisting`이다. (b) 유효 인덱스의 `placement=inline` record에 같은 ID marker가 있지만 REST path·REST line/original_line·연결 review 중 하나가 불일치하거나 marker가 중복이면 `history_restore.status == "ok"`를 유지하고 그 record만 `linkage_invalid`로 격리해 inline·resolve를 0건으로 만든다. 현재 결과에 같은 ID가 있으면 lifecycle은 `persisting`, 없으면 reason=`history_unavailable`인 `not_re_reviewed`이며, 함께 입력한 정상 record는 정상 lifecycle을 산출한다. marker 0개인 `placement=inline`은 이 불일치가 아니라 AC-79의 `inline_pending`이다. (c) 인덱스에 없는 고아 marker는 연결 스레드가 해결됐거나 없으면 종결 이력으로 무시하고, 열려 있으면 그 marker만 `history_unavailable`로 보존한다. `dual-review` marker가 전혀 없는 사람/타 봇 코멘트는 세 집합 어디에도 들어가지 않는다. 세 경우 모두 다른 정상 record를 전체 실패로 끌어내리지 않는다. 검증: 전체 index/필드 실패 유형별, record 연결 불일치·중복별, 고아 marker의 해결/없음/열림별, unmarked comment fake 클라이언트 단위 테스트.
- **AC-66** [실행] 인덱스 payload가 표준 base64 정규식 `^[A-Za-z0-9+/]+={0,2}$`에 일치하고 payload 자체에는 `-`가 0개이며, 디코드하면 UTF-8 JSON object가 된다. 같은 record 집합은 입력 순서와 무관하게 같은 payload를 만든다. 검증: 문자 `+`·`/`·padding `=`을 실제로 만드는 픽스처와 순서 변이 단위 테스트.
- **AC-67** [실행] `in_diff_range=false` 또는 R2.1a base 불일치로 inline에서 요약으로 강등된 finding은 `placement=summary_only`로 인덱스에 실린다. review comment가 전혀 없어도 `summary_only`로 복원되고, 다음 실행에 같은 `id`가 있으면 `persisting`으로 분류되어 `inline_pending`으로 오인되지 않으며 신규 inline·resolve 호출이 0건이다. 검증: 두 강등 사유별 요약 전용 finding 왕복 fake 클라이언트 단위 테스트.
- **AC-68** [실행] 여덟 결손 경로 테스트는 분류 함수에 `path`·`cat`·`src`나 agent-category 매핑을 직접 주입하지 않고 R7.19의 인코딩된 이전 요약, GitHub comment/review/thread 응답, `review_state.py`가 `AGENT_CATEGORY_MAP_V1`에서 만든 현재 상태만 입력으로 사용한다. 에이전트 일부 실패는 다섯 에이전트 각각의 고유 책임 category와 `correctness` 중복 담당의 일부 성공/전원 실패를 모두 거치고, 담당 에이전트 미선택은 실제 R3.1 신호 계산 결과 `S(c)=∅`인 네 optional category를 거친다. **출처 에이전트 미성공은 인덱스에서 디코드한 `src`와 실제 `agent_outcomes`만으로 판정하고 fixture가 결과를 직접 주입하지 않으며, `--base` 축소는 실제 두 base로 계산한 `changed_files` 차이만 입력으로 쓴다.** 각각 디코드된 `cat`과 상태의 `category_coverage`가 `coverage_gap_evidence`로 이어지고 AC-62의 `not_re_reviewed`·resolve 0건 단정이 성립한다. 검증: 여덟 결손 경로와 에이전트별·중복 담당별·미선택 category별 게시 이력 복원 통합 단위 테스트.
- **AC-69** [실행] 같은 raw reviewer-output·critique 입력을 R7.5 병합과 R6.5 변환에 통과시키면 각 synthesis item의 key가 정확히 `finding_id`·`finding`·`source_count`·`observations`·`critiques`·`relation`이고, 각 observation의 key는 정확히 `reviewer`·`claims`이며 `source_count == observations의 고유 reviewer 수`, alias와 중첩 claims/critique 배열 정렬, relation 계산이 R6.5와 일치한다. 병합 전 양쪽의 원 주장, 같은 Claude group 안의 서로 다른 agent 주장, accepted critique는 완전히 같은 claim 외에는 빠지지 않으며 actual reviewer ID는 payload metadata에 없고 private `finding_provenance`·`reviewer_aliases`에만 있다. 검증: 같은 ID의 양쪽 주장, 한쪽 주장, 지지, 한 방향 반박, 양방향 반박, 여러 Claude 에이전트 중복의 변환 단위 테스트 + 중첩 닫힌 key 계약 테스트.
- **AC-70** [실행] raw 입력부터 생성한 **같은 `finding_id`** 세 픽스처가 다음 결과로 이어진다: 양쪽이 독립 제기하고 accepted challenge가 없으면 `relation=bilateral`·`classification=agreed`, 한쪽만 제기하고 상대 입장이 없으면 `relation=unilateral`·`classification=single_source`, 양쪽이 서로 근거 있는 `challenges`를 내면 `relation=contested`·`classification=disputed`. 각 fixture에서 다른 두 비-`unresolved` 분류를 넣은 synthesis 결과는 검증에 실패한다. 별도 근거 부족 fixture의 `unresolved`는 유효한 `unresolved_reason`이 있을 때만 통과한다. 검증: raw reviewer-output → ID 병합 → critique 연결 → 익명화 → synthesis 결과 검증의 end-to-end 단위 테스트.
- **AC-71** [실행] **인덱스-only 이어받기 record가 섞인 fixture에서 `compact` 본문은 현재 실행 finding에는 title을 싣고, 이어받은 `resolved`·`not_re_reviewed`에는 title 없이 ID·category·path:line과 lifecycle reason만 싣는다. 그 record에 대해 빈 title 문자열이나 지어낸 title이 본문에 나타나지 않으며, 같은 입력을 두 번 렌더링하면 바이트 수가 동일하다.** 또한 `SUMMARY_BODY_MAX_BYTES`가 `references/publish-contract.md`와 `publish_findings.py`에서 정확히 49,152로 일치하고, body 크기는 전체 UTF-8 바이트로 계산된다. 정확히 49,152바이트인 `full` body는 허용되고, `full`이 49,153바이트지만 `compact`가 상한 이하인 fixture는 `compact`, `compact`도 초과하지만 `minimal`이 상한 이하인 fixture는 `minimal`을 선택한다. 두 축약 tier 모두 네 lifecycle의 모든 ID, 모든 `not_re_reviewed` reason, 필수 경고와 완전한 단일 v1 인덱스를 보존하고 최종 body는 상한 이하다. 인덱스 블록만 49,153바이트인 fixture는 `summary_index_oversize`, 인덱스는 상한 이하지만 `minimal` 전체가 49,153바이트인 fixture는 `summary_body_oversize`로 `plan`이 종료 코드 != 0이며 적용 가능한 계획과 GitHub 쓰기가 0건이다. 상한 초과 body를 넣은 계획은 `apply`도 첫 쓰기 전에 거부한다. 검증: 정확한 UTF-8 filler를 쓰는 경계·tier·불가분 인덱스·apply 재검증 fake 클라이언트 단위 테스트 + 상수 계약 테스트.
- **AC-72** [실행] `finding_id` 생성기는 모든 출력이 `^[0-9a-f]{12}$`에 일치하고, 정규화된 입력 바이트 `src/app.py\0correctness\0null dereference`의 결과가 전체 SHA-256 `dc9b779e5fab915698ac406ecdf89843b5bc46c76d70384ced5e1c247877d62e`의 앞 12자인 `dc9b779e5fab`과 정확히 같다. 검증: 고정 known-answer 단위 테스트.
- **AC-73** [실행] INTAKE 프리플라이트 명령이 `--model gpt-5.6-terra`, `--sandbox read-only`, `-c model_reasoning_effort="low"`와 개행 없는 한 줄 프롬프트를 정확히 사용한다. 프리플라이트 실패·모델 거부 fixture에서는 다른 모델·effort·sandbox로 재호출한 횟수가 0이고, 사용자 출력에 실패 사실·`preflight_unavailable`·단일 리뷰 계속 여부가 나타나며, 상태에 실패 유형을 기록한 뒤 승인 전에는 CRITIQUE·SYNTHESIS로 전이하지 않는다. 검증: 명령 argv·프롬프트·사용자 출력 capture 및 실패 경로 단위 테스트 + 계약 테스트.
- **AC-74** [실행] `--rounds`를 생략한 정상 양쪽 리뷰 실행은 상태의 `rounds=1`이고 교차비평을 정확히 1라운드만 요청한다. 명시한 `--rounds 0`·`1`·`2`는 각각 상태에 같은 정수로 기록되고 교차비평을 정확히 0·1·2회 요청한다(`0`의 상세 동작은 AC-53과 동일). 검증: 기본값 생략·0·1·2 argv 파싱, 상태 값 및 호출 횟수 단위 테스트.
- **AC-75** [실행] 유효한 이전 v1 record를 현재 finding과 대조하면 `history_diagnostics.source_run_id`·`run_relation`과 `fingerprint_relation`의 `same_anchor`·`anchor_moved`·`anchor_changed`·`not_comparable` 네 경계가 R7.21의 식대로 기록된다. 같은 입력에서 이전 record의 `run`만 형식상 유효한 다른 값으로 바꾸면 `finding_id`, lifecycle 네 집합, inline comments, summary tier, thread resolutions와 GitHub 쓰기 3튜플은 변하지 않는다. 검증: 진단 관계별 및 fp/run-only 변이 fake 클라이언트 단위 테스트.
- **AC-76** [실행] 동일 finding의 4회 실행 왕복을 fake GitHub로 수행한다: run1은 `new`를 inline과 인덱스에 게시하고, run2는 finding 부재를 `resolved`로 분류해 해결 전 record를 인덱스에 싣고 열린 스레드를 resolve하며, run3은 해결된 `resolved` record를 활성 집합에서 제외해 다음 인덱스에서 떨어뜨리고, run4는 인덱스에 없는 기존 marker를 해결된 고아 스레드로 무시한다. 해소 run2와 그 뒤 두 후속 실행 run3·run4의 3세대 구간 모두 `history_restore.status == "ok"`이고, `resolved`는 run2에 정확히 1건, run3·run4의 resolve 호출은 0건이며 정상인 다른 record의 lifecycle은 영향을 받지 않는다. 검증: new → resolved → 종결 record 탈락 → 고아 marker의 4-run round-trip 단위 테스트.
- **AC-77** [실행] R3.1 선택 신호가 없어 optional 담당자가 선택되지 않은 `tests`·`comments`·`error-handling`·`types` 각각에서 `S(c)=∅`, `agent_category_unselected(c)=true`, `agent_category_uncovered(c)=false`다. 그 category의 이전 인덱스 finding이 현재 결과에 없으면 reason=`agent_category_unselected`인 `not_re_reviewed`이고 `resolved`·`resolveReviewThread`는 0건이다. 선택 담당자가 존재하는 category에서는 이 reason이 생기지 않는다. 검증: 실제 선택 함수→category coverage→인덱스 복원→lifecycle 계획 통합 단위 테스트.
- **AC-78** [실행] Codex와 선택된 Claude 에이전트 각각의 산출물이 합치기 전에 주체별로 reviewer-output 변환·검증된다. Codex `--output-last-message`는 trim한 전체가 단일 JSON object일 때만 통과한다. Claude 응답은 trim한 raw JSON object 또는 trim한 전체가 정확히 하나의 소문자 `json` fenced object인 경우만 통과하고, fence 밖 비공백 문자·JSON block 0개/복수·non-object·schema-invalid 응답은 해당 주체의 변환/검증 실패다. 유효 finding 0건은 `success`, 호출 오류·시간 초과·2회 변환/스키마 위반·무산출은 각각 `call_error`·`timeout`·`schema_violation`·`empty_output`으로 `agent_outcomes`에 기록된다. 실패 주체의 finding은 다른 에이전트 응답이나 별도 LLM 보정으로 채워지지 않고 보정 호출 수가 0건이다. 선택 Claude 에이전트 하나가 실패하고 하나 이상 성공하면 Claude reviewer는 `excluded`가 아니고 R3.9의 일부 실패 경로이며, 선택된 Claude 에이전트가 전부 실패할 때만 Claude reviewer가 `excluded`다. Codex 주체 실패는 Codex reviewer `excluded`다. 전부 실패한 Claude 집합에 `schema_violation`이 하나라도 섞이면 `failure_type=schema_excluded`, 없으면 `no_output`이고 두 값이 동시에 생기지 않는다. 검증: Codex/Claude 변환 경계, 다섯 outcome, 무보정, Claude 일부/전부 및 mixed 실패 집계표 단위 테스트.
- **AC-79** [실행] head A의 inline 가능한 `new` finding에 `apply`하면 1단계 요약의 v1 record가 `placement=inline`로 게시된 뒤 2단계 inline 호출이 실패하는 fixture를 만든다. 로컬 상태 루트를 전부 제거하고 head B에서 같은 `finding_id`·inline 가능한 현재 finding으로 새 실행을 시작하면 GitHub 요약에는 record가 있고 marker는 0개이므로 `history_restore.status == "ok"`, `delivery_states.status=inline_pending`, `action=retry_inline`, lifecycle=`persisting`이며 현재 head 위치의 복구 comment가 정확히 1개 계획된다. 이를 성공 적용한 뒤 로컬 상태를 다시 비운 세 번째 `plan`은 `inline_posted`를 복원하고 신규 inline이 0건이다. 대조 fixture의 `placement=summary_only`·marker 0개는 `summary_only`·inline 0건이고, pending finding이 현재 없거나 inline 불가능하면 각각 `action=isolate`와 `current_missing`/`current_not_inline_eligible`를 상태·요약에 남기며 inline·resolve가 0건이다. marker 불일치·중복은 `retry_inline`이 아니라 AC-65의 `linkage_invalid`다. 검증: 요약 성공 → 원자적 inline 실패 → 로컬 상태 제거 → 다음 head 복구 → 완료 확인의 fake GitHub 다중 실행 왕복 단위 테스트.
- **AC-80** [실행] 호출 파서는 `--rounds`의 토큰 값으로 정확히 `0`·`1`·`2`만 수락한다. `/dual-review --pr 42 --base main --rounds <각 허용값> --no-publish`는 네 플래그를 모두 파싱하고, `--rounds`의 `-1`·`3`·`01`·`1.0`·`foo`·값 누락은 각각 종료 코드 != 0으로 상태 디렉터리 생성·리뷰어 호출·GitHub 호출 전에 거부한다. 계약에 없는 `--resume`도 같은 시점에 거부한다. 검증: 허용값 세 개와 잘못된 값·누락·미지원 플래그의 argv 파서 단위 테스트.
- **AC-81** [실행] `repo=octo-org/widget-kit`, `pr_number=42`, `head_sha=0123456789abcdef0123456789abcdef01234567`의 `run_id`는 정확히 `octo-org-widget-kit-pr42-0123456789ab`이다. owner·repo·`pr`+10진 PR 번호·full SHA의 앞 12자를 이 순서와 하이픈으로 한 번씩 결합하며 타임스탬프나 full SHA의 13번째 이후 문자는 넣지 않는다. 같은 입력은 같은 문자열, 앞 12자가 다른 SHA는 다른 문자열을 만들고, 13번째 이후만 다른 SHA는 같은 candidate 문자열을 만들되 AC-61의 full-SHA 충돌 검사 때문에 기존 상태를 재개하지 않는다. 검증: 고정 known-answer, first-12 변경, suffix-only 변경과 상태 재개 거부 단위 테스트.
- **AC-82** [실행] production `render_report(state, synthesis)`가 반환하고 `SKILL.md`가 그대로 표시하는 **실제 사용자 리포트 문자열**을 다음 fixture에서 캡처한다. 정상 fixture도 `잔존 한계` 절에 자유 텍스트의 출처 암시 가능성·Claude 종합자의 자기선호 편향 두 항목과 advisory/non-blocking 문구를 모두 포함한다. base 불일치 fixture는 `requested_ref`·`actual_base_sha`, 승인된 단일 리뷰 fixture는 단일 리뷰어 사실·정확한 R3.7 `failure_type`, Claude 일부 실패 fixture는 실패 agent 목록·canonical category coverage, `disputed`/`unresolved` fixture는 두 finding을 버리지 않은 `두 리뷰어가 갈린 지점`, 범위 축소 fixture는 정확한 경로 집합·제외 파일 수를 포함한다. 같은 fixture의 `summary_action.body`에도 R2.1a·R3.7·R3.9·R6.3·R10.3이 게시를 요구한 항목이 동일한 상태 값으로 나타난다. 테스트는 `references/*.md`의 문구나 report 전용 golden 파일만 읽어서 통과할 수 없고 production renderer 반환값과 `publish_findings.py plan` 출력을 직접 단정한다. 검증: 실제 renderer와 게시 plan을 함께 호출하는 상태별 통합 단위 테스트 + `SKILL.md`의 verbatim 전달 계약 테스트.
- **AC-83** [실행] `docs/dual-review-maintenance.md`의 `후속 작업` 절 안에 `SARIF 이관` 항목이 있고, 그 항목이 현재 미지원 상태와 착수 조건 또는 이관 시 검토할 호환성 범위를 비어 있지 않은 문장으로 기록한다. 단순히 다른 절에 `SARIF`라는 단어가 있거나 빈 표 행만 있으면 실패한다. 검증: Markdown heading 경계를 파싱해 해당 절의 non-empty follow-up record를 단정하는 계약 테스트.
- **AC-84** [실행] R7.6a 단계 0의 ID 재대응이 결정적으로 동작한다. 이전 record와 `(path, cat, fp)`가 모두 같지만 제목이 달라 `finding_id`가 다른 현재 finding이 **정확히 1건**인 fixture에서 그 record는 `persisting`이고, `resolveReviewThread` 호출이 0건이며, 그 finding에 대한 새 inline 코멘트 생성이 0건이고, 상태의 `id_remapped`에 `{old_id, new_id, matched_on: ["path","cat","fp"]}`가 기록되며, 게시 요약에 재대응 사실이 나타난다. 같은 `(path, cat, fp)`를 갖는 현재 finding이 **2건 이상**인 fixture에서는 재대응하지 않고 결손 표로 넘어가며 임의 선택이 일어나지 않는다. 세 값 중 **하나라도 다른** fixture에서도 재대응하지 않는다. 검증: 1건·2건·불일치 세 fixture의 fake 클라이언트 단위 테스트.
- **AC-85** [실행] R7.6a 4행이 category 단위 판정과 독립으로 동작한다. 직전 실행에서 `silent-failure-hunter`가 낸 `cat=correctness` record에 대해 이번 실행에서 그 에이전트가 선택되지 않고 `code-reviewer`만 성공한 fixture에서, R3.10의 `agent_category_uncovered(correctness)`와 `agent_category_unselected(correctness)`가 **모두 거짓**인데도 그 record는 reason=`src_agent_unavailable`인 `not_re_reviewed`이고 `resolveReviewThread` 호출이 0건이다. `SRC_AGENTS(record.src)` 중 하나라도 이번 실행에서 성공한 fixture에서는 4행이 거짓이다. `src`가 `codex`만인 record에는 4행이 적용되지 않는다. 검증: 중복 담당 category와 `src` 조합별 fake 클라이언트 단위 테스트.
- **AC-86** [실행] `fp`의 소비처가 정확히 둘로 한정된다. 이전 record의 `fp`만 형식상 유효한 다른 값으로 바꾼 fixture에서 (a) R7.6a 단계 0의 재대응 결과와 그로 인한 lifecycle은 바뀔 수 있고, (b) R7.21의 `fingerprint_relation`도 바뀔 수 있으나, (c) R7.17의 record↔marker 연결 판정, inline 코멘트의 `path`·`line`·`side`, 요약 tier 선택, R7.5 dedup 결과는 바뀌지 않는다. 검증: fp-only 변이 fake 클라이언트 단위 테스트.

### 요구사항 추적

모든 요구사항이 하나 이상의 수용 기준에 대응한다. 대응이 없는 요구사항은 존재하지 않는다.

| 요구사항 | 수용 기준 |
|---|---|
| R1.1 | AC-33, AC-35 |
| R1.2 | AC-33 |
| R1.3 | AC-28 |
| R1.4 | AC-28, AC-55, AC-74, AC-80 |
| R2.1 | AC-51 |
| R2.1a | AC-54, AC-82 |
| R2.2 | AC-11, AC-51 |
| R2.3 | AC-32 |
| R2.4 | AC-36 |
| R2.5 | AC-51, AC-61, AC-64, AC-80, AC-81 |
| R3.1 | AC-17, AC-60 |
| R3.2 | AC-27, AC-29, AC-48 |
| R3.3 | AC-20, AC-28, AC-73 |
| R3.4 | AC-18 |
| R3.5 | AC-19, AC-78 |
| R3.5a | AC-19, AC-63, AC-78 |
| R3.6 | AC-45 |
| R3.7 | AC-20, AC-59, AC-63, AC-73, AC-78, AC-82 |
| R3.8 | AC-27, AC-44 |
| R3.9 | AC-59, AC-62, AC-68, AC-78, AC-82 |
| R3.10 | AC-60, AC-62, AC-68, AC-77, AC-78 |
| R4.1 | AC-4 |
| R4.2 | AC-4 |
| R4.3 | AC-5 |
| R4.4 | AC-4, AC-5 |
| R5.1 | AC-21, AC-53, AC-74 |
| R5.2 | AC-41 |
| R5.3 | AC-21 |
| R5.4 | AC-22, AC-56 |
| R6.1 | AC-23, AC-24, AC-69 |
| R6.2 | AC-42 |
| R6.3 | AC-43, AC-50, AC-70, AC-82 |
| R6.4 | AC-13, AC-40, AC-82 |
| R6.5 | AC-23, AC-50, AC-69, AC-70 |
| R7.1 | AC-13 |
| R7.2 | AC-15, AC-28 |
| R7.3 | AC-1, AC-2, AC-72, AC-84 |
| R7.4 | AC-3, AC-75 |
| R7.5 | AC-6, AC-86 |
| R7.6 | AC-8, AC-10, AC-49, AC-62, AC-65, AC-76, AC-77, AC-79 |
| R7.6a | AC-10, AC-62, AC-65, AC-68, AC-77, AC-84, AC-85 |
| R7.7 | AC-8, AC-10, AC-14, AC-49, AC-62, AC-79 |
| R7.8 | AC-12, AC-64, AC-66, AC-71 |
| R7.9 | AC-8, AC-46, AC-64 |
| R7.10 | AC-39 |
| R7.11 | AC-11 |
| R7.12 | AC-7, AC-8, AC-9, AC-79 |
| R7.13 | AC-7, AC-8, AC-9, AC-49, AC-79 |
| R7.14 | AC-14 |
| R7.15 | AC-16 |
| R7.16 | AC-46 |
| R7.17 | AC-47, AC-64, AC-65, AC-67, AC-76, AC-79 |
| R7.18 | AC-58 |
| R7.19 | AC-64~AC-68, AC-71, AC-75, AC-76, AC-79 |
| R7.20 | AC-71 |
| R7.21 | AC-75, AC-86 |
| R8.1 | AC-1~AC-6, AC-17~AC-25, AC-50, AC-56, AC-59~AC-63, AC-69~AC-70, AC-72~AC-74, AC-78, AC-80~AC-82 |
| R8.2 | AC-8, AC-14~AC-15, AC-49, AC-55, AC-64~AC-68, AC-71, AC-75~AC-77, AC-79, AC-82, AC-84~AC-86 |
| R8.3 | AC-30 |
| R8.4 | AC-31 |
| R8.5 | AC-26, AC-37, AC-52, AC-71, AC-79 |
| R9.1 | AC-38 |
| R9.2 | AC-28, AC-38, AC-83 |
| R10.1 | AC-25, AC-60 |
| R10.2 | AC-25, AC-57 |
| R10.3 | AC-25, AC-71, AC-82 |

전수 대조는 66개 요구사항 각각의 문언을 열거값·경계/오류·상태 변화·사용자 표시 위치·금지 동작으로 분해하고, 매핑된 AC의 **합집합에 그 조건을 직접 관측하는 단정이 있는지** 다시 확인했다. 단순히 같은 파일이나 기능을 언급하는 AC는 근거로 세지 않았다. 이번 대조에서 READY-01이 지목한 네 결손은 R1.4의 허용값 동작을 AC-74, 잘못된 값 거부를 AC-80, R2.5의 exact known-answer를 AC-81, R6.4의 production report 출력을 AC-82, R9.2의 heading-scoped 후속 작업 record를 AC-83으로 각각 닫았다.

같은 방법으로 나머지 62개 행도 다시 읽어 추가 교차 결손을 찾았다. R2.1a·R3.7·R3.9·R6.3·R10.3의 **실제 리포트 또는 게시 요약 표시**는 모두 production renderer/plan을 직접 실행하는 AC-82에 연결했고, R10.1~R10.3의 등호·초과 경계와 무언의 추가 절단 금지는 AC-25에 보강했다. R2.5의 12자 형식과 “head 변경” 문언을 함께 대조하면서 발견한 동일 12자 prefix의 full-SHA 충돌은 R2.5·AC-61·AC-81에서 명시적 중단으로 정합화했다. 또한 문언과 같은 기능을 단순 언급하던 판정은 고정 SHA의 지문·전 단계 입력(AC-3·51), 주체별 retry 입력(AC-19), 정확한 `.gitignore` 항목(AC-36), 다섯 agent별 계약 우선 문구(AC-45), 요청 base의 실제 diff 기준 적용(AC-54), 추상화 이탈 사용자 안내(AC-56), INTAKE 순서와 완료 기록 재개(AC-61)까지 직접 관측하도록 보강했다. R7.7의 모든 스레드 답글 금지는 reply endpoint가 없는 화이트리스트를 검사하는 AC-14에 연결했다. 나머지 독립 조건은 각 행에 매핑된 AC 합집합의 명시적 입력·경계·출력·금지 동작으로 판정된다. AC-34는 전체 결정적 테스트의 통과를 한 번 더 묶는 메타 기준이라 특정 요구사항의 판정 근거로 등재하지 않는다. AC-1~33·35~83은 모두 적어도 한 요구사항의 실제 판정 근거로 등장한다.

## Architecture

### 컴포넌트

| 컴포넌트 | 책임 | 형태 |
|---|---|---|
| `SKILL.md` | 단계 표, 각 단계의 필수 행동, 두 승인 게이트, 참조 파일 로딩 지시, `render_report` 반환값을 실제 사용자 리포트로 그대로 전달 | 마크다운 지시서 |
| `references/reviewer-contract.md` | 두 리뷰어 공통 계약(구조화 출력, 근거 규율, finding bar), 에이전트 선택 표, `AGENT_CATEGORY_MAP_V1`, Codex 호출 템플릿과 모델·effort, 입력 규모 임계값 | 마크다운 |
| `references/cross-critique.md` | 교차비평 라운드 규칙, 새 근거 정의, 추상화 이탈 신호 정의, 종료 규칙 | 마크다운 |
| `references/synthesis-contract.md` | 종합자 계약(R6.5 익명 per-finding 입력, relation→분류 규칙, 5축 판정, 잔존 한계) | 마크다운 |
| `references/publish-contract.md` | 게시 계약(SHA 고정, inline marker + `placement` 포함 요약 인덱스, GitHub 이력·delivery 복원, 여덟 결손 경로, 요약 48 KiB 상한·축약/중단, 3단계 게시, lifecycle, 엔드포인트 화이트리스트, verdict 정책, 롤백 한계) | 마크다운 |
| `schemas/reviewer-output.schema.json` | 리뷰어 산출 (루트 object, `{"findings": [...]}`). `uniqueItems`·lookaround 미사용 | JSON Schema 2020-12 |
| `schemas/critique.schema.json` | 교차비평 산출 (루트 object). target ID·stance·non-empty evidence required | JSON Schema 2020-12 |
| `schemas/synthesis.schema.json` | 종합 산출 (루트 object). 다섯 축 required, 분류 4값 enum, 조건부 `unresolved_reason` | JSON Schema 2020-12 |
| `schemas/publish-plan.schema.json` | `plan.json` 계약 (루트 object) | JSON Schema 2020-12 |
| `scripts/review_state.py` | **`finding_id`·`anchor_fingerprint` 계산과 R7.5 병합의 소유자.** 상태 머신, 주체별 Markdown→JSON 변환·다섯 outcome·reviewer 집계, 에이전트 선택·category coverage, 위치 실측 검증, 라운드 판정, 실제 출처 sidecar와 익명 관측·critique synthesis view 분리·셔플, relation/분류 검증, 결정적 사용자 리포트 렌더링 | Python 3 표준 라이브러리 |
| `scripts/publish_findings.py` | `plan`/`apply`, GitHub 게시 이력과 placement/marker delivery 복원, **여덟 결손 경로 lifecycle과 ID 재대응**, fp/run 진단, 불가분 인덱스와 요약 크기 guard, 3단계 게시. `finding_id`·`anchor_fingerprint` 계산과 R7.5 병합은 **소유하지 않고** `review_state.py`에서 import해 쓴다 | Python 3 표준 라이브러리 |
| `tests/` | 결정적 단위 테스트와 픽스처 | unittest |

### 상태와 게시 이력 경계

로컬 `.claude/dual-review-state/<run_id>/`는 한 `run_id`의 재개와 3단계 게시 bookkeeping만 담당한다. 서로 다른 head SHA의 실행을 잇는 durable 경계는 GitHub다. `publish_findings.py plan`은 sticky 요약의 R7.19 인덱스를 기준 집합으로 읽고, `placement`를 inline 의도로, inline comment의 `finding_id` marker와 REST review 연결을 완료 증거로 결합하며, GraphQL thread 상태를 덧붙인다. 따라서 1단계 요약만 성공하고 2단계가 실패한 뒤 로컬 상태가 사라져도 `placement=inline`·marker 0개의 `inline_pending`으로 복원한다. 인덱스가 완전할 때만 여덟 결손 경로의 `src`·`path`·`cat` 판정을 수행하고, 완전하지 않으면 `resolved` 집합을 공집합으로 강제한다. `inline_pending`은 완전한 이력의 delivery 중간 상태라 전역 복원을 실패시키지 않으며, marker 불일치만 해당 record를 격리한다. 해결된 고아 marker도 전체 복원을 실패시키지 않는다. 따라서 worktree나 로컬 상태가 사라져도 다음 실행의 판정 입력과 미완료 inline 의도는 사라지지 않으며, 반대로 GitHub 이력이 불완전할 때 로컬 잔여 파일로 추측하지 않는다.

category 책임 매핑은 현재 실행의 Claude 일부 실패와 담당 미선택 coverage에만 쓰인다. `review_state.py`가 R3.10 상수와 선택·성공·실패 집합에서 `category_coverage`를 한 번 계산하고, `publish_findings.py`는 GitHub 인덱스에서 복원한 `cat`을 그 결과의 `selected_agents`·`covered`에 조회한다. R7.19 인덱스 형식에는 매핑이나 coverage를 추가하지 않으며 `cat` 일곱 값 계약도 바꾸지 않는다. 따라서 정적 책임표가 GitHub source of truth를 대체하지 않고, GitHub에서 복원한 과거 category와 현재 실행의 실제 coverage가 결합돼야만 결손이 성립한다.

출처 은닉 경계는 종합자 입력에만 있다. `review_state.py`는 상세 `finding_provenance`와 실제 group→alias `reviewer_aliases`를 비공개 상태에 유지하면서, 종합자에게는 alias별 `observations`·근거 있는 `critiques`·결정적 `relation`이 든 R6.5 view를 준다. 같은 ID 병합 전의 양쪽 주장과 반박은 view에 남지만 실제 reviewer 이름은 없다. 종합 뒤에는 `finding_id`로 상세 provenance를 재결합해 게시 인덱스의 `src`를 만든다. 즉 `reviewer-1/2`는 종합 전용이고 GitHub에 지속되지 않으며, 실제 `src`는 종합자에게 노출되지 않는다.

### 단계

```
INTAKE        대상 PR·base_sha·head_sha·변경 파일 고정, 규모 임계값 확인,
              gh/codex(gpt-5.6-terra) 프리플라이트, 상태 경로 무시 확인
   ↓
REVIEW        Claude 에이전트(매핑 선택) + Codex — 서로의 결과를 모름
   ↓
VALIDATE      스크립트가 주체별 Markdown→JSON·스키마·파일·라인 실측 검증,
              outcome/reviewer 집계, diff 범위 판정, ID 병합 시 group별 원 주장 보존
   ↓
CRITIQUE      상대 findings 반박 (기본 1회, 최대 2회)
              새 근거 0건 → 조기 종료 / 추상화 이탈 신호 → 사용자에게 종료 제안
   ↓
SYNTHESIS     실제 출처 → reviewer-1/2, observations+critiques → relation 계산
              결정적 셔플 → 5축 판정 → relation과 정합한 classification
   ↓
REPORT        review_state.py render_report → 필수 한계·조건부 경고가 든 실제 사용자 Markdown
   ↓
PLAN          GitHub placement/marker/index/review/thread 복원 → delivery 상태 + 여덟 결손 경로 + fp/run 진단
              lifecycle → 불가분 v1 index → full/compact/minimal 렌더 → 48 KiB 검사 → plan.json
   ↓
[승인 게이트]  사용자에게 계획을 보이고 명시적 승인을 받는다
   ↓
APPLY         publish_findings.py apply — head SHA 재확인 후 3단계 게시, 멱등
```

리뷰어 하나가 실패해 남은 리뷰어가 하나뿐이 되면 REVIEW 단계에서 추가 승인 게이트가 발생한다(R3.7). 실패 유형은 `preflight_unavailable`·`schema_excluded`·`no_output` 셋이며 뒤의 둘은 R3.5a의 reviewer `excluded` 집계다. 양쪽이 모두 실패하면 승인을 묻지 않고 중단한다(R3.9). 규모 초과(R10.2)와 추상화 이탈(R5.4)에서도 사용자 결정을 기다리지만 그것은 진행 방식 선택이지 승인 게이트가 아니다. **승인 게이트는 단일 리뷰 승인(R3.7)과 게시 승인(R7.2) 둘이다.**

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

### 사용자 리포트 (`scripts/review_state.py` 산출)

`render_report(state, synthesis)`는 최종 상태와 검증된 종합 결과를 받아 Markdown 문자열을 결정적으로 반환한다. 이것이 R2.1a·R3.7·R3.9·R6.3·R6.4·R10.3이 말하는 **실제 사용자 리포트**이며, `SKILL.md`는 반환 문자열을 축약하거나 자유형식으로 다시 쓰지 않고 그대로 표시한다. `references/synthesis-contract.md`의 문구 존재나 별도 golden fixture만으로 실제 리포트 판정을 대체하지 않는다.

리포트에는 항상 `잔존 한계` 절과 R6.4의 두 항목(자유 텍스트의 출처 암시 가능성, Claude 종합자의 자기선호 편향), 종합 결과가 merge 차단 판단이 아닌 advisory라는 문구를 둔다. 해당 상태가 있을 때는 base 불일치와 `requested_ref`·`actual_base_sha`, 단일 리뷰어 사실과 R3.7 `failure_type`, 실패한 Claude 에이전트 목록과 canonical category coverage, `disputed`·`unresolved` finding을 보존한 `두 리뷰어가 갈린 지점`, 범위 축소 경로 집합과 제외 파일 수도 각각 표시한다. 같은 fixture에서 `publish_findings.py plan`이 생성한 게시 요약은 게시를 요구한 R2.1a·R3.7·R3.9·R6.3·R10.3의 해당 항목을 동일한 상태 값으로 표시해야 한다.

### 게시 계획 (`schemas/publish-plan.schema.json`)

`plan`이 산출하고 `apply`가 소비하는 계약이다. 루트 object, `additionalProperties: false`.

| 필드 | 타입 | 설명 |
|---|---|---|
| `repo`, `pr_number` | string, integer | 대상 고정값 |
| `base_sha`, `reviewed_sha` | string | 상태의 고정값. `reviewed_sha`가 요약 첫 줄에 인용된다 |
| `base_mismatch` | object \| null | `--base`가 PR 실제 base와 다를 때 `{requested_ref, actual_base_sha}`. null이 아니면 `inline_review.skip`이 참이어야 한다(R2.1a) |
| `summary_action` | object | `{kind: "create"|"update", comment_id: integer|null, body: string}` |
| `summary_render` | object | `{max_bytes, index_block_bytes, full_bytes, compact_bytes, minimal_bytes, selected_tier}`. 성공 계획에서 `max_bytes=49152`, `selected_tier`는 `full`/`compact`/`minimal`이고 선택 body의 UTF-8 바이트 수가 상한 이하다 |
| `history_restore` | object | `{status, summary_comment_id, index_version, error, delivery_states}`. `status`는 `ok`/`missing`/`invalid`이고 `status != "ok"`이면 `lifecycle.resolved`는 비어 있어야 한다. `delivery_states` 원소는 R7.17의 `{finding_id, placement, status, action, reason}` 닫힌 계약이다 |
| `inline_review` | object | `{skip: boolean, comments: [...]}`. `skip`이 참이면 2단계를 호출하지 않는다. `comments`에는 정상 `new`와 `delivery_states.action=retry_inline`만 들어갈 수 있다 |
| `thread_resolutions` | array | `[{thread_id, finding_id}]` |
| `summary_only_findings` | array | 강등된 finding. 강등 사유는 셋이다 — R2.1a의 base 불일치(전면 강등), R4.2의 `location_valid=false`, R4.3의 `in_diff_range=false`. R7.19의 `new` record `placement` 규칙과 같은 열거다 |
| `lifecycle` | object | `{new: [...], persisting: [...], resolved: [...], not_re_reviewed: [{finding_id, reason}]}`. `reason`은 R7.6a의 여덟 결손 경로(`codex_unavailable`·`reviewer_excluded`·`reviewer_no_output`·`src_agent_unavailable`·`path_out_of_scope`·`base_narrowed`·`agent_category_uncovered`·`agent_category_unselected`) 또는 `history_unavailable` 중 하나 |
| `skipped_threads` | array | `[{thread_id, reason}]` — R7.18로 건너뛴 스레드 |
| `coverage_gap_evidence` | array | `[{finding_id, reason, field, value}]`; `not_re_reviewed`의 결정적 판정 근거 |
| `id_remapped` | array | `[{old_id, new_id, matched_on}]`; R7.6a 단계 0의 ID 재대응 기록. `matched_on`은 `["path","cat","fp"]` 고정 |

`inline_review.comments` 원소의 구성은 실측으로 확정했다(R7.16). `{path, line, side, body, finding_id}`가 필수이고, finding이 여러 줄에 걸치면 `start_line`·`start_side`를 함께 싣는다. `summary_action.body`에는 R7.8 요약 마커와 R7.19 인덱스 블록이 정확히 하나씩 있어야 하고 UTF-8 바이트 수가 `summary_render.max_bytes` 이하여야 한다. R7.20의 두 oversize 오류에서는 적용 가능한 plan object 자체를 만들지 않으므로 `summary_render.selected_tier`가 null인 실패 진단을 publish-plan 스키마 안에 억지로 넣지 않는다.

### 상태 파일

`.claude/dual-review-state/<run_id>/state.json`은 아래 필드를 갖는다. 이 목록은 상태 스키마의 닫힌 계약이며 구현과 픽스처가 같은 key 집합을 단정한다.

| 필드 | 내용 |
|---|---|
| `run_id`, `repo`, `pr_number` | 실행·대상 식별자 |
| `requested_base_ref`, `actual_base_sha`, `base_sha`, `base_mismatch` | 호출 인자와 PR 실제 base, diff base, R2.1a 판정 |
| `head_sha`, `changed_files`, `rounds` | 고정 리뷰 대상과 유효 교차비평 횟수 |
| `scope_reduction` | 검토 경로 집합과 제외 파일 수 |
| `selected_agents` | 선택 에이전트와 유발 신호·매치 수 |
| `agent_outcomes` | Codex와 선택 Claude 에이전트별 `{result, attempts}`. `result`는 R3.5의 다섯 값뿐 |
| `agent_category_map` | 실행이 사용한 R3.10 `AGENT_CATEGORY_MAP_V1`의 exact object |
| `category_coverage` | 일곱 category별 `{selected_agents, successful_agents, failed_agents, covered}`; 배열은 정렬 |
| `reviewers` | 상위 reviewer별 산출물 경로·집계 성공/`excluded`·R3.5a의 `failure_type`·사유 |
| `finding_provenance` | `finding_id`별 정렬·중복 제거한 reviewer ID 배열; 종합자에게는 비공개 |
| `reviewer_aliases` | 실제 상위 reviewer group→`reviewer-1`/`reviewer-2`; 종합자에게는 비공개 |
| `single_reviewer_approval` | R3.7 승인 여부와 기록 시각 |
| `critique_rounds`, `termination_reason` | 실제 group에 연결된 교차비평과 종료 결과; 종합자에게 직접 전달하지 않음 |
| `synthesis_input`, `synthesis` | R6.5의 익명 per-finding 입력과 relation 검증을 통과한 종합 결과 |
| `previous_review_comments` | R7.17의 REST comment 여섯 필드와 inline 마커 파싱 결과 |
| `previous_reviews` | review의 `id`·`commit_id`·`state`와 comment 연결 |
| `history_restore` | `{status, summary_comment_id, index_version, error, findings, delivery_states}`; `findings` 원소는 R7.19의 아홉 persisted key이고 `delivery_states`는 placement/marker에서 파생한 R7.17의 상태·행동·사유 |
| `history_diagnostics` | `[{finding_id, source_run_id, run_relation, fingerprint_relation}]`; R7.21의 진단 전용 fp/run 소비 결과 |
| `coverage_gap_evidence` | `[{finding_id, reason, field, value}]`; R7.6a의 결손·복원 실패 근거 |
| `id_remapped` | `[{old_id, new_id, matched_on}]`; R7.6a 단계 0의 ID 재대응 기록 |
| `summary_render` | `{max_bytes, index_block_bytes, full_bytes, compact_bytes, minimal_bytes, selected_tier, error}`. `selected_tier`는 성공 시 `full`/`compact`/`minimal`, 실패 시 null이고 `error`는 성공 시 null, 실패 시 `summary_index_oversize`/`summary_body_oversize` |
| `publish_stages` | 요약·inline review·thread resolve 세 단계 완료 기록과 각 쓰기 응답 ID. 이 로컬 기록이 없어도 `placement`/marker로 1·2단계 경계를 복원한다 |
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
git diff(base..head) ─┬─→ Claude 에이전트(선택) → agent별 Markdown → JSON/schema(A) ─┐
                      └─→ codex exec(terra/high)              → reviewer-output(B) ─┤
                                                                                     ↓
                                                   review_state.py validate
                        (주체 outcome/reviewer 집계, 위치, diff 범위, group 관측 + finding_id·fp 계산과 R7.5 ID 병합 — 이 모듈이 소유)
                                                                                     ↓
                                            findings(A)⇄findings(B) 교차비평 (0~2회)
                                                                                     ↓
                                               review_state.py split
                           ├─ private reviewer_aliases (상태 진단 전용)
                           ├─ private finding_provenance ── 종합 뒤 실제 `src` 재결합 ─┐
                           └─ public aliases+observations+critiques → relation → 종합자 ─┤
                                                        → 검증된 synthesis.json ─────────┤
                                           state.category_coverage ─────────────────────┤
 GitHub issue/review comments + reviews + threads → R7.19 restore (`placement`,`cat`,`fp`,`run`) ┴─→ publish_findings.py plan
                                                                               (delivery + 여덟 결손 + 진단)
                                                                                                  ↓
                                                                  full v1 index + visible tiers → 48 KiB guard → plan.json
                                                                            ↓
                                                [사용자 승인]
                                                                            ↓
                                publish_findings.py apply → GitHub (3단계)
```

검증된 `synthesis`와 최종 상태는 게시 plan과 별도로 `render_report`에도 들어가며, 그 반환 Markdown이 `SKILL.md`를 거쳐 사용자에게 그대로 전달된다. 리포트와 게시 요약은 같은 상태 값을 소비하되, 리포트는 GitHub 게시 여부와 무관하게 항상 R6.4의 잔존 한계를 표시한다.

## Failure behavior

| 실패 | 동작 |
|---|---|
| `gh` 미설치·미인증 | INTAKE에서 중단하고 인증 방법을 안내한다. 상태를 만들지 않는다. |
| detached HEAD 또는 현재 브랜치 PR 조회가 0건·2건(2건 이상) | 상태를 만들지 않고 중단하며 `--pr` 지정을 요구한다. 전역 열린 PR 목록에서 추측하지 않는다(R8.2). |
| 잘못된 `--rounds` 또는 미지원 `--resume` | argv 파싱에서 종료 코드 != 0으로 중단한다. 상태 디렉터리·리뷰어·GitHub 호출은 모두 0건이다(R1.4, R2.5). |
| 같은 candidate `run_id`의 full head·base 구성·`--rounds` 충돌 | full `head_sha`·`requested_base_ref`·해석된 `base_sha`·`actual_base_sha`·`rounds`를 대조하고, 상태를 읽어 진행하거나 덮어쓰지 않은 채 비정상 종료한다. 같은 앞 12자를 가진 다른 full SHA는 `run_id_prefix_collision`이다. 충돌 필드와 기존값·새 값을 출력하고 GitHub 쓰기는 0건이다(R2.5). |
| 입력 규모 임계값 초과 | 자동 진행하지 않고 중단 또는 범위 축소를 사용자에게 묻는다. 무언의 절단을 하지 않는다(R10). |
| Codex 프리플라이트 실패·모델 거부 | 모델을 임의로 대체하지 않는다. 사용자에게 알리고 단일 리뷰 승인 경로를 따른다(R3.3, R3.7). |
| Claude 에이전트 일부 실패 | R3.5의 주체 outcome과 R3.10의 고정 매핑으로 선택·성공·실패 집합을 계산한다. 실패자가 있으면서 성공 담당자가 없는 category만 uncovered로 기록하고 나머지로 진행한다. 선택된 에이전트가 전부 실패할 때만 Claude reviewer를 `excluded`로 집계한다. |
| agent-category map 또는 coverage 상태 불일치 | lifecycle 계획을 만들지 않고 비정상 종료한다. 새 결손 reason을 만들거나 GitHub 이력의 값으로 보완하지 않으며 쓰기 호출은 0건이다(R3.10). |
| 주체 출력의 Markdown→JSON 변환 또는 스키마 위반 | 검증 오류만 덧붙여 그 주체에 1회 재요청한다. 2회째 실패 시 주체 outcome을 `schema_violation`으로 기록하고, reviewer `excluded` 여부는 R3.5a로 별도 집계한다. |
| 두 리뷰어 모두 실패 | 게시하지 않고 중단한다. 단일 리뷰 승인을 묻지 않는다(R3.9). |
| 여덟 커버리지 결손 중 하나로 finding이 사라짐 | 복원한 `src`·`path`·`cat`과 현재 상태의 `category_coverage`로 `resolved`가 아니라 `not_re_reviewed`로 분류하고 스레드를 건드리지 않으며 상태·요약에 사유를 남긴다(R7.6a). 담당 category의 `S(c)`가 비면 `agent_category_unselected`, 선택자는 있지만 성공자가 없으면 `agent_category_uncovered`로 구분한다. |
| 종합자 입력에서 actual reviewer ID가 발견되거나 관측·critique·relation 계약이 맞지 않음 | 종합자를 호출하지 않고 SYNTHESIS 전에 중단한다. private sidecar를 입력으로 대체하지 않는다(R6.1, R6.5). |
| 종합 결과의 relation·classification 불일치 또는 근거 없는 `unresolved` | 종합 완료로 기록하거나 게시하지 않고 검증 오류를 표면화한다(R6.3). |
| 실제 사용자 리포트 렌더링 실패 또는 필수 한계·조건부 경고 누락 | 리포트를 자유형식 산문으로 대체하지 않고 비정상 종료한다. 게시 승인·`apply`로 전이하지 않으며 GitHub 쓰기는 0건이다(R6.4, R8.1). |
| 게시 인덱스 부재·손상·`placement` 포함 필드 결손 | 부분 이력을 쓰지 않고 `history_restore.status != "ok"`로 기록한다. `resolved`와 resolve 호출은 0건이며 식별 가능한 이전 finding은 `history_unavailable`로 보존한다(R7.6a, R7.19). |
| 유효 인덱스의 `placement=inline`인데 일치 marker가 없음 | 손상으로 보지 않고 `inline_pending`으로 복원한다. 현재 같은 finding이 inline 가능하면 정확히 한 번 복구하고, 없거나 inline 불가능하면 `current_missing`/`current_not_inline_eligible`로 격리해 inline·resolve를 0건으로 만든다(R7.13, R7.17). |
| 유효 인덱스의 개별 record-marker 연결 불일치 또는 고아 marker | `inline_pending`과 구분한다. 불일치·중복 marker record는 현재 같은 finding이 있으면 `persisting`으로 유지하되 쓰기를 격리하고, 없으면 `history_unavailable`인 `not_re_reviewed`로 보존한다. 열린 고아 스레드만 `history_unavailable`로 보존하며, 해결된·스레드 없는 고아 marker는 종결 이력으로 무시한다. 전체 복원은 실패시키지 않는다(R7.17). |
| 요약 `full` 본문이 49,152 UTF-8 bytes 초과 | 인덱스를 그대로 둔 채 `compact`, 이어 `minimal` 순으로 가시 본문만 축약한다. 처음 상한 이하인 tier를 선택하고 축약 tier·바이트 수를 상태와 계획에 노출한다(R7.20). |
| 완전한 인덱스 또는 `minimal` 요약도 49,152 UTF-8 bytes 초과 | 인덱스 record를 자르거나 코멘트를 분할하지 않는다. `summary_index_oversize` 또는 `summary_body_oversize`로 `plan`을 비정상 종료하고 적용 가능한 계획·GitHub 쓰기를 만들지 않는다. `apply`도 같은 검사를 첫 쓰기 전에 반복한다(R7.20). |
| `viewerCanResolve`가 거짓인 스레드 | resolve 호출을 하지 않고 건너뛰며 스레드 ID와 사유를 상태·요약에 남긴다(R7.18). |
| 위치 검증 실패 | 해당 finding을 inline에서 제외하고 요약에 "위치 미검증"으로 남긴다. 리뷰 전체를 실패시키지 않는다. |
| 교차비평 무진전 | 다음 라운드를 실행하지 않고 종료 사유 `no_new_evidence`를 기록한다. |
| 추상화 이탈 신호 | 라운드를 중단하고 사용자에게 종료를 제안한다. 자동으로 계속하지 않는다. |
| `apply` 직전 head SHA 불일치 | 아무것도 게시하지 않고 비정상 종료한다. 새 SHA로 리뷰를 다시 시작해야 한다. |
| 게시 1단계 실패 | 2·3단계를 실행하지 않고 비정상 종료한다. 재실행 시 1단계부터 다시 시도한다. |
| 게시 2단계 실패 | 원자적 호출이므로 부분 inline 게시는 없다. 3단계를 실행하지 않고 비정상 종료한다. 같은 로컬 상태의 재실행은 완료된 1단계를 건너뛰고 2단계를 marker 대조 후 재시도한다. 로컬 상태가 사라져도 1단계가 GitHub에 남긴 `placement=inline`과 marker 부재로 `inline_pending`을 복원해 다음 head의 현재 finding으로 안전하게 재시도하거나 명시적으로 격리한다(R7.13, R7.17, AC-79). |
| 게시 3단계 일부 실패 | 성공한 스레드 ID를 기록하고 비정상 종료한다. 재실행 시 미해결 스레드만 처리한다. |
| `--base`가 PR 실제 base와 다름 | inline 게시를 전면 금지하고 모든 finding을 요약으로 강등한다. 두 ref를 상태·리포트·게시 요약에 명시한다(R2.1a). |
| 목록 조회 페이지 순회 중 실패 | 부분 목록을 반환하지 않고 오류를 올린다. 불완전한 목록으로 세운 계획은 재게시와 `resolved` 오분류를 낳는다(R8.2). |
| 상태 디렉터리가 git에 무시되지 않음 | 경고를 출력하고 계속 진행한다. `.gitignore`를 임의 수정하지 않는다. |

## Security and risk

**신뢰 경계.** 리뷰어(LLM) 출력은 미신뢰 데이터다. 스키마 검증과 파일·라인 실측 검증(R4)을 통과한 것만 inline으로 게시한다. 리뷰 대상 diff에 프롬프트 인젝션 문구가 있어도, 스킬은 그것으로 게시 정책·승인 게이트·엔드포인트 화이트리스트·모델 선택을 바꾸지 않는다.

**게시 텍스트의 전파.** 게시 본문은 리뷰어가 생성한 텍스트와 diff 인용을 포함한다. 인용 대상은 이미 해당 PR에 존재하는 코드이므로 새로운 노출은 아니다. 저장소 밖 경로 인용은 위치 검증에서 걸러진다.

**게시 이력 파싱.** GitHub 코멘트와 review 응답은 전송 채널만 신뢰하고 내용은 미신뢰 데이터로 취급한다. R7.19 파서는 HTML 주석 안 payload를 명령으로 실행하거나 프롬프트로 넘기지 않고, 지원 version·표준 base64·`placement`를 포함한 닫힌 JSON key 집합·타입·허용값·inline ID 대조만 수행한다. 인덱스 자체가 무효면 부분 데이터로 resolve하지 않는다. 유효 `placement=inline`·marker 0개는 `inline_pending`으로 제한된 복구만 허용하고, marker가 있으나 연결이 어긋난 record는 격리해 공격자가 pending 복구를 중복 댓글 경로로 바꾸지 못하게 한다. `fp`·`run`은 형식 검증 뒤 진단에만 쓰며 GitHub payload가 lifecycle이나 현재 agent-category 책임표를 덮어쓰게 하지 않는다.

**종합 입력 경계.** 실제 reviewer ID는 private `finding_provenance`·`reviewer_aliases`에만 있고 종합자 payload에는 전달하지 않는다. 반대로 `source_count`만 남겨 분류 근거를 잃지 않도록 alias별 원 주장과 evidence 검증을 통과한 critique를 전달한다. payload의 닫힌 key·alias 값·relation을 호출 전에 검증하고, 출력 relation과 classification의 정합성을 호출 뒤 다시 검증한다.

**자격 증명.** 스크립트는 토큰을 읽거나 저장하거나 출력하지 않고 `gh` CLI 인증에 위임한다(R8.4). 상태 파일·로그·게시물에 토큰이 들어가지 않으며, 소스에 토큰 환경변수명이 등장하지 않는 것을 AC-31로 고정한다.

**권한 범위.** 활성 토큰 스코프는 `gist, project, read:org, repo, user, workflow`다. `repo`는 게시에 필요한 최소보다 넓지만 축소는 사용자 계정 설정의 영역이며 이 작업의 범위 밖이다. 대신 엔드포인트 화이트리스트(R7.14)와 그 준수를 강제하는 AC-14로 실제 행사 범위를 좁힌다.

**대상 오지정.** 잘못된 저장소·PR에 게시하는 것이 가장 비싼 실패다. 저장소와 PR 번호를 INTAKE에서 상태에 고정하고, `apply`가 상태의 값만 사용하며 실행 직전 head SHA까지 재확인한다(R7.11).

**리스크와 완화.**

| 리스크 | 완화 |
|---|---|
| 중복·스팸 댓글로 PR 오염 | `finding_id` marker dedup, sticky summary, 일반 `persisting` 재게시 금지, `inline_pending`만 marker 0개·현재 finding inline 가능 조건에서 1회 복구 |
| stale SHA 기준 리뷰 게시 | SHA 고정 + 게시 직전 재확인, 요약 첫 줄에 SHA 명시 |
| false positive 게시 | 교차비평 + 5축 판정 + 위치 실측, 근거 없는 finding은 `unresolved`로 강등 |
| 종합자 자기선호 편향 또는 분류 근거 소실 | actual 출처는 private sidecar로 분리하고 익명 observations·critiques·relation은 보존, relation/classification 검증, blocking verdict 없음, 잔존 한계 명시 |
| 에이전트 일부 실패를 구현별 category 추측으로 누락 | versioned `AGENT_CATEGORY_MAP_V1`, 중복 담당 집합식, 상태 coverage와 문서/상수 대조 테스트 |
| 리뷰가 merge를 차단 | verdict를 `COMMENT`로 고정, 발행 경로 부재를 테스트로 고정 |
| 승인 없는 게시 | `apply` 분리, 자동 호출 경로 부재를 AST 검사로 고정 |
| 대형 diff의 조용한 커버리지 결손 | 임계값 초과 시 사용자 결정 요구, 축소 범위를 상태·리포트·게시에 명시 |
| 이전 게시 인덱스 손상·형식 오염으로 미해소 스레드 resolve | 엄격한 marker/index 검증, 복원 실패 시 `resolved` 0건·`history_unavailable` 기본값 |
| 요약 성공 뒤 inline 실패와 로컬 상태 소실로 댓글 영구 누락 | v1 `placement`로 의도를 지속하고 marker를 완료 증거로 대조해 `inline_pending`만 현재 finding으로 정확히 한 번 복구, 그 밖에는 명시적 격리 |
| 요약 크기 초과로 매 실행이 게시 1단계에서만 실패 | 48 KiB 사전 guard, 가시 본문만 결정적 tier 축약, 인덱스 불가분, 최소 형태도 초과하면 모든 GitHub 쓰기 전 명시적 중단 |
| 같은 candidate `run_id`의 다른 full head·`--base`·`--rounds` 묵살 | full SHA와 상태 고정값 대조 후 prefix 충돌·구성 충돌 시 변경·쓰기 전 중단 |

## Test strategy

결정적 테스트는 `dot_claude/skills/dual-review/tests/`에 두고 `quality-goal` 선례와 같은 방식으로 실행한다.

### 판정 명령

Acceptance criteria의 `[실행]`은 아래 명령 중 대응 행을 뜻한다. 단위 테스트 AC는 해당 파일 안에 AC 번호를 이름 또는 주석으로 남겨 매핑을 기계적으로 검사할 수 있게 한다.

| 판정 ID | 담당 AC | 저장소 루트에서 실행할 명령 |
|---|---|---|
| PUB | AC-7~16, AC-23, AC-25, AC-39, AC-46~47, AC-49, AC-51~52, AC-54~55, AC-57~58, AC-61~62, AC-64~68, AC-71, AC-75~77, AC-79, AC-82 | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_publish_findings.py'` |
| STATE | AC-1~6, AC-17~25, AC-41, AC-45, AC-50, AC-53, AC-56, AC-59~63, AC-69~70, AC-72~74, AC-77~82 | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_review_state.py'` |
| CONTRACT | AC-13, AC-26, AC-28~33, AC-38, AC-40~45, AC-48, AC-60, AC-69, AC-71, AC-73, AC-82~83 | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_content_contracts.py'` |
| ALL | AC-34 | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'` |
| CODEX | AC-27 | 아래 "스크립트 밖 검증"의 실제 `codex exec` 명령 |
| CHEZMOI | AC-35 | `chezmoi --source "$PWD" target-path dot_claude/skills/dual-review/SKILL.md` |
| IGNORE | AC-36 | `git check-ignore -v .claude/dual-review-state/` |
| GH-READ | AC-37 | 아래 "스크립트 밖 검증"의 실제 PR에 대한 읽기 전용 `plan` 명령 |

- `test_publish_findings.py` — PUB 행의 AC. GitHub 접근은 호출 기록을 남기는 fake 클라이언트로 대체하고, 열 메서드 화이트리스트와 스레드 답글 부재·현재 브랜치 `head_ref` 호출·고정 대상의 전 단계 유지·요청 base를 쓴 실제 diff 판정·INTAKE/재개 순서·marker/index 4-run 왕복·record 단위 연결 격리·`placement`/marker delivery 상태·요약 성공 뒤 inline 실패와 로컬 상태 소실 후 다음 head 복구·fp/run 진단·review 연결·R3.10에서 계산한 실제 category coverage를 쓰는 여덟 결손 경로·복원 실패 기본값·실제 리포트 fixture와 같은 상태에서 생성한 사용자 표시용 요약·요약 UTF-8 크기 tier와 oversize 사전 중단·verdict 고정·쓰기 호출 0건·페이지 순회 완전성을 그 기록으로 판정한다.
- `test_review_state.py` — STATE 행의 AC. **`finding_id`·`anchor_fingerprint` 계산과 R7.5 병합의 소유 모듈이므로 그 세 계약(AC-1~3·AC-6·AC-72)을 여기서 판정한다.** 임시 git 저장소 픽스처로 고정 SHA의 지문·파일·라인·diff 범위와 INTAKE 뒤 branch/worktree 변이의 전 단계 입력을 실측하고, 주체별 retry prompt·다섯 outcome과 Claude reviewer 집계, 다섯 agent의 계약 우선 프롬프트, `AGENT_CATEGORY_MAP_V1`의 선택/성공/실패/미선택 집합 계산, rounds 허용·거부 경계, exact `run_id`와 INTAKE 순서·12자 prefix 충돌, R5.4 등호 경계와 사용자 안내, 병합 전 group별 관측 보존, alias 변환, critique 연결, relation 산출, relation/classification 검증, production `render_report`의 실제 Markdown 출력을 raw 입력부터 실행한다.
- `test_content_contracts.py` — CONTRACT 행의 AC. 네 스키마의 루트 형태와 필드 요건(critique의 target·stance·evidence, synthesis의 다섯 축·네 분류 enum·`unresolved_reason`, publish-plan의 `history_restore`·`coverage_gap_evidence`·`skipped_threads`·`summary_render`), `AGENT_CATEGORY_MAP_V1`과 `SUMMARY_BODY_MAX_BYTES`의 문서/스크립트 일치, R6.5 synthesis-input 닫힌 key, `SKILL.md` frontmatter·`version` 형식·플래그·정확한 프리플라이트 인자·두 게이트 문구와 참조 경로·`render_report` 반환값의 verbatim 전달, 금지 플래그 부재, 구조화 출력 금지 구성(`uniqueItems`·lookaround) 부재, 표준 라이브러리 import, 토큰 문자열 부재, 디렉터리 구성, 유지보수 문서의 네 절·heading-scoped 후속 작업, 종합자 계약의 한계·비차단 권한 명시를 확인한다.

스크립트 밖 검증:

- **AC-27** — `DUAL_REVIEW_AC27_DIR=$(mktemp -d)`로 임시 디렉터리를 만든 뒤 최소 프롬프트로 `codex exec --sandbox read-only --ephemeral --model gpt-5.6-terra -c model_reasoning_effort="high" --output-schema "$PWD/dot_claude/skills/dual-review/schemas/reviewer-output.schema.json" --output-last-message "$DUAL_REVIEW_AC27_DIR/result.json" --json 'Return a valid empty review result for schema acceptance testing.'`을 1회 실행한다. 종료 코드 0이고 `result.json`이 같은 스키마를 만족해야 한다.
- **AC-34** — 판정 명령 ALL.
- **AC-35** — 판정 명령 CHEZMOI가 종료 코드 0이고 출력이 `~/.claude/skills/dual-review/SKILL.md`의 절대 경로다. 이 워크트리를 source로 명시해 main checkout을 보는 `chezmoi source-path`의 영향을 제거한다.
- **AC-36** — `git check-ignore -v .claude/dual-review-state/`의 종료 코드가 0이고 출력의 source가 저장소 루트 `.gitignore`, match pattern이 정확히 `.claude/dual-review-state/`인지 대조한다.
- **AC-37** — `gh pr list --state open --limit 1 --json number`로 얻은 PR 번호를 명시해 `publish_findings.py plan`을 빈 finding 집합으로 실행한다. 종료 코드 0, 유효 `plan.json`, 기록된 쓰기 3튜플 0건을 확인한다. 열린 PR이 없으면 `not applicable`로 기록한다.

이 저장소에는 타입 체크·린트·빌드 설정이 없다. 해당 검증 범주는 "not configured"로 기록하며, 근거는 저장소 루트에 `package.json`·`pyproject.toml`·`Makefile`·CI 워크플로가 없다는 사실이다.

## 개정 조합 검토

이 실행의 라운드 1·2 지적, 확정 설계, readiness attempt 1·3·4, 4차 실행 Claude 공식 Spec 리뷰 라운드 1의 SPEC-20~27을 함께 놓고 각각의 수정이 조합될 때 새 결손을 만드는지 다시 점검했다. 선행 Plan의 PLAN-009·010·012처럼 개별 수정은 맞았지만 조합에서 회귀한 사례가 있었으므로, 이번에는 같은 사건 집합·상태 필드·API 메서드·익명화 경계·크기 guard·AC를 양방향으로 대조했다.

| 겹치는 지점 | 관련 finding | 점검 결과 |
|---|---|---|
| R3.7의 실패 셋 ↔ R7.6a의 결손 여덟 ↔ AC-10·62·68·77 | SPEC-09, SPEC-21, SPEC-28, SPEC-31 | reviewer 실패 셋, 출처 에이전트 미성공, 범위 축소, `--base` 축소, 선택 에이전트 실패, 담당 에이전트 미선택을 정확히 여덟로 맞췄다. `S(c)=∅`인 미선택과 `S(c)≠∅ ∧ OK(c)=∅`인 실패 결손은 배타적이고, AC-10은 여섯 사건이 모두 없는 보집합만 `resolved`로 판정한다 |
| R3.5 주체 outcome ↔ R3.5a reviewer 집계 ↔ R3.7 승인 | SPEC-22 | 다섯 outcome은 `agent_outcomes`에 주체별로 기록한다. 유효 0건은 성공, Claude 일부 실패는 일부 coverage 결손, 선택 Claude 전부 실패만 reviewer `excluded`, Codex 주체 실패는 Codex `excluded`라는 술어를 AC-19·63·78이 함께 판정한다 |
| R3.10 책임표 ↔ R3.9 일부 실패/미선택 ↔ R7.6a | READY-01 (attempt 1), SPEC-21 | 다섯 agent와 일곱 category의 완전 매핑, `correctness` 중복 담당, 선택/성공/실패 집합을 하나의 상수와 상태 계산으로 공유한다. 각 agent 실패와 네 optional category 미선택을 AC-60·62·68·77이 문서→상수→상태→lifecycle 층으로 잇는다 |
| R3.10 현재 coverage ↔ R7.19 과거 `cat` | READY-01 (attempt 1), SPEC-13 | GitHub 인덱스는 `placement`를 더한 아홉 key와 기존 일곱 category enum을 유지한다. `publish_findings.py`가 과거 `cat`을 현재 상태의 `category_coverage`에 조회하므로 정적 매핑을 GitHub 이력에 중복 저장하거나 `src`에서 추측하지 않는다 |
| R6.1 실제 출처 은닉 ↔ R6.5 익명 판정 정보 ↔ R7.19 `src` 지속 | READY-02, SPEC-13 | 종합자 view에는 alias별 observations·critiques·relation을 남기고 실제 ID는 두 private sidecar에만 둔다. 종합 뒤 `finding_id`로 `finding_provenance`를 재결합하므로 분류 정보와 다음 실행의 실제 `src`를 둘 다 잃지 않고, alias는 GitHub에 게시하지 않는다(AC-23·69·70) |
| R7.5 ID 병합 ↔ R6.5 per-finding 입력 | READY-02 | 대표 finding 하나를 고르더라도 상위 reviewer group별 원 주장과 target ID로 연결된 critique는 별도 배열에 보존한다. `source_count`만 남기는 축약을 금지해 양측 합의·한쪽 단독·상호 반박이 각각 `bilateral`·`unilateral`·`contested`로 남는다 |
| R5.2 critique schema ↔ R6.5 relation ↔ R6.3 classification | READY-02 | `target_finding_id`·`stance`·non-empty evidence가 모두 유효한 critique만 relation에 들어간다. relation의 비-미결 분류를 1:1로 검증하고 `unresolved`에는 축별 사유를 요구해 enum만 맞춘 임의 분류를 막는다(AC-41·43·50·70) |
| R7.9 inline marker ↔ R7.19 summary index ↔ R7.17 복원 | SPEC-13, SPEC-20 | inline은 기존 ID marker를 유지하고 요약 인덱스가 `placement`와 나머지 metadata를 보충한다. 무효 인덱스만 전체 실패로 두고, 개별 연결 불일치는 해당 record만 격리하며, 해결된 고아 marker는 정상 종결 이력으로 무시한다. AC-65·76의 4-run 왕복에서 후속 실행도 `history_restore=ok`다 |
| R7.12 요약 성공 → inline 실패 ↔ R7.13·R7.17 실행 간 복구 | READY-01 (attempt 3) | `placement=inline`을 1단계에 지속하고 marker를 2단계 완료 증거로 분리했다. marker 0개는 `inline_pending`, 불일치·중복 marker는 `linkage_invalid`, `summary_only`는 marker 불요로 구분한다. AC-79가 로컬 상태 삭제와 다음 head를 포함한 왕복에서 정확히 한 번 복구 또는 명시적 격리를 판정한다 |
| R7.19 `fp`·`run` ↔ R7.6 lifecycle | SPEC-25 | 두 key는 형식 검증 뒤 `history_diagnostics`에만 소비한다. fp의 anchor 관계와 직전 게시 run을 관측하되 그 값만 바꾼 변이에서 lifecycle·요약 tier·쓰기 집합이 같음을 AC-75가 단정해 진단이 판정 경계로 역류하지 않게 했다 |
| R7.7 네 목록 ↔ R7.8 단일 sticky ↔ R7.19 불가분 인덱스 ↔ R7.20 크기 guard | SPEC-23 | full이 넘으면 가시 본문만 compact→minimal 순으로 줄인다. 네 목록의 모든 ID·결손 reason·필수 경고와 전체 인덱스는 보존하며, 최소 형태나 인덱스도 넘으면 sticky 분할·record 절단 없이 1단계 전 모든 쓰기를 중단한다(AC-71) |
| R2.5 로컬 재개 ↔ R7.19 실행 간 이력 | SPEC-13, SPEC-14 | 로컬은 같은 `run_id` bookkeeping만, GitHub는 head SHA를 넘는 이력만 담당하도록 경계를 분리했다. 같은 `run_id`의 플래그 충돌은 중단하고, 다른 `run_id`의 lifecycle은 GitHub에서 복원하므로 서로 대체하거나 덮어쓰지 않는다 |
| R2.1a `--base` ↔ R2.5 재실행 ↔ AC-54·61 | SPEC-14 | 최초 실행의 base 불일치 강등(AC-54)과 재개 시 고정 인자 충돌 중단(AC-61)을 별도 분기로 고정했다. `--rounds`도 같은 충돌 규칙을 쓴다 |
| R1.4 현재 브랜치 ↔ R8.2 인터페이스 ↔ AC-55 | SPEC-15 | `list_open_prs(repo, head_ref, limit)`의 서버 측 branch 필터를 명시하고 0·1·2건 분기를 고정했다. `get_pr_meta`는 정확히 한 PR 번호가 나온 뒤만 호출한다 |
| R1.4 rounds ↔ R2.5 run_id ↔ R6.4 report ↔ R9.2 후속 작업 | READY-01 (attempt 4) | AC-74·80이 rounds의 기본값·허용값·거부값을, AC-81이 exact run_id known-answer를, AC-82가 production renderer의 실제 리포트를, AC-83이 heading-scoped SARIF 후속 record를 직접 판정한다. 이 다섯 AC는 STATE/CONTRACT 명령에 배정했다 |
| R2.5 12자 ID ↔ full head 고정 | READY-01 (attempt 4) 전수 대조 | 앞 12자가 다르면 candidate ID가 달라지고, 앞 12자는 같지만 full SHA가 다른 경우 AC-61의 `run_id_prefix_collision`으로 상태 재사용을 금지한다. exact format을 지키면서 stale head 상태를 재개하지 않는다 |
| 리포트 요구 R2.1a·R3.7·R3.9·R6.3·R6.4·R10.3 ↔ renderer/게시 plan | READY-01 (attempt 4) 전수 대조 | production `render_report`와 `summary_action.body`가 같은 상태 fixture를 소비하도록 인터페이스를 고정하고 AC-82가 실제 두 출력 모두를 검사한다. 참조 문구나 golden-only 검사는 실제 리포트 단정을 대신하지 않는다 |
| R7.6a·R7.17·R7.18·R7.20·R7.21 ↔ 상태·plan 스키마 | SPEC-16, SPEC-23, SPEC-25 | 기존 `history_restore`·`coverage_gap_evidence`·`previous_reviews`·`skipped_threads`에 `history_diagnostics`·`summary_render`를 추가했다. plan은 성공 tier만, 상태는 성공 또는 oversize 오류를 담아 실패 계획을 적용 가능 객체로 위장하지 않는다 |
| R7.19 읽기 집합 ↔ R7.14 화이트리스트 ↔ R8.2·AC-49 | SPEC-13, SPEC-15 | `/pulls/{n}/reviews` 읽기를 열 번째 메서드·화이트리스트에 함께 추가하고, 게시 이력 네 목록 모두의 pagination과 부분 결과 금지를 AC-49가 판정한다. 쓰기 메서드는 네 개로 그대로다 |
| R7.6a reviewer 실패 세 행 | SPEC-26 | 표의 공통 전제가 이미 “이전 인덱스에는 있지만 현재 결과에는 없음”이므로 공허한 타 출처 부재 절을 세 행 모두에서 제외했다. `SRC_HAS`를 Codex exact member/Claude prefix existential로 닫고 세 판정식을 `reviewers[r].failure_type == <type> ∧ SRC_HAS(r, record.src)`라는 같은 형태로 고정했다 |
| R5.4 추상화 이탈 ↔ AC-22 | SPEC-27 | 두 번째 술어를 `current_critique_count >= previous_critique_count`로 고정하고, `==`이면 첫 조건과 함께 true, `<`이면 false인 경계를 직접 단정한다 |
| R7.16 ↔ D18 | SPEC-10 잔여 | D18의 실측 결론은 응답 필드 구성으로 끝내고, cross-hunk 축소는 R7.16이 정한 별도 보수적 정책이라고 다시 분리했다 |
| 요구사항 ↔ AC ↔ Test strategy | SPEC-24, READY-01 (attempt 4), 추적 완전성 | 요구사항 66건 전수 등재(누락 0·유령 0), AC 총 83건 중 메타 기준 AC-34를 뺀 82건이 추적표에 실제 판정 근거로 등장하고, 83건 전부가 판정 명령에 배정되도록 맞췄다. 각 requirement 문언을 열거값·경계/오류·상태 변화·사용자 표시 위치·금지 동작으로 분해해 매핑 AC 합집합과 대조했다. 명시된 네 결손 외에도 AC-3·19·36·45·51·54·56·61을 보강하고 R7.7에 AC-14를 연결했으며, AC 정의는 AC-1부터 AC-83까지 단조 증가한다 |

**Claude r2 반영의 조합 검토 (SPEC-28·29·30·31·32·33).** 이번 라운드의 세 High가 모두 R7.6a 하나에 수렴해 표 전체를 다시 썼다. 개별 해소를 붙이지 않고 판정 입력의 차원을 넓히는 방식으로 통합했다 — category 단위(7·8행)에 출처 에이전트 단위(4행)와 리뷰 표면 단위(5·6행)를 더하고, 그 앞에 ID 재대응 단계를 두었다.

| 교차점 | 관련 finding | 점검 결과 |
|---|---|---|
| 4행(출처 에이전트) ↔ 5·6행(경로) ↔ 7·8행(category) | SPEC-28, SPEC-31 | 세 단위가 서로 다른 입력을 본다. 5·6행은 `record.path ∉ REVIEWED`라는 **같은 술어**를 공유하고 `reason`만 원인으로 갈리며, 4행은 `SRC_AGENTS`와 `agent_outcomes`만, 7·8행은 `category_coverage`만 본다. 표는 위에서 아래로 평가하고 최초 일치를 기록하므로 겹쳐도 결정적이다 |
| ID 재대응 ↔ R7.5 병합 ↔ R7.19 인덱스 ↔ lifecycle | SPEC-32 | `fp`를 lifecycle에 들이면서 세 곳의 서술이 어긋났다. **교차 점검에서 넷을 찾아 고쳤다** — (1) R7.21 첫 문장이 여전히 "`fp`는 판정 입력이 아니다"였고, (2) R7.6의 `persisting` 정의에 재대응 경로가 없어 ID가 다른 `persisting`을 설명하지 못했으며, (3) `id_remapped`가 상태 필드 목록 두 곳에 모두 없었고, (4) R7.20의 "모든 tier에 남기는 필수 경고" 목록에 재대응 사실이 빠져 있었다. R7.5 병합은 `finding_id` 충돌만 다루므로 `fp`와 무관하고 AC-86이 그 불변을 단정한다 |
| `compact` tier 필드 집합 ↔ R7.19 아홉 key ↔ R7.20 축약 계약 | SPEC-29 | `compact`를 `full`과 같은 두 부류로 나눴다. 이어받기 record에 title을 요구하지 않는 근거가 R7.19 record의 key 구성이므로 **개수를 실측해 대조**했고, 초안에 "여덟 key"로 잘못 쓴 것을 아홉으로 정정했다. AC-71이 빈 title·지어낸 title 부재와 재렌더링 바이트 동일성을 단정한다 |
| 결손 경로 수 표기 | SPEC-28, SPEC-31 | 경로가 여섯에서 여덟로 늘면서 "여섯 결손"이 본문 11곳에 남았다. 전수 치환하고 D21의 열거, `plan.lifecycle.not_re_reviewed.reason` 집합, Failure behavior 표, 판정 명령 배정을 함께 맞췄다 |
| `finding_id` 소유 모듈 | SPEC-30 | `review_state.py` 소유로 확정하고 R8.1·R8.2·컴포넌트 표·데이터 흐름도·`test_review_state.py` 설명을 일치시켰다. 판정 명령 표에서 AC-1~3·6·72를 PUB에서 STATE로 옮겨 소유와 검증 위치를 맞췄다 |

교차 점검에서 새로 찾아 고친 것이 다섯이다(R7.21 첫 문장, R7.6 `persisting` 정의, `id_remapped` 상태 필드 두 곳, R7.20 경고 목록, "여덟 key" 오기). 어느 것도 개별 finding에는 없었고 해소들의 교차점에서만 드러났다.

조합 결과, 결손 경로는 출처 에이전트 미성공·`--base` 축소·미선택을 포함한 여덟으로 한정되고 R7.19 v1 인덱스는 `placement`를 포함한 아홉 key다. `placement`는 delivery 복구에만, `run`은 진단에만 쓴다. **`fp`는 예외로 R7.6a 단계 0의 ID 재대응 대조 키를 겸하며**, 그 한 곳 밖에서는 진단 전용이라 여덟 coverage 결손의 판정식을 바꾸지 않는다. 크기 축약은 가시 표현만 바꾸고 아홉 key의 판정 record를 보존한다. 인덱스가 상한을 넘으면 요약만 생략한 채 inline/resolve로 진행하지 않고 **전체 GitHub 쓰기 전에** 중단하므로 R7.12의 단계 순서와 다음 실행의 source of truth를 훼손하지 않는다. 반대로 유효 인덱스의 종결 고아 marker는 전체 실패가 아니어서 4-run 이후에도 새 `resolved`가 가능하다. `inline_pending`은 전역 복원을 실패시키지 않되 현재 finding으로만 복구하고, marker 불일치는 격리하므로 SPEC-20의 record 단위 안전 경계도 유지한다. 새 report renderer는 현재 state/synthesis와 plan이 이미 소비하는 값만 읽고 GitHub 이력·lifecycle·쓰기 surface를 바꾸지 않는다. 12자-prefix 충돌 검사는 로컬 상태 재개 전에만 작동해 GitHub 실행 간 이력 복원과 섞이지 않는다. 종합자용 alias는 실제 `src`를 덮어쓰지 않고 상세 provenance는 종합자에게 노출되지 않는다. API 화이트리스트와 쓰기 surface 네 메서드는 바뀌지 않았다.

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

- D21. `resolved`와 `not_re_reviewed`를 분리한다(R7.6a). 대안은 `resolved` 하나로 두고 요약에 주의 문구만 남기는 것이었으나, 그러면 `resolveReviewThread`가 여전히 호출되어 미해소 지적의 스레드가 닫힌다. 스레드 해결은 되돌리려면 사람이 GitHub에서 직접 열어야 하는 외부 쓰기이므로, 분류 자체를 나눠 호출을 막는 쪽을 택했다. 커버리지 결손 여덟 경로(R3.7(a) 프리플라이트 실패·모델 거부, R3.7(b) `excluded`, R3.7(c) 산출물 없는 종료, **출처 에이전트가 이번에 없음**, R10.2(b) 범위 축소, **`--base` 이동으로 좁아진 diff**, R3.9의 에이전트 일부 실패, category 담당 에이전트 미선택)는 R7.19에서 복원한 `src`·`path`·`cat`과 현재 상태로 판정하며, 그 앞에 R7.6a 단계 0의 `(path, cat, fp)` ID 재대응이 먼저 온다. 마지막 두 경로의 `cat` 책임은 R3.10의 versioned 상수와 현재 실행의 category coverage로만 계산하고 `S(c)=∅`과 `S(c)≠∅ ∧ OK(c)=∅`을 구분한다. GitHub 인덱스 복원이 불완전하면 `resolved`를 0건으로 만들고, 책임표/현재 상태 자체가 불일치하면 lifecycle 계산 전에 중단하는 것이 각각의 결정적 기본값이다.
- D22. 리뷰어 "실패"를 `preflight_unavailable`·`schema_excluded`·`no_output` 셋으로 열거하고 reviewer `excluded`를 뒤의 두 유형으로 결정적으로 나눈다(R3.5a, R3.7). 대안은 `excluded`를 게이트 밖에 두는 것이었으나, R6.3이 두 경로를 같은 단일 리뷰어 상태로 묶는 이상 한쪽만 승인을 요구하면 같은 상태에 두 규칙이 적용된다. 이중 리뷰가 이 스킬의 존재 이유(G1)이므로 단일 리뷰어로 끝나는 모든 경로에 같은 게이트를 건다.
- D23. `run_id`를 `<owner>-<repo>-pr<n>-<head 12자>`로 결정적으로 만들고 별도 재개 플래그를 두지 않는다(R2.5). 대안은 타임스탬프 기반 ID와 `--resume` 플래그였으나, 그러면 재실행이 직전 상태를 찾으려고 디렉터리를 뒤져야 하고 어느 것을 이어갈지가 모호해진다. 12자 SHA prefix는 같은 대상의 완료 기록을 찾는 candidate ID이고, full `head_sha`·`requested_base_ref`·해석된 `base_sha`·`actual_base_sha`·`rounds`는 상태 고정값과 대조한다. 드문 동일-prefix full-SHA 충돌도 같은 디렉터리를 조용히 재사용하지 않고 `run_id_prefix_collision`으로 중단한다(AC-61, AC-81).
- D24. head SHA를 넘는 게시 이력의 유일한 source of truth는 GitHub다(R7.19, 결정 A7). 로컬 파일은 worktree 제거에 취약하고 git notes는 별도 동기화와 이중 진실을 만들므로 채택하지 않았다. inline marker는 ID dedup과 inline 완료 증거를, sticky 요약의 표준-base64 인덱스는 `cat`·`src`·`path`·`line`·`placement`·`fp`·`run`·`lifecycle` 복원을 맡는다. 둘을 결합해 로컬 상태 없이 `summary_only`·`inline_pending`·`inline_posted`를 구분한다. `src`는 단일 문자열 대신 정렬된 배열로 두어 같은 `finding_id`로 병합된 복수 reviewer 출처를 잃지 않는다. `fp`와 `run`은 R7.21의 anchor/직전 게시 진단에 소비하되 형식 검증 뒤 lifecycle과 쓰기 판정에는 사용하지 않는다.
- D25. `AGENT_CATEGORY_MAP_V1`은 selection 표와 분리된 coverage 책임표다(R3.10, A8). `code-reviewer`를 모든 category의 catch-all로 두면 전문 에이전트 실패가 가려지고, 중복 담당자 전원 성공을 요구하면 실제로 성공한 관점도 무시한다. `code-reviewer`는 correctness/security/performance, 전문 에이전트는 자신의 도메인을 맡되 silent-failure와 type은 correctness를 중복 담당하며, 선택된 담당자 중 하나라도 성공하면 covered로 정했다. 선택 담당자가 없으면 실패로 꾸미지 않고 `agent_category_unselected`라는 별도 결손으로 둔다. 이 표는 finding category 허용 목록이 아니므로 전문 에이전트가 다른 category의 유효 finding을 내는 것을 버리지 않는다.
- D26. 같은 `finding_id` 병합 뒤의 종합자 입력은 실제 출처 제거와 분류 근거 보존을 동시에 만족해야 한다(R6.5, A9). 실제 ID를 유지하는 안은 편향 완화를 깨고, count만 남기는 안은 반박 방향·근거를 잃는다. 그래서 상위 두 reviewer group을 run-local alias로 바꾸고 group별 observations와 evidence-backed critiques를 보존하며 relation을 스크립트가 계산한다. alias 대응은 private state에, 실제 세부 provenance는 R7.19 재결합 경로에만 남긴다.

- D27. sticky 요약의 스킬 운영 상한은 최종 UTF-8 body 49,152 bytes다(R7.20). GitHub 공식 REST 문서에 body 상한이 명시되지 않았으므로 플랫폼 한계를 추정해 최대한 채우는 안은 버렸다. 단일 sticky 원칙과 완전한 판정 인덱스를 지키면서 미문서 계층에 여유를 두기 위해 48 KiB를 선택하고, 초과 시 정보 중요도가 낮은 가시 상세부터 결정적으로 줄인다. index 또는 최소 목록까지 자르는 안과 여러 코멘트로 분할하는 안은 각각 lifecycle 복원과 R7.8의 단일 sticky 계약을 깨므로, 그 지점에서는 모든 쓰기 전 실패를 선택한다.

- D28. v1의 `fp`·`run`을 제거하는 대신 진단 전용으로 유지한다(R7.21). 제거하면 index 크기는 줄지만 `placement`를 포함해 확정한 v1 아홉-key 계약과 왕복 픽스처를 바꾸고 anchor 이동 원인과 직전 게시 run을 관측할 수 없어진다. 반대로 lifecycle 키로 승격하면 제목 기반 `finding_id`와 source coverage라는 기존 판정 계약이 흔들린다. 그래서 두 값은 상태 진단으로 실제 소비하되 판정에 영향을 주지 않는 중간안을 선택한다.

- D29. R7.12의 요약→inline→resolve 순서는 유지하고 v1 record에 `placement`를 추가한다. 순서를 inline→요약으로 바꾸면 반대 실패 경계에서 marker만 있고 완전한 `cat`·`src` 인덱스가 없는 고아 상태가 먼저 생긴다. `placement`를 1단계의 durable intent, R7.9 marker와 review 연결을 2단계 완료 증거로 쓰면 기존 단계·쓰기 메서드를 늘리지 않고 두 경계를 구분한다. 추가 record bytes는 R7.20의 기존 불가분 인덱스 상한에 그대로 포함한다.

- D30. 실제 사용자 리포트의 필수 한계·경고를 오케스트레이터의 자유형식 산문에만 맡기지 않고 `review_state.py`의 결정적 `render_report` 반환값으로 고정한다. 참조 문구만 검사하는 대안은 R6.4의 실제 출력 조건을 판정하지 못하고, report 전용 golden만 비교하는 대안은 production 경로와 분리될 수 있어 채택하지 않았다. `SKILL.md`가 production 반환값을 그대로 표시하고 AC-82가 동일 fixture의 게시 요약까지 함께 검사한다.

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

통제와 그 검증: 엔드포인트 화이트리스트(AC-14), 승인 게이트(AC-15, AC-20, AC-28), 위치 실측(AC-4, AC-5), CLI rounds 경계와 exact run ID·prefix 충돌(AC-74, AC-80, AC-81), 에이전트 outcome·category 상수와 coverage 집합식(AC-60, AC-62, AC-68, AC-77, AC-78), 익명 종합 입력과 relation 검증(AC-23, AC-50, AC-69, AC-70), production 사용자 리포트의 한계·조건부 경고(AC-82), 게시 이력 strict parse·record 격리·4-run 왕복(AC-64~68, AC-76), placement/marker delivery 복구(AC-79), 요약 크기 사전 guard(AC-71), verdict 고정(AC-13), 금지 플래그 부재(AC-29), 샌드박스 read-only와 나머지 호출 플래그 존재(AC-48), 토큰 미취급(AC-31).

### Authorization and tenant isolation

멀티테넌시가 없는 단일 사용자 CLI 도구이므로 테넌트 격리는 해당 없다. 대응하는 격리 개념은 **대상 격리**다: 저장소와 PR 번호를 INTAKE에서 고정하고 `apply`가 상태의 값만 사용해, 다른 저장소·다른 PR에 게시되는 경로를 없앤다. 검증은 AC-11(SHA 재확인)과 AC-14(화이트리스트 대조)가 담당한다. 권한은 사용자의 기존 `gh` 토큰 권한을 넘지 않으며, 스킬이 권한을 상승시키거나 새 자격 증명을 만들지 않는다.

### Migration, compatibility, and rollback

신규 스킬이며 아직 v1 writer가 배포되지 않았으므로 자동 데이터 마이그레이션·백필은 없다. READY-01 해소는 출시 전 데이터 계약 교정이라 marker version은 `dual-review:index v1`을 유지하되 record를 기존 초안의 여덟 key에서 필수 `placement`를 포함한 아홉 key로 확정한다. 여덟-key 초안 payload나 `placement`가 없는 record를 실제 v1로 추측하지 않고 `invalid`로 처리해 `resolved`·resolve를 0건으로 만든다. R7.19 이전 형식처럼 요약 인덱스가 없는 게시물도 `history_unavailable`로 보이고 자동 resolve되지 않는다. 이후 새로 게시하거나 다시 발견한 finding은 아홉-key v1 인덱스로 완전 복원되지만, 메타데이터가 끝내 알려지지 않는 legacy inline marker는 ID 경고로 남아 자동 resolve 대상이 되지 않는다. 반면 정상 v1 lifecycle에서 종결 record가 인덱스에서 탈락해 생긴 고아 marker는 legacy가 아니며 R7.17의 해결됨/스레드 없음 규칙으로 무시한다. 지원하지 않는 미래 index version도 추측해 읽지 않고 같은 안전 경로를 따른다. 호환성 대상은 네 외부 계약이다: `pr-review-toolkit` 에이전트 이름 6종, `codex exec` 플래그(`--output-schema`, `--ephemeral`, `--output-last-message`, `--json`, `--sandbox`, `--model`)와 모델 식별자 `gpt-5.6-terra`, GitHub REST/GraphQL 필드, `placement`를 포함한 `dual-review:index v1` 데이터 계약. 넷 다 `docs/dual-review-maintenance.md`의 점검 대상으로 기록한다. 내부 계약인 `AGENT_CATEGORY_MAP_V1`, `SUMMARY_BODY_MAX_BYTES`, R6.5 synthesis-input shape, `render_report`의 필수 절·조건부 경고가 바뀌면 스킬 MINOR 이상을 올리고 문서·상수·픽스처를 같은 변경에서 갱신한다. 이 내부 변경은 기존 GitHub v1 인덱스의 `cat`·`src` shape를 바꾸지 않는다.

롤백 트리거와 절차:

| 트리거 | 절차 |
|---|---|
| 스킬 자체를 되돌림 | 커밋 되돌리기 후 `chezmoi apply`. 런타임 상태는 무시 경로라 필요하면 사용자가 삭제할 수 있다. 이미 게시된 v1 인덱스는 GitHub에 남지만 이전 버전이 해석하지 않는 inert HTML 주석이며 자동 삭제하지 않는다 |
| 잘못 게시된 코멘트 | **자동 롤백을 제공하지 않는다.** 게시된 코멘트의 삭제·최소화는 사용자가 GitHub UI 또는 `gh`로 직접 수행한다. 이 한계를 `references/publish-contract.md`에 명시한다 |
| 게시 중 중단 | 로컬 단계 완료 기록이 남으면 같은 `run_id` 재실행이 이를 사용한다. 기록이 사라져도 GitHub의 `placement`/marker가 요약 성공·inline 미완료 경계를 복원하므로 다음 head에서 정확히 한 번 재시도하거나 격리한다(R7.13, AC-8, AC-9, AC-79) |

### Failure recovery and observability

- 관측 지점: `.claude/dual-review-state/<run_id>/`의 `state.json`(`agent_outcomes`·`agent_category_map`·`category_coverage`·private provenance/alias sidecar·`synthesis_input`·`history_restore.findings`·`history_restore.delivery_states`·`history_diagnostics`·`coverage_gap_evidence`·`summary_render`·`skipped_threads` 포함), 리뷰어 산출물 JSON, Codex 이벤트·stderr 로그, `plan.json`, GitHub sticky 요약의 아홉-key v1 인덱스, 게시 단계 기록.
- 각 GitHub 쓰기 호출의 대상·응답 상태·생성된 코멘트 ID를 상태에 기록해, 부분 실패 후 무엇이 게시됐는지 재실행 없이 알 수 있게 한다.
- 리뷰어별 성공·실패·`excluded` 사유, 주체별 다섯 outcome, 선택된 에이전트와 유발 신호, category별 선택/성공/실패/covered 집합, 범위 축소 내역, 게시 이력 복원 상태와 finding별 최초 결손 근거, placement/marker에서 계산한 delivery status·action·reason, fp/run 진단, 요약 tier·바이트 수·oversize 오류를 상태에 남겨 결손이나 게시 불가가 조용히 숨지 않게 한다. 사용자에게 필요한 실패·축소·delivery 격리·권한 경고는 리포트와 게시 가능한 요약에도 남긴다. 종합 입력에는 alias만 남지만 private 상태에서 실제 group 대응을 진단할 수 있다.
- 알림·메트릭·트레이스는 대화형 CLI 도구에 해당하지 않는다. 사용자에게 직접 출력하는 것이 관측 수단이다.

### High-risk end-to-end verification

고위험 경로는 **PR 게시**다. 검증을 셋으로 나눈다.

1. **결정적 통합 검증(자동).** raw reviewer-output에서 시작해 주체별 다섯 outcome과 reviewer 집계, agent-category coverage, ID 병합 후 alias별 observations·critiques 보존, relation→classification 세 사례를 먼저 실행한다(AC-60, AC-69~70, AC-77~78). 이어 rounds 허용·거부 경계와 exact run ID/prefix 충돌, production 실제 리포트, 게시 lifecycle 전체(new → persisting → resolved → not_re_reviewed), index 생성→4-run 종결/고아 복원 왕복, 요약 전용 finding, 실제 coverage 상태를 사용하는 여덟 결손 경로와 복원 실패 하 resolve 0건, record 단위 연결 격리, 요약 성공→inline 실패→로컬 상태 제거→다음 head의 placement/marker 복구, fp/run 진단 비간섭, 요약 48 KiB 경계·tier·oversize 사전 중단, 네 목록 pagination, 각 게시 단계 실패 후 재실행 멱등, head SHA 불일치 중단, 재개 인자 충돌, 현재 브랜치 PR 해석, 열 메서드 화이트리스트, verdict 고정, `viewerCanResolve` 스킵을 fake GitHub 클라이언트로 실행한다. AC-7~16, AC-49, AC-51~52, AC-54~55, AC-58, AC-61~82가 이 경로다. 중단 조건: 하나라도 실패하면 해당 계약을 고친 뒤 전체 경로를 다시 돌린다.
2. **읽기 전용 실 API 검증(자동).** 검증 시점에 조회한 열린 PR을 대상으로 `plan`을 빈 finding 집합으로 실행해 실제 GitHub 응답 파싱을 검증한다(AC-37). 게시하지 않는다. 열린 PR이 없으면 `not applicable`로 기록한다.
3. **실 게시 E2E(수동, 이 워크플로에서 실행하지 않음).** 실제 `apply`는 외부 비가역 쓰기이므로 이 구현 워크플로의 자동 검증에 포함하지 않는다. 사용자가 스킬을 처음 실전 사용할 때 승인 게이트를 거쳐 첫 head SHA에서 v1 인덱스를 게시하고, 다음 head SHA 실행에서 GitHub만으로 같은 finding 집합이 복원되는지, 중복 없음·재실행 신규 0건인지 확인한다. **이 항목이 검증되지 않은 채 남는다는 사실을 리포트에 명시한다.**

### No production mutation confirmation

이 구현 워크플로는 프로덕션을 변경하지 않는다. 산출물은 `dot_claude/skills/dual-review/` 아래의 문서·스키마·스크립트·테스트, `docs/dual-review-maintenance.md`, `.gitignore` 한 줄이다. 구현 중 자동 커밋·푸시·머지·배포를 하지 않는다. GitHub에 대한 유일한 쓰기 경로는 스킬이 나중에 실행될 때의 PR 코멘트 게시이며, 그것도 사용자 승인 이후에만 일어난다. 이 워크플로의 검증 단계에서는 실제 게시를 수행하지 않는다(위 3항). AC-27은 `codex exec`를 실행하지만 `--sandbox read-only`이며 저장소를 변경하지 않는다.

<!-- strict-only:end -->
