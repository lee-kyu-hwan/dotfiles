# Quality Goal Report

- Task ID: 20260827T111202Z-28-35-create-worktree-스킬-재실행-pr-링크-입력-시-ea9373b7
- Mode: standard
- Status: NEEDS_REDESIGN
- Created: 2026-08-27T11:12:02Z
- Updated: 2026-08-27T11:12:02Z
- Source goal: #28 #35 create-worktree 스킬 재실행 — PR 링크 입력 시 2-review 세션에 PR 번호 윈도우를 생성하고 대상 세션을 직접 지정하도록 확장한다. SPEC-011(창 탐지 규칙)과 SPEC-012({이름} 정의)를 Spec 초안에 선반영한다

## Classification

선택 모드: **standard** (사용자가 `--mode=standard` 명시. 위험 스캔 결과와 동일하므로
다운그레이드 확인 불필요).

**strict 트리거 0건.** 인증·인가·테넌시, 결제·정산·쿠폰 회계, PII·보안통제·시크릿,
DB·스키마 마이그레이션·백필·파괴적 작업, 공개 API·웹훅·큐·멱등성·동시성, 프로덕션
인프라 중 어느 것도 해당하지 않는다. 변경 대상은 chezmoi 소스 트리의 Markdown/YAML
스킬 지침이며 롤백은 `git revert` + `chezmoi apply`로 단순하다. git-crypt 키 링크와
unlock은 대상 저장소의 자체 래퍼가 전담하고(`zambaguni-front/scripts/create-worktree.sh:100-160`)
이번 변경이 래퍼를 수정하지 않으므로 스킬 텍스트가 키 자료를 다루지 않는다.

**standard 조건 4가지 성립.**

1. 다중 파일·레이어 — #35가 지정한 3개 파일이 Claude/Codex 두 런타임 트리에 걸친다.
2. 인터페이스·상태 전이 변경 — 대상 세션 인자와 PR 참조 모드 추가, `argument-hint`·
   `description` 변경, 4단계 세션 선택 우선순위 신설.
3. 비자명한 신규 인터페이스 의존 — `workmux add --pr`, `workmux list --json`,
   `git fetch origin refs/pull/N/head`, `gh` 조회, `tmux list-panes -a`.
4. 대안·비범위·수용 기준의 명시 필요 — #35에 비범위 절과 완료 조건, #28에도 완료 조건이
   있으며 두 이슈를 충돌 없이 결합해야 한다.

**이슈 라벨 증거.** #35에 `enhancement` 라벨(신규 기능 요청). #28은 라벨 없음. 라벨은
보조 증거이며 위 위험 스캔 결과를 대체하지 않는다 — 스캔 단독으로도 standard가 성립한다.

**이슈 재검증.** 두 이슈 모두 OPEN, 코멘트 0건이라 선행 실행 이후 요구사항 변경이 없다.

## Review history

| 아티팩트 | 라운드 | 점수 | 판정 | 블로커 | Critical/High | 게이트 실패 사유 |
|---|---|---|---|---|---|---|
| Spec | 1 | 80 | REVISE | 0건 | 0건 | `score_below_85`, `verdict_not_pass`, `check_failed:acceptance_criteria_objective` |
| Spec | 2 | 88 | REVISE | 0건 | 0건 | `verdict_not_pass`, `check_failed:acceptance_criteria_objective` |

Plan 및 코드 리뷰 라운드는 수행되지 않았다 (Spec 단계에서 종료).

**선행 실행 대비.** 같은 목표의 2026-08-27 첫 실행은 75점(블로커 3건, High 3건) →
82점(High 2건)이었다. 이번 실행은 그 두 High를 초안에 선반영해 시작한 결과 **처음부터
블로커·High가 0건**이었고, 점수는 80 → 88로 통과선 85를 넘겼다. 남은 것은 Medium 2건
뿐이다.

**라운드 간 변화.** 라운드 1의 8건(Medium 6, Low 2)을 모두 개정했고, 라운드 2 리뷰어가
8건 전부의 해소를 증거와 함께 확인했다. 개정 과정에서 AC-9의 대체 문구에 새 결함이
생겨 SPEC-009로 잡혔고, 초안부터 있던 `--pr` 인자 정규화 누락이 SPEC-010으로 잡혔다.

스킬 규칙상 Spec 리뷰는 최대 2라운드이므로(`references/spec-rubric.md`의 "After round 2
without a passing gate, stop and record `NEEDS_REDESIGN`") 여기서 종료한다.

## Blocking-finding resolutions

**이번 실행에는 블로커로 지정된 항목이 없다.** 두 라운드 모두 `blockers` 배열이 비어
있었고 Critical/High 심각도 발견도 0건이었다. 아래는 라운드 1의 Medium/Low 8건과 그
해소 내용이며, 각 항목은 라운드 2 리뷰어가 독립적으로 해소를 확인했다.

| ID | 심각도 | 해소 내용 | 라운드 2 확인 |
|---|---|---|---|
| SPEC-001 | Medium | R7.5가 `window_id`(`@N`)를 `move-window-to-session`에 그대로 넘겼으나 그 스킬의 계약은 `<윈도우이름\|세션:번호>`다. 호출 직전 `tmux display-message -p -t "{window_id}"`로 `세션:번호`를 해석해 넘기고, worktree 경로·handle을 컨텍스트로 전달하며, 사후엔 같은 `window_id`로 재확인하도록 고쳤다(D12) | "RESOLVED. ... This matches the skill's declared contract and its internal use of {worktree경로}/{worktree명}" |
| SPEC-002 | Medium | AC-43이 R7.3(같은 세션 중복 창 금지)을 검증한다고 했으나 지목한 스모크 단계는 **다른** 세션을 써서 R7.5를 태우고 있었다. 스모크를 3차로 분리 — 1차 신규 생성, 2차 같은 세션(R7.3), 3차 다른 세션(R7.5·R2.4)(D10) | "RESOLVED. AC-46 and AC-48 now point at phases that actually create their branch conditions" |
| SPEC-003 | Medium | Goal 5의 "회귀 없음"이 검증 불가였고, 현행 규칙 중 "git-crypt 필터는 있으나 래퍼가 없는 경우"가 누락돼 있었다. R6.10으로 그 규칙을 되살리고, 보존 대상 규칙 18개를 R9.6에 열거해 AC-56으로 확인하게 했다(D14) | "RESOLVED. R6.10 restates the rule and its citation was verified accurate; R9.6 enumerates 18 preserved rules" |
| SPEC-004 | Medium | `argument-hint`만 갱신하고 `description`은 브랜치만 언급한 채였다. `description`은 에이전트가 라우팅에 쓰는 문장이라 PR 자연어 호출이 스킬에 도달하지 못할 수 있다. R9.5로 양쪽 갱신을 요구하고 AC-55로 검증(D13) | "RESOLVED. R9.5 requires updating the description frontmatter in both SKILL.md files" |
| SPEC-005 | Medium | 형식은 유효하나 사라진 저장 세션이 매 호출 무조건 중단을 유발해 자기 교정 경로가 없었다. R2.5로 4단계 복구(알림 → 기본값 제시 → 확인 후 config 갱신 → 자동 생성 금지)를 정의 | "RESOLVED. R2 priority 2 now requires the stored session to exist; R2.5 defines the four-step recovery" |
| SPEC-006 | Medium | AC-9의 "브랜치 유추 키 조회가 exit 1"이 미정의였고 우연 일치 시 올바른 구현에도 실패할 수 있었다. `workmux add --pr 31 --dry-run` 실측으로 **이 PR의 handle이 실제로 브랜치 슬러그와 같음**을 확인해 우려가 실재함을 입증하고, AC-9을 "존재하는 키가 handle 기준인지"로 바꾸며 브랜치 유추 프로브를 조건부 증거로 강등(D4) | "RESOLVED as to the original defect ... A distinct new defect in the replacement wording is filed as SPEC-009" |
| SPEC-007 | Low | R4.2가 base 저장소와 현재 저장소를 비교하는데 두 값의 출처가 미정의였다. R4.0으로 입력 형태별 `{owner}/{repo}` 확정 표와 `gh repo view` + `git remote` 폴백·중단 규칙을 추가 | "RESOLVED. R4.0 defines {owner}/{repo} resolution per input form" |
| SPEC-008 | Low | 증거 기록의 `awk`가 변수 미바인딩 형태라 출력을 낼 수 없는 명령이었고, 공백 경로 한계가 미기재였다. 실제 실행한 `-v wt="$WT"` 형태로 정정하고 R7.1에 공백 경로 한계와 그 경우의 불일치 처리를 명시 | "RESOLVED. The transcript now shows the executed form with the variable bound" |

## Plan approval

- Approval timestamp: 해당 없음 — Spec 단계에서 종료되어 Plan을 작성하지 않았다.
- Plan digest: 해당 없음.

사용자 승인 게이트(`AWAITING_PLAN_APPROVAL`)에 도달하지 않았다.

## Changed files

구현이 시작되지 않았으므로 **저장소 소스 파일 변경은 없다.** 이번 실행이 생성한 파일은
산출물 문서뿐이다.

| 경로 | 종류 | 내용 |
|---|---|---|
| `docs/development/2026-08-27-create-worktree-pr-session-2/spec.md` | 산출물 | 개정된 Spec (SHA-256 `130e179c1949748667f8e072f32bdcce00eea6c679f9472afd434eaae2654737`) |
| `docs/development/2026-08-27-create-worktree-pr-session-2/report.md` | 산출물 | 이 보고서 |

의도한 변경 대상이었으나 **손대지 않은** 파일:

- `dot_agents/skills/create-worktree/SKILL.md`
- `dot_claude/skills/create-worktree/SKILL.md`
- `dot_agents/skills/create-worktree/agents/openai.yaml`

baseline 리비전은 `6d8ccad16b4f8345130fe56913a2eead4169030f`이며, initial dirty path로
선행 실행 산출물 `docs/development/2026-08-27-create-worktree-pr-session/`이 기록되었다.
그 디렉터리는 이번 실행에서 읽기만 했고 수정하지 않았다.

## Verification evidence

구현 단계에 도달하지 않았으므로 **코드 검증은 수행되지 않았다.** 아래는 Spec 작성과
분류 근거를 위해 실제 실행한 명령이다.

### 실행한 명령

| 명령 | 종료 코드 | 증거 |
|---|---|---|
| `git rev-parse --is-inside-work-tree` | 0 | `true` |
| `codex --version` | 0 | `codex-cli 0.149.1` |
| `codex exec --sandbox read-only --ephemeral --model gpt-5.6-terra -c model_reasoning_effort="low" "Reply with one non-empty line."` | 0 | 비어 있지 않은 응답 — 선택 모델 preflight 통과 |
| `git check-ignore -v .claude/quality-state/` | 0 | `.gitignore:25` — 런타임 상태가 이미 무시됨 |
| `gh issue view 28 --json state,labels,comments` | 0 | `OPEN`, 라벨 없음, 코멘트 0건 |
| `gh issue view 35 --json state,labels,comments` | 0 | `OPEN`, `enhancement`, 코멘트 0건 |
| `quality_state.py select-resume` | 0 | `{"match":null}` — 선행 실행이 터미널이라 resume 후보 아님 |
| `workmux --version` | 0 | `workmux 0.1.248` |
| `workmux add --help` | 0 | `--pr <NUMBER\|URL>`, `--name`, `--target-name`, `--parent-session`, `--dry-run` 존재 |
| `workmux open --help` | 0 | `--pr` 없음. `--target-name`, `--parent-session` 있음 |
| `workmux list --help` | 0 | `--json` 존재 |
| `workmux list` | 0 | 디렉터리 `feat-quality-goal-skill` ↔ 브랜치 `chore/post-upgrade-skill-maintenance` (불일치 실례) |
| `workmux list --json` | 0 | `handle`, `path`, `branch`, `is_open`, `mode`, `is_main` 필드 확인 |
| `workmux add --pr 31 --dry-run` | 0 | Worktree `.../30-enhancement-tmux-open-pr-shortcut`, Target `30-enhancement-tmux-open-pr-shortcut` — **handle이 브랜치 슬러그와 일치**. 영속 변경 없음 |
| `git -C {worktree} config --get-regexp '^workmux\.worktree\.'` | 0 | `workmux.worktree.feat-quality-goal-skill.mode`, `...window-session 3-personal` |
| `git -C {worktree} config --get 'workmux.worktree.post-upgrade-skill-maintenance.window-session'` | 1 | 출력 없음 — 브랜치 유추 키는 값이 없음 |
| `tmux list-panes -a -F '...' \| awk -v wt=...` | 0 | `3-personal:2 @19 %60 {worktree경로}` — 이름 독립 매칭 성공 |
| `tmux -L quality-goal-nonexistent-socket list-sessions` | 1 | `error connecting to ...` — 서버 부재 감지 (별도 소켓, 실서버 무영향) |
| `tmux list-sessions \| grep -qxF -- 'definitely-not-a-session'` | 1 | 없는 세션 판정 |
| `tmux has-session -t 2` | 0 | 접두사 함정 재현 (세션 `2`는 없음) |
| `tmux has-session -t 2-rev` | 0 | 접두사 함정 재현 |
| `tmux list-sessions \| grep -qxF -- '2-rev'` | 1 | `grep -qxF`는 올바르게 불일치 판정 |
| `gh repo view --json owner,name -q '...'` | 0 | `lee-kyu-hwan/dotfiles` |
| `git remote get-url origin` | 0 | `git@github.com:lee-kyu-hwan/dotfiles.git` |
| `gh pr view 31 --json state,headRefName,headRefOid` | 0 | `OPEN`, `30-enhancement/tmux-open-pr-shortcut`, `9cfc6267ced574945814536710cf1019a37dc354` |
| `git ls-remote origin '30-enhancement/tmux-open-pr-shortcut'` | 0 | `9cfc6267...` — 원격 head 생존 |
| `git ls-remote origin 'refs/pull/31/head'` | 0 | `9cfc6267...` 동일 |
| `gh pr view 32 --json state,headRefName` | 0 | `OPEN`, `feat/codex-playwright-e2e-profile` |
| `git config --get filter.git-crypt.smudge` (dotfiles) | 1 | 값 없음 — git-crypt 아님 |
| `git config --get filter.git-crypt.smudge` (zambaguni-front) | 0 | `"git-crypt" smudge` |
| `quick_validate.py dot_agents/skills/create-worktree` | 0 | `Skill is valid!` |
| `quick_validate.py dot_claude/skills/create-worktree` | 0 | Claude 전용 키 안내 출력, 종료 코드는 0 |
| `sed -n 3p` 두 SKILL.md | 0 | `description` 양쪽 동일, 브랜치만 언급 |
| `validate_review.py validate` (라운드 1) | 0 | `{"valid":true,"errors":[]}` |
| `validate_review.py gate` (라운드 1) | 3 | `score_below_85`, `verdict_not_pass`, `check_failed:acceptance_criteria_objective` |
| `validate_review.py validate --prior` (라운드 2) | 0 | `{"valid":true,"errors":[]}` |
| `validate_review.py gate --prior` (라운드 2) | 3 | `verdict_not_pass`, `check_failed:acceptance_criteria_objective` — **점수는 통과** |

### 검증 카테고리 상태

| 카테고리 | 상태 | 근거 |
|---|---|---|
| 표적 테스트 | `not configured` | `package.json`, `Makefile`, `justfile` 부재 확인 |
| 전체 스위트 | `not configured` | 같음 |
| 타입 체크 | `not configured` | 같음 |
| 린트 | `not configured` | `.pre-commit-config.yaml`에 gitleaks 훅만 존재 (시크릿 스캔 전용) |
| 빌드 | `not configured` | `package.json`, `.github/workflows` 부재 확인 |
| E2E / 수동 검증 | **미실행** | 구현 단계에 도달하지 않아 Spec의 3층 스모크 테스트(dotfiles PR #31, 1~3차)를 실행하지 않았다. 통과로 기록하지 않는다. 다만 `--dry-run`으로 예상 산출물은 부작용 없이 확인했다 |

## Remaining advisory findings

### Medium (게이트 실패에 기여)

| ID | 요약 | 영향 | 후속 조치 |
|---|---|---|---|
| SPEC-009 | AC-9의 대체 문구가 교란되어 올바른 구현에도 실패한다. workmux는 worktree 키를 **공유 저장소 config**에 handle로 구분해 쓰므로(`move-window-to-session/SKILL.md:113-115`), `git config --get-regexp '^workmux\.worktree\.'`는 저장소의 **모든** worktree 키를 돌려준다. 스모크 시점에 `workmux.worktree.feat-quality-goal-skill.*`가 남아 있어 "모든 키가 테스트 대상 handle 기준"이 성립하지 않는다. 반대로 대상 worktree로 범위를 좁히면 이번 케이스는 handle == 브랜치 슬러그라 동어반복이 된다 | R2.0의 유추 금지 규칙이 실행으로 검증되지 않는다 | (a) 키 단언을 테스트 대상 worktree로 한정하고 무관한 handle은 명시적으로 무시할 것. (b) handle == 브랜치 슬러그일 때도 판별력이 남는 프로브를 추가할 것 — 예를 들어 handle(`feat-quality-goal-skill`)과 브랜치(`chore/post-upgrade-skill-maintenance`)가 다른 **기존 worktree**에 대한 읽기 전용 검사. 그 worktree의 브랜치 유추 키가 exit 1임은 이미 실측되어 있다 |
| SPEC-010 | `workmux add --pr {PR참조}`가 원시 사용자 입력을 그대로 넘긴다. `--pr`의 계약은 `<NUMBER\|URL>`인데(Spec 자신의 사실표 실측) R1.4가 허용하는 세 형태 중 `{owner}/{repo}#{번호}`와 표지 있는 자연어는 workmux가 거부한다. R4.0·R4.1이 번호와 저장소를 이미 분해하지만, `--pr`에 도달하기 전 정규화한다는 요구사항이 없다 | 세 입력 형태 중 둘이 실패한다 | PR 참조를 R4.0·R4.1이 확정한 `{번호}`(저장소가 다르면 정규 URL)로 환원하는 단계를 명시하고, R6.3과 Interfaces 블록을 `--pr {PR번호}`로 바꿀 것. 정규화된 값이 명령에 들어가는지 확인하는 AC를 추가할 것 |

### 프로세스 관찰

**#44 우회 효과.** 선행 실행에서 라운드 2 리뷰어가 이전 라운드 findings를 검증하지
못했던 문제(이슈 #44)를 이번에는 finding ID와 함께 **설명 원문과 적용한 해소 내용**을
전달해 우회했다. 그 결과 라운드 2 리뷰어가 8건 전부의 해소를 개별 증거와 함께 확인했고,
"새 finding이 이전 항목을 재진술했을 가능성" 같은 불확실성이 사라졌다. 이 우회는
`Review invocation contract`의 "prior open finding IDs" 규정을 넘어서므로, 계약 자체를
넓힐지는 #44에서 다룰 사안이다.

**`required_sections` 게이트 항목의 근거 부재.** 라운드 2 리뷰어가 이 항목을 확정하지
못했다고 기록했다 — `spec-rubric.md:16`이 항목 이름만 대고 필수 섹션 목록을 열거하지
않기 때문이다. 오케스트레이터는 `templates/spec.md`와 대조해 11개 섹션이 모두 존재함을
확인했고 `true`로 기록했으나, 리뷰어가 독립적으로 확인할 수단이 없다. 루브릭에 목록을
넣는 것이 후속 조치다.

### 위생 항목

`.claude/quality-state/`는 `.gitignore:25`에 이미 등록되어 있어 런타임 상태가
`git status`에 노출되지 않는다. 별도 조치가 필요 없다.

### quality-goal 스킬 결함 재확인 (#43)

이 보고서를 `set-artifact --kind report`로 등록하지 못했다. 상태 파일의
`artifacts.report`는 `null`로 남아 있다. `record-review`가 라운드 한도 소진을 감지하면
스스로 `NEEDS_REDESIGN`으로 전이하고(`quality_state.py:590,595`), 그 뒤에는
`terminal state is immutable`로 `set-artifact`가 거부된다. SKILL.md가 요구하는
"터미널 전이 **전에** 보고서 등록"을 지킬 수 있는 시점이 존재하지 않는다. 선행 실행에서
발견해 이슈 #43으로 접수된 결함이며 이번 실행에서 동일하게 재현되었다. 알려진 결함이라
우회를 시도하지 않았다.

보고서 파일 자체는 정상 경로
`docs/development/2026-08-27-create-worktree-pr-session-2/report.md`에 존재한다.

## Final status

- Status: `NEEDS_REDESIGN`
- Machine-readable reason: `REVIEW_LIMIT_EXHAUSTED:spec`

Spec 리뷰가 규정된 최대 2라운드를 소진했고 두 라운드 모두 게이트를 통과하지 못했다.
다만 실패의 성격이 선행 실행과 다르다.

| 항목 | 선행 실행 | 이번 실행 |
|---|---|---|
| 최종 점수 | 82 (통과선 85 미달) | **88 (통과선 초과)** |
| 블로커 | 3건 → 0건 | **0건 → 0건** |
| Critical/High | 3건 → 2건 | **0건 → 0건** |
| 게이트 실패 사유 | `score_below_85`, `verdict_not_pass`, `critical_or_high_finding` | `verdict_not_pass`, `check_failed:acceptance_criteria_objective` |

점수와 심각도 기준은 모두 충족했고, 남은 실패 사유는 리뷰어 판정이 `PASS`가 아니라는
것과 그에 대응하는 결정적 체크 하나다. 그 체크(`acceptance_criteria_objective`)를
`false`로 기록한 근거가 SPEC-009 단 하나이며, 그 하나가 `verdict`를 `REVISE`로 묶고
있다.

구현은 시작되지 않았고 저장소 소스 파일은 변경되지 않았다. 사용자 승인 게이트에도
도달하지 않았다.

**남은 작업의 성격.** SPEC-009는 AC 하나의 판정식 문제이고, SPEC-010은 `--pr`에 넘길
값을 정규화하라는 한 줄짜리 요구사항 추가다. 둘 다 해법이 리뷰어의 `required_resolution`에
구체적으로 적혀 있고, SPEC-009의 판별 프로브에 쓸 데이터(handle과 브랜치가 다른 기존
worktree)는 이미 실측되어 있다. 다음 실행에서 이 둘을 초안에 선반영하면 라운드 1에서
통과할 가능성이 높다 — 이번 실행이 선행 실행의 High 2건을 선반영해 블로커 0건으로
시작했던 것과 같은 방식이다.
