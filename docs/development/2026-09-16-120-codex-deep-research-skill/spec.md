# Quality Goal Specification

- Task ID: 20260916T005447Z-120-claude-deep-research-워크플로를-codex-전용-ee19ae42
- Mode: standard
- Status: SPEC_REVIEW
- Created: 2026-09-16
- Updated: 2026-09-16
- Source goal: #120 Claude deep-research 워크플로를 Codex 전용 스킬로 이식

## Problem and context

공용 `dot_agents/skills/deep-research/SKILL.md`는 `Workflow(...)` 호출로
`dot_claude/workflows/deep-research.js`를 실행한다. 발견 결과와 공용 스킬 21행은 이
의존성을 확인하며, Codex 런타임에는 `Workflow`가 없다. 따라서 Codex는 공용 스킬을
발견해도 연구 파이프라인을 실행할 수 없다.

이식 대상은 Claude 구현 1,414줄을 복사하는 일이 아니라, 그중 사용자 안전성과 결과의
신뢰성에 영향을 주는 조사 규칙이다. 원본은 3~6개 앵글, 최대 15개 원문, 최대 25개
주장에 대한 3표 검증과 2표 지지·반박 임계값을 사용한다. 테스트는 검색 실패와 결과 없음,
fetch 실패·paywall·무관함, 예산으로 누락된 검증, `confirmed`/`refuted`/`unverified`
분리, 원문 데이터의 프롬프트 인젝션 격리를 각각 보장한다.

Codex에서는 `web__run.search_query`로 검색하고 `web__run.open`으로 원문을 연다. 보조
에이전트는 부모를 포함한 4개 슬롯 환경에서 최대 3개만 동시에 실행할 수 있다. 따라서
Claude의 최대 25개 주장 × 3표를 그대로 병렬화하면 25배치가 필요하다. 이 Spec은 검증
상한과 폴백을 명시해, 실행 불능이나 과장된 확정을 피한다.

저장소에는 `AGENTS.md`가 없으며 적용할 저장소 규칙은 루트 `CLAUDE.md`다. 이 문서는
사용자 대화와 커밋 메시지를 한국어로 하도록 정한다. `dot_codex/skills/<name>/SKILL.md`는
chezmoi를 통해 `~/.codex/skills/<name>/SKILL.md`로 배포되는 관례이고, `.chezmoiignore`는
새 `deep-research` 경로를 제외하지 않는다.

## Goals

- Codex가 복합적인 다중 출처 조사 요청을 전용 `deep-research` 스킬로 발견하고, Codex
  도구만으로 검증 가능한 연구 보고서를 작성하게 한다.
- 확인한 원문과 교차검증에 근거한 주장만 `confirmed` finding으로 제시하고, 미확인·반박·상한
  밖 항목과 조사 실패를 숨기지 않게 한다.
- 기존 공용 스킬과 Claude 워크플로의 동작을 바꾸지 않은 채 Codex 전용 산출물을 배포 가능한
  위치에 둔다.

## Non-goals

- `dot_agents/skills/deep-research/`, `dot_claude/workflows/deep-research.js`, 또는
  Claude 회귀 테스트의 행위를 변경하지 않는다.
- Claude의 25개 주장 × 3표 동시 실행량, `Workflow` 호출, Claude 전용 런타임이나 도구를
  Codex에서 흉내 내지 않는다.
- 보조 실행 스크립트, 결과 파일 자동 저장, README, 설치 안내를 새로 만들지 않는다.
  `agents/openai.yaml`은 발견·조사·검증에 관여하지 않고 `quick_validate.py`의 검증 대상도
  아닌 표시용 메타데이터이므로 만들지 않는다.
- `chezmoi apply`, 커밋, push, PR 생성, 실제 계정 홈의 배포 파일 변경은 범위 밖이다.
- 단일 사실 조회, 단순 검색, 실시간 외부 서비스에 대한 영속 변경은 deep-research 흐름의
  대상이 아니다.

## Requirements

- **R1.1** `dot_codex/skills/deep-research/SKILL.md`의 frontmatter는 `deep-research`,
  `딥 리서치`, `웹조사해서 정리`, `리서치 보고서`처럼 다중 출처의 검증 보고서를 뜻하는
  요청을 발견하되, 단일 사실·단순 검색 요청은 직접 검색으로 넘기는 경계를 설명해야 한다.
  이 분리는 공용 스킬의 21행 `Workflow` 호출 의존과 Codex 런타임의 비호환성을 전제로 한다.
- **R1.2** 스킬은 질문이 불충분할 때에만 연구 범위에 필요한 질문을 하고, 충분한 질문은
  한 문장의 연구 질문으로 정규화해야 한다.
- **R2.1** 복합 질문은 서로 중복되지 않는 3~6개 관점으로 분해하고, 관점별 검색 결과를
  `성공`, `결과 없음`, `실패`로 구분해야 한다.
- **R2.2** 검색 후보는 중복·무관·유효하지 않은 URL을 구분한 뒤 전체 조사에서
  `web__run.open` 호출을 최대 15회로 배정해 실제 원문을 열고, 품질·발행일·검증 가능한
  주장·원문 인용을 확인해야 한다. 부모와 검증자의 open 호출은 같은 전역 예산을 소비하며,
  검색 결과 요약만으로 finding을 만들면 안 된다.
- **R3.1** Codex 전용 스킬과 그 reference는 Codex 도구인 `web__run.search_query`와
  `web__run.open` 및 선택적인 `collaboration.*`만 지시하고, Claude의 `Workflow`,
  `WebSearch`, `WebFetch`, `~/.claude/`, `.claude/workflows`, `dot_claude/`를 참조하거나
  요구하지 않아야 한다. 금지 참조 검사는 대상 디렉터리 존재를 먼저 확인하고 `rg`의
  종료 코드가 정확히 1(매치 없음)일 때만 통과해야 한다.
- **R4.1** 기본 교차검증은 중요도와 출처 품질로 고른 최대 5개 주장에 대해, 최대 3개의
  동시 보조 에이전트가 같은 주장 묶음을 독립적으로 검증하는 3표 패널이어야 한다. 각 표는
  원문의 인용 적합성, 독립 반대 근거 검색, 출처 품질, 최신성, 마케팅·추측 가능성을 확인하고
  사용한 URL과 판정을 돌려줘야 한다.
- **R4.2** 기본 패널에서 `SUPPORTS_REQUIRED=2`는 3표 중 `supported`가 2표 이상이면
  확정 후보가 된다는 뜻이고, `REFUTATIONS_REQUIRED=2`는 `refuted`가 2표 이상이면
  반박이라는 뜻이다. 둘 중 어느 임계값도 못 채우거나 표가 실행되지 않으면 `unverified`로
  남겨야 하며, 2-1 같은 상충 표결을 만장일치로 표현하면 안 된다.
- **R4.3** 폴백 계단은 다음 한 가지다. 가용 보조 에이전트가 정확히 2명이면 같은 주장을
  두 검증자가 독립적으로 검증하고 두 표가 모두 `supported`일 때만 `confirmed` 후보로
  둔다. 가용 보조 에이전트가 1명 이하이거나 `collaboration.*`을 쓸 수 없으면 부모가
  서로 다른 독립 원문 2개를 열어 같은 검증 체크를 완료하고 신뢰할 만한 직접 반대 근거가
  없을 때만 `confirmed` 후보로 둔다. 어느 단계든 조건 미달은 `unverified`이며,
  폴백 사실·실제 표 수·원문 수를 표시하고 R4.4의 high는 부여하지 않아야 한다.
- **R4.4** 신뢰도(`high`·`medium`·`low`)는 모델의 자유 서술이 아니라 실제로 연 원문의
  출처 품질과 표결이라는 provenance에서만 기계적으로 파생해야 한다. 기본 3표 패널의
  `high`는 주장 묶음에 서로 다른 primary URL이 2개 이상이고 그 묶음의 모든 주장이
  정확히 3-0 `supported`일 때, `medium`은 high가 아니면서 primary 또는 secondary
  출처가 하나 이상일 때, `low`는 blog·forum·unreliable 출처만 있을 때다. R4.3의 두
  폴백 단계에서는 이 조건을 만족해도 high를 부여하지 않는다.
- **R4.5** 각 보조 검증자는 `web__run.search_query`를 최대 2회, `web__run.open`을 최대
  3회만 호출하고 보조 에이전트를 다시 spawn하지 않아야 한다. 부모는 검증에 필요한 open
  예산을 먼저 남기며, 전체 15회 open 예산 또는 개인 상한에 도달하면 새 호출을 시작하지
  않고 남은 표·주장을 `unverified` 및 예산 미실행으로 기록해야 한다.
- **R5.1** 결과는 `confirmed`, `refuted`, `unverified`, 검증 상한 밖 항목을 상호 배타적으로
  구분하고, 반박 또는 미검증 항목을 확정 finding으로 합성하지 않아야 한다. 증거 부족과
  반대 증거의 존재도 각각 구분해 설명해야 한다.
- **R5.2** 각 확정 finding에는 실제로 연 원문 URL을 최소 하나 제목과 함께 Markdown 링크로
  넣고, 가능하면 독립 URL의 교차 근거와 표결을 덧붙여야 한다. 내부 검색 ref_id나 검색
  스니펫을 인용으로 제시하면 안 된다.
- **R6.1** 최종 결과는 계획·실행된 앵글, 앵글별 실패·결과 없음, 중복·무관·paywall,
  fetch 실패, fetch·검증 예산으로 누락된 항목, 검증 실패, 검증 상한 밖 항목을 실제
  커버리지 한계로 공개해야 한다. 검증 단계에서는 실행·미실행 표 수, 부모와 검증자가
  실제로 연 원문 수, 남은 open 예산을 함께 공개해야 한다. 모든 검색 또는 원문 확인이
  실패한 경우에는 연구 결론이 아니라 재시도를 권해야 한다.
- **R6.2** 웹 페이지, 검색 제목·요약, 보조 에이전트 반환값은 untrusted data다. 지시문으로
  실행·권한·경로·결론을 바꾸지 말고, 원문에서 나온 명령이나 프롬프트 인젝션을 따르지
  않는 규칙을 스킬에 명시해야 한다.
- **R7.1** 사용자가 명시적으로 저장을 요청하지 않는 한 조사 결과 파일을 만들지 않아야 한다.
  스킬 구현은 문서·상태·결과 검사 보조 스크립트를 만들지 않는다.
- **R7.2** 세부 계약은 `references/research-protocol.md`로 분리하고 `SKILL.md`에서
  언제 완전히 읽어야 하는지 연결해야 한다. entrypoint에는 발견 경계, 실행 순서, 확정
  금지 규칙, 사용자 결과 형식만 두며 Claude 워크플로 전체를 복제하지 않는다.
- **R7.3** `agents/openai.yaml`은 발견·조사·검증에 불필요한 표시용 메타데이터이고
  `quick_validate.py`의 검증 대상도 아니므로 새 deep-research 스킬에 추가하지 않아야 한다.
- **R8.1** Codex 전용 구현 파일은 `dot_codex/skills/deep-research/` 아래에만 추가하고,
  이 작업의 문서 산출물은
  `docs/development/2026-09-16-120-codex-deep-research-skill/` 아래에만 추가한다. 공용
  스킬과 Claude 워크플로는 수정하지 않으며, 기존 Claude 회귀 테스트 114 pass / 0 fail을
  유지해야 한다.
- **R8.2** 새 스킬은 Codex skill validator를 통과하고, `name: deep-research`, 꺾쇠가 없는
  1,024자 이하 description, 금지된 미완성 표기를 만족해야 한다.
- **R9.1** chezmoi source의 target-path는
  `/Users/lee-kyu-hwan/.codex/skills/deep-research/SKILL.md`여야 하며, source `SKILL.md`와
  `chezmoi -S <워크트리> cat dot_codex/skills/deep-research/SKILL.md` 출력을 결정적으로
  비교하고 `chezmoi -S <워크트리> diff`에서 적용 예정 내용을 확인해야 한다. 실제 apply는
  하지 않는다는 검증 한계를 결과에 남겨야 한다.
- **R10.1** 구현·검증 문서와 사용자 보고는 한국어로 작성한다. 모든 판정 명령은 지정
  워크트리 루트에서 `python3`+PyYAML, `rg`, `node`, `chezmoi`, `git`가 준비된 환경에서
  실행하며, 검증과 변경 범위 확인에는 지정된 정적 검사, chezmoi preview, Claude 회귀,
  변경 통계 및 네 가지 대표 시나리오의 문서 기반 판정을 사용해야 한다.

## Acceptance criteria

- **AC-1** `description`이 네 발견 표현과 다중 출처 검증 보고서의 목적, 단일 사실·단순 검색의 제외를 함께 명시한다. [문서] `dot_codex/skills/deep-research/SKILL.md` frontmatter
- **AC-2** 충분한 질문은 한 문장으로 정규화하고, 부족한 질문에서만 필요한 범위 질문을 하며, 단일 사실 요청을 직접 검색으로 보내는 `요청 분기`가 있다. [문서] `dot_codex/skills/deep-research/SKILL.md`
- **AC-3** 복합 질문에 3~6개 관점, 관점별 검색 상태, 부모·검증자의 합계가 최대 15회인 `web__run.open` 예산, 원문 선택·열기·추출의 순서와 상태 구분이 `조사와 원문 확인` 절에 있다. [문서] `dot_codex/skills/deep-research/references/research-protocol.md`
- **AC-4** Codex 전용 스킬 디렉터리에 Claude 전용 도구·경로 참조가 없다. [실행] (CMD-2)
- **AC-5** 기본 패널은 최대 5개 주장에 대해 최대 3개 보조 에이전트로 독립 검증을 수행하고, 표마다 체크리스트와 URL을 요구하는 `기본 3표 교차검증` 절이 있다. [문서] `dot_codex/skills/deep-research/references/research-protocol.md`
- **AC-6** `supported` 2표 이상은 확정 후보, `refuted` 2표 이상은 반박, 나머지·미실행은 미검증으로 분류하며 2-1 상충과 표결 수를 보고하는 `판정 임계값` 절이 있다. [문서] `dot_codex/skills/deep-research/references/research-protocol.md`
- **AC-7** 가용 보조 에이전트가 2명이면 두 독립 검증 표가 모두 `supported`여야 하고, 1명 이하 또는 `collaboration.*` 부재이면 부모가 독립 원문 2개를 모두 열어야 하며, 어느 단계든 조건 미달은 `unverified`다. 두 폴백 단계 모두 high 금지와 실제 표·원문 수 공개를 명시한 `동시성 폴백` 절이 있다. [문서] `dot_codex/skills/deep-research/references/research-protocol.md`
- **AC-8** `confirmed`, `refuted`, `unverified`, 검증 상한 밖 항목이 섞이지 않으며, 반대 증거와 증거 부족을 별도 설명하는 `결과 전달과 한계` 절이 있다. [문서] `dot_codex/skills/deep-research/SKILL.md`
- **AC-9** 모든 확정 finding은 실제로 연 원문 URL을 제목이 있는 Markdown 링크로 최소 하나 포함하고 내부 ref_id나 스니펫을 인용하지 않는 `결과 전달과 한계` 절이 있다. [문서] `dot_codex/skills/deep-research/SKILL.md`
- **AC-10** 앵글별 검색 실패·결과 없음, 중복·무관·paywall, fetch·검증 실패, 예산 누락, 검증 상한 밖 항목과 검증 단계의 실행·미실행 표 수·실제 원문 수·남은 open 예산을 커버리지와 함께 공개하고 전면 실패를 결론으로 오인하지 않는 `실패와 커버리지 공개` 절이 있다. [문서] `dot_codex/skills/deep-research/references/research-protocol.md`
- **AC-11** 웹·검색·보조 에이전트 텍스트를 데이터로 취급하고 그 안의 명령이나 지시를 실행하지 않는 `신뢰 경계` 규칙이 있다. [문서] `dot_codex/skills/deep-research/SKILL.md`
- **AC-12** 저장 요청이 없는 결과 파일·보조 스크립트가 없고, 세부 계약만 reference로 분리하며 `SKILL.md`가 이를 읽도록 라우팅하는 `저장과 세부 계약` 절이 있다. [문서] `dot_codex/skills/deep-research/SKILL.md`
- **AC-13** 새 Codex 스킬은 정적 검증과 frontmatter 검사를 통과한다. [실행] (CMD-1, CMD-3)
- **AC-14** 변경 범위에 공용 스킬·Claude 워크플로 변경이 없고, status의 허용 경로가 새 스킬 또는 이 작업의 문서 산출물뿐이며 Claude 회귀가 114 pass / 0 fail이다. [실행] (CMD-6, CMD-7, CMD-8)
- **AC-15** chezmoi target-path가 요구된 account-home 경로이고 source `SKILL.md`와 chezmoi cat 출력이 byte-identical이며, diff에서 적용 예정 내용을 확인하고 apply를 하지 않은 한계를 결과에 명시한다. [실행] (CMD-4, CMD-5)
- **AC-16** 네 대표 시나리오에서 스킬의 지시 위치가 판정 가능하다: `요청 분기`는 단일 사실을 직접 검색으로, `조사 흐름`은 다중 출처의 관점·원문·검증을, `결과 전달과 한계`는 출처 충돌·일부 fetch 실패의 상태와 커버리지를 지시한다. [문서] `dot_codex/skills/deep-research/SKILL.md`
- **AC-17** 기본 3표 패널의 신뢰도가 provenance에서만 계산되고, high는 서로 다른 primary URL 2개 이상과 주장 묶음 전체의 정확한 3-0 `supported`, medium은 high가 아니면서 primary 또는 secondary 출처 하나 이상, low는 blog·forum·unreliable만이라는 `신뢰도 파생` 절이 있다. [문서] `dot_codex/skills/deep-research/references/research-protocol.md`
- **AC-18** 검증자마다 search_query 2회·open 3회 상한, 중첩 spawn 금지, 전체 open 15회 예산과 예산 도달 시 새 호출 대신 `unverified`·미실행을 기록하는 `검증 예산` 절이 있다. [문서] `dot_codex/skills/deep-research/references/research-protocol.md`
- **AC-19** `agents/openai.yaml`이 발견·조사·검증에 불필요한 표시용 메타데이터이고 quick_validate.py 검증 대상이 아니어서 만들지 않는다는 `산출물 범위` 절이 있다. [문서] `dot_codex/skills/deep-research/SKILL.md`

## Requirements traceability

| Requirement | Acceptance criteria | Judgement method |
|---|---|---|
| R1.1 | AC-1 | `dot_codex/skills/deep-research/SKILL.md` frontmatter 확인 |
| R1.2 | AC-2, AC-16 | `SKILL.md`의 `요청 분기` 확인 |
| R2.1 | AC-3, AC-16 | `research-protocol.md`의 조사 절 확인 |
| R2.2 | AC-3, AC-9 | `research-protocol.md`와 `SKILL.md`의 원문·인용 규칙 확인 |
| R3.1 | AC-4 | CMD-2 |
| R4.1 | AC-5 | `research-protocol.md`의 기본 패널 확인 |
| R4.2 | AC-6 | `research-protocol.md`의 임계값 확인 |
| R4.3 | AC-7 | `research-protocol.md`의 폴백 확인 |
| R4.4 | AC-17 | `research-protocol.md`의 provenance 신뢰도 파생 확인 |
| R4.5 | AC-18 | `research-protocol.md`의 검증자·전역 예산 확인 |
| R5.1 | AC-8 | `SKILL.md`의 결과 상태 규칙 확인 |
| R5.2 | AC-9 | `SKILL.md`의 finding 인용 규칙 확인 |
| R6.1 | AC-10, AC-16 | `research-protocol.md`의 실패·커버리지 절 확인 |
| R6.2 | AC-11 | `SKILL.md`의 신뢰 경계 확인 |
| R7.1 | AC-12 | `SKILL.md`의 저장 규칙과 파일 목록 확인 |
| R7.2 | AC-12 | `SKILL.md`의 reference 라우팅 확인 |
| R7.3 | AC-19 | `SKILL.md`의 산출물 범위 확인 |
| R8.1 | AC-14 | CMD-6, CMD-7, CMD-8 |
| R8.2 | AC-13 | CMD-1, CMD-3 |
| R9.1 | AC-15 | CMD-4, CMD-5 |
| R10.1 | AC-13, AC-14, AC-16 | CMD-1, CMD-3, CMD-6, CMD-7, CMD-8 및 문서 확인 |

## Architecture

새 산출물은 `dot_codex/skills/deep-research/`에만 둔다.

```text
SKILL.md
  ├─ 발견 경계·요청 분기·사용자 결과 계약
  └─ references/research-protocol.md를 읽도록 라우팅
       ├─ 3~6개 관점 → 검색 상태 기록
       ├─ URL 정규화·선택 → 전체 최대 15회 원문 open·주장 추출
       ├─ 최대 5개 핵심 주장 → 3개 병렬 검증자 묶음
       └─ 상태 분리·커버리지 공개·안전한 폴백
```

`SKILL.md`는 진입점에서 매번 필요한 발견 경계와 안전 규칙을 유지한다. 조건부이고 긴
운영 계약은 `references/research-protocol.md`에 두어, 복잡한 연구 요청일 때만 완전히
읽게 한다. 이는 기존 Codex 스킬의 reference 분리 관례와 skill-creator의 progressive
disclosure 원칙에 맞고, 1,414줄 Claude 워크플로의 구현 세부를 복제하지 않는다.

원문 확인은 `web__run.search_query`와 `web__run.open`의 조합으로 한다. `open`에 성공한
원문만 claim의 출처가 된다. 부모와 검증자의 모든 open 호출은 전체 15회 예산을 공유하고,
검증자를 시작하기 전에 최대 9회(검증자당 3회)를 남긴다. 기본 검증은 부모가 중요도
(central 우선)와 출처 품질(primary, secondary 우선)로 최대 5개를 고른 뒤, 세 보조
에이전트에 같은 묶음을 보낸다. 각 보조 에이전트는 중첩 spawn 없이 최대 두 번 검색하고
세 번 원문을 열어 독립 판정을 수행한다. 이 방식은 동시 슬롯 3개를 초과하지 않으면서도
주장마다 3개의 독립 판정을 유지하며, 예산으로 못 한 표는 `unverified`로 남긴다.

## Interfaces and data flow

입력은 사용자의 자연어 연구 요청이다. 스킬은 충분한 입력을 한 문장 질문으로 정규화하고,
불충분한 입력에서만 범위 질문을 한다. 단일 사실은 이 계약을 시작하지 않는다.

복합 질문의 실행 데이터는 메모리와 대화 안에서만 다음처럼 취급한다.

| 단계 | 입력 | 산출·상태 | 다음 단계의 제한 |
|---|---|---|---|
| 관점 | 정규화 질문 | 3~6개 서로 다른 관점 | 중복 관점 제거 |
| 검색 | 관점별 query | 성공·결과 없음·실패와 후보 URL | 관점별 실패를 보존 |
| 원문 | 후보 URL | 실제로 연 원문, 품질, 날짜, 주장, 인용 | 부모·검증자 합계 최대 15회 open, paywall·무관·실패 별도 |
| 검증 | 최대 5개 핵심 주장 | 주장별 support/refute/unverified 표와 URL, provenance 신뢰도 | 기본 3표 또는 아래 계단식 폴백; 검증자당 검색 2회·open 3회 |
| 합성 | 확정 후보만 | finding, 링크, 표결, 상태·커버리지 한계 | 다른 상태를 finding에 섞지 않음 |

기본 패널은 `supported >= 2`이면 확정 후보로, `refuted >= 2`이면 `refuted`로 판정한다.
둘 다 아니면 `unverified`다. 둘 임계값이 동시에 성립할 수 있는 비정상 결과는 안전하게
`unverified`로 두고 판정 충돌을 공개한다. 2-1은 확정 후보가 될 수 있으나, 반대 표와
비만장일치 사실을 보고한다. 모든 최종 finding은 부모 또는 검증자가 실제로 연 원문 중
최소 하나의 URL을 포함한다.

신뢰도는 모델이 작성하는 설명이 아니라 provenance 계산값이다. 기본 3표 패널에서는 주장
묶음에 서로 다른 primary URL이 2개 이상이고 모든 주장이 정확히 3-0 `supported`일 때만
`high`, high가 아니면서 primary 또는 secondary 출처가 하나 이상이면 `medium`,
blog·forum·unreliable 출처만이면 `low`다.

폴백 계단은 다음 한 가지다. 가용 보조 에이전트가 정확히 2명이면 같은 주장을 두 검증자가
독립적으로 검증하고 두 표가 모두 `supported`일 때만 `confirmed` 후보로 둔다. 가용 보조
에이전트가 1명 이하이거나 `collaboration.*`을 쓸 수 없으면 부모가 서로 다른 독립 원문
2개를 열어 같은 검증 체크를 완료하고 신뢰할 만한 직접 반대 근거가 없을 때만 `confirmed`
후보로 둔다. 어느 단계든 조건 미달은 `unverified`이며, 폴백 사실·실제 표 수·원문 수를
표시하고 R4.4의 high는 부여하지 않아야 한다.

## Failure behavior

- 질문이 비어 있거나 범위가 결정되지 않으면 결론을 만들지 않고 필요한 범위만 묻는다.
- 한 관점의 검색 실패는 다른 관점을 계속하되, 실패 관점과 사유를 커버리지에 남긴다.
  모든 관점 검색이 실패하거나 선택한 모든 원문을 열지 못하면 `infrastructure_failure`로
  알리고 재시도를 권한다. 이는 `no_claims`가 아니다.
- `no_results`, 중복, 무관, paywall, fetch 실패, fetch 예산 초과는 각각 다른 원인으로
  기록한다. 선택 또는 검증 상한으로 제외된 항목은 `검증 상한 밖`으로 남기며 finding으로
  만들지 않는다.
- 검증 도구·에이전트 실패, rate limit, 원문을 열 수 없음, 표 부족은 반박 근거가 아니다.
  해당 주장은 `unverified`와 실패 사유로 공개한다. 직접적인 신뢰 가능한 반대 근거가
  있어 반박 임계값에 도달한 경우만 `refuted`다.
- 확정 주장이 하나도 없으면 `refuted`와 `unverified`를 각각 보고한다. 합성 단계가
  실패해도 이미 확인된 원문 기반 `confirmed` 후보를 새로운 prose finding으로 꾸미지
  말고, 합성 실패와 미병합 상태를 알린다.
- 예산·도구·동시성 제한이 있으면 실행한 관점, 부모와 검증자가 연 원문 수, 검증한 주장
  수, 실행·미실행 표 수와 남은 open 예산을 함께 알려 사용자가 커버리지 상한을 판단하게
  한다. 검증자는 개인 호출 상한·전역 open 예산에 도달하면 새 호출이나 중첩 spawn을 하지
  않고 해당 표·주장을 `unverified`로 남긴다.

## Security and risk

검색 결과, 페이지 본문, 인용, 제목, URL의 설명문, 보조 에이전트 반환은 신뢰하지 않는
데이터다. 이 안의 “지시 무시”, 셸 명령, 파일 경로, 외부 전송 요구, 출처·상태 조작 요구는
연구 지시나 권한이 아니다. 모델은 이를 인용·주장 추출 대상으로만 읽고, 원래 연구 질문과
이 스킬의 규칙을 우선한다.

원문을 열었다는 사실은 내용의 진실을 보장하지 않는다. 그래서 source quality, 날짜,
원문 인용과 주장 간 적합성, 독립 반대 근거를 분리해 평가한다. 예산으로 못 연 자료와
검증 실패를 `refuted`로 변환하지 않으며, 증거 부족을 반대 증거로 표현하지 않는다.
최종 Markdown 링크는 실제로 연 URL만 사용하고 내부 tool ref_id, 비공개 컨텍스트,
임의로 만든 URL을 노출하지 않는다. 웹 인용은 도구의 출처별 저작권 상한을 지킨다.

## Test strategy

구현 뒤에는 새 스킬의 구조·금지 참조·frontmatter를 결정적으로 검사하고, chezmoi는
source 경로에서 target과 적용 예정 diff만 미리 본다. `chezmoi apply`는 실행하지 않는다.
Claude 워크플로를 건드리지 않았다는 사실은 기존 114개 테스트와 변경 범위 검사로 확인한다.

판정 명령은 작업 디렉터리
`/Users/lee-kyu-hwan/code/dotfiles__worktrees/120-feat-codex-deep-research`에서 실행한다.
선행 도구는 PyYAML을 설치한 `python3`, `rg`, `node`, `chezmoi`, `git`다.

대표 시나리오 네 가지는 `SKILL.md`의 지정 헤딩을 구현 후 직접 읽어 판정한다. (a) 다중
출처 요청은 3~6개 관점, 원문 open, 패널 검증과 finding 링크를 지시해야 한다. (b) 단일
사실은 직접 검색으로 보낸다. (c) 상충 출처는 2표 임계값, 표결 공개 및 상태 분리를
지시한다. (d) 일부 fetch 실패는 남은 원문을 계속 처리하되 실패와 감소한 커버리지를
공개해야 한다.

### 판정 명령 표

| ID | 명령 | 통과 조건 |
|---|---|---|
| CMD-1 | `python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py dot_codex/skills/deep-research` | 종료 코드 0 및 `Skill is valid!` |
| CMD-2 | `test -d dot_codex/skills/deep-research && { rg -n -e 'Workflow' -e '\.claude/workflows' -e '~/.claude' -e 'dot_claude/' -e 'WebSearch' -e 'WebFetch' dot_codex/skills/deep-research; test $? -eq 1; }` | 대상 디렉터리가 존재하고 `rg`가 정확히 종료 코드 1(매치 없음)이며, 그 밖의 종료 코드는 실패 |
| CMD-3 | `python3 -c 'from pathlib import Path; import yaml; t=Path("dot_codex/skills/deep-research/SKILL.md").read_text(); f=yaml.safe_load(t.split("---", 2)[1]); assert f["name"] == "deep-research"; assert "<" not in f["description"] and ">" not in f["description"]'` | 종료 코드 0 |
| CMD-4 | `chezmoi -S /Users/lee-kyu-hwan/code/dotfiles__worktrees/120-feat-codex-deep-research target-path dot_codex/skills/deep-research/SKILL.md` | 정확히 `/Users/lee-kyu-hwan/.codex/skills/deep-research/SKILL.md` 출력 |
| CMD-5 | `diff -u dot_codex/skills/deep-research/SKILL.md <(chezmoi -S /Users/lee-kyu-hwan/code/dotfiles__worktrees/120-feat-codex-deep-research cat dot_codex/skills/deep-research/SKILL.md) && chezmoi -S /Users/lee-kyu-hwan/code/dotfiles__worktrees/120-feat-codex-deep-research diff` | source와 chezmoi cat 출력의 byte 비교가 종료 코드 0이고, `chezmoi diff`를 실행하며 apply를 실행하지 않음 |
| CMD-6 | `node --test tests/deep-research.test.mjs` | 114 pass / 0 fail |
| CMD-7 | `git diff --stat` | 기존 추적 파일의 변경 통계가 승인 경로 밖을 포함하지 않음 |
| CMD-8 | `git status --short | awk 'BEGIN { ok=1 } { p=substr($0,4); if (p !~ /^dot_codex\/skills\/deep-research\// && p !~ /^docs\/development\/2026-09-16-120-codex-deep-research-skill\//) ok=0 } END { exit ok ? 0 : 1 }'` | status의 모든 새·수정 경로가 `dot_codex/skills/deep-research/` 또는 `docs/development/2026-09-16-120-codex-deep-research-skill/` 허용 목록 안에 있고 공용·Claude 파일이 없음 |

## Decisions

### D1. Codex 교차검증은 5개 주장 묶음의 3표 패널을 기본으로 한다

대안 A는 주장마다 세 보조 에이전트를 그대로 실행하는 방식이다. 25개 주장을 유지하면
75표가 25개의 직렬 배치가 되어 Codex의 동시 보조 에이전트 3개 상한에서는 완주 가능성이
낮다. 대안 B는 한 보조 에이전트가 여러 주장을 묶어 검증하되 세 보조 에이전트를 동시에
실행하는 방식이다. 주장별로 세 독립 판정을 유지하면서 세 슬롯을 모두 사용한다. 대안 C는
보조 에이전트 없이 부모의 출처 확인만으로 대체하는 방식으로, 비용은 낮지만 독립 판정의
보장이 약하다.

대안 B를 권고한다. 검증 대상은 central 및 더 높은 품질 출처를 우선한 최대 5개로 줄이고,
세 검증자가 각 주장에 독립 검색·원문 열기·반대 근거 탐색을 한다. `SUPPORTS_REQUIRED=2`,
`REFUTATIONS_REQUIRED=2`의 2표 임계값은 그대로 보존한다. 이 축소는 25개보다 넓은 주장
커버리지를 포기하므로 제외한 주장을 `검증 상한 밖`으로 공개한다.

### D2. 낮은 동시성에서는 확정을 늘리지 않는 계단식 폴백을 쓴다

폴백 계단은 다음 한 가지다. 가용 보조 에이전트가 정확히 2명이면 같은 주장을 두 검증자가
독립적으로 검증하고 두 표가 모두 `supported`일 때만 `confirmed` 후보로 둔다. 가용 보조
에이전트가 1명 이하이거나 `collaboration.*`을 쓸 수 없으면 부모가 서로 다른 독립 원문
2개를 열어 같은 검증 체크를 완료하고 신뢰할 만한 직접 반대 근거가 없을 때만 `confirmed`
후보로 둔다. 어느 단계든 조건 미달은 `unverified`이며, 폴백 사실·실제 표 수·원문 수를
표시하고 R4.4의 high는 부여하지 않아야 한다. 이 결정은 도구 부재를 반박으로 바꾸지 않고,
환경별 상한 변화에도 안전한 결과를 낸다.

### D3. 조사 상한은 3~6개 관점, 15개 원문, 5개 검증 주장으로 한다

관점 3~6과 전체 open 15회는 Claude 원본의 원문 상한을 Codex의 부모·검증자 공동 예산으로
보존한다. 서로 다른 관점을 확보하고 관점당 후보를 공정히 배정하는 데 필요한 범위이며,
Codex의 검색은 한 호출에 최대 4 query라는 제약 안에서 여러 호출로 나눌 수 있다. 검증자를
시작하기 전에 최대 9회 open 예산을 남기고, 검증자 한 명은 검색 2회·open 3회까지만 쓴다.
검증만 25에서 5로 낮춘다. 이는 세 검증자가 각 주장 묶음을 독립 확인해야 하는 비용과
3 슬롯 상한을 반영한 것이다. 세 상한 모두 제한으로 잘린 항목·앵글·표를 사용자에게
공개한다.

### D4. `SKILL.md`와 하나의 reference를 분리하고 보조 스크립트는 만들지 않는다

`SKILL.md` 하나에 모든 세부 판정표를 넣는 대안은 매 invocation에 불필요하게 긴 문서를
싣는다. 반대로 Claude 워크플로를 여러 파일·스크립트로 복제하는 대안은 Codex 런타임
도구를 셸에서 호출할 수 없고 유지할 구현만 늘린다. `web__run`과 `collaboration.*`는
모델 런타임 도구이므로 보조 셸 스크립트가 호출할 수 없다. 결과 구조 검사도 기본적으로
파일을 만들지 않는 결과에는 반복 사용 가치가 없다.

그러므로 진입점과 `references/research-protocol.md`만 만든다. 이는 progressive disclosure와
기존 Codex의 contract reference 관례를 따르며, `scripts/`·README·설치 문서는 만들지 않는
결정이다. `agents/openai.yaml`도 발견·조사·검증에 불필요하고 quick_validate.py 검증 대상이
아닌 표시용 메타데이터이므로 만들지 않는다.

### D5. chezmoi는 적용하지 않고 target과 diff로 배포 예정 상태만 증명한다

`chezmoi apply` 뒤 source와 deployed 파일을 직접 비교하는 대안은 실제 account-home을
변경하므로 사용자 선택과 범위를 벗어난다. 대신 source 워크트리를 명시한 `target-path`가
배포 목적지를 결정하는지 확인하고 `chezmoi -S <워크트리> diff`로 적용 시 생성·변경될
내용을 검토한다. 이는 완료조건의 배포 매핑과 예정 내용을 결정적으로 증명하지만, 실제
apply 뒤 파일 존재·동일성을 증명하지는 못한다. 그 한계를 결과에 명시한다.

### D6. 기존 Claude 구현은 회귀 테스트로만 보호한다

이 기능은 Codex 전용 경로에 추가한다. 공용 스킬과 Claude 워크플로를 고쳐 공유하려는
대안은 Codex에 없는 `Workflow` 의존을 해결하지 못하고 기존 동작에 위험을 준다. 따라서
해당 파일은 수정하지 않고 `node --test tests/deep-research.test.mjs`의 114 pass / 0 fail과
변경 범위 검사로 회귀 없음을 확인한다. 저장소 규칙 출처도 존재하지 않는 `AGENTS.md`가
아니라 `CLAUDE.md`로 기록한다.

### D7. 신뢰도는 provenance 계산값으로만 공개한다

모델이 그럴듯한 설명으로 신뢰도를 정하는 대안은 표결·출처 품질과 무관한 과장을 허용한다.
따라서 기본 3표 패널에는 서로 다른 primary URL 2개 이상과 묶음 전체 3-0 `supported`를
동시에 만족할 때만 high를 계산하고, 그 밖에 primary 또는 secondary가 있으면 medium,
blog·forum·unreliable만 있으면 low를 계산한다. 두 표와 부모 원문 폴백은 이 계산의 다른
조건을 만족해도 high를 쓰지 않는다.

### D8. 검증 비용은 원문 예산과 중첩 spawn 금지로 닫는다

검증자에게 호출 상한만 두고 부모 원문 예산과 분리하는 대안은 전체 open 15회 상한을 넘길
수 있다. 전체 open 15회 공동 예산 안에서 검증자당 검색 2회·open 3회, 중첩 spawn 금지를
적용하면 3슬롯 가정이 유지되고 high에 필요한 서로 다른 primary 원문 2개도 확보할 수 있다.
예산이 먼저 소진되면 새 호출 대신 표와 주장을 `unverified`로 남겨 커버리지에 공개한다.
