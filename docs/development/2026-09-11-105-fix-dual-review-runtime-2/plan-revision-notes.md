## 라운드 2 개정

| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |
|---|---|---|---|---|
| R1.1 | PLAN-004, PLAN-008 | AC-1(일치: baseline 기반 rollback과 T8의 CMD-6 소유가 함께 유지됨) | rollback 원칙과 strict 실행 소유권이 같은 AC에서 충돌하지 않는다. | 자체 개정 |
| R1.2 | PLAN-001, PLAN-003, PLAN-004, PLAN-008 | AC-2(일치: prompt 문자열 제거·EOF·전체 suite), AC-9(일치: T8이 CMD-7 live schema gate를 소유) | stdin 수명주기와 live schema 검증의 실행 순서를 유지한다. | 자체 개정 |
| R1.3 | PLAN-004 | AC-3(일치: baseline 복원 원칙이 문서 계약 검증을 보존) | 공통 rollback이 문서·CLI 계약 evidence를 지우지 않는다. | 자체 개정 |
| R2.1 | PLAN-001, PLAN-002, PLAN-003, PLAN-004, PLAN-005 | AC-4(일치: constructed prompt dispatch와 구조화 빈 배열 유지), AC-5(일치: 대용량 prompt의 start 비차단 검증) | stdin dispatch와 start-before-read 검증의 선행 관계를 유지한다. | 치환 없음 |
| R2.2 | PLAN-001, PLAN-003, PLAN-004, PLAN-007 | AC-6(일치: CMD-1에 start-failure cleanup 포함) | 실제 CMD-1 실행 집합으로 cleanup 판정 공백만 닫는다. | 자체 개정 |
| R2.3 | PLAN-001, PLAN-003, PLAN-004, PLAN-007 | AC-6(일치: prompt/output cleanup과 timeout 경로를 함께 판정) | handle index 호환성을 유지한 채 수명주기 검증을 닫는다. | 자체 개정 |
| R3.1 | PLAN-003, PLAN-004, PLAN-008 | AC-7(일치: strict schema 전체 suite), AC-9(일치: canonical schema live gate) | deterministic schema 검증 뒤 live gate를 실행하는 순서를 유지한다. | 자체 개정 |
| R3.2 | PLAN-003, PLAN-004, PLAN-008 | AC-8(일치: critique closed finding 계약), AC-9(일치: 양쪽 critique live schema gate) | critique 정적 계약과 provider 실증이 같은 canonical schema를 사용한다. | 자체 개정 |
| R3.3 | PLAN-003, PLAN-004, PLAN-008 | AC-9(일치: CMD-7 canonical schema 실증), AC-15(일치: Python 3.14.7 전체 source suite), AC-19(일치: live API helper 계약) | deterministic gate를 통과한 helper만 live schema 실증에 사용한다. | 자체 개정 |
| R4.1 | PLAN-004 | AC-10(일치: packaging required path와 scanner 경계), AC-11(일치: source/archive 경로 집합 동등성) | 동일 baseline과 archive 검증이 packaging 경계를 함께 보존한다. | 자체 개정 |
| R4.2 | PLAN-004 | AC-10(일치: text/binary scanner 경계), AC-11(일치: cache fixture archive 제외) | binary fixture 예외와 cache 제외가 source 집합 판정을 넓히지 않는다. | 자체 개정 |
| R4.3 | PLAN-004 | AC-11(일치: 배포본 전체 suite와 cleanup) | archive 검증과 cleanup을 같은 gate에서 유지한다. | 자체 개정 |
| R5.1 | PLAN-002, PLAN-003, PLAN-004, PLAN-005, PLAN-006 | AC-12(일치: prompt 배타 marker와 ingestion 양면 검증) | 구조화 빈 배열은 유지하고 stdout marker 처리는 T4에만 둔다. | 치환 없음 |
| R5.2 | PLAN-003, PLAN-004 | AC-13(일치: termination reason과 reviewer status 보존) | 전체 discover gate가 실패 진단 회귀를 함께 판정한다. | 자체 개정 |
| R5.3 | PLAN-003, PLAN-004 | AC-14(일치: 미완료 run의 nonzero 종료 코드 판정) | terminal 산출물 기록 뒤 종료 코드 계약을 유지한다. | 자체 개정 |
| R6.1 | PLAN-004, PLAN-008 | AC-1(일치: T8이 CMD-6 slash/no-change 실증을 소유) | baseline 보존 뒤 외부 모델 검증을 시작한다. | 자체 개정 |
| R6.2 | PLAN-002, PLAN-003, PLAN-004, PLAN-005, PLAN-008 | AC-16(일치: 여섯 producer와 fresh synthesis를 CMD-8로 판정), AC-17(일치: 기존 run 보존과 증가 run 확인) | deterministic gate 뒤 E2E를 실행해 기존 제품 run을 보존한다. | 치환 없음 |
| R6.3 | PLAN-004 | AC-15(일치: Python 3.14.7 evidence와 기본 live skip), AC-18(일치: 문서 식별자와 not configured 계약) | 환경 evidence와 문서 계약을 공통 baseline 아래 보존한다. | 자체 개정 |
| R6.4 | PLAN-004, PLAN-008 | AC-9(일치: CMD-7 live schema evidence), AC-15(일치: deterministic 전체 suite 선행), AC-19(일치: opt-in live API helper 계약) | live 호출 전 deterministic 검증을 완료하는 순서를 유지한다. | 자체 개정 |
| R6.5 | PLAN-004, PLAN-008 | AC-16(일치: CMD-8의 여섯 producer gate), AC-17(일치: 제품 HEAD/status와 기존 run 보존), AC-20(일치: E2E helper precondition과 동적 run-id 계약) | T8이 precondition 확인 뒤 E2E를 실행하고 mutation 시 중단한다. | 자체 개정 |
