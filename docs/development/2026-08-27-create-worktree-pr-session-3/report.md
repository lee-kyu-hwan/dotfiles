# Quality Goal Report

- Task ID: 20260827T120102Z-28-35-create-worktree-스킬-3차-실행-pr-링크-입력-a16ed82b
- Mode: standard (요청 auto)
- Status: NEEDS_REDESIGN
- Created: 2026-08-27T12:01:02Z
- Updated: 2026-08-28
- Source goal: #28 #35 create-worktree 스킬 3차 실행 — PR 링크 입력 시 `2-review` 세션에 PR 번호 윈도우를 생성하고 대상 세션을 직접 지정하도록 확장한다. SPEC-009(AC-9 판별력)과 SPEC-010(`--pr` 정규화)를 선반영하고, 휘발성 식별자를 증거에서 제거한다

## Classification

`auto` 요청에 대해 strict 위험 스캔 결과 트리거 0건(인증·인가, 결제·정산, PII·시크릿, DB 마이그레이션, 공개 API·큐, 프로덕션 인프라 모두 해당 없음)이었다. 변경 대상은 chezmoi 소스 트리의 Markdown/YAML 스킬 지침이고 롤백은 `git revert` + `chezmoi apply`로 단순하다. git-crypt는 대상 저장소의 자체 래퍼가 전담하며 이번 변경이 래퍼를 수정하지 않으므로 strict 사유가 되지 않는다.

standard 조건은 복수로 성립했다.

1. **다중 파일·레이어** — #35가 지정한 변경 대상 3개 파일이 Claude/Codex 두 런타임 트리에 걸친다
2. **인터페이스·상태 전이 변경** — 선택적 대상 세션 인자와 PR 참조 모드가 추가되고, 4단계 세션 선택 우선순위가 신설된다
3. **비자명한 신규 의존** — `workmux add --pr`, `workmux list --json`, `git fetch origin refs/pull/N/head`, `gh pr view`, `tmux list-panes -a`
4. **대안·비범위·수용 기준 명시 필요** — #35에 '비범위' 절이 있고 두 이슈를 충돌 없이 결합해야 한다

3차 실행 맥락: 2차 실행이 라운드 한도로 종료되며 남긴 Medium 2건을 선반영하고, 2차 Spec이 **이후 제거된 worktree를 근거로 삼아 증거가 죽은** 문제를 고치기 위해 휘발성 식별자를 증거에서 제거했다. 범위 확대가 아니라 기존 증거를 재현 가능한 것으로 교체하는 작업이므로 모드에 영향이 없다.

## Review history

| 아티팩트 | 라운드 | 점수 | 판정 | 블로커 | 대상 digest |
|---|---|---|---|---|---|
| Spec | 1 | — | REVISE | SPEC-011 | `913b54e5` |
| Spec | 2 | 90 | PASS | 없음 | `5c742d28` |
| Plan | 1 | 69 | REVISE | PLAN-001·PLAN-002 | `d49db8b8` (아래 불일치 참조) |
| Plan | 2 | — | PASS | 없음 | `d49db8b8` |
| Code | 1 | 82 | REVISE | 없음 | `29597a06` |
| Code | 2 | 86 | REVISE | 없음 | `4a6ed493` |
| Code | 3 | 88 | REVISE | 없음 | `4a6ed493` |

**라운드 간에 바뀐 것**

- **Spec 1→2**: SPEC-011(창 탐지 규칙이 선택 세션을 실제 위치로 오인)이 블로커로 잡혀 설계를 고쳤다. 이 결함은 나중에 스모크 T12와 재스모크 R3에서 실제로 수정 효과가 실증된 유일한 설계 결함이다.
- **Plan 1→2**: PLAN-001·PLAN-002는 "스모크 테스트가 스킬이 파생해야 할 값(`--target-name`·`--parent-session`)을 오퍼레이터가 직접 타이핑해 단언이 구성적으로 참이 된다"는 지적이었다. 하위 에이전트에게 **입력만** 주고 `workmux`·`git`·`tmux`를 shim으로 감싸 argv를 로깅하는 하네스로 바꿔 해소했다.
- **Code 1→2**: CODE-001~008 중 6건을 Codex 수정 라운드로 반영했다. 실행 순서 요약 절 신설, `target-window` 접미사 비교 규칙, `move-window-to-session` 인자 2개·인라인 금지 명시, git-crypt 문단의 선행사 모호성 해소, 편집 지시문 삭제. CODE-004(AC-59)는 코드로 닫을 수 없어 남았다.
- **Code 2→3**: 산출물은 건드리지 않고 `verification.json`의 증거 기록만 고쳤다. CODE-013(모순된 'AC-59 통과' 잔존), CODE-014(`superseded` 표시가 대체 증거 범위보다 넓음), CODE-015(AC-50 미검증 사유 부정확)를 정리했고 라운드 3이 셋 모두 해소를 확인했다. 대신 CODE-016이 나왔다 — 기록이 정직해진 결과 AC-9b·AC-50의 재배포본 증거 공백이 **확정**되어 `acceptance_criteria_met`을 참으로 판정할 수 없게 됐다. 리뷰어가 제시한 선택지 (a)를 택해 재실측했다(아래 R5 참조).

### 라운드 2·3 리뷰 JSON 유실 (절차 결함)

이 실행에서 코드 리뷰는 실제로 **네 번** 돌았다. 그러나 중간 두 라운드(CODE-009~012, CODE-013~014를 낸 라운드)의 리뷰 JSON이 디스크에 영속화되지 않았다. `code-prior-round2.json`에 그 findings ID가 "이전 열린 발견"으로 남아 있는 것이 실행 사실의 유일한 잔존 증거다.

오케스트레이터는 기억으로 리뷰어 산출물을 재구성해 기록하는 것을 **거부했다** — 감사 기록 위조에 해당하기 때문이다. 대신 남은 라운드 예산으로 최종 상태에 대해 리뷰를 새로 돌려 그것을 라운드 2·3으로 기록했다. 따라서 위 표의 라운드 번호는 **기록상 라운드**이며 실제 리뷰 횟수(4회)와 다르다.

**후속 개선**: `record-review`를 리뷰 직후 무조건 호출하도록 절차를 강제해야 한다. 리뷰어 반환값을 파일로 먼저 떨어뜨리지 않으면 컨텍스트 소실로 증거가 사라진다.

### Plan digest 불일치

Plan 라운드 1 리뷰의 실제 대상은 digest `8c239061`이었으나 state에는 `d49db8b8`으로 기록되어 있다. 오케스트레이터가 **리뷰를 기록하기 전에 Plan을 개정**했고, `record_review`가 현재 등록 아티팩트 기준으로 digest를 검사하므로 원래 값으로는 기록할 수 없었다.

원인을 코드로 확정했다. `set_artifact`는 `artifacts[kind]`에 경로만 쓰고, `artifact_digests`를 갱신하는 유일한 지점은 `record_review`다. v1.0.0의 `approve_plan`은 경로만 비교한 뒤 digest를 새로 계산하며 `artifact_digests["plan"]`과 교차 검사하지 않는다. 따라서 라운드 1·2가 같은 `d49db8b8`을 공유하는 것은 **`set-artifact` 누락이 아니라 기록 순서 오류의 결과**다. 올바른 순서는 기록 → 게이트 → 개정이다.

승인·구현에 실제로 쓰인 digest는 `fdbd2ddf`로, 리뷰가 본 어느 digest와도 다르다. 라운드 1 리뷰 원문은 `plan-review-round1.json`에 그대로 보존되어 있다.

## Blocking-finding resolutions

| 발견 | 단계 | 해소 | 검증 증거 |
|---|---|---|---|
| SPEC-011 | Spec 라운드 1 | 창 탐지를 4단계(`is_open` → 저장 세션 → `target-window` 접미사 → pane 경로 교차)로 재설계하고, 창을 옮기지 않는 경로에서는 **선택 세션이 아니라 실측 세션**을 기록하도록 규칙을 바꿨다 | 재스모크 R3 — `window-session=legacy` 주입 후 세션 미명시 재호출에서 하네스가 기록한 유일한 config 쓰기가 `… .window-session 3-personal`이었다. `SELECTED_SESSION`인 `2-review`가 아니다 |
| PLAN-001 | Plan 라운드 1 | 스모크가 스킬이 파생해야 할 값을 오퍼레이터가 타이핑하던 구조를 폐기하고, 하위 에이전트에 **입력만** 주는 방식으로 전환 | T9 로그 실측 — 에이전트에게 PR URL만 주었는데 `workmux add --pr 31 --target-name 31-tmux-open-pr-shortcut --parent-session 2-review`가 실행됐다 |
| PLAN-002 | Plan 라운드 1 | `workmux`·`git`·`tmux`를 argv 로깅 shim으로 감싸고 `run.sh`로 구동하는 하네스 도입 | 하네스 자체 검증(`workmux --version`이 로그에 기록됨) 후 전 단계 적용 |
| CODE-010 | Code (미기록 라운드) | 수정 라운드가 소스를 바꾼 뒤 **재배포하지 않아** 배포본에 6건이 전부 빠져 있었다. 즉시 경로 단위 `chezmoi apply` 후 재스모크 | `cmp` 3쌍 exit 0으로 AC-55 회복. 재스모크 R1에서 에이전트가 새 문서에만 있는 '실행 순서 요약' 절을 인용했고, R2에서 CODE-002 수정 덕에 `move-window-to-session`을 인라인이 아니라 Skill 도구로 호출했다 |

## Plan approval

- Approval timestamp: 2026-08-28T01:20:29Z
- Plan digest: `fdbd2ddfd163cdef0f528b9235f0fc96344d642568841685a24ac9b02d5ae676`

사용자 승인 문구는 "승인 — 스모크까지 전체"였다. 위 digest 불일치 절에 적었듯 이 digest는 리뷰가 본 `d49db8b8`·`8c239061` 어느 쪽과도 다르다.

## Changed files

| 파일 | 의도한 변경 |
|---|---|
| `dot_claude/skills/create-worktree/SKILL.md` (319행) | PR 참조 모드(URL / `owner/repo#N` / 태그된 자연어), 4단계 세션 선택 우선순위, handle 기반 config 키, 이름 비의존 창 탐지, `--pr` 숫자 정규화. Claude 전용 frontmatter 3줄(`argument-hint`·`user-invocable`·`allowed-tools`) 포함 |
| `dot_agents/skills/create-worktree/SKILL.md` (316행) | 위와 **본문 바이트 동일**. 차이는 Claude 전용 frontmatter 3줄뿐이며 `diff` 출력이 정확히 `3a4,6` + `>` 3줄이어야 한다는 불변식으로 관리된다 |
| `dot_agents/skills/create-worktree/agents/openai.yaml` (4행) | `short_description`과 `default_prompt`를 PR 모드·`2-review` 세션 반영으로 갱신 |

합계 547 삽입 / 301 삭제. 범위 밖 변경 0건(패치 헤더 정확히 3개, `git diff --check` exit 0).

## Verification evidence

**자동 검증 카테고리는 대부분 `not configured`다.** `package.json`·`Makefile`·`justfile`·`.github/workflows` 모두 부재하여 targeted_tests·full_suite·type_check·build를 실행할 대상이 없다. lint는 `.pre-commit-config.yaml`에 gitleaks 훅만 있고 pre-commit 자체가 미설치라 gitleaks를 직접 실행했다(DEV-4). 따라서 이 작업의 검증은 **문서 검토 + 실제 스모크 테스트**가 전부다.

### 핵심 실행 증거

가장 중요한 단일 증거다. 하위 에이전트에게 PR URL만 주었고 세션 이름도, 창 이름도, `--pr`의 인자 형태도 알려주지 않았다. 하네스가 기록한 실제 argv:

```
workmux add --pr 31 --target-name 31-tmux-open-pr-shortcut --parent-session 2-review
```

PR 번호 `31`이 head 브랜치가 담은 이슈 번호 `30`을 이겼다. 이것이 #28·#35가 요구한 핵심 동작이다.

### 재배포 후 재스모크 (R1~R4)

| 단계 | 입력 | 결과 |
|---|---|---|
| R1 | PR URL만 (재배포본) | 재배포 실효 확인 — 새 문서에만 있는 '실행 순서 요약' 절을 인용. AC-27·30·36·40·41·58 재확인 |
| R2 | `3-personal` 이동 지시 | AC-49·AC-13 재확인, `window_id` 동일(이동이지 재생성 아님). CODE-002 수정 실효 — `move-window-to-session`을 Skill 도구로 인자 2개만 넘겨 호출 |
| R2 | AC-44b 접미사 판정 | CODE-003 수정 실효 실증 — 동등 비교는 **실패**, 접미사 판정은 통과 |
| R3 | `window-session=legacy` 주입 + 세션 미명시 | **AC-12b·AC-48·AC-52** — 창 불이동, 기록값이 실측 `3-personal`(선택값 `2-review` 아님). SPEC-011 수정 실증 |
| R4 | 같은 세션(`3-personal`) 명시 | **AC-47** — `tmux list-windows -a` 전체 18행이 전후 바이트 동일, 중복 창 없음 |
| R5 | PR URL만, 생성 경로 (grep 패턴 수정 후) | **AC-50** — 생성(로그 59행) 후 사후 검증 `tmux list-windows -a`(148행) 실행. 창 목록 행 `2-review:4\|@37\|␣31-tmux-open-pr-shortcut`을 `od -c`로 바이트 확인 |
| R6 | 기존 worktree 존재 상태에서 PR URL만 | **AC-9b** — 창 이름 기준 조회 0건, 브랜치 슬러그 기준 0건, 쓰기 0건. 사후 config에 유령 `workmux.worktree.31-*` 섹션 없음 |
| 정리 | `workmux remove -k` | 잔여물 0건, 사전 존재 브랜치 `30-enhancement/tmux-open-pr-shortcut`이 `9cfc6267` 그대로 보존. `-f` 미사용 |

R3·R4의 픽스처는 오퍼레이터가 직접 조성하고 **검증 대상인 재호출만** 에이전트가 수행했다. 조성 값이 판정 대상이 아니므로 PLAN-001의 구성적 참 문제가 재발하지 않는다.

### 배포 정합

`chezmoi apply`는 **경로 단위로만** 실행했다. 인자 없는 실행은 다른 세션이 배포본 quality-goal 스킬을 실행 중일 수 있어 금지되었다. `cmp` 3쌍 exit 0으로 소스↔배포본 일치를 확인했다.

### 미검증으로 남긴 것

| 기준 | 사유 |
|---|---|
| AC-37 (git-crypt 래퍼 경로) | 업무 저장소에 1~2GB 부작용을 만들지 않기 위해 문서 검토만 |
| SPEC-022 분기 (basename ≠ handle) | 이 저장소 기본 명명에서 둘이 같아 스모크로 발동 불가 |
| 실패 상황 기준 (fetch 실패·저장소 불일치·래퍼 부재) | 인위 조성이 다른 기준 판정을 흐림 |
| AC-9b의 음성 단언 일반 | 하네스 완전 준수를 전제로 하며 부분 우회는 탐지하지 못한다 |

## Remaining advisory findings

| 발견 | 심각도 | 영향 | 후속 |
|---|---|---|---|
| **CODE-004 (AC-59)** | Medium | 코드 게이트의 `required_commands_passed`를 false로 만든다. 이 작업이 `COMPLETED`에 도달하지 못하는 **유일한 사유**다 | 아래 전용 절 참조 |
| CODE-016 (AC-9b·AC-50) | Medium | 라운드 3이 제기. **해소됨** — 리뷰어가 제시한 선택지 (a)를 택해 R5·R6로 재실측했다. 다만 라운드 한도 소진으로 이 증거를 검토한 리뷰 라운드는 없다 | 없음 |
| ERRATUM-5 (Spec R7.5 서술) | Low | Spec 본문과 산출물의 인자 계약 서술이 다르다. 산출물이 정확하다 | 다음 실행에서 R7.5 본문을 Interfaces 절의 한정어와 일치시킨다 |
| `quick_validate.py` 스키마 미반영 | Medium | 이 저장소의 Claude 전용 스킬은 앞으로도 이 검증기에서 exit 1이 난다 | 검증기를 교체하거나 `dot_agents` 쪽에만 적용 |
| 리뷰 JSON 영속화 누락 | Medium | 감사 추적 단절 | `record-review`를 리뷰 직후 무조건 호출하도록 절차 강제 |

### AC-59 — 사용자가 인정한 미충족 기준

승인된 AC-59의 판정 기준은 `quick_validate.py`의 **종료 코드 0**이다. 그런데 그 검증기는

```
42:  ALLOWED_PROPERTIES = {'name', 'description', 'license', 'allowed-tools', 'metadata', 'compatibility'}
45:  unexpected_keys = set(frontmatter.keys()) - ALLOWED_PROPERTIES
99:  sys.exit(1)
```

allow list에 `argument-hint`도 `user-invocable`도 없고, 예상 밖 키가 있으면 exit 1이다. 그런데 **Spec R1.8은 `argument-hint`를 요구한다.** 즉 R1.8을 만족하는 한 `dot_claude` 쪽 종료 코드는 항상 1이며, **기준과 요구사항이 서로를 배제한다.**

검증기 경로: `/Users/lee-kyu-hwan/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator/scripts/quick_validate.py`

이것은 **산출물 결함이 아니다.** 변경 전후로 unexpected key 집합이 `argument-hint, user-invocable`로 동일하고 메시지도 기준선과 바이트 동일하다. 어떤 코드 수정으로도 닫을 수 없다.

ERRATUM-4가 판정 기준을 정식 개정하려 시도했으나 **코드 리뷰 CODE-004가 거부했다** — 구현 쪽 정오표로 승인된 수용 기준을 고쳐 쓸 수 없고, 검토자는 결정적 명령의 비영 종료를 waive할 수 없다는 이유다. Spec 리뷰 라운드 한도(2/2)가 소진되어 정식 개정안을 게이트에 태울 수도 없었다.

사용자는 2026-08-28 **"미충족으로 인정하고 진행"**을 선택했다. 권위 있는 기록은 `verification.json`의 `user_accepted_unmet_criteria` 항목이다.

**후속 제안**: `quick_validate.py`는 skill-creator 플러그인 소유이고 Claude Code의 실제 frontmatter 스키마(`argument-hint`·`user-invocable`·`disable-model-invocation`)를 반영하지 않는다. 검증 도구를 교체하거나 `dot_agents` 쪽에만 적용하는 편이 낫다.

## Plan 이탈 (정오표)

| ID | 내용 |
|---|---|
| ERRATUM-1 | `quick_validate.py` 종료 코드를 파이프로 측정해 `head`의 값을 읽었다. `dot_claude`는 실제로 exit 1이 정상이다 |
| ERRATUM-2 | `chezmoi apply <디렉터리>`는 아무것도 매칭하지 않는다. 파일 단위 3개로 지정했다. 사전 점검이 "매칭 없음"과 "드리프트 없음"을 구분하지 못했던 것이 원인 |
| ERRATUM-3 | `target-window` 저장값과 실제 창 이름은 일치가 아니라 **접미사 일치**다(`nerdfont: true`가 붙이는 `U+E418` + 공백). 원 측정이 `.split()`으로 부분 토큰 일치를 전체 일치로 오독했다 |
| ERRATUM-4 | AC-59 판정 기준 개정 시도 → CODE-004가 거부 → 사용자 인정 미충족으로 재분류 |
| ERRATUM-5 | Spec R7.5의 "경로와 handle을 함께 전달한다"와 산출물의 "인자는 2개뿐"이 다르다. 대상 스킬의 실제 계약에 비추어 **산출물이 정확하다** |
| DEV-4 | pre-commit 미설치로 gitleaks를 직접 실행. 그 config의 유일한 훅이 gitleaks라 검증 내용은 동등 |
| DEV-5 | `workmux remove`에 `< /dev/null` 추가. `-k` + 빈 stdin에서 프롬프트 없이 exit 0으로 완료됨을 실측. **`-f`는 쓰지 않았다** |
| DEV-6 | 수정 라운드 후 재배포 누락(CODE-010). 코드 리뷰가 잡아 즉시 재배포하고 수정된 경로를 재배포본에 대해 다시 태웠다 |

## 미결 결정 사항 (사용자)

**변경된 3개 파일 547줄이 `~/.claude`·`~/.agents`에 배포되어 있으나 커밋되지 않았다.** 사용자가 "커밋하지 마라, 3차까지의 산출물 처리는 사용자가 결정한다"고 지시했으므로 오케스트레이터는 커밋하지 않았다. 작업 중 동료 세션이 커밋을 요청했으나 그 요청은 사용자 승인을 대신하지 못하므로 거부했다.

현재 상태의 위험: 배포본은 새 동작을 하지만 git에는 없다. `chezmoi apply`가 다른 경로로 실행되면 배포본이 옛 버전으로 되돌아갈 수 있다.

1·2차 실행 산출물은 **소실되지 않았다.** 커밋 `f23620a`가 `docs/quality-goal-field-reports`·`fix/quality-goal-round-limits` 브랜치에 담고 있으며, main 작업트리의 미추적 사본만 정리된 것이다.

## 도구 제약으로 남은 기록 불일치 (#43 재현)

**상태는 코드 리뷰 라운드 3을 기록한 순간 자동으로 `NEEDS_REDESIGN`으로 전이됐다** (2026-08-28T05:37:21Z, `status_reason: REVIEW_LIMIT_EXHAUSTED:code`). 오케스트레이터가 `transition`을 호출한 적이 없다 — `record-review`가 라운드 한도 도달과 비-PASS 판정을 보고 스스로 종결했다.

이 자동 전이가 두 가지 결과를 낳았다.

**1. 보고서를 아티팩트로 등록할 수 없다.** 스킬은 "터미널 상태로 전이하기 **전에** `set-artifact --kind report`로 등록하라"고 규정하는데, 전이가 보고서 작성보다 먼저 일어났다. 실제 시도 결과:

```
$ quality_state.py set-artifact --kind report --path .../report.md
error: terminal state is immutable: NEEDS_REDESIGN
```

사용자 지시에 따라 **우회하지 않았다.** `state.json`의 `artifacts.report`는 `null`로 남으며, 보고서의 권위 있는 위치는 이 파일의 경로다.

- 보고서 경로: `/Users/lee-kyu-hwan/code/dotfiles/docs/development/2026-08-27-create-worktree-pr-session-3/report.md`

**2. R5·R6 증거가 `state.json`에 반영되지 못했다.** CODE-016을 닫은 재실측(AC-9b·AC-50)은 자동 전이 **이후**에 수행됐다. `verification.json` 파일 자체에는 R5·R6와 갱신된 `known_limits`가 기록되어 있으나, `record-verification` 역시 같은 이유로 거부됐다.

```
$ quality_state.py record-verification --fingerprint e7b515b4…
error: terminal state is immutable: NEEDS_REDESIGN
```

따라서 `state.json`이 가리키는 검증 지문은 `4a6ed493`(R5·R6 이전)이고, 같은 경로의 `verification.json` 파일은 그보다 더 많은 증거를 담고 있다. **산출물 3파일은 R5·R6 동안 불변이며**(diff stat 547/301 동일, `cmp` 3쌍 exit 0) 지문 변화는 이 보고서 파일이 새로 생긴 데서 왔다.

**후속 개선**: `record-review`가 라운드 한도에서 자동 종결하기 전에 보고서 등록 기회를 주어야 한다. 현재 설계에서는 마지막 리뷰를 기록하는 순간 보고서 등록 경로가 닫히므로, 규정된 순서(보고서 등록 → 전이)를 지키는 것이 구조적으로 불가능하다.

## Final status

- Status: NEEDS_REDESIGN
- Machine-readable reason: `REVIEW_LIMIT_EXHAUSTED:code` (`state.json`이 기록한 값)

근본 사유는 `required_commands_passed=false`다. AC-59의 승인된 판정 기준(`quick_validate.py` 종료 코드 0)이 Spec R1.8(`argument-hint` 요구)과 상호 배제적이어서 구조적으로 충족 불가능하다. 사용자가 미충족을 인정했으나 검토자는 결정적 명령의 비영 종료를 waive할 수 없고, Spec 라운드 한도 소진으로 정식 개정도 불가능했다. 코드 리뷰 3라운드가 모두 REVISE(82 → 86 → 88)로 끝나 한도가 소진됐다.

**산출물 자체는 동작한다.** 핵심 목표(PR 링크 입력 시 PR 번호로 `2-review` 세션에 창 생성, 대상 세션 직접 지정)는 실행 증거로 확인됐다. `NEEDS_REDESIGN`은 산출물 결함이 아니라 **수용 기준과 검증 도구 사이의 구조적 모순** 때문이다. 다음 실행은 AC-59 판정 기준을 Spec 게이트를 거쳐 정식 개정하는 것에서 시작해야 한다.
