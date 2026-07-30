---
name: deep-research
description: Use when the user wants a deep, multi-source, fact-checked research report on any topic (triggers like "딥 리서치", "deep research", "웹조사해서 정리", "리서치 보고서"). Runs the deep-research workflow — decompose into search angles, search, extract falsifiable claims, adversarially verify, synthesize a cited report. For a quick single-fact lookup, just search directly instead.
---

# Deep Research

파이프라인은 `dot_claude/workflows/deep-research.js` 워크플로가 실행한다. 이 스킬은
앞단(질문 다듬기)과 뒷단(결과 전달)만 담당한다. **절차를 여기서 다시 서술하지 않는다** —
두 곳에 적으면 수치가 어긋난다. 실제 앵글 수·fetch 상한·검증 임계값은 워크플로 상단의
상수가 유일한 기준이다.

## Step 0 — 스코프 확인 (실행 전)

질문이 불충분하면 2-3개만 되묻는다. 예: 예산·용도·지역이 없는 "어떤 차를 살까".
충분하면 연구 질문을 한 문장으로 정리하고 그대로 진행한다.

WebSearch 한 번으로 끝나는 단일 사실 조회에는 이 스킬을 쓰지 않는다.

## Step 1 — 워크플로 실행

```
Workflow({ name: "deep-research", args: "<다듬은 질문>" })
```

되묻기로 얻은 답을 질문 문장에 녹여 넘긴다. `args`는 문자열이어야 하며, 비어 있으면
워크플로가 즉시 에러를 반환한다.

워크플로가 하는 일: 질문을 검색 앵글로 분해 → 앵글별 병렬 검색 → URL 중복 제거 후
소스 fetch·주장 추출 → 주장별 3표 적대적 검증 → **확정된 주장만** 종합해 인용이 붙은
보고서.

## Step 2 — 결과 전달

반환값을 사용자 언어(기본 한국어)로 전달한다. 소스 제목과 인용문은 원문 언어를 유지한다.

`stats`를 함께 확인하고, 다음이 0이 아니면 **반드시 사용자에게 밝힌다.**

| 필드 | 뜻 |
| --- | --- |
| `anglesFailed` | 검색이 죽은 앵글 수. 커버리지가 계획(`anglesPlanned`)보다 좁다 |
| `fetchErrored` | fetch가 실패한 소스 수 |
| `budgetDropped` | 토큰 예산·fetch 상한으로 건너뛴 소스 |
| `unverified` | 검증기가 실패해 판정하지 못한 주장. **"반박됨"과 다르다** |
| `killed` | 적대적 검증에서 반박된 주장. `refuted[]`에 이유가 담긴다 |

각 finding의 `vote`(예 `3-0`, `2-1`)를 그대로 전달한다. `2-1`은 검증단이 갈린 것이므로
만장일치처럼 서술하지 않는다.

`summary`가 인프라 실패(rate limit, API 에러, 전체 앵글 실패)를 말하면 그것을 리서치
결론으로 전달하지 않는다. 재시도를 제안한다.

## Hard rules

- 반박되거나 미검증인 주장을 finding으로 제시하지 않는다.
- 모든 finding은 fetch된 URL을 최소 하나 인용한다. 기억에서 인용하지 않는다.
- "증거를 찾지 못함"과 "반대 증거가 있음"을 구분해 말한다.
- 사용자가 저장을 요청하지 않으면 파일을 쓰지 않는다.
