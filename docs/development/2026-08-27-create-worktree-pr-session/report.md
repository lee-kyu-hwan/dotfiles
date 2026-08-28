# Quality Goal Report

- Task ID: 20260827T080329Z-28-35-create-worktree-스킬에-pr-링크-입력-시-2-r-6b97d528
- Mode: standard
- Status: NEEDS_REDESIGN
- Created: 2026-08-27T08:03:29Z
- Updated: 2026-08-27T08:03:34Z
- Source goal: #28 #35 create-worktree 스킬에 PR 링크 입력 시 2-review 세션에 PR 번호 윈도우를 생성하고 대상 세션을 직접 지정할 수 있도록 확장한다

## Classification

선택 모드: **standard** (요청 모드 `auto`).

**strict 트리거 없음.** 인증·인가·테넌시, 결제·정산·쿠폰 회계, PII·보안통제·시크릿,
DB·스키마 마이그레이션·파괴적 작업, 공개 API·웹훅·큐·멱등성·동시성, 프로덕션 인프라
중 어느 것도 해당하지 않는다. 변경 대상은 chezmoi 소스 트리의 Markdown 스킬 지침이며
롤백은 `git revert` + `chezmoi apply`로 단순하다. git-crypt 키 링크는 대상 저장소의
자체 래퍼에 위임되어 있고(`dot_claude/skills/create-worktree/SKILL.md:116`) 이번 변경이
그 흐름을 보존하므로 스킬 텍스트가 키 자료를 직접 다루지 않는다.

**standard 조건 4가지가 모두 성립.**

1. 다중 파일·레이어 — 이슈 #35 "변경 대상"이 `dot_agents/skills/create-worktree/SKILL.md`,
   `dot_agents/skills/create-worktree/agents/openai.yaml`,
   `dot_claude/skills/create-worktree/SKILL.md` 3개 파일을 지정하며 Claude/Codex 두
   런타임 트리에 걸친다.
2. 인터페이스·상태 전이 변경 — 스킬 입력 계약에 선택적 대상 세션 인자와 PR URL 모드가
   추가되고, Claude frontmatter `argument-hint`가 바뀌며, 4단계 세션 선택 우선순위가
   신설된다.
3. 비자명한 신규 인터페이스 의존 — `workmux add --pr <NUMBER|URL>` (workmux 0.1.248에
   실재 확인) 및 git-crypt 경로의 `gh` PR 메타데이터 조회.
4. 대안·비범위·수용 기준의 명시 필요 — #35에 "비범위" 절과 완료 조건이 있고 #28에도
   완료 조건이 있으며, 두 이슈를 충돌 없이 결합해야 한다.

**이슈 사실 검증 편차 1건.** 이슈 #35는 "두 원본의 차이가 Claude frontmatter뿐"이라고
전제하나, 실측 `diff`에서 frontmatter 3줄 외에 workmux 버전 표기 문구가 1줄 다르다
(`dot_agents:43` "0.1.233 실측" vs `dot_claude:46` "0.1.233 확인·0.1.248 재확인").
Spec의 D5로 처리 방침을 정했다.

## Review history

| 아티팩트 | 라운드 | 점수 | 판정 | 블로커 | 게이트 |
|---|---|---|---|---|---|
| Spec | 1 | 75 | REVISE | SPEC-001, SPEC-002, SPEC-003 | 실패 — `score_below_85`, `verdict_not_pass`, `blockers_present`, `critical_or_high_finding`, `check_failed:acceptance_criteria_objective` |
| Spec | 2 | 82 | REVISE | (없음) | 실패 — `score_below_85`, `verdict_not_pass`, `critical_or_high_finding` |

Plan 및 코드 리뷰 라운드는 수행되지 않았다 (Spec 단계에서 종료).

**라운드 간 변화.** 라운드 1의 블로커 3건과 Medium/Low 7건을 모두 개정했고, 라운드 2
리뷰어가 SPEC-001·002·003·004·009의 해소를 증거와 함께 확인했다. 점수는 75 → 82로
올랐으나 통과 기준 85에 미달했고, 개정 과정에서 드러난 새로운 High 2건(SPEC-011,
SPEC-012)이 남았다. 스킬 규칙상 Spec 리뷰는 최대 2라운드이므로
(`references/spec-rubric.md`의 "After round 2 without a passing gate, stop and record
`NEEDS_REDESIGN`") 여기서 종료한다.

## Blocking-finding resolutions

| ID | 라운드 | 심각도 | 해소 내용 | 검증 증거 |
|---|---|---|---|---|
| SPEC-001 | 1 | High | git-crypt 래퍼 경로에서 PR head 브랜치를 확보하는 방법이 미정의였다. R4.6(`git fetch origin refs/pull/{N}/head:{head브랜치명}` + `git rev-parse --verify`)과 R6.8(생성 후 `HEAD == headRefOid` 검증)을 추가하고, 실패 행 3개와 AC-21·AC-34를 신설했다 | 라운드 2 리뷰어 확인: "R4.6 now mandates ... and R6.8 adds post-creation HEAD==headRefOid verification. The stated basis is accurate." 근거는 `zambaguni-front/scripts/create-worktree.sh:82-98`을 직접 읽어 확인 — 브랜치가 로컬·`origin` 양쪽에 없으면 현재 HEAD에서 `-b`로 빈 브랜치를 만든다 |
| SPEC-002 | 1 | High | R4.3의 무조건 중단이 R7 창 처리와 모순이었다. "생성 단계만 건너뛰고 R7으로 진행"으로 재정의하고(D7), 흐름도 분기 순서를 `worktree 판정(R7.0) → 세션 선택(R2)`으로 교정했으며, 실패 표에 "중단이 아님" 행을 넣었다 | 라운드 2 리뷰어 확인: "R4.3 now says only the creation step is skipped and control passes to R7 window handling, the flow diagram step 7 matches, the failure table row states '중단이 아님', and D7 records the departure from issue #28's literal wording." |
| SPEC-003 | 1 | High | 18개 요구사항에 대응 AC가 없었다. 요구사항을 51개(R1.1–R9.4)로 정리하고 AC를 48개로 확장한 뒤 "요구사항 전수 대응 확인" 목록을 추가했다 | 라운드 2 리뷰어 확인: "all 51 requirements ... appear in the requirement-to-AC mapping list with no omissions; I enumerated both lists and they match." |

라운드 2에는 블로커로 지정된 항목이 없다. 아래 "Remaining advisory findings"의 SPEC-011·
SPEC-012는 High 심각도이나 리뷰어가 `blockers` 배열에 넣지 않았고
`new_blocker_evidence`도 제공하지 않았다. 게이트는 `critical_or_high_finding` 사유로
실패했다.

### 라운드 1의 Medium/Low 해소

| ID | 심각도 | 해소 내용 |
|---|---|---|
| SPEC-004 | Medium | `1-main` 잔존 검사를 리터럴 grep에서 전수 감사(허용 3용례 / 금지 5용례 목록)로 확장. 라운드 2 리뷰어가 해소 확인 |
| SPEC-005 | Medium | PR #31의 가용성을 실측으로 기록(`state=OPEN`, 원격 head `9cfc6267...` 생존, `refs/pull/31/head` 동일 OID)하고 대체 계획을 명시. 리뷰어의 "이미 머지되었을 것" 우려는 실측으로 반증됨 |
| SPEC-006 | Medium | 고위험 3건(유령 세션 방지·tmux 서버 부재 구분·접두사 함정)을 문서 존재 검사에서 부작용 없는 실행 검사로 승격. 세 명령의 종료 코드를 실측 |
| SPEC-007 | Medium | 명시 세션이 유효 저장값을 덮었을 때의 git config 갱신 규칙을 R2.4로 신설 |
| SPEC-008 | Medium | 자연어 호출을 2-튜플로 환원하는 규칙(R1.6)과 "표지 있는 숫자"로 R1.5와의 모순을 해소(D2) |
| SPEC-009 | Medium | PR 모드 충돌 재시도 이름을 `{PR번호}-{repo명}-{짧은이름}`으로 분리해 PR 번호를 보존(R5.6). 라운드 2 리뷰어가 해소 확인 |
| SPEC-010 | Low | `quick_validate.py`의 절대 경로와 파일별 실측 기준선을 명시. `dot_claude`는 Claude 전용 키 안내가 나오지만 exit 0임을 기록 |

SPEC-005·006·007·008·010은 라운드 2 리뷰어가 **검증하지 못했다** — 리뷰 호출 계약이
"prior open finding IDs"만 전달하도록 규정되어 있어 라운드 1의 설명 원문이 전달되지
않았기 때문이다. 리뷰어는 이를 `NOT VERIFIED`로 명시하고, 새 findings가 이들 중 하나를
재진술했을 가능성을 배제할 수 없다고 기록했다. 오케스트레이터가 대조한 결과 SPEC-011·
SPEC-012는 라운드 1의 어느 항목과도 일치하지 않는 새 발견이다.

## Plan approval

- Approval timestamp: 해당 없음 — Spec 단계에서 종료되어 Plan을 작성하지 않았다.
- Plan digest: 해당 없음.

사용자 승인 게이트(`AWAITING_PLAN_APPROVAL`)에 도달하지 않았다.

## Changed files

구현이 시작되지 않았으므로 **저장소 소스 파일 변경은 없다.** 이번 실행이 생성한 파일은
산출물 문서뿐이다.

| 경로 | 종류 | 내용 |
|---|---|---|
| `docs/development/2026-08-27-create-worktree-pr-session/spec.md` | 산출물 | 개정된 Spec (SHA-256 `8f001e7553c9c6fe707c20af9dc8925f3d10543a92a687335047ad8c75378693`) |
| `docs/development/2026-08-27-create-worktree-pr-session/report.md` | 산출물 | 이 보고서 |

의도한 변경 대상이었으나 **손대지 않은** 파일:

- `dot_agents/skills/create-worktree/SKILL.md`
- `dot_claude/skills/create-worktree/SKILL.md`
- `dot_agents/skills/create-worktree/agents/openai.yaml`

baseline 리비전 `6d8ccad16b4f8345130fe56913a2eead4169030f` 기준으로 사전 dirty 경로는
없었고, 현재도 위 3개 파일은 수정되지 않았다.

## Verification evidence

구현 단계에 도달하지 않았으므로 **코드 검증은 수행되지 않았다.** 아래는 Spec 작성과
분류 근거를 위해 실제 실행한 명령이다.

### 실행한 명령

| 명령 | 종료 코드 | 증거 |
|---|---|---|
| `git rev-parse --is-inside-work-tree` | 0 | `true` |
| `codex --version` | 0 | `codex-cli 0.149.1` |
| `codex exec --sandbox read-only --ephemeral --model gpt-5.6-terra -c model_reasoning_effort="low" "Reply with one non-empty line."` | 0 | `Acknowledged.` — 선택 모델 preflight 통과 |
| `git check-ignore -v .claude/quality-state/` | 0 | `.gitignore:25:.claude/quality-state/` — 런타임 상태가 이미 무시됨 |
| `workmux --version` | 0 | `workmux 0.1.248` |
| `workmux add --help` | 0 | `--pr <NUMBER\|URL>` 존재. `[BRANCH_NAME] ... When used with --pr, this becomes the custom local branch name` |
| `workmux open --help` | 0 | `--pr` 없음. `--target-name`, `--parent-session` 존재 |
| `tmux list-sessions -F '#{session_name}'` | 0 | `1-main`, `2-review`, `3-personal`, `4-eslint`, `5-quick` |
| `tmux -L quality-goal-nonexistent-socket list-sessions` | 1 | `error connecting to /private/tmp/tmux-501/quality-goal-nonexistent-socket (No such file or directory)` — 서버 부재 감지 근거 |
| `tmux list-sessions -F '#{session_name}' \| grep -qxF -- 'definitely-not-a-session'` | 1 | 없는 세션 판정 근거 |
| `tmux has-session -t 2` | 0 | 접두사 함정 재현 — 세션 `2`는 없으나 exit 0 |
| `tmux has-session -t 2-rev` | 0 | 접두사 함정 재현 |
| `tmux list-sessions -F '#{session_name}' \| grep -qxF -- '2-rev'` | 1 | `grep -qxF`가 올바르게 불일치 판정 |
| `gh pr view 31 --repo lee-kyu-hwan/dotfiles --json state,headRefName,headRefOid` | 0 | `state=OPEN`, `30-enhancement/tmux-open-pr-shortcut`, `9cfc6267ced574945814536710cf1019a37dc354` |
| `git ls-remote origin '30-enhancement/tmux-open-pr-shortcut'` | 0 | `9cfc6267...` — 원격 head 브랜치 생존 |
| `git ls-remote origin 'refs/pull/31/head'` | 0 | `9cfc6267...` — 동일 OID |
| `gh pr view 32 --repo lee-kyu-hwan/dotfiles --json state,headRefName` | 0 | `state=OPEN`, `feat/codex-playwright-e2e-profile` |
| `git config --get filter.git-crypt.smudge` (dotfiles) | 1 | 값 없음 — git-crypt 아님. `scripts/create-worktree.sh`도 부재 |
| `git config --get filter.git-crypt.smudge` (zambaguni-front) | 0 | `"git-crypt" smudge` — 래퍼 존재 |
| `quick_validate.py dot_agents/skills/create-worktree` | 0 | `Skill is valid!` |
| `quick_validate.py dot_claude/skills/create-worktree` | 0 | `Unexpected key(s) in SKILL.md frontmatter: argument-hint, user-invocable.` — 종료 코드는 0 |
| `diff dot_agents/.../SKILL.md dot_claude/.../SKILL.md` | 1 | `3a4,6` (frontmatter 3줄) + 43/46행 버전 표기 1줄 |
| `validate_review.py validate --input spec-review-round1.json --artifact spec` | 0 | `{"valid":true,"errors":[]}` |
| `validate_review.py gate --input spec-review-round1.json --checks spec-checks-round1.json` | 3 | `{"passed":false,...}` |
| `validate_review.py validate --input spec-review-round2.json --artifact spec --prior ...` | 0 | `{"valid":true,"errors":[]}` |
| `validate_review.py gate --input spec-review-round2.json --checks spec-checks-round2.json --prior ...` | 3 | `{"passed":false,"reasons":["score_below_85","verdict_not_pass","critical_or_high_finding"]}` |

### 검증 카테고리 상태

| 카테고리 | 상태 | 근거 |
|---|---|---|
| 표적 테스트 | `not configured` | `package.json`, `Makefile`, `justfile` 부재 확인 |
| 전체 스위트 | `not configured` | 같음 |
| 타입 체크 | `not configured` | 같음 |
| 린트 | `not configured` | `.pre-commit-config.yaml`에 gitleaks 훅만 존재 (시크릿 스캔 전용) |
| 빌드 | `not configured` | `package.json`, `.github/workflows` 부재 확인 |
| E2E / 수동 검증 | **미실행** | 구현 단계에 도달하지 않아 Spec의 3층 스모크 테스트(dotfiles PR #31)를 실행하지 않았다. 통과로 기록하지 않는다 |

## Remaining advisory findings

### High (게이트 실패 사유)

| ID | 요약 | 영향 | 후속 조치 |
|---|---|---|---|
| SPEC-011 | R7.1–R7.4이 "창이 열려 있는지, 어느 세션인지"로 분기하지만 **그것을 판정하는 방법이 미정의**다. R7.0은 worktree 경로만 얻고, `tmux list-windows -a`는 R8.1의 사후 검증에만 등장한다. PR 모드에서 특히 위험하다 — 브랜치 모드로 먼저 만든 worktree의 창 이름은 `30-tmux-open-pr-shortcut`인데 PR 모드는 `31-tmux-open-pr-shortcut`을 파생하므로 이름 기반 매칭은 열린 창을 놓치고 R7.2(중복 창 금지)가 조용히 실패한다 | 중복 창 생성, 살아 있는 에이전트 pane 유실 가능 | R7에 창 탐지 규칙(명령과 매칭 키)을 신설하고, 창 이름이 다른 규칙으로 파생된 경우를 명시적으로 다룰 것. 규칙 텍스트만으로 충족되지 않는 AC를 붙일 것 |
| SPEC-012 | `workmux.worktree.{이름}.window-session`의 `{이름}` 자리표시자가 **정의되지 않았다**. `move-window-to-session` 스킬은 이것이 `workmux list`의 `PATH` 열 basename이며 브랜치나 창 이름에서 유추하면 안 된다고 명시한다 — 틀린 키를 넘겨도 git이 오류 없이 새 섹션을 만들고 실제 키는 옛 값을 유지하기 때문이다. PR 모드는 창 이름·디렉터리명·브랜치가 모두 달라 이 위험이 커진다 | 저장값 읽기가 빈 값이 되어 모드 기본값으로 떨어지고, D1/R2.1이 막으려던 "의도적으로 옮긴 창을 되끌고 옴"이 그대로 재발 | R2 또는 Interfaces 절에서 `{이름}`을 `workmux list` PATH basename으로 정의하고 유추 금지를 명시할 것. 스모크 테스트에서 실제 기록된 키가 그 이름과 일치하는지 관찰하는 AC를 추가할 것 |

### Medium

| ID | 요약 | 영향 | 후속 조치 |
|---|---|---|---|
| SPEC-013 | AC-11이 R2.4(명시 세션이 저장값을 덮고 config를 갱신)를 `[실행]`으로 커버한다고 주장하지만, 정의된 스모크 테스트는 세션 미명시 실행 1회뿐이다. 그 관찰은 workmux가 쓴 모드 기본값을 볼 뿐 덮어쓰기 경로를 실행하지 않는다 | R2.4가 실제로는 문서 검토로만 검증됨 | 저장값과 다른 세션을 명시하는 2차 스모크 단계를 추가하거나, AC-11의 실행 주장을 축소하고 잔여 격차를 한계로 기록할 것 |

### Low

| ID | 요약 | 영향 | 후속 조치 |
|---|---|---|---|
| SPEC-014 | R4.1/AC-16이 `state`, `isCrossRepository`, `headRepositoryOwner`, `url`을 요구하지만 이를 소비하는 규칙이 없다. CLOSED/MERGED PR에 대한 동작이 미정의이고, fork 판별은 R4.6의 pull ref가 균일하게 처리하므로 `isCrossRepository`에 소비자가 없다 | 조회 형식과 사용 규칙이 어긋남 | `state`를 소비하는 규칙(CLOSED/MERGED 경고·확인)을 추가하거나 미사용 필드를 제거할 것 |
| SPEC-015 | `{디렉토리명}`(R6.4)과 `{worktree경로}`(R6.8) 획득 방법이 `workmux add --pr` 경로에 대해 미정의다. 또한 정리 절차의 `workmux remove` 뒤 `git branch -D`는 중복이다 — `remove-worktree` 스킬은 `workmux remove`가 이미 로컬 브랜치를 지운다고 기록한다 | 정리 중 오류 메시지 발생 | 각 생성 경로별 경로 획득 방법을 명시하고, 브랜치 삭제를 조건부로 서술할 것 |

### 프로세스 관찰

라운드 2 리뷰어가 SPEC-005·006·007·008·010을 검증하지 못했다. 리뷰 호출 계약이 이전
라운드의 **finding ID만** 전달하도록 규정되어 있어(`Review invocation contract`의
"prior open finding IDs on rounds >= 2") 설명 원문과 증거 위치가 리뷰어에게 가지 않았기
때문이다. 리뷰어는 자신의 새 findings가 이전 항목을 재진술했을 가능성을 배제할 수
없다고 명시했다. 이 계약 자체를 넓힐지는 이 작업의 범위 밖이며, quality-goal 스킬
유지보수 항목으로 남긴다.

### 위생 항목

`.claude/quality-state/`는 `.gitignore:25`에 이미 등록되어 있어 런타임 상태가
`git status`에 노출되지 않는다. 별도 조치가 필요 없다.

### quality-goal 스킬 자체의 순서 결함 (실측)

이 보고서를 `set-artifact --kind report`로 등록하지 못했다. 상태 파일의
`artifacts.report`는 `null`로 남아 있다.

원인: `SKILL.md`는 "Render report.md ... and register it with `set-artifact --kind
report` **BEFORE** transitioning into the terminal state"를 요구하지만,
`scripts/quality_state.py`의 `record-review`가 라운드 한도 소진을 감지하면
**스스로 `NEEDS_REDESIGN`으로 전이한다**(`quality_state.py:590,595`). 전이 후에는
`terminal state is immutable: NEEDS_REDESIGN` 오류로 `set-artifact`가 거부된다
(재현: exit 3). 즉 오케스트레이터가 규정된 순서를 지킬 수 있는 시점이 존재하지 않는다.

동일한 문제가 `BLOCKED`(리뷰 출력 2회 무효 시)에서도 발생할 것으로 보인다 — 같은 함수가
같은 방식으로 전이한다.

**후속 조치 제안** (이 작업 범위 밖, `docs/quality-goal-maintenance.md` 항목):
`record-review`의 자동 전이를 제거하고 오케스트레이터가 보고서 등록 후 명시적으로
`transition`하게 하거나, 터미널 상태에서도 `set-artifact --kind report`만은 허용할 것.
현 상태로는 모든 NEEDS_REDESIGN·BLOCKED 종료에서 보고서 포인터가 유실된다.

보고서 파일 자체는 정상 경로
(`docs/development/2026-08-27-create-worktree-pr-session/report.md`)에 존재한다.

## Final status

- Status: `NEEDS_REDESIGN`
- Machine-readable reason: `SPEC_REVIEW_ROUND_LIMIT_REACHED_WITHOUT_PASS`

Spec 리뷰가 규정된 최대 2라운드를 소진했고 두 라운드 모두 게이트를 통과하지 못했다
(라운드 1: 75점 / 블로커 3건, 라운드 2: 82점 / High 2건, 통과 기준 85점 및 High 0건).
`references/spec-rubric.md`의 "After round 2 without a passing gate, stop and record
`NEEDS_REDESIGN`" 규칙에 따라 종료한다.

구현은 시작되지 않았고 저장소 소스 파일은 변경되지 않았다. 사용자 승인 게이트에도
도달하지 않았다.

**남은 작업의 성격.** 두 High 항목은 Spec의 근본 설계 결함이 아니라 **미정의 구간**이다
— 창 탐지 방법(SPEC-011)과 `{이름}` 자리표시자의 정의(SPEC-012)를 채우면 해소된다.
두 항목 모두 `move-window-to-session` 스킬이 이미 답을 갖고 있다(창 매칭은
`workmux list` PATH basename, 유추 금지 근거는 그 스킬의 104-108행). 다음 실행에서는
이 두 정의를 Spec 초안에 미리 반영한 상태로 시작하는 것이 합리적이다.
