---
title: fable-advisor 대조 조사 — quality-goal 로 가져올 가치
date: 2026-09-05
kind: research (정적 비교)
dotfiles: b30a0de
upstream: DannyMac180/fable-advisor @ 4d6cc62164619a279b076439e1af5439892b958a
status: 보존 문서. 미커밋 로컬 파일이며 GitHub 에 게시되지 않았다
---

# 보존 메타

- 조사 주체: Codex(gpt-5.6-sol) 서브에이전트 4개 병렬 + 루트 교차검증. 2026-09-05 실행.
- 성격: **정적 비교**다. upstream 에이전트를 설치·호출하지 않았고, 모델 성능·비용·복구 동작·타임아웃·승인 프롬프트를 실행 검증하지 않았다. 원문 § "확인하지 못했거나 재현하지 않은 것" 참조.
- 원본: 세션 scratchpad `research/fable-advisor.md` (삭제하지 않음). 이 파일은 그 사본에 아래 "현재 적용 판단" 절만 앞에 붙였다. 본문의 날짜·커밋·판정은 2026-09-05 시점 그대로다.

# 현재 적용 판단 (2026-09-07 추가, 원문과 구분)

원문의 이슈 연결 제안을 2026-09-07 시점 이슈 상태와 대조한 결과. 원문 판정을 바꾸지 않고 "어디에 붙였는가" 만 적는다.

| 원문 항목 | 원문 판정 | 2026-09-07 처리 |
|---|---|---|
| Plan 태스크별 model/effort provenance | 부분 채택 | **#71 보강** — 이미 provenance 를 다루므로 새 이슈 없음. 누락된 requested/actual effort·status·unknown 처리만 제안. Plan 태스크별 author/implementer 동적 라우팅은 #71 범위로 단정하지 않고 향후 판단으로 표기 |
| exit 0 + empty diff 거절 탐지, 부분 결과 보존 | 부분 채택 | **#49-C 보강** — 실패 모드 분리와 부분 변경 보존을 이미 다룸. refusal/no-op/실제 성공 구분과 staged/untracked 검증 사례만 추가 |
| 모델 퇴역·리네이밍 | (D4) 하드 pin 불필요 | **#39 경계 코멘트** — 무응답은 퇴역이 아님. 실행 감시(#85)와 소관 분리 |
| portable timeout, 실행 감시 | 부분 채택 | **신규 #85** — 독립 소유자가 없어 신설. 관측된 무응답 4건(원인 미확정)과 정적 제안을 구분 |
| 6부 contract, ship/fix-first/rethink 게이트, Fable 하드 의존, --skip-git-repo-check | 불필요 | #72 코멘트에 비채택 결정으로 기록됨(2026-09-05) |
| 사람용 1-line verdict | 부분 채택 | #72 산출물 품질 항목으로만 남김. 신규 이슈 없음 |
| clean-context reviewer, evidence 철학 | 우리가 이미 앞섬 | 조치 없음 |
| 우리 게이트의 남은 약점 6건 (B4) | 보강 필요 | #72 코멘트(2026-09-05)에 표로 기록됨. 개별 이슈는 #55·#59·#51 에 귀속 |
| plugin packaging | 부분 채택(조건부) | **#72 조건부 보류** — 외부·팀 배포 요구 미확인. chezmoi 대체 아님. 신규 이슈 없음 |
| readiness checklist gate 전제 | (원문 작성 시점 전제) | 2026-09-06 사용자 결정으로 #70 은 참고용 readiness 만 유지, 게이트·자동 전이는 #76. #72·#76 코멘트 참조 |

---

# 원문 (2026-09-05, 무수정)

# fable-advisor에서 quality-goal로 가져올 가치 조사

- 조사일: 2026-09-05 (Asia/Seoul)
- upstream 고정점: `DannyMac180/fable-advisor@4d6cc62164619a279b076439e1af5439892b958a`
- 로컬 고정점: `lee-kyu-hwan/dotfiles@b30a0dee8465b9b8a3cf5243a47740b3c2116a24`
- 결론 성격: 소스·문서·CLI 계약의 정적 비교. upstream 모델 실행 성능 평가는 아님

## 결론

**전체 이식 가치는 낮고, 선택적 이식 가치는 있다.** fable-advisor의 핵심은 상태 기계가 아니라 짧은 역할 규율이다. 우리 `quality-goal`은 이미 더 풍부한 Spec/Plan, 구조화 finding/evidence, 점수와 hard finding 게이트, 승인·리뷰 digest 결합, fresh reviewer, bounded rounds를 갖는다. upstream의 6부 계약이나 `ship / fix-first / rethink`를 기존 계약 대신 쓰면 품질 보장이 약해진다.

가져올 가치가 큰 순서는 다음과 같다.

1. **부분 채택 — 태스크별 실행 provenance:** Plan 태스크마다 선택 model/effort, 선택 근거, 실제 실행 model/effort, attempt/status를 기록한다. 다만 동적 override는 현재 #70의 역할별 고정 정책을 바꾸므로 #72 아래 후속 이슈로 분리한다.
2. **부분 채택 — 실행 복구:** portable wall-clock timeout, exit 0이지만 실제 변경이 없는 거절 탐지, Sol의 `JUDGMENT CALLS` 보고를 #70 controller에 보강한다. upstream 구현 그대로가 아니라 baseline·staged·untracked·partial result까지 포함해야 한다.
3. **부분 채택 — 사람용 최종 verdict:** 기계 게이트는 그대로 유지하고 최종 사용자 요약에 `ship` / `fix-first` / `rethink`에 해당하는 짧은 결론을 추가할 수 있다.
4. **부분 채택 — 플러그인 패키징:** 팀/외부 배포가 목적일 때만 self-contained Claude plugin을 만든다. 개인용 반복 개발에는 현재 chezmoi standalone 배포가 공식 권장 용도와 더 잘 맞는다.
5. **채택하지 않음:** `--skip-git-repo-check`, 누락 effort를 사용자 기본값에 맡기는 방식, 느슨한 prose verdict로 현재 gate를 대체하는 방식, 글로벌 instruction을 prompt preamble으로 면제하는 방식.

가장 먼저 할 일은 upstream 이식이 아니라 **#61의 개정 후 교차 회귀 점검**이다. #42·#70·#72의 최신 실측은 모델 effort보다 문서 규모, 시간축 상태 전개, 수정 간 상호작용이 현재 실패 원인임을 가리킨다.

## 조사 방법과 커버리지

요청대로 `collab/spawn`을 사용했다. 동시 슬롯 네 개를 다음처럼 배정했다.

| 조사자 | 축 | 범위 |
|---|---|---|
| `/root/axis_a_spec_contract` | A | 6부 contract, 우리 Spec/Plan, task effort |
| `/root/axis_b_review_verdict` | B | verdict, evidence, context-clean reviewer |
| `/root/axis_c_codex_routing` | C | Luna/Sol, `codex exec`, #70 여섯 함정 |
| `/root` | D + 통합 | plugin packaging, Fable 포지셔닝, 전체 교차검증 |

세 서브에이전트는 서로 독립적으로 원문을 읽고 결과만 반환했다. 루트가 clone과 로컬 파일, 이슈, 공식 웹 문서를 다시 읽어 핵심 인용과 판정을 교차검증했다. 전용 `deep-research` Workflow 호출기는 이 세션 도구에 없어, 동일한 원문 우선·미확인 표시 원칙으로 직접 조사했다.

### 읽은 upstream 전체 트리

현재 commit의 recursive tree는 다음뿐이다.

- `.claude-plugin/marketplace.json`
- `.claude-plugin/plugin.json`
- `.gitignore`
- `LICENSE`
- `README.md`
- `agents/fable-advisor.md`
- `agents/codex-implementer.md`
- `agents/sol-implementer.md`
- `skills/orchestration/SKILL.md`
- `assets/fable-advisor-demo-poster.png`
- `assets/fable-advisor-demo.mp4`

모든 텍스트 파일을 원문으로 읽었다. 두 asset은 바이너리이므로 내용 계약 분석에는 사용하지 않았고 파일 형식만 확인했다(PNG 1600×1222, MP4 ISO Base Media). [`raw README`](https://raw.githubusercontent.com/DannyMac180/fable-advisor/main/README.md)도 별도로 열어 clone의 README와 대조했다. LICENSE는 MIT다.

### 읽은 로컬 범위

- `dot_claude/skills/quality-goal/SKILL.md` 전체
- `dot_claude/skills/quality-goal/references/`의 7개 파일 전체
- `dot_claude/skills/quality-goal/scripts/quality_state.py` 전체를 서브에이전트 두 명이 독립 열람; 루트는 상태 전이·review·approval·digest·fingerprint 구간을 재확인
- `dot_claude/skills/quality-goal/scripts/validate_review.py`의 schema/gate 구간
- `dot_claude/skills/quality-goal/templates/{spec,plan,report}.md`
- `dot_claude/skills/quality-goal/schemas/{review,codex-result}.schema.json`
- `dot_claude/agents/quality-reviewer.md` 전체
- `.chezmoiignore`, `run_once_install-claude-plugins.sh.tmpl`, `CLAUDE.md`, `install.sh`, `setup.sh`의 배포 관련 부분

GitHub 이슈 #70, #61, #42, #72는 요청한 `gh issue view <n> --comments`로 읽었다. 해당 출력이 본문을 생략하는 환경이라 `gh issue view --json title,body,labels,comments,url`로 본문도 보완했다. 댓글 수는 각각 2, 0, 2, 1이다.

---

## A. Spec/contract 형식

### A1. 그들의 “6부 spec”은 문서 템플릿이 아니라 매 위임 prompt의 최소 envelope다

**그들의 원문·위치.** 실제 여섯 이름은 다음과 같다.

> `Objective / Files / Interfaces / Constraints / Verification / Reasoning`

마지막 필드의 유일한 고정 표기는 `REASONING: <effort>`다. [upstream `skills/orchestration/SKILL.md:52-63`](https://github.com/DannyMac180/fable-advisor/blob/4d6cc62164619a279b076439e1af5439892b958a/skills/orchestration/SKILL.md#L52-L63)

`agents/codex-implementer.md:34-36`와 `agents/sol-implementer.md:34-36`도 동일한 여섯 항목을 수신 계약으로 반복한다. 누락 항목은 Codex에게 open question으로 넘기고 최종 `GAPS`에 적으라고 한다. 반면 orchestration 문서는 완성하지 못한 spec은 architect가 아직 결정을 못 한 신호라고 한다. **누락을 handoff해도 되는지에 대해 upstream 내부 문구가 긴장 관계에 있다.**

별도 Markdown spec template, JSON schema, validator, controller, contract test는 upstream에 없다. 따라서 “6부”는 기계적으로 강제되는 여섯 section이 아니라 prose 규칙이다.

**우리 대응 위치.** 우리 쪽 대응물은 한 파일이 아니라 승인된 Spec + Plan + 구현 prompt다.

| 6부 항목 | 우리 대응 위치 | 비교 |
|---|---|---|
| Objective | `templates/spec.md:16-38` Goals/Requirements/AC, `SKILL.md:213-218` bounded task | 목표를 객관적 AC까지 확장 |
| Files | `templates/plan.md:22-32` file map/dependencies, `planning-policy.md:6-7,13` | 경로뿐 아니라 책임·의존성·허용 범위 포함 |
| Interfaces | `templates/spec.md:46-50`, `templates/plan.md:22-32` | producer/consumer와 data flow까지 포함 |
| Constraints | `templates/spec.md:22-26`, `templates/plan.md:16-20`, `SKILL.md:213-218` | non-goal, repo 규약, dirty exclusions 포함 |
| Verification | `templates/plan.md:34-60`, `planning-policy.md:5-15`, `SKILL.md:338-361` | 태스크·AC·명령·expected result·workspace fingerprint까지 추적 |
| Reasoning | `references/model-routing.md:5-13,20-29` | 실행 effort는 있으나 태스크별 선택·근거·실행 이력은 없음 |

Spec 자체는 문제/맥락, goal/non-goal, requirement, AC, architecture, interface/data flow, failure, security/risk, test strategy, decisions와 strict-only 위험 절을 갖는다. Plan은 Spec digest, global constraints, file map, dependency, test-first tasks, exact commands, rollback, AC traceability를 갖는다.

**가져올 가치 판정: `불필요` — 6부 contract로 Spec/Plan을 교체하지 않는다.** 앞의 다섯 요소는 이미 더 강한 형태로 존재한다. 교체하면 요구사항·위험·추적성·승인 digest 정보가 줄어든다.

**연결 이슈:** #70의 author prompt가 기존 Spec/Plan 정보를 손실 없이 envelope로 펼치는지 확인하는 AC만 추가한다. 별도 형식 교체는 #72에 비채택 결정으로 기록한다.

### A2. 태스크별 REASONING은 필드보다 provenance가 핵심이다

**그들의 원문·위치.** effort 원칙의 핵심 문구는 다음이다.

> “Pick the lowest rung that is adequate”

[upstream `skills/orchestration/SKILL.md:36-50`](https://github.com/DannyMac180/fable-advisor/blob/4d6cc62164619a279b076439e1af5439892b958a/skills/orchestration/SKILL.md#L36-L50)

upstream 선언을 사실 표로 옮기면 다음과 같다. 이는 upstream의 계약이며 실제 계정의 모델 지원 범위를 이번 조사에서 실행 검증한 것은 아니다.

| Effort | Luna | Sol | upstream 사용 기준 |
|---|---:|---:|---|
| low/medium | 지원 선언 | 지원 선언 | rename, wiring, boilerplate, config, 기존 패턴을 따르는 test |
| high | 지원 선언 | 지원 선언 | 보통 feature, 남은 설계 판단이 소수인 로직 |
| xhigh | 지원 선언 | 지원 선언 | 상호작용 있는 multi-file 변경, spec 보정 뒤 두 번째 시도 |
| max | 지원 선언 | 지원 선언 | concurrency, security-sensitive, 어려운 debugging |
| ultra | 미지원 선언 | 지원 선언 | 내부 delegation을 동반하는 가장 넓고 어려운 작업 |

Luna의 `ultra`처럼 미지원 rung은 반올림하지 않고 `STATUS: unavailable`로 실패한다. effort가 누락되면 flag를 생략하고 사용자 Codex 기본값을 쓰며 `GAPS`에 남긴다.

**에이전트 frontmatter 원문.** 세 파일 모두 `effort:` 필드가 없다.

```yaml
# agents/fable-advisor.md:4-5
model: fable
tools: Read, Grep, Glob
```

```yaml
# agents/codex-implementer.md:4-5
model: sonnet
tools: Bash, Read, Grep, Glob
```

```yaml
# agents/sol-implementer.md:4-5
model: sonnet
tools: Bash, Read, Grep, Glob
```

[advisor](https://github.com/DannyMac180/fable-advisor/blob/4d6cc62164619a279b076439e1af5439892b958a/agents/fable-advisor.md#L1-L6), [Luna wrapper](https://github.com/DannyMac180/fable-advisor/blob/4d6cc62164619a279b076439e1af5439892b958a/agents/codex-implementer.md#L1-L6), [Sol wrapper](https://github.com/DannyMac180/fable-advisor/blob/4d6cc62164619a279b076439e1af5439892b958a/agents/sol-implementer.md#L1-L6)

중요한 구분: `model: sonnet`은 Bash로 Codex를 감독하는 **Claude wrapper subagent**의 모델이다. 실제 코드 생성 모델은 그 wrapper가 CLI의 `--model`로 Luna/Sol을 고른다. advisor는 session effort를 상속하고, 구현 모델 effort는 spec의 `REASONING`에서 온다.

**우리 대응 위치.** 현재 `references/model-routing.md:5-13`은 goal mode/stage 단위 고정이다.

- light + standard: Terra/high
- strict: Sol/high
- bounded redesign: Sol/xhigh
- reviewer: Opus/high
- orchestrator: inherit/high

`quality_state.py:179-218`의 state v1에는 goal 단위 `task_id`, mode, artifacts, rounds, reviews, approval, verification은 있지만 Plan의 세부 T1/T2별 route·effort·attempt는 없다.

**가져올 가치 판정: `부분 채택`.** Plan 태스크에 아래 provenance를 기록하는 것은 유용하다.

- logical task ID
- selected lane/model/effort
- 선택 근거와 위험 하한
- actual model/effort와 attempt
- timeout/refused/unavailable/complete 상태

하지만 처음부터 자유 override를 허용하지 않는다. 1단계는 현행 mode별 고정 route를 태스크에 명시하고 실제 invocation과 대조하는 관측 기능이어야 한다. 데이터가 쌓인 뒤에만 동적 routing을 검토한다. 누락 effort를 사용자 기본값에 맡기는 upstream 정책은 재현성을 해치므로 채택하지 않는다.

**연결 이슈:** #70에는 확장 가능한 invocation/result 필드와 unsupported-effort fail-closed만 넣고, 실제 task-specific policy는 #72 아래 새 하위 이슈로 분리한다. #61과 #70의 안정화보다 뒤에 둔다.

### A3. Luna/Sol lane 기준은 아이디어만 가져오고 문구 충돌은 가져오지 않는다

**그들의 원문·위치.** orchestration의 표는 routine work를 Luna 기본 lane, subtle concurrency·security·hard debugging·wide refactor를 Sol로 보낸다. 그런데 `skills/orchestration/SKILL.md:27`은 routine lane 실패 1회를 escalation 조건으로 쓰고, 같은 파일 `:30`은 보정 spec까지 두 번 실패해야 Sol로 올린다고 쓴다. `agents/sol-implementer.md:3`도 이미 한 번 실패한 작업을 Sol 후보로 적는다.

**우리 대응 위치.** `routing-rules.md:13-23`은 위험을 크기보다 먼저 검사하고 auth, money, PII, migration, public API, concurrency, production blast radius를 strict로 보낸다. 이 방식은 “spec이 담지 못하는 판단량”이라는 upstream 휴리스틱보다 재현성이 높다.

**가져올 가치 판정: `부분 채택`.** “spec이 결과를 얼마나 결정하는가”를 기존 위험 분류의 보조 신호로 쓸 수 있지만, strict 하한이나 공식 round budget을 낮춰서는 안 된다. 1회/2회 충돌을 그대로 복제하지 않는다.

**연결 이슈:** #72의 capability routing 후속. #70의 현재 역할별 고정 정책에는 섞지 않는다.

---

## B. 리뷰·판정·evidence·context-clean

### B1. ship / fix-first / rethink는 좋은 요약 언어지만 gate가 아니다

**그들의 원문·위치.** 최종 verdict 이름은 다음 세 개다.

> `ship / fix-first / rethink`

[upstream `skills/orchestration/SKILL.md:69-79`](https://github.com/DannyMac180/fable-advisor/blob/4d6cc62164619a279b076439e1af5439892b958a/skills/orchestration/SKILL.md#L69-L79)

advisor의 출력 규칙은 다음 정도로 구체화된다.

> “Ship” gets one line; problems get named precisely with the file and the fix.

[upstream `agents/fable-advisor.md:23-33`](https://github.com/DannyMac180/fable-advisor/blob/4d6cc62164619a279b076439e1af5439892b958a/agents/fable-advisor.md#L23-L33)

advisor는 goal 대비 diff를 읽고 요청 누락, 비요청 scope, verification의 실재성, 새 위험을 보라고 한다. 하지만 다음은 정의하지 않는다.

- `fix-first`와 `rethink`의 경계
- severity와 blocker schema
- 점수 또는 required checks
- verdict별 허용 finding 수
- 최종 리뷰 round limit
- verdict를 상태 전이에 결합하는 실행 코드

따라서 “ship 기준 원문”은 위 prose가 전부이며, 별도 formal 판정표는 **원문에 없다**. `rethink`는 접근 자체 재검토로 해석할 수 있지만 이는 문서 의미 해석이지 기계 계약이 아니다.

**우리 대응 위치.** 우리 reviewer verdict는 `PASS / REVISE / BLOCKED`이고 `NEEDS_REDESIGN`은 state다.

- Spec: `spec-rubric.md:14-33`, score ≥85, Critical/High 0, required sections, 결정 해소, 객관적 AC
- Plan: `plan-rubric.md:14-33`, score ≥85, Critical/High 0, required sections, traceability, placeholder 0
- Code: `code-rubric.md:3-30`, score는 advisory이며 명령·AC·scope·docs hard conditions로 통과
- deterministic evaluator: `validate_review.py:9-35,362-404`
- limits: `quality_state.py:20-69`의 Spec 3 / Plan 2 / Code 3
- 동일 blocking ID 재등장 또는 마지막 round 실패: `quality_state.py:646-678` → `NEEDS_REDESIGN`

**가져올 가치 판정: `부분 채택`.** machine verdict와 state는 유지한다. 사용자용 Report 맨 앞에 한 줄짜리 `Ship`, 구체 수정 목록을 동반한 `Fix first`, 설계 재검토 사유를 동반한 `Rethink`를 **표시용 summary**로 매핑할 수 있다. 이것이 state나 gate의 authority가 되어서는 안 된다.

**연결 이슈:** #72의 산출물 품질 계약 후속. #70의 readiness/formal gate를 대체하지 않는다.

### B2. evidence 철학은 같지만 우리 구조가 더 강하다

**그들의 원문·위치.** orchestration이 내세우는 핵심은 다음이다.

> “Reports are claims, not evidence.”

[upstream `skills/orchestration/SKILL.md:91-93`](https://github.com/DannyMac180/fable-advisor/blob/4d6cc62164619a279b076439e1af5439892b958a/skills/orchestration/SKILL.md#L91-L93)

두 implementer는 실제 diff/status를 읽고 spec의 verification command를 wrapper가 다시 실행하고 Codex final message와 대조하게 한다. 반환은 `STATUS`, `CHANGES`, `VERIFIED`, `CODEX SAID`, `GAPS`를 담은 평문 `CODEX REPORT`; Sol은 판단 결정을 한 줄 더 요구한다. exit 0이어도 실제 diff가 비면 `refused`로 보고한다. 다만 schema/validator/controller가 아니라 지침이다.

orchestration 상위 규칙은 재실행뿐 아니라 quoted output을 working tree와 spot-check하는 것도 허용한다. advisor tools는 `Read, Grep, Glob`뿐이므로 advisor 자신은 verification 명령을 실행하지 못한다.

**우리 대응 위치.** `review.schema.json`과 `quality-reviewer.md:34-62`는 다음을 강제한다.

- stable namespaced finding ID
- severity, description, evidence location, rubric item, required resolution
- round 2+ 신규 blocker의 `new_blocker_evidence`
- evidence의 `claim`, `location`, `verified`
- applicable condition이 미검증이면 PASS 금지
- deterministic failure는 reviewer가 면제 불가

Codex result도 `codex-result.schema.json`으로 status, changed files, command/exit/result, Plan deviations, concerns를 구조화한다. `SKILL.md:338-361`은 Codex 보고와 실제 git 변화를 대조하고 검증 뒤 workspace fingerprint를 저장한다.

**가져올 가치 판정: `우리가 이미 앞섬`.** evidence 철학을 새로 이식할 필요는 없다. 다만 Sol의 `JUDGMENT CALLS`는 현재 `plan_deviations`와 다르므로 부분 채택 가치가 있다. Plan을 벗어난 일탈뿐 아니라 Plan이 열어 둔 판단과 선택 근거를 보고하기 때문이다.

**연결 이슈:** `JUDGMENT CALLS`는 #70 result schema 후보. evidence 무결성 보강은 #72의 #55/#59 계열에 둔다.

### B3. context-clean reviewer는 우리 쪽이 더 명시적이다

**그들의 원문·위치.** advisor는 같은 Fable 모델을 쓰되 별도 subagent 문맥에서 goal/diff를 새로 읽는 것을 가치로 설명한다. 표현은 다음처럼 짧다.

> “what you add is a clean context”

[upstream `agents/fable-advisor.md:8-12`](https://github.com/DannyMac180/fable-advisor/blob/4d6cc62164619a279b076439e1af5439892b958a/agents/fable-advisor.md#L8-L12)

commitment boundary와 최종 deliverable에서 호출하며 read-only다. 그러나 invocation ID, resume 금지, prior finding 전달 schema, context whitelist는 없다. optional Codex adversarial review를 먼저 하고 그 findings를 Fable advisor에 넣는 경로는 **독립 이중 1차 review가 아니라 순차 review**다.

**우리 대응 위치.** `SKILL.md:264-311`과 `quality-reviewer.md:10-32,50-68`은 다음을 명시한다.

- 매 round NEW unnamed one-shot invocation
- 이전 reviewer resume/continue 금지
- artifact/rubric/evidence/prior findings만 전달
- hidden reasoning과 무관 conversation 제외
- later round에 open finding 전문, resolution claim/evidence, resolved IDs 전달
- 회귀 탐색과 stable IDs 유지
- 미검증 reviewer는 같은 round에서 1회 free retry 후 capability failure로 분리

**가져올 가치 판정: `우리가 이미 앞섬`.** 같은 모델의 fresh eyes가 독립 lineage와 같지 않다는 upstream의 정직한 caveat만 문서 설명에 참고할 수 있다. #42의 독립 dual review 설계를 upstream의 순차 review로 약화시키면 안 된다.

**연결 이슈:** #42는 현재 독립 1차 review 계약 유지. #70의 author/readiness도 서로 ephemeral context라는 기존 제안을 유지한다.

### B4. 우리 gate의 남은 약점도 과장 없이 기록해야 한다

정적 비교에서 우리 쪽이 앞서지만 “모든 gate가 state machine 자체에서 강제된다”는 주장은 사실보다 강하다.

| 남은 경계 | 근거 | 연결 |
|---|---|---|
| `record_review()`는 schema validator만 호출하고 score/hard checks의 `evaluate_gate()`는 별도 CLI | `quality_state.py:623-633`, `validate_review.py:362-404` | #70 controller 통합 또는 #72 |
| review evidence 배열에 `minItems`가 없음 | `review.schema.json:46-66` | #70 readiness schema 설계, #72 evidence 계약 |
| `record_verification()`은 파일 존재와 fingerprint 형식만 보고 `valid=True` 저장 | `quality_state.py:1006-1041` | #72 evidence 무결성 |
| COMPLETED guard는 저장된 review/verification digest를 비교하지만 현재 fingerprint를 즉시 재계산하지 않음 | `quality_state.py:424-461` | #72의 #55 |
| fresh invocation 여부는 state에 provenance로 기록되지 않음 | `quality_state.py:654-660` | #70/#59 계열 |
| review target digest 대조는 결과 기록 시점이며 reviewer 호출 전 provenance 보장은 아님 | `quality_state.py:599-605` | #70 함정 5, #72의 #59 |

**가져올 가치 판정: `upstream보다 앞서지만 보강 필요`.** upstream은 이 약점을 해결하지 않는다. 위 간극은 우리 이슈 체계로 닫아야 한다.

---

## C. Codex 호출·라우팅·승인

### C1. 실제 `codex exec` 명령

**Luna 원문 명령.** [upstream `agents/codex-implementer.md:73-88`](https://github.com/DannyMac180/fable-advisor/blob/4d6cc62164619a279b076439e1af5439892b958a/agents/codex-implementer.md#L73-L88)

```bash
${T:+$T 600} codex exec --model gpt-5.6-luna ${EFFORT:+-c model_reasoning_effort=$EFFORT} --sandbox workspace-write --skip-git-repo-check --cd "$(pwd)" --output-last-message "$FINAL" - < "$SPEC"
```

**Sol 원문 명령.** [upstream `agents/sol-implementer.md:73-88`](https://github.com/DannyMac180/fable-advisor/blob/4d6cc62164619a279b076439e1af5439892b958a/agents/sol-implementer.md#L73-L88)

```bash
${T:+$T 1800} codex exec --model gpt-5.6-sol ${EFFORT:+-c model_reasoning_effort=$EFFORT} --sandbox workspace-write --skip-git-repo-check --cd "$(pwd)" --output-last-message "$FINAL" - < "$SPEC"
```

`T`는 `gtimeout`, 그다음 `timeout`을 찾는다. 둘 다 없으면 경고하고 무제한 실행한다. prompt와 final은 각각 unique `mktemp -t codex-spec.XXXXXX`, `mktemp -t codex-final.XXXXXX`를 쓴다. Luna는 600초, Sol은 1800초다.

두 prompt에는 글로벌 `AGENTS.md`의 기본 orchestration/model rule에서 이 lane만 opt-out한다고 주장하는 preamble이 있다. 이유는 exit 0 + polite refusal + empty diff 관측이라고 문서에 적혀 있다. 이는 실제 권한 검증 장치가 아니라 prompt 문구다.

**승인·sandbox의 정확한 상태.** 두 명령은 `workspace-write`를 명시하고 `danger-full-access`를 쓰지 않는다. 하지만 `--approve-for-me`, `-a/--ask-for-approval`, `approval_policy` override가 없다. 따라서 **effective approval policy는 upstream 원문만으로 확정할 수 없고 사용자 Codex config를 상속한다.**

로컬 `codex-cli 0.153.4` help도 확인했다.

- `codex exec`에는 `-a/--ask-for-approval`가 없다.
- `codex exec`에는 `--approve-for-me`는 있다.
- root `codex`에는 `-a`가 있고 값은 `on-request`, `never`다.
- root와 exec 모두 `--full-auto`는 없다.

모델 호출 자체는 실행하지 않았으므로 approval prompt, timeout, model availability를 재현한 것은 아니다.

**우리 대응 위치.** `references/model-routing.md:19-30`의 구현 명령은 다음 특성을 더 갖는다.

- `-C "$PROJECT_ROOT"`
- `--ephemeral`
- exact model + quoted effort
- `--output-schema`
- `--output-last-message`
- `--json`
- prompt stdin 파일 + events/stdout + stderr 분리
- `--skip-git-repo-check`, `--full-auto`, `--yolo`, sandbox bypass 금지

반면 wall-clock timeout과 explicit effective approval override는 없다.

**가져올 가치 판정.** unique prompt/result는 `우리가 이미 앞섬`; timeout과 refusal detection은 `부분 채택`; `--skip-git-repo-check`와 opt-out preamble은 `불필요`다.

**연결 이슈:** #70 controller와 #72의 실패 모드 하위 작업. timeout은 바이너리 유무에 따라 무제한이 되지 않게 Python subprocess timeout으로 구현하는 편이 낫다.

### C2. #70 코멘트의 여섯 함정 대조

출처: [#70 첫 실측 댓글](https://github.com/lee-kyu-hwan/dotfiles/issues/70#issuecomment-5541789407)의 1-3번, [#70 후속 댓글](https://github.com/lee-kyu-hwan/dotfiles/issues/70#issuecomment-5550312202)의 4-6번.

| # | 실측 함정 | fable-advisor | 우리 현재 상태 | 판정·이슈 |
|---:|---|---|---|---|
| 1 | `--output-schema`에서 `const`만 둔 property가 type 누락 400; `type`+단일 `enum` 필요 | schema를 안 써서 이 오류 경로에는 안 들어가지만 문제를 해결한 것도 아님 | 현 schema는 type+enum 형태 | upstream `판단 불가`; #70 author/readiness schema에 회귀 fixture |
| 2 | noninteractive stdin이 열려 있으면 추가 입력 대기 | `- < "$SPEC"` 파일 EOF로 회피 | implementation도 파일 EOF. preflight의 positional prompt에는 explicit stdin closure 없음 | implementation `이미 회피`; preflight `채택 보완`, #70 |
| 3 | `codex exec`에는 `-a`가 없고 당시 `--full-auto`도 사라짐 | 둘 다 쓰지 않음. 다만 approval을 명시하지도 않음 | 둘 다 금지/미사용. current exec에는 `--approve-for-me` 존재 | 함정은 `피함`; effective approval 계약은 #70에서 명시 |
| 4 | readiness 최대 2회는 formal round당 값인데 schema maximum으로 전체 누적 제한하면 충돌 | readiness/attempt/state 자체가 없음 | v4.1.0에도 readiness 미구현 | `판단 불가`; #70 state 설계에서 formal round key와 attempt key 결합 |
| 5 | reviewer 호출 전에 target과 state artifact digest를 대조해야 옛 Spec 심사를 막음 | digest/state 없음: 노출 | 결과 기록 때 파일 digest를 대조하지만 호출 전 provenance와는 다름 | 둘 다 완전 해결 아님; #70 + #72/#59 |
| 6 | readiness score를 실제 rubric으로 계산하고 evidence 최소 수를 계약해야 함 | readiness schema 없음 | 공식 review는 score/evidence field가 있지만 evidence `minItems` 없음; readiness 미구현 | `판단 불가`; #70 checklist + schema 최소 evidence |

함정 1은 “JSON Schema가 항상 `const`를 거부한다”는 일반 명제가 아니다. 이슈의 실측은 `const`만 있고 `type`이 없는 해당 schema가 거부됐다는 범위로 기록해야 한다.

### C3. empty-diff, timeout, 판단 결정 보고

**그들의 원문·위치.** 두 implementer는 exit 0이어도 diff가 비면 completion으로 보지 않고 final message를 원인으로 보존한다. Sol은 `JUDGMENT CALLS`를 추가한다. [Luna `:117-124`](https://github.com/DannyMac180/fable-advisor/blob/4d6cc62164619a279b076439e1af5439892b958a/agents/codex-implementer.md#L117-L124), [Sol `:117-125`](https://github.com/DannyMac180/fable-advisor/blob/4d6cc62164619a279b076439e1af5439892b958a/agents/sol-implementer.md#L117-L125)

**우리 대응 위치.** `SKILL.md:330-346`은 result schema 검증과 실제 git/changed_files 대조를 요구하고 `quality_state.py:923-1003`은 baseline과 tracked/staged/untracked fingerprint를 만든다. 그러나 Codex의 “아무 변경도 필요 없는 이미 충족된 task”와 “instruction refusal”을 final message/objective evidence로 분류하는 명시 schema는 없다.

**가져올 가치 판정: `부분 채택`.** 다음처럼 강화해 채택한다.

- timeout은 controller가 직접 강제하고 timeout/partial output/partial diff를 보존
- empty `git diff` 하나만 보지 않고 staged, untracked, baseline, 이미 충족된 objective를 함께 판정
- refusal과 no-op-success를 별도 status로 분리
- actual final message와 실제 diff의 불일치 기록
- high-complexity lane의 judgment calls를 result schema에 추가

**연결 이슈:** #70, #72의 실패 모드 보강.

---

## D. 패키징과 Fable 전제

### D1. fable-advisor는 저장소 하나가 marketplace이자 plugin이다

**그들의 원문·위치.** plugin identity는 다음 두 값으로 고정된다.

```json
{"name": "fable-advisor", "version": "5.0.0"}
```

[upstream `.claude-plugin/plugin.json:1-23`](https://github.com/DannyMac180/fable-advisor/blob/4d6cc62164619a279b076439e1af5439892b958a/.claude-plugin/plugin.json#L1-L23)

marketplace entry는 같은 저장소 root를 source로 쓴다.

```json
{"name": "fable-advisor", "source": "./"}
```

[upstream `.claude-plugin/marketplace.json:1-17`](https://github.com/DannyMac180/fable-advisor/blob/4d6cc62164619a279b076439e1af5439892b958a/.claude-plugin/marketplace.json#L1-L17)

root의 `agents/`와 `skills/`는 auto-discovery된다. 설치는 raw README의 다음 두 단계다.

```text
claude plugin marketplace add DannyMac180/fable-advisor
claude plugin install fable-advisor@fable-advisor
```

Claude Code `2.1.261`에서 clone root에 `claude plugin validate`를 실행한 결과 `Validation passed`, exit 0이었다.

공식 문서와의 대조:

- standalone `.claude/`는 personal/project quick iteration, plugin은 team/community 공유·versioned release·재사용에 맞다. [Claude Code plugin guide](https://code.claude.com/docs/en/plugins)
- `skills/`와 `agents/`는 `.claude-plugin/` 안이 아니라 plugin root에 있어야 한다. 같은 문서의 structure 절.
- plugin skill은 `/plugin-name:skill-name`으로 namespace된다. 같은 문서의 quickstart 절.
- plugin agent도 scoped name으로 load된다. [Plugins reference](https://code.claude.com/docs/en/plugins-reference)
- marketplace의 `source: "./"` 계열 상대 경로는 Git source로 marketplace를 추가할 때는 동작하지만 raw `marketplace.json` URL만 추가하면 동작하지 않는다. [Marketplace docs](https://code.claude.com/docs/en/plugin-marketplaces)
- marketplace plugin은 local cache에 복사되며, 패키지 component/resource 경로는 plugin root 밖을 가리킬 수 없다. 런타임에 사용자의 project evidence를 읽는 권한과는 별개다. [Plugins reference — path behavior](https://code.claude.com/docs/en/plugins-reference)
- manifest에 version을 명시하면 그 값이 update cache key라서 파일만 바꾸고 version을 올리지 않으면 update가 건너뛰어진다. 같은 reference의 version management 절.

`plugin.json`은 default component auto-discovery만 쓸 때 공식 문서상 생략 가능하지만, 공개 identity·namespace·version을 명확히 관리하려면 두는 편이 적절하다. 아래 구조는 기술적 절대 최소가 아니라 **quality-goal 배포에 권장하는 최소**다.

### D2. chezmoi와 plugin의 차이

| 항목 | 현재 chezmoi standalone | Claude plugin |
|---|---|---|
| 소스 배치 | `dot_claude/skills/...` → `~/.claude/skills/...`; agent도 전역 위치 | self-contained plugin cache의 `skills/`, `agents/` |
| 호출명 | `/quality-goal` | `/plugin-name:quality-goal` |
| 대상 | 개인 환경·빠른 반복 | 공유·배포·버전 릴리스 |
| 업데이트 | `chezmoi apply`, source와 home 파일 동기화 | marketplace/plugin update + version/cache semantics |
| 경로 | home의 다른 전역 파일을 상대 참조할 수 있음 | 패키지 component/resource는 plugin root 안에 self-contained |
| 설치 의존 | dotfiles bootstrap과 apply | marketplace registration/install 또는 `--plugin-dir` |
| 버전 | `SKILL.md`의 `version: 4.1.0` | manifest version 또는 source SHA; 두 군데 version을 두면 drift 위험 |
| 설정 | `.claude/settings.json`은 민감 정보 때문에 chezmoi 제외 | plugin root `settings.json`은 제한된 default만 가능 |

현재 `run_once_install-claude-plugins.sh.tmpl:1-7`은 macOS에서 superpowers marketplace/plugin만 한 번 설치한다. quality-goal은 marketplace가 아니라 chezmoi가 직접 배치한다. `.chezmoiignore:20-26`은 민감한 환경 정보 때문에 `.claude/settings.json`을 의도적으로 관리하지 않는다.

### D3. quality-goal을 plugin으로 만들 때 필요한 것

기능을 바꾸지 않는 최소 구조는 다음이다.

```text
quality-goal-plugin/
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json       # 같은 repo를 marketplace로 배포할 때
├── skills/
│   └── quality-goal/
│       ├── SKILL.md
│       ├── references/
│       ├── templates/
│       ├── schemas/
│       ├── scripts/
│       ├── tests/
│       └── evals/
├── agents/
│   └── quality-reviewer.md
├── README.md
└── LICENSE
```

필수 검토점:

1. `${CLAUDE_SKILL_DIR}` 기반 references/templates/scripts 경로는 plugin 안에 함께 복사하면 유지된다.
2. `${CLAUDE_SKILL_DIR}/../../agents/quality-reviewer.md`도 위 구조에서는 plugin root의 agent를 가리켜 cache boundary 안에 남는다.
3. 실제 agent 호출명은 scoped name이 되므로 fresh one-shot invocation 계약을 `plugin-name:quality-reviewer`로 검증해야 한다.
4. `/quality-goal`이 `/plugin-name:quality-goal`로 바뀌는 사용자·eval·문서 영향을 반영해야 한다.
5. 외부 실행 의존인 `python3`, `git`, `gh`, `codex`는 plugin이 자동 제공하지 않는다. README와 preflight에 유지해야 한다.
6. manifest version과 `SKILL.md` version을 둘 다 유지하면 contract test로 동일성을 강제하거나, manifest version을 생략하고 Git SHA 기반 update를 선택해야 한다.
7. `claude --plugin-dir <dir>`, `claude plugin validate <dir>`, fresh install/update, 이름 scope, relative path, resume state, Codex preflight를 별도 fixture에서 검증해야 한다.
8. 현재 민감한 `.claude/settings.json`을 plugin에 복사하면 안 된다. quality-goal에 필요한 component만 self-contained하게 묶는다.

**가져올 가치 판정: `부분 채택`.** 공개/팀 배포가 실제 목표가 될 때는 가치가 크다. 지금 개인 dotfiles에서 반복 수정 중인 단계에는 chezmoi가 더 단순하며, #61/#70/#55/#59 안정화보다 packaging을 먼저 할 이유가 없다.

**연결 이슈:** #72 아래 새 “quality-goal plugin packaging/distribution” 하위 이슈. #70 구현 범위에는 넣지 않는다.

### D4. Fable 5.1을 전제하는 이유는 포지셔닝·경제성이지 기술 의존성이 아니다

**README 원문.** raw README의 한 줄 포지셔닝은 다음과 같다.

> “Fable 5.1 runs the show. Codex does the typing at the effort each task deserves, and Fable reviews before anything ships.”

[`raw README`](https://raw.githubusercontent.com/DannyMac180/fable-advisor/main/README.md)

**Anthropic 공식 포지셔닝.** 대상 페이지는 Fable 5.1을 가장 어려운 knowledge/coding work, 긴 agentic 작업, codebase-wide feature, code review, performance, multi-day autonomous session에 맞는 최상위 일반 모델로 소개한다. 핵심 표현은 다음과 같다.

> “best for ambitious, long-running, asynchronous work”

[Anthropic Fable page](https://www.anthropic.com/claude/fable)

공식 발표는 low/medium effort에서 전 세대와 비슷하거나 더 나은 결과를 낮은 비용으로 낼 수 있고 Claude Code 기본 effort가 high라고 설명한다. [Fable 5.1 announcement](https://www.anthropic.com/claude-fable-and-mythos-5-1)

이 포지셔닝은 fable-advisor가 Fable을 다음 두 구간에 쓰는 이유를 뒷받침한다.

- requirements, decomposition, architecture, spec, routing처럼 판단 밀도가 높은 저볼륨 작업
- accumulated diff를 goal 기준으로 보는 최종 review

반대로 반복 구현은 더 싼 GPT lane으로 보내 비용을 낮추고 vendor lineage를 갈라 review 다양성을 얻으려 한다. Fable이 코드를 못 써서가 아니라, upstream 스스로도 Fable coding 능력을 인정하면서 premium token을 판단 구간에 집중시키는 설계다.

그러나 **Fable은 패턴의 hard dependency가 아니다.** README 자체가 Fable access가 없으면 advisor의 `model: fable`을 `model: opus`로 바꾸고 session도 Opus로 쓰라고 한다. manifest나 `settings.json`이 main session을 Fable로 강제하지도 않는다. 사용자가 `/model fable`을 실행해야 한다. Fable-specific API, hook, tool도 없다.

또한 repo에는 비용/성공률 eval, tests, benchmark harness가 없다. “Codex 구현이 near-parity”, “다른 vendor라 blind spot을 잡는다”, “이 분리가 더 경제적이다”는 README의 설계 주장이지 이 저장소에서 검증한 결과가 아니다. Anthropic의 vendor-authored benchmark도 Fable 역할의 적합성을 보이는 자료일 수는 있지만 이 플러그인의 분업 효과를 직접 검증하지 않는다.

**우리 대응 위치.** quality-goal은 orchestrator `inherit/high`, formal reviewer `opus/high`, 구현 Terra/Sol로 이미 premium judgment + Codex production 구조를 쓴다. #70은 Spec/Plan author를 Codex로 옮기되 Claude formal reviewer를 최종 authority로 남긴다.

**가져올 가치 판정: `부분 채택` — 모델명이 아니라 역할 원칙만.** 판단 authority와 volume-heavy production을 분리하고 cross-lineage verification을 유지하는 원칙은 이미 우리 방향과 맞는다. Fable hard pin으로 바꿀 근거는 없다. 모델 선택은 실제 eval과 availability에 따라 #72에서 다룬다.

**연결 이슈:** #70의 author/reviewer 역할 분리 근거, #72의 capability routing 평가. Fable 전용 새 이슈는 불필요하다.

---

## 이슈별 권고

### #61 — 가장 먼저

[이슈 #61](https://github.com/lee-kyu-hwan/dotfiles/issues/61)은 번호/식별자 이동 파급, finding 해소 간 상호작용, placeholder→구체값 치환 근거를 reviewer 제출 전에 검사하자는 제안이다. #42 최신 실행은 992행·66 requirements·86 AC에서 수정 파급이 여러 절로 번지고 새 High blocker가 생겼다고 기록한다. upstream 6부 contract나 effort escalation에는 이 회귀를 막는 장치가 없다.

권고:

- #61을 #70보다 먼저 또는 #58과 함께 구현
- 기계 가능한 참조/번호/traceability 검사를 controller에 둠
- 판단이 필요한 해소 상호작용은 revision summary와 evidence로 강제
- task effort 상향을 교차 회귀의 해결책으로 취급하지 않음

### #70 — upstream의 실행 아이디어만 선택 흡수

[이슈 #70](https://github.com/lee-kyu-hwan/dotfiles/issues/70)의 최신 댓글은 readiness 97 → Claude 74, 94 → Claude 78이라는 작성자 실측을 기록했다. 이는 이번 조사에서 원시 transcript를 재실행한 수치가 아니다. 다만 두 점 모두 같은 방향으로 크게 갈렸으므로 readiness score를 formal score 예측기로 쓰지 말고 기계적 checklist gate로 바꾸자는 댓글 결론은 합리적이다.

붙일 항목:

- 여섯 함정 전부 fixture/AC화
- preflight stdin EOF 보장
- review 전에 registered artifact path+digest 확인
- readiness attempt를 formal round별로 scope
- score 산식과 evidence 최소 coverage 계약
- controller-enforced timeout과 partial result 보존
- refusal/no-op/complete 구분
- actual model/effort/status provenance
- unsupported effort/model fail-closed
- optional `JUDGMENT CALLS`

붙이지 않을 항목:

- upstream의 6부 문서로 기존 Spec/Plan 대체
- `--skip-git-repo-check`
- 사용자 기본 effort fallback
- prompt preamble으로 상위 instruction/승인 경계 면제
- ship/fix-first/rethink를 formal gate로 사용

### #42 — 독립 dual review를 지킨다

[이슈 #42](https://github.com/lee-kyu-hwan/dotfiles/issues/42)의 독립 Claude/Codex review 후 교차 비평·종합 설계와 달리 upstream optional 경로는 Codex findings를 Fable에게 먼저 전달한다. 이는 같은 것이 아니다.

권고:

- upstream의 clean-context 설명과 짧은 최종 verdict는 참고
- 독립 1차 review 전에는 상대 결과를 노출하지 않음
- 992행 Spec의 review/synthesis와 posting/lifecycle 분할 제안을 effort escalation보다 우선
- upstream sequence를 근거로 독립성 계약을 완화하지 않음

### #72 — 후속 두 개를 새로 분리

[에픽 #72](https://github.com/lee-kyu-hwan/dotfiles/issues/72)의 권장 순서를 유지하고 다음 두 하위 이슈를 안정화 뒤 추가한다.

1. **Task execution routing provenance** — model/effort/rationale/actual/attempt/status를 Plan·state·result에 결합하고 eval 후 override 정책 결정
2. **Plugin packaging/distribution** — self-contained root, namespace migration, version 단일성, cache path, external prerequisites, validate/install/update tests

최신 #72 댓글처럼 #61을 #70보다 앞당기고, #70 readiness는 점수 예측이 아니라 deterministic checklist로 좁힌다.

---

## 최종 채택 매트릭스

| 후보 | 판정 | 근거 | 이슈 |
|---|---|---|---|
| 6부 contract로 우리 Spec/Plan 교체 | **불필요** | upstream은 최소 delegation envelope; 우리 traceability/risk/approval이 더 강함 | #72 비채택 기록 |
| 구현 prompt에서 6부 요소 누락 검사 | **우리가 이미 앞섬** | 승인 Spec+Plan+bounded prompt에 존재 | #70 회귀 AC만 |
| Plan task별 model/effort provenance | **부분 채택** | 비용·재현·지원 실패 분석에 유용; 동적 정책 증거는 없음 | #72 신규 하위 이슈 |
| unsupported effort 반올림 금지 | **채택** | 기존 no-silent-model-substitution과 일치 | #70 + #72 |
| 누락 effort를 사용자 default에 위임 | **불필요** | 실행 재현성 저하 | #70에서 명시 금지 |
| ship/fix-first/rethink를 hard gate로 사용 | **불필요** | 경계/schema/validator 없음 | — |
| 사람용 1-line final verdict | **부분 채택** | 긴 JSON을 대체하지 않는 summary로 유용 | #72 산출물 품질 |
| reports are not evidence 원칙 | **우리가 이미 앞섬** | command 결과, independent verification, fingerprint, digest 존재 | #55/#59 보강 |
| clean-context final reviewer | **우리가 이미 앞섬** | fresh unnamed one-shot + input whitelist + structured prior가 더 강함 | #70에 확장 |
| portable timeout | **부분 채택** | hang/장기 실행 분류에 필요; upstream의 “없으면 무제한”은 부적절 | #70 |
| exit 0 + empty diff refusal 탐지 | **부분 채택** | 실제 work 여부 확인은 유용; staged/untracked/no-op 구분 필요 | #70 |
| Sol `JUDGMENT CALLS` | **부분 채택** | Plan deviation과 별개의 판단 provenance | #70 result schema |
| `--skip-git-repo-check` | **불필요** | quality-goal baseline/fingerprint의 Git 전제와 충돌 | — |
| explicit approval policy | **upstream도 미해결** | 두 쪽 모두 sandbox는 명시하지만 effective approval override는 없음 | #70 |
| plugin manifest + marketplace | **부분 채택** | 공유/버전 배포 시 유용, 개인 반복에는 chezmoi 적합 | #72 신규 하위 이슈 |
| Fable hard dependency | **불필요** | 역할에 적합하나 pattern은 Opus 등으로 대체 가능 | #72 eval만 |
| premium architect/reviewer + cheaper producer 역할 분리 | **우리가 이미 채택 중** | #70 방향 및 현재 Claude review + Codex implementation | #70/#72 |

## 확인하지 못했거나 재현하지 않은 것

- upstream agents를 실제 설치·호출하지 않았다.
- Luna/Sol/Fable model availability, effort 지원 범위, 가격 대비 품질, silent fallback을 실행 검증하지 않았다.
- timeout, approval prompt, empty-diff refusal, auth failure를 재현하지 않았다.
- #70 댓글의 97→74, 94→78 원시 artifacts/transcripts를 독립 재검증하지 않았다. 이슈 작성자의 실측 보고로만 사용했다.
- #42 연구 댓글이 인용한 외부 논문·프로젝트는 이번 fable-advisor 조사 축에서 다시 검증하지 않았고 결론 근거로 재사용하지 않았다.
- upstream binary demo는 재생·프레임 분석하지 않았다. 실행 계약과 무관한 asset으로 분류했다.
- Anthropic 페이지는 공급자 공식 포지셔닝이며 독립 비교 평가가 아니다.

## 출처

- [fable-advisor repository, pinned commit](https://github.com/DannyMac180/fable-advisor/tree/4d6cc62164619a279b076439e1af5439892b958a)
- [raw README](https://raw.githubusercontent.com/DannyMac180/fable-advisor/main/README.md)
- [Anthropic: Claude Fable](https://www.anthropic.com/claude/fable)
- [Anthropic: Fable 5.1 announcement](https://www.anthropic.com/claude-fable-and-mythos-5-1)
- [Claude Code: Create plugins](https://code.claude.com/docs/en/plugins)
- [Claude Code: Plugins reference](https://code.claude.com/docs/en/plugins-reference)
- [Claude Code: Plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [dotfiles issue #70](https://github.com/lee-kyu-hwan/dotfiles/issues/70)
- [dotfiles issue #61](https://github.com/lee-kyu-hwan/dotfiles/issues/61)
- [dotfiles issue #42](https://github.com/lee-kyu-hwan/dotfiles/issues/42)
- [dotfiles epic #72](https://github.com/lee-kyu-hwan/dotfiles/issues/72)
