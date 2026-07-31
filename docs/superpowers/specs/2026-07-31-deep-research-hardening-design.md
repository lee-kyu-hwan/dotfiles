# Deep Research 워크플로 신뢰성 강화 설계

## 목표

`deep-research` 워크플로가 웹에서 가져온 비신뢰 콘텐츠와 에이전트 출력을
그대로 신뢰하지 않도록 바꾼다. 최종 finding은 코드가 확인한 `confirmed`
claim만 참조하고, 실제 fetch한 출처와 실제 검증 투표를 결정적으로 보존해야
한다. 검색·fetch·검증 인프라 실패는 연구 결과와 구분하며, 병렬 완료 순서가
소스 선택 결과를 바꾸지 않아야 한다.

## 범위

- 합성 단계의 claim provenance 검증
- 웹 콘텐츠의 JSON 인코딩과 비신뢰 경계 강화
- search/fetch/verdict/result 상태의 명시적 모델링
- 검증 투표 판정과 누락 패널 처리
- fetch 대상의 결정적·공정한 선택
- URL dedup에서 의미 있는 query 보존
- 스킬 문서와 실제 반환 shape 정합성
- 외부 패키지 없는 회귀 테스트 하네스

다음은 이번 변경의 범위가 아니다.

- 별도 guard 모델 도입
- 워크플로 파일의 다중 모듈 분리
- 리서치 품질을 평가하는 실서비스 벤치마크
- Claude Workflow 런타임 자체 변경

## 설계 원칙

1. JSON Schema가 보장하는 것은 shape이지 provenance가 아니다.
2. 모델이 생성한 ID·텍스트·URL은 후속 코드에서 다시 검증한다.
3. 오류와 “자료 없음”, “반박됨”은 서로 다른 상태로 표현한다.
4. 비결정적인 병렬 완료 순서가 품질·커버리지 결정을 내리지 않게 한다.
5. 비신뢰 콘텐츠를 프롬프트에 넣어야 할 때는 자유 형식 연결 대신
   `JSON.stringify()`로 인코딩한다.
6. 예상한 인프라 실패만 구조화된 결과로 변환하고 프로그래밍 오류는 숨기지
   않는다.

참고 근거:

- Anthropic은 간접 prompt injection 대응으로 비신뢰 tool content의 명시적
  분리, JSON 인코딩, 최소 권한, 출력 검증을 권장한다.
  <https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks>
- Structured Outputs는 schema 적합성을 보장하지만 값의 출처나 의미까지
  보장하지 않는다.
  <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
- RFC 3986에서 query는 path와 함께 리소스를 식별할 수 있다.
  <https://www.rfc-editor.org/rfc/rfc3986.html>

## 데이터 모델

### Search 결과

```text
status: "ok" | "no_results" | "failed"
results: SearchResult[]
errorReason?: string
```

`ok`에는 최소 한 개의 결과가 있어야 한다. `no_results`는 검색은 수행됐지만
관련 결과가 없음을 뜻하고, `failed`는 rate limit·도구 오류·에이전트 실패를
뜻한다. `anglesSucceeded`, `anglesNoResults`, `anglesFailed`를 각각 집계한다.

### Fetch 결과

```text
status: "ok" | "irrelevant" | "paywalled" | "failed"
sourceQuality: "primary" | "secondary" | "blog" | "forum" | "unreliable"
claims: ExtractedClaim[]
publishDate?: string
errorReason?: string
```

`failed`만 `fetchErrored`에 포함한다. `irrelevant`와 `paywalled`는
`fetchSkipped`로 따로 집계한다. `sourcesFetched`는 `status === "ok"`인
소스만 센다. token budget으로 실행하지 못한 소스는 `budgetDropped`에
포함하고 fetch 결과에는 넣지 않는다.

### 검증 결과

```text
outcome: "supported" | "refuted" | "unverified"
evidence: string
confidence: "high" | "medium" | "low"
counterSource?: string
failureReason?: string
```

패널 판정은 다음과 같다.

- `supported` 2표 이상: `confirmed`
- `refuted` 2표 이상: `refuted`
- 그 밖의 모든 조합: `unverified`

`1-1 + 오류 1표`, 유효표 1개 이하, claim 단위 병렬 작업 누락은 모두
`unverified`다. `rankedClaims`의 모든 원소는 `confirmed`, `refuted`,
`unverified` 중 정확히 하나에 남아야 한다.

### 최종 결과

모든 반환값에 다음 discriminator를 둔다.

```text
status:
  "ok"
  | "invalid_input"
  | "infrastructure_failure"
  | "no_claims"
  | "inconclusive"
  | "synthesis_failed"
```

`stats`는 모든 정상·실패 반환 경로에서 같은 숫자 필드를 가지며 없는 값은
0으로 채운다. `sources`도 항상 `url`, `title`, `quality`, `angle`,
`claimCount`, `publishDate`, `fetchStatus`를 같은 shape로 반환한다.

## 프롬프트와 provenance

웹 검색에서 온 `title`, `url`, 추출된 `claim`, `quote`는 모두
`JSON.stringify()`로 인코딩한 객체로 프롬프트에 넣는다. JSON 인코딩은
delimiter 조기 종료를 막지만 prompt injection을 완전히 제거하지는 않으므로
결정적 출력 검증과 함께 사용한다.

합성 입력에는 다음만 제공한다.

- confirmed claim의 opaque ID
- claim·quote·source·vote·verifier evidence를 담은 JSON 데이터
- 비신뢰 데이터는 지시가 아니라는 명시적 정책
- refuted/unverified의 원문이 아닌 개수와 실패 요약

합성 schema의 finding은 자유 URL과 자유 vote 대신 다음을 반환한다.

```text
claimIds: string[]  // minItems: 1
```

워크플로 코드는 모든 `claimIds`가 confirmed map에 존재하는지 검증한다.
최종 finding의 `claims`, `sources`, `votes`, `quotes`, verifier evidence는
해당 confirmed claim에서 재구성한다. 모델은 confirmed claim ID의 grouping만
제안할 수 있다. 제목은 그룹의 첫 confirmed claim으로, confidence는 출처 품질과
실제 투표로 코드가 결정한다. 허용되지 않은 ID나 빈 ID 배열이 있으면 synthesis
실패로 취급해 이미 검증된 claim을 salvage한다. 합성 결과를 `...report`로 직접
spread하지 않는다.

## 검색과 fetch 선택

검색 에이전트는 계속 병렬 실행하지만 fetch는 검색 전체가 끝난 다음 시작한다.

1. 모든 search 결과를 수집한다.
2. 각 앵글 안에서 relevance 순으로 정렬한다.
3. URL을 정규화하며 중복을 제거한다.
4. 앵글을 round-robin으로 순회해 한 번에 한 소스씩 선택한다.
5. `MAX_FETCH`에 도달하거나 후보가 없어질 때까지 반복한다.
6. 선택된 소스만 병렬 fetch한다.

이 방식은 빠른 검색 앵글이 fetch 슬롯을 독점하지 못하게 한다. 어떤 앵글에서
실제 fetch 대상이 하나도 선택되지 않았는지 `anglesWithoutFetch`로 노출한다.

URL 정규화는 scheme·host의 대소문자, `www.`, 마지막 `/`, fragment를
정규화한다. query는 리소스 식별에 사용될 수 있으므로 보존한다. 런타임에
`URL` global이 없다는 현재 제약 때문에 regex 기반 파서를 유지하되,
`http`와 `https`만 fetch 후보로 허용한다.

## 오류 처리

- Scope agent의 budget/API 오류는 `infrastructure_failure`로 반환한다.
- Claude Workflow의 실제 `parallel()`은 모든 task가 settle할 때까지 기다린 뒤
  rejection을 throw하지 않고 해당 위치의 `null`로 정규화한다. 따라서 병렬
  task guard는 성공과 실패 모두 protocol marker가 있는 plain-data envelope로
  반환한다. 성공은 `{ok:true,value}`, 실패는 raw `Error` 대신 C0/C1·
  bidi/format 제어 문자와 길이를 제한한
  `{ok:false,failure:{kind,name,message}}`다. agent 반환값은 항상 `value`
  안에 한 단계 중첩되므로 같은 marker를 위조해도 envelope로 해석되지 않는다.
  Search·Fetch·Verifier의 각 barrier는 정확히 한 envelope 계층만 검증·
  unwrap하고 실패를 barrier 밖에서 새 `Error`로 복원·throw한다.
- Search agent의 null·명시적 실패·재시도 가능한 rejection은 angle 실패로
  기록한다. 비재시도 오류와 task 내부 변환 오류는 failure envelope로 전파한다.
- Fetch agent의 예상한 budget 오류만 `budgetDropped`로 바꾸고, 그 밖의
  재시도 가능 rejection은 fetch 실패로 기록한다. 결과 변환 중 발생한
  `TypeError` 같은 프로그래밍 오류와 비재시도 오류는 failure envelope로
  전파한다.
  fetch barrier 결과의 각 슬롯은 선택한 source의 원래 index로 다시 결합한다.
  기록된 `WorkflowBudgetExceededError` index의 `null`만 budget drop으로
  유지하고, 그 밖의 누락/null 슬롯은 URL·title·angle을 보존한 명시적
  `failed` source로 복원한다. 따라서 모든 fetch 슬롯이 누락되면
  `infrastructure_failure`가 된다.
  `WorkflowBudgetExceededError` 판정은 먼저 공통 error classifier를 통과한
  뒤 실제 constructor 또는 직렬화된 plain-object name만 인정한다. 일반
  `Error` constructor와 HTTP 400~499 우선순위는 budget 이름·retryable
  충돌보다 앞서므로 budget drop으로 숨지 않는다.
- Verifier 호출은 `APIConnectionError`, `APIConnectionTimeoutError`,
  `RetryableError`, `RateLimitError`, `InternalServerError`,
  `WorkflowBudgetExceededError`, 명시적 `retryable === true`, HTTP
  408·409·429·5xx, 알려진 재시도 가능 API error type/code만
  `unverified` 표로 처리한다. SDK를 import할 수 없는 워크플로 sandbox에서는
  실제 `Error` subclass의 `constructor.name`과 직렬화된 오류의 안전한
  `name`·status·type/code shape를 함께 duck-type 판별한다.
- Verifier의 prompt와 호출 options는 `try` 밖에서 만든다. 일반 `Error`,
  `TypeError`·`ReferenceError`·`SyntaxError`·`RangeError`·`EvalError`·
  `URIError`·`AggregateError`와 인증·권한·잘못된 요청 같은 비재시도 오류는
  숨기지 않고 전파한다. 내장 프로그래밍 오류
  constructor와 HTTP 400~499(408·409·429 제외) 판정은 retryable 이름·flag·
  type/code보다 우선한다.
- claim 단위 병렬 결과가 null이어도 원 claim을 보존해 unverified panel을
  만든다. 내부 verifier vote failure는 panel guard 안에서 unwrap·throw되고,
  외부 guard가 새 failure envelope로 감싸 외부 panel barrier까지 전달한다.
  `VERDICT_SCHEMA`도 `additionalProperties: false`로 marker-shaped 추가 필드를
  거부하지만, 보안 경계는 schema가 아니라 guard-owned envelope 계층이다.
- Synthesis throw, null, provenance 검증 실패는 `synthesis_failed` salvage를
  반환한다.

사용자에게 표시하는 label과 log는 기존 `quotedLabel()`·`stripLabelChars()`를
계속 사용한다. scope의 question과 angle label 로그에도 같은 규칙을 적용한다.

## 테스트 설계

`tests/deep-research.test.mjs`에서 Node 내장 `node:test`와 `assert`만 사용한다.
프로덕션 워크플로를 `AsyncFunction`으로 감싸고 `agent`, `parallel`,
`pipeline`, `phase`, `log`, `args`를 결정적 stub으로 주입한다. 기본
`parallel` stub은 `Promise.allSettled()`로 모든 thunk를 실행하고 rejection을
`null`로 바꿔 실제 Claude Workflow 런타임 의미론을 재현한다. 특정 누락
panel을 만드는 테스트의 `parallelOverride` 동작은 그대로 유지한다.

`tests/**`는 `.chezmoiignore`에 추가해 홈 디렉터리에 배포하지 않는다.

필수 회귀 테스트:

1. 빈 입력과 Scope 실패의 구조화된 상태
2. search 실패·빈 결과·부분 성공 통계
3. fetch 실패·paywall·irrelevant·budget drop 구분
4. `1-1 + error`와 누락 panel이 unverified
5. 2 support가 confirmed, 2 refute가 refuted
6. synthesis가 refuted/unverified/존재하지 않는 ID를 반환하면 salvage
7. 최종 URL·vote·quote가 confirmed claim에서 재구성됨
8. 6개 앵글의 36개 결과에서 최대 15개를 round-robin 선택
9. query가 다른 URL을 별도 소스로 유지
10. delimiter·C0/C1·bidi·긴 host를 포함한 입력이 label/log를 위조하지 못함
11. synthesis budget 오류가 confirmed claim을 보존
12. 모든 반환 경로의 stats와 sources shape 일관성
13. search·fetch·verifier의 비복구 task 오류가 null로 숨지 않고 barrier
    밖으로 전파되며, 누락 결과는 기존 실패/unverified 의미를 유지
14. fetch slot 누락과 의도적 budget drop을 구분하고, 복원 오류의
    name·kind·message가 안전한 문자와 길이 제한을 지킴
15. forged sentinel/envelope-shaped verifier 값은 정상 vote 값으로만
    판정되고, budget 이름을 위조한 일반/HTTP 400 오류는 전파됨

검증 명령:

```bash
node --test tests/deep-research.test.mjs
git diff --check
```

## 문서 변경

`dot_agents/skills/deep-research/SKILL.md`는 다음 실제 동작을 설명하도록
수정한다.

- 최대 3표, confirmed에는 최소 2개의 support 표가 필요
- 합계가 3보다 작은 vote는 검증기 실패를 함께 표시
- source title과 quote가 정상 결과에서도 보존됨
- 새 result status와 실패 통계
- `infrastructure_failure`는 연구 결론으로 전달하지 않음

## 완료 조건

- 모델이 임의 URL·vote·refuted claim을 최종 finding에 넣을 수 없다.
- 검색·fetch·검증 실패가 “근거 없음”이나 “반박됨”으로 집계되지 않는다.
- `1-1` 패널은 confirmed가 아니다.
- fetch 선정은 검색 완료 순서와 무관하며 모든 성공 앵글에 공정한 기회를 준다.
- query가 다른 URL은 서로 다른 후보로 남는다.
- 필수 회귀 테스트와 문법·diff 검사가 통과한다.
