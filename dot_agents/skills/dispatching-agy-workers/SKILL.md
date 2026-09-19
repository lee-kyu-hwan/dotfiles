---
name: dispatching-agy-workers
description: Use when offloading self-contained analysis or research units to the agy (Google Antigravity) CLI as parallel workers — extracting patterns from a corpus, adversarially checking candidates, one-shot lookups — to keep the coordinator's context and Claude/Codex usage small. Not for mechanical collection such as gh API calls.
---

# agy 워커 파견

조정(분해·종합·최종 판정)은 Claude·Codex 가 맡고, 한 번에 끝나는 분석 단위만 `agy` 에 맡긴다. 이득은 토큰 수가 아니라 **컨텍스트 격리와 별도 한도**다. agy 결과는 초안이다. 조정자가 기계적으로 검증한 것만 쓴다.

**맞는 쓰임**: 같은 자료를 관점별로 나눠 추출, 후보마다 반박 검증, 한 번에 끝나는 웹 조사.
**안 맞는 쓰임**: gh API 같은 기계적 수집(모델이 필요 없다), 다단계 조사를 통째로 위임.

## 구성

1. **자료**: 스크립트로 작게 만든다(키가 붙은 섹션의 다이제스트). 워커마다 **자료 전체**를 준다. 작업은 자료가 아니라 관점·후보로 나눈다.
2. **프롬프트 파일 하나 = 독립 호출 하나.** 순서는 [공통 지시와 해석 규칙] [자료] [이 워커의 관점] [출력 형태]다. 출력 형태에는 다음을 넣는다:
   - 설명·코드펜스 없이 JSON 객체 하나
   - 근거마다 섹션 키와 **원문 그대로의 인용**(20~200자)
   - 패턴은 서로 다른 출처 2개 이상. 1개뿐이면 `observations`
   - 근거가 약하면 `rejected` 에 이유를 넣는다. 0개여도 된다고 적는다
   - 웹 조사라면 도구 이름과 검색어를 적는다: "`search_web` 도구로 '<검색어>' 를 검색하고"
3. **실행**: `python3 scripts/agy_fanout.py prompts/*.md --out out --expect-json`
4. **인용 검사**: `python3 scripts/check_quotes.py --source digest.md --section-regex '^### (\S+) — ' out/*.result.json`
5. **반박 검증**: 조정자가 후보를 합친 뒤 후보마다 검증 워커를 새 독립 호출로 1개씩 띄운다. 추출 워커가 매긴 신뢰도는 쓰지 않는다.
6. 조정자는 판정이 애매한 후보만 원문과 대조한다.

`scripts/` 경로는 이 스킬 디렉터리 기준이다. 옵션은 `--help` 를 본다.

## 빠른 참조

| 항목 | 값 |
| --- | --- |
| 모델 | `gemini-3.1-pro-low`. `flash-high` 보다 입력이 약 3배 적다 |
| 구조화 출력 | 프롬프트로 JSON 을 지시하고 스크립트가 꺼낸다. `--json-schema` 는 약 14배 비싸고 스키마를 따르지 않는다 |
| 권한 | `--dangerously-skip-permissions` 를 붙이지 않는다. 분석 워커는 도구가 필요 없다 |
| 호출 형태 | 병렬 독립 호출. 독립성이 필요 없는 순차 후속 질문만 `--conversation <id>` 로 이어간다(이력이 캐시로 읽혀 더 싸다) |
| 고정비 | 호출당 약 12k. 몇 분 안에 앞선 호출이 있었을 때만 그중 약 8k 가 캐시로 읽힌다. 워커끼리 공유하는 자료는 캐시되지 않는다 |
| 사용량 | agy JSON 의 `usage`. 스크립트가 `summary.json` 에 합산한다. 이어간 대화는 누적값이라 직전 값과의 차분으로 센다 |
| 크기 | 프롬프트는 argv 로만 전달된다. 900KB 를 넘으면 다이제스트를 줄인다 |

## 흔한 실수

| 실수 | 결과 | 대신 |
| --- | --- | --- |
| `--json-schema` 사용 | 비용 급증, 스키마 자체를 출력 | 프롬프트 JSON + `--expect-json` |
| 자료를 저장소·파일별로 쪼개 나눔 | 경계를 넘는 반복을 못 본다 | 자료 전체 + 관점별 분할 |
| 출처 1개짜리 패턴 허용 | 관찰이 패턴으로 둔갑 | 2개 이상, 나머지는 `observations` |
| 워커의 `high` 를 그대로 사용 | 추출 워커는 과신한다 | 반박 검증 워커 |
| 인용을 믿음 | 줄임표로 이어 붙이거나 표기를 바꾼다 | `check_quotes.py` |
| 토큰을 단어 수로 근사 | 틀린 비교 | `summary.json` 의 `totals` |

실측 근거와 Claude 비교: dotfiles #169.
