---
title: AI 에이전트 작업 관리 도구 — 자체 개발 필요성 독립 검증
date: 2026-09-16
kind: research (문서·원본 소스 정적 검증, 설치·실행 없음)
status: 미커밋 로컬 문서
---

# 조사 방법과 한계

- Orca `stablyai/orca` v1.4.197 (HEAD 615b137, 2026-09-15) shallow clone, `ZinkLu/Orca-Orchestration` 전체 clone 을 읽었다. cmux·Herdr·Codex·Claude Code·GitHub·양사 약관은 공식 문서를 WebFetch 했다.
- 조사 에이전트 4개를 병렬로 돌리고, 결론을 좌우하는 주장은 루트가 소스를 다시 열어 재확인했다.
- 설치·로그인·실행은 하지 않았다. 따라서 "실제 실행 검증" 열은 모두 비어 있다. 아래 판정은 문서상 지원과 소스상 구현까지다.
- 사용자 설계 #98·#99·#104·#121 과 dotfiles 의 `ai-session` 계정 프로필 구현을 함께 읽었다.

# 결론

1. **핵심 문제는 기존 도구가 해결하지 못한다.** "지금 시작 가능한 것·함께 실행 가능한 것·무엇 때문에 대기 중인지·완료 보고가 검증됐는지" 를 계산해 주는 도구는 조사 범위 안에 없다. Orca 가 데이터 모델은 가장 가깝지만 완료를 테스트·PR 로 검증하지 않고, 선행 Task 의 코드를 후속 worktree 로 옮기지 않으며, 공통 파일·계약 충돌 개념이 없다.
2. **그러나 그 핵심 문제는 #98 이 그리는 크기의 제품을 요구하지 않는다.** 의존성 그래프의 원본은 GitHub 서브 이슈와 issue dependencies 로 이미 존재한다. 부족한 것은 그 그래프에 로컬 근거를 합쳐 "다음 행동" 을 계산하는 얇은 계층이다.
3. **추천은 "얇은 별도 계층" 이다.** 독립 제품도, 기존 도구 도입도 아니다. #98·#99 의 실행·전달·복원 runtime 은 미루고, 판단 계층을 먼저 CLI 로 만들어 실제 에픽 하나로 검증한다.
4. **tmux 유지는 구현 수단 선호다.** 다만 Orca·Herdr 로 갈아타도 핵심 문제는 남으므로, tmux 를 버릴 이유가 없다.
5. **계정 격리는 Claude 는 공식 문서로, Codex 는 문서와 소스로 뒷받침된다.** 사용자의 `ai-session` 이 이미 그 방식이다. 디렉터리 격리가 정지를 막는다는 근거는 어느 공식 문서에도 없다.

# 요구사항 매트릭스

범례: ○ 기본 지원 / △ 설정·확장 필요 / × 미지원 확인 / ? 확인 불가. 각 칸은 "문서상/소스상" 이며 실행 검증은 없음.

| 요구 | Orca 단독 | Orca + coordinator 에이전트 | Orca + Orca DAG | cmux | Herdr | GitHub 자체 |
|---|---|---|---|---|---|---|
| 에픽을 논리 단위로 묶기 | △ Run 이 objective 하나를 갖는 namespace | △ 동일 | △ 동일 | × 그룹은 사이드바 묶음 | × | ○ 서브 이슈 100개·8단계 |
| 서브 이슈 간 의존성 표현 | ○ Task.deps + parent_id | ○ | ○ | × | × | ○ blocked_by/blocking, REST·GraphQL |
| 준비된 작업 자동 판정 | ○ pending→ready 를 SQL 로 승격 | ○ | ○ | × | × | △ blocked 표시만 |
| 준비된 작업 자동 배정 | × CLI 경로에서 은퇴. 잔존 RPC 루프 있음 | △ 에이전트가 worker-start 호출 | ○ viewer 서버가 3.5초 폴링, 최대 16 | × | × | × |
| 병렬 안전성(파일·계약·자원 충돌) | × 개념 없음. stale-base 가드는 은퇴 루프 안에만 | × | × 모든 worker 가 같은 worktree | × | × | × |
| 실패 시 후속 처리·재시도 | △ `--retry-of`, circuit_broken. 자동 재시도 없음 | △ 에이전트 판단 | × failed 는 종료, 하위는 pending 채 "완료" 로 종료 | × | × | × |
| 재시작 후 재개 | ○ SQLite, runtime_epoch, consumer_generation | ○ | × 상태가 메모리 전용 | 해당 없음 | ○ 세션 유지 | 해당 없음 |
| 선행 코드의 후속 worktree 전달 | × `merge_ready` 는 무시됨, base 는 호출자 책임 | × | × | × | × | △ 브랜치·PR 로 사람이 |
| 완료 보고를 테스트·PR 로 검증 | × worker_done 은 발신자·dispatch 유효성만 검사 | × | × | × | × | △ CI·리뷰 상태는 있음 |
| 사람 판단 요청 | ○ decision gate, ask | ○ | ○ | × | △ blocked 상태 | △ 라벨·리뷰 |
| 오케스트레이터 지시 이력 | ○ Run inbox 메시지 | ○ | △ | × | × | △ 이슈 코멘트 |
| 멀티머신 통합 관측 | ○ Remote Server, beta. 연결 끊겨도 서버가 실행 소유 | ○ | × | △ SSH·원격 tmux beta | ○ 머신별 서버, 끊김 시 dimmed 캐시 표시 | 해당 없음 |
| 계정별 인증 격리 | ○ 세션마다 CLAUDE_CONFIG_DIR/CODEX_HOME 고정 | ○ | × 개념 없음 | ? | △ pane env 주입 가능 | 해당 없음 |
| tmux 안의 기존 에이전트 관측 | × 자체 PTY. tmux 는 역방향 shim 만 | × | × | △ 병용 | × 자체 멀티플렉서 | 해당 없음 |
| 테스트·성숙도 | orchestration 283 파일 중 103 테스트 | 동일 | 테스트 0, 커밋 21, 1개월 개발 후 정체 | GPL, 활발 | Apache, 활발 | GA |

# 질문별 답변

## 1. 핵심 문제는 기존 도구로 해결되는가

아니다. 표의 "병렬 안전성", "코드 전달", "완료 검증" 세 줄이 전부 × 다. 이 셋이 사용자가 가장 중요하다고 한 문제의 본체다. 나머지 줄은 Orca 나 GitHub 가 이미 채운다.

## 2. Orca 단독 / + 오케스트레이터 / + Orca DAG

- **Orca 단독**: Run·Task·Dispatch·gate·inbox 가 SQLite 에 내구성 있게 있다. 배정은 없다. `orchestration run`·`coordinator-start` 는 "performs no effects" stub 이다 (`src/cli/specs/orchestration.ts:238,249`). 자동 루프 `Coordinator` 는 코드에 남아 있고 RPC `orchestration.run` 으로 도달 가능하다. 문서의 "Run 은 절대 스케줄하지 않는다" 는 CLI 표면에서만 참이다.
- **Orca + coordinator 에이전트**: 공식 권장 경로다. 에이전트가 `task-list` 로 ready 를 보고 `worker-start` 하고 `check --wait` 로 worker_done 을 받는다. 수준 A 는 된다. 수준 B 는 에이전트 프롬프트 품질에 전적으로 의존하고, 실행 중 Task 수정은 `task-update --status/--result` 뿐이라 그래프 재작성은 새 Task 추가로만 가능하다.
- **Orca + Orca DAG**: 정직한 얇은 래퍼다. 서버가 3.5초 폴링으로 ready 를 배정한다 (`server/src/coordinator.ts:73,239`). 그러나 상태가 모듈 전역 메모리뿐이고 (`coordinator.ts:78`), ready 도 in-flight 도 없으면 stuck 과 완료를 구분하지 않고 종료하며 (`coordinator.ts:243`), 모든 worker 가 `--worktree "current"` 로 같은 worktree 를 쓴다 (`coordinator.ts:303`). 테스트 파일 0개, `AGENTS.md` 가 이를 자인한다. 커밋 21개, 2026-07-14~08-14, 이후 정체. 참고 자료로는 좋고 의존 대상은 아니다.

## 3. GitHub 에픽·서브 이슈 연결

GitHub 자체가 원본이 될 수 있다. 서브 이슈는 부모당 100개, 8단계이며 진행률 필드가 있다. Issue dependencies 는 2025-08-21 changelog 로 공개됐고 REST `/issues/{n}/dependencies/blocked_by` 와 GraphQL `blockedBy`/`blocking` 이 있다. 사용자 저장소에서 실측했다.

| 항목 | #98 실측 |
|---|---|
| 서브 이슈 | 1개 (#99) |
| blockedBy / blocking | 0 / 0 |

즉 현재 에픽은 GitHub 그래프를 쓰지 않고 Mermaid 를 손으로 그린다. Orca 는 Projects 뷰에서 parentIssue·SUB_ISSUES_PROGRESS 를 읽지만 (`src/shared/github/project-types.ts`) 이를 Run/Task 로 변환하는 코드는 없다. 그 변환기가 사용자가 만들어야 할 첫 조각이다.

## 4. 시각화가 다음 행동 판단까지 돕는가

- Orca 대시보드는 attention/working/done/idle 4열이고 근거는 훅·OSC 9999·타이틀 추론·프로세스 증거 7종이다 (`src/shared/agent-status-observation.ts`). 이는 "에이전트가 뭘 하는가" 이지 "다음에 뭘 해야 하는가" 가 아니다.
- Orca DAG 는 그래프를 실시간으로 그리지만 노드 상태는 Orca Task status 를 그대로 비춘다. 실패 원인·병목·충돌은 표시하지 않는다. Mermaid 를 동적으로 보여주는 수준이 맞다.
- 사용자가 원하는 "왜 대기 중인가, 병목은 무엇인가, X 가 끝나면 무엇이 열리는가" 는 그래프 위에 계산이 필요하다. 어느 도구도 하지 않는다.

## 5. 실패·승인 대기·재시작·연결 끊김·사용량 제한

- Orca: 승인은 gate 로 Task 를 blocked 시킨다. heartbeat 10분 무응답은 경고만 하고 자동 실패시키지 않는다. 재시작은 epoch·generation fencing 으로 이전 소비자를 차단한다. 사용량 제한을 인식해 Run 을 다루는 코드는 못 찾았다.
- Herdr: 연결 끊김은 dimmed 캐시로 표시하고 입력을 막는다. `agent prompt --wait` 는 5초만 관찰하며 문서가 "timeout 이 입력 미전송을 증명하지 않는다" 고 명시한다. turn 단위 추적은 "does not track individual turns" 로 부정한다.
- Orca DAG: 실패 노드의 하위가 영원히 pending 이고 서버 재시작 시 재개 불가.

## 6. 코드 전달과 최종 통합의 책임

전부 사람 또는 에이전트다. Orca 는 `worker-start --base-branch` 로 호출자가 base 를 정하고, `merge_ready` 메시지는 coordinator 가 `break` 로 무시한다 (`coordinator.ts:193`). "선행 Task completed" 와 "그 커밋이 후속 worktree 의 base 에 포함됨" 을 구분하는 도구는 없다. 사용자 설계 #104 의 "Git branch·commit·PR 로 결과 전달" 원칙이 맞고, 후속 worktree 생성 시 선행 브랜치 head 를 base 로 검증하는 로직은 직접 써야 한다.

## 7. 계정별 인증 격리

| 항목 | Claude Code | Codex |
|---|---|---|
| 환경변수 범위 | 공식: 설정·세션·플러그인·`.credentials.json` 모두 CLAUDE_CONFIG_DIR 아래. macOS Keychain 항목도 그 디렉터리로 키잉 | 공식: "config, auth, logs, sessions, skills" 가 CODEX_HOME 아래 |
| Keychain/keyring | 문서상 격리됨 | 저장 모드 file/keyring/auto. keyring 모드에서 CODEX_HOME 별 키잉 여부 확인 불가 |
| 인증 우선순위 | 공식 목록: 클라우드 → ANTHROPIC_AUTH_TOKEN → ANTHROPIC_API_KEY → apiKeyHelper → CLAUDE_CODE_OAUTH_TOKEN → profile → /login | 소스: CODEX_API_KEY → ephemeral → CODEX_ACCESS_TOKEN → auth.json. OPENAI_API_KEY 는 경로에 없음 |
| 실행 중 교체 | 문서 없음 | 소스: refresh 가 auth.json 을 되쓰고, `reload_if_account_id_matches` 가 account_id 불일치 시 리로드 거부. 교체 금지 원칙이 옳다 |
| 재개 격리 | transcript 가 같은 디렉터리 아래 | sessions 가 CODEX_HOME 아래, 교차 재개 동작 문서 없음 |

정책: OpenAI 약관은 복수 계정을 언급하지 않지만 "circumvent any rate limits or restrictions" 를 금지한다. Anthropic Usage Policy 는 밴 회피용 새 계정과 복수 계정 악용 조율을 금지하며 사용량 제한 우회 목적 복수 계정을 직접 겨냥한 조항은 찾지 못했다. Orca hot-swap 문서는 목적을 "multiple Codex accounts to maximize tokens" 라고 적는다. 이는 OpenAI 조항과 충돌 소지가 있다. 디렉터리 격리가 정지를 막는다는 근거는 없다. 토큰 자체가 account_id·email·plan_type 을 담는다.

추가 구현 필요분: 사용자의 `ai-session` 이 이미 프로필 선택·verifier·env 고정을 한다. 남은 것은 task registry 와의 binding, 재개 시 profile 불일치 보류다. 이는 #94/#95 범위다.

## 8. tmux 는 본질적 요구인가

수단이다. 본질은 세 가지다. 사람이 언제든 붙어 진단할 수 있는 터미널, UI 를 닫아도 지속되는 실행, 기존 스킬·키바인딩 자산. Orca 는 자체 PTY 로 이 셋을 다르게 제공하고 tmux 안의 에이전트는 관측하지 못한다. Herdr 는 tmux 를 대체한다. 어느 쪽도 핵심 문제를 풀지 않으므로 tmux 를 버려서 얻는 것이 없다. 반대로 tmux 유지가 자체 runtime 의 정당화 근거도 아니다.

## 9. 추천

**얇은 별도 계층.** 순서는 다음과 같다.

1. 의존성 원본을 GitHub 서브 이슈 + blocked_by 로 옮긴다. Mermaid 수작업을 없앤다.
2. `next` 성격의 CLI 를 만든다. 입력은 GitHub 그래프, 로컬 worktree·브랜치 head, PR·CI 상태, 이슈 본문에 적은 충돌 메타데이터. 출력은 ready·blocked(사유)·병목·사람 판단 필요·검증되지 않은 완료 목록. 실행·전달은 하지 않는다.
3. 오케스트레이터가 이 출력을 읽고 배정한다. 지시 이력은 이슈 코멘트 또는 로컬 journal 에 남긴다.
4. 위 1~3 이 판단 비용을 실제로 줄이는지 아래 실험으로 확인한 뒤에야 #98 의 runtime·TUI, #99 의 전달 자동화를 결정한다.

기존 도구 기여는 Orca 가 후보지만, Orca 는 tmux 를 관측하지 않으므로 기여하려면 Orca 터미널로 옮겨야 한다. 그 경우 Orca 의 Run·Dispatch·fencing 이 #99 대부분을 대체하고, 사용자는 GitHub→Run 변환기·충돌 lint·완료 검증 gate 만 만들면 된다. 이것이 두 번째 선택지다.

## 10. 독립 개발의 최소 범위와 사용자층

겹치지 않는 최소 범위는 "이슈 그래프 + 로컬 근거 → ready 집합·충돌 lint·근거 기반 완료 판정" 이다. 터미널·프로세스·원격 연결은 만들지 않는다. 오픈소스 사용자층은 에픽 단위로 CLI 에이전트를 tmux 에서 병렬 운영하는 소수다. 이 조합을 표방하는 성숙한 프로젝트는 검색에서 나오지 않았다. 사용자층은 작지만 겹치는 도구도 없다.

# 발견한 모순과 이전 답변의 오류

- Orca 문서 "Run never schedules" 는 CLI 기준으로만 참. 자동 루프와 `orchestration.run` RPC 가 코드에 남아 있고, 마이그레이션은 기존 run 을 `scheduler_state_lost=1` 로 표시한다.
- Orca 문서는 "Settings → Experimental 활성화" 를 요구하지만 `global-settings-types.ts` 의 experimental 키에 orchestration 이 없다.
- Orca 의 stale-base 가드와 heartbeat 경고는 은퇴한 자동 루프 안에만 있어 권장 경로 `worker-start` 에는 적용되지 않는다.
- Orca DAG README 의 "Orca ≥ 1.4.160 필요" 는 서버가 검사하지 않는다. README 의 재시도 서술은 Orca 의 worker 시작 실패 카운터이지 Task 재투입이 아니다.
- 이전 평가 "Orca 원격 작업과 격리 home 지원" 은 소스로 확인됐다. 단 Remote Server 는 문서에 Beta 표기.
- 이전 평가 "Herdr 는 turn 완료 추적과 timeout 에 제한" 은 문서 원문으로 확인됐다.
- #98 의 도구 비교표는 Orca 를 "시각화 참고" 로만 두었는데, 실제로는 Run·Dispatch·fencing·계정 home 이 #99 설계와 가장 많이 겹친다. 재사용 검토 대상으로 격상하는 것이 맞다.
- #98 은 "deep-research Workflow 도구가 없었다" 고 적었다. 이번 세션에는 있었으나 웹 검색 팬아웃 구조가 소스 검증에 맞지 않아 쓰지 않았다.

# 최소 실험

대상: 서브 이슈 4~6개, 의존성 2~3개, 병렬 가능 쌍 1개 이상인 실제 에픽 하나. 세 팔로 같은 에픽을 돌리지 말고, 서브 이슈를 시간순으로 나눠 팔을 바꾼다.

| 팔 | 구성 |
|---|---|
| A 현행 | Mermaid + tmux + 사람이 순회 |
| B 얇은 계층 | GitHub blocked_by + `next` CLI + tmux + 오케스트레이터 |
| C Orca | Orca 설치, coordinator 에이전트, GitHub→Run 수동 변환 |

측정 항목은 각 서브 이슈마다 기록한다.

| 지표 | 합격 | 불합격 |
|---|---|---|
| 다음 행동 결정에 걸린 시간 | B 가 A 의 절반 이하 | A 와 차이 없음 |
| 터미널을 열어야 상태를 알 수 있었던 횟수 | B 에서 0~1회 | 서브 이슈마다 1회 이상 |
| 잘못된 "완료" 판정 | 0 | 1회 이상 |
| 병렬 실행 중 파일·계약 충돌 | 사전 lint 가 잡음 | 실행 후 발견 |
| 선행 코드 미반영 base 로 시작한 후속 작업 | 0 | 1회 이상 |
| runtime·UI 재시작 후 상태 복원 | 재입력 없이 복원 | 수동 재구성 |
| 사람 판단 요청이 누락된 횟수 | 0 | 1회 이상 |

B 가 합격하면 #98 의 runtime·TUI 범위를 "판단 계층 + 관측" 으로 줄인다. B 가 불합격하고 C 가 합격하면 tmux 를 버리고 Orca 위에 얹는다. 둘 다 불합격이면 문제 정의를 다시 한다.

# 출처

- Orca 소스 `stablyai/orca@615b137`: `src/main/runtime/orchestration/{coordinator.ts,lifecycle-reconciliation.ts,types.ts,db/tasks/task-store.ts}`, `src/cli/specs/orchestration.ts`, `src/shared/agent-session-record.ts`, `src/main/claude-accounts/environment.ts`, `docs/site/content/docs/remote-servers.mdx`
- https://www.onorca.dev/docs/cli/orchestration , /docs/model/agents-sessions , /docs/agents/codex-hot-swap
- `ZinkLu/Orca-Orchestration@0d6c334`: `server/src/{coordinator.ts,orca.ts,index.ts}`, `AGENTS.md`
- https://cmux.com/docs/workspace-groups , `manaflow-ai/cmux` docs/workspace-groups.md, docs/agent-hooks.md
- https://herdr.dev/docs/connecting-machines/ , https://herdr.dev/docs/agent-automation/ , `herdrdev/herdr` v0.9.0
- https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues , https://docs.github.com/en/rest/issues/issue-dependencies , https://github.blog/changelog/2025-08-21-dependencies-on-issues/
- https://learn.chatgpt.com/docs/config-file/environment-variables.md , https://learn.chatgpt.com/docs/auth , `openai/codex` codex-rs/login/src/auth/{storage.rs,manager.rs}
- https://code.claude.com/docs/en/authentication , /docs/en/claude-directory , /docs/en/env-vars
- https://openai.com/policies/row-terms-of-use/ (2026-09-13 아카이브), https://www.anthropic.com/legal/consumer-terms , https://www.anthropic.com/legal/aup
