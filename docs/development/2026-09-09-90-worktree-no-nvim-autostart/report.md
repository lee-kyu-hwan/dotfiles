# Quality Goal Report

- Task ID: 20260909T012349Z-90-create-worktree-워크트리-창-0번-페인의-nvim-자동-8a74f29d
- Mode: standard
- Status: COMPLETED
- Created: 2026-09-09
- Updated: 2026-09-09
- Source goal: #90 create-worktree 워크트리 창 0번 페인의 nvim 자동 실행을 제거하고 workmux 설정과 두 create-worktree 스킬 문서를 동기화한다

## Classification

**standard** (요청 모드 `auto`, 위험 스캔 후 자동 선택).

- strict 트리거 없음: 인증·권한·테넌시·결제·PII·비밀정보·스키마 마이그레이션·파괴적 연산·공개 API/웹훅/큐·프로덕션 인프라 어디에도 해당하지 않는다. 이슈 #90 라벨은 `enhancement`·`P3-low`.
- standard 조건(다중 파일·계층): 설정 계층과 문서 계층이 함께 바뀐다. 사용자 확인을 거쳐 `dot_local/bin/executable_tmux-stack-layout` 이 추가돼 **네 파일**이 됐다.
- standard 조건(비자명한 인터페이스 계약): 두 `SKILL.md` 는 frontmatter 3줄을 제외한 본문이 바이트 동일해야 한다는 교차 파일 불변식을 가진다.
- standard 조건(요구사항 명시화 필요): 사용자가 AC·비목표·규모 상한(요구사항 12건·AC 25건)을 명시적으로 요구했고, 검증 경로가 부작용 제약(새 워크트리 생성 금지)으로 한정된다.
- light 배제: 이 nvim 자동 실행을 검증하는 기존 타깃 테스트가 없어 light 의 '기존 타깃 검증으로 증명 가능' 조건이 성립하지 않는다.

## Review history

| 산출물 | 라운드 | score | verdict | 블로커 |
|---|---|---|---|---|
| Spec | 1 | 74 | REVISE | `SPEC-001`·`SPEC-002`·`SPEC-003` |
| Spec | 2 | 83 | REVISE | `SPEC-012` |
| Spec | 3 | 93 | **PASS** | — |
| Plan | 1 | 85 | REVISE | `PLAN-001` |
| Plan | 2 | 95 | **PASS** | — |
| Code | 1 | 94 | **PASS** | — |

### Spec 라운드 1 → 2

블로커 3건 모두 "검증 명령이 실제로 검증하지 않는다" 는 한 뿌리였다.

- `SPEC-001`(High): `CMD-4` 행의 이스케이프 안 된 파이프(`<branch-name|pr-ref>`)로 마크다운 표가 6칸으로 깨져, 표에서 기계 추출하면 명령이 절단됐다. 측정: 그 줄의 `|` 5개, 이스케이프 0개, 분해 셀 6개.
- `SPEC-002`(High): `CMD-3` 의 금지어가 두 스킬 문서의 실제 문언 `레이아웃은 nvim만 실행` 을 하나도 잡지 못했다. 네 금지어 대조 결과 전부 `False`.
- `SPEC-003`(High): `CMD-6` 이 `git diff` 로 index 대 working tree 만 비교해, 커밋이 허용된 이 작업에서 판정력을 잃었다.

사용자가 이 라운드에 원칙을 지시했다 — "판정 명령은 변경 전 baseline 에서 반드시 실패하고 변경 후에 통과해야 한다. 음성 대조가 없으면 그 명령은 채택하지 않는다." 이 원칙이 Spec 의 Test strategy 절에 문장으로 들어갔고, `CMD-2`·`CMD-4` 는 baseline 에서 통과하는 **불변식 명령**으로 정직하게 분류해 고의 위반 입력으로 음성 대조를 증명하게 했다.

### Spec 라운드 2 → 3

라운드 2 개정이 **회귀**를 만들었다. `SPEC-012`(High): 금지어 `nvim만 자동 실행` 을 `nvim만 실행` 으로 **교체**해, `dot_config/workmux/config.yaml:9` 의 현재 문구를 판정에서 놓쳤다(`nvim만 자동 실행한다` 에는 `nvim만 실행` 이 부분 문자열로 없다).

리뷰어는 이것을 `SPEC-002` 재발이 아니라 **새 결함**으로 판정했다. 근거: 라운드 1 `SPEC-002` 의 대상은 두 스킬 문서였고 그 요구는 충족됐으며, `config.yaml:9` 는 라운드 1 스냅샷의 금지어로 이미 덮여 있었으므로 라운드 1 시점에는 결함이 아니었다. 따라서 블로킹 ID 재발에 해당하지 않아 `NEEDS_REDESIGN` 으로 가지 않았다.

라운드 3 개정은 금지어를 **복원**(`nvim만 실행` 은 유지)하고 `config[:config.index("panes:")].rstrip("\n") == config_expected` 블록 등가 비교를 도입해 닫았다.

라운드 3 리뷰의 첫 응답은 `verdict: PASS` 인데 `evidence` 에 `verified: false` 항목 세 건(도구 제약 메타 진술)이 있어 검증기가 `PASS reviews must not contain unverified evidence` 로 거부했다. `record-review-error` 로 기록하고 1회 재시도했으며, 재시도 응답은 근거 표기만 바로잡아 score 93 / 근거 16건 전부 `verified: true` 로 통과했다. 이 오류는 리뷰 라운드를 소비하지 않았다.

### Plan 라운드 1 → 2

`PLAN-001`(High): T2 의 `CMD-4` 음성 대조 하네스가 sh 단일 인용 안에서 **이중 백슬래시**(`b"---\\n"`)를 써서, 어떤 위반을 주입했는지와 무관하게 첫 단언이 항상 실패했다. 위반 생성 스크립트도 무연산이었다. 네 사례의 종료 코드 1 이 주입한 위반이 아니라 하네스 결함에서 나온 **거짓 증거**였다.

**이것은 오케스트레이터의 사전 점검이 놓친 결함이다.** 라운드 1 사전 점검은 음성 대조 절차가 "구체 명령으로 적혔다" 는 형식만 확인하고 하네스를 실행 검증하지 않았다. 리뷰어가 그 사실까지 지적했다.

라운드 2 개정 후 하네스를 기계 추출해 직접 실행한 결과: 전체 종료 코드 0, 양성 대조 stderr **0바이트**, A·B·C·D 각각 `AssertionError` 이며 실패 단언이 서로 다르다(A=`cb == ab`, B=`extra in cf`, C=agents 키 전용성, D=`extra in cf`).

함께 `PLAN-002`(양성 대조 부재), `PLAN-003`(롤백 후 검증이 `CMD-8` 계약의 절반만 남기고 종료 코드를 판정 근거로 씀), `PLAN-004`(태스크별 실패 처리 부재)도 닫았다.

부수적으로 `revision_check` 도구 제약을 만났다 — 추적표의 `Task` 셀에서 첫 태스크만 인식해 `| AC-3 | T1, T2, T3 |` 행이 빈 칸 2개를 만들었다. 임시 사본으로 태스크별 세 행 분리가 `passed: true` 를 내는 것을 확인한 뒤 그 형태를 적용했다(추적표 10행 / AC 8종).

### Code 라운드 1

score 94, PASS. 블로커 없음. Low 3건이 남았다(아래 Remaining advisory findings).

## Blocking-finding resolutions

| finding | 라운드 | 적용한 해소 | 검증 증거 |
|---|---|---|---|
| `SPEC-001` | Spec 1 | `CMD-4` 의 리터럴 파이프를 `bytes([124])` 로 만들어 표 셀을 깨지 않게 했다 | 판정 명령 표 8행 전부 `|` 분해 5칸, 추출 문자열과 원문 셀이 문자 단위 일치 8/8 |
| `SPEC-002` | Spec 1 | 금지어에 `nvim만 실행` 추가, `normalize` 로 줄바꿈 정규화한 기대 문장 등가 비교 | baseline 전사에서 `CMD-3` 종료 코드 1 |
| `SPEC-003` | Spec 1 | `CMD-6`·`CMD-8` 에 baseline SHA `9ff32a30c9498df007ec5dfa558a442cc7841be1` 를 박고 staged·committed·untracked 를 함께 판정 | baseline 전사에서 `CMD-6` 종료 코드 1 (`AssertionError: []`) |
| `SPEC-012` | Spec 2 | 금지어 `nvim만 자동 실행` **복원**(`nvim만 실행` 유지) + `panes:` 앞 주석 영역 전체 블록 등가 비교 | 반례 1 재측정: 라운드 2 종료 코드 0 → 라운드 3 **1** |
| `PLAN-001` | Plan 1 | 하네스의 이중 백슬래시를 실제 개행으로 고쳐 `run_cmd4` 가 Spec `CMD-4` 와 같은 프로그램을 실행하게 했다. 양성 대조 단계를 추가했다 | 하네스 실행 검증: 전체 종료 코드 **0**, 양성 대조 stderr **0바이트**, A·B·C·D 각각 종료 코드 1 이며 실패 단언이 서로 다름 |

## Plan approval

- Approval timestamp: `2026-09-09T14:09:11Z`
- Plan digest: `e3d27d7c8f6a4f00b78b4ee340c36a64e4efa7e53f433da5d4290ae8d21e92d8`

사용자가 승인 게이트에서 "승인 — 구현 시작" 을 선택했다. `approve-plan` 이 Plan 리뷰가 통과시킨 digest 와 일치함을 확인한 뒤 기록했다.

## Changed files

baseline `9ff32a30c9498df007ec5dfa558a442cc7841be1` 대비 **정확히 네 파일**. 커밋은 만들지 않았다 — Plan 이 작업 트리 편집만 지시했고 롤백도 그 전제에 의존한다.

| 파일 | 의도한 변경 |
|---|---|
| `dot_config/workmux/config.yaml` | `panes` 첫 항목 `- command: nvim` → `- {}`. `panes:` 앞 주석 두 블록을 "어떤 프로그램도 자동 실행하지 않는다 / 모든 pane 은 빈 셸" 로 교체. 나머지 두 pane 선언과 `status_format: false`·`base_branch: auto`·`nerdfont: true` 는 보존 |
| `dot_claude/skills/create-worktree/SKILL.md` | `## 주의사항` 첫 항목을 "에이전트(Claude·Codex)를 포함해 어떤 프로그램도 자동 실행하지 않는다. 레이아웃의 세 pane 은 모두 빈 셸" 로 교체 |
| `dot_agents/skills/create-worktree/SKILL.md` | 위와 **완전히 같은 문언**으로 교체. 본문 바이트 동일성 유지 |
| `dot_local/bin/executable_tmux-stack-layout` | 3-pane 분기 주석 세 줄 교체. nvim 전제를 제거하고 열 단위 배치 근거를 확인된 사실로 다시 썼다. 13행 복구 역할 주석과 **실행 코드는 한 줄도 바꾸지 않았다** |

워크플로우 산출물: `docs/development/2026-09-09-90-worktree-no-nvim-autostart/{spec,plan,report}.md` (untracked), `.claude/quality-state/<task-id>/**` (`.gitignore:25` 로 무시됨).

### 열 단위 배치 근거의 사실성

사용자는 이 주석을 다시 쓸 때 **확인 가능한 사실만** 쓰고 추측을 금지했다. 두 주장을 코드·설정에서 도출했다.

- "workmux 기본 배치(좌 1개(세로 전체) + 우 2개(상하))와 같다" — `config.yaml` 의 `panes` 가 `[{}, {split: horizontal, focus: true}, {split: vertical}]` 이므로 좌 1개 + 우 상하 2개가 만들어진다.
- "행 단위로 쌓으면 좌측 패인의 높이가 절반으로 줄어든다" — 같은 스크립트의 `n <= 6` 분기가 `top=$(( n / 2 ))`, `rows=( $top $(( n - top )) )` 이므로 `n=3` 이면 `rows=(1 2)` 이고 행 높이가 `avail_h / nrows` 로 분배돼 좌측 패인이 상단 행 단독으로 창 높이의 약 절반이 된다.

리뷰어는 `H=24·25·26` 산술 실측(top_height 12·12·13)으로 이 계산을 교차 확인했다.

## Verification evidence

### 판정 명령 8개 — 두 독립 측정

명령 문자열은 **Spec 정본**의 판정 명령 표에서 정규식으로 기계 추출했다. 전사: `.claude/quality-state/<task-id>/verification-transcript.md`

| CMD | 구현 전 baseline | 구현 후 (오케스트레이터) | 구현 후 (대칭 점검) |
|---|---|---|---|
| CMD-1 | 1 | **0** | 0 |
| CMD-2 | 0 (불변식) | **0** | 미실행 (읽기 전용 제약) |
| CMD-3 | 1 | **0** | 0 |
| CMD-4 | 0 (불변식) | **0** | 0 |
| CMD-5 | 1 | **0** | 0 |
| CMD-6 | 1 | **0** | 0 |
| CMD-7 | 1 | **0** | 0 |
| CMD-8 | 1 | **0** | 0 |

`CMD-2` 는 두 조건에서 확인했다 — `XDG_STATE_HOME` 격리 하 0, 격리 없는 정상 셸(배포 환경에 더 가깝다) 0.

### 불변식 명령의 음성 대조 (구현 후)

| 하네스 | 사례 | 종료 코드 |
|---|---|---|
| CMD-2 | positive | 0 |
| CMD-2 | `panes[0].split: BROKEN` | 1 (`unknown variant \`BROKEN\``) |
| CMD-4 | positive | 0 |
| CMD-4 | A (agents 본문 한 줄 추가) | 1 (`cb == ab`) |
| CMD-4 | B (claude 세 줄 삭제) | 1 (`extra in cf`) |
| CMD-4 | C (agents 에 세 줄 추가) | 1 (agents 키 전용성) |
| CMD-4 | D (세 줄 순서 뒤바꿈) | 1 (`extra in cf`) |

### 두 스킬 문서 불변식 — 사용자가 요구한 핵심 계약

```
본문 바이트 동일: True (19344 바이트)
claude frontmatter 에만 세 줄: True
frontmatter diff 가 정확히 그 세 줄: True
```

`diff` 명령 교차 확인:

```
4,6d3
< argument-hint: <branch-name|pr-ref> [target-session]
< user-invocable: true
< allowed-tools: Bash
```

### 실제로 실행한 그 밖의 결정적 검사

| 검사 | 결과 |
|---|---|
| gitleaks (네 변경 대상 각각) | `no leaks found`, 종료 코드 0 |
| `bash -n dot_local/bin/executable_tmux-stack-layout` | 통과 |
| `yaml.safe_load` 로 config 파싱 | 통과 (키: `base_branch`·`nerdfont`·`panes`·`status_format`) |
| `git log <baseline>..HEAD` | 비어 있음 — 커밋 없음 |
| 배포본 `~/.config/workmux/config.yaml` SHA-256 | `f3dc146c264371c6149b4c18e6b46ead1ba17eb9672058b5596fdb3d15488ac4` — 워크플로우 내내 불변 |

### 검증 범주별 결과

| 범주 | 상태 | 근거 |
|---|---|---|
| 타깃 테스트 | **not configured** | `tests/` 에는 `tmux-open-pr.test.sh`(대상: `tmux-open-pr` 스크립트)와 `deep-research.test.mjs` 두 파일뿐이다. 두 파일에서 `tmux-stack-layout`·`workmux`·`create-worktree` 등장 횟수는 각각 **0** 이다 |
| 전체 스위트 | **not configured** | 위와 같다. 최상위에 `package.json`·`Makefile`·`justfile`·`pyproject.toml` 이 없고 `.github/workflows` 도 없다 |
| 타입 검사 | **not configured** | 변경 파일은 YAML 주석·Markdown 문서·Bash 주석이다 |
| 린트 | **실행함, 통과** | `.pre-commit-config.yaml` 의 유일한 훅은 gitleaks 다. `pre-commit` 은 미설치이나 `gitleaks` 로 직접 실행했다 |
| 문법 검사 | **실행함, 통과** | `bash -n`, `yaml.safe_load` |
| 빌드 | **not configured** | chezmoi source 저장소이며 빌드 단계가 없다 |
| E2E / 실제 창 생성 | **의도적으로 실행하지 않음** | 사용자가 금지했다. 실제 창 동작은 배포(`chezmoi apply`) 후 사용자가 다음 워크트리를 만들 때 확인된다 — Spec·Plan 이 그렇게 정했고 어떤 AC 도 그것을 판정 수단으로 삼지 않는다 |

### 구현 라운드 1 이 중단된 이유 (환경 제약, Plan 결함 아님)

Codex 는 T1 사전 판정에서 `CMD-2` 가 기대값 0 대신 **101** 을 내자 source 를 편집하지 않고 중단하고 `status: blocked` 로 보고했다 — Plan 의 중단 규칙(`PLAN-004` 해소로 들어간 것)을 정확히 따른 것이다.

```
panicked at tracing-appender-0.2.4/src/rolling.rs:154:14:
initializing rolling file appender failed: InitError { context: "failed to create initial log file",
source: Os { code: 1, kind: PermissionDenied, message: "Operation not permitted" } }
```

`workmux` 가 `~/.local/state/workmux/workmux.log` 에 rolling log 를 만들려 하는데 `workspace-write` 샌드박스가 워크스페이스 밖 쓰기를 막아 panic 했다. `workmux` 가 `XDG_STATE_HOME` 을 따르는 것을 실측으로 확인해 그 값을 Git-ignored 경로(`.claude/quality-state/<task-id>/xdg-state`)로 두어 해소했다. **판정 명령 문자열은 바꾸지 않았다** — 환경변수는 명령 밖에서 설정한다.

### Codex 가 보고한 Plan 이탈 3건

| 이탈 | 판정 |
|---|---|
| T4 사전 `CMD-8` 을 T1~T3 시작 전에 실행하지 않고 누락 | **실제 절차 이탈.** `CODE-001`(Low)로 기록됐다. 구현 당시의 before 증거가 없다. 오케스트레이터가 구현 전 baseline 전사에서 `CMD-8`=1 을 측정해 두었으나, 그것이 구현 당시의 실행을 대체하지는 않는다 |
| 첫 `CMD-3` 사전 wrapper 의 과도 이스케이프 | 결과를 폐기하고 정본 명령으로 재실행했다. 네 source 가 Plan 재구성 결과와 바이트 동일해 wrapper 오류가 구현에 섞인 흔적이 없다 |
| 음성 대조 하네스에 전사 보존 줄 추가 | Plan 라운드 2 의 `PLAN-005`(양성 대조 실패 시 진단 출력 소실)를 구현 단계에서 해소한 것이다. 하네스를 Plan 코드 블록과 diff 해 차이가 shebang 및 성공 경로의 출력 `cp` 뿐이고 검사·변형 프로그램이 동일함을 확인했다 |

## Remaining advisory findings

모두 Low 이며 루브릭상 게이트를 막지 않는다.

| ID | 내용 | 후속 |
|---|---|---|
| `SPEC-015` | `CMD-3` 의 `first_item` 이 다음 목록 항목의 존재를 필수로 가정한다. 주의사항 절에 항목이 하나뿐이면 `ValueError` 로 종료 코드 1(거짓 실패, fail-closed) | 두 스킬의 주의사항 절은 각각 **3개 항목**이고 이 작업은 항목을 지우지 않았다(구현 후 확인). 향후 Spec 개정 시 EOF 를 항목 끝으로 처리하도록 보완 |
| `SPEC-016` | AC-3 산문은 금지 리터럴을 여섯 개 열거하지만 `CMD-3` 의 `banned` 튜플은 일곱 개(`nvim만 자동 실행` 포함). 명령이 AC 보다 엄격하므로 판정 공백은 없다 | 향후 Spec 개정 시 AC-3 열거를 명령과 일치시킨다. 그 한 리터럴이 라운드 2 회귀의 원인이었으므로 다시 삭제되지 않게 주의 |
| `PLAN-005` | 음성 대조의 **양성 대조가 실패할 경우** 진단 출력이 소실된다(`set -e` 로 `cat` 전에 종료되고 EXIT trap 이 scratch 를 지운다) | 구현 단계에서 Codex 가 전사 보존 줄을 추가해 실질적으로 해소했다(Plan 이탈 3번) |
| `CODE-001` | T4 사전 `CMD-8` 실패 기록 누락 | 이 보고서에 이탈로 명시했다. 향후 구현에서 Plan 이 지정한 사전 판정 순서를 실행 시점 그대로 지킨다 |
| `CODE-002` | `executable_tmux-stack-layout:10` 이 바로 위 9행 항목 제목과 같은 문구를 되풀이해 동어반복이 됐다. 사실 관계는 맞고 `CMD-5` 의 required 리터럴과 문자 단위로 일치한다 | 문구를 다듬으려면 Spec `CMD-5` 의 required 리터럴도 함께 개정해야 하므로 선택적 후속 작업으로 둔다. 현 상태가 승인 정본과 일치한다 |
| `CODE-003` | `CMD-2` 를 `eval` 로 현재 셸에서 실행하면 `trap ... EXIT` 가 셸 종료까지 미뤄져 고정 경로 잔존물이 남고 재실행이 즉시 실패한다 | **오케스트레이터 실측에서 실제로 발생했고 정리했다.** 이 판정 명령을 재사용할 때는 반드시 서브셸(`zsh -c`/`bash -c`)로 실행한다. 향후 Spec 개정 기회가 있으면 고정 경로 대신 `mktemp -d` 기반으로 바꾼다 |

### 워크플로우 위생 후속

- `.claude/quality-state/` 는 `.gitignore:25` 로 이미 무시된다. 추가 조치가 필요하지 않다.
- 세션 중 머신이 재부팅되어 대화형 Codex 프로세스와 스크래치패드 스크립트가 소실됐다. 저장소·상태 파일·배포본은 온전했고 스크립트를 복구해 재측정했다. 복구 전 한 차례 빈 명령을 실행한 무효 측정이 있었고 그 사실을 전사에 남겼다.
- 고정 경로 세 개(`/private/tmp/workmux-config-parse-90`, `/private/tmp/create-worktree-skill-negative-90`, `/private/tmp/workmux-config-parse-90__worktrees`)는 현재 모두 비어 있다.

## 남은 작업 (이 워크플로우 범위 밖 — 사용자 결정 사항)

1. **커밋** — 이 브랜치 커밋은 허용됐으나 Plan 이 작업 트리 편집만 지시했고 롤백이 그 전제에 의존하므로 만들지 않았다.
2. **배포** — `chezmoi apply` 는 금지됐다. 사용자가 직접 실행할 때 배포본에 반영된다.
3. **실제 동작 확인** — 배포 후 사용자가 다음 워크트리를 만들 때 0번 pane 이 빈 셸로 열리는지 확인된다. 이 변경은 **앞으로 만들어지는 창에만** 영향을 주며 이미 열려 있는 창·pane·프로세스는 건드리지 않았다.
4. **머지** — 금지됐다.

## Final status

- Status: **completed**
- Machine-readable reason: `COMPLETED`

Spec 3 라운드(74 → 83 → 93 PASS), Plan 2 라운드(85 → 95 PASS), Code 1 라운드(94 PASS)로 모든 게이트를 통과했다. 판정 명령 8개가 구현 후 전부 종료 코드 0 이며 두 독립 측정이 일치한다. 남은 findings 는 Low 6건이고 게이트를 막지 않는다.
