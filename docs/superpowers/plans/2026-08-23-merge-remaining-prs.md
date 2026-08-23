# 남은 PR 2개(#6, #12) 마무리 계획

**목표:** 3주 넘게 열려 있는 PR #6(deep-research)과 #12(Codex PR 리뷰 툴킷)을 리뷰하고
main에 머지한다. 머지 후 **로컬 배포 상태가 저장소와 일치하는 것까지** 완료 조건에 넣는다.

**핵심 제약:** 두 PR은 이미 로컬에서 **사용 중**이다. 그래서 이 작업은 "새 기능 도입"이
아니라 **저장소와 실사용 상태를 일치시키는 작업**이다. #6은 로컬이 저장소보다 낡았고,
#12는 원격 PR에 없는 로컬 커밋이 하나 있다 — 이 비대칭이 순서와 절차를 결정한다.

> 이 문서는 codex adversarial-review를 한 번 거쳐 6건(high 4, medium 2)을 반영한
> 2판이다. 반영 내역은 맨 아래 "리뷰 반영 기록"에 있다.

---

## 확인된 현재 상태

측정 방법을 함께 적는다. 추정과 실측을 섞지 않기 위한 것이다.

| 항목 | #6 deep-research | #12 Codex 리뷰 툴킷 |
|------|------------------|---------------------|
| 브랜치 | `chore/add-deep-research` | `codex-pr-review-toolkit` |
| 상태 | READY | **DRAFT** |
| 규모 | +5,038 / 7파일 / 25커밋 | +2,101 / 11파일 / 8커밋 |
| main 대비 | 25 앞 / 9 뒤 | 8 앞 / 6 뒤 |
| 원격 PR head | `59fc735` | `0e8da12` |
| **로컬 브랜치 head** | 원격과 동일 | **`c5231a7` — 원격보다 1커밋 앞섬** |
| main 머지 | 충돌 없음 (`merge --no-commit` 실측) | 충돌 없음 (동일 방법) |
| 자체 테스트 | 111개 통과 — **단, 아래 A-2 단서 참조** | 없음 (문서·스킬만) |

### #6 — 로컬에 낡은 세대가 배포돼 있다 (대상 2개)

```
                                              브랜치   로컬      로컬 상태
dot_claude/workflows/deep-research.js         1,299줄    431줄   mtime 2026-07-15
dot_agents/skills/deep-research/SKILL.md         74줄     91줄   최초 커밋(947355e)과 동일
```

- **둘 다 chezmoi 관리 대상이 아니다** (`chezmoi source-path` → `not managed`).
  main에 해당 source가 없으므로 관리될 수가 없다. 손으로 놓인 초안이 남아 있는 것이다.
- 브랜치 25커밋 중 **22개가 `fix:`** — "실패 은닉", "크래시", "envelope 위조 방지",
  "병렬 작업 오류 전파", "검증 신뢰성". 지금 `/deep-research`를 실행하면 그 수정이
  하나도 적용되지 않은 조합(431줄 워크플로 + 91줄 스킬)이 돈다.
- 머지하면 두 source가 main에 들어오고, 그 시점부터 chezmoi가 두 로컬 파일을 관리 대상으로
  잡아 **덮어쓴다.** 이것이 의도한 결과다. **두 대상을 한 세트로 다룬다** — 하나만
  갱신되면 새 워크플로와 구형 스킬이 섞인다.

### #12 — 원격 PR에 없는 로컬 커밋

```
c5231a7  fix(skills): PR 리뷰 툴킷 롤백 절차와 스킬 발동 경계 보완
         docs plan +56/-? · design +32 · code-reviewer SKILL +2 · orchestrator SKILL +18
```

`git branch -a --contains c5231a7` → **`codex-pr-review-toolkit` 로컬 브랜치뿐**이다.
원격에도 없고 다른 ref에서도 도달할 수 없다. 계획대로 원격 8커밋을 머지하고 브랜치를
삭제하면 **이 커밋은 영구 유실된다.** 배포본(`~/.codex/skills/pr-review-toolkit/SKILL.md`)은
원격 head와 일치하므로 이 커밋의 내용은 배포조차 되지 않은 상태다.

### CI·게이트 현황

- GitHub Actions 워크플로 없음, main 브랜치 보호 없음 (`gh api .../protection` → 404)
- 저장소 자체 게이트는 pre-commit의 gitleaks뿐
- 따라서 **머지 전 검증은 전적으로 이 계획이 책임진다.** "CI가 잡아줄 것"이라는 가정을
  쓸 수 없다.

---

## 공통 원칙

### 원칙 1 — 검증은 브랜치 head가 아니라 candidate merge에서 한다

두 브랜치는 main보다 9·6커밋 뒤처져 있다. **충돌이 없다는 것과 의미상 정합하다는 것은
다르다.** #21~#23에서 정확히 이 함정을 밟았다 — 낡은 브랜치를 그대로 얹어 그 사이 main이
개선한 내용을 되돌릴 뻔했다.

- [ ] 각 PR마다 최신 `origin/main` 위에 candidate merge 브랜치를 만든다
      (`git checkout -B cand-<n> origin/main && git merge --no-ff origin/<브랜치>`)
- [ ] **테스트·정적 검증·리뷰를 그 candidate에서 실행한다.** 브랜치 head에서 돌린 결과는
      머지 후 상태를 대표하지 않는다
- [ ] 검증 시작·종료 시점의 `git rev-parse HEAD`가 같은지 확인한다 (도중에 바뀌면 무효)

### 원칙 2 — 역행 검사는 양쪽을 본다

`git diff origin/main...origin/<브랜치>`(세 점)는 merge-base부터 **브랜치 쪽** 변경만
보여준다. 역행 검사의 핵심인 **main 쪽 변경이 누락된다.**

- [ ] `mb=$(git merge-base origin/main origin/<브랜치>)`
- [ ] `git diff $mb origin/main -- <공통 파일>` — main이 그 사이 무엇을 바꿨는지
- [ ] `git diff $mb origin/<브랜치> -- <공통 파일>` — 브랜치가 무엇을 바꿨는지
- [ ] candidate merge의 전체 diff(`git diff origin/main..cand-<n>`)를 읽는다 —
      **이것이 실제로 main에 들어갈 내용이다**

공통 파일은 `.chezmoiignore`(양쪽)와 `CLAUDE.md`(#6이 +6줄)다.

### 원칙 3 — 원격 머지 후 로컬을 반드시 전진시킨다

`gh pr merge`는 GitHub의 base를 갱신할 뿐 **로컬 main을 전진시키지 않는다.** 로컬 main에
source가 없는 상태로 `chezmoi apply`를 실행하면 `not managed`로 실패하고 낡은 파일이
그대로 남는다 — 그런데 완료 판정을 통과할 수 있다.

- [ ] 머지 직후: `git fetch origin && git checkout main && git merge --ff-only origin/main`
- [ ] `[ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" ]` 확인
- [ ] 예상 merge commit이 포함됐는지 확인 (`git log --oneline -1`)
- [ ] `chezmoi source-path <대상>`이 **성공하는지** 확인한 뒤에만 apply

### 원칙 4 — `chezmoi apply`는 경로를 직접 나열한다

`chezmoi status`에 이번 작업과 무관한 대기 항목이 있다 (`.claude/settings.json` MM,
`.codex/skills/*` DA). 인자 없는 apply는 그것까지 건드린다.

- [ ] 경로를 변수에 담아 넘기지 않는다 — zsh는 따옴표 없는 변수를 단어 분할하지 않아
      전체가 한 인자가 되고 `not managed` 오류가 난다 (실측)

---

## 순서: #12 준비 → #6 머지 → #12 머지

`c5231a7` 유실 위험이 가장 비가역적이므로 **#12의 로컬 커밋 처리를 맨 앞에** 둔다.
그 다음은 실사용 피해가 진행 중인 #6이고, #12 머지는 마지막이다.

---

## 작업 0 — #12의 로컬 커밋 보전 (가장 먼저)

- [ ] `git log --oneline origin/codex-pr-review-toolkit..codex-pr-review-toolkit`로
      고유 커밋 목록을 확정한다 (현재 `c5231a7` 1개)
- [ ] 내용을 검토한다. 의도적인 수정이면 **PR에 포함시킨다**:
      `git push origin codex-pr-review-toolkit`
- [ ] 푸시 후 `git rev-list --count origin/codex-pr-review-toolkit..codex-pr-review-toolkit`
      이 **0**임을 확인한다
- [ ] 이 커밋이 리뷰 대상에 포함됨을 작업 B의 리뷰 범위에 반영한다 (오케스트레이터
      SKILL.md +18줄이 리뷰되지 않은 채 머지되면 안 된다)

**푸시하지 않기로 결정할 경우**에도 브랜치를 삭제하지 않는다. 삭제는 모든 고유 커밋이
main 또는 보존 ref에서 도달 가능할 때만 한다.

---

## 작업 A — PR #6 (deep-research)

### A-1. 리뷰 관점

- [ ] `silent-failure-hunter` — **최우선.** 브랜치 커밋 메시지가 스스로 "실패 은닉"을
      22번 고쳤다고 말한다. 남은 은닉이 있는지가 이 PR의 핵심 리스크다. 워크플로는
      서브에이전트 결과를 받아 합성하므로, 한 단계가 조용히 빈 값을 돌려주면 보고서가
      근거 없이 그럴듯해진다 — 사용자가 검증할 수 없는 종류의 실패다.
- [ ] `pr-test-analyzer` — 테스트가 2,231줄로 구현보다 크다. **통과 개수는 품질 지표가
      아니다**(A-2 참조). 실제 실패 경로를 덮는지 판정한다.
- [ ] `code-reviewer` — `Workflow` 계약 준수. 대상 파일은 candidate merge의 것으로 지정한다.

`type-design-analyzer`는 제외한다 — 순수 JS라 타입 설계 대상이 없다.

### A-2. "111개 통과"를 근거로 쓸 때의 한계

테스트 파일을 읽고 확인한 사실이다. `tests/deep-research.test.mjs`는

- 소스에서 `export const meta`를 **제거한 뒤** `AsyncFunction`으로 본문을 실행하고
- `agent`, `parallel`, `pipeline`, `phase`, `log`를 **자체 mock으로 대체**한다

따라서 111개 통과는 **그 에뮬레이터 안에서의 로직**을 검증한다. 실제 `Workflow` loader의
스크립트 파싱, `meta` 리터럴 계약, 병렬 오류 정규화는 **검증하지 않는다.** 통과를
"머지해도 안전하다"의 근거로 쓰면 안 된다 — unit test 근거로만 인용한다.

정적 검증으로 메꾼다 (candidate merge에서 실행):

- [ ] `node --check` 상당의 ESM 파싱 확인
- [ ] `meta`가 순수 리터럴인지 (변수·함수 호출·스프레드·템플릿 보간 없음)
- [ ] 금지 API 부재: `Date.now()`, `Math.random()`, 무인자 `new Date()`
      — 현재 브랜치에서 **0건** 확인
- [ ] `meta.phases`의 title과 실제 `phase()` 호출 문자열 일치 여부
- [ ] TypeScript 문법 부재 (타입 주석·인터페이스·제네릭)

### A-3. 런타임 smoke test — 사용자 승인이 필요하다

워크플로는 `args`가 비면 **에이전트를 하나도 띄우지 않고** `invalid_input`으로 조기
반환한다 (`deep-research.js:395-397`). 즉 빈 인자 실행은 **웹 호출 0, 토큰 거의 0**으로
실제 loader와 `meta` 계약을 검증하는 유일한 경로다.

다만 이 세션에는 "요청 없이 workflows/deep-research를 쓰지 말라"는 사용자 지시가 있다.
따라서 이 단계는 **사용자에게 물어본 뒤에만** 실행한다. 승인이 없으면 A-2의 정적 검증으로
갈음하고, **"런타임 미검증"을 머지 보고에 명시한다.**

- [ ] 사용자 승인 시: 빈 인자로 워크플로를 실행해 `invalid_input` 반환 확인
- [ ] 미승인 시: 그 사실을 PR 코멘트와 최종 보고에 남긴다

**정상 질문으로 전체 실행하는 것은 하지 않는다** — 웹 검색 에이전트를 다수 띄워 비용이
크고 결과가 비결정적이라 통과 기준을 세울 수 없다.

### A-4. `.chezmoiignore`의 `tests/**` 검증

단순 렌더 성공은 근거가 부족하다. 현재 머신의 `machine_type`은 `work`이므로 렌더가
성공해도 **server 분기의 출력은 검증되지 않는다.**

- [ ] `work` / `personal` / `server` 세 값으로 각각 렌더해 ignore 경로 집합을 비교한다
- [ ] `tests/**`가 **조건 블록 밖**(모든 머신 공통)에 있는지 확인한다 — 안으로 들어가면
      work 머신에 `~/tests`가 배포된다
- [ ] `chezmoi status`에 `tests/`가 나타나지 않는지 확인

### A-5. 머지

- [ ] `--merge`(merge commit). squash는 25커밋의 `fix:` 이력을 뭉개고, 그 이력이
      "무엇이 왜 고쳐졌는지"의 유일한 기록이다
- [ ] 리뷰 지적은 반영 후 force-push하고 다시 확인한다. 머지 후 별도 PR로 미루지 않는다
- [ ] 머지 직후 **원칙 3**의 로컬 전진 절차를 실행한다

### A-6. 사후 배포 (여기가 실제 목적)

두 unmanaged 대상을 **한 세트**로 다룬다.

- [ ] 사전 백업 + 해시 기록 (둘 다):
      `~/.claude/workflows/deep-research.js`, `~/.agents/skills/deep-research/SKILL.md`
      → `shasum -a 256`으로 pre-apply 해시를 남기고 `.pre-merge.bak` 사본을 만든다
- [ ] `chezmoi source-path`가 두 대상 모두 성공하는지 확인 (원칙 3)
- [ ] apply — 경로 직접 나열 (원칙 4):
      `chezmoi apply ~/.claude/workflows/deep-research.js ~/.agents/skills/deep-research`
- [ ] **부분 성공을 실패로 처리한다.** 둘 중 하나라도 source와 불일치하면 롤백하고 원인을
      찾는다. 새 워크플로 + 구형 91줄 스킬 조합으로 남는 것이 최악이다
- [ ] 사후 확인: 두 대상 모두 `diff -q`로 source와 일치 + `chezmoi source-path` 성공
      (= 관리 대상으로 전환됨) + 줄 수가 431→1,299, 91→74로 바뀜
- [ ] 확인 후 `.pre-merge.bak` 삭제 여부를 사용자에게 보고

---

## 작업 B — PR #12 (Codex PR 리뷰 툴킷)

### B-1. 리뷰 관점

내용이 **에이전트가 읽고 실행하는 스킬 문서 7개**다. #23에서 확인했듯 이 종류의 결함은
문서 오류가 곧 실행 오류다. 리뷰 대상은 `c5231a7`을 포함한 candidate merge다.

- [ ] `comment-analyzer` — 문서가 단정하는 사실의 정확성. 특히 Codex 스킬이 참조하는
      Claude 쪽 플러그인 경로·이름이 현재도 유효한지. 플러그인 버전이 올라가면 조용히
      깨지는 종류다
- [ ] `code-reviewer` — `symlink_pr-review-toolkit-claude.tmpl`의 링크 대상 실재 여부,
      `.chezmoiignore` server 제외의 정합성, `c5231a7`이 바꾼 발동 경계

### B-2. 검증

- [ ] 심볼릭 링크 대상 존재 확인 (템플릿 렌더 후 경로 실재 여부)
- [ ] `.chezmoiignore` 세 machine_type 렌더 검증 (A-4와 동일 방법) — toolkit 제외 규칙이
      **server 블록 안**에 있어야 한다. 밖으로 나가면 work 머신에서 관리가 빠진다
- [ ] 배포본과 candidate merge 내용 일치 재확인 (`c5231a7`을 푸시했다면 배포본이 낡은
      쪽이므로 `chezmoi apply`가 **필요해진다** — 작업 0의 결정에 따라 달라진다)

### B-3. 머지

- [ ] `gh pr ready 12`로 draft 해제
- [ ] `--merge` 사용 (이유는 A-5와 동일)
- [ ] 머지 직후 **원칙 3**의 로컬 전진 절차
- [ ] `chezmoi status`로 drift 확인. `c5231a7`을 포함시켰다면 해당 경로만 apply

---

## 잔여 위험

### 위험 1 — `.chezmoiignore` 자동 머지가 만드는 중복 블록

두 PR이 같은 파일을 건드린다. 순서대로 머지하면 git이 자동 병합하는데 결과가 **의미상
중복**이다 (실측): 같은 `{{ if eq .machine_type "server" }}` 블록이 둘로 갈린다.
`if`/`end` 균형은 맞고 렌더도 통과한다 — **깨지지는 않는다.**

- [ ] 두 PR 머지 후 별도 커밋으로 블록을 하나로 합친다. 기능 변화가 없으므로 main에 직접
      커밋한다
- [ ] 합친 뒤 **세 machine_type 각각으로 렌더해 ignore 경로 집합이 통합 전과 동일한지**
      비교한다. 수동 통합 중 `tests/**`가 server 블록 안으로 들어가거나 toolkit 제외가
      밖으로 나가도 템플릿은 정상 렌더된다 — 렌더 성공만으로는 못 잡는다
- [ ] `chezmoi status` 재확인 후 커밋

### 위험 2 — 리뷰가 대규모 수정을 요구할 경우

#6은 1,299줄 JS다. #22(327→465줄)에서 리뷰 반영이 원 작업량을 넘었다.

- [ ] 지적이 나오면 **재현부터 한다.** 재현 스크립트가 있는 지적을 먼저 고치고, 추론뿐인
      지적은 근거를 확인한 뒤 판단한다
- [ ] 반영 규모가 커도 머지 전에 끝낸다. 단, 리뷰가 **설계 자체**를 문제 삼으면
      (예: 검증 패널 구조가 틀렸다) 머지를 보류하고 사용자에게 알린다 — 이 계획의
      권한 범위를 넘는다

---

## 완료 판정

전부 참이어야 완료다.

- [ ] #6, #12 둘 다 `gh pr view` → MERGED, `gh pr list --state open`에 없음
- [ ] `git rev-parse HEAD` == `git rev-parse origin/main` (로컬 전진 완료)
- [ ] `~/.claude/workflows/deep-research.js` 1,299줄 + source와 `diff -q` 일치
- [ ] `~/.agents/skills/deep-research/SKILL.md` 74줄 + source와 `diff -q` 일치
- [ ] 위 두 대상 모두 `chezmoi source-path` 성공 (관리 대상 전환 확인)
- [ ] `.chezmoiignore` server 블록이 하나이고, 세 machine_type 렌더 결과가 통합 전과 동일
- [ ] `git rev-list --count origin/<브랜치>..<브랜치>`가 두 브랜치 모두 0 — 그 뒤에만
      브랜치 삭제
- [ ] `git status` 깨끗
- [ ] 런타임 smoke test 실행 여부와 결과를 보고에 명시 (미실행이면 "런타임 미검증"으로)

## 하지 않을 것

- 정상 질문으로 워크플로를 전체 실행하는 것 (비결정적·고비용, A-3)
- 사용자 승인 없이 `Workflow` 도구를 호출하는 것 (세션 지시)
- 브랜치 head에서만 검증하고 머지하는 것 (원칙 1)
- 고유 커밋을 확인하지 않고 브랜치를 삭제하는 것 (작업 0)
- 두 PR을 하나로 합치는 것 (성격이 다르고 각각 이력이 온전하다)
- 리뷰 지적을 "머지 후 별도 PR"로 미루는 것 (방치될 자리를 만든다)
- `chezmoi apply`를 인자 없이 실행하는 것 (원칙 4)

---

## 리뷰 반영 기록

codex adversarial-review 1회, 6건 전부 반영.

| # | 지적 | 반영 |
|---|------|------|
| high | 원격 머지 후 로컬 main을 전진시키지 않아 apply가 실패 | 원칙 3 신설, A-5·B-3에 연결 |
| high | #12 로컬 고유 커밋 `c5231a7` 유실 위험 | 작업 0 신설, 완료 판정에 `rev-list` 검사 추가 |
| high | 역행 검사가 main 쪽 변경과 candidate merge를 보지 않음 | 원칙 1·2 신설 |
| high | "111개 통과"가 Workflow 런타임 근거가 못 됨 | A-2에 한계 명시, A-3에 승인 필요 smoke test 분리 |
| medium | `.chezmoiignore` 조건별 의미 보존 미검증 | A-4·B-2·위험 1에 세 machine_type 렌더 검증 |
| medium | 부분 apply로 skill/workflow 세대 불일치 가능 | A-6을 "두 대상 한 세트"로 재작성 |
