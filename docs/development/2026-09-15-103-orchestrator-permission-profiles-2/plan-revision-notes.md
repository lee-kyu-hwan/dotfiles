## 라운드 2 개정

| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |
|---|---|---|---|---|
| R1.1 | PLAN-001 | AC-1(일치: T15가 `test_path_selection_regression`을 선작성하고 focused red/green을 기록함) | 선택 우선순위와 conflict/no-fallback 전제를 보강하며 다른 해소의 전제를 깨거나 새 공백을 열지 않는다. | 자체 개정: CMD-12 selector의 소유·실행 근거가 없던 문장을 구체적인 T15 test-first 계약으로 치환했다. |
| R1.4 | PLAN-001 | AC-4(일치: T2가 `test_account_registry_schema`를 선작성하고 T15 full CMD-1로 최종 판정함) | strict file ownership과 schema 판정을 연결하며 PLAN-002의 hook-reference 보존 전제를 바꾸지 않는다. | 자체 개정: CMD-1 selector의 생성 근거가 없던 계획을 T2 focused red/green 계약으로 치환했다. |
| R3.1 | PLAN-001 | AC-10(일치: T2의 기존 real-path selection 판정과 새 schema selector가 같은 구현 단계에서 green임) | schema test 추가는 real-path 선택 규칙을 변경하지 않아 다른 resolution의 전제나 새 gap을 만들지 않는다. | 자체 개정; 치환 없음: 기존 AC-10 계약은 유지하고 같은 task의 누락 selector만 추가했다. |
| R3.2 | PLAN-001 | AC-11(일치: T2의 Codex-only default/no-fallback 판정은 그대로 유지됨) | account schema selector 배정은 Codex default 경계를 완화하지 않아 교차 해소와 충돌하지 않는다. | 자체 개정; 치환 없음: 기존 AC-11 문언과 판정 수단은 유지했다. |
| R3.3 | PLAN-001 | AC-12(일치: T2의 두 Claude root와 outside-block matrix는 그대로 유지됨) | strict schema 검증 추가가 Claude profile isolation 전제를 깨거나 새 선택 경로를 열지 않는다. | 자체 개정; 치환 없음: 기존 AC-12 문언과 판정 수단은 유지했다. |
| R3.5 | PLAN-001 | AC-14(일치: T2의 priority/directory-only/no-fallback 판정은 그대로 유지됨) | schema selector 추가는 selection priority를 바꾸지 않고 T15 regression selector가 이를 다시 닫는다. | 자체 개정; 치환 없음: 기존 AC-14 계약은 유지하고 누락된 test 소유만 명시했다. |
| R5.2 | PLAN-001 | AC-22(일치: T15의 기존 public-record 판정과 sensitive assertions는 변경 없이 유지됨) | path regression test 추가는 public-record schema나 PLAN-002의 hook bytes premise를 바꾸지 않는다. | 자체 개정; 치환 없음: 기존 AC-22 판정은 유지하고 T15 test-first 목록만 확장했다. |
| R6.5 | PLAN-001 | AC-30(일치: T15의 sensitive/no-live-action sentinel 계약은 변경 없이 유지됨) | focused CMD-12 selector는 disclosure 및 production-boundary 전제를 완화하지 않아 새 gap이 없다. | 자체 개정; 치환 없음: 기존 AC-30 판정은 그대로 유지했다. |
| R7.5 | PLAN-001 | AC-35(일치: focused `test_path_selection_regression` green 뒤 full CMD-12를 포함한 모든 gate를 실행함) | 새 focused green은 full release gate를 대체하지 않으므로 다른 해소의 전제나 검증 공백을 만들지 않는다. | 자체 개정: selector가 실제 생성·실행됨을 증명한 뒤 기존 full command를 실행하도록 순서를 보강했다. |
| 전역 CMD selector 증거 규칙 | PLAN-001 | AC-1(일치: CMD-12 selector의 nonzero collection을 요구함), AC-4(일치: CMD-1 selector의 nonzero collection을 요구함) | 모든 CMD selector에 공통인 green-side `Ran 0 tests` 거부를 추가해 두 국소 해소를 약화하지 않고 같은 유형의 새 공백을 닫는다. | 자체 개정: red-side에만 있던 zero-test 금지를 red/green 양쪽의 전역 규칙으로 치환했다. |
| File map의 Claude settings reference 계약 | PLAN-002 | AC-18(일치: 일곱 event source composition), AC-19(일치: trusted source digest), AC-47(일치: `SubagentStop`·`TaskCompleted` bytes 보존), AC-48(일치: composed settings digest), AC-49(일치: trusted hooks only) | inspect-only interface 설명을 실제 T4/T12 소비 계약과 맞췄으며 PLAN-001의 selector 소유 전제나 새 gap을 만들지 않는다. | 자체 개정: 일부 hook shape만 적던 행을 두 preserved hook의 presence/digest 계약까지 포함하도록 치환했다. |
