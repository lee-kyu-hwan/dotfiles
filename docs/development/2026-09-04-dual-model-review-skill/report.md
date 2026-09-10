# Quality Goal Report

- Task ID: 20260903T160637Z-42-claude-codex-이중-리뷰-종합-pr-게시-스킬-추가-55cca675
- Mode: strict
- Status: NEEDS_REDESIGN
- Created: 2026-09-04
- Updated: 2026-09-04
- Source goal: #42 Claude+Codex 이중 리뷰 → 종합 → PR 게시 스킬 추가

#42의 세 번째 quality-goal 실행이다. 1차는 Spec 라운드 한도, 2차는 Plan 라운드 한도로 끝났고, 3차인 이 실행은 **Spec 블로킹 finding의 재발**로 끝났다. 라운드 한도(spec 3)는 소진되지 않았다.

## Classification

`--mode=standard` 요청에 대해 위험 스캔은 `strict`를 냈고, 사용자가 다운그레이드 근거를 검토한 뒤 **strict 유지를 명시적으로 선택**했다. 조용한 다운그레이드는 없었다.

- **외부 API 쓰기 + 멱등성(strict 트리거).** 스킬이 `gh pr review`로 PR에 게시하고, 이슈 #42가 "중복 게시 방지, 커밋 SHA 명시, 재실행 갱신 정책"을 핵심 차별점으로 지목한다.
- **비가역 외부 노출.** 게시 계약 오류는 실제 PR에 되돌리기 어려운 댓글을 남긴다.
- **다층·다파일 변경, 요구사항 명시 필요(standard 조건).**
- 다운그레이드 시 strict-only 6절(고위험 E2E 검증·대상 격리·롤백 한계)을 제거해야 하는데 그 내용이 이 작업에 실제로 해당한다는 것이 유지 근거였다.

## Review history

| 아티팩트 | 라운드 | 시도 | 점수 | verdict | blockers | 처리 |
|---|---|---|---|---|---|---|
| Spec | 1 | 1 | 91 | REVISE | 없음 | 미검증 evidence 3묶음 → `record-review-unverified` (라운드 미소모) |
| Spec | 1 | 2 | 87 | REVISE | 없음 | 미검증 1건 → `record-review-unverified` (재시도 예산 소진) |
| Spec | 1 | 3 | 80 | REVISE | **SPEC-09** | 미검증 0 → `record-review`로 라운드 1 소비 |
| Spec | 2 | 1 | 79 | REVISE | **SPEC-09**, SPEC-13 | 재발 → `RECURRING_BLOCKING_FINDING:SPEC-09` |

Plan은 이 실행에서 리뷰되지 않았다. Spec 게이트를 통과하지 못해 PLAN_REVIEW에 도달하지 못했다.

### v4.0.0의 미검증 REVISE 경로가 실제로 작동했다

라운드 1의 앞 두 시도는 `verdict == REVISE`·`blockers == []`·`verified: false` 존재라는 조건에 걸려 `record-review-unverified`로 기록됐고 **라운드를 소모하지 않았다**. 그 사이 오케스트레이터가 미검증 조건에 실측 증거를 공급했다.

| 미검증 묶음 | 처리 | 결과 |
|---|---|---|
| gh 인증·GraphQL 계약·PR 코멘트 키·이슈 상태 | 실측해 `evidence/external-state.md`로 공급 | 2차 리뷰에서 전부 `verified: true` |
| 외부 문헌 인용 | 평가 범위에서 제외(게이트 조건 아님) | evidence 항목에서 사라짐 |
| 실행형 AC의 실제 통과 여부 | 평가 범위에서 제외(구현물 없음) | evidence 항목에서 사라짐 |
| R7.16 cross-hunk 전제 | GitHub 공식 REST 문서 조회 결과를 증거로 기록 | 3차 리뷰에서 `verified: true`, SPEC-10으로 별도 지적 |

미검증 3묶음 → 1건 → 0건으로 줄어 라운드 1이 정상 기록됐다. 이 장치가 없었다면 판정이 불완전한 리뷰로 라운드 두 개를 태웠을 것이다.

### 조회로 드러난 사실 정정 둘

- **R7.16의 cross-hunk 전제는 근거가 없었다.** 2026-09-04에 GitHub 공식 REST 문서를 조회한 결과 `side`의 허용값·기본값은 명시돼 있으나 **`start_line`과 `line`이 같은 diff hunk 안에 있어야 한다는 제약은 명시돼 있지 않다**. Spec은 이 규칙을 D18의 실측 결론처럼 서술했으나 그 실측은 응답 키 이름 집합뿐이었다. 라운드 1의 SPEC-10이 이를 지적했고 개정에서 "보수적 선택"으로 정정했다.
- **플러그인 인용 경로가 무효였다.** Spec이 고정한 `pr-review-toolkit/e33a9ec0973a`는 디렉터리로 존재하나 **파일이 하나도 없고**, 활성 설치본은 `0120fb83da5d`다. R3.6이 인용한 행 번호는 활성 설치본에서만 해석된다. 라운드 1의 첫 시도는 "디렉터리가 존재하지 않는다"고 했고 오케스트레이터가 "존재한다"고 정정했으나, 세 번째 시도가 "존재하지만 비어 있다"로 더 정확히 짚었다.

## Blocking-finding resolutions

| ID | 라운드 1 지적 | 적용한 해소 | 라운드 2 판정 |
|---|---|---|---|
| SPEC-09 | `resolved`가 집합 차집합으로만 정의돼, 커버리지 결손으로 사라진 finding이 "해소됨"으로 게시되고 스레드가 자동 해결된다 | R7.6a 신설(결손 경로 표 + `not_re_reviewed` 분류), R7.7을 분류별 게시 동작 표로 재작성, AC-10을 "결손 없는 실행"으로 좁힘, AC-62 신설, publish-plan `lifecycle`에 `not_re_reviewed` 추가, D21 기록 | **미해소.** 결손 경로 열거가 불완전하다 |

라운드 1의 나머지 11건(SPEC-01~08, 10~12)은 라운드 2에서 **전부 해소 확인**됐다.

## 재발 원인 분석

### SPEC-09가 왜 남았는가

R7.6a가 열거한 결손 경로는 셋이다: R10.2(b) 범위 축소, R3.5 `excluded`, R3.9 에이전트 일부 실패.

같은 개정에서 SPEC-03을 해소하며 R3.7에 **리뷰어 실패 세 유형**을 열거했다: (a) Codex 프리플라이트 실패·모델 거부, (b) R3.5 `excluded`, (c) 산출물 없는 종료.

**두 목록이 같은 사건 집합을 다루는데 R7.6a는 (b)만 담았다.** (a)나 (c)로 리뷰어 하나가 통째로 실행되지 않은 실행에서, 그 리뷰어가 냈던 이전 게시 finding은 R7.6a의 세 조건 어디에도 걸리지 않아 `resolved`가 된다. 더 나쁘게, AC-10의 "커버리지 결손 없는 실행" 정의도 셋뿐이라 프리플라이트 실패 실행이 그 정의를 만족하고 **AC가 `resolveReviewThread` 호출을 요구한다**. 라운드 1이 지적한 해악의 구조가 그대로 남았다.

원인은 조합 검토의 불완전성이다. 이 실행의 조합 검토는 R3.5·R3.7·R3.9·R6.3·Architecture와 R7.6a를 겹치는 지점으로 인식했고 R3.9의 에이전트 일부 실패가 R7.6a의 세 번째 경로와 같은 사건임을 상호 참조로 명시했다. 그러나 **R3.7의 (a)·(c)도 결손을 만든다는 대칭은 보지 못했다.** 새로 만든 두 열거를 서로 대조하지 않고 한쪽 방향만 확인했다.

### SPEC-13 — 더 깊은 결함

라운드 2가 새로 낸 High다. `new_blocker_evidence`가 "R7.6a가 존재하기 전에는 성립하지 않는 결함"이라고 정확히 근거를 댔다.

R7.6a는 "이전 게시에 있고 지금 없는 finding"을 세 경로로 분류하라고 하는데, **그 판정에 필요한 입력이 실행 간에 지속되지 않는다.**

| 판정에 필요한 것 | 현재 얻을 수 있는가 |
|---|---|
| finding의 `category` (경로 3 판정) | 불가. `finding_id`는 `sha256(path\0category\0title)` 앞 12자라 역산 불가 |
| finding의 출처 리뷰어 (경로 2 판정) | 불가. `source`는 정규화 finding의 내부 필드일 뿐이고 상태 파일·게시물 어디에도 남지 않는다 |
| finding의 `path` (경로 1 판정) | 부분적. R7.17이 기록하지만 inline 게시된 finding에만 있고 요약으로 강등된 것에는 없다 |

게다가 R2.5가 "head SHA가 바뀌면 이전 실행 상태를 재사용하지 않는다"고 못박았는데, 재리뷰는 통상 새 head SHA에서 일어난다. 즉 직전 실행의 기록에 접근할 수도 없다.

결과적으로 D21의 "판정이 결정적이다"와 R7.6a의 "판정은 스크립트가 수행한다"가 성립하지 않는다. 구현이 "조건 매칭 실패 → `resolved`"로 떨어지면 SPEC-09가 막으려던 비가역 외부 쓰기가 그대로 일어난다. AC-62는 fake 픽스처가 분류 입력을 임의로 공급할 수 있어 이 결손을 검출하지 못한다.

**이것이 재설계가 필요한 이유다.** 해소하려면 게시 마커나 요약에 기계 판독 가능한 finding 메타데이터를 싣거나, head SHA를 넘어 유지되는 게시 이력 레코드를 도입해야 한다. R7.3(finding_id 형식)·R7.9(마커)·R7.17(기록 필드)·R2.5(상태 재사용)를 함께 건드리는 구조 변경이고, 라운드 하나에서 급히 처리할 성격이 아니다.

## Plan approval

- Approval timestamp: 없음 — `AWAITING_PLAN_APPROVAL`에 도달하지 못했다
- Plan digest: 없음 — 이 실행에서 Plan은 리뷰되지 않았다

## Changed files

구현은 시작되지 않았다.

| 파일 | 변경 |
|---|---|
| `docs/development/2026-09-04-dual-model-review-skill/spec.md` | 신규. 651행. 요구사항 60(R1.1~R10.3), AC 63, 결정 D1~D23, strict 전용 6절, 요구사항 추적표 60행, 개정 조합 검토 절 |
| `docs/development/2026-09-04-dual-model-review-skill/plan.md` | 신규. 2차 실행 Plan에 잔여 7건을 반영한 515행본을 초안으로 시딩. 이 실행에서 리뷰되지 않았다 |
| `docs/development/2026-09-04-dual-model-review-skill/report.md` | 신규. 이 리포트 |
| `docs/development/2026-08-28-dual-model-review-skill-2/plan.md` | 사전 준비. 2차 실행 Plan의 잔여 7건 반영(441→515행). 이 실행의 baseline dirty 경로 |

`dot_claude/skills/dual-review/`는 만들어지지 않았다. `.gitignore`는 변경되지 않았다. 커밋·푸시·PR 생성·`chezmoi apply`를 수행하지 않았다.

리베이스는 수행했다: 브랜치가 `origin/main` 위로 올라갔고(`da0abef` → `bb2863c`) 충돌은 없었다.

## Verification evidence

| 명령 | 종료 코드 | 증거 |
|---|---|---|
| `grep '^version:' ~/.claude/skills/quality-goal/SKILL.md` | 0 | `4.0.0` — #66 배포 확인 |
| `grep 'ROUND_LIMITS' quality_state.py` | 0 | `{"spec": 3, "plan": 2, "code": 3}` |
| `git rebase origin/main` | 0 | 충돌 0, `da0abef` 내용 보존 |
| `git rev-list --left-right --count origin/main...HEAD` | 0 | `0 1` — main 대비 앞 1 |
| `codex exec --sandbox read-only --model gpt-5.6-sol -c model_reasoning_effort="low"` | 0 | 응답 `Acknowledged.` |
| `gh auth status` | 0 | 계정 `lee-kyu-hwan`, 스코프에 `repo` |
| `gh api graphql`(인트로스펙션 2회) | 0 | `ResolveReviewThreadInput.threadId`(`ID!`) 필수, `PullRequestReviewThread.viewerCanResolve` 존재 |
| `gh api .../pulls/{1255,1211,1313}/comments`(키만) | 0 | 79건, 세 PR 동일 키 집합 |
| `gh issue view {29,36,42}` | 0 | 전부 OPEN |
| GitHub REST 문서 조회(pulls/comments) | 0 | `side` 확인, **cross-hunk 제약 미명시** |
| `chezmoi source-path` | 0 | `/Users/lee-kyu-hwan/code/dotfiles` — 워크트리 아님 |
| `git check-ignore -q .claude/quality-state/` | 0 | 무시됨 |
| Spec 자체 검증(절·추적표·AC 정합) | 0 | 요구사항 60 전수 등재(누락 0·유령 0), AC 63 전부 참조·배정, `검증:` 없는 AC 0 |
| `validate_review.py validate`(4회) | 0 | 네 리뷰 모두 `{"valid":true,"errors":[]}` |
| `validate_review.py gate`(Spec r1) | 3 | `passed:false` — 5개 사유 |

구현이 없으므로 코드 검증 범주는 전부 미실행이다.

- 단위 테스트: **미실행.** `dot_claude/skills/dual-review/tests/`가 존재하지 않는다.
- 타입 체크·린트·빌드: **not configured.** 저장소 루트에 `tsconfig.json`·`pyproject.toml`·`Makefile`·`package.json`·린터 설정이 없다.
- E2E: **미실행.** 고위험 E2E(AC-27·AC-37·수동 게시)는 구현 이후 단계다.

## Remaining advisory findings

| ID | 심각도 | 내용 | 후속 조치 |
|---|---|---|---|
| SPEC-09 | High(재발) | R7.6a의 결손 경로가 R3.7의 실패 유형 (a)·(c)를 담지 않아 그 실행에서 미해소 finding이 `resolved`로 게시된다. AC-10의 결손 없음 정의도 같은 누락을 갖는다 | R7.6a 결손 경로에 (a)·(c) 추가, AC-10 정의를 "R3.7 세 유형 모두 미발생 + 범위 축소·실패 에이전트 없음"으로 좁힘, AC-62 대상 확장, D21·Architecture의 "세 경로" 서술 정정 |
| SPEC-13 | High(신규) | R7.6a의 판정 입력(`category`·출처 리뷰어·`path`)이 실행 간에 지속되지 않아 분류가 결정 불가능하다 | 게시 마커·요약에 기계 판독 가능한 finding 메타데이터를 싣거나 head SHA를 넘어 유지되는 게시 이력 레코드를 도입. 복원 불가 시 기본값을 `not_re_reviewed`(안전 측)로 고정. AC-62에 그 단정 추가 |
| SPEC-14 | Medium | `run_id`가 `--base`를 포함하지 않아, 같은 head SHA에 `--base`를 바꿔 재실행하면 기존 `base_sha`가 조용히 재사용된다. `--rounds`도 동일 | 재실행 인자와 고정 상태의 충돌 시 중단하거나 새 상태를 만들도록 R2.5에 명시하고 AC-61에 단정 추가 |
| SPEC-15 | Low | AC-55의 "현재 브랜치 PR 조회"를 수행할 메서드가 R8.2의 아홉 메서드에 없다(`get_pr_meta`는 번호를 요구하고 `list_open_prs`는 브랜치 필터가 없다) | 어느 메서드로 수행하는지 명시하고 필요하면 시그니처를 보강 |
| SPEC-16 | Low | R7.18의 `skipped_threads`와 R7.6a의 결손 근거 기록이 Interfaces의 상태 파일 필드 목록에 없다 | 상태 파일 필드 목록에 두 필드 추가 |

리뷰어가 자체 정정한 것 하나: "개정 조합 검토" 절이 "표가 참조하는 AC 63건"이라고 썼으나 실제로 표가 참조하는 것은 61건이다(AC-27·AC-34는 메타 기준으로 제외). 총 AC 수와 혼동된 서술이다.

## Final status

- Status: `NEEDS_REDESIGN`
- Machine-readable reason: `RECURRING_BLOCKING_FINDING:SPEC-09`

`spec-rubric.md`의 "If the same blocking finding ID recurs twice, stop and record `NEEDS_REDESIGN`, even if the round limit has not otherwise been reached" 규칙에 따라 중단했다. **라운드 한도는 소진되지 않았다** — spec 한도 3 중 2를 썼고 라운드 3이 남아 있었다.

`quality_state.py:662`가 이 재발을 자동 감지해 `status_reason`을 설정한다. 오케스트레이터의 판단이 아니라 도구의 결정적 판정이다.

이 판정은 타당하다. SPEC-09를 라운드 3에서 급히 고칠 수는 있으나 SPEC-13이 요구하는 것은 구조 변경이다 — 게시 이력의 지속 방식을 정하는 일이고 R7.3·R7.9·R7.17·R2.5가 함께 움직인다. 라운드 하나에 밀어 넣으면 이 실행이 이미 두 번 겪은 패턴(해소가 새 회귀를 만드는 것)을 반복할 가능성이 높다.

## 세 실행의 누적 관찰

| 실행 | 종료 | 사유 | 도달 단계 |
|---|---|---|---|
| 1차 `20260828T011459Z` | NEEDS_REDESIGN | `REVIEW_LIMIT_EXHAUSTED:spec` | SPEC_REVIEW |
| 2차 `20260828T021938Z` | NEEDS_REDESIGN | `REVIEW_LIMIT_EXHAUSTED:plan` | PLAN_REVIEW |
| 3차 `20260903T160637Z` | NEEDS_REDESIGN | `RECURRING_BLOCKING_FINDING:SPEC-09` | SPEC_REVIEW |

세 번 모두 구현에 도달하지 못했다. 그러나 세 실행이 같은 자리를 맴돈 것은 아니다. 2차가 Spec을 93점 PASS까지 올렸고, 3차는 그 통과본에서 **High 2건을 새로 찾아냈다** — 그중 SPEC-13은 이 실행이 스스로 만든 R7.6a 때문에 비로소 성립하는 결함이다.

관찰 셋:

1. **통과한 Spec이 옳은 Spec은 아니다.** 2차에서 93점 PASS를 받은 판본이 3차 라운드 1에서 80점에 blocker 1건을 받았다. 리뷰어가 매번 다른 각도를 잡고, 특히 SPEC-09처럼 "여러 요구사항의 교차점"에 있는 결함은 한 번의 통과로 걸러지지 않는다.
2. **해소가 회귀를 만드는 패턴이 세 실행 모두에서 반복됐다.** 2차 Plan 라운드 2의 신규 지적 셋이 라운드 1 해소의 회귀였고, 3차 Spec 라운드 2의 SPEC-13도 라운드 1 해소(R7.6a)가 만든 것이다. 조합 검토 절을 도입해 세 건을 미리 잡았지만(R6.3 표현·R2.1/R2.5 순서·D18 분리) SPEC-09의 (a)·(c) 누락은 놓쳤다 — **새로 만든 두 열거를 서로 대조하는 단계가 없었다.**
3. **v4.0.0의 미검증 REVISE 경로는 값을 냈다.** 라운드 두 개를 아꼈고, 그 과정에서 R7.16의 근거 없음과 플러그인 경로 무효화라는 사실 정정 둘이 나왔다.

## 4차 착수 전 확정된 설계 결정

SPEC-13(게시 이력의 실행 간 지속)에 대해 사용자가 방식을 확정했다. **GitHub 자체를 source of truth로 쓴다.** 로컬 파일이나 git notes에 이력을 두지 않는다 — worktree 제거로 사라지는 휘발성 상태이기 때문이다. 이 원칙은 feat-sync 조사(`research.md` 결론 1 "GitHub가 source of truth")와 같고, 실제로 오늘 여섯 개 리뷰 세션이 `gh api`로 기존 리뷰를 읽고 시작한 방식이다.

아래는 4차 실행이 Spec에 반영할 개정안이다. 이 리포트는 3차 실행의 터미널 기록이므로 개정 자체는 4차에서 수행한다.

### 복원 메커니즘

이번 실행이 게시할 때 기계 판독 가능한 메타데이터를 GitHub에 남기고, 다음 실행이 그것을 읽어 "이전에 게시된 finding 집합"을 복원한다.

| 읽기 | 대상 |
|---|---|
| `GET /repos/{owner}/{repo}/pulls/{N}/comments` | inline 코멘트 본문의 finding 마커, `path`·`line`·`node_id` |
| `GET /repos/{owner}/{repo}/pulls/{N}/reviews` | 리뷰 단위 메타데이터 |
| `GET /repos/{owner}/{repo}/issues/{N}/comments` | sticky 요약의 인덱스 블록 |
| GraphQL `reviewThreads` | 스레드 `isResolved`·`viewerCanResolve` |

### R7.9 개정 — 마커 두 층

**inline 마커는 지금 형식을 유지한다**: `<!-- dual-review:finding:<finding_id> -->`. 용도는 dedup 하나이고, `path`·`line`은 REST 응답이 이미 준다(R7.17).

**요약 코멘트에 인덱스 블록을 신설한다**(R7.9a):

```
<!-- dual-review:index v1 <base64(JSON)> -->
```

base64는 표준 알파벳(`+`, `/`, `=`)을 쓴다. base64url의 `-`는 연속되면 HTML 주석을 깨뜨릴 수 있고, 파일 경로에도 `--`가 들어갈 수 있어 평문 key=value나 생 JSON은 안전하지 않다.

디코드된 JSON은 이번 실행이 게시한 **모든** finding의 메타데이터를 담는다 — inline으로 나간 것과 요약으로 강등된 것 전부다.

| 필드 | 용도 |
|---|---|
| `id` | `finding_id`. inline 마커와 대조 |
| `path`, `line` | 위치. 요약 강등분은 REST 응답에 없으므로 여기서만 얻는다 |
| `cat` | `category`. `finding_id`가 해시라 역산 불가하므로 반드시 실어야 한다 |
| `fp` | `anchor_fingerprint`. 내용 지문, 라인 이동 추적 |
| `src` | 출처 리뷰어(`claude:<에이전트명>` 또는 `codex`). 결손 경로 2 판정에 필요 |
| `run` | 게시한 실행의 `run_id` |
| `lifecycle` | 그때의 분류 |

`cat`·`src`·`path`가 SPEC-13이 지적한 "복원 불가능한 세 입력"에 정확히 대응한다.

### R7.6a 개정 — 결손 경로 다섯으로 확장

SPEC-09가 요구한 확장을 함께 반영한다. R3.7의 리뷰어 실패 **세 유형 전부**를 담는다.

| 결손 경로 | 판정 입력 |
|---|---|
| R3.7(a) Codex 프리플라이트 실패·모델 거부 | 인덱스의 `src`가 `codex`인 finding |
| R3.7(b) R3.5 `excluded` | 인덱스의 `src`가 제외된 리뷰어인 finding |
| R3.7(c) 산출물 없는 종료 | 인덱스의 `src`가 그 리뷰어인 finding |
| R10.2(b) 범위 축소 | 인덱스의 `path`가 축소된 경로 집합 밖 |
| 에이전트 부분 실패(R3.9 후단) | 인덱스의 `cat`이 실패한 에이전트의 담당 카테고리 |

**복원 불가 시 기본값은 `not_re_reviewed`다.** 인덱스 블록이 없거나(이 스킬 이전 버전이 게시한 코멘트), 디코드에 실패하거나, 필요한 필드가 비면 `resolved`로 판정하지 않는다. 안전 측으로 떨어지는 것이 비가역 외부 쓰기를 막는다.

`resolved`는 세 조건을 모두 만족할 때만이다: (1) 이전 인덱스에 있고 이번 결과에 없다, (2) 위 다섯 결손 경로 어디에도 걸리지 않는다, (3) 해당 스레드가 아직 열려 있다(이미 resolved면 재처리 불필요).

### R2.5 개정 — 로컬 상태의 범위 축소

`run_id`와 상태 디렉터리는 **한 실행 안의 bookkeeping**으로 범위를 좁힌다. 실행 간 이력은 로컬에 두지 않는다. 따라서 head SHA가 바뀌어 `run_id`가 달라져도 복원에 지장이 없다 — SPEC-13이 지적한 "R2.5가 이전 상태 재사용을 막아 출처 기록에 접근할 수 없다"는 문제가 사라진다. 로컬 상태가 통째로 없어져도(worktree 제거) 다음 실행이 GitHub에서 복원한다.

이 변경은 SPEC-14(재실행 인자와 고정 상태의 충돌)의 표면적도 줄인다. 상태가 실행 내로 한정되면 `--base`를 바꾼 재실행이 낡은 `base_sha`를 물려받을 여지가 작아진다. 다만 같은 `run_id`로 이어가는 경로는 남으므로 SPEC-14의 충돌 처리는 별도로 명시해야 한다.

### R7.3 · R7.17 개정

- **R7.3**: `finding_id` 정의(`sha256(path\0category\0title)` 앞 12자)는 그대로 둔다. `category`를 인덱스가 싣게 되므로 역산할 필요가 없어진다.
- **R7.17**: 기록 대상에 인덱스 블록 파싱 결과를 추가한다. REST 응답의 여섯 필드(`id`·`node_id`·`pull_request_review_id`·`path`·`line`·`original_line`)에 더해, 인덱스에서 복원한 `cat`·`fp`·`src`·`run`과 **복원 실패 여부**를 남긴다. 복원 실패는 R7.6a의 기본값 분기를 타는 근거다.

### 함께 반영할 것

4차에서 이 개정과 같이 처리해야 할 잔여 findings다.

| ID | 처리 |
|---|---|
| SPEC-09 | 위 R7.6a 개정이 결손 경로를 다섯으로 확장해 해소한다. AC-10의 "커버리지 결손 없는 실행" 정의도 "R3.7 세 유형 모두 미발생 + 범위 축소·실패 에이전트 없음"으로 좁히고, AC-62의 대상을 다섯 경로로 늘린다. D21과 Architecture의 "세 경로" 서술을 정정한다 |
| SPEC-13 | 위 복원 메커니즘 전체 |
| SPEC-14 | 같은 `run_id`로 이어가는 재실행에서 `--base`·`--rounds`가 고정된 상태와 다르면 중단하거나 새 상태를 만들도록 R2.5에 명시하고 AC-61에 단정 추가 |
| SPEC-15 | 현재 브랜치 PR 해석을 R8.2의 아홉 메서드 중 어느 것으로 하는지 명시. `get_pr_meta`가 번호를 요구하므로 `list_open_prs`에 브랜치 필터를 넣거나 열 번째 메서드를 추가하는 선택이 필요하다 |
| SPEC-16 | 상태 파일 필드 목록에 `skipped_threads`와 결손 경로 근거 필드 추가 |
| SPEC-10 잔여 | D18 마지막 문장이 여전히 hunk 축소 규칙을 실측의 귀결처럼 읽히게 한다 |
| 조합 검토 절 오기 | "표가 참조하는 AC 63건"은 61건이 맞다(AC-27·AC-34 제외) |

### 새 AC 후보

| AC | 판정 대상 |
|---|---|
| 인덱스 왕복 | 이번 실행이 만든 인덱스 블록을 다음 실행이 디코드해 같은 finding 집합을 복원한다 |
| 복원 실패 기본값 | 인덱스가 없거나 디코드 실패·필드 결손일 때 `resolved`가 0건이고 전부 `not_re_reviewed`다 |
| 다섯 결손 경로 | 각 경로별로 `resolved`가 아니라 `not_re_reviewed`가 되고 `resolveReviewThread` 호출이 없다 |
| base64 안전성 | 인덱스 블록에 `--`가 포함되지 않는다(HTML 주석 파손 방지) |
| 요약 강등분 복원 | inline 코멘트가 없는 강등 finding도 인덱스에서 `path`·`line`이 복원된다 |

### 이 결정이 닫지 않는 것

인덱스 블록은 이 스킬이 게시한 코멘트에만 있다. 사람이 손으로 단 리뷰 코멘트나 다른 봇의 코멘트는 복원 대상이 아니며, 그것들을 `resolved`로 판정하는 일도 없다(마커가 없으면 이 스킬의 finding이 아니다). 스킬의 이전 버전이 인덱스 없이 게시한 코멘트는 복원 불가로 취급돼 `not_re_reviewed`로 떨어진다 — 첫 도입 시 한 번 발생하고 이후 사라지는 전이 비용이다.
