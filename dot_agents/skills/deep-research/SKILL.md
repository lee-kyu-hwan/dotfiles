---
name: deep-research
description: Use when the user wants a deep, multi-source, fact-checked research report (triggers like "딥 리서치", "deep research", "웹조사해서 정리", "리서치 보고서"). For a quick single-fact lookup, search directly instead.
---

# Deep Research

`~/.claude/workflows/deep-research.js`가 파이프라인을 실행한다. 이 스킬은 질문 다듬기와
결과 전달만 담당한다. 앵글 수·fetch 상한·검증 임계값은 워크플로 상단 상수가 기준이다.

## Step 0 — 스코프 확인 (실행 전)

질문이 불충분하면 2-3개만 되묻는다. 예: 예산·용도·지역이 없는 "어떤 차를 살까".
충분하면 연구 질문을 한 문장으로 정리하고 그대로 진행한다.

WebSearch 한 번으로 끝나는 단일 사실 조회에는 이 스킬을 쓰지 않는다.

## Step 1 — 워크플로 실행

```
Workflow({ name: "deep-research", args: "<다듬은 질문>" })
```

되묻기로 얻은 답을 질문 문장에 녹여 넘긴다. `args`는 문자열이어야 하며, 비어 있으면
워크플로가 즉시 `invalid_input`을 반환한다.

## Step 2 — 결과 전달

반환값을 사용자 언어(기본 한국어)로 전달한다. 소스 제목과 인용문은 원문 언어를 유지한다.

먼저 `status`에 따라 행동한다.

| 상태 | 호출자 행동 |
| --- | --- |
| `ok` | `findings`를 전달하고 아래 커버리지·실패 통계를 함께 확인한다 |
| `invalid_input` | 결론을 만들지 말고 연구 질문을 요청한다 |
| `infrastructure_failure` | **연구 결론이 아니다.** 실패 범위를 밝히고 재시도를 권한다 |
| `no_claims` | 확인 가능한 주장을 추출하지 못했음을 소스·커버리지 한계와 함께 밝힌다 |
| `inconclusive` | 확정 주장이 없음을 밝히고 `refuted`와 `unverified`를 구분한다 |
| `synthesis_failed` | 그룹화 실패를 밝히고 `confirmed`에 보존된 검증 주장·인용을 병합하지 않은 채 전달한다 |

검증은 주장마다 최대 3표를 사용한다. `supported`가 2표 이상이어야 확정된다. 유효 투표가
3표보다 적으면 해당 항목의 `erroredVotes`와 `stats.verifierErrored`/`summary`의 실패
맥락을 함께 밝힌다. `votes[].vote`(예: `3-0`, `2-1`, `2-0 (1 errored)`)에서 `2-1`은
의견이 갈린 결과이므로 만장일치처럼 서술하지 않는다. `unverified[]`와 `refuted[]`의
`reason`은 검증기가 남긴 실패·반박 사유다.

최종 finding의 `claims`, `sources`, `sourceDetails`, `quotes`, `votes`, `evidence`는 자유
합성 문구가 아니라 확정된 원 주장과 검증 결과에서 재구성된다. 출처 제목은
`sourceDetails[].title`, 원문 인용은 `quotes[].quote`에서 읽는다.

`stats`를 함께 확인하고, 다음이 0이 아니면 **반드시 사용자에게 밝힌다.**

| 필드 | 뜻 |
| --- | --- |
| `anglesNoResults` | 검색은 완료했지만 유용한 결과가 없던 앵글 수 |
| `anglesFailed` | 검색이 죽은 앵글 수. 커버리지가 계획(`anglesPlanned`)보다 좁다 |
| `anglesWithoutFetch` | 검색 결과는 있었지만 fetch 슬롯을 받지 못한 앵글 수 |
| `fetchSkipped` | 무관하거나 paywall이라 건너뛴 소스 수 |
| `fetchErrored` | fetch가 실패한 소스 수 |
| `budgetDropped` | fetch 상한 또는 실행 예산 때문에 제외된 후보 수. fetch 단계에서 잘린 소스는 `sources[]`에 `fetchStatus: "budget_dropped"`로 남는다 |
| `unverified` | 검증기가 실패해 판정하지 못한 주장. **"반박됨"과 다르다** |
| `killed` | 반박된 주장 수. `refuted[]`의 주장·투표·이유를 숨기지 않는다 |

`claimsVerified`가 `claimsExtracted`보다 작으면 검증 상한에서 잘린 나머지 주장이
`unranked[]`에 남는다. 확정도 반박도 아니므로 finding으로 쓰지 말고, 중요해 보이면
재실행을 권한다.

## Hard rules

- 반박되거나 미검증인 주장을 finding으로 제시하지 않는다.
- 모든 finding은 fetch된 URL을 최소 하나 인용한다. 기억에서 인용하지 않는다.
- "증거를 찾지 못함"과 "반대 증거가 있음"을 구분해 말한다.
- 사용자가 저장을 요청하지 않으면 파일을 쓰지 않는다.
