# Plan 개정 노트

기준은 `.claude/quality-state/<task-id>/snapshots/plan-r1.md` 이며 그 이후의 모든 변경을 기록한다. 라운드 1 리뷰는 PASS 92 였고 blocker 는 없었다. 사용자가 승인 게이트에서 advisory finding 5건을 문서에서 해소하도록 선택해 `AWAITING_PLAN_APPROVAL → PLAN_REVIEW` 로 되돌린 뒤 개정했다. Spec 과 구현 범위는 바꾸지 않았다.

## 라운드 2 개정

| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |
|---|---|---|---|---|
| R2.1 | PLAN-001 | AC-4(일치: 403 header matrix 판정은 그대로 두고 분류 결과의 reason 이름만 못박음) | 네 reason 값을 폐쇄 집합으로 명시해도 재시도 여부 판정 자체는 바뀌지 않으므로 예산·지연 상한과 접근 실패 매핑 전제를 깨지 않는다. | 자체 개정 |
| R2.2 | PLAN-001 | AC-5(일치: 429·5xx 경계와 403 소진 매핑 단정 유지) | `retry-limit-reached` 를 명시한 것은 기존 `failed`/`transport-or-5xx` 매핑을 설명하는 관측 이름일 뿐이어서 새 접근 실패 outcome 을 만들지 않는다. | 자체 개정 |
| R2.3 | PLAN-001 | AC-6(일치: `retry_decision` 과 네 `retry_reason` 값을 이름으로 각각 단정) | reason 을 네 값으로 고정하면 구현이 절반만 발급하고 통과하는 여지가 닫히고, 429·5xx 의 기존 reason 과 충돌하지 않는 폐쇄 집합으로 두어 관측 계약을 넓히지 않는다. | 자체 개정 |
| R3.1 | PLAN-005 | AC-8(일치: `created: true` 한정 삭제와 keep-clone 대조 단정 유지) | 삭제 허용 범위는 손대지 않고 partial 접두를 어느 태스크에서 추가하는지만 옮겼으므로 파괴적 연산 범위가 넓어지지 않는다. | 자체 개정 |
| R3.2 | PLAN-005 | AC-7(일치: cleanup warning·partial·종료 3 단정 유지), AC-9(일치: clone 다섯 필드와 `removed` 사실성 유지) | `clone-cleanup-failed:` 접두를 T4 로 옮겨 그 분기가 T4 의 실패 판정으로 처음 검증되게 했다. T3 의 `static-search-incomplete:` 조건과 독립적으로 OR 로 붙으므로 두 조건이 동시에 참이어도 종료 3 으로 한 번 수렴하고 종료 4 선행 판정과 예산 소진 3 을 바꾸지 않는다. | 라운드 1 의 "T3 이 두 접두를 함께 추가" 근거가 사실과 달랐다. T3 의 CMD-4 는 static 접두만, T4 의 CMD-3 은 cleanup 접두만 필요하므로 강제 결합이 아니었고, 함께 넣으면 T3 안에 실패 판정 없는 분기가 생겨 테스트 우선 규칙과 어긋났다. |
| R4.1 | PLAN-005 | AC-10(일치: 제외 전용 결과의 additive shape 단정 유지), AC-11(일치: 읽기 실패의 `complete: false`·partial·종료 3 단정 유지) | additive 필드 범위는 그대로이고 T3 이 추가하는 partial 조건이 static 접두 하나로 좁아졌을 뿐이어서 AC-11 의 종료 3 단정은 여전히 T3 종료 시점에 달성된다. | 자체 개정 |
| R4.2 | PLAN-005 | AC-10(일치: intentional exclusion 은 warning·상태 변화 없음 유지), AC-11(일치: `read_failures` 비어 있지 않을 때 warning 과 partial) | warning 계기와 `<count>` 정의(`len(read_failures)`)는 그대로 유지하고 접두 추가 위치만 정리했으므로 `SPEC-005` 반영 내용이 보존된다. | 자체 개정 |
| R4.3 | PLAN-002 | AC-12(일치: positive hit 보존과 불완전 zero-hit 의 부재 근거 불가 단정 유지), AC-13(일치: 계약 문서의 additive 필드·fail-closed 소비 문구 단정 유지) | 계약 문서 단정 방식만 보강했고 evidence status 값 집합과 ready gate 는 건드리지 않으므로 폐쇄 집합이 넓어지지 않는다. | 자체 개정 |
| R5.1 | PLAN-002 | AC-14(일치: 세 `sha256` 의미를 테스트가 직접 계산한 값과 각각 대조하고 두 의미의 구분까지 단정) | 문구 단정만으로는 문서와 코드가 어긋나도 통과했다. 테스트가 세 값을 스스로 계산해 대조하도록 바꿨고 필드명·스키마·계산 코드는 바꾸지 않아 I9 의 문서 전용 범위를 넓히지 않는다. | 자체 개정 |
| R5.2 | PLAN-002 | AC-15(일치: I13 follow-up 문구 단정 유지) | I13 은 계속 후속 문서화만이며 구현·Issue 생성이 없다는 경계를 바꾸지 않는다. | 자체 개정 |
| R6.1 | PLAN-003 | AC-16(일치: 폐쇄 집합·schema·clone shape·종료 우선순위 단정 유지) | 신설 테스트 총계를 7개로 정정하고 기대 총 테스트 수를 62로 고정한 것은 계약 단정 범위를 바꾸지 않는다. | 자체 개정 |
| R6.2 | PLAN-003 | AC-17(일치: 정확히 `Ran 62 tests` 로 단정), AC-18(일치: `Ran 30 tests` 유지), AC-19(일치: `Ran 108 tests` 유지) | 하한 61 을 정확값 62 로 바꿔 계획된 테스트 하나가 빠져도 통과하는 여지를 닫았고 형제 스위트 기대값은 그대로여서 회귀 판정이 약해지지 않는다. | 자체 개정 |
| R6.3 | PLAN-004 | AC-20(일치: 변경 경로가 승인 범위에만 있음을 `CMD-9`·`CMD-10` 출력으로 증명) | 보고서 경로를 전체 이름으로 적고 신설 fixture 파일을 예상하지 않는다는 사실과 주입 방식을 사전 선언했으므로 `CMD-10` 의 변경 경로 점검에 대조할 목록이 생기고 허용 경로가 넓어지지 않는다. | 자체 개정 |
